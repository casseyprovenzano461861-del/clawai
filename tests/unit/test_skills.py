# -*- coding: utf-8 -*-
"""
Unit tests for Skills system from src/shared/backend/skills/
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

os.environ["ENVIRONMENT"] = "testing"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.shared.backend.skills.core import (
    Skill, SkillType, SkillCategory, SkillParameter, SkillExecutor,
)
from src.shared.backend.skills.registry import SkillRegistry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_skill():
    """Create a minimal skill for testing."""
    return Skill(
        id="test_sqli",
        name="Test SQL Injection",
        type=SkillType.POC,
        category=SkillCategory.SQL_INJECTION,
        description="A test skill for SQL injection detection",
        parameters=[
            SkillParameter("target", "string", True, description="Target URL"),
            SkillParameter("param", "string", False, "id", "Parameter name"),
        ],
        target_type="url",
        severity="high",
        tags=["sqli", "test"],
        executor="builtin",
    )


@pytest.fixture
def python_skill():
    """Create a skill with a Python executor."""
    return Skill(
        id="test_python_skill",
        name="Test Python Skill",
        type=SkillType.POC,
        category=SkillCategory.XSS,
        description="A test skill using python executor",
        parameters=[
            SkillParameter("target", "string", True, description="Target URL"),
        ],
        target_type="url",
        severity="medium",
        executor="python",
        code='print("hello from {{target}}")',
    )


# ---------------------------------------------------------------------------
# Skill class
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestSkill:
    def test_skill_creation(self, sample_skill):
        assert sample_skill.id == "test_sqli"
        assert sample_skill.name == "Test SQL Injection"
        assert sample_skill.type == SkillType.POC
        assert sample_skill.category == SkillCategory.SQL_INJECTION
        assert len(sample_skill.parameters) == 2
        assert sample_skill.severity == "high"
        assert sample_skill.enabled is True

    def test_skill_to_dict(self, sample_skill):
        d = sample_skill.to_dict()
        assert d["id"] == "test_sqli"
        assert d["type"] == "poc"  # enum value, not the enum itself
        assert d["category"] == "sqli"
        assert isinstance(d["parameters"], list)
        assert d["parameters"][0]["name"] == "target"

    def test_skill_default_values(self):
        skill = Skill(
            id="minimal",
            name="Minimal",
            type=SkillType.RECON,
            category=SkillCategory.GENERAL,
            description="minimal skill",
            parameters=[],
        )
        assert skill.target_type == "url"
        assert skill.severity == "medium"
        assert skill.cve_id is None
        assert skill.references == []
        assert skill.tags == []
        assert skill.author == "ClawAI"
        assert skill.enabled is True
        assert skill.executor == "python"
        assert skill.code == ""
        assert skill.command_template == ""


# ---------------------------------------------------------------------------
# OpenAI Function Calling schema
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestSkillOpenAISchema:
    def test_schema_basic_structure(self, sample_skill):
        schema = sample_skill.get_openai_schema()
        assert schema["type"] == "function"
        assert "function" in schema
        func = schema["function"]
        assert func["name"] == "skill_test_sqli"
        assert "SQL" in func["description"] or "HIGH" in func["description"]

    def test_schema_includes_parameters(self, sample_skill):
        schema = sample_skill.get_openai_schema()
        params = schema["function"]["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        # target param is added automatically since it's a SkillParameter
        assert "target" in params["properties"]

    def test_schema_required_params(self, sample_skill):
        schema = sample_skill.get_openai_schema()
        required = schema["function"]["parameters"]["required"]
        assert "target" in required  # required=True in the parameter

    def test_schema_auto_adds_target_if_missing(self):
        skill = Skill(
            id="no_target_param",
            name="No Target Param",
            type=SkillType.RECON,
            category=SkillCategory.GENERAL,
            description="skill without target parameter",
            parameters=[],
        )
        schema = skill.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "target" in props
        required = schema["function"]["parameters"]["required"]
        assert "target" in required

    def test_schema_severity_in_description(self, sample_skill):
        schema = sample_skill.get_openai_schema()
        assert "[HIGH]" in schema["function"]["description"]

    def test_schema_param_defaults(self):
        skill = Skill(
            id="with_defaults",
            name="With Defaults",
            type=SkillType.SCANNER,
            category=SkillCategory.GENERAL,
            description="skill with default params",
            parameters=[
                SkillParameter("count", "integer", False, 5, "Number of attempts"),
            ],
        )
        schema = skill.get_openai_schema()
        count_prop = schema["function"]["parameters"]["properties"]["count"]
        assert count_prop["default"] == 5


# ---------------------------------------------------------------------------
# SkillExecutor
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestSkillExecutor:
    def test_execute_builtin_skill(self, sample_skill):
        executor = SkillExecutor()
        with patch.object(executor, "_execute_builtin", return_value="detection complete"):
            result = executor.execute(sample_skill, {"target": "http://example.com"})
            assert result["success"] is True
            assert result["skill_id"] == "test_sqli"

    def test_execute_missing_required_param(self, sample_skill):
        executor = SkillExecutor()
        # Remove 'target' from params — it's required
        result = executor.execute(sample_skill, {"param": "id"})
        assert result["success"] is False
        assert "缺少必需参数" in result["error"]

    def test_execute_with_default_param(self, sample_skill):
        executor = SkillExecutor()
        with patch.object(executor, "_execute_builtin", return_value="ok"):
            result = executor.execute(sample_skill, {"target": "http://example.com"})
            # param has default "id", so it should not fail
            assert result["success"] is True

    def test_execute_unknown_executor(self):
        skill = Skill(
            id="bad_executor",
            name="Bad Executor",
            type=SkillType.POC,
            category=SkillCategory.GENERAL,
            description="skill with unknown executor",
            parameters=[SkillParameter("target", "string", True, description="target")],
            executor="unknown_executor",
        )
        executor = SkillExecutor()
        result = executor.execute(skill, {"target": "http://example.com"})
        assert result["success"] is False
        assert "未知的执行器" in result["error"]

    def test_vulnerability_detection_positive(self, sample_skill):
        executor = SkillExecutor()
        with patch.object(executor, "_execute_builtin", return_value="PAYLOAD_HIT found"):
            result = executor.execute(sample_skill, {"target": "http://example.com"})
            assert result["vulnerable"] is True
            assert result["evidence"] is not None

    def test_vulnerability_detection_negative(self, sample_skill):
        executor = SkillExecutor()
        with patch.object(executor, "_execute_builtin", return_value="clean output"):
            result = executor.execute(sample_skill, {"target": "http://example.com"})
            assert result["vulnerable"] is False
            assert result["evidence"] is None

    def test_validate_params_fills_defaults(self):
        skill = Skill(
            id="defaults_test",
            name="Defaults Test",
            type=SkillType.POC,
            category=SkillCategory.GENERAL,
            description="test",
            parameters=[
                SkillParameter("target", "string", True, description="target"),
                SkillParameter("depth", "integer", False, 3, "scan depth"),
            ],
            executor="builtin",
        )
        executor = SkillExecutor()
        validated = executor._validate_params(skill, {"target": "http://x.com"})
        assert validated["depth"] == 3


# ---------------------------------------------------------------------------
# SkillRegistry
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestSkillRegistry:
    def _make_registry_without_extended(self):
        """Create a registry but skip extended skills loading to avoid import errors."""
        with patch.object(SkillRegistry, "_load_extended_skills", lambda self: None):
            with patch.object(SkillRegistry, "_load_enhanced_detection_skills", lambda self: None):
                return SkillRegistry()

    def test_registry_loads_builtin_skills(self):
        reg = self._make_registry_without_extended()
        # Should have loaded at least the 14 built-in skills
        assert len(reg.skills) >= 14

    def test_register_and_get(self):
        reg = self._make_registry_without_extended()
        skill = Skill(
            id="custom_skill",
            name="Custom",
            type=SkillType.RECON,
            category=SkillCategory.GENERAL,
            description="custom skill",
            parameters=[],
        )
        reg.register(skill)
        assert reg.get("custom_skill") is skill

    def test_get_nonexistent_skill(self):
        reg = self._make_registry_without_extended()
        assert reg.get("nonexistent") is None

    def test_unregister(self):
        reg = self._make_registry_without_extended()
        assert reg.get("sqli_basic") is not None
        reg.unregister("sqli_basic")
        assert reg.get("sqli_basic") is None

    def test_list_all_skills(self):
        reg = self._make_registry_without_extended()
        all_skills = reg.list()
        assert len(all_skills) >= 14

    def test_list_filter_by_type(self):
        reg = self._make_registry_without_extended()
        poc_skills = reg.list(type=SkillType.POC)
        assert all(s.type == SkillType.POC for s in poc_skills)

    def test_list_filter_by_category(self):
        reg = self._make_registry_without_extended()
        sqli_skills = reg.list(category=SkillCategory.SQL_INJECTION)
        assert all(s.category == SkillCategory.SQL_INJECTION for s in sqli_skills)

    def test_list_filter_by_severity(self):
        reg = self._make_registry_without_extended()
        critical = reg.list(severity="critical")
        assert all(s.severity == "critical" for s in critical)

    def test_list_filter_by_tags(self):
        reg = self._make_registry_without_extended()
        tagged = reg.list(tags=["sqli"])
        assert all("sqli" in s.tags for s in tagged)

    def test_search_by_name(self):
        reg = self._make_registry_without_extended()
        results = reg.search("SQL注入")
        assert len(results) > 0
        assert any("SQL" in r.name or "注入" in r.name for r in results)

    def test_search_by_description(self):
        reg = self._make_registry_without_extended()
        results = reg.search("UNION")
        assert len(results) > 0

    def test_search_by_tag(self):
        reg = self._make_registry_without_extended()
        results = reg.search("sqli")
        assert len(results) > 0

    def test_search_no_results(self):
        reg = self._make_registry_without_extended()
        results = reg.search("nonexistent_xyz_12345")
        assert results == []

    def test_search_top_k(self):
        reg = self._make_registry_without_extended()
        results = reg.search("注入", top_k=2)
        assert len(results) <= 2

    def test_execute_nonexistent_skill(self):
        reg = self._make_registry_without_extended()
        result = reg.execute("nonexistent_skill", {"target": "http://x.com"})
        assert result["success"] is False
        assert "技能不存在" in result["error"]

    def test_execute_existing_skill(self):
        reg = self._make_registry_without_extended()
        with patch.object(reg.executor, "execute", return_value={
            "skill_id": "sqli_basic",
            "skill_name": "SQL注入基础检测",
            "success": True,
            "vulnerable": False,
            "output": "no injection",
            "evidence": None,
            "error": None,
        }):
            result = reg.execute("sqli_basic", {"target": "http://example.com"})
            assert result["success"] is True

    def test_get_openai_tools(self):
        reg = self._make_registry_without_extended()
        tools = reg.get_openai_tools()
        assert len(tools) >= 14
        for tool in tools:
            assert tool["type"] == "function"
            assert "function" in tool
            assert tool["function"]["name"].startswith("skill_")

    def test_get_openai_tools_excludes_disabled(self):
        reg = self._make_registry_without_extended()
        skill = reg.get("sqli_basic")
        skill.enabled = False
        tools = reg.get_openai_tools()
        names = [t["function"]["name"] for t in tools]
        assert "skill_sqli_basic" not in names
        # Clean up
        skill.enabled = True
