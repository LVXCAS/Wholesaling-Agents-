"""
Contract template management service.
Handles template creation, versioning, validation, and clause management.
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from app.models.contract import (
    ContractTemplate, ContractClause, ContractType, ClauseType,
    ContractValidationResult, ContractAnalytics
)


class ContractTemplateService:
    """Service for managing contract templates and clauses."""
    
    def __init__(self):
        # In-memory storage for demo - would be replaced with database
        self.templates: Dict[UUID, ContractTemplate] = {}
        self.clauses: Dict[UUID, ContractClause] = {}
        self.analytics: Dict[UUID, ContractAnalytics] = {}
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """Initialize default contract templates and clauses."""
        # Create default clauses
        self._create_default_clauses()
        
        # Create default templates
        self._create_purchase_agreement_template()
        self._create_wholesale_assignment_template()
    
    def _create_default_clauses(self):
        """Create default contract clauses."""
        default_clauses = [
            {
                "name": "Purchase Price Clause",
                "clause_type": ClauseType.REQUIRED,
                "content": "The total purchase price for the Property shall be ${purchase_price} ({purchase_price_words} Dollars), payable as follows: ${payment_terms}",
                "variables": {"purchase_price": "float", "purchase_price_words": "string", "payment_terms": "string"},
                "category": "pricing"
            },
            {
                "name": "Earnest Money Clause",
                "clause_type": ClauseType.STANDARD,
                "content": "Buyer shall deposit earnest money in the amount of ${earnest_money} with ${escrow_agent} within ${earnest_money_deadline} days of acceptance of this Agreement.",
                "variables": {"earnest_money": "float", "escrow_agent": "string", "earnest_money_deadline": "int"},
                "category": "earnest_money"
            },
            {
                "name": "Inspection Contingency",
                "clause_type": ClauseType.CONDITIONAL,
                "content": "This Agreement is contingent upon Buyer's approval of the Property condition. Buyer shall have ${inspection_period} days from acceptance to complete inspections and provide written notice of disapproval.",
                "variables": {"inspection_period": "int"},
                "conditions": {"include_inspection": True},
                "category": "contingencies"
            },
            {
                "name": "Financing Contingency",
                "clause_type": ClauseType.CONDITIONAL,
                "content": "This Agreement is contingent upon Buyer obtaining financing in the amount of ${loan_amount} at an interest rate not to exceed ${max_interest_rate}% within ${financing_deadline} days.",
                "variables": {"loan_amount": "float", "max_interest_rate": "float", "financing_deadline": "int"},
                "conditions": {"financing_required": True},
                "category": "contingencies"
            },
            {
                "name": "Closing Date Clause",
                "clause_type": ClauseType.REQUIRED,
                "content": "Closing shall occur on or before ${closing_date} at ${closing_location}. Time is of the essence.",
                "variables": {"closing_date": "date", "closing_location": "string"},
                "category": "closing"
            },
            {
                "name": "As-Is Clause",
                "clause_type": ClauseType.OPTIONAL,
                "content": "Buyer acknowledges that the Property is being sold in its present 'AS-IS' condition. Seller makes no warranties or representations regarding the condition of the Property.",
                "variables": {},
                "category": "condition"
            },
            {
                "name": "Assignment Rights",
                "clause_type": ClauseType.OPTIONAL,
                "content": "Buyer shall have the right to assign this Agreement to any person or entity. Assignment shall not relieve Buyer of obligations hereunder unless Seller provides written consent.",
                "variables": {},
                "category": "assignment"
            }
        ]
        
        for clause_data in default_clauses:
            clause = ContractClause(**clause_data)
            self.clauses[clause.id] = clause
    
    def _create_purchase_agreement_template(self):
        """Create default purchase agreement template."""
        # Get clause IDs for purchase agreement
        purchase_clauses = [
            clause.id for clause in self.clauses.values()
            if clause.category in ["pricing", "earnest_money", "contingencies", "closing"]
        ]
        
        template = ContractTemplate(
            name="Standard Purchase Agreement",
            contract_type=ContractType.PURCHASE_AGREEMENT,
            description="Standard real estate purchase agreement template",
            clauses=purchase_clauses,
            required_fields={
                "buyer_name": "string",
                "seller_name": "string",
                "property_address": "string",
                "purchase_price": "float",
                "closing_date": "date"
            },
            optional_fields={
                "earnest_money": "float",
                "inspection_period": "int",
                "financing_required": "boolean",
                "loan_amount": "float"
            },
            template_structure={
                "sections": [
                    {"name": "Parties", "order": 1},
                    {"name": "Property Description", "order": 2},
                    {"name": "Purchase Price and Terms", "order": 3},
                    {"name": "Contingencies", "order": 4},
                    {"name": "Closing", "order": 5},
                    {"name": "General Provisions", "order": 6}
                ]
            }
        )
        
        self.templates[template.id] = template
        self.analytics[template.id] = ContractAnalytics(template_id=template.id)
    
    def _create_wholesale_assignment_template(self):
        """Create wholesale assignment template."""
        # Get clause IDs for assignment
        assignment_clauses = [
            clause.id for clause in self.clauses.values()
            if clause.category in ["pricing", "assignment", "closing"]
        ]
        
        template = ContractTemplate(
            name="Wholesale Assignment Agreement",
            contract_type=ContractType.WHOLESALE_ASSIGNMENT,
            description="Assignment agreement for wholesale deals",
            clauses=assignment_clauses,
            required_fields={
                "assignor_name": "string",
                "assignee_name": "string",
                "property_address": "string",
                "assignment_fee": "float",
                "original_contract_date": "date"
            },
            optional_fields={
                "earnest_money_transfer": "boolean",
                "closing_coordination": "string"
            }
        )
        
        self.templates[template.id] = template
        self.analytics[template.id] = ContractAnalytics(template_id=template.id)
    
    # Template Management Methods
    
    def create_template(self, template_data: Dict[str, Any]) -> ContractTemplate:
        """Create a new contract template."""
        template = ContractTemplate(**template_data)
        self.templates[template.id] = template
        self.analytics[template.id] = ContractAnalytics(template_id=template.id)
        return template
    
    def get_template(self, template_id: UUID) -> Optional[ContractTemplate]:
        """Get a contract template by ID."""
        return self.templates.get(template_id)
    
    def list_templates(self, contract_type: Optional[ContractType] = None, 
                      active_only: bool = True) -> List[ContractTemplate]:
        """List contract templates with optional filtering."""
        templates = list(self.templates.values())
        
        if active_only:
            templates = [t for t in templates if t.is_active]
        
        if contract_type:
            templates = [t for t in templates if t.contract_type == contract_type]
        
        return sorted(templates, key=lambda t: t.created_at, reverse=True)
    
    def update_template(self, template_id: UUID, updates: Dict[str, Any]) -> Optional[ContractTemplate]:
        """Update a contract template."""
        template = self.templates.get(template_id)
        if not template:
            return None
        
        # Create new version if significant changes
        if any(key in updates for key in ['clauses', 'required_fields', 'template_structure']):
            # Increment version
            version_parts = template.version.split('.')
            major, minor = int(version_parts[0]), int(version_parts[1])
            updates['version'] = f"{major}.{minor + 1}"
        
        # Update fields
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        template.updated_at = datetime.now()
        return template
    
    def delete_template(self, template_id: UUID) -> bool:
        """Soft delete a contract template."""
        template = self.templates.get(template_id)
        if template:
            template.is_active = False
            template.updated_at = datetime.now()
            return True
        return False
    
    # Clause Management Methods
    
    def create_clause(self, clause_data: Dict[str, Any]) -> ContractClause:
        """Create a new contract clause."""
        clause = ContractClause(**clause_data)
        self.clauses[clause.id] = clause
        return clause
    
    def get_clause(self, clause_id: UUID) -> Optional[ContractClause]:
        """Get a contract clause by ID."""
        return self.clauses.get(clause_id)
    
    def list_clauses(self, category: Optional[str] = None, 
                    clause_type: Optional[ClauseType] = None,
                    active_only: bool = True) -> List[ContractClause]:
        """List contract clauses with optional filtering."""
        clauses = list(self.clauses.values())
        
        if active_only:
            clauses = [c for c in clauses if c.is_active]
        
        if category:
            clauses = [c for c in clauses if c.category == category]
        
        if clause_type:
            clauses = [c for c in clauses if c.clause_type == clause_type]
        
        return sorted(clauses, key=lambda c: c.name)
    
    def update_clause(self, clause_id: UUID, updates: Dict[str, Any]) -> Optional[ContractClause]:
        """Update a contract clause."""
        clause = self.clauses.get(clause_id)
        if not clause:
            return None
        
        for key, value in updates.items():
            if hasattr(clause, key):
                setattr(clause, key, value)
        
        clause.updated_at = datetime.now()
        return clause
    
    def delete_clause(self, clause_id: UUID) -> bool:
        """Soft delete a contract clause."""
        clause = self.clauses.get(clause_id)
        if clause:
            clause.is_active = False
            clause.updated_at = datetime.now()
            return True
        return False
    
    # Template Validation Methods
    
    def validate_template(self, template: ContractTemplate) -> ContractValidationResult:
        """Validate a contract template."""
        errors = []
        warnings = []
        suggestions = []
        
        # Check required fields
        if not template.name:
            errors.append("Template name is required")
        
        if not template.contract_type:
            errors.append("Contract type is required")
        
        # Validate clauses exist
        missing_clauses = []
        for clause_id in template.clauses:
            if clause_id not in self.clauses:
                missing_clauses.append(str(clause_id))
        
        if missing_clauses:
            errors.append(f"Missing clauses: {', '.join(missing_clauses)}")
        
        # Check for required clause types
        template_clauses = [self.clauses[cid] for cid in template.clauses if cid in self.clauses]
        required_clauses = [c for c in template_clauses if c.clause_type == ClauseType.REQUIRED]
        
        if not required_clauses:
            warnings.append("Template has no required clauses")
        
        # Validate field types
        invalid_fields = []
        valid_types = ['string', 'int', 'float', 'boolean', 'date', 'datetime']
        
        for field, field_type in template.required_fields.items():
            if field_type not in valid_types:
                invalid_fields.append(f"{field}: {field_type}")
        
        if invalid_fields:
            errors.append(f"Invalid field types: {', '.join(invalid_fields)}")
        
        # Suggestions
        if len(template.clauses) < 3:
            suggestions.append("Consider adding more clauses for comprehensive coverage")
        
        if not template.description:
            suggestions.append("Add a description to help users understand the template purpose")
        
        return ContractValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def get_template_analytics(self, template_id: UUID) -> Optional[ContractAnalytics]:
        """Get analytics for a template."""
        return self.analytics.get(template_id)
    
    def update_template_analytics(self, template_id: UUID, 
                                 usage_increment: int = 1,
                                 success: Optional[bool] = None,
                                 time_to_signature: Optional[float] = None):
        """Update template analytics."""
        analytics = self.analytics.get(template_id)
        if not analytics:
            return
        
        analytics.usage_count += usage_increment
        
        if success is not None:
            # Update success rate (simplified calculation)
            current_successes = analytics.success_rate * (analytics.usage_count - usage_increment)
            new_successes = current_successes + (1 if success else 0)
            analytics.success_rate = new_successes / analytics.usage_count
        
        if time_to_signature is not None:
            # Update average time (simplified calculation)
            if analytics.average_time_to_signature is None:
                analytics.average_time_to_signature = time_to_signature
            else:
                # Weighted average
                total_time = analytics.average_time_to_signature * (analytics.usage_count - 1)
                analytics.average_time_to_signature = (total_time + time_to_signature) / analytics.usage_count
        
        analytics.last_updated = datetime.now()
    
    def search_templates(self, query: str) -> List[ContractTemplate]:
        """Search templates by name or description."""
        query = query.lower()
        results = []
        
        for template in self.templates.values():
            if not template.is_active:
                continue
                
            if (query in template.name.lower() or 
                query in template.description.lower()):
                results.append(template)
        
        return sorted(results, key=lambda t: t.name)
    
    def get_template_with_clauses(self, template_id: UUID) -> Optional[Dict[str, Any]]:
        """Get template with full clause details."""
        template = self.get_template(template_id)
        if not template:
            return None
        
        clause_details = []
        for clause_id in template.clauses:
            clause = self.get_clause(clause_id)
            if clause:
                clause_details.append(clause)
        
        return {
            "template": template,
            "clauses": clause_details,
            "analytics": self.get_template_analytics(template_id)
        }