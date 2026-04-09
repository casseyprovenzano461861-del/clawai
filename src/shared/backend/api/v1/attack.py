# -*- coding: utf-8 -*-
"""
攻击API蓝图
处理攻击链生成和扫描请求
"""
# DEPRECATED: This Flask route module is deprecated.
# Use FastAPI routes in src/shared/backend/ instead.
import warnings
warnings.warn(
    "Flask API routes are deprecated. Use FastAPI routes instead.",
    DeprecationWarning,
    stacklevel=2,
)

from flask import Blueprint, request, jsonify, g
import time

from backend.shared.exceptions import ValidationError
from backend.app.middleware.auth import require_auth
from backend.services.attack_service import AttackService

# 创建蓝图
attack_bp = Blueprint('attack', __name__)


@attack_bp.route('/attack', methods=['POST'])
@require_auth
def attack_endpoint():
    """
    攻击链生成接口
    
    POST /api/v1/attack
    Body: {
        "target": "example.com",
        "use_real": true,
        "scan_options": {}
    }
    """
    try:
        # 解析请求数据
        data = request.json
        if not data or 'target' not in data:
            raise ValidationError("缺少目标参数", field="target")
        
        target = data['target']
        use_real = data.get('use_real', True)  # 默认使用真实执行
        scan_options = data.get('scan_options', {})
        
        # 获取当前用户
        username = g.user.get('username', 'anonymous') if hasattr(g, 'user') else 'anonymous'
        
        # 记录请求
        print(f"收到攻击请求: 用户={username}, 目标={target}, 使用真实执行={use_real}")
        
        # 创建攻击服务
        attack_service = AttackService()
        
        # 执行攻击
        result = attack_service.execute_attack(
            target=target,
            use_real=use_real,
            scan_options=scan_options,
            username=username
        )
        
        return jsonify(result)
        
    except ValidationError as e:
        # 验证错误直接抛出，由错误处理器处理
        raise e
    except Exception as e:
        # 其他错误
        from backend.shared.exceptions import create_error_response
        error_dict, status_code = create_error_response(e)
        return jsonify(error_dict), status_code


@attack_bp.route('/attack/status/<task_id>', methods=['GET'])
@require_auth
def attack_status(task_id: str):
    """
    获取攻击任务状态
    
    GET /api/v1/attack/status/<task_id>
    """
    try:
        # 创建攻击服务
        attack_service = AttackService()
        
        # 获取任务状态
        status = attack_service.get_task_status(task_id)
        
        return jsonify(status)
        
    except Exception as e:
        from backend.shared.exceptions import create_error_response
        error_dict, status_code = create_error_response(e)
        return jsonify(error_dict), status_code


@attack_bp.route('/attack/history', methods=['GET'])
@require_auth
def attack_history():
    """
    获取攻击历史
    
    GET /api/v1/attack/history
    Query Parameters:
        limit: 返回结果数量限制
        offset: 偏移量
    """
    try:
        # 获取查询参数
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
        # 获取当前用户ID
        user_id = g.user.get('id') if hasattr(g, 'user') else None
        
        # 创建攻击服务
        attack_service = AttackService()
        
        # 获取历史记录
        history = attack_service.get_attack_history(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            "history": history,
            "total": len(history),
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        from backend.shared.exceptions import create_error_response
        error_dict, status_code = create_error_response(e)
        return jsonify(error_dict), status_code


@attack_bp.route('/attack/tools', methods=['GET'])
def get_available_tools():
    """
    获取可用工具列表
    
    GET /api/v1/attack/tools
    """
    try:
        # 创建攻击服务
        attack_service = AttackService()
        
        # 获取可用工具
        tools = attack_service.get_available_tools()
        
        return jsonify({
            "tools": tools,
            "total": len(tools),
            "available_count": sum(1 for tool in tools.values() if tool.get("available", False))
        })
        
    except Exception as e:
        from backend.shared.exceptions import create_error_response
        error_dict, status_code = create_error_response(e)
        return jsonify(error_dict), status_code


@attack_bp.route('/attack/quick-scan', methods=['POST'])
def quick_scan():
    """
    快速扫描接口（无需认证）
    
    POST /api/v1/attack/quick-scan
    Body: {
        "target": "example.com"
    }
    """
    try:
        # 解析请求数据
        data = request.json
        if not data or 'target' not in data:
            raise ValidationError("缺少目标参数", field="target")
        
        target = data['target']
        
        # 限制快速扫描的目标类型
        if not (target.startswith('http://') or target.startswith('https://')):
            # 只允许HTTP/HTTPS目标进行快速扫描
            target = f"http://{target}"
        
        # 创建攻击服务
        attack_service = AttackService()
        
        # 执行快速扫描
        result = attack_service.execute_quick_scan(target)
        
        return jsonify(result)
        
    except Exception as e:
        from backend.shared.exceptions import create_error_response
        error_dict, status_code = create_error_response(e)
        return jsonify(error_dict), status_code