"""P1 stage import verification tests."""

import sys
from pathlib import Path

import pytest

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Modules to verify
MODULES_TO_TEST = [
    ("src.shared.backend.ai.hacksynth.planner", "HackSynthPlanner"),
    ("src.shared.backend.ai.hacksynth.llm_planner", "LLMHackSynthPlanner"),
    ("src.shared.backend.ai.hacksynth.summarizer", "HackSynthSummarizer"),
    ("src.shared.backend.ai.hacksynth.llm_summarizer", "LLMHackSynthSummarizer"),
    ("src.shared.backend.ai.hacksynth.manager", "HackSynthManager"),
    ("src.shared.backend.security.input_validation", "SecureInputValidator"),
    ("src.shared.backend.ai_core.llm_orchestrator", "LLMOrchestrator"),
    ("src.shared.backend.audit.manager", "AuditManager"),
    ("src.shared.backend.monitoring.metrics", "MetricsManager"),
]


@pytest.mark.parametrize("module_path,class_name", MODULES_TO_TEST, ids=[f"{m}.{c}" for m, c in MODULES_TO_TEST])
def test_import(module_path, class_name):
    """Verify core module can be imported and has the expected class."""
    module = __import__(module_path, fromlist=[class_name])
    assert hasattr(module, class_name), f"{class_name} not found in {module_path}"
