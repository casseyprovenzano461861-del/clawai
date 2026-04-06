# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
批量修复脚本中的表情符号编码问题
将表情符号替换为文本标识，确保在Windows GBK终端中能正常运行
"""

import os
import re
import sys

def replace_emojis_in_file(filepath):
    """替换文件中的表情符号"""
    emoji_replacements = {
        # 状态符号
        "[成功]": "[成功]",
        "[失败]": "[失败]", 
        "[警告]": "[警告]",
        "[中断]": "[中断]",
        
        # 文件/文档符号
        "[文件]": "[文件]",
        "[文档]": "[文档]",
        "[统计]": "[统计]",
        "[列表]": "[列表]",
        "[图表]": "[图表]",
        
        # 目标/进度符号
        "[目标]": "[目标]",
        "[慢速]": "[慢速]",
        "[建议]": "[建议]",
        
        # 表情符号
        "[搜索]": "[搜索]",
        "[庆祝]": "[庆祝]",
        "[良好]": "[良好]",
        "[警报]": "[警报]",
        
        # 颜色/状态符号
        "[高危]": "[高危]",
        "[中危]": "[中危]",
        "[低危]": "[低危]"
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 替换所有表情符号
        for emoji, replacement in emoji_replacements.items():
            content = content.replace(emoji, replacement)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, f"修复了 {sum(1 for e in emoji_replacements if e in original_content)} 个表情符号"
        else:
            return False, "无需修复"
            
    except Exception as e:
        return False, f"错误: {str(e)}"

def find_py_files_with_emojis(directory):
    """查找包含表情符号的Python文件"""
    files_with_emojis = []
    
    emoji_pattern = re.compile(r'[[成功][失败][警告][文件][文档][统计][目标][慢速][建议][高危][中危][低危][搜索][庆祝][良好][警报][中断][列表][图表]]')
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if emoji_pattern.search(content):
                            files_with_emojis.append(filepath)
                except Exception:
                    continue
    
    return files_with_emojis

def main():
    """主函数"""
    print("=" * 80)
    print("ClawAI 脚本表情符号修复工具")
    print("=" * 80)
    
    # 查找scripts目录下的所有Python文件
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"扫描目录: {scripts_dir}")
    files_with_emojis = find_py_files_with_emojis(scripts_dir)
    
    if not files_with_emojis:
        print("未找到包含表情符号的Python文件")
        return 0
    
    print(f"找到 {len(files_with_emojis)} 个包含表情符号的文件:")
    for filepath in files_with_emojis:
        print(f"  - {os.path.relpath(filepath, scripts_dir)}")
    
    print("\n开始修复...")
    print("-" * 40)
    
    fixed_count = 0
    for filepath in files_with_emojis:
        filename = os.path.basename(filepath)
        success, message = replace_emojis_in_file(filepath)
        
        if success:
            print(f"[成功] {filename}: {message}")
            fixed_count += 1
        else:
            print(f"[信息] {filename}: {message}")
    
    print("\n" + "=" * 80)
    print(f"修复完成!")
    print(f"总共处理: {len(files_with_emojis)} 个文件")
    print(f"成功修复: {fixed_count} 个文件")
    
    # 运行快速测试验证修复
    print("\n运行快速验证测试...")
    try:
        from scripts.simple_test_all import main as test_main
        print("导入simple_test_all.py成功，可以运行测试")
    except Exception as e:
        print(f"导入测试脚本时出错: {str(e)}")
    
    print("\n下一步建议:")
    print("1. 运行测试: python scripts/simple_test_all.py")
    print("2. 验证工具安装: python scripts/auto_install_tools.py")
    print("3. 验证监控系统: python scripts/enhanced_real_execution_monitor.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())