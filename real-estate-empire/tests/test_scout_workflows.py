"""
Test Scout Agent Workflows Implementation
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

from app.agents.scout_agent import ScoutAgent, ScoutWorkflowEngine, execute_scout_workflows
from app.core.agent_state import AgentState, StateManager, AgentType, DealStatus


class TestScoutWorkflows:
    """Test Scout Agent workflow implementations"""
    
    @pytest.fixture
    def scout_agent(self):
        """Create a scout agent for testing"""
        return ScoutAgent(name="TestScoutAgent")
    
    @pytest.fixture
    def workflow_engine(self, scout_agent):
        """Create a workflow engine for testing"""
        return ScoutWorkflowEngine(scout_agent)
    
    @pytest.fixture
    def sample_state(self):
        """Create sample agent state"""
        return StateManager.create_initial_state()
    
    @pytest.fixture
    def sample_deals(self):
        """Create sample deals for testing"""
        return [
            {
                "id": "deal-1",
                "address": "123 Test St",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78701",
                "property_type": "single_family",
                "bedrooms": 3,
                "bathrooms": 2,
                "square_feet": 1500,
                "listing_price": 275000,
                "estimated_value": 320000,
                "days_on_market": 45,
                "motivation_indicators": ["job_relocation"],
                "source": "mls"
            },
            {
                "id": "deal-2", 
                "address": "456 Investment Ave",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78702",
                "property_type": "multi_family",
                "bedrooms": 6,
                "bathrooms": 4,
                "square_feet": 2400,
                "listing_price": 450000,
                "estimated_value": 520000,
                "days_on_market": 75,
                "motivation_indicators": ["estate_sale", "distressed"],
                "source": "foreclosure"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_continuous_scanning_workflow(self, workflow_engine, sample_state):
        """Test continuous scanning workflow execution"""
        # Mock the scout agent's _should_scan method to return True
        workflow_engine.scout_agent._should_scan = Mock(return_value=True)
        
        result = await workflow_engine.execute_continuous_scanning_workflow(sample_state)
        
        assert result["success"] is True
        assert "workflow_id" in result
        assert "deals_discovered" in result
        assert "execution_time" in result
        assert isinstance(result["deals"], list)
    
    @pytest.mark.asyncio
    async def test_deal_evaluation_workflow(self, workflow_engine, sample_deals, sample_state):
        """Test deal evaluation and scoring workflow"""
        result = await workflow_engine.execute_deal_evaluation_workflow(sample_deals, sample_state)
        
        assert result["success"] is True
        assert "workflow_id" in result
        assert "evaluated_deals" in result
        assert "average_score" in result
        assert "high_quality_deals" in result
        
        # Check that deals have been scored
        evaluated_deals = result["evaluated_deals"]
        assert len(evaluated_deals) == len(sample_deals)
        
        for deal in evaluated_deals:
            assert "lead_score" in deal
            assert "overall_score" in deal["lead_score"]
            assert "profit_potential" in deal["lead_score"]
            assert "deal_feasibility" in deal["lead_score"]
            assert "seller_motivation" in deal["lead_score"]
            assert "market_conditions" in deal["lead_score"]
            assert "confidence_level" in deal["lead_score"]
    
    @pytest.mark.asyncio
    async def test_lead_qualification_workflow(self, workflow_engine, sample_deals, sample_state):
        """Test lead qualification workflow"""
        # Add lead scores to sample deals
        for deal in sample_deals:
            deal["lead_score"] = {
                "overall_score": 7.5,
                "profit_potential": 8.0,
                "deal_feasibility": 7.0,
                "seller_motivation": 8.0,
                "market_conditions": 7.0,
                "confidence_level": 0.85
            }
        
        result = await workflow_engine.execute_lead_qualification_workflow(sample_deals, sample_state)
        
        assert result["success"] is True
        assert "workflow_id" in result
        assert "qualified_leads" in result
        assert "qualification_stats" in result
        assert "reports" in result
        
        # Check qualification data
        qualified_leads = result["qualified_leads"]
        for lead in qualified_leads:
            assert "qualification" in lead
            assert "category" in lead["qualification"]
            assert "priority" in lead["qualification"]
            assert "recommended_action" in lead["qualification"]
            
            assert "readiness_assessment" in lead
            assert "urgency_assessment" in lead
    
    @pytest.mark.asyncio
    async def test_alert_notification_workflow(self, workflow_engine, sample_deals, sample_state):
        """Test alert and notification workflow"""
        # Add high scores to trigger alerts
        for deal in sample_deals:
            deal["lead_score"] = {"overall_score": 8.5}
            deal["urgency_assessment"] = {"urgency_level": "critical"}
            deal["qualification"] = {"category": "hot_lead"}
        
        result = await workflow_engine.execute_alert_notification_workflow(sample_deals, sample_state)
        
        assert result["success"] is True
        assert "workflow_id" in result
        assert "alerts_generated" in result
        assert "notifications_sent" in result
        assert "delivery_status" in result
        
        # Check that alerts were generated for high-priority deals
        assert result["alerts_generated"] > 0
        assert result["notifications_sent"] > 0
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_workflow(self, workflow_engine, sample_state):
        """Test performance monitoring and optimization workflow"""
        result = await workflow_engine.execute_performance_monitoring_workflow(sample_state)
        
        assert result["success"] is True
        assert "workflow_id" in result
        assert "performance_metrics" in result
        assert "efficiency_analysis" in result
        assert "optimizations_implemented" in result
        assert "performance_report" in result
        
        # Check performance metrics structure
        metrics = result["performance_metrics"]
        assert "workflow_metrics" in metrics
        assert "deal_discovery_rate" in metrics
        assert "average_deal_score" in metrics
        
        # Check efficiency analysis
        efficiency = result["efficiency_analysis"]
        assert "overall_score" in efficiency
        assert "success_rate" in efficiency
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, workflow_engine, sample_state):
        """Test workflow error handling"""
        # Mock a method to raise an exception
        workflow_engine._prepare_scanning_parameters = Mock(side_effect=Exception("Test error"))
        
        result = await workflow_engine.execute_continuous_scanning_workflow(sample_state)
        
        assert result["success"] is False
        assert "error" in result
        assert "workflow_id" in result
    
    def test_workflow_performance_metrics_update(self, workflow_engine):
        """Test workflow performance metrics updates"""
        initial_workflows = workflow_engine.performance_metrics["workflows_executed"]
        
        # Simulate completed workflow
        workflow_data = {
            "status": "completed",
            "execution_time": 120.0,
            "deals_discovered": 5
        }
        
        workflow_engine._update_workflow_performance_metrics(workflow_data)
        
        assert workflow_engine.performance_metrics["workflows_executed"] == initial_workflows + 1
        assert workflow_engine.performance_metrics["deals_discovered"] == 5
        assert workflow_engine.performance_metrics["average_execution_time"] > 0
    
    @pytest.mark.asyncio
    async def test_deal_scoring_accuracy(self, workflow_engine, sample_state):
        """Test deal scoring accuracy"""
        # Create deals with known characteristics
        test_deals = [
            {
                "address": "High Score Deal",
                "listing_price": 200000,
                "estimated_value": 300000,
                "estimated_repair_cost": 20000,
                "days_on_market": 120,
                "motivation_indicators": ["foreclosure", "divorce"]
            },
            {
                "address": "Low Score Deal", 
                "listing_price": 400000,
                "estimated_value": 410000,
                "estimated_repair_cost": 50000,
                "days_on_market": 5,
                "motivation_indicators": []
            }
        ]
        
        scored_deals = await workflow_engine._score_and_prioritize_deals(test_deals, sample_state)
        
        # High profit, high motivation deal should score higher
        high_score_deal = next(d for d in scored_deals if "High Score" in d["address"])
        low_score_deal = next(d for d in scored_deals if "Low Score" in d["address"])
        
        assert high_score_deal["lead_score"]["overall_score"] > low_score_deal["lead_score"]["overall_score"]
        assert high_score_deal["lead_score"]["profit_potential"] > low_score_deal["lead_score"]["profit_potential"]
        assert high_score_deal["lead_score"]["seller_motivation"] > low_score_deal["lead_score"]["seller_motivation"]
    
    @pytest.mark.asyncio
    async def test_qualification_categorization(self, workflow_engine, sample_state):
        """Test lead qualification categorization"""
        test_deals = [
            {
                "address": "Hot Lead",
                "lead_score": {"overall_score": 8.5},
                "contact_verified": True,
                "owner_research": {"owner_name": "John Doe"},
                "motivation_analysis": {"urgency_level": "high"}
            },
            {
                "address": "Cold Lead",
                "lead_score": {"overall_score": 6.2},
                "contact_verified": False,
                "owner_research": None,
                "motivation_analysis": {"urgency_level": "low"}
            }
        ]
        
        # Process through qualification workflow steps
        validated = await workflow_engine._validate_deal_data(test_deals)
        enriched = await workflow_engine._enrich_deal_data(validated, sample_state)
        readiness_assessed = await workflow_engine._assess_deal_readiness(enriched, sample_state)
        urgency_determined = await workflow_engine._determine_urgency_levels(readiness_assessed, sample_state)
        categorized = await workflow_engine._categorize_qualification_levels(urgency_determined, sample_state)
        
        hot_lead = next(d for d in categorized if "Hot Lead" in d["address"])
        cold_lead = next(d for d in categorized if "Cold Lead" in d["address"])
        
        assert hot_lead["qualification"]["category"] in ["hot_lead", "warm_lead"]
        assert cold_lead["qualification"]["category"] in ["cold_lead", "unqualified"]
        assert hot_lead["qualification"]["priority"] < cold_lead["qualification"]["priority"]
    
    @pytest.mark.asyncio
    async def test_alert_prioritization(self, workflow_engine, sample_state):
        """Test alert prioritization logic"""
        test_deals = [
            {
                "id": "critical-deal",
                "address": "Critical Deal",
                "lead_score": {"overall_score": 9.0},
                "urgency_assessment": {"urgency_level": "critical"},
                "qualification": {"category": "hot_lead"}
            },
            {
                "id": "medium-deal", 
                "address": "Medium Deal",
                "lead_score": {"overall_score": 7.0},
                "urgency_assessment": {"urgency_level": "medium"},
                "qualification": {"category": "warm_lead"}
            }
        ]
        
        alert_worthy = await workflow_engine._identify_alert_worthy_deals(test_deals, sample_state)
        categorized_alerts = await workflow_engine._categorize_alert_types(alert_worthy, sample_state)
        alert_messages = await workflow_engine._generate_alert_messages(categorized_alerts, sample_state)
        
        # Critical deal should generate more alerts
        critical_alerts = [msg for msg in alert_messages if msg["deal_id"] == "critical-deal"]
        medium_alerts = [msg for msg in alert_messages if msg["deal_id"] == "medium-deal"]
        
        assert len(critical_alerts) >= len(medium_alerts)
        
        # Check priority levels
        for alert in critical_alerts:
            assert alert["priority"] in ["critical", "high"]
    
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self, scout_agent, sample_state):
        """Test full workflow integration"""
        # Mock the agent executor to avoid actual LLM calls
        scout_agent.agent_executor = Mock()
        scout_agent.agent_executor.ainvoke = Mock(return_value={"output": "Mock LLM response"})
        
        result_state = await execute_scout_workflows(scout_agent, sample_state)
        
        # Check that state was updated with workflow results
        assert len(result_state["agent_messages"]) > 0
        
        # Check for scout agent messages
        scout_messages = [msg for msg in result_state["agent_messages"] 
                         if msg.get("agent") == AgentType.SCOUT.value]
        assert len(scout_messages) > 0
    
    def test_workflow_history_tracking(self, workflow_engine):
        """Test workflow history tracking"""
        initial_history_count = len(workflow_engine.workflow_history)
        
        # Simulate workflow completion
        workflow_data = {
            "id": "test-workflow",
            "type": "continuous_scanning",
            "status": "completed",
            "execution_time": 60.0
        }
        
        workflow_engine.workflow_history.append(workflow_data)
        
        assert len(workflow_engine.workflow_history) == initial_history_count + 1
        assert workflow_engine.workflow_history[-1]["id"] == "test-workflow"
    
    @pytest.mark.asyncio
    async def test_workflow_concurrency(self, workflow_engine, sample_state, sample_deals):
        """Test workflow concurrency handling"""
        # Start multiple workflows concurrently
        tasks = [
            workflow_engine.execute_deal_evaluation_workflow(sample_deals, sample_state),
            workflow_engine.execute_lead_qualification_workflow(sample_deals, sample_state),
            workflow_engine.execute_performance_monitoring_workflow(sample_state)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All workflows should complete successfully
        for result in results:
            assert not isinstance(result, Exception)
            assert result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])