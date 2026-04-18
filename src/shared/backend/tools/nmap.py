# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Nmap扫描工具模块（基于BaseTool的新版本）
封装nmap扫描功能，提供端口扫描接口
支持：单主机扫描、全端口扫描、子网主机发现
"""

import subprocess
import json
import re
import sys
import os
from typing import Dict, List, Any, Optional

# 导入工具基类
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.tools.base_tool import (
    BaseTool, ToolExecutionMode, ToolCategory, 
    ToolPriority, ToolExecutionResult, register_tool
)


def _is_network_target(target: str) -> bool:
    """判断目标是否为子网/范围（而非单个主机）"""
    t = target.strip()
    # CIDR 表示法：192.168.1.0/24
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$', t):
        return True
    # IP 范围：192.168.1.1-254 或 192.168.1-5.1
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}-\d{1,3}$', t):
        return True
    # 通配符：192.168.1.*
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\*$', t):
        return True
    return False


@register_tool
class NmapTool(BaseTool):
    """Nmap扫描工具类（新版本）"""
    
    def __init__(self):
        super().__init__(
            tool_name="nmap",
            command="nmap",
            description="端口扫描器",
            category=ToolCategory.NETWORK_SCAN,
            priority=ToolPriority.CRITICAL,
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
    
    def _parse_nmap_output(self, output: str) -> List[Dict[str, Any]]:
        """解析nmap输出，提取端口和服务信息"""
        ports = []
        port_pattern = r'(\d+)/tcp\s+(\w+)\s+(\S+)'
        lines = output.split('\n')
        in_port_section = False
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('PORT') and 'STATE' in line and 'SERVICE' in line:
                in_port_section = True
                continue
            
            if not in_port_section:
                continue
            
            if not line or line.startswith('---'):
                continue
            
            match = re.match(port_pattern, line)
            if match:
                port_num = int(match.group(1))
                state = match.group(2)
                service = match.group(3)
                
                if state == 'open':
                    ports.append({
                        "port": port_num,
                        "service": service,
                        "state": state,
                        "service_guess": self._guess_service(port_num)
                    })
        
        return ports

    def _parse_host_discovery(self, output: str) -> List[str]:
        """从 nmap -sn 输出中解析存活主机 IP 列表"""
        hosts = []
        for line in output.splitlines():
            # "Nmap scan report for 192.168.1.5" 或含括号的 hostname
            m = re.search(r'Nmap scan report for (?:\S+ )?\(?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\)?', line)
            if m:
                hosts.append(m.group(1))
        return hosts

    def discover_hosts(self, network: str, timeout: int = 120) -> Dict[str, Any]:
        """
        主机发现：对给定子网执行 nmap -sn（Ping 扫描），返回存活主机列表。
        支持 CIDR（192.168.1.0/24）、范围（192.168.1.1-50）等格式。
        """
        cmd = [
            self.command,
            "-sn",          # 仅做 Ping 扫描，不扫端口
            "-T4",
            "--host-timeout", "10s",
            network
        ]
        result = self._run_command(cmd, timeout=timeout)

        if result.returncode != 0 and not result.stdout:
            return {
                "network": network,
                "alive_hosts": [],
                "error": result.stderr[:300] if result.stderr else "主机发现失败",
                "execution_mode": "real",
                "command": " ".join(cmd),
            }

        hosts = self._parse_host_discovery(result.stdout)
        return {
            "network": network,
            "alive_hosts": hosts,
            "total_alive": len(hosts),
            "raw_output": result.stdout[:2000],
            "execution_mode": "real",
            "command": " ".join(cmd),
        }

    def _execute_real(self, target: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """真实执行nmap扫描"""
        if options is None:
            options = {}

        # ── 子网/网段：先做主机发现，再汇总 ──────────────────────────────
        if _is_network_target(target):
            return self._execute_network_discovery(target, options)

        # 提取选项参数
        full_port = options.get("full_port", False)   # 全端口扫描
        ports = options.get("ports", None)
        if full_port:
            ports = "1-65535"
        elif not ports:
            ports_list = self.common_ports
            ports = ",".join(str(p) for p in ports_list)
        
        scan_type = options.get("scan_type", "-sT")
        timeout = options.get("timeout", 600)
        
        # 清理目标格式
        clean_target = target
        if target.startswith("http://"):
            clean_target = target.replace("http://", "").split("/")[0]
        elif target.startswith("https://"):
            clean_target = target.replace("https://", "").split("/")[0]
        
        # 构建命令
        cmd = [
            self.command,
            scan_type,
            '-p', ports,
            '-T4',           # 较快扫描速度
            '--open',        # 只显示开放端口
            '-n',            # 不进行DNS解析
            '--host-timeout', '2m',
            clean_target
        ]

        # 全端口扫描加 -sV（服务版本检测）
        if full_port:
            cmd.insert(1, "-sV")
            cmd[cmd.index("--host-timeout") + 1] = "5m"
        
        # 执行命令
        result = self._run_command(cmd, timeout=timeout)
        
        if result.returncode != 0:
            error_msg = f"nmap命令执行失败: {result.returncode}"
            if result.stderr:
                error_msg += f"\n{result.stderr[:200]}"
            
            return {
                "target": target,
                "clean_target": clean_target,
                "ports": [],
                "error": error_msg,
                "raw_output": result.stderr[:500] if result.stderr else "",
                "execution_mode": "real"
            }
        
        # 解析结果
        ports_found = self._parse_nmap_output(result.stdout)
        
        return {
            "target": target,
            "clean_target": clean_target,
            "ports": ports_found,
            "total_open_ports": len(ports_found),
            "raw_output": result.stdout[:2000],
            "execution_mode": "real",
            "command": " ".join(cmd),
            "full_port_scan": full_port,
        }

    def _execute_network_discovery(self, network: str, options: Dict) -> Dict[str, Any]:
        """
        子网扫描：先主机发现，再对每个存活主机做端口扫描（最多 20 台）。
        返回结构：
          {
            "network": "192.168.1.0/24",
            "alive_hosts": [...],
            "host_scan_results": { ip: {ports:[...]} },
            "summary": "发现 N 台存活主机，共 M 个开放端口",
          }
        """
        timeout = options.get("timeout", 300)

        # Step 1: Ping 扫描
        discovery = self.discover_hosts(network, timeout=min(timeout, 60))
        alive = discovery.get("alive_hosts", [])

        if not alive:
            return {
                "network": network,
                "alive_hosts": [],
                "host_scan_results": {},
                "summary": f"网段 {network} 内未发现存活主机",
                "raw_output": discovery.get("raw_output", ""),
                "execution_mode": "real",
            }

        # Step 2: 对存活主机逐一扫描（最多 20 台）
        scan_targets = alive[:20]
        host_results: Dict[str, Any] = {}
        total_ports = 0

        ports_str = ",".join(str(p) for p in self.common_ports)
        for ip in scan_targets:
            cmd = [
                self.command, "-sT",
                "-p", ports_str,
                "-T4", "--open", "-n",
                "--host-timeout", "90s",
                ip
            ]
            r = self._run_command(cmd, timeout=120)
            ports_found = self._parse_nmap_output(r.stdout) if r.returncode == 0 else []
            total_ports += len(ports_found)
            host_results[ip] = {
                "ports": ports_found,
                "total_open_ports": len(ports_found),
            }

        summary = (
            f"网段 {network} 发现 {len(alive)} 台存活主机"
            + (f"（仅扫描前 {len(scan_targets)} 台）" if len(alive) > 20 else "")
            + f"，共 {total_ports} 个开放端口"
        )

        return {
            "network": network,
            "alive_hosts": alive,
            "total_alive": len(alive),
            "host_scan_results": host_results,
            "summary": summary,
            "execution_mode": "real",
            "scan_type": "network_discovery",
        }

    def _simulate_execution(self, target: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """模拟nmap执行（当工具不可用时）"""
        import random
        
        # 子网模拟
        if _is_network_target(target):
            fake_hosts = [
                target.rsplit(".", 1)[0] + "." + str(i)
                for i in [1, 10, 20, 100, 200]
                if not target.endswith("*")
            ] or ["192.168.1.1", "192.168.1.10", "192.168.1.100"]

            host_results = {}
            for ip in fake_hosts[:3]:
                ports_sim = []
                for p in random.sample(self.common_ports, 3):
                    ports_sim.append({"port": p, "service": self._guess_service(p), "state": "open", "simulated": True})
                host_results[ip] = {"ports": ports_sim, "total_open_ports": len(ports_sim)}

            return {
                "network": target,
                "alive_hosts": fake_hosts[:3],
                "total_alive": 3,
                "host_scan_results": host_results,
                "summary": f"[模拟] 网段 {target} 发现 3 台存活主机",
                "execution_mode": "simulated",
                "simulated": True,
            }

        # 清理目标格式
        clean_target = target
        if target.startswith("http://"):
            clean_target = target.replace("http://", "").split("/")[0]
        elif target.startswith("https://"):
            clean_target = target.replace("https://", "").split("/")[0]
        
        # 模拟开放端口
        open_count = random.randint(3, 6)
        open_ports = random.sample(self.common_ports, min(open_count, len(self.common_ports)))
        simulated_ports = []
        for port in sorted(open_ports):
            service = self._guess_service(port)
            simulated_ports.append({
                "port": port, "service": service,
                "state": "open", "service_guess": service, "simulated": True
            })
        
        output_lines = [
            f"Starting Nmap 7.94 ( https://nmap.org ) at 2024-01-01 12:00:00 UTC",
            f"Nmap scan report for {clean_target}",
            f"Host is up (0.0010s latency).",
            f"PORT     STATE SERVICE",
            f"{'-' * 60}"
        ]
        for port_info in simulated_ports:
            output_lines.append(f"{port_info['port']}/tcp open  {port_info['service']}")
        output_lines.append(f"Nmap done: 1 IP address (1 host up) scanned in 2.34 seconds")
        
        return {
            "target": target,
            "clean_target": clean_target,
            "ports": simulated_ports,
            "total_open_ports": len(simulated_ports),
            "raw_output": "\n".join(output_lines),
            "execution_mode": "simulated",
            "simulated": True,
            "note": "这是模拟数据，实际环境中请安装nmap进行真实扫描"
        }
    
    def run(self, target: str) -> Dict[str, Any]:
        """执行nmap扫描（兼容旧接口）"""
        result = self.execute(target)
        return result.output


def main():
    """命令行入口点"""
    if len(sys.argv) != 2:
        print("用法: python new_nmap.py <target>")
        print("示例: python new_nmap.py example.com")
        print("示例: python new_nmap.py 192.168.1.1")
        sys.exit(1)
    
    target = sys.argv[1]
    tool = NmapTool()
    
    try:
        # 显示工具状态
        status = tool.get_status()
        print(f"工具状态: {'✅ 可用' if status['available'] else '❌ 不可用'}")
        if status['version']:
            print(f"版本信息: {status['version']}")
        
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
            print("-" * 60)
            print(f"{'端口':<8} {'服务':<15} {'状态':<10}")
            print("-" * 60)
            
            for port_info in result['ports']:
                port = port_info.get('port', '')
                service = port_info.get('service', '')
                state = port_info.get('state', '')
                simulated = " (模拟)" if port_info.get('simulated') else ""
                print(f"{port:<8} {service:<15} {state:<10}{simulated}")
        else:
            print("\n未发现开放端口")
        
        # 可选的JSON输出
        if '--json' in sys.argv:
            print("\n完整JSON输出:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"扫描失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()