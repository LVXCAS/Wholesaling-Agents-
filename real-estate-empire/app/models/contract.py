"""
Contract models for the real estate empire system.
Handles contract templates, clauses, and contract generation.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class ContractType(str, Enum):
    """Types of real estate contracts."""
    PURCHASE_AGREEMENT = "purchase_agreement"
    WHOLESALE_ASSIGNMENT = "wholesale_assignment"
    LEASE_AGREEMENT = "lease_agreement"
    OPTION_CONTRACT = "option_contract"
    JOINT_VENTURE = "joint_venture"
    MANAGEMENT_AGREEMENT = "management_agreement"


class ContractStatus(str, Enum):
    """Status of a contract."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PENDING_SIGNATURE = "pending_signature"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ClauseType(str, Enum):
    """Types of contract clauses."""
    STANDARD = "standard"
    CONDITIONAL = "conditional"
    OPTIONAL = "optional"
    REQUIRED = "required"


class ContractClause(BaseModel):
    """Individual contract clause."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    clause_type: ClauseType
    content: str
    variables: Dict[str, str] = Field(default_factory=dict)  # Variable placeholders
    conditions: Dict[str, Any] = Field(default_factory=dict)  # Conditions for inclusion
    category: str  # e.g., "financing", "inspection", "closing"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ContractTemplate(BaseModel):
    """Contract template with clauses and structure."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    contract_type: ContractType
    description: str
    version: str = "1.0"
    clauses: List[UUID] = Field(default_factory=list)  # References to ContractClause IDs
    required_fields: Dict[str, str] = Field(default_factory=dict)  # Field name -> type
    optional_fields: Dict[str, str] = Field(default_factory=dict)
    template_structure: Dict[str, Any] = Field(default_factory=dict)  # Document structure
    is_active: bool = True
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ContractParty(BaseModel):
    """Party involved in a contract."""
    name: str
    role: str  # "buyer", "seller", "agent", "attorney", etc.
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    entity_type: Optional[str] = None  # "individual", "corporation", "llc", etc.
    signature_required: bool = True


class ContractDocument(BaseModel):
    """Generated contract document."""
    id: UUID = Field(default_factory=uuid4)
    template_id: UUID
    contract_type: ContractType
    status: ContractStatus = ContractStatus.DRAFT
    parties: List[ContractParty] = Field(default_factory=list)
    deal_id: Optional[UUID] = None
    property_address: Optional[str] = None
    
    # Contract terms
    purchase_price: Optional[float] = None
    earnest_money: Optional[float] = None
    closing_date: Optional[datetime] = None
    inspection_period: Optional[int] = None  # days
    financing_contingency: Optional[bool] = None
    
    # Document content
    generated_content: Optional[str] = None
    field_values: Dict[str, Any] = Field(default_factory=dict)
    included_clauses: List[UUID] = Field(default_factory=list)
    
    # Signatures and execution
    signature_requests: List[Dict[str, Any]] = Field(default_factory=list)
    signatures: List[Dict[str, Any]] = Field(default_factory=list)
    executed_at: Optional[datetime] = None
    
    # Metadata
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ContractValidationResult(BaseModel):
    """Result of contract validation."""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class ContractGenerationRequest(BaseModel):
    """Request to generate a contract."""
    template_id: UUID
    deal_data: Dict[str, Any]
    parties: List[ContractParty]
    custom_terms: Dict[str, Any] = Field(default_factory=dict)
    include_optional_clauses: List[str] = Field(default_factory=list)
    exclude_clauses: List[str] = Field(default_factory=list)


class SignatureRequest(BaseModel):
    """Electronic signature request."""
    id: UUID = Field(default_factory=uuid4)
    contract_id: UUID
    signer_name: str
    signer_email: str
    signer_role: str
    document_url: Optional[str] = None
    signature_url: Optional[str] = None
    status: str = "pending"  # pending, sent, signed, declined, expired
    sent_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    reminder_count: int = 0
    expires_at: Optional[datetime] = None


class ContractAnalytics(BaseModel):
    """Analytics data for contracts."""
    template_id: UUID
    usage_count: int = 0
    success_rate: float = 0.0  # Percentage of contracts that get executed
    average_time_to_signature: Optional[float] = None  # days
    common_modifications: List[str] = Field(default_factory=list)
    rejection_reasons: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)