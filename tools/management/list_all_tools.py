# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
ClawAI 完整工具清单生成脚本
列出所有37个安全工具的完整状态（已安装和未安装）
按类别分组显示，包含安装指南和路径信息
"""

import json
import os
from datetime import datetime
from pathlib import Path

def load_tool_data():
    """加载工具状态数据"""
    json_path = Path("tool_check_results_updated.json")
    if not json_path.exists():
        # 尝试其他可能的路径
        json_path = Path("reports/tool_check_results_updated.json")
        if not json_path.exists():
            print("错误: 未找到 tool_check_results_updated.json 文件")
            return None
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"错误: 读取JSON文件失败: {e}")
        return None

def get_category_name(category_key):
    """将英文分类键转换为中文分类名"""
    category_map = {
        "network_scan": "网络扫描",
        "vuln_scan": "漏洞扫描", 
        "web_scan": "Web扫描",
        "fingerprint": "指纹识别",
        "http_probe": "HTTP探测",
        "dir_brute": "目录爆破",
        "exploit": "漏洞利用",
        "cms_scan": "CMS扫描",
        "subdomain": "子域名",
        "brute_force": "暴力破解",
        "password_crack": "密码破解",
        "post_exploit": "后期利用",
        "osint": "情报收集",
        "dns": "DNS工具",
        "exploit_db": "漏洞库",
        "ssl": "SSL/TLS",
        "waf": "WAF检测"
    }
    return category_map.get(category_key, category_key)

def format_install_status(tool):
    """格式化安装状态"""
    if tool.get("installed"):
        return "[OK] 已安装"
    else:
        return "[NO] 未安装"

def format_priority_level(priority):
    """格式化优先级"""
    priority_map = {
        "critical": "[CRITICAL] 关键",
        "high": "[HIGH] 高",
        "medium": "[MEDIUM] 中", 
        "low": "[LOW] 低"
    }
    return priority_map.get(priority, priority)

def group_tools_by_category(tools):
    """按类别分组工具"""
    categories = {}
    for tool in tools:
        category = tool["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append(tool)
    
    # 按工具数量排序
    return dict(sorted(categories.items(), key=lambda x: len(x[1]), reverse=True))

def print_complete_tool_list(data):
    """打印完整工具清单"""
    if not data:
        return
    
    tools = data.get("tools", [])
    summary = data.get("summary", {})
    
    print("=" * 80)
    print("ClawAI 完整工具清单")
    print("=" * 80)
    print()
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"系统平台: {summary.get('system', '未知')}")
    print()
    
    # 统计信息
    total = summary.get("total_tools", 37)
    installed = summary.get("installed_tools", 13)
    rate = summary.get("install_rate", 35.1)
    
    print("[STATS] 统计概览:")
    print(f"  总工具数: {total}")
    print(f"  已安装: {installed}")
    print(f"  未安装: {total - installed}")
    print(f"  安装率: {rate:.1f}%")
    print()
    
    # 本地工具目录信息
    local_exists = summary.get("local_tools_directory_exists", False)
    local_count = summary.get("local_tools_count", 0)
    local_installed = summary.get("local_tools_installed", 0)
    
    if local_exists:
        print("[DIR] 本地工具目录:")
        print(f"  目录存在: {'[OK] 是' if local_exists else '[NO] 否'}")
        print(f"  工具数量: {local_count}")
        print(f"  已安装: {local_installed} ({local_count and (local_installed/local_count*100):.1f}%)")
    print()
    
    # 按类别分组显示
    categories = group_tools_by_category(tools)
    
    for category_key, category_tools in categories.items():
        category_name = get_category_name(category_key)
        category_stats = data.get("categories", {}).get(category_key, {})
        cat_total = category_stats.get("total", len(category_tools))
        cat_installed = category_stats.get("installed", 0)
        
        print(f"* {category_name} 类别 ({cat_total}个工具, {cat_installed}个已安装):")
        print("-" * 70)
        
        for i, tool in enumerate(category_tools, 1):
            status = format_install_status(tool)
            priority = format_priority_level(tool.get("priority", "medium"))
            
            print(f"  {i:2d}. {tool['name']} ({tool['tool_id']})")
            print(f"      状态: {status} | 优先级: {priority}")
            print(f"      描述: {tool.get('description', '无描述')}")
            
            if tool.get("installed"):
                path = tool.get("executable_path", "未知路径")
                version = tool.get("version", "未知版本")
                print(f"      路径: {path}")
                print(f"      版本: {version}")
            else:
                install_guide = tool.get("install_guide", "无安装指南")
                print(f"      安装: {install_guide}")
            
            print()
        
        print()

def generate_installation_priority_list(tools):
    """生成安装优先级列表"""
    print("=" * 80)
    print("安装优先级推荐列表")
    print("=" * 80)
    print()
    print("建议按以下顺序安装工具（从高优先级到低优先级）:")
    print()
    
    # 将工具按类别分组，未安装的放在前面
    uninstalled_tools = [t for t in tools if not t.get("installed")]
    installed_tools = [t for t in tools if t.get("installed")]
    
    # 按类别排序
    category_priority = [
        "network_scan",  # 网络扫描是基础
        "web_scan",      # Web扫描
        "vuln_scan",     # 漏洞扫描
        "dir_brute",     # 目录爆破
        "fingerprint",   # 指纹识别
        "http_probe",    # HTTP探测
        "subdomain",     # 子域名
        "exploit",       # 漏洞利用
        "cms_scan",      # CMS扫描
        "brute_force",   # 暴力破解
        "password_crack", # 密码破解
        "osint",         # 情报收集
        "ssl",           # SSL/TLS
        "dns",           # DNS工具
        "exploit_db",    # 漏洞库
        "waf",           # WAF检测
        "post_exploit"   # 后期利用
    ]
    
    # 生成推荐列表
    recommended_order = []
    for category in category_priority:
        cat_tools = [t for t in uninstalled_tools if t["category"] == category]
        cat_tools.sort(key=lambda x: x.get("priority_level", 3))
        recommended_order.extend(cat_tools)
    
    for i, tool in enumerate(recommended_order, 1):
        category_name = get_category_name(tool["category"])
        print(f"{i:2d}. [{tool.get('priority', 'medium').upper()}] {tool['name']} ({tool['tool_id']}) - {category_name}")
        print(f"    描述: {tool.get('description', '无描述')}")
        print(f"    安装: {tool.get('install_guide', '无安装指南')}")
        print()

def save_to_file(data, output_file="complete_tool_list.txt"):
    """将完整清单保存到文件"""
    import sys
    from io import StringIO
    
    # 重定向输出到字符串
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    print_complete_tool_list(data)
    generate_installation_priority_list(data.get("tools", []))
    
    # 获取输出内容
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout
    
    # 写入文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"完整工具清单已保存到: {output_file}")
        return True
    except Exception as e:
        print(f"保存文件失败: {e}")
        return False

def main():
    """主函数"""
    print("正在加载工具数据...")
    data = load_tool_data()
    
    if not data:
        print("无法加载工具数据，请确保 tool_check_results_updated.json 文件存在。")
        return
    
    # 打印完整清单到控制台
    print_complete_tool_list(data)
    
    # 生成安装优先级列表
    generate_installation_priority_list(data.get("tools", []))
    
    # 保存到文件
    save_to_file(data, "complete_tool_list.txt")
    
    # 也保存为JSON格式的完整清单
    try:
        with open("complete_tool_list.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("JSON格式完整清单已保存到: complete_tool_list.json")
    except Exception as e:
        print(f"保存JSON文件失败: {e}")

if __name__ == "__main__":
    main()