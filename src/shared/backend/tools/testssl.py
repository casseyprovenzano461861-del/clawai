# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
TestSSL SSL/TLS漏洞检测工具模块
封装testssl.sh功能，提供SSL/TLS配置检测接口
"""

import subprocess
import json
import sys
import re
import os


class TestSSLTool:
    """TestSSL SSL/TLS检测工具类"""
    
    def __init__(self, testssl_path: str = None):
        # testssl通常是一个shell脚本
        self.testssl_path = testssl_path or self._find_testssl()
        
    def _find_testssl(self):
        """查找testssl安装路径"""
        possible_paths = [
            "testssl.sh",
            "/usr/bin/testssl.sh",
            "/opt/testssl.sh/testssl.sh",
            os.path.expanduser("~/testssl.sh/testssl.sh"),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return "testssl.sh"
        
    def _run_testssl_command(self, target: str, options: dict = None):
        """运行testssl命令"""
        try:
            # 提取主机名和端口
            hostname = target.replace('https://', '').replace('http://', '').split(':')[0]
            port = '443'
            if ':' in target:
                port = target.split(':')[-1].split('/')[0]
            
            cmd = [
                self.testssl_path,
                f'{hostname}:{port}',
                '--jsonfile', '/tmp/testssl_report.json',
                '--color', '0',  # 禁用颜色输出
                '--quiet',       # 安静模式
            ]
            
            if options:
                if options.get('full'):
                    cmd.append('--full')
                if options.get('vulnerabilities'):
                    cmd.append('--vulnerable')
                if options.get('ciphers'):
                    cmd.append('--ciphers')
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                encoding='utf-8',
                errors='ignore'
            )
            
            # 尝试读取JSON输出文件
            json_file = '/tmp/testssl_report.json'
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    json_output = f.read()
                return json_output
            else:
                return result.stdout + result.stderr
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("testssl扫描超时")
        except FileNotFoundError:
            raise RuntimeError("未找到testssl可执行文件，请确保已安装testssl.sh")
        except Exception as e:
            raise RuntimeError(f"执行错误: {str(e)}")
    
    def _parse_output(self, output: str):
        """解析testssl输出"""
        result = {
            "ssl_enabled": False,
            "protocols": [],
            "ciphers": [],
            "vulnerabilities": [],
            "certificate_info": {},
            "rating": "unknown"
        }
        
        try:
            # 尝试解析JSON输出
            data = json.loads(output)
            
            # 检查SSL是否启用
            if isinstance(data, list) and len(data) > 0:
                result["ssl_enabled"] = True
                
                for item in data:
                    # 提取协议信息
                    if item.get('id') == 'protocols':
                        protocols = item.get('finding', '')
                        if protocols:
                            result["protocols"] = [p.strip() for p in protocols.split(',')]
                    
                    # 提取密码套件
                    elif item.get('id') == 'cipherlist':
                        ciphers = item.get('finding', '')
                        if ciphers:
                            result["ciphers"] = [c.strip() for c in ciphers.split('\n') if c.strip()]
                    
                    # 提取漏洞信息
                    elif 'vulnerable' in item.get('id', '').lower() or 'weak' in item.get('id', '').lower():
                        if item.get('severity') in ['HIGH', 'MEDIUM']:
                            vuln = {
                                "name": item.get('id', ''),
                                "severity": item.get('severity', 'MEDIUM'),
                                "description": item.get('finding', '')
                            }
                            result["vulnerabilities"].append(vuln)
                    
                    # 提取证书信息
                    elif 'certificate' in item.get('id', '').lower():
                        cert_key = item.get('id', '').replace('cert_', '')
                        result["certificate_info"][cert_key] = item.get('finding', '')
            
            # 计算评级
            if result["vulnerabilities"]:
                high_count = sum(1 for v in result["vulnerabilities"] if v["severity"] == "HIGH")
                medium_count = sum(1 for v in result["vulnerabilities"] if v["severity"] == "MEDIUM")
                
                if high_count > 0:
                    result["rating"] = "poor"
                elif medium_count > 0:
                    result["rating"] = "fair"
                else:
                    result["rating"] = "good"
            elif result["ssl_enabled"]:
                result["rating"] = "good"
            
        except json.JSONDecodeError:
            # 如果JSON解析失败，尝试文本解析
            self._parse_text_output(output, result)
        
        return result
    
    def _parse_text_output(self, output: str, result: dict):
        """解析文本输出"""
        # 检查SSL是否启用
        if "SSLv2" in output or "SSLv3" in output or "TLS" in output:
            result["ssl_enabled"] = True
        
        # 提取协议
        protocol_pattern = r'(SSLv2|SSLv3|TLSv1\.0|TLSv1\.1|TLSv1\.2|TLSv1\.3)'
        protocols = re.findall(protocol_pattern, output)
        if protocols:
            result["protocols"] = list(set(protocols))
        
        # 提取漏洞
        vuln_patterns = [
            r'(Heartbleed|POODLE|DROWN|BEAST|CRIME|BREACH|FREAK|Logjam)',
            r'(weak cipher|weak protocol|weak key)',
            r'(Certificate expired|Certificate not trusted)'
        ]
        
        for pattern in vuln_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            for match in matches:
                if match and match not in result["vulnerabilities"]:
                    result["vulnerabilities"].append({
                        "name": match,
                        "severity": "MEDIUM",
                        "description": f"检测到{match}漏洞"
                    })
        
        # 简单评级
        if result["vulnerabilities"]:
            result["rating"] = "fair"
        elif result["ssl_enabled"]:
            result["rating"] = "good"
    
    def run(self, target: str, options: dict = None):
        """执行testssl扫描"""
        if not target or not isinstance(target, str):
            raise ValueError("目标必须是有效的URL字符串")
        
        target = target.strip()
        if not target:
            raise ValueError("目标不能为空")
        
        # 确保有协议前缀
        if not (target.startswith('http://') or target.startswith('https://')):
            target = f"https://{target}"
        
        try:
            output = self._run_testssl_command(target, options)
            result = self._parse_output(output)
            
            return {
                "target": target,
                "tool": "testssl",
                "result": result,
                "raw_output": output[:2000] if len(output) > 2000 else output
            }
            
        except Exception as e:
            return {
                "target": target,
                "tool": "testssl",
                "result": {
                    "ssl_enabled": False,
                    "protocols": [],
                    "ciphers": [],
                    "vulnerabilities": [],
                    "certificate_info": {},
                    "rating": "unknown"
                },
                "error": str(e)
            }


def main():
    """命令行入口点"""
    if len(sys.argv) < 2:
        print("用法: python testssl.py <target_url>")
        print("示例: python testssl.py 'https://example.com'")
        sys.exit(1)
    
    target = sys.argv[1]
    tool = TestSSLTool()
    
    try:
        result = tool.run(target)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"扫描失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
