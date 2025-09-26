#!/usr/bin/env python3
"""
Test LangGraph Integration
"""
import asyncio
import sys
import os
import uuid
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config import load_config
from src.workflows.traditional_workflow import create_ai_system

async def test_langraph_integration():
    """Test LangGraph workflow integration"""
    print("🧪 Testing LangGraph Integration")
    print("=" * 50)

    try:
        # Initialize system with LangGraph
        config = load_config()
        system = await create_ai_system(config, use_langgraph=True)

        # Test basic message processing
        print("\n📝 Testing basic message processing...")
        user_id = "test_user_" + str(uuid.uuid4())[:8]
        session_id = "test_session_" + str(uuid.uuid4())[:8]

        test_messages = [
            "Hello, how are you?",
            "Turn on the living room lights",
            "What's the temperature in the bedroom?",
            "Set the air conditioner to 22 degrees"
        ]

        for i, message in enumerate(test_messages, 1):
            print(f"\n--- Test {i}: {message} ---")

            if hasattr(system, 'process_message'):
                # LangGraph system
                result = await system.process_message(message, user_id, session_id)
                print(f"LangGraph Response: {result.get('response', 'No response')}")

                if result.get('intent_analysis'):
                    print(f"Intent: {result['intent_analysis'].get('primary_intent', 'Unknown')}")
                if result.get('device_actions'):
                    print(f"Device Actions: {len(result['device_actions'])} executed")

            else:
                # Traditional system
                response = await system.process_user_input(
                    message,
                    user_id=user_id,
                    session_id=session_id
                )
                print(f"Traditional Response: {response}")

            # Small delay between tests
            await asyncio.sleep(0.5)

        # Test workflow state retrieval if available
        if hasattr(system, 'get_workflow_state'):
            print(f"\n🔍 Testing workflow state retrieval...")
            state = await system.get_workflow_state(session_id)
            if state:
                print(f"Workflow state keys: {list(state.keys())}")
            else:
                print("No workflow state found")

        print("\n✅ LangGraph integration test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_traditional_fallback():
    """Test fallback to traditional workflow"""
    print("\n🧪 Testing Traditional Workflow Fallback")
    print("=" * 50)

    try:
        # Initialize system without LangGraph
        config = load_config()
        system = await create_ai_system(config, use_langgraph=False)

        print("📝 Testing traditional workflow...")
        user_id = "test_user_" + str(uuid.uuid4())[:8]
        session_id = "test_session_" + str(uuid.uuid4())[:8]

        response = await system.process_user_input(
            "Hello, this is a test message",
            user_id=user_id,
            session_id=session_id
        )

        print(f"Traditional workflow response: {response}")
        print("✅ Traditional fallback test completed!")
        return True

    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_all_tests():
    """Run all integration tests"""
    print("🚀 Starting LangGraph Integration Tests")
    print("=" * 60)

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    tests = [
        test_langraph_integration,
        test_traditional_fallback
    ]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)

        print("\n" + "-" * 60)

    # Summary
    passed = sum(results)
    total = len(results)

    print(f"\n📊 Test Summary: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️ Some tests failed. Check the output above.")

    return passed == total

if __name__ == "__main__":
    asyncio.run(run_all_tests())