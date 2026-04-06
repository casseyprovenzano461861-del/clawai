#!/usr/bin/env python3
"""
CTF 基准测试运行器

基于配置运行 CTF 挑战基准测试，评估 AI 代理的表现。
参考 HackSynth 基准测试框架设计。
"""

import os
import sys
import json
import yaml
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Challenge:
    """CTF 挑战表示类"""

    def __init__(self, challenge_id: str, config_path: Path):
        self.id = challenge_id
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载挑战配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.suffix in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                elif self.config_path.suffix == '.json':
                    return json.load(f)
                else:
                    raise ValueError(f"不支持的配置文件格式: {self.config_path.suffix}")
        except Exception as e:
            logger.error(f"加载挑战配置失败 {self.config_path}: {e}")
            raise

    def validate(self) -> bool:
        """验证挑战配置"""
        required_fields = ['id', 'name', 'platform', 'category', 'difficulty', 'points']
        for field in required_fields:
            if field not in self.config:
                logger.error(f"挑战 {self.id} 缺少必需字段: {field}")
                return False
        return True

    def get_info(self) -> Dict[str, Any]:
        """获取挑战信息"""
        return {
            'id': self.id,
            'name': self.config.get('name', 'Unknown'),
            'platform': self.config.get('platform', 'unknown'),
            'category': self.config.get('category', 'unknown'),
            'difficulty': self.config.get('difficulty', 'unknown'),
            'points': self.config.get('points', 0),
            'description': self.config.get('description', '')[:100] + '...' if len(self.config.get('description', '')) > 100 else self.config.get('description', ''),
        }


class BenchmarkConfig:
    """基准测试配置类"""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载基准测试配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载基准测试配置失败 {self.config_path}: {e}")
            raise

    def validate(self) -> bool:
        """验证基准测试配置"""
        required_fields = ['name', 'platform', 'challenges']
        for field in required_fields:
            if field not in self.config:
                logger.error(f"基准测试配置缺少必需字段: {field}")
                return False
        return True

    def get_challenge_ids(self) -> List[str]:
        """获取挑战ID列表"""
        challenges = []
        for challenge in self.config.get('challenges', []):
            if isinstance(challenge, dict) and 'id' in challenge:
                if challenge.get('enabled', True):
                    challenges.append(challenge['id'])
            elif isinstance(challenge, str):
                challenges.append(challenge)
        return challenges


class BenchmarkRunner:
    """基准测试运行器"""

    def __init__(self, config_path: Path, output_dir: Path):
        self.config_path = config_path
        self.output_dir = output_dir
        self.benchmark_config = BenchmarkConfig(config_path)
        self.challenges = {}
        self.results = {
            'benchmark': self.benchmark_config.config.get('name', 'unknown'),
            'start_time': datetime.now().isoformat(),
            'challenges': [],
            'metrics': {},
            'agent_config': {},
        }

    def find_challenge_file(self, challenge_id: str) -> Optional[Path]:
        """查找挑战配置文件"""
        # 在标准目录中查找
        search_paths = [
            Path(f"picoctf/challenges/{challenge_id}.yaml"),
            Path(f"picoctf/challenges/{challenge_id}.yml"),
            Path(f"overthewire/challenges/{challenge_id}.yaml"),
            Path(f"overthewire/challenges/{challenge_id}.yml"),
            Path(f"challenges/{challenge_id}.yaml"),
            Path(f"challenges/{challenge_id}.yml"),
        ]

        for rel_path in search_paths:
            abs_path = self.config_path.parent.parent / rel_path
            if abs_path.exists():
                return abs_path

        logger.warning(f"未找到挑战文件: {challenge_id}")
        return None

    def load_challenges(self):
        """加载所有挑战"""
        challenge_ids = self.benchmark_config.get_challenge_ids()
        logger.info(f"加载 {len(challenge_ids)} 个挑战")

        for challenge_id in challenge_ids:
            challenge_path = self.find_challenge_file(challenge_id)
            if challenge_path:
                try:
                    challenge = Challenge(challenge_id, challenge_path)
                    if challenge.validate():
                        self.challenges[challenge_id] = challenge
                        logger.info(f"加载挑战: {challenge_id} - {challenge.config.get('name')}")
                    else:
                        logger.error(f"挑战验证失败: {challenge_id}")
                except Exception as e:
                    logger.error(f"加载挑战失败 {challenge_id}: {e}")
            else:
                logger.error(f"未找到挑战文件: {challenge_id}")

    def simulate_challenge_run(self, challenge_id: str) -> Dict[str, Any]:
        """模拟运行挑战（实际实现中应替换为真实的 AI 代理执行）"""
        challenge = self.challenges.get(challenge_id)
        if not challenge:
            return {
                'challenge_id': challenge_id,
                'status': 'skipped',
                'error': 'Challenge not found',
            }

        logger.info(f"开始运行挑战: {challenge_id}")

        # 模拟执行
        time.sleep(0.5)  # 模拟执行时间

        # 模拟结果 - 实际实现中应由 AI 代理生成
        return {
            'challenge_id': challenge_id,
            'status': 'completed',  # 或 'failed', 'timeout'
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration': 45.2,  # 模拟持续时间（秒）
            'steps': 8,  # 模拟步骤数
            'hints_used': 1,  # 模拟使用的提示数
            'score': 85,  # 模拟得分
            'flag_found': True,  # 是否找到标志
            'error': None,  # 错误信息（如果有）
            'agent_interactions': [],  # AI 代理交互记录
        }

    def run_benchmark(self):
        """运行基准测试"""
        logger.info(f"开始基准测试: {self.benchmark_config.config.get('name')}")

        # 加载挑战
        self.load_challenges()

        # 运行每个挑战
        challenge_ids = self.benchmark_config.get_challenge_ids()
        total_challenges = len(challenge_ids)
        completed = 0

        for i, challenge_id in enumerate(challenge_ids, 1):
            logger.info(f"运行挑战 [{i}/{total_challenges}]: {challenge_id}")

            if challenge_id not in self.challenges:
                logger.warning(f"跳过未加载的挑战: {challenge_id}")
                self.results['challenges'].append({
                    'challenge_id': challenge_id,
                    'status': 'skipped',
                    'error': 'Not loaded',
                })
                continue

            # 运行挑战
            result = self.simulate_challenge_run(challenge_id)
            self.results['challenges'].append(result)

            if result.get('status') == 'completed':
                completed += 1

        # 计算总体指标
        self.calculate_metrics()

        # 保存结果
        self.save_results()

        logger.info(f"基准测试完成: {completed}/{total_challenges} 挑战完成")

    def calculate_metrics(self):
        """计算基准测试指标"""
        challenges = self.results['challenges']
        completed = [c for c in challenges if c.get('status') == 'completed']
        failed = [c for c in challenges if c.get('status') == 'failed']
        skipped = [c for c in challenges if c.get('status') == 'skipped']

        # 基本指标
        total = len(challenges)
        completed_count = len(completed)

        if completed_count > 0:
            avg_duration = sum(c.get('duration', 0) for c in completed) / completed_count
            avg_steps = sum(c.get('steps', 0) for c in completed) / completed_count
            avg_score = sum(c.get('score', 0) for c in completed) / completed_count
            avg_hints = sum(c.get('hints_used', 0) for c in completed) / completed_count
        else:
            avg_duration = avg_steps = avg_score = avg_hints = 0

        self.results['metrics'] = {
            'total_challenges': total,
            'completed': completed_count,
            'failed': len(failed),
            'skipped': len(skipped),
            'success_rate': completed_count / total if total > 0 else 0,
            'average_duration': avg_duration,
            'average_steps': avg_steps,
            'average_score': avg_score,
            'average_hints_used': avg_hints,
            'completion_time': datetime.now().isoformat(),
        }

    def save_results(self):
        """保存基准测试结果"""
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 生成结果文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        benchmark_name = self.benchmark_config.config.get('name', 'benchmark').replace(' ', '_').lower()
        result_file = self.output_dir / f"{benchmark_name}_{timestamp}.json"

        # 保存 JSON 结果
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        # 保存 YAML 结果（可选）
        yaml_file = result_file.with_suffix('.yaml')
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.results, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"结果已保存: {result_file}")

        # 生成简要报告
        self.generate_summary_report(result_file)

    def generate_summary_report(self, result_file: Path):
        """生成简要报告"""
        report_file = result_file.with_suffix('.md')

        metrics = self.results['metrics']
        challenges = self.results['challenges']

        report = f"""# 基准测试报告: {self.results['benchmark']}

**运行时间**: {self.results['start_time']}
**完成时间**: {metrics.get('completion_time', 'N/A')}

## 总体指标

- **挑战总数**: {metrics['total_challenges']}
- **完成挑战**: {metrics['completed']}
- **失败挑战**: {metrics['failed']}
- **跳过挑战**: {metrics['skipped']}
- **成功率**: {metrics['success_rate']:.2%}
- **平均耗时**: {metrics['average_duration']:.2f} 秒
- **平均步骤**: {metrics['average_steps']:.2f}
- **平均得分**: {metrics['average_score']:.2f}
- **平均提示使用**: {metrics['average_hints_used']:.2f}

## 挑战详情

| 挑战ID | 状态 | 耗时(秒) | 步骤 | 得分 | 提示使用 | 标志找到 |
|--------|------|----------|------|------|----------|----------|
"""

        for challenge in challenges:
            report += f"| {challenge.get('challenge_id', 'N/A')} "
            report += f"| {challenge.get('status', 'unknown')} "
            report += f"| {challenge.get('duration', 0):.2f} "
            report += f"| {challenge.get('steps', 0)} "
            report += f"| {challenge.get('score', 0)} "
            report += f"| {challenge.get('hints_used', 0)} "
            report += f"| {'✓' if challenge.get('flag_found') else '✗'} |\n"

        report += f"""

## 详细结果

详细结果可在以下文件中找到:
- JSON: `{result_file.name}`
- YAML: `{result_file.stem}.yaml`

## 后续步骤

1. 使用 `result_analyzer.py` 进行深入分析
2. 使用 `report_generator.py` 生成可视化报告
3. 比较不同 AI 代理或配置的表现

---

*报告生成时间: {datetime.now().isoformat()}*
"""

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"报告已生成: {report_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='CTF 基准测试运行器')
    parser.add_argument('--config', '-c', required=True,
                       help='基准测试配置文件路径')
    parser.add_argument('--output', '-o', default='./results',
                       help='输出目录路径')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 验证配置文件
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"配置文件不存在: {config_path}")
        sys.exit(1)

    # 创建输出目录
    output_dir = Path(args.output)

    # 运行基准测试
    try:
        runner = BenchmarkRunner(config_path, output_dir)
        runner.run_benchmark()
        logger.info("基准测试运行完成")
    except Exception as e:
        logger.error(f"基准测试运行失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()