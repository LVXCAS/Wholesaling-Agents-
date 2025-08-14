#!/usr/bin/env python3

import sys
sys.path.append('.')

dependencies = [
    "typing",
    "uuid", 
    "math",
    "datetime",
    "sqlalchemy.orm",
    "app.models.lead_scoring",
    "app.models.lead",
    "app.core.database"
]

for dep in dependencies:
    try:
        if "." in dep:
            parts = dep.split(".")
            module = __import__(dep, fromlist=[parts[-1]])
        else:
            module = __import__(dep)
        print(f"✓ {dep} imported successfully")
    except Exception as e:
        print(f"✗ {dep} failed: {e}")