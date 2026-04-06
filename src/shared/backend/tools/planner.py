# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI调度模块 (Planner)
根据扫描上下文决定下一步执行的工具
"""

import json
import os
import sys
import requests


class AIPlanner:
    def __init__(self, api_key=None, api_base="https://api.deepseek.com"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.api_url = f"{api_base}/chat/completions"
    
    def _call_deepseek_api(self, prompt):
        if not self.api_key:
            return None
            
        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是一个渗透测试调度AI。根据给定的扫描上下文，决定下一步应该执行哪个工具。只返回JSON格式的决策，不要解释。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 500
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return None
                
        except Exception:
            return None
    
    def _parse_ai_response(self, response):
        try:
            lines = response.strip().split('\n')
            json_str = ""
            in_json = False
            
            for line in lines:
                line = line.strip()
                if line.startswith('{') or line.startswith('['):
                    in_json = True
                if in_json:
                    json_str += line
                if line.endswith('}') or line.endswith(']'):
                    break
            
            if not json_str:
                json_str = response.strip()
            
            data = json.loads(json_str)
            
            if isinstance(data, dict) and "actions" in data:
                return data["actions"]
            elif isinstance(data, list):
                return data
            else:
                return []
                
        except Exception:
            return []
    
    def _build_prompt(self, context):
        prompt = """基于以下渗透测试上下文，决定下一步应该执行哪个工具。

扫描上下文：
1. 开放端口: {ports}
2. 指纹信息: {fingerprint}
3. 已知漏洞: {vulnerabilities}
4. 资产列表: {assets}

请分析上下文并返回JSON格式的决策，格式如下：
{{
  "actions": [
    {{
      "tool": "工具名称",
      "reason": "选择理由",
      "priority": 优先级数字(1-10)
    }}
  ]
}}

工具池：
- dirsearch: 目录扫描
- nikto: Web漏洞扫描
- whatweb: Web指纹识别
- sqlmap: SQL注入测试
- nmap: 端口扫描和服务识别
- nuclei: 漏洞扫描
- wpscan: WordPress扫描
- joomscan: Joomla扫描
- masscan: 快速端口扫描
- gobuster: 目录爆破

请基于以下规则决策：
1. 如果有Web服务(80,443,8080等) → dirsearch/nikto
2. 如果有数据库端口(3306,5432等) → sqlmap
3. 如果有CMS指纹(WordPress,Joomla等) → 对应CMS扫描器
4. 如果信息不足 → nmap深度扫描

只返回JSON，不要其他内容。""".format(
            ports=json.dumps(context.get("ports", {}), ensure_ascii=False),
            fingerprint=json.dumps(context.get("fingerprint", {}), ensure_ascii=False),
            vulnerabilities=json.dumps(context.get("vulnerabilities", {}), ensure_ascii=False),
            assets=json.dumps(context.get("assets", []), ensure_ascii=False)
        )
        
        return prompt
    
    def _fallback_rules(self, context):
        actions = []
        ports = context.get("ports", {})
        fingerprint = context.get("fingerprint", {})
        
        web_ports = {80, 443, 8080, 8443, 8888}
        has_web = any(port in web_ports for port in ports.keys())
        
        if has_web:
            actions.append({"tool": "dirsearch", "reason": "发现Web服务端口", "priority": 1})
        
        db_ports = {3306, 5432, 27017, 6379}
        has_db = any(port in db_ports for port in ports.keys())
        
        if has_db:
            actions.append({"tool": "sqlmap", "reason": "发现数据库端口", "priority": 2})
        
        cms_info = fingerprint.get("fingerprint", {})
        cms_list = cms_info.get("cms", [])
        
        for cms in cms_list:
            cms_lower = cms.lower()
            if "wordpress" in cms_lower:
                actions.append({"tool": "wpscan", "reason": "发现WordPress系统", "priority": 1})
            elif "joomla" in cms_lower:
                actions.append({"tool": "joomscan", "reason": "发现Joomla系统", "priority": 1})
        
        if not actions:
            actions.append({"tool": "nmap", "reason": "进行深度端口扫描", "priority": 3})
        
        return actions
    
    def plan(self, context):
        prompt = self._build_prompt(context)
        ai_response = self._call_deepseek_api(prompt)
        
        actions = []
        
        if ai_response:
            actions = self._parse_ai_response(ai_response)
        
        if not actions:
            actions = self._fallback_rules(context)
        
        actions.sort(key=lambda x: x.get("priority", 10))
        
        return {"actions": actions}


def main():
    example_context = {
        "ports": {80: "http", 443: "https", 3306: "mysql"},
        "fingerprint": {
            "fingerprint": {
                "web_server": "nginx/1.18.0",
                "language": ["PHP 7.4"],
                "cms": ["WordPress 5.8"],
                "other": []
            }
        },
        "vulnerabilities": {},
        "assets": ["http://example.com", "https://example.com"]
    }
    
    planner = AIPlanner()
    
    try:
        plan = planner.plan(example_context)
        print(json.dumps(plan, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"计划制定失败: {str(e)} - planner.py:191")
        sys.exit(1)


if __name__ == "__main__":
    main()