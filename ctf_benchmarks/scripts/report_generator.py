#!/usr/bin/env python3
"""
CTF 基准测试报告生成器

生成详细的基准测试报告，包括可视化图表和深入分析。
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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """报告生成器"""

    def __init__(self, input_paths: List[Path], output_dir: Path, format: str = "html"):
        self.input_paths = input_paths
        self.output_dir = output_dir
        self.format = format
        self.data = {}
        self.report_content = ""

    def load_data(self):
        """加载数据文件"""
        logger.info(f"加载 {len(self.input_paths)} 个数据文件")

        for input_path in self.input_paths:
            try:
                if input_path.suffix == '.json':
                    with open(input_path, 'r', encoding='utf-8') as f:
                        content = json.load(f)
                elif input_path.suffix in ['.yaml', '.yml']:
                    with open(input_path, 'r', encoding='utf-8') as f:
                        content = yaml.safe_load(f)
                else:
                    logger.warning(f"不支持的文件格式: {input_path.suffix}")
                    continue

                # 存储数据
                key = input_path.stem
                self.data[key] = content
                logger.info(f"加载数据: {key} - {input_path.name}")

            except Exception as e:
                logger.error(f"加载数据文件失败 {input_path}: {e}")

    def generate_report(self):
        """生成报告"""
        logger.info(f"生成 {self.format.upper()} 格式报告")

        if self.format.lower() == "html":
            self.generate_html_report()
        elif self.format.lower() == "markdown":
            self.generate_markdown_report()
        else:
            logger.error(f"不支持的报告格式: {self.format}")
            return

        self.save_report()

    def generate_html_report(self):
        """生成 HTML 报告"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CTF 基准测试报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
        }}
        h1, h2, h3 {{
            color: #2d3748;
        }}
        h1 {{
            color: white;
            margin: 0;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 2rem 0;
        }}
        .metric-card {{
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border-left: 4px solid #667eea;
        }}
        .metric-value {{
            font-size: 2rem;
            font-weight: bold;
            color: #4a5568;
        }}
        .metric-label {{
            color: #718096;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background-color: #f7fafc;
            font-weight: 600;
            color: #4a5568;
        }}
        tr:hover {{
            background-color: #f7fafc;
        }}
        .success {{
            color: #38a169;
        }}
        .warning {{
            color: #d69e2e;
        }}
        .error {{
            color: #e53e3e;
        }}
        .charts {{
            margin: 2rem 0;
            padding: 1.5rem;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .chart-placeholder {{
            background: #f7fafc;
            border: 2px dashed #cbd5e0;
            border-radius: 8px;
            padding: 3rem;
            text-align: center;
            color: #718096;
            margin: 1rem 0;
        }}
        footer {{
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid #e2e8f0;
            color: #718096;
            font-size: 0.9rem;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        .badge-success {{
            background-color: #c6f6d5;
            color: #22543d;
        }}
        .badge-warning {{
            background-color: #feebc8;
            color: #744210;
        }}
        .badge-error {{
            background-color: #fed7d7;
            color: #742a2a;
        }}
    </style>
</head>
<body>
    <header>
        <h1>CTF 基准测试分析报告</h1>
        <p>生成时间: {timestamp}</p>
    </header>

    <section>
        <h2>📊 执行概览</h2>
        <div class="summary">
"""

        # 生成概览指标卡片
        if self.data:
            # 计算总体指标
            total_challenges = 0
            completed_challenges = 0
            success_rates = []
            durations = []

            for key, content in self.data.items():
                if 'metrics' in content:
                    metrics = content['metrics']
                    total_challenges += metrics.get('total_challenges', 0)
                    completed_challenges += metrics.get('completed', 0)
                    success_rates.append(metrics.get('success_rate', 0))
                    durations.append(metrics.get('average_duration', 0))

            avg_success_rate = statistics.mean(success_rates) if success_rates else 0
            avg_duration = statistics.mean(durations) if durations else 0

            html += f"""
            <div class="metric-card">
                <div class="metric-value">{len(self.data)}</div>
                <div class="metric-label">基准测试数量</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{total_challenges}</div>
                <div class="metric-label">总挑战数</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{completed_challenges}</div>
                <div class="metric-label">完成挑战数</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{avg_success_rate:.1%}</div>
                <div class="metric-label">平均成功率</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{avg_duration:.1f}s</div>
                <div class="metric-label">平均耗时</div>
            </div>
        """

        html += """
        </div>
    </section>

    <section>
        <h2>📈 基准测试详情</h2>
        <table>
            <thead>
                <tr>
                    <th>基准测试</th>
                    <th>挑战数</th>
                    <th>完成数</th>
                    <th>成功率</th>
                    <th>平均耗时</th>
                    <th>平均步骤</th>
                    <th>状态</th>
                </tr>
            </thead>
            <tbody>
"""

        # 生成表格行
        for key, content in self.data.items():
            metrics = content.get('metrics', {})
            success_rate = metrics.get('success_rate', 0)
            status_class = "success" if success_rate >= 0.7 else "warning" if success_rate >= 0.5 else "error"
            status_badge = "badge-success" if success_rate >= 0.7 else "badge-warning" if success_rate >= 0.5 else "badge-error"
            status_text = "优秀" if success_rate >= 0.7 else "良好" if success_rate >= 0.5 else "需改进"

            html += f"""
                <tr>
                    <td><strong>{content.get('benchmark', key)}</strong></td>
                    <td>{metrics.get('total_challenges', 0)}</td>
                    <td>{metrics.get('completed', 0)}</td>
                    <td class="{status_class}">{success_rate:.2%}</td>
                    <td>{metrics.get('average_duration', 0):.1f}s</td>
                    <td>{metrics.get('average_steps', 0):.1f}</td>
                    <td><span class="badge {status_badge}">{status_text}</span></td>
                </tr>
            """

        html += """
            </tbody>
        </table>
    </section>

    <section class="charts">
        <h2>📉 可视化分析</h2>
        <p>以下图表显示了关键指标的分布和趋势：</p>

        <div class="chart-placeholder">
            <h3>成功率分布图</h3>
            <p>📊 此处显示成功率分布的可视化图表</p>
            <p><em>提示: 在实际实现中，这里会显示 Matplotlib 或 Plotly 生成的图表</em></p>
        </div>

        <div class="chart-placeholder">
            <h3>完成时间趋势</h3>
            <p>⏱️ 此处显示完成时间随挑战难度的变化趋势</p>
            <p><em>提示: 使用时间序列图表展示性能改进</em></p>
        </div>

        <div class="chart-placeholder">
            <h3>挑战难度分析</h3>
            <p>🎯 此处显示各挑战的成功率和平均完成时间</p>
            <p><em>提示: 散点图显示挑战难度与成功率的关系</em></p>
        </div>
    </section>

    <section>
        <h2>🔍 详细分析</h2>
        <h3>数据文件</h3>
        <ul>
"""

        # 列出数据文件
        for key in self.data.keys():
            html += f'            <li><code>{key}</code> - 包含基准测试结果数据</li>\n'

        html += """
        </ul>

        <h3>关键发现</h3>
        <ul>
            <li><strong>表现最佳的挑战</strong>: 识别出成功率最高的挑战类型</li>
            <li><strong>需要改进的领域</strong>: 指出需要进一步优化的挑战类型</li>
            <li><strong>效率分析</strong>: 分析步骤数和完成时间的平衡关系</li>
            <li><strong>学习曲线</strong>: 评估随着时间推移的改进情况</li>
        </ul>

        <h3>建议</h3>
        <ol>
            <li><strong>针对性训练</strong>: 针对成功率低的挑战类型进行专项训练</li>
            <li><strong>参数优化</strong>: 调整 AI 代理的参数以提高效率</li>
            <li><strong>工具改进</strong>: 改进工具执行和服务配置</li>
            <li><strong>监控增强</strong>: 增强性能监控和调试能力</li>
        </ol>
    </section>

    <footer>
        <p><strong>CTF 基准测试框架</strong> - 基于 HackSynth 架构设计</p>
        <p>报告生成时间: {timestamp}</p>
        <p>© 2026 ClawAI 项目 - 仅供教育和研究使用</p>
    </footer>
</body>
</html>
"""

        self.report_content = html

    def generate_markdown_report(self):
        """生成 Markdown 报告"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        markdown = f"""# CTF 基准测试报告

**生成时间**: {timestamp}
**数据文件**: {len(self.data)} 个

## 执行概览

| 指标 | 值 |
|------|-----|
| 基准测试数量 | {len(self.data)} |
"""

        # 计算总体指标
        if self.data:
            total_challenges = 0
            completed_challenges = 0
            success_rates = []
            durations = []

            for key, content in self.data.items():
                if 'metrics' in content:
                    metrics = content['metrics']
                    total_challenges += metrics.get('total_challenges', 0)
                    completed_challenges += metrics.get('completed', 0)
                    success_rates.append(metrics.get('success_rate', 0))
                    durations.append(metrics.get('average_duration', 0))

            avg_success_rate = statistics.mean(success_rates) if success_rates else 0
            avg_duration = statistics.mean(durations) if durations else 0

            markdown += f"""| 总挑战数 | {total_challenges} |
| 完成挑战数 | {completed_challenges} |
| 平均成功率 | {avg_success_rate:.2%} |
| 平均耗时 | {avg_duration:.1f} 秒 |

## 基准测试详情

| 基准测试 | 挑战数 | 完成数 | 成功率 | 平均耗时 | 平均步骤 | 状态 |
|----------|--------|--------|--------|----------|----------|------|
"""

            # 生成表格行
            for key, content in self.data.items():
                metrics = content.get('metrics', {})
                success_rate = metrics.get('success_rate', 0)
                status_emoji = "✅" if success_rate >= 0.7 else "⚠️" if success_rate >= 0.5 else "❌"

                markdown += f"""| {content.get('benchmark', key)} | {metrics.get('total_challenges', 0)} | {metrics.get('completed', 0)} | {success_rate:.2%} | {metrics.get('average_duration', 0):.1f}s | {metrics.get('average_steps', 0):.1f} | {status_emoji} |
"""

        markdown += f"""
## 数据文件

共加载 {len(self.data)} 个数据文件：

"""

        for key in self.data.keys():
            markdown += f"- `{key}` - 基准测试结果数据\n"

        markdown += f"""
## 可视化

> **注意**: Markdown 报告中的图表需要转换为图像或使用 Mermaid 图表。

### 成功率分布
```mermaid
pie title 成功率分布
    "优秀 (≥70%)" : {sum(1 for content in self.data.values() if content.get('metrics', {}).get('success_rate', 0) >= 0.7)}
    "良好 (50-69%)" : {sum(1 for content in self.data.values() if 0.5 <= content.get('metrics', {}).get('success_rate', 0) < 0.7)}
    "需改进 (<50%)" : {sum(1 for content in self.data.values() if content.get('metrics', {}).get('success_rate', 0) < 0.5)}
```

## 分析与建议

### 关键发现
1. **表现模式**: 分析成功率的分布模式
2. **效率指标**: 评估时间效率和步骤效率
3. **一致性**: 检查不同基准测试间的一致性

### 改进建议
1. **挑战选择**: 根据成功率调整挑战选择策略
2. **参数调优**: 优化 AI 代理的配置参数
3. **工具增强**: 改进工具执行和监控
4. **训练重点**: 针对薄弱环节进行专项训练

### 后续步骤
1. 运行更多基准测试以获得统计显著性
2. 比较不同 AI 代理或配置的表现
3. 集成到持续集成流程中
4. 建立性能基线

---

**报告信息**
- 生成工具: CTF 基准测试报告生成器
- 数据来源: {', '.join(self.data.keys()) if self.data else '无'}
- 框架版本: 1.0.0
- 参考架构: HackSynth CTF 基准测试框架

*本报告基于实际基准测试结果生成，用于教育和研究目的。*
"""

        self.report_content = markdown

    def save_report(self):
        """保存报告"""
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 生成报告文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.format.lower() == "html":
            report_file = self.output_dir / f"report_{timestamp}.html"
        elif self.format.lower() == "markdown":
            report_file = self.output_dir / f"report_{timestamp}.md"
        else:
            report_file = self.output_dir / f"report_{timestamp}.txt"

        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(self.report_content)

        logger.info(f"报告已保存: {report_file}")

        # 生成辅助文件
        self.generate_supporting_files(report_file)

    def generate_supporting_files(self, report_file: Path):
        """生成辅助文件"""
        # 生成数据摘要
        summary_file = report_file.parent / f"data_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        summary = {
            'report_generated': datetime.now().isoformat(),
            'data_files': list(self.data.keys()),
            'summary_metrics': self._calculate_summary_metrics(),
            'report_file': str(report_file),
        }

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"数据摘要已保存: {summary_file}")

    def _calculate_summary_metrics(self) -> Dict[str, Any]:
        """计算摘要指标"""
        if not self.data:
            return {}

        metrics = {
            'total_benchmarks': len(self.data),
            'success_rates': [],
            'durations': [],
            'steps': [],
        }

        for content in self.data.values():
            if 'metrics' in content:
                metrics['success_rates'].append(content['metrics'].get('success_rate', 0))
                metrics['durations'].append(content['metrics'].get('average_duration', 0))
                metrics['steps'].append(content['metrics'].get('average_steps', 0))

        # 计算统计信息
        for key in ['success_rates', 'durations', 'steps']:
            values = metrics[key]
            if values:
                metrics[f'{key}_mean'] = statistics.mean(values)
                metrics[f'{key}_median'] = statistics.median(values)
                metrics[f'{key}_min'] = min(values)
                metrics[f'{key}_max'] = max(values)
                if len(values) > 1:
                    metrics[f'{key}_std'] = statistics.stdev(values)
                else:
                    metrics[f'{key}_std'] = 0

        return metrics


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='CTF 基准测试报告生成器')
    parser.add_argument('--input', '-i', required=True, nargs='+',
                       help='输入文件路径（支持多个）')
    parser.add_argument('--output', '-o', default='./reports',
                       help='输出目录路径')
    parser.add_argument('--format', '-f', choices=['html', 'markdown'], default='html',
                       help='报告格式')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 验证输入文件
    input_paths = []
    for input_path in args.input:
        path = Path(input_path)
        if path.exists():
            input_paths.append(path)
        else:
            logger.error(f"输入文件不存在: {path}")

    if not input_paths:
        logger.error("没有有效的输入文件")
        sys.exit(1)

    # 创建输出目录
    output_dir = Path(args.output)

    # 生成报告
    try:
        generator = ReportGenerator(input_paths, output_dir, args.format)
        generator.load_data()
        generator.generate_report()
        logger.info("报告生成完成")
    except Exception as e:
        logger.error(f"报告生成失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()