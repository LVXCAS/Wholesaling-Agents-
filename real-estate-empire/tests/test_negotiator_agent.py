"""
Tests for Negotiator Agent - Communication and Negotiation
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.agents.negotiator_agent import (
    NegotiatorAgent, CommunicationChannel, MessageTemplate, 
    OutreachCampaign, ResponseAnalysis, NegotiationStrategy
)
from app.core.agent_state import AgentState, Deal, DealStatus, StateManager, AgentType


class TestNegotiatorAgent:
    """Test cases for NegotiatorAgent"""
    
    @pytest.fixture
    def negotiator_agent(self):
        """Create a negotiator agent for testing"""
        return NegotiatorAgent()
    
    @pytest.fixture
    def sample_deal(self):
        """Create a sample deal for testing"""
        return Deal(
            property_address="123 Main St",
            city="Anytown",
            state="CA",
            zip_code="12345",
            status=DealStatus.APPROVED,
            listing_price=250000,
            estimated_value=240000,
            owner_info={
                "owner_name": "John Smith",
                "owner_phone": "(555) 123-4567",
                "owner_email": "john@example.com"
            },
            motivation_indicators=["job_relocation", "quick_sale"]
        )
    
    @pytest.fixture
    def sample_state(self, sample_deal):
        """Create a sample agent state"""
        state = StateManager.create_initial_state()
        state = StateManager.add_deal(state, sample_deal)
        return state
    
    def test_agent_initialization(self, negotiator_agent):
        """Test agent initialization"""
        assert negotiator_agent.agent_type == AgentType.NEGOTIATOR
        assert negotiator_agent.name == "NegotiatorAgent"
        assert len(negotiator_agent.capabilities) == 5
        assert len(negotiator_agent.message_templates) > 0
        
        # Check capabilities
        capability_names = [cap.name for cap in negotiator_agent.capabilities]
        expected_capabilities = [
            "outreach_campaign_creation",
            "message_generation",
            "response_analysis",
            "negotiation_strategy_development",
            "negotiation_management"
        ]
        
        for expected in expected_capabilities:
            assert expected in capability_names
    
    def test_default_message_templates(self, negotiator_agent):
        """Test default message templates are created"""
        templates = negotiator_agent.message_templates
        
        # Check that templates exist for different channels and purposes
        email_templates = [t for t in templates.values() if t.channel == CommunicationChannel.EMAIL]
        sms_templates = [t for t in templates.values() if t.channel == CommunicationChannel.SMS]
        
        assert len(email_templates) > 0
        assert len(sms_templates) > 0
        
        # Check template structure
        for template in templates.values():
            assert template.name
            assert template.content
            assert template.channel in CommunicationChannel
            assert template.purpose
            assert isinstance(template.variables, list)
    
    def test_get_available_tasks(self, negotiator_agent):
        """Test available tasks"""
        tasks = negotiator_agent.get_available_tasks()
        
        expected_tasks = [
            "create_outreach_campaign",
            "generate_message",
            "analyze_response",
            "develop_negotiation_strategy",
            "manage_negotiation",
            "initiate_outreach",
            "handle_responses"
        ]
        
        for expected_task in expected_tasks:
            assert expected_task in tasks
    
    @pytest.mark.asyncio
    async def test_execute_task_create_outreach_campaign(self, negotiator_agent, sample_deal, sample_state):
        """Test creating outreach campaign task"""
        # Mock the agent executor
        negotiator_agent.agent_executor = AsyncMock()
        negotiator_agent.agent_executor.ainvoke = AsyncMock(return_value={
            "output": "Campaign created successfully with email and SMS channels"
        })
        
        result = await negotiator_agent.execute_task(
            "create_outreach_campaign",
            {"deal": sample_deal.dict()},
            sample_state
        )
        
        assert result["success"] is True
        assert "campaign" in result
        assert "campaign_id" in result
        
        # Check campaign was stored
        campaign_id = result["campaign_id"]
        assert campaign_id in negotiator_agent.active_campaigns
        
        campaign = negotiator_agent.active_campaigns[campaign_id]
        assert campaign.deal_id == sample_deal.id
        assert campaign.status == "active"
    
    @pytest.mark.asyncio
    async def test_execute_task_generate_message(self, negotiator_agent, sample_deal):
        """Test message generation task"""
        result = await negotiator_agent.execute_task(
            "generate_message",
            {
                "deal": sample_deal.dict(),
                "channel": CommunicationChannel.EMAIL,
                "purpose": "initial_contact"
            },
            {}
        )
        
        assert result["success"] is True
        assert "message" in result
        assert result["message"]["channel"] == CommunicationChannel.EMAIL.value
        assert "content" in result["message"]
        assert "subject" in result["message"]
    
    @pytest.mark.asyncio
    async def test_execute_task_analyze_response(self, negotiator_agent):
        """Test response analysis task"""
        # Mock the agent executor
        negotiator_agent.agent_executor = AsyncMock()
        negotiator_agent.agent_executor.ainvoke = AsyncMock(return_value={
            "output": "Positive response with high interest level"
        })
        
        communication = {
            "channel": "email",
            "content": "Yes, I'm interested in your offer. When can we talk?",
            "timestamp": datetime.now().isoformat()
        }
        
        result = await negotiator_agent.execute_task(
            "analyze_response",
            {"communication": communication},
            {}
        )
        
        assert result["success"] is True
        assert "analysis" in result
        assert "recommended_actions" in result
    
    @pytest.mark.asyncio
    async def test_execute_task_develop_negotiation_strategy(self, negotiator_agent, sample_deal):
        """Test negotiation strategy development task"""
        # Mock the agent executor
        negotiator_agent.agent_executor = AsyncMock()
        negotiator_agent.agent_executor.ainvoke = AsyncMock(return_value={
            "output": "Collaborative approach recommended with 85% initial offer"
        })
        
        result = await negotiator_agent.execute_task(
            "develop_negotiation_strategy",
            {
                "deal": sample_deal.dict(),
                "seller_profile": {"motivation_level": 0.8},
                "market_context": {"market_temperature": "neutral"}
            },
            {}
        )
        
        assert result["success"] is True
        assert "strategy" in result
        assert "strategy_id" in result
        
        # Check strategy was stored
        strategy_id = result["strategy_id"]
        assert strategy_id in negotiator_agent.negotiation_strategies
    
    @pytest.mark.asyncio
    async def test_process_state_with_approved_deals(self, negotiator_agent, sample_state):
        """Test processing state with approved deals"""
        # Mock the agent executor
        negotiator_agent.agent_executor = AsyncMock()
        negotiator_agent.agent_executor.ainvoke = AsyncMock(return_value={
            "output": "Campaign created and outreach initiated"
        })
        
        # Ensure deal is approved and not yet contacted
        deals = sample_state["current_deals"]
        deals[0]["status"] = DealStatus.APPROVED.value
        deals[0]["outreach_initiated"] = False
        
        updated_state = await negotiator_agent.process_state(sample_state)
        
        # Check that outreach was initiated
        updated_deals = updated_state["current_deals"]
        assert updated_deals[0]["outreach_initiated"] is True
        assert updated_deals[0]["status"] == DealStatus.OUTREACH_INITIATED.value
        
        # Check that negotiation was added
        negotiations = updated_state["active_negotiations"]
        assert len(negotiations) > 0
        assert negotiations[0]["deal_id"] == deals[0]["id"]
        assert negotiations[0]["status"] == "initial_outreach"
    
    def test_find_template(self, negotiator_agent):
        """Test finding message templates"""
        # Test finding existing template
        template = negotiator_agent._find_template(CommunicationChannel.EMAIL, "initial_contact")
        assert template is not None
        assert template.channel == CommunicationChannel.EMAIL
        assert template.purpose == "initial_contact"
        
        # Test finding non-existent template
        template = negotiator_agent._find_template(CommunicationChannel.PHONE, "nonexistent")
        assert template is None
    
    def test_personalize_message(self, negotiator_agent, sample_deal):
        """Test message personalization"""
        # Get a template
        template = negotiator_agent._find_template(CommunicationChannel.EMAIL, "initial_contact")
        assert template is not None
        
        # Personalize the message
        personalized = negotiator_agent._personalize_message(
            template, 
            sample_deal.dict(), 
            {}
        )
        
        assert personalized["channel"] == CommunicationChannel.EMAIL.value
        assert "John Smith" in personalized["content"]  # Owner name should be replaced
        assert "123 Main St" in personalized["content"]  # Property address should be replaced
        assert personalized["personalized"] is True
    
    def test_parse_campaign_creation_result(self, negotiator_agent, sample_deal):
        """Test parsing campaign creation result"""
        result_text = "Campaign created with email and SMS channels"
        
        parsed = negotiator_agent._parse_campaign_creation_result(result_text, sample_deal.dict())
        
        assert "sequence" in parsed
        assert "initial_messages" in parsed
        assert isinstance(parsed["sequence"], list)
        assert isinstance(parsed["initial_messages"], list)
    
    def test_parse_response_analysis(self, negotiator_agent):
        """Test parsing response analysis result"""
        result_text = "Positive response with high interest"
        
        parsed = negotiator_agent._parse_response_analysis(result_text)
        
        assert "overall_sentiment" in parsed
        assert "interest_level" in parsed
        assert "recommended_next_steps" in parsed
        assert isinstance(parsed["overall_sentiment"], (int, float))
        assert isinstance(parsed["interest_level"], (int, float))
        assert isinstance(parsed["recommended_next_steps"], list)
    
    def test_parse_negotiation_strategy(self, negotiator_agent, sample_deal):
        """Test parsing negotiation strategy result"""
        result_text = "Collaborative approach with 85% initial offer"
        
        parsed = negotiator_agent._parse_negotiation_strategy(result_text, sample_deal.dict())
        
        assert "approach" in parsed
        assert "initial_offer_percentage" in parsed
        assert "primary_tactics" in parsed
        assert parsed["approach"] in ["collaborative", "competitive", "accommodating"]
        assert isinstance(parsed["initial_offer_percentage"], (int, float))
        assert isinstance(parsed["primary_tactics"], list)
    
    def test_determine_next_actions(self, negotiator_agent):
        """Test determining next actions based on analysis"""
        # High interest analysis
        high_interest_analysis = {
            "interest_level": 0.8,
            "overall_sentiment": 0.6
        }
        
        actions = negotiator_agent._determine_next_actions(high_interest_analysis, {})
        
        assert len(actions) > 0
        assert any(action["action"] == "schedule_call" for action in actions)
        
        # Low interest analysis
        low_interest_analysis = {
            "interest_level": 0.2,
            "overall_sentiment": -0.4
        }
        
        actions = negotiator_agent._determine_next_actions(low_interest_analysis, {})
        
        assert len(actions) > 0
        assert any(action["action"] == "address_concerns" for action in actions)
    
    @pytest.mark.asyncio
    async def test_execute_initial_messages(self, negotiator_agent):
        """Test executing initial messages"""
        campaign = {
            "id": "test-campaign-123",
            "deal_id": "test-deal-456"
        }
        
        messages = [
            {
                "channel": "email",
                "subject": "Test Subject",
                "content": "Test content"
            },
            {
                "channel": "sms",
                "content": "Test SMS content"
            }
        ]
        
        # This should not raise an exception
        await negotiator_agent._execute_initial_messages(campaign, messages)
        
        # Check that messages sent counter was incremented
        assert negotiator_agent.messages_sent_today == 2
    
    def test_agent_metrics_tracking(self, negotiator_agent):
        """Test agent metrics are tracked properly"""
        initial_campaigns = negotiator_agent.campaigns_created
        initial_messages = negotiator_agent.messages_sent_today
        
        # Simulate creating a campaign
        negotiator_agent.campaigns_created += 1
        negotiator_agent.messages_sent_today += 3
        
        assert negotiator_agent.campaigns_created == initial_campaigns + 1
        assert negotiator_agent.messages_sent_today == initial_messages + 3


class TestMessageTemplate:
    """Test cases for MessageTemplate"""
    
    def test_message_template_creation(self):
        """Test creating a message template"""
        template = MessageTemplate(
            name="Test Template",
            channel=CommunicationChannel.EMAIL,
            subject="Test Subject",
            content="Hello {owner_name}, interested in {property_address}",
            variables=["owner_name", "property_address"],
            tone="professional",
            purpose="initial_contact"
        )
        
        assert template.name == "Test Template"
        assert template.channel == CommunicationChannel.EMAIL
        assert template.subject == "Test Subject"
        assert "owner_name" in template.variables
        assert "property_address" in template.variables
        assert template.tone == "professional"
        assert template.purpose == "initial_contact"
        assert template.success_rate == 0.0
        assert template.usage_count == 0


class TestOutreachCampaign:
    """Test cases for OutreachCampaign"""
    
    def test_outreach_campaign_creation(self):
        """Test creating an outreach campaign"""
        campaign = OutreachCampaign(
            deal_id="test-deal-123",
            name="Test Campaign",
            description="Test campaign description",
            channels=[CommunicationChannel.EMAIL, CommunicationChannel.SMS],
            max_attempts=3
        )
        
        assert campaign.deal_id == "test-deal-123"
        assert campaign.name == "Test Campaign"
        assert CommunicationChannel.EMAIL in campaign.channels
        assert CommunicationChannel.SMS in campaign.channels
        assert campaign.max_attempts == 3
        assert campaign.status == "draft"
        assert campaign.messages_sent == 0
        assert campaign.responses_received == 0


class TestResponseAnalysis:
    """Test cases for ResponseAnalysis"""
    
    def test_response_analysis_creation(self):
        """Test creating a response analysis"""
        analysis = ResponseAnalysis(
            communication_id="comm-123",
            overall_sentiment=0.7,
            emotional_tone="positive",
            confidence_level=0.9,
            interest_level=0.8,
            urgency_indicators=["timeline_mentioned"],
            key_points=["interested_in_cash_offer"],
            objections_raised=["price_too_low"],
            recommended_next_steps=["schedule_call", "provide_market_analysis"]
        )
        
        assert analysis.communication_id == "comm-123"
        assert analysis.overall_sentiment == 0.7
        assert analysis.emotional_tone == "positive"
        assert analysis.confidence_level == 0.9
        assert analysis.interest_level == 0.8
        assert "timeline_mentioned" in analysis.urgency_indicators
        assert "interested_in_cash_offer" in analysis.key_points
        assert "price_too_low" in analysis.objections_raised
        assert "schedule_call" in analysis.recommended_next_steps


class TestNegotiationStrategy:
    """Test cases for NegotiationStrategy"""
    
    def test_negotiation_strategy_creation(self):
        """Test creating a negotiation strategy"""
        strategy = NegotiationStrategy(
            deal_id="deal-123",
            approach="collaborative",
            initial_offer_percentage=0.85,
            minimum_acceptable_price=200000,
            maximum_offer_price=250000,
            primary_tactics=["market_data_support", "timeline_flexibility"],
            fallback_tactics=["price_increase", "terms_adjustment"],
            seller_motivation_factors=["job_relocation", "quick_sale"]
        )
        
        assert strategy.deal_id == "deal-123"
        assert strategy.approach == "collaborative"
        assert strategy.initial_offer_percentage == 0.85
        assert strategy.minimum_acceptable_price == 200000
        assert strategy.maximum_offer_price == 250000
        assert "market_data_support" in strategy.primary_tactics
        assert "price_increase" in strategy.fallback_tactics
        assert "job_relocation" in strategy.seller_motivation_factors


if __name__ == "__main__":
    pytest.main([__file__])