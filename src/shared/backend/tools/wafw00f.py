# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Wafw00f WAF指纹识别工具模块
封装wafw00f功能，提供Web应用防火墙检测接口
"""

import subprocess
import json
import sys
import re
import os


class Wafw00fTool:
    """Wafw00f WAF检测工具类"""
    
    def __init__(self, wafw00f_path: str = "wafw00f"):
        self.wafw00f_path = wafw00f_path
        
    def _run_wafw00f_command(self, target: str, options: dict = None):
        """运行wafw00f命令"""
        try:
            cmd = [
                self.wafw00f_path,
                target,
                '-a',              # 查找所有WAF
                '-v',              # 详细输出
                '--findall',       # 查找所有可能的WAF
            ]
            
            if options:
                if options.get('proxy'):
                    cmd.extend(['-p', options['proxy']])
                if options.get('headers'):
                    cmd.extend(['-H', options['headers']])
                if options.get('timeout'):
                    cmd.extend(['-t', str(options['timeout'])])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                encoding='utf-8',
                errors='ignore'
            )
            
            return result.stdout + result.stderr
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("wafw00f扫描超时")
        except FileNotFoundError:
            raise RuntimeError("未找到wafw00f可执行文件，请确保已安装wafw00f")
        except Exception as e:
            raise RuntimeError(f"执行错误: {str(e)}")
    
    def _parse_output(self, output: str):
        """解析wafw00f输出"""
        result = {
            "waf_detected": False,
            "waf_name": "",
            "waf_vendor": "",
            "detection_method": [],
            "confidence": "low",
            "bypass_techniques": []
        }
        
        # 检测是否发现WAF
        if "is behind" in output.lower() or "detected" in output.lower():
            result["waf_detected"] = True
            result["confidence"] = "high"
        
        # 提取WAF名称
        waf_patterns = [
            r"behind (.*?) WAF",
            r"Detected (.*?) WAF",
            r"WAF: (.*?)(?:\n|$)",
            r"(Cloudflare|Akamai|Imperva|F5|Fortinet|Barracuda|Citrix|AWS WAF|Azure WAF|Sucuri)"
        ]
        
        for pattern in waf_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                waf_name = match.group(1).strip()
                if waf_name and not result["waf_name"]:
                    result["waf_name"] = waf_name
                    break
        
        # 提取WAF厂商
        vendor_map = {
            'cloudflare': 'Cloudflare',
            'akamai': 'Akamai',
            'imperva': 'Imperva',
            'f5': 'F5 Networks',
            'fortinet': 'Fortinet',
            'barracuda': 'Barracuda',
            'citrix': 'Citrix',
            'aws': 'Amazon Web Services',
            'azure': 'Microsoft Azure',
            'sucuri': 'Sucuri'
        }
        
        for keyword, vendor in vendor_map.items():
            if keyword in output.lower():
                result["waf_vendor"] = vendor
                break
        
        # 提取检测方法
        method_patterns = [
            r"using (.*?) method",
            r"Method: (.*?)(?:\n|$)",
            r"(cookie inspection|header analysis|challenge response|block page detection)"
        ]
        
        for pattern in method_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            for match in matches:
                if match and match not in result["detection_method"]:
                    result["detection_method"].append(match)
        
        # 生成绕过技术建议
        if result["waf_name"]:
            bypass_map = {
                'Cloudflare': ['IP轮换', 'User-Agent随机化', '请求延迟', '使用CDN节点'],
                'Akamai': ['请求参数混淆', 'HTTP方法切换', '使用代理池', '会话保持'],
                'Imperva': ['请求头随机化', '使用WebSocket', '慢速攻击', '分块传输'],
                'F5': ['SSL/TLS指纹修改', 'TCP参数调整', '使用IPv6', '协议降级'],
                'AWS WAF': ['地理IP切换', '请求大小限制绕过', '使用Lambda函数', 'API网关']
            }
            
            for waf_key, techniques in bypass_map.items():
                if waf_key.lower() in result["waf_name"].lower():
                    result["bypass_techniques"] = techniques
                    break
            
            # 通用绕过技术
            if not result["bypass_techniques"]:
                result["bypass_techniques"] = [
                    'User-Agent随机化',
                    '请求头混淆',
                    'IP地址轮换',
                    '请求延迟',
                    '使用代理或VPN'
                ]
        
        return result
    
    def run(self, target: str, options: dict = None):
        """执行wafw00f扫描"""
        if not target or not isinstance(target, str):
            raise ValueError("目标必须是有效的URL字符串")
        
        target = target.strip()
        if not target:
            raise ValueError("目标不能为空")
        
        if not (target.startswith('http://') or target.startswith('https://')):
            target = f"http://{target}"
        
        try:
            output = self._run_wafw00f_command(target, options)
            result = self._parse_output(output)
            
            return {
                "target": target,
                "tool": "wafw00f",
                "result": result,
                "raw_output": output[:2000] if len(output) > 2000 else output
            }
            
        except Exception as e:
            return {
                "target": target,
                "tool": "wafw00f",
                "result": {
                    "waf_detected": False,
                    "waf_name": "",
                    "waf_vendor": "",
                    "detection_method": [],
                    "confidence": "low",
                    "bypass_techniques": []
                },
                "error": str(e)
            }


def main():
    """命令行入口点"""
    if len(sys.argv) < 2:
        print("用法: python wafw00f.py <target_url>")
        print("示例: python wafw00f.py 'http://example.com'")
        sys.exit(1)
    
    target = sys.argv[1]
    tool = Wafw00fTool()
    
    try:
        result = tool.run(target)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"扫描失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
