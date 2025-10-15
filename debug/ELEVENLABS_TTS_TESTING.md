# ElevenLabs TTS Testing - Complete Guide 🎭

## ✅ What's Been Created

### 1. Standalone TTS Tool
**File**: `debug/elevenlabs_tts_standalone.py`
- Independent Python script
- No dependencies on main project
- Direct ElevenLabs API calls
- Supports batch processing

### 2. Test Texts (20 files)
**Directory**: `debug/voice_text/`
- 20 carefully crafted test scenarios
- Covers all Rei Ayanami character moods
- Includes voice tags: [whispers], [sighs], [exhales]
- Natural pauses with `...`

### 3. Documentation
- `debug/voice_text/README.md` - Test files overview
- `debug/voice_text/test_samples_list.md` - Full text list
- `debug/HOW_TO_USE_TTS_TOOL.md` - Usage guide
- `debug/BATCH_TEST_GUIDE.md` - Batch testing guide
- `debug/TEST_ALL_VOICES.md` - Quick reference

## 🚀 How to Use

### Option 1: Test All Files (Batch)

```bash
cd /data/jj/proj/hoorii
python debug/elevenlabs_tts_standalone.py debug/voice_text
```

**Output**: 20 MP3 files with names like:
```
01_greeting_20251014_013045.mp3
02_low_familiarity_rejection_20251014_013046.mp3
...
20_bond_realization_20251014_013104.mp3
```

### Option 2: Test Single File

```bash
python debug/elevenlabs_tts_standalone.py debug/voice_text/09_whisper_intimate.txt
```

**Output**: `09_whisper_intimate_20251014_013045.mp3`

### Option 3: Test Custom Text

```bash
python debug/elevenlabs_tts_standalone.py "...Hello. How are you?"
```

**Output**: `test_20251014_013045.mp3`

### Option 4: Interactive Mode

```bash
python debug/elevenlabs_tts_standalone.py
```

Then:
- Enter text manually
- Type `batch` to process all voice_text files
- Type `q` to quit

## 📋 Test Files Breakdown

### Basic (Files 01-04)
Simple greetings, refusals, questions
- Focus on natural pauses
- No special voice tags

### Emotional (Files 05-08)
Confusion, gratitude, acceptance
- Some with [sighs]
- Natural pauses

### Intimate (Files 09-13)
Whispered moments, rare emotions
- Heavy use of [whispers]
- Mixed tags in file 13

### Functional (Files 14-15)
Device control scenarios
- Acceptance and refusal
- Natural pauses only

### Special (Files 16-20)
Complex emotions, mixed tags
- [exhales], [whispers], [sighs]
- Most emotionally complex

## 🎯 Voice Tags Used

| Tag | Usage | Files |
|-----|-------|-------|
| `...` | Natural pause | All 20 files |
| `[sighs]` | Sighing | 06, 12, 13, 18 |
| `[whispers]` | Whispering | 09, 13, 17, 20 |
| `[exhales]` | Exhaling | 16 |

## 💡 Testing Tips

### Start Small
Test 1-2 files first to verify quality:
```bash
python debug/elevenlabs_tts_standalone.py debug/voice_text/01_greeting.txt
```

### Compare Tags
Listen to differences:
- File 01 (no tags): Pure natural pauses
- File 06 ([sighs]): With sighing
- File 09 ([whispers]): Whispered speech
- File 13 (mixed): Both [sighs] and [whispers]

### Check Quality
- Natural pauses should sound smooth
- [whispers] should be noticeably softer
- [sighs] should have actual sighing sound
- Overall voice should be calm, monotone

## 📊 Expected Results

### File Sizes
- Short texts (01-04): ~17-30 KB
- Medium texts (05-08): ~30-45 KB
- Long texts (09-13): ~45-65 KB
- Complex (16-20): ~40-60 KB

### Processing Time
- Per file: ~2-3 seconds
- All 20 files: ~40-60 seconds total

### API Cost
- Model `eleven_flash_v2_5` is the fastest/cheapest
- Each character costs credits
- Total for 20 files: Check your quota

## 🎭 Character Verification

Listen for Rei Ayanami's traits:
- ✓ Calm, flat tone
- ✓ Natural pauses showing hesitation
- ✓ Rare emotional expression
- ✓ Whispers in intimate moments
- ✓ Sighs for complex emotions
- ✓ Overall detached but gradually warming

## 🔧 Troubleshooting

### Script doesn't run
```bash
# Check Python version
python --version  # Should be 3.7+

# Install aiohttp if needed
pip install aiohttp
```

### API errors
- Check `.env` has correct `ELEVENLABS_API_KEY`
- Verify Voice ID: `19STyYD15bswVz51nqLf`
- Check API quota

### No audio generated
- Check network connection
- Verify API key is valid
- Check quota hasn't exceeded

## 📈 Success Criteria

After batch testing, you should have:
- ✅ 20 MP3 files generated
- ✅ All with clear audio
- ✅ Natural pauses audible
- ✅ Voice tags working ([whispers], [sighs])
- ✅ Consistent voice quality
- ✅ Character-appropriate tone

## 🎉 Next Steps

1. **Run batch test** (when quota available)
2. **Listen to all samples**
3. **Verify voice tags work**
4. **Adjust if needed**
5. **Integrate with main system**

---

**Status**: ✅ All test files ready  
**Command**: `python debug/elevenlabs_tts_standalone.py debug/voice_text`  
**Files**: 20 test texts + 1 tool + 5 docs


