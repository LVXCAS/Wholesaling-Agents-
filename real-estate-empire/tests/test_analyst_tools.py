"""
Test Analyst Agent Tools Implementation
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

from app.agents.analyst_tools import (
    ComparablePropertyFinderTool,
    RepairCostEstimatorTool,
    FinancialCalculatorTool,
    InvestmentStrategyAnalyzerTool,
    RiskAssessmentTool,
    MarketDataAnalysisTool,
    AnalystToolManager
)


class TestAnalystTools:
    """Test Analyst Agent tools"""
    
    @pytest.mark.asyncio
    async def test_comparable_property_finder_tool(self):
        """Test comparable property finder tool"""
        tool = ComparablePropertyFinderTool()
        
        result = await tool.execute(
            property_address="123 Test St",
            property_type="single_family",
            bedrooms=3,
            bathrooms=2,
            square_feet=1500,
            max_distance=2.0,
            max_age=180
        )
        
        assert "comparable_properties" in result
        assert "valuation_estimate" in result
        assert "search_parameters" in result
        
        # Check comparable properties
        comps = result["comparable_properties"]
        assert len(comps) == 5
        
        for comp in comps:
            assert "address" in comp
            assert "sale_price" in comp
            assert "sale_date" in comp
            assert "similarity_score" in comp
            assert "distance_miles" in comp
            assert "price_per_sqft" in comp
            assert "adjustments" in comp
        
        # Check valuation estimate
        valuation = result["valuation_estimate"]
        assert "estimated_value" in valuation
        assert "price_per_sqft" in valuation
        assert "confidence_score" in valuation
        assert "comp_count" in valuation
        assert valuation["comp_count"] == 5
    
    @pytest.mark.asyncio
    async def test_repair_cost_estimator_tool(self):
        """Test repair cost estimator tool"""
        tool = RepairCostEstimatorTool()
        
        result = await tool.execute(
            property_photos=["photo1.jpg", "photo2.jpg"],
            property_description="Needs kitchen and bathroom updates",
            property_age=25,
            square_feet=1500,
            property_condition="fair"
        )
        
        assert "repair_estimate" in result
        assert "line_items" in result
        assert "repair_categories" in result
        assert "analysis_factors" in result
        
        # Check repair estimate
        estimate = result["repair_estimate"]
        assert "total_cost" in estimate
        assert "subtotal" in estimate
        assert "contingency_amount" in estimate
        assert "contingency_percentage" in estimate
        assert "confidence_score" in estimate
        assert "timeline_days" in estimate
        assert estimate["contingency_percentage"] == 0.15
        
        # Check line items
        line_items = result["line_items"]
        assert isinstance(line_items, dict)
        assert len(line_items) > 0
        
        # Check repair categories
        categories = result["repair_categories"]
        assert "priority_repairs" in categories
        assert "cosmetic_repairs" in categories
        assert "structural_repairs" in categories
    
    @pytest.mark.asyncio
    async def test_financial_calculator_tool(self):
        """Test financial calculator tool"""
        tool = FinancialCalculatorTool()
        
        result = await tool.execute(
            purchase_price=275000,
            repair_cost=25000,
            arv=350000,
            monthly_rent=2500,
            down_payment_percentage=0.25,
            interest_rate=0.07,
            loan_term_years=30
        )
        
        assert "financial_metrics" in result
        assert "expense_breakdown" in result
        assert "assumptions" in result
        
        # Check financial metrics
        metrics = result["financial_metrics"]
        required_metrics = [
            "purchase_price", "repair_cost", "total_investment", "after_repair_value",
            "monthly_rent", "monthly_cash_flow", "annual_cash_flow",
            "cap_rate", "cash_on_cash_return", "gross_rent_multiplier",
            "flip_profit", "flip_roi", "wholesale_fee", "wholesale_margin"
        ]
        
        for metric in required_metrics:
            assert metric in metrics
        
        # Verify calculations
        assert metrics["purchase_price"] == 275000
        assert metrics["repair_cost"] == 25000
        assert metrics["total_investment"] == 300000
        assert metrics["after_repair_value"] == 350000
        assert metrics["monthly_rent"] == 2500
        
        # Check expense breakdown
        expenses = result["expense_breakdown"]
        expense_categories = [
            "monthly_mortgage", "insurance", "property_tax",
            "vacancy_loss", "management", "maintenance", "capex"
        ]
        
        for category in expense_categories:
            assert category in expenses
    
    @pytest.mark.asyncio
    async def test_investment_strategy_analyzer_tool(self):
        """Test investment strategy analyzer tool"""
        tool = InvestmentStrategyAnalyzerTool()
        
        financial_metrics = {
            "total_investment": 300000,
            "after_repair_value": 350000,
            "annual_cash_flow": 6000,
            "cap_rate": 0.08,
            "flip_profit": 30000,
            "wholesale_fee": 8000,
            "cash_on_cash_return": 0.12,
            "flip_roi": 0.10,
            "wholesale_margin": 0.03,
            "down_payment": 75000
        }
        
        market_conditions = {
            "market_temperature": "warm",
            "appreciation_forecast": 0.03,
            "rental_demand": "moderate"
        }
        
        result = await tool.execute(
            financial_metrics=financial_metrics,
            market_conditions=market_conditions,
            investor_profile={}
        )
        
        assert "strategies" in result
        assert "recommended_strategy" in result
        assert "strategy_count" in result
        assert "market_analysis" in result
        
        # Check strategies
        strategies = result["strategies"]
        assert len(strategies) > 0
        
        for strategy in strategies:
            required_fields = [
                "strategy_type", "potential_profit", "roi", "risk_level",
                "timeline_days", "funding_required", "pros", "cons",
                "confidence_score", "market_suitability", "risk_adjusted_score"
            ]
            
            for field in required_fields:
                assert field in strategy
            
            # Verify data types and ranges
            assert isinstance(strategy["pros"], list)
            assert isinstance(strategy["cons"], list)
            assert 0.0 <= strategy["confidence_score"] <= 1.0
            assert 0.0 <= strategy["risk_level"] <= 10.0
        
        # Check that strategies are sorted by risk-adjusted score
        scores = [s["risk_adjusted_score"] for s in strategies]
        assert scores == sorted(scores, reverse=True)
        
        # Check market analysis
        market_analysis = result["market_analysis"]
        assert "market_temperature" in market_analysis
        assert "rental_demand" in market_analysis
        assert "strategy_favorability" in market_analysis
    
    @pytest.mark.asyncio
    async def test_risk_assessment_tool(self):
        """Test risk assessment tool"""
        tool = RiskAssessmentTool()
        
        property_data = {
            "year_built": 1990,
            "condition": "fair",
            "location_quality": "good",
            "neighborhood_trend": "stable",
            "days_on_market": 45,
            "property_type": "single_family"
        }
        
        financial_metrics = {
            "cap_rate": 0.07,
            "monthly_cash_flow": 300,
            "roi": 0.12,
            "loan_amount": 225000,
            "total_investment": 300000
        }
        
        market_conditions = {
            "market_temperature": "warm",
            "inventory_level": "normal",
            "price_change_yoy": 0.02
        }
        
        result = await tool.execute(
            property_data=property_data,
            financial_metrics=financial_metrics,
            market_conditions=market_conditions,
            analysis_data={"comparable_properties": [1, 2, 3]}
        )
        
        assert "risk_assessment" in result
        assert "risk_breakdown" in result
        assert "mitigation_strategies" in result
        
        # Check risk assessment
        risk_assessment = result["risk_assessment"]
        assert "overall_risk_score" in risk_assessment
        assert "risk_level" in risk_assessment
        assert "confidence_score" in risk_assessment
        assert "risk_factors" in risk_assessment
        assert "risk_categories" in risk_assessment
        
        # Verify risk score range
        assert 1.0 <= risk_assessment["overall_risk_score"] <= 10.0
        assert 0.0 <= risk_assessment["confidence_score"] <= 1.0
        
        # Verify risk level mapping
        risk_level = risk_assessment["risk_level"]
        assert risk_level in ["low", "moderate", "high", "very_high"]
        
        # Check risk breakdown
        risk_breakdown = result["risk_breakdown"]
        risk_categories = [
            "financial_risk", "property_risk", "market_risk",
            "location_risk", "liquidity_risk", "financing_risk"
        ]
        
        for category in risk_categories:
            assert category in risk_breakdown
            assert 1.0 <= risk_breakdown[category] <= 10.0
        
        # Check mitigation strategies
        mitigation_strategies = result["mitigation_strategies"]
        assert isinstance(mitigation_strategies, list)
    
    @pytest.mark.asyncio
    async def test_market_data_analysis_tool(self):
        """Test market data analysis tool"""
        tool = MarketDataAnalysisTool()
        
        result = await tool.execute(
            property_address="123 Market St",
            property_type="single_family",
            zip_code="12345",
            analysis_period=12
        )
        
        assert "market_analysis" in result
        assert "timestamp" in result
        
        # Check market analysis structure
        analysis = result["market_analysis"]
        required_fields = [
            "property_address", "zip_code", "analysis_date", "analysis_period_months",
            "price_trends", "price_appreciation_6m", "market_temperature",
            "rental_market", "neighborhood_metrics", "investment_attractiveness",
            "market_forecast", "key_insights"
        ]
        
        for field in required_fields:
            assert field in analysis
        
        # Check price trends
        price_trends = analysis["price_trends"]
        assert len(price_trends) == 12
        
        for trend in price_trends:
            assert "date" in trend
            assert "median_price" in trend
            assert "price_change_mom" in trend
            assert "inventory_level" in trend
            assert "days_on_market" in trend
            assert "sales_volume" in trend
        
        # Check rental market data
        rental_market = analysis["rental_market"]
        rental_fields = ["median_rent", "rent_growth_yoy", "vacancy_rate", "rental_demand", "rent_to_price_ratio"]
        for field in rental_fields:
            assert field in rental_market
        
        # Check neighborhood metrics
        neighborhood = analysis["neighborhood_metrics"]
        neighborhood_fields = [
            "walkability_score", "school_rating", "crime_index", "employment_growth",
            "population_growth", "median_income", "amenities_score"
        ]
        for field in neighborhood_fields:
            assert field in neighborhood
        
        # Check investment attractiveness
        attractiveness = analysis["investment_attractiveness"]
        assert "overall_score" in attractiveness
        assert "score_breakdown" in attractiveness
        assert "recommendation" in attractiveness
        assert 0.0 <= attractiveness["overall_score"] <= 1.0
        assert attractiveness["recommendation"] in ["strong_buy", "buy", "hold", "avoid"]
        
        # Check market forecast
        forecast = analysis["market_forecast"]
        assert len(forecast) == 6  # 6 months forecast
        
        for month_forecast in forecast:
            assert "date" in month_forecast
            assert "predicted_price" in month_forecast
            assert "predicted_rent" in month_forecast
            assert "confidence" in month_forecast
            assert 0.0 <= month_forecast["confidence"] <= 1.0
        
        # Check key insights
        insights = analysis["key_insights"]
        assert isinstance(insights, list)
    
    @pytest.mark.asyncio
    async def test_tool_error_handling(self):
        """Test tool error handling"""
        tool = ComparablePropertyFinderTool()
        
        # Test with invalid parameters that might cause errors
        with patch('asyncio.sleep', side_effect=Exception("Test error")):
            result = await tool.execute(
                property_address="",
                square_feet=-1000  # Invalid value
            )
            
            assert "error" in result
            assert "comparable_properties" in result
            assert result["comparable_properties"] == []
    
    def test_analyst_tool_manager_initialization(self):
        """Test analyst tool manager initialization"""
        manager = AnalystToolManager()
        
        expected_tools = [
            "comparable_property_finder",
            "repair_cost_estimator", 
            "financial_calculator",
            "investment_strategy_analyzer",
            "risk_assessment_tool",
            "market_data_analysis"
        ]
        
        assert len(manager.tools) == len(expected_tools)
        for tool_name in expected_tools:
            assert tool_name in manager.tools
            assert tool_name in manager.usage_stats
            assert manager.usage_stats[tool_name]["calls"] == 0
            assert manager.usage_stats[tool_name]["errors"] == 0
    
    @pytest.mark.asyncio
    async def test_analyst_tool_manager_execute_tool(self):
        """Test analyst tool manager tool execution"""
        manager = AnalystToolManager()
        
        # Test successful tool execution
        result = await manager.execute_tool(
            "financial_calculator",
            purchase_price=250000,
            repair_cost=20000,
            monthly_rent=2000
        )
        
        assert result["success"] is True
        assert result["tool"] == "financial_calculator"
        assert "result" in result
        assert "timestamp" in result
        
        # Check usage stats updated
        assert manager.usage_stats["financial_calculator"]["calls"] == 1
        assert manager.usage_stats["financial_calculator"]["errors"] == 0
    
    @pytest.mark.asyncio
    async def test_analyst_tool_manager_unknown_tool(self):
        """Test analyst tool manager with unknown tool"""
        manager = AnalystToolManager()
        
        result = await manager.execute_tool("unknown_tool")
        
        assert result["success"] is False
        assert "error" in result
        assert "Tool not found" in result["error"]
        assert "available_tools" in result
    
    def test_analyst_tool_manager_get_tool_stats(self):
        """Test getting tool statistics"""
        manager = AnalystToolManager()
        
        # Simulate some usage
        manager.usage_stats["financial_calculator"]["calls"] = 5
        manager.usage_stats["financial_calculator"]["errors"] = 1
        manager.usage_stats["repair_cost_estimator"]["calls"] = 3
        
        stats = manager.get_tool_stats()
        
        assert "tools" in stats
        assert "usage_stats" in stats
        assert "total_calls" in stats
        assert "total_errors" in stats
        
        assert stats["total_calls"] == 8
        assert stats["total_errors"] == 1
        assert len(stats["tools"]) == 6
    
    def test_analyst_tool_manager_get_available_tools(self):
        """Test getting available tools list"""
        manager = AnalystToolManager()
        
        tools = manager.get_available_tools()
        
        expected_tools = [
            "comparable_property_finder",
            "repair_cost_estimator",
            "financial_calculator", 
            "investment_strategy_analyzer",
            "risk_assessment_tool",
            "market_data_analysis"
        ]
        
        assert len(tools) == len(expected_tools)
        for tool in expected_tools:
            assert tool in tools
    
    @pytest.mark.asyncio
    async def test_financial_calculator_edge_cases(self):
        """Test financial calculator with edge cases"""
        tool = FinancialCalculatorTool()
        
        # Test with zero interest rate
        result = await tool.execute(
            purchase_price=200000,
            repair_cost=0,
            monthly_rent=1500,
            interest_rate=0.0,
            down_payment_percentage=1.0  # 100% cash purchase
        )
        
        assert result["financial_metrics"]["monthly_mortgage"] == 0
        assert result["financial_metrics"]["loan_amount"] == 0
        
        # Test with very high cap rate property
        result = await tool.execute(
            purchase_price=100000,
            repair_cost=10000,
            monthly_rent=2000,  # Very high rent
            down_payment_percentage=0.25
        )
        
        metrics = result["financial_metrics"]
        assert metrics["cap_rate"] > 0.15  # Should be high cap rate
        assert metrics["monthly_cash_flow"] > 500  # Should be positive cash flow (reduced threshold)
    
    @pytest.mark.asyncio
    async def test_repair_estimator_condition_variations(self):
        """Test repair estimator with different property conditions"""
        tool = RepairCostEstimatorTool()
        
        conditions = ["excellent", "good", "fair", "poor", "distressed"]
        square_feet = 1500
        
        results = []
        for condition in conditions:
            result = await tool.execute(
                property_condition=condition,
                square_feet=square_feet,
                property_age=20
            )
            results.append(result["repair_estimate"]["total_cost"])
        
        # Costs should generally increase with worse condition
        # (though there's randomness in the simulation)
        assert len(results) == len(conditions)
        
        # Test that all results are reasonable positive values
        for cost in results:
            assert cost > 0
            assert cost < 200000  # Reasonable upper bound
        
        # Test that excellent condition generally costs less than poor/distressed
        # Run multiple times to account for randomness
        excellent_costs = []
        distressed_costs = []
        
        for _ in range(5):
            excellent_result = await tool.execute(
                property_condition="excellent",
                square_feet=square_feet,
                property_age=20
            )
            distressed_result = await tool.execute(
                property_condition="distressed", 
                square_feet=square_feet,
                property_age=20
            )
            excellent_costs.append(excellent_result["repair_estimate"]["total_cost"])
            distressed_costs.append(distressed_result["repair_estimate"]["total_cost"])
        
        # Average should show the expected pattern
        avg_excellent = sum(excellent_costs) / len(excellent_costs)
        avg_distressed = sum(distressed_costs) / len(distressed_costs)
        assert avg_distressed > avg_excellent
    
    @pytest.mark.asyncio
    async def test_strategy_analyzer_market_conditions(self):
        """Test strategy analyzer with different market conditions"""
        tool = InvestmentStrategyAnalyzerTool()
        
        base_metrics = {
            "total_investment": 300000,
            "after_repair_value": 350000,
            "annual_cash_flow": 6000,
            "cap_rate": 0.08,
            "flip_profit": 30000,
            "cash_on_cash_return": 0.12,
            "flip_roi": 0.10
        }
        
        # Test hot market
        hot_market = {
            "market_temperature": "hot",
            "rental_demand": "high"
        }
        
        hot_result = await tool.execute(
            financial_metrics=base_metrics,
            market_conditions=hot_market
        )
        
        # Test cold market
        cold_market = {
            "market_temperature": "cold",
            "rental_demand": "low"
        }
        
        cold_result = await tool.execute(
            financial_metrics=base_metrics,
            market_conditions=cold_market
        )
        
        # Hot market should favor flipping, cold market should be more conservative
        hot_strategies = {s["strategy_type"]: s for s in hot_result["strategies"]}
        cold_strategies = {s["strategy_type"]: s for s in cold_result["strategies"]}
        
        if "fix_and_flip" in hot_strategies and "fix_and_flip" in cold_strategies:
            assert hot_strategies["fix_and_flip"]["market_suitability"] >= cold_strategies["fix_and_flip"]["market_suitability"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])