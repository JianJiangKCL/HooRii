"""
Unit tests for TaskPlanner
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import uuid

from src.utils.task_planner import TaskPlanner
from src.core.context_manager import SystemContext
from src.services.database_service import UserInfo
from datetime import datetime


class TestTaskPlanner:
    """Test suite for TaskPlanner"""

    @pytest.fixture
    def task_planner(self, test_config):
        """Create TaskPlanner instance for testing"""
        with patch('src.utils.task_planner.DatabaseService'):
            planner = TaskPlanner(test_config)
            # Mock the lazy-loaded components
            planner._intent_analyzer = MagicMock()
            planner._device_controller = MagicMock()
            planner._character_system = MagicMock()
            return planner

    @pytest.fixture
    def mock_user_info(self):
        """Create mock UserInfo"""
        return UserInfo(
            id="test_user",
            username="test_user",
            familiarity_score=50,
            last_seen=datetime.utcnow(),
            created_at=datetime.utcnow()
        )

    @pytest.mark.asyncio
    async def test_process_request_basic_conversation(self, task_planner, mock_user_info):
        """Test processing a basic conversational request"""
        # Setup mocks
        task_planner.db_service.get_or_create_user = MagicMock(return_value=mock_user_info)

        # Mock intent analysis
        mock_intent = {
            "involves_hardware": False,
            "requires_status": False,
            "requires_memory": False,
            "confidence": 0.9
        }
        task_planner._intent_analyzer.analyze_intent = AsyncMock(return_value=mock_intent)

        # Mock character response
        task_planner._character_system.generate_response = AsyncMock(
            return_value="你好，有什么可以帮助你的吗？"
        )

        # Mock database save
        task_planner.db_service.save_message = MagicMock()

        # Execute
        response, conv_id = await task_planner.process_request(
            user_input="你好",
            user_id="test_user",
            conversation_id=None
        )

        # Verify
        assert response == "你好，有什么可以帮助你的吗？"
        assert conv_id is not None
        assert task_planner._intent_analyzer.analyze_intent.called
        assert task_planner._character_system.generate_response.called
        assert task_planner.db_service.save_message.called

    @pytest.mark.asyncio
    async def test_process_request_device_control(self, task_planner, mock_user_info):
        """Test processing a device control request"""
        # Setup mocks
        task_planner.db_service.get_or_create_user = MagicMock(return_value=mock_user_info)

        # Mock intent analysis - device control
        mock_intent = {
            "involves_hardware": True,
            "device": "lights",
            "action": "turn_on",
            "confidence": 0.95
        }
        task_planner._intent_analyzer.analyze_intent = AsyncMock(return_value=mock_intent)

        # Mock device control
        mock_device_result = {
            "success": True,
            "device": "lights",
            "action": "turn_on"
        }
        task_planner._device_controller.process_device_intent = AsyncMock(
            return_value=mock_device_result
        )

        # Mock character response
        task_planner._character_system.generate_response = AsyncMock(
            return_value="灯已经打开了。"
        )

        # Mock database save
        task_planner.db_service.save_message = MagicMock()

        # Execute
        response, conv_id = await task_planner.process_request(
            user_input="打开灯",
            user_id="test_user",
            conversation_id=None
        )

        # Verify
        assert response == "灯已经打开了。"
        assert task_planner._device_controller.process_device_intent.called
        assert task_planner._character_system.generate_response.called

    @pytest.mark.asyncio
    async def test_process_request_empty_input(self, task_planner):
        """Test handling of empty input"""
        response, conv_id = await task_planner.process_request(
            user_input="",
            user_id="test_user"
        )

        assert response == "请输入您的问题或指令。"
        assert conv_id is not None

    @pytest.mark.asyncio
    async def test_process_request_with_existing_conversation(self, task_planner, mock_user_info):
        """Test processing request with existing conversation"""
        # Setup mocks
        task_planner.db_service.get_or_create_user = MagicMock(return_value=mock_user_info)

        # Create first conversation
        mock_intent = {
            "involves_hardware": False,
            "requires_status": False,
            "requires_memory": False
        }
        task_planner._intent_analyzer.analyze_intent = AsyncMock(return_value=mock_intent)
        task_planner._character_system.generate_response = AsyncMock(return_value="第一条回复")
        task_planner.db_service.save_message = MagicMock()

        # First request
        response1, conv_id = await task_planner.process_request(
            user_input="你好",
            user_id="test_user"
        )

        # Second request with same conversation
        task_planner._character_system.generate_response = AsyncMock(return_value="第二条回复")
        response2, conv_id2 = await task_planner.process_request(
            user_input="再见",
            user_id="test_user",
            conversation_id=conv_id
        )

        assert conv_id == conv_id2  # Same conversation ID
        assert response2 == "第二条回复"

        # Check conversation context was reused
        ctx = task_planner.active_conversations[conv_id]
        assert len(ctx.conversation_history) == 4  # 2 user + 2 assistant

    @pytest.mark.asyncio
    async def test_process_request_error_handling(self, task_planner, mock_user_info):
        """Test error handling during request processing"""
        # Setup mocks
        task_planner.db_service.get_or_create_user = MagicMock(return_value=mock_user_info)

        # Mock intent analysis to throw error
        task_planner._intent_analyzer.analyze_intent = AsyncMock(
            side_effect=Exception("Intent analysis failed")
        )

        # Mock fallback response
        task_planner._character_system.generate_response = AsyncMock(
            return_value="抱歉，处理请求时遇到问题。"
        )

        task_planner.db_service.save_message = MagicMock()

        # Execute
        response, conv_id = await task_planner.process_request(
            user_input="测试错误",
            user_id="test_user"
        )

        # Should handle error gracefully
        assert "抱歉" in response or "问题" in response
        assert conv_id is not None

    @pytest.mark.asyncio
    async def test_determine_tone(self, task_planner):
        """Test tone determination based on familiarity"""
        assert task_planner._determine_tone(10) == "formal"
        assert task_planner._determine_tone(30) == "formal"
        assert task_planner._determine_tone(50) == "polite"
        assert task_planner._determine_tone(70) == "casual"
        assert task_planner._determine_tone(90) == "intimate"
        assert task_planner._determine_tone(100) == "intimate"