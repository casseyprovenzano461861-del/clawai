"""
基于LLM的HackSynth Planner实现
使用大语言模型生成智能渗透测试命令
"""

import json
import logging
import re
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .planner import (
    HackSynthPlanner, PlanningContext, CommandSuggestion,
    PlanningPhase, CommandComplexity
)

logger = logging.getLogger(__name__)


class LLMHackSynthPlanner(HackSynthPlanner):
    """基于LLM的HackSynth Planner实现"""
    
    def __init__(self, config: Dict[str, Any], llm_client=None):
        """
        初始化LLM Planner
        
        Args:
            config: Planner配置
            llm_client: LLM客户端实例
        """
        super().__init__(config)
        self.llm_client = llm_client
        self.llm_config = config.get("llm", {})
        
        # 提示模板
        self.system_prompt_template = config.get("system_prompt", "")
        self.user_prompt_template = config.get("user_prompt", "")
        
        # 生成配置
        self.temperature = self.llm_config.get("temperature", 0.7)
        self.max_tokens = self.llm_config.get("max_tokens", 1024)
        
        logger.info(f"LLM HackSynth Planner初始化完成，使用LLM: {self.llm_config.get('provider', 'unknown')}")
    
    async def generate_plan(
        self,
        context: PlanningContext,
        available_tools: List[str],
        max_suggestions: int = 3
    ) -> List[CommandSuggestion]:
        """
        使用LLM生成渗透测试计划
        
        Args:
            context: 规划上下文
            available_tools: 可用工具列表
            max_suggestions: 最大建议数量
            
        Returns:
            命令建议列表
        """
        logger.info(f"生成渗透测试计划: {context.target}, 阶段: {context.current_phase}")
        
        try:
            # 构建LLM提示
            messages = self._build_llm_messages(context, available_tools)
            
            # 调用LLM生成响应
            llm_response = await self._call_llm(messages)
            
            # 解析LLM响应
            suggestions = self._parse_llm_response(
                llm_response, context, available_tools
            )
            
            # 限制建议数量
            suggestions = suggestions[:max_suggestions]
            
            # 记录规划决策
            self.record_planning_decision(context, suggestions)
            
            logger.info(f"生成 {len(suggestions)} 个命令建议")
            return suggestions
            
        except Exception as e:
            logger.error(f"生成计划失败: {e}")
            # 返回后备建议
            return self._generate_fallback_suggestions(context, available_tools)
    
    async def evaluate_command(
        self,
        command: str,
        context: PlanningContext
    ) -> Dict[str, Any]:
        """
        使用LLM评估命令的适用性
        
        Args:
            command: 待评估的命令
            context: 规划上下文
            
        Returns:
            评估结果
        """
        logger.info(f"评估命令: {command[:50]}...")
        
        try:
            # 构建评估提示
            messages = self._build_evaluation_messages(command, context)
            
            # 调用LLM进行评估
            llm_response = await self._call_llm(messages)
            
            # 解析评估结果
            evaluation = self._parse_evaluation_response(llm_response, command, context)
            
            # 添加工具有效性数据
            tool = self._extract_tool_from_command(command)
            if tool and tool in self.tool_effectiveness:
                evaluation["tool_effectiveness"] = {
                    "success_rate": self.tool_effectiveness[tool].success_rate,
                    "reliability_score": self.tool_effectiveness[tool].reliability_score
                }
            
            logger.info(f"命令评估完成: {evaluation.get('overall_score', 0):.2f}")
            return evaluation
            
        except Exception as e:
            logger.error(f"命令评估失败: {e}")
            return self._generate_fallback_evaluation(command, context)
    
    def _build_llm_messages(
        self,
        context: PlanningContext,
        available_tools: List[str]
    ) -> List[Dict[str, str]]:
        """构建LLM消息"""
        # 构建系统提示
        system_prompt = self.system_prompt_template.format(
            available_tools=", ".join(available_tools),
            current_phase=context.current_phase.value,
            target_type=context.target_type
        )
        
        # 构建用户提示
        context_summary = self._build_context_summary(context)
        user_prompt = self.user_prompt_template.format(
            target=context.target,
            context_summary=context_summary,
            available_tools=", ".join(available_tools),
            current_phase=context.current_phase.value,
            previous_commands="\n".join(context.previous_commands[-5:]) if context.previous_commands else "无"
        )
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _build_context_summary(self, context: PlanningContext) -> str:
        """构建上下文摘要"""
        summary_parts = []
        
        # 目标信息
        summary_parts.append(f"目标: {context.target}")
        summary_parts.append(f"目标类型: {context.target_type}")
        summary_parts.append(f"当前阶段: {context.current_phase.value}")
        
        # 发现信息
        if context.open_ports:
            summary_parts.append(f"开放端口: {', '.join(map(str, context.open_ports[:10]))}")
            if len(context.open_ports) > 10:
                summary_parts.append(f"... 共 {len(context.open_ports)} 个端口")
        
        if context.discovered_services:
            summary_parts.append(f"发现服务: {', '.join(context.discovered_services[:10])}")
            if len(context.discovered_services) > 10:
                summary_parts.append(f"... 共 {len(context.discovered_services)} 个服务")
        
        if context.vulnerabilities_found:
            summary_parts.append(f"发现漏洞: {', '.join(context.vulnerabilities_found[:5])}")
            if len(context.vulnerabilities_found) > 5:
                summary_parts.append(f"... 共 {len(context.vulnerabilities_found)} 个漏洞")
        
        if context.credentials_obtained:
            summary_parts.append(f"获取凭证: {len(context.credentials_obtained)} 个")
        
        # 约束条件
        if context.constraints:
            constraints_str = ", ".join([f"{k}: {v}" for k, v in context.constraints.items()])
            summary_parts.append(f"约束条件: {constraints_str}")
        
        return "\n".join(summary_parts)
    
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
        if "侦察" in user_content or "reconnaissance" in user_content.lower():
            return """基于当前上下文，建议执行以下命令：

1. **nmap基础扫描**
命令: `nmap -sS -sV -O {target}`
工具: nmap
阶段: reconnaissance
复杂性: medium
估计时间: 60秒
成功概率: 0.95
理由: 基础端口扫描，识别开放端口和服务版本
预期输出: 开放端口列表、服务版本信息、操作系统检测

2. **Web技术栈识别**
命令: `whatweb {target}`
工具: whatweb
阶段: reconnaissance
复杂性: low
估计时间: 30秒
成功概率: 0.90
理由: 识别Web应用技术栈，为后续扫描提供信息
预期输出: Web服务器、框架、CMS、技术栈信息

3. **目录暴力破解**
命令: `dirsearch -u {target} -e php,html,js -t 50`
工具: dirsearch
阶段: reconnaissance
复杂性: medium
估计时间: 90秒
成功概率: 0.80
理由: 发现隐藏目录和文件，扩大攻击面
预期输出: 发现的目录和文件列表"""
        
        elif "扫描" in user_content or "scanning" in user_content.lower():
            return """基于当前上下文，建议执行以下命令：

1. **nmap漏洞脚本扫描**
命令: `nmap -sS -sV --script vuln {target}`
工具: nmap
阶段: scanning
复杂性: high
估计时间: 120秒
成功概率: 0.85
理由: 使用nmap漏洞脚本检测已知漏洞
预期输出: 漏洞检测结果、安全配置问题

2. **nuclei漏洞扫描**
命令: `nuclei -u {target} -t cves/ -severity critical,high`
工具: nuclei
阶段: scanning
复杂性: medium
估计时间: 150秒
成功概率: 0.85
理由: 快速扫描已知CVE漏洞
预期输出: CVE漏洞列表、严重级别

3. **nikto Web漏洞扫描**
命令: `nikto -h {target}`
工具: nikto
阶段: scanning
复杂性: medium
估计时间: 180秒
成功概率: 0.75
理由: 全面Web服务器漏洞扫描
预期输出: Web服务器配置问题、已知漏洞"""
        
        else:
            return """基于当前上下文，建议执行以下命令：

1. **基础信息收集**
命令: `nmap -sS -sV {target}`
工具: nmap
阶段: reconnaissance
复杂性: medium
估计时间: 60秒
成功概率: 0.95
理由: 基础信息收集，了解目标系统
预期输出: 开放端口、服务版本信息

2. **Web应用识别**
命令: `whatweb {target}`
工具: whatweb
阶段: reconnaissance
复杂性: low
估计时间: 30秒
成功概率: 0.90
理由: 识别Web应用技术栈
预期输出: Web技术栈信息

3. **快速漏洞扫描**
命令: `nuclei -u {target} -t exposures/`
工具: nuclei
阶段: scanning
复杂性: medium
估计时间: 90秒
成功概率: 0.80
理由: 快速扫描暴露的配置和文件
预期输出: 暴露的配置、敏感文件"""
    
    def _parse_llm_response(
        self,
        response: str,
        context: PlanningContext,
        available_tools: List[str]
    ) -> List[CommandSuggestion]:
        """解析LLM响应为命令建议列表"""
        suggestions = []
        
        # 使用正则表达式提取命令块
        command_pattern = r"(\d+)\.\s*\*\*(.*?)\*\*\s*\n命令:\s*`(.*?)`\s*\n工具:\s*(.*?)\s*\n阶段:\s*(.*?)\s*\n复杂性:\s*(.*?)\s*\n估计时间:\s*(\d+)\s*秒\s*\n成功概率:\s*([\d.]+)\s*\n理由:\s*(.*?)\s*\n预期输出:\s*(.*?)(?=\n\d+\.|\Z)"
        
        matches = re.findall(command_pattern, response, re.DOTALL | re.MULTILINE)
        
        for match in matches:
            try:
                # 提取匹配的字段
                _, name, command, tool, phase_str, complexity_str, time_str, prob_str, rationale, expected_output = match
                
                # 清理字段
                command = command.strip()
                tool = tool.strip()
                phase_str = phase_str.strip().lower()
                complexity_str = complexity_str.strip().lower()
                time_str = time_str.strip()
                prob_str = prob_str.strip()
                rationale = rationale.strip()
                expected_output = expected_output.strip()
                
                # 转换阶段枚举
                phase_map = {
                    "reconnaissance": PlanningPhase.RECONNAISSANCE,
                    "scanning": PlanningPhase.SCANNING,
                    "vulnerability_assessment": PlanningPhase.VULNERABILITY_ASSESSMENT,
                    "exploitation": PlanningPhase.EXPLOITATION,
                    "post_exploitation": PlanningPhase.POST_EXPLOITATION
                }
                
                phase = phase_map.get(phase_str, PlanningPhase.RECONNAISSANCE)
                
                # 转换复杂性枚举
                complexity_map = {
                    "low": CommandComplexity.LOW,
                    "medium": CommandComplexity.MEDIUM,
                    "high": CommandComplexity.HIGH
                }
                
                complexity = complexity_map.get(complexity_str, CommandComplexity.MEDIUM)
                
                # 转换数值
                estimated_time = float(time_str)
                success_probability = float(prob_str)
                
                # 替换目标占位符
                command = command.replace("{target}", context.target)
                
                # 创建命令建议
                suggestion = CommandSuggestion(
                    command=command,
                    tool=tool,
                    phase=phase,
                    complexity=complexity,
                    estimated_time=estimated_time,
                    success_probability=success_probability,
                    rationale=rationale,
                    expected_output=expected_output if expected_output else None,
                    risk_level=self._determine_risk_level(command, complexity)
                )
                
                suggestions.append(suggestion)
                
            except Exception as e:
                logger.warning(f"解析命令建议失败: {e}, 原始内容: {match}")
                continue
        
        # 如果没有解析到结构化内容，尝试提取简单命令
        if not suggestions:
            suggestions = self._extract_simple_commands(response, context, available_tools)
        
        return suggestions
    
    def _extract_simple_commands(
        self,
        response: str,
        context: PlanningContext,
        available_tools: List[str]
    ) -> List[CommandSuggestion]:
        """从响应中提取简单命令"""
        suggestions = []
        
        # 查找命令模式
        command_patterns = [
            r"命令:\s*`(.*?)`",
            r"command:\s*`(.*?)`",
            r"`(.*?)`",
            r"执行:\s*(.*?)\n"
        ]
        
        commands_found = []
        for pattern in command_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            commands_found.extend(matches)
        
        # 去重
        commands_found = list(set(commands_found))
        
        for cmd in commands_found[:3]:  # 最多取3个命令
            try:
                # 清理命令
                cmd = cmd.strip()
                if not cmd:
                    continue
                
                # 替换目标占位符
                cmd = cmd.replace("{target}", context.target)
                
                # 提取工具名称
                tool = self._extract_tool_from_command(cmd) or "unknown"
                
                # 创建简单建议
                suggestion = CommandSuggestion(
                    command=cmd,
                    tool=tool,
                    phase=context.current_phase,
                    complexity=self._estimate_command_complexity(cmd, tool),
                    estimated_time=60.0,
                    success_probability=self._calculate_success_probability(cmd, tool, context),
                    rationale="从LLM响应中提取的命令",
                    risk_level=self._determine_risk_level(cmd, self._estimate_command_complexity(cmd, tool))
                )
                
                suggestions.append(suggestion)
                
            except Exception as e:
                logger.warning(f"创建简单命令建议失败: {e}, 命令: {cmd}")
                continue
        
        return suggestions
    
    def _determine_risk_level(self, command: str, complexity: CommandComplexity) -> str:
        """确定风险级别"""
        command_lower = command.lower()
        
        # 高风险操作
        high_risk_patterns = [
            r"sqlmap.*--os-shell",
            r"hydra.*-l.*-p.*",
            r"msfconsole.*exploit",
            r"rm\s+",
            r"chmod\s+777",
            r"wget.*-O.*/tmp/",
            r"curl.*\|.*bash"
        ]
        
        for pattern in high_risk_patterns:
            if re.search(pattern, command_lower):
                return "high"
        
        # 中风险操作
        medium_risk_patterns = [
            r"sqlmap.*--dbs",
            r"nmap.*-A",
            r"nuclei.*-severity.*critical",
            r"nikto.*-Tuning.*4",
            r"dirsearch.*-t.*100"
        ]
        
        for pattern in medium_risk_patterns:
            if re.search(pattern, command_lower):
                return "medium"
        
        # 基于复杂性判断
        if complexity == CommandComplexity.HIGH:
            return "medium"
        elif complexity == CommandComplexity.MEDIUM:
            return "low"
        else:
            return "low"
    
    def _build_evaluation_messages(self, command: str, context: PlanningContext) -> List[Dict[str, str]]:
        """构建评估消息"""
        system_prompt = """你是一个渗透测试命令评估专家。你的任务是评估给定命令在当前上下文中的适用性、安全性和有效性。

评估维度:
1. 技术正确性 - 命令语法是否正确，参数是否合理
2. 上下文相关性 - 命令是否适合当前渗透测试阶段和目标
3. 安全性 - 命令是否可能对目标系统造成意外损害
4. 效率 - 命令是否高效，是否有更好的替代方案
5. 合规性 - 命令是否符合渗透测试最佳实践

请提供详细的评估报告，包括评分（0-10分）和改进建议。"""
        
        context_summary = self._build_context_summary(context)
        
        user_prompt = f"""请评估以下渗透测试命令:

命令: `{command}`

当前上下文:
{context_summary}

请从以下维度进行评估:
1. 技术正确性 (0-10分)
2. 上下文相关性 (0-10分) 
3. 安全性 (0-10分)
4. 效率 (0-10分)
5. 合规性 (0-10分)

提供每个维度的评分、理由和改进建议。最后给出总体评分和建议。"""
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _parse_evaluation_response(self, response: str, command: str, context: PlanningContext) -> Dict[str, Any]:
        """解析评估响应"""
        evaluation = {
            "command": command,
            "timestamp": datetime.now().isoformat(),
            "dimensions": {},
            "overall_score": 0.0,
            "recommendations": [],
            "risk_assessment": {}
        }
        
        # 提取维度评分
        dimension_patterns = {
            "technical_correctness": r"技术正确性.*?(\d+(?:\.\d+)?)",
            "context_relevance": r"上下文相关性.*?(\d+(?:\.\d+)?)",
            "safety": r"安全性.*?(\d+(?:\.\d+)?)",
            "efficiency": r"效率.*?(\d+(?:\.\d+)?)",
            "compliance": r"合规性.*?(\d+(?:\.\d+)?)"
        }
        
        for dim_name, pattern in dimension_patterns.items():
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    evaluation["dimensions"][dim_name] = {
                        "score": score,
                        "max_score": 10.0
                    }
                except ValueError:
                    evaluation["dimensions"][dim_name] = {
                        "score": 5.0,
                        "max_score": 10.0
                    }
        
        # 计算总体评分
        if evaluation["dimensions"]:
            total_score = sum(dim["score"] for dim in evaluation["dimensions"].values())
            evaluation["overall_score"] = total_score / len(evaluation["dimensions"])
        
        # 提取建议
        recommendation_pattern = r"建议[：:]\s*(.*?)(?=\n\n|\Z)"
        recommendations = re.findall(recommendation_pattern, response, re.DOTALL)
        if recommendations:
            evaluation["recommendations"] = [rec.strip() for rec in recommendations if rec.strip()]
        
        # 风险评估
        tool = self._extract_tool_from_command(command)
        complexity = self._estimate_command_complexity(command, tool)
        risk_level = self._determine_risk_level(command, complexity)
        
        evaluation["risk_assessment"] = {
            "risk_level": risk_level,
            "complexity": complexity.value,
            "tool": tool or "unknown"
        }
        
        return evaluation
    
    def _generate_fallback_evaluation(self, command: str, context: PlanningContext) -> Dict[str, Any]:
        """生成后备评估结果"""
        tool = self._extract_tool_from_command(command)
        complexity = self._estimate_command_complexity(command, tool)
        risk_level = self._determine_risk_level(command, complexity)
        
        # 基于工具和复杂性生成简单评估
        base_score = 6.0
        if tool and tool in self.tool_effectiveness:
            base_score = self.tool_effectiveness[tool].success_rate * 10
        
        # 基于复杂性调整
        if complexity == CommandComplexity.HIGH:
            base_score -= 1.0
        elif complexity == CommandComplexity.LOW:
            base_score += 1.0
        
        return {
            "command": command,
            "timestamp": datetime.now().isoformat(),
            "dimensions": {
                "technical_correctness": {"score": base_score, "max_score": 10.0},
                "context_relevance": {"score": base_score - 1.0, "max_score": 10.0},
                "safety": {"score": 7.0, "max_score": 10.0},
                "efficiency": {"score": base_score, "max_score": 10.0},
                "compliance": {"score": 6.0, "max_score": 10.0}
            },
            "overall_score": base_score - 0.5,
            "recommendations": [
                "这是自动生成的评估，建议进行人工审查",
                f"命令使用工具: {tool or 'unknown'}",
                f"复杂性: {complexity.value}, 风险级别: {risk_level}"
            ],
            "risk_assessment": {
                "risk_level": risk_level,
                "complexity": complexity.value,
                "tool": tool or "unknown"
            }
        }
    
    def _generate_fallback_suggestions(
        self,
        context: PlanningContext,
        available_tools: List[str]
    ) -> List[CommandSuggestion]:
        """生成后备命令建议"""
        suggestions = []
        
        # 基于阶段生成建议
        if context.current_phase == PlanningPhase.RECONNAISSANCE:
            commands = [
                ("nmap -sS -sV -O {target}", "nmap", 60.0, 0.95),
                ("whatweb {target}", "whatweb", 30.0, 0.90),
                ("dirsearch -u {target} -e php,html,js -t 50", "dirsearch", 90.0, 0.80)
            ]
        elif context.current_phase == PlanningPhase.SCANNING:
            commands = [
                ("nmap -sS -sV --script vuln {target}", "nmap", 120.0, 0.85),
                ("nuclei -u {target} -t cves/ -severity critical,high", "nuclei", 150.0, 0.85),
                ("nikto -h {target}", "nikto", 180.0, 0.75)
            ]
        elif context.current_phase == PlanningPhase.VULNERABILITY_ASSESSMENT:
            commands = [
                ("sqlmap -u 'http://{target}/login.php' --forms --batch", "sqlmap", 180.0, 0.70),
                ("nuclei -u {target} -t exposures/", "nuclei", 120.0, 0.80),
                ("nmap -sS -sV --script http-vuln* {target}", "nmap", 150.0, 0.75)
            ]
        elif context.current_phase == PlanningPhase.EXPLOITATION:
            commands = [
                ("sqlmap -u 'http://{target}/vuln.php?id=1' --os-shell", "sqlmap", 300.0, 0.60),
                ("hydra -l admin -P /usr/share/wordlists/rockyou.txt {target} ssh", "hydra", 600.0, 0.50),
                ("msfconsole -q -x 'use exploit/unix/ssh/sshexec; set RHOSTS {target}; exploit'", "metasploit", 240.0, 0.65)
            ]
        else:  # POST_EXPLOITATION
            commands = [
                ("whoami", "system", 5.0, 0.99),
                ("ls -la", "system", 5.0, 0.99),
                ("cat /etc/passwd", "system", 5.0, 0.95)
            ]
        
        for i, (cmd, tool, time, prob) in enumerate(commands[:3]):
            cmd = cmd.replace("{target}", context.target)
            complexity = self._estimate_command_complexity(cmd, tool)
            
            suggestion = CommandSuggestion(
                command=cmd,
                tool=tool,
                phase=context.current_phase,
                complexity=complexity,
                estimated_time=time,
                success_probability=prob,
                rationale=f"后备建议 {i+1}: 基于{context.current_phase.value}阶段的通用命令",
                risk_level=self._determine_risk_level(cmd, complexity)
            )
            
            suggestions.append(suggestion)
        
        return suggestions
    
    def get_planner_info(self) -> Dict[str, Any]:
        """获取Planner信息"""
        return {
            "planner_type": "LLMHackSynthPlanner",
            "llm_provider": self.llm_config.get("provider", "unknown"),
            "llm_model": self.llm_config.get("model", "unknown"),
            "learning_enabled": self.learning_enabled,
            "tool_count": len(self.tool_effectiveness),
            "planning_history_count": len(self.planning_history),
            "config": {
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
        }

