# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
工具验证器
检查所有工具的实现状态和可用性
"""

import os
import sys
import importlib
import json
from typing import Dict, List, Any

class ToolValidator:
    """工具验证器类"""
    
    def __init__(self, tools_dir: str = None):
        if tools_dir is None:
            tools_dir = os.path.dirname(os.path.abspath(__file__))
        self.tools_dir = tools_dir
        
    def discover_tool_files(self) -> List[str]:
        """发现所有工具文件"""
        tool_files = []
        for filename in os.listdir(self.tools_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                tool_files.append(filename)
        return sorted(tool_files)
    
    def analyze_tool_implementation(self, filename: str) -> Dict[str, Any]:
        """分析单个工具的实现状态"""
        module_name = filename[:-3]  # 移除.py
        filepath = os.path.join(self.tools_dir, filename)
        
        result = {
            "filename": filename,
            "module_name": module_name,
            "status": "unknown",
            "has_class": False,
            "class_name": None,
            "has_run_method": False,
            "is_simulated_only": False,
            "size_bytes": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
            "lines": 0
        }
        
        try:
            # 读取文件内容
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result["lines"] = len(content.split('\n'))
            
            # 检查是否包含模拟实现的标志
            simulated_keywords = ["simulated", "模拟", "fake", "placeholder", "_simulate_"]
            result["is_simulated_only"] = any(keyword in content.lower() for keyword in simulated_keywords)
            
            # 检查是否包含正确的类定义
            import re
            class_pattern = r'class\s+(\w+Tool)\s*:'
            match = re.search(class_pattern, content)
            if match:
                result["has_class"] = True
                result["class_name"] = match.group(1)
                
                # 检查是否包含run方法
                if "def run" in content or "def execute" in content:
                    result["has_run_method"] = True
                    result["status"] = "implemented"
                else:
                    result["status"] = "no_run_method"
            else:
                result["status"] = "no_tool_class"
            
            # 特别标记通用模板文件
            if "通用工具" in content or "模拟工具执行" in content:
                result["status"] = "generic_template"
                result["is_simulated_only"] = True
            
        except Exception as e:
            result["status"] = f"error: {str(e)}"
        
        return result
    
    def validate_all_tools(self) -> Dict[str, Any]:
        """验证所有工具"""
        tool_files = self.discover_tool_files()
        results = []
        
        print(f"发现 {len(tool_files)} 个工具文件")
        
        for filename in tool_files:
            print(f"分析: {filename}...", end="")
            analysis = self.analyze_tool_implementation(filename)
            results.append(analysis)
            
            status_symbol = "✓" if analysis["status"] == "implemented" else "⚠"
            print(f" {status_symbol} ({analysis['status']})")
        
        # 统计结果
        stats = {
            "total_files": len(tool_files),
            "implemented": len([r for r in results if r["status"] == "implemented"]),
            "no_run_method": len([r for r in results if r["status"] == "no_run_method"]),
            "no_tool_class": len([r for r in results if r["status"] == "no_tool_class"]),
            "generic_template": len([r for r in results if r["status"] == "generic_template"]),
            "error": len([r for r in results if "error" in r["status"]]),
            "simulated_only": len([r for r in results if r["is_simulated_only"]]),
            "total_lines": sum(r["lines"] for r in results)
        }
        
        return {
            "stats": stats,
            "details": results
        }
    
    def generate_report(self) -> str:
        """生成验证报告"""
        validation = self.validate_all_tools()
        stats = validation["stats"]
        details = validation["details"]
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("ClawAI 工具实现状态报告")
        report_lines.append("=" * 80)
        
        report_lines.append(f"\n统计信息:")
        report_lines.append(f"  文件总数: {stats['total_files']}")
        report_lines.append(f"  已实现: {stats['implemented']}")
        report_lines.append(f"  缺少run方法: {stats['no_run_method']}")
        report_lines.append(f"  缺少工具类: {stats['no_tool_class']}")
        report_lines.append(f"  通用模板: {stats['generic_template']}")
        report_lines.append(f"  仅模拟实现: {stats['simulated_only']}")
        report_lines.append(f"  错误文件: {stats['error']}")
        report_lines.append(f"  总代码行数: {stats['total_lines']:,}")
        
        # 分类展示
        report_lines.append(f"\n详细分析:")
        
        categories = {
            "implemented": "完整实现",
            "generic_template": "通用模板",
            "no_run_method": "缺少run方法", 
            "no_tool_class": "缺少工具类",
            "error": "解析错误"
        }
        
        for status, description in categories.items():
            category_tools = [r for r in details if r["status"] == status or ("error" in status and "error" in r["status"])]
            if category_tools:
                report_lines.append(f"\n{description} ({len(category_tools)}个):")
                for tool in category_tools[:10]:  # 最多显示10个
                    simulated_mark = " [仅模拟]" if tool["is_simulated_only"] else ""
                    report_lines.append(f"  - {tool['filename']}{simulated_mark}")
                if len(category_tools) > 10:
                    report_lines.append(f"  ... 还有 {len(category_tools)-10} 个")
        
        # 建议
        report_lines.append(f"\n建议:")
        if stats["implemented"] < 30:
            report_lines.append(f"  ❌ 当前只有 {stats['implemented']} 个工具完整实现，未达到目标数量 ≥30 个")
            report_lines.append(f"  ✅ 需要至少修复 {30-stats['implemented']} 个工具")
        else:
            report_lines.append(f"  ✅ 已有 {stats['implemented']} 个工具完整实现，满足工具数量要求")
        
        if stats["generic_template"] > 0:
            report_lines.append(f"  ⚠ 有 {stats['generic_template']} 个通用模板文件需要具体实现")
        
        if stats["simulated_only"] > 5:
            report_lines.append(f"  ⚠ 有 {stats['simulated_only']} 个工具仅支持模拟模式，建议增加真实执行功能")
        
        report_lines.append(f"\n下一步:")
        report_lines.append(f"  1. 优先实现缺少run方法的工具")
        report_lines.append(f"  2. 将通用模板文件替换为具体实现")
        report_lines.append(f"  3. 为仅模拟的工具添加真实执行能力")
        
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def get_priority_fixes(self) -> List[Dict[str, Any]]:
        """获取需要优先修复的工具列表"""
        validation = self.validate_all_tools()
        details = validation["details"]
        
        priority_tools = []
        
        for tool in details:
            priority_score = 0
            reason = []
            
            if tool["status"] == "generic_template":
                priority_score += 10
                reason.append("通用模板需要重写")
            
            if tool["status"] == "no_run_method":
                priority_score += 8
                reason.append("缺少run方法")
                
            if tool["status"] == "no_tool_class":
                priority_score += 8
                reason.append("缺少工具类")
                
            if tool["is_simulated_only"]:
                priority_score += 5
                reason.append("仅模拟实现")
                
            # 文件大小太小可能表示实现不完整
            if tool["size_bytes"] < 1000:
                priority_score += 3
                reason.append("文件太小可能不完整")
            
            if priority_score > 0:
                priority_tools.append({
                    "filename": tool["filename"],
                    "priority_score": priority_score,
                    "reasons": reason,
                    "current_status": tool["status"]
                })
        
        # 按优先级排序
        priority_tools.sort(key=lambda x: x["priority_score"], reverse=True)
        return priority_tools[:20]  # 返回前20个需要修复的


def main():
    """主函数"""
    validator = ToolValidator()
    
    print("\n正在验证工具实现状态...")
    
    # 生成报告
    report = validator.generate_report()
    print(report)
    
    # 显示需要优先修复的工具
    priority_fixes = validator.get_priority_fixes()
    if priority_fixes:
        print(f"\n需要优先修复的工具 (前{len(priority_fixes)}个):")
        print("-" * 60)
        for i, tool in enumerate(priority_fixes, 1):
            print(f"{i:2d}. {tool['filename']} (优先级: {tool['priority_score']})")
            print(f"    状态: {tool['current_status']}")
            print(f"    原因: {', '.join(tool['reasons'])}")
    
    # 保存报告到文件
    report_file = os.path.join(os.path.dirname(__file__), "tool_validation_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n报告已保存到: {report_file}")
    
    # 返回状态码
    validation = validator.validate_all_tools()
    if validation["stats"]["implemented"] >= 30:
        print("\n✅ 工具数量满足工具数量要求!")
        return 0
    else:
        print(f"\n❌ 工具数量不足: {validation['stats']['implemented']}/30")
        return 1


if __name__ == "__main__":
    sys.exit(main())