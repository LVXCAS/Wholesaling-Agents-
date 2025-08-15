"""
Closing coordination service.
Handles closing timeline management, multi-party coordination, document preparation tracking,
and funds transfer coordination.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4

from app.models.transaction import (
    ClosingCoordination, TransactionTask, TaskStatus, TaskPriority, TransactionAlert
)


class ClosingCoordinationService:
    """Service for managing closing coordination and timeline management."""
    
    def __init__(self):
        # In-memory storage for demo - would be replaced with database
        self.closings: Dict[UUID, ClosingCoordination] = {}
        self.document_templates: Dict[str, List[str]] = {}
        self.party_roles: Dict[str, List[str]] = {}
        
        # Initialize default templates and configurations
        self._initialize_document_templates()
        self._initialize_party_roles()
    
    def _initialize_document_templates(self):
        """Initialize default document templates for different transaction types."""
        
        # Purchase transaction documents
        self.document_templates["purchase"] = [
            "Final Settlement Statement (HUD-1/CD)",
            "Deed",
            "Title Insurance Policy",
            "Loan Documents (if applicable)",
            "Property Survey",
            "Property Insurance Policy",
            "Final Walkthrough Report",
            "Keys and Garage Door Openers",
            "Utility Transfer Confirmations",
            "HOA Transfer Documents (if applicable)",
            "Warranty Deeds",
            "Tax Proration Documents",
            "Final Title Search Update",
            "Lender's Title Policy",
            "Owner's Title Policy",
            "Property Tax Certificates",
            "Homeowner's Insurance Binder",
            "Final Loan Approval Letter",
            "Cashier's Check/Wire Transfer Confirmations"
        ]
        
        # Wholesale transaction documents
        self.document_templates["wholesale"] = [
            "Assignment Agreement",
            "Original Purchase Agreement",
            "Assignment Fee Payment",
            "Title Search Update",
            "Property Condition Disclosure",
            "Assignment Notice to Seller",
            "End Buyer Qualification Documents",
            "Earnest Money Transfer",
            "Final Settlement Statement"
        ]
        
        # Refinance transaction documents
        self.document_templates["refinance"] = [
            "New Loan Documents",
            "Payoff Letters from Current Lender",
            "Title Insurance Policy",
            "Property Appraisal",
            "Homeowner's Insurance Policy",
            "Final Settlement Statement",
            "Deed of Trust/Mortgage",
            "Promissory Note",
            "Truth in Lending Disclosure",
            "Right of Rescission Notice"
        ]
    
    def _initialize_party_roles(self):
        """Initialize party roles and their typical responsibilities."""
        
        self.party_roles = {
            "buyer": [
                "Review and sign closing documents",
                "Provide certified funds for closing",
                "Complete final walkthrough",
                "Obtain homeowner's insurance",
                "Review settlement statement",
                "Receive keys and property access"
            ],
            "seller": [
                "Sign deed and transfer documents",
                "Provide clear title",
                "Complete any required repairs",
                "Provide utility readings",
                "Transfer property keys",
                "Sign settlement statement"
            ],
            "buyer_agent": [
                "Coordinate buyer activities",
                "Review closing documents",
                "Attend closing",
                "Ensure buyer compliance",
                "Coordinate final walkthrough"
            ],
            "seller_agent": [
                "Coordinate seller activities",
                "Ensure property is ready for closing",
                "Attend closing",
                "Ensure seller compliance",
                "Coordinate key transfer"
            ],
            "lender": [
                "Provide final loan approval",
                "Prepare loan documents",
                "Fund the loan",
                "Coordinate with title company",
                "Provide payoff information"
            ],
            "title_company": [
                "Conduct title search",
                "Prepare closing documents",
                "Coordinate closing meeting",
                "Disburse funds",
                "Record deed and documents",
                "Issue title insurance"
            ],
            "attorney": [
                "Review legal documents",
                "Provide legal advice",
                "Ensure compliance",
                "Handle document preparation",
                "Attend closing if required"
            ]
        }
    
    def create_closing_coordination(self, transaction_id: UUID, closing_date: datetime,
                                   transaction_type: str = "purchase",
                                   parties: Optional[List[Dict[str, Any]]] = None) -> ClosingCoordination:
        """Create a new closing coordination instance."""
        
        coordination = ClosingCoordination(
            transaction_id=transaction_id,
            closing_date=closing_date
        )
        
        # Set required attendees based on parties
        if parties:
            coordination.required_attendees = parties.copy()
        else:
            # Default attendees for purchase transaction
            coordination.required_attendees = [
                {"role": "buyer", "name": "TBD", "required": True},
                {"role": "seller", "name": "TBD", "required": True},
                {"role": "buyer_agent", "name": "TBD", "required": False},
                {"role": "seller_agent", "name": "TBD", "required": False},
                {"role": "title_company", "name": "TBD", "required": True},
                {"role": "lender", "name": "TBD", "required": False}
            ]
        
        # Set required documents based on transaction type
        coordination.required_documents = self.document_templates.get(
            transaction_type, 
            self.document_templates["purchase"]
        ).copy()
        
        # Generate closing timeline tasks
        coordination.timeline_tasks = self._generate_closing_timeline_tasks(
            closing_date, transaction_type
        )
        
        # Set critical deadlines
        coordination.critical_deadlines = self._generate_critical_deadlines(
            closing_date, transaction_type
        )
        
        # Store coordination
        self.closings[coordination.id] = coordination
        
        return coordination
    
    def _generate_closing_timeline_tasks(self, closing_date: datetime, 
                                       transaction_type: str) -> List[TransactionTask]:
        """Generate timeline tasks leading up to closing."""
        tasks = []
        
        # Tasks for purchase transaction
        if transaction_type == "purchase":
            # 7 days before closing
            tasks.append(TransactionTask(
                name="Final Loan Approval",
                description="Obtain final loan approval and commitment letter",
                priority=TaskPriority.CRITICAL,
                due_date=closing_date - timedelta(days=7),
                assigned_to_type="lender",
                task_type="approval"
            ))
            
            # 5 days before closing
            tasks.append(TransactionTask(
                name="Title Search Update",
                description="Complete final title search update",
                priority=TaskPriority.HIGH,
                due_date=closing_date - timedelta(days=5),
                assigned_to_type="title_company",
                task_type="document"
            ))
            
            # 3 days before closing
            tasks.append(TransactionTask(
                name="Prepare Closing Documents",
                description="Prepare all closing documents and settlement statement",
                priority=TaskPriority.CRITICAL,
                due_date=closing_date - timedelta(days=3),
                assigned_to_type="title_company",
                task_type="document"
            ))
            
            # 2 days before closing
            tasks.append(TransactionTask(
                name="Final Walkthrough Scheduling",
                description="Schedule final walkthrough with buyer",
                priority=TaskPriority.HIGH,
                due_date=closing_date - timedelta(days=2),
                assigned_to_type="buyer_agent",
                task_type="manual"
            ))
            
            # 1 day before closing
            tasks.append(TransactionTask(
                name="Funds Verification",
                description="Verify all funds are ready for closing",
                priority=TaskPriority.CRITICAL,
                due_date=closing_date - timedelta(days=1),
                assigned_to_type="title_company",
                task_type="manual"
            ))
            
            tasks.append(TransactionTask(
                name="Final Document Review",
                description="Final review of all closing documents",
                priority=TaskPriority.HIGH,
                due_date=closing_date - timedelta(days=1),
                assigned_to_type="attorney",
                task_type="document"
            ))
            
            # Day of closing
            tasks.append(TransactionTask(
                name="Final Walkthrough",
                description="Complete final walkthrough of property",
                priority=TaskPriority.HIGH,
                due_date=closing_date - timedelta(hours=4),
                assigned_to_type="buyer",
                task_type="manual"
            ))
            
        elif transaction_type == "wholesale":
            # 3 days before closing
            tasks.append(TransactionTask(
                name="Prepare Assignment Documents",
                description="Prepare assignment agreement and related documents",
                priority=TaskPriority.CRITICAL,
                due_date=closing_date - timedelta(days=3),
                assigned_to_type="title_company",
                task_type="document"
            ))
            
            # 2 days before closing
            tasks.append(TransactionTask(
                name="Verify End Buyer Funds",
                description="Verify end buyer has funds ready for closing",
                priority=TaskPriority.CRITICAL,
                due_date=closing_date - timedelta(days=2),
                assigned_to_type="title_company",
                task_type="manual"
            ))
            
            # 1 day before closing
            tasks.append(TransactionTask(
                name="Coordinate Assignment Fee",
                description="Coordinate assignment fee payment at closing",
                priority=TaskPriority.HIGH,
                due_date=closing_date - timedelta(days=1),
                assigned_to_type="title_company",
                task_type="manual"
            ))
        
        return tasks
    
    def _generate_critical_deadlines(self, closing_date: datetime,
                                   transaction_type: str) -> List[Dict[str, Any]]:
        """Generate critical deadlines for closing coordination."""
        deadlines = []
        
        if transaction_type == "purchase":
            deadlines.extend([
                {
                    "name": "Loan Approval Deadline",
                    "date": closing_date - timedelta(days=7),
                    "description": "Final loan approval must be received",
                    "critical": True
                },
                {
                    "name": "Title Search Completion",
                    "date": closing_date - timedelta(days=5),
                    "description": "Final title search must be completed",
                    "critical": True
                },
                {
                    "name": "Document Preparation Deadline",
                    "date": closing_date - timedelta(days=3),
                    "description": "All closing documents must be prepared",
                    "critical": True
                },
                {
                    "name": "Funds Verification Deadline",
                    "date": closing_date - timedelta(days=1),
                    "description": "All funds must be verified and ready",
                    "critical": True
                },
                {
                    "name": "Final Walkthrough Window",
                    "date": closing_date - timedelta(hours=24),
                    "description": "Final walkthrough must be completed within 24 hours of closing",
                    "critical": False
                }
            ])
        
        elif transaction_type == "wholesale":
            deadlines.extend([
                {
                    "name": "Assignment Document Preparation",
                    "date": closing_date - timedelta(days=3),
                    "description": "Assignment documents must be prepared",
                    "critical": True
                },
                {
                    "name": "End Buyer Funds Verification",
                    "date": closing_date - timedelta(days=2),
                    "description": "End buyer funds must be verified",
                    "critical": True
                }
            ])
        
        return deadlines
    
    def get_closing_coordination(self, coordination_id: UUID) -> Optional[ClosingCoordination]:
        """Get closing coordination by ID."""
        return self.closings.get(coordination_id)
    
    def get_coordination_by_transaction(self, transaction_id: UUID) -> Optional[ClosingCoordination]:
        """Get closing coordination by transaction ID."""
        for coordination in self.closings.values():
            if coordination.transaction_id == transaction_id:
                return coordination
        return None
    
    def update_party_attendance(self, coordination_id: UUID, party_name: str,
                               confirmed: bool) -> bool:
        """Update party attendance confirmation."""
        coordination = self.closings.get(coordination_id)
        if not coordination:
            return False
        
        if confirmed and party_name not in coordination.confirmed_attendees:
            coordination.confirmed_attendees.append(party_name)
        elif not confirmed and party_name in coordination.confirmed_attendees:
            coordination.confirmed_attendees.remove(party_name)
        
        coordination.updated_at = datetime.now()
        return True
    
    def add_document(self, coordination_id: UUID, document_info: Dict[str, Any]) -> bool:
        """Add a prepared document to the closing coordination."""
        coordination = self.closings.get(coordination_id)
        if not coordination:
            return False
        
        document = {
            "id": str(uuid4()),
            "name": document_info.get("name", ""),
            "type": document_info.get("type", ""),
            "prepared_by": document_info.get("prepared_by", ""),
            "prepared_at": datetime.now().isoformat(),
            "status": "prepared",
            "review_status": "pending",
            "url": document_info.get("url", ""),
            "notes": document_info.get("notes", "")
        }
        
        coordination.prepared_documents.append(document)
        
        # Update document review status
        doc_name = document["name"]
        if doc_name in coordination.required_documents:
            coordination.document_review_status[doc_name] = "prepared"
        
        coordination.updated_at = datetime.now()
        return True
    
    def review_document(self, coordination_id: UUID, document_id: str,
                       reviewer: str, status: str, notes: Optional[str] = None) -> bool:
        """Review a closing document."""
        coordination = self.closings.get(coordination_id)
        if not coordination:
            return False
        
        # Find document
        document = next(
            (doc for doc in coordination.prepared_documents if doc["id"] == document_id),
            None
        )
        if not document:
            return False
        
        # Update document review
        document["review_status"] = status
        document["reviewed_by"] = reviewer
        document["reviewed_at"] = datetime.now().isoformat()
        
        if notes:
            document["review_notes"] = notes
        
        # Update overall document status
        doc_name = document["name"]
        coordination.document_review_status[doc_name] = status
        
        coordination.updated_at = datetime.now()
        return True
    
    def set_funds_requirement(self, coordination_id: UUID, party: str, amount: float) -> bool:
        """Set funds requirement for a party."""
        coordination = self.closings.get(coordination_id)
        if not coordination:
            return False
        
        coordination.funds_required[party] = amount
        coordination.funds_confirmed[party] = False  # Reset confirmation
        coordination.updated_at = datetime.now()
        return True
    
    def confirm_funds(self, coordination_id: UUID, party: str, confirmed: bool) -> bool:
        """Confirm funds availability for a party."""
        coordination = self.closings.get(coordination_id)
        if not coordination:
            return False
        
        coordination.funds_confirmed[party] = confirmed
        coordination.updated_at = datetime.now()
        return True
    
    def add_wire_instructions(self, coordination_id: UUID, 
                             wire_info: Dict[str, Any]) -> bool:
        """Add wire transfer instructions."""
        coordination = self.closings.get(coordination_id)
        if not coordination:
            return False
        
        wire_instruction = {
            "id": str(uuid4()),
            "party": wire_info.get("party", ""),
            "bank_name": wire_info.get("bank_name", ""),
            "routing_number": wire_info.get("routing_number", ""),
            "account_number": wire_info.get("account_number", ""),
            "amount": wire_info.get("amount", 0.0),
            "reference": wire_info.get("reference", ""),
            "deadline": wire_info.get("deadline", ""),
            "created_at": datetime.now().isoformat()
        }
        
        coordination.wire_instructions.append(wire_instruction)
        coordination.updated_at = datetime.now()
        return True
    
    def schedule_walkthrough(self, coordination_id: UUID, walkthrough_date: datetime) -> bool:
        """Schedule final walkthrough."""
        coordination = self.closings.get(coordination_id)
        if not coordination:
            return False
        
        coordination.walkthrough_scheduled = True
        coordination.walkthrough_date = walkthrough_date
        coordination.updated_at = datetime.now()
        return True
    
    def complete_walkthrough(self, coordination_id: UUID, issues: Optional[List[str]] = None) -> bool:
        """Mark walkthrough as completed."""
        coordination = self.closings.get(coordination_id)
        if not coordination:
            return False
        
        coordination.walkthrough_completed = True
        if issues:
            coordination.walkthrough_issues.extend(issues)
        
        coordination.updated_at = datetime.now()
        return True
    
    def update_task_status(self, coordination_id: UUID, task_id: UUID, 
                          status: TaskStatus, notes: Optional[str] = None) -> bool:
        """Update the status of a timeline task."""
        coordination = self.closings.get(coordination_id)
        if not coordination:
            return False
        
        task = next(
            (task for task in coordination.timeline_tasks if task.id == task_id),
            None
        )
        if not task:
            return False
        
        old_status = task.status
        task.status = status
        task.updated_at = datetime.now()
        
        if status == TaskStatus.COMPLETED and old_status != TaskStatus.COMPLETED:
            task.completed_at = datetime.now()
            task.progress_percentage = 100
        elif status == TaskStatus.IN_PROGRESS and old_status == TaskStatus.PENDING:
            task.started_at = datetime.now()
        
        if notes:
            task.notes.append(f"{datetime.now().isoformat()}: {notes}")
        
        # Update overall coordination status
        self._update_coordination_status(coordination)
        
        return True
    
    def _update_coordination_status(self, coordination: ClosingCoordination):
        """Update overall coordination status based on task completion and readiness."""
        total_tasks = len(coordination.timeline_tasks)
        completed_tasks = len([t for t in coordination.timeline_tasks if t.status == TaskStatus.COMPLETED])
        
        # Check document readiness
        total_docs = len(coordination.required_documents)
        prepared_docs = len([d for d in coordination.prepared_documents])
        reviewed_docs = len([
            status for status in coordination.document_review_status.values()
            if status in ["approved", "reviewed"]
        ])
        
        # Check funds readiness
        funds_ready = all(coordination.funds_confirmed.values()) if coordination.funds_confirmed else False
        
        # Check attendance confirmation
        required_attendees = [a for a in coordination.required_attendees if a.get("required", True)]
        confirmed_count = len(coordination.confirmed_attendees)
        attendance_ready = confirmed_count >= len(required_attendees)
        
        # Determine status
        if (completed_tasks == total_tasks and 
            reviewed_docs >= total_docs * 0.9 and  # 90% of docs reviewed
            funds_ready and 
            attendance_ready):
            coordination.coordination_status = "ready"
        elif (completed_tasks >= total_tasks * 0.8 and  # 80% of tasks done
              prepared_docs >= total_docs * 0.8):  # 80% of docs prepared
            coordination.coordination_status = "coordinating"
        else:
            coordination.coordination_status = "planning"
        
        coordination.updated_at = datetime.now()
    
    def get_overdue_tasks(self, coordination_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get overdue closing tasks."""
        overdue_tasks = []
        current_time = datetime.now()
        
        coordinations = (
            [self.closings[coordination_id]] if coordination_id and coordination_id in self.closings
            else list(self.closings.values())
        )
        
        for coordination in coordinations:
            for task in coordination.timeline_tasks:
                if (task.due_date and 
                    task.due_date < current_time and 
                    task.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]):
                    
                    days_overdue = (current_time - task.due_date).days
                    overdue_tasks.append({
                        "coordination_id": coordination.id,
                        "task_id": task.id,
                        "task_name": task.name,
                        "due_date": task.due_date,
                        "days_overdue": days_overdue,
                        "priority": task.priority,
                        "assigned_to_type": task.assigned_to_type,
                        "closing_date": coordination.closing_date,
                        "transaction_id": coordination.transaction_id
                    })
        
        return sorted(overdue_tasks, key=lambda x: x["days_overdue"], reverse=True)
    
    def get_upcoming_deadlines(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming critical deadlines."""
        upcoming_deadlines = []
        cutoff_date = datetime.now() + timedelta(days=days_ahead)
        
        for coordination in self.closings.values():
            for deadline in coordination.critical_deadlines:
                deadline_date = datetime.fromisoformat(deadline["date"]) if isinstance(deadline["date"], str) else deadline["date"]
                
                if datetime.now() <= deadline_date <= cutoff_date:
                    days_until = (deadline_date - datetime.now()).days
                    upcoming_deadlines.append({
                        "coordination_id": coordination.id,
                        "transaction_id": coordination.transaction_id,
                        "deadline_name": deadline["name"],
                        "deadline_date": deadline_date,
                        "days_until": days_until,
                        "description": deadline["description"],
                        "critical": deadline["critical"],
                        "closing_date": coordination.closing_date
                    })
        
        return sorted(upcoming_deadlines, key=lambda x: x["deadline_date"])
    
    def generate_closing_checklist(self, coordination_id: UUID) -> Optional[Dict[str, Any]]:
        """Generate a comprehensive closing checklist."""
        coordination = self.closings.get(coordination_id)
        if not coordination:
            return None
        
        # Task status summary
        task_summary = {
            "total": len(coordination.timeline_tasks),
            "completed": len([t for t in coordination.timeline_tasks if t.status == TaskStatus.COMPLETED]),
            "in_progress": len([t for t in coordination.timeline_tasks if t.status == TaskStatus.IN_PROGRESS]),
            "pending": len([t for t in coordination.timeline_tasks if t.status == TaskStatus.PENDING]),
            "overdue": len([t for t in coordination.timeline_tasks if t.status == TaskStatus.OVERDUE])
        }
        
        # Document status summary
        doc_summary = {
            "required": len(coordination.required_documents),
            "prepared": len(coordination.prepared_documents),
            "reviewed": len([s for s in coordination.document_review_status.values() if s in ["approved", "reviewed"]]),
            "pending": len([s for s in coordination.document_review_status.values() if s == "pending"])
        }
        
        # Funds status summary
        funds_summary = {
            "total_required": sum(coordination.funds_required.values()),
            "parties_confirmed": len([c for c in coordination.funds_confirmed.values() if c]),
            "parties_pending": len([c for c in coordination.funds_confirmed.values() if not c])
        }
        
        # Attendance status
        attendance_summary = {
            "required_attendees": len([a for a in coordination.required_attendees if a.get("required", True)]),
            "confirmed_attendees": len(coordination.confirmed_attendees),
            "pending_confirmations": len([a for a in coordination.required_attendees if a.get("required", True)]) - len(coordination.confirmed_attendees)
        }
        
        # Readiness assessment
        readiness_score = 0
        max_score = 4
        
        if task_summary["completed"] / task_summary["total"] >= 0.9:
            readiness_score += 1
        if doc_summary["reviewed"] / doc_summary["required"] >= 0.9:
            readiness_score += 1
        if funds_summary["parties_confirmed"] == len(coordination.funds_required):
            readiness_score += 1
        if attendance_summary["pending_confirmations"] == 0:
            readiness_score += 1
        
        readiness_percentage = int((readiness_score / max_score) * 100)
        
        # Issues and recommendations
        issues = []
        recommendations = []
        
        if task_summary["overdue"] > 0:
            issues.append(f"{task_summary['overdue']} overdue tasks")
            recommendations.append("Address overdue tasks immediately")
        
        if doc_summary["pending"] > 0:
            issues.append(f"{doc_summary['pending']} documents pending review")
            recommendations.append("Complete document review process")
        
        if funds_summary["parties_pending"] > 0:
            issues.append(f"{funds_summary['parties_pending']} parties have not confirmed funds")
            recommendations.append("Confirm funds availability with all parties")
        
        if attendance_summary["pending_confirmations"] > 0:
            issues.append(f"{attendance_summary['pending_confirmations']} attendance confirmations pending")
            recommendations.append("Confirm attendance with all required parties")
        
        if not coordination.walkthrough_scheduled and coordination.closing_date - datetime.now() <= timedelta(days=2):
            issues.append("Final walkthrough not scheduled")
            recommendations.append("Schedule final walkthrough within 24 hours of closing")
        
        return {
            "coordination_id": str(coordination_id),
            "closing_date": coordination.closing_date.isoformat(),
            "coordination_status": coordination.coordination_status,
            "readiness_percentage": readiness_percentage,
            "task_summary": task_summary,
            "document_summary": doc_summary,
            "funds_summary": funds_summary,
            "attendance_summary": attendance_summary,
            "walkthrough_status": {
                "scheduled": coordination.walkthrough_scheduled,
                "completed": coordination.walkthrough_completed,
                "issues_count": len(coordination.walkthrough_issues)
            },
            "issues": issues,
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }
    
    def complete_closing(self, coordination_id: UUID) -> bool:
        """Mark closing as completed."""
        coordination = self.closings.get(coordination_id)
        if not coordination:
            return False
        
        coordination.coordination_status = "completed"
        coordination.completed_at = datetime.now()
        coordination.updated_at = datetime.now()
        
        # Mark all tasks as completed
        for task in coordination.timeline_tasks:
            if task.status != TaskStatus.COMPLETED:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.progress_percentage = 100
        
        return True
    
    def list_closings(self, status: Optional[str] = None,
                     upcoming_days: Optional[int] = None) -> List[ClosingCoordination]:
        """List closing coordinations with optional filtering."""
        closings = list(self.closings.values())
        
        if status:
            closings = [c for c in closings if c.coordination_status == status]
        
        if upcoming_days:
            cutoff_date = datetime.now() + timedelta(days=upcoming_days)
            closings = [c for c in closings if c.closing_date <= cutoff_date]
        
        return sorted(closings, key=lambda c: c.closing_date)
    
    def export_closing_summary(self, coordination_id: UUID) -> Optional[Dict[str, Any]]:
        """Export comprehensive closing summary."""
        coordination = self.closings.get(coordination_id)
        if not coordination:
            return None
        
        return {
            "coordination": coordination.model_dump(),
            "checklist": self.generate_closing_checklist(coordination_id),
            "overdue_tasks": self.get_overdue_tasks(coordination_id),
            "upcoming_deadlines": [
                d for d in self.get_upcoming_deadlines(30)
                if d["coordination_id"] == coordination_id
            ],
            "exported_at": datetime.now().isoformat()
        }