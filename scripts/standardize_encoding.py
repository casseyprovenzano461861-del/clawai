# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
统一项目文件编码标准脚本
将所有批处理文件和Python脚本转换为UTF-8 without BOM编码
"""

import os
import sys
import codecs
from pathlib import Path

def convert_to_utf8_without_bom(file_path):
    """将文件转换为UTF-8 without BOM编码"""
    try:
        # 检测当前编码
        with open(file_path, 'rb') as f:
            raw = f.read()
        
        # 检查BOM
        if raw.startswith(b'\xef\xbb\xbf'):
            # UTF-8 with BOM，移除BOM
            content = raw[3:].decode('utf-8')
            encoding = 'utf-8-sig'
        elif raw.startswith(b'\xff\xfe'):
            # UTF-16 LE
            content = raw[2:].decode('utf-16-le')
            encoding = 'utf-16-le'
        elif raw.startswith(b'\xfe\xff'):
            # UTF-16 BE
            content = raw[2:].decode('utf-16-be')
            encoding = 'utf-16-be'
        else:
            # 尝试UTF-8解码
            try:
                content = raw.decode('utf-8')
                encoding = 'utf-8'
            except UnicodeDecodeError:
                # 尝试GBK解码（中文Windows默认）
                try:
                    content = raw.decode('gbk')
                    encoding = 'gbk'
                except UnicodeDecodeError:
                    # 无法识别的编码，跳过
                    print(f"  [WARNING] 无法识别编码，跳过: {file_path}")
                    return False
        
        # 转换为UTF-8 without BOM
        if encoding != 'utf-8':
            with open(file_path, 'w', encoding='utf-8', newline='\r\n') as f:
                f.write(content)
            print(f"  [OK] 转换成功: {encoding} -> UTF-8 (无BOM)")
            return True
        else:
            # 已经是UTF-8，检查是否有BOM
            if raw.startswith(b'\xef\xbb\xbf'):
                with open(file_path, 'w', encoding='utf-8', newline='\r\n') as f:
                    f.write(content)
                print(f"  [OK] 移除BOM: UTF-8 with BOM -> UTF-8 (无BOM)")
                return True
            else:
                print(f"  [SKIP] 已经是UTF-8 (无BOM)，无需转换")
                return True
                
    except Exception as e:
        print(f"  [ERROR] 转换失败: {e}")
        return False

def process_batch_files(project_root):
    """处理所有批处理文件"""
    print("处理批处理文件...")
    batch_extensions = ['.bat', '.cmd']
    
    for ext in batch_extensions:
        for file_path in Path(project_root).rglob(f'*{ext}'):
            if file_path.is_file():
                print(f"\n处理: {file_path.relative_to(project_root)}")
                convert_to_utf8_without_bom(file_path)
    
    # 特殊处理package_deliverables.bat中的start.bat引用
    package_bat = Path(project_root) / 'package_deliverables.bat'
    if package_bat.exists():
        print(f"\n检查打包脚本中的引用...")
        with open(package_bat, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 确保引用的文件存在且编码正确
        references = ['start.bat', 'competition_demo.py', 'config.py', 'docker-compose.yml', 
                     'Dockerfile', 'presentation_outline.md', 'emergency_plan.md']
        for ref in references:
            ref_path = Path(project_root) / ref
            if ref_path.exists():
                print(f"  [OK] 引用文件存在: {ref}")
            else:
                print(f"  [WARN] 引用文件不存在: {ref}")

def process_python_files(project_root):
    """处理Python文件，确保使用UTF-8"""
    print("\n\n处理Python文件...")
    python_files = list(Path(project_root).rglob('*.py'))
    
    for i, file_path in enumerate(python_files, 1):
        if file_path.is_file():
            print(f"\n[{i}/{len(python_files)}] 处理: {file_path.relative_to(project_root)}")
            convert_to_utf8_without_bom(file_path)

def add_encoding_declaration():
    """为Python文件添加编码声明"""
    print("\n\n检查Python文件编码声明...")
    
    for file_path in Path('.').rglob('*.py'):
        if file_path.is_file():
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 检查前两行是否有编码声明
            has_encoding = False
            for line in lines[:2]:
                if 'coding:' in line or 'encoding:' in line:
                    has_encoding = True
                    break
            
            if not has_encoding:
                # 添加编码声明
                with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write('# -*- coding: utf-8 -*-\n')
                    f.writelines(lines)
                print(f"  [OK] 添加编码声明: {file_path}")

def create_unified_bat_template():
    """创建统一的批处理文件模板"""
    print("\n\n创建统一的批处理文件模板...")
    
    template_content = """@echo off
chcp 65001 >nul 2>nul
cd /d "%~dp0"

REM ============================================
REM   统一的批处理文件模板 - UTF-8 编码
REM   使用 chcp 65001 确保中文正常显示
REM ============================================

echo.
echo 执行完成！
pause
"""
    
    template_path = Path('scripts') / 'bat_template.txt'
    template_path.parent.mkdir(exist_ok=True)
    
    with open(template_path, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(template_content)
    
    print(f"  [OK] 创建模板: {template_path}")

def main():
    project_root = Path(__file__).parent.parent
    
    # 设置控制台编码为UTF-8
    try:
        import sys
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass
    
    print("=" * 60)
    print("统一项目编码标准")
    print("=" * 60)
    print(f"项目根目录: {project_root}")
    print()
    
    # 处理批处理文件
    process_batch_files(project_root)
    
    # 处理Python文件
    process_python_files(project_root)
    
    # 添加编码声明
    add_encoding_declaration()
    
    # 创建模板
    create_unified_bat_template()
    
    print("\n" + "=" * 60)
    print("编码标准化完成！")
    print("=" * 60)
    print("\n建议:")
    print("1. 所有批处理文件现在使用UTF-8 without BOM编码")
    print("2. 使用 chcp 65001 确保中文正常显示")
    print("3. Python文件添加了UTF-8编码声明")
    print("4. 创建了统一的批处理文件模板")
    print("\n后续操作:")
    print("1. 运行 test_encoding.py 验证编码转换结果")
    print("2. 运行 start_utf8_final_solution.bat 测试中文显示")
    print("3. 运行 start_english_final.bat 测试英文显示")

if __name__ == '__main__':
    main()