"""
Analyst Agent Data Models
Shared data models for analyst agent and workflows
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class PropertyValuation(BaseModel):
    """Property valuation results"""
    arv: float = Field(description="After Repair Value")
    current_value: float = Field(description="Current market value")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in valuation")
    comp_count: int = Field(description="Number of comparable properties used")
    valuation_method: str = Field(description="Method used for valuation")
    price_per_sqft: Optional[float] = None
    market_adjustment: Optional[float] = None
    condition_adjustment: Optional[float] = None


class RepairEstimate(BaseModel):
    """Repair cost estimation"""
    total_cost: float = Field(description="Total estimated repair cost")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in estimate")
    line_items: Dict[str, float] = Field(default_factory=dict, description="Detailed repair items")
    contingency_percentage: float = Field(default=0.1, description="Contingency buffer")
    timeline_days: Optional[int] = None
    priority_repairs: List[str] = Field(default_factory=list)
    cosmetic_repairs: List[str] = Field(default_factory=list)


class FinancialMetrics(BaseModel):
    """Comprehensive financial analysis metrics"""
    purchase_price: float
    repair_cost: float
    total_investment: float
    after_repair_value: float
    
    # Rental metrics
    monthly_rent: Optional[float] = None
    monthly_expenses: Optional[float] = None
    monthly_cash_flow: Optional[float] = None
    annual_cash_flow: Optional[float] = None
    
    # Investment returns
    cap_rate: Optional[float] = None
    cash_on_cash_return: Optional[float] = None
    roi: Optional[float] = None
    gross_rent_multiplier: Optional[float] = None
    
    # Flip metrics
    flip_profit: Optional[float] = None
    flip_roi: Optional[float] = None
    flip_timeline_days: Optional[int] = None
    
    # Wholesale metrics
    wholesale_fee: Optional[float] = None
    wholesale_margin: Optional[float] = None


class InvestmentStrategy(BaseModel):
    """Investment strategy analysis"""
    strategy_type: str = Field(description="Type of investment strategy")
    potential_profit: float = Field(description="Expected profit")
    roi: float = Field(description="Return on investment")
    risk_level: float = Field(ge=0.0, le=10.0, description="Risk assessment (1-10)")
    timeline_days: int = Field(description="Expected timeline in days")
    funding_required: float = Field(description="Total funding needed")
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)


class PropertyAnalysis(BaseModel):
    """Comprehensive property analysis results"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    property_id: str
    analysis_date: datetime = Field(default_factory=datetime.now)
    
    # Core analysis components
    valuation: PropertyValuation
    repair_estimate: RepairEstimate
    financial_metrics: FinancialMetrics
    
    # Strategy analysis
    strategies: List[InvestmentStrategy] = Field(default_factory=list)
    recommended_strategy: Optional[str] = None
    
    # Market context
    comparable_properties: List[Dict[str, Any]] = Field(default_factory=list)
    market_conditions: Dict[str, Any] = Field(default_factory=dict)
    neighborhood_analysis: Dict[str, Any] = Field(default_factory=dict)
    
    # Risk assessment
    risk_factors: List[str] = Field(default_factory=list)
    overall_risk_score: float = Field(ge=0.0, le=10.0, default=5.0)
    
    # Final recommendation
    investment_recommendation: str = Field(description="proceed, caution, or reject")
    recommendation_reason: str = Field(description="Detailed reasoning for recommendation")
    confidence_level: float = Field(ge=0.0, le=1.0, description="Overall confidence in analysis")


class MarketAnalysis(BaseModel):
    """Market analysis for property context"""
    location: str
    median_home_price: Optional[float] = None
    price_trend_yoy: Optional[float] = None
    days_on_market: Optional[int] = None
    inventory_level: Optional[str] = None
    rental_demand: Optional[str] = None
    appreciation_forecast: Optional[float] = None
    market_temperature: Optional[str] = None  # "hot", "warm", "cool", "cold"