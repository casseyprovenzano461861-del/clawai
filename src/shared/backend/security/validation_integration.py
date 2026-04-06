"""
Pydantic与安全输入验证的集成模块

提供将现有安全验证系统与Pydantic模型集成的功能。
"""

from typing import Any, Dict, Optional, List
from pydantic import BaseModel, validator, root_validator
from pydantic.fields import FieldInfo

try:
    from .input_validation import get_secure_validator, validate_input_secure, ValidationSeverity
    from .sanitize import sanitize_filename, validate_url, filter_sensitive_data
except ImportError:
    # 直接运行脚本时的回退
    from input_validation import get_secure_validator, validate_input_secure, ValidationSeverity
    from sanitize import sanitize_filename, validate_url, filter_sensitive_data


class SecurePydanticMixin:
    """Pydantic安全验证混入类"""

    @classmethod
    def secure_field_validator(cls, field_name: str, input_type: str = "string", sanitize: bool = True):
        """
        创建安全字段验证器装饰器

        Args:
            field_name: 字段名
            input_type: 输入类型 (target, command, json, string, number, boolean, array, object)
            sanitize: 是否清理输入
        """
        def decorator(func):
            @validator(field_name, pre=True, allow_reuse=True)
            def validate_field(cls, value):
                if value is None:
                    return value

                # 获取验证器
                validator_instance = get_secure_validator()

                # 根据输入类型验证
                if input_type == "target":
                    result = validator_instance.validate_target(str(value))
                elif input_type == "command":
                    result = validator_instance.validate_command(str(value))
                elif input_type == "json":
                    result = validator_instance.validate_json(str(value))
                else:
                    result = validator_instance.validate_parameter(field_name, value, input_type)

                if not result.is_valid:
                    # 构建错误消息
                    error_msg = f"字段 '{field_name}' 验证失败: {result.message}"
                    if result.detected_threats:
                        error_msg += f" 检测到威胁: {', '.join(result.detected_threats)}"

                    raise ValueError(error_msg)

                # 如果需要清理，返回清理后的值
                if sanitize and result.sanitized_value is not None:
                    return result.sanitized_value

                return value

            return validate_field
        return decorator

    @classmethod
    def secure_model_validator(cls, sanitize_all: bool = True):
        """
        创建安全模型验证器装饰器

        Args:
            sanitize_all: 是否清理所有字段
        """
        def decorator(func):
            @root_validator(pre=True)
            def validate_model(cls, values):
                validator_instance = get_secure_validator()

                for field_name, value in values.items():
                    if value is None:
                        continue

                    # 跳过不需要验证的字段
                    if field_name.startswith("_"):
                        continue

                    # 字符串字段进行威胁检测
                    if isinstance(value, str):
                        threats, severity = validator_instance._detect_threats(value)
                        if threats and severity in [ValidationSeverity.HIGH, ValidationSeverity.CRITICAL]:
                            error_msg = f"字段 '{field_name}' 包含高危威胁: {', '.join(threats)}"
                            raise ValueError(error_msg)

                        # 清理字符串
                        if sanitize_all:
                            values[field_name] = validator_instance._sanitize_value(value)

                    # 递归检查字典和列表
                    elif isinstance(value, dict):
                        sanitized_dict = cls._sanitize_dict(value, validator_instance)
                        values[field_name] = sanitized_dict

                    elif isinstance(value, list):
                        sanitized_list = cls._sanitize_list(value, validator_instance)
                        values[field_name] = sanitized_list

                return values

            return validate_model
        return decorator

    @staticmethod
    def _sanitize_dict(data: Dict[str, Any], validator) -> Dict[str, Any]:
        """递归清理字典"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = validator._sanitize_value(value)
            elif isinstance(value, dict):
                sanitized[key] = SecurePydanticMixin._sanitize_dict(value, validator)
            elif isinstance(value, list):
                sanitized[key] = SecurePydanticMixin._sanitize_list(value, validator)
            else:
                sanitized[key] = value
        return sanitized

    @staticmethod
    def _sanitize_list(data: List[Any], validator) -> List[Any]:
        """递归清理列表"""
        sanitized = []
        for item in data:
            if isinstance(item, str):
                sanitized.append(validator._sanitize_value(item))
            elif isinstance(item, dict):
                sanitized.append(SecurePydanticMixin._sanitize_dict(item, validator))
            elif isinstance(item, list):
                sanitized.append(SecurePydanticMixin._sanitize_list(item, validator))
            else:
                sanitized.append(item)
        return sanitized


# 预定义的安全验证器
def secure_target_validator(field_name: str = "target"):
    """目标地址安全验证器"""
    return SecurePydanticMixin.secure_field_validator(field_name, "target", True)


def secure_command_validator(field_name: str = "command"):
    """命令安全验证器"""
    return SecurePydanticMixin.secure_field_validator(field_name, "command", True)


def secure_json_validator(field_name: str = "json_data"):
    """JSON安全验证器"""
    return SecurePydanticMixin.secure_field_validator(field_name, "json", True)


def secure_string_validator(field_name: str, max_length: Optional[int] = None):
    """字符串安全验证器"""
    def decorator(func):
        @validator(field_name, pre=True, allow_reuse=True)
        def validate_string(cls, value):
            if value is None:
                return value

            if not isinstance(value, str):
                raise ValueError(f"字段 '{field_name}' 必须是字符串类型")

            # 长度检查
            if max_length and len(value) > max_length:
                raise ValueError(f"字段 '{field_name}' 长度不能超过 {max_length} 字符")

            # 安全验证
            validator_instance = get_secure_validator()
            threats, severity = validator_instance._detect_threats(value)

            if threats and severity in [ValidationSeverity.HIGH, ValidationSeverity.CRITICAL]:
                error_msg = f"字段 '{field_name}' 包含高危威胁: {', '.join(threats)}"
                raise ValueError(error_msg)

            # 清理字符串
            sanitized = validator_instance._sanitize_value(value)
            return sanitized

        return validate_string
    return decorator


def secure_url_validator(field_name: str = "url"):
    """URL安全验证器"""
    def decorator(func):
        @validator(field_name, pre=True, allow_reuse=True)
        def validate_url_field(cls, value):
            if value is None:
                return value

            if not isinstance(value, str):
                raise ValueError(f"字段 '{field_name}' 必须是字符串类型")

            # 使用sanitize模块验证URL
            if not validate_url(value):
                raise ValueError(f"字段 '{field_name}' 包含无效或危险的URL")

            # 安全验证
            validator_instance = get_secure_validator()
            result = validator_instance.validate_target(value)

            if not result.is_valid:
                raise ValueError(f"字段 '{field_name}' URL验证失败: {result.message}")

            return result.sanitized_value or value

        return validate_url_field
    return decorator


def secure_filename_validator(field_name: str = "filename"):
    """文件名安全验证器"""
    def decorator(func):
        @validator(field_name, pre=True, allow_reuse=True)
        def validate_filename_field(cls, value):
            if value is None:
                return value

            if not isinstance(value, str):
                raise ValueError(f"字段 '{field_name}' 必须是字符串类型")

            # 使用sanitize模块清理文件名
            sanitized = sanitize_filename(value)

            # 安全验证
            validator_instance = get_secure_validator()
            threats, severity = validator_instance._detect_threats(sanitized)

            if threats and severity in [ValidationSeverity.HIGH, ValidationSeverity.CRITICAL]:
                error_msg = f"字段 '{field_name}' 文件名包含高危威胁: {', '.join(threats)}"
                raise ValueError(error_msg)

            return sanitized

        return validate_filename_field
    return decorator


# 模型级别的安全装饰器
def secure_model(sanitize_all: bool = True):
    """模型安全装饰器"""
    return SecurePydanticMixin.secure_model_validator(sanitize_all)


# 快速集成函数
def apply_secure_validation(model_class: BaseModel, field_configs: Dict[str, Dict[str, Any]] = None) -> BaseModel:
    """
    为现有Pydantic模型应用安全验证

    Args:
        model_class: Pydantic模型类
        field_configs: 字段配置字典
            {
                "field_name": {
                    "type": "target|command|json|string|url|filename",
                    "sanitize": True/False,
                    "max_length": 100
                }
            }

    Returns:
        应用了安全验证的模型类
    """
    if field_configs is None:
        field_configs = {}

    # 获取模型字段
    fields = model_class.__fields__

    # 为每个字段应用相应的验证器
    for field_name, field_info in fields.items():
        config = field_configs.get(field_name, {})
        field_type = config.get("type", "string")

        # 创建验证器
        if field_type == "target":
            validator_func = secure_target_validator(field_name)
        elif field_type == "command":
            validator_func = secure_command_validator(field_name)
        elif field_type == "json":
            validator_func = secure_json_validator(field_name)
        elif field_type == "url":
            validator_func = secure_url_validator(field_name)
        elif field_type == "filename":
            validator_func = secure_filename_validator(field_name)
        else:  # string
            max_length = config.get("max_length")
            validator_func = secure_string_validator(field_name, max_length)

        # 应用验证器到模型类
        model_class = validator_func(lambda cls: cls)(model_class)

    # 应用模型级别的验证
    model_class = secure_model()(model_class)

    return model_class


# 测试函数
def test_validation_integration():
    """测试验证集成"""
    from pydantic import BaseModel as PydanticBaseModel, Field
    from typing import Optional

    class TestModel(PydanticBaseModel):
        target: str = Field(..., description="目标地址")
        command: Optional[str] = Field(None, description="命令")
        json_data: Optional[str] = Field(None, description="JSON数据")
        filename: Optional[str] = Field(None, description="文件名")
        normal_string: str = Field(..., description="普通字符串")

    # 应用安全验证
    SecureTestModel = apply_secure_validation(TestModel, {
        "target": {"type": "target"},
        "command": {"type": "command"},
        "json_data": {"type": "json"},
        "filename": {"type": "filename"},
        "normal_string": {"type": "string", "max_length": 100}
    })

    print("测试安全验证集成...")

    # 测试正常输入
    try:
        instance = SecureTestModel(
            target="https://example.com",
            command="nmap -sV 127.0.0.1",
            json_data='{"name": "test"}',
            filename="safe_file.txt",
            normal_string="normal input"
        )
        print(f"✅ 正常输入验证通过: {instance}")
    except Exception as e:
        print(f"❌ 正常输入验证失败: {e}")

    # 测试恶意输入
    malicious_cases = [
        {
            "target": "<script>alert(1)</script>",
            "command": "nmap -sV 127.0.0.1",
            "json_data": '{"name": "test"}',
            "filename": "safe_file.txt",
            "normal_string": "normal input"
        },
        {
            "target": "https://example.com",
            "command": "rm -rf /",
            "json_data": '{"name": "test"}',
            "filename": "safe_file.txt",
            "normal_string": "normal input"
        },
        {
            "target": "https://example.com",
            "command": "nmap -sV 127.0.0.1",
            "json_data": '{"command": "cat /etc/passwd"}',
            "filename": "../../../etc/passwd",
            "normal_string": "normal input"
        }
    ]

    for i, case in enumerate(malicious_cases, 1):
        try:
            instance = SecureTestModel(**case)
            print(f"❌ 恶意输入案例 {i} 应该失败但通过了: {instance}")
        except Exception as e:
            print(f"✅ 恶意输入案例 {i} 正确被拒绝: {e}")

    print("测试完成!")


if __name__ == "__main__":
    test_validation_integration()