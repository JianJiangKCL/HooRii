#!/usr/bin/env python3
"""
Intent Analysis Test
Tests the intent analysis component in isolation
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

async def test_intent_analysis():
    """Test intent analysis component"""
    print("🧪 Testing Intent Analysis Component...\n")
    
    planner = HomeAITaskPlanner()
    
    # Create test conversation context
    conversation_ctx = planner.get_or_create_conversation("test_user", "test_conv")
    conversation_ctx.familiarity_score = 75
    
    test_cases = [
        {
            "input": "空调开着嘛",
            "expected_requires_status": True,
            "expected_device": "air_conditioner"
        },
        {
            "input": "打开客厅灯", 
            "expected_requires_hardware": True,
            "expected_device": "living_room_lights",
            "expected_action": "turn_on"
        },
        {
            "input": "关闭电视",
            "expected_requires_hardware": True,
            "expected_device": "tv",
            "expected_action": "turn_off"
        },
        {
            "input": "你好",
            "expected_requires_hardware": False,
            "expected_requires_status": False
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"📝 Test {i}: '{test_case['input']}'")
        
        try:
            result = await planner.analyze_intent(
                test_case['input'], 
                conversation_ctx.familiarity_score, 
                conversation_ctx
            )
            
            # Validate results
            passed = True
            
            if 'expected_requires_status' in test_case:
                if result.get('requires_status') != test_case['expected_requires_status']:
                    print(f"   ❌ requires_status: got {result.get('requires_status')}, expected {test_case['expected_requires_status']}")
                    passed = False
            
            if 'expected_requires_hardware' in test_case:
                if result.get('requires_hardware') != test_case['expected_requires_hardware']:
                    print(f"   ❌ requires_hardware: got {result.get('requires_hardware')}, expected {test_case['expected_requires_hardware']}")
                    passed = False
            
            if 'expected_device' in test_case:
                if result.get('device') != test_case['expected_device']:
                    print(f"   ❌ device: got {result.get('device')}, expected {test_case['expected_device']}")
                    passed = False
            
            if 'expected_action' in test_case:
                if result.get('action') != test_case['expected_action']:
                    print(f"   ❌ action: got {result.get('action')}, expected {test_case['expected_action']}")
                    passed = False
            
            if passed:
                print(f"   ✅ PASSED")
            else:
                print(f"   Full result: {result}")
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        print()
    
    print("✅ Intent Analysis Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_intent_analysis())
