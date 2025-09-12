#!/usr/bin/env python3
"""
Complete test for Langfuse session tracking
"""
import asyncio
import uuid
import logging
from main import HomeAISystem

logging.basicConfig(level=logging.INFO)

async def test_complete_session():
    """Test a complete conversation session"""
    system = HomeAISystem()
    
    # Generate unique IDs to avoid database conflicts
    session_id = f"session_{str(uuid.uuid4())[:8]}"
    user_id = f"user_{str(uuid.uuid4())[:8]}"
    
    print("\n" + "="*60)
    print("🧪 Complete Langfuse Session Test")
    print("="*60)
    print(f"Session ID: {session_id}")
    print(f"User ID: {user_id}")
    print("="*60)
    
    # Conversation flow
    interactions = [
        {"input": "你好", "description": "Initial greeting"},
        {"input": "开灯", "description": "Device control request"},  
        {"input": "把它调亮一点", "description": "Context-dependent adjustment"},
        {"input": "现在灯的状态怎么样？", "description": "Status query"},
        {"input": "谢谢你", "description": "Closing pleasantries"}
    ]
    
    try:
        for i, interaction in enumerate(interactions, 1):
            print(f"\n📝 Turn {i}: {interaction['description']}")
            print(f"Input: {interaction['input']}")
            print("-" * 40)
            
            response = await system.process_user_input(
                user_input=interaction['input'],
                user_id=user_id,
                session_id=session_id
            )
            
            print(f"Response: {response}")
            
            # Small delay between interactions
            await asyncio.sleep(0.5)
        
        print("\n" + "="*60) 
        print("✅ Session completed successfully!")
        print("🔍 Check Langfuse Dashboard:")
        print(f"   • Session: {session_id}")
        print(f"   • User: {user_id}")
        print(f"   • Interactions: {len(interactions)}")
        print("   • Should see grouped traces with session_id")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Session test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Proper cleanup
        await system.cleanup()
        print("\n🧹 Session cleanup completed")

if __name__ == "__main__":
    asyncio.run(test_complete_session())