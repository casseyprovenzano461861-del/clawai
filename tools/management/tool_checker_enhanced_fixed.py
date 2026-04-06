# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
增强版工具安装检查器
检查系统中已安装的渗透测试工具，包括C:\Tools目录中的工具，为缺失工具提供安装指导
"""

import os
import sys
import json
import shutil
import subprocess
import platform
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@dataclass
class ToolStatus:
    """工具状态"""
    name: str
    tool_id: str
    description: str
    category: str
    installed: bool
    executable_path: Optional[str]
    version: Optional[str]
    install_guide: str
    priority: str  # critical, high, medium, low
    
    def to_dict(self):
        """转换为字典"""
        result = asdict(self)
        result["priority_level"] = {
            "critical": 1,
            "high": 2, 
            "medium": 3,
            "low": 4
        }[self.priority]
        return result

class EnhancedToolChecker:
    """增强版工具安装检查器"""
    
    def __init__(self):
        self.system = platform.system().lower()  # windows, linux, darwin
        self.tools_directory = r"C:\Tools"
        
    def check_tool(self, tool_id: str, tool_info: Dict) -> ToolStatus:
        """检查单个工具的安装状态"""
        name = tool_info.get("name", tool_id)
        description = tool_info.get("description", "")
        category = tool_info.get("category", "other")
        priority = tool_info.get("priority", "medium")
        
        # 检查是否已安装
        installed = False
        executable_path = None
        version = None
        install_guide = ""
        
        # 如果是Python工具，检查模块导入
        if tool_id in ["planner", "tool_registry", "tool_validator"]:
            installed = True
            executable_path = "Python module"
            version = "1.0"
            install_guide = "Python模块，项目自带"
            return ToolStatus(name, tool_id, description, category, installed, executable_path, version, install_guide, priority)
        
        # 1. 先检查C:\Tools目录中的工具
        custom_path = self._find_in_tools_directory(tool_id)
        if custom_path:
            installed = True
            executable_path = custom_path
            version = self._get_tool_version(custom_path, tool_id)
        else:
            # 2. 如果C:\Tools中没有，检查标准PATH
            command_names = self._get_tool_commands(tool_id)
            
            for cmd in command_names:
                path = shutil.which(cmd)
                if path:
                    installed = True
                    executable_path = path
                    version = self._get_tool_version(cmd, tool_id)
                    break
        
        # 生成安装指导
        if not installed:
            install_guide = self._generate_install_guide(tool_id)
        else:
            if custom_path:
                install_guide = f"[已安装于] {executable_path} (在C:\\Tools目录)"
            else:
                install_guide = f"[已安装于] {executable_path}"
        
        return ToolStatus(name, tool_id, description, category, installed, executable_path, version, install_guide, priority)
    
    def _find_in_tools_directory(self, tool_id: str) -> Optional[str]:
        """在C:\Tools目录中查找工具"""
        if not os.path.exists(self.tools_directory):
            return None
        
        # 工具ID到可能路径的映射
        tool_paths = {
            "httpx": [r"httpx\httpx.exe"],
            "nuclei": [r"nuclei\nuclei.exe"],
            "whatweb": [r"WhatWeb\whatweb", r"WhatWeb\whatweb.exe"],
            "masscan": [r"masscan-master\masscan.exe", r"masscan-master\bin\masscan.exe"],
            "nikto": [r"nikto-main\program\nikto.pl"],
            "dirsearch": [r"dirsearch\dirsearch.py"],
            "sqlmap": [r"sqlmap\sqlmap.py"],
        }
        
        # 如果tool_id在映射中，检查相应路径
        if tool_id in tool_paths:
            for relative_path in tool_paths[tool_id]:
                full_path = os.path.join(self.tools_directory, relative_path)
                if os.path.exists(full_path):
                    return full_path
        
        # 通用检查：工具名对应的exe或目录
        possible_paths = [
            os.path.join(self.tools_directory, tool_id, f"{tool_id}.exe"),
            os.path.join(self.tools_directory, tool_id, tool_id),
            os.path.join(self.tools_directory, f"{tool_id}.exe"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _get_tool_commands(self, tool_id: str) -> List[str]:
        """获取工具的常用命令名"""
        command_map = {
            "nmap": ["nmap"],
            "masscan": ["masscan"],
            "rustscan": ["rustscan"],
            "nuclei": ["nuclei"],
            "nikto": ["nikto"],
            "whatweb": ["whatweb"],
            "httpx": ["httpx"],
            "dirsearch": ["dirsearch"],
            "gobuster": ["gobuster"],
            "ffuf": ["ffuf"],
            "feroxbuster": ["feroxbuster"],
            "sqlmap": ["sqlmap"],
            "xsstrike": ["xsstrike"],
            "commix": ["commix"],
            "tplmap": ["tplmap"],
            "wpscan": ["wpscan"],
            "joomscan": ["joomscan"],
            "droopescan": ["droopescan"],
            "cmsmap": ["cmsmap"],
            "subfinder": ["subfinder"],
            "amass": ["amass"],
            "sublist3r": ["sublist3r"],
            "hydra": ["hydra"],
            "medusa": ["medusa"],
            "john": ["john", "johnny"],
            "hashcat": ["hashcat"],
            "metasploit": ["msfconsole", "msfvenom"],
            "impacket_tool": ["secretsdump", "psexec"],
            "crackmapexec": ["crackmapexec", "cme"],
            "evil_winrm": ["evil-winrm"],
            "theharvester": ["theharvester"],
            "dnsrecon": ["dnsrecon"],
            "whois_tool": ["whois"],
            "searchsploit": ["searchsploit"],
            "sslscan": ["sslscan"],
            "testssl": ["testssl"],
            "wafw00f": ["wafw00f"],
        }
        
        # 默认命令名
        return command_map.get(tool_id, [tool_id])
    
    def _get_tool_version(self, command: str, tool_id: str) -> Optional[str]:
        """获取工具版本"""
        version_args = self._get_version_arguments(tool_id)
        
        try:
            # 对于Windows上的.exe文件，直接使用绝对路径
            if command.endswith('.exe'):
                cmd_list = [command]
            else:
                cmd_list = [command]
            
            result = subprocess.run(
                cmd_list + version_args,
                capture_output=True,
                text=True,
                timeout=5,
                encoding='utf-8',
                errors='ignore'
            )
            
            # 提取版本信息
            output = result.stdout or result.stderr or ""
            return self._extract_version(output, tool_id)
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            return f"无法获取版本: {str(e)[:50]}"
    
    def _get_version_arguments(self, tool_id: str) -> List[str]:
        """获取版本参数"""
        version_args_map = {
            "python": ["--version"],
            "nikto": ["-Version"],
            "ffuf": ["-V"],
            "gobuster": ["--version"],
            "feroxbuster": ["--version"],
            "wpscan": ["--version"],
            "masscan": ["--version"],
            "nuclei": ["-version"],
            "sqlmap": ["--version"],
            "httpx": ["-version"],
        }
        
        return version_args_map.get(tool_id, ["--version"])
    
    def _extract_version(self, text: str, tool_id: str) -> str:
        """从文本中提取版本号"""
        if not text:
            return "未知版本"
        
        # 常见版本模式
        version_patterns = [
            r'(\d+\.\d+\.\d+)',      # 1.2.3
            r'(\d+\.\d+)',          # 1.2
            r'v(\d+\.\d+\.\d+)',    # v1.2.3
            r'version\s+(\d+\.\d+\.\d+)',  # version 1.2.3
            r'(\d{4}[\d\.\-]+)',    # 2024.1.2
        ]
        
        lines = text.split('\n')
        for line in lines[:5]:  # 只检查前5行
            line = line.strip()
            for pattern in version_patterns:
                import re
                match = re.search(pattern, line)
                if match:
                    version = match.group(1)
                    if '.' in version or '-' in version:
                        return version
        
        # 如果没有匹配的版本号，返回第一行的一部分
        return lines[0][:50] if lines else text[:50]
    
    def _generate_install_guide(self, tool_id: str) -> str:
        """生成安装指导"""
        install_guides = {
            "nmap": "Windows: 从 https://nmap.org/download.html 下载安装包\nLinux: sudo apt install nmap 或 sudo yum install nmap",
            "masscan": "Windows: 从 https://github.com/robertdavidgraham/masscan 下载\nLinux: git clone https://github.com/robertdavidgraham/masscan && cd masscan && make",
            "sqlmap": "git clone https://github.com/sqlmapproject/sqlmap.git",
            "nuclei": "go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest",
            "dirsearch": "git clone https://github.com/maurosoria/dirsearch.git",
            "nikto": "git clone https://github.com/sullo/nikto",
            "wpscan": "需要Ruby: gem install wpscan",
            "whatweb": "git clone https://github.com/urbanadventurer/WhatWeb",
            "httpx": "go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest",
            "gobuster": "go install github.com/OJ/gobuster/v3@latest",
            "ffuf": "go install github.com/ffuf/ffuf@latest",
            "feroxbuster": "从 https://github.com/epi052/feroxbuster/releases 下载",
            "subfinder": "go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
            "amass": "go install -v github.com/owasp-amass/amass/v3/...@master",
        }
        
        if tool_id in install_guides:
            return install_guides[tool_id]
        
        # 默认安装建议
        return f"请搜索 '{tool_id} installation guide' 查找安装方法"
    
    def check_all_tools(self) -> Dict[str, Any]:
        """检查所有工具"""
        try:
            # 导入tool_registry获取工具列表
            from backend.tools.tool_registry import ToolRegistry
            
            registry = ToolRegistry()
            all_tools = []
            
            for tool_id, tool_info in registry.TOOLS.items():
                try:
                    status = self.check_tool(tool_id, tool_info)
                    all_tools.append(status.to_dict())
                    print(f"检查: {tool_id} - {'[已安装]' if status.installed else '[未安装]'}")
                except Exception as e:
                    print(f"检查 {tool_id} 时出错: {str(e)}")
                    all_tools.append({
                        "name": tool_info.get("name", tool_id),
                        "tool_id": tool_id,
                        "description": tool_info.get("description", ""),
                        "category": tool_info.get("category", "other"),
                        "installed": False,
                        "executable_path": None,
                        "version": None,
                        "install_guide": f"检查出错: {str(e)}",
                        "priority": tool_info.get("priority", "medium"),
                        "priority_level": 3
                    })
            
            # 统计
            total_tools = len(all_tools)
            installed_tools = sum(1 for t in all_tools if t["installed"])
            install_rate = installed_tools / total_tools * 100 if total_tools > 0 else 0
            
            # 按类别统计
            categories = {}
            for tool in all_tools:
                cat = tool["category"]
                if cat not in categories:
                    categories[cat] = {"total": 0, "installed": 0}
                categories[cat]["total"] += 1
                if tool["installed"]:
                    categories[cat]["installed"] += 1
            
            # 按优先级统计
            priority_stats = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for tool in all_tools:
                priority = tool.get("priority", "medium")
                if priority in priority_stats:
                    priority_stats[priority] += 1
            
            # 检查C:\Tools目录是否存在
            c_tools_exists = os.path.exists(self.tools_directory)
            
            return {
                "summary": {
                    "total_tools": total_tools,
                    "installed_tools": installed_tools,
                    "install_rate": install_rate,
                    "system": self.system,
                    "timestamp": self._get_timestamp(),
                    "c_tools_directory_exists": c_tools_exists
                },
                "categories": categories,
                "priority_stats": priority_stats,
                "tools": all_tools
            }
            
        except ImportError as e:
            print(f"无法导入tool_registry: {str(e)}")
            # 返回模拟数据用于测试
            return self._generate_sample_data()
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _generate_sample_data(self) -> Dict[str, Any]:
        """生成示例数据（用于测试）"""
        return {
            "summary": {
                "total_tools": 37,
                "installed_tools": 14,
                "install_rate": 37.8,
                "system": self.system,
                "timestamp": self._get_timestamp()
            },
            "categories": {
                "network_scan": {"total": 3, "installed": 1},
                "web_scan": {"total": 4, "installed": 2},
                "dir_brute": {"total": 4, "installed": 1},
                "exploit": {"total": 4, "installed": 1},
                "cms_scan": {"total": 4, "installed": 0},
                "subdomain": {"total": 3, "installed": 0},
                "brute_force": {"total": 4, "installed": 0},
                "post_exploit": {"total": 4, "installed": 0},
                "osint": {"total": 3, "installed": 1},
                "other": {"total": 4, "installed": 1}
            },
            "priority_stats": {"critical": 5, "high": 10, "medium": 15, "low": 7},
            "tools": []
        }
    
    def generate_report(self, check_results: Dict[str, Any]) -> str:
        """生成检查报告"""
        summary = check_results["summary"]
        categories = check_results["categories"]
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("ClawAI 增强版工具安装状态检查报告")
        report_lines.append("=" * 80)
        
        report_lines.append(f"\n[总体统计]:")
        report_lines.append(f"  系统平台: {summary['system'].title()}")
        report_lines.append(f"  工具总数: {summary['total_tools']}")
        report_lines.append(f"  已安装工具: {summary['installed_tools']}")
        report_lines.append(f"  安装率: {summary['install_rate']:.1f}%")
        
        if summary.get('c_tools_directory_exists'):
            report_lines.append(f"  C:\\Tools目录: [存在]")
        else:
            report_lines.append(f"  C:\\Tools目录: [不存在]")
        
        report_lines.append(f"\n[按类别统计]:")
        for category, stats in sorted(categories.items()):
            rate = stats["installed"] / stats["total"] * 100 if stats["total"] > 0 else 0
            progress_bar = self._create_progress_bar(rate)
            report_lines.append(f"  {category}: {stats['installed']}/{stats['total']} {progress_bar} ({rate:.1f}%)")
        
        report_lines.append(f"\n[需要优先安装的工具]:")
        
        # 找出未安装的高优先级工具
        uninstalled_tools = []
        for tool in check_results.get("tools", []):
            if not tool["installed"]:
                priority_level = tool.get("priority_level", 3)
                uninstalled_tools.append((priority_level, tool))
        
        # 按优先级排序
        uninstalled_tools.sort(key=lambda x: x[0])
        
        for i, (priority_level, tool) in enumerate(uninstalled_tools[:10], 1):
            priority_name = {1: "CRITICAL", 2: "HIGH", 3: "MEDIUM", 4: "LOW"}.get(priority_level, "MEDIUM")
            report_lines.append(f"  {i}. [{priority_name}] {tool['name']} ({tool['tool_id']})")
        
        report_lines.append(f"\n[安装建议]:")
        
        # 系统特定的安装建议
        if self.system == "windows":
            report_lines.append("  1. 安装 Chocolatey (包管理器): https://chocolatey.org/")
            report_lines.append("  2. 使用 choco install <tool> 安装工具")
            report_lines.append("  3. 或将C:\\Tools目录添加到PATH环境变量")
            report_lines.append("      set PATH=C:\\Tools\\httpx;%PATH%")
            report_lines.append("      set PATH=C:\\Tools\\nuclei;%PATH%")
        
        report_lines.append(f"\n[快速开始]:")
        report_lines.append("  1. 安装 nmap (端口扫描基础)")
        report_lines.append("  2. 安装 nuclei (漏洞扫描)")
        report_lines.append("  3. 安装 dirsearch (目录爆破)")
        report_lines.append("  4. 安装 httpx (HTTP探测)")
        
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def _create_progress_bar(self, percentage: float, width: int = 20) -> str:
        """创建进度条"""
        filled = int(width * percentage / 100)
        bar = "#" * filled + "." * (width - filled)
        return f"[{bar}]"
    
    def save_results(self, check_results: Dict[str, Any], filename: str = "tool_check_results_enhanced.json"):
        """保存检查结果到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(check_results, f, indent=2, ensure_ascii=False)
            print(f"[结果已保存到]: {filename}")
        except Exception as e:
            print(f"[保存结果失败]: {str(e)}")
    
    def print_detailed_list(self, check_results: Dict[str, Any]):
        """打印详细工具列表"""
        tools = check_results.get("tools", [])
        
        print(f"\n[详细工具列表] ({len(tools)}个工具):")
        print("-" * 100)
        
        # 按类别分组
        categories = {}
        for tool in tools:
            cat = tool["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(tool)
        
        for category, category_tools in sorted(categories.items()):
            print(f"\n[{category.upper()}] ({len(category_tools)}个工具)")
            
            for tool in sorted(category_tools, key=lambda x: x["tool_id"]):
                status = "[已安装]" if tool["installed"] else "[未安装]"
                version_info = f" ({tool['version']})" if tool["version"] else ""
                location = " (在C:\\Tools)" if "C:\\Tools" in str(tool.get('executable_path', '')) else ""
                print(f"  {status} {tool['tool_id']:20} - {tool['name']}{version_info}{location}")
                
                if not tool["installed"] and tool.get("install_guide"):
                    guide_lines = tool["install_guide"].split('\n')
                    for line in guide_lines[:2]:  # 只显示前两行
                        print(f"      [提示] {line}")
                    if len(guide_lines) > 2:
                        print(f"      ... 更多安装选项")

def main():
    """主函数"""
    print("[ClawAI 增强版工具安装检查器]")
    print("正在检查系统中已安装的工具（包括C:\\Tools目录）...")
    
    checker = EnhancedToolChecker()
    
    # 检查所有工具
    check_results = checker.check_all_tools()
    
    # 生成并打印报告
    report = checker.generate_report(check_results)
    print(report)
    
    # 打印详细列表
    checker.print_detailed_list(check_results)
    
    # 保存结果
    checker.save_results(check_results)
    
    # 检查C:\Tools目录状态
    if os.path.exists(checker.tools_directory):
        print(f"\n[C:\\Tools目录内容]:")
        try:
            import subprocess
            result = subprocess.run(["powershell", "-Command", "Get-ChildItem", checker.tools_directory, "-Directory"], 
                                  capture_output=True, text=True)
            if result.stdout:
                print(result.stdout[:500])
        except:
            print("  无法列出目录内容")
    
    # 检查是否需要安装基础工具
    summary = check_results["summary"]
    if summary["install_rate"] < 50:
        print(f"\n[注意] 工具安装率较低 ({summary['install_rate']:.1f}%)，建议:")
        print("   1. 将已下载工具添加到PATH环境变量")
        print("   2. 安装缺失的核心工具")
        print("   3. 运行 add_tools_to_path.bat 配置工具路径")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())