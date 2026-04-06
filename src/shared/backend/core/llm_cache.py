# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
智能LLM缓存系统
支持语义相似度匹配、响应适配和智能过期策略
"""

import json
import hashlib
import logging
import time
import os
import pickle
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path


@dataclass
class CacheEntry:
    """缓存条目"""
    cache_key: str
    original_prompt: str
    response: str
    model_used: str
    timestamp: float
    usage_count: int
    last_accessed: float
    similarity_score: Optional[float] = None
    adaptation_history: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.adaptation_history is None:
            self.adaptation_history = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "cache_key": self.cache_key,
            "original_prompt": self.original_prompt,
            "response": self.response,
            "model_used": self.model_used,
            "timestamp": self.timestamp,
            "usage_count": self.usage_count,
            "last_accessed": self.last_accessed,
            "similarity_score": self.similarity_score,
            "adaptation_history": self.adaptation_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """从字典创建"""
        return cls(**data)
    
    def increment_usage(self):
        """增加使用计数"""
        self.usage_count += 1
        self.last_accessed = time.time()
    
    def add_adaptation(self, new_prompt: str, adapted_response: str, similarity: float):
        """添加适配记录"""
        self.adaptation_history.append({
            "timestamp": time.time(),
            "new_prompt": new_prompt,
            "adapted_response": adapted_response,
            "similarity": similarity
        })


class IntelligentLLMCache:
    """
    智能LLM缓存系统
    支持多种缓存策略和智能匹配
    """
    
    def __init__(self, cache_dir: str = None, backend: str = "sqlite"):
        """
        初始化缓存系统
        
        Args:
            cache_dir: 缓存目录路径
            backend: 缓存后端，支持 "sqlite", "file", "memory"
        """
        self.logger = logging.getLogger(__name__)
        
        # 设置缓存目录
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), "ai_cache")
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.backend = backend
        
        # 初始化缓存后端
        if backend == "sqlite":
            self._init_sqlite_backend()
        elif backend == "file":
            self._init_file_backend()
        else:  # memory
            self.cache_store = {}
        
        # 相似度引擎（简化版，实际应该使用嵌入向量）
        self.similarity_engine = SimilarityEngine()
        
        # 配置
        self.config = {
            "default_ttl": 7 * 24 * 3600,  # 7天
            "max_cache_size": 10000,  # 最大缓存条目数
            "similarity_threshold": 0.8,  # 语义相似度阈值
            "enable_adaptation": True,  # 启用响应适配
            "cleanup_interval": 3600,  # 清理间隔（秒）
            "last_cleanup": time.time()
        }
        
        self.logger.info(f"智能LLM缓存初始化完成，后端: {backend}, 目录: {self.cache_dir}")
    
    def _init_sqlite_backend(self):
        """初始化SQLite后端"""
        db_path = self.cache_dir / "llm_cache.db"
        self.conn = sqlite3.connect(str(db_path))
        self._create_tables()
    
    def _create_tables(self):
        """创建数据库表"""
        cursor = self.conn.cursor()
        
        # 主缓存表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cache_entries (
            cache_key TEXT PRIMARY KEY,
            original_prompt TEXT NOT NULL,
            response TEXT NOT NULL,
            model_used TEXT NOT NULL,
            timestamp REAL NOT NULL,
            usage_count INTEGER DEFAULT 1,
            last_accessed REAL NOT NULL,
            similarity_score REAL,
            adaptation_history TEXT
        )
        ''')
        
        # 索引
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_timestamp ON cache_entries(timestamp)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_usage ON cache_entries(usage_count)
        ''')
        
        self.conn.commit()
    
    def _init_file_backend(self):
        """初始化文件后端"""
        self.cache_store = {}
        self.index_file = self.cache_dir / "cache_index.json"
        self._load_file_cache()
    
    def _load_file_cache(self):
        """加载文件缓存"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, entry_data in data.items():
                        self.cache_store[key] = CacheEntry.from_dict(entry_data)
                self.logger.info(f"从文件加载 {len(self.cache_store)} 个缓存条目")
            except Exception as e:
                self.logger.error(f"加载文件缓存失败: {e}")
                self.cache_store = {}
    
    def _save_file_cache(self):
        """保存文件缓存"""
        try:
            data = {key: entry.to_dict() for key, entry in self.cache_store.items()}
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存文件缓存失败: {e}")
    
    def get_cached_response(self, prompt: str, model: str = "default") -> Optional[str]:
        """
        获取缓存响应
        
        Args:
            prompt: 用户提示
            model: 模型名称
            
        Returns:
            缓存响应或None
        """
        # 1. 精确匹配查找
        exact_match = self._get_exact_match(prompt, model)
        if exact_match:
            self.logger.debug(f"精确缓存命中: {model}")
            return exact_match.response
        
        # 2. 语义相似匹配
        if self.config["enable_adaptation"]:
            similar_entry = self._find_similar_prompt(prompt, model)
            if similar_entry:
                # 使用相似prompt的响应进行适配
                adapted_response = self._adapt_response(similar_entry, prompt)
                if adapted_response:
                    # 记录适配历史
                    similarity = self.similarity_engine.calculate_similarity(
                        prompt, similar_entry.original_prompt
                    )
                    similar_entry.add_adaptation(prompt, adapted_response, similarity)
                    self._update_cache_entry(similar_entry)
                    
                    self.logger.debug(f"语义缓存命中（相似度: {similarity:.2f}）")
                    return adapted_response
        
        # 3. 模式匹配
        pattern_match = self._find_pattern_match(prompt, model)
        if pattern_match:
            self.logger.debug("模式缓存命中")
            return pattern_match.response
        
        return None
    
    def _get_exact_match(self, prompt: str, model: str) -> Optional[CacheEntry]:
        """获取精确匹配"""
        cache_key = self._generate_cache_key(prompt, model)
        
        if self.backend == "sqlite":
            cursor = self.conn.cursor()
            cursor.execute('''
            SELECT * FROM cache_entries 
            WHERE cache_key = ? AND model_used = ?
            ''', (cache_key, model))
            
            row = cursor.fetchone()
            if row:
                entry = self._row_to_cache_entry(row)
                entry.increment_usage()
                self._update_cache_entry(entry)
                return entry
        
        elif self.backend == "file" or self.backend == "memory":
            if cache_key in self.cache_store:
                entry = self.cache_store[cache_key]
                if entry.model_used == model:
                    entry.increment_usage()
                    if self.backend == "file":
                        self._save_file_cache()
                    return entry
        
        return None
    
    def _find_similar_prompt(self, prompt: str, model: str) -> Optional[CacheEntry]:
        """查找相似prompt"""
        # 获取所有同模型的缓存条目
        entries = self._get_entries_by_model(model)
        
        best_entry = None
        best_similarity = 0.0
        
        for entry in entries:
            similarity = self.similarity_engine.calculate_similarity(
                prompt, entry.original_prompt
            )
            
            if similarity > best_similarity and similarity >= self.config["similarity_threshold"]:
                best_similarity = similarity
                best_entry = entry
        
        if best_entry:
            best_entry.increment_usage()
            best_entry.similarity_score = best_similarity
            self._update_cache_entry(best_entry)
        
        return best_entry
    
    def _find_pattern_match(self, prompt: str, model: str) -> Optional[CacheEntry]:
        """查找模式匹配"""
        entries = self._get_entries_by_model(model)
        
        for entry in entries:
            if self.similarity_engine.is_pattern_match(prompt, entry.original_prompt):
                entry.increment_usage()
                self._update_cache_entry(entry)
                return entry
        
        return None
    
    def _adapt_response(self, base_entry: CacheEntry, new_prompt: str) -> Optional[str]:
        """适配响应"""
        # 这里可以使用简单的规则适配，或者调用小型LLM进行适配
        # 简化版：直接返回原始响应，实际应该根据新prompt进行调整
        
        # 检查是否有历史适配记录可用
        for adaptation in reversed(base_entry.adaptation_history):
            similarity = self.similarity_engine.calculate_similarity(
                new_prompt, adaptation["new_prompt"]
            )
            if similarity >= 0.9:
                return adaptation["adapted_response"]
        
        # 简单规则适配：替换关键词
        adapted_response = self._simple_adaptation(base_entry.response, base_entry.original_prompt, new_prompt)
        
        return adapted_response or base_entry.response
    
    def _simple_adaptation(self, base_response: str, original_prompt: str, new_prompt: str) -> str:
        """简单规则适配"""
        # 提取原始prompt中的关键词
        original_keywords = self.similarity_engine.extract_keywords(original_prompt)
        new_keywords = self.similarity_engine.extract_keywords(new_prompt)
        
        # 找出不同的关键词
        different_keywords = []
        for new_keyword in new_keywords:
            if new_keyword not in original_keywords:
                different_keywords.append(new_keyword)
        
        # 如果有不同的关键词，尝试在响应中替换
        if different_keywords:
            adapted_response = base_response
            for keyword in different_keywords:
                # 简单替换：在实际应用中应该更智能
                if keyword in new_prompt and keyword not in original_prompt:
                    # 这里可以添加更复杂的替换逻辑
                    pass
            
            return adapted_response
        
        return base_response
    
    def cache_response(self, prompt: str, response: str, model: str = "default"):
        """
        缓存响应
        
        Args:
            prompt: 用户提示
            response: LLM响应
            model: 模型名称
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(prompt, model)
        
        # 创建缓存条目
        entry = CacheEntry(
            cache_key=cache_key,
            original_prompt=prompt,
            response=response,
            model_used=model,
            timestamp=time.time(),
            usage_count=1,
            last_accessed=time.time()
        )
        
        # 保存到缓存
        self._save_cache_entry(entry)
        
        # 定期清理过期缓存
        self._cleanup_if_needed()
        
        self.logger.debug(f"缓存响应: {model}, 键: {cache_key[:16]}...")
    
    def _generate_cache_key(self, prompt: str, model: str) -> str:
        """生成缓存键"""
        content = f"{model}:{prompt}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _save_cache_entry(self, entry: CacheEntry):
        """保存缓存条目"""
        if self.backend == "sqlite":
            cursor = self.conn.cursor()
            adaptation_history = json.dumps(entry.adaptation_history, ensure_ascii=False)
            
            cursor.execute('''
            INSERT OR REPLACE INTO cache_entries 
            (cache_key, original_prompt, response, model_used, timestamp, 
             usage_count, last_accessed, similarity_score, adaptation_history)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.cache_key,
                entry.original_prompt,
                entry.response,
                entry.model_used,
                entry.timestamp,
                entry.usage_count,
                entry.last_accessed,
                entry.similarity_score,
                adaptation_history
            ))
            
            self.conn.commit()
        
        elif self.backend == "file":
            self.cache_store[entry.cache_key] = entry
            self._save_file_cache()
        
        else:  # memory
            self.cache_store[entry.cache_key] = entry
    
    def _update_cache_entry(self, entry: CacheEntry):
        """更新缓存条目"""
        if self.backend == "sqlite":
            adaptation_history = json.dumps(entry.adaptation_history, ensure_ascii=False)
            
            cursor = self.conn.cursor()
            cursor.execute('''
            UPDATE cache_entries 
            SET usage_count = ?, last_accessed = ?, similarity_score = ?, adaptation_history = ?
            WHERE cache_key = ?
            ''', (
                entry.usage_count,
                entry.last_accessed,
                entry.similarity_score,
                adaptation_history,
                entry.cache_key
            ))
            
            self.conn.commit()
        
        elif self.backend == "file":
            self.cache_store[entry.cache_key] = entry
            self._save_file_cache()
        
        else:  # memory
            self.cache_store[entry.cache_key] = entry
    
    def _get_entries_by_model(self, model: str) -> List[CacheEntry]:
        """获取指定模型的所有缓存条目"""
        entries = []
        
        if self.backend == "sqlite":
            cursor = self.conn.cursor()
            cursor.execute('''
            SELECT * FROM cache_entries WHERE model_used = ? ORDER BY last_accessed DESC LIMIT 100
            ''', (model,))
            
            for row in cursor.fetchall():
                entries.append(self._row_to_cache_entry(row))
        
        elif self.backend == "file" or self.backend == "memory":
            for entry in self.cache_store.values():
                if entry.model_used == model:
                    entries.append(entry)
            
            # 按最后访问时间排序
            entries.sort(key=lambda x: x.last_accessed, reverse=True)
            entries = entries[:100]  # 限制数量
        
        return entries
    
    def _row_to_cache_entry(self, row) -> CacheEntry:
        """SQLite行转换为CacheEntry"""
        adaptation_history = []
        if row[8]:  # adaptation_history字段
            try:
                adaptation_history = json.loads(row[8])
            except:
                pass
        
        return CacheEntry(
            cache_key=row[0],
            original_prompt=row[1],
            response=row[2],
            model_used=row[3],
            timestamp=row[4],
            usage_count=row[5],
            last_accessed=row[6],
            similarity_score=row[7],
            adaptation_history=adaptation_history
        )
    
    def _cleanup_if_needed(self):
        """如果需要，清理过期缓存"""
        current_time = time.time()
        if current_time - self.config["last_cleanup"] < self.config["cleanup_interval"]:
            return
        
        self._cleanup_expired_entries()
        self._cleanup_overflow_entries()
        
        self.config["last_cleanup"] = current_time
        self.logger.debug("缓存清理完成")
    
    def _cleanup_expired_entries(self):
        """清理过期条目"""
        expire_time = time.time() - self.config["default_ttl"]
        
        if self.backend == "sqlite":
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM cache_entries WHERE timestamp < ?', (expire_time,))
            deleted_count = cursor.rowcount
            self.conn.commit()
            
            if deleted_count > 0:
                self.logger.info(f"清理 {deleted_count} 个过期缓存条目")
        
        elif self.backend == "file" or self.backend == "memory":
            expired_keys = []
            for key, entry in self.cache_store.items():
                if entry.timestamp < expire_time:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache_store[key]
            
            if expired_keys:
                self.logger.info(f"清理 {len(expired_keys)} 个过期缓存条目")
                if self.backend == "file":
                    self._save_file_cache()
    
    def _cleanup_overflow_entries(self):
        """清理超出数量限制的条目"""
        if self.backend == "sqlite":
            cursor = self.conn.cursor()
            
            # 获取总条目数
            cursor.execute('SELECT COUNT(*) FROM cache_entries')
            total_count = cursor.fetchone()[0]
            
            if total_count > self.config["max_cache_size"]:
                # 删除使用次数最少的条目
                excess = total_count - self.config["max_cache_size"]
                cursor.execute('''
                DELETE FROM cache_entries 
                WHERE cache_key IN (
                    SELECT cache_key FROM cache_entries 
                    ORDER BY usage_count ASC, last_accessed ASC 
                    LIMIT ?
                )
                ''', (excess,))
                
                deleted_count = cursor.rowcount
                self.conn.commit()
                
                if deleted_count > 0:
                    self.logger.info(f"清理 {deleted_count} 个使用率低的缓存条目")
        
        elif self.backend == "file" or self.backend == "memory":
            if len(self.cache_store) > self.config["max_cache_size"]:
                # 按使用次数和最后访问时间排序
                sorted_entries = sorted(
                    self.cache_store.items(),
                    key=lambda x: (x[1].usage_count, x[1].last_accessed)
                )
                
                # 删除多余的条目
                excess = len(self.cache_store) - self.config["max_cache_size"]
                for i in range(excess):
                    key, _ = sorted_entries[i]
                    del self.cache_store[key]
                
                self.logger.info(f"清理 {excess} 个使用率低的缓存条目")
                
                if self.backend == "file":
                    self._save_file_cache()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            "backend": self.backend,
            "cache_dir": str(self.cache_dir),
            "total_entries": 0,
            "by_model": {},
            "hit_rate": 0.0,
            "avg_usage": 0.0
        }
        
        if self.backend == "sqlite":
            cursor = self.conn.cursor()
            
            # 总条目数
            cursor.execute('SELECT COUNT(*) FROM cache_entries')
            stats["total_entries"] = cursor.fetchone()[0]
            
            # 按模型统计
            cursor.execute('SELECT model_used, COUNT(*) FROM cache_entries GROUP BY model_used')
            for model, count in cursor.fetchall():
                stats["by_model"][model] = count
            
            # 平均使用次数
            cursor.execute('SELECT AVG(usage_count) FROM cache_entries')
            avg_usage = cursor.fetchone()[0]
            stats["avg_usage"] = avg_usage or 0.0
        
        elif self.backend == "file" or self.backend == "memory":
            stats["total_entries"] = len(self.cache_store)
            
            # 按模型统计
            for entry in self.cache_store.values():
                model = entry.model_used
                stats["by_model"][model] = stats["by_model"].get(model, 0) + 1
            
            # 平均使用次数
            if self.cache_store:
                total_usage = sum(entry.usage_count for entry in self.cache_store.values())
                stats["avg_usage"] = total_usage / len(self.cache_store)
        
        return stats
    
    def clear_cache(self, model: str = None):
        """
        清理缓存
        
        Args:
            model: 指定模型，为None时清理所有缓存
        """
        if self.backend == "sqlite":
            cursor = self.conn.cursor()
            
            if model:
                cursor.execute('DELETE FROM cache_entries WHERE model_used = ?', (model,))
                deleted_count = cursor.rowcount
                self.logger.info(f"清理 {deleted_count} 个 {model} 模型的缓存条目")
            else:
                cursor.execute('DELETE FROM cache_entries')
                deleted_count = cursor.rowcount
                self.logger.info(f"清理所有 {deleted_count} 个缓存条目")
            
            self.conn.commit()
        
        elif self.backend == "file" or self.backend == "memory":
            if model:
                keys_to_delete = []
                for key, entry in self.cache_store.items():
                    if entry.model_used == model:
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del self.cache_store[key]
                
                self.logger.info(f"清理 {len(keys_to_delete)} 个 {model} 模型的缓存条目")
            else:
                deleted_count = len(self.cache_store)
                self.cache_store.clear()
                self.logger.info(f"清理所有 {deleted_count} 个缓存条目")
            
            if self.backend == "file":
                self._save_file_cache()


class SimilarityEngine:
    """
    相似度引擎（简化版）
    实际应用中应该使用嵌入向量和更复杂的相似度计算
    """
    
    def __init__(self):
        # 关键词权重（简化处理）
        self.keyword_weights = {
            "scan": 0.3,
            "vulnerability": 0.4,
            "attack": 0.4,
            "security": 0.3,
            "web": 0.2,
            "database": 0.3,
            "port": 0.2,
            "service": 0.2,
            "exploit": 0.4,
            "risk": 0.3
        }
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算文本相似度（简化版）
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            相似度分数 0.0-1.0
        """
        # 简单实现：基于共享关键词
        keywords1 = self.extract_keywords(text1)
        keywords2 = self.extract_keywords(text2)
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # 计算Jaccard相似度
        set1 = set(keywords1)
        set2 = set(keywords2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
        
        jaccard_similarity = intersection / union
        
        # 加权相似度
        weighted_similarity = 0.0
        total_weight = 0.0
        
        for keyword in set1.intersection(set2):
            weight = self.keyword_weights.get(keyword, 0.1)
            weighted_similarity += weight
            total_weight += weight
        
        if total_weight > 0:
            weighted_similarity /= total_weight
        
        # 综合相似度
        combined_similarity = (jaccard_similarity * 0.4 + weighted_similarity * 0.6)
        
        return round(combined_similarity, 3)
    
    def extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取
        keywords = []
        words = text.lower().split()
        
        for word in words:
            # 移除标点符号
            word = ''.join(c for c in word if c.isalnum())
            
            if len(word) >= 3 and word in self.keyword_weights:
                keywords.append(word)
        
        return keywords
    
    def is_pattern_match(self, text1: str, text2: str) -> bool:
        """检查是否模式匹配"""
        # 检查是否有相同的模式，如"扫描{target}的{ports}端口"
        # 简化版：检查是否有相同的结构
        
        # 提取数字和特定词汇
        def extract_pattern(text):
            pattern = []
            for word in text.split():
                if word.isdigit():
                    pattern.append("[NUMBER]")
                elif any(kw in word.lower() for kw in self.keyword_weights.keys()):
                    pattern.append("[KEYWORD]")
                elif len(word) > 5:
                    pattern.append("[TEXT]")
                else:
                    pattern.append(word)
            return " ".join(pattern)
        
        pattern1 = extract_pattern(text1)
        pattern2 = extract_pattern(text2)
        
        return pattern1 == pattern2


def main():
    """测试函数"""
    import json
    
    # 创建缓存系统
    cache = IntelligentLLMCache(backend="memory")
    
    print("=" * 80)
    print("智能LLM缓存系统测试")
    print("=" * 80)
    
    # 测试数据
    test_prompts = [
        "扫描example.com的80和443端口",
        "检查example.com的Web漏洞",
        "评估example.com的安全风险",
        "扫描test.com的3306端口",
        "检查test.com的SQL注入漏洞"
    ]
    
    test_responses = [
        "发现80端口运行nginx，443端口有SSL配置问题",
        "发现XSS和CSRF漏洞，建议修复",
        "目标存在中等风险，建议加强WAF配置",
        "发现MySQL数据库运行在3306端口",
        "发现SQL注入点，建议使用参数化查询"
    ]
    
    # 缓存测试数据
    for i, (prompt, response) in enumerate(zip(test_prompts, test_responses)):
        cache.cache_response(prompt, response, model="test-model")
        print(f"缓存 {i+1}: {prompt[:30]}...")
    
    # 获取缓存统计
    stats = cache.get_cache_stats()
    print(f"\n缓存统计:")
    print(f"  后端: {stats['backend']}")
    print(f"  总条目数: {stats['total_entries']}")
    print(f"  平均使用次数: {stats['avg_usage']:.2f}")
    
    print(f"\n按模型统计:")
    for model, count in stats["by_model"].items():
        print(f"  {model}: {count}条")
    
    # 测试缓存命中
    print(f"\n缓存命中测试:")
    test_queries = [
        "扫描example.com的80和443端口",  # 精确匹配
        "扫描example.com的80端口",  # 相似匹配
        "检查example.com的安全状况",  # 相似匹配
        "完全不相关的查询"  # 无匹配
    ]
    
    for query in test_queries:
        cached_response = cache.get_cached_response(query, model="test-model")
        if cached_response:
            print(f"  命中: {query[:30]}... -> {cached_response[:40]}...")
        else:
            print(f"  未命中: {query[:30]}...")
    
    # 清理缓存测试
    print(f"\n清理缓存测试:")
    cache.clear_cache(model="test-model")
    stats_after = cache.get_cache_stats()
    print(f"  清理后条目数: {stats_after['total_entries']}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()