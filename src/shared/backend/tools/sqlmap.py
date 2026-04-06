# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
SQLMap SQL注入自动化利用工具模块
封装sqlmap功能，提供SQL注入检测和利用接口
"""

import subprocess
import json
import sys
import re
import os


class SQLMapTool:
    """SQLMap SQL注入工具类"""
    
    def __init__(self, sqlmap_path: str = "sqlmap"):
        self.sqlmap_path = sqlmap_path
        
    def _run_sqlmap_command(self, target: str, options: dict = None):
        """运行sqlmap命令"""
        try:
            cmd = [
                self.sqlmap_path,
                '-u', target,
                '--batch',              # 非交互模式
                '--level', '2',         # 测试级别
                '--risk', '1',          # 风险级别
                '--threads', '5',       # 线程数
                '--timeout', '30',      # 超时时间
                '--technique', 'BEUST', # 测试技术
                '--output-dir', '/tmp/sqlmap_output',
                '--forms',              # 自动测试表单
                '--smart',              # 智能模式
            ]
            
            if options:
                if options.get('dbs'):
                    cmd.append('--dbs')
                if options.get('tables'):
                    cmd.extend(['--tables', '-D', options.get('database', '')])
                if options.get('dump'):
                    cmd.append('--dump')
                if options.get('cookie'):
                    cmd.extend(['--cookie', options['cookie']])
                if options.get('data'):
                    cmd.extend(['--data', options['data']])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                encoding='utf-8',
                errors='ignore'
            )
            
            return result.stdout + result.stderr
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("sqlmap扫描超时")
        except FileNotFoundError:
            raise RuntimeError("未找到sqlmap可执行文件，请确保已安装sqlmap")
        except Exception as e:
            raise RuntimeError(f"执行错误: {str(e)}")
    
    def _parse_output(self, output: str):
        """解析sqlmap输出"""
        result = {
            "vulnerable": False,
            "injection_type": [],
            "dbms": "",
            "databases": [],
            "tables": [],
            "payloads": []
        }
        
        # 检测是否存在注入
        if "is vulnerable" in output or "injectable" in output.lower():
            result["vulnerable"] = True
        
        # 提取注入类型
        injection_patterns = [
            r"Type: (.*?)(?:\n|$)",
            r"(boolean-based blind)",
            r"(time-based blind)",
            r"(error-based)",
            r"(UNION query)",
            r"(stacked queries)"
        ]
        for pattern in injection_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            for match in matches:
                if match and match not in result["injection_type"]:
                    result["injection_type"].append(match)
        
        # 提取数据库类型
        dbms_match = re.search(r"back-end DBMS: (.*?)(?:\n|$)", output)
        if dbms_match:
            result["dbms"] = dbms_match.group(1).strip()
        
        # 提取数据库列表
        db_matches = re.findall(r"\[\*\] (\w+)", output)
        if db_matches:
            result["databases"] = list(set(db_matches))
        
        # 提取payload示例
        payload_match = re.search(r"Payload: (.*?)(?:\n|$)", output)
        if payload_match:
            result["payloads"].append(payload_match.group(1).strip())
        
        return result
    
    def run(self, target: str, options: dict = None):
        """执行sqlmap扫描"""
        if not target or not isinstance(target, str):
            raise ValueError("目标必须是有效的URL字符串")
        
        target = target.strip()
        if not target:
            raise ValueError("目标不能为空")
        
        # 确保目标是完整URL
        if not (target.startswith('http://') or target.startswith('https://')):
            target = f"http://{target}"
        
        try:
            output = self._run_sqlmap_command(target, options)
            result = self._parse_output(output)
            
            return {
                "target": target,
                "tool": "sqlmap",
                "result": result,
                "raw_output": output[:2000] if len(output) > 2000 else output
            }
            
        except Exception as e:
            return {
                "target": target,
                "tool": "sqlmap",
                "result": {
                    "vulnerable": False,
                    "injection_type": [],
                    "dbms": "",
                    "databases": [],
                    "tables": [],
                    "payloads": []
                },
                "error": str(e)
            }


def main():
    """命令行入口点"""
    if len(sys.argv) < 2:
        print("用法: python sqlmap.py <target_url>")
        print("示例: python sqlmap.py 'http://example.com/page.php?id=1'")
        sys.exit(1)
    
    target = sys.argv[1]
    tool = SQLMapTool()
    
    try:
        result = tool.run(target)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"扫描失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
