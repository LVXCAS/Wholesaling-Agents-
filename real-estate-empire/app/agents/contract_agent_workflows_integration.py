"""
Contract Agent Workflows Integration
Adds workflow capabilities to the Contract Agent
"""

import logging
from typing import Dict, Any, List
import uuid

logger = logging.getLogger(__name__)


def add_workflow_methods_to_contract_agent():
    """Add workflow methods to the ContractAgent class"""
    from .contract_agent import ContractAgent
    from .contract_workflows import ContractWorkflows, ContractWorkflowType
    
    def _initialize_workflows(self):
        """Initialize contract workflows"""
        try:
            # Initialize the workflow manager
            self.workflows = ContractWorkflows(self)
            logger.info("Contract workflows initialized")
        except Exception as e:
            logger.error(f"Error initializing workflows: {e}")
            self.workflows = None
    
    async def execute_contract_workflow(self, workflow_type: str, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a contract workflow"""
        try:
            # Convert string to enum
            workflow_enum = ContractWorkflowType(workflow_type)
            
            # Execute the workflow
            result = await self.workflows.execute_workflow(workflow_enum, initial_data)
            
            logger.info(f"Executed workflow {workflow_type} for deal: {initial_data.get('deal_id')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_type}: {e}")
            return {
                "success": False,
                "error": str(e),
                "completed": True,
                "current_step": "error"
            }
    
    async def generate_contract_workflow(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the contract generation workflow"""
        return await self.execute_contract_workflow(
            "contract_generation",
            {
                "deal_id": deal_data.get("id", str(uuid.uuid4())),
                "contract_data": deal_data
            }
        )
    
    async def collect_signatures_workflow(self, contract_id: str, parties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute the signature collection workflow"""
        return await self.execute_contract_workflow(
            "signature_collection",
            {
                "contract_id": contract_id,
                "parties": parties
            }
        )
    
    async def store_documents_workflow(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute the document storage workflow"""
        return await self.execute_contract_workflow(
            "document_storage",
            {
                "documents": documents
            }
        )
    
    async def monitor_transaction_workflow(self, contract_id: str, deal_id: str) -> Dict[str, Any]:
        """Execute the transaction monitoring workflow"""
        return await self.execute_contract_workflow(
            "transaction_monitoring",
            {
                "contract_id": contract_id,
                "deal_id": deal_id
            }
        )
    
    async def coordinate_closing_workflow(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the closing coordination workflow"""
        return await self.execute_contract_workflow(
            "closing_coordination",
            transaction_data
        )
    
    # Add methods to the ContractAgent class
    ContractAgent._initialize_workflows = _initialize_workflows
    ContractAgent.execute_contract_workflow = execute_contract_workflow
    ContractAgent.generate_contract_workflow = generate_contract_workflow
    ContractAgent.collect_signatures_workflow = collect_signatures_workflow
    ContractAgent.store_documents_workflow = store_documents_workflow
    ContractAgent.monitor_transaction_workflow = monitor_transaction_workflow
    ContractAgent.coordinate_closing_workflow = coordinate_closing_workflow


# Apply the integration when this module is imported
add_workflow_methods_to_contract_agent()