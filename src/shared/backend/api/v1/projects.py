# -*- coding: utf-8 -*-
"""
项目管理 API
以项目为底座，管理多目标渗透测试任务
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/projects", tags=["项目管理"])


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class TargetItem(BaseModel):
    target: str
    type: str = "domain"   # domain | ip | url | cidr


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    visibility: str = "private"          # private | team | public
    tags: List[str] = []
    targets: List[TargetItem] = []
    scope_include: List[str] = []
    scope_exclude: List[str] = []
    scan_mode: str = "standard"          # quick | standard | deep


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None        # draft | active | paused | completed | archived
    visibility: Optional[str] = None
    tags: Optional[List[str]] = None
    scope_include: Optional[List[str]] = None
    scope_exclude: Optional[List[str]] = None
    scan_mode: Optional[str] = None


class AddTargetRequest(BaseModel):
    target: str
    type: str = "domain"


# ---------------------------------------------------------------------------
# JSON-file backed store（持久化到磁盘，重启不丢数据）
# ---------------------------------------------------------------------------

import json
import threading
from pathlib import Path

_STORE_DIR = Path(os.getenv("CLAWAI_DATA_DIR", "./data"))
_STORE_FILE = _STORE_DIR / "projects.json"
_store_lock = threading.Lock()


def _load_store() -> Dict[str, Any]:
    """从磁盘加载项目存储"""
    try:
        if _STORE_FILE.exists():
            return json.loads(_STORE_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"加载项目存储失败，使用空存储: {e}")
    return {"projects": {}, "next_id": 1}


def _save_store(data: Dict[str, Any]) -> None:
    """持久化项目存储到磁盘"""
    try:
        _STORE_DIR.mkdir(parents=True, exist_ok=True)
        _STORE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.error(f"保存项目存储失败: {e}")


# 启动时加载
_store_data = _load_store()
_projects_store: Dict[str, Dict[str, Any]] = _store_data["projects"]
_next_id: int = _store_data.get("next_id", 1)


def _persist() -> None:
    """将内存状态持久化到磁盘（已持有 _store_lock 时调用）"""
    _save_store({"projects": _projects_store, "next_id": _next_id})


def _new_id() -> str:
    global _next_id
    pid = str(_next_id)
    _next_id += 1
    return pid


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _project_to_response(p: Dict[str, Any], include_details: bool = False) -> Dict[str, Any]:
    resp = {
        "id": p["id"],
        "name": p["name"],
        "description": p.get("description", ""),
        "status": p.get("status", "draft"),
        "visibility": p.get("visibility", "private"),
        "tags": p.get("tags", []),
        "target_count": len(p.get("targets", [])),
        "scan_count": p.get("scan_count", 0),
        "vulnerability_count": p.get("vulnerability_count", 0),
        "last_scan_at": p.get("last_scan_at"),
        "created_at": p.get("created_at"),
        "updated_at": p.get("updated_at"),
    }
    if include_details:
        resp["targets"] = p.get("targets", [])
        resp["scope"] = p.get("scope", {"include": [], "exclude": []})
        resp["config"] = p.get("config", {})
    return resp


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", summary="获取项目列表")
async def list_projects(
    status: Optional[str] = Query(None, description="按状态过滤"),
    search: Optional[str] = Query(None, description="按名称搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """获取所有项目，支持状态过滤和名称搜索"""
    with _store_lock:
        projects = list(_projects_store.values())

    # 按状态过滤
    if status:
        projects = [p for p in projects if p.get("status") == status]

    # 按名称搜索
    if search:
        q = search.lower()
        projects = [p for p in projects if q in p["name"].lower()]

    # 按创建时间降序
    projects.sort(key=lambda p: p.get("created_at", ""), reverse=True)

    total = len(projects)
    start = (page - 1) * page_size
    page_items = projects[start: start + page_size]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_project_to_response(p) for p in page_items],
    }


@router.post("", summary="创建项目", status_code=201)
async def create_project(body: ProjectCreate) -> Dict[str, Any]:
    """创建新项目"""
    with _store_lock:
        pid = _new_id()
        now = _now()

        targets = []
        for t in body.targets:
            targets.append({
                "target": t.target,
                "type": t.type,
                "added_at": now,
                "status": "pending",
            })

        project = {
            "id": pid,
            "name": body.name,
            "description": body.description or "",
            "status": "draft",
            "visibility": body.visibility,
            "tags": body.tags,
            "targets": targets,
            "scope": {
                "include": body.scope_include,
                "exclude": body.scope_exclude,
            },
            "config": {
                "scan_mode": body.scan_mode,
                "tools": {"nmap": True, "sqlmap": True, "nikto": True, "dirsearch": True},
                "rate_limit": 10,
                "timeout": 3600,
                "concurrency": 3,
            },
            "scan_count": 0,
            "vulnerability_count": 0,
            "last_scan_at": None,
            "created_at": now,
            "updated_at": now,
        }

        _projects_store[pid] = project
        _persist()
        logger.info(f"项目已创建: {pid} - {body.name}")
        return _project_to_response(project, include_details=True)


@router.get("/{project_id}", summary="获取项目详情")
async def get_project(project_id: str) -> Dict[str, Any]:
    """获取项目详情（含目标列表、扫描历史统计）"""
    p = _projects_store.get(project_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")
    return _project_to_response(p, include_details=True)


@router.put("/{project_id}", summary="更新项目")
async def update_project(project_id: str, body: ProjectUpdate) -> Dict[str, Any]:
    """更新项目基本信息"""
    with _store_lock:
        p = _projects_store.get(project_id)
        if not p:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

        if body.name is not None:
            p["name"] = body.name
        if body.description is not None:
            p["description"] = body.description
        if body.status is not None:
            valid_statuses = {"draft", "active", "paused", "completed", "archived"}
            if body.status not in valid_statuses:
                raise HTTPException(status_code=400, detail=f"无效状态，允许值: {valid_statuses}")
            p["status"] = body.status
        if body.visibility is not None:
            p["visibility"] = body.visibility
        if body.tags is not None:
            p["tags"] = body.tags
        if body.scope_include is not None:
            p.setdefault("scope", {})["include"] = body.scope_include
        if body.scope_exclude is not None:
            p.setdefault("scope", {})["exclude"] = body.scope_exclude
        if body.scan_mode is not None:
            p.setdefault("config", {})["scan_mode"] = body.scan_mode

        p["updated_at"] = _now()
        _persist()
        return _project_to_response(p, include_details=True)


@router.delete("/{project_id}", summary="删除项目", status_code=204)
async def delete_project(project_id: str):
    """删除项目"""
    with _store_lock:
        if project_id not in _projects_store:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")
        del _projects_store[project_id]
        _persist()
        logger.info(f"项目已删除: {project_id}")


# ---------------------------------------------------------------------------
# Target management
# ---------------------------------------------------------------------------

@router.get("/{project_id}/targets", summary="获取目标列表")
async def list_targets(project_id: str) -> Dict[str, Any]:
    """获取项目的所有目标"""
    p = _projects_store.get(project_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")
    return {"project_id": project_id, "targets": p.get("targets", [])}


@router.post("/{project_id}/targets", summary="添加目标", status_code=201)
async def add_target(project_id: str, body: AddTargetRequest) -> Dict[str, Any]:
    """向项目添加一个目标地址"""
    with _store_lock:
        p = _projects_store.get(project_id)
        if not p:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

        # 去重检查
        existing = [t["target"] for t in p.get("targets", [])]
        if body.target in existing:
            raise HTTPException(status_code=409, detail=f"目标 {body.target} 已存在")

        target_info = {
            "target": body.target,
            "type": body.type,
            "added_at": _now(),
            "status": "pending",
        }
        p.setdefault("targets", []).append(target_info)
        p["updated_at"] = _now()
        _persist()

        logger.info(f"目标已添加: 项目={project_id}, target={body.target}")
        return {"project_id": project_id, "added": target_info, "targets": p["targets"]}


@router.delete("/{project_id}/targets/{target}", summary="移除目标", status_code=204)
async def remove_target(project_id: str, target: str):
    """从项目中移除指定目标"""
    with _store_lock:
        p = _projects_store.get(project_id)
        if not p:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

        before = len(p.get("targets", []))
        p["targets"] = [t for t in p.get("targets", []) if t["target"] != target]
        if len(p["targets"]) == before:
            raise HTTPException(status_code=404, detail=f"目标 {target} 不存在")

        p["updated_at"] = _now()
        _persist()
        logger.info(f"目标已移除: 项目={project_id}, target={target}")


# ---------------------------------------------------------------------------
# Stats summary
# ---------------------------------------------------------------------------

@router.get("/{project_id}/stats", summary="项目统计摘要")
async def get_project_stats(project_id: str) -> Dict[str, Any]:
    """获取项目的扫描统计、漏洞统计摘要"""
    p = _projects_store.get(project_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

    targets = p.get("targets", [])
    status_counts = {}
    for t in targets:
        s = t.get("status", "pending")
        status_counts[s] = status_counts.get(s, 0) + 1

    return {
        "project_id": project_id,
        "target_count": len(targets),
        "target_status": status_counts,
        "scan_count": p.get("scan_count", 0),
        "vulnerability_count": p.get("vulnerability_count", 0),
        "last_scan_at": p.get("last_scan_at"),
    }


# ---------------------------------------------------------------------------
# Vulnerability management
# ---------------------------------------------------------------------------

class VulnCreate(BaseModel):
    title: str
    severity: str = "medium"          # critical | high | medium | low | info
    target: Optional[str] = None
    description: Optional[str] = None
    evidence: Optional[str] = None
    remediation: Optional[str] = None
    cve: Optional[str] = None
    source: str = "manual"            # manual | scan | ai


_vuln_id_counter: int = 1

def _new_vuln_id() -> str:
    global _vuln_id_counter
    vid = f"V{_vuln_id_counter:04d}"
    _vuln_id_counter += 1
    return vid


@router.get("/{project_id}/vulnerabilities", summary="获取漏洞列表")
async def list_vulnerabilities(
    project_id: str,
    severity: Optional[str] = Query(None),
) -> Dict[str, Any]:
    p = _projects_store.get(project_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

    vulns = p.get("vulnerabilities", [])
    if severity:
        vulns = [v for v in vulns if v.get("severity") == severity]

    return {"project_id": project_id, "total": len(vulns), "items": vulns}


@router.post("/{project_id}/vulnerabilities", summary="新增漏洞", status_code=201)
async def add_vulnerability(project_id: str, body: VulnCreate) -> Dict[str, Any]:
    with _store_lock:
        p = _projects_store.get(project_id)
        if not p:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

        vuln = {
            "id": _new_vuln_id(),
            "title": body.title,
            "severity": body.severity,
            "target": body.target,
            "description": body.description or "",
            "evidence": body.evidence or "",
            "remediation": body.remediation or "",
            "cve": body.cve,
            "source": body.source,
            "created_at": _now(),
        }
        p.setdefault("vulnerabilities", []).append(vuln)
        p["vulnerability_count"] = len(p["vulnerabilities"])
        p["updated_at"] = _now()
        _persist()
        return vuln


@router.get("/{project_id}/vulnerabilities/summary", summary="漏洞严重程度统计")
async def vuln_summary(project_id: str) -> Dict[str, Any]:
    p = _projects_store.get(project_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

    counts: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for v in p.get("vulnerabilities", []):
        sev = v.get("severity", "info")
        if sev in counts:
            counts[sev] += 1
    return {"project_id": project_id, "summary": counts, "total": sum(counts.values())}


@router.delete("/{project_id}/vulnerabilities/{vuln_id}", summary="删除漏洞", status_code=204)
async def delete_vulnerability(project_id: str, vuln_id: str):
    with _store_lock:
        p = _projects_store.get(project_id)
        if not p:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

        before = len(p.get("vulnerabilities", []))
        p["vulnerabilities"] = [v for v in p.get("vulnerabilities", []) if v["id"] != vuln_id]
        if len(p["vulnerabilities"]) == before:
            raise HTTPException(status_code=404, detail=f"漏洞 {vuln_id} 不存在")
        p["vulnerability_count"] = len(p["vulnerabilities"])
        p["updated_at"] = _now()
        _persist()


# ---------------------------------------------------------------------------
# Scan history
# ---------------------------------------------------------------------------

class ScanLaunchRequest(BaseModel):
    tool: str                         # nmap | nuclei | sqlmap | dirsearch | nikto | ...
    targets: List[str] = []           # 空则使用项目所有目标
    options: Optional[str] = None     # 额外命令行参数
    mode: str = "standard"            # quick | standard | deep


_scan_id_counter: int = 1

def _new_scan_id() -> str:
    global _scan_id_counter
    sid = f"S{_scan_id_counter:04d}"
    _scan_id_counter += 1
    return sid


@router.get("/{project_id}/scans", summary="获取扫描历史")
async def list_scans(project_id: str) -> Dict[str, Any]:
    p = _projects_store.get(project_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

    scans = p.get("scans", [])
    return {"project_id": project_id, "total": len(scans), "items": scans}


@router.post("/{project_id}/scans", summary="发起扫描", status_code=201)
async def launch_scan(project_id: str, body: ScanLaunchRequest) -> Dict[str, Any]:
    """在项目上下文中发起一次扫描，结果自动关联到项目"""
    p = _projects_store.get(project_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

    # 如果未指定目标，使用项目所有目标
    scan_targets = body.targets or [t["target"] for t in p.get("targets", [])]
    if not scan_targets:
        raise HTTPException(status_code=400, detail="项目没有目标，请先添加目标或指定扫描目标")

    scan_id = _new_scan_id()
    now = _now()

    scan_record = {
        "id": scan_id,
        "project_id": project_id,
        "tool": body.tool,
        "targets": scan_targets,
        "options": body.options or "",
        "mode": body.mode,
        "status": "running",
        "started_at": now,
        "finished_at": None,
        "finding_count": 0,
        "output_summary": "",
    }

    p.setdefault("scans", []).insert(0, scan_record)
    p["scan_count"] = len(p["scans"])
    p["last_scan_at"] = now
    p["updated_at"] = now

    # 更新目标状态为 scanning
    for t in p.get("targets", []):
        if t["target"] in scan_targets:
            t["status"] = "scanning"

    _persist()

    # 异步执行扫描（后台任务）
    import asyncio
    asyncio.create_task(_run_scan_background(project_id, scan_id, body.tool, scan_targets, body.options or ""))

    logger.info(f"扫描已发起: project={project_id} scan={scan_id} tool={body.tool} targets={scan_targets}")
    return scan_record


async def _run_scan_background(project_id: str, scan_id: str, tool: str, targets: List[str], options: str):
    """后台执行扫描并将结果写回项目（Windows 兼容：用线程池运行同步 subprocess）"""
    import asyncio
    import subprocess
    import shutil

    output = ""
    try:
        target_str = targets[0] if targets else ""

        cmd_map = {
            "nmap":      ["nmap", "-sV", "--open", "-T4"] + targets + (options.split() if options else []),
            "nuclei":    ["nuclei", "-u", target_str] + (options.split() if options else []),
            "sqlmap":    ["sqlmap", "-u", target_str, "--batch", "--level=2"] + (options.split() if options else []),
            "nikto":     ["nikto", "-h", target_str] + (options.split() if options else []),
            "dirsearch": ["dirsearch", "-u", target_str, "-q"] + (options.split() if options else []),
            "gobuster":  ["gobuster", "dir", "-u", target_str, "-w", "/usr/share/wordlists/dirb/common.txt", "-q"] + (options.split() if options else []),
            "hydra":     ["hydra", target_str] + (options.split() if options else []),
            "ffuf":      ["ffuf", "-u", f"{target_str}/FUZZ", "-w", "/usr/share/wordlists/dirb/common.txt", "-mc", "200,301,302"] + (options.split() if options else []),
        }

        cmd = cmd_map.get(tool) or ([tool] + targets + (options.split() if options else []))
        tool_bin = cmd[0]

        if not shutil.which(tool_bin):
            output = f"[工具未安装] {tool_bin} 未在系统 PATH 中找到，请先安装该工具。"
        else:
            def _run():
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=300,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                return result.stdout.strip() or f"{tool_bin} 执行完成（无输出）"

            output = await asyncio.to_thread(_run)

    except subprocess.TimeoutExpired:
        output = f"[超时] {tool} 执行超时（300s）"
    except Exception as e:
        import traceback
        output = f"[执行异常] {type(e).__name__}: {e}\n{traceback.format_exc()}"
        logger.error(f"扫描后台任务异常: {e}", exc_info=True)

    # 更新扫描记录
    p = _projects_store.get(project_id)
    if not p:
        return
    for scan in p.get("scans", []):
        if scan["id"] == scan_id:
            scan["status"] = "completed"
            scan["finished_at"] = _now()
            scan["output_summary"] = output[:500] if output else "扫描完成"
            break

    # 更新目标状态
    for t in p.get("targets", []):
        if t["target"] in targets and t.get("status") == "scanning":
            t["status"] = "completed"

    p["updated_at"] = _now()
    _persist()

    # 发布 EventBus 事件
    try:
        from src.shared.backend.ai_core.event_bus import get_event_bus
        bus = get_event_bus()
        await bus.publish("scan_done", {
            "project_id": project_id,
            "scan_id": scan_id,
            "tool": tool,
            "targets": targets,
            "output": output[:200] if output else "",
        })
    except Exception:
        pass


# ---------------------------------------------------------------------------
# AI context
# ---------------------------------------------------------------------------

@router.get("/{project_id}/context", summary="获取 AI 对话上下文")
async def get_project_context(project_id: str) -> Dict[str, Any]:
    """返回项目摘要，供 AI 对话自动注入上下文"""
    p = _projects_store.get(project_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

    vulns = p.get("vulnerabilities", [])
    scans = p.get("scans", [])

    # 漏洞摘要
    sev_counts: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    vuln_titles = []
    for v in vulns[:10]:  # 取前10条
        sev = v.get("severity", "info")
        if sev in sev_counts:
            sev_counts[sev] += 1
        vuln_titles.append(f"[{v.get('severity','?').upper()}] {v.get('title','')}")

    # 扫描摘要
    recent_scans = []
    for s in scans[:5]:  # 最近5次
        recent_scans.append(f"{s.get('tool','')} on {', '.join(s.get('targets',[])[:2])} ({s.get('status','')})")

    context_text = f"""## 当前项目上下文
项目名称: {p['name']}
描述: {p.get('description', '无')}
状态: {p.get('status', 'draft')}
目标列表: {', '.join(t['target'] for t in p.get('targets', []))}

## 漏洞统计
Critical: {sev_counts['critical']} | High: {sev_counts['high']} | Medium: {sev_counts['medium']} | Low: {sev_counts['low']}
{chr(10).join(vuln_titles) if vuln_titles else '暂无发现漏洞'}

## 近期扫描
{chr(10).join(recent_scans) if recent_scans else '尚未发起扫描'}
"""

    return {
        "project_id": project_id,
        "project_name": p["name"],
        "context_text": context_text,
        "targets": [t["target"] for t in p.get("targets", [])],
        "vuln_summary": sev_counts,
        "total_vulns": len(vulns),
        "total_scans": len(scans),
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

class ReportRequest(BaseModel):
    format: str = "markdown"          # markdown | html | pdf
    include_evidence: bool = True
    title: Optional[str] = None


@router.post("/{project_id}/report", summary="生成项目渗透报告")
async def generate_project_report(project_id: str, body: ReportRequest) -> Dict[str, Any]:
    """基于项目数据生成渗透测试报告"""
    p = _projects_store.get(project_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

    vulns = p.get("vulnerabilities", [])
    scans = p.get("scans", [])
    targets = p.get("targets", [])

    # 按严重程度分组
    sev_order = ["critical", "high", "medium", "low", "info"]
    vuln_by_sev: Dict[str, List] = {s: [] for s in sev_order}
    for v in vulns:
        sev = v.get("severity", "info")
        vuln_by_sev.setdefault(sev, []).append(v)

    title = body.title or f"{p['name']} 渗透测试报告"
    now_str = datetime.utcnow().strftime("%Y-%m-%d")

    lines = [
        f"# {title}",
        f"",
        f"**生成时间**: {now_str}  ",
        f"**项目状态**: {p.get('status', 'draft')}  ",
        f"**目标数量**: {len(targets)}  ",
        f"**扫描次数**: {len(scans)}  ",
        f"**漏洞总数**: {len(vulns)}  ",
        f"",
        f"## 目标范围",
    ]
    for t in targets:
        lines.append(f"- `{t['target']}` ({t.get('type','domain')}) — 状态: {t.get('status','pending')}")

    lines += ["", "## 漏洞汇总", ""]
    for sev in sev_order:
        vlist = vuln_by_sev.get(sev, [])
        if not vlist:
            continue
        lines.append(f"### {sev.upper()} ({len(vlist)})")
        for v in vlist:
            lines.append(f"#### {v.get('title', '未命名')}")
            lines.append(f"- **目标**: {v.get('target', 'N/A')}")
            lines.append(f"- **描述**: {v.get('description', '无')}")
            if body.include_evidence and v.get("evidence"):
                lines.append(f"- **证据**:\n```\n{v['evidence']}\n```")
            if v.get("remediation"):
                lines.append(f"- **修复建议**: {v['remediation']}")
            if v.get("cve"):
                lines.append(f"- **CVE**: {v['cve']}")
            lines.append("")

    lines += ["## 扫描历史", ""]
    for s in scans:
        lines.append(f"- **{s.get('tool','')}** | 目标: {', '.join(s.get('targets',[])[:3])} | 状态: {s.get('status','')} | {s.get('started_at','')[:10]}")

    report_content = "\n".join(lines)

    return {
        "project_id": project_id,
        "title": title,
        "format": body.format,
        "content": report_content,
        "generated_at": _now(),
        "stats": {
            "targets": len(targets),
            "scans": len(scans),
            "vulnerabilities": len(vulns),
        }
    }
