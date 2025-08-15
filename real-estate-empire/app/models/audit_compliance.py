"""
Audit and Compliance data models for the Real Estate Empire platform.
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


class AuditEventTypeEnum(str, Enum):
    """Enum for audit event types."""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    DATA_CREATE = "data_create"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_VIEW = "data_view"
    REPORT_GENERATE = "report_generate"
    SYSTEM_CONFIG = "system_config"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_CHECK = "compliance_check"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"


class ComplianceStatusEnum(str, Enum):
    """Enum for compliance status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING_REVIEW = "pending_review"
    REMEDIATED = "remediated"
    EXCEPTION_GRANTED = "exception_granted"


class DataRetentionStatusEnum(str, Enum):
    """Enum for data retention status."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    SCHEDULED_DELETION = "scheduled_deletion"
    DELETED = "deleted"
    LEGAL_HOLD = "legal_hold"


class AuditLogDB(Base):
    """SQLAlchemy model for audit logs."""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Event Information
    event_type = Column(String, nullable=False)
    event_category = Column(String, nullable=True)  # e.g., "security", "data", "system"
    event_description = Column(Text, nullable=False)
    
    # User Information
    user_id = Column(String, nullable=True)  # User identifier
    user_email = Column(String, nullable=True)
    user_role = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    
    # System Information
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    request_id = Column(String, nullable=True)
    
    # Resource Information
    resource_type = Column(String, nullable=True)  # e.g., "property", "portfolio", "report"
    resource_id = Column(String, nullable=True)
    resource_name = Column(String, nullable=True)
    
    # Event Details
    action_performed = Column(String, nullable=True)  # e.g., "create", "update", "delete"
    old_values = Column(JSON, nullable=True)  # Previous values for updates
    new_values = Column(JSON, nullable=True)  # New values for updates
    
    # Context and Metadata
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    error_details = Column(JSON, nullable=True)
    additional_metadata = Column(JSON, nullable=True)
    
    # Compliance and Security
    compliance_relevant = Column(Boolean, default=False)
    security_relevant = Column(Boolean, default=False)
    risk_level = Column(String, nullable=True)  # "low", "medium", "high", "critical"
    
    def __repr__(self):
        return f"<AuditLogDB(id={self.id}, event_type={self.event_type}, user_id={self.user_id})>"


class ComplianceRuleDB(Base):
    """SQLAlchemy model for compliance rules."""
    __tablename__ = "compliance_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Rule Information
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    regulation_reference = Column(String, nullable=True)  # e.g., "GDPR Article 17", "CCPA Section 1798.105"
    
    # Rule Configuration
    rule_type = Column(String, nullable=False)  # e.g., "data_retention", "access_control", "privacy"
    rule_config = Column(JSON, nullable=False)  # Rule-specific configuration
    
    # Applicability
    applies_to_data_types = Column(JSON, nullable=True)  # List of data types this rule applies to
    applies_to_user_roles = Column(JSON, nullable=True)  # List of user roles this rule applies to
    geographic_scope = Column(JSON, nullable=True)  # Geographic regions where this rule applies
    
    # Rule Status
    is_active = Column(Boolean, default=True)
    effective_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    
    # Monitoring
    last_checked = Column(DateTime, nullable=True)
    check_frequency_hours = Column(Integer, default=24)  # How often to check compliance
    
    # Relationships
    compliance_checks = relationship("ComplianceCheckDB", back_populates="rule")
    
    def __repr__(self):
        return f"<ComplianceRuleDB(id={self.id}, name={self.name}, type={self.rule_type})>"


class ComplianceCheckDB(Base):
    """SQLAlchemy model for compliance checks."""
    __tablename__ = "compliance_checks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("compliance_rules.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Check Information
    check_type = Column(String, nullable=False)  # "automated", "manual", "scheduled"
    check_description = Column(Text, nullable=True)
    
    # Check Results
    status = Column(String, nullable=False, default=ComplianceStatusEnum.PENDING_REVIEW)
    compliance_score = Column(Float, nullable=True)  # 0-100 compliance score
    
    # Findings
    violations_found = Column(Integer, default=0)
    violations_details = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    
    # Check Context
    scope_checked = Column(JSON, nullable=True)  # What was checked
    check_parameters = Column(JSON, nullable=True)
    
    # Remediation
    remediation_required = Column(Boolean, default=False)
    remediation_deadline = Column(DateTime, nullable=True)
    remediation_status = Column(String, nullable=True)
    remediation_notes = Column(Text, nullable=True)
    
    # Relationship
    rule = relationship("ComplianceRuleDB", back_populates="compliance_checks")
    
    def __repr__(self):
        return f"<ComplianceCheckDB(id={self.id}, rule_id={self.rule_id}, status={self.status})>"


class DataRetentionPolicyDB(Base):
    """SQLAlchemy model for data retention policies."""
    __tablename__ = "data_retention_policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Policy Information
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Data Classification
    data_type = Column(String, nullable=False)  # e.g., "personal_data", "financial_data", "property_data"
    data_category = Column(String, nullable=True)  # More specific categorization
    
    # Retention Rules
    retention_period_days = Column(Integer, nullable=False)
    retention_trigger = Column(String, nullable=False)  # e.g., "creation_date", "last_access", "user_deletion_request"
    
    # Legal Basis
    legal_basis = Column(String, nullable=True)  # Legal justification for retention
    regulation_reference = Column(String, nullable=True)
    
    # Policy Configuration
    auto_delete_enabled = Column(Boolean, default=True)
    archive_before_delete = Column(Boolean, default=True)
    archive_location = Column(String, nullable=True)
    
    # Exceptions
    legal_hold_override = Column(Boolean, default=True)  # Can legal holds override this policy?
    business_justification_override = Column(Boolean, default=False)
    
    # Policy Status
    is_active = Column(Boolean, default=True)
    effective_date = Column(DateTime, nullable=True)
    
    # Relationships
    retention_records = relationship("DataRetentionRecordDB", back_populates="policy")
    
    def __repr__(self):
        return f"<DataRetentionPolicyDB(id={self.id}, name={self.name}, data_type={self.data_type})>"


class DataRetentionRecordDB(Base):
    """SQLAlchemy model for data retention records."""
    __tablename__ = "data_retention_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("data_retention_policies.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Data Record Information
    data_type = Column(String, nullable=False)
    data_id = Column(String, nullable=False)  # ID of the actual data record
    data_location = Column(String, nullable=True)  # Database table, file path, etc.
    
    # Retention Tracking
    data_created_at = Column(DateTime, nullable=False)
    retention_deadline = Column(DateTime, nullable=False)
    status = Column(String, nullable=False, default=DataRetentionStatusEnum.ACTIVE)
    
    # Processing History
    last_accessed = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)
    archive_location = Column(String, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Legal Holds
    legal_hold_active = Column(Boolean, default=False)
    legal_hold_reason = Column(String, nullable=True)
    legal_hold_start_date = Column(DateTime, nullable=True)
    legal_hold_end_date = Column(DateTime, nullable=True)
    
    # Additional Context
    business_justification = Column(Text, nullable=True)
    processing_notes = Column(Text, nullable=True)
    
    # Relationship
    policy = relationship("DataRetentionPolicyDB", back_populates="retention_records")
    
    def __repr__(self):
        return f"<DataRetentionRecordDB(id={self.id}, data_type={self.data_type}, status={self.status})>"


class RegulatoryReportDB(Base):
    """SQLAlchemy model for regulatory reports."""
    __tablename__ = "regulatory_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Report Information
    report_name = Column(String, nullable=False)
    report_type = Column(String, nullable=False)  # e.g., "gdpr_compliance", "ccpa_compliance", "sox_compliance"
    regulation = Column(String, nullable=False)  # e.g., "GDPR", "CCPA", "SOX"
    
    # Reporting Period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Report Content
    report_data = Column(JSON, nullable=False)
    summary_statistics = Column(JSON, nullable=True)
    compliance_score = Column(Float, nullable=True)
    
    # Report Status
    status = Column(String, nullable=False, default="draft")  # "draft", "final", "submitted"
    generated_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    
    # File Information
    file_path = Column(String, nullable=True)
    file_format = Column(String, nullable=True)  # "pdf", "csv", "json"
    
    def __repr__(self):
        return f"<RegulatoryReportDB(id={self.id}, report_type={self.report_type}, regulation={self.regulation})>"


# Pydantic models for API requests and responses

class AuditLogCreate(BaseModel):
    """Pydantic model for creating audit log entries."""
    event_type: AuditEventTypeEnum
    event_category: Optional[str] = None
    event_description: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    action_performed: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    request_data: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None
    error_details: Optional[Dict[str, Any]] = None
    additional_metadata: Optional[Dict[str, Any]] = None
    compliance_relevant: bool = False
    security_relevant: bool = False
    risk_level: Optional[str] = None
    
    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Pydantic model for audit log API responses."""
    id: uuid.UUID
    created_at: datetime
    event_type: AuditEventTypeEnum
    event_category: Optional[str] = None
    event_description: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    action_performed: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    request_data: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None
    error_details: Optional[Dict[str, Any]] = None
    additional_metadata: Optional[Dict[str, Any]] = None
    compliance_relevant: bool
    security_relevant: bool
    risk_level: Optional[str] = None
    
    class Config:
        from_attributes = True


class ComplianceRuleCreate(BaseModel):
    """Pydantic model for creating compliance rules."""
    name: str
    description: Optional[str] = None
    regulation_reference: Optional[str] = None
    rule_type: str
    rule_config: Dict[str, Any]
    applies_to_data_types: Optional[List[str]] = None
    applies_to_user_roles: Optional[List[str]] = None
    geographic_scope: Optional[List[str]] = None
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    check_frequency_hours: int = 24
    
    class Config:
        from_attributes = True


class ComplianceRuleResponse(BaseModel):
    """Pydantic model for compliance rule API responses."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    name: str
    description: Optional[str] = None
    regulation_reference: Optional[str] = None
    rule_type: str
    rule_config: Dict[str, Any]
    applies_to_data_types: Optional[List[str]] = None
    applies_to_user_roles: Optional[List[str]] = None
    geographic_scope: Optional[List[str]] = None
    is_active: bool
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    last_checked: Optional[datetime] = None
    check_frequency_hours: int
    
    class Config:
        from_attributes = True


class ComplianceCheckCreate(BaseModel):
    """Pydantic model for creating compliance checks."""
    rule_id: uuid.UUID
    check_type: str
    check_description: Optional[str] = None
    scope_checked: Optional[Dict[str, Any]] = None
    check_parameters: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class ComplianceCheckResponse(BaseModel):
    """Pydantic model for compliance check API responses."""
    id: uuid.UUID
    rule_id: uuid.UUID
    created_at: datetime
    check_type: str
    check_description: Optional[str] = None
    status: ComplianceStatusEnum
    compliance_score: Optional[float] = None
    violations_found: int
    violations_details: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    scope_checked: Optional[Dict[str, Any]] = None
    check_parameters: Optional[Dict[str, Any]] = None
    remediation_required: bool
    remediation_deadline: Optional[datetime] = None
    remediation_status: Optional[str] = None
    remediation_notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class DataRetentionPolicyCreate(BaseModel):
    """Pydantic model for creating data retention policies."""
    name: str
    description: Optional[str] = None
    data_type: str
    data_category: Optional[str] = None
    retention_period_days: int
    retention_trigger: str
    legal_basis: Optional[str] = None
    regulation_reference: Optional[str] = None
    auto_delete_enabled: bool = True
    archive_before_delete: bool = True
    archive_location: Optional[str] = None
    legal_hold_override: bool = True
    business_justification_override: bool = False
    effective_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DataRetentionPolicyResponse(BaseModel):
    """Pydantic model for data retention policy API responses."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    name: str
    description: Optional[str] = None
    data_type: str
    data_category: Optional[str] = None
    retention_period_days: int
    retention_trigger: str
    legal_basis: Optional[str] = None
    regulation_reference: Optional[str] = None
    auto_delete_enabled: bool
    archive_before_delete: bool
    archive_location: Optional[str] = None
    legal_hold_override: bool
    business_justification_override: bool
    is_active: bool
    effective_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DataRetentionRecordResponse(BaseModel):
    """Pydantic model for data retention record API responses."""
    id: uuid.UUID
    policy_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    data_type: str
    data_id: str
    data_location: Optional[str] = None
    data_created_at: datetime
    retention_deadline: datetime
    status: DataRetentionStatusEnum
    last_accessed: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    archive_location: Optional[str] = None
    deleted_at: Optional[datetime] = None
    legal_hold_active: bool
    legal_hold_reason: Optional[str] = None
    legal_hold_start_date: Optional[datetime] = None
    legal_hold_end_date: Optional[datetime] = None
    business_justification: Optional[str] = None
    processing_notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class RegulatoryReportCreate(BaseModel):
    """Pydantic model for creating regulatory reports."""
    report_name: str
    report_type: str
    regulation: str
    period_start: datetime
    period_end: datetime
    report_data: Dict[str, Any]
    summary_statistics: Optional[Dict[str, Any]] = None
    compliance_score: Optional[float] = None
    file_format: str = "json"
    
    class Config:
        from_attributes = True


class RegulatoryReportResponse(BaseModel):
    """Pydantic model for regulatory report API responses."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    report_name: str
    report_type: str
    regulation: str
    period_start: datetime
    period_end: datetime
    report_data: Dict[str, Any]
    summary_statistics: Optional[Dict[str, Any]] = None
    compliance_score: Optional[float] = None
    status: str
    generated_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    file_path: Optional[str] = None
    file_format: Optional[str] = None
    
    class Config:
        from_attributes = True


class AuditSearchRequest(BaseModel):
    """Pydantic model for audit log search requests."""
    event_types: Optional[List[AuditEventTypeEnum]] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    compliance_relevant: Optional[bool] = None
    security_relevant: Optional[bool] = None
    risk_level: Optional[str] = None
    limit: int = 100
    offset: int = 0
    
    class Config:
        from_attributes = True


class ComplianceDashboardResponse(BaseModel):
    """Pydantic model for compliance dashboard data."""
    total_rules: int
    active_rules: int
    recent_checks: int
    compliance_score: float
    violations_count: int
    pending_remediations: int
    data_retention_records: int
    upcoming_deadlines: List[Dict[str, Any]]
    compliance_trends: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True