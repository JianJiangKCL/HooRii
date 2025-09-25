#!/usr/bin/env python3
"""
Main entry point for Hoorii Smart Home AI Assistant
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config import load_config
from src.workflows import create_ai_system


async def main():
    """Main application entry point"""
    print("🏠 Starting Hoorii Smart Home AI Assistant...")

    # Load configuration
    config = load_config()

    # Create AI system (will use LangGraph if available)
    system = await create_ai_system(config, use_langgraph=True)

    print("\n🤖 System ready! Type 'exit' to quit.\n")

    # Start interactive session
    session_id = None
    user_id = "default_user"

    try:
        while True:
            user_input = input("\n👤 You: ").strip()

            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye!")
                break

            if not user_input:
                continue

            # Process the message
            if hasattr(system, 'process_message'):
                # LangGraph system
                response = await system.process_message(
                    user_input=user_input,
                    user_id=user_id,
                    session_id=session_id
                )

                if isinstance(response, dict):
                    print(f"\n🤖 Assistant: {response.get('response', 'No response')}")
                else:
                    print(f"\n🤖 Assistant: {response}")
            else:
                # Traditional system
                response = await system.process_user_input(
                    user_input,
                    user_id=user_id,
                    session_id=session_id
                )
                print(f"\n🤖 Assistant: {response}")

    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if hasattr(system, 'cleanup'):
            await system.cleanup()


if __name__ == "__main__":
    asyncio.run(main())