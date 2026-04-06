#!/usr/bin/env python3
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

# 设置环境变量
os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_URL"] = f"sqlite:///{project_root}/data/databases/clawai.db"
os.environ["TOOLS_DIR"] = os.path.join(project_root, "tools", "penetration")
os.environ["JWT_SECRET_KEY"] = "test"

print("Testing import of src.shared.backend.main...")
try:
    from src.shared.backend import main
    print("Import successful!")
    print(f"App object: {main.app}")
except Exception as e:
    print(f"Import failed with error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()