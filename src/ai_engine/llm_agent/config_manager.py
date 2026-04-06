"""
ClawAI LLM代理配置管理器
加载和管理HackSynth风格的配置文件
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class LLMConfigManager:
    """LLM配置管理器"""

    def __init__(self, config_dir: str = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录，默认为当前目录下的configs/
        """
        if config_dir is None:
            # 默认使用ai-engine服务的configs目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_dir = os.path.join(os.path.dirname(current_dir), "configs")
        else:
            self.config_dir = config_dir

        # 确保目录存在
        os.makedirs(self.config_dir, exist_ok=True)

        logger.info(f"配置管理器初始化，目录: {self.config_dir}")

        # 内置默认配置
        self.default_config = self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """创建默认配置"""
        return {
            "name": "clawai_default_agent",
            "description": "ClawAI默认渗透测试代理配置",
            "version": "1.0.0",

            "llm": {
                "model_id": "deepseek-chat",
                "model_local": False,
                "provider": "deepseek",
                "base_url": "https://api.deepseek.com",
                "temperature": 0.7,
                "top_p": 0.9,
                "do_sample": True,
                "max_new_tokens": 1024,
                "prompt_chaining": True
            },

            "agent": {
                "new_observation_length_limit": 2000,
                "timeout_duration": 30,
                "max_iterations": 10,
                "use_skills": True,
                "skill_selection_strategy": "hybrid"
            },

            "planner": {
                "system_prompt": """你是一个渗透测试命令生成器，集成在ClawAI智能安全评估系统中。你的工作是生成有效的安全测试命令。

重要规则:
1. 每条命令必须用<CMD></CMD>标签包裹
2. 只能生成一行命令
3. 避免重复之前的命令
4. 考虑当前上下文和之前的结果

可用技能: {available_skills}""",

                "user_prompt": """历史总结: {summarized_history}

当前目标: {target}
扫描结果: {scan_results}

基于以上信息，生成下一个最有效的命令来推进安全评估。命令必须用<CMD></CMD>标签包裹。"""
            },

            "summarizer": {
                "system_prompt": "你是一个自主代理，负责总结渗透测试历史。保持简洁，包含关键发现（如开放端口、服务版本、潜在漏洞、密码、密钥等）。",

                "user_prompt": """基于历史总结和最新观察，生成新的总结。包含所有之前的行动和发现。

当前总结: {summarized_history}

新增观察: {new_observation}

生成更新后的总结:"""
            },

            "per_planner": {
                "enabled": False,
                "output_mode": "default",
                "compression_threshold": 20,
                "max_replan_attempts": 3
            }
        }

    def list_configs(self) -> List[str]:
        """列出所有可用的配置文件"""
        config_files = []
        for file_path in Path(self.config_dir).glob("*.json"):
            config_files.append(file_path.stem)

        logger.info(f"找到 {len(config_files)} 个配置文件: {config_files}")
        return config_files

    def load_config(self, config_name: str) -> Dict[str, Any]:
        """
        加载指定配置

        Args:
            config_name: 配置名称（不带.json扩展名）

        Returns:
            配置字典
        """
        config_path = os.path.join(self.config_dir, f"{config_name}.json")

        if not os.path.exists(config_path):
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            return self.default_config.copy()

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            logger.info(f"配置文件加载成功: {config_name}")
            return config

        except json.JSONDecodeError as e:
            logger.error(f"配置文件JSON解析失败: {config_path}, 错误: {e}")
            raise ValueError(f"配置文件JSON格式错误: {config_path}")
        except Exception as e:
            logger.error(f"配置文件加载失败: {config_path}, 错误: {e}")
            raise

    def save_config(self, config_name: str, config: Dict[str, Any]) -> str:
        """
        保存配置到文件

        Args:
            config_name: 配置名称
            config: 配置字典

        Returns:
            保存的文件路径
        """
        config_path = os.path.join(self.config_dir, f"{config_name}.json")

        try:
            # 添加/更新元数据
            if "name" not in config:
                config["name"] = config_name
            if "version" not in config:
                config["version"] = "1.0.0"
            if "description" not in config:
                config["description"] = f"ClawAI代理配置 - {config_name}"

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logger.info(f"配置文件保存成功: {config_path}")
            return config_path

        except Exception as e:
            logger.error(f"配置文件保存失败: {config_path}, 错误: {e}")
            raise

    def create_config_from_template(
        self,
        config_name: str,
        template_type: str = "pentest",
        custom_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        从模板创建配置

        Args:
            config_name: 配置名称
            template_type: 模板类型 (pentest, ctf, web_app, network)
            custom_params: 自定义参数

        Returns:
            创建的配置字典
        """
        # 基础模板
        config = self.default_config.copy()
        config["name"] = config_name

        # 根据模板类型调整
        if template_type == "pentest":
            config["description"] = f"渗透测试代理配置 - {config_name}"
            # 使用默认配置即可

        elif template_type == "ctf":
            config["description"] = f"CTF挑战代理配置 - {config_name}"
            config["planner"]["system_prompt"] = """你是一个CTF挑战命令生成器，专注于解决网络安全挑战。

重要规则:
1. 每条命令必须用<CMD></CMD>标签包裹
2. 专注于获取flag
3. 分析之前的输出寻找线索
4. 使用合适的工具和技术

可用技能: {available_skills}"""

        elif template_type == "web_app":
            config["description"] = f"Web应用安全测试代理配置 - {config_name}"
            config["agent"]["max_iterations"] = 15

            # 添加Web应用特定的提示
            config["target_context"] = "目标是一个Web应用程序。专注于Web安全测试技术。"

        elif template_type == "network":
            config["description"] = f"网络安全评估代理配置 - {config_name}"
            config["agent"]["max_iterations"] = 8

            config["target_context"] = "目标是网络基础设施。专注于网络发现、端口扫描和服务识别。"

        else:
            logger.warning(f"未知模板类型: {template_type}，使用默认pentest模板")

        # 应用自定义参数
        if custom_params:
            self._merge_config(config, custom_params)

        return config

    def _merge_config(self, base_config: Dict[str, Any], custom_config: Dict[str, Any]):
        """递归合并配置"""
        for key, value in custom_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._merge_config(base_config[key], value)
            else:
                base_config[key] = value

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """
        验证配置完整性

        Args:
            config: 配置字典

        Returns:
            错误消息列表，空列表表示验证通过
        """
        errors = []

        # 必需字段检查
        required_fields = ["llm", "agent", "planner", "summarizer"]
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必需字段: {field}")

        # LLM配置检查
        if "llm" in config:
            llm_required = ["model_id", "provider"]
            for field in llm_required:
                if field not in config["llm"]:
                    errors.append(f"llm配置缺少字段: {field}")

        # Agent配置检查
        if "agent" in config:
            agent_required = ["max_iterations", "timeout_duration"]
            for field in agent_required:
                if field not in config["agent"]:
                    errors.append(f"agent配置缺少字段: {field}")

        # Planner配置检查
        if "planner" in config:
            planner_required = ["system_prompt", "user_prompt"]
            for field in planner_required:
                if field not in config["planner"]:
                    errors.append(f"planner配置缺少字段: {field}")

        # Summarizer配置检查
        if "summarizer" in config:
            summarizer_required = ["system_prompt", "user_prompt"]
            for field in summarizer_required:
                if field not in config["summarizer"]:
                    errors.append(f"summarizer配置缺少字段: {field}")

        # PERPlanner配置检查（可选）
        if "per_planner" in config:
            per_planner_config = config["per_planner"]
            if not isinstance(per_planner_config, dict):
                errors.append("per_planner配置必须是字典类型")
            else:
                # 检查必需字段
                if "enabled" not in per_planner_config:
                    errors.append("per_planner配置缺少字段: enabled")

        if errors:
            logger.warning(f"配置验证失败，发现 {len(errors)} 个错误")
        else:
            logger.info("配置验证通过")

        return errors

    def get_available_models(self) -> Dict[str, List[str]]:
        """
        获取可用的LLM模型列表

        Returns:
            按提供商分组的模型列表
        """
        models = {
            "openai": [
                "gpt-4o",
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo",
                "gpt-4o-mini"
            ],
            "anthropic": [
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
                "claude-2.1"
            ],
            "deepseek": [
                "deepseek-chat",
                "deepseek-coder"
            ],
            "local": [
                "Llama-3.1-70B",
                "Llama-3.1-8B",
                "Qwen2-72B",
                "Mixtral-8x7B",
                "Phi-3.5-MoE"
            ]
        }

        return models

    def generate_config_for_model(
        self,
        model_id: str,
        config_name: str = None
    ) -> Dict[str, Any]:
        """
        为特定模型生成优化配置

        Args:
            model_id: 模型ID
            config_name: 配置名称

        Returns:
            优化后的配置
        """
        # 识别模型提供商
        provider = "openai"
        if "claude" in model_id.lower():
            provider = "anthropic"
        elif "deepseek" in model_id.lower():
            provider = "deepseek"
        elif any(local in model_id.lower() for local in ["llama", "qwen", "mixtral", "phi"]):
            provider = "local"

        # 基础配置
        if config_name is None:
            config_name = f"{model_id.replace('-', '_').replace('.', '_')}_config"

        config = self.create_config_from_template(config_name, "pentest")

        # 更新LLM配置
        config["llm"]["model_id"] = model_id
        config["llm"]["provider"] = provider
        config["llm"]["model_local"] = (provider == "local")

        # 模型特定优化
        if "gpt-4" in model_id:
            config["llm"]["max_new_tokens"] = 2000
            config["llm"]["temperature"] = 0.8
        elif "claude" in model_id:
            config["llm"]["max_new_tokens"] = 1500
            config["llm"]["temperature"] = 0.7
        elif "deepseek" in model_id:
            config["llm"]["max_new_tokens"] = 1200
            config["llm"]["temperature"] = 0.6
        elif provider == "local":
            config["llm"]["max_new_tokens"] = 800
            config["llm"]["temperature"] = 0.5

        config["description"] = f"为 {model_id} 优化的配置"

        return config