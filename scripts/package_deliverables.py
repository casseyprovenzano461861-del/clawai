# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
ClawAI 交付物打包脚本（Python版本）
"""

import os
import shutil
from datetime import datetime

def main():
    """主函数"""
    print("=" * 60)
    print("ClawAI 比赛交付物打包")
    print("=" * 60)

    # 创建打包目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"ClawAI_Deliverables_{timestamp}"
    package_dir = os.path.join(".", package_name)

    print(f"创建打包目录: {package_dir}")

    # 检查并创建目录
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir)

    # 必须交付物列表
    mandatory_files = [
        "non_interactive_demo.py",
        "competition_demo.py",
        "start.bat",
        "config.py",
        "docker-compose.yml",
        "Dockerfile",
        "presentation_outline.md",
        "emergency_plan.md",
        "tests/test_ai_core_functionality.py",
        "README.md",
        "README_QUICKSTART.md"
    ]

    # 复制文件
    print("复制必须交付物...")
    for file_path in mandatory_files:
        if os.path.exists(file_path):
            dest_dir = os.path.join(package_dir, os.path.dirname(file_path))
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            shutil.copy2(file_path, os.path.join(package_dir, file_path))
            print(f"  [完成] {file_path}")
        else:
            print(f"  [缺失] {file_path} (缺失)")

    # 创建交付物清单
    readme_path = os.path.join(package_dir, "DELIVERABLES_README.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("ClawAI 比赛交付物清单\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"打包时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("核心交付物:\n")
        f.write("1. non_interactive_demo.py - 非交互式演示脚本\n")
        f.write("2. competition_demo.py - 比赛演示脚本\n")
        f.write("3. 测试文件 - AI核心功能测试\n")
        f.write("4. 配置文件和部署脚本\n")
        f.write("5. 演示材料和应急预案\n\n")
        f.write("使用说明:\n")
        f.write("1. 启动演示: 运行 start.bat\n")
        f.write("2. 运行AI测试: python tests/test_ai_core_functionality.py\n")
        f.write("3. Docker部署: docker-compose up\n")

    print(f"\n打包完成!")
    print(f"打包目录: {package_dir}")
    print("包含文件列表:")
    for root, dirs, files in os.walk(package_dir):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, package_dir)
            print(f"  - {rel_path}")

    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n打包被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n打包过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
