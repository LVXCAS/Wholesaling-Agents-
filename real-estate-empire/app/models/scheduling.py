"""
Scheduling and appointment models for the real estate empire system.
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, validator
import uuid


class AppointmentType(str, Enum):
    """Appointment types."""
    PROPERTY_VIEWING = "property_viewing"
    PHONE_CALL = "phone_call"
    VIDEO_CALL = "video_call"
    IN_PERSON_MEETING = "in_person_meeting"
    INSPECTION = "inspection"
    CLOSING = "closing"
    FOLLOW_UP = "follow_up"


class AppointmentStatus(str, Enum):
    """Appointment status types."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class ReminderType(str, Enum):
    """Reminder types."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    VOICE = "voice"


class RecurrenceType(str, Enum):
    """Recurrence types."""
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class AvailabilitySlot(BaseModel):
    """Availability slot model."""
    id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    is_available: bool = True
    buffer_minutes: int = 15  # Buffer time between appointments
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @validator('end_time')
    def end_time_after_start_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v


class Appointment(BaseModel):
    """Appointment model."""
    id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    appointment_type: AppointmentType
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    
    # Participants
    organizer_id: uuid.UUID
    attendee_contact_id: Optional[uuid.UUID] = None
    attendee_name: Optional[str] = None
    attendee_email: Optional[str] = None
    attendee_phone: Optional[str] = None
    
    # Timing
    start_time: datetime
    end_time: datetime
    timezone: str = "UTC"
    duration_minutes: Optional[int] = None
    
    # Location/Meeting details
    location: Optional[str] = None
    meeting_url: Optional[str] = None
    meeting_id: Optional[str] = None
    meeting_password: Optional[str] = None
    
    # Related entities
    property_id: Optional[uuid.UUID] = None
    lead_id: Optional[uuid.UUID] = None
    deal_id: Optional[uuid.UUID] = None
    
    # Recurrence
    recurrence_type: RecurrenceType = RecurrenceType.NONE
    recurrence_interval: int = 1
    recurrence_end_date: Optional[datetime] = None
    parent_appointment_id: Optional[uuid.UUID] = None  # For recurring appointments
    
    # Reminders
    reminders_enabled: bool = True
    reminder_minutes_before: List[int] = [15, 60]  # Default reminders
    
    # Metadata
    notes: Optional[str] = None
    tags: List[str] = []
    metadata: Optional[Dict[str, Any]] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @validator('end_time')
    def end_time_after_start_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

    @validator('duration_minutes', always=True)
    def calculate_duration(cls, v, values):
        if v is None and 'start_time' in values and 'end_time' in values:
            delta = values['end_time'] - values['start_time']
            return int(delta.total_seconds() / 60)
        return v


class AppointmentReminder(BaseModel):
    """Appointment reminder model."""
    id: Optional[uuid.UUID] = None
    appointment_id: uuid.UUID
    reminder_type: ReminderType
    minutes_before: int
    scheduled_time: datetime
    sent_at: Optional[datetime] = None
    status: str = "pending"  # pending, sent, failed
    message_content: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CalendarIntegration(BaseModel):
    """Calendar integration settings."""
    id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    provider: str  # "google", "outlook", "apple", "caldav"
    calendar_id: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    sync_enabled: bool = True
    last_sync_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BookingLink(BaseModel):
    """Public booking link for appointments."""
    id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    name: str
    slug: str  # URL-friendly identifier
    description: Optional[str] = None
    
    # Appointment settings
    appointment_type: AppointmentType
    duration_minutes: int
    buffer_minutes: int = 15
    
    # Availability
    available_days: List[int] = [1, 2, 3, 4, 5]  # Monday=1, Sunday=7
    available_time_start: str = "09:00"  # HH:MM format
    available_time_end: str = "17:00"    # HH:MM format
    timezone: str = "UTC"
    
    # Booking limits
    max_days_in_advance: int = 30
    min_hours_in_advance: int = 2
    max_bookings_per_day: Optional[int] = None
    
    # Form fields
    require_name: bool = True
    require_email: bool = True
    require_phone: bool = False
    custom_fields: List[Dict[str, Any]] = []
    
    # Notifications
    send_confirmation: bool = True
    send_reminders: bool = True
    
    # Status
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FollowUpTask(BaseModel):
    """Follow-up task model."""
    id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    
    # Assignment
    assigned_to: uuid.UUID
    contact_id: Optional[uuid.UUID] = None
    lead_id: Optional[uuid.UUID] = None
    deal_id: Optional[uuid.UUID] = None
    property_id: Optional[uuid.UUID] = None
    
    # Timing
    due_date: datetime
    priority: str = "normal"  # low, normal, high, urgent
    
    # Task details
    task_type: str = "general"  # general, call, email, meeting, research
    estimated_duration_minutes: Optional[int] = None
    
    # Status
    status: str = "pending"  # pending, in_progress, completed, cancelled
    completed_at: Optional[datetime] = None
    
    # Automation
    auto_generated: bool = False
    trigger_event: Optional[str] = None
    
    # Metadata
    notes: Optional[str] = None
    tags: List[str] = []
    metadata: Optional[Dict[str, Any]] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FollowUpSequence(BaseModel):
    """Follow-up sequence template."""
    id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None
    
    # Trigger conditions
    trigger_event: str  # "lead_created", "no_response", "appointment_completed", etc.
    trigger_delay_hours: int = 0
    
    # Sequence steps
    steps: List[Dict[str, Any]] = []  # Each step defines timing, type, and content
    
    # Status
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class NurturingCampaign(BaseModel):
    """Long-term nurturing campaign model."""
    id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None
    
    # Target criteria
    target_lead_status: List[str] = []
    target_lead_score_min: Optional[float] = None
    target_lead_score_max: Optional[float] = None
    target_tags: List[str] = []
    
    # Campaign content
    content_sequence: List[Dict[str, Any]] = []  # Content items with timing
    
    # Settings
    frequency_days: int = 7  # How often to send content
    max_duration_days: Optional[int] = None
    pause_on_engagement: bool = True
    
    # Status
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class EngagementTracking(BaseModel):
    """Engagement tracking for nurturing campaigns."""
    id: Optional[uuid.UUID] = None
    contact_id: uuid.UUID
    campaign_id: uuid.UUID
    
    # Engagement metrics
    emails_sent: int = 0
    emails_opened: int = 0
    emails_clicked: int = 0
    calls_made: int = 0
    calls_answered: int = 0
    meetings_scheduled: int = 0
    meetings_attended: int = 0
    
    # Scoring
    engagement_score: float = 0.0
    last_engagement_date: Optional[datetime] = None
    
    # Status
    campaign_status: str = "active"  # active, paused, completed, unsubscribed
    
    # Timestamps
    started_at: datetime
    last_updated_at: Optional[datetime] = None