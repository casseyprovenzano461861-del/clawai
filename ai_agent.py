#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI AI Agent 启动脚本
快速启动 AI 驱动的渗透测试助手
"""

import os
import sys
import asyncio
import argparse
import logging

# 添加项目根目录到路径
_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_project_root, '.env'))
except ImportError:
    pass

from src.shared.backend.ai_agent import create_orchestrator, AgentMode

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='ClawAI AI Agent - AI 驱动的渗透测试助手'
    )
    
    parser.add_argument(
        '--provider', '-p',
        default=os.getenv('LLM_PROVIDER', 'deepseek'),
        choices=['deepseek', 'openai', 'anthropic', 'mock'],
        help='LLM 提供商 (default: deepseek)'
    )
    
    parser.add_argument(
        '--api-key', '-k',
        default=os.getenv('DEEPSEEK_API_KEY') or os.getenv('OPENAI_API_KEY', ''),
        help='API Key'
    )
    
    parser.add_argument(
        '--model', '-m',
        default='',
        help='模型名称'
    )
    
    parser.add_argument(
        '--mode',
        default='chat',
        choices=['chat', 'autonomous'],
        help='执行模式 (default: chat)'
    )
    
    parser.add_argument(
        '--target', '-t',
        default='',
        help='目标地址'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    return parser.parse_args()


async def main():
    """主函数"""
    args = parse_args()
    
    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建编排器
    print("\n" + "=" * 60)
    print("  ClawAI AI Agent")
    print("  AI 驱动的渗透测试助手")
    print("=" * 60)
    print()
    
    orchestrator = create_orchestrator(
        provider=args.provider,
        api_key=args.api_key,
        model=args.model,
        mode=AgentMode.CHAT if args.mode == 'chat' else AgentMode.AUTONOMOUS
    )
    
    # 设置目标
    if args.target:
        orchestrator.set_target(args.target)
        print(f"目标已设置: {args.target}")
        print()
    
    # 如果是自主模式且有目标，直接启动
    if args.mode == 'autonomous' and args.target:
        print(f"启动自主渗透测试: {args.target}")
        print()
        
        async for event in orchestrator.start_autonomous(args.target):
            event_type = event.get("type")
            
            if event_type == "start":
                print(f"[开始] 目标: {event.get('target')}")
            
            elif event_type == "progress":
                print(f"[进度] {event.get('message', '')}")
            
            elif event_type == "result":
                success = event.get('success', False)
                print(f"[结果] {'成功' if success else '失败'}")
            
            elif event_type == "complete":
                print(f"[完成] 耗时: {event.get('duration', 0):.2f}秒")
        
        return
    
    # 交互式会话
    print("输入消息开始对话，输入 'help' 查看帮助，'exit' 退出")
    print()
    
    while True:
        try:
            user_input = input("\033[36mYou\033[0m: ").strip()
            
            if not user_input:
                continue
            
            # 特殊命令
            if user_input.lower() in ['exit', 'quit', '退出', 'bye']:
                print("\n再见！\n")
                break
            
            if user_input.lower() in ['help', '帮助', '?']:
                print_help()
                continue
            
            if user_input.lower() in ['status', '状态']:
                status = orchestrator.get_status()
                print(f"\n状态: {status['mode']} 模式")
                print(f"上下文: {orchestrator.get_context_summary()}")
                continue
            
            if user_input.lower().startswith('target '):
                target = user_input[7:].strip()
                orchestrator.set_target(target)
                print(f"\n目标已设置: {target}")
                continue
            
            # 处理消息
            print(f"\033[32mClawAI\033[0m: ", end="", flush=True)
            
            response_parts = []
            
            async for event in orchestrator.chat(user_input):
                event_type = event.get("type")
                
                if event_type == "content":
                    content = event.get("content", "")
                    response_parts.append(content)
                    print(content, end="", flush=True)
                
                elif event_type == "tool_call_start":
                    tool_name = event.get("tool_name", "")
                    assessment = event.get("risk_assessment", {})
                    risk_level = assessment.get("level", "unknown")
                    
                    print(f"\n  ┌─ 执行工具: {tool_name}")
                    print(f"  │  风险等级: {risk_level}")
                
                elif event_type == "tool_call_executing":
                    print(f"  │  执行中...")
                
                elif event_type == "tool_call_result":
                    result = event.get("result", {})
                    success = result.get("success", False)
                    simulated = result.get("simulated", False)
                    
                    status_icon = "✓" if success else "✗"
                    sim_note = " (模拟)" if simulated else ""
                    print(f"  └─ {status_icon}{sim_note}")
                
                elif event_type == "tool_call_cancelled":
                    print(f"  └─ 已取消")
                
                elif event_type == "response_end":
                    pass
            
            print()  # 换行
            
        except KeyboardInterrupt:
            print("\n\n会话已中断\n")
            break
        except Exception as e:
            print(f"\n错误: {e}\n")
            logger.error(f"会话错误: {e}")


def print_help():
    """打印帮助信息"""
    help_text = """
可用命令:
  help, 帮助, ?     显示帮助信息
  exit, quit, 退出   退出程序
  status, 状态      查看当前状态
  target <地址>     设置目标地址

示例对话:
  "帮我扫描 example.com"
  "对 192.168.1.1 进行端口扫描"
  "扫描 https://testphp.vulnweb.com 的漏洞"
  "生成测试报告"

更多信息请访问: https://github.com/your-repo/clawai
"""
    print(help_text)


if __name__ == "__main__":
    asyncio.run(main())
