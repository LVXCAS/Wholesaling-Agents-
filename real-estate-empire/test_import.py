#!/usr/bin/env python3

try:
    exec(open('app/services/voice_service.py').read())
    print("File executed successfully")
    print("VoiceService in globals:", 'VoiceService' in globals())
    if 'VoiceService' in globals():
        print("VoiceService class found")
    else:
        print("Available classes:", [name for name in globals() if name[0].isupper()])
except Exception as e:
    print(f"Error during execution: {e}")
    import traceback
    traceback.print_exc()