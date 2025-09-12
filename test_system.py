#!/usr/bin/env python3
"""
Test script for the refactored Home AI System
"""
import asyncio
import logging
from main import HomeAISystem

logging.basicConfig(level=logging.INFO)

async def test_system():
    """Test the refactored system with various inputs"""
    system = HomeAISystem()
    
    test_cases = [
        # Test 1: Simple conversation
        {
            "input": "你好",
            "description": "Simple greeting"
        },
        # Test 2: Device control with LLM understanding
        {
            "input": "开灯",
            "description": "Turn on lights"
        },
        # Test 3: Context-dependent reference
        {
            "input": "把它调亮一点",
            "description": "Adjust brightness with reference"
        },
        # Test 4: Implicit intent
        {
            "input": "好热啊",
            "description": "Implicit request to turn on AC"
        },
        # Test 5: Status query
        {
            "input": "灯开着吗？",
            "description": "Query device status"
        },
        # Test 6: Complex request
        {
            "input": "关掉所有的灯，然后打开空调",
            "description": "Multiple device operations"
        }
    ]
    
    session_id = "test_session"
    user_id = "test_user"
    
    print("\n" + "="*60)
    print("🧪 Testing Refactored Home AI System")
    print("="*60)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test['description']}")
        print(f"Input: {test['input']}")
        print("-" * 40)
        
        try:
            response = await system.process_user_input(
                user_input=test['input'],
                user_id=user_id,
                session_id=session_id
            )
            print(f"Response: {response}")
            
            # Small delay between tests
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print("✅ All tests completed")
    print("="*60)
    
    # Cleanup
    await system.cleanup()

if __name__ == "__main__":
    asyncio.run(test_system())