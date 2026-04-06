# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
JoomScan Joomla漏洞扫描器模块
封装joomscan功能，提供Joomla CMS漏洞检测接口
"""

import subprocess
import json
import sys
import re
import os


class JoomScanTool:
    """JoomScan Joomla漏洞扫描工具类"""
    
    def __init__(self, joomscan_path: str = "joomscan"):
        self.joomscan_path = joomscan_path
        
    def _run_joomscan_command(self, target: str, options: dict = None):
        """运行joomscan命令"""
        try:
            cmd = [
                self.joomscan_path,
                '-u', target,
                '-ec',              # 枚举组件
                '-et',              # 枚举模板
                '-er',              # 枚举模块
                '-es',              # 枚举插件
                '--threads', '5',   # 线程数
                '--timeout', '10',  # 超时时间
            ]
            
            if options:
                if options.get('full'):
                    cmd.append('--full')
                if options.get('cve'):
                    cmd.append('--cve')
                if options.get('cookie'):
                    cmd.extend(['--cookie', options['cookie']])
                if options.get('user_agent'):
                    cmd.extend(['--user-agent', options['user_agent']])
            
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
            raise RuntimeError("joomscan扫描超时")
        except FileNotFoundError:
            raise RuntimeError("未找到joomscan可执行文件，请确保已安装joomscan")
        except Exception as e:
            raise RuntimeError(f"执行错误: {str(e)}")
    
    def _parse_output(self, output: str):
        """解析joomscan输出"""
        result = {
            "joomla_detected": False,
            "version": "",
            "components": [],
            "templates": [],
            "modules": [],
            "plugins": [],
            "vulnerabilities": [],
            "confidence": "low"
        }
        
        # 检测Joomla
        if "Joomla" in output or "joomla" in output.lower():
            result["joomla_detected"] = True
            result["confidence"] = "high"
        
        # 提取版本信息
        version_patterns = [
            r"Version: (.*?)(?:\n|$)",
            r"Joomla! ([\d\.]+)",
            r"v([\d\.]+)"
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                result["version"] = match.group(1).strip()
                break
        
        # 提取组件信息
        component_pattern = r"Component: (.*?)(?:\n|$)"
        components = re.findall(component_pattern, output, re.IGNORECASE)
        if components:
            result["components"] = list(set([c.strip() for c in components]))
        
        # 提取模板信息
        template_pattern = r"Template: (.*?)(?:\n|$)"
        templates = re.findall(template_pattern, output, re.IGNORECASE)
        if templates:
            result["templates"] = list(set([t.strip() for t in templates]))
        
        # 提取模块信息
        module_pattern = r"Module: (.*?)(?:\n|$)"
        modules = re.findall(module_pattern, output, re.IGNORECASE)
        if modules:
            result["modules"] = list(set([m.strip() for m in modules]))
        
        # 提取插件信息
        plugin_pattern = r"Plugin: (.*?)(?:\n|$)"
        plugins = re.findall(plugin_pattern, output, re.IGNORECASE)
        if plugins:
            result["plugins"] = list(set([p.strip() for p in plugins]))
        
        # 提取漏洞信息
        vuln_patterns = [
            r"Vulnerability: (.*?)(?:\n|$)",
            r"\[!\] (.*?)(?:\n|$)",
            r"CVE-(\d{4}-\d+)",
            r"Exploit: (.*?)(?:\n|$)"
        ]
        
        for pattern in vuln_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            for match in matches:
                if match and match not in result["vulnerabilities"]:
                    result["vulnerabilities"].append(match.strip())
        
        return result
    
    def run(self, target: str, options: dict = None):
        """执行joomscan扫描"""
        if not target or not isinstance(target, str):
            raise ValueError("目标必须是有效的URL字符串")
        
        target = target.strip()
        if not target:
            raise ValueError("目标不能为空")
        
        if not (target.startswith('http://') or target.startswith('https://')):
            target = f"http://{target}"
        
        try:
            output = self._run_joomscan_command(target, options)
            result = self._parse_output(output)
            
            return {
                "target": target,
                "tool": "joomscan",
                "result": result,
                "raw_output": output[:2000] if len(output) > 2000 else output
            }
            
        except Exception as e:
            return {
                "target": target,
                "tool": "joomscan",
                "result": {
                    "joomla_detected": False,
                    "version": "",
                    "components": [],
                    "templates": [],
                    "modules": [],
                    "plugins": [],
                    "vulnerabilities": [],
                    "confidence": "low"
                },
                "error": str(e)
            }


def main():
    """命令行入口点"""
    if len(sys.argv) < 2:
        print("用法: python joomscan.py <target_url>")
        print("示例: python joomscan.py 'http://example.com'")
        sys.exit(1)
    
    target = sys.argv[1]
    tool = JoomScanTool()
    
    try:
        result = tool.run(target)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"扫描失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
