# ElevenLabs TTS Tool - Usage Guide

## 📁 Output Directory

**All generated audio files go to**: `debug/tts_output/`

This keeps the project root clean and organizes all test outputs in one place.

## 🚀 Commands

### Test Single File

```bash
python debug/elevenlabs_tts_standalone.py debug/voice_text/01_greeting.txt
```

**Output**: `debug/tts_output/01_greeting_20251014_032104.mp3`

### Test All Files (Batch)

```bash
python debug/elevenlabs_tts_standalone.py debug/voice_text
```

**Output**: 20 files in `debug/tts_output/`:
```
debug/tts_output/01_greeting_20251014_032104.mp3
debug/tts_output/02_low_familiarity_rejection_20251014_032105.mp3
...
debug/tts_output/20_bond_realization_20251014_032123.mp3
```

### Test Custom Text

```bash
python debug/elevenlabs_tts_standalone.py "...I don't understand."
```

**Output**: `debug/tts_output/test_20251014_032104.mp3`

### Custom Output Directory (Optional)

```bash
# Specify different output directory
python debug/elevenlabs_tts_standalone.py debug/voice_text my_output_dir
```

## 📊 Directory Structure

```
debug/
├── elevenlabs_tts_standalone.py    # Main tool
├── voice_text/                     # Input test texts (20 files)
│   ├── 01_greeting.txt
│   ├── 02_low_familiarity_rejection.txt
│   └── ... (18 more)
└── tts_output/                     # Output audio files
    ├── 01_greeting_20251014_032104.mp3
    ├── 02_low_familiarity_rejection_20251014_032105.mp3
    └── ... (more as generated)
```

## 🎵 Generated Files

**Naming**: `{filename}_{timestamp}.mp3`

**Location**: `debug/tts_output/`

**Format**: MP3 (44.1kHz, 128kbps)

## 🧪 Test Workflow

### Step 1: Test One File

```bash
python debug/elevenlabs_tts_standalone.py debug/voice_text/01_greeting.txt
```

**Expected**:
```
✓ API Key: ********************7bbffd349d
✓ Voice ID: 19STyYD15bswVz51nqLf
✓ Model: eleven_flash_v2_5

📄 Processing: debug/voice_text/01_greeting.txt
📝 Text: ...Hello.
🎵 Generating audio...
✅ Saved to: debug/tts_output/01_greeting_20251014_032104.mp3
   Size: 16.0 KB
```

### Step 2: Listen to Verify

```bash
# Play the audio (Linux)
mpv debug/tts_output/01_greeting_20251014_032104.mp3

# Or use any audio player
```

### Step 3: Batch Process All

```bash
python debug/elevenlabs_tts_standalone.py debug/voice_text
```

**Expected**:
```
🎭 Testing 20 text files from debug/voice_text
📁 Output directory: debug/tts_output

✅ Success: 20/20
📁 All files saved in: debug/tts_output
```

## 📋 What Gets Generated

After batch test, you'll have in `debug/tts_output/`:

```
01_greeting_*.mp3                      (~16 KB)
02_low_familiarity_rejection_*.mp3     (~45 KB)
03_simple_refusal_*.mp3                (~28 KB)
04_questioning_*.mp3                   (~35 KB)
05_confusion_*.mp3                     (~50 KB)
06_with_sigh_*.mp3                     (~58 KB)
07_acceptance_*.mp3                    (~30 KB)
08_simple_confirmation_*.mp3           (~20 KB)
09_whisper_intimate_*.mp3              (~60 KB)
10_protection_*.mp3                    (~38 KB)
11_self_doubt_*.mp3                    (~42 KB)
12_rare_emotion_*.mp3                  (~52 KB)
13_mixed_tags_*.mp3                    (~65 KB)
14_device_control_accept_*.mp3         (~28 KB)
15_device_control_refuse_*.mp3         (~55 KB)
16_exhale_completion_*.mp3             (~35 KB)
17_quiet_gratitude_*.mp3               (~38 KB)
18_reluctant_help_*.mp3                (~60 KB)
19_identity_question_*.mp3             (~48 KB)
20_bond_realization_*.mp3              (~70 KB)
```

**Total**: ~800 KB for all 20 files

## 🎭 Character Verification

Listen to verify Rei Ayanami's voice characteristics:

✓ Calm, monotone delivery  
✓ Natural pauses at `...`  
✓ Soft voice at `[whispers]`  
✓ Sighing sounds at `[sighs]`  
✓ Exhaling at `[exhales]`  
✓ Consistent character throughout

## 💡 Tips

1. **Start small**: Test 1-2 files first
2. **Check quality**: Listen before batch processing
3. **Watch quota**: Each file costs API credits
4. **Compare tags**: Listen to difference between files with/without tags

## 🔧 Advanced Usage

### Custom Output Directory

```bash
# Save to specific directory
python debug/elevenlabs_tts_standalone.py debug/voice_text my_custom_dir
```

### Process Specific Files

```bash
# Only intimate moments (files 09-13)
for i in {09..13}; do
  python debug/elevenlabs_tts_standalone.py debug/voice_text/${i}_*.txt
done
```

## 📊 File Organization

```
hoorii/
├── debug/
│   ├── elevenlabs_tts_standalone.py   ← Tool
│   ├── voice_text/                    ← Input (20 .txt)
│   │   ├── 01_greeting.txt
│   │   ├── 02_low_familiarity_rejection.txt
│   │   └── ...
│   └── tts_output/                    ← Output (.mp3)
│       ├── 01_greeting_20251014_032104.mp3
│       ├── 02_low_familiarity_rejection_20251014_032105.mp3
│       └── ...
```

## ✅ Quick Reference

**Test one**:
```bash
python debug/elevenlabs_tts_standalone.py debug/voice_text/01_greeting.txt
```

**Test all**:
```bash
python debug/elevenlabs_tts_standalone.py debug/voice_text
```

**Custom text**:
```bash
python debug/elevenlabs_tts_standalone.py "...Your text here"
```

**All outputs**: `debug/tts_output/`

---

**Updated**: 2025-10-14  
**Output Dir**: `debug/tts_output/` ✅

