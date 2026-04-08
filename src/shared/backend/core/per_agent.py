# -*- coding: utf-8 -*-
"""
PERAgent模块 - P-E-R协作框架主入口
集成Planner、Executor和Reflector，形成完整的智能安全评估系统
"""

import json
from typing import Dict, Any
from .planner import Planner
from .executor import Executor
from .reflector import Reflector
from .graph_manager import GraphManager
from .events import event_broker, EventType
from .tool_manager import ToolManager
from .llm_client import LLMClient


class PERAgent:
    """P-E-R协作框架代理类"""
    
    def __init__(self):
        # 初始化组件
        self.llm_client = LLMClient()
        self.tool_manager = ToolManager()
        self.graph_manager = GraphManager()
        self.planner = Planner(self.llm_client)
        self.executor = Executor(self.tool_manager)
        self.reflector = Reflector(self.llm_client)
        
        # 订阅事件
        self._subscribe_events()
    
    def _subscribe_events(self):
        """订阅事件"""
        event_broker.subscribe(EventType.TASK_CREATED, self._on_task_created)
        event_broker.subscribe(EventType.NODE_COMPLETED, self._on_node_completed)
        event_broker.subscribe(EventType.TASK_COMPLETED, self._on_task_completed)
    
    def _on_task_created(self, data: Dict[str, Any]):
        """任务创建事件处理"""
        print(f"任务创建: {data.get('task_id')}")
    
    def _on_node_completed(self, data: Dict[str, Any]):
        """节点完成事件处理"""
        print(f"节点完成: {data.get('node_id')}")
    
    def _on_task_completed(self, data: Dict[str, Any]):
        """任务完成事件处理"""
        print(f"任务完成: {data.get('task_id')}")
    
    def run(self, goal: str) -> Dict[str, Any]:
        """运行P-E-R协作框架"""
        print(f"开始执行任务: {goal}")
        # 创建任务图
        task_id = self.graph_manager.create_task_graph(goal)
        print(f"创建任务图: {task_id}")
        event_broker.publish(EventType.TASK_CREATED, {"task_id": task_id})
        
        # 主循环
        iteration = 0
        while iteration < 10:  # 限制迭代次数
            iteration += 1
            print(f"\n迭代 {iteration}")
            # 获取任务图
            task_graph = self.graph_manager.get_task_graph(task_id)
            if not task_graph:
                print("任务图不存在，退出")
                break
            
            # 检查任务是否完成
            if self.graph_manager.is_task_complete(task_id):
                print("任务已完成，退出")
                break
            
            # 获取可执行的节点
            ready_nodes = self.graph_manager.get_ready_nodes(task_id)
            print(f"可执行的节点: {[node['id'] for node in ready_nodes]}")
            if not ready_nodes:
                print("没有可执行的节点，退出")
                break
            
            # 处理每个可执行的节点
            for node in ready_nodes:
                print(f"处理节点: {node['id']} - {node['label']}")
                # 执行节点
                event_broker.publish(EventType.NODE_STARTED, {"node_id": node["id"]})
                
                # 执行任务
                print("执行任务...")
                execution_result = self.executor.execute_task(node, task_graph)
                print(f"执行结果: {execution_result}")
                
                # 分析执行结果
                print("分析执行结果...")
                analysis = self.reflector.analyze_execution(node, execution_result)
                print(f"分析结果: {analysis}")
                event_broker.publish(EventType.ANALYSIS_COMPLETED, analysis)
                
                # 更新节点状态
                operations = []
                if "error" in execution_result:
                    operations.append({
                        "operation": "UPDATE_NODE",
                        "node_id": node["id"],
                        "updates": {
                            "status": "failed",
                            "output": execution_result
                        }
                    })
                    event_broker.publish(EventType.NODE_FAILED, {"node_id": node["id"], "error": execution_result["error"]})
                else:
                    operations.append({
                        "operation": "UPDATE_NODE",
                        "node_id": node["id"],
                        "updates": {
                            "status": "completed",
                            "output": execution_result
                        }
                    })
                    event_broker.publish(EventType.NODE_COMPLETED, {"node_id": node["id"]})
                
                # 生成新的规划
                print("生成新的规划...")
                execution_results = {node["id"]: execution_result}
                plan_operations = self.planner.generate_plan(task_graph, execution_results)
                print(f"规划操作: {plan_operations}")
                operations.extend(plan_operations)
                
                # 更新任务图
                print("更新任务图...")
                self.graph_manager.update_task_graph(task_id, operations)
                event_broker.publish(EventType.TASK_UPDATED, {"task_id": task_id})
        
        # 生成攻击情报
        task_graph = self.graph_manager.get_task_graph(task_id)
        intelligence = self.reflector.generate_intelligence(task_graph)
        event_broker.publish(EventType.INTELLIGENCE_GENERATED, intelligence)
        
        # 标记任务完成
        event_broker.publish(EventType.TASK_COMPLETED, {"task_id": task_id})
        
        return {
            "task_id": task_id,
            "task_graph": task_graph,
            "intelligence": intelligence
        }


def main():
    """主函数"""
    agent = PERAgent()
    
    # 运行示例任务
    goal = "对127.0.0.1进行全面的安全测试"
    result = agent.run(goal)
    
    # 打印结果
    print("\n=== 任务执行结果 ===")
    print(f"任务ID: {result['task_id']}")
    print(f"任务状态: {agent.graph_manager.get_task_status(result['task_id'])}")
    
    print("\n=== 攻击情报 ===")
    print(json.dumps(result['intelligence'], indent=2, ensure_ascii=False))
    
    print("\n=== 任务图 ===")
    print(json.dumps(result['task_graph'], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
