"""
Outreach campaign service for managing multi-channel marketing campaigns.
Implements Requirements 3.1, 3.5, and 3.6 for campaign management and analytics.
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import random

from pydantic import BaseModel

from ..models.communication import CommunicationChannel, MessageStatus
from .message_generation_service import MessageGenerationService, MessageGenerationRequest
from .conversation_management_service import ConversationManagementService


class CampaignStatus(str, Enum):
    """Campaign status types."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CampaignType(str, Enum):
    """Campaign types."""
    SINGLE_MESSAGE = "single_message"
    SEQUENCE = "sequence"
    DRIP = "drip"
    NURTURE = "nurture"
    FOLLOW_UP = "follow_up"


class TriggerType(str, Enum):
    """Campaign trigger types."""
    IMMEDIATE = "immediate"
    SCHEDULED = "scheduled"
    RESPONSE_BASED = "response_based"
    TIME_DELAY = "time_delay"
    BEHAVIOR_BASED = "behavior_based"


class CampaignStep(BaseModel):
    """Individual step in a campaign sequence."""
    id: uuid.UUID
    campaign_id: uuid.UUID
    step_number: int
    channel: CommunicationChannel
    message_template_id: Optional[uuid.UUID] = None
    message_content: Optional[str] = None
    subject_template: Optional[str] = None
    delay_hours: int = 0  # Delay from previous step
    trigger_type: TriggerType = TriggerType.TIME_DELAY
    trigger_conditions: Optional[Dict[str, Any]] = None
    a_b_test_variant: Optional[str] = None  # "A", "B", etc.
    active: bool = True


class CampaignTarget(BaseModel):
    """Target criteria for campaign."""
    id: uuid.UUID
    campaign_id: uuid.UUID
    contact_ids: Optional[List[uuid.UUID]] = None
    property_types: Optional[List[str]] = None
    location_filters: Optional[Dict[str, Any]] = None
    lead_sources: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    custom_filters: Optional[Dict[str, Any]] = None
    exclude_contacted_days: Optional[int] = None  # Exclude if contacted within X days


class ABTestConfig(BaseModel):
    """A/B test configuration."""
    id: uuid.UUID
    campaign_id: uuid.UUID
    test_name: str
    variants: List[str] = ["A", "B"]  # Variant names
    traffic_split: Dict[str, float] = {"A": 0.5, "B": 0.5}  # Traffic allocation
    test_metric: str = "response_rate"  # Metric to optimize
    min_sample_size: int = 100
    confidence_level: float = 0.95
    winner_threshold: float = 0.05  # Minimum improvement to declare winner
    auto_promote_winner: bool = False
    test_duration_days: Optional[int] = None


class CampaignRecipient(BaseModel):
    """Individual recipient in a campaign."""
    id: uuid.UUID
    campaign_id: uuid.UUID
    contact_id: uuid.UUID
    conversation_id: Optional[uuid.UUID] = None
    current_step: int = 0
    status: str = "active"  # "active", "completed", "paused", "unsubscribed"
    a_b_variant: Optional[str] = None
    started_at: datetime
    last_message_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class CampaignMetrics(BaseModel):
    """Campaign performance metrics."""
    campaign_id: uuid.UUID
    total_recipients: int = 0
    messages_sent: int = 0
    messages_delivered: int = 0
    messages_opened: int = 0
    messages_clicked: int = 0
    responses_received: int = 0
    unsubscribes: int = 0
    bounces: int = 0
    
    # Calculated rates
    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    response_rate: float = 0.0
    unsubscribe_rate: float = 0.0
    bounce_rate: float = 0.0
    
    # A/B test metrics
    variant_metrics: Optional[Dict[str, Dict[str, Any]]] = None
    
    last_updated: datetime


class Campaign(BaseModel):
    """Complete campaign definition."""
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    campaign_type: CampaignType
    status: CampaignStatus = CampaignStatus.DRAFT
    
    # Scheduling
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    timezone: str = "UTC"
    
    # Campaign configuration
    steps: List[CampaignStep] = []
    targets: Optional[CampaignTarget] = None
    ab_test_config: Optional[ABTestConfig] = None
    
    # Recipients and execution
    recipients: List[CampaignRecipient] = []
    metrics: Optional[CampaignMetrics] = None
    
    # Metadata
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Settings
    max_recipients: Optional[int] = None
    send_rate_limit: Optional[int] = None  # Messages per hour
    respect_unsubscribes: bool = True
    track_opens: bool = True
    track_clicks: bool = True


class OutreachCampaignService:
    """Service for managing outreach campaigns."""
    
    def __init__(
        self, 
        message_service: Optional[MessageGenerationService] = None,
        conversation_service: Optional[ConversationManagementService] = None
    ):
        """Initialize the outreach campaign service."""
        self.message_service = message_service or MessageGenerationService()
        self.conversation_service = conversation_service or ConversationManagementService()
        self.campaigns: Dict[uuid.UUID, Campaign] = {}
        
    def create_campaign(
        self,
        name: str,
        campaign_type: CampaignType,
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Campaign:
        """
        Create a new campaign.
        
        Args:
            name: Campaign name
            campaign_type: Type of campaign
            description: Campaign description
            created_by: Creator identifier
            
        Returns:
            New campaign instance
        """
        campaign_id = uuid.uuid4()
        now = datetime.now()
        
        campaign = Campaign(
            id=campaign_id,
            name=name,
            description=description,
            campaign_type=campaign_type,
            created_by=created_by,
            created_at=now,
            updated_at=now,
            metrics=CampaignMetrics(
                campaign_id=campaign_id,
                last_updated=now
            )
        )
        
        self.campaigns[campaign_id] = campaign
        return campaign
    
    def add_campaign_step(
        self,
        campaign_id: uuid.UUID,
        channel: CommunicationChannel,
        message_content: Optional[str] = None,
        subject_template: Optional[str] = None,
        delay_hours: int = 0,
        trigger_type: TriggerType = TriggerType.TIME_DELAY,
        trigger_conditions: Optional[Dict[str, Any]] = None
    ) -> CampaignStep:
        """
        Add a step to a campaign sequence.
        
        Args:
            campaign_id: Campaign ID
            channel: Communication channel
            message_content: Message content template
            subject_template: Subject line template
            delay_hours: Delay from previous step
            trigger_type: Trigger type
            trigger_conditions: Trigger conditions
            
        Returns:
            Created campaign step
        """
        if campaign_id not in self.campaigns:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        campaign = self.campaigns[campaign_id]
        step_number = len(campaign.steps) + 1
        
        step = CampaignStep(
            id=uuid.uuid4(),
            campaign_id=campaign_id,
            step_number=step_number,
            channel=channel,
            message_content=message_content,
            subject_template=subject_template,
            delay_hours=delay_hours,
            trigger_type=trigger_type,
            trigger_conditions=trigger_conditions
        )
        
        campaign.steps.append(step)
        campaign.updated_at = datetime.now()
        
        return step
    
    def set_campaign_targets(
        self,
        campaign_id: uuid.UUID,
        contact_ids: Optional[List[uuid.UUID]] = None,
        property_types: Optional[List[str]] = None,
        location_filters: Optional[Dict[str, Any]] = None,
        lead_sources: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        custom_filters: Optional[Dict[str, Any]] = None,
        exclude_contacted_days: Optional[int] = None
    ) -> CampaignTarget:
        """
        Set targeting criteria for a campaign.
        
        Args:
            campaign_id: Campaign ID
            contact_ids: Specific contact IDs to target
            property_types: Property types to target
            location_filters: Location-based filters
            lead_sources: Lead sources to target
            tags: Contact tags to target
            custom_filters: Custom filtering criteria
            exclude_contacted_days: Exclude recently contacted leads
            
        Returns:
            Campaign target configuration
        """
        if campaign_id not in self.campaigns:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        campaign = self.campaigns[campaign_id]
        
        targets = CampaignTarget(
            id=uuid.uuid4(),
            campaign_id=campaign_id,
            contact_ids=contact_ids,
            property_types=property_types,
            location_filters=location_filters,
            lead_sources=lead_sources,
            tags=tags,
            custom_filters=custom_filters,
            exclude_contacted_days=exclude_contacted_days
        )
        
        campaign.targets = targets
        campaign.updated_at = datetime.now()
        
        return targets
    
    def setup_ab_test(
        self,
        campaign_id: uuid.UUID,
        test_name: str,
        variants: List[str] = ["A", "B"],
        traffic_split: Optional[Dict[str, float]] = None,
        test_metric: str = "response_rate",
        min_sample_size: int = 100,
        confidence_level: float = 0.95,
        auto_promote_winner: bool = False
    ) -> ABTestConfig:
        """
        Set up A/B testing for a campaign.
        
        Args:
            campaign_id: Campaign ID
            test_name: Name of the test
            variants: List of variant names
            traffic_split: Traffic allocation per variant
            test_metric: Metric to optimize
            min_sample_size: Minimum sample size per variant
            confidence_level: Statistical confidence level
            auto_promote_winner: Auto-promote winning variant
            
        Returns:
            A/B test configuration
        """
        if campaign_id not in self.campaigns:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        campaign = self.campaigns[campaign_id]
        
        # Default equal split if not provided
        if not traffic_split:
            split_value = 1.0 / len(variants)
            traffic_split = {variant: split_value for variant in variants}
        
        ab_config = ABTestConfig(
            id=uuid.uuid4(),
            campaign_id=campaign_id,
            test_name=test_name,
            variants=variants,
            traffic_split=traffic_split,
            test_metric=test_metric,
            min_sample_size=min_sample_size,
            confidence_level=confidence_level,
            auto_promote_winner=auto_promote_winner
        )
        
        campaign.ab_test_config = ab_config
        campaign.updated_at = datetime.now()
        
        return ab_config
    
    def start_campaign(self, campaign_id: uuid.UUID) -> bool:
        """
        Start a campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            True if started successfully
        """
        if campaign_id not in self.campaigns:
            return False
        
        campaign = self.campaigns[campaign_id]
        
        # Validate campaign is ready to start
        if not campaign.steps:
            raise ValueError("Campaign must have at least one step")
        
        if not campaign.targets:
            raise ValueError("Campaign must have targeting criteria")
        
        # Generate recipients based on targeting
        recipients = self._generate_recipients(campaign)
        campaign.recipients = recipients
        
        # Update campaign status
        campaign.status = CampaignStatus.ACTIVE
        campaign.start_date = datetime.now()
        campaign.updated_at = datetime.now()
        
        # Initialize metrics
        campaign.metrics.total_recipients = len(recipients)
        campaign.metrics.last_updated = datetime.now()
        
        return True
    
    def pause_campaign(self, campaign_id: uuid.UUID) -> bool:
        """Pause an active campaign."""
        if campaign_id not in self.campaigns:
            return False
        
        campaign = self.campaigns[campaign_id]
        if campaign.status == CampaignStatus.ACTIVE:
            campaign.status = CampaignStatus.PAUSED
            campaign.updated_at = datetime.now()
            return True
        
        return False
    
    def resume_campaign(self, campaign_id: uuid.UUID) -> bool:
        """Resume a paused campaign."""
        if campaign_id not in self.campaigns:
            return False
        
        campaign = self.campaigns[campaign_id]
        if campaign.status == CampaignStatus.PAUSED:
            campaign.status = CampaignStatus.ACTIVE
            campaign.updated_at = datetime.now()
            return True
        
        return False
    
    def stop_campaign(self, campaign_id: uuid.UUID) -> bool:
        """Stop a campaign."""
        if campaign_id not in self.campaigns:
            return False
        
        campaign = self.campaigns[campaign_id]
        if campaign.status in [CampaignStatus.ACTIVE, CampaignStatus.PAUSED]:
            campaign.status = CampaignStatus.COMPLETED
            campaign.end_date = datetime.now()
            campaign.updated_at = datetime.now()
            return True
        
        return False
    
    def process_campaigns(self) -> Dict[uuid.UUID, int]:
        """
        Process all active campaigns and send due messages.
        
        Returns:
            Dictionary of campaign_id -> messages_sent
        """
        results = {}
        
        for campaign_id, campaign in self.campaigns.items():
            if campaign.status != CampaignStatus.ACTIVE:
                continue
            
            messages_sent = self._process_campaign(campaign)
            results[campaign_id] = messages_sent
        
        return results
    
    def get_campaign_metrics(self, campaign_id: uuid.UUID) -> Optional[CampaignMetrics]:
        """Get campaign performance metrics."""
        if campaign_id not in self.campaigns:
            return None
        
        campaign = self.campaigns[campaign_id]
        self._update_campaign_metrics(campaign)
        return campaign.metrics
    
    def get_ab_test_results(self, campaign_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Get A/B test results for a campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            A/B test results with statistical analysis
        """
        if campaign_id not in self.campaigns:
            return None
        
        campaign = self.campaigns[campaign_id]
        if not campaign.ab_test_config:
            return None
        
        return self._analyze_ab_test(campaign)
    
    def _generate_recipients(self, campaign: Campaign) -> List[CampaignRecipient]:
        """Generate recipient list based on campaign targeting."""
        recipients = []
        
        if not campaign.targets:
            return recipients
        
        # For this implementation, we'll simulate recipient generation
        # In a real system, this would query the database based on targeting criteria
        
        contact_ids = campaign.targets.contact_ids or []
        
        # If no specific contacts, generate some sample ones for testing
        if not contact_ids:
            contact_ids = [uuid.uuid4() for _ in range(10)]
        
        now = datetime.now()
        
        for contact_id in contact_ids:
            # Assign A/B test variant if configured
            variant = None
            if campaign.ab_test_config:
                variant = self._assign_ab_variant(campaign.ab_test_config)
            
            recipient = CampaignRecipient(
                id=uuid.uuid4(),
                campaign_id=campaign.id,
                contact_id=contact_id,
                a_b_variant=variant,
                started_at=now
            )
            
            recipients.append(recipient)
        
        return recipients
    
    def _assign_ab_variant(self, ab_config: ABTestConfig) -> str:
        """Assign A/B test variant based on traffic split."""
        rand = random.random()
        cumulative = 0.0
        
        for variant, split in ab_config.traffic_split.items():
            cumulative += split
            if rand <= cumulative:
                return variant
        
        # Fallback to first variant
        return ab_config.variants[0]
    
    def _process_campaign(self, campaign: Campaign) -> int:
        """Process a single campaign and send due messages."""
        messages_sent = 0
        now = datetime.now()
        
        for recipient in campaign.recipients:
            if recipient.status != "active":
                continue
            
            # Check if recipient is ready for next step
            if self._is_recipient_ready_for_next_step(recipient, campaign, now):
                success = self._send_campaign_message(recipient, campaign)
                if success:
                    messages_sent += 1
                    recipient.current_step += 1
                    recipient.last_message_at = now
                    
                    # Check if recipient completed all steps
                    if recipient.current_step >= len(campaign.steps):
                        recipient.status = "completed"
                        recipient.completed_at = now
        
        # Update campaign metrics
        campaign.metrics.messages_sent += messages_sent
        campaign.metrics.last_updated = now
        
        return messages_sent
    
    def _is_recipient_ready_for_next_step(
        self, 
        recipient: CampaignRecipient, 
        campaign: Campaign, 
        current_time: datetime
    ) -> bool:
        """Check if recipient is ready for the next campaign step."""
        if recipient.current_step >= len(campaign.steps):
            return False
        
        step = campaign.steps[recipient.current_step]
        
        # Check delay from last message
        if recipient.last_message_at:
            time_since_last = current_time - recipient.last_message_at
            if time_since_last.total_seconds() < step.delay_hours * 3600:
                return False
        elif recipient.current_step > 0:
            # First step after start
            time_since_start = current_time - recipient.started_at
            if time_since_start.total_seconds() < step.delay_hours * 3600:
                return False
        
        # Check trigger conditions
        if step.trigger_type == TriggerType.RESPONSE_BASED:
            # Would check if recipient responded to previous message
            # For now, simulate random response
            return random.random() > 0.7
        
        return True
    
    def _send_campaign_message(self, recipient: CampaignRecipient, campaign: Campaign) -> bool:
        """Send a campaign message to a recipient."""
        if recipient.current_step >= len(campaign.steps):
            return False
        
        step = campaign.steps[recipient.current_step]
        
        try:
            # Get or create conversation
            conversation_id = recipient.conversation_id
            if not conversation_id:
                # Create new conversation
                conversation = self.conversation_service.create_conversation(
                    contact_id=recipient.contact_id,
                    subject=f"Campaign: {campaign.name}"
                )
                conversation_id = conversation.id
                recipient.conversation_id = conversation_id
            
            # Generate message content
            message_content = step.message_content or "Default campaign message"
            
            # Use A/B test variant if applicable
            if recipient.a_b_variant and step.a_b_test_variant:
                if recipient.a_b_variant != step.a_b_test_variant:
                    # Skip this step for this variant
                    return True
            
            # Send message through conversation service
            self.conversation_service.add_message(
                conversation_id=conversation_id,
                channel=step.channel,
                direction="outbound",
                content=message_content,
                subject=step.subject_template,
                metadata={
                    "campaign_id": str(campaign.id),
                    "campaign_step": step.step_number,
                    "ab_variant": recipient.a_b_variant
                }
            )
            
            return True
            
        except Exception as e:
            # Log error in real implementation
            print(f"Error sending campaign message: {e}")
            return False
    
    def _update_campaign_metrics(self, campaign: Campaign) -> None:
        """Update campaign performance metrics."""
        if not campaign.metrics:
            return
        
        metrics = campaign.metrics
        
        # Calculate basic metrics
        total_sent = metrics.messages_sent
        if total_sent > 0:
            metrics.delivery_rate = metrics.messages_delivered / total_sent
            metrics.open_rate = metrics.messages_opened / total_sent
            metrics.click_rate = metrics.messages_clicked / total_sent
            metrics.response_rate = metrics.responses_received / total_sent
            metrics.bounce_rate = metrics.bounces / total_sent
            metrics.unsubscribe_rate = metrics.unsubscribes / total_sent
        
        # Update A/B test metrics if applicable
        if campaign.ab_test_config:
            metrics.variant_metrics = self._calculate_variant_metrics(campaign)
        
        metrics.last_updated = datetime.now()
    
    def _calculate_variant_metrics(self, campaign: Campaign) -> Dict[str, Dict[str, Any]]:
        """Calculate metrics for each A/B test variant."""
        variant_metrics = {}
        
        if not campaign.ab_test_config:
            return variant_metrics
        
        # Group recipients by variant
        variant_recipients = {}
        for recipient in campaign.recipients:
            if recipient.a_b_variant:
                if recipient.a_b_variant not in variant_recipients:
                    variant_recipients[recipient.a_b_variant] = []
                variant_recipients[recipient.a_b_variant].append(recipient)
        
        # Calculate metrics for each variant
        for variant, recipients in variant_recipients.items():
            total_recipients = len(recipients)
            completed_recipients = len([r for r in recipients if r.status == "completed"])
            
            variant_metrics[variant] = {
                "total_recipients": total_recipients,
                "completed_recipients": completed_recipients,
                "completion_rate": completed_recipients / total_recipients if total_recipients > 0 else 0,
                "avg_steps_completed": sum(r.current_step for r in recipients) / total_recipients if total_recipients > 0 else 0
            }
        
        return variant_metrics
    
    def _analyze_ab_test(self, campaign: Campaign) -> Dict[str, Any]:
        """Perform statistical analysis of A/B test results."""
        if not campaign.ab_test_config or not campaign.metrics.variant_metrics:
            return {}
        
        variant_metrics = campaign.metrics.variant_metrics
        test_metric = campaign.ab_test_config.test_metric
        
        # Extract metric values for each variant
        variant_values = {}
        for variant, metrics in variant_metrics.items():
            if test_metric == "response_rate":
                variant_values[variant] = metrics.get("completion_rate", 0)
            elif test_metric == "completion_rate":
                variant_values[variant] = metrics.get("completion_rate", 0)
            else:
                variant_values[variant] = metrics.get(test_metric, 0)
        
        # Find best performing variant
        best_variant = max(variant_values.keys(), key=lambda k: variant_values[k])
        best_value = variant_values[best_variant]
        
        # Calculate improvement over other variants
        improvements = {}
        for variant, value in variant_values.items():
            if variant != best_variant and value > 0:
                improvement = (best_value - value) / value
                improvements[variant] = improvement
        
        # Determine statistical significance (simplified)
        is_significant = any(imp > campaign.ab_test_config.winner_threshold for imp in improvements.values())
        
        return {
            "test_name": campaign.ab_test_config.test_name,
            "test_metric": test_metric,
            "variant_values": variant_values,
            "best_variant": best_variant,
            "best_value": best_value,
            "improvements": improvements,
            "is_significant": is_significant,
            "sample_sizes": {v: m["total_recipients"] for v, m in variant_metrics.items()},
            "recommendation": f"Variant {best_variant} is the winner" if is_significant else "No significant difference detected"
        }
    
    def get_campaign(self, campaign_id: uuid.UUID) -> Optional[Campaign]:
        """Get a campaign by ID."""
        return self.campaigns.get(campaign_id)
    
    def list_campaigns(
        self, 
        status: Optional[CampaignStatus] = None,
        campaign_type: Optional[CampaignType] = None
    ) -> List[Campaign]:
        """List campaigns with optional filtering."""
        campaigns = list(self.campaigns.values())
        
        if status:
            campaigns = [c for c in campaigns if c.status == status]
        
        if campaign_type:
            campaigns = [c for c in campaigns if c.campaign_type == campaign_type]
        
        # Sort by created date (newest first)
        campaigns.sort(key=lambda c: c.created_at, reverse=True)
        
        return campaigns
    
    def delete_campaign(self, campaign_id: uuid.UUID) -> bool:
        """Delete a campaign."""
        if campaign_id in self.campaigns:
            del self.campaigns[campaign_id]
            return True
        return False


# Utility functions
def create_drip_campaign(
    service: OutreachCampaignService,
    name: str,
    messages: List[Dict[str, Any]],
    target_contacts: List[uuid.UUID]
) -> Campaign:
    """
    Create a simple drip campaign with predefined messages.
    
    Args:
        service: Campaign service instance
        name: Campaign name
        messages: List of message dictionaries with 'content', 'channel', 'delay_hours'
        target_contacts: List of contact IDs to target
        
    Returns:
        Created campaign
    """
    campaign = service.create_campaign(name, CampaignType.DRIP)
    
    # Add steps
    for i, msg in enumerate(messages):
        service.add_campaign_step(
            campaign.id,
            channel=msg.get("channel", CommunicationChannel.EMAIL),
            message_content=msg.get("content", ""),
            subject_template=msg.get("subject", f"{name} - Message {i+1}"),
            delay_hours=msg.get("delay_hours", 24 * i)  # Default 1 day between messages
        )
    
    # Set targets
    service.set_campaign_targets(campaign.id, contact_ids=target_contacts)
    
    return campaign


def create_ab_test_campaign(
    service: OutreachCampaignService,
    name: str,
    variant_a_content: str,
    variant_b_content: str,
    target_contacts: List[uuid.UUID],
    channel: CommunicationChannel = CommunicationChannel.EMAIL
) -> Campaign:
    """
    Create a simple A/B test campaign.
    
    Args:
        service: Campaign service instance
        name: Campaign name
        variant_a_content: Content for variant A
        variant_b_content: Content for variant B
        target_contacts: List of contact IDs to target
        channel: Communication channel
        
    Returns:
        Created campaign with A/B test
    """
    campaign = service.create_campaign(name, CampaignType.SINGLE_MESSAGE)
    
    # Add steps for each variant
    step_a = service.add_campaign_step(
        campaign.id,
        channel=channel,
        message_content=variant_a_content,
        subject_template=f"{name} - Variant A"
    )
    step_a.a_b_test_variant = "A"
    
    step_b = service.add_campaign_step(
        campaign.id,
        channel=channel,
        message_content=variant_b_content,
        subject_template=f"{name} - Variant B"
    )
    step_b.a_b_test_variant = "B"
    
    # Set up A/B test
    service.setup_ab_test(campaign.id, f"{name} A/B Test")
    
    # Set targets
    service.set_campaign_targets(campaign.id, contact_ids=target_contacts)
    
    return campaign


def get_campaign_performance_summary(
    service: OutreachCampaignService,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Get performance summary across all campaigns.
    
    Args:
        service: Campaign service instance
        date_from: Start date for analysis
        date_to: End date for analysis
        
    Returns:
        Performance summary dictionary
    """
    campaigns = service.list_campaigns()
    
    # Filter by date if provided
    if date_from or date_to:
        filtered_campaigns = []
        for campaign in campaigns:
            if date_from and campaign.created_at < date_from:
                continue
            if date_to and campaign.created_at > date_to:
                continue
            filtered_campaigns.append(campaign)
        campaigns = filtered_campaigns
    
    if not campaigns:
        return {}
    
    # Aggregate metrics
    total_campaigns = len(campaigns)
    total_recipients = sum(c.metrics.total_recipients if c.metrics else 0 for c in campaigns)
    total_sent = sum(c.metrics.messages_sent if c.metrics else 0 for c in campaigns)
    total_delivered = sum(c.metrics.messages_delivered if c.metrics else 0 for c in campaigns)
    total_opened = sum(c.metrics.messages_opened if c.metrics else 0 for c in campaigns)
    total_responses = sum(c.metrics.responses_received if c.metrics else 0 for c in campaigns)
    
    # Calculate overall rates
    delivery_rate = total_delivered / total_sent if total_sent > 0 else 0
    open_rate = total_opened / total_sent if total_sent > 0 else 0
    response_rate = total_responses / total_sent if total_sent > 0 else 0
    
    # Status distribution
    status_counts = {}
    for campaign in campaigns:
        status = campaign.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Type distribution
    type_counts = {}
    for campaign in campaigns:
        campaign_type = campaign.campaign_type.value
        type_counts[campaign_type] = type_counts.get(campaign_type, 0) + 1
    
    return {
        "total_campaigns": total_campaigns,
        "total_recipients": total_recipients,
        "total_messages_sent": total_sent,
        "overall_delivery_rate": delivery_rate,
        "overall_open_rate": open_rate,
        "overall_response_rate": response_rate,
        "status_distribution": status_counts,
        "type_distribution": type_counts,
        "date_range": {
            "from": date_from.isoformat() if date_from else None,
            "to": date_to.isoformat() if date_to else None
        }
    }