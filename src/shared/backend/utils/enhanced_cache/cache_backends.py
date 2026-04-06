# -*- coding: utf-8 -*-
"""
缓存后端实现
支持内存缓存、Redis缓存、Memcached缓存
"""

import time
import threading
import json
from typing import Dict, Any, Optional, List
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """缓存后端抽象基类"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """清除所有缓存"""
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取后端指标"""
        return {"backend": type(self).__name__}
    
    def delete_pattern(self, pattern: str) -> int:
        """按模式删除（默认实现）"""
        # 默认实现不支持模式删除
        return 0
    
    def size(self) -> int:
        """获取缓存大小"""
        return 0
    
    def memory_usage(self) -> int:
        """获取内存使用量"""
        return 0


class MemoryCache(CacheBackend):
    """内存缓存后端"""
    
    def __init__(self, max_size: int = 10000):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.lock = threading.RLock()
        self.access_count = 0
        self.hit_count = 0
        self.miss_count = 0
        self.eviction_count = 0
        
        logger.info(f"MemoryCache 初始化 - 最大大小: {max_size}")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            self.access_count += 1
            
            if key in self.cache:
                item = self.cache[key]
                
                # 检查是否过期
                if item["expires_at"] and item["expires_at"] < time.time():
                    del self.cache[key]
                    self.miss_count += 1
                    return None
                
                self.hit_count += 1
                item["access_count"] += 1
                item["last_accessed"] = time.time()
                return item["value"]
            
            self.miss_count += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        with self.lock:
            # 检查是否达到最大大小
            if len(self.cache) >= self.max_size and key not in self.cache:
                # 淘汰最少访问的项
                self._evict_least_used()
            
            # 计算过期时间
            expires_at = None
            if ttl:
                expires_at = time.time() + ttl
            
            # 设置缓存项
            self.cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": time.time(),
                "last_accessed": time.time(),
                "access_count": 0
            }
            
            return True
    
    def _evict_least_used(self):
        """淘汰最少使用的缓存项"""
        if not self.cache:
            return
        
        # 找到访问次数最少的项
        least_used_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k]["access_count"]
        )
        
        del self.cache[least_used_key]
        self.eviction_count += 1
        logger.debug(f"淘汰缓存项: {least_used_key}")
    
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """按模式删除缓存项"""
        with self.lock:
            deleted_count = 0
            keys_to_delete = []
            
            for key in self.cache.keys():
                if pattern in key:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self.cache[key]
                deleted_count += 1
            
            return deleted_count
    
    def clear(self) -> bool:
        """清除所有缓存"""
        with self.lock:
            self.cache.clear()
            self.access_count = 0
            self.hit_count = 0
            self.miss_count = 0
            self.eviction_count = 0
            return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        with self.lock:
            hit_rate = 0
            total_access = self.hit_count + self.miss_count
            if total_access > 0:
                hit_rate = self.hit_count / total_access * 100
            
            return {
                "backend": "MemoryCache",
                "size": len(self.cache),
                "max_size": self.max_size,
                "access_count": self.access_count,
                "hit_count": self.hit_count,
                "miss_count": self.miss_count,
                "eviction_count": self.eviction_count,
                "hit_rate": round(hit_rate, 2),
                "memory_usage": self.memory_usage()
            }
    
    def size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)
    
    def memory_usage(self) -> int:
        """估算内存使用量"""
        total_size = 0
        for key, item in self.cache.items():
            # 估算键大小
            total_size += len(key.encode('utf-8'))
            
            # 估算值大小
            value = item["value"]
            if isinstance(value, str):
                total_size += len(value.encode('utf-8'))
            elif isinstance(value, (dict, list)):
                total_size += len(json.dumps(value).encode('utf-8'))
            else:
                total_size += 50  # 默认估算
            
            # 其他字段
            total_size += 32
        
        return total_size


class RedisCache(CacheBackend):
    """Redis缓存后端"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, 
                 db: int = 0, password: Optional[str] = None):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.client = None
        self._connect()
        
        logger.info(f"RedisCache 初始化 - {host}:{port}/{db}")
    
    def _connect(self):
        """连接Redis"""
        try:
            import redis
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # 测试连接
            self.client.ping()
            logger.info("Redis连接成功")
            
        except ImportError:
            logger.error("未安装redis-py库，请运行: pip install redis")
            raise
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            self.client = None
            raise
    
    def _ensure_connected(self):
        """确保连接正常"""
        if self.client is None:
            self._connect()
        
        try:
            self.client.ping()
        except Exception:
            logger.warning("Redis连接断开，尝试重连...")
            self._connect()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        self._ensure_connected()
        
        try:
            value = self.client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Redis获取失败 {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        self._ensure_connected()
        
        try:
            # 序列化值
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            if ttl:
                self.client.setex(key, ttl, serialized_value)
            else:
                self.client.set(key, serialized_value)
            
            return True
        except Exception as e:
            logger.error(f"Redis设置失败 {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        self._ensure_connected()
        
        try:
            result = self.client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis删除失败 {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """按模式删除缓存项"""
        self._ensure_connected()
        
        try:
            # 获取匹配的键
            keys = self.client.keys(pattern)
            if keys:
                result = self.client.delete(*keys)
                return result
            return 0
        except Exception as e:
            logger.error(f"Redis按模式删除失败 {pattern}: {e}")
            return 0
    
    def clear(self) -> bool:
        """清除所有缓存"""
        self._ensure_connected()
        
        try:
            self.client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis清除失败: {e}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        self._ensure_connected()
        
        try:
            info = self.client.info()
            
            return {
                "backend": "RedisCache",
                "connected": True,
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "connected_clients": info.get("connected_clients", 0),
                "total_connections_received": info.get("total_connections_received", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
                "db_size": self.client.dbsize()
            }
        except Exception as e:
            logger.error(f"获取Redis指标失败: {e}")
            return {
                "backend": "RedisCache",
                "connected": False,
                "error": str(e)
            }
    
    def size(self) -> int:
        """获取缓存大小"""
        self._ensure_connected()
        try:
            return self.client.dbsize()
        except Exception:
            return 0


# 缓存后端工厂
class CacheBackendFactory:
    """缓存后端工厂"""
    
    @staticmethod
    def create_backend(backend_type: str = "auto", **kwargs) -> CacheBackend:
        """
        创建缓存后端
        
        Args:
            backend_type: 后端类型 (auto, memory, redis)
            **kwargs: 后端特定参数
            
        Returns:
            缓存后端实例
        """
        if backend_type == "auto":
            # 自动选择：先尝试Redis，失败则使用内存缓存
            try:
                return CacheBackendFactory.create_backend("redis", **kwargs)
            except Exception as e:
                logger.warning(f"Redis缓存不可用，回退到内存缓存: {e}")
                return CacheBackendFactory.create_backend("memory", **kwargs)
        
        elif backend_type == "memory":
            max_size = kwargs.get("max_size", 10000)
            return MemoryCache(max_size=max_size)
        
        elif backend_type == "redis":
            host = kwargs.get("host", "localhost")
            port = kwargs.get("port", 6379)
            db = kwargs.get("db", 0)
            password = kwargs.get("password", None)
            return RedisCache(host=host, port=port, db=db, password=password)
        
        else:
            raise ValueError(f"不支持的缓存后端类型: {backend_type}")
