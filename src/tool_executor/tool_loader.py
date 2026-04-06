"""
ClawAI 工具配置加载器
从 YAML 配置文件加载工具配置，支持参数验证和命令构建
"""

import os
import yaml
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ParameterFormat(str, Enum):
    """参数格式类型"""
    FLAG = "flag"           # -name value
    COMBINED = "combined"   # --name=value
    TEMPLATE = "template"   # 使用模板字符串
    POSITIONAL = "positional"  # 位置参数


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    type: str  # string, integer, boolean, etc.
    description: str = ""
    required: bool = False
    default: Any = None
    flag: str = ""  # 命令行标志，如 "-p"
    format: ParameterFormat = ParameterFormat.FLAG
    template: str = ""  # 模板字符串，如 "-T{value}"
    position: Union[int, str] = 0  # 位置参数的位置，或 "last" 表示末尾
    validation: Dict[str, Any] = field(default_factory=dict)
    options: List[Any] = field(default_factory=list)

    def validate_value(self, value: Any) -> tuple[bool, str]:
        """验证参数值"""
        if value is None:
            if self.required:
                return False, f"参数 '{self.name}' 是必需的"
            return True, ""

        # 类型检查
        try:
            if self.type == "integer":
                value = int(value)
                # 范围检查
                if "min" in self.validation and value < self.validation["min"]:
                    return False, f"参数 '{self.name}' 不能小于 {self.validation['min']}"
                if "max" in self.validation and value > self.validation["max"]:
                    return False, f"参数 '{self.name}' 不能大于 {self.validation['max']}"
            elif self.type == "boolean":
                if isinstance(value, str):
                    value = value.lower() in ["true", "yes", "1", "y"]
                else:
                    value = bool(value)
            elif self.type == "string":
                value = str(value)
                # 正则验证
                if "pattern" in self.validation:
                    import re
                    if not re.match(self.validation["pattern"], value):
                        return False, self.validation.get("error_message", f"参数 '{self.name}' 格式无效")
        except (ValueError, TypeError) as e:
            return False, f"参数 '{self.name}' 类型错误: {str(e)}"

        # 选项检查
        if self.options and value not in self.options:
            return False, f"参数 '{self.name}' 必须是以下值之一: {', '.join(map(str, self.options))}"

        return True, ""


@dataclass
class ToolConfig:
    """工具配置定义"""
    name: str
    command: str
    category: str
    description: str = ""
    enabled: bool = True
    requires_container: bool = True
    container_image: str = "kalilinux/kali-rolling:latest"
    container_options: Dict[str, Any] = field(default_factory=dict)
    command_template: str = ""
    defaults: Dict[str, Any] = field(default_factory=dict)
    parameters: List[ToolParameter] = field(default_factory=list)
    output_handling: Dict[str, Any] = field(default_factory=dict)
    limits: Dict[str, Any] = field(default_factory=dict)
    metrics: List[Dict[str, str]] = field(default_factory=list)
    skill_integration: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        # 设置参数默认值
        for param in self.parameters:
            if param.default is None and param.name in self.defaults:
                param.default = self.defaults[param.name]

        # 如果没有命令模板，构建一个简单的
        if not self.command_template:
            self._build_default_template()

    def _build_default_template(self):
        """构建默认命令模板"""
        parts = [self.command]

        # 添加有标志的参数
        flag_params = [p for p in self.parameters if p.flag]
        for param in flag_params:
            if param.format == ParameterFormat.FLAG:
                parts.append(f"{{{param.name}}}")
            elif param.format == ParameterFormat.COMBINED:
                parts.append(f"{{{param.name}}}")

        # 添加位置参数
        positional_params = [p for p in self.parameters if p.format == ParameterFormat.POSITIONAL]
        for param in positional_params:
            parts.append(f"{{{param.name}}}")

        self.command_template = " ".join(parts)

    def validate_parameters(self, user_params: Dict[str, Any]) -> tuple[bool, Dict[str, str], Dict[str, Any]]:
        """
        验证用户提供的参数

        Returns:
            (success, errors, validated_params)
        """
        errors = {}
        validated = {}

        # 设置默认值
        for param in self.parameters:
            if param.name in user_params:
                value = user_params[param.name]
            elif param.default is not None:
                value = param.default
            else:
                value = None

            # 验证
            is_valid, error_msg = param.validate_value(value)
            if not is_valid:
                errors[param.name] = error_msg
            elif value is not None:
                validated[param.name] = value

        # 检查必需参数
        for param in self.parameters:
            if param.required and param.name not in validated:
                errors[param.name] = f"参数 '{param.name}' 是必需的"

        return len(errors) == 0, errors, validated

    def build_command(self, validated_params: Dict[str, Any]) -> str:
        """根据验证后的参数构建命令"""
        # 准备参数值字典
        param_dict = {}

        for param in self.parameters:
            if param.name in validated_params:
                value = validated_params[param.name]

                # 根据参数格式构建命令行部分
                if param.format == ParameterFormat.FLAG and param.flag:
                    if param.type == "boolean":
                        if value:
                            param_dict[param.name] = param.flag
                        else:
                            param_dict[param.name] = ""
                    else:
                        param_dict[param.name] = f"{param.flag} {value}" if value else ""

                elif param.format == ParameterFormat.COMBINED and param.flag:
                    param_dict[param.name] = f"{param.flag}={value}" if value else ""

                elif param.format == ParameterFormat.TEMPLATE and param.template:
                    param_dict[param.name] = param.template.format(value=value)

                elif param.format == ParameterFormat.POSITIONAL:
                    param_dict[param.name] = str(value)

                else:
                    # 默认作为普通参数
                    param_dict[param.name] = str(value)
            else:
                param_dict[param.name] = ""

        # 应用命令模板
        command = self.command_template
        for param_name, param_value in param_dict.items():
            placeholder = f"{{{param_name}}}"
            if placeholder in command:
                command = command.replace(placeholder, param_value if param_value else "")

        # 清理多余的空格
        import re
        command = re.sub(r'\s+', ' ', command).strip()

        return command

    def get_parameter_info(self) -> List[Dict[str, Any]]:
        """获取参数信息（用于 API 文档）"""
        return [
            {
                "name": param.name,
                "type": param.type,
                "description": param.description,
                "required": param.required,
                "default": param.default,
                "flag": param.flag,
                "format": param.format,
                "validation": param.validation,
                "options": param.options
            }
            for param in self.parameters
        ]


class ToolLoader:
    """工具配置加载器"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化工具加载器

        Args:
            config_dir: 工具配置目录，默认为 config/tools/
        """
        if config_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.config_dir = os.path.join(base_dir, "config", "tools")
        else:
            self.config_dir = config_dir

        self.tools: Dict[str, ToolConfig] = {}
        self.load_all_tools()

    def load_all_tools(self):
        """加载所有工具配置"""
        if not os.path.exists(self.config_dir):
            logger.warning(f"工具配置目录不存在: {self.config_dir}")
            return

        tool_count = 0
        for root, dirs, files in os.walk(self.config_dir):
            for file in files:
                if file.endswith(".yaml") or file.endswith(".yml"):
                    file_path = os.path.join(root, file)
                    try:
                        tool_config = self.load_tool_config(file_path)
                        if tool_config:
                            self.tools[tool_config.name] = tool_config
                            tool_count += 1
                    except Exception as e:
                        logger.error(f"加载工具配置失败 {file_path}: {e}")

        logger.info(f"成功加载 {tool_count} 个工具配置")

    def load_tool_config(self, file_path: str) -> Optional[ToolConfig]:
        """从 YAML 文件加载单个工具配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            if not config_data:
                logger.warning(f"配置文件为空: {file_path}")
                return None

            # 转换参数
            parameters = []
            for param_data in config_data.get("parameters", []):
                # 确定参数格式
                format_str = param_data.get("format", "flag")
                try:
                    param_format = ParameterFormat(format_str)
                except ValueError:
                    param_format = ParameterFormat.FLAG

                param = ToolParameter(
                    name=param_data["name"],
                    type=param_data.get("type", "string"),
                    description=param_data.get("description", ""),
                    required=param_data.get("required", False),
                    default=param_data.get("default"),
                    flag=param_data.get("flag", ""),
                    format=param_format,
                    template=param_data.get("template", ""),
                    position=param_data.get("position", 0),
                    validation=param_data.get("validation", {}),
                    options=param_data.get("options", [])
                )
                parameters.append(param)

            # 创建工具配置
            tool_config = ToolConfig(
                name=config_data["name"],
                command=config_data["command"],
                category=config_data.get("category", "unknown"),
                description=config_data.get("description", ""),
                enabled=config_data.get("enabled", True),
                requires_container=config_data.get("requires_container", True),
                container_image=config_data.get("container_image", "kalilinux/kali-rolling:latest"),
                container_options=config_data.get("container_options", {}),
                command_template=config_data.get("command_template", ""),
                defaults=config_data.get("defaults", {}),
                parameters=parameters,
                output_handling=config_data.get("output_handling", {}),
                limits=config_data.get("limits", {}),
                metrics=config_data.get("metrics", []),
                skill_integration=config_data.get("skill_integration", {})
            )

            logger.debug(f"加载工具配置: {tool_config.name}")
            return tool_config

        except Exception as e:
            logger.error(f"加载工具配置失败 {file_path}: {e}")
            raise

    def get_tool(self, tool_name: str) -> Optional[ToolConfig]:
        """获取指定工具配置"""
        return self.tools.get(tool_name)

    def list_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出所有工具（可过滤类别）"""
        tools_list = []
        for name, config in self.tools.items():
            if not config.enabled:
                continue

            if category and config.category != category:
                continue

            tools_list.append({
                "name": name,
                "command": config.command,
                "category": config.category,
                "description": config.description,
                "requires_container": config.requires_container,
                "parameters": config.get_parameter_info()
            })

        return tools_list

    def get_categories(self) -> List[str]:
        """获取所有工具类别"""
        categories = set()
        for config in self.tools.values():
            if config.enabled:
                categories.add(config.category)
        return sorted(categories)

    def validate_and_build_command(self, tool_name: str, user_params: Dict[str, Any]) -> tuple[bool, str, str, Dict[str, Any]]:
        """
        验证参数并构建命令

        Returns:
            (success, command, error_message, validated_params)
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return False, "", f"工具 '{tool_name}' 未找到", {}

        # 验证参数
        success, errors, validated_params = tool.validate_parameters(user_params)
        if not success:
            error_msg = "; ".join([f"{k}: {v}" for k, v in errors.items()])
            return False, "", f"参数验证失败: {error_msg}", {}

        # 构建命令
        try:
            command = tool.build_command(validated_params)
            return True, command, "", validated_params
        except Exception as e:
            return False, "", f"构建命令失败: {str(e)}", {}


# 单例实例
_tool_loader_instance = None

def get_tool_loader(config_dir: Optional[str] = None) -> ToolLoader:
    """获取工具加载器单例"""
    global _tool_loader_instance
    if _tool_loader_instance is None:
        _tool_loader_instance = ToolLoader(config_dir)
    return _tool_loader_instance


if __name__ == "__main__":
    # 测试代码
    import sys

    logging.basicConfig(level=logging.INFO)

    loader = ToolLoader()

    print(f"加载了 {len(loader.tools)} 个工具")
    print("工具列表:")
    for tool in loader.list_tools():
        print(f"  - {tool['name']} ({tool['category']}): {tool['description']}")

    # 测试构建命令
    if "nmap" in loader.tools:
        tool = loader.tools["nmap"]
        print(f"\n测试构建 nmap 命令:")

        # 有效参数
        params = {"target": "example.com", "ports": "80,443"}
        success, command, error, validated = loader.validate_and_build_command("nmap", params)
        if success:
            print(f"  命令: {command}")
        else:
            print(f"  错误: {error}")

        # 无效参数
        params = {"target": ""}
        success, command, error, validated = loader.validate_and_build_command("nmap", params)
        if not success:
            print(f"  预期错误: {error}")