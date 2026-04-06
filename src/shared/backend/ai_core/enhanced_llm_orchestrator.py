# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
增强版LLM编排器 - 支持真实AI模型、本地LLM和智能降级
第一阶段：解决技术诚信问题 - 真实AI模型集成
"""

import os
import sys
import json
import time
import asyncio
import requests
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import subprocess
import platform
from ..security.sanitize import safe_execute, SecurityError

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from config import config


class AIMode(Enum):
    """AI工作模式"""
    AI_FIRST = "ai_first"      # AI优先，失败时降级到规则引擎
    RULE_ONLY = "rule_only"    # 仅使用规则引擎
    HYBRID = "hybrid"          # 混合模式，AI和规则引擎协同工作
    LOCAL_ONLY = "local_only"  # 仅使用本地LLM


class ModelType(Enum):
    """支持的AI模型类型"""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    CLAUDE = "claude"
    OLLAMA = "ollama"          # 本地Ollama模型
    LM_STUDIO = "lm_studio"    # LM Studio本地模型
    RULE_ENGINE = "rule_engine" # 规则引擎降级方案


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    model_type: ModelType
    api_key: str = ""
    base_url: str = ""
    model_name: str = ""
    max_tokens: int = 2000
    temperature: float = 0.3
    timeout: int = 30
    enabled: bool = True
    priority: int = 1  # 优先级，数字越小优先级越高
    is_local: bool = False  # 是否为本地模型


@dataclass
class AIRequest:
    """AI请求"""
    prompt: str
    system_prompt: str = ""
    model_type: ModelType = None  # 如果为None，由编排器自动选择
    temperature: float = None
    max_tokens: int = None
    stream: bool = False
    require_realtime: bool = False  # 是否需要实时响应（影响模型选择）
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AIResponse:
    """AI响应"""
    success: bool
    content: str
    model_used: str
    model_type: ModelType
    response_time: float
    tokens_used: int = 0
    cached: bool = False
    error: Optional[str] = None
    confidence: float = 1.0  # 响应置信度
    raw_response: Optional[Dict] = None
    is_local_model: bool = False


@dataclass
class ModelPerformance:
    """模型性能统计"""
    total_requests: int = 0
    successful_requests: int = 0
    total_response_time: float = 0.0
    average_response_time: float = 0.0
    error_rate: float = 0.0
    last_error: Optional[str] = None
    last_success_time: Optional[float] = None
    availability_score: float = 0.0  # 可用性评分（0-1）


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
        if not self.config.enabled:
            return False
        
        # 云端模型需要API密钥
        if not self.config.is_local and not self.config.api_key:
            return False
        
        # 本地模型需要检查服务是否运行
        if self.config.is_local:
            return self._check_local_service()
        
        return True
    
    def _check_local_service(self) -> bool:
        """检查本地模型服务（子类可以重写）"""
        return True
    
    def update_performance(self, success: bool, response_time: float, error: str = None):
        """更新性能统计"""
        self.performance.total_requests += 1
        
        if success:
            self.performance.successful_requests += 1
            self.performance.last_success_time = time.time()
        else:
            self.performance.last_error = error
        
        self.performance.total_response_time += response_time
        if self.performance.total_requests > 0:
            self.performance.error_rate = 1 - (self.performance.successful_requests / self.performance.total_requests)
            if self.performance.successful_requests > 0:
                self.performance.average_response_time = (
                    self.performance.total_response_time / self.performance.successful_requests
                )
        
        # 计算可用性评分（最近10次请求的成功率）
        self.performance.availability_score = self.performance.successful_requests / max(self.performance.total_requests, 1)


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
                    success=True,
                    content=content,
                    model_used=self.config.name,
                    model_type=self.config.model_type,
                    response_time=response_time,
                    tokens_used=tokens_used,
                    raw_response=result
                )
            else:
                error_msg = f"API调用失败: {response.status_code} - {response.text}"
                self.update_performance(False, response_time, error_msg)
                return AIResponse(
                    success=False,
                    content="",
                    model_used=self.config.name,
                    model_type=self.config.model_type,
                    response_time=response_time,
                    error=error_msg
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"模型调用异常: {str(e)}"
            self.update_performance(False, response_time, error_msg)
            return AIResponse(
                success=False,
                content="",
                model_used=self.config.name,
                model_type=self.config.model_type,
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
                    success=True,
                    content=content,
                    model_used=self.config.name,
                    model_type=self.config.model_type,
                    response_time=response_time,
                    tokens_used=tokens_used,
                    raw_response=result
                )
            else:
                error_msg = f"API调用失败: {response.status_code} - {response.text}"
                self.update_performance(False, response_time, error_msg)
                return AIResponse(
                    success=False,
                    content="",
                    model_used=self.config.name,
                    model_type=self.config.model_type,
                    response_time=response_time,
                    error=error_msg
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"模型调用异常: {str(e)}"
            self.update_performance(False, response_time, error_msg)
            return AIResponse(
                success=False,
                content="",
                model_used=self.config.name,
                model_type=self.config.model_type,
                response_time=response_time,
                error=error_msg
            )


class OllamaModel(BaseAIModel):
    """Ollama本地模型"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.local_service_available = False
        self._check_local_service()
    
    def _check_local_service(self) -> bool:
        """检查Ollama服务是否运行"""
        try:
            # 检查Ollama服务是否运行
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                self.local_service_available = True
                return True
        except:
            pass
        
        self.local_service_available = False
        return False
    
    def call(self, request: AIRequest) -> AIResponse:
        start_time = time.time()
        
        if not self.local_service_available:
            response_time = time.time() - start_time
            self.update_performance(False, response_time, "Ollama服务不可用")
            return AIResponse(
                success=False,
                content="",
                model_used=self.config.name,
                model_type=self.config.model_type,
                response_time=response_time,
                error="Ollama服务不可用，请确保Ollama已安装并运行",
                is_local_model=True
            )
        
        try:
            payload = {
                "model": self.config.model_name,
                "prompt": request.prompt,
                "system": request.system_prompt,
                "stream": request.stream,
                "options": {
                    "temperature": request.temperature or self.config.temperature,
                    "num_predict": request.max_tokens or self.config.max_tokens
                }
            }
            
            # 移除空值
            if not request.system_prompt:
                payload.pop("system", None)
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=self.config.timeout
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("response", "")
                
                self.update_performance(True, response_time)
                return AIResponse(
                    success=True,
                    content=content,
                    model_used=self.config.name,
                    model_type=self.config.model_type,
                    response_time=response_time,
                    raw_response=result,
                    is_local_model=True
                )
            else:
                error_msg = f"Ollama API调用失败: {response.status_code} - {response.text}"
                self.update_performance(False, response_time, error_msg)
                return AIResponse(
                    success=False,
                    content="",
                    model_used=self.config.name,
                    model_type=self.config.model_type,
                    response_time=response_time,
                    error=error_msg,
                    is_local_model=True
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"Ollama模型调用异常: {str(e)}"
            self.update_performance(False, response_time, error_msg)
            return AIResponse(
                success=False,
                content="",
                model_used=self.config.name,
                model_type=self.config.model_type,
                response_time=response_time,
                error=error_msg,
                is_local_model=True
            )


class RuleEngineModel(BaseAIModel):
    """规则引擎模型（降级方案）"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        # 导入现有的规则引擎
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from decision_engine import DecisionEngine
        self.rule_engine = DecisionEngine()
    
    def call(self, request: AIRequest) -> AIResponse:
        start_time = time.time()
        
        try:
            # 使用规则引擎处理请求
            # 这里需要将AI请求转换为规则引擎能处理的格式
            # 简化实现：返回基于规则的响应
            
            # 模拟规则引擎处理
            time.sleep(0.1)  # 模拟处理延迟
            
            # 基于关键词的简单规则
            prompt_lower = request.prompt.lower()
            
            if "漏洞" in prompt_lower or "vulnerability" in prompt_lower:
                content = """基于规则引擎分析：
1. 漏洞类型: 潜在Web应用漏洞
2. 风险等级: 中
3. 建议措施: 进行详细扫描确认
4. 工具推荐: nuclei, nikto, wpscan
5. 优先级: 高"""
            elif "端口" in prompt_lower or "port" in prompt_lower:
                content = """基于规则引擎分析：
1. 常用端口: 80(HTTP), 443(HTTPS), 22(SSH), 3389(RDP)
2. 扫描建议: 使用nmap进行全端口扫描
3. 安全配置: 关闭非必要端口
4. 检测方法: 端口扫描+服务识别"""
            elif "攻击" in prompt_lower or "attack" in prompt_lower:
                content = """基于规则引擎分析：
1. 攻击类型: 需根据具体漏洞确定
2. 风险评估: 需要详细目标分析
3. 建议流程: 信息收集→漏洞扫描→漏洞利用→权限提升
4. 工具链: nmap→nuclei→sqlmap→metasploit"""
            else:
                content = """基于规则引擎分析：
1. 分析类型: 通用安全分析
2. 建议: 提供更具体的目标信息
3. 默认流程: 执行全面渗透测试
4. 预期输出: 详细风险评估报告"""
            
            response_time = time.time() - start_time
            self.update_performance(True, response_time)
            return AIResponse(
                success=True,
                content=content,
                model_used=self.config.name,
                model_type=self.config.model_type,
                response_time=response_time,
                confidence=0.7,  # 规则引擎置信度较低
                raw_response={"rule_based": True}
            )
                
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"规则引擎异常: {str(e)}"
            self.update_performance(False, response_time, error_msg)
            return AIResponse(
                success=False,
                content="",
                model_used=self.config.name,
                model_type=self.config.model_type,
                response_time=response_time,
                error=error_msg
            )


class EnhancedLLMOrchestrator:
    """
    增强版LLM编排器
    支持真实AI模型、本地LLM和智能降级
    """
    
    def __init__(self, mode: str = "ai_first", enable_cache: bool = True):
        """
        初始化增强版编排器
        
        Args:
            mode: 工作模式 (ai_first, rule_only, hybrid, local_only)
            enable_cache: 是否启用缓存
        """
        self.mode = AIMode(mode)
        self.models: Dict[ModelType, BaseAIModel] = {}
        self.cache_enabled = enable_cache
        self.response_cache: Dict[str, AIResponse] = {}
        self.analytics_data: List[Dict] = []
        
        # 初始化所有模型
        self._init_models()
    
    def _init_models(self):
        """初始化所有支持的模型"""
        # DeepSeek模型配置
        deepseek_config = ModelConfig(
            name="DeepSeek",
            model_type=ModelType.DEEPSEEK,
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL,
            model_name=config.DEEPSEEK_MODEL,
            max_tokens=config.DEEPSEEK_MAX_TOKENS,
            timeout=config.DEEPSEEK_TIMEOUT,
            enabled=bool(config.DEEPSEEK_API_KEY),
            priority=1,
            is_local=False
        )
        self.models[ModelType.DEEPSEEK] = DeepSeekModel(deepseek_config)
        
        # OpenAI模型配置
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if openai_key:
            openai_config = ModelConfig(
                name="OpenAI",
                model_type=ModelType.OPENAI,
                api_key=openai_key,
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com"),
                model_name=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                priority=2,
                is_local=False
            )
            self.models[ModelType.OPENAI] = OpenAIModel(openai_config)
        
        # Ollama本地模型
        ollama_config = ModelConfig(
            name="Ollama",
            model_type=ModelType.OLLAMA,
            model_name="llama3.2",  # 默认模型
            base_url="http://localhost:11434",
            priority=3,
            enabled=True,
            is_local=True
        )
        self.models[ModelType.OLLAMA] = OllamaModel(ollama_config)
        
        # 规则引擎（总是可用）
        rule_config = ModelConfig(
            name="RuleEngine",
            model_type=ModelType.RULE_ENGINE,
            enabled=True,
            priority=100,  # 最低优先级
            is_local=True
        )
        self.models[ModelType.RULE_ENGINE] = RuleEngineModel(rule_config)
    
    def get_available_models(self) -> List[Tuple[ModelType, float]]:
        """获取可用的模型列表（按优先级排序）"""
        available = []
        for model_type, model in self.models.items():
            if model.is_available():
                # 计算模型综合评分（优先级 + 可用性）
                score = 1.0 / model.config.priority * model.performance.availability_score
                available.append((model_type, score))
        
        # 按评分排序
        available.sort(key=lambda x: x[1], reverse=True)
        return available
    
    def analyze_target(self, scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        智能分析目标，优先使用真实AI
        
        Args:
            scan_data: 扫描数据
            
        Returns:
            目标分析结果
        """
        if self.mode == AIMode.RULE_ONLY:
            # 仅使用规则引擎
            return self._call_rule_engine(scan_data)
        
        elif self.mode == AIMode.LOCAL_ONLY:
            # 仅使用本地模型
            ai_result = self._call_local_ai(scan_data)
            if ai_result.success:
                return self._format_ai_result(ai_result, "local_ai")
            # 本地模型失败时降级到规则引擎
            return self._call_rule_engine(scan_data)
        
        elif self.mode == AIMode.AI_FIRST:
            # AI优先，失败时降级到规则引擎
            ai_result = self._call_real_ai(scan_data)
            if ai_result.success:
                return self._format_ai_result(ai_result, "real_ai")
            # AI失败时降级到规则引擎
            return self._call_rule_engine(scan_data)
        
        elif self.mode == AIMode.HYBRID:
            # 混合模式：同时调用AI和规则引擎，综合结果
            ai_result = self._call_real_ai(scan_data)
            rule_result = self._call_rule_engine(scan_data)
            
            if ai_result.success:
                # AI成功，使用AI结果为主，规则引擎结果为辅
                result = self._format_ai_result(ai_result, "hybrid_ai_primary")
                result["rule_engine_backup"] = rule_result
                result["decision_method"] = "ai_primary_with_rule_backup"
            else:
                # AI失败，使用规则引擎结果
                result = rule_result
                result["ai_failed"] = True
                result["decision_method"] = "rule_engine_fallback"
            
            return result
    
    def _call_real_ai(self, scan_data: Dict[str, Any]) -> AIResponse:
        """调用真实AI模型"""
        prompt = self._create_target_analysis_prompt(scan_data)
        
        request = AIRequest(
            prompt=prompt,
            system_prompt="你是一个资深网络安全专家，擅长目标分析和风险评估。请提供详细、准确的安全分析。",
            temperature=0.2,
            max_tokens=2000
        )
        
        # 获取可用模型
        available_models = self.get_available_models()
        
        # 过滤出云端AI模型（排除规则引擎和本地模型）
        ai_models = [(mt, score) for mt, score in available_models 
                    if mt not in [ModelType.RULE_ENGINE, ModelType.OLLAMA]]
        
        if not ai_models:
            # 没有可用的云端AI模型
            return AIResponse(
                success=False,
                content="",
                model_used="none",
                model_type=ModelType.RULE_ENGINE,
                response_time=0,
                error="没有可用的云端AI模型"
            )
        
        # 使用评分最高的AI模型
        best_model_type, _ = ai_models[0]
        request.model_type = best_model_type
        
        # 调用模型
        model = self.models.get(best_model_type)
        if model:
            return model.call(request)
        else:
            return AIResponse(
                success=False,
                content="",
                model_used="unknown",
                model_type=best_model_type,
                response_time=0,
                error="模型不存在"
            )
    
    def _call_local_ai(self, scan_data: Dict[str, Any]) -> AIResponse:
        """调用本地AI模型"""
        prompt = self._create_target_analysis_prompt(scan_data)
        
        request = AIRequest(
            prompt=prompt,
            system_prompt="你是一个网络安全专家，请分析以下目标并提供安全建议。",
            temperature=0.3,
            max_tokens=1500
        )
        
        # 尝试使用Ollama
        if ModelType.OLLAMA in self.models:
            ollama_model = self.models[ModelType.OLLAMA]
            if ollama_model.is_available():
                request.model_type = ModelType.OLLAMA
                return ollama_model.call(request)
        
        # 本地模型不可用
        return AIResponse(
            success=False,
            content="",
            model_used="local",
            model_type=ModelType.OLLAMA,
            response_time=0,
            error="本地AI模型不可用",
            is_local_model=True
        )
    
    def _call_rule_engine(self, scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """调用规则引擎"""
        rule_model = self.models.get(ModelType.RULE_ENGINE)
        if not rule_model:
            return {
                "error": "规则引擎不可用",
                "analysis": "规则引擎分析失败",
                "model_used": "rule_engine",
                "mode": "rule_engine_fallback"
            }
        
        prompt = self._create_target_analysis_prompt(scan_data)
        request = AIRequest(prompt=prompt)
        
        response = rule_model.call(request)
        
        if response.success:
            return {
                "analysis": response.content,
                "model_used": response.model_used,
                "response_time": response.response_time,
                "confidence": response.confidence,
                "mode": "rule_engine",
                "is_rule_based": True
            }
        else:
            return {
                "error": response.error,
                "analysis": "规则引擎分析失败",
                "model_used": response.model_used,
                "mode": "rule_engine_fallback"
            }
    
    def _format_ai_result(self, ai_response: AIResponse, mode: str) -> Dict[str, Any]:
        """格式化AI响应结果"""
        # 尝试解析JSON响应
        try:
            analysis_result = json.loads(ai_response.content.strip())
            analysis_result["model_used"] = ai_response.model_used
            analysis_result["model_type"] = ai_response.model_type.value
            analysis_result["response_time"] = ai_response.response_time
            analysis_result["tokens_used"] = ai_response.tokens_used
            analysis_result["mode"] = mode
            analysis_result["is_ai_based"] = True
            analysis_result["is_local_model"] = ai_response.is_local_model
            analysis_result["confidence"] = ai_response.confidence
            
            # 记录分析数据
            self._record_analytics(ai_response, mode)
            
            return analysis_result
        except json.JSONDecodeError:
            # 如果不是JSON，返回原始内容
            return {
                "analysis": ai_response.content,
                "model_used": ai_response.model_used,
                "model_type": ai_response.model_type.value,
                "response_time": ai_response.response_time,
                "tokens_used": ai_response.tokens_used,
                "mode": mode,
                "is_ai_based": True,
                "is_local_model": ai_response.is_local_model,
                "confidence": ai_response.confidence,
                "raw_response": True
            }
    
    def _create_target_analysis_prompt(self, scan_data: Dict[str, Any]) -> str:
        """创建目标分析提示词"""
        # 提取扫描信息
        target = scan_data.get('target', '未知目标')
        scan_time = scan_data.get('scan_time', '未知时间')
        
        ports_info = []
        services_info = []
        
        if "nmap" in scan_data:
            nmap_result = scan_data["nmap"]
            if "ports" in nmap_result:
                for port in nmap_result["ports"][:15]:  # 最多15个端口
                    port_num = port.get('port', '未知')
                    service = port.get('service', '未知服务')
                    state = port.get('state', '未知状态')
                    ports_info.append(f"端口 {port_num}: {service} ({state})")
                    
                    if service != '未知服务' and state == 'open':
                        services_info.append(f"{service} (端口 {port_num})")
        
        # 构建提示词
        prompt = f"""基于以下网络安全扫描结果，请提供详细的目标分析报告：

目标: {target}
扫描时间: {scan_time}

扫描发现:
{chr(10).join(ports_info) if ports_info else '无开放端口发现'}

请提供包含以下部分的分析报告（以JSON格式返回）：
1. 攻击面评估 (attack_surface): 0-10分评分及详细说明
2. 风险评估 (risk_assessment): 低/中/高等级及理由
3. 目标画像 (target_profile): 目标类型、技术栈、潜在业务
4. 漏洞可能性 (vulnerability_likelihood): 各类漏洞可能性评估
5. 攻击优先级建议 (attack_priorities): 建议的攻击路径和优先级
6. 安全建议 (security_recommendations): 针对性的安全加固建议
7. 工具推荐 (tool_recommendations): 适合的渗透测试工具列表

请确保分析专业、准确，基于提供的扫描数据。"""

        if services_info:
            prompt += f"\n\n发现的服务: {', '.join(services_info)}"
        
        return prompt
    
    def _record_analytics(self, response: AIResponse, mode: str):
        """记录分析数据"""
        analytics_record = {
            "timestamp": time.time(),
            "model_used": response.model_used,
            "model_type": response.model_type.value,
            "response_time": response.response_time,
            "success": response.success,
            "mode": mode,
            "is_local": response.is_local_model,
            "tokens_used": response.tokens_used,
            "error": response.error
        }
        self.analytics_data.append(analytics_record)
        
        # 保持最近1000条记录
        if len(self.analytics_data) > 1000:
            self.analytics_data = self.analytics_data[-1000:]
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        if not self.analytics_data:
            return {"total_requests": 0, "summary": "无分析数据"}
        
        total = len(self.analytics_data)
        successful = sum(1 for r in self.analytics_data if r.get("success", False))
        error_rate = 1 - (successful / total) if total > 0 else 0
        
        # 按模型统计
        model_stats = {}
        for record in self.analytics_data:
            model = record.get("model_used", "unknown")
            if model not in model_stats:
                model_stats[model] = {"count": 0, "success": 0, "total_time": 0}
            
            model_stats[model]["count"] += 1
            if record.get("success", False):
                model_stats[model]["success"] += 1
            model_stats[model]["total_time"] += record.get("response_time", 0)
        
        # 计算平均值
        for model, stats in model_stats.items():
            if stats["count"] > 0:
                stats["success_rate"] = stats["success"] / stats["count"]
                stats["avg_time"] = stats["total_time"] / stats["count"]
        
        return {
            "total_requests": total,
            "successful_requests": successful,
            "error_rate": error_rate,
            "model_statistics": model_stats,
            "mode_usage": self._calculate_mode_usage(),
            "performance_summary": {
                "avg_response_time": self._calculate_avg_response_time(),
                "local_model_usage": self._calculate_local_usage()
            }
        }
    
    def _calculate_mode_usage(self) -> Dict[str, int]:
        """计算模式使用情况"""
        mode_counts = {}
        for record in self.analytics_data:
            mode = record.get("mode", "unknown")
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        return mode_counts
    
    def _calculate_avg_response_time(self) -> float:
        """计算平均响应时间"""
        if not self.analytics_data:
            return 0.0
        
        total_time = sum(r.get("response_time", 0) for r in self.analytics_data)
        return total_time / len(self.analytics_data)
    
    def _calculate_local_usage(self) -> float:
        """计算本地模型使用比例"""
        if not self.analytics_data:
            return 0.0
        
        local_count = sum(1 for r in self.analytics_data if r.get("is_local", False))
        return local_count / len(self.analytics_data)
    
    def get_current_mode_info(self) -> Dict[str, Any]:
        """获取当前模式信息"""
        available_models = self.get_available_models()
        
        return {
            "current_mode": self.mode.value,
            "available_models": [
                {
                    "type": mt.value,
                    "name": self.models[mt].config.name if mt in self.models else "Unknown",
                    "priority": self.models[mt].config.priority if mt in self.models else 999,
                    "is_local": self.models[mt].config.is_local if mt in self.models else False,
                    "available": mt in self.models and self.models[mt].is_available(),
                    "performance": {
                        "availability": self.models[mt].performance.availability_score if mt in self.models else 0,
                        "avg_response_time": self.models[mt].performance.average_response_time if mt in self.models else 0,
                        "error_rate": self.models[mt].performance.error_rate if mt in self.models else 0
                    } if mt in self.models else {}
                }
                for mt, _ in available_models
            ],
            "total_models_configured": len(self.models),
            "cache_enabled": self.cache_enabled
        }
    
    def set_mode(self, mode: str):
        """设置工作模式"""
        try:
            self.mode = AIMode(mode)
            return True
        except ValueError:
            return False
    
    def install_local_model(self, model_name: str = "llama3.2") -> Tuple[bool, str]:
        """安装本地模型（Ollama）"""
        if platform.system() == "Windows":
            # Windows安装指南
            return False, "Windows系统请手动安装Ollama：https://ollama.com/download/windows"
        
        try:
            # 检查Ollama是否已安装
            returncode, stdout, stderr = safe_execute(["ollama", "--version"], timeout=30)
            if returncode != 0:
                return False, "Ollama未安装，请先安装Ollama：https://ollama.com"
            
            # 拉取模型
            print(f"正在拉取模型 {model_name}...")
            returncode, stdout, stderr = safe_execute(["ollama", "pull", model_name], timeout=600)  # 10分钟超时

            if returncode == 0:
                # 更新Ollama模型配置
                ollama_model = self.models.get(ModelType.OLLAMA)
                if ollama_model:
                    ollama_model.config.model_name = model_name

                return True, f"模型 {model_name} 安装成功"
            else:
                return False, f"模型拉取失败: {stderr}"
                
        except Exception as e:
            return False, f"安装过程中出错: {str(e)}"


# 测试函数
def test_enhanced_orchestrator():
    """测试增强版LLM编排器"""
    print("=" * 80)
    print("增强版LLM编排器测试 - 第一阶段：真实AI模型集成")
    print("=" * 80)
    
    try:
        # 测试不同模式
        modes = ["ai_first", "rule_only", "hybrid", "local_only"]
        
        for mode in modes:
            print(f"\n测试模式: {mode}")
            print("-" * 40)
            
            orchestrator = EnhancedLLMOrchestrator(mode=mode)
            
            # 获取模式信息
            mode_info = orchestrator.get_current_mode_info()
            print(f"当前模式: {mode_info['current_mode']}")
            print(f"可用模型: {len(mode_info['available_models'])}个")
            
            for model_info in mode_info['available_models']:
                status = "[V]" if model_info['available'] else "[X]"
                print(f"  {status} {model_info['type']}: {model_info['name']} "
                      f"(优先级: {model_info['priority']}, 本地: {model_info['is_local']})")
            
            # 模拟扫描数据
            scan_data = {
                "target": "example.com",
                "scan_time": "2024-01-01 12:00:00",
                "nmap": {
                    "ports": [
                        {"port": 80, "service": "HTTP", "state": "open"},
                        {"port": 443, "service": "HTTPS", "state": "open"},
                        {"port": 22, "service": "SSH", "state": "open"}
                    ]
                }
            }
            
            # 分析目标
            print(f"\n分析目标: {scan_data['target']}")
            start_time = time.time()
            result = orchestrator.analyze_target(scan_data)
            elapsed_time = time.time() - start_time
            
            print(f"分析耗时: {elapsed_time:.2f}秒")
            print(f"使用的模型: {result.get('model_used', 'unknown')}")
            print(f"工作模式: {result.get('mode', 'unknown')}")
            
            if 'error' in result:
                print(f"错误: {result['error']}")
            else:
                print(f"分析成功: {'analysis' in result or '攻击面评估' in str(result)}")
            
            # 获取分析摘要
            analytics = orchestrator.get_analytics_summary()
            print(f"总请求数: {analytics['total_requests']}")
        
        print("\n" + "=" * 80)
        print("增强版LLM编排器测试完成")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_enhanced_orchestrator()
    if success:
        print("\n[SUCCESS] 增强版LLM编排器测试通过!")
    else:
        print("\n[FAILED] 增强版LLM编排器测试失败!")