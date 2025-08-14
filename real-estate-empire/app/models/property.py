"""
Property data models for the Real Estate Empire platform.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlalchemy import Column, DateTime, Float, Integer, String, Boolean, Text, JSON, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from app.core.database import Base


class PropertyTypeEnum(str, Enum):
    """Enum for property types."""
    SINGLE_FAMILY = "single_family"
    MULTI_FAMILY = "multi_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    APARTMENT = "apartment"
    COMMERCIAL = "commercial"
    LAND = "land"
    MOBILE_HOME = "mobile_home"
    OTHER = "other"


class PropertyStatusEnum(str, Enum):
    """Enum for property status."""
    ACTIVE = "active"
    PENDING = "pending"
    SOLD = "sold"
    OFF_MARKET = "off_market"
    FORECLOSURE = "foreclosure"
    PRE_FORECLOSURE = "pre_foreclosure"
    AUCTION = "auction"


class PropertyDB(Base):
    """SQLAlchemy model for property data."""
    __tablename__ = "properties"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Basic Property Information
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)
    county = Column(String, nullable=True)
    
    # Property Characteristics
    property_type = Column(String, nullable=False, default=PropertyTypeEnum.SINGLE_FAMILY)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Float, nullable=True)
    square_feet = Column(Integer, nullable=True)
    lot_size = Column(Float, nullable=True)  # in acres
    year_built = Column(Integer, nullable=True)
    stories = Column(Integer, nullable=True)
    garage_spaces = Column(Integer, nullable=True)
    
    # Location Data
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Financial Information
    current_value = Column(Float, nullable=True)
    assessed_value = Column(Float, nullable=True)
    tax_amount = Column(Float, nullable=True)  # annual property tax
    listing_price = Column(Float, nullable=True)
    last_sale_price = Column(Float, nullable=True)
    last_sale_date = Column(DateTime, nullable=True)
    
    # Property Status
    status = Column(String, nullable=False, default=PropertyStatusEnum.ACTIVE)
    days_on_market = Column(Integer, nullable=True)
    
    # Property Features and Condition
    features = Column(JSON, nullable=True)  # JSON object with various features
    condition_score = Column(Float, nullable=True)  # 0-1 scale
    renovation_needed = Column(Boolean, default=False)
    
    # Market Data
    neighborhood = Column(String, nullable=True)
    school_district = Column(String, nullable=True)
    walk_score = Column(Integer, nullable=True)
    crime_score = Column(Float, nullable=True)
    
    # Data Source Information
    data_source = Column(String, nullable=True)  # e.g., "kaggle", "mls", "zillow"
    external_id = Column(String, nullable=True)  # ID from external source
    data_quality_score = Column(Float, nullable=True)  # 0-1 scale
    
    # Additional Data
    description = Column(Text, nullable=True)
    photos = Column(JSON, nullable=True)  # Array of photo URLs
    virtual_tour_url = Column(String, nullable=True)
    
    # Relationships
    analyses = relationship("PropertyAnalysisDB", back_populates="property")
    leads = relationship("PropertyLeadDB", back_populates="property")
    
    def __repr__(self):
        return f"<PropertyDB(id={self.id}, address={self.address}, city={self.city})>"


class PropertyAnalysisDB(Base):
    """SQLAlchemy model for property analysis results."""
    __tablename__ = "property_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Analysis Type
    analysis_type = Column(String, nullable=False)  # e.g., "flip", "rental", "wholesale"
    
    # Valuation Results
    arv_estimate = Column(Float, nullable=True)
    current_value_estimate = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    comparable_count = Column(Integer, nullable=True)
    
    # Financial Metrics
    repair_estimate = Column(Float, nullable=True)
    potential_profit = Column(Float, nullable=True)
    roi_estimate = Column(Float, nullable=True)
    cash_flow_estimate = Column(Float, nullable=True)
    cap_rate = Column(Float, nullable=True)
    
    # Analysis Details
    analysis_data = Column(JSON, nullable=True)  # Detailed analysis results
    comparable_properties = Column(JSON, nullable=True)  # Array of comparable property data
    
    # Relationship
    property = relationship("PropertyDB", back_populates="analyses")
    
    def __repr__(self):
        return f"<PropertyAnalysisDB(id={self.id}, property_id={self.property_id}, type={self.analysis_type})>"


# Pydantic models for API requests and responses

class PropertyCreate(BaseModel):
    """Pydantic model for creating a property."""
    address: str
    city: str
    state: str
    zip_code: str
    county: Optional[str] = None
    property_type: PropertyTypeEnum = PropertyTypeEnum.SINGLE_FAMILY
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    stories: Optional[int] = None
    garage_spaces: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    current_value: Optional[float] = None
    assessed_value: Optional[float] = None
    tax_amount: Optional[float] = None
    listing_price: Optional[float] = None
    last_sale_price: Optional[float] = None
    last_sale_date: Optional[datetime] = None
    status: PropertyStatusEnum = PropertyStatusEnum.ACTIVE
    days_on_market: Optional[int] = None
    features: Optional[Dict[str, Any]] = None
    condition_score: Optional[float] = Field(None, ge=0, le=1)
    renovation_needed: bool = False
    neighborhood: Optional[str] = None
    school_district: Optional[str] = None
    walk_score: Optional[int] = Field(None, ge=0, le=100)
    crime_score: Optional[float] = Field(None, ge=0, le=100)
    data_source: Optional[str] = None
    external_id: Optional[str] = None
    data_quality_score: Optional[float] = Field(None, ge=0, le=1)
    description: Optional[str] = None
    photos: Optional[List[str]] = None
    virtual_tour_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class PropertyUpdate(BaseModel):
    """Pydantic model for updating a property."""
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    county: Optional[str] = None
    property_type: Optional[PropertyTypeEnum] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    stories: Optional[int] = None
    garage_spaces: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    current_value: Optional[float] = None
    assessed_value: Optional[float] = None
    tax_amount: Optional[float] = None
    listing_price: Optional[float] = None
    last_sale_price: Optional[float] = None
    last_sale_date: Optional[datetime] = None
    status: Optional[PropertyStatusEnum] = None
    days_on_market: Optional[int] = None
    features: Optional[Dict[str, Any]] = None
    condition_score: Optional[float] = Field(None, ge=0, le=1)
    renovation_needed: Optional[bool] = None
    neighborhood: Optional[str] = None
    school_district: Optional[str] = None
    walk_score: Optional[int] = Field(None, ge=0, le=100)
    crime_score: Optional[float] = Field(None, ge=0, le=100)
    data_source: Optional[str] = None
    external_id: Optional[str] = None
    data_quality_score: Optional[float] = Field(None, ge=0, le=1)
    description: Optional[str] = None
    photos: Optional[List[str]] = None
    virtual_tour_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class PropertyResponse(BaseModel):
    """Pydantic model for property API responses."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    address: str
    city: str
    state: str
    zip_code: str
    county: Optional[str] = None
    property_type: PropertyTypeEnum
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    stories: Optional[int] = None
    garage_spaces: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    current_value: Optional[float] = None
    assessed_value: Optional[float] = None
    tax_amount: Optional[float] = None
    listing_price: Optional[float] = None
    last_sale_price: Optional[float] = None
    last_sale_date: Optional[datetime] = None
    status: PropertyStatusEnum
    days_on_market: Optional[int] = None
    features: Optional[Dict[str, Any]] = None
    condition_score: Optional[float] = None
    renovation_needed: bool
    neighborhood: Optional[str] = None
    school_district: Optional[str] = None
    walk_score: Optional[int] = None
    crime_score: Optional[float] = None
    data_source: Optional[str] = None
    external_id: Optional[str] = None
    data_quality_score: Optional[float] = None
    description: Optional[str] = None
    photos: Optional[List[str]] = None
    virtual_tour_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class PropertyAnalysisCreate(BaseModel):
    """Pydantic model for creating a property analysis."""
    property_id: uuid.UUID
    analysis_type: str
    arv_estimate: Optional[float] = None
    current_value_estimate: Optional[float] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    comparable_count: Optional[int] = None
    repair_estimate: Optional[float] = None
    potential_profit: Optional[float] = None
    roi_estimate: Optional[float] = None
    cash_flow_estimate: Optional[float] = None
    cap_rate: Optional[float] = None
    analysis_data: Optional[Dict[str, Any]] = None
    comparable_properties: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True


class PropertyAnalysisResponse(BaseModel):
    """Pydantic model for property analysis API responses."""
    id: uuid.UUID
    property_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    analysis_type: str
    arv_estimate: Optional[float] = None
    current_value_estimate: Optional[float] = None
    confidence_score: Optional[float] = None
    comparable_count: Optional[int] = None
    repair_estimate: Optional[float] = None
    potential_profit: Optional[float] = None
    roi_estimate: Optional[float] = None
    cash_flow_estimate: Optional[float] = None
    cap_rate: Optional[float] = None
    analysis_data: Optional[Dict[str, Any]] = None
    comparable_properties: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True