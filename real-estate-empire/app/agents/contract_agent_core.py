"""
Contract Agent Core - Clean Implementation
Specialized agent for contract generation, electronic signatures, and transaction management
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
import re

from pydantic import BaseModel, Field

from ..core.base_agent import BaseAgent, AgentCapability, AgentStatus
from ..core.agent_state import AgentState, AgentType, Deal, DealStatus, StateManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContractType(str, Enum):
    """Types of contracts that can be generated"""
    PURCHASE_AGREEMENT = "purchase_agreement"
    ASSIGNMENT_CONTRACT = "assignment_contract"
    OPTION_CONTRACT = "option_contract"
    LEASE_OPTION = "lease_option"
    JOINT_VENTURE = "joint_venture"
    MANAGEMENT_AGREEMENT = "management_agreement"
    LISTING_AGREEMENT = "listing_agreement"
    DISCLOSURE_FORM = "disclosure_form"


class ContractStatus(str, Enum):
    """Status of contract documents"""
    DRAFT = "draft"
    GENERATED = "generated"
    UNDER_REVIEW = "under_review"
    SENT_FOR_SIGNATURE = "sent_for_signature"
    PARTIALLY_SIGNED = "partially_signed"
    FULLY_EXECUTED = "fully_executed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    AMENDED = "amended"


class TransactionStatus(str, Enum):
    """Status of real estate transactions"""
    INITIATED = "initiated"
    CONTRACT_EXECUTED = "contract_executed"
    DUE_DILIGENCE = "due_diligence"
    FINANCING_PENDING = "financing_pending"
    INSPECTION_PERIOD = "inspection_period"
    APPRAISAL_PENDING = "appraisal_pending"
    TITLE_REVIEW = "title_review"
    CLOSING_SCHEDULED = "closing_scheduled"
    CLOSING_COMPLETE = "closing_complete"
    TRANSACTION_FAILED = "transaction_failed"


class ContractTemplate(BaseModel):
    """Contract template model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    contract_type: ContractType
    template_content: str
    variables: List[str] = Field(default_factory=list)
    jurisdiction: str = "US"
    version: str = "1.0"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True


class ContractDocument(BaseModel):
    """Generated contract document"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deal_id: str
    contract_type: ContractType
    template_id: str
    status: ContractStatus = ContractStatus.DRAFT
    content: str
    variables_used: Dict[str, Any] = Field(default_factory=dict)
    parties: List[Dict[str, Any]] = Field(default_factory=list)
    terms: Dict[str, Any] = Field(default_factory=dict)
    signature_request_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Transaction(BaseModel):
    """Real estate transaction model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deal_id: str
    contract_id: str
    status: TransactionStatus = TransactionStatus.INITIATED
    milestones: List[Dict[str, Any]] = Field(default_factory=list)
    documents: List[str] = Field(default_factory=list)
    parties: List[Dict[str, Any]] = Field(default_factory=list)
    key_dates: Dict[str, datetime] = Field(default_factory=dict)
    notes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ContractTemplateEngine:
    """Engine for managing and processing contract templates"""
    
    def __init__(self):
        self.template_cache = {}
        self.variable_processors = {}
        logger.info("Contract template engine initialized")
    
    def process_template(self, template: ContractTemplate, variables: Dict[str, Any]) -> str:
        """Process a template with given variables"""
        try:
            content = template.template_content
            
            # Replace variables in template
            for var_name, var_value in variables.items():
                placeholder = f"{{{{{var_name}}}}}"
                content = content.replace(placeholder, str(var_value))
            
            return content
            
        except Exception as e:
            logger.error(f"Error processing template: {e}")
            return ""


class ElectronicSignatureService:
    """Service for managing electronic signatures"""
    
    def __init__(self):
        self.signature_requests = {}
        self.default_provider = "docusign"
        logger.info("Electronic signature service initialized")
    
    async def send_for_signature(self, document_path: str, signers: List[Dict[str, Any]], 
                                subject: str, message: str = "") -> Dict[str, Any]:
        """Send document for electronic signature"""
        try:
            request_id = str(uuid.uuid4())
            
            # Create signature request
            signature_request = {
                "id": request_id,
                "document_path": document_path,
                "signers": signers,
                "subject": subject,
                "message": message,
                "status": "sent",
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(days=30)
            }
            
            self.signature_requests[request_id] = signature_request
            
            logger.info(f"Sent document for signature: {request_id}")
            
            return {
                "success": True,
                "signature_request_id": request_id,
                "status": "sent",
                "expires_at": signature_request["expires_at"].isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending for signature: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class TransactionMonitor:
    """Monitor and track real estate transaction progress"""
    
    def __init__(self):
        self.active_transactions = {}
        logger.info("Transaction monitor initialized")
    
    def create_transaction(self, contract_id: str, deal_id: str, milestones: List[Dict[str, Any]]) -> str:
        """Create a new transaction to monitor"""
        try:
            transaction_id = str(uuid.uuid4())
            
            transaction = Transaction(
                id=transaction_id,
                deal_id=deal_id,
                contract_id=contract_id,
                status=TransactionStatus.INITIATED,
                milestones=milestones,
                key_dates={
                    "created": datetime.now(),
                    "expected_closing": datetime.now() + timedelta(days=30)
                }
            )
            
            self.active_transactions[transaction_id] = transaction
            
            logger.info(f"Created transaction monitor: {transaction_id}")
            
            return transaction_id
            
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            return ""
    
    def update_milestone(self, transaction_id: str, milestone_name: str, status: str) -> bool:
        """Update the status of a transaction milestone"""
        try:
            if transaction_id not in self.active_transactions:
                return False
            
            transaction = self.active_transactions[transaction_id]
            
            # Find and update milestone
            for milestone in transaction.milestones:
                if milestone.get("name") == milestone_name:
                    milestone["status"] = status
                    milestone["updated_at"] = datetime.now()
                    break
            
            logger.info(f"Updated milestone '{milestone_name}' for transaction {transaction_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating milestone: {e}")
            return False


class ContractAgentCore(BaseAgent):
    """
    Contract Agent Core - Autonomous Document Generation and Transaction Management
    
    Specialized agent for:
    - Contract template management with LangGraph integration
    - Dynamic contract generation using AI
    - Electronic signature workflow integration
    - Document management and storage system
    - Transaction coordination and monitoring
    """
    
    def __init__(self, name: str = "ContractAgent"):
        # Define agent capabilities
        capabilities = [
            AgentCapability(
                name="contract_generation",
                description="Generate contracts and legal documents from templates using AI",
                input_schema={
                    "contract_type": "string",
                    "deal_data": "object",
                    "parties": "array",
                    "terms": "object"
                },
                output_schema={
                    "contract_id": "string",
                    "document_path": "string",
                    "status": "string",
                    "content": "string"
                },
                required_tools=["contract_generation", "template_management"],
                estimated_duration=60
            ),
            AgentCapability(
                name="template_management",
                description="Manage contract templates and customization",
                input_schema={
                    "action": "string",
                    "template_data": "object"
                },
                output_schema={
                    "template_id": "string",
                    "success": "boolean",
                    "templates": "array"
                },
                required_tools=["template_management"],
                estimated_duration=30
            ),
            AgentCapability(
                name="electronic_signature",
                description="Manage electronic signature workflows",
                input_schema={
                    "document_path": "string",
                    "signers": "array",
                    "subject": "string",
                    "message": "string"
                },
                output_schema={
                    "signature_request_id": "string",
                    "signing_urls": "array",
                    "status": "string",
                    "expires_at": "string"
                },
                required_tools=["electronic_signature"],
                estimated_duration=30
            ),
            AgentCapability(
                name="document_management",
                description="Store, organize, and retrieve contract documents",
                input_schema={
                    "action": "string",
                    "document_id": "string",
                    "metadata": "object"
                },
                output_schema={
                    "success": "boolean",
                    "document_path": "string",
                    "version": "string"
                },
                required_tools=["document_management"],
                estimated_duration=15
            ),
            AgentCapability(
                name="transaction_tracking",
                description="Track and manage transaction progress",
                input_schema={
                    "transaction_id": "string",
                    "action": "string",
                    "milestone_data": "object"
                },
                output_schema={
                    "status": "string",
                    "milestones": "array",
                    "next_actions": "array",
                    "completion_percentage": "number"
                },
                required_tools=["transaction_tracking"],
                estimated_duration=20
            )
        ]
        
        # Contract-specific state (initialize before calling super().__init__)
        self.contract_templates: Dict[str, ContractTemplate] = {}
        self.active_contracts: Dict[str, ContractDocument] = {}
        self.active_transactions: Dict[str, Transaction] = {}
        self.signature_requests: Dict[str, Dict[str, Any]] = {}
        
        # Initialize base agent
        super().__init__(
            agent_type=AgentType.CONTRACT,
            name=name,
            description="Autonomous agent for contract generation, e-signatures, and transaction management with LangGraph integration",
            capabilities=capabilities
        )
        
        # Core systems
        self.template_engine = None
        self.signature_service = None
        self.transaction_monitor = None
        self.workflow_manager = None
        
        # Performance tracking
        self.contracts_generated = 0
        self.signatures_completed = 0
        self.transactions_managed = 0
        self.templates_created = 0
        
        logger.info(f"Initialized Contract Agent Core with LangGraph integration: {name}")
    
    def _agent_specific_initialization(self):
        """Contract agent specific initialization with LangGraph integration"""
        # Initialize core systems
        self._initialize_template_management_system()
        self._initialize_signature_service()
        self._initialize_transaction_monitoring()
        self._initialize_langgraph_integration()
        
        # Load default contract templates
        self._load_default_templates()
        
        logger.info("Contract Agent core initialization completed with LangGraph integration")
    
    def _initialize_langgraph_integration(self):
        """Initialize LangGraph workflow integration"""
        try:
            # Import workflow manager to avoid circular imports
            from .contract_workflows import ContractWorkflows
            
            # Initialize workflow manager
            self.workflow_manager = ContractWorkflows(self)
            
            logger.info("LangGraph workflow integration initialized")
        except Exception as e:
            logger.error(f"Error initializing LangGraph integration: {e}")
            self.workflow_manager = None
    
    def _initialize_template_management_system(self):
        """Initialize the contract template management system"""
        try:
            # Initialize template engine for dynamic contract generation
            self.template_engine = ContractTemplateEngine()
            
            logger.info("Contract template management system initialized")
        except Exception as e:
            logger.error(f"Error initializing template management: {e}")
            self.template_engine = None
    
    def _initialize_signature_service(self):
        """Initialize electronic signature service integration"""
        try:
            # Initialize signature service
            self.signature_service = ElectronicSignatureService()
            
            logger.info("Electronic signature service initialized")
        except Exception as e:
            logger.error(f"Error initializing signature service: {e}")
            self.signature_service = None
    
    def _initialize_transaction_monitoring(self):
        """Initialize transaction monitoring and milestone tracking"""
        try:
            # Set up transaction monitoring
            self.transaction_monitor = TransactionMonitor()
            
            logger.info("Transaction monitoring system initialized")
        except Exception as e:
            logger.error(f"Error initializing transaction monitoring: {e}")
            self.transaction_monitor = None
    
    def _load_default_templates(self):
        """Load default contract templates"""
        default_templates = [
            ContractTemplate(
                name="Standard Purchase Agreement",
                contract_type=ContractType.PURCHASE_AGREEMENT,
                template_content="PURCHASE AGREEMENT\n\nBuyer: {{buyer_name}}\nSeller: {{seller_name}}\nProperty: {{property_address}}\nPrice: ${{purchase_price}}\nClosing Date: {{closing_date}}",
                variables=["buyer_name", "seller_name", "property_address", "purchase_price", "closing_date"],
                jurisdiction="US"
            ),
            ContractTemplate(
                name="Assignment Contract",
                contract_type=ContractType.ASSIGNMENT_CONTRACT,
                template_content="ASSIGNMENT CONTRACT\n\nAssignor: {{assignor}}\nAssignee: {{assignee}}\nProperty: {{property_address}}\nAssignment Fee: ${{assignment_fee}}",
                variables=["assignor", "assignee", "property_address", "assignment_fee"],
                jurisdiction="US"
            )
        ]
        
        for template in default_templates:
            self.contract_templates[template.id] = template
        
        logger.info(f"Loaded {len(default_templates)} default contract templates")
    
    async def process_state(self, state: AgentState) -> AgentState:
        """Process the current state and perform contract-related tasks"""
        try:
            logger.info("Contract Agent processing state...")
            
            # Check for deals ready for contract generation
            approved_deals = StateManager.get_deals_by_status(state, DealStatus.APPROVED)
            
            # Process contract generation for approved deals
            for deal_dict in approved_deals:
                if not deal_dict.get("contract_generated", False):
                    await self._generate_contract_for_deal(deal_dict, state)
            
            # Add status message
            state = StateManager.add_agent_message(
                state,
                AgentType.CONTRACT,
                f"Processed {len(approved_deals)} approved deals",
                data={
                    "contracts_generated": self.contracts_generated,
                    "active_signatures": len(self.signature_requests),
                    "active_transactions": len(self.active_transactions)
                }
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Error in Contract Agent state processing: {e}")
            return StateManager.add_agent_message(
                state,
                AgentType.CONTRACT,
                f"Contract processing error: {str(e)}",
                priority=4
            )
    
    async def execute_task(self, task: str, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute a specific contract-related task"""
        try:
            logger.info(f"Contract Agent executing task: {task}")
            
            if task == "generate_contract":
                return await self._execute_generate_contract(data, state)
            elif task == "send_for_signature":
                return await self._execute_send_for_signature(data, state)
            elif task == "manage_template":
                return await self.manage_template(data.get("action", "list"), data)
            elif task == "track_transaction":
                return await self._execute_track_transaction(data, state)
            else:
                return {
                    "success": False,
                    "error": f"Unknown task: {task}",
                    "available_tasks": self.get_available_tasks()
                }
                
        except Exception as e:
            logger.error(f"Error executing Contract Agent task '{task}': {e}")
            return {
                "success": False,
                "error": f"Task execution failed: {str(e)}"
            }
    
    def get_available_tasks(self) -> List[str]:
        """Get list of tasks this agent can perform"""
        return [
            "generate_contract",
            "send_for_signature",
            "manage_template",
            "track_transaction"
        ]
    
    async def _generate_contract_for_deal(self, deal_dict: Dict[str, Any], state: AgentState):
        """Generate a contract for a specific deal"""
        try:
            deal_id = deal_dict.get("id")
            logger.info(f"Generating contract for deal: {deal_id}")
            
            # Determine contract type based on deal strategy
            strategy = deal_dict.get("analysis_data", {}).get("recommended_strategy", "purchase")
            contract_type = self._determine_contract_type(strategy)
            
            # Create contract document
            contract_doc = ContractDocument(
                deal_id=deal_id,
                contract_type=contract_type,
                template_id="default",
                status=ContractStatus.GENERATED,
                content=f"Contract for {deal_dict.get('property_address', 'Unknown Property')}",
                parties=self._extract_parties(deal_dict),
                terms=self._extract_terms(deal_dict)
            )
            
            self.active_contracts[contract_doc.id] = contract_doc
            self.contracts_generated += 1
            
            # Update deal status
            deal_dict["contract_generated"] = True
            deal_dict["contract_id"] = contract_doc.id
            deal_dict["status"] = DealStatus.UNDER_CONTRACT.value
            
            logger.info(f"Successfully generated contract {contract_doc.id} for deal {deal_id}")
            
        except Exception as e:
            logger.error(f"Error generating contract for deal {deal_dict.get('id')}: {e}")
    
    def _determine_contract_type(self, strategy: str) -> ContractType:
        """Determine contract type based on investment strategy"""
        strategy_mapping = {
            "flip": ContractType.PURCHASE_AGREEMENT,
            "wholesale": ContractType.ASSIGNMENT_CONTRACT,
            "rental": ContractType.PURCHASE_AGREEMENT,
            "brrrr": ContractType.PURCHASE_AGREEMENT,
            "option": ContractType.OPTION_CONTRACT,
            "lease_option": ContractType.LEASE_OPTION
        }
        
        return strategy_mapping.get(strategy.lower(), ContractType.PURCHASE_AGREEMENT)
    
    def _extract_parties(self, deal_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract parties information from deal data"""
        parties = []
        
        # Add buyer (investor)
        parties.append({
            "role": "buyer",
            "name": "Real Estate Empire LLC",
            "type": "entity"
        })
        
        # Add seller from owner info
        owner_info = deal_dict.get("owner_info", {})
        if owner_info:
            parties.append({
                "role": "seller",
                "name": owner_info.get("name", "Property Owner"),
                "type": "individual"
            })
        
        return parties
    
    def _extract_terms(self, deal_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Extract contract terms from deal data"""
        analysis_data = deal_dict.get("analysis_data", {})
        
        terms = {
            "purchase_price": deal_dict.get("listing_price") or analysis_data.get("offer_price", 0),
            "earnest_money": analysis_data.get("earnest_money", 1000),
            "closing_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "inspection_period": 10,
            "financing_contingency": True,
            "inspection_contingency": True
        }
        
        return terms
    
    async def _execute_generate_contract(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute contract generation task"""
        try:
            contract_type = ContractType(data.get("contract_type", ContractType.PURCHASE_AGREEMENT))
            
            # Create contract document
            contract_doc = ContractDocument(
                deal_id=data.get("deal_id", ""),
                contract_type=contract_type,
                template_id="default",
                status=ContractStatus.GENERATED,
                content=f"Generated contract for {data.get('property_address', 'Unknown Property')}",
                parties=data.get("parties", []),
                terms=data.get("terms", {})
            )
            
            self.active_contracts[contract_doc.id] = contract_doc
            self.contracts_generated += 1
            
            return {
                "success": True,
                "contract_id": contract_doc.id,
                "status": contract_doc.status.value,
                "content": contract_doc.content
            }
            
        except Exception as e:
            return {"success": False, "error": f"Contract generation failed: {str(e)}"}
    
    async def _execute_send_for_signature(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute send for signature task"""
        try:
            if not self.signature_service:
                return {"success": False, "error": "Electronic signature service not available"}
            
            result = await self.signature_service.send_for_signature(
                data.get("document_path", ""),
                data.get("signers", []),
                data.get("subject", "Contract for Signature"),
                data.get("message", "")
            )
            
            if result.get("success"):
                request_id = result.get("signature_request_id")
                
                # Store signature request
                self.signature_requests[request_id] = {
                    "contract_id": data.get("contract_id"),
                    "status": "sent",
                    "created_at": datetime.now(),
                    "signers": data.get("signers", [])
                }
            
            return result
            
        except Exception as e:
            return {"success": False, "error": f"Signature request failed: {str(e)}"}
    
    async def _execute_track_transaction(self, data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute transaction tracking task"""
        try:
            if not self.transaction_monitor:
                return {"success": False, "error": "Transaction monitor not available"}
            
            transaction_id = data.get("transaction_id")
            action = data.get("action", "get_status")
            
            if action == "create":
                transaction_id = self.transaction_monitor.create_transaction(
                    data.get("contract_id", ""),
                    data.get("deal_id", ""),
                    data.get("milestones", [])
                )
                
                if transaction_id:
                    self.transactions_managed += 1
                    return {
                        "success": True,
                        "transaction_id": transaction_id,
                        "status": "created"
                    }
                else:
                    return {"success": False, "error": "Failed to create transaction"}
            
            elif action == "update_milestone":
                success = self.transaction_monitor.update_milestone(
                    transaction_id,
                    data.get("milestone_name", ""),
                    data.get("milestone_status", "")
                )
                
                return {
                    "success": success,
                    "message": "Milestone updated" if success else "Failed to update milestone"
                }
            
            else:
                return {"success": False, "error": f"Unknown transaction action: {action}"}
            
        except Exception as e:
            return {"success": False, "error": f"Transaction tracking failed: {str(e)}"}
    
    async def manage_template(self, action: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage contract templates"""
        try:
            if action == "create":
                return await self._create_template(template_data)
            elif action == "update":
                return await self._update_template(template_data)
            elif action == "delete":
                return await self._delete_template(template_data.get("template_id"))
            elif action == "list":
                return await self._list_templates()
            elif action == "get":
                return await self._get_template(template_data.get("template_id"))
            else:
                return {
                    "success": False,
                    "error": f"Unknown template action: {action}"
                }
        except Exception as e:
            logger.error(f"Error managing template: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _create_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new contract template"""
        try:
            template = ContractTemplate(
                name=template_data.get("name"),
                contract_type=ContractType(template_data.get("contract_type")),
                template_content=template_data.get("content"),
                variables=template_data.get("variables", []),
                jurisdiction=template_data.get("jurisdiction", "US")
            )
            
            self.contract_templates[template.id] = template
            self.templates_created += 1
            
            logger.info(f"Created new contract template: {template.name}")
            
            return {
                "success": True,
                "template_id": template.id,
                "message": f"Template '{template.name}' created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _update_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing contract template"""
        try:
            template_id = template_data.get("template_id")
            if template_id not in self.contract_templates:
                return {
                    "success": False,
                    "error": f"Template {template_id} not found"
                }
            
            template = self.contract_templates[template_id]
            
            # Update template fields
            if "name" in template_data:
                template.name = template_data["name"]
            if "content" in template_data:
                template.template_content = template_data["content"]
            if "variables" in template_data:
                template.variables = template_data["variables"]
            
            template.updated_at = datetime.now()
            
            logger.info(f"Updated contract template: {template.name}")
            
            return {
                "success": True,
                "template_id": template_id,
                "message": f"Template '{template.name}' updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error updating template: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _delete_template(self, template_id: str) -> Dict[str, Any]:
        """Delete a contract template"""
        try:
            if template_id not in self.contract_templates:
                return {
                    "success": False,
                    "error": f"Template {template_id} not found"
                }
            
            template_name = self.contract_templates[template_id].name
            del self.contract_templates[template_id]
            
            logger.info(f"Deleted contract template: {template_name}")
            
            return {
                "success": True,
                "message": f"Template '{template_name}' deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting template: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _list_templates(self) -> Dict[str, Any]:
        """List all contract templates"""
        try:
            templates = []
            for template_id, template in self.contract_templates.items():
                templates.append({
                    "id": template_id,
                    "name": template.name,
                    "contract_type": template.contract_type.value,
                    "jurisdiction": template.jurisdiction,
                    "created_at": template.created_at.isoformat(),
                    "updated_at": template.updated_at.isoformat(),
                    "is_active": template.is_active
                })
            
            return {
                "success": True,
                "templates": templates,
                "count": len(templates)
            }
            
        except Exception as e:
            logger.error(f"Error listing templates: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_template(self, template_id: str) -> Dict[str, Any]:
        """Get a specific contract template"""
        try:
            if template_id not in self.contract_templates:
                return {
                    "success": False,
                    "error": f"Template {template_id} not found"
                }
            
            template = self.contract_templates[template_id]
            
            return {
                "success": True,
                "template": {
                    "id": template_id,
                    "name": template.name,
                    "contract_type": template.contract_type.value,
                    "content": template.template_content,
                    "variables": template.variables,
                    "jurisdiction": template.jurisdiction,
                    "version": template.version,
                    "created_at": template.created_at.isoformat(),
                    "updated_at": template.updated_at.isoformat(),
                    "is_active": template.is_active
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting template: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_contract_workflow(self, workflow_type: str, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a contract workflow using LangGraph"""
        try:
            if not self.workflow_manager:
                return {
                    "success": False,
                    "error": "Workflow manager not initialized",
                    "completed": True
                }
            
            # Execute the workflow
            result = await self.workflow_manager.execute_workflow(workflow_type, initial_data)
            
            logger.info(f"Executed contract workflow {workflow_type} for deal: {initial_data.get('deal_id')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing contract workflow {workflow_type}: {e}")
            return {
                "success": False,
                "error": str(e),
                "completed": True,
                "current_step": "error"
            }
    
    async def generate_contract_with_workflow(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a contract using the LangGraph workflow"""
        return await self.execute_contract_workflow(
            "contract_generation",
            {
                "deal_id": deal_data.get("id", str(uuid.uuid4())),
                "contract_data": deal_data,
                "workflow_type": "contract_generation",
                "current_step": "validate_deal_data",
                "completed": False
            }
        )