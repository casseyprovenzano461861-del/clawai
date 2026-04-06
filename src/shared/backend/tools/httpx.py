# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
HTTPX存活探测工具模块
用于探测HTTP/HTTPS服务的存活状态
"""

import subprocess
import json
import sys
import re


class HTTPXTool:
    def __init__(self, httpx_path=r"C:\Tools\httpx\httpx.exe"):
        self.httpx_path = httpx_path
    
    def _build_targets(self, target):
        target = target.strip()
        
        if target.startswith('http://') or target.startswith('https://'):
            return [target]
        
        targets = []
        
        if ':' in target and not target.startswith('['):
            parts = target.split(':')
            if len(parts) == 2 and parts[1].isdigit():
                host = parts[0]
                port = parts[1]
                targets.extend([f"http://{host}:{port}", f"https://{host}:{port}"])
                return targets
        
        targets.extend([f"http://{target}", f"https://{target}"])
        return targets
    
    def _run_httpx_command(self, targets):
        try:
            cmd = [self.httpx_path, '-status-code', '-title', '-timeout', '10', '-json', '-silent']
            cmd.extend(targets)
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, encoding='utf-8', errors='ignore')
            
            if result.returncode != 0:
                if "command not found" in result.stderr.lower():
                    raise RuntimeError("未找到httpx可执行文件")
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("httpx探测超时")
        except FileNotFoundError:
            raise RuntimeError("未找到httpx可执行文件")
        except Exception as e:
            raise RuntimeError(f"执行错误: {str(e)}")
    
    def _parse_httpx_output(self, output):
        alive = []
        
        if not output.strip():
            return alive
        
        try:
            lines = output.strip().split('\n')
            for line in lines:
                if not line.strip():
                    continue
                    
                try:
                    data = json.loads(line)
                    
                    service = {
                        "url": data.get("url", ""),
                        "status": data.get("status-code", 0),
                        "title": data.get("title", "")
                    }
                    
                    if service["title"]:
                        service["title"] = re.sub(r'<[^>]+>', '', service["title"]).strip()
                    
                    alive.append(service)
                    
                except json.JSONDecodeError:
                    continue
                    
        except Exception:
            return alive
        
        return alive
    
    def run(self, target):
        if not target or not isinstance(target, str):
            return {
                "tool": "httpx",
                "target": "",
                "alive": [],
                "error": "目标必须是有效的字符串"
            }
        
        target = target.strip()
        if not target:
            return {
                "tool": "httpx",
                "target": "",
                "alive": [],
                "error": "目标不能为空"
            }
        
        try:
            targets = self._build_targets(target)
            output = self._run_httpx_command(targets)
            alive = self._parse_httpx_output(output)
            
            return {
                "tool": "httpx",
                "target": target,
                "alive": alive
            }
            
        except Exception as e:
            return {
                "tool": "httpx",
                "target": target,
                "alive": [],
                "error": str(e)
            }


def main():
    if len(sys.argv) != 2:
        print("用法: python  <target> - httpx.py:130")
        sys.exit(1)
    
    target = sys.argv[1]
    tool = HTTPXTool()
    
    try:
        result = tool.run(target)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"存活探测失败: {str(e)} - httpx.py:140")
        sys.exit(1)


if __name__ == "__main__":
    main()