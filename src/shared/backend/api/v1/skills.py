# -*- coding: utf-8 -*-
"""
技能库API端点
提供安全技能的查询、执行、统计和学习路径管理
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from pydantic import Field
import logging

from backend.auth.fastapi_permissions import require_authentication
from backend.schemas.base import BaseSchema
from backend.schemas.error import APIError, ErrorCode

router = APIRouter(prefix="/api/v1/skills", tags=["技能库"])

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 内存存储
# ──────────────────────────────────────────────
_SKILLS: Dict[str, Dict[str, Any]] = {
    "network-recon": {
        "id": "network-recon",
        "name": "网络侦察",
        "description": "使用Nmap进行网络拓扑发现、端口扫描和服务识别",
        "type": "reconnaissance",
        "difficulty": "beginner",
        "category": "侦察",
        "tool": "nmap",
        "tags": ["network", "port-scan", "discovery"],
        "estimatedTime": "5-15分钟",
        "successRate": 95,
        "usageCount": 1234,
        "rating": 4.8,
        "parameters": {
            "target": {"type": "string", "required": True, "description": "目标IP或域名"},
            "ports": {"type": "string", "required": False, "default": "1-1000", "description": "端口范围"},
            "flags": {"type": "string", "required": False, "default": "-sV", "description": "Nmap标志"}
        },
        "created_at": "2026-04-01T00:00:00",
        "updated_at": datetime.now().isoformat()
    },
    "web-fingerprint": {
        "id": "web-fingerprint",
        "name": "Web指纹识别",
        "description": "识别目标Web应用技术栈、CMS类型和版本信息",
        "type": "reconnaissance",
        "difficulty": "beginner",
        "category": "侦察",
        "tool": "whatweb",
        "tags": ["web", "fingerprint", "cms"],
        "estimatedTime": "1-3分钟",
        "successRate": 92,
        "usageCount": 876,
        "rating": 4.6,
        "parameters": {
            "target": {"type": "string", "required": True, "description": "目标URL"}
        },
        "created_at": "2026-04-01T00:00:00",
        "updated_at": datetime.now().isoformat()
    },
    "sql-injection": {
        "id": "sql-injection",
        "name": "SQL注入检测",
        "description": "自动化检测SQL注入漏洞，支持多种注入类型和数据库",
        "type": "exploitation",
        "difficulty": "intermediate",
        "category": "漏洞利用",
        "tool": "sqlmap",
        "tags": ["sql", "injection", "database", "web"],
        "estimatedTime": "10-30分钟",
        "successRate": 78,
        "usageCount": 654,
        "rating": 4.7,
        "parameters": {
            "target": {"type": "string", "required": True, "description": "目标URL（含参数）"},
            "level": {"type": "integer", "required": False, "default": 1, "description": "检测级别 1-5"},
            "risk": {"type": "integer", "required": False, "default": 1, "description": "风险级别 1-3"}
        },
        "created_at": "2026-04-01T00:00:00",
        "updated_at": datetime.now().isoformat()
    },
    "xss-detection": {
        "id": "xss-detection",
        "name": "XSS漏洞检测",
        "description": "检测反射型、存储型和DOM型跨站脚本漏洞",
        "type": "exploitation",
        "difficulty": "intermediate",
        "category": "漏洞利用",
        "tool": "xsstrike",
        "tags": ["xss", "web", "javascript"],
        "estimatedTime": "5-20分钟",
        "successRate": 82,
        "usageCount": 432,
        "rating": 4.5,
        "parameters": {
            "target": {"type": "string", "required": True, "description": "目标URL"}
        },
        "created_at": "2026-04-01T00:00:00",
        "updated_at": datetime.now().isoformat()
    },
    "dir-enumeration": {
        "id": "dir-enumeration",
        "name": "目录枚举",
        "description": "暴力破解Web目录和文件，发现隐藏路径",
        "type": "reconnaissance",
        "difficulty": "beginner",
        "category": "侦察",
        "tool": "dirsearch",
        "tags": ["directory", "fuzzing", "web"],
        "estimatedTime": "5-30分钟",
        "successRate": 88,
        "usageCount": 789,
        "rating": 4.4,
        "parameters": {
            "target": {"type": "string", "required": True, "description": "目标URL"},
            "wordlist": {"type": "string", "required": False, "default": "common.txt", "description": "字典文件"}
        },
        "created_at": "2026-04-01T00:00:00",
        "updated_at": datetime.now().isoformat()
    },
    "vulnerability-scan": {
        "id": "vulnerability-scan",
        "name": "漏洞扫描",
        "description": "使用Nuclei模板扫描已知CVE漏洞，支持10000+漏洞模板",
        "type": "scanning",
        "difficulty": "intermediate",
        "category": "漏洞扫描",
        "tool": "nuclei",
        "tags": ["vulnerability", "cve", "nuclei"],
        "estimatedTime": "10-60分钟",
        "successRate": 91,
        "usageCount": 567,
        "rating": 4.9,
        "parameters": {
            "target": {"type": "string", "required": True, "description": "目标URL或IP"},
            "severity": {"type": "string", "required": False, "default": "medium,high,critical", "description": "严重级别过滤"}
        },
        "created_at": "2026-04-01T00:00:00",
        "updated_at": datetime.now().isoformat()
    },
    "privilege-escalation": {
        "id": "privilege-escalation",
        "name": "权限提升",
        "description": "检测并利用本地权限提升漏洞，获取更高访问权限",
        "type": "post-exploitation",
        "difficulty": "advanced",
        "category": "后渗透",
        "tool": "linpeas",
        "tags": ["privilege", "escalation", "linux"],
        "estimatedTime": "15-45分钟",
        "successRate": 65,
        "usageCount": 234,
        "rating": 4.6,
        "parameters": {
            "target": {"type": "string", "required": True, "description": "目标主机"}
        },
        "created_at": "2026-04-01T00:00:00",
        "updated_at": datetime.now().isoformat()
    },
    "password-crack": {
        "id": "password-crack",
        "name": "密码爆破",
        "description": "对Web登录、SSH、FTP等服务进行密码暴力破解",
        "type": "brute-force",
        "difficulty": "beginner",
        "category": "暴力破解",
        "tool": "hydra",
        "tags": ["password", "brute-force", "login"],
        "estimatedTime": "10-120分钟",
        "successRate": 55,
        "usageCount": 345,
        "rating": 4.2,
        "parameters": {
            "target": {"type": "string", "required": True, "description": "目标地址"},
            "service": {"type": "string", "required": True, "description": "服务类型: ssh/ftp/http-form"},
            "wordlist": {"type": "string", "required": False, "default": "rockyou.txt", "description": "密码字典"}
        },
        "created_at": "2026-04-01T00:00:00",
        "updated_at": datetime.now().isoformat()
    }
}

# 技能执行记录
_EXECUTIONS: Dict[str, Dict[str, Any]] = {}

# 学习路径
_LEARNING_PATHS = [
    {
        "id": "beginner-path",
        "name": "渗透测试入门",
        "description": "从零开始学习渗透测试的基础技能",
        "level": "beginner",
        "skills": ["network-recon", "web-fingerprint", "dir-enumeration", "password-crack"],
        "estimatedHours": 20,
        "completionRate": 0
    },
    {
        "id": "web-pentest-path",
        "name": "Web渗透测试专项",
        "description": "专注于Web应用安全测试的完整技能链",
        "level": "intermediate",
        "skills": ["web-fingerprint", "dir-enumeration", "sql-injection", "xss-detection", "vulnerability-scan"],
        "estimatedHours": 40,
        "completionRate": 0
    },
    {
        "id": "advanced-path",
        "name": "高级渗透测试",
        "description": "覆盖完整攻击链的高级技能组合",
        "level": "advanced",
        "skills": ["network-recon", "vulnerability-scan", "sql-injection", "xss-detection", "privilege-escalation"],
        "estimatedHours": 80,
        "completionRate": 0
    }
]


# ──────────────────────────────────────────────
# 路由
# ──────────────────────────────────────────────
@router.get("")
async def list_skills(
    skill_type: Optional[str] = Query(None, alias="type", description="按类型过滤"),
    difficulty: Optional[str] = Query(None, description="按难度过滤"),
    category: Optional[str] = Query(None, description="按分类过滤"),
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取技能列表"""
    try:
        skills = list(_SKILLS.values())
        if skill_type:
            skills = [s for s in skills if s.get("type") == skill_type]
        if difficulty:
            skills = [s for s in skills if s.get("difficulty") == difficulty]
        if category:
            skills = [s for s in skills if s.get("category") == category]

        return {
            "success": True,
            "data": skills,
            "total": len(skills)
        }
    except Exception as e:
        logger.error(f"获取技能列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(code=ErrorCode.UNKNOWN_ERROR, message="获取技能列表失败", severity="high").model_dump()
        )


@router.get("/stats")
async def get_skill_stats(
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取技能库统计数据"""
    try:
        skills = list(_SKILLS.values())
        total = len(skills)
        by_type: Dict[str, int] = {}
        by_difficulty: Dict[str, int] = {}
        total_usage = 0

        for s in skills:
            t = s.get("type", "other")
            by_type[t] = by_type.get(t, 0) + 1
            d = s.get("difficulty", "unknown")
            by_difficulty[d] = by_difficulty.get(d, 0) + 1
            total_usage += s.get("usageCount", 0)

        avg_success = round(sum(s.get("successRate", 0) for s in skills) / total, 1) if total else 0

        return {
            "success": True,
            "data": {
                "total_skills": total,
                "by_type": by_type,
                "by_difficulty": by_difficulty,
                "total_executions": total_usage,
                "average_success_rate": avg_success,
                "total_executions_today": len(_EXECUTIONS),
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"获取技能统计失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(code=ErrorCode.UNKNOWN_ERROR, message="获取技能统计失败", severity="high").model_dump()
        )


@router.get("/learning-paths")
async def get_learning_paths(
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取学习路径列表"""
    try:
        return {
            "success": True,
            "data": _LEARNING_PATHS,
            "total": len(_LEARNING_PATHS)
        }
    except Exception as e:
        logger.error(f"获取学习路径失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(code=ErrorCode.UNKNOWN_ERROR, message="获取学习路径失败", severity="high").model_dump()
        )


@router.get("/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取技能执行详情"""
    execution = _EXECUTIONS.get(execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message=f"执行记录 {execution_id} 不存在", severity="low").model_dump()
        )
    return {"success": True, "data": execution}


@router.get("/{skill_id}")
async def get_skill(
    skill_id: str,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取技能详情"""
    skill = _SKILLS.get(skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message=f"技能 {skill_id} 不存在", severity="low").model_dump()
        )
    return {"success": True, "data": skill}


@router.post("/{skill_id}/execute")
async def execute_skill(
    skill_id: str,
    background_tasks: BackgroundTasks,
    request_body: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """执行技能"""
    try:
        skill = _SKILLS.get(skill_id)
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message=f"技能 {skill_id} 不存在", severity="low").model_dump()
            )

        # 验证必需参数
        parameters = skill.get("parameters", {})
        for param_name, param_info in parameters.items():
            if param_info.get("required") and param_name not in request_body:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=APIError(
                        code=ErrorCode.VALIDATION_ERROR,
                        message=f"缺少必需参数: {param_name}",
                        severity="medium"
                    ).model_dump()
                )

        # 创建执行记录
        execution_id = str(uuid.uuid4())
        execution = {
            "id": execution_id,
            "skill_id": skill_id,
            "skill_name": skill["name"],
            "target": request_body.get("target", ""),
            "parameters": request_body,
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "finished_at": None,
            "result": None,
            "executed_by": current_user.get("username")
        }
        _EXECUTIONS[execution_id] = execution

        # 更新使用计数
        _SKILLS[skill_id]["usageCount"] = _SKILLS[skill_id].get("usageCount", 0) + 1

        # 后台执行（模拟）
        background_tasks.add_task(_run_skill_execution, execution_id, skill, request_body)

        logger.info(f"技能执行启动: {skill_id} -> {execution_id} by {current_user.get('username')}")
        return {
            "success": True,
            "message": f"技能 {skill['name']} 已开始执行",
            "data": {
                "execution_id": execution_id,
                "status": "running",
                "skill_id": skill_id,
                "target": request_body.get("target")
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行技能失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(code=ErrorCode.UNKNOWN_ERROR, message="执行技能失败", severity="high").model_dump()
        )


async def _run_skill_execution(execution_id: str, skill: Dict, params: Dict):
    """后台执行技能（模拟）"""
    import asyncio
    try:
        await asyncio.sleep(3)  # 模拟执行时间

        execution = _EXECUTIONS.get(execution_id)
        if not execution:
            return

        # 模拟执行结果
        target = params.get("target", "unknown")
        skill_id = skill["id"]

        mock_results = {
            "network-recon": {
                "open_ports": [22, 80, 443, 3306],
                "services": {"22": "SSH OpenSSH 8.9", "80": "HTTP Apache 2.4", "443": "HTTPS Apache 2.4", "3306": "MySQL 8.0"},
                "os": "Linux Ubuntu 22.04"
            },
            "web-fingerprint": {
                "cms": "WordPress 6.4",
                "server": "Apache/2.4.58",
                "php": "8.2.0",
                "plugins": ["Yoast SEO", "WooCommerce"]
            },
            "sql-injection": {
                "vulnerable": True,
                "injection_type": "UNION-based",
                "parameter": "id",
                "database": "MySQL 8.0"
            },
            "vulnerability-scan": {
                "total": 5,
                "critical": 1,
                "high": 2,
                "medium": 2,
                "findings": [
                    {"id": "CVE-2024-1234", "severity": "critical", "name": "WordPress RCE"},
                    {"id": "CVE-2024-5678", "severity": "high", "name": "Apache Path Traversal"}
                ]
            }
        }

        result = mock_results.get(skill_id, {"status": "completed", "target": target})

        execution["status"] = "completed"
        execution["finished_at"] = datetime.now().isoformat()
        execution["result"] = {
            "success": True,
            "output": result,
            "summary": f"技能 {skill['name']} 执行完成，目标: {target}"
        }

    except Exception as e:
        logger.error(f"技能执行失败: {execution_id}: {e}")
        if execution_id in _EXECUTIONS:
            _EXECUTIONS[execution_id]["status"] = "failed"
            _EXECUTIONS[execution_id]["finished_at"] = datetime.now().isoformat()
            _EXECUTIONS[execution_id]["result"] = {"success": False, "error": str(e)}


__all__ = ["router"]
