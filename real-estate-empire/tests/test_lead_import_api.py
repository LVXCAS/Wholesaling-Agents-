"""
Unit tests for the lead import API router.
"""

import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from io import BytesIO

from app.api.routers.lead_import import router
from app.services.lead_import_service import ImportResult, ImportStatusEnum
from app.models.lead import LeadSourceEnum


# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestLeadImportAPI:
    """Test cases for Lead Import API endpoints."""
    
    @pytest.fixture
    def sample_csv_content(self):
        """Sample CSV content for testing."""
        return """Address,City,State,ZIP,Owner Name,Phone,Email,Price
123 Main St,Anytown,CA,12345,John Doe,(555) 123-4567,john@example.com,$250000
456 Oak Ave,Somewhere,TX,67890,Jane Smith,555-987-6543,jane@example.com,$180000"""
    
    @pytest.fixture
    def sample_analysis_result(self):
        """Sample analysis result for mocking."""
        return {
            "headers": ["Address", "City", "State", "ZIP", "Owner Name", "Phone", "Email", "Price"],
            "sample_rows": [
                ["123 Main St", "Anytown", "CA", "12345", "John Doe", "(555) 123-4567", "john@example.com", "$250000"],
                ["456 Oak Ave", "Somewhere", "TX", "67890", "Jane Smith", "555-987-6543", "jane@example.com", "$180000"]
            ],
            "total_rows": 3,
            "suggested_mapping": {
                "address": "Address",
                "city": "City",
                "state": "State",
                "zip_code": "ZIP",
                "owner_name": "Owner Name",
                "owner_phone": "Phone",
                "owner_email": "Email",
                "asking_price": "Price"
            },
            "analysis_status": "success"
        }
    
    @pytest.fixture
    def sample_import_result(self):
        """Sample import result for mocking."""
        return ImportResult(
            total_rows=2,
            successful_imports=2,
            failed_imports=0,
            duplicates_found=0,
            errors=[],
            status=ImportStatusEnum.COMPLETED,
            import_id="test-import-123",
            created_leads=["lead-1", "lead-2"],
            created_properties=["prop-1", "prop-2"]
        )
    
    @patch('app.api.routers.lead_import.get_db')
    @patch('app.api.routers.lead_import.LeadImportService')
    def test_analyze_csv_success(self, mock_service_class, mock_get_db, sample_csv_content, sample_analysis_result):
        """Test successful CSV analysis."""
        # Mock service
        mock_service = Mock()
        mock_service.analyze_csv.return_value = sample_analysis_result
        mock_service_class.return_value = mock_service
        
        # Mock database
        mock_get_db.return_value = Mock()
        
        # Make request
        response = client.post(
            "/api/lead-import/analyze",
            json={"csv_content": sample_csv_content}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_status"] == "success"
        assert "Address" in data["headers"]
        assert "suggested_mapping" in data
        assert data["suggested_mapping"]["address"] == "Address"
    
    @patch('app.api.routers.lead_import.get_db')
    @patch('app.api.routers.lead_import.LeadImportService')
    def test_analyze_csv_error(self, mock_service_class, mock_get_db):
        """Test CSV analysis with error."""
        # Mock service to raise exception
        mock_service = Mock()
        mock_service.analyze_csv.side_effect = Exception("Invalid CSV format")
        mock_service_class.return_value = mock_service
        
        # Mock database
        mock_get_db.return_value = Mock()
        
        # Make request
        response = client.post(
            "/api/lead-import/analyze",
            json={"csv_content": "invalid csv"}
        )
        
        assert response.status_code == 400
        assert "CSV analysis failed" in response.json()["detail"]
    
    @patch('app.api.routers.lead_import.get_db')
    @patch('app.api.routers.lead_import.LeadImportService')
    def test_analyze_csv_file_success(self, mock_service_class, mock_get_db, sample_csv_content, sample_analysis_result):
        """Test successful CSV file analysis."""
        # Mock service
        mock_service = Mock()
        mock_service.analyze_csv.return_value = sample_analysis_result
        mock_service_class.return_value = mock_service
        
        # Mock database
        mock_get_db.return_value = Mock()
        
        # Create file-like object
        csv_file = BytesIO(sample_csv_content.encode('utf-8'))
        
        # Make request
        response = client.post(
            "/api/lead-import/analyze-file",
            files={"file": ("test.csv", csv_file, "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_status"] == "success"
    
    def test_analyze_csv_file_invalid_extension(self):
        """Test CSV file analysis with invalid file extension."""
        # Create file-like object with wrong extension
        file_content = BytesIO(b"some content")
        
        # Make request
        response = client.post(
            "/api/lead-import/analyze-file",
            files={"file": ("test.txt", file_content, "text/plain")}
        )
        
        assert response.status_code == 400
        assert "File must be a CSV file" in response.json()["detail"]
    
    @patch('app.api.routers.lead_import.get_db')
    @patch('app.api.routers.lead_import.LeadImportService')
    def test_import_leads_success(self, mock_service_class, mock_get_db, sample_csv_content, sample_import_result):
        """Test successful lead import."""
        # Mock service
        mock_service = Mock()
        mock_service.import_leads.return_value = sample_import_result
        mock_service_class.return_value = mock_service
        
        # Mock database
        mock_get_db.return_value = Mock()
        
        # Prepare request data
        request_data = {
            "csv_content": sample_csv_content,
            "column_mapping": {
                "address": "Address",
                "city": "City",
                "state": "State",
                "zip_code": "ZIP",
                "owner_name": "Owner Name",
                "owner_phone": "Phone",
                "owner_email": "Email",
                "asking_price": "Price"
            },
            "default_source": "other",
            "skip_duplicates": True
        }
        
        # Make request
        response = client.post(
            "/api/lead-import/import",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["successful_imports"] == 2
        assert data["failed_imports"] == 0
        assert len(data["created_leads"]) == 2
        assert len(data["created_properties"]) == 2
    
    @patch('app.api.routers.lead_import.get_db')
    @patch('app.api.routers.lead_import.LeadImportService')
    def test_import_leads_error(self, mock_service_class, mock_get_db, sample_csv_content):
        """Test lead import with error."""
        # Mock service to raise exception
        mock_service = Mock()
        mock_service.import_leads.side_effect = Exception("Import failed")
        mock_service_class.return_value = mock_service
        
        # Mock database
        mock_get_db.return_value = Mock()
        
        # Prepare request data
        request_data = {
            "csv_content": sample_csv_content,
            "column_mapping": {
                "address": "Address",
                "city": "City"
            },
            "default_source": "other",
            "skip_duplicates": True
        }
        
        # Make request
        response = client.post(
            "/api/lead-import/import",
            json=request_data
        )
        
        assert response.status_code == 400
        assert "Lead import failed" in response.json()["detail"]
    
    @patch('app.api.routers.lead_import.get_db')
    @patch('app.api.routers.lead_import.LeadImportService')
    def test_import_leads_from_file_success(self, mock_service_class, mock_get_db, sample_csv_content, sample_import_result):
        """Test successful lead import from file."""
        # Mock service
        mock_service = Mock()
        mock_service.import_leads.return_value = sample_import_result
        mock_service_class.return_value = mock_service
        
        # Mock database
        mock_get_db.return_value = Mock()
        
        # Create file-like object
        csv_file = BytesIO(sample_csv_content.encode('utf-8'))
        
        # Prepare column mapping
        column_mapping = {
            "address": "Address",
            "city": "City",
            "state": "State",
            "zip_code": "ZIP"
        }
        
        # Make request
        response = client.post(
            "/api/lead-import/import-file",
            files={"file": ("test.csv", csv_file, "text/csv")},
            data={
                "column_mapping": json.dumps(column_mapping),
                "default_source": "other",
                "skip_duplicates": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["successful_imports"] == 2
    
    def test_import_leads_from_file_invalid_extension(self):
        """Test lead import from file with invalid extension."""
        # Create file-like object with wrong extension
        file_content = BytesIO(b"some content")
        
        # Make request
        response = client.post(
            "/api/lead-import/import-file",
            files={"file": ("test.txt", file_content, "text/plain")},
            data={
                "column_mapping": "{}",
                "default_source": "other",
                "skip_duplicates": True
            }
        )
        
        assert response.status_code == 400
        assert "File must be a CSV file" in response.json()["detail"]
    
    def test_import_leads_from_file_invalid_mapping_json(self, sample_csv_content):
        """Test lead import from file with invalid mapping JSON."""
        # Create file-like object
        csv_file = BytesIO(sample_csv_content.encode('utf-8'))
        
        # Make request with invalid JSON
        response = client.post(
            "/api/lead-import/import-file",
            files={"file": ("test.csv", csv_file, "text/csv")},
            data={
                "column_mapping": "invalid json",
                "default_source": "other",
                "skip_duplicates": True
            }
        )
        
        assert response.status_code == 400
        assert "Invalid column mapping JSON" in response.json()["detail"]
    
    def test_get_mapping_template(self):
        """Test getting mapping template."""
        response = client.get("/api/lead-import/mapping-template")
        
        assert response.status_code == 200
        data = response.json()
        assert "property_fields" in data
        assert "lead_fields" in data
        assert "example_mapping" in data
        assert "address" in data["property_fields"]
        assert "owner_name" in data["lead_fields"]
    
    def test_get_available_sources(self):
        """Test getting available sources."""
        response = client.get("/api/lead-import/sources")
        
        assert response.status_code == 200
        data = response.json()
        assert "sources" in data
        assert len(data["sources"]) > 0
        
        # Check that all enum values are present
        source_values = [source["value"] for source in data["sources"]]
        for source_enum in LeadSourceEnum:
            assert source_enum.value in source_values
    
    def test_request_validation(self):
        """Test request validation for required fields."""
        # Test analyze endpoint without csv_content
        response = client.post("/api/lead-import/analyze", json={})
        assert response.status_code == 422  # Validation error
        
        # Test import endpoint without required fields
        response = client.post("/api/lead-import/import", json={})
        assert response.status_code == 422  # Validation error
    
    @patch('app.api.routers.lead_import.get_db')
    @patch('app.api.routers.lead_import.LeadImportService')
    def test_import_with_different_sources(self, mock_service_class, mock_get_db, sample_csv_content, sample_import_result):
        """Test import with different lead sources."""
        # Mock service
        mock_service = Mock()
        mock_service.import_leads.return_value = sample_import_result
        mock_service_class.return_value = mock_service
        
        # Mock database
        mock_get_db.return_value = Mock()
        
        # Test with different sources
        for source in LeadSourceEnum:
            request_data = {
                "csv_content": sample_csv_content,
                "column_mapping": {"address": "Address", "city": "City", "state": "State", "zip_code": "ZIP"},
                "default_source": source.value,
                "skip_duplicates": True
            }
            
            response = client.post("/api/lead-import/import", json=request_data)
            assert response.status_code == 200
    
    @patch('app.api.routers.lead_import.get_db')
    @patch('app.api.routers.lead_import.LeadImportService')
    def test_import_skip_duplicates_options(self, mock_service_class, mock_get_db, sample_csv_content, sample_import_result):
        """Test import with different skip_duplicates options."""
        # Mock service
        mock_service = Mock()
        mock_service.import_leads.return_value = sample_import_result
        mock_service_class.return_value = mock_service
        
        # Mock database
        mock_get_db.return_value = Mock()
        
        # Test with skip_duplicates = True
        request_data = {
            "csv_content": sample_csv_content,
            "column_mapping": {"address": "Address", "city": "City", "state": "State", "zip_code": "ZIP"},
            "default_source": "other",
            "skip_duplicates": True
        }
        
        response = client.post("/api/lead-import/import", json=request_data)
        assert response.status_code == 200
        
        # Test with skip_duplicates = False
        request_data["skip_duplicates"] = False
        response = client.post("/api/lead-import/import", json=request_data)
        assert response.status_code == 200
        
        # Verify service was called with correct parameters
        assert mock_service.import_leads.call_count == 2
        calls = mock_service.import_leads.call_args_list
        assert calls[0][1]["skip_duplicates"] == True
        assert calls[1][1]["skip_duplicates"] == False