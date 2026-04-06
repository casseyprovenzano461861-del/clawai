# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
修复批处理文件的CRLF问题
"""

import os
import sys

def fix_crlf(file_path):
    """修复CRLF换行符"""
    print(f"修复文件: {file_path}")
    
    # 读取文件
    with open(file_path, 'rb') as f:
        content = f.read()
    
    # 统计原始换行符
    cr_count = content.count(b'\r')
    lf_count = content.count(b'\n')
    crlf_count = content.count(b'\r\n')
    crrlf_count = content.count(b'\r\r\n')
    
    print(f"原始统计:")
    print(f"  \\r 出现次数: {cr_count}")
    print(f"  \\n 出现次数: {lf_count}")
    print(f"  \\r\\n 出现次数: {crlf_count}")
    print(f"  \\r\\r\\n 出现次数: {crrlf_count}")
    
    # 修复双重CR问题
    if crrlf_count > 0:
        print(f"发现 {crrlf_count} 个 \\r\\r\\n，正在修复...")
        # 将 \r\r\n 替换为 \r\n
        content = content.replace(b'\r\r\n', b'\r\n')
    
    # 确保所有换行符都是 \r\n
    # 首先将单独的 \n 替换为 \r\n
    if b'\n' in content and b'\r\n' not in content:
        print("发现只有 \\n，没有 \\r\\n，正在修复...")
        content = content.replace(b'\n', b'\r\n')
    elif content.count(b'\n') > content.count(b'\r\n') * 2:
        print("混合换行符，正在标准化为 \\r\\n...")
        # 复杂的替换：先处理 \r\n，再处理剩下的 \n
        content = content.replace(b'\r\n', b'\n')  # 临时转换
        content = content.replace(b'\n', b'\r\n')  # 全部标准化
    
    # 再次统计
    cr_count = content.count(b'\r')
    lf_count = content.count(b'\n')
    crlf_count = content.count(b'\r\n')
    crrlf_count = content.count(b'\r\r\n')
    
    print(f"修复后统计:")
    print(f"  \\r 出现次数: {cr_count}")
    print(f"  \\n 出现次数: {lf_count}")
    print(f"  \\r\\n 出现次数: {crlf_count}")
    print(f"  \\r\\r\\n 出现次数: {crrlf_count}")
    
    # 写入文件
    backup_path = file_path + '.before_crlf_fix'
    with open(backup_path, 'wb') as f:
        f.write(content)
    
    print(f"修复版本已保存到: {backup_path}")
    
    # 复制回原文件
    with open(file_path, 'wb') as f:
        f.write(content)
    
    print(f"原文件已更新: {file_path}")
    
    return True

def main():
    """主函数"""
    files_to_fix = [
        "start.bat",
        "start_new.bat" if os.path.exists("start_new.bat") else None
    ]
    
    files_to_fix = [f for f in files_to_fix if f]
    
    if not files_to_fix:
        print("没有文件需要修复")
        return 1
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            print("\n" + "="*60)
            fix_crlf(file_path)
        else:
            print(f"文件不存在: {file_path}")
    
    print("\n" + "="*60)
    print("修复完成!")
    print("现在可以测试批处理文件:")
    print("  双击 start.bat 或运行 start.bat")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())