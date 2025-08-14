#!/usr/bin/env python3

import sys
sys.path.append('.')

# Test each import individually
print("Testing imports...")

try:
    from typing import List, Dict, Optional, Any, Tuple
    print("✓ typing")
except Exception as e:
    print(f"✗ typing: {e}")

try:
    import uuid
    print("✓ uuid")
except Exception as e:
    print(f"✗ uuid: {e}")

try:
    import math
    print("✓ math")
except Exception as e:
    print(f"✗ math: {e}")

try:
    from datetime import datetime, timedelta
    print("✓ datetime")
except Exception as e:
    print(f"✗ datetime: {e}")

try:
    from sqlalchemy.orm import Session
    print("✓ sqlalchemy.orm")
except Exception as e:
    print(f"✗ sqlalchemy.orm: {e}")

try:
    from app.models.lead_scoring import LeadScore
    print("✓ app.models.lead_scoring")
except Exception as e:
    print(f"✗ app.models.lead_scoring: {e}")

try:
    from app.models.lead import PropertyLeadDB
    print("✓ app.models.lead")
except Exception as e:
    print(f"✗ app.models.lead: {e}")

try:
    from app.core.database import get_db
    print("✓ app.core.database")
except Exception as e:
    print(f"✗ app.core.database: {e}")

# Now try to define a minimal class
print("\nTesting class definition...")

try:
    class TestService:
        def __init__(self):
            pass
    
    print("✓ Class definition works")
    
    # Test instantiation
    service = TestService()
    print("✓ Class instantiation works")
    
except Exception as e:
    print(f"✗ Class definition failed: {e}")

print("\nTesting module execution...")

# Try to execute the service file directly
try:
    with open('app/services/lead_scoring_service.py', 'r') as f:
        content = f.read()
    
    print(f"File size: {len(content)} characters")
    print("File starts with:", content[:100])
    print("File ends with:", content[-100:])
    
    # Try to compile the code
    compile(content, 'app/services/lead_scoring_service.py', 'exec')
    print("✓ File compiles successfully")
    
    # Try to execute it
    exec(content)
    print("✓ File executes successfully")
    
    # Check if LeadScoringService is defined
    if 'LeadScoringService' in locals():
        print("✓ LeadScoringService is defined")
    else:
        print("✗ LeadScoringService is NOT defined")
        print("Available names:", [name for name in locals().keys() if not name.startswith('_')])
    
except Exception as e:
    print(f"✗ File execution failed: {e}")
    import traceback
    traceback.print_exc()