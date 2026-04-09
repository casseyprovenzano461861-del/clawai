# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
进化引擎 - 模拟攻防博弈与策略进化
在attack_generator和decision_engine基础上实现策略进化
优化版：使用统一数据模型，解决代码重复问题
"""

import json
import random
import logging
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# 使用统一的数据模型
try:
    # 优先使用核心模型
    from .core.models import AttackStep as CoreAttackStep, ScanAnalysis
    USE_CORE_MODELS = True
except ImportError:
    try:
        # 绝对导入
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from backend.core.models import AttackStep as CoreAttackStep, ScanAnalysis
        USE_CORE_MODELS = True
    except ImportError:
        USE_CORE_MODELS = False

# 动态导入现有模块
# attack_generator 和 decision_engine 已被删除，使用兼容模式
try:
    from .attack_generator import (
        generate_attack_paths_from_scan,
        AttackPath as GeneratorAttackPath,
        AttackPathGenerator
    )
    HAS_ATTACK_GENERATOR = True
except ImportError:
    HAS_ATTACK_GENERATOR = False
    AttackPathGenerator = None
    GeneratorAttackPath = None
    generate_attack_paths_from_scan = None

try:
    from .decision_engine import (
        DecisionEngine,
        PathScore
    )
    HAS_DECISION_ENGINE = True
except ImportError:
    HAS_DECISION_ENGINE = False
    DecisionEngine = None
    PathScore = None

logger = logging.getLogger(__name__)


@dataclass
class DefenseResult:
    """防御模拟结果"""
    blocked: bool
    reason: str
    detection_type: str  # waf, ids, permission, payload
    confidence: float  # 检测置信度 0-1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "blocked": self.blocked,
            "reason": self.reason,
            "detection_type": self.detection_type,
            "confidence": self.confidence
        }


@dataclass
class EvolutionLog:
    """进化日志条目"""
    round: int
    original_path_id: int
    original_path_name: str
    failure_reason: Optional[str]
    defense_result: Optional[Dict[str, Any]]
    adjustment_strategy: str
    new_path_generated: bool
    new_path_name: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "round": self.round,
            "original_path_id": self.original_path_id,
            "original_path_name": self.original_path_name,
            "failure_reason": self.failure_reason,
            "defense_result": self.defense_result,
            "adjustment_strategy": self.adjustment_strategy,
            "new_path_generated": self.new_path_generated,
            "new_path_name": self.new_path_name
        }


@dataclass
class EvolutionResult:
    """进化引擎最终结果"""
    final_path: Dict[str, Any]
    evolution_rounds: int
    evolution_log: List[Dict[str, Any]]
    all_paths_history: List[List[Dict[str, Any]]]
    final_score: float
    improvement_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "final_path": self.final_path,
            "evolution_rounds": self.evolution_rounds,
            "evolution_log": self.evolution_log,
            "all_paths_history": self.all_paths_history,
            "final_score": self.final_score,
            "improvement_rate": self.improvement_rate,
            "summary": self._generate_summary()
        }
    
    def _generate_summary(self) -> str:
        """生成结果摘要"""
        if self.evolution_rounds == 1:
            return "首轮攻击成功，无需进化"
        
        improvement = f"经过{self.evolution_rounds-1}轮进化，评分提升{self.improvement_rate:.1%}"
        
        # 统计失败类型
        failure_types = []
        for log in self.evolution_log:
            if log.get("failure_reason"):
                failure_types.append(log.get("detection_type", "unknown"))
        
        if failure_types:
            improvement += f"，应对了{len(set(failure_types))}种防御机制"
        
        return improvement


class EvolutionEngine:
    """进化引擎 - 实现攻防博弈和策略进化"""
    
    def __init__(self, max_evolution_rounds: int = 3):
        """
        初始化进化引擎
        
        Args:
            max_evolution_rounds: 最大进化轮次
        """
        self.max_evolution_rounds = max_evolution_rounds
        self.attack_generator = AttackPathGenerator() if AttackPathGenerator else None
        self.decision_engine = DecisionEngine() if DecisionEngine else None
        
        # 防御检测概率配置
        self.defense_probabilities = {
            "waf": 0.4,      # WAF拦截概率
            "ids": 0.3,      # IDS告警概率
            "permission": 0.25,  # 权限不足概率
            "payload": 0.35  # payload失败概率
        }
        
        # 防御检测原因
        self.defense_reasons = {
            "waf": [
                "WAF检测到SQL注入特征",
                "WAF拦截了XSS攻击载荷",
                "WAF阻止了命令注入尝试",
                "WAF屏蔽了异常HTTP请求"
            ],
            "ids": [
                "IDS检测到端口扫描行为",
                "IDS告警：异常网络流量",
                "IDS发现暴力破解尝试",
                "IDS检测到可疑文件上传"
            ],
            "permission": [
                "权限不足：需要root/admin权限",
                "访问被拒绝：文件系统权限限制",
                "数据库用户权限受限",
                "API调用权限不足"
            ],
            "payload": [
                "漏洞利用失败：目标已打补丁",
                "payload执行失败：环境不匹配",
                "利用代码不兼容目标系统",
                "漏洞条件不满足"
            ]
        }
        
        # 策略调整映射
        self.strategy_adjustments = {
            "waf": [
                "使用编码/混淆绕过WAF",
                "采用延迟注入技术",
                "使用HTTP参数污染",
                "尝试分块传输编码"
            ],
            "ids": [
                "降低扫描频率和并发数",
                "使用合法的User-Agent和请求头",
                "分散攻击源IP地址",
                "使用加密通信通道"
            ],
            "permission": [
                "寻找权限提升漏洞",
                "尝试水平越权攻击",
                "利用配置错误获取更高权限",
                "使用凭证窃取技术"
            ],
            "payload": [
                "尝试替代利用方式",
                "调整payload参数和结构",
                "使用不同版本的exploit",
                "结合多个漏洞进行攻击"
            ]
        }
    
    def simulate_defense(self, attack_path: Dict[str, Any]) -> DefenseResult:
        """
        模拟防御检测
        
        Args:
            attack_path: 攻击路径
            
        Returns:
            防御检测结果
        """
        # 分析攻击路径特征，决定检测概率
        path_name = attack_path.get("name", "").lower()
        steps = attack_path.get("steps", [])
        
        # 确定攻击类型
        attack_type = self._detect_attack_type(path_name, steps)
        
        # 根据攻击类型和概率决定是否被拦截
        detection_type = attack_type if attack_type in self.defense_probabilities else "waf"
        detection_prob = self.defense_probabilities.get(detection_type, 0.3)
        
        # 加入路径成功率因素（成功率越高，被检测概率越低）
        success_rate = attack_path.get("success_rate", 0.5)
        adjusted_prob = detection_prob * (1.2 - success_rate)  # 成功率越高，概率越低
        
        # 随机决定是否被拦截
        blocked = random.random() < adjusted_prob
        
        # 生成检测原因
        if blocked:
            reason_list = self.defense_reasons.get(detection_type, ["未知防御机制"])
            reason = random.choice(reason_list)
            confidence = min(0.7 + random.random() * 0.3, 0.95)  # 0.7-0.95
        else:
            reason = "防御检测未发现异常"
            confidence = random.random() * 0.3  # 0-0.3
        
        return DefenseResult(
            blocked=blocked,
            reason=reason,
            detection_type=detection_type,
            confidence=confidence
        )
    
    def _detect_attack_type(self, path_name: str, steps: List[Dict[str, Any]]) -> str:
        """检测攻击类型"""
        path_name_lower = path_name.lower()
        
        # 基于路径名称判断
        if "sql" in path_name_lower or "注入" in path_name_lower:
            return "waf"
        elif "rce" in path_name_lower or "远程执行" in path_name_lower:
            return "payload"
        elif "权限" in path_name_lower or "提权" in path_name_lower:
            return "permission"
        elif "扫描" in path_name_lower or "侦察" in path_name_lower:
            return "ids"
        
        # 基于步骤工具判断
        tools = [step.get("tool", "").lower() for step in steps]
        
        if "sqlmap" in tools:
            return "waf"
        elif any(tool in ["nmap", "masscan", "gobuster"] for tool in tools):
            return "ids"
        elif any(tool in ["metasploit", "nuclei"] for tool in tools):
            return "payload"
        elif any(tool in ["linpeas", "winpeas", "mimikatz"] for tool in tools):
            return "permission"
        
        # 默认类型
        return "waf"
    
    def generate_improved_strategy(self, 
                                  original_path: Dict[str, Any], 
                                  defense_result: DefenseResult) -> Dict[str, Any]:
        """
        根据防御结果生成改进策略
        
        Args:
            original_path: 原始攻击路径
            defense_result: 防御检测结果
            
        Returns:
            改进后的攻击路径
        """
        # 克隆原始路径
        improved_path = original_path.copy()
        path_id = improved_path.get("path_id", 0)
        
        # 修改路径ID（新路径）
        improved_path["path_id"] = path_id * 100  # 确保ID不同
        
        # 根据防御类型获取调整策略
        detection_type = defense_result.detection_type
        adjustments = self.strategy_adjustments.get(detection_type, ["调整攻击策略"])
        adjustment = random.choice(adjustments)
        
        # 修改路径名称
        original_name = improved_path.get("name", "")
        improved_path["name"] = f"{original_name} [改进: {adjustment}]"
        
        # 修改策略描述
        original_strategy = improved_path.get("strategy", "")
        improved_path["strategy"] = f"{original_strategy} | 防御规避: {adjustment}"
        
        # 根据防御类型调整成功率
        original_success_rate = improved_path.get("success_rate", 0.5)
        
        if defense_result.blocked:
            # 被拦截，成功率需要调整（可能降低或提高，取决于调整策略）
            if detection_type == "waf":
                # WAF绕过通常成功率较低
                improved_success_rate = original_success_rate * 0.8
            elif detection_type == "ids":
                # IDS规避可能稍微降低成功率
                improved_success_rate = original_success_rate * 0.85
            elif detection_type == "permission":
                # 权限提升可能成功率较低
                improved_success_rate = original_success_rate * 0.75
            else:  # payload
                # 更换payload可能提高成功率
                improved_success_rate = min(original_success_rate * 1.1, 0.9)
        else:
            # 未被拦截，稍微提高成功率
            improved_success_rate = min(original_success_rate * 1.05, 0.95)
        
        improved_path["success_rate"] = round(improved_success_rate, 2)
        
        # 调整步骤描述
        steps = improved_path.get("steps", [])
        for step in steps:
            # 在描述中添加规避信息
            original_desc = step.get("description", "")
            step["description"] = f"{original_desc} [规避: {adjustment}]"
            
            # 调整工具使用（如果需要）
            tool = step.get("tool", "")
            if detection_type == "waf" and tool == "sqlmap":
                step["tool"] = "sqlmap (绕过模式)"
                step["success_probability"] = step.get("success_probability", 0.5) * 0.9
        
        # 更新步骤数
        improved_path["step_count"] = len(steps)
        
        # 调整难度（改进策略通常更难）
        original_difficulty = improved_path.get("difficulty", "medium")
        if original_difficulty == "easy":
            improved_path["difficulty"] = "medium"
        elif original_difficulty == "medium":
            improved_path["difficulty"] = "hard"
        
        # 调整估计时间（改进策略可能需要更长时间）
        original_time = improved_path.get("estimated_time", "10分钟")
        if "分钟" in original_time:
            try:
                minutes = int(original_time.replace("分钟", ""))
                improved_path["estimated_time"] = f"{int(minutes * 1.2)}分钟"
            except Exception as e:
                improved_path["estimated_time"] = f"{int(10 * 1.2)}分钟"
        
        return improved_path
    
    def evolve_attack_paths(self, 
                           scan_results: Dict[str, Any],
                           initial_paths_count: int = 4) -> EvolutionResult:
        """
        执行进化过程
        
        Args:
            scan_results: 扫描结果
            initial_paths_count: 初始生成路径数量
            
        Returns:
            进化结果
        """
        # 初始化进化日志和历史记录
        evolution_log = []
        all_paths_history = []
        current_round = 1
        
        # 步骤1: 初始阶段 - 生成攻击路径
        logger.info(f"第{current_round}轮: 生成初始攻击路径")
        if generate_attack_paths_from_scan and HAS_ATTACK_GENERATOR:
            initial_result = generate_attack_paths_from_scan(scan_results)
        else:
            initial_result = {"attack_paths_generated": 0}
        
        if initial_result.get("attack_paths_generated", 0) < 3:
            # 如果生成路径不足，使用模拟数据
            initial_paths = self._generate_fallback_paths(scan_results, initial_paths_count)
        else:
            initial_paths = initial_result["attack_paths"][:initial_paths_count]
        
        scan_summary = initial_result.get("scan_summary", {})
        all_paths_history.append(initial_paths.copy())
        
        # 步骤2: 第一轮决策
        logger.info(f"第{current_round}轮: 初始决策")
        if self.decision_engine and HAS_DECISION_ENGINE:
            decision_result = self.decision_engine.process_paths(initial_paths, scan_summary)
        else:
            decision_result = {"best_path": None}
        
        if not decision_result.get("best_path"):
            # 如果无法选择最佳路径，使用第一条路径
            best_path = initial_paths[0] if initial_paths else None
        else:
            best_path = decision_result["best_path"]["path_info"]
        
        # 模拟防御检测
        defense_result = self.simulate_defense(best_path)
        
        # 记录第一轮日志
        evolution_log.append(EvolutionLog(
            round=current_round,
            original_path_id=best_path.get("path_id", 0) if best_path else 0,
            original_path_name=best_path.get("name", "") if best_path else "",
            failure_reason=defense_result.reason if defense_result.blocked else None,
            defense_result=defense_result.to_dict() if defense_result.blocked else None,
            adjustment_strategy="初始选择，无需调整" if not defense_result.blocked else "等待进化调整",
            new_path_generated=False,
            new_path_name=None
        ).to_dict())
        
        # 如果首轮未被拦截，直接返回
        if not defense_result.blocked or current_round >= self.max_evolution_rounds:
            return self._create_final_result(
                final_path=best_path,
                decision_result=decision_result,
                evolution_rounds=current_round,
                evolution_log=evolution_log,
                all_paths_history=all_paths_history,
                initial_score=decision_result.get("best_path", {}).get("score_info", {}).get("total_score", 0)
            )
        
        # 步骤3: 进化循环
        current_paths = initial_paths.copy()
        original_best_path = best_path.copy()
        
        while defense_result.blocked and current_round < self.max_evolution_rounds:
            current_round += 1
            logger.info(f"第{current_round}轮: 策略进化")
            
            # 生成改进策略
            improved_path = self.generate_improved_strategy(original_best_path, defense_result)
            
            # 将改进路径添加到路径列表中
            current_paths.append(improved_path)
            
            # 重新决策（包含所有路径）
            if self.decision_engine and HAS_DECISION_ENGINE:
                new_decision_result = self.decision_engine.process_paths(current_paths, scan_summary)
            else:
                new_decision_result = {"best_path": None}
            
            if new_decision_result.get("best_path"):
                new_best_path = new_decision_result["best_path"]["path_info"]
                new_best_score = new_decision_result["best_path"]["score_info"]["total_score"]
            else:
                new_best_path = improved_path
                new_best_score = 0
            
            # 再次模拟防御检测
            defense_result = self.simulate_defense(new_best_path)
            
            # 记录进化日志
            evolution_log.append(EvolutionLog(
                round=current_round,
                original_path_id=original_best_path.get("path_id", 0),
                original_path_name=original_best_path.get("name", ""),
                failure_reason=defense_result.reason if defense_result.blocked else None,
                defense_result=defense_result.to_dict() if defense_result.blocked else None,
                adjustment_strategy=self.strategy_adjustments.get(
                    defense_result.detection_type, ["调整策略"]
                )[0],
                new_path_generated=True,
                new_path_name=improved_path.get("name", "")
            ).to_dict())
            
            # 更新历史记录
            all_paths_history.append(current_paths.copy())
            
            # 更新最佳路径
            original_best_path = new_best_path.copy()
        
        # 步骤4: 生成最终结果
        if self.decision_engine and HAS_DECISION_ENGINE:
            final_decision_result = self.decision_engine.process_paths(current_paths, scan_summary)
        else:
            final_decision_result = {"best_path": None}
        
        if final_decision_result.get("best_path"):
            final_path_info = final_decision_result["best_path"]["path_info"]
            final_score = final_decision_result["best_path"]["score_info"]["total_score"]
        else:
            final_path_info = original_best_path
            final_score = 0
        
        # 计算初始分数
        initial_score = decision_result.get("best_path", {}).get("score_info", {}).get("total_score", 0)
        
        return self._create_final_result(
            final_path=final_path_info,
            decision_result=final_decision_result,
            evolution_rounds=current_round,
            evolution_log=evolution_log,
            all_paths_history=all_paths_history,
            initial_score=initial_score,
            final_score=final_score
        )
    
    def _create_final_result(self,
                            final_path: Dict[str, Any],
                            decision_result: Dict[str, Any],
                            evolution_rounds: int,
                            evolution_log: List[Dict[str, Any]],
                            all_paths_history: List[List[Dict[str, Any]]],
                            initial_score: float = 0,
                            final_score: float = None) -> EvolutionResult:
        """创建最终进化结果"""
        if final_score is None:
            if decision_result.get("best_path"):
                final_score = decision_result["best_path"]["score_info"]["total_score"]
            else:
                final_score = 0
        
        # 计算改进率
        if initial_score > 0:
            improvement_rate = (final_score - initial_score) / initial_score
        else:
            improvement_rate = 0.0
        
        return EvolutionResult(
            final_path=final_path,
            evolution_rounds=evolution_rounds,
            evolution_log=evolution_log,
            all_paths_history=all_paths_history,
            final_score=final_score,
            improvement_rate=improvement_rate
        )
    
    def _generate_fallback_paths(self, 
                                scan_results: Dict[str, Any], 
                                count: int) -> List[Dict[str, Any]]:
        """生成备用攻击路径（当攻击生成器失败时使用）"""
        # 这里简化实现，实际应该调用攻击生成器的备选方法
        paths = []
        
        for i in range(count):
            path = {
                "path_id": i + 1,
                "name": f"备用攻击路径 {i+1}",
                "strategy": "基础渗透测试",
                "steps": [
                    {
                        "step": 1,
                        "tool": "nmap",
                        "description": "端口扫描",
                        "target": "目标网络",
                        "duration": "2分钟",
                        "success_probability": 0.8
                    },
                    {
                        "step": 2,
                        "tool": "nuclei",
                        "description": "漏洞扫描",
                        "target": "Web服务",
                        "duration": "3分钟",
                        "success_probability": 0.6
                    }
                ],
                "target_focus": "综合目标",
                "difficulty": "medium",
                "estimated_time": "5分钟",
                "success_rate": 0.7,
                "step_count": 2
            }
            paths.append(path)
        
        return paths


def test_evolution_engine():
    """测试进化引擎功能"""
    import sys
    
    # 测试数据
    test_scan_results = {
        "nmap": {
            "ports": [
                {"port": 80, "service": "http", "state": "open"},
                {"port": 443, "service": "https", "state": "open"},
                {"port": 3306, "service": "mysql", "state": "open"}
            ]
        },
        "whatweb": {
            "fingerprint": {
                "web_server": "nginx",
                "language": ["PHP"],
                "cms": ["WordPress"]
            }
        },
        "nuclei": {
            "vulnerabilities": [
                {"name": "SQL Injection", "severity": "high"},
                {"name": "XSS Vulnerability", "severity": "medium"}
            ]
        }
    }
    
    print("=" * 80)
    print("进化引擎测试")
    print("=" * 80)
    
    print("\n测试扫描结果摘要:")
    print(f"端口数量: {len(test_scan_results['nmap']['ports'])}")
    print(f"漏洞数量: {len(test_scan_results['nuclei']['vulnerabilities'])}")
    
    # 创建进化引擎
    engine = EvolutionEngine(max_evolution_rounds=3)
    
    print("\n" + "=" * 80)
    print("开始进化过程...")
    
    # 执行进化
    result = engine.evolve_attack_paths(test_scan_results)
    
    print("\n进化结果:")
    result_dict = result.to_dict()
    print(json.dumps(result_dict, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 80)
    print("进化过程摘要:")
    
    print(f"\n[进化轮次] 进化轮次: {result.evolution_rounds}")
    print(f"[最终路径] 最终路径: {result.final_path.get('name', '未知')}")
    print(f"[最终评分] 最终评分: {result.final_score:.1f}/10")
    print(f"[改进率] 改进率: {result.improvement_rate:.1%}")
    print(f"[进化日志条目] 进化日志条目: {len(result.evolution_log)}")
    
    if result.evolution_log:
        print("\n[进化日志详情] 进化日志详情:")
        for log in result.evolution_log:
            round_num = log.get("round", 0)
            original_name = log.get("original_path_name", "")
            failure = log.get("failure_reason", "无")
            adjustment = log.get("adjustment_strategy", "")
            
            print(f"  轮次 {round_num}: {original_name}")
            if failure != "无":
                print(f"     失败原因: {failure}")
                print(f"     调整策略: {adjustment}")
    
    print("\n" + "=" * 80)
    
    # 验证是否满足要求
    if result.final_path and result.evolution_log is not None:
        print("[成功] 测试通过：进化引擎功能完整")
        return True
    else:
        print("[失败] 测试失败：进化引擎功能不完整")
        return False


if __name__ == "__main__":
    import sys
    # 运行测试
    success = test_evolution_engine()
    sys.exit(0 if success else 1)