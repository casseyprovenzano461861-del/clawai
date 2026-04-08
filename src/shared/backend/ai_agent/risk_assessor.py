# -*- coding: utf-8 -*-
"""
风险评估器
智能判断工具操作的风险等级，决定是否需要用户确认
"""

import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险等级枚举"""
    LOW = "low"              # 信息收集类，无需确认
    MEDIUM = "medium"        # 扫描类，可选确认
    HIGH = "high"            # 漏洞利用类，需要确认
    CRITICAL = "critical"    # 破坏性操作，必须确认
    
    def __str__(self):
        return self.value
    
    @property
    def emoji(self) -> str:
        """获取风险等级对应的表情符号"""
        emojis = {
            RiskLevel.LOW: "🟢",
            RiskLevel.MEDIUM: "🟡", 
            RiskLevel.HIGH: "🟠",
            RiskLevel.CRITICAL: "🔴"
        }
        return emojis.get(self, "⚪")


@dataclass
class RiskAssessment:
    """风险评估结果"""
    level: RiskLevel                          # 风险等级
    needs_confirmation: bool                  # 是否需要用户确认
    reason: str                               # 风险评估原因
    tool_name: str = ""                       # 工具名称
    params: Dict[str, Any] = field(default_factory=dict)  # 工具参数
    warnings: List[str] = field(default_factory=list)     # 警告信息
    recommendations: List[str] = field(default_factory=list)  # 建议
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "level": self.level.value,
            "needs_confirmation": self.needs_confirmation,
            "reason": self.reason,
            "tool_name": self.tool_name,
            "params": self.params,
            "warnings": self.warnings,
            "recommendations": self.recommendations
        }
    
    def get_confirmation_message(self) -> str:
        """生成确认消息"""
        if not self.needs_confirmation:
            return ""
        
        msg_parts = [
            f"{self.level.emoji} 风险警告",
            f"操作: {self.tool_name}",
            f"风险等级: {self.level.value.upper()}",
            f"原因: {self.reason}"
        ]
        
        if self.warnings:
            msg_parts.append("警告:")
            for warning in self.warnings:
                msg_parts.append(f"  - {warning}")
        
        msg_parts.append("\n是否确认执行此操作？(yes/no)")
        
        return "\n".join(msg_parts)


class RiskAssessor:
    """风险评估器
    
    智能判断工具操作的风险等级，决定是否需要用户确认。
    
    风险等级判定逻辑：
    1. 基础风险等级：根据工具类型预设
    2. 参数增强：检查参数中的危险标志
    3. 目标敏感度：检查目标是否为敏感目标
    4. 组合评估：综合以上因素得出最终风险等级
    """
    
    # 工具基础风险等级映射
    TOOL_RISK_LEVELS: Dict[str, RiskLevel] = {
        # 信息收集类 - 低风险
        "nmap_scan": RiskLevel.LOW,
        "whatweb_scan": RiskLevel.LOW,
        "subfinder_scan": RiskLevel.LOW,
        "httpx_probe": RiskLevel.LOW,
        "get_tool_status": RiskLevel.LOW,
        "get_pentest_status": RiskLevel.LOW,
        
        # 目录枚举类 - 中风险
        "dirsearch_scan": RiskLevel.MEDIUM,
        "gobuster_scan": RiskLevel.MEDIUM,
        "ffuf_scan": RiskLevel.MEDIUM,
        
        # 漏洞扫描类 - 中风险
        "nuclei_scan": RiskLevel.MEDIUM,
        "nikto_scan": RiskLevel.MEDIUM,
        "wpscan": RiskLevel.MEDIUM,
        "testssl_scan": RiskLevel.MEDIUM,
        
        # 漏洞检测类 - 高风险
        "sqlmap_scan": RiskLevel.HIGH,
        "xsstrike_scan": RiskLevel.HIGH,
        "hydra_brute": RiskLevel.HIGH,
        
        # 渗透测试流程
        "start_pentest": RiskLevel.HIGH,
        "stop_pentest": RiskLevel.LOW,
        
        # 报告生成
        "generate_report": RiskLevel.LOW,
    }
    
    # 危险参数标志
    DANGEROUS_FLAGS = [
        "--destructive",
        "--wipe",
        "--delete",
        "--drop",
        "--truncate",
        "--exec",
        "--os-shell",
        "--sql-shell",
        "--os-cmd",
        "--priv-esc",
        "--payload",
        "--reverse-shell",
    ]
    
    # 敏感目标模式
    SENSITIVE_TARGET_PATTERNS = [
        r'^127\.',                    # 本地回环
        r'^10\.',                     # 内网 10.0.0.0/8
        r'^172\.(1[6-9]|2[0-9]|3[0-1])\.',  # 内网 172.16.0.0/12
        r'^192\.168\.',               # 内网 192.168.0.0/16
        r'localhost',
        r'\.local$',
        r'\.internal$',
        r'\.corp$',
    ]
    
    # 高危端口
    HIGH_RISK_PORTS = [
        22,    # SSH
        23,    # Telnet
        3389,  # RDP
        5900,  # VNC
        5901,  # VNC
        445,   # SMB
        139,   # NetBIOS
        135,   # RPC
    ]
    
    def __init__(self, strict_mode: bool = False):
        """初始化风险评估器
        
        Args:
            strict_mode: 严格模式，开启后所有操作都需要确认
        """
        self.strict_mode = strict_mode
        logger.info(f"风险评估器初始化完成，严格模式: {strict_mode}")
    
    def assess(self, tool_name: str, params: Dict[str, Any]) -> RiskAssessment:
        """评估工具操作风险
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            
        Returns:
            RiskAssessment: 风险评估结果
        """
        # 1. 获取基础风险等级
        base_level = self.TOOL_RISK_LEVELS.get(tool_name, RiskLevel.MEDIUM)
        warnings = []
        recommendations = []
        
        # 2. 严格模式检查
        if self.strict_mode:
            return RiskAssessment(
                level=RiskLevel.HIGH,
                needs_confirmation=True,
                reason="严格模式已启用，所有操作都需要确认",
                tool_name=tool_name,
                params=params
            )
        
        # 3. 参数增强检查
        params_str = str(params).lower()
        dangerous_flags_found = []
        for flag in self.DANGEROUS_FLAGS:
            if flag.lower() in params_str:
                dangerous_flags_found.append(flag)
        
        if dangerous_flags_found:
            base_level = RiskLevel.CRITICAL
            warnings.append(f"检测到危险参数: {', '.join(dangerous_flags_found)}")
        
        # 4. 目标敏感度检查
        target = params.get("target", "") or params.get("domain", "") or params.get("targets", "")
        if target and self._is_sensitive_target(target):
            if base_level in [RiskLevel.LOW, RiskLevel.MEDIUM]:
                base_level = RiskLevel.HIGH
            warnings.append(f"目标 '{target}' 可能是内网或敏感目标")
        
        # 5. 特殊工具检查
        if tool_name == "sqlmap_scan":
            # SQLMap 特殊检查
            if params.get("level", 1) >= 3:
                base_level = RiskLevel.HIGH
                warnings.append("SQLMap 高级别测试可能触发安全设备告警")
            
            if params.get("risk", 1) >= 2:
                base_level = RiskLevel.HIGH
                warnings.append("SQLMap 高风险模式可能造成数据损坏")
        
        elif tool_name == "hydra_brute":
            # Hydra 密码破解检查
            base_level = RiskLevel.HIGH
            warnings.append("密码破解操作可能触发账户锁定")
            recommendations.append("建议使用小字典进行测试")
        
        elif tool_name == "start_pentest":
            # 渗透测试流程检查
            mode = params.get("mode", "full")
            if mode == "full":
                warnings.append("完整渗透测试将执行漏洞利用阶段")
                recommendations.append("确保已获得明确的授权")
        
        # 6. 生成最终评估结果
        needs_confirmation = base_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        
        # 生成原因描述
        reason = self._generate_reason(base_level, tool_name, warnings)
        
        assessment = RiskAssessment(
            level=base_level,
            needs_confirmation=needs_confirmation,
            reason=reason,
            tool_name=tool_name,
            params=params,
            warnings=warnings,
            recommendations=recommendations
        )
        
        logger.info(f"风险评估完成: {tool_name} -> {base_level.value}, 需确认: {needs_confirmation}")
        
        return assessment
    
    def _is_sensitive_target(self, target: str) -> bool:
        """检查目标是否为敏感目标
        
        Args:
            target: 目标地址
            
        Returns:
            bool: 是否为敏感目标
        """
        target_lower = target.lower()
        for pattern in self.SENSITIVE_TARGET_PATTERNS:
            if re.search(pattern, target_lower):
                return True
        return False
    
    def _generate_reason(self, level: RiskLevel, tool_name: str, warnings: List[str]) -> str:
        """生成风险评估原因描述
        
        Args:
            level: 风险等级
            tool_name: 工具名称
            warnings: 警告信息列表
            
        Returns:
            str: 原因描述
        """
        base_reasons = {
            RiskLevel.LOW: f"工具 '{tool_name}' 属于信息收集类操作，风险较低",
            RiskLevel.MEDIUM: f"工具 '{tool_name}' 属于扫描类操作，可能产生较多网络流量",
            RiskLevel.HIGH: f"工具 '{tool_name}' 属于漏洞利用或敏感操作，需要用户确认",
            RiskLevel.CRITICAL: f"工具 '{tool_name}' 属于破坏性操作，必须用户确认"
        }
        
        reason = base_reasons.get(level, f"工具 '{tool_name}' 风险等级: {level.value}")
        
        if warnings:
            reason += f"。{warnings[0]}"
        
        return reason
    
    def batch_assess(self, operations: List[Dict[str, Any]]) -> List[RiskAssessment]:
        """批量评估多个操作的风险
        
        Args:
            operations: 操作列表，每个元素包含 tool_name 和 params
            
        Returns:
            List[RiskAssessment]: 风险评估结果列表
        """
        return [
            self.assess(op.get("tool_name", ""), op.get("params", {}))
            for op in operations
        ]
    
    def get_highest_risk(self, assessments: List[RiskAssessment]) -> RiskLevel:
        """获取多个评估中的最高风险等级
        
        Args:
            assessments: 风险评估列表
            
        Returns:
            RiskLevel: 最高风险等级
        """
        if not assessments:
            return RiskLevel.LOW
        
        level_order = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.CRITICAL: 3
        }
        
        highest = RiskLevel.LOW
        for assessment in assessments:
            if level_order[assessment.level] > level_order[highest]:
                highest = assessment.level
        
        return highest
    
    def update_tool_risk_level(self, tool_name: str, level: RiskLevel) -> None:
        """更新工具的风险等级（运行时配置）
        
        Args:
            tool_name: 工具名称
            level: 新的风险等级
        """
        self.TOOL_RISK_LEVELS[tool_name] = level
        logger.info(f"更新工具风险等级: {tool_name} -> {level.value}")


def test_risk_assessor():
    """测试风险评估器"""
    assessor = RiskAssessor()
    
    print("=" * 60)
    print("风险评估器测试")
    print("=" * 60)
    
    # 测试用例
    test_cases = [
        {"tool_name": "nmap_scan", "params": {"target": "example.com"}},
        {"tool_name": "sqlmap_scan", "params": {"target": "http://example.com?id=1"}},
        {"tool_name": "hydra_brute", "params": {"target": "192.168.1.1", "service": "ssh"}},
        {"tool_name": "nmap_scan", "params": {"target": "192.168.1.1"}},  # 内网目标
        {"tool_name": "start_pentest", "params": {"target": "example.com", "mode": "full"}},
    ]
    
    for i, case in enumerate(test_cases, 1):
        result = assessor.assess(case["tool_name"], case["params"])
        print(f"\n{i}. {case['tool_name']}")
        print(f"   风险等级: {result.level.emoji} {result.level.value.upper()}")
        print(f"   需要确认: {'是' if result.needs_confirmation else '否'}")
        print(f"   原因: {result.reason}")
        if result.warnings:
            print(f"   警告: {', '.join(result.warnings)}")
    
    print("\n" + "=" * 60)
    print("测试完成")


if __name__ == "__main__":
    test_risk_assessor()
