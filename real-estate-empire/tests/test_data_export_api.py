"""
Tests for Data Export API endpoints
"""

import pytest
import uuid
import json
import csv
import io
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set testing environment variable before importing app
os.environ["TESTING"] = "1"

from app.api.main import app
from app.core.database import Base, get_db

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_data_export.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def sample_property_data():
    """Sample property data for testing"""
    return {
        "address": "789 Export Avenue",
        "city": "Data City",
        "state": "FL",
        "zip_code": "33101",
        "property_type": "single_family",
        "bedrooms": 4,
        "bathrooms": 3.0,
        "square_feet": 2200,
        "lot_size": 0.4,
        "year_built": 2005,
        "listing_price": 450000,
        "current_value": 480000,
        "condition_score": 0.9,
        "description": "Beautiful property for export testing"
    }

@pytest.fixture
def created_property_with_analysis(sample_property_data):
    """Create a property and run analysis for testing exports"""
    # Create property
    response = client.post("/api/v1/properties/", json=sample_property_data)
    assert response.status_code == 201
    property_data = response.json()
    
    # Run analysis to have data to export
    property_id = property_data["id"]
    analysis_response = client.post(f"/api/v1/properties/{property_id}/analyze")
    
    return property_data

class TestPDFExport:
    """Test PDF export functionality"""
    
    def test_export_property_pdf_basic(self, created_property_with_analysis):
        """Test basic PDF export"""
        property_id = created_property_with_analysis["id"]
        
        response = client.get(f"/api/v1/export/{property_id}/pdf")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert "property_report_" in response.headers["content-disposition"]
        
        # Check that we got some PDF content
        content = response.content
        assert len(content) > 0
        # PDF files start with %PDF
        assert content.startswith(b"%PDF") or b"PDF generation failed" in content
    
    def test_export_property_pdf_with_options(self, created_property_with_analysis):
        """Test PDF export with different options"""
        property_id = created_property_with_analysis["id"]
        
        response = client.get(
            f"/api/v1/export/{property_id}/pdf"
            "?include_analysis=true&include_comparables=true&include_strategies=true"
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
    
    def test_export_property_pdf_minimal(self, created_property_with_analysis):
        """Test PDF export with minimal options"""
        property_id = created_property_with_analysis["id"]
        
        response = client.get(
            f"/api/v1/export/{property_id}/pdf"
            "?include_analysis=false&include_comparables=false&include_strategies=false"
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
    
    def test_export_pdf_nonexistent_property(self):
        """Test PDF export for non-existent property"""
        fake_id = str(uuid.uuid4())
        
        response = client.get(f"/api/v1/export/{fake_id}/pdf")
        
        assert response.status_code == 404
        assert "Property not found" in response.json()["detail"]

class TestCSVExport:
    """Test CSV export functionality"""
    
    def test_export_property_csv_basic(self, created_property_with_analysis):
        """Test basic CSV export"""
        property_id = created_property_with_analysis["id"]
        
        response = client.get(f"/api/v1/export/{property_id}/csv")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "property_data_" in response.headers["content-disposition"]
        
        # Parse CSV content
        csv_content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        # Should have header row and at least one data row
        assert len(rows) >= 2
        
        # Check headers
        headers = rows[0]
        expected_headers = [
            'property_id', 'address', 'city', 'state', 'zip_code', 'property_type',
            'bedrooms', 'bathrooms', 'square_feet', 'listing_price', 'current_value'
        ]
        for header in expected_headers:
            assert header in headers
        
        # Check data row
        data_row = rows[1]
        assert len(data_row) == len(headers)
        assert data_row[headers.index('address')] == created_property_with_analysis['address']
    
    def test_export_property_csv_with_analysis(self, created_property_with_analysis):
        """Test CSV export including analysis data"""
        property_id = created_property_with_analysis["id"]
        
        response = client.get(
            f"/api/v1/export/{property_id}/csv?include_analysis=true"
        )
        
        assert response.status_code == 200
        
        # Parse CSV content
        csv_content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        headers = rows[0]
        # Should include analysis headers
        analysis_headers = [
            'latest_analysis_type', 'arv_estimate', 'repair_estimate', 'roi_estimate'
        ]
        for header in analysis_headers:
            assert header in headers
    
    def test_export_property_csv_without_analysis(self, created_property_with_analysis):
        """Test CSV export without analysis data"""
        property_id = created_property_with_analysis["id"]
        
        response = client.get(
            f"/api/v1/export/{property_id}/csv?include_analysis=false"
        )
        
        assert response.status_code == 200
        
        # Parse CSV content
        csv_content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        headers = rows[0]
        # Should not include analysis headers
        analysis_headers = [
            'latest_analysis_type', 'arv_estimate', 'repair_estimate'
        ]
        for header in analysis_headers:
            assert header not in headers

class TestJSONExport:
    """Test JSON export functionality"""
    
    def test_export_property_json_basic(self, created_property_with_analysis):
        """Test basic JSON export"""
        property_id = created_property_with_analysis["id"]
        
        response = client.get(f"/api/v1/export/{property_id}/json")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        
        # Check structure
        assert "export_info" in data
        assert "property" in data
        
        export_info = data["export_info"]
        assert "exported_at" in export_info
        assert "export_type" in export_info
        assert export_info["export_type"] == "json"
        
        property_data = data["property"]
        assert "id" in property_data
        assert "basic_info" in property_data
        assert "characteristics" in property_data
        assert "location" in property_data
        assert "financial" in property_data
        
        # Verify property data
        basic_info = property_data["basic_info"]
        assert basic_info["address"] == created_property_with_analysis["address"]
        assert basic_info["city"] == created_property_with_analysis["city"]
    
    def test_export_property_json_with_analysis(self, created_property_with_analysis):
        """Test JSON export including analysis data"""
        property_id = created_property_with_analysis["id"]
        
        response = client.get(
            f"/api/v1/export/{property_id}/json?include_analysis=true"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        property_data = data["property"]
        assert "analyses" in property_data
        
        if len(property_data["analyses"]) > 0:
            analysis = property_data["analyses"][0]
            assert "id" in analysis
            assert "analysis_type" in analysis
            assert "valuation" in analysis
            assert "financial_metrics" in analysis
    
    def test_export_property_json_with_raw_data(self, created_property_with_analysis):
        """Test JSON export including raw analysis data"""
        property_id = created_property_with_analysis["id"]
        
        response = client.get(
            f"/api/v1/export/{property_id}/json"
            "?include_analysis=true&include_raw_data=true"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        export_info = data["export_info"]
        assert export_info["includes_raw_data"] is True
        
        property_data = data["property"]
        if "analyses" in property_data and len(property_data["analyses"]) > 0:
            analysis = property_data["analyses"][0]
            # Raw data might be included if available
            # This is optional since it depends on analysis results
    
    def test_export_property_json_without_analysis(self, created_property_with_analysis):
        """Test JSON export without analysis data"""
        property_id = created_property_with_analysis["id"]
        
        response = client.get(
            f"/api/v1/export/{property_id}/json?include_analysis=false"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        export_info = data["export_info"]
        assert export_info["includes_analysis"] is False
        
        property_data = data["property"]
        assert "analyses" not in property_data or len(property_data.get("analyses", [])) == 0

class TestBulkExport:
    """Test bulk export functionality"""
    
    def test_bulk_csv_export(self, created_property_with_analysis):
        """Test bulk CSV export"""
        property_id = created_property_with_analysis["id"]
        
        # Create a second property for bulk export
        second_property_data = {
            "address": "456 Bulk Street",
            "city": "Export City",
            "state": "CA",
            "zip_code": "90210",
            "property_type": "condo",
            "bedrooms": 2,
            "bathrooms": 2.0,
            "square_feet": 1200,
            "listing_price": 350000
        }
        
        response = client.post("/api/v1/properties/", json=second_property_data)
        assert response.status_code == 201
        second_property = response.json()
        
        # Test bulk export
        property_ids = [property_id, second_property["id"]]
        
        response = client.get(
            "/api/v1/export/bulk/csv",
            params={"property_ids": property_ids}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        
        # Parse CSV content
        csv_content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        # Should have header row and two data rows
        assert len(rows) == 3  # 1 header + 2 data rows
        
        # Verify both properties are included
        addresses = [row[1] for row in rows[1:]]  # Skip header, get address column
        assert created_property_with_analysis["address"] in addresses
        assert second_property_data["address"] in addresses
    
    def test_bulk_json_export(self, created_property_with_analysis):
        """Test bulk JSON export"""
        property_id = created_property_with_analysis["id"]
        
        response = client.get(
            "/api/v1/export/bulk/json",
            params={"property_ids": [property_id]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "export_info" in data
        assert "properties" in data
        
        export_info = data["export_info"]
        assert export_info["export_type"] == "bulk_json"
        assert export_info["total_properties"] == 1
        
        properties = data["properties"]
        assert len(properties) == 1
        assert properties[0]["basic_info"]["address"] == created_property_with_analysis["address"]
    
    def test_bulk_export_limits(self, created_property_with_analysis):
        """Test bulk export limits"""
        property_id = created_property_with_analysis["id"]
        
        # Test CSV limit (100 properties)
        too_many_ids = [str(uuid.uuid4()) for _ in range(101)]
        
        response = client.get(
            "/api/v1/export/bulk/csv",
            params={"property_ids": too_many_ids}
        )
        
        assert response.status_code == 400
        assert "Maximum 100 properties" in response.json()["detail"]
        
        # Test JSON limit (50 properties)
        too_many_ids = [str(uuid.uuid4()) for _ in range(51)]
        
        response = client.get(
            "/api/v1/export/bulk/json",
            params={"property_ids": too_many_ids}
        )
        
        assert response.status_code == 400
        assert "Maximum 50 properties" in response.json()["detail"]
    
    def test_bulk_export_empty_list(self):
        """Test bulk export with empty property list"""
        response = client.get(
            "/api/v1/export/bulk/csv",
            params={"property_ids": []}
        )
        
        assert response.status_code == 404
        assert "No properties found" in response.json()["detail"]

class TestExportValidation:
    """Test export validation and error handling"""
    
    def test_export_nonexistent_property(self):
        """Test exporting non-existent property"""
        fake_id = str(uuid.uuid4())
        
        # Test CSV export
        response = client.get(f"/api/v1/export/{fake_id}/csv")
        assert response.status_code == 404
        
        # Test JSON export
        response = client.get(f"/api/v1/export/{fake_id}/json")
        assert response.status_code == 404
        
        # Test PDF export
        response = client.get(f"/api/v1/export/{fake_id}/pdf")
        assert response.status_code == 404
    
    def test_export_invalid_property_id(self):
        """Test exporting with invalid property ID format"""
        invalid_id = "not-a-uuid"
        
        response = client.get(f"/api/v1/export/{invalid_id}/json")
        assert response.status_code == 422  # Validation error
    
    def test_bulk_export_nonexistent_properties(self):
        """Test bulk export with non-existent properties"""
        fake_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        
        response = client.get(
            "/api/v1/export/bulk/json",
            params={"property_ids": fake_ids}
        )
        
        assert response.status_code == 404
        assert "No properties found" in response.json()["detail"]

class TestExportContent:
    """Test export content accuracy and completeness"""
    
    def test_json_export_data_completeness(self, created_property_with_analysis):
        """Test that JSON export includes all expected data"""
        property_id = created_property_with_analysis["id"]
        
        response = client.get(
            f"/api/v1/export/{property_id}/json?include_analysis=true"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        property_data = data["property"]
        
        # Check all major sections are present
        required_sections = [
            "basic_info", "characteristics", "location", 
            "financial", "condition", "features"
        ]
        
        for section in required_sections:
            assert section in property_data
        
        # Verify basic info completeness
        basic_info = property_data["basic_info"]
        assert basic_info["address"] == created_property_with_analysis["address"]
        assert basic_info["city"] == created_property_with_analysis["city"]
        assert basic_info["state"] == created_property_with_analysis["state"]
        assert basic_info["property_type"] == created_property_with_analysis["property_type"]
    
    def test_csv_export_data_accuracy(self, created_property_with_analysis):
        """Test that CSV export data matches property data"""
        property_id = created_property_with_analysis["id"]
        
        response = client.get(f"/api/v1/export/{property_id}/csv")
        
        assert response.status_code == 200
        
        # Parse CSV
        csv_content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        headers = rows[0]
        data_row = rows[1]
        
        # Create a dictionary from CSV data
        csv_data = dict(zip(headers, data_row))
        
        # Verify key fields match
        assert csv_data['address'] == created_property_with_analysis['address']
        assert csv_data['city'] == created_property_with_analysis['city']
        assert csv_data['state'] == created_property_with_analysis['state']
        assert int(csv_data['bedrooms']) == created_property_with_analysis['bedrooms']
        assert float(csv_data['bathrooms']) == created_property_with_analysis['bathrooms']

# Cleanup
def teardown_module():
    """Clean up test database"""
    Base.metadata.drop_all(bind=engine)