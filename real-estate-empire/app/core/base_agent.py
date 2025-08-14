"""
Base Agent Classes and Interfaces for Real Estate Empire AI System
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
from enum import Enum
import uuid

from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor
from langchain.tools import Tool
from langchain_core.language_models import BaseLanguageModel

from .agent_state import AgentState, AgentType, StateManager, AgentMessage
from .agent_communication import AgentCommunicationProtocol, MessageType, MessagePriority
from .llm_config import llm_manager


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Agent execution status"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


class AgentCapability(BaseModel):
    """Represents a capability that an agent can perform"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    required_tools: List[str] = Field(default_factory=list)
    estimated_duration: Optional[int] = None  # seconds
    confidence_level: float = Field(default=1.0, ge=0.0, le=1.0)


class AgentMetrics(BaseModel):
    """Performance metrics for an agent"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_response_time: float = 0.0
    success_rate: float = 0.0
    uptime_percentage: float = 100.0
    last_activity: Optional[datetime] = None
    error_count: int = 0
    total_tokens_used: int = 0
    estimated_cost: float = 0.0


class AgentMemory(BaseModel):
    """Agent memory and context management"""
    short_term_memory: Dict[str, Any] = Field(default_factory=dict)
    long_term_memory: Dict[str, Any] = Field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    learned_patterns: Dict[str, Any] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    
    def add_to_short_term(self, key: str, value: Any, ttl: Optional[int] = None):
        """Add item to short-term memory with optional TTL"""
        self.short_term_memory[key] = {
            "value": value,
            "timestamp": datetime.now(),
            "ttl": ttl
        }
    
    def add_to_long_term(self, key: str, value: Any):
        """Add item to long-term memory"""
        self.long_term_memory[key] = {
            "value": value,
            "timestamp": datetime.now()
        }
    
    def get_memory(self, key: str, memory_type: str = "short_term") -> Optional[Any]:
        """Retrieve item from memory"""
        memory_store = getattr(self, f"{memory_type}_memory", {})
        item = memory_store.get(key)
        if item:
            # Check TTL for short-term memory
            if memory_type == "short_term" and item.get("ttl"):
                elapsed = (datetime.now() - item["timestamp"]).seconds
                if elapsed > item["ttl"]:
                    del memory_store[key]
                    return None
            return item["value"]
        return None
    
    def clear_short_term(self):
        """Clear short-term memory"""
        self.short_term_memory.clear()


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the Real Estate Empire system
    Provides common functionality and interface for agent implementations
    """
    
    def __init__(
        self,
        agent_type: AgentType,
        name: str,
        description: str,
        capabilities: List[AgentCapability],
        tools: Optional[List[Tool]] = None,
        llm: Optional[BaseLanguageModel] = None
    ):
        self.agent_type = agent_type
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.tools = tools or []
        self.llm = llm or llm_manager.get_llm(agent_type.value)
        
        # Agent state
        self.status = AgentStatus.IDLE
        self.metrics = AgentMetrics()
        self.memory = AgentMemory()
        self.agent_id = str(uuid.uuid4())
        
        # Communication
        self.communication_protocol: Optional[AgentCommunicationProtocol] = None
        self.message_handlers: Dict[MessageType, Callable] = {}
        
        # Lifecycle hooks
        self.lifecycle_hooks: Dict[str, List[Callable]] = {
            "before_execute": [],
            "after_execute": [],
            "on_error": [],
            "on_success": []
        }
        
        # Initialize agent
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the agent with default configurations"""
        logger.info(f"Initializing {self.agent_type.value} agent: {self.name}")
        
        # Set up default message handlers
        self._setup_message_handlers()
        
        # Initialize metrics
        self.metrics.last_activity = datetime.now()
        
        # Add agent-specific initialization
        self._agent_specific_initialization()
    
    @abstractmethod
    def _agent_specific_initialization(self):
        """Agent-specific initialization logic - to be implemented by subclasses"""
        pass
    
    def _setup_message_handlers(self):
        """Set up default message handlers"""
        self.message_handlers = {
            MessageType.TASK_REQUEST: self._handle_task_request,
            MessageType.STATUS_UPDATE: self._handle_status_update,
            MessageType.DATA_SHARE: self._handle_data_share,
            MessageType.COORDINATION: self._handle_coordination,
            MessageType.ALERT: self._handle_alert
        }
    
    # Abstract methods that must be implemented by subclasses
    
    @abstractmethod
    async def execute_task(self, task: str, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """
        Execute a specific task
        
        Args:
            task: Task identifier
            data: Task input data
            state: Current agent state
            
        Returns:
            Task execution result
        """
        pass
    
    @abstractmethod
    async def process_state(self, state: AgentState) -> AgentState:
        """
        Process the current state and return updated state
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        pass
    
    @abstractmethod
    def get_available_tasks(self) -> List[str]:
        """
        Get list of tasks this agent can perform
        
        Returns:
            List of task identifiers
        """
        pass
    
    # Common agent functionality
    
    async def run(self, state: AgentState) -> AgentState:
        """
        Main execution method for the agent
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        try:
            self.status = AgentStatus.RUNNING
            self.metrics.last_activity = datetime.now()
            
            # Execute lifecycle hooks
            await self._execute_hooks("before_execute", state)
            
            # Process the state
            start_time = datetime.now()
            updated_state = await self.process_state(state)
            end_time = datetime.now()
            
            # Update metrics
            execution_time = (end_time - start_time).total_seconds()
            self._update_metrics(execution_time, success=True)
            
            # Execute success hooks
            await self._execute_hooks("after_execute", updated_state)
            await self._execute_hooks("on_success", updated_state)
            
            self.status = AgentStatus.IDLE
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in {self.name} agent execution: {e}")
            self.status = AgentStatus.ERROR
            self.metrics.error_count += 1
            self.metrics.tasks_failed += 1
            
            # Execute error hooks
            await self._execute_hooks("on_error", state, error=e)
            
            # Add error message to state
            error_state = StateManager.add_agent_message(
                state,
                self.agent_type,
                f"Agent execution failed: {str(e)}",
                data={"error": str(e), "agent_id": self.agent_id},
                priority=4
            )
            
            return error_state
    
    def _update_metrics(self, execution_time: float, success: bool = True):
        """Update agent performance metrics"""
        if success:
            self.metrics.tasks_completed += 1
        else:
            self.metrics.tasks_failed += 1
        
        # Update average response time
        total_tasks = self.metrics.tasks_completed + self.metrics.tasks_failed
        if total_tasks > 0:
            current_avg = self.metrics.average_response_time
            self.metrics.average_response_time = (
                (current_avg * (total_tasks - 1) + execution_time) / total_tasks
            )
            
            # Update success rate
            self.metrics.success_rate = self.metrics.tasks_completed / total_tasks
    
    async def _execute_hooks(self, hook_type: str, state: AgentState, **kwargs):
        """Execute lifecycle hooks"""
        hooks = self.lifecycle_hooks.get(hook_type, [])
        for hook in hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(self, state, **kwargs)
                else:
                    hook(self, state, **kwargs)
            except Exception as e:
                logger.error(f"Error executing {hook_type} hook: {e}")
    
    def add_lifecycle_hook(self, hook_type: str, hook_func: Callable):
        """Add a lifecycle hook"""
        if hook_type in self.lifecycle_hooks:
            self.lifecycle_hooks[hook_type].append(hook_func)
        else:
            logger.warning(f"Unknown hook type: {hook_type}")
    
    # Communication methods
    
    def set_communication_protocol(self, protocol: AgentCommunicationProtocol):
        """Set the communication protocol for this agent"""
        self.communication_protocol = protocol
        protocol.register_agent(self.name, {
            "type": self.agent_type.value,
            "capabilities": [cap.name for cap in self.capabilities],
            "agent_id": self.agent_id
        })
    
    async def send_message(self, recipient: str, message_type: MessageType, 
                          content: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL):
        """Send a message to another agent"""
        if not self.communication_protocol:
            logger.warning(f"No communication protocol set for {self.name}")
            return
        
        if message_type == MessageType.TASK_REQUEST:
            await self.communication_protocol.send_task_request(
                self.name, recipient, content.get("task", ""), content, priority
            )
        elif message_type == MessageType.DATA_SHARE:
            await self.communication_protocol.share_data(
                self.name, recipient, content.get("data_type", ""), content, priority
            )
        elif message_type == MessageType.ALERT:
            await self.communication_protocol.send_alert(
                self.name, recipient, content.get("alert_type", ""), 
                content.get("message", ""), content, priority
            )
    
    # Message handlers
    
    async def _handle_task_request(self, message: AgentMessage):
        """Handle incoming task request"""
        try:
            task = message.content.get("task")
            data = message.content.get("data", {})
            
            if task in self.get_available_tasks():
                # Create a minimal state for task execution
                temp_state = StateManager.create_initial_state()
                result = await self.execute_task(task, data, temp_state)
                
                # Send response
                if self.communication_protocol and message.requires_response:
                    await self.communication_protocol.send_task_response(
                        self.name, message.sender, message.correlation_id, result, True
                    )
            else:
                logger.warning(f"Task '{task}' not supported by {self.name}")
                
        except Exception as e:
            logger.error(f"Error handling task request in {self.name}: {e}")
    
    async def _handle_status_update(self, message: AgentMessage):
        """Handle status update from another agent"""
        status = message.content.get("status")
        logger.info(f"{self.name} received status update from {message.sender}: {status}")
        
        # Store in memory for context
        self.memory.add_to_short_term(f"status_{message.sender}", status, ttl=300)
    
    async def _handle_data_share(self, message: AgentMessage):
        """Handle data sharing from another agent"""
        data_type = message.content.get("data_type")
        data = message.content.get("data")
        
        logger.info(f"{self.name} received data share from {message.sender}: {data_type}")
        
        # Store in memory
        self.memory.add_to_short_term(f"shared_data_{data_type}", data, ttl=600)
    
    async def _handle_coordination(self, message: AgentMessage):
        """Handle coordination request"""
        coordination_type = message.content.get("coordination_type")
        logger.info(f"{self.name} received coordination request: {coordination_type}")
        
        # Default coordination response
        if self.communication_protocol and message.requires_response:
            await self.communication_protocol.send_task_response(
                self.name, message.sender, message.correlation_id, 
                {"status": "acknowledged", "agent": self.name}, True
            )
    
    async def _handle_alert(self, message: AgentMessage):
        """Handle alert message"""
        alert_type = message.content.get("alert_type")
        alert_message = message.content.get("message")
        
        logger.warning(f"{self.name} received alert from {message.sender}: {alert_type} - {alert_message}")
        
        # Store alert in memory
        self.memory.add_to_short_term(f"alert_{alert_type}", {
            "sender": message.sender,
            "message": alert_message,
            "timestamp": message.timestamp
        }, ttl=3600)
    
    # Utility methods
    
    def get_capability(self, name: str) -> Optional[AgentCapability]:
        """Get a specific capability by name"""
        for capability in self.capabilities:
            if capability.name == name:
                return capability
        return None
    
    def has_capability(self, name: str) -> bool:
        """Check if agent has a specific capability"""
        return self.get_capability(name) is not None
    
    def get_metrics(self) -> AgentMetrics:
        """Get current agent metrics"""
        return self.metrics
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of agent memory"""
        return {
            "short_term_items": len(self.memory.short_term_memory),
            "long_term_items": len(self.memory.long_term_memory),
            "conversation_history_length": len(self.memory.conversation_history),
            "learned_patterns": len(self.memory.learned_patterns)
        }
    
    def reset_metrics(self):
        """Reset agent metrics"""
        self.metrics = AgentMetrics()
        self.metrics.last_activity = datetime.now()
    
    def __str__(self) -> str:
        return f"{self.agent_type.value}Agent({self.name})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}' type='{self.agent_type.value}' status='{self.status.value}'>"


class AgentLifecycleManager:
    """Manages the lifecycle of agents in the system"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_groups: Dict[str, List[str]] = {}
        self.communication_protocol = AgentCommunicationProtocol()
    
    async def initialize(self):
        """Initialize the lifecycle manager"""
        await self.communication_protocol.initialize()
    
    def register_agent(self, agent: BaseAgent, group: Optional[str] = None):
        """Register an agent with the lifecycle manager"""
        self.agents[agent.name] = agent
        agent.set_communication_protocol(self.communication_protocol)
        
        if group:
            if group not in self.agent_groups:
                self.agent_groups[group] = []
            self.agent_groups[group].append(agent.name)
        
        logger.info(f"Registered agent: {agent.name} ({agent.agent_type.value})")
    
    def unregister_agent(self, agent_name: str):
        """Unregister an agent"""
        if agent_name in self.agents:
            agent = self.agents[agent_name]
            agent.status = AgentStatus.STOPPED
            del self.agents[agent_name]
            
            # Remove from groups
            for group_agents in self.agent_groups.values():
                if agent_name in group_agents:
                    group_agents.remove(agent_name)
            
            logger.info(f"Unregistered agent: {agent_name}")
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Get an agent by name"""
        return self.agents.get(agent_name)
    
    def get_agents_by_type(self, agent_type: AgentType) -> List[BaseAgent]:
        """Get all agents of a specific type"""
        return [agent for agent in self.agents.values() if agent.agent_type == agent_type]
    
    def get_agents_by_group(self, group: str) -> List[BaseAgent]:
        """Get all agents in a specific group"""
        agent_names = self.agent_groups.get(group, [])
        return [self.agents[name] for name in agent_names if name in self.agents]
    
    def get_agent_status_summary(self) -> Dict[str, Any]:
        """Get a summary of all agent statuses"""
        summary = {
            "total_agents": len(self.agents),
            "by_status": {},
            "by_type": {},
            "active_agents": []
        }
        
        for agent in self.agents.values():
            # Count by status
            status = agent.status.value
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            # Count by type
            agent_type = agent.agent_type.value
            summary["by_type"][agent_type] = summary["by_type"].get(agent_type, 0) + 1
            
            # Track active agents
            if agent.status in [AgentStatus.RUNNING, AgentStatus.IDLE]:
                summary["active_agents"].append({
                    "name": agent.name,
                    "type": agent_type,
                    "status": status,
                    "last_activity": agent.metrics.last_activity
                })
        
        return summary
    
    async def broadcast_message(self, sender: str, message_type: MessageType, 
                              content: Dict[str, Any], exclude: Optional[List[str]] = None):
        """Broadcast a message to all agents"""
        exclude = exclude or []
        
        for agent_name in self.agents:
            if agent_name != sender and agent_name not in exclude:
                agent = self.agents[agent_name]
                await agent.send_message(agent_name, message_type, content)
    
    async def shutdown_all_agents(self):
        """Shutdown all agents gracefully"""
        logger.info("Shutting down all agents...")
        
        for agent in self.agents.values():
            agent.status = AgentStatus.STOPPED
        
        self.agents.clear()
        self.agent_groups.clear()
        
        logger.info("All agents shut down")


# Global agent lifecycle manager
agent_lifecycle_manager = AgentLifecycleManager()