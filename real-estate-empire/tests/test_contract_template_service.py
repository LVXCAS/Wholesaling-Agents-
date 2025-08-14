"""
Unit tests for contract template service.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from app.models.contract import (
    ContractTemplate, ContractClause, ContractType, ClauseType,
    ContractValidationResult
)
from app.services.contract_template_service import ContractTemplateService


class TestContractTemplateService:
    """Test cases for ContractTemplateService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = ContractTemplateService()
    
    def test_initialization(self):
        """Test service initialization with default templates."""
        # Should have default templates
        templates = self.service.list_templates()
        assert len(templates) >= 2
        
        # Should have default clauses
        clauses = self.service.list_clauses()
        assert len(clauses) >= 5
        
        # Should have analytics for templates
        for template in templates:
            analytics = self.service.get_template_analytics(template.id)
            assert analytics is not None
            assert analytics.template_id == template.id
    
    def test_create_template(self):
        """Test creating a new template."""
        template_data = {
            "name": "Test Template",
            "contract_type": ContractType.LEASE_AGREEMENT,
            "description": "Test lease agreement template",
            "required_fields": {"tenant_name": "string", "rent_amount": "float"},
            "optional_fields": {"pet_deposit": "float"}
        }
        
        template = self.service.create_template(template_data)
        
        assert template.name == "Test Template"
        assert template.contract_type == ContractType.LEASE_AGREEMENT
        assert template.is_active is True
        assert template.version == "1.0"
        
        # Should be retrievable
        retrieved = self.service.get_template(template.id)
        assert retrieved is not None
        assert retrieved.id == template.id
        
        # Should have analytics
        analytics = self.service.get_template_analytics(template.id)
        assert analytics is not None
    
    def test_list_templates_filtering(self):
        """Test template listing with filters."""
        # Create test templates
        purchase_template = self.service.create_template({
            "name": "Purchase Test",
            "contract_type": ContractType.PURCHASE_AGREEMENT,
            "description": "Test purchase template"
        })
        
        lease_template = self.service.create_template({
            "name": "Lease Test",
            "contract_type": ContractType.LEASE_AGREEMENT,
            "description": "Test lease template"
        })
        
        # Test filtering by contract type
        purchase_templates = self.service.list_templates(
            contract_type=ContractType.PURCHASE_AGREEMENT
        )
        purchase_names = [t.name for t in purchase_templates]
        assert "Purchase Test" in purchase_names
        assert "Lease Test" not in purchase_names
        
        # Test active only filter
        lease_template.is_active = False
        active_templates = self.service.list_templates(active_only=True)
        active_names = [t.name for t in active_templates]
        assert "Lease Test" not in active_names
        
        all_templates = self.service.list_templates(active_only=False)
        all_names = [t.name for t in all_templates]
        assert "Lease Test" in all_names
    
    def test_update_template(self):
        """Test updating a template."""
        template = self.service.create_template({
            "name": "Original Name",
            "contract_type": ContractType.OPTION_CONTRACT,
            "description": "Original description"
        })
        
        original_version = template.version
        original_updated = template.updated_at
        
        # Update non-structural fields
        updated = self.service.update_template(template.id, {
            "name": "Updated Name",
            "description": "Updated description"
        })
        
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"
        assert updated.version == original_version  # Version unchanged
        assert updated.updated_at > original_updated
        
        # Update structural fields (should increment version)
        updated2 = self.service.update_template(template.id, {
            "required_fields": {"new_field": "string"}
        })
        
        assert updated2.version != original_version
        assert "new_field" in updated2.required_fields
    
    def test_delete_template(self):
        """Test soft deleting a template."""
        template = self.service.create_template({
            "name": "To Delete",
            "contract_type": ContractType.JOINT_VENTURE,
            "description": "Template to delete"
        })
        
        # Should exist initially
        assert self.service.get_template(template.id) is not None
        
        # Delete template
        result = self.service.delete_template(template.id)
        assert result is True
        
        # Should still exist but inactive
        deleted_template = self.service.get_template(template.id)
        assert deleted_template is not None
        assert deleted_template.is_active is False
        
        # Should not appear in active listings
        active_templates = self.service.list_templates(active_only=True)
        active_ids = [t.id for t in active_templates]
        assert template.id not in active_ids
    
    def test_create_clause(self):
        """Test creating a new clause."""
        clause_data = {
            "name": "Test Clause",
            "clause_type": ClauseType.OPTIONAL,
            "content": "This is a test clause with ${variable}.",
            "variables": {"variable": "string"},
            "category": "test"
        }
        
        clause = self.service.create_clause(clause_data)
        
        assert clause.name == "Test Clause"
        assert clause.clause_type == ClauseType.OPTIONAL
        assert clause.is_active is True
        assert "variable" in clause.variables
        
        # Should be retrievable
        retrieved = self.service.get_clause(clause.id)
        assert retrieved is not None
        assert retrieved.id == clause.id
    
    def test_list_clauses_filtering(self):
        """Test clause listing with filters."""
        # Create test clauses
        required_clause = self.service.create_clause({
            "name": "Required Test",
            "clause_type": ClauseType.REQUIRED,
            "content": "Required clause",
            "category": "test"
        })
        
        optional_clause = self.service.create_clause({
            "name": "Optional Test",
            "clause_type": ClauseType.OPTIONAL,
            "content": "Optional clause",
            "category": "other"
        })
        
        # Test filtering by clause type
        required_clauses = self.service.list_clauses(clause_type=ClauseType.REQUIRED)
        required_names = [c.name for c in required_clauses]
        assert "Required Test" in required_names
        
        # Test filtering by category
        test_clauses = self.service.list_clauses(category="test")
        test_names = [c.name for c in test_clauses]
        assert "Required Test" in test_names
        assert "Optional Test" not in test_names
        
        # Test active only filter
        optional_clause.is_active = False
        active_clauses = self.service.list_clauses(active_only=True)
        active_names = [c.name for c in active_clauses]
        assert "Optional Test" not in active_names
    
    def test_update_clause(self):
        """Test updating a clause."""
        clause = self.service.create_clause({
            "name": "Original Clause",
            "clause_type": ClauseType.STANDARD,
            "content": "Original content",
            "category": "original"
        })
        
        original_updated = clause.updated_at
        
        updated = self.service.update_clause(clause.id, {
            "name": "Updated Clause",
            "content": "Updated content"
        })
        
        assert updated is not None
        assert updated.name == "Updated Clause"
        assert updated.content == "Updated content"
        assert updated.updated_at > original_updated
    
    def test_delete_clause(self):
        """Test soft deleting a clause."""
        clause = self.service.create_clause({
            "name": "To Delete",
            "clause_type": ClauseType.CONDITIONAL,
            "content": "Clause to delete",
            "category": "delete"
        })
        
        # Delete clause
        result = self.service.delete_clause(clause.id)
        assert result is True
        
        # Should still exist but inactive
        deleted_clause = self.service.get_clause(clause.id)
        assert deleted_clause is not None
        assert deleted_clause.is_active is False
    
    def test_validate_template_success(self):
        """Test successful template validation."""
        # Create valid clauses
        required_clause = self.service.create_clause({
            "name": "Required Clause",
            "clause_type": ClauseType.REQUIRED,
            "content": "Required content",
            "category": "required"
        })
        
        template = ContractTemplate(
            name="Valid Template",
            contract_type=ContractType.PURCHASE_AGREEMENT,
            description="A valid template",
            clauses=[required_clause.id],
            required_fields={"buyer": "string", "price": "float"},
            optional_fields={"deposit": "float"}
        )
        
        result = self.service.validate_template(template)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_template_errors(self):
        """Test template validation with errors."""
        # Template with missing required fields
        template = ContractTemplate(
            name="",  # Missing name
            contract_type=ContractType.PURCHASE_AGREEMENT,
            description="Test template with errors",  # Required field
            clauses=[uuid4()],  # Non-existent clause
            required_fields={"field": "invalid_type"}  # Invalid field type
        )
        
        result = self.service.validate_template(template)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("name is required" in error for error in result.errors)
        assert any("Missing clauses" in error for error in result.errors)
        assert any("Invalid field types" in error for error in result.errors)
    
    def test_template_analytics(self):
        """Test template analytics tracking."""
        template = self.service.create_template({
            "name": "Analytics Test",
            "contract_type": ContractType.PURCHASE_AGREEMENT,
            "description": "Template for analytics testing"
        })
        
        analytics = self.service.get_template_analytics(template.id)
        assert analytics.usage_count == 0
        assert analytics.success_rate == 0.0
        
        # Update analytics
        self.service.update_template_analytics(
            template.id, 
            usage_increment=1, 
            success=True,
            time_to_signature=5.0
        )
        
        updated_analytics = self.service.get_template_analytics(template.id)
        assert updated_analytics.usage_count == 1
        assert updated_analytics.success_rate == 1.0
        assert updated_analytics.average_time_to_signature == 5.0
        
        # Add another usage
        self.service.update_template_analytics(
            template.id,
            usage_increment=1,
            success=False,
            time_to_signature=3.0
        )
        
        final_analytics = self.service.get_template_analytics(template.id)
        assert final_analytics.usage_count == 2
        assert final_analytics.success_rate == 0.5  # 1 success out of 2
        assert final_analytics.average_time_to_signature == 4.0  # Average of 5 and 3
    
    def test_search_templates(self):
        """Test template search functionality."""
        # Create test templates
        self.service.create_template({
            "name": "Purchase Agreement Template",
            "contract_type": ContractType.PURCHASE_AGREEMENT,
            "description": "Standard purchase agreement"
        })
        
        self.service.create_template({
            "name": "Lease Agreement",
            "contract_type": ContractType.LEASE_AGREEMENT,
            "description": "Residential lease template"
        })
        
        # Search by name
        results = self.service.search_templates("purchase")
        assert len(results) >= 1
        assert any("Purchase" in t.name for t in results)
        
        # Search by description
        results = self.service.search_templates("lease")
        assert len(results) >= 1
        assert any("Lease" in t.name for t in results)
        
        # Case insensitive search
        results = self.service.search_templates("AGREEMENT")
        assert len(results) >= 2
    
    def test_get_template_with_clauses(self):
        """Test getting template with full clause details."""
        # Create a clause
        clause = self.service.create_clause({
            "name": "Test Clause",
            "clause_type": ClauseType.STANDARD,
            "content": "Test content",
            "category": "test"
        })
        
        # Create template with the clause
        template = self.service.create_template({
            "name": "Template with Clauses",
            "contract_type": ContractType.OPTION_CONTRACT,
            "description": "Template for testing clause inclusion",
            "clauses": [clause.id]
        })
        
        # Get template with clauses
        result = self.service.get_template_with_clauses(template.id)
        
        assert result is not None
        assert "template" in result
        assert "clauses" in result
        assert "analytics" in result
        
        assert result["template"].id == template.id
        assert len(result["clauses"]) == 1
        assert result["clauses"][0].id == clause.id
        assert result["analytics"].template_id == template.id
    
    def test_nonexistent_operations(self):
        """Test operations on non-existent items."""
        fake_id = uuid4()
        
        # Template operations
        assert self.service.get_template(fake_id) is None
        assert self.service.update_template(fake_id, {"name": "test"}) is None
        assert self.service.delete_template(fake_id) is False
        assert self.service.get_template_with_clauses(fake_id) is None
        
        # Clause operations
        assert self.service.get_clause(fake_id) is None
        assert self.service.update_clause(fake_id, {"name": "test"}) is None
        assert self.service.delete_clause(fake_id) is False
        
        # Analytics operations
        assert self.service.get_template_analytics(fake_id) is None