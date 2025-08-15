"""
Reporting data models for the Real Estate Empire platform.
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


class ReportTypeEnum(str, Enum):
    """Enum for report types."""
    PORTFOLIO_PERFORMANCE = "portfolio_performance"
    PROPERTY_ANALYSIS = "property_analysis"
    MARKET_ANALYSIS = "market_analysis"
    DEAL_PIPELINE = "deal_pipeline"
    FINANCIAL_SUMMARY = "financial_summary"
    RISK_ASSESSMENT = "risk_assessment"
    INVESTMENT_TRACKING = "investment_tracking"
    CUSTOM = "custom"


class ReportStatusEnum(str, Enum):
    """Enum for report status."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    SCHEDULED = "scheduled"


class ReportFormatEnum(str, Enum):
    """Enum for report formats."""
    PDF = "pdf"
    HTML = "html"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"


class ScheduleFrequencyEnum(str, Enum):
    """Enum for schedule frequencies."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class ReportTemplateDB(Base):
    """SQLAlchemy model for report templates."""
    __tablename__ = "report_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Template Information
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(String, nullable=False)
    
    # Template Configuration
    template_config = Column(JSON, nullable=False)  # Chart types, sections, filters
    default_parameters = Column(JSON, nullable=True)
    
    # Layout and Styling
    layout_config = Column(JSON, nullable=True)
    style_config = Column(JSON, nullable=True)
    
    # Template Status
    is_active = Column(Boolean, default=True)
    is_system_template = Column(Boolean, default=False)
    
    # Relationships
    reports = relationship("ReportDB", back_populates="template")
    
    def __repr__(self):
        return f"<ReportTemplateDB(id={self.id}, name={self.name}, type={self.report_type})>"


class ReportDB(Base):
    """SQLAlchemy model for reports."""
    __tablename__ = "reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("report_templates.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Report Information
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(String, nullable=False)
    
    # Report Parameters
    parameters = Column(JSON, nullable=True)
    filters = Column(JSON, nullable=True)
    date_range_start = Column(DateTime, nullable=True)
    date_range_end = Column(DateTime, nullable=True)
    
    # Report Status
    status = Column(String, nullable=False, default=ReportStatusEnum.PENDING)
    progress_percent = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Report Output
    output_format = Column(String, nullable=False, default=ReportFormatEnum.HTML)
    file_path = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # Report Data
    report_data = Column(JSON, nullable=True)  # Structured report data
    charts_data = Column(JSON, nullable=True)  # Chart configurations and data
    
    # Generation Info
    generated_at = Column(DateTime, nullable=True)
    generation_time_seconds = Column(Float, nullable=True)
    
    # Relationships
    template = relationship("ReportTemplateDB", back_populates="reports")
    schedules = relationship("ReportScheduleDB", back_populates="report")
    
    def __repr__(self):
        return f"<ReportDB(id={self.id}, name={self.name}, status={self.status})>"


class ReportScheduleDB(Base):
    """SQLAlchemy model for report schedules."""
    __tablename__ = "report_schedules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Schedule Configuration
    name = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    schedule_time = Column(String, nullable=True)  # e.g., "09:00" for daily, "MON" for weekly
    timezone = Column(String, nullable=False, default="UTC")
    
    # Schedule Status
    is_active = Column(Boolean, default=True)
    next_run_at = Column(DateTime, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(String, nullable=True)
    
    # Recipients
    email_recipients = Column(JSON, nullable=True)  # List of email addresses
    
    # Relationship
    report = relationship("ReportDB", back_populates="schedules")
    
    def __repr__(self):
        return f"<ReportScheduleDB(id={self.id}, name={self.name}, frequency={self.frequency})>"


class DashboardDB(Base):
    """SQLAlchemy model for custom dashboards."""
    __tablename__ = "dashboards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Dashboard Information
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Dashboard Configuration
    layout_config = Column(JSON, nullable=False)  # Grid layout, widget positions
    widgets_config = Column(JSON, nullable=False)  # Widget configurations
    
    # Dashboard Settings
    refresh_interval_seconds = Column(Integer, default=300)  # 5 minutes
    is_public = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)
    
    # Dashboard Status
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<DashboardDB(id={self.id}, name={self.name})>"


class ChartConfigDB(Base):
    """SQLAlchemy model for chart configurations."""
    __tablename__ = "chart_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Chart Information
    name = Column(String, nullable=False)
    chart_type = Column(String, nullable=False)  # e.g., "line", "bar", "pie", "scatter"
    
    # Chart Configuration
    data_source = Column(String, nullable=False)  # Data source identifier
    query_config = Column(JSON, nullable=False)  # Query parameters
    chart_options = Column(JSON, nullable=True)  # Chart.js or similar options
    
    # Chart Settings
    width = Column(Integer, default=400)
    height = Column(Integer, default=300)
    refresh_interval_seconds = Column(Integer, default=300)
    
    # Chart Status
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<ChartConfigDB(id={self.id}, name={self.name}, type={self.chart_type})>"


# Pydantic models for API requests and responses

class ReportTemplateCreate(BaseModel):
    """Pydantic model for creating a report template."""
    name: str
    description: Optional[str] = None
    report_type: ReportTypeEnum
    template_config: Dict[str, Any]
    default_parameters: Optional[Dict[str, Any]] = None
    layout_config: Optional[Dict[str, Any]] = None
    style_config: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class ReportTemplateResponse(BaseModel):
    """Pydantic model for report template API responses."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    name: str
    description: Optional[str] = None
    report_type: ReportTypeEnum
    template_config: Dict[str, Any]
    default_parameters: Optional[Dict[str, Any]] = None
    layout_config: Optional[Dict[str, Any]] = None
    style_config: Optional[Dict[str, Any]] = None
    is_active: bool
    is_system_template: bool
    
    class Config:
        from_attributes = True


class ReportCreate(BaseModel):
    """Pydantic model for creating a report."""
    name: str
    description: Optional[str] = None
    report_type: ReportTypeEnum
    template_id: Optional[uuid.UUID] = None
    parameters: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    output_format: ReportFormatEnum = ReportFormatEnum.HTML
    
    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    """Pydantic model for report API responses."""
    id: uuid.UUID
    template_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    name: str
    description: Optional[str] = None
    report_type: ReportTypeEnum
    parameters: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    status: ReportStatusEnum
    progress_percent: int
    error_message: Optional[str] = None
    output_format: ReportFormatEnum
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    report_data: Optional[Dict[str, Any]] = None
    charts_data: Optional[Dict[str, Any]] = None
    generated_at: Optional[datetime] = None
    generation_time_seconds: Optional[float] = None
    
    class Config:
        from_attributes = True


class ReportScheduleCreate(BaseModel):
    """Pydantic model for creating a report schedule."""
    report_id: uuid.UUID
    name: str
    frequency: ScheduleFrequencyEnum
    schedule_time: Optional[str] = None
    timezone: str = "UTC"
    email_recipients: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class ReportScheduleResponse(BaseModel):
    """Pydantic model for report schedule API responses."""
    id: uuid.UUID
    report_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    name: str
    frequency: ScheduleFrequencyEnum
    schedule_time: Optional[str] = None
    timezone: str
    is_active: bool
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    email_recipients: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class DashboardCreate(BaseModel):
    """Pydantic model for creating a dashboard."""
    name: str
    description: Optional[str] = None
    layout_config: Dict[str, Any]
    widgets_config: Dict[str, Any]
    refresh_interval_seconds: int = 300
    is_public: bool = False
    is_default: bool = False
    
    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    """Pydantic model for dashboard API responses."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    name: str
    description: Optional[str] = None
    layout_config: Dict[str, Any]
    widgets_config: Dict[str, Any]
    refresh_interval_seconds: int
    is_public: bool
    is_default: bool
    is_active: bool
    
    class Config:
        from_attributes = True


class ChartConfigCreate(BaseModel):
    """Pydantic model for creating a chart configuration."""
    name: str
    chart_type: str
    data_source: str
    query_config: Dict[str, Any]
    chart_options: Optional[Dict[str, Any]] = None
    width: int = 400
    height: int = 300
    refresh_interval_seconds: int = 300
    
    class Config:
        from_attributes = True


class ChartConfigResponse(BaseModel):
    """Pydantic model for chart configuration API responses."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    name: str
    chart_type: str
    data_source: str
    query_config: Dict[str, Any]
    chart_options: Optional[Dict[str, Any]] = None
    width: int
    height: int
    refresh_interval_seconds: int
    is_active: bool
    
    class Config:
        from_attributes = True


class ChartDataResponse(BaseModel):
    """Pydantic model for chart data responses."""
    chart_id: uuid.UUID
    chart_type: str
    data: Dict[str, Any]
    labels: Optional[List[str]] = None
    datasets: Optional[List[Dict[str, Any]]] = None
    options: Optional[Dict[str, Any]] = None
    generated_at: datetime
    
    class Config:
        from_attributes = True


class ReportGenerationRequest(BaseModel):
    """Pydantic model for report generation requests."""
    report_id: uuid.UUID
    force_regenerate: bool = False
    
    class Config:
        from_attributes = True


class BulkReportRequest(BaseModel):
    """Pydantic model for bulk report generation requests."""
    report_ids: List[uuid.UUID]
    output_format: Optional[ReportFormatEnum] = None
    
    class Config:
        from_attributes = True