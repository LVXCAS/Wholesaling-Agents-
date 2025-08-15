"""
Funding source management data models for the Real Estate Empire platform.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class FundingSourceTypeEnum(str, Enum):
    """Types of funding sources"""
    BANK = "bank"
    CREDIT_UNION = "credit_union"
    PRIVATE_LENDER = "private_lender"
    HARD_MONEY = "hard_money"
    PORTFOLIO_LENDER = "portfolio_lender"
    GOVERNMENT = "government"
    PEER_TO_PEER = "peer_to_peer"
    FAMILY_OFFICE = "family_office"
    INSTITUTIONAL = "institutional"


class LoanTypeEnum(str, Enum):
    """Types of loans offered"""
    CONVENTIONAL = "conventional"
    FHA = "fha"
    VA = "va"
    USDA = "usda"
    JUMBO = "jumbo"
    HARD_MONEY = "hard_money"
    BRIDGE = "bridge"
    CONSTRUCTION = "construction"
    COMMERCIAL = "commercial"
    PORTFOLIO = "portfolio"
    DSCR = "dscr"  # Debt Service Coverage Ratio
    ASSET_BASED = "asset_based"


class PropertyTypeEnum(str, Enum):
    """Property types for funding"""
    SINGLE_FAMILY = "single_family"
    MULTI_FAMILY = "multi_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    COMMERCIAL = "commercial"
    MIXED_USE = "mixed_use"
    LAND = "land"
    CONSTRUCTION = "construction"


class FundingStatusEnum(str, Enum):
    """Status of funding relationships"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_APPROVAL = "pending_approval"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class ApplicationStatusEnum(str, Enum):
    """Status of funding applications"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"
    FUNDED = "funded"


class FundingSource(BaseModel):
    """Core funding source information"""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=200)
    funding_type: FundingSourceTypeEnum
    status: FundingStatusEnum = FundingStatusEnum.ACTIVE
    
    # Contact information
    contact_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    
    # Lending criteria
    min_loan_amount: Optional[Decimal] = Field(None, ge=0)
    max_loan_amount: Optional[Decimal] = Field(None, ge=0)
    min_credit_score: Optional[int] = Field(None, ge=300, le=850)
    max_ltv: Optional[Decimal] = Field(None, ge=0, le=1)  # Loan-to-Value ratio
    max_dti: Optional[Decimal] = Field(None, ge=0, le=1)  # Debt-to-Income ratio
    min_dscr: Optional[Decimal] = Field(None, ge=0)  # Debt Service Coverage Ratio
    
    # Geographic coverage
    states_covered: List[str] = Field(default_factory=list)
    nationwide: bool = False
    
    # Loan products offered
    loan_types: List[LoanTypeEnum] = Field(default_factory=list)
    property_types: List[PropertyTypeEnum] = Field(default_factory=list)
    
    # Terms and rates
    typical_rate_range_min: Optional[Decimal] = Field(None, ge=0, le=1)
    typical_rate_range_max: Optional[Decimal] = Field(None, ge=0, le=1)
    typical_term_months: Optional[int] = Field(None, ge=1)
    points_range_min: Optional[Decimal] = Field(None, ge=0)
    points_range_max: Optional[Decimal] = Field(None, ge=0)
    
    # Processing information
    typical_processing_days: Optional[int] = Field(None, ge=1)
    requires_appraisal: bool = True
    requires_inspection: bool = True
    allows_investor_properties: bool = True
    allows_non_owner_occupied: bool = True
    
    # Relationship information
    relationship_manager: Optional[str] = None
    established_date: Optional[datetime] = None
    last_contact_date: Optional[datetime] = None
    total_loans_funded: int = 0
    total_amount_funded: Decimal = Field(default=Decimal('0'), ge=0)
    
    # Performance metrics
    approval_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    average_processing_time: Optional[int] = None  # days
    customer_satisfaction_score: Optional[Decimal] = Field(None, ge=0, le=10)
    
    # Notes and tags
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('max_loan_amount')
    def validate_loan_amount_range(cls, v, values):
        if v is not None and 'min_loan_amount' in values and values['min_loan_amount'] is not None:
            if v < values['min_loan_amount']:
                raise ValueError('max_loan_amount must be greater than or equal to min_loan_amount')
        return v
    
    @validator('typical_rate_range_max')
    def validate_rate_range(cls, v, values):
        if v is not None and 'typical_rate_range_min' in values and values['typical_rate_range_min'] is not None:
            if v < values['typical_rate_range_min']:
                raise ValueError('typical_rate_range_max must be greater than or equal to typical_rate_range_min')
        return v


class LoanProduct(BaseModel):
    """Specific loan product offered by a funding source"""
    id: UUID = Field(default_factory=uuid4)
    funding_source_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    loan_type: LoanTypeEnum
    property_types: List[PropertyTypeEnum] = Field(default_factory=list)
    
    # Loan terms
    min_amount: Decimal = Field(..., ge=0)
    max_amount: Decimal = Field(..., ge=0)
    min_term_months: int = Field(..., ge=1)
    max_term_months: int = Field(..., ge=1)
    
    # Rates and fees
    base_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    rate_adjustments: Dict[str, Decimal] = Field(default_factory=dict)
    origination_fee: Optional[Decimal] = Field(None, ge=0)
    processing_fee: Optional[Decimal] = Field(None, ge=0)
    underwriting_fee: Optional[Decimal] = Field(None, ge=0)
    
    # Requirements
    min_credit_score: Optional[int] = Field(None, ge=300, le=850)
    max_ltv: Optional[Decimal] = Field(None, ge=0, le=1)
    max_dti: Optional[Decimal] = Field(None, ge=0, le=1)
    min_dscr: Optional[Decimal] = Field(None, ge=0)
    min_down_payment: Optional[Decimal] = Field(None, ge=0, le=1)
    
    # Features
    allows_cash_out: bool = False
    allows_interest_only: bool = False
    prepayment_penalty: bool = False
    assumable: bool = False
    
    # Processing
    typical_processing_days: Optional[int] = Field(None, ge=1)
    requires_reserves: Optional[int] = None  # months of payments
    
    # Status and metadata
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FundingApplication(BaseModel):
    """Funding application tracking"""
    id: UUID = Field(default_factory=uuid4)
    funding_source_id: UUID
    loan_product_id: Optional[UUID] = None
    deal_id: UUID
    
    # Application details
    loan_amount: Decimal = Field(..., ge=0)
    loan_type: LoanTypeEnum
    property_type: PropertyTypeEnum
    property_address: str
    property_value: Optional[Decimal] = Field(None, ge=0)
    
    # Borrower information
    borrower_name: str
    borrower_email: Optional[str] = None
    borrower_phone: Optional[str] = None
    credit_score: Optional[int] = Field(None, ge=300, le=850)
    annual_income: Optional[Decimal] = Field(None, ge=0)
    debt_to_income: Optional[Decimal] = Field(None, ge=0, le=1)
    
    # Application status
    status: ApplicationStatusEnum = ApplicationStatusEnum.DRAFT
    submitted_at: Optional[datetime] = None
    decision_date: Optional[datetime] = None
    funded_date: Optional[datetime] = None
    
    # Terms offered
    approved_amount: Optional[Decimal] = Field(None, ge=0)
    approved_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    approved_term_months: Optional[int] = Field(None, ge=1)
    points: Optional[Decimal] = Field(None, ge=0)
    
    # Conditions and requirements
    conditions: List[str] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    submitted_documents: List[str] = Field(default_factory=list)
    
    # Communication log
    notes: Optional[str] = None
    last_contact_date: Optional[datetime] = None
    next_follow_up_date: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FundingSourceMatch(BaseModel):
    """Represents a match between a deal and a funding source"""
    id: UUID = Field(default_factory=uuid4)
    deal_id: UUID
    funding_source_id: UUID
    loan_product_id: Optional[UUID] = None
    
    # Match scoring
    match_score: float = Field(..., ge=0, le=1)
    match_reasons: List[str] = Field(default_factory=list)
    
    # Match criteria results
    loan_amount_match: bool = False
    credit_score_match: bool = False
    ltv_match: bool = False
    dti_match: bool = False
    dscr_match: bool = False
    property_type_match: bool = False
    geographic_match: bool = False
    loan_type_match: bool = False
    
    # Estimated terms
    estimated_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    estimated_points: Optional[Decimal] = Field(None, ge=0)
    estimated_processing_days: Optional[int] = Field(None, ge=1)
    
    # Application tracking
    application_submitted: bool = False
    application_id: Optional[UUID] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FundingSourcePerformance(BaseModel):
    """Performance metrics for funding sources"""
    funding_source_id: UUID
    
    # Application metrics
    total_applications: int = 0
    approved_applications: int = 0
    denied_applications: int = 0
    pending_applications: int = 0
    approval_rate: Decimal = Field(default=Decimal('0'), ge=0, le=1)
    
    # Funding metrics
    total_funded: int = 0
    total_amount_funded: Decimal = Field(default=Decimal('0'), ge=0)
    average_loan_amount: Decimal = Field(default=Decimal('0'), ge=0)
    
    # Processing metrics
    average_processing_days: Optional[Decimal] = None
    fastest_processing_days: Optional[int] = None
    slowest_processing_days: Optional[int] = None
    
    # Rate metrics
    average_rate_offered: Optional[Decimal] = None
    lowest_rate_offered: Optional[Decimal] = None
    highest_rate_offered: Optional[Decimal] = None
    
    # Relationship metrics
    last_application_date: Optional[datetime] = None
    last_funding_date: Optional[datetime] = None
    relationship_strength_score: Optional[Decimal] = Field(None, ge=0, le=10)
    
    # Time period
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class FundingSearchCriteria(BaseModel):
    """Criteria for searching and filtering funding sources"""
    funding_types: Optional[List[FundingSourceTypeEnum]] = None
    loan_types: Optional[List[LoanTypeEnum]] = None
    property_types: Optional[List[PropertyTypeEnum]] = None
    states: Optional[List[str]] = None
    min_loan_amount: Optional[Decimal] = None
    max_loan_amount: Optional[Decimal] = None
    max_rate: Optional[Decimal] = None
    min_credit_score: Optional[int] = None
    max_ltv: Optional[Decimal] = None
    max_processing_days: Optional[int] = None
    requires_investor_properties: Optional[bool] = None
    tags: Optional[List[str]] = None


class FundingAnalytics(BaseModel):
    """Analytics data for funding source management"""
    total_funding_sources: int = 0
    active_funding_sources: int = 0
    total_loan_products: int = 0
    
    # Application metrics
    total_applications: int = 0
    pending_applications: int = 0
    approved_applications: int = 0
    denied_applications: int = 0
    overall_approval_rate: Decimal = Field(default=Decimal('0'), ge=0, le=1)
    
    # Funding metrics
    total_funded_deals: int = 0
    total_amount_funded: Decimal = Field(default=Decimal('0'), ge=0)
    average_loan_amount: Decimal = Field(default=Decimal('0'), ge=0)
    
    # Performance metrics
    average_processing_time: Optional[Decimal] = None
    average_rate: Optional[Decimal] = None
    top_performing_sources: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Distribution metrics
    funding_type_distribution: Dict[str, int] = Field(default_factory=dict)
    loan_type_distribution: Dict[str, int] = Field(default_factory=dict)
    geographic_distribution: Dict[str, int] = Field(default_factory=dict)
    
    # Trends
    monthly_application_trend: List[Dict[str, Any]] = Field(default_factory=list)
    monthly_funding_trend: List[Dict[str, Any]] = Field(default_factory=list)
    
    calculated_at: datetime = Field(default_factory=datetime.utcnow)