"""
Deal Alert Models for Real Estate Deal Sourcing

This module defines the data models for real-time notifications, email alerts,
mobile push notifications, and alert preference management.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, EmailStr
from enum import Enum
import uuid
from datetime import datetime


class AlertTypeEnum(str, Enum):
    """Types of deal alerts"""
    NEW_DEAL = "new_deal"
    PRICE_DROP = "price_drop"
    HIGH_SCORE = "high_score"
    CRITERIA_MATCH = "criteria_match"
    MARKET_CHANGE = "market_change"
    NEIGHBORHOOD_UPDATE = "neighborhood_update"
    LEAD_RESPONSE = "lead_response"
    CONTRACT_UPDATE = "contract_update"
    DEADLINE_REMINDER = "deadline_reminder"
    SYSTEM_NOTIFICATION = "system_notification"


class AlertPriorityEnum(str, Enum):
    """Alert priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class AlertChannelEnum(str, Enum):
    """Alert delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class AlertStatusEnum(str, Enum):
    """Alert status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationFrequencyEnum(str, Enum):
    """Notification frequency options"""
    IMMEDIATE = "immediate"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    NEVER = "never"


class AlertPreference(BaseModel):
    """User alert preferences"""
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(..., description="User identifier")
    
    # Alert type preferences
    alert_type: AlertTypeEnum = Field(..., description="Type of alert")
    enabled: bool = Field(default=True, description="Whether this alert type is enabled")
    
    # Channel preferences
    email_enabled: bool = Field(default=True, description="Enable email notifications")
    sms_enabled: bool = Field(default=False, description="Enable SMS notifications")
    push_enabled: bool = Field(default=True, description="Enable push notifications")
    in_app_enabled: bool = Field(default=True, description="Enable in-app notifications")
    
    # Frequency and timing
    frequency: NotificationFrequencyEnum = Field(default=NotificationFrequencyEnum.IMMEDIATE)
    quiet_hours_start: Optional[str] = Field(None, description="Quiet hours start time (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="Quiet hours end time (HH:MM)")
    timezone: str = Field(default="UTC", description="User timezone")
    
    # Priority filtering
    min_priority: AlertPriorityEnum = Field(default=AlertPriorityEnum.LOW, description="Minimum priority to send")
    
    # Criteria-specific settings
    criteria_settings: Optional[Dict[str, Any]] = Field(None, description="Alert-specific criteria")
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True


class AlertRule(BaseModel):
    """Rule for triggering alerts"""
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(..., description="User identifier")
    name: str = Field(..., description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    
    # Rule conditions
    alert_type: AlertTypeEnum = Field(..., description="Type of alert to trigger")
    conditions: Dict[str, Any] = Field(..., description="Conditions that trigger the alert")
    
    # Alert settings
    priority: AlertPriorityEnum = Field(default=AlertPriorityEnum.MEDIUM)
    channels: List[AlertChannelEnum] = Field(default_factory=lambda: [AlertChannelEnum.EMAIL, AlertChannelEnum.IN_APP])
    
    # Rule status
    active: bool = Field(default=True, description="Whether the rule is active")
    
    # Throttling
    max_alerts_per_hour: Optional[int] = Field(None, ge=1, description="Maximum alerts per hour")
    max_alerts_per_day: Optional[int] = Field(None, ge=1, description="Maximum alerts per day")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = Field(None, description="When rule was last triggered")
    trigger_count: int = Field(default=0, ge=0, description="Number of times rule has been triggered")
    
    class Config:
        use_enum_values = True


class DealAlert(BaseModel):
    """Individual deal alert"""
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(..., description="User identifier")
    rule_id: Optional[uuid.UUID] = Field(None, description="Alert rule that triggered this")
    
    # Alert details
    alert_type: AlertTypeEnum = Field(..., description="Type of alert")
    priority: AlertPriorityEnum = Field(..., description="Alert priority")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    
    # Related data
    deal_id: Optional[uuid.UUID] = Field(None, description="Related deal ID")
    property_id: Optional[uuid.UUID] = Field(None, description="Related property ID")
    lead_id: Optional[uuid.UUID] = Field(None, description="Related lead ID")
    
    # Alert data
    alert_data: Optional[Dict[str, Any]] = Field(None, description="Additional alert data")
    
    # Delivery tracking
    channels: List[AlertChannelEnum] = Field(..., description="Channels to send alert on")
    status: AlertStatusEnum = Field(default=AlertStatusEnum.PENDING)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = Field(None, description="When to send the alert")
    sent_at: Optional[datetime] = Field(None, description="When alert was sent")
    delivered_at: Optional[datetime] = Field(None, description="When alert was delivered")
    read_at: Optional[datetime] = Field(None, description="When alert was read")
    
    # Delivery attempts
    delivery_attempts: int = Field(default=0, ge=0, description="Number of delivery attempts")
    max_delivery_attempts: int = Field(default=3, ge=1, description="Maximum delivery attempts")
    
    # Error tracking
    last_error: Optional[str] = Field(None, description="Last delivery error")
    
    class Config:
        use_enum_values = True


class AlertDelivery(BaseModel):
    """Alert delivery record"""
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    alert_id: uuid.UUID = Field(..., description="Alert identifier")
    channel: AlertChannelEnum = Field(..., description="Delivery channel")
    
    # Delivery details
    recipient: str = Field(..., description="Recipient (email, phone, device ID, etc.)")
    status: AlertStatusEnum = Field(..., description="Delivery status")
    
    # Delivery metadata
    provider: Optional[str] = Field(None, description="Service provider used")
    provider_message_id: Optional[str] = Field(None, description="Provider message ID")
    
    # Timestamps
    sent_at: Optional[datetime] = Field(None, description="When delivery was attempted")
    delivered_at: Optional[datetime] = Field(None, description="When delivery was confirmed")
    opened_at: Optional[datetime] = Field(None, description="When message was opened")
    clicked_at: Optional[datetime] = Field(None, description="When message was clicked")
    
    # Error tracking
    error_message: Optional[str] = Field(None, description="Error message if delivery failed")
    retry_count: int = Field(default=0, ge=0, description="Number of retry attempts")
    
    class Config:
        use_enum_values = True


class AlertTemplate(BaseModel):
    """Template for alert messages"""
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    name: str = Field(..., description="Template name")
    alert_type: AlertTypeEnum = Field(..., description="Alert type this template is for")
    channel: AlertChannelEnum = Field(..., description="Channel this template is for")
    
    # Template content
    subject_template: Optional[str] = Field(None, description="Subject line template")
    message_template: str = Field(..., description="Message body template")
    
    # Template variables
    required_variables: List[str] = Field(default_factory=list, description="Required template variables")
    optional_variables: List[str] = Field(default_factory=list, description="Optional template variables")
    
    # Template settings
    active: bool = Field(default=True, description="Whether template is active")
    default_for_type: bool = Field(default=False, description="Whether this is the default template for the alert type")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def render(self, variables: Dict[str, Any]) -> Dict[str, str]:
        """Render the template with provided variables"""
        # Simple template rendering - in production would use Jinja2 or similar
        subject = self.subject_template or ""
        message = self.message_template
        
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            subject = subject.replace(placeholder, str(value))
            message = message.replace(placeholder, str(value))
        
        return {
            "subject": subject,
            "message": message
        }
    
    class Config:
        use_enum_values = True


class AlertBatch(BaseModel):
    """Batch of alerts for processing"""
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    name: Optional[str] = Field(None, description="Batch name")
    
    # Batch details
    alert_ids: List[uuid.UUID] = Field(..., description="Alert IDs in this batch")
    total_alerts: int = Field(..., ge=0, description="Total number of alerts")
    
    # Processing status
    status: str = Field(default="pending", description="Batch processing status")
    processed_count: int = Field(default=0, ge=0, description="Number of processed alerts")
    success_count: int = Field(default=0, ge=0, description="Number of successful deliveries")
    failed_count: int = Field(default=0, ge=0, description="Number of failed deliveries")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = Field(None, description="When processing started")
    completed_at: Optional[datetime] = Field(None, description="When processing completed")
    
    # Processing metadata
    processing_time_seconds: Optional[float] = Field(None, ge=0, description="Total processing time")
    errors: List[str] = Field(default_factory=list, description="Processing errors")


class AlertAnalytics(BaseModel):
    """Analytics for alert system performance"""
    # Time period
    period_start: datetime = Field(..., description="Analytics period start")
    period_end: datetime = Field(..., description="Analytics period end")
    
    # Volume metrics
    total_alerts_created: int = Field(..., ge=0, description="Total alerts created")
    total_alerts_sent: int = Field(..., ge=0, description="Total alerts sent")
    total_alerts_delivered: int = Field(..., ge=0, description="Total alerts delivered")
    total_alerts_read: int = Field(..., ge=0, description="Total alerts read")
    
    # Performance metrics
    delivery_rate: float = Field(..., ge=0, le=1, description="Delivery success rate")
    read_rate: float = Field(..., ge=0, le=1, description="Read rate")
    average_delivery_time_seconds: Optional[float] = Field(None, ge=0, description="Average delivery time")
    
    # Channel breakdown
    channel_stats: Dict[AlertChannelEnum, Dict[str, int]] = Field(
        default_factory=dict,
        description="Statistics by channel"
    )
    
    # Alert type breakdown
    type_stats: Dict[AlertTypeEnum, Dict[str, int]] = Field(
        default_factory=dict,
        description="Statistics by alert type"
    )
    
    # Priority breakdown
    priority_stats: Dict[AlertPriorityEnum, Dict[str, int]] = Field(
        default_factory=dict,
        description="Statistics by priority"
    )
    
    # User engagement
    active_users: int = Field(..., ge=0, description="Number of users who received alerts")
    engaged_users: int = Field(..., ge=0, description="Number of users who read alerts")
    
    # Error analysis
    top_errors: List[Dict[str, Any]] = Field(default_factory=list, description="Most common errors")
    
    generated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True


class AlertSubscription(BaseModel):
    """User subscription to specific alert criteria"""
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(..., description="User identifier")
    name: str = Field(..., description="Subscription name")
    description: Optional[str] = Field(None, description="Subscription description")
    
    # Subscription criteria
    criteria: Dict[str, Any] = Field(..., description="Criteria for matching deals")
    
    # Alert settings
    alert_types: List[AlertTypeEnum] = Field(
        default_factory=lambda: [AlertTypeEnum.NEW_DEAL, AlertTypeEnum.CRITERIA_MATCH],
        description="Types of alerts to send"
    )
    
    # Delivery preferences
    channels: List[AlertChannelEnum] = Field(
        default_factory=lambda: [AlertChannelEnum.EMAIL, AlertChannelEnum.IN_APP],
        description="Delivery channels"
    )
    frequency: NotificationFrequencyEnum = Field(
        default=NotificationFrequencyEnum.IMMEDIATE,
        description="Notification frequency"
    )
    
    # Subscription status
    active: bool = Field(default=True, description="Whether subscription is active")
    
    # Usage tracking
    alerts_sent: int = Field(default=0, ge=0, description="Number of alerts sent")
    last_alert_sent: Optional[datetime] = Field(None, description="When last alert was sent")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True


class AlertQueue(BaseModel):
    """Queue for managing alert processing"""
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    name: str = Field(..., description="Queue name")
    
    # Queue configuration
    max_size: Optional[int] = Field(None, ge=1, description="Maximum queue size")
    priority_enabled: bool = Field(default=True, description="Whether to process by priority")
    
    # Queue status
    current_size: int = Field(default=0, ge=0, description="Current number of items in queue")
    processing: bool = Field(default=False, description="Whether queue is being processed")
    
    # Processing statistics
    total_processed: int = Field(default=0, ge=0, description="Total items processed")
    total_failed: int = Field(default=0, ge=0, description="Total items failed")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    last_processed_at: Optional[datetime] = Field(None, description="When queue was last processed")
    
    # Performance metrics
    average_processing_time: Optional[float] = Field(None, ge=0, description="Average processing time per item")
    throughput_per_minute: Optional[float] = Field(None, ge=0, description="Items processed per minute")


class WebhookEndpoint(BaseModel):
    """Webhook endpoint for alert delivery"""
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(..., description="User identifier")
    name: str = Field(..., description="Endpoint name")
    
    # Endpoint configuration
    url: str = Field(..., description="Webhook URL")
    method: str = Field(default="POST", description="HTTP method")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom headers")
    
    # Security
    secret: Optional[str] = Field(None, description="Webhook secret for verification")
    
    # Alert filtering
    alert_types: List[AlertTypeEnum] = Field(
        default_factory=list,
        description="Alert types to send to this webhook"
    )
    
    # Status and reliability
    active: bool = Field(default=True, description="Whether endpoint is active")
    last_success: Optional[datetime] = Field(None, description="Last successful delivery")
    last_failure: Optional[datetime] = Field(None, description="Last failed delivery")
    failure_count: int = Field(default=0, ge=0, description="Consecutive failure count")
    
    # Rate limiting
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, description="Rate limit per minute")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True