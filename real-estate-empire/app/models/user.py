"""
User authentication and authorization models.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr
from app.core.database import Base

class UserDB(Base):
    """User database model."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, nullable=False, default="viewer")
    permissions = Column(JSON, nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    
    # Security tracking
    failed_login_attempts = Column(Integer, default=0)
    last_login = Column(DateTime, nullable=True)
    last_failed_login = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    
    # MFA settings
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String, nullable=True)
    backup_codes = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime, nullable=True)
    
    # Profile information
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    timezone = Column(String, default="UTC")
    preferences = Column(JSON, nullable=True)

class SessionDB(Base):
    """User session database model."""
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    token_hash = Column(String, nullable=False)
    refresh_token_hash = Column(String, nullable=True)
    
    # Session metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    device_info = Column(JSON, nullable=True)
    
    # Session timing
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Session status
    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(String, nullable=True)

class APIKeyDB(Base):
    """API key database model."""
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    key_hash = Column(String, nullable=False, unique=True)
    
    # Permissions and scope
    permissions = Column(JSON, nullable=True)
    scopes = Column(JSON, nullable=True)
    rate_limit = Column(Integer, nullable=True)
    
    # Key status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Usage tracking
    last_used = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Pydantic models for API

class UserBase(BaseModel):
    """Base user model."""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "viewer"
    phone: Optional[str] = None
    company: Optional[str] = None
    timezone: str = "UTC"

class UserCreate(UserBase):
    """User creation model."""
    password: str

class UserUpdate(BaseModel):
    """User update model."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None
    preferences: Optional[Dict[str, Any]] = None

class UserResponse(UserBase):
    """User response model."""
    id: str
    is_active: bool
    is_verified: bool
    is_locked: bool
    mfa_enabled: bool
    created_at: datetime
    last_login: Optional[datetime]
    last_activity: Optional[datetime]
    permissions: Optional[List[str]] = None
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    """User login model."""
    username: str
    password: str
    remember_me: bool = False
    mfa_code: Optional[str] = None

class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class PasswordChange(BaseModel):
    """Password change model."""
    current_password: str
    new_password: str

class PasswordReset(BaseModel):
    """Password reset model."""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model."""
    token: str
    new_password: str

class MFASetup(BaseModel):
    """MFA setup model."""
    secret: str
    qr_code: str
    backup_codes: List[str]

class MFAVerify(BaseModel):
    """MFA verification model."""
    code: str

class APIKeyCreate(BaseModel):
    """API key creation model."""
    name: str
    permissions: Optional[List[str]] = None
    scopes: Optional[List[str]] = None
    expires_in_days: Optional[int] = None
    rate_limit: Optional[int] = None

class APIKeyResponse(BaseModel):
    """API key response model."""
    id: str
    name: str
    key: str  # Only returned on creation
    permissions: Optional[List[str]]
    scopes: Optional[List[str]]
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime
    last_used: Optional[datetime]
    usage_count: int
    
    class Config:
        from_attributes = True

class SessionInfo(BaseModel):
    """Session information model."""
    id: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_info: Optional[Dict[str, Any]]
    created_at: datetime
    last_activity: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class UserActivity(BaseModel):
    """User activity model."""
    user_id: str
    action: str
    resource: Optional[str]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime
    success: bool

class SecuritySettings(BaseModel):
    """Security settings model."""
    password_min_length: int
    require_uppercase: bool
    require_lowercase: bool
    require_numbers: bool
    require_special_chars: bool
    max_login_attempts: int
    lockout_duration_minutes: int
    session_timeout_minutes: int
    require_mfa: bool
    password_expiry_days: Optional[int]

class ComplianceReport(BaseModel):
    """Compliance report model."""
    report_id: str
    report_type: str
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    total_users: int
    active_users: int
    locked_users: int
    failed_login_attempts: int
    successful_logins: int
    password_changes: int
    mfa_enabled_users: int
    api_key_usage: int
    security_events: List[Dict[str, Any]]
    compliance_status: str
    recommendations: List[str]