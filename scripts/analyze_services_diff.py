#!/usr/bin/env python3
"""
分析services/和src/目录的差异
识别代码冗余和功能差异
"""

import os
import sys
from pathlib import Path
import hashlib
from typing import Dict, List, Tuple, Set
import json

def get_file_hash(filepath: Path) -> str:
    """计算文件的MD5哈希值"""
    if not filepath.exists():
        return ""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def analyze_directory_structure(services_dir: Path, src_dir: Path) -> Dict:
    """分析两个目录的结构差异"""
    results = {
        "services_only": [],
        "src_only": [],
        "common_files": [],
        "different_files": [],
        "same_files": [],
    }

    # 收集services目录下的文件
    services_files = {}
    for root, dirs, files in os.walk(services_dir):
        for file in files:
            if file.endswith('.py'):
                rel_path = Path(root).relative_to(services_dir) / file
                services_files[str(rel_path)] = Path(root) / file

    # 收集src目录下的文件
    src_files = {}
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                rel_path = Path(root).relative_to(src_dir) / file
                src_files[str(rel_path)] = Path(root) / file

    # 分析差异
    all_files = set(services_files.keys()) | set(src_files.keys())

    for file_rel in sorted(all_files):
        services_path = services_files.get(file_rel)
        src_path = src_files.get(file_rel)

        if services_path and not src_path:
            results["services_only"].append(str(file_rel))
        elif src_path and not services_path:
            results["src_only"].append(str(file_rel))
        else:
            # 两个目录都有这个文件
            services_hash = get_file_hash(services_path)
            src_hash = get_file_hash(src_path)

            if services_hash == src_hash:
                results["same_files"].append(str(file_rel))
            else:
                results["different_files"].append(str(file_rel))
                results["common_files"].append(str(file_rel))

    return results

def analyze_microservices(services_dir: Path) -> Dict:
    """分析微服务结构和功能"""
    microservices = {}

    for service_dir in services_dir.iterdir():
        if service_dir.is_dir():
            service_name = service_dir.name
            main_py = service_dir / "main.py"
            requirements_txt = service_dir / "requirements.txt"

            microservices[service_name] = {
                "path": str(service_dir),
                "has_main": main_py.exists(),
                "has_requirements": requirements_txt.exists(),
                "files": [],
            }

            # 收集Python文件
            for root, dirs, files in os.walk(service_dir):
                for file in files:
                    if file.endswith('.py'):
                        rel_path = Path(root).relative_to(service_dir) / file
                        microservices[service_name]["files"].append(str(rel_path))

    return microservices

def analyze_src_modules(src_dir: Path) -> Dict:
    """分析src目录下的模块结构"""
    modules = {}

    # 查找可能的模块目录
    for item in src_dir.iterdir():
        if item.is_dir() and not item.name.startswith('_'):
            modules[item.name] = {
                "path": str(item),
                "files": [],
            }

            # 收集Python文件
            for root, dirs, files in os.walk(item):
                for file in files:
                    if file.endswith('.py'):
                        rel_path = Path(root).relative_to(item) / file
                        modules[item.name]["files"].append(str(rel_path))

    return modules

def compare_main_files(services_dir: Path, src_dir: Path) -> List[Dict]:
    """比较main.py文件的关键差异"""
    comparisons = []

    # 微服务main.py文件
    service_main_files = []
    for service_dir in services_dir.iterdir():
        if service_dir.is_dir():
            main_py = service_dir / "main.py"
            if main_py.exists():
                service_main_files.append((service_dir.name, main_py))

    # src目录下的main.py文件
    src_main_files = []
    for item in src_dir.iterdir():
        if item.is_dir():
            main_py = item / "main.py"
            if main_py.exists():
                src_main_files.append((item.name, main_py))

    # 比较每个微服务和对应的src模块
    for service_name, service_main in service_main_files:
        # 查找对应的src模块（可能名称不同）
        src_module_name = None
        src_main = None

        # 尝试匹配名称
        for src_name, src_path in src_main_files:
            if service_name.replace('-', '_') == src_name:
                src_module_name = src_name
                src_main = src_path
                break

        if src_main:
            # 比较文件大小
            service_size = service_main.stat().st_size
            src_size = src_main.stat().st_size

            # 读取文件内容（前几行）
            with open(service_main, 'r', encoding='utf-8') as f:
                service_content = f.read(500)

            with open(src_main, 'r', encoding='utf-8') as f:
                src_content = f.read(500)

            comparisons.append({
                "service": service_name,
                "src_module": src_module_name,
                "service_size": service_size,
                "src_size": src_size,
                "size_diff": src_size - service_size,
                "is_similar": service_content[:100] == src_content[:100],
            })

    return comparisons

def main():
    """主分析函数"""
    project_root = Path(__file__).parent.parent
    services_dir = project_root / "services"
    src_dir = project_root / "src"

    print("=" * 80)
    print("ClawAI 微服务 vs 单体代码差异分析")
    print("=" * 80)

    if not services_dir.exists():
        print(f"错误: services目录不存在: {services_dir}")
        return

    if not src_dir.exists():
        print(f"错误: src目录不存在: {src_dir}")
        return

    print(f"\n1. 目录结构分析:")
    print(f"   services目录: {services_dir}")
    print(f"   src目录: {src_dir}")

    # 分析目录结构差异
    print("\n2. 文件差异分析:")
    structure_results = analyze_directory_structure(services_dir, src_dir)

    print(f"   services独有的文件: {len(structure_results['services_only'])}")
    if structure_results['services_only']:
        print("     示例:")
        for file in structure_results['services_only'][:5]:
            print(f"       - {file}")
        if len(structure_results['services_only']) > 5:
            print(f"       ... 还有 {len(structure_results['services_only']) - 5} 个文件")

    print(f"\n   src独有的文件: {len(structure_results['src_only'])}")
    if structure_results['src_only']:
        print("     示例:")
        for file in structure_results['src_only'][:5]:
            print(f"       - {file}")
        if len(structure_results['src_only']) > 5:
            print(f"       ... 还有 {len(structure_results['src_only']) - 5} 个文件")

    print(f"\n   相同的文件: {len(structure_results['same_files'])}")
    print(f"   不同的文件: {len(structure_results['different_files'])}")
    if structure_results['different_files']:
        print("     不同文件列表:")
        for file in structure_results['different_files'][:10]:
            print(f"       - {file}")
        if len(structure_results['different_files']) > 10:
            print(f"       ... 还有 {len(structure_results['different_files']) - 10} 个文件")

    # 分析微服务结构
    print("\n3. 微服务结构分析:")
    microservices = analyze_microservices(services_dir)
    print(f"   找到 {len(microservices)} 个微服务:")
    for service_name, info in microservices.items():
        print(f"   - {service_name}: {len(info['files'])} 个Python文件")
        if info['has_main']:
            print(f"     包含main.py")
        if info['has_requirements']:
            print(f"     包含requirements.txt")

    # 分析src模块结构
    print("\n4. src模块结构分析:")
    modules = analyze_src_modules(src_dir)
    print(f"   找到 {len(modules)} 个模块:")
    for module_name, info in modules.items():
        print(f"   - {module_name}: {len(info['files'])} 个Python文件")

    # 比较main.py文件
    print("\n5. main.py文件比较:")
    main_comparisons = compare_main_files(services_dir, src_dir)
    if main_comparisons:
        print("   微服务 vs 对应src模块的main.py比较:")
        for comp in main_comparisons:
            status = "相似" if comp['is_similar'] else "不同"
            print(f"   - {comp['service']} → {comp['src_module']}: {status}")
            print(f"     大小: {comp['service_size']}B vs {comp['src_size']}B (差异: {comp['size_diff']}B)")
    else:
        print("   未找到对应的main.py文件进行比较")

    # 总结和建议
    print("\n" + "=" * 80)
    print("分析总结和建议:")
    print("=" * 80)

    total_services_files = sum(len(info['files']) for info in microservices.values())
    total_src_files = sum(len(info['files']) for info in modules.values())

    print(f"1. 代码规模:")
    print(f"   - 微服务: {total_services_files} 个Python文件")
    print(f"   - src模块: {total_src_files} 个Python文件")
    print(f"   - 重复文件: {len(structure_results['common_files'])} 个")

    print(f"\n2. 主要差异:")
    print(f"   - {len(structure_results['different_files'])} 个文件内容不同")
    print(f"   - {len(structure_results['services_only'])} 个文件只在services目录")
    print(f"   - {len(structure_results['src_only'])} 个文件只在src目录")

    print(f"\n3. 迁移建议:")
    print(f"   a. 优先迁移services独有的文件")
    print(f"   b. 比较并合并不同的文件")
    print(f"   c. 保留src独有的文件（可能是新增功能）")
    print(f"   d. 相同的文件可以直接复用")

    print(f"\n4. 风险提示:")
    print(f"   - 不同文件可能导致功能不一致")
    print(f"   - 需要手动检查并合并代码逻辑")
    print(f"   - 注意API兼容性")

    # 保存分析结果到文件
    output_file = project_root / "migration_analysis.json"
    output_data = {
        "structure_results": structure_results,
        "microservices": microservices,
        "modules": modules,
        "main_comparisons": main_comparisons,
        "summary": {
            "total_services_files": total_services_files,
            "total_src_files": total_src_files,
            "duplicate_files": len(structure_results['common_files']),
            "different_files": len(structure_results['different_files']),
            "services_only": len(structure_results['services_only']),
            "src_only": len(structure_results['src_only']),
        }
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n分析结果已保存到: {output_file}")
    print("=" * 80)

if __name__ == "__main__":
    main()