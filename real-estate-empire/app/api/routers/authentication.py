"""
Authentication API router.
Handles user authentication, registration, and security operations.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    get_current_user, require_permission, require_role, get_client_ip,
    security_middleware, TokenData, Permission, UserRole
)
from app.services.authentication_service import AuthenticationService
from app.models.user import (
    UserCreate, UserUpdate, UserLogin, TokenResponse, UserResponse,
    PasswordChange, PasswordReset, PasswordResetConfirm, MFASetup,
    MFAVerify, APIKeyCreate, APIKeyResponse, SessionInfo, ComplianceReport
)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_permission(Permission.ADMIN_USERS))
):
    """Register a new user account."""
    
    auth_service = AuthenticationService(db)
    
    try:
        user = auth_service.create_user(user_data, current_user.user_id)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Authenticate user and create session."""
    
    auth_service = AuthenticationService(db)
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    
    try:
        token_response = auth_service.authenticate_user(login_data, ip_address, user_agent)
        
        # Add security headers
        response = security_middleware.add_security_headers(response)
        
        return token_response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    
    auth_service = AuthenticationService(db)
    ip_address = get_client_ip(request)
    
    try:
        return auth_service.refresh_token(refresh_token, ip_address)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/logout")
async def logout(
    session_id: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user and revoke session."""
    
    auth_service = AuthenticationService(db)
    auth_service.logout(current_user.user_id, session_id)
    
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information."""
    
    auth_service = AuthenticationService(db)
    user = db.query(auth_service.UserDB).filter(
        auth_service.UserDB.id == current_user.user_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return auth_service._user_to_response(user)

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user information."""
    
    auth_service = AuthenticationService(db)
    user = db.query(auth_service.UserDB).filter(
        auth_service.UserDB.id == current_user.user_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user fields
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(user, field):
            if field == "phone" and value:
                setattr(user, field, auth_service.encryption.encrypt(value))
            else:
                setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return auth_service._user_to_response(user)

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    
    auth_service = AuthenticationService(db)
    user = db.query(auth_service.UserDB).filter(
        auth_service.UserDB.id == current_user.user_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not auth_service.password_manager.verify_password(
        password_data.current_password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    validation = auth_service.password_manager.validate_password_strength(
        password_data.new_password
    )
    if not validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password validation failed: {', '.join(validation['issues'])}"
        )
    
    # Update password
    user.hashed_password = auth_service.password_manager.hash_password(
        password_data.new_password
    )
    user.password_changed_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Log password change
    auth_service._log_audit_event(
        event_type="password_changed",
        user_id=current_user.user_id,
        details={},
        security_relevant=True
    )
    
    return {"message": "Password changed successfully"}

@router.post("/setup-mfa", response_model=MFASetup)
async def setup_mfa(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Setup MFA for current user."""
    
    auth_service = AuthenticationService(db)
    return auth_service.setup_mfa(current_user.user_id)

@router.post("/enable-mfa")
async def enable_mfa(
    verification: MFAVerify,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable MFA after verification."""
    
    auth_service = AuthenticationService(db)
    success = auth_service.enable_mfa(current_user.user_id, verification)
    
    if success:
        return {"message": "MFA enabled successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to enable MFA"
        )

@router.post("/disable-mfa")
async def disable_mfa(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable MFA for current user."""
    
    auth_service = AuthenticationService(db)
    success = auth_service.disable_mfa(current_user.user_id)
    
    if success:
        return {"message": "MFA disabled successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to disable MFA"
        )

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create API key for current user."""
    
    auth_service = AuthenticationService(db)
    return auth_service.create_api_key(current_user.user_id, key_data)

@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List API keys for current user."""
    
    keys = db.query(auth_service.APIKeyDB).filter(
        auth_service.APIKeyDB.user_id == current_user.user_id
    ).all()
    
    return [
        APIKeyResponse(
            id=key.id,
            name=key.name,
            key="***",  # Don't return actual key
            permissions=key.permissions,
            scopes=key.scopes,
            is_active=key.is_active,
            expires_at=key.expires_at,
            created_at=key.created_at,
            last_used=key.last_used,
            usage_count=key.usage_count
        )
        for key in keys
    ]

@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke API key."""
    
    key = db.query(auth_service.APIKeyDB).filter(
        auth_service.APIKeyDB.id == key_id,
        auth_service.APIKeyDB.user_id == current_user.user_id
    ).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    key.is_active = False
    key.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "API key revoked successfully"}

@router.get("/sessions", response_model=List[SessionInfo])
async def list_sessions(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List active sessions for current user."""
    
    auth_service = AuthenticationService(db)
    return auth_service.get_user_sessions(current_user.user_id)

@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke specific session."""
    
    auth_service = AuthenticationService(db)
    success = auth_service.revoke_session(current_user.user_id, session_id)
    
    if success:
        return {"message": "Session revoked successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to revoke session"
        )

# Admin endpoints

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: TokenData = Depends(require_permission(Permission.ADMIN_USERS)),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    
    auth_service = AuthenticationService(db)
    users = db.query(auth_service.UserDB).offset(skip).limit(limit).all()
    
    return [auth_service._user_to_response(user) for user in users]

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: TokenData = Depends(require_permission(Permission.ADMIN_USERS)),
    db: Session = Depends(get_db)
):
    """Get specific user (admin only)."""
    
    auth_service = AuthenticationService(db)
    user = db.query(auth_service.UserDB).filter(
        auth_service.UserDB.id == user_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return auth_service._user_to_response(user)

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: TokenData = Depends(require_permission(Permission.ADMIN_USERS)),
    db: Session = Depends(get_db)
):
    """Update user (admin only)."""
    
    auth_service = AuthenticationService(db)
    user = db.query(auth_service.UserDB).filter(
        auth_service.UserDB.id == user_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user fields
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(user, field):
            if field == "phone" and value:
                setattr(user, field, auth_service.encryption.encrypt(value))
            else:
                setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    # Log user update
    auth_service._log_audit_event(
        event_type="user_updated",
        user_id=current_user.user_id,
        target_user_id=user_id,
        details={"updated_fields": list(update_data.keys())},
        compliance_relevant=True
    )
    
    return auth_service._user_to_response(user)

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: TokenData = Depends(require_permission(Permission.ADMIN_USERS)),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)."""
    
    auth_service = AuthenticationService(db)
    user = db.query(auth_service.UserDB).filter(
        auth_service.UserDB.id == user_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Soft delete - deactivate user
    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.commit()
    
    # Revoke all sessions
    auth_service.logout(user_id)
    
    # Log user deletion
    auth_service._log_audit_event(
        event_type="user_deleted",
        user_id=current_user.user_id,
        target_user_id=user_id,
        details={},
        compliance_relevant=True,
        risk_level="medium"
    )
    
    return {"message": "User deleted successfully"}

@router.get("/compliance/report", response_model=ComplianceReport)
async def generate_compliance_report(
    start_date: datetime,
    end_date: datetime,
    current_user: TokenData = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Generate compliance report (admin only)."""
    
    auth_service = AuthenticationService(db)
    return auth_service.generate_compliance_report(start_date, end_date)

@router.post("/users/{user_id}/lock")
async def lock_user(
    user_id: str,
    current_user: TokenData = Depends(require_permission(Permission.ADMIN_USERS)),
    db: Session = Depends(get_db)
):
    """Lock user account (admin only)."""
    
    auth_service = AuthenticationService(db)
    user = db.query(auth_service.UserDB).filter(
        auth_service.UserDB.id == user_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_locked = True
    user.updated_at = datetime.utcnow()
    db.commit()
    
    # Revoke all sessions
    auth_service.logout(user_id)
    
    # Log user lock
    auth_service._log_audit_event(
        event_type="user_locked",
        user_id=current_user.user_id,
        target_user_id=user_id,
        details={},
        security_relevant=True,
        risk_level="medium"
    )
    
    return {"message": "User locked successfully"}

@router.post("/users/{user_id}/unlock")
async def unlock_user(
    user_id: str,
    current_user: TokenData = Depends(require_permission(Permission.ADMIN_USERS)),
    db: Session = Depends(get_db)
):
    """Unlock user account (admin only)."""
    
    auth_service = AuthenticationService(db)
    user = db.query(auth_service.UserDB).filter(
        auth_service.UserDB.id == user_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_locked = False
    user.failed_login_attempts = 0
    user.updated_at = datetime.utcnow()
    db.commit()
    
    # Log user unlock
    auth_service._log_audit_event(
        event_type="user_unlocked",
        user_id=current_user.user_id,
        target_user_id=user_id,
        details={},
        security_relevant=True
    )
    
    return {"message": "User unlocked successfully"}