#!/usr/bin/env python3
"""
API Server startup script for Smart Home AI Assistant
"""
import os
import sys
from pathlib import Path

def main():
    """Start the API server"""
    print("🚀 启动智能家居AI助手API服务器...")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env 文件不存在")
        print("请先运行: python setup_env.py")
        print("然后编辑 .env 文件，填入你的API密钥")
        sys.exit(1)
    
    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Check dependencies
    try:
        import uvicorn
        import fastapi
        from src.utils.config import load_config
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请安装依赖: pip install -r requirements.txt")
        sys.exit(1)
    
    # Test configuration
    try:
        config = load_config()
        config.print_config()
    except Exception as e:
        print(f"❌ 配置错误: {e}")
        sys.exit(1)
    
    # Start server
    print("\n🌐 启动API服务器...")
    print("API文档将在 http://localhost:10030/docs 可用")
    print("按 Ctrl+C 停止服务器")
    
    # Use configured API port if available (fallback to 10030)
    try:
        port = getattr(config.system, 'api_port', 10030)
    except Exception:
        port = 10030
    os.system(f"uvicorn src.api.server:app --host 0.0.0.0 --port {port} --reload")

if __name__ == "__main__":
    main()



