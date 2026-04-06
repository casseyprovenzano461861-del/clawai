# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
智能LLM缓存和本地模型支持系统
支持语义缓存、分层缓存、本地模型加载和多模型融合
"""

import json
import os
import hashlib
import pickle
import time
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from pathlib import Path
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    HAS_SBERT = True
except ImportError:
    HAS_SBERT = False
    logging.warning("sentence-transformers not installed, using fallback caching")

try:
    from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logging.warning("transformers not installed, local models not available")

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    prompt: str
    response: str
    embedding: Optional[np.ndarray] = None
    timestamp: float = field(default_factory=time.time)
    access_count: int = 1
    model_name: str = ""
    temperature: float = 0.0
    max_tokens: int = 1000
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "key": self.key,
            "prompt": self.prompt,
            "response": self.response,
            "timestamp": self.timestamp,
            "access_count": self.access_count,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """从字典创建"""
        return cls(
            key=data["key"],
            prompt=data["prompt"],
            response=data["response"],
            timestamp=data["timestamp"],
            access_count=data.get("access_count", 1),
            model_name=data.get("model_name", ""),
            temperature=data.get("temperature", 0.0),
            max_tokens=data.get("max_tokens", 1000),
            metadata=data.get("metadata", {})
        )


@dataclass
class LocalModelConfig:
    """本地模型配置"""
    model_id: str
    model_name: str
    model_type: str  # causal, seq2seq, embedding
    model_path: str
    tokenizer_path: str
    quantized: bool = False
    quant_type: str = ""  # gguf, gptq, awq
    device: str = "cpu"
    memory_limit: int = 4096  # MB
    precision: str = "fp16"  # fp32, fp16, int8, int4
    max_length: int = 2048
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        return os.path.exists(self.model_path) and os.path.exists(self.tokenizer_path)


class SemanticCache:
    """语义缓存（基于向量相似度）"""
    
    def __init__(self, cache_dir: str, embedding_model: str = "all-MiniLM-L6-v2"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 缓存文件
        self.cache_file = self.cache_dir / "cache_entries.json"
        self.vector_index_file = self.cache_dir / "vector_index.faiss"
        self.vector_ids_file = self.cache_dir / "vector_ids.json"
        
        # 缓存数据
        self.entries: Dict[str, CacheEntry] = {}
        self.vector_index = None
        self.vector_ids: List[str] = []
        self.embeddings: List[np.ndarray] = []
        
        # 嵌入模型
        self.embedding_model = None
        self.embedding_dim = 384  # MiniLM的维度
        
        # 配置
        self.max_cache_size = 1000
        self.similarity_threshold = 0.85  # 语义相似度阈值
        self.enable_semantic_cache = HAS_SBERT
        
        # 初始化
        self._load_cache()
        self._init_embedding_model(embedding_model)
        self._load_vector_index()
        
        logger.info(f"SemanticCache initialized with {len(self.entries)} entries")
    
    def _init_embedding_model(self, model_name: str):
        """初始化嵌入模型"""
        if not self.enable_semantic_cache:
            logger.warning("Semantic caching disabled (sentence-transformers not available)")
            return
        
        try:
            self.embedding_model = SentenceTransformer(model_name)
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            logger.info(f"Embedding model loaded: {model_name}, dim={self.embedding_dim}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.enable_semantic_cache = False
    
    def _load_cache(self):
        """加载缓存"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for key, entry_data in data.items():
                    self.entries[key] = CacheEntry.from_dict(entry_data)
                
                logger.info(f"Loaded {len(self.entries)} cache entries")
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")
    
    def _save_cache(self):
        """保存缓存"""
        try:
            data = {k: v.to_dict() for k, v in self.entries.items()}
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Saved {len(self.entries)} cache entries")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _load_vector_index(self):
        """加载向量索引"""
        if not self.enable_semantic_cache:
            return
        
        if self.vector_index_file.exists() and self.vector_ids_file.exists():
            try:
                # 加载FAISS索引
                self.vector_index = faiss.read_index(str(self.vector_index_file))
                
                # 加载向量ID映射
                with open(self.vector_ids_file, 'r', encoding='utf-8') as f:
                    self.vector_ids = json.load(f)
                
                # 重建嵌入列表
                self.embeddings = []
                for key in self.vector_ids:
                    if key in self.entries and self.entries[key].embedding is not None:
                        self.embeddings.append(self.entries[key].embedding)
                
                logger.info(f"Loaded vector index with {len(self.vector_ids)} vectors")
            except Exception as e:
                logger.error(f"Failed to load vector index: {e}")
                self._create_vector_index()
        else:
            self._create_vector_index()
    
    def _create_vector_index(self):
        """创建向量索引"""
        if not self.enable_semantic_cache:
            return
        
        try:
            # 创建新的FAISS索引
            self.vector_index = faiss.IndexFlatL2(self.embedding_dim)
            self.vector_ids = []
            self.embeddings = []
            
            # 为现有缓存条目生成嵌入
            if self.entries:
                logger.info("Generating embeddings for existing cache entries...")
                batch_size = 32
                keys = list(self.entries.keys())
                
                for i in range(0, len(keys), batch_size):
                    batch_keys = keys[i:i+batch_size]
                    batch_entries = [self.entries[key] for key in batch_keys]
                    batch_prompts = [entry.prompt for entry in batch_entries]
                    
                    # 生成嵌入
                    batch_embeddings = self.embedding_model.encode(
                        batch_prompts, 
                        convert_to_numpy=True,
                        normalize_embeddings=True
                    )
                    
                    # 更新条目
                    for j, (key, embedding) in enumerate(zip(batch_keys, batch_embeddings)):
                        self.entries[key].embedding = embedding
                        self.vector_ids.append(key)
                        self.embeddings.append(embedding)
                
                # 添加到索引
                if self.embeddings:
                    embedding_array = np.array(self.embeddings).astype('float32')
                    self.vector_index.add(embedding_array)
                    
                    # 保存索引
                    self._save_vector_index()
                    
                logger.info(f"Created vector index with {len(self.vector_ids)} vectors")
        except Exception as e:
            logger.error(f"Failed to create vector index: {e}")
            self.enable_semantic_cache = False
    
    def _save_vector_index(self):
        """保存向量索引"""
        if not self.enable_semantic_cache or self.vector_index is None:
            return
        
        try:
            # 保存FAISS索引
            faiss.write_index(self.vector_index, str(self.vector_index_file))
            
            # 保存向量ID映射
            with open(self.vector_ids_file, 'w', encoding='utf-8') as f:
                json.dump(self.vector_ids, f, ensure_ascii=False)
            
            logger.debug("Saved vector index")
        except Exception as e:
            logger.error(f"Failed to save vector index: {e}")
    
    def _compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """计算余弦相似度"""
        try:
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
        except:
            return 0.0
    
    def get(self, prompt: str, model_name: str = "", temperature: float = 0.0, 
            max_tokens: int = 1000, use_semantic: bool = True) -> Optional[str]:
        """从缓存获取响应"""
        # 1. 精确匹配（基于哈希）
        key = self._generate_key(prompt, model_name, temperature, max_tokens)
        
        if key in self.entries:
            entry = self.entries[key]
            entry.access_count += 1
            entry.timestamp = time.time()
            logger.debug(f"Exact cache hit for key: {key[:16]}...")
            return entry.response
        
        # 2. 语义匹配（如果启用）
        if use_semantic and self.enable_semantic_cache and self.vector_index is not None:
            semantic_match = self._find_semantic_match(prompt, model_name, temperature)
            if semantic_match:
                entry = self.entries[semantic_match]
                entry.access_count += 1
                entry.timestamp = time.time()
                logger.debug(f"Semantic cache hit: similarity={entry.metadata.get('similarity', 0):.3f}")
                return entry.response
        
        return None
    
    def _generate_key(self, prompt: str, model_name: str = "", temperature: float = 0.0,
                     max_tokens: int = 1000) -> str:
        """生成缓存键"""
        key_data = f"{prompt}|{model_name}|{temperature:.2f}|{max_tokens}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _find_semantic_match(self, prompt: str, model_name: str = "", 
                            temperature: float = 0.0) -> Optional[str]:
        """查找语义匹配"""
        if not self.enable_semantic_cache or self.vector_index is None or not self.vector_ids:
            return None
        
        try:
            # 生成查询嵌入
            query_embedding = self.embedding_model.encode(
                prompt, 
                convert_to_numpy=True,
                normalize_embeddings=True
            ).reshape(1, -1).astype('float32')
            
            # 搜索最近邻
            k = min(5, len(self.vector_ids))
            distances, indices = self.vector_index.search(query_embedding, k)
            
            # 检查相似度阈值
            for i in range(k):
                idx = indices[0][i]
                if idx < 0 or idx >= len(self.vector_ids):
                    continue
                
                key = self.vector_ids[idx]
                if key not in self.entries:
                    continue
                
                entry = self.entries[key]
                
                # 检查模型和温度是否匹配（可选）
                if model_name and entry.model_name and model_name != entry.model_name:
                    continue
                
                # 计算相似度
                entry_embedding = entry.embedding
                if entry_embedding is None:
                    continue
                
                similarity = self._compute_similarity(
                    query_embedding.flatten(), 
                    entry_embedding.flatten()
                )
                
                if similarity >= self.similarity_threshold:
                    entry.metadata["similarity"] = similarity
                    return key
        
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
        
        return None
    
    def put(self, prompt: str, response: str, model_name: str = "", 
            temperature: float = 0.0, max_tokens: int = 1000) -> str:
        """将响应放入缓存"""
        key = self._generate_key(prompt, model_name, temperature, max_tokens)
        
        # 创建缓存条目
        entry = CacheEntry(
            key=key,
            prompt=prompt,
            response=response,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            timestamp=time.time(),
            metadata={"cached_at": datetime.now().isoformat()}
        )
        
        # 生成嵌入（如果启用语义缓存）
        if self.enable_semantic_cache and self.embedding_model:
            try:
                embedding = self.embedding_model.encode(
                    prompt, 
                    convert_to_numpy=True,
                    normalize_embeddings=True
                )
                entry.embedding = embedding
                
                # 添加到向量索引
                if self.vector_index is not None:
                    self.vector_index.add(embedding.reshape(1, -1).astype('float32'))
                    self.vector_ids.append(key)
                    self.embeddings.append(embedding)
                    
                    # 定期保存索引
                    if len(self.vector_ids) % 10 == 0:
                        self._save_vector_index()
            except Exception as e:
                logger.error(f"Failed to generate embedding: {e}")
        
        # 添加到缓存
        self.entries[key] = entry
        
        # 清理过期的缓存条目
        if len(self.entries) > self.max_cache_size:
            self._cleanup_old_entries()
        
        # 保存缓存
        self._save_cache()
        
        logger.debug(f"Cached response for key: {key[:16]}...")
        return key
    
    def _cleanup_old_entries(self):
        """清理旧缓存条目"""
        # 基于LRU（最近最少使用）策略
        if len(self.entries) <= self.max_cache_size:
            return
        
        # 计算要删除的数量
        to_remove = len(self.entries) - self.max_cache_size
        
        # 按访问次数和时间戳排序
        entries_list = list(self.entries.items())
        entries_list.sort(key=lambda x: (x[1].access_count, x[1].timestamp))
        
        # 删除最旧的条目
        removed_keys = []
        for i in range(to_remove):
            key, _ = entries_list[i]
            
            # 从向量索引中移除
            if key in self.vector_ids:
                idx = self.vector_ids.index(key)
                self.vector_ids.pop(idx)
                if idx < len(self.embeddings):
                    self.embeddings.pop(idx)
            
            removed_keys.append(key)
            del self.entries[key]
        
        # 重建向量索引
        if removed_keys and self.enable_semantic_cache:
            self._recreate_vector_index()
        
        logger.info(f"Cleaned up {len(removed_keys)} old cache entries")
    
    def _recreate_vector_index(self):
        """重建向量索引"""
        if not self.enable_semantic_cache:
            return
        
        try:
            # 创建新索引
            self.vector_index = faiss.IndexFlatL2(self.embedding_dim)
            
            # 收集所有嵌入
            all_embeddings = []
            all_keys = []
            
            for key, entry in self.entries.items():
                if entry.embedding is not None:
                    all_embeddings.append(entry.embedding)
                    all_keys.append(key)
            
            # 更新索引和映射
            if all_embeddings:
                embedding_array = np.array(all_embeddings).astype('float32')
                self.vector_index.add(embedding_array)
                self.vector_ids = all_keys
                self.embeddings = all_embeddings
            
            # 保存索引
            self._save_vector_index()
            
        except Exception as e:
            logger.error(f"Failed to recreate vector index: {e}")
    
    def clear(self, older_than_days: Optional[int] = None):
        """清理缓存"""
        if older_than_days is None:
            # 清除所有缓存
            self.entries.clear()
            self.vector_ids.clear()
            self.embeddings.clear()
            if self.vector_index:
                self.vector_index.reset()
            
            logger.info("Cleared all cache entries")
        else:
            # 清除超过指定天数的缓存
            cutoff_time = time.time() - (older_than_days * 24 * 3600)
            keys_to_remove = []
            
            for key, entry in self.entries.items():
                if entry.timestamp < cutoff_time:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.entries[key]
            
            # 更新向量索引
            if keys_to_remove:
                self._recreate_vector_index()
                logger.info(f"Cleared {len(keys_to_remove)} cache entries older than {older_than_days} days")
        
        # 保存更改
        self._save_cache()
        if self.enable_semantic_cache:
            self._save_vector_index()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_entries = len(self.entries)
        
        if total_entries == 0:
            return {
                "total_entries": 0,
                "with_embeddings": 0,
                "avg_access_count": 0,
                "oldest_entry": None,
                "newest_entry": None
            }
        
        # 计算统计信息
        entries_with_embeddings = sum(1 for e in self.entries.values() if e.embedding is not None)
        avg_access_count = sum(e.access_count for e in self.entries.values()) / total_entries
        
        # 查找最旧和最新的条目
        oldest_entry = min(self.entries.values(), key=lambda x: x.timestamp)
        newest_entry = max(self.entries.values(), key=lambda x: x.timestamp)
        
        return {
            "total_entries": total_entries,
            "with_embeddings": entries_with_embeddings,
            "avg_access_count": round(avg_access_count, 2),
            "oldest_entry": datetime.fromtimestamp(oldest_entry.timestamp).isoformat(),
            "newest_entry": datetime.fromtimestamp(newest_entry.timestamp).isoformat(),
            "cache_dir": str(self.cache_dir),
            "semantic_cache_enabled": self.enable_semantic_cache,
            "max_cache_size": self.max_cache_size,
            "similarity_threshold": self.similarity_threshold
        }


class LocalModelManager:
    """本地模型管理器"""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # 模型注册表
        self.model_registry: Dict[str, LocalModelConfig] = {}
        self.loaded_models: Dict[str, Any] = {}  # 加载的模型实例
        
        # 默认模型配置
        self._register_default_models()
        
        # 检查transformers是否可用
        self.transformers_available = HAS_TRANSFORMERS
        
        logger.info(f"LocalModelManager initialized, transformers available: {self.transformers_available}")
    
    def _register_default_models(self):
        """注册默认模型"""
        # 小型聊天模型（适合大多数任务）
        self.register_model(LocalModelConfig(
            model_id="tiny-llama-chat",
            model_name="TinyLlama Chat",
            model_type="causal",
            model_path=str(self.models_dir / "tiny-llama-chat"),
            tokenizer_path=str(self.models_dir / "tiny-llama-chat"),
            quantized=False,
            device="cpu",
            memory_limit=2048,
            precision="fp16",
            max_length=1024
        ))
        
        # 小型代码模型（适合安全分析）
        self.register_model(LocalModelConfig(
            model_id="starcoder-tiny",
            model_name="StarCoder Tiny",
            model_type="causal",
            model_path=str(self.models_dir / "starcoder-tiny"),
            tokenizer_path=str(self.models_dir / "starcoder-tiny"),
            quantized=False,
            device="cpu",
            memory_limit=4096,
            precision="fp16",
            max_length=2048
        ))
        
        # 小型嵌入模型
        self.register_model(LocalModelConfig(
            model_id="minilm-l6",
            model_name="MiniLM-L6",
            model_type="embedding",
            model_path="sentence-transformers/all-MiniLM-L6-v2",
            tokenizer_path="sentence-transformers/all-MiniLM-L6-v2",
            quantized=False,
            device="cpu",
            memory_limit=512,
            precision="fp32",
            max_length=512
        ))
    
    def register_model(self, config: LocalModelConfig):
        """注册模型配置"""
        self.model_registry[config.model_id] = config
        logger.info(f"Registered model: {config.model_name} ({config.model_id})")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """获取可用模型列表"""
        available = []
        
        for model_id, config in self.model_registry.items():
            model_info = {
                "model_id": model_id,
                "model_name": config.model_name,
                "model_type": config.model_type,
                "available": config.is_available(),
                "quantized": config.quantized,
                "device": config.device,
                "max_length": config.max_length,
                "loaded": model_id in self.loaded_models
            }
            available.append(model_info)
        
        return available
    
    def load_model(self, model_id: str, force_reload: bool = False) -> bool:
        """加载模型"""
        if not self.transformers_available:
            logger.error("Transformers library not available")
            return False
        
        if model_id in self.loaded_models and not force_reload:
            logger.info(f"Model {model_id} already loaded")
            return True
        
        if model_id not in self.model_registry:
            logger.error(f"Model not found: {model_id}")
            return False
        
        config = self.model_registry[model_id]
        
        if not config.is_available():
            logger.error(f"Model files not available: {model_id}")
            return False
        
        try:
            logger.info(f"Loading model: {config.model_name}...")
            start_time = time.time()
            
            if config.model_type == "embedding":
                # 加载嵌入模型
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer(config.model_path)
                if config.device == "cuda":
                    model = model.to("cuda")
                
            else:
                # 加载语言模型
                tokenizer = AutoTokenizer.from_pretrained(config.tokenizer_path)
                model = AutoModelForCausalLM.from_pretrained(
                    config.model_path,
                    torch_dtype=self._get_torch_dtype(config.precision),
                    device_map="auto" if config.device == "cuda" else None,
                    low_cpu_mem_usage=True
                )
                
                if config.device == "cpu":
                    model = model.to("cpu")
                elif config.device == "cuda":
                    model = model.to("cuda")
            
            # 保存加载的模型
            self.loaded_models[model_id] = {
                "model": model,
                "config": config,
                "tokenizer": tokenizer if config.model_type != "embedding" else None,
                "loaded_at": time.time()
            }
            
            load_time = time.time() - start_time
            logger.info(f"Model {model_id} loaded in {load_time:.2f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            return False
    
    def _get_torch_dtype(self, precision: str):
        """获取torch数据类型"""
        import torch
        
        dtype_map = {
            "fp32": torch.float32,
            "fp16": torch.float16,
            "bf16": torch.bfloat16,
            "int8": torch.int8,
            "int4": torch.int4
        }
        
        return dtype_map.get(precision, torch.float32)
    
    def unload_model(self, model_id: str):
        """卸载模型"""
        if model_id in self.loaded_models:
            # 清理模型资源
            import torch
            import gc
            
            model_info = self.loaded_models[model_id]
            model = model_info["model"]
            
            # 移动模型到CPU并删除
            if hasattr(model, "to"):
                model.to("cpu")
            
            del model
            if "tokenizer" in model_info and model_info["tokenizer"]:
                del model_info["tokenizer"]
            
            del self.loaded_models[model_id]
            
            # 清理内存
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info(f"Model {model_id} unloaded")
    
    def generate(self, model_id: str, prompt: str, **kwargs) -> Optional[str]:
        """使用本地模型生成文本"""
        if model_id not in self.loaded_models:
            if not self.load_model(model_id):
                return None
        
        model_info = self.loaded_models[model_id]
        config = model_info["config"]
        
        try:
            if config.model_type == "embedding":
                # 嵌入模型不用于文本生成
                logger.error(f"Model {model_id} is an embedding model, not for text generation")
                return None
            
            model = model_info["model"]
            tokenizer = model_info["tokenizer"]
            
            # 准备参数
            generation_params = {
                "max_length": kwargs.get("max_length", config.max_length),
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
                "do_sample": kwargs.get("do_sample", True),
                "num_return_sequences": kwargs.get("num_return_sequences", 1)
            }
            
            # 编码输入
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=config.max_length)
            
            # 移动输入到正确的设备
            device = config.device if hasattr(config, "device") else "cpu"
            if device == "cuda" and hasattr(model, "device"):
                inputs = {k: v.to(model.device) for k, v in inputs.items()}
            
            # 生成文本
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    **generation_params
                )
            
            # 解码输出
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 移除输入部分
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Generation failed for model {model_id}: {e}")
            return None
    
    def get_embedding(self, model_id: str, text: str) -> Optional[np.ndarray]:
        """获取文本嵌入"""
        if model_id not in self.loaded_models:
            if not self.load_model(model_id):
                return None
        
        model_info = self.loaded_models[model_id]
        config = model_info["config"]
        
        if config.model_type != "embedding":
            logger.error(f"Model {model_id} is not an embedding model")
            return None
        
        try:
            model = model_info["model"]
            embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None


class HybridLLMManager:
    """混合LLM管理器（支持API + 本地模型）"""
    
    def __init__(self, cache_dir: str = "llm_cache", models_dir: str = "models"):
        # 初始化组件
        self.cache_system = SemanticCache(cache_dir)
        self.model_manager = LocalModelManager(models_dir)
        
        # API客户端（如果有）
        self.api_clients = {}
        self._init_api_clients()
        
        # 配置
        self.preferred_order = ["api", "local", "cache"]  # 优先级顺序
        self.fallback_enabled = True
        self.cost_optimization = True
        
        logger.info("HybridLLMManager initialized")
    
    def _init_api_clients(self):
        """初始化API客户端"""
        # 这里可以初始化OpenAI、DeepSeek等API客户端
        # 简化实现，实际需要根据配置初始化
        pass
    
    def query(self, prompt: str, model_type: str = "auto", **kwargs) -> Dict[str, Any]:
        """查询LLM（混合模式）"""
        result = {
            "success": False,
            "response": None,
            "source": None,
            "model_used": None,
            "cache_hit": False,
            "cost": 0.0,
            "latency": 0.0,
            "error": None
        }
        
        start_time = time.time()
        
        try:
            # 检查缓存
            cache_response = self._check_cache(prompt, model_type, **kwargs)
            if cache_response:
                result.update({
                    "success": True,
                    "response": cache_response,
                    "source": "cache",
                    "cache_hit": True,
                    "latency": time.time() - start_time
                })
                return result
            
            # 根据优先级尝试不同来源
            for source in self.preferred_order:
                if source == "api" and self._has_api_access():
                    api_response = self._query_api(prompt, model_type, **kwargs)
                    if api_response:
                        # 缓存API响应
                        self.cache_system.put(prompt, api_response, model_type, 
                                            kwargs.get("temperature", 0.0),
                                            kwargs.get("max_tokens", 1000))
                        
                        result.update({
                            "success": True,
                            "response": api_response,
                            "source": "api",
                            "model_used": model_type,
                            "latency": time.time() - start_time,
                            "cost": self._estimate_api_cost(prompt, api_response, model_type)
                        })
                        return result
                
                elif source == "local" and self._has_local_model(model_type):
                    local_response = self._query_local(prompt, model_type, **kwargs)
                    if local_response:
                        # 缓存本地模型响应
                        self.cache_system.put(prompt, local_response, model_type,
                                            kwargs.get("temperature", 0.0),
                                            kwargs.get("max_tokens", 1000))
                        
                        result.update({
                            "success": True,
                            "response": local_response,
                            "source": "local",
                            "model_used": model_type,
                            "latency": time.time() - start_time,
                            "cost": 0.0  # 本地模型无API成本
                        })
                        return result
            
            # 所有来源都失败
            result["error"] = "All LLM sources failed"
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"LLM query failed: {e}")
        
        result["latency"] = time.time() - start_time
        return result
    
    def _check_cache(self, prompt: str, model_type: str, **kwargs) -> Optional[str]:
        """检查缓存"""
        temperature = kwargs.get("temperature", 0.0)
        max_tokens = kwargs.get("max_tokens", 1000)
        
        # 尝试精确匹配
        response = self.cache_system.get(prompt, model_type, temperature, max_tokens, use_semantic=False)
        if response:
            return response
        
        # 尝试语义匹配
        if kwargs.get("use_semantic_cache", True):
            response = self.cache_system.get(prompt, model_type, temperature, max_tokens, use_semantic=True)
            if response:
                return response
        
        return None
    
    def _has_api_access(self) -> bool:
        """检查是否有API访问权限"""
        # 简化实现，实际需要检查API密钥和网络连接
        return False  # 暂时禁用API
    
    def _query_api(self, prompt: str, model_type: str, **kwargs) -> Optional[str]:
        """查询API"""
        # 简化实现，实际需要调用具体的API
        return None
    
    def _has_local_model(self, model_type: str) -> bool:
        """检查是否有本地模型"""
        available_models = self.model_manager.get_available_models()
        for model in available_models:
            if model["available"] and model["loaded"]:
                return True
        return False
    
    def _query_local(self, prompt: str, model_type: str, **kwargs) -> Optional[str]:
        """查询本地模型"""
        # 选择最适合的本地模型
        available_models = self.model_manager.get_available_models()
        suitable_models = [
            m for m in available_models 
            if m["available"] and m["loaded"] and m["model_type"] == "causal"
        ]
        
        if not suitable_models:
            return None
        
        # 选择第一个可用的模型
        model_id = suitable_models[0]["model_id"]
        
        # 生成响应
        response = self.model_manager.generate(model_id, prompt, **kwargs)
        return response
    
    def _estimate_api_cost(self, prompt: str, response: str, model_type: str) -> float:
        """估算API成本"""
        # 简化实现，根据模型和token数量估算成本
        prompt_tokens = len(prompt) / 4  # 近似估算
        response_tokens = len(response) / 4
        
        # 假设成本（每千token）
        cost_per_1k = 0.002  # $0.002 per 1k tokens
        
        total_tokens = prompt_tokens + response_tokens
        cost = (total_tokens / 1000) * cost_per_1k
        
        return round(cost, 6)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        cache_stats = self.cache_system.get_stats()
        model_stats = self.model_manager.get_available_models()
        
        return {
            "cache": cache_stats,
            "models": model_stats,
            "preferred_order": self.preferred_order,
            "fallback_enabled": self.fallback_enabled,
            "cost_optimization": self.cost_optimization
        }
    
    def optimize_cost(self, enable: bool = True):
        """启用成本优化"""
        self.cost_optimization = enable
        
        if enable:
            # 成本优化模式下，优先使用本地模型和缓存
            self.preferred_order = ["cache", "local", "api"]
            logger.info("Cost optimization enabled: preferring cache and local models")
        else:
            # 性能模式下，优先使用API
            self.preferred_order = ["api", "local", "cache"]
            logger.info("Cost optimization disabled: preferring API for performance")


def test_cache_system():
    """测试缓存系统"""
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = SemanticCache(tmpdir)
        
        # 测试基本缓存
        test_prompt = "What is cybersecurity?"
        test_response = "Cybersecurity is the practice of protecting systems, networks, and programs from digital attacks."
        
        # 放入缓存
        key = cache.put(test_prompt, test_response, "test-model")
        print(f"Added to cache with key: {key[:16]}...")
        
        # 获取缓存
        cached_response = cache.get(test_prompt, "test-model")
        if cached_response == test_response:
            print("✓ Cache retrieval successful")
        else:
            print("✗ Cache retrieval failed")
        
        # 测试语义缓存（如果可用）
        similar_prompt = "Can you explain cybersecurity?"
        if cache.enable_semantic_cache:
            semantic_response = cache.get(similar_prompt, "test-model", use_semantic=True)
            if semantic_response:
                print("✓ Semantic cache hit")
            else:
                print("✗ Semantic cache miss (may need more entries)")
        
        # 获取统计信息
        stats = cache.get_stats()
        print(f"\nCache stats: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        
        return cache


def test_local_models():
    """测试本地模型管理"""
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = LocalModelManager(tmpdir)
        
        # 获取可用模型
        available_models = manager.get_available_models()
        print(f"Available models: {len(available_models)}")
        
        for model in available_models:
            print(f"  - {model['model_name']}: available={model['available']}, loaded={model['loaded']}")
        
        return manager


if __name__ == "__main__":
    print("Testing LLM Cache and Local Model Support")
    print("=" * 60)
    
    print("\n1. Testing Cache System:")
    cache = test_cache_system()
    
    print("\n2. Testing Local Model Manager:")
    manager = test_local_models()
    
    print("\n3. Testing Hybrid Manager:")
    hybrid = HybridLLMManager()
    stats = hybrid.get_stats()
    print(f"Hybrid manager stats: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    
    print("\n✅ Tests completed")