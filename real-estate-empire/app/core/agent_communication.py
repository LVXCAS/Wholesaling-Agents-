"""
Agent Communication Protocols and Message Passing System
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
import uuid

# import aioredis  # Temporarily disabled due to Python 3.13 compatibility
import redis
from pydantic import BaseModel


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Types of messages between agents"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    DATA_SHARE = "data_share"
    ALERT = "alert"
    COORDINATION = "coordination"
    ESCALATION = "escalation"


class MessagePriority(int, Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class AgentMessage:
    """Message structure for agent communication"""
    id: str
    sender: str
    recipient: str
    message_type: MessageType
    priority: MessagePriority
    content: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None
    requires_response: bool = False
    expires_at: Optional[datetime] = None


class MessageBus:
    """In-memory message bus for agent communication (simplified for testing)"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.subscribers: Dict[str, List[Callable]] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.message_history: Dict[str, List[AgentMessage]] = {}
        self.messages: Dict[str, AgentMessage] = {}
        
    async def initialize(self):
        """Initialize the message bus"""
        try:
            logger.info("Message bus initialized successfully (in-memory mode)")
        except Exception as e:
            logger.error(f"Failed to initialize message bus: {e}")
            raise e
    
    async def publish_message(self, message: AgentMessage) -> bool:
        """Publish a message to the bus"""
        try:
            # Store message
            self.messages[message.id] = message
            
            # Add to recipient's history
            if message.recipient not in self.message_history:
                self.message_history[message.recipient] = []
            self.message_history[message.recipient].append(message)
            
            # Call subscribers if any
            if message.recipient in self.subscribers:
                for handler in self.subscribers[message.recipient]:
                    try:
                        await handler(message)
                    except Exception as e:
                        logger.error(f"Handler error for {message.recipient}: {e}")
            
            logger.debug(f"Published message {message.id} from {message.sender} to {message.recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return False
    
    async def subscribe_to_agent(self, agent_name: str, handler: Callable):
        """Subscribe to messages for a specific agent"""
        try:
            # Store handler
            if agent_name not in self.subscribers:
                self.subscribers[agent_name] = []
            self.subscribers[agent_name].append(handler)
            
            logger.info(f"Subscribed to messages for agent: {agent_name}")
            
        except Exception as e:
            logger.error(f"Failed to subscribe to agent {agent_name}: {e}")
    
    def _deserialize_message(self, data: Dict[str, Any]) -> AgentMessage:
        """Deserialize message data"""
        return AgentMessage(
            id=data["id"],
            sender=data["sender"],
            recipient=data["recipient"],
            message_type=MessageType(data["message_type"]),
            priority=MessagePriority(data["priority"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            correlation_id=data.get("correlation_id"),
            requires_response=data.get("requires_response", False),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
        )
    
    async def get_message_history(self, agent_name: str, limit: int = 100) -> List[AgentMessage]:
        """Get message history for an agent"""
        try:
            messages = self.message_history.get(agent_name, [])
            return messages[-limit:] if len(messages) > limit else messages
            
        except Exception as e:
            logger.error(f"Failed to get message history for {agent_name}: {e}")
            return []


class AgentCommunicationProtocol:
    """High-level communication protocol for agents"""
    
    def __init__(self):
        self.message_bus = MessageBus()
        self.agent_registry: Dict[str, Dict[str, Any]] = {}
        self.response_handlers: Dict[str, Callable] = {}
        
    async def initialize(self):
        """Initialize the communication protocol"""
        await self.message_bus.initialize()
        logger.info("Agent communication protocol initialized")
    
    def register_agent(self, agent_name: str, agent_info: Dict[str, Any]):
        """Register an agent in the system"""
        self.agent_registry[agent_name] = {
            "name": agent_name,
            "registered_at": datetime.now(),
            "status": "active",
            **agent_info
        }
        logger.info(f"Registered agent: {agent_name}")
    
    async def send_task_request(self, sender: str, recipient: str, task: str, 
                              data: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """Send a task request to another agent"""
        message_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())
        
        message = AgentMessage(
            id=message_id,
            sender=sender,
            recipient=recipient,
            message_type=MessageType.TASK_REQUEST,
            priority=priority,
            content={
                "task": task,
                "data": data,
                "requested_at": datetime.now().isoformat()
            },
            timestamp=datetime.now(),
            correlation_id=correlation_id,
            requires_response=True
        )
        
        success = await self.message_bus.publish_message(message)
        if success:
            logger.info(f"Task request sent: {sender} -> {recipient} ({task})")
            return correlation_id
        else:
            raise Exception("Failed to send task request")
    
    async def send_task_response(self, sender: str, recipient: str, correlation_id: str,
                               result: Dict[str, Any], success: bool = True):
        """Send a task response"""
        message_id = str(uuid.uuid4())
        
        message = AgentMessage(
            id=message_id,
            sender=sender,
            recipient=recipient,
            message_type=MessageType.TASK_RESPONSE,
            priority=MessagePriority.NORMAL,
            content={
                "success": success,
                "result": result,
                "completed_at": datetime.now().isoformat()
            },
            timestamp=datetime.now(),
            correlation_id=correlation_id,
            requires_response=False
        )
        
        await self.message_bus.publish_message(message)
        logger.info(f"Task response sent: {sender} -> {recipient}")
    
    async def send_status_update(self, sender: str, status: str, data: Optional[Dict[str, Any]] = None):
        """Broadcast status update to all agents"""
        message_id = str(uuid.uuid4())
        
        message = AgentMessage(
            id=message_id,
            sender=sender,
            recipient="broadcast",
            message_type=MessageType.STATUS_UPDATE,
            priority=MessagePriority.LOW,
            content={
                "status": status,
                "data": data or {},
                "timestamp": datetime.now().isoformat()
            },
            timestamp=datetime.now(),
            requires_response=False
        )
        
        # Send to all registered agents
        for agent_name in self.agent_registry.keys():
            if agent_name != sender:
                message.recipient = agent_name
                await self.message_bus.publish_message(message)
        
        logger.info(f"Status update broadcast from {sender}: {status}")
    
    async def send_alert(self, sender: str, recipient: str, alert_type: str, 
                        message: str, data: Optional[Dict[str, Any]] = None,
                        priority: MessagePriority = MessagePriority.HIGH):
        """Send an alert message"""
        message_id = str(uuid.uuid4())
        
        alert_message = AgentMessage(
            id=message_id,
            sender=sender,
            recipient=recipient,
            message_type=MessageType.ALERT,
            priority=priority,
            content={
                "alert_type": alert_type,
                "message": message,
                "data": data or {},
                "timestamp": datetime.now().isoformat()
            },
            timestamp=datetime.now(),
            requires_response=False
        )
        
        await self.message_bus.publish_message(alert_message)
        logger.warning(f"Alert sent: {sender} -> {recipient} ({alert_type})")
    
    async def request_coordination(self, sender: str, recipients: List[str], 
                                 coordination_type: str, data: Dict[str, Any]) -> str:
        """Request coordination between multiple agents"""
        correlation_id = str(uuid.uuid4())
        
        for recipient in recipients:
            message_id = str(uuid.uuid4())
            
            message = AgentMessage(
                id=message_id,
                sender=sender,
                recipient=recipient,
                message_type=MessageType.COORDINATION,
                priority=MessagePriority.HIGH,
                content={
                    "coordination_type": coordination_type,
                    "participants": recipients,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                },
                timestamp=datetime.now(),
                correlation_id=correlation_id,
                requires_response=True
            )
            
            await self.message_bus.publish_message(message)
        
        logger.info(f"Coordination request sent: {sender} -> {recipients} ({coordination_type})")
        return correlation_id
    
    async def escalate_to_human(self, sender: str, issue: str, data: Dict[str, Any],
                              priority: MessagePriority = MessagePriority.CRITICAL):
        """Escalate an issue to human oversight"""
        message_id = str(uuid.uuid4())
        
        message = AgentMessage(
            id=message_id,
            sender=sender,
            recipient="human_supervisor",
            message_type=MessageType.ESCALATION,
            priority=priority,
            content={
                "issue": issue,
                "data": data,
                "escalated_at": datetime.now().isoformat(),
                "requires_human_intervention": True
            },
            timestamp=datetime.now(),
            requires_response=True
        )
        
        await self.message_bus.publish_message(message)
        logger.critical(f"Human escalation: {sender} -> {issue}")
    
    async def share_data(self, sender: str, recipient: str, data_type: str, 
                        data: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL):
        """Share data between agents"""
        message_id = str(uuid.uuid4())
        
        message = AgentMessage(
            id=message_id,
            sender=sender,
            recipient=recipient,
            message_type=MessageType.DATA_SHARE,
            priority=priority,
            content={
                "data_type": data_type,
                "data": data,
                "shared_at": datetime.now().isoformat()
            },
            timestamp=datetime.now(),
            requires_response=False
        )
        
        await self.message_bus.publish_message(message)
        logger.info(f"Data shared: {sender} -> {recipient} ({data_type})")
    
    def get_agent_status(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a registered agent"""
        return self.agent_registry.get(agent_name)
    
    def list_active_agents(self) -> List[str]:
        """List all active agents"""
        return [
            name for name, info in self.agent_registry.items()
            if info.get("status") == "active"
        ]
    
    async def get_communication_stats(self) -> Dict[str, Any]:
        """Get communication statistics"""
        stats = {
            "registered_agents": len(self.agent_registry),
            "active_agents": len(self.list_active_agents()),
            "message_types": {mt.value: 0 for mt in MessageType},
            "priority_distribution": {mp.value: 0 for mp in MessagePriority}
        }
        
        # This would be enhanced with actual message statistics from Redis
        return stats


# Global communication protocol instance
communication_protocol = AgentCommunicationProtocol()