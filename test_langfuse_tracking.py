#!/usr/bin/env python3
"""
Test script for Langfuse session and user tracking
"""
import asyncio
import logging
from main import HomeAISystem

logging.basicConfig(level=logging.INFO)

async def test_langfuse_tracking():
    """Test Langfuse session and user tracking"""
    system = HomeAISystem()
    
    # Simulate a conversation session
    session_id = "test_session_langfuse"
    user_id = "test_user_langfuse"
    
    print("\n" + "="*60)
    print("🔍 Testing Langfuse Session and User Tracking")
    print("="*60)
    print(f"Session ID: {session_id}")
    print(f"User ID: {user_id}")
    
    conversation_flow = [
        "你好，我是新用户",
        "开灯",
        "把它调亮一点",
        "空调的状态怎么样？",
        "好热啊，帮我开空调",
        "谢谢你"
    ]
    
    try:
        for i, user_input in enumerate(conversation_flow, 1):
            print(f"\n📝 Turn {i}: {user_input}")
            print("-" * 40)
            
            response = await system.process_user_input(
                user_input=user_input,
                user_id=user_id,
                session_id=session_id
            )
            
            print(f"Response: {response}")
            
            # Small delay between messages
            await asyncio.sleep(0.5)
        
        print("\n" + "="*60)
        print("✅ Session completed successfully")
        print("🔍 Check your Langfuse dashboard for session tracking:")
        print(f"   - Session ID: {session_id}")
        print(f"   - User ID: {user_id}")
        print(f"   - Total messages: {len(conversation_flow)}")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error during conversation: {e}")
    
    finally:
        # Cleanup and flush Langfuse
        await system.cleanup()
        print("\n🧹 Cleanup completed")

if __name__ == "__main__":
    asyncio.run(test_langfuse_tracking())