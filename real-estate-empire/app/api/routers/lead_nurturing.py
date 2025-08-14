"""
API router for lead nurturing functionality.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...core.database import get_db
from ...models.scheduling import NurturingCampaign, EngagementTracking
from ...services.lead_nurturing_service import LeadNurturingService


router = APIRouter(prefix="/nurturing", tags=["nurturing"])


# Request/Response models
class CreateNurturingCampaignRequest(BaseModel):
    name: str
    description: Optional[str] = None
    target_lead_status: List[str] = []
    target_lead_score_min: Optional[float] = None
    target_lead_score_max: Optional[float] = None
    target_tags: List[str] = []
    content_sequence: List[Dict[str, Any]] = []
    frequency_days: int = 7
    max_duration_days: Optional[int] = None
    pause_on_engagement: bool = True


class UpdateNurturingCampaignRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_lead_status: Optional[List[str]] = None
    target_lead_score_min: Optional[float] = None
    target_lead_score_max: Optional[float] = None
    target_tags: Optional[List[str]] = None
    content_sequence: Optional[List[Dict[str, Any]]] = None
    frequency_days: Optional[int] = None
    max_duration_days: Optional[int] = None
    pause_on_engagement: Optional[bool] = None


class TrackEngagementRequest(BaseModel):
    engagement_type: str  # "email_sent", "email_opened", "email_clicked", etc.
    metadata: Optional[Dict[str, Any]] = None


def get_nurturing_service(db: Session = Depends(get_db)) -> LeadNurturingService:
    """Get lead nurturing service instance."""
    return LeadNurturingService(db)


# Campaign Management endpoints
@router.post("/campaigns", response_model=NurturingCampaign)
async def create_nurturing_campaign(
    request: CreateNurturingCampaignRequest,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Create a new nurturing campaign."""
    try:
        campaign = await service.create_nurturing_campaign(
            name=request.name,
            description=request.description,
            target_lead_status=request.target_lead_status,
            target_lead_score_min=request.target_lead_score_min,
            target_lead_score_max=request.target_lead_score_max,
            target_tags=request.target_tags,
            content_sequence=request.content_sequence,
            frequency_days=request.frequency_days,
            max_duration_days=request.max_duration_days,
            pause_on_engagement=request.pause_on_engagement
        )
        return campaign
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create nurturing campaign: {str(e)}")


@router.get("/campaigns/{campaign_id}", response_model=NurturingCampaign)
async def get_nurturing_campaign(
    campaign_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Get a nurturing campaign by ID."""
    campaign = await service.get_nurturing_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Nurturing campaign not found")
    return campaign


@router.put("/campaigns/{campaign_id}", response_model=NurturingCampaign)
async def update_nurturing_campaign(
    campaign_id: uuid.UUID,
    request: UpdateNurturingCampaignRequest,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Update a nurturing campaign."""
    updates = request.dict(exclude_unset=True)
    campaign = await service.update_nurturing_campaign(campaign_id, **updates)
    if not campaign:
        raise HTTPException(status_code=404, detail="Nurturing campaign not found")
    return campaign


@router.get("/campaigns", response_model=List[NurturingCampaign])
async def get_nurturing_campaigns(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    target_lead_status: Optional[str] = Query(None, description="Filter by target lead status"),
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Get nurturing campaigns with filtering."""
    campaigns = await service.get_nurturing_campaigns(
        is_active=is_active,
        target_lead_status=target_lead_status
    )
    return campaigns


@router.post("/campaigns/{campaign_id}/activate", response_model=NurturingCampaign)
async def activate_campaign(
    campaign_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Activate a nurturing campaign."""
    campaign = await service.activate_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Nurturing campaign not found")
    return campaign


@router.post("/campaigns/{campaign_id}/deactivate", response_model=NurturingCampaign)
async def deactivate_campaign(
    campaign_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Deactivate a nurturing campaign."""
    campaign = await service.deactivate_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Nurturing campaign not found")
    return campaign


# Contact Enrollment endpoints
@router.post("/campaigns/{campaign_id}/enroll/{contact_id}", response_model=EngagementTracking)
async def enroll_contact_in_campaign(
    campaign_id: uuid.UUID,
    contact_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Enroll a contact in a nurturing campaign."""
    try:
        engagement = await service.enroll_contact_in_campaign(contact_id, campaign_id)
        return engagement
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enroll contact: {str(e)}")


@router.get("/campaigns/{campaign_id}/contacts/{contact_id}/engagement", response_model=EngagementTracking)
async def get_contact_engagement(
    campaign_id: uuid.UUID,
    contact_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Get engagement tracking for a contact in a campaign."""
    engagement = await service.get_engagement_tracking(contact_id, campaign_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement tracking not found")
    return engagement


@router.post("/campaigns/{campaign_id}/contacts/{contact_id}/pause", response_model=EngagementTracking)
async def pause_contact_in_campaign(
    campaign_id: uuid.UUID,
    contact_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Pause a contact's participation in a campaign."""
    engagement = await service.pause_contact_in_campaign(contact_id, campaign_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement tracking not found")
    return engagement


@router.post("/campaigns/{campaign_id}/contacts/{contact_id}/resume", response_model=EngagementTracking)
async def resume_contact_in_campaign(
    campaign_id: uuid.UUID,
    contact_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Resume a contact's participation in a campaign."""
    engagement = await service.resume_contact_in_campaign(contact_id, campaign_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement tracking not found")
    return engagement


@router.post("/campaigns/{campaign_id}/contacts/{contact_id}/unsubscribe", response_model=EngagementTracking)
async def unsubscribe_contact_from_campaign(
    campaign_id: uuid.UUID,
    contact_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Unsubscribe a contact from a campaign."""
    engagement = await service.unsubscribe_contact_from_campaign(contact_id, campaign_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement tracking not found")
    return engagement


# Engagement Tracking endpoints
@router.post("/campaigns/{campaign_id}/contacts/{contact_id}/track/email-sent", response_model=EngagementTracking)
async def track_email_sent(
    campaign_id: uuid.UUID,
    contact_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Track that an email was sent to a contact."""
    engagement = await service.track_email_sent(contact_id, campaign_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement tracking not found")
    return engagement


@router.post("/campaigns/{campaign_id}/contacts/{contact_id}/track/email-opened", response_model=EngagementTracking)
async def track_email_opened(
    campaign_id: uuid.UUID,
    contact_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Track that an email was opened by a contact."""
    engagement = await service.track_email_opened(contact_id, campaign_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement tracking not found")
    return engagement


@router.post("/campaigns/{campaign_id}/contacts/{contact_id}/track/email-clicked", response_model=EngagementTracking)
async def track_email_clicked(
    campaign_id: uuid.UUID,
    contact_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Track that an email link was clicked by a contact."""
    engagement = await service.track_email_clicked(contact_id, campaign_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement tracking not found")
    return engagement


@router.post("/campaigns/{campaign_id}/contacts/{contact_id}/track/call-made", response_model=EngagementTracking)
async def track_call_made(
    campaign_id: uuid.UUID,
    contact_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Track that a call was made to a contact."""
    engagement = await service.track_call_made(contact_id, campaign_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement tracking not found")
    return engagement


@router.post("/campaigns/{campaign_id}/contacts/{contact_id}/track/call-answered", response_model=EngagementTracking)
async def track_call_answered(
    campaign_id: uuid.UUID,
    contact_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Track that a call was answered by a contact."""
    engagement = await service.track_call_answered(contact_id, campaign_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement tracking not found")
    return engagement


@router.post("/campaigns/{campaign_id}/contacts/{contact_id}/track/meeting-scheduled", response_model=EngagementTracking)
async def track_meeting_scheduled(
    campaign_id: uuid.UUID,
    contact_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Track that a meeting was scheduled with a contact."""
    engagement = await service.track_meeting_scheduled(contact_id, campaign_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement tracking not found")
    return engagement


@router.post("/campaigns/{campaign_id}/contacts/{contact_id}/track/meeting-attended", response_model=EngagementTracking)
async def track_meeting_attended(
    campaign_id: uuid.UUID,
    contact_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Track that a meeting was attended by a contact."""
    engagement = await service.track_meeting_attended(contact_id, campaign_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement tracking not found")
    return engagement


# Content and Recommendations endpoints
@router.get("/campaigns/{campaign_id}/contacts/{contact_id}/next-content")
async def get_next_content_for_contact(
    campaign_id: uuid.UUID,
    contact_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Get the next content item for a contact in a campaign."""
    content = await service.get_next_content_for_contact(contact_id, campaign_id)
    if not content:
        raise HTTPException(status_code=404, detail="No content available for contact")
    return content


@router.get("/campaigns/{campaign_id}/contacts/{contact_id}/should-send")
async def should_send_content(
    campaign_id: uuid.UUID,
    contact_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Check if content should be sent to a contact."""
    should_send = await service.should_send_content(contact_id, campaign_id)
    return {"should_send": should_send}


@router.get("/contacts/{contact_id}/content-recommendations")
async def get_content_recommendations(
    contact_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Get content recommendations for a contact."""
    recommendations = await service.create_content_recommendation_engine(contact_id)
    return {"recommendations": recommendations}


# Processing and Analytics endpoints
@router.post("/campaigns/process")
async def process_nurturing_campaigns(
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Process all active nurturing campaigns and send content."""
    stats = await service.process_nurturing_campaigns()
    return stats


@router.get("/campaigns/{campaign_id}/metrics")
async def get_campaign_performance_metrics(
    campaign_id: uuid.UUID,
    date_from: Optional[datetime] = Query(None, description="Start date for metrics"),
    date_to: Optional[datetime] = Query(None, description="End date for metrics"),
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Get performance metrics for a campaign."""
    metrics = await service.get_campaign_performance_metrics(
        campaign_id,
        date_from=date_from,
        date_to=date_to
    )
    return metrics


@router.get("/campaigns/{campaign_id}/recommendations")
async def get_content_optimization_recommendations(
    campaign_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Get content optimization recommendations for a campaign."""
    recommendations = await service.recommend_content_optimization(campaign_id)
    return {"recommendations": recommendations}


@router.get("/contacts/{contact_id}/engagement-history")
async def get_contact_engagement_history(
    contact_id: uuid.UUID,
    campaign_id: Optional[uuid.UUID] = Query(None, description="Filter by campaign"),
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Get engagement history for a contact."""
    history = await service.get_contact_engagement_history(contact_id, campaign_id)
    return {"engagement_history": history}


@router.post("/contacts/{contact_id}/update-lead-score")
async def update_lead_score_based_on_engagement(
    contact_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Update lead score based on engagement across all campaigns."""
    new_score = await service.update_lead_score_based_on_engagement(contact_id)
    return {"lead_score": new_score}


# Bulk operations
@router.post("/campaigns/{campaign_id}/enroll-bulk")
async def bulk_enroll_contacts(
    campaign_id: uuid.UUID,
    contact_ids: List[uuid.UUID],
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Bulk enroll contacts in a campaign."""
    results = []
    for contact_id in contact_ids:
        try:
            engagement = await service.enroll_contact_in_campaign(contact_id, campaign_id)
            results.append({"contact_id": contact_id, "status": "enrolled", "engagement": engagement})
        except Exception as e:
            results.append({"contact_id": contact_id, "status": "error", "error": str(e)})
    
    return {"results": results}


@router.get("/campaigns/{campaign_id}/eligible-contacts")
async def get_eligible_contacts_for_campaign(
    campaign_id: uuid.UUID,
    service: LeadNurturingService = Depends(get_nurturing_service)
):
    """Get contacts eligible for a nurturing campaign."""
    campaign = await service.get_nurturing_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Nurturing campaign not found")
    
    eligible_contacts = await service.get_eligible_contacts_for_campaign(campaign)
    return {"eligible_contacts": eligible_contacts}