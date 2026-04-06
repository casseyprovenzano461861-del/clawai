# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Tplmap模板注入利用工具模块
封装tplmap功能，提供模板注入检测和利用接口
"""

import subprocess
import json
import sys
import re
import os


class TplmapTool:
    """Tplmap模板注入工具类"""
    
    def __init__(self, tplmap_path: str = "tplmap"):
        self.tplmap_path = tplmap_path
        
    def _run_tplmap_command(self, target: str, options: dict = None):
        """运行tplmap命令"""
        try:
            cmd = [
                self.tplmap_path,
                '-u', target,
                '--batch',          # 非交互模式
                '--level', '2',     # 测试级别
                '--timeout', '10',  # 超时时间
                '--technique', 'all',  # 所有技术
                '--engine', 'all',     # 所有引擎
            ]
            
            if options:
                if options.get('data'):
                    cmd.extend(['--data', options['data']])
                if options.get('cookie'):
                    cmd.extend(['--cookie', options['cookie']])
                if options.get('engine'):
                    cmd.extend(['--engine', options['engine']])
                if options.get('os'):
                    cmd.extend(['--os', options['os']])
            
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
            raise RuntimeError("tplmap扫描超时")
        except FileNotFoundError:
            raise RuntimeError("未找到tplmap可执行文件，请确保已安装tplmap")
        except Exception as e:
            raise RuntimeError(f"执行错误: {str(e)}")
    
    def _parse_output(self, output: str):
        """解析tplmap输出"""
        result = {
            "vulnerable": False,
            "engine_detected": "",
            "injection_type": [],
            "os_detected": "",
            "payloads": [],
            "confidence": "low"
        }
        
        # 检测是否存在模板注入
        if "injection point" in output.lower() or "vulnerable" in output.lower():
            result["vulnerable"] = True
            result["confidence"] = "high"
        
        # 提取模板引擎
        engine_patterns = [
            r"Engine: (.*?)(?:\n|$)",
            r"Template engine: (.*?)(?:\n|$)",
            r"(Jinja2|Twig|Smarty|Freemarker|Velocity|Mako|ERB|JSP|ASP|PHP)"
        ]
        for pattern in engine_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                result["engine_detected"] = match.group(1).strip()
                break
        
        # 提取注入类型
        injection_patterns = [
            r"Type: (.*?)(?:\n|$)",
            r"(code context)",
            r"(blind)",
            r"(time-based)",
            r"(file read)",
            r"(file write)"
        ]
        for pattern in injection_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            for match in matches:
                if match and match not in result["injection_type"]:
                    result["injection_type"].append(match)
        
        # 提取操作系统信息
        os_match = re.search(r"OS: (.*?)(?:\n|$)", output, re.IGNORECASE)
        if os_match:
            result["os_detected"] = os_match.group(1).strip()
        
        # 提取payload示例
        payload_patterns = [
            r"Payload: (.*?)(?:\n|$)",
            r"Exploit: (.*?)(?:\n|$)",
            r"Command: (.*?)(?:\n|$)"
        ]
        for pattern in payload_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            for match in matches:
                if match and match not in result["payloads"]:
                    result["payloads"].append(match[:200])  # 限制长度
        
        return result
    
    def run(self, target: str, options: dict = None):
        """执行tplmap扫描"""
        if not target or not isinstance(target, str):
            raise ValueError("目标必须是有效的URL字符串")
        
        target = target.strip()
        if not target:
            raise ValueError("目标不能为空")
        
        if not (target.startswith('http://') or target.startswith('https://')):
            target = f"http://{target}"
        
        try:
            output = self._run_tplmap_command(target, options)
            result = self._parse_output(output)
            
            return {
                "target": target,
                "tool": "tplmap",
                "result": result,
                "raw_output": output[:2000] if len(output) > 2000 else output
            }
            
        except Exception as e:
            return {
                "target": target,
                "tool": "tplmap",
                "result": {
                    "vulnerable": False,
                    "engine_detected": "",
                    "injection_type": [],
                    "os_detected": "",
                    "payloads": [],
                    "confidence": "low"
                },
                "error": str(e)
            }


def main():
    """命令行入口点"""
    if len(sys.argv) < 2:
        print("用法: python tplmap.py <target_url>")
        print("示例: python tplmap.py 'http://example.com/page?name=test'")
        sys.exit(1)
    
    target = sys.argv[1]
    tool = TplmapTool()
    
    try:
        result = tool.run(target)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"扫描失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
