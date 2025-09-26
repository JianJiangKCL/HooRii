#!/usr/bin/env python3
"""
Test Clean Interaction
Test the application with multiple interactions to verify clean output
"""
import asyncio
import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.workflows.traditional_workflow import HomeAISystem

async def test_clean_interactions():
    """Test multiple interactions with clean output"""
    print("🧪 Clean Interaction Test")
    print("=" * 50)
    
    # Set logging to WARNING to reduce output
    logging.getLogger().setLevel(logging.WARNING)
    
    try:
        system = HomeAISystem()
        session_id = "test_session_123"
        user_id = "test_user"
        
        test_inputs = [
            "你好",
            "你叫什么名字",
            "帮我开空调",
            "把灯关掉"
        ]
        
        for i, user_input in enumerate(test_inputs, 1):
            print(f"\n{i}. 你: {user_input}")
            
            response = await system.process_user_input(
                user_input=user_input,
                user_id=user_id, 
                session_id=session_id
            )
            
            print(f"   凌波丽: {response}")
        
        print("\n✅ Clean interaction test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_clean_interactions())