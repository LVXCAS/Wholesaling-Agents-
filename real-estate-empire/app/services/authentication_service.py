"""
Authentication and authorization service.
Handles user authentication, session management, and security controls.
"""

import uuid
import secrets
import hashlib
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from app.core.database import get_db
from app.core.security import (
    security_config, jwt_manager, password_manager, data_encryption,
    security_monitor, SecurityEvent, UserRole, ROLE_PERMISSIONS
)
from app.models.user import (
    UserDB, SessionDB, APIKeyDB, UserCreate, UserUpdate, UserLogin,
    TokenResponse, UserResponse, PasswordChange, PasswordReset,
    PasswordResetConfirm, MFASetup, MFAVerify, APIKeyCreate,
    APIKeyResponse, SessionInfo, ComplianceReport
)
from app.models.audit_compliance import AuditLogDB, AuditLogCreate

class AuthenticationService:
    """Authentication and authorization service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.encryption = data_encryption
    
    def create_user(self, user_data: UserCreate, created_by: Optional[str] = None) -> UserResponse:
        """Create a new user account."""
        
        # Check if user already exists
        existing_user = self.db.query(UserDB).filter(
            or_(UserDB.username == user_data.username, UserDB.email == user_data.email)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this username or email already exists"
            )
        
        # Validate password strength
        password_validation = password_manager.validate_password_strength(user_data.password)
        if not password_validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password validation failed: {', '.join(password_validation['issues'])}"
            )
        
        # Create user
        user_id = str(uuid.uuid4())
        hashed_password = password_manager.hash_password(user_data.password)
        
        # Get role permissions
        permissions = ROLE_PERMISSIONS.get(user_data.role, ROLE_PERMISSIONS[UserRole.VIEWER])
        
        db_user = UserDB(
            id=user_id,
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=user_data.role,
            permissions=permissions,
            phone=self.encryption.encrypt(user_data.phone) if user_data.phone else None,
            company=user_data.company,
            timezone=user_data.timezone,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        # Log user creation
        self._log_audit_event(
            event_type="user_created",
            user_id=created_by,
            target_user_id=user_id,
            details={"username": user_data.username, "role": user_data.role}
        )
        
        return self._user_to_response(db_user)
    
    def authenticate_user(self, login_data: UserLogin, ip_address: str, user_agent: str) -> TokenResponse:
        """Authenticate user and create session."""
        
        # Check if account is locked
        if security_monitor.is_account_locked(login_data.username, ip_address):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to too many failed attempts"
            )
        
        # Get user
        user = self.db.query(UserDB).filter(UserDB.username == login_data.username).first()
        
        if not user or not password_manager.verify_password(login_data.password, user.hashed_password):
            # Track failed attempt
            security_monitor.track_failed_login(login_data.username, ip_address)
            
            self._log_audit_event(
                event_type="login_failed",
                user_id=login_data.username,
                details={"ip_address": ip_address, "reason": "invalid_credentials"},
                security_relevant=True,
                risk_level="medium"
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )
        
        # Check if user is locked
        if user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is locked"
            )
        
        # Check MFA if enabled
        if user.mfa_enabled and not login_data.mfa_code:
            raise HTTPException(
                status_code=status.HTTP_200_OK,  # Special status for MFA required
                detail="MFA code required",
                headers={"X-MFA-Required": "true"}
            )
        
        if user.mfa_enabled and login_data.mfa_code:
            if not self._verify_mfa_code(user, login_data.mfa_code):
                self._log_audit_event(
                    event_type="mfa_failed",
                    user_id=user.id,
                    details={"ip_address": ip_address},
                    security_relevant=True,
                    risk_level="high"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid MFA code"
                )
        
        # Reset failed attempts on successful login
        security_monitor.reset_failed_attempts(login_data.username, ip_address)
        
        # Update user login info
        user.last_login = datetime.utcnow()
        user.last_activity = datetime.utcnow()
        user.failed_login_attempts = 0
        
        # Create session
        session = self._create_session(user, ip_address, user_agent, login_data.remember_me)
        
        # Create tokens
        token_data = {
            "sub": user.id,
            "username": user.username,
            "role": user.role,
            "permissions": user.permissions or []
        }
        
        access_token = jwt_manager.create_access_token(token_data)
        refresh_token = jwt_manager.create_refresh_token(token_data)
        
        # Update session with token hashes
        session.token_hash = hashlib.sha256(access_token.encode()).hexdigest()
        session.refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        
        self.db.commit()
        
        # Log successful login
        self._log_audit_event(
            event_type="login_success",
            user_id=user.id,
            details={"ip_address": ip_address, "session_id": session.id},
            security_relevant=True
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=security_config.access_token_expire_minutes * 60,
            user=self._user_to_response(user)
        )
    
    def refresh_token(self, refresh_token: str, ip_address: str) -> TokenResponse:
        """Refresh access token using refresh token."""
        
        # Verify refresh token
        payload = jwt_manager.verify_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        user = self.db.query(UserDB).filter(UserDB.id == user_id).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Verify session exists and is active
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        session = self.db.query(SessionDB).filter(
            and_(
                SessionDB.user_id == user_id,
                SessionDB.refresh_token_hash == token_hash,
                SessionDB.is_active == True,
                SessionDB.expires_at > datetime.utcnow()
            )
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Create new tokens
        token_data = {
            "sub": user.id,
            "username": user.username,
            "role": user.role,
            "permissions": user.permissions or []
        }
        
        new_access_token = jwt_manager.create_access_token(token_data)
        new_refresh_token = jwt_manager.create_refresh_token(token_data)
        
        # Update session
        session.token_hash = hashlib.sha256(new_access_token.encode()).hexdigest()
        session.refresh_token_hash = hashlib.sha256(new_refresh_token.encode()).hexdigest()
        session.last_activity = datetime.utcnow()
        
        # Update user activity
        user.last_activity = datetime.utcnow()
        
        self.db.commit()
        
        # Log token refresh
        self._log_audit_event(
            event_type="token_refreshed",
            user_id=user.id,
            details={"ip_address": ip_address, "session_id": session.id}
        )
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=security_config.access_token_expire_minutes * 60,
            user=self._user_to_response(user)
        )
    
    def logout(self, user_id: str, session_id: Optional[str] = None):
        """Logout user and revoke session."""
        
        if session_id:
            # Revoke specific session
            session = self.db.query(SessionDB).filter(
                and_(SessionDB.id == session_id, SessionDB.user_id == user_id)
            ).first()
            if session:
                session.is_active = False
                session.revoked_at = datetime.utcnow()
                session.revoked_reason = "user_logout"
        else:
            # Revoke all user sessions
            self.db.query(SessionDB).filter(SessionDB.user_id == user_id).update({
                "is_active": False,
                "revoked_at": datetime.utcnow(),
                "revoked_reason": "user_logout"
            })
        
        self.db.commit()
        
        # Log logout
        self._log_audit_event(
            event_type="logout",
            user_id=user_id,
            details={"session_id": session_id}
        )
    
    def setup_mfa(self, user_id: str) -> MFASetup:
        """Setup MFA for user."""
        
        user = self.db.query(UserDB).filter(UserDB.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate MFA secret
        secret = pyotp.random_base32()
        
        # Generate QR code
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name="Real Estate Empire"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_code = base64.b64encode(qr_buffer.getvalue()).decode()
        
        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        
        # Store encrypted secret and backup codes
        user.mfa_secret = self.encryption.encrypt(secret)
        user.backup_codes = [self.encryption.encrypt(code) for code in backup_codes]
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        # Log MFA setup
        self._log_audit_event(
            event_type="mfa_setup",
            user_id=user_id,
            details={},
            security_relevant=True
        )
        
        return MFASetup(
            secret=secret,
            qr_code=qr_code,
            backup_codes=backup_codes
        )
    
    def enable_mfa(self, user_id: str, verification: MFAVerify) -> bool:
        """Enable MFA after verification."""
        
        user = self.db.query(UserDB).filter(UserDB.id == user_id).first()
        if not user or not user.mfa_secret:
            raise HTTPException(status_code=404, detail="MFA not set up")
        
        # Verify code
        if not self._verify_mfa_code(user, verification.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid MFA code"
            )
        
        # Enable MFA
        user.mfa_enabled = True
        user.updated_at = datetime.utcnow()
        self.db.commit()
        
        # Log MFA enabled
        self._log_audit_event(
            event_type="mfa_enabled",
            user_id=user_id,
            details={},
            security_relevant=True
        )
        
        return True
    
    def disable_mfa(self, user_id: str) -> bool:
        """Disable MFA for user."""
        
        user = self.db.query(UserDB).filter(UserDB.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.mfa_enabled = False
        user.mfa_secret = None
        user.backup_codes = None
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        # Log MFA disabled
        self._log_audit_event(
            event_type="mfa_disabled",
            user_id=user_id,
            details={},
            security_relevant=True
        )
        
        return True
    
    def create_api_key(self, user_id: str, key_data: APIKeyCreate) -> APIKeyResponse:
        """Create API key for user."""
        
        user = self.db.query(UserDB).filter(UserDB.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate API key
        api_key = f"re_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Set expiration
        expires_at = None
        if key_data.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)
        
        # Create API key record
        db_key = APIKeyDB(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=key_data.name,
            key_hash=key_hash,
            permissions=key_data.permissions,
            scopes=key_data.scopes,
            rate_limit=key_data.rate_limit,
            expires_at=expires_at,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(db_key)
        self.db.commit()
        self.db.refresh(db_key)
        
        # Log API key creation
        self._log_audit_event(
            event_type="api_key_created",
            user_id=user_id,
            details={"key_name": key_data.name, "key_id": db_key.id}
        )
        
        response = APIKeyResponse(
            id=db_key.id,
            name=db_key.name,
            key=api_key,  # Only returned on creation
            permissions=db_key.permissions,
            scopes=db_key.scopes,
            is_active=db_key.is_active,
            expires_at=db_key.expires_at,
            created_at=db_key.created_at,
            last_used=db_key.last_used,
            usage_count=db_key.usage_count
        )
        
        return response
    
    def get_user_sessions(self, user_id: str) -> List[SessionInfo]:
        """Get active sessions for user."""
        
        sessions = self.db.query(SessionDB).filter(
            and_(
                SessionDB.user_id == user_id,
                SessionDB.is_active == True,
                SessionDB.expires_at > datetime.utcnow()
            )
        ).all()
        
        return [
            SessionInfo(
                id=session.id,
                ip_address=session.ip_address,
                user_agent=session.user_agent,
                device_info=session.device_info,
                created_at=session.created_at,
                last_activity=session.last_activity,
                is_active=session.is_active
            )
            for session in sessions
        ]
    
    def revoke_session(self, user_id: str, session_id: str) -> bool:
        """Revoke specific user session."""
        
        session = self.db.query(SessionDB).filter(
            and_(SessionDB.id == session_id, SessionDB.user_id == user_id)
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.is_active = False
        session.revoked_at = datetime.utcnow()
        session.revoked_reason = "user_revoked"
        
        self.db.commit()
        
        # Log session revocation
        self._log_audit_event(
            event_type="session_revoked",
            user_id=user_id,
            details={"session_id": session_id}
        )
        
        return True
    
    def generate_compliance_report(self, start_date: datetime, end_date: datetime) -> ComplianceReport:
        """Generate compliance report for specified period."""
        
        # Get user statistics
        total_users = self.db.query(UserDB).count()
        active_users = self.db.query(UserDB).filter(UserDB.is_active == True).count()
        locked_users = self.db.query(UserDB).filter(UserDB.is_locked == True).count()
        mfa_enabled_users = self.db.query(UserDB).filter(UserDB.mfa_enabled == True).count()
        
        # Get security events from audit log
        security_events = self.db.query(AuditLogDB).filter(
            and_(
                AuditLogDB.security_relevant == True,
                AuditLogDB.timestamp >= start_date,
                AuditLogDB.timestamp <= end_date
            )
        ).all()
        
        # Count specific event types
        failed_logins = len([e for e in security_events if e.event_type == "login_failed"])
        successful_logins = len([e for e in security_events if e.event_type == "login_success"])
        password_changes = len([e for e in security_events if e.event_type == "password_changed"])
        
        # API key usage
        api_key_usage = self.db.query(APIKeyDB).filter(
            and_(
                APIKeyDB.last_used >= start_date,
                APIKeyDB.last_used <= end_date
            )
        ).count()
        
        # Determine compliance status
        compliance_status = "compliant"
        recommendations = []
        
        if mfa_enabled_users / total_users < 0.8:
            compliance_status = "needs_attention"
            recommendations.append("Increase MFA adoption rate")
        
        if failed_logins > successful_logins * 0.1:
            compliance_status = "needs_attention"
            recommendations.append("High failed login rate detected")
        
        return ComplianceReport(
            report_id=str(uuid.uuid4()),
            report_type="security_compliance",
            period_start=start_date,
            period_end=end_date,
            generated_at=datetime.utcnow(),
            total_users=total_users,
            active_users=active_users,
            locked_users=locked_users,
            failed_login_attempts=failed_logins,
            successful_logins=successful_logins,
            password_changes=password_changes,
            mfa_enabled_users=mfa_enabled_users,
            api_key_usage=api_key_usage,
            security_events=[{
                "event_type": e.event_type,
                "timestamp": e.timestamp.isoformat(),
                "user_id": e.user_id,
                "risk_level": e.risk_level
            } for e in security_events],
            compliance_status=compliance_status,
            recommendations=recommendations
        )
    
    def _create_session(self, user: UserDB, ip_address: str, user_agent: str, remember_me: bool) -> SessionDB:
        """Create user session."""
        
        # Set session expiration
        if remember_me:
            expires_at = datetime.utcnow() + timedelta(days=30)
        else:
            expires_at = datetime.utcnow() + timedelta(minutes=security_config.session_timeout_minutes)
        
        session = SessionDB(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash="",  # Will be set after token creation
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        self.db.add(session)
        return session
    
    def _verify_mfa_code(self, user: UserDB, code: str) -> bool:
        """Verify MFA code."""
        
        if not user.mfa_secret:
            return False
        
        # Decrypt secret
        secret = self.encryption.decrypt(user.mfa_secret)
        
        # Verify TOTP code
        totp = pyotp.TOTP(secret)
        if totp.verify(code, valid_window=1):
            return True
        
        # Check backup codes
        if user.backup_codes:
            encrypted_code = self.encryption.encrypt(code.upper())
            if encrypted_code in user.backup_codes:
                # Remove used backup code
                user.backup_codes.remove(encrypted_code)
                user.updated_at = datetime.utcnow()
                return True
        
        return False
    
    def _user_to_response(self, user: UserDB) -> UserResponse:
        """Convert database user to response model."""
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            phone=self.encryption.decrypt(user.phone) if user.phone else None,
            company=user.company,
            timezone=user.timezone,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_locked=user.is_locked,
            mfa_enabled=user.mfa_enabled,
            created_at=user.created_at,
            last_login=user.last_login,
            last_activity=user.last_activity,
            permissions=user.permissions
        )
    
    def _log_audit_event(self, event_type: str, user_id: Optional[str] = None, 
                        target_user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None,
                        security_relevant: bool = False, compliance_relevant: bool = False,
                        risk_level: str = "low"):
        """Log audit event."""
        
        audit_log = AuditLogCreate(
            event_type=event_type,
            event_category="security",
            event_description=f"Security event: {event_type}",
            user_id=user_id,
            target_resource_type="user",
            target_resource_id=target_user_id,
            additional_metadata=details,
            security_relevant=security_relevant,
            compliance_relevant=compliance_relevant,
            risk_level=risk_level
        )
        
        # This would typically call the audit service
        # For now, we'll create the record directly
        db_audit = AuditLogDB(
            id=str(uuid.uuid4()),
            event_type=audit_log.event_type,
            event_category=audit_log.event_category,
            event_description=audit_log.event_description,
            user_id=audit_log.user_id,
            target_resource_type=audit_log.target_resource_type,
            target_resource_id=audit_log.target_resource_id,
            additional_metadata=audit_log.additional_metadata,
            security_relevant=audit_log.security_relevant,
            compliance_relevant=audit_log.compliance_relevant,
            risk_level=audit_log.risk_level,
            timestamp=datetime.utcnow()
        )
        
        self.db.add(db_audit)