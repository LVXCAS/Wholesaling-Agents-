"""
Unit tests for Lead Management API functionality
Tests the API logic without database dependencies
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException

from app.models.lead import (
    PropertyLeadCreate, PropertyLeadUpdate, PropertyLeadResponse,
    CommunicationCreate, CommunicationResponse,
    PropertyLeadDB, CommunicationDB,
    LeadStatusEnum, LeadSourceEnum, ContactMethodEnum
)


class TestLeadManagementLogic:
    """Test the business logic of lead management operations."""
    
    @pytest.fixture
    def sample_property_id(self):
        """Sample property ID for testing."""
        return uuid.uuid4()
    
    @pytest.fixture
    def sample_lead_data(self, sample_property_id):
        """Sample lead data for testing."""
        return PropertyLeadCreate(
            property_id=sample_property_id,
            status=LeadStatusEnum.NEW,
            source=LeadSourceEnum.MLS,
            source_url="https://mls.example.com/property/123",
            lead_score=85.5,
            owner_name="John Doe",
            owner_email="john.doe@example.com",
            owner_phone="+1-555-123-4567",
            owner_address="123 Main St",
            owner_city="Anytown",
            owner_state="CA",
            owner_zip="12345",
            preferred_contact_method=ContactMethodEnum.EMAIL,
            best_contact_time="morning",
            do_not_call=False,
            do_not_email=False,
            do_not_text=False,
            motivation_score=75.0,
            motivation_factors=["financial_distress", "relocation"],
            urgency_level="high",
            asking_price=250000.0,
            mortgage_balance=180000.0,
            equity_estimate=70000.0,
            monthly_payment=1200.0,
            behind_on_payments=False,
            condition_notes="Needs minor repairs",
            repair_needed=True,
            estimated_repair_cost=15000.0,
            notes="Motivated seller, quick close preferred",
            tags=["hot_lead", "cash_buyer_preferred"],
            assigned_to="agent_001"
        )
    
    @pytest.fixture
    def sample_lead_db(self, sample_property_id):
        """Sample lead database object for testing."""
        lead_id = uuid.uuid4()
        return PropertyLeadDB(
            id=lead_id,
            property_id=sample_property_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            status=LeadStatusEnum.NEW,
            source=LeadSourceEnum.MLS,
            source_url="https://mls.example.com/property/123",
            lead_score=85.5,
            owner_name="John Doe",
            owner_email="john.doe@example.com",
            owner_phone="+1-555-123-4567",
            owner_address="123 Main St",
            owner_city="Anytown",
            owner_state="CA",
            owner_zip="12345",
            preferred_contact_method=ContactMethodEnum.EMAIL,
            best_contact_time="morning",
            do_not_call=False,
            do_not_email=False,
            do_not_text=False,
            motivation_score=75.0,
            motivation_factors=["financial_distress", "relocation"],
            urgency_level="high",
            asking_price=250000.0,
            mortgage_balance=180000.0,
            equity_estimate=70000.0,
            monthly_payment=1200.0,
            behind_on_payments=False,
            condition_notes="Needs minor repairs",
            repair_needed=True,
            estimated_repair_cost=15000.0,
            first_contact_date=None,
            last_contact_date=None,
            next_follow_up_date=None,
            contact_attempts=0,
            notes="Motivated seller, quick close preferred",
            tags=["hot_lead", "cash_buyer_preferred"],
            assigned_to="agent_001"
        )
    
    def test_lead_create_data_validation(self, sample_lead_data):
        """Test that lead creation data is properly validated."""
        # Test valid data
        assert sample_lead_data.property_id is not None
        assert sample_lead_data.source == LeadSourceEnum.MLS
        assert sample_lead_data.status == LeadStatusEnum.NEW
        assert 0 <= sample_lead_data.lead_score <= 100
        assert 0 <= sample_lead_data.motivation_score <= 100
        
        # Test invalid lead score
        with pytest.raises(ValueError):
            PropertyLeadCreate(
                property_id=sample_lead_data.property_id,
                source=LeadSourceEnum.MLS,
                lead_score=150.0  # Invalid: > 100
            )
    
    def test_lead_update_data_validation(self):
        """Test that lead update data is properly validated."""
        # Test valid update
        update_data = PropertyLeadUpdate(
            owner_name="Jane Doe",
            lead_score=90.0,
            status=LeadStatusEnum.CONTACTED
        )
        
        assert update_data.owner_name == "Jane Doe"
        assert update_data.lead_score == 90.0
        assert update_data.status == LeadStatusEnum.CONTACTED
        
        # Test invalid score in update
        with pytest.raises(ValueError):
            PropertyLeadUpdate(lead_score=-10.0)  # Invalid: < 0
    
    def test_lead_response_model(self, sample_lead_db):
        """Test that lead response model properly serializes data."""
        response = PropertyLeadResponse.model_validate(sample_lead_db)
        
        assert response.id == sample_lead_db.id
        assert response.owner_name == "John Doe"
        assert response.status == LeadStatusEnum.NEW
        assert response.lead_score == 85.5
        assert response.contact_attempts == 0
    
    def test_communication_create_validation(self):
        """Test communication creation data validation."""
        lead_id = uuid.uuid4()
        
        # Test valid communication
        comm_data = CommunicationCreate(
            lead_id=lead_id,
            channel="email",
            direction="outbound",
            subject="Investment Opportunity",
            content="Hi John, I'm interested in your property...",
            status="sent",
            sent_at=datetime.utcnow()
        )
        
        assert comm_data.lead_id == lead_id
        assert comm_data.channel == "email"
        assert comm_data.direction == "outbound"
        assert comm_data.status == "sent"
    
    def test_lead_status_transitions(self):
        """Test valid lead status transitions."""
        # Test all valid status values
        valid_statuses = [
            LeadStatusEnum.NEW,
            LeadStatusEnum.CONTACTED,
            LeadStatusEnum.INTERESTED,
            LeadStatusEnum.NOT_INTERESTED,
            LeadStatusEnum.QUALIFIED,
            LeadStatusEnum.UNDER_CONTRACT,
            LeadStatusEnum.CLOSED,
            LeadStatusEnum.DEAD
        ]
        
        for status in valid_statuses:
            update_data = PropertyLeadUpdate(status=status)
            assert update_data.status == status
    
    def test_lead_source_validation(self):
        """Test lead source validation."""
        valid_sources = [
            LeadSourceEnum.MLS,
            LeadSourceEnum.PUBLIC_RECORDS,
            LeadSourceEnum.FORECLOSURE,
            LeadSourceEnum.FSBO,
            LeadSourceEnum.EXPIRED_LISTING,
            LeadSourceEnum.ABSENTEE_OWNER,
            LeadSourceEnum.HIGH_EQUITY,
            LeadSourceEnum.DISTRESSED,
            LeadSourceEnum.REFERRAL,
            LeadSourceEnum.MARKETING,
            LeadSourceEnum.COLD_CALL,
            LeadSourceEnum.DIRECT_MAIL,
            LeadSourceEnum.OTHER
        ]
        
        for source in valid_sources:
            lead_data = PropertyLeadCreate(
                property_id=uuid.uuid4(),
                source=source
            )
            assert lead_data.source == source
    
    def test_contact_method_validation(self):
        """Test contact method validation."""
        valid_methods = [
            ContactMethodEnum.EMAIL,
            ContactMethodEnum.PHONE,
            ContactMethodEnum.TEXT,
            ContactMethodEnum.MAIL
        ]
        
        for method in valid_methods:
            lead_data = PropertyLeadCreate(
                property_id=uuid.uuid4(),
                source=LeadSourceEnum.MLS,
                preferred_contact_method=method
            )
            assert lead_data.preferred_contact_method == method
    
    def test_lead_scoring_logic(self):
        """Test lead scoring validation and logic."""
        # Test valid scores
        valid_scores = [0.0, 25.5, 50.0, 75.5, 100.0]
        
        for score in valid_scores:
            lead_data = PropertyLeadCreate(
                property_id=uuid.uuid4(),
                source=LeadSourceEnum.MLS,
                lead_score=score,
                motivation_score=score
            )
            assert lead_data.lead_score == score
            assert lead_data.motivation_score == score
    
    def test_financial_data_validation(self):
        """Test financial data validation."""
        lead_data = PropertyLeadCreate(
            property_id=uuid.uuid4(),
            source=LeadSourceEnum.MLS,
            asking_price=250000.0,
            mortgage_balance=180000.0,
            equity_estimate=70000.0,
            monthly_payment=1200.0,
            estimated_repair_cost=15000.0
        )
        
        assert lead_data.asking_price == 250000.0
        assert lead_data.mortgage_balance == 180000.0
        assert lead_data.equity_estimate == 70000.0
        assert lead_data.monthly_payment == 1200.0
        assert lead_data.estimated_repair_cost == 15000.0
        
        # Test that equity roughly equals asking price minus mortgage
        calculated_equity = lead_data.asking_price - lead_data.mortgage_balance
        assert abs(calculated_equity - lead_data.equity_estimate) <= 1.0  # Allow small rounding differences
    
    def test_contact_preferences_validation(self):
        """Test contact preferences validation."""
        lead_data = PropertyLeadCreate(
            property_id=uuid.uuid4(),
            source=LeadSourceEnum.MLS,
            do_not_call=True,
            do_not_email=False,
            do_not_text=True,
            best_contact_time="evening"
        )
        
        assert lead_data.do_not_call is True
        assert lead_data.do_not_email is False
        assert lead_data.do_not_text is True
        assert lead_data.best_contact_time == "evening"
    
    def test_motivation_factors_validation(self):
        """Test motivation factors validation."""
        motivation_factors = [
            "financial_distress",
            "relocation",
            "divorce",
            "inheritance",
            "downsizing",
            "job_loss",
            "medical_bills"
        ]
        
        lead_data = PropertyLeadCreate(
            property_id=uuid.uuid4(),
            source=LeadSourceEnum.MLS,
            motivation_factors=motivation_factors,
            urgency_level="high"
        )
        
        assert lead_data.motivation_factors == motivation_factors
        assert lead_data.urgency_level == "high"
    
    def test_tags_and_notes_validation(self):
        """Test tags and notes validation."""
        tags = ["hot_lead", "cash_buyer_preferred", "quick_close"]
        notes = "Seller is motivated due to job relocation. Prefers cash offers."
        
        lead_data = PropertyLeadCreate(
            property_id=uuid.uuid4(),
            source=LeadSourceEnum.MLS,
            tags=tags,
            notes=notes,
            assigned_to="agent_001"
        )
        
        assert lead_data.tags == tags
        assert lead_data.notes == notes
        assert lead_data.assigned_to == "agent_001"


class TestLeadManagementBusinessLogic:
    """Test business logic for lead management operations."""
    
    def test_lead_contact_tracking_logic(self):
        """Test logic for tracking lead contacts."""
        # Simulate status change from NEW to CONTACTED
        lead = PropertyLeadDB(
            id=uuid.uuid4(),
            property_id=uuid.uuid4(),
            status=LeadStatusEnum.NEW,
            contact_attempts=0,
            first_contact_date=None,
            last_contact_date=None
        )
        
        # Simulate first contact
        now = datetime.utcnow()
        lead.status = LeadStatusEnum.CONTACTED
        lead.first_contact_date = now
        lead.last_contact_date = now
        lead.contact_attempts = 1
        
        assert lead.status == LeadStatusEnum.CONTACTED
        assert lead.first_contact_date is not None
        assert lead.last_contact_date is not None
        assert lead.contact_attempts == 1
    
    def test_lead_scoring_business_rules(self):
        """Test business rules for lead scoring."""
        # High-value lead characteristics
        high_value_lead = PropertyLeadCreate(
            property_id=uuid.uuid4(),
            source=LeadSourceEnum.FORECLOSURE,  # Distressed property
            motivation_score=90.0,  # Highly motivated
            urgency_level="high",
            equity_estimate=100000.0,  # High equity
            behind_on_payments=True,  # Financial distress
            motivation_factors=["financial_distress", "foreclosure"]
        )
        
        # This lead should score high due to multiple positive factors
        assert high_value_lead.motivation_score >= 80.0
        assert high_value_lead.urgency_level == "high"
        assert high_value_lead.behind_on_payments is True
        
        # Low-value lead characteristics
        low_value_lead = PropertyLeadCreate(
            property_id=uuid.uuid4(),
            source=LeadSourceEnum.MLS,  # Regular listing
            motivation_score=20.0,  # Low motivation
            urgency_level="low",
            equity_estimate=5000.0,  # Low equity
            behind_on_payments=False
        )
        
        assert low_value_lead.motivation_score <= 30.0
        assert low_value_lead.urgency_level == "low"
        assert low_value_lead.behind_on_payments is False
    
    def test_communication_tracking_logic(self):
        """Test logic for tracking communications."""
        lead_id = uuid.uuid4()
        
        # Create initial communication
        comm = CommunicationDB(
            id=uuid.uuid4(),
            lead_id=lead_id,
            channel="email",
            direction="outbound",
            status="sent",
            sent_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        assert comm.lead_id == lead_id
        assert comm.channel == "email"
        assert comm.direction == "outbound"
        assert comm.status == "sent"
        assert comm.sent_at is not None
    
    def test_lead_assignment_logic(self):
        """Test logic for lead assignment."""
        lead = PropertyLeadDB(
            id=uuid.uuid4(),
            property_id=uuid.uuid4(),
            assigned_to=None,
            updated_at=datetime.utcnow()
        )
        
        # Assign lead to agent
        old_updated_at = lead.updated_at
        lead.assigned_to = "agent_002"
        lead.updated_at = datetime.utcnow()
        
        assert lead.assigned_to == "agent_002"
        assert lead.updated_at > old_updated_at
    
    def test_lead_filtering_logic(self):
        """Test logic for lead filtering and search."""
        # Create sample leads with different characteristics
        leads = [
            PropertyLeadDB(
                id=uuid.uuid4(),
                property_id=uuid.uuid4(),
                status=LeadStatusEnum.NEW,
                source=LeadSourceEnum.MLS,
                lead_score=85.0,
                owner_name="John Doe",
                assigned_to="agent_001"
            ),
            PropertyLeadDB(
                id=uuid.uuid4(),
                property_id=uuid.uuid4(),
                status=LeadStatusEnum.CONTACTED,
                source=LeadSourceEnum.FORECLOSURE,
                lead_score=92.0,
                owner_name="Jane Smith",
                assigned_to="agent_002"
            ),
            PropertyLeadDB(
                id=uuid.uuid4(),
                property_id=uuid.uuid4(),
                status=LeadStatusEnum.QUALIFIED,
                source=LeadSourceEnum.FSBO,
                lead_score=78.0,
                owner_name="Bob Johnson",
                assigned_to="agent_001"
            )
        ]
        
        # Test status filtering
        new_leads = [lead for lead in leads if lead.status == LeadStatusEnum.NEW]
        assert len(new_leads) == 1
        assert new_leads[0].owner_name == "John Doe"
        
        # Test source filtering
        foreclosure_leads = [lead for lead in leads if lead.source == LeadSourceEnum.FORECLOSURE]
        assert len(foreclosure_leads) == 1
        assert foreclosure_leads[0].owner_name == "Jane Smith"
        
        # Test score range filtering
        high_score_leads = [lead for lead in leads if lead.lead_score >= 85.0]
        assert len(high_score_leads) == 2
        
        # Test assignment filtering
        agent_001_leads = [lead for lead in leads if lead.assigned_to == "agent_001"]
        assert len(agent_001_leads) == 2
    
    def test_lead_statistics_calculation(self):
        """Test logic for calculating lead statistics."""
        # Sample leads for statistics
        leads = [
            PropertyLeadDB(status=LeadStatusEnum.NEW, lead_score=85.0, created_at=datetime.utcnow()),
            PropertyLeadDB(status=LeadStatusEnum.CONTACTED, lead_score=90.0, created_at=datetime.utcnow()),
            PropertyLeadDB(status=LeadStatusEnum.QUALIFIED, lead_score=95.0, created_at=datetime.utcnow()),
            PropertyLeadDB(status=LeadStatusEnum.CLOSED, lead_score=88.0, created_at=datetime.utcnow()),
            PropertyLeadDB(status=LeadStatusEnum.DEAD, lead_score=60.0, created_at=datetime.utcnow())
        ]
        
        # Calculate statistics
        total_leads = len(leads)
        avg_score = sum(lead.lead_score for lead in leads) / total_leads
        contacted_leads = len([lead for lead in leads if lead.status in [
            LeadStatusEnum.CONTACTED, LeadStatusEnum.QUALIFIED, LeadStatusEnum.CLOSED
        ]])
        qualified_leads = len([lead for lead in leads if lead.status in [
            LeadStatusEnum.QUALIFIED, LeadStatusEnum.CLOSED
        ]])
        closed_leads = len([lead for lead in leads if lead.status == LeadStatusEnum.CLOSED])
        
        # Test calculations
        assert total_leads == 5
        assert avg_score == 83.6  # (85+90+95+88+60)/5
        assert contacted_leads == 3
        assert qualified_leads == 2
        assert closed_leads == 1
        
        # Calculate conversion rates
        contact_rate = (contacted_leads / total_leads) * 100
        qualification_rate = (qualified_leads / contacted_leads) * 100 if contacted_leads > 0 else 0
        close_rate = (closed_leads / qualified_leads) * 100 if qualified_leads > 0 else 0
        
        assert contact_rate == 60.0  # 3/5 * 100
        assert round(qualification_rate, 2) == 66.67  # 2/3 * 100 (rounded)
        assert close_rate == 50.0  # 1/2 * 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])