#!/usr/bin/env python3
"""
测试/attack端点是否工作
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import asyncio
import uvicorn
from fastapi import FastAPI
import requests
import json

async def test_attack_endpoint():
    """测试攻击端点"""
    print("=" * 60)
    print("测试 ClawAI /attack 端点")
    print("=" * 60)

    # 导入应用
    try:
        from src.shared.backend.main import app
        print("[✓] 成功导入FastAPI应用")
    except Exception as e:
        print(f"[✗] 导入应用失败: {e}")
        return False

    # 启动测试服务器
    import threading
    from uvicorn import Config, Server

    config = Config(app=app, host="127.0.0.1", port=8001, log_level="warning")
    server = Server(config)

    # 在后台线程中启动服务器
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    # 等待服务器启动
    import time
    time.sleep(3)

    try:
        # 测试/attack端点
        test_payload = {
            "target": "example.com",
            "use_real": False,  # 使用模拟模式避免工具执行问题
            "rule_engine_mode": True
        }

        print(f"\n发送测试请求到 http://127.0.0.1:8001/attack")
        print(f"请求负载: {json.dumps(test_payload, indent=2)}")

        response = requests.post(
            "http://127.0.0.1:8001/attack",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        print(f"\n响应状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"[✓] /attack端点工作正常")
            print(f"响应内容:")
            print(f"  - 目标: {result.get('target')}")
            print(f"  - 执行模式: {result.get('execution_mode')}")
            print(f"  - 攻击链步骤: {len(result.get('attack_chain', []))}")
            print(f"  - 消息: {result.get('message')}")
            return True
        else:
            print(f"[✗] /attack端点返回错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False

    except Exception as e:
        print(f"[✗] 测试请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 停止服务器
        server.should_exit = True
        server_thread.join(timeout=5)

if __name__ == "__main__":
    success = asyncio.run(test_attack_endpoint())
    sys.exit(0 if success else 1)