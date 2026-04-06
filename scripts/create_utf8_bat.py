# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
创建UTF-8 with BOM编码的批处理文件
"""

import os
import sys

def create_utf8_bat():
    """创建UTF-8 with BOM编码的批处理文件"""
    content = '''@echo off
chcp 65001 >nul 2>nul
cd /d "%~dp0"

echo ============================================
echo   ClawAI 网络安全渗透测试平台 - 启动菜单
echo ============================================
echo.
echo 请选择要执行的操作：
echo.
echo  [1] 启动 API 服务器 (默认端口 5000)
echo  [2] 自动安装安全工具 (P0/P1/P2 优先级)
echo  [3] 运行真实执行监控系统
echo  [4] 分析 API 性能 (缓存和慢速接口)
echo  [5] 清理冗余文件和过期文档
echo  [6] 运行综合测试 (验证所有改进)
echo  [7] 显示系统信息和工具状态
echo  [8] 退出
echo.
set /p choice=请输入选择 (1-8): 

if "%choice%"=="" goto default
if "%choice%"=="1" goto start_api
if "%choice%"=="2" goto install_tools
if "%choice%"=="3" goto run_monitor
if "%choice%"=="4" goto analyze_performance
if "%choice%"=="5" goto cleanup_files
if "%choice%"=="6" goto run_tests
if "%choice%"=="7" goto system_info
if "%choice%"=="8" goto exit

:start_api
echo.
echo 启动 ClawAI API 服务器...
echo 按 Ctrl+C 停止服务
echo.
python backend/api_server.py
goto exit

:install_tools
echo.
echo 运行工具自动安装脚本...
python scripts/auto_install_tools.py
echo.
pause
goto exit

:run_monitor
echo.
echo 运行真实执行监控系统...
python scripts/enhanced_real_execution_monitor.py
echo.
pause
goto exit

:analyze_performance
echo.
echo 分析 API 性能...
python scripts/analyze_api_performance.py --test
echo.
pause
goto exit

:cleanup_files
echo.
echo 清理冗余文件和过期文档...
echo 1. 清理 archive 目录...
python scripts/cleanup_archive_files.py --execute
echo.
echo 2. 清理 docs 目录...
python scripts/cleanup_docs_and_archive.py --docs-only --execute
echo.
echo 3. 清理冗余文件...
python scripts/cleanup_redundant_files.py --execute
echo.
pause
goto exit

:run_tests
echo.
echo 运行综合测试...
python scripts/simple_test_all.py
echo.
pause
goto exit

:system_info
echo.
echo 系统信息:
echo 操作系统: Windows
echo 项目目录: %cd%
echo Python 版本:
python --version
echo.
echo 工具状态:
python scripts/enhanced_real_execution_monitor.py --quick
echo.
pause
goto exit

:default
echo.
echo 使用默认选项：启动 API 服务器...
goto start_api

:exit
echo.
echo 感谢使用 ClawAI！
pause
'''
    
    # 备份原文件
    if os.path.exists('start_utf8.bat'):
        backup_count = 1
        while os.path.exists(f'start_utf8.bat.backup{backup_count}'):
            backup_count += 1
        os.rename('start_utf8.bat', f'start_utf8.bat.backup{backup_count}')
    
    # 保存为UTF-8 with BOM
    try:
        with open('start_utf8.bat', 'wb') as f:
            f.write(b'\xef\xbb\xbf')  # UTF-8 BOM
            f.write(content.encode('utf-8'))
        print("UTF-8 with BOM版本创建成功: start_utf8.bat")
        
        # 检查文件编码
        with open('start_utf8.bat', 'rb') as f:
            first_bytes = f.read(10)
            if first_bytes[:3] == b'\xef\xbb\xbf':
                print("验证: 文件包含UTF-8 BOM标记")
            else:
                print("警告: 文件可能不包含UTF-8 BOM标记")
        
        return True
    except Exception as e:
        print(f"创建失败: {e}")
        return False

def create_simple_test():
    """创建简单的UTF-8测试文件"""
    content = '''@echo off
chcp 65001 >nul 2>nul
echo UTF-8 测试: 中文显示正常
echo Test UTF-8: Chinese display correctly
pause
'''
    
    try:
        with open('test_utf8.bat', 'wb') as f:
            f.write(b'\xef\xbb\xbf')
            f.write(content.encode('utf-8'))
        print("UTF-8测试文件创建成功: test_utf8.bat")
        return True
    except Exception as e:
        print(f"创建测试文件失败: {e}")
        return False

def main():
    """主函数"""
    print("创建UTF-8编码批处理文件")
    print("=" * 60)
    
    # 创建测试文件
    if create_simple_test():
        print("\n简单测试文件创建成功")
        print("请运行 'test_utf8.bat' 测试UTF-8支持")
    
    # 创建完整版本
    if create_utf8_bat():
        print("\n完整UTF-8版本创建成功")
        print("请运行 'start_utf8.bat' 测试完整功能")
    
    print("\n" + "=" * 60)
    print("重要说明:")
    print("1. 这些文件使用UTF-8 with BOM编码")
    print("2. 文件开头设置了 'chcp 65001' 命令")
    print("3. 如果仍有问题，请确保:")
    print("   - Windows版本支持UTF-8代码页 (Windows 10 1809+ / Windows 11)")
    print("   - 控制台字体支持中文 (如'微软雅黑')")
    print("4. 备用方案: 使用英文版 'start_english_final.bat'")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())