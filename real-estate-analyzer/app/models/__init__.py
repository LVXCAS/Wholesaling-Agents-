from .property import PropertyBase, PropertyCreate, PropertyUpdate, Property, PropertyDB, PropertyTypeEnum
from .valuation import (
    ComparablePropertyBase,
    ComparableProperty,
    AnalysisResultBase,
    AnalysisResultCreate,
    AnalysisResult,
    AnalysisResultDB,
    ComparableSaleDB
)

# It's common to define the SQLAlchemy Base in a central database.py and import it into models.
# For now, models define their own Base = declarative_base(). This will need consolidation.
# from app.core.database import Base # Ideal future state

__all__ = [
    "PropertyBase",
    "PropertyCreate",
    "PropertyUpdate",
    "Property",
    "PropertyDB",
    "PropertyTypeEnum",
    "ComparablePropertyBase",
    "ComparableProperty",
    "AnalysisResultBase",
    "AnalysisResultCreate",
    "AnalysisResult",
    "AnalysisResultDB",
    "ComparableSaleDB",
    # "Base", # If Base is consolidated and exposed from here
]
