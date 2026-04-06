# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
大模型集成强化集成测试
测试新模块的集成效果
"""

import sys
import os
import json
import time
from pathlib import Path

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(current_dir))

from backend.core.decision_engine import DecisionEngine, StrategyType, DecisionType, ContextAnalysis, Decision
from backend.core.context_manager import ContextManager, TargetAnalysis
from backend.core.strategy_repository import StrategyRepository, StrategyType as StrategyTypeRepo
from backend.core.intelligent_tool_selector import IntelligentToolSelector, ToolRecommendation
from backend.core.llm_cache import IntelligentLLMCache
from backend.core.enhanced_agent import EnhancedSecurityAgent


def test_decision_engine():
    """测试决策引擎"""
    print("=" * 80)
    print("测试决策引擎")
    print("=" * 80)
    
    # 创建简单的上下文管理器（这里使用实际实现）
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
        
        print(f"[OK] 决策引擎测试成功")
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
        print(f"[FAIL] 决策引擎测试失败: {e}")
        return False


def test_context_manager():
    """测试上下文管理器"""
    print("\n" + "=" * 80)
    print("测试上下文管理器")
    print("=" * 80)
    
    # 创建上下文管理器
    context_manager = ContextManager()
    
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
        },
        "wafw00f": {
            "waf_detected": True,
            "waf_type": "Cloudflare"
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
        "risk_tolerance": "medium"
    }
    
    try:
        # 分析上下文
        context_analysis = context_manager.analyze(test_scan_data, test_user_context)
        
        print(f"[OK] 上下文管理器测试成功")
        print(f"  目标类型: {context_analysis['target_type']}")
        print(f"  技术栈: {len(context_analysis['tech_stack'])}项")
        print(f"  防御措施: {len(context_analysis['defense_measures'])}项")
        print(f"  风险容忍度: {context_analysis['risk_tolerance']}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 上下文管理器测试失败: {e}")
        return False


def test_strategy_repository():
    """测试策略库"""
    print("\n" + "=" * 80)
    print("测试策略库")
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
        
        print(f"[OK] 策略库测试成功")
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
        print(f"[FAIL] 策略库测试失败: {e}")
        return False


def test_intelligent_tool_selector():
    """测试智能工具选择器"""
    print("\n" + "=" * 80)
    print("测试智能工具选择器")
    print("=" * 80)
    
    # 创建智能工具选择器
    selector = IntelligentToolSelector()
    
    # 测试攻击步骤
    test_attack_step = {
        "type": "scanning",
        "description": "Web漏洞扫描",
        "required_capabilities": ["web_scan", "vulnerability_scan"]
    }
    
    # 测试上下文
    test_context = {
        "stealth_required": False,
        "performance_priority": True,
        "coverage_priority": True,
        "target_url": "http://example.com",
        "max_combinations": 2
    }
    
    try:
        # 选择工具
        recommendations = selector.select_tools(test_attack_step, test_context)
        
        print(f"[OK] 智能工具选择器测试成功")
        print(f"  工具推荐数: {len(recommendations)}")
        
        if recommendations:
            for i, rec in enumerate(recommendations[:2]):  # 显示前2个推荐
                print(f"  推荐{i+1}: {rec.name} (置信度: {rec.confidence:.2f}, 风险等级: {rec.risk_level})")
        
        # 获取工具统计
        stats = selector.get_tool_statistics()
        print(f"  工具总数: {stats['total_tools']}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 智能工具选择器测试失败: {e}")
        return False


def test_llm_cache():
    """测试智能LLM缓存"""
    print("\n" + "=" * 80)
    print("测试智能LLM缓存")
    print("=" * 80)
    
    # 创建缓存系统
    cache = IntelligentLLMCache(backend="memory")
    
    try:
        # 测试数据
        test_prompts = [
            "扫描example.com的80和443端口",
            "检查example.com的Web漏洞",
            "评估example.com的安全风险"
        ]
        
        test_responses = [
            "发现80端口运行nginx，443端口有SSL配置问题",
            "发现XSS和CSRF漏洞，建议修复",
            "目标存在中等风险，建议加强WAF配置"
        ]
        
        # 缓存测试数据
        for i, (prompt, response) in enumerate(zip(test_prompts, test_responses)):
            cache.cache_response(prompt, response, model="test-model")
        
        # 获取缓存统计
        stats = cache.get_cache_stats()
        
        print(f"[OK] 智能LLM缓存测试成功")
        print(f"  缓存条目数: {stats['total_entries']}")
        print(f"  平均使用次数: {stats['avg_usage']:.2f}")
        
        # 测试缓存命中
        test_query = "扫描example.com的80和443端口"
        cached_response = cache.get_cached_response(test_query, model="test-model")
        
        if cached_response:
            print(f"  缓存命中: {test_query[:30]}...")
        else:
            print(f"  缓存未命中: {test_query[:30]}...")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 智能LLM缓存测试失败: {e}")
        return False


def test_enhanced_agent_with_new_modules():
    """测试增强AI智能体与新的模块集成"""
    print("\n" + "=" * 80)
    print("测试增强AI智能体与新的模块集成")
    print("=" * 80)
    
    try:
        # 创建增强AI智能体
        agent = EnhancedSecurityAgent()
        
        # 测试数据
        test_data = {
            "target": "example.com",
            "ports": [
                {"port": 80, "service": "http", "state": "open"},
                {"port": 443, "service": "https", "state": "open"},
                {"port": 3306, "service": "mysql", "state": "open"},
                {"port": 22, "service": "ssh", "state": "open"}
            ],
            "vulnerabilities": [
                {"name": "XSS漏洞", "severity": "medium", "description": "跨站脚本漏洞"},
                {"name": "SQL注入", "severity": "high", "description": "SQL注入点"}
            ],
            "fingerprint": {
                "web_server": "nginx/1.18.0",
                "language": ["PHP 7.4"],
                "cms": ["WordPress 5.8"],
                "other": []
            }
        }
        
        # 分析扫描结果
        report = agent.analyze_scan_results(test_data)
        
        print(f"[OK] 增强AI智能体测试成功")
        print(f"  目标: {report.get('target', '未知')}")
        print(f"  风险等级: {report.get('risk_assessment', {}).get('risk_level', '未知')}")
        print(f"  攻击路径数: {len(report.get('attack_paths', []))}")
        print(f"  工具推荐数: {len(report.get('tool_recommendations', []))}")
        
        # 测试LLM查询（如果配置了API）
        if agent.llm_client:
            test_prompt = "针对Web服务器nginx 1.18.0有什么已知漏洞？"
            response = agent.query_llm(test_prompt, use_cache=True)
            
            if response:
                print(f"  LLM查询成功: {response[:50]}...")
            else:
                print(f"  LLM查询失败或无响应")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 增强AI智能体测试失败: {e}")
        return False


def test_integrated_workflow():
    """测试完整的工作流程集成"""
    print("\n" + "=" * 80)
    print("测试完整的工作流程集成")
    print("=" * 80)
    
    try:
        # 1. 初始化所有模块
        context_manager = ContextManager()
        strategy_repository = StrategyRepository()
        tool_selector = IntelligentToolSelector()
        llm_cache = IntelligentLLMCache(backend="memory")
        
        # 2. 准备测试数据
        test_scan_data = {
            "target": "test-website.com",
            "ports": [
                {"port": 80, "service": "http", "state": "open"},
                {"port": 443, "service": "https", "state": "open"},
                {"port": 8080, "service": "http-proxy", "state": "open"}
            ],
            "vulnerabilities": [
                {"name": "Reflected XSS", "severity": "medium"},
                {"name": "Information Disclosure", "severity": "low"}
            ],
            "fingerprint": {
                "web_server": "Apache/2.4.41",
                "language": ["PHP 7.3"],
                "cms": ["WordPress 5.7"],
                "other": ["Bootstrap 4.5", "jQuery 3.5"]
            }
        }
        
        test_user_context = {
            "target": "test-website.com",
            "industry": "education",
            "test_type": "security_assessment",
            "constraints": {
                "network": "external",
                "bandwidth_limit": "high"
            },
            "time_constraints": {
                "strict": True,
                "time_limit": 90,
                "urgency": "normal"
            },
            "risk_tolerance": "low",
            "compliance_requirements": ["GDPR"]
        }
        
        # 3. 上下文分析
        context_analysis = context_manager.analyze(test_scan_data, test_user_context)
        print(f"[OK] 上下文分析完成")
        print(f"  目标类型: {context_analysis['target_type']}")
        print(f"  检测到技术栈: {', '.join(context_analysis['tech_stack'][:3])}")
        
        # 4. 策略选择
        strategy = strategy_repository.select_strategy(context_analysis)
        print(f"[OK] 策略选择完成")
        print(f"  选择策略: {strategy.value}")
        
        # 5. 创建决策引擎
        decision_engine = DecisionEngine(context_manager, strategy_repository)
        decision = decision_engine.make_decision(test_scan_data, test_user_context)
        print(f"[OK] 决策完成")
        print(f"  决策ID: {decision.decision_id}")
        print(f"  置信度: {decision.confidence:.2f}")
        
        # 6. 工具选择
        attack_step = {
            "type": "scanning",
            "description": "Web应用漏洞扫描",
            "required_capabilities": ["web_scan", "vulnerability_scan"]
        }
        
        tool_context = {
            "stealth_required": test_user_context.get("risk_tolerance") == "low",
            "performance_priority": test_user_context.get("time_constraints", {}).get("strict", False),
            "target_url": f"http://{test_scan_data['target']}"
        }
        
        tool_recommendations = tool_selector.select_tools(attack_step, tool_context)
        print(f"[OK] 工具选择完成")
        print(f"  推荐工具数: {len(tool_recommendations)}")
        
        if tool_recommendations:
            for i, rec in enumerate(tool_recommendations[:2]):
                print(f"  工具{i+1}: {rec.name} (风险: {rec.risk_level})")
        
        # 7. LLM缓存测试
        test_prompt = f"针对{test_scan_data['target']}的{test_scan_data['fingerprint']['web_server']}有什么安全建议？"
        test_response = "建议更新到最新版本，配置安全的SSL/TLS，启用WAF规则。"
        
        llm_cache.cache_response(test_prompt, test_response, model="test-model")
        cached_response = llm_cache.get_cached_response(test_prompt, model="test-model")
        
        print(f"[OK] LLM缓存测试完成")
        print(f"  缓存条目数: {llm_cache.get_cache_stats()['total_entries']}")
        
        if cached_response:
            print(f"  缓存命中成功")
        
        print("\n" + "=" * 80)
        print("完整工作流程测试完成！")
        print("所有新模块已成功集成并正常工作。")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 完整工作流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("大模型集成强化 - 集成测试")
    print("=" * 80)
    
    test_results = []
    
    # 运行各个模块的测试
    test_results.append(("决策引擎", test_decision_engine()))
    test_results.append(("上下文管理器", test_context_manager()))
    test_results.append(("策略库", test_strategy_repository()))
    test_results.append(("智能工具选择器", test_intelligent_tool_selector()))
    test_results.append(("智能LLM缓存", test_llm_cache()))
    test_results.append(("增强AI智能体", test_enhanced_agent_with_new_modules()))
    test_results.append(("完整工作流程", test_integrated_workflow()))
    
    # 汇总测试结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, result in test_results if result)
    failed_tests = total_tests - passed_tests
    
    print(f"总计测试: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {failed_tests}")
    print(f"通过率: {(passed_tests / total_tests * 100):.1f}%")
    
    print("\n详细结果:")
    for name, result in test_results:
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"  {name}: {status}")
    
    print("\n" + "=" * 80)
    if failed_tests == 0:
        print("所有测试通过！大模型集成强化实现成功。")
        print("=" * 80)
        return 0
    else:
        print(f"有{failed_tests}个测试失败，请检查相关模块。")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())