"""
简化的API服务器 - 借鉴PentAGI的架构
用于快速测试和启动
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
import time

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 存储执行状态
execution_status = {
    "status": "idle",
    "last_execution": None,
    "active_tasks": 0
}

@app.route('/')
def index():
    """项目首页"""
    return jsonify({
        "project": "ClawAI - 智能安全评估系统",
        "version": "1.0.0",
        "description": "基于AI的自动化渗透测试平台",
        "endpoints": {
            "/": "项目首页",
            "/health": "健康检查",
            "/tools": "可用工具列表",
            "/scan": "执行安全扫描 (POST)",
            "/status": "执行状态"
        },
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/health')
def health():
    """健康检查接口"""
    return jsonify({
        "status": "healthy",
        "service": "ClawAI API Server",
        "version": "1.0.0",
        "uptime": "0",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/tools')
def get_tools():
    """获取可用工具列表"""
    # 模拟工具列表
    tools = [
        {
            "name": "nmap",
            "description": "网络扫描工具",
            "category": "reconnaissance",
            "status": "available",
            "command": "nmap"
        },
        {
            "name": "sqlmap",
            "description": "SQL注入检测工具",
            "category": "exploitation",
            "status": "available",
            "command": "sqlmap"
        },
        {
            "name": "nikto",
            "description": "Web服务器扫描工具",
            "category": "scanning",
            "status": "available",
            "command": "nikto"
        },
        {
            "name": "dirsearch",
            "description": "Web路径扫描工具",
            "category": "scanning",
            "status": "available",
            "command": "dirsearch"
        }
    ]
    
    return jsonify({
        "tools": tools,
        "count": len(tools),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/scan', methods=['POST'])
def scan():
    """执行安全扫描"""
    data = request.json
    
    if not data or 'target' not in data:
        return jsonify({
            "error": "缺少目标参数",
            "message": "请提供目标地址 (target)"
        }), 400
    
    target = data['target']
    scan_type = data.get('type', 'quick')
    
    # 更新执行状态
    execution_status["status"] = "scanning"
    execution_status["last_execution"] = time.time()
    execution_status["active_tasks"] += 1
    
    # 模拟扫描结果
    scan_results = {
        "target": target,
        "scan_type": scan_type,
        "status": "completed",
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "findings": [
            {
                "type": "open_port",
                "severity": "info",
                "description": f"在 {target} 上发现开放端口 80",
                "details": {"port": 80, "service": "http", "state": "open"}
            },
            {
                "type": "open_port",
                "severity": "info",
                "description": f"在 {target} 上发现开放端口 443",
                "details": {"port": 443, "service": "https", "state": "open"}
            },
            {
                "type": "vulnerability",
                "severity": "medium",
                "description": "发现潜在的SQL注入漏洞",
                "details": {"cve": "CVE-2023-1234", "risk": "中等"}
            }
        ],
        "summary": {
            "open_ports": 2,
            "vulnerabilities": 1,
            "scan_duration": "0.5秒"
        }
    }
    
    # 更新执行状态
    execution_status["status"] = "idle"
    execution_status["active_tasks"] -= 1
    
    return jsonify({
        "message": "扫描完成",
        "results": scan_results,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/status')
def status():
    """获取执行状态"""
    return jsonify({
        "execution_status": execution_status,
        "server_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "uptime": "0"
    })

@app.route('/api-docs')
def api_docs():
    """API文档"""
    docs = {
        "api_version": "1.0.0",
        "endpoints": {
            "GET /": "项目首页",
            "GET /health": "健康检查",
            "GET /tools": "获取可用工具列表",
            "POST /scan": "执行安全扫描",
            "GET /status": "获取执行状态",
            "GET /api-docs": "API文档 (当前页面)"
        },
        "examples": {
            "scan_request": {
                "method": "POST",
                "url": "/scan",
                "body": {
                    "target": "example.com",
                    "type": "quick"
                }
            }
        },
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return jsonify(docs)

if __name__ == '__main__':
    print("启动 ClawAI 简化API服务器...")
    print("服务地址: http://localhost:5000")
    print("API文档: http://localhost:5000/api-docs")
    print("健康检查: http://localhost:5000/health")
    print("按 Ctrl+C 停止服务器")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )