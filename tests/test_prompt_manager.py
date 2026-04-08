"""
Prompt管理系统测试
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "shared"))

from backend.prompts import (
    PromptManager,
    get_prompt_service,
    render_prompt,
    TemplateNotFoundError
)


def test_prompt_manager():
    """测试Prompt管理器"""
    print("=" * 60)
    print("测试 PromptManager")
    print("=" * 60)
    
    # 初始化管理器
    template_dir = project_root / "src" / "shared" / "backend" / "prompts" / "templates"
    manager = PromptManager(template_dir=str(template_dir))
    
    # 列出可用模板
    print("\n可用模板列表:")
    templates = manager.list_templates()
    for t in templates:
        print(f"  - {t.name}: {t.description}")
    
    print(f"\n共 {len(templates)} 个模板")


def test_render_planning():
    """测试攻击规划Prompt渲染"""
    print("\n" + "=" * 60)
    print("测试攻击规划Prompt渲染")
    print("=" * 60)
    
    service = get_prompt_service()
    
    # 渲染规划Prompt
    result = service.render_planning_prompt(
        target="example.com",
        target_info={
            "type": "web",
            "open_ports": [80, 443],
            "services": {"80": "nginx", "443": "nginx"}
        },
        vulnerabilities=[
            {"name": "XSS", "severity": "medium", "description": "跨站脚本漏洞"}
        ],
        tools=[
            {"name": "nmap", "description": "网络扫描工具", "category": "reconnaissance"},
            {"name": "nikto", "description": "Web扫描工具", "category": "scanning"}
        ]
    )
    
    print(f"\n模板名称: {result.template_name}")
    print(f"Token估算: {result.token_estimate}")
    print(f"内容长度: {len(result.content)}")
    print(f"内容哈希: {result.hash}")
    print(f"\n渲染结果预览 (前500字符):\n")
    print(result.content[:500] + "..." if len(result.content) > 500 else result.content)


def test_render_execution():
    """测试工具执行Prompt渲染"""
    print("\n" + "=" * 60)
    print("测试工具执行Prompt渲染")
    print("=" * 60)
    
    service = get_prompt_service()
    
    result = service.render_execution_prompt(
        tool_name="nmap",
        target="192.168.1.1",
        parameters={"ports": "1-1000", "scripts": "default"},
        tool_description="网络端口扫描工具",
        context={"scan_type": "quick"}
    )
    
    print(f"\nToken估算: {result.token_estimate}")
    print(f"\n渲染结果预览:\n")
    print(result.content[:800] + "..." if len(result.content) > 800 else result.content)


def test_render_verification():
    """测试漏洞验证Prompt渲染"""
    print("\n" + "=" * 60)
    print("测试漏洞验证Prompt渲染")
    print("=" * 60)
    
    service = get_prompt_service()
    
    result = service.render_verification_prompt(
        vulnerability={
            "name": "SQL Injection",
            "type": "injection",
            "severity": "critical",
            "description": "登录页面存在SQL注入漏洞"
        },
        target="http://example.com/login",
        target_context={
            "service": "Apache",
            "version": "2.4.41"
        },
        evidence=[
            {"type": "response", "value": "SQL syntax error detected"}
        ]
    )
    
    print(f"\nToken估算: {result.token_estimate}")
    print(f"\n渲染结果预览:\n")
    print(result.content[:800] + "..." if len(result.content) > 800 else result.content)


def test_system_prompts():
    """测试系统提示获取"""
    print("\n" + "=" * 60)
    print("测试系统提示")
    print("=" * 60)
    
    service = get_prompt_service()
    
    for role in ["planner", "executor", "reflector"]:
        try:
            prompt = service.get_system_prompt(role)
            print(f"\n{role.upper()} 系统提示 ({len(prompt)} 字符):")
            print(prompt[:300] + "..." if len(prompt) > 300 else prompt)
        except Exception as e:
            print(f"获取 {role} 系统提示失败: {e}")


def test_quick_render():
    """测试快速渲染函数"""
    print("\n" + "=" * 60)
    print("测试快速渲染函数")
    print("=" * 60)
    
    try:
        content = render_prompt(
            "planner/attack_planning",
            {"target": "test.example.com"}
        )
        print(f"\n快速渲染结果 ({len(content)} 字符):")
        print(content[:400] + "...")
    except TemplateNotFoundError as e:
        print(f"模板未找到: {e}")


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("ClawAI Prompt管理系统测试")
    print("=" * 60)
    
    try:
        test_prompt_manager()
        test_render_planning()
        test_render_execution()
        test_render_verification()
        test_system_prompts()
        test_quick_render()
        
        print("\n" + "=" * 60)
        print("所有测试完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
