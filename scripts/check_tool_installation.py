#!/usr/bin/env python3
"""
工具安装状态检查脚本
检查ClawAI项目所需的所有安全工具是否已安装
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.absolute()))
from config import config

class ToolChecker:
    """工具检查器"""

    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.results = {}

    def check_tool(self, tool_name, tool_path_env=None, default_command=None):
        """检查单个工具是否可用"""
        tool_info = {
            "tool_name": tool_name,
            "installed": False,
            "path": None,
            "version": None,
            "check_method": "unknown"
        }

        # 方法1：检查PATH环境变量
        if default_command:
            path_in_system = shutil.which(default_command)
            if path_in_system:
                tool_info["installed"] = True
                tool_info["path"] = path_in_system
                tool_info["check_method"] = "system_path"

                # 尝试获取版本
                try:
                    result = subprocess.run(
                        [default_command, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        encoding='utf-8',
                        errors='ignore'
                    )
                    if result.stdout:
                        tool_info["version"] = result.stdout.strip()[:100]
                    elif result.stderr:
                        tool_info["version"] = result.stderr.strip()[:100]
                except:
                    pass

        # 方法2：检查config.py中配置的路径
        if not tool_info["installed"] and tool_path_env:
            tool_path = getattr(config, tool_path_env, None)
            if tool_path and os.path.exists(tool_path):
                tool_info["installed"] = True
                tool_info["path"] = tool_path
                tool_info["check_method"] = "config_path"

        # 方法3：检查项目内工具目录
        if not tool_info["installed"]:
            external_tools_dir = self.project_root / "external_tools"
            possible_paths = [
                external_tools_dir / f"{tool_name}.py",
                external_tools_dir / f"{tool_name}.exe",
                external_tools_dir / tool_name / f"{tool_name}.py",
            ]

            for path in possible_paths:
                if path.exists():
                    tool_info["installed"] = True
                    tool_info["path"] = str(path)
                    tool_info["check_method"] = "project_tools"
                    break

        return tool_info

    def check_all_tools(self):
        """检查所有核心工具"""
        tools_to_check = [
            # 核心扫描工具
            ("nmap", "NMAP_PATH", "nmap"),
            ("sqlmap", None, "sqlmap"),
            ("nuclei", "NUCLEI_PATH", "nuclei"),
            ("whatweb", "WHATWEB_PATH", "whatweb"),
            ("nikto", None, "nikto"),
            ("dirsearch", None, "dirsearch"),
            ("gobuster", None, "gobuster"),

            # 漏洞利用工具
            ("hydra", None, "hydra"),
            ("john", None, "john"),
            ("hashcat", None, "hashcat"),

            # Web安全工具
            ("wapiti", None, "wapiti"),
            ("skipfish", None, "skipfish"),
            ("wafw00f", None, "wafw00f"),
            ("xsstrike", None, None),  # 可能需要特殊检查

            # 信息收集工具
            ("masscan", None, "masscan"),
            ("sslscan", None, "sslscan"),
            ("testssl", None, "testssl.sh"),
        ]

        for tool_name, tool_path_env, default_command in tools_to_check:
            self.results[tool_name] = self.check_tool(tool_name, tool_path_env, default_command)

        return self.results

    def check_docker(self):
        """检查Docker是否可用"""
        docker_info = {
            "tool_name": "docker",
            "installed": False,
            "path": None,
            "version": None,
            "check_method": "system_path"
        }

        try:
            # 检查docker命令
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                encoding='utf-8',
                errors='ignore'
            )
            if result.returncode == 0:
                docker_info["installed"] = True
                docker_info["version"] = result.stdout.strip()
                docker_info["path"] = shutil.which("docker") or "docker"
        except:
            pass

        self.results["docker"] = docker_info
        return docker_info

    def check_python_dependencies(self):
        """检查Python依赖"""
        deps_info = {
            "tool_name": "python_deps",
            "installed": True,
            "missing_deps": [],
            "check_method": "pip"
        }

        required_deps = [
            "requests",
            "beautifulsoup4",
            "lxml",
            "sqlalchemy",
            "pydantic",
            "fastapi",
            "uvicorn",
            "jinja2",
            "markdown",
            "python-multipart",
        ]

        missing = []
        for dep in required_deps:
            try:
                __import__(dep.replace("-", "_"))
            except ImportError:
                missing.append(dep)

        deps_info["missing_deps"] = missing
        deps_info["installed"] = len(missing) == 0

        self.results["python_deps"] = deps_info
        return deps_info

    def generate_report(self):
        """生成检查报告"""
        print("=" * 70)
        print("ClawAI 工具安装状态检查报告")
        print("=" * 70)

        total_tools = len(self.results)
        installed_tools = sum(1 for r in self.results.values() if r.get("installed", False))

        print(f"\n总体统计: {installed_tools}/{total_tools} 个工具已安装 ({installed_tools/total_tools*100:.1f}%)")

        # 分类显示
        categories = {
            "核心扫描工具": ["nmap", "sqlmap", "nuclei", "whatweb", "nikto"],
            "目录爆破工具": ["dirsearch", "gobuster"],
            "暴力破解工具": ["hydra", "john", "hashcat"],
            "Web安全工具": ["wapiti", "skipfish", "wafw00f", "xsstrike"],
            "网络扫描工具": ["masscan", "sslscan", "testssl"],
            "基础设施": ["docker", "python_deps"],
        }

        for category, tools in categories.items():
            print(f"\n{category}:")
            for tool in tools:
                if tool in self.results:
                    result = self.results[tool]
                    status = "✅" if result.get("installed", False) else "❌"
                    method = result.get("check_method", "unknown")
                    path = result.get("path", "未找到")

                    if path and len(path) > 50:
                        path = path[:47] + "..."
                    elif not path:
                        path = "未找到"

                    print(f"  {status} {tool:15} | {method:15} | {path}")

        # 显示未安装的关键工具
        print(f"\n未安装的关键工具:")
        critical_tools = ["nmap", "sqlmap", "nuclei", "whatweb"]
        missing_critical = [t for t in critical_tools if t in self.results and not self.results[t].get("installed", False)]

        if missing_critical:
            for tool in missing_critical:
                print(f"  ❌ {tool}")
            print(f"\n⚠️  警告: {len(missing_critical)}/{len(critical_tools)} 个核心工具未安装")
            print("  这将严重影响漏洞检测率！")
        else:
            print("  ✅ 所有核心工具已安装")

        # Docker状态
        docker_info = self.results.get("docker", {})
        if docker_info.get("installed", False):
            print(f"\n✅ Docker 已安装: {docker_info.get('version', '未知版本')}")
            print("  提示: 可以使用Docker容器运行Kali工具")
        else:
            print(f"\n❌ Docker 未安装")
            print("  提示: 建议安装Docker以使用容器化工具")

        # Python依赖
        deps_info = self.results.get("python_deps", {})
        if deps_info.get("installed", False):
            print(f"\n✅ Python依赖已满足")
        else:
            missing = deps_info.get("missing_deps", [])
            print(f"\n❌ 缺失Python依赖: {', '.join(missing)}")
            print(f"  运行: pip install {' '.join(missing)}")

        print(f"\n" + "=" * 70)
        print("建议安装顺序:")
        print("1. 安装Docker (用于容器化工具)")
        print("2. 安装nmap、sqlmap、nuclei、whatweb等核心工具")
        print("3. 安装Python缺失依赖")
        print("4. 更新config.py中的工具路径配置")
        print("=" * 70)

        return self.results

def main():
    """主函数"""
    checker = ToolChecker()

    print("检查工具安装状态...")

    # 检查所有工具
    checker.check_all_tools()
    checker.check_docker()
    checker.check_python_dependencies()

    # 生成报告
    results = checker.generate_report()

    # 保存结果到文件
    report_file = checker.project_root / "reports" / "tool_installation_report.json"
    import json
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n详细报告已保存至: {report_file}")

    # 返回检查结果
    critical_missing = ["nmap", "sqlmap", "nuclei", "whatweb"]
    missing_count = sum(1 for t in critical_missing
                       if t in results and not results[t].get("installed", False))

    return missing_count == 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"检查过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)