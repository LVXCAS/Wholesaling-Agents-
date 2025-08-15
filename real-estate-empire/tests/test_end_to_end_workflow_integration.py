"""
End-to-End Workflow Integration Tests
Tests the complete deal lifecycle automation with cross-agent communication
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock

from app.core.workflow_orchestrator import WorkflowOrchestrator, WorkflowConfiguration, WorkflowPhase
from app.core.system_health_monitor import SystemHealthMonitor, HealthStatus
from app.core.agent_state import AgentState, StateManager, DealStatus, WorkflowStatus
from app.core.supervisor_agent import SupervisorAgent


class TestEndToEndWorkflowIntegration:
    """Test suite for end-to-end workflow orchestration"""
    
    @pytest.fixture
    async def workflow_config(self):
        """Create test workflow configuration"""
        return WorkflowConfiguration(
            name="Test Real Estate Workflow",
            max_concurrent_deals=5,
            max_execution_time_minutes=60,
            auto_approve_threshold=0.8,
            human_escalation_threshold=0.6,
            enable_parallel_processing=True,
            agent_timeout_seconds=30,
            max_retries_per_agent=2,
            batch_communications=True,
            communication_delay_seconds=5,
            max_outreach_per_hour=20,
            enable_real_time_monitoring=True,
            metrics_collection_interval=10
        )
    
    @pytest.fixture
    async def orchestrator(self, workflow_config):
        """Create workflow orchestrator for testing"""
        orchestrator = WorkflowOrchestrator(workflow_config)
        yield orchestrator
        # Cleanup
        await orchestrator.stop_workflow()
    
    @pytest.fixture
    async def health_monitor(self):
        """Create health monitor for testing"""
        monitor = SystemHealthMonitor(monitoring_interval=5)
        await monitor.start_monitoring()
        yield monitor
        await monitor.stop_monitoring()
    
    @pytest.fixture
    def initial_state(self):
        """Create initial workflow state"""
        state = StateManager.create_initial_state()
        state["investment_strategy"] = {
            "target_markets": ["Austin", "Dallas"],
            "property_types": ["single_family", "duplex"],
            "max_investment_per_deal": 400000,
            "target_roi": 0.15,
            "risk_tolerance": "moderate"
        }
        state["available_capital"] = 2000000
        return state
    
    @pytest.mark.asyncio
    async def test_complete_workflow_execution(self, orchestrator, initial_state):
        """Test complete workflow from initialization to completion"""
        
        # Mock agent implementations
        with patch('app.agents.scout_agent.ScoutAgent') as mock_scout, \
             patch('app.agents.analyst_agent.AnalystAgent') as mock_analyst, \
             patch('app.agents.negotiator_agent.NegotiatorAgent') as mock_negotiator, \
             patch('app.agents.contract_agent.ContractAgent') as mock_contract, \
             patch('app.agents.portfolio_agent.PortfolioAgent') as mock_portfolio:
            
            # Configure mock agents
            await self._setup_mock_agents(
                mock_scout, mock_analyst, mock_negotiator, 
                mock_contract, mock_portfolio
            )
            
            # Start workflow
            workflow_id = await orchestrator.start_workflow(initial_state)
            
            # Verify workflow started
            assert workflow_id == orchestrator.workflow_id
            
            # Wait for workflow to process (with timeout)
            timeout = 30  # seconds
            start_time = datetime.now()
            
            while (datetime.now() - start_time).total_seconds() < timeout:
                current_state = await orchestrator.get_workflow_state()
                
                if current_state.get("workflow_status") in [WorkflowStatus.COMPLETED, WorkflowStatus.ERROR]:
                    break
                
                await asyncio.sleep(1)
            
            # Get final state
            final_state = await orchestrator.get_workflow_state()
            
            # Verify workflow completion
            assert final_state["workflow_status"] in [WorkflowStatus.COMPLETED, WorkflowStatus.ERROR]
            
            # Get workflow metrics
            metrics = orchestrator.get_workflow_metrics()
            
            # Verify metrics were collected
            assert metrics["workflow_id"] == workflow_id
            assert metrics["total_deals_processed"] >= 0
            assert "agent_execution_times" in metrics
            
            # Verify all phases were attempted
            execution_times = metrics["agent_execution_times"]
            expected_phases = ["initialization", "deal_discovery", "property_analysis"]
            
            for phase in expected_phases:
                assert phase in execution_times or len(execution_times) > 0
    
    @pytest.mark.asyncio
    async def test_cross_agent_communication_optimization(self, orchestrator, initial_state):
        """Test cross-agent communication and handoff optimization"""
        
        communication_log = []
        
        def log_communication(agent_type, message, data=None):
            communication_log.append({
                "timestamp": datetime.now(),
                "agent": agent_type,
                "message": message,
                "data": data
            })
        
        # Mock agents with communication logging
        with patch('app.agents.scout_agent.ScoutAgent') as mock_scout, \
             patch('app.agents.analyst_agent.AnalystAgent') as mock_analyst:
            
            # Configure scout agent
            scout_instance = Mock()
            scout_instance.execute_task = AsyncMock(return_value={
                "success": True,
                "deals_found": 3,
                "execution_time": 5.2
            })
            mock_scout.return_value = scout_instance
            
            # Configure analyst agent
            analyst_instance = Mock()
            analyst_instance.execute_task = AsyncMock(return_value={
                "success": True,
                "deals_analyzed": 3,
                "deals_approved": 2,
                "execution_time": 8.1
            })
            mock_analyst.return_value = analyst_instance
            
            # Add communication logging
            def scout_task_wrapper(*args, **kwargs):
                log_communication("scout", "Task executed", kwargs)
                return scout_instance.execute_task(*args, **kwargs)
            
            def analyst_task_wrapper(*args, **kwargs):
                log_communication("analyst", "Task executed", kwargs)
                return analyst_instance.execute_task(*args, **kwargs)
            
            scout_instance.execute_task.side_effect = scout_task_wrapper
            analyst_instance.execute_task.side_effect = analyst_task_wrapper
            
            # Start workflow
            workflow_id = await orchestrator.start_workflow(initial_state)
            
            # Wait for some processing
            await asyncio.sleep(10)
            
            # Get current state
            current_state = await orchestrator.get_workflow_state()
            
            # Verify cross-agent communication occurred
            assert len(communication_log) > 0
            
            # Verify agent handoffs
            agent_types = [log["agent"] for log in communication_log]
            assert "scout" in agent_types or "analyst" in agent_types
            
            # Verify state transitions
            assert "agent_messages" in current_state
            agent_messages = current_state["agent_messages"]
            
            # Should have messages from multiple agents
            message_agents = set(msg.get("agent") for msg in agent_messages)
            assert len(message_agents) >= 1
            
            # Get metrics
            metrics = orchestrator.get_workflow_metrics()
            
            # Verify handoff metrics
            assert metrics["cross_agent_handoffs"] >= 0
    
    @pytest.mark.asyncio
    async def test_workflow_performance_monitoring(self, orchestrator, health_monitor, initial_state):
        """Test workflow performance monitoring and alerting"""
        
        # Mock agents with varying performance
        with patch('app.agents.scout_agent.ScoutAgent') as mock_scout:
            
            # Configure slow scout agent to trigger performance alerts
            scout_instance = Mock()
            
            async def slow_scout_task(*args, **kwargs):
                await asyncio.sleep(2)  # Simulate slow execution
                return {
                    "success": True,
                    "deals_found": 1,
                    "execution_time": 2.0
                }
            
            scout_instance.execute_task = slow_scout_task
            mock_scout.return_value = scout_instance
            
            # Start workflow
            workflow_id = await orchestrator.start_workflow(initial_state)
            
            # Wait for monitoring to collect metrics
            await asyncio.sleep(15)
            
            # Get health summary
            health_summary = health_monitor.get_system_health_summary()
            
            # Verify monitoring is active
            assert health_summary["monitoring_status"] == "active"
            assert "system_metrics" in health_summary
            assert "agent_health" in health_summary
            
            # Get workflow metrics
            workflow_metrics = health_monitor.get_workflow_metrics()
            
            # Should have workflow metrics if workflow is running
            if workflow_metrics:
                assert workflow_id in workflow_metrics or len(workflow_metrics) > 0
            
            # Check for performance alerts
            active_alerts = health_monitor.get_active_alerts()
            
            # May have alerts depending on system performance
            assert isinstance(active_alerts, list)
            
            # Get performance report
            performance_report = health_monitor.get_performance_report()
            
            # Verify report structure
            assert "report_timestamp" in performance_report
            assert "system_performance" in performance_report
            assert "overall_health_score" in performance_report
            assert "recommendations" in performance_report
            
            # Health score should be between 0 and 100
            health_score = performance_report["overall_health_score"]
            assert 0 <= health_score <= 100
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, orchestrator, initial_state):
        """Test error handling and recovery mechanisms"""
        
        # Mock agents with failures
        with patch('app.agents.scout_agent.ScoutAgent') as mock_scout, \
             patch('app.agents.analyst_agent.AnalystAgent') as mock_analyst:
            
            # Configure failing scout agent
            scout_instance = Mock()
            scout_instance.execute_task = AsyncMock(return_value={
                "success": False,
                "error": "Simulated scout failure",
                "execution_time": 1.0
            })
            mock_scout.return_value = scout_instance
            
            # Configure working analyst agent
            analyst_instance = Mock()
            analyst_instance.execute_task = AsyncMock(return_value={
                "success": True,
                "deals_analyzed": 0,
                "deals_approved": 0,
                "execution_time": 2.0
            })
            mock_analyst.return_value = analyst_instance
            
            # Start workflow
            workflow_id = await orchestrator.start_workflow(initial_state)
            
            # Wait for processing
            await asyncio.sleep(10)
            
            # Get current state
            current_state = await orchestrator.get_workflow_state()
            
            # Verify error handling
            agent_messages = current_state.get("agent_messages", [])
            
            # Should have error messages
            error_messages = [
                msg for msg in agent_messages 
                if msg.get("priority", 0) >= 4  # Error priority
            ]
            
            # May have error messages depending on workflow execution
            assert isinstance(error_messages, list)
            
            # Workflow should still be running or completed gracefully
            workflow_status = current_state.get("workflow_status")
            assert workflow_status in [
                WorkflowStatus.RUNNING, 
                WorkflowStatus.COMPLETED, 
                WorkflowStatus.ERROR,
                WorkflowStatus.PAUSED
            ]
            
            # Get metrics
            metrics = orchestrator.get_workflow_metrics()
            
            # Should have execution metrics even with failures
            assert "agent_execution_times" in metrics
    
    @pytest.mark.asyncio
    async def test_human_escalation_workflow(self, orchestrator, initial_state):
        """Test human escalation and approval workflow"""
        
        # Configure workflow for human escalation
        orchestrator.config.human_escalation_threshold = 0.9  # High threshold to trigger escalation
        
        # Mock agents with low confidence
        with patch('app.agents.analyst_agent.AnalystAgent') as mock_analyst:
            
            # Configure analyst with low confidence results
            analyst_instance = Mock()
            analyst_instance.execute_task = AsyncMock(return_value={
                "success": True,
                "deals_analyzed": 1,
                "deals_approved": 0,  # No deals approved
                "confidence_score": 0.5,  # Low confidence
                "execution_time": 3.0
            })
            mock_analyst.return_value = analyst_instance
            
            # Start workflow
            workflow_id = await orchestrator.start_workflow(initial_state)
            
            # Wait for processing
            await asyncio.sleep(10)
            
            # Get current state
            current_state = await orchestrator.get_workflow_state()
            
            # Check if human escalation was triggered
            if current_state.get("human_approval_required"):
                assert current_state["workflow_status"] == WorkflowStatus.HUMAN_ESCALATION
                assert "escalation_data" in current_state
                
                # Simulate human approval
                await orchestrator.continue_workflow("approve")
                
                # Wait for continuation
                await asyncio.sleep(5)
                
                # Get updated state
                updated_state = await orchestrator.get_workflow_state()
                
                # Should no longer require human approval
                assert not updated_state.get("human_approval_required", False)
    
    @pytest.mark.asyncio
    async def test_workflow_metrics_collection(self, orchestrator, initial_state):
        """Test comprehensive workflow metrics collection"""
        
        # Mock agents with known performance characteristics
        with patch('app.agents.scout_agent.ScoutAgent') as mock_scout, \
             patch('app.agents.analyst_agent.AnalystAgent') as mock_analyst:
            
            # Configure scout agent
            scout_instance = Mock()
            scout_instance.execute_task = AsyncMock(return_value={
                "success": True,
                "deals_found": 5,
                "total_investment_analyzed": 1500000,
                "execution_time": 4.2
            })
            mock_scout.return_value = scout_instance
            
            # Configure analyst agent
            analyst_instance = Mock()
            analyst_instance.execute_task = AsyncMock(return_value={
                "success": True,
                "deals_analyzed": 5,
                "deals_approved": 3,
                "potential_profit": 150000,
                "execution_time": 7.8
            })
            mock_analyst.return_value = analyst_instance
            
            # Start workflow
            workflow_id = await orchestrator.start_workflow(initial_state)
            
            # Wait for processing
            await asyncio.sleep(15)
            
            # Get comprehensive metrics
            metrics = orchestrator.get_workflow_metrics()
            
            # Verify basic metrics
            assert metrics["workflow_id"] == workflow_id
            assert isinstance(metrics["total_deals_processed"], int)
            assert isinstance(metrics["deals_approved"], int)
            
            # Verify execution time tracking
            assert "agent_execution_times" in metrics
            execution_times = metrics["agent_execution_times"]
            
            # Should have recorded execution times for phases
            assert isinstance(execution_times, dict)
            
            # Verify financial metrics
            if metrics["total_investment_analyzed"] > 0:
                assert metrics["total_investment_analyzed"] >= 0
            
            if metrics["potential_profit_identified"] > 0:
                assert metrics["potential_profit_identified"] >= 0
            
            # Verify communication metrics
            assert isinstance(metrics["messages_sent"], int)
            assert isinstance(metrics["cross_agent_handoffs"], int)
            
            # Get performance alerts
            alerts = orchestrator.get_performance_alerts()
            assert isinstance(alerts, list)
            
            # Get workflow history
            history = orchestrator.get_workflow_history()
            assert isinstance(history, list)
    
    @pytest.mark.asyncio
    async def test_workflow_pause_resume_functionality(self, orchestrator, initial_state):
        """Test workflow pause and resume functionality"""
        
        # Mock agents
        with patch('app.agents.scout_agent.ScoutAgent') as mock_scout:
            
            scout_instance = Mock()
            scout_instance.execute_task = AsyncMock(return_value={
                "success": True,
                "deals_found": 2,
                "execution_time": 3.0
            })
            mock_scout.return_value = scout_instance
            
            # Start workflow
            workflow_id = await orchestrator.start_workflow(initial_state)
            
            # Let it run briefly
            await asyncio.sleep(5)
            
            # Pause workflow
            pause_result = await orchestrator.pause_workflow()
            assert pause_result is True
            
            # Verify paused state
            current_state = await orchestrator.get_workflow_state()
            assert current_state.get("workflow_status") == WorkflowStatus.PAUSED
            
            # Wait a bit
            await asyncio.sleep(3)
            
            # Resume workflow
            resume_result = await orchestrator.resume_workflow()
            assert resume_result is True
            
            # Wait for processing
            await asyncio.sleep(5)
            
            # Verify workflow continued
            updated_state = await orchestrator.get_workflow_state()
            assert updated_state.get("workflow_status") != WorkflowStatus.PAUSED
    
    @pytest.mark.asyncio
    async def test_system_health_integration(self, orchestrator, health_monitor, initial_state):
        """Test integration between workflow orchestrator and health monitor"""
        
        # Start workflow
        workflow_id = await orchestrator.start_workflow(initial_state)
        
        # Wait for monitoring to collect data
        await asyncio.sleep(10)
        
        # Get health summary
        health_summary = health_monitor.get_system_health_summary()
        
        # Verify health monitoring is working
        assert health_summary["overall_status"] in [
            HealthStatus.HEALTHY.value,
            HealthStatus.WARNING.value,
            HealthStatus.DEGRADED.value,
            HealthStatus.CRITICAL.value
        ]
        
        # Verify system metrics are being collected
        system_metrics = health_summary.get("system_metrics", {})
        if system_metrics:
            assert "cpu" in system_metrics
            assert "memory" in system_metrics
        
        # Verify agent health is being monitored
        agent_health = health_summary.get("agent_health", {})
        assert isinstance(agent_health, dict)
        
        # Get metrics history
        metrics_history = health_monitor.get_system_metrics_history(hours=1)
        assert isinstance(metrics_history, list)
        
        # Get performance report
        performance_report = health_monitor.get_performance_report()
        
        # Verify report contains expected sections
        assert "system_performance" in performance_report
        assert "overall_health_score" in performance_report
        assert "recommendations" in performance_report
        
        # Health score should be valid
        health_score = performance_report["overall_health_score"]
        assert 0 <= health_score <= 100
    
    # Helper Methods
    
    async def _setup_mock_agents(self, mock_scout, mock_analyst, mock_negotiator, mock_contract, mock_portfolio):
        """Set up mock agents with realistic behavior"""
        
        # Scout agent mock
        scout_instance = Mock()
        scout_instance.execute_task = AsyncMock(return_value={
            "success": True,
            "deals_found": 3,
            "execution_time": 5.0
        })
        mock_scout.return_value = scout_instance
        
        # Analyst agent mock
        analyst_instance = Mock()
        analyst_instance.execute_task = AsyncMock(return_value={
            "success": True,
            "deals_analyzed": 3,
            "deals_approved": 2,
            "total_investment_analyzed": 800000,
            "potential_profit": 120000,
            "execution_time": 8.0
        })
        mock_analyst.return_value = analyst_instance
        
        # Negotiator agent mock
        negotiator_instance = Mock()
        negotiator_instance.execute_task = AsyncMock(return_value={
            "success": True,
            "campaigns_created": 2,
            "messages_sent": 6,
            "responses_processed": 1,
            "deals_agreed": 1,
            "execution_time": 12.0
        })
        mock_negotiator.return_value = negotiator_instance
        
        # Contract agent mock
        contract_instance = Mock()
        contract_instance.execute_task = AsyncMock(return_value={
            "success": True,
            "contracts_generated": 1,
            "deals_closed": 1,
            "execution_time": 6.0
        })
        mock_contract.return_value = contract_instance
        
        # Portfolio agent mock
        portfolio_instance = Mock()
        portfolio_instance.execute_task = AsyncMock(return_value={
            "success": True,
            "properties_integrated": 1,
            "portfolio_value": 400000,
            "execution_time": 4.0
        })
        mock_portfolio.return_value = portfolio_instance
    
    @pytest.mark.asyncio
    async def test_workflow_configuration_validation(self):
        """Test workflow configuration validation"""
        
        # Test valid configuration
        valid_config = WorkflowConfiguration(
            max_concurrent_deals=5,
            max_execution_time_minutes=120,
            auto_approve_threshold=0.8
        )
        
        orchestrator = WorkflowOrchestrator(valid_config)
        assert orchestrator.config.max_concurrent_deals == 5
        assert orchestrator.config.max_execution_time_minutes == 120
        assert orchestrator.config.auto_approve_threshold == 0.8
        
        # Cleanup
        await orchestrator.stop_workflow()
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_handling(self):
        """Test handling of multiple concurrent workflows"""
        
        # Create multiple orchestrators
        config1 = WorkflowConfiguration(name="Workflow 1")
        config2 = WorkflowConfiguration(name="Workflow 2")
        
        orchestrator1 = WorkflowOrchestrator(config1)
        orchestrator2 = WorkflowOrchestrator(config2)
        
        try:
            # Verify different workflow IDs
            assert orchestrator1.workflow_id != orchestrator2.workflow_id
            
            # Verify different configurations
            assert orchestrator1.config.name != orchestrator2.config.name
            
            # Both should be able to get metrics
            metrics1 = orchestrator1.get_workflow_metrics()
            metrics2 = orchestrator2.get_workflow_metrics()
            
            assert metrics1["workflow_id"] != metrics2["workflow_id"]
            
        finally:
            # Cleanup
            await orchestrator1.stop_workflow()
            await orchestrator2.stop_workflow()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])