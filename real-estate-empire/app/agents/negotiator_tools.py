"""
Negotiator Agent Tools - Communication and Negotiation Tools
Specialized tools for the Negotiator Agent to handle outreach, communication, and negotiation
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
import re
from dataclasses import dataclass

from pydantic import BaseModel, Field
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

from ..core.agent_tools import BaseAgentTool, ToolMetadata, ToolCategory, ToolAccessLevel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CommunicationChannel(str, Enum):
    """Communication channels"""
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    VOICEMAIL = "voicemail"
    DIRECT_MAIL = "direct_mail"


class MessageStatus(str, Enum):
    """Message delivery status"""
    DRAFT = "draft"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    RESPONDED = "responded"
    FAILED = "failed"
    BOUNCED = "bounced"


@dataclass
class CommunicationResult:
    """Result of communication attempt"""
    success: bool
    message_id: str
    channel: CommunicationChannel
    status: MessageStatus
    recipient: str
    sent_at: datetime
    error: Optional[str] = None
    delivery_info: Optional[Dict[str, Any]] = None


class EmailCommunicationTool(BaseAgentTool):
    """Tool for sending email communications"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="email_communication",
            description="Send personalized email communications to property owners and leads",
            category=ToolCategory.COMMUNICATION,
            access_level=ToolAccessLevel.RESTRICTED,
            allowed_agents=["negotiator", "supervisor"],
            rate_limit=500,  # 500 emails per minute
            cost_per_call=0.05
        )
        super().__init__(metadata)
        
        # Email configuration (would be loaded from environment)
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email_user = "noreply@realestateinvestor.com"
        self.email_password = "app_password"  # Would use secure storage
        self.from_name = "Real Estate Investment Team"
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Send email communication"""
        recipient = kwargs.get("recipient", "")
        subject = kwargs.get("subject", "")
        content = kwargs.get("content", "")
        html_content = kwargs.get("html_content", None)
        reply_to = kwargs.get("reply_to", None)
        tracking_enabled = kwargs.get("tracking_enabled", True)
        
        if not recipient or not subject or not content:
            return {
                "success": False,
                "error": "Missing required fields: recipient, subject, or content"
            }
        
        try:
            # Create message
            message = MimeMultipart("alternative")
            message["From"] = f"{self.from_name} <{self.email_user}>"
            message["To"] = recipient
            message["Subject"] = subject
            
            if reply_to:
                message["Reply-To"] = reply_to
            
            # Add tracking if enabled
            if tracking_enabled:
                content = self._add_email_tracking(content)
                if html_content:
                    html_content = self._add_email_tracking(html_content, is_html=True)
            
            # Add text content
            text_part = MimeText(content, "plain")
            message.attach(text_part)
            
            # Add HTML content if provided
            if html_content:
                html_part = MimeText(html_content, "html")
                message.attach(html_part)
            
            # Send email
            result = await self._send_email(message, recipient)
            
            return {
                "message_id": result.message_id,
                "status": result.status.value,
                "sent_at": result.sent_at.isoformat(),
                "recipient": recipient,
                "tracking_enabled": tracking_enabled,
                "delivery_info": result.delivery_info
            }
            
        except Exception as e:
            logger.error(f"Error sending email to {recipient}: {e}")
            return {
                "success": False,
                "error": str(e),
                "recipient": recipient
            }
    
    async def _send_email(self, message: MimeMultipart, recipient: str) -> CommunicationResult:
        """Send email using SMTP"""
        message_id = str(uuid.uuid4())
        
        try:
            # In production, this would use actual SMTP
            # For now, simulate email sending
            await asyncio.sleep(0.1)  # Simulate network delay
            
            logger.info(f"Email sent to {recipient} with subject: {message['Subject']}")
            
            return CommunicationResult(
                success=True,
                message_id=message_id,
                channel=CommunicationChannel.EMAIL,
                status=MessageStatus.SENT,
                recipient=recipient,
                sent_at=datetime.now(),
                delivery_info={
                    "smtp_server": self.smtp_server,
                    "message_size": len(str(message))
                }
            )
            
        except Exception as e:
            return CommunicationResult(
                success=False,
                message_id=message_id,
                channel=CommunicationChannel.EMAIL,
                status=MessageStatus.FAILED,
                recipient=recipient,
                sent_at=datetime.now(),
                error=str(e)
            )
    
    def _add_email_tracking(self, content: str, is_html: bool = False) -> str:
        """Add email tracking pixels and links"""
        tracking_id = str(uuid.uuid4())
        
        if is_html:
            # Add tracking pixel for HTML emails
            tracking_pixel = f'<img src="https://track.realestateinvestor.com/pixel/{tracking_id}" width="1" height="1" style="display:none;">'
            content += tracking_pixel
        else:
            # Add tracking for text emails (less intrusive)
            content += f"\n\n---\nMessage ID: {tracking_id[:8]}"
        
        return content


class SMSCommunicationTool(BaseAgentTool):
    """Tool for sending SMS communications"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="sms_communication",
            description="Send personalized SMS messages to property owners and leads",
            category=ToolCategory.COMMUNICATION,
            access_level=ToolAccessLevel.RESTRICTED,
            allowed_agents=["negotiator", "supervisor"],
            rate_limit=100,  # 100 SMS per minute
            cost_per_call=0.10
        )
        super().__init__(metadata)
        
        # SMS configuration (would integrate with Twilio, etc.)
        self.from_number = "+15551234567"
        self.service_provider = "twilio"
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Send SMS communication"""
        recipient = kwargs.get("recipient", "")
        message = kwargs.get("message", "")
        sender_name = kwargs.get("sender_name", "Real Estate Team")
        
        if not recipient or not message:
            return {
                "success": False,
                "error": "Missing required fields: recipient or message"
            }
        
        # Validate phone number format
        if not self._validate_phone_number(recipient):
            return {
                "success": False,
                "error": "Invalid phone number format"
            }
        
        # Check message length (SMS limit is 160 characters)
        if len(message) > 160:
            return {
                "success": False,
                "error": f"Message too long ({len(message)} characters). SMS limit is 160 characters."
            }
        
        try:
            # Add sender identification if not already present
            if sender_name and not message.lower().startswith(sender_name.lower()):
                message = f"{sender_name}: {message}"
            
            # Send SMS
            result = await self._send_sms(recipient, message)
            
            return {
                "message_id": result.message_id,
                "status": result.status.value,
                "sent_at": result.sent_at.isoformat(),
                "recipient": recipient,
                "message_length": len(message),
                "delivery_info": result.delivery_info
            }
            
        except Exception as e:
            logger.error(f"Error sending SMS to {recipient}: {e}")
            return {
                "success": False,
                "error": str(e),
                "recipient": recipient
            }
    
    async def _send_sms(self, recipient: str, message: str) -> CommunicationResult:
        """Send SMS using service provider"""
        message_id = str(uuid.uuid4())
        
        try:
            # In production, this would integrate with Twilio or similar
            # For now, simulate SMS sending
            await asyncio.sleep(0.05)  # Simulate API call
            
            logger.info(f"SMS sent to {recipient}: {message[:50]}...")
            
            return CommunicationResult(
                success=True,
                message_id=message_id,
                channel=CommunicationChannel.SMS,
                status=MessageStatus.SENT,
                recipient=recipient,
                sent_at=datetime.now(),
                delivery_info={
                    "provider": self.service_provider,
                    "from_number": self.from_number,
                    "message_length": len(message)
                }
            )
            
        except Exception as e:
            return CommunicationResult(
                success=False,
                message_id=message_id,
                channel=CommunicationChannel.SMS,
                status=MessageStatus.FAILED,
                recipient=recipient,
                sent_at=datetime.now(),
                error=str(e)
            )
    
    def _validate_phone_number(self, phone: str) -> bool:
        """Validate phone number format"""
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Check if it's a valid US phone number (10 or 11 digits)
        if len(digits_only) == 10:
            return True
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            return True
        
        return False


class VoiceCommunicationTool(BaseAgentTool):
    """Tool for voice calls and voicemail drops"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="voice_communication",
            description="Make voice calls and leave voicemail messages",
            category=ToolCategory.COMMUNICATION,
            access_level=ToolAccessLevel.RESTRICTED,
            allowed_agents=["negotiator", "supervisor"],
            rate_limit=50,  # 50 calls per minute
            cost_per_call=0.25
        )
        super().__init__(metadata)
        
        # Voice service configuration
        self.service_provider = "twilio_voice"
        self.caller_id = "+15551234567"
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Make voice call or leave voicemail"""
        recipient = kwargs.get("recipient", "")
        call_type = kwargs.get("call_type", "call")  # call, voicemail
        script = kwargs.get("script", "")
        max_duration = kwargs.get("max_duration", 300)  # 5 minutes
        record_call = kwargs.get("record_call", True)
        
        if not recipient or not script:
            return {
                "success": False,
                "error": "Missing required fields: recipient or script"
            }
        
        try:
            if call_type == "voicemail":
                result = await self._leave_voicemail(recipient, script)
            else:
                result = await self._make_call(recipient, script, max_duration, record_call)
            
            return {
                "call_id": result.message_id,
                "status": result.status.value,
                "started_at": result.sent_at.isoformat(),
                "recipient": recipient,
                "call_type": call_type,
                "delivery_info": result.delivery_info
            }
            
        except Exception as e:
            logger.error(f"Error with voice communication to {recipient}: {e}")
            return {
                "success": False,
                "error": str(e),
                "recipient": recipient
            }
    
    async def _make_call(self, recipient: str, script: str, max_duration: int, record_call: bool) -> CommunicationResult:
        """Make a voice call"""
        call_id = str(uuid.uuid4())
        
        try:
            # In production, this would integrate with Twilio Voice API
            # For now, simulate call initiation
            await asyncio.sleep(0.2)  # Simulate API call
            
            logger.info(f"Voice call initiated to {recipient}")
            
            return CommunicationResult(
                success=True,
                message_id=call_id,
                channel=CommunicationChannel.PHONE,
                status=MessageStatus.SENT,
                recipient=recipient,
                sent_at=datetime.now(),
                delivery_info={
                    "provider": self.service_provider,
                    "caller_id": self.caller_id,
                    "max_duration": max_duration,
                    "recording_enabled": record_call,
                    "script_length": len(script)
                }
            )
            
        except Exception as e:
            return CommunicationResult(
                success=False,
                message_id=call_id,
                channel=CommunicationChannel.PHONE,
                status=MessageStatus.FAILED,
                recipient=recipient,
                sent_at=datetime.now(),
                error=str(e)
            )
    
    async def _leave_voicemail(self, recipient: str, script: str) -> CommunicationResult:
        """Leave a voicemail message"""
        voicemail_id = str(uuid.uuid4())
        
        try:
            # In production, this would use voice synthesis and voicemail drop services
            # For now, simulate voicemail drop
            await asyncio.sleep(0.3)  # Simulate voicemail drop
            
            logger.info(f"Voicemail dropped for {recipient}")
            
            return CommunicationResult(
                success=True,
                message_id=voicemail_id,
                channel=CommunicationChannel.VOICEMAIL,
                status=MessageStatus.DELIVERED,
                recipient=recipient,
                sent_at=datetime.now(),
                delivery_info={
                    "provider": self.service_provider,
                    "caller_id": self.caller_id,
                    "script_length": len(script),
                    "voice_type": "synthetic"
                }
            )
            
        except Exception as e:
            return CommunicationResult(
                success=False,
                message_id=voicemail_id,
                channel=CommunicationChannel.VOICEMAIL,
                status=MessageStatus.FAILED,
                recipient=recipient,
                sent_at=datetime.now(),
                error=str(e)
            )


class ResponseAnalysisTool(BaseAgentTool):
    """Tool for analyzing seller responses and communications"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="response_analysis",
            description="Analyze seller responses for sentiment, interest, and negotiation insights",
            category=ToolCategory.ANALYSIS,
            access_level=ToolAccessLevel.RESTRICTED,
            allowed_agents=["negotiator", "supervisor"],
            rate_limit=200,
            cost_per_call=0.03
        )
        super().__init__(metadata)
        
        # Analysis configuration
        self.sentiment_keywords = {
            "positive": ["interested", "yes", "sounds good", "tell me more", "when", "how much"],
            "negative": ["not interested", "no", "stop", "remove", "don't call", "busy"],
            "neutral": ["maybe", "thinking", "consider", "let me", "need time"]
        }
        
        self.urgency_keywords = ["urgent", "quickly", "asap", "soon", "immediately", "deadline"]
        self.motivation_keywords = ["moving", "relocating", "divorce", "financial", "inherited", "estate"]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Analyze response content"""
        content = kwargs.get("content", "")
        channel = kwargs.get("channel", "email")
        context = kwargs.get("context", {})
        
        if not content:
            return {
                "success": False,
                "error": "No content provided for analysis"
            }
        
        try:
            # Perform comprehensive analysis
            analysis = await self._analyze_response(content, channel, context)
            
            return {
                "analysis_id": str(uuid.uuid4()),
                "sentiment": analysis["sentiment"],
                "interest_level": analysis["interest_level"],
                "urgency_level": analysis["urgency_level"],
                "key_points": analysis["key_points"],
                "objections": analysis["objections"],
                "questions": analysis["questions"],
                "motivation_signals": analysis["motivation_signals"],
                "recommended_actions": analysis["recommended_actions"],
                "confidence_score": analysis["confidence_score"],
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing response: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_response(self, content: str, channel: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform detailed response analysis"""
        content_lower = content.lower()
        
        # Sentiment analysis
        sentiment_score = self._calculate_sentiment(content_lower)
        
        # Interest level analysis
        interest_level = self._calculate_interest_level(content_lower)
        
        # Urgency analysis
        urgency_level = self._calculate_urgency_level(content_lower)
        
        # Extract key information
        key_points = self._extract_key_points(content)
        objections = self._identify_objections(content_lower)
        questions = self._extract_questions(content)
        motivation_signals = self._identify_motivation_signals(content_lower)
        
        # Generate recommendations
        recommended_actions = self._generate_recommendations(
            sentiment_score, interest_level, urgency_level, objections
        )
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(content, channel)
        
        return {
            "sentiment": {
                "score": sentiment_score,
                "label": self._sentiment_label(sentiment_score)
            },
            "interest_level": interest_level,
            "urgency_level": urgency_level,
            "key_points": key_points,
            "objections": objections,
            "questions": questions,
            "motivation_signals": motivation_signals,
            "recommended_actions": recommended_actions,
            "confidence_score": confidence_score
        }
    
    def _calculate_sentiment(self, content: str) -> float:
        """Calculate sentiment score (-1.0 to 1.0)"""
        positive_count = sum(1 for word in self.sentiment_keywords["positive"] if word in content)
        negative_count = sum(1 for word in self.sentiment_keywords["negative"] if word in content)
        neutral_count = sum(1 for word in self.sentiment_keywords["neutral"] if word in content)
        
        total_sentiment_words = positive_count + negative_count + neutral_count
        
        if total_sentiment_words == 0:
            return 0.0
        
        # Calculate weighted sentiment
        sentiment_score = (positive_count - negative_count) / total_sentiment_words
        return max(-1.0, min(1.0, sentiment_score))
    
    def _calculate_interest_level(self, content: str) -> float:
        """Calculate interest level (0.0 to 1.0)"""
        interest_indicators = [
            "interested", "tell me more", "how much", "when", "details",
            "sounds good", "yes", "okay", "sure", "maybe"
        ]
        
        disinterest_indicators = [
            "not interested", "no thanks", "not now", "busy", "stop"
        ]
        
        interest_count = sum(1 for indicator in interest_indicators if indicator in content)
        disinterest_count = sum(1 for indicator in disinterest_indicators if indicator in content)
        
        if interest_count == 0 and disinterest_count == 0:
            return 0.5  # Neutral
        
        total_indicators = interest_count + disinterest_count
        interest_level = interest_count / total_indicators if total_indicators > 0 else 0.5
        
        return max(0.0, min(1.0, interest_level))
    
    def _calculate_urgency_level(self, content: str) -> float:
        """Calculate urgency level (0.0 to 1.0)"""
        urgency_count = sum(1 for word in self.urgency_keywords if word in content)
        
        # Normalize based on content length
        content_words = len(content.split())
        if content_words == 0:
            return 0.0
        
        urgency_ratio = urgency_count / content_words
        urgency_level = min(1.0, urgency_ratio * 10)  # Scale up the ratio
        
        return urgency_level
    
    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from the response"""
        # Simple extraction based on sentence structure
        sentences = content.split('.')
        key_points = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Filter out very short sentences
                # Look for important sentence patterns
                if any(word in sentence.lower() for word in ["want", "need", "looking", "interested", "price", "when"]):
                    key_points.append(sentence)
        
        return key_points[:5]  # Return top 5 key points
    
    def _identify_objections(self, content: str) -> List[str]:
        """Identify objections in the response"""
        objection_patterns = [
            "too low", "not enough", "higher price", "more money",
            "not ready", "need time", "thinking about it",
            "other offers", "already listed", "with agent"
        ]
        
        objections = []
        for pattern in objection_patterns:
            if pattern in content:
                objections.append(pattern.replace("_", " ").title())
        
        return objections
    
    def _extract_questions(self, content: str) -> List[str]:
        """Extract questions from the response"""
        # Simple question extraction
        sentences = content.split('.')
        questions = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence.endswith('?') or any(word in sentence.lower() for word in ["what", "when", "where", "how", "why", "who"]):
                questions.append(sentence)
        
        return questions
    
    def _identify_motivation_signals(self, content: str) -> List[str]:
        """Identify seller motivation signals"""
        motivation_signals = []
        
        for keyword in self.motivation_keywords:
            if keyword in content:
                motivation_signals.append(keyword.title())
        
        return motivation_signals
    
    def _generate_recommendations(self, sentiment: float, interest: float, urgency: float, objections: List[str]) -> List[str]:
        """Generate recommended actions based on analysis"""
        recommendations = []
        
        if interest > 0.7:
            recommendations.append("Schedule immediate phone call")
            recommendations.append("Prepare detailed offer presentation")
        elif interest > 0.4:
            recommendations.append("Send follow-up with more information")
            recommendations.append("Address any concerns raised")
        else:
            recommendations.append("Add to long-term nurture campaign")
        
        if sentiment < -0.3:
            recommendations.append("Address negative sentiment with empathy")
            recommendations.append("Provide social proof and testimonials")
        
        if urgency > 0.5:
            recommendations.append("Respond within 2 hours")
            recommendations.append("Emphasize quick closing capability")
        
        if objections:
            recommendations.append("Prepare objection handling responses")
            recommendations.append("Provide market data to support position")
        
        return recommendations
    
    def _calculate_confidence_score(self, content: str, channel: str) -> float:
        """Calculate confidence score for the analysis"""
        # Base confidence on content length and channel
        content_length = len(content.split())
        
        if content_length < 5:
            return 0.3  # Low confidence for very short responses
        elif content_length < 20:
            return 0.6  # Medium confidence
        else:
            return 0.9  # High confidence for detailed responses
    
    def _sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label"""
        if score > 0.3:
            return "positive"
        elif score < -0.3:
            return "negative"
        else:
            return "neutral"


class NegotiationStrategyTool(BaseAgentTool):
    """Tool for generating negotiation strategies and tactics"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="negotiation_strategy",
            description="Generate negotiation strategies and tactics based on deal and seller analysis",
            category=ToolCategory.ANALYSIS,
            access_level=ToolAccessLevel.RESTRICTED,
            allowed_agents=["negotiator", "supervisor"],
            rate_limit=100,
            cost_per_call=0.08
        )
        super().__init__(metadata)
        
        # Strategy templates
        self.strategy_templates = {
            "collaborative": {
                "approach": "Win-win focused, relationship building",
                "tactics": ["market_data_support", "flexible_terms", "timeline_accommodation"],
                "initial_offer": 0.85
            },
            "competitive": {
                "approach": "Firm positioning, leverage-based",
                "tactics": ["time_pressure", "alternative_options", "firm_deadlines"],
                "initial_offer": 0.75
            },
            "accommodating": {
                "approach": "Seller-focused, flexible approach",
                "tactics": ["seller_benefits", "convenience_emphasis", "flexible_closing"],
                "initial_offer": 0.90
            }
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Generate negotiation strategy"""
        deal_data = kwargs.get("deal_data", {})
        seller_profile = kwargs.get("seller_profile", {})
        market_context = kwargs.get("market_context", {})
        
        if not deal_data:
            return {
                "success": False,
                "error": "Deal data is required for strategy generation"
            }
        
        try:
            strategy = await self._generate_strategy(deal_data, seller_profile, market_context)
            
            return {
                "strategy_id": str(uuid.uuid4()),
                "approach": strategy["approach"],
                "initial_offer_percentage": strategy["initial_offer_percentage"],
                "recommended_tactics": strategy["tactics"],
                "fallback_options": strategy["fallback_options"],
                "timeline_recommendations": strategy["timeline"],
                "risk_assessment": strategy["risk_assessment"],
                "success_probability": strategy["success_probability"],
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating negotiation strategy: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _generate_strategy(self, deal_data: Dict[str, Any], seller_profile: Dict[str, Any], market_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive negotiation strategy"""
        
        # Analyze seller motivation
        motivation_level = self._assess_motivation_level(seller_profile)
        
        # Determine optimal approach
        approach = self._select_approach(motivation_level, seller_profile, market_context)
        
        # Calculate offer parameters
        offer_params = self._calculate_offer_parameters(deal_data, market_context, approach)
        
        # Generate tactics
        tactics = self._select_tactics(approach, seller_profile, market_context)
        
        # Create timeline
        timeline = self._create_negotiation_timeline(motivation_level, market_context)
        
        # Assess risks
        risk_assessment = self._assess_negotiation_risks(deal_data, seller_profile, market_context)
        
        # Calculate success probability
        success_probability = self._calculate_success_probability(
            motivation_level, approach, market_context, risk_assessment
        )
        
        return {
            "approach": approach,
            "initial_offer_percentage": offer_params["initial_percentage"],
            "minimum_acceptable": offer_params["minimum_acceptable"],
            "maximum_offer": offer_params["maximum_offer"],
            "tactics": tactics["primary"],
            "fallback_options": tactics["fallback"],
            "timeline": timeline,
            "risk_assessment": risk_assessment,
            "success_probability": success_probability
        }
    
    def _assess_motivation_level(self, seller_profile: Dict[str, Any]) -> float:
        """Assess seller motivation level (0.0 to 1.0)"""
        motivation_indicators = seller_profile.get("motivation_indicators", [])
        
        high_motivation = ["foreclosure", "divorce", "job_relocation", "financial_distress"]
        medium_motivation = ["estate_sale", "downsizing", "upgrade"]
        low_motivation = ["testing_market", "curious"]
        
        high_count = sum(1 for indicator in motivation_indicators if indicator in high_motivation)
        medium_count = sum(1 for indicator in motivation_indicators if indicator in medium_motivation)
        low_count = sum(1 for indicator in motivation_indicators if indicator in low_motivation)
        
        total_indicators = high_count + medium_count + low_count
        
        if total_indicators == 0:
            return 0.5  # Neutral motivation
        
        motivation_score = (high_count * 1.0 + medium_count * 0.6 + low_count * 0.2) / total_indicators
        return min(1.0, motivation_score)
    
    def _select_approach(self, motivation_level: float, seller_profile: Dict[str, Any], market_context: Dict[str, Any]) -> str:
        """Select optimal negotiation approach"""
        market_temperature = market_context.get("market_temperature", "neutral")
        
        if motivation_level > 0.7:
            return "collaborative"  # High motivation - build relationship
        elif motivation_level < 0.3 and market_temperature == "hot":
            return "competitive"  # Low motivation in hot market - be firm
        else:
            return "accommodating"  # Default to accommodating approach
    
    def _calculate_offer_parameters(self, deal_data: Dict[str, Any], market_context: Dict[str, Any], approach: str) -> Dict[str, Any]:
        """Calculate offer parameters"""
        listing_price = deal_data.get("listing_price", 0)
        estimated_value = deal_data.get("estimated_value", listing_price)
        
        # Get base percentage from strategy template
        base_percentage = self.strategy_templates[approach]["initial_offer"]
        
        # Adjust based on market conditions
        market_temperature = market_context.get("market_temperature", "neutral")
        if market_temperature == "hot":
            base_percentage += 0.05  # Increase offer in hot market
        elif market_temperature == "cold":
            base_percentage -= 0.05  # Decrease offer in cold market
        
        # Calculate offer amounts
        initial_offer = estimated_value * base_percentage
        minimum_acceptable = estimated_value * (base_percentage - 0.10)
        maximum_offer = estimated_value * (base_percentage + 0.10)
        
        return {
            "initial_percentage": base_percentage,
            "initial_offer": initial_offer,
            "minimum_acceptable": minimum_acceptable,
            "maximum_offer": maximum_offer
        }
    
    def _select_tactics(self, approach: str, seller_profile: Dict[str, Any], market_context: Dict[str, Any]) -> Dict[str, Any]:
        """Select negotiation tactics"""
        base_tactics = self.strategy_templates[approach]["tactics"].copy()
        
        # Add situation-specific tactics
        additional_tactics = []
        fallback_tactics = []
        
        if "foreclosure" in seller_profile.get("motivation_indicators", []):
            additional_tactics.append("timeline_urgency")
            fallback_tactics.append("cash_advantage")
        
        if market_context.get("inventory_level") == "low":
            additional_tactics.append("market_scarcity")
        
        return {
            "primary": base_tactics + additional_tactics,
            "fallback": fallback_tactics + ["price_increase", "terms_flexibility"]
        }
    
    def _create_negotiation_timeline(self, motivation_level: float, market_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create negotiation timeline"""
        if motivation_level > 0.7:
            # High motivation - faster timeline
            return {
                "initial_response_hours": 2,
                "follow_up_intervals": [6, 24, 72],
                "decision_deadline_days": 7,
                "closing_timeline_days": 14
            }
        else:
            # Lower motivation - more patient approach
            return {
                "initial_response_hours": 24,
                "follow_up_intervals": [24, 72, 168],
                "decision_deadline_days": 14,
                "closing_timeline_days": 30
            }
    
    def _assess_negotiation_risks(self, deal_data: Dict[str, Any], seller_profile: Dict[str, Any], market_context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess negotiation risks"""
        risks = {
            "competition_risk": "medium",
            "price_escalation_risk": "low",
            "timeline_risk": "low",
            "seller_backing_out_risk": "low"
        }
        
        # Adjust risks based on context
        if market_context.get("market_temperature") == "hot":
            risks["competition_risk"] = "high"
            risks["price_escalation_risk"] = "high"
        
        if seller_profile.get("motivation_indicators", []):
            risks["seller_backing_out_risk"] = "low"
        else:
            risks["seller_backing_out_risk"] = "medium"
        
        return risks
    
    def _calculate_success_probability(self, motivation_level: float, approach: str, market_context: Dict[str, Any], risk_assessment: Dict[str, Any]) -> float:
        """Calculate probability of negotiation success"""
        base_probability = 0.6  # Base 60% success rate
        
        # Adjust for motivation
        base_probability += motivation_level * 0.3
        
        # Adjust for approach effectiveness
        if approach == "collaborative":
            base_probability += 0.1
        
        # Adjust for market conditions
        market_temp = market_context.get("market_temperature", "neutral")
        if market_temp == "cold":
            base_probability += 0.1
        elif market_temp == "hot":
            base_probability -= 0.1
        
        # Adjust for risks
        high_risk_count = sum(1 for risk in risk_assessment.values() if risk == "high")
        base_probability -= high_risk_count * 0.1
        
        return max(0.1, min(0.9, base_probability))


# Register negotiator tools with the global registry
def register_negotiator_tools():
    """Register all negotiator tools with the global tool registry"""
    from ..core.agent_tools import tool_registry
    
    tools = [
        EmailCommunicationTool(),
        SMSCommunicationTool(),
        VoiceCommunicationTool(),
        ResponseAnalysisTool(),
        NegotiationStrategyTool()
    ]
    
    for tool in tools:
        tool_registry.register_tool(tool)
    
    logger.info(f"Registered {len(tools)} negotiator tools")


# Auto-register tools when module is imported
register_negotiator_tools()