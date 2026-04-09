#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI 命令行工具

使用方法:
  python clawai.py [命令] [参数]

命令:
  chat      AI对话模式（默认）
  scan      执行安全扫描
  tools     管理安全工具
  status    查看服务状态
  start     启动ClawAI服务
  help      显示帮助信息

示例:
  python clawai.py                    # 进入AI对话模式
  python clawai.py chat -t example.com  # 带目标的对话模式
  python clawai.py scan 192.168.1.1   # 快速扫描
  python clawai.py tools list         # 列出工具
  python clawai.py status             # 查看状态
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """主入口 - 委托给 Click CLI"""
    try:
        from src.cli.main import cli
        cli()
    except ImportError as e:
        # 如果新CLI不可用，回退到旧版
        print(f"警告: Click CLI模块不可用 ({e})，使用旧版...")
        _legacy_main()


def _legacy_main():
    """旧版CLI（回退用）"""
    import subprocess
    import argparse
    import requests

    def print_banner():
        print("""
╔═══════════════════════════════════════════╗
║            ClawAI 命令行工具             ║
╚═══════════════════════════════════════════╝
""")

    def start_service():
        print("启动ClawAI服务...")
        if sys.platform.startswith('win32'):
            subprocess.Popen(['cmd', '/c', 'start.bat'])
        else:
            subprocess.Popen(['bash', 'start.sh'])
        print("服务启动中，请稍候...")
        print("后端服务将运行在: http://localhost:5000")
        print("前端服务将运行在: http://localhost:5173")

    def execute_scan(target):
        print(f"执行安全扫描，目标: {target}")
        try:
            response = requests.post(
                'http://localhost:5000/api/v1/attack',
                json={'target': target, 'use_real': False},
                timeout=300
            )
            if response.status_code == 200:
                result = response.json()
                print(f"\n扫描完成！目标: {result.get('target')}")
            else:
                print(f"扫描失败: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("错误: 无法连接到后端服务")
        except Exception as e:
            print(f"错误: {str(e)}")

    def manage_tools(action):
        try:
            if action == 'list':
                response = requests.get('http://localhost:5000/api/v1/tools')
                if response.status_code == 200:
                    tools = response.json()
                    print("\n可用工具:")
                    for tool in tools:
                        print(f"  - {tool['name']}: {tool.get('description', '')}")
        except:
            print("无法连接到后端服务")

    def check_status():
        try:
            response = requests.get('http://localhost:5000/api/v1/health', timeout=5)
            if response.status_code == 200:
                print("后端服务: 运行正常")
            else:
                print("后端服务: 无法访问")
        except:
            print("后端服务: 未启动")

    print_banner()
    parser = argparse.ArgumentParser(description='ClawAI 命令行工具')
    parser.add_argument('command', nargs='?', default='help', help='命令')
    parser.add_argument('args', nargs='*', help='命令参数')
    args = parser.parse_args()

    command = args.command.lower() if args.command else 'help'

    if command == 'start':
        start_service()
    elif command == 'scan':
        if args.args:
            execute_scan(args.args[0])
        else:
            print("错误: 缺少目标参数")
    elif command == 'tools':
        manage_tools(args.args[0] if args.args else 'list')
    elif command == 'status':
        check_status()
    elif command in ['help', '--help', '-h']:
        print(__doc__)
    else:
        print(f"未知命令: {command}")
        print("可用命令: chat, scan, tools, status, start, help")


if __name__ == '__main__':
    main()
