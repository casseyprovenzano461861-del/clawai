# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
XSStrike XSS漏洞检测与利用工具模块
封装XSStrike功能，提供XSS漏洞检测接口
"""

import subprocess
import json
import sys
import re
import os


class XSStrikeTool:
    """XSStrike XSS漏洞检测工具类"""
    
    def __init__(self, xsstrike_path: str = None):
        # XSStrike通常通过python脚本运行
        self.xsstrike_path = xsstrike_path or self._find_xsstrike()
        
    def _find_xsstrike(self):
        """查找XSStrike安装路径"""
        possible_paths = [
            "xsstrike",
            "python xsstrike.py",
            "/opt/XSStrike/xsstrike.py",
            "/usr/share/xsstrike/xsstrike.py",
            os.path.expanduser("~/XSStrike/xsstrike.py"),
        ]
        for path in possible_paths:
            if os.path.exists(path.split()[-1]):
                return path
        return "python xsstrike.py"
        
    def _run_xsstrike_command(self, target: str, options: dict = None):
        """运行XSStrike命令"""
        try:
            cmd = [
                'python', self.xsstrike_path,
                '-u', target,
                '--blind',          # 盲测模式
                '-t', '5',          # 线程数
                '--timeout', '10',  # 超时
            ]
            
            if options:
                if options.get('crawl'):
                    cmd.append('--crawl')
                if options.get('params'):
                    cmd.extend(['--params', options['params']])
                if options.get('data'):
                    cmd.extend(['--data', options['data']])
                if options.get('cookie'):
                    cmd.extend(['--cookie', options['cookie']])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
                encoding='utf-8',
                errors='ignore'
            )
            
            return result.stdout + result.stderr
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("XSStrike扫描超时")
        except FileNotFoundError:
            raise RuntimeError("未找到XSStrike，请确保已安装XSStrike")
        except Exception as e:
            raise RuntimeError(f"执行错误: {str(e)}")
    
    def _parse_output(self, output: str):
        """解析XSStrike输出"""
        result = {
            "vulnerable": False,
            "xss_type": [],
            "payloads": [],
            "vulnerable_params": [],
            "confidence": "low"
        }
        
        # 检测是否发现XSS
        if "Vulnerable" in output or "XSS" in output or "payload" in output.lower():
            result["vulnerable"] = True
            result["confidence"] = "high"
        
        # 提取XSS类型
        if "Reflected" in output:
            result["xss_type"].append("Reflected XSS")
        if "Stored" in output:
            result["xss_type"].append("Stored XSS")
        if "DOM" in output:
            result["xss_type"].append("DOM-based XSS")
        
        # 提取payload
        payload_patterns = [
            r"Payload: (.*?)(?:\n|$)",
            r"<script>(.*?)</script>",
            r"javascript:(.*?)(?:\n|$)",
        ]
        for pattern in payload_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            for match in matches:
                if match and match not in result["payloads"]:
                    result["payloads"].append(match[:200])  # 限制长度
        
        # 提取易受攻击的参数
        param_match = re.findall(r"Parameter: (\w+)", output)
        if param_match:
            result["vulnerable_params"] = list(set(param_match))
        
        return result
    
    def run(self, target: str, options: dict = None):
        """执行XSStrike扫描"""
        if not target or not isinstance(target, str):
            raise ValueError("目标必须是有效的URL字符串")
        
        target = target.strip()
        if not target:
            raise ValueError("目标不能为空")
        
        if not (target.startswith('http://') or target.startswith('https://')):
            target = f"http://{target}"
        
        try:
            output = self._run_xsstrike_command(target, options)
            result = self._parse_output(output)
            
            return {
                "target": target,
                "tool": "xsstrike",
                "result": result,
                "raw_output": output[:2000] if len(output) > 2000 else output
            }
            
        except Exception as e:
            return {
                "target": target,
                "tool": "xsstrike",
                "result": {
                    "vulnerable": False,
                    "xss_type": [],
                    "payloads": [],
                    "vulnerable_params": [],
                    "confidence": "low"
                },
                "error": str(e)
            }


def main():
    """命令行入口点"""
    if len(sys.argv) < 2:
        print("用法: python xsstrike.py <target_url>")
        print("示例: python xsstrike.py 'http://example.com/page.php?q=test'")
        sys.exit(1)
    
    target = sys.argv[1]
    tool = XSStrikeTool()
    
    try:
        result = tool.run(target)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"扫描失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
