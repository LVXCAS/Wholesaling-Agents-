"""
Integration tests for Lead Management API
Tests the API endpoints with minimal mocking
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.routers import lead_management
from app.models.lead import (
    LeadStatusEnum, LeadSourceEnum, ContactMethodEnum,
    PropertyLeadDB, CommunicationDB
)


@pytest.fixture
def test_app():
    """Create test FastAPI app with lead management router."""
    app = FastAPI()
    app.include_router(lead_management.router)
    return app


@pytest.fixture
def client(test_app):
    """Create test client with mocked database."""
    
    # Mock database session
    mock_db = Mock()
    
    # Mock database dependency
    def mock_get_db():
        return mock_db
    
    # Override dependency
    from app.core.database import get_db
    test_app.dependency_overrides[get_db] = mock_get_db
    
    return TestClient(test_app), mock_db


@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing."""
    return {
        "property_id": str(uuid.uuid4()),
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


class TestLeadCRUDIntegration:
    """Test CRUD operations integration."""
    
    def test_create_lead_endpoint(self, client, sample_lead_data):
        """Test lead creation endpoint."""
        test_client, mock_db = client
        
        # Mock database operations
        mock_lead = PropertyLeadDB(
            id=uuid.uuid4(),
            **sample_lead_data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            contact_attempts=0
        )
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Mock the created lead to be returned
        with patch('app.api.routers.lead_management.PropertyLeadDB') as mock_lead_class:
            mock_lead_class.return_value = mock_lead
            
            response = test_client.post("/api/v1/leads/", json=sample_lead_data)
            
            # Verify response
            assert response.status_code == 201
            
            # Verify database operations were called
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()
    
    def test_get_lead_endpoint(self, client):
        """Test lead retrieval endpoint."""
        test_client, mock_db = client
        
        lead_id = uuid.uuid4()
        mock_lead = PropertyLeadDB(
            id=lead_id,
            property_id=uuid.uuid4(),
            status=LeadStatusEnum.NEW,
            source=LeadSourceEnum.MLS,
            owner_name="John Doe",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            contact_attempts=0,
            do_not_call=False,
            do_not_email=False,
            do_not_text=False,
            behind_on_payments=False,
            repair_needed=False
        )
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_lead
        mock_db.query.return_value = mock_query
        
        response = test_client.get(f"/api/v1/leads/{lead_id}")
        
        # Verify response
        assert response.status_code == 200
        
        # Verify database query was called
        mock_db.query.assert_called_once()
    
    def test_get_lead_not_found(self, client):
        """Test lead retrieval with non-existent ID."""
        test_client, mock_db = client
        
        lead_id = uuid.uuid4()
        
        # Mock database query to return None
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        response = test_client.get(f"/api/v1/leads/{lead_id}")
        
        # Verify 404 response
        assert response.status_code == 404
        assert "Lead not found" in response.json()["detail"]
    
    def test_update_lead_endpoint(self, client):
        """Test lead update endpoint."""
        test_client, mock_db = client
        
        lead_id = uuid.uuid4()
        mock_lead = PropertyLeadDB(
            id=lead_id,
            property_id=uuid.uuid4(),
            status=LeadStatusEnum.NEW,
            source=LeadSourceEnum.MLS,
            owner_name="John Doe",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            contact_attempts=0,
            do_not_call=False,
            do_not_email=False,
            do_not_text=False,
            behind_on_payments=False,
            repair_needed=False
        )
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_lead
        mock_db.query.return_value = mock_query
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        update_data = {
            "owner_name": "Jane Doe",
            "lead_score": 90.0
        }
        
        response = test_client.put(f"/api/v1/leads/{lead_id}", json=update_data)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify database operations
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_delete_lead_endpoint(self, client):
        """Test lead deletion endpoint."""
        test_client, mock_db = client
        
        lead_id = uuid.uuid4()
        mock_lead = PropertyLeadDB(
            id=lead_id,
            property_id=uuid.uuid4(),
            status=LeadStatusEnum.NEW,
            source=LeadSourceEnum.MLS,
            owner_name="John Doe",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            contact_attempts=0,
            do_not_call=False,
            do_not_email=False,
            do_not_text=False,
            behind_on_payments=False,
            repair_needed=False
        )
        
        # Mock database queries
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_lead
        mock_query.filter.return_value.delete.return_value = None
        mock_db.query.return_value = mock_query
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None
        
        response = test_client.delete(f"/api/v1/leads/{lead_id}")
        
        # Verify response
        assert response.status_code == 200
        assert "Lead deleted successfully" in response.json()["message"]
        
        # Verify database operations
        mock_db.delete.assert_called_once_with(mock_lead)
        mock_db.commit.assert_called_once()


class TestLeadListingIntegration:
    """Test lead listing and filtering integration."""
    
    def test_list_leads_basic(self, client):
        """Test basic lead listing."""
        test_client, mock_db = client
        
        # Mock database query
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        mock_query.order_by.return_value = mock_query
        mock_db.query.return_value = mock_query
        
        response = test_client.get("/api/v1/leads/")
        
        # Verify response
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
        # Verify database query
        mock_db.query.assert_called_once()
    
    def test_list_leads_with_filters(self, client):
        """Test lead listing with filters."""
        test_client, mock_db = client
        
        # Mock database query with filters
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        response = test_client.get(
            f"/api/v1/leads/?status={LeadStatusEnum.NEW}&source={LeadSourceEnum.MLS}&min_score=80"
        )
        
        # Verify response
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
        # Verify filters were applied (multiple filter calls)
        assert mock_query.filter.call_count >= 3


class TestLeadStatusManagementIntegration:
    """Test lead status management integration."""
    
    def test_update_lead_status(self, client):
        """Test lead status update."""
        test_client, mock_db = client
        
        lead_id = uuid.uuid4()
        mock_lead = PropertyLeadDB(
            id=lead_id,
            property_id=uuid.uuid4(),
            status=LeadStatusEnum.NEW,
            source=LeadSourceEnum.MLS,
            owner_name="John Doe",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            contact_attempts=0,
            first_contact_date=None,
            last_contact_date=None,
            do_not_call=False,
            do_not_email=False,
            do_not_text=False,
            behind_on_payments=False,
            repair_needed=False
        )
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_lead
        mock_db.query.return_value = mock_query
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        response = test_client.patch(
            f"/api/v1/leads/{lead_id}/status",
            params={"new_status": LeadStatusEnum.CONTACTED}
        )
        
        # Verify response
        assert response.status_code == 200
        
        # Verify database operations
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_assign_lead(self, client):
        """Test lead assignment."""
        test_client, mock_db = client
        
        lead_id = uuid.uuid4()
        mock_lead = PropertyLeadDB(
            id=lead_id,
            property_id=uuid.uuid4(),
            status=LeadStatusEnum.NEW,
            source=LeadSourceEnum.MLS,
            owner_name="John Doe",
            assigned_to="agent_001",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            contact_attempts=0,
            do_not_call=False,
            do_not_email=False,
            do_not_text=False,
            behind_on_payments=False,
            repair_needed=False
        )
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_lead
        mock_db.query.return_value = mock_query
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        response = test_client.patch(
            f"/api/v1/leads/{lead_id}/assign",
            params={"assigned_to": "agent_002"}
        )
        
        # Verify response
        assert response.status_code == 200
        
        # Verify database operations
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()


class TestCommunicationIntegration:
    """Test communication management integration."""
    
    def test_create_communication(self, client):
        """Test communication creation."""
        test_client, mock_db = client
        
        lead_id = uuid.uuid4()
        mock_lead = PropertyLeadDB(
            id=lead_id,
            property_id=uuid.uuid4(),
            status=LeadStatusEnum.NEW,
            source=LeadSourceEnum.MLS,
            owner_name="John Doe",
            contact_attempts=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            do_not_call=False,
            do_not_email=False,
            do_not_text=False,
            behind_on_payments=False,
            repair_needed=False
        )
        
        mock_communication = CommunicationDB(
            id=uuid.uuid4(),
            lead_id=lead_id,
            channel="email",
            direction="outbound",
            subject="Test Subject",
            content="Test Content",
            status="sent",
            created_at=datetime.utcnow()
        )
        
        # Mock database queries
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_lead
        mock_db.query.return_value = mock_query
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        communication_data = {
            "lead_id": str(lead_id),
            "channel": "email",
            "direction": "outbound",
            "subject": "Test Subject",
            "content": "Test Content",
            "status": "sent"
        }
        
        with patch('app.api.routers.lead_management.CommunicationDB') as mock_comm_class:
            mock_comm_class.return_value = mock_communication
            
            response = test_client.post(
                f"/api/v1/leads/{lead_id}/communications",
                json=communication_data
            )
            
            # Verify response
            assert response.status_code == 201
            
            # Verify database operations
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()
    
    def test_get_lead_communications(self, client):
        """Test retrieving lead communications."""
        test_client, mock_db = client
        
        lead_id = uuid.uuid4()
        mock_lead = PropertyLeadDB(
            id=lead_id,
            property_id=uuid.uuid4(),
            status=LeadStatusEnum.NEW,
            source=LeadSourceEnum.MLS,
            owner_name="John Doe",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            contact_attempts=0,
            do_not_call=False,
            do_not_email=False,
            do_not_text=False,
            behind_on_payments=False,
            repair_needed=False
        )
        
        # Mock database queries
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_lead
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        response = test_client.get(f"/api/v1/leads/{lead_id}/communications")
        
        # Verify response
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
        # Verify database queries
        assert mock_db.query.call_count >= 2  # One for lead check, one for communications


class TestLeadStatsIntegration:
    """Test lead statistics integration."""
    
    def test_get_lead_stats(self, client):
        """Test lead statistics retrieval."""
        test_client, mock_db = client
        
        # Mock database queries for statistics
        mock_query = Mock()
        mock_query.count.return_value = 100
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value.group_by.return_value.all.return_value = [
            (LeadStatusEnum.NEW, 50),
            (LeadStatusEnum.CONTACTED, 30),
            (LeadStatusEnum.QUALIFIED, 20)
        ]
        mock_query.with_entities.return_value.scalar.return_value = 85.5
        mock_db.query.return_value = mock_query
        
        response = test_client.get("/api/v1/leads/stats/summary")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "summary" in data
        assert "status_distribution" in data
        assert "source_distribution" in data
        assert "conversion_funnel" in data
        
        # Verify summary fields
        summary = data["summary"]
        assert "total_leads" in summary
        assert "new_leads_last_30_days" in summary
        assert "average_lead_score" in summary
        assert "contact_rate" in summary
        assert "qualification_rate" in summary
        assert "close_rate" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])