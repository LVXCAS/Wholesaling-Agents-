"""
Conversation management service for tracking and managing multi-channel conversations.
Implements Requirements 3.3, 3.4, and 3.5 for conversation threading and context management.
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from pydantic import BaseModel

from ..models.communication import CommunicationChannel, MessageStatus
from .response_analysis_service import ResponseAnalysisService, ResponseAnalysisResult


class ConversationStatus(str, Enum):
    """Conversation status types."""
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"
    ARCHIVED = "archived"


class ConversationPriority(str, Enum):
    """Conversation priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NextActionType(str, Enum):
    """Types of next actions."""
    RESPOND = "respond"
    FOLLOW_UP = "follow_up"
    SCHEDULE_CALL = "schedule_call"
    SEND_INFORMATION = "send_information"
    ESCALATE = "escalate"
    CLOSE = "close"
    WAIT = "wait"


class ConversationMessage(BaseModel):
    """Individual message in a conversation."""
    id: uuid.UUID
    conversation_id: uuid.UUID
    channel: CommunicationChannel
    direction: str  # "inbound" or "outbound"
    content: str
    subject: Optional[str] = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    timestamp: datetime
    status: MessageStatus = MessageStatus.SENT
    analysis_result: Optional[ResponseAnalysisResult] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationSummary(BaseModel):
    """Summary of a conversation."""
    conversation_id: uuid.UUID
    key_points: List[str] = []
    sentiment_trend: str = "stable"  # "improving", "declining", "stable"
    interest_level: float = 0.5  # 0.0 to 1.0
    main_concerns: List[str] = []
    questions_asked: List[str] = []
    objections_raised: List[str] = []
    commitments_made: List[str] = []
    next_steps: List[str] = []
    last_updated: datetime


class NextAction(BaseModel):
    """Recommended next action for a conversation."""
    id: uuid.UUID
    conversation_id: uuid.UUID
    action_type: NextActionType
    description: str
    priority: ConversationPriority
    due_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    completed: bool = False
    created_at: datetime


class ConversationContext(BaseModel):
    """Context information for a conversation."""
    conversation_id: uuid.UUID
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    property_address: Optional[str] = None
    property_details: Optional[Dict[str, Any]] = None
    lead_source: Optional[str] = None
    tags: List[str] = []
    custom_fields: Optional[Dict[str, Any]] = None
    last_updated: datetime


class Conversation(BaseModel):
    """Complete conversation thread."""
    id: uuid.UUID
    contact_id: Optional[uuid.UUID] = None
    subject: Optional[str] = None
    status: ConversationStatus = ConversationStatus.ACTIVE
    priority: ConversationPriority = ConversationPriority.MEDIUM
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None
    
    messages: List[ConversationMessage] = []
    summary: Optional[ConversationSummary] = None
    context: Optional[ConversationContext] = None
    next_actions: List[NextAction] = []
    
    # Metrics
    message_count: int = 0
    response_time_avg: Optional[float] = None  # Average response time in hours
    channels_used: List[CommunicationChannel] = []


class ConversationManagementService:
    """Service for managing conversations across multiple channels."""
    
    def __init__(self, response_analysis_service: Optional[ResponseAnalysisService] = None):
        """Initialize the conversation management service."""
        self.response_analysis_service = response_analysis_service or ResponseAnalysisService()
        self.conversations: Dict[uuid.UUID, Conversation] = {}
        
    def create_conversation(
        self, 
        contact_id: Optional[uuid.UUID] = None,
        subject: Optional[str] = None,
        context: Optional[ConversationContext] = None
    ) -> Conversation:
        """
        Create a new conversation thread.
        
        Args:
            contact_id: ID of the contact
            subject: Conversation subject
            context: Initial context information
            
        Returns:
            New conversation instance
        """
        conversation_id = uuid.uuid4()
        now = datetime.now()
        
        conversation = Conversation(
            id=conversation_id,
            contact_id=contact_id,
            subject=subject,
            created_at=now,
            updated_at=now,
            context=context or ConversationContext(
                conversation_id=conversation_id,
                last_updated=now
            )
        )
        
        self.conversations[conversation_id] = conversation
        return conversation
    
    def add_message(
        self, 
        conversation_id: uuid.UUID,
        channel: CommunicationChannel,
        direction: str,
        content: str,
        subject: Optional[str] = None,
        sender: Optional[str] = None,
        recipient: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """
        Add a message to a conversation thread.
        
        Args:
            conversation_id: ID of the conversation
            channel: Communication channel
            direction: "inbound" or "outbound"
            content: Message content
            subject: Message subject (for email)
            sender: Sender information
            recipient: Recipient information
            metadata: Additional metadata
            
        Returns:
            Created message instance
        """
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation = self.conversations[conversation_id]
        now = datetime.now()
        
        # Create message
        message = ConversationMessage(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            channel=channel,
            direction=direction,
            content=content,
            subject=subject,
            sender=sender,
            recipient=recipient,
            timestamp=now,
            metadata=metadata
        )
        
        # Analyze inbound messages
        if direction == "inbound":
            analysis = self.response_analysis_service.analyze_response(
                content, channel, context={"conversation_id": str(conversation_id)}
            )
            message.analysis_result = analysis
        
        # Add message to conversation
        conversation.messages.append(message)
        conversation.message_count += 1
        conversation.last_message_at = now
        conversation.updated_at = now
        
        # Update channels used
        if channel not in conversation.channels_used:
            conversation.channels_used.append(channel)
        
        # Update conversation summary and next actions
        self._update_conversation_summary(conversation)
        self._update_next_actions(conversation)
        
        return message
    
    def get_conversation(self, conversation_id: uuid.UUID) -> Optional[Conversation]:
        """Get a conversation by ID."""
        return self.conversations.get(conversation_id)
    
    def get_conversations_by_contact(self, contact_id: uuid.UUID) -> List[Conversation]:
        """Get all conversations for a specific contact."""
        return [
            conv for conv in self.conversations.values()
            if conv.contact_id == contact_id
        ]
    
    def search_conversations(
        self, 
        query: Optional[str] = None,
        status: Optional[ConversationStatus] = None,
        priority: Optional[ConversationPriority] = None,
        channel: Optional[CommunicationChannel] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Conversation]:
        """
        Search conversations based on criteria.
        
        Args:
            query: Text search query
            status: Filter by status
            priority: Filter by priority
            channel: Filter by channel
            date_from: Filter by date range start
            date_to: Filter by date range end
            
        Returns:
            List of matching conversations
        """
        results = []
        
        for conversation in self.conversations.values():
            # Status filter
            if status and conversation.status != status:
                continue
                
            # Priority filter
            if priority and conversation.priority != priority:
                continue
                
            # Channel filter
            if channel and channel not in conversation.channels_used:
                continue
                
            # Date range filter
            if date_from and conversation.created_at < date_from:
                continue
            if date_to and conversation.created_at > date_to:
                continue
                
            # Text search
            if query:
                query_lower = query.lower()
                found = False
                
                # Search in subject
                if conversation.subject and query_lower in conversation.subject.lower():
                    found = True
                
                # Search in messages
                if not found:
                    for message in conversation.messages:
                        if query_lower in message.content.lower():
                            found = True
                            break
                
                # Search in context
                if not found and conversation.context:
                    if (conversation.context.contact_name and 
                        query_lower in conversation.context.contact_name.lower()):
                        found = True
                    elif (conversation.context.property_address and 
                          query_lower in conversation.context.property_address.lower()):
                        found = True
                
                if not found:
                    continue
            
            results.append(conversation)
        
        # Sort by last message date (most recent first)
        results.sort(key=lambda c: c.last_message_at or c.created_at, reverse=True)
        return results
    
    def update_conversation_status(
        self, 
        conversation_id: uuid.UUID, 
        status: ConversationStatus
    ) -> bool:
        """Update conversation status."""
        if conversation_id not in self.conversations:
            return False
        
        conversation = self.conversations[conversation_id]
        conversation.status = status
        conversation.updated_at = datetime.now()
        
        return True
    
    def update_conversation_priority(
        self, 
        conversation_id: uuid.UUID, 
        priority: ConversationPriority
    ) -> bool:
        """Update conversation priority."""
        if conversation_id not in self.conversations:
            return False
        
        conversation = self.conversations[conversation_id]
        conversation.priority = priority
        conversation.updated_at = datetime.now()
        
        return True
    
    def get_conversation_metrics(self, conversation_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get metrics for a conversation."""
        if conversation_id not in self.conversations:
            return None
        
        conversation = self.conversations[conversation_id]
        
        # Calculate response times
        response_times = []
        last_outbound = None
        
        for message in conversation.messages:
            if message.direction == "outbound":
                last_outbound = message.timestamp
            elif message.direction == "inbound" and last_outbound:
                response_time = (message.timestamp - last_outbound).total_seconds() / 3600
                response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else None
        
        # Calculate sentiment trend
        sentiment_scores = []
        for message in conversation.messages:
            if message.analysis_result:
                sentiment_scores.append(message.analysis_result.sentiment_analysis.sentiment_score)
        
        sentiment_trend = "stable"
        if len(sentiment_scores) > 1:
            first_sentiment = sentiment_scores[0]
            last_sentiment = sentiment_scores[-1]
            
            if last_sentiment > first_sentiment + 0.1:
                sentiment_trend = "improving"
            elif last_sentiment < first_sentiment - 0.1:
                sentiment_trend = "declining"
        
        # Calculate interest level
        interest_levels = []
        for message in conversation.messages:
            if message.analysis_result:
                interest_levels.append(message.analysis_result.overall_interest_level)
        
        avg_interest = sum(interest_levels) / len(interest_levels) if interest_levels else 0.5
        
        return {
            "message_count": conversation.message_count,
            "channels_used": len(conversation.channels_used),
            "duration_days": (datetime.now() - conversation.created_at).days,
            "avg_response_time_hours": avg_response_time,
            "sentiment_trend": sentiment_trend,
            "avg_interest_level": avg_interest,
            "last_activity": conversation.last_message_at
        }
    
    def _update_conversation_summary(self, conversation: Conversation) -> None:
        """Update conversation summary based on messages and analysis."""
        if not conversation.messages:
            return
        
        # Initialize or update summary
        if not conversation.summary:
            conversation.summary = ConversationSummary(
                conversation_id=conversation.id,
                last_updated=datetime.now()
            )
        
        summary = conversation.summary
        
        # Extract key information from analyzed messages
        key_points = []
        questions = []
        objections = []
        concerns = []
        
        for message in conversation.messages:
            if message.analysis_result:
                analysis = message.analysis_result
                
                # Extract questions
                questions.extend(analysis.question_extraction.questions)
                
                # Extract objections
                for objection in analysis.objection_analysis.objections_detected:
                    objections.append(objection.value)
                
                # Extract concerns from negative sentiment
                if analysis.sentiment_analysis.sentiment_type.value in ["negative", "very_negative"]:
                    concerns.extend(analysis.sentiment_analysis.key_phrases)
        
        # Update summary fields
        summary.questions_asked = list(set(questions))
        summary.objections_raised = list(set(objections))
        summary.main_concerns = list(set(concerns))
        summary.last_updated = datetime.now()
        
        # Calculate metrics
        metrics = self.get_conversation_metrics(conversation.id)
        if metrics:
            summary.sentiment_trend = metrics["sentiment_trend"]
            summary.interest_level = metrics["avg_interest_level"]
    
    def _update_next_actions(self, conversation: Conversation) -> None:
        """Update next actions based on latest message analysis."""
        if not conversation.messages:
            return
        
        latest_message = conversation.messages[-1]
        
        # Only generate actions for inbound messages
        if latest_message.direction != "inbound" or not latest_message.analysis_result:
            return
        
        analysis = latest_message.analysis_result
        
        # Clear existing incomplete actions
        conversation.next_actions = [
            action for action in conversation.next_actions if action.completed
        ]
        
        # Generate new actions based on analysis
        actions = self._generate_next_actions(conversation, analysis)
        conversation.next_actions.extend(actions)
    
    def _generate_next_actions(
        self, 
        conversation: Conversation, 
        analysis: ResponseAnalysisResult
    ) -> List[NextAction]:
        """Generate next actions based on response analysis."""
        actions = []
        now = datetime.now()
        
        # Determine priority based on urgency and interest
        if analysis.response_urgency.value == "immediate":
            priority = ConversationPriority.URGENT
            due_date = now + timedelta(hours=1)
        elif analysis.response_urgency.value == "high":
            priority = ConversationPriority.HIGH
            due_date = now + timedelta(hours=24)
        elif analysis.response_urgency.value == "medium":
            priority = ConversationPriority.MEDIUM
            due_date = now + timedelta(days=2)
        else:
            priority = ConversationPriority.LOW
            due_date = now + timedelta(days=7)
        
        # Generate actions based on intent and analysis
        if analysis.intent_analysis.primary_intent.value == "interested":
            actions.append(NextAction(
                id=uuid.uuid4(),
                conversation_id=conversation.id,
                action_type=NextActionType.SCHEDULE_CALL,
                description="Schedule a call to discuss the property and next steps",
                priority=ConversationPriority.HIGH,
                due_date=now + timedelta(hours=4),
                context={"interest_level": analysis.overall_interest_level},
                created_at=now
            ))
        
        elif analysis.intent_analysis.primary_intent.value == "wants_to_discuss":
            actions.append(NextAction(
                id=uuid.uuid4(),
                conversation_id=conversation.id,
                action_type=NextActionType.RESPOND,
                description="Respond to schedule discussion",
                priority=priority,
                due_date=due_date,
                created_at=now
            ))
        
        elif analysis.intent_analysis.primary_intent.value == "not_interested":
            actions.append(NextAction(
                id=uuid.uuid4(),
                conversation_id=conversation.id,
                action_type=NextActionType.CLOSE,
                description="Close conversation - contact not interested",
                priority=ConversationPriority.LOW,
                due_date=now + timedelta(days=1),
                created_at=now
            ))
        
        # Actions for questions
        if analysis.question_extraction.questions:
            actions.append(NextAction(
                id=uuid.uuid4(),
                conversation_id=conversation.id,
                action_type=NextActionType.RESPOND,
                description=f"Answer {len(analysis.question_extraction.questions)} questions",
                priority=priority,
                due_date=due_date,
                context={"questions": analysis.question_extraction.questions},
                created_at=now
            ))
        
        # Actions for objections
        if analysis.objection_analysis.objections_detected:
            actions.append(NextAction(
                id=uuid.uuid4(),
                conversation_id=conversation.id,
                action_type=NextActionType.RESPOND,
                description="Address objections and concerns",
                priority=ConversationPriority.HIGH,
                due_date=now + timedelta(hours=12),
                context={"objections": [obj.value for obj in analysis.objection_analysis.objections_detected]},
                created_at=now
            ))
        
        # Default response action if no specific action generated
        if not actions:
            actions.append(NextAction(
                id=uuid.uuid4(),
                conversation_id=conversation.id,
                action_type=NextActionType.RESPOND,
                description="Respond to message",
                priority=priority,
                due_date=due_date,
                created_at=now
            ))
        
        return actions
    
    def complete_action(self, action_id: uuid.UUID) -> bool:
        """Mark an action as completed."""
        for conversation in self.conversations.values():
            for action in conversation.next_actions:
                if action.id == action_id:
                    action.completed = True
                    return True
        return False
    
    def get_pending_actions(
        self, 
        priority: Optional[ConversationPriority] = None,
        overdue_only: bool = False
    ) -> List[NextAction]:
        """Get pending actions across all conversations."""
        actions = []
        now = datetime.now()
        
        for conversation in self.conversations.values():
            for action in conversation.next_actions:
                if action.completed:
                    continue
                
                if priority and action.priority != priority:
                    continue
                
                if overdue_only and (not action.due_date or action.due_date > now):
                    continue
                
                actions.append(action)
        
        # Sort by due date and priority
        actions.sort(key=lambda a: (
            a.due_date or datetime.max,
            {"urgent": 0, "high": 1, "medium": 2, "low": 3}[a.priority.value]
        ))
        
        return actions
    
    def archive_old_conversations(self, days_old: int = 90) -> int:
        """Archive conversations older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        archived_count = 0
        
        for conversation in self.conversations.values():
            if (conversation.status == ConversationStatus.CLOSED and
                conversation.updated_at < cutoff_date):
                conversation.status = ConversationStatus.ARCHIVED
                archived_count += 1
        
        return archived_count


# Utility functions
def merge_conversations(
    service: ConversationManagementService,
    primary_conversation_id: uuid.UUID,
    secondary_conversation_id: uuid.UUID
) -> bool:
    """
    Merge two conversations into one.
    
    Args:
        service: Conversation management service
        primary_conversation_id: ID of conversation to keep
        secondary_conversation_id: ID of conversation to merge into primary
        
    Returns:
        True if successful, False otherwise
    """
    primary = service.get_conversation(primary_conversation_id)
    secondary = service.get_conversation(secondary_conversation_id)
    
    if not primary or not secondary:
        return False
    
    # Merge messages
    primary.messages.extend(secondary.messages)
    primary.messages.sort(key=lambda m: m.timestamp)
    
    # Update counts and metadata
    primary.message_count += secondary.message_count
    primary.channels_used = list(set(primary.channels_used + secondary.channels_used))
    
    # Update timestamps
    if secondary.last_message_at and (
        not primary.last_message_at or 
        secondary.last_message_at > primary.last_message_at
    ):
        primary.last_message_at = secondary.last_message_at
    
    primary.updated_at = datetime.now()
    
    # Merge next actions
    primary.next_actions.extend([
        action for action in secondary.next_actions if not action.completed
    ])
    
    # Remove secondary conversation
    del service.conversations[secondary_conversation_id]
    
    # Update summary
    service._update_conversation_summary(primary)
    
    return True


def get_conversation_analytics(
    service: ConversationManagementService,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Get analytics across all conversations.
    
    Args:
        service: Conversation management service
        date_from: Start date for analysis
        date_to: End date for analysis
        
    Returns:
        Analytics dictionary
    """
    conversations = service.search_conversations(date_from=date_from, date_to=date_to)
    
    if not conversations:
        return {}
    
    # Basic metrics
    total_conversations = len(conversations)
    total_messages = sum(conv.message_count for conv in conversations)
    
    # Status distribution
    status_counts = {}
    for conv in conversations:
        status = conv.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Channel usage
    channel_counts = {}
    for conv in conversations:
        for channel in conv.channels_used:
            channel_name = channel.value
            channel_counts[channel_name] = channel_counts.get(channel_name, 0) + 1
    
    # Response times
    response_times = []
    for conv in conversations:
        metrics = service.get_conversation_metrics(conv.id)
        if metrics and metrics["avg_response_time_hours"]:
            response_times.append(metrics["avg_response_time_hours"])
    
    avg_response_time = sum(response_times) / len(response_times) if response_times else None
    
    # Interest levels
    interest_levels = []
    for conv in conversations:
        metrics = service.get_conversation_metrics(conv.id)
        if metrics:
            interest_levels.append(metrics["avg_interest_level"])
    
    avg_interest = sum(interest_levels) / len(interest_levels) if interest_levels else 0.5
    
    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "avg_messages_per_conversation": total_messages / total_conversations,
        "status_distribution": status_counts,
        "channel_usage": channel_counts,
        "avg_response_time_hours": avg_response_time,
        "avg_interest_level": avg_interest,
        "date_range": {
            "from": date_from.isoformat() if date_from else None,
            "to": date_to.isoformat() if date_to else None
        }
    }