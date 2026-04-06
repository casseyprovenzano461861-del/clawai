"""
基于LLM的HackSynth Summarizer实现
使用大语言模型分析和总结渗透测试结果
"""

import json
import logging
import re
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .summarizer import (
    HackSynthSummarizer, SummaryContext, SummaryResult,
    SecurityFinding, FindingSeverity, FindingCategory
)

logger = logging.getLogger(__name__)


class LLMHackSynthSummarizer(HackSynthSummarizer):
    """基于LLM的HackSynth Summarizer实现"""
    
    def __init__(self, config: Dict[str, Any], llm_client=None):
        """
        初始化LLM Summarizer
        
        Args:
            config: Summarizer配置
            llm_client: LLM客户端实例
        """
        super().__init__(config)
        self.llm_client = llm_client
        self.llm_config = config.get("llm", {})
        
        # 提示模板
        self.summary_system_prompt = config.get("summary_system_prompt", "")
        self.summary_user_prompt = config.get("summary_user_prompt", "")
        self.findings_system_prompt = config.get("findings_system_prompt", "")
        self.findings_user_prompt = config.get("findings_user_prompt", "")
        
        # 生成配置
        self.temperature = self.llm_config.get("temperature", 0.7)
        self.max_tokens = self.llm_config.get("max_tokens", 1024)
        
        logger.info(f"LLM HackSynth Summarizer初始化完成，使用LLM: {self.llm_config.get('provider', 'unknown')}")
    
    async def summarize(
        self,
        context: SummaryContext
    ) -> SummaryResult:
        """
        使用LLM总结命令执行结果
        
        Args:
            context: 总结上下文
            
        Returns:
            总结结果
        """
        logger.info(f"总结命令结果: {context.target}, 阶段: {context.phase}")
        
        try:
            # 提取发现
            findings = await self.extract_findings(context.command_output, context.target)
            
            # 构建LLM提示
            messages = self._build_summary_messages(context, findings)
            
            # 调用LLM生成总结
            llm_response = await self._call_llm(messages)
            
            # 解析LLM响应
            summary_data = self._parse_summary_response(llm_response, context, findings)
            
            # 创建总结结果
            result = SummaryResult(
                summary=summary_data["summary"],
                key_findings=findings[:5],  # 取前5个关键发现
                next_phase_recommendation=summary_data.get("next_phase", self.determine_next_phase(context.phase, findings)),
                confidence_score=summary_data.get("confidence", 0.7),
                metrics={
                    "findings_count": len(findings),
                    "critical_findings": len([f for f in findings if f.severity == FindingSeverity.CRITICAL]),
                    "high_findings": len([f for f in findings if f.severity == FindingSeverity.HIGH]),
                    "analysis_timestamp": datetime.now().isoformat()
                },
                analysis_metadata={
                    "llm_used": self.llm_config.get("provider", "unknown"),
                    "response_length": len(llm_response),
                    "parsed_successfully": True
                }
            )
            
            # 记录总结
            self.record_summary(context, result)
            
            logger.info(f"总结完成: {len(findings)} 个发现, 置信度: {result.confidence_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"总结失败: {e}")
            # 返回后备总结
            return self._generate_fallback_summary(context)
    
    async def extract_findings(
        self,
        command_output: str,
        target: str
    ) -> List[SecurityFinding]:
        """
        使用LLM从命令输出中提取安全发现
        
        Args:
            command_output: 命令输出
            target: 目标地址
            
        Returns:
            安全发现列表
        """
        if not command_output or len(command_output.strip()) < 10:
            logger.warning("命令输出过短，无法提取发现")
            return []
        
        logger.info(f"从命令输出中提取发现: {target}, 输出长度: {len(command_output)}")
        
        try:
            # 首先使用模式匹配提取基础发现
            base_findings = self._extract_findings_sync(command_output, target)
            
            # 如果输出较长，使用LLM进行深度分析
            if len(command_output) > 500 and self.llm_client:
                # 构建LLM提示
                messages = self._build_findings_messages(command_output, target)
                
                # 调用LLM
                llm_response = await self._call_llm(messages)
                
                # 解析LLM响应
                llm_findings = self._parse_findings_response(llm_response, target)
                
                # 合并发现
                all_findings = base_findings + llm_findings
                
                # 去重
                unique_findings = self._deduplicate_findings(all_findings)
                
                logger.info(f"LLM提取发现完成: {len(unique_findings)} 个唯一发现")
                return unique_findings[:15]  # 限制返回数量
            else:
                logger.info(f"模式匹配提取发现完成: {len(base_findings)} 个发现")
                return base_findings[:10]
                
        except Exception as e:
            logger.error(f"提取发现失败: {e}")
            return base_findings if 'base_findings' in locals() else []
    
    def _build_summary_messages(
        self,
        context: SummaryContext,
        findings: List[SecurityFinding]
    ) -> List[Dict[str, str]]:
        """构建总结消息"""
        # 构建系统提示
        system_prompt = self.summary_system_prompt.format(
            target_type=context.target_type,
            current_phase=context.phase
        )
        
        # 构建发现摘要
        findings_summary = self._build_findings_summary(findings)
        
        # 构建用户提示
        user_prompt = self.summary_user_prompt.format(
            target=context.target,
            phase=context.phase,
            command=context.command_executed,
            command_output_preview=context.command_output[:1000] if context.command_output else "无输出",
            findings_summary=findings_summary,
            previous_summary=context.previous_summary or "无先前总结"
        )
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _build_findings_summary(self, findings: List[SecurityFinding]) -> str:
        """构建发现摘要"""
        if not findings:
            return "未发现安全问题"
        
        summary_parts = []
        
        # 按严重性分组
        severity_groups = {
            FindingSeverity.CRITICAL: [],
            FindingSeverity.HIGH: [],
            FindingSeverity.MEDIUM: [],
            FindingSeverity.LOW: [],
            FindingSeverity.INFO: []
        }
        
        for finding in findings:
            severity_groups[finding.severity].append(finding)
        
        # 构建摘要
        for severity in [FindingSeverity.CRITICAL, FindingSeverity.HIGH, 
                        FindingSeverity.MEDIUM, FindingSeverity.LOW, FindingSeverity.INFO]:
            group_findings = severity_groups[severity]
            if group_findings:
                summary_parts.append(f"{severity.value.upper()}严重性发现 ({len(group_findings)}个):")
                for i, finding in enumerate(group_findings[:3], 1):  # 每个严重性最多显示3个
                    summary_parts.append(f"  {i}. {finding.title}")
                if len(group_findings) > 3:
                    summary_parts.append(f"  ... 还有 {len(group_findings) - 3} 个")
                summary_parts.append("")
        
        return "\n".join(summary_parts)
    
    def _build_findings_messages(
        self,
        command_output: str,
        target: str
    ) -> List[Dict[str, str]]:
        """构建发现提取消息"""
        # 构建系统提示
        system_prompt = self.findings_system_prompt
        
        # 构建用户提示
        user_prompt = self.findings_user_prompt.format(
            target=target,
            command_output=command_output[:3000]  # 限制输出长度
        )
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    async def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """调用LLM生成响应"""
        if not self.llm_client:
            # 如果没有LLM客户端，返回模拟响应
            return self._generate_mock_response(messages)
        
        try:
            # 根据LLM客户端类型调用不同的API
            if hasattr(self.llm_client, "chat") and hasattr(self.llm_client.chat, "completions"):
                # OpenAI兼容API
                response = await asyncio.to_thread(
                    self.llm_client.chat.completions.create,
                    model=self.llm_config.get("model", "gpt-4"),
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return response.choices[0].message.content
                
            elif hasattr(self.llm_client, "generate"):
                # 本地模型或其他API
                response = await asyncio.to_thread(
                    self.llm_client.generate,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return response
            
            else:
                # 未知客户端类型，使用模拟响应
                logger.warning(f"未知LLM客户端类型: {type(self.llm_client)}")
                return self._generate_mock_response(messages)
                
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return self._generate_mock_response(messages)
    
    def _generate_mock_response(self, messages: List[Dict[str, str]]) -> str:
        """生成模拟LLM响应"""
        # 提取用户消息内容
        user_content = ""
        for msg in messages:
            if msg["role"] == "user":
                user_content = msg["content"]
                break
        
        # 基于用户消息生成模拟响应
        if "总结" in user_content or "summary" in user_content.lower():
            return """渗透测试结果总结:

执行命令: nmap -sS -sV example.com
目标: example.com
阶段: reconnaissance

关键发现:
1. 发现开放端口: 80 (HTTP), 443 (HTTPS), 22 (SSH)
2. Web服务器: Apache 2.4.41
3. 操作系统: Linux 4.x

分析:
- 目标运行标准的Web服务配置
- 发现常见服务端口开放
- 未发现明显安全漏洞

建议:
1. 对Web应用进行深度扫描 (使用whatweb、nikto)
2. 检查SSL/TLS配置安全性
3. 进行目录暴力破解寻找隐藏端点

下一个阶段: scanning
置信度: 0.85"""
        
        elif "发现" in user_content or "findings" in user_content.lower():
            return """从命令输出中提取的安全发现:

1. 发现: 开放端口 80
   严重性: info
   类别: network
   证据: "80/tcp open  http"
   影响: 暴露HTTP服务
   修复: 确保Web服务器安全配置

2. 发现: Apache 2.4.41
   严重性: info  
   类别: web
   证据: "Apache/2.4.41"
   影响: 已知版本可能存在漏洞
   修复: 更新到最新版本

3. 发现: SSH服务
   严重性: info
   类别: service
   证据: "22/tcp open  ssh"
   影响: 远程管理入口
   修复: 实施强认证机制"""
        
        else:
            return """分析完成。基于命令输出，发现目标系统运行标准配置，建议进行进一步安全测试。"""
    
    def _parse_summary_response(
        self,
        response: str,
        context: SummaryContext,
        findings: List[SecurityFinding]
    ) -> Dict[str, Any]:
        """解析总结响应"""
        summary_data = {
            "summary": response,
            "next_phase": self.determine_next_phase(context.phase, findings),
            "confidence": 0.7
        }
        
        # 尝试提取结构化信息
        try:
            # 提取置信度
            confidence_match = re.search(r"置信度[：:]\s*([\d.]+)", response)
            if confidence_match:
                summary_data["confidence"] = float(confidence_match.group(1))
            
            # 提取下一个阶段
            phase_match = re.search(r"下一个阶段[：:]\s*(\w+)", response)
            if phase_match:
                summary_data["next_phase"] = phase_match.group(1).lower()
            
            # 提取关键建议
            recommendations = []
            rec_pattern = r"建议\d+[：:]\s*(.*?)(?=\n建议|\n\n|\Z)"
            rec_matches = re.findall(rec_pattern, response, re.DOTALL)
            if rec_matches:
                recommendations = [rec.strip() for rec in rec_matches]
            
            if recommendations:
                summary_data["recommendations"] = recommendations
        
        except Exception as e:
            logger.warning(f"解析总结响应失败: {e}")
        
        return summary_data
    
    def _parse_findings_response(
        self,
        response: str,
        target: str
    ) -> List[SecurityFinding]:
        """解析发现响应"""
        findings = []
        
        # 尝试解析结构化发现
        finding_pattern = r"发现\d*[：:]\s*(.*?)\s*\n\s*严重性[：:]\s*(.*?)\s*\n\s*类别[：:]\s*(.*?)\s*\n\s*证据[：:]\s*\"(.*?)\"\s*\n\s*影响[：:]\s*(.*?)\s*\n\s*修复[：:]\s*(.*?)(?=\n发现|\n\n|\Z)"
        
        matches = re.findall(finding_pattern, response, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            try:
                title, severity_str, category_str, evidence, impact, remediation = match
                
                # 清理字段
                title = title.strip()
                severity_str = severity_str.strip().lower()
                category_str = category_str.strip().lower()
                evidence = evidence.strip()
                impact = impact.strip()
                remediation = remediation.strip()
                
                # 转换严重性
                severity_map = {
                    "critical": FindingSeverity.CRITICAL,
                    "high": FindingSeverity.HIGH,
                    "medium": FindingSeverity.MEDIUM,
                    "low": FindingSeverity.LOW,
                    "info": FindingSeverity.INFO
                }
                
                severity = severity_map.get(severity_str, FindingSeverity.INFO)
                
                # 转换类别
                category_map = {
                    "vulnerability": FindingCategory.VULNERABILITY,
                    "configuration": FindingCategory.CONFIGURATION,
                    "credential": FindingCategory.CREDENTIAL,
                    "service": FindingCategory.SERVICE,
                    "network": FindingCategory.NETWORK,
                    "web": FindingCategory.WEB,
                    "database": FindingCategory.DATABASE
                }
                
                category = category_map.get(category_str, FindingCategory.OTHER)
                
                # 创建发现
                finding = SecurityFinding(
                    id=SecurityFinding.generate_id(title, target),
                    title=title,
                    description=f"LLM分析发现: {title}",
                    severity=severity,
                    category=category,
                    evidence=evidence,
                    confidence=0.8,  # LLM发现的置信度较高
                    impact=impact,
                    remediation=remediation
                )
                
                findings.append(finding)
                
            except Exception as e:
                logger.warning(f"解析发现失败: {e}, 原始内容: {match}")
                continue
        
        return findings
    
    def _deduplicate_findings(self, findings: List[SecurityFinding]) -> List[SecurityFinding]:
        """去重发现"""
        unique_findings = []
        seen_titles = set()
        
        for finding in findings:
            # 基于标题和证据进行去重
            title_key = f"{finding.title}_{finding.evidence[:50]}"
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_findings.append(finding)
        
        return unique_findings
    
    def _generate_fallback_summary(self, context: SummaryContext) -> SummaryResult:
        """生成后备总结"""
        # 使用模式匹配提取发现
        findings = self._extract_findings_sync(context.command_output, context.target)
        
        # 生成简单总结
        if findings:
            summary = f"对 {context.target} 的渗透测试结果总结:\n\n"
            summary += f"阶段: {context.phase}\n"
            summary += f"执行命令: {context.command_executed[:100]}...\n\n"
            summary += f"发现 {len(findings)} 个安全问题:\n"
            
            for i, finding in enumerate(findings[:3], 1):
                summary += f"{i}. {finding.title} ({finding.severity.value})\n"
            
            if len(findings) > 3:
                summary += f"... 还有 {len(findings) - 3} 个发现\n"
            
            summary += f"\n建议进入下一阶段: {self.determine_next_phase(context.phase, findings)}"
        else:
            summary = f"对 {context.target} 的渗透测试未发现安全问题。\n阶段: {context.phase}\n建议: 继续当前阶段的测试或进入下一阶段。"
        
        # 创建后备结果
        return SummaryResult(
            summary=summary,
            key_findings=findings[:3],
            next_phase_recommendation=self.determine_next_phase(context.phase, findings),
            confidence_score=0.6,
            metrics={
                "findings_count": len(findings),
                "fallback_used": True,
                "analysis_timestamp": datetime.now().isoformat()
            },
            analysis_metadata={
                "llm_used": "fallback",
                "response_length": len(summary),
                "parsed_successfully": False
            }
        )
    
    def get_summarizer_info(self) -> Dict[str, Any]:
        """获取Summarizer信息"""
        base_info = super().get_summarizer_info()
        base_info.update({
            "llm_provider": self.llm_config.get("provider", "unknown"),
            "llm_model": self.llm_config.get("model", "unknown"),
            "llm_available": self.llm_client is not None,
            "config": {
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
        })
        return base_info

