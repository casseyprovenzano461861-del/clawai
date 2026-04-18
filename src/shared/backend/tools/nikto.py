# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Nikto Web漏洞扫描工具（基于BaseTool的新版本）
封装nikto Web漏洞扫描功能，支持真实/模拟执行自动切换
"""

import subprocess
import json
import re
import sys
import os
import tempfile
import time
from typing import Dict, List, Any, Optional

# 导入工具基类
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.tools.base_tool import (
    BaseTool, ToolExecutionMode, ToolCategory, 
    ToolPriority, ToolExecutionResult, register_tool
)


@register_tool
class NiktoTool(BaseTool):
    """Nikto Web漏洞扫描工具类（新版本）"""
    
    def __init__(self):
        super().__init__(
            tool_name="nikto",
            command="nikto",
            description="Web服务器漏洞扫描器",
            category=ToolCategory.WEB_VULN,
            priority=ToolPriority.HIGH,
            requires_installation=True,
            fallback_to_simulated=True
        )
        
        # 常见漏洞模式
        self.vuln_patterns = [
            r'\+ (\d+:\s+.+)',  # 标准漏洞格式
            r'OSVDB-\d+:',      # OSVDB引用
            r'CVE-\d+-\d+:',    # CVE引用
        ]
        
        # 常见Web漏洞类型
        self.common_vulnerabilities = [
            ("Apache/2.4.29 版本过旧，可能存在已知漏洞", "medium"),
            ("未设置X-Content-Type-Options HTTP头", "low"),
            ("robots.txt 文件可访问，可能泄露敏感信息", "low"),
            ("HTTP TRACE 方法启用，可能用于XST攻击", "medium"),
            ("Cookie缺少HttpOnly标志", "low"),
            ("检测到可能的目录遍历漏洞", "high"),
            ("SSL/TLS 配置存在弱加密套件", "medium"),
            ("Web服务器版本信息泄露", "low"),
            ("PHP版本过旧，可能存在已知漏洞", "high"),
            ("未设置Content-Security-Policy头", "low"),
            ("检测到公开的管理后台地址", "info"),
            ("服务器返回详细的错误信息", "medium"),
            ("支持的HTTP方法过多（如PUT、DELETE）", "medium"),
            ("检测到跨站脚本（XSS）漏洞", "high"),
            ("SQL注入漏洞（可能）", "high"),
            ("检测到开放重定向漏洞", "medium")
        ]
    
    def _determine_severity(self, vuln_text: str) -> str:
        """根据漏洞描述确定严重级别"""
        text_lower = vuln_text.lower()
        
        if any(word in text_lower for word in ["critical", "remote code execution", "rce", "sql injection", "xss", "cross site", "directory traversal", "command injection"]):
            return "high"
        elif any(word in text_lower for word in ["medium", "information disclosure", "misconfiguration", "cross-site request forgery", "csrf"]):
            return "medium"
        elif any(word in text_lower for word in ["low", "informational", "header", "cookies", "banner"]):
            return "low"
        else:
            return "info"
    
    def _parse_nikto_output(self, output: str) -> Dict[str, Any]:
        """解析nikto输出，提取漏洞信息"""
        vulnerabilities = []
        lines = output.split('\n')
        
        current_vuln = None
        
        for line in lines:
            line = line.strip()
            
            # 跳过无关行
            if not line or line.startswith('-') or line.startswith('+ Nikto') or line.startswith('+ Target IP:'):
                continue
            
            # 检查是否是漏洞项
            if line.startswith('+ '):
                if current_vuln:
                    vulnerabilities.append(current_vuln)
                
                vuln_text = line[2:].strip()
                severity = self._determine_severity(vuln_text)
                
                current_vuln = {
                    "id": len(vulnerabilities) + 1,
                    "name": vuln_text[:120],  # 截断避免过长
                    "severity": severity,
                    "description": vuln_text,
                    "type": "web_vulnerability",
                    "details": []
                }
            
            # 如果是详细信息，追加到当前漏洞
            elif current_vuln and line.startswith('|'):
                info = line[1:].strip()
                current_vuln["details"].append(info)
        
        # 添加最后一个漏洞
        if current_vuln:
            vulnerabilities.append(current_vuln)
        
        return {
            "vulnerabilities": vulnerabilities,
            "vulnerability_count": len(vulnerabilities),
            "parsed_successfully": len(vulnerabilities) > 0
        }
    
    def _execute_real(self, target: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """真实执行nikto扫描"""
        if options is None:
            options = {}
        
        # 清理目标URL
        clean_target = target
        if not (target.startswith("http://") or target.startswith("https://")):
            clean_target = f"http://{target}"
        
        # 提取选项参数
        timeout = options.get("timeout", 90)  # 90秒超时（nikto内部-timeout 30）
        tuning = options.get("tuning", "x")  # 排除某些检查以避免误报
        port = options.get("port", None)
        
        try:
            # 创建临时文件存储结果
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                output_file = f.name
            
            # 构建nikto命令
            cmd = [
                self.command,
                '-h', clean_target,
                '-o', output_file,
                '-Format', 'txt',
                '-Tuning', tuning,
                '-timeout', '30',
                '-nointeractive'  # 非交互模式
            ]
            
            # 添加端口（如果指定）
            if port:
                cmd.extend(['-p', str(port)])
            
            self.logger.info(f"执行nikto命令: {' '.join(cmd[:5])}...")
            
            # 执行命令
            result = self._run_command(cmd, timeout=timeout)
            
            # 读取输出文件
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8', errors='ignore') as f:
                    file_output = f.read()
                os.unlink(output_file)
                
                raw_output = file_output
            else:
                raw_output = result.stdout
            
            # 解析结果
            parsed_results = self._parse_nikto_output(raw_output)
            
            return {
                "target": target,
                "clean_target": clean_target,
                "scan_results": parsed_results,
                "raw_output": raw_output[:2000],
                "execution_mode": "real",
                "command": ' '.join(cmd[:8]),  # 简化命令显示
                "return_code": result.returncode,
                "parsed_successfully": parsed_results.get("parsed_successfully", False)
            }
            
        except Exception as e:
            error_msg = f"nikto执行错误: {str(e)}"
            if isinstance(e, subprocess.TimeoutExpired):
                error_msg = "nikto扫描超时"
            elif isinstance(e, FileNotFoundError):
                error_msg = "未找到nikto可执行文件"
            
            return {
                "target": target,
                "clean_target": clean_target,
                "scan_results": {
                    "vulnerabilities": [],
                    "vulnerability_count": 0,
                    "error": error_msg
                },
                "execution_mode": "real",
                "raw_output": error_msg
            }
    
    def _simulate_execution(self, target: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """模拟nikto执行（当工具不可用时）"""
        import random
        
        # 清理目标URL
        clean_target = target
        if not (target.startswith("http://") or target.startswith("https://")):
            clean_target = f"http://{target}"
        
        # 随机选择3-7个漏洞
        vuln_count = random.randint(3, 7)
        selected_vulns = random.sample(self.common_vulnerabilities, vuln_count)
        
        vulnerabilities = []
        for i, (name, severity) in enumerate(selected_vulns, 1):
            vuln_details = [
                "这是模拟的漏洞数据，用于测试目的",
                f"目标: {clean_target}",
                f"漏洞类型: {severity.upper()}",
                "建议在实际环境中运行完整的nikto扫描"
            ]
            
            if random.random() > 0.7:  # 30%概率添加额外细节
                if "Apache" in name:
                    vuln_details.append("建议升级到Apache 2.4.55或更高版本")
                elif "XSS" in name:
                    vuln_details.append("建议实施输入验证和输出编码")
                elif "SQL" in name:
                    vuln_details.append("建议使用参数化查询")
            
            vulnerabilities.append({
                "id": i,
                "name": name,
                "severity": severity,
                "description": name,
                "type": "web_vulnerability",
                "details": vuln_details,
                "simulated": True
            })
        
        # 生成nikto格式的输出
        output_lines = [
            f"- Nikto v2.5.0",
            f"+ Target IP: 192.168.1.100",
            f"+ Target Hostname: {clean_target.replace('http://', '').replace('https://', '')}",
            f"+ Target Port: 80",
            f"+ Start Time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        for i, vuln in enumerate(vulnerabilities, 1):
            output_lines.append(f"+ {i}: {vuln['name']}")
            output_lines.append(f"| Severity: {vuln['severity']}")
            output_lines.append(f"| Type: {vuln['type']}")
            for detail in vuln['details'][:2]:  # 只添加前两个细节
                output_lines.append(f"| {detail}")
            output_lines.append("")
        
        output_lines.append(f"+ {len(vulnerabilities)+1}: Scan completed")
        output_lines.append(f"- End Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        raw_output = "\n".join(output_lines)
        
        return {
            "target": target,
            "clean_target": clean_target,
            "scan_results": {
                "vulnerabilities": vulnerabilities,
                "vulnerability_count": len(vulnerabilities),
                "parsed_successfully": True
            },
            "raw_output": raw_output,
            "execution_mode": "simulated",
            "simulated": True,
            "note": "这是模拟数据，实际环境中请安装nikto进行真实扫描",
            "installation_guide": """
nikto安装指南:

  Linux (Kali/Ubuntu/Debian):
    sudo apt-get update
    sudo apt-get install nikto
  
  Linux (其他发行版):
    # 从GitHub克隆
    git clone https://github.com/sullo/nikto.git
    cd nikto
    # 安装依赖（Perl）
    sudo apt-get install libnet-ssleay-perl libwhisker2-perl
  
  macOS:
    brew install nikto
  
  Docker方式:
    docker pull sullo/nikto
    docker run -it sullo/nikto -h http://example.com
  
  Windows:
    1. 安装Perl: https://www.perl.org/get.html
    2. 安装必要的Perl模块:
        ppm install LWP::Protocol::https
        ppm install Net::SSLeay
    3. 下载nikto: https://github.com/sullo/nikto
    4. 运行: perl nikto.pl -h http://example.com
"""
        }
    
    def run(self, target: str) -> Dict[str, Any]:
        """执行nikto扫描（兼容旧接口）"""
        result = self.execute(target)
        return result.output


def main():
    """命令行入口点"""
    if len(sys.argv) < 2:
        print("用法: python new_nikto.py <target_url>")
        print("示例: python new_nikto.py http://example.com")
        print("示例: python new_nikto.py https://target-site.com")
        print("选项:")
        print("  --port <port>         指定端口")
        print("  --tuning <x|a|b|c|e>  调整扫描类型 (x=排除)")
        print("  --timeout <seconds>   设置超时时间")
        print("  --json                输出完整JSON")
        sys.exit(1)
    
    target = sys.argv[1]
    
    # 解析选项
    options = {}
    
    if "--port" in sys.argv:
        try:
            port_index = sys.argv.index("--port") + 1
            if port_index < len(sys.argv):
                options["port"] = sys.argv[port_index]
        except (ValueError, IndexError):
            pass
    
    if "--tuning" in sys.argv:
        try:
            tuning_index = sys.argv.index("--tuning") + 1
            if tuning_index < len(sys.argv):
                tuning_val = sys.argv[tuning_index]
                if tuning_val in ['x', 'a', 'b', 'c', 'e']:
                    options["tuning"] = tuning_val
        except (ValueError, IndexError):
            pass
    
    if "--timeout" in sys.argv:
        try:
            timeout_index = sys.argv.index("--timeout") + 1
            if timeout_index < len(sys.argv):
                timeout_val = int(sys.argv[timeout_index])
                if 10 <= timeout_val <= 3600:
                    options["timeout"] = timeout_val
        except (ValueError, IndexError):
            pass
    
    tool = NiktoTool()
    
    try:
        # 显示工具状态
        status = tool.get_status()
        print(f"工具状态: {'✅ 可用' if status['available'] else '❌ 不可用'}")
        if status['version']:
            print(f"版本信息: {status['version']}")
        
        if not status['available']:
            print("\n⚠️  工具不可用，将使用模拟模式")
            print("如需真实扫描，请安装nikto")
        
        # 执行扫描
        result = tool.execute(target, options)
        
        # 输出结果摘要
        print(f"\n扫描目标: {result.output['target']}")
        print(f"执行模式: {result.output['execution_mode']}")
        
        if result.output.get('simulated'):
            print("⚠️  注意: 这是模拟数据")
        
        scan_results = result.output.get('scan_results', {})
        
        # 显示漏洞统计
        vuln_count = scan_results.get('vulnerability_count', 0)
        print(f"发现的漏洞数量: {vuln_count}")
        
        # 按严重程度分类
        if vuln_count > 0:
            vulnerabilities = scan_results.get('vulnerabilities', [])
            severity_counts = {"high": 0, "medium": 0, "low": 0, "info": 0}
            
            for vuln in vulnerabilities:
                severity = vuln.get('severity', 'info').lower()
                if severity in severity_counts:
                    severity_counts[severity] += 1
            
            print(f"\n漏洞严重程度分布:")
            for severity, count in severity_counts.items():
                if count > 0:
                    print(f"  {severity.upper():6s}: {count:2d}")
        
        # 显示发现的漏洞（前5个）
        vulnerabilities = scan_results.get('vulnerabilities', [])
        if vulnerabilities:
            print(f"\n发现的漏洞（前{min(5, len(vulnerabilities))}个）:")
            for i, vuln in enumerate(vulnerabilities[:5], 1):
                severity = vuln.get('severity', 'info')
                severity_icon = "🔴" if severity == "high" else "🟡" if severity == "medium" else "🔵"
                print(f"  {severity_icon} {i}. {vuln.get('name', '未知漏洞')}")
                details = vuln.get('details', [])
                if details and len(details) > 0:
                    print(f"     详情: {details[0][:60]}...")
        
        # 显示安装指南（如果使用模拟模式）
        if result.output.get('simulated') and result.output.get('installation_guide'):
            print(f"\n安装指南: 请查看工具的installation_guide字段")
        
        # 可选的JSON输出
        if '--json' in sys.argv:
            print("\n完整JSON输出:")
            print(json.dumps(result.output, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"扫描失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()