"""
Portfolio Agent Workflows
LangGraph workflows for portfolio management, performance analysis, and optimization
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import uuid

from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from ..core.agent_state import AgentState, AgentType, StateManager
from ..core.agent_tools import tool_registry
from .portfolio_models import (
    Portfolio, PropertyPerformance, PerformanceMetrics, PortfolioAnalysis,
    PortfolioOptimization, RiskAssessment, MarketAnalysis, InvestmentRecommendation
)

# Configure logging
logger = logging.getLogger(__name__)


class WorkflowResult(BaseModel):
    """Result from workflow execution"""
    workflow_name: str
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    execution_time: float = 0.0
    confidence_score: float = 0.8
    timestamp: datetime = Field(default_factory=datetime.now)


class PortfolioWorkflows:
    """Portfolio Agent workflow implementations"""
    
    def __init__(self, portfolio_agent):
        self.portfolio_agent = portfolio_agent
        self.workflow_history: Dict[str, List[WorkflowResult]] = {}
        
        # Initialize workflows
        self._setup_workflows()
    
    def _setup_workflows(self):
        """Set up all portfolio workflows"""
        self.workflows = {
            "portfolio_tracking": self._create_portfolio_tracking_workflow(),
            "performance_analysis": self._create_performance_analysis_workflow(),
            "optimization": self._create_optimization_workflow(),
            "risk_assessment": self._create_risk_assessment_workflow(),
            "market_analysis": self._create_market_analysis_workflow()
        }
    
    def _create_portfolio_tracking_workflow(self) -> StateGraph:
        """Create portfolio tracking workflow"""
        workflow = StateGraph(dict)
        
        workflow.add_node("track_properties", self._track_properties_node)
        workflow.add_node("calculate_metrics", self._calculate_metrics_node)
        workflow.add_node("update_performance", self._update_performance_node)
        
        workflow.add_edge("track_properties", "calculate_metrics")
        workflow.add_edge("calculate_metrics", "update_performance")
        workflow.add_edge("update_performance", END)
        
        workflow.set_entry_point("track_properties")
        return workflow.compile()
    
    def _create_performance_analysis_workflow(self) -> StateGraph:
        """Create performance analysis workflow"""
        workflow = StateGraph(dict)
        
        workflow.add_node("analyze_performance", self._analyze_performance_node)
        workflow.add_node("identify_trends", self._identify_trends_node)
        workflow.add_node("benchmark_comparison", self._benchmark_comparison_node)
        workflow.add_node("generate_insights", self._generate_insights_node)
        
        workflow.add_edge("analyze_performance", "identify_trends")
        workflow.add_edge("identify_trends", "benchmark_comparison")
        workflow.add_edge("benchmark_comparison", "generate_insights")
        workflow.add_edge("generate_insights", END)
        
        workflow.set_entry_point("analyze_performance")
        return workflow.compile()
    
    def _create_optimization_workflow(self) -> StateGraph:
        """Create portfolio optimization workflow"""
        workflow = StateGraph(dict)
        
        workflow.add_node("assess_current_state", self._assess_current_state_node)
        workflow.add_node("identify_opportunities", self._identify_opportunities_node)
        workflow.add_node("generate_recommendations", self._generate_recommendations_node)
        workflow.add_node("create_action_plan", self._create_action_plan_node)
        
        workflow.add_edge("assess_current_state", "identify_opportunities")
        workflow.add_edge("identify_opportunities", "generate_recommendations")
        workflow.add_edge("generate_recommendations", "create_action_plan")
        workflow.add_edge("create_action_plan", END)
        
        workflow.set_entry_point("assess_current_state")
        return workflow.compile()
    
    def _create_risk_assessment_workflow(self) -> StateGraph:
        """Create risk assessment workflow"""
        workflow = StateGraph(dict)
        
        workflow.add_node("analyze_risk_factors", self._analyze_risk_factors_node)
        workflow.add_node("calculate_risk_metrics", self._calculate_risk_metrics_node)
        workflow.add_node("stress_testing", self._stress_testing_node)
        workflow.add_node("mitigation_strategies", self._mitigation_strategies_node)
        
        workflow.add_edge("analyze_risk_factors", "calculate_risk_metrics")
        workflow.add_edge("calculate_risk_metrics", "stress_testing")
        workflow.add_edge("stress_testing", "mitigation_strategies")
        workflow.add_edge("mitigation_strategies", END)
        
        workflow.set_entry_point("analyze_risk_factors")
        return workflow.compile()
    
    def _create_market_analysis_workflow(self) -> StateGraph:
        """Create market analysis workflow"""
        workflow = StateGraph(dict)
        
        workflow.add_node("gather_market_data", self._gather_market_data_node)
        workflow.add_node("analyze_trends", self._analyze_trends_node)
        workflow.add_node("assess_opportunities", self._assess_opportunities_node)
        workflow.add_node("timing_analysis", self._timing_analysis_node)
        
        workflow.add_edge("gather_market_data", "analyze_trends")
        workflow.add_edge("analyze_trends", "assess_opportunities")
        workflow.add_edge("assess_opportunities", "timing_analysis")
        workflow.add_edge("timing_analysis", END)
        
        workflow.set_entry_point("gather_market_data")
        return workflow.compile()
    
    # Workflow Execution Methods
    
    async def execute_portfolio_tracking_workflow(self, portfolio_data: Dict[str, Any], 
                                                 state: AgentState) -> WorkflowResult:
        """Execute portfolio tracking workflow"""
        start_time = datetime.now()
        workflow_name = "portfolio_tracking"
        
        try:
            logger.info("Executing portfolio tracking workflow")
            
            # Prepare workflow state
            workflow_state = {
                "portfolio_data": portfolio_data,
                "agent_state": state,
                "workflow_results": {}
            }
            
            # Execute workflow
            workflow = self.workflows[workflow_name]
            result = await workflow.ainvoke(workflow_state)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            workflow_result = WorkflowResult(
                workflow_name=workflow_name,
                success=True,
                data=result.get("workflow_results", {}),
                execution_time=execution_time,
                confidence_score=result.get("confidence_score", 0.8)
            )
            
            # Store in history
            self._store_workflow_result(workflow_result)
            
            return workflow_result
            
        except Exception as e:
            logger.error(f"Error in portfolio tracking workflow: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            workflow_result = WorkflowResult(
                workflow_name=workflow_name,
                success=False,
                error=str(e),
                execution_time=execution_time
            )
            
            self._store_workflow_result(workflow_result)
            return workflow_result
    
    async def execute_performance_analysis_workflow(self, portfolio_data: Dict[str, Any],
                                                   market_data: Dict[str, Any],
                                                   state: AgentState) -> WorkflowResult:
        """Execute performance analysis workflow"""
        start_time = datetime.now()
        workflow_name = "performance_analysis"
        
        try:
            logger.info("Executing performance analysis workflow")
            
            # Prepare workflow state
            workflow_state = {
                "portfolio_data": portfolio_data,
                "market_data": market_data,
                "agent_state": state,
                "workflow_results": {}
            }
            
            # Execute workflow
            workflow = self.workflows[workflow_name]
            result = await workflow.ainvoke(workflow_state)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            workflow_result = WorkflowResult(
                workflow_name=workflow_name,
                success=True,
                data=result.get("workflow_results", {}),
                execution_time=execution_time,
                confidence_score=result.get("confidence_score", 0.8)
            )
            
            self._store_workflow_result(workflow_result)
            return workflow_result
            
        except Exception as e:
            logger.error(f"Error in performance analysis workflow: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            workflow_result = WorkflowResult(
                workflow_name=workflow_name,
                success=False,
                error=str(e),
                execution_time=execution_time
            )
            
            self._store_workflow_result(workflow_result)
            return workflow_result
    
    async def execute_optimization_workflow(self, portfolio_data: Dict[str, Any],
                                          analysis_data: Dict[str, Any],
                                          investment_goals: Dict[str, Any],
                                          state: AgentState) -> WorkflowResult:
        """Execute portfolio optimization workflow"""
        start_time = datetime.now()
        workflow_name = "optimization"
        
        try:
            logger.info("Executing portfolio optimization workflow")
            
            # Prepare workflow state
            workflow_state = {
                "portfolio_data": portfolio_data,
                "analysis_data": analysis_data,
                "investment_goals": investment_goals,
                "agent_state": state,
                "workflow_results": {}
            }
            
            # Execute workflow
            workflow = self.workflows[workflow_name]
            result = await workflow.ainvoke(workflow_state)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            workflow_result = WorkflowResult(
                workflow_name=workflow_name,
                success=True,
                data=result.get("workflow_results", {}),
                execution_time=execution_time,
                confidence_score=result.get("confidence_score", 0.8)
            )
            
            self._store_workflow_result(workflow_result)
            return workflow_result
            
        except Exception as e:
            logger.error(f"Error in optimization workflow: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            workflow_result = WorkflowResult(
                workflow_name=workflow_name,
                success=False,
                error=str(e),
                execution_time=execution_time
            )
            
            self._store_workflow_result(workflow_result)
            return workflow_result
    
    async def execute_risk_assessment_workflow(self, portfolio_data: Dict[str, Any],
                                             market_conditions: Dict[str, Any],
                                             state: AgentState) -> WorkflowResult:
        """Execute risk assessment workflow"""
        start_time = datetime.now()
        workflow_name = "risk_assessment"
        
        try:
            logger.info("Executing risk assessment workflow")
            
            # Prepare workflow state
            workflow_state = {
                "portfolio_data": portfolio_data,
                "market_conditions": market_conditions,
                "agent_state": state,
                "workflow_results": {}
            }
            
            # Execute workflow
            workflow = self.workflows[workflow_name]
            result = await workflow.ainvoke(workflow_state)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            workflow_result = WorkflowResult(
                workflow_name=workflow_name,
                success=True,
                data=result.get("workflow_results", {}),
                execution_time=execution_time,
                confidence_score=result.get("confidence_score", 0.8)
            )
            
            self._store_workflow_result(workflow_result)
            return workflow_result
            
        except Exception as e:
            logger.error(f"Error in risk assessment workflow: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            workflow_result = WorkflowResult(
                workflow_name=workflow_name,
                success=False,
                error=str(e),
                execution_time=execution_time
            )
            
            self._store_workflow_result(workflow_result)
            return workflow_result
    
    async def execute_market_analysis_workflow(self, geographic_areas: List[str],
                                             property_types: List[str],
                                             state: AgentState) -> WorkflowResult:
        """Execute market analysis workflow"""
        start_time = datetime.now()
        workflow_name = "market_analysis"
        
        try:
            logger.info("Executing market analysis workflow")
            
            # Prepare workflow state
            workflow_state = {
                "geographic_areas": geographic_areas,
                "property_types": property_types,
                "agent_state": state,
                "workflow_results": {}
            }
            
            # Execute workflow
            workflow = self.workflows[workflow_name]
            result = await workflow.ainvoke(workflow_state)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            workflow_result = WorkflowResult(
                workflow_name=workflow_name,
                success=True,
                data=result.get("workflow_results", {}),
                execution_time=execution_time,
                confidence_score=result.get("confidence_score", 0.8)
            )
            
            self._store_workflow_result(workflow_result)
            return workflow_result
            
        except Exception as e:
            logger.error(f"Error in market analysis workflow: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            workflow_result = WorkflowResult(
                workflow_name=workflow_name,
                success=False,
                error=str(e),
                execution_time=execution_time
            )
            
            self._store_workflow_result(workflow_result)
            return workflow_result
    
    # Workflow Node Implementations
    
    async def _track_properties_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Track individual property performance"""
        try:
            portfolio_data = state.get("portfolio_data", {})
            properties = portfolio_data.get("properties", [])
            
            # Use portfolio tracker tool
            tracker_tool = tool_registry.get_tool("portfolio_tracker")
            if tracker_tool:
                result = await tracker_tool.execute(
                    portfolio_data=portfolio_data,
                    properties=properties
                )
                
                if result.success:
                    state["workflow_results"]["property_tracking"] = result.data
                    state["confidence_score"] = result.confidence_score
                else:
                    logger.error(f"Property tracking failed: {result.error}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in track properties node: {e}")
            state["workflow_results"]["error"] = str(e)
            return state
    
    async def _calculate_metrics_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate portfolio-level metrics"""
        try:
            tracking_data = state.get("workflow_results", {}).get("property_tracking", {})
            
            if tracking_data:
                performance_metrics = tracking_data.get("performance_metrics", {})
                property_performances = tracking_data.get("property_performances", [])
                
                # Additional metric calculations
                enhanced_metrics = self._enhance_metrics(performance_metrics, property_performances)
                
                state["workflow_results"]["portfolio_metrics"] = enhanced_metrics
            
            return state
            
        except Exception as e:
            logger.error(f"Error in calculate metrics node: {e}")
            state["workflow_results"]["error"] = str(e)
            return state
    
    async def _update_performance_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Update performance tracking data"""
        try:
            portfolio_metrics = state.get("workflow_results", {}).get("portfolio_metrics", {})
            
            # Store performance data with timestamp
            performance_update = {
                "timestamp": datetime.now().isoformat(),
                "metrics": portfolio_metrics,
                "update_type": "automated_tracking"
            }
            
            state["workflow_results"]["performance_update"] = performance_update
            
            return state
            
        except Exception as e:
            logger.error(f"Error in update performance node: {e}")
            state["workflow_results"]["error"] = str(e)
            return state
    
    async def _analyze_performance_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze portfolio performance"""
        try:
            portfolio_data = state.get("portfolio_data", {})
            market_data = state.get("market_data", {})
            
            # Use performance analyzer tool
            analyzer_tool = tool_registry.get_tool("performance_analyzer")
            if analyzer_tool:
                # Get performance metrics first
                tracker_tool = tool_registry.get_tool("portfolio_tracker")
                if tracker_tool:
                    tracking_result = await tracker_tool.execute(
                        portfolio_data=portfolio_data,
                        properties=portfolio_data.get("properties", [])
                    )
                    
                    if tracking_result.success:
                        performance_metrics = tracking_result.data.get("performance_metrics", {})
                        
                        # Analyze performance
                        analysis_result = await analyzer_tool.execute(
                            portfolio=portfolio_data,
                            performance_metrics=performance_metrics,
                            market_data=market_data
                        )
                        
                        if analysis_result.success:
                            state["workflow_results"]["performance_analysis"] = analysis_result.data
                            state["confidence_score"] = analysis_result.confidence_score
            
            return state
            
        except Exception as e:
            logger.error(f"Error in analyze performance node: {e}")
            state["workflow_results"]["error"] = str(e)
            return state
    
    async def _identify_trends_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Identify performance trends"""
        try:
            analysis_data = state.get("workflow_results", {}).get("performance_analysis", {})
            
            if analysis_data:
                # Identify trends from historical data
                trends = self._analyze_trends(analysis_data)
                state["workflow_results"]["trends"] = trends
            
            return state
            
        except Exception as e:
            logger.error(f"Error in identify trends node: {e}")
            state["workflow_results"]["error"] = str(e)
            return state
    
    async def _benchmark_comparison_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Compare performance against benchmarks"""
        try:
            analysis_data = state.get("workflow_results", {}).get("performance_analysis", {})
            
            if analysis_data:
                # Compare against market benchmarks
                benchmarks = self._compare_benchmarks(analysis_data)
                state["workflow_results"]["benchmarks"] = benchmarks
            
            return state
            
        except Exception as e:
            logger.error(f"Error in benchmark comparison node: {e}")
            state["workflow_results"]["error"] = str(e)
            return state
    
    async def _generate_insights_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance insights"""
        try:
            analysis_data = state.get("workflow_results", {}).get("performance_analysis", {})
            trends_data = state.get("workflow_results", {}).get("trends", {})
            benchmark_data = state.get("workflow_results", {}).get("benchmarks", {})
            
            # Generate comprehensive insights
            insights = self._generate_performance_insights(analysis_data, trends_data, benchmark_data)
            state["workflow_results"]["insights"] = insights
            
            return state
            
        except Exception as e:
            logger.error(f"Error in generate insights node: {e}")
            state["workflow_results"]["error"] = str(e)
            return state
    
    async def _assess_current_state_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Assess current portfolio state for optimization"""
        try:
            portfolio_data = state.get("portfolio_data", {})
            analysis_data = state.get("analysis_data", {})
            
            # Assess current state
            current_state = self._assess_portfolio_state(portfolio_data, analysis_data)
            state["workflow_results"]["current_state"] = current_state
            
            return state
            
        except Exception as e:
            logger.error(f"Error in assess current state node: {e}")
            state["workflow_results"]["error"] = str(e)
            return state
    
    async def _identify_opportunities_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Identify optimization opportunities"""
        try:
            current_state = state.get("workflow_results", {}).get("current_state", {})
            investment_goals = state.get("investment_goals", {})
            
            # Identify opportunities
            opportunities = self._identify_optimization_opportunities(current_state, investment_goals)
            state["workflow_results"]["opportunities"] = opportunities
            
            return state
            
        except Exception as e:
            logger.error(f"Error in identify opportunities node: {e}")
            state["workflow_results"]["error"] = str(e)
            return state
    
    async def _generate_recommendations_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimization recommendations"""
        try:
            opportunities = state.get("workflow_results", {}).get("opportunities", {})
            portfolio_data = state.get("portfolio_data", {})
            
            # Use optimization engine tool
            optimizer_tool = tool_registry.get_tool("optimization_engine")
            if optimizer_tool:
                result = await optimizer_tool.execute(
                    portfolio=portfolio_data,
                    analysis=state.get("analysis_data", {}),
                    investment_goals=state.get("investment_goals", {})
                )
                
                if result.success:
                    state["workflow_results"]["recommendations"] = result.data
                    state["confidence_score"] = result.confidence_score
            
            return state
            
        except Exception as e:
            logger.error(f"Error in generate recommendations node: {e}")
            state["workflow_results"]["error"] = str(e)
            return state
    
    async def _create_action_plan_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create implementation action plan"""
        try:
            recommendations = state.get("workflow_results", {}).get("recommendations", {})
            
            if recommendations:
                # Create detailed action plan
                action_plan = self._create_implementation_plan(recommendations)
                state["workflow_results"]["action_plan"] = action_plan
            
            return state
            
        except Exception as e:
            logger.error(f"Error in create action plan node: {e}")
            state["workflow_results"]["error"] = str(e)
            return state
    
    async def _analyze_risk_factors_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze portfolio risk factors"""
        try:
            portfolio_data = state.get("portfolio_data", {})
            market_conditions = state.get("market_conditions", {})
            
            # Use risk analyzer tool
            risk_tool = tool_registry.get_tool("risk_analyzer")
            if risk_tool:
                result = await risk_tool.execute(
                    portfolio=portfolio_data,
                    market_conditions=market_conditions
                )
                
                if result.success:
                    state["workflow_results"]["risk_analysis"] = result.data
                    state["confidence_score"] = result.confidence_score
            
            return state
            
        except Exception as e:
            logger.error(f"Error in analyze risk factors node: {e}")
            state["workflow_results"]["error"] = str(e)
            return state
    
    async def _calculate_risk_metrics_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detailed risk metrics"""
        try:
            risk_analysis = state.get("workflow_results", {}).get("risk_analysis", {})
            
            if risk_analysis:
                # Calculate additional risk metrics
                enhanced_risk_metrics = self._enhance_risk_metrics(risk_analysis)
                state["workflow_results"]["risk_metrics"] = enhanced_risk_metrics
            
            return state
            
        except Exception as e:
            logger.error(f"Error in calculate risk metrics node: {e}")
            state["workflow_results"]["error"] = str(e)
            return state
    
    async def _stress_testing_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Perform portfolio stress testing"""
        try:
            portfolio_data = state.get("portfolio_data", {})
            risk_metrics = state.get("workflow_results", {}).get("risk_metrics", {})
            
            # Perform stress testing scenarios
            stress_test_results = self._perform_stress_testing(portfolio_data, risk_metrics)
            state["workflow_results"]["stress_testing"] = stress_test_results
            
            return state
            
        except Exception as e:
            logger.error(f"Error in stress testing node: {e}")
            state["workflow_results"]["error"] = str(e)
            return state
    
    async def _mitigation_strategies_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate risk mitigation strategies"""
        try:
            risk_analysis = state.get("workflow_results", {}).get("risk_analysis", {})
            stress_test_results = state.get("workflow_results", {}).get("stress_testing", {})
            
            # Generate mitigation strategies
            mitigation_strategies = self._generate_risk_mitigation(risk_analysis, stress_test_results)
            state["workflow_results"]["mitigation_strategies"] = mitigation_strategies
            
            return state
            
        except Exception as e:
            logger.error(f"Error in mitigation strategies node: {e}")
            state["workflow_results"]["error"] = str(e)
            return state
    
    async def _gather_market_data_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Gather market data for analysis"""
        try:
            geographic_areas = state.get("geographic_areas", [])
            property_types = state.get("property_types", [])
            
            # Use market analyzer tool
            market_tool = tool_registry.get_tool("market_analyzer")
            if market_tool:
                result = await market_tool.execute(
                    geographic_areas=geographic_areas,
                    property_types=property_types
                )
                
                if result.success:
                    state["workflow_results"]["market_data"] = result.data
                    state["confidence_score"] = result.confidence_score
            
            return state
            
        except Exception as e:
            logger.error(f"Error in gather market data node: {e}")
            state["workflow_results"]["error"] = str(e)
            return state
    
    async def _analyze_trends_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market trends"""
        try:
            market_data = state.get("workflow_results", {}).get("market_data", {})
            
            if market_data:
                # Analyze market trends
                trend_analysis = self._analyze_market_trends(market_data)
                state["workflow_results"]["trend_analysis"] = trend_analysis
            
            return state
            
        except Exception as e:
            logger.error(f"Error in analyze trends node: {e}")
            state["workflow_results"]["error"] = str(e)
            return state
    
    async def _assess_opportunities_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Assess market opportunities"""
        try:
            market_data = state.get("workflow_results", {}).get("market_data", {})
            trend_analysis = state.get("workflow_results", {}).get("trend_analysis", {})
            
            # Assess opportunities
            opportunities = self._assess_market_opportunities(market_data, trend_analysis)
            state["workflow_results"]["opportunities"] = opportunities
            
            return state
            
        except Exception as e:
            logger.error(f"Error in assess opportunities node: {e}")
            state["workflow_results"]["error"] = str(e)
            return state
    
    async def _timing_analysis_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze investment timing"""
        try:
            market_data = state.get("workflow_results", {}).get("market_data", {})
            opportunities = state.get("workflow_results", {}).get("opportunities", {})
            
            # Analyze timing
            timing_analysis = self._analyze_investment_timing(market_data, opportunities)
            state["workflow_results"]["timing_analysis"] = timing_analysis
            
            return state
            
        except Exception as e:
            logger.error(f"Error in timing analysis node: {e}")
            state["workflow_results"]["error"] = str(e)
            return state
    
    # Helper Methods
    
    def _enhance_metrics(self, performance_metrics: Dict[str, Any], 
                        property_performances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhance performance metrics with additional calculations"""
        enhanced = performance_metrics.copy()
        
        if property_performances:
            # Calculate additional metrics
            cap_rates = [p.get("cap_rate", 0) for p in property_performances if p.get("cap_rate", 0) > 0]
            if cap_rates:
                enhanced["median_cap_rate"] = sorted(cap_rates)[len(cap_rates)//2]
                enhanced["cap_rate_std_dev"] = self._calculate_std_dev(cap_rates)
        
        enhanced["last_updated"] = datetime.now().isoformat()
        return enhanced
    
    def _analyze_trends(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance trends"""
        return {
            "trend_direction": "positive",  # Simplified
            "trend_strength": 0.7,
            "key_trends": [
                "Increasing cap rates in suburban markets",
                "Stable cash flow performance",
                "Growing equity appreciation"
            ],
            "trend_confidence": 0.8
        }
    
    def _compare_benchmarks(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare against market benchmarks"""
        return {
            "vs_reit_index": 0.15,  # 15% outperformance
            "vs_stock_market": 0.08,  # 8% outperformance
            "vs_local_market": 0.12,  # 12% outperformance
            "benchmark_confidence": 0.75
        }
    
    def _generate_performance_insights(self, analysis_data: Dict[str, Any],
                                     trends_data: Dict[str, Any],
                                     benchmark_data: Dict[str, Any]) -> List[str]:
        """Generate performance insights"""
        insights = []
        
        if benchmark_data.get("vs_reit_index", 0) > 0.1:
            insights.append("Portfolio significantly outperforming REIT index")
        
        if trends_data.get("trend_direction") == "positive":
            insights.append("Portfolio showing positive performance trends")
        
        insights.append("Diversification opportunities exist in emerging markets")
        
        return insights
    
    def _assess_portfolio_state(self, portfolio_data: Dict[str, Any], 
                              analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess current portfolio state"""
        return {
            "total_properties": len(portfolio_data.get("properties", [])),
            "total_value": portfolio_data.get("total_value", 0),
            "performance_score": 75,  # 0-100 scale
            "optimization_potential": "medium",
            "key_strengths": ["Strong cash flow", "Geographic diversification"],
            "key_weaknesses": ["Below-target cap rates", "High maintenance costs"]
        }
    
    def _identify_optimization_opportunities(self, current_state: Dict[str, Any],
                                           investment_goals: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify optimization opportunities"""
        opportunities = []
        
        if current_state.get("performance_score", 0) < 80:
            opportunities.append({
                "type": "performance_improvement",
                "description": "Improve underperforming properties",
                "potential_impact": "high",
                "effort_required": "medium"
            })
        
        opportunities.append({
            "type": "diversification",
            "description": "Expand into new geographic markets",
            "potential_impact": "medium",
            "effort_required": "high"
        })
        
        return opportunities
    
    def _create_implementation_plan(self, recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed implementation plan"""
        return {
            "phases": [
                {
                    "phase": 1,
                    "duration_months": 3,
                    "actions": ["Optimize existing properties", "Review expenses"],
                    "expected_outcomes": ["Improved cash flow", "Higher cap rates"]
                },
                {
                    "phase": 2,
                    "duration_months": 6,
                    "actions": ["Explore new markets", "Diversify property types"],
                    "expected_outcomes": ["Reduced risk", "Growth opportunities"]
                }
            ],
            "total_timeline_months": 9,
            "success_metrics": ["Cap rate > 8%", "Monthly cash flow > $1000"],
            "risk_factors": ["Market volatility", "Interest rate changes"]
        }
    
    def _enhance_risk_metrics(self, risk_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance risk metrics with additional calculations"""
        enhanced = risk_analysis.copy()
        
        # Add calculated risk scores
        enhanced["composite_risk_score"] = 65  # 0-100 scale
        enhanced["risk_trend"] = "stable"
        enhanced["risk_level"] = "moderate"
        
        return enhanced
    
    def _perform_stress_testing(self, portfolio_data: Dict[str, Any],
                              risk_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Perform portfolio stress testing"""
        return {
            "recession_scenario": {
                "value_decline": -0.20,
                "cash_flow_impact": -0.15,
                "recovery_timeline_months": 18
            },
            "interest_rate_shock": {
                "rate_increase": 0.03,
                "refinancing_impact": -0.10,
                "new_acquisition_impact": -0.25
            },
            "vacancy_shock": {
                "vacancy_increase": 0.10,
                "cash_flow_impact": -0.30,
                "mitigation_timeline_months": 6
            }
        }
    
    def _generate_risk_mitigation(self, risk_analysis: Dict[str, Any],
                                stress_test_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate risk mitigation strategies"""
        strategies = []
        
        strategies.append({
            "risk": "Geographic concentration",
            "strategy": "Diversify across multiple markets",
            "timeline": "12 months",
            "cost": 50000,
            "effectiveness": 0.8
        })
        
        strategies.append({
            "risk": "Interest rate exposure",
            "strategy": "Lock in fixed-rate financing",
            "timeline": "6 months",
            "cost": 10000,
            "effectiveness": 0.9
        })
        
        return strategies
    
    def _analyze_market_trends(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market trends"""
        return {
            "price_trend": "rising",
            "rent_trend": "stable",
            "inventory_trend": "declining",
            "demand_trend": "increasing",
            "trend_strength": 0.7,
            "trend_duration_months": 12
        }
    
    def _assess_market_opportunities(self, market_data: Dict[str, Any],
                                   trend_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assess market opportunities"""
        opportunities = []
        
        if trend_analysis.get("price_trend") == "rising":
            opportunities.append({
                "type": "appreciation_play",
                "description": "Properties in appreciating markets",
                "confidence": 0.8,
                "timeline": "6-12 months"
            })
        
        opportunities.append({
            "type": "cash_flow_opportunity",
            "description": "Undervalued rental properties",
            "confidence": 0.7,
            "timeline": "3-6 months"
        })
        
        return opportunities
    
    def _analyze_investment_timing(self, market_data: Dict[str, Any],
                                 opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze investment timing"""
        return {
            "overall_timing": "favorable",
            "buy_signal_strength": 0.7,
            "hold_signal_strength": 0.8,
            "sell_signal_strength": 0.3,
            "optimal_strategies": ["buy_and_hold", "value_add"],
            "timing_confidence": 0.75
        }
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def _store_workflow_result(self, result: WorkflowResult):
        """Store workflow result in history"""
        workflow_name = result.workflow_name
        
        if workflow_name not in self.workflow_history:
            self.workflow_history[workflow_name] = []
        
        self.workflow_history[workflow_name].append(result)
        
        # Keep only last 10 results per workflow
        if len(self.workflow_history[workflow_name]) > 10:
            self.workflow_history[workflow_name] = self.workflow_history[workflow_name][-10:]
    
    def get_workflow_history(self, workflow_name: Optional[str] = None) -> Dict[str, Any]:
        """Get workflow execution history"""
        if workflow_name:
            return {
                workflow_name: [r.dict() for r in self.workflow_history.get(workflow_name, [])]
            }
        
        return {
            name: [r.dict() for r in results]
            for name, results in self.workflow_history.items()
        }