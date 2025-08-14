"""
Portfolio Agent - Investment Management and Optimization
Specialized agent for portfolio tracking, performance analysis, and investment optimization
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
from .portfolio_models import (
    Portfolio, PropertyPerformance, PortfolioAnalysis, PortfolioOptimization,
    InvestmentRecommendation, RiskAssessment, MarketAnalysis, PerformanceMetrics
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PortfolioAgent(BaseAgent):
    """
    Portfolio Agent - Investment Management and Optimization
    
    Responsibilities:
    - Track portfolio performance metrics for all properties
    - Identify underperforming assets and suggest optimization strategies
    - Recommend diversification strategies based on current holdings
    - Integrate with accounting systems for real-time financial reporting
    - Provide maintenance tracking and expense management
    - Analyze market conditions for buying, holding, or selling recommendations
    - Generate performance reports and investment insights
    - Optimize portfolio allocation and risk management
    """
    
    def __init__(self, name: str = "PortfolioAgent", description: str = "Investment portfolio management agent"):
        # Define agent capabilities
        capabilities = [
            AgentCapability(
                name="portfolio_tracking",
                description="Track performance metrics for all properties in portfolio",
                input_schema={
                    "portfolio_id": "str",
                    "properties": "List[Dict[str, Any]]"
                },
                output_schema={
                    "performance_metrics": "PerformanceMetrics",
                    "property_performances": "List[PropertyPerformance]"
                },
                required_tools=["portfolio_tracker", "performance_calculator"],
                estimated_duration=120
            ),
            AgentCapability(
                name="performance_analysis",
                description="Analyze portfolio performance and identify optimization opportunities",
                input_schema={
                    "portfolio": "Portfolio",
                    "market_data": "Dict[str, Any]"
                },
                output_schema={
                    "analysis": "PortfolioAnalysis",
                    "recommendations": "List[InvestmentRecommendation]"
                },
                required_tools=["performance_analyzer", "market_data"],
                estimated_duration=180
            ),
            AgentCapability(
                name="optimization_recommendations",
                description="Generate portfolio optimization recommendations",
                input_schema={
                    "portfolio": "Portfolio",
                    "analysis": "PortfolioAnalysis",
                    "investment_goals": "Dict[str, Any]"
                },
                output_schema={
                    "optimization": "PortfolioOptimization",
                    "action_plan": "List[Dict[str, Any]]"
                },
                required_tools=["optimization_engine", "strategy_analyzer"],
                estimated_duration=150
            ),
            AgentCapability(
                name="market_condition_analysis",
                description="Analyze market conditions for investment decisions",
                input_schema={
                    "geographic_areas": "List[str]",
                    "property_types": "List[str]"
                },
                output_schema={
                    "market_analysis": "MarketAnalysis",
                    "investment_timing": "Dict[str, Any]"
                },
                required_tools=["market_analyzer", "trend_predictor"],
                estimated_duration=90
            ),
            AgentCapability(
                name="risk_assessment",
                description="Assess portfolio risk and generate mitigation strategies",
                input_schema={
                    "portfolio": "Portfolio",
                    "market_conditions": "Dict[str, Any]"
                },
                output_schema={
                    "risk_assessment": "RiskAssessment",
                    "mitigation_strategies": "List[Dict[str, Any]]"
                },
                required_tools=["risk_analyzer", "scenario_modeler"],
                estimated_duration=120
            )
        ]
        
        # Portfolio-specific attributes (initialize before base agent)
        self.portfolios: Dict[str, Portfolio] = {}
        self.performance_history: Dict[str, List[PerformanceMetrics]] = {}
        self.optimization_cache: Dict[str, PortfolioOptimization] = {}
        
        # Portfolio configuration
        self.default_performance_targets = {
            "min_cap_rate": 0.08,
            "min_cash_flow": 200,
            "min_roi": 0.15,
            "max_vacancy_rate": 0.05,
            "target_diversification": 0.7
        }
        
        # Risk management parameters
        self.risk_thresholds = {
            "concentration_limit": 0.3,  # Max 30% in single market
            "leverage_limit": 0.8,       # Max 80% LTV
            "cash_reserve_ratio": 0.1,   # 10% cash reserves
            "maintenance_reserve": 0.05   # 5% for maintenance
        }
        
        # Performance metrics
        self.analyses_completed_today = 0
        self.total_analyses_completed = 0
        self.average_analysis_time = 0.0
        self.optimization_success_rate = 0.0
        
        # Initialize agent executor
        self.agent_executor: Optional[AgentExecutor] = None
        
        # Initialize workflows
        self.workflows: Optional['PortfolioWorkflows'] = None
        
        # Initialize base agent
        super().__init__(
            agent_type=AgentType.PORTFOLIO,
            name=name,
            description=description,
            capabilities=capabilities
        )
        
        # Setup agent executor after base initialization
        self._setup_agent_executor()
        
        # Initialize workflows (import here to avoid circular import)
        from .portfolio_workflows import PortfolioWorkflows
        self.workflows = PortfolioWorkflows(self)
    
    def _agent_specific_initialization(self):
        """Portfolio agent specific initialization"""
        logger.info("Initializing Portfolio Agent...")
        
        # Set up default portfolio parameters
        self._setup_default_parameters()
        
        # Initialize performance tracking
        self._initialize_performance_tracking()
        
        # Set up portfolio workflows
        self._setup_portfolio_workflows()
        
        logger.info("Portfolio Agent initialization complete")
    
    def _setup_default_parameters(self):
        """Set up default portfolio parameters"""
        self.portfolio_parameters = {
            "performance_tracking": {
                "update_frequency": "daily",
                "metrics_retention": 365,  # days
                "benchmark_comparison": True,
                "automated_alerts": True
            },
            "optimization": {
                "rebalance_threshold": 0.05,  # 5% deviation
                "optimization_frequency": "monthly",
                "risk_tolerance": "moderate",
                "diversification_targets": {
                    "geographic": 0.3,  # Max 30% in single market
                    "property_type": 0.4,  # Max 40% in single type
                    "strategy": 0.5  # Max 50% in single strategy
                }
            },
            "reporting": {
                "report_frequency": "monthly",
                "include_projections": True,
                "benchmark_indices": ["REITs", "S&P500", "Local_Market"],
                "tax_optimization": True
            }
        }
    
    def _initialize_performance_tracking(self):
        """Initialize performance tracking system"""
        self.performance_cache = {}
        self.cache_expiry = timedelta(hours=1)  # Cache expires after 1 hour
        self.last_performance_update = datetime.now()
    
    def _setup_portfolio_workflows(self):
        """Set up portfolio workflows"""
        self.portfolio_workflows = {
            "comprehensive_analysis": [
                "portfolio_tracking",
                "performance_analysis",
                "market_condition_analysis",
                "risk_assessment",
                "optimization_recommendations"
            ],
            "performance_review": [
                "portfolio_tracking",
                "performance_analysis"
            ],
            "optimization": [
                "performance_analysis",
                "optimization_recommendations"
            ],
            "risk_review": [
                "risk_assessment",
                "market_condition_analysis"
            ]
        }
    
    def _setup_agent_executor(self):
        """Set up the LangChain agent executor"""
        try:
            # Get available tools for portfolio agent
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
            
            logger.info(f"Portfolio agent executor created with {len(langchain_tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to setup portfolio agent executor: {e}")
            self.agent_executor = None
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the portfolio agent"""
        return """
        You are an expert real estate portfolio management agent specializing in investment optimization and performance analysis.
        
        Your primary mission is to:
        1. Track and analyze portfolio performance across all properties
        2. Identify underperforming assets and optimization opportunities
        3. Recommend diversification strategies and risk management
        4. Provide market-based buy/hold/sell recommendations
        5. Generate comprehensive performance reports and insights
        6. Optimize portfolio allocation for maximum returns
        
        Key Responsibilities:
        - Portfolio Tracking: Monitor performance metrics for all properties
        - Performance Analysis: Analyze returns, cash flow, and appreciation
        - Optimization: Recommend portfolio improvements and rebalancing
        - Risk Management: Assess and mitigate portfolio risks
        - Market Analysis: Consider market conditions for investment decisions
        - Reporting: Generate detailed performance and optimization reports
        
        Analysis Standards:
        - Track key metrics: cap rate, cash flow, ROI, appreciation, vacancy
        - Compare performance against benchmarks and targets
        - Consider geographic and property type diversification
        - Assess risk factors and concentration limits
        - Provide actionable optimization recommendations
        - Include market timing considerations
        
        Performance Targets:
        - Minimum 8% cap rate for rental properties
        - Minimum $200 monthly cash flow per property
        - Maximum 5% vacancy rate
        - Geographic diversification across multiple markets
        - Property type diversification
        
        Risk Management:
        - Maximum 30% concentration in single market
        - Maximum 80% leverage ratio
        - Maintain 10% cash reserves
        - Monitor market cycle timing
        - Assess tenant and income stability
        
        Communication Style:
        - Provide data-driven analysis with specific metrics
        - Use clear visualizations and comparisons
        - Highlight key opportunities and risks
        - Structure recommendations by priority
        - Include implementation timelines
        - Focus on actionable insights
        
        Always prioritize portfolio optimization for long-term wealth building while managing downside risk.
        """
    
    # Core Agent Methods
    
    async def execute_task(self, task: str, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute a specific portfolio task"""
        logger.info(f"Portfolio agent executing task: {task}")
        
        try:
            if task == "analyze_portfolio":
                return await self._analyze_portfolio(data, state)
            elif task == "track_performance":
                return await self._execute_tracking_workflow(data, state)
            elif task == "optimize_portfolio":
                return await self._execute_optimization_workflow(data, state)
            elif task == "assess_risk":
                return await self._execute_risk_workflow(data, state)
            elif task == "analyze_market":
                return await self._execute_market_workflow(data, state)
            elif task == "generate_report":
                return await self._generate_performance_report(data, state)
            else:
                raise ValueError(f"Unknown task: {task}")
                
        except Exception as e:
            logger.error(f"Error executing portfolio task {task}: {e}")
            return {
                "success": False,
                "error": str(e),
                "task": task
            }
    
    async def _execute_tracking_workflow(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute portfolio tracking workflow"""
        if not self.workflows:
            return {"success": False, "error": "Workflows not initialized"}
        
        portfolio_data = data.get("portfolio", {})
        result = await self.workflows.execute_portfolio_tracking_workflow(portfolio_data, state)
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time,
            "confidence_score": result.confidence_score
        }
    
    async def _execute_optimization_workflow(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute portfolio optimization workflow"""
        if not self.workflows:
            return {"success": False, "error": "Workflows not initialized"}
        
        portfolio_data = data.get("portfolio", {})
        analysis_data = data.get("analysis", {})
        goals_data = data.get("investment_goals", {})
        
        result = await self.workflows.execute_optimization_workflow(
            portfolio_data, analysis_data, goals_data, state
        )
        
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
        
        portfolio_data = data.get("portfolio", {})
        market_data = data.get("market_conditions", {})
        
        result = await self.workflows.execute_risk_assessment_workflow(
            portfolio_data, market_data, state
        )
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time,
            "confidence_score": result.confidence_score
        }
    
    async def _execute_market_workflow(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute market analysis workflow"""
        if not self.workflows:
            return {"success": False, "error": "Workflows not initialized"}
        
        geographic_areas = data.get("geographic_areas", [])
        property_types = data.get("property_types", [])
        
        result = await self.workflows.execute_market_analysis_workflow(
            geographic_areas, property_types, state
        )
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time,
            "confidence_score": result.confidence_score
        }
    
    async def process_state(self, state: AgentState) -> AgentState:
        """Process the current state and manage portfolio"""
        logger.info("Portfolio agent processing state...")
        
        try:
            # Get current portfolio status
            portfolio_status = state.get("portfolio_status", {})
            closed_deals = state.get("closed_deals", [])
            
            # Check if there are new properties to add to portfolio
            new_properties = [
                deal for deal in closed_deals
                if not deal.get("added_to_portfolio", False)
            ]
            
            if new_properties:
                # Add new properties to portfolio tracking
                await self._add_properties_to_portfolio(new_properties, state)
            
            # Perform regular portfolio analysis
            if self._should_perform_analysis():
                analysis_result = await self._analyze_portfolio({}, state)
                
                if analysis_result.get("success", False):
                    # Update portfolio status in state
                    portfolio_analysis = analysis_result.get("analysis", {})
                    state["portfolio_status"] = portfolio_analysis.get("portfolio_metrics", {})
                    state["portfolio_performance"] = portfolio_analysis.get("performance_data", {})
                    
                    # Check for optimization opportunities
                    optimization_needed = self._check_optimization_needed(portfolio_analysis)
                    
                    if optimization_needed:
                        # Generate optimization recommendations
                        optimization_result = await self._execute_optimization_workflow(
                            {"portfolio": portfolio_analysis}, state
                        )
                        
                        if optimization_result.get("success", False):
                            # Add optimization recommendations to state
                            recommendations = optimization_result.get("data", {}).get("recommendations", [])
                            
                            state = StateManager.add_agent_message(
                                state,
                                AgentType.PORTFOLIO,
                                f"Generated {len(recommendations)} portfolio optimization recommendations",
                                data={
                                    "recommendations": recommendations,
                                    "optimization_priority": "high" if len(recommendations) > 3 else "medium"
                                },
                                priority=2
                            )
            
            # Update performance metrics
            self.analyses_completed_today += 1
            self.total_analyses_completed += 1
            
            return state
            
        except Exception as e:
            logger.error(f"Error in portfolio agent state processing: {e}")
            state = StateManager.add_agent_message(
                state,
                AgentType.PORTFOLIO,
                f"Error in portfolio agent: {str(e)}",
                priority=4
            )
            return state
    
    def get_available_tasks(self) -> List[str]:
        """Get list of tasks this agent can perform"""
        return [
            "analyze_portfolio",
            "track_performance",
            "optimize_portfolio",
            "assess_risk",
            "analyze_market",
            "generate_report"
        ]
    
    def get_available_workflows(self) -> List[str]:
        """Get list of workflows this agent can execute"""
        return [
            "portfolio_tracking",
            "performance_analysis",
            "optimization_recommendations",
            "risk_assessment",
            "market_condition_analysis"
        ]
    
    async def execute_workflow(self, workflow_name: str, portfolio_data: Dict[str, Any], 
                              state: AgentState, **kwargs):
        """Execute a specific workflow"""
        from .portfolio_workflows import WorkflowResult
        
        if not self.workflows:
            return WorkflowResult(
                workflow_name=workflow_name,
                success=False,
                error="Workflows not initialized"
            )
        
        try:
            if workflow_name == "portfolio_tracking":
                return await self.workflows.execute_portfolio_tracking_workflow(portfolio_data, state)
            elif workflow_name == "performance_analysis":
                market_data = kwargs.get("market_data", {})
                return await self.workflows.execute_performance_analysis_workflow(
                    portfolio_data, market_data, state
                )
            elif workflow_name == "optimization_recommendations":
                analysis_data = kwargs.get("analysis_data", {})
                goals_data = kwargs.get("investment_goals", {})
                return await self.workflows.execute_optimization_workflow(
                    portfolio_data, analysis_data, goals_data, state
                )
            elif workflow_name == "risk_assessment":
                market_data = kwargs.get("market_conditions", {})
                return await self.workflows.execute_risk_assessment_workflow(
                    portfolio_data, market_data, state
                )
            elif workflow_name == "market_condition_analysis":
                geographic_areas = kwargs.get("geographic_areas", [])
                property_types = kwargs.get("property_types", [])
                return await self.workflows.execute_market_analysis_workflow(
                    geographic_areas, property_types, state
                )
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
    
    async def _analyze_portfolio(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Perform comprehensive portfolio analysis using workflows"""
        try:
            logger.info("Starting comprehensive portfolio analysis")
            
            if not self.workflows:
                return {
                    "success": False,
                    "error": "Workflows not initialized"
                }
            
            # Get portfolio data from state or data parameter
            portfolio_data = data.get("portfolio") or state.get("portfolio_status", {})
            closed_deals = state.get("closed_deals", [])
            
            # Build portfolio from closed deals if not provided
            if not portfolio_data and closed_deals:
                portfolio_data = self._build_portfolio_from_deals(closed_deals)
            
            if not portfolio_data:
                return {
                    "success": False,
                    "error": "No portfolio data available for analysis"
                }
            
            # Execute analysis workflows in sequence
            workflow_results = {}
            
            # 1. Portfolio Tracking Workflow
            logger.info("Executing portfolio tracking workflow...")
            tracking_result = await self.workflows.execute_portfolio_tracking_workflow(
                portfolio_data, state
            )
            workflow_results["portfolio_tracking"] = tracking_result
            
            if not tracking_result.success:
                logger.error(f"Portfolio tracking failed: {tracking_result.error}")
                return {
                    "success": False,
                    "error": f"Portfolio tracking failed: {tracking_result.error}"
                }
            
            # 2. Performance Analysis Workflow
            logger.info("Executing performance analysis workflow...")
            market_data = state.get("market_conditions", {})
            performance_result = await self.workflows.execute_performance_analysis_workflow(
                portfolio_data, market_data, state
            )
            workflow_results["performance_analysis"] = performance_result
            
            # 3. Risk Assessment Workflow
            logger.info("Executing risk assessment workflow...")
            risk_result = await self.workflows.execute_risk_assessment_workflow(
                portfolio_data, market_data, state
            )
            workflow_results["risk_assessment"] = risk_result
            
            # 4. Market Analysis Workflow
            logger.info("Executing market analysis workflow...")
            geographic_areas = self._extract_geographic_areas(portfolio_data)
            property_types = self._extract_property_types(portfolio_data)
            market_result = await self.workflows.execute_market_analysis_workflow(
                geographic_areas, property_types, state
            )
            workflow_results["market_analysis"] = market_result
            
            # 5. Optimization Workflow
            logger.info("Executing optimization workflow...")
            analysis_data = performance_result.data if performance_result.success else {}
            investment_goals = state.get("investment_strategy", {})
            optimization_result = await self.workflows.execute_optimization_workflow(
                portfolio_data, analysis_data, investment_goals, state
            )
            workflow_results["optimization"] = optimization_result
            
            # Compile comprehensive analysis results
            analysis = {
                "portfolio_metrics": tracking_result.data if tracking_result.success else {},
                "performance_data": performance_result.data if performance_result.success else {},
                "risk_assessment": risk_result.data if risk_result.success else {},
                "market_analysis": market_result.data if market_result.success else {},
                "optimization_recommendations": optimization_result.data if optimization_result.success else {},
                "workflow_results": workflow_results,
                "analysis_timestamp": datetime.now().isoformat(),
                "confidence_level": self._calculate_overall_confidence(workflow_results)
            }
            
            # Store analysis in history
            portfolio_id = portfolio_data.get("id", "default")
            if portfolio_id not in self.performance_history:
                self.performance_history[portfolio_id] = []
            
            self.performance_history[portfolio_id].append({
                "timestamp": datetime.now(),
                "analysis": analysis
            })
            
            logger.info("Comprehensive portfolio analysis completed successfully")
            
            return {
                "success": True,
                "analysis": analysis,
                "execution_time": sum([
                    r.execution_time for r in workflow_results.values() 
                    if hasattr(r, 'execution_time') and r.execution_time
                ]),
                "confidence_score": analysis["confidence_level"]
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive portfolio analysis: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_portfolio_from_deals(self, closed_deals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build portfolio data structure from closed deals"""
        properties = []
        total_value = 0.0
        total_equity = 0.0
        monthly_cash_flow = 0.0
        
        for deal in closed_deals:
            property_data = {
                "id": deal.get("id"),
                "address": deal.get("property_address"),
                "city": deal.get("city"),
                "state": deal.get("state"),
                "property_type": deal.get("property_type"),
                "acquisition_cost": deal.get("listing_price", 0),
                "current_value": deal.get("estimated_value", 0),
                "monthly_rent": deal.get("analysis_data", {}).get("monthly_rent", 0),
                "monthly_expenses": deal.get("analysis_data", {}).get("monthly_expenses", 0),
                "acquisition_date": deal.get("discovered_at")
            }
            
            properties.append(property_data)
            total_value += property_data["current_value"]
            total_equity += property_data["current_value"] - property_data["acquisition_cost"]
            monthly_cash_flow += property_data["monthly_rent"] - property_data["monthly_expenses"]
        
        return {
            "id": "main_portfolio",
            "name": "Main Investment Portfolio",
            "properties": properties,
            "total_properties": len(properties),
            "total_value": total_value,
            "total_equity": total_equity,
            "monthly_cash_flow": monthly_cash_flow,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
    
    def _extract_geographic_areas(self, portfolio_data: Dict[str, Any]) -> List[str]:
        """Extract unique geographic areas from portfolio"""
        areas = set()
        for prop in portfolio_data.get("properties", []):
            city = prop.get("city")
            state = prop.get("state")
            if city and state:
                areas.add(f"{city}, {state}")
        return list(areas)
    
    def _extract_property_types(self, portfolio_data: Dict[str, Any]) -> List[str]:
        """Extract unique property types from portfolio"""
        types = set()
        for prop in portfolio_data.get("properties", []):
            prop_type = prop.get("property_type")
            if prop_type:
                types.add(prop_type)
        return list(types)
    
    def _calculate_overall_confidence(self, workflow_results: Dict[str, Any]) -> float:
        """Calculate overall confidence score from workflow results"""
        confidence_scores = []
        
        for result in workflow_results.values():
            if hasattr(result, 'confidence_score') and result.confidence_score:
                confidence_scores.append(result.confidence_score)
        
        if not confidence_scores:
            return 0.8  # Default confidence
        
        return sum(confidence_scores) / len(confidence_scores)
    
    def _should_perform_analysis(self) -> bool:
        """Check if portfolio analysis should be performed"""
        # Perform analysis if it's been more than 24 hours since last update
        time_since_update = datetime.now() - self.last_performance_update
        return time_since_update > timedelta(hours=24)
    
    def _check_optimization_needed(self, portfolio_analysis: Dict[str, Any]) -> bool:
        """Check if portfolio optimization is needed"""
        performance_data = portfolio_analysis.get("performance_data", {})
        
        # Check if any metrics are below targets
        cap_rate = performance_data.get("average_cap_rate", 0)
        cash_flow = performance_data.get("monthly_cash_flow", 0)
        roi = performance_data.get("average_roi", 0)
        
        return (
            cap_rate < self.default_performance_targets["min_cap_rate"] or
            cash_flow < self.default_performance_targets["min_cash_flow"] or
            roi < self.default_performance_targets["min_roi"]
        )
    
    async def _add_properties_to_portfolio(self, new_properties: List[Dict[str, Any]], 
                                         state: AgentState):
        """Add new properties to portfolio tracking"""
        for prop in new_properties:
            # Mark as added to portfolio
            prop["added_to_portfolio"] = True
            prop["portfolio_added_date"] = datetime.now().isoformat()
            
            logger.info(f"Added property {prop.get('property_address')} to portfolio tracking")
        
        # Update last performance update time
        self.last_performance_update = datetime.now()
    
    async def _generate_performance_report(self, data: Dict[str, Any], 
                                         state: AgentState) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        try:
            portfolio_data = data.get("portfolio") or state.get("portfolio_status", {})
            report_type = data.get("report_type", "comprehensive")
            
            if not portfolio_data:
                return {
                    "success": False,
                    "error": "No portfolio data available for reporting"
                }
            
            # Generate report based on type
            if report_type == "comprehensive":
                # Perform full analysis first
                analysis_result = await self._analyze_portfolio(data, state)
                
                if not analysis_result.get("success", False):
                    return analysis_result
                
                analysis = analysis_result["analysis"]
                
                report = {
                    "report_type": "comprehensive",
                    "generated_at": datetime.now().isoformat(),
                    "portfolio_summary": analysis.get("portfolio_metrics", {}),
                    "performance_analysis": analysis.get("performance_data", {}),
                    "risk_assessment": analysis.get("risk_assessment", {}),
                    "market_analysis": analysis.get("market_analysis", {}),
                    "optimization_recommendations": analysis.get("optimization_recommendations", {}),
                    "executive_summary": self._generate_executive_summary(analysis),
                    "action_items": self._extract_action_items(analysis)
                }
            else:
                # Generate basic performance report
                report = {
                    "report_type": "basic",
                    "generated_at": datetime.now().isoformat(),
                    "portfolio_summary": portfolio_data,
                    "basic_metrics": self._calculate_basic_metrics(portfolio_data)
                }
            
            return {
                "success": True,
                "report": report,
                "report_id": str(uuid.uuid4())
            }
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_executive_summary(self, analysis: Dict[str, Any]) -> str:
        """Generate executive summary from analysis"""
        portfolio_metrics = analysis.get("portfolio_metrics", {})
        performance_data = analysis.get("performance_data", {})
        
        total_properties = portfolio_metrics.get("total_properties", 0)
        total_value = portfolio_metrics.get("total_value", 0)
        monthly_cash_flow = performance_data.get("monthly_cash_flow", 0)
        average_cap_rate = performance_data.get("average_cap_rate", 0)
        
        return f"""
        Portfolio consists of {total_properties} properties with total value of ${total_value:,.2f}.
        Current monthly cash flow is ${monthly_cash_flow:,.2f} with average cap rate of {average_cap_rate:.2%}.
        Portfolio performance is {'above' if average_cap_rate > 0.08 else 'below'} target metrics.
        """
    
    def _extract_action_items(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract action items from analysis"""
        action_items = []
        
        optimization_recs = analysis.get("optimization_recommendations", {})
        risk_assessment = analysis.get("risk_assessment", {})
        
        # Add optimization actions
        recommendations = optimization_recs.get("recommendations", [])
        for rec in recommendations[:3]:  # Top 3 recommendations
            action_items.append(f"Optimization: {rec.get('description', 'Review recommendation')}")
        
        # Add risk mitigation actions
        risk_factors = risk_assessment.get("risk_factors", [])
        for risk in risk_factors[:2]:  # Top 2 risks
            action_items.append(f"Risk Mitigation: Address {risk}")
        
        return action_items
    
    def _calculate_basic_metrics(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate basic portfolio metrics"""
        properties = portfolio_data.get("properties", [])
        
        if not properties:
            return {}
        
        total_value = sum(prop.get("current_value", 0) for prop in properties)
        total_rent = sum(prop.get("monthly_rent", 0) for prop in properties)
        total_expenses = sum(prop.get("monthly_expenses", 0) for prop in properties)
        
        return {
            "total_properties": len(properties),
            "total_value": total_value,
            "monthly_rent": total_rent,
            "monthly_expenses": total_expenses,
            "monthly_cash_flow": total_rent - total_expenses,
            "average_property_value": total_value / len(properties) if properties else 0
        }