#!/usr/bin/env python3
"""
Test Performance Optimizations
Test the speed and efficiency improvements
"""
import asyncio
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import HomeAISystem

async def test_response_speed():
    """Test response speed with optimizations"""
    print("🚀 Performance Optimization Test")
    print("=" * 50)
    
    system = HomeAISystem()
    session_id = "perf_test_session"
    user_id = "perf_test_user"
    
    test_cases = [
        "你好",
        "帮我开灯", 
        "你叫什么名字",
        "刚才那个灯怎么样了"  # Test context reference
    ]
    
    total_start_time = time.time()
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{test_input}'")
        start_time = time.time()
        
        response = await system.process_user_input(
            user_input=test_input,
            user_id=user_id,
            session_id=session_id
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"   Response: {response[:50]}...")
        print(f"   ⏱️  Time: {response_time:.2f}s")
        
        # Small delay to let background tasks complete
        await asyncio.sleep(0.5)
    
    total_time = time.time() - total_start_time
    avg_time = total_time / len(test_cases)
    
    print(f"\n📊 Performance Summary:")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average per response: {avg_time:.2f}s")
    print(f"   Optimizations applied:")
    print(f"     ✅ Claude API prompt caching")
    print(f"     ✅ Async context saving")
    print(f"     ✅ Background database operations")
    print(f"     ✅ Non-blocking post-response tasks")
    
    return avg_time < 3.0  # Target: under 3 seconds per response

if __name__ == "__main__":
    async def main():
        success = await test_response_speed()
        if success:
            print(f"\n🎉 Performance test PASSED!")
        else:
            print(f"\n⚠️  Performance could be improved")
    
    asyncio.run(main())