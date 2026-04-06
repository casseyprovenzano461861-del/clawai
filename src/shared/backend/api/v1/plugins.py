# -*- coding: utf-8 -*-
"""
插件管理API端点
提供插件的查询、安装、启用/禁用、更新和配置管理
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import Field
import logging

from backend.auth.fastapi_permissions import require_authentication
from backend.schemas.base import BaseSchema
from backend.schemas.error import APIError, ErrorCode

router = APIRouter(prefix="/api/v1/plugins", tags=["插件管理"])

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 内存存储（生产环境应使用数据库）
# ──────────────────────────────────────────────
_PLUGINS: Dict[str, Dict[str, Any]] = {
    "nmap-scanner": {
        "id": "nmap-scanner",
        "name": "Nmap 网络扫描器",
        "version": "7.94.0",
        "description": "业界标准的网络探测和安全审计工具，支持端口扫描、服务识别、OS检测",
        "author": "Gordon Lyon",
        "category": "scanner",
        "type": "scanner",
        "status": "active",
        "enabled": True,
        "installed": True,
        "icon": "🔍",
        "tags": ["network", "port-scan", "os-detection"],
        "downloads": 125000,
        "rating": 4.9,
        "size": "8.2 MB",
        "installed_at": "2026-04-01T00:00:00",
        "updated_at": datetime.now().isoformat(),
        "settings": {
            "timeout": 30,
            "max_retries": 3,
            "default_flags": "-sV -O"
        }
    },
    "sqlmap-injector": {
        "id": "sqlmap-injector",
        "name": "SQLMap 注入检测",
        "version": "1.8.3",
        "description": "自动化SQL注入漏洞检测与利用工具",
        "author": "sqlmapproject",
        "category": "exploit",
        "type": "exploit",
        "status": "active",
        "enabled": True,
        "installed": True,
        "icon": "💉",
        "tags": ["sql-injection", "database", "web"],
        "downloads": 89000,
        "rating": 4.7,
        "size": "5.1 MB",
        "installed_at": "2026-04-01T00:00:00",
        "updated_at": datetime.now().isoformat(),
        "settings": {
            "level": 1,
            "risk": 1,
            "threads": 4
        }
    },
    "nuclei-scanner": {
        "id": "nuclei-scanner",
        "name": "Nuclei 漏洞扫描",
        "version": "3.2.1",
        "description": "基于模板的漏洞扫描器，拥有海量CVE模板库",
        "author": "ProjectDiscovery",
        "category": "scanner",
        "type": "scanner",
        "status": "available",
        "enabled": False,
        "installed": False,
        "icon": "☢️",
        "tags": ["vulnerability", "cve", "template"],
        "downloads": 67000,
        "rating": 4.8,
        "size": "45 MB",
        "installed_at": None,
        "updated_at": datetime.now().isoformat(),
        "settings": {}
    },
    "metasploit-framework": {
        "id": "metasploit-framework",
        "name": "Metasploit 框架",
        "version": "6.4.0",
        "description": "世界最广泛使用的渗透测试框架",
        "author": "Rapid7",
        "category": "exploit",
        "type": "exploit",
        "status": "available",
        "enabled": False,
        "installed": False,
        "icon": "💀",
        "tags": ["exploit", "post-exploitation", "payloads"],
        "downloads": 234000,
        "rating": 4.9,
        "size": "512 MB",
        "installed_at": None,
        "updated_at": datetime.now().isoformat(),
        "settings": {}
    },
    "burpsuite-integration": {
        "id": "burpsuite-integration",
        "name": "Burp Suite 集成",
        "version": "2024.1",
        "description": "Web应用安全测试平台集成，支持代理拦截和扫描",
        "author": "PortSwigger",
        "category": "proxy",
        "type": "proxy",
        "status": "available",
        "enabled": False,
        "installed": False,
        "icon": "🕷️",
        "tags": ["web", "proxy", "scanner"],
        "downloads": 98000,
        "rating": 4.6,
        "size": "156 MB",
        "installed_at": None,
        "updated_at": datetime.now().isoformat(),
        "settings": {}
    },
    "ai-report-gen": {
        "id": "ai-report-gen",
        "name": "AI 智能报告生成器",
        "version": "1.2.0",
        "description": "基于AI的渗透测试报告自动生成，支持多种格式导出",
        "author": "ClawAI Team",
        "category": "reporting",
        "type": "reporting",
        "status": "active",
        "enabled": True,
        "installed": True,
        "icon": "📊",
        "tags": ["ai", "report", "automation"],
        "downloads": 15000,
        "rating": 4.5,
        "size": "2.3 MB",
        "installed_at": "2026-04-01T00:00:00",
        "updated_at": datetime.now().isoformat(),
        "settings": {
            "language": "zh-CN",
            "template": "standard",
            "include_charts": True
        }
    }
}

_MARKETPLACE_EXTRA = [
    {
        "id": "dirsearch-fuzzer",
        "name": "Dirsearch 目录扫描",
        "version": "0.4.3",
        "description": "高速Web路径暴力破解和目录枚举工具",
        "author": "maurosoria",
        "category": "scanner",
        "status": "available",
        "enabled": False,
        "installed": False,
        "icon": "📁",
        "tags": ["directory", "fuzzing", "web"],
        "downloads": 45000,
        "rating": 4.4,
        "size": "3.8 MB"
    },
    {
        "id": "hydra-brute",
        "name": "Hydra 爆破工具",
        "version": "9.5",
        "description": "快速多协议网络登录破解工具",
        "author": "vanhauser-thc",
        "category": "brute-force",
        "status": "available",
        "enabled": False,
        "installed": False,
        "icon": "🔓",
        "tags": ["brute-force", "login", "protocol"],
        "downloads": 78000,
        "rating": 4.3,
        "size": "1.2 MB"
    }
]


# ──────────────────────────────────────────────
# Pydantic 模型
# ──────────────────────────────────────────────
class PluginSettingsUpdate(BaseSchema):
    settings: Dict[str, Any] = Field(..., description="插件配置项")


# ──────────────────────────────────────────────
# 路由
# ──────────────────────────────────────────────
@router.get("")
async def list_plugins(
    category: Optional[str] = Query(None, description="按分类过滤"),
    installed: Optional[bool] = Query(None, description="只显示已安装"),
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取插件列表"""
    try:
        plugins = list(_PLUGINS.values())
        if category:
            plugins = [p for p in plugins if p.get("category") == category]
        if installed is not None:
            plugins = [p for p in plugins if p.get("installed") == installed]

        return {
            "success": True,
            "data": plugins,
            "total": len(plugins)
        }
    except Exception as e:
        logger.error(f"获取插件列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(code=ErrorCode.UNKNOWN_ERROR, message="获取插件列表失败", severity="high").model_dump()
        )


@router.get("/marketplace")
async def get_marketplace(
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取插件市场（包含未安装插件）"""
    try:
        all_plugins = list(_PLUGINS.values()) + _MARKETPLACE_EXTRA
        return {
            "success": True,
            "data": all_plugins,
            "total": len(all_plugins),
            "categories": ["scanner", "exploit", "proxy", "reporting", "brute-force"]
        }
    except Exception as e:
        logger.error(f"获取插件市场失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(code=ErrorCode.UNKNOWN_ERROR, message="获取插件市场失败", severity="high").model_dump()
        )


@router.get("/{plugin_id}")
async def get_plugin(
    plugin_id: str,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取插件详情"""
    plugin = _PLUGINS.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message=f"插件 {plugin_id} 不存在", severity="low").model_dump()
        )
    return {"success": True, "data": plugin}


@router.post("/{plugin_id}/install")
async def install_plugin(
    plugin_id: str,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """安装插件"""
    try:
        # 先在已知插件中查找
        plugin = _PLUGINS.get(plugin_id)
        if not plugin:
            # 从市场列表查找
            market_plugin = next((p for p in _MARKETPLACE_EXTRA if p["id"] == plugin_id), None)
            if not market_plugin:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message=f"插件 {plugin_id} 不存在", severity="low").model_dump()
                )
            # 加入已知插件
            _PLUGINS[plugin_id] = {**market_plugin, "settings": {}, "installed_at": None}
            plugin = _PLUGINS[plugin_id]

        if plugin.get("installed"):
            return {"success": True, "message": f"插件 {plugin_id} 已安装", "data": plugin}

        # 模拟安装
        plugin["installed"] = True
        plugin["enabled"] = True
        plugin["status"] = "active"
        plugin["installed_at"] = datetime.now().isoformat()
        plugin["updated_at"] = datetime.now().isoformat()

        logger.info(f"插件安装成功: {plugin_id} by {current_user.get('username')}")
        return {
            "success": True,
            "message": f"插件 {plugin['name']} 安装成功",
            "data": plugin
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"安装插件失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(code=ErrorCode.UNKNOWN_ERROR, message="安装插件失败", severity="high").model_dump()
        )


@router.post("/{plugin_id}/enable")
async def enable_plugin(
    plugin_id: str,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """启用插件"""
    plugin = _PLUGINS.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message=f"插件 {plugin_id} 不存在", severity="low").model_dump()
        )
    if not plugin.get("installed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIError(code=ErrorCode.VALIDATION_ERROR, message="请先安装插件", severity="medium").model_dump()
        )

    plugin["enabled"] = True
    plugin["status"] = "active"
    plugin["updated_at"] = datetime.now().isoformat()

    return {"success": True, "message": f"插件 {plugin['name']} 已启用", "data": plugin}


@router.post("/{plugin_id}/disable")
async def disable_plugin(
    plugin_id: str,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """禁用插件"""
    plugin = _PLUGINS.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message=f"插件 {plugin_id} 不存在", severity="low").model_dump()
        )

    plugin["enabled"] = False
    plugin["status"] = "disabled"
    plugin["updated_at"] = datetime.now().isoformat()

    return {"success": True, "message": f"插件 {plugin['name']} 已禁用", "data": plugin}


@router.post("/{plugin_id}/update")
async def update_plugin(
    plugin_id: str,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """更新插件到最新版本"""
    plugin = _PLUGINS.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message=f"插件 {plugin_id} 不存在", severity="low").model_dump()
        )
    if not plugin.get("installed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIError(code=ErrorCode.VALIDATION_ERROR, message="插件未安装，无法更新", severity="medium").model_dump()
        )

    # 模拟更新（实际应触发包管理器）
    plugin["status"] = "active"
    plugin["updated_at"] = datetime.now().isoformat()

    logger.info(f"插件更新成功: {plugin_id}")
    return {
        "success": True,
        "message": f"插件 {plugin['name']} 更新成功",
        "data": plugin
    }


@router.delete("/{plugin_id}")
async def uninstall_plugin(
    plugin_id: str,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """卸载插件"""
    plugin = _PLUGINS.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message=f"插件 {plugin_id} 不存在", severity="low").model_dump()
        )

    plugin["installed"] = False
    plugin["enabled"] = False
    plugin["status"] = "available"
    plugin["installed_at"] = None
    plugin["settings"] = {}
    plugin["updated_at"] = datetime.now().isoformat()

    logger.info(f"插件卸载成功: {plugin_id} by {current_user.get('username')}")
    return {"success": True, "message": f"插件 {plugin['name']} 已卸载"}


@router.get("/{plugin_id}/settings")
async def get_plugin_settings(
    plugin_id: str,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取插件配置"""
    plugin = _PLUGINS.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message=f"插件 {plugin_id} 不存在", severity="low").model_dump()
        )
    return {"success": True, "data": plugin.get("settings", {})}


@router.put("/{plugin_id}/settings")
async def update_plugin_settings(
    plugin_id: str,
    settings_data: PluginSettingsUpdate,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """更新插件配置"""
    plugin = _PLUGINS.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message=f"插件 {plugin_id} 不存在", severity="low").model_dump()
        )

    plugin["settings"] = {**plugin.get("settings", {}), **settings_data.settings}
    plugin["updated_at"] = datetime.now().isoformat()

    return {"success": True, "message": "配置更新成功", "data": plugin["settings"]}


__all__ = ["router"]
