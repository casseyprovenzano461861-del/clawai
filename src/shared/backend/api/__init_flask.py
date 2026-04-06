# -*- coding: utf-8 -*-
"""
API蓝图注册
注册所有API蓝图到Flask应用
"""

from flask import Flask

from backend.api.v1.attack import attack_bp
from backend.api.v1.auth import auth_bp
from backend.api.v1.health import health_bp
from backend.api.v1.workflow import workflow_bp
from backend.api.v1.cache import cache_bp


def register_blueprints(app: Flask):
    """
    注册所有API蓝图到Flask应用
    
    Args:
        app: Flask应用实例
    """
    # 注册API v1蓝图
    app.register_blueprint(attack_bp, url_prefix='/api/v1')
    app.register_blueprint(auth_bp, url_prefix='/api/v1')
    app.register_blueprint(health_bp, url_prefix='/api/v1')
    app.register_blueprint(workflow_bp, url_prefix='/api/v1')
    app.register_blueprint(cache_bp, url_prefix='/api/v1')
    
    # 注册根路径重定向
    @app.route('/')
    def index():
        return {
            "message": "ClawAI API Server",
            "version": "2.0.0",
            "architecture": "layered_architecture_v2",
            "endpoints": {
                "api_v1": "/api/v1",
                "health": "/api/v1/health",
                "attack": "/api/v1/attack",
                "auth": "/api/v1/auth",
                "cache": "/api/v1/cache"
            }
        }
    
    # 注册API文档
    @app.route('/api/docs')
    def api_docs():
        return {
            "api_version": "v1",
            "architecture": "layered_architecture_v2",
            "endpoints": {
                "GET /api/v1/health": "健康检查",
                "POST /api/v1/auth/login": "用户登录",
                "POST /api/v1/auth/register": "用户注册",
                "GET /api/v1/auth/me": "获取当前用户信息",
                "POST /api/v1/attack": "执行攻击（需要认证）",
                "GET /api/v1/attack/status/<task_id>": "获取攻击任务状态",
                "GET /api/v1/attack/history": "获取攻击历史",
                "GET /api/v1/attack/tools": "获取可用工具列表",
                "POST /api/v1/attack/quick-scan": "快速扫描（无需认证）",
                "GET /api/v1/workflows": "获取工作流模板列表（需要认证）",
                "GET /api/v1/workflows/<workflow_id>": "获取工作流模板详情（需要认证）",
                "POST /api/v1/workflows": "创建工作流模板（需要认证）",
                "PUT /api/v1/workflows/<workflow_id>": "更新工作流模板（需要认证）",
                "POST /api/v1/workflows/<workflow_id>/execute": "执行工作流（需要认证）",
                "GET /api/v1/executions": "获取执行记录列表（需要认证）",
                "GET /api/v1/executions/<execution_id>": "获取执行记录详情（需要认证）",
                "GET /api/v1/executions/<execution_id>/status": "获取执行状态（无需认证）",
                "DELETE /api/v1/executions/<execution_id>": "取消执行（需要认证）",
                "GET /api/v1/executions/<execution_id>/tasks": "获取执行的任务列表（需要认证）",
                "GET /api/v1/cache/stats": "获取缓存统计信息",
                "GET /api/v1/cache/endpoints": "获取所有端点缓存信息",
                "GET /api/v1/cache/endpoint/<endpoint>": "获取特定端点缓存详情",
                "POST /api/v1/cache/clear": "清除缓存",
                "GET /api/v1/cache/health": "缓存健康检查",
                "POST /api/v1/cache/cleanup": "清理过期缓存条目",
                "GET /api/v1/cache/config": "获取缓存配置信息"
            },
            "authentication": {
                "enabled": True,
                "type": "Bearer Token",
                "header": "Authorization: Bearer <token>"
            },
            "security_features": [
                "输入验证和清理",
                "JWT认证",
                "工具白名单",
                "命令注入防护",
                "权限控制",
                "速率限制",
                "安全头部"
            ],
            "workflow_features": [
                "工作流模板管理",
                "任务调度和状态管理",
                "结果存储和报告生成",
                "实时进度监控",
                "多阶段自动化测试流程",
                "可扩展的工作流定义"
            ],
            "cache_features": [
                "缓存统计和监控",
                "端点级缓存管理",
                "健康检查和优化建议",
                "过期条目自动清理",
                "命中率分析和报告"
            ]
        }
    
    return app