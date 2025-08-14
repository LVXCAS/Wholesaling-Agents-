"""
LangGraph Setup and Workflow Orchestration Engine
"""

import asyncio
import logging
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
# from langgraph.prebuilt import ToolExecutor  # Not available in current version

from .agent_state import AgentState, StateManager, AgentType, WorkflowStatus
from .llm_config import llm_manager
from .agent_communication import AgentCommunicationProtocol


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LangGraphOrchestrator:
    """
    Main orchestrator for the LangGraph workflow system
    Manages agent coordination and workflow execution
    """
    
    def __init__(self):
        self.workflow: Optional[StateGraph] = None
        self.compiled_workflow = None
        self.memory_saver = MemorySaver()
        self.communication_protocol = AgentCommunicationProtocol()
        self.agent_registry: Dict[str, Any] = {}
        self._setup_workflow()
    
    def _setup_workflow(self):
        """Initialize the LangGraph workflow"""
        logger.info("Setting up LangGraph workflow...")
        
        # Create the state graph
        self.workflow = StateGraph(AgentState)
        
        # Add agent nodes
        self._add_agent_nodes()
        
        # Define workflow edges and routing
        self._define_workflow_edges()
        
        # Set entry point
        self.workflow.set_entry_point("supervisor")
        
        # Compile the workflow with memory
        self.compiled_workflow = self.workflow.compile(
            checkpointer=self.memory_saver,
            interrupt_before=["human_escalation"],  # Pause for human input
            interrupt_after=["contract"]  # Pause after critical steps
        )
        
        logger.info("LangGraph workflow setup complete")
    
    def _add_agent_nodes(self):
        """Add all agent nodes to the workflow"""
        agent_nodes = [
            ("supervisor", self._supervisor_agent),
            ("scout", self._scout_agent),
            ("analyst", self._analyst_agent),
            ("negotiator", self._negotiator_agent),
            ("contract", self._contract_agent),
            ("portfolio", self._portfolio_agent),
            ("market", self._market_agent),
            ("funding", self._funding_agent),
            ("computer_vision", self._computer_vision_agent),
            ("data_ingestion", self._data_ingestion_agent),
            ("human_escalation", self._human_escalation_node)
        ]
        
        for node_name, node_func in agent_nodes:
            self.workflow.add_node(node_name, node_func)
            logger.info(f"Added agent node: {node_name}")
    
    def _define_workflow_edges(self):
        """Define the workflow routing logic"""
        
        # Supervisor makes routing decisions
        self.workflow.add_conditional_edges(
            "supervisor",
            self._route_next_action,
            {
                "scout": "scout",
                "analyze": "analyst", 
                "negotiate": "negotiator",
                "contract": "contract",
                "portfolio": "portfolio",
                "market_analysis": "market",
                "funding": "funding",
                "computer_vision": "computer_vision",
                "data_ingestion": "data_ingestion",
                "human_escalation": "human_escalation",
                "end": END
            }
        )
        
        # All agents return to supervisor for coordination
        agent_names = ["scout", "analyst", "negotiator", "contract", 
                      "portfolio", "market", "funding", "computer_vision", "data_ingestion"]
        
        for agent_name in agent_names:
            self.workflow.add_edge(agent_name, "supervisor")
        
        # Human escalation can return to supervisor or end
        self.workflow.add_conditional_edges(
            "human_escalation",
            self._handle_human_response,
            {
                "continue": "supervisor",
                "end": END
            }
        )
    
    def _route_next_action(self, state: AgentState) -> str:
        """Route to the next agent based on current state"""
        next_action = state.get("next_action")
        
        if not next_action:
            # Default routing logic based on state analysis
            if not state.get("current_deals"):
                return "scout"
            elif any(not deal.get("analyzed", False) for deal in state["current_deals"]):
                return "analyze"
            elif any(deal.get("status") == "approved" and not deal.get("outreach_initiated", False) 
                    for deal in state["current_deals"]):
                return "negotiate"
            else:
                return "end"
        
        return next_action
    
    def _handle_human_response(self, state: AgentState) -> str:
        """Handle human escalation responses"""
        human_input = state.get("human_input", "").lower()
        
        if human_input in ["continue", "proceed", "yes", "approve"]:
            return "continue"
        else:
            return "end"
    
    # Agent Implementation Methods
    
    async def _supervisor_agent(self, state: AgentState) -> AgentState:
        """Supervisor agent - orchestrates the entire system using the SupervisorAgent framework"""
        logger.info("Supervisor agent executing...")
        
        try:
            # Import supervisor agent here to avoid circular imports
            from .supervisor_agent import SupervisorAgent
            
            # Create or get supervisor agent instance
            if not hasattr(self, '_supervisor_instance'):
                self._supervisor_instance = SupervisorAgent()
                # Initialize decision engine after creation
                self._supervisor_instance.decision_engine.initialize()
            
            # Process state using the supervisor agent framework
            updated_state = await self._supervisor_instance.process_state(state)
            
            # Update workflow status
            updated_state["workflow_status"] = WorkflowStatus.RUNNING
            
            logger.info(f"Supervisor completed processing")
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Supervisor agent error: {e}")
            state = StateManager.add_agent_message(
                state,
                AgentType.SUPERVISOR,
                f"Error in supervisor agent: {str(e)}",
                priority=5
            )
            state["workflow_status"] = WorkflowStatus.ERROR
            return state
    
    async def _scout_agent(self, state: AgentState) -> AgentState:
        """Scout agent - discovers new investment opportunities"""
        logger.info("Scout agent executing...")
        
        try:
            # Get LLM for scout
            scout_llm = llm_manager.get_llm("scout")
            
            # Create scouting prompt
            scout_prompt = f"""
            Current Context:
            - Geographic Focus: {state.get('current_geographic_focus', 'national')}
            - Market Conditions: {state.get('market_conditions', {})}
            - Investment Strategy: {state.get('investment_strategy', {})}
            - Available Capital: ${state.get('available_capital', 0):,.2f}
            
            Your mission: Find 5-10 high-potential real estate investment opportunities.
            
            Tasks:
            1. Identify properties that match our investment criteria
            2. Score each lead based on profit potential (1-10 scale)
            3. Gather property details and owner information
            4. Identify motivation indicators for sellers
            5. Prioritize leads by potential ROI and deal feasibility
            
            Focus on:
            - Properties with strong cash flow potential
            - Distressed properties with significant equity upside
            - Motivated sellers (foreclosure, divorce, job relocation, etc.)
            - Properties in emerging or stable neighborhoods
            
            Provide structured data for each opportunity including:
            - Property address and basic details
            - Estimated value and potential profit
            - Lead score and reasoning
            - Owner information and motivation indicators
            - Recommended next steps
            """
            
            # Execute scouting
            scout_response = await scout_llm.ainvoke(scout_prompt)
            
            # Parse scout results (this would integrate with real data sources)
            new_deals = self._parse_scout_results(scout_response.content)
            
            # Add new deals to state
            for deal_data in new_deals:
                from .agent_state import Deal, DealStatus
                deal = Deal(
                    property_address=deal_data.get("address", "Unknown"),
                    city=deal_data.get("city", "Unknown"),
                    state=deal_data.get("state", "Unknown"),
                    zip_code=deal_data.get("zip_code", "Unknown"),
                    status=DealStatus.DISCOVERED,
                    listing_price=deal_data.get("listing_price"),
                    estimated_value=deal_data.get("estimated_value"),
                    source="scout_agent",
                    tags=deal_data.get("tags", [])
                )
                state = StateManager.add_deal(state, deal)
            
            # Add scout message
            state = StateManager.add_agent_message(
                state,
                AgentType.SCOUT,
                f"Discovered {len(new_deals)} new investment opportunities",
                data={"deals_found": len(new_deals), "geographic_focus": state.get('current_geographic_focus')},
                priority=2
            )
            
            logger.info(f"Scout agent found {len(new_deals)} new deals")
            
        except Exception as e:
            logger.error(f"Scout agent error: {e}")
            state = StateManager.add_agent_message(
                state,
                AgentType.SCOUT,
                f"Error in scout agent: {str(e)}",
                priority=4
            )
        
        return state
    
    async def _analyst_agent(self, state: AgentState) -> AgentState:
        """Analyst agent - performs comprehensive property analysis"""
        logger.info("Analyst agent executing...")
        
        try:
            # Get LLM for analyst
            analyst_llm = llm_manager.get_llm("analyst")
            
            # Find deals that need analysis
            unanalyzed_deals = [
                deal for deal in state.get("current_deals", [])
                if not deal.get("analyzed", False)
            ]
            
            for deal in unanalyzed_deals[:3]:  # Analyze up to 3 deals per cycle
                analysis_prompt = f"""
                Perform comprehensive financial analysis for this property:
                
                Property Details:
                - Address: {deal.get('property_address')}
                - City: {deal.get('city')}, {deal.get('state')} {deal.get('zip_code')}
                - Listing Price: ${deal.get('listing_price', 0):,.2f}
                - Property Type: {deal.get('property_type', 'Unknown')}
                - Bedrooms: {deal.get('bedrooms', 'Unknown')}
                - Bathrooms: {deal.get('bathrooms', 'Unknown')}
                - Square Feet: {deal.get('square_feet', 'Unknown')}
                
                Market Context:
                - Market Conditions: {state.get('market_conditions', {})}
                - Investment Strategy: {state.get('investment_strategy', {})}
                
                Provide comprehensive analysis including:
                1. Comparable property analysis (estimate 3-5 comps)
                2. After Repair Value (ARV) estimation with confidence interval
                3. Repair cost estimation (conservative estimate)
                4. Financial projections for multiple strategies:
                   - Fix and Flip
                   - Buy and Hold Rental
                   - Wholesale Assignment
                   - BRRRR Strategy
                5. Risk assessment with specific risk factors
                6. Investment recommendation (Proceed/Pass) with confidence score (1-10)
                7. Expected timeline and profit potential
                
                Use conservative estimates and clearly state all assumptions.
                """
                
                # Get analysis from LLM
                analysis_response = await analyst_llm.ainvoke(analysis_prompt)
                analysis_data = self._parse_analysis_results(analysis_response.content)
                
                # Update deal with analysis
                deal.update({
                    "analyzed": True,
                    "analysis_data": analysis_data,
                    "analyst_recommendation": analysis_data.get("recommendation", "pass"),
                    "confidence_score": analysis_data.get("confidence_score", 0),
                    "arv_estimate": analysis_data.get("arv_estimate"),
                    "repair_estimate": analysis_data.get("repair_estimate"),
                    "potential_profit": analysis_data.get("potential_profit"),
                    "last_updated": datetime.now().isoformat()
                })
                
                # Update deal status
                new_status = "approved" if analysis_data.get("recommendation") == "proceed" else "rejected"
                deal["status"] = new_status
            
            # Add analyst message
            analyzed_count = len(unanalyzed_deals[:3])
            state = StateManager.add_agent_message(
                state,
                AgentType.ANALYST,
                f"Completed analysis for {analyzed_count} properties",
                data={"deals_analyzed": analyzed_count},
                priority=2
            )
            
            logger.info(f"Analyst agent analyzed {analyzed_count} deals")
            
        except Exception as e:
            logger.error(f"Analyst agent error: {e}")
            state = StateManager.add_agent_message(
                state,
                AgentType.ANALYST,
                f"Error in analyst agent: {str(e)}",
                priority=4
            )
        
        return state
    
    # Placeholder implementations for other agents
    async def _negotiator_agent(self, state: AgentState) -> AgentState:
        """Negotiator agent - handles seller communications"""
        logger.info("Negotiator agent executing...")
        # Implementation will be added in next phase
        return state
    
    async def _contract_agent(self, state: AgentState) -> AgentState:
        """Contract agent - manages legal documents"""
        logger.info("Contract agent executing...")
        # Implementation will be added in next phase
        return state
    
    async def _portfolio_agent(self, state: AgentState) -> AgentState:
        """Portfolio agent - manages investment portfolio"""
        logger.info("Portfolio agent executing...")
        # Implementation will be added in next phase
        return state
    
    async def _market_agent(self, state: AgentState) -> AgentState:
        """Market agent - analyzes market conditions"""
        logger.info("Market agent executing...")
        # Implementation will be added in next phase
        return state
    
    async def _funding_agent(self, state: AgentState) -> AgentState:
        """Funding agent - manages funding and investors"""
        logger.info("Funding agent executing...")
        # Implementation will be added in next phase
        return state
    
    async def _computer_vision_agent(self, state: AgentState) -> AgentState:
        """Computer vision agent - analyzes property images"""
        logger.info("Computer vision agent executing...")
        # Implementation will be added in next phase
        return state
    
    async def _data_ingestion_agent(self, state: AgentState) -> AgentState:
        """Data ingestion agent - processes new data sources"""
        logger.info("Data ingestion agent executing...")
        # Implementation will be added in next phase
        return state
    
    async def _human_escalation_node(self, state: AgentState) -> AgentState:
        """Human escalation node - pauses for human input"""
        logger.info("Human escalation triggered - awaiting human input...")
        
        state = StateManager.add_agent_message(
            state,
            AgentType.SUPERVISOR,
            "Workflow paused for human review and approval",
            priority=5
        )
        
        state["human_approval_required"] = True
        state["workflow_status"] = WorkflowStatus.HUMAN_ESCALATION
        
        return state
    
    # Helper Methods
    
    def _analyze_system_state(self, state: AgentState) -> str:
        """Analyze current system state for supervisor decision making"""
        current_deals = state.get("current_deals", [])
        
        analysis = {
            "total_deals": len(current_deals),
            "unanalyzed_deals": len([d for d in current_deals if not d.get("analyzed", False)]),
            "approved_deals": len([d for d in current_deals if d.get("status") == "approved"]),
            "active_negotiations": len(state.get("active_negotiations", [])),
            "workflow_status": state.get("workflow_status", "unknown"),
            "last_action": state.get("current_step", "none")
        }
        
        return str(analysis)
    
    def _parse_supervisor_decision(self, response: str) -> Dict[str, str]:
        """Parse supervisor LLM response into structured decision"""
        # Simple parsing - in production, use more sophisticated NLP
        response_lower = response.lower()
        
        if "scout" in response_lower or "find" in response_lower:
            action = "scout"
        elif "analy" in response_lower:
            action = "analyze"
        elif "negotiat" in response_lower:
            action = "negotiate"
        elif "contract" in response_lower:
            action = "contract"
        elif "portfolio" in response_lower:
            action = "portfolio"
        elif "market" in response_lower:
            action = "market_analysis"
        elif "fund" in response_lower:
            action = "funding"
        elif "vision" in response_lower or "image" in response_lower:
            action = "computer_vision"
        elif "data" in response_lower or "ingest" in response_lower:
            action = "data_ingestion"
        elif "human" in response_lower or "escalat" in response_lower:
            action = "human_escalation"
        elif "end" in response_lower or "complete" in response_lower:
            action = "end"
        else:
            action = "scout"  # Default action
        
        return {
            "action": action,
            "reasoning": response[:200] + "..." if len(response) > 200 else response
        }
    
    def _parse_scout_results(self, response: str) -> List[Dict[str, Any]]:
        """Parse scout LLM response into structured deal data"""
        # Placeholder implementation - in production, use structured output
        # This would integrate with real MLS APIs, Zillow, etc.
        
        sample_deals = [
            {
                "address": "123 Main St",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78701",
                "listing_price": 350000,
                "estimated_value": 400000,
                "lead_score": 8,
                "tags": ["distressed", "motivated_seller"]
            },
            {
                "address": "456 Oak Ave",
                "city": "Austin", 
                "state": "TX",
                "zip_code": "78702",
                "listing_price": 275000,
                "estimated_value": 320000,
                "lead_score": 7,
                "tags": ["foreclosure", "high_equity"]
            }
        ]
        
        return sample_deals
    
    def _parse_analysis_results(self, response: str) -> Dict[str, Any]:
        """Parse analyst LLM response into structured analysis data"""
        # Placeholder implementation - in production, use structured output
        
        return {
            "recommendation": "proceed" if "proceed" in response.lower() else "pass",
            "confidence_score": 7.5,  # Would be extracted from LLM response
            "arv_estimate": 400000,
            "repair_estimate": 25000,
            "potential_profit": 50000,
            "risk_factors": ["market_volatility", "repair_overruns"],
            "analysis_summary": response[:500] + "..." if len(response) > 500 else response
        }
    
    # Public Interface Methods
    
    async def start_workflow(self, initial_state: Optional[AgentState] = None) -> str:
        """Start a new workflow execution"""
        if not initial_state:
            initial_state = StateManager.create_initial_state()
        
        workflow_id = initial_state["workflow_id"]
        
        try:
            # Start the workflow
            config = {"configurable": {"thread_id": workflow_id}}
            
            # Execute workflow
            result = await self.compiled_workflow.ainvoke(initial_state, config)
            
            logger.info(f"Workflow {workflow_id} completed successfully")
            return workflow_id
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}")
            raise e
    
    async def continue_workflow(self, workflow_id: str, human_input: Optional[str] = None) -> AgentState:
        """Continue a paused workflow"""
        config = {"configurable": {"thread_id": workflow_id}}
        
        # Add human input if provided
        if human_input:
            current_state = await self.get_workflow_state(workflow_id)
            current_state["human_input"] = human_input
            current_state["human_approval_required"] = False
        
        # Continue workflow
        result = await self.compiled_workflow.ainvoke(None, config)
        return result
    
    async def get_workflow_state(self, workflow_id: str) -> AgentState:
        """Get current state of a workflow"""
        config = {"configurable": {"thread_id": workflow_id}}
        state = await self.compiled_workflow.aget_state(config)
        return state.values
    
    def get_workflow_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get execution history of a workflow"""
        config = {"configurable": {"thread_id": workflow_id}}
        history = self.compiled_workflow.get_state_history(config)
        return [{"step": h.next, "state": h.values} for h in history]


# Global orchestrator instance
orchestrator = LangGraphOrchestrator()