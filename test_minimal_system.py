#!/usr/bin/env python3
"""
Simple test script for the minimal processing system
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.workflows.langraph_workflow import LangGraphHomeAISystem
from src.utils.config import load_config

async def test_minimal_processing():
    """Test the minimal processing system"""
    config = load_config()
    system = LangGraphHomeAISystem(config)

    # Test user inputs
    test_inputs = [
        "你好",  # Simple greeting
        "开灯",  # Device control (requires familiarity)
        "今天天气怎么样？",  # General query
    ]

    print("🧪 Testing Minimal Processing System")
    print("=" * 50)

    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n📝 Test {i}: {user_input}")

        try:
            # Process using minimal mode (already configured as default)
            result = await system.process_message(user_input)

            print(f"🤖 Response: {result.get('character_response', 'No response')}")
            print(f"🔍 Intent: {result.get('intent_analysis', {}).get('involves_hardware', False)}")
            print(f"⏱️  Processing mode: {result.get('metadata', {}).get('processing_type', 'unknown')}")
            print(f"🛡️  Rate limited: {result.get('metadata', {}).get('rate_limited', False)}")

            if result.get('metadata', {}).get('fallback_used'):
                print("⚠️  Fallback response used (API issue)")

        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n✅ Testing completed")

if __name__ == "__main__":
    asyncio.run(test_minimal_processing())