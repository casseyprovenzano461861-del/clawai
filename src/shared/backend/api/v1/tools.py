# -*- coding: utf-8 -*-
"""
工具相关API接口
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from src.shared.backend.core.tool_manager import ToolManager

router = APIRouter(tags=["tools"])

# 初始化工具管理器
tool_manager = ToolManager()


@router.get("/", response_model=Dict[str, Any])
def get_tools():
    """获取所有工具列表"""
    if tool_manager is None:
        raise HTTPException(status_code=503, detail="工具管理器未初始化")
    tools_list = []
    try:
        for tool_name, tool_config in tool_manager.tools.items():
            tools_list.append({
                "name": tool_name,
                "description": tool_config.get("description", ""),
                "category": tool_config.get("category", "other"),
                "status": "available" if tool_manager.check_tool_installed(tool_name) else "unavailable",
                "required": tool_config.get("required", False),
                "version": tool_manager.get_tool_version(tool_name) if hasattr(tool_manager, "get_tool_version") else None,
            })
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取工具列表失败: {exc}")

    return {
        "message": "Tools API is working!",
        "tools_count": len(tool_manager.tools),
        "tools": tools_list
    }


@router.get("/categories", response_model=Dict[str, str])
def get_tool_categories():
    """获取工具类别"""
    return tool_manager.tool_categories


@router.get("/versions", response_model=Dict[str, Dict[str, Any]])
def get_tool_versions():
    """获取工具版本信息"""
    return tool_manager.get_tool_versions()


@router.get("/updates", response_model=List[Dict[str, Any]])
def check_tool_updates():
    """检查工具更新"""
    return tool_manager.check_all_updates()


@router.get("/scenarios", response_model=List[Dict[str, Any]])
def get_scan_scenarios():
    """获取支持的扫描场景"""
    return tool_manager.get_supported_scan_scenarios()


@router.post("/execute-scenario", response_model=Dict[str, str])
def execute_scan_scenario(scenario_name: str, params: Dict[str, Any]):
    """执行扫描场景"""
    try:
        result = tool_manager.execute_scan_scenario(scenario_name, params)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/execute-parallel", response_model=Dict[str, str])
def execute_tools_in_parallel(tasks: List[Dict[str, Any]]):
    """并行执行多个工具"""
    try:
        result = tool_manager.execute_tools_in_parallel(tasks)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status/{tool_name}", response_model=Dict[str, Any])
def get_tool_status(tool_name: str):
    """获取工具状态"""
    if tool_manager is None:
        raise HTTPException(status_code=503, detail="工具管理器未初始化")
    if tool_name not in tool_manager.tools:
        raise HTTPException(status_code=404, detail=f"工具 {tool_name} 不存在")
    
    return {
        "name": tool_name,
        "installed": tool_manager.check_tool_installed(tool_name),
        "version": tool_manager.get_tool_version(tool_name),
        "update_info": tool_manager.check_tool_update(tool_name)
    }
