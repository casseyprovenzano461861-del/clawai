# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
ClawAI 交付物清单生成脚本
生成比赛交付物的完整清单和打包脚本
"""

import os
import sys
import json
from datetime import datetime

def print_header(text):
    print("\n" + "=" * 80)
    print(f" {text} ".center(80, "="))
    print("=" * 80)

def print_success(text):
    print(f"[SUCCESS] {text}")

def print_warning(text):
    print(f"[WARNING] {text}")

def print_error(text):
    print(f"[ERROR] {text}")

def analyze_project_structure():
    """分析项目结构"""
    print_header("分析项目结构")
    
    categories = {
        "演示脚本": [],
        "测试脚本": [],
        "工具检查": [],
        "清理工具": [],
        "文档材料": [],
        "配置文件": [],
        "其他重要文件": []
    }
    
    # 扫描根目录文件
    for item in os.listdir('.'):
        if os.path.isfile(item):
            if 'demo' in item.lower():
                categories["演示脚本"].append(item)
            elif 'test' in item.lower():
                categories["测试脚本"].append(item)
            elif 'tool' in item.lower() or 'check' in item.lower():
                categories["工具检查"].append(item)
            elif 'cleanup' in item.lower() or 'enhanced' in item.lower():
                categories["清理工具"].append(item)
            elif item.endswith('.md') or item.endswith('.txt'):
                categories["文档材料"].append(item)
            elif item.endswith('.py') or item.endswith('.bat'):
                categories["其他重要文件"].append(item)
            elif item.endswith('.env') or item.endswith('.yml') or item.endswith('.json'):
                categories["配置文件"].append(item)
    
    # 打印分类结果
    total_files = sum(len(files) for files in categories.values())
    
    print(f"项目根目录文件总数: {total_files}")
    print("\n文件分类:")
    
    for category, files in categories.items():
        if files:
            print(f"  {category} ({len(files)}个):")
            for file in sorted(files):
                file_size = os.path.getsize(file)
                print(f"    - {file} ({file_size:,} bytes)")
    
    return categories

def check_deliverables():
    """检查核心交付物"""
    print_header("检查核心交付物")
    
    deliverables = {
        "必须交付物": [],
        "建议交付物": [],
        "可选交付物": []
    }
    
    # 必须交付物
    mandatory_files = [
        "non_interactive_demo.py",  # 主演示脚本
        "competition_demo.py",       # 备用演示脚本
        "tests/test_ai_core_functionality.py",  # AI核心测试
        "README.md",                  # 项目说明
        "README_QUICKSTART.md",      # 快速开始
        "start.bat",                  # 启动脚本
        "config.py",                  # 配置文件
        "docker-compose.yml",        # Docker配置
        "Dockerfile",                # Docker镜像
        "presentation_outline.md",   # PPT大纲
        "emergency_plan.md",         # 应急预案
    ]
    
    # 建议交付物
    recommended_files = [
        "record_demo_video.py",      # 视频录制脚本
        "performance_test.py",       # 性能测试
        "final_task_verification.py",  # 任务验证
        "cleanup_duplicate_files.py",  # 清理工具
        "enhanced_project_cleanup.py",  # 增强清理
        "tool_check_results_final.json",  # 最终工具检查
        "tool_status_summary_final.txt",  # 工具状态摘要
        "comprehensive_project_analysis.md",  # 项目分析
    ]
    
    # 可选交付物
    optional_files = [
        "test_ai_core_simple.py",    # 简化测试
        "complete_tool_list.txt",    # 完整工具列表
        "uninstalled_tools_detailed.txt",  # 未安装工具
        "final_verification.py",     # 最终验证
        "create_simple_ppt.py",      # PPT创建脚本
        "PPT_README.md",             # PPT使用说明
    ]
    
    # 检查文件存在性
    def check_files(file_list, category):
        missing = []
        existing = []
        
        for file_path in file_list:
            if os.path.exists(file_path):
                existing.append(file_path)
            else:
                missing.append(file_path)
        
        deliverables[category].append({
            "existing": existing,
            "missing": missing,
            "total": len(file_list)
        })
        
        return existing, missing
    
    # 检查所有分类
    mandatory_existing, mandatory_missing = check_files(mandatory_files, "必须交付物")
    recommended_existing, recommended_missing = check_files(recommended_files, "建议交付物")
    optional_existing, optional_missing = check_files(optional_files, "可选交付物")
    
    # 打印检查结果
    print("必须交付物检查:")
    print(f"  存在: {len(mandatory_existing)}/{len(mandatory_files)}")
    for file in mandatory_existing:
        print(f"    [完成] {file}")

    if mandatory_missing:
        print(f"  缺失: {len(mandatory_missing)}/{len(mandatory_files)}")
        for file in mandatory_missing:
            print(f"    [缺失] {file}")
    
    print("\n建议交付物检查:")
    print(f"  存在: {len(recommended_existing)}/{len(recommended_files)}")
    
    print("\n可选交付物检查:")
    print(f"  存在: {len(optional_existing)}/{len(optional_files)}")
    
    return deliverables

def create_package_script():
    """创建打包脚本"""
    print_header("创建打包脚本")
    
    # Windows批处理打包脚本
    batch_script = """@echo off
echo ========================================
echo   ClawAI 比赛交付物打包脚本
echo ========================================
echo.

REM 设置变量
set PACKAGE_NAME=ClawAI_Competition_Deliverables_%DATE:~0,4%%DATE:~5,2%%DATE:~8,2%
set SOURCE_DIR=%~dp0
set PACKAGE_DIR=%SOURCE_DIR%%PACKAGE_NAME%

echo 创建打包目录: %PACKAGE_DIR%
if exist "%PACKAGE_DIR%" (
    echo 目录已存在，删除旧版本...
    rmdir /s /q "%PACKAGE_DIR%"
)
mkdir "%PACKAGE_DIR%"

echo.
echo 复制必须交付物...
mkdir "%PACKAGE_DIR%\\mandatory"

REM 复制必须文件
copy "non_interactive_demo.py" "%PACKAGE_DIR%\\mandatory\\"
copy "competition_demo.py" "%PACKAGE_DIR%\\mandatory\\"
copy "start.bat" "%PACKAGE_DIR%\\mandatory\\"
copy "config.py" "%PACKAGE_DIR%\\mandatory\\"
copy "docker-compose.yml" "%PACKAGE_DIR%\\mandatory\\"
copy "Dockerfile" "%PACKAGE_DIR%\\mandatory\\"
copy "presentation_outline.md" "%PACKAGE_DIR%\\mandatory\\"
copy "emergency_plan.md" "%PACKAGE_DIR%\\mandatory\\"
xcopy "tests" "%PACKAGE_DIR%\\mandatory\\tests\\" /E /I

echo.
echo 复制建议交付物...
mkdir "%PACKAGE_DIR%\\recommended"

copy "record_demo_video.py" "%PACKAGE_DIR%\\recommended\\"
copy "performance_test.py" "%PACKAGE_DIR%\\recommended\\"
copy "final_task_verification.py" "%PACKAGE_DIR%\\recommended\\"
copy "cleanup_duplicate_files.py" "%PACKAGE_DIR%\\recommended\\"
copy "enhanced_project_cleanup.py" "%PACKAGE_DIR%\\recommended\\"
copy "tool_check_results_final.json" "%PACKAGE_DIR%\\recommended\\"
copy "tool_status_summary_final.txt" "%PACKAGE_DIR%\\recommended\\"

echo.
echo 复制文档文件...
mkdir "%PACKAGE_DIR%\\documentation"

copy "README.md" "%PACKAGE_DIR%\\documentation\\"
copy "README_QUICKSTART.md" "%PACKAGE_DIR%\\documentation\\"
copy "comprehensive_project_analysis.md" "%PACKAGE_DIR%\\documentation\\"
copy "PPT_README.md" "%PACKAGE_DIR%\\documentation\\"

echo.
echo 创建项目结构备份...
xcopy "backend" "%PACKAGE_DIR%\\project_structure\\backend\\" /E /I
xcopy "configs" "%PACKAGE_DIR%\\project_structure\\configs\\" /E /I
xcopy "data" "%PACKAGE_DIR%\\project_structure\\data\\" /E /I
xcopy "docs" "%PACKAGE_DIR%\\project_structure\\docs\\" /E /I
xcopy "frontend" "%PACKAGE_DIR%\\project_structure\\frontend\\" /E /I
xcopy "scripts" "%PACKAGE_DIR%\\project_structure\\scripts\\" /E /I
xcopy "tools" "%PACKAGE_DIR%\\project_structure\\tools\\" /E /I
xcopy "utils" "%PACKAGE_DIR%\\project_structure\\utils\\" /E /I

echo.
echo 创建交付物清单...
echo ClawAI 比赛交付物清单 > "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo ============================== >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo. >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo 打包时间: %DATE% %TIME% >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo. >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo 必须交付物: >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo 1. non_interactive_demo.py - 非交互式演示脚本 >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo 2. competition_demo.py - 比赛演示脚本 >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo 3. tests/test_ai_core_functionality.py - AI核心测试 >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo 4. start.bat - 启动脚本 >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo 5. config.py - 配置文件 >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo 6. docker-compose.yml - Docker编排文件 >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo 7. Dockerfile - Docker镜像构建文件 >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo 8. presentation_outline.md - PPT演示大纲 >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo 9. emergency_plan.md - 比赛应急预案 >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo. >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo 建议交付物: >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo 1. record_demo_video.py - 视频录制脚本 >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo 2. performance_test.py - 性能测试脚本 >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo 3. cleanup_duplicate_files.py - 文件清理工具 >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo. >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo 使用说明: >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo 1. 启动演示: 运行 start.bat >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo 2. 运行演示: python non_interactive_demo.py --scenes 1,2,3 >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo 3. 性能测试: python performance_test.py >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"
echo 4. Docker部署: docker-compose up >> "%PACKAGE_DIR%\\DELIVERABLES_README.txt"

echo.
echo 创建压缩包...
cd "%PACKAGE_DIR%\\.."
tar -czf "%PACKAGE_NAME%.tar.gz" "%PACKAGE_NAME%"

echo.
echo ========================================
echo 打包完成！
echo 压缩包: %PACKAGE_NAME%.tar.gz
echo 原始目录: %PACKAGE_DIR%
echo ========================================
echo.
echo 按任意键退出...
pause > nul
"""
    
    # 保存批处理脚本
    batch_file = "package_deliverables.bat"
    with open(batch_file, 'w', encoding='gbk') as f:
        f.write(batch_script)
    
    print_success(f"批处理打包脚本已创建: {batch_file}")
    
    # 创建Python打包脚本（跨平台）
    python_script = """#!/usr/bin/env python3
"""
    
    # 简化版Python打包脚本
    python_script = """#!/usr/bin/env python3
"""
    
    python_file = "package_deliverables.py"
    with open(python_file, 'w', encoding='utf-8') as f:
        f.write("#!/usr/bin/env python3\n")
        f.write('"""\n')
        f.write("ClawAI 交付物打包脚本（Python版本）\n")
        f.write('"""\n\n')
        f.write("import os\n")
        f.write("import shutil\n")
        f.write("from datetime import datetime\n\n")
        f.write("def main():\n")
        f.write('    """主函数"""\n')
        f.write('    print("=" * 60)\n')
        f.write('    print("ClawAI 比赛交付物打包")\n')
        f.write('    print("=" * 60)\n\n')
        f.write('    # 创建打包目录\n')
        f.write('    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")\n')
        f.write('    package_name = f"ClawAI_Deliverables_{timestamp}"\n')
        f.write('    package_dir = os.path.join(".", package_name)\n\n')
        f.write('    print(f"创建打包目录: {package_dir}")\n\n')
        f.write('    # 检查并创建目录\n')
        f.write('    if os.path.exists(package_dir):\n')
        f.write('        shutil.rmtree(package_dir)\n')
        f.write('    os.makedirs(package_dir)\n\n')
        f.write('    # 必须交付物列表\n')
        f.write('    mandatory_files = [\n')
        f.write('        "non_interactive_demo.py",\n')
        f.write('        "competition_demo.py",\n')
        f.write('        "start.bat",\n')
        f.write('        "config.py",\n')
        f.write('        "docker-compose.yml",\n')
        f.write('        "Dockerfile",\n')
        f.write('        "presentation_outline.md",\n')
        f.write('        "emergency_plan.md",\n')
        f.write('        "tests/test_ai_core_functionality.py",\n')
        f.write('        "README.md",\n')
        f.write('        "README_QUICKSTART.md"\n')
        f.write('    ]\n\n')
        f.write('    # 复制文件\n')
        f.write('    print("复制必须交付物...")\n')
        f.write('    for file_path in mandatory_files:\n')
        f.write('        if os.path.exists(file_path):\n')
        f.write('            dest_dir = os.path.join(package_dir, os.path.dirname(file_path))\n')
        f.write('            if dest_dir and not os.path.exists(dest_dir):\n')
        f.write('                os.makedirs(dest_dir)\n')
        f.write('            shutil.copy2(file_path, os.path.join(package_dir, file_path))\n')
        f.write('            print(f"  [完成] {file_path}")\n')
        f.write('        else:\n')
        f.write('            print(f"  [缺失] {file_path} (缺失)")\n\n')
        f.write('    # 创建交付物清单\n')
        f.write('    readme_path = os.path.join(package_dir, "DELIVERABLES_README.txt")\n')
        f.write('    with open(readme_path, "w", encoding="utf-8") as f:\n')
        f.write('        f.write("ClawAI 比赛交付物清单\\n")\n')
        f.write('        f.write("=" * 40 + "\\n\\n")\n')
        f.write('        f.write(f"打包时间: {datetime.now().strftime(\'%Y-%m-%d %H:%M:%S\')}\\n\\n")\n')
        f.write('        f.write("核心交付物:\\n")\n')
        f.write('        f.write("1. non_interactive_demo.py - 非交互式演示脚本\\n")\n')
        f.write('        f.write("2. competition_demo.py - 比赛演示脚本\\n")\n')
        f.write('        f.write("3. 测试文件 - AI核心功能测试\\n")\n')
        f.write('        f.write("4. 配置文件和部署脚本\\n")\n')
        f.write('        f.write("5. 演示材料和应急预案\\n\\n")\n')
        f.write('        f.write("使用说明:\\n")\n')
        f.write('        f.write("1. 启动演示: 运行 start.bat\\n")\n')
        f.write('        f.write("2. 运行AI测试: python tests/test_ai_core_functionality.py\\n")\n')
        f.write('        f.write("3. Docker部署: docker-compose up\\n")\n\n')
        f.write('    print(f"\\n打包完成!")\n')
        f.write('    print(f"打包目录: {package_dir}")\n')
        f.write('    print("包含文件列表:")\n')
        f.write('    for root, dirs, files in os.walk(package_dir):\n')
        f.write('        for file in files:\n')
        f.write('            file_path = os.path.join(root, file)\n')
        f.write('            rel_path = os.path.relpath(file_path, package_dir)\n')
        f.write('            print(f"  - {rel_path}")\n\n')
        f.write('    return True\n\n')
        f.write('if __name__ == "__main__":\n')
        f.write('    try:\n')
        f.write('        success = main()\n')
        f.write('        exit(0 if success else 1)\n')
        f.write('    except KeyboardInterrupt:\n')
        f.write('        print("\\n打包被用户中断")\n')
        f.write('        exit(1)\n')
        f.write('    except Exception as e:\n')
        f.write('        print(f"\\n打包过程中发生错误: {e}")\n')
        f.write('        import traceback\n')
        f.write('        traceback.print_exc()\n')
        f.write('        exit(1)\n')
    
    print_success(f"Python打包脚本已创建: {python_file}")
    
    return batch_file, python_file

def create_deliverables_report():
    """创建交付物报告"""
    print_header("创建交付物报告")
    
    # 分析项目结构
    categories = analyze_project_structure()
    
    # 检查交付物
    deliverables = check_deliverables()
    
    # 创建打包脚本
    batch_file, python_file = create_package_script()
    
    # 生成报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"deliverables_report_{timestamp}.json"
    
    report_data = {
        "report_date": datetime.now().isoformat(),
        "project_analysis": {
            "total_categories": len(categories),
            "category_details": {cat: len(files) for cat, files in categories.items() if files}
        },
        "deliverables_status": {
            "mandatory": {
                "total": deliverables["必须交付物"][0]["total"],
                "existing": len(deliverables["必须交付物"][0]["existing"]),
                "missing": len(deliverables["必须交付物"][0]["missing"]),
                "missing_files": deliverables["必须交付物"][0]["missing"]
            },
            "recommended": {
                "total": deliverables["建议交付物"][0]["total"],
                "existing": len(deliverables["建议交付物"][0]["existing"]),
                "missing": len(deliverables["建议交付物"][0]["missing"])
            },
            "optional": {
                "total": deliverables["可选交付物"][0]["total"],
                "existing": len(deliverables["可选交付物"][0]["existing"]),
                "missing": len(deliverables["可选交付物"][0]["missing"])
            }
        },
        "package_scripts": {
            "batch": batch_file,
            "python": python_file
        },
        "recommendations": []
    }
    
    # 添加建议
    if deliverables["必须交付物"][0]["missing"]:
        report_data["recommendations"].append("缺少必须交付物，请补充缺失文件")
    
    if len(deliverables["必须交付物"][0]["existing"]) / deliverables["必须交付物"][0]["total"] < 0.8:
        report_data["recommendations"].append("必须交付物完整度低于80%，建议补充")
    
    # 保存报告
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print_success(f"交付物报告已创建: {report_file}")
    
    # 打印摘要
    print_header("交付物准备摘要")
    print(f"项目分析完成，共 {sum(len(files) for files in categories.values())} 个文件")
    print(f"必须交付物: {len(deliverables['必须交付物'][0]['existing'])}/{deliverables['必须交付物'][0]['total']} 完成")
    print(f"打包脚本: {batch_file} (Windows), {python_file} (跨平台)")
    print(f"详细报告: {report_file}")
    
    return report_data

def main():
    """主函数"""
    print_header("ClawAI 交付物清单生成工具")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        report = create_deliverables_report()
        
        print_header("使用说明")
        print("1. 运行打包脚本:")
        print("   Windows: 双击 package_deliverables.bat")
        print("   跨平台: python package_deliverables.py")
        print("\n2. 检查交付物:")
        print("   运行: python deliverables_checklist.py")
        print("\n3. 演示准备:")
        print("   主演示: python non_interactive_demo.py --scenes 1,2,3")
        print("   性能测试: python performance_test.py")
        print("   应急预案: 参考 emergency_plan.md")
        
        print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print_error(f"生成交付物清单时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)