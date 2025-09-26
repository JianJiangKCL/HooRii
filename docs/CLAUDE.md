# Claude Development Rules for Home AI Project

## Test File Generation Rules

### When creating test files, always place them in the `debug/` folder

**Test file naming convention:**
- Component tests: `debug/test_[component_name].py`
- Integration tests: `debug/test_integration_[feature].py`
- System tests: `debug/test_system_[scenario].py`
- Connection tests: `debug/test_connection_[service].py`
- Session tests: `debug/test_session_[type].py`

**Test file template structure:**
```python
#!/usr/bin/env python3
"""
[Test Description]
"""
import asyncio
import uuid
import logging
from datetime import datetime

# Test specific imports here

async def test_[function_name]():
    """Test [description]"""
    # Setup
    print("🧪 [Test Name]")
    print("=" * 50)
    
    try:
        # Test logic here
        
        print("✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup if needed
        pass

if __name__ == "__main__":
    asyncio.run(test_[function_name]())
```

### Component Testing Rules

1. **Langfuse Tests**: Always test with unique session/user IDs
2. **Database Tests**: Use transaction rollbacks for cleanup
3. **Context Tests**: Test context persistence and state management
4. **Integration Tests**: Test full conversation flows
5. **Error Handling**: Test error scenarios and recovery

### File Organization
- Main code: Root directory
- Tests: `debug/` folder only
- Prompts: `prompts/` folder
- Context saves: `contexts/` folder
- Configuration: Root directory

### Development Commands

**Run specific test:**
```bash
python debug/test_[component].py
```

**Run all debug tests:**
```bash
cd debug && for f in test_*.py; do echo "=== Running $f ===" && python "$f" && echo; done
```

**Clean debug folder:**
```bash
rm -f debug/test_*.py
```

### Prompt Management
- All LLM prompts must be in `prompts/` folder
- Load prompts using `_load_prompt_file()` method
- Fallback to default prompts if files not found

### Context Management
- Always pass `SystemContext` between components
- Update context state after each operation
- Save context to `contexts/` for persistence

### Database Rules
- Use proper session management
- Handle SQLAlchemy session binding carefully
- Log all device interactions
- Implement proper cleanup methods

### Observability Rules
- Use `@observe` decorator for all major functions
- Track sessions with Langfuse session management
- Include user tracking and familiarity scoring
- Add metadata for debugging

This file serves as the development guideline for maintaining code quality and organization.