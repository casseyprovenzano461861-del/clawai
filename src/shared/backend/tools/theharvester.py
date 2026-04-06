# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
TheHarvester信息收集工具模块
封装theHarvester功能，提供邮箱、子域名等信息收集接口
"""

import subprocess
import json
import sys
import re
import os


class TheHarvesterTool:
    """TheHarvester信息收集工具类"""
    
    def __init__(self, theharvester_path: str = "theHarvester"):
        self.theharvester_path = theharvester_path
        
    def _run_theharvester_command(self, target: str, options: dict = None):
        """运行theHarvester命令"""
        try:
            cmd = [
                self.theharvester_path,
                '-d', target,
                '-b', 'all',        # 所有数据源
                '-l', '100',        # 限制结果数
                '-f', '/tmp/theharvester_report.html',  # 输出文件
            ]
            
            if options:
                if options.get('sources'):
                    cmd.extend(['-b', options['sources']])
                if options.get('limit'):
                    cmd.extend(['-l', str(options['limit'])])
                if options.get('start'):
                    cmd.extend(['-s', str(options['start'])])
                if options.get('takeover'):
                    cmd.append('--takeover')
            
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
            raise RuntimeError("theHarvester扫描超时")
        except FileNotFoundError:
            raise RuntimeError("未找到theHarvester可执行文件，请确保已安装theHarvester")
        except Exception as e:
            raise RuntimeError(f"执行错误: {str(e)}")
    
    def _parse_output(self, output: str):
        """解析theHarvester输出"""
        result = {
            "emails": [],
            "hosts": [],
            "subdomains": [],
            "ips": [],
            "vhosts": [],
            "total_results": 0
        }
        
        # 解析邮箱
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        emails = re.findall(email_pattern, output)
        if emails:
            result["emails"] = list(set(emails))
        
        # 解析主机和子域名
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            
            # 主机/子域名
            if line and not line.startswith('[*]') and not line.startswith('[+]'):
                # 可能是主机名或子域名
                if '.' in line and not line.startswith('http'):
                    # 检查是否是有效域名
                    if re.match(r'^[\w\.-]+\.[a-zA-Z]{2,}$', line):
                        if line not in result["hosts"]:
                            result["hosts"].append(line)
        
        # 解析IP地址
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ips = re.findall(ip_pattern, output)
        if ips:
            result["ips"] = list(set(ips))
        
        # 从hosts中提取子域名
        for host in result["hosts"]:
            if host.startswith('www.') or '.' in host:
                # 提取子域名部分
                parts = host.split('.')
                if len(parts) > 2:
                    subdomain = '.'.join(parts[:-2])
                    if subdomain and subdomain not in result["subdomains"]:
                        result["subdomains"].append(subdomain)
        
        # 统计总数
        result["total_results"] = (
            len(result["emails"]) + 
            len(result["hosts"]) + 
            len(result["subdomains"]) + 
            len(result["ips"]) + 
            len(result["vhosts"])
        )
        
        return result
    
    def run(self, target: str, options: dict = None):
        """执行theHarvester扫描"""
        if not target or not isinstance(target, str):
            raise ValueError("目标必须是有效的域名字符串")
        
        target = target.strip()
        if not target:
            raise ValueError("目标不能为空")
        
        # 移除协议前缀
        target = target.replace('http://', '').replace('https://', '').replace('www.', '')
        
        try:
            output = self._run_theharvester_command(target, options)
            result = self._parse_output(output)
            
            return {
                "target": target,
                "tool": "theharvester",
                "result": result,
                "raw_output": output[:2000] if len(output) > 2000 else output
            }
            
        except Exception as e:
            return {
                "target": target,
                "tool": "theharvester",
                "result": {
                    "emails": [],
                    "hosts": [],
                    "subdomains": [],
                    "ips": [],
                    "vhosts": [],
                    "total_results": 0
                },
                "error": str(e)
            }


def main():
    """命令行入口点"""
    if len(sys.argv) < 2:
        print("用法: python theharvester.py <domain>")
        print("示例: python theharvester.py 'example.com'")
        sys.exit(1)
    
    target = sys.argv[1]
    tool = TheHarvesterTool()
    
    try:
        result = tool.run(target)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"扫描失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
