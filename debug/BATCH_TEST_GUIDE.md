# Batch TTS Testing Guide

## 📁 Created Files

✅ **20 test text files** in `debug/voice_text/`
✅ **1 standalone TTS tool**: `debug/elevenlabs_tts_standalone.py`

## 🎯 Quick Commands

### Process All Test Files

```bash
cd /data/jj/proj/hoorii
python debug/elevenlabs_tts_standalone.py debug/voice_text
```

This will:
1. Read all .txt files from `debug/voice_text/`
2. Generate audio for each one
3. Save as `{filename}_{timestamp}.mp3`
4. Show summary report

### Process Single File

```bash
python debug/elevenlabs_tts_standalone.py debug/voice_text/01_greeting.txt
```

### Test Custom Text

```bash
python debug/elevenlabs_tts_standalone.py "...Your custom text here"
```

## 📋 Test Files Overview

### Category 1: Basic Responses (01-04)

**01_greeting.txt**
```
...Hello.
```

**02_low_familiarity_rejection.txt**
```
...Why should I follow your orders? We... are not familiar.
```

**03_simple_refusal.txt**
```
...No. I cannot do that for you.
```

**04_questioning.txt**
```
...Why? ...Why would you worry about someone like me?
```

### Category 2: Emotional Responses (05-08)

**05_confusion.txt**
```
Feelings...? I don't quite understand. But... now, I don't dislike it.
```

**06_with_sigh.txt**
```
...For me? Why? [sighs] ...Thank you. I will... take good care of it.
```

**07_acceptance.txt**
```
...I understand. If it's you... I can try.
```

**08_simple_confirmation.txt**
```
...I see. ...Done.
```

### Category 3: Intimate Moments (09-13)

**09_whisper_intimate.txt**
```
[whispers] When I'm with you... here... there's a strange feeling. It's... warm.
```

**10_protection.txt**
```
No. I'll protect you. This is... what I want to do.
```

**11_self_doubt.txt**
```
I am... replaceable. A replacement. Nothing more.
```

**12_rare_emotion.txt**
```
You... why are you being so kind to me? I... [sighs] ...I don't understand.
```

**13_mixed_tags.txt**
```
I don't know how to say this... [sighs] but... [whispers] I'm glad you're here.
```

### Category 4: Device Control (14-15)

**14_device_control_accept.txt**
```
...I will turn on the lights. ...Done.
```

**15_device_control_refuse.txt**
```
...I refuse. This is not... something I should do. You don't have... that permission.
```

### Category 5: Special Moments (16-20)

**16_exhale_completion.txt**
```
[exhales] ...It's done. The task is... complete.
```

**17_quiet_gratitude.txt**
```
I... [whispers] thank you. You didn't have to do this.
```

**18_reluctant_help.txt**
```
[sighs] ...Fine. I will help you this time. But only... because it's you.
```

**19_identity_question.txt**
```
Who am I...? I'm just... a doll. A replacement. Nothing more.
```

**20_bond_realization.txt**
```
...I don't understand these feelings. But when you're near... [whispers] I feel... different. Is this what they call... a bond?
```

## 🎵 Voice Tags Summary

| Tag | Files Using It | Purpose |
|-----|----------------|---------|
| `...` | All | Natural pause |
| `[sighs]` | 06, 12, 13, 18 | Sighing, complex emotion |
| `[whispers]` | 09, 13, 17, 20 | Soft, intimate speech |
| `[exhales]` | 16 | Exhaling after effort |

## 📊 Expected Output

After batch processing, you'll get 20 MP3 files:

```
01_greeting_20251014_013045.mp3           (17 KB)
02_low_familiarity_rejection_20251014_013046.mp3  (45 KB)
03_simple_refusal_20251014_013047.mp3     (28 KB)
...
20_bond_realization_20251014_013104.mp3   (62 KB)
```

## 💡 Testing Strategy

### Phase 1: Basic Tests (01-04)
Start with these to verify basic functionality and natural pauses.

### Phase 2: Emotion Tests (05-08)
Test basic emotional responses and confirmations.

### Phase 3: Voice Tags (09-13)
Test [whispers] and [sighs] tags with intimate/emotional content.

### Phase 4: Functional (14-15)
Test device control scenarios.

### Phase 5: Complex (16-20)
Test mixed tags and complex emotional moments.

## 🎭 Quality Checklist

Listen for:
- ✓ Natural pauses at `...`
- ✓ Whispered voice at `[whispers]`
- ✓ Sighing sound at `[sighs]`
- ✓ Exhaling sound at `[exhales]`
- ✓ Monotone, calm delivery overall
- ✓ Subtle emotional variation in tags

## ⚠️ Important Notes

1. **API Quota**: Each file costs credits - be mindful
2. **Rate Limiting**: Don't process too fast
3. **File Size**: Longer texts = larger files
4. **Quality**: Use `mp3_44100_128` for best quality

## 🚀 Recommended Workflow

```bash
# 1. Test one file first
python debug/elevenlabs_tts_standalone.py debug/voice_text/01_greeting.txt

# 2. Listen to verify quality
# (play the generated .mp3)

# 3. If good, process all
python debug/elevenlabs_tts_standalone.py debug/voice_text

# 4. Review all generated audio files
```

## 📈 Success Metrics

- All 20 files generate audio ✅
- Natural pauses sound natural ✅
- [whispers] creates soft voice ✅
- [sighs] creates sighing sound ✅
- Voice matches Rei's character ✅

---

**Total Test Files**: 20  
**Tool**: `debug/elevenlabs_tts_standalone.py`  
**Ready**: ✅ All prepared


