#!/usr/bin/env python3
"""
Character System Test
Tests the character (凌波丽) response generation in isolation
"""
import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable OpenTelemetry for tests
os.environ['OTEL_TRACES_EXPORTER'] = 'none'
os.environ['OTEL_METRICS_EXPORTER'] = 'none'
os.environ['OTEL_LOGS_EXPORTER'] = 'none'

from main import HomeAITaskPlanner

async def test_character_system():
    """Test character response generation"""
    print("🧪 Testing Character System (凌波丽)...\n")
    
    planner = HomeAITaskPlanner()
    
    # Create test conversation context
    conversation_ctx = planner.get_or_create_conversation("test_user", "test_conv")
    conversation_ctx.familiarity_score = 75
    conversation_ctx.tone = "casual"
    
    test_scenarios = [
        {
            "message": "你好凌波丽",
            "context": "",
            "prompt_type": "general",
            "description": "Simple greeting"
        },
        {
            "message": "空调状态查询完成",
            "context": "设备状态信息: {'air_conditioner': {'status': 'off', 'temperature': 24}}",
            "prompt_type": "device_control",
            "description": "Device status response"
        },
        {
            "message": "设备控制完成",
            "context": "控制器输出: {'success': True, 'message': '客厅灯已开启'}\n执行结果: {'success': True, 'device_id': 'living_room_lights', 'new_state': {'status': 'on', 'brightness': 80}}",
            "prompt_type": "device_control",
            "description": "Device control confirmation"
        },
        {
            "message": "你为什么要帮助我？",
            "context": "",
            "prompt_type": "general",
            "description": "Personal question"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"📝 Test {i}: {scenario['description']}")
        print(f"   Message: '{scenario['message']}'")
        
        try:
            response = await planner.call_character(
                message=scenario['message'],
                tone=conversation_ctx.tone,
                context=scenario['context'],
                conversation_context=conversation_ctx,
                prompt_type=scenario['prompt_type']
            )
            
            print(f"   ✅ Response: {response}")
            
            # Check for character traits
            character_traits = {
                "short_sentences": len(response.split('。')) <= 3,
                "uses_ellipsis": "......" in response or "..." in response,
                "not_overly_emotional": "！！" not in response and "!!!" not in response,
                "chinese_response": any('\u4e00' <= char <= '\u9fff' for char in response)
            }
            
            trait_count = sum(character_traits.values())
            print(f"   Character traits: {trait_count}/4 ({'✅' if trait_count >= 2 else '⚠️'})")
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        print()
    
    print("✅ Character System Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_character_system())
