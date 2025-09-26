"""
Unit tests for IntentAnalyzer
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from src.core.intent_analyzer import IntentAnalyzer
from src.core.context_manager import SystemContext


class TestIntentAnalyzer:
    """Test suite for IntentAnalyzer"""

    @pytest.fixture
    def analyzer(self, test_config):
        """Create IntentAnalyzer instance for testing"""
        with patch('anthropic.Anthropic'):
            return IntentAnalyzer(test_config)

    @pytest.fixture
    def mock_context(self):
        """Create mock context for testing"""
        ctx = SystemContext(
            user_input="打开灯",
            familiarity_score=50,
            conversation_tone="neutral"
        )
        ctx.conversation_history = []
        return ctx

    @pytest.mark.asyncio
    async def test_analyze_intent_basic_conversation(self, analyzer, mock_context):
        """Test intent analysis for basic conversation"""
        mock_context.user_input = "你好"

        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.content = '''
        {
            "involves_hardware": false,
            "requires_status": false,
            "requires_memory": false,
            "confidence": 0.95,
            "reasoning": "User is greeting"
        }
        '''

        with patch.object(analyzer.claude_client.messages, 'create', return_value=mock_response):
            result = await analyzer.analyze_intent("你好", mock_context)

            assert result is not None
            assert result["involves_hardware"] == False
            assert result["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_analyze_intent_device_control(self, analyzer, mock_context):
        """Test intent analysis for device control"""
        mock_context.user_input = "打开灯"

        # Mock the LLM response for device control
        mock_response = MagicMock()
        mock_response.content = '''
        {
            "involves_hardware": true,
            "requires_status": false,
            "requires_memory": false,
            "confidence": 0.9,
            "device": "lights",
            "action": "turn_on",
            "reasoning": "User wants to turn on the lights"
        }
        '''

        with patch.object(analyzer.claude_client.messages, 'create', return_value=mock_response):
            result = await analyzer.analyze_intent("打开灯", mock_context)

            assert result is not None
            assert result["involves_hardware"] == True
            assert result["device"] == "lights"
            assert result["action"] == "turn_on"

    @pytest.mark.asyncio
    async def test_analyze_intent_status_query(self, analyzer, mock_context):
        """Test intent analysis for status query"""
        mock_context.user_input = "灯开着吗？"

        # Mock the LLM response for status query
        mock_response = MagicMock()
        mock_response.content = '''
        {
            "involves_hardware": false,
            "requires_status": true,
            "requires_memory": false,
            "confidence": 0.85,
            "device": "lights",
            "query_type": "status",
            "reasoning": "User asking about light status"
        }
        '''

        with patch.object(analyzer.claude_client.messages, 'create', return_value=mock_response):
            result = await analyzer.analyze_intent("灯开着吗？", mock_context)

            assert result is not None
            assert result["requires_status"] == True
            assert result["device"] == "lights"

    @pytest.mark.asyncio
    async def test_analyze_intent_error_handling(self, analyzer, mock_context):
        """Test error handling in intent analysis"""
        # Simulate an API error
        with patch.object(analyzer.claude_client.messages, 'create', side_effect=Exception("API Error")):
            result = await analyzer.analyze_intent("测试", mock_context)

            # Should return a fallback response
            assert result is not None
            assert "involves_hardware" in result
            assert result["involves_hardware"] == False

    @pytest.mark.asyncio
    async def test_analyze_intent_invalid_json(self, analyzer, mock_context):
        """Test handling of invalid JSON response"""
        mock_response = MagicMock()
        mock_response.content = "Invalid JSON {not valid}"

        with patch.object(analyzer.claude_client.messages, 'create', return_value=mock_response):
            result = await analyzer.analyze_intent("测试", mock_context)

            # Should return a fallback response
            assert result is not None
            assert "involves_hardware" in result

    @pytest.mark.asyncio
    async def test_analyze_intent_with_context_history(self, analyzer, mock_context):
        """Test intent analysis with conversation history"""
        mock_context.conversation_history = [
            {"role": "user", "content": "我想控制一下家里的设备"},
            {"role": "assistant", "content": "好的，请告诉我您想控制什么设备"},
            {"role": "user", "content": "把它关掉"}  # "它" refers to previous context
        ]
        mock_context.user_input = "把它关掉"

        mock_response = MagicMock()
        mock_response.content = '''
        {
            "involves_hardware": true,
            "requires_status": false,
            "requires_memory": false,
            "confidence": 0.7,
            "device": "unknown",
            "action": "turn_off",
            "reasoning": "User wants to turn off something mentioned earlier"
        }
        '''

        with patch.object(analyzer.claude_client.messages, 'create', return_value=mock_response):
            result = await analyzer.analyze_intent("把它关掉", mock_context)

            assert result is not None
            assert result["involves_hardware"] == True
            assert result["action"] == "turn_off"