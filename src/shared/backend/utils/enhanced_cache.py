# -*- coding: utf-8 -*-
"""
增强型缓存系统
支持多种缓存后端，提供缓存指标监控和智能失效策略
"""

import json
import time
import hashlib
import logging
from typing import Dict, Any, Optional, Callable, Union, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import pickle

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
            "hit_rate": self.hit_rate()
        }


class CacheBackend(ABC):
    """缓存后端抽象基类"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """设置缓存值"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass
    
    @abstractmethod
    def keys(self, pattern: str = "*") -> List[str]:
        """获取匹配模式的键"""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """清空缓存"""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """获取缓存大小"""
        pass
    
    @abstractmethod
    def memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        pass


class MemoryCache(CacheBackend):
    """内存缓存后端"""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.access_times: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self.cache:
            item = self.cache[key]
            # 检查是否过期
            if item.get('expire_at', float('inf')) < time.time():
                self.delete(key)
                return None
            
            # 更新访问时间
            self.access_times[key] = time.time()
            return item.get('value')
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """设置缓存值"""
        # 如果缓存已满，淘汰最久未使用的
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        expire_at = time.time() + ttl
        self.cache[key] = {
            'value': value,
            'expire_at': expire_at,
            'created_at': time.time()
        }
        self.access_times[key] = time.time()
        return True
    
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        if key in self.cache:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if key in self.cache:
            item = self.cache[key]
            return item.get('expire_at', float('inf')) >= time.time()
        return False
    
    def keys(self, pattern: str = "*") -> List[str]:
        """获取匹配模式的键"""
        import fnmatch
        return [k for k in self.cache.keys() if fnmatch.fnmatch(k, pattern)]
    
    def clear(self) -> bool:
        """清空缓存"""
        self.cache.clear()
        self.access_times.clear()
        return True
    
    def size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)
    
    def memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        import sys
        total_size = 0
        for key, value in self.cache.items():
            total_size += sys.getsizeof(key)
            total_size += sys.getsizeof(value)
        
        return {
            "items": len(self.cache),
            "total_bytes": total_size,
            "max_size": self.max_size,
            "usage_percent": round(len(self.cache) / self.max_size * 100, 2)
        }
    
    def _evict_lru(self):
        """淘汰最久未使用的缓存项"""
        if not self.access_times:
            return
        
        # 找到最久未访问的键
        lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]
        self.delete(lru_key)


class RedisCache(CacheBackend):
    """Redis缓存后端"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, 
                 db: int = 0, password: Optional[str] = None):
        try:
            import redis
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=False  # 保持二进制数据
            )
            # 测试连接
            self.redis_client.ping()
            logger.info(f"Redis缓存连接成功: {host}:{port}/{db}")
        except ImportError:
            logger.error("redis-py未安装，请运行: pip install redis")
            raise
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            raise
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            data = self.redis_client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis获取失败 {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """设置缓存值"""
        try:
            data = pickle.dumps(value)
            if ttl > 0:
                self.redis_client.setex(key, ttl, data)
            else:
                self.redis_client.set(key, data)
            return True
        except Exception as e:
            logger.error(f"Redis设置失败 {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Redis删除失败 {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Redis检查失败 {key}: {e}")
            return False
    
    def keys(self, pattern: str = "*") -> List[str]:
        """获取匹配模式的键"""
        try:
            keys = self.redis_client.keys(pattern)
            return [k.decode('utf-8') if isinstance(k, bytes) else k for k in keys]
        except Exception as e:
            logger.error(f"Redis获取键失败: {e}")
            return []
    
    def clear(self) -> bool:
        """清空缓存"""
        try:
            self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis清空失败: {e}")
            return False
    
    def size(self) -> int:
        """获取缓存大小"""
        try:
            return self.redis_client.dbsize()
        except Exception as e:
            logger.error(f"Redis获取大小失败: {e}")
            return 0
    
    def memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        try:
            info = self.redis_client.info('memory')
            return {
                "used_memory": info.get('used_memory', 0),
                "used_memory_human": info.get('used_memory_human', '0B'),
                "used_memory_peak": info.get('used_memory_peak', 0),
                "used_memory_peak_human": info.get('used_memory_peak_human', '0B'),
                "used_memory_rss": info.get('used_memory_rss', 0),
                "used_memory_rss_human": info.get('used_memory_rss_human', '0B'),
                "maxmemory": info.get('maxmemory', 0),
                "maxmemory_human": info.get('maxmemory_human', '0B'),
                "maxmemory_policy": info.get('maxmemory_policy', 'noeviction')
            }
        except Exception as e:
            logger.error(f"Redis获取内存信息失败: {e}")
            return {}


class EnhancedCacheSystem:
    """
    增强型缓存系统
    支持多种缓存后端，提供缓存指标监控和智能失效策略
    """
    
    def __init__(self, cache_type: str = "memory", **kwargs):
        """
        初始化缓存系统
        
        Args:
            cache_type: 缓存类型，支持 "memory" 或 "redis"
            **kwargs: 缓存后端配置参数
        """
        self.cache_type = cache_type
        self.cache_backend = self._init_cache_backend(cache_type, **kwargs)
        self.metrics = CacheMetrics()
        self.key_prefix = "clawai:cache:"
        
        logger.info(f"增强缓存系统初始化完成 - 类型: {cache_type}")
    
    def _init_cache_backend(self, cache_type: str, **kwargs) -> CacheBackend:
        """初始化缓存后端"""
        if cache_type == "redis":
            return RedisCache(**kwargs)
        else:  # 默认为内存缓存
            max_size = kwargs.get('max_size', 1000)
            return MemoryCache(max_size=max_size)
    
    def _make_key(self, key: str) -> str:
        """生成完整的缓存键"""
        return f"{self.key_prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        full_key = self._make_key(key)
        try:
            value = self.cache_backend.get(full_key)
            if value is not None:
                self.metrics.record_hit()
                logger.debug(f"缓存命中: {key}")
            else:
                self.metrics.record_miss()
                logger.debug(f"缓存未命中: {key}")
            return value
        except Exception as e:
            self.metrics.record_error()
            logger.error(f"缓存获取失败 {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """设置缓存值"""
        full_key = self._make_key(key)
        try:
            success = self.cache_backend.set(full_key, value, ttl)
            if success:
                logger.debug(f"缓存设置成功: {key} (TTL: {ttl}s)")
            else:
                logger.warning(f"缓存设置失败: {key}")
            return success
        except Exception as e:
            logger.error(f"缓存设置失败 {key}: {e}")
            return False
    
    def get_with_fallback(self, key: str, fallback_func: Callable, 
                         ttl: int = 3600, force_refresh: bool = False) -> Any:
        """
        获取缓存，如果不存在则调用fallback函数
        
        Args:
            key: 缓存键
            fallback_func: 缓存未命中时调用的函数
            ttl: 缓存生存时间（秒）
            force_refresh: 是否强制刷新缓存
            
        Returns:
            缓存值或fallback函数结果
        """
        if not force_refresh:
            cached_value = self.get(key)
            if cached_value is not None:
                return cached_value
        
        # 缓存未命中或强制刷新，调用fallback函数
        try:
            value = fallback_func()
            self.set(key, value, ttl)
            return value
        except Exception as e:
            logger.error(f"fallback函数执行失败 {key}: {e}")
            raise
    
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        full_key = self._make_key(key)
        try:
            success = self.cache_backend.delete(full_key)
            if success:
                logger.debug(f"缓存删除成功: {key}")
            return success
        except Exception as e:
            logger.error(f"缓存删除失败 {key}: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """按模式清除缓存，返回清除的数量"""
        full_pattern = self._make_key(pattern)
        try:
            keys = self.cache_backend.keys(full_pattern)
            deleted_count = 0
            for key in keys:
                # 移除键前缀
                original_key = key.replace(self.key_prefix, "", 1)
                if self.delete(original_key):
                    deleted_count += 1
                    self.metrics.record_eviction()
            
            logger.info(f"缓存模式清除完成: {pattern} -> 删除 {deleted_count} 个键")
            return deleted_count
        except Exception as e:
            logger.error(f"缓存模式清除失败 {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        full_key = self._make_key(key)
        try:
            return self.cache_backend.exists(full_key)
        except Exception as e:
            logger.error(f"缓存检查失败 {key}: {e}")
            return False
    
    def clear(self) -> bool:
        """清空缓存"""
        try:
            success = self.cache_backend.clear()
            if success:
                logger.info("缓存清空完成")
            return success
        except Exception as e:
            logger.error(f"缓存清空失败: {e}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取缓存指标"""
        metrics = self.metrics.to_dict()
        metrics.update({
            "cache_type": self.cache_type,
            "backend_info": self.cache_backend.memory_usage()
        })
        return metrics
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 测试缓存操作
            test_key = "health_check"
            test_value = {"timestamp": time.time(), "status": "healthy"}
            
            # 设置测试值
            set_success = self.set(test_key, test_value, ttl=10)
            
            # 获取测试值
            get_value = self.get(test_key)
            
            # 删除测试值
            delete_success = self.delete(test_key)
            
            health_status = {
                "status": "healthy" if set_success and get_value and delete_success else "unhealthy",
                "set_success": set_success,
                "get_success": get_value is not None,
                "delete_success": delete_success,
                "timestamp": time.time(),
                "metrics": self.get_metrics()
            }
            
            return health_status
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }


# 全局缓存实例
_cache_instance: Optional[EnhancedCacheSystem] = None

def get_cache_instance() -> EnhancedCacheSystem:
    """获取全局缓存实例"""
    global _cache_instance
    if _cache_instance is None:
        # 从配置加载
        try:
            from config import config
            cache_type = getattr(config, 'CACHE_TYPE', 'memory')
            
            if cache_type == 'redis':
                _cache_instance = EnhancedCacheSystem(
                    cache_type='redis',
                    host=getattr(config, 'REDIS_HOST', 'localhost'),
                    port=getattr(config, 'REDIS_PORT', 6379),
                    db=getattr(config, 'REDIS_DB', 0),
                    password=getattr(config, 'REDIS_PASSWORD', None)
                )
            else:
                _cache_instance = EnhancedCacheSystem(cache_type='memory')
                
            logger.info(f"全局缓存实例初始化完成: {cache_type}")
        except ImportError:
            # 如果配置模块不可用，使用默认内存缓存
            _cache_instance = EnhancedCacheSystem(cache_type='memory')
            logger.info("使用默认内存缓存")
    
    return _cache_instance


def cache_decorator(ttl: int = 3600, key_prefix: str = ""):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存生存时间（秒）
        key_prefix: 键前缀
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = get_cache_instance()
            
            # 生成缓存键
            func_name = func.__name__
            args_str = str(args)
            kwargs_str = str(sorted(kwargs.items()))
            key_content = f"{func_name}:{args_str}:{