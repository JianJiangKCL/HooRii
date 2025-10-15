#!/usr/bin/env python3
"""
Gemini Setup Verification
Verifies that Gemini configuration is correctly set up
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set minimal environment
os.environ['DATABASE_URL'] = 'sqlite:///./hoorii.db'
os.environ['LANGFUSE_SECRET_KEY'] = ''
os.environ['LANGFUSE_PUBLIC_KEY'] = ''

# Set Gemini configuration
os.environ['LLM_PROVIDER'] = 'gemini'
os.environ['GEMINI_API_KEY'] = 'AIzaSyB2Z9cNLVY8lpz9WjrQ6pZEtFj56zajDJc'
os.environ['GEMINI_MODEL'] = 'gemini-2.5-flash'
os.environ['GEMINI_BASE_URL'] = 'https://generativelanguage.googleapis.com/v1beta/'


def main():
    print("=" * 70)
    print("🔍 Gemini Setup Verification")
    print("=" * 70)
    
    # Check 1: Configuration loading
    print("\n1️⃣  Checking configuration...")
    try:
        from src.utils.config import load_config
        config = load_config()
        print(f"   ✅ Configuration loaded successfully")
        print(f"   📋 LLM Provider: {config.llm.provider}")
        print(f"   📋 Gemini Model: {config.gemini.model}")
        print(f"   📋 API Key: {config.gemini.api_key[:20]}..." if len(config.gemini.api_key) > 20 else config.gemini.api_key)
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return 1
    
    # Check 2: Package installation
    print("\n2️⃣  Checking package installation...")
    try:
        import google.generativeai as genai
        print(f"   ✅ google-generativeai is installed")
        print(f"   📦 Version: {genai.__version__}")
    except ImportError as e:
        print(f"   ❌ google-generativeai is not installed")
        print(f"   💡 Install with: pip install google-generativeai>=0.3.0")
        return 1
    
    # Check 3: LLM Client creation
    print("\n3️⃣  Checking LLM client creation...")
    try:
        from src.utils.llm_client import create_llm_client
        llm_client = create_llm_client(config)
        print(f"   ✅ LLM Client created: {type(llm_client).__name__}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return 1
    
    # Check 4: API connectivity
    print("\n4️⃣  Checking API connectivity...")
    print("   ⚠️  Note: This may fail due to regional restrictions")
    try:
        # Configure Gemini
        genai.configure(api_key=config.gemini.api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Try a simple request
        response = model.generate_content("Say 'Hello' in one word")
        print(f"   ✅ API is accessible")
        print(f"   🤖 Test response: {response.text[:50]}")
    except Exception as e:
        error_msg = str(e)
        if "location is not supported" in error_msg.lower():
            print(f"   ❌ Regional Restriction Detected")
            print(f"   ")
            print(f"   The Gemini API is not available in your region.")
            print(f"   ")
            print(f"   💡 Solutions:")
            print(f"      1. Use a VPN to connect from a supported region (US, EU, etc.)")
            print(f"      2. Switch to Anthropic Claude: LLM_PROVIDER=anthropic")
            print(f"      3. Contact Google Cloud support for region access")
            print(f"      4. Try creating a new API key from Google AI Studio")
            return 2
        else:
            print(f"   ❌ API Error: {error_msg[:100]}")
            return 1
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ Setup Verification Complete")
    print("=" * 70)
    print("\n📝 Your Gemini integration is configured correctly!")
    print("\n🚀 Next Steps:")
    print("   1. Create or update your .env file with Gemini credentials")
    print("   2. Run the full integration test: python debug/test_gemini_integration.py")
    print("   3. Test with actual components: python debug/intent_analysis_test.py")
    print("\n📚 For more information, see: docs/GEMINI_INTEGRATION.md")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

