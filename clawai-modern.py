#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI - 现代界面启动脚本
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cli.modern_ui import main

if __name__ == "__main__":
    main()
