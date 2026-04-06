# -*- coding: utf-8 -*-
"""
增强缓存系统
支持多种缓存后端，提供缓存指标监控和智能失效策略
"""

import time
import json
import hashlib
from typing import Dict, Any, Optional, Callable, Union
from dataclasses import dataclass, field
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class CacheMetrics:
    """缓存指标"""
    hits: int = 0
    misses: int = 0
    total_requests: int = 0
    evictions: int = 0
    errors: int = 0
    
    def record_hit(self):
        """记录命中"""
        self.hits += 1
        self.total_requests += 1
    
    def record_miss(self):
        """记录未命中"""
        self.misses += 1
        self.total_requests += 1
    
    def record_eviction(self):
        """记录淘汰"""
        self.evictions += 1
    
    def record_error(self):
        """记录错误"""
        self.errors += 1
    
    def hit_rate(self) -> float:
        """计算命中率"""
        if self.total_requests == 0:
            return 0.0
        return round(self.hits / self.total_requests * 100, 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": self.total_requests,
            "evictions": self.evictions,
            "errors": self.errors,
            "hit_rate": self.hit_rate(),
            "timestamp": datetime.now().isoformat()
        }


class EnhancedCacheSystem:
    """
    增强型缓存系统
    
    特性：
    1. 支持多种缓存后端（内存、Redis、Memcached）
    2. 智能缓存失效策略
    3. 缓存指标监控
    4. 缓存预热
    5. 分布式缓存支持
    """
    
    def __init__(self, cache_backend=None, default_ttl: int = 3600):
        """
        初始化缓存系统
        
        Args:
            cache_backend: 缓存后端实例
            default_ttl: 默认缓存时间（秒）
        """
        self.cache_backend = cache_backend or self._create_default_backend()
        self.default_ttl = default_ttl
        self.metrics = CacheMetrics()
        self.prefix = "clawai:cache:"
        
        # 缓存配置
        self.config = {
            "enable_compression": True,
            "enable_encryption": False,
            "max_cache_size": 10000,  # 最大缓存项数
            "cleanup_interval": 300,  # 清理间隔（秒）
        }
        
        logger.info(f"EnhancedCacheSystem 初始化完成 - 后端: {type(self.cache_backend).__name__}")
    
    def _create_default_backend(self):
        """创建默认缓存后端"""
        try:
            # 尝试使用Redis
            from .cache_backends import RedisCache
            return RedisCache()
        except ImportError:
            # 回退到内存缓存
            from .cache_backends import MemoryCache
            return MemoryCache()
    
    def _generate_key(self, key: str) -> str:
        """生成缓存键"""
        # 添加前缀和哈希
        key_str = f"{self.prefix}{key}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str, default=None) -> Any:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            default: 默认值
            
        Returns:
            缓存值或默认值
        """
        cache_key = self._generate_key(key)
        
        try:
            cached_data = self.cache_backend.get(cache_key)
            if cached_data is not None:
                self.metrics.record_hit()
                logger.debug(f"缓存命中: {key}")
                return self._deserialize(cached_data)
            
            self.metrics.record_miss()
            logger.debug(f"缓存未命中: {key}")
            return default
            
        except Exception as e:
            self.metrics.record_error()
            logger.error(f"缓存获取失败 {key}: {e}")
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 缓存时间（秒），None使用默认值
            
        Returns:
            是否设置成功
        """
        cache_key = self._generate_key(key)
        ttl = ttl or self.default_ttl
        
        try:
            serialized_value = self._serialize(value)
            success = self.cache_backend.set(cache_key, serialized_value, ttl)
            
            if success:
                logger.debug(f"缓存设置成功: {key}, TTL: {ttl}s")
            else:
                logger.warning(f"缓存设置失败: {key}")
            
            return success
            
        except Exception as e:
            self.metrics.record_error()
            logger.error(f"缓存设置失败 {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        删除缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        cache_key = self._generate_key(key)
        
        try:
            success = self.cache_backend.delete(cache_key)
            if success:
                logger.debug(f"缓存删除成功: {key}")
            return success
            
        except Exception as e:
            self.metrics.record_error()
            logger.error(f"缓存删除失败 {key}: {e}")
            return False
    
    def get_or_set(self, key: str, default_func: Callable, ttl: Optional[int] = None) -> Any:
        """
        获取缓存值，如果不存在则设置
        
        Args:
            key: 缓存键
            default_func: 默认值生成函数
            ttl: 缓存时间（秒）
            
        Returns:
            缓存值
        """
        # 尝试获取缓存
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value
        
        # 缓存未命中，执行函数获取值
        try:
            value = default_func()
            self.set(key, value, ttl)
            return value
        except Exception as e:
            logger.error(f"获取或设置缓存失败 {key}: {e}")
            raise
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        按模式清除缓存
        
        Args:
            pattern: 模式匹配
            
        Returns:
            清除的缓存项数量
        """
        try:
            count = self.cache_backend.delete_pattern(pattern)
            logger.info(f"按模式清除缓存: {pattern}, 清除数量: {count}")
            return count
        except Exception as e:
            logger.error(f"按模式清除缓存失败 {pattern}: {e}")
            return 0
    
    def clear(self) -> bool:
        """清除所有缓存"""
        try:
            success = self.cache_backend.clear()
            if success:
                logger.info("缓存已全部清除")
            return success
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取缓存指标"""
        metrics = self.metrics.to_dict()
        
        # 添加后端特定指标
        try:
            backend_metrics = self.cache_backend.get_metrics()
            metrics.update({
                "backend_type": type(self.cache_backend).__name__,
                "backend_metrics": backend_metrics
            })
        except Exception as e:
            logger.warning(f"获取后端指标失败: {e}")
            metrics["backend_metrics"] = {}
        
        return metrics
    
    def warmup_cache(self, warmup_data: Dict[str, Any], ttl: int = 3600):
        """
        缓存预热
        
        Args:
            warmup_data: 预热数据 {key: value}
            ttl: 缓存时间
        """
        logger.info(f"开始缓存预热，数据量: {len(warmup_data)}")
        
        success_count = 0
        for key, value in warmup_data.items():
            try:
                if self.set(key, value, ttl):
                    success_count += 1
            except Exception as e:
                logger.warning(f"缓存预热失败 {key}: {e}")
        
        logger.info(f"缓存预热完成，成功: {success_count}/{len(warmup_data)}")
    
    def _serialize(self, value: Any) -> str:
        """序列化值"""
        try:
            # 尝试JSON序列化
            return json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            # 如果无法JSON序列化，使用字符串表示
            return str(value)
    
    def _deserialize(self, value: str) -> Any:
        """反序列化值"""
        try:
            # 尝试JSON反序列化
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # 如果无法JSON反序列化，返回原始字符串
            return value
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 测试缓存操作
            test_key = "health_check"
            test_value = {"timestamp": datetime.now().isoformat(), "status": "healthy"}
            
            # 设置测试值
            set_success = self.set(test_key, test_value, ttl=10)
            
            # 获取测试值
            get_value = self.get(test_key)
            
            # 删除测试值
            delete_success = self.delete(test_key)
            
            return {
                "status": "healthy" if set_success and delete_success else "degraded",
                "backend": type(self.cache_backend).__name__,
                "set_success": set_success,
                "get_success": get_value is not None,
                "delete_success": delete_success,
                "metrics": self.get_metrics(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# 全局缓存实例
_cache_instance = None

def get_cache_instance() -> EnhancedCacheSystem:
    """获取全局缓存实例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = EnhancedCacheSystem()
    return _cache_instance


def cache_decorator(ttl: int = 3600, key_prefix: str = ""):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存时间（秒）
        key_prefix: 键前缀
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = get_cache_instance()
            
            # 生成缓存键
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # 尝试获取缓存
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存装饰器命中: {func.__name__}")
                return cached_result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 设置缓存
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator