"""
Analyst Agent Workflows - Comprehensive property analysis workflows
Implements the five core analyst workflows: valuation, financial analysis, strategy comparison, risk assessment, and recommendation generation
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import uuid
import json

from pydantic import BaseModel, Field
from langchain.schema import HumanMessage, AIMessage

from ..core.agent_state import AgentState, AgentType, Deal, DealStatus, StateManager
from ..core.agent_tools import tool_registry
from .analyst_models import PropertyAnalysis, PropertyValuation, RepairEstimate, FinancialMetrics, InvestmentStrategy

logger = logging.getLogger(__name__)


class WorkflowResult(BaseModel):
    """Result of a workflow execution"""
    workflow_name: str
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    execution_time: float = 0.0
    confidence_score: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)


class AnalystWorkflows:
    """
    Analyst Agent Workflows Implementation
    
    Implements the five core analyst workflows:
    1. Property Valuation Workflow
    2. Financial Analysis Workflow  
    3. Strategy Comparison Workflow
    4. Risk Assessment Workflow
    5. Recommendation Generation Workflow
    """
    
    def __init__(self, analyst_agent):
        self.analyst_agent = analyst_agent
        self.workflow_history: Dict[str, List[WorkflowResult]] = {}
        
        # Workflow configuration
        self.workflow_config = {
            "property_valuation": {
                "timeout_seconds": 180,
                "min_comparables": 3,
                "max_comp_distance": 2.0,
                "confidence_threshold": 0.7
            },
            "financial_analysis": {
                "timeout_seconds": 90,
                "required_metrics": ["cap_rate", "cash_flow", "roi"],
                "confidence_threshold": 0.8
            },
            "strategy_comparison": {
                "timeout_seconds": 150,
                "min_strategies": 2,
                "confidence_threshold": 0.75
            },
            "risk_assessment": {
                "timeout_seconds": 60,
                "risk_factors_threshold": 3,
                "confidence_threshold": 0.8
            },
            "recommendation_generation": {
                "timeout_seconds": 45,
                "confidence_threshold": 0.85
            }
        }
    
    async def execute_property_valuation_workflow(self, deal: Dict[str, Any], 
                                                 state: AgentState) -> WorkflowResult:
        """
        Property Valuation Workflow
        
        Steps:
        1. Find comparable properties
        2. Analyze market conditions
        3. Calculate current value and ARV
        4. Generate confidence score
        5. Return structured valuation
        """
        start_time = datetime.now()
        workflow_name = "property_valuation"
        
        try:
            logger.info(f"Starting property valuation workflow for deal {deal.get('id')}")
            
            # Step 1: Find comparable properties
            comp_finder_tool = tool_registry.get_tool("comparable_property_finder")
            if not comp_finder_tool:
                raise ValueError("Comparable property finder tool not available")
            
            comp_result = await comp_finder_tool.execute(
                property_address=deal.get("property_address", ""),
                property_type=deal.get("property_type", "single_family"),
                bedrooms=deal.get("bedrooms", 3),
                bathrooms=deal.get("bathrooms", 2),
                square_feet=deal.get("square_feet", 1500),
                max_distance=self.workflow_config["property_valuation"]["max_comp_distance"],
                max_age=180
            )
            
            if not comp_result.get("comparable_properties"):
                raise ValueError("No comparable properties found")
            
            comparables = comp_result["comparable_properties"]
            valuation_estimate = comp_result["valuation_estimate"]
            
            # Step 2: Analyze market conditions
            market_conditions = state.get("market_conditions", {})
            local_market_data = state.get("local_market_data", {})
            
            # Step 3: Calculate refined valuation using market data
            refined_valuation = await self._refine_valuation_with_market_data(
                valuation_estimate, comparables, market_conditions, deal
            )
            
            # Step 4: Generate confidence score
            confidence_score = await self._calculate_valuation_confidence(
                comparables, market_conditions, refined_valuation
            )
            
            # Step 5: Create structured valuation result
            property_valuation = PropertyValuation(
                arv=refined_valuation["arv"],
                current_value=refined_valuation["current_value"],
                confidence_score=confidence_score,
                comp_count=len(comparables),
                valuation_method="comparable_sales_adjusted",
                price_per_sqft=refined_valuation.get("price_per_sqft"),
                market_adjustment=refined_valuation.get("market_adjustment"),
                condition_adjustment=refined_valuation.get("condition_adjustment")
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = WorkflowResult(
                workflow_name=workflow_name,
                success=True,
                data={
                    "valuation": property_valuation.model_dump(),
                    "comparables": comparables,
                    "market_context": market_conditions,
                    "valuation_details": refined_valuation
                },
                execution_time=execution_time,
                confidence_score=confidence_score
            )
            
            # Record result in history
            self._record_workflow_result(result)
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Property valuation workflow failed: {e}")
            
            return WorkflowResult(
                workflow_name=workflow_name,
                success=False,
                error=str(e),
                execution_time=execution_time,
                confidence_score=0.0
            )
    
    async def execute_financial_analysis_workflow(self, deal: Dict[str, Any], 
                                                 valuation: PropertyValuation,
                                                 repair_estimate: RepairEstimate,
                                                 state: AgentState) -> WorkflowResult:
        """
        Financial Analysis Workflow
        
        Steps:
        1. Calculate basic financial metrics
        2. Analyze rental potential
        3. Calculate investment returns
        4. Generate scenario analysis
        5. Return comprehensive financial metrics
        """
        start_time = datetime.now()
        workflow_name = "financial_analysis"
        
        try:
            logger.info(f"Starting financial analysis workflow for deal {deal.get('id')}")
            
            # Step 1: Get financial calculator tool
            financial_calc_tool = tool_registry.get_tool("financial_calculator")
            if not financial_calc_tool:
                raise ValueError("Financial calculator tool not available")
            
            # Step 2: Calculate comprehensive financial metrics
            purchase_price = deal.get("listing_price", 0)
            repair_cost = repair_estimate.total_cost
            arv = valuation.arv
            
            # Estimate monthly rent (1% rule as baseline, then refine)
            estimated_rent = await self._estimate_monthly_rent(deal, state)
            
            financial_result = await financial_calc_tool.execute(
                purchase_price=purchase_price,
                repair_cost=repair_cost,
                arv=arv,
                monthly_rent=estimated_rent,
                down_payment_percentage=0.25,
                interest_rate=0.07,
                loan_term_years=30,
                vacancy_rate=0.05,
                management_fee=0.08,
                maintenance_reserve=0.05,
                capex_reserve=0.05
            )
            
            if not financial_result.get("financial_metrics"):
                raise ValueError("Failed to calculate financial metrics")
            
            metrics = financial_result["financial_metrics"]
            
            # Step 3: Generate scenario analysis
            scenarios = await self._generate_financial_scenarios(
                purchase_price, repair_cost, arv, estimated_rent
            )
            
            # Step 4: Calculate confidence score
            confidence_score = await self._calculate_financial_confidence(
                metrics, scenarios, deal, state
            )
            
            # Step 5: Create structured financial metrics
            financial_metrics = FinancialMetrics(
                purchase_price=purchase_price,
                repair_cost=repair_cost,
                total_investment=metrics["total_investment"],
                after_repair_value=arv,
                monthly_rent=estimated_rent,
                monthly_expenses=metrics["monthly_expenses"],
                monthly_cash_flow=metrics["monthly_cash_flow"],
                annual_cash_flow=metrics["annual_cash_flow"],
                cap_rate=metrics["cap_rate"],
                cash_on_cash_return=metrics["cash_on_cash_return"],
                roi=metrics.get("roi", 0),
                gross_rent_multiplier=metrics["gross_rent_multiplier"],
                flip_profit=metrics.get("flip_profit"),
                flip_roi=metrics.get("flip_roi"),
                flip_timeline_days=metrics.get("flip_timeline_days"),
                wholesale_fee=metrics.get("wholesale_fee"),
                wholesale_margin=metrics.get("wholesale_margin")
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = WorkflowResult(
                workflow_name=workflow_name,
                success=True,
                data={
                    "financial_metrics": financial_metrics.model_dump(),
                    "scenarios": scenarios,
                    "expense_breakdown": financial_result.get("expense_breakdown", {}),
                    "assumptions": financial_result.get("assumptions", {})
                },
                execution_time=execution_time,
                confidence_score=confidence_score
            )
            
            # Record result in history
            self._record_workflow_result(result)
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Financial analysis workflow failed: {e}")
            
            return WorkflowResult(
                workflow_name=workflow_name,
                success=False,
                error=str(e),
                execution_time=execution_time,
                confidence_score=0.0
            )
    
    async def execute_strategy_comparison_workflow(self, deal: Dict[str, Any],
                                                  financial_metrics: FinancialMetrics,
                                                  state: AgentState) -> WorkflowResult:
        """
        Strategy Comparison Workflow
        
        Steps:
        1. Analyze investment strategies
        2. Calculate strategy-specific metrics
        3. Assess market suitability
        4. Rank strategies by risk-adjusted returns
        5. Return strategy recommendations
        """
        start_time = datetime.now()
        workflow_name = "strategy_comparison"
        
        try:
            logger.info(f"Starting strategy comparison workflow for deal {deal.get('id')}")
            
            # Step 1: Get strategy analyzer tool
            strategy_tool = tool_registry.get_tool("investment_strategy_analyzer")
            if not strategy_tool:
                raise ValueError("Investment strategy analyzer tool not available")
            
            # Step 2: Analyze strategies
            market_conditions = state.get("market_conditions", {})
            investor_profile = state.get("investment_strategy", {})
            
            strategy_result = await strategy_tool.execute(
                financial_metrics=financial_metrics.model_dump(),
                market_conditions=market_conditions,
                investor_profile=investor_profile
            )
            
            if not strategy_result.get("strategies"):
                raise ValueError("No investment strategies generated")
            
            strategies_data = strategy_result["strategies"]
            
            # Step 3: Convert to structured strategy objects
            strategies = []
            for strategy_data in strategies_data:
                strategy = InvestmentStrategy(
                    strategy_type=strategy_data["strategy_type"],
                    potential_profit=strategy_data["potential_profit"],
                    roi=strategy_data["roi"],
                    risk_level=strategy_data["risk_level"],
                    timeline_days=strategy_data["timeline_days"],
                    funding_required=strategy_data["funding_required"],
                    pros=strategy_data.get("pros", []),
                    cons=strategy_data.get("cons", []),
                    confidence_score=strategy_data.get("confidence_score", 0.8)
                )
                strategies.append(strategy)
            
            # Step 4: Enhanced strategy analysis
            enhanced_strategies = await self._enhance_strategy_analysis(
                strategies, deal, market_conditions, state
            )
            
            # Step 5: Calculate overall confidence
            confidence_score = await self._calculate_strategy_confidence(
                enhanced_strategies, market_conditions
            )
            
            # Step 6: Determine recommended strategy
            recommended_strategy = strategy_result.get("recommended_strategy")
            if not recommended_strategy and enhanced_strategies:
                recommended_strategy = enhanced_strategies[0].strategy_type
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = WorkflowResult(
                workflow_name=workflow_name,
                success=True,
                data={
                    "strategies": [s.model_dump() for s in enhanced_strategies],
                    "recommended_strategy": recommended_strategy,
                    "market_analysis": strategy_result.get("market_analysis", {}),
                    "strategy_count": len(enhanced_strategies)
                },
                execution_time=execution_time,
                confidence_score=confidence_score
            )
            
            # Record result in history
            self._record_workflow_result(result)
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Strategy comparison workflow failed: {e}")
            
            return WorkflowResult(
                workflow_name=workflow_name,
                success=False,
                error=str(e),
                execution_time=execution_time,
                confidence_score=0.0
            )
    
    async def execute_risk_assessment_workflow(self, deal: Dict[str, Any],
                                             analysis_data: Dict[str, Any],
                                             state: AgentState) -> WorkflowResult:
        """
        Risk Assessment Workflow
        
        Steps:
        1. Identify property-specific risks
        2. Assess market risks
        3. Evaluate financial risks
        4. Calculate overall risk score
        5. Return comprehensive risk assessment
        """
        start_time = datetime.now()
        workflow_name = "risk_assessment"
        
        try:
            logger.info(f"Starting risk assessment workflow for deal {deal.get('id')}")
            
            # Step 1: Get risk assessment tool
            risk_tool = tool_registry.get_tool("risk_assessment_tool")
            if not risk_tool:
                raise ValueError("Risk assessment tool not available")
            
            # Step 2: Execute risk assessment
            risk_result = await risk_tool.execute(
                property_data=deal,
                financial_metrics=analysis_data.get("financial_metrics", {}),
                market_conditions=state.get("market_conditions", {}),
                analysis_data=analysis_data
            )
            
            if not risk_result.get("risk_assessment"):
                raise ValueError("Risk assessment failed")
            
            risk_data = risk_result["risk_assessment"]
            
            # Step 3: Enhanced risk analysis
            enhanced_risks = await self._enhance_risk_analysis(
                risk_data, deal, analysis_data, state
            )
            
            # Step 4: Calculate confidence score
            confidence_score = await self._calculate_risk_confidence(
                enhanced_risks, deal, state
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = WorkflowResult(
                workflow_name=workflow_name,
                success=True,
                data={
                    "risk_factors": enhanced_risks.get("risk_factors", []),
                    "overall_risk_score": enhanced_risks.get("overall_risk_score", 5.0),
                    "risk_categories": enhanced_risks.get("risk_categories", {}),
                    "mitigation_strategies": enhanced_risks.get("mitigation_strategies", []),
                    "risk_tolerance_match": enhanced_risks.get("risk_tolerance_match", True)
                },
                execution_time=execution_time,
                confidence_score=confidence_score
            )
            
            # Record result in history
            self._record_workflow_result(result)
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Risk assessment workflow failed: {e}")
            
            return WorkflowResult(
                workflow_name=workflow_name,
                success=False,
                error=str(e),
                execution_time=execution_time,
                confidence_score=0.0
            )
    
    async def execute_recommendation_generation_workflow(self, deal: Dict[str, Any],
                                                       workflow_results: Dict[str, WorkflowResult],
                                                       state: AgentState) -> WorkflowResult:
        """
        Recommendation Generation Workflow
        
        Steps:
        1. Synthesize all analysis results
        2. Apply investment criteria
        3. Generate recommendation
        4. Calculate overall confidence
        5. Return final recommendation
        """
        start_time = datetime.now()
        workflow_name = "recommendation_generation"
        
        try:
            logger.info(f"Starting recommendation generation workflow for deal {deal.get('id')}")
            
            # Step 1: Extract key data from workflow results
            valuation_data = workflow_results.get("property_valuation", WorkflowResult(workflow_name="empty", success=False)).data
            financial_data = workflow_results.get("financial_analysis", WorkflowResult(workflow_name="empty", success=False)).data
            strategy_data = workflow_results.get("strategy_comparison", WorkflowResult(workflow_name="empty", success=False)).data
            risk_data = workflow_results.get("risk_assessment", WorkflowResult(workflow_name="empty", success=False)).data
            
            # Step 2: Apply investment criteria
            investment_criteria = state.get("investment_criteria", {})
            criteria_analysis = await self._analyze_investment_criteria(
                valuation_data, financial_data, strategy_data, risk_data, investment_criteria
            )
            
            # Step 3: Generate recommendation
            recommendation = await self._generate_investment_recommendation(
                criteria_analysis, workflow_results, deal, state
            )
            
            # Step 4: Calculate overall confidence
            confidence_score = await self._calculate_overall_confidence(
                workflow_results, recommendation
            )
            
            # Step 5: Generate detailed reasoning
            reasoning = await self._generate_recommendation_reasoning(
                recommendation, criteria_analysis, workflow_results
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = WorkflowResult(
                workflow_name=workflow_name,
                success=True,
                data={
                    "investment_recommendation": recommendation,
                    "recommendation_reason": reasoning,
                    "criteria_analysis": criteria_analysis,
                    "confidence_level": confidence_score,
                    "key_metrics": {
                        "cap_rate": financial_data.get("financial_metrics", {}).get("cap_rate"),
                        "cash_flow": financial_data.get("financial_metrics", {}).get("monthly_cash_flow"),
                        "roi": financial_data.get("financial_metrics", {}).get("roi"),
                        "risk_score": risk_data.get("overall_risk_score")
                    }
                },
                execution_time=execution_time,
                confidence_score=confidence_score
            )
            
            # Record result in history
            self._record_workflow_result(result)
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Recommendation generation workflow failed: {e}")
            
            return WorkflowResult(
                workflow_name=workflow_name,
                success=False,
                error=str(e),
                execution_time=execution_time,
                confidence_score=0.0
            )
    
    # Helper Methods
    
    async def _refine_valuation_with_market_data(self, valuation_estimate: Dict[str, Any],
                                               comparables: List[Dict[str, Any]],
                                               market_conditions: Dict[str, Any],
                                               deal: Dict[str, Any]) -> Dict[str, Any]:
        """Refine valuation using market conditions and trends"""
        base_value = valuation_estimate.get("estimated_value", 0)
        
        # Market adjustment factors
        market_temp = market_conditions.get("market_temperature", "warm")
        price_trend = market_conditions.get("price_change_yoy", 0.0)
        
        market_adjustment = 0.0
        if market_temp == "hot":
            market_adjustment = 0.05
        elif market_temp == "cold":
            market_adjustment = -0.05
        
        # Trend adjustment
        trend_adjustment = min(max(price_trend / 100, -0.1), 0.1)  # Cap at ±10%
        
        # Condition adjustment
        property_condition = deal.get("property_condition", "fair")
        condition_adjustments = {
            "excellent": 0.05,
            "good": 0.0,
            "fair": -0.05,
            "poor": -0.15
        }
        condition_adjustment = condition_adjustments.get(property_condition, 0.0)
        
        # Calculate adjusted values
        total_adjustment = market_adjustment + trend_adjustment + condition_adjustment
        adjusted_value = base_value * (1 + total_adjustment)
        arv = adjusted_value * 1.1  # Assume 10% potential upside after repairs
        
        return {
            "current_value": adjusted_value,
            "arv": arv,
            "price_per_sqft": adjusted_value / max(deal.get("square_feet", 1500), 1),
            "market_adjustment": market_adjustment,
            "trend_adjustment": trend_adjustment,
            "condition_adjustment": condition_adjustment,
            "total_adjustment": total_adjustment
        }
    
    async def _calculate_valuation_confidence(self, comparables: List[Dict[str, Any]],
                                            market_conditions: Dict[str, Any],
                                            valuation: Dict[str, Any]) -> float:
        """Calculate confidence score for valuation"""
        confidence_factors = []
        
        # Comparable quality
        if len(comparables) >= 5:
            confidence_factors.append(0.9)
        elif len(comparables) >= 3:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.6)
        
        # Comparable similarity
        avg_similarity = sum(comp.get("similarity_score", 0.8) for comp in comparables) / len(comparables)
        confidence_factors.append(avg_similarity)
        
        # Market data quality
        market_data_quality = 0.8 if market_conditions else 0.6
        confidence_factors.append(market_data_quality)
        
        # Distance factor
        avg_distance = sum(comp.get("distance_miles", 1.0) for comp in comparables) / len(comparables)
        distance_factor = max(0.5, 1.0 - (avg_distance / 2.0))
        confidence_factors.append(distance_factor)
        
        return sum(confidence_factors) / len(confidence_factors)
    
    async def _estimate_monthly_rent(self, deal: Dict[str, Any], state: AgentState) -> float:
        """Estimate monthly rent for the property"""
        # Use 1% rule as baseline
        purchase_price = deal.get("listing_price", 0)
        baseline_rent = purchase_price * 0.01
        
        # Adjust based on market conditions
        market_conditions = state.get("market_conditions", {})
        rent_growth = market_conditions.get("rent_growth_yoy", 0.0)
        
        # Adjust for property characteristics
        bedrooms = deal.get("bedrooms", 3)
        square_feet = deal.get("square_feet", 1500)
        
        # Simple adjustment factors
        bedroom_factor = 1.0 + (bedrooms - 3) * 0.1
        size_factor = 1.0 + (square_feet - 1500) / 1500 * 0.2
        
        adjusted_rent = baseline_rent * bedroom_factor * size_factor * (1 + rent_growth / 100)
        
        return max(adjusted_rent, purchase_price * 0.005)  # Minimum 0.5% rule
    
    async def _generate_financial_scenarios(self, purchase_price: float, repair_cost: float,
                                          arv: float, monthly_rent: float) -> Dict[str, Any]:
        """Generate conservative, likely, and optimistic financial scenarios"""
        scenarios = {}
        
        # Conservative scenario (10% worse)
        scenarios["conservative"] = {
            "purchase_price": purchase_price,
            "repair_cost": repair_cost * 1.2,  # 20% higher repair costs
            "monthly_rent": monthly_rent * 0.9,  # 10% lower rent
            "vacancy_rate": 0.08,  # Higher vacancy
            "scenario_probability": 0.3
        }
        
        # Likely scenario (base case)
        scenarios["likely"] = {
            "purchase_price": purchase_price,
            "repair_cost": repair_cost,
            "monthly_rent": monthly_rent,
            "vacancy_rate": 0.05,
            "scenario_probability": 0.5
        }
        
        # Optimistic scenario (10% better)
        scenarios["optimistic"] = {
            "purchase_price": purchase_price,
            "repair_cost": repair_cost * 0.9,  # 10% lower repair costs
            "monthly_rent": monthly_rent * 1.1,  # 10% higher rent
            "vacancy_rate": 0.03,  # Lower vacancy
            "scenario_probability": 0.2
        }
        
        return scenarios
    
    async def _calculate_financial_confidence(self, metrics: Dict[str, Any],
                                            scenarios: Dict[str, Any],
                                            deal: Dict[str, Any],
                                            state: AgentState) -> float:
        """Calculate confidence score for financial analysis"""
        confidence_factors = []
        
        # Data quality
        required_data = ["listing_price", "square_feet", "bedrooms", "bathrooms"]
        data_completeness = sum(1 for field in required_data if deal.get(field)) / len(required_data)
        confidence_factors.append(data_completeness)
        
        # Market data availability
        market_data_quality = 0.8 if state.get("market_conditions") else 0.6
        confidence_factors.append(market_data_quality)
        
        # Metric reasonableness
        cap_rate = metrics.get("cap_rate", 0)
        cash_flow = metrics.get("monthly_cash_flow", 0)
        
        metric_reasonableness = 0.9 if (0.05 <= cap_rate <= 0.15 and cash_flow > 0) else 0.7
        confidence_factors.append(metric_reasonableness)
        
        # Scenario consistency
        scenario_confidence = 0.8  # Assume good scenario modeling
        confidence_factors.append(scenario_confidence)
        
        return sum(confidence_factors) / len(confidence_factors)
    
    async def _enhance_strategy_analysis(self, strategies: List[InvestmentStrategy],
                                       deal: Dict[str, Any],
                                       market_conditions: Dict[str, Any],
                                       state: AgentState) -> List[InvestmentStrategy]:
        """Enhance strategy analysis with additional context"""
        enhanced_strategies = []
        
        for strategy in strategies:
            # Add market-specific adjustments
            market_temp = market_conditions.get("market_temperature", "warm")
            
            # Adjust confidence based on market conditions
            if strategy.strategy_type == "fix_and_flip" and market_temp == "hot":
                strategy.confidence_score = min(strategy.confidence_score * 1.1, 1.0)
            elif strategy.strategy_type == "buy_and_hold_rental":
                rental_demand = market_conditions.get("rental_demand", "moderate")
                if rental_demand == "high":
                    strategy.confidence_score = min(strategy.confidence_score * 1.05, 1.0)
            
            enhanced_strategies.append(strategy)
        
        # Sort by risk-adjusted return
        enhanced_strategies.sort(
            key=lambda s: (s.roi * s.confidence_score) / max(s.risk_level, 1),
            reverse=True
        )
        
        return enhanced_strategies
    
    async def _calculate_strategy_confidence(self, strategies: List[InvestmentStrategy],
                                           market_conditions: Dict[str, Any]) -> float:
        """Calculate overall confidence in strategy analysis"""
        if not strategies:
            return 0.0
        
        # Average strategy confidence
        avg_confidence = sum(s.confidence_score for s in strategies) / len(strategies)
        
        # Market data quality factor
        market_factor = 0.9 if market_conditions else 0.7
        
        # Strategy diversity factor
        diversity_factor = min(len(strategies) / 3.0, 1.0)  # Better with more strategies
        
        return (avg_confidence + market_factor + diversity_factor) / 3
    
    async def _enhance_risk_analysis(self, risk_data: Dict[str, Any],
                                   deal: Dict[str, Any],
                                   analysis_data: Dict[str, Any],
                                   state: AgentState) -> Dict[str, Any]:
        """Enhance risk analysis with additional context"""
        enhanced_risks = risk_data.copy()
        
        # Add property-specific risks
        property_age = datetime.now().year - deal.get("year_built", 1990)
        if property_age > 30:
            enhanced_risks.setdefault("risk_factors", []).append("Older property may require major systems updates")
        
        # Add market risks
        market_conditions = state.get("market_conditions", {})
        if market_conditions.get("market_temperature") == "hot":
            enhanced_risks.setdefault("risk_factors", []).append("Hot market may lead to overpaying")
        
        # Add financial risks
        financial_metrics = analysis_data.get("financial_metrics", {})
        if financial_metrics.get("cap_rate", 0) < 0.06:
            enhanced_risks.setdefault("risk_factors", []).append("Low cap rate indicates higher risk")
        
        # Calculate risk categories
        enhanced_risks["risk_categories"] = {
            "property_risk": min(property_age / 50.0 * 10, 10),
            "market_risk": 5.0,  # Default moderate risk
            "financial_risk": max(10 - financial_metrics.get("cap_rate", 0.08) * 100, 1),
            "liquidity_risk": 4.0
        }
        
        # Add mitigation strategies
        enhanced_risks["mitigation_strategies"] = [
            "Conduct thorough property inspection",
            "Maintain adequate cash reserves",
            "Consider property management company",
            "Monitor market conditions regularly"
        ]
        
        return enhanced_risks
    
    async def _calculate_risk_confidence(self, risk_data: Dict[str, Any],
                                       deal: Dict[str, Any],
                                       state: AgentState) -> float:
        """Calculate confidence in risk assessment"""
        confidence_factors = []
        
        # Data completeness
        property_data_fields = ["year_built", "property_condition", "square_feet"]
        completeness = sum(1 for field in property_data_fields if deal.get(field)) / len(property_data_fields)
        confidence_factors.append(completeness)
        
        # Market data availability
        market_factor = 0.9 if state.get("market_conditions") else 0.7
        confidence_factors.append(market_factor)
        
        # Risk factor identification
        risk_factors_count = len(risk_data.get("risk_factors", []))
        risk_factor_confidence = min(risk_factors_count / 5.0, 1.0)  # Better with more identified risks
        confidence_factors.append(risk_factor_confidence)
        
        return sum(confidence_factors) / len(confidence_factors)
    
    async def _analyze_investment_criteria(self, valuation_data: Dict[str, Any],
                                         financial_data: Dict[str, Any],
                                         strategy_data: Dict[str, Any],
                                         risk_data: Dict[str, Any],
                                         investment_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how the deal meets investment criteria"""
        criteria_analysis = {}
        
        # Default criteria if not specified
        default_criteria = {
            "min_cap_rate": 0.08,
            "min_cash_flow": 200,
            "max_risk_score": 7.0,
            "min_roi": 0.15
        }
        
        criteria = {**default_criteria, **investment_criteria}
        
        # Extract metrics
        financial_metrics = financial_data.get("financial_metrics", {})
        cap_rate = financial_metrics.get("cap_rate", 0)
        cash_flow = financial_metrics.get("monthly_cash_flow", 0)
        roi = financial_metrics.get("roi", 0)
        risk_score = risk_data.get("overall_risk_score", 5.0)
        
        # Analyze each criterion
        criteria_analysis["cap_rate"] = {
            "required": criteria["min_cap_rate"],
            "actual": cap_rate,
            "meets_criteria": cap_rate >= criteria["min_cap_rate"],
            "score": min(cap_rate / criteria["min_cap_rate"], 2.0)  # Cap at 2x requirement
        }
        
        criteria_analysis["cash_flow"] = {
            "required": criteria["min_cash_flow"],
            "actual": cash_flow,
            "meets_criteria": cash_flow >= criteria["min_cash_flow"],
            "score": min(cash_flow / criteria["min_cash_flow"], 2.0) if criteria["min_cash_flow"] > 0 else 1.0
        }
        
        criteria_analysis["risk_score"] = {
            "required": criteria["max_risk_score"],
            "actual": risk_score,
            "meets_criteria": risk_score <= criteria["max_risk_score"],
            "score": max(0.1, criteria["max_risk_score"] / max(risk_score, 1))
        }
        
        criteria_analysis["roi"] = {
            "required": criteria["min_roi"],
            "actual": roi,
            "meets_criteria": roi >= criteria["min_roi"],
            "score": min(roi / criteria["min_roi"], 2.0) if criteria["min_roi"] > 0 else 1.0
        }
        
        # Overall criteria score
        total_score = sum(c["score"] for c in criteria_analysis.values())
        criteria_met = sum(1 for c in criteria_analysis.values() if c["meets_criteria"])
        
        criteria_analysis["overall"] = {
            "total_criteria": len(criteria_analysis),
            "criteria_met": criteria_met,
            "criteria_percentage": criteria_met / len(criteria_analysis),
            "average_score": total_score / len(criteria_analysis)
        }
        
        return criteria_analysis
    
    async def _generate_investment_recommendation(self, criteria_analysis: Dict[str, Any],
                                                workflow_results: Dict[str, WorkflowResult],
                                                deal: Dict[str, Any],
                                                state: AgentState) -> str:
        """Generate final investment recommendation"""
        overall_analysis = criteria_analysis.get("overall", {})
        criteria_percentage = overall_analysis.get("criteria_percentage", 0)
        average_score = overall_analysis.get("average_score", 0)
        
        # Get workflow success rates
        successful_workflows = sum(1 for result in workflow_results.values() if result.success)
        total_workflows = len(workflow_results)
        workflow_success_rate = successful_workflows / total_workflows if total_workflows > 0 else 0
        
        # Decision logic
        if criteria_percentage >= 0.8 and average_score >= 1.2 and workflow_success_rate >= 0.8:
            return "proceed"
        elif criteria_percentage >= 0.6 and average_score >= 1.0 and workflow_success_rate >= 0.6:
            return "caution"
        else:
            return "reject"
    
    async def _calculate_overall_confidence(self, workflow_results: Dict[str, WorkflowResult],
                                          recommendation: str) -> float:
        """Calculate overall confidence in the analysis"""
        if not workflow_results:
            return 0.0
        
        # Average workflow confidence
        confidence_scores = [result.confidence_score for result in workflow_results.values() if result.success]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Workflow completion factor
        completion_factor = len(confidence_scores) / len(workflow_results)
        
        # Recommendation confidence adjustment
        recommendation_factor = {
            "proceed": 1.0,
            "caution": 0.8,
            "reject": 0.9  # High confidence in rejection
        }.get(recommendation, 0.7)
        
        return avg_confidence * completion_factor * recommendation_factor
    
    async def _generate_recommendation_reasoning(self, recommendation: str,
                                               criteria_analysis: Dict[str, Any],
                                               workflow_results: Dict[str, WorkflowResult]) -> str:
        """Generate detailed reasoning for the recommendation"""
        reasoning_parts = []
        
        # Criteria analysis summary
        overall = criteria_analysis.get("overall", {})
        criteria_met = overall.get("criteria_met", 0)
        total_criteria = overall.get("total_criteria", 0)
        
        reasoning_parts.append(f"Investment criteria: {criteria_met}/{total_criteria} criteria met")
        
        # Key metrics
        cap_rate_analysis = criteria_analysis.get("cap_rate", {})
        cash_flow_analysis = criteria_analysis.get("cash_flow", {})
        
        if cap_rate_analysis.get("meets_criteria"):
            reasoning_parts.append(f"Cap rate of {cap_rate_analysis.get('actual', 0):.2%} meets minimum requirement")
        else:
            reasoning_parts.append(f"Cap rate of {cap_rate_analysis.get('actual', 0):.2%} below minimum requirement")
        
        if cash_flow_analysis.get("meets_criteria"):
            reasoning_parts.append(f"Monthly cash flow of ${cash_flow_analysis.get('actual', 0):.0f} meets minimum requirement")
        else:
            reasoning_parts.append(f"Monthly cash flow of ${cash_flow_analysis.get('actual', 0):.0f} below minimum requirement")
        
        # Workflow results
        successful_workflows = [name for name, result in workflow_results.items() if result.success]
        if successful_workflows:
            reasoning_parts.append(f"Successfully completed analysis: {', '.join(successful_workflows)}")
        
        # Recommendation-specific reasoning
        if recommendation == "proceed":
            reasoning_parts.append("Strong financial metrics and low risk profile support investment")
        elif recommendation == "caution":
            reasoning_parts.append("Mixed results suggest careful consideration and additional due diligence")
        else:
            reasoning_parts.append("Poor financial metrics or high risk factors recommend avoiding this investment")
        
        return ". ".join(reasoning_parts) + "."
    
    def get_workflow_history(self, workflow_name: Optional[str] = None) -> Dict[str, List[WorkflowResult]]:
        """Get workflow execution history"""
        if workflow_name:
            return {workflow_name: self.workflow_history.get(workflow_name, [])}
        return self.workflow_history.copy()
    
    def _record_workflow_result(self, result: WorkflowResult):
        """Record workflow result in history"""
        if result.workflow_name not in self.workflow_history:
            self.workflow_history[result.workflow_name] = []
        
        self.workflow_history[result.workflow_name].append(result)
        
        # Keep only last 100 results per workflow
        if len(self.workflow_history[result.workflow_name]) > 100:
            self.workflow_history[result.workflow_name] = self.workflow_history[result.workflow_name][-100:]