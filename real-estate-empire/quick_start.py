#!/usr/bin/env python3
"""
Quick start script for Data Processor
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def main():
    print("🚀 Quick Start - AI Data Processor")
    print("=" * 40)
    
    # Start server
    print("1. Starting API server...")
    try:
        # Start server in background
        server_cmd = [
            sys.executable, "-m", "uvicorn",
            "app.api.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ]
        
        process = subprocess.Popen(server_cmd)
        print("✅ Server starting on http://localhost:8000")
        
        # Wait for server to start
        time.sleep(3)
        
        # Open test page
        print("2. Opening test page...")
        test_page = Path(__file__).parent / "data_processor_standalone.html"
        webbrowser.open(f"file://{test_page.absolute()}")
        
        print("3. Server is running!")
        print("   • Test page opened in browser")
        print("   • API docs: http://localhost:8000/docs")
        print("   • Press Ctrl+C to stop")
        
        # Wait for user to stop
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            process.terminate()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTry manually:")
        print("uvicorn app.api.main:app --reload")

if __name__ == "__main__":
    main()