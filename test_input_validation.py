#!/usr/bin/env python3
"""
测试输入验证集成
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.shared.backend.schemas.attack import AttackRequest
from src.shared.backend.schemas.tool import ToolExecuteRequest
from src.shared.backend.security.input_validation import get_secure_validator


def test_attack_request_validation():
    """测试AttackRequest验证"""
    print("=" * 80)
    print("测试 AttackRequest 输入验证")
    print("=" * 80)

    # 正常用例
    print("\n1. 正常用例:")
    try:
        request = AttackRequest(
            target="https://example.com",
            use_real=True,
            rule_engine_mode=True,
            timeout=300,
            parameters={"param1": "value1"}
        )
        print(f"  ✅ 正常请求创建成功: target={request.target}")
    except Exception as e:
        print(f"  ❌ 正常请求失败: {e}")

    # 恶意用例
    malicious_cases = [
        {
            "name": "XSS攻击",
            "target": "<script>alert('xss')</script>",
            "use_real": True,
            "rule_engine_mode": True,
            "timeout": 300,
            "parameters": {}
        },
        {
            "name": "SQL注入",
            "target": "example.com' OR '1'='1",
            "use_real": True,
            "rule_engine_mode": True,
            "timeout": 300,
            "parameters": {}
        },
        {
            "name": "命令注入",
            "target": "example.com | cat /etc/passwd",
            "use_real": True,
            "rule_engine_mode": True,
            "timeout": 300,
            "parameters": {}
        },
        {
            "name": "路径遍历",
            "target": "../../../etc/passwd",
            "use_real": True,
            "rule_engine_mode": True,
            "timeout": 300,
            "parameters": {}
        },
        {
            "name": "恶意参数",
            "target": "https://example.com",
            "use_real": True,
            "rule_engine_mode": True,
            "timeout": 300,
            "parameters": {"cmd": "rm -rf /"}
        }
    ]

    print("\n2. 恶意用例 (应该失败):")
    for case in malicious_cases:
        try:
            request = AttackRequest(**case)
            print(f"  ❌ {case['name']}: 应该失败但通过了: target={request.target}")
        except Exception as e:
            print(f"  ✅ {case['name']}: 正确被拒绝: {str(e)[:80]}...")


def test_tool_execute_request_validation():
    """测试ToolExecuteRequest验证"""
    print("\n" + "=" * 80)
    print("测试 ToolExecuteRequest 输入验证")
    print("=" * 80)

    # 正常用例
    print("\n1. 正常用例:")
    try:
        request = ToolExecuteRequest(
            tool="nmap",
            target="192.168.1.1",
            parameters={"ports": "80,443"},
            timeout=60,
            use_docker=True
        )
        print(f"  ✅ 正常请求创建成功: tool={request.tool}, target={request.target}")
    except Exception as e:
        print(f"  ❌ 正常请求失败: {e}")

    # 恶意用例
    malicious_cases = [
        {
            "name": "XSS攻击",
            "tool": "nmap",
            "target": "<script>alert(1)</script>",
            "parameters": {},
            "timeout": 60,
            "use_docker": True
        },
        {
            "name": "命令注入",
            "tool": "nmap",
            "target": "127.0.0.1; rm -rf /",
            "parameters": {},
            "timeout": 60,
            "use_docker": True
        },
        {
            "name": "恶意工具名",
            "tool": "rm -rf /",
            "target": "127.0.0.1",
            "parameters": {},
            "timeout": 60,
            "use_docker": True
        },
        {
            "name": "恶意参数",
            "tool": "nmap",
            "target": "192.168.1.1",
            "parameters": {"command": "cat /etc/passwd"},
            "timeout": 60,
            "use_docker": True
        }
    ]

    print("\n2. 恶意用例 (应该失败):")
    for case in malicious_cases:
        try:
            request = ToolExecuteRequest(**case)
            print(f"  ❌ {case['name']}: 应该失败但通过了: tool={request.tool}, target={request.target}")
        except Exception as e:
            print(f"  ✅ {case['name']}: 正确被拒绝: {str(e)[:80]}...")


def test_secure_validator_directly():
    """直接测试安全验证器"""
    print("\n" + "=" * 80)
    print("直接测试安全验证器")
    print("=" * 80)

    validator = get_secure_validator()

    test_cases = [
        ("正常目标", "https://example.com", "target"),
        ("XSS攻击", "<script>alert(1)</script>", "target"),
        ("SQL注入", "admin' OR '1'='1", "target"),
        ("命令注入", "127.0.0.1 | rm -rf /", "command"),
        ("正常命令", "nmap -sV 127.0.0.1", "command"),
    ]

    for name, value, input_type in test_cases:
        if input_type == "target":
            result = validator.validate_target(value)
        elif input_type == "command":
            result = validator.validate_command(value)

        status = "✅" if result.is_valid else "❌"
        print(f"  {status} {name}: {value[:40]:40} -> {result.message}")
        if result.detected_threats:
            print(f"       威胁: {result.detected_threats}")


def main():
    """主测试函数"""
    print("输入验证集成测试")
    print("=" * 80)

    try:
        test_secure_validator_directly()
        test_attack_request_validation()
        test_tool_execute_request_validation()

        print("\n" + "=" * 80)
        print("测试完成!")
        return True

    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)