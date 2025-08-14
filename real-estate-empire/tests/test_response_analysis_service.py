"""
Unit tests for the response analysis service.
Tests Requirements 3.3 and 3.6 implementation.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import uuid

from app.services.response_analysis_service import (
    ResponseAnalysisService,
    ResponseAnalysisResult,
    SentimentType,
    IntentType,
    ObjectionType,
    UrgencyLevel,
    SentimentAnalysis,
    IntentAnalysis,
    ObjectionAnalysis,
    QuestionExtraction,
    analyze_conversation_thread
)
from app.models.communication import CommunicationChannel


# Global fixtures
@pytest.fixture
def service():
    """Create response analysis service instance."""
    return ResponseAnalysisService()


@pytest.fixture
def positive_message():
    """Sample positive response message."""
    return "Yes, I'm very interested! This sounds great. When can we talk?"


@pytest.fixture
def negative_message():
    """Sample negative response message."""
    return "No thanks, not interested. Please don't contact me again."


@pytest.fixture
def neutral_message():
    """Sample neutral response message."""
    return "I received your message about my property. Can you tell me more details?"


@pytest.fixture
def objection_message():
    """Sample message with objections."""
    return "Your offer is too low. The house is worth much more than that. I'm not ready to sell right now."


@pytest.fixture
def question_message():
    """Sample message with questions."""
    return "How much are you offering? When would you close? What's the process like?"


class TestResponseAnalysisService:
    """Test cases for ResponseAnalysisService."""
    
    def test_service_initialization(self, service):
        """Test service initializes correctly."""
        assert service is not None
        assert service.sentiment_keywords is not None
        assert service.intent_patterns is not None
        assert service.objection_patterns is not None


class TestSentimentAnalysis:
    """Test sentiment analysis functionality."""
    
    def test_positive_sentiment_analysis(self, service, positive_message):
        """Test analysis of positive sentiment message."""
        result = service.analyze_response(positive_message, CommunicationChannel.EMAIL)
        
        assert result.sentiment_analysis.sentiment_type in [SentimentType.POSITIVE, SentimentType.VERY_POSITIVE]
        assert result.sentiment_analysis.sentiment_score > 0.0
        assert result.sentiment_analysis.confidence_score > 0.0
        assert len(result.sentiment_analysis.emotional_indicators) > 0
    
    def test_negative_sentiment_analysis(self, service, negative_message):
        """Test analysis of negative sentiment message."""
        result = service.analyze_response(negative_message, CommunicationChannel.EMAIL)
        
        assert result.sentiment_analysis.sentiment_type in [SentimentType.NEGATIVE, SentimentType.VERY_NEGATIVE]
        assert result.sentiment_analysis.sentiment_score < 0.0
        assert result.sentiment_analysis.confidence_score > 0.0
        assert len(result.sentiment_analysis.emotional_indicators) > 0
    
    def test_neutral_sentiment_analysis(self, service, neutral_message):
        """Test analysis of neutral sentiment message."""
        result = service.analyze_response(neutral_message, CommunicationChannel.EMAIL)
        
        assert result.sentiment_analysis.sentiment_type == SentimentType.NEUTRAL
        assert -0.2 <= result.sentiment_analysis.sentiment_score <= 0.2
    
    def test_sentiment_confidence_scoring(self, service):
        """Test sentiment confidence scoring."""
        # Message with clear positive indicators
        clear_message = "Yes, I'm very interested! This is excellent! I love it!"
        result1 = service.analyze_response(clear_message, CommunicationChannel.EMAIL)
        
        # Message with ambiguous sentiment
        ambiguous_message = "I got your message about the property."
        result2 = service.analyze_response(ambiguous_message, CommunicationChannel.EMAIL)
        
        assert result1.sentiment_analysis.confidence_score > result2.sentiment_analysis.confidence_score


class TestIntentAnalysis:
    """Test intent analysis functionality."""
    
    def test_interested_intent_detection(self, service):
        """Test detection of interested intent."""
        message = "Yes, I'm interested in selling. Let's talk about this."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert result.intent_analysis.primary_intent == IntentType.INTERESTED
        assert result.intent_analysis.action_required is True
        assert result.intent_analysis.confidence_score > 0.0
    
    def test_not_interested_intent_detection(self, service):
        """Test detection of not interested intent."""
        message = "Not interested in selling. Please don't contact me again."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert result.intent_analysis.primary_intent == IntentType.NOT_INTERESTED
        assert result.intent_analysis.action_required is False
    
    def test_price_inquiry_intent_detection(self, service):
        """Test detection of price inquiry intent."""
        message = "How much are you offering for my house? What's the price?"
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert result.intent_analysis.primary_intent == IntentType.PRICE_INQUIRY
        assert result.intent_analysis.action_required is True
    
    def test_wants_to_discuss_intent_detection(self, service):
        """Test detection of wants to discuss intent."""
        message = "Let's talk about this. Can you call me to discuss?"
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert result.intent_analysis.primary_intent == IntentType.WANTS_TO_DISCUSS
        assert result.intent_analysis.action_required is True
    
    def test_unsubscribe_intent_detection(self, service):
        """Test detection of unsubscribe intent."""
        message = "Unsubscribe me from your list. Stop calling me."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert result.intent_analysis.primary_intent == IntentType.UNSUBSCRIBE
        assert result.intent_analysis.action_required is False
    
    def test_secondary_intents_detection(self, service):
        """Test detection of secondary intents."""
        message = "I'm interested but I need more information about the price and timeline."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert result.intent_analysis.primary_intent == IntentType.INTERESTED
        assert len(result.intent_analysis.secondary_intents) > 0


class TestObjectionAnalysis:
    """Test objection analysis functionality."""
    
    def test_price_objection_detection(self, service):
        """Test detection of price objections."""
        message = "Your offer is too low. The house is worth much more than that."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert ObjectionType.PRICE_TOO_LOW in result.objection_analysis.objections_detected
        assert result.objection_analysis.objection_severity > 0.0
        assert len(result.objection_analysis.suggested_responses) > 0
    
    def test_not_selling_objection_detection(self, service):
        """Test detection of not selling objections."""
        message = "I'm not selling the house. We're keeping it in the family."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert ObjectionType.NOT_SELLING in result.objection_analysis.objections_detected
        assert result.objection_analysis.objection_severity > 0.0
    
    def test_timing_objection_detection(self, service):
        """Test detection of timing objections."""
        message = "Not the right time for us. Maybe later in the future."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert ObjectionType.TIMING_NOT_RIGHT in result.objection_analysis.objections_detected
    
    def test_trust_objection_detection(self, service):
        """Test detection of trust objections."""
        message = "This sounds like a scam. I don't trust this offer."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert ObjectionType.TRUST_CONCERNS in result.objection_analysis.objections_detected
        assert result.objection_analysis.objection_severity > 0.7
    
    def test_multiple_objections_detection(self, service, objection_message):
        """Test detection of multiple objections."""
        result = service.analyze_response(objection_message, CommunicationChannel.EMAIL)
        
        assert len(result.objection_analysis.objections_detected) > 1
        assert ObjectionType.PRICE_TOO_LOW in result.objection_analysis.objections_detected
        assert ObjectionType.TIMING_NOT_RIGHT in result.objection_analysis.objections_detected
    
    def test_objection_response_suggestions(self, service):
        """Test objection response suggestions."""
        message = "Your price is too low for my property."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert len(result.objection_analysis.suggested_responses) > 0
        assert any("price" in response.lower() for response in result.objection_analysis.suggested_responses)


class TestQuestionExtraction:
    """Test question extraction functionality."""
    
    def test_question_extraction(self, service, question_message):
        """Test extraction of questions from message."""
        result = service.analyze_response(question_message, CommunicationChannel.EMAIL)
        
        assert len(result.question_extraction.questions) > 0
        assert len(result.question_extraction.question_types) > 0
        assert "price" in result.question_extraction.question_types
    
    def test_price_question_classification(self, service):
        """Test classification of price questions."""
        message = "How much are you offering? What's the price for my house?"
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert "price" in result.question_extraction.question_types
        assert len(result.question_extraction.questions) >= 1
    
    def test_timeline_question_classification(self, service):
        """Test classification of timeline questions."""
        message = "When would you close? How soon can this happen?"
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert "timeline" in result.question_extraction.question_types
    
    def test_process_question_classification(self, service):
        """Test classification of process questions."""
        message = "How does this work? What's the procedure for selling?"
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert "process" in result.question_extraction.question_types
    
    def test_immediate_response_detection(self, service):
        """Test detection of immediate response requirements."""
        message = "I need an answer today! This is urgent, please respond ASAP."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert result.question_extraction.requires_immediate_response is True
    
    def test_no_immediate_response_needed(self, service):
        """Test when no immediate response is needed."""
        message = "Just wondering about the general process when you have time."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert result.question_extraction.requires_immediate_response is False


class TestInterestLevelCalculation:
    """Test interest level calculation."""
    
    def test_high_interest_calculation(self, service):
        """Test calculation of high interest level."""
        message = "Yes, I'm very interested! This sounds excellent. Let's discuss this soon."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert result.overall_interest_level > 0.7
    
    def test_low_interest_calculation(self, service):
        """Test calculation of low interest level."""
        message = "Not interested at all. This is a terrible offer. Don't contact me."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert result.overall_interest_level < 0.3
    
    def test_medium_interest_calculation(self, service):
        """Test calculation of medium interest level."""
        message = "I received your message. Can you provide more information?"
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert 0.3 <= result.overall_interest_level <= 0.7


class TestUrgencyDetermination:
    """Test urgency level determination."""
    
    def test_immediate_urgency(self, service):
        """Test immediate urgency detection."""
        message = "I need to know right now! Please respond immediately."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert result.response_urgency == UrgencyLevel.IMMEDIATE
    
    def test_high_urgency(self, service):
        """Test high urgency detection."""
        message = "Yes, I'm interested in selling. Let's discuss this."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert result.response_urgency == UrgencyLevel.HIGH
    
    def test_medium_urgency(self, service):
        """Test medium urgency detection."""
        message = "I have some general questions about the process."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert result.response_urgency == UrgencyLevel.MEDIUM
    
    def test_low_urgency(self, service):
        """Test low urgency detection."""
        message = "Not interested in selling right now."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert result.response_urgency == UrgencyLevel.LOW


class TestRecommendedActions:
    """Test recommended actions generation."""
    
    def test_interested_actions(self, service):
        """Test actions for interested responses."""
        message = "Yes, I'm interested in your offer. Let's talk."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert len(result.recommended_actions) > 0
        assert any("schedule" in action.lower() for action in result.recommended_actions)
    
    def test_question_actions(self, service):
        """Test actions for responses with questions."""
        message = "How much are you offering? When would you close?"
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert any("answer" in action.lower() for action in result.recommended_actions)
    
    def test_objection_actions(self, service):
        """Test actions for responses with objections."""
        message = "Your offer is too low. I don't trust this process."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert any("objection" in action.lower() for action in result.recommended_actions)
        assert any("trust" in action.lower() for action in result.recommended_actions)
    
    def test_negative_sentiment_actions(self, service):
        """Test actions for negative sentiment responses."""
        message = "This is terrible. I hate this offer. Very disappointed."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert any("empathetic" in action.lower() for action in result.recommended_actions)


class TestFollowUpSuggestions:
    """Test follow-up suggestions generation."""
    
    def test_immediate_follow_up(self, service):
        """Test immediate follow-up suggestions."""
        message = "I need an answer today! This is urgent."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert any("1 hour" in suggestion for suggestion in result.follow_up_suggestions)
    
    def test_high_priority_follow_up(self, service):
        """Test high priority follow-up suggestions."""
        message = "Yes, I'm interested. Let's discuss this."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert any("24 hours" in suggestion for suggestion in result.follow_up_suggestions)
    
    def test_positive_sentiment_follow_up(self, service):
        """Test follow-up suggestions for positive sentiment."""
        message = "This sounds great! I'm very interested."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert any("momentum" in suggestion.lower() for suggestion in result.follow_up_suggestions)


class TestBatchAnalysis:
    """Test batch analysis functionality."""
    
    def test_batch_analyze_responses(self, service):
        """Test batch analysis of multiple responses."""
        messages = [
            {"content": "Yes, I'm interested!", "channel": CommunicationChannel.EMAIL},
            {"content": "Not interested, thanks.", "channel": CommunicationChannel.SMS},
            {"content": "Tell me more details.", "channel": CommunicationChannel.EMAIL}
        ]
        
        results = service.batch_analyze_responses(messages)
        
        assert len(results) == 3
        assert all(isinstance(result, ResponseAnalysisResult) for result in results)
        assert results[0].intent_analysis.primary_intent == IntentType.INTERESTED
        assert results[1].intent_analysis.primary_intent == IntentType.NOT_INTERESTED
        assert results[2].intent_analysis.primary_intent == IntentType.NEEDS_MORE_INFO


class TestAnalysisConfidence:
    """Test analysis confidence calculation."""
    
    def test_high_confidence_analysis(self, service):
        """Test high confidence analysis."""
        message = "Yes, I'm very interested! This is excellent! When can we talk?"
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert result.analysis_confidence > 0.7
    
    def test_low_confidence_analysis(self, service):
        """Test low confidence analysis."""
        message = "Hmm, maybe."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert result.analysis_confidence < 0.7


class TestContextualAnalysis:
    """Test contextual analysis features."""
    
    def test_analysis_with_context(self, service):
        """Test analysis with additional context."""
        message = "That's interesting."
        context = {"previous_messages": ["I can offer $200k for your house"]}
        
        result = service.analyze_response(message, CommunicationChannel.EMAIL, context)
        
        assert result is not None
        assert result.original_message == message
    
    def test_analysis_without_context(self, service):
        """Test analysis without context."""
        message = "That's interesting."
        
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert result is not None
        assert result.original_message == message


class TestChannelSpecificAnalysis:
    """Test channel-specific analysis."""
    
    def test_email_analysis(self, service):
        """Test analysis for email channel."""
        message = "Thank you for your email. I'm interested in learning more."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert result.channel == CommunicationChannel.EMAIL
    
    def test_sms_analysis(self, service):
        """Test analysis for SMS channel."""
        message = "Yes interested. Call me."
        result = service.analyze_response(message, CommunicationChannel.SMS)
        
        assert result.channel == CommunicationChannel.SMS
    
    def test_voice_analysis(self, service):
        """Test analysis for voice channel."""
        message = "Hi, I got your voicemail about my property. I'm interested."
        result = service.analyze_response(message, CommunicationChannel.VOICE)
        
        assert result.channel == CommunicationChannel.VOICE


class TestConversationThreadAnalysis:
    """Test conversation thread analysis."""
    
    def test_conversation_thread_analysis(self, service):
        """Test analysis of entire conversation thread."""
        messages = [
            {"content": "I got your message about my house.", "channel": CommunicationChannel.EMAIL},
            {"content": "Tell me more about your offer.", "channel": CommunicationChannel.EMAIL},
            {"content": "Yes, I'm interested! Let's talk.", "channel": CommunicationChannel.EMAIL}
        ]
        
        thread_analysis = analyze_conversation_thread(messages, service)
        
        assert "thread_summary" in thread_analysis
        assert "individual_analyses" in thread_analysis
        assert "recommendations" in thread_analysis
        
        summary = thread_analysis["thread_summary"]
        assert summary["message_count"] == 3
        assert "average_interest_level" in summary
        assert "sentiment_trend" in summary
    
    def test_improving_sentiment_trend(self, service):
        """Test detection of improving sentiment trend."""
        messages = [
            {"content": "Not sure about this.", "channel": CommunicationChannel.EMAIL},
            {"content": "This sounds better now.", "channel": CommunicationChannel.EMAIL},
            {"content": "Yes, I'm very interested!", "channel": CommunicationChannel.EMAIL}
        ]
        
        thread_analysis = analyze_conversation_thread(messages, service)
        summary = thread_analysis["thread_summary"]
        
        assert summary["sentiment_trend"] == "improving"
    
    def test_declining_sentiment_trend(self, service):
        """Test detection of declining sentiment trend."""
        messages = [
            {"content": "This sounds interesting.", "channel": CommunicationChannel.EMAIL},
            {"content": "I'm having second thoughts.", "channel": CommunicationChannel.EMAIL},
            {"content": "Not interested anymore.", "channel": CommunicationChannel.EMAIL}
        ]
        
        thread_analysis = analyze_conversation_thread(messages, service)
        summary = thread_analysis["thread_summary"]
        
        assert summary["sentiment_trend"] == "declining"
    
    def test_thread_recommendations(self, service):
        """Test thread-level recommendations."""
        messages = [
            {"content": "Yes, I'm very interested in your offer!", "channel": CommunicationChannel.EMAIL}
        ]
        
        thread_analysis = analyze_conversation_thread(messages, service)
        recommendations = thread_analysis["recommendations"]
        
        assert len(recommendations) > 0
        assert any("high interest" in rec.lower() for rec in recommendations)


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_message_analysis(self, service):
        """Test analysis of empty message."""
        result = service.analyze_response("", CommunicationChannel.EMAIL)
        
        assert result is not None
        assert result.original_message == ""
        assert result.analysis_confidence < 0.5
    
    def test_very_short_message_analysis(self, service):
        """Test analysis of very short message."""
        result = service.analyze_response("Ok", CommunicationChannel.SMS)
        
        assert result is not None
        assert result.original_message == "Ok"
    
    def test_very_long_message_analysis(self, service):
        """Test analysis of very long message."""
        long_message = "This is a very long message. " * 100
        result = service.analyze_response(long_message, CommunicationChannel.EMAIL)
        
        assert result is not None
        assert result.original_message == long_message
    
    def test_special_characters_message(self, service):
        """Test analysis of message with special characters."""
        message = "Yes! I'm interested... What's the price? $$$"
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert result is not None
        assert result.intent_analysis.primary_intent == IntentType.INTERESTED
    
    def test_mixed_language_indicators(self, service):
        """Test message with mixed positive and negative indicators."""
        message = "I love the idea but I hate the timing. This is great but terrible."
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        assert result is not None
        assert result.sentiment_analysis.sentiment_type == SentimentType.NEUTRAL


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""
    
    def test_interested_seller_scenario(self, service):
        """Test complete analysis of interested seller response."""
        message = "Hi! I got your message about buying my house at 123 Main St. I'm definitely interested in hearing more. How much are you thinking? When could we close? I need to sell quickly due to a job relocation. Please call me at 555-1234. Thanks!"
        
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        # Verify comprehensive analysis
        assert result.sentiment_analysis.sentiment_type in [SentimentType.POSITIVE, SentimentType.VERY_POSITIVE]
        assert result.intent_analysis.primary_intent == IntentType.INTERESTED
        assert result.overall_interest_level > 0.7
        assert result.response_urgency in [UrgencyLevel.HIGH, UrgencyLevel.MEDIUM]
        assert len(result.question_extraction.questions) > 0
        assert len(result.recommended_actions) > 0
    
    def test_objection_heavy_scenario(self, service):
        """Test analysis of response with multiple objections."""
        message = "I got your lowball offer. $150k is insulting for my house - it's worth at least $250k. I'm not ready to sell anyway, and I don't trust investors. This feels like a scam."
        
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        # Verify objection handling
        assert result.sentiment_analysis.sentiment_type in [SentimentType.NEGATIVE, SentimentType.VERY_NEGATIVE]
        assert len(result.objection_analysis.objections_detected) > 1
        assert ObjectionType.PRICE_TOO_LOW in result.objection_analysis.objections_detected
        assert ObjectionType.TRUST_CONCERNS in result.objection_analysis.objections_detected
        assert result.objection_analysis.objection_severity > 0.5
        assert len(result.objection_analysis.suggested_responses) > 0
    
    def test_information_seeking_scenario(self, service):
        """Test analysis of information-seeking response."""
        message = "I received your message about my property. Can you explain how this process works? What are the steps involved? Do you charge any fees? How do you determine the offer price? I want to understand everything before making any decisions."
        
        result = service.analyze_response(message, CommunicationChannel.EMAIL)
        
        # Verify information-seeking analysis - could be NEEDS_MORE_INFO or PRICE_INQUIRY
        assert result.intent_analysis.primary_intent in [IntentType.NEEDS_MORE_INFO, IntentType.PRICE_INQUIRY]
        assert len(result.question_extraction.questions) >= 1
        assert any(qtype in ["process", "price", "general"] for qtype in result.question_extraction.question_types)
        assert result.overall_interest_level > 0.4  # Neutral to positive interest
        assert any("answer" in action.lower() for action in result.recommended_actions)


if __name__ == "__main__":
    pytest.main([__file__])