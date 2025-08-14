"""
Tests for Lead Management API endpoints
"""

import pytest
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from app.models.lead import (
    PropertyLeadDB, CommunicationDB,
    LeadStatusEnum, LeadSourceEnum, ContactMethodEnum
)


@pytest.fixture
def client():
    """Create test client with mocked database."""
    from fastapi import FastAPI
    from app.api.routers.lead_management import router
    
    # Create a test app with just the lead management router
    test_app = FastAPI()
    test_app.include_router(router)
    
    # Mock the database dependency
    def mock_get_db():
        return Mock(spec=Session)
    
    test_app.dependency_overrides[get_db] = mock_get_db
    
    return TestClient(test_app)


@pytest.fixture
def db_session():
    """Create test database session."""
    return Mock(spec=Session)


@pytest.fixture
def sample_property_id():
    """Sample property ID for testing."""
    return uuid.uuid4()


@pytest.fixture
def sample_lead_data(sample_property_id):
    """Sample lead data for testing."""
    return {
        "property_id": str(sample_property_id),
        "status": LeadStatusEnum.NEW,
        "source": LeadSourceEnum.MLS,
        "source_url": "https://mls.example.com/property/123",
        "lead_score": 85.5,
        "owner_name": "John Doe",
        "owner_email": "john.doe@example.com",
        "owner_phone": "+1-555-123-4567",
        "owner_address": "123 Main St",
        "owner_city": "Anytown",
        "owner_state": "CA",
        "owner_zip": "12345",
        "preferred_contact_method": ContactMethodEnum.EMAIL,
        "best_contact_time": "morning",
        "do_not_call": False,
        "do_not_email": False,
        "do_not_text": False,
        "motivation_score": 75.0,
        "motivation_factors": ["financial_distress", "relocation"],
        "urgency_level": "high",
        "asking_price": 250000.0,
        "mortgage_balance": 180000.0,
        "equity_estimate": 70000.0,
        "monthly_payment": 1200.0,
        "behind_on_payments": False,
        "condition_notes": "Needs minor repairs",
        "repair_needed": True,
        "estimated_repair_cost": 15000.0,
        "notes": "Motivated seller, quick close preferred",
        "tags": ["hot_lead", "cash_buyer_preferred"],
        "assigned_to": "agent_001"
    }


@pytest.fixture
def sample_communication_data():
    """Sample communication data for testing."""
    return {
        "channel": "email",
        "direction": "outbound",
        "subject": "Investment Opportunity for Your Property",
        "content": "Hi John, I'm interested in purchasing your property...",
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat()
    }


class TestLeadCRUD:
    """Test CRUD operations for leads."""
    
    def test_create_lead_success(self, client, sample_lead_data):
        """Test successful lead creation."""
        response = client.post("/api/v1/leads/", json=sample_lead_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["owner_name"] == "John Doe"
        assert data["status"] == LeadStatusEnum.NEW
        assert data["lead_score"] == 85.5
        assert "id" in data
        assert "created_at" in data
    
    def test_create_lead_invalid_data(self, client):
        """Test lead creation with invalid data."""
        invalid_data = {
            "property_id": "invalid-uuid",
            "source": "invalid_source"
        }
        
        response = client.post("/api/v1/leads/", json=invalid_data)
        assert response.status_code == 422
    
    def test_get_lead_success(self, client, sample_lead_data):
        """Test successful lead retrieval."""
        # First create a lead
        create_response = client.post("/api/v1/leads/", json=sample_lead_data)
        lead_id = create_response.json()["id"]
        
        # Then retrieve it
        response = client.get(f"/api/v1/leads/{lead_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == lead_id
        assert data["owner_name"] == "John Doe"
    
    def test_get_lead_not_found(self, client):
        """Test lead retrieval with non-existent ID."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/leads/{fake_id}")
        
        assert response.status_code == 404
        assert "Lead not found" in response.json()["detail"]
    
    def test_update_lead_success(self, client, sample_lead_data):
        """Test successful lead update."""
        # First create a lead
        create_response = client.post("/api/v1/leads/", json=sample_lead_data)
        lead_id = create_response.json()["id"]
        
        # Update the lead
        update_data = {
            "owner_name": "Jane Doe",
            "lead_score": 90.0,
            "notes": "Updated notes"
        }
        
        response = client.put(f"/api/v1/leads/{lead_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["owner_name"] == "Jane Doe"
        assert data["lead_score"] == 90.0
        assert data["notes"] == "Updated notes"
    
    def test_delete_lead_success(self, client, sample_lead_data):
        """Test successful lead deletion."""
        # First create a lead
        create_response = client.post("/api/v1/leads/", json=sample_lead_data)
        lead_id = create_response.json()["id"]
        
        # Delete the lead
        response = client.delete(f"/api/v1/leads/{lead_id}")
        
        assert response.status_code == 200
        assert "Lead deleted successfully" in response.json()["message"]
        
        # Verify it's deleted
        get_response = client.get(f"/api/v1/leads/{lead_id}")
        assert get_response.status_code == 404


class TestLeadFiltering:
    """Test lead filtering and sorting functionality."""
    
    def test_list_leads_basic(self, client):
        """Test basic lead listing."""
        response = client.get("/api/v1/leads/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_leads_with_pagination(self, client):
        """Test lead listing with pagination."""
        response = client.get("/api/v1/leads/?skip=0&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
    
    def test_list_leads_with_status_filter(self, client):
        """Test lead listing with status filter."""
        response = client.get(f"/api/v1/leads/?status={LeadStatusEnum.NEW}")
        
        assert response.status_code == 200
        data = response.json()
        for lead in data:
            assert lead["status"] == LeadStatusEnum.NEW
    
    def test_list_leads_with_source_filter(self, client):
        """Test lead listing with source filter."""
        response = client.get(f"/api/v1/leads/?source={LeadSourceEnum.MLS}")
        
        assert response.status_code == 200
        data = response.json()
        for lead in data:
            assert lead["source"] == LeadSourceEnum.MLS
    
    def test_list_leads_with_score_range(self, client):
        """Test lead listing with score range filter."""
        response = client.get("/api/v1/leads/?min_score=80&max_score=95")
        
        assert response.status_code == 200
        data = response.json()
        for lead in data:
            if lead["lead_score"] is not None:
                assert 80 <= lead["lead_score"] <= 95
    
    def test_list_leads_with_search(self, client):
        """Test lead listing with search."""
        response = client.get("/api/v1/leads/?search=john")
        
        assert response.status_code == 200
        data = response.json()
        # Results should contain "john" in name, email, phone, or notes
        assert isinstance(data, list)
    
    def test_list_leads_with_sorting(self, client):
        """Test lead listing with sorting."""
        response = client.get("/api/v1/leads/?sort_by=lead_score&sort_order=desc")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify sorting (scores should be in descending order)
        scores = [lead["lead_score"] for lead in data if lead["lead_score"] is not None]
        assert scores == sorted(scores, reverse=True)


class TestLeadStatusManagement:
    """Test lead status update functionality."""
    
    def test_update_lead_status_success(self, client, sample_lead_data):
        """Test successful lead status update."""
        # Create a lead
        create_response = client.post("/api/v1/leads/", json=sample_lead_data)
        lead_id = create_response.json()["id"]
        
        # Update status
        response = client.patch(
            f"/api/v1/leads/{lead_id}/status",
            params={"new_status": LeadStatusEnum.CONTACTED}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == LeadStatusEnum.CONTACTED
        assert data["first_contact_date"] is not None
        assert data["last_contact_date"] is not None
    
    def test_update_lead_status_not_found(self, client):
        """Test status update for non-existent lead."""
        fake_id = str(uuid.uuid4())
        response = client.patch(
            f"/api/v1/leads/{fake_id}/status",
            params={"new_status": LeadStatusEnum.CONTACTED}
        )
        
        assert response.status_code == 404


class TestLeadAssignment:
    """Test lead assignment functionality."""
    
    def test_assign_lead_success(self, client, sample_lead_data):
        """Test successful lead assignment."""
        # Create a lead
        create_response = client.post("/api/v1/leads/", json=sample_lead_data)
        lead_id = create_response.json()["id"]
        
        # Assign lead
        response = client.patch(
            f"/api/v1/leads/{lead_id}/assign",
            params={"assigned_to": "agent_002"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["assigned_to"] == "agent_002"
    
    def test_assign_lead_not_found(self, client):
        """Test assignment for non-existent lead."""
        fake_id = str(uuid.uuid4())
        response = client.patch(
            f"/api/v1/leads/{fake_id}/assign",
            params={"assigned_to": "agent_002"}
        )
        
        assert response.status_code == 404


class TestCommunications:
    """Test communication management functionality."""
    
    def test_create_communication_success(self, client, sample_lead_data, sample_communication_data):
        """Test successful communication creation."""
        # Create a lead
        create_response = client.post("/api/v1/leads/", json=sample_lead_data)
        lead_id = create_response.json()["id"]
        
        # Create communication
        response = client.post(
            f"/api/v1/leads/{lead_id}/communications",
            json=sample_communication_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["lead_id"] == lead_id
        assert data["channel"] == "email"
        assert data["direction"] == "outbound"
        assert "id" in data
    
    def test_create_communication_lead_not_found(self, client, sample_communication_data):
        """Test communication creation for non-existent lead."""
        fake_id = str(uuid.uuid4())
        response = client.post(
            f"/api/v1/leads/{fake_id}/communications",
            json=sample_communication_data
        )
        
        assert response.status_code == 404
    
    def test_get_lead_communications(self, client, sample_lead_data, sample_communication_data):
        """Test retrieving lead communications."""
        # Create a lead
        create_response = client.post("/api/v1/leads/", json=sample_lead_data)
        lead_id = create_response.json()["id"]
        
        # Create communication
        client.post(
            f"/api/v1/leads/{lead_id}/communications",
            json=sample_communication_data
        )
        
        # Get communications
        response = client.get(f"/api/v1/leads/{lead_id}/communications")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["channel"] == "email"
    
    def test_get_communications_with_filters(self, client, sample_lead_data, sample_communication_data):
        """Test retrieving communications with filters."""
        # Create a lead
        create_response = client.post("/api/v1/leads/", json=sample_lead_data)
        lead_id = create_response.json()["id"]
        
        # Create communication
        client.post(
            f"/api/v1/leads/{lead_id}/communications",
            json=sample_communication_data
        )
        
        # Get communications with channel filter
        response = client.get(
            f"/api/v1/leads/{lead_id}/communications?channel=email&direction=outbound"
        )
        
        assert response.status_code == 200
        data = response.json()
        for comm in data:
            assert comm["channel"] == "email"
            assert comm["direction"] == "outbound"


class TestLeadStats:
    """Test lead statistics functionality."""
    
    def test_get_lead_stats_basic(self, client):
        """Test basic lead statistics retrieval."""
        response = client.get("/api/v1/leads/stats/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "summary" in data
        assert "status_distribution" in data
        assert "source_distribution" in data
        assert "conversion_funnel" in data
        
        # Check summary fields
        summary = data["summary"]
        assert "total_leads" in summary
        assert "new_leads_last_30_days" in summary
        assert "average_lead_score" in summary
        assert "contact_rate" in summary
        assert "qualification_rate" in summary
        assert "close_rate" in summary
    
    def test_get_lead_stats_with_filters(self, client):
        """Test lead statistics with filters."""
        response = client.get("/api/v1/leads/stats/summary?assigned_to=agent_001&days=7")
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
    
    def test_get_lead_stats_invalid_days(self, client):
        """Test lead statistics with invalid days parameter."""
        response = client.get("/api/v1/leads/stats/summary?days=0")
        
        assert response.status_code == 422  # Validation error


class TestLeadValidation:
    """Test input validation for lead endpoints."""
    
    def test_create_lead_missing_required_fields(self, client):
        """Test lead creation with missing required fields."""
        invalid_data = {
            "owner_name": "John Doe"
            # Missing property_id and source
        }
        
        response = client.post("/api/v1/leads/", json=invalid_data)
        assert response.status_code == 422
    
    def test_create_lead_invalid_enum_values(self, client, sample_property_id):
        """Test lead creation with invalid enum values."""
        invalid_data = {
            "property_id": str(sample_property_id),
            "source": "invalid_source",
            "status": "invalid_status"
        }
        
        response = client.post("/api/v1/leads/", json=invalid_data)
        assert response.status_code == 422
    
    def test_create_lead_invalid_score_range(self, client, sample_property_id):
        """Test lead creation with invalid score values."""
        invalid_data = {
            "property_id": str(sample_property_id),
            "source": LeadSourceEnum.MLS,
            "lead_score": 150.0  # Should be 0-100
        }
        
        response = client.post("/api/v1/leads/", json=invalid_data)
        assert response.status_code == 422
    
    def test_list_leads_invalid_pagination(self, client):
        """Test lead listing with invalid pagination parameters."""
        response = client.get("/api/v1/leads/?skip=-1&limit=0")
        assert response.status_code == 422
    
    def test_list_leads_invalid_sort_order(self, client):
        """Test lead listing with invalid sort order."""
        response = client.get("/api/v1/leads/?sort_order=invalid")
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__])