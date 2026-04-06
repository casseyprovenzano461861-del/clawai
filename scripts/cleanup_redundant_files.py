#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理冗余文件和备份文件
识别并删除项目中的临时文件、备份文件和冗余副本
"""

import os
import sys
import shutil
import json
from pathlib import Path
from typing import List, Dict, Tuple, Set

# 设置标准输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

class RedundantFileCleaner:
    """冗余文件清理器"""
    
    def __init__(self, root_dir: str = None):
        self.root_dir = root_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.deleted_files = []
        self.deleted_dirs = []
        self.skipped_files = []
        self.total_size_freed = 0
        
        # 需要保留的关键目录
        self.critical_dirs = {
            "backend",
            "frontend", 
            "config",
            "configs",
            "utils",
            "scripts",
            "tests",
            "docs",
            "data",
            "logs",
            "reports",
            "tools",
            "external_tools"
        }
        
        # 需要保留的关键文件
        self.critical_files = {
            "README.md",
            "README_QUICKSTART.md",
            "README_updated.md",
            "config.py",
            "config/project_config.py",
            ".env",
            ".env.example",
            "docker-compose.yml",
            "Dockerfile",
            "Dockerfile.frontend",
            "Dockerfile.production",
            "start.bat",
            "package.json",
            "package-lock.json"
        }
        
        # 冗余文件模式
        self.redundant_patterns = [
            # 备份文件
            "*.backup", "*.bak", "*.old", "*.orig", "*.save",
            # 临时文件
            "*.tmp", "*.temp", "*.swp", "*.swo", "~*",
            # 缓存文件
            "*.pyc", "*.pyo", "__pycache__", ".pytest_cache",
            # 日志和调试文件
            "*.log", "debug_*.py", "test_*.log",
            # 重复文件
            "*_copy.py", "*_副本.py", "*_v2.py", "*_final.py", "*_enhanced.py"
        ]
        
        # 已知的冗余目录（相对路径）
        self.redundant_dirs = [
            "node_modules",  # 前端依赖
            ".git",         # Git目录（但需要保留）
            ".vscode",      # IDE配置
            ".idea",        # IDE配置
            "venv",         # Python虚拟环境
            "env",          # Python虚拟环境
            ".env.local",   # 本地环境文件
            "dist",         # 构建输出
            "build",        # 构建输出
            "coverage",     # 测试覆盖率
            ".pytest_cache" # pytest缓存
        ]
    
    def is_critical_file(self, filepath: str) -> bool:
        """检查是否是关键文件"""
        rel_path = os.path.relpath(filepath, self.root_dir)
        
        # 检查完整路径匹配
        if rel_path in self.critical_files:
            return True
        
        # 检查目录是否关键
        parts = Path(rel_path).parts
        if parts and parts[0] in self.critical_dirs:
            return True
        
        # 检查文件扩展名
        if filepath.endswith(('.py', '.md', '.json', '.yaml', '.yml', '.txt', '.bat', '.ps1', '.sh')):
            # 这些是源代码文件，通常需要保留
            # 但需要进一步检查是否是冗余副本
            filename = os.path.basename(filepath)
            
            # 检查是否是明显冗余的文件
            redundant_keywords = ['_copy', '_副本', '_v2', '_v3', '_final', '_enhanced', '_fixed']
            for keyword in redundant_keywords:
                if keyword in filename.lower():
                    # 检查是否有对应的主文件
                    base_name = filename.replace(keyword, '')
                    parent_dir = os.path.dirname(filepath)
                    
                    # 查找可能的原始文件
                    possible_originals = [
                        os.path.join(parent_dir, base_name),
                        os.path.join(parent_dir, base_name.replace('_enhanced', '')),
                        os.path.join(parent_dir, base_name.replace('_fixed', '')),
                        os.path.join(parent_dir, base_name.replace('_v2', '').replace('_v3', '')),
                    ]
                    
                    for original in possible_originals:
                        if os.path.exists(original):
                            print(f"  [警告]  发现冗余文件: {filename} (已有: {os.path.basename(original)})")
                            return False
            
            # 默认保留源代码文件
            return True
        
        return False
    
    def is_redundant_file(self, filepath: str) -> bool:
        """检查是否是冗余文件"""
        filename = os.path.basename(filepath)
        
        # 检查文件模式
        for pattern in self.redundant_patterns:
            if pattern.startswith('*'):
                extension = pattern[1:]
                if filename.endswith(extension) or filename == pattern[1:]:
                    return True
            elif pattern in filename:
                return True
        
        # 检查常见冗余模式
        redundant_patterns = [
            '备份', 'backup', 'old', 'temp', 'tmp', 
            '_copy', '_副本', '_duplicate', '_重复'
        ]
        
        for pattern in redundant_patterns:
            if pattern in filename.lower():
                return True
        
        return False
    
    def is_redundant_directory(self, dirpath: str) -> bool:
        """检查是否是冗余目录"""
        dirname = os.path.basename(dirpath)
        
        # 检查已知冗余目录
        if dirname in self.redundant_dirs:
            return True
        
        # 检查是否是IDE配置目录
        if dirname.startswith('.') and dirname not in ['.env', '.git']:
            return True
        
        # 检查是否是虚拟环境
        if dirname in ['venv', 'env', 'virtualenv', '.venv']:
            return True
        
        # 检查是否是构建输出
        if dirname in ['dist', 'build', 'out', 'target', 'bin', 'obj']:
            return True
        
        return False
    
    def find_redundant_files(self) -> List[Dict[str, any]]:
        """查找所有冗余文件"""
        redundant_files = []
        
        print(f"正在扫描目录: {self.root_dir}")
        print("=" * 80)
        
        for root, dirs, files in os.walk(self.root_dir):
            # 跳过冗余目录
            dirs[:] = [d for d in dirs if not self.is_redundant_directory(os.path.join(root, d))]
            
            # 检查文件
            for filename in files:
                filepath = os.path.join(root, filename)
                
                # 跳过关键文件
                if self.is_critical_file(filepath):
                    continue
                
                # 检查是否是冗余文件
                if self.is_redundant_file(filepath):
                    try:
                        file_size = os.path.getsize(filepath)
                        redundant_files.append({
                            'path': filepath,
                            'size': file_size,
                            'reason': self._get_redundant_reason(filepath)
                        })
                    except OSError:
                        # 无法访问的文件，跳过
                        pass
        
        return redundant_files
    
    def _get_redundant_reason(self, filepath: str) -> str:
        """获取文件冗余的原因"""
        filename = os.path.basename(filepath)
        
        reasons = []
        
        if '__pycache__' in filepath:
            reasons.append('Python缓存文件')
        elif filename.endswith('.pyc') or filename.endswith('.pyo'):
            reasons.append('Python编译文件')
        elif filename.endswith('.backup') or filename.endswith('.bak') or filename.endswith('.old'):
            reasons.append('备份文件')
        elif filename.endswith('.tmp') or filename.endswith('.temp'):
            reasons.append('临时文件')
        elif '_copy' in filename.lower() or '_副本' in filename.lower():
            reasons.append('重复副本')
        elif '_v2' in filename.lower() or '_v3' in filename.lower():
            reasons.append('版本冗余')
        elif '_final' in filename.lower() or '_enhanced' in filename.lower():
            reasons.append('改进冗余')
        elif '~' in filename:
            reasons.append('临时备份文件')
        
        if not reasons:
            return '未知冗余类型'
        
        return ', '.join(reasons)
    
    def find_duplicate_files(self) -> List[Dict[str, any]]:
        """查找重复文件（基于文件名模式）"""
        duplicate_files = []
        file_groups = {}
        
        # 按文件名模式分组
        for root, dirs, files in os.walk(self.root_dir):
            # 跳过冗余目录
            dirs[:] = [d for d in dirs if not self.is_redundant_directory(os.path.join(root, d))]
            
            for filename in files:
                if not filename.endswith('.py'):
                    continue
                
                # 标准化文件名（移除版本标记）
                normalized = self._normalize_filename(filename)
                if normalized not in file_groups:
                    file_groups[normalized] = []
                
                filepath = os.path.join(root, filename)
                try:
                    file_size = os.path.getsize(filepath)
                    file_groups[normalized].append({
                        'path': filepath,
                        'filename': filename,
                        'size': file_size,
                        'mtime': os.path.getmtime(filepath)
                    })
                except OSError:
                    pass
        
        # 查找有多个文件的组
        for normalized, files in file_groups.items():
            if len(files) > 1:
                # 按修改时间排序，保留最新的
                files.sort(key=lambda x: x['mtime'], reverse=True)
                latest = files[0]
                duplicates = files[1:]
                
                duplicate_files.append({
                    'original': latest,
                    'duplicates': duplicates,
                    'group_name': normalized
                })
        
        return duplicate_files
    
    def _normalize_filename(self, filename: str) -> str:
        """标准化文件名（移除版本标记）"""
        # 移除常见的版本后缀
        patterns_to_remove = [
            '_v2', '_v3', '_v4', '_v5',
            '_final', '_enhanced', '_fixed', '_improved',
            '_copy', '_副本', '_duplicate',
            '_backup', '_bak', '_old'
        ]
        
        normalized = filename.lower()
        for pattern in patterns_to_remove:
            normalized = normalized.replace(pattern, '')
        
        # 移除文件扩展名
        if '.' in normalized:
            normalized = normalized[:normalized.rindex('.')]
        
        return normalized
    
    def cleanup_files(self, redundant_files: List[Dict[str, any]], dry_run: bool = True) -> Dict[str, any]:
        """清理文件"""
        results = {
            'deleted': [],
            'skipped': [],
            'total_size': 0,
            'dry_run': dry_run
        }
        
        print(f"\n{'[DRY RUN] ' if dry_run else ''}开始清理文件:")
        print("=" * 80)
        
        for file_info in redundant_files:
            filepath = file_info['path']
            filesize = file_info['size']
            reason = file_info['reason']
            
            rel_path = os.path.relpath(filepath, self.root_dir)
            
            # 检查是否是关键文件
            if self.is_critical_file(filepath):
                print(f"  [警告]  跳过关键文件: {rel_path}")
                results['skipped'].append({
                    'path': filepath,
                    'reason': '关键文件'
                })
                continue
            
            # 检查文件是否存在
            if not os.path.exists(filepath):
                print(f"  [警告]  文件不存在: {rel_path}")
                continue
            
            try:
                if dry_run:
                    print(f"  [模拟] 删除: {rel_path} ({filesize:,} 字节) - {reason}")
                    results['deleted'].append({
                        'path': filepath,
                        'size': filesize,
                        'reason': reason
                    })
                    results['total_size'] += filesize
                else:
                    if os.path.isdir(filepath):
                        shutil.rmtree(filepath)
                        print(f"  [成功] 删除目录: {rel_path} ({filesize:,} 字节) - {reason}")
                    else:
                        os.remove(filepath)
                        print(f"  [成功] 删除文件: {rel_path} ({filesize:,} 字节) - {reason}")
                    
                    results['deleted'].append({
                        'path': filepath,
                        'size': filesize,
                        'reason': reason
                    })
                    results['total_size'] += filesize
                    
            except Exception as e:
                print(f"  [失败] 删除失败: {rel_path} - {str(e)}")
                results['skipped'].append({
                    'path': filepath,
                    'reason': f'删除失败: {str(e)}'
                })
        
        return results
    
    def cleanup_duplicate_files(self, duplicate_groups: List[Dict[str, any]], dry_run: bool = True) -> Dict[str, any]:
        """清理重复文件"""
        results = {
            'deleted': [],
            'skipped': [],
            'total_size': 0,
            'dry_run': dry_run
        }
        
        print(f"\n{'[DRY RUN] ' if dry_run else ''}开始清理重复文件:")
        print("=" * 80)
        
        for group in duplicate_groups:
            original = group['original']
            duplicates = group['duplicates']
            group_name = group['group_name']
            
            print(f"\n  [文件组] 文件组: {group_name}")
            print(f"    原始文件: {os.path.relpath(original['path'], self.root_dir)} (最新)")
            
            for dup in duplicates:
                rel_path = os.path.relpath(dup['path'], self.root_dir)
                
                # 检查是否是关键文件
                if self.is_critical_file(dup['path']):
                    print(f"    [警告]  跳过关键文件: {rel_path}")
                    results['skipped'].append({
                        'path': dup['path'],
                        'reason': '关键文件',
                        'group': group_name
                    })
                    continue
                
                try:
                    if dry_run:
                        print(f"    [模拟] 删除重复: {rel_path} ({dup['size']:,} 字节)")
                        results['deleted'].append({
                            'path': dup['path'],
                            'size': dup['size'],
                            'reason': f'重复文件: {group_name}',
                            'group': group_name
                        })
                        results['total_size'] += dup['size']
                    else:
                        os.remove(dup['path'])
                        print(f"    [成功] 删除重复: {rel_path} ({dup['size']:,} 字节)")
                        
                        results['deleted'].append({
                            'path': dup['path'],
                            'size': dup['size'],
                            'reason': f'重复文件: {group_name}',
                            'group': group_name
                        })
                        results['total_size'] += dup['size']
                        
                except Exception as e:
                    print(f"    [失败] 删除失败: {rel_path} - {str(e)}")
                    results['skipped'].append({
                        'path': dup['path'],
                        'reason': f'删除失败: {str(e)}',
                        'group': group_name
                    })
        
        return results
    
    def generate_report(self, cleanup_results: Dict[str, any], duplicate_results: Dict[str, any]) -> str:
        """生成清理报告"""
        report_lines = []
        
        report_lines.append("=" * 100)
        report_lines.append("ClawAI 冗余文件清理报告")
        report_lines.append("=" * 100)
        
        # 汇总统计
        total_deleted = len(cleanup_results['deleted']) + len(duplicate_results['deleted'])
        total_size = cleanup_results['total_size'] + duplicate_results['total_size']
        total_skipped = len(cleanup_results['skipped']) + len(duplicate_results['skipped'])
        
        mode = "模拟运行" if cleanup_results['dry_run'] else "实际执行"
        
        report_lines.append(f"\n[统计] 清理汇总 ({mode}):")
        report_lines.append(f"  删除文件数: {total_deleted}")
        report_lines.append(f"  释放空间: {total_size:,} 字节 ({total_size/1024/1024:.2f} MB)")
        report_lines.append(f"  跳过文件数: {total_skipped}")
        
        # 冗余文件详情
        if cleanup_results['deleted']:
            report_lines.append(f"\n[删除] 冗余文件清理详情 ({len(cleanup_results['deleted'])} 个):")
            for file_info in cleanup_results['deleted'][:20]:  # 最多显示20个
                rel_path = os.path.relpath(file_info['path'], self.root_dir)
                report_lines.append(f"  - {rel_path} ({file_info['size']:,} 字节) - {file_info['reason']}")
            
            if len(cleanup_results['deleted']) > 20:
                report_lines.append(f"  ... 还有 {len(cleanup_results['deleted']) - 20} 个文件未显示")
        
        # 重复文件详情
        if duplicate_results['deleted']:
            report_lines.append(f"\n[文档] 重复文件清理详情 ({len(duplicate_results['deleted'])} 个):")
            
            # 按分组显示
            groups = {}
            for file_info in duplicate_results['deleted']:
                group = file_info.get('group', '未知')
                if group not in groups:
                    groups[group] = []
                groups[group].append(file_info)
            
            for group_name, files in list(groups.items())[:10]:  # 最多显示10个组
                report_lines.append(f"  [组] {group_name}: {len(files)} 个重复文件")
                for file_info in files[:3]:  # 每个组最多显示3个
                    rel_path = os.path.relpath(file_info['path'], self.root_dir)
                    report_lines.append(f"    - {rel_path} ({file_info['size']:,} 字节)")
                if len(files) > 3:
                    report_lines.append(f"    ... 还有 {len(files) - 3} 个文件")
        
        # 跳过的文件
        all_skipped = cleanup_results['skipped'] + duplicate_results['skipped']
        if all_skipped:
            report_lines.append(f"\n[警告]  跳过的文件 ({len(all_skipped)} 个):")
            for skip_info in all_skipped[:10]:
                rel_path = os.path.relpath(skip_info['path'], self.root_dir)
                reason = skip_info.get('reason', '未知原因')
                report_lines.append(f"  - {rel_path} - {reason}")
            
            if len(all_skipped) > 10:
                report_lines.append(f"  ... 还有 {len(all_skipped) - 10} 个文件未显示")
        
        # 建议
        report_lines.append(f"\n[建议] 建议:")
        if cleanup_results['dry_run']:
            report_lines.append("  1. 运行清理命令: python scripts/cleanup_redundant_files.py --execute")
            report_lines.append("  2. 清理前建议备份重要文件")
        else:
            report_lines.append("  1. [成功] 清理已完成")
            report_lines.append("  2. 建议定期运行清理以保持项目整洁")
        
        report_lines.append(f"\n[目录] 项目根目录: {self.root_dir}")
        report_lines.append("=" * 100)
        
        return "\n".join(report_lines)
    
    def save_report(self, report: str, filename: str = None):
        """保存报告"""
        if filename is None:
            reports_dir = os.path.join(self.root_dir, "reports")
            os.makedirs(reports_dir, exist_ok=True)
            filename = os.path.join(reports_dir, "redundant_files_cleanup_report.txt")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n[文档] 报告已保存: {filename}")
        return filename

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='清理冗余文件和备份文件')
    parser.add_argument('--execute', action='store_true', help='实际执行删除操作（默认是模拟运行）')
    parser.add_argument('--root', type=str, help='项目根目录')
    parser.add_argument('--report', type=str, help='报告文件路径')
    
    args = parser.parse_args()
    
    print("[搜索] ClawAI 冗余文件清理工具")
    print("正在初始化清理器...")
    
    try:
        cleaner = RedundantFileCleaner(args.root)
        
        # 查找冗余文件
        print("\n1. 查找冗余文件...")
        redundant_files = cleaner.find_redundant_files()
        print(f"   找到 {len(redundant_files)} 个冗余文件")
        
        # 查找重复文件
        print("\n2. 查找重复文件...")
        duplicate_groups = cleaner.find_duplicate_files()
        duplicate_files_count = sum(len(g['duplicates']) for g in duplicate_groups)
        print(f"   找到 {duplicate_files_count} 个重复文件（{len(duplicate_groups)} 个文件组）")
        
        if not redundant_files and duplicate_files_count == 0:
            print("\n[成功] 未发现需要清理的冗余文件！")
            return 0
        
        # 清理文件
        dry_run = not args.execute
        
        cleanup_results = cleaner.cleanup_files(redundant_files, dry_run=dry_run)
        duplicate_results = cleaner.cleanup_duplicate_files(duplicate_groups, dry_run=dry_run)
        
        # 生成报告
        print("\n生成清理报告...")
        report = cleaner.generate_report(cleanup_results, duplicate_results)
        print(report)
        
        # 保存报告
        report_file = cleaner.save_report(report, args.report)
        
        # 显示摘要
        total_deleted = len(cleanup_results['deleted']) + len(duplicate_results['deleted'])
        total_size = cleanup_results['total_size'] + duplicate_results['total_size']
        
        print(f"\n[统计] 清理完成摘要:")
        print(f"  模式: {'模拟运行' if dry_run else '实际执行'}")
        print(f"  删除文件数: {total_deleted}")
        print(f"  释放空间: {total_size:,} 字节 ({total_size/1024/1024:.2f} MB)")
        
        if dry_run and total_deleted > 0:
            print(f"\n[建议] 要实际执行清理，请运行: python scripts/cleanup_redundant_files.py --execute")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n[中断]  清理被用户中断")
        return 1
    except Exception as e:
        print(f"\n[失败] 清理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())