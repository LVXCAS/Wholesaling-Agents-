"""
Unit tests for follow-up management service.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
import uuid

from app.services.followup_management_service import FollowUpManagementService
from app.models.scheduling import FollowUpTask, FollowUpSequence


class TestFollowUpManagementService:
    """Unit tests for FollowUpManagementService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.service = FollowUpManagementService(self.mock_db)
        self.assigned_to = uuid.uuid4()
        self.contact_id = uuid.uuid4()
        self.lead_id = uuid.uuid4()
        self.due_date = datetime.utcnow() + timedelta(hours=24)
    
    @pytest.mark.asyncio
    async def test_create_follow_up_task(self):
        """Test creating a follow-up task."""
        task = await self.service.create_follow_up_task(
            title="Test Follow-up",
            assigned_to=self.assigned_to,
            due_date=self.due_date,
            description="Test description",
            contact_id=self.contact_id,
            priority="high",
            task_type="call"
        )
        
        assert task.title == "Test Follow-up"
        assert task.assigned_to == self.assigned_to
        assert task.due_date == self.due_date
        assert task.description == "Test description"
        assert task.contact_id == self.contact_id
        assert task.priority == "high"
        assert task.task_type == "call"
        assert task.status == "pending"
        assert task.auto_generated is False
        assert task.id is not None
        assert task.created_at is not None
    
    @pytest.mark.asyncio
    async def test_create_follow_up_task_with_defaults(self):
        """Test creating a follow-up task with default values."""
        task = await self.service.create_follow_up_task(
            title="Simple Task",
            assigned_to=self.assigned_to,
            due_date=self.due_date
        )
        
        assert task.title == "Simple Task"
        assert task.priority == "normal"
        assert task.task_type == "general"
        assert task.status == "pending"
        assert task.auto_generated is False
    
    @pytest.mark.asyncio
    async def test_schedule_follow_up_task(self):
        """Test scheduling a follow-up task with delay."""
        delay_hours = 48
        
        task = await self.service.schedule_follow_up_task(
            title="Scheduled Task",
            assigned_to=self.assigned_to,
            delay_hours=delay_hours,
            contact_id=self.contact_id
        )
        
        expected_due_date = datetime.utcnow() + timedelta(hours=delay_hours)
        
        assert task.title == "Scheduled Task"
        assert task.assigned_to == self.assigned_to
        assert task.contact_id == self.contact_id
        assert task.auto_generated is True
        
        # Check due date is approximately correct (within 1 minute)
        time_diff = abs((task.due_date - expected_due_date).total_seconds())
        assert time_diff < 60
    
    @pytest.mark.asyncio
    async def test_prioritize_tasks(self):
        """Test task prioritization logic."""
        now = datetime.utcnow()
        
        # Create tasks with different priorities and due dates
        urgent_task = FollowUpTask(
            id=uuid.uuid4(),
            title="Urgent Task",
            assigned_to=self.assigned_to,
            due_date=now + timedelta(hours=1),
            priority="urgent",
            status="pending"
        )
        
        overdue_task = FollowUpTask(
            id=uuid.uuid4(),
            title="Overdue Task",
            assigned_to=self.assigned_to,
            due_date=now - timedelta(days=1),
            priority="normal",
            status="pending"
        )
        
        low_priority_task = FollowUpTask(
            id=uuid.uuid4(),
            title="Low Priority Task",
            assigned_to=self.assigned_to,
            due_date=now + timedelta(days=7),
            priority="low",
            status="pending"
        )
        
        tasks = [low_priority_task, urgent_task, overdue_task]
        prioritized = await self.service.prioritize_tasks(tasks)
        
        # Urgent task due in 1 hour should be first (urgent priority + due soon bonus)
        # Overdue task should be second (gets bonus points for being overdue)
        # Low priority task should be last
        assert prioritized[0].title == "Urgent Task"
        assert prioritized[1].title == "Overdue Task"
        assert prioritized[2].title == "Low Priority Task"
    
    @pytest.mark.asyncio
    async def test_create_follow_up_sequence(self):
        """Test creating a follow-up sequence."""
        steps = [
            {
                "title": "Initial contact",
                "delay_hours": 1,
                "task_type": "call",
                "priority": "high"
            },
            {
                "title": "Follow-up email",
                "delay_hours": 24,
                "task_type": "email",
                "priority": "normal"
            }
        ]
        
        sequence = await self.service.create_follow_up_sequence(
            name="Lead Follow-up Sequence",
            trigger_event="lead_created",
            steps=steps,
            description="Standard lead follow-up process"
        )
        
        assert sequence.name == "Lead Follow-up Sequence"
        assert sequence.trigger_event == "lead_created"
        assert sequence.steps == steps
        assert sequence.description == "Standard lead follow-up process"
        assert sequence.trigger_delay_hours == 0
        assert sequence.is_active is True
        assert sequence.id is not None
        assert sequence.created_at is not None
    
    @pytest.mark.asyncio
    async def test_auto_generate_follow_ups_lead_created(self):
        """Test auto-generating follow-ups for lead creation."""
        context = {
            "assigned_to": self.assigned_to,
            "contact_id": self.contact_id,
            "lead_id": self.lead_id
        }
        
        tasks = await self.service.auto_generate_follow_ups("lead_created", context)
        
        assert len(tasks) == 3  # Based on the lead_created pattern
        
        # Check first task (initial contact)
        first_task = tasks[0]
        assert first_task.title == "Initial contact attempt"
        assert first_task.task_type == "call"
        assert first_task.priority == "high"
        assert first_task.auto_generated is True
        assert first_task.trigger_event == "lead_created"
        
        # Check second task (follow-up email)
        second_task = tasks[1]
        assert second_task.title == "Follow-up email if no response"
        assert second_task.task_type == "email"
        assert second_task.priority == "normal"
        
        # Check third task (second call)
        third_task = tasks[2]
        assert third_task.title == "Second follow-up call"
        assert third_task.task_type == "call"
        assert third_task.priority == "normal"
        
        # Check due dates are properly spaced
        assert first_task.due_date < second_task.due_date < third_task.due_date
    
    @pytest.mark.asyncio
    async def test_auto_generate_follow_ups_no_response(self):
        """Test auto-generating follow-ups for no response."""
        context = {
            "assigned_to": self.assigned_to,
            "contact_id": self.contact_id
        }
        
        tasks = await self.service.auto_generate_follow_ups("no_response", context)
        
        assert len(tasks) == 2  # Based on the no_response pattern
        
        first_task = tasks[0]
        assert first_task.title == "Try different communication channel"
        assert first_task.priority == "normal"
        
        second_task = tasks[1]
        assert second_task.title == "Research additional contact methods"
        assert second_task.task_type == "research"
        assert second_task.priority == "low"
    
    @pytest.mark.asyncio
    async def test_auto_generate_follow_ups_unknown_event(self):
        """Test auto-generating follow-ups for unknown event type."""
        context = {
            "assigned_to": self.assigned_to,
            "contact_id": self.contact_id
        }
        
        tasks = await self.service.auto_generate_follow_ups("unknown_event", context)
        
        assert len(tasks) == 0  # No pattern for unknown events
    
    @pytest.mark.asyncio
    async def test_auto_generate_follow_ups_no_assigned_to(self):
        """Test auto-generating follow-ups without assigned_to."""
        context = {
            "contact_id": self.contact_id
        }
        
        tasks = await self.service.auto_generate_follow_ups("lead_created", context)
        
        assert len(tasks) == 0  # Should not create tasks without assigned_to
    
    @pytest.mark.asyncio
    async def test_get_task_effectiveness_metrics(self):
        """Test getting task effectiveness metrics."""
        metrics = await self.service.get_task_effectiveness_metrics(
            assigned_to=self.assigned_to,
            task_type="call"
        )
        
        # Check that all expected metrics are present
        expected_keys = [
            "total_tasks", "completed_tasks", "overdue_tasks", "completion_rate",
            "average_completion_time_hours", "tasks_by_priority", "tasks_by_type",
            "completion_rate_by_type"
        ]
        
        for key in expected_keys:
            assert key in metrics
        
        assert isinstance(metrics["tasks_by_priority"], dict)
        assert isinstance(metrics["tasks_by_type"], dict)
        assert isinstance(metrics["completion_rate_by_type"], dict)
    
    @pytest.mark.asyncio
    async def test_get_task_statistics(self):
        """Test getting task statistics."""
        statistics = await self.service.get_task_statistics(
            assigned_to=self.assigned_to
        )
        
        # Check that all expected statistics are present
        expected_keys = [
            "total_tasks", "pending_tasks", "completed_tasks", "overdue_tasks",
            "completion_rate", "average_completion_time_days", "tasks_by_priority",
            "tasks_by_type", "productivity_score"
        ]
        
        for key in expected_keys:
            assert key in statistics
        
        assert isinstance(statistics["tasks_by_priority"], dict)
        assert isinstance(statistics["tasks_by_type"], dict)
        assert isinstance(statistics["productivity_score"], (int, float))
    
    @pytest.mark.asyncio
    async def test_complete_follow_up_task(self):
        """Test completing a follow-up task."""
        # Mock the get_follow_up_task method
        mock_task = FollowUpTask(
            id=uuid.uuid4(),
            title="Test Task",
            assigned_to=self.assigned_to,
            due_date=self.due_date,
            status="pending"
        )
        
        self.service.get_follow_up_task = AsyncMock(return_value=mock_task)
        self.service.trigger_completion_sequences = AsyncMock(return_value=[])
        
        completed_task = await self.service.complete_follow_up_task(
            mock_task.id,
            notes="Task completed successfully"
        )
        
        assert completed_task.status == "completed"
        assert completed_task.notes == "Task completed successfully"
        assert completed_task.completed_at is not None
        assert completed_task.updated_at is not None
        
        # Verify that completion sequences were triggered
        self.service.trigger_completion_sequences.assert_called_once_with(mock_task)
    
    @pytest.mark.asyncio
    async def test_cancel_follow_up_task(self):
        """Test cancelling a follow-up task."""
        # Mock the get_follow_up_task method
        mock_task = FollowUpTask(
            id=uuid.uuid4(),
            title="Test Task",
            assigned_to=self.assigned_to,
            due_date=self.due_date,
            status="pending",
            notes="Original notes"
        )
        
        self.service.get_follow_up_task = AsyncMock(return_value=mock_task)
        
        cancelled_task = await self.service.cancel_follow_up_task(
            mock_task.id,
            reason="No longer needed"
        )
        
        assert cancelled_task.status == "cancelled"
        assert "Cancelled: No longer needed" in cancelled_task.notes
        assert cancelled_task.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_snooze_task(self):
        """Test snoozing a task."""
        original_due_date = datetime.utcnow() + timedelta(hours=2)
        
        # Mock the get_follow_up_task method
        mock_task = FollowUpTask(
            id=uuid.uuid4(),
            title="Test Task",
            assigned_to=self.assigned_to,
            due_date=original_due_date,
            status="pending"
        )
        
        self.service.get_follow_up_task = AsyncMock(return_value=mock_task)
        
        snooze_hours = 24
        snoozed_task = await self.service.snooze_task(mock_task.id, snooze_hours)
        
        expected_due_date = original_due_date + timedelta(hours=snooze_hours)
        
        assert snoozed_task.due_date == expected_due_date
        assert snoozed_task.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_bulk_update_tasks(self):
        """Test bulk updating tasks."""
        task_ids = [uuid.uuid4(), uuid.uuid4()]
        updates = {"priority": "high", "status": "in_progress"}
        
        # Mock the update_follow_up_task method
        mock_tasks = [
            FollowUpTask(
                id=task_ids[0],
                title="Task 1",
                assigned_to=self.assigned_to,
                due_date=self.due_date,
                priority="high",
                status="in_progress"
            ),
            FollowUpTask(
                id=task_ids[1],
                title="Task 2",
                assigned_to=self.assigned_to,
                due_date=self.due_date,
                priority="high",
                status="in_progress"
            )
        ]
        
        self.service.update_follow_up_task = AsyncMock(side_effect=mock_tasks)
        
        updated_tasks = await self.service.bulk_update_tasks(task_ids, updates)
        
        assert len(updated_tasks) == 2
        for task in updated_tasks:
            assert task.priority == "high"
            assert task.status == "in_progress"
        
        # Verify update_follow_up_task was called for each task
        assert self.service.update_follow_up_task.call_count == 2