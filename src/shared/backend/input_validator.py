# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
输入验证模块
增强安全性，防止注入攻击和恶意输入
"""

import re
import ipaddress
from urllib.parse import urlparse
from typing import Dict, Any, List, Tuple, Optional
from config import config


class InputValidator:
    """输入验证器"""
    
    def __init__(self):
        # 目标验证模式
        self.target_patterns = config.ALLOWED_TARGET_PATTERNS
        
        # 恶意模式检测
        self.malicious_patterns = [
            r"(?i)(union.*select|select.*union)",  # SQL注入 - UNION SELECT
            r"(?i)(or\s+['\"]?1['\"]?\s*=\s*['\"]?1)",  # SQL注入 - OR 1=1
            r"(?i)(<script.*?>.*?</script>)",      # XSS
            r"(?i)(\.\./|\.\.\\)",                 # 目录遍历
            r"(?i)(exec\(|system\(|popen\()",      # 命令注入
            r"(?i)(eval\(|assert\()",              # 代码注入
            r"(?i)(file://|php://|data://)",       # 协议注入
            r"(?i)(javascript:|vbscript:)",        # 脚本协议
            r"(?i)(onload=|onerror=|onclick=)",    # 事件处理器
            r"(?i)(sleep\(|waitfor\s+delay)",      # 时间盲注
            r"(?i)(benchmark\(|pg_sleep\()",       # 性能盲注
            r"(?i)(\|.*cat|\|.*ls|\|.*rm|\|.*wget|\|.*curl)",  # 管道命令注入
        ]
        
        # 端口范围验证
        self.valid_port_range = (1, 65535)
        
        # 最大输入长度
        self.max_target_length = config.MAX_TARGET_LENGTH
        
    def validate_target(self, target: str) -> Tuple[bool, str]:
        """
        验证目标地址
        
        Args:
            target: 目标IP/域名/URL
            
        Returns:
            (是否有效, 错误信息)
        """
        # 检查长度
        if len(target) > self.max_target_length:
            return False, f"目标地址过长，最大长度: {self.max_target_length}"
        
        # 检查恶意模式
        for pattern in self.malicious_patterns:
            if re.search(pattern, target):
                return False, "检测到恶意输入模式"
        
        # 尝试匹配允许的模式
        for pattern in self.target_patterns:
            if re.match(pattern, target):
                return True, "目标地址有效"
        
        # 特殊处理：带端口的IP地址
        if ":" in target:
            parts = target.split(":")
            if len(parts) == 2:
                host, port_str = parts
                try:
                    port = int(port_str)
                    if port < self.valid_port_range[0] or port > self.valid_port_range[1]:
                        return False, f"端口号超出范围 ({self.valid_port_range[0]}-{self.valid_port_range[1]})"
                    
                    # 验证主机部分
                    for pattern in self.target_patterns:
                        if re.match(pattern, host):
                            return True, "带端口的目标地址有效"
                except ValueError:
                    pass
        
        return False, "无效的目标地址格式"
    
    def sanitize_target(self, target: str) -> str:
        """
        清理目标地址
        
        Args:
            target: 原始目标地址
            
        Returns:
            清理后的目标地址
        """
        # 移除多余空格
        target = target.strip()
        
        # 移除控制字符
        target = ''.join(char for char in target if ord(char) >= 32)
        
        # 移除脚本标签
        target = re.sub(r'<script.*?>.*?</script>', '', target, flags=re.IGNORECASE)
        target = re.sub(r'<.*?javascript:.*?>', '', target, flags=re.IGNORECASE)
        
        # 确保URL格式正确
        if target.startswith("http://") or target.startswith("https://"):
            # 解析URL并重建
            try:
                parsed = urlparse(target)
                # 只保留scheme, netloc, path
                sanitized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if parsed.query:
                    # 简单清理查询参数
                    sanitized += "?" + self._sanitize_query(parsed.query)
                return sanitized
            except:
                pass
        
        return target
    
    def _sanitize_query(self, query: str) -> str:
        """清理URL查询参数"""
        # 移除潜在的恶意字符
        sanitized = re.sub(r"[<>\"'`]", "", query)
        # 限制长度
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        return sanitized
    
    def validate_ip_address(self, ip: str) -> bool:
        """
        验证IP地址
        
        Args:
            ip: IP地址
            
        Returns:
            是否有效
        """
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def validate_domain(self, domain: str) -> bool:
        """
        验证域名
        
        Args:
            domain: 域名
            
        Returns:
            是否有效
        """
        # 基本域名验证 - 要求至少有一个点分隔符（有TLD）
        pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)+$"
        return bool(re.match(pattern, domain))
    
    def validate_url(self, url: str) -> bool:
        """
        验证URL
        
        Args:
            url: URL
            
        Returns:
            是否有效
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ["http", "https"]
        except:
            return False
    
    def validate_port(self, port: int) -> bool:
        """
        验证端口号
        
        Args:
            port: 端口号
            
        Returns:
            是否有效
        """
        return self.valid_port_range[0] <= port <= self.valid_port_range[1]
    
    def validate_scan_parameters(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """
        验证扫描参数
        
        Args:
            params: 扫描参数
            
        Returns:
            (是否有效, 错误信息)
        """
        # 检查必需参数
        if "target" not in params:
            return False, "缺少目标参数"
        
        # 验证目标
        target = params["target"]
        is_valid, message = self.validate_target(target)
        if not is_valid:
            return False, f"目标验证失败: {message}"
        
        # 验证可选参数
        if "ports" in params:
            ports = params["ports"]
            if isinstance(ports, list):
                for port in ports:
                    if not isinstance(port, int) or not self.validate_port(port):
                        return False, f"无效的端口号: {port}"
            elif isinstance(ports, str):
                # 处理端口范围字符串，如 "80,443,8080" 或 "1-1000"
                try:
                    port_ranges = ports.split(",")
                    for port_range in port_ranges:
                        if "-" in port_range:
                            start, end = map(int, port_range.split("-"))
                            if not self.validate_port(start) or not self.validate_port(end) or start > end:
                                return False, f"无效的端口范围: {port_range}"
                        else:
                            port = int(port_range)
                            if not self.validate_port(port):
                                return False, f"无效的端口号: {port}"
                except ValueError:
                    return False, "无效的端口格式"
        
        # 验证扫描深度
        if "depth" in params:
            depth = params["depth"]
            if not isinstance(depth, int) or depth < 1 or depth > 10:
                return False, "扫描深度必须在1-10之间"
        
        # 验证超时时间
        if "timeout" in params:
            timeout = params["timeout"]
            if not isinstance(timeout, (int, float)) or timeout < 1 or timeout > 300:
                return False, "超时时间必须在1-300秒之间"
        
        return True, "参数验证通过"
    
    def detect_malicious_input(self, input_str: str) -> Dict[str, Any]:
        """
        检测恶意输入
        
        Args:
            input_str: 输入字符串
            
        Returns:
            检测结果
        """
        results = {
            "is_malicious": False,
            "detected_patterns": [],
            "severity": "low"
        }
        
        # 检查恶意模式
        for pattern in self.malicious_patterns:
            if re.search(pattern, input_str, re.IGNORECASE):
                results["is_malicious"] = True
                results["detected_patterns"].append(pattern)
        
        # 设置严重性
        if results["is_malicious"]:
            # 检查是否有高危模式
            high_severity_patterns = [
                r"(?i)(union.*select|select.*union)",
                r"(?i)(or\s+['\"]?1['\"]?\s*=\s*['\"]?1)",  # SQL注入 - OR 1=1
                r"(?i)(exec\(|system\(|popen\()",
                r"(?i)(eval\(|assert\()",
                r"(?i)(\.\./|\.\.\\)",
                r"(?i)(\|.*cat|\|.*ls|\|.*rm|\|.*wget|\|.*curl)",  # 管道命令注入
            ]
            
            for pattern in high_severity_patterns:
                if any(p == pattern for p in results["detected_patterns"]):
                    results["severity"] = "high"
                    break
            else:
                results["severity"] = "medium"
        
        return results
    
    def get_safe_target(self, target: str) -> str:
        """
        获取安全的目标地址
        
        Args:
            target: 原始目标地址
            
        Returns:
            安全的目标地址
        """
        # 清理目标
        sanitized = self.sanitize_target(target)
        
        # 验证目标
        is_valid, message = self.validate_target(sanitized)
        
        if not is_valid:
            # 如果验证失败，返回默认安全值
            return "127.0.0.1"
        
        return sanitized


# 全局验证器实例
_validator = None

def get_validator() -> InputValidator:
    """
    获取全局输入验证器实例
    
    Returns:
        输入验证器实例
    """
    global _validator
    if _validator is None:
        _validator = InputValidator()
    return _validator

def validate_target(target: str) -> Tuple[bool, str]:
    """
    全局目标验证函数
    
    Args:
        target: 目标地址
        
    Returns:
        (是否有效, 错误信息)
    """
    validator = get_validator()
    return validator.validate_target(target)

def sanitize_target(target: str) -> str:
    """
    全局目标清理函数
    
    Args:
        target: 原始目标地址
        
    Returns:
        清理后的目标地址
    """
    validator = get_validator()
    return validator.sanitize_target(target)

def detect_malicious_input(input_str: str) -> Dict[str, Any]:
    """
    全局恶意输入检测函数
    
    Args:
        input_str: 输入字符串
        
    Returns:
        检测结果
    """
    validator = get_validator()
    return validator.detect_malicious_input(input_str)


def main():
    """测试输入验证器"""
    print("=" * 80)
    print("输入验证器测试")
    print("=" * 80)
    
    validator = get_validator()
    
    # 测试目标验证
    test_targets = [
        "192.168.1.1",
        "example.com",
        "https://example.com",
        "http://localhost:8080",
        "127.0.0.1:3000",
        "evil.com'; DROP TABLE users;--",
        "<script>alert('xss')</script>",
        "../../etc/passwd",
        "example.com:99999",  # 无效端口
        "very-long-domain-name-that-exceeds-the-maximum-allowed-length-very-long-domain-name-that-exceeds-the-maximum-allowed-length-very-long-domain-name-that-exceeds-the-maximum-allowed-length.example.com"
    ]
    
    print("\n目标验证测试:")
    for target in test_targets:
        is_valid, message = validator.validate_target(target)
        status = "✅" if is_valid else "❌"
        print(f"  {status} {target[:50]:50} -> {message}")
    
    # 测试恶意输入检测
    print("\n恶意输入检测测试:")
    malicious_inputs = [
        "normal input",
        "admin' OR '1'='1",
        "<img src=x onerror=alert(1)>",
        "../../../etc/passwd",
        "| cat /etc/passwd",
        "eval('malicious code')"
    ]
    
    for input_str in malicious_inputs:
        result = validator.detect_malicious_input(input_str)
        status = "⚠️ " if result["is_malicious"] else "✅"
        severity = result["severity"]
        print(f"  {status} {input_str[:40]:40} -> 恶意: {result['is_malicious']}, 严重性: {severity}")
    
    # 测试清理功能
    print("\n输入清理测试:")
    dirty_inputs = [
        "  https://example.com/path?query=value  ",
        "http://evil.com/<script>alert(1)</script>",
        "example.com:8080\t\n"
    ]
    
    for dirty in dirty_inputs:
        cleaned = validator.sanitize_target(dirty)
        print(f"  🧹 '{dirty[:30]}...' -> '{cleaned[:30]}...'")
    
    print("\n" + "=" * 80)
    print("测试完成")


if __name__ == "__main__":
    main()