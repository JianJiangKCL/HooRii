#!/usr/bin/env python3
"""
LLM Provider Switcher
Quickly switch between Gemini and Anthropic based on availability
"""
import os
import sys

def check_gemini_availability():
    """Check if Gemini API is accessible"""
    try:
        import google.generativeai as genai
        
        # Try to configure and test
        api_key = os.getenv("GEMINI_API_KEY", "AIzaSyB2Z9cNLVY8lpz9WjrQ6pZEtFj56zajDJc")
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Hi")
        
        return True, "Gemini API is accessible"
    except Exception as e:
        error_msg = str(e)
        if "location is not supported" in error_msg.lower():
            return False, "Regional restriction (VPN required)"
        return False, f"Error: {error_msg[:100]}"


def update_env_file(provider: str):
    """Update .env file with new provider"""
    env_path = "/data/jj/proj/hoorii/.env"
    
    try:
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Update LLM_PROVIDER line
        with open(env_path, 'w') as f:
            for line in lines:
                if line.startswith('LLM_PROVIDER='):
                    f.write(f'LLM_PROVIDER={provider}\n')
                else:
                    f.write(line)
        
        print(f"✅ Updated .env: LLM_PROVIDER={provider}")
        return True
    except Exception as e:
        print(f"❌ Failed to update .env: {e}")
        return False


def main():
    print("=" * 70)
    print("🔄 LLM Provider Switcher")
    print("=" * 70)
    
    # Check Gemini availability
    print("\n1️⃣  Checking Gemini availability...")
    gemini_ok, gemini_msg = check_gemini_availability()
    
    if gemini_ok:
        print(f"   ✅ {gemini_msg}")
    else:
        print(f"   ❌ {gemini_msg}")
    
    # Decide which provider to use
    print("\n2️⃣  Determining best provider...")
    
    if gemini_ok:
        print("   ✅ Using Gemini (fast & cheap)")
        provider = "gemini"
    else:
        print("   ⚠️  Gemini unavailable")
        print("   📋 Checking for Anthropic key...")
        
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key and len(anthropic_key) > 10:
            print("   ✅ Switching to Anthropic Claude")
            provider = "anthropic"
        else:
            print("   ❌ No Anthropic key found")
            print("\n" + "=" * 70)
            print("⚠️  SOLUTION REQUIRED")
            print("=" * 70)
            print("\n📝 Options:")
            print("   1. Connect VPN to supported region and run again")
            print("   2. Set ANTHROPIC_API_KEY in .env file")
            print("   3. Use: export LLM_PROVIDER=anthropic")
            return 1
    
    # Update .env file
    print("\n3️⃣  Updating configuration...")
    if update_env_file(provider):
        print("\n" + "=" * 70)
        print(f"✅ SUCCESS - Using {provider.upper()}")
        print("=" * 70)
        print(f"\n🚀 You can now run: python scripts/run_app.py")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())

