# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
NmapScanSkill - Nmap端口扫描技能

功能：
1. 端口扫描和服务识别
2. 操作系统检测
3. 脚本扫描
"""

import random
import time
from typing import Dict, List, Any
from .base_skill import BaseSkill


class NmapScanSkill(BaseSkill):
    """Nmap端口扫描技能"""
    
    def get_name(self) -> str:
        return "NmapScanSkill"
    
    def get_description(self) -> str:
        return "使用Nmap进行端口扫描、服务识别和操作系统检测"
    
    def get_category(self) -> str:
        return "reconnaissance"
    
    def get_difficulty(self) -> str:
        return "easy"
    
    def get_required_tools(self) -> List[str]:
        return ["nmap"]
    
    def get_prerequisites(self) -> List[str]:
        return []  # 基础技能，无需前置
    
    def get_success_rate(self) -> float:
        """获取技能成功率"""
        return 0.95  # Nmap扫描成功率很高
    
    def get_estimated_time(self) -> str:
        """获取预估执行时间"""
        return "5-10分钟"
    
    def can_handle(self, context: Dict[str, Any]) -> bool:
        """
        判断是否能处理当前上下文
        
        条件：
        1. 有目标地址
        2. 目标可达（可通过简单检查）
        3. 尚未进行深度端口扫描
        """
        if not context:
            return False
        
        target = context.get("target", "")
        if not target:
            return False
        
        # 检查是否已有完整的nmap扫描结果
        scan_results = context.get("scan_results", {})
        if "nmap" in scan_results:
            nmap_data = scan_results["nmap"]
            # 如果已有详细的端口信息，可能不需要再次扫描
            if isinstance(nmap_data, dict) and "ports" in nmap_data:
                ports = nmap_data["ports"]
                if ports and len(ports) >= 3:  # 如果有3个以上端口信息，认为已扫描
                    return False
        
        # 检查当前状态
        current_state = context.get("current_state", {})
        if "open_ports" in current_state and len(current_state["open_ports"]) >= 5:
            # 如果已有5个以上开放端口信息，可能不需要再次扫描
            return False
        
        return True
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行Nmap扫描
        
        模拟执行，实际环境中应调用真实nmap命令
        """
        target = context.get("target", "")
        
        if not target:
            return {
                "success": False,
                "error": "缺少目标地址",
                "skill_name": self.name
            }
        
        try:
            # 模拟扫描过程
            self._simulate_scanning(target)
            
            # 生成模拟结果
            scan_result = self._generate_nmap_result(target)
            
            return {
                "success": True,
                "skill_name": self.name,
                "target": target,
                "scan_type": "nmap_comprehensive",
                "open_ports": scan_result["open_ports"],
                "services": scan_result["services"],
                "os_info": scan_result["os_info"],
                "scan_time": scan_result["scan_time"],
                "details": {
                    "command_used": f"nmap -sV -sC -O -T4 {target}",
                    "scan_options": "版本检测(-sV)、默认脚本(-sC)、OS检测(-O)、激进时序(-T4)",
                    "ports_scanned": "1-1000",
                    "host_status": "up"
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Nmap扫描失败: {str(e)}",
                "skill_name": self.name,
                "target": target
            }
    
    def _simulate_scanning(self, target: str) -> None:
        """模拟扫描过程"""
        # 模拟扫描时间
        scan_time = random.uniform(2.0, 5.0)
        time.sleep(min(scan_time, 0.5))  # 实际等待时间缩短
    
    def _generate_nmap_result(self, target: str) -> Dict[str, Any]:
        """生成模拟的Nmap扫描结果"""
        
        # 常见的端口和服务
        common_ports = [
            {"port": 80, "service": "http", "state": "open", "version": "nginx/1.18.0"},
            {"port": 443, "service": "https", "state": "open", "version": "nginx/1.18.0"},
            {"port": 22, "service": "ssh", "state": "open", "version": "OpenSSH 8.2p1"},
            {"port": 21, "service": "ftp", "state": "closed", "version": ""},
            {"port": 25, "service": "smtp", "state": "filtered", "version": ""},
            {"port": 53, "service": "domain", "state": "open", "version": "ISC BIND 9.11"},
            {"port": 3306, "service": "mysql", "state": "open", "version": "MySQL 8.0.26"},
            {"port": 3389, "service": "ms-wbt-server", "state": "closed", "version": ""},
            {"port": 8080, "service": "http-proxy", "state": "open", "version": "Apache/2.4.41"},
            {"port": 8443, "service": "https-alt", "state": "open", "version": "Apache/2.4.41"}
        ]
        
        # 随机选择一些端口作为开放
        open_ports = []
        for port_info in common_ports:
            if port_info["state"] == "open" or random.random() < 0.3:
                open_ports.append(port_info)
        
        # 确保至少有一些开放端口
        if len(open_ports) < 3:
            open_ports = [p for p in common_ports if p["state"] == "open"][:5]
        
        # 提取服务信息
        services = {}
        for port_info in open_ports:
            service = port_info["service"]
            if service not in services:
                services[service] = []
            services[service].append(str(port_info["port"]))
        
        # 操作系统信息
        os_choices = [
            "Linux 5.4.0-42-generic",
            "Windows 10 Pro 19042",
            "Ubuntu 20.04 LTS",
            "CentOS 7.9",
            "Debian 10.10"
        ]
        os_info = random.choice(os_choices)
        
        return {
            "open_ports": open_ports,
            "services": services,
            "os_info": os_info,
            "scan_time": f"{random.uniform(1.5, 4.2):.1f} seconds"
        }
    
    def _extract_from_existing_scan(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        从现有扫描结果中提取Nmap信息
        
        用于当已有扫描结果时，避免重复扫描
        """
        if "nmap" not in scan_results:
            return {}
        
        nmap_data = scan_results["nmap"]
        if not isinstance(nmap_data, dict):
            return {}
        
        result = {
            "open_ports": [],
            "services": {},
            "os_info": "Unknown"
        }
        
        # 提取端口信息
        if "ports" in nmap_data and isinstance(nmap_data["ports"], list):
            result["open_ports"] = nmap_data["ports"]
            
            # 构建服务映射
            for port_info in nmap_data["ports"]:
                if isinstance(port_info, dict):
                    service = port_info.get("service", "")
                    port = port_info.get("port", "")
                    if service and port:
                        if service not in result["services"]:
                            result["services"][service] = []
                        result["services"][service].append(str(port))
        
        # 提取OS信息
        if "os" in nmap_data:
            result["os_info"] = nmap_data["os"]
        
        return result