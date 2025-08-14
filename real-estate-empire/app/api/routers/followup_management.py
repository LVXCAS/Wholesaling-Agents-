"""
API router for follow-up management functionality.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...core.database import get_db
from ...models.scheduling import FollowUpTask, FollowUpSequence
from ...services.followup_management_service import FollowUpManagementService


router = APIRouter(prefix="/follow-ups", tags=["follow-ups"])


# Request/Response models
class CreateFollowUpTaskRequest(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: datetime
    contact_id: Optional[uuid.UUID] = None
    lead_id: Optional[uuid.UUID] = None
    deal_id: Optional[uuid.UUID] = None
    property_id: Optional[uuid.UUID] = None
    priority: str = "normal"
    task_type: str = "general"
    estimated_duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    tags: List[str] = []


class UpdateFollowUpTaskRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class CompleteTaskRequest(BaseModel):
    notes: Optional[str] = None


class SnoozeTaskRequest(BaseModel):
    snooze_hours: int


class CreateFollowUpSequenceRequest(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_event: str
    trigger_delay_hours: int = 0
    steps: List[Dict[str, Any]]


class TriggerSequenceRequest(BaseModel):
    trigger_event: str
    context: Dict[str, Any]


class BulkUpdateRequest(BaseModel):
    task_ids: List[uuid.UUID]
    updates: Dict[str, Any]


def get_followup_service(db: Session = Depends(get_db)) -> FollowUpManagementService:
    """Get follow-up management service instance."""
    return FollowUpManagementService(db)


@router.post("/tasks", response_model=FollowUpTask)
async def create_follow_up_task(
    request: CreateFollowUpTaskRequest,
    assigned_to: uuid.UUID = Query(..., description="ID of the user assigned to the task"),
    service: FollowUpManagementService = Depends(get_followup_service)
):
    """Create a new follow-up task."""
    try:
        task = await service.create_follow_up_task(
            title=request.title,
            description=request.description,
            assigned_to=assigned_to,
            due_date=request.due_date,
            contact_id=request.contact_id,
            lead_id=request.lead_id,
            deal_id=request.deal_id,
            property_id=request.property_id,
            priority=request.priority,
            task_type=request.task_type,
            estimated_duration_minutes=request.estimated_duration_minutes,
            notes=request.notes,
            tags=request.tags
        )
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create follow-up task: {str(e)}")


@router.get("/tasks/{task_id}", response_model=FollowUpTask)
async def get_follow_up_task(
    task_id: uuid.UUID,
    service: FollowUpManagementService = Depends(get_followup_service)
):
    """Get a follow-up task by ID."""
    task = await service.get_follow_up_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Follow-up task not found")
    return task


@router.put("/tasks/{task_id}", response_model=FollowUpTask)
async def update_follow_up_task(
    task_id: uuid.UUID,
    request: UpdateFollowUpTaskRequest,
    service: FollowUpManagementService = Depends(get_followup_service)
):
    """Update a follow-up task."""
    updates = request.dict(exclude_unset=True)
    task = await service.update_follow_up_task(task_id, **updates)
    if not task:
        raise HTTPException(status_code=404, detail="Follow-up task not found")
    return task


@router.post("/tasks/{task_id}/complete", response_model=FollowUpTask)
async def complete_follow_up_task(
    task_id: uuid.UUID,
    request: CompleteTaskRequest,
    service: FollowUpManagementService = Depends(get_followup_service)
):
    """Mark a follow-up task as completed."""
    task = await service.complete_follow_up_task(task_id, request.notes)
    if not task:
        raise HTTPException(status_code=404, detail="Follow-up task not found")
    return task


@router.post("/tasks/{task_id}/cancel", response_model=FollowUpTask)
async def cancel_follow_up_task(
    task_id: uuid.UUID,
    reason: Optional[str] = Query(None, description="Cancellation reason"),
    service: FollowUpManagementService = Depends(get_followup_service)
):
    """Cancel a follow-up task."""
    task = await service.cancel_follow_up_task(task_id, reason)
    if not task:
        raise HTTPException(status_code=404, detail="Follow-up task not found")
    return task


@router.post("/tasks/{task_id}/snooze", response_model=FollowUpTask)
async def snooze_follow_up_task(
    task_id: uuid.UUID,
    request: SnoozeTaskRequest,
    service: FollowUpManagementService = Depends(get_followup_service)
):
    """Snooze a follow-up task by extending its due date."""
    task = await service.snooze_task(task_id, request.snooze_hours)
    if not task:
        raise HTTPException(status_code=404, detail="Follow-up task not found")
    return task


@router.get("/tasks", response_model=List[FollowUpTask])
async def get_follow_up_tasks(
    assigned_to: Optional[uuid.UUID] = Query(None, description="Filter by assigned user"),
    contact_id: Optional[uuid.UUID] = Query(None, description="Filter by contact"),
    lead_id: Optional[uuid.UUID] = Query(None, description="Filter by lead"),
    deal_id: Optional[uuid.UUID] = Query(None, description="Filter by deal"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    due_before: Optional[datetime] = Query(None, description="Filter by due date before"),
    due_after: Optional[datetime] = Query(None, description="Filter by due date after"),
    limit: int = Query(100, description="Maximum number of tasks to return"),
    offset: int = Query(0, description="Number of tasks to skip"),
    service: FollowUpManagementService = Depends(get_followup_service)
):
    """Get follow-up tasks with filtering options."""
    tasks = await service.get_follow_up_tasks(
        assigned_to=assigned_to,
        contact_id=contact_id,
        lead_id=lead_id,
        deal_id=deal_id,
        status=status,
        priority=priority,
        due_before=due_before,
        due_after=due_after,
        limit=limit,
        offset=offset
    )
    return tasks


@router.get("/tasks/overdue", response_model=List[FollowUpTask])
async def get_overdue_tasks(
    assigned_to: Optional[uuid.UUID] = Query(None, description="Filter by assigned user"),
    service: FollowUpManagementService = Depends(get_followup_service)
):
    """Get overdue follow-up tasks."""
    tasks = await service.get_overdue_tasks(assigned_to)
    return tasks


@router.get("/tasks/upcoming", response_model=List[FollowUpTask])
async def get_upcoming_tasks(
    assigned_to: Optional[uuid.UUID] = Query(None, description="Filter by assigned user"),
    days_ahead: int = Query(7, description="Number of days ahead to look"),
    service: FollowUpManagementService = Depends(get_followup_service)
):
    """Get upcoming follow-up tasks."""
    tasks = await service.get_upcoming_tasks(assigned_to, days_ahead)
    return tasks


@router.post("/tasks/prioritize", response_model=List[FollowUpTask])
async def prioritize_tasks(
    task_ids: List[uuid.UUID],
    service: FollowUpManagementService = Depends(get_followup_service)
):
    """Prioritize a list of tasks."""
    # Get the tasks first
    tasks = []
    for task_id in task_ids:
        task = await service.get_follow_up_task(task_id)
        if task:
            tasks.append(task)
    
    prioritized_tasks = await service.prioritize_tasks(tasks)
    return prioritized_tasks


@router.post("/tasks/bulk-update", response_model=List[FollowUpTask])
async def bulk_update_tasks(
    request: BulkUpdateRequest,
    service: FollowUpManagementService = Depends(get_followup_service)
):
    """Bulk update multiple tasks."""
    updated_tasks = await service.bulk_update_tasks(request.task_ids, request.updates)
    return updated_tasks


@router.post("/tasks/schedule", response_model=FollowUpTask)
async def schedule_follow_up_task(
    title: str = Query(..., description="Task title"),
    assigned_to: uuid.UUID = Query(..., description="User assigned to the task"),
    delay_hours: int = Query(..., description="Hours to delay the task"),
    contact_id: Optional[uuid.UUID] = Query(None, description="Related contact ID"),
    lead_id: Optional[uuid.UUID] = Query(None, description="Related lead ID"),
    deal_id: Optional[uuid.UUID] = Query(None, description="Related deal ID"),
    service: FollowUpManagementService = Depends(get_followup_service)
):
    """Schedule a follow-up task with a delay."""
    task = await service.schedule_follow_up_task(
        title=title,
        assigned_to=assigned_to,
        delay_hours=delay_hours,
        contact_id=contact_id,
        lead_id=lead_id,
        deal_id=deal_id
    )
    return task


# Follow-up Sequences endpoints
@router.post("/sequences", response_model=FollowUpSequence)
async def create_follow_up_sequence(
    request: CreateFollowUpSequenceRequest,
    service: FollowUpManagementService = Depends(get_followup_service)
):
    """Create a follow-up sequence template."""
    sequence = await service.create_follow_up_sequence(
        name=request.name,
        description=request.description,
        trigger_event=request.trigger_event,
        trigger_delay_hours=request.trigger_delay_hours,
        steps=request.steps
    )
    return sequence


@router.get("/sequences/{sequence_id}", response_model=FollowUpSequence)
async def get_follow_up_sequence(
    sequence_id: uuid.UUID,
    service: FollowUpManagementService = Depends(get_followup_service)
):
    """Get a follow-up sequence by ID."""
    sequence = await service.get_follow_up_sequence(sequence_id)
    if not sequence:
        raise HTTPException(status_code=404, detail="Follow-up sequence not found")
    return sequence


@router.get("/sequences", response_model=List[FollowUpSequence])
async def get_follow_up_sequences(
    trigger_event: Optional[str] = Query(None, description="Filter by trigger event"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    service: FollowUpManagementService = Depends(get_followup_service)
):
    """Get follow-up sequences with filtering."""
    sequences = await service.get_follow_up_sequences(
        trigger_event=trigger_event,
        is_active=is_active
    )
    return sequences


@router.post("/sequences/trigger", response_model=List[FollowUpTask])
async def trigger_follow_up_sequence(
    request: TriggerSequenceRequest,
    assigned_to: uuid.UUID = Query(..., description="User to assign created tasks to"),
    service: FollowUpManagementService = Depends(get_followup_service)
):
    """Trigger follow-up sequences based on an event."""
    tasks = await service.trigger_follow_up_sequence(
        trigger_event=request.trigger_event,
        assigned_to=assigned_to,
        context=request.context
    )
    return tasks


@router.post("/auto-generate", response_model=List[FollowUpTask])
async def auto_generate_follow_ups(
    event_type: str = Query(..., description="Type of event that occurred"),
    assigned_to: uuid.UUID = Query(..., description="User to assign tasks to"),
    contact_id: Optional[uuid.UUID] = Query(None, description="Related contact ID"),
    lead_id: Optional[uuid.UUID] = Query(None, description="Related lead ID"),
    deal_id: Optional[uuid.UUID] = Query(None, description="Related deal ID"),
    property_id: Optional[uuid.UUID] = Query(None, description="Related property ID"),
    service: FollowUpManagementService = Depends(get_followup_service)
):
    """Auto-generate follow-up tasks based on events."""
    context = {
        "assigned_to": assigned_to,
        "contact_id": contact_id,
        "lead_id": lead_id,
        "deal_id": deal_id,
        "property_id": property_id
    }
    
    tasks = await service.auto_generate_follow_ups(event_type, context)
    return tasks


# Analytics endpoints
@router.get("/analytics/effectiveness")
async def get_task_effectiveness_metrics(
    assigned_to: Optional[uuid.UUID] = Query(None, description="Filter by assigned user"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    date_from: Optional[datetime] = Query(None, description="Start date for metrics"),
    date_to: Optional[datetime] = Query(None, description="End date for metrics"),
    service: FollowUpManagementService = Depends(get_followup_service)
):
    """Get effectiveness metrics for follow-up tasks."""
    metrics = await service.get_task_effectiveness_metrics(
        assigned_to=assigned_to,
        task_type=task_type,
        date_from=date_from,
        date_to=date_to
    )
    return metrics


@router.get("/analytics/statistics")
async def get_task_statistics(
    assigned_to: Optional[uuid.UUID] = Query(None, description="Filter by assigned user"),
    date_from: Optional[datetime] = Query(None, description="Start date for statistics"),
    date_to: Optional[datetime] = Query(None, description="End date for statistics"),
    service: FollowUpManagementService = Depends(get_followup_service)
):
    """Get task statistics and analytics."""
    statistics = await service.get_task_statistics(
        assigned_to=assigned_to,
        date_from=date_from,
        date_to=date_to
    )
    return statistics