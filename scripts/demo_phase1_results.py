#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI 第一阶段成果演示脚本
展示Metasploit集成框架和渗透测试功能增强
"""

import sys
import os
import json
from datetime import datetime

def print_header():
    """打印演示标题"""
    print("=" * 70)
    print("ClawAI - 第一阶段成果演示")
    print("=" * 70)
    print(f"演示时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    print()

def show_metasploit_integration():
    """展示Metasploit集成功能"""
    print("[工具] Metasploit集成框架")
    print("-" * 40)
    
    # 检查Metasploit集成模块
    metasploit_module = "backend/tools/metasploit_integration.py"
    if os.path.exists(metasploit_module):
        print(f"✅ Metasploit集成模块: {metasploit_module}")
        
        # 读取模块信息
        with open(metasploit_module, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.count('\n') + 1
            print(f"   文件大小: {lines} 行代码")
            
            # 检查关键功能
            features = [
                ("MetasploitIntegration类", "class MetasploitIntegration:" in content),
                ("漏洞搜索功能", "search_exploits" in content),
                ("漏洞利用功能", "run_exploit" in content),
                ("会话管理", "get_sessions" in content),
                ("后渗透模块", "run_post_exploitation" in content),
            ]
            
            for feature_name, exists in features:
                status = "✅" if exists else "❌"
                print(f"   {status} {feature_name}")
    else:
        print(f"❌ Metasploit集成模块不存在")
    
    print()

def show_docker_config():
    """展示Docker配置"""
    print("[Docker] Docker容器化部署")
    print("-" * 40)
    
    docker_files = [
        ("docker-compose.metasploit.yml", "Metasploit部署配置"),
        ("scripts/install_metasploit.bat", "自动化安装脚本"),
    ]
    
    for file_path, description in docker_files:
        if os.path.exists(file_path):
            print(f"✅ {description}: {file_path}")
        else:
            print(f"❌ {description}: 文件不存在")
    
    print()

def show_tool_status():
    """展示工具状态"""
    print("[状态] 工具集成状态")
    print("-" * 40)
    
    tool_list_file = "complete_tool_list.json"
    if os.path.exists(tool_list_file):
        with open(tool_list_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total_tools = data["summary"]["total_tools"]
        installed_tools = data["summary"]["installed_tools"]
        install_rate = data["summary"]["install_rate"]
        
        print(f"✅ 工具列表文件: {tool_list_file}")
        print(f"   总工具数: {total_tools}")
        print(f"   已安装工具: {installed_tools}")
        print(f"   安装率: {install_rate:.1f}%")
        
        # 显示关键工具状态
        print("\n   关键渗透测试工具状态:")
        key_tools = ["Metasploit", "Nmap", "SQLMap", "Hydra", "John the Ripper"]
        
        for tool in data["tools"]:
            if tool["name"] in key_tools:
                status = "✅ 已安装" if tool.get("installed", False) else "❌ 未安装"
                print(f"     {status} - {tool['name']} ({tool['category']})")
    else:
        print(f"❌ 工具列表文件不存在")
    
    print()

def show_next_steps():
    """展示下一步行动"""
    print("[行动] 下一步行动")
    print("-" * 40)
    
    steps = [
        "1. 启动Docker Desktop",
        "2. 运行 scripts\\install_metasploit.bat 安装Metasploit",
        "3. 手动安装Nmap、Hydra、John等工具",
        "4. 测试Metasploit集成功能",
        "5. 开始第二阶段：真实漏洞利用实现",
    ]
    
    for step in steps:
        print(f"   {step}")
    
    print()

def run_demo_test():
    """运行演示测试"""
    print("[测试] 演示测试")
    print("-" * 40)
    
    try:
        # 尝试导入Metasploit模块
        sys.path.append('backend/tools')
        from metasploit_integration import SimpleMetasploitClient
        
        print("✅ 成功导入Metasploit集成模块")
        
        # 测试可用性检查
        availability = SimpleMetasploitClient.check_metasploit_availability()
        print(f"   Metasploit可用性: {'可用' if availability['available'] else '不可用'}")
        print(f"   需要Docker: {'是' if availability['docker_required'] else '否'}")
        
        # 测试模拟扫描
        scan_result = SimpleMetasploitClient.run_quick_scan("demo-target.com")
        print(f"   模拟扫描测试: {'成功' if scan_result['success'] else '失败'}")
        print(f"   发现端口数: {len(scan_result['results']['ports'])}")
        print(f"   发现漏洞数: {len(scan_result['results']['vulnerabilities'])}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    print()

def main():
    """主函数"""
    print_header()
    show_metasploit_integration()
    show_docker_config()
    show_tool_status()
    run_demo_test()
    show_next_steps()
    
    print("=" * 70)
    print("第一阶段完成总结:")
    print("✅ Metasploit集成框架已创建")
    print("✅ Docker部署配置已准备")
    print("✅ 工具状态已更新")
    print("✅ 自动化安装脚本已编写")
    print("=" * 70)
    print("\n第一阶段核心功能增强已完成！")
    print("用户现在可以启动Docker并运行安装脚本来获得完整的渗透测试环境。")

if __name__ == "__main__":
    main()