# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
CMSMap CMS漏洞扫描器模块
封装CMSMap功能，提供WordPress、Joomla、Drupal等CMS漏洞检测接口
"""

import subprocess
import json
import sys
import re
import os


class CMSMapTool:
    """CMSMap CMS漏洞扫描工具类"""
    
    def __init__(self, cmsmap_path: str = "cmsmap"):
        self.cmsmap_path = cmsmap_path
        
    def _run_cmsmap_command(self, target: str, options: dict = None):
        """运行CMSMap命令"""
        try:
            cmd = [
                self.cmsmap_path,
                '-t', target,
                '-f',              # 指纹识别
                '-s',              # 扫描漏洞
                '--noedb',         # 不检查Exploit-DB
                '--threads', '3',  # 线程数
                '--timeout', '10', # 超时时间
            ]
            
            if options:
                if options.get('cms_type'):
                    cmd.extend(['-F', options['cms_type']])  # 指定CMS类型
                if options.get('plugins'):
                    cmd.append('--plugins')  # 扫描插件
                if options.get('themes'):
                    cmd.append('--themes')   # 扫描主题
                if options.get('aggressive'):
                    cmd.append('-a')         # 激进模式
            
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
            raise RuntimeError("CMSMap扫描超时")
        except FileNotFoundError:
            raise RuntimeError("未找到CMSMap可执行文件，请确保已安装CMSMap")
        except Exception as e:
            raise RuntimeError(f"执行错误: {str(e)}")
    
    def _parse_output(self, output: str):
        """解析CMSMap输出"""
        result = {
            "cms_detected": "",
            "version": "",
            "vulnerabilities": [],
            "plugins": [],
            "themes": [],
            "confidence": "low"
        }
        
        # 检测CMS类型
        cms_patterns = [
            (r"WordPress detected", "WordPress"),
            (r"Joomla detected", "Joomla"),
            (r"Drupal detected", "Drupal"),
            (r"Version: (.*?)(?:\n|$)", "version")
        ]
        
        for pattern, cms_type in cms_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                if cms_type == "version":
                    result["version"] = match.group(1).strip()
                elif not result["cms_detected"]:
                    result["cms_detected"] = cms_type
                    result["confidence"] = "high"
        
        # 提取漏洞信息
        vuln_patterns = [
            r"Vulnerability: (.*?)(?:\n|$)",
            r"\[!\] (.*?)(?:\n|$)",
            r"Exploit: (.*?)(?:\n|$)"
        ]
        
        for pattern in vuln_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            for match in matches:
                if match and match not in result["vulnerabilities"]:
                    result["vulnerabilities"].append(match.strip())
        
        # 提取插件信息
        plugin_match = re.findall(r"Plugin: (.*?)(?:\n|$)", output, re.IGNORECASE)
        if plugin_match:
            result["plugins"] = list(set([p.strip() for p in plugin_match]))
        
        # 提取主题信息
        theme_match = re.findall(r"Theme: (.*?)(?:\n|$)", output, re.IGNORECASE)
        if theme_match:
            result["themes"] = list(set([t.strip() for t in theme_match]))
        
        return result
    
    def run(self, target: str, options: dict = None):
        """执行CMSMap扫描"""
        if not target or not isinstance(target, str):
            raise ValueError("目标必须是有效的URL字符串")
        
        target = target.strip()
        if not target:
            raise ValueError("目标不能为空")
        
        if not (target.startswith('http://') or target.startswith('https://')):
            target = f"http://{target}"
        
        try:
            output = self._run_cmsmap_command(target, options)
            result = self._parse_output(output)
            
            return {
                "target": target,
                "tool": "cmsmap",
                "result": result,
                "raw_output": output[:2000] if len(output) > 2000 else output
            }
            
        except Exception as e:
            return {
                "target": target,
                "tool": "cmsmap",
                "result": {
                    "cms_detected": "",
                    "version": "",
                    "vulnerabilities": [],
                    "plugins": [],
                    "themes": [],
                    "confidence": "low"
                },
                "error": str(e)
            }


def main():
    """命令行入口点"""
    if len(sys.argv) < 2:
        print("用法: python cmsmap.py <target_url>")
        print("示例: python cmsmap.py 'http://example.com'")
        sys.exit(1)
    
    target = sys.argv[1]
    tool = CMSMapTool()
    
    try:
        result = tool.run(target)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"扫描失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
