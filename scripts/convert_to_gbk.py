# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
将批处理文件转换为GBK编码
"""

import os
import sys

def convert_file_to_gbk(file_path):
    """将文件转换为GBK编码"""
    print(f"转换文件: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在")
        return False
    
    # 备份原文件
    backup_path = file_path + '.backup'
    try:
        with open(file_path, 'rb') as f:
            original_content = f.read()
        with open(backup_path, 'wb') as f:
            f.write(original_content)
        print(f"备份已创建: {backup_path}")
    except Exception as e:
        print(f"备份失败: {e}")
        return False
    
    # 尝试以UTF-8读取
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print("以UTF-8编码读取成功")
    except UnicodeDecodeError:
        # 尝试以GBK读取
        try:
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()
            print("以GBK编码读取成功")
        except Exception as e:
            print(f"读取失败: {e}")
            # 尝试以latin-1读取（不会失败）
            with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
                content = f.read()
            print("以latin-1编码读取成功（可能丢失中文字符）")
    except Exception as e:
        print(f"读取失败: {e}")
        return False
    
    # 以GBK编码写入
    try:
        with open(file_path, 'w', encoding='gbk', errors='replace') as f:
            f.write(content)
        print("以GBK编码写入成功")
        return True
    except Exception as e:
        print(f"写入失败: {e}")
        return False

def main():
    """主函数"""
    files_to_convert = [
        'test_simple.bat',
        'start.bat'
    ]
    
    print("批处理文件编码转换工具")
    print("=" * 60)
    
    for file_path in files_to_convert:
        if os.path.exists(file_path):
            print(f"\n处理文件: {file_path}")
            if convert_file_to_gbk(file_path):
                print(f"  转换成功")
            else:
                print(f"  转换失败")
        else:
            print(f"\n文件不存在: {file_path}")
    
    print("\n" + "=" * 60)
    print("转换完成!")
    print("现在可以测试批处理文件:")
    for file_path in files_to_convert:
        if os.path.exists(file_path):
            print(f"  {file_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())