# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Masscan扫描工具模块（基于BaseTool的新版本）
封装masscan高速端口扫描功能
"""

import logging
import subprocess
import json
import re
import sys
import os
import tempfile
from typing import Dict, List, Any, Optional

# 导入工具基类
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.tools.base_tool import (
    BaseTool, ToolExecutionMode, ToolCategory,
    ToolPriority, ToolExecutionResult, register_tool
)

logger = logging.getLogger(__name__)


@register_tool
class MasscanTool(BaseTool):
    """Masscan扫描工具类（新版本）"""
    
    def __init__(self):
        super().__init__(
            tool_name="masscan",
            command="masscan",
            description="高速端口扫描器",
            category=ToolCategory.NETWORK_SCAN,
            priority=ToolPriority.HIGH,
            requires_installation=True,
            fallback_to_simulated=True
        )
        
        # 常用端口列表
        self.common_ports = [
            21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 
            443, 445, 993, 995, 1433, 1521, 3306, 3389, 5432, 
            5900, 6379, 8080, 8443, 27017
        ]
        
        # 服务映射
        self.service_map = {
            21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns",
            80: "http", 110: "pop3", 111: "rpcbind", 135: "msrpc",
            139: "netbios-ssn", 143: "imap", 443: "https", 445: "microsoft-ds",
            993: "imaps", 995: "pop3s", 1433: "ms-sql-s", 1521: "oracle",
            3306: "mysql", 3389: "ms-wbt-server", 5432: "postgresql",
            5900: "vnc", 6379: "redis", 8080: "http-proxy", 8443: "https-alt",
            27017: "mongodb"
        }
    
    def _guess_service(self, port: int) -> str:
        """根据端口猜测服务"""
        return self.service_map.get(port, "unknown")
    
    def _parse_masscan_output(self, output: str) -> List[Dict[str, Any]]:
        """解析masscan输出，提取端口信息"""
        ports = []
        
        # 尝试解析JSON输出
        try:
            data = json.loads(output)
            if isinstance(data, list):
                for item in data:
                    if 'ports' in item:
                        for port_info in item['ports']:
                            if port_info.get('status') == 'open':
                                port_num = port_info.get('port', 0)
                                ports.append({
                                    "port": port_num,
                                    "service": self._guess_service(port_num),
                                    "state": "open",
                                    "proto": port_info.get('proto', 'tcp'),
                                    "ip": item.get('ip', '')
                                })
            return ports
        except json.JSONDecodeError:
            pass
        
        # 如果JSON解析失败，尝试解析文本输出
        port_pattern = r'Discovered open port (\d+)/tcp on (.+)'
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            match = re.match(port_pattern, line)
            if match:
                port_num = int(match.group(1))
                ip = match.group(2)
                
                ports.append({
                    "port": port_num,
                    "service": self._guess_service(port_num),
                    "state": "open",
                    "proto": "tcp",
                    "ip": ip
                })
        
        return ports
    
    def _execute_real(self, target: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """真实执行masscan扫描"""
        if options is None:
            options = {}
        
        # 提取选项参数
        ports = options.get("ports", None)
        if not ports:
            ports_list = self.common_ports
            ports = ",".join(str(p) for p in ports_list)
        
        rate = options.get("rate", 1000)  # 扫描速率（包/秒）
        timeout = options.get("timeout", 300)  # 5分钟超时
        
        # 清理目标格式
        clean_target = target
        if target.startswith("http://"):
            clean_target = target.replace("http://", "")
        elif target.startswith("https://"):
            clean_target = target.replace("https://", "")
        
        # 创建临时文件存储JSON结果
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                temp_file = f.name
            
            # 构建masscan命令
            cmd = [
                self.command,
                clean_target,
                '-p', ports,
                '--rate', str(rate),
                '--open-only',
                '-oJ', temp_file,
                '--max-retries', '1'
            ]
            
            # 执行命令
            result = self._run_command(cmd, timeout=timeout)
            
            # 读取JSON输出
            json_output = ""
            if os.path.exists(temp_file):
                with open(temp_file, 'r', encoding='utf-8') as f:
                    json_output = f.read()
            
            # 解析结果
            ports_found = self._parse_masscan_output(json_output if json_output else result.stdout)
            
            return {
                "target": target,
                "clean_target": clean_target,
                "ports": ports_found,
                "total_open_ports": len(ports_found),
                "raw_output": json_output[:1000] if json_output else result.stdout[:1000],
                "execution_mode": "real",
                "command": " ".join(cmd),
                "scan_rate": rate
            }
            
        except Exception as e:
            error_msg = f"masscan执行错误: {str(e)}"
            if isinstance(e, subprocess.TimeoutExpired):
                error_msg = "masscan扫描超时"
            elif isinstance(e, FileNotFoundError):
                error_msg = "未找到masscan可执行文件"
            
            return {
                "target": target,
                "clean_target": clean_target,
                "ports": [],
                "error": error_msg,
                "execution_mode": "real",
                "raw_output": error_msg
            }
        
        finally:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.debug(f"Error: {e}")
    
    def _simulate_execution(self, target: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """模拟masscan执行（当工具不可用时）"""
        import random
        
        # 清理目标格式
        clean_target = target
        if target.startswith("http://"):
            clean_target = target.replace("http://", "")
        elif target.startswith("https://"):
            clean_target = target.replace("https://", "")
        
        # 模拟开放端口
        simulated_ports = []
        
        # 随机选择2-5个端口作为开放端口
        open_count = random.randint(2, 5)
        open_ports = random.sample(self.common_ports, min(open_count, len(self.common_ports)))
        
        for port in sorted(open_ports):
            service = self._guess_service(port)
            simulated_ports.append({
                "port": port,
                "service": service,
                "state": "open",
                "proto": "tcp",
                "ip": clean_target,
                "simulated": True
            })
        
        # 生成模拟的JSON输出
        simulated_data = [
            {
                "ip": clean_target,
                "timestamp": "2024-01-01 12:00:00",
                "ports": [
                    {
                        "port": port_info["port"],
                        "proto": "tcp",
                        "status": "open",
                        "reason": "syn-ack",
                        "ttl": 64
                    }
                    for port_info in simulated_ports
                ]
            }
        ]
        
        simulated_json = json.dumps(simulated_data, indent=2)
        
        return {
            "target": target,
            "clean_target": clean_target,
            "ports": simulated_ports,
            "total_open_ports": len(simulated_ports),
            "raw_output": simulated_json,
            "execution_mode": "simulated",
            "simulated": True,
            "note": "这是模拟数据，实际环境中请安装masscan进行真实扫描",
            "installation_guide": """
masscan安装指南:
  Linux (源码编译):
    sudo apt-get install git gcc make libpcap-dev
    git clone https://github.com/robertdavidgraham/masscan
    cd masscan
    make
    sudo make install
    
  Windows:
    1. 下载: https://github.com/robertdavidgraham/masscan/releases
    2. 解压并添加路径到系统PATH
    
  注意: masscan需要root权限或CAP_NET_RAW能力
"""
        }
    
    def run(self, target: str) -> Dict[str, Any]:
        """执行masscan扫描（兼容旧接口）"""
        result = self.execute(target)
        return result.output


def main():
    """命令行入口点"""
    if len(sys.argv) != 2:
        print("用法: python new_masscan.py <target>")
        print("示例: python new_masscan.py example.com")
        print("示例: python new_masscan.py 192.168.1.0/24")
        sys.exit(1)
    
    target = sys.argv[1]
    tool = MasscanTool()
    
    try:
        # 显示工具状态
        status = tool.get_status()
        print(f"工具状态: {'✅ 可用' if status['available'] else '❌ 不可用'}")
        if status['version']:
            print(f"版本信息: {status['version']}")
        
        if not status['available']:
            print("\n⚠️  工具不可用，将使用模拟模式")
            print("如需真实扫描，请安装masscan")
        
        # 执行扫描
        result = tool.run(target)
        
        # 输出结果
        print(f"\n扫描目标: {result['target']}")
        print(f"执行模式: {result['execution_mode']}")
        
        if result.get('simulated'):
            print("⚠️  注意: 这是模拟数据")
        
        if result.get('error'):
            print(f"错误: {result['error']}")
        
        if result['ports']:
            print(f"\n发现 {len(result['ports'])} 个开放端口:")
            print("-" * 70)
            print(f"{'端口':<8} {'服务':<15} {'IP地址':<20} {'状态':<10}")
            print("-" * 70)
            
            for port_info in result['ports']:
                port = port_info.get('port', '')
                service = port_info.get('service', '')
                ip = port_info.get('ip', '')
                state = port_info.get('state', '')
                simulated = " (模拟)" if port_info.get('simulated') else ""
                print(f"{port:<8} {service:<15} {ip:<20} {state:<10}{simulated}")
        else:
            print("\n未发现开放端口")
        
        # 显示扫描统计
        if result.get('scan_rate'):
            print(f"\n扫描速率: {result['scan_rate']} 包/秒")
        
        # 可选的JSON输出
        if '--json' in sys.argv:
            print("\n完整JSON输出:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"扫描失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()