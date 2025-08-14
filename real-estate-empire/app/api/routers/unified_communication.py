"""
API router for unified communication service.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ...services.unified_communication_service import (
    UnifiedCommunicationService, CommunicationRequest, CommunicationResponse
)
from ...services.email_service import EmailServiceConfig
from ...services.sms_service import SMSServiceConfig
from ...services.voice_service import VoiceServiceConfig
from ...models.communication import (
    CommunicationChannel, MessageStatus, MessagePriority, ContactInfo,
    CommunicationPreferences, CommunicationHistory, CommunicationAnalytics
)


# Request/Response models for API
class SendCommunicationRequest(BaseModel):
    """Request model for sending communication."""
    channel: CommunicationChannel
    recipient: ContactInfo
    content: str
    subject: Optional[str] = None
    template_id: Optional[uuid.UUID] = None
    template_variables: Optional[Dict[str, Any]] = None
    priority: MessagePriority = MessagePriority.NORMAL
    scheduled_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class SendMultiChannelRequest(BaseModel):
    """Request model for sending multi-channel communication."""
    recipient: ContactInfo
    content: str
    subject: Optional[str] = None
    channels: Optional[List[CommunicationChannel]] = None
    template_ids: Optional[Dict[CommunicationChannel, uuid.UUID]] = None
    template_variables: Optional[Dict[str, Any]] = None
    priority: MessagePriority = MessagePriority.NORMAL
    delay_between_channels: float = 1.0


class CommunicationStatusResponse(BaseModel):
    """Response model for communication status."""
    request_id: uuid.UUID
    channel: CommunicationChannel
    message_id: uuid.UUID
    status: MessageStatus
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AnalyticsRequest(BaseModel):
    """Request model for analytics."""
    start_date: datetime
    end_date: datetime
    channel: Optional[CommunicationChannel] = None


# Create router
router = APIRouter(prefix="/api/communication", tags=["communication"])


# Global service instance for dependency injection
_communication_service: Optional[UnifiedCommunicationService] = None

def get_communication_service() -> UnifiedCommunicationService:
    """Get unified communication service instance."""
    global _communication_service
    
    if _communication_service is None:
        # In a real application, this would be configured with proper credentials
        email_config = EmailServiceConfig(
            smtp_host="smtp.gmail.com",
            smtp_username="test@example.com",
            smtp_password="password",
            default_from_email="test@example.com"
        )
        
        sms_config = SMSServiceConfig(
            twilio_account_sid="test_sid",
            twilio_auth_token="test_token",
            default_from_phone="+15551234567"
        )
        
        voice_config = VoiceServiceConfig(
            twilio_account_sid="test_sid",
            twilio_auth_token="test_token",
            default_from_phone="+15551234567",
            webhook_base_url="https://api.example.com"
        )
        
        _communication_service = UnifiedCommunicationService(
            email_config=email_config,
            sms_config=sms_config,
            voice_config=voice_config
        )
    
    return _communication_service

def set_communication_service(service: UnifiedCommunicationService):
    """Set the communication service instance (for testing)."""
    global _communication_service
    _communication_service = service


@router.post("/send", response_model=CommunicationStatusResponse)
async def send_communication(
    request: SendCommunicationRequest,
    service: UnifiedCommunicationService = Depends(get_communication_service)
):
    """Send a communication through the specified channel."""
    try:
        comm_request = CommunicationRequest(
            channel=request.channel,
            recipient=request.recipient,
            content=request.content,
            subject=request.subject,
            template_id=request.template_id,
            template_variables=request.template_variables,
            priority=request.priority,
            scheduled_at=request.scheduled_at,
            metadata=request.metadata
        )
        
        response = await service.send_communication(comm_request)
        
        return CommunicationStatusResponse(
            request_id=response.request_id,
            channel=response.channel,
            message_id=response.message_id,
            status=response.status,
            sent_at=response.sent_at,
            error_message=response.error_message,
            metadata=response.metadata
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/send-multi-channel", response_model=List[CommunicationStatusResponse])
async def send_multi_channel_communication(
    request: SendMultiChannelRequest,
    service: UnifiedCommunicationService = Depends(get_communication_service)
):
    """Send communication across multiple channels."""
    try:
        responses = await service.send_multi_channel_communication(
            recipient=request.recipient,
            content=request.content,
            subject=request.subject,
            channels=request.channels,
            template_ids=request.template_ids,
            template_variables=request.template_variables,
            priority=request.priority,
            delay_between_channels=request.delay_between_channels
        )
        
        return [
            CommunicationStatusResponse(
                request_id=response.request_id,
                channel=response.channel,
                message_id=response.message_id,
                status=response.status,
                sent_at=response.sent_at,
                error_message=response.error_message,
                metadata=response.metadata
            )
            for response in responses
        ]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status/{request_id}", response_model=CommunicationStatusResponse)
async def get_communication_status(
    request_id: uuid.UUID,
    service: UnifiedCommunicationService = Depends(get_communication_service)
):
    """Get the status of a communication request."""
    response = service.get_request_status(request_id)
    
    if not response:
        raise HTTPException(status_code=404, detail="Communication request not found")
    
    return CommunicationStatusResponse(
        request_id=response.request_id,
        channel=response.channel,
        message_id=response.message_id,
        status=response.status,
        sent_at=response.sent_at,
        error_message=response.error_message,
        metadata=response.metadata
    )


@router.get("/history/{contact_id}", response_model=List[CommunicationHistory])
async def get_communication_history(
    contact_id: uuid.UUID,
    channel: Optional[CommunicationChannel] = None,
    limit: Optional[int] = None,
    service: UnifiedCommunicationService = Depends(get_communication_service)
):
    """Get communication history for a contact."""
    try:
        history = service.get_communication_history(contact_id, channel, limit)
        return history
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/preferences/{contact_id}")
async def set_communication_preferences(
    contact_id: uuid.UUID,
    preferences: CommunicationPreferences,
    service: UnifiedCommunicationService = Depends(get_communication_service)
):
    """Set communication preferences for a contact."""
    try:
        service.set_communication_preferences(contact_id, preferences)
        return {"message": "Preferences updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/preferences/{contact_id}", response_model=CommunicationPreferences)
async def get_communication_preferences(
    contact_id: uuid.UUID,
    service: UnifiedCommunicationService = Depends(get_communication_service)
):
    """Get communication preferences for a contact."""
    preferences = service.get_communication_preferences(contact_id)
    
    if not preferences:
        raise HTTPException(status_code=404, detail="Preferences not found")
    
    return preferences


@router.post("/analytics", response_model=Dict[CommunicationChannel, CommunicationAnalytics])
async def get_communication_analytics(
    request: AnalyticsRequest,
    service: UnifiedCommunicationService = Depends(get_communication_service)
):
    """Get communication analytics."""
    try:
        analytics = await service.get_unified_analytics(
            start_date=request.start_date,
            end_date=request.end_date,
            channel=request.channel
        )
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/services", response_model=List[CommunicationChannel])
async def get_active_services(
    service: UnifiedCommunicationService = Depends(get_communication_service)
):
    """Get list of active communication services."""
    return service.get_active_services()


@router.get("/connectivity", response_model=Dict[CommunicationChannel, bool])
async def test_service_connectivity(
    service: UnifiedCommunicationService = Depends(get_communication_service)
):
    """Test connectivity to all configured services."""
    try:
        connectivity = await service.test_service_connectivity()
        return connectivity
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "unified_communication"}