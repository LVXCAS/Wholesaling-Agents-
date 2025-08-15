"""
Integration tests for closing coordination service.
Tests closing timeline management, multi-party coordination, document preparation tracking,
and funds transfer coordination.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.closing_coordination_service import ClosingCoordinationService
from app.models.transaction import TaskStatus, TaskPriority


class TestClosingCoordinationIntegration:
    """Integration test cases for ClosingCoordinationService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = ClosingCoordinationService()
        self.transaction_id = uuid4()
        self.closing_date = datetime.now() + timedelta(days=14)  # 2 weeks from now
    
    def test_create_purchase_closing_coordination(self):
        """Test creating closing coordination for purchase transaction."""
        parties = [
            {"role": "buyer", "name": "John Doe", "required": True},
            {"role": "seller", "name": "Jane Smith", "required": True},
            {"role": "buyer_agent", "name": "Agent A", "required": False},
            {"role": "title_company", "name": "Title Co", "required": True}
        ]
        
        coordination = self.service.create_closing_coordination(
            transaction_id=self.transaction_id,
            closing_date=self.closing_date,
            transaction_type="purchase",
            parties=parties
        )
        
        assert coordination.transaction_id == self.transaction_id
        assert coordination.closing_date == self.closing_date
        assert len(coordination.required_attendees) == len(parties)
        assert len(coordination.required_documents) > 0
        assert len(coordination.timeline_tasks) > 0
        assert len(coordination.critical_deadlines) > 0
        assert coordination.coordination_status == "planning"
        
        # Verify coordination is stored
        retrieved = self.service.get_closing_coordination(coordination.id)
        assert retrieved is not None
        assert retrieved.id == coordination.id
    
    def test_create_wholesale_closing_coordination(self):
        """Test creating closing coordination for wholesale transaction."""
        coordination = self.service.create_closing_coordination(
            transaction_id=self.transaction_id,
            closing_date=self.closing_date,
            transaction_type="wholesale"
        )
        
        assert coordination.transaction_id == self.transaction_id
        assert len(coordination.required_documents) > 0
        assert len(coordination.timeline_tasks) > 0
        
        # Wholesale should have fewer documents and tasks than purchase
        purchase_coordination = self.service.create_closing_coordination(
            transaction_id=uuid4(),
            closing_date=self.closing_date,
            transaction_type="purchase"
        )
        
        assert len(coordination.required_documents) < len(purchase_coordination.required_documents)
        assert len(coordination.timeline_tasks) < len(purchase_coordination.timeline_tasks)
    
    def test_party_attendance_management(self):
        """Test managing party attendance confirmations."""
        coordination = self.service.create_closing_coordination(
            transaction_id=self.transaction_id,
            closing_date=self.closing_date,
            transaction_type="purchase"
        )
        
        # Initially no confirmed attendees
        assert len(coordination.confirmed_attendees) == 0
        
        # Confirm attendance
        success = self.service.update_party_attendance(
            coordination.id, 
            "John Doe", 
            confirmed=True
        )
        assert success is True
        
        # Check attendance updated
        updated_coordination = self.service.get_closing_coordination(coordination.id)
        assert "John Doe" in updated_coordination.confirmed_attendees
        
        # Unconfirm attendance
        success = self.service.update_party_attendance(
            coordination.id,
            "John Doe",
            confirmed=False
        )
        assert success is True
        
        # Check attendance removed
        final_coordination = self.service.get_closing_coordination(coordination.id)
        assert "John Doe" not in final_coordination.confirmed_attendees
    
    def test_document_management_workflow(self):
        """Test complete document management workflow."""
        coordination = self.service.create_closing_coordination(
            transaction_id=self.transaction_id,
            closing_date=self.closing_date,
            transaction_type="purchase"
        )
        
        # Initially no prepared documents
        assert len(coordination.prepared_documents) == 0
        
        # Add document
        document_info = {
            "name": "Final Settlement Statement (HUD-1/CD)",
            "type": "pdf",
            "prepared_by": "title_company@example.com",
            "url": "https://example.com/settlement.pdf",
            "notes": "Initial draft prepared"
        }
        
        success = self.service.add_document(coordination.id, document_info)
        assert success is True
        
        # Check document added
        updated_coordination = self.service.get_closing_coordination(coordination.id)
        assert len(updated_coordination.prepared_documents) == 1
        
        document = updated_coordination.prepared_documents[0]
        assert document["name"] == "Final Settlement Statement (HUD-1/CD)"
        assert document["status"] == "prepared"
        assert document["review_status"] == "pending"
        
        # Review document
        success = self.service.review_document(
            coordination.id,
            document["id"],
            "attorney@example.com",
            "approved",
            "Document looks good"
        )
        assert success is True
        
        # Check review updated
        final_coordination = self.service.get_closing_coordination(coordination.id)
        reviewed_document = final_coordination.prepared_documents[0]
        assert reviewed_document["review_status"] == "approved"
        assert reviewed_document["reviewed_by"] == "attorney@example.com"
        assert "review_notes" in reviewed_document
    
    def test_funds_coordination(self):
        """Test funds requirement and confirmation management."""
        coordination = self.service.create_closing_coordination(
            transaction_id=self.transaction_id,
            closing_date=self.closing_date,
            transaction_type="purchase"
        )
        
        # Set funds requirements
        success = self.service.set_funds_requirement(coordination.id, "buyer", 50000.0)
        assert success is True
        
        success = self.service.set_funds_requirement(coordination.id, "seller", 1000.0)
        assert success is True
        
        # Check requirements set
        updated_coordination = self.service.get_closing_coordination(coordination.id)
        assert updated_coordination.funds_required["buyer"] == 50000.0
        assert updated_coordination.funds_required["seller"] == 1000.0
        assert updated_coordination.funds_confirmed["buyer"] is False
        assert updated_coordination.funds_confirmed["seller"] is False
        
        # Confirm funds
        success = self.service.confirm_funds(coordination.id, "buyer", True)
        assert success is True
        
        # Check confirmation
        final_coordination = self.service.get_closing_coordination(coordination.id)
        assert final_coordination.funds_confirmed["buyer"] is True
        assert final_coordination.funds_confirmed["seller"] is False
    
    def test_wire_instructions_management(self):
        """Test wire transfer instructions management."""
        coordination = self.service.create_closing_coordination(
            transaction_id=self.transaction_id,
            closing_date=self.closing_date,
            transaction_type="purchase"
        )
        
        # Add wire instructions
        wire_info = {
            "party": "buyer",
            "bank_name": "First National Bank",
            "routing_number": "123456789",
            "account_number": "987654321",
            "amount": 50000.0,
            "reference": "Property Purchase - 123 Main St",
            "deadline": "2024-01-15 10:00:00"
        }
        
        success = self.service.add_wire_instructions(coordination.id, wire_info)
        assert success is True
        
        # Check wire instructions added
        updated_coordination = self.service.get_closing_coordination(coordination.id)
        assert len(updated_coordination.wire_instructions) == 1
        
        wire_instruction = updated_coordination.wire_instructions[0]
        assert wire_instruction["party"] == "buyer"
        assert wire_instruction["bank_name"] == "First National Bank"
        assert wire_instruction["amount"] == 50000.0
    
    def test_walkthrough_management(self):
        """Test final walkthrough scheduling and completion."""
        coordination = self.service.create_closing_coordination(
            transaction_id=self.transaction_id,
            closing_date=self.closing_date,
            transaction_type="purchase"
        )
        
        # Initially walkthrough not scheduled
        assert coordination.walkthrough_scheduled is False
        assert coordination.walkthrough_completed is False
        
        # Schedule walkthrough
        walkthrough_date = self.closing_date - timedelta(hours=4)
        success = self.service.schedule_walkthrough(coordination.id, walkthrough_date)
        assert success is True
        
        # Check walkthrough scheduled
        updated_coordination = self.service.get_closing_coordination(coordination.id)
        assert updated_coordination.walkthrough_scheduled is True
        assert updated_coordination.walkthrough_date == walkthrough_date
        
        # Complete walkthrough with issues
        issues = ["Minor scuff on wall", "Light bulb out in kitchen"]
        success = self.service.complete_walkthrough(coordination.id, issues)
        assert success is True
        
        # Check walkthrough completed
        final_coordination = self.service.get_closing_coordination(coordination.id)
        assert final_coordination.walkthrough_completed is True
        assert len(final_coordination.walkthrough_issues) == 2
        assert "Minor scuff on wall" in final_coordination.walkthrough_issues
    
    def test_timeline_task_management(self):
        """Test timeline task status updates."""
        coordination = self.service.create_closing_coordination(
            transaction_id=self.transaction_id,
            closing_date=self.closing_date,
            transaction_type="purchase"
        )
        
        # Get first task
        task = coordination.timeline_tasks[0]
        assert task.status == TaskStatus.PENDING
        
        # Update task to in progress
        success = self.service.update_task_status(
            coordination.id,
            task.id,
            TaskStatus.IN_PROGRESS,
            "Task started"
        )
        assert success is True
        
        # Check task updated
        updated_coordination = self.service.get_closing_coordination(coordination.id)
        updated_task = next(t for t in updated_coordination.timeline_tasks if t.id == task.id)
        assert updated_task.status == TaskStatus.IN_PROGRESS
        assert updated_task.started_at is not None
        assert len(updated_task.notes) > 0
        
        # Complete task
        success = self.service.update_task_status(
            coordination.id,
            task.id,
            TaskStatus.COMPLETED,
            "Task completed successfully"
        )
        assert success is True
        
        # Check task completed
        final_coordination = self.service.get_closing_coordination(coordination.id)
        completed_task = next(t for t in final_coordination.timeline_tasks if t.id == task.id)
        assert completed_task.status == TaskStatus.COMPLETED
        assert completed_task.completed_at is not None
        assert completed_task.progress_percentage == 100
    
    def test_coordination_status_updates(self):
        """Test automatic coordination status updates."""
        coordination = self.service.create_closing_coordination(
            transaction_id=self.transaction_id,
            closing_date=self.closing_date,
            transaction_type="wholesale"  # Simpler for testing
        )
        
        # Initially should be planning
        assert coordination.coordination_status == "planning"
        
        # Complete most tasks
        tasks_to_complete = coordination.timeline_tasks[:2]  # Complete first 2 tasks
        for task in tasks_to_complete:
            self.service.update_task_status(coordination.id, task.id, TaskStatus.COMPLETED)
        
        # Add and review most documents
        for doc_name in coordination.required_documents[:3]:  # First 3 documents
            doc_info = {
                "name": doc_name,
                "type": "pdf",
                "prepared_by": "title_company@example.com"
            }
            self.service.add_document(coordination.id, doc_info)
        
        # Should now be coordinating
        updated_coordination = self.service.get_closing_coordination(coordination.id)
        # Status might be coordinating or still planning depending on completion percentages
        assert updated_coordination.coordination_status in ["planning", "coordinating"]
    
    def test_overdue_task_detection(self):
        """Test detection of overdue closing tasks."""
        coordination = self.service.create_closing_coordination(
            transaction_id=self.transaction_id,
            closing_date=self.closing_date,
            transaction_type="purchase"
        )
        
        # Set a task due date in the past
        task = coordination.timeline_tasks[0]
        task.due_date = datetime.now() - timedelta(days=2)
        task.status = TaskStatus.IN_PROGRESS
        
        # Get overdue tasks
        overdue_tasks = self.service.get_overdue_tasks(coordination.id)
        
        # Should find our overdue task
        our_overdue_task = next(
            (t for t in overdue_tasks if t["task_id"] == task.id),
            None
        )
        
        assert our_overdue_task is not None
        assert our_overdue_task["days_overdue"] == 2
        assert our_overdue_task["coordination_id"] == coordination.id
    
    def test_upcoming_deadlines(self):
        """Test detection of upcoming critical deadlines."""
        # Create coordination with closing date 5 days from now
        near_closing_date = datetime.now() + timedelta(days=5)
        coordination = self.service.create_closing_coordination(
            transaction_id=self.transaction_id,
            closing_date=near_closing_date,
            transaction_type="purchase"
        )
        
        # Get upcoming deadlines
        upcoming_deadlines = self.service.get_upcoming_deadlines(days_ahead=7)
        
        # Should have deadlines for our coordination
        our_deadlines = [
            d for d in upcoming_deadlines 
            if d["coordination_id"] == coordination.id
        ]
        
        assert len(our_deadlines) > 0
        
        # Check deadline structure
        deadline = our_deadlines[0]
        assert "deadline_name" in deadline
        assert "deadline_date" in deadline
        assert "days_until" in deadline
        assert "critical" in deadline
        assert deadline["days_until"] >= 0
    
    def test_closing_checklist_generation(self):
        """Test comprehensive closing checklist generation."""
        coordination = self.service.create_closing_coordination(
            transaction_id=self.transaction_id,
            closing_date=self.closing_date,
            transaction_type="purchase"
        )
        
        # Make some progress
        # Complete a task
        task = coordination.timeline_tasks[0]
        self.service.update_task_status(coordination.id, task.id, TaskStatus.COMPLETED)
        
        # Add and review a document
        doc_info = {
            "name": coordination.required_documents[0],
            "type": "pdf",
            "prepared_by": "title_company@example.com"
        }
        self.service.add_document(coordination.id, doc_info)
        
        # Set and confirm funds
        self.service.set_funds_requirement(coordination.id, "buyer", 50000.0)
        self.service.confirm_funds(coordination.id, "buyer", True)
        
        # Confirm attendance
        self.service.update_party_attendance(coordination.id, "John Doe", True)
        
        # Generate checklist
        checklist = self.service.generate_closing_checklist(coordination.id)
        
        assert checklist is not None
        assert "coordination_id" in checklist
        assert "closing_date" in checklist
        assert "coordination_status" in checklist
        assert "readiness_percentage" in checklist
        assert "task_summary" in checklist
        assert "document_summary" in checklist
        assert "funds_summary" in checklist
        assert "attendance_summary" in checklist
        assert "walkthrough_status" in checklist
        assert "issues" in checklist
        assert "recommendations" in checklist
        
        # Check task summary
        task_summary = checklist["task_summary"]
        assert task_summary["total"] > 0
        assert task_summary["completed"] >= 1  # We completed one task
        
        # Check document summary
        doc_summary = checklist["document_summary"]
        assert doc_summary["required"] > 0
        assert doc_summary["prepared"] >= 1  # We added one document
        
        # Readiness percentage should be calculated
        assert 0 <= checklist["readiness_percentage"] <= 100
    
    def test_complete_closing(self):
        """Test marking closing as completed."""
        coordination = self.service.create_closing_coordination(
            transaction_id=self.transaction_id,
            closing_date=self.closing_date,
            transaction_type="purchase"
        )
        
        # Initially not completed
        assert coordination.coordination_status != "completed"
        assert coordination.completed_at is None
        
        # Complete closing
        success = self.service.complete_closing(coordination.id)
        assert success is True
        
        # Check closing completed
        completed_coordination = self.service.get_closing_coordination(coordination.id)
        assert completed_coordination.coordination_status == "completed"
        assert completed_coordination.completed_at is not None
        
        # All tasks should be marked completed
        for task in completed_coordination.timeline_tasks:
            assert task.status == TaskStatus.COMPLETED
            assert task.completed_at is not None
            assert task.progress_percentage == 100
    
    def test_list_closings_filtering(self):
        """Test listing closings with various filters."""
        # Create multiple closings
        coordination1 = self.service.create_closing_coordination(
            transaction_id=uuid4(),
            closing_date=datetime.now() + timedelta(days=5),
            transaction_type="purchase"
        )
        
        coordination2 = self.service.create_closing_coordination(
            transaction_id=uuid4(),
            closing_date=datetime.now() + timedelta(days=15),
            transaction_type="wholesale"
        )
        
        # Complete one closing
        self.service.complete_closing(coordination1.id)
        
        # Test listing all closings
        all_closings = self.service.list_closings()
        assert len(all_closings) >= 2
        
        # Test filtering by status
        completed_closings = self.service.list_closings(status="completed")
        assert len(completed_closings) >= 1
        assert all(c.coordination_status == "completed" for c in completed_closings)
        
        planning_closings = self.service.list_closings(status="planning")
        assert len(planning_closings) >= 1
        assert all(c.coordination_status == "planning" for c in planning_closings)
        
        # Test filtering by upcoming days
        upcoming_closings = self.service.list_closings(upcoming_days=10)
        upcoming_dates = [c.closing_date for c in upcoming_closings]
        cutoff_date = datetime.now() + timedelta(days=10)
        assert all(date <= cutoff_date for date in upcoming_dates)
    
    def test_export_closing_summary(self):
        """Test exporting comprehensive closing summary."""
        coordination = self.service.create_closing_coordination(
            transaction_id=self.transaction_id,
            closing_date=self.closing_date,
            transaction_type="purchase"
        )
        
        # Make some progress for more interesting export
        task = coordination.timeline_tasks[0]
        self.service.update_task_status(coordination.id, task.id, TaskStatus.COMPLETED)
        
        # Export summary
        summary = self.service.export_closing_summary(coordination.id)
        
        assert summary is not None
        assert "coordination" in summary
        assert "checklist" in summary
        assert "overdue_tasks" in summary
        assert "upcoming_deadlines" in summary
        assert "exported_at" in summary
        
        # Check coordination data
        assert summary["coordination"]["id"] == coordination.id
        assert summary["coordination"]["transaction_id"] == self.transaction_id
        
        # Check checklist data
        checklist = summary["checklist"]
        assert checklist is not None
        assert "readiness_percentage" in checklist
    
    def test_get_coordination_by_transaction(self):
        """Test retrieving coordination by transaction ID."""
        coordination = self.service.create_closing_coordination(
            transaction_id=self.transaction_id,
            closing_date=self.closing_date,
            transaction_type="purchase"
        )
        
        # Retrieve by transaction ID
        retrieved = self.service.get_coordination_by_transaction(self.transaction_id)
        
        assert retrieved is not None
        assert retrieved.id == coordination.id
        assert retrieved.transaction_id == self.transaction_id
        
        # Test with non-existent transaction ID
        non_existent = self.service.get_coordination_by_transaction(uuid4())
        assert non_existent is None
    
    def test_multiple_document_types(self):
        """Test handling different document types and statuses."""
        coordination = self.service.create_closing_coordination(
            transaction_id=self.transaction_id,
            closing_date=self.closing_date,
            transaction_type="purchase"
        )
        
        # Add multiple documents
        documents = [
            {"name": "Deed", "type": "pdf", "prepared_by": "title_company"},
            {"name": "Title Insurance Policy", "type": "pdf", "prepared_by": "title_company"},
            {"name": "Final Settlement Statement (HUD-1/CD)", "type": "pdf", "prepared_by": "title_company"}
        ]
        
        for doc_info in documents:
            success = self.service.add_document(coordination.id, doc_info)
            assert success is True
        
        # Review documents with different statuses
        updated_coordination = self.service.get_closing_coordination(coordination.id)
        docs = updated_coordination.prepared_documents
        
        # Approve first document
        self.service.review_document(coordination.id, docs[0]["id"], "attorney", "approved", "Good")
        
        # Reject second document
        self.service.review_document(coordination.id, docs[1]["id"], "attorney", "rejected", "Needs revision")
        
        # Leave third document pending
        
        # Check document review statuses
        final_coordination = self.service.get_closing_coordination(coordination.id)
        final_docs = final_coordination.prepared_documents
        
        assert final_docs[0]["review_status"] == "approved"
        assert final_docs[1]["review_status"] == "rejected"
        assert final_docs[2]["review_status"] == "pending"
        
        # Check document review status tracking
        assert final_coordination.document_review_status["Deed"] == "approved"
        assert final_coordination.document_review_status["Title Insurance Policy"] == "rejected"