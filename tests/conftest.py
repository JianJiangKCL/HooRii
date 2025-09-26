"""
Pytest configuration and fixtures for all tests
"""
import pytest
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import Config, SystemConfig
from src.core.context_manager import SystemContext

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_config():
    """Create a test configuration"""
    from unittest.mock import MagicMock
    from src.utils.config import AnthropicConfig, LangfuseConfig

    config = MagicMock()
    config.anthropic = MagicMock()
    config.anthropic.api_key = "test-api-key"
    config.langfuse = MagicMock()
    config.langfuse.enabled = False
    config.system = SystemConfig(
        default_familiarity_score=50,
        max_history_storage=10,
        max_conversation_turns=5
    )
    return config

@pytest.fixture
def mock_context():
    """Create a mock SystemContext for testing"""
    ctx = SystemContext(
        user_input="Test input",
        familiarity_score=50,
        conversation_tone="neutral"
    )
    ctx.conversation_history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"}
    ]
    return ctx

@pytest.fixture
def mock_intent_response():
    """Mock intent analysis response"""
    return {
        "involves_hardware": False,
        "requires_status": False,
        "requires_memory": False,
        "confidence": 0.9,
        "device": None,
        "action": None
    }