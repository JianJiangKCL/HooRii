"""
Integration tests for the complete workflow
"""
import pytest
import asyncio
import json
from datetime import datetime

from src.utils.config import load_config
from src.workflows.langraph_workflow import LangGraphHomeAISystem
from src.utils.task_planner import TaskPlanner


class TestWorkflowIntegration:
    """Integration tests for complete system workflow"""

    @pytest.fixture
    def config(self):
        """Load actual configuration"""
        return load_config()

    @pytest.fixture
    def langraph_system(self, config):
        """Create LangGraph system for testing"""
        return LangGraphHomeAISystem(config)

    @pytest.fixture
    def task_planner(self, config):
        """Create TaskPlanner for testing"""
        return TaskPlanner(config)

    @pytest.mark.asyncio
    async def test_end_to_end_conversation(self, langraph_system):
        """Test end-to-end conversation flow"""
        user_id = f"integration_test_user_{datetime.now().timestamp()}"

        # Test basic greeting
        result = await langraph_system.process_message(
            user_input="你好",
            user_id=user_id
        )

        assert result is not None
        assert 'response' in result
        assert result['response'] is not None
        assert len(result['response']) > 0
        assert 'session_id' in result

        # Store session_id for next request
        session_id = result.get('session_id')

        # Test follow-up message
        result2 = await langraph_system.process_message(
            user_input="你叫什么名字？",
            user_id=user_id,
            session_id=session_id
        )

        assert result2 is not None
        assert 'response' in result2
        # Should maintain same session
        assert result2.get('session_id') == session_id

    @pytest.mark.asyncio
    async def test_device_control_flow(self, langraph_system):
        """Test device control workflow"""
        user_id = f"device_test_user_{datetime.now().timestamp()}"

        # Test device control request (should be rejected for new user)
        result = await langraph_system.process_message(
            user_input="打开灯",
            user_id=user_id
        )

        assert result is not None
        assert 'response' in result

        # Parse the response if it's JSON
        if isinstance(result.get('final_response'), str):
            try:
                final_response = json.loads(result['final_response'])
                assert 'response' in final_response
            except:
                # If not JSON, the response itself should be valid
                assert result['response'] is not None

    @pytest.mark.asyncio
    async def test_task_planner_integration(self, task_planner):
        """Test TaskPlanner integration"""
        user_id = f"planner_test_user_{datetime.now().timestamp()}"

        # Test basic flow
        response, conv_id = await task_planner.process_request(
            user_input="测试消息",
            user_id=user_id
        )

        assert response is not None
        assert conv_id is not None
        assert len(response) > 0

        # Test conversation continuity
        response2, conv_id2 = await task_planner.process_request(
            user_input="第二条消息",
            user_id=user_id,
            conversation_id=conv_id
        )

        assert conv_id2 == conv_id
        assert response2 is not None

    @pytest.mark.asyncio
    async def test_error_recovery(self, langraph_system):
        """Test system error recovery"""
        # Test with invalid/malformed input
        result = await langraph_system.process_message(
            user_input="",  # Empty input
            user_id="error_test_user"
        )

        # System should handle gracefully
        assert result is not None
        if 'error' in result:
            assert 'response' in result  # Should still have a response

    @pytest.mark.asyncio
    async def test_session_management(self, task_planner):
        """Test session and context management"""
        user_id = f"session_test_user_{datetime.now().timestamp()}"

        # Create multiple conversations
        conversations = []
        for i in range(3):
            response, conv_id = await task_planner.process_request(
                user_input=f"会话 {i}",
                user_id=user_id
            )
            conversations.append(conv_id)

        # All should have different conversation IDs
        assert len(set(conversations)) == 3

        # Test reusing a conversation
        response, conv_id = await task_planner.process_request(
            user_input="继续会话",
            user_id=user_id,
            conversation_id=conversations[0]
        )

        assert conv_id == conversations[0]

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, task_planner):
        """Test handling of concurrent requests"""
        user_ids = [f"concurrent_user_{i}_{datetime.now().timestamp()}" for i in range(5)]

        # Create concurrent requests
        tasks = []
        for user_id in user_ids:
            task = task_planner.process_request(
                user_input="并发测试",
                user_id=user_id
            )
            tasks.append(task)

        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete successfully
        for result in results:
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent request failed: {result}")
            else:
                response, conv_id = result
                assert response is not None
                assert conv_id is not None


class TestDatabaseIntegration:
    """Test database-related integration"""

    @pytest.mark.asyncio
    async def test_user_creation_and_familiarity(self, task_planner):
        """Test user creation and familiarity tracking"""
        user_id = f"familiarity_test_{datetime.now().timestamp()}"

        # First interaction - new user with default familiarity
        response1, _ = await task_planner.process_request(
            user_input="第一次见面",
            user_id=user_id
        )

        # Get user from database
        user = task_planner.db_service.get_or_create_user(user_id)
        initial_familiarity = user.familiarity_score

        assert initial_familiarity == task_planner.config.system.default_familiarity_score

        # Multiple interactions (in real system, familiarity would increase)
        for i in range(3):
            await task_planner.process_request(
                user_input=f"交互 {i}",
                user_id=user_id
            )

        # Check if user still exists
        user = task_planner.db_service.get_or_create_user(user_id)
        assert user.id == user_id