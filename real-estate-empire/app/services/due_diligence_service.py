"""
Due diligence management service.
Handles due diligence checklist automation, document request tracking,
finding management, risk assessment, and automated compliance checking.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4

from app.models.transaction import (
    DueDiligenceChecklist, DueDiligenceItem, DocumentStatus, ComplianceStatus,
    TaskPriority, TransactionAlert
)


class DueDiligenceService:
    """Service for managing due diligence processes and compliance."""
    
    def __init__(self):
        # In-memory storage for demo - would be replaced with database
        self.checklists: Dict[UUID, DueDiligenceChecklist] = {}
        self.compliance_rules: Dict[str, Dict[str, Any]] = {}
        self.document_templates: Dict[str, List[str]] = {}
        
        # Initialize default templates and rules
        self._initialize_default_templates()
        self._initialize_compliance_rules()
    
    def _initialize_default_templates(self):
        """Initialize default due diligence templates for different transaction types."""
        
        # Purchase transaction template
        self.document_templates["purchase"] = [
            {
                "name": "Property Inspection Report",
                "description": "Professional property inspection report",
                "category": "physical",
                "priority": TaskPriority.HIGH,
                "required_documents": ["inspection_report", "photos"],
                "is_required": True,
                "risk_level": "high"
            },
            {
                "name": "Title Search and Commitment",
                "description": "Title search results and title commitment",
                "category": "legal",
                "priority": TaskPriority.CRITICAL,
                "required_documents": ["title_search", "title_commitment"],
                "is_required": True,
                "risk_level": "critical"
            },
            {
                "name": "Property Tax Records",
                "description": "Current and historical property tax information",
                "category": "financial",
                "priority": TaskPriority.HIGH,
                "required_documents": ["tax_records", "tax_assessments"],
                "is_required": True,
                "risk_level": "medium"
            },
            {
                "name": "Property Disclosures",
                "description": "All required property disclosure documents",
                "category": "legal",
                "priority": TaskPriority.HIGH,
                "required_documents": ["seller_disclosures", "lead_paint_disclosure"],
                "is_required": True,
                "risk_level": "high"
            },
            {
                "name": "HOA Documents",
                "description": "Homeowners association documents and financials",
                "category": "legal",
                "priority": TaskPriority.MEDIUM,
                "required_documents": ["hoa_bylaws", "hoa_financials", "hoa_meeting_minutes"],
                "is_required": False,
                "risk_level": "medium"
            },
            {
                "name": "Utility Records",
                "description": "Utility usage and cost history",
                "category": "financial",
                "priority": TaskPriority.MEDIUM,
                "required_documents": ["utility_bills", "utility_history"],
                "is_required": False,
                "risk_level": "low"
            },
            {
                "name": "Environmental Assessment",
                "description": "Environmental hazard assessment",
                "category": "environmental",
                "priority": TaskPriority.MEDIUM,
                "required_documents": ["environmental_report"],
                "is_required": False,
                "risk_level": "high"
            },
            {
                "name": "Survey and Boundary Information",
                "description": "Property survey and boundary documentation",
                "category": "physical",
                "priority": TaskPriority.MEDIUM,
                "required_documents": ["property_survey", "boundary_map"],
                "is_required": False,
                "risk_level": "medium"
            },
            {
                "name": "Zoning and Permits",
                "description": "Zoning information and building permits",
                "category": "legal",
                "priority": TaskPriority.MEDIUM,
                "required_documents": ["zoning_certificate", "building_permits"],
                "is_required": True,
                "risk_level": "medium"
            },
            {
                "name": "Insurance Information",
                "description": "Property insurance history and claims",
                "category": "financial",
                "priority": TaskPriority.MEDIUM,
                "required_documents": ["insurance_history", "claims_history"],
                "is_required": False,
                "risk_level": "medium"
            }
        ]
        
        # Wholesale transaction template (simplified)
        self.document_templates["wholesale"] = [
            {
                "name": "Property Condition Assessment",
                "description": "Basic property condition evaluation",
                "category": "physical",
                "priority": TaskPriority.HIGH,
                "required_documents": ["condition_photos", "repair_estimates"],
                "is_required": True,
                "risk_level": "high"
            },
            {
                "name": "Title Verification",
                "description": "Basic title verification",
                "category": "legal",
                "priority": TaskPriority.HIGH,
                "required_documents": ["title_search"],
                "is_required": True,
                "risk_level": "high"
            },
            {
                "name": "Market Analysis",
                "description": "Comparable sales and market analysis",
                "category": "financial",
                "priority": TaskPriority.HIGH,
                "required_documents": ["comps", "market_analysis"],
                "is_required": True,
                "risk_level": "medium"
            },
            {
                "name": "Property Tax Status",
                "description": "Current property tax status",
                "category": "financial",
                "priority": TaskPriority.MEDIUM,
                "required_documents": ["tax_status"],
                "is_required": True,
                "risk_level": "medium"
            }
        ]
    
    def _initialize_compliance_rules(self):
        """Initialize compliance rules for different jurisdictions and transaction types."""
        
        # Federal compliance rules
        self.compliance_rules["federal"] = {
            "lead_paint_disclosure": {
                "applies_to": "properties_built_before_1978",
                "required": True,
                "deadline_days": 10,
                "description": "Lead-based paint disclosure required for pre-1978 properties"
            },
            "fair_housing": {
                "applies_to": "all_transactions",
                "required": True,
                "deadline_days": 0,
                "description": "Fair housing compliance required for all transactions"
            }
        }
        
        # State compliance rules (example for multiple states)
        self.compliance_rules["state"] = {
            "property_disclosure": {
                "applies_to": "residential_sales",
                "required": True,
                "deadline_days": 5,
                "description": "Property condition disclosure required"
            },
            "septic_inspection": {
                "applies_to": "properties_with_septic",
                "required": True,
                "deadline_days": 15,
                "description": "Septic system inspection required"
            }
        }
        
        # Local compliance rules
        self.compliance_rules["local"] = {
            "occupancy_permit": {
                "applies_to": "rental_properties",
                "required": True,
                "deadline_days": 30,
                "description": "Certificate of occupancy required for rental properties"
            }
        }
    
    def create_checklist(self, transaction_id: UUID, transaction_type: str,
                        property_details: Optional[Dict[str, Any]] = None) -> DueDiligenceChecklist:
        """Create a due diligence checklist for a transaction."""
        
        checklist = DueDiligenceChecklist(
            transaction_id=transaction_id,
            name=f"Due Diligence - {transaction_type.title()}",
            description=f"Due diligence checklist for {transaction_type} transaction"
        )
        
        # Get template items for transaction type
        template_items = self.document_templates.get(transaction_type, [])
        
        # Create checklist items from template
        for template in template_items:
            # Check if item applies to this property
            if self._item_applies_to_property(template, property_details):
                item = DueDiligenceItem(
                    name=template["name"],
                    description=template["description"],
                    category=template["category"],
                    priority=template["priority"],
                    required_documents=template["required_documents"].copy(),
                    is_required=template["is_required"],
                    risk_level=template["risk_level"]
                )
                
                # Set due date based on priority (ensure future dates)
                if item.priority == TaskPriority.CRITICAL:
                    item.due_date = datetime.now() + timedelta(days=3)
                elif item.priority == TaskPriority.HIGH:
                    item.due_date = datetime.now() + timedelta(days=7)
                elif item.priority == TaskPriority.MEDIUM:
                    item.due_date = datetime.now() + timedelta(days=14)
                else:
                    item.due_date = datetime.now() + timedelta(days=21)
                
                checklist.items.append(item)
        
        # Add compliance-based items
        compliance_items = self._generate_compliance_items(transaction_type, property_details)
        checklist.items.extend(compliance_items)
        
        # Update checklist totals
        checklist.total_items = len(checklist.items)
        
        # Store checklist
        self.checklists[checklist.id] = checklist
        
        return checklist
    
    def _item_applies_to_property(self, template: Dict[str, Any], 
                                 property_details: Optional[Dict[str, Any]]) -> bool:
        """Check if a template item applies to the specific property."""
        if not property_details:
            return True
        
        # Example logic for conditional items
        if template["name"] == "HOA Documents":
            return property_details.get("has_hoa", False)
        
        if template["name"] == "Environmental Assessment":
            # Require for commercial or properties near industrial areas
            return (property_details.get("property_type") == "commercial" or
                   property_details.get("near_industrial", False))
        
        return True
    
    def _generate_compliance_items(self, transaction_type: str,
                                  property_details: Optional[Dict[str, Any]]) -> List[DueDiligenceItem]:
        """Generate compliance-based due diligence items."""
        compliance_items = []
        
        # Check federal compliance
        for rule_name, rule in self.compliance_rules["federal"].items():
            if self._compliance_applies(rule, transaction_type, property_details):
                item = DueDiligenceItem(
                    name=f"Federal Compliance: {rule_name.replace('_', ' ').title()}",
                    description=rule["description"],
                    category="compliance",
                    priority=TaskPriority.CRITICAL,
                    is_required=rule["required"],
                    due_date=datetime.now() + timedelta(days=max(1, rule["deadline_days"])),  # Ensure at least 1 day
                    risk_level="critical"
                )
                compliance_items.append(item)
        
        # Check state compliance
        for rule_name, rule in self.compliance_rules["state"].items():
            if self._compliance_applies(rule, transaction_type, property_details):
                item = DueDiligenceItem(
                    name=f"State Compliance: {rule_name.replace('_', ' ').title()}",
                    description=rule["description"],
                    category="compliance",
                    priority=TaskPriority.HIGH,
                    is_required=rule["required"],
                    due_date=datetime.now() + timedelta(days=max(1, rule["deadline_days"])),  # Ensure at least 1 day
                    risk_level="high"
                )
                compliance_items.append(item)
        
        return compliance_items
    
    def _compliance_applies(self, rule: Dict[str, Any], transaction_type: str,
                           property_details: Optional[Dict[str, Any]]) -> bool:
        """Check if a compliance rule applies to the transaction."""
        applies_to = rule["applies_to"]
        
        if applies_to == "all_transactions":
            return True
        
        if applies_to == "residential_sales" and transaction_type in ["purchase", "wholesale"]:
            return True
        
        if applies_to == "properties_built_before_1978" and property_details:
            year_built = property_details.get("year_built")
            return year_built and year_built < 1978
        
        if applies_to == "properties_with_septic" and property_details:
            return property_details.get("has_septic", False)
        
        if applies_to == "rental_properties" and property_details:
            return property_details.get("intended_use") == "rental"
        
        return False
    
    def get_checklist(self, checklist_id: UUID) -> Optional[DueDiligenceChecklist]:
        """Get a due diligence checklist by ID."""
        return self.checklists.get(checklist_id)
    
    def get_checklist_by_transaction(self, transaction_id: UUID) -> Optional[DueDiligenceChecklist]:
        """Get due diligence checklist for a transaction."""
        for checklist in self.checklists.values():
            if checklist.transaction_id == transaction_id:
                return checklist
        return None
    
    def update_item_status(self, checklist_id: UUID, item_id: UUID,
                          status: DocumentStatus, notes: Optional[str] = None) -> bool:
        """Update the status of a due diligence item."""
        checklist = self.checklists.get(checklist_id)
        if not checklist:
            return False
        
        item = next((item for item in checklist.items if item.id == item_id), None)
        if not item:
            return False
        
        # Update item status
        old_status = item.status
        item.status = status
        item.updated_at = datetime.now()
        
        if notes:
            item.review_notes.append(f"{datetime.now().isoformat()}: {notes}")
        
        # Update completion tracking
        if status == DocumentStatus.APPROVED and old_status != DocumentStatus.APPROVED:
            item.completed_at = datetime.now()
            item.completion_percentage = 100
        elif status != DocumentStatus.APPROVED and old_status == DocumentStatus.APPROVED:
            item.completed_at = None
            item.completion_percentage = 0
        
        # Update checklist progress
        self._update_checklist_progress(checklist)
        
        return True
    
    def add_document(self, checklist_id: UUID, item_id: UUID,
                    document_info: Dict[str, Any]) -> bool:
        """Add a document to a due diligence item."""
        checklist = self.checklists.get(checklist_id)
        if not checklist:
            return False
        
        item = next((item for item in checklist.items if item.id == item_id), None)
        if not item:
            return False
        
        # Add document
        document = {
            "id": str(uuid4()),
            "name": document_info.get("name", ""),
            "type": document_info.get("type", ""),
            "url": document_info.get("url", ""),
            "uploaded_at": datetime.now().isoformat(),
            "uploaded_by": document_info.get("uploaded_by", ""),
            "size": document_info.get("size", 0),
            "status": "received"
        }
        
        item.received_documents.append(document)
        
        # Update item status if it was required or requested
        if item.status in [DocumentStatus.REQUIRED, DocumentStatus.REQUESTED]:
            item.status = DocumentStatus.RECEIVED
        
        item.updated_at = datetime.now()
        
        # Update checklist progress
        self._update_checklist_progress(checklist)
        
        return True
    
    def request_documents(self, checklist_id: UUID, item_id: UUID,
                         recipient: str, message: Optional[str] = None) -> bool:
        """Request documents for a due diligence item."""
        checklist = self.checklists.get(checklist_id)
        if not checklist:
            return False
        
        item = next((item for item in checklist.items if item.id == item_id), None)
        if not item:
            return False
        
        # Update item status
        item.status = DocumentStatus.REQUESTED
        item.updated_at = datetime.now()
        
        # Add request note
        request_note = f"Documents requested from {recipient}"
        if message:
            request_note += f": {message}"
        item.review_notes.append(f"{datetime.now().isoformat()}: {request_note}")
        
        # In a real implementation, this would send actual requests
        # For now, we'll just log the request
        
        return True
    
    def review_item(self, checklist_id: UUID, item_id: UUID,
                   reviewer: str, review_result: str, notes: str) -> bool:
        """Review a due diligence item."""
        checklist = self.checklists.get(checklist_id)
        if not checklist:
            return False
        
        item = next((item for item in checklist.items if item.id == item_id), None)
        if not item:
            return False
        
        # Update item with review
        item.reviewer = reviewer
        item.review_notes.append(f"{datetime.now().isoformat()}: {notes}")
        
        if review_result.lower() == "approved":
            item.status = DocumentStatus.APPROVED
            item.approved_by = reviewer
            item.approved_at = datetime.now()
            item.completed_at = datetime.now()
            item.completion_percentage = 100
        elif review_result.lower() == "rejected":
            item.status = DocumentStatus.REJECTED
        else:
            item.status = DocumentStatus.REVIEWED
        
        item.updated_at = datetime.now()
        
        # Update checklist progress
        self._update_checklist_progress(checklist)
        
        return True
    
    def _update_checklist_progress(self, checklist: DueDiligenceChecklist):
        """Update checklist progress and risk assessment."""
        if not checklist.items:
            return
        
        # Update completion counts
        completed_items = [
            item for item in checklist.items 
            if item.status == DocumentStatus.APPROVED
        ]
        checklist.completed_items = len(completed_items)
        checklist.completion_percentage = int(
            (checklist.completed_items / checklist.total_items) * 100
        )
        
        # Update overall risk level
        risk_levels = [item.risk_level for item in checklist.items]
        if "critical" in risk_levels:
            checklist.overall_risk_level = "critical"
        elif "high" in risk_levels:
            checklist.overall_risk_level = "high"
        elif "medium" in risk_levels:
            checklist.overall_risk_level = "medium"
        else:
            checklist.overall_risk_level = "low"
        
        # Identify risks from incomplete critical/high items
        checklist.identified_risks = []
        for item in checklist.items:
            if (item.status not in [DocumentStatus.APPROVED, DocumentStatus.REVIEWED] and
                item.risk_level in ["critical", "high"]):
                checklist.identified_risks.append(
                    f"Missing {item.name} ({item.risk_level} risk)"
                )
        
        # Update compliance status
        self._update_compliance_status(checklist)
        
        checklist.updated_at = datetime.now()
        
        # Mark as completed if all required items are done
        if checklist.completion_percentage == 100:
            checklist.completed_at = datetime.now()
    
    def _update_compliance_status(self, checklist: DueDiligenceChecklist):
        """Update compliance status based on completed items."""
        compliance_items = [
            item for item in checklist.items 
            if item.category == "compliance"
        ]
        
        if not compliance_items:
            checklist.compliance_status = ComplianceStatus.COMPLIANT
            return
        
        # Check if all compliance items are approved
        approved_compliance = [
            item for item in compliance_items
            if item.status == DocumentStatus.APPROVED
        ]
        
        rejected_compliance = [
            item for item in compliance_items
            if item.status == DocumentStatus.REJECTED
        ]
        
        if rejected_compliance:
            checklist.compliance_status = ComplianceStatus.NON_COMPLIANT
            checklist.compliance_notes.append(
                f"Non-compliant items: {', '.join([item.name for item in rejected_compliance])}"
            )
        elif len(approved_compliance) == len(compliance_items):
            checklist.compliance_status = ComplianceStatus.COMPLIANT
        else:
            checklist.compliance_status = ComplianceStatus.PENDING
    
    def get_overdue_items(self, checklist_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get overdue due diligence items."""
        overdue_items = []
        current_time = datetime.now()
        
        checklists = (
            [self.checklists[checklist_id]] if checklist_id and checklist_id in self.checklists
            else list(self.checklists.values())
        )
        
        for checklist in checklists:
            for item in checklist.items:
                if (item.due_date and 
                    item.due_date < current_time and 
                    item.status not in [DocumentStatus.APPROVED, DocumentStatus.REVIEWED]):
                    
                    days_overdue = (current_time - item.due_date).days
                    overdue_items.append({
                        "checklist_id": checklist.id,
                        "item_id": item.id,
                        "item_name": item.name,
                        "category": item.category,
                        "due_date": item.due_date,
                        "days_overdue": days_overdue,
                        "priority": item.priority,
                        "risk_level": item.risk_level,
                        "transaction_id": checklist.transaction_id
                    })
        
        return sorted(overdue_items, key=lambda x: x["days_overdue"], reverse=True)
    
    def get_items_by_category(self, checklist_id: UUID, 
                             category: str) -> List[DueDiligenceItem]:
        """Get due diligence items by category."""
        checklist = self.checklists.get(checklist_id)
        if not checklist:
            return []
        
        return [item for item in checklist.items if item.category == category]
    
    def get_items_by_status(self, checklist_id: UUID,
                           status: DocumentStatus) -> List[DueDiligenceItem]:
        """Get due diligence items by status."""
        checklist = self.checklists.get(checklist_id)
        if not checklist:
            return []
        
        return [item for item in checklist.items if item.status == status]
    
    def generate_risk_report(self, checklist_id: UUID) -> Optional[Dict[str, Any]]:
        """Generate a comprehensive risk assessment report."""
        checklist = self.checklists.get(checklist_id)
        if not checklist:
            return None
        
        # Categorize risks
        risk_categories = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        for item in checklist.items:
            if item.status not in [DocumentStatus.APPROVED]:
                risk_categories[item.risk_level].append({
                    "name": item.name,
                    "category": item.category,
                    "status": item.status.value,
                    "due_date": item.due_date.isoformat() if item.due_date else None,
                    "overdue": item.due_date < datetime.now() if item.due_date else False
                })
        
        # Calculate risk score
        risk_score = 0
        for item in checklist.items:
            if item.status not in [DocumentStatus.APPROVED]:
                if item.risk_level == "critical":
                    risk_score += 10
                elif item.risk_level == "high":
                    risk_score += 5
                elif item.risk_level == "medium":
                    risk_score += 2
                else:
                    risk_score += 1
        
        # Determine overall risk level
        if risk_score >= 20:
            overall_risk = "critical"
        elif risk_score >= 10:
            overall_risk = "high"
        elif risk_score >= 5:
            overall_risk = "medium"
        else:
            overall_risk = "low"
        
        # Generate recommendations
        recommendations = []
        if risk_categories["critical"]:
            recommendations.append("Address critical risk items immediately")
        if risk_categories["high"]:
            recommendations.append("Prioritize high-risk items for completion")
        
        overdue_count = len(self.get_overdue_items(checklist_id))
        if overdue_count > 0:
            recommendations.append(f"Address {overdue_count} overdue items")
        
        return {
            "checklist_id": str(checklist_id),
            "overall_risk_level": overall_risk,
            "risk_score": risk_score,
            "risk_categories": risk_categories,
            "completion_percentage": checklist.completion_percentage,
            "compliance_status": checklist.compliance_status.value,
            "overdue_items_count": overdue_count,
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }
    
    def auto_check_compliance(self, checklist_id: UUID) -> Dict[str, Any]:
        """Automatically check compliance status and generate alerts."""
        checklist = self.checklists.get(checklist_id)
        if not checklist:
            return {"error": "Checklist not found"}
        
        compliance_issues = []
        warnings = []
        
        # Check for missing required documents
        required_items = [item for item in checklist.items if item.is_required]
        missing_required = [
            item for item in required_items
            if item.status not in [DocumentStatus.APPROVED, DocumentStatus.REVIEWED]
        ]
        
        for item in missing_required:
            if item.due_date and item.due_date < datetime.now():
                compliance_issues.append(f"Overdue required item: {item.name}")
            else:
                warnings.append(f"Missing required item: {item.name}")
        
        # Check compliance-specific items
        compliance_items = [item for item in checklist.items if item.category == "compliance"]
        for item in compliance_items:
            if item.status == DocumentStatus.REJECTED:
                compliance_issues.append(f"Non-compliant: {item.name}")
            elif item.status not in [DocumentStatus.APPROVED, DocumentStatus.REVIEWED]:
                if item.due_date and item.due_date < datetime.now():
                    compliance_issues.append(f"Overdue compliance item: {item.name}")
                else:
                    warnings.append(f"Pending compliance item: {item.name}")
        
        # Update compliance status
        if compliance_issues:
            checklist.compliance_status = ComplianceStatus.NON_COMPLIANT
        elif warnings and any("compliance" in w.lower() for w in warnings):
            checklist.compliance_status = ComplianceStatus.REQUIRES_REVIEW
        elif missing_required:
            checklist.compliance_status = ComplianceStatus.PENDING
        else:
            checklist.compliance_status = ComplianceStatus.COMPLIANT
        
        return {
            "compliance_status": checklist.compliance_status.value,
            "compliance_issues": compliance_issues,
            "warnings": warnings,
            "checked_at": datetime.now().isoformat()
        }
    
    def export_checklist(self, checklist_id: UUID, format: str = "json") -> Optional[Dict[str, Any]]:
        """Export due diligence checklist in specified format."""
        checklist = self.checklists.get(checklist_id)
        if not checklist:
            return None
        
        if format.lower() == "json":
            # Convert to dict and handle UUID serialization
            checklist_dict = checklist.model_dump()
            
            # Convert UUIDs to strings for JSON serialization
            def convert_uuids(obj):
                if isinstance(obj, dict):
                    return {k: convert_uuids(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_uuids(item) for item in obj]
                elif hasattr(obj, '__str__') and 'UUID' in str(type(obj)):
                    return str(obj)
                else:
                    return obj
            
            checklist_dict = convert_uuids(checklist_dict)
            
            return {
                "checklist": checklist_dict,
                "risk_report": self.generate_risk_report(checklist_id),
                "compliance_check": self.auto_check_compliance(checklist_id),
                "exported_at": datetime.now().isoformat()
            }
        
        return None
    
    def list_checklists(self, transaction_id: Optional[UUID] = None,
                       status: Optional[ComplianceStatus] = None) -> List[DueDiligenceChecklist]:
        """List due diligence checklists with optional filtering."""
        checklists = list(self.checklists.values())
        
        if transaction_id:
            checklists = [c for c in checklists if c.transaction_id == transaction_id]
        
        if status:
            checklists = [c for c in checklists if c.compliance_status == status]
        
        return sorted(checklists, key=lambda c: c.created_at, reverse=True)