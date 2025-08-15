"""
Unit tests for transaction workflow service.
Tests milestone tracking, progress monitoring, task generation, and deadline monitoring.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.transaction_workflow_service import TransactionWorkflowService
from app.models.transaction import (
    TransactionWorkflow, TransactionInstance, TransactionMilestone, TransactionTask,
    TransactionStatus, MilestoneStatus, TaskStatus, TaskPriority
)


class TestTransactionWorkflowService:
    """Test cases for TransactionWorkflowService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = TransactionWorkflowService()
    
    def test_initialize_default_workflows(self):
        """Test that default workflows are initialized."""
        workflows = self.service.list_workflows()
        assert len(workflows) >= 2
        
        # Check for purchase workflow
        purchase_workflows = [w for w in workflows if w.transaction_type == "purchase"]
        assert len(purchase_workflows) >= 1
        
        # Check for wholesale workflow
        wholesale_workflows = [w for w in workflows if w.transaction_type == "wholesale"]
        assert len(wholesale_workflows) >= 1
    
    def test_create_workflow(self):
        """Test creating a new workflow."""
        workflow = TransactionWorkflow(
            name="Test Workflow",
            description="Test workflow description",
            transaction_type="test",
            default_timeline_days=30
        )
        
        created_workflow = self.service.create_workflow(workflow)
        
        assert created_workflow.id is not None
        assert created_workflow.name == "Test Workflow"
        assert created_workflow.transaction_type == "test"
        assert created_workflow.created_at is not None
        
        # Verify it's stored
        retrieved = self.service.get_workflow(created_workflow.id)
        assert retrieved is not None
        assert retrieved.name == "Test Workflow"
    
    def test_create_transaction_from_workflow(self):
        """Test creating a transaction instance from a workflow."""
        # Get a default workflow
        workflows = self.service.list_workflows(transaction_type="purchase")
        assert len(workflows) > 0
        
        workflow = workflows[0]
        
        # Create transaction
        transaction = self.service.create_transaction(
            workflow_id=workflow.id,
            property_address="123 Test St, Test City, TS 12345",
            transaction_type="purchase",
            purchase_price=250000.0,
            contract_date=datetime.now()
        )
        
        assert transaction.id is not None
        assert transaction.workflow_id == workflow.id
        assert transaction.property_address == "123 Test St, Test City, TS 12345"
        assert transaction.purchase_price == 250000.0
        assert transaction.status == TransactionStatus.INITIATED
        assert len(transaction.current_milestones) > 0
        
        # Check that closing date was set
        assert transaction.closing_date is not None
        expected_closing = transaction.contract_date + timedelta(days=workflow.default_timeline_days)
        assert transaction.closing_date.date() == expected_closing.date()
    
    def test_milestone_creation_from_template(self):
        """Test that milestones are properly created from workflow templates."""
        workflows = self.service.list_workflows(transaction_type="purchase")
        workflow = workflows[0]
        
        transaction = self.service.create_transaction(
            workflow_id=workflow.id,
            property_address="123 Test St",
            transaction_type="purchase"
        )
        
        # Check milestones
        assert len(transaction.current_milestones) == len(workflow.milestones)
        
        for i, milestone in enumerate(transaction.current_milestones):
            template_milestone = workflow.milestones[i]
            assert milestone.name == template_milestone.name
            assert milestone.order == template_milestone.order
            assert milestone.is_critical == template_milestone.is_critical
            assert len(milestone.tasks) == len(template_milestone.tasks)
            
            # Check tasks
            for j, task in enumerate(milestone.tasks):
                template_task = template_milestone.tasks[j]
                assert task.name == template_task.name
                assert task.priority == template_task.priority
                assert task.task_type == template_task.task_type
    
    def test_start_milestone(self):
        """Test starting a milestone."""
        workflows = self.service.list_workflows(transaction_type="purchase")
        workflow = workflows[0]
        
        transaction = self.service.create_transaction(
            workflow_id=workflow.id,
            property_address="123 Test St",
            transaction_type="purchase"
        )
        
        # Start first milestone
        first_milestone = transaction.current_milestones[0]
        success = self.service.start_milestone(transaction.id, first_milestone.id)
        
        assert success is True
        
        # Refresh transaction
        updated_transaction = self.service.get_transaction(transaction.id)
        updated_milestone = next(
            m for m in updated_transaction.current_milestones 
            if m.id == first_milestone.id
        )
        
        assert updated_milestone.status == MilestoneStatus.IN_PROGRESS
        assert updated_milestone.actual_start_date is not None
        
        # Check that initial tasks are started
        initial_tasks = [t for t in updated_milestone.tasks if not t.depends_on]
        for task in initial_tasks:
            assert task.status == TaskStatus.IN_PROGRESS
            assert task.started_at is not None
            assert task.id in updated_transaction.active_tasks
    
    def test_complete_task(self):
        """Test completing a task."""
        workflows = self.service.list_workflows(transaction_type="purchase")
        workflow = workflows[0]
        
        transaction = self.service.create_transaction(
            workflow_id=workflow.id,
            property_address="123 Test St",
            transaction_type="purchase"
        )
        
        # Start first milestone
        first_milestone = transaction.current_milestones[0]
        self.service.start_milestone(transaction.id, first_milestone.id)
        
        # Get first task
        updated_transaction = self.service.get_transaction(transaction.id)
        updated_milestone = next(
            m for m in updated_transaction.current_milestones 
            if m.id == first_milestone.id
        )
        first_task = updated_milestone.tasks[0]
        
        # Complete the task
        success = self.service.complete_task(
            transaction.id, 
            first_task.id, 
            "Task completed successfully"
        )
        
        assert success is True
        
        # Verify task completion
        final_transaction = self.service.get_transaction(transaction.id)
        final_milestone = next(
            m for m in final_transaction.current_milestones 
            if m.id == first_milestone.id
        )
        completed_task = next(t for t in final_milestone.tasks if t.id == first_task.id)
        
        assert completed_task.status == TaskStatus.COMPLETED
        assert completed_task.completed_at is not None
        assert completed_task.progress_percentage == 100
        assert "Task completed successfully" in completed_task.notes
        assert first_task.id not in final_transaction.active_tasks
        
        # Check milestone progress update
        completed_tasks = [t for t in final_milestone.tasks if t.status == TaskStatus.COMPLETED]
        expected_progress = int((len(completed_tasks) / len(final_milestone.tasks)) * 100)
        assert final_milestone.progress_percentage == expected_progress
    
    def test_complete_milestone(self):
        """Test completing a milestone."""
        workflows = self.service.list_workflows(transaction_type="wholesale")  # Shorter workflow
        workflow = workflows[0]
        
        transaction = self.service.create_transaction(
            workflow_id=workflow.id,
            property_address="123 Test St",
            transaction_type="wholesale"
        )
        
        # Start and complete first milestone
        first_milestone = transaction.current_milestones[0]
        self.service.start_milestone(transaction.id, first_milestone.id)
        
        # Complete all tasks in the milestone
        updated_transaction = self.service.get_transaction(transaction.id)
        updated_milestone = next(
            m for m in updated_transaction.current_milestones 
            if m.id == first_milestone.id
        )
        
        for task in updated_milestone.tasks:
            self.service.complete_task(transaction.id, task.id)
        
        # Complete the milestone
        success = self.service.complete_milestone(transaction.id, first_milestone.id)
        assert success is True
        
        # Verify milestone completion
        final_transaction = self.service.get_transaction(transaction.id)
        final_milestone = next(
            m for m in final_transaction.current_milestones 
            if m.id == first_milestone.id
        )
        
        assert final_milestone.status == MilestoneStatus.COMPLETED
        assert final_milestone.actual_completion_date is not None
        assert final_milestone.progress_percentage == 100
        assert first_milestone.id in final_transaction.completed_milestones
    
    def test_transaction_progress_calculation(self):
        """Test transaction progress calculation."""
        workflows = self.service.list_workflows(transaction_type="wholesale")
        workflow = workflows[0]
        
        transaction = self.service.create_transaction(
            workflow_id=workflow.id,
            property_address="123 Test St",
            transaction_type="wholesale"
        )
        
        # Initially should be 0% progress
        assert transaction.overall_progress == 0
        
        # Complete first milestone
        first_milestone = transaction.current_milestones[0]
        self.service.start_milestone(transaction.id, first_milestone.id)
        
        updated_transaction = self.service.get_transaction(transaction.id)
        updated_milestone = next(
            m for m in updated_transaction.current_milestones 
            if m.id == first_milestone.id
        )
        
        for task in updated_milestone.tasks:
            self.service.complete_task(transaction.id, task.id)
        
        self.service.complete_milestone(transaction.id, first_milestone.id)
        
        # Update progress
        final_transaction = self.service.update_transaction_progress(transaction.id)
        
        # Should have some progress now
        assert final_transaction.overall_progress > 0
        
        # If we complete all milestones, should be 100%
        total_milestones = len(final_transaction.current_milestones)
        expected_progress = int((1 / total_milestones) * 100)
        assert final_transaction.overall_progress >= expected_progress
    
    def test_overdue_task_detection(self):
        """Test detection of overdue tasks."""
        workflows = self.service.list_workflows(transaction_type="purchase")
        workflow = workflows[0]
        
        transaction = self.service.create_transaction(
            workflow_id=workflow.id,
            property_address="123 Test St",
            transaction_type="purchase"
        )
        
        # Manually set a task due date in the past
        first_milestone = transaction.current_milestones[0]
        first_task = first_milestone.tasks[0]
        first_task.due_date = datetime.now() - timedelta(days=2)
        first_task.status = TaskStatus.IN_PROGRESS
        
        # Get overdue tasks
        overdue_tasks = self.service.get_overdue_tasks(transaction.id)
        
        assert len(overdue_tasks) == 1
        assert overdue_tasks[0]["task_id"] == first_task.id
        assert overdue_tasks[0]["days_overdue"] == 2
        assert overdue_tasks[0]["transaction_id"] == transaction.id
        
        # Verify task status was updated
        updated_transaction = self.service.get_transaction(transaction.id)
        updated_milestone = updated_transaction.current_milestones[0]
        updated_task = updated_milestone.tasks[0]
        assert updated_task.status == TaskStatus.OVERDUE
        assert first_task.id in updated_transaction.overdue_tasks
    
    def test_deadline_monitoring(self):
        """Test deadline monitoring and alert creation."""
        workflows = self.service.list_workflows(transaction_type="purchase")
        workflow = workflows[0]
        
        transaction = self.service.create_transaction(
            workflow_id=workflow.id,
            property_address="123 Test St",
            transaction_type="purchase"
        )
        
        # Set a task due date 2 days from now
        first_milestone = transaction.current_milestones[0]
        first_task = first_milestone.tasks[0]
        first_task.due_date = datetime.now() + timedelta(days=2)
        first_task.status = TaskStatus.IN_PROGRESS
        
        # Monitor deadlines
        alerts = self.service.monitor_deadlines()
        
        # Should create an alert for the upcoming deadline
        task_alerts = [a for a in alerts if a.transaction_id == transaction.id]
        assert len(task_alerts) >= 1
        
        alert = task_alerts[0]
        assert alert.alert_type == "deadline"
        assert alert.severity in ["medium", "high"]
        assert first_task.name in alert.title
    
    def test_critical_path_status_update(self):
        """Test critical path status updates."""
        workflows = self.service.list_workflows(transaction_type="purchase")
        workflow = workflows[0]
        
        # Create transaction with closing date
        closing_date = datetime.now() + timedelta(days=30)
        transaction = self.service.create_transaction(
            workflow_id=workflow.id,
            property_address="123 Test St",
            transaction_type="purchase",
            closing_date=closing_date
        )
        
        # Initially should be on track
        self.service.update_transaction_progress(transaction.id)
        updated_transaction = self.service.get_transaction(transaction.id)
        assert updated_transaction.critical_path_status in ["on_track", "ahead"]
        
        # Simulate being behind schedule by setting created_at to past
        transaction.created_at = datetime.now() - timedelta(days=20)
        transaction.overall_progress = 10  # Very low progress for 20 days
        
        self.service.update_transaction_progress(transaction.id)
        final_transaction = self.service.get_transaction(transaction.id)
        assert final_transaction.critical_path_status in ["at_risk", "delayed"]
    
    def test_transaction_report_generation(self):
        """Test comprehensive transaction report generation."""
        workflows = self.service.list_workflows(transaction_type="purchase")
        workflow = workflows[0]
        
        transaction = self.service.create_transaction(
            workflow_id=workflow.id,
            property_address="123 Test St",
            transaction_type="purchase",
            purchase_price=300000.0,
            closing_date=datetime.now() + timedelta(days=45)
        )
        
        # Make some progress
        first_milestone = transaction.current_milestones[0]
        self.service.start_milestone(transaction.id, first_milestone.id)
        
        # Complete one task
        updated_transaction = self.service.get_transaction(transaction.id)
        updated_milestone = next(
            m for m in updated_transaction.current_milestones 
            if m.id == first_milestone.id
        )
        first_task = updated_milestone.tasks[0]
        self.service.complete_task(transaction.id, first_task.id)
        
        # Generate report
        report = self.service.generate_transaction_report(transaction.id)
        
        assert report is not None
        assert report.transaction_id == transaction.id
        assert report.current_status == transaction.status
        assert report.overall_progress >= 0
        
        # Check transaction summary
        assert report.transaction_summary["property_address"] == "123 Test St"
        assert report.transaction_summary["purchase_price"] == 300000.0
        
        # Check milestone progress
        assert len(report.milestone_progress) > 0
        assert all("name" in mp for mp in report.milestone_progress)
        assert all("status" in mp for mp in report.milestone_progress)
        assert all("progress" in mp for mp in report.milestone_progress)
        
        # Check task summary
        assert "total" in report.task_summary
        assert "completed" in report.task_summary
        assert "in_progress" in report.task_summary
        assert report.task_summary["total"] > 0
        
        # Check risk assessment
        assert "risk_level" in report.risk_assessment
        assert report.risk_assessment["risk_level"] in ["low", "medium", "high"]
    
    def test_list_transactions_filtering(self):
        """Test transaction listing with filters."""
        workflows = self.service.list_workflows()
        purchase_workflow = next(w for w in workflows if w.transaction_type == "purchase")
        wholesale_workflow = next(w for w in workflows if w.transaction_type == "wholesale")
        
        # Create transactions of different types
        purchase_transaction = self.service.create_transaction(
            workflow_id=purchase_workflow.id,
            property_address="123 Purchase St",
            transaction_type="purchase"
        )
        
        wholesale_transaction = self.service.create_transaction(
            workflow_id=wholesale_workflow.id,
            property_address="456 Wholesale Ave",
            transaction_type="wholesale"
        )
        
        # Test filtering by transaction type
        purchase_transactions = self.service.list_transactions(transaction_type="purchase")
        assert len(purchase_transactions) >= 1
        assert all(t.transaction_type == "purchase" for t in purchase_transactions)
        
        wholesale_transactions = self.service.list_transactions(transaction_type="wholesale")
        assert len(wholesale_transactions) >= 1
        assert all(t.transaction_type == "wholesale" for t in wholesale_transactions)
        
        # Test filtering by status
        initiated_transactions = self.service.list_transactions(status=TransactionStatus.INITIATED)
        assert len(initiated_transactions) >= 2
        assert all(t.status == TransactionStatus.INITIATED for t in initiated_transactions)
        
        # Test limit
        limited_transactions = self.service.list_transactions(limit=1)
        assert len(limited_transactions) == 1
    
    def test_task_dependency_handling(self):
        """Test task dependency handling."""
        # Create a custom workflow with task dependencies
        workflow = TransactionWorkflow(
            name="Dependency Test Workflow",
            description="Test workflow with task dependencies",
            transaction_type="test"
        )
        
        # Create tasks with dependencies
        task1 = TransactionTask(
            name="Task 1",
            description="First task",
            priority=TaskPriority.HIGH
        )
        
        task2 = TransactionTask(
            name="Task 2", 
            description="Second task depends on first",
            priority=TaskPriority.MEDIUM,
            depends_on=[task1.id]
        )
        
        milestone = TransactionMilestone(
            name="Test Milestone",
            description="Test milestone with dependencies",
            order=1,
            tasks=[task1, task2]
        )
        
        workflow.milestones = [milestone]
        created_workflow = self.service.create_workflow(workflow)
        
        # Create transaction
        transaction = self.service.create_transaction(
            workflow_id=created_workflow.id,
            property_address="123 Dependency St",
            transaction_type="test"
        )
        
        # Start milestone
        milestone_instance = transaction.current_milestones[0]
        self.service.start_milestone(transaction.id, milestone_instance.id)
        
        # Check that only task1 started (no dependencies)
        updated_transaction = self.service.get_transaction(transaction.id)
        updated_milestone = updated_transaction.current_milestones[0]
        
        task1_instance = next(t for t in updated_milestone.tasks if t.name == "Task 1")
        task2_instance = next(t for t in updated_milestone.tasks if t.name == "Task 2")
        
        assert task1_instance.status == TaskStatus.IN_PROGRESS
        assert task2_instance.status == TaskStatus.PENDING
        
        # Complete task1
        self.service.complete_task(transaction.id, task1_instance.id)
        
        # Check that task2 now starts
        final_transaction = self.service.get_transaction(transaction.id)
        final_milestone = final_transaction.current_milestones[0]
        final_task2 = next(t for t in final_milestone.tasks if t.name == "Task 2")
        
        assert final_task2.status == TaskStatus.IN_PROGRESS
    
    def test_workflow_listing_filters(self):
        """Test workflow listing with filters."""
        # Test listing all workflows
        all_workflows = self.service.list_workflows(active_only=False)
        assert len(all_workflows) >= 2
        
        # Test filtering by transaction type
        purchase_workflows = self.service.list_workflows(transaction_type="purchase")
        assert len(purchase_workflows) >= 1
        assert all(w.transaction_type == "purchase" for w in purchase_workflows)
        
        # Test active only filter
        active_workflows = self.service.list_workflows(active_only=True)
        assert all(w.is_active for w in active_workflows)
        
        # Create inactive workflow
        inactive_workflow = TransactionWorkflow(
            name="Inactive Workflow",
            description="Inactive test workflow",
            transaction_type="test",
            is_active=False
        )
        self.service.create_workflow(inactive_workflow)
        
        # Test that inactive workflow is excluded when active_only=True
        active_only_workflows = self.service.list_workflows(active_only=True)
        inactive_names = [w.name for w in active_only_workflows]
        assert "Inactive Workflow" not in inactive_names
        
        # Test that inactive workflow is included when active_only=False
        all_workflows_including_inactive = self.service.list_workflows(active_only=False)
        all_names = [w.name for w in all_workflows_including_inactive]
        assert "Inactive Workflow" in all_names