#!/usr/bin/env python3
"""
Profile Performance Bottlenecks
Identify where time is being spent in the pipeline
"""
import asyncio
import time
import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import HomeAISystem

class PerformanceProfiler:
    def __init__(self):
        self.timings = {}
    
    def start_timer(self, name: str):
        self.timings[name] = {"start": time.time()}
    
    def end_timer(self, name: str):
        if name in self.timings:
            self.timings[name]["duration"] = time.time() - self.timings[name]["start"]
    
    def report(self):
        print("\n⏱️  Performance Profile:")
        print("-" * 40)
        total_time = 0
        for name, timing in sorted(self.timings.items(), key=lambda x: x[1].get("duration", 0), reverse=True):
            duration = timing.get("duration", 0)
            total_time += duration
            print(f"  {name:<25} {duration:>6.2f}s")
        print("-" * 40)
        print(f"  {'TOTAL':<25} {total_time:>6.2f}s")

async def profile_single_request():
    """Profile a single request to find bottlenecks"""
    print("🔍 Profiling Single Request")
    print("=" * 50)
    
    # Reduce logging noise
    logging.getLogger().setLevel(logging.ERROR)
    
    profiler = PerformanceProfiler()
    
    profiler.start_timer("System Initialization")
    system = HomeAISystem()
    profiler.end_timer("System Initialization")
    
    session_id = "profile_session"
    user_id = "profile_user"
    test_input = "你好"
    
    print(f"Input: '{test_input}'")
    
    # Profile the main processing
    profiler.start_timer("Total Processing")
    
    # Use the full processing pipeline
    response = await system.process_user_input(
        user_input=test_input,
        user_id=user_id,
        session_id=session_id
    )
    
    profiler.end_timer("Total Processing")
    
    print(f"Response: {response}")
    
    profiler.report()
    
    # Identify the slowest component
    slowest = max(profiler.timings.items(), key=lambda x: x[1].get("duration", 0))
    print(f"\n🐌 Slowest component: {slowest[0]} ({slowest[1]['duration']:.2f}s)")
    
    return profiler.timings

if __name__ == "__main__":
    asyncio.run(profile_single_request())