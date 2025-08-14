"""
Tests for Contract Agent Tools
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import uuid

from app.agents.contract_tools import (
    ContractGenerationTool,
    ElectronicSignatureTool,
    DocumentManagementTool,
    LegalComplianceTool,
    TransactionTrackingTool,
    ContractType,
    DocumentFormat,
    SignatureProvider,
    get_contract_tools,
    get_tool_by_name
)


class TestContractGenerationTool:
    """Test contract generation functionality"""
    
    @pytest.fixture
    def contract_tool(self):
        return ContractGenerationTool()
    
    @pytest.fixture
    def sample_deal_data(self):
        return {
            "property": {
                "address": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "zip_code": "12345",
                "property_type": "Single Family",
                "square_feet": 2000,
                "lot_size": 0.25
            }
        }
    
    @pytest.fixture
    def sample_parties(self):
        return [
            {
                "role": "Buyer",
                "name": "John Doe",
                "address": "456 Oak Ave, Anytown, CA 12345",
                "phone": "(555) 123-4567",
                "email": "john@example.com"
            },
            {
                "role": "Seller",
                "name": "Jane Smith",
                "address": "789 Pine St, Anytown, CA 12345",
                "phone": "(555) 987-6543",
                "email": "jane@example.com"
            }
        ]
    
    @pytest.fixture
    def sample_terms(self):
        return {
            "purchase_price": 500000,
            "earnest_money": 10000,
            "down_payment": 100000,
            "financing_amount": 400000,
            "closing_date": "2024-02-15",
            "contingencies": [
                "Inspection contingency (10 days)",
                "Financing contingency (30 days)",
                "Appraisal contingency"
            ],
            "inclusions": [
                "All built-in appliances",
                "Window treatments",
                "Garage door opener"
            ]
        }
    
    @pytest.mark.asyncio
    async def test_generate_purchase_agreement(self, contract_tool, sample_deal_data, sample_parties, sample_terms):
        """Test generating a purchase agreement"""
        result = await contract_tool.execute(
            contract_type=ContractType.PURCHASE_AGREEMENT,
            deal_data=sample_deal_data,
            parties=sample_parties,
            terms=sample_terms,
            output_format=DocumentFormat.HTML
        )
        
        assert result["success"] is True
        assert "contract_id" in result
        assert "document_path" in result
        assert "content_preview" in result
        
        # Check full content in result object
        full_content = result["result"].document_content
        assert "123 Main St" in full_content
        assert "John Doe" in full_content
        assert "500000" in full_content
    
    @pytest.mark.asyncio
    async def test_generate_assignment_contract(self, contract_tool, sample_deal_data, sample_parties):
        """Test generating an assignment contract"""
        assignment_terms = {
            "original_contract_date": "2024-01-15",
            "original_purchase_price": 480000,
            "assignment_fee": 20000,
            "assignment_date": "2024-02-01",
            "closing_date": "2024-02-15"
        }
        
        result = await contract_tool.execute(
            contract_type=ContractType.ASSIGNMENT_CONTRACT,
            deal_data=sample_deal_data,
            parties=sample_parties,
            terms=assignment_terms
        )
        
        assert result["success"] is True
        assert "contract_id" in result
        
        # Check full content in result object
        full_content = result["result"].document_content
        assert "20000" in full_content
        assert "ASSIGNMENT OF REAL ESTATE CONTRACT" in full_content
    
    @pytest.mark.asyncio
    async def test_missing_contract_type(self, contract_tool):
        """Test error handling for missing contract type"""
        result = await contract_tool.execute(
            deal_data={},
            parties=[],
            terms={}
        )
        
        assert result["success"] is False
        assert "Contract type is required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_invalid_template(self, contract_tool):
        """Test error handling for invalid template"""
        result = await contract_tool.execute(
            contract_type="invalid_contract_type",
            deal_data={},
            parties=[],
            terms={}
        )
        
        assert result["success"] is False
        assert "Template not found" in result["error"]


class TestElectronicSignatureTool:
    """Test electronic signature functionality"""
    
    @pytest.fixture
    def signature_tool(self):
        return ElectronicSignatureTool()
    
    @pytest.fixture
    def sample_signers(self):
        return [
            {
                "name": "John Doe",
                "email": "john@example.com",
                "role": "Buyer"
            },
            {
                "name": "Jane Smith",
                "email": "jane@example.com",
                "role": "Seller"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_send_for_signature(self, signature_tool, sample_signers):
        """Test sending document for signature"""
        result = await signature_tool.execute(
            action="send_for_signature",
            document_path="contracts/CONTRACT_20241225_12345.html",
            signers=sample_signers,
            subject="Purchase Agreement for Signature",
            message="Please review and sign this purchase agreement."
        )
        
        assert result["success"] is True
        assert "signature_request_id" in result
        assert "signing_urls" in result
        assert len(result["signing_urls"]) == 2
        assert result["status"] == "sent"
    
    @pytest.mark.asyncio
    async def test_check_signature_status(self, signature_tool):
        """Test checking signature status"""
        result = await signature_tool.execute(
            action="check_status",
            signature_request_id="SIG_20241225_12345"
        )
        
        assert result["success"] is True
        assert "status" in result
        assert "last_updated" in result
    
    @pytest.mark.asyncio
    async def test_download_signed_document(self, signature_tool):
        """Test downloading signed document"""
        result = await signature_tool.execute(
            action="download_signed",
            signature_request_id="SIG_20241225_12345"
        )
        
        assert result["success"] is True
        assert "download_url" in result
        assert "document_path" in result
    
    @pytest.mark.asyncio
    async def test_missing_document_path(self, signature_tool):
        """Test error handling for missing document path"""
        result = await signature_tool.execute(
            action="send_for_signature",
            signers=[]
        )
        
        assert result["success"] is False
        assert "Document path and signers are required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_invalid_action(self, signature_tool):
        """Test error handling for invalid action"""
        result = await signature_tool.execute(
            action="invalid_action"
        )
        
        assert result["success"] is False
        assert "Unknown action" in result["error"]


class TestDocumentManagementTool:
    """Test document management functionality"""
    
    @pytest.fixture
    def doc_tool(self):
        return DocumentManagementTool()
    
    @pytest.mark.asyncio
    async def test_store_document(self, doc_tool):
        """Test storing a document"""
        result = await doc_tool.execute(
            action="store",
            document_content="<html><body>Test contract content</body></html>",
            metadata={
                "contract_type": "purchase_agreement",
                "deal_id": "DEAL_12345",
                "parties": ["John Doe", "Jane Smith"]
            }
        )
        
        assert result["success"] is True
        assert "document_id" in result
        assert "stored_path" in result
        assert "metadata" in result
        assert result["metadata"]["contract_type"] == "purchase_agreement"
    
    @pytest.mark.asyncio
    async def test_retrieve_document(self, doc_tool):
        """Test retrieving a document"""
        result = await doc_tool.execute(
            action="retrieve",
            document_id="DOC_20241225_12345"
        )
        
        assert result["success"] is True
        assert "document_path" in result
        assert "download_url" in result
        assert "retrieved_at" in result
    
    @pytest.mark.asyncio
    async def test_list_documents(self, doc_tool):
        """Test listing documents"""
        result = await doc_tool.execute(
            action="list",
            deal_id="DEAL_12345",
            limit=10
        )
        
        assert result["success"] is True
        assert "documents" in result
        assert "total_count" in result
        assert isinstance(result["documents"], list)
    
    @pytest.mark.asyncio
    async def test_search_documents(self, doc_tool):
        """Test searching documents"""
        result = await doc_tool.execute(
            action="search",
            query="purchase agreement",
            filters={"document_type": "purchase_agreement"}
        )
        
        assert result["success"] is True
        assert "results" in result
        assert "total_matches" in result
        assert result["query"] == "purchase agreement"
    
    @pytest.mark.asyncio
    async def test_missing_document_content(self, doc_tool):
        """Test error handling for missing document content"""
        result = await doc_tool.execute(
            action="store"
        )
        
        assert result["success"] is False
        assert "Either document_path or document_content is required" in result["error"]


class TestLegalComplianceTool:
    """Test legal compliance checking functionality"""
    
    @pytest.fixture
    def compliance_tool(self):
        return LegalComplianceTool()
    
    @pytest.fixture
    def sample_contract_content(self):
        return """
        <html><body>
        <h1>REAL ESTATE PURCHASE AGREEMENT</h1>
        <p>Purchase Price: $500,000</p>
        <p>Earnest Money: $10,000</p>
        <p>Inspection Contingency: 10 days</p>
        <p>Financing Contingency: 30 days</p>
        <div class="signature-section">
            <p>Buyer Signature: ________________</p>
            <p>Seller Signature: ________________</p>
        </div>
        </body></html>
        """
    
    @pytest.mark.asyncio
    async def test_compliance_check_purchase_agreement(self, compliance_tool, sample_contract_content):
        """Test compliance check for purchase agreement"""
        result = await compliance_tool.execute(
            document_content=sample_contract_content,
            contract_type=ContractType.PURCHASE_AGREEMENT,
            jurisdiction="CA"
        )
        
        assert result["success"] is True
        assert "compliant" in result
        assert "issues_count" in result
        assert "warnings_count" in result
        assert "summary" in result
        assert result["result"].jurisdiction == "CA"
    
    @pytest.mark.asyncio
    async def test_compliance_check_missing_earnest_money(self, compliance_tool):
        """Test compliance check for contract missing earnest money"""
        contract_without_earnest = """
        <html><body>
        <h1>REAL ESTATE PURCHASE AGREEMENT</h1>
        <p>Purchase Price: $500,000</p>
        <p>Inspection Contingency: 10 days</p>
        <div class="signature-section">
            <p>Buyer Signature: ________________</p>
            <p>Seller Signature: ________________</p>
        </div>
        </body></html>
        """
        
        result = await compliance_tool.execute(
            document_content=contract_without_earnest,
            contract_type=ContractType.PURCHASE_AGREEMENT
        )
        
        assert result["success"] is True
        assert result["compliant"] is False
        assert result["issues_count"] > 0
        assert any("earnest money" in issue.lower() for issue in result["result"].issues)
    
    @pytest.mark.asyncio
    async def test_compliance_check_missing_signature(self, compliance_tool):
        """Test compliance check for contract missing signature section"""
        contract_without_signature = """
        <html><body>
        <h1>REAL ESTATE PURCHASE AGREEMENT</h1>
        <p>Purchase Price: $500,000</p>
        <p>Earnest Money: $10,000</p>
        </body></html>
        """
        
        result = await compliance_tool.execute(
            document_content=contract_without_signature,
            contract_type=ContractType.PURCHASE_AGREEMENT
        )
        
        assert result["success"] is True
        assert result["compliant"] is False
        assert any("signature" in issue.lower() for issue in result["result"].issues)
    
    @pytest.mark.asyncio
    async def test_missing_document_content(self, compliance_tool):
        """Test error handling for missing document content"""
        result = await compliance_tool.execute(
            contract_type=ContractType.PURCHASE_AGREEMENT
        )
        
        assert result["success"] is False
        assert "Either document_content or document_path is required" in result["error"]


class TestTransactionTrackingTool:
    """Test transaction tracking functionality"""
    
    @pytest.fixture
    def tracking_tool(self):
        return TransactionTrackingTool()
    
    @pytest.mark.asyncio
    async def test_get_transaction_status(self, tracking_tool):
        """Test getting transaction status"""
        result = await tracking_tool.execute(
            action="get_status",
            transaction_id="TXN_20241225_12345"
        )
        
        assert result["success"] is True
        assert "current_status" in result
        assert "progress_percentage" in result
        assert result["result"].transaction_id == "TXN_20241225_12345"
        assert len(result["result"].milestones) > 0
        assert len(result["result"].pending_items) >= 0
        assert len(result["result"].completed_items) >= 0
    
    @pytest.mark.asyncio
    async def test_update_milestone(self, tracking_tool):
        """Test updating a transaction milestone"""
        result = await tracking_tool.execute(
            action="update_milestone",
            transaction_id="TXN_20241225_12345",
            milestone="Inspection Period",
            status="completed",
            notes="Inspection completed successfully"
        )
        
        assert result["success"] is True
        assert result["transaction_id"] == "TXN_20241225_12345"
        assert result["milestone"] == "Inspection Period"
        assert result["new_status"] == "completed"
        assert result["notes"] == "Inspection completed successfully"
    
    @pytest.mark.asyncio
    async def test_get_timeline(self, tracking_tool):
        """Test getting transaction timeline"""
        result = await tracking_tool.execute(
            action="get_timeline",
            transaction_id="TXN_20241225_12345"
        )
        
        assert result["success"] is True
        assert "timeline" in result
        assert "contract_date" in result
        assert "estimated_closing" in result
        assert isinstance(result["timeline"], list)
        assert len(result["timeline"]) > 0
    
    @pytest.mark.asyncio
    async def test_missing_transaction_id(self, tracking_tool):
        """Test error handling for missing transaction ID"""
        result = await tracking_tool.execute(
            action="get_status"
        )
        
        assert result["success"] is False
        assert "Transaction ID is required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_missing_milestone_data(self, tracking_tool):
        """Test error handling for missing milestone data"""
        result = await tracking_tool.execute(
            action="update_milestone",
            transaction_id="TXN_12345"
        )
        
        assert result["success"] is False
        assert "Transaction ID, milestone, and status are required" in result["error"]


class TestContractToolsRegistry:
    """Test contract tools registry functionality"""
    
    def test_get_contract_tools(self):
        """Test getting all contract tools"""
        tools = get_contract_tools()
        
        assert isinstance(tools, dict)
        assert "contract_generation" in tools
        assert "electronic_signature" in tools
        assert "document_management" in tools
        assert "legal_compliance" in tools
        assert "transaction_tracking" in tools
    
    def test_get_tool_by_name(self):
        """Test getting specific tool by name"""
        tool = get_tool_by_name("contract_generation")
        assert tool is not None
        assert isinstance(tool, ContractGenerationTool)
        
        tool = get_tool_by_name("nonexistent_tool")
        assert tool is None
    
    def test_tool_metadata(self):
        """Test tool metadata is properly set"""
        tools = get_contract_tools()
        
        for tool_name, tool in tools.items():
            assert hasattr(tool, 'metadata')
            assert tool.metadata.name == tool_name
            assert tool.metadata.category is not None
            assert tool.metadata.access_level is not None


if __name__ == "__main__":
    pytest.main([__file__])