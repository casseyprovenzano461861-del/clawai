#!/usr/bin/env python3
"""
ClawAI API 测试脚本
用于验证重构后的API功能
"""

import requests
import json
import time
import sys

# API基础URL - 微服务架构使用api-gateway端口8080
BASE_URL = "http://localhost:8080"


def test_health_check():
    """测试健康检查"""
    print("1. 测试健康检查接口...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"   错误: {e}")
        return False


def test_tools_list():
    """测试工具列表接口"""
    print("\n2. 测试工具列表接口...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/tools/available", timeout=5)
        print(f"   状态码: {response.status_code}")
        data = response.json()
        print(f"   工具数量: {data.get('count', 0)}")
        print(f"   工具列表: {data.get('tools', [])}")
        return response.status_code == 200
    except Exception as e:
        print(f"   错误: {e}")
        return False


def test_scan_function():
    """测试AI分析功能"""
    print("\n3. 测试AI分析功能接口...")
    try:
        # 测试LLM配置列表端点
        response = requests.get(f"{BASE_URL}/api/v1/llm/configs", timeout=5)
        print(f"   状态码: {response.status_code}")
        data = response.json()
        print(f"   配置数量: {data.get('count', 0)}")
        configs = data.get('configs', [])
        config_names = [c.get('name', '') for c in configs]
        print(f"   配置名称: {config_names}")
        return response.status_code == 200
    except Exception as e:
        print(f"   错误: {e}")
        return False


def test_status_endpoint():
    """测试技能列表接口"""
    print("\n4. 测试技能列表接口...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/skills", timeout=5)
        print(f"   状态码: {response.status_code}")
        data = response.json()
        print(f"   技能数量: {data.get('count', 0)}")
        categories = data.get('categories', {})
        if isinstance(categories, dict):
            print(f"   技能类别: {list(categories.keys())}")
        else:
            print(f"   技能类别: {categories}")
        return response.status_code == 200
    except Exception as e:
        print(f"   错误: {e}")
        return False


def test_api_docs():
    """测试API文档接口"""
    print("\n5. 测试API文档接口...")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        print(f"   状态码: {response.status_code}")
        # FastAPI文档返回HTML，检查状态码即可
        return response.status_code == 200
    except Exception as e:
        print(f"   错误: {e}")
        return False


def test_tool_manager():
    """测试工具管理器"""
    print("\n6. 测试工具管理器...")
    try:
        import sys
        sys.path.append('.')
        from backend.core.tool_manager import ToolManager
        
        manager = ToolManager()
        
        # 获取可用工具
        tools = manager.get_available_tools()
        print(f"   加载工具数量: {len(tools)}")
        
        # 健康检查
        health = manager.health_check()
        print(f"   工具健康状态: {health.get('status', 'N/A')}")
        print(f"   可用工具比例: {health.get('availability_rate', 0)}%")
        
        return len(tools) > 0
    except Exception as e:
        print(f"   错误: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("ClawAI API 功能测试")
    print("=" * 60)
    
    # 等待API服务器启动
    print("等待API服务器启动...")
    time.sleep(2)
    
    # 执行测试
    tests = [
        test_health_check,
        test_tools_list,
        test_scan_function,
        test_status_endpoint,
        test_api_docs,
        test_tool_manager
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"测试异常: {e}")
            results.append(False)
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, result in enumerate(results):
        status = "✓ 通过" if result else "✗ 失败"
        print(f"测试 {i+1}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！ClawAI API 功能正常。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查API服务器状态。")
        return 1


if __name__ == "__main__":
    sys.exit(main())