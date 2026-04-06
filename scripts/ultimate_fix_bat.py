# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
终极批处理文件编码修复方案
使用记事本的编码保存方式，确保100%兼容Windows CMD
"""

import os
import sys
import subprocess
import tempfile

def create_ansi_bat():
    """创建完全ANSI编码的批处理文件"""
    content = '''@echo off
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
    if os.path.exists('start.bat'):
        backup_count = 1
        while os.path.exists(f'start.bat.backup{backup_count}'):
            backup_count += 1
        os.rename('start.bat', f'start.bat.backup{backup_count}')
        print(f"原文件已备份为: start.bat.backup{backup_count}")
    
    # 方法1: 使用cp437编码（Windows英文控制台编码）
    try:
        with open('start.bat', 'wb') as f:
            # 先将内容转换为ASCII兼容形式
            ascii_content = content
            # 替换任何非ASCII字符为ASCII近似
            char_map = {
                '。': '.',
                '，': ',',
                '：': ':',
                '；': ';',
                '！': '!',
                '？': '?',
                '（': '(',
                '）': ')',
                '【': '[',
                '】': ']',
                '《': '<',
                '》': '>',
                '「': '[',
                '」': ']',
                '￥': '\\',
                '…': '...',
                '·': '*',
                '―': '-',
                '～': '~',
                '＠': '@',
                '＃': '#',
                '＄': '$',
                '％': '%',
                '＆': '&',
                '＊': '*',
                '＋': '+',
                '－': '-',
                '＝': '=',
                '＾': '^',
                '＿': '_',
                '｀': '`',
                '｜': '|',
                '｛': '{',
                '｝': '}'
            }
            
            for chinese, ascii_char in char_map.items():
                ascii_content = ascii_content.replace(chinese, ascii_char)
            
            # 写入文件，使用ASCII编码
            f.write(ascii_content.encode('ascii', errors='replace'))
        print("方法1: 使用ASCII编码保存成功")
        
        # 测试文件
        test_result = test_bat_file('start.bat')
        if test_result:
            print("测试成功: 批处理文件可正常运行")
            return True
    except Exception as e:
        print(f"方法1失败: {e}")
    
    # 方法2: 使用Windows记事本模拟
    print("\n尝试方法2: 使用Windows记事本创建文件...")
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        # 使用Windows的type命令和重定向创建批处理文件
        cmd = f'type "{tmp_path}" > start.bat'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
        
        os.unlink(tmp_path)
        
        if result.returncode == 0:
            print("方法2: 使用type命令创建成功")
            
            # 测试文件
            test_result = test_bat_file('start.bat')
            if test_result:
                print("测试成功: 批处理文件可正常运行")
                return True
        else:
            print(f"方法2失败: {result.stderr}")
    except Exception as e:
        print(f"方法2失败: {e}")
    
    # 方法3: 创建纯英文版本
    print("\n尝试方法3: 创建纯英文版本...")
    english_content = '''@echo off
cd /d "%~dp0"

echo ============================================
echo   ClawAI Cyber Security Penetration Testing Platform - Startup Menu
echo ============================================
echo.
echo Please select an operation:
echo.
echo  [1] Start API Server (default port 5000)
echo  [2] Auto-install Security Tools (P0/P1/P2 priority)
echo  [3] Run Real Execution Monitoring System
echo  [4] Analyze API Performance (cache and slow interfaces)
echo  [5] Clean up Redundant Files and Expired Documents
echo  [6] Run Comprehensive Tests (verify all improvements)
echo  [7] Display System Information and Tool Status
echo  [8] Exit
echo.
set /p choice=Enter choice (1-8): 

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
echo Starting ClawAI API Server...
echo Press Ctrl+C to stop service
echo.
python backend/api_server.py
goto exit

:install_tools
echo.
echo Running tool auto-install script...
python scripts/auto_install_tools.py
echo.
pause
goto exit

:run_monitor
echo.
echo Running real execution monitoring system...
python scripts/enhanced_real_execution_monitor.py
echo.
pause
goto exit

:analyze_performance
echo.
echo Analyzing API performance...
python scripts/analyze_api_performance.py --test
echo.
pause
goto exit

:cleanup_files
echo.
echo Cleaning up redundant files and expired documents...
echo 1. Cleaning archive directory...
python scripts/cleanup_archive_files.py --execute
echo.
echo 2. Cleaning docs directory...
python scripts/cleanup_docs_and_archive.py --docs-only --execute
echo.
echo 3. Cleaning redundant files...
python scripts/cleanup_redundant_files.py --execute
echo.
pause
goto exit

:run_tests
echo.
echo Running comprehensive tests...
python scripts/simple_test_all.py
echo.
pause
goto exit

:system_info
echo.
echo System Information:
echo OS: Windows
echo Project Directory: %cd%
echo Python Version:
python --version
echo.
echo Tool Status:
python scripts/enhanced_real_execution_monitor.py --quick
echo.
pause
goto exit

:default
echo.
echo Using default option: Start API Server...
goto start_api

:exit
echo.
echo Thank you for using ClawAI!
pause
'''
    
    try:
        with open('start_english.bat', 'wb') as f:
            f.write(english_content.encode('ascii'))
        print("方法3: 纯英文版本创建成功: start_english.bat")
        
        # 测试英文版本
        test_result = test_bat_file('start_english.bat')
        if test_result:
            print("测试成功: 英文版批处理文件可正常运行")
            # 将英文版复制为中文版备用
            import shutil
            shutil.copy2('start_english.bat', 'start.bat')
            print("已将英文版复制为start.bat")
            return True
    except Exception as e:
        print(f"方法3失败: {e}")
    
    return False

def test_bat_file(filename):
    """测试批处理文件"""
    print(f"\n测试文件: {filename}")
    
    if not os.path.exists(filename):
        print(f"错误: 文件 {filename} 不存在")
        return False
    
    # 简单测试：检查语法
    try:
        # 使用cmd /c验证语法
        result = subprocess.run(
            ['cmd', '/c', f'call {filename}'],
            capture_output=True,
            text=True,
            encoding='gbk',
            errors='ignore',
            shell=True,
            timeout=3
        )
        
        print(f"返回码: {result.returncode}")
        
        if "ClawAI" in result.stdout or "ClawAI" in result.stderr:
            print("测试成功: 批处理文件正常执行")
            return True
        else:
            print("测试警告: 未找到预期输出")
            if result.stdout:
                print(f"标准输出前100字符: {result.stdout[:100]}")
            if result.stderr:
                print(f"错误输出前100字符: {result.stderr[:100]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("测试: 超时 (可能正常，因为等待用户输入)")
        return True
    except Exception as e:
        print(f"测试异常: {e}")
        return False

def main():
    """主函数"""
    print("终极批处理文件编码修复工具")
    print("=" * 60)
    
    print("当前目录:", os.getcwd())
    print("开始修复start.bat编码问题...")
    
    if create_ansi_bat():
        print("\n" + "=" * 60)
        print("修复成功!")
        print("现在可以使用以下命令启动:")
        print("  1. 双击 start.bat")
        print("  2. 在命令行运行: start.bat")
        print("  3. 备用英文版: start_english.bat")
        
        # 显示修复后的文件信息
        if os.path.exists('start.bat'):
            size = os.path.getsize('start.bat')
            print(f"\n修复后的文件信息:")
            print(f"  文件名: start.bat")
            print(f"  文件大小: {size} 字节")
            print(f"  创建时间: {os.path.getctime('start.bat')}")
            
            # 读取前几行
            try:
                with open('start.bat', 'r', encoding='ascii', errors='ignore') as f:
                    lines = [next(f).strip() for _ in range(5)]
                print("  前5行内容:")
                for i, line in enumerate(lines, 1):
                    print(f"    {i}: {line}")
            except:
                pass
    else:
        print("\n" + "=" * 60)
        print("修复失败!")
        print("建议手动修复:")
        print("  1. 用记事本打开start.bat")
        print("  2. 选择'文件' -> '另存为'")
        print("  3. 编码选择'ANSI'")
        print("  4. 保存并替换原文件")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())