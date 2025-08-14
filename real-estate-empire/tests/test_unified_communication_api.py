"""
Tests for unified communication API.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import uuid
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.routers.unified_communication import router, set_communication_service
from app.models.communication import (
    CommunicationChannel, MessageStatus, MessagePriority, ContactInfo,
    CommunicationPreferences, CommunicationHistory
)
from app.services.unified_communication_service import (
    CommunicationResponse, UnifiedCommunicationService
)


# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture
def sample_contact():
    """Sample contact for testing."""
    return {
        "id": str(uuid.uuid4()),
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+15551234567",
        "preferred_channel": "email"
    }


@pytest.fixture
def sample_communication_request(sample_contact):
    """Sample communication request."""
    return {
        "channel": "email",
        "recipient": sample_contact,
        "content": "Test message",
        "subject": "Test Subject",
        "priority": "normal"
    }


class TestUnifiedCommunicationAPI:
    """Test unified communication API endpoints."""
    
    def setup_method(self):
        """Setup method to reset service before each test."""
        # Reset the global service instance
        set_communication_service(None)
    
    def test_send_communication_success(self, sample_communication_request):
        """Test successful communication sending."""
        # Setup mock service
        mock_service = Mock(spec=UnifiedCommunicationService)
        mock_response = CommunicationResponse(
            request_id=uuid.uuid4(),
            channel=CommunicationChannel.EMAIL,
            message_id=uuid.uuid4(),
            status=MessageStatus.SENT,
            sent_at=datetime.now()
        )
        mock_service.send_communication = AsyncMock(return_value=mock_response)
        
        # Set the mock service
        set_communication_service(mock_service)
        
        # Make request
        response = client.post("/api/communication/send", json=sample_communication_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["channel"] == "email"
        assert data["status"] == "sent"
        assert "request_id" in data
        assert "message_id" in data
    
    def test_send_communication_failure(self, sample_communication_request):
        """Test communication sending failure."""
        # Setup mock service to raise exception
        mock_service = Mock(spec=UnifiedCommunicationService)
        mock_service.send_communication = AsyncMock(side_effect=ValueError("Test error"))
        
        # Set the mock service
        set_communication_service(mock_service)
        
        # Make request
        response = client.post("/api/communication/send", json=sample_communication_request)
        
        assert response.status_code == 400
        assert "Test error" in response.json()["detail"]
    
    def test_send_multi_channel_communication(self, sample_contact):
        """Test multi-channel communication sending."""
        # Setup mock service
        mock_service = Mock(spec=UnifiedCommunicationService)
        mock_responses = [
            CommunicationResponse(
                request_id=uuid.uuid4(),
                channel=CommunicationChannel.EMAIL,
                message_id=uuid.uuid4(),
                status=MessageStatus.SENT
            ),
            CommunicationResponse(
                request_id=uuid.uuid4(),
                channel=CommunicationChannel.SMS,
                message_id=uuid.uuid4(),
                status=MessageStatus.SENT
            )
        ]
        mock_service.send_multi_channel_communication = AsyncMock(return_value=mock_responses)
        
        # Set the mock service
        set_communication_service(mock_service)
        
        # Make request
        request_data = {
            "recipient": sample_contact,
            "content": "Test message",
            "subject": "Test Subject",
            "channels": ["email", "sms"],
            "delay_between_channels": 0.5
        }
        
        response = client.post("/api/communication/send-multi-channel", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["channel"] == "email"
        assert data[1]["channel"] == "sms"
        assert all(item["status"] == "sent" for item in data)
    
    def test_get_communication_status_found(self):
        """Test getting communication status when found."""
        # Setup mock service
        mock_service = Mock(spec=UnifiedCommunicationService)
        request_id = uuid.uuid4()
        mock_response = CommunicationResponse(
            request_id=request_id,
            channel=CommunicationChannel.EMAIL,
            message_id=uuid.uuid4(),
            status=MessageStatus.DELIVERED,
            sent_at=datetime.now()
        )
        mock_service.get_request_status.return_value = mock_response
        
        # Set the mock service
        set_communication_service(mock_service)
        
        # Make request
        response = client.get(f"/api/communication/status/{request_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["request_id"] == str(request_id)
        assert data["status"] == "delivered"
    
    def test_get_communication_status_not_found(self):
        """Test getting communication status when not found."""
        # Setup mock service
        mock_service = Mock(spec=UnifiedCommunicationService)
        mock_service.get_request_status.return_value = None
        
        # Set the mock service
        set_communication_service(mock_service)
        
        # Make request
        request_id = uuid.uuid4()
        response = client.get(f"/api/communication/status/{request_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_communication_history(self):
        """Test getting communication history."""
        # Setup mock service
        mock_service = Mock(spec=UnifiedCommunicationService)
        contact_id = uuid.uuid4()
        mock_history = [
            CommunicationHistory(
                id=uuid.uuid4(),
                contact_id=contact_id,
                channel=CommunicationChannel.EMAIL,
                message_id=uuid.uuid4(),
                direction="outbound",
                subject="Test Subject",
                content="Test message",
                status=MessageStatus.SENT,
                timestamp=datetime.now(),
                metadata={}
            )
        ]
        mock_service.get_communication_history.return_value = mock_history
        
        # Set the mock service
        set_communication_service(mock_service)
        
        # Make request
        response = client.get(f"/api/communication/history/{contact_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["contact_id"] == str(contact_id)
        assert data[0]["channel"] == "email"
    
    def test_get_communication_history_with_filters(self):
        """Test getting communication history with filters."""
        # Setup mock service
        mock_service = Mock(spec=UnifiedCommunicationService)
        contact_id = uuid.uuid4()
        mock_service.get_communication_history.return_value = []
        
        # Set the mock service
        set_communication_service(mock_service)
        
        # Make request with filters
        response = client.get(
            f"/api/communication/history/{contact_id}?channel=email&limit=10"
        )
        
        assert response.status_code == 200
        # Verify service was called with correct parameters
        mock_service.get_communication_history.assert_called_once_with(
            contact_id, CommunicationChannel.EMAIL, 10
        )
    
    def test_set_communication_preferences(self):
        """Test setting communication preferences."""
        # Setup mock service
        mock_service = Mock(spec=UnifiedCommunicationService)
        mock_service.set_communication_preferences.return_value = None
        
        # Set the mock service
        set_communication_service(mock_service)
        
        # Make request
        contact_id = uuid.uuid4()
        preferences_data = {
            "contact_id": str(contact_id),
            "email_enabled": True,
            "sms_enabled": False,
            "voice_enabled": True,
            "preferred_channel": "email",
            "do_not_contact": False,
            "unsubscribed_channels": []
        }
        
        response = client.post(
            f"/api/communication/preferences/{contact_id}",
            json=preferences_data
        )
        
        assert response.status_code == 200
        assert "successfully" in response.json()["message"]
    
    def test_get_communication_preferences_found(self):
        """Test getting communication preferences when found."""
        # Setup mock service
        mock_service = Mock(spec=UnifiedCommunicationService)
        contact_id = uuid.uuid4()
        mock_preferences = CommunicationPreferences(
            contact_id=contact_id,
            email_enabled=True,
            sms_enabled=False,
            preferred_channel=CommunicationChannel.EMAIL
        )
        mock_service.get_communication_preferences.return_value = mock_preferences
        
        # Set the mock service
        set_communication_service(mock_service)
        
        # Make request
        response = client.get(f"/api/communication/preferences/{contact_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["contact_id"] == str(contact_id)
        assert data["email_enabled"] is True
        assert data["sms_enabled"] is False
    
    def test_get_communication_preferences_not_found(self):
        """Test getting communication preferences when not found."""
        # Setup mock service
        mock_service = Mock(spec=UnifiedCommunicationService)
        mock_service.get_communication_preferences.return_value = None
        
        # Set the mock service
        set_communication_service(mock_service)
        
        # Make request
        contact_id = uuid.uuid4()
        response = client.get(f"/api/communication/preferences/{contact_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_communication_analytics(self):
        """Test getting communication analytics."""
        # Setup mock service
        mock_service = Mock(spec=UnifiedCommunicationService)
        from app.models.communication import CommunicationAnalytics
        
        mock_analytics = {
            CommunicationChannel.EMAIL: CommunicationAnalytics(
                channel=CommunicationChannel.EMAIL,
                total_sent=100,
                total_delivered=95,
                delivery_rate=0.95,
                period_start=datetime.now() - timedelta(days=7),
                period_end=datetime.now()
            )
        }
        mock_service.get_unified_analytics = AsyncMock(return_value=mock_analytics)
        
        # Set the mock service
        set_communication_service(mock_service)
        
        # Make request
        analytics_request = {
            "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "channel": "email"
        }
        
        response = client.post("/api/communication/analytics", json=analytics_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert data["email"]["total_sent"] == 100
    
    def test_get_active_services(self):
        """Test getting active services."""
        # Setup mock service
        mock_service = Mock(spec=UnifiedCommunicationService)
        mock_service.get_active_services.return_value = [
            CommunicationChannel.EMAIL,
            CommunicationChannel.SMS
        ]
        
        # Set the mock service
        set_communication_service(mock_service)
        
        # Make request
        response = client.get("/api/communication/services")
        
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "sms" in data
        assert len(data) == 2
    
    def test_test_service_connectivity(self):
        """Test service connectivity testing."""
        # Setup mock service
        mock_service = Mock(spec=UnifiedCommunicationService)
        mock_connectivity = {
            CommunicationChannel.EMAIL: True,
            CommunicationChannel.SMS: False,
            CommunicationChannel.VOICE: True
        }
        mock_service.test_service_connectivity = AsyncMock(return_value=mock_connectivity)
        
        # Set the mock service
        set_communication_service(mock_service)
        
        # Make request
        response = client.get("/api/communication/connectivity")
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] is True
        assert data["sms"] is False
        assert data["voice"] is True
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/api/communication/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "unified_communication"
    
    def test_invalid_request_data(self):
        """Test API with invalid request data."""
        # Test with missing required fields
        invalid_request = {
            "channel": "email",
            # Missing recipient and content
        }
        
        response = client.post("/api/communication/send", json=invalid_request)
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_channel(self, sample_contact):
        """Test API with invalid channel."""
        invalid_request = {
            "channel": "invalid_channel",
            "recipient": sample_contact,
            "content": "Test message"
        }
        
        response = client.post("/api/communication/send", json=invalid_request)
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_uuid(self):
        """Test API with invalid UUID."""
        response = client.get("/api/communication/status/invalid-uuid")
        
        assert response.status_code == 422  # Validation error


@pytest.mark.integration
class TestUnifiedCommunicationAPIIntegration:
    """Integration tests for unified communication API."""
    
    @pytest.mark.skip(reason="Requires real service configurations")
    def test_real_service_integration(self):
        """Test with real service integrations."""
        # This would test with actual email/SMS/voice services
        pass
    
    def test_api_documentation(self):
        """Test that API documentation is accessible."""
        response = client.get("/docs")
        # This would test if the OpenAPI docs are accessible
        # Skipping for now as it requires proper FastAPI setup