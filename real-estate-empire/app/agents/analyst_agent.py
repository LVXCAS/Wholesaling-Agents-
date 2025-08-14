"""
Analyst Agent - Comprehensive Property Analysis and Financial Modeling
Specialized agent for deep property analysis, financial calculations, and investment strategy evaluation
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
from .analyst_models import PropertyAnalysis, PropertyValuation, RepairEstimate, FinancialMetrics, InvestmentStrategy, MarketAnalysis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)





class AnalystAgent(BaseAgent):
    """
    Analyst Agent - Comprehensive Property Analysis and Financial Modeling
    
    Responsibilities:
    - Perform deep property analysis and financial modeling
    - Calculate comprehensive financial metrics and projections
    - Analyze comparable properties for accurate valuations
    - Estimate repair costs using AI and market data
    - Evaluate multiple investment strategies
    - Provide risk assessment and confidence scoring
    - Generate detailed investment recommendations
    """
    
    def __init__(self, name: str = "AnalystAgent", description: str = "Comprehensive property analysis agent"):
        # Define agent capabilities
        capabilities = [
            AgentCapability(
                name="property_valuation",
                description="Perform comprehensive property valuation using comparable sales",
                input_schema={
                    "property": "PropertyData",
                    "market_data": "Dict[str, Any]"
                },
                output_schema={
                    "valuation": "PropertyValuation",
                    "comparables": "List[Dict[str, Any]]"
                },
                required_tools=["comparable_finder", "market_data"],
                estimated_duration=180
            ),
            AgentCapability(
                name="repair_estimation",
                description="Estimate repair costs using AI vision and market data",
                input_schema={
                    "property": "PropertyData",
                    "photos": "List[str]",
                    "description": "str"
                },
                output_schema={
                    "repair_estimate": "RepairEstimate"
                },
                required_tools=["repair_estimator", "ai_vision"],
                estimated_duration=120
            ),
            AgentCapability(
                name="financial_analysis",
                description="Calculate comprehensive financial metrics and projections",
                input_schema={
                    "property": "PropertyData",
                    "valuation": "PropertyValuation",
                    "repair_estimate": "RepairEstimate"
                },
                output_schema={
                    "financial_metrics": "FinancialMetrics"
                },
                required_tools=["financial_calculator", "market_data"],
                estimated_duration=90
            ),
            AgentCapability(
                name="strategy_analysis",
                description="Analyze and compare multiple investment strategies",
                input_schema={
                    "property": "PropertyData",
                    "financial_metrics": "FinancialMetrics",
                    "market_conditions": "Dict[str, Any]"
                },
                output_schema={
                    "strategies": "List[InvestmentStrategy]",
                    "recommended_strategy": "str"
                },
                required_tools=["strategy_analyzer", "market_data"],
                estimated_duration=150
            ),
            AgentCapability(
                name="risk_assessment",
                description="Assess investment risks and generate confidence scores",
                input_schema={
                    "property": "PropertyData",
                    "analysis": "PropertyAnalysis"
                },
                output_schema={
                    "risk_factors": "List[str]",
                    "risk_score": "float",
                    "confidence_score": "float"
                },
                required_tools=["risk_analyzer", "market_data"],
                estimated_duration=60
            )
        ]
        
        # Analyst-specific attributes (initialize before base agent)
        self.analysis_history: Dict[str, PropertyAnalysis] = {}
        self.market_cache: Dict[str, MarketAnalysis] = {}
        self.comparable_cache: Dict[str, List[Dict[str, Any]]] = {}
        
        # Analysis configuration
        self.default_cap_rate_threshold = 0.08
        self.default_cash_flow_threshold = 200
        self.default_roi_threshold = 0.15
        self.repair_contingency_percentage = 0.15
        
        # Performance metrics
        self.analyses_completed_today = 0
        self.total_analyses_completed = 0
        self.average_analysis_time = 0.0
        self.accuracy_score = 0.0
        
        # Initialize agent executor
        self.agent_executor: Optional[AgentExecutor] = None
        
        # Initialize workflows
        self.workflows: Optional[AnalystWorkflows] = None
        
        # Initialize base agent
        super().__init__(
            agent_type=AgentType.ANALYST,
            name=name,
            description=description,
            capabilities=capabilities
        )
        
        # Setup agent executor after base initialization
        self._setup_agent_executor()
        
        # Initialize workflows (import here to avoid circular import)
        from .analyst_workflows import AnalystWorkflows
        self.workflows = AnalystWorkflows(self)
    
    def _agent_specific_initialization(self):
        """Analyst agent specific initialization"""
        logger.info("Initializing Analyst Agent...")
        
        # Set up default analysis parameters
        self._setup_default_parameters()
        
        # Initialize market data cache
        self._initialize_market_cache()
        
        # Set up analysis workflows
        self._setup_analysis_workflows()
        
        logger.info("Analyst Agent initialization complete")
    
    def _setup_default_parameters(self):
        """Set up default analysis parameters"""
        self.analysis_parameters = {
            "valuation": {
                "min_comps": 3,
                "max_comp_distance": 2.0,  # miles
                "max_comp_age": 180,  # days
                "adjustment_factors": {
                    "condition": {"excellent": 1.1, "good": 1.0, "fair": 0.9, "poor": 0.8},
                    "location": {"prime": 1.05, "good": 1.0, "average": 0.95, "poor": 0.9}
                }
            },
            "repair_estimation": {
                "contingency_percentage": 0.15,
                "labor_cost_multiplier": 1.2,
                "material_cost_inflation": 0.05
            },
            "financial_analysis": {
                "vacancy_rate": 0.05,
                "management_fee": 0.08,
                "maintenance_reserve": 0.05,
                "capex_reserve": 0.05
            }
        }
    
    def _initialize_market_cache(self):
        """Initialize market data cache"""
        self.market_cache = {}
        self.cache_expiry = timedelta(hours=6)  # Cache expires after 6 hours
    
    def _setup_analysis_workflows(self):
        """Set up analysis workflows"""
        self.analysis_workflows = {
            "comprehensive": [
                "property_valuation",
                "repair_estimation", 
                "financial_analysis",
                "strategy_analysis",
                "risk_assessment"
            ],
            "quick": [
                "property_valuation",
                "financial_analysis"
            ],
            "detailed": [
                "property_valuation",
                "repair_estimation",
                "financial_analysis",
                "strategy_analysis",
                "risk_assessment"
            ]
        }
    
    def _setup_agent_executor(self):
        """Set up the LangChain agent executor"""
        try:
            # Get available tools for analyst agent
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
                max_iterations=15,
                max_execution_time=600,  # 10 minutes
                return_intermediate_steps=True
            )
            
            logger.info(f"Analyst agent executor created with {len(langchain_tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to setup analyst agent executor: {e}")
            self.agent_executor = None
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the analyst agent"""
        return """
        You are an expert real estate financial analyst agent specializing in comprehensive property analysis and investment evaluation.
        
        Your primary mission is to:
        1. Perform accurate property valuations using comparable sales analysis
        2. Estimate repair costs using property photos, descriptions, and market data
        3. Calculate comprehensive financial metrics for investment evaluation
        4. Analyze multiple investment strategies (flip, rental, wholesale, BRRRR)
        5. Assess investment risks and provide confidence scores
        6. Generate detailed investment recommendations
        
        Key Responsibilities:
        - Property Valuation: Use comparable sales to determine current value and ARV
        - Repair Estimation: Analyze property condition and estimate renovation costs
        - Financial Analysis: Calculate cap rates, cash flow, ROI, and other key metrics
        - Strategy Comparison: Evaluate different investment approaches and recommend optimal strategy
        - Risk Assessment: Identify potential risks and assign confidence scores
        - Market Analysis: Consider local market conditions and trends
        
        Analysis Standards:
        - Use minimum 3 comparable properties for valuations
        - Include 15% contingency in repair estimates
        - Consider vacancy rates, management fees, and reserves in rental analysis
        - Provide conservative estimates with clear assumptions
        - Assign confidence scores based on data quality and market conditions
        - Identify and flag potential risks or red flags
        
        Investment Criteria:
        - Minimum 8% cap rate for rental properties
        - Minimum $200 monthly cash flow
        - Minimum 15% ROI for flip projects
        - Maximum 70% ARV for purchase price (including repairs)
        
        Communication Style:
        - Provide detailed analysis with supporting data
        - Use specific numbers and metrics
        - Explain methodology and assumptions
        - Highlight key opportunities and risks
        - Structure output for easy processing by other agents
        - Include confidence levels for all estimates
        
        Always focus on providing accurate, conservative analysis that enables informed investment decisions.
        """
    
    # Core Agent Methods
    
    async def execute_task(self, task: str, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute a specific analyst task"""
        logger.info(f"Analyst agent executing task: {task}")
        
        try:
            if task == "analyze_property":
                return await self._analyze_property(data, state)
            elif task == "valuate_property":
                return await self._execute_valuation_workflow(data, state)
            elif task == "estimate_repairs":
                return await self._estimate_repair_costs(data.get("deal", {}), state)
            elif task == "calculate_financials":
                return await self._execute_financial_workflow(data, state)
            elif task == "analyze_strategies":
                return await self._execute_strategy_workflow(data, state)
            elif task == "assess_risk":
                return await self._execute_risk_workflow(data, state)
            else:
                raise ValueError(f"Unknown task: {task}")
                
        except Exception as e:
            logger.error(f"Error executing analyst task {task}: {e}")
            return {
                "success": False,
                "error": str(e),
                "task": task
            }
    
    async def _execute_valuation_workflow(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute property valuation workflow"""
        if not self.workflows:
            return {"success": False, "error": "Workflows not initialized"}
        
        deal = data.get("deal", {})
        result = await self.workflows.execute_property_valuation_workflow(deal, state)
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time,
            "confidence_score": result.confidence_score
        }
    
    async def _execute_financial_workflow(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute financial analysis workflow"""
        if not self.workflows:
            return {"success": False, "error": "Workflows not initialized"}
        
        deal = data.get("deal", {})
        valuation_data = data.get("valuation", {})
        repair_data = data.get("repair_estimate", {})
        
        # Create objects from data
        valuation = PropertyValuation(**valuation_data) if valuation_data else None
        repair_estimate = RepairEstimate(**repair_data) if repair_data else None
        
        if not valuation or not repair_estimate:
            return {"success": False, "error": "Valuation and repair estimate required"}
        
        result = await self.workflows.execute_financial_analysis_workflow(deal, valuation, repair_estimate, state)
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time,
            "confidence_score": result.confidence_score
        }
    
    async def _execute_strategy_workflow(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute strategy comparison workflow"""
        if not self.workflows:
            return {"success": False, "error": "Workflows not initialized"}
        
        deal = data.get("deal", {})
        financial_data = data.get("financial_metrics", {})
        
        # Create financial metrics object
        financial_metrics = FinancialMetrics(**financial_data) if financial_data else None
        
        if not financial_metrics:
            return {"success": False, "error": "Financial metrics required"}
        
        result = await self.workflows.execute_strategy_comparison_workflow(deal, financial_metrics, state)
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time,
            "confidence_score": result.confidence_score
        }
    
    async def _execute_risk_workflow(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute risk assessment workflow"""
        if not self.workflows:
            return {"success": False, "error": "Workflows not initialized"}
        
        deal = data.get("deal", {})
        analysis_data = data.get("analysis_data", {})
        
        result = await self.workflows.execute_risk_assessment_workflow(deal, analysis_data, state)
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time,
            "confidence_score": result.confidence_score
        }
    
    async def process_state(self, state: AgentState) -> AgentState:
        """Process the current state and analyze properties"""
        logger.info("Analyst agent processing state...")
        
        try:
            # Get deals that need analysis
            deals_to_analyze = [
                deal for deal in state.get("current_deals", [])
                if not deal.get("analyzed", False) and deal.get("status") == DealStatus.DISCOVERED.value
            ]
            
            if not deals_to_analyze:
                logger.info("No deals requiring analysis")
                return state
            
            # Analyze each deal
            analyzed_count = 0
            for deal in deals_to_analyze:
                try:
                    # Perform comprehensive analysis
                    analysis_result = await self._analyze_property({"deal": deal}, state)
                    
                    if analysis_result.get("success", False):
                        # Update deal with analysis results
                        analysis = analysis_result["analysis"]
                        deal.update({
                            "analyzed": True,
                            "analysis_data": analysis,
                            "analyst_recommendation": analysis.get("investment_recommendation"),
                            "confidence_score": analysis.get("confidence_level"),
                            "last_analyzed": datetime.now().isoformat()
                        })
                        
                        # Update deal status based on recommendation
                        if analysis.get("investment_recommendation") == "proceed":
                            deal["status"] = DealStatus.ANALYZED.value
                        elif analysis.get("investment_recommendation") == "caution":
                            deal["status"] = DealStatus.ANALYZING.value
                        else:
                            deal["status"] = DealStatus.REJECTED.value
                        
                        analyzed_count += 1
                        
                        # Store analysis in history
                        self.analysis_history[deal.get("id", str(uuid.uuid4()))] = analysis
                        
                    else:
                        logger.error(f"Failed to analyze deal: {analysis_result.get('error')}")
                        
                except Exception as e:
                    logger.error(f"Error analyzing individual deal: {e}")
                    continue
            
            # Update metrics
            self.analyses_completed_today += analyzed_count
            self.total_analyses_completed += analyzed_count
            
            # Add agent message
            if analyzed_count > 0:
                state = StateManager.add_agent_message(
                    state,
                    AgentType.ANALYST,
                    f"Analyzed {analyzed_count} properties with comprehensive financial modeling",
                    data={
                        "deals_analyzed": analyzed_count,
                        "total_deals": len(deals_to_analyze),
                        "recommendations": {
                            "proceed": len([d for d in deals_to_analyze if d.get("analyst_recommendation") == "proceed"]),
                            "caution": len([d for d in deals_to_analyze if d.get("analyst_recommendation") == "caution"]),
                            "reject": len([d for d in deals_to_analyze if d.get("analyst_recommendation") == "reject"])
                        }
                    },
                    priority=2
                )
                
                # Set next action if there are approved deals
                approved_deals = [d for d in deals_to_analyze if d.get("analyst_recommendation") == "proceed"]
                if approved_deals:
                    state = StateManager.set_next_action(
                        state,
                        "negotiate",
                        f"Found {len(approved_deals)} approved deals ready for outreach"
                    )
            
            return state
            
        except Exception as e:
            logger.error(f"Error in analyst agent state processing: {e}")
            state = StateManager.add_agent_message(
                state,
                AgentType.ANALYST,
                f"Error in analyst agent: {str(e)}",
                priority=4
            )
            return state
    
    def get_available_tasks(self) -> List[str]:
        """Get list of tasks this agent can perform"""
        return [
            "analyze_property",
            "valuate_property", 
            "estimate_repairs",
            "calculate_financials",
            "analyze_strategies",
            "assess_risk"
        ]
    
    def get_available_workflows(self) -> List[str]:
        """Get list of workflows this agent can execute"""
        return [
            "property_valuation",
            "financial_analysis",
            "strategy_comparison", 
            "risk_assessment",
            "recommendation_generation"
        ]
    
    async def execute_workflow(self, workflow_name: str, deal: Dict[str, Any], 
                              state: AgentState, **kwargs):
        """Execute a specific workflow"""
        from .analyst_workflows import WorkflowResult
        
        if not self.workflows:
            return WorkflowResult(
                workflow_name=workflow_name,
                success=False,
                error="Workflows not initialized"
            )
        
        try:
            if workflow_name == "property_valuation":
                return await self.workflows.execute_property_valuation_workflow(deal, state)
            elif workflow_name == "financial_analysis":
                valuation = kwargs.get("valuation")
                repair_estimate = kwargs.get("repair_estimate")
                if not valuation or not repair_estimate:
                    raise ValueError("Valuation and repair estimate required for financial analysis")
                return await self.workflows.execute_financial_analysis_workflow(deal, valuation, repair_estimate, state)
            elif workflow_name == "strategy_comparison":
                financial_metrics = kwargs.get("financial_metrics")
                if not financial_metrics:
                    raise ValueError("Financial metrics required for strategy comparison")
                return await self.workflows.execute_strategy_comparison_workflow(deal, financial_metrics, state)
            elif workflow_name == "risk_assessment":
                analysis_data = kwargs.get("analysis_data", {})
                return await self.workflows.execute_risk_assessment_workflow(deal, analysis_data, state)
            elif workflow_name == "recommendation_generation":
                workflow_results = kwargs.get("workflow_results", {})
                return await self.workflows.execute_recommendation_generation_workflow(deal, workflow_results, state)
            else:
                raise ValueError(f"Unknown workflow: {workflow_name}")
                
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_name}: {e}")
            return WorkflowResult(
                workflow_name=workflow_name,
                success=False,
                error=str(e)
            )
    
    def get_workflow_history(self, workflow_name: Optional[str] = None) -> Dict[str, Any]:
        """Get workflow execution history"""
        if not self.workflows:
            return {}
        return self.workflows.get_workflow_history(workflow_name)
    
    # Private Implementation Methods
    
    async def _analyze_property(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Perform comprehensive property analysis using workflows"""
        deal = data.get("deal", {})
        
        if not self.workflows:
            return {
                "success": False,
                "error": "Workflows not initialized"
            }
        
        try:
            logger.info(f"Starting comprehensive property analysis for deal {deal.get('id')}")
            
            # Execute all analysis workflows in sequence
            workflow_results = {}
            
            # 1. Property Valuation Workflow
            logger.info("Executing property valuation workflow...")
            valuation_result = await self.workflows.execute_property_valuation_workflow(deal, state)
            workflow_results["property_valuation"] = valuation_result
            
            if not valuation_result.success:
                logger.error(f"Property valuation failed: {valuation_result.error}")
                return {
                    "success": False,
                    "error": f"Property valuation failed: {valuation_result.error}"
                }
            
            # Extract valuation data
            valuation_data = valuation_result.data.get("valuation", {})
            valuation = PropertyValuation(**valuation_data)
            
            # 2. Repair Cost Estimation (using existing tool)
            logger.info("Estimating repair costs...")
            repair_result = await self._estimate_repair_costs(deal, state)
            if not repair_result.get("success", False):
                logger.error("Repair estimation failed")
                return {
                    "success": False,
                    "error": "Repair cost estimation failed"
                }
            
            repair_data = repair_result.get("repair_estimate", {})
            repair_estimate = RepairEstimate(
                total_cost=repair_data.get("total_cost", 0),
                confidence_score=repair_data.get("confidence_score", 0.8),
                line_items=repair_data.get("line_items", {}),
                contingency_percentage=repair_data.get("contingency_percentage", 0.15),
                timeline_days=repair_data.get("timeline_days", 45),
                priority_repairs=repair_data.get("priority_repairs", []),
                cosmetic_repairs=repair_data.get("cosmetic_repairs", [])
            )
            
            # 3. Financial Analysis Workflow
            logger.info("Executing financial analysis workflow...")
            financial_result = await self.workflows.execute_financial_analysis_workflow(
                deal, valuation, repair_estimate, state
            )
            workflow_results["financial_analysis"] = financial_result
            
            if not financial_result.success:
                logger.error(f"Financial analysis failed: {financial_result.error}")
                return {
                    "success": False,
                    "error": f"Financial analysis failed: {financial_result.error}"
                }
            
            # Extract financial metrics
            financial_data = financial_result.data.get("financial_metrics", {})
            financial_metrics = FinancialMetrics(**financial_data)
            
            # 4. Strategy Comparison Workflow
            logger.info("Executing strategy comparison workflow...")
            strategy_result = await self.workflows.execute_strategy_comparison_workflow(
                deal, financial_metrics, state
            )
            workflow_results["strategy_comparison"] = strategy_result
            
            if not strategy_result.success:
                logger.warning(f"Strategy comparison failed: {strategy_result.error}")
                # Continue with default strategy
                strategies = []
                recommended_strategy = "buy_and_hold_rental"
            else:
                strategies_data = strategy_result.data.get("strategies", [])
                strategies = [InvestmentStrategy(**s) for s in strategies_data]
                recommended_strategy = strategy_result.data.get("recommended_strategy", "buy_and_hold_rental")
            
            # 5. Risk Assessment Workflow
            logger.info("Executing risk assessment workflow...")
            analysis_data = {
                "valuation": valuation_result.data,
                "financial_metrics": financial_result.data,
                "repair_estimate": repair_result
            }
            
            risk_result = await self.workflows.execute_risk_assessment_workflow(
                deal, analysis_data, state
            )
            workflow_results["risk_assessment"] = risk_result
            
            if not risk_result.success:
                logger.warning(f"Risk assessment failed: {risk_result.error}")
                # Continue with default risk assessment
                risk_factors = ["Insufficient data for complete risk assessment"]
                overall_risk_score = 5.0
            else:
                risk_factors = risk_result.data.get("risk_factors", [])
                overall_risk_score = risk_result.data.get("overall_risk_score", 5.0)
            
            # 6. Recommendation Generation Workflow
            logger.info("Executing recommendation generation workflow...")
            recommendation_result = await self.workflows.execute_recommendation_generation_workflow(
                deal, workflow_results, state
            )
            workflow_results["recommendation_generation"] = recommendation_result
            
            if not recommendation_result.success:
                logger.warning(f"Recommendation generation failed: {recommendation_result.error}")
                # Generate fallback recommendation
                investment_recommendation = "caution"
                recommendation_reason = "Analysis incomplete - manual review required"
                confidence_level = 0.5
            else:
                investment_recommendation = recommendation_result.data.get("investment_recommendation", "caution")
                recommendation_reason = recommendation_result.data.get("recommendation_reason", "")
                confidence_level = recommendation_result.data.get("confidence_level", 0.5)
            
            # 7. Compile comprehensive analysis
            comprehensive_analysis = PropertyAnalysis(
                property_id=deal.get("id", str(uuid.uuid4())),
                valuation=valuation,
                repair_estimate=repair_estimate,
                financial_metrics=financial_metrics,
                strategies=strategies,
                recommended_strategy=recommended_strategy,
                comparable_properties=valuation_result.data.get("comparables", []),
                market_conditions=state.get("market_conditions", {}),
                neighborhood_analysis={},  # Could be enhanced later
                risk_factors=risk_factors,
                overall_risk_score=overall_risk_score,
                investment_recommendation=investment_recommendation,
                recommendation_reason=recommendation_reason,
                confidence_level=confidence_level
            )
            
            # Record workflow results
            for result in workflow_results.values():
                self.workflows._record_workflow_result(result)
            
            logger.info(f"Comprehensive analysis completed for deal {deal.get('id')} with recommendation: {investment_recommendation}")
            
            return {
                "success": True,
                "analysis": comprehensive_analysis.model_dump(),
                "workflow_results": {name: result.model_dump() for name, result in workflow_results.items()},
                "deal_id": deal.get("id"),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive property analysis: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _estimate_repair_costs(self, deal: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Estimate repair costs using repair estimator tool"""
        try:
            repair_tool = tool_registry.get_tool("repair_cost_estimator")
            if not repair_tool:
                raise ValueError("Repair cost estimator tool not available")
            
            result = await repair_tool.execute(
                property_photos=deal.get("photos", []),
                property_description=deal.get("description", ""),
                property_age=datetime.now().year - deal.get("year_built", 1990),
                square_feet=deal.get("square_feet", 1500),
                property_condition=deal.get("property_condition", "fair")
            )
            
            return {
                "success": True,
                "repair_estimate": result.get("repair_estimate", {}),
                "line_items": result.get("line_items", {}),
                "repair_categories": result.get("repair_categories", {})
            }
            
        except Exception as e:
            logger.error(f"Repair cost estimation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_analysis_results(self, llm_output: str, deal: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM output into structured analysis data"""
        # This is a simplified parser - in production, use structured output
        # or more sophisticated NLP parsing
        
        # Create sample comprehensive analysis
        property_address = deal.get("property_address", "Unknown Property")
        listing_price = deal.get("listing_price", 250000)
        
        # Sample valuation
        valuation = {
            "arv": listing_price * 1.15,
            "current_value": listing_price * 0.95,
            "confidence_score": 0.85,
            "comp_count": 5,
            "valuation_method": "comparable_sales",
            "price_per_sqft": 150.0,
            "market_adjustment": 0.02,
            "condition_adjustment": -0.05
        }
        
        # Sample repair estimate
        repair_estimate = {
            "total_cost": listing_price * 0.12,
            "confidence_score": 0.80,
            "line_items": {
                "kitchen_renovation": 15000,
                "bathroom_updates": 8000,
                "flooring": 6000,
                "paint_interior": 3000,
                "landscaping": 2000
            },
            "contingency_percentage": 0.15,
            "timeline_days": 45,
            "priority_repairs": ["kitchen_renovation", "bathroom_updates"],
            "cosmetic_repairs": ["paint_interior", "landscaping"]
        }
        
        # Sample financial metrics
        total_investment = listing_price + repair_estimate["total_cost"]
        monthly_rent = listing_price * 0.01  # 1% rule approximation
        monthly_expenses = monthly_rent * 0.45  # 45% expense ratio
        
        financial_metrics = {
            "purchase_price": listing_price,
            "repair_cost": repair_estimate["total_cost"],
            "total_investment": total_investment,
            "after_repair_value": valuation["arv"],
            "monthly_rent": monthly_rent,
            "monthly_expenses": monthly_expenses,
            "monthly_cash_flow": monthly_rent - monthly_expenses,
            "annual_cash_flow": (monthly_rent - monthly_expenses) * 12,
            "cap_rate": ((monthly_rent - monthly_expenses) * 12) / total_investment,
            "cash_on_cash_return": ((monthly_rent - monthly_expenses) * 12) / (total_investment * 0.25),  # 25% down
            "roi": (valuation["arv"] - total_investment) / total_investment,
            "gross_rent_multiplier": total_investment / (monthly_rent * 12),
            "flip_profit": valuation["arv"] - total_investment - (total_investment * 0.08),  # 8% selling costs
            "flip_roi": (valuation["arv"] - total_investment - (total_investment * 0.08)) / total_investment,
            "flip_timeline_days": 90,
            "wholesale_fee": 8000,
            "wholesale_margin": 8000 / listing_price
        }
        
        # Sample investment strategies
        strategies = [
            {
                "strategy_type": "buy_and_hold_rental",
                "potential_profit": financial_metrics["annual_cash_flow"],
                "roi": financial_metrics["cash_on_cash_return"],
                "risk_level": 4.0,
                "timeline_days": 30,
                "funding_required": total_investment * 0.25,
                "pros": ["Steady cash flow", "Appreciation potential", "Tax benefits"],
                "cons": ["Property management required", "Vacancy risk", "Maintenance costs"],
                "confidence_score": 0.85
            },
            {
                "strategy_type": "fix_and_flip",
                "potential_profit": financial_metrics["flip_profit"],
                "roi": financial_metrics["flip_roi"],
                "risk_level": 6.0,
                "timeline_days": financial_metrics["flip_timeline_days"],
                "funding_required": total_investment,
                "pros": ["Quick profit", "No landlord responsibilities", "Market appreciation"],
                "cons": ["Market risk", "Construction delays", "Holding costs"],
                "confidence_score": 0.75
            },
            {
                "strategy_type": "wholesale",
                "potential_profit": financial_metrics["wholesale_fee"],
                "roi": financial_metrics["wholesale_margin"],
                "risk_level": 2.0,
                "timeline_days": 14,
                "funding_required": 1000,  # Earnest money
                "pros": ["Low risk", "Quick turnaround", "No renovation needed"],
                "cons": ["Lower profit", "Requires buyer network", "Market dependent"],
                "confidence_score": 0.90
            }
        ]
        
        # Determine recommended strategy
        best_strategy = max(strategies, key=lambda x: x["roi"] * x["confidence_score"] / x["risk_level"])
        
        # Sample risk assessment
        risk_factors = []
        overall_risk_score = 5.0
        
        if financial_metrics["cap_rate"] < 0.06:
            risk_factors.append("Low cap rate below market standards")
            overall_risk_score += 1.0
        
        if repair_estimate["total_cost"] > listing_price * 0.15:
            risk_factors.append("High repair costs relative to purchase price")
            overall_risk_score += 1.0
        
        if deal.get("days_on_market", 0) > 90:
            risk_factors.append("Property has been on market for extended period")
            overall_risk_score += 0.5
        
        # Investment recommendation
        if financial_metrics["cap_rate"] >= 0.08 and financial_metrics["monthly_cash_flow"] >= 200:
            investment_recommendation = "proceed"
            recommendation_reason = "Strong financial metrics meet investment criteria"
            confidence_level = 0.85
        elif financial_metrics["cap_rate"] >= 0.06 or financial_metrics["monthly_cash_flow"] >= 100:
            investment_recommendation = "caution"
            recommendation_reason = "Marginal financial metrics, requires careful consideration"
            confidence_level = 0.70
        else:
            investment_recommendation = "reject"
            recommendation_reason = "Financial metrics do not meet minimum investment criteria"
            confidence_level = 0.90
        
        # Compile comprehensive analysis
        analysis = {
            "id": str(uuid.uuid4()),
            "property_id": deal.get("id", str(uuid.uuid4())),
            "analysis_date": datetime.now().isoformat(),
            "valuation": valuation,
            "repair_estimate": repair_estimate,
            "financial_metrics": financial_metrics,
            "strategies": strategies,
            "recommended_strategy": best_strategy["strategy_type"],
            "comparable_properties": self._generate_sample_comps(deal),
            "market_conditions": {
                "market_temperature": "warm",
                "price_trend": "stable",
                "inventory_level": "normal",
                "rental_demand": "strong"
            },
            "neighborhood_analysis": {
                "school_rating": 7.5,
                "crime_score": 6.0,
                "walkability": 8.0,
                "appreciation_trend": "positive"
            },
            "risk_factors": risk_factors,
            "overall_risk_score": min(10.0, overall_risk_score),
            "investment_recommendation": investment_recommendation,
            "recommendation_reason": recommendation_reason,
            "confidence_level": confidence_level
        }
        
        return analysis
    
    def _generate_sample_comps(self, deal: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate sample comparable properties"""
        base_price = deal.get("listing_price", 250000)
        
        comps = []
        for i in range(5):
            comp = {
                "address": f"{1000 + i * 100} Comparable St",
                "sale_price": base_price + (i * 10000) - 20000,
                "sale_date": (datetime.now() - timedelta(days=30 + i * 20)).isoformat(),
                "bedrooms": deal.get("bedrooms", 3) + (i % 2 - 1),
                "bathrooms": deal.get("bathrooms", 2) + (i % 3 - 1) * 0.5,
                "square_feet": deal.get("square_feet", 1500) + (i * 100) - 200,
                "distance_miles": 0.5 + i * 0.3,
                "similarity_score": 0.95 - (i * 0.05),
                "adjustments": {
                    "condition": 0 if i < 3 else -5000,
                    "location": 0 if i < 2 else 3000,
                    "size": (deal.get("square_feet", 1500) - (deal.get("square_feet", 1500) + (i * 100) - 200)) * 100
                }
            }
            comps.append(comp)
        
        return comps
    
    # Additional helper methods would be implemented here for:
    # - Market data retrieval and caching
    # - Comparable property analysis
    # - Repair cost estimation
    # - Financial calculations
    # - Risk assessment algorithms
    
    def get_analysis_history(self, property_id: Optional[str] = None) -> Dict[str, Any]:
        """Get analysis history for a property or all properties"""
        if property_id:
            return self.analysis_history.get(property_id, {})
        return self.analysis_history
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get analyst agent performance metrics"""
        return {
            "analyses_completed_today": self.analyses_completed_today,
            "total_analyses_completed": self.total_analyses_completed,
            "average_analysis_time": self.average_analysis_time,
            "accuracy_score": self.accuracy_score,
            "cache_hit_rate": len(self.market_cache) / max(1, self.total_analyses_completed),
            "agent_metrics": self.get_metrics().dict()
        }