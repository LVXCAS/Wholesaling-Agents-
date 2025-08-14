"""
Lead nurturing service for managing long-term nurturing campaigns and engagement tracking.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid
import asyncio
from sqlalchemy.orm import Session

from ..models.scheduling import (
    NurturingCampaign, EngagementTracking
)
from ..models.communication import CommunicationChannel
from ..core.database import get_db


class LeadNurturingService:
    """Service for managing lead nurturing campaigns and engagement tracking."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_nurturing_campaign(
        self,
        name: str,
        description: Optional[str] = None,
        target_lead_status: List[str] = None,
        target_lead_score_min: Optional[float] = None,
        target_lead_score_max: Optional[float] = None,
        target_tags: List[str] = None,
        content_sequence: List[Dict[str, Any]] = None,
        frequency_days: int = 7,
        max_duration_days: Optional[int] = None,
        pause_on_engagement: bool = True
    ) -> NurturingCampaign:
        """Create a new nurturing campaign."""
        
        campaign = NurturingCampaign(
            id=uuid.uuid4(),
            name=name,
            description=description,
            target_lead_status=target_lead_status or [],
            target_lead_score_min=target_lead_score_min,
            target_lead_score_max=target_lead_score_max,
            target_tags=target_tags or [],
            content_sequence=content_sequence or [],
            frequency_days=frequency_days,
            max_duration_days=max_duration_days,
            pause_on_engagement=pause_on_engagement,
            created_at=datetime.utcnow()
        )
        
        return campaign
    
    async def get_nurturing_campaign(self, campaign_id: uuid.UUID) -> Optional[NurturingCampaign]:
        """Get a nurturing campaign by ID."""
        # This would query the database for the campaign
        # For now, returning None as placeholder
        return None
    
    async def update_nurturing_campaign(
        self,
        campaign_id: uuid.UUID,
        **updates
    ) -> Optional[NurturingCampaign]:
        """Update a nurturing campaign."""
        campaign = await self.get_nurturing_campaign(campaign_id)
        if not campaign:
            return None
        
        # Update fields
        for key, value in updates.items():
            if hasattr(campaign, key):
                setattr(campaign, key, value)
        
        return campaign
    
    async def get_nurturing_campaigns(
        self,
        is_active: Optional[bool] = None,
        target_lead_status: Optional[str] = None
    ) -> List[NurturingCampaign]:
        """Get nurturing campaigns with filtering."""
        # This would query the database with filters
        # For now, returning empty list as placeholder
        return []
    
    async def activate_campaign(self, campaign_id: uuid.UUID) -> Optional[NurturingCampaign]:
        """Activate a nurturing campaign."""
        return await self.update_nurturing_campaign(campaign_id, is_active=True)
    
    async def deactivate_campaign(self, campaign_id: uuid.UUID) -> Optional[NurturingCampaign]:
        """Deactivate a nurturing campaign."""
        return await self.update_nurturing_campaign(campaign_id, is_active=False)
    
    async def enroll_contact_in_campaign(
        self,
        contact_id: uuid.UUID,
        campaign_id: uuid.UUID
    ) -> EngagementTracking:
        """Enroll a contact in a nurturing campaign."""
        
        engagement = EngagementTracking(
            id=uuid.uuid4(),
            contact_id=contact_id,
            campaign_id=campaign_id,
            started_at=datetime.utcnow(),
            campaign_status="active"
        )
        
        return engagement
    
    async def get_engagement_tracking(
        self,
        contact_id: uuid.UUID,
        campaign_id: uuid.UUID
    ) -> Optional[EngagementTracking]:
        """Get engagement tracking for a contact in a campaign."""
        # This would query the database for engagement tracking
        # For now, returning None as placeholder
        return None
    
    async def update_engagement_tracking(
        self,
        contact_id: uuid.UUID,
        campaign_id: uuid.UUID,
        **updates
    ) -> Optional[EngagementTracking]:
        """Update engagement tracking."""
        engagement = await self.get_engagement_tracking(contact_id, campaign_id)
        if not engagement:
            return None
        
        # Update fields
        for key, value in updates.items():
            if hasattr(engagement, key):
                setattr(engagement, key, value)
        
        engagement.last_updated_at = datetime.utcnow()
        return engagement
    
    async def track_email_sent(
        self,
        contact_id: uuid.UUID,
        campaign_id: uuid.UUID
    ) -> Optional[EngagementTracking]:
        """Track that an email was sent to a contact."""
        engagement = await self.get_engagement_tracking(contact_id, campaign_id)
        if not engagement:
            return None
        
        engagement.emails_sent += 1
        engagement.last_updated_at = datetime.utcnow()
        
        return engagement
    
    async def track_email_opened(
        self,
        contact_id: uuid.UUID,
        campaign_id: uuid.UUID
    ) -> Optional[EngagementTracking]:
        """Track that an email was opened by a contact."""
        engagement = await self.get_engagement_tracking(contact_id, campaign_id)
        if not engagement:
            return None
        
        engagement.emails_opened += 1
        engagement.last_engagement_date = datetime.utcnow()
        engagement.last_updated_at = datetime.utcnow()
        
        # Update engagement score
        await self.update_engagement_score(engagement)
        
        return engagement
    
    async def track_email_clicked(
        self,
        contact_id: uuid.UUID,
        campaign_id: uuid.UUID
    ) -> Optional[EngagementTracking]:
        """Track that an email link was clicked by a contact."""
        engagement = await self.get_engagement_tracking(contact_id, campaign_id)
        if not engagement:
            return None
        
        engagement.emails_clicked += 1
        engagement.last_engagement_date = datetime.utcnow()
        engagement.last_updated_at = datetime.utcnow()
        
        # Update engagement score
        await self.update_engagement_score(engagement)
        
        return engagement
    
    async def track_call_made(
        self,
        contact_id: uuid.UUID,
        campaign_id: uuid.UUID
    ) -> Optional[EngagementTracking]:
        """Track that a call was made to a contact."""
        engagement = await self.get_engagement_tracking(contact_id, campaign_id)
        if not engagement:
            return None
        
        engagement.calls_made += 1
        engagement.last_updated_at = datetime.utcnow()
        
        return engagement
    
    async def track_call_answered(
        self,
        contact_id: uuid.UUID,
        campaign_id: uuid.UUID
    ) -> Optional[EngagementTracking]:
        """Track that a call was answered by a contact."""
        engagement = await self.get_engagement_tracking(contact_id, campaign_id)
        if not engagement:
            return None
        
        engagement.calls_answered += 1
        engagement.last_engagement_date = datetime.utcnow()
        engagement.last_updated_at = datetime.utcnow()
        
        # Update engagement score
        await self.update_engagement_score(engagement)
        
        return engagement
    
    async def track_meeting_scheduled(
        self,
        contact_id: uuid.UUID,
        campaign_id: uuid.UUID
    ) -> Optional[EngagementTracking]:
        """Track that a meeting was scheduled with a contact."""
        engagement = await self.get_engagement_tracking(contact_id, campaign_id)
        if not engagement:
            return None
        
        engagement.meetings_scheduled += 1
        engagement.last_engagement_date = datetime.utcnow()
        engagement.last_updated_at = datetime.utcnow()
        
        # Update engagement score
        await self.update_engagement_score(engagement)
        
        return engagement
    
    async def track_meeting_attended(
        self,
        contact_id: uuid.UUID,
        campaign_id: uuid.UUID
    ) -> Optional[EngagementTracking]:
        """Track that a meeting was attended by a contact."""
        engagement = await self.get_engagement_tracking(contact_id, campaign_id)
        if not engagement:
            return None
        
        engagement.meetings_attended += 1
        engagement.last_engagement_date = datetime.utcnow()
        engagement.last_updated_at = datetime.utcnow()
        
        # Update engagement score
        await self.update_engagement_score(engagement)
        
        return engagement
    
    async def update_engagement_score(self, engagement: EngagementTracking) -> float:
        """Calculate and update engagement score based on activities."""
        
        # Define scoring weights for different activities
        weights = {
            "email_open": 1.0,
            "email_click": 2.0,
            "call_answered": 3.0,
            "meeting_scheduled": 5.0,
            "meeting_attended": 8.0
        }
        
        # Calculate base score from activities
        score = 0.0
        score += engagement.emails_opened * weights["email_open"]
        score += engagement.emails_clicked * weights["email_click"]
        score += engagement.calls_answered * weights["call_answered"]
        score += engagement.meetings_scheduled * weights["meeting_scheduled"]
        score += engagement.meetings_attended * weights["meeting_attended"]
        
        # Apply time decay (recent engagement is more valuable)
        if engagement.last_engagement_date:
            days_since_engagement = (datetime.utcnow() - engagement.last_engagement_date).days
            decay_factor = max(0.1, 1.0 - (days_since_engagement * 0.02))  # 2% decay per day, min 10%
            score *= decay_factor
        
        # Apply frequency bonus (consistent engagement is valuable)
        total_activities = (engagement.emails_opened + engagement.emails_clicked + 
                          engagement.calls_answered + engagement.meetings_scheduled + 
                          engagement.meetings_attended)
        
        if total_activities > 0:
            days_active = (datetime.utcnow() - engagement.started_at).days + 1
            frequency = total_activities / days_active
            frequency_bonus = min(frequency * 0.5, 2.0)  # Max 2 point bonus
            score += frequency_bonus
        
        # Normalize score to 0-100 range
        engagement.engagement_score = min(score, 100.0)
        
        return engagement.engagement_score
    
    async def get_eligible_contacts_for_campaign(
        self,
        campaign: NurturingCampaign
    ) -> List[uuid.UUID]:
        """Get contacts eligible for a nurturing campaign."""
        # This would query the database for eligible contacts based on campaign criteria
        # For now, returning empty list as placeholder
        return []
    
    async def get_next_content_for_contact(
        self,
        contact_id: uuid.UUID,
        campaign_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """Get the next content item for a contact in a campaign."""
        campaign = await self.get_nurturing_campaign(campaign_id)
        engagement = await self.get_engagement_tracking(contact_id, campaign_id)
        
        if not campaign or not engagement or not campaign.content_sequence:
            return None
        
        # Calculate which content item should be sent next
        days_in_campaign = (datetime.utcnow() - engagement.started_at).days
        content_index = days_in_campaign // campaign.frequency_days
        
        if content_index >= len(campaign.content_sequence):
            # Campaign completed or should repeat
            if campaign.max_duration_days:
                max_content_cycles = campaign.max_duration_days // campaign.frequency_days
                if content_index >= max_content_cycles:
                    return None  # Campaign completed
            
            # Repeat content sequence
            content_index = content_index % len(campaign.content_sequence)
        
        return campaign.content_sequence[content_index]
    
    async def should_send_content(
        self,
        contact_id: uuid.UUID,
        campaign_id: uuid.UUID
    ) -> bool:
        """Check if content should be sent to a contact."""
        campaign = await self.get_nurturing_campaign(campaign_id)
        engagement = await self.get_engagement_tracking(contact_id, campaign_id)
        
        if not campaign or not engagement:
            return False
        
        if not campaign.is_active or engagement.campaign_status != "active":
            return False
        
        # Check if campaign should be paused due to recent engagement
        if campaign.pause_on_engagement and engagement.last_engagement_date:
            days_since_engagement = (datetime.utcnow() - engagement.last_engagement_date).days
            if days_since_engagement < campaign.frequency_days:
                return False
        
        # Check if it's time for next content
        days_in_campaign = (datetime.utcnow() - engagement.started_at).days
        
        # Content should be sent at intervals of frequency_days
        # After 8 days with 7-day frequency, we should send content (8 >= 7)
        return days_in_campaign >= campaign.frequency_days
    
    async def process_nurturing_campaigns(self) -> Dict[str, int]:
        """Process all active nurturing campaigns and send content."""
        
        campaigns = await self.get_nurturing_campaigns(is_active=True)
        
        stats = {
            "campaigns_processed": 0,
            "contacts_processed": 0,
            "content_sent": 0,
            "errors": 0
        }
        
        for campaign in campaigns:
            try:
                stats["campaigns_processed"] += 1
                
                # Get eligible contacts for this campaign
                eligible_contacts = await self.get_eligible_contacts_for_campaign(campaign)
                
                for contact_id in eligible_contacts:
                    try:
                        stats["contacts_processed"] += 1
                        
                        # Check if content should be sent
                        if await self.should_send_content(contact_id, campaign.id):
                            content = await self.get_next_content_for_contact(contact_id, campaign.id)
                            
                            if content:
                                # Send the content (this would integrate with communication services)
                                await self.send_nurturing_content(contact_id, campaign.id, content)
                                stats["content_sent"] += 1
                    
                    except Exception as e:
                        print(f"Error processing contact {contact_id} in campaign {campaign.id}: {e}")
                        stats["errors"] += 1
            
            except Exception as e:
                print(f"Error processing campaign {campaign.id}: {e}")
                stats["errors"] += 1
        
        return stats
    
    async def send_nurturing_content(
        self,
        contact_id: uuid.UUID,
        campaign_id: uuid.UUID,
        content: Dict[str, Any]
    ) -> bool:
        """Send nurturing content to a contact."""
        
        content_type = content.get("type", "email")
        
        try:
            if content_type == "email":
                # Send email content
                await self.send_nurturing_email(contact_id, campaign_id, content)
                await self.track_email_sent(contact_id, campaign_id)
            
            elif content_type == "sms":
                # Send SMS content
                await self.send_nurturing_sms(contact_id, campaign_id, content)
            
            elif content_type == "call":
                # Schedule a call
                await self.schedule_nurturing_call(contact_id, campaign_id, content)
            
            return True
        
        except Exception as e:
            print(f"Error sending nurturing content: {e}")
            return False
    
    async def send_nurturing_email(
        self,
        contact_id: uuid.UUID,
        campaign_id: uuid.UUID,
        content: Dict[str, Any]
    ):
        """Send nurturing email content."""
        # This would integrate with email service
        # For now, just a placeholder
        pass
    
    async def send_nurturing_sms(
        self,
        contact_id: uuid.UUID,
        campaign_id: uuid.UUID,
        content: Dict[str, Any]
    ):
        """Send nurturing SMS content."""
        # This would integrate with SMS service
        # For now, just a placeholder
        pass
    
    async def schedule_nurturing_call(
        self,
        contact_id: uuid.UUID,
        campaign_id: uuid.UUID,
        content: Dict[str, Any]
    ):
        """Schedule a nurturing call."""
        # This would integrate with appointment scheduling service
        # For now, just a placeholder
        pass
    
    async def pause_contact_in_campaign(
        self,
        contact_id: uuid.UUID,
        campaign_id: uuid.UUID
    ) -> Optional[EngagementTracking]:
        """Pause a contact's participation in a campaign."""
        return await self.update_engagement_tracking(
            contact_id,
            campaign_id,
            campaign_status="paused"
        )
    
    async def resume_contact_in_campaign(
        self,
        contact_id: uuid.UUID,
        campaign_id: uuid.UUID
    ) -> Optional[EngagementTracking]:
        """Resume a contact's participation in a campaign."""
        return await self.update_engagement_tracking(
            contact_id,
            campaign_id,
            campaign_status="active"
        )
    
    async def unsubscribe_contact_from_campaign(
        self,
        contact_id: uuid.UUID,
        campaign_id: uuid.UUID
    ) -> Optional[EngagementTracking]:
        """Unsubscribe a contact from a campaign."""
        return await self.update_engagement_tracking(
            contact_id,
            campaign_id,
            campaign_status="unsubscribed"
        )
    
    async def get_campaign_performance_metrics(
        self,
        campaign_id: uuid.UUID,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get performance metrics for a campaign."""
        
        # This would calculate metrics from database
        # For now, returning sample metrics
        return {
            "total_contacts": 0,
            "active_contacts": 0,
            "paused_contacts": 0,
            "unsubscribed_contacts": 0,
            "total_emails_sent": 0,
            "total_emails_opened": 0,
            "total_emails_clicked": 0,
            "total_calls_made": 0,
            "total_calls_answered": 0,
            "total_meetings_scheduled": 0,
            "total_meetings_attended": 0,
            "average_engagement_score": 0.0,
            "open_rate": 0.0,
            "click_rate": 0.0,
            "call_answer_rate": 0.0,
            "meeting_attendance_rate": 0.0,
            "conversion_rate": 0.0
        }
    
    async def get_contact_engagement_history(
        self,
        contact_id: uuid.UUID,
        campaign_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get engagement history for a contact."""
        
        # This would query engagement history from database
        # For now, returning empty list as placeholder
        return []
    
    async def recommend_content_optimization(
        self,
        campaign_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Recommend content optimizations based on performance."""
        
        metrics = await self.get_campaign_performance_metrics(campaign_id)
        recommendations = []
        
        # Analyze performance and generate recommendations
        if metrics["open_rate"] < 0.2:  # Less than 20% open rate
            recommendations.append({
                "type": "subject_line",
                "priority": "high",
                "message": "Low email open rate detected. Consider A/B testing different subject lines.",
                "suggested_actions": [
                    "Test personalized subject lines",
                    "Try shorter subject lines",
                    "Use urgency or curiosity in subject lines"
                ]
            })
        
        if metrics["click_rate"] < 0.05:  # Less than 5% click rate
            recommendations.append({
                "type": "content",
                "priority": "medium",
                "message": "Low click-through rate. Content may not be engaging enough.",
                "suggested_actions": [
                    "Add more compelling call-to-action buttons",
                    "Include more valuable content",
                    "Segment content based on lead interests"
                ]
            })
        
        if metrics["call_answer_rate"] < 0.3:  # Less than 30% call answer rate
            recommendations.append({
                "type": "timing",
                "priority": "medium",
                "message": "Low call answer rate. Consider adjusting call timing.",
                "suggested_actions": [
                    "Try calling at different times of day",
                    "Send a pre-call email or SMS",
                    "Use local phone numbers"
                ]
            })
        
        return recommendations
    
    async def create_content_recommendation_engine(
        self,
        contact_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Recommend content based on contact behavior and preferences."""
        
        # This would analyze contact behavior and recommend content
        # For now, returning sample recommendations
        return [
            {
                "content_type": "email",
                "subject": "Market Update for Your Area",
                "priority": "high",
                "reason": "Contact has shown interest in market trends",
                "best_send_time": "Tuesday 10:00 AM"
            },
            {
                "content_type": "call",
                "topic": "Investment Opportunity Discussion",
                "priority": "medium",
                "reason": "Contact has high engagement score",
                "best_call_time": "Wednesday 2:00 PM"
            }
        ]
    
    async def update_lead_score_based_on_engagement(
        self,
        contact_id: uuid.UUID
    ) -> float:
        """Update lead score based on engagement across all campaigns."""
        
        # This would calculate and update lead score based on engagement
        # For now, returning sample score
        return 75.0