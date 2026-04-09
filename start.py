#!/usr/bin/env python3
"""
ClawAI 统一启动脚本
支持一键启动后端、前端或全部服务

增强特性：
- 自动加载 .env 文件（无需额外依赖）
- 启动前检测端口占用，冲突时自动选择下一个可用端口
- 后端健康检查就绪后再启动前端
- 彩色进度输出
"""

import os
import sys
import signal
import socket
import subprocess
import argparse
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 颜色输出
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_banner():
    """打印启动横幅"""
    banner = f"""
{Colors.CYAN}{'='*60}{Colors.END}
{Colors.BOLD}{Colors.MAGENTA}   ██████╗██╗      ██████╗ ██╗   ██╗██████╗ 
  ██╔════╝██║     ██╔═══██╗██║   ██║██╔══██╗
  ██║     ██║     ██║   ██║██║   ██║██║  ██║
  ██║     ██║     ██║   ██║██║   ██║██║  ██║
  ╚██████╗███████╗╚██████╔╝╚██████╔╝██████╔╝
   ╚═════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝ {Colors.END}
{Colors.CYAN}{'='*60}{Colors.END}
{Colors.GREEN}   AI驱动的智能安全评估系统 v2.0.0{Colors.END}
{Colors.CYAN}{'='*60}{Colors.END}
"""
    print(banner)


def print_service(name: str, url: str, status: str = "启动中"):
    """打印服务状态"""
    status_color = Colors.GREEN if status == "运行中" else Colors.YELLOW
    print(f"  {Colors.BLUE}[{name}]{Colors.END} {url} {status_color}{status}{Colors.END}")


def print_step(msg: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}▶ {msg}{Colors.END}")


def print_ok(msg: str):
    print(f"  {Colors.GREEN}✓{Colors.END} {msg}")


def print_warn(msg: str):
    print(f"  {Colors.YELLOW}⚠{Colors.END} {msg}")


def print_err(msg: str):
    print(f"  {Colors.RED}✗{Colors.END} {msg}")


# ---------------------------------------------------------------------------
# .env 加载（无依赖）
# ---------------------------------------------------------------------------

def load_dotenv(env_file: Path) -> int:
    """解析 .env 文件并写入 os.environ（已有变量不覆盖）。返回加载条数。"""
    if not env_file.exists():
        return 0
    count = 0
    with open(env_file, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
                count += 1
    return count


# ---------------------------------------------------------------------------
# 端口检测
# ---------------------------------------------------------------------------

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """检测端口是否已被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def find_free_port(start: int, max_tries: int = 20) -> int:
    """从 start 开始向上查找第一个空闲端口，找不到则返回 start"""
    for port in range(start, start + max_tries):
        if not is_port_in_use(port):
            return port
    return start


def resolve_port(requested: int, name: str, auto: bool) -> int:
    """检查端口是否可用；占用时若 auto=True 自动选下一个，否则报错退出"""
    if not is_port_in_use(requested):
        return requested
    if auto:
        free = find_free_port(requested + 1)
        print_warn(f"{name} 端口 {requested} 已被占用，自动切换到 {free}")
        return free
    print_err(f"{name} 端口 {requested} 已被占用，用 --{name.lower().replace(' ', '-')}-port 指定其他端口，或加 --auto-port 自动选择")
    sys.exit(1)


# ---------------------------------------------------------------------------
# 后端健康检查
# ---------------------------------------------------------------------------

def wait_for_backend(host: str, port: int, timeout: int = 30) -> bool:
    """等待后端健康检查接口就绪，最多等待 timeout 秒"""
    url = f"http://{host if host != '0.0.0.0' else '127.0.0.1'}:{port}/health"
    deadline = time.time() + timeout
    dots = 0
    print(f"  {Colors.YELLOW}等待后端就绪", end="", flush=True)
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status < 500:
                    print(f" {Colors.GREEN}就绪！{Colors.END}")
                    return True
        except Exception:
            pass
        print(".", end="", flush=True)
        dots += 1
        time.sleep(1)
    print(f" {Colors.RED}超时{Colors.END}")
    return False


# ---------------------------------------------------------------------------
# 命令执行
# ---------------------------------------------------------------------------

def run_command(cmd, cwd: str = None, env: dict = None) -> subprocess.Popen:
    """运行命令并返回进程（支持列表或字符串）"""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    use_shell = isinstance(cmd, str)
    return subprocess.Popen(
        cmd,
        cwd=cwd or str(PROJECT_ROOT),
        env=full_env,
        shell=use_shell,
    )


# ---------------------------------------------------------------------------
# 服务管理器
# ---------------------------------------------------------------------------

class ServiceManager:
    """服务管理器"""

    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.setup_signal_handlers()

    def setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self, signum=None, frame=None):
        print(f"\n{Colors.YELLOW}正在关闭所有服务...{Colors.END}")
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
        print(f"{Colors.GREEN}所有服务已关闭{Colors.END}")
        sys.exit(0)

    def add_process(self, proc: subprocess.Popen):
        self.processes.append(proc)

    def wait(self):
        for proc in self.processes:
            proc.wait()


# ---------------------------------------------------------------------------
# 后端启动
# ---------------------------------------------------------------------------

def start_backend(args) -> Optional[subprocess.Popen]:
    """启动后端服务"""
    print_step("启动后端服务")

    backend_cwd = str(PROJECT_ROOT / "src" / "shared")

    for subdir in ["data/databases", "static", "logs"]:
        Path(backend_cwd, subdir).mkdir(parents=True, exist_ok=True)

    extra_paths = os.pathsep.join([
        str(PROJECT_ROOT),
        str(PROJECT_ROOT / "src" / "shared"),
        str(PROJECT_ROOT / "src"),
    ])
    python_path = extra_paths
    if os.environ.get("PYTHONPATH"):
        python_path = extra_paths + os.pathsep + os.environ["PYTHONPATH"]

    env = {
        "PYTHONPATH": python_path,
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
        "DATABASE_URL": os.getenv("DATABASE_URL", "sqlite:///./data/databases/clawai.db"),
        "TOOLS_DIR": os.getenv("TOOLS_DIR", str(PROJECT_ROOT / "tools" / "penetration")),
        "JWT_SECRET_KEY": os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key-not-for-production"),
        "SECRET_KEY": os.getenv("SECRET_KEY", "dev-secret-key-not-for-production"),
    }

    cmd = [
        sys.executable, "-m", "uvicorn",
        "backend.main:app",
        "--host", args.host,
        "--port", str(args.backend_port),
    ]
    if args.mode == "dev":
        cmd.append("--reload")

    proc = run_command(cmd, cwd=backend_cwd, env=env)
    print_service("后端 API", f"http://127.0.0.1:{args.backend_port}")
    print_service("API 文档", f"http://127.0.0.1:{args.backend_port}/docs")
    return proc


# ---------------------------------------------------------------------------
# 前端启动
# ---------------------------------------------------------------------------

def start_frontend(args) -> Optional[subprocess.Popen]:
    """启动前端服务"""
    print_step("启动前端服务")

    frontend_dir = PROJECT_ROOT / "frontend"

    if not frontend_dir.exists():
        print_err("前端目录不存在")
        return None

    if not (frontend_dir / "node_modules").exists():
        print_warn("node_modules 不存在，正在安装依赖...")
        install_proc = run_command("npm install", cwd=str(frontend_dir))
        install_proc.wait()
        if install_proc.returncode != 0:
            print_err("npm install 失败")
            return None
        print_ok("前端依赖安装完成")

    cmd = "npm run dev" if args.mode == "dev" else "npm run build && npm run preview"
    proc = run_command(cmd, cwd=str(frontend_dir))
    print_service("前端 UI", f"http://localhost:{args.frontend_port}")
    return proc


# ---------------------------------------------------------------------------
# 依赖检查
# ---------------------------------------------------------------------------

def check_dependencies() -> bool:
    """检查依赖"""
    print_step("检查依赖")
    issues = []

    # Python 版本
    if sys.version_info < (3, 10):
        issues.append(f"Python >= 3.10（当前 {sys.version.split()[0]}）")
    else:
        print_ok(f"Python {sys.version.split()[0]}")

    # Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print_ok(f"Node.js {result.stdout.strip()}")
        else:
            issues.append("Node.js 未安装")
    except FileNotFoundError:
        issues.append("Node.js 未安装")

    # uvicorn
    try:
        result = subprocess.run(
            [sys.executable, "-m", "uvicorn", "--version"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print_ok(f"uvicorn {result.stdout.strip()}")
        else:
            issues.append("uvicorn 未安装（pip install uvicorn）")
    except Exception:
        issues.append("uvicorn 未安装")

    # 目录
    for subdir in ["data/databases", "static", "logs"]:
        d = PROJECT_ROOT / "src" / "shared" / subdir
        d.mkdir(parents=True, exist_ok=True)
    print_ok("运行时目录已就绪")

    if issues:
        print(f"\n{Colors.RED}依赖检查失败:{Colors.END}")
        for issue in issues:
            print_err(issue)
        return False

    print_ok("所有依赖正常")
    return True


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ClawAI 统一启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python start.py                  # 启动后端 + 前端（默认）
  python start.py --backend        # 仅启动后端
  python start.py --frontend       # 仅启动前端
  python start.py --mode prod      # 生产模式
  python start.py --check          # 仅检查依赖
  python start.py --no-wait        # 不等待后端就绪直接启前端
        """
    )
    parser.add_argument("--backend", action="store_true", help="仅启动后端服务")
    parser.add_argument("--frontend", action="store_true", help="仅启动前端服务")
    parser.add_argument("--mode", choices=["dev", "prod"], default="dev", help="运行模式（默认 dev）")
    parser.add_argument("--host", default="0.0.0.0", help="后端绑定地址（默认 0.0.0.0）")
    parser.add_argument("--backend-port", type=int, default=8000, help="后端端口（默认 8000）")
    parser.add_argument("--frontend-port", type=int, default=5173, help="前端端口（默认 5173）")
    parser.add_argument("--check", action="store_true", help="仅检查依赖")
    parser.add_argument("--no-check", action="store_true", help="跳过依赖检查")
    parser.add_argument("--no-wait", action="store_true", help="不等待后端健康检查就绪")
    parser.add_argument("--wait-timeout", type=int, default=30, help="等待后端就绪超时秒数（默认 30）")
    parser.add_argument("--env-file", default=".env", help=".env 文件路径（默认 .env）")
    parser.add_argument("--auto-port", action="store_true", help="端口冲突时自动选择下一个可用端口")
    args = parser.parse_args()

    print_banner()

    # 加载 .env
    env_path = PROJECT_ROOT / args.env_file
    n = load_dotenv(env_path)
    if n > 0:
        print_ok(f"已从 {args.env_file} 加载 {n} 个环境变量")
    elif env_path.exists():
        print_warn(f"{args.env_file} 存在但无新变量（可能已全部设置）")
    else:
        print_warn(f"{args.env_file} 不存在，使用默认配置")

    # 仅检查依赖
    if args.check:
        check_dependencies()
        return

    if not args.no_check and not check_dependencies():
        sys.exit(1)

    start_all = not args.backend and not args.frontend
    start_backend_flag = start_all or args.backend
    start_frontend_flag = start_all or args.frontend

    # 端口冲突检测（支持自动选择）
    print_step("检查端口")
    auto = args.auto_port
    if start_backend_flag:
        args.backend_port = resolve_port(args.backend_port, "后端", auto)
        print_ok(f"后端端口 {args.backend_port} 可用")
    if start_frontend_flag:
        args.frontend_port = resolve_port(args.frontend_port, "前端", auto)
        print_ok(f"前端端口 {args.frontend_port} 可用")

    svc_manager = ServiceManager()

    # 启动后端
    if start_backend_flag:
        proc = start_backend(args)
        if proc:
            svc_manager.add_process(proc)
        else:
            print_err("后端启动失败")
            sys.exit(1)

    # 等待后端就绪后再启动前端
    if start_backend_flag and start_frontend_flag and not args.no_wait:
        ready = wait_for_backend(args.host, args.backend_port, timeout=args.wait_timeout)
        if not ready:
            print_warn("后端未在超时内就绪，仍继续启动前端（可用 --no-wait 跳过此等待）")

    # 启动前端
    if start_frontend_flag:
        proc = start_frontend(args)
        if proc:
            svc_manager.add_process(proc)

    # 访问地址汇总
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}  服务地址{Colors.END}")
    print(f"{Colors.CYAN}{'─'*60}{Colors.END}")
    if start_backend_flag:
        print(f"  后端 API   {Colors.GREEN}http://127.0.0.1:{args.backend_port}{Colors.END}")
        print(f"  API 文档   {Colors.GREEN}http://127.0.0.1:{args.backend_port}/docs{Colors.END}")
        print(f"  WS 事件    {Colors.GREEN}ws://127.0.0.1:{args.backend_port}/ws/per-events{Colors.END}")
    if start_frontend_flag:
        print(f"  前端 UI    {Colors.GREEN}http://localhost:{args.frontend_port}{Colors.END}")
    print(f"{Colors.CYAN}{'─'*60}{Colors.END}")
    print(f"  按 {Colors.BOLD}Ctrl+C{Colors.END} 停止所有服务")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")

    try:
        svc_manager.wait()
    except KeyboardInterrupt:
        svc_manager.shutdown()


if __name__ == "__main__":
    main()
