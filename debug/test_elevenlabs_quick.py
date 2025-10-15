#!/usr/bin/env python3
"""
Quick ElevenLabs TTS Test (no interactive prompts)
"""
import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable OpenTelemetry for tests
os.environ['OTEL_TRACES_EXPORTER'] = 'none'
os.environ['OTEL_METRICS_EXPORTER'] = 'none'
os.environ['OTEL_LOGS_EXPORTER'] = 'none'

from src.utils.text_formatting import format_for_elevenlabs
from src.utils.config import load_config
from src.services.agora_tts_service import AgoraTTSService


async def main():
    """Quick test"""
    print("🎭 Testing ElevenLabs TTS with Natural Pauses")
    print("=" * 60)
    
    # Test formatting
    original = "...为什么要听从你的指令？我们...并不熟悉。"
    formatted = format_for_elevenlabs(original)
    print(f"Original:  {original}")
    print(f"Formatted: {formatted}")
    print(f"Changed:   {'Yes' if formatted != original else 'No'}\n")
    
    # Test TTS
    try:
        config = load_config()
        tts = AgoraTTSService(config)
        
        print(f"Provider: {tts.provider}")
        print(f"Voice ID: {tts.default_voice}")
        print(f"Model:    {tts.model}")
        print(f"Enabled:  {tts.enabled}\n")
        
        if not tts.enabled:
            print("❌ TTS disabled!")
            return
        
        print("Generating audio...")
        audio_base64 = await tts.text_to_speech(original)
        
        if audio_base64:
            import base64
            from datetime import datetime
            audio_bytes = base64.b64decode(audio_base64)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_rei_{timestamp}.mp3"
            with open(filename, "wb") as f:
                f.write(audio_bytes)
            
            print(f"✅ Success! Saved to: {filename}")
            print(f"   Size: {len(audio_bytes)} bytes")
            print("\n🎧 Play the file to hear the natural pauses!")
        else:
            print("❌ Failed to generate audio")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())


