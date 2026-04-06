# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
增强的真实执行监控系统
整合工具安装检查、健康检查和真实执行比例监控
"""

import os
import sys
import json
import time
import datetime
import subprocess
import shutil
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import platform

# 可选导入 matplotlib
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@dataclass
class EnhancedToolStatus:
    """增强的工具状态"""
    tool_id: str
    name: str
    description: str
    category: str
    priority: str  # P0, P1, P2
    installed: bool
    executable_path: Optional[str]
    version: Optional[str]
    health_status: str  # healthy, warning, error
    real_execution_capable: bool
    test_output: Optional[str]
    last_check: float
    installation_method: Optional[str]
    installation_guide: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result["priority_level"] = {
            "P0": 1,
            "P1": 2,
            "P2": 3
        }[self.priority]
        return result

@dataclass
class EnhancedExecutionStats:
    """增强的执行统计"""
    timestamp: str
    total_tools: int
    installed_tools: int
    installation_rate: float
    healthy_tools: int
    health_rate: float
    real_execution_tools: int
    real_execution_rate: float
    p0_tools_installed: int
    p0_tools_total: int
    p0_installation_rate: float
    details: Dict[str, Any]

class EnhancedRealExecutionMonitor:
    """增强的真实执行监控器"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.history_file = "reports/enhanced_real_execution_history.json"
        self.tool_configs = self._load_tool_configs()
        self.history = self._load_history()
    
    def _load_tool_configs(self) -> Dict[str, Dict[str, Any]]:
        """加载工具配置"""
        # 工具优先级配置
        return {
            "P0": {  # 核心工具，必需，100%真实执行
                "nmap": {
                    "name": "Nmap",
                    "description": "端口扫描工具",
                    "category": "network_scan",
                    "check_command": ["nmap", "--version"],
                    "test_args": ["--version"],
                    "min_version": "7.80",
                    "real_execution_capable": True
                },
                "whatweb": {
                    "name": "WhatWeb",
                    "description": "Web指纹识别工具",
                    "category": "web_scan",
                    "check_command": ["whatweb", "--version"],
                    "test_args": ["--version"],
                    "min_version": "0.5.0",
                    "real_execution_capable": True
                },
                "httpx": {
                    "name": "HTTPX",
                    "description": "HTTP探测与存活检测",
                    "category": "web_scan",
                    "check_command": ["httpx", "--version"],
                    "test_args": ["--version"],
                    "min_version": "1.3.0",
                    "real_execution_capable": True
                },
                "nuclei": {
                    "name": "Nuclei",
                    "description": "漏洞扫描工具",
                    "category": "vulnerability_scan",
                    "check_command": ["nuclei", "--version"],
                    "test_args": ["--version"],
                    "min_version": "3.0.0",
                    "real_execution_capable": True
                }
            },
            "P1": {  # 重要工具，优先安装，90%真实执行
                "sqlmap": {
                    "name": "SQLMap",
                    "description": "SQL注入检测工具",
                    "category": "web_scan",
                    "check_command": ["sqlmap", "--version"],
                    "test_args": ["--version"],
                    "min_version": "1.7.0",
                    "real_execution_capable": True
                },
                "nikto": {
                    "name": "Nikto",
                    "description": "Web服务器漏洞扫描器",
                    "category": "web_scan",
                    "check_command": ["nikto", "-Version"],
                    "test_args": ["-Version"],
                    "min_version": "2.5.0",
                    "real_execution_capable": True
                },
                "masscan": {
                    "name": "Masscan",
                    "description": "高速端口扫描器",
                    "category": "network_scan",
                    "check_command": ["masscan", "--version"],
                    "test_args": ["--version"],
                    "min_version": "1.3.0",
                    "real_execution_capable": True
                },
                "dirsearch": {
                    "name": "Dirsearch",
                    "description": "Web目录爆破工具",
                    "category": "web_scan",
                    "check_command": ["dirsearch", "--version"],
                    "test_args": ["--version"],
                    "min_version": "0.4.0",
                    "real_execution_capable": True
                }
            },
            "P2": {  # 辅助工具，推荐安装，70%真实执行
                "wafw00f": {
                    "name": "WAFW00F",
                    "description": "WAF检测工具",
                    "category": "web_scan",
                    "check_command": ["wafw00f", "--version"],
                    "test_args": ["--version"],
                    "min_version": "2.1.0",
                    "real_execution_capable": True
                },
                "subfinder": {
                    "name": "Subfinder",
                    "description": "子域名枚举工具",
                    "category": "reconnaissance",
                    "check_command": ["subfinder", "--version"],
                    "test_args": ["--version"],
                    "min_version": "2.6.0",
                    "real_execution_capable": True
                },
                "amass": {
                    "name": "Amass",
                    "description": "深度子域名枚举工具",
                    "category": "reconnaissance",
                    "check_command": ["amass", "--version"],
                    "test_args": ["--version"],
                    "min_version": "4.0.0",
                    "real_execution_capable": True
                },
                "feroxbuster": {
                    "name": "Feroxbuster",
                    "description": "快速目录爆破工具",
                    "category": "web_scan",
                    "check_command": ["feroxbuster", "--version"],
                    "test_args": ["--version"],
                    "min_version": "2.9.0",
                    "real_execution_capable": True
                }
            }
        }
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """加载历史数据"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载历史数据失败: {str(e)}")
        
        # 创建报告目录
        reports_dir = os.path.dirname(self.history_file)
        os.makedirs(reports_dir, exist_ok=True)
        
        return []
    
    def _save_history(self):
        """保存历史数据"""
        try:
            reports_dir = os.path.dirname(self.history_file)
            os.makedirs(reports_dir, exist_ok=True)
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
            print(f"[成功] 历史数据已保存到: {self.history_file}")
        except Exception as e:
            print(f"[失败] 保存历史数据失败: {str(e)}")
    
    def _check_tool_installed(self, tool_id: str, check_command: List[str]) -> Tuple[bool, Optional[str]]:
        """检查工具是否已安装"""
        try:
            for cmd in check_command:
                path = shutil.which(cmd)
                if path:
                    return True, path
            
            # 尝试运行命令
            result = subprocess.run(
                check_command,
                capture_output=True,
                text=True,
                timeout=5,
                encoding='utf-8',
                errors='ignore'
            )
            # 返回码为0或1通常表示命令可用
            if result.returncode == 0 or result.returncode == 1:
                # 找到命令路径
                for cmd in check_command:
                    path = shutil.which(cmd)
                    if path:
                        return True, path
            
            return False, None
        except Exception:
            return False, None
    
    def _get_tool_version(self, tool_id: str, check_command: List[str]) -> Optional[str]:
        """获取工具版本"""
        try:
            result = subprocess.run(
                check_command,
                capture_output=True,
                text=True,
                timeout=5,
                encoding='utf-8',
                errors='ignore'
            )
            
            output = result.stdout or result.stderr or ""
            
            # 提取版本号
            version_patterns = [
                r'(\d+\.\d+\.\d+)',      # 1.2.3
                r'(\d+\.\d+)',          # 1.2
                r'v(\d+\.\d+\.\d+)',    # v1.2.3
                r'version\s+(\d+\.\d+\.\d+)',  # version 1.2.3
                r'Version:\s+(\d+\.\d+\.\d+)' # Version: 1.2.3
            ]
            
            for pattern in version_patterns:
                import re
                match = re.search(pattern, output)
                if match:
                    return match.group(1)
            
            return output[:50].strip() if output.strip() else None
        except Exception:
            return None
    
    def _test_tool_health(self, tool_id: str, tool_path: str, test_args: List[str]) -> Tuple[str, Optional[str]]:
        """测试工具健康状态"""
        try:
            cmd = [tool_path]
            cmd.extend(test_args)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0 or result.returncode == 1:
                return "healthy", result.stdout[:200] if result.stdout else result.stderr[:200]
            else:
                return "error", f"执行失败，返回码: {result.returncode}"
                
        except subprocess.TimeoutExpired:
            return "warning", "执行超时"
        except Exception as e:
            return "error", f"执行异常: {str(e)}"
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """比较版本号"""
        def parse_version(version_str: str) -> List[int]:
            parts = version_str.replace('v', '').split('.')
            result = []
            for part in parts:
                try:
                    result.append(int(part))
                except ValueError:
                    result.append(0)
            return result
        
        v1_parts = parse_version(version1)
        v2_parts = parse_version(version2)
        
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        for i in range(max_len):
            if v1_parts[i] > v2_parts[i]:
                return 1
            elif v1_parts[i] < v2_parts[i]:
                return -1
        
        return 0
    
    def _generate_installation_guide(self, tool_id: str, system: str) -> str:
        """生成安装指导"""
        installation_guides = {
            "windows": {
                "nmap": "choco install nmap -y 或 从 https://nmap.org/download.html 下载",
                "whatweb": "choco install ruby -y 然后 gem install whatweb",
                "httpx": "下载 https://github.com/projectdiscovery/httpx/releases",
                "nuclei": "下载 https://github.com/projectdiscovery/nuclei/releases",
                "sqlmap": "pip install sqlmap",
                "nikto": "git clone https://github.com/sullo/nikto",
                "masscan": "下载 https://github.com/robertdavidgraham/masscan/releases",
                "dirsearch": "git clone https://github.com/maurosoria/dirsearch",
                "wafw00f": "pip install wafw00f",
                "subfinder": "下载 https://github.com/projectdiscovery/subfinder/releases",
                "amass": "下载 https://github.com/owasp-amass/amass/releases",
                "feroxbuster": "下载 https://github.com/epi052/feroxbuster/releases"
            },
            "linux": {
                "nmap": "sudo apt install nmap 或 sudo yum install nmap",
                "whatweb": "sudo apt install whatweb 或 gem install whatweb",
                "httpx": "go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest",
                "nuclei": "go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest",
                "sqlmap": "git clone https://github.com/sqlmapproject/sqlmap.git",
                "nikto": "sudo apt install nikto 或 git clone https://github.com/sullo/nikto",
                "masscan": "git clone https://github.com/robertdavidgraham/masscan && cd masscan && make",
                "dirsearch": "git clone https://github.com/maurosoria/dirsearch",
                "wafw00f": "pip3 install wafw00f",
                "subfinder": "go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
                "amass": "go install -v github.com/owasp-amass/amass/v4@master",
                "feroxbuster": "cargo install feroxbuster"
            },
            "darwin": {
                "nmap": "brew install nmap",
                "whatweb": "brew install whatweb",
                "httpx": "brew install httpx",
                "nuclei": "brew install nuclei",
                "sqlmap": "brew install sqlmap",
                "nikto": "brew install nikto",
                "masscan": "brew install masscan",
                "dirsearch": "brew install dirsearch",
                "wafw00f": "pip3 install wafw00f",
                "subfinder": "brew install subfinder",
                "amass": "brew install amass",
                "feroxbuster": "brew install feroxbuster"
            }
        }
        
        system_key = "windows" if system == "windows" else "darwin" if system == "darwin" else "linux"
        
        if system_key in installation_guides and tool_id in installation_guides[system_key]:
            return installation_guides[system_key][tool_id]
        
        return f"请搜索 '{tool_id} {system_key} installation'"
    
    def check_tool(self, tool_id: str, priority: str, config: Dict[str, Any]) -> EnhancedToolStatus:
        """检查单个工具的完整状态"""
        name = config["name"]
        description = config["description"]
        category = config["category"]
        check_command = config["check_command"]
        test_args = config["test_args"]
        min_version = config.get("min_version")
        real_execution_capable = config["real_execution_capable"]
        
        # 检查是否安装
        installed, executable_path = self._check_tool_installed(tool_id, check_command)
        
        version = None
        health_status = "unknown"
        test_output = None
        installation_method = None
        
        if installed and executable_path:
            # 获取版本
            version = self._get_tool_version(tool_id, check_command)
            
            # 测试健康状态
            health_status, test_output = self._test_tool_health(tool_id, executable_path, test_args)
            
            # 检查版本要求
            if version and min_version:
                try:
                    if self._compare_versions(version, min_version) < 0:
                        health_status = "warning"
                        if test_output:
                            test_output = f"版本过低: {version} < {min_version}. {test_output}"
                        else:
                            test_output = f"版本过低: {version} < {min_version}"
                except Exception:
                    pass
            
            # 确定安装方法
            installation_method = "system_path"
        else:
            # 生成安装指导
            installation_method = "not_installed"
            health_status = "error"
        
        # 生成安装指导
        installation_guide = self._generate_installation_guide(tool_id, self.system)
        
        return EnhancedToolStatus(
            tool_id=tool_id,
            name=name,
            description=description,
            category=category,
            priority=priority,
            installed=installed,
            executable_path=executable_path,
            version=version,
            health_status=health_status,
            real_execution_capable=real_execution_capable,
            test_output=test_output,
            last_check=time.time(),
            installation_method=installation_method,
            installation_guide=installation_guide
        )
    
    def check_all_tools(self) -> Dict[str, Any]:
        """检查所有工具"""
        print("=" * 80)
        print("增强的真实执行监控系统")
        print("=" * 80)
        print(f"系统: {platform.system()} {platform.release()}")
        print(f"时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        all_tools = []
        stats_by_priority = {}
        
        for priority in ["P0", "P1", "P2"]:
            if priority not in self.tool_configs:
                continue
            
            print(f"\n检查优先级 {priority} 工具:")
            print("-" * 40)
            
            tools = self.tool_configs[priority]
            priority_tools = []
            
            for tool_id, config in tools.items():
                status = self.check_tool(tool_id, priority, config)
                priority_tools.append(status.to_dict())
                
                status_symbol = "[成功]" if status.installed else "[失败]"
                health_symbol = "[低危]" if status.health_status == "healthy" else "[中危]" if status.health_status == "warning" else "[高危]"
                
                print(f"  {status_symbol}{health_symbol} {tool_id:15} - {status.name}")
                if not status.installed:
                    print(f"     安装指导: {status.installation_guide}")
            
            stats_by_priority[priority] = {
                "total": len(priority_tools),
                "installed": sum(1 for t in priority_tools if t["installed"]),
                "healthy": sum(1 for t in priority_tools if t["installed"] and t["health_status"] == "healthy"),
                "real_execution_capable": sum(1 for t in priority_tools if t["real_execution_capable"])
            }
            
            all_tools.extend(priority_tools)
        
        # 计算总体统计
        total_tools = len(all_tools)
        installed_tools = sum(1 for t in all_tools if t["installed"])
        healthy_tools = sum(1 for t in all_tools if t["installed"] and t["health_status"] == "healthy")
        real_execution_tools = sum(1 for t in all_tools if t["installed"] and t["health_status"] == "healthy" and t["real_execution_capable"])
        
        installation_rate = installed_tools / total_tools * 100 if total_tools > 0 else 0
        health_rate = healthy_tools / installed_tools * 100 if installed_tools > 0 else 0
        real_execution_rate = real_execution_tools / total_tools * 100 if total_tools > 0 else 0
        
        # P0核心工具统计
        p0_stats = stats_by_priority.get("P0", {"total": 0, "installed": 0})
        p0_installation_rate = p0_stats["installed"] / p0_stats["total"] * 100 if p0_stats["total"] > 0 else 0
        
        # 创建统计记录
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        stats = EnhancedExecutionStats(
            timestamp=timestamp,
            total_tools=total_tools,
            installed_tools=installed_tools,
            installation_rate=installation_rate,
            healthy_tools=healthy_tools,
            health_rate=health_rate,
            real_execution_tools=real_execution_tools,
            real_execution_rate=real_execution_rate,
            p0_tools_installed=p0_stats["installed"],
            p0_tools_total=p0_stats["total"],
            p0_installation_rate=p0_installation_rate,
            details={
                "tools": all_tools,
                "stats_by_priority": stats_by_priority,
                "system_info": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "python_version": platform.python_version()
                }
            }
        )
        
        # 添加到历史记录
        self.history.append(asdict(stats))
        self._save_history()
        
        return asdict(stats)
    
    def generate_comprehensive_report(self, stats: Dict[str, Any]) -> str:
        """生成综合报告"""
        report_lines = []
        report_lines.append("=" * 100)
        report_lines.append("ClawAI 增强的真实执行监控报告")
        report_lines.append("=" * 100)
        report_lines.append(f"报告时间: {stats['timestamp']}")
        report_lines.append(f"系统平台: {stats['details']['system_info']['system']} {stats['details']['system_info']['release']}")
        report_lines.append("")
        
        # 总体统计
        report_lines.append("[总体统计]")
        report_lines.append(f"  工具总数: {stats['total_tools']}")
        report_lines.append(f"  已安装工具: {stats['installed_tools']} ({stats['installation_rate']:.1f}%)")
        report_lines.append(f"  健康工具: {stats['healthy_tools']} ({stats['health_rate']:.1f}% 已安装工具)")
        report_lines.append(f"  真实执行工具: {stats['real_execution_tools']} ({stats['real_execution_rate']:.1f}%)")
        report_lines.append("")
        
        # 按优先级统计
        report_lines.append("[按优先级统计]")
        stats_by_priority = stats['details']['stats_by_priority']
        
        for priority in ["P0", "P1", "P2"]:
            if priority in stats_by_priority:
                priority_stats = stats_by_priority[priority]
                total = priority_stats["total"]
                installed = priority_stats["installed"]
                healthy = priority_stats["healthy"]
                
                install_rate = installed / total * 100 if total > 0 else 0
                health_rate = healthy / installed * 100 if installed > 0 else 0
                
                install_bar = self._create_progress_bar(install_rate)
                health_bar = self._create_progress_bar(health_rate)
                
                report_lines.append(f"  {priority}级工具 ({total}个):")
                report_lines.append(f"    安装率: {install_rate:5.1f}% {install_bar}")
                report_lines.append(f"    健康率: {health_rate:5.1f}% {health_bar}")
        report_lines.append("")
        
        # P0核心工具状态
        report_lines.append("[P0核心工具状态]")
        p0_tools = [t for t in stats['details']['tools'] if t['priority'] == 'P0']
        
        for tool in p0_tools:
            status_symbol = "[成功]" if tool["installed"] else "[失败]"
            health_symbol = "[低危]" if tool["health_status"] == "healthy" else "[中危]" if tool["health_status"] == "warning" else "[高危]"
            version_info = f" ({tool['version']})" if tool["version"] else ""
            
            report_lines.append(f"  {status_symbol}{health_symbol} {tool['tool_id']:15} - {tool['name']}{version_info}")
            
            if not tool["installed"]:
                guide_lines = tool["installation_guide"].split('\n')
                for line in guide_lines[:1]:
                    report_lines.append(f"      安装: {line}")
        report_lines.append("")
        
        # 真实执行能力分析
        report_lines.append("[真实执行能力分析]")
        real_execution_rate = stats["real_execution_rate"]
        
        if real_execution_rate >= 80:
            report_lines.append(f"  [优秀] 优秀! 真实执行比例: {real_execution_rate:.1f}%")
            report_lines.append("     已达到高级安全测试要求")
        elif real_execution_rate >= 60:
            report_lines.append(f"  [良好] 良好! 真实执行比例: {real_execution_rate:.1f}%")
            report_lines.append("     基本满足日常安全测试需求")
        elif real_execution_rate >= 40:
            report_lines.append(f"  [警告] 一般! 真实执行比例: {real_execution_rate:.1f}%")
            report_lines.append("     建议继续安装核心工具")
        else:
            report_lines.append(f"  [严重] 不足! 真实执行比例: {real_execution_rate:.1f}%")
            report_lines.append("     严重影响真实测试能力")
        report_lines.append("")
        
        # 建议
        report_lines.append("[改进建议]")
        
        if stats["p0_installation_rate"] < 100:
            missing_p0 = stats["p0_tools_total"] - stats["p0_tools_installed"]
            report_lines.append(f"  1. 优先安装 {missing_p0} 个缺失的P0核心工具")
            report_lines.append("     使用 scripts/auto_install_tools.py 自动安装")
        
        if stats["health_rate"] < 90:
            report_lines.append(f"  2. 修复 {int(stats['installed_tools'] * (100 - stats['health_rate']) / 100)} 个不健康的工具")
            report_lines.append("     检查版本要求，更新到推荐版本")
        
        if stats["real_execution_rate"] < 70:
            needed_tools = int((70 - stats["real_execution_rate"]) / 100 * stats["total_tools"] / 0.7)
            report_lines.append(f"  3. 需要安装/修复 {needed_tools} 个工具达到70%真实执行目标")
        
        report_lines.append("  4. 定期运行监控: python scripts/enhanced_real_execution_monitor.py")
        report_lines.append("")
        
        # 下一步行动
        report_lines.append("[下一步行动]")
        report_lines.append("  1. 自动安装工具: python scripts/auto_install_tools.py")
        report_lines.append("  2. API性能测试: python scripts/analyze_api_performance.py")
        report_lines.append("  3. 启动系统测试: python backend/api_server.py")
        report_lines.append("  4. 监控改进: python utils/performance/monitor_real_execution.py")
        
        report_lines.append("=" * 100)
        
        return "\n".join(report_lines)
    
    def _create_progress_bar(self, percentage: float, width: int = 20) -> str:
        """创建进度条"""
        filled = int(width * percentage / 100)
        bar = "#" * filled + "." * (width - filled)
        return f"[{bar}]"
    
    def generate_visualization(self, stats: Dict[str, Any], output_file: str = "reports/enhanced_real_execution_trend.png"):
        """生成可视化图表"""
        if len(self.history) < 2:
            print("历史数据不足，无法创建可视化图表")
            return
        
        if not MATPLOTLIB_AVAILABLE:
            print("未安装matplotlib，无法生成可视化图表")
            return
        
        dates = [record['timestamp'][:10] for record in self.history]
        installation_rates = [record['installation_rate'] for record in self.history]
        health_rates = [record['health_rate'] for record in self.history]
        real_execution_rates = [record['real_execution_rate'] for record in self.history]
        p0_rates = [record['p0_installation_rate'] for record in self.history]
        
        plt.figure(figsize=(14, 10))
        
        # 子图1: 总体趋势
        plt.subplot(2, 2, 1)
        plt.plot(dates, installation_rates, 'b-o', label='安装率', linewidth=2, markersize=6)
        plt.plot(dates, health_rates, 'g-^', label='健康率', linewidth=2, markersize=6)
        plt.plot(dates, real_execution_rates, 'r-s', label='真实执行率', linewidth=2, markersize=6)
        plt.axhline(y=70, color='orange', linestyle='--', alpha=0.5, label='目标线 (70%)')
        plt.axhline(y=80, color='green', linestyle='--', alpha=0.5, label='优秀线 (80%)')
        plt.xlabel('日期')
        plt.ylabel('比例 (%)')
        plt.title('总体工具状态趋势')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        
        # 子图2: P0核心工具趋势
        plt.subplot(2, 2, 2)
        plt.plot(dates, p0_rates, 'purple-o', label='P0工具安装率', linewidth=2, markersize=6)
        plt.axhline(y=100, color='red', linestyle='--', alpha=0.5, label='目标 (100%)')
        plt.fill_between(dates, 0, p0_rates, alpha=0.3, color='purple')
        plt.xlabel('日期')
        plt.ylabel('安装率 (%)')
        plt.title('P0核心工具安装趋势')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        
        # 子图3: 当前状态饼图
        plt.subplot(2, 2, 3)
        labels = ['已安装健康', '已安装不健康', '未安装']
        sizes = [
            stats['healthy_tools'],
            stats['installed_tools'] - stats['healthy_tools'],
            stats['total_tools'] - stats['installed_tools']
        ]
        colors = ['#4CAF50', '#FFC107', '#F44336']
        explode = (0.1, 0, 0)  # 突出显示健康工具
        plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=90)
        plt.axis('equal')
        plt.title(f'工具状态分布 (总计: {stats["total_tools"]})')
        
        # 子图4: 真实执行能力
        plt.subplot(2, 2, 4)
        categories = ['P0工具', 'P1工具', 'P2工具']
        stats_by_priority = stats['details']['stats_by_priority']
        
        real_execution_by_priority = []
        for priority in categories:
            if priority in stats_by_priority:
                stats_priority = stats_by_priority[priority]
                total = stats_priority["total"]
                real = stats_priority["real_execution_capable"]
                rate = real / total * 100 if total > 0 else 0
                real_execution_by_priority.append(rate)
            else:
                real_execution_by_priority.append(0)
        
        bars = plt.bar(categories, real_execution_by_priority, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        plt.xlabel('工具优先级')
        plt.ylabel('真实执行能力 (%)')
        plt.title('各优先级真实执行能力')
        plt.ylim(0, 100)
        
        # 在柱子上添加数值
        for bar, value in zip(bars, real_execution_by_priority):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{value:.1f}%', 
                    ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"[成功] 可视化图表已保存到: {output_file}")
    
    def save_detailed_report(self, stats: Dict[str, Any], filename: str = "reports/enhanced_real_execution_detailed.json"):
        """保存详细报告"""
        try:
            reports_dir = os.path.dirname(filename)
            os.makedirs(reports_dir, exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            print(f"[成功] 详细报告已保存到: {filename}")
        except Exception as e:
            print(f"[失败] 保存详细报告失败: {str(e)}")

def main():
    """主函数"""
    print("[监控] ClawAI 增强的真实执行监控系统")
    print("正在启动监控...")
    
    try:
        monitor = EnhancedRealExecutionMonitor()
        
        # 运行检查
        print("\n运行工具状态检查...")
        stats = monitor.check_all_tools()
        
        # 生成综合报告
        print("\n生成综合报告...")
        report = monitor.generate_comprehensive_report(stats)
        print(report)
        
        # 保存详细报告
        detailed_report_file = "reports/enhanced_real_execution_detailed.json"
        monitor.save_detailed_report(stats, detailed_report_file)
        
        # 保存文本报告
        text_report_file = "reports/enhanced_real_execution_report.txt"
        with open(text_report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"[成功] 文本报告已保存到: {text_report_file}")
        
        # 生成可视化图表（如果有足够数据）
        if len(monitor.history) >= 2:
            monitor.generate_visualization(stats)
        
        # 显示关键指标
        print(f"\n[目标] 关键指标:")
        print(f"  P0核心工具安装率: {stats['p0_installation_rate']:.1f}% ({stats['p0_tools_installed']}/{stats['p0_tools_total']})")
        print(f"  总体工具安装率: {stats['installation_rate']:.1f}% ({stats['installed_tools']}/{stats['total_tools']})")
        print(f"  工具健康率: {stats['health_rate']:.1f}% ({stats['healthy_tools']}/{stats['installed_tools']})")
        print(f"  真实执行比例: {stats['real_execution_rate']:.1f}% ({stats['real_execution_tools']}/{stats['total_tools']})")
        
        # 检查目标达成
        if stats['p0_installation_rate'] >= 100:
            print(f"\n[庆祝] P0核心工具已全部安装!")
        else:
            missing = stats['p0_tools_total'] - stats['p0_tools_installed']
            print(f"\n[警告]  缺少 {missing} 个P0核心工具，建议优先安装")
        
        if stats['real_execution_rate'] >= 70:
            print(f"[庆祝] 已达到70%真实执行目标!")
        elif stats['real_execution_rate'] >= 50:
            needed = 70 - stats['real_execution_rate']
            print(f"[良好] 接近目标，还需提升 {needed:.1f}%")
        else:
            needed = 70 - stats['real_execution_rate']
            print(f"[警报] 真实执行能力不足，需要提升 {needed:.1f}%")
        
        print(f"\n[列表] 报告文件:")
        print(f"  详细报告: {detailed_report_file}")
        print(f"  文本报告: {text_report_file}")
        print(f"  历史数据: {monitor.history_file}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n[中断]  监控被用户中断")
        return 1
    except Exception as e:
        print(f"\n[失败] 监控失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())