# -*- coding: utf-8 -*-
"""
工作流API蓝图
处理工作流管理和执行请求
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
from typing import Dict, Any, Optional

from backend.shared.exceptions import ValidationError
from backend.app.middleware.auth import require_auth
from backend.infrastructure.workflow.workflow_manager import get_workflow_manager

# 创建蓝图
workflow_bp = Blueprint('workflow', __name__)


@workflow_bp.route('/workflows', methods=['GET'])
@require_auth
def list_workflows():
    """
    获取工作流模板列表
    
    GET /api/v1/workflows
    
    Query Parameters:
        limit: 返回结果数量限制
        offset: 偏移量
    
    Returns:
        工作流列表
    """
    try:
        # 获取查询参数
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        # 获取工作流管理器
        wm = get_workflow_manager()
        
        # 获取工作流列表
        workflows = wm.list_workflows()
        
        # 应用分页
        start_idx = offset
        end_idx = offset + limit
        paginated_workflows = workflows[start_idx:end_idx]
        
        return jsonify({
            "workflows": paginated_workflows,
            "total": len(workflows),
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        from backend.shared.exceptions import create_error_response
        error_dict, status_code = create_error_response(e)
        return jsonify(error_dict), status_code


@workflow_bp.route('/workflows/<workflow_id>', methods=['GET'])
@require_auth
def get_workflow(workflow_id: str):
    """
    获取工作流模板详情
    
    GET /api/v1/workflows/<workflow_id>
    
    Returns:
        工作流详情
    """
    try:
        # 获取工作流管理器
        wm = get_workflow_manager()
        
        # 获取工作流定义
        workflow = wm.get_workflow(workflow_id)
        
        if not workflow:
            from backend.shared.exceptions import ResourceNotFoundError
            raise ResourceNotFoundError(f"工作流不存在: {workflow_id}")
        
        # 返回工作流详情
        return jsonify({
            "id": workflow.id,
            "name": workflow.name,
            "version": workflow.version,
            "description": workflow.description,
            "phases": workflow.phases,
            "steps": {step_id: step.to_dict() for step_id, step in workflow.steps.items()},
            "execution_order": workflow.get_execution_order(),
            "step_count": len(workflow.steps)
        })
        
    except Exception as e:
        from backend.shared.exceptions import create_error_response
        error_dict, status_code = create_error_response(e)
        return jsonify(error_dict), status_code


@workflow_bp.route('/workflows', methods=['POST'])
@require_auth
def create_workflow():
    """
    创建工作流模板
    
    POST /api/v1/workflows
    
    Body: {
        "id": "custom_workflow",
        "name": "自定义工作流",
        "version": "1.0",
        "description": "自定义工作流描述",
        "phases": [...]
    }
    
    Returns:
        创建的工作流ID
    """
    try:
        # 解析请求数据
        data = request.json
        if not data:
            raise ValidationError("缺少请求数据")
        
        # 验证必要字段
        if 'name' not in data:
            raise ValidationError("缺少工作流名称", field="name")
        
        if 'phases' not in data or not isinstance(data['phases'], list):
            raise ValidationError("缺少或无效的阶段定义", field="phases")
        
        # 获取工作流管理器
        wm = get_workflow_manager()
        
        # 创建工作流
        workflow_id = wm.create_workflow(data)
        
        return jsonify({
            "id": workflow_id,
            "message": "工作流创建成功",
            "success": True
        }), 201
        
    except Exception as e:
        from backend.shared.exceptions import create_error_response
        error_dict, status_code = create_error_response(e)
        return jsonify(error_dict), status_code


@workflow_bp.route('/workflows/<workflow_id>', methods=['PUT'])
@require_auth
def update_workflow(workflow_id: str):
    """
    更新工作流模板
    
    PUT /api/v1/workflows/<workflow_id>
    
    Body: {
        "name": "更新后的工作流",
        "version": "2.0",
        "description": "更新后的描述",
        "phases": [...]
    }
    
    Returns:
        更新结果
    """
    try:
        # 解析请求数据
        data = request.json
        if not data:
            raise ValidationError("缺少请求数据")
        
        # 获取工作流管理器
        wm = get_workflow_manager()
        
        # 检查工作流是否存在
        existing_workflow = wm.get_workflow(workflow_id)
        if not existing_workflow:
            from backend.shared.exceptions import ResourceNotFoundError
            raise ResourceNotFoundError(f"工作流不存在: {workflow_id}")
        
        # 合并现有数据和更新数据
        # 实际应用中，应该从数据库获取原始数据，然后合并
        # 这里简化为直接创建新工作流（会替换原有）
        update_data = {
            "id": workflow_id,
            "name": data.get("name", existing_workflow.name),
            "version": data.get("version", existing_workflow.version),
            "description": data.get("description", existing_workflow.description),
            "phases": data.get("phases", existing_workflow.phases)
        }
        
        # 更新工作流
        updated_id = wm.create_workflow(update_data)
        
        return jsonify({
            "id": updated_id,
            "message": "工作流更新成功",
            "success": True
        })
        
    except Exception as e:
        from backend.shared.exceptions import create_error_response
        error_dict, status_code = create_error_response(e)
        return jsonify(error_dict), status_code


@workflow_bp.route('/workflows/<workflow_id>/execute', methods=['POST'])
@require_auth
def execute_workflow(workflow_id: str):
    """
    执行工作流
    
    POST /api/v1/workflows/<workflow_id>/execute
    
    Body: {
        "target": "example.com",
        "extra_params": {}
    }
    
    Returns:
        执行ID
    """
    try:
        # 解析请求数据
        data = request.json
        if not data or 'target' not in data:
            raise ValidationError("缺少目标参数", field="target")
        
        target = data['target']
        extra_params = data.get('extra_params', {})
        
        # 验证目标
        if not target or not isinstance(target, str):
            raise ValidationError("目标必须是有效的字符串", field="target")
        
        if len(target) > 255:
            raise ValidationError("目标地址过长", field="target")
        
        # 获取当前用户
        username = g.user.get('username', 'anonymous') if hasattr(g, 'user') else 'anonymous'
        
        # 获取工作流管理器
        wm = get_workflow_manager()
        
        # 执行工作流
        execution_id = wm.execute_workflow(
            workflow_id=workflow_id,
            target=target,
            created_by=username,
            extra_params=extra_params
        )
        
        return jsonify({
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "target": target,
            "message": "工作流执行已启动",
            "status_url": f"/api/v1/executions/{execution_id}"
        })
        
    except Exception as e:
        from backend.shared.exceptions import create_error_response
        error_dict, status_code = create_error_response(e)
        return jsonify(error_dict), status_code


@workflow_bp.route('/executions', methods=['GET'])
@require_auth
def list_executions():
    """
    获取执行记录列表
    
    GET /api/v1/executions
    
    Query Parameters:
        workflow_id: 工作流ID过滤
        status: 状态过滤
        limit: 返回结果数量限制
        offset: 偏移量
    
    Returns:
        执行记录列表
    """
    try:
        # 获取查询参数
        workflow_id = request.args.get('workflow_id')
        status = request.args.get('status')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        # 获取工作流管理器
        wm = get_workflow_manager()
        
        # 获取执行记录
        executions = wm.list_executions(
            workflow_id=workflow_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        # 获取当前用户
        username = g.user.get('username', 'anonymous') if hasattr(g, 'user') else 'anonymous'
        
        # 如果不是管理员，只返回当前用户的执行记录
        # 这里简化处理，实际应用中应该根据用户权限过滤
        user_executions = [e for e in executions if e.get("created_by") == username]
        
        return jsonify({
            "executions": user_executions,
            "total": len(user_executions),
            "limit": limit,
            "offset": offset,
            "filtered_by": {
                "workflow_id": workflow_id,
                "status": status,
                "user": username
            }
        })
        
    except Exception as e:
        from backend.shared.exceptions import create_error_response
        error_dict, status_code = create_error_response(e)
        return jsonify(error_dict), status_code


@workflow_bp.route('/executions/<execution_id>', methods=['GET'])
@require_auth
def get_execution(execution_id: str):
    """
    获取执行记录详情
    
    GET /api/v1/executions/<execution_id>
    
    Returns:
        执行记录详情
    """
    try:
        # 获取工作流管理器
        wm = get_workflow_manager()
        
        # 获取执行状态
        status = wm.get_execution_status(execution_id)
        
        if status["status"] == "not_found":
            from backend.shared.exceptions import ResourceNotFoundError
            raise ResourceNotFoundError(f"执行记录不存在: {execution_id}")
        
        # 检查权限（当前用户只能查看自己的执行记录）
        current_user = g.user.get('username', 'anonymous') if hasattr(g, 'user') else 'anonymous'
        execution_user = status.get("created_by", "anonymous")
        
        if current_user != execution_user:
            from backend.shared.exceptions import PermissionDeniedError
            raise PermissionDeniedError("无权访问此执行记录")
        
        return jsonify(status)
        
    except Exception as e:
        from backend.shared.exceptions import create_error_response
        error_dict, status_code = create_error_response(e)
        return jsonify(error_dict), status_code


@workflow_bp.route('/executions/<execution_id>/status', methods=['GET'])
def get_execution_status(execution_id: str):
    """
    获取执行状态（无需认证）
    
    GET /api/v1/executions/<execution_id>/status
    
    Returns:
        执行状态
    """
    try:
        # 获取工作流管理器
        wm = get_workflow_manager()
        
        # 获取执行状态
        status = wm.get_execution_status(execution_id)
        
        if status["status"] == "not_found":
            from backend.shared.exceptions import ResourceNotFoundError
            raise ResourceNotFoundError(f"执行记录不存在: {execution_id}")
        
        # 只返回基本信息，不包含敏感数据
        public_status = {
            "execution_id": status["execution_id"],
            "workflow_id": status["workflow_id"],
            "target": status["target"],
            "status": status["status"],
            "progress": status["progress"],
            "tasks_count": status["tasks_count"],
            "completed_tasks": status["completed_tasks"],
            "failed_tasks": status["failed_tasks"]
        }
        
        return jsonify(public_status)
        
    except Exception as e:
        from backend.shared.exceptions import create_error_response
        error_dict, status_code = create_error_response(e)
        return jsonify(error_dict), status_code


@workflow_bp.route('/executions/<execution_id>', methods=['DELETE'])
@require_auth
def cancel_execution(execution_id: str):
    """
    取消执行
    
    DELETE /api/v1/executions/<execution_id>
    
    Returns:
        取消结果
    """
    try:
        # 获取工作流管理器
        wm = get_workflow_manager()
        
        # 首先检查执行记录是否存在
        status = wm.get_execution_status(execution_id)
        if status["status"] == "not_found":
            from backend.shared.exceptions import ResourceNotFoundError
            raise ResourceNotFoundError(f"执行记录不存在: {execution_id}")
        
        # 检查权限
        current_user = g.user.get('username', 'anonymous') if hasattr(g, 'user') else 'anonymous'
        execution_user = status.get("created_by", "anonymous")
        
        if current_user != execution_user:
            from backend.shared.exceptions import PermissionDeniedError
            raise PermissionDeniedError("无权取消此执行记录")
        
        # 取消执行
        success = wm.cancel_execution(execution_id)
        
        return jsonify({
            "execution_id": execution_id,
            "success": success,
            "message": "执行已取消" if success else "无法取消执行"
        })
        
    except Exception as e:
        from backend.shared.exceptions import create_error_response
        error_dict, status_code = create_error_response(e)
        return jsonify(error_dict), status_code


@workflow_bp.route('/executions/<execution_id>/tasks', methods=['GET'])
@require_auth
def get_execution_tasks(execution_id: str):
    """
    获取执行的任务列表
    
    GET /api/v1/executions/<execution_id>/tasks
    
    Returns:
        任务列表
    """
    try:
        # 获取工作流管理器
        wm = get_workflow_manager()
        
        # 检查执行记录是否存在
        status = wm.get_execution_status(execution_id)
        if status["status"] == "not_found":
            from backend.shared.exceptions import ResourceNotFoundError
            raise ResourceNotFoundError(f"执行记录不存在: {execution_id}")
        
        # 检查权限
        current_user = g.user.get('username', 'anonymous') if hasattr(g, 'user') else 'anonymous'
        execution_user = status.get("created_by", "anonymous")
        
        if current_user != execution_user:
            from backend.shared.exceptions import PermissionDeniedError
            raise PermissionDeniedError("无权访问此执行记录")
        
        # 从数据库直接获取任务
        db = wm.db
        tasks = db.get_execution_tasks(execution_id)
        
        # 获取任务详情
        detailed_tasks = []
        for task in tasks:
            task_id = task["id"]
            task_detail = db.get_task(task_id)
            if task_detail:
                detailed_tasks.append(task_detail)
        
        return jsonify({
            "execution_id": execution_id,
            "tasks": detailed_tasks,
            "total": len(detailed_tasks)
        })
        
    except Exception as e:
        from backend.shared.exceptions import create_error_response
        error_dict, status_code = create_error_response(e)
        return jsonify(error_dict), status_code