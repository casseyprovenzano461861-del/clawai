# -*- coding: utf-8 -*-
"""
基准测试运行器模块
用于执行测试挑战并收集结果
"""

import time
import subprocess
import os
import json
from typing import List, Dict, Any
from .challenge_loader import ChallengeLoader
from .result_evaluator import ResultEvaluator


class BenchmarkRunner:
    """基准测试运行器类"""
    
    def __init__(self, challenges_dir="challenges", results_dir="benchmark_results"):
        self.challenges_dir = challenges_dir
        self.results_dir = results_dir
        self.challenge_loader = ChallengeLoader(challenges_dir)
        self.result_evaluator = ResultEvaluator()
        
        # 创建结果目录
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
    
    def run_challenge(self, challenge_name: str) -> Dict[str, Any]:
        """运行单个挑战"""
        challenge = self.challenge_loader.get_challenge(challenge_name)
        if not challenge:
            return {"error": f"挑战 {challenge_name} 不存在"}
        
        print(f"开始运行挑战: {challenge_name}")
        print(f"目标: {challenge.get('target')}")
        print(f"难度: {challenge.get('difficulty')}")
        print(f"超时: {challenge.get('timeout')} 秒")
        
        start_time = time.time()
        
        try:
            # 执行ClawAI扫描
            output = self._execute_scan(challenge)
            
            # 评估结果
            result = self.result_evaluator.evaluate_result(challenge, output)
            
            # 计算执行时间
            execution_time = time.time() - start_time
            result["execution_time"] = execution_time
            
            print(f"挑战 {challenge_name} 执行完成")
            print(f"执行时间: {execution_time:.2f} 秒")
            print(f"成功率: {result['success_rate'] * 100:.2f}%")
            print(f"发现标志: {len(result['found_flags'])}/{result['total_flags']}")
            
            # 保存结果
            self._save_result(challenge_name, result)
            
            return result
            
        except Exception as e:
            print(f"运行挑战 {challenge_name} 时出错: {e}")
            return {"error": str(e)}
    
    def run_all_challenges(self) -> Dict[str, Any]:
        """运行所有挑战"""
        challenges = self.challenge_loader.list_challenges()
        results = []
        
        print(f"开始运行所有挑战 (共 {len(challenges)} 个)")
        
        for challenge_name in challenges:
            result = self.run_challenge(challenge_name)
            if "error" not in result:
                results.append(result)
        
        # 生成报告
        report = self.result_evaluator.generate_report(results)
        
        # 保存报告
        report_path = os.path.join(self.results_dir, f"benchmark_report_{time.strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n基准测试完成")
        print(f"总挑战数: {report['summary']['total_challenges']}")
        print(f"成功挑战数: {report['summary']['successful_challenges']}")
        print(f"部分成功挑战数: {report['summary']['partial_challenges']}")
        print(f"失败挑战数: {report['summary']['failed_challenges']}")
        print(f"总标志数: {report['summary']['total_flags']}")
        print(f"发现标志数: {report['summary']['found_flags']}")
        print(f"总体成功率: {report['summary']['overall_success_rate'] * 100:.2f}%")
        print(f"报告已保存到: {report_path}")
        
        if report['recommendations']:
            print("\n改进建议:")
            for recommendation in report['recommendations']:
                print(f"- {recommendation}")
        
        return report
    
    def _execute_scan(self, challenge: Dict[str, Any]) -> str:
        """执行扫描"""
        target = challenge.get("target")
        timeout = challenge.get("timeout", 3600)
        
        # 构建扫描命令
        scan_command = [
            "python", "src/shared/backend/main.py",
            "--target", target,
            "--timeout", str(timeout)
        ]
        
        print(f"执行扫描命令: {' '.join(scan_command)}")
        
        # 执行命令
        try:
            result = subprocess.run(
                scan_command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # 合并标准输出和标准错误
            output = result.stdout + "\n" + result.stderr
            return output
            
        except subprocess.TimeoutExpired:
            return f"扫描超时 (超过 {timeout} 秒)"
        except Exception as e:
            return f"扫描执行失败: {str(e)}"
    
    def _save_result(self, challenge_name: str, result: Dict[str, Any]):
        """保存结果"""
        result_path = os.path.join(self.results_dir, f"{challenge_name}_result.json")
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    
    def list_challenges(self):
        """列出所有挑战"""
        return self.challenge_loader.list_challenges()
    
    def get_challenge(self, challenge_name: str):
        """获取挑战信息"""
        return self.challenge_loader.get_challenge(challenge_name)
