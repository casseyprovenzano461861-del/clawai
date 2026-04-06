# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Nuclei漏洞扫描工具模块
封装nuclei扫描功能，提供简单的漏洞扫描接口
"""

import subprocess
import json
import sys


class NucleiTool:
    """Nuclei漏洞扫描工具类"""
    
    def __init__(self, nuclei_path: str = r"C:\Tools\nuclei\nuclei.exe"):
        self.nuclei_path = nuclei_path
    
    def _run_nuclei_command(self, target: str):
        """运行nuclei命令"""
        try:
            cmd = [
                self.nuclei_path,
                '-u', target,
                '-json',
                '-silent',
                '-t', 'cves/',
                '--severity', 'low,medium,high,critical'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                encoding='utf-8',
                errors='ignore'
            )
            
            # 只要有stdout输出就正常解析
            if not result.stdout:
                raise RuntimeError("nuclei命令无输出")
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("nuclei扫描超时")
        except FileNotFoundError:
            raise RuntimeError("未找到nuclei可执行文件")
        except Exception as e:
            raise RuntimeError(f"执行错误: {str(e)}")
    
    def _parse_nuclei_output(self, output: str):
        """解析nuclei输出，提取漏洞信息"""
        vulnerabilities = []
        
        lines = output.strip().split('\n')
        
        for line in lines:
            if not line.strip():
                continue
                
            try:
                data = json.loads(line)
                name = data.get('info', {}).get('name', 'Unknown')
                severity = data.get('info', {}).get('severity', 'unknown')
                
                vulnerabilities.append({
                    "name": name,
                    "severity": severity.lower()
                })
                
            except (json.JSONDecodeError, Exception):
                continue
        return vulnerabilities
    
    def run(self, target: str):
        """执行nuclei扫描"""
        if not target or not isinstance(target, str):
            raise ValueError("目标必须是有效的字符串")
        
        target = target.strip()
        if not target:
            raise ValueError("目标不能为空")
        
        if not (target.startswith('http://') or target.startswith('https://')):
            raise ValueError("目标必须是有效的URL")
        
        try:
            output = self._run_nuclei_command(target)
            vulnerabilities = self._parse_nuclei_output(output)
            
            return {
                "target": target,
                "vulnerabilities": vulnerabilities
            }
            
        except Exception as e:
            return {
                "target": target,
                "vulnerabilities": [],
                "error": str(e)
            }


def main():
    """命令行入口点"""
    if len(sys.argv) != 2:
        print("用法: python  <target_url> - nuclei.py:108")
        print("示例: python  http://example.com - nuclei.py:109")
        print("示例: python  https://127.0.0.1 - nuclei.py:110")
        sys.exit(1)
    
    target = sys.argv[1]
    tool = NucleiTool()
    
    try:
        result = tool.run(target)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"扫描失败: {str(e)} - nuclei.py:120")
        sys.exit(1)


if __name__ == "__main__":
    main()