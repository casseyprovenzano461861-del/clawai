"""
Pytest configuration and fixtures for ClawAI tests.
"""
import sys
import os
from pathlib import Path
from typing import Generator, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

import pytest
from dotenv import load_dotenv

# Load test environment variables
test_env_path = project_root / ".env.test"
if test_env_path.exists():
    load_dotenv(test_env_path)
else:
    # Load default .env file for testing
    load_dotenv(project_root / ".env.example")

# Test configuration
TEST_CONFIG = {
    "environment": "testing",
    "database_url": "sqlite:///:memory:",
    "log_level": "DEBUG",
    "enable_real_attack": False,
}


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment before all tests."""
    # Set environment variables for testing
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DATABASE_URL"] = TEST_CONFIG["database_url"]
    os.environ["LOG_LEVEL"] = TEST_CONFIG["log_level"]
    os.environ["ENABLE_REAL_ATTACK"] = str(TEST_CONFIG["enable_real_attack"])

    print(f"\n=== Test Environment Setup ===")
    print(f"Environment: {os.getenv('ENVIRONMENT')}")
    print(f"Database: {os.getenv('DATABASE_URL')}")
    print(f"Log Level: {os.getenv('LOG_LEVEL')}")
    print("=============================\n")

    yield

    # Cleanup after tests
    print("\n=== Test Environment Cleanup ===")


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    class MockLLMClient:
        def __init__(self):
            self.responses = []
            self.requests = []

        def generate(self, prompt: str, **kwargs) -> str:
            self.requests.append(prompt)
            # Return mock response
            if "nmap" in prompt.lower():
                return "<CMD>nmap -sV -sC example.com</CMD>"
            elif "scan" in prompt.lower():
                return "Scanning completed. Found open ports: 80, 443"
            else:
                return "Mock response for testing"

        def reset(self):
            self.responses = []
            self.requests = []

    return MockLLMClient()


@pytest.fixture
def secure_validator():
    """Fixture for secure input validator."""
    from src.shared.backend.security.input_validation import get_secure_validator
    return get_secure_validator()


@pytest.fixture
def per_planner():
    """Fixture for PERPlanner."""
    from src.shared.backend.per.planner import PERPlanner
    planner = PERPlanner()
    planner.clear_history()  # Start with clean state
    return planner


@pytest.fixture
def sample_target_info():
    """Sample target information for testing."""
    return {
        "target": "test.example.com",
        "type": "web_application",
        "description": "Test target for unit tests",
        "ports": [80, 443],
        "services": ["http", "https"]
    }


@pytest.fixture
async def test_client():
    """Async test client for FastAPI."""
    # Note: This needs to be implemented when we have the FastAPI app
    # For now, return a simple mock
    class MockTestClient:
        def __init__(self):
            self.base_url = "http://testserver"

        async def get(self, url: str, **kwargs):
            return MockResponse(200, {"message": "OK"})

        async def post(self, url: str, json: Any = None, **kwargs):
            return MockResponse(201, {"message": "Created", "data": json})

    class MockResponse:
        def __init__(self, status_code: int, json_data: Any):
            self.status_code = status_code
            self._json_data = json_data

        def json(self):
            return self._json_data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP Error: {self.status_code}")

    return MockTestClient()


# Configure pytest
def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow tests"
    )
    parser.addoption(
        "--test-perf",
        action="store_true",
        default=False,
        help="Run performance tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on command line options."""
    skip_slow = pytest.mark.skip(reason="Need --run-slow option to run")
    skip_perf = pytest.mark.skip(reason="Need --test-perf option to run")

    for item in items:
        if "slow" in item.keywords and not config.getoption("--run-slow"):
            item.add_marker(skip_slow)
        if "perf" in item.keywords and not config.getoption("--test-perf"):
            item.add_marker(skip_perf)


# Test markers
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "perf: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers",
        "unit: marks tests as unit tests"
    )