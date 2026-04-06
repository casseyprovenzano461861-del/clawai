# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
WhatWeb指纹识别工具模块
用于识别网站使用的技术栈和框架，并生成攻击路径分析
"""

import subprocess
import json
import sys
import re


class WhatWebTool:
    def __init__(self, whatweb_path="whatweb"):
        self.whatweb_path = whatweb_path
        self.tech_map = {
            'nginx': 'web_server', 'apache': 'web_server', 'iis': 'web_server',
            'php': 'language', 'python': 'language', 'node': 'language', 'java': 'language',
            'django': 'framework', 'laravel': 'framework', 'spring': 'framework',
            'wordpress': 'cms', 'joomla': 'cms', 'drupal': 'cms'
        }
    
    def _run_whatweb_command(self, target):
        try:
            cmd = [self.whatweb_path, '-a', '3', '--log-json', '-', '--no-errors', target]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, encoding='utf-8', errors='ignore')
            if result.returncode != 0:
                raise RuntimeError(f"whatweb命令执行失败: {result.returncode}")
            return result.stdout
        except subprocess.TimeoutExpired:
            raise RuntimeError("whatweb扫描超时")
        except FileNotFoundError:
            raise RuntimeError("未找到whatweb可执行文件")
        except Exception as e:
            raise RuntimeError(f"执行错误: {str(e)}")
    
    def _categorize_tech(self, tech_name):
        tech_lower = tech_name.lower()
        for keyword, category in self.tech_map.items():
            if keyword in tech_lower:
                return category
        return "other"
    
    def _generate_attack_paths(self, fingerprint):
        """生成攻击路径描述"""
        paths = []
        
        # Web服务器攻击路径
        if fingerprint["web_server"]:
            server = fingerprint["web_server"].lower()
            if 'nginx' in server:
                paths.append("Nginx服务器可能存在配置错误，导致目录遍历或请求走私攻击")
            elif 'apache' in server:
                paths.append("Apache服务器可能存在.htaccess配置漏洞，导致权限绕过或文件泄露")
            elif 'iis' in server:
                paths.append("IIS服务器可能存在解析漏洞，导致短文件名泄露或权限配置错误")
        
        # 编程语言攻击路径
        for lang in fingerprint["language"]:
            if len(paths) >= 3:
                break
            lang_lower = lang.lower()
            if 'php' in lang_lower:
                paths.append("PHP环境可能存在文件上传漏洞，结合远程代码执行(RCE)实现系统控制")
            elif 'python' in lang_lower:
                paths.append("Python应用可能存在反序列化漏洞，导致远程代码执行或数据泄露")
            elif 'node' in lang_lower:
                paths.append("Node.js应用可能存在原型链污染或依赖包漏洞，导致命令注入攻击")
            elif 'java' in lang_lower:
                paths.append("Java应用可能存在反序列化漏洞，结合XXE攻击实现远程代码执行")
        
        # 框架攻击路径
        if len(paths) < 3:
            for framework in fingerprint["framework"]:
                if len(paths) >= 3:
                    break
                framework_lower = framework.lower()
                if 'django' in framework_lower:
                    paths.append("Django框架可能存在CSRF漏洞或调试模式泄露，导致权限提升攻击")
                elif 'laravel' in framework_lower:
                    paths.append("Laravel框架可能存在反序列化漏洞或配置泄露，导致路由绕过攻击")
                elif 'spring' in framework_lower:
                    paths.append("Spring框架可能存在远程代码执行漏洞，结合反序列化实现权限提升")
        
        # CMS攻击路径
        if len(paths) < 3:
            for cms in fingerprint["cms"]:
                if len(paths) >= 3:
                    break
                cms_lower = cms.lower()
                if 'wordpress' in cms_lower:
                    paths.append("WordPress系统可能存在插件或主题漏洞，结合弱口令攻击实现权限提升")
                elif 'joomla' in cms_lower:
                    paths.append("Joomla系统可能存在组件漏洞，导致SQL注入或文件上传攻击")
                elif 'drupal' in cms_lower:
                    paths.append("Drupal系统可能存在模块漏洞，导致远程代码执行或权限提升攻击")
        
        # 补充通用攻击路径
        if len(paths) < 3:
            generic = [
                "系统可能存在弱口令漏洞，导致未授权访问或权限提升",
                "应用可能存在信息泄露漏洞，暴露敏感配置或用户数据",
                "服务可能存在配置错误，导致权限绕过或服务暴露"
            ]
            for path in generic:
                if len(paths) >= 3:
                    break
                if path not in paths:
                    paths.append(path)
        
        return paths
    
    def _parse_output(self, output):
        fingerprint = {"web_server": "", "language": [], "framework": [], "cms": [], "other": []}
        
        try:
            data = json.loads(output)
            if not data:
                fingerprint["attack_surface"] = []
                return fingerprint
            
            plugins = data[0].get("plugins", {})
            for plugin_name, plugin_data in plugins.items():
                if isinstance(plugin_data, dict):
                    category = self._categorize_tech(plugin_name)
                    
                    if category == "web_server" and not fingerprint["web_server"]:
                        string_data = plugin_data.get("string", [])
                        if string_data:
                            fingerprint["web_server"] = string_data[0]
                    elif category != "web_server":
                        tech_info = plugin_name
                        version = plugin_data.get("version", [])
                        if version:
                            tech_info += f" {version[0]}"
                        if tech_info not in fingerprint[category]:
                            fingerprint[category].append(tech_info)
            
            fingerprint["attack_surface"] = self._generate_attack_paths(fingerprint)
            return fingerprint
            
        except json.JSONDecodeError:
            return self._parse_text(output)
        except Exception:
            fingerprint["attack_surface"] = []
            return fingerprint
    
    def _parse_text(self, output):
        fingerprint = {"web_server": "", "language": [], "framework": [], "cms": [], "other": []}
        
        for line in output.split('\n'):
            line = line.strip()
            
            server_match = re.search(r'Server\[(.*?)\]', line)
            if server_match and not fingerprint["web_server"]:
                fingerprint["web_server"] = server_match.group(1)
            
            tech_match = re.search(r'([A-Z][a-zA-Z]+)\[(.*?)\]', line)
            if tech_match:
                tech_name = tech_match.group(1)
                if tech_name in ['HTTPServer', 'Title', 'IP', 'Country']:
                    continue
                
                category = self._categorize_tech(tech_name)
                tech_info = tech_name
                tech_value = tech_match.group(2)
                if tech_value and tech_value != tech_name:
                    tech_info += f" {tech_value}"
                
                if category == "web_server" and not fingerprint["web_server"]:
                    fingerprint["web_server"] = tech_info
                elif category != "web_server" and tech_info not in fingerprint[category]:
                    fingerprint[category].append(tech_info)
        
        fingerprint["attack_surface"] = self._generate_attack_paths(fingerprint)
        return fingerprint
    
    def run(self, target):
        if not target or not isinstance(target, str):
            raise ValueError("目标必须是有效的字符串")
        
        target = target.strip()
        if not target:
            raise ValueError("目标不能为空")
        
        if not (target.startswith('http://') or target.startswith('https://')):
            target = f"http://{target}"
        
        try:
            output = self._run_whatweb_command(target)
            fingerprint = self._parse_output(output)
            return {"target": target, "fingerprint": fingerprint}
            
        except Exception as e:
            return {
                "target": target,
                "fingerprint": {
                    "web_server": "", 
                    "language": [], 
                    "framework": [], 
                    "cms": [], 
                    "other": [],
                    "attack_surface": []
                },
                "error": str(e)
            }


def main():
    if len(sys.argv) != 2:
        print("用法: python  <target_url> - whatweb.py:211")
        sys.exit(1)
    
    target = sys.argv[1]
    tool = WhatWebTool()
    
    try:
        result = tool.run(target)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"指纹识别失败: {str(e)} - whatweb.py:221")
        sys.exit(1)


if __name__ == "__main__":
    main()