#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI 命令行入口
提供便捷的命令行访问方式
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cli.clawai_cli import cli

if __name__ == '__main__':
    cli()
