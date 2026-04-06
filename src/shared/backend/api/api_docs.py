# -*- coding: utf-8 -*-
"""
API文档蓝图
"""

from flask import Blueprint, jsonify

# 创建蓝图
docs_bp = Blueprint('docs', __name__)


@docs_bp.route('/docs', methods=['GET'])
def api_docs():
    """
    API文档
    
    GET /api/docs
    """
    endpoints = {
        "POST /api/v1/auth/login": {
            "description": "用户登录",
            "parameters": {
                "username": "用户名",
                "password": "密码"
            },
            "response": "包含访问令牌和用户信息的JSON数据"
        },
        "POST /api/v1/auth/register": {
            "description": "用户注册",
            "parameters": {
                "username": "用户名",
                "password": "密码",
                "email": "邮箱"
            },
            "response": "注册成功信息和用户数据"
        },
        "POST /api/v1/attack": {
            "description": "生成攻击链",
            "authentication": "需要Bearer令牌",
            "parameters": {
                "target": "目标IP/域名/URL",
                "use_real": "是否使用真实执行（可选，默认true）",
                "scan_options": "扫描选项（可选）"
            },
            "response": "包含攻击链、决策分析、目标分析的JSON数据"
        },
        "POST /api/v1/attack/quick-scan": {
            "description": "快速扫描（无需认证）",
            "parameters": {
                "target": "目标URL"
            },
            "response": "快速扫描结果"
        },
        "GET /api/v1/attack/status/<task_id>": {
            "description": "获取攻击任务状态",
            "authentication": "需要Bearer令牌",
            "response": "任务状态信息"
        },
        "GET /api/v1/attack/history": {
            "description": "获取攻击历史",
            "authentication": "需要Bearer令牌",
            "parameters": {
                "limit": "返回结果数量限制（可选，默认10）",
                "offset": "偏移量（可选，默认0）"
            },
            "response": "攻击历史列表"
        },
        "GET /api/v1/attack/tools": {
            "description": "获取可用工具列表",
            "response": "工具信息字典"
        },
        "GET /api/v1/health": {
            "description": "基础健康检查",
            "response": "服务状态信息"
        },
        "GET /api/v1/health/detailed": {
            "description": "详细健康检查",
            "response": "包含系统信息的详细健康报告"
        },
        "GET /api/v1/health/architecture": {
            "description": "架构健康检查",
            "response": "新架构状态信息"
        },
        "GET /api/v1/knowledge-graph/graph": {
            "description": "获取知识图谱数据",
            "parameters": {
                "filter_type": "过滤节点类型 (可选)",
                "search": "搜索关键词 (可选)",
                "limit": "返回节点数量限制 (可选)"
            },
            "response": "完整的知识图谱数据，包含节点和边"
        },
        "GET /api/v1/knowledge-graph/stats": {
            "description": "获取知识图谱统计信息",
            "response": "知识图谱的统计信息"
        },
        "GET /api/v1/knowledge-graph/node/<node_id>": {
            "description": "获取节点详细信息",
            "response": "节点的详细信息"
        },
        "GET /api/v1/knowledge-graph/edge/<edge_id>": {
            "description": "获取边详细信息",
            "response": "边的详细信息"
        },
        "GET /api/v1/knowledge-graph/search": {
            "description": "搜索知识图谱",
            "parameters": {
                "q": "搜索关键词",
                "type": "搜索类型 (node, edge, all) 默认: all"
            },
            "response": "搜索结果"
        },
        "GET /api/v1/knowledge-graph/health": {
            "description": "知识图谱服务健康检查",
            "response": "服务健康状态"
        }
    }
    
    return jsonify({
        "service": "ClawAI API Server",
        "version": "2.0.0",
        "architecture": "layered_architecture_v2",
        "description": "基于分层架构重构的安全评估平台",
        "authentication": {
            "enabled": True,
            "method": "JWT Bearer Token",
            "endpoints": ["/api/v1/auth/login", "/api/v1/auth/register"]
        },
        "endpoints": endpoints,
        "features": [
            "真实工具执行能力",
            "智能攻击链生成",
            "统一错误处理",
            "标准化的工具适配器",
            "清晰的架构分层",
            "减少模拟数据依赖"
        ]
    })