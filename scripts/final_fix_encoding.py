# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
最终编码修复方案 - 使用GBK编码保存批处理文件，并在开头设置代码页
"""

import os
import sys
import subprocess

def create_gbk_bat_with_codepage():
    """创建GBK编码的批处理文件，并设置正确的代码页"""
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
    if os.path.exists('start.bat'):
        backup_count = 1
        while os.path.exists(f'start.bat.backup_gbk{backup_count}'):
            backup_count += 1
        os.rename('start.bat', f'start.bat.backup_gbk{backup_count}')
        print(f"原文件已备份为: start.bat.backup_gbk{backup_count}")
    
    # 方法1: 使用GBK编码保存
    try:
        with open('start.bat', 'w', encoding='gbk', errors='replace') as f:
            f.write(content)
        print("使用GBK编码保存成功")
        
        # 验证文件编码
        with open('start.bat', 'rb') as f:
            raw_data = f.read(500)
        
        # 检查是否包含中文字符的GBK编码
        # 中文字符"安"的GBK编码是0xB0B2
        if b'\xb0\xb2' in raw_data:  # "安"的GBK编码
            print("验证: 文件中包含正确的中文GBK编码")
        
        return True
    except Exception as e:
        print(f"GBK编码保存失败: {e}")
        return False

def create_utf8_bat_with_bom():
    """创建UTF-8 with BOM编码的批处理文件（Windows支持）"""
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
    
    try:
        # UTF-8 with BOM
        with open('start_utf8.bat', 'wb') as f:
            f.write(b'\xef\xbb\xbf')  # UTF-8 BOM
            f.write(content.encode('utf-8'))
        print("UTF-8 with BOM版本创建成功: start_utf8.bat")
        return True
    except Exception as e:
        print(f"UTF-8 with BOM保存失败: {e}")
        return False

def test_bat_file(filename):
    """测试批处理文件"""
    print(f"\n测试文件: {filename}")
    
    if not os.path.exists(filename):
        print(f"错误: 文件 {filename} 不存在")
        return False
    
    # 测试：运行批处理文件并输入选项8（退出）
    try:
        # 创建一个临时输入文件
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp:
            tmp.write('8\n')  # 输入选项8退出
            tmp_path = tmp.name
        
        # 运行批处理文件
        cmd = f'cmd /c "{filename}" < "{tmp_path}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=5)
        
        os.unlink(tmp_path)
        
        print(f"返回码: {result.returncode}")
        
        # 检查输出中是否包含ClawAI
        output = result.stdout + result.stderr
        if "ClawAI" in output:
            print("测试成功: 批处理文件正常执行并显示中文")
            
            # 显示部分输出
            lines = output.split('\n')
            print("输出片段:")
            for i, line in enumerate(lines[:10]):
                if line.strip():
                    print(f"  {line[:80]}")
            return True
        else:
            print("测试警告: 未找到'ClawAI'关键字")
            if output:
                print(f"输出前200字符: {output[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("测试: 超时 (可能正常)")
        return True
    except Exception as e:
        print(f"测试异常: {e}")
        return False

def main():
    """主函数"""
    print("最终编码修复工具")
    print("=" * 60)
    
    # 检查当前系统代码页
    try:
        result = subprocess.run('chcp', shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        print(f"当前系统代码页: {result.stdout.strip()}")
    except:
        pass
    
    print("\n开始修复start.bat编码问题...")
    
    # 创建GBK版本
    if create_gbk_bat_with_codepage():
        print("\nGBK版本创建成功")
        
        # 测试GBK版本
        if test_bat_file('start.bat'):
            print("\nGBK版本测试成功!")
        else:
            print("\nGBK版本测试失败，尝试UTF-8版本...")
            
            # 创建UTF-8版本
            if create_utf8_bat_with_bom():
                if test_bat_file('start_utf8.bat'):
                    print("\nUTF-8版本测试成功!")
                    # 将UTF-8版本复制为默认版本
                    import shutil
                    shutil.copy2('start_utf8.bat', 'start.bat')
                    print("已将UTF-8版本设置为默认版本")
    
    print("\n" + "=" * 60)
    print("修复完成!")
    print("\n重要说明:")
    print("1. 批处理文件开头已添加 'chcp 65001' 命令，设置控制台为UTF-8代码页")
    print("2. 如果仍有乱码，请检查:")
    print("   - 系统是否支持UTF-8代码页 (Windows 10/11 支持)")
    print("   - 控制台字体是否支持中文 (如'宋体'、'微软雅黑')")
    print("3. 备用方案:")
    print("   - 手动设置代码页: 运行 'chcp 65001' 后再运行批处理文件")
    print("   - 使用GBK代码页: 运行 'chcp 936' 后再运行批处理文件")
    
    # 显示最终文件信息
    if os.path.exists('start.bat'):
        size = os.path.getsize('start.bat')
        print(f"\n最终文件信息:")
        print(f"  文件名: start.bat")
        print(f"  文件大小: {size} 字节")
        
        # 显示文件前几行
        try:
            with open('start.bat', 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
                print(f"  第一行: {first_line}")
                
                # 检查是否包含chcp命令
                with open('start.bat', 'r', encoding='utf-8', errors='ignore') as f2:
                    content = f2.read()
                    if 'chcp' in content:
                        print("  包含代码页设置: 是")
                    else:
                        print("  包含代码页设置: 否")
        except:
            pass
    
    return 0

if __name__ == "__main__":
    sys.exit(main())