"""
Scout Agent - Autonomous Deal Discovery and Lead Generation
Specialized agent for discovering and evaluating real estate investment opportunities
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import uuid
import json

from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from ..core.base_agent import BaseAgent, AgentCapability, AgentStatus
from ..core.agent_state import AgentState, AgentType, Deal, DealStatus, StateManager
from ..core.agent_tools import tool_registry, LangChainToolAdapter
from ..core.llm_config import llm_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InvestmentCriteria(BaseModel):
    """Investment criteria for filtering deals"""
    max_price: Optional[float] = None
    min_price: Optional[float] = None
    property_types: List[str] = Field(default_factory=lambda: ["single_family", "multi_family", "condo"])
    min_bedrooms: Optional[int] = None
    max_bedrooms: Optional[int] = None
    min_bathrooms: Optional[float] = None
    max_bathrooms: Optional[float] = None
    min_square_feet: Optional[int] = None
    max_square_feet: Optional[int] = None
    max_days_on_market: Optional[int] = 90
    target_locations: List[str] = Field(default_factory=list)
    exclude_locations: List[str] = Field(default_factory=list)
    min_cap_rate: Optional[float] = 0.08
    min_cash_flow: Optional[float] = 200
    max_repair_cost: Optional[float] = 50000
    motivation_indicators: List[str] = Field(default_factory=lambda: [
        "foreclosure", "divorce", "job_relocation", "estate_sale", "distressed"
    ])


class LeadScore(BaseModel):
    """Lead scoring model"""
    overall_score: float = Field(ge=0.0, le=10.0)
    profit_potential: float = Field(ge=0.0, le=10.0)
    deal_feasibility: float = Field(ge=0.0, le=10.0)
    seller_motivation: float = Field(ge=0.0, le=10.0)
    market_conditions: float = Field(ge=0.0, le=10.0)
    confidence_level: float = Field(ge=0.0, le=1.0)
    scoring_factors: Dict[str, Any] = Field(default_factory=dict)


class DealOpportunity(BaseModel):
    """Represents a discovered deal opportunity"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    property_address: str
    city: str
    state: str
    zip_code: str
    
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
    estimated_repair_cost: Optional[float] = None
    potential_profit: Optional[float] = None
    
    # Lead Information
    lead_score: Optional[LeadScore] = None
    source: str
    source_url: Optional[str] = None
    days_on_market: Optional[int] = None
    motivation_indicators: List[str] = Field(default_factory=list)
    
    # Owner Information
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_email: Optional[str] = None
    owner_address: Optional[str] = None
    
    # Metadata
    discovered_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class ScoutingWorkflow(BaseModel):
    """Represents a scouting workflow configuration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    criteria: InvestmentCriteria
    target_sources: List[str] = Field(default_factory=lambda: ["mls", "public_records", "foreclosures"])
    scan_frequency: int = 60  # minutes
    max_deals_per_scan: int = 50
    auto_score_threshold: float = 7.0
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    last_run: Optional[datetime] = None


class ScoutAgent(BaseAgent):
    """
    Scout Agent - Autonomous Deal Discovery and Lead Generation
    
    Responsibilities:
    - Continuously scan multiple data sources for investment opportunities
    - Apply investment criteria to filter properties
    - Score and prioritize leads based on potential profitability
    - Gather comprehensive property and owner information
    - Identify motivated sellers and distressed properties
    """
    
    def __init__(self, name: str = "ScoutAgent", description: str = "Autonomous deal discovery agent"):
        # Define agent capabilities
        capabilities = [
            AgentCapability(
                name="property_discovery",
                description="Discover properties from multiple sources (MLS, foreclosures, public records)",
                input_schema={
                    "criteria": "InvestmentCriteria",
                    "sources": "List[str]",
                    "max_results": "int"
                },
                output_schema={
                    "deals": "List[DealOpportunity]",
                    "total_found": "int",
                    "sources_scanned": "List[str]"
                },
                required_tools=["property_search", "market_data"],
                estimated_duration=120
            ),
            AgentCapability(
                name="lead_scoring",
                description="Score and prioritize leads based on investment potential",
                input_schema={
                    "deals": "List[DealOpportunity]",
                    "criteria": "InvestmentCriteria"
                },
                output_schema={
                    "scored_deals": "List[DealOpportunity]",
                    "top_deals": "List[DealOpportunity]"
                },
                required_tools=["property_analysis", "financial_calculator"],
                estimated_duration=60
            ),
            AgentCapability(
                name="owner_research",
                description="Research property owners and gather contact information",
                input_schema={
                    "properties": "List[DealOpportunity]"
                },
                output_schema={
                    "enriched_deals": "List[DealOpportunity]"
                },
                required_tools=["property_search"],
                estimated_duration=30
            ),
            AgentCapability(
                name="motivation_analysis",
                description="Analyze seller motivation indicators",
                input_schema={
                    "deals": "List[DealOpportunity]"
                },
                output_schema={
                    "analyzed_deals": "List[DealOpportunity]"
                },
                required_tools=["market_data"],
                estimated_duration=45
            )
        ]
        
        # Scout-specific attributes (initialize before base agent)
        self.investment_criteria = InvestmentCriteria()
        self.active_workflows: Dict[str, ScoutingWorkflow] = {}
        self.discovered_deals: Dict[str, DealOpportunity] = {}
        self.scanning_enabled = True
        self.last_scan_time: Optional[datetime] = None
        
        # Performance metrics
        self.deals_discovered_today = 0
        self.total_deals_discovered = 0
        self.average_lead_score = 0.0
        self.top_sources: Dict[str, int] = {}
        
        # Initialize agent executor
        self.agent_executor: Optional[AgentExecutor] = None
        
        # Initialize base agent
        super().__init__(
            agent_type=AgentType.SCOUT,
            name=name,
            description=description,
            capabilities=capabilities
        )
        
        # Setup agent executor after base initialization
        self._setup_agent_executor()
    
    def _agent_specific_initialization(self):
        """Scout agent specific initialization"""
        logger.info("Initializing Scout Agent...")
        
        # Set up default investment criteria
        self._setup_default_criteria()
        
        # Create default scouting workflow
        self._create_default_workflow()
        
        # Initialize scanning schedule
        self._schedule_continuous_scanning()
        
        logger.info("Scout Agent initialization complete")
    
    def _setup_default_criteria(self):
        """Set up default investment criteria"""
        self.investment_criteria = InvestmentCriteria(
            max_price=500000,
            min_price=50000,
            property_types=["single_family", "multi_family", "condo", "townhouse"],
            max_days_on_market=120,
            min_cap_rate=0.06,
            min_cash_flow=150,
            max_repair_cost=75000,
            motivation_indicators=[
                "foreclosure", "pre_foreclosure", "divorce", "job_relocation", 
                "estate_sale", "distressed", "vacant", "tax_lien"
            ]
        )
    
    def _create_default_workflow(self):
        """Create default scouting workflow"""
        default_workflow = ScoutingWorkflow(
            name="Primary Deal Discovery",
            description="Main workflow for discovering investment opportunities",
            criteria=self.investment_criteria,
            target_sources=["mls", "public_records", "foreclosures", "off_market"],
            scan_frequency=30,  # 30 minutes
            max_deals_per_scan=25,
            auto_score_threshold=6.5
        )
        
        self.active_workflows[default_workflow.id] = default_workflow
    
    def _setup_agent_executor(self):
        """Set up the LangChain agent executor"""
        try:
            # Get available tools for scout agent
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
            
            logger.info(f"Scout agent executor created with {len(langchain_tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to setup scout agent executor: {e}")
            self.agent_executor = None
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the scout agent"""
        return """
        You are an expert real estate scout agent specializing in discovering high-potential investment opportunities.
        
        Your primary mission is to:
        1. Continuously scan multiple data sources for investment properties
        2. Apply sophisticated investment criteria to filter opportunities
        3. Score and prioritize leads based on profit potential and feasibility
        4. Research property owners and identify motivation indicators
        5. Gather comprehensive property and market data
        
        Key Responsibilities:
        - Property Discovery: Search MLS listings, foreclosures, public records, and off-market properties
        - Lead Qualification: Apply investment criteria to filter out unsuitable properties
        - Lead Scoring: Evaluate each opportunity on a 1-10 scale based on:
          * Profit potential (potential equity, cash flow, appreciation)
          * Deal feasibility (financing, timeline, complexity)
          * Seller motivation (urgency, flexibility, circumstances)
          * Market conditions (trends, competition, timing)
        - Owner Research: Find contact information and motivation indicators
        - Data Enrichment: Gather comprehensive property details and market context
        
        Investment Focus Areas:
        - Properties with strong cash flow potential (8%+ cap rates)
        - Distressed properties with significant equity upside
        - Motivated sellers (foreclosure, divorce, relocation, estate sales)
        - Properties in stable or emerging neighborhoods
        - Off-market opportunities with less competition
        
        Quality Standards:
        - Only recommend deals with 7+ lead scores for immediate action
        - Provide conservative estimates and clearly state assumptions
        - Include confidence levels for all estimates and projections
        - Identify and flag potential risks or red flags
        - Prioritize deals with highest profit potential and lowest risk
        
        Communication Style:
        - Be concise and data-driven in your analysis
        - Provide specific numbers and metrics
        - Explain your reasoning for scores and recommendations
        - Highlight key opportunities and urgent actions needed
        - Use structured output for easy processing by other agents
        
        Always focus on finding deals that align with our investment strategy and have strong potential for profitability.
        """
    
    def _schedule_continuous_scanning(self):
        """Schedule continuous scanning based on workflow configurations"""
        # This would integrate with a task scheduler in production
        # For now, we'll track the last scan time and scan frequency
        self.last_scan_time = datetime.now()
        logger.info("Continuous scanning scheduled")
    
    # Core Agent Methods
    
    async def execute_task(self, task: str, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute a specific scout task"""
        logger.info(f"Scout agent executing task: {task}")
        
        try:
            if task == "discover_deals":
                return await self._discover_deals(data, state)
            elif task == "score_leads":
                return await self._score_leads(data, state)
            elif task == "research_owners":
                return await self._research_owners(data, state)
            elif task == "analyze_motivation":
                return await self._analyze_motivation(data, state)
            elif task == "continuous_scan":
                return await self._continuous_scan(data, state)
            else:
                raise ValueError(f"Unknown task: {task}")
                
        except Exception as e:
            logger.error(f"Error executing scout task {task}: {e}")
            return {
                "success": False,
                "error": str(e),
                "task": task
            }
    
    async def process_state(self, state: AgentState) -> AgentState:
        """Process the current state and discover new deals"""
        logger.info("Scout agent processing state...")
        
        try:
            # Check if continuous scanning is needed
            if self._should_scan():
                # Perform continuous scanning
                scan_result = await self._continuous_scan({}, state)
                
                if scan_result.get("success", False):
                    new_deals = scan_result.get("deals", [])
                    
                    # Add new deals to state
                    for deal_data in new_deals:
                        deal = Deal(
                            property_address=deal_data.get("property_address", "Unknown"),
                            city=deal_data.get("city", "Unknown"),
                            state=deal_data.get("state", "Unknown"),
                            zip_code=deal_data.get("zip_code", "Unknown"),
                            status=DealStatus.DISCOVERED,
                            listing_price=deal_data.get("listing_price"),
                            estimated_value=deal_data.get("estimated_value"),
                            potential_profit=deal_data.get("potential_profit"),
                            source="scout_agent",
                            owner_info=deal_data.get("owner_info", {}),
                            motivation_indicators=deal_data.get("motivation_indicators", []),
                            tags=deal_data.get("tags", [])
                        )
                        state = StateManager.add_deal(state, deal)
                    
                    # Update metrics
                    self.deals_discovered_today += len(new_deals)
                    self.total_deals_discovered += len(new_deals)
                    
                    # Add agent message
                    state = StateManager.add_agent_message(
                        state,
                        AgentType.SCOUT,
                        f"Discovered {len(new_deals)} new investment opportunities",
                        data={
                            "deals_found": len(new_deals),
                            "total_scanned": scan_result.get("total_scanned", 0),
                            "sources_used": scan_result.get("sources_used", [])
                        },
                        priority=2
                    )
                    
                    # Set next action based on results
                    if new_deals:
                        state = StateManager.set_next_action(
                            state, 
                            "analyze", 
                            f"Found {len(new_deals)} new deals that need analysis"
                        )
                    
                    logger.info(f"Scout agent discovered {len(new_deals)} new deals")
                else:
                    logger.warning("Scout scanning failed")
            
            # Update last scan time
            self.last_scan_time = datetime.now()
            
            return state
            
        except Exception as e:
            logger.error(f"Error in scout agent state processing: {e}")
            state = StateManager.add_agent_message(
                state,
                AgentType.SCOUT,
                f"Error in scout agent: {str(e)}",
                priority=4
            )
            return state
    
    def get_available_tasks(self) -> List[str]:
        """Get list of tasks this agent can perform"""
        return [
            "discover_deals",
            "score_leads", 
            "research_owners",
            "analyze_motivation",
            "continuous_scan"
        ]
    
    # Private Implementation Methods
    
    def _should_scan(self) -> bool:
        """Check if it's time to perform a scan"""
        if not self.scanning_enabled:
            return False
        
        if not self.last_scan_time:
            return True
        
        # Check if any workflow is due for scanning
        for workflow in self.active_workflows.values():
            if not workflow.enabled:
                continue
                
            if not workflow.last_run:
                return True
                
            time_since_last_run = datetime.now() - workflow.last_run
            if time_since_last_run.total_seconds() >= workflow.scan_frequency * 60:
                return True
        
        return False
    
    async def _continuous_scan(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Perform continuous scanning for new deals"""
        logger.info("Starting continuous deal scanning...")
        
        if not self.agent_executor:
            return {
                "success": False,
                "error": "Agent executor not initialized"
            }
        
        try:
            # Get market context from state
            market_conditions = state.get("market_conditions", {})
            investment_strategy = state.get("investment_strategy", {})
            geographic_focus = state.get("current_geographic_focus", "national")
            
            # Create scanning prompt
            scan_prompt = f"""
            Perform comprehensive deal discovery scan:
            
            Current Context:
            - Geographic Focus: {geographic_focus}
            - Market Conditions: {json.dumps(market_conditions, indent=2)}
            - Investment Strategy: {json.dumps(investment_strategy, indent=2)}
            - Investment Criteria: {self.investment_criteria.dict()}
            
            Mission: Find 10-15 high-potential real estate investment opportunities
            
            Tasks:
            1. Search multiple sources (MLS, foreclosures, public records, off-market)
            2. Apply investment criteria to filter properties
            3. Score each lead (1-10 scale) based on:
               - Profit potential (equity upside, cash flow)
               - Deal feasibility (financing, timeline)
               - Seller motivation (urgency, flexibility)
               - Market conditions (trends, competition)
            4. Research property owners and contact information
            5. Identify motivation indicators
            6. Prioritize by overall investment potential
            
            Focus Areas:
            - Properties with 8%+ cap rates or strong cash flow
            - Distressed properties with significant equity upside
            - Motivated sellers (foreclosure, divorce, relocation, estate)
            - Properties in stable or emerging neighborhoods
            - Off-market opportunities with less competition
            
            For each property, provide:
            - Complete address and property details
            - Financial estimates (listing price, ARV, repair costs)
            - Lead score with detailed reasoning
            - Owner information and motivation indicators
            - Recommended next steps and urgency level
            
            Only include properties with lead scores of 6.0 or higher.
            Provide conservative estimates and state all assumptions clearly.
            """
            
            # Execute scanning
            result = await self.agent_executor.ainvoke({
                "input": scan_prompt,
                "chat_history": []
            })
            
            # Parse the result
            deals = self._parse_scanning_results(result.get("output", ""))
            
            # Update workflow last run times
            for workflow in self.active_workflows.values():
                workflow.last_run = datetime.now()
            
            return {
                "success": True,
                "deals": deals,
                "total_scanned": len(deals),
                "sources_used": ["mls", "public_records", "foreclosures"],
                "scan_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in continuous scanning: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _discover_deals(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Discover deals based on specific criteria"""
        criteria = data.get("criteria", self.investment_criteria.dict())
        sources = data.get("sources", ["mls", "public_records", "foreclosures"])
        max_results = data.get("max_results", 25)
        
        # Use property search tool
        search_result = await tool_registry.execute_tool(
            "property_search",
            self.name,
            self.agent_type.value,
            criteria=criteria,
            location=data.get("location", ""),
            max_results=max_results
        )
        
        if search_result.get("success", False):
            properties = search_result["result"].get("properties", [])
            
            # Convert to deal opportunities
            deals = []
            for prop in properties:
                deal = DealOpportunity(
                    property_address=prop.get("address", "Unknown"),
                    city=prop.get("city", "Unknown"),
                    state=prop.get("state", "Unknown"),
                    zip_code=prop.get("zip_code", "Unknown"),
                    property_type=prop.get("property_type"),
                    bedrooms=prop.get("bedrooms"),
                    bathrooms=prop.get("bathrooms"),
                    square_feet=prop.get("square_feet"),
                    listing_price=prop.get("price"),
                    source=prop.get("source", "unknown"),
                    days_on_market=prop.get("days_on_market")
                )
                deals.append(deal.dict())
            
            return {
                "success": True,
                "deals": deals,
                "total_found": len(deals),
                "sources_scanned": sources
            }
        else:
            return {
                "success": False,
                "error": search_result.get("error", "Property search failed")
            }
    
    async def _score_leads(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Score and prioritize leads"""
        deals = data.get("deals", [])
        scored_deals = []
        
        for deal_data in deals:
            # Calculate lead score
            score = await self._calculate_lead_score(deal_data, state)
            deal_data["lead_score"] = score.dict()
            scored_deals.append(deal_data)
        
        # Sort by overall score
        scored_deals.sort(key=lambda x: x["lead_score"]["overall_score"], reverse=True)
        
        # Get top deals (score >= 7.0)
        top_deals = [deal for deal in scored_deals if deal["lead_score"]["overall_score"] >= 7.0]
        
        return {
            "success": True,
            "scored_deals": scored_deals,
            "top_deals": top_deals,
            "average_score": sum(d["lead_score"]["overall_score"] for d in scored_deals) / len(scored_deals) if scored_deals else 0
        }
    
    async def _research_owners(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Research property owners and gather contact information"""
        properties = data.get("properties", [])
        enriched_deals = []
        
        for prop in properties:
            # Simulate owner research (would integrate with actual data sources)
            owner_info = {
                "owner_name": f"Owner of {prop.get('property_address', 'Unknown')}",
                "owner_phone": "(555) 123-4567",
                "owner_email": "owner@example.com",
                "owner_address": prop.get("property_address", "Unknown")
            }
            
            prop.update(owner_info)
            enriched_deals.append(prop)
        
        return {
            "success": True,
            "enriched_deals": enriched_deals
        }
    
    async def _analyze_motivation(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Analyze seller motivation indicators"""
        deals = data.get("deals", [])
        analyzed_deals = []
        
        for deal in deals:
            # Analyze motivation indicators
            motivation_score = self._calculate_motivation_score(deal)
            deal["motivation_score"] = motivation_score
            analyzed_deals.append(deal)
        
        return {
            "success": True,
            "analyzed_deals": analyzed_deals
        }
    
    async def _calculate_lead_score(self, deal_data: Dict[str, Any], state: AgentState) -> LeadScore:
        """Calculate comprehensive lead score"""
        
        # Profit potential score (0-10)
        profit_potential = self._score_profit_potential(deal_data)
        
        # Deal feasibility score (0-10)
        deal_feasibility = self._score_deal_feasibility(deal_data)
        
        # Seller motivation score (0-10)
        seller_motivation = self._score_seller_motivation(deal_data)
        
        # Market conditions score (0-10)
        market_conditions = self._score_market_conditions(deal_data, state)
        
        # Calculate overall score (weighted average)
        overall_score = (
            profit_potential * 0.35 +
            deal_feasibility * 0.25 +
            seller_motivation * 0.25 +
            market_conditions * 0.15
        )
        
        # Calculate confidence level
        confidence_level = min(1.0, (
            (profit_potential + deal_feasibility + seller_motivation + market_conditions) / 40.0
        ))
        
        return LeadScore(
            overall_score=round(overall_score, 1),
            profit_potential=round(profit_potential, 1),
            deal_feasibility=round(deal_feasibility, 1),
            seller_motivation=round(seller_motivation, 1),
            market_conditions=round(market_conditions, 1),
            confidence_level=round(confidence_level, 2),
            scoring_factors={
                "profit_weight": 0.35,
                "feasibility_weight": 0.25,
                "motivation_weight": 0.25,
                "market_weight": 0.15
            }
        )
    
    def _score_profit_potential(self, deal_data: Dict[str, Any]) -> float:
        """Score profit potential (0-10)"""
        listing_price = deal_data.get("listing_price", 0)
        estimated_value = deal_data.get("estimated_value", listing_price * 1.1)
        estimated_repair = deal_data.get("estimated_repair_cost", listing_price * 0.1)
        
        if listing_price <= 0:
            return 5.0  # Neutral score for missing data
        
        # Calculate potential profit
        potential_profit = estimated_value - listing_price - estimated_repair
        profit_margin = potential_profit / listing_price if listing_price > 0 else 0
        
        # Score based on profit margin
        if profit_margin >= 0.30:  # 30%+ profit margin
            return 10.0
        elif profit_margin >= 0.20:  # 20-30% profit margin
            return 8.0
        elif profit_margin >= 0.15:  # 15-20% profit margin
            return 7.0
        elif profit_margin >= 0.10:  # 10-15% profit margin
            return 6.0
        elif profit_margin >= 0.05:  # 5-10% profit margin
            return 4.0
        else:  # <5% profit margin
            return 2.0
    
    def _score_deal_feasibility(self, deal_data: Dict[str, Any]) -> float:
        """Score deal feasibility (0-10)"""
        score = 7.0  # Base score
        
        # Adjust based on property type
        property_type = deal_data.get("property_type", "").lower()
        if property_type in ["single_family", "condo"]:
            score += 1.0
        elif property_type in ["multi_family"]:
            score += 0.5
        
        # Adjust based on days on market
        days_on_market = deal_data.get("days_on_market", 30)
        if days_on_market > 90:
            score += 1.0  # Longer on market = more negotiable
        elif days_on_market > 60:
            score += 0.5
        
        # Adjust based on repair estimate
        listing_price = deal_data.get("listing_price", 0)
        repair_cost = deal_data.get("estimated_repair_cost", 0)
        if listing_price > 0:
            repair_ratio = repair_cost / listing_price
            if repair_ratio > 0.25:  # >25% repair costs
                score -= 2.0
            elif repair_ratio > 0.15:  # 15-25% repair costs
                score -= 1.0
        
        return max(0.0, min(10.0, score))
    
    def _score_seller_motivation(self, deal_data: Dict[str, Any]) -> float:
        """Score seller motivation (0-10)"""
        motivation_indicators = deal_data.get("motivation_indicators", [])
        
        # Base score
        score = 5.0
        
        # High motivation indicators
        high_motivation = ["foreclosure", "pre_foreclosure", "divorce", "estate_sale", "job_relocation"]
        medium_motivation = ["vacant", "distressed", "tax_lien", "bankruptcy"]
        
        for indicator in motivation_indicators:
            if indicator.lower() in high_motivation:
                score += 2.0
            elif indicator.lower() in medium_motivation:
                score += 1.0
        
        # Adjust based on days on market
        days_on_market = deal_data.get("days_on_market", 30)
        if days_on_market > 120:
            score += 2.0
        elif days_on_market > 90:
            score += 1.0
        
        return max(0.0, min(10.0, score))
    
    def _score_market_conditions(self, deal_data: Dict[str, Any], state: AgentState) -> float:
        """Score market conditions (0-10)"""
        market_conditions = state.get("market_conditions", {})
        
        # Base score
        score = 6.0
        
        # Adjust based on market temperature
        market_temp = market_conditions.get("market_temperature", "").lower()
        if market_temp == "hot":
            score += 1.0
        elif market_temp == "cold":
            score -= 1.0
        
        # Adjust based on inventory levels
        inventory = market_conditions.get("inventory_level", "").lower()
        if inventory == "low":
            score += 1.0
        elif inventory == "high":
            score -= 1.0
        
        # Adjust based on price trends
        price_trend = market_conditions.get("price_change_yoy", 0)
        if price_trend > 0.05:  # >5% price growth
            score += 1.0
        elif price_trend < -0.05:  # >5% price decline
            score -= 1.0
        
        return max(0.0, min(10.0, score))
    
    def _calculate_motivation_score(self, deal: Dict[str, Any]) -> float:
        """Calculate motivation score for a deal"""
        return self._score_seller_motivation(deal)
    
    def _parse_scanning_results(self, llm_output: str) -> List[Dict[str, Any]]:
        """Parse LLM output into structured deal data"""
        # This is a simplified parser - in production, use structured output
        # or more sophisticated NLP parsing
        
        deals = []
        
        # Sample deals for demonstration
        sample_deals = [
            {
                "property_address": "123 Investment St",
                "city": "Austin",
                "state": "TX", 
                "zip_code": "78701",
                "property_type": "single_family",
                "bedrooms": 3,
                "bathrooms": 2,
                "square_feet": 1500,
                "listing_price": 275000,
                "estimated_value": 320000,
                "estimated_repair_cost": 15000,
                "potential_profit": 30000,
                "days_on_market": 45,
                "motivation_indicators": ["job_relocation", "motivated_seller"],
                "owner_info": {
                    "owner_name": "John Smith",
                    "owner_phone": "(512) 555-0123"
                },
                "tags": ["high_potential", "quick_close"],
                "lead_score": {
                    "overall_score": 8.2,
                    "profit_potential": 8.5,
                    "deal_feasibility": 8.0,
                    "seller_motivation": 8.5,
                    "market_conditions": 7.5,
                    "confidence_level": 0.85
                }
            },
            {
                "property_address": "456 Opportunity Ave",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78702", 
                "property_type": "multi_family",
                "bedrooms": 6,
                "bathrooms": 4,
                "square_feet": 2400,
                "listing_price": 450000,
                "estimated_value": 520000,
                "estimated_repair_cost": 25000,
                "potential_profit": 45000,
                "days_on_market": 75,
                "motivation_indicators": ["estate_sale", "distressed"],
                "owner_info": {
                    "owner_name": "Estate of Mary Johnson",
                    "owner_phone": "(512) 555-0456"
                },
                "tags": ["estate_sale", "duplex", "cash_flow"],
                "lead_score": {
                    "overall_score": 7.8,
                    "profit_potential": 8.0,
                    "deal_feasibility": 7.5,
                    "seller_motivation": 8.5,
                    "market_conditions": 7.0,
                    "confidence_level": 0.80
                }
            }
        ]
        
        return sample_deals
    
    # Public Interface Methods
    
    def update_investment_criteria(self, criteria: InvestmentCriteria):
        """Update investment criteria"""
        self.investment_criteria = criteria
        logger.info("Investment criteria updated")
    
    def add_workflow(self, workflow: ScoutingWorkflow):
        """Add a new scouting workflow"""
        self.active_workflows[workflow.id] = workflow
        logger.info(f"Added scouting workflow: {workflow.name}")
    
    def remove_workflow(self, workflow_id: str):
        """Remove a scouting workflow"""
        if workflow_id in self.active_workflows:
            del self.active_workflows[workflow_id]
            logger.info(f"Removed scouting workflow: {workflow_id}")
    
    def enable_scanning(self):
        """Enable continuous scanning"""
        self.scanning_enabled = True
        logger.info("Continuous scanning enabled")
    
    def disable_scanning(self):
        """Disable continuous scanning"""
        self.scanning_enabled = False
        logger.info("Continuous scanning disabled")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get scout agent performance metrics"""
        return {
            "deals_discovered_today": self.deals_discovered_today,
            "total_deals_discovered": self.total_deals_discovered,
            "average_lead_score": self.average_lead_score,
            "active_workflows": len(self.active_workflows),
            "scanning_enabled": self.scanning_enabled,
            "last_scan_time": self.last_scan_time.isoformat() if self.last_scan_time else None,
            "top_sources": self.top_sources,
            "agent_metrics": self.get_metrics().dict()
        }
    
    def get_discovered_deals(self) -> List[Dict[str, Any]]:
        """Get all discovered deals"""
        return [deal.dict() for deal in self.discovered_deals.values()]
    
    def get_top_deals(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top-scored deals"""
        deals = list(self.discovered_deals.values())
        deals.sort(
            key=lambda x: x.lead_score.overall_score if x.lead_score else 0,
            reverse=True
        )
        return [deal.dict() for deal in deals[:limit]]


# Scout Agent Workflows Implementation

class ScoutWorkflowEngine:
    """Workflow engine for Scout Agent operations"""
    
    def __init__(self, scout_agent: ScoutAgent):
        self.scout_agent = scout_agent
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_history: List[Dict[str, Any]] = []
        self.performance_metrics = {
            "workflows_executed": 0,
            "deals_discovered": 0,
            "average_execution_time": 0.0,
            "success_rate": 0.0,
            "last_optimization": None
        }
    
    async def execute_continuous_scanning_workflow(self, state: AgentState) -> Dict[str, Any]:
        """
        Continuous Scanning Workflow
        - Monitors multiple data sources continuously
        - Applies investment criteria filtering
        - Discovers new opportunities automatically
        - Updates deal pipeline in real-time
        """
        workflow_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        logger.info(f"Starting continuous scanning workflow {workflow_id}")
        
        try:
            # Initialize workflow tracking
            workflow_data = {
                "id": workflow_id,
                "type": "continuous_scanning",
                "status": "running",
                "started_at": start_time,
                "steps_completed": [],
                "current_step": "initialization"
            }
            self.active_workflows[workflow_id] = workflow_data
            
            # Step 1: Check scanning conditions
            workflow_data["current_step"] = "condition_check"
            if not self.scout_agent._should_scan():
                logger.info("Scanning conditions not met, skipping workflow")
                workflow_data["status"] = "skipped"
                workflow_data["reason"] = "scanning_conditions_not_met"
                return {"success": True, "workflow_id": workflow_id, "status": "skipped"}
            
            workflow_data["steps_completed"].append("condition_check")
            
            # Step 2: Prepare scanning parameters
            workflow_data["current_step"] = "parameter_preparation"
            scan_params = await self._prepare_scanning_parameters(state)
            workflow_data["scan_params"] = scan_params
            workflow_data["steps_completed"].append("parameter_preparation")
            
            # Step 3: Execute multi-source scanning
            workflow_data["current_step"] = "multi_source_scanning"
            scan_results = await self._execute_multi_source_scanning(scan_params, state)
            workflow_data["scan_results"] = scan_results
            workflow_data["steps_completed"].append("multi_source_scanning")
            
            # Step 4: Apply investment criteria filtering
            workflow_data["current_step"] = "criteria_filtering"
            filtered_deals = await self._apply_investment_criteria_filtering(
                scan_results.get("raw_properties", []), 
                state
            )
            workflow_data["filtered_deals"] = len(filtered_deals)
            workflow_data["steps_completed"].append("criteria_filtering")
            
            # Step 5: Score and prioritize deals
            workflow_data["current_step"] = "deal_scoring"
            scored_deals = await self._score_and_prioritize_deals(filtered_deals, state)
            workflow_data["scored_deals"] = len(scored_deals)
            workflow_data["steps_completed"].append("deal_scoring")
            
            # Step 6: Update deal pipeline
            workflow_data["current_step"] = "pipeline_update"
            pipeline_update = await self._update_deal_pipeline(scored_deals, state)
            workflow_data["pipeline_update"] = pipeline_update
            workflow_data["steps_completed"].append("pipeline_update")
            
            # Step 7: Generate alerts and notifications
            workflow_data["current_step"] = "alert_generation"
            alerts = await self._generate_deal_alerts(scored_deals, state)
            workflow_data["alerts_generated"] = len(alerts)
            workflow_data["steps_completed"].append("alert_generation")
            
            # Complete workflow
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            workflow_data.update({
                "status": "completed",
                "completed_at": end_time,
                "execution_time": execution_time,
                "deals_discovered": len(scored_deals),
                "high_priority_deals": len([d for d in scored_deals if d.get("lead_score", {}).get("overall_score", 0) >= 8.0])
            })
            
            # Update performance metrics
            self._update_workflow_performance_metrics(workflow_data)
            
            # Archive workflow
            self.workflow_history.append(workflow_data)
            del self.active_workflows[workflow_id]
            
            logger.info(f"Continuous scanning workflow {workflow_id} completed successfully")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "deals_discovered": len(scored_deals),
                "high_priority_deals": workflow_data["high_priority_deals"],
                "execution_time": execution_time,
                "alerts_generated": len(alerts),
                "deals": scored_deals
            }
            
        except Exception as e:
            logger.error(f"Continuous scanning workflow {workflow_id} failed: {e}")
            
            workflow_data.update({
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.now()
            })
            
            self.workflow_history.append(workflow_data)
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
            
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": str(e)
            }
    
    async def execute_deal_evaluation_workflow(self, deals: List[Dict[str, Any]], state: AgentState) -> Dict[str, Any]:
        """
        Deal Evaluation and Scoring Workflow
        - Performs comprehensive analysis of discovered deals
        - Calculates multi-factor lead scores
        - Ranks deals by investment potential
        - Provides detailed scoring rationale
        """
        workflow_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        logger.info(f"Starting deal evaluation workflow {workflow_id} for {len(deals)} deals")
        
        try:
            workflow_data = {
                "id": workflow_id,
                "type": "deal_evaluation",
                "status": "running",
                "started_at": start_time,
                "input_deals": len(deals),
                "steps_completed": [],
                "current_step": "initialization"
            }
            self.active_workflows[workflow_id] = workflow_data
            
            # Step 1: Validate input deals
            workflow_data["current_step"] = "input_validation"
            validated_deals = await self._validate_deal_data(deals)
            workflow_data["validated_deals"] = len(validated_deals)
            workflow_data["steps_completed"].append("input_validation")
            
            # Step 2: Enrich deal data
            workflow_data["current_step"] = "data_enrichment"
            enriched_deals = await self._enrich_deal_data(validated_deals, state)
            workflow_data["enriched_deals"] = len(enriched_deals)
            workflow_data["steps_completed"].append("data_enrichment")
            
            # Step 3: Calculate profit potential scores
            workflow_data["current_step"] = "profit_scoring"
            profit_scored_deals = await self._calculate_profit_potential_scores(enriched_deals, state)
            workflow_data["steps_completed"].append("profit_scoring")
            
            # Step 4: Assess deal feasibility
            workflow_data["current_step"] = "feasibility_assessment"
            feasibility_assessed_deals = await self._assess_deal_feasibility(profit_scored_deals, state)
            workflow_data["steps_completed"].append("feasibility_assessment")
            
            # Step 5: Analyze seller motivation
            workflow_data["current_step"] = "motivation_analysis"
            motivation_analyzed_deals = await self._analyze_seller_motivation(feasibility_assessed_deals, state)
            workflow_data["steps_completed"].append("motivation_analysis")
            
            # Step 6: Evaluate market conditions impact
            workflow_data["current_step"] = "market_evaluation"
            market_evaluated_deals = await self._evaluate_market_conditions_impact(motivation_analyzed_deals, state)
            workflow_data["steps_completed"].append("market_evaluation")
            
            # Step 7: Calculate composite scores
            workflow_data["current_step"] = "composite_scoring"
            final_scored_deals = await self._calculate_composite_scores(market_evaluated_deals, state)
            workflow_data["final_scored_deals"] = len(final_scored_deals)
            workflow_data["steps_completed"].append("composite_scoring")
            
            # Step 8: Rank and prioritize
            workflow_data["current_step"] = "ranking"
            ranked_deals = await self._rank_and_prioritize_deals(final_scored_deals)
            workflow_data["steps_completed"].append("ranking")
            
            # Complete workflow
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Calculate evaluation statistics
            scores = [deal.get("lead_score", {}).get("overall_score", 0) for deal in ranked_deals]
            avg_score = sum(scores) / len(scores) if scores else 0
            high_quality_deals = len([s for s in scores if s >= 7.0])
            
            workflow_data.update({
                "status": "completed",
                "completed_at": end_time,
                "execution_time": execution_time,
                "average_score": avg_score,
                "high_quality_deals": high_quality_deals,
                "score_distribution": self._calculate_score_distribution(scores)
            })
            
            # Update performance metrics
            self._update_workflow_performance_metrics(workflow_data)
            
            # Archive workflow
            self.workflow_history.append(workflow_data)
            del self.active_workflows[workflow_id]
            
            logger.info(f"Deal evaluation workflow {workflow_id} completed successfully")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "evaluated_deals": ranked_deals,
                "average_score": avg_score,
                "high_quality_deals": high_quality_deals,
                "execution_time": execution_time
            }
            
        except Exception as e:
            logger.error(f"Deal evaluation workflow {workflow_id} failed: {e}")
            
            workflow_data.update({
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.now()
            })
            
            self.workflow_history.append(workflow_data)
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
            
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": str(e)
            }
    
    async def execute_lead_qualification_workflow(self, deals: List[Dict[str, Any]], state: AgentState) -> Dict[str, Any]:
        """
        Lead Qualification Workflow
        - Applies qualification criteria to filter leads
        - Verifies contact information and owner details
        - Assesses deal readiness and urgency
        - Categorizes leads by qualification level
        """
        workflow_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        logger.info(f"Starting lead qualification workflow {workflow_id} for {len(deals)} deals")
        
        try:
            workflow_data = {
                "id": workflow_id,
                "type": "lead_qualification",
                "status": "running",
                "started_at": start_time,
                "input_deals": len(deals),
                "steps_completed": [],
                "current_step": "initialization"
            }
            self.active_workflows[workflow_id] = workflow_data
            
            # Step 1: Apply basic qualification criteria
            workflow_data["current_step"] = "basic_qualification"
            basic_qualified = await self._apply_basic_qualification_criteria(deals, state)
            workflow_data["basic_qualified"] = len(basic_qualified)
            workflow_data["steps_completed"].append("basic_qualification")
            
            # Step 2: Verify contact information
            workflow_data["current_step"] = "contact_verification"
            contact_verified = await self._verify_contact_information(basic_qualified, state)
            workflow_data["contact_verified"] = len(contact_verified)
            workflow_data["steps_completed"].append("contact_verification")
            
            # Step 3: Research owner details
            workflow_data["current_step"] = "owner_research"
            owner_researched = await self._research_owner_details(contact_verified, state)
            workflow_data["owner_researched"] = len(owner_researched)
            workflow_data["steps_completed"].append("owner_research")
            
            # Step 4: Assess deal readiness
            workflow_data["current_step"] = "readiness_assessment"
            readiness_assessed = await self._assess_deal_readiness(owner_researched, state)
            workflow_data["steps_completed"].append("readiness_assessment")
            
            # Step 5: Determine urgency levels
            workflow_data["current_step"] = "urgency_determination"
            urgency_determined = await self._determine_urgency_levels(readiness_assessed, state)
            workflow_data["steps_completed"].append("urgency_determination")
            
            # Step 6: Categorize qualification levels
            workflow_data["current_step"] = "qualification_categorization"
            categorized_leads = await self._categorize_qualification_levels(urgency_determined, state)
            workflow_data["steps_completed"].append("qualification_categorization")
            
            # Step 7: Generate qualification reports
            workflow_data["current_step"] = "report_generation"
            qualification_reports = await self._generate_qualification_reports(categorized_leads, state)
            workflow_data["reports_generated"] = len(qualification_reports)
            workflow_data["steps_completed"].append("report_generation")
            
            # Complete workflow
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Calculate qualification statistics
            qualification_stats = self._calculate_qualification_statistics(categorized_leads)
            
            workflow_data.update({
                "status": "completed",
                "completed_at": end_time,
                "execution_time": execution_time,
                "qualification_stats": qualification_stats
            })
            
            # Update performance metrics
            self._update_workflow_performance_metrics(workflow_data)
            
            # Archive workflow
            self.workflow_history.append(workflow_data)
            del self.active_workflows[workflow_id]
            
            logger.info(f"Lead qualification workflow {workflow_id} completed successfully")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "qualified_leads": categorized_leads,
                "qualification_stats": qualification_stats,
                "execution_time": execution_time,
                "reports": qualification_reports
            }
            
        except Exception as e:
            logger.error(f"Lead qualification workflow {workflow_id} failed: {e}")
            
            workflow_data.update({
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.now()
            })
            
            self.workflow_history.append(workflow_data)
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
            
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": str(e)
            }
    
    async def execute_alert_notification_workflow(self, deals: List[Dict[str, Any]], state: AgentState) -> Dict[str, Any]:
        """
        Alert and Notification Workflow
        - Generates alerts for high-priority deals
        - Creates notifications for different stakeholders
        - Manages alert escalation and urgency
        - Tracks notification delivery and responses
        """
        workflow_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        logger.info(f"Starting alert notification workflow {workflow_id} for {len(deals)} deals")
        
        try:
            workflow_data = {
                "id": workflow_id,
                "type": "alert_notification",
                "status": "running",
                "started_at": start_time,
                "input_deals": len(deals),
                "steps_completed": [],
                "current_step": "initialization"
            }
            self.active_workflows[workflow_id] = workflow_data
            
            # Step 1: Identify alert-worthy deals
            workflow_data["current_step"] = "alert_identification"
            alert_worthy_deals = await self._identify_alert_worthy_deals(deals, state)
            workflow_data["alert_worthy_deals"] = len(alert_worthy_deals)
            workflow_data["steps_completed"].append("alert_identification")
            
            # Step 2: Categorize alert types
            workflow_data["current_step"] = "alert_categorization"
            categorized_alerts = await self._categorize_alert_types(alert_worthy_deals, state)
            workflow_data["alert_categories"] = list(categorized_alerts.keys())
            workflow_data["steps_completed"].append("alert_categorization")
            
            # Step 3: Generate alert messages
            workflow_data["current_step"] = "message_generation"
            alert_messages = await self._generate_alert_messages(categorized_alerts, state)
            workflow_data["messages_generated"] = len(alert_messages)
            workflow_data["steps_completed"].append("message_generation")
            
            # Step 4: Determine notification channels
            workflow_data["current_step"] = "channel_determination"
            notification_plan = await self._determine_notification_channels(alert_messages, state)
            workflow_data["notification_channels"] = list(notification_plan.keys())
            workflow_data["steps_completed"].append("channel_determination")
            
            # Step 5: Send notifications
            workflow_data["current_step"] = "notification_sending"
            sent_notifications = await self._send_notifications(notification_plan, state)
            workflow_data["notifications_sent"] = len(sent_notifications)
            workflow_data["steps_completed"].append("notification_sending")
            
            # Step 6: Track delivery status
            workflow_data["current_step"] = "delivery_tracking"
            delivery_status = await self._track_notification_delivery(sent_notifications, state)
            workflow_data["delivery_status"] = delivery_status
            workflow_data["steps_completed"].append("delivery_tracking")
            
            # Step 7: Handle escalations
            workflow_data["current_step"] = "escalation_handling"
            escalations = await self._handle_alert_escalations(alert_messages, delivery_status, state)
            workflow_data["escalations_handled"] = len(escalations)
            workflow_data["steps_completed"].append("escalation_handling")
            
            # Complete workflow
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            workflow_data.update({
                "status": "completed",
                "completed_at": end_time,
                "execution_time": execution_time,
                "total_alerts": len(alert_messages),
                "successful_deliveries": delivery_status.get("successful", 0),
                "failed_deliveries": delivery_status.get("failed", 0)
            })
            
            # Update performance metrics
            self._update_workflow_performance_metrics(workflow_data)
            
            # Archive workflow
            self.workflow_history.append(workflow_data)
            del self.active_workflows[workflow_id]
            
            logger.info(f"Alert notification workflow {workflow_id} completed successfully")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "alerts_generated": len(alert_messages),
                "notifications_sent": len(sent_notifications),
                "delivery_status": delivery_status,
                "execution_time": execution_time
            }
            
        except Exception as e:
            logger.error(f"Alert notification workflow {workflow_id} failed: {e}")
            
            workflow_data.update({
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.now()
            })
            
            self.workflow_history.append(workflow_data)
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
            
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": str(e)
            }
    
    async def execute_performance_monitoring_workflow(self, state: AgentState) -> Dict[str, Any]:
        """
        Performance Monitoring and Optimization Workflow
        - Monitors scout agent performance metrics
        - Analyzes workflow efficiency and success rates
        - Identifies optimization opportunities
        - Implements performance improvements
        """
        workflow_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        logger.info(f"Starting performance monitoring workflow {workflow_id}")
        
        try:
            workflow_data = {
                "id": workflow_id,
                "type": "performance_monitoring",
                "status": "running",
                "started_at": start_time,
                "steps_completed": [],
                "current_step": "initialization"
            }
            self.active_workflows[workflow_id] = workflow_data
            
            # Step 1: Collect performance metrics
            workflow_data["current_step"] = "metrics_collection"
            performance_metrics = await self._collect_performance_metrics(state)
            workflow_data["metrics_collected"] = len(performance_metrics)
            workflow_data["steps_completed"].append("metrics_collection")
            
            # Step 2: Analyze workflow efficiency
            workflow_data["current_step"] = "efficiency_analysis"
            efficiency_analysis = await self._analyze_workflow_efficiency()
            workflow_data["efficiency_score"] = efficiency_analysis.get("overall_score", 0)
            workflow_data["steps_completed"].append("efficiency_analysis")
            
            # Step 3: Identify bottlenecks
            workflow_data["current_step"] = "bottleneck_identification"
            bottlenecks = await self._identify_performance_bottlenecks(efficiency_analysis)
            workflow_data["bottlenecks_found"] = len(bottlenecks)
            workflow_data["steps_completed"].append("bottleneck_identification")
            
            # Step 4: Generate optimization recommendations
            workflow_data["current_step"] = "optimization_recommendations"
            optimizations = await self._generate_optimization_recommendations(bottlenecks, performance_metrics)
            workflow_data["optimizations_recommended"] = len(optimizations)
            workflow_data["steps_completed"].append("optimization_recommendations")
            
            # Step 5: Implement automatic optimizations
            workflow_data["current_step"] = "automatic_optimization"
            implemented_optimizations = await self._implement_automatic_optimizations(optimizations, state)
            workflow_data["optimizations_implemented"] = len(implemented_optimizations)
            workflow_data["steps_completed"].append("automatic_optimization")
            
            # Step 6: Update performance baselines
            workflow_data["current_step"] = "baseline_update"
            updated_baselines = await self._update_performance_baselines(performance_metrics)
            workflow_data["baselines_updated"] = len(updated_baselines)
            workflow_data["steps_completed"].append("baseline_update")
            
            # Step 7: Generate performance report
            workflow_data["current_step"] = "report_generation"
            performance_report = await self._generate_performance_report(
                performance_metrics, efficiency_analysis, optimizations, implemented_optimizations
            )
            workflow_data["steps_completed"].append("report_generation")
            
            # Complete workflow
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            workflow_data.update({
                "status": "completed",
                "completed_at": end_time,
                "execution_time": execution_time,
                "performance_improvement": efficiency_analysis.get("improvement_percentage", 0)
            })
            
            # Update performance metrics
            self._update_workflow_performance_metrics(workflow_data)
            self.performance_metrics["last_optimization"] = end_time.isoformat()
            
            # Archive workflow
            self.workflow_history.append(workflow_data)
            del self.active_workflows[workflow_id]
            
            logger.info(f"Performance monitoring workflow {workflow_id} completed successfully")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "performance_metrics": performance_metrics,
                "efficiency_analysis": efficiency_analysis,
                "optimizations_implemented": implemented_optimizations,
                "performance_report": performance_report,
                "execution_time": execution_time
            }
            
        except Exception as e:
            logger.error(f"Performance monitoring workflow {workflow_id} failed: {e}")
            
            workflow_data.update({
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.now()
            })
            
            self.workflow_history.append(workflow_data)
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
            
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": str(e)
            }
    
    # Supporting Methods for Workflows
    
    async def _prepare_scanning_parameters(self, state: AgentState) -> Dict[str, Any]:
        """Prepare parameters for multi-source scanning"""
        return {
            "geographic_focus": state.get("current_geographic_focus", "national"),
            "investment_criteria": self.scout_agent.investment_criteria.dict(),
            "market_conditions": state.get("market_conditions", {}),
            "target_sources": ["mls", "foreclosures", "public_records", "off_market"],
            "max_results_per_source": 25,
            "min_score_threshold": 6.0
        }
    
    async def _execute_multi_source_scanning(self, params: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute scanning across multiple data sources"""
        try:
            # Use comprehensive deal discovery tool
            from .scout_tools import scout_tool_manager
            
            if scout_tool_manager:
                result = await scout_tool_manager.execute_tool(
                    "comprehensive_deal_discovery",
                    location=params.get("geographic_focus", ""),
                    criteria=params.get("investment_criteria", {}),
                    include_sources=params.get("target_sources", []),
                    max_results=params.get("max_results_per_source", 25) * len(params.get("target_sources", [])),
                    min_score=params.get("min_score_threshold", 6.0)
                )
                
                if result.get("success", False):
                    return {
                        "raw_properties": result["result"].get("properties", []),
                        "total_scanned": result["result"].get("total_found", 0),
                        "sources_used": result["result"].get("source_results", {})
                    }
            
            # Fallback to individual tool calls
            return await self._fallback_multi_source_scanning(params, state)
            
        except Exception as e:
            logger.error(f"Multi-source scanning failed: {e}")
            return {"raw_properties": [], "total_scanned": 0, "sources_used": {}}
    
    async def _fallback_multi_source_scanning(self, params: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Fallback scanning method using individual tools"""
        all_properties = []
        sources_used = {}
        
        # Simulate scanning results for demonstration
        sample_properties = [
            {
                "id": str(uuid.uuid4()),
                "address": f"{100 + i * 10} Sample St",
                "city": "Austin",
                "state": "TX",
                "zip_code": f"787{i:02d}",
                "property_type": "single_family",
                "bedrooms": 3 + (i % 2),
                "bathrooms": 2.0 + (i % 2) * 0.5,
                "square_feet": 1500 + i * 100,
                "listing_price": 250000 + i * 25000,
                "days_on_market": 15 + i * 10,
                "source": ["mls", "foreclosures", "off_market"][i % 3],
                "motivation_indicators": [["job_relocation"], ["foreclosure"], ["estate_sale"]][i % 3]
            }
            for i in range(15)
        ]
        
        all_properties.extend(sample_properties)
        sources_used = {"mls": 5, "foreclosures": 5, "off_market": 5}
        
        return {
            "raw_properties": all_properties,
            "total_scanned": len(all_properties),
            "sources_used": sources_used
        }
    
    async def _apply_investment_criteria_filtering(self, properties: List[Dict[str, Any]], state: AgentState) -> List[Dict[str, Any]]:
        """Apply investment criteria to filter properties"""
        filtered_properties = []
        criteria = self.scout_agent.investment_criteria
        
        for prop in properties:
            # Apply price filters
            if criteria.max_price and prop.get("listing_price", 0) > criteria.max_price:
                continue
            if criteria.min_price and prop.get("listing_price", 0) < criteria.min_price:
                continue
            
            # Apply property type filter
            if criteria.property_types and prop.get("property_type") not in criteria.property_types:
                continue
            
            # Apply bedroom filters
            if criteria.min_bedrooms and prop.get("bedrooms", 0) < criteria.min_bedrooms:
                continue
            if criteria.max_bedrooms and prop.get("bedrooms", 0) > criteria.max_bedrooms:
                continue
            
            # Apply days on market filter
            if criteria.max_days_on_market and prop.get("days_on_market", 0) > criteria.max_days_on_market:
                continue
            
            filtered_properties.append(prop)
        
        return filtered_properties
    
    async def _score_and_prioritize_deals(self, deals: List[Dict[str, Any]], state: AgentState) -> List[Dict[str, Any]]:
        """Score and prioritize deals based on investment potential"""
        scored_deals = []
        
        for deal in deals:
            # Calculate comprehensive lead score
            lead_score = await self.scout_agent._calculate_lead_score(deal, state)
            deal["lead_score"] = lead_score.dict()
            scored_deals.append(deal)
        
        # Sort by overall score (highest first)
        scored_deals.sort(key=lambda x: x["lead_score"]["overall_score"], reverse=True)
        
        return scored_deals
    
    async def _update_deal_pipeline(self, deals: List[Dict[str, Any]], state: AgentState) -> Dict[str, Any]:
        """Update the deal pipeline with new deals"""
        new_deals_added = 0
        updated_deals = 0
        
        for deal_data in deals:
            # Check if deal already exists
            existing_deal = None
            for existing in state.get("current_deals", []):
                if (existing.get("property_address") == deal_data.get("address") and
                    existing.get("city") == deal_data.get("city")):
                    existing_deal = existing
                    break
            
            if existing_deal:
                # Update existing deal
                existing_deal.update({
                    "last_updated": datetime.now().isoformat(),
                    "lead_score": deal_data.get("lead_score", {}),
                    "tags": deal_data.get("tags", [])
                })
                updated_deals += 1
            else:
                # Add new deal
                new_deal = Deal(
                    property_address=deal_data.get("address", "Unknown"),
                    city=deal_data.get("city", "Unknown"),
                    state=deal_data.get("state", "Unknown"),
                    zip_code=deal_data.get("zip_code", "Unknown"),
                    property_type=deal_data.get("property_type"),
                    bedrooms=deal_data.get("bedrooms"),
                    bathrooms=deal_data.get("bathrooms"),
                    square_feet=deal_data.get("square_feet"),
                    listing_price=deal_data.get("listing_price"),
                    estimated_value=deal_data.get("estimated_value"),
                    potential_profit=deal_data.get("potential_profit"),
                    source=deal_data.get("source", "scout_agent"),
                    motivation_indicators=deal_data.get("motivation_indicators", []),
                    tags=deal_data.get("tags", [])
                )
                
                state = StateManager.add_deal(state, new_deal)
                new_deals_added += 1
        
        return {
            "new_deals_added": new_deals_added,
            "updated_deals": updated_deals,
            "total_pipeline_deals": len(state.get("current_deals", []))
        }
    
    async def _generate_deal_alerts(self, deals: List[Dict[str, Any]], state: AgentState) -> List[Dict[str, Any]]:
        """Generate alerts for high-priority deals"""
        alerts = []
        
        for deal in deals:
            lead_score = deal.get("lead_score", {})
            overall_score = lead_score.get("overall_score", 0)
            
            # Generate alerts for high-scoring deals
            if overall_score >= 8.5:
                alerts.append({
                    "id": str(uuid.uuid4()),
                    "type": "high_priority_deal",
                    "priority": "critical",
                    "deal_id": deal.get("id"),
                    "message": f"Exceptional deal discovered: {deal.get('address')} - Score: {overall_score:.1f}",
                    "data": deal,
                    "created_at": datetime.now().isoformat()
                })
            elif overall_score >= 7.5:
                alerts.append({
                    "id": str(uuid.uuid4()),
                    "type": "good_deal",
                    "priority": "high",
                    "deal_id": deal.get("id"),
                    "message": f"Good deal opportunity: {deal.get('address')} - Score: {overall_score:.1f}",
                    "data": deal,
                    "created_at": datetime.now().isoformat()
                })
        
        return alerts
    
    async def _validate_deal_data(self, deals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate deal data for completeness and accuracy"""
        validated_deals = []
        
        for deal in deals:
            # Check required fields
            if not deal.get("address") or not deal.get("city") or not deal.get("state"):
                continue
            
            # Validate numeric fields
            if deal.get("listing_price") and deal["listing_price"] <= 0:
                continue
            
            # Add validation score
            deal["validation_score"] = 0.9  # Simplified validation
            validated_deals.append(deal)
        
        return validated_deals
    
    async def _enrich_deal_data(self, deals: List[Dict[str, Any]], state: AgentState) -> List[Dict[str, Any]]:
        """Enrich deal data with additional information"""
        enriched_deals = []
        
        for deal in deals:
            # Add market context
            deal["market_context"] = state.get("market_conditions", {})
            
            # Add neighborhood data (simulated)
            deal["neighborhood_data"] = {
                "school_rating": 7.5,
                "crime_score": 6.0,
                "walkability": 8.0,
                "appreciation_trend": "positive"
            }
            
            # Add comparable properties (simulated)
            deal["comparable_properties"] = [
                {
                    "address": f"Comp {i} Street",
                    "sale_price": deal.get("listing_price", 250000) + (i * 10000),
                    "sale_date": "2024-01-15",
                    "similarity_score": 0.85 - (i * 0.1)
                }
                for i in range(3)
            ]
            
            enriched_deals.append(deal)
        
        return enriched_deals
    
    async def _calculate_profit_potential_scores(self, deals: List[Dict[str, Any]], state: AgentState) -> List[Dict[str, Any]]:
        """Calculate profit potential scores for deals"""
        for deal in deals:
            listing_price = deal.get("listing_price", 0)
            estimated_value = deal.get("estimated_value", listing_price * 1.1)
            repair_cost = deal.get("estimated_repair_cost", listing_price * 0.1)
            
            # Calculate potential profit
            potential_profit = estimated_value - listing_price - repair_cost
            profit_margin = potential_profit / listing_price if listing_price > 0 else 0
            
            # Score profit potential (0-10)
            if profit_margin >= 0.3:  # 30%+ margin
                profit_score = 10.0
            elif profit_margin >= 0.2:  # 20-30% margin
                profit_score = 8.0
            elif profit_margin >= 0.15:  # 15-20% margin
                profit_score = 6.0
            elif profit_margin >= 0.1:  # 10-15% margin
                profit_score = 4.0
            else:
                profit_score = 2.0
            
            deal["profit_potential_score"] = profit_score
            deal["potential_profit"] = potential_profit
            deal["profit_margin"] = profit_margin
        
        return deals
    
    async def _assess_deal_feasibility(self, deals: List[Dict[str, Any]], state: AgentState) -> List[Dict[str, Any]]:
        """Assess deal feasibility"""
        for deal in deals:
            # Factors affecting feasibility
            listing_price = deal.get("listing_price", 0)
            repair_cost = deal.get("estimated_repair_cost", 0)
            days_on_market = deal.get("days_on_market", 30)
            
            # Calculate feasibility score (0-10)
            feasibility_score = 7.0  # Base score
            
            # Adjust for financing difficulty
            if listing_price > 500000:
                feasibility_score -= 1.0
            elif listing_price < 100000:
                feasibility_score -= 0.5
            
            # Adjust for repair complexity
            if repair_cost > 50000:
                feasibility_score -= 1.5
            elif repair_cost > 25000:
                feasibility_score -= 0.5
            
            # Adjust for market timing
            if days_on_market > 90:
                feasibility_score += 1.0  # Easier to negotiate
            elif days_on_market < 7:
                feasibility_score -= 0.5  # Competitive market
            
            deal["feasibility_score"] = max(0.0, min(10.0, feasibility_score))
        
        return deals
    
    async def _analyze_seller_motivation(self, deals: List[Dict[str, Any]], state: AgentState) -> List[Dict[str, Any]]:
        """Analyze seller motivation indicators"""
        for deal in deals:
            motivation_indicators = deal.get("motivation_indicators", [])
            
            # Calculate motivation score
            motivation_score = self.scout_agent._calculate_motivation_score(deal)
            deal["seller_motivation_score"] = motivation_score
            
            # Add motivation analysis
            deal["motivation_analysis"] = {
                "indicators": motivation_indicators,
                "urgency_level": "high" if motivation_score >= 8.0 else "medium" if motivation_score >= 6.0 else "low",
                "negotiation_leverage": "high" if motivation_score >= 7.0 else "medium" if motivation_score >= 5.0 else "low"
            }
        
        return deals
    
    async def _evaluate_market_conditions_impact(self, deals: List[Dict[str, Any]], state: AgentState) -> List[Dict[str, Any]]:
        """Evaluate market conditions impact on deals"""
        market_conditions = state.get("market_conditions", {})
        
        for deal in deals:
            # Calculate market conditions score
            market_score = self.scout_agent._score_market_conditions(deal, state)
            deal["market_conditions_score"] = market_score
            
            # Add market impact analysis
            deal["market_impact"] = {
                "market_temperature": market_conditions.get("market_temperature", "warm"),
                "inventory_level": market_conditions.get("inventory_level", "normal"),
                "price_trend": market_conditions.get("price_change_yoy", 0),
                "competition_level": "high" if market_score < 6.0 else "medium" if market_score < 8.0 else "low"
            }
        
        return deals
    
    async def _calculate_composite_scores(self, deals: List[Dict[str, Any]], state: AgentState) -> List[Dict[str, Any]]:
        """Calculate composite lead scores"""
        for deal in deals:
            profit_score = deal.get("profit_potential_score", 5.0)
            feasibility_score = deal.get("feasibility_score", 5.0)
            motivation_score = deal.get("seller_motivation_score", 5.0)
            market_score = deal.get("market_conditions_score", 5.0)
            
            # Weighted composite score
            overall_score = (
                profit_score * 0.35 +
                feasibility_score * 0.25 +
                motivation_score * 0.25 +
                market_score * 0.15
            )
            
            # Calculate confidence level
            score_variance = abs(profit_score - feasibility_score) + abs(motivation_score - market_score)
            confidence_level = max(0.5, 1.0 - (score_variance / 20.0))
            
            deal["lead_score"] = {
                "overall_score": round(overall_score, 1),
                "profit_potential": profit_score,
                "deal_feasibility": feasibility_score,
                "seller_motivation": motivation_score,
                "market_conditions": market_score,
                "confidence_level": round(confidence_level, 2)
            }
        
        return deals
    
    async def _rank_and_prioritize_deals(self, deals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank and prioritize deals by overall score"""
        # Sort by overall score (highest first)
        ranked_deals = sorted(
            deals,
            key=lambda x: x.get("lead_score", {}).get("overall_score", 0),
            reverse=True
        )
        
        # Add ranking information
        for i, deal in enumerate(ranked_deals):
            deal["rank"] = i + 1
            deal["priority_level"] = (
                "critical" if deal.get("lead_score", {}).get("overall_score", 0) >= 8.5 else
                "high" if deal.get("lead_score", {}).get("overall_score", 0) >= 7.5 else
                "medium" if deal.get("lead_score", {}).get("overall_score", 0) >= 6.5 else
                "low"
            )
        
        return ranked_deals
    
    def _calculate_score_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate score distribution statistics"""
        if not scores:
            return {}
        
        return {
            "excellent": len([s for s in scores if s >= 8.5]),
            "good": len([s for s in scores if 7.5 <= s < 8.5]),
            "fair": len([s for s in scores if 6.5 <= s < 7.5]),
            "poor": len([s for s in scores if s < 6.5])
        }
    
    # Additional workflow support methods would continue here...
    # For brevity, I'll implement key methods and indicate where others would go
    
    async def _apply_basic_qualification_criteria(self, deals: List[Dict[str, Any]], state: AgentState) -> List[Dict[str, Any]]:
        """Apply basic qualification criteria"""
        qualified_deals = []
        
        for deal in deals:
            # Basic qualification checks
            if (deal.get("lead_score", {}).get("overall_score", 0) >= 6.0 and
                deal.get("listing_price", 0) > 0 and
                deal.get("address")):
                qualified_deals.append(deal)
        
        return qualified_deals
    
    async def _verify_contact_information(self, deals: List[Dict[str, Any]], state: AgentState) -> List[Dict[str, Any]]:
        """Verify contact information for deals"""
        # Simulate contact verification
        for deal in deals:
            deal["contact_verified"] = True
            deal["contact_confidence"] = 0.85
        
        return deals
    
    async def _research_owner_details(self, deals: List[Dict[str, Any]], state: AgentState) -> List[Dict[str, Any]]:
        """Research owner details"""
        # Simulate owner research
        for deal in deals:
            deal["owner_research"] = {
                "owner_name": f"Owner of {deal.get('address', 'Unknown')}",
                "ownership_duration": "5 years",
                "motivation_factors": deal.get("motivation_indicators", [])
            }
        
        return deals
    
    def _update_workflow_performance_metrics(self, workflow_data: Dict[str, Any]):
        """Update workflow performance metrics"""
        self.performance_metrics["workflows_executed"] += 1
        
        if workflow_data.get("status") == "completed":
            execution_time = workflow_data.get("execution_time", 0)
            current_avg = self.performance_metrics["average_execution_time"]
            total_workflows = self.performance_metrics["workflows_executed"]
            
            # Update rolling average
            self.performance_metrics["average_execution_time"] = (
                (current_avg * (total_workflows - 1) + execution_time) / total_workflows
            )
            
            # Update success rate
            successful_workflows = len([w for w in self.workflow_history if w.get("status") == "completed"])
            self.performance_metrics["success_rate"] = successful_workflows / total_workflows
            
            # Update deals discovered
            deals_discovered = workflow_data.get("deals_discovered", 0)
            self.performance_metrics["deals_discovered"] += deals_discovered
    
    # Additional workflow support methods
    
    async def _assess_deal_readiness(self, deals: List[Dict[str, Any]], state: AgentState) -> List[Dict[str, Any]]:
        """Assess deal readiness for outreach"""
        for deal in deals:
            readiness_factors = {
                "contact_verified": deal.get("contact_verified", False),
                "owner_research_complete": bool(deal.get("owner_research")),
                "motivation_analyzed": bool(deal.get("motivation_analysis")),
                "financial_analysis_complete": bool(deal.get("lead_score"))
            }
            
            readiness_score = sum(readiness_factors.values()) / len(readiness_factors)
            
            deal["readiness_assessment"] = {
                "readiness_score": readiness_score,
                "readiness_level": "ready" if readiness_score >= 0.8 else "partial" if readiness_score >= 0.6 else "not_ready",
                "missing_factors": [k for k, v in readiness_factors.items() if not v]
            }
        
        return deals
    
    async def _determine_urgency_levels(self, deals: List[Dict[str, Any]], state: AgentState) -> List[Dict[str, Any]]:
        """Determine urgency levels for deals"""
        for deal in deals:
            urgency_factors = {
                "high_motivation": deal.get("seller_motivation_score", 0) >= 8.0,
                "time_sensitive": deal.get("days_on_market", 0) > 90,
                "high_profit": deal.get("profit_potential_score", 0) >= 8.0,
                "market_opportunity": deal.get("market_conditions_score", 0) >= 7.0
            }
            
            urgency_score = sum(urgency_factors.values())
            
            if urgency_score >= 3:
                urgency_level = "critical"
            elif urgency_score >= 2:
                urgency_level = "high"
            elif urgency_score >= 1:
                urgency_level = "medium"
            else:
                urgency_level = "low"
            
            deal["urgency_assessment"] = {
                "urgency_level": urgency_level,
                "urgency_score": urgency_score,
                "urgency_factors": urgency_factors
            }
        
        return deals
    
    async def _categorize_qualification_levels(self, deals: List[Dict[str, Any]], state: AgentState) -> List[Dict[str, Any]]:
        """Categorize deals by qualification level"""
        for deal in deals:
            overall_score = deal.get("lead_score", {}).get("overall_score", 0)
            readiness_level = deal.get("readiness_assessment", {}).get("readiness_level", "not_ready")
            urgency_level = deal.get("urgency_assessment", {}).get("urgency_level", "low")
            
            # Determine qualification category
            if overall_score >= 8.0 and readiness_level == "ready" and urgency_level in ["critical", "high"]:
                qualification_category = "hot_lead"
            elif overall_score >= 7.0 and readiness_level in ["ready", "partial"]:
                qualification_category = "warm_lead"
            elif overall_score >= 6.0:
                qualification_category = "cold_lead"
            else:
                qualification_category = "unqualified"
            
            deal["qualification"] = {
                "category": qualification_category,
                "priority": 1 if qualification_category == "hot_lead" else 2 if qualification_category == "warm_lead" else 3,
                "recommended_action": self._get_recommended_action(qualification_category, urgency_level)
            }
        
        return deals
    
    def _get_recommended_action(self, category: str, urgency: str) -> str:
        """Get recommended action based on qualification category and urgency"""
        if category == "hot_lead":
            return "immediate_outreach" if urgency == "critical" else "priority_outreach"
        elif category == "warm_lead":
            return "scheduled_outreach"
        elif category == "cold_lead":
            return "nurture_campaign"
        else:
            return "disqualify"
    
    async def _generate_qualification_reports(self, deals: List[Dict[str, Any]], state: AgentState) -> List[Dict[str, Any]]:
        """Generate qualification reports for deals"""
        reports = []
        
        # Group deals by qualification category
        categories = {}
        for deal in deals:
            category = deal.get("qualification", {}).get("category", "unqualified")
            if category not in categories:
                categories[category] = []
            categories[category].append(deal)
        
        # Generate summary report
        summary_report = {
            "id": str(uuid.uuid4()),
            "type": "qualification_summary",
            "timestamp": datetime.now().isoformat(),
            "total_deals": len(deals),
            "category_breakdown": {cat: len(deals_list) for cat, deals_list in categories.items()},
            "recommendations": self._generate_qualification_recommendations(categories)
        }
        reports.append(summary_report)
        
        return reports
    
    def _generate_qualification_recommendations(self, categories: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Generate qualification recommendations"""
        recommendations = []
        
        hot_leads = len(categories.get("hot_lead", []))
        warm_leads = len(categories.get("warm_lead", []))
        
        if hot_leads > 0:
            recommendations.append(f"Prioritize immediate outreach to {hot_leads} hot leads")
        
        if warm_leads > 5:
            recommendations.append(f"Schedule systematic outreach campaign for {warm_leads} warm leads")
        
        return recommendations
    
    def _calculate_qualification_statistics(self, deals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate qualification statistics"""
        if not deals:
            return {}
        
        categories = {}
        urgency_levels = {}
        readiness_levels = {}
        
        for deal in deals:
            # Count categories
            category = deal.get("qualification", {}).get("category", "unqualified")
            categories[category] = categories.get(category, 0) + 1
            
            # Count urgency levels
            urgency = deal.get("urgency_assessment", {}).get("urgency_level", "low")
            urgency_levels[urgency] = urgency_levels.get(urgency, 0) + 1
            
            # Count readiness levels
            readiness = deal.get("readiness_assessment", {}).get("readiness_level", "not_ready")
            readiness_levels[readiness] = readiness_levels.get(readiness, 0) + 1
        
        return {
            "total_deals": len(deals),
            "qualification_categories": categories,
            "urgency_distribution": urgency_levels,
            "readiness_distribution": readiness_levels,
            "qualification_rate": (categories.get("hot_lead", 0) + categories.get("warm_lead", 0)) / len(deals)
        }
    
    # Alert notification workflow methods
    
    async def _identify_alert_worthy_deals(self, deals: List[Dict[str, Any]], state: AgentState) -> List[Dict[str, Any]]:
        """Identify deals worthy of alerts"""
        alert_worthy = []
        
        for deal in deals:
            overall_score = deal.get("lead_score", {}).get("overall_score", 0)
            urgency_level = deal.get("urgency_assessment", {}).get("urgency_level", "low")
            qualification_category = deal.get("qualification", {}).get("category", "unqualified")
            
            # Criteria for alert-worthy deals
            if (overall_score >= 8.0 or 
                urgency_level == "critical" or 
                qualification_category == "hot_lead"):
                alert_worthy.append(deal)
        
        return alert_worthy
    
    async def _categorize_alert_types(self, deals: List[Dict[str, Any]], state: AgentState) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize alerts by type"""
        categories = {
            "high_score_deals": [],
            "urgent_deals": [],
            "hot_leads": [],
            "market_opportunities": []
        }
        
        for deal in deals:
            overall_score = deal.get("lead_score", {}).get("overall_score", 0)
            urgency_level = deal.get("urgency_assessment", {}).get("urgency_level", "low")
            qualification_category = deal.get("qualification", {}).get("category", "unqualified")
            market_score = deal.get("market_conditions_score", 0)
            
            if overall_score >= 8.5:
                categories["high_score_deals"].append(deal)
            
            if urgency_level == "critical":
                categories["urgent_deals"].append(deal)
            
            if qualification_category == "hot_lead":
                categories["hot_leads"].append(deal)
            
            if market_score >= 8.0:
                categories["market_opportunities"].append(deal)
        
        return categories
    
    async def _generate_alert_messages(self, categorized_alerts: Dict[str, List[Dict[str, Any]]], state: AgentState) -> List[Dict[str, Any]]:
        """Generate alert messages"""
        messages = []
        
        for category, deals in categorized_alerts.items():
            if not deals:
                continue
            
            for deal in deals:
                message = {
                    "id": str(uuid.uuid4()),
                    "category": category,
                    "deal_id": deal.get("id"),
                    "priority": self._get_alert_priority(category),
                    "title": self._get_alert_title(category, deal),
                    "message": self._get_alert_message(category, deal),
                    "data": deal,
                    "created_at": datetime.now().isoformat(),
                    "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
                }
                messages.append(message)
        
        return messages
    
    def _get_alert_priority(self, category: str) -> str:
        """Get alert priority based on category"""
        priority_map = {
            "high_score_deals": "critical",
            "urgent_deals": "critical",
            "hot_leads": "high",
            "market_opportunities": "medium"
        }
        return priority_map.get(category, "low")
    
    def _get_alert_title(self, category: str, deal: Dict[str, Any]) -> str:
        """Get alert title"""
        address = deal.get("address", "Unknown Address")
        score = deal.get("lead_score", {}).get("overall_score", 0)
        
        title_map = {
            "high_score_deals": f"Exceptional Deal Alert: {address} (Score: {score:.1f})",
            "urgent_deals": f"Urgent Deal Alert: {address}",
            "hot_leads": f"Hot Lead Alert: {address}",
            "market_opportunities": f"Market Opportunity: {address}"
        }
        return title_map.get(category, f"Deal Alert: {address}")
    
    def _get_alert_message(self, category: str, deal: Dict[str, Any]) -> str:
        """Get alert message content"""
        address = deal.get("address", "Unknown")
        price = deal.get("listing_price", 0)
        profit = deal.get("potential_profit", 0)
        
        message_map = {
            "high_score_deals": f"Exceptional investment opportunity at {address}. Listed at ${price:,.0f} with potential profit of ${profit:,.0f}. Immediate action recommended.",
            "urgent_deals": f"Time-sensitive opportunity at {address}. High seller motivation detected. Contact immediately.",
            "hot_leads": f"Qualified hot lead at {address}. All criteria met for immediate outreach.",
            "market_opportunities": f"Strong market opportunity at {address}. Favorable market conditions detected."
        }
        return message_map.get(category, f"New deal opportunity at {address}")
    
    async def _determine_notification_channels(self, messages: List[Dict[str, Any]], state: AgentState) -> Dict[str, List[Dict[str, Any]]]:
        """Determine notification channels for messages"""
        channels = {
            "email": [],
            "sms": [],
            "dashboard": [],
            "slack": []
        }
        
        for message in messages:
            priority = message.get("priority", "low")
            
            # All messages go to dashboard
            channels["dashboard"].append(message)
            
            # High priority messages go to multiple channels
            if priority in ["critical", "high"]:
                channels["email"].append(message)
                channels["sms"].append(message)
                channels["slack"].append(message)
            elif priority == "medium":
                channels["email"].append(message)
                channels["slack"].append(message)
        
        return channels
    
    async def _send_notifications(self, notification_plan: Dict[str, List[Dict[str, Any]]], state: AgentState) -> List[Dict[str, Any]]:
        """Send notifications through various channels"""
        sent_notifications = []
        
        for channel, messages in notification_plan.items():
            for message in messages:
                # Simulate sending notification
                notification = {
                    "id": str(uuid.uuid4()),
                    "channel": channel,
                    "message_id": message["id"],
                    "status": "sent",
                    "sent_at": datetime.now().isoformat(),
                    "recipient": "user@example.com" if channel == "email" else "+1234567890" if channel == "sms" else "dashboard"
                }
                sent_notifications.append(notification)
        
        return sent_notifications
    
    async def _track_notification_delivery(self, notifications: List[Dict[str, Any]], state: AgentState) -> Dict[str, Any]:
        """Track notification delivery status"""
        # Simulate delivery tracking
        successful = len([n for n in notifications if n.get("status") == "sent"])
        failed = len(notifications) - successful
        
        return {
            "total_sent": len(notifications),
            "successful": successful,
            "failed": failed,
            "delivery_rate": successful / len(notifications) if notifications else 0
        }
    
    async def _handle_alert_escalations(self, messages: List[Dict[str, Any]], delivery_status: Dict[str, Any], state: AgentState) -> List[Dict[str, Any]]:
        """Handle alert escalations"""
        escalations = []
        
        # Escalate critical alerts that may have failed delivery
        critical_messages = [m for m in messages if m.get("priority") == "critical"]
        
        for message in critical_messages:
            escalation = {
                "id": str(uuid.uuid4()),
                "original_message_id": message["id"],
                "escalation_reason": "critical_priority",
                "escalated_at": datetime.now().isoformat(),
                "escalation_action": "human_notification"
            }
            escalations.append(escalation)
        
        return escalations
    
    # Performance monitoring workflow methods
    
    async def _collect_performance_metrics(self, state: AgentState) -> Dict[str, Any]:
        """Collect performance metrics"""
        return {
            "workflow_metrics": self.performance_metrics,
            "deal_discovery_rate": len(state.get("current_deals", [])),
            "average_deal_score": self._calculate_average_deal_score(state),
            "qualification_rate": self._calculate_qualification_rate(state),
            "alert_generation_rate": self._calculate_alert_generation_rate(),
            "system_uptime": 99.5,  # Simulated
            "error_rate": 0.02  # Simulated
        }
    
    def _calculate_average_deal_score(self, state: AgentState) -> float:
        """Calculate average deal score"""
        deals = state.get("current_deals", [])
        if not deals:
            return 0.0
        
        scores = []
        for deal in deals:
            if isinstance(deal, dict) and "analysis_data" in deal:
                score = deal.get("analysis_data", {}).get("lead_score", {}).get("overall_score", 0)
                scores.append(score)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _calculate_qualification_rate(self, state: AgentState) -> float:
        """Calculate qualification rate"""
        deals = state.get("current_deals", [])
        if not deals:
            return 0.0
        
        qualified_deals = len([d for d in deals if d.get("status") in ["analyzed", "approved"]])
        return qualified_deals / len(deals)
    
    def _calculate_alert_generation_rate(self) -> float:
        """Calculate alert generation rate"""
        # Simulate alert generation rate calculation
        return 0.15  # 15% of deals generate alerts
    
    async def _analyze_workflow_efficiency(self) -> Dict[str, Any]:
        """Analyze workflow efficiency"""
        if not self.workflow_history:
            return {
                "overall_score": 7.0, 
                "improvement_percentage": 0,
                "average_execution_time": 0,
                "success_rate": 1.0
            }
        
        # Calculate efficiency metrics
        completed_workflows = [w for w in self.workflow_history if w.get("status") == "completed"]
        
        if not completed_workflows:
            return {
                "overall_score": 5.0, 
                "improvement_percentage": 0,
                "average_execution_time": 0,
                "success_rate": 0.0
            }
        
        avg_execution_time = sum(w.get("execution_time", 0) for w in completed_workflows) / len(completed_workflows)
        success_rate = len(completed_workflows) / len(self.workflow_history)
        
        # Calculate overall efficiency score
        time_score = max(0, 10 - (avg_execution_time / 60))  # Penalize long execution times
        success_score = success_rate * 10
        
        overall_score = (time_score + success_score) / 2
        
        return {
            "overall_score": overall_score,
            "average_execution_time": avg_execution_time,
            "success_rate": success_rate,
            "improvement_percentage": 5.0  # Simulated improvement
        }
    
    async def _identify_performance_bottlenecks(self, efficiency_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        # Analyze execution times
        if efficiency_analysis.get("average_execution_time", 0) > 300:  # 5 minutes
            bottlenecks.append({
                "type": "execution_time",
                "severity": "high",
                "description": "Workflow execution times are too long",
                "recommendation": "Optimize data source queries and parallel processing"
            })
        
        # Analyze success rate
        if efficiency_analysis.get("success_rate", 1.0) < 0.9:
            bottlenecks.append({
                "type": "success_rate",
                "severity": "medium",
                "description": "Workflow success rate is below target",
                "recommendation": "Improve error handling and retry mechanisms"
            })
        
        return bottlenecks
    
    async def _generate_optimization_recommendations(self, bottlenecks: List[Dict[str, Any]], metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization recommendations"""
        recommendations = []
        
        for bottleneck in bottlenecks:
            recommendation = {
                "id": str(uuid.uuid4()),
                "bottleneck_type": bottleneck["type"],
                "priority": bottleneck["severity"],
                "recommendation": bottleneck["recommendation"],
                "estimated_impact": "medium",
                "implementation_effort": "low"
            }
            recommendations.append(recommendation)
        
        # Add general optimization recommendations
        if metrics.get("deal_discovery_rate", 0) < 10:
            recommendations.append({
                "id": str(uuid.uuid4()),
                "bottleneck_type": "discovery_rate",
                "priority": "medium",
                "recommendation": "Expand data source coverage and scanning frequency",
                "estimated_impact": "high",
                "implementation_effort": "medium"
            })
        
        return recommendations
    
    async def _implement_automatic_optimizations(self, optimizations: List[Dict[str, Any]], state: AgentState) -> List[Dict[str, Any]]:
        """Implement automatic optimizations"""
        implemented = []
        
        for optimization in optimizations:
            if optimization.get("implementation_effort") == "low":
                # Simulate implementing low-effort optimizations
                implementation = {
                    "optimization_id": optimization["id"],
                    "status": "implemented",
                    "implemented_at": datetime.now().isoformat(),
                    "description": f"Implemented: {optimization['recommendation']}"
                }
                implemented.append(implementation)
        
        return implemented
    
    async def _update_performance_baselines(self, metrics: Dict[str, Any]) -> List[str]:
        """Update performance baselines"""
        updated_baselines = []
        
        # Update workflow execution time baseline
        if "workflow_metrics" in metrics:
            self.performance_metrics["average_execution_time"] = metrics["workflow_metrics"].get("average_execution_time", 0)
            updated_baselines.append("execution_time")
        
        # Update success rate baseline
        if "workflow_metrics" in metrics:
            self.performance_metrics["success_rate"] = metrics["workflow_metrics"].get("success_rate", 0)
            updated_baselines.append("success_rate")
        
        return updated_baselines
    
    async def _generate_performance_report(self, metrics: Dict[str, Any], efficiency: Dict[str, Any], 
                                         optimizations: List[Dict[str, Any]], implemented: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate performance report"""
        return {
            "id": str(uuid.uuid4()),
            "report_type": "scout_performance",
            "generated_at": datetime.now().isoformat(),
            "metrics_summary": metrics,
            "efficiency_analysis": efficiency,
            "optimization_recommendations": len(optimizations),
            "optimizations_implemented": len(implemented),
            "overall_health_score": efficiency.get("overall_score", 7.0),
            "key_insights": [
                f"Workflow success rate: {efficiency.get('success_rate', 0):.1%}",
                f"Average execution time: {efficiency.get('average_execution_time', 0):.1f} seconds",
                f"Optimizations implemented: {len(implemented)}"
            ]
        }


# Add workflow engine to ScoutAgent
def add_workflow_engine_to_scout_agent():
    """Add workflow engine to existing ScoutAgent instances"""
    # This would be called during agent initialization
    pass


# Workflow execution methods for ScoutAgent
async def execute_scout_workflows(scout_agent: ScoutAgent, state: AgentState) -> AgentState:
    """Execute scout agent workflows based on current state"""
    workflow_engine = ScoutWorkflowEngine(scout_agent)
    
    try:
        # Execute continuous scanning workflow
        scan_result = await workflow_engine.execute_continuous_scanning_workflow(state)
        
        if scan_result.get("success", False) and scan_result.get("deals"):
            deals = scan_result["deals"]
            
            # Execute deal evaluation workflow
            eval_result = await workflow_engine.execute_deal_evaluation_workflow(deals, state)
            
            if eval_result.get("success", False):
                evaluated_deals = eval_result["evaluated_deals"]
                
                # Execute lead qualification workflow
                qual_result = await workflow_engine.execute_lead_qualification_workflow(evaluated_deals, state)
                
                if qual_result.get("success", False):
                    qualified_leads = qual_result["qualified_leads"]
                    
                    # Execute alert notification workflow
                    alert_result = await workflow_engine.execute_alert_notification_workflow(qualified_leads, state)
                    
                    # Add workflow results to state
                    state = StateManager.add_agent_message(
                        state,
                        AgentType.SCOUT,
                        f"Scout workflows completed: {len(qualified_leads)} qualified leads, {alert_result.get('alerts_generated', 0)} alerts",
                        data={
                            "scan_result": scan_result,
                            "evaluation_result": eval_result,
                            "qualification_result": qual_result,
                            "alert_result": alert_result
                        },
                        priority=2
                    )
        
        # Execute performance monitoring workflow periodically
        perf_result = await workflow_engine.execute_performance_monitoring_workflow(state)
        
        return state
        
    except Exception as e:
        logger.error(f"Scout workflow execution failed: {e}")
        state = StateManager.add_agent_message(
            state,
            AgentType.SCOUT,
            f"Scout workflow execution failed: {str(e)}",
            priority=4
        )
        return state


# Add workflow engine to ScoutAgent
def add_workflow_engine_to_scout_agent():
    """Add workflow engine to existing ScoutAgent instances"""
    # This would be called during agent initialization
    pass


# Workflow execution methods for ScoutAgent
async def execute_scout_workflows(scout_agent: ScoutAgent, state: AgentState) -> AgentState:
    """Execute scout agent workflows based on current state"""
    workflow_engine = ScoutWorkflowEngine(scout_agent)
    
    try:
        # Execute continuous scanning workflow
        scan_result = await workflow_engine.execute_continuous_scanning_workflow(state)
        
        if scan_result.get("success", False) and scan_result.get("deals"):
            deals = scan_result["deals"]
            
            # Execute deal evaluation workflow
            eval_result = await workflow_engine.execute_deal_evaluation_workflow(deals, state)
            
            if eval_result.get("success", False):
                evaluated_deals = eval_result["evaluated_deals"]
                
                # Execute lead qualification workflow
                qual_result = await workflow_engine.execute_lead_qualification_workflow(evaluated_deals, state)
                
                if qual_result.get("success", False):
                    qualified_leads = qual_result["qualified_leads"]
                    
                    # Execute alert notification workflow
                    alert_result = await workflow_engine.execute_alert_notification_workflow(qualified_leads, state)
                    
                    # Add workflow results to state
                    state = StateManager.add_agent_message(
                        state,
                        AgentType.SCOUT,
                        f"Scout workflows completed: {len(qualified_leads)} qualified leads, {alert_result.get('alerts_generated', 0)} alerts",
                        data={
                            "scan_result": scan_result,
                            "evaluation_result": eval_result,
                            "qualification_result": qual_result,
                            "alert_result": alert_result
                        },
                        priority=2
                    )
        
        # Execute performance monitoring workflow periodically
        perf_result = await workflow_engine.execute_performance_monitoring_workflow(state)
        
        return state
        
    except Exception as e:
        logger.error(f"Scout workflow execution failed: {e}")
        state = StateManager.add_agent_message(
            state,
            AgentType.SCOUT,
            f"Scout workflow execution failed: {str(e)}",
            priority=4
        )
        return state
