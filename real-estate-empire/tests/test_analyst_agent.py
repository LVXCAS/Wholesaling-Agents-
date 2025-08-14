"""
Test Analyst Agent Implementation
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

from app.agents.analyst_agent import AnalystAgent, PropertyAnalysis, PropertyValuation, RepairEstimate, FinancialMetrics, InvestmentStrategy
from app.core.agent_state import AgentState, StateManager, AgentType, DealStatus


class TestAnalystAgent:
    """Test Analyst Agent implementation"""
    
    @pytest.fixture
    def analyst_agent(self):
        """Create an analyst agent for testing"""
        return AnalystAgent(name="TestAnalystAgent")
    
    @pytest.fixture
    def sample_state(self):
        """Create sample agent state"""
        return StateManager.create_initial_state()
    
    @pytest.fixture
    def sample_deal(self):
        """Create sample deal for analysis"""
        return {
            "id": "deal-1",
            "property_address": "123 Analysis St",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701",
            "property_type": "single_family",
            "bedrooms": 3,
            "bathrooms": 2,
            "square_feet": 1500,
            "lot_size": 0.25,
            "year_built": 1995,
            "listing_price": 275000,
            "days_on_market": 45,
            "condition": "fair",
            "photos": ["photo1.jpg", "photo2.jpg"],
            "description": "Nice property in good neighborhood",
            "status": DealStatus.DISCOVERED.value,
            "analyzed": False
        }
    
    @pytest.fixture
    def sample_state_with_deals(self, sample_state, sample_deal):
        """Create state with deals to analyze"""
        sample_state["current_deals"] = [sample_deal]
        return sample_state
    
    def test_analyst_agent_initialization(self, analyst_agent):
        """Test analyst agent initialization"""
        assert analyst_agent.name == "TestAnalystAgent"
        assert analyst_agent.agent_type == AgentType.ANALYST
        assert len(analyst_agent.capabilities) == 5
        assert analyst_agent.default_cap_rate_threshold == 0.08
        assert analyst_agent.default_cash_flow_threshold == 200
        assert analyst_agent.analyses_completed_today == 0
        
        # Check capabilities
        capability_names = [cap.name for cap in analyst_agent.capabilities]
        expected_capabilities = [
            "property_valuation",
            "repair_estimation", 
            "financial_analysis",
            "strategy_analysis",
            "risk_assessment"
        ]
        for expected in expected_capabilities:
            assert expected in capability_names
    
    def test_get_available_tasks(self, analyst_agent):
        """Test getting available tasks"""
        tasks = analyst_agent.get_available_tasks()
        expected_tasks = [
            "analyze_property",
            "valuate_property",
            "estimate_repairs",
            "calculate_financials",
            "analyze_strategies",
            "assess_risk"
        ]
        
        assert len(tasks) == len(expected_tasks)
        for task in expected_tasks:
            assert task in tasks
    
    @pytest.mark.asyncio
    async def test_analyze_property_task(self, analyst_agent, sample_deal, sample_state):
        """Test property analysis task execution"""
        # Mock the agent executor to avoid actual LLM calls
        from unittest.mock import AsyncMock
        analyst_agent.agent_executor = Mock()
        analyst_agent.agent_executor.ainvoke = AsyncMock(return_value={"output": "Mock analysis result"})
        
        result = await analyst_agent.execute_task(
            "analyze_property",
            {"deal": sample_deal},
            sample_state
        )
        
        assert result["success"] is True
        assert "analysis" in result
        assert "deal_id" in result
        assert "analysis_timestamp" in result
        
        # Check analysis structure
        analysis = result["analysis"]
        assert "valuation" in analysis
        assert "repair_estimate" in analysis
        assert "financial_metrics" in analysis
        assert "strategies" in analysis
        assert "investment_recommendation" in analysis
        assert "confidence_level" in analysis
    
    @pytest.mark.asyncio
    async def test_process_state_with_deals(self, analyst_agent, sample_state_with_deals):
        """Test processing state with deals to analyze"""
        # Mock the agent executor
        from unittest.mock import AsyncMock
        analyst_agent.agent_executor = Mock()
        analyst_agent.agent_executor.ainvoke = AsyncMock(return_value={"output": "Mock analysis result"})
        
        updated_state = await analyst_agent.process_state(sample_state_with_deals)
        
        # Check that deal was analyzed
        deal = updated_state["current_deals"][0]
        assert deal["analyzed"] is True
        assert "analysis_data" in deal
        assert "analyst_recommendation" in deal
        assert "confidence_score" in deal
        
        # Check that agent message was added
        assert len(updated_state["agent_messages"]) > 0
        analyst_messages = [msg for msg in updated_state["agent_messages"] 
                          if msg.get("agent") == AgentType.ANALYST.value]
        assert len(analyst_messages) > 0
    
    @pytest.mark.asyncio
    async def test_process_state_no_deals(self, analyst_agent, sample_state):
        """Test processing state with no deals to analyze"""
        updated_state = await analyst_agent.process_state(sample_state)
        
        # State should be unchanged
        assert updated_state == sample_state
    
    @pytest.mark.asyncio
    async def test_process_state_already_analyzed_deals(self, analyst_agent, sample_state_with_deals):
        """Test processing state with already analyzed deals"""
        # Mark deal as already analyzed
        sample_state_with_deals["current_deals"][0]["analyzed"] = True
        
        updated_state = await analyst_agent.process_state(sample_state_with_deals)
        
        # No new analysis should be performed
        assert len(updated_state["agent_messages"]) == 0
    
    def test_parse_analysis_results(self, analyst_agent, sample_deal):
        """Test parsing of analysis results"""
        llm_output = "Mock LLM analysis output"
        
        analysis = analyst_agent._parse_analysis_results(llm_output, sample_deal)
        
        # Check required fields
        assert "id" in analysis
        assert "property_id" in analysis
        assert "analysis_date" in analysis
        assert "valuation" in analysis
        assert "repair_estimate" in analysis
        assert "financial_metrics" in analysis
        assert "strategies" in analysis
        assert "investment_recommendation" in analysis
        assert "confidence_level" in analysis
        
        # Check valuation structure
        valuation = analysis["valuation"]
        assert "arv" in valuation
        assert "current_value" in valuation
        assert "confidence_score" in valuation
        assert "comp_count" in valuation
        
        # Check repair estimate structure
        repair_estimate = analysis["repair_estimate"]
        assert "total_cost" in repair_estimate
        assert "confidence_score" in repair_estimate
        assert "line_items" in repair_estimate
        assert "contingency_percentage" in repair_estimate
        
        # Check financial metrics structure
        financial_metrics = analysis["financial_metrics"]
        assert "purchase_price" in financial_metrics
        assert "repair_cost" in financial_metrics
        assert "total_investment" in financial_metrics
        assert "after_repair_value" in financial_metrics
        assert "cap_rate" in financial_metrics
        assert "cash_on_cash_return" in financial_metrics
        
        # Check strategies
        strategies = analysis["strategies"]
        assert len(strategies) > 0
        for strategy in strategies:
            assert "strategy_type" in strategy
            assert "potential_profit" in strategy
            assert "roi" in strategy
            assert "risk_level" in strategy
            assert "confidence_score" in strategy
    
    def test_generate_sample_comps(self, analyst_agent, sample_deal):
        """Test generation of sample comparable properties"""
        comps = analyst_agent._generate_sample_comps(sample_deal)
        
        assert len(comps) == 5
        
        for comp in comps:
            assert "address" in comp
            assert "sale_price" in comp
            assert "sale_date" in comp
            assert "bedrooms" in comp
            assert "bathrooms" in comp
            assert "square_feet" in comp
            assert "distance_miles" in comp
            assert "similarity_score" in comp
            assert "adjustments" in comp
    
    def test_analysis_parameters_setup(self, analyst_agent):
        """Test analysis parameters setup"""
        params = analyst_agent.analysis_parameters
        
        assert "valuation" in params
        assert "repair_estimation" in params
        assert "financial_analysis" in params
        
        # Check valuation parameters
        valuation_params = params["valuation"]
        assert "min_comps" in valuation_params
        assert "max_comp_distance" in valuation_params
        assert "max_comp_age" in valuation_params
        assert "adjustment_factors" in valuation_params
        
        # Check repair estimation parameters
        repair_params = params["repair_estimation"]
        assert "contingency_percentage" in repair_params
        assert "labor_cost_multiplier" in repair_params
        
        # Check financial analysis parameters
        financial_params = params["financial_analysis"]
        assert "vacancy_rate" in financial_params
        assert "management_fee" in financial_params
        assert "maintenance_reserve" in financial_params
    
    def test_analysis_workflows_setup(self, analyst_agent):
        """Test analysis workflows setup"""
        workflows = analyst_agent.analysis_workflows
        
        assert "comprehensive" in workflows
        assert "quick" in workflows
        assert "detailed" in workflows
        
        # Check comprehensive workflow
        comprehensive = workflows["comprehensive"]
        expected_steps = [
            "property_valuation",
            "repair_estimation",
            "financial_analysis", 
            "strategy_analysis",
            "risk_assessment"
        ]
        assert comprehensive == expected_steps
        
        # Check quick workflow
        quick = workflows["quick"]
        assert len(quick) < len(comprehensive)
        assert "property_valuation" in quick
        assert "financial_analysis" in quick
    
    @pytest.mark.asyncio
    async def test_task_execution_error_handling(self, analyst_agent, sample_deal, sample_state):
        """Test error handling in task execution"""
        # Test unknown task
        result = await analyst_agent.execute_task(
            "unknown_task",
            {"deal": sample_deal},
            sample_state
        )
        
        assert result["success"] is False
        assert "error" in result
        assert "Unknown task" in result["error"]
    
    @pytest.mark.asyncio
    async def test_state_processing_error_handling(self, analyst_agent, sample_state):
        """Test error handling in state processing"""
        # Create invalid state that will cause error
        invalid_state = sample_state.copy()
        invalid_state["current_deals"] = [{"invalid": "deal"}]  # Missing required fields
        
        # Mock agent executor to raise exception
        from unittest.mock import AsyncMock
        analyst_agent.agent_executor = Mock()
        analyst_agent.agent_executor.ainvoke = AsyncMock(side_effect=Exception("Test error"))
        
        updated_state = await analyst_agent.process_state(invalid_state)
        
        # Should have error message
        error_messages = [msg for msg in updated_state["agent_messages"] 
                         if msg.get("agent") == AgentType.ANALYST.value and "Error" in msg.get("message", "")]
        assert len(error_messages) > 0
    
    def test_get_analysis_history(self, analyst_agent):
        """Test getting analysis history"""
        # Add some mock analysis to history
        test_analysis = {"test": "analysis"}
        analyst_agent.analysis_history["property-1"] = test_analysis
        
        # Test getting specific property history
        history = analyst_agent.get_analysis_history("property-1")
        assert history == test_analysis
        
        # Test getting all history
        all_history = analyst_agent.get_analysis_history()
        assert "property-1" in all_history
        assert all_history["property-1"] == test_analysis
        
        # Test getting non-existent property
        empty_history = analyst_agent.get_analysis_history("non-existent")
        assert empty_history == {}
    
    def test_get_performance_metrics(self, analyst_agent):
        """Test getting performance metrics"""
        # Set some test metrics
        analyst_agent.analyses_completed_today = 5
        analyst_agent.total_analyses_completed = 25
        analyst_agent.average_analysis_time = 120.5
        analyst_agent.accuracy_score = 0.85
        
        metrics = analyst_agent.get_performance_metrics()
        
        assert metrics["analyses_completed_today"] == 5
        assert metrics["total_analyses_completed"] == 25
        assert metrics["average_analysis_time"] == 120.5
        assert metrics["accuracy_score"] == 0.85
        assert "cache_hit_rate" in metrics
        assert "agent_metrics" in metrics
    
    def test_market_cache_initialization(self, analyst_agent):
        """Test market cache initialization"""
        assert isinstance(analyst_agent.market_cache, dict)
        assert len(analyst_agent.market_cache) == 0
        assert analyst_agent.cache_expiry.total_seconds() == 6 * 3600  # 6 hours
    
    @pytest.mark.asyncio
    async def test_comprehensive_analysis_workflow(self, analyst_agent, sample_deal, sample_state):
        """Test comprehensive analysis workflow execution"""
        # Mock the agent executor
        from unittest.mock import AsyncMock
        analyst_agent.agent_executor = Mock()
        analyst_agent.agent_executor.ainvoke = AsyncMock(return_value={"output": "Comprehensive analysis"})
        
        result = await analyst_agent._analyze_property({"deal": sample_deal}, sample_state)
        
        assert result["success"] is True
        analysis = result["analysis"]
        
        # Verify all components of comprehensive analysis
        assert "valuation" in analysis
        assert "repair_estimate" in analysis
        assert "financial_metrics" in analysis
        assert "strategies" in analysis
        assert "risk_factors" in analysis
        assert "investment_recommendation" in analysis
        
        # Verify investment recommendation logic
        recommendation = analysis["investment_recommendation"]
        assert recommendation in ["proceed", "caution", "reject"]
        
        # Verify confidence level
        confidence = analysis["confidence_level"]
        assert 0.0 <= confidence <= 1.0
    
    def test_investment_recommendation_logic(self, analyst_agent, sample_deal):
        """Test investment recommendation logic"""
        # Test different scenarios
        
        # High cap rate and cash flow - should recommend proceed
        high_performance_deal = sample_deal.copy()
        high_performance_deal["listing_price"] = 200000  # Lower price for better metrics
        
        analysis = analyst_agent._parse_analysis_results("", high_performance_deal)
        
        # The logic should be based on financial metrics
        financial_metrics = analysis["financial_metrics"]
        if (financial_metrics["cap_rate"] >= 0.08 and 
            financial_metrics["monthly_cash_flow"] >= 200):
            assert analysis["investment_recommendation"] == "proceed"
    
    def test_risk_factor_identification(self, analyst_agent, sample_deal):
        """Test risk factor identification"""
        # Test deal with potential risk factors
        risky_deal = sample_deal.copy()
        risky_deal["listing_price"] = 500000  # High price
        risky_deal["days_on_market"] = 150  # Long time on market
        risky_deal["condition"] = "poor"  # Poor condition
        
        analysis = analyst_agent._parse_analysis_results("", risky_deal)
        
        risk_factors = analysis["risk_factors"]
        assert isinstance(risk_factors, list)
        
        # Should identify some risk factors for this risky deal
        if analysis["financial_metrics"]["cap_rate"] < 0.06:
            assert any("cap rate" in factor.lower() for factor in risk_factors)
    
    @pytest.mark.asyncio
    async def test_multiple_deals_processing(self, analyst_agent, sample_state):
        """Test processing multiple deals simultaneously"""
        # Create multiple deals
        deals = []
        for i in range(3):
            deal = {
                "id": f"deal-{i}",
                "property_address": f"{100 + i * 10} Test St",
                "city": "Austin",
                "state": "TX",
                "listing_price": 250000 + i * 25000,
                "status": DealStatus.DISCOVERED.value,
                "analyzed": False
            }
            deals.append(deal)
        
        sample_state["current_deals"] = deals
        
        # Mock agent executor
        from unittest.mock import AsyncMock
        analyst_agent.agent_executor = Mock()
        analyst_agent.agent_executor.ainvoke = AsyncMock(return_value={"output": "Analysis result"})
        
        updated_state = await analyst_agent.process_state(sample_state)
        
        # All deals should be analyzed
        analyzed_deals = [d for d in updated_state["current_deals"] if d.get("analyzed")]
        assert len(analyzed_deals) == 3
        
        # Metrics should be updated
        assert analyst_agent.analyses_completed_today == 3
        assert analyst_agent.total_analyses_completed == 3


class TestPropertyAnalysisModels:
    """Test property analysis data models"""
    
    def test_property_valuation_model(self):
        """Test PropertyValuation model"""
        valuation = PropertyValuation(
            arv=350000,
            current_value=320000,
            confidence_score=0.85,
            comp_count=5,
            valuation_method="comparable_sales"
        )
        
        assert valuation.arv == 350000
        assert valuation.current_value == 320000
        assert valuation.confidence_score == 0.85
        assert valuation.comp_count == 5
        assert valuation.valuation_method == "comparable_sales"
    
    def test_repair_estimate_model(self):
        """Test RepairEstimate model"""
        repair_estimate = RepairEstimate(
            total_cost=25000,
            confidence_score=0.80,
            line_items={"kitchen": 15000, "bathroom": 10000},
            contingency_percentage=0.15,
            timeline_days=45
        )
        
        assert repair_estimate.total_cost == 25000
        assert repair_estimate.confidence_score == 0.80
        assert repair_estimate.line_items["kitchen"] == 15000
        assert repair_estimate.contingency_percentage == 0.15
        assert repair_estimate.timeline_days == 45
    
    def test_financial_metrics_model(self):
        """Test FinancialMetrics model"""
        metrics = FinancialMetrics(
            purchase_price=275000,
            repair_cost=25000,
            total_investment=300000,
            after_repair_value=350000,
            monthly_rent=2500,
            monthly_cash_flow=500,
            cap_rate=0.08,
            cash_on_cash_return=0.12
        )
        
        assert metrics.purchase_price == 275000
        assert metrics.repair_cost == 25000
        assert metrics.total_investment == 300000
        assert metrics.after_repair_value == 350000
        assert metrics.monthly_rent == 2500
        assert metrics.monthly_cash_flow == 500
        assert metrics.cap_rate == 0.08
        assert metrics.cash_on_cash_return == 0.12
    
    def test_investment_strategy_model(self):
        """Test InvestmentStrategy model"""
        strategy = InvestmentStrategy(
            strategy_type="buy_and_hold_rental",
            potential_profit=6000,
            roi=0.15,
            risk_level=4.0,
            timeline_days=30,
            funding_required=75000,
            pros=["Steady cash flow", "Appreciation"],
            cons=["Management required", "Vacancy risk"],
            confidence_score=0.85
        )
        
        assert strategy.strategy_type == "buy_and_hold_rental"
        assert strategy.potential_profit == 6000
        assert strategy.roi == 0.15
        assert strategy.risk_level == 4.0
        assert strategy.timeline_days == 30
        assert strategy.funding_required == 75000
        assert len(strategy.pros) == 2
        assert len(strategy.cons) == 2
        assert strategy.confidence_score == 0.85
    
    def test_property_analysis_model(self):
        """Test PropertyAnalysis model"""
        valuation = PropertyValuation(
            arv=350000,
            current_value=320000,
            confidence_score=0.85,
            comp_count=5,
            valuation_method="comparable_sales"
        )
        
        repair_estimate = RepairEstimate(
            total_cost=25000,
            confidence_score=0.80,
            line_items={"kitchen": 15000}
        )
        
        financial_metrics = FinancialMetrics(
            purchase_price=275000,
            repair_cost=25000,
            total_investment=300000,
            after_repair_value=350000
        )
        
        analysis = PropertyAnalysis(
            property_id="prop-1",
            valuation=valuation,
            repair_estimate=repair_estimate,
            financial_metrics=financial_metrics,
            investment_recommendation="proceed",
            recommendation_reason="Strong financial metrics",
            confidence_level=0.85
        )
        
        assert analysis.property_id == "prop-1"
        assert analysis.valuation == valuation
        assert analysis.repair_estimate == repair_estimate
        assert analysis.financial_metrics == financial_metrics
        assert analysis.investment_recommendation == "proceed"
        assert analysis.confidence_level == 0.85
        assert analysis.overall_risk_score == 5.0  # Default value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])