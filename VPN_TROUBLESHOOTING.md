# VPN故障排查指南

## 🔴 问题症状

您看到了这些错误：
```
Gemini API error: 400 User location is not supported for the API use.
finish_reason=2  (SAFETY - 安全过滤器阻止)
```

## 🔍 根本原因

1. **VPN连接问题**：Gemini API需要VPN连接到支持的地区（美国、欧盟等）
2. **VPN不稳定**：连接可能时好时坏
3. **安全过滤器**：某些prompt格式触发了Gemini的安全过滤器（已修复）

## ✅ 解决方案

### 方案1：修复VPN连接（推荐 - 使用Gemini）

```bash
# 1. 确保VPN连接到支持的地区
# 支持的地区：美国、欧盟、日本等

# 2. 测试连接
cd /data/jj/proj/hoorii
python debug/verify_gemini_setup.py

# 3. 如果测试通过，运行应用
python scripts/run_app.py
```

### 方案2：切换到Anthropic Claude（无需VPN）

如果VPN持续不稳定，可以切换到Anthropic：

```bash
# 1. 编辑.env文件
nano .env

# 2. 修改这一行：
LLM_PROVIDER=anthropic  # 从gemini改为anthropic

# 3. 添加Anthropic API Key（如果有）：
ANTHROPIC_API_KEY=your_key_here

# 4. 运行应用
python scripts/run_app.py
```

### 方案3：使用自动切换脚本

```bash
# 自动检测可用的provider并切换
python scripts/switch_llm_provider.py

# 然后运行应用
python scripts/run_app.py
```

## 🎯 我已经做的修复

### 1. 安全过滤器问题（finish_reason=2）
✅ **已修复**：
- 添加了安全设置 `BLOCK_NONE` 来放宽过滤
- 简化了prompt格式，避免触发过滤器
- 添加了更好的错误处理

### 2. prompt构建优化
✅ **已优化**：
- 使用更简洁的prompt格式
- 只发送最后一条用户消息，避免过长内容
- 移除了可能触发过滤的格式

### 3. 配置文件
✅ **已更新**：
- `.env`文件包含清晰的切换说明
- 代码默认使用Gemini（当VPN可用时）
- 支持快速切换到Anthropic

## 📊 提供商对比

| 特性 | Gemini 2.5 Flash | Anthropic Claude 3 |
|------|------------------|-------------------|
| **需要VPN** | ✅ 是 | ❌ 否 |
| **速度** | ⚡ 非常快 | 🐢 中等 |
| **成本** | 💰 $0.075/1M tokens | 💸 $3/1M tokens |
| **质量** | 👍 很好 | 🌟 优秀 |
| **稳定性** | ⚠️ 取决于VPN | ✅ 很稳定 |

## 🔧 快速测试命令

### 测试Gemini连接
```bash
python -c "import google.generativeai as genai; genai.configure(api_key='AIzaSyB2Z9cNLVY8lpz9WjrQ6pZEtFj56zajDJc'); print(genai.GenerativeModel('gemini-2.5-flash').generate_content('Hello').text)"
```

### 测试当前配置
```bash
cd /data/jj/proj/hoorii
python -c "from src.utils.config import load_config; config = load_config(); print(f'Provider: {config.llm.provider}')"
```

### 测试LLM客户端
```bash
python debug/verify_gemini_setup.py
```

## 💡 推荐工作流程

### 如果您有稳定的VPN：
```bash
# 1. 连接VPN到美国/欧盟
# 2. 使用Gemini（默认）
python scripts/run_app.py
```

### 如果VPN不稳定：
```bash
# 1. 编辑.env，改为 LLM_PROVIDER=anthropic
# 2. 设置 ANTHROPIC_API_KEY
# 3. 运行应用
python scripts/run_app.py
```

### 混合使用：
```bash
# VPN正常时用Gemini（便宜快速）
export LLM_PROVIDER=gemini

# VPN断开时切换到Claude（无需VPN）
export LLM_PROVIDER=anthropic
```

## 📝 日志说明

### 正常日志（可以忽略）：
```
⚠️ Warning: Langfuse keys not configured. Observability will be disabled.
→ 这是正常的，Langfuse是可选的监控工具

OpenAI TTS configuration missing or disabled. Provider unavailable.
→ 这是正常的，如果不需要语音输出可以忽略
```

### 需要关注的错误：
```
❌ 400 User location is not supported
→ VPN问题，需要连接VPN或切换到Anthropic

❌ finish_reason=2 (SAFETY)
→ 安全过滤器（已修复），如果还出现请报告
```

## 🆘 如果问题持续

1. **VPN连接测试**：
   ```bash
   curl -I https://generativelanguage.googleapis.com
   ```

2. **查看详细日志**：
   ```bash
   export LOG_LEVEL=DEBUG
   python scripts/run_app.py
   ```

3. **使用Anthropic**：
   最简单的解决方案，不依赖VPN

## ✅ 当前状态

- ✅ Gemini API Key已配置
- ✅ 安全过滤器已优化
- ✅ prompt格式已修复
- ✅ 支持快速切换providers
- ⚠️ 需要稳定的VPN连接（或使用Anthropic）

您现在可以：
1. 连接VPN → 使用Gemini（快速便宜）
2. 或切换到Anthropic → 无需VPN（稳定）

