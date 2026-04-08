# -*- coding: utf-8 -*-
"""
Planner模块 - 战略规划器
负责全局战略规划，基于因果图生成攻击路径
"""

import json
from typing import List, Dict, Any, Optional


class Planner:
    """规划器类"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    def initialize_task_graph(self, goal: str) -> Dict[str, Any]:
        """初始化任务图"""
        return {
            "id": "task_1",
            "goal": goal,
            "nodes": [
                {
                    "id": "node_1",
                    "type": "initialization",
                    "label": "初始化任务",
                    "status": "completed",
                    "dependencies": [],
                    "output": {"goal": goal}
                },
                {
                    "id": "node_2",
                    "type": "reconnaissance",
                    "label": "信息收集",
                    "status": "pending",
                    "dependencies": ["node_1"],
                    "output": {}
                },
                {
                    "id": "node_3",
                    "type": "vulnerability_scan",
                    "label": "漏洞扫描",
                    "status": "pending",
                    "dependencies": ["node_2"],
                    "output": {}
                },
                {
                    "id": "node_4",
                    "type": "exploitation",
                    "label": "漏洞利用",
                    "status": "pending",
                    "dependencies": ["node_3"],
                    "output": {}
                },
                {
                    "id": "node_5",
                    "type": "report",
                    "label": "生成报告",
                    "status": "pending",
                    "dependencies": ["node_4"],
                    "output": {}
                }
            ],
            "edges": [
                {"from": "node_1", "to": "node_2"},
                {"from": "node_2", "to": "node_3"},
                {"from": "node_3", "to": "node_4"},
                {"from": "node_4", "to": "node_5"}
            ]
        }
    
    def generate_plan(self, task_graph: Dict[str, Any], execution_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成规划"""
        operations = []
        
        # 分析执行结果，更新任务图
        for node_id, result in execution_results.items():
            # 寻找对应的节点
            for node in task_graph["nodes"]:
                if node["id"] == node_id:
                    # 更新节点状态
                    operations.append({
                        "operation": "UPDATE_NODE",
                        "node_id": node_id,
                        "updates": {
                            "status": "completed",
                            "output": result
                        }
                    })
                    
                    # 根据节点类型和结果生成新的子任务
                    if node["type"] == "reconnaissance":
                        # 基于信息收集结果生成新的扫描任务
                        ports = result.get("ports", [])
                        if ports:
                            for port in ports:
                                port_num = port.get("port")
                                service = port.get("service", "")
                                if port_num and service:
                                    new_node_id = f"node_{len(task_graph['nodes']) + 1}"
                                    operations.append({
                                        "operation": "ADD_NODE",
                                        "node": {
                                            "id": new_node_id,
                                            "type": "service_scan",
                                            "label": f"扫描服务 {service} (端口 {port_num})",
                                            "status": "pending",
                                            "dependencies": [node_id],
                                            "output": {}
                                        }
                                    })
                                    operations.append({
                                        "operation": "ADD_EDGE",
                                        "edge": {
                                            "from": node_id,
                                            "to": new_node_id
                                        }
                                    })
                                    operations.append({
                                        "operation": "ADD_EDGE",
                                        "edge": {
                                            "from": new_node_id,
                                            "to": "node_3"
                                        }
                                    })
                    
                    elif node["type"] == "vulnerability_scan":
                        # 基于漏洞扫描结果生成新的利用任务
                        vulnerabilities = result.get("vulnerabilities", [])
                        if vulnerabilities:
                            for vuln in vulnerabilities:
                                vuln_name = vuln.get("name")
                                severity = vuln.get("severity")
                                if vuln_name and severity in ["high", "critical"]:
                                    new_node_id = f"node_{len(task_graph['nodes']) + 1}"
                                    operations.append({
                                        "operation": "ADD_NODE",
                                        "node": {
                                            "id": new_node_id,
                                            "type": "exploit",
                                            "label": f"利用漏洞 {vuln_name} (严重程度: {severity})",
                                            "status": "pending",
                                            "dependencies": [node_id],
                                            "output": {}
                                        }
                                    })
                                    operations.append({
                                        "operation": "ADD_EDGE",
                                        "edge": {
                                            "from": node_id,
                                            "to": new_node_id
                                        }
                                    })
                                    operations.append({
                                        "operation": "ADD_EDGE",
                                        "edge": {
                                            "from": new_node_id,
                                            "to": "node_5"
                                        }
                                    })
        
        # 标记下一批待执行的节点
        for node in task_graph["nodes"]:
            if node["status"] == "pending":
                # 检查所有依赖是否已完成
                dependencies_completed = all(
                    any(n["id"] == dep and n["status"] == "completed" for n in task_graph["nodes"])
                    for dep in node["dependencies"]
                )
                if dependencies_completed:
                    operations.append({
                        "operation": "UPDATE_NODE",
                        "node_id": node["id"],
                        "updates": {
                            "status": "in_progress"
                        }
                    })
        
        return operations
