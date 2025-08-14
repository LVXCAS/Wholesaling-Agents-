"""
Tests for email service integration.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import uuid

from app.services.email_service import (
    EmailService, EmailServiceConfig, EmailTemplateEngine, EmailTracker
)
from app.models.communication import (
    EmailMessage, EmailTemplate, MessageStatus, MessagePriority,
    CommunicationChannel
)


@pytest.fixture
def email_config():
    """Email service configuration for testing."""
    return EmailServiceConfig(
        smtp_host="smtp.test.com",
        smtp_port=587,
        smtp_username="test@example.com",
        smtp_password="password",
        default_from_email="test@example.com",
        default_from_name="Test Sender"
    )


@pytest.fixture
def email_service(email_config):
    """Email service instance for testing."""
    return EmailService(email_config)


@pytest.fixture
def sample_template():
    """Sample email template for testing."""
    return EmailTemplate(
        id=uuid.uuid4(),
        name="Welcome Email",
        subject="Welcome {{name}}!",
        body_html="<h1>Welcome {{name}}!</h1><p>Thanks for joining us.</p>",
        body_text="Welcome {{name}}! Thanks for joining us.",
        variables=["name"],
        category="onboarding"
    )


@pytest.fixture
def sample_message():
    """Sample email message for testing."""
    return EmailMessage(
        id=uuid.uuid4(),
        to_email="recipient@example.com",
        to_name="John Doe",
        subject="Test Email",
        body_html="<p>This is a test email.</p>",
        body_text="This is a test email.",
        priority=MessagePriority.NORMAL
    )


class TestEmailTemplateEngine:
    """Test email template engine."""
    
    def test_render_template(self, sample_template):
        """Test template rendering with variables."""
        engine = EmailTemplateEngine()
        variables = {"name": "John Doe"}
        
        rendered = engine.render_template(sample_template, variables)
        
        assert rendered["subject"] == "Welcome John Doe!"
        assert "Welcome John Doe!" in rendered["body_html"]
        assert "Welcome John Doe!" in rendered["body_text"]
    
    def test_validate_template_valid(self, sample_template):
        """Test validation of valid template."""
        engine = EmailTemplateEngine()
        errors = engine.validate_template(sample_template)
        assert len(errors) == 0
    
    def test_validate_template_invalid(self):
        """Test validation of invalid template."""
        engine = EmailTemplateEngine()
        invalid_template = EmailTemplate(
            name="Invalid Template",
            subject="Welcome {{name}!",  # Missing closing brace
            body_html="<h1>Welcome {{invalid_syntax</h1>",
            body_text="Welcome {{name}}!",
            variables=["name"]
        )
        
        errors = engine.validate_template(invalid_template)
        assert len(errors) > 0


class TestEmailTracker:
    """Test email tracker."""
    
    def test_generate_tracking_pixel(self):
        """Test tracking pixel generation."""
        tracker = EmailTracker()
        message_id = uuid.uuid4()
        
        pixel = tracker.generate_tracking_pixel(message_id)
        
        assert str(message_id) in pixel
        assert 'width="1"' in pixel
        assert 'height="1"' in pixel
    
    def test_generate_tracking_links(self):
        """Test tracking link generation."""
        tracker = EmailTracker()
        message_id = uuid.uuid4()
        content = '<a href="https://example.com">Click here</a>'
        
        tracked_content = tracker.generate_tracking_links(content, message_id)
        
        assert str(message_id) in tracked_content
        assert "track/click" in tracked_content
    
    def test_track_open(self):
        """Test email open tracking."""
        tracker = EmailTracker()
        message_id = uuid.uuid4()
        
        tracker.track_open(message_id)
        
        assert message_id in tracker.tracking_data
        assert "opened_at" in tracker.tracking_data[message_id]
    
    def test_track_click(self):
        """Test email click tracking."""
        tracker = EmailTracker()
        message_id = uuid.uuid4()
        url = "https://example.com"
        
        tracker.track_click(message_id, url)
        
        assert message_id in tracker.tracking_data
        assert "clicks" in tracker.tracking_data[message_id]
        assert len(tracker.tracking_data[message_id]["clicks"]) == 1
        assert tracker.tracking_data[message_id]["clicks"][0]["url"] == url


class TestEmailService:
    """Test email service."""
    
    def test_create_template(self, email_service, sample_template):
        """Test template creation."""
        created_template = email_service.create_template(sample_template)
        
        assert created_template.id is not None
        assert created_template.created_at is not None
        assert created_template.updated_at is not None
        assert email_service.get_template(created_template.id) == created_template
    
    def test_update_template(self, email_service, sample_template):
        """Test template update."""
        created_template = email_service.create_template(sample_template)
        
        updates = {"subject": "Updated Subject"}
        updated_template = email_service.update_template(created_template.id, updates)
        
        assert updated_template.subject == "Updated Subject"
        assert updated_template.updated_at > created_template.created_at
    
    def test_list_templates(self, email_service):
        """Test template listing."""
        template1 = EmailTemplate(
            name="Template 1",
            subject="Subject 1",
            body_html="<p>Body 1</p>",
            body_text="Body 1",
            category="category1"
        )
        template2 = EmailTemplate(
            name="Template 2",
            subject="Subject 2",
            body_html="<p>Body 2</p>",
            body_text="Body 2",
            category="category2"
        )
        
        email_service.create_template(template1)
        email_service.create_template(template2)
        
        all_templates = email_service.list_templates()
        assert len(all_templates) == 2
        
        category1_templates = email_service.list_templates(category="category1")
        assert len(category1_templates) == 1
        assert category1_templates[0].name == "Template 1"
    
    def test_delete_template(self, email_service, sample_template):
        """Test template deletion."""
        created_template = email_service.create_template(sample_template)
        
        result = email_service.delete_template(created_template.id)
        assert result is True
        assert email_service.get_template(created_template.id) is None
    
    @patch('app.services.email_service.aiosmtplib.send')
    @pytest.mark.asyncio
    async def test_send_email(self, mock_send, email_service, sample_message):
        """Test email sending."""
        mock_send.return_value = None
        
        result = await email_service.send_email(sample_message)
        
        assert result is True
        assert sample_message.status == MessageStatus.SENT
        assert sample_message.sent_at is not None
        mock_send.assert_called_once()
    
    @patch('app.services.email_service.aiosmtplib.send')
    @pytest.mark.asyncio
    async def test_send_email_failure(self, mock_send, email_service, sample_message):
        """Test email sending failure."""
        mock_send.side_effect = Exception("SMTP Error")
        
        result = await email_service.send_email(sample_message)
        
        assert result is False
        assert sample_message.status == MessageStatus.FAILED
    
    @patch('app.services.email_service.aiosmtplib.send')
    @pytest.mark.asyncio
    async def test_send_template_email(self, mock_send, email_service, sample_template):
        """Test sending email with template."""
        mock_send.return_value = None
        email_service.create_template(sample_template)
        
        variables = {"name": "John Doe"}
        message = await email_service.send_template_email(
            template_id=sample_template.id,
            to_email="test@example.com",
            variables=variables
        )
        
        assert message.subject == "Welcome John Doe!"
        assert message.status == MessageStatus.SENT
        assert message.template_id == sample_template.id
        mock_send.assert_called_once()
    
    def test_handle_bounce(self, email_service, sample_message):
        """Test bounce handling."""
        email_service.sent_messages[sample_message.id] = sample_message
        
        email_service.handle_bounce(sample_message.id, "Invalid email address")
        
        assert sample_message.status == MessageStatus.BOUNCED
        assert sample_message.bounced_at is not None
        assert sample_message.bounce_reason == "Invalid email address"
    
    def test_handle_reply(self, email_service, sample_message):
        """Test reply handling."""
        email_service.sent_messages[sample_message.id] = sample_message
        
        email_service.handle_reply(sample_message.id, "Thanks for the email!")
        
        assert sample_message.status == MessageStatus.REPLIED
    
    def test_get_analytics(self, email_service):
        """Test analytics generation."""
        # Create test messages
        now = datetime.now()
        messages = []
        
        for i in range(10):
            message = EmailMessage(
                id=uuid.uuid4(),
                to_email=f"test{i}@example.com",
                subject=f"Test {i}",
                body_html=f"<p>Test {i}</p>",
                body_text=f"Test {i}",
                status=MessageStatus.SENT if i < 8 else MessageStatus.BOUNCED,
                sent_at=now - timedelta(hours=i)
            )
            messages.append(message)
            email_service.sent_messages[message.id] = message
        
        # Set some as delivered and opened
        # First 3 are opened (which implies delivered)
        for i in range(3):
            if messages[i].status != MessageStatus.BOUNCED:
                messages[i].status = MessageStatus.OPENED
        # Next 3 are delivered but not opened
        for i in range(3, 6):
            if messages[i].status != MessageStatus.BOUNCED:
                messages[i].status = MessageStatus.DELIVERED
        # The rest remain as SENT or BOUNCED
        
        start_date = now - timedelta(days=1)
        end_date = now + timedelta(days=1)
        
        analytics = email_service.get_analytics(start_date, end_date)
        
        assert analytics.channel == CommunicationChannel.EMAIL
        assert analytics.total_sent == 10
        assert analytics.total_delivered == 3  # Only those explicitly set to DELIVERED
        assert analytics.total_opened == 3     # Those set to OPENED
        assert analytics.total_bounced == 2    # Last 2 were set to BOUNCED
        assert analytics.delivery_rate == 0.3  # 3/10
        assert analytics.open_rate == 1.0      # 3/3 (all delivered were opened)
        assert analytics.bounce_rate == 0.2    # 2/10
    
    @patch('app.services.email_service.aiosmtplib.send')
    @pytest.mark.asyncio
    async def test_send_bulk_emails(self, mock_send, email_service, sample_template):
        """Test bulk email sending."""
        mock_send.return_value = None
        email_service.create_template(sample_template)
        
        recipients = [
            {"email": "user1@example.com", "variables": {"name": "User 1"}},
            {"email": "user2@example.com", "variables": {"name": "User 2"}},
            {"email": "user3@example.com", "variables": {"name": "User 3"}}
        ]
        
        messages = await email_service.send_bulk_emails(
            template_id=sample_template.id,
            recipients=recipients,
            batch_size=2,
            delay_seconds=0.1
        )
        
        assert len(messages) == 3
        assert all(msg.status == MessageStatus.SENT for msg in messages)
        assert mock_send.call_count == 3


@pytest.mark.integration
class TestEmailServiceIntegration:
    """Integration tests for email service."""
    
    @pytest.mark.asyncio
    async def test_full_email_workflow(self, email_service):
        """Test complete email workflow."""
        # Create template
        template = EmailTemplate(
            name="Integration Test",
            subject="Hello {{name}}",
            body_html="<h1>Hello {{name}}</h1><p>This is a test.</p>",
            body_text="Hello {{name}}. This is a test.",
            variables=["name"],
            category="test"
        )
        
        created_template = email_service.create_template(template)
        
        # Mock SMTP for integration test
        with patch('app.services.email_service.aiosmtplib.send') as mock_send:
            mock_send.return_value = None
            
            # Send template email
            message = await email_service.send_template_email(
                template_id=created_template.id,
                to_email="integration@example.com",
                variables={"name": "Integration Test"},
                to_name="Test User"
            )
            
            # Verify message
            assert message.subject == "Hello Integration Test"
            assert message.status == MessageStatus.SENT
            assert message.to_email == "integration@example.com"
            
            # Test analytics
            start_date = datetime.now() - timedelta(hours=1)
            end_date = datetime.now() + timedelta(hours=1)
            
            analytics = email_service.get_analytics(start_date, end_date)
            assert analytics.total_sent >= 1
            
            # Clean up
            email_service.delete_template(created_template.id)


if __name__ == "__main__":
    pytest.main([__file__])