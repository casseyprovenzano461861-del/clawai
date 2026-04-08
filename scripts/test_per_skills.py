# -*- coding: utf-8 -*-
"""
测试 Skills 在 P-E-R 流程中的实际调用

针对 DVWA 运行 P-E-R，验证技能是否被正确选择和执行
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.shared.backend.ai_agent.intelligent_per import IntelligentPERAgent


class MockLLMClient:
    """Mock LLM 客户端，模拟 AI 返回技能调用"""
    
    def __init__(self):
        self.call_count = 0
        self.last_planning_call = 0
    
    def chat(self, messages, tools=None):
        """模拟 LLM 响应"""
        self.call_count += 1
        
        # 判断是否是 planning 调用（有 tools 参数）
        is_planning = tools is not None
        
        if is_planning:
            self.last_planning_call = self.call_count
            print(f"  [Mock] Planning 调用 #{self.call_count}")
            
            # 根据 planning 调用次数决定返回什么
            if self.last_planning_call == 1:
                # 第一次 planning：信息收集
                tool_calls = [type('ToolCall', (), {
                    'function': type('Function', (), {
                        'name': 'nmap_scan',
                        'arguments': '{"target": "http://127.0.0.1/dvwa", "ports": "80,3306"}'
                    })()
                })()]
                
                response = type('MockResponse', (), {
                    'content': "执行端口扫描",
                    'tool_calls': tool_calls,
                    'usage': type('Usage', (), {'prompt_tokens': 100, 'completion_tokens': 50})()
                })()
                
                print(f"  [Mock] 返回 tool_calls: {[tc.function.name for tc in tool_calls]}")
                return response
                
            else:
                # 第二次 planning：使用技能
                tool_calls = [type('ToolCall', (), {
                    'function': type('Function', (), {
                        'name': 'skill_dvwa_sqli',
                        'arguments': '{"target": "http://127.0.0.1/dvwa", "level": "low"}'
                    })()
                })()]
                
                response = type('MockResponse', (), {
                    'content': "使用 DVWA SQL 注入技能",
                    'tool_calls': tool_calls,
                    'usage': type('Usage', (), {'prompt_tokens': 100, 'completion_tokens': 50})()
                })()
                
                print(f"  [Mock] 返回 tool_calls: {[tc.function.name for tc in tool_calls]}")
                return response
        else:
            # Reflecting 调用
            print(f"  [Mock] Reflecting 调用 #{self.call_count}")
            
            # 第二次 reflecting 后返回目标达成
            if self.last_planning_call >= 3:
                content = """
本次迭代发现了 DVWA 应用存在 SQL 注入漏洞。
通过 skill_dvwa_sqli 技能成功利用了漏洞，提取了用户数据。
目标已达成，无需继续测试。
"""
            else:
                content = "继续测试"
            
            response = type('MockResponse', (), {
                'content': content,
                'tool_calls': [],
                'usage': type('Usage', (), {'prompt_tokens': 100, 'completion_tokens': 50})()
            })()
            
            return response


async def mock_tool_executor(tool, params):
    """Mock 工具执行器"""
    class Result:
        success = True
        simulated = True
        output = {}
    
    result = Result()
    
    if tool == "nmap_scan":
        result.output = {
            "ports": [
                {"port": 80, "service": "http", "state": "open"},
                {"port": 3306, "service": "mysql", "state": "open"}
            ]
        }
    elif tool == "whatweb_scan":
        result.output = {
            "technologies": ["PHP", "Apache", "MySQL", "DVWA"]
        }
    
    return result


async def test_per_with_skills():
    """测试 P-E-R 流程中的技能调用"""
    print("=" * 60)
    print("测试 P-E-R 流程中的技能调用")
    print("=" * 60)
    
    agent = IntelligentPERAgent(
        llm_client=MockLLMClient(),
        tool_executor=mock_tool_executor,
        max_iterations=3
    )
    
    target = "http://127.0.0.1/dvwa"
    
    print(f"\n目标: {target}")
    print("\n开始 P-E-R 测试...\n")
    
    events = []
    async for event in agent.run(target=target, goal="对 DVWA 进行渗透测试"):
        events.append(event)
        
        if event["type"] == "start":
            print(f"[*] 开始测试: {event['target']}")
            print(f"    RAG 启用: {event['features']['rag_enabled']}")
            print(f"    预算管理: {event['features']['budget_enabled']}")
            
        elif event["type"] == "iteration":
            print(f"\n[迭代 {event['num']}/{event['max']}]")
            
        elif event["type"] == "phase":
            print(f"  [{event['phase']}] {event.get('message', '')}")
            
        elif event["type"] == "plan":
            print(f"  生成的任务: {event['tasks']}")
            
        elif event["type"] == "task_start":
            print(f"  执行任务: {event['task']}")
            
        elif event["type"] == "task_result":
            print(f"  任务结果: {'成功' if event['success'] else '失败'}")
            print(f"  模拟执行: {event['simulated']}")
            if event.get("is_skill"):
                print(f"  >>> 这是一个技能调用: {event.get('skill_id')}")
                print(f"  >>> 发现漏洞: {event.get('vulnerable')}")
            if event.get("findings"):
                print(f"  发现: {event['findings']}")
                
        elif event["type"] == "reflection":
            print(f"  反思摘要: {event['summary'][:100]}...")
            
        elif event["type"] == "complete":
            print(f"\n[*] 测试完成!")
            print(f"    迭代次数: {event['iterations']}")
            print(f"    发现数量: {event['findings_count']}")
    
    # 检查技能是否被调用
    # 检查任务历史中的技能调用
    skill_tasks = [h for h in agent.ctx.history if h.get("is_skill")]
    print(f"\n技能调用次数: {len(skill_tasks)}")
    
    # 检查发现
    findings = agent.ctx.findings
    print(f"发现的问题: {len(findings)}")
    for f in findings:
        print(f"  - {f}")
    
    # 检查是否有技能来源的发现
    skill_findings = [f for f in findings if f.get("source") == "skill"]
    print(f"\n技能发现的漏洞: {len(skill_findings)}")
    
    return len(skill_tasks) > 0 or len(skill_findings) > 0


async def main():
    """主测试"""
    success = await test_per_with_skills()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ 测试通过：技能在 P-E-R 流程中被正确调用")
    else:
        print("✗ 测试失败：技能未被调用")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
