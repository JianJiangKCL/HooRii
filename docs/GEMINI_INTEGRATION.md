# Gemini 2.5 Flash Integration Guide

## Overview

The HooRII Smart Home AI Assistant now supports Google Gemini 2.5 Flash as an alternative LLM provider alongside Anthropic Claude.

## What Was Changed

### 1. Configuration System (`src/utils/config.py`)

Added three new configuration classes:
- `GeminiConfig`: Stores Gemini API credentials and settings
- `LLMConfig`: General LLM provider selection
- Updated `Config` class to load both Anthropic and Gemini configurations

### 2. LLM Client Abstraction Layer (`src/utils/llm_client.py`)

Created a new abstraction layer with:
- `LLMClient`: Abstract base class for all LLM providers
- `AnthropicLLMClient`: Anthropic Claude implementation
- `GeminiLLMClient`: Google Gemini implementation
- `create_llm_client()`: Factory function to create the appropriate client

### 3. Core Components Updated

All core components now use the new LLM abstraction:
- `src/core/task_planner.py`
- `src/core/character_system.py`
- `src/core/intent_analyzer.py`
- `src/core/device_controller.py`

### 4. Dependencies

Added `google-generativeai>=0.3.0` to `requirements.txt`

## Configuration

### Environment Variables

```bash
# LLM Provider Selection
LLM_PROVIDER=gemini                # Options: anthropic, gemini
LLM_ENABLED=true

# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/
GEMINI_MAX_TOKENS=1000

# Anthropic Claude API Configuration (fallback)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-sonnet-20240229
ANTHROPIC_MAX_TOKENS=1000
```

### Your Current Configuration

Based on the information provided:
```bash
GEMINI_API_KEY=AIzaSyB2Z9cNLVY8lpz9WjrQ6pZEtFj56zajDJc
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/
GEMINI_MODEL=gemini-2.5-flash
```

## Regional Restrictions

⚠️ **Important**: Google Gemini API has regional restrictions. The error "User location is not supported for the API use" indicates that:

1. The API key may be restricted to specific regions
2. The server location (where the code is running) may not be supported
3. Gemini API is not available in all countries/regions

### Checking Your Region Support

Run the test to check if Gemini is available in your region:

```bash
cd /data/jj/proj/hoorii
python debug/test_gemini_integration.py
```

### Workarounds

If you encounter regional restrictions:

1. **Use a VPN**: Connect to a supported region (e.g., US, EU)
2. **Use Anthropic Claude**: Switch back to Claude by setting:
   ```bash
   LLM_PROVIDER=anthropic
   ```
3. **Request Region Access**: Contact Google Cloud support to enable your region
4. **Use Google AI Studio**: Create a new API key from Google AI Studio which may have different region support

## Switching Between Providers

### To Use Gemini:
```bash
export LLM_PROVIDER=gemini
export GEMINI_API_KEY=your_key_here
```

### To Use Anthropic Claude:
```bash
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=your_key_here
```

## Architecture

### LLM Client Abstraction

```python
# Before (directly using Anthropic)
claude_client = anthropic.Anthropic(api_key=config.anthropic.api_key)
response = claude_client.messages.create(...)

# After (using abstraction)
llm_client = create_llm_client(config)
response = await llm_client.generate(
    system_prompt=system_prompt,
    messages=messages,
    max_tokens=max_tokens,
    temperature=temperature
)
```

### Message Format

Both providers use a unified message format:
```python
messages = [
    {"role": "user", "content": "用户输入"},
    {"role": "assistant", "content": "助手回复"},
    {"role": "user", "content": "下一个用户输入"}
]
```

## Testing

### Run Integration Tests

```bash
# Test Gemini integration
python debug/test_gemini_integration.py

# Test with actual components
python debug/intent_analysis_test.py
python debug/character_test.py
```

### Manual Testing

```python
from src.utils.config import load_config
from src.utils.llm_client import create_llm_client

# Load configuration
config = load_config()
print(f"Using LLM provider: {config.llm.provider}")

# Create client
llm_client = create_llm_client(config)

# Generate response
response = await llm_client.generate(
    system_prompt="你是一个友好的AI助手",
    messages=[{"role": "user", "content": "你好"}],
    max_tokens=100,
    temperature=0.7
)

print(response)
```

## Troubleshooting

### Error: "User location is not supported"

**Cause**: Gemini API is not available in your region.

**Solutions**:
1. Use a VPN to connect from a supported region
2. Switch to Anthropic Claude provider
3. Contact Google Cloud support

### Error: "GEMINI_API_KEY is required"

**Cause**: API key not set in environment variables.

**Solution**: Set the API key:
```bash
export GEMINI_API_KEY=your_key_here
```

### Error: "ImportError: No module named 'google.generativeai'"

**Cause**: Package not installed.

**Solution**: Install the package:
```bash
pip install google-generativeai>=0.3.0
```

### Error: "Gemini returned no text. Finish reason: 2"

**Cause**: Response was blocked by safety filters or regional restrictions.

**Solutions**:
1. Modify the prompt to avoid triggering safety filters
2. Check if your region is supported
3. Review Gemini's content policy

## Performance Considerations

### Token Usage

- **Gemini 2.5 Flash**: Generally faster and cheaper than Claude
- **Anthropic Claude**: More consistent with complex reasoning tasks

### Response Time

- **Gemini**: ~1-2 seconds for typical requests
- **Claude**: ~2-3 seconds for typical requests

### Cost Comparison

- **Gemini 2.5 Flash**: $0.075/1M input tokens, $0.30/1M output tokens
- **Claude 3 Sonnet**: $3/1M input tokens, $15/1M output tokens

## Migration Guide

### From Claude-Only to Multi-Provider

The migration is automatic. All existing code continues to work because:

1. The LLM client abstraction maintains the same interface
2. Configuration validation ensures only one provider is active
3. Error handling is consistent across providers

### Gradual Migration

You can test Gemini without changing production:

1. Keep `LLM_PROVIDER=anthropic` in production
2. Test with `LLM_PROVIDER=gemini` in development
3. Compare results and performance
4. Switch when ready

## Future Enhancements

Potential improvements:
1. Support for more providers (OpenAI GPT-4, Claude 3.5, etc.)
2. Automatic failover between providers
3. Load balancing across multiple providers
4. Provider-specific optimizations
5. Cost tracking and optimization

## Support

For issues or questions:
1. Check this documentation
2. Run integration tests
3. Review logs for detailed error messages
4. Consult Gemini API documentation: https://ai.google.dev/docs

## References

- [Google Gemini API Documentation](https://ai.google.dev/docs)
- [Anthropic Claude API Documentation](https://docs.anthropic.com/)
- [HooRII Project Documentation](../docs/README.md)

