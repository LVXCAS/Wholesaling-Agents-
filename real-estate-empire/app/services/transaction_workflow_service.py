"""
Transaction workflow service.
Handles transaction milestone tracking, progress monitoring, automated task generation,
and deadline monitoring with alert system.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4

from app.models.transaction import (
    TransactionWorkflow, TransactionInstance, TransactionMilestone, TransactionTask,
    TransactionStatus, MilestoneStatus, TaskStatus, TaskPriority, TransactionAlert,
    TransactionReport
)


class TransactionWorkflowService:
    """Service for managing transaction workflows and milestone tracking."""
    
    def __init__(self):
        # In-memory storage for demo - would be replaced with database
        self.workflows: Dict[UUID, TransactionWorkflow] = {}
        self.transactions: Dict[UUID, TransactionInstance] = {}
        self.alerts: Dict[UUID, TransactionAlert] = {}
        
        # Initialize default workflows
        self._initialize_default_workflows()
    
    def _initialize_default_workflows(self):
        """Initialize default transaction workflows."""
        # Purchase workflow
        purchase_workflow = self._create_purchase_workflow()
        self.workflows[purchase_workflow.id] = purchase_workflow
        
        # Wholesale workflow
        wholesale_workflow = self._create_wholesale_workflow()
        self.workflows[wholesale_workflow.id] = wholesale_workflow
    
    def _create_purchase_workflow(self) -> TransactionWorkflow:
        """Create default purchase transaction workflow."""
        workflow = TransactionWorkflow(
            name="Standard Purchase Transaction",
            description="Standard workflow for property purchase transactions",
            transaction_type="purchase",
            default_timeline_days=45
        )
        
        # Define milestones
        milestones = [
            TransactionMilestone(
                name="Contract Execution",
                description="Execute purchase agreement and initial setup",
                order=1,
                estimated_duration=3,
                is_critical=True,
                tasks=[
                    TransactionTask(
                        name="Execute Purchase Agreement",
                        description="Get all parties to sign the purchase agreement",
                        priority=TaskPriority.CRITICAL,
                        task_type="document",
                        required_documents=["purchase_agreement"],
                        completion_criteria=["All parties signed", "Earnest money deposited"]
                    ),
                    TransactionTask(
                        name="Submit Earnest Money",
                        description="Submit earnest money to title company or attorney",
                        priority=TaskPriority.HIGH,
                        task_type="manual",
                        completion_criteria=["Earnest money deposited", "Receipt obtained"]
                    ),
                    TransactionTask(
                        name="Order Title Search",
                        description="Order preliminary title search and commitment",
                        priority=TaskPriority.HIGH,
                        task_type="automated",
                        automation_config={"service": "title_company", "auto_order": True}
                    )
                ]
            ),
            TransactionMilestone(
                name="Due Diligence Period",
                description="Complete property inspections and due diligence",
                order=2,
                estimated_duration=10,
                is_critical=True,
                tasks=[
                    TransactionTask(
                        name="Schedule Property Inspection",
                        description="Schedule and complete property inspection",
                        priority=TaskPriority.HIGH,
                        task_type="manual",
                        completion_criteria=["Inspection scheduled", "Inspection completed", "Report received"]
                    ),
                    TransactionTask(
                        name="Review Property Disclosures",
                        description="Review all property disclosure documents",
                        priority=TaskPriority.MEDIUM,
                        task_type="document",
                        required_documents=["property_disclosures", "seller_disclosures"]
                    ),
                    TransactionTask(
                        name="Verify Property Taxes",
                        description="Verify current property tax information",
                        priority=TaskPriority.MEDIUM,
                        task_type="automated",
                        automation_config={"service": "tax_records", "auto_verify": True}
                    )
                ]
            ),
            TransactionMilestone(
                name="Financing Approval",
                description="Secure financing and complete loan approval",
                order=3,
                estimated_duration=21,
                is_critical=True,
                can_run_parallel=True,
                tasks=[
                    TransactionTask(
                        name="Submit Loan Application",
                        description="Submit complete loan application to lender",
                        priority=TaskPriority.CRITICAL,
                        task_type="document",
                        required_documents=["loan_application", "financial_documents", "employment_verification"]
                    ),
                    TransactionTask(
                        name="Order Appraisal",
                        description="Order property appraisal through lender",
                        priority=TaskPriority.HIGH,
                        task_type="automated",
                        automation_config={"service": "lender", "trigger": "loan_application_submitted"}
                    ),
                    TransactionTask(
                        name="Provide Additional Documentation",
                        description="Provide any additional documentation requested by lender",
                        priority=TaskPriority.HIGH,
                        task_type="document"
                    ),
                    TransactionTask(
                        name="Receive Loan Approval",
                        description="Receive final loan approval and commitment letter",
                        priority=TaskPriority.CRITICAL,
                        task_type="approval",
                        completion_criteria=["Loan approved", "Commitment letter received", "Conditions satisfied"]
                    )
                ]
            ),
            TransactionMilestone(
                name="Pre-Closing Preparation",
                description="Prepare for closing and coordinate final details",
                order=4,
                estimated_duration=7,
                is_critical=True,
                tasks=[
                    TransactionTask(
                        name="Review Title Commitment",
                        description="Review title commitment and resolve any issues",
                        priority=TaskPriority.HIGH,
                        task_type="document",
                        required_documents=["title_commitment"]
                    ),
                    TransactionTask(
                        name="Coordinate Closing Date",
                        description="Coordinate closing date with all parties",
                        priority=TaskPriority.HIGH,
                        task_type="manual",
                        completion_criteria=["Date confirmed with all parties", "Closing scheduled"]
                    ),
                    TransactionTask(
                        name="Prepare Closing Documents",
                        description="Prepare all closing documents and statements",
                        priority=TaskPriority.HIGH,
                        task_type="automated",
                        automation_config={"service": "title_company", "auto_prepare": True}
                    ),
                    TransactionTask(
                        name="Final Walkthrough",
                        description="Complete final walkthrough of property",
                        priority=TaskPriority.MEDIUM,
                        task_type="manual",
                        completion_criteria=["Walkthrough completed", "No issues identified"]
                    )
                ]
            ),
            TransactionMilestone(
                name="Closing",
                description="Complete the closing process",
                order=5,
                estimated_duration=1,
                is_critical=True,
                tasks=[
                    TransactionTask(
                        name="Attend Closing",
                        description="Attend closing and sign all documents",
                        priority=TaskPriority.CRITICAL,
                        task_type="manual",
                        completion_criteria=["All documents signed", "Funds transferred", "Keys received"]
                    ),
                    TransactionTask(
                        name="Record Deed",
                        description="Record deed and transfer ownership",
                        priority=TaskPriority.CRITICAL,
                        task_type="automated",
                        automation_config={"service": "title_company", "auto_record": True}
                    ),
                    TransactionTask(
                        name="Transfer Utilities",
                        description="Transfer utilities to new owner",
                        priority=TaskPriority.MEDIUM,
                        task_type="manual"
                    )
                ]
            )
        ]
        
        workflow.milestones = milestones
        return workflow
    
    def _create_wholesale_workflow(self) -> TransactionWorkflow:
        """Create default wholesale transaction workflow."""
        workflow = TransactionWorkflow(
            name="Wholesale Assignment",
            description="Workflow for wholesale property assignments",
            transaction_type="wholesale",
            default_timeline_days=14
        )
        
        # Define milestones for wholesale
        milestones = [
            TransactionMilestone(
                name="Property Under Contract",
                description="Get property under contract with seller",
                order=1,
                estimated_duration=1,
                is_critical=True,
                tasks=[
                    TransactionTask(
                        name="Execute Purchase Agreement",
                        description="Execute purchase agreement with seller",
                        priority=TaskPriority.CRITICAL,
                        task_type="document",
                        required_documents=["purchase_agreement"]
                    ),
                    TransactionTask(
                        name="Submit Earnest Money",
                        description="Submit minimal earnest money",
                        priority=TaskPriority.HIGH,
                        task_type="manual"
                    )
                ]
            ),
            TransactionMilestone(
                name="Find End Buyer",
                description="Market property and find end buyer",
                order=2,
                estimated_duration=7,
                is_critical=True,
                tasks=[
                    TransactionTask(
                        name="Market Property",
                        description="Market property to investor network",
                        priority=TaskPriority.CRITICAL,
                        task_type="automated",
                        automation_config={"service": "marketing", "auto_distribute": True}
                    ),
                    TransactionTask(
                        name="Screen Potential Buyers",
                        description="Screen and qualify potential buyers",
                        priority=TaskPriority.HIGH,
                        task_type="manual"
                    ),
                    TransactionTask(
                        name="Negotiate Assignment Fee",
                        description="Negotiate assignment fee with end buyer",
                        priority=TaskPriority.HIGH,
                        task_type="manual"
                    )
                ]
            ),
            TransactionMilestone(
                name="Assignment Execution",
                description="Execute assignment agreement",
                order=3,
                estimated_duration=2,
                is_critical=True,
                tasks=[
                    TransactionTask(
                        name="Prepare Assignment Agreement",
                        description="Prepare assignment agreement documents",
                        priority=TaskPriority.CRITICAL,
                        task_type="automated",
                        automation_config={"service": "document_generation", "template": "assignment_agreement"}
                    ),
                    TransactionTask(
                        name="Execute Assignment",
                        description="Get assignment agreement signed by all parties",
                        priority=TaskPriority.CRITICAL,
                        task_type="document",
                        required_documents=["assignment_agreement"]
                    )
                ]
            ),
            TransactionMilestone(
                name="Closing Coordination",
                description="Coordinate closing with all parties",
                order=4,
                estimated_duration=4,
                is_critical=True,
                tasks=[
                    TransactionTask(
                        name="Coordinate with Title Company",
                        description="Coordinate closing with title company",
                        priority=TaskPriority.HIGH,
                        task_type="manual"
                    ),
                    TransactionTask(
                        name="Prepare Closing Documents",
                        description="Ensure all closing documents are prepared",
                        priority=TaskPriority.HIGH,
                        task_type="automated"
                    ),
                    TransactionTask(
                        name="Collect Assignment Fee",
                        description="Collect assignment fee at closing",
                        priority=TaskPriority.CRITICAL,
                        task_type="manual",
                        completion_criteria=["Assignment fee collected", "Transaction completed"]
                    )
                ]
            )
        ]
        
        workflow.milestones = milestones
        return workflow
    
    def create_workflow(self, workflow: TransactionWorkflow) -> TransactionWorkflow:
        """Create a new transaction workflow."""
        if not workflow.id:
            workflow.id = uuid4()
        
        workflow.created_at = datetime.now()
        workflow.updated_at = datetime.now()
        
        self.workflows[workflow.id] = workflow
        return workflow
    
    def get_workflow(self, workflow_id: UUID) -> Optional[TransactionWorkflow]:
        """Get a workflow by ID."""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self, transaction_type: Optional[str] = None, 
                      active_only: bool = True) -> List[TransactionWorkflow]:
        """List available workflows."""
        workflows = list(self.workflows.values())
        
        if active_only:
            workflows = [w for w in workflows if w.is_active]
        
        if transaction_type:
            workflows = [w for w in workflows if w.transaction_type == transaction_type]
        
        return sorted(workflows, key=lambda w: w.name)
    
    def create_transaction(self, workflow_id: UUID, 
                          property_address: str,
                          transaction_type: str,
                          **kwargs) -> TransactionInstance:
        """Create a new transaction instance from a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Create transaction instance
        transaction = TransactionInstance(
            workflow_id=workflow_id,
            property_address=property_address,
            transaction_type=transaction_type,
            **kwargs
        )
        
        # Initialize milestones from workflow
        transaction.current_milestones = [
            self._create_milestone_instance(milestone, transaction.id)
            for milestone in workflow.milestones
        ]
        
        # Set initial timeline
        if transaction.contract_date and not transaction.closing_date:
            transaction.closing_date = (
                transaction.contract_date + 
                timedelta(days=workflow.default_timeline_days)
            )
        
        # Generate initial tasks
        self._generate_initial_tasks(transaction)
        
        # Store transaction
        self.transactions[transaction.id] = transaction
        
        return transaction
    
    def _create_milestone_instance(self, milestone_template: TransactionMilestone, 
                                  transaction_id: UUID) -> TransactionMilestone:
        """Create a milestone instance from template."""
        milestone = TransactionMilestone(
            name=milestone_template.name,
            description=milestone_template.description,
            order=milestone_template.order,
            estimated_duration=milestone_template.estimated_duration,
            is_critical=milestone_template.is_critical,
            can_run_parallel=milestone_template.can_run_parallel,
            auto_start=milestone_template.auto_start,
            auto_complete=milestone_template.auto_complete
        )
        
        # Create task instances and build ID mapping
        task_id_mapping = {}  # old_id -> new_id
        new_tasks = []
        
        for task_template in milestone_template.tasks:
            new_task = self._create_task_instance(task_template, transaction_id)
            task_id_mapping[task_template.id] = new_task.id
            new_tasks.append(new_task)
        
        # Update task dependencies with new IDs
        for i, task_template in enumerate(milestone_template.tasks):
            new_task = new_tasks[i]
            new_task.depends_on = [
                task_id_mapping[dep_id] for dep_id in task_template.depends_on
                if dep_id in task_id_mapping
            ]
            new_task.blocks = [
                task_id_mapping[block_id] for block_id in task_template.blocks
                if block_id in task_id_mapping
            ]
        
        milestone.tasks = new_tasks
        return milestone
    
    def _create_task_instance(self, task_template: TransactionTask, 
                             transaction_id: UUID) -> TransactionTask:
        """Create a task instance from template."""
        task = TransactionTask(
            name=task_template.name,
            description=task_template.description,
            priority=task_template.priority,
            task_type=task_template.task_type,
            automation_config=task_template.automation_config.copy(),
            required_documents=task_template.required_documents.copy(),
            completion_criteria=task_template.completion_criteria.copy(),
            assigned_to_type=task_template.assigned_to_type
        )
        
        return task
    
    def _generate_initial_tasks(self, transaction: TransactionInstance):
        """Generate initial tasks and set due dates."""
        current_date = datetime.now()
        
        for milestone in transaction.current_milestones:
            # Calculate milestone target date
            if milestone.order == 1:
                milestone.target_date = current_date + timedelta(days=milestone.estimated_duration or 1)
            else:
                # Find previous milestone
                prev_milestone = next(
                    (m for m in transaction.current_milestones if m.order == milestone.order - 1),
                    None
                )
                if prev_milestone and prev_milestone.target_date:
                    milestone.target_date = (
                        prev_milestone.target_date + 
                        timedelta(days=milestone.estimated_duration or 1)
                    )
            
            # Set task due dates
            for i, task in enumerate(milestone.tasks):
                if milestone.target_date:
                    # Distribute tasks evenly within milestone duration
                    days_offset = (milestone.estimated_duration or 1) * (i + 1) / len(milestone.tasks)
                    task.due_date = milestone.target_date - timedelta(days=max(0, (milestone.estimated_duration or 1) - days_offset))
        
        # Start first milestone if auto_start is enabled
        first_milestone = next(
            (m for m in transaction.current_milestones if m.order == 1),
            None
        )
        if first_milestone and first_milestone.auto_start:
            self.start_milestone(transaction.id, first_milestone.id)
    
    def get_transaction(self, transaction_id: UUID) -> Optional[TransactionInstance]:
        """Get a transaction by ID."""
        return self.transactions.get(transaction_id)
    
    def list_transactions(self, status: Optional[TransactionStatus] = None,
                         transaction_type: Optional[str] = None,
                         limit: Optional[int] = None) -> List[TransactionInstance]:
        """List transactions with optional filtering."""
        transactions = list(self.transactions.values())
        
        if status:
            transactions = [t for t in transactions if t.status == status]
        
        if transaction_type:
            transactions = [t for t in transactions if t.transaction_type == transaction_type]
        
        # Sort by creation date (newest first)
        transactions.sort(key=lambda t: t.created_at, reverse=True)
        
        if limit:
            transactions = transactions[:limit]
        
        return transactions
    
    def update_transaction_progress(self, transaction_id: UUID) -> Optional[TransactionInstance]:
        """Update transaction progress based on milestone and task completion."""
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            return None
        
        total_milestones = len(transaction.current_milestones)
        completed_milestones = len(transaction.completed_milestones)
        
        # Calculate overall progress
        if total_milestones > 0:
            milestone_progress = (completed_milestones / total_milestones) * 100
            
            # Add partial progress from current milestones
            current_milestone_progress = 0
            active_milestones = [
                m for m in transaction.current_milestones 
                if m.id not in transaction.completed_milestones and m.status == MilestoneStatus.IN_PROGRESS
            ]
            
            for milestone in active_milestones:
                milestone_weight = 1 / total_milestones
                current_milestone_progress += milestone.progress_percentage * milestone_weight
            
            transaction.overall_progress = min(100, int(milestone_progress + current_milestone_progress))
        
        # Update transaction status based on progress
        if transaction.overall_progress == 100:
            transaction.status = TransactionStatus.COMPLETED
            transaction.completed_at = datetime.now()
        elif transaction.overall_progress > 80:
            transaction.status = TransactionStatus.CLOSING_PREP
        elif transaction.overall_progress > 60:
            transaction.status = TransactionStatus.FINANCING
        elif transaction.overall_progress > 40:
            transaction.status = TransactionStatus.DUE_DILIGENCE
        elif transaction.overall_progress > 0:
            transaction.status = TransactionStatus.UNDER_CONTRACT
        
        # Check critical path status
        self._update_critical_path_status(transaction)
        
        transaction.updated_at = datetime.now()
        return transaction
    
    def _update_critical_path_status(self, transaction: TransactionInstance):
        """Update critical path status based on milestone progress."""
        if not transaction.closing_date:
            return
        
        days_to_closing = (transaction.closing_date - datetime.now()).days
        
        # Calculate expected progress based on timeline
        total_days = (transaction.closing_date - transaction.created_at).days
        elapsed_days = (datetime.now() - transaction.created_at).days
        expected_progress = (elapsed_days / total_days) * 100 if total_days > 0 else 0
        
        # Determine critical path status
        progress_difference = transaction.overall_progress - expected_progress
        
        if progress_difference >= 10:
            transaction.critical_path_status = "ahead"
        elif progress_difference >= -5:
            transaction.critical_path_status = "on_track"
        elif progress_difference >= -15:
            transaction.critical_path_status = "at_risk"
        else:
            transaction.critical_path_status = "delayed"
        
        # Generate alerts for at-risk or delayed transactions
        if transaction.critical_path_status in ["at_risk", "delayed"]:
            self._create_timeline_alert(transaction)
    
    def start_milestone(self, transaction_id: UUID, milestone_id: UUID) -> bool:
        """Start a milestone and its initial tasks."""
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            return False
        
        milestone = next(
            (m for m in transaction.current_milestones if m.id == milestone_id),
            None
        )
        if not milestone:
            return False
        
        # Check dependencies
        if milestone.depends_on_milestones:
            for dep_id in milestone.depends_on_milestones:
                if dep_id not in transaction.completed_milestones:
                    return False  # Dependencies not met
        
        # Start milestone
        milestone.status = MilestoneStatus.IN_PROGRESS
        milestone.actual_start_date = datetime.now()
        
        # Start initial tasks (those without dependencies)
        for task in milestone.tasks:
            if not task.depends_on:
                task.status = TaskStatus.IN_PROGRESS
                task.started_at = datetime.now()
                transaction.active_tasks.append(task.id)
        
        transaction.updated_at = datetime.now()
        return True
    
    def complete_milestone(self, transaction_id: UUID, milestone_id: UUID) -> bool:
        """Complete a milestone and start next milestones if applicable."""
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            return False
        
        milestone = next(
            (m for m in transaction.current_milestones if m.id == milestone_id),
            None
        )
        if not milestone:
            return False
        
        # Check if all tasks are completed
        incomplete_tasks = [t for t in milestone.tasks if t.status != TaskStatus.COMPLETED]
        if incomplete_tasks:
            return False  # Cannot complete milestone with incomplete tasks
        
        # Complete milestone
        milestone.status = MilestoneStatus.COMPLETED
        milestone.actual_completion_date = datetime.now()
        milestone.progress_percentage = 100
        transaction.completed_milestones.append(milestone_id)
        
        # Start next milestones if they have auto_start enabled
        next_milestones = [
            m for m in transaction.current_milestones
            if m.order == milestone.order + 1 and m.auto_start
        ]
        
        for next_milestone in next_milestones:
            self.start_milestone(transaction_id, next_milestone.id)
        
        # Update transaction progress
        self.update_transaction_progress(transaction_id)
        
        return True
    
    def complete_task(self, transaction_id: UUID, task_id: UUID, 
                     completion_notes: Optional[str] = None) -> bool:
        """Complete a task and update milestone progress."""
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            return False
        
        # Find task in milestones
        task = None
        milestone = None
        
        for m in transaction.current_milestones:
            for t in m.tasks:
                if t.id == task_id:
                    task = t
                    milestone = m
                    break
            if task:
                break
        
        if not task or not milestone:
            return False
        
        # Complete task
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        task.progress_percentage = 100
        
        if completion_notes:
            task.notes.append(completion_notes)
        
        # Remove from active tasks
        if task_id in transaction.active_tasks:
            transaction.active_tasks.remove(task_id)
        
        # Start dependent tasks
        for dependent_task in milestone.tasks:
            if (task_id in dependent_task.depends_on and 
                dependent_task.status == TaskStatus.PENDING):
                dependent_task.status = TaskStatus.IN_PROGRESS
                dependent_task.started_at = datetime.now()
                transaction.active_tasks.append(dependent_task.id)
        
        # Update milestone progress
        completed_tasks = [t for t in milestone.tasks if t.status == TaskStatus.COMPLETED]
        milestone.progress_percentage = int((len(completed_tasks) / len(milestone.tasks)) * 100)
        
        # Auto-complete milestone if all tasks are done and auto_complete is enabled
        if (milestone.progress_percentage == 100 and 
            milestone.auto_complete and 
            milestone.status != MilestoneStatus.COMPLETED):
            self.complete_milestone(transaction_id, milestone.id)
        
        transaction.updated_at = datetime.now()
        return True
    
    def get_overdue_tasks(self, transaction_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get overdue tasks across transactions."""
        overdue_tasks = []
        current_time = datetime.now()
        
        transactions = (
            [self.transactions[transaction_id]] if transaction_id and transaction_id in self.transactions
            else list(self.transactions.values())
        )
        
        for transaction in transactions:
            for milestone in transaction.current_milestones:
                for task in milestone.tasks:
                    if (task.due_date and 
                        task.due_date < current_time and 
                        task.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]):
                        
                        overdue_tasks.append({
                            "transaction_id": transaction.id,
                            "milestone_id": milestone.id,
                            "task_id": task.id,
                            "task_name": task.name,
                            "due_date": task.due_date,
                            "days_overdue": (current_time - task.due_date).days,
                            "priority": task.priority,
                            "property_address": transaction.property_address
                        })
                        
                        # Update task status to overdue
                        task.status = TaskStatus.OVERDUE
                        if task.id not in transaction.overdue_tasks:
                            transaction.overdue_tasks.append(task.id)
        
        return sorted(overdue_tasks, key=lambda x: x["days_overdue"], reverse=True)
    
    def _create_timeline_alert(self, transaction: TransactionInstance):
        """Create timeline alert for at-risk or delayed transactions."""
        alert = TransactionAlert(
            transaction_id=transaction.id,
            alert_type="timeline",
            severity="high" if transaction.critical_path_status == "delayed" else "medium",
            title=f"Transaction Timeline {transaction.critical_path_status.title()}",
            message=f"Transaction for {transaction.property_address} is {transaction.critical_path_status}",
            action_required=True,
            suggested_actions=[
                "Review milestone progress",
                "Identify bottlenecks",
                "Adjust timeline or resources",
                "Communicate with parties"
            ]
        )
        
        self.alerts[alert.id] = alert
        
        # Add to transaction alerts
        transaction.active_alerts.append({
            "alert_id": str(alert.id),
            "type": alert.alert_type,
            "severity": alert.severity,
            "created_at": alert.created_at.isoformat()
        })
    
    def create_deadline_alert(self, transaction_id: UUID, task_id: UUID, 
                            days_before: int = 3) -> Optional[TransactionAlert]:
        """Create deadline alert for upcoming task due dates."""
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            return None
        
        # Find task
        task = None
        for milestone in transaction.current_milestones:
            for t in milestone.tasks:
                if t.id == task_id:
                    task = t
                    break
            if task:
                break
        
        if not task or not task.due_date:
            return None
        
        # Check if alert should be created
        days_until_due = (task.due_date - datetime.now()).days
        if days_until_due <= days_before and days_until_due > 0:
            alert = TransactionAlert(
                transaction_id=transaction_id,
                alert_type="deadline",
                severity="medium" if days_until_due > 1 else "high",
                title=f"Task Due Soon: {task.name}",
                message=f"Task '{task.name}' is due in {days_until_due} day(s)",
                action_required=True,
                suggested_actions=[
                    "Complete the task",
                    "Update task progress",
                    "Request deadline extension if needed"
                ],
                expires_at=task.due_date
            )
            
            self.alerts[alert.id] = alert
            return alert
        
        return None
    
    def monitor_deadlines(self) -> List[TransactionAlert]:
        """Monitor all transactions for upcoming deadlines and create alerts."""
        new_alerts = []
        
        for transaction in self.transactions.values():
            if transaction.status in [TransactionStatus.COMPLETED, TransactionStatus.CANCELLED]:
                continue
            
            for milestone in transaction.current_milestones:
                for task in milestone.tasks:
                    if task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
                        alert = self.create_deadline_alert(transaction.id, task.id)
                        if alert:
                            new_alerts.append(alert)
        
        return new_alerts
    
    def generate_transaction_report(self, transaction_id: UUID) -> Optional[TransactionReport]:
        """Generate comprehensive transaction status report."""
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            return None
        
        # Calculate timeline analysis
        timeline_analysis = self._analyze_transaction_timeline(transaction)
        
        # Milestone progress
        milestone_progress = []
        for milestone in transaction.current_milestones:
            milestone_progress.append({
                "name": milestone.name,
                "status": milestone.status.value,
                "progress": milestone.progress_percentage,
                "target_date": milestone.target_date.isoformat() if milestone.target_date else None,
                "actual_start": milestone.actual_start_date.isoformat() if milestone.actual_start_date else None,
                "actual_completion": milestone.actual_completion_date.isoformat() if milestone.actual_completion_date else None
            })
        
        # Task summary
        all_tasks = [task for milestone in transaction.current_milestones for task in milestone.tasks]
        task_summary = {
            "total": len(all_tasks),
            "completed": len([t for t in all_tasks if t.status == TaskStatus.COMPLETED]),
            "in_progress": len([t for t in all_tasks if t.status == TaskStatus.IN_PROGRESS]),
            "pending": len([t for t in all_tasks if t.status == TaskStatus.PENDING]),
            "overdue": len([t for t in all_tasks if t.status == TaskStatus.OVERDUE])
        }
        
        # Overdue items
        overdue_items = self.get_overdue_tasks(transaction_id)
        
        # Risk assessment
        risk_assessment = self._assess_transaction_risk(transaction)
        
        report = TransactionReport(
            transaction_id=transaction_id,
            transaction_summary={
                "property_address": transaction.property_address,
                "transaction_type": transaction.transaction_type,
                "purchase_price": transaction.purchase_price,
                "closing_date": transaction.closing_date.isoformat() if transaction.closing_date else None,
                "created_at": transaction.created_at.isoformat()
            },
            current_status=transaction.status,
            overall_progress=transaction.overall_progress,
            timeline_analysis=timeline_analysis,
            critical_path_status=transaction.critical_path_status,
            milestone_progress=milestone_progress,
            task_summary=task_summary,
            overdue_items=overdue_items,
            risk_assessment=risk_assessment
        )
        
        return report
    
    def _analyze_transaction_timeline(self, transaction: TransactionInstance) -> Dict[str, Any]:
        """Analyze transaction timeline and project completion."""
        if not transaction.closing_date:
            return {"status": "no_closing_date"}
        
        current_date = datetime.now()
        days_to_closing = (transaction.closing_date - current_date).days
        
        # Calculate projected completion based on current progress
        if transaction.overall_progress > 0:
            total_days = (transaction.closing_date - transaction.created_at).days
            elapsed_days = (current_date - transaction.created_at).days
            progress_rate = transaction.overall_progress / elapsed_days if elapsed_days > 0 else 0
            
            if progress_rate > 0:
                remaining_progress = 100 - transaction.overall_progress
                projected_days_remaining = remaining_progress / progress_rate
                projected_completion = current_date + timedelta(days=projected_days_remaining)
            else:
                projected_completion = transaction.closing_date
        else:
            projected_completion = transaction.closing_date
        
        return {
            "days_to_closing": days_to_closing,
            "projected_completion": projected_completion.isoformat(),
            "on_schedule": projected_completion <= transaction.closing_date,
            "schedule_variance_days": (projected_completion - transaction.closing_date).days
        }
    
    def _assess_transaction_risk(self, transaction: TransactionInstance) -> Dict[str, Any]:
        """Assess transaction risk factors."""
        risk_factors = []
        risk_level = "low"
        
        # Timeline risk
        if transaction.critical_path_status == "delayed":
            risk_factors.append("Transaction is behind schedule")
            risk_level = "high"
        elif transaction.critical_path_status == "at_risk":
            risk_factors.append("Transaction timeline is at risk")
            risk_level = "medium"
        
        # Overdue tasks risk
        overdue_count = len(transaction.overdue_tasks)
        if overdue_count > 0:
            risk_factors.append(f"{overdue_count} overdue tasks")
            if overdue_count > 3:
                risk_level = "high"
            elif risk_level == "low":
                risk_level = "medium"
        
        # Closing date proximity risk
        if transaction.closing_date:
            days_to_closing = (transaction.closing_date - datetime.now()).days
            if days_to_closing <= 7 and transaction.overall_progress < 90:
                risk_factors.append("Closing date approaching with low completion")
                risk_level = "high"
        
        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "overdue_task_count": overdue_count,
            "critical_path_status": transaction.critical_path_status
        }