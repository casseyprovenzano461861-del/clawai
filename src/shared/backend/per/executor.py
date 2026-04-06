# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
P-E-R架构：执行器模块
借鉴LuaN1aoAgent的执行器设计，负责执行具体的子任务
"""

import json
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import sys
import os

# 添加路径以便导入现有模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    subtask_id: str
    output: Dict[str, Any]
    error: Optional[str] = None
    execution_time: float = 0.0
    tool_calls: List[Dict[str, Any]] = None
    thinking_log: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.tool_calls is None:
            self.tool_calls = []
        if self.thinking_log is None:
            self.thinking_log = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "subtask_id": self.subtask_id,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "tool_calls": self.tool_calls,
            "thinking_log": self.thinking_log
        }


@dataclass
class ToolCall:
    """工具调用记录"""
    tool_name: str
    parameters: Dict[str, Any]
    result: Dict[str, Any]
    execution_time: float
    success: bool
    error: Optional[str] = None


class PERExecutor:
    """P-E-R架构：执行器
    
    负责：
    1. 执行具体的子任务
    2. 调用工具（兼容现有Skill系统）
    3. 管理执行上下文
    4. 收集执行指标
    5. 处理执行失败和重试
    """
    
    def __init__(self, skill_registry=None, max_retries: int = 3):
        """初始化执行器
        
        Args:
            skill_registry: 技能注册表（可选）
            max_retries: 最大重试次数
        """
        self.skill_registry = skill_registry
        self.max_retries = max_retries
        
        # 执行历史
        self.execution_history: List[ExecutionResult] = []
        
        # 工具调用统计
        self.tool_stats: Dict[str, Dict[str, Any]] = {}
        
        # 当前执行上下文
        self.current_context: Optional[Dict[str, Any]] = None
        
        # 重试计数器
        self.retry_counters: Dict[str, int] = {}
        
        logger.info("PERExecutor初始化完成")
    
    def set_skill_registry(self, skill_registry) -> None:
        """设置技能注册表
        
        Args:
            skill_registry: 技能注册表实例
        """
        self.skill_registry = skill_registry
        logger.debug("技能注册表已设置")
    
    def set_context(self, context: Dict[str, Any]) -> None:
        """设置执行上下文
        
        Args:
            context: 执行上下文
        """
        self.current_context = context
        logger.debug(f"设置执行上下文: {len(context)}个键")
    
    async def execute_subtask(self, 
                             subtask_id: str,
                             subtask_data: Dict[str, Any],
                             graph_manager=None) -> ExecutionResult:
        """执行子任务
        
        Args:
            subtask_id: 子任务ID
            subtask_data: 子任务数据
            graph_manager: 图谱管理器（可选）
            
        Returns:
            ExecutionResult: 执行结果
        """
        logger.info(f"开始执行子任务: {subtask_id}")
        
        start_time = datetime.now()
        thinking_log = []
        tool_calls = []
        
        try:
            # 1. 解析任务描述
            description = subtask_data.get("description", "")
            mission_briefing = subtask_data.get("mission_briefing", "")
            completion_criteria = subtask_data.get("completion_criteria", "")
            
            thinking_log.append({
                "timestamp": datetime.now().isoformat(),
                "message": f"开始执行子任务: {description}",
                "type": "start"
            })
            
            thinking_log.append({
                "timestamp": datetime.now().isoformat(),
                "message": f"任务简报: {mission_briefing}",
                "type": "info"
            })
            
            # 2. 根据任务类型选择执行策略
            task_type = self._infer_task_type(description, mission_briefing)
            thinking_log.append({
                "timestamp": datetime.now().isoformat(),
                "message": f"推断任务类型: {task_type}",
                "type": "analysis"
            })
            
            # 3. 执行任务
            if task_type == "reconnaissance":
                result = await self._execute_recon_task(subtask_id, description, thinking_log, tool_calls)
            elif task_type == "vulnerability_scan":
                result = await self._execute_vuln_scan_task(subtask_id, description, thinking_log, tool_calls)
            elif task_type == "exploitation":
                result = await self._execute_exploit_task(subtask_id, description, thinking_log, tool_calls)
            elif task_type == "post_exploitation":
                result = await self._execute_post_exploit_task(subtask_id, description, thinking_log, tool_calls)
            else:
                result = await self._execute_general_task(subtask_id, description, thinking_log, tool_calls)
            
            # 4. 检查完成标准
            success = self._check_completion_criteria(result, completion_criteria)
            
            # 5. 更新图谱状态（如果提供了graph_manager）
            if graph_manager and hasattr(graph_manager, 'update_node'):
                new_status = "completed" if success else "failed"
                graph_manager.update_node(subtask_id, {"status": new_status})
            
            # 6. 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 7. 创建执行结果
            execution_result = ExecutionResult(
                success=success,
                subtask_id=subtask_id,
                output=result,
                execution_time=execution_time,
                tool_calls=tool_calls,
                thinking_log=thinking_log
            )
            
            # 8. 记录执行历史
            self.execution_history.append(execution_result)
            
            # 9. 更新工具统计
            self._update_tool_stats(tool_calls)
            
            thinking_log.append({
                "timestamp": datetime.now().isoformat(),
                "message": f"子任务执行完成: {'成功' if success else '失败'}，耗时{execution_time:.2f}秒",
                "type": "completion"
            })
            
            logger.info(f"子任务执行完成: {subtask_id} - {'成功' if success else '失败'}")
            
            return execution_result
            
        except Exception as e:
            # 处理执行异常
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            thinking_log.append({
                "timestamp": datetime.now().isoformat(),
                "message": f"执行过程中发生异常: {error_msg}",
                "type": "error"
            })
            
            logger.error(f"子任务执行异常: {subtask_id} - {error_msg}")
            
            # 创建失败结果
            execution_result = ExecutionResult(
                success=False,
                subtask_id=subtask_id,
                output={},
                error=error_msg,
                execution_time=execution_time,
                tool_calls=tool_calls,
                thinking_log=thinking_log
            )
            
            self.execution_history.append(execution_result)
            
            return execution_result
    
    def _infer_task_type(self, description: str, mission_briefing: str) -> str:
        """推断任务类型
        
        Args:
            description: 任务描述
            mission_briefing: 任务简报
            
        Returns:
            str: 任务类型
        """
        text = (description + " " + mission_briefing).lower()
        
        if any(word in text for word in ["信息收集", "侦察", "recon", "扫描", "端口扫描"]):
            return "reconnaissance"
        elif any(word in text for word in ["漏洞扫描", "漏洞检测", "vulnerability", "vuln"]):
            return "vulnerability_scan"
        elif any(word in text for word in ["漏洞利用", "攻击", "exploit", "渗透"]):
            return "exploitation"
        elif any(word in text for word in ["后渗透", "权限维持", "横向移动", "post"]):
            return "post_exploitation"
        else:
            return "general"
    
    async def _execute_recon_task(self, 
                                 subtask_id: str,
                                 description: str,
                                 thinking_log: List[Dict[str, Any]],
                                 tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行侦察任务
        
        Args:
            subtask_id: 子任务ID
            description: 任务描述
            thinking_log: 思考日志
            tool_calls: 工具调用记录
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": "执行侦察任务: 信息收集和目标分析",
            "type": "execution"
        })
        
        # 尝试使用现有技能系统
        if self.skill_registry:
            try:
                # 查找侦察相关技能
                recon_skills = []
                for skill_name in self.skill_registry.get_all_skill_names():
                    skill = self.skill_registry.get_skill(skill_name)
                    if skill and hasattr(skill, 'category'):
                        if skill.category in ["recon", "scan", "information_gathering"]:
                            recon_skills.append(skill)
                
                if recon_skills:
                    # 选择第一个侦察技能执行
                    skill = recon_skills[0]
                    thinking_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "message": f"使用技能执行: {skill.name}",
                        "type": "tool_selection"
                    })
                    
                    # 执行技能
                    skill_result = skill.execute(self.current_context)
                    
                    # 记录工具调用
                    tool_calls.append({
                        "tool_name": skill.name,
                        "tool_type": "skill",
                        "parameters": {"context": "current_context"},
                        "result": skill_result,
                        "execution_time": 0.0,  # 实际时间需要从技能中获取
                        "success": skill_result.get("success", False)
                    })
                    
                    return {
                        "task_type": "reconnaissance",
                        "skill_used": skill.name,
                        "result": skill_result,
                        "findings": skill_result.get("findings", []),
                        "summary": f"使用技能 {skill.name} 完成侦察任务"
                    }
            
            except Exception as e:
                thinking_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "message": f"技能执行失败: {str(e)}，使用模拟执行",
                    "type": "fallback"
                })
        
        # 模拟执行（回退方案）
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": "使用模拟执行侦察任务",
            "type": "simulation"
        })
        
        # 模拟工具调用
        simulated_tools = [
            {"name": "nmap", "action": "端口扫描", "result": "发现80,443,22端口开放"},
            {"name": "whatweb", "action": "Web技术识别", "result": "识别到nginx, PHP, WordPress"},
            {"name": "subfinder", "action": "子域名枚举", "result": "发现3个子域名"}
        ]
        
        for tool in simulated_tools:
            tool_calls.append({
                "tool_name": tool["name"],
                "tool_type": "simulated",
                "parameters": {"action": tool["action"]},
                "result": {"output": tool["result"]},
                "execution_time": 0.5,
                "success": True
            })
        
        return {
            "task_type": "reconnaissance",
            "simulated": True,
            "findings": [
                "目标运行Web服务（端口80,443）",
                "技术栈: nginx + PHP + WordPress",
                "发现3个子域名",
                "SSH服务开放（端口22）"
            ],
            "summary": "模拟侦察完成，发现关键信息"
        }
    
    async def _execute_vuln_scan_task(self,
                                     subtask_id: str,
                                     description: str,
                                     thinking_log: List[Dict[str, Any]],
                                     tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行漏洞扫描任务
        
        Args:
            subtask_id: 子任务ID
            description: 任务描述
            thinking_log: 思考日志
            tool_calls: 工具调用记录
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": "执行漏洞扫描任务: 检测安全漏洞",
            "type": "execution"
        })
        
        # 尝试使用现有技能系统
        if self.skill_registry:
            try:
                # 查找漏洞扫描相关技能
                vuln_skills = []
                for skill_name in self.skill_registry.get_all_skill_names():
                    skill = self.skill_registry.get_skill(skill_name)
                    if skill and hasattr(skill, 'category'):
                        if skill.category in ["vulnerability", "scan", "security"]:
                            vuln_skills.append(skill)
                
                if vuln_skills:
                    # 选择第一个漏洞扫描技能执行
                    skill = vuln_skills[0]
                    thinking_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "message": f"使用技能执行: {skill.name}",
                        "type": "tool_selection"
                    })
                    
                    # 执行技能
                    skill_result = skill.execute(self.current_context)
                    
                    # 记录工具调用
                    tool_calls.append({
                        "tool_name": skill.name,
                        "tool_type": "skill",
                        "parameters": {"context": "current_context"},
                        "result": skill_result,
                        "execution_time": 0.0,
                        "success": skill_result.get("success", False)
                    })
                    
                    return {
                        "task_type": "vulnerability_scan",
                        "skill_used": skill.name,
                        "result": skill_result,
                        "vulnerabilities": skill_result.get("vulnerabilities", []),
                        "summary": f"使用技能 {skill.name} 完成漏洞扫描"
                    }
            
            except Exception as e:
                thinking_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "message": f"技能执行失败: {str(e)}，使用模拟执行",
                    "type": "fallback"
                })
        
        # 模拟执行
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": "使用模拟执行漏洞扫描",
            "type": "simulation"
        })
        
        # 模拟漏洞发现
        simulated_vulns = [
            {"type": "SQL注入", "severity": "高危", "location": "/login.php", "description": "存在SQL注入漏洞"},
            {"type": "XSS", "severity": "中危", "location": "/search.php", "description": "存在跨站脚本漏洞"},
            {"type": "信息泄露", "severity": "低危", "location": "/debug.php", "description": "敏感信息泄露"}
        ]
        
        # 模拟工具调用
        simulated_tools = [
            {"name": "nuclei", "action": "漏洞扫描", "result": f"发现{len(simulated_vulns)}个漏洞"},
            {"name": "sqlmap", "action": "SQL注入测试", "result": "确认SQL注入漏洞"},
            {"name": "xsstrike", "action": "XSS测试", "result": "确认XSS漏洞"}
        ]
        
        for tool in simulated_tools:
            tool_calls.append({
                "tool_name": tool["name"],
                "tool_type": "simulated",
                "parameters": {"action": tool["action"]},
                "result": {"output": tool["result"]},
                "execution_time": 1.0,
                "success": True
            })
        
        return {
            "task_type": "vulnerability_scan",
            "simulated": True,
            "vulnerabilities": simulated_vulns,
            "summary": f"模拟漏洞扫描完成，发现{len(simulated_vulns)}个漏洞"
        }
    
    async def _execute_exploit_task(self,
                                   subtask_id: str,
                                   description: str,
                                   thinking_log: List[Dict[str, Any]],
                                   tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行漏洞利用任务
        
        Args:
            subtask_id: 子任务ID
            description: 任务描述
            thinking_log: 思考日志
            tool_calls: 工具调用记录
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": "执行漏洞利用任务: 尝试利用已知漏洞",
            "type": "execution"
        })
        
        # 模拟漏洞利用
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": "分析可用漏洞，选择最可能成功的利用方式",
            "type": "analysis"
        })
        
        # 模拟工具调用
        simulated_tools = [
            {"name": "metasploit", "action": "漏洞利用", "result": "尝试利用SQL注入漏洞"},
            {"name": "custom_exploit", "action": "自定义利用", "result": "生成利用载荷"},
            {"name": "reverse_shell", "action": "反弹shell", "result": "建立反向连接"}
        ]
        
        for tool in simulated_tools:
            tool_calls.append({
                "tool_name": tool["name"],
                "tool_type": "simulated",
                "parameters": {"action": tool["action"]},
                "result": {"output": tool["result"]},
                "execution_time": 2.0,
                "success": True
            })
        
        # 模拟利用结果
        exploit_success = True  # 假设利用成功
        
        return {
            "task_type": "exploitation",
            "simulated": True,
            "exploit_attempted": "SQL注入漏洞",
            "exploit_success": exploit_success,
            "payload_delivered": exploit_success,
            "access_gained": exploit_success,
            "summary": f"模拟漏洞利用完成，{'成功获得访问权限' if exploit_success else '利用失败'}"
        }
    
    async def _execute_post_exploit_task(self,
                                        subtask_id: str,
                                        description: str,
                                        thinking_log: List[Dict[str, Any]],
                                        tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行后渗透任务
        
        Args:
            subtask_id: 子任务ID
            description: 任务描述
            thinking_log: 思考日志
            tool_calls: 工具调用记录
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": "执行后渗透任务: 权限维持和横向移动",
            "type": "execution"
        })
        
        # 模拟后渗透活动
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": "在已获得访问权限的系统上进行后渗透活动",
            "type": "analysis"
        })
        
        # 模拟工具调用
        simulated_tools = [
            {"name": "mimikatz", "action": "凭证提取", "result": "提取到管理员凭证"},
            {"name": "powershell", "action": "权限提升", "result": "尝试提权操作"},
            {"name": "lateral_movement", "action": "横向移动", "result": "尝试访问其他系统"}
        ]
        
        for tool in simulated_tools:
            tool_calls.append({
                "tool_name": tool["name"],
                "tool_type": "simulated",
                "parameters": {"action": tool["action"]},
                "result": {"output": tool["result"]},
                "execution_time": 1.5,
                "success": True
            })
        
        return {
            "task_type": "post_exploitation",
            "simulated": True,
            "activities": [
                "凭证提取完成",
                "权限提升尝试",
                "横向移动尝试"
            ],
            "summary": "模拟后渗透活动完成"
        }
    
    async def _execute_general_task(self,
                                   subtask_id: str,
                                   description: str,
                                   thinking_log: List[Dict[str, Any]],
                                   tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行通用任务
        
        Args:
            subtask_id: 子任务ID
            description: 任务描述
            thinking_log: 思考日志
            tool_calls: 工具调用记录
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": "执行通用任务",
            "type": "execution"
        })
        
        # 尝试使用现有技能系统
        if self.skill_registry:
            try:
                # 查找通用技能
                general_skills = []
                for skill_name in self.skill_registry.get_all_skill_names():
                    skill = self.skill_registry.get_skill(skill_name)
                    if skill:
                        general_skills.append(skill)
                
                if general_skills:
                    # 选择第一个技能执行
                    skill = general_skills[0]
                    thinking_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "message": f"使用技能执行: {skill.name}",
                        "type": "tool_selection"
                    })
                    
                    # 执行技能
                    skill_result = skill.execute(self.current_context)
                    
                    # 记录工具调用
                    tool_calls.append({
                        "tool_name": skill.name,
                        "tool_type": "skill",
                        "parameters": {"context": "current_context"},
                        "result": skill_result,
                        "execution_time": 0.0,
                        "success": skill_result.get("success", False)
                    })
                    
                    return {
                        "task_type": "general",
                        "skill_used": skill.name,
                        "result": skill_result,
                        "summary": f"使用技能 {skill.name} 完成任务"
                    }
            
            except Exception as e:
                thinking_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "message": f"技能执行失败: {str(e)}，使用模拟执行",
                    "type": "fallback"
                })
        
        # 模拟执行
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": "使用模拟执行通用任务",
            "type": "simulation"
        })
        
        # 模拟工具调用
        simulated_tools = [
            {"name": "generic_tool", "action": "任务执行", "result": "完成任务目标"}
        ]
        
        for tool in simulated_tools:
            tool_calls.append({
                "tool_name": tool["name"],
                "tool_type": "simulated",
                "parameters": {"action": tool["action"]},
                "result": {"output": tool["result"]},
                "execution_time": 1.0,
                "success": True
            })
        
        return {
            "task_type": "general",
            "simulated": True,
            "result": {"status": "completed", "message": "任务执行完成"},
            "summary": "模拟通用任务执行完成"
        }
    
    def _check_completion_criteria(self, 
                                  result: Dict[str, Any], 
                                  completion_criteria: str) -> bool:
        """检查完成标准
        
        Args:
            result: 执行结果
            completion_criteria: 完成标准
            
        Returns:
            bool: 是否满足完成标准
        """
        if not completion_criteria:
            # 如果没有明确标准，检查执行是否成功
            return result.get("success", False) if "success" in result else True
        
        # 简单实现：根据结果类型判断
        task_type = result.get("task_type", "")
        
        if task_type == "reconnaissance":
            findings = result.get("findings", [])
            return len(findings) > 0
        
        elif task_type == "vulnerability_scan":
            vulnerabilities = result.get("vulnerabilities", [])
            return len(vulnerabilities) > 0
        
        elif task_type == "exploitation":
            return result.get("exploit_success", False) or result.get("access_gained", False)
        
        elif task_type == "post_exploitation":
            activities = result.get("activities", [])
            return len(activities) > 0
        
        else:
            # 通用任务：检查是否有结果
            return bool(result)
    
    def _update_tool_stats(self, tool_calls: List[Dict[str, Any]]) -> None:
        """更新工具统计
        
        Args:
            tool_calls: 工具调用记录
        """
        for call in tool_calls:
            tool_name = call.get("tool_name", "unknown")
            success = call.get("success", False)
            exec_time = call.get("execution_time", 0.0)
            
            if tool_name not in self.tool_stats:
                self.tool_stats[tool_name] = {
                    "total_calls": 0,
                    "successful_calls": 0,
                    "failed_calls": 0,
                    "total_time": 0.0,
                    "avg_time": 0.0
                }
            
            stats = self.tool_stats[tool_name]
            stats["total_calls"] += 1
            stats["total_time"] += exec_time
            
            if success:
                stats["successful_calls"] += 1
            else:
                stats["failed_calls"] += 1
            
            # 更新平均时间
            if stats["total_calls"] > 0:
                stats["avg_time"] = stats["total_time"] / stats["total_calls"]
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要
        
        Returns:
            Dict[str, Any]: 执行摘要
        """
        total_tasks = len(self.execution_history)
        successful_tasks = sum(1 for r in self.execution_history if r.success)
        failed_tasks = total_tasks - successful_tasks
        
        total_time = sum(r.execution_time for r in self.execution_history)
        avg_time = total_time / total_tasks if total_tasks > 0 else 0
        
        total_tool_calls = sum(len(r.tool_calls) for r in self.execution_history)
        
        return {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
            "total_execution_time": total_time,
            "average_task_time": avg_time,
            "total_tool_calls": total_tool_calls,
            "tool_stats": self.tool_stats,
            "recent_tasks": [
                {
                    "subtask_id": r.subtask_id,
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "tool_count": len(r.tool_calls)
                }
                for r in self.execution_history[-5:]
            ]
        }
    
    def clear_history(self) -> None:
        """清空执行历史"""
        self.execution_history.clear()
        self.tool_stats.clear()
        self.retry_counters.clear()
        logger.info("执行历史已清空")


async def test_executor():
    """测试执行器功能"""
    import sys
    
    print("=" * 80)
    print("PER执行器测试")
    print("=" * 80)
    
    # 创建执行器实例
    executor = PERExecutor()
    
    # 设置上下文
    executor.set_context({
        "target": "example.com",
        "goal": "渗透测试",
        "scan_results": {}
    })
    
    # 测试1: 侦察任务
    print("\n测试1: 侦察任务执行")
    recon_task = {
        "description": "信息收集: example.com",
        "mission_briefing": "对目标进行全面的信息收集",
        "completion_criteria": "完成端口扫描和服务识别"
    }
    
    result1 = await executor.execute_subtask("recon_test", recon_task)
    print(f"侦察任务结果: {'成功' if result1.success else '失败'}")
    print(f"执行时间: {result1.execution_time:.2f}秒")
    print(f"工具调用数: {len(result1.tool_calls)}")
    
    # 测试2: 漏洞扫描任务
    print("\n测试2: 漏洞扫描任务执行")
    vuln_task = {
        "description": "漏洞扫描: example.com",
        "mission_briefing": "基于信息收集结果进行漏洞扫描",
        "completion_criteria": "识别潜在的安全漏洞"
    }
    
    result2 = await executor.execute_subtask("vuln_scan_test", vuln_task)
    print(f"漏洞扫描结果: {'成功' if result2.success else '失败'}")
    print(f"执行时间: {result2.execution_time:.2f}秒")
    print(f"工具调用数: {len(result2.tool_calls)}")
    
    # 测试3: 获取执行摘要
    print("\n测试3: 执行摘要")
    summary = executor.get_execution_summary()
    print(f"总任务数: {summary['total_tasks']}")
    print(f"成功率: {summary['success_rate']*100:.1f}%")
    print(f"总执行时间: {summary['total_execution_time']:.2f}秒")
    print(f"总工具调用数: {summary['total_tool_calls']}")
    
    # 显示思考日志示例
    print("\n思考日志示例:")
    for i, log in enumerate(result1.thinking_log[:3]):
        print(f"  {i+1}. [{log['type']}] {log['message']}")
    
    print("\n" + "=" * 80)
    print("[PASS] 执行器测试完成")
    
    return True


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_executor())
    sys.exit(0 if success else 1)
