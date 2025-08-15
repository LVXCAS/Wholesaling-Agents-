"""
Security and authentication module for Real Estate Empire platform.
Provides comprehensive security controls including authentication, authorization,
encryption, and security monitoring.
"""

import os
import jwt
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())

# Security logger
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.INFO)

class SecurityConfig:
    """Security configuration settings."""
    
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = REFRESH_TOKEN_EXPIRE_DAYS
        self.encryption_key = ENCRYPTION_KEY
        self.password_min_length = 8
        self.max_login_attempts = 5
        self.lockout_duration_minutes = 15
        self.session_timeout_minutes = 60
        self.require_mfa = os.getenv("REQUIRE_MFA", "false").lower() == "true"

class UserRole:
    """User role definitions."""
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"
    INVESTOR = "investor"
    VIEWER = "viewer"

class Permission:
    """Permission definitions."""
    READ_PROPERTIES = "read:properties"
    WRITE_PROPERTIES = "write:properties"
    DELETE_PROPERTIES = "delete:properties"
    READ_LEADS = "read:leads"
    WRITE_LEADS = "write:leads"
    DELETE_LEADS = "delete:leads"
    READ_CONTRACTS = "read:contracts"
    WRITE_CONTRACTS = "write:contracts"
    DELETE_CONTRACTS = "delete:contracts"
    READ_PORTFOLIO = "read:portfolio"
    WRITE_PORTFOLIO = "write:portfolio"
    DELETE_PORTFOLIO = "delete:portfolio"
    READ_ANALYTICS = "read:analytics"
    WRITE_ANALYTICS = "write:analytics"
    ADMIN_USERS = "admin:users"
    ADMIN_SYSTEM = "admin:system"

# Role-Permission mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.READ_PROPERTIES, Permission.WRITE_PROPERTIES, Permission.DELETE_PROPERTIES,
        Permission.READ_LEADS, Permission.WRITE_LEADS, Permission.DELETE_LEADS,
        Permission.READ_CONTRACTS, Permission.WRITE_CONTRACTS, Permission.DELETE_CONTRACTS,
        Permission.READ_PORTFOLIO, Permission.WRITE_PORTFOLIO, Permission.DELETE_PORTFOLIO,
        Permission.READ_ANALYTICS, Permission.WRITE_ANALYTICS,
        Permission.ADMIN_USERS, Permission.ADMIN_SYSTEM
    ],
    UserRole.MANAGER: [
        Permission.READ_PROPERTIES, Permission.WRITE_PROPERTIES,
        Permission.READ_LEADS, Permission.WRITE_LEADS,
        Permission.READ_CONTRACTS, Permission.WRITE_CONTRACTS,
        Permission.READ_PORTFOLIO, Permission.WRITE_PORTFOLIO,
        Permission.READ_ANALYTICS, Permission.WRITE_ANALYTICS
    ],
    UserRole.AGENT: [
        Permission.READ_PROPERTIES, Permission.WRITE_PROPERTIES,
        Permission.READ_LEADS, Permission.WRITE_LEADS,
        Permission.READ_CONTRACTS, Permission.WRITE_CONTRACTS,
        Permission.READ_PORTFOLIO, Permission.READ_ANALYTICS
    ],
    UserRole.INVESTOR: [
        Permission.READ_PROPERTIES, Permission.READ_LEADS,
        Permission.READ_CONTRACTS, Permission.READ_PORTFOLIO,
        Permission.READ_ANALYTICS
    ],
    UserRole.VIEWER: [
        Permission.READ_PROPERTIES, Permission.READ_LEADS,
        Permission.READ_PORTFOLIO, Permission.READ_ANALYTICS
    ]
}

class TokenData(BaseModel):
    """Token data model."""
    user_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    permissions: Optional[List[str]] = None

class SecurityEvent(BaseModel):
    """Security event model for logging."""
    event_type: str
    user_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime
    details: Optional[Dict[str, Any]]
    risk_level: str = "low"

class PasswordManager:
    """Password hashing and validation."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength."""
        issues = []
        score = 0
        
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        else:
            score += 1
            
        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        else:
            score += 1
            
        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        else:
            score += 1
            
        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one number")
        else:
            score += 1
            
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("Password must contain at least one special character")
        else:
            score += 1
            
        strength = "weak"
        if score >= 4:
            strength = "strong"
        elif score >= 3:
            strength = "medium"
            
        return {
            "valid": len(issues) == 0,
            "strength": strength,
            "score": score,
            "issues": issues
        }

class DataEncryption:
    """Data encryption and decryption utilities."""
    
    def __init__(self, key: Optional[str] = None):
        if key:
            self.key = key.encode() if isinstance(key, str) else key
        else:
            self.key = ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        if not data:
            return data
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        if not encrypted_data:
            return encrypted_data
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_dict(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Encrypt specific fields in a dictionary."""
        encrypted_data = data.copy()
        for field in fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))
        return encrypted_data
    
    def decrypt_dict(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Decrypt specific fields in a dictionary."""
        decrypted_data = data.copy()
        for field in fields:
            if field in decrypted_data and decrypted_data[field]:
                decrypted_data[field] = self.decrypt(decrypted_data[field])
        return decrypted_data

class JWTManager:
    """JWT token management."""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(to_encode, self.config.secret_key, algorithm=self.config.algorithm)
        
        # Log token creation
        security_logger.info(f"Access token created for user: {data.get('sub')}")
        
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.config.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(to_encode, self.config.secret_key, algorithm=self.config.algorithm)
        
        # Log token creation
        security_logger.info(f"Refresh token created for user: {data.get('sub')}")
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.config.secret_key, algorithms=[self.config.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            security_logger.warning("Token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            security_logger.warning("Invalid token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

class SecurityMonitor:
    """Security event monitoring and logging."""
    
    def __init__(self):
        self.failed_attempts = {}  # Track failed login attempts
        self.locked_accounts = {}  # Track locked accounts
    
    def log_security_event(self, event: SecurityEvent):
        """Log security event."""
        security_logger.info(
            f"Security Event: {event.event_type} | "
            f"User: {event.user_id} | "
            f"IP: {event.ip_address} | "
            f"Risk: {event.risk_level} | "
            f"Details: {event.details}"
        )
    
    def track_failed_login(self, username: str, ip_address: str) -> bool:
        """Track failed login attempts and return if account should be locked."""
        key = f"{username}:{ip_address}"
        
        if key not in self.failed_attempts:
            self.failed_attempts[key] = {"count": 0, "last_attempt": datetime.utcnow()}
        
        self.failed_attempts[key]["count"] += 1
        self.failed_attempts[key]["last_attempt"] = datetime.utcnow()
        
        # Log failed attempt
        self.log_security_event(SecurityEvent(
            event_type="failed_login",
            user_id=username,
            ip_address=ip_address,
            user_agent=None,
            timestamp=datetime.utcnow(),
            details={"attempt_count": self.failed_attempts[key]["count"]},
            risk_level="medium"
        ))
        
        # Check if account should be locked
        if self.failed_attempts[key]["count"] >= 5:
            self.lock_account(username, ip_address)
            return True
        
        return False
    
    def lock_account(self, username: str, ip_address: str):
        """Lock account due to too many failed attempts."""
        key = f"{username}:{ip_address}"
        self.locked_accounts[key] = datetime.utcnow() + timedelta(minutes=15)
        
        self.log_security_event(SecurityEvent(
            event_type="account_locked",
            user_id=username,
            ip_address=ip_address,
            user_agent=None,
            timestamp=datetime.utcnow(),
            details={"reason": "too_many_failed_attempts"},
            risk_level="high"
        ))
    
    def is_account_locked(self, username: str, ip_address: str) -> bool:
        """Check if account is locked."""
        key = f"{username}:{ip_address}"
        
        if key in self.locked_accounts:
            if datetime.utcnow() < self.locked_accounts[key]:
                return True
            else:
                # Unlock account
                del self.locked_accounts[key]
                if key in self.failed_attempts:
                    del self.failed_attempts[key]
        
        return False
    
    def reset_failed_attempts(self, username: str, ip_address: str):
        """Reset failed login attempts after successful login."""
        key = f"{username}:{ip_address}"
        if key in self.failed_attempts:
            del self.failed_attempts[key]

# Global instances
security_config = SecurityConfig()
jwt_manager = JWTManager(security_config)
password_manager = PasswordManager()
data_encryption = DataEncryption()
security_monitor = SecurityMonitor()
security_bearer = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)) -> TokenData:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    payload = jwt_manager.verify_token(token)
    
    user_id = payload.get("sub")
    username = payload.get("username")
    role = payload.get("role")
    permissions = payload.get("permissions", [])
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return TokenData(
        user_id=user_id,
        username=username,
        role=role,
        permissions=permissions
    )

def require_permission(permission: str):
    """Decorator to require specific permission."""
    def permission_checker(current_user: TokenData = Depends(get_current_user)):
        if permission not in (current_user.permissions or []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )
        return current_user
    return permission_checker

def require_role(role: str):
    """Decorator to require specific role."""
    def role_checker(current_user: TokenData = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role}"
            )
        return current_user
    return role_checker

def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def validate_request_signature(request: Request, secret: str) -> bool:
    """Validate webhook request signature."""
    signature = request.headers.get("X-Signature-256")
    if not signature:
        return False
    
    # Implementation would depend on the specific signature scheme
    # This is a placeholder for webhook signature validation
    return True

class SecurityMiddleware:
    """Security middleware for request processing."""
    
    def __init__(self):
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
    
    def add_security_headers(self, response):
        """Add security headers to response."""
        for header, value in self.security_headers.items():
            response.headers[header] = value
        return response

# Initialize security middleware
security_middleware = SecurityMiddleware()