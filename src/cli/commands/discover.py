#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
discover 命令 — 主动靶机发现

在当前局域网内自动枚举存活主机，对每台主机做服务指纹识别，
然后用规则引擎对"像靶机"的特征进行评分，输出推荐目标列表。

使用方式（CLI）：
    python clawai.py discover
    python clawai.py discover --network 192.168.1.0/24
    python clawai.py discover --quick         # 只做 ping，不扫端口
    python clawai.py discover --auto-scan     # 对 Top1 自动开始深度扫描

使用方式（Chat）：
    /discover
    发现靶机
    找靶机 192.168.23.0/24
"""

COMMAND_META = {
    "name": "discover",
    "aliases": ["发现靶机", "找靶机", "find", "hunt"],
    "category": "local",
    "description_zh": "主动扫描局域网，发现并推荐靶机目标",
    "description_en": "Actively scan LAN to discover and recommend pentest targets",
    "argument_hint": "[--network <cidr>] [--quick] [--auto-scan]",
}

# ─── 靶机特征评分规则 ─────────────────────────────────────────────────────────
#
# 每条规则格式：(得分, 描述, 匹配函数)
# 匹配函数接受 host_info dict，返回 bool
#
# host_info 结构：
#   {
#     "ip": str,
#     "open_ports": [{"port": int, "service": str}, ...],
#     "os_hint": str,   # 从 TTL 或 nmap 猜测
#     "raw_output": str,
#   }

_SCORE_RULES = [
    # ── 高分：经典靶机服务组合 ──────────────────────────────────────────────
    (25, "同时开放 HTTP(80) + SSH(22)，典型 Web 靶机组合",
     lambda h: _has_ports(h, {22, 80})),

    (20, "开放 HTTP(80) 服务",
     lambda h: _has_port(h, 80)),

    (15, "开放 HTTPS(443) 服务",
     lambda h: _has_port(h, 443)),

    (15, "开放 SSH(22) 服务，可能需要凭据获取",
     lambda h: _has_port(h, 22)),

    (20, "开放非标 Web 端口 (8080/8443/8888/8000)",
     lambda h: _has_any_port(h, {8080, 8443, 8888, 8000, 8008, 9090})),

    (25, "开放 FTP(21) — 常见靶机弱口令/匿名登录场景",
     lambda h: _has_port(h, 21)),

    (20, "开放 Telnet(23) — 明文协议，靶机常见",
     lambda h: _has_port(h, 23)),

    (15, "开放 SMB(445) — Windows 靶机或 Samba",
     lambda h: _has_port(h, 445)),

    (15, "开放数据库端口 (3306/5432/1433/1521/27017/6379)",
     lambda h: _has_any_port(h, {3306, 5432, 1433, 1521, 27017, 6379})),

    (10, "开放 RDP(3389) — Windows 靶机",
     lambda h: _has_port(h, 3389)),

    (10, "开放 VNC(5900) — 图形化访问靶机",
     lambda h: _has_port(h, 5900)),

    (15, "开放多个端口 (≥4)，攻击面广",
     lambda h: len(h.get("open_ports", [])) >= 4),

    (10, "开放端口数量多 (≥7)",
     lambda h: len(h.get("open_ports", [])) >= 7),

    # ── 服务版本特征（从 banner/raw_output 检测）──────────────────────────
    (30, "检测到 Metasploitable / DVWA / VulnHub 关键字",
     lambda h: _keyword_in_output(h, ["metasploitable", "dvwa", "vulnhub",
                                       "damn vulnerable", "intentionally vulnerable"])),

    (20, "检测到 CMS (WordPress/Joomla/Drupal/Fuel CMS)",
     lambda h: _keyword_in_output(h, ["wordpress", "joomla", "drupal",
                                       "fuel cms", "prestashop"])),

    (15, "检测到过时框架 (Struts2/ThinkPHP/WebLogic)",
     lambda h: _keyword_in_output(h, ["struts", "thinkphp", "weblogic",
                                       "jboss", "activemq", "geronimo"])),

    (10, "检测到 Apache/Nginx 版本信息暴露",
     lambda h: _keyword_in_output(h, ["apache/", "nginx/", "microsoft-iis/"])),

    (15, "检测到默认页面 (Welcome/Default/Test Page)",
     lambda h: _keyword_in_output(h, ["it works!", "test page", "default page",
                                       "welcome to", "under construction",
                                       "default web page"])),

    # ── Linux 靶机特征 ─────────────────────────────────────────────────────
    (10, "TTL≈64，推测为 Linux 系统（常见靶机平台）",
     lambda h: _ttl_linux(h)),

    # ── 扣分项：生产环境特征（不像靶机）──────────────────────────────────
    (-20, "端口过少 (≤1)，可能是网络设备",
     lambda h: len(h.get("open_ports", [])) <= 1),

    (-10, "仅开放 DNS(53)，可能是路由器/DNS服务器",
     lambda h: _has_port(h, 53) and len(h.get("open_ports", [])) <= 2),

    (-30, "IP 以 .1 或 .254 结尾，通常是网关/宿主机而非靶机",
     lambda h: h.get("ip", "").split(".")[-1] in ("1", "254")),

    (-20, "开放 902/912 (VMware 服务端口)，通常是 VMware 宿主机",
     lambda h: _has_any_port(h, {902, 912})),
]

# ─── 辅助函数 ─────────────────────────────────────────────────────────────────

def _has_port(host_info: dict, port: int) -> bool:
    return any(p["port"] == port for p in host_info.get("open_ports", []))

def _has_ports(host_info: dict, ports: set) -> bool:
    open_set = {p["port"] for p in host_info.get("open_ports", [])}
    return ports.issubset(open_set)

def _has_any_port(host_info: dict, ports: set) -> bool:
    open_set = {p["port"] for p in host_info.get("open_ports", [])}
    return bool(ports & open_set)

def _keyword_in_output(host_info: dict, keywords: list) -> bool:
    text = (host_info.get("raw_output", "") + " " + host_info.get("banner", "")).lower()
    return any(kw in text for kw in keywords)

def _ttl_linux(host_info: dict) -> bool:
    ttl = host_info.get("ttl", 0)
    return 55 <= ttl <= 70  # Linux TTL≈64（减去中间路由后的典型值）


def score_host(host_info: dict) -> tuple:
    """
    对单台主机打分，返回 (total_score, matched_rules)
    matched_rules: [(score, description), ...]
    """
    total = 0
    matched = []
    for score, desc, fn in _SCORE_RULES:
        try:
            if fn(host_info):
                total += score
                matched.append((score, desc))
        except Exception:
            pass
    return max(0, total), matched


# ─── 网络接口枚举 ─────────────────────────────────────────────────────────────

# 可扫描的最大子网前缀长度（/24 = 256 IP，/23 = 512，/22 = 1024...）
# /20 = 4096 IP，用 90s 超时必然扫不完，默认只扫 /23 及更小的网段
_MAX_SCAN_PREFIX = 23

# 优先级高的网段前缀（靶机常见网段，优先扫描）
_PRIORITY_PREFIXES = ("192.168.", "10.")

# 跳过的网段（VMware 内部通信、WSL 等，基本不会有靶机）
_SKIP_PREFIXES = ("198.18.", "198.51.", "203.0.")


def _should_skip_network(cidr: str) -> tuple:
    """
    判断网段是否应该跳过，返回 (should_skip: bool, reason: str)
    """
    import ipaddress
    try:
        net = ipaddress.ip_network(cidr, strict=False)
        # 跳过超大网段（/20 以上，超时风险高）
        if net.prefixlen < _MAX_SCAN_PREFIX:
            host_count = net.num_addresses
            return True, f"网段过大（/{net.prefixlen}, {host_count} 个 IP），跳过以避免超时"
        # 跳过已知非靶机网段
        network_str = str(net.network_address)
        for prefix in _SKIP_PREFIXES:
            if network_str.startswith(prefix):
                return True, f"已知非靶机网段（{prefix}*），跳过"
    except Exception:
        pass
    return False, ""


def _network_priority(cidr: str) -> int:
    """网段扫描优先级（数字越小越优先）"""
    for i, prefix in enumerate(_PRIORITY_PREFIXES):
        if cidr.startswith(prefix):
            return i
    return len(_PRIORITY_PREFIXES)


def get_local_networks() -> list:
    """
    获取本机所有局域网网段（排除回环、虚拟网卡等）。
    返回 CIDR 字符串列表，如 ['192.168.23.0/24', '10.0.0.0/24']
    """
    import socket
    import struct

    networks = []

    try:
        # 方法1：netifaces（更准确）
        import netifaces
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr.get("addr", "")
                    netmask = addr.get("netmask", "")
                    if _is_private_ip(ip) and netmask:
                        cidr = _ip_mask_to_cidr(ip, netmask)
                        if cidr and cidr not in networks:
                            networks.append(cidr)
        return networks
    except ImportError:
        pass

    # 方法2：socket + 系统命令（无 netifaces 时的回退）
    try:
        import subprocess
        import platform

        if platform.system() == "Windows":
            result = subprocess.run(
                ["ipconfig"], capture_output=True, text=True, timeout=5
            )
            import re
            # 找 IPv4 地址和子网掩码
            blocks = result.stdout.split("\n\n")
            for block in blocks:
                ip_m = re.search(r'IPv4.*?:\s*([\d.]+)', block)
                mask_m = re.search(r'[Ss]ubnet.*?:\s*([\d.]+)', block)
                if ip_m and mask_m:
                    ip = ip_m.group(1)
                    mask = mask_m.group(1)
                    if _is_private_ip(ip):
                        cidr = _ip_mask_to_cidr(ip, mask)
                        if cidr and cidr not in networks:
                            networks.append(cidr)
        else:
            result = subprocess.run(
                ["ip", "addr"], capture_output=True, text=True, timeout=5
            )
            import re
            for m in re.finditer(r'inet (\d+\.\d+\.\d+\.\d+/\d+)', result.stdout):
                cidr_raw = m.group(1)
                # 规范化为网络地址
                import ipaddress
                try:
                    net = ipaddress.ip_interface(cidr_raw)
                    cidr = str(net.network)
                    if _is_private_ip(str(net.ip)) and cidr not in networks:
                        networks.append(cidr)
                except Exception:
                    pass
    except Exception:
        pass

    # 最终回退：通过 socket 获取本机 IP 猜网段
    if not networks:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            if _is_private_ip(local_ip):
                # 假设 /24
                parts = local_ip.rsplit(".", 1)
                networks.append(f"{parts[0]}.0/24")
        except Exception:
            pass

    return networks


def _is_private_ip(ip: str) -> bool:
    """判断是否为私有/局域网 IP（排除回环和常见虚拟机内部网段的 .1）"""
    if not ip or ip.startswith("127.") or ip.startswith("169.254."):
        return False
    try:
        import ipaddress
        obj = ipaddress.ip_address(ip)
        return obj.is_private and not obj.is_loopback and not obj.is_link_local
    except Exception:
        return False


def _get_self_ips() -> set:
    """获取本机所有 IP 地址（用于从扫描结果中排除宿主机自身）"""
    self_ips = set()
    try:
        import socket
        # 方法1：netifaces
        try:
            import netifaces
            for iface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(iface)
                import netifaces as nf
                if nf.AF_INET in addrs:
                    for addr in addrs[nf.AF_INET]:
                        ip = addr.get("addr", "")
                        if ip:
                            self_ips.add(ip)
            return self_ips
        except ImportError:
            pass
        # 方法2：socket + ipconfig/ip addr
        import subprocess, platform, re
        if platform.system() == "Windows":
            result = subprocess.run(
                ["ipconfig"], capture_output=True, text=True, timeout=5
            )
            for m in re.finditer(r'IPv4.*?:\s*([\d.]+)', result.stdout):
                self_ips.add(m.group(1))
        else:
            result = subprocess.run(
                ["hostname", "-I"], capture_output=True, text=True, timeout=5
            )
            for ip in result.stdout.split():
                if re.match(r'^\d+\.\d+\.\d+\.\d+$', ip):
                    self_ips.add(ip)
    except Exception:
        pass
    return self_ips


def _ip_mask_to_cidr(ip: str, mask: str) -> str:
    """将 IP + 子网掩码 转换为 CIDR 网络地址，如 192.168.1.5 + 255.255.255.0 → 192.168.1.0/24"""
    try:
        import ipaddress
        interface = ipaddress.ip_interface(f"{ip}/{mask}")
        return str(interface.network)
    except Exception:
        return ""


# ─── 主命令实现 ───────────────────────────────────────────────────────────────

class DiscoverCommand:
    """主动靶机发现命令"""

    def execute(self, args: list, ctx: dict) -> str:
        import asyncio
        from rich.console import Console
        console: Console = ctx.get("console", Console())

        # 解析参数
        network = None
        quick = False
        auto_scan = False
        i = 0
        while i < len(args):
            a = args[i]
            if a in ("--network", "-n") and i + 1 < len(args):
                network = args[i + 1]
                i += 2
            elif a == "--quick":
                quick = True
                i += 1
            elif a == "--auto-scan":
                auto_scan = True
                i += 1
            else:
                # 位置参数当作网段
                from src.shared.backend.tools.nmap import _is_network_target
                if _is_network_target(a):
                    network = a
                i += 1

        chat_cli = ctx.get("chat_cli")
        if chat_cli:
            # 在 chat 上下文中，通过 asyncio 运行
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(
                            asyncio.run,
                            self._run(console, network, quick, auto_scan, chat_cli)
                        )
                        return future.result()
                else:
                    return loop.run_until_complete(
                        self._run(console, network, quick, auto_scan, chat_cli)
                    )
            except Exception as e:
                console.print(f"[red]发现失败: {e}[/]")
                return ""
        else:
            return asyncio.run(self._run(console, network, quick, auto_scan, None))

    async def _run(self, console, network, quick, auto_scan, chat_cli) -> str:
        import asyncio
        from rich.table import Table
        from rich.panel import Panel
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
        from rich.prompt import Prompt, Confirm

        console.print()
        console.print(Panel(
            "[bold cyan]主动靶机发现[/bold cyan]\n"
            "[dim]自动扫描局域网，用 AI 规则识别最可能的靶机目标[/dim]",
            border_style="cyan",
            padding=(0, 2),
        ))

        # ── Step 1：确定要扫描的网段 ─────────────────────────────────────
        if network:
            networks = [network]
            console.print(f"[dim]目标网段: {network}[/dim]")
        else:
            console.print("[dim]Step 1/3  自动检测本机网络接口...[/dim]")
            networks = get_local_networks()
            if not networks:
                return (
                    "[yellow]未能自动检测到局域网段。\n"
                    "请手动指定：/discover --network 192.168.1.0/24[/yellow]"
                )
            # 过滤 + 排序：跳过大网段/非靶机网段，优先扫 192.168.x
        scannable = []
        skipped = []
        for net in networks:
            skip, reason = _should_skip_network(net)
            if skip:
                skipped.append((net, reason))
            else:
                scannable.append(net)
        # 按优先级排序（192.168.x 优先）
        scannable.sort(key=_network_priority)

        if skipped:
            for net, reason in skipped:
                console.print(f"[dim]  跳过 {net}: {reason}[/dim]")
        if not scannable:
            # 如果全被跳过，取前 3 个最小网段强制扫
            scannable = sorted(networks, key=lambda c: int(c.split('/')[1]))[-3:]
            console.print(f"[yellow]所有网段均被过滤，强制扫描: {', '.join(scannable)}[/yellow]")
        console.print(f"[dim]将扫描 {len(scannable)} 个网段: {', '.join(scannable)}[/dim]")

        # ── Step 2：主机发现 ─────────────────────────────────────────────
        console.print("[dim]Step 2/3  主机存活探测（nmap -sn）...[/dim]")
        from src.shared.backend.tools.nmap import NmapTool
        tool = NmapTool()

        all_alive: list = []
        with Progress(
            SpinnerColumn(style="cyan"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(style="cyan"),
            console=console,
            transient=True,
        ) as progress:
            tasks_list = []
            for net in scannable:
                t = progress.add_task(f"探测 {net}", total=None)
                tasks_list.append((net, t))

            for net, task_id in tasks_list:
                progress.update(task_id, description=f"[cyan]探测 {net}...[/]")
                try:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(tool.discover_hosts, net, 60),
                        timeout=75,   # 比 nmap 内部超时多 15s 缓冲
                    )
                    hosts = result.get("alive_hosts", [])
                    all_alive.extend(hosts)
                    progress.update(task_id,
                        description=f"[green]✓ {net} → {len(hosts)} 台存活[/]")
                except asyncio.TimeoutError:
                    progress.update(task_id,
                        description=f"[yellow]⚠ {net} 超时跳过[/]")
                except Exception as e:
                    progress.update(task_id,
                        description=f"[red]✗ {net} 失败: {str(e)[:30]}[/]")

        if not all_alive:
            return (
                "未发现任何存活主机。\n"
                "可能原因：\n"
                "  • 目标主机开启了防火墙/禁止 ICMP\n"
                "  • 网段不在当前局域网内\n"
                "  • 需要 root/管理员权限才能发送 ARP 探测\n\n"
                "建议：尝试指定已知 IP 段，如 /discover --network 192.168.23.0/24"
            )

        # 去重并排序
        all_alive = sorted(set(all_alive), key=lambda ip: list(map(int, ip.split("."))))

        # ── 排除宿主机自身所有 IP ────────────────────────────────────────
        host_self_ips = _get_self_ips()
        before_count = len(all_alive)
        all_alive = [ip for ip in all_alive if ip not in host_self_ips]
        if before_count != len(all_alive):
            excluded = before_count - len(all_alive)
            console.print(f"[dim]  已排除 {excluded} 个宿主机自身 IP[/dim]")

        console.print(f"[bold green]发现 {len(all_alive)} 台存活主机[/bold green]")

        # ── Step 3：端口扫描 + 指纹 + 评分 ─────────────────────────────
        if quick:
            console.print("[dim]快速模式：跳过端口扫描，仅展示存活主机[/dim]")
            host_infos = [{"ip": ip, "open_ports": [], "raw_output": ""} for ip in all_alive]
        else:
            console.print(f"[dim]Step 3/3  对 {min(len(all_alive), 15)} 台主机做服务指纹扫描...[/dim]")
            host_infos = await self._fingerprint_hosts(
                all_alive[:15], tool, console
            )

        # 评分 + 排序
        scored = []
        for info in host_infos:
            score, matched = score_host(info)
            scored.append({**info, "_score": score, "_matched": matched})
        scored.sort(key=lambda x: x["_score"], reverse=True)

        # ── 展示结果 ─────────────────────────────────────────────────────
        self._render_results(scored, console)

        # ── 交互：选择目标进行扫描 ────────────────────────────────────────
        if chat_cli and scored:
            top = scored[0]
            if auto_scan:
                target = top["ip"]
                console.print(f"\n[bold]自动选择 Top1: {target}（评分 {top['_score']}）[/bold]")
            else:
                console.print()
                ips = [h["ip"] for h in scored[:10]]
                choices_str = "/".join(str(i + 1) for i in range(len(ips)))
                console.print("[bold]选择操作：[/bold]")
                console.print(f"  输入序号（1-{len(ips)}）直接扫描该主机")
                console.print("  输入 [dim]n[/dim] 退出，不进行扫描")
                choice = Prompt.ask("请选择", default="1")
                if choice.lower() == "n":
                    return f"发现 {len(all_alive)} 台存活主机，未启动扫描。"
                try:
                    idx = int(choice) - 1
                    target = ips[max(0, min(idx, len(ips) - 1))]
                except (ValueError, IndexError):
                    target = ips[0]

            console.print(f"\n[bold cyan]→ 开始扫描 {target}...[/bold cyan]\n")
            chat_cli.session.target = target
            return await chat_cli._execute_scan(
                target,
                profile="standard",
                full_port=False,
            )

        # 无 chat_cli（纯 CLI 模式）
        top_ips = [h["ip"] for h in scored[:5]]
        return (
            f"发现 {len(all_alive)} 台存活主机，推荐靶机（按评分排序）：\n"
            + "\n".join(f"  {i+1}. {ip}（评分 {scored[i]['_score']}）"
                        for i, ip in enumerate(top_ips))
            + "\n\n使用 `python clawai.py scan <IP>` 对目标展开扫描。"
        )

    async def _fingerprint_hosts(
        self, hosts: list, tool: "NmapTool", console
    ) -> list:
        """
        并发对每台主机做快速端口扫描 + 服务版本探测。
        最多 5 并发，避免扫描太慢。
        """
        import asyncio

        common_ports = ",".join(str(p) for p in [
            21, 22, 23, 25, 53, 80, 110, 135, 139, 143,
            443, 445, 993, 995, 1433, 1521, 3306, 3389,
            5432, 5900, 6379, 8080, 8443, 8888, 27017
        ])

        sem = asyncio.Semaphore(5)  # 最多 5 并发
        results = []

        async def scan_one(ip: str) -> dict:
            async with sem:
                r = await asyncio.to_thread(
                    tool._execute_real, ip,
                    {"scan_type": "-sT", "ports": common_ports, "timeout": 60}
                )
                ports = r.get("ports", [])
                # 尝试从 raw_output 提取 TTL
                import re
                ttl_m = re.search(r'ttl[=\s]+(\d+)', r.get("raw_output", ""), re.I)
                ttl = int(ttl_m.group(1)) if ttl_m else 0
                return {
                    "ip": ip,
                    "open_ports": ports,
                    "raw_output": r.get("raw_output", "")[:500],
                    "ttl": ttl,
                    "banner": "",
                }

        with console.status("[cyan]正在指纹扫描...[/]"):
            tasks = [scan_one(ip) for ip in hosts]
            results = await asyncio.gather(*tasks, return_exceptions=False)

        # 对有 HTTP 端口的主机，额外抓 banner
        http_hosts = [
            r for r in results
            if any(p["port"] in (80, 8080, 8443, 443) for p in r.get("open_ports", []))
        ]
        if http_hosts:
            banner_tasks = [self._grab_banner(h) for h in http_hosts[:8]]
            banners = await asyncio.gather(*banner_tasks, return_exceptions=True)
            for h, banner in zip(http_hosts, banners):
                if isinstance(banner, str):
                    h["banner"] = banner

        return list(results)

    async def _grab_banner(self, host_info: dict) -> str:
        """
        对开放的 HTTP 端口做一次 curl 请求，获取响应头和标题
        作为额外的指纹信息。
        """
        import asyncio
        ports_info = host_info.get("open_ports", [])
        for port_info in ports_info:
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
                return stdout.decode("utf-8", errors="replace")[:500]
            except Exception:
                pass
        return ""

    def _render_results(self, scored: list, console) -> None:
        """用 Rich Table 展示评分结果"""
        from rich.table import Table
        from rich.text import Text

        tbl = Table(
            title="靶机推荐列表",
            border_style="cyan",
            show_header=True,
            header_style="bold cyan",
        )
        tbl.add_column("排名", style="bold", width=5, justify="center")
        tbl.add_column("IP 地址", style="bold green", width=18)
        tbl.add_column("评分", width=7, justify="right")
        tbl.add_column("开放端口", width=35)
        tbl.add_column("靶机特征", width=45)

        colors = {0: "red", 1: "yellow", 2: "yellow", 3: "cyan"}

        for rank, h in enumerate(scored[:10], 1):
            score = h["_score"]
            matched = h["_matched"]
            ports = h.get("open_ports", [])

            # 评分颜色
            if score >= 60:
                score_color, rank_icon = "red", "🎯"
            elif score >= 35:
                score_color, rank_icon = "yellow", "🔴"
            elif score >= 15:
                score_color, rank_icon = "cyan", "🟡"
            else:
                score_color, rank_icon = "dim", "⚪"

            # 端口列表
            port_strs = [f"{p['port']}/{p.get('service','?')}" for p in ports[:6]]
            ports_text = "  ".join(port_strs) or "[dim]无[/dim]"

            # Top 命中规则（最高分的前2条，只显示正分规则）
            top_rules = sorted(matched, key=lambda x: x[0], reverse=True)[:2]
            hint = "; ".join(d[:28] for _, d in top_rules if _ > 0) if top_rules else "[dim]无特征[/dim]"

            # 如果是疑似宿主机/网关（.1 或 .254 或有 VMware 端口），加醒目提示
            ip_last = h["ip"].split(".")[-1]
            has_vmware = _has_any_port(h, {902, 912})
            if ip_last in ("1", "254") or has_vmware:
                hint = "[yellow]⚠ 疑似宿主机/网关[/yellow]; " + hint

            tbl.add_row(
                f"{rank_icon} {rank}",
                h["ip"],
                f"[{score_color}]{score}[/{score_color}]",
                ports_text,
                hint,
            )

        console.print(tbl)

        # 详细说明 Top1
        if scored:
            top = scored[0]
            if top["_score"] >= 15 and top["_matched"]:
                console.print(
                    f"\n[bold cyan]Top1 分析 — {top['ip']} "
                    f"（总分 {top['_score']}）[/bold cyan]"
                )
                for score, desc in sorted(top["_matched"], key=lambda x: x[0], reverse=True):
                    icon = "+" if score > 0 else "-"
                    color = "green" if score > 0 else "red"
                    console.print(f"  [{color}]{icon}{score:+3d}[/{color}]  {desc}")
