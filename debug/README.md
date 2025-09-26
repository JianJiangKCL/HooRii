# Debug & Testing Directory

This directory contains all test files and debugging utilities for the HooRii Smart Home AI Assistant.

## Test Files

### `agora_tts_test.py`
Comprehensive test suite for the Agora TTS (Text-to-Speech) service.

**Features tested:**
- Configuration validation
- API signature generation
- TTS synthesis with different methods
- Audio file saving
- Error handling scenarios

**Usage:**
```bash
cd /data/jj/proj/hoorii
python debug/agora_tts_test.py
```

**Requirements:**
- Agora TTS must be properly configured in `.env` file
- Network access to Agora API endpoints
- Valid Agora credentials and project ID

**Test Scenarios:**
1. **Configuration Test**: Validates service setup and credentials
2. **Signature Generation**: Tests API authentication signature creation
3. **TTS Synthesis**: Tests actual text-to-speech conversion
4. **File Save**: Tests saving audio output to file
5. **Error Handling**: Tests various failure scenarios

The test will automatically skip network-dependent tests if the service is not properly configured, making it safe to run in any environment.

## Test Guidelines

All test files in this directory follow the project's testing rules:
- Include proper path setup for importing from parent directory
- Disable OpenTelemetry for tests
- Use descriptive names ending in `_test.py`
- Provide comprehensive test coverage
- Handle configuration and network issues gracefully
