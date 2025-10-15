import asyncio
import uuid

import pytest

from src.utils.config import load_config
from src.workflows.langraph_workflow import LangGraphHomeAISystem


@pytest.mark.asyncio
async def test_multi_turn_conversation_retains_context(monkeypatch):
    """Ensure consecutive turns share the same session and context."""
    # Disable outbound TTS calls during tests
    monkeypatch.setenv("OPENAI_TTS_ENABLED", "false")

    config = load_config()
    system = LangGraphHomeAISystem(config)

    try:
        user_id = "test_user_multi_turn"
        session_id = f"test-session-{uuid.uuid4()}"

        # First turn establishes the session
        response_one = await system.process_message(
            user_input="请记住，我叫小明。",
            user_id=user_id,
            session_id=session_id,
        )

        conversation_id = response_one.get("session_id") or session_id
        context = system.task_planner.active_conversations.get(conversation_id)
        assert context is not None, "Conversation context should be stored after first turn"

        first_turn_count = context.message_count
        assert first_turn_count >= 2, "User and assistant messages should be recorded"

        # Second turn should reuse the same conversation and append history
        response_two = await system.process_message(
            user_input="我刚才说我叫什么？",
            user_id=user_id,
            session_id=conversation_id,
        )

        assert response_two.get("session_id") == conversation_id
        assert context.message_count > first_turn_count, "Message count should grow across turns"

        recent_roles = [msg["role"] for msg in context.conversation_history[-4:]]
        assert recent_roles.count("user") >= 2
        assert recent_roles.count("assistant") >= 2

    finally:
        if hasattr(system, "cleanup"):
            await system.cleanup()
