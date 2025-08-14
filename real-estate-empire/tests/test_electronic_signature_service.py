"""
Integration tests for electronic signature service.
"""

import pytest
from datetime import datetime, date, timedelta
from uuid import uuid4

from app.models.contract import (
    ContractDocument, ContractParty, ContractType, ContractStatus
)
from app.services.electronic_signature_service import ElectronicSignatureService


class TestElectronicSignatureService:
    """Test cases for ElectronicSignatureService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.signature_service = ElectronicSignatureService()
        
        # Create test contract
        self.test_contract = ContractDocument(
            template_id=uuid4(),
            contract_type=ContractType.PURCHASE_AGREEMENT,
            parties=[
                ContractParty(
                    name="John Buyer", 
                    role="buyer", 
                    email="john@example.com",
                    signature_required=True
                ),
                ContractParty(
                    name="Jane Seller", 
                    role="seller", 
                    email="jane@example.com",
                    signature_required=True
                ),
                ContractParty(
                    name="Bob Agent", 
                    role="agent", 
                    email="bob@example.com",
                    signature_required=False  # Agent doesn't need to sign
                )
            ],
            property_address="123 Test St, Test City, TS 12345",
            purchase_price=300000.0,
            generated_content="Test contract content for signature testing."
        )
    
    def test_create_signature_request(self):
        """Test creating signature requests for contract parties."""
        requests = self.signature_service.create_signature_request(self.test_contract)
        
        # Should create requests only for parties requiring signatures
        assert len(requests) == 2  # Buyer and seller, not agent
        
        # Verify request details
        buyer_request = next((r for r in requests if r.signer_role == "buyer"), None)
        seller_request = next((r for r in requests if r.signer_role == "seller"), None)
        
        assert buyer_request is not None
        assert buyer_request.signer_name == "John Buyer"
        assert buyer_request.signer_email == "john@example.com"
        assert buyer_request.status == "sent"
        assert buyer_request.sent_at is not None
        assert buyer_request.document_url is not None
        assert buyer_request.expires_at > datetime.now()
        
        assert seller_request is not None
        assert seller_request.signer_name == "Jane Seller"
        assert seller_request.signer_email == "jane@example.com"
        
        # Contract should be updated
        assert self.test_contract.status == ContractStatus.PENDING_SIGNATURE
        assert len(self.test_contract.signature_requests) == 2
        
        # Requests should be stored in service
        assert len(self.signature_service.signature_requests) == 2
    
    def test_create_signature_request_missing_email(self):
        """Test error handling when party has no email."""
        # Create contract with party missing email
        contract = ContractDocument(
            template_id=uuid4(),
            contract_type=ContractType.PURCHASE_AGREEMENT,
            parties=[
                ContractParty(
                    name="No Email Party", 
                    role="buyer", 
                    signature_required=True
                    # Missing email
                )
            ],
            generated_content="Test contract"
        )
        
        with pytest.raises(ValueError, match="has no email address"):
            self.signature_service.create_signature_request(contract)
    
    def test_check_signature_status(self):
        """Test checking signature request status."""
        requests = self.signature_service.create_signature_request(self.test_contract)
        request = requests[0]
        
        # Check initial status
        status_check = self.signature_service.check_signature_status(request.id)
        assert status_check is not None
        assert status_check.id == request.id
        
        # Status might change due to mock API
        assert status_check.status in ["sent", "delivered", "signed", "declined"]
    
    def test_get_signature_request(self):
        """Test retrieving signature request by ID."""
        requests = self.signature_service.create_signature_request(self.test_contract)
        request = requests[0]
        
        retrieved = self.signature_service.get_signature_request(request.id)
        assert retrieved is not None
        assert retrieved.id == request.id
        assert retrieved.signer_name == request.signer_name
        
        # Test non-existent request
        fake_id = uuid4()
        assert self.signature_service.get_signature_request(fake_id) is None
    
    def test_list_signature_requests(self):
        """Test listing signature requests with filters."""
        # Create requests for multiple contracts
        requests1 = self.signature_service.create_signature_request(self.test_contract)
        
        contract2 = ContractDocument(
            template_id=uuid4(),
            contract_type=ContractType.LEASE_AGREEMENT,
            parties=[
                ContractParty(name="Alice Tenant", role="tenant", email="alice@example.com", signature_required=True)
            ],
            generated_content="Lease contract"
        )
        requests2 = self.signature_service.create_signature_request(contract2)
        
        # List all requests
        all_requests = self.signature_service.list_signature_requests()
        assert len(all_requests) >= 3  # At least 2 from contract1 + 1 from contract2
        
        # Filter by contract ID
        contract1_requests = self.signature_service.list_signature_requests(
            contract_id=self.test_contract.id
        )
        assert len(contract1_requests) == 2
        
        # Filter by status
        sent_requests = self.signature_service.list_signature_requests(status="sent")
        assert all(r.status == "sent" for r in sent_requests)
    
    def test_send_reminder(self):
        """Test sending signature reminders."""
        requests = self.signature_service.create_signature_request(self.test_contract)
        request = requests[0]
        
        initial_reminder_count = request.reminder_count
        
        # Send reminder
        result = self.signature_service.send_reminder(request.id)
        assert result is True
        
        # Check reminder count increased
        updated_request = self.signature_service.get_signature_request(request.id)
        assert updated_request.reminder_count == initial_reminder_count + 1
        
        # Test with custom message
        custom_message = "Please sign the contract urgently!"
        result2 = self.signature_service.send_reminder(request.id, custom_message)
        assert result2 is True
        
        # Test non-existent request
        fake_id = uuid4()
        result3 = self.signature_service.send_reminder(fake_id)
        assert result3 is False
    
    def test_process_signature_callback(self):
        """Test processing signature callbacks from e-signature provider."""
        requests = self.signature_service.create_signature_request(self.test_contract)
        request = requests[0]
        
        # Mock callback data for signed document
        callback_data = {
            "request_id": str(request.id),
            "status": "signed",
            "signed_at": datetime.now().isoformat()
        }
        
        result = self.signature_service.process_signature_callback(callback_data)
        assert result is True
        
        # Check request was updated
        updated_request = self.signature_service.get_signature_request(request.id)
        assert updated_request.status == "signed"
        assert updated_request.signed_at is not None
        
        # Check signed document was stored
        signed_doc = self.signature_service.get_signed_document(self.test_contract.id)
        assert signed_doc is not None
        assert "content" in signed_doc
        assert "signatures" in signed_doc
        
        # Test invalid callback data
        invalid_callback = {"invalid": "data"}
        result2 = self.signature_service.process_signature_callback(invalid_callback)
        assert result2 is False
    
    def test_check_contract_completion(self):
        """Test checking if all required signatures are complete."""
        requests = self.signature_service.create_signature_request(self.test_contract)
        
        # Initially not complete
        assert self.signature_service.check_contract_completion(self.test_contract) is False
        
        # Mark first request as signed
        requests[0].status = "signed"
        requests[0].signed_at = datetime.now()
        
        # Still not complete (need both signatures)
        assert self.signature_service.check_contract_completion(self.test_contract) is False
        
        # Mark second request as signed
        requests[1].status = "signed"
        requests[1].signed_at = datetime.now()
        
        # Now complete
        assert self.signature_service.check_contract_completion(self.test_contract) is True
    
    def test_finalize_contract(self):
        """Test finalizing a contract after all signatures are complete."""
        requests = self.signature_service.create_signature_request(self.test_contract)
        
        # Cannot finalize incomplete contract
        result = self.signature_service.finalize_contract(self.test_contract)
        assert result is False
        assert self.test_contract.status != ContractStatus.EXECUTED
        
        # Mark all requests as signed
        for request in requests:
            request.status = "signed"
            request.signed_at = datetime.now()
        
        # Now can finalize
        result = self.signature_service.finalize_contract(self.test_contract)
        assert result is True
        assert self.test_contract.status == ContractStatus.EXECUTED
        assert self.test_contract.executed_at is not None
        assert len(self.test_contract.signatures) == 2
        
        # Verify signature details
        signature_names = [sig["signer_name"] for sig in self.test_contract.signatures]
        assert "John Buyer" in signature_names
        assert "Jane Seller" in signature_names
    
    def test_cancel_signature_request(self):
        """Test cancelling a signature request."""
        requests = self.signature_service.create_signature_request(self.test_contract)
        request = requests[0]
        
        # Cancel request
        result = self.signature_service.cancel_signature_request(
            request.id, 
            reason="Contract terms changed"
        )
        assert result is True
        
        # Check status updated
        updated_request = self.signature_service.get_signature_request(request.id)
        assert updated_request.status == "cancelled"
        
        # Cannot cancel already completed request
        request.status = "signed"
        result2 = self.signature_service.cancel_signature_request(request.id)
        assert result2 is False
        
        # Test non-existent request
        fake_id = uuid4()
        result3 = self.signature_service.cancel_signature_request(fake_id)
        assert result3 is False
    
    def test_get_signature_analytics(self):
        """Test signature analytics generation."""
        # Create multiple signature requests
        requests1 = self.signature_service.create_signature_request(self.test_contract)
        
        contract2 = ContractDocument(
            template_id=uuid4(),
            contract_type=ContractType.LEASE_AGREEMENT,
            parties=[
                ContractParty(name="Alice Tenant", role="tenant", email="alice@example.com", signature_required=True)
            ],
            generated_content="Lease contract"
        )
        requests2 = self.signature_service.create_signature_request(contract2)
        
        # Mark some as signed
        requests1[0].status = "signed"
        requests1[0].signed_at = datetime.now()
        requests2[0].status = "declined"
        
        # Get overall analytics
        analytics = self.signature_service.get_signature_analytics()
        
        assert analytics["total_requests"] >= 3
        assert "completion_rate" in analytics
        assert "status_breakdown" in analytics
        assert "signed_count" in analytics
        assert "pending_count" in analytics
        
        # Get contract-specific analytics
        contract_analytics = self.signature_service.get_signature_analytics(
            contract_id=self.test_contract.id
        )
        assert contract_analytics["total_requests"] == 2
        assert contract_analytics["signed_count"] == 1
    
    def test_signature_request_expiry(self):
        """Test handling of expired signature requests."""
        requests = self.signature_service.create_signature_request(self.test_contract)
        request = requests[0]
        
        # Set expiry to past date
        request.expires_at = datetime.now() - timedelta(days=1)
        
        # Try to send reminder - should fail due to expiry
        result = self.signature_service.send_reminder(request.id)
        assert result is False
        assert request.status == "expired"
    
    def test_contract_with_no_signature_requirements(self):
        """Test contract with no parties requiring signatures."""
        contract = ContractDocument(
            template_id=uuid4(),
            contract_type=ContractType.PURCHASE_AGREEMENT,
            parties=[
                ContractParty(name="Observer", role="observer", signature_required=False)
            ],
            generated_content="Contract with no signature requirements"
        )
        
        # Should create no signature requests
        requests = self.signature_service.create_signature_request(contract)
        assert len(requests) == 0
        
        # Contract should be immediately complete
        assert self.signature_service.check_contract_completion(contract) is True
        
        # Should be able to finalize immediately
        result = self.signature_service.finalize_contract(contract)
        assert result is True
        assert contract.status == ContractStatus.EXECUTED
    
    def test_custom_signature_message(self):
        """Test creating signature request with custom message."""
        custom_message = "Please review and sign this important contract by end of day."
        
        requests = self.signature_service.create_signature_request(
            self.test_contract, 
            custom_message=custom_message
        )
        
        # Requests should be created successfully
        assert len(requests) == 2
        assert all(r.status == "sent" for r in requests)
        
        # In a real implementation, we would verify the custom message was used
        # For now, we just verify the requests were created
    
    def test_get_signed_document(self):
        """Test retrieving signed documents."""
        requests = self.signature_service.create_signature_request(self.test_contract)
        
        # Initially no signed document
        signed_doc = self.signature_service.get_signed_document(self.test_contract.id)
        assert signed_doc is None
        
        # Simulate signature completion
        callback_data = {
            "request_id": str(requests[0].id),
            "status": "signed",
            "signed_at": datetime.now().isoformat()
        }
        
        self.signature_service.process_signature_callback(callback_data)
        
        # Now should have signed document
        signed_doc = self.signature_service.get_signed_document(self.test_contract.id)
        assert signed_doc is not None
        assert "content" in signed_doc
        assert "signatures" in signed_doc
        assert "downloaded_at" in signed_doc