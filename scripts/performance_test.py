# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
ClawAI 性能测试脚本
测试演示脚本的性能和可靠性
"""

import time
import subprocess
import sys
import os
from datetime import datetime

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

def test_demo_script_load():
    """测试演示脚本加载时间"""
    print_header("测试1: 演示脚本加载时间")
    
    start_time = time.time()
    try:
        # 导入演示脚本模块以测试加载时间
        import importlib.util
        
        # 加载non_interactive_demo模块
        spec = importlib.util.spec_from_file_location("non_interactive_demo", "non_interactive_demo.py")
        module = importlib.util.module_from_spec(spec)
        
        # 记录加载时间
        load_start = time.time()
        spec.loader.exec_module(module)
        load_time = time.time() - load_start
        
        print(f"演示脚本加载时间: {load_time:.3f} 秒")
        
        if load_time < 1.0:
            print_success(f"加载速度正常 (< 1.0秒)")
            return True
        elif load_time < 3.0:
            print_warning(f"加载速度较慢 (1.0-3.0秒)")
            return True
        else:
            print_error(f"加载速度过慢 (> 3.0秒)")
            return False
            
    except Exception as e:
        print_error(f"演示脚本加载失败: {e}")
        return False

def test_demo_execution(scene_number=1):
    """测试演示执行时间"""
    print_header(f"测试2: 演示场景{scene_number}执行时间")
    
    try:
        cmd = [
            sys.executable,
            "non_interactive_demo.py",
            "--scenes", str(scene_number),
            "--delay", "0",
            "--scene-delay", "0",
            "--quiet"
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 1分钟超时
        )
        elapsed_time = time.time() - start_time
        
        print(f"场景{scene_number}执行时间: {elapsed_time:.2f} 秒")
        
        if result.returncode == 0:
            print_success(f"场景{scene_number}执行成功")
            
            # 检查输出中是否包含成功信息
            output = result.stdout + result.stderr
            if "SUCCESS" in output or "完成" in output or "成功" in output:
                print_success("输出包含成功指示")
            else:
                print_warning("输出中未找到明确成功指示")
            
            # 性能基准
            if elapsed_time < 10.0:
                print_success(f"执行速度优秀 (< 10秒)")
                return True
            elif elapsed_time < 30.0:
                print_success(f"执行速度良好 (10-30秒)")
                return True
            elif elapsed_time < 60.0:
                print_warning(f"执行速度较慢 (30-60秒)")
                return True
            else:
                print_error(f"执行速度过慢 (> 60秒)")
                return False
        else:
            print_error(f"场景{scene_number}执行失败，退出码: {result.returncode}")
            print(f"错误输出: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print_error(f"场景{scene_number}执行超时 (超过60秒)")
        return False
    except Exception as e:
        print_error(f"测试场景{scene_number}时发生错误: {e}")
        return False

def test_demo_completeness():
    """测试演示完整性"""
    print_header("测试3: 演示完整性测试")
    
    try:
        # 测试所有场景
        all_scenes_passed = True
        
        for scene in [1, 2, 3]:
            print(f"\n测试场景 {scene}...")
            
            cmd = [
                sys.executable,
                "non_interactive_demo.py",
                "--scenes", str(scene),
                "--delay", "0",
                "--scene-delay", "0",
                "--quiet"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                output = result.stdout + result.stderr
                
                # 检查场景特定关键词
                if scene == 1 and ("AI Decision" in output or "AI决策" in output):
                    print_success(f"场景{scene}包含预期内容")
                elif scene == 2 and ("Multi-Model" in output or "多模型" in output):
                    print_success(f"场景{scene}包含预期内容")
                elif scene == 3 and ("Workflow" in output or "工作流" in output):
                    print_success(f"场景{scene}包含预期内容")
                else:
                    print_warning(f"场景{scene}输出可能不完整")
                    all_scenes_passed = False
            else:
                print_error(f"场景{scene}执行失败")
                all_scenes_passed = False
        
        if all_scenes_passed:
            print_success("所有演示场景完整性测试通过")
            return True
        else:
            print_warning("部分演示场景完整性测试失败")
            return False
            
    except Exception as e:
        print_error(f"演示完整性测试失败: {e}")
        return False

def test_memory_usage():
    """测试内存使用情况"""
    print_header("测试4: 内存使用测试")
    
    try:
        import psutil
        
        # 获取当前进程内存使用
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        memory_mb = memory_info.rss / 1024 / 1024  # 转换为MB
        
        print(f"当前进程内存使用: {memory_mb:.2f} MB")
        
        if memory_mb < 100:
            print_success(f"内存使用正常 (< 100 MB)")
            return True
        elif memory_mb < 500:
            print_success(f"内存使用可接受 (100-500 MB)")
            return True
        elif memory_mb < 1000:
            print_warning(f"内存使用较高 (500-1000 MB)")
            return True
        else:
            print_error(f"内存使用过高 (> 1000 MB)")
            return False
            
    except ImportError:
        print_warning("psutil模块未安装，跳过内存测试")
        return True  # 跳过测试不算失败
    except Exception as e:
        print_error(f"内存测试失败: {e}")
        return False

def run_all_tests():
    """运行所有性能测试"""
    print_header("ClawAI 性能测试套件")
    print(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = []
    
    # 测试1: 脚本加载
    test1_result = test_demo_script_load()
    test_results.append(("演示脚本加载", test1_result))
    
    # 测试2: 场景执行
    test2_result = test_demo_execution(scene_number=1)
    test_results.append(("场景1执行", test2_result))
    
    # 测试3: 演示完整性
    test3_result = test_demo_completeness()
    test_results.append(("演示完整性", test3_result))
    
    # 测试4: 内存使用
    test4_result = test_memory_usage()
    test_results.append(("内存使用", test4_result))
    
    # 总结结果
    print_header("性能测试总结")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, result in test_results if result)
    
    print(f"测试总数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    
    print("\n详细结果:")
    for test_name, result in test_results:
        status = "通过" if result else "失败"
        print(f"  {test_name}: {status}")
    
    # 创建测试报告
    report_file = f"performance_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    import json
    report_data = {
        "test_date": datetime.now().isoformat(),
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": total_tests - passed_tests,
        "results": [
            {
                "test_name": test_name,
                "passed": result,
                "timestamp": datetime.now().isoformat()
            }
            for test_name, result in test_results
        ]
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print_success(f"测试报告已保存到 {report_file}")
    
    # 返回总体结果
    if passed_tests >= total_tests * 0.8:  # 80%通过率
        print_success("性能测试: 通过 (80%以上测试通过)")
        return True
    else:
        print_error("性能测试: 失败 (通过率低于80%)")
        return False

def quick_test():
    """快速测试模式"""
    print_header("快速性能测试模式")
    
    try:
        # 只测试场景1的执行
        print("运行快速测试...")
        
        start_time = time.time()
        cmd = [
            sys.executable,
            "non_interactive_demo.py",
            "--scenes", "1",
            "--delay", "0",
            "--scene-delay", "0",
            "--quiet"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        elapsed_time = time.time() - start_time
        
        print(f"快速测试执行时间: {elapsed_time:.2f} 秒")
        
        if result.returncode == 0 and elapsed_time < 10.0:
            print_success("快速测试通过")
            return True
        else:
            print_error("快速测试失败")
            return False
            
    except Exception as e:
        print_error(f"快速测试失败: {e}")
        return False

def main():
    """主函数"""
    print_header("ClawAI 性能测试脚本")
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        success = quick_test()
    else:
        success = run_all_tests()
    
    print(f"\n测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)