# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
攻击路径智能规划器
使用图算法优化攻击路径，支持多目标优化和智能决策
"""

import json
import math
import heapq
import random
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AttackNodeType(Enum):
    """攻击节点类型"""
    TARGET = "target"
    PORT = "port"
    SERVICE = "service"
    VULNERABILITY = "vulnerability"
    CREDENTIAL = "credential"
    ACCESS = "access"
    PRIVILEGE = "privilege"
    DATA = "data"


class AttackEdgeType(Enum):
    """攻击边类型"""
    SCAN = "scan"  # 扫描发现
    EXPLOIT = "exploit"  # 漏洞利用
    BRUTEFORCE = "bruteforce"  # 暴力破解
    ENUMERATE = "enumerate"  # 信息枚举
    ESCALATE = "escalate"  # 权限提升
    LATERAL = "lateral"  # 横向移动
    PERSIST = "persist"  # 持久化
    EXFIL = "exfil"  # 数据外泄


@dataclass
class AttackNode:
    """攻击图节点"""
    node_id: str
    node_type: AttackNodeType
    value: Any
    properties: Dict[str, Any]
    risk: float  # 0.0-1.0
    value_score: float  # 0.0-1.0
    children: List[str]  # 子节点ID列表


@dataclass
class AttackEdge:
    """攻击图边"""
    edge_id: str
    source_id: str
    target_id: str
    edge_type: AttackEdgeType
    success_probability: float  # 0.0-1.0
    cost: float  # 时间成本
    stealth: float  # 隐蔽性 0.0-1.0
    tool_requirements: List[str]  # 所需工具ID
    prerequisites: List[str]  # 前提条件


@dataclass
class AttackPath:
    """攻击路径（增强版）"""
    path_id: str
    nodes: List[AttackNode]
    edges: List[AttackEdge]
    total_success_probability: float
    total_cost: float
    total_stealth: float
    total_risk: float
    total_value: float
    steps: List[Dict[str, Any]]
    score: float  # 综合评分


class AttackPlanner:
    """攻击路径规划器"""
    
    def __init__(self, knowledge_base: Dict = None):
        self.knowledge_base = knowledge_base or self._load_default_knowledge()
        self.nodes: Dict[str, AttackNode] = {}
        self.edges: Dict[str, AttackEdge] = {}
        
        # 攻击模式库
        self.attack_patterns = self._load_attack_patterns()
        
        # 评分权重配置
        self.weights = {
            "success": 0.35,      # 成功率权重
            "cost": 0.25,         # 成本权重（负向）
            "stealth": 0.20,      # 隐蔽性权重
            "value": 0.20         # 价值权重
        }
    
    def _load_default_knowledge(self) -> Dict:
        """加载默认知识库"""
        return {
            "port_vulnerabilities": {
                21: ["anonymous_login", "weak_password", "directory_traversal"],
                22: ["weak_password", "ssh_key_leak", "cve-2018-15473"],
                23: ["clear_text", "weak_password"],
                25: ["open_relay", "spoofing"],
                53: ["zone_transfer", "cache_poisoning"],
                80: ["xss", "sqli", "rce", "lfi", "csrf"],
                443: ["ssl_vulnerabilities", "heartbleed", "poodle"],
                445: ["eternalblue", "smb_relay", "zerologon"],
                1433: ["weak_password", "sqli", "xp_cmdshell"],
                3306: ["weak_password", "sqli", "cve-2012-2122"],
                3389: ["bluekeep", "weak_password", "cve-2019-0708"],
                5432: ["weak_password", "sqli"],
                5900: ["weak_password", "unencrypted"],
                6379: ["unauthorized_access", "lua_sandbox"],
                27017: ["unauthorized_access", "nosqli"]
            },
            "service_tools": {
                "http": ["dirsearch", "nikto", "nuclei", "sqlmap", "wpscan", "joomscan"],
                "ssh": ["hydra", "medusa", "crackmapexec"],
                "ftp": ["hydra", "ftp_bruteforce"],
                "smb": ["crackmapexec", "enum4linux", "smbmap"],
                "mysql": ["sqlmap", "hydra", "mysql_audit"],
                "rdp": ["hydra", "crowbar", "rdp_bruteforce"],
                "redis": ["redis_audit", "redis_exploit"],
                "vnc": ["vnc_bruteforce"]
            },
            "vulnerability_exploits": {
                "xss": ["beef", "xsstrike"],
                "sqli": ["sqlmap", "commix"],
                "rce": ["metasploit", "nuclei"],
                "lfi": ["lfi_scanner", "php_filter_chain"],
                "csrf": ["csrf_tester"],
                "weak_password": ["hydra", "medusa", "crackmapexec"]
            }
        }
    
    def _load_attack_patterns(self) -> List[Dict]:
        """加载攻击模式"""
        return [
            {
                "name": "Web渗透链",
                "description": "针对Web应用的完整攻击链",
                "steps": [
                    {"type": AttackNodeType.PORT, "value": [80, 443, 8080, 8443]},
                    {"type": AttackNodeType.SERVICE, "value": "http"},
                    {"type": AttackEdgeType.SCAN, "tools": ["whatweb", "dirsearch"]},
                    {"type": AttackEdgeType.ENUMERATE, "tools": ["nikto", "nuclei"]},
                    {"type": AttackNodeType.VULNERABILITY, "value": ["xss", "sqli", "rce"]},
                    {"type": AttackEdgeType.EXPLOIT, "tools": ["sqlmap", "metasploit"]},
                    {"type": AttackNodeType.ACCESS, "value": "web_access"},
                    {"type": AttackEdgeType.ESCALATE, "tools": ["webshell", "reverse_shell"]}
                ]
            },
            {
                "name": "数据库攻击链",
                "description": "针对数据库的攻击链",
                "steps": [
                    {"type": AttackNodeType.PORT, "value": [3306, 5432, 1433, 27017]},
                    {"type": AttackNodeType.SERVICE, "value": ["mysql", "postgresql", "mssql", "mongodb"]},
                    {"type": AttackEdgeType.SCAN, "tools": ["nmap"]},
                    {"type": AttackEdgeType.BRUTEFORCE, "tools": ["hydra", "medusa"]},
                    {"type": AttackNodeType.CREDENTIAL, "value": "database_credential"},
                    {"type": AttackNodeType.ACCESS, "value": "database_access"},
                    {"type": AttackEdgeType.ENUMERATE, "tools": ["database_enum"]},
                    {"type": AttackNodeType.DATA, "value": "sensitive_data"}
                ]
            },
            {
                "name": "横向移动链",
                "description": "内网横向移动攻击链",
                "steps": [
                    {"type": AttackNodeType.ACCESS, "value": "initial_access"},
                    {"type": AttackEdgeType.ENUMERATE, "tools": ["nmap", "crackmapexec"]},
                    {"type": AttackNodeType.SERVICE, "value": ["smb", "ssh", "rdp"]},
                    {"type": AttackEdgeType.BRUTEFORCE, "tools": ["hydra", "crackmapexec"]},
                    {"type": AttackNodeType.CREDENTIAL, "value": "stolen_credential"},
                    {"type": AttackEdgeType.LATERAL, "tools": ["psexec", "wmiexec"]},
                    {"type": AttackNodeType.ACCESS, "value": "lateral_access"},
                    {"type": AttackEdgeType.PERSIST, "tools": ["persistence_tools"]}
                ]
            }
        ]
    
    def build_attack_graph(self, scan_data: Dict) -> Dict[str, Any]:
        """基于扫描数据构建攻击图"""
        target = scan_data.get("target", "unknown")
        ports = scan_data.get("ports", [])
        vulnerabilities = scan_data.get("vulnerabilities", [])
        fingerprint = scan_data.get("fingerprint", {})
        
        # 清空现有图
        self.nodes = {}
        self.edges = {}
        
        # 创建目标节点
        target_node = AttackNode(
            node_id=f"target_{target}",
            node_type=AttackNodeType.TARGET,
            value=target,
            properties={"type": "initial_target"},
            risk=0.1,
            value_score=0.8,
            children=[]
        )
        self.nodes[target_node.node_id] = target_node
        
        # 创建端口节点
        port_nodes = []
        for port_info in ports:
            port = port_info.get("port", 0)
            service = port_info.get("service", "").lower()
            state = port_info.get("state", "open")
            
            if state != "open":
                continue
            
            # 评估端口风险
            port_risk = self._assess_port_risk(port, service)
            
            # 创建端口节点
            port_node = AttackNode(
                node_id=f"port_{port}",
                node_type=AttackNodeType.PORT,
                value=port,
                properties={"service": service, "state": state},
                risk=port_risk,
                value_score=self._calculate_port_value(port, service),
                children=[]
            )
            port_nodes.append(port_node)
            self.nodes[port_node.node_id] = port_node
            
            # 添加从目标到端口的边（扫描发现）
            scan_edge = AttackEdge(
                edge_id=f"scan_{target}_{port}",
                source_id=target_node.node_id,
                target_id=port_node.node_id,
                edge_type=AttackEdgeType.SCAN,
                success_probability=0.95,
                cost=5.0,
                stealth=0.8,
                tool_requirements=["nmap"],
                prerequisites=[]
            )
            self.edges[scan_edge.edge_id] = scan_edge
            
            # 创建服务节点
            if service:
                service_node = AttackNode(
                    node_id=f"service_{port}_{service}",
                    node_type=AttackNodeType.SERVICE,
                    value=service,
                    properties={"port": port, "version": port_info.get("version", "")},
                    risk=port_risk * 1.2,
                    value_score=port_node.value_score,
                    children=[]
                )
                self.nodes[service_node.node_id] = service_node
                
                # 添加从端口到服务的边
                service_edge = AttackEdge(
                    edge_id=f"service_{port}_{service}",
                    source_id=port_node.node_id,
                    target_id=service_node.node_id,
                    edge_type=AttackEdgeType.ENUMERATE,
                    success_probability=0.9,
                    cost=2.0,
                    stealth=0.9,
                    tool_requirements=["nmap", "banner_grab"],
                    prerequisites=[]
                )
                self.edges[service_edge.edge_id] = service_edge
                
                # 添加可能的漏洞节点
                self._add_vulnerability_nodes(service_node, vulnerabilities)
        
        # 添加基于指纹的节点
        self._add_fingerprint_nodes(fingerprint, target_node)
        
        graph_info = {
            "target": target,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "port_count": len(port_nodes),
            "vulnerability_count": len(vulnerabilities)
        }
        
        logger.info(f"Built attack graph with {len(self.nodes)} nodes and {len(self.edges)} edges")
        return graph_info
    
    def _assess_port_risk(self, port: int, service: str) -> float:
        """评估端口风险"""
        risk_map = {
            21: 0.6,   # FTP
            22: 0.7,   # SSH
            23: 0.8,   # Telnet
            25: 0.5,   # SMTP
            53: 0.4,   # DNS
            80: 0.6,   # HTTP
            443: 0.5,  # HTTPS
            445: 0.9,  # SMB
            1433: 0.8, # MSSQL
            3306: 0.7, # MySQL
            3389: 0.9, # RDP
            5432: 0.7, # PostgreSQL
            5900: 0.8, # VNC
            6379: 0.6, # Redis
            27017: 0.6  # MongoDB
        }
        
        return risk_map.get(port, 0.3)
    
    def _calculate_port_value(self, port: int, service: str) -> float:
        """计算端口价值"""
        value_map = {
            80: 0.9,    # Web服务通常有价值
            443: 0.9,   # HTTPS服务
            3389: 0.8,  # RDP远程桌面
            22: 0.7,    # SSH管理
            3306: 0.8,  # MySQL数据库
            1433: 0.8,  # MSSQL数据库
            445: 0.7,   # SMB文件共享
            21: 0.4,    # FTP
            23: 0.3,    # Telnet
            25: 0.5,    # SMTP邮件
            53: 0.3,    # DNS
            5432: 0.7,  # PostgreSQL
            5900: 0.6,  # VNC
            6379: 0.5,  # Redis
            27017: 0.5  # MongoDB
        }
        
        return value_map.get(port, 0.3)
    
    def _add_vulnerability_nodes(self, service_node: AttackNode, vulnerabilities: List[Dict]):
        """添加漏洞节点"""
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "").lower()
            severity_score = {
                "critical": 0.9,
                "high": 0.8,
                "medium": 0.6,
                "low": 0.4,
                "info": 0.2
            }.get(severity, 0.3)
            
            vuln_node = AttackNode(
                node_id=f"vuln_{str(hash(str(vuln)))[:8]}",
                node_type=AttackNodeType.VULNERABILITY,
                value=vuln.get("name", "unknown"),
                properties={
                    "severity": severity,
                    "description": vuln.get("description", ""),
                    "cve": vuln.get("cve", "")
                },
                risk=severity_score,
                value_score=severity_score * 0.8,  # 漏洞价值与风险相关
                children=[]
            )
            self.nodes[vuln_node.node_id] = vuln_node
            
            # 添加从服务到漏洞的边（发现漏洞）
            vuln_edge = AttackEdge(
                edge_id=f"find_vuln_{service_node.node_id}_{vuln_node.node_id}",
                source_id=service_node.node_id,
                target_id=vuln_node.node_id,
                edge_type=AttackEdgeType.SCAN,
                success_probability=0.7,
                cost=10.0,
                stealth=0.6,
                tool_requirements=["nuclei", "nikto", "vuln_scanner"],
                prerequisites=[]
            )
            self.edges[vuln_edge.edge_id] = vuln_edge
            
            # 添加从漏洞到访问节点的边（利用漏洞）
            access_node = AttackNode(
                node_id=f"access_{vuln_node.node_id}",
                node_type=AttackNodeType.ACCESS,
                value="initial_access",
                properties={"source": "vulnerability_exploit"},
                risk=severity_score * 1.1,
                value_score=severity_score,
                children=[]
            )
            self.nodes[access_node.node_id] = access_node
            
            exploit_edge = AttackEdge(
                edge_id=f"exploit_{vuln_node.node_id}_{access_node.node_id}",
                source_id=vuln_node.node_id,
                target_id=access_node.node_id,
                edge_type=AttackEdgeType.EXPLOIT,
                success_probability=severity_score * 0.8,  # 高严重度漏洞利用成功率更高
                cost=15.0,
                stealth=0.4,
                tool_requirements=["metasploit", "custom_exploit"],
                prerequisites=[]
            )
            self.edges[exploit_edge.edge_id] = exploit_edge
    
    def _add_fingerprint_nodes(self, fingerprint: Dict, target_node: AttackNode):
        """添加基于指纹的节点"""
        if not fingerprint:
            return
        
        # 添加CMS节点
        cms_list = fingerprint.get("cms", [])
        for cms in cms_list:
            cms_node = AttackNode(
                node_id=f"cms_{str(hash(cms))[:8]}",
                node_type=AttackNodeType.SERVICE,
                value=cms,
                properties={"type": "cms", "fingerprint": "web_fingerprint"},
                risk=0.6,
                value_score=0.7,
                children=[]
            )
            self.nodes[cms_node.node_id] = cms_node
            
            # 添加从目标到CMS的边
            cms_edge = AttackEdge(
                edge_id=f"fingerprint_{target_node.node_id}_{cms_node.node_id}",
                source_id=target_node.node_id,
                target_id=cms_node.node_id,
                edge_type=AttackEdgeType.SCAN,
                success_probability=0.9,
                cost=2.0,
                stealth=0.9,
                tool_requirements=["whatweb", "wappalyzer"],
                prerequisites=[]
            )
            self.edges[cms_edge.edge_id] = cms_edge
    
    def find_all_paths(self, start_node_id: str, end_node_types: List[AttackNodeType], max_depth: int = 10) -> List[List[str]]:
        """查找所有从起始节点到指定类型节点的路径"""
        all_paths = []
        
        def dfs(current_node_id: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            
            current_node = self.nodes.get(current_node_id)
            if not current_node:
                return
            
            # 检查是否到达目标类型节点
            if current_node.node_type in end_node_types:
                all_paths.append(path.copy())
                return
            
            # 继续搜索
            for edge in self.edges.values():
                if edge.source_id == current_node_id:
                    next_node_id = edge.target_id
                    if next_node_id not in path:  # 避免循环
                        path.append(next_node_id)
                        dfs(next_node_id, path, depth + 1)
                        path.pop()
        
        dfs(start_node_id, [start_node_id], 0)
        return all_paths
    
    def calculate_path_score(self, path_nodes: List[str]) -> AttackPath:
        """计算路径评分并创建AttackPath对象"""
        if not path_nodes or len(path_nodes) < 2:
            return None
        
        # 收集路径上的节点和边
        path_node_objects = []
        path_edge_objects = []
        steps = []
        
        total_success = 1.0
        total_cost = 0.0
        total_stealth = 0.0
        total_risk = 0.0
        total_value = 0.0
        
        for i in range(len(path_nodes) - 1):
            source_id = path_nodes[i]
            target_id = path_nodes[i + 1]
            
            # 获取节点
            source_node = self.nodes[source_id]
            target_node = self.nodes[target_id]
            
            if i == 0:
                path_node_objects.append(source_node)
            
            path_node_objects.append(target_node)
            
            # 查找边
            edge_found = None
            for edge in self.edges.values():
                if edge.source_id == source_id and edge.target_id == target_id:
                    edge_found = edge
                    break
            
            if edge_found:
                path_edge_objects.append(edge_found)
                
                # 更新统计
                total_success *= edge_found.success_probability
                total_cost += edge_found.cost
                total_stealth += edge_found.stealth
                total_risk += source_node.risk
                total_value += source_node.value_score
                
                # 创建步骤描述
                step = {
                    "step_id": f"step_{i+1}",
                    "from": source_node.node_type.value,
                    "to": target_node.node_type.value,
                    "action": edge_found.edge_type.value,
                    "success_probability": edge_found.success_probability,
                    "cost": edge_found.cost,
                    "tools": edge_found.tool_requirements
                }
                steps.append(step)
        
        # 添加最后一个节点的风险和价值
        if path_nodes:
            last_node = self.nodes[path_nodes[-1]]
            total_risk += last_node.risk
            total_value += last_node.value_score
        
        # 计算平均隐蔽性
        avg_stealth = total_stealth / len(path_edge_objects) if path_edge_objects else 0
        
        # 计算综合评分
        score = (
            self.weights["success"] * total_success +
            self.weights["stealth"] * avg_stealth +
            self.weights["value"] * (total_value / len(path_nodes)) -
            self.weights["cost"] * (total_cost / 100.0)  # 成本是负向指标
        )
        
        # 创建AttackPath对象
        attack_path = AttackPath(
            path_id=f"path_{str(hash(str(path_nodes)))[:8]}",
            nodes=path_node_objects,
            edges=path_edge_objects,
            total_success_probability=total_success,
            total_cost=total_cost,
            total_stealth=avg_stealth,
            total_risk=total_risk / len(path_nodes),
            total_value=total_value / len(path_nodes),
            steps=steps,
            score=score
        )
        
        return attack_path
    
    def find_optimal_paths(self, start_node_id: str, end_node_types: List[AttackNodeType], 
                          top_k: int = 5, algorithm: str = "astar") -> List[AttackPath]:
        """寻找最优攻击路径"""
        if algorithm == "astar":
            return self._astar_search(start_node_id, end_node_types, top_k)
        elif algorithm == "dijkstra":
            return self._dijkstra_search(start_node_id, end_node_types, top_k)
        else:
            return self._bfs_search(start_node_id, end_node_types, top_k)
    
    def _astar_search(self, start_node_id: str, end_node_types: List[AttackNodeType], 
                     top_k: int) -> List[AttackPath]:
        """A*算法搜索最优路径"""
        # 使用优先队列
        open_set = []
        heapq.heappush(open_set, (0, 0, start_node_id, []))  # (f_score, count, node_id, path)
        
        visited = {start_node_id: 0}
        paths_found = []
        
        count = 1  # 用于打破平局
        
        while open_set and len(paths_found) < top_k * 3:
            f_score, _, current_node_id, path = heapq.heappop(open_set)
            
            current_node = self.nodes.get(current_node_id)
            if not current_node:
                continue
            
            new_path = path + [current_node_id]
            
            # 检查是否到达目标
            if current_node.node_type in end_node_types:
                attack_path = self.calculate_path_score(new_path)
                if attack_path:
                    paths_found.append(attack_path)
                continue
            
            # 扩展节点
            for edge in self.edges.values():
                if edge.source_id == current_node_id:
                    neighbor_id = edge.target_id
                    
                    # 计算g_score（实际成本）
                    g_score = visited.get(current_node_id, 0) + edge.cost
                    
                    # 计算h_score（启发式估计到最近目标的最小成本）
                    h_score = self._heuristic_cost(neighbor_id, end_node_types)
                    
                    f_score = g_score + h_score
                    
                    if neighbor_id not in visited or g_score < visited[neighbor_id]:
                        visited[neighbor_id] = g_score
                        count += 1
                        heapq.heappush(open_set, (f_score, count, neighbor_id, new_path))
        
        # 按评分排序并返回top_k
        paths_found.sort(key=lambda x: x.score, reverse=True)
        return paths_found[:top_k]
    
    def _heuristic_cost(self, node_id: str, end_node_types: List[AttackNodeType]) -> float:
        """启发式函数，估计从节点到目标的最小成本"""
        node = self.nodes.get(node_id)
        if not node:
            return float('inf')
        
        # 如果已经是目标类型，成本为0
        if node.node_type in end_node_types:
            return 0
        
        # 基于节点类型和目标类型的距离估计
        type_distance = {
            AttackNodeType.TARGET: 50,
            AttackNodeType.PORT: 30,
            AttackNodeType.SERVICE: 20,
            AttackNodeType.VULNERABILITY: 10,
            AttackNodeType.ACCESS: 0,
            AttackNodeType.PRIVILEGE: 5,
            AttackNodeType.DATA: 0,
            AttackNodeType.CREDENTIAL: 15
        }
        
        # 计算当前节点类型到最近目标类型的距离
        min_distance = float('inf')
        current_distance = type_distance.get(node.node_type, 25)
        
        for end_type in end_node_types:
            end_distance = type_distance.get(end_type, 25)
            distance = abs(current_distance - end_distance)
            min_distance = min(min_distance, distance)
        
        return min_distance
    
    def _dijkstra_search(self, start_node_id: str, end_node_types: List[AttackNodeType],
                        top_k: int) -> List[AttackPath]:
        """Dijkstra算法搜索最优路径"""
        # 实现略（基于成本的最短路径）
        return self._bfs_search(start_node_id, end_node_types, top_k)
    
    def _bfs_search(self, start_node_id: str, end_node_types: List[AttackNodeType],
                   top_k: int) -> List[AttackPath]:
        """广度优先搜索路径"""
        all_paths = self.find_all_paths(start_node_id, end_node_types, max_depth=8)
        
        # 计算每条路径的评分
        scored_paths = []
        for path_nodes in all_paths:
            attack_path = self.calculate_path_score(path_nodes)
            if attack_path:
                scored_paths.append(attack_path)
        
        # 按评分排序
        scored_paths.sort(key=lambda x: x.score, reverse=True)
        return scored_paths[:top_k]
    
    def generate_attack_plan(self, scan_data: Dict, max_paths: int = 3) -> Dict[str, Any]:
        """生成完整的攻击计划"""
        # 构建攻击图
        graph_info = self.build_attack_graph(scan_data)
        
        # 查找最优攻击路径
        start_node_id = f"target_{scan_data.get('target', 'unknown')}"
        target_nodes = [AttackNodeType.ACCESS, AttackNodeType.PRIVILEGE, AttackNodeType.DATA]
        
        optimal_paths = self.find_optimal_paths(
            start_node_id=start_node_id,
            end_node_types=target_nodes,
            top_k=max_paths,
            algorithm="astar"
        )
        
        # 转换为前端友好格式
        formatted_paths = []
        for path in optimal_paths:
            formatted_path = {
                "path_id": path.path_id,
                "name": self._generate_path_name(path),
                "description": self._generate_path_description(path),
                "steps": path.steps,
                "total_success_probability": round(path.total_success_probability, 2),
                "total_cost": round(path.total_cost, 1),
                "total_stealth": round(path.total_stealth, 2),
                "total_risk": round(path.total_risk, 2),
                "total_value": round(path.total_value, 2),
                "score": round(path.score, 3)
            }
            formatted_paths.append(formatted_path)
        
        # 生成整体评估
        overall_assessment = self._generate_overall_assessment(formatted_paths, graph_info)
        
        plan = {
            "graph_info": graph_info,
            "paths": formatted_paths,
            "overall_assessment": overall_assessment,
            "timestamp": datetime.now().isoformat(),
            "planner_version": "1.0"
        }
        
        return plan
    
    def _generate_path_name(self, path: AttackPath) -> str:
        """生成路径名称"""
        node_types = [node.node_type.value for node in path.nodes]
        
        if AttackNodeType.VULNERABILITY.value in node_types:
            return "漏洞利用攻击链"
        elif AttackNodeType.CREDENTIAL.value in node_types:
            return "凭据攻击链"
        elif any(port in [node.value for node in path.nodes if node.node_type == AttackNodeType.PORT] 
                for port in [80, 443, 8080, 8443]):
            return "Web渗透攻击链"
        elif any(port in [node.value for node in path.nodes if node.node_type == AttackNodeType.PORT] 
                for port in [3306, 5432, 1433, 27017]):
            return "数据库攻击链"
        else:
            return "通用攻击链"
    
    def _generate_path_description(self, path: AttackPath) -> str:
        """生成路径描述"""
        description_parts = []
        
        for i, step in enumerate(path.steps):
            action_map = {
                "scan": "扫描",
                "exploit": "利用",
                "bruteforce": "暴力破解",
                "enumerate": "枚举",
                "escalate": "权限提升",
                "lateral": "横向移动",
                "persist": "持久化",
                "exfil": "数据外泄"
            }
            
            action = action_map.get(step["action"], step["action"])
            tools = "、".join(step["tools"][:2])
            
            if i == 0:
                description_parts.append(f"通过{action}发现{step['to']}")
            else:
                description_parts.append(f"然后使用{tools}进行{action}")
        
        description = "，".join(description_parts)
        return f"攻击路径：{description}。成功率{path.total_success_probability*100:.1f}%，预计耗时{path.total_cost:.0f}分钟。"
    
    def _generate_overall_assessment(self, paths: List[Dict], graph_info: Dict) -> Dict:
        """生成整体评估"""
        if not paths:
            return {
                "risk_level": "low",
                "summary": "未发现有效的攻击路径，目标安全性较好。",
                "recommendations": ["保持当前安全配置", "定期进行安全评估"]
            }
        
        # 计算平均风险
        avg_risk = sum(p["total_risk"] for p in paths) / len(paths)
        
        if avg_risk > 0.7:
            risk_level = "critical"
        elif avg_risk > 0.5:
            risk_level = "high"
        elif avg_risk > 0.3:
            risk_level = "medium"
        elif avg_risk > 0.1:
            risk_level = "low"
        else:
            risk_level = "info"
        
        # 生成摘要
        best_path = paths[0]
        summary = f"发现{len(paths)}条有效攻击路径。最佳路径成功率{best_path['total_success_probability']*100:.1f}%，"
        summary += f"风险等级{risk_level}。"
        
        # 生成建议
        recommendations = []
        
        if risk_level in ["critical", "high"]:
            recommendations.append("立即修复高危漏洞")
            recommendations.append("加强网络边界防护")
            recommendations.append("实施多因素认证")
        
        if any("Web" in p["name"] for p in paths):
            recommendations.append("加固Web应用安全配置")
            recommendations.append("部署WAF防护")
        
        if any("数据库" in p["name"] for p in paths):
            recommendations.append("加强数据库访问控制")
            recommendations.append("定期更换数据库密码")
        
        return {
            "risk_level": risk_level,
            "risk_score": round(avg_risk, 2),
            "summary": summary,
            "recommendations": recommendations,
            "paths_count": len(paths),
            "best_path_score": best_path["score"]
        }


def test_planner():
    """测试规划器"""
    test_data = {
        "target": "example.com",
        "ports": [
            {"port": 80, "service": "http", "state": "open"},
            {"port": 443, "service": "https", "state": "open"},
            {"port": 3306, "service": "mysql", "state": "open"},
            {"port": 22, "service": "ssh", "state": "open"}
        ],
        "vulnerabilities": [
            {"name": "SQL注入漏洞", "severity": "high", "description": "存在SQL注入点"},
            {"name": "XSS漏洞", "severity": "medium", "description": "跨站脚本漏洞"}
        ],
        "fingerprint": {
            "cms": ["WordPress 5.8"],
            "web_server": "nginx/1.18.0"
        }
    }
    
    planner = AttackPlanner()
    plan = planner.generate_attack_plan(test_data, max_paths=3)
    
    print(json.dumps(plan, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    test_planner()