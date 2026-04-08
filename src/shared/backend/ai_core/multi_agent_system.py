# -*- coding: utf-8 -*-
"""
多智能体协同系统
实现Lead Agent和Sub Agents的协同机制
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field

from src.shared.backend.core.tool_manager import ToolManager
from src.shared.backend.ai_core.llm_orchestrator import LLMOrchestrator
from src.shared.backend.skills.skill_library import SkillLibrary
from src.shared.backend.metrics.quantitative_metrics import QuantitativeMetricsCalculator


@dataclass
class AgentResult:
    """智能体执行结果"""
    success: bool
    data: Dict[str, Any]
    message: str = ""


class BaseAgent:
    """基础智能体类"""
    
    def __init__(self):
        self.tool_manager = ToolManager()
        self.llm_orchestrator = LLMOrchestrator()
        self.skill_library = SkillLibrary()
        self.metrics_calculator = QuantitativeMetricsCalculator()
    
    def execute(self, *args, **kwargs) -> AgentResult:
        """执行任务"""
        raise NotImplementedError


class LeadAgent(BaseAgent):
    """主导智能体，负责全局规划和协调"""
    
    def execute(self, target: str) -> AgentResult:
        """执行全局规划"""
        try:
            # 1. 分析目标
            target_analysis = self._analyze_target(target)
            
            # 2. 制定攻击策略
            attack_strategy = self._create_attack_strategy(target_analysis)
            
            # 3. 分配任务
            tasks = self._assign_tasks(attack_strategy)
            
            return AgentResult(
                success=True,
                data={
                    "target_analysis": target_analysis,
                    "attack_strategy": attack_strategy,
                    "tasks": tasks
                },
                message="全局规划完成"
            )
        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                message=f"全局规划失败: {str(e)}"
            )
    
    def _analyze_target(self, target: str) -> Dict[str, Any]:
        """分析目标"""
        # 使用LLM分析目标
        prompt = f"分析目标 {target}，包括可能的技术栈、漏洞类型和攻击面"
        analysis = self.llm_orchestrator.generate_response(prompt)
        
        return {
            "target": target,
            "analysis": analysis,
            "estimated_attack_surface": "中等"
        }
    
    def _create_attack_strategy(self, target_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """制定攻击策略"""
        # 使用LLM制定攻击策略
        prompt = f"基于目标分析 {target_analysis}，制定详细的攻击策略"
        strategy = self.llm_orchestrator.generate_response(prompt)
        
        return {
            "strategy": strategy,
            "phases": ["reconnaissance", "scanning", "exploitation", "post_exploitation", "reporting"]
        }
    
    def _assign_tasks(self, attack_strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分配任务"""
        tasks = []
        
        # 为每个阶段分配任务
        for phase in attack_strategy["phases"]:
            tasks.append({
                "phase": phase,
                "agent": self._get_agent_for_phase(phase),
                "description": self._get_task_description(phase)
            })
        
        return tasks
    
    def _get_agent_for_phase(self, phase: str) -> str:
        """根据阶段获取对应的智能体"""
        agent_map = {
            "reconnaissance": "ReconAgent",
            "scanning": "ScanAgent",
            "exploitation": "ExploitAgent",
            "post_exploitation": "ExploitAgent",
            "reporting": "ReportAgent"
        }
        return agent_map.get(phase, "ReconAgent")
    
    def _get_task_description(self, phase: str) -> str:
        """获取任务描述"""
        description_map = {
            "reconnaissance": "收集目标的基本信息，包括子域名、开放端口、技术栈等",
            "scanning": "扫描目标的漏洞和安全问题",
            "exploitation": "尝试利用发现的漏洞",
            "post_exploitation": "在成功利用漏洞后进行进一步操作",
            "reporting": "生成完整的安全测试报告"
        }
        return description_map.get(phase, "执行相关任务")


class ReconAgent(BaseAgent):
    """侦察智能体，负责信息收集"""
    
    def execute(self, target: str, lead_result: AgentResult) -> AgentResult:
        """执行侦察任务"""
        try:
            # 1. 执行信息收集工具
            tools = ["nmap", "subfinder", "whatweb"]
            results = {}
            
            for tool in tools:
                if tool == "nmap":
                    result = self.tool_manager.execute_tool_with_params(
                        "nmap",
                        {"target": target, "ports": "1-1000"}
                    )
                elif tool == "subfinder":
                    result = self.tool_manager.execute_tool_with_params(
                        "subfinder",
                        {"domain": target}
                    )
                elif tool == "whatweb":
                    result = self.tool_manager.execute_tool_with_params(
                        "whatweb",
                        {"target": f"https://{target}"}
                    )
                
                results[tool] = result
            
            # 2. 基于扫描结果推荐技能
            recommended_skills = self.skill_library.get_recommended_skills(results)
            
            # 3. 分析收集到的信息
            analysis = self._analyze_recon_results(results)
            
            return AgentResult(
                success=True,
                data={
                    "tool_results": results,
                    "analysis": analysis,
                    "recommended_skills": recommended_skills
                },
                message="侦察任务完成"
            )
        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                message=f"侦察任务失败: {str(e)}"
            )
    
    def _analyze_recon_results(self, results: Dict[str, str]) -> Dict[str, Any]:
        """分析侦察结果"""
        # 使用LLM分析侦察结果
        prompt = f"分析以下侦察结果，提取关键信息：{results}"
        analysis = self.llm_orchestrator.generate_response(prompt)
        
        return {
            "summary": analysis,
            "key_findings": ["开放端口", "子域名", "技术栈"]
        }


class ScanAgent(BaseAgent):
    """扫描智能体，负责漏洞扫描"""
    
    def execute(self, target: str, recon_result: AgentResult) -> AgentResult:
        """执行扫描任务"""
        try:
            # 1. 执行漏洞扫描工具
            tools = ["nuclei", "nikto", "sqlmap"]
            results = {}
            
            for tool in tools:
                if tool == "nuclei":
                    result = self.tool_manager.execute_tool_with_params(
                        "nuclei",
                        {"target": f"https://{target}"}
                    )
                elif tool == "nikto":
                    result = self.tool_manager.execute_tool_with_params(
                        "nikto",
                        {"target": f"https://{target}"}
                    )
                elif tool == "sqlmap":
                    result = self.tool_manager.execute_tool_with_params(
                        "sqlmap",
                        {"url": f"https://{target}"}
                    )
                
                results[tool] = result
            
            # 2. 分析扫描结果
            vulnerabilities = self._analyze_scan_results(results)
            
            # 3. 基于扫描结果推荐技能
            recommended_skills = self.skill_library.get_recommended_skills(results)
            
            return AgentResult(
                success=True,
                data={
                    "tool_results": results,
                    "vulnerabilities": vulnerabilities,
                    "recommended_skills": recommended_skills
                },
                message="扫描任务完成"
            )
        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                message=f"扫描任务失败: {str(e)}"
            )
    
    def _analyze_scan_results(self, results: Dict[str, str]) -> List[Dict[str, Any]]:
        """分析扫描结果"""
        # 使用LLM分析扫描结果
        prompt = f"从以下扫描结果中提取漏洞信息：{results}"
        analysis = self.llm_orchestrator.generate_response(prompt)
        
        # 模拟漏洞列表
        return [
            {
                "name": "SQL注入漏洞",
                "severity": "high",
                "description": "目标网站存在SQL注入漏洞",
                "tool": "sqlmap"
            },
            {
                "name": "XSS漏洞",
                "severity": "medium",
                "description": "目标网站存在XSS漏洞",
                "tool": "nuclei"
            }
        ]


class ExploitAgent(BaseAgent):
    """利用智能体，负责漏洞利用"""
    
    def execute(self, target: str, scan_result: AgentResult) -> AgentResult:
        """执行利用任务"""
        try:
            # 1. 获取漏洞信息
            vulnerabilities = scan_result.data.get("vulnerabilities", [])
            
            # 2. 尝试利用漏洞
            exploitation_results = {}
            
            for vuln in vulnerabilities:
                if vuln["severity"] in ["high", "critical"]:
                    # 模拟漏洞利用
                    exploitation_results[vuln["name"]] = {
                        "success": True,
                        "output": f"成功利用 {vuln['name']}"
                    }
                else:
                    exploitation_results[vuln["name"]] = {
                        "success": False,
                        "output": f"未尝试利用 {vuln['name']}"
                    }
            
            # 3. 分析利用结果
            analysis = self._analyze_exploitation_results(exploitation_results)
            
            return AgentResult(
                success=True,
                data={
                    "exploitation_results": exploitation_results,
                    "analysis": analysis
                },
                message="利用任务完成"
            )
        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                message=f"利用任务失败: {str(e)}"
            )
    
    def _analyze_exploitation_results(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """分析利用结果"""
        # 使用LLM分析利用结果
        prompt = f"分析以下漏洞利用结果：{results}"
        analysis = self.llm_orchestrator.generate_response(prompt)
        
        return {
            "summary": analysis,
            "successful_exploits": [name for name, result in results.items() if result["success"]]
        }


class ReportAgent(BaseAgent):
    """报告智能体，负责生成报告"""
    
    def execute(self, target: str, recon_result: AgentResult, scan_result: AgentResult, exploit_result: AgentResult) -> AgentResult:
        """执行报告生成任务"""
        try:
            # 1. 收集所有结果
            report_data = {
                "target": target,
                "reconnaissance": recon_result.data,
                "scanning": scan_result.data,
                "exploitation": exploit_result.data
            }
            
            # 2. 计算量化指标
            metrics = self.metrics_calculator.calculate_from_scan_results(scan_result.data.get("tool_results", {}))
            
            # 3. 生成报告
            report = self._generate_report(report_data, metrics)
            
            return AgentResult(
                success=True,
                data={
                    "report": report,
                    "report_data": report_data,
                    "metrics": metrics
                },
                message="报告生成完成"
            )
        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                message=f"报告生成失败: {str(e)}"
            )
    
    def _generate_report(self, report_data: Dict[str, Any], metrics: Dict[str, Any]) -> str:
        """生成报告"""
        # 使用LLM生成报告，包含量化指标
        prompt = f"基于以下渗透测试结果和量化指标生成详细的安全测试报告：\n\n渗透测试结果：{report_data}\n\n量化指标：{metrics}"
        report = self.llm_orchestrator.generate_response(prompt)
        
        return report


class MultiAgentSystem:
    """多智能体协同系统"""
    
    def __init__(self):
        self.lead_agent = LeadAgent()
        self.recon_agent = ReconAgent()
        self.scan_agent = ScanAgent()
        self.exploit_agent = ExploitAgent()
        self.report_agent = ReportAgent()
    
    def run_pentest(self, target: str) -> Dict[str, Any]:
        """运行渗透测试"""
        # 1. 全局规划
        lead_result = self.lead_agent.execute(target)
        if not lead_result.success:
            return {
                "success": False,
                "message": lead_result.message,
                "data": {}
            }
        
        # 2. 信息收集
        recon_result = self.recon_agent.execute(target, lead_result)
        if not recon_result.success:
            return {
                "success": False,
                "message": recon_result.message,
                "data": {
                    "lead_result": lead_result.data
                }
            }
        
        # 3. 漏洞扫描
        scan_result = self.scan_agent.execute(target, recon_result)
        if not scan_result.success:
            return {
                "success": False,
                "message": scan_result.message,
                "data": {
                    "lead_result": lead_result.data,
                    "recon_result": recon_result.data
                }
            }
        
        # 4. 漏洞利用
        exploit_result = self.exploit_agent.execute(target, scan_result)
        if not exploit_result.success:
            return {
                "success": False,
                "message": exploit_result.message,
                "data": {
                    "lead_result": lead_result.data,
                    "recon_result": recon_result.data,
                    "scan_result": scan_result.data
                }
            }
        
        # 5. 报告生成
        report_result = self.report_agent.execute(target, recon_result, scan_result, exploit_result)
        if not report_result.success:
            return {
                "success": False,
                "message": report_result.message,
                "data": {
                    "lead_result": lead_result.data,
                    "recon_result": recon_result.data,
                    "scan_result": scan_result.data,
                    "exploit_result": exploit_result.data
                }
            }
        
        return {
            "success": True,
            "message": "渗透测试完成",
            "data": {
                "lead_result": lead_result.data,
                "recon_result": recon_result.data,
                "scan_result": scan_result.data,
                "exploit_result": exploit_result.data,
                "report_result": report_result.data
            }
        }


# 测试代码
if __name__ == "__main__":
    # 初始化多智能体系统
    multi_agent_system = MultiAgentSystem()
    
    print("=" * 80)
    print("多智能体协同系统测试")
    print("=" * 80)
    
    # 测试渗透测试
    target = "example.com"
    print(f"开始对 {target} 进行渗透测试...")
    
    result = multi_agent_system.run_pentest(target)
    
    print(f"测试结果: {'成功' if result['success'] else '失败'}")
    print(f"消息: {result['message']}")
    
    if result['success']:
        print("\n渗透测试完成，生成了详细报告")
    
    print("\n" + "=" * 80)
    print("测试完成")
