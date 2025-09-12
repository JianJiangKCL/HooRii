# Debug Folder

This folder contains all test files for the Home AI system.

## Usage

All test files should be created in this folder following the naming convention:
- `test_[component_name].py` for component tests
- `test_integration_[feature].py` for integration tests
- `test_system_[scenario].py` for system tests

## Running Tests

Run individual test:
```bash
python debug/test_component.py
```

Run all tests:
```bash
cd debug && for f in test_*.py; do echo "=== Running $f ===" && python "$f" && echo; done
```

## Test Categories

1. **Component Tests**: Test individual components (intent_analyzer, device_controller, character_system)
2. **Integration Tests**: Test component interactions
3. **System Tests**: Test complete conversation flows
4. **Connection Tests**: Test external service connections (Langfuse, database)
5. **Session Tests**: Test session management and persistence

Refer to `../CLAUDE.md` for detailed development rules and test templates.