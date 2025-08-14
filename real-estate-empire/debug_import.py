#!/usr/bin/env python3

import sys
sys.path.append('.')

try:
    import app.services.lead_scoring_service as lss
    print("Module imported successfully")
    print("Module attributes:", [attr for attr in dir(lss) if not attr.startswith('_')])
    
    # Try to access the class
    if hasattr(lss, 'LeadScoringService'):
        print("LeadScoringService class found!")
    else:
        print("LeadScoringService class NOT found")
        
    # Check if there are any import errors in the module
    print("Module file:", lss.__file__)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()