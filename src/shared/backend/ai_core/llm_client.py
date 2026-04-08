#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM客户端
用于集成AI能力，为渗透测试提供智能分析和决策
"""

import os
import asyncio
import json
from typing import Dict, List, Optional, Any


class LLMClient:
    """LLM客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化LLM客户端
        
        Args:
            api_key: API密钥
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = "gpt-3.5-turbo"
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """生成AI响应
        
        Args:
            prompt: 提示词
            **kwargs: 额外参数
            
        Returns:
            AI响应
        """
        try:
            # 模拟LLM响应
            # 实际实现中，这里应该调用OpenAI API或其他LLM服务
            await asyncio.sleep(1)  # 模拟网络延迟
            
            # 基于提示词生成响应
            response = self._generate_mock_response(prompt)
            
            return {
                "success": True,
                "response": response,
                "model": self.model
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_vulnerability(self, vulnerability: Dict[str, Any]) -> Dict[str, Any]:
        """分析漏洞
        
        Args:
            vulnerability: 漏洞信息
            
        Returns:
            分析结果
        """
        prompt = f"""请分析以下漏洞，并提供详细的分析和修复建议：

漏洞信息：
{json.dumps(vulnerability, indent=2, ensure_ascii=False)}

请提供：
1. 漏洞详细分析
2. 可能的攻击场景
3. 修复建议
4. 风险等级评估"""
        
        result = await self.generate(prompt)
        return result
    
    async def generate_exploit(self, vulnerability: Dict[str, Any]) -> Dict[str, Any]:
        """生成漏洞利用方案
        
        Args:
            vulnerability: 漏洞信息
            
        Returns:
            利用方案
        """
        prompt = f"""请为以下漏洞生成详细的利用方案：

漏洞信息：
{json.dumps(vulnerability, indent=2, ensure_ascii=False)}

请提供：
1. 利用步骤
2. 所需工具
3. 预期结果
4. 注意事项"""
        
        result = await self.generate(prompt)
        return result
    
    async def generate_report(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成渗透测试报告
        
        Args:
            scan_results: 扫描结果
            
        Returns:
            报告内容
        """
        prompt = f"""请基于以下扫描结果生成详细的渗透测试报告：

扫描结果：
{json.dumps(scan_results, indent=2, ensure_ascii=False)}

报告应包含：
1. 执行摘要
2. 测试目标和范围
3. 发现的漏洞
4. 漏洞分析
5. 修复建议
6. 安全加固措施"""
        
        result = await self.generate(prompt)
        return result
    
    def _generate_mock_response(self, prompt: str) -> str:
        """生成模拟响应
        
        Args:
            prompt: 提示词
            
        Returns:
            模拟响应
        """
        if "漏洞分析" in prompt:
            return """## 漏洞分析

该漏洞是一个典型的SQL注入漏洞，攻击者可以通过操纵输入参数来执行恶意SQL语句。

### 可能的攻击场景
1. 未授权访问数据库
2. 数据泄露
3. 数据库被篡改
4. 服务器被完全控制

### 修复建议
1. 使用参数化查询
2. 实施输入验证
3. 最小权限原则
4. 定期安全审计

### 风险等级评估
**高风险** - 可以导致数据泄露和系统完全被控制"""
        elif "利用方案" in prompt:
            return """## 漏洞利用方案

### 利用步骤
1. 确认漏洞存在：使用单引号测试
2. 提取数据库信息：使用UNION注入
3. 获取敏感数据：查询用户表
4. 提升权限：利用数据库函数

### 所需工具
- SQLmap
- Burp Suite
- 浏览器

### 预期结果
成功获取数据库中的敏感信息，包括用户凭据和配置信息。

### 注意事项
- 操作前获得授权
- 避免对生产系统造成破坏
- 记录所有操作步骤"""
        elif "渗透测试报告" in prompt:
            return """# 渗透测试报告

## 1. 执行摘要
本次渗透测试针对目标系统进行了全面的安全评估，发现了多个安全漏洞，其中包括高危漏洞。

## 2. 测试目标和范围
- 目标：192.168.1.1
- 测试范围：Web应用和网络服务
- 测试时间：2026-04-07

## 3. 发现的漏洞
- SQL注入漏洞（高危）
- 信息泄露漏洞（中危）
- XSS漏洞（低危）

## 4. 漏洞分析
详细分析了每个漏洞的技术细节和潜在影响。

## 5. 修复建议
提供了详细的修复方案和时间线。

## 6. 安全加固措施
建议实施的长期安全措施，包括定期安全审计和员工培训。"""
        else:
            return "我是ClawAI的AI助手，专门用于渗透测试和安全分析。我可以帮助你分析漏洞、生成利用方案和编写测试报告。"    
    async def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """聊天模式
        
        Args:
            messages: 消息列表
            
        Returns:
            聊天响应
        """
        try:
            # 模拟聊天响应
            await asyncio.sleep(0.5)
            
            # 基于最后一条消息生成响应
            last_message = messages[-1].get("content", "")
            response = self._generate_chat_response(last_message)
            
            return {
                "success": True,
                "response": response,
                "model": self.model
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_chat_response(self, message: str) -> str:
        """生成聊天响应
        
        Args:
            message: 用户消息
            
        Returns:
            聊天响应
        """
        message = message.lower()
        
        if "你好" in message or "hi" in message or "hello" in message:
            return "你好！我是ClawAI的AI助手，专门用于渗透测试和安全分析。有什么我可以帮助你的吗？"
        elif "帮助" in message or "help" in message:
            return "我可以帮助你：\n1. 分析漏洞\n2. 生成漏洞利用方案\n3. 编写渗透测试报告\n4. 提供安全建议\n请告诉我你需要什么帮助。"
        elif "漏洞" in message:
            return "请提供漏洞的详细信息，我可以帮你分析并提供修复建议。"
        elif "扫描" in message or "测试" in message:
            return "请告诉我你要测试的目标，我可以帮你制定测试计划。"
        else:
            return "我理解你需要帮助，请提供更多细节，以便我能够更好地协助你。"


# 测试代码
if __name__ == "__main__":
    async def test_llm_client():
        client = LLMClient()
        
        # 测试生成响应
        result = await client.generate("分析SQL注入漏洞")
        print("生成响应:")
        print(result["response"])
        print()
        
        # 测试聊天
        chat_result = await client.chat([
            {"role": "user", "content": "你好，我需要帮助分析一个漏洞"}
        ])
        print("聊天响应:")
        print(chat_result["response"])
        print()
        
        # 测试漏洞分析
        vulnerability = {
            "id": "vuln_1",
            "name": "SQL注入漏洞",
            "severity": "high",
            "description": "目标存在SQL注入漏洞",
            "location": "http://example.com/api?id=1"
        }
        analysis_result = await client.analyze_vulnerability(vulnerability)
        print("漏洞分析:")
        print(analysis_result["response"])
    
    asyncio.run(test_llm_client())
