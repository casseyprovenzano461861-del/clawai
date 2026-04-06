#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析工具列表，制定集成优先级
"""

import json
import os

def analyze_tools():
    # 读取工具列表
    with open('complete_tool_list.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=" * 60)
    print("工具集成分析报告")
    print("=" * 60)
    
    # 统计信息
    total_tools = data['summary']['total_tools']
    installed_tools = data['summary']['installed_tools']
    install_rate = data['summary']['install_rate']
    
    print(f"\n[统计] 总体统计:")
    print(f"  总工具数: {total_tools}")
    print(f"  已安装: {installed_tools}")
    print(f"  安装率: {install_rate:.1f}%")
    
    # 按类别统计
    print(f"\n[分类] 按类别统计:")
    categories = data['categories']
    for category, stats in categories.items():
        print(f"  {category}: {stats['installed']}/{stats['total']} ({(stats['installed']/stats['total']*100):.1f}%)")
    
    # 已安装工具列表
    print(f"\n[已安装] 已安装工具 ({installed_tools}个):")
    installed = [t for t in data['tools'] if t.get('installed')]
    for tool in installed:
        print(f"  - {tool['name']} ({tool['category']})")
    
    # 缺失的关键渗透测试工具
    print(f"\n[缺失] 缺失的关键渗透测试工具:")
    
    # 定义关键工具列表
    critical_tools = [
        {"name": "Metasploit", "category": "exploit_framework", "reason": "核心渗透测试框架"},
        {"name": "Nmap", "category": "network_scan", "reason": "端口扫描和漏洞检测"},
        {"name": "Hydra", "category": "brute_force", "reason": "暴力破解工具"},
        {"name": "John the Ripper", "category": "password_crack", "reason": "密码破解"},
        {"name": "CrackMapExec", "category": "post_exploit", "reason": "Windows域渗透"},
        {"name": "LinPEAS/WinPEAS", "category": "post_exploit", "reason": "权限提升检查"},
        {"name": "Mimikatz", "category": "post_exploit", "reason": "Windows凭证提取"},
        {"name": "Responder", "category": "post_exploit", "reason": "LLMNR/NBT-NS毒化"},
        {"name": "Impacket", "category": "post_exploit", "reason": "横向移动工具集"},
        {"name": "Burp Suite", "category": "web_scan", "reason": "Web应用安全测试"},
        {"name": "Gobuster", "category": "dir_brute", "reason": "目录暴力破解"},
        {"name": "Nikto", "category": "vuln_scan", "reason": "Web服务器漏洞扫描"},
        {"name": "WPScan", "category": "cms_scan", "reason": "WordPress漏洞扫描"},
        {"name": "Searchsploit", "category": "exploit_db", "reason": "Exploit-DB搜索"},
        {"name": "Sn1per", "category": "recon", "reason": "自动化侦察框架"},
    ]
    
    # 检查哪些关键工具缺失
    existing_tool_names = [t['name'].lower() for t in data['tools']]
    missing_critical = []
    
    for tool in critical_tools:
        found = False
        for existing_name in existing_tool_names:
            if tool['name'].lower() in existing_name or existing_name in tool['name'].lower():
                found = True
                # 检查是否已安装
                for t in data['tools']:
                    if tool['name'].lower() in t['name'].lower() or t['name'].lower() in tool['name'].lower():
                        if not t.get('installed', False):
                            print(f"  - {tool['name']}: 在列表中但未安装 ({tool['reason']})")
                        else:
                            print(f"  - {tool['name']}: 已安装 [OK]")
                        break
                break
        
        if not found:
            missing_critical.append(tool)
            print(f"  - {tool['name']}: 完全缺失 ({tool['reason']})")
    
    # 集成优先级建议
    print(f"\n[优先级] 第一阶段集成优先级建议 (4月3日-4月10日):")
    print("  1. Metasploit - 核心渗透测试框架")
    print("  2. Nmap - 端口扫描和漏洞检测")
    print("  3. Hydra - 暴力破解工具")
    print("  4. John the Ripper - 密码破解")
    print("  5. CrackMapExec - Windows域渗透")
    print("  6. LinPEAS/WinPEAS - 权限提升检查")
    print("  7. Mimikatz - Windows凭证提取")
    print("  8. Responder - LLMNR/NBT-NS毒化")
    print("  9. Impacket - 横向移动工具集")
    print("  10. Gobuster - 目录暴力破解")
    
    # 生成行动计划
    print(f"\n[步骤] 具体实施步骤:")
    print("  1. 为每个工具创建Docker容器或安装脚本")
    print("  2. 在backend/tools/目录下创建工具执行模块")
    print("  3. 更新complete_tool_list.json中的安装状态")
    print("  4. 在unified_executor_final.py中集成工具执行逻辑")
    print("  5. 编写测试用例验证工具功能")
    
    return data, critical_tools, missing_critical

if __name__ == "__main__":
    analyze_tools()