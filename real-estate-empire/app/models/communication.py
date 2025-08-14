"""
Communication models for email, SMS, and voice services.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, EmailStr
import uuid


class CommunicationChannel(str, Enum):
    """Communication channel types."""
    EMAIL = "email"
    SMS = "sms"
    VOICE = "voice"


class MessageStatus(str, Enum):
    """Message status types."""
    DRAFT = "draft"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    FAILED = "failed"


class MessagePriority(str, Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class EmailTemplate(BaseModel):
    """Email template model."""
    id: Optional[uuid.UUID] = None
    name: str
    subject: str
    body_html: str
    body_text: str
    variables: List[str] = []
    category: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SMSTemplate(BaseModel):
    """SMS template model."""
    id: Optional[uuid.UUID] = None
    name: str
    message: str
    variables: List[str] = []
    category: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class VoiceScript(BaseModel):
    """Voice script model."""
    id: Optional[uuid.UUID] = None
    name: str
    script: str
    variables: List[str] = []
    category: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ContactInfo(BaseModel):
    """Contact information model."""
    id: Optional[uuid.UUID] = None
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    preferred_channel: Optional[CommunicationChannel] = None


class EmailMessage(BaseModel):
    """Email message model."""
    id: Optional[uuid.UUID] = None
    to_email: EmailStr
    to_name: Optional[str] = None
    from_email: Optional[EmailStr] = None
    from_name: Optional[str] = None
    subject: str
    body_html: str
    body_text: str
    template_id: Optional[uuid.UUID] = None
    template_variables: Optional[Dict[str, Any]] = None
    status: MessageStatus = MessageStatus.DRAFT
    priority: MessagePriority = MessagePriority.NORMAL
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    bounced_at: Optional[datetime] = None
    bounce_reason: Optional[str] = None
    reply_to: Optional[EmailStr] = None
    tags: List[str] = []
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SMSMessage(BaseModel):
    """SMS message model."""
    id: Optional[uuid.UUID] = None
    to_phone: str
    from_phone: Optional[str] = None
    message: str
    template_id: Optional[uuid.UUID] = None
    template_variables: Optional[Dict[str, Any]] = None
    status: MessageStatus = MessageStatus.DRAFT
    priority: MessagePriority = MessagePriority.NORMAL
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    tags: List[str] = []
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class VoiceCall(BaseModel):
    """Voice call model."""
    id: Optional[uuid.UUID] = None
    to_phone: str
    from_phone: Optional[str] = None
    script_id: Optional[uuid.UUID] = None
    script_variables: Optional[Dict[str, Any]] = None
    status: MessageStatus = MessageStatus.DRAFT
    priority: MessagePriority = MessagePriority.NORMAL
    scheduled_at: Optional[datetime] = None
    initiated_at: Optional[datetime] = None
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    recording_url: Optional[str] = None
    transcription: Optional[str] = None
    voicemail_dropped: bool = False
    tags: List[str] = []
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CommunicationHistory(BaseModel):
    """Communication history model."""
    id: Optional[uuid.UUID] = None
    contact_id: uuid.UUID
    channel: CommunicationChannel
    message_id: uuid.UUID
    direction: str  # "outbound" or "inbound"
    subject: Optional[str] = None
    content: str
    status: MessageStatus
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class CommunicationAnalytics(BaseModel):
    """Communication analytics model."""
    channel: CommunicationChannel
    total_sent: int = 0
    total_delivered: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    total_replied: int = 0
    total_bounced: int = 0
    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    reply_rate: float = 0.0
    bounce_rate: float = 0.0
    period_start: datetime
    period_end: datetime


class CommunicationPreferences(BaseModel):
    """Communication preferences model."""
    contact_id: uuid.UUID
    email_enabled: bool = True
    sms_enabled: bool = True
    voice_enabled: bool = True
    preferred_channel: Optional[CommunicationChannel] = None
    preferred_time_start: Optional[str] = None  # HH:MM format
    preferred_time_end: Optional[str] = None    # HH:MM format
    timezone: Optional[str] = None
    do_not_contact: bool = False
    unsubscribed_channels: List[CommunicationChannel] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None