# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
ClawAI 工具安装状态摘要生成脚本
生成更清晰的工具安装状态总结，突出显示24个未安装的工具
"""

import json
import os
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

def main():
    """主函数"""
    print("正在加载工具数据...")
    data = load_tool_data()
    
    if not data:
        print("无法加载工具数据，请确保 tool_check_results_updated.json 文件存在。")
        return
    
    tools = data.get("tools", [])
    summary = data.get("summary", {})
    
    # 创建总结文件
    output_file = "tool_installation_summary.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("ClawAI 工具安装状态清晰总结\n")
        f.write("=" * 80 + "\n\n")
        
        # 总体统计
        total = summary.get("total_tools", 37)
        installed = summary.get("installed_tools", 13)
        uninstalled = total - installed
        
        f.write("📊 总体安装状态\n")
        f.write("-" * 40 + "\n")
        f.write(f"总工具数: {total}个\n")
        f.write(f"✅ 已安装: {installed}个 ({installed/total*100:.1f}%)\n")
        f.write(f"❌ 未安装: {uninstalled}个 ({uninstalled/total*100:.1f}%)\n\n")
        
        # 按类别统计
        f.write("📁 按类别统计\n")
        f.write("-" * 40 + "\n")
        
        categories = {}
        for tool in tools:
            category = tool["category"]
            if category not in categories:
                categories[category] = {"total": 0, "installed": 0, "tools": []}
            categories[category]["total"] += 1
            categories[category]["tools"].append(tool)
            if tool.get("installed"):
                categories[category]["installed"] += 1
        
        # 按未安装数量排序
        sorted_categories = sorted(categories.items(), key=lambda x: (x[1]["total"] - x[1]["installed"]), reverse=True)
        
        for category_key, stats in sorted_categories:
            category_name = get_category_name(category_key)
            uninstalled_count = stats["total"] - stats["installed"]
            
            if uninstalled_count > 0:
                f.write(f"{category_name}: {stats['total']}个工具, ❌ {uninstalled_count}个未安装\n")
        
        f.write("\n")
        
        # 本地工具目录说明
        local_exists = summary.get("local_tools_directory_exists", False)
        local_count = summary.get("local_tools_count", 0)
        local_installed = summary.get("local_tools_installed", 0)
        
        f.write("💡 重要说明\n")
        f.write("-" * 40 + "\n")
        f.write("注意: 工具数量统计说明\n")
        f.write("1. 总工具数: 37个安全工具\n")
        f.write("2. 未安装工具: 24个（需要手动安装）\n")
        f.write("3. 本地工具目录: 包含10个预先安装的工具（100%已安装）\n")
        f.write("4. 本地工具目录不是总工具数的全部，只是部分工具\n\n")
        
        # 未安装工具清单
        f.write("❌ 24个未安装工具详细清单\n")
        f.write("-" * 40 + "\n")
        
        uninstalled_tools = [t for t in tools if not t.get("installed")]
        
        for i, tool in enumerate(uninstalled_tools, 1):
            category_name = get_category_name(tool["category"])
            f.write(f"{i:2d}. {tool['name']} ({tool['tool_id']}) - {category_name}\n")
            f.write(f"    描述: {tool.get('description', '无描述')}\n")
            f.write(f"    安装: {tool.get('install_guide', '无安装指南')}\n")
        
        # 安装建议
        f.write("\n🔧 安装建议\n")
        f.write("-" * 40 + "\n")
        f.write("建议按以下顺序安装:\n")
        f.write("1. 网络扫描工具 (Nmap, Masscan, RustScan)\n")
        f.write("2. Web扫描工具 (Nikto)\n")
        f.write("3. 目录爆破工具 (Gobuster, FFUF, Feroxbuster)\n")
        f.write("4. 子域名工具 (Subfinder, Amass, Sublist3r)\n")
        f.write("5. CMS扫描工具 (WPScan, Droopescan)\n")
        f.write("6. 其他工具 (按需安装)\n\n")
        
        # 快速安装脚本提示
        f.write("⚡ 快速安装方法\n")
        f.write("-" * 40 + "\n")
        f.write("已为您生成以下安装文件:\n")
        f.write("1. quick_install_tools.bat - Windows快速安装脚本\n")
        f.write("2. uninstalled_tools_detailed.txt - 未安装工具详细清单\n")
        f.write("3. complete_tool_list.txt - 完整工具清单（包含所有37个工具）\n")
        f.write("\n运行 quick_install_tools.bat 开始批量安装工具\n")
    
    print(f"工具安装状态总结已保存到: {output_file}")
    
    # 在控制台也显示关键信息
    print("\n" + "=" * 60)
    print("工具安装状态关键信息")
    print("=" * 60)
    print(f"✅ 总工具数: {total}个")
    print(f"✅ 已安装: {installed}个 ({installed/total*100:.1f}%)")
    print(f"❌ 未安装: {uninstalled}个 ({uninstalled/total*100:.1f}%)")
    print(f"📁 本地工具目录: {local_count}个工具 ({local_installed}个已安装)")
    print("\n💡 注意: '本地工具目录'的10个工具是预先安装的，不是总工具数")
    print("   完整的37个工具清单见 complete_tool_list.txt")
    print("   24个未安装工具清单见 uninstalled_tools_detailed.txt")

if __name__ == "__main__":
    main()