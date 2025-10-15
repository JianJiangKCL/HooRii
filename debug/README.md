# Debug & Testing Directory

## 🏠 Device Controller Testing

### Real Devices Test

Test device controller with real device configurations (dimmable light and curtain):

```bash
python debug/device_controller_real_devices_test.py
```

This test covers:
- **演示调光灯** (Dimmable Light): brightness, hue, saturation controls
- **演示窗帘** (Curtain): position controls
- Color name conversion (hue → Chinese color names)

### Initialize Real Devices

To add real devices to the database:

```bash
python scripts/init_real_devices.py
```

This will add:
1. **演示调光灯** - Dimmable light with color controls
2. **演示窗帘** - Curtain with position controls

### Workflow Integration Test

Test complete device control flow through LangGraph workflow:

```bash
python debug/workflow_device_control_test.py
```

This test covers:
- Familiarity checking mechanism
- Device control execution
- Standard JSON output format validation
- Langfuse monitoring coverage
- Dimmable light and curtain controls

See `docs/DEVICE_CONTROLLER_REAL_DEVICES.md` and `docs/DEVICE_CONTROL_WORKFLOW_VALIDATION.md` for detailed documentation.

---

## 🎭 ElevenLabs TTS Testing Suite

### Quick Start

**Test one file**:
```bash
python debug/elevenlabs_tts_standalone.py debug/voice_text/01_greeting.txt
```

**Test all files**:
```bash
python debug/elevenlabs_tts_standalone.py debug/voice_text
```

**All outputs save to**: `debug/tts_output/` ✅

## 📁 Directory Structure

```
debug/
├── elevenlabs_tts_standalone.py    # Standalone TTS tool
│
├── voice_text/                     # Test texts (20 files)
│   ├── 01_greeting.txt
│   ├── 02_low_familiarity_rejection.txt
│   ├── ... (18 more .txt files)
│   ├── README.md
│   └── test_samples_list.md
│
├── tts_output/                     # Generated audio (all .mp3)
│   ├── .gitignore
│   ├── README.md
│   └── (generated .mp3 files here)
│
└── Documentation/
    ├── QUICK_START.md              # Quick reference
    ├── USAGE_GUIDE.md              # Complete usage guide
    ├── ELEVENLABS_TTS_TESTING.md   # Testing details
    └── (more guides)
```

## 🎯 Test Files

**20 test texts** covering:
- Basic responses (01-04)
- Emotional responses (05-08)
- Intimate moments (09-13)
- Device control (14-15)
- Complex emotions (16-20)

**Voice tags used**:
- `...` - Natural pause (all files)
- `[whispers]` - 4 files
- `[sighs]` - 4 files
- `[exhales]` - 1 file

## 🔧 Configuration

**Voice**: `19STyYD15bswVz51nqLf`  
**Model**: `eleven_flash_v2_5`  
**Output**: `debug/tts_output/` ✅

## 📚 Documentation

- **QUICK_START.md** - One-page reference
- **USAGE_GUIDE.md** - Full usage guide
- **voice_text/README.md** - Test texts overview
- **tts_output/README.md** - Output directory info

## ✅ Status

- [x] Tool created and tested
- [x] 20 test texts ready
- [x] Output directory configured
- [x] Voice tags working
- [x] Documentation complete

## 🚀 Next Steps

When API quota available, run:
```bash
python debug/elevenlabs_tts_standalone.py debug/voice_text
```

This will generate all 20 audio files in `debug/tts_output/`.

---

**See**: `QUICK_START.md` for commands
