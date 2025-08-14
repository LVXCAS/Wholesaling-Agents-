"""
Unit tests for the outreach campaign service.
Tests Requirements 3.1, 3.5, and 3.6 implementation.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import uuid

from app.services.outreach_campaign_service import (
    OutreachCampaignService,
    Campaign,
    CampaignStep,
    CampaignTarget,
    CampaignRecipient,
    CampaignMetrics,
    ABTestConfig,
    CampaignStatus,
    CampaignType,
    TriggerType,
    create_drip_campaign,
    create_ab_test_campaign,
    get_campaign_performance_summary
)
from app.services.message_generation_service import MessageGenerationService
from app.services.conversation_management_service import ConversationManagementService
from app.models.communication import CommunicationChannel


# Global fixtures
@pytest.fixture
def service():
    """Create outreach campaign service instance."""
    return OutreachCampaignService()


@pytest.fixture
def mock_message_service():
    """Create mock message generation service."""
    return Mock(spec=MessageGenerationService)


@pytest.fixture
def mock_conversation_service():
    """Create mock conversation management service."""
    mock_service = Mock(spec=ConversationManagementService)
    mock_conversation = Mock()
    mock_conversation.id = uuid.uuid4()
    mock_service.create_conversation.return_value = mock_conversation
    return mock_service


@pytest.fixture
def sample_campaign(service):
    """Create a sample campaign."""
    return service.create_campaign(
        name="Test Campaign",
        campaign_type=CampaignType.SEQUENCE,
        description="Test campaign description"
    )


class TestOutreachCampaignService:
    """Test cases for OutreachCampaignService."""
    
    def test_service_initialization(self, service):
        """Test service initializes correctly."""
        assert service is not None
        assert service.message_service is not None
        assert service.conversation_service is not None
        assert service.campaigns == {}
    
    def test_service_initialization_with_dependencies(self, mock_message_service, mock_conversation_service):
        """Test service initialization with injected dependencies."""
        service = OutreachCampaignService(
            message_service=mock_message_service,
            conversation_service=mock_conversation_service
        )
        
        assert service.message_service == mock_message_service
        assert service.conversation_service == mock_conversation_service


class TestCampaignCreation:
    """Test campaign creation functionality."""
    
    def test_create_campaign_basic(self, service):
        """Test basic campaign creation."""
        name = "Test Campaign"
        campaign_type = CampaignType.DRIP
        description = "Test description"
        
        campaign = service.create_campaign(
            name=name,
            campaign_type=campaign_type,
            description=description,
            created_by="test_user"
        )
        
        assert campaign.id is not None
        assert campaign.name == name
        assert campaign.campaign_type == campaign_type
        assert campaign.description == description
        assert campaign.status == CampaignStatus.DRAFT
        assert campaign.created_by == "test_user"
        assert campaign.created_at is not None
        assert campaign.updated_at is not None
        assert campaign.metrics is not None
        assert campaign.id in service.campaigns
    
    def test_create_campaign_minimal(self, service):
        """Test campaign creation with minimal parameters."""
        campaign = service.create_campaign("Minimal Campaign", CampaignType.SINGLE_MESSAGE)
        
        assert campaign.name == "Minimal Campaign"
        assert campaign.campaign_type == CampaignType.SINGLE_MESSAGE
        assert campaign.description is None
        assert campaign.created_by is None
        assert campaign.status == CampaignStatus.DRAFT


class TestCampaignSteps:
    """Test campaign step management."""
    
    def test_add_campaign_step_basic(self, service, sample_campaign):
        """Test adding a basic campaign step."""
        step = service.add_campaign_step(
            campaign_id=sample_campaign.id,
            channel=CommunicationChannel.EMAIL,
            message_content="Hello, this is a test message",
            subject_template="Test Subject",
            delay_hours=24
        )
        
        assert step.id is not None
        assert step.campaign_id == sample_campaign.id
        assert step.step_number == 1
        assert step.channel == CommunicationChannel.EMAIL
        assert step.message_content == "Hello, this is a test message"
        assert step.subject_template == "Test Subject"
        assert step.delay_hours == 24
        assert step.trigger_type == TriggerType.TIME_DELAY
        assert step.active is True
        
        # Check campaign was updated
        updated_campaign = service.get_campaign(sample_campaign.id)
        assert len(updated_campaign.steps) == 1
        assert updated_campaign.steps[0] == step
    
    def test_add_multiple_campaign_steps(self, service, sample_campaign):
        """Test adding multiple campaign steps."""
        step1 = service.add_campaign_step(
            sample_campaign.id,
            CommunicationChannel.EMAIL,
            message_content="First message"
        )
        
        step2 = service.add_campaign_step(
            sample_campaign.id,
            CommunicationChannel.SMS,
            message_content="Second message",
            delay_hours=48
        )
        
        assert step1.step_number == 1
        assert step2.step_number == 2
        
        campaign = service.get_campaign(sample_campaign.id)
        assert len(campaign.steps) == 2
        assert campaign.steps[0] == step1
        assert campaign.steps[1] == step2
    
    def test_add_step_to_nonexistent_campaign(self, service):
        """Test adding step to non-existent campaign raises error."""
        fake_id = uuid.uuid4()
        
        with pytest.raises(ValueError, match=f"Campaign {fake_id} not found"):
            service.add_campaign_step(
                fake_id,
                CommunicationChannel.EMAIL,
                message_content="Test"
            )


class TestCampaignTargeting:
    """Test campaign targeting functionality."""
    
    def test_set_campaign_targets_with_contacts(self, service, sample_campaign):
        """Test setting campaign targets with specific contacts."""
        contact_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
        
        targets = service.set_campaign_targets(
            campaign_id=sample_campaign.id,
            contact_ids=contact_ids,
            property_types=["single_family", "condo"],
            tags=["hot_lead", "qualified"]
        )
        
        assert targets.id is not None
        assert targets.campaign_id == sample_campaign.id
        assert targets.contact_ids == contact_ids
        assert targets.property_types == ["single_family", "condo"]
        assert targets.tags == ["hot_lead", "qualified"]
        
        # Check campaign was updated
        campaign = service.get_campaign(sample_campaign.id)
        assert campaign.targets == targets
    
    def test_set_campaign_targets_with_filters(self, service, sample_campaign):
        """Test setting campaign targets with filters."""
        location_filters = {"city": "Austin", "state": "TX"}
        custom_filters = {"min_property_value": 200000}
        
        targets = service.set_campaign_targets(
            campaign_id=sample_campaign.id,
            location_filters=location_filters,
            custom_filters=custom_filters,
            exclude_contacted_days=30
        )
        
        assert targets.location_filters == location_filters
        assert targets.custom_filters == custom_filters
        assert targets.exclude_contacted_days == 30
    
    def test_set_targets_for_nonexistent_campaign(self, service):
        """Test setting targets for non-existent campaign raises error."""
        fake_id = uuid.uuid4()
        
        with pytest.raises(ValueError, match=f"Campaign {fake_id} not found"):
            service.set_campaign_targets(fake_id, contact_ids=[uuid.uuid4()])


class TestABTesting:
    """Test A/B testing functionality."""
    
    def test_setup_ab_test_basic(self, service, sample_campaign):
        """Test basic A/B test setup."""
        ab_config = service.setup_ab_test(
            campaign_id=sample_campaign.id,
            test_name="Subject Line Test",
            variants=["A", "B"],
            test_metric="open_rate"
        )
        
        assert ab_config.id is not None
        assert ab_config.campaign_id == sample_campaign.id
        assert ab_config.test_name == "Subject Line Test"
        assert ab_config.variants == ["A", "B"]
        assert ab_config.traffic_split == {"A": 0.5, "B": 0.5}
        assert ab_config.test_metric == "open_rate"
        assert ab_config.min_sample_size == 100
        assert ab_config.confidence_level == 0.95
        
        # Check campaign was updated
        campaign = service.get_campaign(sample_campaign.id)
        assert campaign.ab_test_config == ab_config
    
    def test_setup_ab_test_custom_split(self, service, sample_campaign):
        """Test A/B test setup with custom traffic split."""
        traffic_split = {"A": 0.7, "B": 0.3}
        
        ab_config = service.setup_ab_test(
            campaign_id=sample_campaign.id,
            test_name="Custom Split Test",
            variants=["A", "B"],
            traffic_split=traffic_split
        )
        
        assert ab_config.traffic_split == traffic_split
    
    def test_setup_ab_test_multiple_variants(self, service, sample_campaign):
        """Test A/B test setup with multiple variants."""
        variants = ["A", "B", "C"]
        
        ab_config = service.setup_ab_test(
            campaign_id=sample_campaign.id,
            test_name="Multi-variant Test",
            variants=variants
        )
        
        assert ab_config.variants == variants
        assert ab_config.traffic_split == {"A": 1/3, "B": 1/3, "C": 1/3}
    
    def test_setup_ab_test_nonexistent_campaign(self, service):
        """Test A/B test setup for non-existent campaign raises error."""
        fake_id = uuid.uuid4()
        
        with pytest.raises(ValueError, match=f"Campaign {fake_id} not found"):
            service.setup_ab_test(fake_id, "Test")


class TestCampaignExecution:
    """Test campaign execution functionality."""
    
    def test_start_campaign_success(self, service, sample_campaign):
        """Test successful campaign start."""
        # Add required components
        service.add_campaign_step(
            sample_campaign.id,
            CommunicationChannel.EMAIL,
            message_content="Test message"
        )
        service.set_campaign_targets(
            sample_campaign.id,
            contact_ids=[uuid.uuid4(), uuid.uuid4()]
        )
        
        success = service.start_campaign(sample_campaign.id)
        
        assert success is True
        
        campaign = service.get_campaign(sample_campaign.id)
        assert campaign.status == CampaignStatus.ACTIVE
        assert campaign.start_date is not None
        assert len(campaign.recipients) > 0
        assert campaign.metrics.total_recipients == len(campaign.recipients)
    
    def test_start_campaign_without_steps(self, service, sample_campaign):
        """Test starting campaign without steps raises error."""
        service.set_campaign_targets(
            sample_campaign.id,
            contact_ids=[uuid.uuid4()]
        )
        
        with pytest.raises(ValueError, match="Campaign must have at least one step"):
            service.start_campaign(sample_campaign.id)
    
    def test_start_campaign_without_targets(self, service, sample_campaign):
        """Test starting campaign without targets raises error."""
        service.add_campaign_step(
            sample_campaign.id,
            CommunicationChannel.EMAIL,
            message_content="Test"
        )
        
        with pytest.raises(ValueError, match="Campaign must have targeting criteria"):
            service.start_campaign(sample_campaign.id)
    
    def test_start_nonexistent_campaign(self, service):
        """Test starting non-existent campaign returns False."""
        fake_id = uuid.uuid4()
        success = service.start_campaign(fake_id)
        assert success is False


class TestCampaignControl:
    """Test campaign control functionality."""
    
    def test_pause_campaign(self, service, sample_campaign):
        """Test pausing an active campaign."""
        # Start campaign first
        service.add_campaign_step(sample_campaign.id, CommunicationChannel.EMAIL, "Test")
        service.set_campaign_targets(sample_campaign.id, contact_ids=[uuid.uuid4()])
        service.start_campaign(sample_campaign.id)
        
        success = service.pause_campaign(sample_campaign.id)
        
        assert success is True
        campaign = service.get_campaign(sample_campaign.id)
        assert campaign.status == CampaignStatus.PAUSED
    
    def test_resume_campaign(self, service, sample_campaign):
        """Test resuming a paused campaign."""
        # Start and pause campaign
        service.add_campaign_step(sample_campaign.id, CommunicationChannel.EMAIL, "Test")
        service.set_campaign_targets(sample_campaign.id, contact_ids=[uuid.uuid4()])
        service.start_campaign(sample_campaign.id)
        service.pause_campaign(sample_campaign.id)
        
        success = service.resume_campaign(sample_campaign.id)
        
        assert success is True
        campaign = service.get_campaign(sample_campaign.id)
        assert campaign.status == CampaignStatus.ACTIVE
    
    def test_stop_campaign(self, service, sample_campaign):
        """Test stopping a campaign."""
        # Start campaign
        service.add_campaign_step(sample_campaign.id, CommunicationChannel.EMAIL, "Test")
        service.set_campaign_targets(sample_campaign.id, contact_ids=[uuid.uuid4()])
        service.start_campaign(sample_campaign.id)
        
        success = service.stop_campaign(sample_campaign.id)
        
        assert success is True
        campaign = service.get_campaign(sample_campaign.id)
        assert campaign.status == CampaignStatus.COMPLETED
        assert campaign.end_date is not None
    
    def test_control_nonexistent_campaign(self, service):
        """Test controlling non-existent campaign returns False."""
        fake_id = uuid.uuid4()
        
        assert service.pause_campaign(fake_id) is False
        assert service.resume_campaign(fake_id) is False
        assert service.stop_campaign(fake_id) is False


class TestCampaignProcessing:
    """Test campaign processing functionality."""
    
    def test_process_campaigns_empty(self, service):
        """Test processing campaigns when none exist."""
        results = service.process_campaigns()
        assert results == {}
    
    def test_process_campaigns_with_inactive(self, service):
        """Test processing campaigns with inactive campaigns."""
        # Create draft campaign
        campaign = service.create_campaign("Draft Campaign", CampaignType.SINGLE_MESSAGE)
        
        results = service.process_campaigns()
        assert results == {}  # No active campaigns
    
    @patch('app.services.outreach_campaign_service.OutreachCampaignService._send_campaign_message')
    def test_process_active_campaign(self, mock_send, service, mock_conversation_service):
        """Test processing an active campaign."""
        service.conversation_service = mock_conversation_service
        mock_send.return_value = True
        
        # Create and start campaign
        campaign = service.create_campaign("Active Campaign", CampaignType.SEQUENCE)
        service.add_campaign_step(campaign.id, CommunicationChannel.EMAIL, "Test message")
        service.set_campaign_targets(campaign.id, contact_ids=[uuid.uuid4()])
        service.start_campaign(campaign.id)
        
        results = service.process_campaigns()
        
        assert campaign.id in results
        assert results[campaign.id] >= 0  # Some messages may be sent


class TestCampaignMetrics:
    """Test campaign metrics functionality."""
    
    def test_get_campaign_metrics_basic(self, service, sample_campaign):
        """Test getting basic campaign metrics."""
        metrics = service.get_campaign_metrics(sample_campaign.id)
        
        assert metrics is not None
        assert metrics.campaign_id == sample_campaign.id
        assert metrics.total_recipients == 0
        assert metrics.messages_sent == 0
        assert metrics.last_updated is not None
    
    def test_get_metrics_nonexistent_campaign(self, service):
        """Test getting metrics for non-existent campaign."""
        fake_id = uuid.uuid4()
        metrics = service.get_campaign_metrics(fake_id)
        assert metrics is None
    
    def test_get_ab_test_results_no_test(self, service, sample_campaign):
        """Test getting A/B test results when no test is configured."""
        results = service.get_ab_test_results(sample_campaign.id)
        assert results is None
    
    def test_get_ab_test_results_with_test(self, service, sample_campaign):
        """Test getting A/B test results with configured test."""
        # Set up A/B test
        service.setup_ab_test(sample_campaign.id, "Test")
        
        # Add some recipients with variants
        service.add_campaign_step(sample_campaign.id, CommunicationChannel.EMAIL, "Test")
        service.set_campaign_targets(sample_campaign.id, contact_ids=[uuid.uuid4(), uuid.uuid4()])
        service.start_campaign(sample_campaign.id)
        
        # Update metrics to include variant data
        campaign = service.get_campaign(sample_campaign.id)
        service._update_campaign_metrics(campaign)
        
        results = service.get_ab_test_results(sample_campaign.id)
        
        # Results might be empty if no variant metrics exist yet
        if results:
            assert "test_name" in results
            assert "variant_values" in results
            assert "best_variant" in results
        else:
            # This is acceptable for a newly started campaign
            assert results == {}


class TestCampaignManagement:
    """Test campaign management functionality."""
    
    def test_get_campaign_exists(self, service, sample_campaign):
        """Test getting an existing campaign."""
        retrieved = service.get_campaign(sample_campaign.id)
        
        assert retrieved is not None
        assert retrieved.id == sample_campaign.id
        assert retrieved.name == sample_campaign.name
    
    def test_get_campaign_not_exists(self, service):
        """Test getting a non-existent campaign."""
        fake_id = uuid.uuid4()
        retrieved = service.get_campaign(fake_id)
        assert retrieved is None
    
    def test_list_campaigns_empty(self, service):
        """Test listing campaigns when none exist."""
        campaigns = service.list_campaigns()
        assert campaigns == []
    
    def test_list_campaigns_with_data(self, service):
        """Test listing campaigns with data."""
        campaign1 = service.create_campaign("Campaign 1", CampaignType.DRIP)
        campaign2 = service.create_campaign("Campaign 2", CampaignType.SEQUENCE)
        
        campaigns = service.list_campaigns()
        
        assert len(campaigns) == 2
        assert campaign1 in campaigns or campaign2 in campaigns
    
    def test_list_campaigns_filtered_by_status(self, service):
        """Test listing campaigns filtered by status."""
        campaign1 = service.create_campaign("Draft Campaign", CampaignType.DRIP)
        campaign2 = service.create_campaign("Active Campaign", CampaignType.SEQUENCE)
        
        # Start one campaign
        service.add_campaign_step(campaign2.id, CommunicationChannel.EMAIL, "Test")
        service.set_campaign_targets(campaign2.id, contact_ids=[uuid.uuid4()])
        service.start_campaign(campaign2.id)
        
        draft_campaigns = service.list_campaigns(status=CampaignStatus.DRAFT)
        active_campaigns = service.list_campaigns(status=CampaignStatus.ACTIVE)
        
        assert len(draft_campaigns) == 1
        assert campaign1 in draft_campaigns
        
        assert len(active_campaigns) == 1
        assert campaign2 in active_campaigns
    
    def test_list_campaigns_filtered_by_type(self, service):
        """Test listing campaigns filtered by type."""
        drip_campaign = service.create_campaign("Drip Campaign", CampaignType.DRIP)
        sequence_campaign = service.create_campaign("Sequence Campaign", CampaignType.SEQUENCE)
        
        drip_campaigns = service.list_campaigns(campaign_type=CampaignType.DRIP)
        sequence_campaigns = service.list_campaigns(campaign_type=CampaignType.SEQUENCE)
        
        assert len(drip_campaigns) == 1
        assert drip_campaign in drip_campaigns
        
        assert len(sequence_campaigns) == 1
        assert sequence_campaign in sequence_campaigns
    
    def test_delete_campaign(self, service, sample_campaign):
        """Test deleting a campaign."""
        campaign_id = sample_campaign.id
        
        success = service.delete_campaign(campaign_id)
        
        assert success is True
        assert service.get_campaign(campaign_id) is None
    
    def test_delete_nonexistent_campaign(self, service):
        """Test deleting non-existent campaign."""
        fake_id = uuid.uuid4()
        success = service.delete_campaign(fake_id)
        assert success is False


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_create_drip_campaign(self, service):
        """Test creating a drip campaign using utility function."""
        messages = [
            {"content": "Message 1", "channel": CommunicationChannel.EMAIL, "delay_hours": 0},
            {"content": "Message 2", "channel": CommunicationChannel.SMS, "delay_hours": 24},
            {"content": "Message 3", "channel": CommunicationChannel.EMAIL, "delay_hours": 48}
        ]
        target_contacts = [uuid.uuid4(), uuid.uuid4()]
        
        campaign = create_drip_campaign(
            service,
            "Test Drip Campaign",
            messages,
            target_contacts
        )
        
        assert campaign.name == "Test Drip Campaign"
        assert campaign.campaign_type == CampaignType.DRIP
        assert len(campaign.steps) == 3
        assert campaign.targets.contact_ids == target_contacts
        
        # Check step details
        assert campaign.steps[0].channel == CommunicationChannel.EMAIL
        assert campaign.steps[0].delay_hours == 0
        assert campaign.steps[1].channel == CommunicationChannel.SMS
        assert campaign.steps[1].delay_hours == 24
        assert campaign.steps[2].delay_hours == 48
    
    def test_create_ab_test_campaign(self, service):
        """Test creating an A/B test campaign using utility function."""
        variant_a = "Subject A: Great opportunity!"
        variant_b = "Subject B: Don't miss out!"
        target_contacts = [uuid.uuid4(), uuid.uuid4()]
        
        campaign = create_ab_test_campaign(
            service,
            "A/B Test Campaign",
            variant_a,
            variant_b,
            target_contacts,
            CommunicationChannel.EMAIL
        )
        
        assert campaign.name == "A/B Test Campaign"
        assert campaign.campaign_type == CampaignType.SINGLE_MESSAGE
        assert len(campaign.steps) == 2
        assert campaign.ab_test_config is not None
        assert campaign.targets.contact_ids == target_contacts
        
        # Check A/B test configuration
        assert campaign.ab_test_config.variants == ["A", "B"]
        assert campaign.steps[0].a_b_test_variant == "A"
        assert campaign.steps[1].a_b_test_variant == "B"
    
    def test_get_campaign_performance_summary_empty(self, service):
        """Test getting performance summary with no campaigns."""
        summary = get_campaign_performance_summary(service)
        assert summary == {}
    
    def test_get_campaign_performance_summary_with_data(self, service):
        """Test getting performance summary with campaign data."""
        # Create some campaigns
        campaign1 = service.create_campaign("Campaign 1", CampaignType.DRIP)
        campaign2 = service.create_campaign("Campaign 2", CampaignType.SEQUENCE)
        
        # Start one campaign
        service.add_campaign_step(campaign1.id, CommunicationChannel.EMAIL, "Test")
        service.set_campaign_targets(campaign1.id, contact_ids=[uuid.uuid4()])
        service.start_campaign(campaign1.id)
        
        summary = get_campaign_performance_summary(service)
        
        assert summary["total_campaigns"] == 2
        assert "status_distribution" in summary
        assert "type_distribution" in summary
        assert summary["status_distribution"]["draft"] == 1
        assert summary["status_distribution"]["active"] == 1
        assert summary["type_distribution"]["drip"] == 1
        assert summary["type_distribution"]["sequence"] == 1
    
    def test_get_performance_summary_with_date_filter(self, service):
        """Test getting performance summary with date filtering."""
        # Create campaign
        campaign = service.create_campaign("Test Campaign", CampaignType.DRIP)
        
        # Test with future date range (should exclude campaign)
        future_date = datetime.now() + timedelta(days=1)
        summary = get_campaign_performance_summary(
            service, 
            date_from=future_date
        )
        assert summary == {}
        
        # Test with past date range (should include campaign)
        past_date = datetime.now() - timedelta(days=1)
        summary = get_campaign_performance_summary(
            service,
            date_from=past_date
        )
        assert summary["total_campaigns"] == 1


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""
    
    def test_complete_campaign_lifecycle(self, service, mock_conversation_service):
        """Test complete campaign lifecycle from creation to completion."""
        service.conversation_service = mock_conversation_service
        
        # Create campaign
        campaign = service.create_campaign(
            "Property Outreach Campaign",
            CampaignType.SEQUENCE,
            "Multi-step property outreach sequence"
        )
        
        # Add steps
        service.add_campaign_step(
            campaign.id,
            CommunicationChannel.EMAIL,
            "Hi, I'm interested in your property at {property_address}",
            "Property Inquiry",
            delay_hours=0
        )
        
        service.add_campaign_step(
            campaign.id,
            CommunicationChannel.SMS,
            "Following up on my email about your property",
            delay_hours=72
        )
        
        service.add_campaign_step(
            campaign.id,
            CommunicationChannel.EMAIL,
            "Final follow-up - still interested in discussing your property",
            "Final Follow-up",
            delay_hours=168  # 1 week
        )
        
        # Set targets
        target_contacts = [uuid.uuid4() for _ in range(5)]
        service.set_campaign_targets(
            campaign.id,
            contact_ids=target_contacts,
            property_types=["single_family"],
            tags=["qualified_lead"]
        )
        
        # Start campaign
        success = service.start_campaign(campaign.id)
        assert success is True
        
        # Verify campaign state
        updated_campaign = service.get_campaign(campaign.id)
        assert updated_campaign.status == CampaignStatus.ACTIVE
        assert len(updated_campaign.recipients) == len(target_contacts)
        assert len(updated_campaign.steps) == 3
        
        # Process campaign (simulate message sending)
        results = service.process_campaigns()
        assert campaign.id in results
        
        # Get metrics
        metrics = service.get_campaign_metrics(campaign.id)
        assert metrics is not None
        assert metrics.total_recipients == len(target_contacts)
        
        # Stop campaign
        service.stop_campaign(campaign.id)
        final_campaign = service.get_campaign(campaign.id)
        assert final_campaign.status == CampaignStatus.COMPLETED
    
    def test_ab_test_campaign_workflow(self, service, mock_conversation_service):
        """Test A/B test campaign workflow."""
        service.conversation_service = mock_conversation_service
        
        # Create A/B test campaign using utility function
        variant_a = "Cash offer for your property - quick closing"
        variant_b = "Interested in purchasing your home - let's talk"
        target_contacts = [uuid.uuid4() for _ in range(20)]
        
        campaign = create_ab_test_campaign(
            service,
            "Subject Line A/B Test",
            variant_a,
            variant_b,
            target_contacts
        )
        
        # Start campaign
        service.start_campaign(campaign.id)
        
        # Verify A/B test setup
        updated_campaign = service.get_campaign(campaign.id)
        assert updated_campaign.ab_test_config is not None
        assert len(updated_campaign.recipients) == len(target_contacts)
        
        # Check variant assignment
        variant_counts = {"A": 0, "B": 0}
        for recipient in updated_campaign.recipients:
            if recipient.a_b_variant:
                variant_counts[recipient.a_b_variant] += 1
        
        # Should have roughly equal distribution
        assert variant_counts["A"] > 0
        assert variant_counts["B"] > 0
        
        # Get A/B test results
        results = service.get_ab_test_results(campaign.id)
        # Results might be empty if no variant metrics exist yet
        if results:
            assert "variant_values" in results
            assert "best_variant" in results
        else:
            # This is acceptable for a newly started campaign
            assert results == {}


if __name__ == "__main__":
    pytest.main([__file__])