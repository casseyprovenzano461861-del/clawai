# -*- coding: utf-8 -*-
"""
GraphManager模块 - 任务图管理器
负责任务图的状态管理、拓扑排序和依赖解析
"""

import json
from typing import Dict, Any, List, Optional


class GraphManager:
    """图管理器类"""
    
    def __init__(self):
        self.task_graphs = {}
    
    def create_task_graph(self, goal: str) -> str:
        """创建任务图"""
        task_id = f"task_{len(self.task_graphs) + 1}"
        task_graph = {
            "id": task_id,
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
        
        self.task_graphs[task_id] = task_graph
        return task_id
    
    def get_task_graph(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务图"""
        return self.task_graphs.get(task_id)
    
    def update_task_graph(self, task_id: str, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """更新任务图"""
        task_graph = self.get_task_graph(task_id)
        if not task_graph:
            raise ValueError(f"任务图 {task_id} 不存在")
        
        for operation in operations:
            op_type = operation.get("operation")
            
            if op_type == "ADD_NODE":
                node = operation.get("node")
                if node:
                    task_graph["nodes"].append(node)
            
            elif op_type == "UPDATE_NODE":
                node_id = operation.get("node_id")
                updates = operation.get("updates", {})
                if node_id:
                    for node in task_graph["nodes"]:
                        if node["id"] == node_id:
                            node.update(updates)
                            break
            
            elif op_type == "ADD_EDGE":
                edge = operation.get("edge")
                if edge:
                    task_graph["edges"].append(edge)
            
            elif op_type == "DEPRECATE_NODE":
                node_id = operation.get("node_id")
                if node_id:
                    for node in task_graph["nodes"]:
                        if node["id"] == node_id:
                            node["status"] = "deprecated"
                            break
        
        return task_graph
    
    def get_ready_nodes(self, task_id: str) -> List[Dict[str, Any]]:
        """获取可执行的节点"""
        task_graph = self.get_task_graph(task_id)
        if not task_graph:
            return []
        
        ready_nodes = []
        for node in task_graph["nodes"]:
            if node["status"] == "pending":
                # 检查所有依赖是否已完成
                dependencies_completed = all(
                    any(n["id"] == dep and n["status"] == "completed" for n in task_graph["nodes"])
                    for dep in node["dependencies"]
                )
                if dependencies_completed:
                    ready_nodes.append(node)
        
        return ready_nodes
    
    def get_in_progress_nodes(self, task_id: str) -> List[Dict[str, Any]]:
        """获取正在执行的节点"""
        task_graph = self.get_task_graph(task_id)
        if not task_graph:
            return []
        
        return [node for node in task_graph["nodes"] if node["status"] == "in_progress"]
    
    def get_completed_nodes(self, task_id: str) -> List[Dict[str, Any]]:
        """获取已完成的节点"""
        task_graph = self.get_task_graph(task_id)
        if not task_graph:
            return []
        
        return [node for node in task_graph["nodes"] if node["status"] == "completed"]
    
    def get_failed_nodes(self, task_id: str) -> List[Dict[str, Any]]:
        """获取失败的节点"""
        task_graph = self.get_task_graph(task_id)
        if not task_graph:
            return []
        
        return [node for node in task_graph["nodes"] if node["status"] == "failed"]
    
    def topological_sort(self, task_id: str) -> List[str]:
        """拓扑排序"""
        task_graph = self.get_task_graph(task_id)
        if not task_graph:
            return []
        
        # 构建依赖关系
        dependencies = {}
        for node in task_graph["nodes"]:
            dependencies[node["id"]] = node["dependencies"]
        
        # Kahn算法进行拓扑排序
        in_degree = {node["id"]: 0 for node in task_graph["nodes"]}
        for node_id, deps in dependencies.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1
        
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            
            for n in task_graph["nodes"]:
                if node_id in n["dependencies"]:
                    in_degree[n["id"]] -= 1
                    if in_degree[n["id"]] == 0:
                        queue.append(n["id"])
        
        return result
    
    def get_parallel_tasks(self, task_id: str) -> List[List[str]]:
        """获取可并行执行的任务组"""
        task_graph = self.get_task_graph(task_id)
        if not task_graph:
            return []
        
        # 构建依赖关系
        dependencies = {}
        for node in task_graph["nodes"]:
            dependencies[node["id"]] = node["dependencies"]
        
        # 计算每个节点的入度
        in_degree = {node["id"]: 0 for node in task_graph["nodes"]}
        for node_id, deps in dependencies.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1
        
        # 广度优先搜索，分组可并行的任务
        parallel_groups = []
        visited = set()
        
        while True:
            # 找到当前入度为0且未访问的节点
            current_group = [node_id for node_id, degree in in_degree.items() if degree == 0 and node_id not in visited]
            
            if not current_group:
                break
            
            parallel_groups.append(current_group)
            
            # 标记为已访问，并更新依赖节点的入度
            for node_id in current_group:
                visited.add(node_id)
                for n in task_graph["nodes"]:
                    if node_id in n["dependencies"]:
                        in_degree[n["id"]] -= 1
        
        return parallel_groups
    
    def is_task_complete(self, task_id: str) -> bool:
        """检查任务是否完成"""
        task_graph = self.get_task_graph(task_id)
        if not task_graph:
            return False
        
        # 检查所有节点是否都已完成或废弃
        for node in task_graph["nodes"]:
            if node["status"] not in ["completed", "deprecated"]:
                return False
        
        return True
    
    def get_task_status(self, task_id: str) -> str:
        """获取任务状态"""
        task_graph = self.get_task_graph(task_id)
        if not task_graph:
            return "not_found"
        
        if self.is_task_complete(task_id):
            return "completed"
        
        failed_nodes = self.get_failed_nodes(task_id)
        if failed_nodes:
            return "failed"
        
        in_progress_nodes = self.get_in_progress_nodes(task_id)
        if in_progress_nodes:
            return "in_progress"
        
        return "pending"
