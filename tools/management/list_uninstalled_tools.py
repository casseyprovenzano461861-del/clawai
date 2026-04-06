# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
列出未安装的工具，提供安装指导
"""

import json
import os

def load_tool_status():
    """加载工具状态数据"""
    try:
        with open('tool_check_results_updated.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载工具状态失败: {str(e)}")
        # 尝试加载原始文件
        try:
            with open('tool_check_results_enhanced.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e2:
            print(f"加载原始工具状态也失败: {str(e2)}")
            return None

def categorize_uninstalled_tools(tool_data):
    """按类别分类未安装的工具"""
    if not tool_data or 'tools' not in tool_data:
        return {}
    
    categories = {}
    
    for tool in tool_data['tools']:
        if not tool.get('installed', False):
            category = tool.get('category', 'other')
            if category not in categories:
                categories[category] = []
            
            categories[category].append({
                'name': tool['name'],
                'tool_id': tool['tool_id'],
                'description': tool.get('description', ''),
                'install_guide': tool.get('install_guide', '请搜索安装方法'),
                'priority': tool.get('priority', 'medium')
            })
    
    return categories

def get_installation_priority(tool):
    """获取安装优先级"""
    priority_map = {
        'critical': 1,
        'high': 2,
        'medium': 3,
        'low': 4
    }
    return priority_map.get(tool.get('priority', 'medium'), 3)

def generate_installation_plan(uninstalled_tools):
    """生成安装计划"""
    print("=" * 80)
    print("ClawAI 未安装工具清单及安装指南")
    print("=" * 80)
    
    total_uninstalled = sum(len(tools) for tools in uninstalled_tools.values())
    print(f"未安装工具总数: {total_uninstalled}个")
    print()
    
    # 按类别输出
    for category, tools in sorted(uninstalled_tools.items()):
        print(f"【{category.upper()}】类别 ({len(tools)}个工具)")
        print("-" * 60)
        
        # 按优先级排序
        tools_sorted = sorted(tools, key=lambda x: get_installation_priority(x))
        
        for i, tool in enumerate(tools_sorted, 1):
            priority_symbol = {
                1: "[!]",
                2: "[*]",
                3: "[-]",
                4: "[.]"
            }.get(get_installation_priority(tool), "[-]")
            
            print(f"{priority_symbol} {i}. {tool['name']} ({tool['tool_id']})")
            print(f"   描述: {tool['description']}")
            print(f"   安装: {tool['install_guide']}")
            print()
    
    return total_uninstalled

def generate_category_summary(uninstalled_tools):
    """生成类别摘要"""
    print("=" * 80)
    print("按类别统计")
    print("=" * 80)
    
    for category, tools in sorted(uninstalled_tools.items()):
        print(f"{category}: {len(tools)}个未安装工具")
    
    print()

def generate_priority_recommendations(uninstalled_tools):
    """生成优先级安装建议"""
    print("=" * 80)
    print("安装优先级建议")
    print("=" * 80)
    
    all_tools = []
    for category, tools in uninstalled_tools.items():
        for tool in tools:
            tool['category'] = category
            all_tools.append(tool)
    
    # 按优先级排序
    all_tools_sorted = sorted(all_tools, key=lambda x: get_installation_priority(x))
    
    print("建议按以下顺序安装（从高优先级开始）:")
    print()
    
    for i, tool in enumerate(all_tools_sorted[:15], 1):  # 只显示前15个
        priority_text = {
            1: "[CRITICAL]",
            2: "[HIGH]",
            3: "[MEDIUM]",
            4: "[LOW]"
        }.get(get_installation_priority(tool), "[MEDIUM]")
        
        print(f"{i}. {priority_text} {tool['name']} ({tool['tool_id']}) - {tool['category']}")
    
    if len(all_tools_sorted) > 15:
        print(f"... 和其他 {len(all_tools_sorted) - 15} 个工具")

def generate_windows_installation_guide():
    """生成Windows安装指南"""
    print("=" * 80)
    print("Windows平台安装指南")
    print("=" * 80)
    
    print("1. 使用 Chocolatey 包管理器（推荐）")
    print("   安装 Chocolatey:")
    print("   powershell -Command \"Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))\"")
    print()
    
    print("2. 常用工具安装命令:")
    print("   choco install nmap -y")
    print("   choco install masscan -y")
    print("   choco install go -y  # 安装Go语言环境")
    print("   choco install python -y  # 确保Python已安装")
    print()
    
    print("3. Go语言工具安装:")
    print("   安装Go后，使用以下命令:")
    print("   go install github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest")
    print("   go install github.com/projectdiscovery/httpx/cmd/httpx@latest")
    print("   go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest")
    print()
    
    print("4. Python工具安装:")
    print("   pip install sqlmap")
    print("   pip install dirsearch")
    print("   pip install wafw00f")
    print()
    
    print("5. 手动下载安装:")
    print("   - Nmap: https://nmap.org/download.html")
    print("   - Masscan: https://github.com/robertdavidgraham/masscan/releases")
    print("   - Nikto: https://github.com/sullo/nikto")

def generate_quick_install_script():
    """生成快速安装脚本"""
    print("=" * 80)
    print("快速安装脚本 (Windows)")
    print("=" * 80)
    
    script_content = '''@echo off
echo ClawAI 工具快速安装脚本
echo.

:: 检查是否以管理员身份运行
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 请以管理员身份运行此脚本
    pause
    exit /b 1
)

:: 1. 安装 Chocolatey
echo 步骤1: 安装 Chocolatey 包管理器...
powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"

:: 2. 安装核心工具
echo.
echo 步骤2: 安装核心工具...
choco install nmap -y
choco install masscan -y
choco install go -y
choco install python -y

:: 3. 设置Go环境变量
echo.
echo 步骤3: 设置Go环境变量...
setx GOPATH "%%USERPROFILE%%\\go"
setx PATH "%%USERPROFILE%%\\go\\bin;%%PATH%%"

:: 4. 安装Go语言安全工具
echo.
echo 步骤4: 安装Go语言安全工具...
go install github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest

echo.
echo 安装完成!
echo 请重启命令行窗口以使环境变量生效
pause
'''
    
    print("将以下内容保存为 install_tools.bat 并运行:")
    print(script_content)
    
    # 保存脚本文件
    script_path = "quick_install_tools.bat"
    try:
        with open(script_path, 'w', encoding='gbk') as f:
            f.write(script_content)
        print(f"\n脚本已保存到: {script_path}")
    except Exception as e:
        print(f"保存脚本失败: {str(e)}")

def main():
    """主函数"""
    print("ClawAI 未安装工具分析")
    print("=" * 60)
    
    # 加载工具状态
    tool_data = load_tool_status()
    if not tool_data:
        print("无法加载工具状态数据")
        return 1
    
    # 按类别分类未安装工具
    uninstalled_tools = categorize_uninstalled_tools(tool_data)
    
    if not uninstalled_tools:
        print("恭喜! 所有工具都已安装。")
        return 0
    
    # 生成报告
    total_uninstalled = generate_installation_plan(uninstalled_tools)
    generate_category_summary(uninstalled_tools)
    generate_priority_recommendations(uninstalled_tools)
    generate_windows_installation_guide()
    generate_quick_install_script()
    
    # 保存详细列表
    save_detailed_list(uninstalled_tools)
    
    print("=" * 80)
    print(f"总结: 共有 {total_uninstalled} 个工具需要安装")
    print("建议优先安装网络扫描工具 (nmap, masscan) 和漏洞扫描工具 (nuclei)")
    print("=" * 80)
    
    return 0

def save_detailed_list(uninstalled_tools):
    """保存详细列表到文件"""
    try:
        output_lines = []
        output_lines.append("ClawAI 未安装工具详细清单")
        output_lines.append("=" * 60)
        output_lines.append("")
        
        all_tools = []
        for category, tools in uninstalled_tools.items():
            for tool in tools:
                tool['category'] = category
                all_tools.append(tool)
        
        # 按工具ID排序
        all_tools_sorted = sorted(all_tools, key=lambda x: x['tool_id'])
        
        for tool in all_tools_sorted:
            output_lines.append(f"工具ID: {tool['tool_id']}")
            output_lines.append(f"名称: {tool['name']}")
            output_lines.append(f"类别: {tool['category']}")
            output_lines.append(f"描述: {tool['description']}")
            output_lines.append(f"安装指南: {tool['install_guide']}")
            output_lines.append("-" * 40)
        
        with open('uninstalled_tools_detailed.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        
        print(f"\n详细清单已保存到: uninstalled_tools_detailed.txt")
        
    except Exception as e:
        print(f"保存详细清单失败: {str(e)}")

if __name__ == "__main__":
    main()