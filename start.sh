#!/bin/bash
# ClawAI 统一启动脚本 v2.0

# 颜色定义
RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
CYAN='\033[96m'
BOLD='\033[1m'
END='\033[0m'

# 横幅
banner() {
    echo ""
    echo "======================================================================"
    echo "   ╔═════════════════════════════════════════════════════════╗"
    echo "   ║                                                             ║"
    echo "   ║   ██████╗██╗      ██████╗ ██╗   ██╗██████╗                ║"
    echo "   ║   ██╔════╝██║     ██╔═══██╗██║   ██║██╔══██╗               ║"
    echo "   ║   ██║     ██║     ██║   ██║██║   ██║██║  ██║               ║"
    echo "   ║   ██║     ██║     ██║   ██║██║   ██║██║  ██║               ║"
    echo "   ║   ╚██████╗███████╗╚██████╔╝╚██████╔╝██████╔╝               ║"
    echo "   ║    ╚═════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝                ║"
    echo "   ║                                                             ║"
    echo "   ║          AI驱动的智能安全评估系统 v2.0.0                   ║"
    echo "   ║                                                             ║"
    echo "   ╚═════════════════════════════════════════════════════════╝"
    echo "======================================================================"
    echo ""
}

# 菜单
menu() {
    clear
    banner
    echo "${CYAN}[启动选项]${END}"
    echo ""
    echo "  ${CYAN}[1]${END}  开发模式 (dev)         - 后端 + 前端"
    echo "  ${CYAN}[2]${END}  生产模式 (prod)          - 后端 + 前端"
    echo "  ${CYAN}[3]${END}  仅后端 (backend)         - 后端服务"
    echo "  ${CYAN}[4]${END}  仅前端 (frontend)          - 前端服务"
    echo "  ${CYAN}[5]${END}  AI 对话 (chat)          - CLI 对话模式"
    echo "  ${CYAN}[6]${END}  TUI 界面 (tui)          - 图形界面模式"
    echo "  ${CYAN}[7]${END}  帮助信息 (help)"
    echo "  ${CYAN}[8]${END}  退出"
    echo ""
    read -p "请选择 [1-8]: " choice
}

# 处理命令
handle_command() {
    case "$1" in
        dev|1)
            echo ""
            echo "${GREEN}[启动]${END} 开发模式..."
            python clawai.py dev
            ;;
        prod|2)
            echo ""
            echo "${GREEN}[启动]${END} 生产模式..."
            python clawai.py prod
            ;;
        backend|3)
            echo ""
            echo "${GREEN}[启动]${END} 后端服务..."
            python clawai.py backend
            ;;
        frontend|4)
            echo ""
            echo "${GREEN}[启动]${END} 前端服务..."
            python clawai.py frontend
            ;;
        chat|5)
            echo ""
            echo "${GREEN}[启动]${END} AI 对话模式..."
            python clawai.py chat
            ;;
        tui|6)
            echo ""
            echo "${GREEN}[启动]${END} TUI 图形界面..."
            python clawai.py tui
            ;;
        help|7)
            python clawai.py --help
            echo ""
            read -p "按 Enter 继续..."
            ;;
        exit|8)
            echo ""
            echo "${GREEN}再见！${END}"
            exit 0
            ;;
        *)
            echo "${RED}错误: 未知选项 $1${END}"
            echo ""
            python clawai.py --help
            ;;
    esac
}

# 主循环
if [ -n "$1" ]; then
    # 有参数，直接执行
    handle_command "$1"
else
    # 无参数，显示菜单
    while true; do
        menu
        case "$choice" in
            1|dev)     handle_command dev     ;;
            2|prod)    handle_command prod    ;;
            3|backend)  handle_command backend ;;
            4|frontend) handle_command frontend ;;
            5|chat)    handle_command chat    ;;
            6|tui)     handle_command tui     ;;
            7|help)    handle_command help    ;;
            8|exit)    exit 0            ;;
        esac
    done
fi
