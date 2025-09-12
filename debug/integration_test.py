#!/usr/bin/env python3
"""
Integration Test
Tests the full system flow: Intent → Controller → Character
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

async def test_full_integration():
    """Test complete system integration"""
    print("🧪 Testing Full System Integration...\n")
    
    planner = HomeAITaskPlanner()
    
    test_flows = [
        {
            "input": "空调开着嘛",
            "expected_flow": "Intent Analysis → Device Status Query → Character Response",
            "description": "Status query flow"
        },
        {
            "input": "打开客厅灯",
            "expected_flow": "Intent Analysis → Device Controller → Device Execution → Character Response",
            "description": "Device control flow"
        },
        {
            "input": "你好",
            "expected_flow": "Intent Analysis → Character Response (direct)",
            "description": "Conversational flow"
        }
    ]
    
    for i, test_flow in enumerate(test_flows, 1):
        print(f"📝 Integration Test {i}: {test_flow['description']}")
        print(f"   Input: '{test_flow['input']}'")
        print(f"   Expected Flow: {test_flow['expected_flow']}")
        
        try:
            # Process the full request
            response, conversation_id = await planner.process_request(
                test_flow['input'], 
                "integration_test_user"
            )
            
            print(f"   ✅ Response: {response}")
            print(f"   Conversation ID: {conversation_id[:8]}...")
            
            # Validate response characteristics
            if response and len(response.strip()) > 0:
                print(f"   ✅ Valid response generated")
            else:
                print(f"   ❌ Empty or invalid response")
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("✅ Integration Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_full_integration())
