"""
End-to-End Workflow Orchestration System
Implements complete deal lifecycle automation with cross-agent communication optimization
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from dataclasses import dataclass, field

from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .agent_state import AgentState, AgentType, Deal, DealStatus, StateManager, WorkflowStatus
from .supervisor_agent import SupervisorAgent
from .agent_communication import AgentCommunicationProtocol, MessageType, MessagePriority
from .shared_memory import SharedMemoryManager
from .llm_config import llm_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkflowPhase(str, Enum):
    """Phases of the complete deal lifecycle"""
    INITIALIZATION = "initialization"
    DEAL_DISCOVERY = "deal_discovery"
    PROPERTY_ANALYSIS = "property_analysis"
    OUTREACH_COMMUNICATION = "outreach_communication"
    NEGOTIATION = "negotiation"
    CONTRACT_GENERATION = "contract_generation"
    DUE_DILIGENCE = "due_diligence"
    CLOSING_COORDINATION = "closing_coordination"
    PORTFOLIO_INTEGRATION = "portfolio_integration"
    PERFORMANCE_MONITORING = "performance_monitoring"
    COMPLETION = "completion"


class WorkflowTrigger(str, Enum):
    """Triggers that can initiate workflow actions"""
    MANUAL_START = "manual_start"
    SCHEDULED_RUN = "scheduled_run"
    DEAL_THRESHOLD = "deal_threshold"
    MARKET_OPPORTUNITY = "market_opportunity"
    PORTFOLIO_REBALANCE = "portfolio_rebalance"
    EMERGENCY_RESPONSE = "emergency_response"


@dataclass
class WorkflowMetrics:
    """Metrics for workflow performance tracking"""
    workflow_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    current_phase: WorkflowPhase = WorkflowPhase.INITIALIZATION
    
    # Performance metrics
    total_deals_processed: int = 0
    deals_approved: int = 0
    deals_under_contract: int = 0
    deals_closed: int = 0
    
    # Agent performance
    agent_execution_times: Dict[str, List[float]] = field(default_factory=dict)
    agent_success_rates: Dict[str, float] = field(default_factory=dict)
    cross_agent_handoffs: int = 0
    
    # Communication metrics
    messages_sent: int = 0
    responses_received: int = 0
    escalations_to_human: int = 0
    
    # Financial metrics
    total_investment_analyzed: float = 0.0
    potential_profit_identified: float = 0.0
    actual_profit_realized: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "current_phase": self.current_phase.value,
            "total_deals_processed": self.total_deals_processed,
            "deals_approved": self.deals_approved,
            "deals_under_contract": self.deals_under_contract,
            "deals_closed": self.deals_closed,
            "agent_execution_times": self.agent_execution_times,
            "agent_success_rates": self.agent_success_rates,
            "cross_agent_handoffs": self.cross_agent_handoffs,
            "messages_sent": self.messages_sent,
            "responses_received": self.responses_received,
            "escalations_to_human": self.escalations_to_human,
            "total_investment_analyzed": self.total_investment_analyzed,
            "potential_profit_identified": self.potential_profit_identified,
            "actual_profit_realized": self.actual_profit_realized
        }


class WorkflowConfiguration(BaseModel):
    """Configuration for workflow execution"""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Real Estate Deal Lifecycle"
    description: str = "Complete automation of real estate investment process"
    
    # Execution parameters
    max_concurrent_deals: int = 10
    max_execution_time_minutes: int = 480  # 8 hours
    auto_approve_threshold: float = 0.85
    human_escalation_threshold: float = 0.7
    
    # Agent coordination settings
    enable_parallel_processing: bool = True
    agent_timeout_seconds: int = 300  # 5 minutes
    max_retries_per_agent: int = 3
    
    # Communication optimization
    batch_communications: bool = True
    communication_delay_seconds: int = 30
    max_outreach_per_hour: int = 50
    
    # Performance monitoring
    enable_real_time_monitoring: bool = True
    metrics_collection_interval: int = 60  # seconds
    performance_alert_threshold: float = 0.5
    
    # Integration settings
    enable_external_integrations: bool = True
    mls_integration_enabled: bool = True
    crm_integration_enabled: bool = True
    accounting_integration_enabled: bool = True


class WorkflowOrchestrator:
    """
    End-to-End Workflow Orchestration System
    
    Manages the complete real estate deal lifecycle with:
    - Cross-agent communication optimization
    - Performance monitoring and alerting
    - Automated decision making and routing
    - Human escalation handling
    - Real-time metrics collection
    """
    
    def __init__(self, config: Optional[WorkflowConfiguration] = None):
        self.config = config or WorkflowConfiguration()
        self.workflow_id = self.config.workflow_id
        
        # Core components
        self.supervisor = SupervisorAgent()
        self.communication_protocol = AgentCommunicationProtocol()
        self.shared_memory = SharedMemoryManager()
        
        # Workflow state management
        self.workflow_graph: Optional[StateGraph] = None
        self.compiled_workflow = None
        self.memory_saver = MemorySaver()
        
        # Performance tracking
        self.metrics = WorkflowMetrics(
            workflow_id=self.workflow_id,
            start_time=datetime.now()
        )
        
        # Agent registry and coordination
        self.agent_registry: Dict[str, Any] = {}
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_history: List[Dict[str, Any]] = []
        
        # Communication optimization
        self.message_queue: List[Dict[str, Any]] = []
        self.batch_processor_task: Optional[asyncio.Task] = None
        
        # Performance monitoring
        self.monitoring_task: Optional[asyncio.Task] = None
        self.performance_alerts: List[Dict[str, Any]] = []
        
        # Initialize workflow
        self._initialize_workflow()
        
        logger.info(f"Workflow Orchestrator initialized: {self.workflow_id}")
    
    def _initialize_workflow(self):
        """Initialize the complete workflow graph"""
        logger.info("Initializing end-to-end workflow orchestration...")
        
        # Create workflow graph
        self.workflow_graph = StateGraph(AgentState)
        
        # Add all workflow phases as nodes
        self._add_workflow_nodes()
        
        # Define workflow routing and transitions
        self._define_workflow_transitions()
        
        # Set entry point
        self.workflow_graph.set_entry_point("initialization")
        
        # Compile workflow with checkpointing
        self.compiled_workflow = self.workflow_graph.compile(
            checkpointer=self.memory_saver,
            interrupt_before=["human_escalation", "contract_generation"],
            interrupt_after=["closing_coordination"]
        )
        
        logger.info("Workflow orchestration initialization complete")
    
    def _add_workflow_nodes(self):
        """Add all workflow phase nodes"""
        workflow_nodes = [
            ("initialization", self._initialization_phase),
            ("deal_discovery", self._deal_discovery_phase),
            ("property_analysis", self._property_analysis_phase),
            ("outreach_communication", self._outreach_communication_phase),
            ("negotiation", self._negotiation_phase),
            ("contract_generation", self._contract_generation_phase),
            ("due_diligence", self._due_diligence_phase),
            ("closing_coordination", self._closing_coordination_phase),
            ("portfolio_integration", self._portfolio_integration_phase),
            ("performance_monitoring", self._performance_monitoring_phase),
            ("human_escalation", self._human_escalation_phase),
            ("completion", self._completion_phase)
        ]
        
        for node_name, node_func in workflow_nodes:
            self.workflow_graph.add_node(node_name, node_func)
            logger.debug(f"Added workflow node: {node_name}")
    
    def _define_workflow_transitions(self):
        """Define workflow phase transitions and routing logic"""
        
        # Initialization phase routing
        self.workflow_graph.add_conditional_edges(
            "initialization",
            self._route_from_initialization,
            {
                "deal_discovery": "deal_discovery",
                "performance_monitoring": "performance_monitoring",
                "completion": "completion"
            }
        )
        
        # Deal discovery phase routing
        self.workflow_graph.add_conditional_edges(
            "deal_discovery",
            self._route_from_deal_discovery,
            {
                "property_analysis": "property_analysis",
                "deal_discovery": "deal_discovery",  # Continue scouting
                "completion": "completion"
            }
        )
        
        # Property analysis phase routing
        self.workflow_graph.add_conditional_edges(
            "property_analysis",
            self._route_from_property_analysis,
            {
                "outreach_communication": "outreach_communication",
                "deal_discovery": "deal_discovery",  # Need more deals
                "completion": "completion"
            }
        )
        
        # Outreach communication phase routing
        self.workflow_graph.add_conditional_edges(
            "outreach_communication",
            self._route_from_outreach_communication,
            {
                "negotiation": "negotiation",
                "outreach_communication": "outreach_communication",  # Continue outreach
                "deal_discovery": "deal_discovery",
                "human_escalation": "human_escalation"
            }
        )
        
        # Negotiation phase routing
        self.workflow_graph.add_conditional_edges(
            "negotiation",
            self._route_from_negotiation,
            {
                "contract_generation": "contract_generation",
                "negotiation": "negotiation",  # Continue negotiating
                "outreach_communication": "outreach_communication",  # Back to outreach
                "human_escalation": "human_escalation"
            }
        )
        
        # Contract generation phase routing
        self.workflow_graph.add_conditional_edges(
            "contract_generation",
            self._route_from_contract_generation,
            {
                "due_diligence": "due_diligence",
                "negotiation": "negotiation",  # Renegotiate terms
                "human_escalation": "human_escalation"
            }
        )
        
        # Due diligence phase routing
        self.workflow_graph.add_conditional_edges(
            "due_diligence",
            self._route_from_due_diligence,
            {
                "closing_coordination": "closing_coordination",
                "negotiation": "negotiation",  # Renegotiate based on findings
                "completion": "completion"  # Deal falls through
            }
        )
        
        # Closing coordination phase routing
        self.workflow_graph.add_conditional_edges(
            "closing_coordination",
            self._route_from_closing_coordination,
            {
                "portfolio_integration": "portfolio_integration",
                "due_diligence": "due_diligence",  # Issues found
                "completion": "completion"
            }
        )
        
        # Portfolio integration phase routing
        self.workflow_graph.add_conditional_edges(
            "portfolio_integration",
            self._route_from_portfolio_integration,
            {
                "performance_monitoring": "performance_monitoring",
                "deal_discovery": "deal_discovery",  # Continue with new deals
                "completion": "completion"
            }
        )
        
        # Performance monitoring phase routing
        self.workflow_graph.add_conditional_edges(
            "performance_monitoring",
            self._route_from_performance_monitoring,
            {
                "deal_discovery": "deal_discovery",
                "portfolio_integration": "portfolio_integration",
                "completion": "completion"
            }
        )
        
        # Human escalation routing
        self.workflow_graph.add_conditional_edges(
            "human_escalation",
            self._route_from_human_escalation,
            {
                "deal_discovery": "deal_discovery",
                "property_analysis": "property_analysis",
                "outreach_communication": "outreach_communication",
                "negotiation": "negotiation",
                "contract_generation": "contract_generation",
                "completion": "completion"
            }
        )
        
        # Completion is terminal
        self.workflow_graph.add_edge("completion", END)
    
    # Workflow Phase Implementations
    
    async def _initialization_phase(self, state: AgentState) -> AgentState:
        """Initialize workflow and set up initial parameters"""
        logger.info("Executing initialization phase...")
        
        start_time = datetime.now()
        self.metrics.current_phase = WorkflowPhase.INITIALIZATION
        
        try:
            # Initialize shared memory
            await self.shared_memory.initialize_workflow_memory(self.workflow_id)
            
            # Set up initial state
            if not state.get("workflow_id"):
                state["workflow_id"] = self.workflow_id
            
            state["workflow_status"] = WorkflowStatus.RUNNING
            state["current_phase"] = WorkflowPhase.INITIALIZATION.value
            state["phase_start_time"] = start_time.isoformat()
            
            # Initialize agent coordination
            state["agent_coordination"] = {
                "active_agents": [],
                "pending_handoffs": [],
                "communication_queue": []
            }
            
            # Set initial investment parameters
            if not state.get("investment_strategy"):
                state["investment_strategy"] = {
                    "target_markets": ["Austin", "Dallas", "Houston"],
                    "property_types": ["single_family", "duplex", "small_multifamily"],
                    "max_investment_per_deal": 500000,
                    "target_roi": 0.15,
                    "risk_tolerance": "moderate"
                }
            
            # Initialize performance tracking
            state["performance_metrics"] = self.metrics.to_dict()
            
            # Start monitoring if enabled
            if self.config.enable_real_time_monitoring:
                await self._start_performance_monitoring()
            
            # Start communication batch processor
            if self.config.batch_communications:
                await self._start_communication_processor()
            
            # Add initialization message
            state = StateManager.add_agent_message(
                state,
                AgentType.SUPERVISOR,
                "Workflow orchestration initialized successfully",
                data={
                    "workflow_id": self.workflow_id,
                    "config": self.config.dict(),
                    "phase": WorkflowPhase.INITIALIZATION.value
                },
                priority=1
            )
            
            # Record execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_phase_execution_time("initialization", execution_time)
            
            logger.info(f"Initialization phase completed in {execution_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Initialization phase failed: {e}")
            state = StateManager.add_agent_message(
                state,
                AgentType.SUPERVISOR,
                f"Initialization phase error: {str(e)}",
                priority=5
            )
            state["workflow_status"] = WorkflowStatus.ERROR
        
        return state
    
    async def _deal_discovery_phase(self, state: AgentState) -> AgentState:
        """Execute deal discovery using scout agent"""
        logger.info("Executing deal discovery phase...")
        
        start_time = datetime.now()
        self.metrics.current_phase = WorkflowPhase.DEAL_DISCOVERY
        
        try:
            # Import scout agent
            from ..agents.scout_agent import ScoutAgent
            
            # Create or get scout agent
            if "scout" not in self.agent_registry:
                self.agent_registry["scout"] = ScoutAgent()
            
            scout_agent = self.agent_registry["scout"]
            
            # Execute scouting task
            scout_result = await scout_agent.execute_task(
                "discover_deals",
                {
                    "investment_strategy": state.get("investment_strategy", {}),
                    "market_conditions": state.get("market_conditions", {}),
                    "target_deal_count": self.config.max_concurrent_deals
                },
                state
            )
            
            if scout_result.get("success", False):
                # Update metrics
                new_deals = scout_result.get("deals_found", 0)
                self.metrics.total_deals_processed += new_deals
                
                # Add scout message
                state = StateManager.add_agent_message(
                    state,
                    AgentType.SCOUT,
                    f"Discovered {new_deals} new investment opportunities",
                    data=scout_result,
                    priority=2
                )
                
                logger.info(f"Scout agent discovered {new_deals} deals")
            else:
                logger.warning(f"Scout agent failed: {scout_result.get('error')}")
            
            # Record execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_phase_execution_time("deal_discovery", execution_time)
            
        except Exception as e:
            logger.error(f"Deal discovery phase failed: {e}")
            state = StateManager.add_agent_message(
                state,
                AgentType.SUPERVISOR,
                f"Deal discovery phase error: {str(e)}",
                priority=4
            )
        
        return state
    
    async def _property_analysis_phase(self, state: AgentState) -> AgentState:
        """Execute property analysis using analyst agent"""
        logger.info("Executing property analysis phase...")
        
        start_time = datetime.now()
        self.metrics.current_phase = WorkflowPhase.PROPERTY_ANALYSIS
        
        try:
            # Import analyst agent
            from ..agents.analyst_agent import AnalystAgent
            
            # Create or get analyst agent
            if "analyst" not in self.agent_registry:
                self.agent_registry["analyst"] = AnalystAgent()
            
            analyst_agent = self.agent_registry["analyst"]
            
            # Find unanalyzed deals
            current_deals = state.get("current_deals", [])
            unanalyzed_deals = [
                deal for deal in current_deals
                if not deal.get("analyzed", False)
            ]
            
            if unanalyzed_deals:
                # Execute analysis task
                analysis_result = await analyst_agent.execute_task(
                    "analyze_deals",
                    {
                        "deals": unanalyzed_deals[:5],  # Analyze up to 5 deals
                        "market_conditions": state.get("market_conditions", {}),
                        "investment_strategy": state.get("investment_strategy", {})
                    },
                    state
                )
                
                if analysis_result.get("success", False):
                    # Update metrics
                    analyzed_count = analysis_result.get("deals_analyzed", 0)
                    approved_count = analysis_result.get("deals_approved", 0)
                    
                    self.metrics.deals_approved += approved_count
                    self.metrics.total_investment_analyzed += analysis_result.get("total_investment_analyzed", 0)
                    self.metrics.potential_profit_identified += analysis_result.get("potential_profit", 0)
                    
                    # Add analyst message
                    state = StateManager.add_agent_message(
                        state,
                        AgentType.ANALYST,
                        f"Analyzed {analyzed_count} deals, approved {approved_count}",
                        data=analysis_result,
                        priority=2
                    )
                    
                    logger.info(f"Analyst agent analyzed {analyzed_count} deals")
                else:
                    logger.warning(f"Analyst agent failed: {analysis_result.get('error')}")
            
            # Record execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_phase_execution_time("property_analysis", execution_time)
            
        except Exception as e:
            logger.error(f"Property analysis phase failed: {e}")
            state = StateManager.add_agent_message(
                state,
                AgentType.SUPERVISOR,
                f"Property analysis phase error: {str(e)}",
                priority=4
            )
        
        return state
    
    async def _outreach_communication_phase(self, state: AgentState) -> AgentState:
        """Execute outreach and communication using negotiator agent"""
        logger.info("Executing outreach communication phase...")
        
        start_time = datetime.now()
        self.metrics.current_phase = WorkflowPhase.OUTREACH_COMMUNICATION
        
        try:
            # Import negotiator agent
            from ..agents.negotiator_agent import NegotiatorAgent
            
            # Create or get negotiator agent
            if "negotiator" not in self.agent_registry:
                self.agent_registry["negotiator"] = NegotiatorAgent()
            
            negotiator_agent = self.agent_registry["negotiator"]
            
            # Execute outreach task
            outreach_result = await negotiator_agent.execute_task(
                "initiate_outreach",
                {
                    "approved_deals": StateManager.get_deals_by_status(state, DealStatus.APPROVED),
                    "communication_config": {
                        "max_outreach_per_hour": self.config.max_outreach_per_hour,
                        "batch_communications": self.config.batch_communications
                    }
                },
                state
            )
            
            if outreach_result.get("success", False):
                # Update metrics
                campaigns_created = outreach_result.get("campaigns_created", 0)
                messages_sent = outreach_result.get("messages_sent", 0)
                
                self.metrics.messages_sent += messages_sent
                
                # Add negotiator message
                state = StateManager.add_agent_message(
                    state,
                    AgentType.NEGOTIATOR,
                    f"Created {campaigns_created} outreach campaigns, sent {messages_sent} messages",
                    data=outreach_result,
                    priority=2
                )
                
                logger.info(f"Negotiator agent created {campaigns_created} campaigns")
            else:
                logger.warning(f"Negotiator agent failed: {outreach_result.get('error')}")
            
            # Record execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_phase_execution_time("outreach_communication", execution_time)
            
        except Exception as e:
            logger.error(f"Outreach communication phase failed: {e}")
            state = StateManager.add_agent_message(
                state,
                AgentType.SUPERVISOR,
                f"Outreach communication phase error: {str(e)}",
                priority=4
            )
        
        return state
    
    async def _negotiation_phase(self, state: AgentState) -> AgentState:
        """Execute negotiation management"""
        logger.info("Executing negotiation phase...")
        
        start_time = datetime.now()
        self.metrics.current_phase = WorkflowPhase.NEGOTIATION
        
        try:
            # Get negotiator agent
            negotiator_agent = self.agent_registry.get("negotiator")
            
            if negotiator_agent:
                # Execute negotiation management
                negotiation_result = await negotiator_agent.execute_task(
                    "manage_negotiations",
                    {
                        "active_negotiations": state.get("active_negotiations", []),
                        "auto_approve_threshold": self.config.auto_approve_threshold
                    },
                    state
                )
                
                if negotiation_result.get("success", False):
                    # Update metrics
                    responses_processed = negotiation_result.get("responses_processed", 0)
                    deals_agreed = negotiation_result.get("deals_agreed", 0)
                    
                    self.metrics.responses_received += responses_processed
                    self.metrics.deals_under_contract += deals_agreed
                    
                    # Add negotiation message
                    state = StateManager.add_agent_message(
                        state,
                        AgentType.NEGOTIATOR,
                        f"Processed {responses_processed} responses, {deals_agreed} deals agreed",
                        data=negotiation_result,
                        priority=2
                    )
                    
                    logger.info(f"Negotiation phase processed {responses_processed} responses")
            
            # Record execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_phase_execution_time("negotiation", execution_time)
            
        except Exception as e:
            logger.error(f"Negotiation phase failed: {e}")
            state = StateManager.add_agent_message(
                state,
                AgentType.SUPERVISOR,
                f"Negotiation phase error: {str(e)}",
                priority=4
            )
        
        return state
    
    async def _contract_generation_phase(self, state: AgentState) -> AgentState:
        """Execute contract generation using contract agent"""
        logger.info("Executing contract generation phase...")
        
        start_time = datetime.now()
        self.metrics.current_phase = WorkflowPhase.CONTRACT_GENERATION
        
        try:
            # Import contract agent
            from ..agents.contract_agent import ContractAgent
            
            # Create or get contract agent
            if "contract" not in self.agent_registry:
                self.agent_registry["contract"] = ContractAgent()
            
            contract_agent = self.agent_registry["contract"]
            
            # Execute contract generation
            contract_result = await contract_agent.execute_task(
                "generate_contracts",
                {
                    "agreed_deals": StateManager.get_deals_by_status(state, DealStatus.AGREED),
                    "auto_send_for_signature": True
                },
                state
            )
            
            if contract_result.get("success", False):
                # Update metrics
                contracts_generated = contract_result.get("contracts_generated", 0)
                
                # Add contract message
                state = StateManager.add_agent_message(
                    state,
                    AgentType.CONTRACT,
                    f"Generated {contracts_generated} contracts",
                    data=contract_result,
                    priority=2
                )
                
                logger.info(f"Contract agent generated {contracts_generated} contracts")
            
            # Record execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_phase_execution_time("contract_generation", execution_time)
            
        except Exception as e:
            logger.error(f"Contract generation phase failed: {e}")
            state = StateManager.add_agent_message(
                state,
                AgentType.SUPERVISOR,
                f"Contract generation phase error: {str(e)}",
                priority=4
            )
        
        return state
    
    async def _due_diligence_phase(self, state: AgentState) -> AgentState:
        """Execute due diligence management"""
        logger.info("Executing due diligence phase...")
        
        start_time = datetime.now()
        self.metrics.current_phase = WorkflowPhase.DUE_DILIGENCE
        
        try:
            # Get contract agent for due diligence management
            contract_agent = self.agent_registry.get("contract")
            
            if contract_agent:
                # Execute due diligence task
                dd_result = await contract_agent.execute_task(
                    "manage_due_diligence",
                    {
                        "contracts_under_review": StateManager.get_deals_by_status(state, DealStatus.UNDER_CONTRACT)
                    },
                    state
                )
                
                if dd_result.get("success", False):
                    # Add due diligence message
                    state = StateManager.add_agent_message(
                        state,
                        AgentType.CONTRACT,
                        f"Due diligence progress updated",
                        data=dd_result,
                        priority=2
                    )
            
            # Record execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_phase_execution_time("due_diligence", execution_time)
            
        except Exception as e:
            logger.error(f"Due diligence phase failed: {e}")
            state = StateManager.add_agent_message(
                state,
                AgentType.SUPERVISOR,
                f"Due diligence phase error: {str(e)}",
                priority=4
            )
        
        return state
    
    async def _closing_coordination_phase(self, state: AgentState) -> AgentState:
        """Execute closing coordination"""
        logger.info("Executing closing coordination phase...")
        
        start_time = datetime.now()
        self.metrics.current_phase = WorkflowPhase.CLOSING_COORDINATION
        
        try:
            # Get contract agent for closing coordination
            contract_agent = self.agent_registry.get("contract")
            
            if contract_agent:
                # Execute closing coordination
                closing_result = await contract_agent.execute_task(
                    "coordinate_closing",
                    {
                        "deals_ready_to_close": StateManager.get_deals_by_status(state, DealStatus.READY_TO_CLOSE)
                    },
                    state
                )
                
                if closing_result.get("success", False):
                    # Update metrics
                    deals_closed = closing_result.get("deals_closed", 0)
                    self.metrics.deals_closed += deals_closed
                    
                    # Add closing message
                    state = StateManager.add_agent_message(
                        state,
                        AgentType.CONTRACT,
                        f"Coordinated closing for {deals_closed} deals",
                        data=closing_result,
                        priority=2
                    )
            
            # Record execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_phase_execution_time("closing_coordination", execution_time)
            
        except Exception as e:
            logger.error(f"Closing coordination phase failed: {e}")
            state = StateManager.add_agent_message(
                state,
                AgentType.SUPERVISOR,
                f"Closing coordination phase error: {str(e)}",
                priority=4
            )
        
        return state
    
    async def _portfolio_integration_phase(self, state: AgentState) -> AgentState:
        """Execute portfolio integration using portfolio agent"""
        logger.info("Executing portfolio integration phase...")
        
        start_time = datetime.now()
        self.metrics.current_phase = WorkflowPhase.PORTFOLIO_INTEGRATION
        
        try:
            # Import portfolio agent
            from ..agents.portfolio_agent import PortfolioAgent
            
            # Create or get portfolio agent
            if "portfolio" not in self.agent_registry:
                self.agent_registry["portfolio"] = PortfolioAgent()
            
            portfolio_agent = self.agent_registry["portfolio"]
            
            # Execute portfolio integration
            portfolio_result = await portfolio_agent.execute_task(
                "integrate_new_properties",
                {
                    "closed_deals": StateManager.get_deals_by_status(state, DealStatus.CLOSED),
                    "portfolio_strategy": state.get("investment_strategy", {})
                },
                state
            )
            
            if portfolio_result.get("success", False):
                # Add portfolio message
                state = StateManager.add_agent_message(
                    state,
                    AgentType.PORTFOLIO,
                    f"Integrated new properties into portfolio",
                    data=portfolio_result,
                    priority=2
                )
            
            # Record execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_phase_execution_time("portfolio_integration", execution_time)
            
        except Exception as e:
            logger.error(f"Portfolio integration phase failed: {e}")
            state = StateManager.add_agent_message(
                state,
                AgentType.SUPERVISOR,
                f"Portfolio integration phase error: {str(e)}",
                priority=4
            )
        
        return state
    
    async def _performance_monitoring_phase(self, state: AgentState) -> AgentState:
        """Execute performance monitoring and optimization"""
        logger.info("Executing performance monitoring phase...")
        
        start_time = datetime.now()
        self.metrics.current_phase = WorkflowPhase.PERFORMANCE_MONITORING
        
        try:
            # Update performance metrics
            await self._update_performance_metrics(state)
            
            # Check for performance alerts
            alerts = await self._check_performance_alerts(state)
            
            if alerts:
                self.performance_alerts.extend(alerts)
                
                # Add performance alert message
                state = StateManager.add_agent_message(
                    state,
                    AgentType.SUPERVISOR,
                    f"Generated {len(alerts)} performance alerts",
                    data={"alerts": alerts},
                    priority=3
                )
            
            # Update state with current metrics
            state["performance_metrics"] = self.metrics.to_dict()
            
            # Record execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_phase_execution_time("performance_monitoring", execution_time)
            
        except Exception as e:
            logger.error(f"Performance monitoring phase failed: {e}")
            state = StateManager.add_agent_message(
                state,
                AgentType.SUPERVISOR,
                f"Performance monitoring phase error: {str(e)}",
                priority=4
            )
        
        return state
    
    async def _human_escalation_phase(self, state: AgentState) -> AgentState:
        """Handle human escalation"""
        logger.info("Executing human escalation phase...")
        
        start_time = datetime.now()
        self.metrics.escalations_to_human += 1
        
        try:
            # Prepare escalation data
            escalation_data = {
                "workflow_id": self.workflow_id,
                "current_phase": self.metrics.current_phase.value,
                "escalation_reason": state.get("escalation_reason", "Manual escalation"),
                "context": state.get("escalation_context", {}),
                "performance_metrics": self.metrics.to_dict(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Add escalation message
            state = StateManager.add_agent_message(
                state,
                AgentType.SUPERVISOR,
                "Workflow escalated to human oversight",
                data=escalation_data,
                priority=5
            )
            
            # Set workflow status
            state["workflow_status"] = WorkflowStatus.HUMAN_ESCALATION
            state["human_approval_required"] = True
            state["escalation_data"] = escalation_data
            
            # Record execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_phase_execution_time("human_escalation", execution_time)
            
            logger.warning("Workflow escalated to human oversight")
            
        except Exception as e:
            logger.error(f"Human escalation phase failed: {e}")
            state = StateManager.add_agent_message(
                state,
                AgentType.SUPERVISOR,
                f"Human escalation phase error: {str(e)}",
                priority=5
            )
        
        return state
    
    async def _completion_phase(self, state: AgentState) -> AgentState:
        """Complete workflow execution"""
        logger.info("Executing completion phase...")
        
        try:
            # Finalize metrics
            self.metrics.end_time = datetime.now()
            self.metrics.current_phase = WorkflowPhase.COMPLETION
            
            # Calculate final performance metrics
            total_execution_time = (self.metrics.end_time - self.metrics.start_time).total_seconds()
            
            # Update state with final results
            state["workflow_status"] = WorkflowStatus.COMPLETED
            state["completion_time"] = self.metrics.end_time.isoformat()
            state["total_execution_time"] = total_execution_time
            state["final_metrics"] = self.metrics.to_dict()
            
            # Add completion message
            state = StateManager.add_agent_message(
                state,
                AgentType.SUPERVISOR,
                f"Workflow completed successfully in {total_execution_time:.2f}s",
                data={
                    "total_deals_processed": self.metrics.total_deals_processed,
                    "deals_closed": self.metrics.deals_closed,
                    "total_profit_identified": self.metrics.potential_profit_identified,
                    "execution_time": total_execution_time
                },
                priority=1
            )
            
            # Stop monitoring tasks
            await self._stop_background_tasks()
            
            # Store workflow history
            self.workflow_history.append({
                "workflow_id": self.workflow_id,
                "metrics": self.metrics.to_dict(),
                "completion_time": self.metrics.end_time.isoformat()
            })
            
            logger.info(f"Workflow {self.workflow_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Completion phase failed: {e}")
            state = StateManager.add_agent_message(
                state,
                AgentType.SUPERVISOR,
                f"Completion phase error: {str(e)}",
                priority=5
            )
            state["workflow_status"] = WorkflowStatus.ERROR
        
        return state
    
    # Routing Logic Methods
    
    def _route_from_initialization(self, state: AgentState) -> str:
        """Route from initialization phase"""
        # Check if we have existing deals to process
        current_deals = state.get("current_deals", [])
        
        if not current_deals:
            return "deal_discovery"
        elif any(not deal.get("analyzed", False) for deal in current_deals):
            return "property_analysis"
        else:
            return "performance_monitoring"
    
    def _route_from_deal_discovery(self, state: AgentState) -> str:
        """Route from deal discovery phase"""
        current_deals = state.get("current_deals", [])
        
        if not current_deals:
            # Continue scouting if no deals found
            return "deal_discovery"
        else:
            # Move to analysis
            return "property_analysis"
    
    def _route_from_property_analysis(self, state: AgentState) -> str:
        """Route from property analysis phase"""
        approved_deals = StateManager.get_deals_by_status(state, DealStatus.APPROVED)
        
        if approved_deals:
            return "outreach_communication"
        else:
            # Need more deals
            return "deal_discovery"
    
    def _route_from_outreach_communication(self, state: AgentState) -> str:
        """Route from outreach communication phase"""
        active_negotiations = state.get("active_negotiations", [])
        
        if active_negotiations:
            return "negotiation"
        else:
            # Continue outreach or find more deals
            approved_deals = StateManager.get_deals_by_status(state, DealStatus.APPROVED)
            if approved_deals:
                return "outreach_communication"
            else:
                return "deal_discovery"
    
    def _route_from_negotiation(self, state: AgentState) -> str:
        """Route from negotiation phase"""
        agreed_deals = StateManager.get_deals_by_status(state, DealStatus.AGREED)
        
        if agreed_deals:
            return "contract_generation"
        else:
            # Continue negotiating or go back to outreach
            active_negotiations = state.get("active_negotiations", [])
            if active_negotiations:
                return "negotiation"
            else:
                return "outreach_communication"
    
    def _route_from_contract_generation(self, state: AgentState) -> str:
        """Route from contract generation phase"""
        under_contract_deals = StateManager.get_deals_by_status(state, DealStatus.UNDER_CONTRACT)
        
        if under_contract_deals:
            return "due_diligence"
        else:
            # Go back to negotiation
            return "negotiation"
    
    def _route_from_due_diligence(self, state: AgentState) -> str:
        """Route from due diligence phase"""
        ready_to_close_deals = StateManager.get_deals_by_status(state, DealStatus.READY_TO_CLOSE)
        
        if ready_to_close_deals:
            return "closing_coordination"
        else:
            # Check if deals fell through or need renegotiation
            return "completion"
    
    def _route_from_closing_coordination(self, state: AgentState) -> str:
        """Route from closing coordination phase"""
        closed_deals = StateManager.get_deals_by_status(state, DealStatus.CLOSED)
        
        if closed_deals:
            return "portfolio_integration"
        else:
            return "completion"
    
    def _route_from_portfolio_integration(self, state: AgentState) -> str:
        """Route from portfolio integration phase"""
        # Check if we should continue with more deals or complete
        total_deals = len(state.get("current_deals", []))
        
        if total_deals < self.config.max_concurrent_deals:
            return "deal_discovery"
        else:
            return "performance_monitoring"
    
    def _route_from_performance_monitoring(self, state: AgentState) -> str:
        """Route from performance monitoring phase"""
        # Check if workflow should continue or complete
        workflow_duration = (datetime.now() - self.metrics.start_time).total_seconds() / 60
        
        if workflow_duration > self.config.max_execution_time_minutes:
            return "completion"
        else:
            return "deal_discovery"
    
    def _route_from_human_escalation(self, state: AgentState) -> str:
        """Route from human escalation phase"""
        human_input = state.get("human_input", "").lower()
        
        if human_input in ["continue", "proceed", "yes"]:
            # Return to the phase that triggered escalation
            escalation_context = state.get("escalation_context", {})
            return escalation_context.get("return_phase", "deal_discovery")
        else:
            return "completion"
    
    # Performance Monitoring Methods
    
    async def _start_performance_monitoring(self):
        """Start background performance monitoring"""
        if not self.monitoring_task or self.monitoring_task.done():
            self.monitoring_task = asyncio.create_task(self._performance_monitoring_loop())
            logger.info("Performance monitoring started")
    
    async def _performance_monitoring_loop(self):
        """Background performance monitoring loop"""
        while True:
            try:
                await asyncio.sleep(self.config.metrics_collection_interval)
                
                # Update performance metrics
                await self._collect_performance_metrics()
                
                # Check for alerts
                alerts = await self._check_performance_alerts({})
                
                if alerts:
                    self.performance_alerts.extend(alerts)
                    logger.warning(f"Generated {len(alerts)} performance alerts")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
    
    async def _start_communication_processor(self):
        """Start background communication batch processor"""
        if not self.batch_processor_task or self.batch_processor_task.done():
            self.batch_processor_task = asyncio.create_task(self._communication_processor_loop())
            logger.info("Communication batch processor started")
    
    async def _communication_processor_loop(self):
        """Background communication processing loop"""
        while True:
            try:
                await asyncio.sleep(self.config.communication_delay_seconds)
                
                if self.message_queue:
                    # Process batched messages
                    messages_to_process = self.message_queue.copy()
                    self.message_queue.clear()
                    
                    await self._process_message_batch(messages_to_process)
                    
                    logger.debug(f"Processed {len(messages_to_process)} batched messages")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Communication processor error: {e}")
    
    async def _stop_background_tasks(self):
        """Stop all background tasks"""
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self.batch_processor_task and not self.batch_processor_task.done():
            self.batch_processor_task.cancel()
            try:
                await self.batch_processor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Background tasks stopped")
    
    # Helper Methods
    
    def _record_phase_execution_time(self, phase: str, execution_time: float):
        """Record execution time for a phase"""
        if phase not in self.metrics.agent_execution_times:
            self.metrics.agent_execution_times[phase] = []
        
        self.metrics.agent_execution_times[phase].append(execution_time)
    
    async def _update_performance_metrics(self, state: AgentState):
        """Update performance metrics from current state"""
        # Update deal counts
        current_deals = state.get("current_deals", [])
        self.metrics.total_deals_processed = len(current_deals)
        
        # Count deals by status
        self.metrics.deals_approved = len([d for d in current_deals if d.get("status") == "approved"])
        self.metrics.deals_under_contract = len([d for d in current_deals if d.get("status") == "under_contract"])
        self.metrics.deals_closed = len([d for d in current_deals if d.get("status") == "closed"])
        
        # Update communication metrics
        agent_messages = state.get("agent_messages", [])
        self.metrics.messages_sent = len([m for m in agent_messages if m.get("agent") == "negotiator"])
        
        # Calculate agent success rates
        for agent_type in self.agent_registry.keys():
            if agent_type in self.metrics.agent_execution_times:
                execution_times = self.metrics.agent_execution_times[agent_type]
                if execution_times:
                    avg_time = sum(execution_times) / len(execution_times)
                    # Success rate based on execution time (faster = better)
                    self.metrics.agent_success_rates[agent_type] = max(0.0, 1.0 - (avg_time / 300.0))
    
    async def _collect_performance_metrics(self):
        """Collect real-time performance metrics"""
        # This would integrate with actual monitoring systems
        # For now, we'll update basic metrics
        pass
    
    async def _check_performance_alerts(self, state: AgentState) -> List[Dict[str, Any]]:
        """Check for performance alerts"""
        alerts = []
        
        # Check execution time alerts
        for agent_type, execution_times in self.metrics.agent_execution_times.items():
            if execution_times:
                avg_time = sum(execution_times) / len(execution_times)
                if avg_time > 300:  # 5 minutes
                    alerts.append({
                        "type": "performance_alert",
                        "agent": agent_type,
                        "message": f"Agent {agent_type} average execution time is {avg_time:.2f}s",
                        "severity": "warning",
                        "timestamp": datetime.now().isoformat()
                    })
        
        # Check success rate alerts
        for agent_type, success_rate in self.metrics.agent_success_rates.items():
            if success_rate < self.config.performance_alert_threshold:
                alerts.append({
                    "type": "success_rate_alert",
                    "agent": agent_type,
                    "message": f"Agent {agent_type} success rate is {success_rate:.2%}",
                    "severity": "warning",
                    "timestamp": datetime.now().isoformat()
                })
        
        return alerts
    
    async def _process_message_batch(self, messages: List[Dict[str, Any]]):
        """Process a batch of messages"""
        # This would integrate with actual communication systems
        # For now, we'll just log the batch processing
        logger.debug(f"Processing batch of {len(messages)} messages")
    
    # Public Interface Methods
    
    async def start_workflow(self, initial_state: Optional[AgentState] = None, trigger: WorkflowTrigger = WorkflowTrigger.MANUAL_START) -> str:
        """Start the end-to-end workflow"""
        logger.info(f"Starting workflow with trigger: {trigger.value}")
        
        if not initial_state:
            initial_state = StateManager.create_initial_state()
            initial_state["workflow_id"] = self.workflow_id
        
        initial_state["workflow_trigger"] = trigger.value
        initial_state["workflow_config"] = self.config.dict()
        
        try:
            # Execute workflow
            config = {"configurable": {"thread_id": self.workflow_id}}
            result = await self.compiled_workflow.ainvoke(initial_state, config)
            
            logger.info(f"Workflow {self.workflow_id} execution completed")
            return self.workflow_id
            
        except Exception as e:
            logger.error(f"Workflow {self.workflow_id} failed: {e}")
            raise e
    
    async def continue_workflow(self, human_input: Optional[str] = None) -> AgentState:
        """Continue a paused workflow"""
        config = {"configurable": {"thread_id": self.workflow_id}}
        
        # Add human input if provided
        if human_input:
            current_state = await self.get_workflow_state()
            current_state["human_input"] = human_input
            current_state["human_approval_required"] = False
        
        # Continue workflow
        result = await self.compiled_workflow.ainvoke(None, config)
        return result
    
    async def get_workflow_state(self) -> AgentState:
        """Get current workflow state"""
        config = {"configurable": {"thread_id": self.workflow_id}}
        state = await self.compiled_workflow.aget_state(config)
        return state.values
    
    def get_workflow_metrics(self) -> Dict[str, Any]:
        """Get current workflow metrics"""
        return self.metrics.to_dict()
    
    def get_performance_alerts(self) -> List[Dict[str, Any]]:
        """Get current performance alerts"""
        return self.performance_alerts.copy()
    
    def get_workflow_history(self) -> List[Dict[str, Any]]:
        """Get workflow execution history"""
        return self.workflow_history.copy()
    
    async def pause_workflow(self) -> bool:
        """Pause the current workflow"""
        try:
            # Stop background tasks
            await self._stop_background_tasks()
            
            # Update state
            current_state = await self.get_workflow_state()
            current_state["workflow_status"] = WorkflowStatus.PAUSED
            
            logger.info(f"Workflow {self.workflow_id} paused")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pause workflow: {e}")
            return False
    
    async def resume_workflow(self) -> bool:
        """Resume a paused workflow"""
        try:
            # Restart background tasks
            if self.config.enable_real_time_monitoring:
                await self._start_performance_monitoring()
            
            if self.config.batch_communications:
                await self._start_communication_processor()
            
            # Continue workflow
            await self.continue_workflow()
            
            logger.info(f"Workflow {self.workflow_id} resumed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume workflow: {e}")
            return False
    
    async def stop_workflow(self) -> bool:
        """Stop the current workflow"""
        try:
            # Stop background tasks
            await self._stop_background_tasks()
            
            # Update metrics
            self.metrics.end_time = datetime.now()
            
            # Update state
            current_state = await self.get_workflow_state()
            current_state["workflow_status"] = WorkflowStatus.STOPPED
            current_state["stop_time"] = self.metrics.end_time.isoformat()
            
            logger.info(f"Workflow {self.workflow_id} stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop workflow: {e}")
            return False


# Global workflow orchestrator instance
workflow_orchestrator: Optional[WorkflowOrchestrator] = None


def get_workflow_orchestrator(config: Optional[WorkflowConfiguration] = None) -> WorkflowOrchestrator:
    """Get or create the global workflow orchestrator"""
    global workflow_orchestrator
    
    if workflow_orchestrator is None:
        workflow_orchestrator = WorkflowOrchestrator(config)
    
    return workflow_orchestrator