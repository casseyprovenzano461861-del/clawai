"""
tests/unit/test_validator.py

VulnValidatorAgent 和 Reflector 硬规则的单元测试
"""
import pytest
from unittest.mock import MagicMock, patch
from dataclasses import asdict


# ─── ValidatorAgent 测试 ─────────────────────────────────────────────────────

class TestValidationResult:
    """ValidationResult 数据类基本测试"""

    def test_default_values(self):
        from src.shared.backend.per.validator import ValidationResult
        r = ValidationResult()
        assert r.verified is False
        assert r.confidence == 0.0
        assert r.evidence == []
        assert r.error is None

    def test_to_dict_keys(self):
        from src.shared.backend.per.validator import ValidationResult
        r = ValidationResult(verified=True, vuln_type="sqli", target="http://test", confidence=0.9)
        d = r.to_dict()
        for key in ("verified", "vuln_type", "target", "confidence", "evidence", "exploit_proof", "suggested_next"):
            assert key in d

    def test_verified_result(self):
        from src.shared.backend.per.validator import ValidationResult
        r = ValidationResult(
            verified=True,
            vuln_type="xss",
            target="http://example.com",
            evidence=["Payload: <script>alert(1)</script>"],
            confidence=0.92,
        )
        assert r.verified is True
        assert r.confidence > 0.9
        assert len(r.evidence) == 1


class TestVulnValidatorAgentFallback:
    """当 vuln_detector 不可用时的失败安全测试"""

    def test_graceful_failure_when_detector_unavailable(self):
        """导入失败时返回 verified=False 而非抛出异常"""
        from src.shared.backend.per.validator import VulnValidatorAgent
        agent = VulnValidatorAgent(timeout=5)

        # 模拟 _dispatch 抛出异常
        with patch.object(agent, "_dispatch", side_effect=RuntimeError("detector not available")):
            result = agent.validate({"type": "sqli"}, "http://test.local")
        
        assert result.verified is False
        assert result.error is not None
        assert "detector not available" in result.error

    def test_unknown_vuln_type_does_not_crash(self):
        """未知漏洞类型不应崩溃"""
        from src.shared.backend.per.validator import VulnValidatorAgent
        agent = VulnValidatorAgent(timeout=2)

        with patch.object(agent, "_dispatch", return_value=__import__(
            "src.shared.backend.per.validator", fromlist=["ValidationResult"]
        ).ValidationResult(verified=False, vuln_type="unknown", target="http://t")):
            result = agent.validate({"type": "totally_unknown_vuln_42"}, "http://t")

        assert result is not None

    def test_empty_findings_returns_unverified(self):
        """检测器返回空列表时应返回 verified=False"""
        from src.shared.backend.per.validator import VulnValidatorAgent
        agent = VulnValidatorAgent(timeout=2)

        with patch.object(agent, "_dispatch") as mock_dispatch:
            from src.shared.backend.per.validator import ValidationResult
            mock_dispatch.return_value = ValidationResult(
                verified=False,
                vuln_type="sqli",
                target="http://test",
                confidence=0.1,
                exploit_proof="二次验证未能复现漏洞",
            )
            result = agent.validate({"type": "sqli"}, "http://test")

        assert result.verified is False
        assert result.confidence < 0.5


# ─── Reflector 硬规则测试 ────────────────────────────────────────────────────

class TestReflectorHardRules:
    """PERReflector._apply_hard_rules() 的单元测试"""

    @pytest.fixture
    def reflector(self):
        from src.shared.backend.per.reflector import PERReflector
        return PERReflector(llm_client=None, use_llm=False)

    def test_tool_failed_when_success_false(self, reflector):
        result = reflector._apply_hard_rules({"success": False, "error": "timeout"})
        assert result == "tool_failed"

    def test_vuln_found_when_vulnerable_true(self, reflector):
        result = reflector._apply_hard_rules({"success": True, "vulnerable": True})
        assert result == "vuln_found"

    def test_vuln_found_when_vulnerabilities_list(self, reflector):
        result = reflector._apply_hard_rules({
            "success": True,
            "vulnerabilities": [{"type": "xss"}],
        })
        assert result == "vuln_found"

    def test_no_new_finding_when_empty_output(self, reflector):
        result = reflector._apply_hard_rules({"success": True, "findings": [], "output": ""})
        assert result == "no_new_finding"

    def test_none_when_has_output(self, reflector):
        """有实质性输出时不触发硬规则，交给 LLM/规则分析"""
        result = reflector._apply_hard_rules({
            "success": True,
            "findings": [],
            "output": "Nmap scan report for 192.168.1.1 — 22/tcp open ssh",
        })
        assert result is None

    def test_hard_rule_report_tool_failed(self, reflector):
        report = reflector._build_hard_rule_report(
            "task_01",
            "tool_failed",
            {"success": False, "error": "connection refused", "task_type": "reconnaissance"},
            {"description": "扫描目标"},
        )
        assert report["hard_action"] == "switch_tool"
        assert report["hard_rule"] is True
        assert report["audit_result"]["status"] == "failed"

    def test_hard_rule_report_vuln_found(self, reflector):
        report = reflector._build_hard_rule_report(
            "task_02",
            "vuln_found",
            {"success": True, "vulnerable": True, "vulnerabilities": [{"type": "sqli"}]},
            {"description": "SQL注入扫描"},
        )
        assert report["hard_action"] == "trigger_validation"
        assert report["hard_rule"] is True

    def test_hard_rule_report_no_new_finding(self, reflector):
        report = reflector._build_hard_rule_report(
            "task_03",
            "no_new_finding",
            {"success": True, "findings": [], "output": ""},
            {"description": "目录枚举"},
        )
        assert report["hard_action"] == "mutate_payload"
        assert report["hard_rule"] is True


# ─── intelligence_summary 硬规则聚合测试 ─────────────────────────────────────

class TestIntelligenceSummaryAggregation:
    """验证 intelligence_summary 中 pending_validations 等字段的聚合"""

    @pytest.fixture
    def reflector(self):
        from src.shared.backend.per.reflector import PERReflector
        return PERReflector(llm_client=None, use_llm=False)

    def test_pending_validations_aggregated(self, reflector):
        reflections = [
            {
                "subtask_id": "t1",
                "hard_action": "trigger_validation",
                "key_findings": ["SQL error detected"],
                "execution_summary": {"vulnerabilities": [{"type": "sqli"}]},
                "audit_result": {"status": "partial_success"},
            },
        ]
        summary = reflector._generate_intelligence_with_rules(reflections)
        assert "pending_validations" in summary
        assert len(summary["pending_validations"]) == 1

    def test_tool_failures_aggregated(self, reflector):
        reflections = [
            {
                "subtask_id": "t2",
                "hard_action": "switch_tool",
                "key_findings": [],
                "execution_summary": {},
                "audit_result": {"status": "failed"},
            },
        ]
        summary = reflector._generate_intelligence_with_rules(reflections)
        assert "tool_failures" in summary
        assert "t2" in summary["tool_failures"]
