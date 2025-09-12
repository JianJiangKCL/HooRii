#!/usr/bin/env python3
"""
Test Intent Analyzer - LLM-only approach
Tests the refactored intent analyzer without hardcoded mappings
"""
import asyncio
import sys
import os
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from context_manager import SystemContext
from intent_analyzer import IntentAnalyzer

async def test_llm_intent_analysis():
    """Test LLM-only intent analysis"""
    print("🧪 LLM-Only Intent Analysis Test")
    print("=" * 50)
    
    try:
        # Setup
        config = Config()
        context = SystemContext()
        analyzer = IntentAnalyzer(config)
        
        # Test cases
        test_cases = [
            "开灯",
            "把客厅的灯关掉", 
            "空调太热了",
            "它太亮了",  # Reference test
            "电视的音量调小点",
            "你好，今天天气怎么样？"  # Non-hardware test
        ]
        
        print("Testing various user inputs:")
        print("-" * 30)
        
        for i, user_input in enumerate(test_cases, 1):
            print(f"\n{i}. 输入: '{user_input}'")
            
            # Analyze intent
            result = await analyzer.analyze_intent(user_input, context)
            
            print(f"   设备: {result.get('device')}")
            print(f"   操作: {result.get('action')}")
            print(f"   涉及硬件: {result.get('involves_hardware')}")
            print(f"   置信度: {result.get('confidence'):.2f}")
            print(f"   推理: {result.get('reasoning', 'N/A')[:60]}...")
            
            # Add to context for reference resolution testing
            if result.get('device'):
                context.update_device_state(result['device'], {"last_action": result.get('action')})
        
        print("\n✅ LLM intent analysis test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_fallback_behavior():
    """Test fallback behavior when LLM is unavailable"""
    print("\n🧪 Fallback Behavior Test")
    print("=" * 50)
    
    try:
        # Setup with invalid API key to trigger fallback
        config = Config()
        original_key = config.anthropic.api_key
        config.anthropic.api_key = "invalid-key"
        
        context = SystemContext()
        analyzer = IntentAnalyzer(config)
        
        print("Testing fallback with invalid API key...")
        
        # Test fallback
        result = await analyzer.analyze_intent("开灯", context)
        
        print(f"Fallback result:")
        print(f"   涉及硬件: {result.get('involves_hardware')}")
        print(f"   置信度: {result.get('confidence')}")
        print(f"   推理: {result.get('reasoning')}")
        
        # Should be conservative fallback
        assert result.get('confidence', 0) < 0.5, "Fallback should have low confidence"
        assert result.get('involves_hardware') == False, "Fallback should be conservative about hardware"
        
        print("\n✅ Fallback behavior test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    async def run_tests():
        print(f"🚀 Starting Intent Analyzer LLM-Only Tests")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Setup logging
        logging.basicConfig(level=logging.WARNING)  # Reduce noise
        
        results = []
        
        # Run tests
        results.append(await test_llm_intent_analysis())
        results.append(await test_fallback_behavior())
        
        # Summary
        passed = sum(results)
        total = len(results)
        print(f"\n📊 Test Results: {passed}/{total} passed")
        
        if passed == total:
            print("🎉 All tests passed!")
        else:
            print("⚠️  Some tests failed")
            
        return passed == total
    
    asyncio.run(run_tests())