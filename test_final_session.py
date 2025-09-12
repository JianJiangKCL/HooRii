#!/usr/bin/env python3
"""
Final comprehensive test for Langfuse session tracking
"""
import asyncio
import uuid
from main import HomeAISystem

async def test_final_session():
    """Test session tracking with Langfuse"""
    system = HomeAISystem()
    
    # Unique session for this test
    session_id = f"final_test_{str(uuid.uuid4())[:8]}"
    user_id = f"user_{str(uuid.uuid4())[:8]}"
    
    print("🧪 Final Session Test - Langfuse Integration")
    print("=" * 50)
    print(f"Session: {session_id}")
    print(f"User: {user_id}")
    print("=" * 50)
    
    # Test interactions
    interactions = [
        "你好",  # Greeting
        "开灯",  # Device control
        "谢谢"   # Closing
    ]
    
    try:
        for i, user_input in enumerate(interactions, 1):
            print(f"\n💬 Turn {i}: {user_input}")
            print("-" * 30)
            
            response = await system.process_user_input(
                user_input=user_input,
                user_id=user_id,
                session_id=session_id
            )
            
            print(f"🤖 Response: {response[:100]}...")
            
            await asyncio.sleep(1)  # Brief pause between interactions
        
        print(f"\n✅ Session completed successfully!")
        print(f"🔗 Check your Langfuse dashboard for session: {session_id}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure proper cleanup and flush
        await system.cleanup()

if __name__ == "__main__":
    asyncio.run(test_final_session())