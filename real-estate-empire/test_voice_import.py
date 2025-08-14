#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

try:
    print("Testing voice service import...")
    from app.services.voice_service import VoiceService
    print("VoiceService imported successfully!")
except ImportError as e:
    print(f"Import error: {e}")
    
    # Try importing the module directly
    try:
        import app.services.voice_service as vs
        print("Module imported successfully")
        print("Available classes:", [x for x in dir(vs) if x[0].isupper()])
    except Exception as e2:
        print(f"Module import error: {e2}")