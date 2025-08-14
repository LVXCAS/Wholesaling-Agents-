"""
Tests for Analyst Agent Workflows
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.agents.analyst_workflows import AnalystWorkflows, WorkflowResult
from app.agents.analyst_agent import AnalystAgent
from app.agents.analyst_models import PropertyValuation, RepairEstimate, FinancialMetrics
from app.core.agent_state import AgentState, StateManager, AgentType, DealStatus


@pytest.fixture
def mock_analyst_agent():
    """Create a mock analyst agent"""
    agent = Mock(spec=AnalystAgent)
    agent.name = "TestAnalystAgent"
    agent.agent_type = AgentType.ANALYST
    return agent


@pytest.fixture
def analyst_workflows(mock_analyst_agent):
    """Create analyst workflows instance"""
    return AnalystWorkflows(mock_analyst_agent)


@pytest.fixture
def sample_deal():
    """Sample deal data for testing"""
    return {
        "id": "test-deal-123",
        "property_address": "123 Test St",
        "city": "Test City",
        "state": "TS",
        "zip_code": "12345",
        "property_type": "single_family",
        "bedrooms": 3,
        "bathrooms": 2,
        "square_feet": 1500,
        "year_built": 1990,
        "listing_price": 250000,
        "property_condition": "fair"
    }


@pytest.fixture
def sample_state():
    """Sample agent state for testing"""
    state = StateManager.create_initial_state()
    state["market_conditions"] = {
        "market_temperature": "warm",
        "price_change_yoy": 0.05,
        "rental_demand": "moderate"
    }
    state["investment_criteria"] = {
        "min_cap_rate": 0.08,
        "min_cash_flow": 200,
        "max_risk_score": 7.0,
        "min_roi": 0.15
    }
    return state


class TestAnalystWorkflows:
    """Test analyst workflows functionality"""
    
    @pytest.mark.asyncio
    async def test_property_valuation_workflow_success(self, analyst_workflows, sample_deal, sample_state):
        """Test successful property valuation workflow"""
        # Mock the comparable property finder tool
        mock_tool = AsyncMock()
        mock_tool.execute.return_value = {
            "comparable_properties": [
                {
                    "id": "comp1",
                    "sale_price": 240000,
                    "similarity_score": 0.9,
                    "distance_miles": 0.5
                },
                {
                    "id": "comp2", 
                    "sale_price": 260000,
                    "similarity_score": 0.85,
                    "distance_miles": 1.0
                }
            ],
            "valuation_estimate": {
                "estimated_value": 250000,
                "confidence_score": 0.85,
                "comp_count": 2
            }
        }
        
        with patch('app.core.agent_tools.tool_registry.get_tool', return_value=mock_tool):
            result = await analyst_workflows.execute_property_valuation_workflow(sample_deal, sample_state)
        
        assert result.success is True
        assert result.workflow_name == "property_valuation"
        assert "valuation" in result.data
        assert result.confidence_score > 0
        assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_property_valuation_workflow_failure(self, analyst_workflows, sample_deal, sample_state):
        """Test property valuation workflow failure"""
        # Mock tool that returns no comparables
        mock_tool = AsyncMock()
        mock_tool.execute.return_value = {
            "comparable_properties": [],
            "valuation_estimate": None
        }
        
        with patch('app.core.agent_tools.tool_registry.get_tool', return_value=mock_tool):
            result = await analyst_workflows.execute_property_valuation_workflow(sample_deal, sample_state)
        
        assert result.success is False
        assert result.error is not None
        assert "No comparable properties found" in result.error
    
    @pytest.mark.asyncio
    async def test_financial_analysis_workflow_success(self, analyst_workflows, sample_deal, sample_state):
        """Test successful financial analysis workflow"""
        # Create sample valuation and repair estimate
        valuation = PropertyValuation(
            arv=275000,
            current_value=250000,
            confidence_score=0.85,
            comp_count=3,
            valuation_method="comparable_sales"
        )
        
        repair_estimate = RepairEstimate(
            total_cost=25000,
            confidence_score=0.8,
            line_items={"kitchen": 15000, "bathroom": 10000},
            contingency_percentage=0.15
        )
        
        # Mock financial calculator tool
        mock_tool = AsyncMock()
        mock_tool.execute.return_value = {
            "financial_metrics": {
                "purchase_price": 250000,
                "repair_cost": 25000,
                "total_investment": 275000,
                "after_repair_value": 275000,
                "monthly_rent": 2500,
                "monthly_expenses": 1800,
                "monthly_cash_flow": 700,
                "annual_cash_flow": 8400,
                "cap_rate": 0.09,
                "cash_on_cash_return": 0.12,
                "roi": 0.15,
                "gross_rent_multiplier": 9.2
            },
            "expense_breakdown": {},
            "assumptions": {}
        }
        
        with patch('app.core.agent_tools.tool_registry.get_tool', return_value=mock_tool):
            result = await analyst_workflows.execute_financial_analysis_workflow(
                sample_deal, valuation, repair_estimate, sample_state
            )
        
        assert result.success is True
        assert result.workflow_name == "financial_analysis"
        assert "financial_metrics" in result.data
        assert result.confidence_score > 0
    
    @pytest.mark.asyncio
    async def test_strategy_comparison_workflow_success(self, analyst_workflows, sample_deal, sample_state):
        """Test successful strategy comparison workflow"""
        # Create sample financial metrics
        financial_metrics = FinancialMetrics(
            purchase_price=250000,
            repair_cost=25000,
            total_investment=275000,
            after_repair_value=275000,
            monthly_rent=2500,
            monthly_cash_flow=700,
            cap_rate=0.09,
            cash_on_cash_return=0.12,
            roi=0.15
        )
        
        # Mock strategy analyzer tool
        mock_tool = AsyncMock()
        mock_tool.execute.return_value = {
            "strategies": [
                {
                    "strategy_type": "buy_and_hold_rental",
                    "potential_profit": 8400,
                    "roi": 0.12,
                    "risk_level": 4.0,
                    "timeline_days": 30,
                    "funding_required": 68750,
                    "pros": ["Steady cash flow"],
                    "cons": ["Property management"],
                    "confidence_score": 0.85
                }
            ],
            "recommended_strategy": "buy_and_hold_rental",
            "market_analysis": {}
        }
        
        with patch('app.core.agent_tools.tool_registry.get_tool', return_value=mock_tool):
            result = await analyst_workflows.execute_strategy_comparison_workflow(
                sample_deal, financial_metrics, sample_state
            )
        
        assert result.success is True
        assert result.workflow_name == "strategy_comparison"
        assert "strategies" in result.data
        assert result.data["recommended_strategy"] == "buy_and_hold_rental"
    
    @pytest.mark.asyncio
    async def test_risk_assessment_workflow_success(self, analyst_workflows, sample_deal, sample_state):
        """Test successful risk assessment workflow"""
        analysis_data = {
            "financial_metrics": {
                "cap_rate": 0.09,
                "cash_flow": 700
            }
        }
        
        # Mock risk assessment tool
        mock_tool = AsyncMock()
        mock_tool.execute.return_value = {
            "risk_assessment": {
                "risk_factors": ["Market volatility", "Property age"],
                "overall_risk_score": 5.5,
                "risk_categories": {
                    "property_risk": 6.0,
                    "market_risk": 5.0,
                    "financial_risk": 4.0
                }
            }
        }
        
        with patch('app.core.agent_tools.tool_registry.get_tool', return_value=mock_tool):
            result = await analyst_workflows.execute_risk_assessment_workflow(
                sample_deal, analysis_data, sample_state
            )
        
        assert result.success is True
        assert result.workflow_name == "risk_assessment"
        assert "risk_factors" in result.data
        assert "overall_risk_score" in result.data
    
    @pytest.mark.asyncio
    async def test_recommendation_generation_workflow_success(self, analyst_workflows, sample_deal, sample_state):
        """Test successful recommendation generation workflow"""
        # Create mock workflow results
        workflow_results = {
            "property_valuation": WorkflowResult(
                workflow_name="property_valuation",
                success=True,
                data={"valuation": {"arv": 275000, "confidence_score": 0.85}},
                confidence_score=0.85
            ),
            "financial_analysis": WorkflowResult(
                workflow_name="financial_analysis", 
                success=True,
                data={"financial_metrics": {"cap_rate": 0.09, "monthly_cash_flow": 700, "roi": 0.15}},
                confidence_score=0.8
            ),
            "risk_assessment": WorkflowResult(
                workflow_name="risk_assessment",
                success=True,
                data={"overall_risk_score": 5.0, "risk_factors": ["Market risk"]},
                confidence_score=0.75
            )
        }
        
        result = await analyst_workflows.execute_recommendation_generation_workflow(
            sample_deal, workflow_results, sample_state
        )
        
        assert result.success is True
        assert result.workflow_name == "recommendation_generation"
        assert "investment_recommendation" in result.data
        assert result.data["investment_recommendation"] in ["proceed", "caution", "reject"]
        assert "recommendation_reason" in result.data
        assert "confidence_level" in result.data
    
    @pytest.mark.asyncio
    async def test_workflow_history_tracking(self, analyst_workflows, sample_deal, sample_state):
        """Test that workflow results are tracked in history"""
        # Mock a simple workflow execution
        mock_tool = AsyncMock()
        mock_tool.execute.return_value = {
            "comparable_properties": [{"id": "comp1", "sale_price": 250000}],
            "valuation_estimate": {"estimated_value": 250000, "confidence_score": 0.8}
        }
        
        with patch('app.core.agent_tools.tool_registry.get_tool', return_value=mock_tool):
            result = await analyst_workflows.execute_property_valuation_workflow(sample_deal, sample_state)
        
        # Check that result was recorded in history
        history = analyst_workflows.get_workflow_history("property_valuation")
        assert "property_valuation" in history
        assert len(history["property_valuation"]) == 1
        assert history["property_valuation"][0].workflow_name == "property_valuation"
    
    def test_workflow_configuration(self, analyst_workflows):
        """Test workflow configuration settings"""
        config = analyst_workflows.workflow_config
        
        assert "property_valuation" in config
        assert "financial_analysis" in config
        assert "strategy_comparison" in config
        assert "risk_assessment" in config
        assert "recommendation_generation" in config
        
        # Check that each workflow has required config
        for workflow_name, workflow_config in config.items():
            assert "timeout_seconds" in workflow_config
            assert "confidence_threshold" in workflow_config
    
    @pytest.mark.asyncio
    async def test_workflow_timeout_handling(self, analyst_workflows, sample_deal, sample_state):
        """Test workflow timeout handling"""
        # Mock a tool that takes too long
        mock_tool = AsyncMock()
        mock_tool.execute.side_effect = asyncio.TimeoutError("Tool execution timed out")
        
        with patch('app.core.agent_tools.tool_registry.get_tool', return_value=mock_tool):
            result = await analyst_workflows.execute_property_valuation_workflow(sample_deal, sample_state)
        
        assert result.success is False
        assert "timed out" in result.error.lower() or "timeout" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_missing_tool_handling(self, analyst_workflows, sample_deal, sample_state):
        """Test handling of missing tools"""
        with patch('app.core.agent_tools.tool_registry.get_tool', return_value=None):
            result = await analyst_workflows.execute_property_valuation_workflow(sample_deal, sample_state)
        
        assert result.success is False
        assert "not available" in result.error
    
    def test_workflow_result_model(self):
        """Test WorkflowResult model validation"""
        # Test valid result
        result = WorkflowResult(
            workflow_name="test_workflow",
            success=True,
            data={"test": "data"},
            confidence_score=0.85
        )
        
        assert result.workflow_name == "test_workflow"
        assert result.success is True
        assert result.data == {"test": "data"}
        assert result.confidence_score == 0.85
        assert isinstance(result.timestamp, datetime)
        
        # Test result with error
        error_result = WorkflowResult(
            workflow_name="test_workflow",
            success=False,
            error="Test error message"
        )
        
        assert error_result.success is False
        assert error_result.error == "Test error message"
        assert error_result.confidence_score == 0.0


if __name__ == "__main__":
    pytest.main([__file__])