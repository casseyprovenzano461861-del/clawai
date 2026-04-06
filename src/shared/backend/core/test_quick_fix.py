# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
快速测试决策引擎修复
"""

import sys
import os
import json

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(current_dir))

from decision_engine import DecisionEngine, StrategyType, DecisionType, ContextAnalysis, Decision
from context_manager import ContextManager
from strategy_repository import StrategyRepository


def test_decision_engine_fix():
    """测试决策引擎修复"""
    print("=" * 80)
    print("测试决策引擎修复")
    print("=" * 80)
    
    # 创建上下文管理器
    context_manager = ContextManager()
    
    # 创建策略库
    strategy_repository = StrategyRepository()
    
    # 创建决策引擎
    decision_engine = DecisionEngine(context_manager, strategy_repository)
    
    # 测试数据
    test_scan_data = {
        "target": "example.com",
        "ports": [
            {"port": 80, "service": "http", "state": "open"},
            {"port": 443, "service": "https", "state": "open"},
            {"port": 3306, "service": "mysql", "state": "open"}
        ],
        "vulnerabilities": [
            {"name": "SQL Injection", "severity": "high"},
            {"name": "XSS Vulnerability", "severity": "medium"}
        ],
        "fingerprint": {
            "web_server": "nginx/1.18.0",
            "language": ["PHP 7.4"],
            "cms": ["WordPress 5.8"],
            "other": ["jQuery", "Bootstrap"]
        }
    }
    
    test_user_context = {
        "target": "example.com",
        "industry": "e-commerce",
        "test_type": "pentest",
        "constraints": {
            "network": "external",
            "bandwidth_limit": "medium"
        },
        "time_constraints": {
            "strict": False,
            "time_limit": 120
        },
        "risk_tolerance": "medium",
        "compliance_requirements": ["PCI-DSS"]
    }
    
    try:
        # 做出决策
        decision = decision_engine.make_decision(test_scan_data, test_user_context)
        
        print(f"✓ 决策引擎测试成功")
        print(f"  决策ID: {decision.decision_id}")
        print(f"  策略类型: {decision.strategy.value}")
        print(f"  决策类型: {decision.decision_type.value}")
        print(f"  置信度: {decision.confidence:.2f}")
        print(f"  决策理由: {decision.rationale}")
        
        # 检查决策历史
        history = decision_engine.get_decision_history()
        print(f"  决策历史记录: {len(history)}条")
        
        return True
        
    except Exception as e:
        print(f"✗ 决策引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_strategy_repository_matching():
    """测试策略库匹配"""
    print("\n" + "=" * 80)
    print("测试策略库匹配")
    print("=" * 80)
    
    # 创建策略库
    repository = StrategyRepository()
    
    # 测试上下文
    test_context = {
        "target_type": "Web",
        "tech_stack": ["nginx", "PHP", "WordPress", "MySQL"],
        "defense_measures": ["WAF: Cloudflare"],
        "compliance_requirements": ["PCI-DSS"],
        "time_constraints": {
            "strict": False,
            "time_limit": 180,
            "urgency": "normal"
        },
        "risk_tolerance": "medium",
        "target_confidence": 0.85,
        "vulnerabilities": [
            {"name": "XSS", "severity": "medium"},
            {"name": "SQLi", "severity": "high"}
        ],
        "environment_constraints": {
            "network": "external",
            "access_level": "normal"
        }
    }
    
    try:
        # 获取匹配的策略
        matching_strategies = repository.get_matching_strategies(test_context)
        
        print(f"✓ 策略库测试成功")
        print(f"  总策略数: {repository.get_strategy_statistics()['total_strategies']}")
        print(f"  匹配策略数: {len(matching_strategies)}")
        
        if matching_strategies:
            print(f"  最佳策略: {matching_strategies[0]['name']}")
            print(f"  最佳策略得分: {matching_strategies[0]['score']:.2f}")
        
        # 选择最佳策略
        best_strategy = repository.select_strategy(test_context)
        print(f"  选择的策略类型: {best_strategy.value}")
        
        return True
        
    except Exception as e:
        print(f"✗ 策略库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("大模型集成强化 - 快速修复测试")
    print("=" * 80)
    
    # 测试决策引擎修复
    decision_engine_result = test_decision_engine_fix()
    
    # 测试策略库匹配
    strategy_repo_result = test_strategy_repository_matching()
    
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    if decision_engine_result and strategy_repo_result:
        print("✓ 所有修复测试通过！")
        print("  决策引擎现在可以正确处理字典类型的上下文")
        print("  策略库匹配算法正常工作")
        return 0
    else:
        print("✗ 有测试失败，请检查相关模块")
        return 1


if __name__ == "__main__":
    sys.exit(main())