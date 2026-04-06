# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
ClawAI 演示视频录制脚本
用于录制演示视频的各个场景
"""

import os
import sys
import time
import subprocess

def print_header(text):
    print("\n" + "=" * 80)
    print(f" {text} ".center(80, "="))
    print("=" * 80)

def print_success(text):
    print(f"[SUCCESS] {text}")

def print_warning(text):
    print(f"[WARNING] {text}")

def print_error(text):
    print(f"[ERROR] {text}")

def record_scene(scene_number, scene_name, delay=1.0):
    """录制单个场景"""
    print_header(f"录制场景 {scene_number}: {scene_name}")
    
    try:
        # 构建命令
        cmd = [
            sys.executable,
            "non_interactive_demo.py",
            "--scenes", str(scene_number),
            "--delay", str(delay),
            "--scene-delay", "0.5"
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        print(f"开始录制场景 {scene_number}...")
        
        # 执行演示脚本
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=False,  # 不捕获输出，让用户看到演示
            text=True,
            timeout=300  # 5分钟超时
        )
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            print_success(f"场景 {scene_number} 录制完成")
            print(f"  录制时长: {elapsed_time:.2f} 秒")
            return True
        else:
            print_error(f"场景 {scene_number} 录制失败，退出码: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print_error(f"场景 {scene_number} 录制超时")
        return False
    except Exception as e:
        print_error(f"录制场景 {scene_number} 时发生错误: {e}")
        return False

def record_full_demo(delay=1.0, scene_delay=2.0):
    """录制完整演示"""
    print_header("录制完整演示")
    
    try:
        cmd = [
            sys.executable,
            "non_interactive_demo.py",
            "--scenes", "1,2,3",
            "--delay", str(delay),
            "--scene-delay", str(scene_delay)
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        print("开始录制完整演示...")
        
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=False,
            text=True,
            timeout=600  # 10分钟超时
        )
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            print_success("完整演示录制完成")
            print(f"  总录制时长: {elapsed_time:.2f} 秒")
            return True
        else:
            print_error(f"完整演示录制失败，退出码: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print_error("完整演示录制超时")
        return False
    except Exception as e:
        print_error(f"录制完整演示时发生错误: {e}")
        return False

def create_recording_plan():
    """创建录制计划"""
    print_header("ClawAI 演示视频录制计划")
    
    plan = {
        "total_scenes": 4,
        "scenes": [
            {
                "number": 1,
                "name": "AI决策制定",
                "description": "AI分析目标并推荐攻击路径",
                "estimated_time": "90秒",
                "delay": 1.0
            },
            {
                "number": 2,
                "name": "多模型对比",
                "description": "4个AI模型协同决策",
                "estimated_time": "90秒",
                "delay": 1.0
            },
            {
                "number": 3,
                "name": "完整工作流",
                "description": "6阶段渗透测试完整流程",
                "estimated_time": "120秒",
                "delay": 1.0
            },
            {
                "name": "完整演示",
                "description": "所有场景连续演示",
                "estimated_time": "5分钟",
                "delay": 1.0,
                "scene_delay": 2.0
            }
        ]
    }
    
    print("录制计划:")
    for i, scene in enumerate(plan["scenes"], 1):
        if "number" in scene:
            print(f"  场景 {scene['number']}: {scene['name']}")
        else:
            print(f"  完整演示: {scene['name']}")
        print(f"    描述: {scene['description']}")
        print(f"    预计时长: {scene['estimated_time']}")
        print()
    
    return plan

def main():
    """主函数"""
    print_header("ClawAI 演示视频录制脚本")
    print("开始时间: " + time.strftime("%Y-%m-%d %H:%M:%S"))
    
    # 创建录制计划
    plan = create_recording_plan()
    
    # 询问用户要录制哪些内容
    print("\n请选择要录制的演示内容:")
    print("  1. 场景1: AI决策制定")
    print("  2. 场景2: 多模型对比")
    print("  3. 场景3: 完整工作流")
    print("  4. 完整演示（所有场景）")
    print("  5. 所有内容（场景1-3 + 完整演示）")
    print("  0. 退出")
    
    try:
        choice = input("\n请输入选择（多个选择用逗号分隔，例如：1,2,3）: ").strip()
        
        if choice == "0":
            print("退出录制")
            return
        
        choices = [c.strip() for c in choice.split(",")]
        
        success_count = 0
        total_count = 0
        
        # 执行选择的录制
        if "1" in choices or "5" in choices:
            total_count += 1
            if record_scene(1, "AI决策制定", delay=1.0):
                success_count += 1
        
        if "2" in choices or "5" in choices:
            total_count += 1
            if record_scene(2, "多模型对比", delay=1.0):
                success_count += 1
        
        if "3" in choices or "5" in choices:
            total_count += 1
            if record_scene(3, "完整工作流", delay=1.0):
                success_count += 1
        
        if "4" in choices or "5" in choices:
            total_count += 1
            if record_full_demo(delay=1.0, scene_delay=2.0):
                success_count += 1
        
        # 输出结果
        print_header("录制结果总结")
        print(f"成功录制: {success_count}/{total_count}")
        
        if success_count == total_count:
            print_success("所有录制任务完成！")
            print("\n录制文件建议:")
            print("  1. 使用屏幕录制软件（如OBS Studio）录制终端输出")
            print("  2. 设置合适的分辨率和帧率（推荐1920x1080, 30fps）")
            print("  3. 确保音频清晰")
            print("  4. 后期添加片头和字幕")
        else:
            print_warning("部分录制任务失败，请检查错误信息")
        
        # 创建录制记录
        record_file = f"recording_report_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(record_file, 'w', encoding='utf-8') as f:
            f.write(f"ClawAI 演示录制报告\n")
            f.write(f"录制时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"成功录制: {success_count}/{total_count}\n")
            f.write(f"选择的内容: {choice}\n")
            f.write("\n详细录制计划:\n")
            for scene in plan["scenes"]:
                if "number" in scene:
                    f.write(f"  场景 {scene['number']}: {scene['name']}\n")
                else:
                    f.write(f"  完整演示: {scene['name']}\n")
        
        print_success(f"录制报告已保存到 {record_file}")
        
    except KeyboardInterrupt:
        print("\n\n录制被用户中断")
    except Exception as e:
        print_error(f"录制过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n\n程序执行错误: {e}")
        import traceback
        traceback.print_exc()