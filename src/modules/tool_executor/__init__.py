"""
工具执行模块
安全工具执行和管理
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from pydantic import BaseModel, Field
import logging
import uuid
import time

from .. import BaseModule, ModuleConfig

logger = logging.getLogger(__name__)


class ToolExecutorConfig(BaseModel):
    """工具执行配置"""
    tools_dir: str = "./tools/penetration"
    container_timeout: int = 300
    enabled: bool = True
    max_concurrent_tasks: int = 5


# Pydantic模型
class ToolExecuteRequest(BaseModel):
    """工具执行请求"""
    tool_name: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)
    parameters: Dict[str, Any] = {}
    timeout: Optional[int] = None


class ToolExecutionResult(BaseModel):
    """工具执行结果"""
    task_id: str
    tool_name: str
    target: str
    status: str
    output: Optional[str] = None
    error: Optional[str] = None
    exit_code: Optional[int] = None
    duration: Optional[float] = None
    created_at: float
    completed_at: Optional[float] = None


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    progress: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float
    updated_at: float


class ToolInfo(BaseModel):
    """工具信息"""
    name: str
    description: str
    category: str
    command_template: str
    parameters: List[Dict[str, Any]]
    supported_targets: List[str]


class ToolExecutorModule(BaseModule):
    """工具执行模块"""

    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        self.tool_config = ToolExecutorConfig(**config.config)
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.tool_loader = None
        self.task_queue = []

    def _setup_routes(self) -> None:
        """设置工具执行路由"""

        @self.router.get("/health")
        async def health_check():
            """工具执行服务健康检查"""
            return {
                "service": "tool_executor",
                "status": "healthy" if self._setup_complete else "unhealthy",
                "tools_loaded": self.tool_loader is not None,
                "active_tasks": len([t for t in self.tasks.values() if t["status"] in ["running", "pending"]]),
                "total_tools": len(self._get_available_tools())
            }

        @self.router.get("/tools/available")
        async def get_available_tools():
            """获取可用工具列表"""
            try:
                tools = self._get_available_tools()
                return {
                    "tools": tools,
                    "total": len(tools)
                }
            except Exception as e:
                logger.error(f"获取工具列表失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"获取工具列表失败: {str(e)}"
                )

        @self.router.post("/tools/execute", response_model=ToolExecutionResult)
        async def execute_tool(
            request: ToolExecuteRequest,
            background_tasks: BackgroundTasks
        ):
            """执行工具"""
            try:
                # 验证工具是否存在
                available_tools = self._get_available_tools()
                tool_names = [t["name"] for t in available_tools]

                if request.tool_name not in tool_names:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"工具不存在: {request.tool_name}"
                    )

                # 创建任务
                task_id = str(uuid.uuid4())
                created_at = time.time()

                task = {
                    "task_id": task_id,
                    "tool_name": request.tool_name,
                    "target": request.target,
                    "parameters": request.parameters,
                    "status": "pending",
                    "created_at": created_at,
                    "timeout": request.timeout or self.tool_config.container_timeout
                }

                self.tasks[task_id] = task

                # 将任务添加到后台执行
                background_tasks.add_task(
                    self._execute_tool_task,
                    task_id
                )

                return ToolExecutionResult(
                    task_id=task_id,
                    tool_name=request.tool_name,
                    target=request.target,
                    status="pending",
                    created_at=created_at
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"创建工具执行任务失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"创建任务失败: {str(e)}"
                )

        @self.router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
        async def get_task_status(task_id: str):
            """获取任务状态"""
            if task_id not in self.tasks:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"任务不存在: {task_id}"
                )

            task = self.tasks[task_id]
            response = TaskStatusResponse(
                task_id=task_id,
                status=task["status"],
                created_at=task["created_at"],
                updated_at=task.get("updated_at", task["created_at"])
            )

            if "progress" in task:
                response.progress = task["progress"]

            if task["status"] == "completed" and "result" in task:
                response.result = task["result"]

            if task["status"] == "failed" and "error" in task:
                response.error = task["error"]

            return response

    def _get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        # 这里需要实际的工具发现逻辑
        # 暂时返回模拟工具列表
        return [
            {
                "name": "nmap",
                "description": "网络发现和安全审计工具",
                "category": "reconnaissance",
                "command_template": "nmap -sV -sC {target}",
                "parameters": [
                    {"name": "scan_type", "type": "string", "default": "normal", "options": ["quick", "normal", "detailed"]}
                ],
                "supported_targets": ["ip", "hostname", "network"]
            },
            {
                "name": "sqlmap",
                "description": "自动SQL注入和数据库接管工具",
                "category": "exploitation",
                "command_template": "sqlmap -u {target} --batch",
                "parameters": [
                    {"name": "level", "type": "integer", "default": 1, "min": 1, "max": 5}
                ],
                "supported_targets": ["url"]
            },
            {
                "name": "dirsearch",
                "description": "Web路径暴力破解工具",
                "category": "reconnaissance",
                "command_template": "dirsearch -u {target} -e php,html,js",
                "parameters": [
                    {"name": "extensions", "type": "string", "default": "php,html,js"}
                ],
                "supported_targets": ["url"]
            },
            {
                "name": "nikto",
                "description": "Web服务器扫描器",
                "category": "vulnerability",
                "command_template": "nikto -h {target}",
                "parameters": [],
                "supported_targets": ["hostname", "ip"]
            },
            {
                "name": "whatweb",
                "description": "Web技术识别工具",
                "category": "reconnaissance",
                "command_template": "whatweb {target}",
                "parameters": [],
                "supported_targets": ["url"]
            }
        ]

    async def _execute_tool_task(self, task_id: str):
        """执行工具任务（后台）"""
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]
        task["status"] = "running"
        task["updated_at"] = time.time()

        try:
            logger.info(f"开始执行工具任务: {task_id} - {task['tool_name']} 对 {task['target']}")

            # 模拟工具执行
            await self._simulate_tool_execution(task_id)

            # 更新任务状态为完成
            task["status"] = "completed"
            task["updated_at"] = time.time()
            task["result"] = {
                "output": f"工具 {task['tool_name']} 执行成功",
                "exit_code": 0,
                "duration": task["updated_at"] - task["created_at"]
            }

            logger.info(f"工具任务完成: {task_id}")

        except Exception as e:
            logger.error(f"工具任务执行失败: {task_id} - {e}")
            task["status"] = "failed"
            task["updated_at"] = time.time()
            task["error"] = str(e)

    async def _simulate_tool_execution(self, task_id: str):
        """模拟工具执行（用于测试）"""
        import asyncio

        task = self.tasks[task_id]
        execution_time = 2.0  # 模拟执行时间（秒）

        # 模拟执行进度
        steps = 10
        for i in range(steps):
            await asyncio.sleep(execution_time / steps)
            progress = (i + 1) / steps
            task["progress"] = progress

        # 模拟工具输出
        if task["tool_name"] == "nmap":
            task["output"] = """Starting Nmap 7.94 ( https://nmap.org )
Nmap scan report for example.com (93.184.216.34)
Host is up (0.12s latency).
Not shown: 998 filtered ports
PORT    STATE SERVICE  VERSION
80/tcp  open  http     nginx
443/tcp open  ssl/http nginx

Nmap done: 1 IP address (1 host up) scanned in 2.34 seconds"""
        elif task["tool_name"] == "sqlmap":
            task["output"] = """[INFO] testing connection to the target URL
[INFO] checking if the target is protected by some kind of WAF/IPS
[INFO] testing if the target URL is stable
[INFO] target URL is stable
[INFO] testing if GET parameter 'id' is dynamic
[INFO] confirming that GET parameter 'id' is dynamic
[INFO] GET parameter 'id' is dynamic
[INFO] heuristic (basic) test shows that GET parameter 'id' might be injectable

[INFO] testing for SQL injection on GET parameter 'id'
[INFO] testing 'AND boolean-based blind - WHERE or HAVING clause'
[INFO] testing 'MySQL >= 5.0 boolean-based blind - Parameter replace'
[INFO] GET parameter 'id' appears to be 'MySQL >= 5.0 boolean-based blind' injectable"""
        else:
            task["output"] = f"工具 {task['tool_name']} 执行完成"

    def _initialize(self) -> None:
        """初始化工具执行模块"""
        logger.info(f"正在初始化工具执行模块: {self.name}")

        try:
            # 初始化工具加载器
            # 这里可以加载实际的工具配置
            self.tool_loader = {
                "tools_dir": self.tool_config.tools_dir,
                "initialized": True
            }
            logger.info(f"工具加载器初始化成功，工具目录: {self.tool_config.tools_dir}")
        except Exception as e:
            logger.error(f"工具加载器初始化失败: {e}")
            self.tool_loader = None

        logger.info(f"工具执行模块 {self.name} 初始化完成")

    def _cleanup(self) -> None:
        """清理工具执行模块资源"""
        logger.info(f"正在清理工具执行模块: {self.name}")

        # 取消所有正在运行的任务
        for task_id, task in self.tasks.items():
            if task["status"] in ["running", "pending"]:
                task["status"] = "cancelled"
                task["updated_at"] = time.time()
                task["error"] = "服务关闭"

        self.tasks.clear()
        logger.info(f"工具执行模块 {self.name} 清理完成")


# 模块工厂函数
def create_module(config: ModuleConfig) -> ToolExecutorModule:
    """创建工具执行模块实例"""
    return ToolExecutorModule(config)