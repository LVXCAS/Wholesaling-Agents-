"""
Comprehensive tests for security and compliance implementation.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.security import (
    PasswordManager, DataEncryption, JWTManager, SecurityMonitor,
    SecurityConfig, SecurityEvent, UserRole, Permission
)
from app.services.authentication_service import AuthenticationService
from app.models.user import (
    UserDB, SessionDB, APIKeyDB, UserCreate, UserLogin, MFAVerify
)

class TestPasswordManager:
    """Test password management functionality."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123!"
        hashed = PasswordManager.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert PasswordManager.verify_password(password, hashed)
    
    def test_verify_password(self):
        """Test password verification."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = PasswordManager.hash_password(password)
        
        assert PasswordManager.verify_password(password, hashed)
        assert not PasswordManager.verify_password(wrong_password, hashed)
    
    def test_validate_password_strength(self):
        """Test password strength validation."""
        # Strong password
        strong_password = "StrongPass123!"
        result = PasswordManager.validate_password_strength(strong_password)
        assert result["valid"]
        assert result["strength"] == "strong"
        assert result["score"] == 5
        
        # Weak password
        weak_password = "weak"
        result = PasswordManager.validate_password_strength(weak_password)
        assert not result["valid"]
        assert result["strength"] == "weak"
        assert len(result["issues"]) > 0

class TestDataEncryption:
    """Test data encryption functionality."""
    
    def test_encrypt_decrypt(self):
        """Test data encryption and decryption."""
        encryption = DataEncryption()
        original_data = "sensitive information"
        
        encrypted = encryption.encrypt(original_data)
        assert encrypted != original_data
        
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == original_data
    
    def test_encrypt_decrypt_dict(self):
        """Test dictionary field encryption."""
        encryption = DataEncryption()
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
            "address": "123 Main St"
        }
        fields_to_encrypt = ["phone", "address"]
        
        encrypted_data = encryption.encrypt_dict(data, fields_to_encrypt)
        assert encrypted_data["name"] == data["name"]  # Not encrypted
        assert encrypted_data["email"] == data["email"]  # Not encrypted
        assert encrypted_data["phone"] != data["phone"]  # Encrypted
        assert encrypted_data["address"] != data["address"]  # Encrypted
        
        decrypted_data = encryption.decrypt_dict(encrypted_data, fields_to_encrypt)
        assert decrypted_data == data
    
    def test_empty_data_handling(self):
        """Test handling of empty/None data."""
        encryption = DataEncryption()
        
        assert encryption.encrypt("") == ""
        assert encryption.encrypt(None) is None
        assert encryption.decrypt("") == ""
        assert encryption.decrypt(None) is None

class TestJWTManager:
    """Test JWT token management."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        config = SecurityConfig()
        jwt_manager = JWTManager(config)
        
        data = {"sub": "user123", "username": "testuser"}
        token = jwt_manager.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token
        payload = jwt_manager.verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        config = SecurityConfig()
        jwt_manager = JWTManager(config)
        
        data = {"sub": "user123", "username": "testuser"}
        token = jwt_manager.create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token
        payload = jwt_manager.verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["type"] == "refresh"
    
    def test_verify_expired_token(self):
        """Test expired token verification."""
        config = SecurityConfig()
        config.access_token_expire_minutes = -1  # Expired
        jwt_manager = JWTManager(config)
        
        data = {"sub": "user123"}
        token = jwt_manager.create_access_token(data)
        
        with pytest.raises(Exception):  # Should raise HTTPException
            jwt_manager.verify_token(token)

class TestSecurityMonitor:
    """Test security monitoring functionality."""
    
    def test_track_failed_login(self):
        """Test failed login tracking."""
        monitor = SecurityMonitor()
        username = "testuser"
        ip_address = "192.168.1.1"
        
        # Track multiple failed attempts
        for i in range(4):
            locked = monitor.track_failed_login(username, ip_address)
            assert not locked  # Should not be locked yet
        
        # Fifth attempt should trigger lock
        locked = monitor.track_failed_login(username, ip_address)
        assert locked
        
        # Check if account is locked
        assert monitor.is_account_locked(username, ip_address)
    
    def test_reset_failed_attempts(self):
        """Test resetting failed login attempts."""
        monitor = SecurityMonitor()
        username = "testuser"
        ip_address = "192.168.1.1"
        
        # Track failed attempts
        monitor.track_failed_login(username, ip_address)
        monitor.track_failed_login(username, ip_address)
        
        # Reset attempts
        monitor.reset_failed_attempts(username, ip_address)
        
        # Should not be locked after reset
        assert not monitor.is_account_locked(username, ip_address)
    
    def test_account_unlock_after_timeout(self):
        """Test automatic account unlock after timeout."""
        monitor = SecurityMonitor()
        username = "testuser"
        ip_address = "192.168.1.1"
        
        # Lock account
        for i in range(5):
            monitor.track_failed_login(username, ip_address)
        
        assert monitor.is_account_locked(username, ip_address)
        
        # Simulate timeout by modifying lock time
        key = f"{username}:{ip_address}"
        monitor.locked_accounts[key] = datetime.utcnow() - timedelta(minutes=20)
        
        # Should be unlocked now
        assert not monitor.is_account_locked(username, ip_address)

@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock(spec=Session)

@pytest.fixture
def auth_service(mock_db):
    """Authentication service with mock database."""
    return AuthenticationService(mock_db)

class TestAuthenticationService:
    """Test authentication service functionality."""
    
    def test_create_user(self, auth_service, mock_db):
        """Test user creation."""
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="StrongPass123!",
            full_name="Test User",
            role=UserRole.AGENT
        )
        
        # Mock database query to return None (user doesn't exist)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Create user
        user = auth_service.create_user(user_data)
        
        # Verify user creation
        assert user.username == user_data.username
        assert user.email == user_data.email
        assert user.role == user_data.role
        assert mock_db.add.called
        assert mock_db.commit.called
    
    def test_create_duplicate_user(self, auth_service, mock_db):
        """Test creating duplicate user."""
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="StrongPass123!"
        )
        
        # Mock existing user
        existing_user = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing_user
        
        # Should raise exception for duplicate user
        with pytest.raises(Exception):
            auth_service.create_user(user_data)
    
    def test_authenticate_user_success(self, auth_service, mock_db):
        """Test successful user authentication."""
        login_data = UserLogin(username="testuser", password="StrongPass123!")
        
        # Mock user
        mock_user = Mock()
        mock_user.id = "user123"
        mock_user.username = "testuser"
        mock_user.hashed_password = PasswordManager.hash_password("StrongPass123!")
        mock_user.is_active = True
        mock_user.is_locked = False
        mock_user.mfa_enabled = False
        mock_user.role = UserRole.AGENT
        mock_user.permissions = ["read:properties"]
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        # Mock security monitor
        with patch('app.services.authentication_service.security_monitor') as mock_monitor:
            mock_monitor.is_account_locked.return_value = False
            mock_monitor.reset_failed_attempts = Mock()
            
            # Authenticate user
            token_response = auth_service.authenticate_user(
                login_data, "192.168.1.1", "test-agent"
            )
            
            # Verify response
            assert token_response.access_token
            assert token_response.refresh_token
            assert token_response.user.username == "testuser"
    
    def test_authenticate_user_invalid_password(self, auth_service, mock_db):
        """Test authentication with invalid password."""
        login_data = UserLogin(username="testuser", password="WrongPassword")
        
        # Mock user with different password
        mock_user = Mock()
        mock_user.hashed_password = PasswordManager.hash_password("CorrectPassword123!")
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Mock security monitor
        with patch('app.services.authentication_service.security_monitor') as mock_monitor:
            mock_monitor.is_account_locked.return_value = False
            mock_monitor.track_failed_login = Mock()
            
            # Should raise exception for invalid password
            with pytest.raises(Exception):
                auth_service.authenticate_user(login_data, "192.168.1.1", "test-agent")
            
            # Verify failed attempt was tracked
            mock_monitor.track_failed_login.assert_called_once()
    
    def test_authenticate_locked_user(self, auth_service, mock_db):
        """Test authentication of locked user."""
        login_data = UserLogin(username="testuser", password="StrongPass123!")
        
        # Mock security monitor to return locked account
        with patch('app.services.authentication_service.security_monitor') as mock_monitor:
            mock_monitor.is_account_locked.return_value = True
            
            # Should raise exception for locked account
            with pytest.raises(Exception):
                auth_service.authenticate_user(login_data, "192.168.1.1", "test-agent")
    
    def test_setup_mfa(self, auth_service, mock_db):
        """Test MFA setup."""
        user_id = "user123"
        
        # Mock user
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.email = "test@example.com"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.commit = Mock()
        
        # Setup MFA
        mfa_setup = auth_service.setup_mfa(user_id)
        
        # Verify MFA setup
        assert mfa_setup.secret
        assert mfa_setup.qr_code
        assert len(mfa_setup.backup_codes) == 10
        assert mock_db.commit.called
    
    def test_enable_mfa(self, auth_service, mock_db):
        """Test MFA enabling."""
        user_id = "user123"
        
        # Mock user with MFA secret
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.mfa_secret = auth_service.encryption.encrypt("TESTSECRET123456")
        mock_user.mfa_enabled = False
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.commit = Mock()
        
        # Mock MFA verification
        with patch.object(auth_service, '_verify_mfa_code', return_value=True):
            verification = MFAVerify(code="123456")
            result = auth_service.enable_mfa(user_id, verification)
            
            assert result is True
            assert mock_user.mfa_enabled is True
            assert mock_db.commit.called
    
    def test_create_api_key(self, auth_service, mock_db):
        """Test API key creation."""
        user_id = "user123"
        
        # Mock user
        mock_user = Mock()
        mock_user.id = user_id
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Create API key
        from app.models.user import APIKeyCreate
        key_data = APIKeyCreate(
            name="Test API Key",
            permissions=["read:properties"],
            expires_in_days=30
        )
        
        api_key = auth_service.create_api_key(user_id, key_data)
        
        # Verify API key creation
        assert api_key.name == "Test API Key"
        assert api_key.key.startswith("re_")
        assert api_key.permissions == ["read:properties"]
        assert mock_db.add.called
        assert mock_db.commit.called

class TestSecurityIntegration:
    """Integration tests for security features."""
    
    def test_role_permissions(self):
        """Test role-based permissions."""
        from app.core.security import ROLE_PERMISSIONS
        
        # Admin should have all permissions
        admin_permissions = ROLE_PERMISSIONS[UserRole.ADMIN]
        assert Permission.ADMIN_USERS in admin_permissions
        assert Permission.ADMIN_SYSTEM in admin_permissions
        
        # Viewer should have limited permissions
        viewer_permissions = ROLE_PERMISSIONS[UserRole.VIEWER]
        assert Permission.READ_PROPERTIES in viewer_permissions
        assert Permission.ADMIN_USERS not in viewer_permissions
    
    def test_security_headers(self):
        """Test security headers middleware."""
        from app.core.security import SecurityMiddleware
        
        middleware = SecurityMiddleware()
        mock_response = Mock()
        mock_response.headers = {}
        
        response = middleware.add_security_headers(mock_response)
        
        # Verify security headers are added
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Strict-Transport-Security" in response.headers
        assert "Content-Security-Policy" in response.headers
    
    def test_encryption_key_generation(self):
        """Test encryption key generation and usage."""
        from cryptography.fernet import Fernet
        
        # Generate new key
        key = Fernet.generate_key()
        encryption = DataEncryption(key.decode())
        
        # Test encryption with new key
        data = "test data"
        encrypted = encryption.encrypt(data)
        decrypted = encryption.decrypt(encrypted)
        
        assert decrypted == data

class TestComplianceFeatures:
    """Test compliance and audit features."""
    
    def test_audit_logging(self, auth_service, mock_db):
        """Test audit event logging."""
        # Mock database operations
        mock_db.add = Mock()
        
        # Log audit event
        auth_service._log_audit_event(
            event_type="test_event",
            user_id="user123",
            details={"test": "data"},
            security_relevant=True,
            risk_level="medium"
        )
        
        # Verify audit log was created
        mock_db.add.assert_called_once()
        
        # Get the audit log object that was added
        audit_log = mock_db.add.call_args[0][0]
        assert audit_log.event_type == "test_event"
        assert audit_log.user_id == "user123"
        assert audit_log.security_relevant is True
        assert audit_log.risk_level == "medium"
    
    def test_compliance_report_generation(self, auth_service, mock_db):
        """Test compliance report generation."""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        # Mock database queries
        mock_db.query.return_value.count.return_value = 100
        mock_db.query.return_value.filter.return_value.count.return_value = 80
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Generate compliance report
        report = auth_service.generate_compliance_report(start_date, end_date)
        
        # Verify report structure
        assert report.report_type == "security_compliance"
        assert report.total_users == 100
        assert report.active_users == 80
        assert isinstance(report.security_events, list)
        assert report.compliance_status in ["compliant", "needs_attention"]

if __name__ == "__main__":
    pytest.main([__file__])