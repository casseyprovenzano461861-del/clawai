# -*- coding: utf-8 -*-
"""
上下文缺口分析器
智能判断当前上下文与任务需求的差距，自动补充数据
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class GapType(Enum):
    """缺口类型"""
    TARGET_INFO = "target_info"           # 缺少目标基本信息
    PORT_INFO = "port_info"               # 缺少端口信息
    SERVICE_INFO = "service_info"         # 缺少服务信息
    WEB_INFO = "web_info"                 # 缺少Web信息
    VULN_INFO = "vuln_info"              # 缺少漏洞信息
    CREDENTIAL = "credential"            # 缺少凭证信息
    EXPLOIT_INFO = "exploit_info"        # 缺少利用信息
    NONE = "none"                        # 无缺口


@dataclass
class ContextGap:
    """上下文缺口"""
    gap_type: GapType
    description: str
    suggested_tools: List[str]
    priority: int  # 1-5，1最高
    reason: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "gap_type": self.gap_type.value,
            "description": self.description,
            "suggested_tools": self.suggested_tools,
            "priority": self.priority,
            "reason": self.reason
        }


@dataclass
class GapAnalysisResult:
    """缺口分析结果"""
    has_gaps: bool
    gaps: List[ContextGap]
    recommended_actions: List[Dict[str, Any]]
    confidence: float
    summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_gaps": self.has_gaps,
            "gaps": [g.to_dict() for g in self.gaps],
            "recommended_actions": self.recommended_actions,
            "confidence": self.confidence,
            "summary": self.summary
        }


class ContextGapAnalyzer:
    """上下文缺口分析器
    
    功能：
    1. 分析当前上下文与任务需求的差距
    2. 判断是否需要运行工具补充数据
    3. 智能建议下一步操作
    """
    
    # 目标类型所需的最小信息
    MINIMUM_INFO_REQUIREMENTS = {
        "web_application": ["open_ports", "web_info"],
        "network": ["open_ports", "service_info"],
        "domain": ["dns_info", "subdomains"],
        "ip_address": ["open_ports", "service_info"],
        "unknown": ["open_ports"]
    }
    
    # 缺口类型到工具的映射
    GAP_TO_TOOLS = {
        GapType.TARGET_INFO: ["nmap_scan", "whatweb_scan"],
        GapType.PORT_INFO: ["nmap_scan"],
        GapType.SERVICE_INFO: ["nmap_scan"],
        GapType.WEB_INFO: ["whatweb_scan", "nuclei_scan", "dirsearch_scan"],
        GapType.VULN_INFO: ["nuclei_scan", "sqlmap_scan", "nikto_scan"],
        GapType.CREDENTIAL: ["hydra_brute"],
        GapType.EXPLOIT_INFO: ["searchsploit", "msfconsole"],
    }
    
    # 判断是否有足够信息的阈值
    INFO_THRESHOLDS = {
        "min_ports": 1,         # 至少发现1个开放端口
        "min_services": 0,      # 服务信息
        "min_findings": 0,      # 发现数量
    }
    
    def __init__(self, llm_client=None):
        """初始化缺口分析器
        
        Args:
            llm_client: LLM客户端（用于AI增强分析）
        """
        self.llm_client = llm_client
    
    def analyze(
        self,
        user_input: str,
        context: Dict[str, Any],
        task_phase: str = "unknown"
    ) -> GapAnalysisResult:
        """分析上下文缺口
        
        Args:
            user_input: 用户输入
            context: 当前上下文
            task_phase: 当前任务阶段
            
        Returns:
            GapAnalysisResult: 分析结果
        """
        gaps = []
        
        # 1. 检查目标基本信息
        target = context.get("target", "")
        if not target:
            gaps.append(ContextGap(
                gap_type=GapType.TARGET_INFO,
                description="缺少目标地址",
                suggested_tools=[],
                priority=1,
                reason="无法执行任何操作，需要目标地址"
            ))
        
        # 2. 检查端口信息
        open_ports = context.get("open_ports", [])
        if target and len(open_ports) < self.INFO_THRESHOLDS["min_ports"]:
            gaps.append(ContextGap(
                gap_type=GapType.PORT_INFO,
                description=f"端口信息不足（当前{len(open_ports)}个开放端口）",
                suggested_tools=self.GAP_TO_TOOLS[GapType.PORT_INFO],
                priority=2,
                reason="需要了解目标的开放端口和服务"
            ))
        
        # 3. 检查Web信息（如果目标是Web应用）
        target_type = context.get("target_type", self._infer_target_type(target))
        if target_type == "web_application":
            web_info = context.get("scan_results", {}).get("whatweb", {})
            if not web_info:
                gaps.append(ContextGap(
                    gap_type=GapType.WEB_INFO,
                    description="缺少Web技术栈信息",
                    suggested_tools=self.GAP_TO_TOOLS[GapType.WEB_INFO],
                    priority=2,
                    reason="需要了解目标的Web技术栈"
                ))
        
        # 4. 检查漏洞信息（根据任务阶段）
        if task_phase in ["vuln_scan", "exploitation"]:
            vulnerabilities = context.get("vulnerabilities", [])
            if len(vulnerabilities) == 0:
                gaps.append(ContextGap(
                    gap_type=GapType.VULN_INFO,
                    description="未发现漏洞",
                    suggested_tools=self.GAP_TO_TOOLS[GapType.VULN_INFO],
                    priority=3,
                    reason="需要执行漏洞扫描"
                ))
        
        # 5. 检查是否需要凭证
        if task_phase == "exploitation":
            credentials = context.get("credentials", [])
            if not credentials and "brute" in user_input.lower():
                gaps.append(ContextGap(
                    gap_type=GapType.CREDENTIAL,
                    description="缺少有效凭证",
                    suggested_tools=self.GAP_TO_TOOLS[GapType.CREDENTIAL],
                    priority=4,
                    reason="暴力破解可能需要更多尝试"
                ))
        
        # 6. 生成推荐操作
        recommended_actions = self._generate_recommendations(gaps)
        
        # 7. 计算置信度
        confidence = 1.0 - (len(gaps) * 0.15)  # 每个缺口降低15%置信度
        confidence = max(0.1, min(1.0, confidence))
        
        # 8. 生成摘要
        summary = self._generate_summary(gaps, context)
        
        return GapAnalysisResult(
            has_gaps=len(gaps) > 0,
            gaps=gaps,
            recommended_actions=recommended_actions,
            confidence=confidence,
            summary=summary
        )
    
    def needs_more_info(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """快速判断是否需要更多信息
        
        Args:
            user_input: 用户输入
            context: 当前上下文
            
        Returns:
            Tuple[bool, List[str]]: (是否需要更多信息, 建议的工具列表)
        """
        result = self.analyze(user_input, context)
        
        if not result.has_gaps:
            return False, []
        
        # 只返回高优先级的缺口
        high_priority_gaps = [g for g in result.gaps if g.priority <= 2]
        
        if not high_priority_gaps:
            return False, []
        
        suggested_tools = []
        for gap in high_priority_gaps:
            suggested_tools.extend(gap.suggested_tools)
        
        return True, list(set(suggested_tools))
    
    def get_recommended_next_action(
        self,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """获取推荐的下一步操作
        
        Args:
            context: 当前上下文
            
        Returns:
            Optional[Dict]: 推荐操作，如果不需要则返回None
        """
        target = context.get("target", "")
        if not target:
            return None
        
        # 基于当前状态推荐
        open_ports = context.get("open_ports", [])
        vulnerabilities = context.get("vulnerabilities", [])
        
        if len(open_ports) == 0:
            return {
                "tool": "nmap_scan",
                "params": {"target": target, "scan_type": "quick"},
                "reason": "需要先了解目标的开放端口"
            }
        
        if len(vulnerabilities) == 0:
            return {
                "tool": "nuclei_scan",
                "params": {"target": f"http://{target}"},
                "reason": "端口已知，建议进行漏洞扫描"
            }
        
        return None
    
    def _infer_target_type(self, target: str) -> str:
        """推断目标类型"""
        if not target:
            return "unknown"
        
        target = target.lower()
        
        if target.startswith("http://") or target.startswith("https://"):
            return "web_application"
        elif ":" in target:
            return "network"
        elif re.match(r'^\d+\.\d+\.\d+\.\d+$', target):
            return "ip_address"
        else:
            return "domain"
    
    def _generate_recommendations(
        self,
        gaps: List[ContextGap]
    ) -> List[Dict[str, Any]]:
        """生成推荐操作"""
        recommendations = []
        
        for gap in sorted(gaps, key=lambda x: x.priority):
            for tool in gap.suggested_tools[:2]:  # 每个缺口最多推荐2个工具
                recommendations.append({
                    "tool": tool,
                    "reason": gap.reason,
                    "priority": gap.priority
                })
        
        return recommendations
    
    def _generate_summary(
        self,
        gaps: List[ContextGap],
        context: Dict[str, Any]
    ) -> str:
        """生成分析摘要"""
        if not gaps:
            return "当前上下文信息充足，可以继续执行任务。"
        
        gap_descriptions = [f"{g.description}（优先级：{g.priority}）" for g in gaps[:3]]
        
        summary = f"发现 {len(gaps)} 个信息缺口：\n"
        summary += "\n".join(f"- {d}" for d in gap_descriptions)
        
        if len(gaps) > 3:
            summary += f"\n- ...还有 {len(gaps) - 3} 个缺口"
        
        return summary


# ==================== 便捷函数 ====================

def analyze_context_gaps(
    user_input: str,
    context: Dict[str, Any],
    task_phase: str = "unknown"
) -> GapAnalysisResult:
    """分析上下文缺口
    
    Args:
        user_input: 用户输入
        context: 当前上下文
        task_phase: 当前任务阶段
        
    Returns:
        GapAnalysisResult: 分析结果
    """
    analyzer = ContextGapAnalyzer()
    return analyzer.analyze(user_input, context, task_phase)


# ==================== 测试 ====================

def test_context_gap_analyzer():
    """测试上下文缺口分析器"""
    print("=" * 60)
    print("上下文缺口分析器测试")
    print("=" * 60)
    
    analyzer = ContextGapAnalyzer()
    
    # 测试1: 空上下文
    print("\n1. 空上下文测试:")
    result = analyzer.analyze("扫描目标", {})
    print(f"  有缺口: {result.has_gaps}")
    print(f"  缺口数: {len(result.gaps)}")
    print(f"  摘要: {result.summary[:100]}...")
    
    # 测试2: 部分信息
    print("\n2. 部分信息测试:")
    context = {
        "target": "example.com",
        "open_ports": [{"port": 80, "service": "http"}]
    }
    result = analyzer.analyze("扫描目标", context)
    print(f"  有缺口: {result.has_gaps}")
    print(f"  推荐操作: {len(result.recommended_actions)}")
    
    # 测试3: 完整信息
    print("\n3. 完整信息测试:")
    context = {
        "target": "example.com",
        "open_ports": [{"port": 80, "service": "http"}],
        "scan_results": {"whatweb": {"technologies": ["nginx"]}},
        "vulnerabilities": [{"type": "XSS", "severity": "medium"}]
    }
    result = analyzer.analyze("分析漏洞", context, task_phase="analysis")
    print(f"  有缺口: {result.has_gaps}")
    print(f"  置信度: {result.confidence:.2f}")
    
    # 测试4: 快速判断
    print("\n4. 快速判断测试:")
    needs, tools = analyzer.needs_more_info("扫描目标", {"target": "example.com"})
    print(f"  需要更多信息: {needs}")
    print(f"  建议工具: {tools}")
    
    print("\n" + "=" * 60)
    print("测试完成")


if __name__ == "__main__":
    test_context_gap_analyzer()
