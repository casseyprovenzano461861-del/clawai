# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
修复cleanup_archive_files.py中的表情符号编码问题
"""

import os
import re

def fix_emojis_in_file(filepath):
    """替换文件中的表情符号为文本标识"""
    emoji_replacements = {
        # 文件/文档符号
        "📁": "[目录]",
        "📊": "[统计]",
        "📈": "[图表]",
        "📦": "[大小]",
        "📄": "[报告]",
        "📭": "[空]",
        "📋": "[计划]",
        
        # 状态符号
        "✅": "[成功]",
        "❌": "[失败]",
        "⏹️": "[中断]",
        "🎯": "[目标]",
        "💡": "[建议]",
        "💾": "[存储]",
        "🗑️": "[删除]",
        
        # 其他符号
        "🔍": "[分析]",
        "🚀": "[执行]",
        "🔧": "[工具]",
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

def main():
    """主函数"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_file = os.path.join(script_dir, "cleanup_archive_files.py")
    
    print("正在修复cleanup_archive_files.py中的表情符号...")
    success, message = fix_emojis_in_file(target_file)
    
    if success:
        print(f"[成功] {message}")
        print("文件已修复，可以正常运行。")
    else:
        print(f"[信息] {message}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())