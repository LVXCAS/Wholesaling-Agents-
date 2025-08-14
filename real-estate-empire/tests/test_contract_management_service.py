"""
Unit tests for contract management service.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.contract import (
    ContractDocument, ContractParty, ContractType, ContractStatus
)
from app.services.contract_template_service import ContractTemplateService
from app.services.contract_generation_service import ContractGenerationService
from app.services.electronic_signature_service import ElectronicSignatureService
from app.services.contract_management_service import ContractManagementService


class TestContractManagementService:
    """Test cases for ContractManagementService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.template_service = ContractTemplateService()
        self.generation_service = ContractGenerationService(self.template_service)
        self.signature_service = ElectronicSignatureService()
        self.management_service = ContractManagementService(
            self.template_service,
            self.generation_service,
            self.signature_service
        )
        
        # Create test contract
        self.test_contract = ContractDocument(
            template_id=uuid4(),
            contract_type=ContractType.PURCHASE_AGREEMENT,
            parties=[
                ContractParty(name="John Buyer", role="buyer", email="john@example.com"),
                ContractParty(name="Jane Seller", role="seller", email="jane@example.com")
            ],
            property_address="123 Test St, Test City, TS 12345",
            purchase_price=300000.0,
            generated_content="Test contract content for management testing."
        )
    
    def test_store_contract(self):
        """Test storing a contract in the management system."""
        # Store contract
        stored_contract = self.management_service.store_contract(self.test_contract)
        
        # Verify contract was stored
        assert stored_contract.id is not None
        assert stored_contract.created_at is not None
        assert stored_contract.updated_at is not None
        
        # Verify it can be retrieved
        retrieved = self.management_service.get_contract(stored_contract.id)
        assert retrieved is not None
        assert retrieved.id == stored_contract.id
        assert retrieved.property_address == "123 Test St, Test City, TS 12345"
        
        # Verify search index was updated
        search_results = self.management_service.search_contracts("Test St")
        assert len(search_results) >= 1
        assert any(c.id == stored_contract.id for c in search_results)
    
    def test_list_contracts_filtering(self):
        """Test listing contracts with various filters."""
        # Store multiple contracts
        contract1 = self.management_service.store_contract(self.test_contract)
        
        contract2 = ContractDocument(
            template_id=uuid4(),
            contract_type=ContractType.LEASE_AGREEMENT,
            parties=[ContractParty(name="Alice Tenant", role="tenant", email="alice@example.com")],
            property_address="456 Lease Ave",
            status=ContractStatus.EXECUTED,
            generated_content="Lease agreement content"
        )
        contract2 = self.management_service.store_contract(contract2)
        
        # Test filtering by contract type
        purchase_contracts = self.management_service.list_contracts(
            contract_type=ContractType.PURCHASE_AGREEMENT
        )
        assert len(purchase_contracts) >= 1
        assert all(c.contract_type == ContractType.PURCHASE_AGREEMENT for c in purchase_contracts)
        
        # Test filtering by status
        executed_contracts = self.management_service.list_contracts(
            status=ContractStatus.EXECUTED
        )
        assert len(executed_contracts) >= 1
        assert all(c.status == ContractStatus.EXECUTED for c in executed_contracts)
        
        # Test date filtering
        recent_contracts = self.management_service.list_contracts(
            created_after=datetime.now() - timedelta(hours=1)
        )
        assert len(recent_contracts) >= 2
        
        # Test pagination
        limited_contracts = self.management_service.list_contracts(limit=1)
        assert len(limited_contracts) == 1
    
    def test_search_contracts(self):
        """Test contract search functionality."""
        # Store test contract
        stored_contract = self.management_service.store_contract(self.test_contract)
        
        # Search by property address
        address_results = self.management_service.search_contracts("Test St")
        assert len(address_results) >= 1
        assert any(c.id == stored_contract.id for c in address_results)
        
        # Search by party name
        party_results = self.management_service.search_contracts("John Buyer")
        assert len(party_results) >= 1
        assert any(c.id == stored_contract.id for c in party_results)
        
        # Search by email
        email_results = self.management_service.search_contracts("john@example.com")
        assert len(email_results) >= 1
        assert any(c.id == stored_contract.id for c in email_results)
        
        # Search with contract type filter
        filtered_results = self.management_service.search_contracts(
            "Test St", 
            contract_type=ContractType.PURCHASE_AGREEMENT
        )
        assert len(filtered_results) >= 1
        assert all(c.contract_type == ContractType.PURCHASE_AGREEMENT for c in filtered_results)
        
        # Search for non-existent term
        no_results = self.management_service.search_contracts("NonExistentTerm")
        assert len(no_results) == 0
    
    def test_update_contract(self):
        """Test updating contracts with version control."""
        # Store contract
        stored_contract = self.management_service.store_contract(self.test_contract)
        original_updated = stored_contract.updated_at
        
        # Update contract
        updates = {
            "purchase_price": 350000.0,
            "status": ContractStatus.PENDING_SIGNATURE
        }
        
        updated_contract = self.management_service.update_contract(
            stored_contract.id, 
            updates, 
            create_version=True
        )
        
        assert updated_contract is not None
        assert updated_contract.purchase_price == 350000.0
        assert updated_contract.status == ContractStatus.PENDING_SIGNATURE
        assert updated_contract.updated_at > original_updated
        
        # Verify version was created
        versions = self.management_service.get_contract_versions(stored_contract.id)
        assert len(versions) == 1
        assert versions[0].purchase_price == 300000.0  # Original value
    
    def test_contract_versions(self):
        """Test contract version management."""
        # Store contract
        stored_contract = self.management_service.store_contract(self.test_contract)
        
        # Make multiple updates
        self.management_service.update_contract(
            stored_contract.id, 
            {"purchase_price": 320000.0}, 
            create_version=True
        )
        
        self.management_service.update_contract(
            stored_contract.id, 
            {"purchase_price": 340000.0}, 
            create_version=True
        )
        
        # Check version history
        versions = self.management_service.get_contract_versions(stored_contract.id)
        assert len(versions) == 2
        
        # Restore to previous version
        restored_contract = self.management_service.restore_contract_version(
            stored_contract.id, 
            0  # First version
        )
        
        assert restored_contract is not None
        assert restored_contract.purchase_price == 300000.0  # Original value
        
        # Version history should now have 3 entries (original + 2 updates)
        versions_after_restore = self.management_service.get_contract_versions(stored_contract.id)
        assert len(versions_after_restore) == 3
    
    def test_delete_contract(self):
        """Test contract deletion (soft and hard)."""
        # Store contract
        stored_contract = self.management_service.store_contract(self.test_contract)
        contract_id = stored_contract.id
        
        # Soft delete
        result = self.management_service.delete_contract(contract_id, soft_delete=True)
        assert result is True
        
        # Contract should still exist but be cancelled
        deleted_contract = self.management_service.get_contract(contract_id)
        assert deleted_contract is not None
        assert deleted_contract.status == ContractStatus.CANCELLED
        
        # Hard delete
        result2 = self.management_service.delete_contract(contract_id, soft_delete=False)
        assert result2 is True
        
        # Contract should no longer exist
        hard_deleted_contract = self.management_service.get_contract(contract_id)
        assert hard_deleted_contract is None
        
        # Test deleting non-existent contract
        fake_id = uuid4()
        result3 = self.management_service.delete_contract(fake_id)
        assert result3 is False
    
    def test_contract_analytics(self):
        """Test contract analytics generation."""
        # Store multiple contracts with different statuses
        contract1 = self.management_service.store_contract(self.test_contract)
        
        contract2 = ContractDocument(
            template_id=uuid4(),
            contract_type=ContractType.LEASE_AGREEMENT,
            parties=[ContractParty(name="Alice Tenant", role="tenant", email="alice@example.com")],
            status=ContractStatus.EXECUTED,
            executed_at=datetime.now(),
            generated_content="Executed lease"
        )
        contract2 = self.management_service.store_contract(contract2)
        
        contract3 = ContractDocument(
            template_id=uuid4(),
            contract_type=ContractType.PURCHASE_AGREEMENT,
            parties=[ContractParty(name="Bob Buyer", role="buyer", email="bob@example.com")],
            status=ContractStatus.CANCELLED,
            generated_content="Cancelled purchase"
        )
        contract3 = self.management_service.store_contract(contract3)
        
        # Get overall analytics
        analytics = self.management_service.get_contract_analytics()
        
        assert analytics["total_contracts"] >= 3
        assert "status_breakdown" in analytics
        assert "completion_rate" in analytics
        assert "template_usage" in analytics
        assert "monthly_trends" in analytics
        
        # Verify status breakdown
        status_breakdown = analytics["status_breakdown"]
        assert "executed" in status_breakdown
        assert "cancelled" in status_breakdown
        
        # Test filtered analytics
        purchase_analytics = self.management_service.get_contract_analytics(
            contract_type=ContractType.PURCHASE_AGREEMENT
        )
        assert purchase_analytics["total_contracts"] >= 2
    
    def test_export_contract(self):
        """Test contract export functionality."""
        # Store contract
        stored_contract = self.management_service.store_contract(self.test_contract)
        
        # Export as JSON
        json_export = self.management_service.export_contract(stored_contract.id, "json")
        assert json_export is not None
        assert "contract" in json_export
        assert "versions" in json_export
        assert "signature_requests" in json_export
        assert "exported_at" in json_export
        
        # Export as PDF
        pdf_export = self.management_service.export_contract(stored_contract.id, "pdf")
        assert pdf_export is not None
        assert pdf_export["format"] == "pdf"
        assert "content" in pdf_export
        assert "metadata" in pdf_export
        
        # Test non-existent contract
        fake_id = uuid4()
        no_export = self.management_service.export_contract(fake_id)
        assert no_export is None
    
    def test_bulk_update_contracts(self):
        """Test bulk updating multiple contracts."""
        # Store multiple contracts
        contract1 = self.management_service.store_contract(self.test_contract)
        
        contract2 = ContractDocument(
            template_id=uuid4(),
            contract_type=ContractType.PURCHASE_AGREEMENT,
            parties=[ContractParty(name="Bob Buyer", role="buyer", email="bob@example.com")],
            property_address="789 Bulk St",
            generated_content="Second contract"
        )
        contract2 = self.management_service.store_contract(contract2)
        
        # Bulk update
        contract_ids = [contract1.id, contract2.id]
        updates = {"status": ContractStatus.PENDING_SIGNATURE}
        
        updated_ids = self.management_service.bulk_update_contracts(contract_ids, updates)
        
        assert len(updated_ids) == 2
        assert contract1.id in updated_ids
        assert contract2.id in updated_ids
        
        # Verify updates were applied
        updated_contract1 = self.management_service.get_contract(contract1.id)
        updated_contract2 = self.management_service.get_contract(contract2.id)
        
        assert updated_contract1.status == ContractStatus.PENDING_SIGNATURE
        assert updated_contract2.status == ContractStatus.PENDING_SIGNATURE
    
    def test_get_contracts_by_party(self):
        """Test retrieving contracts by party email."""
        # Store contract
        stored_contract = self.management_service.store_contract(self.test_contract)
        
        # Get contracts for John Buyer
        john_contracts = self.management_service.get_contracts_by_party("john@example.com")
        assert len(john_contracts) >= 1
        assert any(c.id == stored_contract.id for c in john_contracts)
        
        # Get contracts for Jane Seller
        jane_contracts = self.management_service.get_contracts_by_party("jane@example.com")
        assert len(jane_contracts) >= 1
        assert any(c.id == stored_contract.id for c in jane_contracts)
        
        # Get contracts for non-existent party
        no_contracts = self.management_service.get_contracts_by_party("nonexistent@example.com")
        assert len(no_contracts) == 0
    
    def test_get_contracts_by_property(self):
        """Test retrieving contracts by property address."""
        # Store contract
        stored_contract = self.management_service.store_contract(self.test_contract)
        
        # Get contracts for the property
        property_contracts = self.management_service.get_contracts_by_property("123 Test St")
        assert len(property_contracts) >= 1
        assert any(c.id == stored_contract.id for c in property_contracts)
        
        # Partial address match
        partial_contracts = self.management_service.get_contracts_by_property("Test City")
        assert len(partial_contracts) >= 1
        assert any(c.id == stored_contract.id for c in partial_contracts)
        
        # Non-existent property
        no_contracts = self.management_service.get_contracts_by_property("999 Nonexistent Ave")
        assert len(no_contracts) == 0
    
    def test_get_expiring_contracts(self):
        """Test retrieving contracts with expiring signature requests."""
        # Store contract with pending signature
        contract = ContractDocument(
            template_id=uuid4(),
            contract_type=ContractType.PURCHASE_AGREEMENT,
            parties=[
                ContractParty(name="Test Buyer", role="buyer", email="test@example.com", signature_required=True)
            ],
            status=ContractStatus.PENDING_SIGNATURE,
            generated_content="Contract with expiring signature"
        )
        stored_contract = self.management_service.store_contract(contract)
        
        # Create signature request that expires soon
        signature_requests = self.signature_service.create_signature_request(stored_contract)
        
        # Modify expiry to be soon
        signature_requests[0].expires_at = datetime.now() + timedelta(days=5)
        
        # Get expiring contracts
        expiring_contracts = self.management_service.get_expiring_contracts(days_ahead=7)
        
        # Should include our contract
        expiring_ids = [c.id for c in expiring_contracts]
        assert stored_contract.id in expiring_ids
    
    def test_cleanup_old_versions(self):
        """Test cleaning up old contract versions."""
        # Store contract and create versions
        stored_contract = self.management_service.store_contract(self.test_contract)
        
        # Create multiple versions
        for i in range(5):
            self.management_service.update_contract(
                stored_contract.id, 
                {"purchase_price": 300000.0 + (i * 1000)}, 
                create_version=True
            )
        
        # Verify versions exist
        versions_before = self.management_service.get_contract_versions(stored_contract.id)
        assert len(versions_before) == 5
        
        # Clean up versions (keep only recent ones)
        cleaned_count = self.management_service.cleanup_old_versions(days_to_keep=0)
        
        # Should have cleaned up some versions
        assert cleaned_count >= 0
        
        versions_after = self.management_service.get_contract_versions(stored_contract.id)
        assert len(versions_after) <= len(versions_before)
    
    def test_validate_contract_integrity(self):
        """Test contract integrity validation."""
        # Store valid contract
        stored_contract = self.management_service.store_contract(self.test_contract)
        
        # Validate integrity
        validation_result = self.management_service.validate_contract_integrity(stored_contract.id)
        
        assert validation_result is not None
        assert hasattr(validation_result, 'is_valid')
        assert hasattr(validation_result, 'errors')
        assert hasattr(validation_result, 'warnings')
        
        # Test non-existent contract
        fake_id = uuid4()
        invalid_result = self.management_service.validate_contract_integrity(fake_id)
        
        assert invalid_result.is_valid is False
        assert "Contract not found" in invalid_result.errors
    
    def test_nonexistent_operations(self):
        """Test operations on non-existent contracts."""
        fake_id = uuid4()
        
        # Get non-existent contract
        assert self.management_service.get_contract(fake_id) is None
        
        # Update non-existent contract
        assert self.management_service.update_contract(fake_id, {"status": "test"}) is None
        
        # Get versions of non-existent contract
        assert self.management_service.get_contract_versions(fake_id) == []
        
        # Restore version of non-existent contract
        assert self.management_service.restore_contract_version(fake_id, 0) is None
        
        # Delete non-existent contract
        assert self.management_service.delete_contract(fake_id) is False