"""
Unit tests for contract generation service.
"""

import pytest
from datetime import datetime, date
from uuid import uuid4

from app.models.contract import (
    ContractDocument, ContractParty, ContractGenerationRequest,
    ContractType, ContractStatus, ClauseType
)
from app.services.contract_template_service import ContractTemplateService
from app.services.contract_generation_service import ContractGenerationService


class TestContractGenerationService:
    """Test cases for ContractGenerationService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.template_service = ContractTemplateService()
        self.generation_service = ContractGenerationService(self.template_service)
        
        # Get a default template for testing
        templates = self.template_service.list_templates(
            contract_type=ContractType.PURCHASE_AGREEMENT
        )
        self.test_template = templates[0] if templates else None
    
    def test_generate_basic_contract(self):
        """Test generating a basic contract."""
        if not self.test_template:
            pytest.skip("No test template available")
        
        # Prepare test data
        deal_data = {
            "buyer_name": "John Doe",
            "seller_name": "Jane Smith",
            "property_address": "123 Main St, Anytown, ST 12345",
            "purchase_price": 250000.0,
            "closing_date": date(2024, 6, 15)
        }
        
        parties = [
            ContractParty(name="John Doe", role="buyer", email="john@example.com"),
            ContractParty(name="Jane Smith", role="seller", email="jane@example.com")
        ]
        
        request = ContractGenerationRequest(
            template_id=self.test_template.id,
            deal_data=deal_data,
            parties=parties
        )
        
        # Generate contract
        contract = self.generation_service.generate_contract(request)
        
        # Verify contract properties
        assert contract.template_id == self.test_template.id
        assert contract.contract_type == ContractType.PURCHASE_AGREEMENT
        assert contract.status == ContractStatus.DRAFT
        assert len(contract.parties) == 2
        assert contract.purchase_price == 250000.0
        assert contract.closing_date == date(2024, 6, 15)
        assert contract.property_address == "123 Main St, Anytown, ST 12345"
        
        # Verify content generation
        assert contract.generated_content is not None
        assert len(contract.generated_content) > 0
        assert "John Doe" in contract.generated_content
        assert "Jane Smith" in contract.generated_content
        assert "$250,000.00" in contract.generated_content
    
    def test_field_value_extraction(self):
        """Test field value extraction and type conversion."""
        if not self.test_template:
            pytest.skip("No test template available")
        
        deal_data = {
            "buyer_name": "Test Buyer",
            "seller_name": "Test Seller",
            "property_address": "Test Address",
            "purchase_price": "300000",  # String number
            "closing_date": "2024-07-01",  # String date
            "earnest_money": 5000.50,
            "inspection_period": "10"  # String integer
        }
        
        custom_terms = {
            "financing_required": "true"  # String boolean
        }
        
        parties = [
            ContractParty(name="Test Buyer", role="buyer"),
            ContractParty(name="Test Seller", role="seller")
        ]
        
        request = ContractGenerationRequest(
            template_id=self.test_template.id,
            deal_data=deal_data,
            parties=parties,
            custom_terms=custom_terms
        )
        
        contract = self.generation_service.generate_contract(request)
        
        # Verify type conversions
        assert contract.field_values["purchase_price"] == 300000.0
        assert contract.field_values["closing_date"] == date(2024, 7, 1)
        assert contract.field_values["inspection_period"] == 10
        assert contract.field_values["financing_required"] is True
    
    def test_missing_required_field(self):
        """Test error handling for missing required fields."""
        if not self.test_template:
            pytest.skip("No test template available")
        
        # Missing required field
        deal_data = {
            "buyer_name": "Test Buyer",
            "seller_name": "Test Seller"
            # Missing property_address and purchase_price
        }
        
        parties = [ContractParty(name="Test Buyer", role="buyer")]
        
        request = ContractGenerationRequest(
            template_id=self.test_template.id,
            deal_data=deal_data,
            parties=parties
        )
        
        # Should raise ValueError for missing required field
        with pytest.raises(ValueError, match="Required field"):
            self.generation_service.generate_contract(request)
    
    def test_invalid_field_type(self):
        """Test error handling for invalid field types."""
        if not self.test_template:
            pytest.skip("No test template available")
        
        deal_data = {
            "buyer_name": "Test Buyer",
            "seller_name": "Test Seller",
            "property_address": "Test Address",
            "purchase_price": "not_a_number",  # Invalid float
            "closing_date": date(2024, 6, 15)
        }
        
        parties = [ContractParty(name="Test Buyer", role="buyer")]
        
        request = ContractGenerationRequest(
            template_id=self.test_template.id,
            deal_data=deal_data,
            parties=parties
        )
        
        # Should raise ValueError for invalid type conversion
        with pytest.raises(ValueError, match="Cannot convert field"):
            self.generation_service.generate_contract(request)
    
    def test_conditional_clause_inclusion(self):
        """Test conditional clause inclusion based on deal data."""
        # Create a conditional clause
        conditional_clause = self.template_service.create_clause({
            "name": "Financing Contingency Test",
            "clause_type": ClauseType.CONDITIONAL,
            "content": "This agreement is contingent upon financing approval.",
            "conditions": {"financing_required": True},
            "category": "contingencies"
        })
        
        # Create template with conditional clause
        template = self.template_service.create_template({
            "name": "Test Template with Conditional",
            "contract_type": ContractType.PURCHASE_AGREEMENT,
            "description": "Template for testing conditional clauses",
            "clauses": [conditional_clause.id],
            "required_fields": {"buyer_name": "string", "seller_name": "string"}
        })
        
        parties = [ContractParty(name="Test Buyer", role="buyer")]
        
        # Test with condition met
        deal_data_with_financing = {
            "buyer_name": "Test Buyer",
            "seller_name": "Test Seller",
            "financing_required": True
        }
        
        request = ContractGenerationRequest(
            template_id=template.id,
            deal_data=deal_data_with_financing,
            parties=parties
        )
        
        contract = self.generation_service.generate_contract(request)
        assert conditional_clause.id in contract.included_clauses
        assert "financing approval" in contract.generated_content
        
        # Test with condition not met
        deal_data_no_financing = {
            "buyer_name": "Test Buyer",
            "seller_name": "Test Seller",
            "financing_required": False
        }
        
        request2 = ContractGenerationRequest(
            template_id=template.id,
            deal_data=deal_data_no_financing,
            parties=parties
        )
        
        contract2 = self.generation_service.generate_contract(request2)
        assert conditional_clause.id not in contract2.included_clauses
        assert "financing approval" not in contract2.generated_content
    
    def test_optional_clause_inclusion(self):
        """Test optional clause inclusion/exclusion."""
        # Create optional clause
        optional_clause = self.template_service.create_clause({
            "name": "As-Is Clause Test",
            "clause_type": ClauseType.OPTIONAL,
            "content": "Property sold as-is.",
            "category": "condition"
        })
        
        template = self.template_service.create_template({
            "name": "Test Template with Optional",
            "contract_type": ContractType.PURCHASE_AGREEMENT,
            "description": "Template for testing optional clauses",
            "clauses": [optional_clause.id],
            "required_fields": {"buyer_name": "string", "seller_name": "string"}
        })
        
        deal_data = {
            "buyer_name": "Test Buyer",
            "seller_name": "Test Seller"
        }
        
        parties = [ContractParty(name="Test Buyer", role="buyer")]
        
        # Test without including optional clause
        request1 = ContractGenerationRequest(
            template_id=template.id,
            deal_data=deal_data,
            parties=parties
        )
        
        contract1 = self.generation_service.generate_contract(request1)
        assert optional_clause.id not in contract1.included_clauses
        
        # Test with including optional clause
        request2 = ContractGenerationRequest(
            template_id=template.id,
            deal_data=deal_data,
            parties=parties,
            include_optional_clauses=["As-Is Clause Test"]
        )
        
        contract2 = self.generation_service.generate_contract(request2)
        assert optional_clause.id in contract2.included_clauses
        assert "as-is" in contract2.generated_content.lower()
    
    def test_clause_exclusion(self):
        """Test excluding specific clauses."""
        # Get template with multiple clauses
        if not self.test_template:
            pytest.skip("No test template available")
        
        deal_data = {
            "buyer_name": "Test Buyer",
            "seller_name": "Test Seller",
            "property_address": "Test Address",
            "purchase_price": 200000.0,
            "closing_date": date(2024, 6, 15)
        }
        
        parties = [ContractParty(name="Test Buyer", role="buyer")]
        
        # Get a clause to exclude
        template_clauses = [
            self.template_service.get_clause(cid) 
            for cid in self.test_template.clauses
        ]
        clause_to_exclude = next((c for c in template_clauses if c), None)
        
        if not clause_to_exclude:
            pytest.skip("No clauses available to exclude")
        
        request = ContractGenerationRequest(
            template_id=self.test_template.id,
            deal_data=deal_data,
            parties=parties,
            exclude_clauses=[clause_to_exclude.name]
        )
        
        contract = self.generation_service.generate_contract(request)
        assert clause_to_exclude.id not in contract.included_clauses
    
    def test_contract_validation_success(self):
        """Test successful contract validation."""
        if not self.test_template:
            pytest.skip("No test template available")
        
        # Create valid contract
        contract = ContractDocument(
            template_id=self.test_template.id,
            contract_type=ContractType.PURCHASE_AGREEMENT,
            parties=[
                ContractParty(name="John Doe", role="buyer", email="john@example.com"),
                ContractParty(name="Jane Smith", role="seller", email="jane@example.com")
            ],
            purchase_price=250000.0,
            earnest_money=5000.0,
            closing_date=date(2024, 12, 15),
            property_address="123 Main St",
            generated_content="Valid contract content with all required information."
        )
        
        result = self.generation_service.validate_contract(contract)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_contract_validation_errors(self):
        """Test contract validation with errors."""
        # Create invalid contract
        contract = ContractDocument(
            template_id=uuid4(),
            contract_type=ContractType.PURCHASE_AGREEMENT,
            parties=[],  # No parties
            purchase_price=-1000.0,  # Negative price
            earnest_money=300000.0,  # Earnest money > purchase price
            closing_date=date(2020, 1, 1),  # Past date
            generated_content="Contract with [MISSING_FIELD] placeholders."
        )
        
        result = self.generation_service.validate_contract(contract)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert len(result.warnings) > 0
        assert "MISSING_FIELD" in result.missing_fields
    
    def test_update_contract_status(self):
        """Test updating contract status."""
        contract = ContractDocument(
            template_id=uuid4(),
            contract_type=ContractType.PURCHASE_AGREEMENT,
            status=ContractStatus.DRAFT
        )
        
        original_updated = contract.updated_at
        
        # Update to executed status
        updated_contract = self.generation_service.update_contract_status(
            contract, ContractStatus.EXECUTED
        )
        
        assert updated_contract.status == ContractStatus.EXECUTED
        assert updated_contract.executed_at is not None
        assert updated_contract.updated_at > original_updated
    
    def test_regenerate_contract(self):
        """Test regenerating contract with updated data."""
        if not self.test_template:
            pytest.skip("No test template available")
        
        # Create original contract
        original_data = {
            "buyer_name": "Original Buyer",
            "seller_name": "Original Seller",
            "property_address": "Original Address",
            "purchase_price": 200000.0,
            "closing_date": date(2024, 6, 15)
        }
        
        parties = [
            ContractParty(name="Original Buyer", role="buyer"),
            ContractParty(name="Original Seller", role="seller")
        ]
        
        request = ContractGenerationRequest(
            template_id=self.test_template.id,
            deal_data=original_data,
            parties=parties
        )
        
        original_contract = self.generation_service.generate_contract(request)
        original_id = original_contract.id
        original_created = original_contract.created_at
        
        # Regenerate with updated data
        updated_data = {
            "purchase_price": 250000.0,
            "earnest_money": 10000.0
        }
        
        regenerated_contract = self.generation_service.regenerate_contract(
            original_contract, updated_data
        )
        
        # Verify updates
        assert regenerated_contract.id == original_id  # Same ID
        assert regenerated_contract.created_at == original_created  # Same creation time
        assert regenerated_contract.purchase_price == 250000.0  # Updated price
        assert regenerated_contract.earnest_money == 10000.0  # New field
        assert regenerated_contract.field_values["buyer_name"] == "Original Buyer"  # Preserved
    
    def test_nonexistent_template(self):
        """Test error handling for non-existent template."""
        fake_template_id = uuid4()
        
        request = ContractGenerationRequest(
            template_id=fake_template_id,
            deal_data={"test": "data"},
            parties=[ContractParty(name="Test", role="buyer")]
        )
        
        with pytest.raises(ValueError, match="Template .* not found"):
            self.generation_service.generate_contract(request)
    
    def test_nested_field_extraction(self):
        """Test extraction of nested field values."""
        if not self.test_template:
            pytest.skip("No test template available")
        
        # Create template that expects nested fields
        template = self.template_service.create_template({
            "name": "Nested Fields Template",
            "contract_type": ContractType.PURCHASE_AGREEMENT,
            "description": "Template with nested field references",
            "required_fields": {
                "buyer.name": "string",
                "property.address": "string",
                "terms.price": "float"
            }
        })
        
        # Deal data with nested structure
        deal_data = {
            "buyer": {"name": "John Doe", "email": "john@example.com"},
            "property": {"address": "123 Main St", "type": "single_family"},
            "terms": {"price": 300000.0, "deposit": 15000.0}
        }
        
        parties = [ContractParty(name="John Doe", role="buyer")]
        
        request = ContractGenerationRequest(
            template_id=template.id,
            deal_data=deal_data,
            parties=parties
        )
        
        contract = self.generation_service.generate_contract(request)
        
        # Verify nested field extraction
        assert contract.field_values["buyer.name"] == "John Doe"
        assert contract.field_values["property.address"] == "123 Main St"
        assert contract.field_values["terms.price"] == 300000.0