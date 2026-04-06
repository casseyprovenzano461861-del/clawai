# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
ClawAI 非交互式演示脚本
自动运行所有演示场景，无需用户交互
用于演示、测试和自动化展示
"""

import time
import sys
import os

def print_line():
    print("=" * 60)

def print_header(title):
    print_line()
    print(title.center(60))
    print_line()

def print_step(step, text):
    print(f"\n[Step {step}] {text}")

def simulate_thinking(text):
    print(f"\n[AI Thinking] {text}")
    print("Processing", end="", flush=True)
    for _ in range(3):
        time.sleep(0.3)
        print(".", end="", flush=True)
    print()

class NonInteractiveDemoSystem:
    def __init__(self, delay_between_scenes=1.0, scene_delay=0.5):
        self.scenes = [
            "AI Decision Making",
            "Multi-Model Comparison", 
            "Complete Workflow"
        ]
        self.delay_between_scenes = delay_between_scenes
        self.scene_delay = scene_delay
    
    def run_scene1(self):
        """场景1: AI决策制定"""
        print_header("SCENE 1: AI DECISION MAKING")
        
        print_step(1, "目标分析")
        print("目标: demo-target.com")
        simulate_thinking("分析目标系统...")
        
        print("[SUCCESS] 分析完成:")
        print("  - 技术栈: WordPress 5.8 + PHP 7.4")
        print("  - 开放端口: 80, 443, 3306")
        print("  - Web服务器: Apache 2.4.41")
        
        print_step(2, "漏洞检测")
        simulate_thinking("检查漏洞...")
        
        print("[SUCCESS] 发现漏洞:")
        print("  - [严重] WordPress RCE (CVE-2023-1234)")
        print("  - [高危] 登录表单SQL注入")
        
        print_step(3, "AI攻击规划")
        simulate_thinking("规划最优攻击路径...")
        
        print("[SUCCESS] AI推荐:")
        print("  - 攻击路径: rce_attack")
        print("  - 评分: 8.5/10")
        print("  - 置信度: 92%")
        
        time.sleep(self.scene_delay)
        return True
    
    def run_scene2(self):
        """场景2: 多模型对比"""
        print_header("SCENE 2: MULTI-MODEL COMPARISON")
        
        print_step(1, "初始化AI模型")
        models = ["DeepSeek", "OpenAI", "Claude", "Local"]
        
        for model in models:
            simulate_thinking(f"加载 {model}...")
            print(f"  [OK] {model} 就绪")
        
        print_step(2, "模型投票")
        print("每个模型独立分析...")
        time.sleep(1)
        
        print("\n模型决策:")
        decisions = [
            ("DeepSeek", "rce_attack", 85),
            ("OpenAI", "rce_attack", 78),
            ("Claude", "sql_injection", 65),
            ("Local", "rce_attack", 55)
        ]
        
        for name, decision, confidence in decisions:
            print(f"  [{name}] {decision} ({confidence}% 置信度)")
            time.sleep(0.3)
        
        print_step(3, "最终决策")
        simulate_thinking("构建共识...")
        
        print("[SUCCESS] 最终决策:")
        print("  - 选择: rce_attack")
        print("  - 支持度: 3/4 模型 (75%)")
        print("  - 总体置信度: 82%")
        
        time.sleep(self.scene_delay)
        return True
    
    def run_scene3(self):
        """场景3: 完整工作流"""
        print_header("SCENE 3: COMPLETE WORKFLOW")
        
        print_step(1, "工作流初始化")
        print("开始6阶段渗透测试...")
        simulate_thinking("初始化工作流引擎...")
        
        stages = [
            ("侦察阶段", "收集目标信息"),
            ("扫描阶段", "端口和服务发现"),
            ("漏洞分析", "识别安全缺陷"),
            ("利用阶段", "执行攻击"),
            ("后渗透阶段", "数据收集"),
            ("报告生成", "生成最终报告")
        ]
        
        for i, (name, desc) in enumerate(stages, 1):
            print_step(i, f"{name}")
            print(f"  描述: {desc}")
            simulate_thinking(f"执行 {name}...")
            print(f"  [OK] {name} 完成")
            time.sleep(0.5)
        
        print_step(7, "工作流完成")
        print("[SUCCESS] 所有阶段完成!")
        print("  - 总时间: 24.4 秒")
        print("  - 目标: demo-target.com")
        print("  - 状态: 成功")
        
        time.sleep(self.scene_delay)
        return True
    
    def show_conclusion(self):
        """展示演示结论"""
        print_header("DEMO CONCLUSION")
        
        print("\n演示摘要:")
        print("[OK] 场景 1: AI决策制定")
        print("  - AI分析目标并推荐攻击")
        print("  - 评分: 8.5/10, 置信度: 92%")
        
        print("\n[OK] 场景 2: 多模型对比")
        print("  - 4个AI模型协同决策")
        print("  - 最终: rce_attack (3/4 模型支持)")
        
        print("\n[OK] 场景 3: 完整工作流")
        print("  - 6阶段渗透测试")
        print("  - 总时间: 24.4 秒")
        print("  - 成功率: 100%")
        
        print("\n技术优势:")
        print("  - 真正的AI决策，非规则引擎")
        print("  - 集成37个安全工具")
        print("  - 支持Docker部署")
        print("  - 模块化架构")
        
        print_line()
        print("感谢观看 ClawAI 演示!")
        print_line()
    
    def run_demo(self, scene_numbers=None):
        """
        运行完整演示
        
        Args:
            scene_numbers: 要运行的场景编号列表（1-3），None表示全部运行
        """
        try:
            print_header("CLAWAI 非交互式演示")
            print("\n欢迎使用 ClawAI 演示系统!")
            print("此演示将展示3个核心能力:")
            for i, scene in enumerate(self.scenes, 1):
                print(f"  {i}. {scene}")
            
            print(f"\n等待 {self.delay_between_scenes} 秒后开始演示...")
            time.sleep(self.delay_between_scenes)
            
            # 确定要运行的场景
            if scene_numbers is None:
                scene_numbers = [1, 2, 3]
            
            # 运行指定场景
            for scene_num in scene_numbers:
                if scene_num == 1:
                    self.run_scene1()
                elif scene_num == 2:
                    self.run_scene2()
                elif scene_num == 3:
                    self.run_scene3()
                
                if scene_num != scene_numbers[-1]:
                    print(f"\n等待 {self.delay_between_scenes} 秒后继续下一个场景...")
                    time.sleep(self.delay_between_scenes)
            
            # 显示结论
            self.show_conclusion()
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n[INFO] 演示被用户中断")
            return False
        except Exception as e:
            print(f"\n\n[ERROR] 演示错误: {e}")
            return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ClawAI 非交互式演示脚本')
    parser.add_argument('--scenes', type=str, default='1,2,3',
                        help='要运行的场景编号，用逗号分隔 (默认: 1,2,3)')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='场景间延迟时间(秒) (默认: 1.0)')
    parser.add_argument('--scene-delay', type=float, default=0.5,
                        help='场景内步骤延迟时间(秒) (默认: 0.5)')
    parser.add_argument('--quiet', action='store_true',
                        help='安静模式，减少输出')
    parser.add_argument('--test', action='store_true',
                        help='测试模式，快速运行')
    
    args = parser.parse_args()
    
    # 解析场景编号
    scene_numbers = []
    try:
        scene_numbers = [int(num.strip()) for num in args.scenes.split(',')]
        # 验证场景编号
        for num in scene_numbers:
            if num < 1 or num > 3:
                print(f"[ERROR] 无效的场景编号: {num}，有效范围: 1-3")
                sys.exit(1)
    except ValueError:
        print("[ERROR] 无效的场景编号格式，请使用逗号分隔的数字")
        sys.exit(1)
    
    # 测试模式调整参数
    if args.test:
        args.delay = 0.1
        args.scene_delay = 0.1
    
    # 安静模式调整输出
    if args.quiet:
        # 这里可以重定向输出，但为了简单起见，我们只减少延迟
        args.delay = 0
        args.scene_delay = 0
    
    print(f"开始 ClawAI 非交互式演示...")
    print(f"配置: 场景 {scene_numbers}, 延迟 {args.delay}s, 场景延迟 {args.scene_delay}s")
    time.sleep(1)
    
    demo = NonInteractiveDemoSystem(
        delay_between_scenes=args.delay,
        scene_delay=args.scene_delay
    )
    
    success = demo.run_demo(scene_numbers)
    
    if success:
        print("\n[SUCCESS] 演示成功完成!")
        print("[INFO] 适用于自动化测试和展示。")
    else:
        print("\n[ERROR] 演示执行失败!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)