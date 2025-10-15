# Voice Test Texts for Rei Ayanami

This directory contains test texts for ElevenLabs TTS with Rei Ayanami's voice.

## Test Files

### Basic Responses (01-04)
- `01_greeting.txt` - Simple greeting
- `02_low_familiarity_rejection.txt` - Rejecting stranger's request
- `03_simple_refusal.txt` - Direct refusal
- `04_questioning.txt` - Questioning user's concern

### Emotional Responses (05-08)
- `05_confusion.txt` - Expressing confusion about feelings
- `06_with_sigh.txt` - Response with sighing
- `07_acceptance.txt` - Accepting request from trusted user
- `08_simple_confirmation.txt` - Brief confirmation

### Intimate Moments (09-13)
- `09_whisper_intimate.txt` - Whispering intimate feelings
- `10_protection.txt` - Protective declaration
- `11_self_doubt.txt` - Self-doubt expression
- `12_rare_emotion.txt` - Rare emotional moment
- `13_mixed_tags.txt` - Multiple voice tags combined

### Device Control (14-15)
- `14_device_control_accept.txt` - Accepting device control
- `15_device_control_refuse.txt` - Refusing device control

## Voice Tags Used

- `...` - Natural pause (most common)
- `[sighs]` - Sighing (occasional)
- `[whispers]` - Whispering (rare, intimate)
- `[exhales]` - Exhaling (very rare)

## Usage

### Test All Files

```bash
cd /data/jj/proj/hoorii
python debug/elevenlabs_tts_standalone.py debug/voice_text
```

### Test Single File

```bash
python debug/elevenlabs_tts_standalone.py debug/voice_text/01_greeting.txt
```

### Test Direct Text

```bash
python debug/elevenlabs_tts_standalone.py "...Hello. How are you?"
```

## Output

Audio files will be saved with format:
```
{original_filename}_{timestamp}.mp3
```

Example:
```
01_greeting_20251013_223045.mp3
02_low_familiarity_rejection_20251013_223047.mp3
...
```

## Notes

- Each text file should contain a single line or paragraph
- Voice tags will be processed automatically
- Natural pauses (`...`) are kept as-is
- ElevenLabs interprets tags and pauses naturally


