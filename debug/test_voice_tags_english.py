#!/usr/bin/env python3
"""
Test ElevenLabs Voice Tags with English text
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.text_formatting import format_for_elevenlabs


def main():
    """Test Voice Tags formatting with English examples"""
    print("=" * 70)
    print("🎭 ElevenLabs Voice Tags Test (English)")
    print("=" * 70)
    print("\nSupported Voice Tags:")
    print("  [whispers] - soft/intimate speech")
    print("  [sighs] - sighing")
    print("  [exhales] - exhaling")
    print("  [curious] - curious tone")
    print("  ... (ellipsis) - natural pause (kept as-is)")
    print("=" * 70)
    
    test_cases = [
        {
            "name": "Low familiarity rejection",
            "original": "...Why should I follow your orders? We... are not familiar.",
        },
        {
            "name": "Simple greeting",
            "original": "...Hello.",
        },
        {
            "name": "Confusion",
            "original": "Feelings...? I don't quite understand. But... now, I don't dislike it.",
        },
        {
            "name": "With sigh",
            "original": "...For me? Why? [sighs] ...Thank you.",
        },
        {
            "name": "With whisper tag",
            "original": "(whisper) When I'm with you... here... there's a strange feeling.",
        },
        {
            "name": "Wrapped whisper",
            "original": "I don't understand... but (whisper: this feels different).",
        },
        {
            "name": "Example from docs",
            "original": "[whispers] I never knew it could be this way, but I'm glad we're here.",
        },
        {
            "name": "Natural pauses only",
            "original": "...I see. ...If it's you... I can try.",
        },
        {
            "name": "Exhale example",
            "original": "[exhales] ...I don't know what to say.",
        },
    ]
    
    for i, case in enumerate(test_cases, 1):
        formatted = format_for_elevenlabs(case["original"])
        
        print(f"\n[{i}] {case['name']}")
        print(f"Original:  {case['original']}")
        print(f"Formatted: {formatted}")
        print(f"Changed:   {'Yes' if formatted != case['original'] else 'No'}")
        print("-" * 70)
    
    print("\n" + "=" * 70)
    print("✅ Formatting test completed!")
    print("\n💡 Key points:")
    print("   - Keep '...' as-is (ElevenLabs understands natural pauses)")
    print("   - (whisper) → [whispers]")
    print("   - [sighs], [exhales] kept as-is")
    print("   - Tags are lowercase in square brackets")
    print("\n🎵 These tags will be sent directly to ElevenLabs API")
    print("=" * 70)


if __name__ == "__main__":
    main()


