# -*- coding: utf-8 -*-
"""
测试 Skills 库集成

验证 Skills 库是否正确集成到 P-E-R Agent
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.shared.backend.skills import get_skill_registry, SkillType, SkillCategory


def test_skill_registry():
    """测试技能注册表"""
    print("=" * 60)
    print("测试 Skills 注册表")
    print("=" * 60)
    
    registry = get_skill_registry()
    
    # 列出所有技能
    skills = registry.list()
    print(f"\n已注册技能数量: {len(skills)}")
    
    print("\n技能列表:")
    for skill in skills:
        print(f"  - {skill.id}: {skill.name} [{skill.severity.upper()}]")
    
    return registry


def test_skill_schema():
    """测试 OpenAI Function Calling Schema"""
    print("\n" + "=" * 60)
    print("测试 OpenAI Schema 生成")
    print("=" * 60)
    
    registry = get_skill_registry()
    schemas = registry.get_openai_tools()
    
    print(f"\n生成的 Schema 数量: {len(schemas)}")
    
    # 显示几个示例
    for schema in schemas[:3]:
        func = schema.get("function", {})
        print(f"\n技能: {func.get('name')}")
        print(f"描述: {func.get('description')[:80]}...")
        params = func.get("parameters", {}).get("properties", {})
        print(f"参数: {list(params.keys())}")
    
    return schemas


def test_skill_search():
    """测试技能搜索"""
    print("\n" + "=" * 60)
    print("测试技能搜索")
    print("=" * 60)
    
    registry = get_skill_registry()
    
    # 搜索 SQL 注入相关技能
    results = registry.search("sql注入", top_k=5)
    print(f"\n搜索 'sql注入' 结果:")
    for skill in results:
        print(f"  - {skill.id}: {skill.name}")
    
    # 搜索 XSS 相关技能
    results = registry.search("xss", top_k=5)
    print(f"\n搜索 'xss' 结果:")
    for skill in results:
        print(f"  - {skill.id}: {skill.name}")
    
    # 搜索 DVWA 相关技能
    results = registry.search("dvwa", top_k=5)
    print(f"\n搜索 'dvwa' 结果:")
    for skill in results:
        print(f"  - {skill.id}: {skill.name}")


def test_skill_execution():
    """测试技能执行"""
    print("\n" + "=" * 60)
    print("测试技能执行")
    print("=" * 60)
    
    registry = get_skill_registry()
    
    # 测试 SQL 注入检测（使用安全的测试 URL）
    print("\n执行 sqli_basic 技能:")
    result = registry.execute("sqli_basic", {
        "target": "http://example.com/test",
        "param": "id"
    })
    print(f"  成功: {result.get('success')}")
    print(f"  输出: {result.get('output', '')[:200]}")
    
    # 测试备份文件检测
    print("\n执行 info_backup_files 技能:")
    result = registry.execute("info_backup_files", {
        "target": "http://example.com"
    })
    print(f"  成功: {result.get('success')}")
    print(f"  输出: {result.get('output', '')[:200]}")


def test_per_integration():
    """测试 P-E-R Agent 集成"""
    print("\n" + "=" * 60)
    print("测试 P-E-R Agent 集成")
    print("=" * 60)
    
    # 检查 intelligent_per 中的 Skills 导入
    from src.shared.backend.ai_agent.intelligent_per import _get_skill_registry
    
    registry = _get_skill_registry()
    if registry:
        print(f"\n✓ Skills 库已成功集成到 P-E-R Agent")
        print(f"  可用技能数量: {len(registry.list())}")
        
        # 检查工具定义
        from src.shared.backend.ai_agent.intelligent_per import IntelligentPERAgent
        
        # 创建一个 mock agent 来检查工具定义
        class MockLLMClient:
            def chat(self, *args, **kwargs):
                class MockResponse:
                    content = '{"tasks": []}'
                    tool_calls = []
                return MockResponse()
        
        class MockToolExecutor:
            async def __call__(self, tool, params):
                class MockResult:
                    success = True
                    simulated = True
                    output = {}
                return MockResult()
        
        agent = IntelligentPERAgent(
            llm_client=MockLLMClient(),
            tool_executor=MockToolExecutor()
        )
        
        tools = agent._get_tool_definitions()
        skills = [t for t in tools if t.get("is_skill")]
        
        print(f"\n  工具定义中包含的技能数量: {len(skills)}")
        for s in skills[:5]:
            print(f"    - {s['name']}")
        
        # 检查 Schema
        schemas = agent._get_tools_schema()
        skill_schemas = [s for s in schemas if s.get("function", {}).get("name", "").startswith("skill_")]
        print(f"\n  生成的技能 Schema 数量: {len(skill_schemas)}")
        
    else:
        print("\n✗ Skills 库未集成到 P-E-R Agent")


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("ClawAI Skills 库集成测试")
    print("=" * 60)
    
    # 1. 测试注册表
    test_skill_registry()
    
    # 2. 测试 Schema 生成
    test_skill_schema()
    
    # 3. 测试搜索
    test_skill_search()
    
    # 4. 测试执行
    test_skill_execution()
    
    # 5. 测试 P-E-R 集成
    test_per_integration()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
