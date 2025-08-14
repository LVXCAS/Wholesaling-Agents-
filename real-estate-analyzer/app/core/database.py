import os
from app.core.config import settings # Added import
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import DeclarativeMeta # For Base type hint

# Old DATABASE_URL definition and related comments removed.

# Create SQLAlchemy engine
# Add connect_args for SQLite to allow multiple threads
connect_args = {'check_same_thread': False} if 'sqlite' in str(settings.DATABASE_URL) else {}
engine = create_engine(str(settings.DATABASE_URL), connect_args=connect_args)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for declarative class definitions
# All SQLAlchemy models will inherit from this Base
Base: DeclarativeMeta = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create all tables in the database
# This is useful for initial setup or testing
# Alembic will be used for migrations in a more robust setup
def create_tables():
    # Import all models here before calling Base.metadata.create_all
    # This ensures they are registered with SQLAlchemy's metadata
    # from app.models.property import PropertyDB # Example
    # from app.models.valuation import AnalysisResultDB, ComparableSaleDB # Example
    # It's better if models are imported somewhere before this function is called,
    # or pass metadata directly. For now, we assume models are registered.
    # A common pattern is to import all models in their respective __init__.py
    # and then import those __init__.py modules.
    # Let's ensure models are imported so Base.metadata knows about them.
    # This can be done by importing the model modules.
    from app.models import property # This should trigger registration if models use the Base from here
    from app.models import valuation # This should trigger registration
    Base.metadata.create_all(bind=engine)
