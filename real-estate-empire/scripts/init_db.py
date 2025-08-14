#!/usr/bin/env python3
"""
Database initialization script for Real Estate Empire.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import create_tables, engine
from app.models import *  # Import all models to register them


def main():
    """Initialize the database with all tables."""
    print("Creating database tables...")
    
    try:
        create_tables()
        print("✅ Database tables created successfully!")
        
        # Test the connection
        with engine.connect() as conn:
            print("✅ Database connection test successful!")
            
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()