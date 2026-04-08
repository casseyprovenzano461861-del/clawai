#!/usr/bin/env python3
"""
ClawAI 统一启动脚本
支持一键启动后端、前端或全部服务
"""

import os
import sys
import signal
import subprocess
import argparse
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
    print(f"{Colors.BLUE}[{name}]{Colors.END} {url} {status_color}{status}{Colors.END}")

def run_command(cmd: List[str], cwd: str = None, env: dict = None) -> subprocess.Popen:
    """运行命令并返回进程"""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    
    return subprocess.Popen(
        cmd,
        cwd=cwd or PROJECT_ROOT,
        env=full_env,
        shell=True if sys.platform == 'win32' else False
    )

class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """设置信号处理器"""
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
    
    def shutdown(self, signum=None, frame=None):
        """关闭所有服务"""
        print(f"\n{Colors.YELLOW}正在关闭所有服务...{Colors.END}")
        
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                proc.kill()
        
        print(f"{Colors.GREEN}所有服务已关闭{Colors.END}")
        sys.exit(0)
    
    def add_process(self, proc: subprocess.Popen):
        """添加进程"""
        self.processes.append(proc)
    
    def wait(self):
        """等待所有进程"""
        for proc in self.processes:
            proc.wait()

def start_backend(args) -> Optional[subprocess.Popen]:
    """启动后端服务"""
    print(f"\n{Colors.BOLD}启动后端服务...{Colors.END}")
    
    # 设置环境变量
    env = {
        "ENVIRONMENT": "development",
        "DATABASE_URL": f"sqlite:///{PROJECT_ROOT / 'data' / 'databases' / 'clawai.db'}",
        "TOOLS_DIR": str(PROJECT_ROOT / "tools" / "penetration"),
        "JWT_SECRET_KEY": os.getenv("JWT_SECRET_KEY", "clawai-dev-secret-key"),
    }
    
    # 构建命令
    if args.mode == "dev":
        cmd = f'python -m uvicorn src.shared.backend.main:app --host {args.host} --port {args.backend_port} --reload'
    else:
        cmd = f'python -m uvicorn src.shared.backend.main:app --host {args.host} --port {args.backend_port}'
    
    proc = run_command(cmd, env=env)
    
    print_service("后端API", f"http://{args.host}:{args.backend_port}")
    print_service("API文档", f"http://{args.host}:{args.backend_port}/docs")
    
    return proc

def start_frontend(args) -> Optional[subprocess.Popen]:
    """启动前端服务"""
    print(f"\n{Colors.BOLD}启动前端服务...{Colors.END}")
    
    frontend_dir = PROJECT_ROOT / "frontend"
    
    if not frontend_dir.exists():
        print(f"{Colors.RED}错误: 前端目录不存在{Colors.END}")
        return None
    
    # 检查node_modules
    if not (frontend_dir / "node_modules").exists():
        print(f"{Colors.YELLOW}正在安装前端依赖...{Colors.END}")
        install_proc = run_command("npm install", cwd=str(frontend_dir))
        install_proc.wait()
    
    # 构建命令
    if args.mode == "dev":
        cmd = "npm run dev"
    else:
        cmd = "npm run build && npm run preview"
    
    proc = run_command(cmd, cwd=str(frontend_dir))
    
    print_service("前端UI", f"http://localhost:{args.frontend_port}")
    
    return proc

def check_dependencies():
    """检查依赖"""
    print(f"\n{Colors.BOLD}检查依赖...{Colors.END}")
    
    issues = []
    
    # 检查Python
    if sys.version_info < (3, 10):
        issues.append("Python版本需要 >= 3.10")
    
    # 检查Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            issues.append("Node.js未安装")
    except FileNotFoundError:
        issues.append("Node.js未安装")
    
    # 检查数据库目录
    db_dir = PROJECT_ROOT / "data" / "databases"
    if not db_dir.exists():
        db_dir.mkdir(parents=True, exist_ok=True)
        print(f"  {Colors.GREEN}✓{Colors.END} 创建数据库目录")
    
    # 检查日志目录
    logs_dir = PROJECT_ROOT / "logs"
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True, exist_ok=True)
        print(f"  {Colors.GREEN}✓{Colors.END} 创建日志目录")
    
    if issues:
        print(f"{Colors.RED}依赖检查失败:{Colors.END}")
        for issue in issues:
            print(f"  {Colors.RED}✗{Colors.END} {issue}")
        return False
    
    print(f"  {Colors.GREEN}✓{Colors.END} 所有依赖正常")
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="ClawAI 统一启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python start.py              # 启动所有服务
  python start.py --backend    # 仅启动后端
  python start.py --frontend   # 仅启动前端
  python start.py --mode dev   # 开发模式
  python start.py --check      # 仅检查依赖
        """
    )
    
    parser.add_argument("--backend", action="store_true", help="仅启动后端服务")
    parser.add_argument("--frontend", action="store_true", help="仅启动前端服务")
    parser.add_argument("--mode", choices=["dev", "prod"], default="dev", help="运行模式")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机")
    parser.add_argument("--backend-port", type=int, default=8000, help="后端端口")
    parser.add_argument("--frontend-port", type=int, default=3000, help="前端端口")
    parser.add_argument("--check", action="store_true", help="仅检查依赖")
    parser.add_argument("--no-check", action="store_true", help="跳过依赖检查")
    
    args = parser.parse_args()
    
    # 打印横幅
    print_banner()
    
    # 检查依赖
    if args.check:
        check_dependencies()
        return
    
    if not args.no_check and not check_dependencies():
        sys.exit(1)
    
    # 确定要启动的服务
    start_all = not args.backend and not args.frontend
    start_backend_flag = start_all or args.backend
    start_frontend_flag = start_all or args.frontend
    
    # 创建服务管理器
    manager = ServiceManager()
    
    # 启动服务
    if start_backend_flag:
        proc = start_backend(args)
        if proc:
            manager.add_process(proc)
    
    if start_frontend_flag:
        proc = start_frontend(args)
        if proc:
            manager.add_process(proc)
    
    # 打印使用提示
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}服务已启动，按 Ctrl+C 停止{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"\n{Colors.BOLD}快捷键:{Colors.END}")
    print(f"  Ctrl+C  停止所有服务")
    print(f"  Ctrl+K  打开命令面板(前端)")
    print(f"  Ctrl+H  打开扫描历史(前端)")
    
    # 等待进程
    try:
        manager.wait()
    except KeyboardInterrupt:
        manager.shutdown()

if __name__ == "__main__":
    main()
