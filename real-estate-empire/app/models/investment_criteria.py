"""
Investment Criteria Models for Real Estate Deal Sourcing

This module defines the data models for investment criteria used to filter
and score potential real estate deals.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import uuid
from datetime import datetime


class PropertyTypeEnum(str, Enum):
    """Property types for investment criteria"""
    SINGLE_FAMILY = "single_family"
    MULTI_FAMILY = "multi_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    COMMERCIAL = "commercial"
    LAND = "land"


class StrategyTypeEnum(str, Enum):
    """Investment strategy types"""
    FLIP = "flip"
    RENTAL = "rental"
    WHOLESALE = "wholesale"
    BRRRR = "brrrr"
    BUY_HOLD = "buy_hold"


class CriteriaOperator(str, Enum):
    """Operators for criteria matching"""
    EQUALS = "equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    BETWEEN = "between"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"


class CriteriaRule(BaseModel):
    """Individual criteria rule"""
    field: str = Field(..., description="Property field to evaluate")
    operator: CriteriaOperator = Field(..., description="Comparison operator")
    value: Union[str, int, float, List[Any]] = Field(..., description="Value to compare against")
    weight: float = Field(default=1.0, ge=0.0, le=10.0, description="Weight for scoring (0-10)")
    required: bool = Field(default=False, description="Whether this rule is mandatory")
    
    @field_validator('value')
    @classmethod
    def validate_value_for_operator(cls, v, info):
        """Validate value matches operator requirements"""
        # Get operator from the model data
        if hasattr(info, 'data') and 'operator' in info.data:
            operator = info.data['operator']
            if operator == CriteriaOperator.BETWEEN and not isinstance(v, list):
                raise ValueError("BETWEEN operator requires a list of two values")
            if operator in [CriteriaOperator.IN, CriteriaOperator.NOT_IN] and not isinstance(v, list):
                raise ValueError("IN/NOT_IN operators require a list of values")
        return v


class GeographicCriteria(BaseModel):
    """Geographic criteria for property location"""
    states: Optional[List[str]] = Field(None, description="Allowed states")
    cities: Optional[List[str]] = Field(None, description="Allowed cities")
    zip_codes: Optional[List[str]] = Field(None, description="Allowed zip codes")
    max_distance_from_point: Optional[float] = Field(None, description="Max distance in miles from a point")
    center_lat: Optional[float] = Field(None, description="Center latitude for distance calculation")
    center_lng: Optional[float] = Field(None, description="Center longitude for distance calculation")
    exclude_states: Optional[List[str]] = Field(None, description="States to exclude")
    exclude_cities: Optional[List[str]] = Field(None, description="Cities to exclude")


class FinancialCriteria(BaseModel):
    """Financial criteria for investment evaluation"""
    min_price: Optional[float] = Field(None, ge=0, description="Minimum purchase price")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum purchase price")
    min_cap_rate: Optional[float] = Field(None, ge=0, description="Minimum cap rate (%)")
    min_cash_flow: Optional[float] = Field(None, description="Minimum monthly cash flow")
    min_roi: Optional[float] = Field(None, ge=0, description="Minimum ROI (%)")
    min_cash_on_cash: Optional[float] = Field(None, ge=0, description="Minimum cash-on-cash return (%)")
    max_ltv: Optional[float] = Field(None, ge=0, le=100, description="Maximum loan-to-value ratio (%)")
    min_equity_percentage: Optional[float] = Field(None, ge=0, le=100, description="Minimum equity percentage")
    max_repair_cost: Optional[float] = Field(None, ge=0, description="Maximum repair cost")
    min_arv: Optional[float] = Field(None, ge=0, description="Minimum after repair value")


class PropertyCriteria(BaseModel):
    """Physical property criteria"""
    property_types: Optional[List[PropertyTypeEnum]] = Field(None, description="Allowed property types")
    min_bedrooms: Optional[int] = Field(None, ge=0, description="Minimum bedrooms")
    max_bedrooms: Optional[int] = Field(None, ge=0, description="Maximum bedrooms")
    min_bathrooms: Optional[float] = Field(None, ge=0, description="Minimum bathrooms")
    max_bathrooms: Optional[float] = Field(None, ge=0, description="Maximum bathrooms")
    min_square_feet: Optional[int] = Field(None, ge=0, description="Minimum square footage")
    max_square_feet: Optional[int] = Field(None, ge=0, description="Maximum square footage")
    min_lot_size: Optional[float] = Field(None, ge=0, description="Minimum lot size (acres)")
    max_lot_size: Optional[float] = Field(None, ge=0, description="Maximum lot size (acres)")
    min_year_built: Optional[int] = Field(None, ge=1800, description="Minimum year built")
    max_year_built: Optional[int] = Field(None, ge=1800, description="Maximum year built")
    required_features: Optional[List[str]] = Field(None, description="Required property features")
    excluded_features: Optional[List[str]] = Field(None, description="Features to exclude")


class MarketCriteria(BaseModel):
    """Market and neighborhood criteria"""
    min_days_on_market: Optional[int] = Field(None, ge=0, description="Minimum days on market")
    max_days_on_market: Optional[int] = Field(None, ge=0, description="Maximum days on market")
    min_price_reduction: Optional[float] = Field(None, ge=0, description="Minimum price reduction (%)")
    distressed_only: Optional[bool] = Field(False, description="Only consider distressed properties")
    foreclosure_only: Optional[bool] = Field(False, description="Only consider foreclosures")
    off_market_only: Optional[bool] = Field(False, description="Only consider off-market properties")
    motivated_seller_indicators: Optional[List[str]] = Field(None, description="Required motivation indicators")


class InvestmentCriteria(BaseModel):
    """Complete investment criteria definition"""
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    name: str = Field(..., description="Criteria name/title")
    description: Optional[str] = Field(None, description="Criteria description")
    strategy: StrategyTypeEnum = Field(..., description="Primary investment strategy")
    
    # Criteria categories
    geographic: Optional[GeographicCriteria] = Field(None, description="Geographic criteria")
    financial: Optional[FinancialCriteria] = Field(None, description="Financial criteria")
    property: Optional[PropertyCriteria] = Field(None, description="Property criteria")
    market: Optional[MarketCriteria] = Field(None, description="Market criteria")
    
    # Custom rules
    custom_rules: Optional[List[CriteriaRule]] = Field(None, description="Custom criteria rules")
    
    # Metadata
    active: bool = Field(default=True, description="Whether criteria is active")
    priority: int = Field(default=1, ge=1, le=10, description="Criteria priority (1-10)")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(None, description="User who created criteria")
    
    class Config:
        use_enum_values = True


class CriteriaTemplate(BaseModel):
    """Template for common investment criteria"""
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    strategy: StrategyTypeEnum = Field(..., description="Investment strategy")
    criteria: InvestmentCriteria = Field(..., description="Template criteria")
    is_public: bool = Field(default=False, description="Whether template is publicly available")
    usage_count: int = Field(default=0, description="Number of times template has been used")
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(None, description="User who created template")
    
    class Config:
        use_enum_values = True


class CriteriaMatch(BaseModel):
    """Result of criteria matching against a property"""
    property_id: uuid.UUID = Field(..., description="Property ID that was evaluated")
    criteria_id: uuid.UUID = Field(..., description="Criteria ID used for evaluation")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall match score (0-100)")
    meets_required: bool = Field(..., description="Whether all required criteria are met")
    
    # Detailed scoring
    geographic_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    financial_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    property_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    market_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    custom_rules_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    
    # Rule-level results
    rule_results: Dict[str, Any] = Field(default_factory=dict, description="Individual rule evaluation results")
    failed_required_rules: List[str] = Field(default_factory=list, description="Required rules that failed")
    
    # Metadata
    evaluated_at: datetime = Field(default_factory=datetime.now)
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in the evaluation")


class CriteriaMatchSummary(BaseModel):
    """Summary of criteria matching results"""
    total_properties_evaluated: int = Field(..., ge=0)
    properties_meeting_criteria: int = Field(..., ge=0)
    average_score: float = Field(..., ge=0.0, le=100.0)
    top_matches: List[CriteriaMatch] = Field(default_factory=list)
    criteria_effectiveness: Dict[str, float] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.now)