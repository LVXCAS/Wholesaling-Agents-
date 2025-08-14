import uuid
from datetime import datetime
from typing import Optional, List # Added List for future use potentially

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Float, Integer, String, func, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship # Ensure this is kept if used by PropertyDB

from app.core.database import Base # Keep existing Base import

from enum import Enum

class PropertyTypeEnum(str, Enum):
    SINGLE_FAMILY = "Single Family"
    MULTI_FAMILY = "Multi-Family"
    CONDO = "Condo"
    TOWNHOUSE = "Townhouse"
    LAND = "Land"
    OTHER = "Other"

# Updated PropertyCreate as per user feedback
class PropertyCreate(BaseModel):
    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "ignore",
        "from_attributes": True
    }
    
    address: str
    city: Optional[str] = ""
    state: Optional[str] = ""
    zip_code: Optional[str] = ""
    property_type: Optional[PropertyTypeEnum] = PropertyTypeEnum.SINGLE_FAMILY
    square_feet: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    year_built: Optional[int] = None
    lot_size: Optional[float] = None
    current_value: Optional[float] = None
    last_sale_price: Optional[float] = None
    last_sale_date: Optional[datetime] = None
    estimated_rent: Optional[float] = None
    repair_cost: Optional[float] = None
    arv: Optional[float] = None
    notes: Optional[str] = ""
    data_source: Optional[str] = "manual"

# Keep existing PropertyBase, PropertyUpdate, Property (Pydantic response model)
# These might need alignment with PropertyCreate if their fields differ significantly now.
# For now, assume they are compatible enough or will be adjusted later.
class PropertyBase(BaseModel):
    model_config = {
        "arbitrary_types_allowed": True,
        "from_attributes": True,
        "extra": "ignore"
    }
    
    address: str = Field(...)
    city: Optional[str] = ""
    state: Optional[str] = ""
    zip_code: Optional[str] = ""
    property_type: PropertyTypeEnum = PropertyTypeEnum.SINGLE_FAMILY
    square_feet: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    year_built: Optional[int] = None
    lot_size: Optional[float] = None
    current_value: Optional[float] = None
    last_sale_price: Optional[float] = None
    last_sale_date: Optional[datetime] = None
    estimated_rent: Optional[float] = None
    repair_cost: Optional[float] = None
    arv: Optional[float] = None
    notes: Optional[str] = ""
    data_source: Optional[str] = "manual"
class PropertyUpdate(PropertyBase):
    model_config = {
        "arbitrary_types_allowed": True,
        "from_attributes": True,
        "extra": "ignore"
    }
    address: Optional[str] = None # Explicitly make all fields optional for update

class Property(PropertyBase): # For API responses
    model_config = {
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
# Keep existing PropertyDB (SQLAlchemy model)
class PropertyDB(Base):
    __tablename__ = "properties"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    address = Column(String, nullable=False)
    city = Column(String, nullable=True, default="") # Align with PropertyCreate
    state = Column(String, nullable=True, default="") # Align
    zip_code = Column(String, nullable=True, default="") # Align
    bedrooms = Column(Integer, nullable=True) # Align
    bathrooms = Column(Float, nullable=True) # Align
    square_feet = Column(Integer, nullable=True) # Align
    lot_size = Column(Float, nullable=True)
    year_built = Column(Integer, nullable=True)
    property_type = Column(SAEnum(PropertyTypeEnum, name="property_type_enum"), nullable=True, default=PropertyTypeEnum.SINGLE_FAMILY) # Align
    current_value = Column(Float, nullable=True)
    last_sale_price = Column(Float, nullable=True)
    last_sale_date = Column(DateTime, nullable=True)
    estimated_rent: Column[Optional[float]] = Column(Float, nullable=True) # Added
    repair_cost: Column[Optional[float]] = Column(Float, nullable=True) # Added
    arv: Column[Optional[float]] = Column(Float, nullable=True) # Added
    notes: Column[Optional[str]] = Column(String, nullable=True, default="") # Added
    data_source: Column[Optional[str]] = Column(String, nullable=True, default="manual") # Added
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    analysis_results = relationship("AnalysisResultDB", back_populates="property")
    def __repr__(self):
        return f"<PropertyDB(id={self.id}, address='{self.address}')>"
