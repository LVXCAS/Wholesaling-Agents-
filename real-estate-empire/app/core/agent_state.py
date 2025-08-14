"""
Shared Agent State Management for LangGraph Workflows
"""

import uuid
from datetime import datetime
from typing import TypedDict, List, Optional, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    HUMAN_ESCALATION = "human_escalation"


class AgentType(str, Enum):
    """Types of agents in the system"""
    SUPERVISOR = "supervisor"
    SCOUT = "scout"
    ANALYST = "analyst"
    NEGOTIATOR = "negotiator"
    CONTRACT = "contract"
    PORTFOLIO = "portfolio"
    MARKET = "market"
    FUNDING = "funding"
    COMPUTER_VISION = "computer_vision"
    DATA_INGESTION = "data_ingestion"


class DealStatus(str, Enum):
    """Status of deals in the pipeline"""
    DISCOVERED = "discovered"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    APPROVED = "approved"
    OUTREACH_INITIATED = "outreach_initiated"
    IN_NEGOTIATION = "in_negotiation"
    UNDER_CONTRACT = "under_contract"
    CLOSING = "closing"
    CLOSED = "closed"
    REJECTED = "rejected"
    DEAD = "dead"


class GeographicLevel(str, Enum):
    """Geographic hierarchy levels"""
    NATIONAL = "national"
    REGIONAL = "regional"
    STATE = "state"
    CITY = "city"
    ZIPCODE = "zipcode"


class AgentMessage(BaseModel):
    """Message from an agent"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent: AgentType
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Optional[Dict[str, Any]] = None
    priority: int = Field(default=1, ge=1, le=5)  # 1=low, 5=critical


class Deal(BaseModel):
    """Represents a real estate deal in the pipeline"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    property_address: str
    city: str
    state: str
    zip_code: str
    status: DealStatus = DealStatus.DISCOVERED
    
    # Property Details
    property_type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    
    # Financial Data
    listing_price: Optional[float] = None
    estimated_value: Optional[float] = None
    arv_estimate: Optional[float] = None
    repair_estimate: Optional[float] = None
    potential_profit: Optional[float] = None
    
    # Analysis Results
    analyzed: bool = False
    analysis_data: Optional[Dict[str, Any]] = None
    analyst_recommendation: Optional[str] = None
    confidence_score: Optional[float] = None
    
    # Outreach & Negotiation
    outreach_initiated: bool = False
    campaign_data: Optional[Dict[str, Any]] = None
    negotiation_status: Optional[str] = None
    
    # Owner Information
    owner_info: Optional[Dict[str, Any]] = None
    contact_info: Optional[Dict[str, Any]] = None
    motivation_indicators: List[str] = Field(default_factory=list)
    
    # Metadata
    source: Optional[str] = None
    discovered_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    assigned_to: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class Negotiation(BaseModel):
    """Active negotiation tracking"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deal_id: str
    status: str
    started_at: datetime = Field(default_factory=datetime.now)
    last_contact: Optional[datetime] = None
    next_follow_up: Optional[datetime] = None
    
    # Communication History
    messages_sent: int = 0
    responses_received: int = 0
    sentiment_score: Optional[float] = None
    interest_level: Optional[float] = None
    
    # Negotiation Data
    initial_offer: Optional[float] = None
    current_offer: Optional[float] = None
    seller_asking: Optional[float] = None
    objections: List[str] = Field(default_factory=list)
    
    # Campaign Data
    campaign_data: Optional[Dict[str, Any]] = None


class PortfolioMetrics(BaseModel):
    """Portfolio performance metrics"""
    total_properties: int = 0
    total_value: float = 0.0
    total_equity: float = 0.0
    monthly_cash_flow: float = 0.0
    average_cap_rate: float = 0.0
    average_coc_return: float = 0.0
    average_roi: float = 0.0
    
    # Performance Tracking
    ytd_profit: float = 0.0
    ytd_deals_closed: int = 0
    pipeline_value: float = 0.0
    
    # Risk Metrics
    diversification_score: float = 0.0
    risk_score: float = 0.0
    
    last_updated: datetime = Field(default_factory=datetime.now)


class MarketConditions(BaseModel):
    """Current market conditions and trends"""
    geographic_level: GeographicLevel
    location: str
    
    # Market Metrics
    median_home_price: Optional[float] = None
    price_change_yoy: Optional[float] = None
    days_on_market: Optional[int] = None
    inventory_months: Optional[float] = None
    
    # Economic Indicators
    interest_rates: Optional[float] = None
    unemployment_rate: Optional[float] = None
    population_growth: Optional[float] = None
    
    # Investment Metrics
    cap_rate_average: Optional[float] = None
    rent_growth_yoy: Optional[float] = None
    foreclosure_rate: Optional[float] = None
    
    # Market Sentiment
    market_temperature: Optional[str] = None  # "hot", "warm", "cool", "cold"
    investor_activity: Optional[str] = None   # "high", "medium", "low"
    
    last_updated: datetime = Field(default_factory=datetime.now)


class AgentPerformance(BaseModel):
    """Agent performance tracking"""
    agent_type: AgentType
    
    # Execution Metrics
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_response_time: float = 0.0
    uptime_percentage: float = 100.0
    
    # Quality Metrics
    accuracy_rate: float = 0.0
    confidence_score: float = 0.0
    success_rate: float = 0.0
    
    # Cost Metrics
    llm_tokens_used: int = 0
    estimated_cost: float = 0.0
    cost_per_task: float = 0.0
    
    # Learning Metrics
    improvement_rate: float = 0.0
    feedback_score: float = 0.0
    
    last_updated: datetime = Field(default_factory=datetime.now)


class AgentState(TypedDict):
    """
    Shared state between all agents in the LangGraph workflow
    This is the central state that gets passed between agents
    """
    
    # Workflow Management
    workflow_id: str
    workflow_status: WorkflowStatus
    current_step: str
    next_action: Optional[str]
    
    # Deal Pipeline
    current_deals: List[Dict[str, Any]]  # Serialized Deal objects
    analyzed_deals: List[Dict[str, Any]]
    active_negotiations: List[Dict[str, Any]]  # Serialized Negotiation objects
    pending_contracts: List[Dict[str, Any]]
    closed_deals: List[Dict[str, Any]]
    
    # Portfolio Management
    portfolio_status: Dict[str, Any]  # Serialized PortfolioMetrics
    portfolio_performance: Dict[str, Any]
    investment_strategy: Dict[str, Any]
    
    # Market Intelligence
    market_conditions: Dict[str, Any]  # Serialized MarketConditions
    regional_trends: Dict[str, Any]
    local_market_data: Dict[str, Any]
    
    # Funding & Capital
    funding_status: Dict[str, Any]
    investor_profiles: List[Dict[str, Any]]
    available_capital: float
    capital_requirements: float
    
    # Agent Communication
    agent_messages: List[Dict[str, Any]]  # Serialized AgentMessage objects
    agent_performance: Dict[str, Any]  # AgentType -> AgentPerformance
    escalation_flags: List[Dict[str, Any]]
    
    # Geographic Context
    current_geographic_focus: str
    geographic_level: GeographicLevel
    target_markets: List[str]
    
    # System State
    active_agents: List[AgentType]
    human_input: Optional[str]
    human_approval_required: bool
    system_alerts: List[Dict[str, Any]]
    
    # Configuration
    investment_criteria: Dict[str, Any]
    risk_tolerance: Dict[str, Any]
    automation_level: str  # "full", "supervised", "manual"
    
    # Timestamps
    workflow_started: str  # ISO format datetime
    last_updated: str      # ISO format datetime


class StateManager:
    """Manages agent state serialization and validation"""
    
    @staticmethod
    def create_initial_state(workflow_id: Optional[str] = None) -> AgentState:
        """Create initial agent state"""
        now = datetime.now().isoformat()
        
        return AgentState(
            # Workflow Management
            workflow_id=workflow_id or str(uuid.uuid4()),
            workflow_status=WorkflowStatus.INITIALIZING,
            current_step="supervisor",
            next_action=None,
            
            # Deal Pipeline
            current_deals=[],
            analyzed_deals=[],
            active_negotiations=[],
            pending_contracts=[],
            closed_deals=[],
            
            # Portfolio Management
            portfolio_status={},
            portfolio_performance={},
            investment_strategy={},
            
            # Market Intelligence
            market_conditions={},
            regional_trends={},
            local_market_data={},
            
            # Funding & Capital
            funding_status={},
            investor_profiles=[],
            available_capital=0.0,
            capital_requirements=0.0,
            
            # Agent Communication
            agent_messages=[],
            agent_performance={},
            escalation_flags=[],
            
            # Geographic Context
            current_geographic_focus="national",
            geographic_level=GeographicLevel.NATIONAL,
            target_markets=[],
            
            # System State
            active_agents=[],
            human_input=None,
            human_approval_required=False,
            system_alerts=[],
            
            # Configuration
            investment_criteria={},
            risk_tolerance={},
            automation_level="supervised",
            
            # Timestamps
            workflow_started=now,
            last_updated=now
        )
    
    @staticmethod
    def add_agent_message(state: AgentState, agent: AgentType, message: str, 
                         data: Optional[Dict[str, Any]] = None, priority: int = 1) -> AgentState:
        """Add a message from an agent to the state"""
        agent_message = AgentMessage(
            agent=agent,
            message=message,
            data=data,
            priority=priority
        )
        
        state["agent_messages"].append(agent_message.dict())
        state["last_updated"] = datetime.now().isoformat()
        
        return state
    
    @staticmethod
    def update_deal_status(state: AgentState, deal_id: str, status: DealStatus, 
                          data: Optional[Dict[str, Any]] = None) -> AgentState:
        """Update the status of a specific deal"""
        # Find and update deal in current_deals
        for deal_dict in state["current_deals"]:
            if deal_dict.get("id") == deal_id:
                deal_dict["status"] = status.value
                deal_dict["last_updated"] = datetime.now().isoformat()
                if data:
                    deal_dict.update(data)
                break
        
        state["last_updated"] = datetime.now().isoformat()
        return state
    
    @staticmethod
    def add_deal(state: AgentState, deal: Deal) -> AgentState:
        """Add a new deal to the state"""
        state["current_deals"].append(deal.dict())
        state["last_updated"] = datetime.now().isoformat()
        return state
    
    @staticmethod
    def get_deals_by_status(state: AgentState, status: DealStatus) -> List[Dict[str, Any]]:
        """Get all deals with a specific status"""
        return [deal for deal in state["current_deals"] if deal.get("status") == status.value]
    
    @staticmethod
    def set_next_action(state: AgentState, action: str, reason: Optional[str] = None) -> AgentState:
        """Set the next action for the workflow"""
        state["next_action"] = action
        state["current_step"] = action
        state["last_updated"] = datetime.now().isoformat()
        
        if reason:
            StateManager.add_agent_message(
                state, 
                AgentType.SUPERVISOR, 
                f"Next action: {action}. Reason: {reason}"
            )
        
        return state