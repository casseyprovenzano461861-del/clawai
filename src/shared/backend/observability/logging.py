# -*- coding: utf-8 -*-
"""
日志管理模块
"""

import logging
import os
from logging.handlers import RotatingFileHandler


class LoggingManager:
    """日志管理类"""
    
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.loggers = {}
        self._initialize_logging()
    
    def _initialize_logging(self):
        """初始化日志配置"""
        # 创建日志目录
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # 基本配置
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def get_logger(self, name):
        """获取日志记录器"""
        if name not in self.loggers:
            logger = logging.getLogger(name)
            
            # 创建文件处理器
            log_file = os.path.join(self.log_dir, f"{name}.log")
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            
            # 设置文件处理器的格式
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            # 添加文件处理器到日志记录器
            logger.addHandler(file_handler)
            
            # 保存日志记录器
            self.loggers[name] = logger
        
        return self.loggers[name]
    
    def set_level(self, name, level):
        """设置日志级别"""
        logger = self.get_logger(name)
        logger.setLevel(level)
    
    def log(self, name, level, message):
        """记录日志"""
        logger = self.get_logger(name)
        if level == 'debug':
            logger.debug(message)
        elif level == 'info':
            logger.info(message)
        elif level == 'warning':
            logger.warning(message)
        elif level == 'error':
            logger.error(message)
        elif level == 'critical':
            logger.critical(message)
