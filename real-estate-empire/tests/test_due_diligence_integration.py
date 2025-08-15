"""
Integration tests for due diligence management service.
Tests checklist automation, document tracking, risk assessment, and compliance checking.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.due_diligence_service import DueDiligenceService
from app.models.transaction import (
    DocumentStatus, ComplianceStatus, TaskPriority
)


class TestDueDiligenceIntegration:
    """Integration test cases for DueDiligenceService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = DueDiligenceService()
        self.transaction_id = uuid4()
    
    def test_create_purchase_checklist(self):
        """Test creating a due diligence checklist for purchase transaction."""
        property_details = {
            "year_built": 1975,
            "has_hoa": True,
            "property_type": "residential",
            "intended_use": "primary_residence"
        }
        
        checklist = self.service.create_checklist(
            transaction_id=self.transaction_id,
            transaction_type="purchase",
            property_details=property_details
        )
        
        assert checklist.transaction_id == self.transaction_id
        assert checklist.name == "Due Diligence - Purchase"
        assert len(checklist.items) > 0
        assert checklist.total_items == len(checklist.items)
        
        # Check that HOA documents are included
        hoa_items = [item for item in checklist.items if "HOA" in item.name]
        assert len(hoa_items) > 0
        
        # Check that lead paint disclosure is included (pre-1978 property)
        lead_paint_items = [item for item in checklist.items if "Lead" in item.name]
        assert len(lead_paint_items) > 0
        
        # Verify checklist is stored
        retrieved = self.service.get_checklist(checklist.id)
        assert retrieved is not None
        assert retrieved.id == checklist.id
    
    def test_create_wholesale_checklist(self):
        """Test creating a due diligence checklist for wholesale transaction."""
        checklist = self.service.create_checklist(
            transaction_id=self.transaction_id,
            transaction_type="wholesale"
        )
        
        assert checklist.transaction_id == self.transaction_id
        assert checklist.name == "Due Diligence - Wholesale"
        assert len(checklist.items) > 0
        
        # Wholesale should have fewer items than purchase
        purchase_checklist = self.service.create_checklist(
            transaction_id=uuid4(),
            transaction_type="purchase"
        )
        assert len(checklist.items) < len(purchase_checklist.items)
        
        # Check for key wholesale items
        condition_items = [item for item in checklist.items if "Condition" in item.name]
        assert len(condition_items) > 0
        
        market_items = [item for item in checklist.items if "Market" in item.name]
        assert len(market_items) > 0
    
    def test_document_workflow(self):
        """Test complete document workflow from request to approval."""
        checklist = self.service.create_checklist(
            transaction_id=self.transaction_id,
            transaction_type="purchase"
        )
        
        # Get first item
        item = checklist.items[0]
        assert item.status == DocumentStatus.REQUIRED
        
        # Request documents
        success = self.service.request_documents(
            checklist.id, 
            item.id, 
            "seller@example.com",
            "Please provide the required documents"
        )
        assert success is True
        
        # Check status updated
        updated_checklist = self.service.get_checklist(checklist.id)
        updated_item = next(i for i in updated_checklist.items if i.id == item.id)
        assert updated_item.status == DocumentStatus.REQUESTED
        assert len(updated_item.review_notes) > 0
        
        # Add document
        document_info = {
            "name": "inspection_report.pdf",
            "type": "pdf",
            "url": "https://example.com/doc.pdf",
            "uploaded_by": "seller@example.com",
            "size": 1024000
        }
        
        success = self.service.add_document(checklist.id, item.id, document_info)
        assert success is True
        
        # Check document added and status updated
        final_checklist = self.service.get_checklist(checklist.id)
        final_item = next(i for i in final_checklist.items if i.id == item.id)
        assert final_item.status == DocumentStatus.RECEIVED
        assert len(final_item.received_documents) == 1
        assert final_item.received_documents[0]["name"] == "inspection_report.pdf"
        
        # Review and approve
        success = self.service.review_item(
            checklist.id,
            item.id,
            "reviewer@example.com",
            "approved",
            "Document looks good, approved"
        )
        assert success is True
        
        # Check final status
        approved_checklist = self.service.get_checklist(checklist.id)
        approved_item = next(i for i in approved_checklist.items if i.id == item.id)
        assert approved_item.status == DocumentStatus.APPROVED
        assert approved_item.approved_by == "reviewer@example.com"
        assert approved_item.approved_at is not None
        assert approved_item.completion_percentage == 100
        
        # Check checklist progress updated
        assert approved_checklist.completed_items > 0
        assert approved_checklist.completion_percentage > 0
    
    def test_compliance_checking(self):
        """Test automated compliance checking."""
        property_details = {
            "year_built": 1975,  # Pre-1978, requires lead paint disclosure
            "property_type": "residential"
        }
        
        checklist = self.service.create_checklist(
            transaction_id=self.transaction_id,
            transaction_type="purchase",
            property_details=property_details
        )
        
        # Should have compliance items
        compliance_items = [item for item in checklist.items if item.category == "compliance"]
        assert len(compliance_items) > 0
        
        # Initial compliance check
        compliance_result = self.service.auto_check_compliance(checklist.id)
        # Should be pending or requires_review since compliance items are not completed
        assert compliance_result["compliance_status"] in [
            ComplianceStatus.PENDING.value, 
            ComplianceStatus.REQUIRES_REVIEW.value
        ]
        assert len(compliance_result["warnings"]) > 0
        
        # Approve a compliance item
        lead_paint_item = next(
            (item for item in compliance_items if "Lead" in item.name),
            None
        )
        if lead_paint_item:
            self.service.review_item(
                checklist.id,
                lead_paint_item.id,
                "compliance_officer@example.com",
                "approved",
                "Lead paint disclosure completed"
            )
        
        # Check compliance again
        updated_compliance = self.service.auto_check_compliance(checklist.id)
        # Should still be pending/requires_review if other compliance items exist, or compliant if all done
        assert updated_compliance["compliance_status"] in [
            ComplianceStatus.PENDING.value,
            ComplianceStatus.REQUIRES_REVIEW.value,
            ComplianceStatus.COMPLIANT.value
        ]
    
    def test_risk_assessment(self):
        """Test risk assessment and reporting."""
        checklist = self.service.create_checklist(
            transaction_id=self.transaction_id,
            transaction_type="purchase"
        )
        
        # Generate initial risk report
        risk_report = self.service.generate_risk_report(checklist.id)
        assert risk_report is not None
        assert "overall_risk_level" in risk_report
        assert "risk_score" in risk_report
        assert "risk_categories" in risk_report
        
        # Should have risks since nothing is completed
        assert risk_report["risk_score"] > 0
        assert risk_report["overall_risk_level"] in ["low", "medium", "high", "critical"]
        
        # Complete a critical item
        critical_items = [item for item in checklist.items if item.risk_level == "critical"]
        if critical_items:
            critical_item = critical_items[0]
            self.service.review_item(
                checklist.id,
                critical_item.id,
                "reviewer@example.com",
                "approved",
                "Critical item completed"
            )
            
            # Risk should be reduced
            updated_risk_report = self.service.generate_risk_report(checklist.id)
            assert updated_risk_report["risk_score"] < risk_report["risk_score"]
    
    def test_overdue_item_detection(self):
        """Test detection of overdue due diligence items."""
        checklist = self.service.create_checklist(
            transaction_id=self.transaction_id,
            transaction_type="wholesale"  # Use wholesale for simpler checklist
        )
        
        # Set all items to future dates first to avoid interference
        for item in checklist.items:
            item.due_date = datetime.now() + timedelta(days=7)
        
        # Set one specific item due date in the past
        test_item = checklist.items[0]
        test_item.due_date = datetime.now() - timedelta(days=3)
        test_item.status = DocumentStatus.REQUESTED
        
        # Get overdue items
        overdue_items = self.service.get_overdue_items(checklist.id)
        
        # Find our specific overdue item
        our_overdue_item = next(
            (item for item in overdue_items if item["item_id"] == test_item.id),
            None
        )
        
        assert our_overdue_item is not None
        assert our_overdue_item["days_overdue"] == 3
        assert our_overdue_item["checklist_id"] == checklist.id
    
    def test_category_filtering(self):
        """Test filtering items by category."""
        checklist = self.service.create_checklist(
            transaction_id=self.transaction_id,
            transaction_type="purchase"
        )
        
        # Test different categories
        categories = ["physical", "legal", "financial", "compliance"]
        
        for category in categories:
            items = self.service.get_items_by_category(checklist.id, category)
            # Should have items in each category
            if items:  # Some categories might be empty for certain transaction types
                assert all(item.category == category for item in items)
    
    def test_status_filtering(self):
        """Test filtering items by status."""
        checklist = self.service.create_checklist(
            transaction_id=self.transaction_id,
            transaction_type="purchase"
        )
        
        # Initially all should be required
        required_items = self.service.get_items_by_status(checklist.id, DocumentStatus.REQUIRED)
        assert len(required_items) == len(checklist.items)
        
        # Change status of one item
        item = checklist.items[0]
        self.service.update_item_status(
            checklist.id,
            item.id,
            DocumentStatus.REQUESTED,
            "Status updated for testing"
        )
        
        # Check filtering
        requested_items = self.service.get_items_by_status(checklist.id, DocumentStatus.REQUESTED)
        assert len(requested_items) == 1
        assert requested_items[0].id == item.id
        
        required_items = self.service.get_items_by_status(checklist.id, DocumentStatus.REQUIRED)
        assert len(required_items) == len(checklist.items) - 1
    
    def test_checklist_progress_calculation(self):
        """Test checklist progress calculation."""
        checklist = self.service.create_checklist(
            transaction_id=self.transaction_id,
            transaction_type="wholesale"  # Smaller checklist for easier testing
        )
        
        # Initially 0% complete
        assert checklist.completion_percentage == 0
        assert checklist.completed_items == 0
        
        # Complete half the items
        items_to_complete = checklist.items[:len(checklist.items)//2]
        
        for item in items_to_complete:
            self.service.review_item(
                checklist.id,
                item.id,
                "reviewer@example.com",
                "approved",
                "Item completed"
            )
        
        # Check progress
        updated_checklist = self.service.get_checklist(checklist.id)
        expected_percentage = int((len(items_to_complete) / len(checklist.items)) * 100)
        assert updated_checklist.completion_percentage == expected_percentage
        assert updated_checklist.completed_items == len(items_to_complete)
        
        # Complete all items
        remaining_items = checklist.items[len(checklist.items)//2:]
        for item in remaining_items:
            self.service.review_item(
                checklist.id,
                item.id,
                "reviewer@example.com",
                "approved",
                "Item completed"
            )
        
        # Should be 100% complete
        final_checklist = self.service.get_checklist(checklist.id)
        assert final_checklist.completion_percentage == 100
        assert final_checklist.completed_items == len(checklist.items)
        assert final_checklist.completed_at is not None
    
    def test_export_functionality(self):
        """Test checklist export functionality."""
        checklist = self.service.create_checklist(
            transaction_id=self.transaction_id,
            transaction_type="purchase"
        )
        
        # Complete some items to make export more interesting
        item = checklist.items[0]
        self.service.review_item(
            checklist.id,
            item.id,
            "reviewer@example.com",
            "approved",
            "Item completed for export test"
        )
        
        # Export checklist
        export_data = self.service.export_checklist(checklist.id, "json")
        assert export_data is not None
        assert "checklist" in export_data
        assert "risk_report" in export_data
        assert "compliance_check" in export_data
        assert "exported_at" in export_data
        
        # Verify export contains expected data
        assert export_data["checklist"]["id"] == str(checklist.id)
        assert export_data["checklist"]["transaction_id"] == str(self.transaction_id)
        assert len(export_data["checklist"]["items"]) == len(checklist.items)
    
    def test_multiple_checklists_management(self):
        """Test managing multiple checklists."""
        # Create multiple checklists
        transaction_id_1 = uuid4()
        transaction_id_2 = uuid4()
        
        checklist_1 = self.service.create_checklist(
            transaction_id=transaction_id_1,
            transaction_type="purchase"
        )
        
        checklist_2 = self.service.create_checklist(
            transaction_id=transaction_id_2,
            transaction_type="wholesale"
        )
        
        # Test listing all checklists
        all_checklists = self.service.list_checklists()
        assert len(all_checklists) >= 2
        
        # Test filtering by transaction
        transaction_1_checklists = self.service.list_checklists(transaction_id=transaction_id_1)
        assert len(transaction_1_checklists) == 1
        assert transaction_1_checklists[0].id == checklist_1.id
        
        # Test getting checklist by transaction
        retrieved_checklist = self.service.get_checklist_by_transaction(transaction_id_2)
        assert retrieved_checklist is not None
        assert retrieved_checklist.id == checklist_2.id
    
    def test_property_specific_requirements(self):
        """Test that property-specific requirements are properly applied."""
        # Property with HOA
        property_with_hoa = {
            "has_hoa": True,
            "property_type": "residential"
        }
        
        checklist_with_hoa = self.service.create_checklist(
            transaction_id=uuid4(),
            transaction_type="purchase",
            property_details=property_with_hoa
        )
        
        hoa_items = [item for item in checklist_with_hoa.items if "HOA" in item.name]
        assert len(hoa_items) > 0
        
        # Property without HOA
        property_without_hoa = {
            "has_hoa": False,
            "property_type": "residential"
        }
        
        checklist_without_hoa = self.service.create_checklist(
            transaction_id=uuid4(),
            transaction_type="purchase",
            property_details=property_without_hoa
        )
        
        hoa_items_no_hoa = [item for item in checklist_without_hoa.items if "HOA" in item.name]
        assert len(hoa_items_no_hoa) == 0
        
        # Commercial property
        commercial_property = {
            "property_type": "commercial"
        }
        
        commercial_checklist = self.service.create_checklist(
            transaction_id=uuid4(),
            transaction_type="purchase",
            property_details=commercial_property
        )
        
        # Should have environmental assessment for commercial
        env_items = [item for item in commercial_checklist.items if "Environmental" in item.name]
        assert len(env_items) > 0
    
    def test_compliance_rule_application(self):
        """Test that compliance rules are properly applied based on property characteristics."""
        # Pre-1978 property (requires lead paint disclosure)
        old_property = {
            "year_built": 1975,
            "property_type": "residential"
        }
        
        old_checklist = self.service.create_checklist(
            transaction_id=uuid4(),
            transaction_type="purchase",
            property_details=old_property
        )
        
        lead_items = [item for item in old_checklist.items if "Lead" in item.name]
        assert len(lead_items) > 0
        
        # Post-1978 property (no lead paint disclosure required)
        new_property = {
            "year_built": 1985,
            "property_type": "residential"
        }
        
        new_checklist = self.service.create_checklist(
            transaction_id=uuid4(),
            transaction_type="purchase",
            property_details=new_property
        )
        
        lead_items_new = [item for item in new_checklist.items if "Lead" in item.name]
        assert len(lead_items_new) == 0
        
        # Property with septic system
        septic_property = {
            "has_septic": True,
            "property_type": "residential"
        }
        
        septic_checklist = self.service.create_checklist(
            transaction_id=uuid4(),
            transaction_type="purchase",
            property_details=septic_property
        )
        
        septic_items = [item for item in septic_checklist.items if "Septic" in item.name]
        assert len(septic_items) > 0