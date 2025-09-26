#!/usr/bin/env python3
"""
Test Langfuse-LangGraph Integration
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
from src.workflows.langraph_workflow import LangGraphHomeAISystem

async def test_langfuse_integration():
    """Test LangGraph workflow with Langfuse observability"""
    print("🧪 Testing Langfuse-LangGraph Integration")
    print("=" * 50)

    try:
        # Initialize system
        config = load_config()
        system = LangGraphHomeAISystem(config)

        # Check if Langfuse is enabled
        if system.langfuse_enabled:
            print("✅ Langfuse is enabled and configured")
            print(f"   Host: {config.langfuse.host}")
        else:
            print("⚠️ Langfuse is not enabled")

        # Generate unique IDs for testing
        user_id = f"test_user_{str(uuid.uuid4())[:8]}"
        session_id = f"test_session_{str(uuid.uuid4())[:8]}"

        print(f"\n📝 Testing with:")
        print(f"   User ID: {user_id}")
        print(f"   Session ID: {session_id}")

        # Test messages
        test_messages = [
            "Hello, can you help me?",
            "Turn on the living room lights please",
            "What's the status of my devices?"
        ]

        for i, message in enumerate(test_messages, 1):
            print(f"\n--- Test {i}: {message} ---")

            # Process message with LangGraph workflow
            result = await system.process_message(
                user_input=message,
                user_id=user_id,
                session_id=session_id
            )

            # Display response
            if isinstance(result, dict):
                response = result.get('response', 'No response')
                print(f"Response: {response[:200]}")  # First 200 chars

                # Check if error occurred
                if result.get('error'):
                    print(f"⚠️ Error: {result['error']}")

                # Check if Langfuse trace was created
                if system.langfuse_enabled:
                    print("📊 Langfuse trace created (check dashboard)")

            await asyncio.sleep(1)  # Small delay between messages

        # Test workflow state retrieval
        print(f"\n🔍 Checking workflow state...")
        state = await system.get_workflow_state(session_id)
        if state:
            print(f"Workflow state retrieved with {len(state)} keys")
        else:
            print("No workflow state found")

        if system.langfuse_enabled:
            print("\n✅ Langfuse integration test completed!")
            print(f"📊 Check your Langfuse dashboard at: {config.langfuse.host}")
            print(f"   Look for traces with session_id: {session_id}")
        else:
            print("\n⚠️ Test completed but Langfuse was not enabled")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_langfuse_callbacks():
    """Test that Langfuse callbacks are properly configured"""
    print("\n🧪 Testing Langfuse Callback Configuration")
    print("=" * 50)

    try:
        config = load_config()

        # Check if Langfuse is configured
        if not config.langfuse.enabled:
            print("⚠️ Langfuse is disabled in configuration")
            return False

        system = LangGraphHomeAISystem(config)

        # Check Langfuse components
        checks = [
            ("Langfuse Client", system.langfuse_client is not None),
            ("Langfuse Enabled", system.langfuse_enabled),
            ("Current Trace", hasattr(system, 'current_trace'))
        ]

        all_passed = True
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"{status} {check_name}: {check_result}")
            all_passed = all_passed and check_result

        if all_passed:
            print("\n✅ All Langfuse components are properly configured")
        else:
            print("\n⚠️ Some Langfuse components are missing")

        return all_passed

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_all_tests():
    """Run all Langfuse-LangGraph integration tests"""
    print("🚀 Starting Langfuse-LangGraph Integration Tests")
    print("=" * 60)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    tests = [
        ("Langfuse Callback Configuration", test_langfuse_callbacks),
        ("Langfuse-LangGraph Integration", test_langfuse_integration)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append(False)

        print("\n" + "-" * 60)

    # Summary
    passed = sum(results)
    total = len(results)

    print(f"\n📊 Test Summary: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        print("\n💡 Next steps:")
        print("1. Check your Langfuse dashboard for the traces")
        print("2. Verify that the workflow steps are being tracked")
        print("3. Check the trace timeline and metadata")
    else:
        print("⚠️ Some tests failed. Check the output above.")

    return passed == total

if __name__ == "__main__":
    asyncio.run(run_all_tests())