"""
Integration tests for Property Management Service.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services.property_management_service import (
    PropertyManagementService,
    MaintenanceRequest,
    ExpenseRecord,
    TenantRecord,
    PropertyInspection,
    MaintenanceStatusEnum,
    MaintenancePriorityEnum,
    ExpenseCategoryEnum,
    TenantStatusEnum,
    InspectionTypeEnum
)
from app.models.property import PropertyDB


class TestPropertyManagementIntegration:
    """Integration test cases for PropertyManagementService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def property_management_service(self, mock_db):
        """Create a PropertyManagementService instance with mocked dependencies."""
        return PropertyManagementService(mock_db)
    
    @pytest.fixture
    def sample_property_id(self):
        """Sample property ID for testing."""
        return uuid.uuid4()
    
    @pytest.fixture
    def mock_property(self, sample_property_id):
        """Mock property object."""
        property_obj = Mock(spec=PropertyDB)
        property_obj.id = sample_property_id
        property_obj.address = "123 Test St"
        return property_obj
    
    def test_create_maintenance_request_success(self, property_management_service, sample_property_id, mock_property, mock_db):
        """Test successful creation of maintenance request."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_property
        
        request_data = {
            'title': 'Leaky Faucet',
            'description': 'Kitchen faucet is leaking',
            'category': 'plumbing',
            'estimated_cost': 150.0,
            'notes': 'Urgent repair needed'
        }
        
        # Execute
        result = property_management_service.create_maintenance_request(sample_property_id, request_data)
        
        # Assert
        assert isinstance(result, MaintenanceRequest)
        assert result.property_id == sample_property_id
        assert result.title == 'Leaky Faucet'
        assert result.description == 'Kitchen faucet is leaking'
        assert result.status == MaintenanceStatusEnum.PENDING
        # "leak" keyword triggers emergency priority
        assert result.priority == MaintenancePriorityEnum.EMERGENCY
        assert result.estimated_cost == 150.0
    
    def test_create_maintenance_request_emergency_priority(self, property_management_service, sample_property_id, mock_property, mock_db):
        """Test creation of emergency maintenance request."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_property
        
        request_data = {
            'title': 'Gas Leak',
            'description': 'Emergency gas leak in basement',
            'category': 'emergency'
        }
        
        # Execute
        result = property_management_service.create_maintenance_request(sample_property_id, request_data)
        
        # Assert
        assert result.priority == MaintenancePriorityEnum.EMERGENCY
    
    def test_create_maintenance_request_property_not_found(self, property_management_service, sample_property_id, mock_db):
        """Test maintenance request creation with non-existent property."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        request_data = {
            'title': 'Test Request',
            'description': 'Test description'
        }
        
        # Execute and Assert
        with pytest.raises(ValueError, match=f"Property {sample_property_id} not found"):
            property_management_service.create_maintenance_request(sample_property_id, request_data)
    
    def test_determine_maintenance_priority(self, property_management_service):
        """Test maintenance priority determination logic."""
        # Test emergency priority
        priority = property_management_service._determine_maintenance_priority('emergency', 'gas leak detected')
        assert priority == MaintenancePriorityEnum.EMERGENCY
        
        # Test high priority
        priority = property_management_service._determine_maintenance_priority('hvac', 'heating system not working')
        assert priority == MaintenancePriorityEnum.HIGH
        
        # Test medium priority (default)
        priority = property_management_service._determine_maintenance_priority('general', 'paint touch up needed')
        assert priority == MaintenancePriorityEnum.MEDIUM
    
    def test_update_maintenance_request(self, property_management_service):
        """Test updating maintenance request."""
        request_id = uuid.uuid4()
        update_data = {
            'status': 'completed',
            'actual_cost': 175.0,
            'completed_date': datetime.now(),
            'notes': 'Repair completed successfully'
        }
        
        result = property_management_service.update_maintenance_request(request_id, update_data)
        
        assert isinstance(result, MaintenanceRequest)
        assert result.id == request_id
        assert result.status == MaintenanceStatusEnum.COMPLETED
        assert result.actual_cost == 175.0
    
    def test_schedule_maintenance(self, property_management_service):
        """Test scheduling maintenance request."""
        request_id = uuid.uuid4()
        scheduled_date = datetime.now() + timedelta(days=2)
        vendor_id = uuid.uuid4()
        
        result = property_management_service.schedule_maintenance(request_id, scheduled_date, vendor_id)
        
        assert isinstance(result, MaintenanceRequest)
        assert result.status == MaintenanceStatusEnum.SCHEDULED
        assert result.scheduled_date == scheduled_date
        assert result.vendor_id == vendor_id
    
    def test_record_expense_success(self, property_management_service, sample_property_id, mock_property, mock_db):
        """Test successful expense recording."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_property
        
        expense_data = {
            'description': 'Plumbing repair',
            'amount': 250.0,
            'vendor_name': 'ABC Plumbing',
            'category': 'maintenance',
            'tax_deductible': True
        }
        
        # Execute
        result = property_management_service.record_expense(sample_property_id, expense_data)
        
        # Assert
        assert isinstance(result, ExpenseRecord)
        assert result.property_id == sample_property_id
        assert result.description == 'Plumbing repair'
        assert result.amount == 250.0
        assert result.category == ExpenseCategoryEnum.MAINTENANCE
        assert result.tax_deductible is True
    
    def test_auto_categorize_expense(self, property_management_service):
        """Test automatic expense categorization."""
        # Test maintenance categorization
        category = property_management_service._auto_categorize_expense('plumbing repair', 'ABC Plumbing')
        assert category == ExpenseCategoryEnum.MAINTENANCE.value
        
        # Test utilities categorization
        category = property_management_service._auto_categorize_expense('electric bill', 'Power Company')
        assert category == ExpenseCategoryEnum.UTILITIES.value
        
        # Test insurance categorization
        category = property_management_service._auto_categorize_expense('property insurance premium', 'Insurance Co')
        assert category == ExpenseCategoryEnum.INSURANCE.value
        
        # Test default categorization
        category = property_management_service._auto_categorize_expense('miscellaneous expense', 'Unknown Vendor')
        assert category == ExpenseCategoryEnum.OTHER.value
    
    def test_record_expense_property_not_found(self, property_management_service, sample_property_id, mock_db):
        """Test expense recording with non-existent property."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        expense_data = {
            'description': 'Test expense',
            'amount': 100.0
        }
        
        # Execute and Assert
        with pytest.raises(ValueError, match=f"Property {sample_property_id} not found"):
            property_management_service.record_expense(sample_property_id, expense_data)
    
    def test_categorize_expenses_bulk(self, property_management_service, sample_property_id):
        """Test bulk expense categorization."""
        # Mock get_expenses to return some uncategorized expenses
        mock_expenses = [
            Mock(category=ExpenseCategoryEnum.OTHER, description='plumbing repair', vendor_name='ABC Plumbing'),
            Mock(category=ExpenseCategoryEnum.OTHER, description='electric bill', vendor_name='Power Co'),
            Mock(category=ExpenseCategoryEnum.MAINTENANCE, description='already categorized', vendor_name='Vendor')
        ]
        
        property_management_service.get_expenses = Mock(return_value=mock_expenses)
        
        result = property_management_service.categorize_expenses_bulk(sample_property_id)
        
        assert result['success'] is True
        assert result['total_expenses'] == 3
        assert result['categorized_count'] == 2  # Two were recategorized
    
    def test_add_tenant_success(self, property_management_service, sample_property_id, mock_property, mock_db):
        """Test successful tenant addition."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_property
        
        tenant_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@email.com',
            'phone': '555-1234',
            'lease_start_date': datetime.now(),
            'lease_end_date': datetime.now() + timedelta(days=365),
            'monthly_rent': 1500.0,
            'security_deposit': 1500.0
        }
        
        # Execute
        result = property_management_service.add_tenant(sample_property_id, tenant_data)
        
        # Assert
        assert isinstance(result, TenantRecord)
        assert result.property_id == sample_property_id
        assert result.first_name == 'John'
        assert result.last_name == 'Doe'
        assert result.email == 'john.doe@email.com'
        assert result.monthly_rent == 1500.0
        assert result.status == TenantStatusEnum.PENDING
    
    def test_add_tenant_property_not_found(self, property_management_service, sample_property_id, mock_db):
        """Test tenant addition with non-existent property."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        tenant_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'lease_start_date': datetime.now(),
            'lease_end_date': datetime.now() + timedelta(days=365),
            'monthly_rent': 1500.0
        }
        
        # Execute and Assert
        with pytest.raises(ValueError, match=f"Property {sample_property_id} not found"):
            property_management_service.add_tenant(sample_property_id, tenant_data)
    
    def test_update_tenant(self, property_management_service):
        """Test tenant update."""
        tenant_id = uuid.uuid4()
        update_data = {
            'status': 'active',
            'monthly_rent': 1600.0,
            'phone': '555-5678'
        }
        
        result = property_management_service.update_tenant(tenant_id, update_data)
        
        assert isinstance(result, TenantRecord)
        assert result.id == tenant_id
        assert result.status == TenantStatusEnum.ACTIVE
        assert result.monthly_rent == 1600.0
    
    def test_process_tenant_move_in(self, property_management_service):
        """Test tenant move-in process."""
        tenant_id = uuid.uuid4()
        move_in_date = datetime.now()
        
        result = property_management_service.process_tenant_move_in(tenant_id, move_in_date)
        
        assert result['success'] is True
        assert 'tenant' in result
        assert 'inspection' in result
        assert isinstance(result['tenant'], TenantRecord)
        assert isinstance(result['inspection'], PropertyInspection)
        assert result['tenant'].status == TenantStatusEnum.ACTIVE
        assert result['inspection'].inspection_type == InspectionTypeEnum.MOVE_IN
    
    def test_process_tenant_move_out(self, property_management_service):
        """Test tenant move-out process."""
        tenant_id = uuid.uuid4()
        move_out_date = datetime.now()
        
        result = property_management_service.process_tenant_move_out(tenant_id, move_out_date)
        
        assert result['success'] is True
        assert 'tenant' in result
        assert 'inspection' in result
        assert isinstance(result['tenant'], TenantRecord)
        assert isinstance(result['inspection'], PropertyInspection)
        assert result['tenant'].status == TenantStatusEnum.INACTIVE
        assert result['inspection'].inspection_type == InspectionTypeEnum.MOVE_OUT
    
    def test_schedule_inspection_success(self, property_management_service, sample_property_id, mock_property, mock_db):
        """Test successful inspection scheduling."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_property
        
        scheduled_date = datetime.now() + timedelta(days=7)
        
        # Execute
        result = property_management_service.schedule_inspection(
            property_id=sample_property_id,
            inspection_type=InspectionTypeEnum.ROUTINE,
            scheduled_date=scheduled_date,
            inspector_name="John Inspector"
        )
        
        # Assert
        assert isinstance(result, PropertyInspection)
        assert result.property_id == sample_property_id
        assert result.inspection_type == InspectionTypeEnum.ROUTINE
        assert result.scheduled_date == scheduled_date
        assert result.inspector_name == "John Inspector"
        assert result.status == "scheduled"
    
    def test_schedule_inspection_property_not_found(self, property_management_service, sample_property_id, mock_db):
        """Test inspection scheduling with non-existent property."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute and Assert
        with pytest.raises(ValueError, match=f"Property {sample_property_id} not found"):
            property_management_service.schedule_inspection(
                property_id=sample_property_id,
                inspection_type=InspectionTypeEnum.ROUTINE,
                scheduled_date=datetime.now(),
                inspector_name="Inspector"
            )
    
    def test_complete_inspection(self, property_management_service):
        """Test inspection completion."""
        inspection_id = uuid.uuid4()
        findings = [
            {'title': 'Leaky Faucet', 'description': 'Kitchen faucet dripping', 'severity': 'medium'},
            {'title': 'Broken Window', 'description': 'Bedroom window cracked', 'severity': 'high'}
        ]
        photos = ['photo1.jpg', 'photo2.jpg']
        
        # Mock create_maintenance_request to avoid actual creation
        property_management_service.create_maintenance_request = Mock()
        
        result = property_management_service.complete_inspection(inspection_id, findings, photos)
        
        assert isinstance(result, PropertyInspection)
        assert result.id == inspection_id
        assert result.status == "completed"
        assert result.findings == findings
        assert result.photos == photos
        assert result.follow_up_required is True
        assert len(result.follow_up_items) == 1  # Only high severity items
        
        # Verify maintenance request was created for high-priority finding
        property_management_service.create_maintenance_request.assert_called_once()
    
    def test_schedule_routine_inspections(self, property_management_service, sample_property_id, mock_property, mock_db):
        """Test scheduling routine inspections."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_property
        
        # Execute
        result = property_management_service.schedule_routine_inspections(sample_property_id)
        
        # Assert
        assert len(result) == 2  # Quarterly and annual inspections
        assert all(isinstance(inspection, PropertyInspection) for inspection in result)
        assert any(inspection.inspection_type == InspectionTypeEnum.ROUTINE for inspection in result)
        assert any(inspection.inspection_type == InspectionTypeEnum.ANNUAL for inspection in result)
    
    def test_get_property_management_dashboard(self, property_management_service, sample_property_id):
        """Test property management dashboard generation."""
        # Mock all the get methods
        property_management_service.get_maintenance_requests = Mock(return_value=[
            Mock(status=MaintenanceStatusEnum.PENDING),
            Mock(status=MaintenanceStatusEnum.COMPLETED)
        ])
        property_management_service.get_expenses = Mock(return_value=[
            Mock(amount=100.0),
            Mock(amount=200.0)
        ])
        property_management_service.get_tenants = Mock(return_value=[
            Mock(status=TenantStatusEnum.ACTIVE),
            Mock(status=TenantStatusEnum.INACTIVE)
        ])
        property_management_service.get_inspections = Mock(return_value=[
            Mock(scheduled_date=datetime.now() + timedelta(days=5)),
            Mock(scheduled_date=datetime.now() - timedelta(days=5))
        ])
        
        result = property_management_service.get_property_management_dashboard(sample_property_id)
        
        assert result['property_id'] == sample_property_id
        assert 'summary' in result
        assert result['summary']['total_monthly_expenses'] == 300.0
        assert result['summary']['pending_maintenance_requests'] == 1
        assert result['summary']['active_tenants'] == 1
        assert result['summary']['upcoming_inspections'] == 1
    
    def test_generate_expense_report(self, property_management_service, sample_property_id):
        """Test expense report generation."""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        # Mock expenses
        mock_expenses = [
            Mock(category=ExpenseCategoryEnum.MAINTENANCE, amount=150.0),
            Mock(category=ExpenseCategoryEnum.UTILITIES, amount=200.0),
            Mock(category=ExpenseCategoryEnum.MAINTENANCE, amount=100.0)
        ]
        property_management_service.get_expenses = Mock(return_value=mock_expenses)
        
        result = property_management_service.generate_expense_report(sample_property_id, start_date, end_date)
        
        assert result['property_id'] == sample_property_id
        assert result['total_expenses'] == 450.0
        assert result['expense_count'] == 3
        assert 'maintenance' in result['category_totals']
        assert 'utilities' in result['category_totals']
        assert result['category_totals']['maintenance'] == 250.0
        assert result['category_totals']['utilities'] == 200.0
    
    def test_error_handling_create_maintenance_request(self, property_management_service, sample_property_id, mock_db):
        """Test error handling in create_maintenance_request."""
        # Setup to raise an exception
        mock_db.query.side_effect = Exception("Database error")
        
        request_data = {
            'title': 'Test Request',
            'description': 'Test description'
        }
        
        # Execute and assert
        with pytest.raises(Exception, match="Database error"):
            property_management_service.create_maintenance_request(sample_property_id, request_data)
    
    def test_error_handling_record_expense(self, property_management_service, sample_property_id, mock_db):
        """Test error handling in record_expense."""
        # Setup to raise an exception
        mock_db.query.side_effect = Exception("Database error")
        
        expense_data = {
            'description': 'Test expense',
            'amount': 100.0
        }
        
        # Execute and assert
        with pytest.raises(Exception, match="Database error"):
            property_management_service.record_expense(sample_property_id, expense_data)
    
    def test_error_handling_add_tenant(self, property_management_service, sample_property_id, mock_db):
        """Test error handling in add_tenant."""
        # Setup to raise an exception
        mock_db.query.side_effect = Exception("Database error")
        
        tenant_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'lease_start_date': datetime.now(),
            'lease_end_date': datetime.now() + timedelta(days=365),
            'monthly_rent': 1500.0
        }
        
        # Execute and assert
        with pytest.raises(Exception, match="Database error"):
            property_management_service.add_tenant(sample_property_id, tenant_data)
    
    def test_error_handling_schedule_inspection(self, property_management_service, sample_property_id, mock_db):
        """Test error handling in schedule_inspection."""
        # Setup to raise an exception
        mock_db.query.side_effect = Exception("Database error")
        
        # Execute and assert
        with pytest.raises(Exception, match="Database error"):
            property_management_service.schedule_inspection(
                property_id=sample_property_id,
                inspection_type=InspectionTypeEnum.ROUTINE,
                scheduled_date=datetime.now(),
                inspector_name="Inspector"
            )


if __name__ == "__main__":
    pytest.main([__file__])