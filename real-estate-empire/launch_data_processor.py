#!/usr/bin/env python3
"""
Launch script for the AI Data Processor web interface
"""

import os
import sys
import webbrowser
import subprocess
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import pandas
        import google.generativeai
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install required packages:")
        print("pip install fastapi uvicorn pandas google-generativeai python-multipart")
        return False

def check_gemini_api_key():
    """Check if Gemini API key is configured"""
    if os.getenv('GEMINI_API_KEY'):
        print("✅ Gemini API key is configured")
        return True
    else:
        print("⚠️  Gemini API key not found in environment variables")
        print("Please set GEMINI_API_KEY environment variable")
        print("You can get an API key from: https://makersuite.google.com/app/apikey")
        return False

def start_api_server():
    """Start the FastAPI server"""
    print("🚀 Starting API server...")
    
    # Change to the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    try:
        # Start uvicorn server
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "app.api.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ]
        
        print("📡 API server starting at http://localhost:8000")
        print("📚 API docs available at http://localhost:8000/docs")
        
        # Start server in background
        process = subprocess.Popen(cmd)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        return process
        
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return None

def open_web_interface():
    """Open the web interface in browser"""
    print("🌐 Opening web interface...")
    
    # Path to the HTML file
    html_file = Path(__file__).parent / "app" / "frontend" / "data-processor.html"
    
    if html_file.exists():
        # Open in default browser
        webbrowser.open(f"file://{html_file.absolute()}")
        print(f"✅ Web interface opened: {html_file}")
    else:
        print(f"❌ Web interface not found: {html_file}")
        print("Please ensure the frontend files are in the correct location")

def show_usage_instructions():
    """Show usage instructions"""
    print("\n" + "="*60)
    print("🎯 AI Data Processor - Usage Instructions")
    print("="*60)
    print()
    print("1. 📤 Upload ZIP Files:")
    print("   • Select a ZIP file containing your data files")
    print("   • Supported formats: CSV, Excel, JSON, TSV, TXT")
    print()
    print("2. 🤖 Choose Processing Mode:")
    print("   • Auto Format: Let AI determine the best ML format")
    print("   • Custom Schema: Provide your own target schema")
    print()
    print("3. 🧠 AI Processing:")
    print("   • Gemini AI analyzes your data structure")
    print("   • Suggests optimal ML preprocessing steps")
    print("   • Provides data quality insights")
    print()
    print("4. 📊 Review Results:")
    print("   • Check processing summary")
    print("   • View data preview")
    print("   • Read AI recommendations")
    print()
    print("5. 💾 Export Data:")
    print("   • Download processed data as CSV, JSON, or Excel")
    print("   • Ready for ML model training")
    print()
    print("🔗 API Endpoints:")
    print("   • POST /api/v1/data-processor/upload-zip")
    print("   • POST /api/v1/data-processor/auto-format")
    print("   • POST /api/v1/data-processor/export/{format}")
    print()

def main():
    """Main launcher function"""
    print("🏗️  AI Data Processor Launcher")
    print("=" * 50)
    print("Intelligent data preprocessing with Gemini AI")
    print()
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check API key
    api_key_ok = check_gemini_api_key()
    
    # Start API server
    server_process = start_api_server()
    
    if server_process:
        try:
            # Open web interface
            time.sleep(2)  # Give server more time to start
            open_web_interface()
            
            # Show instructions
            show_usage_instructions()
            
            if not api_key_ok:
                print("⚠️  Note: Some AI features may not work without Gemini API key")
            
            print("\n🎮 Controls:")
            print("   • Press Ctrl+C to stop the server")
            print("   • Server logs will appear below")
            print("\n" + "="*50)
            
            # Wait for server process
            server_process.wait()
            
        except KeyboardInterrupt:
            print("\n🛑 Shutting down server...")
            server_process.terminate()
            server_process.wait()
            print("✅ Server stopped")
    
    else:
        print("❌ Could not start API server")
        print("\nManual startup:")
        print("1. cd to project directory")
        print("2. Run: uvicorn app.api.main:app --reload")
        print("3. Open: app/frontend/data-processor.html")

if __name__ == "__main__":
    main()