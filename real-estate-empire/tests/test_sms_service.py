"""
Tests for SMS service integration.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import uuid

from app.services.sms_service import (
    SMSService, SMSServiceConfig, SMSTemplateEngine, SMSComplianceManager
)
from app.models.communication import (
    SMSMessage, SMSTemplate, MessageStatus, MessagePriority,
    CommunicationChannel
)


@pytest.fixture
def sms_config():
    """SMS service configuration for testing."""
    return SMSServiceConfig(
        twilio_account_sid="test_sid",
        twilio_auth_token="test_token",
        default_from_phone="+15551234567",
        webhook_url="https://example.com/webhook"
    )


@pytest.fixture
def sms_service(sms_config):
    """SMS service instance for testing."""
    with patch('app.services.sms_service.Client') as mock_client:
        service = SMSService(sms_config)
        service.twilio_client = mock_client.return_value
        return service


@pytest.fixture
def sample_template():
    """Sample SMS template for testing."""
    return SMSTemplate(
        id=uuid.uuid4(),
        name="Welcome SMS",
        message="Welcome {{name}}! Thanks for joining us. Reply STOP to opt out.",
        variables=["name"],
        category="onboarding"
    )


@pytest.fixture
def sample_message():
    """Sample SMS message for testing."""
    return SMSMessage(
        id=uuid.uuid4(),
        to_phone="+15559876543",
        message="This is a test SMS message.",
        priority=MessagePriority.NORMAL
    )


class TestSMSTemplateEngine:
    """Test SMS template engine."""
    
    def test_render_template(self, sample_template):
        """Test template rendering with variables."""
        engine = SMSTemplateEngine()
        variables = {"name": "John Doe"}
        
        rendered = engine.render_template(sample_template, variables)
        
        assert "Welcome John Doe!" in rendered
        assert "Reply STOP to opt out." in rendered
    
    def test_validate_template_valid(self, sample_template):
        """Test validation of valid template."""
        engine = SMSTemplateEngine()
        errors = engine.validate_template(sample_template)
        assert len(errors) == 0
    
    def test_validate_template_invalid(self):
        """Test validation of invalid template."""
        engine = SMSTemplateEngine()
        invalid_template = SMSTemplate(
            name="Invalid Template",
            message="Welcome {{invalid_syntax",  # Missing closing brace
            variables=["name"]
        )
        
        errors = engine.validate_template(invalid_template)
        assert len(errors) > 0
    
    def test_validate_template_too_long(self):
        """Test validation of template that's too long."""
        engine = SMSTemplateEngine()
        long_template = SMSTemplate(
            name="Long Template",
            message="x" * 1601,  # Exceeds 1600 character limit
            variables=[]
        )
        
        errors = engine.validate_template(long_template)
        assert any("too long" in error for error in errors)


class TestSMSComplianceManager:
    """Test SMS compliance manager."""
    
    def test_normalize_phone_number(self):
        """Test phone number normalization."""
        manager = SMSComplianceManager()
        
        # Test various formats
        assert manager.normalize_phone_number("(555) 123-4567") == "15551234567"
        assert manager.normalize_phone_number("555-123-4567") == "15551234567"
        assert manager.normalize_phone_number("5551234567") == "15551234567"
        assert manager.normalize_phone_number("+1 555 123 4567") == "15551234567"
        assert manager.normalize_phone_number("15551234567") == "15551234567"
    
    def test_validate_phone_number(self):
        """Test phone number validation."""
        manager = SMSComplianceManager()
        
        assert manager.validate_phone_number("5551234567") is True
        assert manager.validate_phone_number("+15551234567") is True
        assert manager.validate_phone_number("(555) 123-4567") is True
        assert manager.validate_phone_number("123") is False
        assert manager.validate_phone_number("") is False
    
    def test_opt_out_functionality(self):
        """Test opt-out functionality."""
        manager = SMSComplianceManager()
        phone = "+15551234567"
        
        # Initially not opted out
        assert manager.is_opted_out(phone) is False
        
        # Opt out
        manager.opt_out_number(phone)
        assert manager.is_opted_out(phone) is True
        
        # Opt back in
        manager.opt_in_number(phone)
        assert manager.is_opted_out(phone) is False
    
    def test_process_incoming_message_opt_out(self):
        """Test processing incoming opt-out message."""
        manager = SMSComplianceManager()
        phone = "+15551234567"
        
        response = manager.process_incoming_message(phone, "STOP")
        
        assert response is not None
        assert "unsubscribed" in response.lower()
        assert manager.is_opted_out(phone) is True
    
    def test_process_incoming_message_opt_in(self):
        """Test processing incoming opt-in message."""
        manager = SMSComplianceManager()
        phone = "+15551234567"
        
        # First opt out
        manager.opt_out_number(phone)
        assert manager.is_opted_out(phone) is True
        
        # Then opt back in
        response = manager.process_incoming_message(phone, "START")
        
        assert response is not None
        assert "subscribed" in response.lower()
        assert manager.is_opted_out(phone) is False
    
    def test_process_incoming_message_regular(self):
        """Test processing regular incoming message."""
        manager = SMSComplianceManager()
        phone = "+15551234567"
        
        response = manager.process_incoming_message(phone, "Hello, this is a regular message")
        
        assert response is None
        assert manager.is_opted_out(phone) is False


class TestSMSService:
    """Test SMS service."""
    
    def test_create_template(self, sms_service, sample_template):
        """Test template creation."""
        created_template = sms_service.create_template(sample_template)
        
        assert created_template.id is not None
        assert created_template.created_at is not None
        assert created_template.updated_at is not None
        assert sms_service.get_template(created_template.id) == created_template
    
    def test_update_template(self, sms_service, sample_template):
        """Test template update."""
        created_template = sms_service.create_template(sample_template)
        
        updates = {"message": "Updated message"}
        updated_template = sms_service.update_template(created_template.id, updates)
        
        assert updated_template.message == "Updated message"
        assert updated_template.updated_at > created_template.created_at
    
    def test_list_templates(self, sms_service):
        """Test template listing."""
        template1 = SMSTemplate(
            name="Template 1",
            message="Message 1",
            category="category1"
        )
        template2 = SMSTemplate(
            name="Template 2",
            message="Message 2",
            category="category2"
        )
        
        sms_service.create_template(template1)
        sms_service.create_template(template2)
        
        all_templates = sms_service.list_templates()
        assert len(all_templates) == 2
        
        category1_templates = sms_service.list_templates(category="category1")
        assert len(category1_templates) == 1
        assert category1_templates[0].name == "Template 1"
    
    def test_delete_template(self, sms_service, sample_template):
        """Test template deletion."""
        created_template = sms_service.create_template(sample_template)
        
        result = sms_service.delete_template(created_template.id)
        assert result is True
        assert sms_service.get_template(created_template.id) is None
    
    @pytest.mark.asyncio
    async def test_send_sms(self, sms_service, sample_message):
        """Test SMS sending."""
        mock_message = MagicMock()
        mock_message.sid = "test_sid"
        sms_service.twilio_client.messages.create.return_value = mock_message
        
        result = await sms_service.send_sms(sample_message)
        
        assert result is True
        assert sample_message.status == MessageStatus.SENT
        assert sample_message.sent_at is not None
        sms_service.twilio_client.messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_sms_opted_out(self, sms_service, sample_message):
        """Test SMS sending to opted-out number."""
        # Opt out the number first
        sms_service.compliance_manager.opt_out_number(sample_message.to_phone)
        
        result = await sms_service.send_sms(sample_message)
        
        assert result is False
        assert sample_message.status == MessageStatus.FAILED
        sms_service.twilio_client.messages.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_send_sms_invalid_phone(self, sms_service):
        """Test SMS sending to invalid phone number."""
        invalid_message = SMSMessage(
            id=uuid.uuid4(),
            to_phone="123",  # Invalid phone number
            message="Test message"
        )
        
        result = await sms_service.send_sms(invalid_message)
        
        assert result is False
        assert invalid_message.status == MessageStatus.FAILED
        sms_service.twilio_client.messages.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_send_template_sms(self, sms_service, sample_template):
        """Test sending SMS with template."""
        mock_message = MagicMock()
        mock_message.sid = "test_sid"
        sms_service.twilio_client.messages.create.return_value = mock_message
        sms_service.create_template(sample_template)
        
        variables = {"name": "John Doe"}
        message = await sms_service.send_template_sms(
            template_id=sample_template.id,
            to_phone="+15559876543",
            variables=variables
        )
        
        assert "Welcome John Doe!" in message.message
        assert message.status == MessageStatus.SENT
        assert message.template_id == sample_template.id
        sms_service.twilio_client.messages.create.assert_called_once()
    
    def test_handle_delivery_status(self, sms_service, sample_message):
        """Test delivery status handling."""
        sms_service.sent_messages[sample_message.id] = sample_message
        
        sms_service.handle_delivery_status(sample_message.id, "delivered")
        
        assert sample_message.status == MessageStatus.DELIVERED
        assert sample_message.delivered_at is not None
    
    @pytest.mark.asyncio
    async def test_handle_incoming_message_opt_out(self, sms_service):
        """Test handling incoming opt-out message."""
        phone = "+15551234567"
        
        with patch.object(sms_service, 'send_sms') as mock_send:
            response = sms_service.handle_incoming_message(phone, "STOP")
            
            assert response is not None
            assert "unsubscribed" in response.lower()
            assert sms_service.compliance_manager.is_opted_out(phone) is True
            mock_send.assert_called_once()
    
    def test_get_analytics(self, sms_service):
        """Test analytics generation."""
        # Create test messages
        now = datetime.now()
        messages = []
        
        for i in range(10):
            message = SMSMessage(
                id=uuid.uuid4(),
                to_phone=f"+155512345{i:02d}",
                message=f"Test {i}",
                status=MessageStatus.SENT if i < 8 else MessageStatus.FAILED,
                sent_at=now - timedelta(hours=i)
            )
            messages.append(message)
            sms_service.sent_messages[message.id] = message
        
        # Set some as delivered
        for i in range(6):
            if messages[i].status != MessageStatus.FAILED:
                messages[i].status = MessageStatus.DELIVERED
        
        start_date = now - timedelta(days=1)
        end_date = now + timedelta(days=1)
        
        analytics = sms_service.get_analytics(start_date, end_date)
        
        assert analytics.channel == CommunicationChannel.SMS
        assert analytics.total_sent == 10
        assert analytics.total_delivered == 6
        assert analytics.total_bounced == 2
        assert analytics.delivery_rate == 0.6
        assert analytics.bounce_rate == 0.2
        assert analytics.open_rate == 0.0  # SMS doesn't track opens
        assert analytics.click_rate == 0.0  # SMS doesn't track clicks
    
    @pytest.mark.asyncio
    async def test_send_bulk_sms(self, sms_service, sample_template):
        """Test bulk SMS sending."""
        mock_message = MagicMock()
        mock_message.sid = "test_sid"
        sms_service.twilio_client.messages.create.return_value = mock_message
        sms_service.create_template(sample_template)
        
        recipients = [
            {"phone": "+15551234567", "variables": {"name": "User 1"}},
            {"phone": "+15551234568", "variables": {"name": "User 2"}},
            {"phone": "+15551234569", "variables": {"name": "User 3"}}
        ]
        
        messages = await sms_service.send_bulk_sms(
            template_id=sample_template.id,
            recipients=recipients,
            batch_size=2,
            delay_seconds=0.1
        )
        
        assert len(messages) == 3
        assert all(msg.status == MessageStatus.SENT for msg in messages)
        assert sms_service.twilio_client.messages.create.call_count == 3
    
    def test_opt_out_management(self, sms_service):
        """Test opt-out management functions."""
        phone_numbers = ["+15551234567", "+15551234568", "+15551234569"]
        
        # Import opt-outs
        sms_service.import_opt_outs(phone_numbers)
        assert sms_service.get_opt_out_count() == 3
        
        # Export opt-outs
        exported = sms_service.export_opt_outs()
        assert len(exported) == 3
        
        # Check that normalized numbers are stored
        for phone in phone_numbers:
            normalized = sms_service.compliance_manager.normalize_phone_number(phone)
            assert normalized in exported


@pytest.mark.integration
class TestSMSServiceIntegration:
    """Integration tests for SMS service."""
    
    @pytest.mark.asyncio
    async def test_full_sms_workflow(self, sms_service):
        """Test complete SMS workflow."""
        # Create template
        template = SMSTemplate(
            name="Integration Test",
            message="Hello {{name}}! This is a test. Reply STOP to opt out.",
            variables=["name"],
            category="test"
        )
        
        created_template = sms_service.create_template(template)
        
        # Mock Twilio for integration test
        mock_message = MagicMock()
        mock_message.sid = "test_sid"
        sms_service.twilio_client.messages.create.return_value = mock_message
        
        # Send template SMS
        message = await sms_service.send_template_sms(
            template_id=created_template.id,
            to_phone="+15559876543",
            variables={"name": "Integration Test"}
        )
        
        # Verify message
        assert "Hello Integration Test!" in message.message
        assert message.status == MessageStatus.SENT
        assert message.to_phone == "+15559876543"
        
        # Test delivery status update
        sms_service.handle_delivery_status(message.id, "delivered")
        assert message.status == MessageStatus.DELIVERED
        
        # Test analytics
        start_date = datetime.now() - timedelta(hours=1)
        end_date = datetime.now() + timedelta(hours=1)
        
        analytics = sms_service.get_analytics(start_date, end_date)
        assert analytics.total_sent >= 1
        assert analytics.total_delivered >= 1
        
        # Test incoming message handling
        response = sms_service.handle_incoming_message("+15559876543", "STOP")
        assert response is not None
        assert sms_service.compliance_manager.is_opted_out("+15559876543") is True
        
        # Clean up
        sms_service.delete_template(created_template.id)


if __name__ == "__main__":
    pytest.main([__file__])