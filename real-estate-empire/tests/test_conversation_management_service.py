"""
Unit tests for the conversation management service.
Tests Requirements 3.3, 3.4, and 3.5 implementation.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import uuid

from app.services.conversation_management_service import (
    ConversationManagementService,
    Conversation,
    ConversationMessage,
    ConversationStatus,
    ConversationPriority,
    NextActionType,
    NextAction,
    ConversationContext,
    ConversationSummary,
    merge_conversations,
    get_conversation_analytics
)
from app.services.response_analysis_service import ResponseAnalysisService
from app.models.communication import CommunicationChannel


# Global fixtures
@pytest.fixture
def service():
    """Create conversation management service instance."""
    return ConversationManagementService()


@pytest.fixture
def mock_response_analysis_service():
    """Create mock response analysis service."""
    mock_service = Mock(spec=ResponseAnalysisService)
    mock_result = Mock()
    mock_result.overall_interest_level = 0.7
    mock_result.response_urgency.value = "high"
    mock_result.intent_analysis.primary_intent.value = "interested"
    mock_result.question_extraction.questions = ["How much?"]
    mock_result.objection_analysis.objections_detected = []
    mock_result.sentiment_analysis.sentiment_score = 0.5
    mock_result.sentiment_analysis.sentiment_type.value = "positive"
    mock_result.sentiment_analysis.key_phrases = ["interested"]
    mock_service.analyze_response.return_value = mock_result
    return mock_service


@pytest.fixture
def sample_conversation(service):
    """Create a sample conversation."""
    context = ConversationContext(
        conversation_id=uuid.uuid4(),
        contact_name="John Smith",
        contact_email="john@example.com",
        property_address="123 Main St",
        last_updated=datetime.now()
    )
    
    return service.create_conversation(
        contact_id=uuid.uuid4(),
        subject="Property Inquiry - 123 Main St",
        context=context
    )


class TestConversationManagementService:
    """Test cases for ConversationManagementService."""
    
    def test_service_initialization(self, service):
        """Test service initializes correctly."""
        assert service is not None
        assert service.response_analysis_service is not None
        assert service.conversations == {}


class TestConversationCreation:
    """Test conversation creation functionality."""
    
    def test_create_conversation_basic(self, service):
        """Test basic conversation creation."""
        contact_id = uuid.uuid4()
        subject = "Test Conversation"
        
        conversation = service.create_conversation(
            contact_id=contact_id,
            subject=subject
        )
        
        assert conversation.id is not None
        assert conversation.contact_id == contact_id
        assert conversation.subject == subject
        assert conversation.status == ConversationStatus.ACTIVE
        assert conversation.priority == ConversationPriority.MEDIUM
        assert conversation.message_count == 0
        assert len(conversation.messages) == 0
        assert conversation.id in service.conversations
    
    def test_create_conversation_with_context(self, service):
        """Test conversation creation with context."""
        contact_id = uuid.uuid4()
        context = ConversationContext(
            conversation_id=uuid.uuid4(),
            contact_name="Jane Doe",
            contact_email="jane@example.com",
            property_address="456 Oak Ave",
            last_updated=datetime.now()
        )
        
        conversation = service.create_conversation(
            contact_id=contact_id,
            context=context
        )
        
        assert conversation.context is not None
        assert conversation.context.contact_name == "Jane Doe"
        assert conversation.context.contact_email == "jane@example.com"
        assert conversation.context.property_address == "456 Oak Ave"
    
    def test_create_conversation_without_context(self, service):
        """Test conversation creation without explicit context."""
        conversation = service.create_conversation()
        
        assert conversation.context is not None
        assert conversation.context.conversation_id == conversation.id


class TestMessageManagement:
    """Test message management functionality."""
    
    def test_add_outbound_message(self, service, sample_conversation):
        """Test adding an outbound message."""
        message = service.add_message(
            conversation_id=sample_conversation.id,
            channel=CommunicationChannel.EMAIL,
            direction="outbound",
            content="Hello, I'm interested in your property.",
            subject="Property Inquiry",
            sender="investor@example.com",
            recipient="owner@example.com"
        )
        
        assert message.id is not None
        assert message.conversation_id == sample_conversation.id
        assert message.channel == CommunicationChannel.EMAIL
        assert message.direction == "outbound"
        assert message.content == "Hello, I'm interested in your property."
        assert message.subject == "Property Inquiry"
        assert message.analysis_result is None  # No analysis for outbound
        
        # Check conversation updates
        updated_conversation = service.get_conversation(sample_conversation.id)
        assert updated_conversation.message_count == 1
        assert len(updated_conversation.messages) == 1
        assert CommunicationChannel.EMAIL in updated_conversation.channels_used
        assert updated_conversation.last_message_at is not None
    
    def test_add_inbound_message_with_analysis(self, service, sample_conversation):
        """Test adding an inbound message with analysis."""
        # Mock the response analysis service
        service.response_analysis_service = Mock()
        mock_result = Mock()
        mock_result.overall_interest_level = 0.8
        mock_result.response_urgency.value = "high"
        mock_result.intent_analysis.primary_intent.value = "interested"
        mock_result.question_extraction.questions = ["When can we meet?"]
        mock_result.objection_analysis.objections_detected = []
        mock_result.sentiment_analysis.sentiment_score = 0.6
        mock_result.sentiment_analysis.sentiment_type.value = "positive"
        mock_result.sentiment_analysis.key_phrases = ["interested", "excited"]
        service.response_analysis_service.analyze_response.return_value = mock_result
        
        message = service.add_message(
            conversation_id=sample_conversation.id,
            channel=CommunicationChannel.SMS,
            direction="inbound",
            content="Yes, I'm interested! When can we meet?",
            sender="555-1234"
        )
        
        assert message.analysis_result is not None
        assert message.analysis_result.overall_interest_level == 0.8
        
        # Check that analysis was called
        service.response_analysis_service.analyze_response.assert_called_once()
        
        # Check conversation updates
        updated_conversation = service.get_conversation(sample_conversation.id)
        assert updated_conversation.message_count == 1
        assert CommunicationChannel.SMS in updated_conversation.channels_used
        assert len(updated_conversation.next_actions) > 0  # Should generate actions
    
    def test_add_message_to_nonexistent_conversation(self, service):
        """Test adding message to non-existent conversation raises error."""
        fake_id = uuid.uuid4()
        
        with pytest.raises(ValueError, match=f"Conversation {fake_id} not found"):
            service.add_message(
                conversation_id=fake_id,
                channel=CommunicationChannel.EMAIL,
                direction="outbound",
                content="Test message"
            )
    
    def test_multiple_channels_tracking(self, service, sample_conversation):
        """Test tracking of multiple channels used."""
        # Add email message
        service.add_message(
            conversation_id=sample_conversation.id,
            channel=CommunicationChannel.EMAIL,
            direction="outbound",
            content="Email message"
        )
        
        # Add SMS message
        service.add_message(
            conversation_id=sample_conversation.id,
            channel=CommunicationChannel.SMS,
            direction="inbound",
            content="SMS response"
        )
        
        # Add voice message
        service.add_message(
            conversation_id=sample_conversation.id,
            channel=CommunicationChannel.VOICE,
            direction="outbound",
            content="Voice call transcript"
        )
        
        conversation = service.get_conversation(sample_conversation.id)
        assert len(conversation.channels_used) == 3
        assert CommunicationChannel.EMAIL in conversation.channels_used
        assert CommunicationChannel.SMS in conversation.channels_used
        assert CommunicationChannel.VOICE in conversation.channels_used


class TestConversationRetrieval:
    """Test conversation retrieval functionality."""
    
    def test_get_conversation_exists(self, service, sample_conversation):
        """Test getting an existing conversation."""
        retrieved = service.get_conversation(sample_conversation.id)
        
        assert retrieved is not None
        assert retrieved.id == sample_conversation.id
        assert retrieved.subject == sample_conversation.subject
    
    def test_get_conversation_not_exists(self, service):
        """Test getting a non-existent conversation."""
        fake_id = uuid.uuid4()
        retrieved = service.get_conversation(fake_id)
        
        assert retrieved is None
    
    def test_get_conversations_by_contact(self, service):
        """Test getting conversations by contact ID."""
        contact_id = uuid.uuid4()
        
        # Create multiple conversations for the same contact
        conv1 = service.create_conversation(contact_id=contact_id, subject="Conv 1")
        conv2 = service.create_conversation(contact_id=contact_id, subject="Conv 2")
        conv3 = service.create_conversation(contact_id=uuid.uuid4(), subject="Conv 3")  # Different contact
        
        conversations = service.get_conversations_by_contact(contact_id)
        
        assert len(conversations) == 2
        assert conv1 in conversations
        assert conv2 in conversations
        assert conv3 not in conversations


class TestConversationSearch:
    """Test conversation search functionality."""
    
    def test_search_by_status(self, service):
        """Test searching conversations by status."""
        # Create conversations with different statuses
        conv1 = service.create_conversation(subject="Active Conv")
        conv2 = service.create_conversation(subject="Closed Conv")
        service.update_conversation_status(conv2.id, ConversationStatus.CLOSED)
        
        active_conversations = service.search_conversations(status=ConversationStatus.ACTIVE)
        closed_conversations = service.search_conversations(status=ConversationStatus.CLOSED)
        
        assert len(active_conversations) == 1
        assert conv1 in active_conversations
        
        assert len(closed_conversations) == 1
        assert conv2 in closed_conversations
    
    def test_search_by_priority(self, service):
        """Test searching conversations by priority."""
        conv1 = service.create_conversation(subject="High Priority")
        conv2 = service.create_conversation(subject="Low Priority")
        
        service.update_conversation_priority(conv1.id, ConversationPriority.HIGH)
        service.update_conversation_priority(conv2.id, ConversationPriority.LOW)
        
        high_priority = service.search_conversations(priority=ConversationPriority.HIGH)
        low_priority = service.search_conversations(priority=ConversationPriority.LOW)
        
        assert len(high_priority) == 1
        assert conv1 in high_priority
        
        assert len(low_priority) == 1
        assert conv2 in low_priority
    
    def test_search_by_channel(self, service):
        """Test searching conversations by channel."""
        conv1 = service.create_conversation(subject="Email Conv")
        conv2 = service.create_conversation(subject="SMS Conv")
        
        # Add messages with different channels
        service.add_message(conv1.id, CommunicationChannel.EMAIL, "outbound", "Email message")
        service.add_message(conv2.id, CommunicationChannel.SMS, "outbound", "SMS message")
        
        email_conversations = service.search_conversations(channel=CommunicationChannel.EMAIL)
        sms_conversations = service.search_conversations(channel=CommunicationChannel.SMS)
        
        assert len(email_conversations) == 1
        assert conv1 in email_conversations
        
        assert len(sms_conversations) == 1
        assert conv2 in sms_conversations
    
    def test_search_by_text_query(self, service):
        """Test searching conversations by text query."""
        conv1 = service.create_conversation(subject="Property on Main Street")
        conv2 = service.create_conversation(subject="House on Oak Avenue")
        
        # Add messages with different content
        service.add_message(conv1.id, CommunicationChannel.EMAIL, "outbound", "Interested in Main Street property")
        service.add_message(conv2.id, CommunicationChannel.EMAIL, "outbound", "Oak Avenue house inquiry")
        
        main_street_results = service.search_conversations(query="Main Street")
        oak_results = service.search_conversations(query="Oak")
        
        assert len(main_street_results) == 1
        assert conv1 in main_street_results
        
        assert len(oak_results) == 1
        assert conv2 in oak_results
    
    def test_search_by_date_range(self, service):
        """Test searching conversations by date range."""
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        
        # Create conversation
        conv = service.create_conversation(subject="Test Conv")
        
        # Search with date range that includes the conversation
        results_include = service.search_conversations(date_from=yesterday, date_to=tomorrow)
        assert conv in results_include
        
        # Search with date range that excludes the conversation
        results_exclude = service.search_conversations(date_from=tomorrow)
        assert conv not in results_exclude


class TestConversationUpdates:
    """Test conversation update functionality."""
    
    def test_update_conversation_status(self, service, sample_conversation):
        """Test updating conversation status."""
        original_updated_at = sample_conversation.updated_at
        
        success = service.update_conversation_status(
            sample_conversation.id, 
            ConversationStatus.CLOSED
        )
        
        assert success is True
        
        updated_conversation = service.get_conversation(sample_conversation.id)
        assert updated_conversation.status == ConversationStatus.CLOSED
        assert updated_conversation.updated_at >= original_updated_at
    
    def test_update_nonexistent_conversation_status(self, service):
        """Test updating status of non-existent conversation."""
        fake_id = uuid.uuid4()
        success = service.update_conversation_status(fake_id, ConversationStatus.CLOSED)
        
        assert success is False
    
    def test_update_conversation_priority(self, service, sample_conversation):
        """Test updating conversation priority."""
        original_updated_at = sample_conversation.updated_at
        
        success = service.update_conversation_priority(
            sample_conversation.id, 
            ConversationPriority.HIGH
        )
        
        assert success is True
        
        updated_conversation = service.get_conversation(sample_conversation.id)
        assert updated_conversation.priority == ConversationPriority.HIGH
        assert updated_conversation.updated_at >= original_updated_at
    
    def test_update_nonexistent_conversation_priority(self, service):
        """Test updating priority of non-existent conversation."""
        fake_id = uuid.uuid4()
        success = service.update_conversation_priority(fake_id, ConversationPriority.HIGH)
        
        assert success is False


class TestConversationMetrics:
    """Test conversation metrics functionality."""
    
    def test_get_conversation_metrics_basic(self, service, sample_conversation):
        """Test getting basic conversation metrics."""
        # Add some messages
        service.add_message(sample_conversation.id, CommunicationChannel.EMAIL, "outbound", "Hello")
        service.add_message(sample_conversation.id, CommunicationChannel.SMS, "inbound", "Hi there")
        
        metrics = service.get_conversation_metrics(sample_conversation.id)
        
        assert metrics is not None
        assert metrics["message_count"] == 2
        assert metrics["channels_used"] == 2
        assert metrics["duration_days"] >= 0
        assert "last_activity" in metrics
    
    def test_get_metrics_nonexistent_conversation(self, service):
        """Test getting metrics for non-existent conversation."""
        fake_id = uuid.uuid4()
        metrics = service.get_conversation_metrics(fake_id)
        
        assert metrics is None
    
    def test_response_time_calculation(self, service, sample_conversation):
        """Test response time calculation in metrics."""
        now = datetime.now()
        
        # Add outbound message
        outbound_msg = service.add_message(
            sample_conversation.id, 
            CommunicationChannel.EMAIL, 
            "outbound", 
            "Hello"
        )
        outbound_msg.timestamp = now
        
        # Add inbound response 2 hours later
        inbound_msg = service.add_message(
            sample_conversation.id, 
            CommunicationChannel.EMAIL, 
            "inbound", 
            "Hi back"
        )
        inbound_msg.timestamp = now + timedelta(hours=2)
        
        metrics = service.get_conversation_metrics(sample_conversation.id)
        
        # Should calculate response time (though exact value depends on implementation)
        assert "avg_response_time_hours" in metrics


class TestNextActions:
    """Test next actions functionality."""
    
    def test_next_actions_generation_interested(self, service, sample_conversation):
        """Test next actions generation for interested response."""
        # Mock the response analysis service
        service.response_analysis_service = Mock()
        mock_result = Mock()
        mock_result.overall_interest_level = 0.8
        mock_result.response_urgency.value = "high"
        mock_result.intent_analysis.primary_intent.value = "interested"
        mock_result.question_extraction.questions = []
        mock_result.objection_analysis.objections_detected = []
        mock_result.sentiment_analysis.sentiment_score = 0.6
        mock_result.sentiment_analysis.sentiment_type.value = "positive"
        mock_result.sentiment_analysis.key_phrases = ["interested"]
        service.response_analysis_service.analyze_response.return_value = mock_result
        
        # Add inbound message
        service.add_message(
            sample_conversation.id,
            CommunicationChannel.EMAIL,
            "inbound",
            "Yes, I'm very interested!"
        )
        
        conversation = service.get_conversation(sample_conversation.id)
        assert len(conversation.next_actions) > 0
        
        # Should have a schedule call action
        schedule_actions = [
            action for action in conversation.next_actions 
            if action.action_type == NextActionType.SCHEDULE_CALL
        ]
        assert len(schedule_actions) > 0
    
    def test_next_actions_generation_questions(self, service, sample_conversation):
        """Test next actions generation for messages with questions."""
        # Mock the response analysis service
        service.response_analysis_service = Mock()
        mock_result = Mock()
        mock_result.overall_interest_level = 0.6
        mock_result.response_urgency.value = "medium"
        mock_result.intent_analysis.primary_intent.value = "needs_more_info"
        mock_result.question_extraction.questions = ["How much?", "When?"]
        mock_result.objection_analysis.objections_detected = []
        mock_result.sentiment_analysis.sentiment_score = 0.3
        mock_result.sentiment_analysis.sentiment_type.value = "neutral"
        mock_result.sentiment_analysis.key_phrases = []
        service.response_analysis_service.analyze_response.return_value = mock_result
        
        # Add inbound message with questions
        service.add_message(
            sample_conversation.id,
            CommunicationChannel.EMAIL,
            "inbound",
            "How much are you offering? When would you close?"
        )
        
        conversation = service.get_conversation(sample_conversation.id)
        
        # Should have respond action for questions
        respond_actions = [
            action for action in conversation.next_actions 
            if action.action_type == NextActionType.RESPOND and 
               action.context and "questions" in action.context
        ]
        assert len(respond_actions) > 0
    
    def test_complete_action(self, service, sample_conversation):
        """Test completing an action."""
        # Add message to generate actions
        service.response_analysis_service = Mock()
        mock_result = Mock()
        mock_result.overall_interest_level = 0.5
        mock_result.response_urgency.value = "medium"
        mock_result.intent_analysis.primary_intent.value = "needs_more_info"
        mock_result.question_extraction.questions = []
        mock_result.objection_analysis.objections_detected = []
        mock_result.sentiment_analysis.sentiment_score = 0.0
        mock_result.sentiment_analysis.sentiment_type.value = "neutral"
        mock_result.sentiment_analysis.key_phrases = []
        service.response_analysis_service.analyze_response.return_value = mock_result
        
        service.add_message(
            sample_conversation.id,
            CommunicationChannel.EMAIL,
            "inbound",
            "Tell me more"
        )
        
        conversation = service.get_conversation(sample_conversation.id)
        action = conversation.next_actions[0]
        
        # Complete the action
        success = service.complete_action(action.id)
        assert success is True
        assert action.completed is True
    
    def test_complete_nonexistent_action(self, service):
        """Test completing non-existent action."""
        fake_id = uuid.uuid4()
        success = service.complete_action(fake_id)
        assert success is False
    
    def test_get_pending_actions(self, service, sample_conversation):
        """Test getting pending actions."""
        # Add message to generate actions
        service.response_analysis_service = Mock()
        mock_result = Mock()
        mock_result.overall_interest_level = 0.7
        mock_result.response_urgency.value = "high"
        mock_result.intent_analysis.primary_intent.value = "interested"
        mock_result.question_extraction.questions = []
        mock_result.objection_analysis.objections_detected = []
        mock_result.sentiment_analysis.sentiment_score = 0.5
        mock_result.sentiment_analysis.sentiment_type.value = "positive"
        mock_result.sentiment_analysis.key_phrases = []
        service.response_analysis_service.analyze_response.return_value = mock_result
        
        service.add_message(
            sample_conversation.id,
            CommunicationChannel.EMAIL,
            "inbound",
            "I'm interested"
        )
        
        pending_actions = service.get_pending_actions()
        assert len(pending_actions) > 0
        
        # Test filtering by priority
        high_priority_actions = service.get_pending_actions(priority=ConversationPriority.HIGH)
        assert len(high_priority_actions) > 0


class TestConversationSummary:
    """Test conversation summary functionality."""
    
    def test_summary_creation(self, service, sample_conversation):
        """Test that summary is created when messages are added."""
        # Mock the response analysis service
        service.response_analysis_service = Mock()
        mock_result = Mock()
        mock_result.overall_interest_level = 0.6
        mock_result.response_urgency.value = "medium"
        mock_result.intent_analysis.primary_intent.value = "needs_more_info"
        mock_result.question_extraction.questions = ["How much?"]
        mock_result.objection_analysis.objections_detected = []
        mock_result.sentiment_analysis.sentiment_score = 0.3
        mock_result.sentiment_analysis.sentiment_type.value = "neutral"
        mock_result.sentiment_analysis.key_phrases = []
        service.response_analysis_service.analyze_response.return_value = mock_result
        
        # Add message
        service.add_message(
            sample_conversation.id,
            CommunicationChannel.EMAIL,
            "inbound",
            "How much are you offering?"
        )
        
        conversation = service.get_conversation(sample_conversation.id)
        assert conversation.summary is not None
        assert len(conversation.summary.questions_asked) > 0


class TestArchiving:
    """Test conversation archiving functionality."""
    
    def test_archive_old_conversations(self, service):
        """Test archiving old closed conversations."""
        # Create old closed conversation
        old_conv = service.create_conversation(subject="Old Conversation")
        service.update_conversation_status(old_conv.id, ConversationStatus.CLOSED)
        
        # Manually set old date
        old_conv.updated_at = datetime.now() - timedelta(days=100)
        
        # Create recent closed conversation
        recent_conv = service.create_conversation(subject="Recent Conversation")
        service.update_conversation_status(recent_conv.id, ConversationStatus.CLOSED)
        
        # Archive conversations older than 90 days
        archived_count = service.archive_old_conversations(days_old=90)
        
        assert archived_count == 1
        assert service.get_conversation(old_conv.id).status == ConversationStatus.ARCHIVED
        assert service.get_conversation(recent_conv.id).status == ConversationStatus.CLOSED


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_merge_conversations(self, service):
        """Test merging two conversations."""
        # Create two conversations
        conv1 = service.create_conversation(subject="Primary Conversation")
        conv2 = service.create_conversation(subject="Secondary Conversation")
        
        # Add messages to both
        service.add_message(conv1.id, CommunicationChannel.EMAIL, "outbound", "Message 1")
        service.add_message(conv2.id, CommunicationChannel.SMS, "inbound", "Message 2")
        
        # Merge conversations
        success = merge_conversations(service, conv1.id, conv2.id)
        
        assert success is True
        
        # Check primary conversation has all messages
        primary = service.get_conversation(conv1.id)
        assert primary.message_count == 2
        assert len(primary.messages) == 2
        assert len(primary.channels_used) == 2
        
        # Check secondary conversation is removed
        secondary = service.get_conversation(conv2.id)
        assert secondary is None
    
    def test_merge_nonexistent_conversations(self, service):
        """Test merging non-existent conversations."""
        fake_id1 = uuid.uuid4()
        fake_id2 = uuid.uuid4()
        
        success = merge_conversations(service, fake_id1, fake_id2)
        assert success is False
    
    def test_get_conversation_analytics(self, service):
        """Test getting conversation analytics."""
        # Create some conversations with messages
        conv1 = service.create_conversation(subject="Conv 1")
        conv2 = service.create_conversation(subject="Conv 2")
        
        service.add_message(conv1.id, CommunicationChannel.EMAIL, "outbound", "Message 1")
        service.add_message(conv1.id, CommunicationChannel.EMAIL, "inbound", "Response 1")
        service.add_message(conv2.id, CommunicationChannel.SMS, "outbound", "Message 2")
        
        service.update_conversation_status(conv2.id, ConversationStatus.CLOSED)
        
        analytics = get_conversation_analytics(service)
        
        assert analytics["total_conversations"] == 2
        assert analytics["total_messages"] == 3
        assert analytics["avg_messages_per_conversation"] == 1.5
        assert "status_distribution" in analytics
        assert "channel_usage" in analytics
        assert analytics["status_distribution"]["active"] == 1
        assert analytics["status_distribution"]["closed"] == 1
    
    def test_get_analytics_empty(self, service):
        """Test getting analytics with no conversations."""
        analytics = get_conversation_analytics(service)
        assert analytics == {}


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""
    
    def test_complete_conversation_flow(self, service):
        """Test a complete conversation flow from start to finish."""
        # Create conversation
        contact_id = uuid.uuid4()
        context = ConversationContext(
            conversation_id=uuid.uuid4(),
            contact_name="Sarah Johnson",
            contact_email="sarah@example.com",
            property_address="789 Pine St",
            last_updated=datetime.now()
        )
        
        conversation = service.create_conversation(
            contact_id=contact_id,
            subject="Property Inquiry - 789 Pine St",
            context=context
        )
        
        # Mock response analysis
        service.response_analysis_service = Mock()
        
        # Initial outreach
        service.add_message(
            conversation.id,
            CommunicationChannel.EMAIL,
            "outbound",
            "Hi Sarah, I'm interested in purchasing your property at 789 Pine St. Would you be open to discussing this?"
        )
        
        # Interested response
        mock_result = Mock()
        mock_result.overall_interest_level = 0.8
        mock_result.response_urgency.value = "high"
        mock_result.intent_analysis.primary_intent.value = "interested"
        mock_result.question_extraction.questions = ["How much?"]
        mock_result.objection_analysis.objections_detected = []
        mock_result.sentiment_analysis.sentiment_score = 0.6
        mock_result.sentiment_analysis.sentiment_type.value = "positive"
        mock_result.sentiment_analysis.key_phrases = ["interested"]
        service.response_analysis_service.analyze_response.return_value = mock_result
        
        service.add_message(
            conversation.id,
            CommunicationChannel.EMAIL,
            "inbound",
            "Yes, I'm interested! How much are you thinking?"
        )
        
        # Follow-up with price
        service.add_message(
            conversation.id,
            CommunicationChannel.EMAIL,
            "outbound",
            "I can offer $250,000 for a quick cash sale. Would that work for you?"
        )
        
        # Check conversation state
        final_conversation = service.get_conversation(conversation.id)
        
        assert final_conversation.message_count == 3
        assert final_conversation.status == ConversationStatus.ACTIVE
        assert len(final_conversation.next_actions) > 0
        assert final_conversation.summary is not None
        assert len(final_conversation.summary.questions_asked) > 0
        
        # Check metrics
        metrics = service.get_conversation_metrics(conversation.id)
        assert metrics["message_count"] == 3
        assert metrics["channels_used"] == 1
        assert metrics["avg_interest_level"] > 0.5


if __name__ == "__main__":
    pytest.main([__file__])