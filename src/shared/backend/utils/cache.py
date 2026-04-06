# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
缓存模块 - 提供简单高效的内存缓存功能
支持TTL、LRU淘汰策略、统计信息
"""

import time
import threading
from typing import Dict, Any, Optional, Tuple
from collections import OrderedDict
import hashlib
import json

class ResultCache:
    """结果缓存类，支持TTL和LRU淘汰策略"""
    
    def __init__(self, max_size: int = 100, default_ttl: int = 300):
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认缓存时间（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.lock = threading.RLock()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0,
            "expired": 0
        }
    
    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = {
            "args": args,
            "kwargs": kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值或None（如果不存在或已过期）
        """
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # 检查是否过期
                if time.time() < entry["expires_at"]:
                    # 移动到最近使用位置
                    self.cache.move_to_end(key)
                    self.stats["hits"] += 1
                    return entry["value"]
                else:
                    # 已过期，删除
                    del self.cache[key]
                    self.stats["expired"] += 1
                    self.stats["misses"] += 1
                    return None
            else:
                self.stats["misses"] += 1
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 缓存时间（秒），None使用默认TTL
        """
        if ttl is None:
            ttl = self.default_ttl
        
        with self.lock:
            # 如果缓存已满，淘汰最旧的条目
            if len(self.cache) >= self.max_size:
                # LRU淘汰：删除第一个（最久未使用）的条目
                if self.cache:
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                    self.stats["evictions"] += 1
            
            self.cache[key] = {
                "value": value,
                "expires_at": time.time() + ttl,
                "created_at": time.time(),
                "ttl": ttl
            }
            # 移动到最近使用位置
            self.cache.move_to_end(key)
            self.stats["sets"] += 1
    
    def delete(self, key: str) -> bool:
        """
        删除缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功删除
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.stats["evictions"] += len(self.cache)
    
    def cleanup(self) -> int:
        """
        清理过期条目
        
        Returns:
            清理的过期条目数量
        """
        cleaned = 0
        now = time.time()
        
        with self.lock:
            expired_keys = []
            for key, entry in self.cache.items():
                if now >= entry["expires_at"]:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
                cleaned += 1
            
            self.stats["expired"] += cleaned
        
        return cleaned
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self.lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            now = time.time()
            expired_count = sum(1 for entry in self.cache.values() if now >= entry["expires_at"])
            
            return {
                "total_entries": len(self.cache),
                "expired_entries": expired_count,
                "max_size": self.max_size,
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "sets": self.stats["sets"],
                "evictions": self.stats["evictions"],
                "expired_removed": self.stats["expired"],
                "hit_rate": hit_rate,
                "memory_usage_estimate": len(self.cache) * 100  # 粗略估计每个条目100字节
            }
    
    def get_entries(self, limit: int = 10) -> Dict[str, Dict[str, Any]]:
        """
        获取缓存条目信息
        
        Args:
            limit: 返回条目数量限制
            
        Returns:
            缓存条目信息
        """
        entries = {}
        now = time.time()
        
        with self.lock:
            for i, (key, entry) in enumerate(self.cache.items()):
                if i >= limit:
                    break
                
                entries[key] = {
                    "created_at": entry["created_at"],
                    "expires_at": entry["expires_at"],
                    "ttl": entry["ttl"],
                    "remaining_ttl": max(0, entry["expires_at"] - now),
                    "value_type": type(entry["value"]).__name__
                }
        
        return entries


def cache_decorator(ttl: Optional[int] = None, max_size: int = 100):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存时间（秒）
        max_size: 缓存最大条目数
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        cache = ResultCache(max_size=max_size, default_ttl=ttl or 300)
        
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = cache._generate_key(func.__name__, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                # 标记为缓存命中
                if isinstance(cached_result, dict):
                    cached_result["_cache"] = {
                        "hit": True,
                        "cached_at": cache.cache[cache_key]["created_at"],
                        "key": cache_key[:8]  # 显示前8位用于调试
                    }
                return cached_result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            cache.set(cache_key, result, ttl)
            
            # 标记为缓存未命中
            if isinstance(result, dict):
                result["_cache"] = {
                    "hit": False,
                    "key": cache_key[:8]
                }
            
            return result
        
        # 添加缓存管理方法到包装函数
        wrapper.cache = cache
        wrapper.clear_cache = cache.clear
        wrapper.get_cache_stats = cache.get_stats
        wrapper.cleanup_cache = cache.cleanup
        
        return wrapper
    
    return decorator


class EndpointCache:
    """API端点专用缓存"""
    
    def __init__(self):
        self.endpoint_caches: Dict[str, ResultCache] = {}
        self.default_configs = {
            "/health": {"ttl": 30, "max_size": 5},          # 健康检查：30秒
            "/health/detailed": {"ttl": 60, "max_size": 10}, # 详细健康检查：60秒
            "/api-docs": {"ttl": 300, "max_size": 5},       # API文档：5分钟
            "/health/security": {"ttl": 60, "max_size": 5}, # 安全健康检查：60秒
            "default": {"ttl": 30, "max_size": 10}          # 默认配置
        }
    
    def get_cache_for_endpoint(self, endpoint: str) -> ResultCache:
        """获取端点对应的缓存实例"""
        if endpoint not in self.endpoint_caches:
            config = self.default_configs.get(endpoint, self.default_configs["default"])
            self.endpoint_caches[endpoint] = ResultCache(
                max_size=config["max_size"],
                default_ttl=config["ttl"]
            )
        
        return self.endpoint_caches[endpoint]
    
    def get(self, endpoint: str, key_data: Any) -> Optional[Any]:
        """获取端点缓存值"""
        cache = self.get_cache_for_endpoint(endpoint)
        cache_key = cache._generate_key(key_data)
        return cache.get(cache_key)
    
    def set(self, endpoint: str, key_data: Any, value: Any, ttl: Optional[int] = None) -> None:
        """设置端点缓存值"""
        cache = self.get_cache_for_endpoint(endpoint)
        cache_key = cache._generate_key(key_data)
        cache.set(cache_key, value, ttl)
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有端点缓存统计"""
        stats = {}
        for endpoint, cache in self.endpoint_caches.items():
            stats[endpoint] = cache.get_stats()
        
        return {
            "total_endpoints": len(self.endpoint_caches),
            "endpoints": stats
        }


# 全局端点缓存实例
endpoint_cache = EndpointCache()


import functools

def endpoint_cache_decorator(endpoint: str, ttl: Optional[int] = None):
    """
    API端点缓存装饰器
    
    Args:
        endpoint: 端点路径
        ttl: 自定义TTL（秒）
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键数据
            key_data = {
                "args": args,
                "kwargs": kwargs,
                "request_data": None
            }
            
            # 尝试从请求中获取数据（如果可用）
            try:
                from flask import request
                if request.method in ["POST", "PUT", "PATCH"]:
                    key_data["request_data"] = request.get_json(silent=True)
                elif request.method == "GET":
                    key_data["request_data"] = request.args.to_dict()
            except ImportError:
                pass
            
            # 尝试从缓存获取
            cached_result = endpoint_cache.get(endpoint, key_data)
            if cached_result is not None:
                # 标记为缓存命中
                if isinstance(cached_result, dict):
                    cached_result["_cache"] = {
                        "hit": True,
                        "endpoint": endpoint,
                        "timestamp": time.time()
                    }
                return cached_result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果（只缓存成功响应）
            should_cache = True
            if isinstance(result, tuple) and len(result) == 2:
                response, status_code = result
                should_cache = 200 <= status_code < 300
                if should_cache:
                    endpoint_cache.set(endpoint, key_data, result, ttl)
            elif isinstance(result, dict):
                endpoint_cache.set(endpoint, key_data, result, ttl)
            
            # 标记为缓存未命中
            if isinstance(result, dict) and should_cache:
                result["_cache"] = {
                    "hit": False,
                    "endpoint": endpoint
                }
            
            return result
        
        return wrapper
    
    return decorator


if __name__ == "__main__":
    # 测试缓存功能
    cache = ResultCache(max_size=5, default_ttl=10)
    
    # 测试设置和获取
    cache.set("key1", "value1")
    print(f"获取key1: {cache.get('key1')}")  # 应该返回value1
    
    # 测试过期
    cache.set("key2", "value2", ttl=1)
    time.sleep(1.5)
    print(f"获取过期的key2: {cache.get('key2')}")  # 应该返回None
    
    # 测试LRU淘汰
    for i in range(10):
        cache.set(f"test_key_{i}", f"test_value_{i}")
    
    print(f"缓存条目数: {len(cache.cache)}")  # 应该最多5个
    print(f"缓存统计: {cache.get_stats()}")
    
    # 测试装饰器
    @cache_decorator(ttl=5)
    def expensive_operation(x, y):
        time.sleep(0.1)  # 模拟耗时操作
        return {"result": x + y, "computed_at": time.time()}
    
    print("\n测试缓存装饰器:")
    start = time.time()
    result1 = expensive_operation(1, 2)
    print(f"第一次执行: {result1}, 耗时: {time.time() - start:.3f}s")
    
    start = time.time()
    result2 = expensive_operation(1, 2)
    print(f"第二次执行（应命中缓存）: {result2}, 耗时: {time.time() - start:.3f}s")
    
    print(f"缓存命中: {result2.get('_cache', {}).get('hit', False)}")
    
    # 测试端点缓存
    print("\n测试端点缓存:")
    endpoint_cache.set("/health", {}, {"status": "healthy"})
    cached = endpoint_cache.get("/health", {})
    print(f"端点缓存获取: {cached}")