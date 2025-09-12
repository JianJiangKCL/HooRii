#!/usr/bin/env python3
"""
Test Langfuse connectivity and configuration
"""
import os
import requests
from config import load_config

def test_langfuse_connection():
    """Test if Langfuse is properly configured and accessible"""
    print("🔍 Testing Langfuse Connection")
    print("=" * 50)
    
    # Load config
    config = load_config()
    
    # Check configuration
    print(f"📋 Configuration:")
    print(f"   Enabled: {config.langfuse.enabled}")
    print(f"   Host: {config.langfuse.host}")
    print(f"   Public Key: {config.langfuse.public_key[:10]}..." if config.langfuse.public_key else "   Public Key: Not set")
    print(f"   Secret Key: {'✅ Set' if config.langfuse.secret_key else '❌ Not set'}")
    
    if not config.langfuse.enabled:
        print("\n❌ Langfuse is disabled in config")
        return False
    
    if not config.langfuse.secret_key or not config.langfuse.public_key:
        print("\n❌ Langfuse keys not configured")
        return False
    
    # Test import
    print(f"\n📦 Testing imports:")
    try:
        from langfuse import Langfuse, observe, get_client
        print("   ✅ All Langfuse imports successful")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        print("   💡 Install with: pip install langfuse")
        return False
    
    # Test connection
    print(f"\n🌐 Testing connection:")
    try:
        # Set environment variables first
        import os
        os.environ['LANGFUSE_SECRET_KEY'] = config.langfuse.secret_key
        os.environ['LANGFUSE_PUBLIC_KEY'] = config.langfuse.public_key
        os.environ['LANGFUSE_HOST'] = config.langfuse.host
        
        langfuse = Langfuse(
            secret_key=config.langfuse.secret_key,
            public_key=config.langfuse.public_key,
            host=config.langfuse.host
        )
        
        # Check authentication
        auth_result = langfuse.auth_check()
        print(f"   🔐 Authentication: {'✅ Valid' if auth_result else '❌ Failed'}")
        
        # Try to create a test span with session
        with langfuse.start_as_current_span(
            name="connection_test",
            metadata={"test": "connection", "session_id": "test_session_conn"}
        ) as span:
            span.update(
                metadata={"status": "success"}
            )
        
        # Flush to ensure it's sent
        langfuse.flush()
        
        print("   ✅ Connection successful!")
        print(f"   📊 Test span created successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        
        # Test basic HTTP connectivity
        try:
            response = requests.get(config.langfuse.host, timeout=10)
            print(f"   🌐 Host reachable (status: {response.status_code})")
        except Exception as http_e:
            print(f"   🌐 Host unreachable: {http_e}")
        
        return False

def test_environment_variables():
    """Check if environment variables are set"""
    print(f"\n🔧 Environment Variables:")
    env_vars = [
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_PUBLIC_KEY", 
        "LANGFUSE_HOST"
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            display_value = f"{value[:10]}..." if len(value) > 10 else value
            print(f"   {var}: {display_value}")
        else:
            print(f"   {var}: ❌ Not set")

if __name__ == "__main__":
    test_environment_variables()
    success = test_langfuse_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Langfuse is properly configured and connected!")
        print("💡 You should see traces in your Langfuse dashboard")
    else:
        print("❌ Langfuse connection failed")
        print("💡 Check your configuration in config.toml")
        print("💡 Ensure Langfuse service is running")
    print("=" * 50)