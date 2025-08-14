"""
Tests for Property Analysis API endpoints
"""

import pytest
import uuid
import os
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set testing environment variable before importing app
os.environ["TESTING"] = "1"

from app.api.main import app
from app.core.database import Base, get_db
from app.models.property import PropertyDB, PropertyAnalysisDB

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_property_analysis.db"

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
        "address": "123 Test Street",
        "city": "Test City",
        "state": "CA",
        "zip_code": "12345",
        "property_type": "single_family",
        "bedrooms": 3,
        "bathrooms": 2.0,
        "square_feet": 1500,
        "lot_size": 0.25,
        "year_built": 2000,
        "listing_price": 300000,
        "current_value": 320000,
        "condition_score": 0.8
    }

@pytest.fixture
def created_property(sample_property_data):
    """Create a property in the test database"""
    response = client.post("/api/v1/properties/", json=sample_property_data)
    assert response.status_code == 201
    return response.json()

class TestPropertyCRUD:
    """Test property CRUD operations"""
    
    def test_create_property(self, sample_property_data):
        """Test creating a new property"""
        response = client.post("/api/v1/properties/", json=sample_property_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["address"] == sample_property_data["address"]
        assert data["city"] == sample_property_data["city"]
        assert data["property_type"] == sample_property_data["property_type"]
        assert "id" in data
        assert "created_at" in data
    
    def test_get_property(self, created_property):
        """Test retrieving a property by ID"""
        property_id = created_property["id"]
        response = client.get(f"/api/v1/properties/{property_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == property_id
        assert data["address"] == created_property["address"]
    
    def test_get_nonexistent_property(self):
        """Test retrieving a non-existent property"""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/properties/{fake_id}")
        
        assert response.status_code == 404
        response_data = response.json()
        assert "Property not found" in response_data.get("detail", response_data.get("error", ""))
    
    def test_update_property(self, created_property):
        """Test updating a property"""
        property_id = created_property["id"]
        update_data = {
            "listing_price": 350000,
            "bedrooms": 4,
            "description": "Updated description"
        }
        
        response = client.put(f"/api/v1/properties/{property_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["listing_price"] == 350000
        assert data["bedrooms"] == 4
        assert data["description"] == "Updated description"
        # Ensure other fields remain unchanged
        assert data["address"] == created_property["address"]
    
    def test_list_properties(self, created_property):
        """Test listing properties"""
        response = client.get("/api/v1/properties/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check if our created property is in the list
        property_ids = [prop["id"] for prop in data]
        assert created_property["id"] in property_ids
    
    def test_list_properties_with_filters(self, created_property):
        """Test listing properties with filters"""
        # Filter by city
        response = client.get("/api/v1/properties/?city=Test City")
        assert response.status_code == 200
        data = response.json()
        assert all(prop["city"] == "Test City" for prop in data)
        
        # Filter by property type
        response = client.get("/api/v1/properties/?property_type=single_family")
        assert response.status_code == 200
        data = response.json()
        assert all(prop["property_type"] == "single_family" for prop in data)
    
    def test_delete_property(self, created_property):
        """Test deleting a property"""
        property_id = created_property["id"]
        
        # Delete the property
        response = client.delete(f"/api/v1/properties/{property_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify it's deleted
        response = client.get(f"/api/v1/properties/{property_id}")
        assert response.status_code == 404

class TestPropertyAnalysis:
    """Test property analysis endpoints"""
    
    def test_analyze_property_comprehensive(self, created_property):
        """Test comprehensive property analysis"""
        property_id = created_property["id"]
        
        response = client.post(f"/api/v1/properties/{property_id}/analyze?analysis_type=comprehensive")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["property_id"] == property_id
        assert data["analysis_type"] == "comprehensive"
        assert "analysis" in data
        assert "timestamp" in data
    
    def test_analyze_property_valuation_only(self, created_property):
        """Test valuation-only analysis"""
        property_id = created_property["id"]
        
        response = client.post(f"/api/v1/properties/{property_id}/analyze?analysis_type=valuation")
        
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_type"] == "valuation"
    
    def test_get_comparable_properties(self, created_property):
        """Test getting comparable properties"""
        property_id = created_property["id"]
        
        response = client.get(f"/api/v1/properties/{property_id}/comparables")
        
        assert response.status_code == 200
        data = response.json()
        assert "comparable_properties" in data
        assert "valuation_estimate" in data
        assert "search_criteria" in data
        assert isinstance(data["comparable_properties"], list)
    
    def test_get_comparable_properties_with_params(self, created_property):
        """Test getting comparable properties with custom parameters"""
        property_id = created_property["id"]
        
        response = client.get(
            f"/api/v1/properties/{property_id}/comparables"
            "?max_distance=1.5&max_age_days=90&min_comps=5"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["search_criteria"]["max_distance_miles"] == 1.5
        assert data["search_criteria"]["max_age_days"] == 90
        assert data["search_criteria"]["min_comparables"] == 5
    
    def test_estimate_repair_costs(self, created_property):
        """Test repair cost estimation"""
        property_id = created_property["id"]
        
        response = client.post(
            f"/api/v1/properties/{property_id}/repair-estimate",
            json={
                "photos": ["http://example.com/photo1.jpg", "http://example.com/photo2.jpg"],
                "description": "Property needs kitchen and bathroom updates",
                "condition_override": "fair"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "repair_estimate" in data
        assert "analysis_inputs" in data
        assert data["analysis_inputs"]["photos_provided"] == 2
        assert data["analysis_inputs"]["description_provided"] is True
        assert data["analysis_inputs"]["condition_override"] == "fair"
    
    def test_get_property_analyses_history(self, created_property):
        """Test getting property analysis history"""
        property_id = created_property["id"]
        
        # First create an analysis
        client.post(f"/api/v1/properties/{property_id}/analyze")
        
        # Then get the history
        response = client.get(f"/api/v1/properties/{property_id}/analyses")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            analysis = data[0]
            assert "id" in analysis
            assert "analysis_type" in analysis
            assert "created_at" in analysis

class TestPropertyAnalysisValidation:
    """Test validation and error handling"""
    
    def test_analyze_nonexistent_property(self):
        """Test analyzing a non-existent property"""
        fake_id = str(uuid.uuid4())
        response = client.post(f"/api/v1/properties/{fake_id}/analyze")
        
        assert response.status_code == 404
        assert "Property not found" in response.json()["detail"]
    
    def test_create_property_invalid_data(self):
        """Test creating property with invalid data"""
        invalid_data = {
            "address": "",  # Empty address
            "city": "Test City",
            "state": "CA",
            "zip_code": "12345",
            "bedrooms": -1,  # Invalid bedrooms
            "condition_score": 1.5  # Invalid condition score (should be 0-1)
        }
        
        response = client.post("/api/v1/properties/", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_update_property_invalid_id(self):
        """Test updating property with invalid ID"""
        response = client.put("/api/v1/properties/invalid-id", json={"listing_price": 300000})
        assert response.status_code == 422  # Invalid UUID format
    
    def test_get_comparables_invalid_params(self, created_property):
        """Test getting comparables with invalid parameters"""
        property_id = created_property["id"]
        
        # Test with negative distance
        response = client.get(f"/api/v1/properties/{property_id}/comparables?max_distance=-1")
        # Should still work but use default values
        assert response.status_code == 200

class TestAPIHealthAndDocs:
    """Test API health and documentation endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Real Estate Empire" in data["message"]
        assert "version" in data
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_docs_endpoint(self):
        """Test API documentation endpoint"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

# Cleanup
def teardown_module():
    """Clean up test database"""
    Base.metadata.drop_all(bind=engine)