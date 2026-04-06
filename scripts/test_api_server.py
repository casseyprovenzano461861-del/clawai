#!/usr/bin/env python3
"""
测试API服务器能否正常启动
"""

import sys
import os
import time
import socket
import threading
import subprocess
from pathlib import Path

def check_port_available(port: int, host: str = 'localhost') -> bool:
    """检查端口是否可用"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result != 0  # 端口未被占用
    except Exception as e:
        print(f"检查端口时出错: {e}")
        return False

def test_server_startup():
    """测试服务器启动"""
    print("=" * 60)
    print("测试 API 服务器启动")
    print("=" * 60)
    
    # 检查端口5000是否可用
    if not check_port_available(5000):
        print("⚠️  端口 5000 已被占用，尝试使用端口 5001")
        port = 5001
    else:
        port = 5000
    
    # 尝试导入API服务器模块
    print("1. 导入API服务器模块...")
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from backend.api_server import app
        
        print("✅ API服务器模块导入成功")
        
        # 检查Redis模块
        print("2. 检查Redis模块...")
        try:
            import redis
            print("✅ Redis模块导入成功")
        except ImportError as e:
            print(f"❌ Redis模块导入失败: {e}")
            return False
        
        # 检查配置
        print("3. 检查配置模块...")
        try:
            from config import config
            print("✅ 配置模块导入成功")
            
            # 验证配置
            errors = config.validate_config()
            if errors:
                print("⚠️  配置验证警告:")
                for error in errors:
                    print(f"   - {error}")
            else:
                print("✅ 配置验证通过")
        except Exception as e:
            print(f"❌ 配置模块检查失败: {e}")
            return False
        
        # 测试服务器启动（在单独的线程中）
        print(f"4. 尝试启动服务器（端口 {port}）...")
        
        # 修改配置中的端口
        os.environ['BACKEND_PORT'] = str(port)
        
        def run_server():
            try:
                app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
            except Exception as e:
                print(f"服务器运行错误: {e}")
        
        # 启动服务器线程
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # 等待服务器启动
        time.sleep(3)
        
        # 检查服务器是否响应
        print("5. 测试服务器响应...")
        try:
            import requests
            response = requests.get(f'http://localhost:{port}/health', timeout=5)
            if response.status_code == 200:
                print(f"✅ 服务器启动成功！状态码: {response.status_code}")
                print(f"响应内容: {response.json()}")
                
                # 测试详细健康检查
                print("6. 测试详细健康检查...")
                response = requests.get(f'http://localhost:{port}/health/detailed', timeout=5)
                if response.status_code == 200:
                    print(f"✅ 详细健康检查成功！")
                    
                    # 测试API文档
                    print("7. 测试API文档...")
                    response = requests.get(f'http://localhost:{port}/api-docs', timeout=5)
                    if response.status_code == 200:
                        print(f"✅ API文档访问成功！")
                        return True
                    else:
                        print(f"❌ API文档访问失败，状态码: {response.status_code}")
                        return False
                else:
                    print(f"❌ 详细健康检查失败，状态码: {response.status_code}")
                    return False
            else:
                print(f"❌ 服务器响应异常，状态码: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 服务器请求失败: {e}")
            return False
        except ImportError:
            print("⚠️  requests模块未安装，跳过请求测试")
            print("✅ 服务器启动测试完成（未进行HTTP请求测试）")
            return True
        
    except ImportError as e:
        print(f"[ERROR] API服务器模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"[ERROR] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("API服务器启动测试")
    print("=" * 60)
    
    success = test_server_startup()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ API服务器启动测试通过！")
        print("   服务器已成功启动，可以响应请求。")
        print("\n后续步骤:")
        print("1. 运行 'python backend/api_server.py' 启动完整服务器")
        print("2. 访问 http://localhost:5000/api-docs 查看API文档")
        print("3. 运行 'start.bat' 使用启动菜单")
    else:
        print("❌ API服务器启动测试失败")
        print("   请检查上述错误信息并修复问题。")
        print("\n常见问题:")
        print("1. 确保Redis模块已安装: 'pip install redis'")
        print("2. 检查Python依赖是否完整: 'pip install -r requirements.txt'")
        print("3. 确保端口5000未被其他应用占用")
    
    print("=" * 60)
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())