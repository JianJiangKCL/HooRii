# ElevenLabs TTS Testing Suite ✅

## 🎉 Complete Setup

All files created and ready for testing!

## 📦 What You Got

### 1. Standalone TTS Tool
**`debug/elevenlabs_tts_standalone.py`** (9 KB)
- Independent ElevenLabs TTS client
- No project dependencies (except aiohttp)
- Batch and single file processing
- Direct API integration

### 2. Test Text Files (20 files)
**`debug/voice_text/*.txt`**

| # | File | Content Preview | Tags |
|---|------|-----------------|------|
| 01 | greeting | `...Hello.` | ... |
| 02 | low_familiarity_rejection | `...Why should I follow your orders?` | ... |
| 03 | simple_refusal | `...No. I cannot do that for you.` | ... |
| 04 | questioning | `...Why? ...Why would you worry?` | ... |
| 05 | confusion | `Feelings...? I don't quite understand.` | ... |
| 06 | with_sigh | `[sighs] ...Thank you.` | ..., [sighs] |
| 07 | acceptance | `...I understand. If it's you...` | ... |
| 08 | simple_confirmation | `...I see. ...Done.` | ... |
| 09 | whisper_intimate | `[whispers] When I'm with you...` | [whispers], ... |
| 10 | protection | `No. I'll protect you.` | ... |
| 11 | self_doubt | `I am... replaceable.` | ... |
| 12 | rare_emotion | `You... [sighs] ...I don't understand.` | ..., [sighs] |
| 13 | mixed_tags | `[sighs] but... [whispers] I'm glad` | ..., [sighs], [whispers] |
| 14 | device_control_accept | `...I will turn on the lights.` | ... |
| 15 | device_control_refuse | `...I refuse. This is not...` | ... |
| 16 | exhale_completion | `[exhales] ...It's done.` | [exhales], ... |
| 17 | quiet_gratitude | `I... [whispers] thank you.` | [whispers], ... |
| 18 | reluctant_help | `[sighs] ...Fine. I will help you.` | [sighs], ... |
| 19 | identity_question | `Who am I...? I'm just... a doll.` | ... |
| 20 | bond_realization | `[whispers] I feel... different.` | [whispers], ... |

### 3. Helper Scripts
- **`debug/run_batch_test.sh`** - Bash script for batch testing
- Creates timestamped output directory
- Processes all files at once

### 4. Documentation (5 files)
- **`debug/voice_text/README.md`** - Voice text overview
- **`debug/voice_text/test_samples_list.md`** - Full text details
- **`debug/HOW_TO_USE_TTS_TOOL.md`** - Tool usage guide
- **`debug/BATCH_TEST_GUIDE.md`** - Batch processing guide
- **`debug/TEST_ALL_VOICES.md`** - Quick reference

## 🚀 Usage Examples

### Test One File

```bash
cd /data/jj/proj/hoorii
python debug/elevenlabs_tts_standalone.py debug/voice_text/01_greeting.txt
```

**Output**:
```
✓ API Key: ********************7bbffd349d
✓ Voice ID: 19STyYD15bswVz51nqLf
✓ Model: eleven_flash_v2_5

📝 Text: ...Hello.
🎵 Generating audio...
✅ Saved to: ./01_greeting_20251014_013150.mp3
   Size: 17.2 KB
```

### Test All Files

```bash
python debug/elevenlabs_tts_standalone.py debug/voice_text
```

**Output**: Processes all 20 files with summary

### Test Custom Text

```bash
python debug/elevenlabs_tts_standalone.py "...I don't understand. But... [whispers] thank you."
```

## 🎯 Voice Tags Reference

### Supported Tags (from ElevenLabs docs)

**Vocal Delivery**:
- `[whispers]` - Soft, intimate speech
- `[sighs]` - Sighing sound
- `[exhales]` - Exhaling sound

**Reactions**:
- `[laughs]` - Laughing (not used for Rei)
- `[starts laughing]` - Begins laughing (not used)

**Emotional**:
- `[curious]` - Curious tone
- `[sarcastic]` - Sarcastic (not Rei's style)
- `[excited]` - Excited (not Rei's style)

**Natural**:
- `...` - Ellipsis for natural pause (kept as-is)

### Used in Test Files

✅ `...` - All 20 files  
✅ `[sighs]` - Files 06, 12, 13, 18  
✅ `[whispers]` - Files 09, 13, 17, 20  
✅ `[exhales]` - File 16

## 📊 Test Scenarios Coverage

| Scenario | Files | Purpose |
|----------|-------|---------|
| **Basic interaction** | 01-04 | Test natural pauses |
| **Emotional response** | 05-08 | Test feelings/confusion |
| **Intimate moments** | 09-13 | Test [whispers] tag |
| **Device control** | 14-15 | Test functional responses |
| **Complex emotions** | 16-20 | Test mixed tags |

## 🎭 Character Consistency

All texts maintain:
- ✓ Short sentences
- ✓ Minimal emotion
- ✓ Frequent pauses (...)
- ✓ Rare voice tags (only when needed)
- ✓ Gradual emotional development
- ✓ Rei Ayanami's personality

## 💻 Code Structure

### Standalone Tool Features

```python
class ElevenLabsTTS:
    def __init__(api_key, voice_id, model)
    async def text_to_speech(text) -> bytes
    async def save_audio(text, output_path) -> bool

# Main functions
async def test_single_text(tts, text)
async def test_from_file(tts, file_path)
async def test_directory(tts, directory)
```

### No Dependencies on Main Project

The tool is completely standalone:
- Only needs: `aiohttp`, `asyncio`
- Reads `.env` for config
- Can be used independently

## 🧪 Testing Workflow

### Step 1: Verify Setup

```bash
# Check files exist
ls debug/voice_text/*.txt

# Should show 20 .txt files
```

### Step 2: Test One Sample

```bash
# Test greeting (simplest)
python debug/elevenlabs_tts_standalone.py debug/voice_text/01_greeting.txt

# Listen to verify quality
```

### Step 3: Test Voice Tags

```bash
# Test whisper
python debug/elevenlabs_tts_standalone.py debug/voice_text/09_whisper_intimate.txt

# Test sigh
python debug/elevenlabs_tts_standalone.py debug/voice_text/06_with_sigh.txt

# Test mixed tags
python debug/elevenlabs_tts_standalone.py debug/voice_text/13_mixed_tags.txt
```

### Step 4: Batch Process (if quota permits)

```bash
# Process all 20 files
python debug/elevenlabs_tts_standalone.py debug/voice_text

# Or use shell script
./debug/run_batch_test.sh
```

## 📈 Success Metrics

After testing, verify:
- [ ] All files generate audio
- [ ] Natural pauses (`...`) sound smooth
- [ ] `[whispers]` creates soft voice
- [ ] `[sighs]` creates sighing sound
- [ ] `[exhales]` creates exhaling sound
- [ ] Voice is calm and monotone
- [ ] Character feels like Rei Ayanami

## ⚠️ Important Notes

1. **API Quota**: Watch your usage - 20 files will use credits
2. **Rate Limits**: Don't spam requests
3. **File Output**: Defaults to current directory
4. **Quality**: Model `eleven_flash_v2_5` balances speed/quality

## 🎵 Audio Quality Settings

Current config (in tool):
- **Voice**: `19STyYD15bswVz51nqLf`
- **Model**: `eleven_flash_v2_5` (fast, low latency)
- **Format**: `mp3_44100_128` (44.1kHz, 128kbps)

To change, edit the script or pass parameters.

## 🔗 Integration

After testing, the same voice tags work in main system:
- Character responses use `...` and tags
- Auto-formatted by `src/utils/text_formatting.py`
- Sent to ElevenLabs via `src/services/agora_tts_service.py`

## 📚 Documentation

- **This file** - Complete testing guide
- **HOW_TO_USE_TTS_TOOL.md** - Tool usage
- **BATCH_TEST_GUIDE.md** - Batch processing
- **voice_text/README.md** - Test files overview
- **voice_text/test_samples_list.md** - All texts with details

---

## ✅ Quick Start Summary

```bash
# Single file test
python debug/elevenlabs_tts_standalone.py debug/voice_text/01_greeting.txt

# Batch test all files
python debug/elevenlabs_tts_standalone.py debug/voice_text

# Custom text
python debug/elevenlabs_tts_standalone.py "...Your text here"
```

**Status**: ✅ Ready to test  
**Files**: 20 texts + tool + docs  
**Next**: Run tests when API quota available


