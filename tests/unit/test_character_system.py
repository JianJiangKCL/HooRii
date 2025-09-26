"""
Unit tests for CharacterSystem
"""
import pytest
from unittest.mock import MagicMock, patch

from src.core.character_system import CharacterSystem
from src.core.context_manager import SystemContext


class TestCharacterSystem:
    """Test suite for CharacterSystem"""

    @pytest.fixture
    def character_system(self, test_config):
        """Create CharacterSystem instance for testing"""
        with patch('anthropic.Anthropic'):
            return CharacterSystem(test_config)

    @pytest.fixture
    def mock_context(self):
        """Create mock context for testing"""
        ctx = SystemContext(
            user_input="你好",
            familiarity_score=30,
            conversation_tone="formal"
        )
        ctx.conversation_history = [
            {"role": "user", "content": "你好"},
        ]
        ctx.current_intent = {
            "involves_hardware": False,
            "confidence": 0.9
        }
        return ctx

    @pytest.mark.asyncio
    async def test_generate_response_basic(self, character_system, mock_context):
        """Test basic response generation"""
        mock_response = MagicMock()
        mock_response.content = "......你好。\n有什么事吗？"

        with patch.object(character_system.claude_client.messages, 'create', return_value=mock_response):
            response = await character_system.generate_response(
                context=mock_context,
                response_data=None
            )

            assert response is not None
            assert "你好" in response or "有什么事" in response

    @pytest.mark.asyncio
    async def test_generate_response_with_device_result(self, character_system, mock_context):
        """Test response generation with device control result"""
        mock_context.current_intent = {
            "involves_hardware": True,
            "device": "lights",
            "action": "turn_on",
            "device_result": {
                "success": True,
                "device": "lights",
                "action": "turn_on"
            }
        }

        mock_response = MagicMock()
        mock_response.content = "......灯已经打开了。"

        with patch.object(character_system.claude_client.messages, 'create', return_value=mock_response):
            response = await character_system.generate_response(
                context=mock_context,
                response_data={"device_result": {"success": True}}
            )

            assert response is not None
            assert len(response) > 0

    @pytest.mark.asyncio
    async def test_generate_response_different_tones(self, character_system):
        """Test response generation with different conversation tones"""
        # Test formal tone (low familiarity)
        ctx_formal = SystemContext(
            user_input="你好",
            familiarity_score=20,
            conversation_tone="formal"
        )
        ctx_formal.conversation_history = []

        mock_response = MagicMock()
        mock_response.content = "......你好。\n我是凌波丽。"

        with patch.object(character_system.claude_client.messages, 'create', return_value=mock_response):
            response = await character_system.generate_response(
                context=ctx_formal,
                response_data=None
            )
            assert response is not None

        # Test intimate tone (high familiarity)
        ctx_intimate = SystemContext(
            user_input="你好",
            familiarity_score=90,
            conversation_tone="intimate"
        )
        ctx_intimate.conversation_history = []

        mock_response.content = "...嗯，你来了。"

        with patch.object(character_system.claude_client.messages, 'create', return_value=mock_response):
            response = await character_system.generate_response(
                context=ctx_intimate,
                response_data=None
            )
            assert response is not None

    @pytest.mark.asyncio
    async def test_generate_response_error_handling(self, character_system, mock_context):
        """Test error handling in response generation"""
        # Simulate an API error
        with patch.object(character_system.claude_client.messages, 'create', side_effect=Exception("API Error")):
            response = await character_system.generate_response(
                context=mock_context,
                response_data=None
            )

            # Should return an error response
            assert response is not None
            assert "出现了问题" in response or "问题" in response

    @pytest.mark.asyncio
    async def test_generate_response_with_conversation_history(self, character_system, mock_context):
        """Test response generation considering conversation history"""
        mock_context.conversation_history = [
            {"role": "user", "content": "你叫什么名字？"},
            {"role": "assistant", "content": "......凌波丽。"},
            {"role": "user", "content": "你喜欢什么？"}
        ]
        mock_context.user_input = "你喜欢什么？"

        mock_response = MagicMock()
        mock_response.content = "......\n我不知道。"

        with patch.object(character_system.claude_client.messages, 'create', return_value=mock_response):
            response = await character_system.generate_response(
                context=mock_context,
                response_data=None
            )

            assert response is not None
            assert len(response) > 0

    @pytest.mark.asyncio
    async def test_generate_idle_response(self, character_system, mock_context):
        """Test idle response generation"""
        mock_response = MagicMock()
        mock_response.content = "......"

        with patch.object(character_system.claude_client.messages, 'create', return_value=mock_response):
            response = await character_system.generate_idle_response(mock_context)

            assert response is not None
            assert "..." in response or "。" in response