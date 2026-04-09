# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Feroxbuster目录爆破工具（基于BaseTool的新版本）
封装feroxbuster目录爆破功能，支持真实/模拟执行自动切换
"""

import logging
import subprocess
import json
import re
import sys
import os
import tempfile
import random
from typing import Dict, List, Any, Optional

# 导入工具基类
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.tools.base_tool import (
    BaseTool, ToolExecutionMode, ToolCategory,
    ToolPriority, ToolExecutionResult, register_tool
)

logger = logging.getLogger(__name__)


@register_tool
class FeroxbusterTool(BaseTool):
    """Feroxbuster目录爆破工具类（新版本）"""
    
    def __init__(self):
        super().__init__(
            tool_name="feroxbuster",
            command="feroxbuster",
            description="快速递归目录爆破器（Rust编写）",
            category=ToolCategory.DIR_BRUTE,
            priority=ToolPriority.HIGH,
            requires_installation=True,
            fallback_to_simulated=True
        )
        
        # 常见Web路径
        self.common_paths = [
            "/admin/",
            "/login/",
            "/dashboard/",
            "/api/",
            "/wp-admin/",
            "/phpmyadmin/",
            "/backup/",
            "/config/",
            "/uploads/",
            "/static/",
            "/assets/",
            "/js/",
            "/css/",
            "/images/",
            "/doc/",
            "/test/",
            "/debug/",
            "/console/",
            "/manager/",
            "/admin.php",
            "/login.php",
            "/index.php",
            "/config.php",
            "/.git/",
            "/.env",
            "/robots.txt",
            "/sitemap.xml",
            "/wp-content/",
            "/wp-includes/",
            "/vendor/",
            "/storage/",
            "/public/",
            "/private/",
            "/secret/",
            "/hidden/"
        ]
        
        # 默认字典路径（常见位置）
        self.default_wordlists = [
            "/usr/share/seclists/Discovery/Web-Content/common.txt",
            "/usr/share/wordlists/dirb/common.txt",
            "/usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt"
        ]
    
    def _parse_feroxbuster_output(self, output: str) -> List[Dict[str, Any]]:
        """解析feroxbuster输出，提取发现的目录和文件"""
        findings = []
        
        # 匹配feroxbuster输出格式
        # 格式示例: 200      GET       75l      189w     2176c http://example.com/admin/
        pattern = r'(\d{3})\s+(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH)\s+(\d+)l\s+(\d+)w\s+(\d+)c\s+(.+)'
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 跳过统计行和空行
            if not line or 'Finished scan' in line or 'Requests made' in line or 'Resources found' in line:
                continue
            
            match = re.match(pattern, line)
            if match:
                status_code = int(match.group(1))
                method = match.group(2)
                lines_count = int(match.group(3))
                words_count = int(match.group(4))
                chars_count = int(match.group(5))
                url = match.group(6)
                
                # 从URL中提取路径
                path = url
                if '://' in url:
                    path = url.split('://', 1)[1]
                    if '/' in path:
                        path = '/' + path.split('/', 1)[1]
                
                findings.append({
                    "url": url,
                    "path": path,
                    "status_code": status_code,
                    "method": method,
                    "lines": lines_count,
                    "words": words_count,
                    "chars": chars_count
                })
        
        return findings
    
    def _find_wordlist(self) -> Optional[str]:
        """查找可用的字典文件"""
        for wordlist in self.default_wordlists:
            if os.path.exists(wordlist):
                return wordlist
        
        # 如果没有找到系统字典，尝试创建临时字典
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                # 写入常见的目录路径
                for path in self.common_paths:
                    f.write(f"{path.lstrip('/')}\n")
                temp_wordlist = f.name
            
            self.logger.info(f"创建临时字典: {temp_wordlist}")
            return temp_wordlist
        except Exception:
            return None
    
    def _execute_real(self, target: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """真实执行feroxbuster目录爆破"""
        if options is None:
            options = {}
        
        # 清理目标URL
        clean_target = target
        if not (target.startswith("http://") or target.startswith("https://")):
            clean_target = f"http://{target}"
        
        # 提取选项参数
        wordlist_path = options.get("wordlist", None)
        recursion_depth = options.get("recursion_depth", 2)
        threads = options.get("threads", 10)
        timeout = options.get("timeout", 600)  # 10分钟超时
        
        # 如果没有提供字典，尝试查找
        if not wordlist_path or not os.path.exists(wordlist_path):
            wordlist_path = self._find_wordlist()
        
        if not wordlist_path:
            return {
                "target": target,
                "error": "未找到可用的字典文件",
                "suggestion": "请安装seclists或提供自定义字典",
                "execution_mode": "real"
            }
        
        # 创建临时文件存储输出
        temp_output_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                temp_output_file = f.name
            
            # 构建feroxbuster命令
            cmd = [
                self.command,
                '-u', clean_target,
                '-t', str(threads),
                '-r',  # 递归扫描
                '--recursion-depth', str(recursion_depth),
                '-w', wordlist_path,
                '--no-state',
                '--quiet',
                '--output', temp_output_file
            ]
            
            # 添加额外选项
            if options.get("extensions"):
                extensions = options["extensions"]
                if isinstance(extensions, str):
                    cmd.extend(['-x', extensions])
                elif isinstance(extensions, list):
                    cmd.extend(['-x', ','.join(extensions)])
            
            self.logger.info(f"执行feroxbuster命令: {' '.join(cmd[:8])}...")
            
            # 执行命令
            result = self._run_command(cmd, timeout=timeout)
            
            # 读取输出文件
            output_content = ""
            if os.path.exists(temp_output_file):
                with open(temp_output_file, 'r', encoding='utf-8') as f:
                    output_content = f.read()
            
            # 如果没有从文件读取到内容，使用命令输出
            if not output_content:
                output_content = result.stdout if result.stdout else result.stderr
            
            # 解析结果
            findings = self._parse_feroxbuster_output(output_content)
            
            # 统计信息
            stats = {
                "total_findings": len(findings),
                "status_codes": {},
                "recursion_depth": recursion_depth,
                "wordlist": wordlist_path
            }
            
            for finding in findings:
                status = finding["status_code"]
                if status not in stats["status_codes"]:
                    stats["status_codes"][status] = 0
                stats["status_codes"][status] += 1
            
            return {
                "target": target,
                "clean_target": clean_target,
                "findings": findings,
                "statistics": stats,
                "raw_output": output_content[:2000],
                "execution_mode": "real",
                "command_short": f"feroxbuster -u {clean_target} -w {os.path.basename(wordlist_path)}",
                "return_code": result.returncode,
                "wordlist_used": wordlist_path
            }
            
        except Exception as e:
            error_msg = f"feroxbuster执行错误: {str(e)}"
            if isinstance(e, subprocess.TimeoutExpired):
                error_msg = "feroxbuster扫描超时"
            elif isinstance(e, FileNotFoundError):
                error_msg = "未找到feroxbuster可执行文件"
            
            return {
                "target": target,
                "clean_target": clean_target,
                "findings": [],
                "error": error_msg,
                "execution_mode": "real",
                "raw_output": error_msg
            }
        
        finally:
            # 清理临时文件
            if temp_output_file and os.path.exists(temp_output_file):
                try:
                    os.unlink(temp_output_file)
                except Exception as e:
                    logger.debug(f"Error: {e}")
    
    def _simulate_execution(self, target: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """模拟feroxbuster执行（当工具不可用时）"""
        # 清理目标URL
        clean_target = target
        if not (target.startswith("http://") or target.startswith("https://")):
            clean_target = f"http://{target}"
        
        # 随机选择5-12个路径作为发现结果
        findings_count = random.randint(5, 12)
        selected_paths = random.sample(self.common_paths, min(findings_count, len(self.common_paths)))
        
        # 模拟不同的状态码
        status_code_distribution = {
            200: 0.5,   # 50% 200 OK
            301: 0.1,   # 10% 301 重定向
            302: 0.1,   # 10% 302 重定向
            403: 0.15,  # 15% 403 禁止访问
            404: 0.15   # 15% 404 未找到
        }
        
        findings = []
        for i, path in enumerate(selected_paths):
            # 根据分布选择状态码
            rand_val = random.random()
            cumulative = 0
            selected_code = 200
            
            for code, prob in status_code_distribution.items():
                cumulative += prob
                if rand_val <= cumulative:
                    selected_code = code
                    break
            
            # 生成URL
            url = clean_target.rstrip('/') + path
            
            # 生成随机的内容统计
            lines_count = random.randint(10, 100)
            words_count = random.randint(20, 200)
            chars_count = random.randint(200, 2000)
            
            findings.append({
                "url": url,
                "path": path,
                "status_code": selected_code,
                "method": "GET",
                "lines": lines_count,
                "words": words_count,
                "chars": chars_count,
                "simulated": True
            })
        
        # 统计信息
        stats = {
            "total_findings": len(findings),
            "status_codes": {},
            "recursion_depth": options.get("recursion_depth", 2) if options else 2,
            "wordlist": "simulated",
            "note": "模拟数据，仅供参考"
        }
        
        for finding in findings:
            status = finding["status_code"]
            if status not in stats["status_codes"]:
                stats["status_codes"][status] = 0
            stats["status_codes"][status] += 1
        
        # 生成模拟的输出格式
        output_lines = []
        for finding in findings:
            line = f"{finding['status_code']:3d}      GET       {finding['lines']:3d}l      {finding['words']:3d}w     {finding['chars']:4d}c {finding['url']}"
            output_lines.append(line)
        
        # 添加统计信息
        output_lines.append("")
        output_lines.append(f"-------------------")
        output_lines.append(f"Finished scan in 0:01:{random.randint(30, 90)}")
        output_lines.append(f"Requests made: {len(findings) * 2}")
        output_lines.append(f"Resources found: {len(findings)}")
        
        raw_output = "\n".join(output_lines)
        
        return {
            "target": target,
            "clean_target": clean_target,
            "findings": findings,
            "statistics": stats,
            "raw_output": raw_output,
            "execution_mode": "simulated",
            "simulated": True,
            "note": "这是模拟数据，实际环境中请安装feroxbuster进行真实扫描",
            "installation_guide": """
feroxbuster安装指南:

  Linux (Kali/Ubuntu/Debian):
    sudo apt-get update
    sudo apt-get install feroxbuster
  
  Linux (其他发行版，Rust方式):
    curl -sSf https://sh.rustup.rs | sh
    source ~/.cargo/env
    cargo install feroxbuster
  
  Linux (预编译二进制):
    # 下载最新版本: https://github.com/epi052/feroxbuster/releases
    wget https://github.com/epi052/feroxbuster/releases/latest/download/feroxbuster-x86_64-unknown-linux-gnu.tar.xz
    tar -xf feroxbuster-*.tar.xz
    sudo mv feroxbuster /usr/local/bin/
  
  macOS (Homebrew):
    brew install feroxbuster
  
  Windows:
    1. 下载: https://github.com/epi052/feroxbuster/releases/latest/download/feroxbuster-x86_64-pc-windows-msvc.zip
    2. 解压并将feroxbuster.exe添加到系统PATH
  
  字典安装 (推荐):
    sudo apt-get install seclists  # Kali/Ubuntu
    或
    git clone https://github.com/danielmiessler/SecLists.git /usr/share/seclists

  常用命令:
    feroxbuster -u http://example.com -w /usr/share/seclists/Discovery/Web-Content/common.txt
    feroxbuster -u https://target.com -x php,html,txt -t 20
"""
        }
    
    def run(self, target: str) -> Dict[str, Any]:
        """执行feroxbuster目录爆破（兼容旧接口）"""
        result = self.execute(target)
        return result.output


def main():
    """命令行入口点"""
    if len(sys.argv) < 2:
        print("用法: python new_feroxbuster.py <target_url>")
        print("示例: python new_feroxbuster.py http://example.com")
        print("示例: python new_feroxbuster.py https://target-site.com")
        print("选项:")
        print("  --wordlist <path>       指定字典文件路径")
        print("  --depth <num>           递归深度 (默认: 2)")
        print("  --threads <num>         线程数 (默认: 10)")
        print("  --extensions <exts>     文件扩展名 (逗号分隔)")
        print("  --json                  输出完整JSON")
        sys.exit(1)
    
    target = sys.argv[1]
    
    # 解析选项
    options = {}
    
    if "--wordlist" in sys.argv:
        try:
            wordlist_index = sys.argv.index("--wordlist") + 1
            if wordlist_index < len(sys.argv):
                wordlist_path = sys.argv[wordlist_index]
                if os.path.exists(wordlist_path):
                    options["wordlist"] = wordlist_path
                else:
                    print(f"警告: 字典文件不存在: {wordlist_path}")
        except (ValueError, IndexError):
            pass
    
    if "--depth" in sys.argv:
        try:
            depth_index = sys.argv.index("--depth") + 1
            if depth_index < len(sys.argv):
                depth_val = int(sys.argv[depth_index])
                if 1 <= depth_val <= 10:
                    options["recursion_depth"] = depth_val
        except (ValueError, IndexError):
            pass
    
    if "--threads" in sys.argv:
        try:
            threads_index = sys.argv.index("--threads") + 1
            if threads_index < len(sys.argv):
                threads_val = int(sys.argv[threads_index])
                if 1 <= threads_val <= 100:
                    options["threads"] = threads_val
        except (ValueError, IndexError):
            pass
    
    if "--extensions" in sys.argv:
        try:
            ext_index = sys.argv.index("--extensions") + 1
            if ext_index < len(sys.argv):
                options["extensions"] = sys.argv[ext_index]
        except (ValueError, IndexError):
            pass
    
    tool = FeroxbusterTool()
    
    try:
        # 显示工具状态
        status = tool.get_status()
        print(f"工具状态: {'✅ 可用' if status['available'] else '❌ 不可用'}")
        if status['version']:
            print(f"版本信息: {status['version']}")
        
        if not status['available']:
            print("\n⚠️  工具不可用，将使用模拟模式")
            print("如需真实扫描，请安装feroxbuster")
        
        # 执行扫描
        result = tool.execute(target, options)
        
        # 输出结果摘要
        print(f"\n扫描目标: {result.output['target']}")
        print(f"执行模式: {result.output['execution_mode']}")
        
        if result.output.get('simulated'):
            print("⚠️  注意: 这是模拟数据")
        
        if result.output.get('error'):
            print(f"错误: {result.output['error']}")
        
        scan_stats = result.output.get('statistics', {})
        
        # 显示发现统计
        total_findings = scan_stats.get('total_findings', 0)
        print(f"\n发现结果: {total_findings} 个路径")
        
        if total_findings > 0:
            # 按状态码分类
            status_codes = scan_stats.get('status_codes', {})
            if status_codes:
                print(f"\n状态码分布:")
                for status_code, count in sorted(status_codes.items()):
                    status_desc = {
                        200: "正常",
                        301: "永久重定向",
                        302: "临时重定向",
                        403: "禁止访问",
                        404: "未找到"
                    }.get(status_code, "其他")
                    print(f"  {status_code}: {count:3d} ({status_desc})")
            
            # 显示发现的前10个路径
            findings = result.output.get('findings', [])
            if findings:
                print(f"\n发现的路径（前{min(10, len(findings))}个）:")
                print("-" * 90)
                print(f"{'状态码':<8} {'方法':<6} {'路径':<50}")
                print("-" * 90)
                
                for i, finding in enumerate(findings[:10], 1):
                    status_code = finding.get('status_code', 0)
                    method = finding.get('method', 'GET')
                    path = finding.get('path', '')
                    
                    # 状态码颜色
                    status_color = ""
                    if status_code == 200:
                        status_color = "🟢"
                    elif status_code in [301, 302]:
                        status_color = "🟡"
                    elif status_code == 403:
                        status_color = "🔴"
                    elif status_code == 404:
                        status_color = "⚫"
                    else:
                        status_color = "⚪"
                    
                    simulated = " (模拟)" if finding.get('simulated') else ""
                    print(f"{status_color} {status_code:<6} {method:<6} {path[:48]:<50}{simulated}")
        
        # 显示扫描设置
        if scan_stats:
            print(f"\n扫描设置:")
            print(f"  递归深度: {scan_stats.get('recursion_depth', 2)}")
            if result.output.get('wordlist_used'):
                print(f"  字典文件: {result.output.get('wordlist_used')}")
        
        # 显示安装指南（如果使用模拟模式）
        if result.output.get('simulated') and result.output.get('installation_guide'):
            print(f"\n安装指南: 请查看工具的installation_guide字段")
        
        # 可选的JSON输出
        if '--json' in sys.argv:
            print("\n完整JSON输出:")
            print(json.dumps(result.output, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"扫描失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()