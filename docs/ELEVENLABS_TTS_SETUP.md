# ElevenLabs TTS 配置指南

## 概述

本系统已集成 ElevenLabs TTS，专门为凌波丽角色配置了语气控制功能。系统会自动将文本中的语气标记转换为 SSML 格式，实现更自然的语音合成。

## 配置步骤

### 1. 设置 ElevenLabs API

1. 注册 [ElevenLabs](https://elevenlabs.io/) 账号
2. 获取 API Key
3. 确认使用的 Voice ID: `19STyYD15bswVz51nqLf`

### 2. 运行配置脚本

```bash
python scripts/setup_elevenlabs_tts.py
```

这个脚本会：
- 检查 `.env` 文件是否存在
- 更新 TTS 配置为 ElevenLabs
- 设置正确的 Voice ID 和 Model

### 3. 手动配置（可选）

如果需要手动配置，编辑 `.env` 文件：

```env
# Text-to-Speech Provider
TTS_PROVIDER=elevenlabs
TTS_ENABLED=true

# ElevenLabs TTS Configuration
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_VOICE_ID=19STyYD15bswVz51nqLf
ELEVENLABS_MODEL=eleven_flash_v2_5
ELEVENLABS_OUTPUT_FORMAT=mp3_44100_128
ELEVENLABS_TTS_ENABLED=true

# 可选：微调语音参数
# ELEVENLABS_VOICE_SETTINGS={"stability":0.5,"similarity_boost":0.75}
```

## 语气控制 - ElevenLabs Audio Tags

系统使用 **ElevenLabs Audio Tags** 格式（不是 SSML），自动转换文本标记：

### 支持的 Audio Tags

| 原文标记 | ElevenLabs Tag | 效果 |
|---------|----------------|------|
| `...` (省略号) | `[PAUSES]` | 停顿和沉默 |
| `【停顿】` | `[PAUSES]` | 明确停顿 |
| `【叹气】` | `[SIGH]` | 叹气声效 |
| `【轻声：内容】` | `[QUIETLY] 内容` | 轻声说话 |
| `【犹豫：内容】` | `[NERVOUS] 内容` | 犹豫语气 |
| `【强调：内容】` | `[LOUDLY] 内容` | 强调大声 |

### 其他可用 Audio Tags

- `[EXCITED]` - 兴奋
- `[FRUSTRATED]` - 沮丧
- `[TIRED]` - 疲惫
- `[NERVOUS]` - 紧张

### 转换示例

**原始文本：**
```
...为什么要听从你的指令？我们...并不熟悉。
```

**转换后（Audio Tags）：**
```
[PAUSES] 为什么要听从你的指令？我们 [PAUSES] 并不熟悉。
```

**原始文本：**
```
...给我的？为什么？【叹气】...谢谢。
```

**转换后（Audio Tags）：**
```
[PAUSES] 给我的？为什么？ [SIGH] [PAUSES] 谢谢。
```

**原始文本：**
```
【轻声：这里】会有奇怪的感觉。
```

**转换后（Audio Tags）：**
```
[QUIETLY] 这里会有奇怪的感觉。
```

## 角色 Prompt 更新

`prompts/character.txt` 已更新，包含语气标记使用指南：

- LLM 会被指示在生成回复时使用这些标记
- 标记会在 TTS 处理前自动转换
- 显示给用户的文本会移除 SSML 标记

## 测试

### 运行测试脚本

```bash
python debug/test_tts_with_markers.py
```

测试内容：
1. 文本格式化转换测试
2. 单个样本 TTS 合成测试
3. 多个样本批量生成测试

### 测试样本

脚本会生成以下测试音频文件：
- `test_rei_tts_output.mp3` - 主要测试样本
- `test_sample1.mp3` - 拒绝场景
- `test_sample2.mp3` - 困惑场景
- `test_sample3.mp3` - 感谢场景

## 使用流程

### 1. 在对话中自动使用

系统会自动处理：
```
用户: 帮我打开空调
凌波丽: ......为什么要听从你的指令？我们......并不熟悉。
```

TTS 会自动：
1. 识别 `......` 标记
2. 转换为 SSML `<break time="800ms"/>`
3. 发送到 ElevenLabs 生成语音
4. 返回带有自然停顿的音频

### 2. API 调用

```python
from src.services.agora_tts_service import AgoraTTSService
from src.utils.config import load_config

config = load_config()
tts = AgoraTTSService(config)

# 文本会自动格式化
text = "......为什么要听从你的指令？"
audio_base64 = await tts.text_to_speech(text)
```

## 工具函数

### 文本格式化

```python
from src.utils.text_formatting import (
    format_for_rei_ayanami,
    convert_to_elevenlabs_ssml,
    remove_ssml_for_display
)

# 格式化文本
original = "......为什么？"
formatted = format_for_rei_ayanami(original)  # 转换为 SSML

# 移除 SSML 用于显示
display = remove_ssml_for_display(formatted)
```

### 支持的 TTS Provider

```python
from src.utils.text_formatting import format_text_for_tts

# 自动选择格式化方式
text = "......"
formatted = format_text_for_tts(text, provider='elevenlabs')  # 使用 SSML
formatted = format_text_for_tts(text, provider='openai')      # 不处理
```

## 故障排查

### 问题：TTS 不工作

**检查清单：**
1. `.env` 中 `ELEVENLABS_API_KEY` 是否正确
2. `TTS_PROVIDER=elevenlabs` 是否设置
3. `ELEVENLABS_TTS_ENABLED=true` 是否启用
4. Voice ID 是否正确：`19STyYD15bswVz51nqLf`

### 问题：音频没有停顿效果

**可能原因：**
1. 文本中没有使用 `......` 标记
2. SSML 转换未启用
3. ElevenLabs API 版本不支持 SSML

**解决方案：**
- 检查 `src/utils/text_formatting.py` 是否正确导入
- 查看日志中是否有 "Text formatted for elevenlabs" 消息
- 使用测试脚本验证转换

### 问题：语音质量不佳

**调整参数：**
在 `.env` 中添加：
```env
ELEVENLABS_VOICE_SETTINGS={"stability":0.5,"similarity_boost":0.75}
```

参数说明：
- `stability` (0-1)：稳定性，越高越一致但可能不够自然
- `similarity_boost` (0-1)：相似度提升，越高越接近原始声音

## 模型说明

### eleven_flash_v2_5

- **特点**：快速、低延迟
- **适用场景**：实时对话、流式输出
- **语言支持**：多语言（包括中文）
- **SSML 支持**：完整支持

### 其他可选模型

```env
# 标准多语言模型（更高质量但较慢）
ELEVENLABS_MODEL=eleven_multilingual_v2

# Turbo 模型（最快）
ELEVENLABS_MODEL=eleven_turbo_v2

# Flash v2.5（推荐）
ELEVENLABS_MODEL=eleven_flash_v2_5
```

## 性能优化

### 减少延迟

```env
# 优化流式传输延迟（0-4，越高越快但质量可能下降）
ELEVENLABS_OPTIMIZE_STREAMING_LATENCY=2
```

### 输出格式

```env
# 高质量 MP3
ELEVENLABS_OUTPUT_FORMAT=mp3_44100_128

# 低延迟 MP3（更快但质量稍低）
ELEVENLABS_OUTPUT_FORMAT=mp3_22050_32

# PCM（未压缩，最高质量）
ELEVENLABS_OUTPUT_FORMAT=pcm_44100
```

## 参考资源

- [ElevenLabs API 文档](https://elevenlabs.io/docs)
- [ElevenLabs Voice Library](https://elevenlabs.io/voice-library)
- [SSML 标准](https://www.w3.org/TR/speech-synthesis11/)

## 更新日志

### 2025-10-13
- ✅ 添加 ElevenLabs TTS 支持
- ✅ 实现语气标记自动转换
- ✅ 更新凌波丽角色 prompt
- ✅ 配置 Voice ID: 19STyYD15bswVz51nqLf
- ✅ 使用模型: eleven_flash_v2_5
- ✅ 创建测试脚本和配置工具

