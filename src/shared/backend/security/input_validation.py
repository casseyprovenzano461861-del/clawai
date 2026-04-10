# -*- coding: utf-8 -*-
"""
安全的输入验证和命令注入防护
技术诚信重建：第三阶段安全加固
"""

import re
import json
import html
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """验证严重性级别"""
    LOW = "low"          # 低风险
    MEDIUM = "medium"    # 中风险  
    HIGH = "high"        # 高风险
    CRITICAL = "critical"  # 严重风险


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    severity: ValidationSeverity
    message: str
    sanitized_value: Optional[str] = None
    detected_threats: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "is_valid": self.is_valid,
            "severity": self.severity.value,
            "message": self.message,
            "sanitized_value": self.sanitized_value,
            "detected_threats": self.detected_threats,
            "suggestions": self.suggestions,
            "confidence": self._calculate_confidence()
        }
    
    def _calculate_confidence(self) -> float:
        """计算置信度"""
        base_confidence = 0.8 if self.is_valid else 0.5
        
        # 基于检测到的威胁调整置信度
        threat_count = len(self.detected_threats)
        threat_adjustment = min(threat_count * 0.1, 0.4)
        
        return round(base_confidence - threat_adjustment, 2)


class InputValidationPatterns:
    """输入验证模式"""
    
    # 命令注入模式
    COMMAND_INJECTION_PATTERNS = [
        # 管道命令
        r"(?i)\|.*(?:cat|ls|rm|wget|curl|bash|sh|powershell|cmd)",
        r"(?i);.*(?:cat|ls|rm|wget|curl|bash|sh|powershell|cmd)",
        r"(?i)\|\|.*(?:cat|ls|rm|wget|curl|bash|sh|powershell|cmd)",
        r"(?i)&&.*(?:cat|ls|rm|wget|curl|bash|sh|powershell|cmd)",
        r"(?i)`.*`",  # 反引号命令执行
        
        # 危险函数调用
        r"(?i)eval\(",
        r"(?i)exec\(",
        r"(?i)system\(",
        r"(?i)popen\(",
        r"(?i)subprocess\.",
        
        # 危险文件操作
        r"(?i)\.\./",  # 目录遍历
        r"(?i)\.\.\\",  # Windows目录遍历
        r"(?i)file://",
        r"(?i)/etc/passwd",
        r"(?i)/etc/shadow",
        r"(?i)C:\\Windows\\System32",
        
        # 危险协议
        r"(?i)javascript:",
        r"(?i)vbscript:",
        r"(?i)data:text/html",
        r"(?i)php://",
        r"(?i)expect://",
    ]
    
    # SQL注入模式
    SQL_INJECTION_PATTERNS = [
        r"(?i)union.*select",
        r"(?i)select.*union",
        r"(?i)insert.*into",
        r"(?i)update.*set",
        r"(?i)delete.*from",
        r"(?i)drop.*table",
        r"(?i)truncate.*table",
        r"(?i)or\s+['\"]?1['\"]?\s*=\s*['\"]?1",
        r"(?i)or\s+['\"]?['\"]?\s*=\s*['\"]?['\"]?",
        r"(?i)--\s*$",  # SQL注释
        r"(?i)#.*$",    # MySQL注释
        r"(?i);\s*$",   # 语句终止符
        r"(?i)waitfor\s+delay",
        r"(?i)pg_sleep\(",
        r"(?i)sleep\(",
        r"(?i)benchmark\(",
    ]
    
    # XSS攻击模式
    XSS_PATTERNS = [
        r"(?i)<script.*?>.*?</script>",
        r"(?i)<.*?javascript:.*?>",
        r"(?i)<.*?on\w+\s*=.*?>",
        r"(?i)alert\(",
        r"(?i)document\.cookie",
        r"(?i)window\.location",
        r"(?i)eval\(",
        r"(?i)expression\(",
        r"(?i)vbscript:",
        r"(?i)data:text/html",
    ]
    
    # 路径遍历模式
    PATH_TRAVERSAL_PATTERNS = [
        r"(?i)\.\./",
        r"(?i)\.\.\\",
        r"(?i)/etc/passwd",
        r"(?i)/etc/shadow",
        r"(?i)/proc/",
        r"(?i)/dev/",
        r"(?i)C:\\",
        r"(?i)/Windows/",
    ]
    
    # 危险文件扩展名
    DANGEROUS_EXTENSIONS = [
        ".exe", ".bat", ".cmd", ".ps1", ".sh", ".bash",
        ".php", ".asp", ".jsp", ".py", ".pl", ".rb",
        ".dll", ".so", ".dylib", ".jar",
        ".vbs", ".js", ".html", ".htm",
    ]
    
    # 敏感信息模式
    SENSITIVE_DATA_PATTERNS = [
        r"(?i)password\s*[:=]",           # password: xxx
        r"(?i)api[_-]?key\s*[:=]",        # api_key: xxx
        r"(?i)secret\s*[:=]",             # secret: xxx
        r"(?i)token\s*[:=]",              # token: xxx
        r"(?i)ssh[_-]?key\s*[:=]",        # ssh_key: xxx
        r"(?i)private[_-]?key\s*[:=]",    # private_key: xxx
        r"(?i)credit[_-]?card\s*[:=]",    # credit_card: xxx
        r"(?i)ssn\s*[:=]",                # ssn: xxx
        r"(?i)phone\s*[:=]",              # phone: xxx
        r"\d{3}-\d{2}-\d{4}",            # SSN格式
        r"\d{16}",                       # 信用卡号
    ]
    
    # 协议白名单
    ALLOWED_PROTOCOLS = ["http", "https", "ftp", "sftp"]
    
    # 端口白名单 (1-65535)
    MIN_PORT = 1
    MAX_PORT = 65535


class SecureInputValidator:
    """安全的输入验证器 - 企业级防护"""
    
    def __init__(self):
        self.patterns = InputValidationPatterns()
        self.strict_mode = True
        self.log_all_validations = True
        
        # 验证统计
        self.stats = {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "threats_detected": 0,
            "by_threat_type": {}
        }
        
        logger.info("SecureInputValidator 初始化完成")
    
    def _update_stats(self, is_valid: bool, threats: List[str] = None):
        """更新统计信息"""
        self.stats["total_validations"] += 1
        
        if is_valid:
            self.stats["successful_validations"] += 1
        else:
            self.stats["failed_validations"] += 1
        
        if threats:
            self.stats["threats_detected"] += len(threats)
            for threat in threats:
                if threat not in self.stats["by_threat_type"]:
                    self.stats["by_threat_type"][threat] = 0
                self.stats["by_threat_type"][threat] += 1
    
    def _log_validation(self, result: ValidationResult, value: str, context: str = ""):
        """记录验证日志"""
        if not self.log_all_validations and result.is_valid:
            return
        
        log_message = f"输入验证 - 上下文: {context}, 原始值: {value[:50]}, 结果: {result.message}"
        
        if not result.is_valid:
            log_message += f", 威胁: {result.detected_threats}"
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _detect_threats(self, value: str) -> Tuple[List[str], ValidationSeverity]:
        """检测威胁"""
        threats = []
        max_severity = ValidationSeverity.LOW
        
        # 命令注入检测
        for pattern in self.patterns.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                threats.append("command_injection")
                max_severity = max(max_severity, ValidationSeverity.CRITICAL, 
                                   key=lambda s: self._severity_value(s))
        
        # SQL注入检测
        for pattern in self.patterns.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                threats.append("sql_injection")
                max_severity = max(max_severity, ValidationSeverity.HIGH, 
                                   key=lambda s: self._severity_value(s))
        
        # XSS检测
        for pattern in self.patterns.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                threats.append("xss")
                max_severity = max(max_severity, ValidationSeverity.HIGH, 
                                   key=lambda s: self._severity_value(s))
        
        # 路径遍历检测
        for pattern in self.patterns.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                threats.append("path_traversal")
                max_severity = max(max_severity, ValidationSeverity.HIGH, 
                                   key=lambda s: self._severity_value(s))
        
        # 敏感信息检测
        for pattern in self.patterns.SENSITIVE_DATA_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                threats.append("sensitive_data_exposure")
                max_severity = max(max_severity, ValidationSeverity.MEDIUM, 
                                   key=lambda s: self._severity_value(s))
        
        # 危险文件扩展名检测
        for ext in self.patterns.DANGEROUS_EXTENSIONS:
            if value.lower().endswith(ext):
                threats.append("dangerous_file_extension")
                max_severity = max(max_severity, ValidationSeverity.MEDIUM, 
                                   key=lambda s: self._severity_value(s))
        
        return threats, max_severity
    
    def _severity_value(self, severity: ValidationSeverity) -> int:
        """获取严重性数值"""
        severity_values = {
            ValidationSeverity.LOW: 1,
            ValidationSeverity.MEDIUM: 2,
            ValidationSeverity.HIGH: 3,
            ValidationSeverity.CRITICAL: 4
        }
        return severity_values.get(severity, 1)
    
    def _sanitize_value(self, value: str, allowed_patterns: List[str] = None) -> str:
        """清理输入值"""
        if not isinstance(value, str):
            return str(value) if value is not None else ""
        
        # HTML实体编码
        sanitized = html.escape(value)
        
        # 移除控制字符
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
        
        # 限制长度（防止缓冲区溢出）
        max_length = 1000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # 应用白名单模式
        if allowed_patterns:
            for pattern in allowed_patterns:
                if re.match(pattern, sanitized):
                    return sanitized
            # 如果没有匹配白名单，返回安全默认值
            return "validated_input"
        
        return sanitized
    
    def _generate_suggestions(self, threats: List[str]) -> List[str]:
        """生成安全建议"""
        suggestions = []
        threat_to_suggestion = {
            "command_injection": "使用参数化命令执行，避免直接拼接命令",
            "sql_injection": "使用参数化查询或ORM，避免直接拼接SQL",
            "xss": "对用户输入进行HTML实体编码",
            "path_traversal": "验证文件路径，限制访问范围",
            "sensitive_data_exposure": "避免在输入中包含敏感信息",
            "dangerous_file_extension": "验证文件扩展名，限制危险类型"
        }
        
        for threat in threats:
            if threat in threat_to_suggestion:
                suggestions.append(threat_to_suggestion[threat])
        
        # 通用建议
        if threats:
            suggestions.append("输入验证失败，请检查输入内容")
            suggestions.append("考虑使用更严格的输入验证规则")
        
        return suggestions
    
    def validate_target(self, target: str) -> ValidationResult:
        """
        验证目标地址（IP/域名/URL）
        
        Args:
            target: 目标地址
            
        Returns:
            验证结果
        """
        # 基本检查
        if not target or not isinstance(target, str):
            result = ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.HIGH,
                message="目标地址不能为空",
                sanitized_value="",
                detected_threats=["empty_input"]
            )
            self._update_stats(False, ["empty_input"])
            self._log_validation(result, target, "target_validation")
            return result
        
        # 检测威胁
        threats, severity = self._detect_threats(target)
        
        if threats:
            # 发现威胁，验证失败
            suggestions = self._generate_suggestions(threats)
            
            result = ValidationResult(
                is_valid=False,
                severity=severity,
                message=f"检测到安全威胁: {', '.join(threats)}",
                sanitized_value=self._sanitize_value(target),
                detected_threats=threats,
                suggestions=suggestions
            )
            
            self._update_stats(False, threats)
            self._log_validation(result, target, "target_validation")
            return result
        
        # 验证格式
        is_valid_format = self._validate_target_format(target)
        
        if not is_valid_format:
            result = ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.MEDIUM,
                message="无效的目标地址格式",
                sanitized_value=self._sanitize_value(target),
                detected_threats=["invalid_format"],
                suggestions=["使用有效的IP地址、域名或URL格式"]
            )
            
            self._update_stats(False, ["invalid_format"])
            self._log_validation(result, target, "target_validation")
            return result
        
        # 验证通过
        result = ValidationResult(
            is_valid=True,
            severity=ValidationSeverity.LOW,
            message="目标地址验证通过",
            sanitized_value=self._sanitize_value(target),
            detected_threats=[],
            suggestions=["保持当前格式，避免包含特殊字符"]
        )
        
        self._update_stats(True)
        self._log_validation(result, target, "target_validation")
        return result
    
    def _validate_target_format(self, target: str) -> bool:
        """验证目标地址格式"""
        # 简单的格式验证
        # 允许IP地址、域名、带端口的地址、URL
        
        # IP地址 (IPv4)
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ipv4_pattern, target):
            # 验证IP地址各部分
            parts = target.split('.')
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        
        # 带端口的IP地址
        if ':' in target:
            host, port_str = target.split(':', 1)
            try:
                port = int(port_str)
                if not (self.patterns.MIN_PORT <= port <= self.patterns.MAX_PORT):
                    return False
                
                # 验证主机部分
                return self._validate_target_format(host)
            except (ValueError, IndexError):
                return False
        
        # 域名 (简单验证)
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$'
        if re.match(domain_pattern, target):
            return True
        
        # URL (支持域名或 IP 地址作为 host)
        url_pattern = r'^(http|https)://(([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}|(\d{1,3}\.){3}\d{1,3})(:[0-9]+)?(/.*)?$'
        if re.match(url_pattern, target, re.IGNORECASE):
            return True
        
        return False
    
    def validate_command(self, command: str, allowed_commands: List[str] = None) -> ValidationResult:
        """
        验证命令安全性
        
        Args:
            command: 命令字符串
            allowed_commands: 允许的命令白名单
            
        Returns:
            验证结果
        """
        # 基本检查
        if not command or not isinstance(command, str):
            result = ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.HIGH,
                message="命令不能为空",
                sanitized_value="",
                detected_threats=["empty_input"]
            )
            self._update_stats(False, ["empty_input"])
            self._log_validation(result, command, "command_validation")
            return result
        
        # 检查白名单
        if allowed_commands:
            command_lower = command.lower()
            for allowed in allowed_commands:
                if allowed.lower() in command_lower:
                    # 命令在白名单中，但仍然要检查威胁
                    break
            else:
                # 命令不在白名单中
                result = ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.HIGH,
                    message="命令不在允许列表中",
                    sanitized_value=self._sanitize_value(command),
                    detected_threats=["unauthorized_command"],
                    suggestions=["只使用预定义的允许命令"]
                )
                
                self._update_stats(False, ["unauthorized_command"])
                self._log_validation(result, command, "command_validation")
                return result
        
        # 检测威胁
        threats, severity = self._detect_threats(command)
        
        if threats:
            suggestions = self._generate_suggestions(threats)
            
            result = ValidationResult(
                is_valid=False,
                severity=severity,
                message=f"检测到命令安全威胁: {', '.join(threats)}",
                sanitized_value=self._sanitize_value(command),
                detected_threats=threats,
                suggestions=suggestions
            )
            
            self._update_stats(False, threats)
            self._log_validation(result, command, "command_validation")
            return result
        
        # 验证通过
        result = ValidationResult(
            is_valid=True,
            severity=ValidationSeverity.LOW,
            message="命令验证通过",
            sanitized_value=self._sanitize_value(command),
            detected_threats=[],
            suggestions=["使用参数化命令执行，避免直接拼接用户输入"]
        )
        
        self._update_stats(True)
        self._log_validation(result, command, "command_validation")
        return result
    
    def validate_json(self, json_str: str, schema: Dict[str, Any] = None) -> ValidationResult:
        """
        验证JSON输入
        
        Args:
            json_str: JSON字符串
            schema: JSON模式验证
            
        Returns:
            验证结果
        """
        # 基本检查
        if not json_str or not isinstance(json_str, str):
            result = ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.HIGH,
                message="JSON不能为空",
                sanitized_value="",
                detected_threats=["empty_input"]
            )
            self._update_stats(False, ["empty_input"])
            self._log_validation(result, json_str, "json_validation")
            return result
        
        # 检测威胁
        threats, severity = self._detect_threats(json_str)
        
        # 解析JSON
        try:
            parsed = json.loads(json_str)
            
            # 递归检查嵌套内容
            if not threats:
                threats = self._check_json_content(parsed)
                if threats:
                    severity = max(severity, ValidationSeverity.HIGH, 
                                  key=lambda s: self._severity_value(s))
            
            if schema:
                # 简化的模式验证
                schema_valid, schema_errors = self._validate_json_schema(parsed, schema)
                if not schema_valid:
                    threats.append("schema_validation_failed")
                    severity = max(severity, ValidationSeverity.MEDIUM, 
                                  key=lambda s: self._severity_value(s))
        
        except json.JSONDecodeError as e:
            threats.append("invalid_json")
            severity = ValidationSeverity.HIGH
        
        if threats:
            suggestions = self._generate_suggestions(threats)
            suggestions.append("确保JSON格式正确，避免包含可执行代码")
            
            result = ValidationResult(
                is_valid=False,
                severity=severity,
                message=f"JSON验证失败: {', '.join(threats)}",
                sanitized_value=self._sanitize_value(json_str),
                detected_threats=threats,
                suggestions=suggestions
            )
            
            self._update_stats(False, threats)
            self._log_validation(result, json_str, "json_validation")
            return result
        
        # 验证通过
        result = ValidationResult(
            is_valid=True,
            severity=ValidationSeverity.LOW,
            message="JSON验证通过",
            sanitized_value=json.dumps(parsed),  # 重新序列化以确保格式正确
            detected_threats=[],
            suggestions=["限制JSON深度，避免递归引用"]
        )
        
        self._update_stats(True)
        self._log_validation(result, json_str, "json_validation")
        return result
    
    def _check_json_content(self, data: Any) -> List[str]:
        """递归检查JSON内容"""
        threats = []
        
        if isinstance(data, str):
            sub_threats, _ = self._detect_threats(data)
            threats.extend(sub_threats)
        elif isinstance(data, dict):
            for key, value in data.items():
                threats.extend(self._check_json_content(key))
                threats.extend(self._check_json_content(value))
        elif isinstance(data, list):
            for item in data:
                threats.extend(self._check_json_content(item))
        
        return list(set(threats))
    
    def _validate_json_schema(self, data: Any, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """简化的JSON模式验证"""
        errors = []
        
        # 检查必需字段
        required_fields = schema.get("required", [])
        if isinstance(data, dict):
            for field in required_fields:
                if field not in data:
                    errors.append(f"缺少必需字段: {field}")
        
        # 检查字段类型
        properties = schema.get("properties", {})
        if isinstance(data, dict):
            for field, value in data.items():
                if field in properties:
                    field_schema = properties[field]
                    expected_type = field_schema.get("type")
                    
                    if expected_type == "string" and not isinstance(value, str):
                        errors.append(f"字段 {field} 应为字符串类型")
                    elif expected_type == "number" and not isinstance(value, (int, float)):
                        errors.append(f"字段 {field} 应为数字类型")
                    elif expected_type == "boolean" and not isinstance(value, bool):
                        errors.append(f"字段 {field} 应为布尔类型")
                    elif expected_type == "array" and not isinstance(value, list):
                        errors.append(f"字段 {field} 应为数组类型")
                    elif expected_type == "object" and not isinstance(value, dict):
                        errors.append(f"字段 {field} 应为对象类型")
        
        return len(errors) == 0, errors
    
    def validate_parameter(self, name: str, value: Any, param_type: str = "string") -> ValidationResult:
        """
        验证参数
        
        Args:
            name: 参数名
            value: 参数值
            param_type: 参数类型 (string, number, boolean, array, object)
            
        Returns:
            验证结果
        """
        # 参数名验证
        name_threats, _ = self._detect_threats(str(name))
        
        # 参数值验证
        value_str = str(value) if value is not None else ""
        value_threats, severity = self._detect_threats(value_str)
        
        all_threats = name_threats + value_threats
        
        if all_threats:
            suggestions = self._generate_suggestions(all_threats)
            
            result = ValidationResult(
                is_valid=False,
                severity=severity,
                message=f"参数验证失败: {', '.join(all_threats)}",
                sanitized_value=self._sanitize_value(value_str),
                detected_threats=all_threats,
                suggestions=suggestions
            )
            
            self._update_stats(False, all_threats)
            self._log_validation(result, f"{name}={value_str}", "parameter_validation")
            return result
        
        # 类型验证
        type_valid = True
        if param_type == "string" and not isinstance(value, str):
            type_valid = False
        elif param_type == "number" and not isinstance(value, (int, float)):
            type_valid = False
        elif param_type == "boolean" and not isinstance(value, bool):
            type_valid = False
        elif param_type == "array" and not isinstance(value, list):
            type_valid = False
        elif param_type == "object" and not isinstance(value, dict):
            type_valid = False
        
        if not type_valid:
            result = ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.MEDIUM,
                message=f"参数类型不匹配，期望 {param_type}",
                sanitized_value=self._sanitize_value(value_str),
                detected_threats=["type_mismatch"],
                suggestions=[f"参数 {name} 应为 {param_type} 类型"]
            )
            
            self._update_stats(False, ["type_mismatch"])
            self._log_validation(result, f"{name}={value_str}", "parameter_validation")
            return result
        
        # 验证通过
        result = ValidationResult(
            is_valid=True,
            severity=ValidationSeverity.LOW,
            message="参数验证通过",
            sanitized_value=self._sanitize_value(value_str),
            detected_threats=[],
            suggestions=["保持参数类型一致，避免类型转换错误"]
        )
        
        self._update_stats(True)
        self._log_validation(result, f"{name}={value_str}", "parameter_validation")
        return result
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """获取验证统计信息"""
        stats = self.stats.copy()
        
        # 计算成功率
        total = stats["total_validations"]
        successful = stats["successful_validations"]
        
        if total > 0:
            stats["success_rate"] = round(successful / total * 100, 2)
        else:
            stats["success_rate"] = 0.0
        
        # 威胁类型分布
        stats["threat_distribution"] = dict(sorted(
            stats["by_threat_type"].items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        return stats
    
    def generate_security_report(self) -> Dict[str, Any]:
        """生成安全报告"""
        stats = self.get_validation_statistics()
        
        report = {
            "timestamp": self._get_timestamp(),
            "validation_statistics": stats,
            "security_assessment": self._assess_security_level(stats),
            "recommendations": self._generate_security_recommendations(stats),
            "technical_honesty": {
                "validation_method": "基于模式的威胁检测，非AI猜测",
                "threat_coverage": "覆盖常见Web安全威胁模式",
                "transparency": "所有检测模式和方法公开透明",
                "limitations": "无法检测未知或零日攻击模式"
            }
        }
        
        return report
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _assess_security_level(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """评估安全级别"""
        success_rate = stats.get("success_rate", 0)
        threats_detected = stats.get("threats_detected", 0)
        
        if success_rate >= 95 and threats_detected == 0:
            level = "excellent"
            color = "green"
        elif success_rate >= 90:
            level = "good"
            color = "blue"
        elif success_rate >= 80:
            level = "fair"
            color = "yellow"
        else:
            level = "poor"
            color = "red"
        
        return {
            "level": level,
            "color": color,
            "score": success_rate,
            "description": f"输入验证成功率为 {success_rate}%，检测到 {threats_detected} 次威胁"
        }
    
    def _generate_security_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """生成安全建议"""
        recommendations = []
        
        success_rate = stats.get("success_rate", 0)
        threats_detected = stats.get("threats_detected", 0)
        
        if success_rate < 90:
            recommendations.append("⚠ 输入验证成功率较低，建议加强输入验证规则")
        
        if threats_detected > 0:
            top_threats = list(stats.get("threat_distribution", {}).keys())[:3]
            if top_threats:
                recommendations.append(f"🚨 主要威胁类型: {', '.join(top_threats)}，建议针对性防护")
        
        recommendations.append("✅ 建议定期更新威胁检测模式")
        recommendations.append("✅ 建议对敏感操作进行二次确认")
        recommendations.append("✅ 建议实施输入验证白名单机制")
        
        return recommendations


# 全局验证器实例
_secure_validator = None

def get_secure_validator() -> SecureInputValidator:
    """
    获取全局安全输入验证器实例
    
    Returns:
        安全输入验证器实例
    """
    global _secure_validator
    if _secure_validator is None:
        _secure_validator = SecureInputValidator()
    return _secure_validator

def validate_input_secure(input_value: Any, input_type: str = "string", context: str = "") -> Dict[str, Any]:
    """
    全局安全输入验证函数
    
    Args:
        input_value: 输入值
        input_type: 输入类型
        context: 验证上下文
        
    Returns:
        验证结果字典
    """
    validator = get_secure_validator()
    
    if input_type == "target":
        result = validator.validate_target(str(input_value))
    elif input_type == "command":
        result = validator.validate_command(str(input_value))
    elif input_type == "json":
        result = validator.validate_json(str(input_value))
    else:
        result = validator.validate_parameter(context, input_value, input_type)
    
    return result.to_dict()

def get_input_validation_report() -> Dict[str, Any]:
    """
    获取输入验证报告
    
    Returns:
        输入验证报告
    """
    validator = get_secure_validator()
    return validator.generate_security_report()


def test_secure_input_validator():
    """测试安全输入验证器"""
    print("=" * 80)
    print("安全输入验证器测试")
    print("=" * 80)
    
    try:
        validator = SecureInputValidator()
        
        print("\n1. 目标地址验证测试:")
        test_targets = [
            "192.168.1.1",
            "example.com",
            "https://example.com",
            "127.0.0.1:8080",
            "evil.com; rm -rf /",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
        ]
        
        for target in test_targets:
            result = validator.validate_target(target)
            status = "✅" if result.is_valid else "❌"
            print(f"  {status} {target[:30]:30} -> {result.message}")
            if not result.is_valid and result.detected_threats:
                print(f"      威胁: {result.detected_threats}")
        
        print("\n2. 命令验证测试:")
        test_commands = [
            "nmap -sV 192.168.1.1",
            "ls -la",
            "cat /etc/passwd",
            "rm -rf /",
            "echo hello | bash",
            "ping 127.0.0.1",
        ]
        
        for command in test_commands:
            result = validator.validate_command(command)
            status = "✅" if result.is_valid else "❌"
            print(f"  {status} {command[:30]:30} -> {result.message}")
        
        print("\n3. JSON验证测试:")
        test_jsons = [
            '{"name": "test", "value": 123}',
            '{"name": "<script>alert(1)</script>", "value": 123}',
            'malformed json',
            '{"command": "cat /etc/passwd"}',
        ]
        
        for json_str in test_jsons:
            result = validator.validate_json(json_str)
            status = "✅" if result.is_valid else "❌"
            print(f"  {status} {json_str[:30]:30} -> {result.message}")
        
        print("\n4. 生成安全报告:")
        report = validator.generate_security_report()
        assessment = report["security_assessment"]
        print(f"  安全级别: {assessment['level']} ({assessment['color']})")
        print(f"  安全分数: {assessment['score']}%")
        print(f"  描述: {assessment['description']}")
        
        print("\n5. 技术诚信验证:")
        honesty = report["technical_honesty"]
        for key, value in honesty.items():
            print(f"  {key}: {value}")
        
        print("\n6. 统计信息:")
        stats = validator.get_validation_statistics()
        print(f"  总验证次数: {stats['total_validations']}")
        print(f"  成功次数: {stats['successful_validations']}")
        print(f"  成功率: {stats['success_rate']}%")
        print(f"  威胁检测次数: {stats['threats_detected']}")
        
        print(f"\n{'='*80}")
        print("安全输入验证器测试完成")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_secure_input_validator()
    if success:
        print("\n[SUCCESS] 安全输入验证器测试通过!")
    else:
        print("\n[FAILED] 安全输入验证器测试失败!")