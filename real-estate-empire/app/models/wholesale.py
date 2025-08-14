"""
Wholesale analysis models for the Real Estate Empire platform.
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


class DealStatusEnum(str, Enum):
    """Enum for wholesale deal status."""
    LEAD = "lead"
    ANALYZING = "analyzing"
    CONTACTED = "contacted"
    NEGOTIATING = "negotiating"
    UNDER_CONTRACT = "under_contract"
    MARKETING = "marketing"
    ASSIGNED = "assigned"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    DEAD = "dead"


class StrategyTypeEnum(str, Enum):
    """Enum for investment strategies."""
    WHOLESALE = "wholesale"
    FIX_AND_FLIP = "fix_and_flip"
    BUY_AND_HOLD = "buy_and_hold"
    BRRRR = "brrrr"
    LIVE_IN_FLIP = "live_in_flip"


class WholesaleDealDB(Base):
    """SQLAlchemy model for wholesale deals."""
    __tablename__ = "wholesale_deals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("property_leads.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Deal Status and Tracking
    status = Column(String, nullable=False, default=DealStatusEnum.LEAD)
    deal_score = Column(Float, nullable=True)  # 0-100 scale
    priority_level = Column(String, nullable=True)  # "low", "medium", "high"
    
    # Property Analysis
    arv_estimate = Column(Float, nullable=True)
    current_value_estimate = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)  # 0-1 scale
    condition_score = Column(Float, nullable=True)  # 0-1 scale
    
    # Repair and Renovation
    repair_estimate = Column(Float, nullable=True)
    repair_breakdown = Column(JSON, nullable=True)  # Detailed repair costs
    renovation_timeline = Column(Integer, nullable=True)  # days
    
    # Financial Analysis
    max_allowable_offer = Column(Float, nullable=True)
    wholesale_fee = Column(Float, nullable=True)
    potential_profit = Column(Float, nullable=True)
    buyer_profit_estimate = Column(Float, nullable=True)
    
    # Deal Terms
    offer_amount = Column(Float, nullable=True)
    contract_price = Column(Float, nullable=True)
    earnest_money = Column(Float, nullable=True)
    closing_date = Column(DateTime, nullable=True)
    assignment_fee = Column(Float, nullable=True)
    
    # Costs and Expenses
    holding_costs = Column(Float, nullable=True)
    closing_costs = Column(Float, nullable=True)
    marketing_costs = Column(Float, nullable=True)
    total_costs = Column(Float, nullable=True)
    
    # Buyer Information
    target_buyer_type = Column(String, nullable=True)
    buyer_id = Column(UUID(as_uuid=True), nullable=True)
    buyer_name = Column(String, nullable=True)
    buyer_contact = Column(String, nullable=True)
    
    # Timeline Tracking
    contract_date = Column(DateTime, nullable=True)
    marketing_start_date = Column(DateTime, nullable=True)
    assignment_date = Column(DateTime, nullable=True)
    actual_closing_date = Column(DateTime, nullable=True)
    
    # Performance Metrics
    days_to_contract = Column(Integer, nullable=True)
    days_to_assignment = Column(Integer, nullable=True)
    actual_profit = Column(Float, nullable=True)
    roi_actual = Column(Float, nullable=True)
    
    # Additional Data
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tags
    assigned_to = Column(String, nullable=True)  # User ID or name
    
    # Strategy Analysis
    strategies = Column(JSON, nullable=True)  # Array of strategy analyses
    recommended_strategy = Column(String, nullable=True)
    
    # Relationships
    property = relationship("PropertyDB")
    lead = relationship("PropertyLeadDB")
    
    def __repr__(self):
        return f"<WholesaleDealDB(id={self.id}, property_id={self.property_id}, status={self.status})>"


class RepairItemDB(Base):
    """SQLAlchemy model for repair cost items."""
    __tablename__ = "repair_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Item Details
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # e.g., "cosmetic", "structural", "mechanical"
    subcategory = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    
    # Cost Information
    unit = Column(String, nullable=False)  # e.g., "sqft", "each", "linear_ft"
    cost_per_unit = Column(Float, nullable=False)
    labor_cost_per_unit = Column(Float, nullable=True)
    material_cost_per_unit = Column(Float, nullable=True)
    
    # Regional Adjustments
    region = Column(String, nullable=True)  # state or metro area
    cost_adjustment_factor = Column(Float, default=1.0)
    
    # Additional Data
    typical_quantity = Column(Float, nullable=True)
    difficulty_level = Column(String, nullable=True)  # "easy", "medium", "hard"
    time_estimate = Column(Float, nullable=True)  # hours
    
    # Data Source
    data_source = Column(String, nullable=True)
    last_updated = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<RepairItemDB(id={self.id}, name={self.name}, cost_per_unit={self.cost_per_unit})>"


class InvestmentStrategyDB(Base):
    """SQLAlchemy model for investment strategy analysis."""
    __tablename__ = "investment_strategies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("wholesale_deals.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Strategy Details
    strategy_type = Column(String, nullable=False)
    strategy_name = Column(String, nullable=True)
    
    # Financial Projections
    initial_investment = Column(Float, nullable=True)
    total_costs = Column(Float, nullable=True)
    projected_revenue = Column(Float, nullable=True)
    projected_profit = Column(Float, nullable=True)
    roi_estimate = Column(Float, nullable=True)
    
    # Timeline
    timeline_months = Column(Integer, nullable=True)
    exit_timeline = Column(Integer, nullable=True)
    
    # Risk Assessment
    risk_level = Column(String, nullable=True)  # "low", "medium", "high"
    risk_factors = Column(JSON, nullable=True)  # Array of risk factors
    
    # Market Assumptions
    market_assumptions = Column(JSON, nullable=True)
    sensitivity_analysis = Column(JSON, nullable=True)
    
    # Strategy-Specific Data
    strategy_data = Column(JSON, nullable=True)  # Strategy-specific calculations
    
    # Relationship
    deal = relationship("WholesaleDealDB")
    
    def __repr__(self):
        return f"<InvestmentStrategyDB(id={self.id}, deal_id={self.deal_id}, strategy_type={self.strategy_type})>"


# Pydantic models for API requests and responses

class WholesaleDealCreate(BaseModel):
    """Pydantic model for creating a wholesale deal."""
    property_id: uuid.UUID
    lead_id: Optional[uuid.UUID] = None
    status: DealStatusEnum = DealStatusEnum.LEAD
    deal_score: Optional[float] = Field(None, ge=0, le=100)
    priority_level: Optional[str] = None
    arv_estimate: Optional[float] = None
    current_value_estimate: Optional[float] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    condition_score: Optional[float] = Field(None, ge=0, le=1)
    repair_estimate: Optional[float] = None
    repair_breakdown: Optional[Dict[str, Any]] = None
    renovation_timeline: Optional[int] = None
    max_allowable_offer: Optional[float] = None
    wholesale_fee: Optional[float] = None
    potential_profit: Optional[float] = None
    buyer_profit_estimate: Optional[float] = None
    holding_costs: Optional[float] = None
    closing_costs: Optional[float] = None
    marketing_costs: Optional[float] = None
    target_buyer_type: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    assigned_to: Optional[str] = None
    strategies: Optional[List[Dict[str, Any]]] = None
    recommended_strategy: Optional[str] = None
    
    class Config:
        from_attributes = True


class WholesaleDealUpdate(BaseModel):
    """Pydantic model for updating a wholesale deal."""
    status: Optional[DealStatusEnum] = None
    deal_score: Optional[float] = Field(None, ge=0, le=100)
    priority_level: Optional[str] = None
    arv_estimate: Optional[float] = None
    current_value_estimate: Optional[float] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    condition_score: Optional[float] = Field(None, ge=0, le=1)
    repair_estimate: Optional[float] = None
    repair_breakdown: Optional[Dict[str, Any]] = None
    renovation_timeline: Optional[int] = None
    max_allowable_offer: Optional[float] = None
    wholesale_fee: Optional[float] = None
    potential_profit: Optional[float] = None
    buyer_profit_estimate: Optional[float] = None
    offer_amount: Optional[float] = None
    contract_price: Optional[float] = None
    earnest_money: Optional[float] = None
    closing_date: Optional[datetime] = None
    assignment_fee: Optional[float] = None
    holding_costs: Optional[float] = None
    closing_costs: Optional[float] = None
    marketing_costs: Optional[float] = None
    target_buyer_type: Optional[str] = None
    buyer_id: Optional[uuid.UUID] = None
    buyer_name: Optional[str] = None
    buyer_contact: Optional[str] = None
    contract_date: Optional[datetime] = None
    marketing_start_date: Optional[datetime] = None
    assignment_date: Optional[datetime] = None
    actual_closing_date: Optional[datetime] = None
    actual_profit: Optional[float] = None
    roi_actual: Optional[float] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    assigned_to: Optional[str] = None
    strategies: Optional[List[Dict[str, Any]]] = None
    recommended_strategy: Optional[str] = None
    
    class Config:
        from_attributes = True


class WholesaleDealResponse(BaseModel):
    """Pydantic model for wholesale deal API responses."""
    id: uuid.UUID
    property_id: uuid.UUID
    lead_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    status: DealStatusEnum
    deal_score: Optional[float] = None
    priority_level: Optional[str] = None
    arv_estimate: Optional[float] = None
    current_value_estimate: Optional[float] = None
    confidence_score: Optional[float] = None
    condition_score: Optional[float] = None
    repair_estimate: Optional[float] = None
    repair_breakdown: Optional[Dict[str, Any]] = None
    renovation_timeline: Optional[int] = None
    max_allowable_offer: Optional[float] = None
    wholesale_fee: Optional[float] = None
    potential_profit: Optional[float] = None
    buyer_profit_estimate: Optional[float] = None
    offer_amount: Optional[float] = None
    contract_price: Optional[float] = None
    earnest_money: Optional[float] = None
    closing_date: Optional[datetime] = None
    assignment_fee: Optional[float] = None
    holding_costs: Optional[float] = None
    closing_costs: Optional[float] = None
    marketing_costs: Optional[float] = None
    total_costs: Optional[float] = None
    target_buyer_type: Optional[str] = None
    buyer_id: Optional[uuid.UUID] = None
    buyer_name: Optional[str] = None
    buyer_contact: Optional[str] = None
    contract_date: Optional[datetime] = None
    marketing_start_date: Optional[datetime] = None
    assignment_date: Optional[datetime] = None
    actual_closing_date: Optional[datetime] = None
    days_to_contract: Optional[int] = None
    days_to_assignment: Optional[int] = None
    actual_profit: Optional[float] = None
    roi_actual: Optional[float] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    assigned_to: Optional[str] = None
    strategies: Optional[List[Dict[str, Any]]] = None
    recommended_strategy: Optional[str] = None
    
    class Config:
        from_attributes = True


class RepairItemCreate(BaseModel):
    """Pydantic model for creating a repair item."""
    name: str
    category: str
    subcategory: Optional[str] = None
    description: Optional[str] = None
    unit: str
    cost_per_unit: float
    labor_cost_per_unit: Optional[float] = None
    material_cost_per_unit: Optional[float] = None
    region: Optional[str] = None
    cost_adjustment_factor: float = 1.0
    typical_quantity: Optional[float] = None
    difficulty_level: Optional[str] = None
    time_estimate: Optional[float] = None
    data_source: Optional[str] = None
    
    class Config:
        from_attributes = True


class RepairItemResponse(BaseModel):
    """Pydantic model for repair item API responses."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    name: str
    category: str
    subcategory: Optional[str] = None
    description: Optional[str] = None
    unit: str
    cost_per_unit: float
    labor_cost_per_unit: Optional[float] = None
    material_cost_per_unit: Optional[float] = None
    region: Optional[str] = None
    cost_adjustment_factor: float
    typical_quantity: Optional[float] = None
    difficulty_level: Optional[str] = None
    time_estimate: Optional[float] = None
    data_source: Optional[str] = None
    last_updated: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class InvestmentStrategyCreate(BaseModel):
    """Pydantic model for creating an investment strategy."""
    deal_id: uuid.UUID
    strategy_type: StrategyTypeEnum
    strategy_name: Optional[str] = None
    initial_investment: Optional[float] = None
    total_costs: Optional[float] = None
    projected_revenue: Optional[float] = None
    projected_profit: Optional[float] = None
    roi_estimate: Optional[float] = None
    timeline_months: Optional[int] = None
    exit_timeline: Optional[int] = None
    risk_level: Optional[str] = None
    risk_factors: Optional[List[str]] = None
    market_assumptions: Optional[Dict[str, Any]] = None
    sensitivity_analysis: Optional[Dict[str, Any]] = None
    strategy_data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class InvestmentStrategyResponse(BaseModel):
    """Pydantic model for investment strategy API responses."""
    id: uuid.UUID
    deal_id: uuid.UUID
    created_at: datetime
    strategy_type: StrategyTypeEnum
    strategy_name: Optional[str] = None
    initial_investment: Optional[float] = None
    total_costs: Optional[float] = None
    projected_revenue: Optional[float] = None
    projected_profit: Optional[float] = None
    roi_estimate: Optional[float] = None
    timeline_months: Optional[int] = None
    exit_timeline: Optional[int] = None
    risk_level: Optional[str] = None
    risk_factors: Optional[List[str]] = None
    market_assumptions: Optional[Dict[str, Any]] = None
    sensitivity_analysis: Optional[Dict[str, Any]] = None
    strategy_data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True