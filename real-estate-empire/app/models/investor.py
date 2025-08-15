"""
Investor management data models for the Real Estate Empire platform.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class InvestorTypeEnum(str, Enum):
    """Types of investors"""
    INDIVIDUAL = "individual"
    INSTITUTIONAL = "institutional"
    FAMILY_OFFICE = "family_office"
    FUND = "fund"
    SYNDICATE = "syndicate"


class InvestmentPreferenceEnum(str, Enum):
    """Investment preferences"""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    MIXED_USE = "mixed_use"
    LAND = "land"
    DEVELOPMENT = "development"
    DISTRESSED = "distressed"
    TURNKEY = "turnkey"


class RiskToleranceEnum(str, Enum):
    """Risk tolerance levels"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class InvestorStatusEnum(str, Enum):
    """Investor relationship status"""
    PROSPECT = "prospect"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class CommunicationPreferenceEnum(str, Enum):
    """Communication preferences"""
    EMAIL = "email"
    PHONE = "phone"
    TEXT = "text"
    IN_PERSON = "in_person"
    VIDEO_CALL = "video_call"


class InvestorProfile(BaseModel):
    """Core investor profile information"""
    id: UUID = Field(default_factory=uuid4)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    phone: Optional[str] = Field(None, max_length=20)
    company: Optional[str] = Field(None, max_length=200)
    title: Optional[str] = Field(None, max_length=100)
    
    # Investor classification
    investor_type: InvestorTypeEnum
    status: InvestorStatusEnum = InvestorStatusEnum.PROSPECT
    
    # Investment preferences
    investment_preferences: List[InvestmentPreferenceEnum] = Field(default_factory=list)
    risk_tolerance: RiskToleranceEnum = RiskToleranceEnum.MODERATE
    min_investment: Optional[Decimal] = Field(None, ge=0)
    max_investment: Optional[Decimal] = Field(None, ge=0)
    preferred_markets: List[str] = Field(default_factory=list)
    
    # Communication preferences
    communication_preferences: List[CommunicationPreferenceEnum] = Field(default_factory=list)
    preferred_contact_time: Optional[str] = None
    timezone: Optional[str] = None
    
    # Financial information
    net_worth: Optional[Decimal] = Field(None, ge=0)
    liquid_capital: Optional[Decimal] = Field(None, ge=0)
    annual_income: Optional[Decimal] = Field(None, ge=0)
    
    # Metadata
    source: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('max_investment')
    def validate_investment_range(cls, v, values):
        if v is not None and 'min_investment' in values and values['min_investment'] is not None:
            if v < values['min_investment']:
                raise ValueError('max_investment must be greater than or equal to min_investment')
        return v

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class InvestmentHistory(BaseModel):
    """Track investor's investment history"""
    id: UUID = Field(default_factory=uuid4)
    investor_id: UUID
    deal_id: UUID
    investment_amount: Decimal = Field(..., ge=0)
    investment_date: datetime
    expected_return: Optional[Decimal] = None
    actual_return: Optional[Decimal] = None
    status: str  # active, completed, exited
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InvestorCommunication(BaseModel):
    """Track communications with investors"""
    id: UUID = Field(default_factory=uuid4)
    investor_id: UUID
    communication_type: CommunicationPreferenceEnum
    subject: str
    content: str
    direction: str  # inbound, outbound
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    deal_id: Optional[UUID] = None
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InvestorPerformanceMetrics(BaseModel):
    """Performance metrics for investor relationships"""
    investor_id: UUID
    total_investments: int = 0
    total_invested: Decimal = Field(default=Decimal('0'), ge=0)
    total_returns: Decimal = Field(default=Decimal('0'))
    average_roi: Optional[Decimal] = None
    active_investments: int = 0
    completed_investments: int = 0
    last_investment_date: Optional[datetime] = None
    lifetime_value: Decimal = Field(default=Decimal('0'))
    communication_frequency: Optional[float] = None  # communications per month
    response_rate: Optional[float] = None  # percentage
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


class DealInvestorMatch(BaseModel):
    """Represents a match between a deal and an investor"""
    id: UUID = Field(default_factory=uuid4)
    deal_id: UUID
    investor_id: UUID
    match_score: float = Field(..., ge=0, le=1)
    match_reasons: List[str] = Field(default_factory=list)
    investment_preferences_match: Dict[str, bool] = Field(default_factory=dict)
    risk_assessment_match: bool = False
    financial_capacity_match: bool = False
    geographic_preference_match: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    contacted: bool = False
    contacted_at: Optional[datetime] = None
    response: Optional[str] = None
    response_at: Optional[datetime] = None


class InvestorDealPresentation(BaseModel):
    """Track deal presentations sent to investors"""
    id: UUID = Field(default_factory=uuid4)
    investor_id: UUID
    deal_id: UUID
    presentation_type: str  # email, pdf, video, meeting
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    opened: bool = False
    opened_at: Optional[datetime] = None
    downloaded: bool = False
    downloaded_at: Optional[datetime] = None
    response_received: bool = False
    response_at: Optional[datetime] = None
    investment_decision: Optional[str] = None  # interested, not_interested, maybe
    follow_up_scheduled: bool = False
    follow_up_date: Optional[datetime] = None


class InvestorSearchCriteria(BaseModel):
    """Criteria for searching and filtering investors"""
    investor_types: Optional[List[InvestorTypeEnum]] = None
    statuses: Optional[List[InvestorStatusEnum]] = None
    investment_preferences: Optional[List[InvestmentPreferenceEnum]] = None
    risk_tolerance: Optional[List[RiskToleranceEnum]] = None
    min_investment_capacity: Optional[Decimal] = None
    max_investment_capacity: Optional[Decimal] = None
    preferred_markets: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    last_contact_days: Optional[int] = None  # contacted within X days
    min_total_invested: Optional[Decimal] = None
    min_roi: Optional[Decimal] = None


class InvestorAnalytics(BaseModel):
    """Analytics data for investor management"""
    total_investors: int = 0
    active_investors: int = 0
    prospect_investors: int = 0
    total_invested_capital: Decimal = Field(default=Decimal('0'))
    average_investment_size: Decimal = Field(default=Decimal('0'))
    top_performing_investors: List[Dict[str, Any]] = Field(default_factory=list)
    investor_acquisition_rate: Optional[float] = None  # new investors per month
    investor_retention_rate: Optional[float] = None  # percentage
    communication_metrics: Dict[str, Any] = Field(default_factory=dict)
    geographic_distribution: Dict[str, int] = Field(default_factory=dict)
    investment_preference_distribution: Dict[str, int] = Field(default_factory=dict)
    calculated_at: datetime = Field(default_factory=datetime.utcnow)