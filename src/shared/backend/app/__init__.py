# -*- coding: utf-8 -*-
"""
Flask应用工厂
创建和配置Flask应用实例
"""

from flask import Flask
from flask_cors import CORS

from config import config
from backend.api import register_blueprints
from backend.app.middleware.error_handler import register_error_handlers
from backend.app.middleware.auth import setup_auth_routes


def create_app():
    """
    创建Flask应用实例
    
    Returns:
        Flask应用实例
    """
    # 创建Flask应用
    app = Flask(__name__)
    
    # 配置CORS
    CORS(app)
    
    # 应用配置
    app.config['SECRET_KEY'] = config.JWT_SECRET
    app.config['DEBUG'] = config.DEBUG
    
    # 注册认证路由
    app = setup_auth_routes(app)
    
    # 注册错误处理器
    app = register_error_handlers(app)
    
    # 注册API蓝图
    app = register_blueprints(app)
    
    return app
