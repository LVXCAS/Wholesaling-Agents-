"""
Portfolio data models for the Real Estate Empire platform.
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


class PortfolioStatusEnum(str, Enum):
    """Enum for portfolio status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class PropertyInvestmentStatusEnum(str, Enum):
    """Enum for property investment status."""
    OWNED = "owned"
    UNDER_CONTRACT = "under_contract"
    SOLD = "sold"
    RENTED = "rented"
    VACANT = "vacant"
    REHAB = "rehab"


class PerformanceMetricTypeEnum(str, Enum):
    """Enum for performance metric types."""
    MONTHLY_CASH_FLOW = "monthly_cash_flow"
    CAP_RATE = "cap_rate"
    COC_RETURN = "coc_return"
    ROI = "roi"
    APPRECIATION = "appreciation"
    TOTAL_RETURN = "total_return"
    OCCUPANCY_RATE = "occupancy_rate"
    EXPENSE_RATIO = "expense_ratio"


class PortfolioDB(Base):
    """SQLAlchemy model for portfolio data."""
    __tablename__ = "portfolios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Basic Portfolio Information
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default=PortfolioStatusEnum.ACTIVE)
    
    # Portfolio Strategy
    investment_strategy = Column(String, nullable=True)  # e.g., "buy_and_hold", "flip", "wholesale"
    target_markets = Column(JSON, nullable=True)  # Array of target market areas
    investment_criteria = Column(JSON, nullable=True)  # Investment criteria settings
    
    # Portfolio Metrics (cached for performance)
    total_properties = Column(Integer, default=0)
    total_value = Column(Float, default=0.0)
    total_equity = Column(Float, default=0.0)
    total_debt = Column(Float, default=0.0)
    monthly_income = Column(Float, default=0.0)
    monthly_expenses = Column(Float, default=0.0)
    monthly_cash_flow = Column(Float, default=0.0)
    
    # Performance Metrics
    average_cap_rate = Column(Float, nullable=True)
    average_coc_return = Column(Float, nullable=True)
    average_roi = Column(Float, nullable=True)
    total_return_ytd = Column(Float, nullable=True)
    total_return_inception = Column(Float, nullable=True)
    
    # Risk Metrics
    diversification_score = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    
    # Metadata
    last_performance_update = Column(DateTime, nullable=True)
    
    # Relationships
    properties = relationship("PortfolioPropertyDB", back_populates="portfolio")
    performance_history = relationship("PortfolioPerformanceDB", back_populates="portfolio")
    
    def __repr__(self):
        return f"<PortfolioDB(id={self.id}, name={self.name}, properties={self.total_properties})>"


class PortfolioPropertyDB(Base):
    """SQLAlchemy model for properties in a portfolio."""
    __tablename__ = "portfolio_properties"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Investment Details
    acquisition_date = Column(DateTime, nullable=False)
    acquisition_price = Column(Float, nullable=False)
    closing_costs = Column(Float, default=0.0)
    rehab_costs = Column(Float, default=0.0)
    total_investment = Column(Float, nullable=False)  # acquisition + closing + rehab
    
    # Current Status
    status = Column(String, nullable=False, default=PropertyInvestmentStatusEnum.OWNED)
    current_value = Column(Float, nullable=True)
    current_debt = Column(Float, default=0.0)
    current_equity = Column(Float, nullable=True)
    
    # Income and Expenses
    monthly_rent = Column(Float, default=0.0)
    monthly_expenses = Column(Float, default=0.0)
    monthly_cash_flow = Column(Float, default=0.0)
    
    # Performance Metrics
    cap_rate = Column(Float, nullable=True)
    coc_return = Column(Float, nullable=True)  # Cash-on-Cash return
    roi = Column(Float, nullable=True)
    appreciation_rate = Column(Float, nullable=True)
    
    # Property Management
    property_manager = Column(String, nullable=True)
    management_fee_percent = Column(Float, default=0.0)
    
    # Exit Strategy
    exit_strategy = Column(String, nullable=True)  # e.g., "hold", "sell", "refinance"
    target_exit_date = Column(DateTime, nullable=True)
    target_exit_value = Column(Float, nullable=True)
    
    # Metadata
    last_valuation_date = Column(DateTime, nullable=True)
    last_performance_update = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    portfolio = relationship("PortfolioDB", back_populates="properties")
    property = relationship("PropertyDB")
    performance_history = relationship("PropertyPerformanceDB", back_populates="portfolio_property")
    
    def __repr__(self):
        return f"<PortfolioPropertyDB(id={self.id}, portfolio_id={self.portfolio_id}, property_id={self.property_id})>"


class PropertyPerformanceDB(Base):
    """SQLAlchemy model for tracking property performance over time."""
    __tablename__ = "property_performance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_property_id = Column(UUID(as_uuid=True), ForeignKey("portfolio_properties.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Performance Period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    period_type = Column(String, nullable=False)  # "monthly", "quarterly", "annual"
    
    # Financial Performance
    rental_income = Column(Float, default=0.0)
    other_income = Column(Float, default=0.0)
    total_income = Column(Float, default=0.0)
    
    # Expenses
    mortgage_payment = Column(Float, default=0.0)
    property_taxes = Column(Float, default=0.0)
    insurance = Column(Float, default=0.0)
    maintenance_repairs = Column(Float, default=0.0)
    property_management = Column(Float, default=0.0)
    utilities = Column(Float, default=0.0)
    other_expenses = Column(Float, default=0.0)
    total_expenses = Column(Float, default=0.0)
    
    # Net Performance
    net_cash_flow = Column(Float, default=0.0)
    
    # Property Value
    estimated_value = Column(Float, nullable=True)
    value_change = Column(Float, nullable=True)
    value_change_percent = Column(Float, nullable=True)
    
    # Calculated Metrics
    cap_rate = Column(Float, nullable=True)
    coc_return = Column(Float, nullable=True)
    roi = Column(Float, nullable=True)
    
    # Occupancy
    occupancy_rate = Column(Float, nullable=True)
    vacancy_days = Column(Integer, default=0)
    
    # Relationship
    portfolio_property = relationship("PortfolioPropertyDB", back_populates="performance_history")
    
    def __repr__(self):
        return f"<PropertyPerformanceDB(id={self.id}, period={self.period_start} to {self.period_end})>"


class PortfolioPerformanceDB(Base):
    """SQLAlchemy model for tracking portfolio-level performance over time."""
    __tablename__ = "portfolio_performance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Performance Period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    period_type = Column(String, nullable=False)  # "monthly", "quarterly", "annual"
    
    # Portfolio Metrics
    total_properties = Column(Integer, default=0)
    total_value = Column(Float, default=0.0)
    total_equity = Column(Float, default=0.0)
    total_debt = Column(Float, default=0.0)
    
    # Income and Cash Flow
    total_income = Column(Float, default=0.0)
    total_expenses = Column(Float, default=0.0)
    net_cash_flow = Column(Float, default=0.0)
    
    # Performance Metrics
    average_cap_rate = Column(Float, nullable=True)
    average_coc_return = Column(Float, nullable=True)
    average_roi = Column(Float, nullable=True)
    total_return = Column(Float, nullable=True)
    
    # Value Changes
    appreciation = Column(Float, nullable=True)
    appreciation_percent = Column(Float, nullable=True)
    
    # Risk Metrics
    diversification_score = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    
    # Occupancy
    average_occupancy_rate = Column(Float, nullable=True)
    
    # Relationship
    portfolio = relationship("PortfolioDB", back_populates="performance_history")
    
    def __repr__(self):
        return f"<PortfolioPerformanceDB(id={self.id}, portfolio_id={self.portfolio_id}, period={self.period_start})>"


# Pydantic models for API requests and responses

class PortfolioCreate(BaseModel):
    """Pydantic model for creating a portfolio."""
    name: str
    description: Optional[str] = None
    investment_strategy: Optional[str] = None
    target_markets: Optional[List[str]] = None
    investment_criteria: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class PortfolioUpdate(BaseModel):
    """Pydantic model for updating a portfolio."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[PortfolioStatusEnum] = None
    investment_strategy: Optional[str] = None
    target_markets: Optional[List[str]] = None
    investment_criteria: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class PortfolioResponse(BaseModel):
    """Pydantic model for portfolio API responses."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    name: str
    description: Optional[str] = None
    status: PortfolioStatusEnum
    investment_strategy: Optional[str] = None
    target_markets: Optional[List[str]] = None
    investment_criteria: Optional[Dict[str, Any]] = None
    total_properties: int
    total_value: float
    total_equity: float
    total_debt: float
    monthly_income: float
    monthly_expenses: float
    monthly_cash_flow: float
    average_cap_rate: Optional[float] = None
    average_coc_return: Optional[float] = None
    average_roi: Optional[float] = None
    total_return_ytd: Optional[float] = None
    total_return_inception: Optional[float] = None
    diversification_score: Optional[float] = None
    risk_score: Optional[float] = None
    last_performance_update: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PortfolioPropertyCreate(BaseModel):
    """Pydantic model for adding a property to a portfolio."""
    property_id: uuid.UUID
    acquisition_date: datetime
    acquisition_price: float
    closing_costs: float = 0.0
    rehab_costs: float = 0.0
    monthly_rent: float = 0.0
    monthly_expenses: float = 0.0
    property_manager: Optional[str] = None
    management_fee_percent: float = 0.0
    exit_strategy: Optional[str] = None
    target_exit_date: Optional[datetime] = None
    target_exit_value: Optional[float] = None
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class PortfolioPropertyUpdate(BaseModel):
    """Pydantic model for updating a portfolio property."""
    status: Optional[PropertyInvestmentStatusEnum] = None
    current_value: Optional[float] = None
    current_debt: Optional[float] = None
    monthly_rent: Optional[float] = None
    monthly_expenses: Optional[float] = None
    property_manager: Optional[str] = None
    management_fee_percent: Optional[float] = None
    exit_strategy: Optional[str] = None
    target_exit_date: Optional[datetime] = None
    target_exit_value: Optional[float] = None
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class PortfolioPropertyResponse(BaseModel):
    """Pydantic model for portfolio property API responses."""
    id: uuid.UUID
    portfolio_id: uuid.UUID
    property_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    acquisition_date: datetime
    acquisition_price: float
    closing_costs: float
    rehab_costs: float
    total_investment: float
    status: PropertyInvestmentStatusEnum
    current_value: Optional[float] = None
    current_debt: float
    current_equity: Optional[float] = None
    monthly_rent: float
    monthly_expenses: float
    monthly_cash_flow: float
    cap_rate: Optional[float] = None
    coc_return: Optional[float] = None
    roi: Optional[float] = None
    appreciation_rate: Optional[float] = None
    property_manager: Optional[str] = None
    management_fee_percent: float
    exit_strategy: Optional[str] = None
    target_exit_date: Optional[datetime] = None
    target_exit_value: Optional[float] = None
    last_valuation_date: Optional[datetime] = None
    last_performance_update: Optional[datetime] = None
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class PropertyPerformanceCreate(BaseModel):
    """Pydantic model for creating property performance data."""
    portfolio_property_id: uuid.UUID
    period_start: datetime
    period_end: datetime
    period_type: str
    rental_income: float = 0.0
    other_income: float = 0.0
    mortgage_payment: float = 0.0
    property_taxes: float = 0.0
    insurance: float = 0.0
    maintenance_repairs: float = 0.0
    property_management: float = 0.0
    utilities: float = 0.0
    other_expenses: float = 0.0
    estimated_value: Optional[float] = None
    occupancy_rate: Optional[float] = None
    vacancy_days: int = 0
    
    class Config:
        from_attributes = True


class PropertyPerformanceResponse(BaseModel):
    """Pydantic model for property performance API responses."""
    id: uuid.UUID
    portfolio_property_id: uuid.UUID
    created_at: datetime
    period_start: datetime
    period_end: datetime
    period_type: str
    rental_income: float
    other_income: float
    total_income: float
    mortgage_payment: float
    property_taxes: float
    insurance: float
    maintenance_repairs: float
    property_management: float
    utilities: float
    other_expenses: float
    total_expenses: float
    net_cash_flow: float
    estimated_value: Optional[float] = None
    value_change: Optional[float] = None
    value_change_percent: Optional[float] = None
    cap_rate: Optional[float] = None
    coc_return: Optional[float] = None
    roi: Optional[float] = None
    occupancy_rate: Optional[float] = None
    vacancy_days: int
    
    class Config:
        from_attributes = True


class PortfolioSummary(BaseModel):
    """Pydantic model for portfolio summary data."""
    portfolio: PortfolioResponse
    properties: List[PortfolioPropertyResponse]
    performance_metrics: Dict[str, Any]
    recent_performance: List[PropertyPerformanceResponse]
    
    class Config:
        from_attributes = True


class PerformanceBenchmark(BaseModel):
    """Pydantic model for performance benchmarking."""
    metric_name: str
    portfolio_value: float
    benchmark_value: float
    percentile_rank: float
    comparison_result: str  # "above", "below", "at" benchmark
    
    class Config:
        from_attributes = True


class PortfolioAnalytics(BaseModel):
    """Pydantic model for portfolio analytics data."""
    portfolio_id: uuid.UUID
    total_return_ytd: float
    total_return_inception: float
    cash_flow_trend: List[Dict[str, Any]]
    value_trend: List[Dict[str, Any]]
    performance_by_property: List[Dict[str, Any]]
    benchmarks: List[PerformanceBenchmark]
    risk_metrics: Dict[str, Any]
    diversification_analysis: Dict[str, Any]
    
    class Config:
        from_attributes = True