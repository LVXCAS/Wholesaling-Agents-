"""
AI-powered response analysis service for analyzing seller communications.
Implements Requirements 3.3 and 3.6 for sentiment analysis and communication effectiveness.
"""
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from pydantic import BaseModel

from ..models.communication import CommunicationChannel


class SentimentType(str, Enum):
    """Sentiment classification types."""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class IntentType(str, Enum):
    """Intent classification types."""
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    NEEDS_MORE_INFO = "needs_more_info"
    WANTS_TO_DISCUSS = "wants_to_discuss"
    PRICE_INQUIRY = "price_inquiry"
    TIMELINE_INQUIRY = "timeline_inquiry"
    PROCESS_INQUIRY = "process_inquiry"
    OBJECTION = "objection"
    COMPLAINT = "complaint"
    SPAM_REPORT = "spam_report"
    UNSUBSCRIBE = "unsubscribe"


class ObjectionType(str, Enum):
    """Common objection types."""
    PRICE_TOO_LOW = "price_too_low"
    NOT_SELLING = "not_selling"
    ALREADY_LISTED = "already_listed"
    FAMILY_DECISION = "family_decision"
    TIMING_NOT_RIGHT = "timing_not_right"
    NEED_REPAIRS_FIRST = "need_repairs_first"
    SENTIMENTAL_VALUE = "sentimental_value"
    MARKET_TIMING = "market_timing"
    TRUST_CONCERNS = "trust_concerns"
    PROCESS_CONCERNS = "process_concerns"


class UrgencyLevel(str, Enum):
    """Response urgency levels."""
    IMMEDIATE = "immediate"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NO_RESPONSE_NEEDED = "no_response_needed"


class SentimentAnalysis(BaseModel):
    """Sentiment analysis result."""
    sentiment_type: SentimentType
    confidence_score: float  # 0.0 to 1.0
    sentiment_score: float   # -1.0 to 1.0 (negative to positive)
    emotional_indicators: List[str] = []
    key_phrases: List[str] = []


class IntentAnalysis(BaseModel):
    """Intent analysis result."""
    primary_intent: IntentType
    secondary_intents: List[IntentType] = []
    confidence_score: float  # 0.0 to 1.0
    intent_indicators: List[str] = []
    action_required: bool = True


class ObjectionAnalysis(BaseModel):
    """Objection analysis result."""
    objections_detected: List[ObjectionType] = []
    objection_severity: float = 0.0  # 0.0 to 1.0
    objection_phrases: List[str] = []
    suggested_responses: List[str] = []


class QuestionExtraction(BaseModel):
    """Extracted questions from response."""
    questions: List[str] = []
    question_types: List[str] = []  # "price", "timeline", "process", etc.
    requires_immediate_response: bool = False


class ResponseAnalysisResult(BaseModel):
    """Complete response analysis result."""
    id: uuid.UUID
    original_message: str
    channel: CommunicationChannel
    timestamp: datetime
    
    sentiment_analysis: SentimentAnalysis
    intent_analysis: IntentAnalysis
    objection_analysis: ObjectionAnalysis
    question_extraction: QuestionExtraction
    
    overall_interest_level: float  # 0.0 to 1.0
    response_urgency: UrgencyLevel
    recommended_actions: List[str] = []
    follow_up_suggestions: List[str] = []
    
    analysis_confidence: float  # 0.0 to 1.0
    created_at: datetime


class ResponseAnalysisService:
    """AI-powered response analysis service."""
    
    def __init__(self, ai_service=None):
        """Initialize the response analysis service."""
        self.ai_service = ai_service
        self.sentiment_keywords = self._load_sentiment_keywords()
        self.intent_patterns = self._load_intent_patterns()
        self.objection_patterns = self._load_objection_patterns()
        
    def analyze_response(
        self, 
        message: str, 
        channel: CommunicationChannel,
        context: Optional[Dict[str, Any]] = None
    ) -> ResponseAnalysisResult:
        """
        Analyze a seller response message comprehensively.
        
        Args:
            message: The response message to analyze
            channel: Communication channel (email, SMS, voice)
            context: Optional context about the conversation
            
        Returns:
            Complete analysis result
        """
        # Perform individual analyses
        sentiment = self._analyze_sentiment(message)
        intent = self._analyze_intent(message, context)
        objections = self._analyze_objections(message)
        questions = self._extract_questions(message)
        
        # Calculate overall metrics
        interest_level = self._calculate_interest_level(sentiment, intent, objections)
        urgency = self._determine_urgency(intent, questions, objections)
        
        # Generate recommendations
        actions = self._generate_recommended_actions(sentiment, intent, objections, questions)
        follow_ups = self._generate_follow_up_suggestions(sentiment, intent, urgency)
        
        # Calculate overall confidence
        confidence = self._calculate_analysis_confidence(sentiment, intent, objections)
        
        return ResponseAnalysisResult(
            id=uuid.uuid4(),
            original_message=message,
            channel=channel,
            timestamp=datetime.now(),
            sentiment_analysis=sentiment,
            intent_analysis=intent,
            objection_analysis=objections,
            question_extraction=questions,
            overall_interest_level=interest_level,
            response_urgency=urgency,
            recommended_actions=actions,
            follow_up_suggestions=follow_ups,
            analysis_confidence=confidence,
            created_at=datetime.now()
        )
    
    def batch_analyze_responses(
        self, 
        messages: List[Dict[str, Any]]
    ) -> List[ResponseAnalysisResult]:
        """
        Analyze multiple responses in batch.
        
        Args:
            messages: List of message dictionaries with 'content', 'channel', etc.
            
        Returns:
            List of analysis results
        """
        results = []
        
        for msg_data in messages:
            result = self.analyze_response(
                message=msg_data.get("content", ""),
                channel=msg_data.get("channel", CommunicationChannel.EMAIL),
                context=msg_data.get("context")
            )
            results.append(result)
            
        return results
    
    def _analyze_sentiment(self, message: str) -> SentimentAnalysis:
        """Analyze sentiment of the message."""
        message_lower = message.lower()
        
        # Count positive and negative indicators
        positive_score = 0
        negative_score = 0
        emotional_indicators = []
        key_phrases = []
        
        # Check for positive indicators
        for phrase, weight in self.sentiment_keywords["positive"].items():
            if phrase in message_lower:
                positive_score += weight
                emotional_indicators.append(f"positive: {phrase}")
                key_phrases.append(phrase)
        
        # Check for negative indicators
        for phrase, weight in self.sentiment_keywords["negative"].items():
            if phrase in message_lower:
                negative_score += weight
                emotional_indicators.append(f"negative: {phrase}")
                key_phrases.append(phrase)
        
        # Calculate overall sentiment score
        total_score = positive_score - negative_score
        normalized_score = max(-1.0, min(1.0, total_score / 10.0))  # Normalize to -1 to 1
        
        # Determine sentiment type
        if normalized_score >= 0.6:
            sentiment_type = SentimentType.VERY_POSITIVE
        elif normalized_score >= 0.2:
            sentiment_type = SentimentType.POSITIVE
        elif normalized_score >= -0.2:
            sentiment_type = SentimentType.NEUTRAL
        elif normalized_score >= -0.6:
            sentiment_type = SentimentType.NEGATIVE
        else:
            sentiment_type = SentimentType.VERY_NEGATIVE
        
        # Calculate confidence based on number of indicators found
        confidence = min(1.0, (positive_score + negative_score) / 5.0)
        
        return SentimentAnalysis(
            sentiment_type=sentiment_type,
            confidence_score=confidence,
            sentiment_score=normalized_score,
            emotional_indicators=emotional_indicators,
            key_phrases=key_phrases
        )
    
    def _analyze_intent(self, message: str, context: Optional[Dict[str, Any]] = None) -> IntentAnalysis:
        """Analyze the intent of the message."""
        message_lower = message.lower()
        intent_scores = {}
        indicators = []
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern, weight in patterns.items():
                if re.search(pattern, message_lower):
                    score += weight
                    indicators.append(f"{intent}: {pattern}")
            
            if score > 0:
                intent_scores[intent] = score
        
        # Determine primary intent with priority handling
        if intent_scores:
            # Special handling: NOT_INTERESTED takes priority over INTERESTED
            if "not_interested" in intent_scores and "interested" in intent_scores:
                if intent_scores["not_interested"] >= intent_scores["interested"]:
                    primary_intent = "not_interested"
                else:
                    primary_intent = "interested"
            else:
                primary_intent = max(intent_scores.keys(), key=lambda k: intent_scores[k])
            
            confidence = min(1.0, intent_scores[primary_intent] / 3.0)
            
            # Get secondary intents
            secondary_intents = [
                intent for intent, score in intent_scores.items() 
                if intent != primary_intent and score >= 1.0
            ]
        else:
            primary_intent = IntentType.NEEDS_MORE_INFO
            confidence = 0.3
            secondary_intents = []
        
        # Determine if action is required
        action_required = primary_intent not in [
            IntentType.SPAM_REPORT, 
            IntentType.UNSUBSCRIBE,
            IntentType.NOT_INTERESTED
        ]
        
        return IntentAnalysis(
            primary_intent=IntentType(primary_intent),
            secondary_intents=[IntentType(intent) for intent in secondary_intents],
            confidence_score=confidence,
            intent_indicators=indicators,
            action_required=action_required
        )
    
    def _analyze_objections(self, message: str) -> ObjectionAnalysis:
        """Analyze objections in the message."""
        message_lower = message.lower()
        objections_found = []
        objection_phrases = []
        severity_score = 0.0
        
        # Check for objection patterns
        for objection, patterns in self.objection_patterns.items():
            for pattern, severity in patterns.items():
                if re.search(pattern, message_lower):
                    objections_found.append(ObjectionType(objection))
                    objection_phrases.append(pattern)
                    severity_score = max(severity_score, severity)
        
        # Generate suggested responses based on objections
        suggested_responses = self._generate_objection_responses(objections_found)
        
        return ObjectionAnalysis(
            objections_detected=objections_found,
            objection_severity=severity_score,
            objection_phrases=objection_phrases,
            suggested_responses=suggested_responses
        )
    
    def _extract_questions(self, message: str) -> QuestionExtraction:
        """Extract questions from the message."""
        questions = []
        question_types = []
        
        # Split by sentence endings and look for questions
        sentences = re.split(r'[.!]+', message)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Check if it's a question (ends with ? or contains question words)
            is_question = (
                sentence.endswith('?') or
                re.search(r'\bhow\b.*\?', sentence.lower()) or
                re.search(r'\bwhat\b.*\?', sentence.lower()) or
                re.search(r'\bwhen\b.*\?', sentence.lower()) or
                re.search(r'\bwhere\b.*\?', sentence.lower()) or
                re.search(r'\bwhy\b.*\?', sentence.lower()) or
                re.search(r'\bwho\b.*\?', sentence.lower()) or
                re.search(r'\bcan you\b', sentence.lower()) or
                re.search(r'\bwould you\b', sentence.lower()) or
                re.search(r'\bcould you\b', sentence.lower()) or
                re.search(r'\bhow much\b', sentence.lower()) or
                re.search(r'\bhow long\b', sentence.lower()) or
                re.search(r'\bhow soon\b', sentence.lower())
            )
            
            if is_question:
                questions.append(sentence.strip('?').strip())
                
                # Classify question type
                sentence_lower = sentence.lower()
                if any(word in sentence_lower for word in ['price', 'cost', 'much', 'offer', 'money']):
                    question_types.append('price')
                elif any(word in sentence_lower for word in ['when', 'timeline', 'time', 'soon', 'long']):
                    question_types.append('timeline')
                elif any(word in sentence_lower for word in ['how', 'process', 'work', 'procedure', 'steps']):
                    question_types.append('process')
                elif any(word in sentence_lower for word in ['why', 'reason']):
                    question_types.append('reason')
                else:
                    question_types.append('general')
        
        # Determine if immediate response is needed
        immediate_keywords = ['urgent', 'asap', 'immediately', 'right away', 'today']
        requires_immediate = any(keyword in message.lower() for keyword in immediate_keywords)
        
        return QuestionExtraction(
            questions=questions,
            question_types=question_types,
            requires_immediate_response=requires_immediate
        )
    
    def _calculate_interest_level(
        self, 
        sentiment: SentimentAnalysis, 
        intent: IntentAnalysis, 
        objections: ObjectionAnalysis
    ) -> float:
        """Calculate overall interest level (0.0 to 1.0)."""
        base_score = 0.5
        
        # Adjust based on sentiment
        if sentiment.sentiment_type == SentimentType.VERY_POSITIVE:
            base_score += 0.3
        elif sentiment.sentiment_type == SentimentType.POSITIVE:
            base_score += 0.2
        elif sentiment.sentiment_type == SentimentType.NEGATIVE:
            base_score -= 0.2
        elif sentiment.sentiment_type == SentimentType.VERY_NEGATIVE:
            base_score -= 0.3
        
        # Adjust based on intent - prioritize NOT_INTERESTED over INTERESTED when both are detected
        if intent.primary_intent == IntentType.NOT_INTERESTED:
            base_score -= 0.4
        elif intent.primary_intent == IntentType.INTERESTED and IntentType.NOT_INTERESTED not in intent.secondary_intents:
            base_score += 0.3
        elif intent.primary_intent == IntentType.WANTS_TO_DISCUSS:
            base_score += 0.2
        elif intent.primary_intent == IntentType.OBJECTION:
            base_score -= 0.2
        elif intent.primary_intent == IntentType.UNSUBSCRIBE:
            base_score -= 0.5
        
        # Adjust based on objections
        base_score -= objections.objection_severity * 0.3
        
        return max(0.0, min(1.0, base_score))
    
    def _determine_urgency(
        self, 
        intent: IntentAnalysis, 
        questions: QuestionExtraction, 
        objections: ObjectionAnalysis
    ) -> UrgencyLevel:
        """Determine response urgency level."""
        if questions.requires_immediate_response:
            return UrgencyLevel.IMMEDIATE
        
        # Check for unsubscribe or not interested first
        if intent.primary_intent in [IntentType.UNSUBSCRIBE, IntentType.NOT_INTERESTED]:
            return UrgencyLevel.LOW
        
        if intent.primary_intent in [IntentType.INTERESTED, IntentType.WANTS_TO_DISCUSS]:
            return UrgencyLevel.HIGH
        
        if intent.primary_intent in [IntentType.PRICE_INQUIRY, IntentType.TIMELINE_INQUIRY]:
            return UrgencyLevel.HIGH
        
        if questions.questions:
            return UrgencyLevel.MEDIUM
        
        if objections.objections_detected:
            return UrgencyLevel.MEDIUM
        
        return UrgencyLevel.MEDIUM
    
    def _generate_recommended_actions(
        self, 
        sentiment: SentimentAnalysis, 
        intent: IntentAnalysis, 
        objections: ObjectionAnalysis, 
        questions: QuestionExtraction
    ) -> List[str]:
        """Generate recommended actions based on analysis."""
        actions = []
        
        # Actions based on intent
        if intent.primary_intent == IntentType.INTERESTED:
            actions.append("Schedule a call to discuss details")
            actions.append("Prepare property analysis and offer")
        elif intent.primary_intent == IntentType.WANTS_TO_DISCUSS:
            actions.append("Respond promptly to schedule conversation")
        elif intent.primary_intent == IntentType.PRICE_INQUIRY:
            actions.append("Provide price range or schedule valuation call")
        elif intent.primary_intent == IntentType.NOT_INTERESTED:
            actions.append("Add to long-term nurture campaign")
            actions.append("Respect their decision and maintain relationship")
        
        # Actions based on questions
        if questions.questions:
            actions.append("Answer all questions thoroughly")
            if questions.requires_immediate_response:
                actions.append("Respond within 1 hour")
        
        # Actions based on objections
        if objections.objections_detected:
            actions.append("Address objections with empathy")
            actions.append("Provide relevant information to overcome concerns")
            # Add specific trust-building actions
            if ObjectionType.TRUST_CONCERNS in objections.objections_detected:
                actions.append("Focus on building trust")
        
        # Actions based on sentiment
        if sentiment.sentiment_type in [SentimentType.NEGATIVE, SentimentType.VERY_NEGATIVE]:
            actions.append("Use empathetic tone in response")
            actions.append("Focus on building trust")
        
        return actions
    
    def _generate_follow_up_suggestions(
        self, 
        sentiment: SentimentAnalysis, 
        intent: IntentAnalysis, 
        urgency: UrgencyLevel
    ) -> List[str]:
        """Generate follow-up suggestions."""
        suggestions = []
        
        if urgency == UrgencyLevel.IMMEDIATE:
            suggestions.append("Follow up within 1 hour if no response")
        elif urgency == UrgencyLevel.HIGH:
            suggestions.append("Follow up within 24 hours if no response")
        elif urgency == UrgencyLevel.MEDIUM:
            suggestions.append("Follow up in 2-3 days if no response")
        else:
            suggestions.append("Follow up in 1 week if appropriate")
        
        if intent.primary_intent == IntentType.INTERESTED:
            suggestions.append("Send additional property information")
            suggestions.append("Prepare contract templates")
        
        if sentiment.sentiment_type in [SentimentType.POSITIVE, SentimentType.VERY_POSITIVE]:
            suggestions.append("Move quickly to maintain momentum")
        
        return suggestions
    
    def _calculate_analysis_confidence(
        self, 
        sentiment: SentimentAnalysis, 
        intent: IntentAnalysis, 
        objections: ObjectionAnalysis
    ) -> float:
        """Calculate overall analysis confidence."""
        confidence_scores = [
            sentiment.confidence_score,
            intent.confidence_score,
            0.8 if objections.objections_detected else 0.6  # Higher confidence when objections are clear
        ]
        
        return sum(confidence_scores) / len(confidence_scores)
    
    def _generate_objection_responses(self, objections: List[ObjectionType]) -> List[str]:
        """Generate suggested responses for objections."""
        responses = []
        
        objection_responses = {
            ObjectionType.PRICE_TOO_LOW: [
                "I understand price is important. Let me explain how I arrived at this valuation.",
                "Would you be open to discussing what price range you had in mind?"
            ],
            ObjectionType.NOT_SELLING: [
                "I completely understand. Would you mind if I stayed in touch in case your situation changes?",
                "No pressure at all. I'm here if you ever want to explore your options."
            ],
            ObjectionType.ALREADY_LISTED: [
                "That's great that you're already working with an agent. Best of luck with the sale!",
                "If things don't work out with your current listing, I'd be happy to discuss alternatives."
            ],
            ObjectionType.TIMING_NOT_RIGHT: [
                "Timing is everything in real estate. When might be a better time to revisit this?",
                "I understand. Would you like me to check back with you in a few months?"
            ],
            ObjectionType.TRUST_CONCERNS: [
                "I completely understand your concerns. Let me provide some references and credentials.",
                "Trust is essential in any transaction. What information would help you feel more comfortable?"
            ]
        }
        
        for objection in objections:
            if objection in objection_responses:
                responses.extend(objection_responses[objection])
        
        return responses
    
    def _load_sentiment_keywords(self) -> Dict[str, Dict[str, float]]:
        """Load sentiment analysis keywords and weights."""
        return {
            "positive": {
                "interested": 3.0,
                "yes": 2.0,
                "great": 2.0,
                "excellent": 2.0,
                "perfect": 2.0,
                "love": 2.0,
                "like": 1.5,
                "good": 1.5,
                "sounds good": 2.5,
                "thank you": 1.5,
                "appreciate": 1.5,
                "helpful": 1.5,
                "please": 1.0,
                "sure": 1.5,
                "absolutely": 2.0,
                "definitely": 2.0
            },
            "negative": {
                "no": 2.0,
                "not interested": 3.0,
                "never": 2.5,
                "hate": 2.5,
                "terrible": 2.5,
                "awful": 2.5,
                "scam": 3.0,
                "spam": 3.0,
                "annoying": 2.0,
                "stop": 2.5,
                "leave me alone": 3.0,
                "don't call": 2.5,
                "don't contact": 2.5,
                "remove": 2.0,
                "unsubscribe": 2.5,
                "angry": 2.0,
                "frustrated": 2.0,
                "disappointed": 1.5
            }
        }
    
    def _load_intent_patterns(self) -> Dict[str, Dict[str, float]]:
        """Load intent detection patterns and weights."""
        return {
            "interested": {
                r"\binterested\b": 3.0,
                r"\byes\b": 2.0,
                r"\btell me more\b": 2.5,
                r"\bsounds good\b": 2.5,
                r"\blet's talk\b": 3.0,
                r"\bcall me\b": 2.5,
                r"\bwhen can we\b": 2.0,
                r"\bi'm ready\b": 3.0
            },
            "not_interested": {
                r"\bnot interested\b": 3.0,
                r"\bno thanks\b": 2.5,
                r"\bnot selling\b": 3.0,
                r"\bdon't want\b": 2.0,
                r"\bnot ready\b": 2.0,
                r"\bmaybe later\b": 1.5
            },
            "needs_more_info": {
                r"\btell me more\b": 2.0,
                r"\bmore information\b": 2.5,
                r"\bdetails\b": 1.5,
                r"\bexplain\b": 2.0,
                r"\bhow does\b": 2.0,
                r"\bwhat is\b": 1.5
            },
            "wants_to_discuss": {
                r"\bcall me\b": 3.0,
                r"\blet's talk\b": 3.0,
                r"\bdiscuss\b": 2.5,
                r"\bschedule\b": 2.5,
                r"\bmeet\b": 2.0,
                r"\bconversation\b": 2.0
            },
            "price_inquiry": {
                r"\bhow much\b": 3.0,
                r"\bprice\b": 2.0,
                r"\boffer\b": 2.5,
                r"\bvalue\b": 2.0,
                r"\bworth\b": 2.0,
                r"\bcost\b": 1.5
            },
            "timeline_inquiry": {
                r"\bwhen\b": 2.0,
                r"\btimeline\b": 2.5,
                r"\bhow long\b": 2.0,
                r"\bhow soon\b": 2.5,
                r"\bquickly\b": 2.0
            },
            "unsubscribe": {
                r"\bunsubscribe\b": 3.0,
                r"\bremove me\b": 3.0,
                r"\bstop calling\b": 3.0,
                r"\bstop emailing\b": 3.0,
                r"\bdon't contact\b": 2.5,
                r"\bleave me alone\b": 3.0
            }
        }
    
    def _load_objection_patterns(self) -> Dict[str, Dict[str, float]]:
        """Load objection detection patterns and severity scores."""
        return {
            "price_too_low": {
                r"\btoo low\b": 0.8,
                r"\bnot enough\b": 0.7,
                r"\bworth more\b": 0.8,
                r"\binsulting\b": 0.9,
                r"\bridiculously low\b": 0.9
            },
            "not_selling": {
                r"\bnot selling\b": 0.9,
                r"\bkeeping the house\b": 0.8,
                r"\bstaying put\b": 0.7,
                r"\bnot moving\b": 0.8
            },
            "already_listed": {
                r"\balready listed\b": 0.6,
                r"\bhave an agent\b": 0.6,
                r"\bwith a realtor\b": 0.6,
                r"\bon the market\b": 0.5
            },
            "timing_not_right": {
                r"\bnot the right time\b": 0.7,
                r"\btoo soon\b": 0.6,
                r"\bnot ready\b": 0.7,
                r"\bmaybe later\b": 0.5,
                r"\bin the future\b": 0.4
            },
            "trust_concerns": {
                r"\bscam\b": 0.9,
                r"\bdon't trust\b": 0.8,
                r"\bsuspicious\b": 0.7,
                r"\blegitimate\b": 0.6,
                r"\bproof\b": 0.5
            }
        }


# Utility functions
def analyze_conversation_thread(
    messages: List[Dict[str, Any]], 
    service: ResponseAnalysisService
) -> Dict[str, Any]:
    """
    Analyze an entire conversation thread.
    
    Args:
        messages: List of message dictionaries in chronological order
        service: Response analysis service instance
        
    Returns:
        Thread analysis summary
    """
    analyses = service.batch_analyze_responses(messages)
    
    # Calculate thread-level metrics
    avg_interest = sum(a.overall_interest_level for a in analyses) / len(analyses)
    avg_sentiment = sum(a.sentiment_analysis.sentiment_score for a in analyses) / len(analyses)
    
    # Track sentiment trend
    sentiment_trend = "stable"
    if len(analyses) > 1:
        first_sentiment = analyses[0].sentiment_analysis.sentiment_score
        last_sentiment = analyses[-1].sentiment_analysis.sentiment_score
        
        if last_sentiment > first_sentiment + 0.1:
            sentiment_trend = "improving"
        elif last_sentiment < first_sentiment - 0.1:
            sentiment_trend = "declining"
    
    # Collect all objections
    all_objections = []
    for analysis in analyses:
        all_objections.extend(analysis.objection_analysis.objections_detected)
    
    # Collect all questions
    all_questions = []
    for analysis in analyses:
        all_questions.extend(analysis.question_extraction.questions)
    
    return {
        "thread_summary": {
            "message_count": len(analyses),
            "average_interest_level": avg_interest,
            "average_sentiment": avg_sentiment,
            "sentiment_trend": sentiment_trend,
            "total_objections": len(all_objections),
            "total_questions": len(all_questions),
            "requires_immediate_attention": any(
                a.response_urgency == UrgencyLevel.IMMEDIATE for a in analyses
            )
        },
        "individual_analyses": analyses,
        "recommendations": _generate_thread_recommendations(analyses)
    }


def _generate_thread_recommendations(analyses: List[ResponseAnalysisResult]) -> List[str]:
    """Generate recommendations for the entire conversation thread."""
    recommendations = []
    
    if not analyses:
        return recommendations
    
    latest_analysis = analyses[-1]
    
    # Based on latest response
    if latest_analysis.overall_interest_level > 0.7:
        recommendations.append("High interest detected - prioritize this lead")
        recommendations.append("Prepare detailed offer and schedule call")
    elif latest_analysis.overall_interest_level < 0.3:
        recommendations.append("Low interest - consider long-term nurture approach")
    
    # Based on trend
    if len(analyses) > 1:
        interest_trend = analyses[-1].overall_interest_level - analyses[0].overall_interest_level
        if interest_trend > 0.2:
            recommendations.append("Interest is increasing - maintain momentum")
        elif interest_trend < -0.2:
            recommendations.append("Interest is declining - reassess approach")
    
    # Based on objections
    all_objections = []
    for analysis in analyses:
        all_objections.extend(analysis.objection_analysis.objections_detected)
    
    if all_objections:
        recommendations.append("Address recurring objections systematically")
    
    return recommendations