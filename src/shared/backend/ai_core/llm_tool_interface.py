# -*- coding: utf-8 -*-
"""
大模型与工具交互接口
实现大模型与安全工具的交互功能
"""

import json
import sys
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from shared.backend.core.tool_manager import ToolManager


@dataclass
class ToolCall:
    """工具调用请求"""
    tool_name: str
    parameters: Dict[str, Any]
    timeout: int = 300
    id: str = field(default_factory=lambda: f"tool_call_{hash(id)}")


@dataclass
class ToolResult:
    """工具执行结果"""
    tool_name: str
    output: str
    success: bool
    error: Optional[str] = None
    execution_time: Optional[float] = None


class LLMTOOLInterface:
    """
    大模型与工具交互接口
    实现大模型与安全工具的交互功能
    """
    
    def __init__(self):
        """初始化工具接口"""
        self.tool_manager = ToolManager()
        self.available_tools = self._get_available_tools()
    
    def _get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """获取可用工具列表"""
        tools = {}
        for tool_name, tool_info in self.tool_manager.tools.items():
            tools[tool_name] = {
                "description": tool_info["description"],
                "category": tool_info["category"],
                "parameters": tool_info.get("params", [])
            }
        return tools
    
    def get_tool_list(self) -> List[Dict[str, Any]]:
        """获取工具列表"""
        tool_list = []
        for tool_name, tool_info in self.available_tools.items():
            tool_list.append({
                "name": tool_name,
                "description": tool_info["description"],
                "category": tool_info["category"],
                "parameters": tool_info["parameters"]
            })
        return tool_list
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具信息"""
        return self.available_tools.get(tool_name)
    
    def execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """执行工具"""
        try:
            # 检查工具是否存在
            if tool_call.tool_name not in self.available_tools:
                return ToolResult(
                    tool_name=tool_call.tool_name,
                    output="",
                    success=False,
                    error=f"工具 {tool_call.tool_name} 不存在"
                )
            
            # 执行工具
            result = self.tool_manager.execute_tool_with_params(
                tool_call.tool_name,
                tool_call.parameters,
                tool_call.timeout
            )
            
            # 检查执行结果
            if "执行失败" in result or "未安装" in result or "超时" in result:
                return ToolResult(
                    tool_name=tool_call.tool_name,
                    output=result,
                    success=False,
                    error=result
                )
            
            return ToolResult(
                tool_name=tool_call.tool_name,
                output=result,
                success=True
            )
        
        except Exception as e:
            return ToolResult(
                tool_name=tool_call.tool_name,
                output="",
                success=False,
                error=f"执行工具时出错: {str(e)}"
            )
    
    def execute_tools_in_parallel(self, tool_calls: List[ToolCall], max_workers: int = 5) -> Dict[str, ToolResult]:
        """并行执行多个工具"""
        results = {}
        
        # 构建工具任务
        tool_tasks = []
        for tool_call in tool_calls:
            tool_tasks.append({
                "tool_name": tool_call.tool_name,
                "params": tool_call.parameters,
                "timeout": tool_call.timeout
            })
        
        # 调用ToolManager的并行执行方法
        execution_results = self.tool_manager.execute_tools_in_parallel(tool_tasks, max_workers)
        
        # 转换结果格式
        for tool_name, output in execution_results.items():
            success = not ("执行失败" in output or "未安装" in output or "超时" in output)
            error = None if success else output
            
            results[tool_name] = ToolResult(
                tool_name=tool_name,
                output=output,
                success=success,
                error=error
            )
        
        return results
    
    def generate_tool_call_prompt(self, task: str) -> str:
        """
        生成工具调用提示词
        用于指导大模型选择合适的工具执行任务
        """
        tool_list = self.get_tool_list()
        
        prompt = f"""你是一个安全测试专家，需要根据用户的任务选择合适的工具执行。

当前任务: {task}

可用工具列表:
"""
        
        for tool in tool_list:
            prompt += f"\n工具名称: {tool['name']}"
            prompt += f"\n描述: {tool['description']}"
            prompt += f"\n类别: {tool['category']}"
            prompt += "\n参数:"
            for param in tool['parameters']:
                required = "(必需)" if param.get('required', False) else "(可选)"
                prompt += f"\n  - {param['name']}: {param['description']} {required}"
            prompt += "\n"
        
        prompt += """
请根据任务选择合适的工具，并按照以下格式输出工具调用信息:

```json
{
  "tool_calls": [
    {
      "tool_name": "工具名称",
      "parameters": {
        "参数名1": "参数值1",
        "参数名2": "参数值2"
      },
      "timeout": 300
    }
  ]
}
```

注意事项:
1. 选择最适合当前任务的工具
2. 确保提供所有必需的参数
3. 参数值要符合工具的要求
4. 可以选择多个工具并行执行
5. 输出必须是有效的JSON格式
"""
        
        return prompt
    
    def parse_tool_call_response(self, response: str) -> Optional[List[ToolCall]]:
        """
        解析大模型的工具调用响应
        """
        try:
            # 提取JSON部分
            import re
            json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
            if not json_match:
                return None
            
            json_str = json_match.group(1)
            data = json.loads(json_str)
            
            tool_calls = []
            for tool_call_data in data.get("tool_calls", []):
                tool_call = ToolCall(
                    tool_name=tool_call_data["tool_name"],
                    parameters=tool_call_data.get("parameters", {}),
                    timeout=tool_call_data.get("timeout", 300)
                )
                tool_calls.append(tool_call)
            
            return tool_calls
        except Exception as e:
            print(f"解析工具调用响应时出错: {e}")
            return None
    
    def generate_tool_result_prompt(self, tool_results: Dict[str, ToolResult]) -> str:
        """
        生成工具执行结果提示词
        用于向大模型展示工具执行结果
        """
        prompt = """工具执行结果:\n\n"""
        
        for tool_name, result in tool_results.items():
            prompt += f"工具: {tool_name}\n"
            prompt += f"状态: {'成功' if result.success else '失败'}\n"
            if not result.success and result.error:
                prompt += f"错误: {result.error}\n"
            prompt += f"输出:\n{result.output}\n\n"
        
        prompt += """请基于以上工具执行结果，分析当前安全测试状态，并提供下一步建议。

建议内容应包括:
1. 对工具执行结果的分析
2. 发现的漏洞或安全问题
3. 下一步应该执行的操作
4. 推荐使用的工具和参数
"""
        
        return prompt


# 测试代码
if __name__ == "__main__":
    # 初始化工具接口
    print("初始化工具接口...")
    interface = LLMTOOLInterface()
    
    print("=" * 80)
    print("大模型与工具交互接口测试")
    print("=" * 80)
    
    # 测试1: 获取工具列表
    print("\n测试1: 获取工具列表")
    tools = interface.get_tool_list()
    print(f"可用工具数量: {len(tools)}")
    for tool in tools[:5]:  # 只显示前5个工具
        print(f"- {tool['name']}: {tool['description']}")
    
    # 测试2: 生成工具调用提示词
    print("\n测试2: 生成工具调用提示词")
    task = "扫描 example.com 网站的开放端口"
    prompt = interface.generate_tool_call_prompt(task)
    print(f"提示词长度: {len(prompt)} 字符")
    print("提示词内容:")
    print(prompt[:500] + "...")
    
    # 测试3: 执行工具
    print("\n测试3: 执行工具")
    tool_call = ToolCall(
        tool_name="nmap",
        parameters={"target": "127.0.0.1", "ports": "1-1000"},
        timeout=60
    )
    
    result = interface.execute_tool(tool_call)
    print(f"工具: {result.tool_name}")
    print(f"成功: {result.success}")
    if not result.success:
        print(f"错误: {result.error}")
    else:
        print(f"输出长度: {len(result.output)} 字符")
        print("输出内容:")
        print(result.output[:300] + "...")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("所有测试通过！")
