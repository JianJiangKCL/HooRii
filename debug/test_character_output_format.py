#!/usr/bin/env python3
"""
Test Character Output Format
Check the actual format returned by character system
"""
import asyncio
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from context_manager import SystemContext  
from character_system import CharacterSystem

async def test_character_output():
    """Test what format character system actually returns"""
    print("🧪 Character Output Format Test")
    print("=" * 50)
    
    try:
        config = Config()
        character_system = CharacterSystem(config)
        context = SystemContext()
        context.user_input = "你好"
        context.familiarity_score = 25
        context.conversation_tone = "formal"
        
        # Test normal response
        print("Testing normal character response...")
        response = await character_system.generate_response(context, None)
        
        print(f"\nResponse type: {type(response)}")
        print(f"Response content: {repr(response)}")
        print(f"Response (first 200 chars): {response[:200]}")
        
        # Try to parse as JSON to see if it's actually JSON
        try:
            parsed = json.loads(response)
            print(f"\n✅ Response is valid JSON:")
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
        except:
            print(f"\n✅ Response is plain text (not JSON)")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_character_output())