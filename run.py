#!/usr/bin/env python3
"""
ClawAI 启动脚本 (新结构版本)
"""

import os
import sys
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 设置环境变量
os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_URL"] = f"sqlite:///{project_root / 'data' / 'databases' / 'clawai.db'}"
os.environ["TOOLS_DIR"] = str(project_root / "tools" / "penetration")
os.environ["JWT_SECRET_KEY"] = "your-secret-key-change-this-in-production"

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="启动 ClawAI 应用 (新结构)")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    parser.add_argument("--reload", action="store_true", help="启用热重载")

    args = parser.parse_args()

    print("=" * 60)
    print("ClawAI - 智能安全评估系统 (新结构)")
    print("=" * 60)
    print(f"版本: 2.0.0 (激进重构版本)")
    print(f"项目根目录: {project_root}")
    print(f"环境: {os.getenv('ENVIRONMENT')}")
    print(f"数据库: {os.getenv('DATABASE_URL')}")
    print(f"工具目录: {os.getenv('TOOLS_DIR')}")
    print()
    print(f"启动服务器: http://{args.host}:{args.port}")
    print(f"API文档: http://{args.host}:{args.port}/docs")
    print(f"健康检查: http://{args.host}:{args.port}/health")
    print(f"工具列表: http://{args.host}:{args.port}/tools")
    print("=" * 60)
    print()

    uvicorn.run(
        "src.shared.backend.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )