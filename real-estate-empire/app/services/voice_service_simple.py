"""
Simple voice service test.
"""

print("DEBUG: Starting voice service module")

class VoiceServiceConfig:
    """Voice service configuration."""
    
    def __init__(self, test: str = "test"):
        self.test = test

print("DEBUG: VoiceServiceConfig defined")

class VoiceService:
    """Voice service."""
    
    def __init__(self, config: VoiceServiceConfig):
        self.config = config

print("DEBUG: VoiceService defined")
print("DEBUG: Module loaded successfully")