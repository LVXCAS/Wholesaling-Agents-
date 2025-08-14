"""
Lead Scoring Models for Real Estate Deal Sourcing

This module defines the data models for lead scoring, motivation analysis,
and deal potential estimation.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
import uuid
from datetime import datetime


class MotivationFactorEnum(str, Enum):
    """Motivation factors for property sellers"""
    FINANCIAL_DISTRESS = "financial_distress"
    DIVORCE = "divorce"
    DEATH_IN_FAMILY = "death_in_family"
    JOB_RELOCATION = "job_relocation"
    DOWNSIZING = "downsizing"
    UPSIZING = "upsizing"
    RETIREMENT = "retirement"
    HEALTH_ISSUES = "health_issues"
    INHERITED_PROPERTY = "inherited_property"
    TIRED_LANDLORD = "tired_landlord"
    PROPERTY_CONDITION = "property_condition"
    MARKET_TIMING = "market_timing"
    TAX_ISSUES = "tax_issues"
    FORECLOSURE_THREAT = "foreclosure_threat"
    BANKRUPTCY = "bankruptcy"
    BUSINESS_CLOSURE = "business_closure"
    MULTIPLE_PROPERTIES = "multiple_properties"
    VACANT_PROPERTY = "vacant_property"
    RENTAL_PROBLEMS = "rental_problems"
    MAINTENANCE_BURDEN = "maintenance_burden"


class DealPotentialEnum(str, Enum):
    """Deal potential categories"""
    EXCELLENT = "excellent"  # 80-100 score
    GOOD = "good"           # 60-79 score
    FAIR = "fair"           # 40-59 score
    POOR = "poor"           # 20-39 score
    VERY_POOR = "very_poor" # 0-19 score


class LeadSourceEnum(str, Enum):
    """Lead source types"""
    MLS = "mls"
    FORECLOSURE = "foreclosure"
    PUBLIC_RECORDS = "public_records"
    OFF_MARKET = "off_market"
    REFERRAL = "referral"
    MARKETING = "marketing"
    COLD_CALLING = "cold_calling"
    DIRECT_MAIL = "direct_mail"
    ONLINE_LEAD = "online_lead"
    NETWORKING = "networking"
    WHOLESALER = "wholesaler"
    AGENT_REFERRAL = "agent_referral"


class MotivationIndicator(BaseModel):
    """Individual motivation indicator"""
    factor: MotivationFactorEnum = Field(..., description="Type of motivation factor")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in this indicator (0-1)")
    weight: float = Field(default=1.0, ge=0.0, le=10.0, description="Weight of this factor (0-10)")
    evidence: Optional[str] = Field(None, description="Evidence supporting this indicator")
    source: Optional[str] = Field(None, description="Source of this information")
    detected_at: datetime = Field(default_factory=datetime.now)


class PropertyConditionScore(BaseModel):
    """Property condition assessment"""
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall condition score (0-100)")
    structural_score: float = Field(..., ge=0.0, le=100.0, description="Structural condition (0-100)")
    cosmetic_score: float = Field(..., ge=0.0, le=100.0, description="Cosmetic condition (0-100)")
    systems_score: float = Field(..., ge=0.0, le=100.0, description="Systems condition (0-100)")
    
    repair_needed: bool = Field(default=False, description="Whether repairs are needed")
    estimated_repair_cost: Optional[float] = Field(None, ge=0, description="Estimated repair cost")
    repair_urgency: Optional[str] = Field(None, description="Urgency of repairs (low/medium/high)")
    
    assessment_date: datetime = Field(default_factory=datetime.now)
    assessment_method: Optional[str] = Field(None, description="How condition was assessed")
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence in assessment")


class MarketMetrics(BaseModel):
    """Market-related metrics for lead scoring"""
    days_on_market: Optional[int] = Field(None, ge=0, description="Days property has been on market")
    price_reductions: Optional[int] = Field(None, ge=0, description="Number of price reductions")
    total_price_reduction: Optional[float] = Field(None, ge=0, description="Total price reduction amount")
    price_reduction_percentage: Optional[float] = Field(None, ge=0, description="Price reduction percentage")
    
    list_to_sale_ratio: Optional[float] = Field(None, ge=0, description="List price to sale price ratio")
    market_value_ratio: Optional[float] = Field(None, ge=0, description="List price to market value ratio")
    
    comparable_sales_count: Optional[int] = Field(None, ge=0, description="Number of comparable sales")
    market_activity_score: Optional[float] = Field(None, ge=0, le=100, description="Market activity score")
    
    seasonal_factor: Optional[float] = Field(None, ge=0, le=2, description="Seasonal market factor")
    market_trend: Optional[str] = Field(None, description="Market trend (rising/stable/declining)")


class FinancialIndicators(BaseModel):
    """Financial indicators for lead scoring"""
    equity_percentage: Optional[float] = Field(None, ge=0, le=100, description="Owner equity percentage")
    loan_to_value: Optional[float] = Field(None, ge=0, le=200, description="Loan to value ratio")
    monthly_payment: Optional[float] = Field(None, ge=0, description="Monthly mortgage payment")
    payment_to_income_ratio: Optional[float] = Field(None, ge=0, description="Payment to income ratio")
    
    tax_delinquency: bool = Field(default=False, description="Property tax delinquency")
    tax_amount_owed: Optional[float] = Field(None, ge=0, description="Amount of taxes owed")
    
    foreclosure_status: Optional[str] = Field(None, description="Foreclosure status")
    foreclosure_date: Optional[datetime] = Field(None, description="Foreclosure date if applicable")
    
    bankruptcy_history: bool = Field(default=False, description="Owner bankruptcy history")
    lien_amount: Optional[float] = Field(None, ge=0, description="Total lien amount")


class OwnerProfile(BaseModel):
    """Owner profile information for scoring"""
    ownership_duration: Optional[int] = Field(None, ge=0, description="Years of ownership")
    owner_occupied: Optional[bool] = Field(None, description="Whether owner occupied")
    out_of_state_owner: bool = Field(default=False, description="Owner lives out of state")
    
    property_count: Optional[int] = Field(None, ge=1, description="Number of properties owned")
    investor_profile: bool = Field(default=False, description="Whether owner is an investor")
    
    age_estimate: Optional[int] = Field(None, ge=18, le=120, description="Estimated owner age")
    life_stage: Optional[str] = Field(None, description="Life stage (young/middle/senior)")
    
    contact_attempts: int = Field(default=0, ge=0, description="Number of contact attempts")
    responsiveness_score: Optional[float] = Field(None, ge=0, le=100, description="Responsiveness score")
    
    previous_sales: Optional[int] = Field(None, ge=0, description="Number of previous property sales")
    sale_frequency: Optional[float] = Field(None, ge=0, description="Average years between sales")


class LeadScore(BaseModel):
    """Complete lead scoring result"""
    lead_id: uuid.UUID = Field(..., description="Lead identifier")
    property_id: Optional[uuid.UUID] = Field(None, description="Associated property ID")
    
    # Overall scoring
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall lead score (0-100)")
    deal_potential: DealPotentialEnum = Field(..., description="Deal potential category")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in scoring")
    
    # Component scores
    motivation_score: float = Field(..., ge=0.0, le=100.0, description="Motivation score")
    financial_score: float = Field(..., ge=0.0, le=100.0, description="Financial opportunity score")
    property_score: float = Field(..., ge=0.0, le=100.0, description="Property condition score")
    market_score: float = Field(..., ge=0.0, le=100.0, description="Market opportunity score")
    owner_score: float = Field(..., ge=0.0, le=100.0, description="Owner profile score")
    
    # Detailed analysis
    motivation_indicators: List[MotivationIndicator] = Field(default_factory=list)
    property_condition: Optional[PropertyConditionScore] = None
    market_metrics: Optional[MarketMetrics] = None
    financial_indicators: Optional[FinancialIndicators] = None
    owner_profile: Optional[OwnerProfile] = None
    
    # Metadata
    scored_at: datetime = Field(default_factory=datetime.now)
    scoring_version: str = Field(default="1.0", description="Version of scoring algorithm")
    data_sources: List[str] = Field(default_factory=list, description="Data sources used")
    
    # Recommendations
    recommended_actions: List[str] = Field(default_factory=list)
    priority_level: str = Field(default="medium", description="Priority level (low/medium/high/urgent)")
    estimated_close_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    estimated_profit_potential: Optional[float] = Field(None, ge=0)
    
    class Config:
        use_enum_values = True


class ScoringWeights(BaseModel):
    """Configurable weights for lead scoring components"""
    motivation_weight: float = Field(default=30.0, ge=0.0, le=100.0, description="Weight for motivation score")
    financial_weight: float = Field(default=25.0, ge=0.0, le=100.0, description="Weight for financial score")
    property_weight: float = Field(default=20.0, ge=0.0, le=100.0, description="Weight for property score")
    market_weight: float = Field(default=15.0, ge=0.0, le=100.0, description="Weight for market score")
    owner_weight: float = Field(default=10.0, ge=0.0, le=100.0, description="Weight for owner score")
    
    def validate_weights(self) -> bool:
        """Validate that weights sum to 100"""
        total = self.motivation_weight + self.financial_weight + self.property_weight + self.market_weight + self.owner_weight
        return abs(total - 100.0) < 0.01


class ScoringConfig(BaseModel):
    """Configuration for lead scoring algorithm"""
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    name: str = Field(..., description="Configuration name")
    description: Optional[str] = Field(None, description="Configuration description")
    
    weights: ScoringWeights = Field(default_factory=ScoringWeights)
    
    # Motivation factor weights
    motivation_factor_weights: Dict[MotivationFactorEnum, float] = Field(
        default_factory=lambda: {
            MotivationFactorEnum.FINANCIAL_DISTRESS: 10.0,
            MotivationFactorEnum.FORECLOSURE_THREAT: 9.5,
            MotivationFactorEnum.DIVORCE: 8.5,
            MotivationFactorEnum.DEATH_IN_FAMILY: 8.0,
            MotivationFactorEnum.JOB_RELOCATION: 7.5,
            MotivationFactorEnum.HEALTH_ISSUES: 7.0,
            MotivationFactorEnum.INHERITED_PROPERTY: 6.5,
            MotivationFactorEnum.TIRED_LANDLORD: 6.0,
            MotivationFactorEnum.RETIREMENT: 5.5,
            MotivationFactorEnum.PROPERTY_CONDITION: 5.0,
            MotivationFactorEnum.VACANT_PROPERTY: 4.5,
            MotivationFactorEnum.DOWNSIZING: 4.0,
            MotivationFactorEnum.UPSIZING: 3.5,
            MotivationFactorEnum.MARKET_TIMING: 3.0
        }
    )
    
    # Thresholds
    excellent_threshold: float = Field(default=80.0, ge=0.0, le=100.0)
    good_threshold: float = Field(default=60.0, ge=0.0, le=100.0)
    fair_threshold: float = Field(default=40.0, ge=0.0, le=100.0)
    poor_threshold: float = Field(default=20.0, ge=0.0, le=100.0)
    
    # Minimum data requirements
    min_confidence_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    require_motivation_indicators: bool = Field(default=False)
    require_financial_data: bool = Field(default=False)
    
    # Active status
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True


class LeadScoringBatch(BaseModel):
    """Batch lead scoring request"""
    lead_ids: List[uuid.UUID] = Field(..., description="List of lead IDs to score")
    config_id: Optional[uuid.UUID] = Field(None, description="Scoring configuration to use")
    force_rescore: bool = Field(default=False, description="Force rescoring even if recent score exists")
    
    
class LeadScoringBatchResult(BaseModel):
    """Batch lead scoring result"""
    total_leads: int = Field(..., ge=0)
    successful_scores: int = Field(..., ge=0)
    failed_scores: int = Field(..., ge=0)
    
    scores: List[LeadScore] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    
    processing_time: float = Field(..., ge=0.0, description="Processing time in seconds")
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class ScoringAnalytics(BaseModel):
    """Analytics for lead scoring performance"""
    total_leads_scored: int = Field(..., ge=0)
    average_score: float = Field(..., ge=0.0, le=100.0)
    
    score_distribution: Dict[DealPotentialEnum, int] = Field(default_factory=dict)
    
    top_motivation_factors: List[Dict[str, Any]] = Field(default_factory=list)
    conversion_rates: Dict[DealPotentialEnum, float] = Field(default_factory=dict)
    
    scoring_accuracy: Optional[float] = Field(None, ge=0.0, le=1.0)
    false_positive_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    false_negative_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    generated_at: datetime = Field(default_factory=datetime.now)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None