# How to Use ElevenLabs TTS Standalone Tool

## 🎯 Quick Start

### Batch Process All Test Texts

```bash
cd /data/jj/proj/hoorii
python debug/elevenlabs_tts_standalone.py debug/voice_text
```

This will process all 20 test files and generate audio files.

### Test Single File

```bash
python debug/elevenlabs_tts_standalone.py debug/voice_text/01_greeting.txt
```

### Test Direct Text

```bash
python debug/elevenlabs_tts_standalone.py "...Hello. How are you today?"
```

### Interactive Mode

```bash
python debug/elevenlabs_tts_standalone.py
```

Then enter text interactively, or type `batch` to process all voice_text files.

## 📁 Test Files Available

We have **20 test texts** in `debug/voice_text/`:

### Basic (01-04)
- 01_greeting - Simple greeting
- 02_low_familiarity_rejection - Stranger rejection
- 03_simple_refusal - Direct refusal
- 04_questioning - Questioning concern

### Emotional (05-08)
- 05_confusion - Confused about feelings
- 06_with_sigh - Response with [sighs]
- 07_acceptance - Accepting from trusted user
- 08_simple_confirmation - Brief confirmation

### Intimate (09-13)
- 09_whisper_intimate - [whispers] intimate moment
- 10_protection - Protective statement
- 11_self_doubt - Self-doubt expression
- 12_rare_emotion - Rare emotional moment
- 13_mixed_tags - Multiple tags combined

### Device Control (14-15)
- 14_device_control_accept - Accepting control
- 15_device_control_refuse - Refusing control

### Special (16-20)
- 16_exhale_completion - [exhales] after task
- 17_quiet_gratitude - [whispers] gratitude
- 18_reluctant_help - [sighs] reluctant help
- 19_identity_question - Identity questioning
- 20_bond_realization - Mixed tags with [whispers]

## 🎵 Output Files

Audio files are saved as:
```
{filename}_{timestamp}.mp3
```

Example:
```
01_greeting_20251014_013045.mp3
02_low_familiarity_rejection_20251014_013046.mp3
...
```

## 📊 Expected Results

When you run batch processing:

```
🎭 Testing 20 text files from debug/voice_text
======================================================================

📄 Processing: debug/voice_text/01_greeting.txt
📝 Text: ...Hello.
🎵 Generating audio...
✅ Saved to: ./01_greeting_20251014_013045.mp3
   Size: 24.3 KB

📄 Processing: debug/voice_text/02_low_familiarity_rejection.txt
📝 Text: ...Why should I follow your orders? We... are not familiar.
🎵 Generating audio...
✅ Saved to: ./02_low_familiarity_rejection_20251014_013046.mp3
   Size: 45.2 KB

...

📊 Test Summary
======================================================================
✅ 01_greeting.txt
✅ 02_low_familiarity_rejection.txt
✅ 03_simple_refusal.txt
...

✅ Success: 20/20
```

## 💡 Tips

1. **Keep API quota in mind** - Each text costs credits
2. **Listen to outputs** - Verify voice tags work as expected
3. **Compare different tags** - Hear difference between [sighs], [whispers], etc.
4. **Natural pauses** - `...` creates natural pauses without tags

## 🔧 Voice Tags Reference

**Used in test files**:
- `...` - Natural pause (kept as-is)
- `[whispers]` - Soft, intimate speech
- `[sighs]` - Sighing sound
- `[exhales]` - Exhaling sound

**Not used (out of character)**:
- `[laughs]` - Rei rarely laughs
- `[excited]` - Not her style
- `[shouting]` - Never

## 🎭 Rei's Character Voice

The voice should sound:
- Calm and monotone
- With natural pauses showing hesitation
- Occasionally sighing (complex emotions)
- Rarely whispering (intimate moments)
- Detached but gradually warming

## ⚠️ Troubleshooting

### Error: quota_exceeded

Your API quota is insufficient. Either:
- Wait for quota reset
- Upgrade your plan
- Test fewer files at once

### Error: voice_not_found

Voice ID is wrong. Should be: `19STyYD15bswVz51nqLf`

### Error: API key missing

Set in `.env`:
```
ELEVENLABS_API_KEY=your_key_here
```

---

**Tool**: `debug/elevenlabs_tts_standalone.py`  
**Texts**: `debug/voice_text/*.txt` (20 files)  
**Ready**: ✅ All files created


