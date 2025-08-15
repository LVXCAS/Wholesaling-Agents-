"""
Security configuration and environment setup.
Manages security settings, environment variables, and configuration validation.
"""

import os
import secrets
from typing import Dict, Any, List, Optional
from pydantic import BaseSettings, validator
from cryptography.fernet import Fernet

class SecuritySettings(BaseSettings):
    """Security settings from environment variables."""
    
    # JWT Settings
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Encryption Settings
    ENCRYPTION_KEY: str = Fernet.generate_key().decode()
    DATABASE_ENCRYPTION_KEY: str = Fernet.generate_key().decode()
    
    # Password Policy
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL_CHARS: bool = True
    PASSWORD_EXPIRY_DAYS: Optional[int] = None
    
    # Account Security
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    SESSION_TIMEOUT_MINUTES: int = 60
    REQUIRE_MFA: bool = False
    
    # API Security
    API_RATE_LIMIT_PER_MINUTE: int = 100
    API_RATE_LIMIT_PER_HOUR: int = 1000
    API_KEY_EXPIRY_DAYS: int = 365
    
    # HTTPS and TLS
    FORCE_HTTPS: bool = True
    TLS_VERSION: str = "1.2"
    HSTS_MAX_AGE: int = 31536000  # 1 year
    
    # CORS Settings
    CORS_ALLOWED_ORIGINS: List[str] = ["https://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOWED_HEADERS: List[str] = ["*"]
    
    # Security Headers
    CONTENT_SECURITY_POLICY: str = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    X_FRAME_OPTIONS: str = "DENY"
    X_CONTENT_TYPE_OPTIONS: str = "nosniff"
    X_XSS_PROTECTION: str = "1; mode=block"
    REFERRER_POLICY: str = "strict-origin-when-cross-origin"
    
    # Data Protection
    DATA_RETENTION_DAYS: int = 2555  # 7 years default
    GDPR_COMPLIANCE: bool = True
    CCPA_COMPLIANCE: bool = True
    AUTO_DELETE_EXPIRED_DATA: bool = True
    ANONYMIZE_DELETED_DATA: bool = True
    
    # Audit and Logging
    AUDIT_LOG_RETENTION_DAYS: int = 2555  # 7 years
    SECURITY_LOG_LEVEL: str = "INFO"
    LOG_SENSITIVE_DATA: bool = False
    ENABLE_AUDIT_TRAIL: bool = True
    
    # External Service Security
    WEBHOOK_SECRET_KEY: str = secrets.token_urlsafe(32)
    API_WEBHOOK_TIMEOUT: int = 30
    EXTERNAL_API_TIMEOUT: int = 30
    
    # Database Security
    DATABASE_SSL_MODE: str = "require"
    DATABASE_SSL_CERT: Optional[str] = None
    DATABASE_SSL_KEY: Optional[str] = None
    DATABASE_SSL_CA: Optional[str] = None
    
    # Backup and Recovery
    BACKUP_ENCRYPTION_KEY: str = Fernet.generate_key().decode()
    BACKUP_RETENTION_DAYS: int = 90
    ENABLE_POINT_IN_TIME_RECOVERY: bool = True
    
    # Monitoring and Alerting
    SECURITY_ALERT_EMAIL: Optional[str] = None
    SECURITY_ALERT_WEBHOOK: Optional[str] = None
    FAILED_LOGIN_ALERT_THRESHOLD: int = 10
    SUSPICIOUS_ACTIVITY_ALERT: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @validator('CORS_ALLOWED_ORIGINS', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('CORS_ALLOWED_METHODS', pre=True)
    def parse_cors_methods(cls, v):
        if isinstance(v, str):
            return [method.strip() for method in v.split(',')]
        return v
    
    @validator('CORS_ALLOWED_HEADERS', pre=True)
    def parse_cors_headers(cls, v):
        if isinstance(v, str):
            return [header.strip() for header in v.split(',')]
        return v

class SecurityConfigManager:
    """Security configuration manager."""
    
    def __init__(self):
        self.settings = SecuritySettings()
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Validate security configuration."""
        errors = []
        
        # Validate JWT settings
        if len(self.settings.SECRET_KEY) < 32:
            errors.append("SECRET_KEY must be at least 32 characters long")
        
        # Validate encryption keys
        try:
            Fernet(self.settings.ENCRYPTION_KEY.encode())
        except Exception:
            errors.append("ENCRYPTION_KEY is not a valid Fernet key")
        
        try:
            Fernet(self.settings.DATABASE_ENCRYPTION_KEY.encode())
        except Exception:
            errors.append("DATABASE_ENCRYPTION_KEY is not a valid Fernet key")
        
        # Validate password policy
        if self.settings.PASSWORD_MIN_LENGTH < 8:
            errors.append("PASSWORD_MIN_LENGTH should be at least 8")
        
        # Validate timeouts
        if self.settings.SESSION_TIMEOUT_MINUTES < 5:
            errors.append("SESSION_TIMEOUT_MINUTES should be at least 5 minutes")
        
        if self.settings.LOCKOUT_DURATION_MINUTES < 1:
            errors.append("LOCKOUT_DURATION_MINUTES should be at least 1 minute")
        
        # Validate HTTPS settings
        if not self.settings.FORCE_HTTPS and os.getenv("ENVIRONMENT") == "production":
            errors.append("FORCE_HTTPS should be enabled in production")
        
        if errors:
            raise ValueError(f"Security configuration errors: {'; '.join(errors)}")
    
    def get_jwt_config(self) -> Dict[str, Any]:
        """Get JWT configuration."""
        return {
            "secret_key": self.settings.SECRET_KEY,
            "algorithm": self.settings.ALGORITHM,
            "access_token_expire_minutes": self.settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "refresh_token_expire_days": self.settings.REFRESH_TOKEN_EXPIRE_DAYS
        }
    
    def get_password_policy(self) -> Dict[str, Any]:
        """Get password policy configuration."""
        return {
            "min_length": self.settings.PASSWORD_MIN_LENGTH,
            "require_uppercase": self.settings.PASSWORD_REQUIRE_UPPERCASE,
            "require_lowercase": self.settings.PASSWORD_REQUIRE_LOWERCASE,
            "require_numbers": self.settings.PASSWORD_REQUIRE_NUMBERS,
            "require_special_chars": self.settings.PASSWORD_REQUIRE_SPECIAL_CHARS,
            "expiry_days": self.settings.PASSWORD_EXPIRY_DAYS
        }
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers configuration."""
        return {
            "Content-Security-Policy": self.settings.CONTENT_SECURITY_POLICY,
            "X-Frame-Options": self.settings.X_FRAME_OPTIONS,
            "X-Content-Type-Options": self.settings.X_CONTENT_TYPE_OPTIONS,
            "X-XSS-Protection": self.settings.X_XSS_PROTECTION,
            "Referrer-Policy": self.settings.REFERRER_POLICY,
            "Strict-Transport-Security": f"max-age={self.settings.HSTS_MAX_AGE}; includeSubDomains"
        }
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration."""
        return {
            "allow_origins": self.settings.CORS_ALLOWED_ORIGINS,
            "allow_credentials": self.settings.CORS_ALLOW_CREDENTIALS,
            "allow_methods": self.settings.CORS_ALLOWED_METHODS,
            "allow_headers": self.settings.CORS_ALLOWED_HEADERS
        }
    
    def get_rate_limit_config(self) -> Dict[str, int]:
        """Get rate limiting configuration."""
        return {
            "per_minute": self.settings.API_RATE_LIMIT_PER_MINUTE,
            "per_hour": self.settings.API_RATE_LIMIT_PER_HOUR
        }
    
    def get_audit_config(self) -> Dict[str, Any]:
        """Get audit configuration."""
        return {
            "retention_days": self.settings.AUDIT_LOG_RETENTION_DAYS,
            "log_level": self.settings.SECURITY_LOG_LEVEL,
            "log_sensitive_data": self.settings.LOG_SENSITIVE_DATA,
            "enable_audit_trail": self.settings.ENABLE_AUDIT_TRAIL
        }
    
    def get_data_protection_config(self) -> Dict[str, Any]:
        """Get data protection configuration."""
        return {
            "retention_days": self.settings.DATA_RETENTION_DAYS,
            "gdpr_compliance": self.settings.GDPR_COMPLIANCE,
            "ccpa_compliance": self.settings.CCPA_COMPLIANCE,
            "auto_delete_expired": self.settings.AUTO_DELETE_EXPIRED_DATA,
            "anonymize_deleted": self.settings.ANONYMIZE_DELETED_DATA
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    def generate_new_keys(self) -> Dict[str, str]:
        """Generate new encryption keys."""
        return {
            "secret_key": secrets.token_urlsafe(32),
            "encryption_key": Fernet.generate_key().decode(),
            "database_encryption_key": Fernet.generate_key().decode(),
            "backup_encryption_key": Fernet.generate_key().decode(),
            "webhook_secret_key": secrets.token_urlsafe(32)
        }
    
    def export_config_template(self) -> str:
        """Export environment configuration template."""
        template = """# Real Estate Empire Security Configuration

# JWT Settings
SECRET_KEY=your_secret_key_here_minimum_32_characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Encryption Settings
ENCRYPTION_KEY=your_fernet_encryption_key_here
DATABASE_ENCRYPTION_KEY=your_database_encryption_key_here

# Password Policy
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL_CHARS=true
PASSWORD_EXPIRY_DAYS=90

# Account Security
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15
SESSION_TIMEOUT_MINUTES=60
REQUIRE_MFA=false

# API Security
API_RATE_LIMIT_PER_MINUTE=100
API_RATE_LIMIT_PER_HOUR=1000
API_KEY_EXPIRY_DAYS=365

# HTTPS and TLS
FORCE_HTTPS=true
TLS_VERSION=1.2
HSTS_MAX_AGE=31536000

# CORS Settings
CORS_ALLOWED_ORIGINS=https://localhost:3000,https://yourdomain.com
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOWED_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOWED_HEADERS=*

# Security Headers
CONTENT_SECURITY_POLICY=default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'
X_FRAME_OPTIONS=DENY
X_CONTENT_TYPE_OPTIONS=nosniff
X_XSS_PROTECTION=1; mode=block
REFERRER_POLICY=strict-origin-when-cross-origin

# Data Protection
DATA_RETENTION_DAYS=2555
GDPR_COMPLIANCE=true
CCPA_COMPLIANCE=true
AUTO_DELETE_EXPIRED_DATA=true
ANONYMIZE_DELETED_DATA=true

# Audit and Logging
AUDIT_LOG_RETENTION_DAYS=2555
SECURITY_LOG_LEVEL=INFO
LOG_SENSITIVE_DATA=false
ENABLE_AUDIT_TRAIL=true

# External Service Security
WEBHOOK_SECRET_KEY=your_webhook_secret_key_here
API_WEBHOOK_TIMEOUT=30
EXTERNAL_API_TIMEOUT=30

# Database Security
DATABASE_SSL_MODE=require
DATABASE_SSL_CERT=
DATABASE_SSL_KEY=
DATABASE_SSL_CA=

# Backup and Recovery
BACKUP_ENCRYPTION_KEY=your_backup_encryption_key_here
BACKUP_RETENTION_DAYS=90
ENABLE_POINT_IN_TIME_RECOVERY=true

# Monitoring and Alerting
SECURITY_ALERT_EMAIL=security@yourdomain.com
SECURITY_ALERT_WEBHOOK=https://yourdomain.com/security-alerts
FAILED_LOGIN_ALERT_THRESHOLD=10
SUSPICIOUS_ACTIVITY_ALERT=true

# Environment
ENVIRONMENT=production
"""
        return template

# Global security configuration instance
security_config_manager = SecurityConfigManager()

def get_security_config() -> SecurityConfigManager:
    """Get global security configuration manager."""
    return security_config_manager

def validate_environment_security():
    """Validate environment security configuration."""
    config = get_security_config()
    
    # Check for default/weak values in production
    if config.is_production():
        warnings = []
        
        if config.settings.SECRET_KEY == "your_secret_key_here":
            warnings.append("SECRET_KEY is using default value")
        
        if not config.settings.FORCE_HTTPS:
            warnings.append("HTTPS is not enforced in production")
        
        if not config.settings.REQUIRE_MFA:
            warnings.append("MFA is not required in production")
        
        if config.settings.SESSION_TIMEOUT_MINUTES > 120:
            warnings.append("Session timeout is longer than recommended for production")
        
        if warnings:
            print("Security warnings:", "; ".join(warnings))
    
    return True

# Initialize and validate configuration on import
validate_environment_security()