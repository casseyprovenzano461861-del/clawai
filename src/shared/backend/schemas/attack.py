"""
攻击相关Pydantic模型
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime
from enum import Enum

from .base import BaseSchema
from ..security.validation_integration import secure_target_validator, secure_string_validator, secure_model, get_secure_validator
from ..security.input_validation import ValidationSeverity


class AttackMode(str, Enum):
    """攻击模式枚举"""
    SIMULATION = "simulation"
    REAL = "real"
    HYBRID = "hybrid"


class RuleEngineMode(str, Enum):
    """规则引擎模式枚举"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    AUTO = "auto"


class AttackRequest(BaseSchema):
    """攻击请求模型"""
    target: str = Field(..., min_length=1, max_length=2048, description="目标地址")
    use_real: bool = Field(default=True, description="是否使用真实工具执行")
    rule_engine_mode: bool = Field(default=True, description="是否启用规则引擎")
    timeout: Optional[int] = Field(default=300, ge=30, le=3600, description="超时时间（秒）")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="额外参数")

    @validator('target')
    def validate_target(cls, v):
        """验证目标地址"""
        # 基础URL验证
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

        # 简单的格式检查
        if not (v.startswith('http://') or v.startswith('https://')):
            # 如果不是URL，尝试添加http://前缀
            v = f'http://{v}'

        return result.sanitized_value or v

    @validator('parameters', pre=True)
    def validate_parameters(cls, v):
        """验证参数"""
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


class ToolSeverity(str, Enum):
    """工具执行严重性枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttackStep(BaseSchema):
    """攻击步骤模型"""
    step: int = Field(..., ge=1, description="步骤序号")
    tool: str = Field(..., description="工具名称")
    title: str = Field(..., description="步骤标题")
    description: str = Field(..., description="步骤描述")
    duration: str = Field(..., description="执行时长")
    success: bool = Field(..., description="是否成功")
    severity: ToolSeverity = Field(default=ToolSeverity.MEDIUM, description="严重级别")
    highlight: bool = Field(default=False, description="是否高亮显示")
    details: Optional[Dict[str, Any]] = Field(default=None, description="详细结果")


class RuleEngineDecision(BaseSchema):
    """规则引擎决策模型"""
    selected_path_type: str = Field(..., description="选择的路径类型")
    selected_score: float = Field(..., ge=0, le=10, description="选择分数")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    selection_reasons: List[str] = Field(default_factory=list, description="选择原因")
    path_comparison: List[Dict[str, Any]] = Field(default_factory=list, description="路径比较")
    decision_factors: Dict[str, float] = Field(default_factory=dict, description="决策因素")


class TargetAnalysis(BaseSchema):
    """目标分析模型"""
    attack_surface: float = Field(default=0.0, ge=0, le=10, description="攻击面评分")
    open_ports: int = Field(default=0, ge=0, description="开放端口数量")
    vulnerabilities: int = Field(default=0, ge=0, description="漏洞总数")
    sql_injections: int = Field(default=0, ge=0, description="SQL注入数量")
    has_cms: bool = Field(default=False, description="是否检测到CMS")
    cms_type: Optional[str] = Field(default=None, description="CMS类型")
    cms_version: Optional[str] = Field(default=None, description="CMS版本")


class AttackResponse(BaseSchema):
    """攻击响应模型"""
    target: str = Field(..., description="目标地址")
    execution_time: str = Field(..., description="执行时间")
    execution_mode: str = Field(..., description="执行模式")
    rule_engine_used: bool = Field(..., description="是否使用规则引擎")
    rule_engine_model: str = Field(..., description="规则引擎模型")
    attack_chain: List[AttackStep] = Field(default_factory=list, description="攻击链")
    rule_engine_decision: Optional[RuleEngineDecision] = Field(default=None, description="规则引擎决策")
    target_analysis: TargetAnalysis = Field(default_factory=TargetAnalysis, description="目标分析")
    message: str = Field(default="", description="消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    success: bool = Field(default=True, description="是否成功")


class AttackStatus(str, Enum):
    """攻击状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AttackStatusResponse(BaseSchema):
    """攻击状态响应模型"""
    attack_id: str = Field(..., description="攻击ID")
    status: AttackStatus = Field(..., description="攻击状态")
    progress: float = Field(default=0.0, ge=0, le=100, description="进度百分比")
    current_step: Optional[str] = Field(default=None, description="当前步骤")
    estimated_time_remaining: Optional[str] = Field(default=None, description="预计剩余时间")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    result: Optional[AttackResponse] = Field(default=None, description="攻击结果")