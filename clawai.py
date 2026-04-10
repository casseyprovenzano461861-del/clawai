#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI - AI驱动的智能安全评估系统
统一命令行工具 v2.0

使用方法:
  clawai [命令] [选项]

命令:
  dev         开发模式：启动后端 + 前端
  prod        生产模式：启动后端 + 前端
  backend     仅启动后端服务
  frontend    仅启动前端服务
  chat        AI 对话模式（默认）
  tui         TUI 图形界面模式
  scan        快速安全扫描
  status      查看系统状态
  tools       管理安全工具
  session     会话管理
  check       检查依赖和环境
  version     显示版本信息
  help        显示帮助信息

示例:
  clawai dev                  # 开发模式启动
  clawai chat -t example.com   # 带目标的对话模式
  clawai scan 192.168.1.1    # 快速扫描
  clawai backend --port 8000   # 后端端口 8000
  clawai status               # 查看状态
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Optional

# Windows 下强制 UTF-8 输出，避免中文/方框字符乱码
if os.name == 'nt':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# 启用 Windows ANSI 颜色支持
def _enable_ansi_colors() -> bool:
    """尝试启用 ANSI 颜色，返回是否成功"""
    if os.environ.get('NO_COLOR'):
        return False
    if os.name == 'nt':
        try:
            import colorama
            colorama.init(autoreset=False)
            return True
        except ImportError:
            # colorama 未安装时尝试直接启用 Windows VT 模式
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except Exception:
                return False
    return True

_ANSI_ENABLED = _enable_ansi_colors()

# 颜色输出（兼容 Windows 和 Unix）
class Colors:
    """终端颜色支持"""
    RED = '\033[91m' if _ANSI_ENABLED else ''
    GREEN = '\033[92m' if _ANSI_ENABLED else ''
    YELLOW = '\033[93m' if _ANSI_ENABLED else ''
    BLUE = '\033[94m' if _ANSI_ENABLED else ''
    MAGENTA = '\033[95m' if _ANSI_ENABLED else ''
    CYAN = '\033[96m' if _ANSI_ENABLED else ''
    WHITE = '\033[97m' if _ANSI_ENABLED else ''
    BOLD = '\033[1m' if _ANSI_ENABLED else ''
    DIM = '\033[2m' if _ANSI_ENABLED else ''
    END = '\033[0m' if _ANSI_ENABLED else ''

    # 组合样式
    SUCCESS = GREEN
    ERROR = RED
    WARNING = YELLOW
    INFO = CYAN
    PRIMARY = MAGENTA
    SECONDARY = BLUE


def print_banner():
    """打印欢迎横幅"""
    banner = f"""
{Colors.CYAN}{'='*70}{Colors.END}
{Colors.BOLD}{Colors.MAGENTA}
   ╔═══════════════════════════════════════════════════════════╗
   ║                                                             ║
   ║   ██████╗██╗      ██████╗ ██╗   ██╗██████╗                ║
   ║   ██╔════╝██║     ██╔═══██╗██║   ██║██╔══██╗               ║
   ║   ██║     ██║     ██║   ██║██║   ██║██║  ██║               ║
   ║   ██║     ██║     ██║   ██║██║   ██║██║  ██║               ║
   ║   ╚██████╗███████╗╚██████╔╝╚██████╔╝██████╔╝               ║
   ║    ╚═════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝                ║
   ║                                                             ║
   ║          AI驱动的智能安全评估系统 v2.0.0                   ║
   ║                                                             ║
   ╚═══════════════════════════════════════════════════════════╝
{Colors.END}
{Colors.CYAN}{'='*70}{Colors.END}
{Colors.INFO}  快速开始:{Colors.END}
  {Colors.SECONDARY}clawai dev{Colors.END}         # 开发模式（后端 + 前端）
  {Colors.SECONDARY}clawai chat{Colors.END}        # AI 对话模式
  {Colors.SECONDARY}clawai scan <目标>{Colors.END} # 快速扫描
{Colors.CYAN}{'='*70}{Colors.END}
"""
    print(banner)


def print_command(cmd: str, desc: str):
    """打印命令说明"""
    print(f"  {Colors.SECONDARY}{cmd:30s}{Colors.END} {Colors.DIM}{desc}{Colors.END}")


def print_success(msg: str):
    """打印成功消息"""
    print(f"  {Colors.GREEN}✓{Colors.END} {msg}")


def print_error(msg: str):
    """打印错误消息"""
    print(f"  {Colors.RED}✗{Colors.END} {msg}")


def print_warning(msg: str):
    """打印警告消息"""
    print(f"  {Colors.YELLOW}⚠{Colors.END} {msg}")


def print_info(msg: str):
    """打印信息消息"""
    print(f"  {Colors.CYAN}ℹ{Colors.END} {msg}")


# ---------------------------------------------------------------------------
# 服务管理（整合 start.py 功能）
# ---------------------------------------------------------------------------

def cmd_dev(args):
    """开发模式：启动后端 + 前端"""
    print_banner()
    print_info("启动开发环境...")

    import subprocess

    # 启动 start.py（带开发模式参数）
    try:
        proc = subprocess.Popen(
            [sys.executable, str(PROJECT_ROOT / "start.py"), "--mode", "dev"],
            cwd=str(PROJECT_ROOT)
        )
        print_success(f"开发环境已启动 (PID: {proc.pid})")
        print_info("按 Ctrl+C 停止服务")
        proc.wait()
    except KeyboardInterrupt:
        print_warning("\n正在停止开发环境...")
        proc.terminate()
        proc.wait()
        print_success("开发环境已停止")
    except Exception as e:
        print_error(f"启动失败: {e}")


def cmd_prod(args):
    """生产模式：启动后端 + 前端"""
    print_banner()
    print_info("启动生产环境...")

    import subprocess

    try:
        proc = subprocess.Popen(
            [sys.executable, str(PROJECT_ROOT / "start.py"), "--mode", "prod"],
            cwd=str(PROJECT_ROOT)
        )
        print_success(f"生产环境已启动 (PID: {proc.pid})")
        print_info("按 Ctrl+C 停止服务")
        proc.wait()
    except KeyboardInterrupt:
        print_warning("\n正在停止生产环境...")
        proc.terminate()
        proc.wait()
        print_success("生产环境已停止")
    except Exception as e:
        print_error(f"启动失败: {e}")


def cmd_backend(args):
    """仅启动后端服务"""
    print_banner()
    print_info("启动后端服务...")

    import subprocess

    cmd_parts = [sys.executable, str(PROJECT_ROOT / "start.py"), "--backend"]
    if args.port:
        cmd_parts.extend(["--backend-port", str(args.port)])
    if args.host:
        cmd_parts.extend(["--host", args.host])
    if args.reload:
        cmd_parts.append("--reload")

    try:
        proc = subprocess.Popen(cmd_parts, cwd=str(PROJECT_ROOT))
        print_success(f"后端服务已启动 (PID: {proc.pid})")
        print_info("按 Ctrl+C 停止服务")
        proc.wait()
    except KeyboardInterrupt:
        print_warning("\n正在停止后端服务...")
        proc.terminate()
        proc.wait()
        print_success("后端服务已停止")
    except Exception as e:
        print_error(f"启动失败: {e}")


def cmd_frontend(args):
    """仅启动前端服务"""
    print_banner()
    print_info("启动前端服务...")

    import subprocess

    cmd_parts = [sys.executable, str(PROJECT_ROOT / "start.py"), "--frontend"]
    if args.port:
        cmd_parts.extend(["--frontend-port", str(args.port)])

    try:
        proc = subprocess.Popen(cmd_parts, cwd=str(PROJECT_ROOT))
        print_success(f"前端服务已启动 (PID: {proc.pid})")
        print_info("按 Ctrl+C 停止服务")
        proc.wait()
    except KeyboardInterrupt:
        print_warning("\n正在停止前端服务...")
        proc.terminate()
        proc.wait()
        print_success("前端服务已停止")
    except Exception as e:
        print_error(f"启动失败: {e}")


# ---------------------------------------------------------------------------
# CLI 交互模式（整合 chat_cli.py 功能）
# ---------------------------------------------------------------------------

def cmd_chat(args):
    """AI 对话模式"""
    print_banner()

    # 初始化 ChatCLI
    from src.cli.chat_cli import ClawAIChatCLI

    config = {}
    if args.model:
        provider = "deepseek"
        if args.model.startswith("gpt-") or args.model.startswith("o1"):
            provider = "openai"
        elif args.model.startswith("claude-"):
            provider = "anthropic"
        config["llm"] = {"model_id": args.model, "provider": provider}

    chat_cli = ClawAIChatCLI(config)

    if args.target:
        chat_cli.set_target(args.target)
        print_success(f"目标已设置: {args.target}")

    # 快捷提示
    print()
    print_command("/help", "显示帮助")
    print_command("/nmap <目标>", "端口扫描")
    print_command("/status", "查看状态")
    print("")

    # 启动 REPL
    from src.cli.main import run_chat_mode
    asyncio.run(run_chat_mode(target=args.target, model=args.model))


def cmd_tui(args):
    """TUI 图形界面模式"""
    print_banner()
    print_info("启动 TUI 模式...")

    try:
        from src.cli.tui.app import run_tui
        asyncio.run(run_tui(target=args.target))
    except Exception as e:
        print_error(f"TUI 启动失败: {e}")
        print_info("降级到 REPL 模式...")
        cmd_chat(args)


def cmd_scan(args):
    """快速安全扫描"""
    print_banner()

    if not args.target:
        print_error("请指定扫描目标")
        print_info("用法: clawai scan <目标>")
        return

    print_info(f"开始扫描目标: {args.target}")

    from src.cli.chat_cli import ClawAIChatCLI
    chat_cli = ClawAIChatCLI()
    chat_cli.set_target(args.target)

    # 异步执行扫描
    async def _scan():
        response = await chat_cli.chat(f"扫描 {args.target}")
        print(f"\n{response}")

    asyncio.run(_scan())


# ---------------------------------------------------------------------------
# 系统管理命令
# ---------------------------------------------------------------------------

def cmd_status(args):
    """查看系统状态"""
    print_banner()
    print_info("系统状态检查...")

    import requests

    try:
        # 检查后端
        try:
            resp = requests.get("http://127.0.0.1:8000/health", timeout=3)
            if resp.status_code == 200:
                print_success("后端服务: 运行中 (http://127.0.0.1:8000)")
            else:
                print_warning(f"后端服务: 响应异常 ({resp.status_code})")
        except requests.exceptions.ConnectionError:
            print_error("后端服务: 未启动")

        # 检查前端
        try:
            resp = requests.get("http://localhost:5173", timeout=3)
            print_success("前端服务: 运行中 (http://localhost:5173)")
        except requests.exceptions.ConnectionError:
            print_warning("前端服务: 未启动")

        # 检查 Python 版本
        print_success(f"Python: {sys.version.split()[0]}")

        # 检查 API Key
        has_key = bool(os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY"))
        if has_key:
            print_success("API Key: 已配置")
        else:
            print_warning("API Key: 未配置（将使用模拟模式）")

    except ImportError:
        print_error("requests 模块未安装")
    except Exception as e:
        print_error(f"状态检查失败: {e}")


def cmd_tools(args):
    """管理安全工具"""
    print_banner()

    if args.action == "list":
        print_info("可用安全工具:")
        tools_dir = PROJECT_ROOT / "tools" / "penetration"
        if tools_dir.exists():
            for item in sorted(tools_dir.iterdir()):
                if item.is_dir():
                    print_command(f"  {item.name}", "")
        else:
            print_warning("工具目录不存在")
    elif args.action == "check":
        print_info("检查工具状态...")
        # TODO: 实现工具状态检查
        print_success("工具检查功能开发中")
    else:
        print_info("工具管理子命令:")
        print_command("  clawai tools list", "列出所有工具")
        print_command("  clawai tools check", "检查工具状态")


def cmd_session(args):
    """会话管理"""
    print_banner()

    from src.cli.chat_cli import ClawAIChatCLI

    if args.action == "list":
        print_info("已保存的会话:")
        sessions = ClawAIChatCLI.list_saved_sessions()
        for s in sessions:
            print_command(f"  {s['session_id'][:20]}", f"{s.get('target', '-')} | {s.get('updated_at', '')[:19]}")
    elif args.action == "load" and args.session_id:
        print_info(f"加载会话: {args.session_id}")
        # TODO: 实现会话加载
        print_warning("会话加载功能开发中")
    elif args.action == "export" and args.session_id:
        print_info(f"导出会话: {args.session_id}")
        # TODO: 实现会话导出
        print_warning("会话导出功能开发中")
    else:
        print_info("会话管理子命令:")
        print_command("  clawai session list", "列出所有会话")
        print_command("  clawai session load <id>", "加载指定会话")
        print_command("  clawai session export <id>", "导出指定会话")


def cmd_check(args):
    """检查依赖和环境"""
    print_banner()
    print_info("检查依赖和环境...")

    import subprocess

    issues = []

    # Python 版本
    if sys.version_info >= (3, 10):
        print_success(f"Python: {sys.version.split()[0]}")
    else:
        issues.append(f"Python >= 3.10（当前 {sys.version.split()[0]}）")

    # Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Node.js: {result.stdout.strip()}")
        else:
            issues.append("Node.js 未正确安装")
    except FileNotFoundError:
        issues.append("Node.js 未安装")

    # uvicorn
    try:
        result = subprocess.run(
            [sys.executable, "-m", "uvicorn", "--version"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print_success(f"uvicorn: {result.stdout.strip()}")
        else:
            issues.append("uvicorn 未安装（pip install uvicorn）")
    except Exception:
        issues.append("uvicorn 未安装")

    # 环境变量
    has_api_key = bool(os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY"))
    if has_api_key:
        print_success("API Key: 已配置")
    else:
        print_warning("API Key: 未配置（将使用模拟模式）")

    # 结果
    if issues:
        print()
        print_error("依赖检查失败:")
        for issue in issues:
            print(f"    ✗ {issue}")
        return False
    else:
        print_success("所有依赖正常")
        return True


def cmd_version(args):
    """显示版本信息"""
    print(f"""
{Colors.CYAN}ClawAI{Colors.END} v2.0.0
{Colors.DIM}AI驱动的智能安全评估系统{Colors.END}

{Colors.INFO}Python:{Colors.END}    {sys.version.split()[0]}
{Colors.INFO}Platform:{Colors.END}  {sys.platform}

{Colors.DIM}更多信息: https://github.com/your-org/clawai{Colors.END}
""")


def cmd_help(args):
    """显示帮助信息"""
    print_banner()
    print(f"""
{Colors.BOLD}{Colors.PRIMARY}命令列表{Colors.END}

{Colors.SECONDARY}服务管理:{Colors.END}
  clawai dev                    开发模式（后端 + 前端）
  clawai prod                   生产模式（后端 + 前端）
  clawai backend                仅启动后端服务
  clawai frontend               仅启动前端服务

{Colors.SECONDARY}交互模式:{Colors.END}
  clawai chat                  AI 对话模式
  clawai tui                   TUI 图形界面模式
  clawai scan <目标>            快速安全扫描

{Colors.SECONDARY}系统管理:{Colors.END}
  clawai status                查看系统状态
  clawai tools list             列出安全工具
  clawai session list           会话管理
  clawai check                 检查依赖和环境
  clawai version               显示版本信息

{Colors.SECONDARY}选项:{Colors.END}
  -t, --target <地址>         设置目标地址
  -m, --model <模型>          指定 AI 模型
  --host <地址>               后端绑定地址（默认 0.0.0.0）
  --port <端口>               服务端口（后端 8000/前端 5173）
  --reload                    后端自动重载（开发模式）
  -h, --help                  显示帮助信息
  -v, --version               显示版本信息

{Colors.DIM}示例:{Colors.END}
  {Colors.SECONDARY}clawai dev{Colors.END}                    # 开发模式启动
  {Colors.SECONDARY}clawai chat -t example.com{Colors.END}  # 带目标的对话
  {Colors.SECONDARY}clawai scan 192.168.1.1{Colors.END}   # 快速扫描
  {Colors.SECONDARY}clawai status{Colors.END}               # 查看状态

{Colors.INFO}更多信息: https://github.com/your-org/clawai{Colors.END}
""")


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(
        prog="clawai",
        description="ClawAI - AI驱动的智能安全评估系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False
    )

    # 全局选项
    parser.add_argument("-v", "--version", action="store_true", help="显示版本信息")
    parser.add_argument("-h", "--help", action="store_true", help="显示帮助信息")

    # 服务管理命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # dev 命令
    dev_parser = subparsers.add_parser("dev", help="开发模式（后端 + 前端）")
    dev_parser.add_argument("--host", default="0.0.0.0", help="后端绑定地址")
    dev_parser.add_argument("--backend-port", type=int, default=8000, help="后端端口")
    dev_parser.add_argument("--frontend-port", type=int, default=5173, help="前端端口")

    # prod 命令
    prod_parser = subparsers.add_parser("prod", help="生产模式（后端 + 前端）")
    prod_parser.add_argument("--host", default="0.0.0.0", help="后端绑定地址")
    prod_parser.add_argument("--backend-port", type=int, default=8000, help="后端端口")
    prod_parser.add_argument("--frontend-port", type=int, default=5173, help="前端端口")

    # backend 命令
    backend_parser = subparsers.add_parser("backend", help="仅启动后端服务")
    backend_parser.add_argument("--host", default="0.0.0.0", help="后端绑定地址")
    backend_parser.add_argument("-p", "--port", type=int, default=8000, help="后端端口")
    backend_parser.add_argument("--reload", action="store_true", help="自动重载（开发模式）")

    # frontend 命令
    frontend_parser = subparsers.add_parser("frontend", help="仅启动前端服务")
    frontend_parser.add_argument("-p", "--port", type=int, default=5173, help="前端端口")

    # chat 命令
    chat_parser = subparsers.add_parser("chat", help="AI 对话模式")
    chat_parser.add_argument("-t", "--target", help="设置目标地址")
    chat_parser.add_argument("-m", "--model", help="指定 AI 模型")

    # tui 命令
    tui_parser = subparsers.add_parser("tui", help="TUI 图形界面模式")
    tui_parser.add_argument("-t", "--target", help="设置目标地址")

    # scan 命令
    scan_parser = subparsers.add_parser("scan", help="快速安全扫描")
    scan_parser.add_argument("target", help="扫描目标")
    scan_parser.add_argument("--profile", choices=["quick", "standard", "deep"], default="standard", help="扫描配置")

    # tools 命令
    tools_parser = subparsers.add_parser("tools", help="管理安全工具")
    tools_parser.add_argument("action", choices=["list", "check"], help="操作类型")

    # session 命令
    session_parser = subparsers.add_parser("session", help="会话管理")
    session_parser.add_argument("action", choices=["list", "load", "export"], help="操作类型")
    session_parser.add_argument("session_id", nargs="?", help="会话 ID")

    # check 命令
    check_parser = subparsers.add_parser("check", help="检查依赖和环境")

    # status 命令
    status_parser = subparsers.add_parser("status", help="查看系统状态")

    # version 命令
    version_parser = subparsers.add_parser("version", help="显示版本信息")

    # 解析参数
    args = parser.parse_args()

    # 全局选项优先
    if args.version:
        cmd_version(args)
        return 0
    if args.help:
        cmd_help(args)
        return 0

    # 无命令时，显示帮助
    if not args.command:
        cmd_help(args)
        return 0

    # 命令分发
    commands = {
        "dev": cmd_dev,
        "prod": cmd_prod,
        "backend": cmd_backend,
        "frontend": cmd_frontend,
        "chat": cmd_chat,
        "tui": cmd_tui,
        "scan": cmd_scan,
        "status": cmd_status,
        "tools": cmd_tools,
        "session": cmd_session,
        "check": cmd_check,
        "version": cmd_version,
        "help": cmd_help,
    }

    handler = commands.get(args.command)
    if handler:
        try:
            handler(args)
            return 0
        except KeyboardInterrupt:
            print_warning("\n操作已取消")
            return 130
        except Exception as e:
            print_error(f"命令执行失败: {e}")
            return 1
    else:
        print_error(f"未知命令: {args.command}")
        cmd_help(args)
        return 1


if __name__ == "__main__":
    sys.exit(main())
