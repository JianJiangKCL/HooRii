#!/usr/bin/env python3
"""
Standalone ElevenLabs TTS Tool
Independent script for testing ElevenLabs text-to-speech with voice tags
"""
import os
import sys
import asyncio
import aiohttp
import base64
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class ElevenLabsTTS:
    """Standalone ElevenLabs TTS client"""
    
    def __init__(
        self,
        api_key: str,
        voice_id: str = "19STyYD15bswVz51nqLf",
        model: str = "eleven_turbo_v2_5",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True
    ):
        self.api_key = api_key
        self.voice_id = voice_id
        self.model = model
        self.base_url = "https://api.elevenlabs.io"
        
        # Voice settings for consistency
        self.voice_settings = {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
            "use_speaker_boost": use_speaker_boost
        }
    
    async def text_to_speech(
        self,
        text: str,
        output_format: str = "mp3_44100_128"
    ) -> Optional[bytes]:
        """
        Convert text to speech using ElevenLabs API
        
        Args:
            text: Text to convert (can include voice tags like [whispers], [sighs])
            output_format: Audio output format
            
        Returns:
            Audio bytes or None if failed
        """
        url = f"{self.base_url}/v1/text-to-speech/{self.voice_id}"
        
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        
        payload = {
            "text": text,
            "model_id": self.model
        }
        
        # Add voice_settings if provided
        if self.voice_settings:
            payload["voice_settings"] = self.voice_settings
        
        params = {
            "output_format": output_format
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        print(f"❌ API Error ({response.status}): {error_text}")
                        return None
                    
                    audio_bytes = await response.read()
                    if not audio_bytes:
                        print("❌ No audio data received")
                        return None
                    
                    return audio_bytes
                    
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None
    
    async def save_audio(
        self,
        text: str,
        output_path: str,
        output_format: str = "mp3_44100_128"
    ) -> bool:
        """
        Generate audio and save to file
        
        Args:
            text: Text to convert
            output_path: Path to save audio file
            output_format: Audio format
            
        Returns:
            True if successful
        """
        print(f"\n📝 Text: {text}")
        print(f"🎵 Generating audio...")
        
        audio_bytes = await self.text_to_speech(text, output_format)
        
        if not audio_bytes:
            print(f"❌ Failed to generate audio")
            return False
        
        try:
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            
            size_kb = len(audio_bytes) / 1024
            print(f"✅ Saved to: {output_path}")
            print(f"   Size: {size_kb:.1f} KB")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save file: {e}")
            return False


async def test_single_text(tts: ElevenLabsTTS, text: str, output_dir: str = "debug/tts_output"):
    """Test a single text sample"""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"test_{timestamp}.mp3")
    
    success = await tts.save_audio(text, output_file)
    return success


async def test_from_file(tts: ElevenLabsTTS, text_file: str, output_dir: str = "debug/tts_output"):
    """Test from a text file"""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        with open(text_file, 'r', encoding='utf-8') as f:
            text = f.read().strip()
        
        if not text:
            print(f"⚠️  File {text_file} is empty")
            return False
        
        # Generate output filename from input filename
        base_name = Path(text_file).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"{base_name}_{timestamp}.mp3")
        
        print(f"\n{'='*70}")
        print(f"📄 Processing: {text_file}")
        print(f"{'='*70}")
        
        success = await tts.save_audio(text, output_file)
        return success
        
    except Exception as e:
        print(f"❌ Error reading file {text_file}: {e}")
        return False


async def test_directory(tts: ElevenLabsTTS, text_dir: str, output_dir: str = "debug/tts_output"):
    """Test all text files in a directory"""
    text_dir_path = Path(text_dir)
    
    if not text_dir_path.exists():
        print(f"❌ Directory not found: {text_dir}")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all .txt files
    text_files = sorted(text_dir_path.glob("*.txt"))
    
    if not text_files:
        print(f"⚠️  No .txt files found in {text_dir}")
        return
    
    print(f"\n{'='*70}")
    print(f"🎭 Testing {len(text_files)} text files from {text_dir}")
    print(f"📁 Output directory: {output_dir}")
    print(f"{'='*70}")
    
    results = []
    for text_file in text_files:
        success = await test_from_file(tts, str(text_file), output_dir)
        results.append((text_file.name, success))
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"📊 Test Summary")
    print(f"{'='*70}")
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    for filename, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {filename}")
    
    print(f"\n✅ Success: {success_count}/{total_count}")
    print(f"📁 All files saved in: {output_dir}")
    print(f"{'='*70}")


def load_elevenlabs_config() -> Dict[str, Any]:
    """Load ElevenLabs configuration from config file"""
    config_file = Path("config/elevenlabs_config.json")
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                print(f"✓ Loaded config from: {config_file}")
                return config
        except Exception as e:
            print(f"⚠️  Failed to load {config_file}: {e}")
    
    # Fallback to .env
    print("⚠️  Config file not found, trying .env")
    api_key = os.getenv("ELEVENLABS_API_KEY")
    
    if not api_key:
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith("ELEVENLABS_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        break
    
    return {
        "api_key": api_key or "",
        "voice_id": os.getenv("ELEVENLABS_VOICE_ID", "rWArYo7a2NWuBYf5BE4V"),
        "model": os.getenv("ELEVENLABS_MODEL", "eleven_turbo_v2_5"),
        "output_format": os.getenv("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128"),
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }


def main():
    """Main entry point"""
    print("=" * 70)
    print("🎭 ElevenLabs TTS Standalone Tool")
    print("=" * 70)
    
    # Load configuration
    config = load_elevenlabs_config()
    
    api_key = config.get("api_key")
    if not api_key or api_key == "your_elevenlabs_api_key":
        print("❌ ELEVENLABS_API_KEY not found!")
        print("Set it in config/elevenlabs_config.json or .env")
        sys.exit(1)
    
    voice_id = config.get("voice_id", "rWArYo7a2NWuBYf5BE4V")
    model = config.get("model", "eleven_turbo_v2_5")
    voice_settings = config.get("voice_settings")
    
    print(f"\n✓ API Key: {'*' * 20}{api_key[-10:]}")
    print(f"✓ Voice ID: {voice_id}")
    print(f"✓ Model: {model}")
    if voice_settings:
        print(f"\n🎛️  Voice Settings:")
        print(f"   Stability: {voice_settings.get('stability', 0.5)}")
        print(f"   Similarity Boost: {voice_settings.get('similarity_boost', 0.75)}")
        print(f"   Style: {voice_settings.get('style', 0.0)}")
        print(f"   Speaker Boost: {voice_settings.get('use_speaker_boost', True)}")
    
    # Create TTS instance
    tts = ElevenLabsTTS(api_key, voice_id, model, voice_settings)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if os.path.isfile(arg):
            # Single file
            print(f"\n📄 Mode: Single file")
            output_dir = sys.argv[2] if len(sys.argv) > 2 else "debug/tts_output"
            asyncio.run(test_from_file(tts, arg, output_dir))
            
        elif os.path.isdir(arg):
            # Directory
            print(f"\n📁 Mode: Directory batch")
            output_dir = sys.argv[2] if len(sys.argv) > 2 else "debug/tts_output"
            asyncio.run(test_directory(tts, arg, output_dir))
            
        else:
            # Direct text
            print(f"\n📝 Mode: Direct text")
            output_dir = sys.argv[2] if len(sys.argv) > 2 else "debug/tts_output"
            asyncio.run(test_single_text(tts, arg, output_dir))
    else:
        # Interactive mode
        print("\n" + "=" * 70)
        print("Usage:")
        print("  1. Direct text:  python elevenlabs_tts_standalone.py 'Your text here' [output_dir]")
        print("  2. From file:    python elevenlabs_tts_standalone.py path/to/file.txt [output_dir]")
        print("  3. From dir:     python elevenlabs_tts_standalone.py path/to/dir [output_dir]")
        print("  4. Interactive:  python elevenlabs_tts_standalone.py")
        print()
        print("Default output directory: debug/tts_output/")
        print("=" * 70)
        
        print("\n🎬 Interactive Mode")
        print("Enter text (or 'q' to quit, 'batch' to process debug/voice_text/):\n")
        
        while True:
            try:
                text = input("Text: ").strip()
                
                if not text or text.lower() == 'q':
                    break
                
                if text.lower() == 'batch':
                    asyncio.run(test_directory(tts, "debug/voice_text", "debug/tts_output"))
                    continue
                
                asyncio.run(test_single_text(tts, text, "debug/tts_output"))
                
            except KeyboardInterrupt:
                print("\n\n👋 Bye!")
                break
            except EOFError:
                break
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()

