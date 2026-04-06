# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
工具安装检查模块
统一检查和管理所有安全工具的安装状态
"""

import subprocess
import shutil
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ToolChecker:
    """工具安装检查器"""
    
    def __init__(self):
        # 工具配置：工具名 -> (可执行文件路径, 描述, 类别, 优先级)
        self.tools_config = {
            # ==== 网络扫描类工具 ====
            "nmap": {
                "command": "nmap",
                "description": "端口扫描器",
                "category": "network_scan",
                "priority": 1,
                "required": True,
                "test_command": ["--version"]
            },
            "masscan": {
                "command": "masscan",
                "description": "高速端口扫描器",
                "category": "network_scan",
                "priority": 2,
                "required": False,
                "test_command": ["--version"]
            },
            "rustscan": {
                "command": "rustscan",
                "description": "Rust实现的快速端口扫描器",
                "category": "network_scan",
                "priority": 3,
                "required": False,
                "test_command": ["--version"]
            },
            
            # ==== Web漏洞扫描类工具 ====
            "sqlmap": {
                "command": "sqlmap",
                "description": "SQL注入检测工具",
                "category": "web_vuln",
                "priority": 1,
                "required": False,
                "test_command": ["--version"]
            },
            "wpscan": {
                "command": "wpscan",
                "description": "WordPress安全扫描器",
                "category": "web_vuln",
                "priority": 2,
                "required": False,
                "test_command": ["--version"]
            },
            "nikto": {
                "command": "nikto",
                "description": "Web服务器漏洞扫描器",
                "category": "web_vuln",
                "priority": 3,
                "required": False,
                "test_command": ["-Version"]
            },
            "nuclei": {
                "command": "nuclei",
                "description": "漏洞扫描器",
                "category": "web_vuln",
                "priority": 4,
                "required": False,
                "test_command": ["-version"]
            },
            "whatweb": {
                "command": "whatweb",
                "description": "Web指纹识别工具",
                "category": "web_vuln",
                "priority": 5,
                "required": False,
                "test_command": ["--version"]
            },
            
            # ==== 目录爆破类工具 ====
            "dirsearch": {
                "command": "dirsearch",
                "description": "目录扫描工具",
                "category": "dir_brute",
                "priority": 1,
                "required": False,
                "test_command": ["--version"]
            },
            "feroxbuster": {
                "command": "feroxbuster",
                "description": "Rust目录爆破工具",
                "category": "dir_brute",
                "priority": 2,
                "required": False,
                "test_command": ["--version"]
            },
            "gobuster": {
                "command": "gobuster",
                "description": "Go目录爆破工具",
                "category": "dir_brute",
                "priority": 3,
                "required": False,
                "test_command": ["--version"]
            },
            "ffuf": {
                "command": "ffuf",
                "description": "Web模糊测试工具",
                "category": "dir_brute",
                "priority": 4,
                "required": False,
                "test_command": ["-V"]
            },
            
            # ==== 信息收集类工具 ====
            "httpx": {
                "command": "httpx",
                "description": "HTTP探测工具",
                "category": "info_gathering",
                "priority": 1,
                "required": False,
                "test_command": ["-version"]
            },
            "subfinder": {
                "command": "subfinder",
                "description": "子域名枚举工具",
                "category": "info_gathering",
                "priority": 2,
                "required": False,
                "test_command": ["-version"]
            },
            "amass": {
                "command": "amass",
                "description": "深度子域名枚举工具",
                "category": "info_gathering",
                "priority": 3,
                "required": False,
                "test_command": ["-version"]
            },
            "sublist3r": {
                "command": "sublist3r",
                "description": "子域名枚举工具（Python）",
                "category": "info_gathering",
                "priority": 4,
                "required": False,
                "test_command": ["-h"]
            },
            "dnsrecon": {
                "command": "dnsrecon",
                "description": "DNS信息收集工具",
                "category": "info_gathering",
                "priority": 5,
                "required": False,
                "test_command": ["-h"]
            },
            
            # ==== 其他安全工具 ====
            "crackmapexec": {
                "command": "crackmapexec",
                "description": "Windows域渗透测试工具",
                "category": "post_exploitation",
                "priority": 1,
                "required": False,
                "test_command": ["--version"]
            },
            "wafw00f": {
                "command": "wafw00f",
                "description": "WAF检测工具",
                "category": "web_vuln",
                "priority": 6,
                "required": False,
                "test_command": ["--version"]
            },
            "testssl": {
                "command": "testssl",
                "description": "SSL/TLS安全测试工具",
                "category": "security_testing",
                "priority": 1,
                "required": False,
                "test_command": ["--version"]
            },
            "sslscan": {
                "command": "sslscan",
                "description": "SSL安全扫描器",
                "category": "security_testing",
                "priority": 2,
                "required": False,
                "test_command": ["--version"]
            },
            
            # ==== 密码破解类工具（保持模拟） ====
            "hydra": {
                "command": "hydra",
                "description": "密码破解工具",
                "category": "password_cracking",
                "priority": 1,
                "required": False,
                "test_command": ["-V"]
            },
            "john": {
                "command": "john",
                "description": "John the Ripper密码破解工具",
                "category": "password_cracking",
                "priority": 2,
                "required": False,
                "test_command": ["--version"]
            },
            "hashcat": {
                "command": "hashcat",
                "description": "高级密码恢复工具",
                "category": "password_cracking",
                "priority": 3,
                "required": False,
                "test_command": ["--version"]
            },
        }
    
    @staticmethod
    def is_tool_installed(tool_name: str) -> bool:
        """检查工具是否已安装"""
        return shutil.which(tool_name) is not None
    
    def check_tool(self, tool_name: str) -> Dict[str, Any]:
        """检查单个工具的安装状态"""
        if tool_name not in self.tools_config:
            return {
                "tool_name": tool_name,
                "installed": False,
                "error": f"工具 {tool_name} 未在配置中定义"
            }
        
        config = self.tools_config[tool_name]
        command = config["command"]
        test_command = config.get("test_command", ["--version"])
        
        is_installed = self.is_tool_installed(command)
        is_working = False
        version_info = ""
        error_message = ""
        
        if is_installed:
            try:
                # 尝试运行测试命令验证工具是否工作
                cmd = [command] + test_command
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    encoding='utf-8',
                    errors='ignore'
                )
                
                if result.returncode == 0 or result.returncode == 1:  # 很多工具用返回码1显示版本
                    is_working = True
                    version_output = result.stdout[:200] if result.stdout else result.stderr[:200]
                    version_info = version_output.strip().split('\n')[0] if version_output else ""
                else:
                    error_message = f"命令返回码: {result.returncode}"
                    if result.stderr:
                        error_message += f", 错误: {result.stderr[:100]}"
                    
            except subprocess.TimeoutExpired:
                error_message = "命令执行超时"
            except Exception as e:
                error_message = f"执行错误: {str(e)}"
        
        return {
            "tool_name": tool_name,
            "command": command,
            "description": config["description"],
            "category": config["category"],
            "priority": config["priority"],
            "required": config["required"],
            "installed": is_installed,
            "working": is_working,
            "version": version_info,
            "error": error_message,
            "config_available": True
        }
    
    def check_all_tools(self) -> Dict[str, Any]:
        """检查所有工具安装状态"""
        logger.info("开始检查所有工具安装状态...")
        
        results = {}
        installed_count = 0
        working_count = 0
        required_installed = True
        
        for tool_name in sorted(self.tools_config.keys()):
            result = self.check_tool(tool_name)
            results[tool_name] = result
            
            if result["installed"]:
                installed_count += 1
            if result["working"]:
                working_count += 1
            
            if result["required"] and not result["working"]:
                required_installed = False
        
        total_tools = len(self.tools_config)
        stats = {
            "total_tools": total_tools,
            "installed_tools": installed_count,
            "working_tools": working_count,
            "installed_percentage": (installed_count / total_tools * 100) if total_tools > 0 else 0,
            "working_percentage": (working_count / total_tools * 100) if total_tools > 0 else 0,
            "all_required_installed": required_installed,
            "categories": {}
        }
        
        # 按类别统计
        for tool_name, result in results.items():
            category = result["category"]
            if category not in stats["categories"]:
                stats["categories"][category] = {
                    "total": 0,
                    "installed": 0,
                    "working": 0
                }
            
            stats["categories"][category]["total"] += 1
            if result["installed"]:
                stats["categories"][category]["installed"] += 1
            if result["working"]:
                stats["categories"][category]["working"] += 1
        
        logger.info(f"工具检查完成: {installed_count}/{total_tools} 个工具已安装")
        
        return {
            "statistics": stats,
            "results": results
        }
    
    def check_tools_by_category(self, category: str) -> Dict[str, Any]:
        """按类别检查工具"""
        category_tools = {}
        for tool_name, config in self.tools_config.items():
            if config["category"] == category:
                category_tools[tool_name] = config
        
        if not category_tools:
            return {"error": f"类别 {category} 没有配置的工具"}
        
        results = {}
        for tool_name in category_tools:
            results[tool_name] = self.check_tool(tool_name)
        
        return {
            "category": category,
            "results": results
        }
    
    def generate_installation_report(self, detailed: bool = True) -> str:
        """生成安装报告"""
        check_result = self.check_all_tools()
        stats = check_result["statistics"]
        results = check_result["results"]
        
        report_lines = [
            "=" * 80,
            "ClawAI 工具安装状态报告",
            "=" * 80,
            f"总工具数: {stats['total_tools']}",
            f"已安装工具: {stats['installed_tools']} ({stats['installed_percentage']:.1f}%)",
            f"工作正常工具: {stats['working_tools']} ({stats['working_percentage']:.1f}%)",
            f"必需工具安装状态: {'✅ 全部安装' if stats['all_required_installed'] else '❌ 有缺失'}",
            "=" * 80
        ]
        
        if detailed:
            # 按类别显示
            report_lines.append("\n按类别统计:")
            report_lines.append("-" * 60)
            for category, cat_stats in stats["categories"].items():
                installed_pct = (cat_stats["installed"] / cat_stats["total"] * 100) if cat_stats["total"] > 0 else 0
                report_lines.append(f"{category:20} {cat_stats['installed']:3}/{cat_stats['total']:3} ({installed_pct:5.1f}%)")
            
            # 显示工具详情
            report_lines.append("\n\n工具详情:")
            report_lines.append("-" * 100)
            report_lines.append(f"{'工具名称':20} {'状态':10} {'版本/错误':50}")
            report_lines.append("-" * 100)
            
            for tool_name in sorted(results.keys()):
                result = results[tool_name]
                status = "✅ 正常" if result["working"] else ("⚠️  已安装" if result["installed"] else "❌ 未安装")
                info = result["version"] if result["version"] else (result["error"] if result["error"] else "")
                info = info[:48] + "..." if len(info) > 48 else info
                report_lines.append(f"{tool_name:20} {status:10} {info:50}")
        
        report_lines.append("\n" + "=" * 80)
        report_lines.append("说明:")
        report_lines.append("- ✅ 正常: 工具已安装且工作正常")
        report_lines.append("- ⚠️  已安装: 工具已安装但测试失败")
        report_lines.append("- ❌ 未安装: 工具未安装")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def get_installation_guide(self, tool_name: str) -> Optional[str]:
        """获取工具安装指南"""
        installation_guides = {
            "nmap": """
nmap 安装指南:
  Windows:
    1. 下载: https://nmap.org/download.html
    2. 运行安装程序
    3. 将nmap添加到系统PATH
    
  Linux (Ubuntu/Debian):
    sudo apt-get update
    sudo apt-get install nmap
    
  macOS:
    brew install nmap
""",
            "masscan": """
masscan 安装指南:
  Linux (源码编译):
    sudo apt-get install git gcc make libpcap-dev
    git clone https://github.com/robertdavidgraham/masscan
    cd masscan
    make
    sudo make install
    
  Windows:
    1. 下载: https://github.com/robertdavidgraham/masscan/releases
    2. 解压并添加路径到系统PATH
""",
            "wpscan": """
wpscan 安装指南:
  Docker方式:
    docker pull wpscanteam/wpscan
    使用: docker run --rm wpscanteam/wpscan --url <target>
    
  Ruby方式:
    gem install wpscan
    
  Linux (Ubuntu):
    sudo apt-get install wpscan
""",
            "nikto": """
nikto 安装指南:
  Linux (Ubuntu/Debian):
    sudo apt-get update
    sudo apt-get install nikto
    
  macOS:
    brew install nikto
    
  其他系统:
    下载: https://github.com/sullo/nikto
    运行: perl nikto.pl -h <target>
""",
            "nuclei": """
nuclei 安装指南:
  所有平台:
    go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
    或从 https://github.com/projectdiscovery/nuclei/releases 下载
    
  初始化模板:
    nuclei -update-templates
"""
        }
        
        return installation_guides.get(tool_name)
    
    def save_check_results(self, filepath: str = "tool_check_results.json"):
        """保存检查结果到文件"""
        check_result = self.check_all_tools()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(check_result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"检查结果已保存到: {filepath}")
        return filepath


def main():
    """主函数：测试工具检查器"""
    print("ClawAI 工具安装检查器")
    print("=" * 60)
    
    checker = ToolChecker()
    
    # 检查所有工具
    print("正在检查工具安装状态...")
    check_result = checker.check_all_tools()
    stats = check_result["statistics"]
    
    # 显示简要报告
    print(f"\n检查完成:")
    print(f"  总工具数: {stats['total_tools']}")
    print(f"  已安装工具: {stats['installed_tools']} ({stats['installed_percentage']:.1f}%)")
    print(f"  工作正常工具: {stats['working_tools']} ({stats['working_percentage']:.1f}%)")
    
    # 显示必需工具状态
    required_tools = [name for name, config in checker.tools_config.items() if config["required"]]
    print(f"\n必需工具检查 ({len(required_tools)} 个):")
    for tool_name in required_tools:
        result = check_result["results"][tool_name]
        status = "[OK]" if result["working"] else "[ERR]"
        print(f"  {status} {tool_name}: {result['version'] or result['error']}")
    
    # 生成详细报告
    report = checker.generate_installation_report(detailed=True)
    print(f"\n{report}")
    
    # 保存结果
    checker.save_check_results()
    
    # 提供建议
    print("\n安装建议:")
    installed_count = stats["installed_tools"]
    total_count = stats["total_tools"]
    
    if installed_count < total_count * 0.5:
        print("  ⚠️  超过一半的工具未安装，建议按以下顺序安装:")
        print("    1. nmap (必需)")
        print("    2. wpscan, nikto, nuclei (Web扫描)")
        print("    3. dirsearch, feroxbuster (目录爆破)")
    elif installed_count < total_count * 0.8:
        print("  ⚠️  部分工具未安装，建议安装剩余工具以提高覆盖率")
        print("    检查工具详情查看具体未安装的工具")
    else:
        print("  ✅ 工具安装状态良好")
    
    return check_result


if __name__ == "__main__":
    main()