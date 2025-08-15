"""
Transaction workflow models for the real estate empire system.
Handles transaction milestones, workflows, due diligence, and closing coordination.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class TransactionStatus(str, Enum):
    """Status of a real estate transaction."""
    INITIATED = "initiated"
    UNDER_CONTRACT = "under_contract"
    DUE_DILIGENCE = "due_diligence"
    FINANCING = "financing"
    APPRAISAL = "appraisal"
    INSPECTION = "inspection"
    CLOSING_PREP = "closing_prep"
    CLOSING = "closing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class MilestoneStatus(str, Enum):
    """Status of individual milestones."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    """Priority levels for tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Status of individual tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class DocumentStatus(str, Enum):
    """Status of transaction documents."""
    REQUIRED = "required"
    REQUESTED = "requested"
    RECEIVED = "received"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"
    MISSING = "missing"


class ComplianceStatus(str, Enum):
    """Compliance check status."""
    PENDING = "pending"
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    REQUIRES_REVIEW = "requires_review"


class TransactionTask(BaseModel):
    """Individual task within a transaction milestone."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_to: Optional[str] = None  # User ID or role
    assigned_to_type: str = "user"  # "user", "role", "agent", "external"
    
    # Timing
    due_date: Optional[datetime] = None
    estimated_duration: Optional[int] = None  # minutes
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Dependencies
    depends_on: List[UUID] = Field(default_factory=list)  # Other task IDs
    blocks: List[UUID] = Field(default_factory=list)  # Tasks this blocks
    
    # Task details
    task_type: str = "manual"  # "manual", "automated", "document", "approval"
    automation_config: Dict[str, Any] = Field(default_factory=dict)
    required_documents: List[str] = Field(default_factory=list)
    completion_criteria: List[str] = Field(default_factory=list)
    
    # Progress tracking
    progress_percentage: int = 0
    notes: List[str] = Field(default_factory=list)
    attachments: List[str] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class TransactionMilestone(BaseModel):
    """Major milestone in a transaction workflow."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    status: MilestoneStatus = MilestoneStatus.NOT_STARTED
    order: int  # Sequence order in workflow
    
    # Timing
    target_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    actual_completion_date: Optional[datetime] = None
    estimated_duration: Optional[int] = None  # days
    
    # Tasks
    tasks: List[TransactionTask] = Field(default_factory=list)
    required_approvals: List[str] = Field(default_factory=list)
    
    # Dependencies
    depends_on_milestones: List[UUID] = Field(default_factory=list)
    
    # Milestone configuration
    is_critical: bool = False
    can_run_parallel: bool = True
    auto_start: bool = False
    auto_complete: bool = False
    
    # Progress tracking
    progress_percentage: int = 0
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class TransactionWorkflow(BaseModel):
    """Complete workflow definition for a transaction type."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    transaction_type: str  # "purchase", "wholesale", "refinance", etc.
    version: str = "1.0"
    
    # Workflow structure
    milestones: List[TransactionMilestone] = Field(default_factory=list)
    workflow_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Default settings
    default_timeline_days: int = 30
    critical_path_buffer_days: int = 3
    
    # Automation settings
    auto_task_generation: bool = True
    auto_deadline_monitoring: bool = True
    auto_notifications: bool = True
    
    # Metadata
    is_active: bool = True
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class TransactionInstance(BaseModel):
    """Active instance of a transaction workflow."""
    id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    deal_id: Optional[UUID] = None
    contract_id: Optional[UUID] = None
    
    # Transaction details
    property_address: str
    transaction_type: str
    status: TransactionStatus = TransactionStatus.INITIATED
    
    # Parties
    buyer: Optional[str] = None
    seller: Optional[str] = None
    buyer_agent: Optional[str] = None
    seller_agent: Optional[str] = None
    lender: Optional[str] = None
    title_company: Optional[str] = None
    attorney: Optional[str] = None
    
    # Key dates
    contract_date: Optional[datetime] = None
    closing_date: Optional[datetime] = None
    inspection_deadline: Optional[datetime] = None
    financing_deadline: Optional[datetime] = None
    appraisal_deadline: Optional[datetime] = None
    
    # Financial details
    purchase_price: Optional[float] = None
    earnest_money: Optional[float] = None
    loan_amount: Optional[float] = None
    
    # Current workflow state
    current_milestones: List[TransactionMilestone] = Field(default_factory=list)
    completed_milestones: List[UUID] = Field(default_factory=list)
    active_tasks: List[UUID] = Field(default_factory=list)
    overdue_tasks: List[UUID] = Field(default_factory=list)
    
    # Progress tracking
    overall_progress: int = 0
    critical_path_status: str = "on_track"  # "on_track", "at_risk", "delayed"
    
    # Alerts and notifications
    active_alerts: List[Dict[str, Any]] = Field(default_factory=list)
    notification_settings: Dict[str, bool] = Field(default_factory=dict)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class DueDiligenceItem(BaseModel):
    """Individual due diligence checklist item."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    category: str  # "financial", "legal", "physical", "environmental", etc.
    priority: TaskPriority = TaskPriority.MEDIUM
    
    # Status and completion
    status: DocumentStatus = DocumentStatus.REQUIRED
    is_required: bool = True
    completion_percentage: int = 0
    
    # Document requirements
    required_documents: List[str] = Field(default_factory=list)
    received_documents: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Review and approval
    reviewer: Optional[str] = None
    review_notes: List[str] = Field(default_factory=list)
    approval_required: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    # Risk assessment
    risk_level: str = "low"  # "low", "medium", "high", "critical"
    risk_factors: List[str] = Field(default_factory=list)
    mitigation_actions: List[str] = Field(default_factory=list)
    
    # Timing
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class DueDiligenceChecklist(BaseModel):
    """Complete due diligence checklist for a transaction."""
    id: UUID = Field(default_factory=uuid4)
    transaction_id: UUID
    name: str
    description: str
    
    # Checklist items
    items: List[DueDiligenceItem] = Field(default_factory=list)
    
    # Progress tracking
    total_items: int = 0
    completed_items: int = 0
    completion_percentage: int = 0
    
    # Risk assessment
    overall_risk_level: str = "low"
    identified_risks: List[str] = Field(default_factory=list)
    risk_mitigation_plan: List[str] = Field(default_factory=list)
    
    # Compliance
    compliance_status: ComplianceStatus = ComplianceStatus.PENDING
    compliance_notes: List[str] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class ClosingCoordination(BaseModel):
    """Closing coordination and timeline management."""
    id: UUID = Field(default_factory=uuid4)
    transaction_id: UUID
    
    # Closing details
    closing_date: datetime
    closing_time: Optional[str] = None
    closing_location: Optional[str] = None
    closing_agent: Optional[str] = None
    
    # Parties coordination
    required_attendees: List[Dict[str, Any]] = Field(default_factory=list)
    confirmed_attendees: List[str] = Field(default_factory=list)
    
    # Document preparation
    required_documents: List[str] = Field(default_factory=list)
    prepared_documents: List[Dict[str, Any]] = Field(default_factory=list)
    document_review_status: Dict[str, str] = Field(default_factory=dict)
    
    # Funds coordination
    funds_required: Dict[str, float] = Field(default_factory=dict)  # party -> amount
    funds_confirmed: Dict[str, bool] = Field(default_factory=dict)
    wire_instructions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Final walkthrough
    walkthrough_scheduled: bool = False
    walkthrough_date: Optional[datetime] = None
    walkthrough_completed: bool = False
    walkthrough_issues: List[str] = Field(default_factory=list)
    
    # Closing timeline
    timeline_tasks: List[TransactionTask] = Field(default_factory=list)
    critical_deadlines: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Status tracking
    coordination_status: str = "planning"  # "planning", "coordinating", "ready", "completed"
    issues: List[str] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class TransactionAlert(BaseModel):
    """Alert or notification for transaction events."""
    id: UUID = Field(default_factory=uuid4)
    transaction_id: UUID
    alert_type: str  # "deadline", "overdue", "risk", "milestone", "document"
    severity: str = "medium"  # "low", "medium", "high", "critical"
    
    # Alert content
    title: str
    message: str
    action_required: bool = False
    suggested_actions: List[str] = Field(default_factory=list)
    
    # Recipients
    recipients: List[str] = Field(default_factory=list)
    notification_channels: List[str] = Field(default_factory=list)  # "email", "sms", "app"
    
    # Status
    is_active: bool = True
    acknowledged_by: List[str] = Field(default_factory=list)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


class TransactionReport(BaseModel):
    """Comprehensive transaction status report."""
    transaction_id: UUID
    generated_at: datetime = Field(default_factory=datetime.now)
    
    # Summary
    transaction_summary: Dict[str, Any] = Field(default_factory=dict)
    current_status: TransactionStatus
    overall_progress: int
    
    # Timeline analysis
    timeline_analysis: Dict[str, Any] = Field(default_factory=dict)
    critical_path_status: str
    projected_closing_date: Optional[datetime] = None
    
    # Task and milestone status
    milestone_progress: List[Dict[str, Any]] = Field(default_factory=list)
    task_summary: Dict[str, int] = Field(default_factory=dict)
    overdue_items: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Risk assessment
    risk_assessment: Dict[str, Any] = Field(default_factory=dict)
    identified_issues: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    
    # Due diligence status
    due_diligence_summary: Dict[str, Any] = Field(default_factory=dict)
    
    # Document status
    document_summary: Dict[str, Any] = Field(default_factory=dict)
    
    # Financial summary
    financial_summary: Dict[str, Any] = Field(default_factory=dict)