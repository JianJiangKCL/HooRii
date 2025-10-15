#!/usr/bin/env python3
"""
Device Controller Real Devices Test
Tests device controller with real device configurations (dimmable light and curtain)
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

from src.utils.config import Config
from src.core.device_controller import DeviceController
from src.core.context_manager import SystemContext


async def test_dimmable_light():
    """Test dimmable light with color controls"""
    print("\n" + "="*60)
    print("Testing Dimmable Light (演示调光灯)")
    print("="*60)
    
    config = Config()
    controller = DeviceController(config)
    
    # Create a test context
    context = SystemContext(
        session_id="test_session",
        user_id="test_user",
        user_input="",
        familiarity_score=60,
        conversation_tone="polite"
    )
    
    # Test 1: Turn on the light
    print("\n1️⃣  Test: Turn on light")
    intent = {
        "intent_type": "device_control",
        "involves_hardware": True,
        "entities": {"device": "演示调光灯"}
    }
    context.user_input = "打开调光灯"
    
    result = await controller.process_device_intent(intent, context)
    print(f"Result: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # Test 2: Set brightness
    print("\n2️⃣  Test: Set brightness to 50%")
    intent = {
        "intent_type": "device_control",
        "involves_hardware": True,
        "entities": {"device": "演示调光灯", "brightness": 50}
    }
    context.user_input = "把调光灯亮度调到50%"
    
    result = await controller.process_device_intent(intent, context)
    print(f"Result: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # Test 3: Set color to red (hue = 0)
    print("\n3️⃣  Test: Set color to red")
    intent = {
        "intent_type": "device_control",
        "involves_hardware": True,
        "entities": {"device": "演示调光灯", "color": "红色"}
    }
    context.user_input = "把调光灯设置成红色"
    
    result = await controller.process_device_intent(intent, context)
    print(f"Result: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # Test 4: Set color to blue (hue = 240)
    print("\n4️⃣  Test: Set color to blue with saturation 80%")
    intent = {
        "intent_type": "device_control",
        "involves_hardware": True,
        "entities": {"device": "演示调光灯", "color": "蓝色", "saturation": 80}
    }
    context.user_input = "把调光灯设置成蓝色，饱和度80%"
    
    result = await controller.process_device_intent(intent, context)
    print(f"Result: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # Test 5: Query light status
    print("\n5️⃣  Test: Query light status")
    intent = {
        "intent_type": "device_query",
        "involves_hardware": False,
        "entities": {"device": "演示调光灯"}
    }
    context.user_input = "调光灯现在是什么状态？"
    
    result = await controller.process_device_intent(intent, context)
    print(f"Result: {json.dumps(result, ensure_ascii=False, indent=2)}")


async def test_curtain():
    """Test curtain with position controls"""
    print("\n" + "="*60)
    print("Testing Curtain (演示窗帘)")
    print("="*60)
    
    config = Config()
    controller = DeviceController(config)
    
    # Create a test context
    context = SystemContext(
        session_id="test_session",
        user_id="test_user",
        user_input="",
        familiarity_score=60,
        conversation_tone="polite"
    )
    
    # Test 1: Open curtain completely
    print("\n1️⃣  Test: Open curtain completely")
    intent = {
        "intent_type": "device_control",
        "involves_hardware": True,
        "entities": {"device": "演示窗帘", "action": "open"}
    }
    context.user_input = "打开窗帘"
    
    result = await controller.process_device_intent(intent, context)
    print(f"Result: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # Test 2: Set curtain to 50% position
    print("\n2️⃣  Test: Set curtain to 50% position")
    intent = {
        "intent_type": "device_control",
        "involves_hardware": True,
        "entities": {"device": "演示窗帘", "position": 50}
    }
    context.user_input = "把窗帘开到一半"
    
    result = await controller.process_device_intent(intent, context)
    print(f"Result: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # Test 3: Close curtain completely
    print("\n3️⃣  Test: Close curtain completely")
    intent = {
        "intent_type": "device_control",
        "involves_hardware": True,
        "entities": {"device": "演示窗帘", "action": "close"}
    }
    context.user_input = "关闭窗帘"
    
    result = await controller.process_device_intent(intent, context)
    print(f"Result: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # Test 4: Query curtain status
    print("\n4️⃣  Test: Query curtain status")
    intent = {
        "intent_type": "device_query",
        "involves_hardware": False,
        "entities": {"device": "演示窗帘"}
    }
    context.user_input = "窗帘现在是什么状态？"
    
    result = await controller.process_device_intent(intent, context)
    print(f"Result: {json.dumps(result, ensure_ascii=False, indent=2)}")


async def test_color_conversion():
    """Test color name to hue conversion"""
    print("\n" + "="*60)
    print("Testing Color Name Conversion")
    print("="*60)
    
    config = Config()
    controller = DeviceController(config)
    
    test_hues = [0, 30, 60, 120, 180, 240, 270, 300, 330]
    
    for hue in test_hues:
        color_name = controller._get_color_name_from_hue(hue)
        print(f"Hue {hue}° → {color_name}")


async def main():
    """Run all tests"""
    print("\n")
    print("*" * 60)
    print("Device Controller Real Devices Test Suite")
    print("Testing with real device configurations:")
    print("  - 演示调光灯 (Dimmable Light)")
    print("  - 演示窗帘 (Curtain)")
    print("*" * 60)
    
    try:
        # Test dimmable light
        await test_dimmable_light()
        
        # Test curtain
        await test_curtain()
        
        # Test color conversion
        await test_color_conversion()
        
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

