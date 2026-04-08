#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI CLI 界面演示
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def demo():
    """演示界面效果"""
    
    # 清屏
    console.clear()
    
    # 1. Banner
    banner = """
   ██████╗██╗     ███████╗ █████╗  ██████╗ ██╗  ██╗
  ██╔════╝██║     ██╔════╝██╔══██╗██╔═══██╗╚██╗██╔╝
  ██║     ██║     █████╗  ███████║██║   ██║ ╚███╔╝ 
  ██║     ██║     ██╔══╝  ██╔══██║██║   ██║ ██╔██╗ 
  ╚██████╗███████╗███████╗██║  ██║╚██████╔╝██╔╝ ██╗
   ╚═════╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝
              [ AI 渗透测试助手 ]
    """
    console.print(banner, style="bold cyan")
    console.print("━" * 55, style="dim")
    console.print("  ⚡ 版本 2.0   ⚡ Skills: 27   ⚡ Tools: 63", style="green")
    console.print()
    
    # 2. 状态表
    table = Table(title="⚡ 系统状态", box=box.ROUNDED, border_style="cyan", show_header=False)
    table.add_column("Key", style="dim")
    table.add_column("Value", style="green")
    table.add_row("AI 引擎", "DeepSeek / GPT-4")
    table.add_row("Skills 库", "27 个技能")
    table.add_row("工具集成", "63 个工具")
    table.add_row("P-E-R 模式", "就绪")
    console.print(table)
    console.print()
    
    # 3. 模拟扫描
    console.print("\n[12:00:01] ℹ️ System", style="dim")
    console.print(Panel("🎯 开始对 http://127.0.0.1/dvwa 进行渗透测试...", border_style="dim", box=box.ROUNDED))
    
    # 工具执行
    tools = [
        ("🔄 nmap_scan", "yellow", "正在扫描端口..."),
        ("✅ nmap_scan", "green", "发现端口: 80, 3306"),
        ("🔄 whatweb_scan", "yellow", "正在识别技术栈..."),
        ("✅ whatweb_scan", "green", "检测到: PHP, Apache, MySQL, DVWA"),
        ("🔄 nuclei_scan", "yellow", "正在扫描漏洞..."),
        ("✅ nuclei_scan", "green", "发现 3 个潜在漏洞"),
        ("🔄 skill_sqli_basic", "yellow", "正在测试 SQL 注入..."),
        ("✅ skill_sqli_basic", "green", "检测到 SQL 注入漏洞!"),
    ]
    
    for icon_tool, color, msg in tools:
        console.print(f"  {icon_tool}: {msg}", style=color)
        time.sleep(0.1)
    
    # 4. 发现
    console.print("\n  🔍 发现漏洞:", style="bold yellow")
    
    findings = [
        ("critical", "SQL Injection", "/vulnerabilities/sqli/?id=1"),
        ("high", "Command Injection", "/vulnerabilities/exec/?ip=127.0.0.1"),
        ("medium", "XSS (Reflected)", "/vulnerabilities/xss_r/?name=test"),
    ]
    
    sev_colors = {"critical": "red", "high": "orange1", "medium": "yellow"}
    
    for sev, title, evidence in findings:
        color = sev_colors.get(sev, "white")
        console.print(f"  [{sev.upper()}] ", style=color, end="")
        console.print(f"{title}", style="bold white")
        console.print(f"    └─ {evidence}", style="dim")
    
    # 5. 进度
    console.print()
    console.print("  漏洞验证 [████████████████░░░░] 80%", style="cyan")
    console.print("  漏洞利用 [██████████░░░░░░░░░░] 50%", style="cyan")
    console.print("  报告生成 [████████████████████] 100%", style="green")
    
    # 6. 报告
    console.print("\n[12:00:15] 🤖 ClawAI", style="cyan")
    report = """
渗透测试报告已生成!

📊 检测统计:
  • 已知漏洞总数: 10
  • 检测到: 8
  • 检测率: 80%

🎯 CWE 覆盖:
  • CWE-89 (SQL Injection) ✓
  • CWE-79 (XSS) ✓
  • CWE-78 (Command Injection) ✓
  • CWE-98 (File Inclusion) ✓

⚡ 攻击能效:
  • 自动利用成功: 8
  • 能效率: 80%

报告已保存到: tests/dvwa_report.json
"""
    console.print(Panel(report, border_style="cyan", box=box.ROUNDED))
    
    console.print("\n✅ 演示完成!", style="green")


if __name__ == "__main__":
    demo()
