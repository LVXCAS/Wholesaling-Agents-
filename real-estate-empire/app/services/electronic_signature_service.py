"""
Electronic signature service.
Handles signature requests, tracking, reminders, and document processing.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from app.models.contract import (
    ContractDocument, SignatureRequest, ContractParty, ContractStatus
)


class ElectronicSignatureService:
    """Service for managing electronic signatures."""
    
    def __init__(self):
        # In-memory storage for demo - would be replaced with database and external e-signature API
        self.signature_requests: Dict[UUID, SignatureRequest] = {}
        self.signed_documents: Dict[UUID, Dict[str, Any]] = {}
        
        # Mock configuration for e-signature provider
        self.config = {
            "provider": "DocuSign",  # Could be DocuSign, HelloSign, Adobe Sign, etc.
            "api_key": "mock_api_key",
            "callback_url": "https://api.realestate-empire.com/signatures/callback",
            "default_expiry_days": 30
        }
    
    def create_signature_request(self, contract: ContractDocument, 
                                custom_message: Optional[str] = None) -> List[SignatureRequest]:
        """Create signature requests for all parties requiring signatures."""
        signature_requests = []
        
        for party in contract.parties:
            if not party.signature_required:
                continue
            
            if not party.email:
                raise ValueError(f"Party '{party.name}' requires signature but has no email address")
            
            # Create signature request
            request = SignatureRequest(
                contract_id=contract.id,
                signer_name=party.name,
                signer_email=party.email,
                signer_role=party.role,
                expires_at=datetime.now() + timedelta(days=self.config["default_expiry_days"])
            )
            
            # Generate document URL (mock)
            request.document_url = self._generate_document_url(contract, request.id)
            
            # Send signature request
            self._send_signature_request(request, contract, custom_message)
            
            # Store request
            self.signature_requests[request.id] = request
            signature_requests.append(request)
        
        # Update contract signature requests
        contract.signature_requests = [
            {
                "id": str(req.id),
                "signer_name": req.signer_name,
                "signer_email": req.signer_email,
                "status": req.status,
                "sent_at": req.sent_at.isoformat() if req.sent_at else None
            }
            for req in signature_requests
        ]
        
        # Update contract status
        if signature_requests:
            contract.status = ContractStatus.PENDING_SIGNATURE
            contract.updated_at = datetime.now()
        
        return signature_requests
    
    def _generate_document_url(self, contract: ContractDocument, request_id: UUID) -> str:
        """Generate a secure URL for the document to be signed."""
        # In a real implementation, this would upload the document to the e-signature provider
        # and return the signing URL
        return f"https://mock-esign-provider.com/sign/{contract.id}/{request_id}"
    
    def _send_signature_request(self, request: SignatureRequest, 
                               contract: ContractDocument,
                               custom_message: Optional[str] = None):
        """Send signature request via e-signature provider."""
        # Mock implementation - in reality, this would call the e-signature provider's API
        
        # Prepare email content
        subject = f"Signature Required: {contract.contract_type.value.replace('_', ' ').title()}"
        
        if custom_message:
            message = custom_message
        else:
            message = self._generate_default_signature_message(request, contract)
        
        # Mock API call to e-signature provider
        api_response = self._mock_esign_api_call("send_signature_request", {
            "document_content": contract.generated_content,
            "signer_email": request.signer_email,
            "signer_name": request.signer_name,
            "subject": subject,
            "message": message,
            "callback_url": self.config["callback_url"],
            "expires_at": request.expires_at.isoformat()
        })
        
        # Update request with API response
        request.signature_url = api_response.get("signature_url")
        request.status = "sent"
        request.sent_at = datetime.now()
    
    def _generate_default_signature_message(self, request: SignatureRequest, 
                                          contract: ContractDocument) -> str:
        """Generate default signature request message."""
        return f"""
Dear {request.signer_name},

You have been requested to sign a {contract.contract_type.value.replace('_', ' ').title()}.

Property Address: {contract.property_address or 'N/A'}
Your Role: {request.signer_role.title()}

Please click the link below to review and sign the document:
{request.signature_url or '[SIGNATURE_URL]'}

This signature request will expire on {request.expires_at.strftime('%B %d, %Y')}.

If you have any questions, please contact us immediately.

Best regards,
Real Estate Empire Team
        """.strip()
    
    def _mock_esign_api_call(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock API call to e-signature provider."""
        # This simulates calling an external e-signature service
        if endpoint == "send_signature_request":
            return {
                "success": True,
                "signature_url": f"https://mock-esign-provider.com/sign/{uuid4()}",
                "envelope_id": str(uuid4()),
                "status": "sent"
            }
        elif endpoint == "get_signature_status":
            # Mock different statuses for testing
            import random
            statuses = ["sent", "delivered", "signed", "declined"]
            return {
                "status": random.choice(statuses),
                "signed_at": datetime.now().isoformat() if random.choice([True, False]) else None
            }
        elif endpoint == "download_signed_document":
            return {
                "document_content": "Mock signed document content",
                "signatures": [
                    {
                        "signer_name": data.get("signer_name"),
                        "signed_at": datetime.now().isoformat(),
                        "ip_address": "192.168.1.1"
                    }
                ]
            }
        elif endpoint == "send_reminder":
            return {"success": True}
        elif endpoint == "cancel_signature_request":
            return {"success": True}
        
        return {"success": False, "error": "Unknown endpoint"}
    
    def check_signature_status(self, request_id: UUID) -> Optional[SignatureRequest]:
        """Check the status of a signature request."""
        request = self.signature_requests.get(request_id)
        if not request:
            return None
        
        # Query e-signature provider for status update
        api_response = self._mock_esign_api_call("get_signature_status", {
            "request_id": str(request_id)
        })
        
        # Update request status
        old_status = request.status
        request.status = api_response.get("status", request.status)
        
        if api_response.get("signed_at") and not request.signed_at:
            request.signed_at = datetime.fromisoformat(api_response["signed_at"])
        
        # Log status change
        if old_status != request.status:
            print(f"Signature request {request_id} status changed: {old_status} -> {request.status}")
        
        return request
    
    def get_signature_request(self, request_id: UUID) -> Optional[SignatureRequest]:
        """Get a signature request by ID."""
        return self.signature_requests.get(request_id)
    
    def list_signature_requests(self, contract_id: Optional[UUID] = None,
                               status: Optional[str] = None) -> List[SignatureRequest]:
        """List signature requests with optional filtering."""
        requests = list(self.signature_requests.values())
        
        if contract_id:
            requests = [r for r in requests if r.contract_id == contract_id]
        
        if status:
            requests = [r for r in requests if r.status == status]
        
        return sorted(requests, key=lambda r: r.sent_at or datetime.min, reverse=True)
    
    def send_reminder(self, request_id: UUID, custom_message: Optional[str] = None) -> bool:
        """Send a reminder for a pending signature request."""
        request = self.signature_requests.get(request_id)
        if not request:
            return False
        
        if request.status in ["signed", "declined", "expired"]:
            return False  # Cannot send reminder for completed requests
        
        # Check if request has expired
        if request.expires_at and datetime.now() > request.expires_at:
            request.status = "expired"
            return False
        
        # Prepare reminder message
        if custom_message:
            message = custom_message
        else:
            message = f"""
Dear {request.signer_name},

This is a reminder that you have a pending signature request.

Please click the link below to review and sign the document:
{request.signature_url}

This signature request will expire on {request.expires_at.strftime('%B %d, %Y')}.

Best regards,
Real Estate Empire Team
            """.strip()
        
        # Mock sending reminder
        api_response = self._mock_esign_api_call("send_reminder", {
            "request_id": str(request_id),
            "message": message
        })
        
        if api_response.get("success"):
            request.reminder_count += 1
            return True
        
        return False
    
    def process_signature_callback(self, callback_data: Dict[str, Any]) -> bool:
        """Process callback from e-signature provider."""
        # Extract information from callback
        request_id = callback_data.get("request_id")
        if not request_id:
            return False
        
        try:
            request_uuid = UUID(request_id)
        except ValueError:
            return False
        
        request = self.signature_requests.get(request_uuid)
        if not request:
            return False
        
        # Update request status
        old_status = request.status
        request.status = callback_data.get("status", request.status)
        
        if callback_data.get("signed_at"):
            request.signed_at = datetime.fromisoformat(callback_data["signed_at"])
        
        # If signed, download and store the signed document
        if request.status == "signed":
            self._download_signed_document(request)
        
        print(f"Signature callback processed: {request_id} - {old_status} -> {request.status}")
        return True
    
    def _download_signed_document(self, request: SignatureRequest):
        """Download and store the signed document."""
        api_response = self._mock_esign_api_call("download_signed_document", {
            "request_id": str(request.id),
            "signer_name": request.signer_name
        })
        
        if api_response.get("document_content"):
            # Store signed document
            self.signed_documents[request.contract_id] = {
                "content": api_response["document_content"],
                "signatures": api_response.get("signatures", []),
                "downloaded_at": datetime.now().isoformat()
            }
    
    def get_signed_document(self, contract_id: UUID) -> Optional[Dict[str, Any]]:
        """Get the signed document for a contract."""
        return self.signed_documents.get(contract_id)
    
    def check_contract_completion(self, contract: ContractDocument) -> bool:
        """Check if all required signatures have been completed."""
        required_signatures = [p for p in contract.parties if p.signature_required]
        
        if not required_signatures:
            return True  # No signatures required
        
        # Check signature requests
        contract_requests = [
            r for r in self.signature_requests.values()
            if r.contract_id == contract.id
        ]
        
        signed_requests = [r for r in contract_requests if r.status == "signed"]
        
        # All required parties must have signed
        signed_emails = {r.signer_email for r in signed_requests}
        required_emails = {p.email for p in required_signatures}
        
        return required_emails.issubset(signed_emails)
    
    def finalize_contract(self, contract: ContractDocument) -> bool:
        """Finalize a contract after all signatures are complete."""
        if not self.check_contract_completion(contract):
            return False
        
        # Update contract status
        contract.status = ContractStatus.EXECUTED
        contract.executed_at = datetime.now()
        contract.updated_at = datetime.now()
        
        # Update contract signatures list
        contract_requests = [
            r for r in self.signature_requests.values()
            if r.contract_id == contract.id and r.status == "signed"
        ]
        
        contract.signatures = [
            {
                "signer_name": r.signer_name,
                "signer_email": r.signer_email,
                "signer_role": r.signer_role,
                "signed_at": r.signed_at.isoformat() if r.signed_at else None,
                "signature_id": str(r.id)
            }
            for r in contract_requests
        ]
        
        return True
    
    def cancel_signature_request(self, request_id: UUID, reason: Optional[str] = None) -> bool:
        """Cancel a pending signature request."""
        request = self.signature_requests.get(request_id)
        if not request:
            return False
        
        if request.status in ["signed", "declined", "expired"]:
            return False  # Cannot cancel completed requests
        
        # Mock API call to cancel request
        api_response = self._mock_esign_api_call("cancel_signature_request", {
            "request_id": str(request_id),
            "reason": reason
        })
        
        if api_response.get("success"):
            request.status = "cancelled"
            return True
        
        return False
    
    def get_signature_analytics(self, contract_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get analytics for signature requests."""
        requests = self.list_signature_requests(contract_id=contract_id)
        
        if not requests:
            return {
                "total_requests": 0,
                "completion_rate": 0.0,
                "average_time_to_sign": None,
                "status_breakdown": {}
            }
        
        # Calculate metrics
        total_requests = len(requests)
        signed_requests = [r for r in requests if r.status == "signed"]
        completion_rate = len(signed_requests) / total_requests * 100
        
        # Calculate average time to sign
        sign_times = []
        for request in signed_requests:
            if request.sent_at and request.signed_at:
                time_diff = request.signed_at - request.sent_at
                sign_times.append(time_diff.total_seconds() / 3600)  # Hours
        
        average_time_to_sign = sum(sign_times) / len(sign_times) if sign_times else None
        
        # Status breakdown
        status_breakdown = {}
        for request in requests:
            status = request.status
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        return {
            "total_requests": total_requests,
            "completion_rate": completion_rate,
            "average_time_to_sign": average_time_to_sign,
            "status_breakdown": status_breakdown,
            "signed_count": len(signed_requests),
            "pending_count": len([r for r in requests if r.status in ["sent", "delivered"]])
        }