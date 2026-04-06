"""
工具相关Pydantic模型
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

from .base import BaseSchema
from ..security.validation_integration import secure_model, get_secure_validator
from ..security.input_validation import ValidationSeverity


class ToolCategory(str, Enum):
    """工具分类枚举"""
    RECONNAISSANCE = "reconnaissance"
    VULNERABILITY_SCANNING = "vulnerability_scanning"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    REPORTING = "reporting"
    UTILITY = "utility"


class ToolStatus(str, Enum):
    """工具状态枚举"""
    AVAILABLE = "available"
    INSTALLED = "installed"
    NOT_INSTALLED = "not_installed"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


class ToolExecuteRequest(BaseSchema):
    """工具执行请求模型"""
    tool: str = Field(..., min_length=1, max_length=100, description="工具名称")
    target: str = Field(..., min_length=1, max_length=2048, description="目标地址")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
    timeout: Optional[int] = Field(default=60, ge=10, le=3600, description="超时时间（秒）")
    use_docker: bool = Field(default=True, description="是否使用Docker隔离")

    @validator('target')
    def validate_target(cls, v):
        """验证目标地址"""
        if not v:
            raise ValueError("目标地址不能为空")

        # 使用安全验证器
        validator_instance = get_secure_validator()
        result = validator_instance.validate_target(v)

        if not result.is_valid:
            # 如果验证失败但目标是URL格式，特殊处理
            # 因为安全验证器的URL验证可能太严格
            if v.startswith('http://') or v.startswith('https://'):
                # 检查是否包含威胁
                threats, severity = validator_instance._detect_threats(v)
                if threats and severity in [ValidationSeverity.HIGH, ValidationSeverity.CRITICAL]:
                    error_msg = f"目标地址包含高危威胁: {', '.join(threats)}"
                    raise ValueError(error_msg)
                # 如果没有高危威胁，接受URL
                # 清理并返回
                sanitized = validator_instance._sanitize_value(v)
                return sanitized
            else:
                error_msg = f"目标地址验证失败: {result.message}"
                if result.detected_threats:
                    error_msg += f" 威胁: {', '.join(result.detected_threats)}"
                raise ValueError(error_msg)

        return result.sanitized_value or v

    @validator('tool')
    def validate_tool(cls, v):
        """验证工具名称"""
        if not v:
            raise ValueError("工具名称不能为空")

        # 使用安全验证器检查命令注入
        validator_instance = get_secure_validator()
        threats, severity = validator_instance._detect_threats(v)

        if threats and severity in [ValidationSeverity.HIGH, ValidationSeverity.CRITICAL]:
            raise ValueError(f"工具名称包含高危威胁: {', '.join(threats)}")

        return v

    @validator('parameters', pre=True)
    def validate_parameters(cls, v):
        """验证工具参数"""
        if not isinstance(v, dict):
            raise ValueError("参数必须是字典类型")

        # 安全验证：检查参数值是否包含威胁
        validator_instance = get_secure_validator()

        for key, value in v.items():
            if isinstance(value, str):
                threats, severity = validator_instance._detect_threats(value)
                if threats and severity in [ValidationSeverity.HIGH, ValidationSeverity.CRITICAL]:
                    raise ValueError(f"参数 '{key}' 包含高危威胁: {', '.join(threats)}")

        return v


class ToolExecutionResult(BaseSchema):
    """工具执行结果模型"""
    tool: str = Field(..., description="工具名称")
    target: str = Field(..., description="目标地址")
    success: bool = Field(..., description="是否成功")
    output: Optional[str] = Field(default=None, description="标准输出")
    error: Optional[str] = Field(default=None, description="错误输出")
    exit_code: Optional[int] = Field(default=None, description="退出代码")
    duration: float = Field(default=0.0, description="执行时间（秒）")
    start_time: datetime = Field(default_factory=datetime.now, description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="执行参数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class ToolInfo(BaseSchema):
    """工具信息模型"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    category: ToolCategory = Field(..., description="工具分类")
    command: str = Field(..., description="命令模板")
    version: Optional[str] = Field(default=None, description="版本号")
    status: ToolStatus = Field(default=ToolStatus.NOT_INSTALLED, description="工具状态")
    installed: bool = Field(default=False, description="是否已安装")
    install_command: Optional[str] = Field(default=None, description="安装命令")
    health_check_command: Optional[str] = Field(default=None, description="健康检查命令")
    timeout: int = Field(default=60, description="默认超时时间（秒）")
    parameters_template: Dict[str, Any] = Field(default_factory=dict, description="参数模板")
    docker_image: Optional[str] = Field(default=None, description="Docker镜像")
    supported_os: List[str] = Field(default_factory=lambda: ["linux", "darwin"], description="支持的操作系统")


class ToolHealthCheck(BaseSchema):
    """工具健康检查模型"""
    name: str = Field(..., description="工具名称")
    healthy: bool = Field(..., description="是否健康")
    message: str = Field(..., description="健康状态消息")
    version: Optional[str] = Field(default=None, description="版本号")
    last_checked: datetime = Field(default_factory=datetime.now, description="最后检查时间")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")


class ToolsListResponse(BaseSchema):
    """工具列表响应模型"""
    tools: List[ToolInfo] = Field(default_factory=list, description="工具列表")
    categories: Dict[str, int] = Field(default_factory=dict, description="分类统计")
    total: int = Field(default=0, description="工具总数")
    installed_count: int = Field(default=0, description="已安装工具数量")
    available_count: int = Field(default=0, description="可用工具数量")


class ToolCategoryResponse(BaseSchema):
    """工具分类响应模型"""
    category: ToolCategory = Field(..., description="分类")
    tools: List[ToolInfo] = Field(default_factory=list, description="工具列表")
    count: int = Field(default=0, description="工具数量")