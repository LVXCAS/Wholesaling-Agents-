"""
Unit tests for the lead import service.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.lead_import_service import (
    LeadImportService, ColumnMapping, ImportResult, ImportStatusEnum
)
from app.models.lead import PropertyLeadDB, LeadSourceEnum, LeadStatusEnum
from app.models.property import PropertyDB


class TestLeadImportService:
    """Test cases for LeadImportService."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def import_service(self, mock_db):
        """Create LeadImportService instance with mock database."""
        return LeadImportService(mock_db)
    
    @pytest.fixture
    def sample_csv_content(self):
        """Sample CSV content for testing."""
        return """Address,City,State,ZIP,Owner Name,Phone,Email,Price
123 Main St,Anytown,CA,12345,John Doe,(555) 123-4567,john@example.com,$250000
456 Oak Ave,Somewhere,TX,67890,Jane Smith,555-987-6543,jane@example.com,$180000
789 Pine Rd,Elsewhere,FL,11111,Bob Johnson,5551234567,bob@example.com,$320000"""
    
    @pytest.fixture
    def sample_column_mapping(self):
        """Sample column mapping for testing."""
        return ColumnMapping(
            address="Address",
            city="City",
            state="State",
            zip_code="ZIP",
            owner_name="Owner Name",
            owner_phone="Phone",
            owner_email="Email",
            asking_price="Price"
        )
    
    def test_analyze_csv_success(self, import_service, sample_csv_content):
        """Test successful CSV analysis."""
        result = import_service.analyze_csv(sample_csv_content)
        
        assert result["analysis_status"] == "success"
        assert "Address" in result["headers"]
        assert "City" in result["headers"]
        assert len(result["sample_rows"]) <= 5
        assert "suggested_mapping" in result
        assert result["suggested_mapping"]["address"] == "Address"
        assert result["suggested_mapping"]["city"] == "City"
    
    def test_analyze_csv_empty_content(self, import_service):
        """Test CSV analysis with empty content."""
        result = import_service.analyze_csv("")
        
        assert result["analysis_status"] == "error"
        assert "error_message" in result
    
    def test_analyze_csv_invalid_content(self, import_service):
        """Test CSV analysis with invalid content."""
        result = import_service.analyze_csv("invalid,csv\ncontent")
        
        # Should still work with basic CSV content
        assert result["analysis_status"] == "success"
        assert result["headers"] == ["invalid", "csv"]
    
    def test_suggest_column_mapping(self, import_service):
        """Test column mapping suggestions."""
        headers = ["Property Address", "City", "State", "ZIP Code", "Owner Name", "Phone Number"]
        mapping = import_service._suggest_column_mapping(headers)
        
        assert mapping["address"] == "Property Address"
        assert mapping["city"] == "City"
        assert mapping["state"] == "State"
        assert mapping["zip_code"] == "ZIP Code"
        assert mapping["owner_name"] == "Owner Name"
        assert mapping["owner_phone"] == "Phone Number"
    
    def test_extract_property_data_success(self, import_service, sample_column_mapping):
        """Test successful property data extraction."""
        row = {
            "Address": "123 Main St",
            "City": "Anytown",
            "State": "CA",
            "ZIP": "12345",
            "Bedrooms": "3",
            "Bathrooms": "2.5"
        }
        
        # Add bedroom and bathroom mapping
        sample_column_mapping.bedrooms = "Bedrooms"
        sample_column_mapping.bathrooms = "Bathrooms"
        
        result = import_service._extract_property_data(row, sample_column_mapping, 1)
        
        assert result["address"] == "123 Main St"
        assert result["city"] == "Anytown"
        assert result["state"] == "CA"
        assert result["zip_code"] == "12345"
        assert result["bedrooms"] == 3
        assert result["bathrooms"] == 2.5
    
    def test_extract_property_data_missing_required(self, import_service, sample_column_mapping):
        """Test property data extraction with missing required fields."""
        row = {
            "Address": "123 Main St",
            "City": "Anytown",
            # Missing State and ZIP
        }
        
        with pytest.raises(ValueError, match="Missing required property fields"):
            import_service._extract_property_data(row, sample_column_mapping, 1)
    
    def test_extract_lead_data_success(self, import_service, sample_column_mapping):
        """Test successful lead data extraction."""
        property_id = uuid.uuid4()
        row = {
            "Owner Name": "John Doe",
            "Phone": "(555) 123-4567",
            "Email": "john@example.com",
            "Price": "$250,000"
        }
        
        result = import_service._extract_lead_data(
            row, sample_column_mapping, property_id, LeadSourceEnum.OTHER, 1
        )
        
        assert result["property_id"] == property_id
        assert result["owner_name"] == "John Doe"
        assert result["owner_phone"] == "(555) 123-4567"
        assert result["owner_email"] == "john@example.com"
        assert result["asking_price"] == 250000.0
        assert result["source"] == LeadSourceEnum.OTHER
    
    def test_normalize_phone(self, import_service):
        """Test phone number normalization."""
        assert import_service._normalize_phone("5551234567") == "(555) 123-4567"
        assert import_service._normalize_phone("(555) 123-4567") == "(555) 123-4567"
        assert import_service._normalize_phone("555-123-4567") == "(555) 123-4567"
        assert import_service._normalize_phone("1-555-123-4567") == "(555) 123-4567"
        assert import_service._normalize_phone("invalid") == "invalid"
    
    def test_normalize_property_type(self, import_service):
        """Test property type normalization."""
        assert import_service._normalize_property_type("Single Family") == "single_family"
        assert import_service._normalize_property_type("SFH") == "single_family"
        assert import_service._normalize_property_type("Multi-Family") == "multi_family"
        assert import_service._normalize_property_type("Condo") == "condo"
        assert import_service._normalize_property_type("Unknown Type") == "single_family"
    
    def test_normalize_source(self, import_service):
        """Test source normalization."""
        assert import_service._normalize_source("MLS") == "mls"
        assert import_service._normalize_source("Public Records") == "public_records"
        assert import_service._normalize_source("FSBO") == "fsbo"
        assert import_service._normalize_source("Unknown Source") == "other"
    
    def test_is_valid_email(self, import_service):
        """Test email validation."""
        assert import_service._is_valid_email("test@example.com") == True
        assert import_service._is_valid_email("user.name@domain.co.uk") == True
        assert import_service._is_valid_email("invalid-email") == False
        assert import_service._is_valid_email("@domain.com") == False
        assert import_service._is_valid_email("user@") == False
    
    def test_safe_int_convert(self, import_service):
        """Test safe integer conversion."""
        assert import_service._safe_int_convert("123") == 123
        assert import_service._safe_int_convert("1,234") == 1234
        assert import_service._safe_int_convert("$1,234") == 1234
        assert import_service._safe_int_convert("123.45") == 123
        assert import_service._safe_int_convert("invalid") is None
        assert import_service._safe_int_convert("") is None
    
    def test_safe_float_convert(self, import_service):
        """Test safe float conversion."""
        assert import_service._safe_float_convert("123.45") == 123.45
        assert import_service._safe_float_convert("1,234.56") == 1234.56
        assert import_service._safe_float_convert("$1,234.56") == 1234.56
        assert import_service._safe_float_convert("invalid") is None
        assert import_service._safe_float_convert("") is None
    
    def test_find_duplicate_property_exists(self, import_service, mock_db):
        """Test finding duplicate property when it exists."""
        property_data = {
            "address": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "12345"
        }
        
        existing_property = PropertyDB(id=uuid.uuid4(), **property_data)
        mock_db.query.return_value.filter.return_value.first.return_value = existing_property
        
        result = import_service._find_duplicate_property(property_data)
        
        assert result == existing_property
        mock_db.query.assert_called_once_with(PropertyDB)
    
    def test_find_duplicate_property_not_exists(self, import_service, mock_db):
        """Test finding duplicate property when it doesn't exist."""
        property_data = {
            "address": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "12345"
        }
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = import_service._find_duplicate_property(property_data)
        
        assert result is None
    
    def test_find_duplicate_lead_by_email(self, import_service, mock_db):
        """Test finding duplicate lead by email."""
        property_id = uuid.uuid4()
        lead_data = {
            "property_id": property_id,
            "owner_email": "john@example.com"
        }
        
        existing_lead = PropertyLeadDB(id=uuid.uuid4(), **lead_data)
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = existing_lead
        
        result = import_service._find_duplicate_lead(lead_data, property_id)
        
        assert result == existing_lead
    
    def test_find_duplicate_lead_not_exists(self, import_service, mock_db):
        """Test finding duplicate lead when it doesn't exist."""
        property_id = uuid.uuid4()
        lead_data = {
            "property_id": property_id,
            "owner_email": "john@example.com"
        }
        
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        
        result = import_service._find_duplicate_lead(lead_data, property_id)
        
        assert result is None
    
    def test_import_leads_success(self, import_service, mock_db, sample_csv_content, sample_column_mapping):
        """Test successful lead import."""
        # Mock no duplicates found
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        
        # Mock successful database operations
        mock_property = Mock()
        mock_property.id = uuid.uuid4()
        mock_lead = Mock()
        mock_lead.id = uuid.uuid4()
        
        mock_db.add.side_effect = None
        mock_db.flush.side_effect = None
        mock_db.commit.side_effect = None
        
        # Mock the created objects
        def mock_add(obj):
            if isinstance(obj, PropertyDB):
                obj.id = mock_property.id
            elif isinstance(obj, PropertyLeadDB):
                obj.id = mock_lead.id
        
        mock_db.add.side_effect = mock_add
        
        result = import_service.import_leads(
            csv_content=sample_csv_content,
            column_mapping=sample_column_mapping,
            default_source=LeadSourceEnum.OTHER,
            skip_duplicates=True
        )
        
        assert result.status == ImportStatusEnum.COMPLETED
        assert result.successful_imports == 3
        assert result.failed_imports == 0
        assert result.duplicates_found == 0
        assert len(result.created_leads) == 3
        assert len(result.created_properties) == 3
    
    def test_import_leads_empty_csv(self, import_service, sample_column_mapping):
        """Test import with empty CSV."""
        empty_csv = "Address,City,State,ZIP\n"  # Header only
        
        result = import_service.import_leads(
            csv_content=empty_csv,
            column_mapping=sample_column_mapping,
            default_source=LeadSourceEnum.OTHER,
            skip_duplicates=True
        )
        
        assert result.status == ImportStatusEnum.FAILED
        assert result.total_rows == 0
        assert result.successful_imports == 0
        assert len(result.errors) == 1
        assert "No data rows found" in result.errors[0]["error"]
    
    def test_import_leads_with_duplicates(self, import_service, mock_db, sample_csv_content, sample_column_mapping):
        """Test import with duplicate leads."""
        # Mock existing property found (duplicate)
        existing_property = PropertyDB(id=uuid.uuid4())
        mock_db.query.return_value.filter.return_value.first.return_value = existing_property
        
        # Mock existing lead found (duplicate)
        existing_lead = PropertyLeadDB(id=uuid.uuid4())
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = existing_lead
        
        result = import_service.import_leads(
            csv_content=sample_csv_content,
            column_mapping=sample_column_mapping,
            default_source=LeadSourceEnum.OTHER,
            skip_duplicates=True
        )
        
        assert result.duplicates_found == 3  # All leads are duplicates
        assert result.successful_imports == 0
        assert result.status == ImportStatusEnum.FAILED
    
    def test_import_leads_with_errors(self, import_service, sample_column_mapping):
        """Test import with validation errors."""
        # CSV with missing required fields
        invalid_csv = """Address,City,State,ZIP,Owner Name
123 Main St,Anytown,,12345,John Doe
456 Oak Ave,Somewhere,TX,,Jane Smith"""
        
        result = import_service.import_leads(
            csv_content=invalid_csv,
            column_mapping=sample_column_mapping,
            default_source=LeadSourceEnum.OTHER,
            skip_duplicates=True
        )
        
        assert result.status == ImportStatusEnum.FAILED
        assert result.failed_imports == 2
        assert result.successful_imports == 0
        assert len(result.errors) == 2
    
    def test_import_leads_partial_success(self, import_service, mock_db, sample_column_mapping):
        """Test import with partial success."""
        # CSV with one valid row and one invalid row
        mixed_csv = """Address,City,State,ZIP,Owner Name
123 Main St,Anytown,CA,12345,John Doe
456 Oak Ave,Somewhere,,67890,Jane Smith"""
        
        # Mock no duplicates for valid row
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        
        # Mock successful database operations for valid row
        mock_property = Mock()
        mock_property.id = uuid.uuid4()
        mock_lead = Mock()
        mock_lead.id = uuid.uuid4()
        
        def mock_add(obj):
            if isinstance(obj, PropertyDB):
                obj.id = mock_property.id
            elif isinstance(obj, PropertyLeadDB):
                obj.id = mock_lead.id
        
        mock_db.add.side_effect = mock_add
        
        result = import_service.import_leads(
            csv_content=mixed_csv,
            column_mapping=sample_column_mapping,
            default_source=LeadSourceEnum.OTHER,
            skip_duplicates=True
        )
        
        assert result.status == ImportStatusEnum.PARTIAL
        assert result.successful_imports == 1
        assert result.failed_imports == 1
        assert len(result.errors) == 1
    
    def test_get_mapped_value(self, import_service):
        """Test getting mapped value from row."""
        row = {"Column1": "Value1", "Column2": "  Value2  ", "Column3": ""}
        
        assert import_service._get_mapped_value(row, "Column1") == "Value1"
        assert import_service._get_mapped_value(row, "Column2") == "Value2"
        assert import_service._get_mapped_value(row, "Column3") is None
        assert import_service._get_mapped_value(row, "NonExistent") is None
        assert import_service._get_mapped_value(row, None) is None