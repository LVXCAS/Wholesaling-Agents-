"""
Contract management service.
Handles contract storage, organization, search, version control, and analytics.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4

from app.models.contract import (
    ContractDocument, ContractTemplate, ContractStatus, ContractType,
    ContractValidationResult, ContractAnalytics
)
from app.services.contract_template_service import ContractTemplateService
from app.services.contract_generation_service import ContractGenerationService
from app.services.electronic_signature_service import ElectronicSignatureService


class ContractManagementService:
    """Service for comprehensive contract management."""
    
    def __init__(self, 
                 template_service: ContractTemplateService,
                 generation_service: ContractGenerationService,
                 signature_service: ElectronicSignatureService):
        self.template_service = template_service
        self.generation_service = generation_service
        self.signature_service = signature_service
        
        # In-memory storage for demo - would be replaced with database
        self.contracts: Dict[UUID, ContractDocument] = {}
        self.contract_versions: Dict[UUID, List[ContractDocument]] = {}
        self.contract_analytics: Dict[UUID, ContractAnalytics] = {}
        
        # Search index for contracts
        self.search_index: Dict[str, List[UUID]] = {}
    
    def store_contract(self, contract: ContractDocument) -> ContractDocument:
        """Store a contract in the management system."""
        # Generate ID if not present
        if not contract.id:
            contract.id = uuid4()
        
        # Set timestamps
        if not contract.created_at:
            contract.created_at = datetime.now()
        contract.updated_at = datetime.now()
        
        # Store contract
        self.contracts[contract.id] = contract
        
        # Initialize version history
        if contract.id not in self.contract_versions:
            self.contract_versions[contract.id] = []
        
        # Add to search index
        self._update_search_index(contract)
        
        # Initialize analytics
        if contract.template_id not in self.contract_analytics:
            self.contract_analytics[contract.template_id] = ContractAnalytics(
                template_id=contract.template_id
            )
        
        return contract
    
    def get_contract(self, contract_id: UUID) -> Optional[ContractDocument]:
        """Retrieve a contract by ID."""
        return self.contracts.get(contract_id)
    
    def list_contracts(self, 
                      contract_type: Optional[ContractType] = None,
                      status: Optional[ContractStatus] = None,
                      deal_id: Optional[UUID] = None,
                      created_after: Optional[datetime] = None,
                      created_before: Optional[datetime] = None,
                      limit: Optional[int] = None,
                      offset: int = 0) -> List[ContractDocument]:
        """List contracts with optional filtering."""
        contracts = list(self.contracts.values())
        
        # Apply filters
        if contract_type:
            contracts = [c for c in contracts if c.contract_type == contract_type]
        
        if status:
            contracts = [c for c in contracts if c.status == status]
        
        if deal_id:
            contracts = [c for c in contracts if c.deal_id == deal_id]
        
        if created_after:
            contracts = [c for c in contracts if c.created_at >= created_after]
        
        if created_before:
            contracts = [c for c in contracts if c.created_at <= created_before]
        
        # Sort by creation date (newest first)
        contracts.sort(key=lambda c: c.created_at, reverse=True)
        
        # Apply pagination
        if offset > 0:
            contracts = contracts[offset:]
        
        if limit:
            contracts = contracts[:limit]
        
        return contracts
    
    def search_contracts(self, query: str, 
                        contract_type: Optional[ContractType] = None,
                        limit: int = 50) -> List[ContractDocument]:
        """Search contracts by content, parties, or property address."""
        query_lower = query.lower()
        matching_contracts = []
        
        for contract in self.contracts.values():
            # Skip if contract type filter doesn't match
            if contract_type and contract.contract_type != contract_type:
                continue
            
            # Search in various fields
            search_fields = [
                contract.property_address or "",
                contract.generated_content or "",
                " ".join([p.name for p in contract.parties]),
                " ".join([p.email or "" for p in contract.parties])
            ]
            
            # Check if query matches any field
            if any(query_lower in field.lower() for field in search_fields):
                matching_contracts.append(contract)
        
        # Sort by relevance (simple: by creation date)
        matching_contracts.sort(key=lambda c: c.created_at, reverse=True)
        
        return matching_contracts[:limit]
    
    def _update_search_index(self, contract: ContractDocument):
        """Update search index with contract information."""
        # Extract searchable terms
        terms = []
        
        if contract.property_address:
            terms.extend(contract.property_address.lower().split())
        
        for party in contract.parties:
            terms.extend(party.name.lower().split())
            if party.email:
                terms.append(party.email.lower())
        
        if contract.generated_content:
            # Extract key terms from content (simplified)
            content_words = contract.generated_content.lower().split()
            # Add only meaningful words (length > 3)
            terms.extend([word for word in content_words if len(word) > 3])
        
        # Update index
        for term in set(terms):  # Remove duplicates
            if term not in self.search_index:
                self.search_index[term] = []
            if contract.id not in self.search_index[term]:
                self.search_index[term].append(contract.id)
    
    def update_contract(self, contract_id: UUID, 
                       updates: Dict[str, Any],
                       create_version: bool = True) -> Optional[ContractDocument]:
        """Update a contract with version control."""
        contract = self.contracts.get(contract_id)
        if not contract:
            return None
        
        # Create version backup if requested
        if create_version:
            self._create_contract_version(contract)
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(contract, key):
                setattr(contract, key, value)
        
        contract.updated_at = datetime.now()
        
        # Update search index
        self._update_search_index(contract)
        
        return contract
    
    def _create_contract_version(self, contract: ContractDocument):
        """Create a version backup of the contract."""
        # Create a copy of the contract
        version_data = contract.model_dump()
        version_data['id'] = uuid4()  # New ID for version
        version_contract = ContractDocument(**version_data)
        
        # Store in version history
        if contract.id not in self.contract_versions:
            self.contract_versions[contract.id] = []
        
        self.contract_versions[contract.id].append(version_contract)
    
    def get_contract_versions(self, contract_id: UUID) -> List[ContractDocument]:
        """Get version history for a contract."""
        return self.contract_versions.get(contract_id, [])
    
    def restore_contract_version(self, contract_id: UUID, 
                                version_index: int) -> Optional[ContractDocument]:
        """Restore a contract to a previous version."""
        versions = self.contract_versions.get(contract_id, [])
        
        if version_index < 0 or version_index >= len(versions):
            return None
        
        # Get the version to restore
        version_to_restore = versions[version_index]
        
        # Create current version backup
        current_contract = self.contracts.get(contract_id)
        if current_contract:
            self._create_contract_version(current_contract)
        
        # Restore the version (keep original ID and timestamps)
        restored_data = version_to_restore.model_dump()
        restored_data['id'] = contract_id
        restored_data['updated_at'] = datetime.now()
        
        restored_contract = ContractDocument(**restored_data)
        self.contracts[contract_id] = restored_contract
        
        return restored_contract
    
    def delete_contract(self, contract_id: UUID, 
                       soft_delete: bool = True) -> bool:
        """Delete a contract (soft or hard delete)."""
        contract = self.contracts.get(contract_id)
        if not contract:
            return False
        
        if soft_delete:
            # Mark as cancelled instead of deleting
            contract.status = ContractStatus.CANCELLED
            contract.updated_at = datetime.now()
        else:
            # Hard delete
            del self.contracts[contract_id]
            
            # Clean up versions
            if contract_id in self.contract_versions:
                del self.contract_versions[contract_id]
            
            # Clean up search index
            for term_contracts in self.search_index.values():
                if contract_id in term_contracts:
                    term_contracts.remove(contract_id)
        
        return True
    
    def get_contract_analytics(self, 
                              template_id: Optional[UUID] = None,
                              contract_type: Optional[ContractType] = None,
                              date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Get comprehensive contract analytics."""
        # Filter contracts based on criteria
        contracts = list(self.contracts.values())
        
        if template_id:
            contracts = [c for c in contracts if c.template_id == template_id]
        
        if contract_type:
            contracts = [c for c in contracts if c.contract_type == contract_type]
        
        if date_range:
            start_date, end_date = date_range
            contracts = [c for c in contracts if start_date <= c.created_at <= end_date]
        
        if not contracts:
            return {
                "total_contracts": 0,
                "status_breakdown": {},
                "completion_rate": 0.0,
                "average_time_to_execution": None,
                "template_usage": {},
                "monthly_trends": []
            }
        
        # Calculate metrics
        total_contracts = len(contracts)
        
        # Status breakdown
        status_breakdown = {}
        for contract in contracts:
            status = contract.status.value
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        # Completion rate
        executed_contracts = [c for c in contracts if c.status == ContractStatus.EXECUTED]
        completion_rate = len(executed_contracts) / total_contracts * 100
        
        # Average time to execution
        execution_times = []
        for contract in executed_contracts:
            if contract.executed_at:
                time_diff = contract.executed_at - contract.created_at
                execution_times.append(time_diff.total_seconds() / 86400)  # Days
        
        average_time_to_execution = (
            sum(execution_times) / len(execution_times) 
            if execution_times else None
        )
        
        # Template usage
        template_usage = {}
        for contract in contracts:
            template_id_str = str(contract.template_id)
            template_usage[template_id_str] = template_usage.get(template_id_str, 0) + 1
        
        # Monthly trends (last 12 months)
        monthly_trends = self._calculate_monthly_trends(contracts)
        
        return {
            "total_contracts": total_contracts,
            "status_breakdown": status_breakdown,
            "completion_rate": completion_rate,
            "average_time_to_execution": average_time_to_execution,
            "template_usage": template_usage,
            "monthly_trends": monthly_trends,
            "executed_count": len(executed_contracts),
            "pending_count": len([c for c in contracts if c.status == ContractStatus.PENDING_SIGNATURE])
        }
    
    def _calculate_monthly_trends(self, contracts: List[ContractDocument]) -> List[Dict[str, Any]]:
        """Calculate monthly contract creation trends."""
        # Group contracts by month
        monthly_data = {}
        
        for contract in contracts:
            month_key = contract.created_at.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "month": month_key,
                    "total": 0,
                    "executed": 0,
                    "pending": 0,
                    "cancelled": 0
                }
            
            monthly_data[month_key]["total"] += 1
            
            if contract.status == ContractStatus.EXECUTED:
                monthly_data[month_key]["executed"] += 1
            elif contract.status == ContractStatus.PENDING_SIGNATURE:
                monthly_data[month_key]["pending"] += 1
            elif contract.status == ContractStatus.CANCELLED:
                monthly_data[month_key]["cancelled"] += 1
        
        # Sort by month and return last 12 months
        sorted_months = sorted(monthly_data.values(), key=lambda x: x["month"])
        return sorted_months[-12:]  # Last 12 months
    
    def export_contract(self, contract_id: UUID, 
                       format: str = "json") -> Optional[Dict[str, Any]]:
        """Export contract in specified format."""
        contract = self.contracts.get(contract_id)
        if not contract:
            return None
        
        if format.lower() == "json":
            return {
                "contract": contract.model_dump(),
                "versions": [v.model_dump() for v in self.get_contract_versions(contract_id)],
                "signature_requests": self.signature_service.list_signature_requests(contract_id),
                "exported_at": datetime.now().isoformat()
            }
        elif format.lower() == "pdf":
            # In a real implementation, this would generate a PDF
            return {
                "format": "pdf",
                "content": contract.generated_content,
                "metadata": {
                    "contract_id": str(contract_id),
                    "contract_type": contract.contract_type.value,
                    "status": contract.status.value,
                    "parties": [p.model_dump() for p in contract.parties]
                }
            }
        
        return None
    
    def bulk_update_contracts(self, contract_ids: List[UUID], 
                             updates: Dict[str, Any]) -> List[UUID]:
        """Bulk update multiple contracts."""
        updated_ids = []
        
        for contract_id in contract_ids:
            if self.update_contract(contract_id, updates, create_version=False):
                updated_ids.append(contract_id)
        
        return updated_ids
    
    def get_contracts_by_party(self, party_email: str) -> List[ContractDocument]:
        """Get all contracts involving a specific party."""
        matching_contracts = []
        
        for contract in self.contracts.values():
            for party in contract.parties:
                if party.email and party.email.lower() == party_email.lower():
                    matching_contracts.append(contract)
                    break
        
        return sorted(matching_contracts, key=lambda c: c.created_at, reverse=True)
    
    def get_contracts_by_property(self, property_address: str) -> List[ContractDocument]:
        """Get all contracts for a specific property."""
        matching_contracts = []
        address_lower = property_address.lower()
        
        for contract in self.contracts.values():
            if (contract.property_address and 
                address_lower in contract.property_address.lower()):
                matching_contracts.append(contract)
        
        return sorted(matching_contracts, key=lambda c: c.created_at, reverse=True)
    
    def get_expiring_contracts(self, days_ahead: int = 30) -> List[ContractDocument]:
        """Get contracts with signature requests expiring soon."""
        expiring_contracts = []
        cutoff_date = datetime.now() + timedelta(days=days_ahead)
        
        for contract in self.contracts.values():
            if contract.status != ContractStatus.PENDING_SIGNATURE:
                continue
            
            # Check signature requests
            signature_requests = self.signature_service.list_signature_requests(contract.id)
            
            for request in signature_requests:
                if (request.status in ["sent", "delivered"] and 
                    request.expires_at and 
                    request.expires_at <= cutoff_date):
                    expiring_contracts.append(contract)
                    break
        
        return sorted(expiring_contracts, key=lambda c: c.created_at)
    
    def cleanup_old_versions(self, days_to_keep: int = 90) -> int:
        """Clean up old contract versions to save storage."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleaned_count = 0
        
        for contract_id, versions in self.contract_versions.items():
            # Keep only versions newer than cutoff date
            filtered_versions = [
                v for v in versions 
                if v.created_at >= cutoff_date
            ]
            
            cleaned_count += len(versions) - len(filtered_versions)
            self.contract_versions[contract_id] = filtered_versions
        
        return cleaned_count
    
    def validate_contract_integrity(self, contract_id: UUID) -> ContractValidationResult:
        """Validate contract integrity and completeness."""
        contract = self.contracts.get(contract_id)
        if not contract:
            return ContractValidationResult(
                is_valid=False,
                errors=["Contract not found"],
                warnings=[],
                missing_fields=[],
                suggestions=[]
            )
        
        # Use generation service validation
        return self.generation_service.validate_contract(contract)