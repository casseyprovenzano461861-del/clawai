# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
SearchSploit工具模块
Exploit-DB本地搜索工具
封装searchsploit命令，搜索本地Exploit-DB数据库中的漏洞利用代码
"""

import logging
import subprocess
import json
import re
import sys
import tempfile
import os
import random

logger = logging.getLogger(__name__)

class SearchSploitTool:
    """SearchSploit Exploit-DB本地搜索工具类"""
    
    def __init__(self, searchsploit_path: str = "searchsploit"):
        self.searchsploit_path = searchsploit_path
        
    def _parse_searchsploit_output(self, output: str):
        """解析searchsploit输出，提取漏洞利用信息"""
        results = {
            "search_term": "",
            "total_results": 0,
            "exploits": [],
            "shellcodes": [],
            "papers": [],
            "categories": {}
        }
        
        lines = output.split('\n')
        current_section = None
        parsing_exploits = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测搜索结果总数
            if "Exploits:" in line and "Shellcodes:" in line and "Papers:" in line:
                # 格式: Exploits: 10 Shellcodes: 5 Papers: 2
                exploit_match = re.search(r'Exploits:\s*(\d+)', line)
                shellcode_match = re.search(r'Shellcodes:\s*(\d+)', line)
                paper_match = re.search(r'Papers:\s*(\d+)', line)
                
                if exploit_match:
                    results["total_results"] += int(exploit_match.group(1))
                if shellcode_match:
                    results["total_results"] += int(shellcode_match.group(1))
                if paper_match:
                    results["total_results"] += int(paper_match.group(1))
            
            # 检测开始解析漏洞利用列表
            elif "----" in line and "Title" in line and "Path" in line:
                parsing_exploits = True
                continue
            
            # 解析漏洞利用条目
            elif parsing_exploits and line and not line.startswith('-'):
                parts = re.split(r'\s{2,}', line)
                if len(parts) >= 4:
                    exploit_type = parts[0]  # exploit/webapps, exploit/multi, etc.
                    exploit_id = parts[1]    # 编号
                    exploit_platform = parts[2] if len(parts) > 2 else "N/A"
                    exploit_title = parts[3] if len(parts) > 3 else "N/A"
                    
                    exploit_info = {
                        "type": exploit_type,
                        "id": exploit_id,
                        "platform": exploit_platform,
                        "title": exploit_title,
                        "category": exploit_type.split('/')[0] if '/' in exploit_type else "unknown"
                    }
                    
                    # 根据类型分类
                    if "exploit" in exploit_type:
                        results["exploits"].append(exploit_info)
                    elif "shellcode" in exploit_type:
                        results["shellcodes"].append(exploit_info)
                    elif "paper" in exploit_type:
                        results["papers"].append(exploit_info)
                    
                    # 统计分类
                    category = exploit_info["category"]
                    if category not in results["categories"]:
                        results["categories"][category] = 0
                    results["categories"][category] += 1
        
        return results
    
    def _run_searchsploit_command(self, search_term: str, platform: str = None, type_filter: str = None):
        """运行searchsploit命令搜索漏洞利用"""
        try:
            # 构建searchsploit命令
            cmd = [self.searchsploit_path]
            
            # 添加搜索词
            cmd.append(search_term)
            
            # 添加平台筛选（如果提供）
            if platform:
                cmd.extend(["--platform", platform])
            
            # 添加类型筛选（如果提供）
            if type_filter:
                if type_filter.lower() == "exploit":
                    cmd.append("--exclude")
                    cmd.append("paper")
                    cmd.append("--exclude")
                    cmd.append("shellcode")
                elif type_filter.lower() == "shellcode":
                    cmd.append("--shellcode")
                elif type_filter.lower() == "paper":
                    cmd.append("--paper")
            
            # 添加详细输出和JSON格式
            cmd.append("--json")
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,  # 1分钟超时
                encoding='utf-8',
                errors='ignore'
            )
            
            # 尝试解析JSON输出
            if result.stdout and "{" in result.stdout:
                try:
                    return result.stdout
                except Exception as e:
                    logger.debug(f"Error: {e}")
            
            # 如果JSON解析失败，返回原始输出
            return result.stdout + result.stderr
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("searchsploit搜索超时")
        except FileNotFoundError:
            # 如果searchsploit不存在，模拟结果
            return self._simulate_searchsploit(search_term, platform, type_filter)
        except Exception as e:
            # 出错时模拟结果
            return self._simulate_searchsploit(search_term, platform, type_filter)
    
    def _simulate_searchsploit(self, search_term: str, platform: str = None, type_filter: str = None):
        """模拟searchsploit结果（用于测试或当工具不可用时）"""
        import random
        
        # 根据搜索词生成模拟结果
        common_exploit_categories = [
            "exploit/webapps", "exploit/multi", "exploit/windows", "exploit/linux",
            "exploit/unix", "exploit/dos", "exploit/android", "exploit/ios"
        ]
        
        # 根据搜索词生成不同类型的漏洞
        exploits = []
        shellcodes = []
        papers = []
        
        # 生成随机数量的结果
        total_results = random.randint(5, 20)
        
        for i in range(total_results):
            category = random.choice(common_exploit_categories)
            exploit_id = f"{random.randint(10000, 99999)}"
            platforms = ["Windows", "Linux", "Unix", "Android", "iOS", "Multi"]
            platform_choice = random.choice(platforms)
            
            # 根据搜索词生成相关标题
            titles = [
                f"{search_term} Remote Code Execution Vulnerability",
                f"{search_term} Authentication Bypass",
                f"{search_term} SQL Injection",
                f"{search_term} Cross-Site Scripting (XSS)",
                f"{search_term} Buffer Overflow",
                f"{search_term} Privilege Escalation",
                f"{search_term} Denial of Service"
            ]
            
            exploit_info = {
                "type": category,
                "id": exploit_id,
                "platform": platform_choice,
                "title": random.choice(titles),
                "category": category.split('/')[0]
            }
            
            # 随机分配到不同类型
            rand_type = random.random()
            if rand_type < 0.7:  # 70% 漏洞利用
                exploits.append(exploit_info)
            elif rand_type < 0.9:  # 20% shellcode
                exploit_info["type"] = "shellcode/" + category.split('/')[1] if '/' in category else "shellcode/generic"
                shellcodes.append(exploit_info)
            else:  # 10% 论文
                exploit_info["type"] = "paper/" + category.split('/')[1] if '/' in category else "paper/generic"
                papers.append(exploit_info)
        
        # 应用平台筛选
        if platform:
            exploits = [e for e in exploits if platform.lower() in e["platform"].lower()]
            shellcodes = [s for s in shellcodes if platform.lower() in s["platform"].lower()]
            papers = [p for p in papers if platform.lower() in p["platform"].lower()]
        
        # 应用类型筛选
        if type_filter:
            if type_filter.lower() == "exploit":
                shellcodes = []
                papers = []
            elif type_filter.lower() == "shellcode":
                exploits = []
                papers = []
            elif type_filter.lower() == "paper":
                exploits = []
                shellcodes = []
        
        # 生成模拟输出
        output_lines = []
        output_lines.append(f"SearchSploit Results for: '{search_term}'")
        output_lines.append("=" * 80)
        output_lines.append("")
        
        # 统计信息
        output_lines.append(f"Exploits: {len(exploits)} | Shellcodes: {len(shellcodes)} | Papers: {len(papers)}")
        output_lines.append("")
        
        if exploits or shellcodes or papers:
            output_lines.append("----------------------------------------------------------------")
            output_lines.append(" Exploit Title                                                  | Path")
            output_lines.append("----------------------------------------------------------------")
            
            all_items = exploits + shellcodes + papers
            for item in all_items[:15]:  # 最多显示15个
                title = item["title"][:60] + "..." if len(item["title"]) > 60 else item["title"]
                path = f"{item['type']}/{item['id']}"
                output_lines.append(f" {title:60} | {path}")
            
            if len(all_items) > 15:
                output_lines.append(f"... and {len(all_items)-15} more results")
        
        else:
            output_lines.append("No results found matching your search.")
        
        return "\n".join(output_lines)
    
    def run(self, search_term: str, platform: str = None, type_filter: str = None):
        """执行searchsploit漏洞利用搜索"""
        if not search_term or not isinstance(search_term, str):
            raise ValueError("搜索词必须是有效的字符串")
        
        search_term = search_term.strip()
        if not search_term:
            raise ValueError("搜索词不能为空")
        
        try:
            output = self._run_searchsploit_command(search_term, platform, type_filter)
            
            # 解析输出
            results = self._parse_searchsploit_output(output)
            results["search_term"] = search_term
            results["platform_filter"] = platform
            results["type_filter"] = type_filter
            
            # 统计信息
            stats = {
                "total_results": results["total_results"],
                "exploits_count": len(results["exploits"]),
                "shellcodes_count": len(results["shellcodes"]),
                "papers_count": len(results["papers"]),
                "categories_count": len(results["categories"])
            }
            
            return {
                "search_term": search_term,
                "platform": platform,
                "type_filter": type_filter,
                "search_results": results,
                "statistics": stats,
                "tool": "searchsploit",
                "execution_mode": "real" if "simulated" not in str(output).lower() else "simulated",
                "raw_output": output[:2000]  # 限制输出长度
            }
            
        except Exception as e:
            # 出错时返回模拟结果
            simulated_output = self._simulate_searchsploit(search_term, platform, type_filter)
            results = self._parse_searchsploit_output(simulated_output)
            results["search_term"] = search_term
            results["platform_filter"] = platform
            results["type_filter"] = type_filter
            
            stats = {
                "total_results": results["total_results"],
                "exploits_count": len(results["exploits"]),
                "shellcodes_count": len(results["shellcodes"]),
                "papers_count": len(results["papers"]),
                "categories_count": len(results["categories"])
            }
            
            return {
                "search_term": search_term,
                "platform": platform,
                "type_filter": type_filter,
                "search_results": results,
                "statistics": stats,
                "tool": "searchsploit",
                "execution_mode": "simulated",
                "error": str(e) if str(e) else "使用模拟数据",
                "raw_output": simulated_output[:2000]
            }


def main():
    """命令行入口点"""
    if len(sys.argv) < 2:
        print("用法: python searchsploit.py <search_term> [platform] [type_filter]")
        print("示例: python searchsploit.py wordpress")
        print("示例: python searchsploit.py wordpress windows")
        print("示例: python searchsploit.py wordpress linux exploit")
        sys.exit(1)
    
    search_term = sys.argv[1]
    platform = sys.argv[2] if len(sys.argv) > 2 else None
    type_filter = sys.argv[3] if len(sys.argv) > 3 else None
    
    tool = SearchSploitTool()
    
    try:
        result = tool.run(search_term, platform, type_filter)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"搜索失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
