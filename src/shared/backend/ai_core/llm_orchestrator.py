# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
规则引擎编排器 - 统一管理所有规则引擎调用
⚠️ 技术诚信说明：本模块使用规则引擎而非真正的AI/机器学习系统

核心事实：
1. 没有真正的AI模型：所有"AI决策"实际上是硬编码的if-else规则
2. 没有深度学习：所谓的"多模型协同决策"是固定的规则投票机制
3. 没有机器学习：所有的"AI学习"是预设的数据统计，没有真正的学习算法
4. 模拟数据依赖：当配置中没有API密钥时，返回固定的模拟数据
"""

import os
import sys
import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import requests
from functools import lru_cache

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from config import config


class ModelType(Enum):
    """支持的AI模型类型"""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    CLAUDE = "claude"
    LOCAL = "local"  # 本地模型降级


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    api_key: str = ""
    base_url: str = ""
    model_name: str = ""
    max_tokens: int = 2000
    temperature: float = 0.3
    timeout: int = 30
    enabled: bool = True
    priority: int = 1  # 优先级，数字越小优先级越高


@dataclass
class AIRequest:
    """AI请求"""
    prompt: str
    system_prompt: str = ""
    model_type: ModelType = ModelType.DEEPSEEK
    temperature: float = None
    max_tokens: int = None
    stream: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AIResponse:
    """AI响应"""
    content: str
    model_used: str
    response_time: float
    tokens_used: int = 0
    cached: bool = False
    error: Optional[str] = None
    raw_response: Optional[Dict] = None


@dataclass
class ModelPerformance:
    """模型性能统计"""
    total_requests: int = 0
    successful_requests: int = 0
    total_response_time: float = 0.0
    average_response_time: float = 0.0
    last_error: Optional[str] = None
    last_success_time: Optional[float] = None


class BaseAIModel:
    """AI模型基类"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.performance = ModelPerformance()
    
    def call(self, request: AIRequest) -> AIResponse:
        """调用模型API"""
        raise NotImplementedError
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        return self.config.enabled and bool(self.config.api_key)
    
    def update_performance(self, success: bool, response_time: float, error: str = None):
        """更新性能统计"""
        self.performance.total_requests += 1
        if success:
            self.performance.successful_requests += 1
            self.performance.last_success_time = time.time()
        else:
            self.performance.last_error = error
        
        self.performance.total_response_time += response_time
        if self.performance.successful_requests > 0:
            self.performance.average_response_time = (
                self.performance.total_response_time / self.performance.successful_requests
            )


class DeepSeekModel(BaseAIModel):
    """DeepSeek模型"""
    
    def call(self, request: AIRequest) -> AIResponse:
        start_time = time.time()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})
            
            payload = {
                "model": self.config.model_name,
                "messages": messages,
                "max_tokens": request.max_tokens or self.config.max_tokens,
                "temperature": request.temperature or self.config.temperature,
                "stream": request.stream
            }
            
            response = requests.post(
                f"{self.config.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.config.timeout
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                tokens_used = result.get("usage", {}).get("total_tokens", 0)
                
                self.update_performance(True, response_time)
                return AIResponse(
                    content=content,
                    model_used=self.config.name,
                    response_time=response_time,
                    tokens_used=tokens_used,
                    raw_response=result
                )
            else:
                error_msg = f"API调用失败: {response.status_code} - {response.text}"
                self.update_performance(False, response_time, error_msg)
                return AIResponse(
                    content="",
                    model_used=self.config.name,
                    response_time=response_time,
                    error=error_msg
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"模型调用异常: {str(e)}"
            self.update_performance(False, response_time, error_msg)
            return AIResponse(
                content="",
                model_used=self.config.name,
                response_time=response_time,
                error=error_msg
            )


class OpenAIModel(BaseAIModel):
    """OpenAI模型（兼容OpenAI API）"""
    
    def call(self, request: AIRequest) -> AIResponse:
        start_time = time.time()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})
            
            payload = {
                "model": self.config.model_name,
                "messages": messages,
                "max_tokens": request.max_tokens or self.config.max_tokens,
                "temperature": request.temperature or self.config.temperature,
                "stream": request.stream
            }
            
            # OpenAI兼容API
            api_url = f"{self.config.base_url}/v1/chat/completions"
            
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=self.config.timeout
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                tokens_used = result.get("usage", {}).get("total_tokens", 0)
                
                self.update_performance(True, response_time)
                return AIResponse(
                    content=content,
                    model_used=self.config.name,
                    response_time=response_time,
                    tokens_used=tokens_used,
                    raw_response=result
                )
            else:
                error_msg = f"API调用失败: {response.status_code} - {response.text}"
                self.update_performance(False, response_time, error_msg)
                return AIResponse(
                    content="",
                    model_used=self.config.name,
                    response_time=response_time,
                    error=error_msg
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"模型调用异常: {str(e)}"
            self.update_performance(False, response_time, error_msg)
            return AIResponse(
                content="",
                model_used=self.config.name,
                response_time=response_time,
                error=error_msg
            )


class LocalModel(BaseAIModel):
    """本地模型（降级方案）"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        # 这里可以集成本地模型如Ollama、LM Studio等
        self.local_available = self._check_local_model()
    
    def _check_local_model(self) -> bool:
        """检查本地模型是否可用"""
        # 这里可以检查本地模型服务是否运行
        # 例如检查Ollama服务是否可用
        return False  # 默认不可用
    
    def call(self, request: AIRequest) -> AIResponse:
        start_time = time.time()
        
        if not self.local_available:
            response_time = time.time() - start_time
            self.update_performance(False, response_time, "本地模型不可用")
            return AIResponse(
                content="",
                model_used=self.config.name,
                response_time=response_time,
                error="本地模型不可用"
            )
        
        # 这里实现本地模型调用逻辑
        # 例如调用Ollama API
        response_time = time.time() - start_time
        self.update_performance(True, response_time)
        return AIResponse(
            content="[本地模型] 这是一个模拟响应，实际需要配置本地模型服务",
            model_used=self.config.name,
            response_time=response_time
        )


class LLMOrchestrator:
    """
    AI编排器 - 统一管理所有AI模型调用
    支持多模型协同决策和智能回退机制
    """
    
    def __init__(self, enable_cache: bool = True):
        self.models: Dict[ModelType, BaseAIModel] = {}
        self.cache_enabled = enable_cache
        self.response_cache: Dict[str, AIResponse] = {}
        self._init_models()
    
    def _init_models(self):
        """初始化所有支持的模型"""
        # DeepSeek模型配置
        deepseek_config = ModelConfig(
            name="DeepSeek",
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL,
            model_name=config.DEEPSEEK_MODEL,
            max_tokens=config.DEEPSEEK_MAX_TOKENS,
            timeout=config.DEEPSEEK_TIMEOUT,
            enabled=bool(config.DEEPSEEK_API_KEY),
            priority=1
        )
        self.models[ModelType.DEEPSEEK] = DeepSeekModel(deepseek_config)
        
        # OpenAI模型配置（如果有配置）
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if openai_key:
            openai_config = ModelConfig(
                name="OpenAI",
                api_key=openai_key,
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com"),
                model_name=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                priority=2
            )
            self.models[ModelType.OPENAI] = OpenAIModel(openai_config)
        
        # 本地模型（降级方案）
        local_config = ModelConfig(
            name="Local",
            enabled=True,  # 本地模型总是启用作为降级方案
            priority=100  # 最低优先级
        )
        self.models[ModelType.LOCAL] = LocalModel(local_config)
    
    def get_available_models(self) -> List[ModelType]:
        """获取可用的模型列表（按优先级排序）"""
        available = []
        for model_type, model in self.models.items():
            if model.is_available():
                available.append((model_type, model.config.priority))
        
        # 按优先级排序
        available.sort(key=lambda x: x[1])
        return [model_type for model_type, _ in available]
    
    def _generate_cache_key(self, request: AIRequest) -> str:
        """生成缓存键"""
        import hashlib
        cache_data = {
            "prompt": request.prompt,
            "system_prompt": request.system_prompt,
            "model_type": request.model_type.value,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def call_model(self, request: AIRequest) -> AIResponse:
        """
        调用AI模型
        
        Args:
            request: AI请求
            
        Returns:
            AI响应
        """
        # 检查缓存
        if self.cache_enabled:
            cache_key = self._generate_cache_key(request)
            if cache_key in self.response_cache:
                cached_response = self.response_cache[cache_key]
                cached_response.cached = True
                return cached_response
        
        # 获取指定模型
        model = self.models.get(request.model_type)
        if not model or not model.is_available():
            # 模型不可用，尝试其他可用模型
            available_models = self.get_available_models()
            if not available_models:
                return AIResponse(
                    content="",
                    model_used="none",
                    response_time=0,
                    error="没有可用的AI模型"
                )
            
            # 使用最高优先级的可用模型
            fallback_model_type = available_models[0]
            model = self.models[fallback_model_type]
            request.model_type = fallback_model_type
        
        # 调用模型
        response = model.call(request)
        
        # 缓存成功的响应
        if self.cache_enabled and not response.error:
            cache_key = self._generate_cache_key(request)
            self.response_cache[cache_key] = response
        
        return response
    
    def call_with_fallback(self, request: AIRequest) -> AIResponse:
        """
        调用AI模型，支持自动回退
        
        Args:
            request: AI请求
            
        Returns:
            AI响应（使用第一个成功的模型）
        """
        available_models = self.get_available_models()
        
        for model_type in available_models:
            request.model_type = model_type
            response = self.call_model(request)
            
            if not response.error:
                return response
        
        # 所有模型都失败
        return AIResponse(
            content="",
            model_used="none",
            response_time=0,
            error="所有AI模型调用失败"
        )
    
    def analyze_target(self, scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI分析目标
        
        Args:
            scan_data: 扫描数据
            
        Returns:
            目标分析结果
        """
        prompt = self._create_target_analysis_prompt(scan_data)
        
        request = AIRequest(
            prompt=prompt,
            system_prompt="你是一个资深网络安全专家，擅长目标分析和风险评估。",
            model_type=ModelType.DEEPSEEK,
            temperature=0.2  # 低温度以获得更确定的回答
        )
        
        response = self.call_with_fallback(request)
        
        if response.error:
            return {
                "error": response.error,
                "analysis": "AI分析失败",
                "model_used": response.model_used
            }
        
        # 尝试解析JSON响应
        try:
            analysis_result = json.loads(response.content.strip())
            analysis_result["model_used"] = response.model_used
            analysis_result["response_time"] = response.response_time
            return analysis_result
        except json.JSONDecodeError:
            # 如果不是JSON，返回原始内容
            return {
                "analysis": response.content,
                "model_used": response.model_used,
                "response_time": response.response_time,
                "raw_response": True
            }
    
    def plan_attack_path(self, target_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI规划攻击路径
        
        Args:
            target_analysis: 目标分析结果
            
        Returns:
            攻击路径规划
        """
        prompt = self._create_attack_planning_prompt(target_analysis)
        
        request = AIRequest(
            prompt=prompt,
            system_prompt="你是一个资深渗透测试专家，擅长攻击路径规划和风险评估。",
            model_type=ModelType.DEEPSEEK,
            temperature=0.3
        )
        
        response = self.call_with_fallback(request)
        
        if response.error:
            return {
                "error": response.error,
                "attack_plan": "AI攻击规划失败",
                "model_used": response.model_used
            }
        
        # 尝试解析JSON响应
        try:
            attack_plan = json.loads(response.content.strip())
            attack_plan["model_used"] = response.model_used
            attack_plan["response_time"] = response.response_time
            return attack_plan
        except json.JSONDecodeError:
            # 如果不是JSON，返回原始内容
            return {
                "attack_plan": response.content,
                "model_used": response.model_used,
                "response_time": response.response_time,
                "raw_response": True
            }
    
    def generate_exploit_code(self, vulnerability: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI生成漏洞利用代码
        
        Args:
            vulnerability: 漏洞信息
            
        Returns:
            漏洞利用代码
        """
        prompt = self._create_code_generation_prompt(vulnerability)
        
        request = AIRequest(
            prompt=prompt,
            system_prompt="你是一个资深安全研究员，擅长编写安全、有效的漏洞利用代码。",
            model_type=ModelType.DEEPSEEK,
            temperature=0.4  # 稍高温度以获得更多创造性
        )
        
        response = self.call_with_fallback(request)
        
        if response.error:
            return {
                "error": response.error,
                "exploit_code": "AI代码生成失败",
                "model_used": response.model_used
            }
        
        return {
            "exploit_code": response.content,
            "model_used": response.model_used,
            "response_time": response.response_time,
            "language": self._detect_code_language(response.content)
        }
    
    def _create_target_analysis_prompt(self, scan_data: Dict[str, Any]) -> str:
        """创建目标分析提示词"""
        # 提取扫描信息
        ports_info = []
        if "nmap" in scan_data:
            nmap_result = scan_data["nmap"]
            if "ports" in nmap_result:
                for port in nmap_result["ports"][:10]:  # 只取前10个端口
                    ports_info.append(f"端口 {port['port']}: {port.get('service', '未知服务')} ({port.get('state', '未知状态')})")
        
        # 构建提示词
        prompt = f"""基于以下扫描结果进行目标分析：

目标: {scan_data.get('target', '未知目标')}
扫描时间: {scan_data.get('scan_time', '未知时间')}

扫描发现:
{chr(10).join(ports_info) if ports_info else '无开放端口发现'}

请提供详细的目标分析，包括：
1. 攻击面评估
2. 风险评估  
3. 目标画像
4. 攻击优先级建议

请以JSON格式返回分析结果。"""
        
        return prompt
    
    def _create_attack_planning_prompt(self, target_analysis: Dict[str, Any]) -> str:
        """创建攻击路径规划提示词"""
        # 提取分析信息
        attack_surface = target_analysis.get('attack_surface', '未知')
        vulnerabilities = target_analysis.get('vulnerabilities', 0)
        
        # 构建提示词
        prompt = f"""基于以下目标分析规划攻击路径：

目标分析:
- 攻击面评分: {attack_surface}/10
- 漏洞数量: {vulnerabilities}

请基于以下维度规划攻击路径：
1. 可利用性 (exploitability)
2. 影响程度 (impact)  
3. 隐蔽性 (stealth)
4. 成功率 (success_rate)
5. 时间效率 (time_efficiency)

请推荐1个最佳攻击路径和2个备选路径，以JSON格式返回：
{{
  "selected_path_type": "攻击路径类型",
  "selected_score": 0-10评分,
  "confidence": 0-1置信度,
  "selection_reasons": ["选择理由1", "选择理由2"],
  "alternative_paths": [
    {{"path_type": "备选路径1", "score": 评分, "reason": "未被选中的主要原因"}},
    {{"path_type": "备选路径2", "score": 评分, "reason": "未被选中的主要原因"}}
  ],
  "decision_factors": {{
    "exploitability": 0-10,
    "impact": 0-10,
    "stealth": 0-10,
    "success_rate": 0-1,
    "time_efficiency": 0-10
  }}
}}"""
        
        return prompt
    
    def _create_code_generation_prompt(self, vulnerability: Dict[str, Any]) -> str:
        """创建代码生成提示词"""
        vuln_type = vulnerability.get('type', '未知漏洞')
        description = vulnerability.get('description', '未提供描述')
        severity = vulnerability.get('severity', 'medium')
        
        prompt = f"""为以下漏洞生成漏洞利用代码：

漏洞类型: {vuln_type}
漏洞描述: {description}
严重等级: {severity}

请生成安全、有效的漏洞利用代码，要求：
1. 包含适当的错误处理
2. 添加详细的注释说明
3. 考虑不同环境适配性
4. 包含使用说明

请以代码块形式返回，包含完整代码实现。"""
        
        return prompt
    
    def _detect_code_language(self, code: str) -> str:
        """检测代码语言"""
        code_lower = code.lower()
        
        if 'def ' in code_lower or 'import ' in code_lower or 'python' in code_lower:
            return 'python'
        elif 'function ' in code_lower or 'const ' in code_lower or 'let ' in code_lower or 'var ' in code_lower:
            return 'javascript'
        elif '<?php' in code_lower or '$' in code_lower:
            return 'php'
        elif 'public class' in code_lower or 'public static void' in code_lower:
            return 'java'
        elif '#include' in code_lower or 'int main' in code_lower:
            return 'c/c++'
        elif '<html' in code_lower or '<body' in code_lower:
            return 'html'
        else:
            return 'unknown'