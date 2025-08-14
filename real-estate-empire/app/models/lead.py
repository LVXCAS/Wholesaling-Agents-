"""
Lead data models for the Real Estate Empire platform.
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


class LeadStatusEnum(str, Enum):
    """Enum for lead status."""
    NEW = "new"
    CONTACTED = "contacted"
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    QUALIFIED = "qualified"
    UNDER_CONTRACT = "under_contract"
    CLOSED = "closed"
    DEAD = "dead"


class LeadSourceEnum(str, Enum):
    """Enum for lead sources."""
    MLS = "mls"
    PUBLIC_RECORDS = "public_records"
    FORECLOSURE = "foreclosure"
    FSBO = "fsbo"
    EXPIRED_LISTING = "expired_listing"
    ABSENTEE_OWNER = "absentee_owner"
    HIGH_EQUITY = "high_equity"
    DISTRESSED = "distressed"
    REFERRAL = "referral"
    MARKETING = "marketing"
    COLD_CALL = "cold_call"
    DIRECT_MAIL = "direct_mail"
    OTHER = "other"


class ContactMethodEnum(str, Enum):
    """Enum for preferred contact methods."""
    EMAIL = "email"
    PHONE = "phone"
    TEXT = "text"
    MAIL = "mail"


class PropertyLeadDB(Base):
    """SQLAlchemy model for property leads."""
    __tablename__ = "property_leads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Lead Information
    status = Column(String, nullable=False, default=LeadStatusEnum.NEW)
    source = Column(String, nullable=False)
    source_url = Column(String, nullable=True)
    lead_score = Column(Float, nullable=True)  # 0-100 scale
    
    # Owner Information
    owner_name = Column(String, nullable=True)
    owner_email = Column(String, nullable=True)
    owner_phone = Column(String, nullable=True)
    owner_address = Column(String, nullable=True)
    owner_city = Column(String, nullable=True)
    owner_state = Column(String, nullable=True)
    owner_zip = Column(String, nullable=True)
    
    # Contact Preferences
    preferred_contact_method = Column(String, nullable=True)
    best_contact_time = Column(String, nullable=True)
    do_not_call = Column(Boolean, default=False)
    do_not_email = Column(Boolean, default=False)
    do_not_text = Column(Boolean, default=False)
    
    # Motivation Indicators
    motivation_score = Column(Float, nullable=True)  # 0-100 scale
    motivation_factors = Column(JSON, nullable=True)  # Array of motivation indicators
    urgency_level = Column(String, nullable=True)  # "low", "medium", "high"
    
    # Financial Information
    asking_price = Column(Float, nullable=True)
    mortgage_balance = Column(Float, nullable=True)
    equity_estimate = Column(Float, nullable=True)
    monthly_payment = Column(Float, nullable=True)
    behind_on_payments = Column(Boolean, default=False)
    
    # Property Condition
    condition_notes = Column(Text, nullable=True)
    repair_needed = Column(Boolean, default=False)
    estimated_repair_cost = Column(Float, nullable=True)
    
    # Lead Tracking
    first_contact_date = Column(DateTime, nullable=True)
    last_contact_date = Column(DateTime, nullable=True)
    next_follow_up_date = Column(DateTime, nullable=True)
    contact_attempts = Column(Integer, default=0)
    
    # Additional Data
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tags
    assigned_to = Column(String, nullable=True)  # User ID or name
    
    # Relationships
    property = relationship("PropertyDB", back_populates="leads")
    communications = relationship("CommunicationDB", back_populates="lead")
    
    def __repr__(self):
        return f"<PropertyLeadDB(id={self.id}, property_id={self.property_id}, status={self.status})>"


class CommunicationDB(Base):
    """SQLAlchemy model for tracking communications with leads."""
    __tablename__ = "communications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("property_leads.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Communication Details
    channel = Column(String, nullable=False)  # "email", "phone", "text", "mail"
    direction = Column(String, nullable=False)  # "outbound", "inbound"
    subject = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    
    # Status and Tracking
    status = Column(String, nullable=False)  # "sent", "delivered", "opened", "replied", "bounced"
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    replied_at = Column(DateTime, nullable=True)
    
    # Response Analysis
    response_sentiment = Column(Float, nullable=True)  # -1 to 1 scale
    response_interest_level = Column(Float, nullable=True)  # 0 to 1 scale
    response_objections = Column(JSON, nullable=True)  # Array of objections
    response_questions = Column(JSON, nullable=True)  # Array of questions
    
    # Additional Data
    campaign_id = Column(UUID(as_uuid=True), nullable=True)
    template_id = Column(UUID(as_uuid=True), nullable=True)
    external_id = Column(String, nullable=True)  # ID from external service
    communication_metadata = Column(JSON, nullable=True)
    
    # Relationship
    lead = relationship("PropertyLeadDB", back_populates="communications")
    
    def __repr__(self):
        return f"<CommunicationDB(id={self.id}, lead_id={self.lead_id}, channel={self.channel})>"


# Pydantic models for API requests and responses

class PropertyLeadCreate(BaseModel):
    """Pydantic model for creating a property lead."""
    property_id: uuid.UUID
    status: LeadStatusEnum = LeadStatusEnum.NEW
    source: LeadSourceEnum
    source_url: Optional[str] = None
    lead_score: Optional[float] = Field(None, ge=0, le=100)
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_address: Optional[str] = None
    owner_city: Optional[str] = None
    owner_state: Optional[str] = None
    owner_zip: Optional[str] = None
    preferred_contact_method: Optional[ContactMethodEnum] = None
    best_contact_time: Optional[str] = None
    do_not_call: bool = False
    do_not_email: bool = False
    do_not_text: bool = False
    motivation_score: Optional[float] = Field(None, ge=0, le=100)
    motivation_factors: Optional[List[str]] = None
    urgency_level: Optional[str] = None
    asking_price: Optional[float] = None
    mortgage_balance: Optional[float] = None
    equity_estimate: Optional[float] = None
    monthly_payment: Optional[float] = None
    behind_on_payments: bool = False
    condition_notes: Optional[str] = None
    repair_needed: bool = False
    estimated_repair_cost: Optional[float] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    assigned_to: Optional[str] = None
    
    class Config:
        from_attributes = True


class PropertyLeadUpdate(BaseModel):
    """Pydantic model for updating a property lead."""
    status: Optional[LeadStatusEnum] = None
    source: Optional[LeadSourceEnum] = None
    source_url: Optional[str] = None
    lead_score: Optional[float] = Field(None, ge=0, le=100)
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_address: Optional[str] = None
    owner_city: Optional[str] = None
    owner_state: Optional[str] = None
    owner_zip: Optional[str] = None
    preferred_contact_method: Optional[ContactMethodEnum] = None
    best_contact_time: Optional[str] = None
    do_not_call: Optional[bool] = None
    do_not_email: Optional[bool] = None
    do_not_text: Optional[bool] = None
    motivation_score: Optional[float] = Field(None, ge=0, le=100)
    motivation_factors: Optional[List[str]] = None
    urgency_level: Optional[str] = None
    asking_price: Optional[float] = None
    mortgage_balance: Optional[float] = None
    equity_estimate: Optional[float] = None
    monthly_payment: Optional[float] = None
    behind_on_payments: Optional[bool] = None
    condition_notes: Optional[str] = None
    repair_needed: Optional[bool] = None
    estimated_repair_cost: Optional[float] = None
    first_contact_date: Optional[datetime] = None
    last_contact_date: Optional[datetime] = None
    next_follow_up_date: Optional[datetime] = None
    contact_attempts: Optional[int] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    assigned_to: Optional[str] = None
    
    class Config:
        from_attributes = True


class PropertyLeadResponse(BaseModel):
    """Pydantic model for property lead API responses."""
    id: uuid.UUID
    property_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    status: LeadStatusEnum
    source: LeadSourceEnum
    source_url: Optional[str] = None
    lead_score: Optional[float] = None
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_address: Optional[str] = None
    owner_city: Optional[str] = None
    owner_state: Optional[str] = None
    owner_zip: Optional[str] = None
    preferred_contact_method: Optional[ContactMethodEnum] = None
    best_contact_time: Optional[str] = None
    do_not_call: bool
    do_not_email: bool
    do_not_text: bool
    motivation_score: Optional[float] = None
    motivation_factors: Optional[List[str]] = None
    urgency_level: Optional[str] = None
    asking_price: Optional[float] = None
    mortgage_balance: Optional[float] = None
    equity_estimate: Optional[float] = None
    monthly_payment: Optional[float] = None
    behind_on_payments: bool
    condition_notes: Optional[str] = None
    repair_needed: bool
    estimated_repair_cost: Optional[float] = None
    first_contact_date: Optional[datetime] = None
    last_contact_date: Optional[datetime] = None
    next_follow_up_date: Optional[datetime] = None
    contact_attempts: int
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    assigned_to: Optional[str] = None
    
    class Config:
        from_attributes = True


class CommunicationCreate(BaseModel):
    """Pydantic model for creating a communication record."""
    lead_id: uuid.UUID
    channel: str
    direction: str
    subject: Optional[str] = None
    content: Optional[str] = None
    status: str = "sent"
    sent_at: Optional[datetime] = None
    campaign_id: Optional[uuid.UUID] = None
    template_id: Optional[uuid.UUID] = None
    external_id: Optional[str] = None
    communication_metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class CommunicationResponse(BaseModel):
    """Pydantic model for communication API responses."""
    id: uuid.UUID
    lead_id: uuid.UUID
    created_at: datetime
    channel: str
    direction: str
    subject: Optional[str] = None
    content: Optional[str] = None
    status: str
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    response_sentiment: Optional[float] = None
    response_interest_level: Optional[float] = None
    response_objections: Optional[List[str]] = None
    response_questions: Optional[List[str]] = None
    campaign_id: Optional[uuid.UUID] = None
    template_id: Optional[uuid.UUID] = None
    external_id: Optional[str] = None
    communication_metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True