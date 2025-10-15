#!/usr/bin/env python3
"""
Setup script for ElevenLabs TTS configuration
Helps configure the .env file for Rei Ayanami voice
"""
import os
import sys
from pathlib import Path


def main():
    """Setup ElevenLabs TTS configuration"""
    print("=" * 60)
    print("🎭 ElevenLabs TTS Setup for Rei Ayanami")
    print("=" * 60)
    
    # Find .env file
    env_file = Path(".env")
    
    if not env_file.exists():
        print("\n❌ .env file not found!")
        print("Creating .env file with ElevenLabs configuration...")
        
        # Create basic .env with ElevenLabs config
        env_content = """# Smart Home AI Assistant Configuration

# LLM Provider
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp

# Database
DATABASE_URL=sqlite:///./hoorii.db

# System Settings
DEBUG=false
LOG_LEVEL=INFO
DEFAULT_FAMILIARITY_SCORE=25
MIN_FAMILIARITY_FOR_HARDWARE=40

# Text-to-Speech Provider
TTS_PROVIDER=elevenlabs
TTS_ENABLED=true

# ElevenLabs TTS (Rei Ayanami voice configuration)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=19STyYD15bswVz51nqLf
ELEVENLABS_MODEL=eleven_flash_v2_5
ELEVENLABS_OUTPUT_FORMAT=mp3_44100_128
ELEVENLABS_TTS_ENABLED=true
"""
        env_file.write_text(env_content)
        print("✅ Created .env file!")
        print("\n⚠️  Please edit .env and add your API keys:")
        print("   - GEMINI_API_KEY")
        print("   - ELEVENLABS_API_KEY")
        return
    
    # Read existing .env
    env_content = env_file.read_text()
    lines = env_content.split('\n')
    
    # Check and update configuration
    updates_needed = []
    
    # Check TTS_PROVIDER
    if 'TTS_PROVIDER=' not in env_content or 'TTS_PROVIDER=openai' in env_content:
        updates_needed.append("TTS_PROVIDER should be 'elevenlabs'")
    
    # Check ELEVENLABS_VOICE_ID
    if 'ELEVENLABS_VOICE_ID=19STyYD15bswVz51nqLf' not in env_content:
        updates_needed.append("ELEVENLABS_VOICE_ID should be '19STyYD15bswVz51nqLf'")
    
    # Check ELEVENLABS_MODEL
    if 'ELEVENLABS_MODEL=eleven_flash_v2_5' not in env_content:
        updates_needed.append("ELEVENLABS_MODEL should be 'eleven_flash_v2_5'")
    
    if updates_needed:
        print("\n⚠️  Configuration needs updates:")
        for update in updates_needed:
            print(f"   • {update}")
        
        print("\n📝 Updating .env file...")
        
        # Update configuration
        new_lines = []
        for line in lines:
            if line.startswith('TTS_PROVIDER='):
                new_lines.append('TTS_PROVIDER=elevenlabs')
            elif line.startswith('ELEVENLABS_VOICE_ID='):
                new_lines.append('ELEVENLABS_VOICE_ID=19STyYD15bswVz51nqLf')
            elif line.startswith('ELEVENLABS_MODEL='):
                new_lines.append('ELEVENLABS_MODEL=eleven_flash_v2_5')
            elif line.startswith('ELEVENLABS_TTS_ENABLED='):
                new_lines.append('ELEVENLABS_TTS_ENABLED=true')
            elif line.startswith('TTS_ENABLED='):
                new_lines.append('TTS_ENABLED=true')
            else:
                new_lines.append(line)
        
        # Add missing lines if needed
        if 'ELEVENLABS_VOICE_ID=' not in env_content:
            new_lines.append('')
            new_lines.append('# ElevenLabs TTS Configuration')
            new_lines.append('ELEVENLABS_VOICE_ID=19STyYD15bswVz51nqLf')
            new_lines.append('ELEVENLABS_MODEL=eleven_flash_v2_5')
            new_lines.append('ELEVENLABS_OUTPUT_FORMAT=mp3_44100_128')
            new_lines.append('ELEVENLABS_TTS_ENABLED=true')
        
        # Backup original
        backup_file = env_file.with_suffix('.env.backup')
        backup_file.write_text(env_content)
        print(f"   📋 Backup created: {backup_file}")
        
        # Write updated config
        env_file.write_text('\n'.join(new_lines))
        print("   ✅ Configuration updated!")
    else:
        print("\n✅ Configuration is already correct!")
    
    # Display current configuration
    print("\n" + "=" * 60)
    print("Current ElevenLabs Configuration:")
    print("=" * 60)
    
    for line in env_file.read_text().split('\n'):
        if any(key in line for key in ['TTS_', 'ELEVENLABS_']):
            # Hide API keys
            if 'API_KEY=' in line and '=' in line:
                key, value = line.split('=', 1)
                if value and value != 'your_elevenlabs_api_key_here':
                    print(f"{key}=***hidden***")
                else:
                    print(line)
            else:
                print(line)
    
    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("\n💡 Next steps:")
    print("   1. Make sure ELEVENLABS_API_KEY is set in .env")
    print("   2. Run: python debug/test_tts_with_markers.py")
    print("   3. Test the full system with the new voice")
    print("=" * 60)


if __name__ == "__main__":
    main()


