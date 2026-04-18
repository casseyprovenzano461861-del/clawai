# -*- coding: utf-8 -*-
"""
vm 命令 — VMware 靶机管理
用法：
    clawai vm start <vmx_path>
    clawai vm stop  <vmx_path>
    clawai vm ip    <vmx_path>
    clawai vm list
    clawai vm ensure <vmx_path>   # 启动 + 自动配网 + 返回 IP（供 scan 使用）
"""

from pathlib import Path
from rich.console import Console
from rich.table import Table


class VMCommand:
    """VMware 靶机生命周期管理命令"""

    def execute(self, action: str, args: list, console: Console) -> str:
        from src.cli.vm_manager import get_vm_manager

        mgr = get_vm_manager()

        if not mgr.vmrun:
            console.print("[red]未找到 vmrun.exe，请安装 VMware Workstation[/]")
            return ""

        if action == "list":
            return self._list(mgr, console)
        elif action in ("start", "stop", "ip", "ensure"):
            if not args:
                console.print(f"[red]用法: vm {action} <vmx路径>[/]")
                return ""
            vmx = args[0]
            if action == "start":
                return self._start(mgr, vmx, console)
            elif action == "stop":
                return self._stop(mgr, vmx, console)
            elif action == "ip":
                return self._get_ip(mgr, vmx, console)
            elif action == "ensure":
                return self._ensure(mgr, vmx, console)
        elif action == "register":
            if len(args) < 2:
                console.print("[red]用法: vm register <vmx路径> <IP地址>[/]")
                return ""
            return self._register(mgr, args[0], args[1], console)
        else:
            console.print(f"[yellow]未知操作: {action}。可用: list start stop ip ensure register[/]")
            return ""

    def _list(self, mgr, console: Console) -> str:
        running = mgr.list_running()
        if not running:
            console.print("[yellow]没有正在运行的虚拟机[/]")
            return ""
        t = Table(title="运行中的虚拟机", show_lines=True)
        t.add_column("名称", style="cyan")
        t.add_column("VMX 路径", style="dim")
        for vmx in running:
            name = Path(vmx).stem
            t.add_row(name, vmx)
        console.print(t)
        return f"共 {len(running)} 台 VM 运行中"

    def _start(self, mgr, vmx: str, console: Console) -> str:
        console.print(f"[cyan]启动: {Path(vmx).stem}[/]")
        ok = mgr.start(vmx)
        if ok:
            console.print("[green]启动命令已发送（nogui 模式）[/]")
            return "started"
        else:
            console.print("[red]启动失败，请检查 VMX 路径[/]")
            return "failed"

    def _stop(self, mgr, vmx: str, console: Console) -> str:
        console.print(f"[cyan]停止: {Path(vmx).stem}[/]")
        ok = mgr.stop(vmx)
        if ok:
            console.print("[green]已停止[/]")
            return "stopped"
        else:
            console.print("[red]停止失败[/]")
            return "failed"

    def _get_ip(self, mgr, vmx: str, console: Console) -> str:
        console.print(f"[cyan]获取 IP: {Path(vmx).stem}[/]")
        ip = mgr.get_ip_for(vmx)
        if ip:
            console.print(f"[green]IP: {ip}[/]")
            return ip
        else:
            console.print("[yellow]未检测到 IP，VM 可能需要网络注入[/]")
            console.print("提示: 使用 [bold]clawai vm ensure <vmx>[/] 自动配网")
            return ""

    def _ensure(self, mgr, vmx: str, console: Console) -> str:
        console.print(f"[cyan]确保靶机就绪: {Path(vmx).stem}[/]")
        ip = mgr.ensure_running(vmx)
        if ip:
            console.print(f"[green bold]靶机就绪！IP: {ip}[/]")
            console.print(f"[dim]可直接运行: clawai scan {ip}[/]")
            return ip
        else:
            console.print("[red]自动配网失败[/]")
            console.print("[yellow]请在 VMware 控制台手动执行: sudo dhclient ens33[/]")
            console.print(f"[yellow]获取 IP 后运行: clawai vm register \"{vmx}\" <IP>[/]")
            return ""

    def _register(self, mgr, vmx: str, ip: str, console: Console) -> str:
        """手动注册靶机 IP 到持久化缓存"""
        mgr.register_ip(vmx, ip)
        console.print(f"[green]已注册 {Path(vmx).stem} → {ip}[/]")
        console.print(f"[dim]之后可直接运行: clawai scan {ip}[/]")
        return ip
