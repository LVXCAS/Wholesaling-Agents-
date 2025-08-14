"""
Negotiator Agent Workflows - Communication and Negotiation Workflows
Specialized workflows for the Negotiator Agent to manage outreach campaigns, 
response handling, and negotiation processes
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json

from pydantic import BaseModel, Field

from ..core.agent_state import AgentState, Deal, DealStatus, Negotiation, StateManager
from .negotiator_agent import (
    CommunicationChannel, OutreachCampaign, CommunicationHistory, 
    NegotiationStrategy, ResponseAnalysis
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep(BaseModel):
    """Individual workflow step"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    step_type: str  # communication, analysis, decision, wait
    parameters: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    timeout_minutes: int = 60
    retry_count: int = 0
    max_retries: int = 3
    status: WorkflowStatus = WorkflowStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class WorkflowExecution(BaseModel):
    """Workflow execution tracking"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_name: str
    deal_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    steps: List[WorkflowStep] = Field(default_factory=list)
    current_step_index: int = 0
    context: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_duration_minutes: Optional[float] = None
    success_rate: float = 0.0


class NegotiatorWorkflowEngine:
    """Engine for executing negotiator workflows"""
    
    def __init__(self, negotiator_agent):
        self.negotiator_agent = negotiator_agent
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.workflow_templates: Dict[str, List[WorkflowStep]] = {}
        
        # Initialize workflow templates
        self._initialize_workflow_templates()
    
    def _initialize_workflow_templates(self):
        """Initialize predefined workflow templates"""
        
        # Outreach Campaign Workflow
        self.workflow_templates["outreach_campaign"] = [
            WorkflowStep(
                name="analyze_deal_and_seller",
                description="Analyze deal data and seller profile for campaign planning",
                step_type="analysis",
                parameters={"analysis_type": "campaign_planning"},
                timeout_minutes=30
            ),
            WorkflowStep(
                name="create_campaign_strategy",
                description="Create multi-channel outreach campaign strategy",
                step_type="decision",
                parameters={"strategy_type": "outreach_campaign"},
                dependencies=["analyze_deal_and_seller"],
                timeout_minutes=45
            ),
            WorkflowStep(
                name="generate_initial_messages",
                description="Generate personalized messages for all channels",
                step_type="communication",
                parameters={"message_type": "initial_contact"},
                dependencies=["create_campaign_strategy"],
                timeout_minutes=60
            ),
            WorkflowStep(
                name="send_initial_outreach",
                description="Send initial outreach messages",
                step_type="communication",
                parameters={"action": "send_messages"},
                dependencies=["generate_initial_messages"],
                timeout_minutes=30
            ),
            WorkflowStep(
                name="schedule_follow_ups",
                description="Schedule automated follow-up messages",
                step_type="decision",
                parameters={"action": "schedule_follow_ups"},
                dependencies=["send_initial_outreach"],
                timeout_minutes=15
            )
        ]
        
        # Response Handling Workflow
        self.workflow_templates["response_handling"] = [
            WorkflowStep(
                name="analyze_response",
                description="Analyze seller response for sentiment and intent",
                step_type="analysis",
                parameters={"analysis_type": "response_analysis"},
                timeout_minutes=20
            ),
            WorkflowStep(
                name="determine_response_strategy",
                description="Determine appropriate response strategy",
                step_type="decision",
                parameters={"decision_type": "response_strategy"},
                dependencies=["analyze_response"],
                timeout_minutes=30
            ),
            WorkflowStep(
                name="generate_response",
                description="Generate personalized response message",
                step_type="communication",
                parameters={"message_type": "response"},
                dependencies=["determine_response_strategy"],
                timeout_minutes=45
            ),
            WorkflowStep(
                name="send_response",
                description="Send response to seller",
                step_type="communication",
                parameters={"action": "send_response"},
                dependencies=["generate_response"],
                timeout_minutes=15
            ),
            WorkflowStep(
                name="update_negotiation_status",
                description="Update negotiation tracking and next steps",
                step_type="decision",
                parameters={"action": "update_status"},
                dependencies=["send_response"],
                timeout_minutes=10
            )
        ]
        
        # Negotiation Management Workflow
        self.workflow_templates["negotiation_management"] = [
            WorkflowStep(
                name="assess_negotiation_position",
                description="Assess current negotiation position and seller stance",
                step_type="analysis",
                parameters={"analysis_type": "negotiation_position"},
                timeout_minutes=30
            ),
            WorkflowStep(
                name="develop_negotiation_strategy",
                description="Develop or update negotiation strategy",
                step_type="decision",
                parameters={"strategy_type": "negotiation"},
                dependencies=["assess_negotiation_position"],
                timeout_minutes=45
            ),
            WorkflowStep(
                name="prepare_offer_or_counteroffer",
                description="Prepare offer or counteroffer based on strategy",
                step_type="decision",
                parameters={"action": "prepare_offer"},
                dependencies=["develop_negotiation_strategy"],
                timeout_minutes=60
            ),
            WorkflowStep(
                name="present_offer",
                description="Present offer to seller through appropriate channel",
                step_type="communication",
                parameters={"message_type": "offer_presentation"},
                dependencies=["prepare_offer_or_counteroffer"],
                timeout_minutes=30
            ),
            WorkflowStep(
                name="track_offer_response",
                description="Track and monitor seller response to offer",
                step_type="analysis",
                parameters={"tracking_type": "offer_response"},
                dependencies=["present_offer"],
                timeout_minutes=1440  # 24 hours
            )
        ]
        
        # Follow-up and Nurturing Workflow
        self.workflow_templates["follow_up_nurturing"] = [
            WorkflowStep(
                name="assess_follow_up_timing",
                description="Determine optimal follow-up timing based on previous interactions",
                step_type="analysis",
                parameters={"analysis_type": "follow_up_timing"},
                timeout_minutes=15
            ),
            WorkflowStep(
                name="select_follow_up_channel",
                description="Select most effective communication channel for follow-up",
                step_type="decision",
                parameters={"decision_type": "channel_selection"},
                dependencies=["assess_follow_up_timing"],
                timeout_minutes=10
            ),
            WorkflowStep(
                name="generate_follow_up_message",
                description="Generate personalized follow-up message",
                step_type="communication",
                parameters={"message_type": "follow_up"},
                dependencies=["select_follow_up_channel"],
                timeout_minutes=30
            ),
            WorkflowStep(
                name="send_follow_up",
                description="Send follow-up message to seller",
                step_type="communication",
                parameters={"action": "send_follow_up"},
                dependencies=["generate_follow_up_message"],
                timeout_minutes=15
            ),
            WorkflowStep(
                name="schedule_next_follow_up",
                description="Schedule next follow-up if no response",
                step_type="decision",
                parameters={"action": "schedule_next"},
                dependencies=["send_follow_up"],
                timeout_minutes=10
            )
        ]
        
        # Relationship Management Workflow
        self.workflow_templates["relationship_management"] = [
            WorkflowStep(
                name="analyze_relationship_status",
                description="Analyze current relationship status with seller",
                step_type="analysis",
                parameters={"analysis_type": "relationship_status"},
                timeout_minutes=20
            ),
            WorkflowStep(
                name="identify_relationship_opportunities",
                description="Identify opportunities to strengthen relationship",
                step_type="decision",
                parameters={"decision_type": "relationship_opportunities"},
                dependencies=["analyze_relationship_status"],
                timeout_minutes=30
            ),
            WorkflowStep(
                name="create_relationship_building_plan",
                description="Create plan for building stronger relationship",
                step_type="decision",
                parameters={"plan_type": "relationship_building"},
                dependencies=["identify_relationship_opportunities"],
                timeout_minutes=45
            ),
            WorkflowStep(
                name="execute_relationship_activities",
                description="Execute relationship building activities",
                step_type="communication",
                parameters={"activity_type": "relationship_building"},
                dependencies=["create_relationship_building_plan"],
                timeout_minutes=60
            ),
            WorkflowStep(
                name="monitor_relationship_progress",
                description="Monitor progress of relationship building efforts",
                step_type="analysis",
                parameters={"monitoring_type": "relationship_progress"},
                dependencies=["execute_relationship_activities"],
                timeout_minutes=30
            )
        ]
        
        logger.info(f"Initialized {len(self.workflow_templates)} workflow templates")
    
    async def start_workflow(self, workflow_name: str, deal_id: str, context: Dict[str, Any] = None) -> str:
        """Start a new workflow execution"""
        if workflow_name not in self.workflow_templates:
            raise ValueError(f"Unknown workflow: {workflow_name}")
        
        # Create workflow execution
        execution = WorkflowExecution(
            workflow_name=workflow_name,
            deal_id=deal_id,
            steps=[step.copy() for step in self.workflow_templates[workflow_name]],
            context=context or {},
            started_at=datetime.now()
        )
        
        # Store execution
        self.active_executions[execution.id] = execution
        
        # Start execution
        asyncio.create_task(self._execute_workflow(execution.id))
        
        logger.info(f"Started workflow '{workflow_name}' for deal {deal_id} (execution: {execution.id})")
        return execution.id
    
    async def _execute_workflow(self, execution_id: str):
        """Execute a workflow"""
        execution = self.active_executions.get(execution_id)
        if not execution:
            logger.error(f"Workflow execution not found: {execution_id}")
            return
        
        try:
            execution.status = WorkflowStatus.RUNNING
            
            while execution.current_step_index < len(execution.steps):
                current_step = execution.steps[execution.current_step_index]
                
                # Check dependencies
                if not await self._check_dependencies(execution, current_step):
                    logger.warning(f"Dependencies not met for step {current_step.name}")
                    await asyncio.sleep(60)  # Wait and retry
                    continue
                
                # Execute step
                success = await self._execute_step(execution, current_step)
                
                if success:
                    execution.current_step_index += 1
                else:
                    # Handle step failure
                    if current_step.retry_count < current_step.max_retries:
                        current_step.retry_count += 1
                        logger.info(f"Retrying step {current_step.name} (attempt {current_step.retry_count})")
                        await asyncio.sleep(30)  # Wait before retry
                    else:
                        logger.error(f"Step {current_step.name} failed after {current_step.max_retries} retries")
                        execution.status = WorkflowStatus.FAILED
                        break
            
            # Complete workflow if all steps succeeded
            if execution.current_step_index >= len(execution.steps):
                execution.status = WorkflowStatus.COMPLETED
                execution.completed_at = datetime.now()
                
                if execution.started_at:
                    duration = execution.completed_at - execution.started_at
                    execution.total_duration_minutes = duration.total_seconds() / 60
                
                # Calculate success rate
                successful_steps = sum(1 for step in execution.steps if step.status == WorkflowStatus.COMPLETED)
                execution.success_rate = successful_steps / len(execution.steps)
                
                logger.info(f"Workflow {execution.workflow_name} completed successfully (execution: {execution_id})")
        
        except Exception as e:
            logger.error(f"Error executing workflow {execution_id}: {e}")
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
    
    async def _check_dependencies(self, execution: WorkflowExecution, step: WorkflowStep) -> bool:
        """Check if step dependencies are satisfied"""
        if not step.dependencies:
            return True
        
        for dep_name in step.dependencies:
            dep_step = next((s for s in execution.steps if s.name == dep_name), None)
            if not dep_step or dep_step.status != WorkflowStatus.COMPLETED:
                return False
        
        return True
    
    async def _execute_step(self, execution: WorkflowExecution, step: WorkflowStep) -> bool:
        """Execute a single workflow step"""
        logger.info(f"Executing step: {step.name} for workflow {execution.id}")
        
        try:
            step.status = WorkflowStatus.RUNNING
            step.started_at = datetime.now()
            
            # Execute step based on type
            if step.step_type == "analysis":
                result = await self._execute_analysis_step(execution, step)
            elif step.step_type == "communication":
                result = await self._execute_communication_step(execution, step)
            elif step.step_type == "decision":
                result = await self._execute_decision_step(execution, step)
            elif step.step_type == "wait":
                result = await self._execute_wait_step(execution, step)
            else:
                raise ValueError(f"Unknown step type: {step.step_type}")
            
            # Store result and mark as completed
            step.result = result
            step.status = WorkflowStatus.COMPLETED
            step.completed_at = datetime.now()
            
            # Update execution context with step result
            execution.context[f"step_{step.name}_result"] = result
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing step {step.name}: {e}")
            step.status = WorkflowStatus.FAILED
            step.error = str(e)
            step.completed_at = datetime.now()
            return False
    
    async def _execute_analysis_step(self, execution: WorkflowExecution, step: WorkflowStep) -> Dict[str, Any]:
        """Execute an analysis step"""
        analysis_type = step.parameters.get("analysis_type")
        
        if analysis_type == "campaign_planning":
            return await self._analyze_for_campaign_planning(execution)
        elif analysis_type == "response_analysis":
            return await self._analyze_response(execution)
        elif analysis_type == "negotiation_position":
            return await self._analyze_negotiation_position(execution)
        elif analysis_type == "follow_up_timing":
            return await self._analyze_follow_up_timing(execution)
        elif analysis_type == "relationship_status":
            return await self._analyze_relationship_status(execution)
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
    
    async def _execute_communication_step(self, execution: WorkflowExecution, step: WorkflowStep) -> Dict[str, Any]:
        """Execute a communication step"""
        action = step.parameters.get("action")
        message_type = step.parameters.get("message_type")
        
        if action == "send_messages":
            return await self._send_initial_messages(execution)
        elif action == "send_response":
            return await self._send_response(execution)
        elif action == "send_follow_up":
            return await self._send_follow_up(execution)
        elif message_type == "initial_contact":
            return await self._generate_initial_messages(execution)
        elif message_type == "response":
            return await self._generate_response_message(execution)
        elif message_type == "follow_up":
            return await self._generate_follow_up_message(execution)
        elif message_type == "offer_presentation":
            return await self._present_offer(execution)
        else:
            raise ValueError(f"Unknown communication action/type: {action or message_type}")
    
    async def _execute_decision_step(self, execution: WorkflowExecution, step: WorkflowStep) -> Dict[str, Any]:
        """Execute a decision step"""
        decision_type = step.parameters.get("decision_type")
        strategy_type = step.parameters.get("strategy_type")
        action = step.parameters.get("action")
        
        if strategy_type == "outreach_campaign":
            return await self._create_campaign_strategy(execution)
        elif strategy_type == "negotiation":
            return await self._develop_negotiation_strategy(execution)
        elif decision_type == "response_strategy":
            return await self._determine_response_strategy(execution)
        elif decision_type == "channel_selection":
            return await self._select_communication_channel(execution)
        elif action == "schedule_follow_ups":
            return await self._schedule_follow_ups(execution)
        elif action == "update_status":
            return await self._update_negotiation_status(execution)
        elif action == "prepare_offer":
            return await self._prepare_offer(execution)
        else:
            raise ValueError(f"Unknown decision type/action: {decision_type or strategy_type or action}")
    
    async def _execute_wait_step(self, execution: WorkflowExecution, step: WorkflowStep) -> Dict[str, Any]:
        """Execute a wait step"""
        wait_minutes = step.parameters.get("wait_minutes", 60)
        await asyncio.sleep(wait_minutes * 60)
        
        return {
            "waited_minutes": wait_minutes,
            "completed_at": datetime.now().isoformat()
        }
    
    # Analysis Step Implementations
    
    async def _analyze_for_campaign_planning(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Analyze deal and seller for campaign planning"""
        deal_id = execution.deal_id
        
        # This would integrate with the negotiator agent's analysis capabilities
        analysis_result = await self.negotiator_agent.execute_task(
            "analyze_deal_for_campaign",
            {"deal_id": deal_id},
            {}  # Empty state for now
        )
        
        return {
            "deal_analysis": analysis_result.get("deal_analysis", {}),
            "seller_profile": analysis_result.get("seller_profile", {}),
            "recommended_channels": analysis_result.get("recommended_channels", ["email", "sms"]),
            "motivation_level": analysis_result.get("motivation_level", 0.5),
            "urgency_level": analysis_result.get("urgency_level", 0.3)
        }
    
    async def _analyze_response(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Analyze seller response"""
        latest_communication = execution.context.get("latest_communication", {})
        
        if not latest_communication:
            return {"error": "No communication to analyze"}
        
        analysis_result = await self.negotiator_agent.execute_task(
            "analyze_response",
            {"communication": latest_communication},
            {}
        )
        
        return analysis_result
    
    async def _analyze_negotiation_position(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Analyze current negotiation position"""
        deal_id = execution.deal_id
        
        return {
            "current_position": "initial_contact",
            "seller_interest_level": 0.6,
            "negotiation_leverage": 0.7,
            "market_position": "favorable",
            "recommended_approach": "collaborative"
        }
    
    async def _analyze_follow_up_timing(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Analyze optimal follow-up timing"""
        last_contact = execution.context.get("last_contact_time")
        response_history = execution.context.get("response_history", [])
        
        # Calculate optimal timing based on response patterns
        if not response_history:
            recommended_hours = 24  # Default 24 hours for first follow-up
        else:
            # Analyze response patterns to optimize timing
            avg_response_time = sum(r.get("response_time_hours", 24) for r in response_history) / len(response_history)
            recommended_hours = min(72, max(6, avg_response_time * 1.5))
        
        return {
            "recommended_follow_up_hours": recommended_hours,
            "optimal_time_of_day": "10:00 AM",
            "preferred_day_of_week": "Tuesday",
            "urgency_level": execution.context.get("urgency_level", 0.3)
        }
    
    async def _analyze_relationship_status(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Analyze relationship status with seller"""
        communication_history = execution.context.get("communication_history", [])
        
        # Calculate relationship metrics
        total_interactions = len(communication_history)
        positive_interactions = sum(1 for comm in communication_history 
                                  if comm.get("sentiment_score", 0) > 0.3)
        
        relationship_score = positive_interactions / max(total_interactions, 1)
        
        return {
            "relationship_score": relationship_score,
            "total_interactions": total_interactions,
            "positive_interactions": positive_interactions,
            "trust_level": min(1.0, relationship_score * 1.2),
            "rapport_indicators": ["responsive", "asks_questions"] if relationship_score > 0.6 else []
        }
    
    # Communication Step Implementations
    
    async def _generate_initial_messages(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Generate initial contact messages"""
        campaign_strategy = execution.context.get("step_create_campaign_strategy_result", {})
        
        messages = []
        for channel in campaign_strategy.get("recommended_channels", ["email"]):
            message_result = await self.negotiator_agent.execute_task(
                "generate_message",
                {
                    "deal_id": execution.deal_id,
                    "channel": channel,
                    "purpose": "initial_contact",
                    "context": campaign_strategy
                },
                {}
            )
            
            if message_result.get("success", False):
                messages.append(message_result["message"])
        
        return {
            "generated_messages": messages,
            "message_count": len(messages),
            "channels_covered": [msg.get("channel") for msg in messages]
        }
    
    async def _send_initial_messages(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Send initial outreach messages"""
        messages = execution.context.get("step_generate_initial_messages_result", {}).get("generated_messages", [])
        
        sent_messages = []
        for message in messages:
            # Simulate sending message
            sent_result = {
                "message_id": str(uuid.uuid4()),
                "channel": message.get("channel"),
                "status": "sent",
                "sent_at": datetime.now().isoformat()
            }
            sent_messages.append(sent_result)
        
        return {
            "sent_messages": sent_messages,
            "total_sent": len(sent_messages),
            "campaign_initiated": True
        }
    
    async def _generate_response_message(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Generate response message"""
        response_strategy = execution.context.get("step_determine_response_strategy_result", {})
        
        message_result = await self.negotiator_agent.execute_task(
            "generate_message",
            {
                "deal_id": execution.deal_id,
                "channel": response_strategy.get("recommended_channel", "email"),
                "purpose": "response",
                "context": response_strategy
            },
            {}
        )
        
        return message_result
    
    async def _send_response(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Send response to seller"""
        response_message = execution.context.get("step_generate_response_result", {})
        
        # Simulate sending response
        return {
            "message_id": str(uuid.uuid4()),
            "status": "sent",
            "sent_at": datetime.now().isoformat(),
            "channel": response_message.get("channel", "email")
        }
    
    async def _generate_follow_up_message(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Generate follow-up message"""
        channel_selection = execution.context.get("step_select_follow_up_channel_result", {})
        
        message_result = await self.negotiator_agent.execute_task(
            "generate_message",
            {
                "deal_id": execution.deal_id,
                "channel": channel_selection.get("selected_channel", "email"),
                "purpose": "follow_up",
                "context": execution.context
            },
            {}
        )
        
        return message_result
    
    async def _send_follow_up(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Send follow-up message"""
        follow_up_message = execution.context.get("step_generate_follow_up_message_result", {})
        
        # Simulate sending follow-up
        return {
            "message_id": str(uuid.uuid4()),
            "status": "sent",
            "sent_at": datetime.now().isoformat(),
            "channel": follow_up_message.get("channel", "email"),
            "follow_up_sequence": execution.context.get("follow_up_count", 0) + 1
        }
    
    async def _present_offer(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Present offer to seller"""
        offer_details = execution.context.get("step_prepare_offer_or_counteroffer_result", {})
        
        # Generate offer presentation message
        message_result = await self.negotiator_agent.execute_task(
            "generate_message",
            {
                "deal_id": execution.deal_id,
                "channel": "email",  # Offers typically sent via email
                "purpose": "offer_presentation",
                "context": offer_details
            },
            {}
        )
        
        # Simulate sending offer
        return {
            "offer_id": str(uuid.uuid4()),
            "message_id": str(uuid.uuid4()),
            "status": "sent",
            "sent_at": datetime.now().isoformat(),
            "offer_amount": offer_details.get("offer_amount"),
            "terms": offer_details.get("terms", {})
        }
    
    # Decision Step Implementations
    
    async def _create_campaign_strategy(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Create outreach campaign strategy"""
        deal_analysis = execution.context.get("step_analyze_deal_and_seller_result", {})
        
        strategy_result = await self.negotiator_agent.execute_task(
            "develop_campaign_strategy",
            {
                "deal_id": execution.deal_id,
                "deal_analysis": deal_analysis
            },
            {}
        )
        
        return strategy_result
    
    async def _develop_negotiation_strategy(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Develop negotiation strategy"""
        negotiation_position = execution.context.get("step_assess_negotiation_position_result", {})
        
        strategy_result = await self.negotiator_agent.execute_task(
            "develop_negotiation_strategy",
            {
                "deal_id": execution.deal_id,
                "negotiation_position": negotiation_position
            },
            {}
        )
        
        return strategy_result
    
    async def _determine_response_strategy(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Determine response strategy"""
        response_analysis = execution.context.get("step_analyze_response_result", {})
        
        # Determine strategy based on analysis
        sentiment = response_analysis.get("sentiment", {}).get("score", 0.0)
        interest_level = response_analysis.get("interest_level", 0.5)
        
        if interest_level > 0.7:
            strategy = "immediate_engagement"
            recommended_channel = "phone"
        elif interest_level > 0.4:
            strategy = "informative_follow_up"
            recommended_channel = "email"
        else:
            strategy = "nurture_campaign"
            recommended_channel = "sms"
        
        return {
            "strategy": strategy,
            "recommended_channel": recommended_channel,
            "urgency": "high" if interest_level > 0.7 else "medium",
            "tone": "enthusiastic" if sentiment > 0.3 else "professional"
        }
    
    async def _select_communication_channel(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Select optimal communication channel"""
        timing_analysis = execution.context.get("step_assess_follow_up_timing_result", {})
        communication_history = execution.context.get("communication_history", [])
        
        # Analyze channel effectiveness
        channel_performance = {}
        for comm in communication_history:
            channel = comm.get("channel", "email")
            if channel not in channel_performance:
                channel_performance[channel] = {"sent": 0, "responded": 0}
            
            channel_performance[channel]["sent"] += 1
            if comm.get("responded", False):
                channel_performance[channel]["responded"] += 1
        
        # Select best performing channel
        best_channel = "email"  # Default
        best_rate = 0.0
        
        for channel, perf in channel_performance.items():
            if perf["sent"] > 0:
                response_rate = perf["responded"] / perf["sent"]
                if response_rate > best_rate:
                    best_rate = response_rate
                    best_channel = channel
        
        return {
            "selected_channel": best_channel,
            "response_rate": best_rate,
            "channel_performance": channel_performance,
            "reasoning": f"Selected {best_channel} based on {best_rate:.1%} response rate"
        }
    
    async def _schedule_follow_ups(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Schedule follow-up messages"""
        campaign_strategy = execution.context.get("step_create_campaign_strategy_result", {})
        
        # Create follow-up schedule
        follow_up_schedule = [
            {"delay_hours": 24, "channel": "sms", "message_type": "gentle_follow_up"},
            {"delay_hours": 72, "channel": "email", "message_type": "value_proposition"},
            {"delay_hours": 168, "channel": "phone", "message_type": "final_attempt"}
        ]
        
        return {
            "follow_up_schedule": follow_up_schedule,
            "total_follow_ups": len(follow_up_schedule),
            "campaign_duration_days": 7,
            "auto_scheduling_enabled": True
        }
    
    async def _update_negotiation_status(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Update negotiation status and tracking"""
        response_sent = execution.context.get("step_send_response_result", {})
        
        # Update negotiation tracking
        return {
            "status_updated": True,
            "new_status": "awaiting_response",
            "last_contact": response_sent.get("sent_at"),
            "next_follow_up": (datetime.now() + timedelta(hours=48)).isoformat(),
            "interaction_count": execution.context.get("interaction_count", 0) + 1
        }
    
    async def _prepare_offer(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Prepare offer or counteroffer"""
        negotiation_strategy = execution.context.get("step_develop_negotiation_strategy_result", {})
        
        # Calculate offer based on strategy
        strategy = negotiation_strategy.get("strategy", {})
        offer_percentage = strategy.get("initial_offer_percentage", 0.85)
        
        # This would integrate with property analysis for accurate pricing
        estimated_value = 250000  # Would get from deal data
        offer_amount = estimated_value * offer_percentage
        
        return {
            "offer_amount": offer_amount,
            "offer_percentage": offer_percentage,
            "terms": {
                "closing_timeline": "14 days",
                "inspection_period": "7 days",
                "financing": "cash",
                "contingencies": ["inspection"]
            },
            "strategy_basis": strategy.get("approach", "collaborative"),
            "market_justification": "Based on recent comparable sales and current market conditions"
        }
    
    # Workflow Management Methods
    
    def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a workflow execution"""
        execution = self.active_executions.get(execution_id)
        if not execution:
            return None
        
        return {
            "execution_id": execution_id,
            "workflow_name": execution.workflow_name,
            "deal_id": execution.deal_id,
            "status": execution.status.value,
            "current_step": execution.current_step_index,
            "total_steps": len(execution.steps),
            "progress_percentage": (execution.current_step_index / len(execution.steps)) * 100,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "success_rate": execution.success_rate
        }
    
    def list_active_workflows(self) -> List[Dict[str, Any]]:
        """List all active workflow executions"""
        return [
            self.get_workflow_status(execution_id)
            for execution_id in self.active_executions.keys()
        ]
    
    async def pause_workflow(self, execution_id: str) -> bool:
        """Pause a workflow execution"""
        execution = self.active_executions.get(execution_id)
        if execution and execution.status == WorkflowStatus.RUNNING:
            execution.status = WorkflowStatus.PAUSED
            logger.info(f"Paused workflow execution: {execution_id}")
            return True
        return False
    
    async def resume_workflow(self, execution_id: str) -> bool:
        """Resume a paused workflow execution"""
        execution = self.active_executions.get(execution_id)
        if execution and execution.status == WorkflowStatus.PAUSED:
            execution.status = WorkflowStatus.RUNNING
            asyncio.create_task(self._execute_workflow(execution_id))
            logger.info(f"Resumed workflow execution: {execution_id}")
            return True
        return False
    
    async def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel a workflow execution"""
        execution = self.active_executions.get(execution_id)
        if execution and execution.status in [WorkflowStatus.RUNNING, WorkflowStatus.PAUSED]:
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.now()
            logger.info(f"Cancelled workflow execution: {execution_id}")
            return True
        return False
    
    def cleanup_completed_workflows(self, max_age_hours: int = 24):
        """Clean up completed workflow executions older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        to_remove = []
        for execution_id, execution in self.active_executions.items():
            if (execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED] and
                execution.completed_at and execution.completed_at < cutoff_time):
                to_remove.append(execution_id)
        
        for execution_id in to_remove:
            del self.active_executions[execution_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} completed workflow executions")
        
        return len(to_remove)