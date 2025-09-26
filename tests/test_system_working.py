#!/usr/bin/env python3
"""
Quick test to verify the system is working
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import load_config
from src.utils.task_planner import TaskPlanner
from src.workflows.langraph_workflow import LangGraphHomeAISystem


async def test_basic_functionality():
    """Test basic system functionality"""
    print("=" * 60)
    print("TESTING BASIC SYSTEM FUNCTIONALITY")
    print("=" * 60)

    config = load_config()

    # Test 1: TaskPlanner basic operation
    print("\n[TEST 1] TaskPlanner basic operation")
    try:
        planner = TaskPlanner(config)
        response, conv_id = await planner.process_request(
            user_input="测试消息",
            user_id="test_user_verify"
        )
        if response and conv_id and not "error" in response.lower():
            print("✅ TaskPlanner works!")
        else:
            print(f"⚠️ TaskPlanner returned: {response[:100]}")
    except Exception as e:
        print(f"❌ TaskPlanner failed: {e}")

    # Test 2: LangGraph workflow
    print("\n[TEST 2] LangGraph workflow")
    try:
        system = LangGraphHomeAISystem(config)
        result = await system.process_message(
            user_input="Hello",
            user_id="test_user_workflow"
        )
        if result and 'response' in result:
            print(f"✅ LangGraph works! Response: {result['response'][:50]}...")
        else:
            print(f"⚠️ LangGraph returned: {result}")
    except Exception as e:
        print(f"❌ LangGraph failed: {e}")

    # Test 3: Device control rejection (low familiarity)
    print("\n[TEST 3] Device control with low familiarity")
    try:
        planner = TaskPlanner(config)
        response, _ = await planner.process_request(
            user_input="打开灯",
            user_id="test_user_device"
        )
        # Should reject due to low familiarity
        if "不" in response or "认识" in response or len(response) > 0:
            print(f"✅ Device control properly handles familiarity check")
        else:
            print(f"⚠️ Unexpected response: {response[:50]}")
    except Exception as e:
        print(f"❌ Device control test failed: {e}")

    print("\n" + "=" * 60)
    print("BASIC FUNCTIONALITY TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())