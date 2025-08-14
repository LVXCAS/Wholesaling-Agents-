"""
Tests for Base Agent Classes and Interfaces
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.core.base_agent import (
    BaseAgent, AgentCapability, AgentMetrics, AgentMemory, 
    AgentStatus, AgentLifecycleManager, agent_lifecycle_manager
)
from app.core.agent_state import AgentState, AgentType, StateManager
from app.core.agent_communication import MessageType, MessagePriority
from app.core.shared_memory import SharedMemoryManager, MemoryType, MemoryScope


class TestAgentCapability:
    """Test AgentCapability model"""
    
    def test_capability_creation(self):
        """Test creating an agent capability"""
        capability = AgentCapability(
            name="property_analysis",
            description="Analyze property investment potential",
            input_schema={"property_data": "dict"},
            output_schema={"analysis_result": "dict"},
            required_tools=["calculator", "comparables_api"],
            estimated_duration=30,
            confidence_level=0.9
        )
        
        assert capability.name == "property_analysis"
        assert capability.description == "Analyze property investment potential"
        assert len(capability.required_tools) == 2
        assert capability.confidence_level == 0.9


class TestAgentMetrics:
    """Test AgentMetrics model"""
    
    def test_metrics_initialization(self):
        """Test metrics initialization with defaults"""
        metrics = AgentMetrics()
        
        assert metrics.tasks_completed == 0
        assert metrics.tasks_failed == 0
        assert metrics.success_rate == 0.0
        assert metrics.uptime_percentage == 100.0
    
    def test_metrics_with_values(self):
        """Test metrics with specific values"""
        metrics = AgentMetrics(
            tasks_completed=10,
            tasks_failed=2,
            average_response_time=1.5,
            success_rate=0.83
        )
        
        assert metrics.tasks_completed == 10
        assert metrics.tasks_failed == 2
        assert metrics.success_rate == 0.83


class TestAgentMemory:
    """Test AgentMemory model"""
    
    def test_memory_initialization(self):
        """Test memory initialization"""
        memory = AgentMemory()
        
        assert len(memory.short_term_memory) == 0
        assert len(memory.long_term_memory) == 0
        assert len(memory.conversation_history) == 0
    
    def test_short_term_memory_operations(self):
        """Test short-term memory operations"""
        memory = AgentMemory()
        
        # Add to short-term memory
        memory.add_to_short_term("test_key", "test_value", ttl=60)
        
        # Retrieve from short-term memory
        value = memory.get_memory("test_key", "short_term")
        assert value == "test_value"
        
        # Test non-existent key
        assert memory.get_memory("non_existent", "short_term") is None
    
    def test_long_term_memory_operations(self):
        """Test long-term memory operations"""
        memory = AgentMemory()
        
        # Add to long-term memory
        memory.add_to_long_term("persistent_key", {"data": "important"})
        
        # Retrieve from long-term memory
        value = memory.get_memory("persistent_key", "long_term")
        assert value == {"data": "important"}
    
    def test_memory_clear(self):
        """Test clearing short-term memory"""
        memory = AgentMemory()
        
        memory.add_to_short_term("temp1", "value1")
        memory.add_to_short_term("temp2", "value2")
        
        assert len(memory.short_term_memory) == 2
        
        memory.clear_short_term()
        assert len(memory.short_term_memory) == 0


class MockAgent(BaseAgent):
    """Mock agent implementation for testing"""
    
    def _agent_specific_initialization(self):
        """Mock agent-specific initialization"""
        self.initialized = True
    
    async def execute_task(self, task: str, data: dict, state: AgentState) -> dict:
        """Mock task execution"""
        if task == "test_task":
            return {"result": "success", "data": data}
        elif task == "failing_task":
            raise Exception("Task failed")
        else:
            return {"result": "unknown_task"}
    
    async def process_state(self, state: AgentState) -> AgentState:
        """Mock state processing"""
        # Add a test message to demonstrate processing
        updated_state = StateManager.add_agent_message(
            state,
            self.agent_type,
            f"Processed by {self.name}",
            data={"processed_at": datetime.now().isoformat()}
        )
        return updated_state
    
    def get_available_tasks(self) -> list:
        """Mock available tasks"""
        return ["test_task", "failing_task", "analysis_task"]


class TestBaseAgent:
    """Test BaseAgent abstract class"""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing"""
        capabilities = [
            AgentCapability(
                name="test_capability",
                description="Test capability",
                input_schema={"input": "str"},
                output_schema={"output": "str"}
            )
        ]
        
        agent = MockAgent(
            agent_type=AgentType.SCOUT,
            name="test_scout",
            description="Test scout agent",
            capabilities=capabilities
        )
        
        return agent
    
    def test_agent_initialization(self, mock_agent):
        """Test agent initialization"""
        assert mock_agent.agent_type == AgentType.SCOUT
        assert mock_agent.name == "test_scout"
        assert mock_agent.status == AgentStatus.IDLE
        assert len(mock_agent.capabilities) == 1
        assert mock_agent.initialized == True
        assert mock_agent.agent_id is not None
    
    def test_agent_capabilities(self, mock_agent):
        """Test agent capability management"""
        # Test has_capability
        assert mock_agent.has_capability("test_capability") == True
        assert mock_agent.has_capability("non_existent") == False
        
        # Test get_capability
        capability = mock_agent.get_capability("test_capability")
        assert capability is not None
        assert capability.name == "test_capability"
        
        assert mock_agent.get_capability("non_existent") is None
    
    @pytest.mark.asyncio
    async def test_agent_execution_success(self, mock_agent):
        """Test successful agent execution"""
        initial_state = StateManager.create_initial_state()
        
        result_state = await mock_agent.run(initial_state)
        
        assert mock_agent.status == AgentStatus.IDLE
        assert mock_agent.metrics.tasks_completed == 1
        assert mock_agent.metrics.tasks_failed == 0
        assert len(result_state["agent_messages"]) > 0
    
    @pytest.mark.asyncio
    async def test_task_execution(self, mock_agent):
        """Test task execution"""
        initial_state = StateManager.create_initial_state()
        
        # Test successful task
        result = await mock_agent.execute_task("test_task", {"input": "test"}, initial_state)
        assert result["result"] == "success"
        assert result["data"]["input"] == "test"
        
        # Test failing task
        with pytest.raises(Exception):
            await mock_agent.execute_task("failing_task", {}, initial_state)
    
    def test_available_tasks(self, mock_agent):
        """Test getting available tasks"""
        tasks = mock_agent.get_available_tasks()
        assert "test_task" in tasks
        assert "failing_task" in tasks
        assert "analysis_task" in tasks
    
    def test_metrics_update(self, mock_agent):
        """Test metrics updating"""
        initial_completed = mock_agent.metrics.tasks_completed
        initial_failed = mock_agent.metrics.tasks_failed
        
        # Simulate successful task
        mock_agent._update_metrics(1.5, success=True)
        
        assert mock_agent.metrics.tasks_completed == initial_completed + 1
        assert mock_agent.metrics.average_response_time == 1.5
        assert mock_agent.metrics.success_rate > 0
        
        # Simulate failed task
        mock_agent._update_metrics(2.0, success=False)
        
        assert mock_agent.metrics.tasks_failed == initial_failed + 1
    
    def test_memory_operations(self, mock_agent):
        """Test agent memory operations"""
        # Test short-term memory
        mock_agent.memory.add_to_short_term("temp_data", {"value": 123})
        value = mock_agent.memory.get_memory("temp_data", "short_term")
        assert value["value"] == 123
        
        # Test long-term memory
        mock_agent.memory.add_to_long_term("learned_pattern", {"pattern": "abc"})
        pattern = mock_agent.memory.get_memory("learned_pattern", "long_term")
        assert pattern["pattern"] == "abc"
    
    def test_lifecycle_hooks(self, mock_agent):
        """Test lifecycle hooks"""
        hook_called = {"value": False}
        
        def test_hook(agent, state, **kwargs):
            hook_called["value"] = True
        
        mock_agent.add_lifecycle_hook("before_execute", test_hook)
        
        # Check hook was added
        assert len(mock_agent.lifecycle_hooks["before_execute"]) == 1
    
    @pytest.mark.asyncio
    async def test_message_handling(self, mock_agent):
        """Test message handling"""
        from app.core.agent_communication import AgentMessage
        
        # Test task request message
        message = AgentMessage(
            id="test-msg-1",
            sender="test_sender",
            recipient=mock_agent.name,
            message_type=MessageType.TASK_REQUEST,
            priority=MessagePriority.NORMAL,
            content={"task": "test_task", "data": {"input": "test"}},
            timestamp=datetime.now(),
            requires_response=False
        )
        
        await mock_agent._handle_task_request(message)
        
        # Test status update message
        status_message = AgentMessage(
            id="test-msg-2",
            sender="test_sender",
            recipient=mock_agent.name,
            message_type=MessageType.STATUS_UPDATE,
            priority=MessagePriority.LOW,
            content={"status": "running"},
            timestamp=datetime.now()
        )
        
        await mock_agent._handle_status_update(status_message)
        
        # Check if status was stored in memory
        stored_status = mock_agent.memory.get_memory("status_test_sender", "short_term")
        assert stored_status == "running"
    
    def test_agent_string_representation(self, mock_agent):
        """Test agent string representations"""
        str_repr = str(mock_agent)
        assert "scoutAgent" in str_repr
        assert "test_scout" in str_repr
        
        repr_str = repr(mock_agent)
        assert "MockAgent" in repr_str
        assert "test_scout" in repr_str
        assert "scout" in repr_str


class TestAgentLifecycleManager:
    """Test AgentLifecycleManager"""
    
    @pytest.fixture
    def lifecycle_manager(self):
        """Create a lifecycle manager for testing"""
        return AgentLifecycleManager()
    
    @pytest.fixture
    def mock_agents(self):
        """Create mock agents for testing"""
        capabilities = [
            AgentCapability(
                name="test_capability",
                description="Test capability",
                input_schema={"input": "str"},
                output_schema={"output": "str"}
            )
        ]
        
        scout_agent = MockAgent(
            agent_type=AgentType.SCOUT,
            name="scout_1",
            description="Scout agent 1",
            capabilities=capabilities
        )
        
        analyst_agent = MockAgent(
            agent_type=AgentType.ANALYST,
            name="analyst_1",
            description="Analyst agent 1",
            capabilities=capabilities
        )
        
        return [scout_agent, analyst_agent]
    
    @pytest.mark.asyncio
    async def test_lifecycle_manager_initialization(self, lifecycle_manager):
        """Test lifecycle manager initialization"""
        await lifecycle_manager.initialize()
        
        assert lifecycle_manager.communication_protocol is not None
        assert len(lifecycle_manager.agents) == 0
    
    def test_agent_registration(self, lifecycle_manager, mock_agents):
        """Test agent registration"""
        scout_agent, analyst_agent = mock_agents
        
        # Register agents
        lifecycle_manager.register_agent(scout_agent, group="discovery")
        lifecycle_manager.register_agent(analyst_agent, group="analysis")
        
        # Check registration
        assert len(lifecycle_manager.agents) == 2
        assert "scout_1" in lifecycle_manager.agents
        assert "analyst_1" in lifecycle_manager.agents
        
        # Check groups
        assert "discovery" in lifecycle_manager.agent_groups
        assert "analysis" in lifecycle_manager.agent_groups
        assert "scout_1" in lifecycle_manager.agent_groups["discovery"]
    
    def test_agent_retrieval(self, lifecycle_manager, mock_agents):
        """Test agent retrieval methods"""
        scout_agent, analyst_agent = mock_agents
        
        lifecycle_manager.register_agent(scout_agent)
        lifecycle_manager.register_agent(analyst_agent)
        
        # Test get_agent
        retrieved_scout = lifecycle_manager.get_agent("scout_1")
        assert retrieved_scout == scout_agent
        
        # Test get_agents_by_type
        scout_agents = lifecycle_manager.get_agents_by_type(AgentType.SCOUT)
        assert len(scout_agents) == 1
        assert scout_agents[0] == scout_agent
        
        analyst_agents = lifecycle_manager.get_agents_by_type(AgentType.ANALYST)
        assert len(analyst_agents) == 1
        assert analyst_agents[0] == analyst_agent
    
    def test_agent_unregistration(self, lifecycle_manager, mock_agents):
        """Test agent unregistration"""
        scout_agent, analyst_agent = mock_agents
        
        lifecycle_manager.register_agent(scout_agent)
        lifecycle_manager.register_agent(analyst_agent)
        
        assert len(lifecycle_manager.agents) == 2
        
        # Unregister one agent
        lifecycle_manager.unregister_agent("scout_1")
        
        assert len(lifecycle_manager.agents) == 1
        assert "scout_1" not in lifecycle_manager.agents
        assert "analyst_1" in lifecycle_manager.agents
        assert scout_agent.status == AgentStatus.STOPPED
    
    def test_status_summary(self, lifecycle_manager, mock_agents):
        """Test agent status summary"""
        scout_agent, analyst_agent = mock_agents
        
        lifecycle_manager.register_agent(scout_agent)
        lifecycle_manager.register_agent(analyst_agent)
        
        summary = lifecycle_manager.get_agent_status_summary()
        
        assert summary["total_agents"] == 2
        assert "by_status" in summary
        assert "by_type" in summary
        assert "active_agents" in summary
        
        # Check status counts
        assert summary["by_status"]["idle"] == 2
        
        # Check type counts
        assert summary["by_type"]["scout"] == 1
        assert summary["by_type"]["analyst"] == 1
    
    @pytest.mark.asyncio
    async def test_shutdown_all_agents(self, lifecycle_manager, mock_agents):
        """Test shutting down all agents"""
        scout_agent, analyst_agent = mock_agents
        
        lifecycle_manager.register_agent(scout_agent)
        lifecycle_manager.register_agent(analyst_agent)
        
        assert len(lifecycle_manager.agents) == 2
        
        await lifecycle_manager.shutdown_all_agents()
        
        assert len(lifecycle_manager.agents) == 0
        assert len(lifecycle_manager.agent_groups) == 0
        assert scout_agent.status == AgentStatus.STOPPED
        assert analyst_agent.status == AgentStatus.STOPPED


class TestSharedMemoryManager:
    """Test SharedMemoryManager"""
    
    @pytest.fixture
    def memory_manager(self):
        """Create a memory manager for testing"""
        return SharedMemoryManager(database_url="sqlite:///:memory:")
    
    @pytest.mark.asyncio
    async def test_memory_manager_initialization(self, memory_manager):
        """Test memory manager initialization"""
        await memory_manager.initialize()
        
        assert memory_manager.engine is not None
        assert memory_manager.SessionLocal is not None
    
    @pytest.mark.asyncio
    async def test_transient_memory_operations(self, memory_manager):
        """Test transient memory operations"""
        await memory_manager.initialize()
        
        # Store value
        success = await memory_manager.store(
            key="test_key",
            value={"data": "test"},
            memory_type=MemoryType.TRANSIENT,
            scope=MemoryScope.AGENT_PRIVATE,
            owner="test_agent"
        )
        assert success == True
        
        # Retrieve value
        value = await memory_manager.retrieve(
            key="test_key",
            scope=MemoryScope.AGENT_PRIVATE,
            owner="test_agent"
        )
        assert value["data"] == "test"
        
        # Delete value
        deleted = await memory_manager.delete(
            key="test_key",
            scope=MemoryScope.AGENT_PRIVATE,
            owner="test_agent"
        )
        assert deleted == True
        
        # Verify deletion
        value = await memory_manager.retrieve(
            key="test_key",
            scope=MemoryScope.AGENT_PRIVATE,
            owner="test_agent"
        )
        assert value is None
    
    @pytest.mark.asyncio
    async def test_persistent_memory_operations(self, memory_manager):
        """Test persistent memory operations"""
        await memory_manager.initialize()
        
        # Store value
        success = await memory_manager.store(
            key="persistent_key",
            value={"important": "data"},
            memory_type=MemoryType.PERSISTENT,
            scope=MemoryScope.SYSTEM_WIDE,
            owner="system"
        )
        assert success == True
        
        # Retrieve value
        value = await memory_manager.retrieve(
            key="persistent_key",
            scope=MemoryScope.SYSTEM_WIDE,
            owner="system"
        )
        assert value["important"] == "data"
    
    @pytest.mark.asyncio
    async def test_memory_with_ttl(self, memory_manager):
        """Test memory with time-to-live"""
        await memory_manager.initialize()
        
        # Store value with short TTL
        success = await memory_manager.store(
            key="ttl_key",
            value="expires_soon",
            memory_type=MemoryType.TRANSIENT,
            scope=MemoryScope.AGENT_PRIVATE,
            owner="test_agent",
            ttl=1  # 1 second
        )
        assert success == True
        
        # Retrieve immediately
        value = await memory_manager.retrieve(
            key="ttl_key",
            scope=MemoryScope.AGENT_PRIVATE,
            owner="test_agent"
        )
        assert value == "expires_soon"
        
        # Wait for expiration
        await asyncio.sleep(2)
        
        # Should be expired now
        value = await memory_manager.retrieve(
            key="ttl_key",
            scope=MemoryScope.AGENT_PRIVATE,
            owner="test_agent"
        )
        assert value is None
    
    @pytest.mark.asyncio
    async def test_list_keys(self, memory_manager):
        """Test listing keys"""
        await memory_manager.initialize()
        
        # Store multiple values
        await memory_manager.store("key1", "value1", MemoryType.TRANSIENT, MemoryScope.AGENT_PRIVATE, "agent1")
        await memory_manager.store("key2", "value2", MemoryType.TRANSIENT, MemoryScope.AGENT_PRIVATE, "agent1")
        await memory_manager.store("key3", "value3", MemoryType.TRANSIENT, MemoryScope.AGENT_PRIVATE, "agent2")
        
        # List keys for agent1
        keys = await memory_manager.list_keys(MemoryScope.AGENT_PRIVATE, "agent1")
        assert "key1" in keys
        assert "key2" in keys
        assert "key3" not in keys
    
    def test_memory_stats(self, memory_manager):
        """Test memory statistics"""
        stats = memory_manager.get_memory_stats()
        
        assert "transient_items" in stats
        assert "redis_available" in stats
        assert "database_available" in stats
        assert "access_stats" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])