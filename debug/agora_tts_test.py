#!/usr/bin/env python3
"""
Agora TTS Service Test
Tests the AgoraTTSService functionality including configuration, authentication, and TTS synthesis
"""
import sys
import os
import asyncio
import logging
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable OpenTelemetry for tests
os.environ['OTEL_TRACES_EXPORTER'] = 'none'
os.environ['OTEL_METRICS_EXPORTER'] = 'none'
os.environ['OTEL_LOGS_EXPORTER'] = 'none'

from src.utils.config import load_config
from src.services.agora_tts_service import AgoraTTSService


def setup_logging():
    """Setup logging for the test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def test_agora_tts_configuration():
    """Test Agora TTS service configuration"""
    print("\n=== Testing Agora TTS Configuration ===")
    
    try:
        config = load_config()
        tts_service = AgoraTTSService(config)
        
        print(f"✅ Service initialized successfully")
        print(f"   - Enabled: {tts_service.enabled}")
        print(f"   - App Key: {'***' + tts_service.app_key[-4:] if tts_service.app_key else 'Not configured'}")
        print(f"   - App Secret: {'***' + tts_service.app_secret[-4:] if tts_service.app_secret else 'Not configured'}")
        print(f"   - Project ID: {tts_service.project_id}")
        print(f"   - Base URL: {tts_service.base_url}")
        
        # Check configuration validity
        if not tts_service.enabled:
            print("⚠️  Agora TTS is disabled in configuration")
            return False
            
        if not tts_service.app_key or not tts_service.app_secret:
            print("❌ Agora credentials not configured")
            return False
            
        if not tts_service.project_id or tts_service.project_id in {"", "default", "your_project_id"}:
            print("❌ Agora project ID not configured correctly")
            return False
            
        print("✅ Configuration is valid")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


async def test_agora_tts_signature_generation():
    """Test Agora API signature generation"""
    print("\n=== Testing Signature Generation ===")
    
    try:
        config = load_config()
        tts_service = AgoraTTSService(config)
        
        if not tts_service.app_key or not tts_service.app_secret:
            print("⚠️  Skipping signature test - credentials not configured")
            return True
            
        # Test signature generation
        method = "POST"
        url = "/v1/projects/test/tts-tasks"
        body = '{"text": "Hello world", "voice": "zh-CN-XiaoxiaoNeural"}'
        
        headers = tts_service._generate_signature(method, url, body)
        
        print("✅ Signature generated successfully")
        print(f"   - X-Agora-Key: {headers.get('X-Agora-Key', 'Missing')}")
        print(f"   - X-Agora-Timestamp: {headers.get('X-Agora-Timestamp', 'Missing')}")
        print(f"   - X-Agora-Nonce: {headers.get('X-Agora-Nonce', 'Missing')}")
        print(f"   - X-Agora-Signature: {headers.get('X-Agora-Signature', 'Missing')[:20]}...")
        print(f"   - Content-Type: {headers.get('Content-Type', 'Missing')}")
        
        # Verify required headers are present
        required_headers = ['X-Agora-Key', 'X-Agora-Timestamp', 'X-Agora-Nonce', 'X-Agora-Signature']
        for header in required_headers:
            if not headers.get(header):
                print(f"❌ Missing required header: {header}")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Signature generation test failed: {e}")
        return False


async def test_agora_tts_synthesis():
    """Test Agora TTS synthesis"""
    print("\n=== Testing TTS Synthesis ===")
    
    try:
        config = load_config()
        tts_service = AgoraTTSService(config)
        
        if not tts_service.enabled:
            print("⚠️  Skipping synthesis test - Agora TTS is disabled")
            return True
            
        if not tts_service.app_key or not tts_service.app_secret:
            print("⚠️  Skipping synthesis test - credentials not configured")
            return True
            
        if not tts_service.project_id or tts_service.project_id in {"", "default", "your_project_id"}:
            print("⚠️  Skipping synthesis test - project ID not configured")
            return True
        
        # Test text
        test_text = "你好，我是凌波丽。这是一个测试语音合成的句子。"
        
        print(f"🎵 Testing synthesis with text: '{test_text}'")
        print("   This may take a few seconds...")
        
        # Test synthesize_speech method (returns bytes)
        audio_data = await tts_service.synthesize_speech(
            text=test_text,
            voice="zh-CN-XiaoxiaoNeural",
            format="mp3"
        )
        
        if audio_data:
            print(f"✅ Synthesis successful!")
            print(f"   - Audio data size: {len(audio_data)} bytes")
            print(f"   - Audio type: {type(audio_data)}")
            
            # Test text_to_speech method (returns base64 string)
            base64_audio = await tts_service.text_to_speech(test_text)
            if base64_audio:
                print(f"✅ Base64 encoding successful!")
                print(f"   - Base64 length: {len(base64_audio)} characters")
                print(f"   - Base64 prefix: {base64_audio[:50]}...")
            else:
                print("❌ Base64 encoding failed")
                return False
                
        else:
            print("❌ Synthesis failed - no audio data returned")
            print("   This could be due to:")
            print("   - Network connectivity issues")
            print("   - Invalid credentials")
            print("   - API quota exceeded")
            print("   - Service temporarily unavailable")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Synthesis test failed: {e}")
        return False


async def test_agora_tts_save_file():
    """Test saving TTS audio to file"""
    print("\n=== Testing Audio File Save ===")
    
    try:
        config = load_config()
        tts_service = AgoraTTSService(config)
        
        if not tts_service.enabled or not tts_service.app_key or not tts_service.app_secret:
            print("⚠️  Skipping file save test - service not properly configured")
            return True
            
        test_text = "这是一个保存音频文件的测试。"
        output_file = "/tmp/agora_tts_test.mp3"
        
        print(f"💾 Testing file save with text: '{test_text}'")
        print(f"   Output file: {output_file}")
        
        success = await tts_service.save_audio_file(test_text, output_file)
        
        if success:
            print("✅ Audio file saved successfully!")
            
            # Check if file exists and has content
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"   - File size: {file_size} bytes")
                
                # Clean up test file
                os.remove(output_file)
                print("   - Test file cleaned up")
            else:
                print("❌ File was not created")
                return False
        else:
            print("❌ Audio file save failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ File save test failed: {e}")
        return False


async def test_agora_tts_error_handling():
    """Test error handling scenarios"""
    print("\n=== Testing Error Handling ===")
    
    try:
        # Test with disabled service
        config = load_config()
        
        # Create a service with disabled configuration
        disabled_service = AgoraTTSService(config)
        disabled_service.enabled = False
        
        result = await disabled_service.text_to_speech("Test text")
        if result is None:
            print("✅ Disabled service correctly returns None")
        else:
            print("❌ Disabled service should return None")
            return False
        
        # Test with missing credentials
        no_creds_service = AgoraTTSService(config)
        no_creds_service.app_key = None
        no_creds_service.app_secret = None
        
        result = await no_creds_service.text_to_speech("Test text")
        if result is None:
            print("✅ Service without credentials correctly returns None")
        else:
            print("❌ Service without credentials should return None")
            return False
            
        # Test with invalid project ID
        invalid_project_service = AgoraTTSService(config)
        invalid_project_service.project_id = "default"
        
        result = await invalid_project_service.synthesize_speech("Test text")
        if result is None:
            print("✅ Service with invalid project ID correctly returns None")
        else:
            print("❌ Service with invalid project ID should return None")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


async def main():
    """Run all Agora TTS tests"""
    setup_logging()
    
    print("🎤 Agora TTS Service Test Suite")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_agora_tts_configuration),
        ("Signature Generation", test_agora_tts_signature_generation),
        ("TTS Synthesis", test_agora_tts_synthesis),
        ("File Save", test_agora_tts_save_file),
        ("Error Handling", test_agora_tts_error_handling),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check configuration and network connectivity.")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
