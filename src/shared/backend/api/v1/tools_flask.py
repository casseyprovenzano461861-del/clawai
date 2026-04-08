# -*- coding: utf-8 -*-
"""
工具相关API接口（Flask版本）
"""

from flask import Blueprint, jsonify, request
from typing import List, Dict, Any
from src.shared.backend.core.tool_manager import ToolManager

# 创建蓝图
tools_bp = Blueprint('tools', __name__)

# 初始化工具管理器
tool_manager = ToolManager()


@tools_bp.route('/', methods=['GET'])
def get_tools():
    """获取所有工具列表"""
    tools = []
    for tool_name, tool_info in tool_manager.tools.items():
        tools.append({
            "name": tool_name,
            "description": tool_info["description"],
            "category": tool_info.get("category", "unknown"),
            "params": tool_info.get("params", [])
        })
    return jsonify(tools)


@tools_bp.route('/categories', methods=['GET'])
def get_tool_categories():
    """获取工具类别"""
    return jsonify(tool_manager.tool_categories)


@tools_bp.route('/versions', methods=['GET'])
def get_tool_versions():
    """获取工具版本信息"""
    return jsonify(tool_manager.get_tool_versions())


@tools_bp.route('/updates', methods=['GET'])
def check_tool_updates():
    """检查工具更新"""
    return jsonify(tool_manager.check_all_updates())


@tools_bp.route('/scenarios', methods=['GET'])
def get_scan_scenarios():
    """获取支持的扫描场景"""
    return jsonify(tool_manager.get_supported_scan_scenarios())


@tools_bp.route('/execute-scenario', methods=['POST'])
def execute_scan_scenario():
    """执行扫描场景"""
    try:
        data = request.get_json()
        scenario_name = data.get('scenario_name')
        params = data.get('params', {})
        
        if not scenario_name:
            return jsonify({"error": "缺少场景名称"}), 400
        
        result = tool_manager.execute_scan_scenario(scenario_name, params)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@tools_bp.route('/execute-parallel', methods=['POST'])
def execute_tools_in_parallel():
    """并行执行多个工具"""
    try:
        data = request.get_json()
        tasks = data.get('tasks', [])
        
        if not tasks:
            return jsonify({"error": "缺少任务列表"}), 400
        
        result = tool_manager.execute_tools_in_parallel(tasks)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@tools_bp.route('/status/<tool_name>', methods=['GET'])
def get_tool_status(tool_name):
    """获取工具状态"""
    if tool_name not in tool_manager.tools:
        return jsonify({"error": f"工具 {tool_name} 不存在"}), 404
    
    return jsonify({
        "name": tool_name,
        "installed": tool_manager.check_tool_installed(tool_name),
        "version": tool_manager.get_tool_version(tool_name),
        "update_info": tool_manager.check_tool_update(tool_name)
    })
