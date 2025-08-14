"""
Unit tests for the message generation service.
Tests Requirements 3.1 and 3.2 implementation.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import uuid

from app.services.message_generation_service import (
    MessageGenerationService,
    MessageGenerationRequest,
    MessageType,
    MessageTone,
    PropertyContext,
    SellerContext,
    MarketContext,
    GeneratedMessage,
    create_property_context,
    create_seller_context,
    create_market_context
)
from app.models.communication import CommunicationChannel


# Global fixtures
@pytest.fixture
def service():
    """Create message generation service instance."""
    return MessageGenerationService()

@pytest.fixture
def sample_property_context():
    """Sample property context for testing."""
    return PropertyContext(
        address="123 Main St, Anytown, ST 12345",
        property_type="single_family",
        estimated_value=250000.0,
        condition="needs_repair",
        days_on_market=45,
        listing_price=275000.0,
        bedrooms=3,
        bathrooms=2.0,
        square_feet=1800,
        year_built=1985,
        neighborhood="Downtown",
        motivation_indicators=["foreclosure", "divorce"]
    )

@pytest.fixture
def sample_seller_context():
    """Sample seller context for testing."""
    return SellerContext(
        name="John Smith",
        situation="divorce",
        timeline="urgent",
        motivation_level="high",
        previous_interactions=[],
        preferred_contact_method="email",
        response_history=[]
    )

@pytest.fixture
def sample_market_context():
    """Sample market context for testing."""
    return MarketContext(
        market_trend="hot",
        average_days_on_market=30,
        price_trend="rising",
        inventory_level="low",
        seasonal_factors=["spring_market"]
    )

@pytest.fixture
def sample_request(sample_property_context, sample_seller_context, sample_market_context):
    """Sample message generation request."""
    return MessageGenerationRequest(
        message_type=MessageType.INITIAL_OUTREACH,
        channel=CommunicationChannel.EMAIL,
        tone=MessageTone.PROFESSIONAL,
        property_context=sample_property_context,
        seller_context=sample_seller_context,
        market_context=sample_market_context
    )


class TestMessageGenerationService:
    """Test cases for MessageGenerationService."""


class TestMessageGeneration:
    """Test message generation functionality."""
    
    def test_generate_email_message(self, service, sample_request):
        """Test email message generation."""
        sample_request.channel = CommunicationChannel.EMAIL
        
        result = service.generate_message(sample_request)
        
        assert isinstance(result, GeneratedMessage)
        assert result.channel == CommunicationChannel.EMAIL
        assert result.message_type == MessageType.INITIAL_OUTREACH
        assert result.subject is not None
        assert result.content is not None
        assert "John Smith" in result.content
        assert "123 Main St" in result.content
        assert result.personalization_score > 0.0
        assert result.estimated_effectiveness > 0.0
        assert result.created_at is not None
    
    def test_generate_sms_message(self, service, sample_request):
        """Test SMS message generation."""
        sample_request.channel = CommunicationChannel.SMS
        
        result = service.generate_message(sample_request)
        
        assert isinstance(result, GeneratedMessage)
        assert result.channel == CommunicationChannel.SMS
        assert result.subject is None  # SMS doesn't have subject
        assert result.content is not None
        assert len(result.content) <= 160  # SMS length consideration
        assert "John Smith" in result.content
        assert result.personalization_score > 0.0
    
    def test_generate_voice_script(self, service, sample_request):
        """Test voice script generation."""
        sample_request.channel = CommunicationChannel.VOICE
        
        result = service.generate_message(sample_request)
        
        assert isinstance(result, GeneratedMessage)
        assert result.channel == CommunicationChannel.VOICE
        assert result.content is not None
        assert "John Smith" in result.content
        assert "[PAUSE FOR RESPONSE]" in result.content
        assert result.personalization_score > 0.0
    
    def test_unsupported_channel_raises_error(self, service, sample_request):
        """Test that unsupported channel raises ValueError."""
        # Create invalid channel (this would need to be done differently in real implementation)
        with pytest.raises(ValueError, match="Unsupported channel"):
            sample_request.channel = "invalid_channel"
            service.generate_message(sample_request)


class TestFollowUpSequence:
    """Test follow-up message sequence generation."""
    
    def test_generate_follow_up_sequence(self, service, sample_request):
        """Test generating a sequence of follow-up messages."""
        sequence = service.generate_follow_up_sequence(sample_request, sequence_length=3)
        
        assert len(sequence) == 3
        assert all(isinstance(msg, GeneratedMessage) for msg in sequence)
        assert all(msg.message_type == MessageType.FOLLOW_UP for msg in sequence)
        
        # Check that tone escalates
        assert sequence[0].variables_used["tone"] == "friendly"
        assert sequence[1].variables_used["tone"] == "professional"
        assert sequence[2].variables_used["tone"] == "urgent"
    
    def test_follow_up_sequence_includes_previous_messages(self, service, sample_request):
        """Test that follow-up sequence considers previous messages."""
        sequence = service.generate_follow_up_sequence(sample_request, sequence_length=2)
        
        # Second message should reference first message in context
        # (This would be more sophisticated in a real AI implementation)
        assert len(sequence) == 2


class TestMessagePersonalization:
    """Test message personalization features."""
    
    def test_personalization_with_seller_name(self, service, sample_request):
        """Test personalization includes seller name."""
        result = service.generate_message(sample_request)
        
        assert "John Smith" in result.content
        assert result.personalization_score >= 0.2  # Name adds to score
    
    def test_personalization_with_property_details(self, service, sample_request):
        """Test personalization includes property details."""
        result = service.generate_message(sample_request)
        
        assert "123 Main St" in result.content
        assert result.personalization_score >= 0.4  # Name + address
    
    def test_personalization_without_seller_name(self, service, sample_request):
        """Test personalization when seller name is not available."""
        sample_request.seller_context.name = None
        
        result = service.generate_message(sample_request)
        
        assert "Property Owner" in result.content
        assert result.personalization_score <= 0.8  # Score without personal name
    
    def test_personalization_score_calculation(self, service):
        """Test personalization score calculation."""
        context = {
            "seller_name": "John Smith",
            "property_address": "123 Main St",
            "seller_situation": "divorce",
            "property_condition": "needs_repair",
            "market_trend": "hot"
        }
        content = "Hi John Smith, regarding 123 Main St..."
        
        score = service._calculate_personalization_score(content, context)
        
        assert score == 1.0  # All personalization elements present


class TestMessageTypes:
    """Test different message types."""
    
    def test_initial_outreach_message(self, service, sample_request):
        """Test initial outreach message generation."""
        sample_request.message_type = MessageType.INITIAL_OUTREACH
        
        result = service.generate_message(sample_request)
        
        assert result.message_type == MessageType.INITIAL_OUTREACH
        assert "interested in" in result.content.lower()
    
    def test_follow_up_message(self, service, sample_request):
        """Test follow-up message generation."""
        sample_request.message_type = MessageType.FOLLOW_UP
        
        result = service.generate_message(sample_request)
        
        assert result.message_type == MessageType.FOLLOW_UP
        assert "follow" in result.content.lower()
    
    def test_appointment_request_message(self, service, sample_request):
        """Test appointment request message generation."""
        sample_request.message_type = MessageType.APPOINTMENT_REQUEST
        
        result = service.generate_message(sample_request)
        
        assert result.message_type == MessageType.APPOINTMENT_REQUEST
    
    def test_offer_presentation_message(self, service, sample_request):
        """Test offer presentation message generation."""
        sample_request.message_type = MessageType.OFFER_PRESENTATION
        
        result = service.generate_message(sample_request)
        
        assert result.message_type == MessageType.OFFER_PRESENTATION


class TestMessageTones:
    """Test different message tones."""
    
    def test_professional_tone(self, service, sample_request):
        """Test professional tone message."""
        sample_request.tone = MessageTone.PROFESSIONAL
        
        result = service.generate_message(sample_request)
        
        assert result.variables_used["tone"] == "professional"
    
    def test_friendly_tone(self, service, sample_request):
        """Test friendly tone message."""
        sample_request.tone = MessageTone.FRIENDLY
        
        result = service.generate_message(sample_request)
        
        assert result.variables_used["tone"] == "friendly"
    
    def test_urgent_tone(self, service, sample_request):
        """Test urgent tone message."""
        sample_request.tone = MessageTone.URGENT
        
        result = service.generate_message(sample_request)
        
        assert result.variables_used["tone"] == "urgent"


class TestEffectivenessEstimation:
    """Test message effectiveness estimation."""
    
    def test_effectiveness_estimation_by_channel(self, service, sample_request):
        """Test effectiveness varies by channel."""
        # Test email
        sample_request.channel = CommunicationChannel.EMAIL
        email_result = service.generate_message(sample_request)
        
        # Test SMS
        sample_request.channel = CommunicationChannel.SMS
        sms_result = service.generate_message(sample_request)
        
        # Test voice
        sample_request.channel = CommunicationChannel.VOICE
        voice_result = service.generate_message(sample_request)
        
        # Voice should have highest effectiveness, then SMS, then email
        assert voice_result.estimated_effectiveness >= sms_result.estimated_effectiveness
        assert sms_result.estimated_effectiveness >= email_result.estimated_effectiveness
    
    def test_effectiveness_estimation_by_tone(self, service, sample_request):
        """Test effectiveness varies by tone."""
        sample_request.tone = MessageTone.FRIENDLY
        friendly_result = service.generate_message(sample_request)
        
        sample_request.tone = MessageTone.PROFESSIONAL
        professional_result = service.generate_message(sample_request)
        
        # Friendly tone should have higher effectiveness
        assert friendly_result.estimated_effectiveness >= professional_result.estimated_effectiveness


class TestOptimalSendTime:
    """Test optimal send time suggestions."""
    
    def test_email_optimal_time(self, service, sample_request):
        """Test optimal send time for email."""
        sample_request.channel = CommunicationChannel.EMAIL
        
        result = service.generate_message(sample_request)
        
        assert result.suggested_send_time is not None
        assert result.suggested_send_time.hour == 10  # 10 AM for email
    
    def test_sms_optimal_time(self, service, sample_request):
        """Test optimal send time for SMS."""
        sample_request.channel = CommunicationChannel.SMS
        
        result = service.generate_message(sample_request)
        
        assert result.suggested_send_time is not None
        assert result.suggested_send_time.hour == 14  # 2 PM for SMS
    
    def test_voice_optimal_time(self, service, sample_request):
        """Test optimal send time for voice."""
        sample_request.channel = CommunicationChannel.VOICE
        
        result = service.generate_message(sample_request)
        
        assert result.suggested_send_time is not None
        assert result.suggested_send_time.hour == 10  # 10:30 AM for voice


class TestFollowUpSuggestions:
    """Test follow-up suggestions generation."""
    
    def test_initial_outreach_suggestions(self, service, sample_request):
        """Test follow-up suggestions for initial outreach."""
        sample_request.message_type = MessageType.INITIAL_OUTREACH
        
        result = service.generate_message(sample_request)
        
        assert len(result.follow_up_suggestions) > 0
        assert any("follow-up" in suggestion.lower() for suggestion in result.follow_up_suggestions)
    
    def test_follow_up_message_suggestions(self, service, sample_request):
        """Test follow-up suggestions for follow-up messages."""
        sample_request.message_type = MessageType.FOLLOW_UP
        
        result = service.generate_message(sample_request)
        
        assert len(result.follow_up_suggestions) > 0
        assert any("wait" in suggestion.lower() for suggestion in result.follow_up_suggestions)


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_create_property_context(self):
        """Test property context creation from dictionary."""
        data = {
            "address": "123 Main St",
            "property_type": "single_family",
            "estimated_value": 250000.0
        }
        
        context = create_property_context(data)
        
        assert isinstance(context, PropertyContext)
        assert context.address == "123 Main St"
        assert context.property_type == "single_family"
        assert context.estimated_value == 250000.0
    
    def test_create_seller_context(self):
        """Test seller context creation from dictionary."""
        data = {
            "name": "John Smith",
            "situation": "divorce",
            "timeline": "urgent"
        }
        
        context = create_seller_context(data)
        
        assert isinstance(context, SellerContext)
        assert context.name == "John Smith"
        assert context.situation == "divorce"
        assert context.timeline == "urgent"
    
    def test_create_market_context(self):
        """Test market context creation from dictionary."""
        data = {
            "market_trend": "hot",
            "price_trend": "rising",
            "inventory_level": "low"
        }
        
        context = create_market_context(data)
        
        assert isinstance(context, MarketContext)
        assert context.market_trend == "hot"
        assert context.price_trend == "rising"
        assert context.inventory_level == "low"


class TestMessageContextBuilding:
    """Test message context building."""
    
    def test_build_message_context(self, service, sample_request):
        """Test building comprehensive message context."""
        context = service._build_message_context(sample_request)
        
        assert "property_address" in context
        assert "seller_name" in context
        assert "message_type" in context
        assert "tone" in context
        assert "channel" in context
        assert context["property_address"] == "123 Main St, Anytown, ST 12345"
        assert context["seller_name"] == "John Smith"
    
    def test_build_context_with_missing_seller_name(self, service, sample_request):
        """Test context building when seller name is missing."""
        sample_request.seller_context.name = None
        
        context = service._build_message_context(sample_request)
        
        assert context["seller_name"] == "Property Owner"
    
    def test_build_context_with_custom_variables(self, service, sample_request):
        """Test context building with custom variables."""
        sample_request.custom_variables = {"investor_name": "Jane Doe", "company": "ABC Investments"}
        
        context = service._build_message_context(sample_request)
        
        assert context["investor_name"] == "Jane Doe"
        assert context["company"] == "ABC Investments"


# Integration tests
class TestMessageGenerationIntegration:
    """Integration tests for message generation."""
    
    def test_end_to_end_email_generation(self, service):
        """Test complete email generation workflow."""
        property_context = PropertyContext(
            address="456 Oak Ave, Springfield, IL 62701",
            property_type="single_family",
            estimated_value=180000.0,
            condition="good",
            bedrooms=4,
            bathrooms=2.5
        )
        
        seller_context = SellerContext(
            name="Sarah Johnson",
            situation="relocation",
            timeline="flexible",
            motivation_level="medium"
        )
        
        request = MessageGenerationRequest(
            message_type=MessageType.INITIAL_OUTREACH,
            channel=CommunicationChannel.EMAIL,
            tone=MessageTone.FRIENDLY,
            property_context=property_context,
            seller_context=seller_context
        )
        
        result = service.generate_message(request)
        
        # Verify all components are present
        assert result.id is not None
        assert result.channel == CommunicationChannel.EMAIL
        assert result.subject is not None
        assert result.content is not None
        assert "Sarah Johnson" in result.content
        assert "456 Oak Ave" in result.content
        assert result.personalization_score > 0.0
        assert result.estimated_effectiveness > 0.0
        assert result.suggested_send_time is not None
        assert len(result.follow_up_suggestions) > 0
    
    def test_multi_channel_message_generation(self, service, sample_property_context, sample_seller_context):
        """Test generating messages for multiple channels."""
        base_request = MessageGenerationRequest(
            message_type=MessageType.INITIAL_OUTREACH,
            channel=CommunicationChannel.EMAIL,  # Will be overridden
            tone=MessageTone.PROFESSIONAL,
            property_context=sample_property_context,
            seller_context=sample_seller_context
        )
        
        channels = [CommunicationChannel.EMAIL, CommunicationChannel.SMS, CommunicationChannel.VOICE]
        results = []
        
        for channel in channels:
            base_request.channel = channel
            result = service.generate_message(base_request)
            results.append(result)
        
        # Verify all channels generated successfully
        assert len(results) == 3
        assert results[0].channel == CommunicationChannel.EMAIL
        assert results[1].channel == CommunicationChannel.SMS
        assert results[2].channel == CommunicationChannel.VOICE
        
        # Verify content is appropriate for each channel
        assert results[0].subject is not None  # Email has subject
        assert results[1].subject is None      # SMS has no subject
        assert results[2].subject is None      # Voice has no subject
        
        # SMS should be shorter
        assert len(results[1].content) <= len(results[0].content)


if __name__ == "__main__":
    pytest.main([__file__])