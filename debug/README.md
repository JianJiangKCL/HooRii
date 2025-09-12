# Debug and Testing Directory

This directory contains all testing and debugging utilities for the HooRii Smart Home AI Assistant.

## Test Files

### Component Tests (Test individual components in isolation)

- `intent_analysis_test.py` - Tests the intent analysis component
- `character_test.py` - Tests the character (凌波丽) response generation
- `device_controller_test.py` - Tests device controller logic

### Integration Tests

- `integration_test.py` - Tests the full system flow

### Usage

Run individual component tests:
```bash
cd /path/to/hoorii
python debug/intent_analysis_test.py
python debug/character_test.py
python debug/device_controller_test.py
```

Run integration test:
```bash
python debug/integration_test.py
```

### Test Structure

All test files follow this pattern:
1. Add parent directory to Python path
2. Disable OpenTelemetry for clean output
3. Import required components
4. Run focused tests with clear output
5. Validate expected behavior

### Adding New Tests

When creating new test files:
1. Use the naming convention: `component_test.py`
2. Include the standard header (see existing files)
3. Focus on testing one component or flow
4. Provide clear test descriptions and expected outcomes
5. Handle errors gracefully with meaningful messages

### Component Architecture

Tests are designed to validate the decoupled architecture:

```
User Input → Task Planner → Intent Analysis
                ↓
         Device Controller (if needed)
                ↓
         Execute Device Command
                ↓
         Character System → Response
```

Each component should be testable in isolation.
