# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI缓存系统
智能缓存AI响应，减少API调用，提高响应速度
"""

import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict
from datetime import datetime, timedelta
import logging


logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_access(self):
        """更新访问时间"""
        self.last_accessed = time.time()
        self.access_count += 1
    
    def is_expired(self, ttl_seconds: int) -> bool:
        """检查是否过期"""
        age = time.time() - self.created_at
        return age > ttl_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "key": self.key,
            "value_size": len(str(self.value)) if isinstance(self.value, str) else 0,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "last_accessed": datetime.fromtimestamp(self.last_accessed).isoformat(),
            "access_count": self.access_count,
            "size_bytes": self.size_bytes,
            "age_seconds": time.time() - self.created_at,
            "metadata": self.metadata
        }


class AICacheSystem:
    """
    AI缓存系统
    支持TTL、LRU淘汰、智能缓存策略
    """
    
    def __init__(
        self,
        max_size_mb: int = 100,
        default_ttl_seconds: int = 3600,  # 1小时
        enable_persistence: bool = False,
        persistence_file: str = "ai_cache.db"
    ):
        """
        初始化缓存系统
        
        Args:
            max_size_mb: 最大缓存大小（MB）
            default_ttl_seconds: 默认TTL（秒）
            enable_persistence: 是否启用持久化
            persistence_file: 持久化文件路径
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl_seconds = default_ttl_seconds
        self.enable_persistence = enable_persistence
        self.persistence_file = persistence_file
        
        # 使用OrderedDict实现LRU
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.current_size_bytes = 0
        
        # 统计信息
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_requests": 0,
            "total_saved_ms": 0
        }
        
        # 加载持久化缓存
        if enable_persistence:
            self._load_from_disk()
    
    def _generate_key(self, data: Dict[str, Any]) -> str:
        """生成缓存键"""
        # 规范化数据以确保一致性
        normalized = {}
        for key in sorted(data.keys()):
            value = data[key]
            if isinstance(value, dict):
                # 递归规范化字典
                normalized[key] = self._generate_key(value)
            elif isinstance(value, list):
                # 对列表进行排序和字符串化
                normalized[key] = json.dumps(sorted(value), sort_keys=True)
            else:
                normalized[key] = str(value)
        
        # 生成MD5哈希
        cache_str = json.dumps(normalized, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _calculate_size(self, value: Any) -> int:
        """计算值的大小（字节）"""
        try:
            # 使用 JSON 估算大小（安全替代 pickle）
            return len(json.dumps(value, default=str).encode('utf-8'))
        except Exception:
            # 备用方法：字符串长度
            return len(str(value))
    
    def _make_room_for(self, size_bytes: int):
        """为新的缓存条目腾出空间（LRU淘汰）"""
        while self.current_size_bytes + size_bytes > self.max_size_bytes and self.cache:
            # 移除最久未使用的条目
            oldest_key, oldest_entry = next(iter(self.cache.items()))
            del self.cache[oldest_key]
            self.current_size_bytes -= oldest_entry.size_bytes
            self.stats["evictions"] += 1
            
            logger.debug(f"淘汰缓存条目: {oldest_key}, 大小: {oldest_entry.size_bytes}字节")
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或已过期则返回None
        """
        self.stats["total_requests"] += 1
        
        if key not in self.cache:
            self.stats["misses"] += 1
            return None
        
        entry = self.cache[key]
        
        # 检查是否过期
        if entry.is_expired(self.default_ttl_seconds):
            # 移除过期条目
            del self.cache[key]
            self.current_size_bytes -= entry.size_bytes
            self.stats["misses"] += 1
            logger.debug(f"缓存条目过期: {key}")
            return None
        
        # 更新访问信息（移至最近使用）
        entry.update_access()
        self.cache.move_to_end(key)
        
        self.stats["hits"] += 1
        logger.debug(f"缓存命中: {key}")
        return entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, metadata: Optional[Dict] = None):
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl_seconds: TTL（秒），如果为None则使用默认值
            metadata: 元数据
        """
        # 计算值大小
        size_bytes = self._calculate_size(value)
        
        # 检查是否超过最大大小
        if size_bytes > self.max_size_bytes:
            logger.warning(f"缓存值过大 ({size_bytes}字节)，跳过缓存")
            return
        
        # 腾出空间
        self._make_room_for(size_bytes)
        
        # 创建缓存条目
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            last_accessed=time.time(),
            size_bytes=size_bytes,
            metadata=metadata or {}
        )
        
        # 添加到缓存
        self.cache[key] = entry
        self.current_size_bytes += size_bytes
        
        # 持久化
        if self.enable_persistence:
            self._save_to_disk()
        
        logger.debug(f"缓存设置: {key}, 大小: {size_bytes}字节, TTL: {ttl}秒")
    
    def cache_ai_response(
        self,
        prompt: str,
        system_prompt: str,
        model_name: str,
        response: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ) -> str:
        """
        缓存AI响应
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            model_name: 模型名称
            response: AI响应
            ttl_seconds: TTL（秒）
            
        Returns:
            缓存键
        """
        cache_data = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "model_name": model_name,
            "response": response
        }
        
        key = self._generate_key(cache_data)
        
        metadata = {
            "model": model_name,
            "prompt_hash": hashlib.md5(prompt.encode()).hexdigest(),
            "system_prompt_hash": hashlib.md5(system_prompt.encode()).hexdigest(),
            "response_time": response.get("response_time", 0),
            "tokens_used": response.get("tokens_used", 0)
        }
        
        self.set(key, response, ttl_seconds, metadata)
        return key
    
    def get_ai_response(
        self,
        prompt: str,
        system_prompt: str,
        model_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取缓存的AI响应
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            model_name: 模型名称
            
        Returns:
            缓存的AI响应，如果不存在则返回None
        """
        cache_data = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "model_name": model_name
        }
        
        key = self._generate_key(cache_data)
        return self.get(key)
    
    def invalidate_by_pattern(self, pattern: str):
        """
        根据模式使缓存失效
        
        Args:
            pattern: 匹配模式（在键中查找）
        """
        keys_to_remove = []
        for key in self.cache.keys():
            if pattern in key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            entry = self.cache[key]
            del self.cache[key]
            self.current_size_bytes -= entry.size_bytes
            logger.info(f"根据模式'{pattern}'使缓存失效: {key}")
    
    def invalidate_by_metadata(self, metadata_filter: Dict[str, Any]):
        """
        根据元数据使缓存失效
        
        Args:
            metadata_filter: 元数据过滤器
        """
        keys_to_remove = []
        for key, entry in self.cache.items():
            match = True
            for filter_key, filter_value in metadata_filter.items():
                if entry.metadata.get(filter_key) != filter_value:
                    match = False
                    break
            
            if match:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            entry = self.cache[key]
            del self.cache[key]
            self.current_size_bytes -= entry.size_bytes
            logger.info(f"根据元数据使缓存失效: {key}")
    
    def clear_expired(self):
        """清除所有过期的缓存条目"""
        expired_keys = []
        for key, entry in self.cache.items():
            if entry.is_expired(self.default_ttl_seconds):
                expired_keys.append(key)
        
        for key in expired_keys:
            entry = self.cache[key]
            del self.cache[key]
            self.current_size_bytes -= entry.size_bytes
        
        logger.info(f"清除 {len(expired_keys)} 个过期缓存条目")
        return len(expired_keys)
    
    def clear_all(self):
        """清除所有缓存"""
        count = len(self.cache)
        self.cache.clear()
        self.current_size_bytes = 0
        logger.info(f"清除所有 {count} 个缓存条目")
        
        if self.enable_persistence:
            self._save_to_disk()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        hit_rate = 0
        if self.stats["total_requests"] > 0:
            hit_rate = self.stats["hits"] / self.stats["total_requests"]
        
        avg_saved_time = 0
        if self.stats["hits"] > 0:
            avg_saved_time = self.stats["total_saved_ms"] / self.stats["hits"]
        
        return {
            **self.stats,
            "hit_rate": round(hit_rate, 4),
            "avg_saved_time_ms": round(avg_saved_time, 2),
            "current_size_bytes": self.current_size_bytes,
            "current_size_mb": round(self.current_size_bytes / (1024 * 1024), 2),
            "max_size_mb": round(self.max_size_bytes / (1024 * 1024), 2),
            "entry_count": len(self.cache),
            "utilization_percent": round((self.current_size_bytes / self.max_size_bytes) * 100, 2)
        }
    
    def get_cache_info(self) -> List[Dict[str, Any]]:
        """获取所有缓存条目的信息"""
        return [entry.to_dict() for entry in self.cache.values()]
    
    def _save_to_disk(self):
        """保存缓存到磁盘"""
        try:
            # 将 CacheEntry 对象序列化为可 JSON 化的字典
            cache_data = {}
            for key, entry in self.cache.items():
                cache_data[key] = {
                    "key": entry.key,
                    "value": entry.value,
                    "created_at": entry.created_at,
                    "last_accessed": entry.last_accessed,
                    "access_count": entry.access_count,
                    "size_bytes": entry.size_bytes,
                    "metadata": entry.metadata
                }

            with open(self.persistence_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'cache': cache_data,
                    'current_size_bytes': self.current_size_bytes,
                    'stats': self.stats
                }, f, default=str, ensure_ascii=False)
            logger.debug(f"缓存持久化到: {self.persistence_file}")
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
    
    def _load_from_disk(self):
        """从磁盘加载缓存"""
        try:
            with open(self.persistence_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 从 JSON 重建 CacheEntry 对象
            raw_cache = data.get('cache', {})
            for key, entry_data in raw_cache.items():
                self.cache[key] = CacheEntry(
                    key=entry_data["key"],
                    value=entry_data["value"],
                    created_at=entry_data["created_at"],
                    last_accessed=entry_data["last_accessed"],
                    access_count=entry_data.get("access_count", 0),
                    size_bytes=entry_data.get("size_bytes", 0),
                    metadata=entry_data.get("metadata", {})
                )

            self.current_size_bytes = data.get('current_size_bytes', 0)
            self.stats = data.get('stats', self.stats.copy())
            
            # 清除过期的条目
            self.clear_expired()
            logger.info(f"从磁盘加载缓存: {len(self.cache)} 个条目")
        except FileNotFoundError:
            logger.info("未找到缓存文件，创建新缓存")
        except Exception as e:
            logger.error(f"加载缓存失败: {e}")
    
    def record_time_saved(self, saved_ms: float):
        """记录节省的时间"""
        self.stats["total_saved_ms"] += saved_ms


# 测试函数
def test_cache_system():
    """测试缓存系统"""
    import time
    import json
    
    print("=" * 80)
    print("AI缓存系统测试")
    print("=" * 80)
    
    # 创建缓存系统
    cache = AICacheSystem(max_size_mb=10, default_ttl_seconds=2)
    
    # 测试1: 基本缓存功能
    print("\n测试1: 基本缓存功能")
    
    test_data = {"prompt": "测试提示词", "response": "测试响应"}
    key = "test_key"
    
    cache.set(key, test_data)
    cached = cache.get(key)
    
    print(f"设置缓存: {key}")
    print(f"获取缓存: {cached}")
    print(f"缓存命中: {cached == test_data}")
    
    # 测试2: AI响应缓存
    print("\n测试2: AI响应缓存")
    
    ai_response = {
        "content": "这是一个AI响应",
        "model_used": "deepseek",
        "response_time": 1.5,
        "tokens_used": 100
    }
    
    cache_key = cache.cache_ai_response(
        prompt="分析目标安全性",
        system_prompt="你是安全专家",
        model_name="deepseek",
        response=ai_response
    )
    
    print(f"AI响应缓存键: {cache_key}")
    
    cached_response = cache.get_ai_response(
        prompt="分析目标安全性",
        system_prompt="你是安全专家",
        model_name="deepseek"
    )
    
    print(f"获取缓存的AI响应: {cached_response}")
    
    # 测试3: TTL过期
    print("\n测试3: TTL过期")
    print("等待3秒让缓存过期...")
    time.sleep(3)
    
    expired_response = cache.get_ai_response(
        prompt="分析目标安全性",
        system_prompt="你是安全专家",
        model_name="deepseek"
    )
    
    print(f"过期后获取: {expired_response}")
    print(f"缓存是否过期: {expired_response is None}")
    
    # 测试4: 统计信息
    print("\n测试4: 统计信息")
    
    # 生成一些缓存访问
    for i in range(5):
        cache.get("non_existent_key")  # 未命中
        cache.get(key)  # 命中（如果没过期）
    
    stats = cache.get_stats()
    print("缓存统计:")
    for stat_key, stat_value in stats.items():
        print(f"  {stat_key}: {stat_value}")
    
    # 测试5: 缓存信息
    print("\n测试5: 缓存信息")
    cache_info = cache.get_cache_info()
    print(f"缓存条目数量: {len(cache_info)}")
    
    if cache_info:
        print("第一个缓存条目:")
        for info_key, info_value in cache_info[0].items():
            print(f"  {info_key}: {info_value}")
    
    # 测试6: 清除缓存
    print("\n测试6: 清除缓存")
    cache.clear_all()
    stats_after_clear = cache.get_stats()
    print(f"清除后条目数量: {stats_after_clear['entry_count']}")
    
    print("\n" + "=" * 80)
    print("测试完成")


if __name__ == "__main__":
    test_cache_system()