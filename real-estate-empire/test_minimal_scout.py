#!/usr/bin/env python3
"""
Minimal test for scout tools
"""

import sys
import os
sys.path.insert(0, '.')

# Test minimal imports
try:
    print("Testing minimal scout tool import...")
    
    # Import dependencies first
    from app.core.agent_tools import BaseAgentTool, ToolMetadata, ToolCategory, ToolAccessLevel
    print("✓ Base dependencies imported")
    
    # Try to import just the enums and models
    from app.agents.scout_tools import PropertySource, PropertyStatus
    print("✓ Enums imported")
    
    # Try to import data models
    from app.agents.scout_tools import PropertyListing, OwnerInformation
    print("✓ Data models imported")
    
    print("✓ All basic imports successful")
    
except Exception as e:
    print(f"✗ Import error: {e}")
    import traceback
    traceback.print_exc()