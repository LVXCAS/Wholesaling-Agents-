"""
Investment package generation data models for the Real Estate Empire platform.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class PackageTypeEnum(str, Enum):
    """Types of investment packages"""
    EXECUTIVE_SUMMARY = "executive_summary"
    DETAILED_ANALYSIS = "detailed_analysis"
    INVESTOR_PRESENTATION = "investor_presentation"
    MARKETING_FLYER = "marketing_flyer"
    FINANCIAL_PROJECTIONS = "financial_projections"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    CUSTOM = "custom"


class PackageStatusEnum(str, Enum):
    """Status of investment packages"""
    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    DISTRIBUTED = "distributed"
    ARCHIVED = "archived"
    ERROR = "error"


class DeliveryMethodEnum(str, Enum):
    """Methods for delivering investment packages"""
    EMAIL = "email"
    DOWNLOAD_LINK = "download_link"
    PHYSICAL_MAIL = "physical_mail"
    SECURE_PORTAL = "secure_portal"
    PRESENTATION = "presentation"


class PackageFormatEnum(str, Enum):
    """Formats for investment packages"""
    PDF = "pdf"
    POWERPOINT = "powerpoint"
    WORD = "word"
    HTML = "html"
    VIDEO = "video"
    INTERACTIVE = "interactive"


class InvestmentPackageTemplate(BaseModel):
    """Template for generating investment packages"""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=200)
    package_type: PackageTypeEnum
    description: Optional[str] = None
    
    # Template configuration
    format: PackageFormatEnum = PackageFormatEnum.PDF
    sections: List[str] = Field(default_factory=list)
    required_data_fields: List[str] = Field(default_factory=list)
    optional_data_fields: List[str] = Field(default_factory=list)
    
    # Design settings
    template_file_path: Optional[str] = None
    brand_colors: Dict[str, str] = Field(default_factory=dict)
    logo_path: Optional[str] = None
    font_settings: Dict[str, Any] = Field(default_factory=dict)
    
    # Content settings
    include_financial_projections: bool = True
    include_market_analysis: bool = True
    include_risk_assessment: bool = True
    include_comparable_properties: bool = True
    include_photos: bool = True
    include_maps: bool = True
    
    # Customization options
    customizable_sections: List[str] = Field(default_factory=list)
    variable_content_blocks: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    created_by: Optional[str] = None
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class InvestmentPackage(BaseModel):
    """Generated investment package"""
    id: UUID = Field(default_factory=uuid4)
    template_id: UUID
    deal_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    package_type: PackageTypeEnum
    status: PackageStatusEnum = PackageStatusEnum.DRAFT
    
    # Package content
    title: str
    subtitle: Optional[str] = None
    executive_summary: Optional[str] = None
    investment_highlights: List[str] = Field(default_factory=list)
    
    # Property information
    property_address: Optional[str] = None
    property_description: Optional[str] = None
    property_photos: List[str] = Field(default_factory=list)
    property_features: List[str] = Field(default_factory=list)
    
    # Financial data
    purchase_price: Optional[Decimal] = Field(None, ge=0)
    estimated_value: Optional[Decimal] = Field(None, ge=0)
    renovation_cost: Optional[Decimal] = Field(None, ge=0)
    total_investment: Optional[Decimal] = Field(None, ge=0)
    projected_rental_income: Optional[Decimal] = Field(None, ge=0)
    projected_expenses: Optional[Decimal] = Field(None, ge=0)
    projected_cash_flow: Optional[Decimal] = None
    projected_roi: Optional[Decimal] = None
    projected_cap_rate: Optional[Decimal] = None
    
    # Market analysis
    market_overview: Optional[str] = None
    comparable_properties: List[Dict[str, Any]] = Field(default_factory=list)
    market_trends: List[str] = Field(default_factory=list)
    neighborhood_analysis: Optional[str] = None
    
    # Risk assessment
    risk_factors: List[str] = Field(default_factory=list)
    mitigation_strategies: List[str] = Field(default_factory=list)
    risk_score: Optional[float] = Field(None, ge=0, le=10)
    
    # Investment structure
    investment_amount_required: Optional[Decimal] = Field(None, ge=0)
    minimum_investment: Optional[Decimal] = Field(None, ge=0)
    maximum_investment: Optional[Decimal] = Field(None, ge=0)
    investment_terms: Optional[str] = None
    expected_hold_period: Optional[int] = None  # months
    exit_strategy: Optional[str] = None
    
    # Additional content
    custom_sections: Dict[str, Any] = Field(default_factory=dict)
    appendices: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Generation metadata
    generated_by: Optional[str] = None
    generation_parameters: Dict[str, Any] = Field(default_factory=dict)
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    generated_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PackageDistribution(BaseModel):
    """Track distribution of investment packages"""
    id: UUID = Field(default_factory=uuid4)
    package_id: UUID
    recipient_id: UUID  # Investor ID
    recipient_name: str
    recipient_email: Optional[str] = None
    
    # Distribution details
    delivery_method: DeliveryMethodEnum
    delivery_address: Optional[str] = None
    subject_line: Optional[str] = None
    message: Optional[str] = None
    
    # Tracking
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    downloaded_at: Optional[datetime] = None
    viewed_duration: Optional[int] = None  # seconds
    
    # Engagement tracking
    pages_viewed: List[int] = Field(default_factory=list)
    sections_viewed: List[str] = Field(default_factory=list)
    time_spent_per_section: Dict[str, int] = Field(default_factory=dict)
    
    # Response tracking
    responded: bool = False
    response_date: Optional[datetime] = None
    response_type: Optional[str] = None  # interested, not_interested, request_meeting
    response_notes: Optional[str] = None
    
    # Follow-up
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    follow_up_notes: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PackageGenerationRequest(BaseModel):
    """Request to generate an investment package"""
    template_id: UUID
    deal_id: UUID
    package_name: str
    
    # Customization options
    custom_title: Optional[str] = None
    custom_subtitle: Optional[str] = None
    custom_executive_summary: Optional[str] = None
    additional_highlights: List[str] = Field(default_factory=list)
    
    # Content overrides
    include_sections: Optional[List[str]] = None
    exclude_sections: Optional[List[str]] = None
    custom_content: Dict[str, Any] = Field(default_factory=dict)
    
    # Formatting options
    format: Optional[PackageFormatEnum] = None
    brand_customization: Dict[str, Any] = Field(default_factory=dict)
    
    # Distribution settings
    auto_distribute: bool = False
    distribution_list: List[UUID] = Field(default_factory=list)  # Investor IDs
    delivery_method: Optional[DeliveryMethodEnum] = None
    
    # Generation parameters
    priority: str = "normal"  # low, normal, high
    requested_by: Optional[str] = None
    notes: Optional[str] = None


class PackageAnalytics(BaseModel):
    """Analytics for investment package performance"""
    package_id: UUID
    
    # Distribution metrics
    total_distributed: int = 0
    total_delivered: int = 0
    total_opened: int = 0
    total_downloaded: int = 0
    
    # Engagement metrics
    open_rate: Decimal = Field(default=Decimal('0'), ge=0, le=1)
    download_rate: Decimal = Field(default=Decimal('0'), ge=0, le=1)
    average_view_time: Optional[int] = None  # seconds
    most_viewed_sections: List[str] = Field(default_factory=list)
    
    # Response metrics
    total_responses: int = 0
    interested_responses: int = 0
    not_interested_responses: int = 0
    meeting_requests: int = 0
    response_rate: Decimal = Field(default=Decimal('0'), ge=0, le=1)
    interest_rate: Decimal = Field(default=Decimal('0'), ge=0, le=1)
    
    # Performance by delivery method
    performance_by_method: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Time-based metrics
    best_send_times: List[str] = Field(default_factory=list)
    response_time_distribution: Dict[str, int] = Field(default_factory=dict)
    
    # Calculated at
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class PackageTemplate(BaseModel):
    """Simplified template for common package types"""
    name: str
    package_type: PackageTypeEnum
    sections: List[str]
    required_fields: List[str]
    format: PackageFormatEnum = PackageFormatEnum.PDF


class MarketingMaterial(BaseModel):
    """Marketing materials generated from investment packages"""
    id: UUID = Field(default_factory=uuid4)
    package_id: UUID
    material_type: str  # flyer, brochure, social_media, email_template
    format: PackageFormatEnum
    
    # Content
    title: str
    description: Optional[str] = None
    key_points: List[str] = Field(default_factory=list)
    call_to_action: Optional[str] = None
    
    # Design elements
    images: List[str] = Field(default_factory=list)
    layout_template: Optional[str] = None
    color_scheme: Dict[str, str] = Field(default_factory=dict)
    
    # Distribution channels
    target_channels: List[str] = Field(default_factory=list)
    distribution_schedule: Optional[datetime] = None
    
    # Performance tracking
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PackageCustomization(BaseModel):
    """Customization settings for investment packages"""
    investor_id: UUID
    
    # Preferred formats
    preferred_formats: List[PackageFormatEnum] = Field(default_factory=list)
    preferred_delivery_methods: List[DeliveryMethodEnum] = Field(default_factory=list)
    
    # Content preferences
    preferred_sections: List[str] = Field(default_factory=list)
    excluded_sections: List[str] = Field(default_factory=list)
    detail_level: str = "standard"  # brief, standard, detailed
    
    # Visual preferences
    preferred_colors: Dict[str, str] = Field(default_factory=dict)
    font_preferences: Dict[str, str] = Field(default_factory=dict)
    include_photos: bool = True
    include_charts: bool = True
    
    # Communication preferences
    preferred_language: str = "en"
    timezone: Optional[str] = None
    best_contact_times: List[str] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PackagePerformanceReport(BaseModel):
    """Performance report for investment packages"""
    
    # Overall metrics
    total_packages_generated: int = 0
    total_packages_distributed: int = 0
    average_generation_time: Optional[float] = None  # minutes
    
    # Engagement metrics
    overall_open_rate: Decimal = Field(default=Decimal('0'))
    overall_response_rate: Decimal = Field(default=Decimal('0'))
    overall_interest_rate: Decimal = Field(default=Decimal('0'))
    
    # Performance by type
    performance_by_type: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    performance_by_format: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Top performing packages
    top_packages: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Trends
    monthly_generation_trend: List[Dict[str, Any]] = Field(default_factory=list)
    engagement_trends: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Recommendations
    optimization_recommendations: List[str] = Field(default_factory=list)
    
    # Report metadata
    report_period_start: datetime
    report_period_end: datetime
    generated_at: datetime = Field(default_factory=datetime.utcnow)