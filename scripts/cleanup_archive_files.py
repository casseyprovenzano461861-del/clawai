# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
专门清理archive目录中的过期文件和锐评文件
智能保留重要文件，删除重复和过时内容
"""

import os
import sys
import shutil
from datetime import datetime, timedelta
from pathlib import Path

class ArchiveCleaner:
    """archive目录清理器"""
    
    def __init__(self, archive_dir: str = None):
        self.archive_dir = archive_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "archive")
        self.deleted_files = []
        self.deleted_size = 0
        self.kept_files = []
        
        # 需要保留的重要文件（基于文件名关键词）
        self.important_keywords = [
            "README", "PPT", "presentation", "demo", "demo_presentation", 
            "emergency", "DAY7", "day7", "executor", "workflow",
            "architecture", "frontend", "optimized"
        ]
        
        # 需要清理的锐评/分析文件关键词
        self.critical_keywords = [
            "锐评", "评价", "评估", "分析", "总结", "报告",
            "improvement", "analysis", "summary", "report", "optimization"
        ]
        
        # 重复文件模式
        self.duplicate_patterns = [
            ("项目全面锐评报告", "深度锐评报告"),  # 全面报告应该保留最新的
            ("ClawAI问题解决方案总结", "ClawAI项目详细优化方向报告"),  # 优化方向可能更新
            ("项目整理优化方案", "项目整理完成报告"),  # 完成报告可能更完整
        ]
        
        # 过期天数（超过7天的文件认为是过期的）
        self.expiry_days = 7
    
    def should_keep_file(self, filepath: str, file_mtime: datetime) -> bool:
        """判断是否应该保留文件"""
        filename = os.path.basename(filepath)
        
        # 1. 检查是否是重要文件
        for keyword in self.important_keywords:
            if keyword.lower() in filename.lower():
                return True
        
        # 2. 检查是否是近期文件（7天内）
        today = datetime.now()
        if file_mtime + timedelta(days=self.expiry_days) >= today:
            return True
        
        # 3. 检查是否是最终版本或演示文件
        if any(x in filename.lower() for x in ["final", "demo", "presentation", "deployment"]):
            return True
        
        # 4. 对于锐评文件，保留最新的2-3个
        if any(keyword in filename for keyword in ["锐评", "评估", "分析", "总结"]):
            # 这类文件需要进一步分析，暂时标记为待处理
            return None
        
        return False
    
    def find_duplicate_files(self) -> list:
        """查找重复文件"""
        duplicates = []
        files_by_type = {}
        
        for filepath in Path(self.archive_dir).glob("*.md"):
            filename = filepath.name
            
            # 提取文件类型（移除日期和版本信息）
            file_type = self._extract_file_type(filename)
            if not file_type:
                continue
            
            if file_type not in files_by_type:
                files_by_type[file_type] = []
            
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
            files_by_type[file_type].append({
                'path': str(filepath),
                'filename': filename,
                'mtime': mtime,
                'size': filepath.stat().st_size
            })
        
        # 找出有重复的文件类型
        for file_type, files in files_by_type.items():
            if len(files) > 1:
                # 按修改时间排序
                files.sort(key=lambda x: x['mtime'], reverse=True)
                
                # 保留最新的1-2个，标记其余的为重复
                keep_count = min(2, len(files))
                for i, file_info in enumerate(files):
                    if i >= keep_count:
                        duplicates.append(file_info)
        
        return duplicates
    
    def _extract_file_type(self, filename: str) -> str:
        """提取文件类型（移除日期和版本信息）"""
        # 移除日期信息（如_20260330）
        import re
        filename = re.sub(r'_\d{8}', '', filename)
        
        # 移除文件扩展名
        if filename.endswith('.md'):
            filename = filename[:-3]
        
        # 移除常见版本后缀
        for suffix in ['_v2', '_v3', '_final', '_enhanced', '_updated']:
            if filename.endswith(suffix):
                filename = filename[:-len(suffix)]
        
        return filename.lower()
    
    def analyze_files(self) -> dict:
        """分析archive目录中的文件"""
        analysis = {
            'total_files': 0,
            'total_size': 0,
            'to_delete': [],
            'to_keep': [],
            'duplicates': [],
            'expired': [],
            'critical_reports': []
        }
        
        # 查找重复文件
        duplicates = self.find_duplicate_files()
        analysis['duplicates'] = duplicates
        
        # 分析所有文件
        for filepath in Path(self.archive_dir).glob("*.md"):
            filepath_str = str(filepath)
            filename = filepath.name
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
            size = filepath.stat().st_size
            
            analysis['total_files'] += 1
            analysis['total_size'] += size
            
            # 检查是否是锐评/分析报告
            is_critical = any(keyword in filename for keyword in self.critical_keywords)
            if is_critical:
                analysis['critical_reports'].append({
                    'path': filepath_str,
                    'filename': filename,
                    'mtime': mtime,
                    'size': size
                })
            
            # 检查是否过期（超过7天）
            today = datetime.now()
            if mtime + timedelta(days=self.expiry_days) < today:
                analysis['expired'].append({
                    'path': filepath_str,
                    'filename': filename,
                    'mtime': mtime,
                    'size': size,
                    'days_old': (today - mtime).days
                })
        
        return analysis
    
    def generate_cleanup_plan(self, analysis: dict, keep_recent_reports: int = 3) -> dict:
        """生成清理计划"""
        plan = {
            'delete': [],
            'keep': [],
            'reason': {}
        }
        
        # 1. 首先标记所有重复文件为删除
        for dup in analysis['duplicates']:
            plan['delete'].append(dup['path'])
            plan['reason'][dup['path']] = f"重复文件: {dup['filename']}"
        
        # 2. 处理锐评/分析报告：保留最新的几个，删除旧的
        critical_reports = analysis['critical_reports']
        if critical_reports:
            # 按修改时间排序
            critical_reports.sort(key=lambda x: x['mtime'], reverse=True)
            
            # 保留最新的几个
            keep_count = min(keep_recent_reports, len(critical_reports))
            for i, report in enumerate(critical_reports):
                if i < keep_count:
                    plan['keep'].append(report['path'])
                    plan['reason'][report['path']] = f"保留最近的分析报告 ({i+1}/{keep_count})"
                else:
                    # 计算days_old
                    today = datetime.now()
                    days_old = (today - report['mtime']).days
                    plan['delete'].append(report['path'])
                    plan['reason'][report['path']] = f"删除旧的分析报告 ({days_old}天前)"
        
        # 3. 处理过期文件（非重要文件）
        expired_files = analysis['expired']
        for expired in expired_files:
            # 检查是否是重要文件
            filename = expired['filename']
            is_important = any(keyword.lower() in filename.lower() 
                             for keyword in self.important_keywords)
            
            if not is_important and expired['path'] not in plan['delete']:
                plan['delete'].append(expired['path'])
                plan['reason'][expired['path']] = f"过期文件 ({expired['days_old']}天前)"
            elif is_important:
                plan['keep'].append(expired['path'])
                plan['reason'][expired['path']] = f"保留重要文件（虽过期{expired['days_old']}天）"
        
        # 移除重复项
        plan['delete'] = list(set(plan['delete']))
        plan['keep'] = list(set(plan['keep']))
        
        # 确保delete和keep没有重叠
        for path in plan['delete']:
            if path in plan['keep']:
                plan['keep'].remove(path)
        
        return plan
    
    def execute_cleanup(self, plan: dict, dry_run: bool = True) -> dict:
        """执行清理"""
        results = {
            'deleted': [],
            'kept': [],
            'errors': [],
            'total_size_freed': 0,
            'dry_run': dry_run
        }
        
        print(f"\n{'[模拟运行] ' if dry_run else ''}开始清理archive目录:")
        print("=" * 80)
        
        # 删除文件
        for filepath in plan['delete']:
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
        
        # 记录保留的文件
        for filepath in plan['keep']:
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                results['kept'].append({
                    'path': filepath,
                    'size': file_size,
                    'reason': plan['reason'].get(filepath, '保留')
                })
        
        return results
    
    def generate_report(self, analysis: dict, plan: dict, results: dict) -> str:
        """生成清理报告"""
        report_lines = []
        
        report_lines.append("=" * 100)
        report_lines.append("ClawAI Archive目录清理报告")
        report_lines.append("=" * 100)
        
        # 基本信息
        report_lines.append(f"\n[目录] 目录: {self.archive_dir}")
        report_lines.append(f"[统计] 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"[图表] 原始文件数: {analysis['total_files']}")
        report_lines.append(f"[大小] 原始总大小: {analysis['total_size']:,} 字节 ({analysis['total_size']/1024/1024:.2f} MB)")
        
        # 分析摘要
        report_lines.append(f"\n[分析] 分析摘要:")
        report_lines.append(f"  锐评/分析报告: {len(analysis['critical_reports'])} 个")
        report_lines.append(f"  过期文件 (>7天): {len(analysis['expired'])} 个")
        report_lines.append(f"  重复文件: {len(analysis['duplicates'])} 个")
        
        # 清理计划
        report_lines.append(f"\n[计划] 清理计划:")
        report_lines.append(f"  计划删除: {len(plan['delete'])} 个文件")
        report_lines.append(f"  计划保留: {len(plan['keep'])} 个文件")
        
        if results:
            mode = "模拟运行" if results['dry_run'] else "实际执行"
            report_lines.append(f"\n[执行] 执行结果 ({mode}):")
            report_lines.append(f"  实际删除: {len(results['deleted'])} 个文件")
            report_lines.append(f"  释放空间: {results['total_size_freed']:,} 字节 ({results['total_size_freed']/1024/1024:.2f} MB)")
            report_lines.append(f"  错误数: {len(results['errors'])}")
            
            if results['deleted']:
                report_lines.append(f"\n[删除]  已删除文件:")
                for deleted in results['deleted'][:10]:  # 最多显示10个
                    filename = os.path.basename(deleted['path'])
                    report_lines.append(f"  - {filename} ({deleted['size']:,} 字节)")
                    report_lines.append(f"    原因: {deleted['reason']}")
                
                if len(results['deleted']) > 10:
                    report_lines.append(f"  ... 还有 {len(results['deleted']) - 10} 个文件未显示")
        
        # 重要保留文件
        if plan['keep']:
            report_lines.append(f"\n[存储] 重要保留文件:")
            kept_critical = [f for f in plan['keep'] if any(kw in f for kw in self.important_keywords)]
            for i, filepath in enumerate(kept_critical[:5]):  # 最多显示5个
                filename = os.path.basename(filepath)
                size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
                report_lines.append(f"  {i+1}. {filename} ({size:,} 字节)")
        
        # 建议
        report_lines.append(f"\n[建议] 建议:")
        if results and results['dry_run'] and len(plan['delete']) > 0:
            report_lines.append("  1. 运行实际清理: python scripts/cleanup_archive_files.py --execute")
        else:
            report_lines.append("  1. [成功] 清理已完成")
        
        report_lines.append("  2. 建议定期运行清理，保持archive目录整洁")
        report_lines.append("  3. 新分析报告应放在docs/reports目录下")
        
        report_lines.append("\n" + "=" * 100)
        
        return "\n".join(report_lines)
    
    def save_report(self, report: str, filename: str = None):
        """保存报告"""
        if filename is None:
            reports_dir = os.path.join(os.path.dirname(self.archive_dir), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(reports_dir, f"archive_cleanup_report_{timestamp}.md")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n[报告] 报告已保存: {filename}")
        return filename

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='清理archive目录中的过期文件和锐评文件')
    parser.add_argument('--execute', action='store_true', help='实际执行删除操作（默认是模拟运行）')
    parser.add_argument('--keep-reports', type=int, default=3, help='保留最近的分析报告数量（默认: 3）')
    parser.add_argument('--archive-dir', type=str, help='archive目录路径')
    
    args = parser.parse_args()
    
    print("[工具] ClawAI Archive目录清理工具")
    print("正在分析archive目录...")
    
    try:
        cleaner = ArchiveCleaner(args.archive_dir)
        
        # 分析文件
        analysis = cleaner.analyze_files()
        
        if analysis['total_files'] == 0:
            print("[空] archive目录中没有找到.md文件")
            return 0
        
        print(f"[统计] 分析完成: 找到 {analysis['total_files']} 个文件")
        print(f"[大小] 总大小: {analysis['total_size']:,} 字节 ({analysis['total_size']/1024/1024:.2f} MB)")
        
        # 生成清理计划
        plan = cleaner.generate_cleanup_plan(analysis, keep_recent_reports=args.keep_reports)
        
        if not plan['delete']:
            print("\n[成功] 未发现需要清理的文件，archive目录已保持整洁")
            return 0
        
        print(f"\n[计划] 清理计划:")
        print(f"  计划删除: {len(plan['delete'])} 个文件")
        print(f"  计划保留: {len(plan['keep'])} 个文件")
        
        # 执行清理
        dry_run = not args.execute
        results = cleaner.execute_cleanup(plan, dry_run=dry_run)
        
        # 生成报告
        print("\n[报告] 生成清理报告...")
        report = cleaner.generate_report(analysis, plan, results)
        print(report)
        
        # 保存报告
        report_file = cleaner.save_report(report)
        
        # 显示摘要
        if results['deleted']:
            print(f"\n[目标] 清理摘要:")
            print(f"  模式: {'模拟运行' if dry_run else '实际执行'}")
            print(f"  删除文件数: {len(results['deleted'])}")
            print(f"  释放空间: {results['total_size_freed']:,} 字节 ({results['total_size_freed']/1024/1024:.2f} MB)")
        
        if dry_run and plan['delete']:
            print(f"\n[建议] 要实际执行清理，请运行: python scripts/cleanup_archive_files.py --execute")
        
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