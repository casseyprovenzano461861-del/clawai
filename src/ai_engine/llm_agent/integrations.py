"""
ClawAI LLM代理集成模块
将HackSynth风格代理与现有ClawAI系统集成
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional, Tuple
import asyncio

# 添加模块路径以导入现有ClawAI模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .pentest_agent import ClawAIPentestAgent
from .config_manager import LLMConfigManager

logger = logging.getLogger(__name__)


class LLMAgentIntegrator:
    """LLM代理集成器"""

    def __init__(
        self,
        config_manager: LLMConfigManager = None,
        tool_executor_url: str = "http://tool-executor:8082",
        skill_registry = None
    ):
        """
        初始化集成器

        Args:
            config_manager: 配置管理器实例
            tool_executor_url: 工具执行服务URL
            skill_registry: 技能注册表实例
        """
        self.config_manager = config_manager or LLMConfigManager()
        self.tool_executor_url = tool_executor_url
        self.skill_registry = skill_registry

        # 代理实例缓存
        self._agents = {}

        logger.info("LLM代理集成器初始化完成")

    def create_agent(
        self,
        config_name: str = "clawai_pentest_agent",
        custom_config: Dict[str, Any] = None
    ) -> ClawAIPentestAgent:
        """
        创建代理实例

        Args:
            config_name: 配置名称
            custom_config: 自定义配置（可选）

        Returns:
            ClawAIPentestAgent实例
        """
        # 生成缓存键
        cache_key = f"{config_name}_{hash(str(custom_config)) if custom_config else 'default'}"

        if cache_key in self._agents:
            logger.info(f"使用缓存的代理: {config_name}")
            return self._agents[cache_key]

        # 加载或创建配置
        if custom_config:
            config = custom_config
            # 验证配置
            errors = self.config_manager.validate_config(config)
            if errors:
                logger.warning(f"自定义配置验证失败: {errors}")
                # 使用默认配置作为后备
                config = self.config_manager.load_config(config_name)
        else:
            config = self.config_manager.load_config(config_name)

        # 创建代理
        agent = ClawAIPentestAgent(
            config=config,
            tool_executor_url=self.tool_executor_url,
            skill_registry=self.skill_registry
        )

        # 缓存代理
        self._agents[cache_key] = agent

        logger.info(f"创建新代理: {config_name}")
        return agent

    def list_available_configs(self) -> List[Dict[str, str]]:
        """列出可用配置"""
        config_names = self.config_manager.list_configs()
        configs = []

        for name in config_names:
            try:
                config = self.config_manager.load_config(name)
                configs.append({
                    "name": name,
                    "description": config.get("description", ""),
                    "llm_model": config.get("llm", {}).get("model_id", "unknown"),
                    "provider": config.get("llm", {}).get("provider", "unknown")
                })
            except Exception as e:
                logger.error(f"加载配置 {name} 失败: {e}")
                continue

        return configs

    async def run_pentest_workflow(
        self,
        target: str,
        config_name: str = "clawai_pentest_agent",
        initial_scan_results: Dict[str, Any] = None,
        available_skills: List[str] = None,
        max_iterations: int = None
    ) -> Dict[str, Any]:
        """
        运行完整的渗透测试工作流

        Args:
            target: 目标地址
            config_name: 代理配置名称
            initial_scan_results: 初始扫描结果
            available_skills: 可用技能列表
            max_iterations: 最大迭代次数

        Returns:
            工作流结果
        """
        logger.info(f"开始渗透测试工作流: {target}")

        # 创建代理
        agent = self.create_agent(config_name)

        # 获取可用技能列表
        if available_skills is None and self.skill_registry:
            try:
                skills = self.skill_registry.get_all_skills()
                available_skills = [skill.name for skill in skills]
                logger.info(f"从技能注册表获取 {len(available_skills)} 个技能")
            except Exception as e:
                logger.error(f"获取技能列表失败: {e}")
                available_skills = ["nmap", "whatweb", "sqlmap", "nuclei"]

        # 运行计划-执行循环
        results = await agent.plan_and_execute(
            target=target,
            scan_results=initial_scan_results,
            available_skills=available_skills,
            max_iterations=max_iterations
        )

        # 添加元数据
        results["config_name"] = config_name
        results["agent_version"] = "1.0.0"
        results["available_skills"] = available_skills

        logger.info(f"渗透测试工作流完成: {target}, {len(results['iterations'])} 次迭代")
        return results

    async def analyze_target(
        self,
        target: str,
        config_name: str = "clawai_pentest_agent"
    ) -> Dict[str, Any]:
        """
        快速目标分析

        Args:
            target: 目标地址
            config_name: 代理配置名称

        Returns:
            分析结果
        """
        logger.info(f"目标分析: {target}")

        agent = self.create_agent(config_name)

        # 使用planner进行初步分析
        planner_output, input_tokens, output_tokens = agent.planner(
            target=target,
            scan_results={},
            available_skills=["nmap", "whatweb", "nuclei", "nikto"]
        )

        # 提取建议的命令
        command = agent.extract_command(planner_output)

        analysis = {
            "target": target,
            "analysis_timestamp": asyncio.get_event_loop().time(),
            "planner_analysis": planner_output,
            "suggested_command": command,
            "token_usage": {
                "input": input_tokens,
                "output": output_tokens
            },
            "recommendations": self._generate_recommendations(planner_output, command)
        }

        logger.info(f"目标分析完成: {target}")
        return analysis

    def _generate_recommendations(
        self,
        planner_output: str,
        suggested_command: str
    ) -> List[Dict[str, Any]]:
        """基于planner输出生成推荐"""
        recommendations = []

        # 分析planner输出中的关键词
        output_lower = planner_output.lower()

        if "nmap" in output_lower or "port" in output_lower or "scan" in output_lower:
            recommendations.append({
                "action": "port_scan",
                "priority": "high",
                "tool": "nmap",
                "reason": "建议进行端口扫描以识别开放端口和服务"
            })

        if "web" in output_lower or "http" in output_lower or "website" in output_lower:
            recommendations.append({
                "action": "web_fingerprinting",
                "priority": "high",
                "tool": "whatweb",
                "reason": "目标可能是Web应用，建议进行技术栈识别"
            })

        if "sql" in output_lower or "injection" in output_lower or "database" in output_lower:
            recommendations.append({
                "action": "sql_injection_test",
                "priority": "medium",
                "tool": "sqlmap",
                "reason": "可能存在SQL注入漏洞"
            })

        if "directory" in output_lower or "dir" in output_lower or "brute" in output_lower:
            recommendations.append({
                "action": "directory_bruteforce",
                "priority": "medium",
                "tool": "dirsearch",
                "reason": "建议进行目录暴力破解"
            })

        # 如果没有检测到特定模式，添加通用推荐
        if not recommendations:
            recommendations.extend([
                {
                    "action": "port_scan",
                    "priority": "high",
                    "tool": "nmap",
                    "reason": "基础端口扫描"
                },
                {
                    "action": "web_fingerprinting",
                    "priority": "medium",
                    "tool": "whatweb",
                    "reason": "技术栈识别"
                },
                {
                    "action": "vulnerability_scan",
                    "priority": "medium",
                    "tool": "nuclei",
                    "reason": "漏洞扫描"
                }
            ])

        return recommendations

    async def generate_attack_plan(
        self,
        target: str,
        scan_results: Dict[str, Any],
        config_name: str = "clawai_pentest_agent"
    ) -> Dict[str, Any]:
        """
        生成攻击计划

        Args:
            target: 目标地址
            scan_results: 扫描结果
            config_name: 代理配置名称

        Returns:
            攻击计划
        """
        logger.info(f"生成攻击计划: {target}")

        agent = self.create_agent(config_name)

        # 多次运行planner生成不同方案
        plans = []
        for i in range(3):  # 生成3个不同方案
            planner_output, input_tokens, output_tokens = agent.planner(
                target=target,
                scan_results=scan_results,
                available_skills=["nmap", "whatweb", "sqlmap", "nuclei", "nikto", "hydra"]
            )

            command = agent.extract_command(planner_output)

            plans.append({
                "plan_id": i + 1,
                "name": f"方案 {i + 1}",
                "planner_output": planner_output,
                "command": command,
                "tokens": {
                    "input": input_tokens,
                    "output": output_tokens
                },
                "complexity": self._estimate_complexity(planner_output, command),
                "estimated_time": self._estimate_time(planner_output, command)
            })

            # 重置代理状态以生成不同方案
            agent.reset()

        # 选择最佳方案（基于复杂性和估计时间）
        best_plan = self._select_best_plan(plans)

        attack_plan = {
            "target": target,
            "generated_at": asyncio.get_event_loop().time(),
            "available_plans": plans,
            "selected_plan": best_plan,
            "selection_criteria": {
                "complexity_weight": 0.4,
                "time_weight": 0.3,
                "completeness_weight": 0.3
            }
        }

        logger.info(f"攻击计划生成完成: {target}，选择方案 {best_plan['plan_id']}")
        return attack_plan

    def _estimate_complexity(self, planner_output: str, command: str) -> str:
        """估计方案复杂性"""
        if not command:
            return "unknown"

        command_lower = command.lower()

        if any(tool in command_lower for tool in ["sqlmap", "metasploit", "hydra", "exploit"]):
            return "high"
        elif any(tool in command_lower for tool in ["nmap", "nuclei", "nikto", "dirsearch"]):
            return "medium"
        else:
            return "low"

    def _estimate_time(self, planner_output: str, command: str) -> str:
        """估计执行时间"""
        if not command:
            return "unknown"

        command_lower = command.lower()

        if "comprehensive" in planner_output.lower() or "full" in planner_output.lower():
            return "30+ minutes"
        elif any(term in command_lower for term in ["-p-", "all ports", "complete"]):
            return "10-30 minutes"
        elif any(term in command_lower for term in ["-sS", "quick", "fast"]):
            return "1-5 minutes"
        else:
            return "5-10 minutes"

    def _select_best_plan(self, plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """选择最佳方案"""
        if not plans:
            return {}

        # 简单评分算法
        scored_plans = []
        for plan in plans:
            score = 0.0

            # 复杂性评分（中等复杂性最佳）
            complexity = plan.get("complexity", "unknown")
            if complexity == "medium":
                score += 0.4
            elif complexity == "high":
                score += 0.3
            elif complexity == "low":
                score += 0.2

            # 时间评分（较短时间更好）
            time_str = plan.get("estimated_time", "unknown")
            if "1-5" in time_str:
                score += 0.3
            elif "5-10" in time_str:
                score += 0.25
            elif "10-30" in time_str:
                score += 0.2
            elif "30+" in time_str:
                score += 0.1

            # 完整性评分（基于planner输出长度）
            planner_output = plan.get("planner_output", "")
            if len(planner_output) > 100:
                score += 0.3
            elif len(planner_output) > 50:
                score += 0.2
            else:
                score += 0.1

            plan["score"] = score
            scored_plans.append(plan)

        # 选择最高分
        scored_plans.sort(key=lambda x: x["score"], reverse=True)
        return scored_plans[0]

    def cleanup(self):
        """清理资源"""
        self._agents.clear()
        logger.info("LLM代理集成器资源已清理")


# 全局集成器实例（单例模式）
_integrator_instance = None


def get_integrator() -> LLMAgentIntegrator:
    """获取全局集成器实例"""
    global _integrator_instance
    if _integrator_instance is None:
        _integrator_instance = LLMAgentIntegrator()
    return _integrator_instance