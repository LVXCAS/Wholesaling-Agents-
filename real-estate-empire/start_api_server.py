#!/usr/bin/env python3
"""
Simple API server startup script for Data Processor
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_port_available(port=8000):
    """Check if port is available"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True
        except OSError:
            return False

def find_available_port(start_port=8000):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + 10):
        if check_port_available(port):
            return port
    return None

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting Real Estate Empire API Server")
    print("=" * 50)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Check if we're in the right directory
    if not (project_dir / "app" / "api" / "main.py").exists():
        print("❌ Error: Cannot find app/api/main.py")
        print(f"Current directory: {project_dir}")
        print("Please run this script from the real-estate-empire directory")
        return False
    
    # Find available port
    port = find_available_port(8000)
    if not port:
        print("❌ Error: No available ports found (8000-8009)")
        return False
    
    if port != 8000:
        print(f"⚠️  Port 8000 is busy, using port {port}")
    
    # Set environment variables
    os.environ.setdefault('PYTHONPATH', str(project_dir))
    
    # Check for Gemini API key
    if not os.getenv('GEMINI_API_KEY'):
        print("⚠️  Warning: GEMINI_API_KEY not set")
        print("   Some AI features may not work")
        print("   Get your key from: https://makersuite.google.com/app/apikey")
        print()
    
    # Start server
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.api.main:app",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--reload"
    ]
    
    print(f"🌐 Starting server on http://localhost:{port}")
    print(f"📚 API docs will be at http://localhost:{port}/docs")
    print(f"🤖 Data Processor at http://localhost:{port}/api/v1/data-processor/")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Start the server
        process = subprocess.run(cmd)
        return True
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return True
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

def main():
    """Main function"""
    try:
        success = start_server()
        if not success:
            print("\n💡 Troubleshooting tips:")
            print("1. Make sure you're in the real-estate-empire directory")
            print("2. Install dependencies: pip install fastapi uvicorn")
            print("3. Check if another server is running on port 8000")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()