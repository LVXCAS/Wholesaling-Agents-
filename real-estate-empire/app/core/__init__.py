"""
Core package for the Real Estate Empire platform.
"""

from .database import get_db, create_tables, drop_tables, engine, SessionLocal, Base

__all__ = [
    "get_db",
    "create_tables", 
    "drop_tables",
    "engine",
    "SessionLocal",
    "Base",
]