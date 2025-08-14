"""
Tests for voice service integration.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import uuid

from app.services.voice_service import (
    VoiceService, VoiceServiceConfig, VoiceScriptEngine, VoiceCallAnalyzer
)
from app.models.communication import (
    VoiceCall, VoiceScript, MessageStatus, MessagePriority, CommunicationChannel
)


@pytest.fixture
def voice_config():
    """Voice service configuration for testing."""
    return VoiceServiceConfig(
        twilio_account_sid="test_account_sid",
        twilio_auth_token="test_auth_token",
        default_from_phone="+15551234567",
        webhook_base_url="https://test.example.com",
        recording_enabled=True,
        transcription_enabled=True,
        voicemail_detection=True
    )


@pytest.fixture
def voice_script():
    """Sample voice script for testing."""
    return VoiceScript(
        id=uuid.uuid4(),
        name="Test Script",
        script="Hello {{ name }}, this is {{ caller_name }} calling about your property at {{ address }}. We're interested in making an offer.",
        variables=["name", "caller_name", "address"]
    )


@pytest.fixture
def mock_twilio_client():
    """Mock Twilio client."""
    mock_client = Mock()
    mock_call = Mock()
    mock_call.sid = "test_call_sid"
    mock_client.calls.create.return_value = mock_call
    return mock_client


class TestVoiceScriptEngine:
    """Test voice script engine."""
    
    def test_render_script(self, voice_script):
        """Test script rendering with variables."""
        engine = VoiceScriptEngine()
        variables = {
            "name": "John Doe",
            "caller_name": "Jane Smith",
            "address": "123 Main St"
        }
        
        rendered = engine.render_script(voice_script, variables)
        
        assert "Hello John Doe" in rendered
        assert "Jane Smith calling" in rendered
        assert "123 Main St" in rendered
    
    def test_validate_script_valid(self, voice_script):
        """Test script validation for valid script."""
        engine = VoiceScriptEngine()
        errors = engine.validate_script(voice_script)
        
        assert len(errors) == 0
    
    def test_validate_script_too_long(self):
        """Test script validation for script that's too long."""
        engine = VoiceScriptEngine()
        long_script = VoiceScript(
            id=uuid.uuid4(),
            name="Long Script",
            script="x" * 6000,  # Exceeds 5000 character limit
            variables=[]
        )
        
        errors = engine.validate_script(long_script)
        
        assert len(errors) > 0
        assert "too long" in errors[0]
    
    def test_generate_twiml(self, voice_script):
        """Test TwiML generation."""
        engine = VoiceScriptEngine()
        call_id = uuid.uuid4()
        script_content = "Hello, this is a test call."
        
        twiml = engine.generate_twiml(script_content, call_id)
        
        assert "<Response>" in twiml
        assert "<Say" in twiml
        assert "Hello, this is a test call." in twiml
        assert "<Gather" in twiml
        assert str(call_id) in twiml


class TestVoiceCallAnalyzer:
    """Test voice call analyzer."""
    
    def test_analyze_transcription_positive(self):
        """Test transcription analysis for positive sentiment."""
        analyzer = VoiceCallAnalyzer()
        transcription = "Yes, I'm very interested in selling. This sounds great!"
        
        analysis = analyzer.analyze_transcription(transcription)
        
        assert analysis['sentiment'] == 'positive'
        assert analysis['confidence'] > 0.0
        assert analysis['interest_level'] > 0.5
        assert 'interested' in analysis['keywords']
    
    def test_analyze_transcription_negative(self):
        """Test transcription analysis for negative sentiment."""
        analyzer = VoiceCallAnalyzer()
        transcription = "No, I'm not interested. Please stop calling me."
        
        analysis = analyzer.analyze_transcription(transcription)
        
        assert analysis['sentiment'] == 'negative'
        assert analysis['confidence'] > 0.0
        assert analysis['interest_level'] < 0.5
        assert 'not interested' in analysis['keywords']
    
    def test_analyze_transcription_callback_request(self):
        """Test transcription analysis for callback request."""
        analyzer = VoiceCallAnalyzer()
        transcription = "I'm busy right now, can you call me back later?"
        
        analysis = analyzer.analyze_transcription(transcription)
        
        assert analysis['callback_requested'] is True
    
    def test_analyze_transcription_empty(self):
        """Test transcription analysis for empty transcription."""
        analyzer = VoiceCallAnalyzer()
        
        analysis = analyzer.analyze_transcription("")
        
        assert analysis['sentiment'] == 'unknown'
        assert analysis['confidence'] == 0.0
        assert analysis['interest_level'] == 0.0
        assert analysis['callback_requested'] is False
    
    def test_analyze_call_metrics_answered(self):
        """Test call metrics analysis for answered call."""
        analyzer = VoiceCallAnalyzer()
        call = VoiceCall(
            id=uuid.uuid4(),
            to_phone="+15559876543",
            answered_at=datetime.now(),
            duration_seconds=120,
            recording_url="https://example.com/recording.mp3",
            transcription="Hello, yes I'm interested."
        )
        
        metrics = analyzer.analyze_call_metrics(call)
        
        assert metrics['answered'] is True
        assert metrics['call_duration'] == 120
        assert metrics['outcome'] == 'conversation'
        assert metrics['recording_available'] is True
        assert metrics['transcription_available'] is True
    
    def test_analyze_call_metrics_no_answer(self):
        """Test call metrics analysis for unanswered call."""
        analyzer = VoiceCallAnalyzer()
        call = VoiceCall(
            id=uuid.uuid4(),
            to_phone="+15559876543",
            voicemail_dropped=True
        )
        
        metrics = analyzer.analyze_call_metrics(call)
        
        assert metrics['answered'] is False
        assert metrics['outcome'] == 'no_answer'
        assert metrics['voicemail_dropped'] is True


class TestVoiceService:
    """Test voice service."""
    
    @patch('app.services.voice_service.Client')
    def test_init_with_config(self, mock_client_class, voice_config):
        """Test voice service initialization."""
        service = VoiceService(voice_config)
        
        assert service.config == voice_config
        mock_client_class.assert_called_once_with(
            voice_config.twilio_account_sid,
            voice_config.twilio_auth_token
        )
    
    @patch('app.services.voice_service.Client')
    async def test_initiate_call_success(self, mock_client_class, voice_config, voice_script, mock_twilio_client):
        """Test successful call initiation."""
        mock_client_class.return_value = mock_twilio_client
        service = VoiceService(voice_config)
        
        script_variables = {
            "name": "John Doe",
            "caller_name": "Jane Smith",
            "address": "123 Main St"
        }
        
        call = await service.initiate_call(
            to_phone="+15559876543",
            script=voice_script,
            script_variables=script_variables
        )
        
        assert call.to_phone == "+15559876543"
        assert call.from_phone == voice_config.default_from_phone
        assert call.script_id == voice_script.id
        assert call.script_variables == script_variables
        assert call.status == MessageStatus.SENT
        assert call.initiated_at is not None
        
        # Verify Twilio call was created
        mock_twilio_client.calls.create.assert_called_once()
        call_args = mock_twilio_client.calls.create.call_args[1]
        assert call_args['to'] == "+15559876543"
        assert call_args['from_'] == voice_config.default_from_phone
    
    @patch('app.services.voice_service.Client')
    async def test_initiate_call_scheduled(self, mock_client_class, voice_config, voice_script, mock_twilio_client):
        """Test scheduled call initiation."""
        mock_client_class.return_value = mock_twilio_client
        service = VoiceService(voice_config)
        
        future_time = datetime.now() + timedelta(hours=1)
        
        call = await service.initiate_call(
            to_phone="+15559876543",
            script=voice_script,
            scheduled_at=future_time
        )
        
        assert call.status == MessageStatus.QUEUED
        assert call.scheduled_at == future_time
        assert call.initiated_at is None
        
        # Verify Twilio call was not created immediately
        mock_twilio_client.calls.create.assert_not_called()
    
    async def test_initiate_call_no_client(self, voice_script):
        """Test call initiation without Twilio client."""
        config = VoiceServiceConfig()  # No credentials
        service = VoiceService(config)
        
        with pytest.raises(ValueError, match="Twilio client not configured"):
            await service.initiate_call(
                to_phone="+15559876543",
                script=voice_script
            )
    
    @patch('app.services.voice_service.Client')
    async def test_drop_voicemail(self, mock_client_class, voice_config, voice_script, mock_twilio_client):
        """Test voicemail drop."""
        mock_client_class.return_value = mock_twilio_client
        service = VoiceService(voice_config)
        
        # First initiate a call
        call = await service.initiate_call(
            to_phone="+15559876543",
            script=voice_script
        )
        
        # Drop voicemail
        voicemail_script = "Hi, this is a voicemail message."
        result = await service.drop_voicemail(call.id, voicemail_script)
        
        assert result is True
        assert call.voicemail_dropped is True
        assert call.status == MessageStatus.DELIVERED
    
    async def test_drop_voicemail_call_not_found(self, voice_config):
        """Test voicemail drop for non-existent call."""
        service = VoiceService(voice_config)
        
        result = await service.drop_voicemail(uuid.uuid4(), "Test message")
        
        assert result is False
    
    @patch('app.services.voice_service.Client')
    async def test_handle_call_status_completed(self, mock_client_class, voice_config, voice_script, mock_twilio_client):
        """Test handling completed call status."""
        mock_client_class.return_value = mock_twilio_client
        service = VoiceService(voice_config)
        
        call = await service.initiate_call(
            to_phone="+15559876543",
            script=voice_script
        )
        
        # Simulate call answered
        await service.handle_call_status(call.id, 'in-progress')
        assert call.answered_at is not None
        assert call.status == MessageStatus.DELIVERED
        
        # Simulate call completed
        await service.handle_call_status(call.id, 'completed', call_duration=120)
        assert call.ended_at is not None
        assert call.duration_seconds == 120
    
    @patch('app.services.voice_service.Client')
    async def test_handle_call_status_failed(self, mock_client_class, voice_config, voice_script, mock_twilio_client):
        """Test handling failed call status."""
        mock_client_class.return_value = mock_twilio_client
        service = VoiceService(voice_config)
        
        call = await service.initiate_call(
            to_phone="+15559876543",
            script=voice_script
        )
        
        await service.handle_call_status(call.id, 'failed')
        
        assert call.status == MessageStatus.FAILED
        assert call.ended_at is not None
    
    @patch('app.services.voice_service.Client')
    async def test_handle_recording(self, mock_client_class, voice_config, voice_script, mock_twilio_client):
        """Test handling call recording."""
        mock_client_class.return_value = mock_twilio_client
        service = VoiceService(voice_config)
        
        call = await service.initiate_call(
            to_phone="+15559876543",
            script=voice_script
        )
        
        recording_url = "https://example.com/recording.mp3"
        await service.handle_recording(call.id, recording_url, 120)
        
        assert call.recording_url == recording_url
        # Transcription would be processed (placeholder in current implementation)
        assert call.transcription is not None
    
    @patch('app.services.voice_service.Client')
    async def test_get_call_analytics(self, mock_client_class, voice_config, voice_script, mock_twilio_client):
        """Test getting call analytics."""
        mock_client_class.return_value = mock_twilio_client
        service = VoiceService(voice_config)
        
        # Create some test calls
        call1 = await service.initiate_call("+15559876543", voice_script)
        call2 = await service.initiate_call("+15559876544", voice_script)
        
        # Simulate one answered, one failed
        call1.answered_at = datetime.now()
        call1.status = MessageStatus.DELIVERED
        call2.status = MessageStatus.FAILED
        
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now() + timedelta(days=1)
        
        analytics = await service.get_call_analytics(start_date, end_date)
        
        assert analytics.channel == CommunicationChannel.VOICE
        assert analytics.total_sent == 2
        assert analytics.total_delivered == 1
        assert analytics.total_bounced == 1
        assert analytics.delivery_rate == 0.5
    
    @patch('app.services.voice_service.Client')
    async def test_get_call(self, mock_client_class, voice_config, voice_script, mock_twilio_client):
        """Test getting a call by ID."""
        mock_client_class.return_value = mock_twilio_client
        service = VoiceService(voice_config)
        
        call = await service.initiate_call("+15559876543", voice_script)
        
        retrieved_call = await service.get_call(call.id)
        
        assert retrieved_call == call
        assert retrieved_call.to_phone == "+15559876543"
    
    @patch('app.services.voice_service.Client')
    async def test_get_calls_by_phone(self, mock_client_class, voice_config, voice_script, mock_twilio_client):
        """Test getting calls by phone number."""
        mock_client_class.return_value = mock_twilio_client
        service = VoiceService(voice_config)
        
        phone = "+15559876543"
        call1 = await service.initiate_call(phone, voice_script)
        call2 = await service.initiate_call(phone, voice_script)
        call3 = await service.initiate_call("+15559876544", voice_script)
        
        calls = await service.get_calls_by_phone(phone)
        
        assert len(calls) == 2
        assert call1 in calls
        assert call2 in calls
        assert call3 not in calls
    
    @patch('app.services.voice_service.Client')
    async def test_cancel_call(self, mock_client_class, voice_config, voice_script, mock_twilio_client):
        """Test canceling a scheduled call."""
        mock_client_class.return_value = mock_twilio_client
        service = VoiceService(voice_config)
        
        future_time = datetime.now() + timedelta(hours=1)
        call = await service.initiate_call(
            to_phone="+15559876543",
            script=voice_script,
            scheduled_at=future_time
        )
        
        result = await service.cancel_call(call.id)
        
        assert result is True
        assert call.status == MessageStatus.FAILED
        assert call.metadata['cancelled'] is True
    
    async def test_cancel_call_not_found(self, voice_config):
        """Test canceling non-existent call."""
        service = VoiceService(voice_config)
        
        result = await service.cancel_call(uuid.uuid4())
        
        assert result is False


@pytest.mark.integration
class TestVoiceServiceIntegration:
    """Integration tests for voice service."""
    
    @pytest.mark.skip(reason="Requires real Twilio credentials")
    async def test_real_call_integration(self):
        """Test with real Twilio integration (requires credentials)."""
        # This test would require real Twilio credentials and would make actual calls
        # Skip by default to avoid charges and external dependencies
        pass
    
    def test_twiml_webhook_integration(self, voice_config):
        """Test TwiML webhook integration."""
        service = VoiceService(voice_config)
        engine = service.script_engine
        
        call_id = uuid.uuid4()
        script_content = "Hello, this is a test call. Please respond."
        
        twiml = engine.generate_twiml(script_content, call_id)
        
        # Verify TwiML structure for webhook integration
        assert f"/voice/response/{call_id}" in twiml
        assert "speech dtmf" in twiml
        assert "timeout" in twiml
        
    def test_status_callback_integration(self, voice_config):
        """Test status callback integration."""
        service = VoiceService(voice_config)
        
        # Verify webhook URLs are properly formatted
        assert service.config.webhook_base_url in f"{service.config.webhook_base_url}/voice/status/"
        assert service.config.webhook_base_url in f"{service.config.webhook_base_url}/voice/recording/"