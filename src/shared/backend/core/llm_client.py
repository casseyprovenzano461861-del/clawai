# -*- coding: utf-8 -*-
"""
LLMClient模块 - 语言模型客户端
负责与语言模型进行交互
"""

import os
import requests
from typing import Optional, Dict, Any


class LLMClient:
    """语言模型客户端类"""
    
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = "deepseek-chat"
    
    def call(self, prompt: str, system_prompt: str = "你是一个资深网络安全专家，擅长攻击路径分析和威胁建模") -> Optional[str]:
        """调用语言模型"""
        if not self.api_key:
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            }
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
        except Exception as e:
            print(f"调用LLM失败: {str(e)}")
            return None
    
    def analyze_security(self, scan_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """分析安全扫描结果"""
        target = scan_result.get('target', 'unknown')
        ports = scan_result.get('ports', [])
        vulnerabilities = scan_result.get('vulnerabilities', [])
        
        ports_str = "无开放端口"
        if ports:
            ports_list = [f"{p.get('port', '')}/{p.get('service', '未知')}" for p in ports]
            ports_str = "、".join(ports_list)
        
        vulns_str = "无已知漏洞"
        if vulnerabilities:
            vulns_list = []
            for v in vulnerabilities:
                name = v.get('name', '未知漏洞')
                severity = v.get('severity', 'unknown')
                vulns_list.append(f"{name}({severity})")
            vulns_str = "、".join(vulns_list)
        
        prompt = f"""请分析以下安全扫描结果：

目标：{target}
开放端口：{ports_str}
漏洞：{vulns_str}

请以资深网络安全专家的身份，进行攻击路径推演和威胁分析，输出JSON格式的分析结果：
{{
  "summary": "简要总结安全状况",
  "risk_level": "low/medium/high",
  "attack_path": "攻击者可能如何利用这些端口和漏洞进行攻击，包括攻击路径、利用方式和潜在危害",
  "advice": "具体的修复建议和安全措施"
}}

攻击路径分析要求：
1. 即使没有漏洞，也要分析端口暴露的攻击面
2. 考虑攻击者如何利用开放端口进行初始访问
3. 分析可能的横向移动路径
4. 评估权限提升的可能性
5. 考虑数据泄露和持久化威胁

请确保输出是有效的JSON格式，不要包含其他内容。"""
        
        response = self.call(prompt)
        if response:
            try:
                import json
                return json.loads(response.strip())
            except Exception:
                pass
        
        return None
