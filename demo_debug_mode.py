#!/usr/bin/env python3
"""
Demo script to show debug mode functionality
"""
import asyncio
import logging
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import HomeAISystem

async def demo_debug_mode():
    """Demo both normal and debug modes"""
    print("🎬 Demo: Debug Mode Functionality")
    print("=" * 50)
    
    # Demo 1: Normal mode (WARNING level)
    print("\n📱 Normal Mode (Clean Output):")
    print("-" * 30)
    logging.getLogger().setLevel(logging.WARNING)
    
    system = HomeAISystem()
    response = await system.process_user_input(
        user_input="你好",
        user_id="demo_user",
        session_id="demo_session_1"
    )
    print(f"凌波丽: {response}")
    
    print("\n" + "=" * 50)
    
    # Demo 2: Debug mode (DEBUG level)
    print("\n🐛 Debug Mode (Detailed Logs):")
    print("-" * 30)
    logging.getLogger().setLevel(logging.DEBUG)
    
    response = await system.process_user_input(
        user_input="帮我开灯",
        user_id="demo_user",
        session_id="demo_session_2"
    )
    print(f"凌波丽: {response}")
    
    print("\n" + "=" * 50)
    print("📋 Usage:")
    print("  python main.py           # Clean output")
    print("  python main.py --debug   # Detailed logs")

if __name__ == "__main__":
    asyncio.run(demo_debug_mode())