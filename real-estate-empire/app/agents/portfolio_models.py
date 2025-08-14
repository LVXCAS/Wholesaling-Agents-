"""
Portfolio Agent Data Models
Pydantic models for portfolio management, performance tracking, and optimization
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum

from pydantic import BaseModel, Field


class PortfolioTypeEnum(str, Enum):
    """Types of real estate portfolios"""
    RENTAL = "rental"
    FLIP = "flip"
    WHOLESALE = "wholesale"
    MIXED = "mixed"
    COMMERCIAL = "commercial"
    RESIDENTIAL = "residential"


class PropertyStrategyEnum(str, Enum):
    """Investment strategies for properties"""
    BUY_AND_HOLD = "buy_and_hold"
    FLIP = "flip"
    WHOLESALE = "wholesale"
    BRRRR = "brrrr"
    RENT_TO_OWN = "rent_to_own"
    SHORT_TERM_RENTAL = "short_term_rental"


class RiskLevelEnum(str, Enum):
    """Risk levels for investments"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class MarketCycleEnum(str, Enum):
    """Market cycle phases"""
    RECOVERY = "recovery"
    EXPANSION = "expansion"
    HYPER_SUPPLY = "hyper_supply"
    RECESSION = "recession"


class Portfolio(BaseModel):
    """Main portfolio model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    portfolio_type: PortfolioTypeEnum = PortfolioTypeEnum.MIXED
    
    # Properties
    properties: List[Dict[str, Any]] = Field(default_factory=list)
    total_properties: int = 0
    
    # Financial Metrics
    total_value: float = 0.0
    total_equity: float = 0.0
    total_debt: float = 0.0
    monthly_cash_flow: float = 0.0
    annual_cash_flow: float = 0.0
    
    # Performance Metrics
    average_cap_rate: float = 0.0
    average_coc_return: float = 0.0  # Cash-on-cash return
    average_roi: float = 0.0
    total_return: float = 0.0
    
    # Diversification
    geographic_diversification: Dict[str, float] = Field(default_factory=dict)
    property_type_diversification: Dict[str, float] = Field(default_factory=dict)
    strategy_diversification: Dict[str, float] = Field(default_factory=dict)
    
    # Risk Metrics
    risk_score: float = 0.0
    leverage_ratio: float = 0.0
    concentration_risk: float = 0.0
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    owner_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PropertyPerformance(BaseModel):
    """Individual property performance tracking"""
    property_id: str
    portfolio_id: str
    
    # Basic Property Info
    address: str
    city: str
    state: str
    property_type: str
    strategy: PropertyStrategyEnum
    
    # Acquisition Data
    acquisition_date: datetime
    acquisition_cost: float
    initial_investment: float  # Including repairs, closing costs
    
    # Current Valuation
    current_value: float
    estimated_arv: Optional[float] = None
    last_appraisal_date: Optional[datetime] = None
    
    # Financial Performance
    monthly_rent: float = 0.0
    monthly_expenses: float = 0.0
    monthly_cash_flow: float = 0.0
    annual_cash_flow: float = 0.0
    
    # Returns
    cap_rate: float = 0.0
    cash_on_cash_return: float = 0.0
    total_return: float = 0.0
    annualized_return: float = 0.0
    
    # Equity and Appreciation
    current_equity: float = 0.0
    appreciation: float = 0.0
    appreciation_percentage: float = 0.0
    
    # Operational Metrics
    vacancy_rate: float = 0.0
    maintenance_costs_ytd: float = 0.0
    capex_costs_ytd: float = 0.0
    
    # Performance Indicators
    performance_score: float = 0.0  # 0-100 scale
    benchmark_comparison: float = 0.0  # vs market benchmark
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PerformanceMetrics(BaseModel):
    """Comprehensive performance metrics for portfolio"""
    portfolio_id: str
    calculation_date: datetime = Field(default_factory=datetime.now)
    
    # Portfolio Size
    total_properties: int
    total_units: int = 0  # For multi-family properties
    
    # Financial Metrics
    total_value: float
    total_equity: float
    total_debt: float
    loan_to_value: float = 0.0
    
    # Income Metrics
    gross_monthly_rent: float
    net_monthly_rent: float
    monthly_expenses: float
    monthly_cash_flow: float
    annual_cash_flow: float
    
    # Return Metrics
    portfolio_cap_rate: float
    portfolio_coc_return: float
    portfolio_roi: float
    total_return_percentage: float
    
    # Appreciation Metrics
    total_appreciation: float
    appreciation_percentage: float
    average_annual_appreciation: float
    
    # Operational Metrics
    average_vacancy_rate: float
    average_days_vacant: float
    maintenance_cost_percentage: float
    capex_percentage: float
    
    # Efficiency Metrics
    rent_per_sqft: float = 0.0
    value_per_sqft: float = 0.0
    cash_flow_per_unit: float = 0.0
    
    # Benchmark Comparisons
    vs_reit_performance: float = 0.0
    vs_stock_market: float = 0.0
    vs_local_market: float = 0.0
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PortfolioAnalysis(BaseModel):
    """Comprehensive portfolio analysis results"""
    portfolio_id: str
    analysis_date: datetime = Field(default_factory=datetime.now)
    analysis_type: str = "comprehensive"
    
    # Performance Summary
    performance_metrics: PerformanceMetrics
    property_performances: List[PropertyPerformance]
    
    # Strengths and Weaknesses
    top_performers: List[Dict[str, Any]] = Field(default_factory=list)
    underperformers: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Diversification Analysis
    geographic_concentration: Dict[str, float] = Field(default_factory=dict)
    property_type_concentration: Dict[str, float] = Field(default_factory=dict)
    strategy_concentration: Dict[str, float] = Field(default_factory=dict)
    diversification_score: float = 0.0
    
    # Risk Analysis
    risk_factors: List[str] = Field(default_factory=list)
    risk_score: float = 0.0
    risk_level: RiskLevelEnum = RiskLevelEnum.MODERATE
    
    # Market Context
    market_conditions: Dict[str, Any] = Field(default_factory=dict)
    market_cycle_phase: MarketCycleEnum = MarketCycleEnum.EXPANSION
    
    # Key Insights
    key_insights: List[str] = Field(default_factory=list)
    improvement_opportunities: List[str] = Field(default_factory=list)
    
    # Confidence and Quality
    confidence_score: float = 0.8
    data_quality_score: float = 0.8
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class InvestmentRecommendation(BaseModel):
    """Investment recommendation for portfolio optimization"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    recommendation_type: str  # "buy", "sell", "hold", "improve", "refinance"
    priority: str = "medium"  # "low", "medium", "high", "critical"
    
    # Target
    property_id: Optional[str] = None
    target_description: str
    
    # Recommendation Details
    title: str
    description: str
    rationale: str
    expected_impact: str
    
    # Financial Projections
    estimated_cost: float = 0.0
    estimated_return: float = 0.0
    payback_period_months: Optional[int] = None
    roi_projection: float = 0.0
    
    # Implementation
    implementation_steps: List[str] = Field(default_factory=list)
    timeline_months: int = 1
    required_resources: List[str] = Field(default_factory=list)
    
    # Risk Assessment
    risk_level: RiskLevelEnum = RiskLevelEnum.MODERATE
    risk_factors: List[str] = Field(default_factory=list)
    mitigation_strategies: List[str] = Field(default_factory=list)
    
    # Metrics
    confidence_score: float = 0.8
    urgency_score: float = 0.5
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "pending"  # "pending", "approved", "rejected", "implemented"
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PortfolioOptimization(BaseModel):
    """Portfolio optimization analysis and recommendations"""
    portfolio_id: str
    optimization_date: datetime = Field(default_factory=datetime.now)
    optimization_type: str = "comprehensive"
    
    # Current State Analysis
    current_performance: PerformanceMetrics
    current_allocation: Dict[str, float] = Field(default_factory=dict)
    
    # Optimization Goals
    target_cap_rate: float = 0.08
    target_cash_flow: float = 1000.0
    target_roi: float = 0.15
    risk_tolerance: RiskLevelEnum = RiskLevelEnum.MODERATE
    
    # Recommended Changes
    recommendations: List[InvestmentRecommendation] = Field(default_factory=list)
    rebalancing_suggestions: Dict[str, Any] = Field(default_factory=dict)
    
    # Projected Outcomes
    projected_performance: Dict[str, float] = Field(default_factory=dict)
    improvement_potential: Dict[str, float] = Field(default_factory=dict)
    
    # Implementation Plan
    phase_1_actions: List[str] = Field(default_factory=list)
    phase_2_actions: List[str] = Field(default_factory=list)
    phase_3_actions: List[str] = Field(default_factory=list)
    
    # Timeline and Resources
    implementation_timeline_months: int = 12
    required_capital: float = 0.0
    expected_roi: float = 0.0
    
    # Risk Assessment
    optimization_risks: List[str] = Field(default_factory=list)
    risk_mitigation: List[str] = Field(default_factory=list)
    
    # Confidence Metrics
    confidence_score: float = 0.8
    success_probability: float = 0.7
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RiskAssessment(BaseModel):
    """Portfolio risk assessment"""
    portfolio_id: str
    assessment_date: datetime = Field(default_factory=datetime.now)
    
    # Overall Risk Metrics
    overall_risk_score: float = 0.0  # 0-100 scale
    risk_level: RiskLevelEnum = RiskLevelEnum.MODERATE
    
    # Risk Categories
    market_risk: float = 0.0
    credit_risk: float = 0.0
    liquidity_risk: float = 0.0
    operational_risk: float = 0.0
    concentration_risk: float = 0.0
    leverage_risk: float = 0.0
    
    # Specific Risk Factors
    risk_factors: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Geographic Risk
    geographic_concentration: Dict[str, float] = Field(default_factory=dict)
    geographic_risk_score: float = 0.0
    
    # Property Type Risk
    property_type_concentration: Dict[str, float] = Field(default_factory=dict)
    property_type_risk_score: float = 0.0
    
    # Financial Risk
    leverage_ratio: float = 0.0
    debt_service_coverage: float = 0.0
    cash_reserves_ratio: float = 0.0
    
    # Market Risk
    market_cycle_risk: float = 0.0
    interest_rate_sensitivity: float = 0.0
    economic_sensitivity: float = 0.0
    
    # Mitigation Strategies
    recommended_mitigations: List[str] = Field(default_factory=list)
    insurance_recommendations: List[str] = Field(default_factory=list)
    diversification_recommendations: List[str] = Field(default_factory=list)
    
    # Stress Testing
    recession_scenario_impact: float = 0.0
    interest_rate_shock_impact: float = 0.0
    vacancy_shock_impact: float = 0.0
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MarketAnalysis(BaseModel):
    """Market analysis for portfolio context"""
    analysis_date: datetime = Field(default_factory=datetime.now)
    geographic_scope: str
    
    # Market Metrics
    median_home_price: float = 0.0
    price_appreciation_yoy: float = 0.0
    days_on_market: int = 0
    inventory_months: float = 0.0
    
    # Rental Market
    median_rent: float = 0.0
    rent_growth_yoy: float = 0.0
    vacancy_rate: float = 0.0
    cap_rate_average: float = 0.0
    
    # Economic Indicators
    unemployment_rate: float = 0.0
    population_growth: float = 0.0
    job_growth: float = 0.0
    income_growth: float = 0.0
    
    # Investment Climate
    investor_activity_level: str = "moderate"
    foreclosure_rate: float = 0.0
    new_construction_rate: float = 0.0
    
    # Market Cycle
    market_cycle_phase: MarketCycleEnum = MarketCycleEnum.EXPANSION
    cycle_position: float = 0.5  # 0-1 scale within cycle
    
    # Trends and Predictions
    price_trend: str = "stable"  # "declining", "stable", "rising"
    rent_trend: str = "stable"
    market_temperature: str = "balanced"  # "cold", "cool", "balanced", "warm", "hot"
    
    # Investment Recommendations
    buy_recommendation: str = "neutral"  # "strong_buy", "buy", "neutral", "sell", "strong_sell"
    hold_recommendation: str = "hold"
    sell_recommendation: str = "neutral"
    
    # Risk Factors
    market_risks: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    
    # Data Quality
    data_sources: List[str] = Field(default_factory=list)
    confidence_score: float = 0.8
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PortfolioReport(BaseModel):
    """Comprehensive portfolio report"""
    portfolio_id: str
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_type: str = "monthly"
    generated_at: datetime = Field(default_factory=datetime.now)
    
    # Executive Summary
    executive_summary: str
    key_highlights: List[str] = Field(default_factory=list)
    
    # Performance Data
    performance_metrics: PerformanceMetrics
    performance_trends: Dict[str, List[float]] = Field(default_factory=dict)
    
    # Analysis Results
    portfolio_analysis: PortfolioAnalysis
    risk_assessment: RiskAssessment
    market_analysis: MarketAnalysis
    
    # Recommendations
    optimization_recommendations: List[InvestmentRecommendation] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)
    
    # Appendices
    property_details: List[PropertyPerformance] = Field(default_factory=list)
    market_data: Dict[str, Any] = Field(default_factory=dict)
    assumptions: List[str] = Field(default_factory=list)
    
    # Report Metadata
    report_period_start: datetime
    report_period_end: datetime
    next_report_date: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Utility Models

class PortfolioComparison(BaseModel):
    """Compare multiple portfolios or time periods"""
    comparison_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    comparison_type: str  # "portfolio_vs_portfolio", "time_period", "benchmark"
    comparison_date: datetime = Field(default_factory=datetime.now)
    
    # Comparison Data
    baseline: Dict[str, Any]
    comparison_targets: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metrics Comparison
    performance_comparison: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    risk_comparison: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    
    # Analysis
    key_differences: List[str] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PortfolioGoals(BaseModel):
    """Portfolio investment goals and targets"""
    portfolio_id: str
    goals_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Financial Goals
    target_portfolio_value: float = 0.0
    target_monthly_cash_flow: float = 0.0
    target_annual_return: float = 0.15
    target_cap_rate: float = 0.08
    
    # Growth Goals
    target_property_count: int = 0
    target_geographic_markets: int = 3
    target_property_types: List[str] = Field(default_factory=list)
    
    # Timeline
    goal_timeline_years: int = 5
    milestone_dates: Dict[str, datetime] = Field(default_factory=dict)
    
    # Risk Parameters
    max_risk_tolerance: RiskLevelEnum = RiskLevelEnum.MODERATE
    max_leverage_ratio: float = 0.8
    min_cash_reserves: float = 50000.0
    
    # Strategy Preferences
    preferred_strategies: List[PropertyStrategyEnum] = Field(default_factory=list)
    excluded_strategies: List[PropertyStrategyEnum] = Field(default_factory=list)
    
    # Progress Tracking
    current_progress: Dict[str, float] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }