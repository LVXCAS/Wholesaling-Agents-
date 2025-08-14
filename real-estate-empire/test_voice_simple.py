#!/usr/bin/env python3

# Test if we can define the classes directly
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

try:
    # Import dependencies
    from app.models.communication import (
        VoiceCall, VoiceScript, MessageStatus, MessagePriority,
        CommunicationAnalytics, CommunicationChannel
    )
    print("✓ Communication models imported")
    
    # Try to define a simple class
    class TestVoiceService:
        def __init__(self):
            self.test = "working"
    
    print("✓ Test class defined")
    
    # Now try to import the actual file
    import importlib.util
    spec = importlib.util.spec_from_file_location("voice_service", "app/services/voice_service.py")
    voice_module = importlib.util.module_from_spec(spec)
    
    print("✓ Module spec created")
    
    # Execute the module
    spec.loader.exec_module(voice_module)
    
    print("✓ Module executed")
    print("Available in module:", [x for x in dir(voice_module) if not x.startswith('_')])
    
    # Check if classes exist
    if hasattr(voice_module, 'VoiceService'):
        print("✓ VoiceService found!")
    else:
        print("✗ VoiceService not found")
        
    if hasattr(voice_module, 'VoiceServiceConfig'):
        print("✓ VoiceServiceConfig found!")
    else:
        print("✗ VoiceServiceConfig not found")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()