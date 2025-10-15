#!/usr/bin/env python3
"""
Workflow Device Control Test
Tests complete device control flow through LangGraph workflow
Validates:
1. Familiarity checking
2. Device control execution
3. Standard JSON output format
4. Langfuse monitoring
"""
import sys
import os
import asyncio
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable OpenTelemetry for tests
os.environ['OTEL_TRACES_EXPORTER'] = 'none'
os.environ['OTEL_METRICS_EXPORTER'] = 'none'
os.environ['OTEL_LOGS_EXPORTER'] = 'none'

from src.workflows.langraph_workflow import LangGraphHomeAISystem
from src.utils.config import load_config


async def test_familiarity_check():
    """Test familiarity checking mechanism"""
    print("\n" + "="*60)
    print("Test 1: Familiarity Check")
    print("="*60)
    
    config = load_config()
    system = LangGraphHomeAISystem(config)
    
    print("\n📝 Scenario 1: Low familiarity user (25/100) tries to control air conditioner (requires 60)")
    result = await system.process_message(
        "打开空调",
        user_id="low_familiarity_user",
        session_id="test_familiarity_low"
    )
    
    print("\nResult:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    device_actions = result.get("device_actions", [])
    if device_actions and not device_actions[0].get("success"):
        print("\n✅ PASS: Low familiarity user correctly denied")
    else:
        print("\n❌ FAIL: Low familiarity user should be denied")
    
    print("\n📝 Scenario 2: High familiarity user (70/100) controls air conditioner")
    result = await system.process_message(
        "打开空调",
        user_id="high_familiarity_user",
        session_id="test_familiarity_high"
    )
    
    print("\nResult:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    device_actions = result.get("device_actions", [])
    if device_actions and device_actions[0].get("success"):
        print("\n✅ PASS: High familiarity user correctly allowed")
    else:
        print("\n❌ FAIL: High familiarity user should be allowed")


async def test_device_control_output():
    """Test device control JSON output format"""
    print("\n" + "="*60)
    print("Test 2: Device Control JSON Output Format")
    print("="*60)
    
    config = load_config()
    system = LangGraphHomeAISystem(config)
    
    print("\n📝 Scenario: Control dimmable light")
    result = await system.process_message(
        "把调光灯调到80%亮度，设置成蓝色",
        user_id="test_user",
        session_id="test_output_format"
    )
    
    print("\nResult:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # Validate output format
    device_actions = result.get("device_actions", [])
    if device_actions:
        action = device_actions[0]
        
        print("\n🔍 Validating output format:")
        
        required_fields = [
            "success", "device_id", "device_name", "command", 
            "new_state", "control_output"
        ]
        
        for field in required_fields:
            if field in action:
                print(f"  ✅ {field}: present")
            else:
                print(f"  ❌ {field}: missing")
        
        # Validate control_output structure
        if "control_output" in action:
            control_output = action["control_output"]
            print("\n🔍 Validating control_output structure:")
            
            required_output_fields = [
                "device_id", "device_name", "device_type", 
                "command", "parameters", "timestamp"
            ]
            
            for field in required_output_fields:
                if field in control_output:
                    print(f"  ✅ {field}: {control_output.get(field)}")
                else:
                    print(f"  ❌ {field}: missing")
            
            # Check timestamp format (ISO8601)
            timestamp = control_output.get("timestamp")
            if timestamp and "T" in timestamp:
                print(f"\n✅ PASS: Timestamp is in ISO8601 format")
            else:
                print(f"\n❌ FAIL: Timestamp format incorrect")
        else:
            print("\n❌ FAIL: control_output missing")


async def test_dimmable_light_control():
    """Test dimmable light with color controls"""
    print("\n" + "="*60)
    print("Test 3: Dimmable Light Control")
    print("="*60)
    
    config = load_config()
    system = LangGraphHomeAISystem(config)
    
    test_cases = [
        ("打开调光灯", "Turn on light"),
        ("把调光灯亮度调到50%", "Set brightness to 50%"),
        ("把调光灯设置成红色", "Set color to red"),
        ("把调光灯设置成蓝色，饱和度80%", "Set blue with 80% saturation"),
    ]
    
    for i, (user_input, description) in enumerate(test_cases, 1):
        print(f"\n📝 Test case {i}: {description}")
        print(f"   User input: {user_input}")
        
        result = await system.process_message(
            user_input,
            user_id="test_user",
            session_id=f"test_dimmable_{i}"
        )
        
        device_actions = result.get("device_actions", [])
        if device_actions and device_actions[0].get("success"):
            action = device_actions[0]
            print(f"   ✅ Command: {action.get('command')}")
            print(f"   ✅ New state: {json.dumps(action.get('new_state'), ensure_ascii=False)}")
        else:
            print(f"   ❌ Failed to execute")


async def test_curtain_control():
    """Test curtain position control"""
    print("\n" + "="*60)
    print("Test 4: Curtain Control")
    print("="*60)
    
    config = load_config()
    system = LangGraphHomeAISystem(config)
    
    test_cases = [
        ("打开窗帘", "Open curtain fully"),
        ("把窗帘开到一半", "Set curtain to 50%"),
        ("关闭窗帘", "Close curtain"),
    ]
    
    for i, (user_input, description) in enumerate(test_cases, 1):
        print(f"\n📝 Test case {i}: {description}")
        print(f"   User input: {user_input}")
        
        result = await system.process_message(
            user_input,
            user_id="test_user",
            session_id=f"test_curtain_{i}"
        )
        
        device_actions = result.get("device_actions", [])
        if device_actions and device_actions[0].get("success"):
            action = device_actions[0]
            print(f"   ✅ Command: {action.get('command')}")
            print(f"   ✅ New state: {json.dumps(action.get('new_state'), ensure_ascii=False)}")
        else:
            print(f"   ❌ Failed to execute")


async def test_langfuse_monitoring():
    """Test Langfuse monitoring coverage"""
    print("\n" + "="*60)
    print("Test 5: Langfuse Monitoring")
    print("="*60)
    
    config = load_config()
    
    # Check if Langfuse is enabled
    if config.langfuse.enabled:
        print("\n✅ Langfuse is enabled")
        print(f"   Host: {config.langfuse.host}")
        print(f"   Public key: {config.langfuse.public_key[:10]}...")
    else:
        print("\n⚠️  Langfuse is disabled in config")
    
    system = LangGraphHomeAISystem(config)
    
    if system.langfuse_enabled:
        print("\n✅ Langfuse client initialized successfully")
        
        print("\n📝 Executing test operation to generate trace...")
        result = await system.process_message(
            "打开调光灯",
            user_id="langfuse_test_user",
            session_id="langfuse_test_session"
        )
        
        print("\n✅ Operation completed")
        print("   Check Langfuse UI for trace: langgraph_workflow")
        print("   Expected spans:")
        print("     - task_plan_node")
        print("     - execute_device_actions_node")
        print("     - device_controller (generation)")
        print("     - generate_audio_node")
        print("     - finalize_response_node")
    else:
        print("\n⚠️  Langfuse integration not available")
        print("   To enable: set langfuse.enabled=true in config")


async def main():
    """Run all tests"""
    print("\n")
    print("*" * 60)
    print("Workflow Device Control Test Suite")
    print("*" * 60)
    
    try:
        # Test 1: Familiarity check
        await test_familiarity_check()
        
        # Test 2: Output format
        await test_device_control_output()
        
        # Test 3: Dimmable light
        await test_dimmable_light_control()
        
        # Test 4: Curtain
        await test_curtain_control()
        
        # Test 5: Langfuse monitoring
        await test_langfuse_monitoring()
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60 + "\n")
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ Test failed with error: {e}")
        print("="*60 + "\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

