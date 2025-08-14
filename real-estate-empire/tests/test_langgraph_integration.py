"""
Integration tests for LangGraph setup and agent communication
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.core.langgraph_setup import LangGraphOrchestrator
from app.core.agent_state import StateManager, AgentState, AgentType, WorkflowStatus
from app.core.agent_communication import AgentCommunicationProtocol, MessageType, MessagePriority
from app.core.llm_config import llm_manager


class TestLangGraphSetup:
    """Test LangGraph workflow setup and execution"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing"""
        return LangGraphOrchestrator()
    
    @pytest.fixture
    def initial_state(self):
        """Create initial state for testing"""
        return StateManager.create_initial_state()
    
    def test_workflow_initialization(self, orchestrator):
        """Test that workflow is properly initialized"""
        assert orchestrator.workflow is not None
        assert orchestrator.compiled_workflow is not None
        assert orchestrator.memory_saver is not None
    
    def test_initial_state_creation(self, initial_state):
        """Test initial state creation"""
        assert initial_state["workflow_status"] == WorkflowStatus.INITIALIZING
        assert initial_state["current_step"] == "supervisor"
        assert len(initial_state["current_deals"]) == 0
        assert initial_state["available_capital"] == 0.0
    
    @pytest.mark.asyncio
    async def test_supervisor_agent_execution(self, orchestrator, initial_state):
        """Test supervisor agent execution"""
        with patch.object(llm_manager, 'get_llm') as mock_llm:
            # Mock LLM response
            mock_response = Mock()
            mock_response.content = "I recommend we start with scouting for new deals to build our pipeline."
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
            
            # Execute supervisor agent
            result_state = await orchestrator._supervisor_agent(initial_state)
            
            # Verify state updates
            assert result_state["workflow_status"] == WorkflowStatus.RUNNING
            assert result_state["next_action"] == "scout"
            assert len(result_state["agent_messages"]) > 0
    
    @pytest.mark.asyncio
    async def test_scout_agent_execution(self, orchestrator, initial_state):
        """Test scout agent execution"""
        with patch.object(llm_manager, 'get_llm') as mock_llm:
            # Mock LLM response
            mock_response = Mock()
            mock_response.content = "Found 2 high-potential properties in Austin, TX"
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
            
            # Execute scout agent
            result_state = await orchestrator._scout_agent(initial_state)
            
            # Verify deals were added
            assert len(result_state["current_deals"]) > 0
            assert any("scout" in msg["agent"] for msg in result_state["agent_messages"])
    
    @pytest.mark.asyncio
    async def test_analyst_agent_execution(self, orchestrator):
        """Test analyst agent execution"""
        # Create state with unanalyzed deals
        state = StateManager.create_initial_state()
        state["current_deals"] = [{
            "id": "test-deal-1",
            "property_address": "123 Test St",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701",
            "listing_price": 300000,
            "analyzed": False
        }]
        
        with patch.object(llm_manager, 'get_llm') as mock_llm:
            # Mock LLM response
            mock_response = Mock()
            mock_response.content = "This property shows strong potential. I recommend we proceed with an offer."
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
            
            # Execute analyst agent
            result_state = await orchestrator._analyst_agent(state)
            
            # Verify analysis was completed
            deal = result_state["current_deals"][0]
            assert deal["analyzed"] == True
            assert "analysis_data" in deal
    
    def test_routing_logic(self, orchestrator):
        """Test workflow routing logic"""
        # Test routing with no deals
        state = StateManager.create_initial_state()
        route = orchestrator._route_next_action(state)
        assert route == "scout"
        
        # Test routing with unanalyzed deals
        state["current_deals"] = [{"analyzed": False}]
        route = orchestrator._route_next_action(state)
        assert route == "analyze"
        
        # Test routing with approved deals
        state["current_deals"] = [{"analyzed": True, "status": "approved", "outreach_initiated": False}]
        route = orchestrator._route_next_action(state)
        assert route == "negotiate"


class TestAgentCommunication:
    """Test agent communication protocols"""
    
    @pytest.fixture
    def comm_protocol(self):
        """Create communication protocol for testing"""
        return AgentCommunicationProtocol()
    
    def test_agent_registration(self, comm_protocol):
        """Test agent registration"""
        agent_info = {"type": "scout", "version": "1.0"}
        comm_protocol.register_agent("scout_agent", agent_info)
        
        status = comm_protocol.get_agent_status("scout_agent")
        assert status is not None
        assert status["name"] == "scout_agent"
        assert status["status"] == "active"
    
    def test_active_agents_list(self, comm_protocol):
        """Test listing active agents"""
        comm_protocol.register_agent("agent1", {"type": "scout"})
        comm_protocol.register_agent("agent2", {"type": "analyst"})
        
        active_agents = comm_protocol.list_active_agents()
        assert len(active_agents) == 2
        assert "agent1" in active_agents
        assert "agent2" in active_agents
    
    @pytest.mark.asyncio
    async def test_message_sending(self, comm_protocol):
        """Test message sending between agents"""
        with patch.object(comm_protocol.message_bus, 'publish_message') as mock_publish:
            mock_publish.return_value = True
            
            correlation_id = await comm_protocol.send_task_request(
                sender="supervisor",
                recipient="scout",
                task="find_deals",
                data={"location": "Austin, TX"},
                priority=MessagePriority.HIGH
            )
            
            assert correlation_id is not None
            mock_publish.assert_called_once()


class TestStateManager:
    """Test state management functionality"""
    
    def test_add_agent_message(self):
        """Test adding agent messages to state"""
        state = StateManager.create_initial_state()
        
        updated_state = StateManager.add_agent_message(
            state,
            AgentType.SCOUT,
            "Found 5 new deals",
            data={"deals_count": 5},
            priority=2
        )
        
        assert len(updated_state["agent_messages"]) == 1
        message = updated_state["agent_messages"][0]
        assert message["agent"] == AgentType.SCOUT
        assert message["message"] == "Found 5 new deals"
        assert message["data"]["deals_count"] == 5
    
    def test_deal_management(self):
        """Test deal addition and status updates"""
        from app.core.agent_state import Deal, DealStatus
        
        state = StateManager.create_initial_state()
        
        # Add a deal
        deal = Deal(
            property_address="123 Test St",
            city="Austin",
            state="TX",
            zip_code="78701"
        )
        
        updated_state = StateManager.add_deal(state, deal)
        assert len(updated_state["current_deals"]) == 1
        
        # Update deal status
        deal_id = updated_state["current_deals"][0]["id"]
        updated_state = StateManager.update_deal_status(
            updated_state,
            deal_id,
            DealStatus.ANALYZED,
            {"confidence_score": 8.5}
        )
        
        updated_deal = updated_state["current_deals"][0]
        assert updated_deal["status"] == DealStatus.ANALYZED
        assert updated_deal["confidence_score"] == 8.5
    
    def test_deals_by_status_filter(self):
        """Test filtering deals by status"""
        from app.core.agent_state import Deal, DealStatus
        
        state = StateManager.create_initial_state()
        
        # Add deals with different statuses
        deal1 = Deal(property_address="123 St", city="Austin", state="TX", zip_code="78701")
        deal2 = Deal(property_address="456 Ave", city="Austin", state="TX", zip_code="78702")
        
        state = StateManager.add_deal(state, deal1)
        state = StateManager.add_deal(state, deal2)
        
        # Update one deal status
        deal_id = state["current_deals"][0]["id"]
        state = StateManager.update_deal_status(state, deal_id, DealStatus.ANALYZED)
        
        # Filter deals
        discovered_deals = StateManager.get_deals_by_status(state, DealStatus.DISCOVERED)
        analyzed_deals = StateManager.get_deals_by_status(state, DealStatus.ANALYZED)
        
        assert len(discovered_deals) == 1
        assert len(analyzed_deals) == 1
    
    def test_next_action_setting(self):
        """Test setting next action in workflow"""
        state = StateManager.create_initial_state()
        
        updated_state = StateManager.set_next_action(
            state,
            "scout",
            "Need to find more deals for the pipeline"
        )
        
        assert updated_state["next_action"] == "scout"
        assert updated_state["current_step"] == "scout"
        assert len(updated_state["agent_messages"]) == 1


class TestLLMConfiguration:
    """Test LLM configuration and management"""
    
    def test_llm_manager_initialization(self):
        """Test LLM manager initialization"""
        assert llm_manager.llm_instances is not None
        assert len(llm_manager.llm_instances) > 0
    
    def test_agent_llm_configs(self):
        """Test agent-specific LLM configurations"""
        scout_config = llm_manager.get_config("scout")
        analyst_config = llm_manager.get_config("analyst")
        
        assert scout_config.temperature == 0.3  # Lower for consistent scoring
        assert analyst_config.temperature == 0.2  # Lowest for financial accuracy
        assert scout_config.max_tokens == 2000
        assert analyst_config.max_tokens == 4000
    
    def test_llm_retrieval(self):
        """Test LLM instance retrieval"""
        scout_llm = llm_manager.get_llm("scout")
        analyst_llm = llm_manager.get_llm("analyst")
        
        assert scout_llm is not None
        assert analyst_llm is not None
        assert scout_llm != analyst_llm  # Different instances
    
    @pytest.mark.asyncio
    async def test_llm_fallback_mechanism(self):
        """Test LLM fallback to backup models"""
        with patch.object(llm_manager, 'get_llm') as mock_get_llm:
            # Mock primary LLM to fail
            mock_primary = Mock()
            mock_primary.ainvoke = AsyncMock(side_effect=Exception("API Error"))
            mock_get_llm.return_value = mock_primary
            
            with patch.object(llm_manager, '_create_llm_instance') as mock_create:
                # Mock backup LLM to succeed
                mock_backup = Mock()
                mock_backup.ainvoke = AsyncMock(return_value=Mock(content="Backup response"))
                mock_create.return_value = mock_backup
                
                # Test fallback
                response = await llm_manager.invoke_with_fallback("scout", "Test prompt")
                assert response == "Backup response"
    
    def test_cost_estimation(self):
        """Test LLM cost estimation"""
        cost = llm_manager.estimate_cost("scout", prompt_tokens=100, completion_tokens=50)
        assert cost > 0
        assert isinstance(cost, float)


@pytest.mark.integration
class TestEndToEndWorkflow:
    """End-to-end integration tests"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_cycle(self):
        """Test a complete workflow cycle from start to finish"""
        orchestrator = LangGraphOrchestrator()
        
        with patch.object(llm_manager, 'get_llm') as mock_llm:
            # Mock all LLM responses
            mock_response = Mock()
            mock_response.content = "Proceeding with scouting for new deals"
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
            
            # Start workflow
            initial_state = StateManager.create_initial_state()
            workflow_id = await orchestrator.start_workflow(initial_state)
            
            assert workflow_id is not None
            
            # Get final state
            final_state = await orchestrator.get_workflow_state(workflow_id)
            assert final_state["workflow_status"] in [WorkflowStatus.RUNNING, WorkflowStatus.COMPLETED]
    
    @pytest.mark.asyncio
    async def test_human_escalation_workflow(self):
        """Test workflow with human escalation"""
        orchestrator = LangGraphOrchestrator()
        
        # Create state that triggers human escalation
        state = StateManager.create_initial_state()
        state["next_action"] = "human_escalation"
        
        result_state = await orchestrator._human_escalation_node(state)
        
        assert result_state["workflow_status"] == WorkflowStatus.HUMAN_ESCALATION
        assert result_state["human_approval_required"] == True
    
    @pytest.mark.asyncio
    async def test_workflow_continuation_after_pause(self):
        """Test continuing workflow after human input"""
        orchestrator = LangGraphOrchestrator()
        
        with patch.object(orchestrator, 'get_workflow_state') as mock_get_state:
            mock_state = StateManager.create_initial_state()
            mock_state["workflow_status"] = WorkflowStatus.HUMAN_ESCALATION
            mock_get_state.return_value = mock_state
            
            with patch.object(orchestrator.compiled_workflow, 'ainvoke') as mock_invoke:
                mock_invoke.return_value = mock_state
                
                # Continue workflow with human input
                result = await orchestrator.continue_workflow("test-workflow", "approve")
                
                assert result is not None
                mock_invoke.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])