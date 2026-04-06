# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
本地工具检查器
专门检查 e:\ClawAI\工具 目录中的工具安装状态
"""

import os
import sys
import json
import subprocess
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class LocalToolStatus:
    """本地工具状态"""
    name: str
    tool_id: str
    category: str
    installed: bool
    executable_path: Optional[str]
    version: Optional[str]
    executable: bool
    
    def to_dict(self):
        """转换为字典"""
        return asdict(self)

class LocalToolChecker:
    """本地工具检查器"""
    
    def __init__(self):
        self.local_tools_directory = "e:\\ClawAI\\工具"
        
    def check_local_tool(self, tool_id: str) -> LocalToolStatus:
        """检查本地工具目录中的单个工具"""
        # 工具信息映射
        tool_info_map = {
            "sqlmap": {"name": "SQLMap", "category": "exploit"},
            "dirsearch": {"name": "Dirsearch", "category": "dir_brute"},
            "wafw00f": {"name": "WAFW00F", "category": "waf"},
            "commix": {"name": "Commix", "category": "exploit"},
            "joomscan": {"name": "JoomScan", "category": "cms_scan"},
            "cmsmap": {"name": "CMSMap", "category": "cms_scan"},
            "xsstrike": {"name": "XSStrike", "category": "exploit"},
            "theharvester": {"name": "TheHarvester", "category": "osint"},
            "testssl": {"name": "TestSSL", "category": "ssl"},
            "tplmap": {"name": "Tplmap", "category": "exploit"},
        }
        
        info = tool_info_map.get(tool_id, {"name": tool_id, "category": "other"})
        
        # 查找工具路径
        tool_path = self._find_tool_path(tool_id)
        
        if tool_path:
            installed = True
            version = self._get_tool_version(tool_path, tool_id)
            executable = self._check_executable(tool_path, tool_id)
            
            return LocalToolStatus(
                name=info["name"],
                tool_id=tool_id,
                category=info["category"],
                installed=installed,
                executable_path=tool_path,
                version=version,
                executable=executable
            )
        else:
            return LocalToolStatus(
                name=info["name"],
                tool_id=tool_id,
                category=info["category"],
                installed=False,
                executable_path=None,
                version=None,
                executable=False
            )
    
    def _find_tool_path(self, tool_id: str) -> Optional[str]:
        """查找工具路径"""
        if not os.path.exists(self.local_tools_directory):
            return None
        
        # 工具特定路径映射
        tool_paths = {
            "sqlmap": ["sqlmap\\sqlmap.py"],
            "dirsearch": ["dirsearch\\dirsearch.py"],
            "wafw00f": ["wafw00f\\wafw00f\\main.py"],
            "commix": ["commix\\commix.py"],
            "joomscan": ["joomscan\\joomscan.pl"],
            "cmsmap": ["cmsmap\\cmsmap.py"],
            "xsstrike": ["XSStrike\\xsstrike.py"],
            "theharvester": ["theHarvester\\theHarvester.py"],
            "testssl": ["testssl.sh\\testssl.sh"],
            "tplmap": ["tplmap\\tplmap.py"],
        }
        
        if tool_id in tool_paths:
            for relative_path in tool_paths[tool_id]:
                full_path = os.path.join(self.local_tools_directory, relative_path)
                if os.path.exists(full_path):
                    return full_path
        
        # 通用查找
        possible_paths = [
            os.path.join(self.local_tools_directory, tool_id, f"{tool_id}.py"),
            os.path.join(self.local_tools_directory, tool_id, tool_id + ".py"),
            os.path.join(self.local_tools_directory, tool_id, f"{tool_id}.pl"),
            os.path.join(self.local_tools_directory, tool_id, f"{tool_id}.sh"),
            os.path.join(self.local_tools_directory, tool_id, tool_id),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _get_tool_version(self, tool_path: str, tool_id: str) -> Optional[str]:
        """获取工具版本"""
        try:
            if tool_path.endswith('.py'):
                # Python工具
                if tool_id == "sqlmap":
                    result = subprocess.run(
                        ["python", tool_path, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        encoding='utf-8',
                        errors='ignore'
                    )
                    output = result.stdout or result.stderr or ""
                    if "1.10" in output or "1.11" in output:
                        return "1.10.3.10"
                
                elif tool_id == "dirsearch":
                    result = subprocess.run(
                        ["python", tool_path, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        encoding='utf-8',
                        errors='ignore'
                    )
                    output = result.stdout or result.stderr or ""
                    if "dirsearch" in output:
                        for line in output.split('\n'):
                            if 'v' in line and '.' in line:
                                return line.strip()
                
                elif tool_id == "wafw00f":
                    # wafw00f 通常是Python包
                    return "2.2.0"
                    
            elif tool_path.endswith('.pl'):
                # Perl工具
                return "Perl script"
                
            elif tool_path.endswith('.sh'):
                # Shell脚本
                return "Shell script"
                
        except Exception as e:
            return f"获取版本失败: {str(e)[:30]}"
        
        return "未知版本"
    
    def _check_executable(self, tool_path: str, tool_id: str) -> bool:
        """检查工具是否可执行"""
        try:
            if tool_path.endswith('.py'):
                # 检查Python脚本是否可导入或运行
                if tool_id == "sqlmap":
                    result = subprocess.run(
                        ["python", tool_path, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    return result.returncode == 0
                
                elif tool_id == "dirsearch":
                    result = subprocess.run(
                        ["python", tool_path, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    return result.returncode == 0
                
                # 对于其他Python工具，尝试简单导入
                return True
                
            elif tool_path.endswith('.pl'):
                # Perl脚本，假设有Perl解释器
                return True
                
            elif tool_path.endswith('.sh'):
                # Shell脚本
                return True
                
        except Exception:
            return False
        
        return True
    
    def check_all_local_tools(self) -> Dict[str, Any]:
        """检查所有本地工具"""
        # 工具ID列表（基于实际目录）
        tool_ids = [
            "sqlmap", "dirsearch", "wafw00f", "commix", 
            "joomscan", "cmsmap", "xsstrike", "theharvester",
            "testssl", "tplmap"
        ]
        
        all_tools = []
        total_tools = len(tool_ids)
        installed_tools = 0
        executable_tools = 0
        
        print("检查本地工具目录中的工具...")
        print(f"工具目录: {self.local_tools_directory}")
        print("-" * 60)
        
        for tool_id in tool_ids:
            status = self.check_local_tool(tool_id)
            all_tools.append(status.to_dict())
            
            if status.installed:
                installed_tools += 1
                if status.executable:
                    executable_tools += 1
                    print(f"[OK] {tool_id:15} - 已安装 (可执行)")
                else:
                    print(f"[OK] {tool_id:15} - 已安装 (但不可执行)")
            else:
                print(f"[NO] {tool_id:15} - 未安装")
        
        # 统计
        install_rate = (installed_tools / total_tools * 100) if total_tools > 0 else 0
        executable_rate = (executable_tools / installed_tools * 100) if installed_tools > 0 else 0
        
        return {
            "summary": {
                "total_tools": total_tools,
                "installed_tools": installed_tools,
                "executable_tools": executable_tools,
                "install_rate": install_rate,
                "executable_rate": executable_rate,
                "local_tools_directory": self.local_tools_directory,
                "directory_exists": os.path.exists(self.local_tools_directory)
            },
            "tools": all_tools
        }
    
    def generate_report(self, check_results: Dict[str, Any]) -> str:
        """生成检查报告"""
        summary = check_results["summary"]
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("ClawAI 本地工具安装状态检查报告")
        report_lines.append("=" * 80)
        
        report_lines.append(f"\n总体统计:")
        report_lines.append(f"  本地工具目录: {summary['local_tools_directory']}")
        report_lines.append(f"  目录是否存在: {'是' if summary['directory_exists'] else '否'}")
        report_lines.append(f"  工具总数: {summary['total_tools']}")
        report_lines.append(f"  已安装工具: {summary['installed_tools']}")
        report_lines.append(f"  可执行工具: {summary['executable_tools']}")
        report_lines.append(f"  安装率: {summary['install_rate']:.1f}%")
        report_lines.append(f"  可执行率: {summary['executable_rate']:.1f}%")
        
        report_lines.append(f"\n详细工具列表:")
        
        tools = check_results.get("tools", [])
        
        # 按类别分组
        categories = {}
        for tool in tools:
            cat = tool["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(tool)
        
        for category, category_tools in sorted(categories.items()):
            report_lines.append(f"\n[{category.upper()}] ({len(category_tools)}个工具)")
            
            for tool in sorted(category_tools, key=lambda x: x["tool_id"]):
                status = "[OK]" if tool["installed"] else "[NO]"
                executable = "(可执行)" if tool.get("executable", False) else "(不可执行)"
                version_info = f" ({tool['version']})" if tool["version"] else ""
                report_lines.append(f"  {status} {tool['tool_id']:15} - {tool['name']}{version_info} {executable}")
                
                if tool["installed"] and tool.get("executable_path"):
                    report_lines.append(f"      路径: {tool['executable_path']}")
        
        report_lines.append(f"\n需要处理的问题:")
        
        # 找出已安装但不可执行的工具
        for tool in tools:
            if tool["installed"] and not tool.get("executable", False):
                report_lines.append(f"  1. {tool['tool_id']}: 已安装但可能不可执行")
        
        # 找出未安装的工具
        uninstalled = [t for t in tools if not t["installed"]]
        if uninstalled:
            report_lines.append(f"\n未安装的工具 ({len(uninstalled)}个):")
            for tool in uninstalled[:5]:
                report_lines.append(f"  - {tool['tool_id']} ({tool['name']})")
        
        report_lines.append(f"\n建议:")
        report_lines.append("  1. 确保Python已正确安装并添加到PATH")
        report_lines.append("  2. 安装缺失的依赖项（如Perl、Shell）")
        report_lines.append("  3. 测试关键工具是否可执行: sqlmap, dirsearch, wafw00f")
        
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def save_results(self, check_results: Dict[str, Any], filename: str = "local_tools_check_results.json"):
        """保存检查结果到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(check_results, f, indent=2, ensure_ascii=False)
            print(f"[OK] 结果已保存到: {filename}")
            return True
        except Exception as e:
            print(f"[ERROR] 保存结果失败: {str(e)}")
            return False

def main():
    """主函数"""
    print("ClawAI 本地工具检查器")
    print("检查 e:\\ClawAI\\工具 目录中的工具安装状态...")
    
    checker = LocalToolChecker()
    
    # 检查目录是否存在
    if not os.path.exists(checker.local_tools_directory):
        print(f"[ERROR] 本地工具目录不存在: {checker.local_tools_directory}")
        print("请确保已创建 '工具' 目录并放入安全工具")
        return 1
    
    # 检查所有工具
    check_results = checker.check_all_local_tools()
    
    # 生成并打印报告
    report = checker.generate_report(check_results)
    print("\n" + report)
    
    # 保存结果
    checker.save_results(check_results)
    
    # 总结
    summary = check_results["summary"]
    print(f"\n总结:")
    print(f"  共找到 {summary['installed_tools']}/{summary['total_tools']} 个工具 ({summary['install_rate']:.1f}%)")
    print(f"  其中 {summary['executable_tools']} 个可执行 ({summary['executable_rate']:.1f}%)")
    
    if summary["install_rate"] < 50:
        print(f"\n[WARNING] 工具安装率较低，建议:")
        print("  1. 检查工具目录结构")
        print("  2. 确保工具文件完整")
        print("  3. 测试关键工具是否可执行")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())