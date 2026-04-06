# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
清理docs和archive目录中的过期文件、锐评文件和重复文件
扩展自cleanup_archive_files.py，支持多目录清理
"""

import os
import sys
import shutil
from datetime import datetime, timedelta
from pathlib import Path

class MultiDirectoryCleaner:
    """多目录清理器"""
    
    def __init__(self, directories: list = None):
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        
        # 默认清理目录
        if directories is None:
            self.directories = [
                os.path.join(self.base_dir, "docs"),
                os.path.join(self.base_dir, "archive")
            ]
        else:
            self.directories = directories
        
        self.deleted_files = []
        self.deleted_size = 0
        self.kept_files = []
        
        # 需要保留的重要文件关键词（扩展到docs目录）
        self.important_keywords = [
            # 文档/指南类
            "README", "API使用指南", "TECHNICAL_DOCUMENTATION", "DEPLOYMENT", "INSTALL",
            "GUIDE", "guide", "README_dynamic", "tool_priority",
            
            # 演示类
            "PPT", "presentation", "demo", "demo_presentation", "ClawAI_Demo_Presentation",
            
            # 计划和紧急类
            "emergency", "DAY7", "day7", "executor", "workflow", "PLAN",
            
            # 架构和优化类
            "architecture", "frontend", "optimized", "unification", "migration",
            "unified", "optimization", "structure",
            
            # 配置和部署
            "deploy", "config", "production", "docker", "nginx",
            
            # 报告（只保留少数重要报告）
            "performance", "concurrent", "user_experience", "user_acceptance"
        ]
        
        # 需要清理的锐评/分析文件关键词
        self.critical_keywords = [
            # 中文关键词
            "锐评", "评价", "评估", "分析", "总结", "报告", "改进", "方案", "计划",
            "实施", "短期", "中期", "长期", "优化", "整理", "完成", "问题", "解决方案",
            
            # 英文关键词
            "analysis", "summary", "report", "improvement", "optimization",
            "plan", "implementation", "short_term", "mid_term", "long_term",
            "review", "assessment", "evaluation", "solution", "problem",
            "archive_", "comprehensive", "cleanup"
        ]
        
        # 文件类型扩展名（支持更多文档类型）
        self.file_extensions = ['.md', '.txt', '.rst', '.adoc', '.org', '.docx', '.pdf']
        
        # 过期天数（超过14天的文件认为是过期的）
        self.expiry_days = 14
        
        # 保留最近报告数量
        self.keep_recent_reports = 2
    
    def should_keep_file(self, filepath: str, filename: str, file_mtime: datetime) -> bool:
        """判断是否应该保留文件"""
        
        # 1. 检查是否是重要文件
        for keyword in self.important_keywords:
            if keyword.lower() in filename.lower():
                return True
        
        # 2. 检查是否是近期文件（14天内）
        today = datetime.now()
        if file_mtime + timedelta(days=self.expiry_days) >= today:
            return True
        
        # 3. 检查是否是最终版本或演示文件
        final_keywords = ["final", "demo", "presentation", "deployment", "production", "release"]
        if any(x in filename.lower() for x in final_keywords):
            return True
        
        # 4. 检查是否是技术文档或指南
        guide_keywords = ["guide", "指南", "manual", "handbook", "教程", "tutorial"]
        if any(x in filename.lower() for x in guide_keywords):
            return True
        
        # 5. 对于锐评文件，进一步分析
        if any(keyword in filename for keyword in self.critical_keywords):
            # 这类文件需要进一步分析，暂时标记为待处理
            return None
        
        return False
    
    def analyze_directory(self, directory: str) -> dict:
        """分析单个目录中的文件"""
        analysis = {
            'directory': directory,
            'total_files': 0,
            'total_size': 0,
            'critical_reports': [],
            'expired_files': [],
            'all_files': []
        }
        
        # 收集所有文件
        for ext in self.file_extensions:
            for filepath in Path(directory).glob(f"*{ext}"):
                filepath_str = str(filepath)
                filename = filepath.name
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                size = filepath.stat().st_size
                
                file_info = {
                    'path': filepath_str,
                    'filename': filename,
                    'mtime': mtime,
                    'size': size
                }
                
                analysis['total_files'] += 1
                analysis['total_size'] += size
                analysis['all_files'].append(file_info)
                
                # 检查是否是锐评/分析报告
                is_critical = any(keyword in filename for keyword in self.critical_keywords)
                if is_critical:
                    analysis['critical_reports'].append(file_info)
                
                # 检查是否过期（超过14天）
                today = datetime.now()
                if mtime + timedelta(days=self.expiry_days) < today:
                    expired_info = file_info.copy()
                    expired_info['days_old'] = (today - mtime).days
                    analysis['expired_files'].append(expired_info)
        
        return analysis
    
    def analyze_all_directories(self) -> dict:
        """分析所有目录"""
        all_analysis = {
            'directories': {},
            'summary': {
                'total_files': 0,
                'total_size': 0,
                'critical_reports': 0,
                'expired_files': 0
            }
        }
        
        for directory in self.directories:
            if not os.path.exists(directory):
                print(f"[警告] 目录不存在: {directory}")
                continue
            
            print(f"[分析] 正在分析: {directory}")
            analysis = self.analyze_directory(directory)
            all_analysis['directories'][directory] = analysis
            
            # 更新汇总统计
            all_analysis['summary']['total_files'] += analysis['total_files']
            all_analysis['summary']['total_size'] += analysis['total_size']
            all_analysis['summary']['critical_reports'] += len(analysis['critical_reports'])
            all_analysis['summary']['expired_files'] += len(analysis['expired_files'])
        
        return all_analysis
    
    def generate_cleanup_plan(self, all_analysis: dict) -> dict:
        """生成清理计划"""
        plan = {
            'delete': [],
            'keep': [],
            'reason': {},
            'by_directory': {}
        }
        
        for directory, analysis in all_analysis['directories'].items():
            plan['by_directory'][directory] = {
                'delete': [],
                'keep': [],
                'total_files': analysis['total_files']
            }
            
            # 处理锐评/分析报告：保留最新的几个，删除旧的
            critical_reports = analysis['critical_reports']
            if critical_reports:
                # 按修改时间排序
                critical_reports.sort(key=lambda x: x['mtime'], reverse=True)
                
                # 保留最新的几个
                keep_count = min(self.keep_recent_reports, len(critical_reports))
                for i, report in enumerate(critical_reports):
                    if i < keep_count:
                        plan['keep'].append(report['path'])
                        plan['by_directory'][directory]['keep'].append(report['path'])
                        plan['reason'][report['path']] = f"保留最近的分析报告 ({i+1}/{keep_count})"
                    else:
                        today = datetime.now()
                        days_old = (today - report['mtime']).days
                        plan['delete'].append(report['path'])
                        plan['by_directory'][directory]['delete'].append(report['path'])
                        plan['reason'][report['path']] = f"删除旧的分析报告 ({days_old}天前)"
            
            # 处理过期文件（非重要文件）
            expired_files = analysis['expired_files']
            for expired in expired_files:
                # 检查是否是重要文件
                filename = expired['filename']
                is_important = any(keyword.lower() in filename.lower() 
                                 for keyword in self.important_keywords)
                
                if not is_important and expired['path'] not in plan['delete']:
                    plan['delete'].append(expired['path'])
                    plan['by_directory'][directory]['delete'].append(expired['path'])
                    plan['reason'][expired['path']] = f"过期文件 ({expired['days_old']}天前)"
                elif is_important:
                    plan['keep'].append(expired['path'])
                    plan['by_directory'][directory]['keep'].append(expired['path'])
                    plan['reason'][expired['path']] = f"保留重要文件（虽过期{expired['days_old']}天）"
        
        # 移除重复项
        plan['delete'] = list(set(plan['delete']))
        plan['keep'] = list(set(plan['keep']))
        
        # 确保delete和keep没有重叠
        for path in plan['delete']:
            if path in plan['keep']:
                plan['keep'].remove(path)
                if path in plan['reason']:
                    del plan['reason'][path]
        
        return plan
    
    def execute_cleanup(self, plan: dict, dry_run: bool = True) -> dict:
        """执行清理"""
        results = {
            'deleted': [],
            'kept': [],
            'errors': [],
            'total_size_freed': 0,
            'dry_run': dry_run,
            'by_directory': {}
        }
        
        print(f"\n{'[模拟运行] ' if dry_run else ''}开始清理docs和archive目录:")
        print("=" * 80)
        
        # 按目录分组删除
        for directory in self.directories:
            if not os.path.exists(directory):
                continue
            
            dir_deleted = []
            dir_kept = []
            
            print(f"\n处理目录: {directory}")
            print("-" * 40)
            
            # 获取该目录需要删除的文件
            dir_files_to_delete = [f for f in plan['delete'] if f.startswith(directory)]
            
            for filepath in dir_files_to_delete:
                try:
                    if os.path.exists(filepath):
                        file_size = os.path.getsize(filepath)
                        
                        if dry_run:
                            print(f"  [模拟] 删除: {os.path.basename(filepath)} ({file_size:,} 字节)")
                            print(f"      原因: {plan['reason'].get(filepath, '未知')}")
                        else:
                            os.remove(filepath)
                            print(f"  [删除] 已删除: {os.path.basename(filepath)} ({file_size:,} 字节)")
                            print(f"      原因: {plan['reason'].get(filepath, '未知')}")
                        
                        results['deleted'].append({
                            'path': filepath,
                            'size': file_size,
                            'reason': plan['reason'].get(filepath, '未知')
                        })
                        dir_deleted.append({
                            'path': filepath,
                            'size': file_size,
                            'reason': plan['reason'].get(filepath, '未知')
                        })
                        results['total_size_freed'] += file_size
                    else:
                        print(f"  [警告] 文件不存在: {filepath}")
                except Exception as e:
                    error_msg = f"删除失败: {str(e)}"
                    print(f"  [错误] {error_msg}: {os.path.basename(filepath)}")
                    results['errors'].append({
                        'path': filepath,
                        'error': error_msg
                    })
            
            # 记录该目录保留的文件
            dir_files_to_keep = [f for f in plan['keep'] if f.startswith(directory)]
            for filepath in dir_files_to_keep:
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    results['kept'].append({
                        'path': filepath,
                        'size': file_size,
                        'reason': plan['reason'].get(filepath, '保留')
                    })
                    dir_kept.append({
                        'path': filepath,
                        'size': file_size,
                        'reason': plan['reason'].get(filepath, '保留')
                    })
            
            results['by_directory'][directory] = {
                'deleted': dir_deleted,
                'kept': dir_kept,
                'deleted_count': len(dir_deleted),
                'kept_count': len(dir_kept)
            }
        
        return results
    
    def generate_report(self, all_analysis: dict, plan: dict, results: dict) -> str:
        """生成清理报告"""
        report_lines = []
        
        report_lines.append("=" * 120)
        report_lines.append("ClawAI Docs和Archive目录清理报告")
        report_lines.append("=" * 120)
        
        # 基本信息
        report_lines.append(f"\n[基本信息]")
        report_lines.append(f"  清理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"  清理目录数: {len(self.directories)}")
        report_lines.append(f"  原始总文件数: {all_analysis['summary']['total_files']}")
        report_lines.append(f"  原始总大小: {all_analysis['summary']['total_size']:,} 字节 ({all_analysis['summary']['total_size']/1024/1024:.2f} MB)")
        
        # 各目录详细分析
        report_lines.append(f"\n[各目录详细分析]")
        for directory, analysis in all_analysis['directories'].items():
            dir_name = os.path.basename(directory)
            report_lines.append(f"\n  [目录] {dir_name}:")
            report_lines.append(f"    文件总数: {analysis['total_files']}")
            report_lines.append(f"    锐评/分析报告: {len(analysis['critical_reports'])} 个")
            report_lines.append(f"    过期文件 (>14天): {len(analysis['expired_files'])} 个")
            report_lines.append(f"    总大小: {analysis['total_size']:,} 字节")
        
        # 清理计划
        report_lines.append(f"\n[清理计划]")
        report_lines.append(f"  计划删除: {len(plan['delete'])} 个文件")
        report_lines.append(f"  计划保留: {len(plan['keep'])} 个文件")
        
        # 执行结果
        if results:
            mode = "模拟运行" if results['dry_run'] else "实际执行"
            report_lines.append(f"\n[执行结果] ({mode})")
            report_lines.append(f"  实际删除: {len(results['deleted'])} 个文件")
            report_lines.append(f"  释放空间: {results['total_size_freed']:,} 字节 ({results['total_size_freed']/1024/1024:.2f} MB)")
            report_lines.append(f"  错误数: {len(results['errors'])}")
            
            # 各目录执行结果
            report_lines.append(f"\n[各目录执行结果]")
            for directory, dir_results in results['by_directory'].items():
                dir_name = os.path.basename(directory)
                report_lines.append(f"\n  [目录] {dir_name}:")
                report_lines.append(f"    删除文件数: {dir_results['deleted_count']}")
                report_lines.append(f"    保留文件数: {dir_results['kept_count']}")
                
                if dir_results['deleted']:
                    report_lines.append(f"    已删除文件示例:")
                    for deleted in dir_results['deleted'][:3]:  # 最多显示3个
                        filename = os.path.basename(deleted['path'])
                        report_lines.append(f"      - {filename} ({deleted['size']:,} 字节)")
                        report_lines.append(f"        原因: {deleted['reason']}")
                    
                    if len(dir_results['deleted']) > 3:
                        report_lines.append(f"      ... 还有 {len(dir_results['deleted']) - 3} 个文件未显示")
        
        # 重要保留文件
        if plan['keep']:
            report_lines.append(f"\n[重要保留文件]")
            kept_important = []
            for filepath in plan['keep']:
                filename = os.path.basename(filepath)
                if any(keyword.lower() in filename.lower() for keyword in self.important_keywords):
                    if os.path.exists(filepath):
                        size = os.path.getsize(filepath)
                        kept_important.append((filename, size, filepath))
            
            # 按目录分组显示
            dir_groups = {}
            for filename, size, filepath in kept_important:
                dir_path = os.path.dirname(filepath)
                dir_name = os.path.basename(dir_path)
                if dir_name not in dir_groups:
                    dir_groups[dir_name] = []
                dir_groups[dir_name].append((filename, size))
            
            for dir_name, files in dir_groups.items():
                report_lines.append(f"\n  [目录] {dir_name}:")
                for i, (filename, size) in enumerate(files[:5]):  # 每个目录最多显示5个
                    report_lines.append(f"    {i+1}. {filename} ({size:,} 字节)")
                
                if len(files) > 5:
                    report_lines.append(f"    ... 还有 {len(files) - 5} 个文件")
        
        # 建议
        report_lines.append(f"\n[建议]")
        if results and results['dry_run'] and len(plan['delete']) > 0:
            report_lines.append("  1. 运行实际清理: python scripts/cleanup_docs_and_archive.py --execute")
        else:
            report_lines.append("  1. [成功] 清理已完成")
        
        report_lines.append("  2. 建议定期运行清理，保持文档目录整洁")
        report_lines.append("  3. 新分析报告应放在特定reports目录下")
        report_lines.append("  4. 技术文档和指南应放在docs/guides目录下")
        
        report_lines.append("\n" + "=" * 120)
        
        return "\n".join(report_lines)
    
    def save_report(self, report: str, filename: str = None):
        """保存报告"""
        if filename is None:
            reports_dir = os.path.join(self.base_dir, "reports")
            os.makedirs(reports_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(reports_dir, f"docs_and_archive_cleanup_report_{timestamp}.md")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n[报告] 报告已保存: {filename}")
        return filename

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='清理docs和archive目录中的过期文件和锐评文件')
    parser.add_argument('--execute', action='store_true', help='实际执行删除操作（默认是模拟运行）')
    parser.add_argument('--keep-reports', type=int, default=2, help='保留最近的分析报告数量（默认: 2）')
    parser.add_argument('--docs-only', action='store_true', help='只清理docs目录')
    parser.add_argument('--archive-only', action='store_true', help='只清理archive目录')
    
    args = parser.parse_args()
    
    print("[工具] ClawAI Docs和Archive目录清理工具")
    
    # 确定要清理的目录
    base_dir = os.path.dirname(os.path.dirname(__file__))
    directories = []
    
    if args.docs_only:
        directories.append(os.path.join(base_dir, "docs"))
        print("模式: 只清理docs目录")
    elif args.archive_only:
        directories.append(os.path.join(base_dir, "archive"))
        print("模式: 只清理archive目录")
    else:
        directories = [
            os.path.join(base_dir, "docs"),
            os.path.join(base_dir, "archive")
        ]
        print("模式: 同时清理docs和archive目录")
    
    try:
        cleaner = MultiDirectoryCleaner(directories)
        cleaner.keep_recent_reports = args.keep_reports
        
        print("正在分析目录...")
        
        # 分析文件
        all_analysis = cleaner.analyze_all_directories()
        
        if all_analysis['summary']['total_files'] == 0:
            print("[空] 目标目录中没有找到文件")
            return 0
        
        print(f"[统计] 分析完成:")
        print(f"  总文件数: {all_analysis['summary']['total_files']}")
        print(f"  锐评/分析报告: {all_analysis['summary']['critical_reports']} 个")
        print(f"  过期文件 (>14天): {all_analysis['summary']['expired_files']} 个")
        print(f"  总大小: {all_analysis['summary']['total_size']:,} 字节 ({all_analysis['summary']['total_size']/1024/1024:.2f} MB)")
        
        # 生成清理计划
        plan = cleaner.generate_cleanup_plan(all_analysis)
        
        if not plan['delete']:
            print("\n[成功] 未发现需要清理的文件，所有目录已保持整洁")
            return 0
        
        print(f"\n[计划] 清理计划:")
        print(f"  计划删除: {len(plan['delete'])} 个文件")
        print(f"  计划保留: {len(plan['keep'])} 个文件")
        
        # 显示各目录计划
        for directory, dir_plan in plan['by_directory'].items():
            dir_name = os.path.basename(directory)
            print(f"  [目录] {dir_name}: 删除 {len(dir_plan['delete'])} 个，保留 {len(dir_plan['keep'])} 个")
        
        # 执行清理
        dry_run = not args.execute
        results = cleaner.execute_cleanup(plan, dry_run=dry_run)
        
        # 生成报告
        print("\n[报告] 生成清理报告...")
        report = cleaner.generate_report(all_analysis, plan, results)
        print(report)
        
        # 保存报告
        report_file = cleaner.save_report(report)
        
        # 显示摘要
        if results['deleted']:
            print(f"\n[摘要] 清理摘要:")
            print(f"  模式: {'模拟运行' if dry_run else '实际执行'}")
            print(f"  删除文件数: {len(results['deleted'])}")
            print(f"  释放空间: {results['total_size_freed']:,} 字节 ({results['total_size_freed']/1024/1024:.2f} MB)")
        
        if dry_run and plan['delete']:
            print(f"\n[建议] 要实际执行清理，请运行: python scripts/cleanup_docs_and_archive.py --execute")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n[中断] 清理被用户中断")
        return 1
    except Exception as e:
        print(f"\n[失败] 清理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())