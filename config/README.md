# Configuration Directory

## ElevenLabs TTS Configuration

### File: `elevenlabs_config.json`

This file contains all ElevenLabs TTS settings, loaded by both:
- Main workflow (`src/utils/config.py`)
- Standalone TTS tool (`debug/elevenlabs_tts_standalone.py`)

### Current Configuration

```json
{
  "api_key": "92b7a...349d",
  "voice_id": "rWArYo7a2NWuBYf5BE4V",
  "model": "eleven_turbo_v2_5",
  "output_format": "mp3_44100_128",
  "enabled": true
}
```

### Parameters

- **api_key**: Your ElevenLabs API key
- **voice_id**: Voice ID (currently: Rei Ayanami voice)
- **model**: TTS model
  - `eleven_turbo_v2_5` - Fastest, lowest latency (current)
  - `eleven_flash_v2_5` - Balanced
  - `eleven_multilingual_v2` - Highest quality
- **output_format**: Audio format
  - `mp3_44100_128` - High quality MP3 (current)
  - `mp3_22050_32` - Lower quality, faster
  - `pcm_44100` - Uncompressed
- **enabled**: Enable/disable TTS
- **voice_settings**: Voice parameters (optional, set to null for defaults)
- **optimize_streaming_latency**: 0-4, higher = faster but lower quality

### Usage

The configuration is automatically loaded when:
1. Running main system: `python src/main.py`
2. Starting API server: `python scripts/start_api_server.py`
3. Using standalone tool: `python debug/elevenlabs_tts_standalone.py`

### Priority

1. `config/elevenlabs_config.json` (highest priority)
2. Environment variables in `.env` (fallback)
3. Hard-coded defaults (last resort)

### Editing

Simply edit `config/elevenlabs_config.json` and restart the application.

**No need to modify `.env` for ElevenLabs settings** - use this config file instead!

---

**Note**: Keep API key secure, don't commit to public repos

