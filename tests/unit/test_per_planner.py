"""
tests/unit/test_per_planner.py

PERPlanner 与 VulnValidatorAgent 的单元测试
仅测试非 LLM 路径（规则模式、数据结构、历史记录）
"""

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import asdict


# ---------------------------------------------------------------------------
# PERPlanner 测试
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestPERPlannerInit:
    """PERPlanner 初始化测试"""

    def test_default_init_without_llm(self):
        from src.shared.backend.per.planner import PERPlanner
        planner = PERPlanner(use_llm=False)
        assert planner.use_llm is False
        assert planner.llm_client is None
        assert planner.llm_integration is None
        assert planner.planning_history == []
        assert planner.rejected_strategies == []
        assert planner.long_term_objectives == []
        assert planner.environment_context == {}

    def test_use_llm_true_but_no_client_falls_back(self):
        """use_llm=True 但 llm_client=None 时，实际 use_llm 应为 False"""
        from src.shared.backend.per.planner import PERPlanner
        planner = PERPlanner(llm_client=None, use_llm=True)
        assert planner.use_llm is False

    def test_output_mode_stored(self):
        from src.shared.backend.per.planner import PERPlanner
        planner = PERPlanner(use_llm=False, output_mode="debug")
        assert planner.output_mode == "debug"


@pytest.mark.unit
class TestPERPlannerRulesBasedPlanning:
    """规则模式规划测试（不依赖 LLM）"""

    @pytest.fixture
    def planner(self):
        from src.shared.backend.per.planner import PERPlanner
        p = PERPlanner(use_llm=False)
        p.clear_history()
        return p

    async def test_pentest_goal_generates_4_operations(self, planner):
        ops = await planner.generate_initial_plan(
            "对 example.com 进行渗透测试",
            {"target": "example.com"},
        )
        assert len(ops) == 4
        assert all(op["command"] == "ADD_NODE" for op in ops)

    async def test_pentest_plan_has_correct_priorities(self, planner):
        ops = await planner.generate_initial_plan(
            "渗透测试 example.com",
            {"target": "example.com"},
        )
        priorities = [op["node_data"]["priority"] for op in ops]
        assert priorities == [1, 2, 3, 4]

    async def test_pentest_plan_has_dependencies(self, planner):
        ops = await planner.generate_initial_plan(
            "安全测试 example.com",
            {"target": "example.com"},
        )
        # 第一个无依赖，后续有依赖
        assert "dependencies" not in ops[0]["node_data"]
        assert "dependencies" in ops[1]["node_data"]
        assert ops[1]["node_data"]["dependencies"] == ["recon_example.com"]

    async def test_scan_goal_generates_3_operations(self, planner):
        ops = await planner.generate_initial_plan(
            "漏洞扫描 target.local",
            {"target": "target.local"},
        )
        assert len(ops) == 3
        assert all(op["command"] == "ADD_NODE" for op in ops)

    async def test_recon_goal_generates_3_operations(self, planner):
        ops = await planner.generate_initial_plan(
            "信息收集 target.local",
            {"target": "target.local"},
        )
        assert len(ops) == 3

    async def test_recon_goal_with_alias_keyword(self, planner):
        """侦察 关键词也能触发信息收集规划"""
        ops = await planner.generate_initial_plan(
            "侦察 target.local",
            {"target": "target.local"},
        )
        assert len(ops) == 3

    async def test_general_goal_generates_3_operations(self, planner):
        ops = await planner.generate_initial_plan(
            "任意目标",
            {"target": "unknown"},
        )
        assert len(ops) == 3

    async def test_operations_contain_node_data(self, planner):
        ops = await planner.generate_initial_plan(
            "渗透测试 example.com",
            {"target": "example.com"},
        )
        for op in ops:
            assert "node_data" in op
            nd = op["node_data"]
            assert "id" in nd
            assert "description" in nd
            assert "type" in nd
            assert "status" in nd

    async def test_target_from_target_info(self, planner):
        ops = await planner.generate_initial_plan(
            "渗透测试 target",
            {"target": "custom.host"},
        )
        assert ops[0]["node_data"]["id"] == "recon_custom.host"


@pytest.mark.unit
class TestPERPlannerHistoryTracking:
    """规划历史追踪测试"""

    @pytest.fixture
    def planner(self):
        from src.shared.backend.per.planner import PERPlanner
        p = PERPlanner(use_llm=False)
        p.clear_history()
        return p

    async def test_generate_initial_plan_records_history(self, planner):
        await planner.generate_initial_plan("渗透测试 t.local", {"target": "t.local"})
        assert len(planner.planning_history) == 1

    async def test_planning_attempt_has_correct_fields(self, planner):
        await planner.generate_initial_plan("渗透测试 t.local", {"target": "t.local"})
        attempt = planner.planning_history[0]
        assert attempt.strategy is not None
        assert attempt.goal == "渗透测试 t.local"
        assert attempt.outcome_summary is not None
        assert isinstance(attempt.graph_operations, list)
        assert len(attempt.graph_operations) > 0
        assert attempt.timestamp is not None

    def test_record_planning_attempt_manually(self, planner):
        planner.record_planning_attempt(
            strategy="测试策略",
            goal="测试目标",
            outcome_summary="测试结果",
            graph_operations=[{"command": "ADD_NODE", "node_data": {"id": "t1"}}],
        )
        assert len(planner.planning_history) == 1
        assert planner.planning_history[0].strategy == "测试策略"

    def test_record_rejected_strategy(self, planner):
        planner.record_rejected_strategy(
            strategy="激进攻击",
            reason="风险过高",
            context={"target": "prod"},
        )
        assert len(planner.rejected_strategies) == 1
        rejected = planner.rejected_strategies[0]
        assert rejected["strategy"] == "激进攻击"
        assert rejected["reason"] == "风险过高"
        assert "timestamp" in rejected

    def test_needs_compression_after_20_attempts(self, planner):
        for i in range(21):
            planner.record_planning_attempt(
                strategy=f"策略{i}",
                goal="目标",
                outcome_summary="结果",
                graph_operations=[],
            )
        assert planner.needs_compression() is True

    def test_no_compression_needed_under_20(self, planner):
        for i in range(19):
            planner.record_planning_attempt(
                strategy=f"策略{i}",
                goal="目标",
                outcome_summary="结果",
                graph_operations=[],
            )
        assert planner.needs_compression() is False

    def test_mark_compressed_resets_flag(self, planner):
        for i in range(21):
            planner.record_planning_attempt(
                strategy=f"策略{i}",
                goal="目标",
                outcome_summary="结果",
                graph_operations=[],
            )
        assert planner.needs_compression() is True
        planner.mark_compressed()
        assert planner.needs_compression() is False


@pytest.mark.unit
class TestPERPlannerEnvironmentAndObjectives:
    """环境上下文和长期目标测试"""

    @pytest.fixture
    def planner(self):
        from src.shared.backend.per.planner import PERPlanner
        p = PERPlanner(use_llm=False)
        p.clear_history()
        return p

    def test_set_environment_context(self, planner):
        ctx = {"network": "internal", "os": "linux"}
        planner.set_environment_context(ctx)
        assert planner.environment_context == ctx

    def test_add_long_term_objective(self, planner):
        planner.add_long_term_objective("获取系统权限")
        planner.add_long_term_objective("获取数据库数据")
        assert len(planner.long_term_objectives) == 2
        assert "获取系统权限" in planner.long_term_objectives


@pytest.mark.unit
class TestPERPlannerClearHistory:
    """clear_history 测试"""

    def test_clears_all_history(self):
        from src.shared.backend.per.planner import PERPlanner
        planner = PERPlanner(use_llm=False)
        planner.record_planning_attempt("s", "g", "o", [])
        planner.record_rejected_strategy("s", "r", {})
        planner._needs_compression = True
        planner.compressed_history_summary = "summary"
        planner.compression_count = 5

        planner.clear_history()

        assert planner.planning_history == []
        assert planner.rejected_strategies == []
        assert planner._needs_compression is False
        assert planner.compressed_history_summary is None
        assert planner.compression_count == 0


@pytest.mark.unit
class TestPERPlannerSummary:
    """get_planning_summary 测试"""

    def test_summary_structure(self):
        from src.shared.backend.per.planner import PERPlanner
        planner = PERPlanner(use_llm=False)
        planner.clear_history()
        planner.add_long_term_objective("目标A")

        summary = planner.get_planning_summary()

        assert "total_attempts" in summary
        assert "recent_strategies" in summary
        assert "rejected_strategies_count" in summary
        assert "long_term_objectives" in summary
        assert "use_llm" in summary
        assert "needs_compression" in summary
        assert summary["use_llm"] is False
        assert "目标A" in summary["long_term_objectives"]


@pytest.mark.unit
class TestPERPlannerDynamicReplanRules:
    """动态重规划（规则模式）测试"""

    @pytest.fixture
    def planner(self):
        from src.shared.backend.per.planner import PERPlanner
        p = PERPlanner(use_llm=False)
        p.clear_history()
        return p

    async def test_deprecate_failed_nodes(self, planner):
        graph_state = {
            "nodes": {
                "recon_x": {"status": "completed"},
                "vuln_x": {"status": "failed", "priority": 2},
            }
        }
        intelligence = {"findings": [], "audit_result": {"status": "in_progress"}}

        ops = await planner.dynamic_replan("渗透测试 x", graph_state, intelligence)

        deprecate_ops = [op for op in ops if op["command"] == "DEPRECATE_NODE"]
        assert len(deprecate_ops) == 1
        assert deprecate_ops[0]["node_id"] == "vuln_x"

    async def test_alternative_task_created_for_failed_node(self, planner):
        graph_state = {
            "nodes": {
                "vuln_x": {"status": "failed", "priority": 2},
            }
        }
        intelligence = {"findings": [], "audit_result": {"status": "in_progress"}}

        ops = await planner.dynamic_replan("渗透测试 x", graph_state, intelligence)

        alt_ops = [op for op in ops if op["command"] == "ADD_NODE"
                    and "alternative" in op["node_data"].get("id", "")]
        assert len(alt_ops) == 1
        assert alt_ops[0]["node_data"]["id"] == "vuln_x_alternative"

    async def test_findings_generate_followup_tasks(self, planner):
        graph_state = {"nodes": {}}
        intelligence = {
            "findings": ["发现SQL注入", "发现XSS"],
            "audit_result": {"status": "in_progress"},
        }

        ops = await planner.dynamic_replan("目标", graph_state, intelligence)

        followup_ops = [op for op in ops if op["command"] == "ADD_NODE"
                        and "followup_" in op["node_data"].get("id", "")]
        assert len(followup_ops) == 2

    async def test_goal_achieved_returns_empty(self, planner):
        graph_state = {"nodes": {}}
        intelligence = {
            "findings": [],
            "audit_result": {"status": "goal_achieved"},
        }

        ops = await planner.dynamic_replan("目标", graph_state, intelligence)
        assert ops == []

    async def test_max_3_followup_tasks(self, planner):
        graph_state = {"nodes": {}}
        intelligence = {
            "findings": ["f1", "f2", "f3", "f4", "f5"],
            "audit_result": {"status": "in_progress"},
        }

        ops = await planner.dynamic_replan("目标", graph_state, intelligence)

        followup_ops = [op for op in ops if op["command"] == "ADD_NODE"
                        and "followup_" in op["node_data"].get("id", "")]
        assert len(followup_ops) <= 3


# ---------------------------------------------------------------------------
# ValidationResult 数据类测试
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestValidationResultDataclass:
    """ValidationResult 数据类基本测试"""

    def test_default_values(self):
        from src.shared.backend.per.validator import ValidationResult
        r = ValidationResult()
        assert r.verified is False
        assert r.vuln_type == "unknown"
        assert r.target == ""
        assert r.evidence == []
        assert r.confidence == 0.0
        assert r.exploit_proof == ""
        assert r.suggested_next == ""
        assert r.raw_findings == []
        assert r.error is None

    def test_custom_values(self):
        from src.shared.backend.per.validator import ValidationResult
        r = ValidationResult(
            verified=True,
            vuln_type="sqli",
            target="http://test.local",
            evidence=["Payload: ' OR 1=1--"],
            confidence=0.92,
            exploit_proof="SQL注入已验证",
            suggested_next="dump 数据库",
        )
        assert r.verified is True
        assert r.vuln_type == "sqli"
        assert len(r.evidence) == 1

    def test_to_dict(self):
        from src.shared.backend.per.validator import ValidationResult
        r = ValidationResult(verified=True, vuln_type="xss", confidence=0.8)
        d = r.to_dict()
        assert d["verified"] is True
        assert d["vuln_type"] == "xss"
        assert d["confidence"] == 0.8
        assert "evidence" in d
        assert "error" in d


# ---------------------------------------------------------------------------
# VulnValidatorAgent 失败安全测试
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestVulnValidatorAgentFallback:
    """VulnValidatorAgent 在检测器不可用时的失败安全测试"""

    def test_exception_in_dispatch_returns_unverified(self):
        from src.shared.backend.per.validator import VulnValidatorAgent, ValidationResult
        agent = VulnValidatorAgent(timeout=5)

        with patch.object(agent, "_dispatch", side_effect=RuntimeError("detector unavailable")):
            result = agent.validate({"type": "sqli"}, "http://test.local")

        assert result.verified is False
        assert result.error is not None
        assert "detector unavailable" in result.error

    def test_suggested_next_populated_on_error(self):
        from src.shared.backend.per.validator import VulnValidatorAgent
        agent = VulnValidatorAgent(timeout=5)

        with patch.object(agent, "_dispatch", side_effect=RuntimeError("fail")):
            result = agent.validate({"type": "xss"}, "http://test")

        assert result.suggested_next != ""

    def test_finding_url_overrides_target(self):
        """finding 中的 url 字段应覆盖 target 参数"""
        from src.shared.backend.per.validator import VulnValidatorAgent, ValidationResult
        agent = VulnValidatorAgent(timeout=5)

        with patch.object(agent, "_dispatch") as mock_dispatch:
            mock_dispatch.return_value = ValidationResult(
                verified=True, vuln_type="sqli", target="http://override.local", confidence=0.9,
            )
            result = agent.validate(
                {"type": "sqli", "url": "http://override.local"},
                "http://fallback.local",
            )

        assert result.target == "http://override.local"
