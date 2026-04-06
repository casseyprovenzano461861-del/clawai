# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
修复批处理文件编码问题
Windows批处理文件需要使用GBK/ANSI编码，而不是UTF-8
"""

import os
import sys
import codecs
import chardet

def detect_encoding(file_path):
    """检测文件编码"""
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result['encoding'], result['confidence']

def convert_to_gbk(file_path, backup=True):
    """将文件转换为GBK编码"""
    if backup:
        backup_path = file_path + '.utf8_backup'
        with open(file_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        print(f"备份文件已创建: {backup_path}")
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # 修复可能的编码问题
    # 1. 替换可能导致问题的字符
    content = content.replace('»', '>>')
    content = content.replace('«', '<<')
    
    # 2. 确保换行符是Windows格式
    if '\r\n' not in content and '\n' in content:
        content = content.replace('\n', '\r\n')
    
    # 保存为GBK编码
    with open(file_path, 'w', encoding='gbk', errors='replace') as f:
        f.write(content)
    
    print(f"文件已转换为GBK编码: {file_path}")
    
    # 验证转换
    encoding, confidence = detect_encoding(file_path)
    print(f"转换后编码检测: {encoding} (置信度: {confidence:.2f})")
    
    return True

def create_safe_bat_file(bat_path):
    """创建安全的批处理文件版本"""
    safe_content = '''@echo off
chcp 65001 >nul 2>&1
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
    
    # 保存为GBK编码
    with open(bat_path, 'w', encoding='gbk') as f:
        f.write(safe_content)
    
    print(f"安全的批处理文件已创建: {bat_path}")
    return True

def main():
    """主函数"""
    bat_files = [
        "start.bat",
        "scripts/start_api.bat" if os.path.exists("scripts/start_api.bat") else None
    ]
    
    bat_files = [f for f in bat_files if f and os.path.exists(f)]
    
    if not bat_files:
        print("未找到批处理文件")
        return 1
    
    print("批处理文件编码修复工具")
    print("=" * 60)
    
    for bat_file in bat_files:
        print(f"\n处理文件: {bat_file}")
        
        # 检测当前编码
        encoding, confidence = detect_encoding(bat_file)
        print(f"  当前编码: {encoding} (置信度: {confidence:.2f})")
        
        if encoding and encoding.lower() in ['utf-8', 'utf-8-sig']:
            print("  检测到UTF-8编码，需要转换为GBK...")
            try:
                convert_to_gbk(bat_file, backup=True)
                print("  转换成功!")
            except Exception as e:
                print(f"  转换失败: {e}")
                print("  尝试创建安全的替代版本...")
                backup_name = bat_file + '.original'
                os.rename(bat_file, backup_name)
                create_safe_bat_file(bat_file)
        elif encoding and encoding.lower() in ['gb2312', 'gbk', 'gb18030']:
            print("  已经是GBK编码，无需转换")
        else:
            print(f"  未知编码 ({encoding})，尝试创建安全版本...")
            backup_name = bat_file + '.original'
            if os.path.exists(backup_name):
                os.remove(backup_name)
            os.rename(bat_file, backup_name)
            create_safe_bat_file(bat_file)
    
    # 验证修复
    print("\n" + "=" * 60)
    print("验证修复结果...")
    
    for bat_file in bat_files:
        print(f"\n验证文件: {bat_file}")
        
        # 尝试运行批处理文件（只显示菜单）
        try:
            import subprocess
            result = subprocess.run(
                [bat_file, "&&", "exit"],
                capture_output=True,
                text=True,
                encoding='gbk',
                errors='ignore',
                shell=True,
                timeout=5
            )
            
            if result.returncode == 0 or result.returncode == 1:
                print("  运行测试: 成功")
                # 检查输出中是否包含预期的内容
                if "ClawAI" in result.stdout or "ClawAI" in result.stderr:
                    print("  内容验证: 成功")
                else:
                    print("  内容验证: 警告 - 未找到预期内容")
            else:
                print(f"  运行测试: 失败 (返回码: {result.returncode})")
                print(f"  错误输出: {result.stderr[:200]}")
                
        except subprocess.TimeoutExpired:
            print("  运行测试: 超时 (可能正常，因为等待用户输入)")
        except Exception as e:
            print(f"  运行测试: 异常 - {e}")
    
    print("\n修复完成!")
    print("=" * 60)
    print("重要说明:")
    print("1. 如果start.bat仍有问题，请手动编辑并使用GBK编码保存")
    print("2. 可以使用记事本打开文件，选择'文件' -> '另存为' -> 编码选择'ANSI'或'GBK'")
    print("3. 建议使用Notepad++等支持编码转换的编辑器")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())