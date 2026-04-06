# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Dirsearch目录和文件爆破工具模块
封装dirsearch功能，提供目录和文件枚举接口
"""

import subprocess
import json
import sys
import re
import os


class DirsearchTool:
    """Dirsearch目录爆破工具类"""
    
    def __init__(self, dirsearch_path: str = "dirsearch"):
        self.dirsearch_path = dirsearch_path
        
    def _run_dirsearch_command(self, target: str, options: dict = None):
        """运行dirsearch命令"""
        try:
            cmd = [
                self.dirsearch_path,
                '-u', target,
                '-e', 'php,asp,aspx,jsp,html,htm,json,txt',  # 扩展名
                '-t', '10',          # 线程数
                '-r',                # 递归扫描
                '--timeout', '5',    # 超时时间
                '--max-retries', '1',# 最大重试
                '--random-agents',   # 随机User-Agent
                '--extensions-without-dot',  # 无点扩展名
                '--simple-report', '/tmp/dirsearch_report.txt'
            ]
            
            if options:
                if options.get('wordlist'):
                    cmd.extend(['-w', options['wordlist']])
                if options.get('recursive_depth'):
                    cmd.extend(['--recursive-depth', str(options['recursive_depth'])])
                if options.get('exclude_status'):
                    cmd.extend(['--exclude-status', options['exclude_status']])
                if options.get('cookie'):
                    cmd.extend(['--cookie', options['cookie']])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                encoding='utf-8',
                errors='ignore'
            )
            
            return result.stdout + result.stderr
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("dirsearch扫描超时")
        except FileNotFoundError:
            raise RuntimeError("未找到dirsearch可执行文件，请确保已安装dirsearch")
        except Exception as e:
            raise RuntimeError(f"执行错误: {str(e)}")
    
    def _parse_output(self, output: str):
        """解析dirsearch输出"""
        result = {
            "found_directories": [],
            "found_files": [],
            "status_codes": {},
            "total_found": 0
        }
        
        # 解析输出行
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            
            # 匹配找到的路径
            if line.startswith('[+]'):
                # 格式: [+] http://example.com/admin (CODE:200|SIZE:1234)
                path_match = re.search(r'\[\+\]\s+(.*?)\s+\(CODE:(\d+)\|SIZE:(\d+)\)', line)
                if path_match:
                    path = path_match.group(1)
                    status = int(path_match.group(2))
                    size = int(path_match.group(3))
                    
                    # 判断是目录还是文件
                    if path.endswith('/'):
                        item_type = "directory"
                        result["found_directories"].append({
                            "path": path,
                            "status": status,
                            "size": size
                        })
                    else:
                        item_type = "file"
                        result["found_files"].append({
                            "path": path,
                            "status": status,
                            "size": size
                        })
                    
                    # 统计状态码
                    if status not in result["status_codes"]:
                        result["status_codes"][status] = 0
                    result["status_codes"][status] += 1
        
        result["total_found"] = len(result["found_directories"]) + len(result["found_files"])
        
        # 按状态码排序
        result["status_codes"] = dict(sorted(result["status_codes"].items()))
        
        return result
    
    def run(self, target: str, options: dict = None):
        """执行dirsearch扫描"""
        if not target or not isinstance(target, str):
            raise ValueError("目标必须是有效的URL字符串")
        
        target = target.strip()
        if not target:
            raise ValueError("目标不能为空")
        
        if not (target.startswith('http://') or target.startswith('https://')):
            target = f"http://{target}"
        
        try:
            output = self._run_dirsearch_command(target, options)
            result = self._parse_output(output)
            
            return {
                "target": target,
                "tool": "dirsearch",
                "result": result,
                "raw_output": output[:2000] if len(output) > 2000 else output
            }
            
        except Exception as e:
            return {
                "target": target,
                "tool": "dirsearch",
                "result": {
                    "found_directories": [],
                    "found_files": [],
                    "status_codes": {},
                    "total_found": 0
                },
                "error": str(e)
            }


def main():
    """命令行入口点"""
    if len(sys.argv) < 2:
        print("用法: python dirsearch.py <target_url>")
        print("示例: python dirsearch.py 'http://example.com'")
        sys.exit(1)
    
    target = sys.argv[1]
    tool = DirsearchTool()
    
    try:
        result = tool.run(target)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"扫描失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
