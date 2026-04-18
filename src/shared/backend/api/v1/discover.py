# -*- coding: utf-8 -*-
"""
靶机发现 API

通过 WebSocket 流式推送靶机发现进度，复用 CLI discover 命令的核心逻辑。

端点：
  POST /api/v1/discover/start   启动发现任务（返回 task_id）
  GET  /api/v1/discover/{task_id}  查询任务状态 + 结果
  WS   /ws/discover/{task_id}      实时接收进度事件
  GET  /api/v1/discover/networks   获取本机局域网段列表
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局任务注册表 {task_id -> task_info}
_discover_tasks: Dict[str, Dict[str, Any]] = {}

# 每个 task_id 对应的事件队列（供 WebSocket 推送）
_event_queues: Dict[str, asyncio.Queue] = {}


# ─── Pydantic 模型 ────────────────────────────────────────────────────────────

class DiscoverStartRequest(BaseModel):
    network: Optional[str] = None   # 指定网段，如 192.168.1.0/24；不填则自动检测
    quick: bool = False             # 快速模式：只 ping，不扫端口


class DiscoverStartResponse(BaseModel):
    task_id: str
    message: str


class HostResult(BaseModel):
    ip: str
    score: int
    rank: int
    open_ports: List[Dict[str, Any]]
    matched_rules: List[str]      # 命中的评分规则描述
    os_hint: str = ""
    banner: str = ""


class DiscoverStatusResponse(BaseModel):
    task_id: str
    status: str                   # pending | running | completed | error
    networks_scanned: List[str]
    alive_count: int
    results: List[HostResult]
    error: Optional[str] = None


# ─── REST 端点 ────────────────────────────────────────────────────────────────

@router.get("/networks")
async def get_local_networks() -> Dict[str, Any]:
    """获取本机所有局域网段，供前端展示可扫描网段"""
    try:
        import sys, os
        _root = os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * 5))
        if _root not in sys.path:
            sys.path.insert(0, _root)

        from src.cli.commands.discover import get_local_networks, _should_skip_network
        networks = get_local_networks()
        result = []
        for net in networks:
            skip, reason = _should_skip_network(net)
            result.append({
                "cidr": net,
                "skippable": skip,
                "skip_reason": reason,
            })
        return {"networks": result}
    except Exception as e:
        logger.error(f"获取本机网段失败: {e}")
        return {"networks": [], "error": str(e)}


@router.post("/start", response_model=DiscoverStartResponse)
async def start_discover(req: DiscoverStartRequest) -> DiscoverStartResponse:
    """启动靶机发现任务"""
    task_id = str(uuid.uuid4())[:8]

    _discover_tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "networks_scanned": [],
        "alive_count": 0,
        "results": [],
        "error": None,
    }
    _event_queues[task_id] = asyncio.Queue(maxsize=500)

    # 后台启动
    asyncio.create_task(_run_discover(task_id, req.network, req.quick))

    return DiscoverStartResponse(
        task_id=task_id,
        message=f"靶机发现已启动 (id: {task_id})，通过 /ws/discover/{task_id} 接收实时进度",
    )


@router.get("/{task_id}", response_model=DiscoverStatusResponse)
async def get_discover_status(task_id: str) -> DiscoverStatusResponse:
    """查询发现任务状态和结果"""
    if task_id not in _discover_tasks:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")

    info = _discover_tasks[task_id]
    return DiscoverStatusResponse(
        task_id=task_id,
        status=info["status"],
        networks_scanned=info["networks_scanned"],
        alive_count=info["alive_count"],
        results=[HostResult(**r) for r in info["results"]],
        error=info.get("error"),
    )


# ─── WebSocket 端点 ───────────────────────────────────────────────────────────

@router.websocket("/ws/{task_id}")
async def discover_websocket(websocket: WebSocket, task_id: str):
    """
    客户端通过此 WebSocket 实时接收靶机发现进度事件。

    消息格式：
    {
      "type": "log" | "progress" | "host_found" | "result" | "completed" | "error",
      "data": { ... }
    }
    """
    await websocket.accept()

    # 确保任务队列存在（客户端可能在任务启动前连接）
    if task_id not in _event_queues:
        _event_queues[task_id] = asyncio.Queue(maxsize=500)

    queue = _event_queues[task_id]

    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30)
                await websocket.send_json(event)
                if event.get("type") in ("completed", "error"):
                    break
            except asyncio.TimeoutError:
                # 发送心跳保持连接
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug(f"发现 WebSocket 断开: {e}")
    finally:
        # 清理队列
        _event_queues.pop(task_id, None)


# ─── 核心执行逻辑 ─────────────────────────────────────────────────────────────

async def _run_discover(
    task_id: str,
    network: Optional[str],
    quick: bool,
) -> None:
    """
    后台执行靶机发现，通过队列推送事件到 WebSocket。
    完整复用 CLI discover 逻辑，但用事件队列替代 Rich console 输出。
    """
    info = _discover_tasks[task_id]
    info["status"] = "running"

    def emit(event_type: str, data: Dict[str, Any]):
        """向 WebSocket 队列推送事件，不阻塞"""
        if task_id in _event_queues:
            try:
                _event_queues[task_id].put_nowait({"type": event_type, "data": data})
            except asyncio.QueueFull:
                pass

    def log(msg: str, level: str = "info"):
        emit("log", {"message": msg, "level": level})

    try:
        import sys, os
        _root = os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * 5))
        if _root not in sys.path:
            sys.path.insert(0, _root)

        from src.cli.commands.discover import (
            get_local_networks,
            _should_skip_network,
            _network_priority,
            score_host,
        )
        from src.shared.backend.tools.nmap import NmapTool

        # ── Step 1：确定网段 ──────────────────────────────────────────────
        emit("progress", {"step": 1, "total": 3, "message": "检测本机网络接口..."})

        if network:
            scannable = [network]
            log(f"使用指定网段: {network}")
        else:
            all_networks = get_local_networks()
            log(f"检测到 {len(all_networks)} 个网段")

            scannable = []
            for net in all_networks:
                skip, reason = _should_skip_network(net)
                if skip:
                    log(f"跳过 {net}: {reason}", "warning")
                else:
                    scannable.append(net)

            scannable.sort(key=_network_priority)

            if not scannable:
                scannable = sorted(
                    all_networks,
                    key=lambda c: int(c.split("/")[1])
                )[-3:]
                log(f"所有网段均被过滤，强制扫描: {', '.join(scannable)}", "warning")

        info["networks_scanned"] = scannable
        log(f"将扫描 {len(scannable)} 个网段: {', '.join(scannable)}")

        if not scannable:
            raise ValueError("未找到可扫描网段")

        # ── Step 2：主机发现 ──────────────────────────────────────────────
        emit("progress", {"step": 2, "total": 3, "message": f"主机存活探测 ({len(scannable)} 个网段)..."})

        tool = NmapTool()
        all_alive: List[str] = []

        for i, net in enumerate(scannable):
            log(f"探测 {net} ({i+1}/{len(scannable)})...")
            emit("progress", {
                "step": 2,
                "total": 3,
                "sub_current": i + 1,
                "sub_total": len(scannable),
                "message": f"探测 {net}...",
            })
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(tool.discover_hosts, net, 60),
                    timeout=75,
                )
                hosts = result.get("alive_hosts", [])
                all_alive.extend(hosts)
                log(f"✓ {net} → 发现 {len(hosts)} 台存活主机", "success")
                for host_ip in hosts:
                    emit("host_found", {"ip": host_ip, "network": net})
            except asyncio.TimeoutError:
                log(f"⚠ {net} 扫描超时，跳过", "warning")
            except Exception as e:
                log(f"✗ {net} 扫描失败: {str(e)[:60]}", "error")

        # 去重排序
        all_alive = sorted(set(all_alive), key=lambda ip: list(map(int, ip.split("."))))
        info["alive_count"] = len(all_alive)
        log(f"共发现 {len(all_alive)} 台存活主机", "success")

        if not all_alive:
            info["status"] = "completed"
            emit("completed", {
                "alive_count": 0,
                "results": [],
                "message": "未发现存活主机。可能需要管理员权限或网段内无靶机。",
            })
            return

        # ── Step 3：指纹识别 + 评分 ──────────────────────────────────────
        scan_targets = all_alive[:15]
        emit("progress", {
            "step": 3,
            "total": 3,
            "message": f"对 {len(scan_targets)} 台主机做指纹扫描...",
        })

        if quick:
            log("快速模式：跳过端口扫描")
            host_infos = [{"ip": ip, "open_ports": [], "raw_output": "", "banner": ""} for ip in scan_targets]
        else:
            host_infos = await _fingerprint_hosts(scan_targets, tool, emit, log)

        # 评分
        scored = []
        for host_info in host_infos:
            score, matched = score_host(host_info)
            scored.append({**host_info, "_score": score, "_matched": matched})
        scored.sort(key=lambda x: x["_score"], reverse=True)

        # 构建结果
        results = []
        for rank, h in enumerate(scored, 1):
            matched_rules = [desc for _, desc in h["_matched"]]
            ports = h.get("open_ports", [])
            result_item = {
                "ip": h["ip"],
                "score": h["_score"],
                "rank": rank,
                "open_ports": ports,
                "matched_rules": matched_rules,
                "os_hint": h.get("os_hint", ""),
                "banner": h.get("banner", "")[:200],
            }
            results.append(result_item)
            # 实时推送每个结果
            emit("host_result", result_item)
            log(f"#{rank} {h['ip']} — 评分 {h['_score']} ({len(ports)} 个端口)", "info")

        info["results"] = results
        info["status"] = "completed"

        emit("completed", {
            "alive_count": len(all_alive),
            "results": results,
            "message": f"发现完成，共 {len(results)} 台主机评分排名",
        })

    except Exception as exc:
        logger.error(f"靶机发现任务 {task_id} 异常: {exc}", exc_info=True)
        info["status"] = "error"
        info["error"] = str(exc)
        if task_id in _event_queues:
            try:
                _event_queues[task_id].put_nowait({
                    "type": "error",
                    "data": {"message": str(exc)},
                })
            except asyncio.QueueFull:
                pass


async def _fingerprint_hosts(
    hosts: List[str],
    tool: Any,
    emit,
    log,
) -> List[Dict[str, Any]]:
    """并发对每台主机做快速端口扫描"""
    common_ports = ",".join(str(p) for p in [
        21, 22, 23, 25, 53, 80, 110, 135, 139, 143,
        443, 445, 993, 995, 1433, 1521, 3306, 3389,
        5432, 5900, 6379, 8080, 8443, 8888, 27017,
    ])

    sem = asyncio.Semaphore(5)
    completed_count = [0]

    async def scan_one(ip: str) -> Dict[str, Any]:
        async with sem:
            try:
                r = await asyncio.wait_for(
                    asyncio.to_thread(
                        tool._execute_real, ip,
                        {"scan_type": "-sT", "ports": common_ports, "timeout": 60}
                    ),
                    timeout=90,
                )
                import re
                ttl_m = re.search(r'ttl[=\s]+(\d+)', r.get("raw_output", ""), re.I)
                ttl = int(ttl_m.group(1)) if ttl_m else 0

                result = {
                    "ip": ip,
                    "open_ports": r.get("ports", []),
                    "raw_output": r.get("raw_output", "")[:500],
                    "ttl": ttl,
                    "banner": "",
                    "os_hint": "Linux" if 55 <= ttl <= 70 else ("Windows" if 120 <= ttl <= 130 else ""),
                }
            except Exception as e:
                result = {"ip": ip, "open_ports": [], "raw_output": "", "ttl": 0, "banner": "", "os_hint": ""}

            completed_count[0] += 1
            emit("progress", {
                "step": 3,
                "total": 3,
                "sub_current": completed_count[0],
                "sub_total": len(hosts),
                "message": f"指纹扫描 {ip} ({completed_count[0]}/{len(hosts)})",
            })
            return result

    results = await asyncio.gather(*[scan_one(ip) for ip in hosts])

    # 对 HTTP 主机额外抓 banner
    http_results = [
        r for r in results
        if any(p["port"] in (80, 8080, 8443, 443) for p in r.get("open_ports", []))
    ]
    if http_results:
        banner_tasks = [_grab_banner(h) for h in http_results[:8]]
        banners = await asyncio.gather(*banner_tasks, return_exceptions=True)
        for h, banner in zip(http_results, banners):
            if isinstance(banner, str) and banner:
                h["banner"] = banner

    return list(results)


async def _grab_banner(host_info: Dict[str, Any]) -> str:
    """对 HTTP 端口做快速 banner 抓取"""
    for port_info in host_info.get("open_ports", []):
        port = port_info["port"]
        if port not in (80, 8080, 8443, 443, 8888):
            continue
        scheme = "https" if port in (443, 8443) else "http"
        url = f"{scheme}://{host_info['ip']}:{port}"
        try:
            proc = await asyncio.create_subprocess_exec(
                "curl", "-sk", "-m", "5", "-I", url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=8)
            return stdout.decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
    return ""
