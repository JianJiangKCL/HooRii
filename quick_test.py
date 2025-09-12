#!/usr/bin/env python3
"""
Quick test for the updated system
"""
import asyncio
from main import HomeAISystem

async def quick_test():
    """Quick test of the system"""
    system = HomeAISystem()
    
    # Test one interaction
    response = await system.process_user_input(
        user_input="你好",
        user_id="test_user",
        session_id="test_session"
    )
    
    print(f"Response: {response}")

if __name__ == "__main__":
    asyncio.run(quick_test())