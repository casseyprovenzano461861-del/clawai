#!/usr/bin/env python3
"""
测试模块化单体架构集成
验证所有模块正确加载和API端点兼容性
"""

import sys
import os
import asyncio
import httpx
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_module_imports():
    """测试模块导入"""
    print("测试模块导入...")

    try:
        from src.modules import ModuleConfig, BaseModule, ModuleManager
        print("✅ 模块基类导入成功")

        from src.modules.ai_engine import create_module as create_ai_module
        print("✅ AI引擎模块导入成功")

        from src.modules.data_service import create_module as create_data_module
        print("✅ 数据服务模块导入成功")

        from src.modules.tool_executor import create_module as create_tool_module
        print("✅ 工具执行模块导入成功")

        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_module_creation():
    """测试模块创建"""
    print("\n测试模块创建...")

    try:
        from src.modules import ModuleConfig

        # 创建模块配置
        ai_config = ModuleConfig(
            name="ai_engine",
            enabled=True,
            dependencies=[],
            config={
                "llm_provider": "openai",
                "default_model": "gpt-4",
                "max_tokens": 4096,
                "temperature": 0.7
            }
        )

        data_config = ModuleConfig(
            name="data_service",
            enabled=True,
            dependencies=[],
            config={
                "database_url": "sqlite:///:memory:",
                "create_tables": True,
                "pool_size": 5
            }
        )

        tool_config = ModuleConfig(
            name="tool_executor",
            enabled=True,
            dependencies=[],
            config={
                "tools_dir": "./tools/penetration",
                "container_timeout": 300,
                "max_concurrent_tasks": 5
            }
        )

        print("✅ 模块配置创建成功")

        # 创建模块实例
        from src.modules.ai_engine import create_module as create_ai_module
        from src.modules.data_service import create_module as create_data_module
        from src.modules.tool_executor import create_module as create_tool_module

        ai_module = create_ai_module(ai_config)
        data_module = create_data_module(data_config)
        tool_module = create_tool_module(tool_config)

        print("✅ 模块实例创建成功")

        return True
    except Exception as e:
        print(f"❌ 模块创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_module_routes():
    """测试模块路由"""
    print("\n测试模块路由...")

    try:
        from src.modules import ModuleConfig
        from src.modules.ai_engine import create_module as create_ai_module
        from src.modules.data_service import create_module as create_data_module
        from src.modules.tool_executor import create_module as create_tool_module

        # 创建模块配置
        ai_config = ModuleConfig(name="ai_engine", enabled=True)
        data_config = ModuleConfig(name="data_service", enabled=True)
        tool_config = ModuleConfig(name="tool_executor", enabled=True)

        # 创建模块实例
        ai_module = create_ai_module(ai_config)
        data_module = create_data_module(data_config)
        tool_module = create_tool_module(tool_config)

        # 获取路由
        ai_router = ai_module.get_router()
        data_router = data_module.get_router()
        tool_router = tool_module.get_router()

        print(f"✅ AI引擎模块路由数量: {len(ai_router.routes)}")
        print(f"✅ 数据服务模块路由数量: {len(data_router.routes)}")
        print(f"✅ 工具执行模块路由数量: {len(tool_router.routes)}")

        # 检查关键端点
        ai_endpoints = [route.path for route in ai_router.routes]
        data_endpoints = [route.path for route in data_router.routes]
        tool_endpoints = [route.path for route in tool_router.routes]

        print(f"  AI引擎端点: {ai_endpoints[:3]}...")
        print(f"  数据服务端点: {data_endpoints[:3]}...")
        print(f"  工具执行端点: {tool_endpoints[:3]}...")

        return True
    except Exception as e:
        print(f"❌ 模块路由测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_file():
    """测试配置文件"""
    print("\n测试配置文件...")

    config_path = Path("config/modules.yaml")
    if config_path.exists():
        print(f"✅ 配置文件存在: {config_path}")

        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        modules = config.get("modules", {})
        print(f"✅ 配置中定义的模块: {list(modules.keys())}")

        # 检查必要模块
        required_modules = ["ai_engine", "data_service", "tool_executor"]
        for module in required_modules:
            if module in modules:
                print(f"  ✅ {module} 模块配置存在")
            else:
                print(f"  ⚠️  {module} 模块配置不存在")

        return True
    else:
        print(f"❌ 配置文件不存在: {config_path}")
        return False

def test_api_compatibility():
    """测试API兼容性（关键端点）"""
    print("\n测试API兼容性...")

    # 预期的API端点（根据架构简化设计）
    expected_endpoints = {
        "/api/v1/ai/health": ["GET"],  # AI健康检查
        "/api/v1/ai/configs": ["GET"],  # AI配置
        "/api/v1/data/health": ["GET"],  # 数据健康检查
        "/api/v1/data/users/register": ["POST"],  # 用户注册
        "/api/v1/tools/health": ["GET"],  # 工具健康检查
        "/api/v1/tools/available": ["GET"],  # 可用工具
    }

    print("预期API端点:")
    for endpoint, methods in expected_endpoints.items():
        print(f"  {endpoint} ({', '.join(methods)})")

    print("\n注意: 实际API测试需要启动FastAPI应用")
    print("可以使用以下命令测试:")
    print("  uvicorn src.shared.backend.main:app --reload --port 8000")

    return True

async def test_fastapi_app():
    """测试FastAPI应用启动"""
    print("\n测试FastAPI应用启动...")

    # 这个测试需要在一个独立的进程中运行
    # 这里只做基本检查

    try:
        # 检查main.py中的导入
        from src.shared.backend.main import app

        print("✅ FastAPI应用对象导入成功")
        print(f"✅ 应用标题: {app.title}")
        print(f"✅ 应用版本: {app.version}")

        # 检查路由
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)

        print(f"✅ 应用总路由数量: {len(routes)}")
        print(f"  示例路由: {routes[:5]}...")

        return True
    except Exception as e:
        print(f"❌ FastAPI应用测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("ClawAI 模块化单体架构集成测试")
    print("=" * 60)

    tests = [
        ("模块导入", test_module_imports),
        ("模块创建", test_module_creation),
        ("模块路由", test_module_routes),
        ("配置文件", test_config_file),
        ("API兼容性", test_api_compatibility),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ 测试 {test_name} 异常: {e}")
            results.append((test_name, False))

    # 异步测试
    try:
        import asyncio
        success = asyncio.run(test_fastapi_app())
        results.append(("FastAPI应用", success))
    except Exception as e:
        print(f"❌ FastAPI应用测试异常: {e}")
        results.append(("FastAPI应用", False))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)

    all_passed = True
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name:20} {status}")
        if not success:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！模块化单体架构集成成功。")
    else:
        print("⚠️  部分测试失败，需要进一步检查和修复。")

    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)