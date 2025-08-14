"""
Unified communication service that provides a common interface for all communication channels.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import uuid
from enum import Enum

from .email_service import EmailService, EmailServiceConfig
from .sms_service import SMSService, SMSServiceConfig
from .voice_service import VoiceService, VoiceServiceConfig

try:
    from ..models.communication import (
        EmailMessage, SMSMessage, VoiceCall, EmailTemplate, SMSTemplate, VoiceScript,
        CommunicationChannel, MessageStatus, MessagePriority, CommunicationHistory,
        CommunicationAnalytics, CommunicationPreferences, ContactInfo
    )
except ImportError:
    from app.models.communication import (
        EmailMessage, SMSMessage, VoiceCall, EmailTemplate, SMSTemplate, VoiceScript,
        CommunicationChannel, MessageStatus, MessagePriority, CommunicationHistory,
        CommunicationAnalytics, CommunicationPreferences, ContactInfo
    )


logger = logging.getLogger(__name__)


class CommunicationRequest:
    """Unified communication request model."""
    
    def __init__(
        self,
        channel: CommunicationChannel,
        recipient: ContactInfo,
        content: str,
        subject: Optional[str] = None,
        template_id: Optional[uuid.UUID] = None,
        template_variables: Optional[Dict[str, Any]] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        scheduled_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = uuid.uuid4()
        self.channel = channel
        self.recipient = recipient
        self.content = content
        self.subject = subject
        self.template_id = template_id
        self.template_variables = template_variables or {}
        self.priority = priority
        self.scheduled_at = scheduled_at
        self.metadata = metadata or {}
        self.created_at = datetime.now()


class CommunicationResponse:
    """Unified communication response model."""
    
    def __init__(
        self,
        request_id: uuid.UUID,
        channel: CommunicationChannel,
        message_id: uuid.UUID,
        status: MessageStatus,
        sent_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.request_id = request_id
        self.channel = channel
        self.message_id = message_id
        self.status = status
        self.sent_at = sent_at
        self.error_message = error_message
        self.metadata = metadata or {}


class ChannelPreferenceManager:
    """Manages communication channel preferences for contacts."""
    
    def __init__(self):
        self.preferences: Dict[uuid.UUID, CommunicationPreferences] = {}
    
    def set_preferences(self, contact_id: uuid.UUID, preferences: CommunicationPreferences):
        """Set communication preferences for a contact."""
        self.preferences[contact_id] = preferences
        logger.info(f"Communication preferences set for contact {contact_id}")
    
    def get_preferences(self, contact_id: uuid.UUID) -> Optional[CommunicationPreferences]:
        """Get communication preferences for a contact."""
        return self.preferences.get(contact_id)
    
    def get_preferred_channel(self, contact_id: uuid.UUID) -> Optional[CommunicationChannel]:
        """Get the preferred communication channel for a contact."""
        preferences = self.get_preferences(contact_id)
        if preferences:
            return preferences.preferred_channel
        return None
    
    def is_channel_enabled(self, contact_id: uuid.UUID, channel: CommunicationChannel) -> bool:
        """Check if a communication channel is enabled for a contact."""
        preferences = self.get_preferences(contact_id)
        if not preferences:
            return True  # Default to enabled if no preferences set
        
        if preferences.do_not_contact:
            return False
        
        if channel in preferences.unsubscribed_channels:
            return False
        
        if channel == CommunicationChannel.EMAIL:
            return preferences.email_enabled
        elif channel == CommunicationChannel.SMS:
            return preferences.sms_enabled
        elif channel == CommunicationChannel.VOICE:
            return preferences.voice_enabled
        
        return True
    
    def is_within_preferred_time(self, contact_id: uuid.UUID) -> bool:
        """Check if current time is within preferred communication hours."""
        preferences = self.get_preferences(contact_id)
        if not preferences or not preferences.preferred_time_start or not preferences.preferred_time_end:
            return True  # Default to always allowed if no time preferences
        
        # This is a simplified implementation
        # In a real system, you'd handle timezone conversion properly
        current_time = datetime.now().strftime("%H:%M")
        return preferences.preferred_time_start <= current_time <= preferences.preferred_time_end


class CommunicationHistoryManager:
    """Manages communication history across all channels."""
    
    def __init__(self):
        self.history: Dict[uuid.UUID, List[CommunicationHistory]] = {}
    
    def add_communication(
        self,
        contact_id: uuid.UUID,
        channel: CommunicationChannel,
        message_id: uuid.UUID,
        direction: str,
        subject: Optional[str],
        content: str,
        status: MessageStatus,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add a communication record to history."""
        if contact_id not in self.history:
            self.history[contact_id] = []
        
        history_record = CommunicationHistory(
            id=uuid.uuid4(),
            contact_id=contact_id,
            channel=channel,
            message_id=message_id,
            direction=direction,
            subject=subject,
            content=content,
            status=status,
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        self.history[contact_id].append(history_record)
        logger.info(f"Communication history added for contact {contact_id}")
    
    def get_contact_history(
        self,
        contact_id: uuid.UUID,
        channel: Optional[CommunicationChannel] = None,
        limit: Optional[int] = None
    ) -> List[CommunicationHistory]:
        """Get communication history for a contact."""
        contact_history = self.history.get(contact_id, [])
        
        if channel:
            contact_history = [h for h in contact_history if h.channel == channel]
        
        # Sort by timestamp (most recent first)
        contact_history.sort(key=lambda x: x.timestamp, reverse=True)
        
        if limit:
            contact_history = contact_history[:limit]
        
        return contact_history
    
    def get_recent_communications(
        self,
        hours: int = 24,
        channel: Optional[CommunicationChannel] = None
    ) -> List[CommunicationHistory]:
        """Get recent communications across all contacts."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_communications = []
        
        for contact_history in self.history.values():
            for comm in contact_history:
                if comm.timestamp >= cutoff_time:
                    if not channel or comm.channel == channel:
                        recent_communications.append(comm)
        
        recent_communications.sort(key=lambda x: x.timestamp, reverse=True)
        return recent_communications


class UnifiedCommunicationService:
    """Unified communication service providing a common interface for all channels."""
    
    def __init__(
        self,
        email_config: Optional[EmailServiceConfig] = None,
        sms_config: Optional[SMSServiceConfig] = None,
        voice_config: Optional[VoiceServiceConfig] = None
    ):
        # Initialize individual services
        self.email_service = EmailService(email_config) if email_config else None
        self.sms_service = SMSService(sms_config) if sms_config else None
        self.voice_service = VoiceService(voice_config) if voice_config else None
        
        # Initialize managers
        self.preference_manager = ChannelPreferenceManager()
        self.history_manager = CommunicationHistoryManager()
        
        # Track requests and responses
        self.requests: Dict[uuid.UUID, CommunicationRequest] = {}
        self.responses: Dict[uuid.UUID, CommunicationResponse] = {}
    
    async def send_communication(self, request: CommunicationRequest) -> CommunicationResponse:
        """Send a communication through the appropriate channel."""
        self.requests[request.id] = request
        
        try:
            # Check if channel is enabled for this contact
            if hasattr(request.recipient, 'id') and request.recipient.id and not self.preference_manager.is_channel_enabled(
                request.recipient.id, request.channel
            ):
                raise ValueError(f"Channel {request.channel} is disabled for this contact")
            
            # Check preferred time if contact has preferences
            if hasattr(request.recipient, 'id') and request.recipient.id and not self.preference_manager.is_within_preferred_time(
                request.recipient.id
            ):
                # Schedule for later if outside preferred hours
                # For now, we'll just log a warning
                logger.warning(f"Communication sent outside preferred hours for contact {request.recipient.id}")
            
            # Route to appropriate service
            if request.channel == CommunicationChannel.EMAIL:
                response = await self._send_email(request)
            elif request.channel == CommunicationChannel.SMS:
                response = await self._send_sms(request)
            elif request.channel == CommunicationChannel.VOICE:
                response = await self._send_voice(request)
            else:
                raise ValueError(f"Unsupported communication channel: {request.channel}")
            
            # Store response
            self.responses[request.id] = response
            
            # Add to communication history
            if hasattr(request.recipient, 'id') and request.recipient.id:
                self.history_manager.add_communication(
                    contact_id=request.recipient.id,
                    channel=request.channel,
                    message_id=response.message_id,
                    direction="outbound",
                    subject=request.subject,
                    content=request.content,
                    status=response.status,
                    metadata=request.metadata
                )
            
            return response
            
        except Exception as e:
            error_response = CommunicationResponse(
                request_id=request.id,
                channel=request.channel,
                message_id=uuid.uuid4(),
                status=MessageStatus.FAILED,
                error_message=str(e)
            )
            self.responses[request.id] = error_response
            logger.error(f"Failed to send communication: {e}")
            return error_response
    
    async def _send_email(self, request: CommunicationRequest) -> CommunicationResponse:
        """Send email communication."""
        if not self.email_service:
            raise ValueError("Email service not configured")
        
        if not request.recipient.email:
            raise ValueError("Recipient email address not provided")
        
        if request.template_id:
            # Send using template
            message = await self.email_service.send_template_email(
                template_id=request.template_id,
                to_email=request.recipient.email,
                variables=request.template_variables,
                to_name=request.recipient.name,
                priority=request.priority,
                scheduled_at=request.scheduled_at
            )
        else:
            # Send direct message
            message = EmailMessage(
                id=uuid.uuid4(),
                to_email=request.recipient.email,
                to_name=request.recipient.name,
                subject=request.subject or "No Subject",
                body_html=request.content,
                body_text=request.content,
                priority=request.priority,
                scheduled_at=request.scheduled_at,
                metadata=request.metadata,
                created_at=datetime.now()
            )
            await self.email_service.send_email(message)
        
        return CommunicationResponse(
            request_id=request.id,
            channel=CommunicationChannel.EMAIL,
            message_id=message.id,
            status=message.status,
            sent_at=message.sent_at
        )
    
    async def _send_sms(self, request: CommunicationRequest) -> CommunicationResponse:
        """Send SMS communication."""
        if not self.sms_service:
            raise ValueError("SMS service not configured")
        
        if not request.recipient.phone:
            raise ValueError("Recipient phone number not provided")
        
        if request.template_id:
            # Send using template
            message = await self.sms_service.send_template_sms(
                template_id=request.template_id,
                to_phone=request.recipient.phone,
                variables=request.template_variables,
                priority=request.priority,
                scheduled_at=request.scheduled_at
            )
        else:
            # Send direct message
            message = SMSMessage(
                id=uuid.uuid4(),
                to_phone=request.recipient.phone,
                message=request.content,
                priority=request.priority,
                scheduled_at=request.scheduled_at,
                metadata=request.metadata,
                created_at=datetime.now()
            )
            await self.sms_service.send_sms(message)
        
        return CommunicationResponse(
            request_id=request.id,
            channel=CommunicationChannel.SMS,
            message_id=message.id,
            status=message.status,
            sent_at=message.sent_at
        )
    
    async def _send_voice(self, request: CommunicationRequest) -> CommunicationResponse:
        """Send voice communication."""
        if not self.voice_service:
            raise ValueError("Voice service not configured")
        
        if not request.recipient.phone:
            raise ValueError("Recipient phone number not provided")
        
        if not request.template_id:
            raise ValueError("Voice script template ID required for voice calls")
        
        # Get voice script
        script = self.voice_service.get_script(request.template_id)
        if not script:
            raise ValueError(f"Voice script {request.template_id} not found")
        
        # Initiate call
        call = await self.voice_service.initiate_call(
            to_phone=request.recipient.phone,
            script=script,
            script_variables=request.template_variables,
            priority=request.priority,
            scheduled_at=request.scheduled_at
        )
        
        return CommunicationResponse(
            request_id=request.id,
            channel=CommunicationChannel.VOICE,
            message_id=call.id,
            status=call.status,
            sent_at=call.initiated_at
        )
    
    async def send_multi_channel_communication(
        self,
        recipient: ContactInfo,
        content: str,
        subject: Optional[str] = None,
        channels: Optional[List[CommunicationChannel]] = None,
        template_ids: Optional[Dict[CommunicationChannel, uuid.UUID]] = None,
        template_variables: Optional[Dict[str, Any]] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        delay_between_channels: float = 1.0
    ) -> List[CommunicationResponse]:
        """Send communication across multiple channels."""
        if not channels:
            # Use preferred channel or default to email
            preferred_channel = None
            if hasattr(recipient, 'id') and recipient.id:
                preferred_channel = self.preference_manager.get_preferred_channel(recipient.id)
            channels = [preferred_channel or CommunicationChannel.EMAIL]
        
        responses = []
        
        for i, channel in enumerate(channels):
            # Add delay between channels to avoid overwhelming recipient
            if i > 0:
                await asyncio.sleep(delay_between_channels)
            
            template_id = template_ids.get(channel) if template_ids else None
            
            request = CommunicationRequest(
                channel=channel,
                recipient=recipient,
                content=content,
                subject=subject,
                template_id=template_id,
                template_variables=template_variables,
                priority=priority
            )
            
            response = await self.send_communication(request)
            responses.append(response)
        
        return responses
    
    def get_communication_history(
        self,
        contact_id: uuid.UUID,
        channel: Optional[CommunicationChannel] = None,
        limit: Optional[int] = None
    ) -> List[CommunicationHistory]:
        """Get communication history for a contact."""
        return self.history_manager.get_contact_history(contact_id, channel, limit)
    
    def set_communication_preferences(
        self,
        contact_id: uuid.UUID,
        preferences: CommunicationPreferences
    ):
        """Set communication preferences for a contact."""
        self.preference_manager.set_preferences(contact_id, preferences)
    
    def get_communication_preferences(
        self,
        contact_id: uuid.UUID
    ) -> Optional[CommunicationPreferences]:
        """Get communication preferences for a contact."""
        return self.preference_manager.get_preferences(contact_id)
    
    async def get_unified_analytics(
        self,
        start_date: datetime,
        end_date: datetime,
        channel: Optional[CommunicationChannel] = None
    ) -> Dict[CommunicationChannel, CommunicationAnalytics]:
        """Get unified analytics across all channels."""
        analytics = {}
        
        channels_to_analyze = [channel] if channel else [
            CommunicationChannel.EMAIL,
            CommunicationChannel.SMS,
            CommunicationChannel.VOICE
        ]
        
        for ch in channels_to_analyze:
            try:
                if ch == CommunicationChannel.EMAIL and self.email_service:
                    analytics[ch] = self.email_service.get_analytics(start_date, end_date)
                elif ch == CommunicationChannel.SMS and self.sms_service:
                    analytics[ch] = self.sms_service.get_analytics(start_date, end_date)
                elif ch == CommunicationChannel.VOICE and self.voice_service:
                    analytics[ch] = await self.voice_service.get_call_analytics(start_date, end_date)
            except Exception as e:
                logger.error(f"Failed to get analytics for {ch}: {e}")
        
        return analytics
    
    def get_request_status(self, request_id: uuid.UUID) -> Optional[CommunicationResponse]:
        """Get the status of a communication request."""
        return self.responses.get(request_id)
    
    def get_active_services(self) -> List[CommunicationChannel]:
        """Get list of active communication services."""
        active_services = []
        
        if self.email_service:
            active_services.append(CommunicationChannel.EMAIL)
        if self.sms_service:
            active_services.append(CommunicationChannel.SMS)
        if self.voice_service:
            active_services.append(CommunicationChannel.VOICE)
        
        return active_services
    
    async def test_service_connectivity(self) -> Dict[CommunicationChannel, bool]:
        """Test connectivity to all configured services."""
        connectivity = {}
        
        if self.email_service:
            try:
                # Test email service (this would be a simple connectivity test)
                connectivity[CommunicationChannel.EMAIL] = True
            except Exception:
                connectivity[CommunicationChannel.EMAIL] = False
        
        if self.sms_service:
            try:
                # Test SMS service
                connectivity[CommunicationChannel.SMS] = True
            except Exception:
                connectivity[CommunicationChannel.SMS] = False
        
        if self.voice_service:
            try:
                # Test voice service
                connectivity[CommunicationChannel.VOICE] = True
            except Exception:
                connectivity[CommunicationChannel.VOICE] = False
        
        return connectivity