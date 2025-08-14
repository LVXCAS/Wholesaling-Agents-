"""
AI-powered message generation service for personalized outreach.
Implements Requirements 3.1 and 3.2 for automated, personalized communication.
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from pydantic import BaseModel

from ..models.communication import (
    EmailTemplate, SMSTemplate, VoiceScript, ContactInfo,
    CommunicationChannel, MessagePriority
)


class MessageType(str, Enum):
    """Types of messages that can be generated."""
    INITIAL_OUTREACH = "initial_outreach"
    FOLLOW_UP = "follow_up"
    APPOINTMENT_REQUEST = "appointment_request"
    OFFER_PRESENTATION = "offer_presentation"
    NEGOTIATION = "negotiation"
    CONTRACT_FOLLOW_UP = "contract_follow_up"
    THANK_YOU = "thank_you"


class MessageTone(str, Enum):
    """Tone options for message generation."""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    URGENT = "urgent"
    CASUAL = "casual"
    EMPATHETIC = "empathetic"


class PropertyContext(BaseModel):
    """Property context for message personalization."""
    address: str
    property_type: str
    estimated_value: Optional[float] = None
    condition: Optional[str] = None
    days_on_market: Optional[int] = None
    listing_price: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    year_built: Optional[int] = None
    neighborhood: Optional[str] = None
    motivation_indicators: List[str] = []


class SellerContext(BaseModel):
    """Seller context for message personalization."""
    name: Optional[str] = None
    situation: Optional[str] = None  # "divorce", "foreclosure", "relocation", etc.
    timeline: Optional[str] = None  # "urgent", "flexible", "no_rush"
    motivation_level: Optional[str] = None  # "high", "medium", "low"
    previous_interactions: List[str] = []
    preferred_contact_method: Optional[str] = None
    response_history: List[Dict[str, Any]] = []


class MarketContext(BaseModel):
    """Market context for message personalization."""
    market_trend: Optional[str] = None  # "hot", "balanced", "cold"
    average_days_on_market: Optional[int] = None
    price_trend: Optional[str] = None  # "rising", "stable", "declining"
    inventory_level: Optional[str] = None  # "low", "normal", "high"
    seasonal_factors: List[str] = []


class MessageGenerationRequest(BaseModel):
    """Request model for message generation."""
    message_type: MessageType
    channel: CommunicationChannel
    tone: MessageTone = MessageTone.PROFESSIONAL
    property_context: PropertyContext
    seller_context: SellerContext
    market_context: Optional[MarketContext] = None
    custom_variables: Optional[Dict[str, Any]] = None
    previous_messages: List[str] = []
    call_to_action: Optional[str] = None
    urgency_level: Optional[str] = None


class GeneratedMessage(BaseModel):
    """Generated message response."""
    id: uuid.UUID
    channel: CommunicationChannel
    message_type: MessageType
    subject: Optional[str] = None  # For email
    content: str
    variables_used: Dict[str, Any]
    personalization_score: float  # 0.0 to 1.0
    estimated_effectiveness: float  # 0.0 to 1.0
    suggested_send_time: Optional[datetime] = None
    follow_up_suggestions: List[str] = []
    created_at: datetime


class MessageGenerationService:
    """AI-powered message generation service."""
    
    def __init__(self, ai_service=None):
        """Initialize the message generation service."""
        self.ai_service = ai_service
        self.templates = self._load_base_templates()
        
    def generate_message(self, request: MessageGenerationRequest) -> GeneratedMessage:
        """
        Generate a personalized message based on the request.
        
        Args:
            request: Message generation request with context
            
        Returns:
            Generated message with personalization
        """
        # Generate personalized content based on channel
        if request.channel == CommunicationChannel.EMAIL:
            return self._generate_email_message(request)
        elif request.channel == CommunicationChannel.SMS:
            return self._generate_sms_message(request)
        elif request.channel == CommunicationChannel.VOICE:
            return self._generate_voice_script(request)
        else:
            raise ValueError(f"Unsupported channel: {request.channel}")
    
    def generate_follow_up_sequence(
        self, 
        initial_request: MessageGenerationRequest,
        sequence_length: int = 5
    ) -> List[GeneratedMessage]:
        """
        Generate a sequence of follow-up messages.
        
        Args:
            initial_request: Initial message request
            sequence_length: Number of follow-up messages to generate
            
        Returns:
            List of generated follow-up messages
        """
        messages = []
        
        for i in range(sequence_length):
            # Create follow-up request with escalating urgency
            follow_up_request = initial_request.model_copy()
            follow_up_request.message_type = MessageType.FOLLOW_UP
            follow_up_request.previous_messages = [msg.content for msg in messages]
            
            # Adjust tone and urgency based on sequence position
            if i == 0:
                follow_up_request.tone = MessageTone.FRIENDLY
            elif i < 2:
                follow_up_request.tone = MessageTone.PROFESSIONAL
            else:
                follow_up_request.tone = MessageTone.URGENT
                
            message = self.generate_message(follow_up_request)
            messages.append(message)
            
        return messages
    
    def _generate_email_message(self, request: MessageGenerationRequest) -> GeneratedMessage:
        """Generate personalized email message."""
        # Build context for AI generation
        context = self._build_message_context(request)
        
        # Generate subject line
        subject = self._generate_email_subject(request, context)
        
        # Generate email body
        content = self._generate_email_content(request, context)
        
        # Calculate personalization metrics
        personalization_score = self._calculate_personalization_score(content, context)
        effectiveness_score = self._estimate_effectiveness(request, content)
        
        return GeneratedMessage(
            id=uuid.uuid4(),
            channel=CommunicationChannel.EMAIL,
            message_type=request.message_type,
            subject=subject,
            content=content,
            variables_used=context,
            personalization_score=personalization_score,
            estimated_effectiveness=effectiveness_score,
            suggested_send_time=self._suggest_optimal_send_time(request),
            follow_up_suggestions=self._generate_follow_up_suggestions(request),
            created_at=datetime.now()
        )
    
    def _generate_sms_message(self, request: MessageGenerationRequest) -> GeneratedMessage:
        """Generate personalized SMS message."""
        context = self._build_message_context(request)
        
        # Generate concise SMS content (160 character limit consideration)
        content = self._generate_sms_content(request, context)
        
        personalization_score = self._calculate_personalization_score(content, context)
        effectiveness_score = self._estimate_effectiveness(request, content)
        
        return GeneratedMessage(
            id=uuid.uuid4(),
            channel=CommunicationChannel.SMS,
            message_type=request.message_type,
            content=content,
            variables_used=context,
            personalization_score=personalization_score,
            estimated_effectiveness=effectiveness_score,
            suggested_send_time=self._suggest_optimal_send_time(request),
            follow_up_suggestions=self._generate_follow_up_suggestions(request),
            created_at=datetime.now()
        )
    
    def _generate_voice_script(self, request: MessageGenerationRequest) -> GeneratedMessage:
        """Generate personalized voice script."""
        context = self._build_message_context(request)
        
        # Generate conversational voice script
        content = self._generate_voice_content(request, context)
        
        personalization_score = self._calculate_personalization_score(content, context)
        effectiveness_score = self._estimate_effectiveness(request, content)
        
        return GeneratedMessage(
            id=uuid.uuid4(),
            channel=CommunicationChannel.VOICE,
            message_type=request.message_type,
            content=content,
            variables_used=context,
            personalization_score=personalization_score,
            estimated_effectiveness=effectiveness_score,
            suggested_send_time=self._suggest_optimal_send_time(request),
            follow_up_suggestions=self._generate_follow_up_suggestions(request),
            created_at=datetime.now()
        )
    
    def _build_message_context(self, request: MessageGenerationRequest) -> Dict[str, Any]:
        """Build comprehensive context for message generation."""
        context = {
            "property_address": request.property_context.address,
            "property_type": request.property_context.property_type,
            "seller_name": request.seller_context.name or "Property Owner",
            "message_type": request.message_type.value,
            "tone": request.tone.value,
            "channel": request.channel.value
        }
        
        # Add property-specific context
        if request.property_context.estimated_value:
            context["estimated_value"] = f"${request.property_context.estimated_value:,.0f}"
        
        if request.property_context.condition:
            context["property_condition"] = request.property_context.condition
            
        if request.property_context.days_on_market:
            context["days_on_market"] = request.property_context.days_on_market
            
        # Add seller-specific context
        if request.seller_context.situation:
            context["seller_situation"] = request.seller_context.situation
            
        if request.seller_context.timeline:
            context["seller_timeline"] = request.seller_context.timeline
            
        # Add market context
        if request.market_context:
            context["market_trend"] = request.market_context.market_trend
            context["market_conditions"] = request.market_context.price_trend
            
        # Add custom variables
        if request.custom_variables:
            context.update(request.custom_variables)
            
        return context
    
    def _generate_email_subject(self, request: MessageGenerationRequest, context: Dict[str, Any]) -> str:
        """Generate compelling email subject line."""
        property_address = context.get("property_address", "your property")
        
        subject_templates = {
            MessageType.INITIAL_OUTREACH: [
                f"Quick question about {property_address}",
                f"Interested in {property_address}",
                f"Cash offer for {property_address}",
                f"Your property on {property_address.split(',')[0] if ',' in property_address else property_address}"
            ],
            MessageType.FOLLOW_UP: [
                f"Following up on {property_address}",
                f"Still interested in {property_address}",
                f"Quick update regarding {property_address}"
            ],
            MessageType.APPOINTMENT_REQUEST: [
                f"Can we schedule a quick call about {property_address}?",
                f"15-minute call about {property_address}?"
            ],
            MessageType.OFFER_PRESENTATION: [
                f"Cash offer ready for {property_address}",
                f"Formal offer for {property_address}"
            ]
        }
        
        templates = subject_templates.get(request.message_type, [f"Regarding {property_address}"])
        return templates[0]  # In a real implementation, this would use AI to select/generate
    
    def _generate_email_content(self, request: MessageGenerationRequest, context: Dict[str, Any]) -> str:
        """Generate personalized email content."""
        # This is a simplified version - in production, this would use advanced AI
        seller_name = context.get("seller_name", "Property Owner")
        property_address = context.get("property_address")
        
        if request.message_type == MessageType.INITIAL_OUTREACH:
            return f"""Hi {seller_name},

I hope this email finds you well. I'm reaching out regarding your property at {property_address}.

I'm a local real estate investor, and I'm interested in potentially purchasing your property. I work with cash buyers and can often close quickly if that would be helpful for your situation.

Would you be open to a brief conversation about your property? I'd be happy to discuss any questions you might have.

Best regards,
[Your Name]
[Your Phone]
[Your Email]"""

        elif request.message_type == MessageType.FOLLOW_UP:
            return f"""Hi {seller_name},

I wanted to follow up on my previous message about {property_address}. 

I understand you're probably busy, but I'm still very interested in your property and would love to discuss how I might be able to help with your situation.

If now isn't the right time, I completely understand. Please let me know if there's a better time to connect.

Best regards,
[Your Name]"""

        return f"Personalized message for {seller_name} regarding {property_address}"
    
    def _generate_sms_content(self, request: MessageGenerationRequest, context: Dict[str, Any]) -> str:
        """Generate concise SMS content."""
        seller_name = context.get("seller_name", "Property Owner")
        property_address = context.get("property_address")
        
        if request.message_type == MessageType.INITIAL_OUTREACH:
            return f"Hi {seller_name}, I'm interested in your property at {property_address}. Cash buyer, quick close possible. Can we chat briefly? Thanks!"
        
        elif request.message_type == MessageType.FOLLOW_UP:
            return f"Hi {seller_name}, following up on {property_address}. Still interested if you'd like to discuss. Thanks!"
        
        return f"Hi {seller_name}, regarding {property_address}. Let's connect!"
    
    def _generate_voice_content(self, request: MessageGenerationRequest, context: Dict[str, Any]) -> str:
        """Generate conversational voice script."""
        seller_name = context.get("seller_name", "Property Owner")
        property_address = context.get("property_address")
        
        if request.message_type == MessageType.INITIAL_OUTREACH:
            return f"""Hi, is this {seller_name}? 

My name is [Your Name], and I'm calling about your property at {property_address}. 

I'm a local real estate investor, and I'm interested in potentially purchasing your property. I work with cash buyers and can often close quickly.

Do you have a few minutes to chat about your property and your situation?

[PAUSE FOR RESPONSE]

Great! I'd love to learn more about your property and see if there's a way I can help with your situation."""

        elif request.message_type == MessageType.FOLLOW_UP:
            return f"""Hi {seller_name}, this is [Your Name] calling back about {property_address}.

I left a message earlier and wanted to follow up. I'm still very interested in your property.

Are you available for a quick conversation?

[PAUSE FOR RESPONSE]"""

        return f"Hi {seller_name}, calling about {property_address}. Let's discuss your options."
    
    def _calculate_personalization_score(self, content: str, context: Dict[str, Any]) -> float:
        """Calculate how personalized the message is (0.0 to 1.0)."""
        score = 0.0
        
        # Check for personal elements
        if context.get("seller_name", "Property Owner") != "Property Owner":
            score += 0.2
        
        if context.get("property_address") and context.get("property_address") in content:
            score += 0.2
            
        if context.get("seller_situation"):
            score += 0.2
            
        if context.get("property_condition"):
            score += 0.2
            
        if context.get("market_trend"):
            score += 0.2
            
        return min(score, 1.0)
    
    def _estimate_effectiveness(self, request: MessageGenerationRequest, content: str) -> float:
        """Estimate message effectiveness (0.0 to 1.0)."""
        # Simplified effectiveness estimation
        base_score = 0.5
        
        # Adjust based on message type
        if request.message_type == MessageType.INITIAL_OUTREACH:
            base_score += 0.1
        elif request.message_type == MessageType.FOLLOW_UP:
            base_score += 0.05
            
        # Adjust based on channel
        if request.channel == CommunicationChannel.EMAIL:
            base_score += 0.1
        elif request.channel == CommunicationChannel.SMS:
            base_score += 0.15
        elif request.channel == CommunicationChannel.VOICE:
            base_score += 0.2
            
        # Adjust based on tone
        if request.tone == MessageTone.FRIENDLY:
            base_score += 0.1
        elif request.tone == MessageTone.PROFESSIONAL:
            base_score += 0.05
            
        return min(base_score, 1.0)
    
    def _suggest_optimal_send_time(self, request: MessageGenerationRequest) -> datetime:
        """Suggest optimal time to send the message."""
        # Simplified logic - in production, this would consider recipient timezone,
        # historical response patterns, channel best practices, etc.
        now = datetime.now()
        
        if request.channel == CommunicationChannel.EMAIL:
            # Best email times: Tuesday-Thursday, 10 AM or 2 PM
            return now.replace(hour=10, minute=0, second=0, microsecond=0)
        elif request.channel == CommunicationChannel.SMS:
            # Best SMS times: 12-6 PM
            return now.replace(hour=14, minute=0, second=0, microsecond=0)
        elif request.channel == CommunicationChannel.VOICE:
            # Best call times: 10-11 AM or 4-5 PM
            return now.replace(hour=10, minute=30, second=0, microsecond=0)
            
        return now
    
    def _generate_follow_up_suggestions(self, request: MessageGenerationRequest) -> List[str]:
        """Generate suggestions for follow-up actions."""
        suggestions = []
        
        if request.message_type == MessageType.INITIAL_OUTREACH:
            suggestions.extend([
                "Send follow-up email in 3 days if no response",
                "Try different channel (SMS if email sent, email if SMS sent)",
                "Research additional property details for next contact"
            ])
        elif request.message_type == MessageType.FOLLOW_UP:
            suggestions.extend([
                "Wait 5-7 days before next follow-up",
                "Consider changing message tone or approach",
                "Try calling if previous messages were text-based"
            ])
            
        return suggestions
    
    def _load_base_templates(self) -> Dict[str, Any]:
        """Load base message templates."""
        # In production, these would be loaded from database
        return {
            "email_templates": {},
            "sms_templates": {},
            "voice_scripts": {}
        }


# Utility functions for message generation
def create_property_context(property_data: Dict[str, Any]) -> PropertyContext:
    """Create PropertyContext from property data dictionary."""
    return PropertyContext(**property_data)


def create_seller_context(seller_data: Dict[str, Any]) -> SellerContext:
    """Create SellerContext from seller data dictionary."""
    return SellerContext(**seller_data)


def create_market_context(market_data: Dict[str, Any]) -> MarketContext:
    """Create MarketContext from market data dictionary."""
    return MarketContext(**market_data)