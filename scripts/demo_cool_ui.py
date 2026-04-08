#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI 炫酷界面演示
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cli.cool_ui import CoolUI, CoolClawAIChat

def demo():
    """演示炫酷界面"""
    
    # 1. Banner
    CoolUI.print_banner()
    
    # 2. 状态面板
    CoolUI.print_status_box("系统状态", [
        ("AI 引擎", "DeepSeek / GPT-4"),
        ("Skills 库", "27 个技能"),
        ("工具集成", "63 个工具"),
        ("P-E-R 模式", "就绪"),
    ])
    
    print()
    
    # 3. 模拟扫描过程
    CoolUI.print_message("system", "🎯 开始对 http://127.0.0.1/dvwa 进行渗透测试...")
    
    # 工具执行
    tools = [
        ("nmap_scan", "发现开放端口: 80, 3306"),
        ("whatweb_scan", "检测到: PHP, Apache, MySQL, DVWA"),
        ("nuclei_scan", "发现 3 个潜在漏洞"),
        ("skill_sqli_basic", "检测到 SQL 注入漏洞"),
    ]
    
    for tool, output in tools:
        CoolUI.print_tool_card(tool, "running")
        CoolUI.print_tool_card(tool, "success", output)
    
    print()
    
    # 4. 发现漏洞
    CoolUI.print_message("success", "发现以下漏洞：")
    
    findings = [
        ("critical", "SQL Injection", "/vulnerabilities/sqli/?id=1"),
        ("high", "Command Injection", "/vulnerabilities/exec/?ip=127.0.0.1"),
        ("medium", "XSS (Reflected)", "/vulnerabilities/xss_r/?name=test"),
        ("medium", "CSRF", "/vulnerabilities/csrf/"),
        ("high", "File Inclusion", "/vulnerabilities/fi/?page=../../../etc/passwd"),
    ]
    
    for sev, title, evidence in findings:
        CoolUI.print_finding(sev, title, evidence)
    
    print()
    
    # 5. 进度条
    CoolUI.print_progress_bar(8, 10, "漏洞验证")
    CoolUI.print_progress_bar(5, 10, "漏洞利用")
    CoolUI.print_progress_bar(10, 10, "报告生成")
    
    print()
    
    # 6. 最终报告
    CoolUI.print_message("assistant", """
渗透测试报告已生成！

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
""")

if __name__ == "__main__":
    demo()
