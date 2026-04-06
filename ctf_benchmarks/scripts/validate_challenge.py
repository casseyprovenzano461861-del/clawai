#!/usr/bin/env python3
"""
CTF 挑战配置验证器

验证挑战配置文件的格式、完整性和一致性。
"""

import os
import sys
import json
import yaml
import logging
import argparse
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChallengeValidator:
    """挑战验证器"""

    # 必需字段定义
    REQUIRED_FIELDS = ['id', 'name', 'platform', 'category', 'difficulty', 'points']

    # 有效平台列表
    VALID_PLATFORMS = ['picoctf', 'overthewire', 'ctftime', 'custom']

    # 有效类别列表
    VALID_CATEGORIES = ['web', 'linux', 'binary', 'crypto', 'forensics', 'misc']

    # 有效难度级别
    VALID_DIFFICULTIES = ['very_easy', 'easy', 'medium', 'hard', 'expert']

    # 标志格式正则表达式
    FLAG_REGEXES = {
        'picoctf': r'picoCTF\{.*\}',
        'overthewire': r'[A-Za-z0-9]{10,}',  # 实际标志格式因挑战而异
        'general': r'.{10,}',  # 通用标志格式
    }

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = None
        self.errors = []
        self.warnings = []
        self.valid = False

    def load_config(self) -> bool:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.suffix in ['.yaml', '.yml']:
                    self.config = yaml.safe_load(f)
                elif self.config_path.suffix == '.json':
                    self.config = json.load(f)
                else:
                    self.errors.append(f"不支持的配置文件格式: {self.config_path.suffix}")
                    return False
            return True
        except Exception as e:
            self.errors.append(f"加载配置文件失败: {e}")
            return False

    def validate(self) -> bool:
        """执行验证"""
        if not self.load_config():
            return False

        logger.info(f"验证挑战配置: {self.config_path.name}")

        # 验证必需字段
        self.validate_required_fields()

        # 验证字段值
        if self.config:
            self.validate_field_values()
            self.validate_solution()
            self.validate_test_cases()
            self.validate_metrics()
            self.validate_container_config()
            self.validate_agent_config()

        # 检查错误和警告
        if self.errors:
            logger.error(f"验证失败，发现 {len(self.errors)} 个错误")
            for error in self.errors:
                logger.error(f"  ✗ {error}")
            self.valid = False
        else:
            if self.warnings:
                logger.warning(f"验证通过，但有 {len(self.warnings)} 个警告")
                for warning in self.warnings:
                    logger.warning(f"  ⚠ {warning}")
            else:
                logger.info("验证通过，无错误或警告")
            self.valid = True

        return self.valid

    def validate_required_fields(self):
        """验证必需字段"""
        if not self.config:
            return

        for field in self.REQUIRED_FIELDS:
            if field not in self.config:
                self.errors.append(f"缺少必需字段: {field}")

    def validate_field_values(self):
        """验证字段值"""
        # 验证平台
        platform = self.config.get('platform', '').lower()
        if platform and platform not in self.VALID_PLATFORMS:
            self.warnings.append(f"未知平台: {platform}，有效平台: {', '.join(self.VALID_PLATFORMS)}")

        # 验证类别
        category = self.config.get('category', '').lower()
        if category and category not in self.VALID_CATEGORIES:
            self.warnings.append(f"未知类别: {category}，有效类别: {', '.join(self.VALID_CATEGORIES)}")

        # 验证难度
        difficulty = self.config.get('difficulty', '').lower()
        if difficulty and difficulty not in self.VALID_DIFFICULTIES:
            self.warnings.append(f"未知难度: {difficulty}，有效难度: {', '.join(self.VALID_DIFFICULTIES)}")

        # 验证分值
        points = self.config.get('points')
        if points is not None:
            if not isinstance(points, (int, float)):
                self.errors.append(f"分值必须是数字: {points}")
            elif points < 0:
                self.warnings.append(f"分值为负数: {points}")

        # 验证ID格式
        challenge_id = self.config.get('id', '')
        if challenge_id:
            # ID 应只包含字母、数字、连字符和下划线
            if not re.match(r'^[a-zA-Z0-9_-]+$', challenge_id):
                self.warnings.append(f"挑战ID包含特殊字符: {challenge_id}，建议只使用字母、数字、连字符和下划线")

    def validate_solution(self):
        """验证解决方案"""
        solution = self.config.get('solution')
        validation_regex = self.config.get('validation_regex')

        if solution is None:
            self.warnings.append("未提供解决方案（solution字段）")
        elif not isinstance(solution, str):
            self.errors.append("解决方案必须是字符串")

        if validation_regex:
            try:
                re.compile(validation_regex)
            except re.error as e:
                self.errors.append(f"验证正则表达式无效: {e}")

            # 检查解决方案是否匹配验证正则表达式
            if solution and validation_regex:
                try:
                    if not re.match(validation_regex, solution):
                        self.errors.append(f"解决方案不匹配验证正则表达式: {solution} 不匹配 {validation_regex}")
                except re.error:
                    pass  # 正则表达式错误已在前面捕获

    def validate_test_cases(self):
        """验证测试用例"""
        test_cases = self.config.get('test_cases', [])

        if not test_cases:
            self.warnings.append("未定义测试用例")
            return

        for i, test_case in enumerate(test_cases):
            if not isinstance(test_case, dict):
                self.errors.append(f"测试用例 {i} 必须是字典")
                continue

            # 验证测试用例ID
            test_id = test_case.get('id')
            if not test_id:
                self.warnings.append(f"测试用例 {i} 缺少ID")

            # 验证命令
            command = test_case.get('command')
            if not command:
                self.warnings.append(f"测试用例 {i} 缺少命令")
            elif not isinstance(command, str):
                self.errors.append(f"测试用例 {i} 命令必须是字符串")

            # 验证超时
            timeout = test_case.get('timeout')
            if timeout is not None:
                if not isinstance(timeout, (int, float)):
                    self.errors.append(f"测试用例 {i} 超时必须是数字")
                elif timeout <= 0:
                    self.warnings.append(f"测试用例 {i} 超时非正数: {timeout}")

    def validate_metrics(self):
        """验证指标配置"""
        metrics = self.config.get('metrics', {})

        if not metrics:
            self.warnings.append("未定义指标配置")
            return

        # 验证最大步骤数
        max_steps = metrics.get('max_steps')
        if max_steps is not None:
            if not isinstance(max_steps, int):
                self.errors.append("max_steps 必须是整数")
            elif max_steps <= 0:
                self.warnings.append(f"max_steps 非正数: {max_steps}")

        # 验证最大时间
        max_time = metrics.get('max_time')
        if max_time is not None:
            if not isinstance(max_time, (int, float)):
                self.errors.append("max_time 必须是数字")
            elif max_time <= 0:
                self.warnings.append(f"max_time 非正数: {max_time}")

        # 验证Token预算
        token_budget = metrics.get('token_budget')
        if token_budget is not None:
            if not isinstance(token_budget, (int, float)):
                self.errors.append("token_budget 必须是数字")
            elif token_budget <= 0:
                self.warnings.append(f"token_budget 非正数: {token_budget}")

    def validate_container_config(self):
        """验证容器配置"""
        container_config = self.config.get('container_config')

        if not container_config:
            # 容器配置是可选的
            return

        if not isinstance(container_config, dict):
            self.errors.append("container_config 必须是字典")
            return

        # 验证镜像
        image = container_config.get('image')
        if not image:
            self.warnings.append("容器配置缺少镜像名称")
        elif not isinstance(image, str):
            self.errors.append("容器镜像必须是字符串")

        # 验证端口
        ports = container_config.get('ports', [])
        if ports:
            if not isinstance(ports, list):
                self.errors.append("容器端口必须是列表")
            else:
                for i, port in enumerate(ports):
                    if isinstance(port, str):
                        # 格式: "主机端口:容器端口"
                        if ':' not in port:
                            self.warnings.append(f"端口配置 {i} 格式不正确，应为 '主机端口:容器端口': {port}")
                    elif not isinstance(port, int):
                        self.warnings.append(f"端口配置 {i} 应为字符串或整数: {port}")

    def validate_agent_config(self):
        """验证AI代理配置"""
        agent_config = self.config.get('agent_config')

        if not agent_config:
            # 代理配置是可选的
            return

        if not isinstance(agent_config, dict):
            self.errors.append("agent_config 必须是字典")
            return

        # 验证观察空间
        observation_space = agent_config.get('observation_space')
        if observation_space:
            if not isinstance(observation_space, dict):
                self.errors.append("observation_space 必须是字典")

            max_length = observation_space.get('max_length')
            if max_length is not None:
                if not isinstance(max_length, int):
                    self.errors.append("observation_space.max_length 必须是整数")
                elif max_length <= 0:
                    self.warnings.append(f"observation_space.max_length 非正数: {max_length}")

        # 验证动作空间
        action_space = agent_config.get('action_space')
        if action_space:
            if not isinstance(action_space, dict):
                self.errors.append("action_space 必须是字典")

            allowed_commands = action_space.get('allowed_commands')
            if allowed_commands:
                if not isinstance(allowed_commands, list):
                    self.errors.append("action_space.allowed_commands 必须是列表")
                else:
                    for i, cmd in enumerate(allowed_commands):
                        if not isinstance(cmd, str):
                            self.warnings.append(f"allowed_commands[{i}] 必须是字符串: {cmd}")

    def get_validation_report(self) -> str:
        """获取验证报告"""
        report = []
        report.append(f"验证报告: {self.config_path.name}")
        report.append("=" * 60)

        if self.config:
            # 基本信息
            report.append(f"挑战ID: {self.config.get('id', 'N/A')}")
            report.append(f"名称: {self.config.get('name', 'N/A')}")
            report.append(f"平台: {self.config.get('platform', 'N/A')}")
            report.append(f"类别: {self.config.get('category', 'N/A')}")
            report.append(f"难度: {self.config.get('difficulty', 'N/A')}")
            report.append(f"分值: {self.config.get('points', 'N/A')}")
            report.append("")

        # 错误
        if self.errors:
            report.append("❌ 错误:")
            for error in self.errors:
                report.append(f"  • {error}")
            report.append("")

        # 警告
        if self.warnings:
            report.append("⚠️ 警告:")
            for warning in self.warnings:
                report.append(f"  • {warning}")
            report.append("")

        # 总结
        if self.errors:
            report.append(f"❌ 验证失败: {len(self.errors)} 个错误")
        elif self.warnings:
            report.append(f"✅ 验证通过，但有 {len(self.warnings)} 个警告")
        else:
            report.append("✅ 验证通过，无错误或警告")

        report.append("=" * 60)
        return "\n".join(report)


def validate_challenge_file(file_path: Path) -> Tuple[bool, str]:
    """验证单个挑战文件"""
    validator = ChallengeValidator(file_path)
    is_valid = validator.validate()
    report = validator.get_validation_report()
    return is_valid, report


def validate_challenge_directory(directory_path: Path) -> Dict[str, Tuple[bool, str]]:
    """验证目录中的所有挑战文件"""
    results = {}

    # 查找所有YAML和JSON文件
    yaml_files = list(directory_path.glob("*.yaml")) + list(directory_path.glob("*.yml"))
    json_files = list(directory_path.glob("*.json"))

    all_files = yaml_files + json_files

    logger.info(f"在目录中发现 {len(all_files)} 个挑战文件: {directory_path}")

    for file_path in all_files:
        is_valid, report = validate_challenge_file(file_path)
        results[file_path.name] = (is_valid, report)

    return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='CTF 挑战配置验证器')
    parser.add_argument('path', help='挑战文件或目录路径')
    parser.add_argument('--output', '-o', help='输出报告文件路径')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--summary', '-s', action='store_true', help='只显示摘要')

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    path = Path(args.path)

    if not path.exists():
        logger.error(f"路径不存在: {path}")
        sys.exit(1)

    all_reports = []

    if path.is_file():
        # 验证单个文件
        is_valid, report = validate_challenge_file(path)
        all_reports.append(report)

        if not args.summary:
            print(report)

        if not is_valid:
            logger.error("挑战文件验证失败")
            sys.exit(1)

    elif path.is_dir():
        # 验证目录中的所有文件
        results = validate_challenge_directory(path)

        valid_count = sum(1 for is_valid, _ in results.values() if is_valid)
        total_count = len(results)

        # 生成汇总报告
        summary = []
        summary.append(f"验证摘要: {path}")
        summary.append("=" * 60)
        summary.append(f"总文件数: {total_count}")
        summary.append(f"有效文件: {valid_count}")
        summary.append(f"无效文件: {total_count - valid_count}")
        summary.append("")

        # 文件状态
        for filename, (is_valid, report) in results.items():
            status = "✅" if is_valid else "❌"
            summary.append(f"{status} {filename}")

        summary.append("=" * 60)
        summary_report = "\n".join(summary)

        all_reports.append(summary_report)

        if not args.summary:
            print(summary_report)

            # 显示详细报告（可选）
            for filename, (is_valid, report) in results.items():
                if not is_valid or args.verbose:
                    print("\n" + "=" * 60)
                    print(f"详细报告: {filename}")
                    print("=" * 60)
                    print(report)

        if valid_count < total_count:
            logger.warning(f"部分文件验证失败: {valid_count}/{total_count} 通过")
            # 不退出，因为可能只是警告
    else:
        logger.error(f"无效的路径类型: {path}")
        sys.exit(1)

    # 输出报告到文件
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            for report in all_reports:
                f.write(report + "\n\n")
        logger.info(f"报告已保存到: {output_path}")


if __name__ == '__main__':
    main()