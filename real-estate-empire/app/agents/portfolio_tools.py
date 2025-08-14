"""
Portfolio Agent Tools
Specialized tools for portfolio management, performance tracking, and optimization
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import statistics

from ..core.agent_tools import AgentTool, ToolCategory, ToolResult
from .portfolio_models import (
    Portfolio, PropertyPerformance, PerformanceMetrics, PortfolioAnalysis,
    RiskAssessment, MarketAnalysis, InvestmentRecommendation
)

# Configure logging
logger = logging.getLogger(__name__)


class PortfolioTracker(AgentTool):
    """Tool for tracking portfolio performance metrics"""
    
    def __init__(self):
        super().__init__(
            name="portfolio_tracker",
            description="Track performance metrics for all properties in portfolio",
            category=ToolCategory.ANALYSIS,
            input_schema={
                "portfolio_data": "Dict[str, Any]",
                "properties": "List[Dict[str, Any]]"
            },
            output_schema={
                "performance_metrics": "PerformanceMetrics",
                "property_performances": "List[PropertyPerformance]"
            },
            required_permissions=["read_portfolio", "calculate_metrics"]
        )
    
    async def execute(self, portfolio_data: Dict[str, Any], 
                     properties: List[Dict[str, Any]], **kwargs) -> ToolResult:
        """Track portfolio performance metrics"""
        try:
            logger.info("Tracking portfolio performance metrics")
            
            # Calculate individual property performances
            property_performances = []
            for prop in properties:
                perf = self._calculate_property_performance(prop)
                property_performances.append(perf)
            
            # Calculate portfolio-level metrics
            portfolio_metrics = self._calculate_portfolio_metrics(
                portfolio_data, property_performances
            )
            
            return ToolResult(
                success=True,
                data={
                    "performance_metrics": portfolio_metrics.dict(),
                    "property_performances": [p.dict() for p in property_performances]
                },
                execution_time=2.5,
                confidence_score=0.9
            )
            
        except Exception as e:
            logger.error(f"Error in portfolio tracking: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                execution_time=0.5
            )    

    def _calculate_property_performance(self, prop: Dict[str, Any]) -> PropertyPerformance:
        """Calculate performance metrics for individual property"""
        # Extract property data
        acquisition_cost = prop.get("acquisition_cost", 0)
        current_value = prop.get("current_value", 0)
        monthly_rent = prop.get("monthly_rent", 0)
        monthly_expenses = prop.get("monthly_expenses", 0)
        
        # Calculate performance metrics
        monthly_cash_flow = monthly_rent - monthly_expenses
        annual_cash_flow = monthly_cash_flow * 12
        
        # Calculate returns
        cap_rate = annual_cash_flow / current_value if current_value > 0 else 0
        cash_on_cash_return = annual_cash_flow / acquisition_cost if acquisition_cost > 0 else 0
        
        # Calculate equity and appreciation
        current_equity = current_value - (acquisition_cost * 0.8)  # Assuming 80% LTV
        appreciation = current_value - acquisition_cost
        appreciation_percentage = appreciation / acquisition_cost if acquisition_cost > 0 else 0
        
        return PropertyPerformance(
            property_id=prop.get("id", ""),
            portfolio_id=prop.get("portfolio_id", ""),
            address=prop.get("address", ""),
            city=prop.get("city", ""),
            state=prop.get("state", ""),
            property_type=prop.get("property_type", ""),
            strategy=prop.get("strategy", "buy_and_hold"),
            acquisition_date=datetime.fromisoformat(prop.get("acquisition_date", datetime.now().isoformat())),
            acquisition_cost=acquisition_cost,
            initial_investment=acquisition_cost,
            current_value=current_value,
            monthly_rent=monthly_rent,
            monthly_expenses=monthly_expenses,
            monthly_cash_flow=monthly_cash_flow,
            annual_cash_flow=annual_cash_flow,
            cap_rate=cap_rate,
            cash_on_cash_return=cash_on_cash_return,
            current_equity=current_equity,
            appreciation=appreciation,
            appreciation_percentage=appreciation_percentage,
            performance_score=self._calculate_performance_score(cap_rate, cash_on_cash_return)
        )
    
    def _calculate_portfolio_metrics(self, portfolio_data: Dict[str, Any], 
                                   property_performances: List[PropertyPerformance]) -> PerformanceMetrics:
        """Calculate portfolio-level performance metrics"""
        if not property_performances:
            return PerformanceMetrics(
                portfolio_id=portfolio_data.get("id", ""),
                total_properties=0
            )
        
        # Aggregate financial metrics
        total_value = sum(p.current_value for p in property_performances)
        total_equity = sum(p.current_equity for p in property_performances)
        total_debt = total_value - total_equity
        gross_monthly_rent = sum(p.monthly_rent for p in property_performances)
        monthly_expenses = sum(p.monthly_expenses for p in property_performances)
        monthly_cash_flow = sum(p.monthly_cash_flow for p in property_performances)
        
        # Calculate averages
        avg_cap_rate = statistics.mean([p.cap_rate for p in property_performances if p.cap_rate > 0])
        avg_coc_return = statistics.mean([p.cash_on_cash_return for p in property_performances if p.cash_on_cash_return > 0])
        
        return PerformanceMetrics(
            portfolio_id=portfolio_data.get("id", ""),
            total_properties=len(property_performances),
            total_value=total_value,
            total_equity=total_equity,
            total_debt=total_debt,
            loan_to_value=total_debt / total_value if total_value > 0 else 0,
            gross_monthly_rent=gross_monthly_rent,
            net_monthly_rent=gross_monthly_rent,
            monthly_expenses=monthly_expenses,
            monthly_cash_flow=monthly_cash_flow,
            annual_cash_flow=monthly_cash_flow * 12,
            portfolio_cap_rate=avg_cap_rate,
            portfolio_coc_return=avg_coc_return,
            portfolio_roi=avg_coc_return  # Simplified
        )
    
    def _calculate_performance_score(self, cap_rate: float, coc_return: float) -> float:
        """Calculate performance score (0-100)"""
        # Simple scoring based on cap rate and cash-on-cash return
        cap_rate_score = min(cap_rate * 1000, 50)  # Max 50 points for cap rate
        coc_score = min(coc_return * 250, 50)  # Max 50 points for CoC return
        return cap_rate_score + coc_score


class PerformanceAnalyzer(AgentTool):
    """Tool for analyzing portfolio performance and identifying optimization opportunities"""
    
    def __init__(self):
        super().__init__(
            name="performance_analyzer",
            description="Analyze portfolio performance and identify optimization opportunities",
            category=ToolCategory.ANALYSIS,
            input_schema={
                "portfolio": "Portfolio",
                "performance_metrics": "PerformanceMetrics",
                "market_data": "Dict[str, Any]"
            },
            output_schema={
                "analysis": "PortfolioAnalysis",
                "recommendations": "List[InvestmentRecommendation]"
            },
            required_permissions=["read_portfolio", "analyze_performance"]
        )
    
    async def execute(self, portfolio: Dict[str, Any], performance_metrics: Dict[str, Any],
                     market_data: Dict[str, Any], **kwargs) -> ToolResult:
        """Analyze portfolio performance"""
        try:
            logger.info("Analyzing portfolio performance")
            
            # Identify top performers and underperformers
            properties = portfolio.get("properties", [])
            top_performers = self._identify_top_performers(properties)
            underperformers = self._identify_underperformers(properties)
            
            # Analyze diversification
            diversification_analysis = self._analyze_diversification(properties)
            
            # Generate insights and recommendations
            insights = self._generate_insights(performance_metrics, market_data)
            recommendations = self._generate_recommendations(
                performance_metrics, top_performers, underperformers
            )
            
            analysis = {
                "portfolio_id": portfolio.get("id", ""),
                "analysis_date": datetime.now().isoformat(),
                "performance_metrics": performance_metrics,
                "top_performers": top_performers,
                "underperformers": underperformers,
                "diversification_analysis": diversification_analysis,
                "key_insights": insights,
                "recommendations": [r.dict() for r in recommendations],
                "confidence_score": 0.85
            }
            
            return ToolResult(
                success=True,
                data={
                    "analysis": analysis,
                    "recommendations": [r.dict() for r in recommendations]
                },
                execution_time=3.0,
                confidence_score=0.85
            )
            
        except Exception as e:
            logger.error(f"Error in performance analysis: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                execution_time=0.5
            )
    
    def _identify_top_performers(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify top performing properties"""
        # Sort by performance score and return top 3
        sorted_props = sorted(
            properties, 
            key=lambda p: p.get("performance_score", 0), 
            reverse=True
        )
        return sorted_props[:3]
    
    def _identify_underperformers(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify underperforming properties"""
        # Properties with cap rate < 6% or negative cash flow
        underperformers = []
        for prop in properties:
            cap_rate = prop.get("cap_rate", 0)
            cash_flow = prop.get("monthly_cash_flow", 0)
            if cap_rate < 0.06 or cash_flow < 0:
                underperformers.append(prop)
        return underperformers
    
    def _analyze_diversification(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze portfolio diversification"""
        if not properties:
            return {}
        
        # Geographic diversification
        cities = {}
        states = {}
        for prop in properties:
            city = prop.get("city", "Unknown")
            state = prop.get("state", "Unknown")
            cities[city] = cities.get(city, 0) + 1
            states[state] = states.get(state, 0) + 1
        
        # Property type diversification
        prop_types = {}
        for prop in properties:
            prop_type = prop.get("property_type", "Unknown")
            prop_types[prop_type] = prop_types.get(prop_type, 0) + 1
        
        total_props = len(properties)
        return {
            "geographic_concentration": {
                city: count/total_props for city, count in cities.items()
            },
            "state_concentration": {
                state: count/total_props for state, count in states.items()
            },
            "property_type_concentration": {
                prop_type: count/total_props for prop_type, count in prop_types.items()
            },
            "diversification_score": self._calculate_diversification_score(cities, states, prop_types, total_props)
        }
    
    def _calculate_diversification_score(self, cities: Dict, states: Dict, 
                                       prop_types: Dict, total_props: int) -> float:
        """Calculate diversification score (0-1)"""
        # Simple diversification score based on concentration
        max_city_concentration = max(cities.values()) / total_props if cities else 1
        max_state_concentration = max(states.values()) / total_props if states else 1
        max_type_concentration = max(prop_types.values()) / total_props if prop_types else 1
        
        # Lower concentration = higher diversification
        diversification = 1 - (max_city_concentration + max_state_concentration + max_type_concentration) / 3
        return max(0, diversification)
    
    def _generate_insights(self, performance_metrics: Dict[str, Any], 
                          market_data: Dict[str, Any]) -> List[str]:
        """Generate key insights from analysis"""
        insights = []
        
        cap_rate = performance_metrics.get("portfolio_cap_rate", 0)
        cash_flow = performance_metrics.get("monthly_cash_flow", 0)
        
        if cap_rate > 0.08:
            insights.append(f"Portfolio cap rate of {cap_rate:.1%} exceeds target of 8%")
        elif cap_rate < 0.06:
            insights.append(f"Portfolio cap rate of {cap_rate:.1%} is below market average")
        
        if cash_flow > 1000:
            insights.append(f"Strong monthly cash flow of ${cash_flow:,.2f}")
        elif cash_flow < 0:
            insights.append("Portfolio has negative cash flow requiring attention")
        
        return insights
    
    def _generate_recommendations(self, performance_metrics: Dict[str, Any],
                                top_performers: List[Dict[str, Any]],
                                underperformers: List[Dict[str, Any]]) -> List[InvestmentRecommendation]:
        """Generate investment recommendations"""
        recommendations = []
        
        # Recommendations for underperformers
        for prop in underperformers:
            rec = InvestmentRecommendation(
                recommendation_type="improve",
                priority="high",
                property_id=prop.get("id"),
                target_description=f"Property at {prop.get('address', 'Unknown')}",
                title="Improve Underperforming Property",
                description=f"Property showing cap rate of {prop.get('cap_rate', 0):.1%}",
                rationale="Below target performance metrics",
                expected_impact="Increase cash flow and cap rate",
                estimated_cost=10000,
                estimated_return=2000,
                roi_projection=0.2,
                implementation_steps=[
                    "Analyze rent vs market rates",
                    "Review and optimize expenses",
                    "Consider property improvements"
                ],
                timeline_months=3
            )
            recommendations.append(rec)
        
        return recommendations


class OptimizationEngine(AgentTool):
    """Tool for generating portfolio optimization recommendations"""
    
    def __init__(self):
        super().__init__(
            name="optimization_engine",
            description="Generate portfolio optimization recommendations",
            category=ToolCategory.OPTIMIZATION,
            input_schema={
                "portfolio": "Portfolio",
                "analysis": "PortfolioAnalysis",
                "investment_goals": "Dict[str, Any]"
            },
            output_schema={
                "optimization": "PortfolioOptimization",
                "action_plan": "List[Dict[str, Any]]"
            },
            required_permissions=["read_portfolio", "generate_recommendations"]
        )
    
    async def execute(self, portfolio: Dict[str, Any], analysis: Dict[str, Any],
                     investment_goals: Dict[str, Any], **kwargs) -> ToolResult:
        """Generate optimization recommendations"""
        try:
            logger.info("Generating portfolio optimization recommendations")
            
            # Analyze current performance vs goals
            performance_gaps = self._identify_performance_gaps(analysis, investment_goals)
            
            # Generate optimization strategies
            optimization_strategies = self._generate_optimization_strategies(
                portfolio, analysis, performance_gaps
            )
            
            # Create implementation plan
            action_plan = self._create_action_plan(optimization_strategies)
            
            optimization = {
                "portfolio_id": portfolio.get("id", ""),
                "optimization_date": datetime.now().isoformat(),
                "performance_gaps": performance_gaps,
                "optimization_strategies": optimization_strategies,
                "action_plan": action_plan,
                "projected_improvements": self._project_improvements(optimization_strategies),
                "confidence_score": 0.8
            }
            
            return ToolResult(
                success=True,
                data={
                    "optimization": optimization,
                    "action_plan": action_plan
                },
                execution_time=2.0,
                confidence_score=0.8
            )
            
        except Exception as e:
            logger.error(f"Error in optimization engine: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                execution_time=0.5
            )
    
    def _identify_performance_gaps(self, analysis: Dict[str, Any], 
                                 investment_goals: Dict[str, Any]) -> Dict[str, float]:
        """Identify gaps between current performance and goals"""
        performance_metrics = analysis.get("performance_metrics", {})
        
        gaps = {}
        
        # Cap rate gap
        current_cap_rate = performance_metrics.get("portfolio_cap_rate", 0)
        target_cap_rate = investment_goals.get("target_cap_rate", 0.08)
        gaps["cap_rate_gap"] = target_cap_rate - current_cap_rate
        
        # Cash flow gap
        current_cash_flow = performance_metrics.get("monthly_cash_flow", 0)
        target_cash_flow = investment_goals.get("target_monthly_cash_flow", 1000)
        gaps["cash_flow_gap"] = target_cash_flow - current_cash_flow
        
        return gaps
    
    def _generate_optimization_strategies(self, portfolio: Dict[str, Any],
                                        analysis: Dict[str, Any],
                                        performance_gaps: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization strategies"""
        strategies = []
        
        # Strategy for improving cap rate
        if performance_gaps.get("cap_rate_gap", 0) > 0.01:
            strategies.append({
                "strategy": "improve_cap_rate",
                "description": "Increase rental income and reduce expenses",
                "actions": [
                    "Review market rents and adjust pricing",
                    "Optimize property management expenses",
                    "Improve property condition to justify higher rents"
                ],
                "expected_impact": performance_gaps["cap_rate_gap"] * 0.5
            })
        
        # Strategy for improving cash flow
        if performance_gaps.get("cash_flow_gap", 0) > 100:
            strategies.append({
                "strategy": "improve_cash_flow",
                "description": "Increase net operating income",
                "actions": [
                    "Reduce vacancy rates",
                    "Implement cost-saving measures",
                    "Consider rent increases where appropriate"
                ],
                "expected_impact": performance_gaps["cash_flow_gap"] * 0.6
            })
        
        return strategies
    
    def _create_action_plan(self, optimization_strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create implementation action plan"""
        action_plan = []
        
        for i, strategy in enumerate(optimization_strategies):
            for j, action in enumerate(strategy.get("actions", [])):
                action_plan.append({
                    "phase": f"Phase {i+1}",
                    "action": action,
                    "timeline": f"Month {j+1}",
                    "priority": "high" if i == 0 else "medium",
                    "strategy": strategy["strategy"]
                })
        
        return action_plan
    
    def _project_improvements(self, optimization_strategies: List[Dict[str, Any]]) -> Dict[str, float]:
        """Project improvements from optimization strategies"""
        improvements = {
            "projected_cap_rate_improvement": 0,
            "projected_cash_flow_improvement": 0,
            "projected_roi_improvement": 0
        }
        
        for strategy in optimization_strategies:
            if strategy["strategy"] == "improve_cap_rate":
                improvements["projected_cap_rate_improvement"] += strategy.get("expected_impact", 0)
            elif strategy["strategy"] == "improve_cash_flow":
                improvements["projected_cash_flow_improvement"] += strategy.get("expected_impact", 0)
        
        return improvements


class RiskAnalyzer(AgentTool):
    """Tool for assessing portfolio risk and generating mitigation strategies"""
    
    def __init__(self):
        super().__init__(
            name="risk_analyzer",
            description="Assess portfolio risk and generate mitigation strategies",
            category=ToolCategory.ANALYSIS,
            input_schema={
                "portfolio": "Portfolio",
                "market_conditions": "Dict[str, Any]"
            },
            output_schema={
                "risk_assessment": "RiskAssessment",
                "mitigation_strategies": "List[Dict[str, Any]]"
            },
            required_permissions=["read_portfolio", "analyze_risk"]
        )
    
    async def execute(self, portfolio: Dict[str, Any], market_conditions: Dict[str, Any],
                     **kwargs) -> ToolResult:
        """Assess portfolio risk"""
        try:
            logger.info("Assessing portfolio risk")
            
            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(portfolio)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(portfolio, market_conditions)
            
            # Generate mitigation strategies
            mitigation_strategies = self._generate_mitigation_strategies(risk_factors)
            
            risk_assessment = {
                "portfolio_id": portfolio.get("id", ""),
                "assessment_date": datetime.now().isoformat(),
                "overall_risk_score": risk_metrics["overall_risk_score"],
                "risk_categories": risk_metrics,
                "risk_factors": risk_factors,
                "mitigation_strategies": mitigation_strategies,
                "confidence_score": 0.8
            }
            
            return ToolResult(
                success=True,
                data={
                    "risk_assessment": risk_assessment,
                    "mitigation_strategies": mitigation_strategies
                },
                execution_time=1.5,
                confidence_score=0.8
            )
            
        except Exception as e:
            logger.error(f"Error in risk analysis: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                execution_time=0.5
            )
    
    def _calculate_risk_metrics(self, portfolio: Dict[str, Any]) -> Dict[str, float]:
        """Calculate various risk metrics"""
        properties = portfolio.get("properties", [])
        
        if not properties:
            return {"overall_risk_score": 0}
        
        # Geographic concentration risk
        cities = {}
        for prop in properties:
            city = prop.get("city", "Unknown")
            cities[city] = cities.get(city, 0) + 1
        
        max_city_concentration = max(cities.values()) / len(properties)
        concentration_risk = max_city_concentration * 100  # 0-100 scale
        
        # Leverage risk (simplified)
        total_value = sum(prop.get("current_value", 0) for prop in properties)
        total_debt = total_value * 0.7  # Assume 70% average LTV
        leverage_risk = (total_debt / total_value) * 100 if total_value > 0 else 0
        
        # Overall risk score
        overall_risk_score = (concentration_risk + leverage_risk) / 2
        
        return {
            "overall_risk_score": overall_risk_score,
            "concentration_risk": concentration_risk,
            "leverage_risk": leverage_risk,
            "market_risk": 50,  # Placeholder
            "liquidity_risk": 40  # Placeholder
        }
    
    def _identify_risk_factors(self, portfolio: Dict[str, Any], 
                             market_conditions: Dict[str, Any]) -> List[str]:
        """Identify specific risk factors"""
        risk_factors = []
        
        properties = portfolio.get("properties", [])
        
        # Check for geographic concentration
        cities = {}
        for prop in properties:
            city = prop.get("city", "Unknown")
            cities[city] = cities.get(city, 0) + 1
        
        max_concentration = max(cities.values()) / len(properties) if properties else 0
        if max_concentration > 0.5:
            risk_factors.append(f"High geographic concentration: {max_concentration:.1%} in single market")
        
        # Check for property type concentration
        prop_types = {}
        for prop in properties:
            prop_type = prop.get("property_type", "Unknown")
            prop_types[prop_type] = prop_types.get(prop_type, 0) + 1
        
        max_type_concentration = max(prop_types.values()) / len(properties) if properties else 0
        if max_type_concentration > 0.7:
            risk_factors.append(f"High property type concentration: {max_type_concentration:.1%} in single type")
        
        # Market-based risks
        if market_conditions.get("market_temperature") == "hot":
            risk_factors.append("Market overheating risk - prices may be inflated")
        
        return risk_factors
    
    def _generate_mitigation_strategies(self, risk_factors: List[str]) -> List[Dict[str, Any]]:
        """Generate risk mitigation strategies"""
        strategies = []
        
        for risk_factor in risk_factors:
            if "geographic concentration" in risk_factor:
                strategies.append({
                    "risk": risk_factor,
                    "strategy": "Geographic Diversification",
                    "actions": [
                        "Consider acquisitions in different markets",
                        "Research emerging markets with growth potential",
                        "Gradually reduce concentration in single market"
                    ],
                    "timeline": "6-12 months",
                    "priority": "high"
                })
            elif "property type concentration" in risk_factor:
                strategies.append({
                    "risk": risk_factor,
                    "strategy": "Property Type Diversification",
                    "actions": [
                        "Explore different property types",
                        "Consider commercial vs residential mix",
                        "Evaluate multi-family opportunities"
                    ],
                    "timeline": "3-6 months",
                    "priority": "medium"
                })
        
        return strategies


class MarketAnalyzer(AgentTool):
    """Tool for analyzing market conditions for investment decisions"""
    
    def __init__(self):
        super().__init__(
            name="market_analyzer",
            description="Analyze market conditions for investment decisions",
            category=ToolCategory.ANALYSIS,
            input_schema={
                "geographic_areas": "List[str]",
                "property_types": "List[str]"
            },
            output_schema={
                "market_analysis": "MarketAnalysis",
                "investment_timing": "Dict[str, Any]"
            },
            required_permissions=["read_market_data", "analyze_trends"]
        )
    
    async def execute(self, geographic_areas: List[str], property_types: List[str],
                     **kwargs) -> ToolResult:
        """Analyze market conditions"""
        try:
            logger.info(f"Analyzing market conditions for {len(geographic_areas)} areas")
            
            # Simulate market analysis (in real implementation, would fetch actual data)
            market_analysis = self._analyze_market_conditions(geographic_areas, property_types)
            
            # Generate investment timing recommendations
            investment_timing = self._analyze_investment_timing(market_analysis)
            
            return ToolResult(
                success=True,
                data={
                    "market_analysis": market_analysis,
                    "investment_timing": investment_timing
                },
                execution_time=2.0,
                confidence_score=0.75
            )
            
        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                execution_time=0.5
            )
    
    def _analyze_market_conditions(self, geographic_areas: List[str], 
                                 property_types: List[str]) -> Dict[str, Any]:
        """Analyze current market conditions"""
        # Simulated market analysis
        return {
            "analysis_date": datetime.now().isoformat(),
            "geographic_scope": ", ".join(geographic_areas),
            "median_home_price": 350000,
            "price_appreciation_yoy": 0.08,
            "days_on_market": 25,
            "inventory_months": 2.5,
            "median_rent": 2500,
            "rent_growth_yoy": 0.06,
            "vacancy_rate": 0.04,
            "cap_rate_average": 0.075,
            "market_cycle_phase": "expansion",
            "market_temperature": "warm",
            "buy_recommendation": "buy",
            "confidence_score": 0.75
        }
    
    def _analyze_investment_timing(self, market_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze investment timing based on market conditions"""
        market_temp = market_analysis.get("market_temperature", "balanced")
        cycle_phase = market_analysis.get("market_cycle_phase", "expansion")
        
        if market_temp == "hot" and cycle_phase == "expansion":
            timing_recommendation = "caution"
            timing_rationale = "Market may be overheated, consider waiting for better opportunities"
        elif market_temp == "cool" and cycle_phase == "recession":
            timing_recommendation = "buy"
            timing_rationale = "Good buying opportunity with lower prices"
        else:
            timing_recommendation = "neutral"
            timing_rationale = "Balanced market conditions, proceed with normal criteria"
        
        return {
            "timing_recommendation": timing_recommendation,
            "timing_rationale": timing_rationale,
            "market_cycle_position": 0.6,  # 0-1 scale within cycle
            "optimal_strategies": ["buy_and_hold", "value_add"],
            "risks_to_monitor": ["interest_rate_changes", "economic_indicators"]
        }