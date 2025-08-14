"""
Tests for Supervisor Agent Framework
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.core.supervisor_agent import (
    SupervisorAgent, SupervisorDecision, DecisionType, Priority,
    WorkflowCoordination, ConflictResolution, PerformanceMonitoring,
    DecisionEngine, CoordinationManager, ConflictResolver, PerformanceMonitor
)
from app.core.agent_state import AgentState, AgentType, StateManager, WorkflowStatus
from app.core.base_agent import AgentStatus


class TestSupervisorDecision:
    """Test SupervisorDecision model"""
    
    def test_decision_creation(self):
        """Test creating a supervisor decision"""
        decision = SupervisorDecision(
            decision_type=DecisionType.ROUTE_TO_AGENT,
            target_agent="scout",
            action="scout",
            reasoning="Need more deals in pipeline",
            priority=Priority.HIGH,
            confidence=0.9
        )
        
        assert decision.decision_type == DecisionType.ROUTE_TO_AGENT
        assert decision.target_agent == "scout"
        assert decision.action == "scout"
        assert decision.priority == Priority.HIGH
        assert decision.confidence == 0.9
        assert decision.executed == False
        assert decision.id is not None


class TestWorkflowCoordination:
    """Test WorkflowCoordination model"""
    
    def test_coordination_creation(self):
        """Test creating workflow coordination"""
        coordination = WorkflowCoordination(
            workflow_id="test-workflow-123",
            active_agents=["scout", "analyst"],
            pending_tasks={"scout": "find_deals", "analyst": "analyze_property"}
        )
        
        assert coordination.workflow_id == "test-workflow-123"
        assert len(coordination.active_agents) == 2
        assert "scout" in coordination.active_agents
        assert coordination.pending_tasks["scout"] == "find_deals"


class TestConflictResolution:
    """Test ConflictResolution model"""
    
    def test_conflict_creation(self):
        """Test creating conflict resolution"""
        conflict = ConflictResolution(
            conflicting_agents=["agent1", "agent2"],
            conflict_type="resource_conflict",
            description="Both agents trying to access same resource",
            resolution_strategy="priority_based"
        )
        
        assert len(conflict.conflicting_agents) == 2
        assert conflict.conflict_type == "resource_conflict"
        assert conflict.resolved == False
        assert conflict.conflict_id is not None


class TestDecisionEngine:
    """Test DecisionEngine"""
    
    @pytest.fixture
    def supervisor_agent(self):
        """Create supervisor agent for testing"""
        return SupervisorAgent()
    
    @pytest.fixture
    def decision_engine(self, supervisor_agent):
        """Create decision engine for testing"""
        return DecisionEngine(supervisor_agent)
    
    def test_decision_engine_initialization(self, decision_engine):
        """Test decision engine initialization"""
        decision_engine.initialize()
        
        assert len(decision_engine.decision_rules) > 0
        assert decision_engine.confidence_threshold == 0.8
    
    @pytest.mark.asyncio
    async def test_route_to_scout_rule(self, decision_engine):
        """Test rule for routing to scout agent"""
        state = StateManager.create_initial_state()
        analysis = {"current_deals": 2}  # Low number of deals
        
        decision = await decision_engine._rule_route_to_scout(state, analysis)
        
        assert decision is not None
        assert decision.decision_type == DecisionType.ROUTE_TO_AGENT
        assert decision.target_agent == "scout"
        assert decision.confidence == 0.9
    
    @pytest.mark.asyncio
    async def test_route_to_analyst_rule(self, decision_engine):
        """Test rule for routing to analyst agent"""
        state = StateManager.create_initial_state()
        state["current_deals"] = [
            {"id": "deal1", "analyzed": False},
            {"id": "deal2", "analyzed": True}
        ]
        analysis = {}
        
        decision = await decision_engine._rule_route_to_analyst(state, analysis)
        
        assert decision is not None
        assert decision.decision_type == DecisionType.ROUTE_TO_AGENT
        assert decision.target_agent == "analyst"
        assert decision.confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_route_to_negotiator_rule(self, decision_engine):
        """Test rule for routing to negotiator agent"""
        state = StateManager.create_initial_state()
        state["current_deals"] = [
            {"id": "deal1", "status": "approved", "outreach_initiated": False},
            {"id": "deal2", "status": "analyzing"}
        ]
        analysis = {}
        
        decision = await decision_engine._rule_route_to_negotiator(state, analysis)
        
        assert decision is not None
        assert decision.decision_type == DecisionType.ROUTE_TO_AGENT
        assert decision.target_agent == "negotiator"
        assert decision.confidence == 0.92
    
    @pytest.mark.asyncio
    async def test_escalate_to_human_rule(self, decision_engine):
        """Test rule for escalating to human"""
        state = StateManager.create_initial_state()
        analysis = {
            "system_health": {
                "status": "critical",
                "issues": ["Database connection failed"]
            }
        }
        
        decision = await decision_engine._rule_escalate_to_human(state, analysis)
        
        assert decision is not None
        assert decision.decision_type == DecisionType.ESCALATE_TO_HUMAN
        assert decision.priority == Priority.CRITICAL
        assert decision.confidence == 1.0
    
    @pytest.mark.asyncio
    async def test_end_workflow_rule(self, decision_engine):
        """Test rule for ending workflow"""
        state = StateManager.create_initial_state()
        state["current_deals"] = [
            {"id": "deal1", "status": "closed"},
            {"id": "deal2", "status": "closed"}
        ]
        state["active_negotiations"] = []
        analysis = {}
        
        decision = await decision_engine._rule_end_workflow(state, analysis)
        
        assert decision is not None
        assert decision.decision_type == DecisionType.END_WORKFLOW
        assert decision.confidence == 0.85
    
    @pytest.mark.asyncio
    async def test_make_decision_with_matching_rule(self, decision_engine):
        """Test making decision when rule matches"""
        decision_engine.initialize()
        
        state = StateManager.create_initial_state()
        state["current_deals"] = [{"id": "deal1", "analyzed": False}]
        analysis = {"current_deals": 1}
        
        decision = await decision_engine.make_decision(state, analysis)
        
        assert decision is not None
        assert decision.confidence >= decision_engine.confidence_threshold
    
    @pytest.mark.asyncio
    async def test_make_decision_default(self, decision_engine):
        """Test making default decision when no rules match"""
        decision_engine.initialize()
        decision_engine.confidence_threshold = 1.0  # Set high threshold
        
        state = StateManager.create_initial_state()
        analysis = {"current_deals": 10}  # High number, won't trigger scout rule
        
        decision = await decision_engine.make_decision(state, analysis)
        
        assert decision is not None
        assert decision.target_agent == "scout"  # Default action
        assert decision.confidence == 0.5


class TestCoordinationManager:
    """Test CoordinationManager"""
    
    @pytest.fixture
    def supervisor_agent(self):
        """Create supervisor agent for testing"""
        return SupervisorAgent()
    
    @pytest.fixture
    def coordination_manager(self, supervisor_agent):
        """Create coordination manager for testing"""
        return CoordinationManager(supervisor_agent)
    
    @pytest.mark.asyncio
    async def test_create_sequential_coordination_plan(self, coordination_manager):
        """Test creating sequential coordination plan"""
        agents = ["scout", "analyst", "negotiator"]
        state = StateManager.create_initial_state()
        
        plan = await coordination_manager.create_coordination_plan(
            agents, "sequential", state
        )
        
        assert plan["type"] == "sequential"
        assert len(plan["agents"]) == 3
        assert len(plan["steps"]) == 3
        assert plan["steps"][0]["agent"] == "scout"
        assert plan["steps"][0]["depends_on"] is None
        assert plan["steps"][1]["depends_on"] == "scout"
        assert plan["coordination_id"] is not None
    
    @pytest.mark.asyncio
    async def test_create_parallel_coordination_plan(self, coordination_manager):
        """Test creating parallel coordination plan"""
        agents = ["scout", "analyst"]
        state = StateManager.create_initial_state()
        
        plan = await coordination_manager.create_coordination_plan(
            agents, "parallel", state
        )
        
        assert plan["type"] == "parallel"
        assert len(plan["agents"]) == 2
        assert len(plan["steps"]) == 2
        assert plan["steps"][0]["depends_on"] is None
        assert plan["steps"][1]["depends_on"] is None
    
    @pytest.mark.asyncio
    async def test_update_coordination(self, coordination_manager):
        """Test updating coordination state"""
        state = StateManager.create_initial_state()
        workflow_id = state["workflow_id"]
        state["active_agents"] = ["scout", "analyst"]
        
        await coordination_manager.update_coordination(state)
        
        assert workflow_id in coordination_manager.supervisor.workflow_coordinations
        coordination = coordination_manager.supervisor.workflow_coordinations[workflow_id]
        assert coordination.workflow_id == workflow_id
        assert len(coordination.active_agents) == 2
        assert coordination.last_coordination is not None


class TestConflictResolver:
    """Test ConflictResolver"""
    
    @pytest.fixture
    def supervisor_agent(self):
        """Create supervisor agent for testing"""
        return SupervisorAgent()
    
    @pytest.fixture
    def conflict_resolver(self, supervisor_agent):
        """Create conflict resolver for testing"""
        return ConflictResolver(supervisor_agent)
    
    @pytest.mark.asyncio
    async def test_detect_conflicts(self, conflict_resolver):
        """Test conflict detection"""
        state = StateManager.create_initial_state()
        
        conflicts = await conflict_resolver.detect_conflicts(state)
        
        # Should return empty list for clean state
        assert isinstance(conflicts, list)
    
    @pytest.mark.asyncio
    async def test_resolve_resource_conflict(self, conflict_resolver):
        """Test resolving resource conflict"""
        conflict = ConflictResolution(
            conflicting_agents=["agent1", "agent2"],
            conflict_type="resource_conflict",
            description="Resource access conflict",
            resolution_strategy="priority_based"
        )
        
        state = StateManager.create_initial_state()
        
        result = await conflict_resolver.resolve_conflict(conflict, state)
        
        assert result["resolved"] == True
        assert len(result["actions_taken"]) > 0
        assert "Reallocated resources" in result["actions_taken"]
    
    @pytest.mark.asyncio
    async def test_resolve_decision_conflict(self, conflict_resolver):
        """Test resolving decision conflict"""
        conflict = ConflictResolution(
            conflicting_agents=["agent1", "agent2"],
            conflict_type="decision_conflict",
            description="Contradictory decisions",
            resolution_strategy="priority_based"
        )
        
        state = StateManager.create_initial_state()
        
        result = await conflict_resolver.resolve_conflict(conflict, state)
        
        assert result["resolved"] == True
        assert "Applied priority-based resolution" in result["actions_taken"]


class TestPerformanceMonitor:
    """Test PerformanceMonitor"""
    
    @pytest.fixture
    def supervisor_agent(self):
        """Create supervisor agent for testing"""
        return SupervisorAgent()
    
    @pytest.fixture
    def performance_monitor(self, supervisor_agent):
        """Create performance monitor for testing"""
        return PerformanceMonitor(supervisor_agent)
    
    @pytest.mark.asyncio
    async def test_update_monitoring_data(self, performance_monitor):
        """Test updating monitoring data"""
        state = StateManager.create_initial_state()
        state["workflow_status"] = WorkflowStatus.RUNNING
        state["active_agents"] = ["scout", "analyst"]
        
        await performance_monitor.update_monitoring_data(state)
        
        monitoring = performance_monitor.supervisor.performance_monitoring
        assert monitoring.last_monitoring_update is not None
        assert monitoring.system_health["workflow_status"] == WorkflowStatus.RUNNING
        assert monitoring.system_health["active_agents"] == 2
    
    @pytest.mark.asyncio
    async def test_generate_recommendations(self, performance_monitor):
        """Test generating performance recommendations"""
        # Add some decision history to trigger recommendations
        for i in range(6):
            decision = SupervisorDecision(
                decision_type=DecisionType.ROUTE_TO_AGENT,
                target_agent="scout",
                action="scout",
                reasoning=f"Decision {i}"
            )
            performance_monitor.supervisor.decision_history.append(decision)
        
        recommendations = await performance_monitor.generate_recommendations()
        
        assert isinstance(recommendations, list)
        if recommendations:
            assert "type" in recommendations[0]
            assert "description" in recommendations[0]


class TestSupervisorAgent:
    """Test SupervisorAgent"""
    
    @pytest.fixture
    def supervisor_agent(self):
        """Create supervisor agent for testing"""
        return SupervisorAgent()
    
    def test_supervisor_initialization(self, supervisor_agent):
        """Test supervisor agent initialization"""
        assert supervisor_agent.agent_type == AgentType.SUPERVISOR
        assert supervisor_agent.name == "supervisor_agent"
        assert supervisor_agent.status == AgentStatus.IDLE
        assert len(supervisor_agent.capabilities) == 5
        assert supervisor_agent.initialized == True
        
        # Check supervisor-specific components
        assert supervisor_agent.decision_engine is not None
        assert supervisor_agent.coordination_manager is not None
        assert supervisor_agent.conflict_resolver is not None
        assert supervisor_agent.performance_monitor is not None
    
    def test_supervisor_capabilities(self, supervisor_agent):
        """Test supervisor capabilities"""
        assert supervisor_agent.has_capability("workflow_orchestration")
        assert supervisor_agent.has_capability("agent_coordination")
        assert supervisor_agent.has_capability("conflict_resolution")
        assert supervisor_agent.has_capability("performance_monitoring")
        assert supervisor_agent.has_capability("human_escalation")
    
    def test_available_tasks(self, supervisor_agent):
        """Test available supervisor tasks"""
        tasks = supervisor_agent.get_available_tasks()
        
        expected_tasks = [
            "make_routing_decision",
            "coordinate_agents",
            "resolve_conflict",
            "monitor_performance",
            "escalate_to_human"
        ]
        
        for task in expected_tasks:
            assert task in tasks
    
    @pytest.mark.asyncio
    async def test_process_state(self, supervisor_agent):
        """Test supervisor state processing"""
        initial_state = StateManager.create_initial_state()
        initial_state["current_deals"] = [{"id": "deal1", "analyzed": False}]
        
        with patch.object(supervisor_agent.decision_engine, 'make_decision') as mock_decision:
            mock_decision.return_value = SupervisorDecision(
                decision_type=DecisionType.ROUTE_TO_AGENT,
                target_agent="analyst",
                action="analyze",
                reasoning="Test decision"
            )
            
            result_state = await supervisor_agent.process_state(initial_state)
            
            assert result_state is not None
            assert len(result_state["agent_messages"]) > 0
            mock_decision.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_routing_task(self, supervisor_agent):
        """Test executing routing decision task"""
        state = StateManager.create_initial_state()
        data = {"context": "test"}
        
        with patch.object(supervisor_agent.decision_engine, 'make_decision') as mock_decision:
            mock_decision.return_value = SupervisorDecision(
                decision_type=DecisionType.ROUTE_TO_AGENT,
                target_agent="scout",
                action="scout",
                reasoning="Test routing"
            )
            
            result = await supervisor_agent.execute_task("make_routing_decision", data, state)
            
            assert "decision" in result
            assert "analysis" in result
            assert result["decision"]["target_agent"] == "scout"
    
    @pytest.mark.asyncio
    async def test_execute_coordination_task(self, supervisor_agent):
        """Test executing agent coordination task"""
        state = StateManager.create_initial_state()
        data = {
            "agents": ["scout", "analyst"],
            "coordination_type": "sequential"
        }
        
        result = await supervisor_agent.execute_task("coordinate_agents", data, state)
        
        assert "coordination_plan" in result
        plan = result["coordination_plan"]
        assert plan["type"] == "sequential"
        assert len(plan["agents"]) == 2
    
    @pytest.mark.asyncio
    async def test_execute_conflict_resolution_task(self, supervisor_agent):
        """Test executing conflict resolution task"""
        state = StateManager.create_initial_state()
        data = {
            "conflict_data": {
                "agents": ["agent1", "agent2"],
                "type": "resource_conflict",
                "description": "Test conflict"
            }
        }
        
        result = await supervisor_agent.execute_task("resolve_conflict", data, state)
        
        assert "resolution_result" in result
        assert result["resolution_result"]["resolved"] == True
    
    @pytest.mark.asyncio
    async def test_execute_performance_monitoring_task(self, supervisor_agent):
        """Test executing performance monitoring task"""
        state = StateManager.create_initial_state()
        data = {}
        
        result = await supervisor_agent.execute_task("monitor_performance", data, state)
        
        assert "performance_data" in result
        assert "recommendations" in result
    
    @pytest.mark.asyncio
    async def test_execute_human_escalation_task(self, supervisor_agent):
        """Test executing human escalation task"""
        state = StateManager.create_initial_state()
        data = {
            "reason": "Test escalation",
            "context": {"test": "data"}
        }
        
        result = await supervisor_agent.execute_task("escalate_to_human", data, state)
        
        assert "escalation_id" in result
        assert result["status"] == "escalated"
        assert len(supervisor_agent.pending_human_decisions) == 1
    
    def test_situation_analysis(self, supervisor_agent):
        """Test situation analysis"""
        state = StateManager.create_initial_state()
        state["current_deals"] = [{"id": "deal1"}, {"id": "deal2"}]
        state["active_negotiations"] = [{"id": "neg1"}]
        
        analysis = asyncio.run(supervisor_agent._analyze_situation(state))
        
        assert "workflow_status" in analysis
        assert "current_deals" in analysis
        assert "pending_negotiations" in analysis
        assert "system_health" in analysis
        assert analysis["current_deals"] == 2
        assert analysis["pending_negotiations"] == 1
    
    def test_system_health_assessment(self, supervisor_agent):
        """Test system health assessment"""
        state = StateManager.create_initial_state()
        
        # Test healthy state
        health = supervisor_agent._assess_system_health(state)
        assert health["status"] == "healthy"
        assert len(health["issues"]) == 0
        
        # Test degraded state with errors
        state["agent_messages"] = [
            {"message": "Error occurred", "priority": 4}
        ]
        health = supervisor_agent._assess_system_health(state)
        assert health["status"] == "degraded"
        assert len(health["issues"]) > 0
        
        # Test critical state
        state["workflow_status"] = WorkflowStatus.ERROR
        health = supervisor_agent._assess_system_health(state)
        assert health["status"] == "critical"
    
    def test_bottleneck_identification(self, supervisor_agent):
        """Test bottleneck identification"""
        state = StateManager.create_initial_state()
        
        # Create stalled deal
        old_time = (datetime.now() - timedelta(minutes=10)).isoformat()
        state["current_deals"] = [
            {
                "id": "deal1",
                "status": "analyzing",
                "last_updated": old_time
            }
        ]
        
        bottlenecks = supervisor_agent._identify_bottlenecks(state)
        assert len(bottlenecks) > 0
        assert "Analysis bottleneck" in bottlenecks[0]
    
    def test_opportunity_identification(self, supervisor_agent):
        """Test opportunity identification"""
        state = StateManager.create_initial_state()
        state["current_deals"] = [
            {
                "id": "deal1",
                "status": "approved",
                "outreach_initiated": False
            }
        ]
        
        opportunities = supervisor_agent._identify_opportunities(state)
        assert len(opportunities) > 0
        assert "Outreach opportunity" in opportunities[0]
    
    @pytest.mark.asyncio
    async def test_human_response_handling(self, supervisor_agent):
        """Test handling human responses"""
        # Add pending decision
        decision = SupervisorDecision(
            decision_type=DecisionType.ESCALATE_TO_HUMAN,
            action="test_action",
            reasoning="Test escalation"
        )
        supervisor_agent.pending_human_decisions.append(decision)
        supervisor_agent.human_approval_required = True
        
        # Test approval
        response = await supervisor_agent.handle_human_response("approve")
        assert response["status"] == "approved"
        assert response["action"] == "continue"
        assert len(supervisor_agent.pending_human_decisions) == 0
        assert supervisor_agent.human_approval_required == False
        
        # Test rejection
        supervisor_agent.pending_human_decisions.append(decision)
        supervisor_agent.human_approval_required = True
        
        response = await supervisor_agent.handle_human_response("reject")
        assert response["status"] == "rejected"
        assert response["action"] == "abort"
        assert len(supervisor_agent.pending_human_decisions) == 0
        
        # Test unclear response
        response = await supervisor_agent.handle_human_response("maybe")
        assert response["status"] == "clarification_needed"
    
    def test_decision_history(self, supervisor_agent):
        """Test decision history management"""
        # Add some decisions
        for i in range(5):
            decision = SupervisorDecision(
                decision_type=DecisionType.ROUTE_TO_AGENT,
                target_agent="scout",
                action=f"action_{i}",
                reasoning=f"Reason {i}"
            )
            supervisor_agent.decision_history.append(decision)
        
        history = supervisor_agent.get_decision_history(limit=3)
        assert len(history) == 3
        assert history[0]["action"] == "action_2"  # Most recent first
    
    def test_performance_summary(self, supervisor_agent):
        """Test performance summary"""
        summary = supervisor_agent.get_performance_summary()
        
        assert "monitoring_data" in summary
        assert "decision_count" in summary
        assert "active_conflicts" in summary
        assert "workflow_coordinations" in summary
        assert summary["decision_count"] == len(supervisor_agent.decision_history)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])