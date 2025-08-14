"""
Negotiation data models for the Real Estate Empire platform.
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


class NegotiationStatusEnum(str, Enum):
    """Enum for negotiation status."""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COUNTER_OFFER = "counter_offer"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    STALLED = "stalled"
    CLOSED = "closed"


class OfferTypeEnum(str, Enum):
    """Enum for offer types."""
    INITIAL = "initial"
    COUNTER = "counter"
    FINAL = "final"
    BACKUP = "backup"


class SellerMotivationEnum(str, Enum):
    """Enum for seller motivation levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    URGENT = "urgent"


class MarketConditionEnum(str, Enum):
    """Enum for market conditions."""
    BUYERS_MARKET = "buyers_market"
    SELLERS_MARKET = "sellers_market"
    BALANCED = "balanced"


class NegotiationStrategyDB(Base):
    """SQLAlchemy model for negotiation strategies."""
    __tablename__ = "negotiation_strategies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Strategy Details
    strategy_name = Column(String, nullable=False)
    recommended_offer_price = Column(Float, nullable=False)
    max_offer_price = Column(Float, nullable=False)
    negotiation_approach = Column(String, nullable=False)  # aggressive, moderate, conservative
    
    # Market Analysis
    market_condition = Column(String, nullable=False, default=MarketConditionEnum.BALANCED)
    seller_motivation = Column(String, nullable=False, default=SellerMotivationEnum.MODERATE)
    days_on_market_factor = Column(Float, nullable=True)
    comparable_sales_factor = Column(Float, nullable=True)
    
    # Strategy Components
    talking_points = Column(JSON, nullable=True)  # Array of key talking points
    value_propositions = Column(JSON, nullable=True)  # Array of value propositions
    potential_objections = Column(JSON, nullable=True)  # Array of potential objections and responses
    contingencies = Column(JSON, nullable=True)  # Array of recommended contingencies
    
    # Confidence and Risk
    confidence_score = Column(Float, nullable=False, default=0.5)  # 0-1 scale
    risk_assessment = Column(JSON, nullable=True)  # Risk factors and mitigation strategies
    
    # Relationships
    property = relationship("PropertyDB")
    offers = relationship("OfferDB", back_populates="strategy")
    
    def __repr__(self):
        return f"<NegotiationStrategyDB(id={self.id}, property_id={self.property_id}, strategy={self.strategy_name})>"


class OfferDB(Base):
    """SQLAlchemy model for offers."""
    __tablename__ = "offers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("negotiation_strategies.id"), nullable=False)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Offer Details
    offer_type = Column(String, nullable=False, default=OfferTypeEnum.INITIAL)
    offer_amount = Column(Float, nullable=False)
    earnest_money = Column(Float, nullable=True)
    down_payment = Column(Float, nullable=True)
    financing_type = Column(String, nullable=True)  # cash, conventional, fha, etc.
    
    # Terms
    closing_date = Column(DateTime, nullable=True)
    inspection_period = Column(Integer, nullable=True)  # days
    appraisal_contingency = Column(Boolean, default=True)
    financing_contingency = Column(Boolean, default=True)
    inspection_contingency = Column(Boolean, default=True)
    
    # Custom Terms
    custom_terms = Column(JSON, nullable=True)  # Additional custom terms
    contingencies = Column(JSON, nullable=True)  # Array of contingencies
    
    # Status
    status = Column(String, nullable=False, default=NegotiationStatusEnum.INITIATED)
    response_received = Column(Boolean, default=False)
    response_date = Column(DateTime, nullable=True)
    response_details = Column(JSON, nullable=True)
    
    # Relationships
    strategy = relationship("NegotiationStrategyDB", back_populates="offers")
    property = relationship("PropertyDB")
    counter_offers = relationship("CounterOfferDB", back_populates="original_offer")
    
    def __repr__(self):
        return f"<OfferDB(id={self.id}, property_id={self.property_id}, amount=${self.offer_amount})>"


class CounterOfferDB(Base):
    """SQLAlchemy model for counter offers."""
    __tablename__ = "counter_offers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_offer_id = Column(UUID(as_uuid=True), ForeignKey("offers.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Counter Offer Details
    counter_amount = Column(Float, nullable=False)
    seller_changes = Column(JSON, nullable=True)  # Changes requested by seller
    buyer_response = Column(JSON, nullable=True)  # Our response analysis
    
    # Analysis
    analysis_result = Column(JSON, nullable=True)  # AI analysis of the counter offer
    recommended_response = Column(String, nullable=True)  # accept, counter, reject
    risk_factors = Column(JSON, nullable=True)  # Identified risk factors
    
    # Status
    status = Column(String, nullable=False, default=NegotiationStatusEnum.IN_PROGRESS)
    responded = Column(Boolean, default=False)
    response_date = Column(DateTime, nullable=True)
    
    # Relationships
    original_offer = relationship("OfferDB", back_populates="counter_offers")
    
    def __repr__(self):
        return f"<CounterOfferDB(id={self.id}, offer_id={self.original_offer_id}, amount=${self.counter_amount})>"


# Pydantic models for API requests and responses

class NegotiationStrategyCreate(BaseModel):
    """Pydantic model for creating a negotiation strategy."""
    property_id: uuid.UUID
    strategy_name: str
    recommended_offer_price: float
    max_offer_price: float
    negotiation_approach: str
    market_condition: MarketConditionEnum = MarketConditionEnum.BALANCED
    seller_motivation: SellerMotivationEnum = SellerMotivationEnum.MODERATE
    days_on_market_factor: Optional[float] = None
    comparable_sales_factor: Optional[float] = None
    talking_points: Optional[List[str]] = None
    value_propositions: Optional[List[str]] = None
    potential_objections: Optional[List[Dict[str, str]]] = None
    contingencies: Optional[List[str]] = None
    confidence_score: float = Field(0.5, ge=0, le=1)
    risk_assessment: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class NegotiationStrategyResponse(BaseModel):
    """Pydantic model for negotiation strategy API responses."""
    id: uuid.UUID
    property_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    strategy_name: str
    recommended_offer_price: float
    max_offer_price: float
    negotiation_approach: str
    market_condition: MarketConditionEnum
    seller_motivation: SellerMotivationEnum
    days_on_market_factor: Optional[float] = None
    comparable_sales_factor: Optional[float] = None
    talking_points: Optional[List[str]] = None
    value_propositions: Optional[List[str]] = None
    potential_objections: Optional[List[Dict[str, str]]] = None
    contingencies: Optional[List[str]] = None
    confidence_score: float
    risk_assessment: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class OfferCreate(BaseModel):
    """Pydantic model for creating an offer."""
    strategy_id: uuid.UUID
    property_id: uuid.UUID
    offer_type: OfferTypeEnum = OfferTypeEnum.INITIAL
    offer_amount: float
    earnest_money: Optional[float] = None
    down_payment: Optional[float] = None
    financing_type: Optional[str] = None
    closing_date: Optional[datetime] = None
    inspection_period: Optional[int] = None
    appraisal_contingency: bool = True
    financing_contingency: bool = True
    inspection_contingency: bool = True
    custom_terms: Optional[Dict[str, Any]] = None
    contingencies: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class OfferResponse(BaseModel):
    """Pydantic model for offer API responses."""
    id: uuid.UUID
    strategy_id: uuid.UUID
    property_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    offer_type: OfferTypeEnum
    offer_amount: float
    earnest_money: Optional[float] = None
    down_payment: Optional[float] = None
    financing_type: Optional[str] = None
    closing_date: Optional[datetime] = None
    inspection_period: Optional[int] = None
    appraisal_contingency: bool
    financing_contingency: bool
    inspection_contingency: bool
    custom_terms: Optional[Dict[str, Any]] = None
    contingencies: Optional[List[str]] = None
    status: NegotiationStatusEnum
    response_received: bool
    response_date: Optional[datetime] = None
    response_details: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class CounterOfferCreate(BaseModel):
    """Pydantic model for creating a counter offer."""
    original_offer_id: uuid.UUID
    counter_amount: float
    seller_changes: Optional[Dict[str, Any]] = None
    buyer_response: Optional[Dict[str, Any]] = None
    analysis_result: Optional[Dict[str, Any]] = None
    recommended_response: Optional[str] = None
    risk_factors: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class CounterOfferResponse(BaseModel):
    """Pydantic model for counter offer API responses."""
    id: uuid.UUID
    original_offer_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    counter_amount: float
    seller_changes: Optional[Dict[str, Any]] = None
    buyer_response: Optional[Dict[str, Any]] = None
    analysis_result: Optional[Dict[str, Any]] = None
    recommended_response: Optional[str] = None
    risk_factors: Optional[List[str]] = None
    status: NegotiationStatusEnum
    responded: bool
    response_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class NegotiationCoachingRequest(BaseModel):
    """Pydantic model for negotiation coaching requests."""
    property_id: uuid.UUID
    situation: str  # Description of current negotiation situation
    seller_response: Optional[str] = None
    specific_concerns: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class NegotiationCoachingResponse(BaseModel):
    """Pydantic model for negotiation coaching responses."""
    talking_points: List[str]
    objection_responses: Dict[str, str]
    value_propositions: List[str]
    negotiation_script: str
    recommended_approach: str
    confidence_tips: List[str]
    
    class Config:
        from_attributes = True