"""
Unit tests for lead nurturing service.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
import uuid

from app.services.lead_nurturing_service import LeadNurturingService
from app.models.scheduling import NurturingCampaign, EngagementTracking


class TestLeadNurturingService:
    """Unit tests for LeadNurturingService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.service = LeadNurturingService(self.mock_db)
        self.contact_id = uuid.uuid4()
        self.campaign_id = uuid.uuid4()
    
    @pytest.mark.asyncio
    async def test_create_nurturing_campaign(self):
        """Test creating a nurturing campaign."""
        content_sequence = [
            {
                "type": "email",
                "subject": "Welcome to our program",
                "content": "Welcome email content",
                "delay_days": 0
            },
            {
                "type": "email",
                "subject": "Market insights",
                "content": "Market insights content",
                "delay_days": 7
            }
        ]
        
        campaign = await self.service.create_nurturing_campaign(
            name="New Lead Nurturing",
            description="Campaign for new leads",
            target_lead_status=["new", "contacted"],
            target_lead_score_min=0.0,
            target_lead_score_max=50.0,
            target_tags=["real-estate", "investor"],
            content_sequence=content_sequence,
            frequency_days=7,
            max_duration_days=90,
            pause_on_engagement=True
        )
        
        assert campaign.name == "New Lead Nurturing"
        assert campaign.description == "Campaign for new leads"
        assert campaign.target_lead_status == ["new", "contacted"]
        assert campaign.target_lead_score_min == 0.0
        assert campaign.target_lead_score_max == 50.0
        assert campaign.target_tags == ["real-estate", "investor"]
        assert campaign.content_sequence == content_sequence
        assert campaign.frequency_days == 7
        assert campaign.max_duration_days == 90
        assert campaign.pause_on_engagement is True
        assert campaign.is_active is True
        assert campaign.id is not None
        assert campaign.created_at is not None
    
    @pytest.mark.asyncio
    async def test_create_nurturing_campaign_with_defaults(self):
        """Test creating a nurturing campaign with default values."""
        campaign = await self.service.create_nurturing_campaign(
            name="Simple Campaign"
        )
        
        assert campaign.name == "Simple Campaign"
        assert campaign.target_lead_status == []
        assert campaign.target_tags == []
        assert campaign.content_sequence == []
        assert campaign.frequency_days == 7
        assert campaign.max_duration_days is None
        assert campaign.pause_on_engagement is True
        assert campaign.is_active is True
    
    @pytest.mark.asyncio
    async def test_enroll_contact_in_campaign(self):
        """Test enrolling a contact in a campaign."""
        engagement = await self.service.enroll_contact_in_campaign(
            self.contact_id,
            self.campaign_id
        )
        
        assert engagement.contact_id == self.contact_id
        assert engagement.campaign_id == self.campaign_id
        assert engagement.campaign_status == "active"
        assert engagement.emails_sent == 0
        assert engagement.emails_opened == 0
        assert engagement.emails_clicked == 0
        assert engagement.calls_made == 0
        assert engagement.calls_answered == 0
        assert engagement.meetings_scheduled == 0
        assert engagement.meetings_attended == 0
        assert engagement.engagement_score == 0.0
        assert engagement.id is not None
        assert engagement.started_at is not None
    
    @pytest.mark.asyncio
    async def test_track_email_sent(self):
        """Test tracking email sent."""
        # Mock the get_engagement_tracking method
        mock_engagement = EngagementTracking(
            id=uuid.uuid4(),
            contact_id=self.contact_id,
            campaign_id=self.campaign_id,
            emails_sent=0,
            started_at=datetime.utcnow()
        )
        
        self.service.get_engagement_tracking = AsyncMock(return_value=mock_engagement)
        
        updated_engagement = await self.service.track_email_sent(
            self.contact_id,
            self.campaign_id
        )
        
        assert updated_engagement.emails_sent == 1
        assert updated_engagement.last_updated_at is not None
    
    @pytest.mark.asyncio
    async def test_track_email_opened(self):
        """Test tracking email opened."""
        # Mock the get_engagement_tracking method
        mock_engagement = EngagementTracking(
            id=uuid.uuid4(),
            contact_id=self.contact_id,
            campaign_id=self.campaign_id,
            emails_opened=0,
            started_at=datetime.utcnow()
        )
        
        self.service.get_engagement_tracking = AsyncMock(return_value=mock_engagement)
        self.service.update_engagement_score = AsyncMock(return_value=5.0)
        
        updated_engagement = await self.service.track_email_opened(
            self.contact_id,
            self.campaign_id
        )
        
        assert updated_engagement.emails_opened == 1
        assert updated_engagement.last_engagement_date is not None
        assert updated_engagement.last_updated_at is not None
        
        # Verify that engagement score was updated
        self.service.update_engagement_score.assert_called_once_with(mock_engagement)
    
    @pytest.mark.asyncio
    async def test_track_email_clicked(self):
        """Test tracking email clicked."""
        # Mock the get_engagement_tracking method
        mock_engagement = EngagementTracking(
            id=uuid.uuid4(),
            contact_id=self.contact_id,
            campaign_id=self.campaign_id,
            emails_clicked=0,
            started_at=datetime.utcnow()
        )
        
        self.service.get_engagement_tracking = AsyncMock(return_value=mock_engagement)
        self.service.update_engagement_score = AsyncMock(return_value=10.0)
        
        updated_engagement = await self.service.track_email_clicked(
            self.contact_id,
            self.campaign_id
        )
        
        assert updated_engagement.emails_clicked == 1
        assert updated_engagement.last_engagement_date is not None
        assert updated_engagement.last_updated_at is not None
        
        # Verify that engagement score was updated
        self.service.update_engagement_score.assert_called_once_with(mock_engagement)
    
    @pytest.mark.asyncio
    async def test_track_meeting_attended(self):
        """Test tracking meeting attended."""
        # Mock the get_engagement_tracking method
        mock_engagement = EngagementTracking(
            id=uuid.uuid4(),
            contact_id=self.contact_id,
            campaign_id=self.campaign_id,
            meetings_attended=0,
            started_at=datetime.utcnow()
        )
        
        self.service.get_engagement_tracking = AsyncMock(return_value=mock_engagement)
        self.service.update_engagement_score = AsyncMock(return_value=25.0)
        
        updated_engagement = await self.service.track_meeting_attended(
            self.contact_id,
            self.campaign_id
        )
        
        assert updated_engagement.meetings_attended == 1
        assert updated_engagement.last_engagement_date is not None
        assert updated_engagement.last_updated_at is not None
        
        # Verify that engagement score was updated
        self.service.update_engagement_score.assert_called_once_with(mock_engagement)
    
    @pytest.mark.asyncio
    async def test_update_engagement_score(self):
        """Test engagement score calculation."""
        engagement = EngagementTracking(
            id=uuid.uuid4(),
            contact_id=self.contact_id,
            campaign_id=self.campaign_id,
            emails_opened=5,
            emails_clicked=2,
            calls_answered=1,
            meetings_scheduled=1,
            meetings_attended=1,
            last_engagement_date=datetime.utcnow() - timedelta(days=1),
            started_at=datetime.utcnow() - timedelta(days=10)
        )
        
        score = await self.service.update_engagement_score(engagement)
        
        # Expected score calculation:
        # emails_opened: 5 * 1.0 = 5.0
        # emails_clicked: 2 * 2.0 = 4.0
        # calls_answered: 1 * 3.0 = 3.0
        # meetings_scheduled: 1 * 5.0 = 5.0
        # meetings_attended: 1 * 8.0 = 8.0
        # Base score: 25.0
        # Time decay (1 day ago): 0.98 factor = 24.5
        # Frequency bonus: 10 activities / 11 days = 0.91 * 0.5 = 0.45
        # Total: ~24.95
        
        assert score > 20.0  # Should be a significant score
        assert score == engagement.engagement_score
        assert score <= 100.0  # Should not exceed maximum
    
    @pytest.mark.asyncio
    async def test_get_next_content_for_contact(self):
        """Test getting next content for a contact."""
        content_sequence = [
            {"type": "email", "subject": "Welcome", "content": "Welcome content"},
            {"type": "email", "subject": "Follow-up", "content": "Follow-up content"},
            {"type": "call", "topic": "Check-in call", "script": "Call script"}
        ]
        
        mock_campaign = NurturingCampaign(
            id=self.campaign_id,
            name="Test Campaign",
            content_sequence=content_sequence,
            frequency_days=7,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        mock_engagement = EngagementTracking(
            id=uuid.uuid4(),
            contact_id=self.contact_id,
            campaign_id=self.campaign_id,
            started_at=datetime.utcnow() - timedelta(days=14),  # 2 weeks ago
            campaign_status="active"
        )
        
        self.service.get_nurturing_campaign = AsyncMock(return_value=mock_campaign)
        self.service.get_engagement_tracking = AsyncMock(return_value=mock_engagement)
        
        content = await self.service.get_next_content_for_contact(
            self.contact_id,
            self.campaign_id
        )
        
        # After 14 days with 7-day frequency, should get content index 2 (14 // 7 = 2)
        assert content == content_sequence[2]
        assert content["type"] == "call"
        assert content["topic"] == "Check-in call"
    
    @pytest.mark.asyncio
    async def test_should_send_content_active_campaign(self):
        """Test should_send_content for active campaign."""
        mock_campaign = NurturingCampaign(
            id=self.campaign_id,
            name="Test Campaign",
            frequency_days=7,
            is_active=True,
            pause_on_engagement=False,
            created_at=datetime.utcnow()
        )
        
        mock_engagement = EngagementTracking(
            id=uuid.uuid4(),
            contact_id=self.contact_id,
            campaign_id=self.campaign_id,
            started_at=datetime.utcnow() - timedelta(days=8),  # 8 days ago
            campaign_status="active"
        )
        
        self.service.get_nurturing_campaign = AsyncMock(return_value=mock_campaign)
        self.service.get_engagement_tracking = AsyncMock(return_value=mock_engagement)
        
        should_send = await self.service.should_send_content(
            self.contact_id,
            self.campaign_id
        )
        
        assert should_send is True
    
    @pytest.mark.asyncio
    async def test_should_send_content_paused_on_engagement(self):
        """Test should_send_content when paused due to recent engagement."""
        mock_campaign = NurturingCampaign(
            id=self.campaign_id,
            name="Test Campaign",
            frequency_days=7,
            is_active=True,
            pause_on_engagement=True,
            created_at=datetime.utcnow()
        )
        
        mock_engagement = EngagementTracking(
            id=uuid.uuid4(),
            contact_id=self.contact_id,
            campaign_id=self.campaign_id,
            started_at=datetime.utcnow() - timedelta(days=8),
            last_engagement_date=datetime.utcnow() - timedelta(days=2),  # Recent engagement
            campaign_status="active"
        )
        
        self.service.get_nurturing_campaign = AsyncMock(return_value=mock_campaign)
        self.service.get_engagement_tracking = AsyncMock(return_value=mock_engagement)
        
        should_send = await self.service.should_send_content(
            self.contact_id,
            self.campaign_id
        )
        
        assert should_send is False  # Should be paused due to recent engagement
    
    @pytest.mark.asyncio
    async def test_should_send_content_inactive_campaign(self):
        """Test should_send_content for inactive campaign."""
        mock_campaign = NurturingCampaign(
            id=self.campaign_id,
            name="Test Campaign",
            frequency_days=7,
            is_active=False,  # Inactive campaign
            created_at=datetime.utcnow()
        )
        
        mock_engagement = EngagementTracking(
            id=uuid.uuid4(),
            contact_id=self.contact_id,
            campaign_id=self.campaign_id,
            started_at=datetime.utcnow() - timedelta(days=8),
            campaign_status="active"
        )
        
        self.service.get_nurturing_campaign = AsyncMock(return_value=mock_campaign)
        self.service.get_engagement_tracking = AsyncMock(return_value=mock_engagement)
        
        should_send = await self.service.should_send_content(
            self.contact_id,
            self.campaign_id
        )
        
        assert should_send is False  # Should not send for inactive campaign
    
    @pytest.mark.asyncio
    async def test_pause_contact_in_campaign(self):
        """Test pausing a contact in a campaign."""
        mock_engagement = EngagementTracking(
            id=uuid.uuid4(),
            contact_id=self.contact_id,
            campaign_id=self.campaign_id,
            campaign_status="active",
            started_at=datetime.utcnow()
        )
        
        self.service.get_engagement_tracking = AsyncMock(return_value=mock_engagement)
        
        paused_engagement = await self.service.pause_contact_in_campaign(
            self.contact_id,
            self.campaign_id
        )
        
        assert paused_engagement.campaign_status == "paused"
        assert paused_engagement.last_updated_at is not None
    
    @pytest.mark.asyncio
    async def test_unsubscribe_contact_from_campaign(self):
        """Test unsubscribing a contact from a campaign."""
        mock_engagement = EngagementTracking(
            id=uuid.uuid4(),
            contact_id=self.contact_id,
            campaign_id=self.campaign_id,
            campaign_status="active",
            started_at=datetime.utcnow()
        )
        
        self.service.get_engagement_tracking = AsyncMock(return_value=mock_engagement)
        
        unsubscribed_engagement = await self.service.unsubscribe_contact_from_campaign(
            self.contact_id,
            self.campaign_id
        )
        
        assert unsubscribed_engagement.campaign_status == "unsubscribed"
        assert unsubscribed_engagement.last_updated_at is not None
    
    @pytest.mark.asyncio
    async def test_get_campaign_performance_metrics(self):
        """Test getting campaign performance metrics."""
        metrics = await self.service.get_campaign_performance_metrics(self.campaign_id)
        
        # Check that all expected metrics are present
        expected_keys = [
            "total_contacts", "active_contacts", "paused_contacts", "unsubscribed_contacts",
            "total_emails_sent", "total_emails_opened", "total_emails_clicked",
            "total_calls_made", "total_calls_answered", "total_meetings_scheduled",
            "total_meetings_attended", "average_engagement_score", "open_rate",
            "click_rate", "call_answer_rate", "meeting_attendance_rate", "conversion_rate"
        ]
        
        for key in expected_keys:
            assert key in metrics
        
        # Check that rates are percentages (0.0 to 1.0)
        assert 0.0 <= metrics["open_rate"] <= 1.0
        assert 0.0 <= metrics["click_rate"] <= 1.0
        assert 0.0 <= metrics["call_answer_rate"] <= 1.0
        assert 0.0 <= metrics["meeting_attendance_rate"] <= 1.0
        assert 0.0 <= metrics["conversion_rate"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_recommend_content_optimization(self):
        """Test content optimization recommendations."""
        # Mock low performance metrics
        low_performance_metrics = {
            "open_rate": 0.15,  # Below 20% threshold
            "click_rate": 0.03,  # Below 5% threshold
            "call_answer_rate": 0.25,  # Below 30% threshold
            "total_contacts": 100,
            "total_emails_sent": 500,
            "total_emails_opened": 75,
            "total_emails_clicked": 15
        }
        
        self.service.get_campaign_performance_metrics = AsyncMock(return_value=low_performance_metrics)
        
        recommendations = await self.service.recommend_content_optimization(self.campaign_id)
        
        assert len(recommendations) == 3  # Should have 3 recommendations based on low metrics
        
        # Check subject line recommendation
        subject_rec = next((r for r in recommendations if r["type"] == "subject_line"), None)
        assert subject_rec is not None
        assert subject_rec["priority"] == "high"
        assert "subject lines" in subject_rec["message"].lower()
        
        # Check content recommendation
        content_rec = next((r for r in recommendations if r["type"] == "content"), None)
        assert content_rec is not None
        assert content_rec["priority"] == "medium"
        assert "click-through rate" in content_rec["message"].lower()
        
        # Check timing recommendation
        timing_rec = next((r for r in recommendations if r["type"] == "timing"), None)
        assert timing_rec is not None
        assert timing_rec["priority"] == "medium"
        assert "call answer rate" in timing_rec["message"].lower()
    
    @pytest.mark.asyncio
    async def test_create_content_recommendation_engine(self):
        """Test content recommendation engine."""
        recommendations = await self.service.create_content_recommendation_engine(self.contact_id)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Check structure of recommendations
        for rec in recommendations:
            assert "content_type" in rec
            assert "priority" in rec
            assert "reason" in rec
            assert rec["content_type"] in ["email", "sms", "call"]
            assert rec["priority"] in ["low", "medium", "high"]
    
    @pytest.mark.asyncio
    async def test_update_lead_score_based_on_engagement(self):
        """Test updating lead score based on engagement."""
        new_score = await self.service.update_lead_score_based_on_engagement(self.contact_id)
        
        assert isinstance(new_score, (int, float))
        assert 0.0 <= new_score <= 100.0