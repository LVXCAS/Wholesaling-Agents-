"""
Follow-up management service for creating, scheduling, and tracking follow-up tasks.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid
import asyncio
from sqlalchemy.orm import Session

from ..models.scheduling import (
    FollowUpTask, FollowUpSequence
)
from ..models.communication import CommunicationChannel
from ..core.database import get_db


class FollowUpManagementService:
    """Service for managing follow-up tasks and sequences."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_follow_up_task(
        self,
        title: str,
        assigned_to: uuid.UUID,
        due_date: datetime,
        description: Optional[str] = None,
        contact_id: Optional[uuid.UUID] = None,
        lead_id: Optional[uuid.UUID] = None,
        deal_id: Optional[uuid.UUID] = None,
        property_id: Optional[uuid.UUID] = None,
        priority: str = "normal",
        task_type: str = "general",
        estimated_duration_minutes: Optional[int] = None,
        auto_generated: bool = False,
        trigger_event: Optional[str] = None,
        **kwargs
    ) -> FollowUpTask:
        """Create a new follow-up task."""
        
        task = FollowUpTask(
            id=uuid.uuid4(),
            title=title,
            description=description,
            assigned_to=assigned_to,
            contact_id=contact_id,
            lead_id=lead_id,
            deal_id=deal_id,
            property_id=property_id,
            due_date=due_date,
            priority=priority,
            task_type=task_type,
            estimated_duration_minutes=estimated_duration_minutes,
            auto_generated=auto_generated,
            trigger_event=trigger_event,
            created_at=datetime.utcnow(),
            **kwargs
        )
        
        return task
    
    async def get_follow_up_task(self, task_id: uuid.UUID) -> Optional[FollowUpTask]:
        """Get a follow-up task by ID."""
        # This would query the database for the task
        # For now, returning None as placeholder
        return None
    
    async def update_follow_up_task(
        self,
        task_id: uuid.UUID,
        **updates
    ) -> Optional[FollowUpTask]:
        """Update a follow-up task."""
        task = await self.get_follow_up_task(task_id)
        if not task:
            return None
        
        # Update fields
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        task.updated_at = datetime.utcnow()
        return task
    
    async def complete_follow_up_task(
        self,
        task_id: uuid.UUID,
        notes: Optional[str] = None
    ) -> Optional[FollowUpTask]:
        """Mark a follow-up task as completed."""
        task = await self.get_follow_up_task(task_id)
        if not task:
            return None
        
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        if notes:
            task.notes = notes
        task.updated_at = datetime.utcnow()
        
        # Trigger any follow-up sequences based on completion
        await self.trigger_completion_sequences(task)
        
        return task
    
    async def cancel_follow_up_task(
        self,
        task_id: uuid.UUID,
        reason: Optional[str] = None
    ) -> Optional[FollowUpTask]:
        """Cancel a follow-up task."""
        task = await self.get_follow_up_task(task_id)
        if not task:
            return None
        
        task.status = "cancelled"
        if reason:
            task.notes = f"{task.notes or ''}\nCancelled: {reason}".strip()
        task.updated_at = datetime.utcnow()
        
        return task
    
    async def get_follow_up_tasks(
        self,
        assigned_to: Optional[uuid.UUID] = None,
        contact_id: Optional[uuid.UUID] = None,
        lead_id: Optional[uuid.UUID] = None,
        deal_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        due_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[FollowUpTask]:
        """Get follow-up tasks with filtering options."""
        # This would query the database with filters
        # For now, returning empty list as placeholder
        return []
    
    async def get_overdue_tasks(
        self,
        assigned_to: Optional[uuid.UUID] = None
    ) -> List[FollowUpTask]:
        """Get overdue follow-up tasks."""
        now = datetime.utcnow()
        return await self.get_follow_up_tasks(
            assigned_to=assigned_to,
            status="pending",
            due_before=now
        )
    
    async def get_upcoming_tasks(
        self,
        assigned_to: Optional[uuid.UUID] = None,
        days_ahead: int = 7
    ) -> List[FollowUpTask]:
        """Get upcoming follow-up tasks."""
        now = datetime.utcnow()
        future_date = now + timedelta(days=days_ahead)
        
        return await self.get_follow_up_tasks(
            assigned_to=assigned_to,
            status="pending",
            due_after=now,
            due_before=future_date
        )
    
    async def prioritize_tasks(
        self,
        tasks: List[FollowUpTask]
    ) -> List[FollowUpTask]:
        """Prioritize tasks based on various factors."""
        priority_weights = {
            "urgent": 4,
            "high": 3,
            "normal": 2,
            "low": 1
        }
        
        def calculate_priority_score(task: FollowUpTask) -> float:
            score = priority_weights.get(task.priority, 2)
            
            # Increase score for overdue tasks
            if task.due_date < datetime.utcnow():
                days_overdue = (datetime.utcnow() - task.due_date).days
                score += min(days_overdue * 0.5, 5)  # Cap at +5
            
            # Increase score for tasks due soon
            time_until_due = task.due_date - datetime.utcnow()
            if time_until_due.total_seconds() > 0:
                hours_until_due = time_until_due.total_seconds() / 3600
                if hours_until_due <= 24:
                    score += 2
                elif hours_until_due <= 48:
                    score += 1
            
            # Increase score for certain task types
            if task.task_type in ["call", "meeting"]:
                score += 0.5
            
            return score
        
        # Sort by priority score (highest first)
        return sorted(tasks, key=calculate_priority_score, reverse=True)
    
    async def schedule_follow_up_task(
        self,
        title: str,
        assigned_to: uuid.UUID,
        delay_hours: int,
        contact_id: Optional[uuid.UUID] = None,
        lead_id: Optional[uuid.UUID] = None,
        deal_id: Optional[uuid.UUID] = None,
        **kwargs
    ) -> FollowUpTask:
        """Schedule a follow-up task with a delay."""
        due_date = datetime.utcnow() + timedelta(hours=delay_hours)
        
        return await self.create_follow_up_task(
            title=title,
            assigned_to=assigned_to,
            due_date=due_date,
            contact_id=contact_id,
            lead_id=lead_id,
            deal_id=deal_id,
            auto_generated=True,
            **kwargs
        )
    
    async def create_follow_up_sequence(
        self,
        name: str,
        trigger_event: str,
        steps: List[Dict[str, Any]],
        description: Optional[str] = None,
        trigger_delay_hours: int = 0
    ) -> FollowUpSequence:
        """Create a follow-up sequence template."""
        
        sequence = FollowUpSequence(
            id=uuid.uuid4(),
            name=name,
            description=description,
            trigger_event=trigger_event,
            trigger_delay_hours=trigger_delay_hours,
            steps=steps,
            created_at=datetime.utcnow()
        )
        
        return sequence
    
    async def get_follow_up_sequence(self, sequence_id: uuid.UUID) -> Optional[FollowUpSequence]:
        """Get a follow-up sequence by ID."""
        # This would query the database for the sequence
        # For now, returning None as placeholder
        return None
    
    async def get_follow_up_sequences(
        self,
        trigger_event: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[FollowUpSequence]:
        """Get follow-up sequences with filtering."""
        # This would query the database with filters
        # For now, returning empty list as placeholder
        return []
    
    async def trigger_follow_up_sequence(
        self,
        trigger_event: str,
        assigned_to: uuid.UUID,
        context: Dict[str, Any]
    ) -> List[FollowUpTask]:
        """Trigger follow-up sequences based on an event."""
        sequences = await self.get_follow_up_sequences(
            trigger_event=trigger_event,
            is_active=True
        )
        
        created_tasks = []
        
        for sequence in sequences:
            # Apply initial delay if specified
            base_time = datetime.utcnow() + timedelta(hours=sequence.trigger_delay_hours)
            
            for step in sequence.steps:
                # Calculate due date for this step
                step_delay_hours = step.get("delay_hours", 0)
                due_date = base_time + timedelta(hours=step_delay_hours)
                
                # Create the follow-up task
                task = await self.create_follow_up_task(
                    title=step.get("title", "Follow-up task"),
                    description=step.get("description"),
                    assigned_to=assigned_to,
                    due_date=due_date,
                    priority=step.get("priority", "normal"),
                    task_type=step.get("task_type", "general"),
                    estimated_duration_minutes=step.get("duration_minutes"),
                    auto_generated=True,
                    trigger_event=trigger_event,
                    contact_id=context.get("contact_id"),
                    lead_id=context.get("lead_id"),
                    deal_id=context.get("deal_id"),
                    property_id=context.get("property_id")
                )
                
                created_tasks.append(task)
        
        return created_tasks
    
    async def trigger_completion_sequences(self, completed_task: FollowUpTask) -> List[FollowUpTask]:
        """Trigger sequences based on task completion."""
        if not completed_task.trigger_event:
            return []
        
        # Look for sequences triggered by task completion
        completion_event = f"{completed_task.trigger_event}_completed"
        
        context = {
            "contact_id": completed_task.contact_id,
            "lead_id": completed_task.lead_id,
            "deal_id": completed_task.deal_id,
            "property_id": completed_task.property_id,
            "completed_task_id": completed_task.id
        }
        
        return await self.trigger_follow_up_sequence(
            completion_event,
            completed_task.assigned_to,
            context
        )
    
    async def get_task_effectiveness_metrics(
        self,
        assigned_to: Optional[uuid.UUID] = None,
        task_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get effectiveness metrics for follow-up tasks."""
        
        # This would calculate metrics from database
        # For now, returning sample metrics
        return {
            "total_tasks": 0,
            "completed_tasks": 0,
            "overdue_tasks": 0,
            "completion_rate": 0.0,
            "average_completion_time_hours": 0.0,
            "tasks_by_priority": {
                "urgent": 0,
                "high": 0,
                "normal": 0,
                "low": 0
            },
            "tasks_by_type": {},
            "completion_rate_by_type": {}
        }
    
    async def auto_generate_follow_ups(
        self,
        event_type: str,
        context: Dict[str, Any]
    ) -> List[FollowUpTask]:
        """Auto-generate follow-up tasks based on events."""
        
        # Define common follow-up patterns
        follow_up_patterns = {
            "lead_created": [
                {
                    "title": "Initial contact attempt",
                    "delay_hours": 1,
                    "task_type": "call",
                    "priority": "high",
                    "duration_minutes": 15
                },
                {
                    "title": "Follow-up email if no response",
                    "delay_hours": 24,
                    "task_type": "email",
                    "priority": "normal",
                    "duration_minutes": 10
                },
                {
                    "title": "Second follow-up call",
                    "delay_hours": 72,
                    "task_type": "call",
                    "priority": "normal",
                    "duration_minutes": 15
                }
            ],
            "no_response": [
                {
                    "title": "Try different communication channel",
                    "delay_hours": 48,
                    "task_type": "general",
                    "priority": "normal",
                    "duration_minutes": 10
                },
                {
                    "title": "Research additional contact methods",
                    "delay_hours": 168,  # 1 week
                    "task_type": "research",
                    "priority": "low",
                    "duration_minutes": 30
                }
            ],
            "appointment_completed": [
                {
                    "title": "Send thank you and next steps",
                    "delay_hours": 2,
                    "task_type": "email",
                    "priority": "high",
                    "duration_minutes": 15
                },
                {
                    "title": "Follow up on discussed items",
                    "delay_hours": 24,
                    "task_type": "call",
                    "priority": "normal",
                    "duration_minutes": 20
                }
            ],
            "property_analysis_completed": [
                {
                    "title": "Present analysis to lead",
                    "delay_hours": 4,
                    "task_type": "call",
                    "priority": "high",
                    "duration_minutes": 30
                },
                {
                    "title": "Follow up on analysis feedback",
                    "delay_hours": 48,
                    "task_type": "call",
                    "priority": "normal",
                    "duration_minutes": 15
                }
            ]
        }
        
        pattern = follow_up_patterns.get(event_type, [])
        if not pattern:
            return []
        
        assigned_to = context.get("assigned_to")
        if not assigned_to:
            return []
        
        created_tasks = []
        base_time = datetime.utcnow()
        
        for step in pattern:
            due_date = base_time + timedelta(hours=step["delay_hours"])
            
            task = await self.create_follow_up_task(
                title=step["title"],
                assigned_to=assigned_to,
                due_date=due_date,
                priority=step["priority"],
                task_type=step["task_type"],
                estimated_duration_minutes=step["duration_minutes"],
                auto_generated=True,
                trigger_event=event_type,
                contact_id=context.get("contact_id"),
                lead_id=context.get("lead_id"),
                deal_id=context.get("deal_id"),
                property_id=context.get("property_id")
            )
            
            created_tasks.append(task)
        
        return created_tasks
    
    async def snooze_task(
        self,
        task_id: uuid.UUID,
        snooze_hours: int
    ) -> Optional[FollowUpTask]:
        """Snooze a task by extending its due date."""
        task = await self.get_follow_up_task(task_id)
        if not task:
            return None
        
        task.due_date = task.due_date + timedelta(hours=snooze_hours)
        task.updated_at = datetime.utcnow()
        
        return task
    
    async def bulk_update_tasks(
        self,
        task_ids: List[uuid.UUID],
        updates: Dict[str, Any]
    ) -> List[FollowUpTask]:
        """Bulk update multiple tasks."""
        updated_tasks = []
        
        for task_id in task_ids:
            task = await self.update_follow_up_task(task_id, **updates)
            if task:
                updated_tasks.append(task)
        
        return updated_tasks
    
    async def get_task_statistics(
        self,
        assigned_to: Optional[uuid.UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get task statistics and analytics."""
        
        # This would calculate statistics from database
        # For now, returning sample statistics
        return {
            "total_tasks": 0,
            "pending_tasks": 0,
            "completed_tasks": 0,
            "overdue_tasks": 0,
            "completion_rate": 0.0,
            "average_completion_time_days": 0.0,
            "tasks_by_priority": {
                "urgent": 0,
                "high": 0,
                "normal": 0,
                "low": 0
            },
            "tasks_by_type": {
                "call": 0,
                "email": 0,
                "meeting": 0,
                "research": 0,
                "general": 0
            },
            "productivity_score": 0.0  # Based on completion rate and timeliness
        }