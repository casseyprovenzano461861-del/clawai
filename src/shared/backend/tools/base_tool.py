# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
工具基类模块
提供统一的工具接口和基础功能，支持真实执行与模拟执行的自动切换
"""

import subprocess
import json
import os
import sys
import shutil
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ToolExecutionMode(Enum):
    """工具执行模式"""
    REAL = "real"
    SIMULATED = "simulated"
    HYBRID = "hybrid"
    ERROR = "error"


class ToolCategory(Enum):
    """工具类别"""
    NETWORK_SCAN = "network_scan"
    WEB_VULN = "web_vuln"
    DIR_BRUTE = "dir_brute"
    INFO_GATHERING = "info_gathering"
    PASSWORD_CRACKING = "password_cracking"
    POST_EXPLOITATION = "post_exploitation"
    SECURITY_TESTING = "security_testing"
    OTHER = "other"


class ToolPriority(Enum):
    """工具优先级"""
    CRITICAL = 1  # 必需工具
    HIGH = 2     # 重要工具
    MEDIUM = 3   # 推荐工具
    LOW = 4      # 可选工具


@dataclass
class ToolExecutionResult:
    """工具执行结果"""
    target: str
    tool_name: str
    execution_mode: ToolExecutionMode
    output: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    execution_time: Optional[float] = None
    attempts: int = 1
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result["execution_mode"] = self.execution_mode.value
        return result


class BaseTool(ABC):
    """工具基类"""
    
    def __init__(self, 
                 tool_name: str, 
                 command: str, 
                 description: str,
                 category: ToolCategory,
                 priority: ToolPriority = ToolPriority.MEDIUM,
                 requires_installation: bool = True,
                 fallback_to_simulated: bool = True):
        """
        初始化工具
        
        Args:
            tool_name: 工具名称（唯一标识）
            command: 工具可执行文件路径或命令名
            description: 工具描述
            category: 工具类别
            priority: 工具优先级
            requires_installation: 是否需要安装
            fallback_to_simulated: 是否允许降级到模拟执行
        """
        self.tool_name = tool_name
        self.command = command
        self.description = description
        self.category = category
        self.priority = priority
        self.requires_installation = requires_installation
        self.fallback_to_simulated = fallback_to_simulated
        
        # 执行状态
        self._installed = None
        self._working = None
        self._version = None
    
    def _check_installation(self) -> Tuple[bool, bool, Optional[str]]:
        """检查工具安装状态
        
        Returns:
            Tuple[bool, bool, Optional[str]]: (是否安装, 是否工作, 版本信息)
        """
        # 缓存检查结果
        if self._installed is not None:
            return self._installed, self._working, self._version
        
        is_installed = shutil.which(self.command) is not None
        
        if not is_installed:
            self._installed = False
            self._working = False
            self._version = None
            return False, False, None
        
        # 测试工具是否工作
        is_working = False
        version_info = ""
        
        try:
            # 尝试运行工具帮助命令
            test_cmd = self._get_test_command()
            result = subprocess.run(
                test_cmd,
                capture_output=True,
                text=True,
                timeout=5,
                encoding='utf-8',
                errors='ignore'
            )
            
            # 很多工具用返回码1显示版本信息
            if result.returncode == 0 or result.returncode == 1:
                is_working = True
                version_output = result.stdout if result.stdout else result.stderr
                version_info = self._parse_version(version_output)
                
                if not version_info:
                    version_info = f"版本未知（命令返回码: {result.returncode}）"
            else:
                logger.warning(f"工具 {self.tool_name} 测试失败，返回码: {result.returncode}")
        
        except (subprocess.TimeoutExpired, Exception) as e:
            logger.warning(f"工具 {self.tool_name} 测试异常: {str(e)}")
        
        self._installed = is_installed
        self._working = is_working
        self._version = version_info
        
        return is_installed, is_working, version_info
    
    def _get_test_command(self) -> List[str]:
        """获取测试工具是否工作的命令"""
        # 默认使用 --version 或 -v 测试
        if self.command == "python" or self.command.endswith("python"):
            return [self.command, "--version"]
        elif "nikto" in self.command.lower():
            return [self.command, "-Version"]
        elif "ffuf" in self.command.lower():
            return [self.command, "-V"]
        else:
            return [self.command, "--version"]
    
    def _parse_version(self, output: str) -> str:
        """解析版本信息"""
        if not output:
            return ""
        
        # 尝试提取版本号
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            # 匹配常见的版本格式
            version_patterns = [
                r'(\d+\.\d+\.\d+)',  # 1.2.3
                r'(\d+\.\d+)',       # 1.2
                r'v(\d+\.\d+\.\d+)', # v1.2.3
                r'version\s+(\d+\.\d+\.\d+)',  # version 1.2.3
            ]
            
            for pattern in version_patterns:
                match = re.search(pattern, line)
                if match:
                    return match.group(1) if '.' in match.group(0) else match.group(0)
        
        # 如果没找到版本号，返回第一行
        return lines[0][:50] if lines else ""
    
    def is_available(self) -> bool:
        """检查工具是否可用（已安装且工作）"""
        _, is_working, _ = self._check_installation()
        return is_working
    
    def get_status(self) -> Dict[str, Any]:
        """获取工具状态信息"""
        is_installed, is_working, version = self._check_installation()
        
        return {
            "tool_name": self.tool_name,
            "command": self.command,
            "description": self.description,
            "category": self.category.value,
            "priority": self.priority.value,
            "installed": is_installed,
            "working": is_working,
            "version": version,
            "available": is_working,
            "requires_installation": self.requires_installation,
            "fallback_to_simulated": self.fallback_to_simulated
        }
    
    def _run_command(self, 
                    args: List[str], 
                    timeout: int = 300, 
                    capture_output: bool = True) -> subprocess.CompletedProcess:
        """运行命令
        
        Args:
            args: 命令参数列表
            timeout: 超时时间（秒）
            capture_output: 是否捕获输出
            
        Returns:
            subprocess.CompletedProcess对象
        """
        try:
            return subprocess.run(
                args,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='ignore'
            )
        except subprocess.TimeoutExpired as e:
            logger.error(f"工具 {self.tool_name} 执行超时: {str(e)}")
            raise
        except FileNotFoundError as e:
            logger.error(f"未找到工具 {self.tool_name} 命令: {self.command}")
            raise
        except Exception as e:
            logger.error(f"工具 {self.tool_name} 执行错误: {str(e)}")
            raise
    
    def _execute_real(self, target: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """真实执行工具（子类必须实现）
        
        Args:
            target: 目标地址
            options: 执行选项
            
        Returns:
            执行结果字典
        """
        raise NotImplementedError("子类必须实现 _execute_real 方法")
    
    def _simulate_execution(self, target: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """模拟执行工具（子类可以实现）
        
        Args:
            target: 目标地址
            options: 执行选项
            
        Returns:
            模拟执行结果
        """
        # 默认实现：返回简单的模拟结果
        logger.warning(f"工具 {self.tool_name} 使用模拟执行模式")
        
        return {
            "target": target,
            "simulated": True,
            "message": f"工具 {self.tool_name} 未安装或不可用，使用模拟数据",
            "note": "这是模拟数据，仅供测试使用"
        }
    
    def execute(self, 
                target: str, 
                options: Optional[Dict] = None,
                max_retries: int = 1) -> ToolExecutionResult:
        """执行工具
        
        Args:
            target: 目标地址
            options: 执行选项
            max_retries: 最大重试次数
            
        Returns:
            ToolExecutionResult对象
        """
        import time
        
        if options is None:
            options = {}
        
        result = None
        last_error = None
        attempts = 0
        
        for attempt in range(max_retries + 1):
            attempts += 1
            start_time = time.time()
            
            try:
                # 检查工具是否可用
                is_available = self.is_available()
                
                if is_available or not self.fallback_to_simulated:
                    # 真实执行
                    output = self._execute_real(target, options)
                    execution_mode = ToolExecutionMode.REAL
                else:
                    # 降级到模拟执行
                    if attempt > 0:
                        # 重试时等待一段时间
                        time.sleep(2 ** attempt)
                    
                    output = self._simulate_execution(target, options)
                    execution_mode = ToolExecutionMode.SIMULATED
                
                end_time = time.time()
                
                result = ToolExecutionResult(
                    target=target,
                    tool_name=self.tool_name,
                    execution_mode=execution_mode,
                    output=output,
                    success=True,
                    start_time=start_time,
                    end_time=end_time,
                    execution_time=end_time - start_time,
                    attempts=attempts,
                    retry_count=attempt
                )
                
                logger.info(f"工具 {self.tool_name} 执行成功，模式: {execution_mode.value}，耗时: {result.execution_time:.2f}秒")
                break
                
            except subprocess.TimeoutExpired as e:
                end_time = time.time()
                error_msg = f"工具执行超时: {str(e)}"
                last_error = e
                
                result = ToolExecutionResult(
                    target=target,
                    tool_name=self.tool_name,
                    execution_mode=ToolExecutionMode.ERROR,
                    output={},
                    success=False,
                    error_message=error_msg,
                    start_time=start_time,
                    end_time=end_time,
                    execution_time=end_time - start_time,
                    attempts=attempts,
                    retry_count=attempt
                )
                
                logger.warning(f"工具 {self.tool_name} 超时，尝试 {attempt}/{max_retries}")
                
            except Exception as e:
                end_time = time.time()
                error_msg = f"执行错误: {str(e)}"
                last_error = e
                
                result = ToolExecutionResult(
                    target=target,
                    tool_name=self.tool_name,
                    execution_mode=ToolExecutionMode.ERROR,
                    output={},
                    success=False,
                    error_message=error_msg,
                    start_time=start_time,
                    end_time=end_time,
                    execution_time=end_time - start_time,
                    attempts=attempts,
                    retry_count=attempt
                )
                
                logger.error(f"工具 {self.tool_name} 执行失败: {error_msg}")
        
        # 如果所有尝试都失败
        if result is None or not result.success:
            if result is None:
                # 创建错误结果
                result = ToolExecutionResult(
                    target=target,
                    tool_name=self.tool_name,
                    execution_mode=ToolExecutionMode.ERROR,
                    output={},
                    success=False,
                    error_message=f"所有重试都失败: {last_error}" if last_error else "未知错误",
                    attempts=attempts,
                    retry_count=max_retries
                )
            
            # 如果允许降级，尝试模拟执行
            if self.fallback_to_simulated and result.execution_mode == ToolExecutionMode.ERROR:
                try:
                    simulated_output = self._simulate_execution(target, options)
                    result.output = simulated_output
                    result.execution_mode = ToolExecutionMode.SIMULATED
                    result.success = True  # 模拟执行视为成功
                    result.error_message = None
                    logger.info(f"工具 {self.tool_name} 降级到模拟执行成功")
                except Exception as e:
                    logger.error(f"工具 {self.tool_name} 模拟执行也失败: {str(e)}")
        
        return result
    
    @abstractmethod
    def run(self, target: str) -> Dict[str, Any]:
        """执行工具（兼容旧接口）
        
        Args:
            target: 目标地址
            
        Returns:
            结果字典
        """
        pass


# 工具工厂类
class ToolFactory:
    """工具工厂，用于创建和管理工具实例"""
    
    _tools_registry = {}
    
    @classmethod
    def register_tool(cls, tool_class):
        """注册工具类"""
        tool_name = getattr(tool_class, 'tool_name', None) or tool_class.__name__.replace('Tool', '').lower()
        cls._tools_registry[tool_name] = tool_class
        logger.info(f"注册工具: {tool_name} -> {tool_class.__name__}")
        return tool_class
    
    @classmethod
    def create_tool(cls, tool_name: str, *args, **kwargs):
        """创建工具实例"""
        if tool_name not in cls._tools_registry:
            raise ValueError(f"工具 {tool_name} 未注册")
        
        tool_class = cls._tools_registry[tool_name]
        return tool_class(*args, **kwargs)
    
    @classmethod
    def get_available_tools(cls) -> List[str]:
        """获取所有已注册的工具名称"""
        return list(cls._tools_registry.keys())
    
    @classmethod
    def create_all_tools(cls) -> Dict[str, BaseTool]:
        """创建所有已注册的工具实例"""
        tools = {}
        for tool_name in cls.get_available_tools():
            try:
                tools[tool_name] = cls.create_tool(tool_name)
            except Exception as e:
                logger.error(f"创建工具 {tool_name} 失败: {str(e)}")
        
        return tools


# 工具装饰器
def register_tool(tool_class):
    """工具类装饰器，用于自动注册"""
    return ToolFactory.register_tool(tool_class)


# 导入re模块用于版本解析
import re

# 测试函数
def main():
    """测试工具基类"""
    print("测试工具基类...")
    
    # 创建一个测试工具类
    @register_tool
    class TestTool(BaseTool):
        def __init__(self):
            super().__init__(
                tool_name="test",
                command="python",
                description="测试工具",
                category=ToolCategory.OTHER,
                priority=ToolPriority.LOW,
                requires_installation=True,
                fallback_to_simulated=True
            )
        
        def _execute_real(self, target: str, options: Optional[Dict] = None) -> Dict[str, Any]:
            """真实执行测试工具"""
            result = self._run_command(["python", "--version"])
            return {
                "target": target,
                "python_version": result.stdout.strip(),
                "return_code": result.returncode
            }
        
        def _simulate_execution(self, target: str, options: Optional[Dict] = None) -> Dict[str, Any]:
            """模拟执行测试工具"""
            return {
                "target": target,
                "python_version": "Python 3.9.0 (simulated)",
                "simulated": True
            }
        
        def run(self, target: str) -> Dict[str, Any]:
            """兼容旧接口"""
            result = self.execute(target)
            return result.output
    
    # 测试工具工厂
    print(f"已注册工具: {ToolFactory.get_available_tools()}")
    
    # 创建测试工具
    try:
        test_tool = ToolFactory.create_tool("test")
        print(f"\n工具状态: {test_tool.get_status()}")
        
        # 执行测试
        test_result = test_tool.execute("test_target")
        print(f"\n执行结果: {json.dumps(test_result.to_dict(), indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
    
    print("\n测试完成！")


if __name__ == "__main__":
    main()