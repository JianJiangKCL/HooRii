# Quick Start - ElevenLabs TTS Testing

## ⚡ One-Line Commands

### Test One File
```bash
python debug/elevenlabs_tts_standalone.py debug/voice_text/01_greeting.txt
```
→ Output: `debug/tts_output/01_greeting_TIMESTAMP.mp3`

### Test All 20 Files
```bash
python debug/elevenlabs_tts_standalone.py debug/voice_text
```
→ Output: `debug/tts_output/*.mp3` (20 files)

### Test Custom Text
```bash
python debug/elevenlabs_tts_standalone.py "...Hello there"
```
→ Output: `debug/tts_output/test_TIMESTAMP.mp3`

## 📁 Structure

```
debug/
├── elevenlabs_tts_standalone.py  ← Tool
├── voice_text/                   ← Input (20 .txt files)
└── tts_output/                   ← Output (all .mp3 files)
```

## ✅ Tested

Single file test passed:
```
✅ Saved to: debug/tts_output/01_greeting_20251014_032104.mp3
   Size: 16.0 KB
```

## 🎯 Next

Run batch test when API quota available:
```bash
python debug/elevenlabs_tts_standalone.py debug/voice_text
```

---

**See**: `debug/USAGE_GUIDE.md` for full documentation
