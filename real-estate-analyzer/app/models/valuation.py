import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SAEnum

from app.core.database import Base
from app.models.property import PropertyTypeEnum


# Pydantic Models for Comparables
class ComparablePropertyBase(BaseModel):
    # This might mirror some fields from Property model or have its own specific fields
    # For now, let's assume it's a simplified version of a property
    address: str = Field(..., example="125 Main St")
    sale_price: float = Field(..., example=280000.00)
    sale_date: datetime = Field(..., example="2023-06-15T10:00:00Z")
    square_feet: int = Field(..., example=1600)
    bedrooms: int = Field(..., example=3)
    bathrooms: float = Field(..., example=2.0)
    distance_miles: Optional[float] = Field(None, example=0.25) # Distance from subject property
    adjusted_price: Optional[float] = Field(None, example=282000.00) # Price after adjustments

class ComparableProperty(ComparablePropertyBase):
    id: Optional[uuid.UUID] = Field(None, example="b2c3d4e5-f6g7-8901-2345-67890abcdef1") # If it's an existing property

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2

# Pydantic Models for Analysis Result
class AnalysisResultBase(BaseModel):
    arv_estimate: float = Field(..., example=285000.00)
    confidence_score: float = Field(..., example=0.85, ge=0, le=1)
    comparable_count: int = Field(..., example=7, ge=0)
    repair_estimate: Optional[float] = Field(None, example=15000.00, ge=0)
    profit_potential: Optional[float] = Field(None, example=45000.00) # Can be negative

class AnalysisResultCreate(AnalysisResultBase):
    property_id: uuid.UUID # Link to the property being analyzed
    # comparable_properties: List[ComparablePropertyBase] # Store the comparables used for this specific analysis

class AnalysisResult(AnalysisResultBase):
    id: uuid.UUID = Field(..., example="c3d4e5f6-g7h8-9012-3456-7890abcdef12")
    property_id: uuid.UUID
    analysis_date: datetime
    # Store a snapshot of comparables used for this analysis.
    # This is important because market conditions and comps change.
    # Using JSONB in DB to store this list of Pydantic models.
    comparable_properties_snapshot: List[ComparableProperty] = Field([], example=[
        {"address": "125 Main St", "sale_price": 280000, "sale_date": "2023-06-15T10:00:00Z", "square_feet": 1600, "bedrooms": 3, "bathrooms": 2.0, "distance_miles": 0.25, "adjusted_price": 282000}
    ])


    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2

# SQLAlchemy Model for Analysis Result
class AnalysisResultDB(Base): # Renamed to avoid Pydantic model name clash
    __tablename__ = "analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False) # Foreign key to PropertyDB

    arv_estimate = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False) # Range 0-1
    comparable_count = Column(Integer, nullable=False)
    repair_estimate = Column(Float, nullable=True)
    profit_potential = Column(Float, nullable=True)

    analysis_date = Column(DateTime, server_default=func.now(), nullable=False)

    # Store the list of comparable properties (as dicts or JSON) used for this specific analysis.
    # This makes the analysis result self-contained and reproducible.
    comparable_properties_snapshot = Column(JSON, nullable=True) # List of ComparableProperty dicts

    # Relationship back to PropertyDB
    property = relationship("PropertyDB", back_populates="analysis_results")

    # We might also have a separate table for comparables if they are managed independently
    # or if many analyses can share the same set of comparables (though snapshotting is safer for ARV history).
    # The current design with JSONB snapshot is simpler for Phase 1.

    def __repr__(self):
        return f"<AnalysisResultDB(id={self.id}, property_id={self.property_id}, arv_estimate={self.arv_estimate})>"

# SQLAlchemy Model for Comparable Sales (if managed independently, not just as snapshots)
# The issue mentions "Comparable_sales table for comp data". This implies a separate table.
# Let's define it. It could store general comps that are then selected and snapshotted into an analysis.
class ComparableSaleDB(Base):
    __tablename__ = "comparable_sales"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Fields similar to PropertyDB but specific to sales, or could be a PropertyDB itself marked as a comp
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)

    bedrooms = Column(Integer, nullable=False)
    bathrooms = Column(Float, nullable=False)
    square_feet = Column(Integer, nullable=False)
    lot_size = Column(Float, nullable=True)
    year_built = Column(Integer, nullable=True)
    # property_type = Column(SAEnum(PropertyTypeEnum, name="comparable_property_type_enum"), nullable=False) # Re-using PropertyTypeEnum
    property_type = Column(String, nullable=False) # Using String for now, to be replaced with SAEnum(PropertyTypeEnum)

    sale_price = Column(Float, nullable=False)
    sale_date = Column(DateTime, nullable=False)

    # Could have a field to store notes or source of this comparable data
    source = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # This table might not directly link to AnalysisResultDB if comps are snapshotted.
    # However, an analysis could reference IDs from this table if we don't snapshot full data.
    # For Phase 1, snapshotting into AnalysisResultDB.comparable_properties_snapshot is simpler.
    # This table would be populated by data_fetcher.py or manually.

    def __repr__(self):
        return f"<ComparableSaleDB(id={self.id}, address='{self.address}', sale_price={self.sale_price})>"
