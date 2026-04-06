#!/usr/bin/env python3
"""
CTF 基准测试结果分析器

分析基准测试结果，生成详细统计和比较报告。
"""

import os
import sys
import json
import yaml
import logging
import argparse
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ResultAnalyzer:
    """结果分析器"""

    def __init__(self, result_paths: List[Path], output_dir: Path):
        self.result_paths = result_paths
        self.output_dir = output_dir
        self.results = []
        self.analysis = {}

    def load_results(self):
        """加载所有结果文件"""
        logger.info(f"加载 {len(self.result_paths)} 个结果文件")

        for result_path in self.result_paths:
            try:
                if result_path.suffix == '.json':
                    with open(result_path, 'r', encoding='utf-8') as f:
                        result = json.load(f)
                elif result_path.suffix in ['.yaml', '.yml']:
                    with open(result_path, 'r', encoding='utf-8') as f:
                        result = yaml.safe_load(f)
                else:
                    logger.warning(f"不支持的结果文件格式: {result_path.suffix}")
                    continue

                # 添加源文件信息
                result['_source_file'] = result_path.name
                result['_source_path'] = str(result_path)
                self.results.append(result)

                logger.info(f"加载结果: {result.get('benchmark', 'unknown')} - {result_path.name}")

            except Exception as e:
                logger.error(f"加载结果文件失败 {result_path}: {e}")

    def analyze_results(self):
        """分析结果"""
        if not self.results:
            logger.warning("没有可分析的结果")
            return

        logger.info(f"分析 {len(self.results)} 个基准测试结果")

        # 基本统计
        self.analysis['basic_stats'] = self._calculate_basic_stats()

        # 挑战级别分析
        self.analysis['challenge_analysis'] = self._analyze_challenges()

        # 跨基准测试比较
        self.analysis['comparative_analysis'] = self._compare_benchmarks()

        # 时间趋势分析（如果有多个时间点的结果）
        self.analysis['trend_analysis'] = self._analyze_trends()

        # 性能指标分布
        self.analysis['performance_distribution'] = self._analyze_distributions()

    def _calculate_basic_stats(self) -> Dict[str, Any]:
        """计算基本统计"""
        stats = {
            'total_benchmarks': len(self.results),
            'benchmarks': [],
            'aggregate_metrics': {
                'total_challenges': 0,
                'completed_challenges': 0,
                'success_rate': 0.0,
                'avg_duration': 0.0,
                'avg_steps': 0.0,
                'avg_score': 0.0,
            }
        }

        success_rates = []
        durations = []
        steps = []
        scores = []

        for result in self.results:
            metrics = result.get('metrics', {})
            benchmark_info = {
                'name': result.get('benchmark', 'unknown'),
                'source_file': result.get('_source_file'),
                'metrics': metrics,
            }
            stats['benchmarks'].append(benchmark_info)

            # 收集指标用于聚合
            stats['aggregate_metrics']['total_challenges'] += metrics.get('total_challenges', 0)
            stats['aggregate_metrics']['completed_challenges'] += metrics.get('completed', 0)

            success_rate = metrics.get('success_rate', 0.0)
            if success_rate is not None:
                success_rates.append(success_rate)

            duration = metrics.get('average_duration', 0.0)
            if duration is not None:
                durations.append(duration)

            step = metrics.get('average_steps', 0.0)
            if step is not None:
                steps.append(step)

            score = metrics.get('average_score', 0.0)
            if score is not None:
                scores.append(score)

        # 计算聚合统计
        if success_rates:
            stats['aggregate_metrics']['success_rate'] = statistics.mean(success_rates)
            stats['aggregate_metrics']['success_rate_std'] = statistics.stdev(success_rates) if len(success_rates) > 1 else 0

        if durations:
            stats['aggregate_metrics']['avg_duration'] = statistics.mean(durations)
            stats['aggregate_metrics']['duration_std'] = statistics.stdev(durations) if len(durations) > 1 else 0

        if steps:
            stats['aggregate_metrics']['avg_steps'] = statistics.mean(steps)
            stats['aggregate_metrics']['steps_std'] = statistics.stdev(steps) if len(steps) > 1 else 0

        if scores:
            stats['aggregate_metrics']['avg_score'] = statistics.mean(scores)
            stats['aggregate_metrics']['score_std'] = statistics.stdev(scores) if len(scores) > 1 else 0

        return stats

    def _analyze_challenges(self) -> Dict[str, Any]:
        """分析挑战级别表现"""
        challenge_stats = {}

        for result in self.results:
            benchmark_name = result.get('benchmark', 'unknown')
            challenges = result.get('challenges', [])

            for challenge in challenges:
                challenge_id = challenge.get('challenge_id')
                if not challenge_id:
                    continue

                if challenge_id not in challenge_stats:
                    challenge_stats[challenge_id] = {
                        'attempts': 0,
                        'completions': 0,
                        'failures': 0,
                        'durations': [],
                        'steps': [],
                        'scores': [],
                        'hints_used': [],
                        'benchmarks': set(),
                    }

                stats = challenge_stats[challenge_id]
                stats['attempts'] += 1
                stats['benchmarks'].add(benchmark_name)

                status = challenge.get('status')
                if status == 'completed':
                    stats['completions'] += 1
                    stats['durations'].append(challenge.get('duration', 0))
                    stats['steps'].append(challenge.get('steps', 0))
                    stats['scores'].append(challenge.get('score', 0))
                    stats['hints_used'].append(challenge.get('hints_used', 0))
                elif status == 'failed':
                    stats['failures'] += 1

        # 计算挑战级别统计
        for challenge_id, stats in challenge_stats.items():
            attempts = stats['attempts']
            completions = stats['completions']

            stats['success_rate'] = completions / attempts if attempts > 0 else 0

            if stats['durations']:
                stats['avg_duration'] = statistics.mean(stats['durations'])
                stats['duration_std'] = statistics.stdev(stats['durations']) if len(stats['durations']) > 1 else 0
            else:
                stats['avg_duration'] = 0
                stats['duration_std'] = 0

            if stats['steps']:
                stats['avg_steps'] = statistics.mean(stats['steps'])
                stats['steps_std'] = statistics.stdev(stats['steps']) if len(stats['steps']) > 1 else 0
            else:
                stats['avg_steps'] = 0
                stats['steps_std'] = 0

            if stats['scores']:
                stats['avg_score'] = statistics.mean(stats['scores'])
                stats['score_std'] = statistics.stdev(stats['scores']) if len(stats['scores']) > 1 else 0
            else:
                stats['avg_score'] = 0
                stats['score_std'] = 0

            if stats['hints_used']:
                stats['avg_hints'] = statistics.mean(stats['hints_used'])
            else:
                stats['avg_hints'] = 0

            stats['benchmarks'] = list(stats['benchmarks'])

        return challenge_stats

    def _compare_benchmarks(self) -> Dict[str, Any]:
        """比较不同基准测试的表现"""
        if len(self.results) < 2:
            return {'message': '需要至少2个基准测试结果进行比较'}

        comparison = {
            'benchmark_names': [],
            'success_rates': [],
            'avg_durations': [],
            'avg_steps': [],
            'avg_scores': [],
        }

        for result in self.results:
            metrics = result.get('metrics', {})
            comparison['benchmark_names'].append(result.get('benchmark', 'unknown'))
            comparison['success_rates'].append(metrics.get('success_rate', 0))
            comparison['avg_durations'].append(metrics.get('average_duration', 0))
            comparison['avg_steps'].append(metrics.get('average_steps', 0))
            comparison['avg_scores'].append(metrics.get('average_score', 0))

        # 排名
        sorted_by_success = sorted(zip(comparison['benchmark_names'], comparison['success_rates']),
                                  key=lambda x: x[1], reverse=True)
        sorted_by_duration = sorted(zip(comparison['benchmark_names'], comparison['avg_durations']),
                                   key=lambda x: x[1])  # 时间越短越好
        sorted_by_steps = sorted(zip(comparison['benchmark_names'], comparison['avg_steps']),
                                key=lambda x: x[1])  # 步骤越少越好
        sorted_by_score = sorted(zip(comparison['benchmark_names'], comparison['avg_scores']),
                                key=lambda x: x[1], reverse=True)

        comparison['rankings'] = {
            'by_success_rate': [{'benchmark': name, 'success_rate': rate} for name, rate in sorted_by_success],
            'by_duration': [{'benchmark': name, 'duration': duration} for name, duration in sorted_by_duration],
            'by_steps': [{'benchmark': name, 'steps': steps} for name, steps in sorted_by_steps],
            'by_score': [{'benchmark': name, 'score': score} for name, score in sorted_by_score],
        }

        return comparison

    def _analyze_trends(self) -> Dict[str, Any]:
        """分析时间趋势（如果结果有时间戳）"""
        # 这里简化实现，实际中可以根据时间戳分析趋势
        return {
            'message': '趋势分析需要带时间戳的多次运行结果',
            'suggestion': '多次运行同一基准测试并包含时间戳以获得趋势数据'
        }

    def _analyze_distributions(self) -> Dict[str, Any]:
        """分析性能指标分布"""
        distributions = {
            'success_rate': {'values': [], 'min': 0, 'max': 0, 'mean': 0},
            'duration': {'values': [], 'min': 0, 'max': 0, 'mean': 0},
            'steps': {'values': [], 'min': 0, 'max': 0, 'mean': 0},
            'score': {'values': [], 'min': 0, 'max': 0, 'mean': 0},
        }

        for result in self.results:
            metrics = result.get('metrics', {})
            distributions['success_rate']['values'].append(metrics.get('success_rate', 0))
            distributions['duration']['values'].append(metrics.get('average_duration', 0))
            distributions['steps']['values'].append(metrics.get('average_steps', 0))
            distributions['score']['values'].append(metrics.get('average_score', 0))

        for key, dist in distributions.items():
            values = dist['values']
            if values:
                dist['min'] = min(values)
                dist['max'] = max(values)
                dist['mean'] = statistics.mean(values)
                dist['std'] = statistics.stdev(values) if len(values) > 1 else 0
                dist['count'] = len(values)

        return distributions

    def save_analysis(self):
        """保存分析结果"""
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 生成分析文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_file = self.output_dir / f"analysis_{timestamp}.json"

        # 保存 JSON 分析结果
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis, f, indent=2, ensure_ascii=False)

        # 生成分析报告
        self.generate_analysis_report(analysis_file)

        logger.info(f"分析结果已保存: {analysis_file}")

    def generate_analysis_report(self, analysis_file: Path):
        """生成分析报告"""
        report_file = analysis_file.with_suffix('.md')

        basic_stats = self.analysis.get('basic_stats', {})
        aggregate = basic_stats.get('aggregate_metrics', {})

        report = f"""# CTF 基准测试分析报告

**分析时间**: {datetime.now().isoformat()}
**分析结果文件**: {analysis_file.name}

## 概述

- **分析基准测试数量**: {basic_stats.get('total_benchmarks', 0)}
- **总挑战数**: {aggregate.get('total_challenges', 0)}
- **完成挑战数**: {aggregate.get('completed_challenges', 0)}
- **平均成功率**: {aggregate.get('success_rate', 0):.2%} (±{aggregate.get('success_rate_std', 0):.2%})

## 聚合指标

| 指标 | 平均值 | 标准差 |
|------|--------|--------|
| 成功率 | {aggregate.get('success_rate', 0):.2%} | {aggregate.get('success_rate_std', 0):.2%} |
| 平均耗时 | {aggregate.get('avg_duration', 0):.2f} 秒 | {aggregate.get('duration_std', 0):.2f} |
| 平均步骤 | {aggregate.get('avg_steps', 0):.2f} | {aggregate.get('steps_std', 0):.2f} |
| 平均得分 | {aggregate.get('avg_score', 0):.2f} | {aggregate.get('score_std', 0):.2f} |

## 基准测试详情

| 基准测试 | 挑战数 | 完成数 | 成功率 | 平均耗时 | 平均步骤 | 平均得分 |
|----------|--------|--------|--------|----------|----------|----------|
"""

        for benchmark in basic_stats.get('benchmarks', []):
            metrics = benchmark.get('metrics', {})
            report += f"| {benchmark.get('name', 'N/A')} "
            report += f"| {metrics.get('total_challenges', 0)} "
            report += f"| {metrics.get('completed', 0)} "
            report += f"| {metrics.get('success_rate', 0):.2%} "
            report += f"| {metrics.get('average_duration', 0):.2f} "
            report += f"| {metrics.get('average_steps', 0):.2f} "
            report += f"| {metrics.get('average_score', 0):.2f} |\n"

        # 挑战分析部分
        challenge_analysis = self.analysis.get('challenge_analysis', {})
        if challenge_analysis:
            report += f"""

## 挑战表现分析

共分析 {len(challenge_analysis)} 个不同挑战。

### 最具挑战性的挑战（成功率最低）

"""
            # 按成功率排序
            sorted_challenges = sorted(
                challenge_analysis.items(),
                key=lambda x: x[1].get('success_rate', 0)
            )[:5]  # 前5个最难挑战

            for challenge_id, stats in sorted_challenges:
                report += f"- **{challenge_id}**: {stats.get('success_rate', 0):.2%} 成功率 "
                report += f"({stats.get('completions', 0)}/{stats.get('attempts', 0)} 完成)\n"

        # 比较分析部分
        comparative = self.analysis.get('comparative_analysis', {})
        if comparative.get('rankings'):
            report += f"""

## 基准测试排名

### 按成功率排名
"""
            for i, item in enumerate(comparative['rankings']['by_success_rate'][:5], 1):
                report += f"{i}. **{item['benchmark']}**: {item['success_rate']:.2%}\n"

        report += f"""

## 详细分析

详细分析数据可在以下文件中找到:
- JSON: `{analysis_file.name}`
- 使用 Python 或数据分析工具进行进一步分析

## 建议

1. **改进建议**: 关注成功率低于 50% 的挑战
2. **优化方向**: 减少平均步骤数和完成时间
3. **比较分析**: 运行不同 AI 代理配置以找到最优设置

---

*报告生成时间: {datetime.now().isoformat()}*
"""

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"分析报告已生成: {report_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='CTF 基准测试结果分析器')
    parser.add_argument('--results', '-r', required=True, nargs='+',
                       help='结果文件路径（支持多个）')
    parser.add_argument('--output', '-o', default='./analysis',
                       help='输出目录路径')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 验证结果文件
    result_paths = []
    for result_path in args.results:
        path = Path(result_path)
        if path.exists():
            result_paths.append(path)
        else:
            logger.error(f"结果文件不存在: {path}")

    if not result_paths:
        logger.error("没有有效的结果文件")
        sys.exit(1)

    # 创建输出目录
    output_dir = Path(args.output)

    # 运行分析
    try:
        analyzer = ResultAnalyzer(result_paths, output_dir)
        analyzer.load_results()
        analyzer.analyze_results()
        analyzer.save_analysis()
        logger.info("结果分析完成")
    except Exception as e:
        logger.error(f"结果分析失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()