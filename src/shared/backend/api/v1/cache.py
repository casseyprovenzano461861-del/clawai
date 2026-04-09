# -*- coding: utf-8 -*-
"""
缓存统计API蓝图
提供缓存系统的统计信息和监控功能
"""
# DEPRECATED: This Flask route module is deprecated.
# Use FastAPI routes in src/shared/backend/ instead.
import warnings
warnings.warn(
    "Flask API routes are deprecated. Use FastAPI routes instead.",
    DeprecationWarning,
    stacklevel=2,
)

from flask import Blueprint, jsonify, request
import time
from typing import Dict, Any, Optional

# 导入缓存模块
try:
    from backend.utils.cache import (
        ResultCache,
        EndpointCache,
        endpoint_cache,
        cache_decorator,
        endpoint_cache_decorator
    )
    CACHE_AVAILABLE = True
except ImportError as e:
    print(f"缓存模块导入失败: {e}")
    CACHE_AVAILABLE = False

# 创建蓝图
cache_bp = Blueprint('cache', __name__)


def get_cache_status() -> Dict[str, Any]:
    """
    获取缓存系统状态
    
    Returns:
        缓存状态字典
    """
    if not CACHE_AVAILABLE:
        return {
            "available": False,
            "message": "缓存模块不可用",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    try:
        # 获取端点缓存统计信息
        stats = endpoint_cache.get_all_stats()
        
        # 计算总体统计
        total_hits = 0
        total_misses = 0
        total_entries = 0
        
        for endpoint_stat in stats.get("endpoints", {}).values():
            total_hits += endpoint_stat.get("hits", 0)
            total_misses += endpoint_stat.get("misses", 0)
            total_entries += endpoint_stat.get("total_entries", 0)
        
        total_requests = total_hits + total_misses
        hit_rate_percent = (total_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "available": True,
            "status": "active",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "stats": stats,
            "summary": {
                "total_endpoints": stats.get("total_endpoints", 0),
                "total_entries": total_entries,
                "total_hits": total_hits,
                "total_misses": total_misses,
                "hit_rate_percent": hit_rate_percent,
                "total_requests": total_requests
            }
        }
        
    except Exception as e:
        return {
            "available": True,
            "status": "error",
            "message": str(e),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }


@cache_bp.route('/cache/stats', methods=['GET'])
def cache_stats():
    """
    获取缓存统计信息
    
    GET /api/v1/cache/stats
    
    Returns:
        缓存统计信息的JSON响应
    """
    status = get_cache_status()
    
    if not status.get("available", False):
        return jsonify(status), 503  # Service Unavailable
    
    if status.get("status") == "error":
        return jsonify(status), 500
    
    return jsonify(status)


@cache_bp.route('/cache/endpoints', methods=['GET'])
def cache_endpoints():
    """
    获取所有端点缓存信息
    
    GET /api/v1/cache/endpoints
    
    Returns:
        端点缓存信息的JSON响应
    """
    if not CACHE_AVAILABLE:
        return jsonify({
            "available": False,
            "message": "缓存模块不可用",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 503
    
    try:
        stats = endpoint_cache.get_all_stats()
        
        # 格式化端点信息
        endpoints_info = []
        for endpoint, endpoint_stats in stats.get("endpoints", {}).items():
            endpoints_info.append({
                "endpoint": endpoint,
                "total_entries": endpoint_stats.get("total_entries", 0),
                "hits": endpoint_stats.get("hits", 0),
                "misses": endpoint_stats.get("misses", 0),
                "hit_rate": endpoint_stats.get("hit_rate", 0),
                "max_size": endpoint_stats.get("max_size", 0),
                "evictions": endpoint_stats.get("evictions", 0)
            })
        
        return jsonify({
            "available": True,
            "status": "success",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_endpoints": stats.get("total_endpoints", 0),
            "endpoints": endpoints_info
        })
        
    except Exception as e:
        return jsonify({
            "available": True,
            "status": "error",
            "message": str(e),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 500


@cache_bp.route('/cache/endpoint/<path:endpoint>', methods=['GET'])
def cache_endpoint_detail(endpoint: str):
    """
    获取特定端点缓存详情
    
    GET /api/v1/cache/endpoint/<endpoint>
    
    Args:
        endpoint: 端点路径
        
    Returns:
        端点缓存详情的JSON响应
    """
    if not CACHE_AVAILABLE:
        return jsonify({
            "available": False,
            "message": "缓存模块不可用",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 503
    
    try:
        stats = endpoint_cache.get_all_stats()
        endpoint_stats = stats.get("endpoints", {}).get(endpoint)
        
        if not endpoint_stats:
            return jsonify({
                "available": True,
                "status": "not_found",
                "message": f"端点 '{endpoint}' 的缓存信息不存在",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }), 404
        
        return jsonify({
            "available": True,
            "status": "success",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "endpoint": endpoint,
            "stats": endpoint_stats
        })
        
    except Exception as e:
        return jsonify({
            "available": True,
            "status": "error",
            "message": str(e),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 500


@cache_bp.route('/cache/clear', methods=['POST'])
def cache_clear():
    """
    清除缓存
    
    POST /api/v1/cache/clear
    
    Query Parameters:
        endpoint (可选): 要清除的端点路径
        
    Returns:
        清除操作结果的JSON响应
    """
    if not CACHE_AVAILABLE:
        return jsonify({
            "available": False,
            "message": "缓存模块不可用",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 503
    
    try:
        endpoint_to_clear = request.args.get('endpoint', None)
        
        if endpoint_to_clear:
            # 清除特定端点的缓存
            if endpoint_to_clear in endpoint_cache.endpoint_caches:
                cache_instance = endpoint_cache.endpoint_caches[endpoint_to_clear]
                cleared_count = len(cache_instance.cache)
                cache_instance.clear()
                message = f"清除了端点 '{endpoint_to_clear}' 的缓存，共 {cleared_count} 个条目"
            else:
                return jsonify({
                    "available": True,
                    "status": "not_found",
                    "message": f"端点 '{endpoint_to_clear}' 的缓存不存在",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }), 404
        else:
            # 清除所有端点缓存
            total_cleared = 0
            for endpoint, cache_instance in endpoint_cache.endpoint_caches.items():
                total_cleared += len(cache_instance.cache)
                cache_instance.clear()
            
            message = f"清除了所有端点缓存，共 {total_cleared} 个条目"
        
        return jsonify({
            "available": True,
            "status": "success",
            "message": message,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        return jsonify({
            "available": True,
            "status": "error",
            "message": str(e),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 500


@cache_bp.route('/cache/health', methods=['GET'])
def cache_health():
    """
    缓存健康检查
    
    GET /api/v1/cache/health
    
    Returns:
        缓存健康状态的JSON响应
    """
    status = get_cache_status()
    
    if not status.get("available", False):
        return jsonify({
            "status": "unavailable",
            "message": "缓存系统不可用",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 503
    
    if status.get("status") == "error":
        return jsonify({
            "status": "unhealthy",
            "message": status.get("message", "缓存系统错误"),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 500
    
    # 检查缓存性能
    hit_rate = status.get("summary", {}).get("hit_rate_percent", 0)
    total_requests = status.get("summary", {}).get("total_requests", 0)
    
    health_status = "healthy"
    issues = []
    
    if total_requests > 0 and hit_rate < 50:
        health_status = "degraded"
        issues.append(f"缓存命中率较低: {hit_rate:.1f}%")
    
    if status.get("summary", {}).get("total_entries", 0) == 0 and total_requests > 10:
        health_status = "degraded"
        issues.append("缓存条目数为0，但请求次数较多，可能缓存未生效")
    
    return jsonify({
        "status": health_status,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "metrics": {
            "hit_rate_percent": hit_rate,
            "total_requests": total_requests,
            "total_endpoints": status.get("summary", {}).get("total_endpoints", 0),
            "total_entries": status.get("summary", {}).get("total_entries", 0)
        },
        "issues": issues,
        "recommendations": generate_health_recommendations(health_status, issues, hit_rate)
    })


@cache_bp.route('/cache/cleanup', methods=['POST'])
def cache_cleanup():
    """
    清理过期缓存条目
    
    POST /api/v1/cache/cleanup
    
    Returns:
        清理操作结果的JSON响应
    """
    if not CACHE_AVAILABLE:
        return jsonify({
            "available": False,
            "message": "缓存模块不可用",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 503
    
    try:
        total_cleaned = 0
        
        for endpoint, cache_instance in endpoint_cache.endpoint_caches.items():
            cleaned = cache_instance.cleanup()
            total_cleaned += cleaned
        
        return jsonify({
            "available": True,
            "status": "success",
            "message": f"清理了 {total_cleaned} 个过期缓存条目",
            "cleaned_count": total_cleaned,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        return jsonify({
            "available": True,
            "status": "error",
            "message": str(e),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 500


def generate_health_recommendations(health_status: str, issues: list, hit_rate: float) -> list:
    """
    生成健康优化建议
    
    Args:
        health_status: 健康状态
        issues: 问题列表
        hit_rate: 命中率
        
    Returns:
        建议列表
    """
    recommendations = []
    
    if health_status == "healthy":
        recommendations.append("缓存系统运行正常")
        if hit_rate > 80:
            recommendations.append("缓存命中率优秀，继续保持")
        else:
            recommendations.append(f"当前命中率: {hit_rate:.1f}%，建议监控缓存使用情况")
    elif health_status == "degraded":
        recommendations.append("缓存系统存在性能问题，建议：")
        for issue in issues:
            recommendations.append(f"  - 解决: {issue}")
        
        if hit_rate < 50:
            recommendations.append("  - 检查端点缓存配置，可能需要调整TTL")
            recommendations.append("  - 确认缓存装饰器是否正确应用")
            recommendations.append("  - 考虑增加缓存容量")
        
        recommendations.append("  - 增加监控频率")
        recommendations.append("  - 定期清理过期缓存")
    else:
        recommendations.append("缓存系统异常，建议：")
        recommendations.append("  - 检查缓存配置")
        recommendations.append("  - 重启应用服务")
        recommendations.append("  - 查看应用日志排查问题")
    
    return recommendations


@cache_bp.route('/cache/config', methods=['GET'])
def cache_config():
    """
    获取缓存配置信息
    
    GET /api/v1/cache/config
    
    Returns:
        缓存配置信息的JSON响应
    """
    if not CACHE_AVAILABLE:
        return jsonify({
            "available": False,
            "message": "缓存模块不可用",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 503
    
    try:
        config_info = {
            "available": True,
            "status": "success",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "default_configs": endpoint_cache.default_configs,
            "active_endpoints": list(endpoint_cache.endpoint_caches.keys()),
            "cache_classes": {
                "ResultCache": "基础缓存类，支持TTL和LRU淘汰",
                "EndpointCache": "API端点专用缓存管理",
                "cache_decorator": "通用缓存装饰器",
                "endpoint_cache_decorator": "端点缓存装饰器"
            }
        }
        
        return jsonify(config_info)
        
    except Exception as e:
        return jsonify({
            "available": True,
            "status": "error",
            "message": str(e),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 500
