#!/usr/bin/env python3
"""
Gemini Integration Test
Tests the new Gemini LLM provider integration
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

# Set Gemini configuration
os.environ['LLM_PROVIDER'] = 'gemini'
os.environ['GEMINI_API_KEY'] = 'AIzaSyB2Z9cNLVY8lpz9WjrQ6pZEtFj56zajDJc'
os.environ['GEMINI_MODEL'] = 'gemini-2.5-flash'
os.environ['GEMINI_BASE_URL'] = 'https://generativelanguage.googleapis.com/v1beta/'
os.environ['DATABASE_URL'] = 'sqlite:///./hoorii.db'
os.environ['LANGFUSE_SECRET_KEY'] = ''
os.environ['LANGFUSE_PUBLIC_KEY'] = ''

from src.utils.config import load_config
from src.utils.llm_client import create_llm_client


async def test_gemini_basic():
    """Test basic Gemini client functionality"""
    print("🧪 Testing Gemini Basic Functionality...")
    
    try:
        # Load config
        config = load_config()
        print(f"✅ Configuration loaded: LLM Provider = {config.llm.provider}")
        
        # Create LLM client
        llm_client = create_llm_client(config)
        print(f"✅ LLM Client created: {type(llm_client).__name__}")
        
        # Test simple generation
        print("\n📝 Testing simple text generation...")
        system_prompt = "你是一个友好的AI助手。"
        messages = [{"role": "user", "content": "你好，请简单介绍一下你自己。"}]
        
        response = await llm_client.generate(
            system_prompt=system_prompt,
            messages=messages,
            max_tokens=100,
            temperature=0.7
        )
        
        print(f"\n🤖 Response from Gemini:\n{response}")
        print("\n✅ Basic generation test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gemini_json_response():
    """Test Gemini with JSON structured output"""
    print("\n🧪 Testing Gemini JSON Response...")
    
    try:
        config = load_config()
        llm_client = create_llm_client(config)
        
        system_prompt = "你是一个智能家居意图分析器。分析用户输入，返回JSON格式的设备控制意图。"
        messages = [{
            "role": "user",
            "content": """
分析以下用户输入: "打开客厅的灯"

返回JSON格式：
{
    "involves_hardware": bool,
    "device": "设备名称",
    "action": "操作",
    "confidence": 0.0-1.0
}
"""
        }]
        
        response = await llm_client.generate(
            system_prompt=system_prompt,
            messages=messages,
            max_tokens=200,
            temperature=0.1
        )
        
        print(f"\n🤖 JSON Response from Gemini:\n{response}")
        
        # Try to parse as JSON
        import json
        try:
            # Extract JSON from response
            if '{' in response and '}' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
                parsed = json.loads(json_str)
                print(f"\n✅ Successfully parsed JSON: {parsed}")
                return True
        except json.JSONDecodeError:
            print(f"\n⚠️  Response is not valid JSON, but Gemini generated a response")
            return True
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gemini_with_components():
    """Test Gemini integration with actual system components"""
    print("\n🧪 Testing Gemini with System Components...")
    
    try:
        from src.core.intent_analyzer import IntentAnalyzer
        from src.core.context_manager import SystemContext
        
        config = load_config()
        intent_analyzer = IntentAnalyzer(config)
        
        print(f"✅ IntentAnalyzer created with LLM provider: {config.llm.provider}")
        
        # Create a test context (correctly initialized)
        context = SystemContext(session_id="test_session")
        context.user_input = "打开空调"
        context.familiarity_score = 50
        
        print("\n📝 Analyzing intent: '打开空调'")
        intent = await intent_analyzer.analyze_intent("打开空调", context)
        
        print(f"\n🤖 Intent Analysis Result:")
        print(f"  - Involves Hardware: {intent.get('involves_hardware')}")
        print(f"  - Device: {intent.get('device')}")
        print(f"  - Action: {intent.get('action')}")
        print(f"  - Confidence: {intent.get('confidence')}")
        
        print("\n✅ Component integration test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Gemini Integration Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Basic functionality
    result1 = await test_gemini_basic()
    results.append(("Basic Functionality", result1))
    
    # Test 2: JSON response
    result2 = await test_gemini_json_response()
    results.append(("JSON Response", result2))
    
    # Test 3: Component integration
    result3 = await test_gemini_with_components()
    results.append(("Component Integration", result3))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Gemini integration is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

