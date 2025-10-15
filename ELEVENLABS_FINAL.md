# ✅ ElevenLabs TTS - Final Configuration

## 🎯 Applied to Main Workflow

**Voice**: `19STyYD15bswVz51nqLf` (Rei Ayanami)  
**Model**: `eleven_turbo_v2_5` (Fastest)  
**Status**: ✅ INTEGRATED & TESTED

## ⚡ Quick Commands

### Run Main System
```bash
python src/main.py
```

### Run API Server
```bash
python scripts/start_api_server.py
```

### Test TTS Only
```bash
python debug/elevenlabs_tts_standalone.py debug/voice_text/01_greeting.txt
```

## 📊 Configuration Summary

```env
TTS_PROVIDER=elevenlabs
ELEVENLABS_VOICE_ID=19STyYD15bswVz51nqLf
ELEVENLABS_MODEL=eleven_turbo_v2_5
ELEVENLABS_API_KEY=92b7a...349d ✅
```

## 🎭 Voice Tags

- `...` → Natural pause (kept as-is)
- `(whisper)` → `[whispers]`
- `[sighs]` → Kept as-is
- `[exhales]` → Kept as-is

## ✅ Tested

- [x] Main workflow: ✅ (85 KB audio generated)
- [x] Standalone tool: ✅ (working)
- [x] Voice tags: ✅ (converting correctly)
- [x] Character prompt: ✅ (English with tags)

## 📁 Output Directory

All audio saves to: **`debug/tts_output/`** ✅

---

**Everything is ready! Just run `python src/main.py`** 🎉
