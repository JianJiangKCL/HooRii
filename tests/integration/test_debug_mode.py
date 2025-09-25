#!/usr/bin/env python3
"""
Test Debug Mode
Compare normal vs debug mode output
"""
import subprocess
import sys
import os
import asyncio

def test_mode(debug=False):
    """Test application in normal or debug mode"""
    mode_name = "DEBUG" if debug else "NORMAL"
    print(f"\n{'='*50}")
    print(f"🧪 Testing {mode_name} Mode")
    print(f"{'='*50}")
    
    # Prepare command
    cmd = [sys.executable, "main.py"]
    if debug:
        cmd.append("--debug")
    
    # Test input
    test_input = "你好\nexit\n"
    
    try:
        result = subprocess.run(
            cmd,
            input=test_input,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
            
        return True
        
    except subprocess.TimeoutExpired:
        print(f"⏰ {mode_name} mode test timed out")
        return False
    except Exception as e:
        print(f"❌ {mode_name} mode test failed: {e}")
        return False

def main():
    print("🚀 Testing Debug Mode Implementation")
    
    # Test normal mode (clean)
    test_mode(debug=False)
    
    # Test debug mode (verbose)
    test_mode(debug=True)
    
    print(f"\n{'='*50}")
    print("📋 Usage Examples:")
    print("  Normal mode (clean):  python main.py")
    print("  Debug mode (verbose): python main.py --debug")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()