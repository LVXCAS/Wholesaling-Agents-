"""
Negotiator Agent - Autonomous Communication and Deal Negotiation
Specialized agent for seller outreach, communication, and negotiation management
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
import re

from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from ..core.base_agent import BaseAgent, AgentCapability, AgentStatus
from ..core.agent_state import AgentState, AgentType, Deal, DealStatus, StateManager, Negotiation
from ..core.agent_tools import tool_registry, LangChainToolAdapter
from ..core.llm_config import llm_manager
from .negotiation_coaching_integration import NegotiationCoachingIntegration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CommunicationChannel(str, Enum):
    """Communication channels available"""
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    VOICEMAIL = "voicemail"
    DIRECT_MAIL = "direct_mail"


class MessageTemplate(BaseModel):
    """Template for communication messages"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    channel: CommunicationChannel
    subject: Optional[str] = None
    content: str
    variables: List[str] = Field(default_factory=list)
    tone: str = "professional"  # professional, friendly, urgent, casual
    purpose: str  # initial_contact, follow_up, negotiation, closing
    success_rate: float = 0.0
    usage_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


class OutreachCampaign(BaseModel):
    """Outreach campaign configuration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deal_id: str
    name: str
    description: str
    
    # Campaign Configuration
    channels: List[CommunicationChannel] = Field(default_factory=list)
    sequence: List[Dict[str, Any]] = Field(default_factory=list)  # Ordered steps
    personalization_level: str = "high"  # low, medium, high
    
    # Timing Configuration
    initial_delay_hours: int = 0
    follow_up_intervals: List[int] = Field(default_factory=lambda: [24, 72, 168])  # hours
    max_attempts: int = 5
    
    # Status Tracking
    status: str = "draft"  # draft, active, paused, completed, cancelled
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Performance Metrics
    messages_sent: int = 0
    responses_received: int = 0
    positive_responses: int = 0
    appointments_scheduled: int = 0
    
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)


class CommunicationHistory(BaseModel):
    """History of communications with a contact"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deal_id: str
    contact_id: str
    
    # Message Details
    channel: CommunicationChannel
    direction: str  # inbound, outbound
    subject: Optional[str] = None
    content: str
    template_used: Optional[str] = None
    
    # Status and Tracking
    status: str = "sent"  # sent, delivered, read, responded, failed
    sent_at: datetime = Field(default_factory=datetime.now)
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    
    # Analysis Results
    sentiment_score: Optional[float] = None  # -1.0 to 1.0
    interest_level: Optional[float] = None   # 0.0 to 1.0
    urgency_level: Optional[float] = None    # 0.0 to 1.0
    objections: List[str] = Field(default_factory=list)
    questions: List[str] = Field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NegotiationStrategy(BaseModel):
    """Negotiation strategy for a specific deal"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deal_id: str
    
    # Strategy Configuration
    approach: str = "collaborative"  # collaborative, competitive, accommodating
    initial_offer_percentage: float = 0.85  # Percentage of asking price
    minimum_acceptable_price: Optional[float] = None
    maximum_offer_price: Optional[float] = None
    
    # Negotiation Tactics
    primary_tactics: List[str] = Field(default_factory=list)
    fallback_tactics: List[str] = Field(default_factory=list)
    concession_strategy: Dict[str, Any] = Field(default_factory=dict)
    
    # Market Context
    market_conditions: Dict[str, Any] = Field(default_factory=dict)
    comparable_sales: List[Dict[str, Any]] = Field(default_factory=list)
    seller_motivation_factors: List[str] = Field(default_factory=list)
    
    # Timeline
    target_closing_date: Optional[datetime] = None
    negotiation_deadline: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)


class ResponseAnalysis(BaseModel):
    """Analysis of seller response"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    communication_id: str
    
    # Sentiment Analysis
    overall_sentiment: float = Field(ge=-1.0, le=1.0)  # -1.0 (negative) to 1.0 (positive)
    emotional_tone: str = "neutral"  # positive, negative, neutral, mixed
    confidence_level: float = Field(ge=0.0, le=1.0)
    
    # Interest Analysis
    interest_level: float = Field(ge=0.0, le=1.0)  # 0.0 (no interest) to 1.0 (very interested)
    urgency_indicators: List[str] = Field(default_factory=list)
    motivation_signals: List[str] = Field(default_factory=list)
    
    # Content Analysis
    key_points: List[str] = Field(default_factory=list)
    objections_raised: List[str] = Field(default_factory=list)
    questions_asked: List[str] = Field(default_factory=list)
    concerns_expressed: List[str] = Field(default_factory=list)
    
    # Negotiation Insights
    price_sensitivity: Optional[float] = None  # 0.0 (flexible) to 1.0 (rigid)
    timeline_flexibility: Optional[float] = None
    terms_preferences: Dict[str, Any] = Field(default_factory=dict)
    
    # Recommended Actions
    suggested_response_tone: str = "professional"
    recommended_next_steps: List[str] = Field(default_factory=list)
    follow_up_timing: Optional[int] = None  # hours
    escalation_needed: bool = False
    
    analyzed_at: datetime = Field(default_factory=datetime.now)


class NegotiatorAgent(BaseAgent):
    """
    Negotiator Agent - Autonomous Communication and Deal Negotiation
    
    Responsibilities:
    - Initiate and manage outreach campaigns to property owners
    - Generate personalized messages across multiple channels
    - Analyze seller responses and sentiment
    - Develop and execute negotiation strategies
    - Handle objections and build rapport with sellers
    - Coordinate multi-channel communication sequences
    - Track communication effectiveness and optimize approaches
    """
    
    def __init__(self, name: str = "NegotiatorAgent", description: str = "Autonomous communication and negotiation agent"):
        # Define agent capabilities
        capabilities = [
            AgentCapability(
                name="outreach_campaign_creation",
                description="Create and configure multi-channel outreach campaigns",
                input_schema={
                    "deal": "Deal",
                    "campaign_config": "Dict[str, Any]"
                },
                output_schema={
                    "campaign": "OutreachCampaign",
                    "initial_messages": "List[Dict[str, Any]]"
                },
                required_tools=["communication", "market_data"],
                estimated_duration=180
            ),
            AgentCapability(
                name="message_generation",
                description="Generate personalized messages for different channels and purposes",
                input_schema={
                    "deal": "Deal",
                    "channel": "CommunicationChannel",
                    "purpose": "str",
                    "context": "Dict[str, Any]"
                },
                output_schema={
                    "message": "Dict[str, Any]",
                    "personalization_score": "float"
                },
                required_tools=["communication"],
                estimated_duration=60
            ),
            AgentCapability(
                name="response_analysis",
                description="Analyze seller responses for sentiment, interest, and negotiation insights",
                input_schema={
                    "communication": "CommunicationHistory"
                },
                output_schema={
                    "analysis": "ResponseAnalysis",
                    "recommended_actions": "List[str]"
                },
                required_tools=["communication"],
                estimated_duration=45
            ),
            AgentCapability(
                name="negotiation_strategy_development",
                description="Develop negotiation strategies based on deal and seller analysis",
                input_schema={
                    "deal": "Deal",
                    "seller_profile": "Dict[str, Any]",
                    "market_context": "Dict[str, Any]"
                },
                output_schema={
                    "strategy": "NegotiationStrategy",
                    "tactics": "List[str]"
                },
                required_tools=["property_analysis", "market_data"],
                estimated_duration=120
            ),
            AgentCapability(
                name="negotiation_management",
                description="Manage active negotiations and coordinate responses",
                input_schema={
                    "negotiation": "Negotiation",
                    "latest_communication": "CommunicationHistory"
                },
                output_schema={
                    "updated_negotiation": "Negotiation",
                    "next_actions": "List[Dict[str, Any]]"
                },
                required_tools=["communication", "financial_calculator"],
                estimated_duration=90
            )
        ]
        
        # Negotiator-specific attributes (initialize before base agent)
        self.message_templates: Dict[str, MessageTemplate] = {}
        self.active_campaigns: Dict[str, OutreachCampaign] = {}
        self.communication_history: Dict[str, List[CommunicationHistory]] = {}
        self.negotiation_strategies: Dict[str, NegotiationStrategy] = {}
        
        # Performance metrics
        self.campaigns_created = 0
        self.messages_sent_today = 0
        self.responses_received_today = 0
        self.negotiations_active = 0
        self.average_response_rate = 0.0
        self.average_sentiment_score = 0.0
        
        # Initialize agent executor
        self.agent_executor: Optional[AgentExecutor] = None
        
        # Initialize coaching integration
        self.coaching_integration: Optional[NegotiationCoachingIntegration] = None
        
        # Initialize base agent
        super().__init__(
            agent_type=AgentType.NEGOTIATOR,
            name=name,
            description=description,
            capabilities=capabilities
        )
        
        # Setup agent executor after base initialization
        self._setup_agent_executor()
        
        # Initialize coaching integration
        self._setup_coaching_integration()
    
    def _agent_specific_initialization(self):
        """Negotiator agent specific initialization"""
        logger.info("Initializing Negotiator Agent...")
        
        # Set up default message templates
        self._setup_default_templates()
        
        # Initialize communication tracking
        self._initialize_communication_tracking()
        
        # Set up response monitoring
        self._setup_response_monitoring()
        
        logger.info("Negotiator Agent initialization complete")
    
    def _setup_coaching_integration(self):
        """Set up negotiation coaching integration"""
        try:
            from app.core.database import get_db
            db = next(get_db())
            self.coaching_integration = NegotiationCoachingIntegration(db)
            logger.info("Negotiation coaching integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize coaching integration: {e}")
            self.coaching_integration = None
    
    def _setup_default_templates(self):
        """Set up default message templates"""
        # Initial contact email template
        initial_email = MessageTemplate(
            name="Initial Contact - Email",
            channel=CommunicationChannel.EMAIL,
            subject="Interested in Your Property at {property_address}",
            content="""
            Hello {owner_name},

            I hope this message finds you well. My name is {agent_name}, and I'm a real estate investor 
            who specializes in helping homeowners with quick, hassle-free property sales.

            I'm interested in your property at {property_address} and would like to discuss a potential 
            cash offer. I can close quickly without the need for financing contingencies, inspections, 
            or repairs.

            Key benefits of working with me:
            • Cash offer - no financing delays
            • Close in as little as 7-14 days
            • No repairs needed - I buy as-is
            • No real estate commissions
            • Flexible closing date to fit your timeline

            Would you be open to a brief conversation about your property? I'd be happy to provide 
            a no-obligation cash offer.

            Best regards,
            {agent_name}
            {contact_phone}
            {contact_email}
            """,
            variables=["owner_name", "property_address", "agent_name", "contact_phone", "contact_email"],
            tone="professional",
            purpose="initial_contact"
        )
        
        # Follow-up SMS template
        follow_up_sms = MessageTemplate(
            name="Follow-up - SMS",
            channel=CommunicationChannel.SMS,
            content="""
            Hi {owner_name}, this is {agent_name}. I sent you an email about your property at 
            {property_address}. I'm prepared to make a cash offer. Are you interested in discussing? 
            Text back or call {contact_phone}. Thanks!
            """,
            variables=["owner_name", "property_address", "agent_name", "contact_phone"],
            tone="friendly",
            purpose="follow_up"
        )
        
        # Negotiation response template
        negotiation_email = MessageTemplate(
            name="Negotiation Response - Email",
            channel=CommunicationChannel.EMAIL,
            subject="Re: Your Property at {property_address}",
            content="""
            Hello {owner_name},

            Thank you for your response regarding {property_address}. I appreciate you taking the time 
            to consider my offer.

            {personalized_response}

            Based on our conversation and my analysis of the property and local market conditions, 
            I'd like to present the following:

            {offer_details}

            This offer reflects:
            • Current market conditions in your area
            • The property's condition and any needed repairs
            • A fair cash price for a quick, guaranteed closing

            I'm flexible on the closing timeline and can work with your schedule. Would you like to 
            discuss this further?

            Best regards,
            {agent_name}
            {contact_phone}
            """,
            variables=["owner_name", "property_address", "personalized_response", "offer_details", "agent_name", "contact_phone"],
            tone="professional",
            purpose="negotiation"
        )
        
        # Store templates
        self.message_templates[initial_email.id] = initial_email
        self.message_templates[follow_up_sms.id] = follow_up_sms
        self.message_templates[negotiation_email.id] = negotiation_email
        
        logger.info(f"Initialized {len(self.message_templates)} default message templates")
    
    def _initialize_communication_tracking(self):
        """Initialize communication tracking systems"""
        # This would integrate with actual communication APIs
        # For now, we'll set up the data structures
        self.communication_history = {}
        logger.info("Communication tracking initialized")
    
    def _setup_response_monitoring(self):
        """Set up response monitoring and analysis"""
        # This would integrate with email/SMS APIs for response monitoring
        # For now, we'll set up the framework
        logger.info("Response monitoring setup complete")
    
    def _setup_agent_executor(self):
        """Set up the LangChain agent executor"""
        try:
            # Get available tools for negotiator agent
            available_tools = tool_registry.list_tools_for_agent(self.name, self.agent_type.value)
            
            # Convert to LangChain tools
            langchain_tools = []
            for tool_name in available_tools:
                agent_tool = tool_registry.get_tool(tool_name)
                if agent_tool:
                    lc_tool = LangChainToolAdapter.create_langchain_tool(
                        agent_tool, self.name, self.agent_type.value
                    )
                    langchain_tools.append(lc_tool)
            
            # Create system prompt
            system_prompt = self._create_system_prompt()
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ])
            
            # Create agent
            agent = create_openai_functions_agent(
                llm=self.llm,
                tools=langchain_tools,
                prompt=prompt
            )
            
            # Create agent executor
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=langchain_tools,
                verbose=True,
                max_iterations=10,
                max_execution_time=300,  # 5 minutes
                return_intermediate_steps=True
            )
            
            logger.info(f"Negotiator agent executor created with {len(langchain_tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to setup negotiator agent executor: {e}")
            self.agent_executor = None
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the negotiator agent"""
        return """
        You are an expert real estate negotiator agent specializing in seller outreach, communication, and deal negotiation.
        
        Your primary mission is to:
        1. Create and execute effective outreach campaigns to property owners
        2. Generate personalized, compelling messages across multiple channels
        3. Analyze seller responses for sentiment, interest, and negotiation insights
        4. Develop and implement strategic negotiation approaches
        5. Build rapport and trust with property owners
        6. Handle objections and overcome seller concerns
        7. Coordinate multi-channel communication sequences
        
        Key Responsibilities:
        - Outreach Campaign Management: Design multi-channel campaigns (email, SMS, phone, direct mail)
        - Message Personalization: Create compelling, personalized messages based on property and owner data
        - Response Analysis: Analyze seller communications for sentiment, interest level, and negotiation insights
        - Negotiation Strategy: Develop property-specific negotiation strategies based on market data and seller psychology
        - Objection Handling: Address seller concerns and objections with empathy and data-driven responses
        - Relationship Building: Establish trust and rapport with property owners
        - Communication Optimization: Track and optimize message effectiveness and response rates
        
        Communication Principles:
        - Always be professional, respectful, and empathetic
        - Focus on win-win outcomes and mutual benefit
        - Use data and market insights to support your position
        - Adapt your communication style to each seller's preferences
        - Be transparent about your process and intentions
        - Respond promptly to seller communications
        - Maintain detailed records of all interactions
        
        Negotiation Approach:
        - Start with collaborative, relationship-building approach
        - Use market data and comparable sales to justify offers
        - Address seller motivations and pain points
        - Be flexible on terms while maintaining profit margins
        - Create urgency when appropriate without being pushy
        - Always have backup strategies and alternatives
        - Know when to walk away from unprofitable deals
        
        Message Personalization Factors:
        - Property characteristics and condition
        - Owner demographics and situation
        - Local market conditions and trends
        - Seller motivation indicators
        - Previous communication history
        - Preferred communication channels
        - Response patterns and timing
        
        Success Metrics:
        - Response rates by channel and message type
        - Sentiment scores of seller responses
        - Conversion rates from initial contact to negotiation
        - Time to first response and deal closure
        - Seller satisfaction and referral rates
        - Profit margins maintained through negotiation
        
        Always maintain a professional, empathetic tone while being persuasive and results-oriented.
        Focus on building long-term relationships and reputation in the market.
        """
    
    # Core Agent Methods
    
    async def execute_task(self, task: str, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute a specific negotiator task"""
        logger.info(f"Negotiator agent executing task: {task}")
        
        try:
            if task == "create_outreach_campaign":
                return await self._create_outreach_campaign(data, state)
            elif task == "generate_message":
                return await self._generate_message(data, state)
            elif task == "analyze_response":
                return await self._analyze_response(data, state)
            elif task == "develop_negotiation_strategy":
                return await self._develop_negotiation_strategy(data, state)
            elif task == "manage_negotiation":
                return await self._manage_negotiation(data, state)
            elif task == "initiate_outreach":
                return await self._initiate_outreach(data, state)
            elif task == "handle_responses":
                return await self._handle_responses(data, state)
            elif task == "get_coaching":
                return await self._get_negotiation_coaching(data, state)
            elif task == "track_coaching_effectiveness":
                return await self._track_coaching_effectiveness(data, state)
            else:
                raise ValueError(f"Unknown task: {task}")
                
        except Exception as e:
            logger.error(f"Error executing negotiator task {task}: {e}")
            return {
                "success": False,
                "error": str(e),
                "task": task
            }
    
    async def process_state(self, state: AgentState) -> AgentState:
        """Process the current state and manage communications/negotiations"""
        logger.info("Negotiator agent processing state...")
        
        try:
            # Get approved deals that need outreach
            approved_deals = StateManager.get_deals_by_status(state, DealStatus.APPROVED)
            
            # Initiate outreach for new approved deals
            for deal_dict in approved_deals:
                if not deal_dict.get("outreach_initiated", False):
                    # Create outreach campaign
                    campaign_result = await self._create_outreach_campaign(
                        {"deal": deal_dict}, state
                    )
                    
                    if campaign_result.get("success", False):
                        # Mark outreach as initiated
                        deal_dict["outreach_initiated"] = True
                        deal_dict["campaign_data"] = campaign_result.get("campaign", {})
                        
                        # Update deal status
                        state = StateManager.update_deal_status(
                            state, 
                            deal_dict["id"], 
                            DealStatus.OUTREACH_INITIATED,
                            {"campaign_id": campaign_result["campaign"]["id"]}
                        )
                        
                        # Add to active negotiations
                        negotiation = Negotiation(
                            deal_id=deal_dict["id"],
                            status="initial_outreach",
                            campaign_data=campaign_result["campaign"]
                        )
                        
                        state["active_negotiations"].append(negotiation.dict())
                        
                        logger.info(f"Initiated outreach for deal {deal_dict['id']}")
            
            # Handle responses for active negotiations
            active_negotiations = state.get("active_negotiations", [])
            for negotiation_dict in active_negotiations:
                if negotiation_dict.get("status") in ["initial_outreach", "in_negotiation"]:
                    # Integrate coaching if available
                    if self.coaching_integration:
                        state = await self.coaching_integration.integrate_with_negotiator_workflow(
                            state, negotiation_dict
                        )
                    
                    # Check for responses and handle them
                    response_result = await self._handle_responses(
                        {"negotiation": negotiation_dict}, state
                    )
                    
                    if response_result.get("success", False):
                        # Update negotiation status
                        negotiation_dict.update(response_result.get("updated_negotiation", {}))
            
            # Add agent message about activity
            outreach_count = len([d for d in approved_deals if not d.get("outreach_initiated", False)])
            active_count = len([n for n in active_negotiations if n.get("status") in ["initial_outreach", "in_negotiation"]])
            
            if outreach_count > 0 or active_count > 0:
                state = StateManager.add_agent_message(
                    state,
                    AgentType.NEGOTIATOR,
                    f"Managing {outreach_count} new outreach campaigns and {active_count} active negotiations",
                    data={
                        "new_outreach": outreach_count,
                        "active_negotiations": active_count,
                        "messages_sent_today": self.messages_sent_today,
                        "responses_received_today": self.responses_received_today
                    },
                    priority=2
                )
            
            # Set next action if there are active negotiations
            if active_negotiations:
                state = StateManager.set_next_action(
                    state,
                    "contract",
                    f"Have {len(active_negotiations)} active negotiations that may need contracts"
                )
            
            return state
            
        except Exception as e:
            logger.error(f"Error in negotiator agent state processing: {e}")
            state = StateManager.add_agent_message(
                state,
                AgentType.NEGOTIATOR,
                f"Error in negotiator agent: {str(e)}",
                priority=4
            )
            return state
    
    def get_available_tasks(self) -> List[str]:
        """Get list of tasks this agent can perform"""
        return [
            "create_outreach_campaign",
            "generate_message",
            "analyze_response",
            "develop_negotiation_strategy",
            "manage_negotiation",
            "initiate_outreach",
            "handle_responses",
            "get_coaching",
            "track_coaching_effectiveness"
        ]
    
    # Private Implementation Methods
    
    async def _create_outreach_campaign(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Create a comprehensive outreach campaign for a deal"""
        logger.info("Creating outreach campaign...")
        
        if not self.agent_executor:
            return {
                "success": False,
                "error": "Agent executor not initialized"
            }
        
        try:
            deal = data.get("deal", {})
            campaign_config = data.get("campaign_config", {})
            
            # Get market context
            market_conditions = state.get("market_conditions", {})
            
            # Create campaign prompt
            campaign_prompt = f"""
            Create a comprehensive outreach campaign for this property deal:
            
            Deal Information:
            {json.dumps(deal, indent=2)}
            
            Market Context:
            {json.dumps(market_conditions, indent=2)}
            
            Campaign Requirements:
            - Multi-channel approach (email, SMS, phone)
            - Personalized messaging based on property and owner data
            - Strategic timing and follow-up sequence
            - Professional yet compelling tone
            - Focus on seller benefits and motivation
            
            Tasks:
            1. Analyze the property and owner information
            2. Identify seller motivation indicators
            3. Create personalized initial contact messages for each channel
            4. Design follow-up sequence with optimal timing
            5. Develop objection handling responses
            6. Set campaign success metrics and tracking
            
            For each message, provide:
            - Channel (email, SMS, phone script)
            - Subject line (if applicable)
            - Personalized content
            - Key selling points
            - Call to action
            - Timing recommendations
            
            Focus on building rapport, demonstrating value, and creating urgency while maintaining professionalism.
            """
            
            # Execute campaign creation
            result = await self.agent_executor.ainvoke({
                "input": campaign_prompt,
                "chat_history": []
            })
            
            # Parse the result and create campaign object
            campaign_data = self._parse_campaign_creation_result(result.get("output", ""), deal)
            
            # Create campaign object
            campaign = OutreachCampaign(
                deal_id=deal.get("id", ""),
                name=f"Outreach Campaign - {deal.get('property_address', 'Unknown')}",
                description=f"Multi-channel outreach for property at {deal.get('property_address', 'Unknown')}",
                channels=[CommunicationChannel.EMAIL, CommunicationChannel.SMS, CommunicationChannel.PHONE],
                sequence=campaign_data.get("sequence", []),
                status="active",
                started_at=datetime.now()
            )
            
            # Store campaign
            self.active_campaigns[campaign.id] = campaign
            self.campaigns_created += 1
            
            return {
                "success": True,
                "campaign": campaign.dict(),
                "initial_messages": campaign_data.get("initial_messages", []),
                "campaign_id": campaign.id
            }
            
        except Exception as e:
            logger.error(f"Error creating outreach campaign: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _generate_message(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Generate a personalized message for a specific purpose"""
        deal = data.get("deal", {})
        channel = data.get("channel", CommunicationChannel.EMAIL)
        purpose = data.get("purpose", "initial_contact")
        context = data.get("context", {})
        
        # Find appropriate template
        template = self._find_template(channel, purpose)
        if not template:
            return {
                "success": False,
                "error": f"No template found for channel {channel} and purpose {purpose}"
            }
        
        # Generate personalized message
        message = self._personalize_message(template, deal, context)
        
        return {
            "success": True,
            "message": message,
            "template_used": template.id,
            "personalization_score": 0.8  # Would calculate based on actual personalization
        }
    
    async def _analyze_response(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Analyze a seller response for sentiment and negotiation insights"""
        communication = data.get("communication", {})
        
        if not self.agent_executor:
            return {
                "success": False,
                "error": "Agent executor not initialized"
            }
        
        try:
            # Create analysis prompt
            analysis_prompt = f"""
            Analyze this seller response for negotiation insights:
            
            Communication Details:
            - Channel: {communication.get('channel', 'unknown')}
            - Content: {communication.get('content', '')}
            - Context: Previous outreach about property investment opportunity
            
            Analysis Required:
            1. Sentiment Analysis:
               - Overall sentiment (-1.0 to 1.0)
               - Emotional tone (positive, negative, neutral, mixed)
               - Confidence level in analysis
            
            2. Interest Level Assessment:
               - Interest level (0.0 to 1.0)
               - Urgency indicators
               - Motivation signals
            
            3. Content Analysis:
               - Key points mentioned
               - Objections raised
               - Questions asked
               - Concerns expressed
            
            4. Negotiation Insights:
               - Price sensitivity indicators
               - Timeline flexibility signals
               - Terms preferences
            
            5. Recommended Actions:
               - Suggested response tone
               - Next steps
               - Follow-up timing
               - Escalation needs
            
            Provide specific, actionable insights for continuing the negotiation.
            """
            
            # Execute analysis
            result = await self.agent_executor.ainvoke({
                "input": analysis_prompt,
                "chat_history": []
            })
            
            # Parse analysis result
            analysis = self._parse_response_analysis(result.get("output", ""))
            
            return {
                "success": True,
                "analysis": analysis,
                "recommended_actions": analysis.get("recommended_next_steps", [])
            }
            
        except Exception as e:
            logger.error(f"Error analyzing response: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _develop_negotiation_strategy(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Develop a negotiation strategy for a specific deal"""
        deal = data.get("deal", {})
        seller_profile = data.get("seller_profile", {})
        market_context = data.get("market_context", {})
        
        if not self.agent_executor:
            return {
                "success": False,
                "error": "Agent executor not initialized"
            }
        
        try:
            # Create strategy development prompt
            strategy_prompt = f"""
            Develop a comprehensive negotiation strategy for this real estate deal:
            
            Deal Information:
            {json.dumps(deal, indent=2)}
            
            Seller Profile:
            {json.dumps(seller_profile, indent=2)}
            
            Market Context:
            {json.dumps(market_context, indent=2)}
            
            Strategy Development Requirements:
            1. Analyze seller motivation and circumstances
            2. Determine optimal negotiation approach (collaborative, competitive, accommodating)
            3. Calculate initial offer percentage and price ranges
            4. Identify primary and fallback negotiation tactics
            5. Develop concession strategy
            6. Set timeline and deadlines
            7. Prepare for common objections
            
            Consider:
            - Property condition and repair needs
            - Local market conditions and comparable sales
            - Seller's timeline and flexibility
            - Financing and closing requirements
            - Profit margins and investment criteria
            
            Provide a detailed strategy with specific tactics, pricing recommendations, and contingency plans.
            """
            
            # Execute strategy development
            result = await self.agent_executor.ainvoke({
                "input": strategy_prompt,
                "chat_history": []
            })
            
            # Parse strategy result
            strategy_data = self._parse_negotiation_strategy(result.get("output", ""), deal)
            
            # Create strategy object
            strategy = NegotiationStrategy(
                deal_id=deal.get("id", ""),
                approach=strategy_data.get("approach", "collaborative"),
                initial_offer_percentage=strategy_data.get("initial_offer_percentage", 0.85),
                primary_tactics=strategy_data.get("primary_tactics", []),
                fallback_tactics=strategy_data.get("fallback_tactics", []),
                seller_motivation_factors=strategy_data.get("motivation_factors", [])
            )
            
            # Store strategy
            self.negotiation_strategies[strategy.id] = strategy
            
            return {
                "success": True,
                "strategy": strategy.dict(),
                "tactics": strategy.primary_tactics,
                "strategy_id": strategy.id
            }
            
        except Exception as e:
            logger.error(f"Error developing negotiation strategy: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _manage_negotiation(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Manage an active negotiation"""
        negotiation = data.get("negotiation", {})
        latest_communication = data.get("latest_communication", {})
        
        # Update negotiation based on latest communication
        updated_negotiation = negotiation.copy()
        
        # Analyze the communication if provided
        if latest_communication:
            analysis_result = await self._analyze_response(
                {"communication": latest_communication}, state
            )
            
            if analysis_result.get("success", False):
                analysis = analysis_result["analysis"]
                
                # Update negotiation metrics
                updated_negotiation["sentiment_score"] = analysis.get("overall_sentiment", 0.0)
                updated_negotiation["interest_level"] = analysis.get("interest_level", 0.0)
                updated_negotiation["last_contact"] = datetime.now().isoformat()
                updated_negotiation["responses_received"] += 1
                
                # Determine next actions based on analysis
                next_actions = self._determine_next_actions(analysis, negotiation)
                
                return {
                    "success": True,
                    "updated_negotiation": updated_negotiation,
                    "next_actions": next_actions,
                    "analysis": analysis
                }
        
        return {
            "success": True,
            "updated_negotiation": updated_negotiation,
            "next_actions": []
        }
    
    async def _initiate_outreach(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Initiate outreach for approved deals"""
        approved_deals = StateManager.get_deals_by_status(state, DealStatus.APPROVED)
        initiated_count = 0
        
        for deal_dict in approved_deals:
            if not deal_dict.get("outreach_initiated", False):
                # Create and execute outreach campaign
                campaign_result = await self._create_outreach_campaign(
                    {"deal": deal_dict}, state
                )
                
                if campaign_result.get("success", False):
                    # Execute initial messages
                    await self._execute_initial_messages(
                        campaign_result["campaign"], 
                        campaign_result["initial_messages"]
                    )
                    
                    initiated_count += 1
        
        return {
            "success": True,
            "campaigns_initiated": initiated_count,
            "message": f"Initiated outreach for {initiated_count} deals"
        }
    
    async def _handle_responses(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Handle responses from sellers"""
        # This would integrate with actual communication APIs
        # For now, simulate response handling
        
        negotiation = data.get("negotiation", {})
        
        # Simulate checking for responses
        has_response = False  # Would check actual communication channels
        
        if has_response:
            # Process the response
            # This would involve actual response analysis and follow-up generation
            pass
        
        return {
            "success": True,
            "responses_processed": 0,
            "updated_negotiation": negotiation
        }
    
    # Helper Methods
    
    def _find_template(self, channel: CommunicationChannel, purpose: str) -> Optional[MessageTemplate]:
        """Find appropriate message template"""
        for template in self.message_templates.values():
            if template.channel == channel and template.purpose == purpose:
                return template
        return None
    
    def _personalize_message(self, template: MessageTemplate, deal: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize a message template with deal and context data"""
        content = template.content
        subject = template.subject
        
        # Replace variables with actual data
        replacements = {
            "owner_name": deal.get("owner_info", {}).get("owner_name", "Property Owner"),
            "property_address": deal.get("property_address", "your property"),
            "agent_name": "Real Estate Investment Team",
            "contact_phone": "(555) 123-4567",
            "contact_email": "invest@example.com"
        }
        
        # Apply replacements
        for var, value in replacements.items():
            content = content.replace(f"{{{var}}}", str(value))
            if subject:
                subject = subject.replace(f"{{{var}}}", str(value))
        
        return {
            "channel": template.channel.value,
            "subject": subject,
            "content": content,
            "template_id": template.id,
            "personalized": True
        }
    
    def _parse_campaign_creation_result(self, result: str, deal: Dict[str, Any]) -> Dict[str, Any]:
        """Parse campaign creation result from agent"""
        # This would parse the actual agent output
        # For now, return a structured campaign
        return {
            "sequence": [
                {
                    "step": 1,
                    "channel": "email",
                    "timing": 0,
                    "message_type": "initial_contact"
                },
                {
                    "step": 2,
                    "channel": "sms",
                    "timing": 24,
                    "message_type": "follow_up"
                }
            ],
            "initial_messages": [
                {
                    "channel": "email",
                    "subject": f"Interested in Your Property at {deal.get('property_address', 'Unknown')}",
                    "content": "Initial email content..."
                }
            ]
        }
    
    def _parse_response_analysis(self, result: str) -> Dict[str, Any]:
        """Parse response analysis result from agent"""
        # This would parse the actual agent analysis
        # For now, return a structured analysis
        return {
            "overall_sentiment": 0.3,
            "emotional_tone": "neutral",
            "confidence_level": 0.8,
            "interest_level": 0.6,
            "urgency_indicators": ["timeline_mentioned"],
            "key_points": ["interested_in_cash_offer"],
            "objections_raised": ["price_too_low"],
            "recommended_next_steps": ["provide_market_analysis", "schedule_call"],
            "follow_up_timing": 24
        }
    
    def _parse_negotiation_strategy(self, result: str, deal: Dict[str, Any]) -> Dict[str, Any]:
        """Parse negotiation strategy result from agent"""
        # This would parse the actual agent strategy
        # For now, return a structured strategy
        return {
            "approach": "collaborative",
            "initial_offer_percentage": 0.85,
            "primary_tactics": ["market_data_support", "timeline_flexibility", "cash_advantage"],
            "fallback_tactics": ["price_increase", "terms_adjustment"],
            "motivation_factors": ["quick_sale_needed", "avoid_repairs"]
        }
    
    def _determine_next_actions(self, analysis: Dict[str, Any], negotiation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine next actions based on response analysis"""
        actions = []
        
        interest_level = analysis.get("interest_level", 0.0)
        sentiment = analysis.get("overall_sentiment", 0.0)
        
        if interest_level > 0.7:
            actions.append({
                "action": "schedule_call",
                "priority": "high",
                "timing": "immediate"
            })
        elif interest_level > 0.4:
            actions.append({
                "action": "send_follow_up",
                "priority": "medium",
                "timing": "24_hours"
            })
        
        if sentiment < -0.3:
            actions.append({
                "action": "address_concerns",
                "priority": "high",
                "timing": "immediate"
            })
        
        return actions
    
    async def _execute_initial_messages(self, campaign: Dict[str, Any], messages: List[Dict[str, Any]]):
        """Execute initial messages for a campaign"""
        for message in messages:
            # This would integrate with actual communication APIs
            # For now, simulate sending
            self.messages_sent_today += 1
            logger.info(f"Sent {message['channel']} message for campaign {campaign['id']}")    

    # Coaching Integration Methods
    
    async def _get_negotiation_coaching(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Get real-time negotiation coaching"""
        try:
            if not self.coaching_integration:
                return {
                    "success": False,
                    "error": "Coaching integration not available"
                }
            
            property_id = data.get("property_id")
            if not property_id:
                return {
                    "success": False,
                    "error": "Property ID is required"
                }
            
            # Get coaching
            coaching_result = await self.coaching_integration.provide_real_time_coaching(
                property_id=uuid.UUID(property_id),
                situation=data.get("situation", "Active negotiation"),
                seller_response=data.get("seller_response"),
                specific_concerns=data.get("specific_concerns", []),
                negotiation_phase=data.get("negotiation_phase", "initial")
            )
            
            if coaching_result.get("success"):
                logger.info(f"Provided coaching for property {property_id}")
                
                # Track coaching usage
                self._track_coaching_usage(coaching_result)
            
            return coaching_result
            
        except Exception as e:
            logger.error(f"Error getting negotiation coaching: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _track_coaching_effectiveness(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Track the effectiveness of coaching sessions"""
        try:
            if not self.coaching_integration:
                return {
                    "success": False,
                    "error": "Coaching integration not available"
                }
            
            session_id = data.get("session_id")
            outcome = data.get("outcome")
            user_feedback = data.get("user_feedback")
            
            if not session_id or not outcome:
                return {
                    "success": False,
                    "error": "Session ID and outcome are required"
                }
            
            # Track effectiveness
            result = await self.coaching_integration.track_coaching_effectiveness(
                session_id=session_id,
                outcome=outcome,
                user_feedback=user_feedback
            )
            
            if result.get("success"):
                logger.info(f"Tracked coaching effectiveness for session {session_id}: {result.get('effectiveness_score')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error tracking coaching effectiveness: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _track_coaching_usage(self, coaching_result: Dict[str, Any]):
        """Track coaching usage for performance metrics"""
        try:
            if coaching_result.get("success"):
                # Update performance metrics
                session_id = coaching_result.get("session_id")
                if session_id:
                    # Track that coaching was provided
                    logger.info(f"Coaching session {session_id} provided successfully")
                    
                    # Could add more detailed tracking here
                    # e.g., track which types of coaching are most requested
                    
        except Exception as e:
            logger.error(f"Error tracking coaching usage: {e}")
    
    def get_coaching_analytics(self, property_id: Optional[str] = None) -> Dict[str, Any]:
        """Get coaching analytics"""
        try:
            if not self.coaching_integration:
                return {
                    "error": "Coaching integration not available"
                }
            
            return self.coaching_integration.get_coaching_analytics(property_id)
            
        except Exception as e:
            logger.error(f"Error getting coaching analytics: {e}")
            return {
                "error": str(e)
            }
    
    async def generate_coaching_report(self, property_id: str) -> Dict[str, Any]:
        """Generate a comprehensive coaching report"""
        try:
            if not self.coaching_integration:
                return {
                    "error": "Coaching integration not available"
                }
            
            return await self.coaching_integration.generate_coaching_report(property_id)
            
        except Exception as e:
            logger.error(f"Error generating coaching report: {e}")
            return {
                "error": str(e)
            }