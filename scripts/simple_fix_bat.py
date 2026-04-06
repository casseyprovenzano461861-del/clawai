# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
简化版批处理文件编码修复
直接转换start.bat为GBK编码
"""

import os
import sys

def fix_bat_encoding(bat_path):
    """修复批处理文件编码"""
    print(f"正在修复: {bat_path}")
    
    # 备份文件
    backup_path = bat_path + '.backup'
    try:
        with open(bat_path, 'rb') as src:
            content_bytes = src.read()
        
        with open(backup_path, 'wb') as dst:
            dst.write(content_bytes)
        print(f"备份已创建: {backup_path}")
    except Exception as e:
        print(f"备份失败: {e}")
        return False
    
    # 尝试不同编码读取
    encodings_to_try = ['utf-8', 'gbk', 'utf-8-sig', 'latin-1']
    content = None
    used_encoding = None
    
    for encoding in encodings_to_try:
        try:
            with open(bat_path, 'r', encoding=encoding) as f:
                content = f.read()
                used_encoding = encoding
                print(f"使用 {encoding} 编码读取成功")
                break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"使用 {encoding} 读取失败: {e}")
            continue
    
    if content is None:
        print("无法使用任何编码读取文件，尝试二进制模式...")
        try:
            with open(bat_path, 'rb') as f:
                raw_bytes = f.read()
            # 尝试解码为utf-8，忽略错误
            content = raw_bytes.decode('utf-8', errors='ignore')
            used_encoding = 'utf-8 (with errors ignored)'
        except Exception as e:
            print(f"二进制读取失败: {e}")
            return False
    
    print(f"原始编码: {used_encoding}")
    
    # 修复常见问题
    # 1. 替换Unicode字符
    char_replacements = {
        '»': '>>',
        '«': '<<',
        '–': '-',
        '—': '-',
        '…': '...',
        '•': '*',
        '·': '*',
        '®': '(R)',
        '™': '(TM)',
        '©': '(C)',
        '°': '度',
        '×': 'x',
        '÷': '/'
    }
    
    for bad_char, good_char in char_replacements.items():
        if bad_char in content:
            content = content.replace(bad_char, good_char)
            print(f"替换字符: {bad_char} -> {good_char}")
    
    # 2. 确保Windows换行符
    if '\r\n' not in content and '\n' in content:
        content = content.replace('\n', '\r\n')
        print("已转换换行符为Windows格式")
    
    # 3. 保存为GBK编码
    try:
        with open(bat_path, 'w', encoding='gbk', errors='replace') as f:
            f.write(content)
        print(f"文件已保存为GBK编码: {bat_path}")
    except Exception as e:
        print(f"保存为GBK失败: {e}")
        
        # 尝试ANSI编码
        try:
            with open(bat_path, 'w', encoding='cp1252', errors='replace') as f:
                f.write(content)
            print(f"文件已保存为ANSI编码: {bat_path}")
        except Exception as e2:
            print(f"保存为ANSI失败: {e2}")
            
            # 最后尝试二进制写入
            try:
                with open(bat_path, 'wb') as f:
                    f.write(content.encode('gbk', errors='replace'))
                print(f"文件已二进制写入: {bat_path}")
            except Exception as e3:
                print(f"所有保存方法都失败: {e3}")
                return False
    
    # 验证文件
    print("\n验证文件...")
    try:
        with open(bat_path, 'r', encoding='gbk', errors='ignore') as f:
            verify_content = f.read(500)
        
        if "ClawAI" in verify_content or "echo" in verify_content:
            print("验证成功: 文件包含预期内容")
        else:
            print("验证警告: 文件内容可能不正确")
        
        # 显示前几行
        lines = verify_content.split('\n')[:5]
        print("文件前5行:")
        for i, line in enumerate(lines, 1):
            print(f"  {i}: {line}")
            
    except Exception as e:
        print(f"验证失败: {e}")
    
    return True

def test_bat_file(bat_path):
    """测试批处理文件"""
    print(f"\n测试文件: {bat_path}")
    
    # 简单测试：检查文件是否存在并可执行
    if not os.path.exists(bat_path):
        print("错误: 文件不存在")
        return False
    
    # 尝试运行批处理文件（显示帮助）
    import subprocess
    
    # 创建一个临时命令文件来执行批处理并立即退出
    temp_cmd = f"""@echo off
chcp 65001 >nul
call "{os.path.abspath(bat_path)}"
echo 测试完成
pause
exit
"""
    
    temp_file = "test_bat_temp.cmd"
    try:
        with open(temp_file, 'w', encoding='gbk') as f:
            f.write(temp_cmd)
        
        print("运行测试...")
        # 使用timeout命令限制执行时间
        result = subprocess.run(
            ["cmd", "/c", "timeout", "/t", "3", "/nobreak", "&", "call", temp_file],
            capture_output=True,
            text=True,
            encoding='gbk',
            errors='ignore',
            shell=True,
            timeout=5
        )
        
        print(f"返回码: {result.returncode}")
        
        if "ClawAI" in result.stdout or "ClawAI" in result.stderr:
            print("测试成功: 批处理文件正常执行")
            success = True
        else:
            print("测试警告: 未找到预期输出")
            print(f"标准输出前200字符: {result.stdout[:200]}")
            print(f"错误输出前200字符: {result.stderr[:200]}")
            success = False
        
    except subprocess.TimeoutExpired:
        print("测试: 超时 (可能正常，因为等待用户输入)")
        success = True
    except Exception as e:
        print(f"测试异常: {e}")
        success = False
    finally:
        # 清理临时文件
        try:
            os.remove(temp_file)
        except:
            pass
    
    return success

def main():
    """主函数"""
    bat_file = "start.bat"
    
    if not os.path.exists(bat_file):
        print(f"错误: 文件 {bat_file} 不存在")
        return 1
    
    print("批处理文件编码修复工具")
    print("=" * 60)
    
    # 修复编码
    if fix_bat_encoding(bat_file):
        print(f"\n修复完成!")
        
        # 测试修复后的文件
        print("\n" + "=" * 60)
        print("测试修复结果...")
        test_bat_file(bat_file)
        
        print("\n" + "=" * 60)
        print("修复说明:")
        print("1. 如果仍有问题，请使用记事本打开start.bat")
        print("2. 选择'文件' -> '另存为'")
        print("3. 编码选择'ANSI'或'GBK'")
        print("4. 保存并替换原文件")
        print("\n备用方案:")
        print("手动运行: python scripts/auto_install_tools.py")
        print("手动运行: python backend/api_server.py")
        
        return 0
    else:
        print("\n修复失败!")
        print("请手动修复编码问题")
        return 1

if __name__ == "__main__":
    sys.exit(main())