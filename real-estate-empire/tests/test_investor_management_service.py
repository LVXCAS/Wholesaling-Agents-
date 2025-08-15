"""
Unit tests for the investor management service.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4, UUID
from unittest.mock import Mock, patch

from app.models.investor import (
    InvestorProfile, InvestmentHistory, InvestorCommunication,
    InvestorPerformanceMetrics, DealInvestorMatch, InvestorDealPresentation,
    InvestorSearchCriteria, InvestorAnalytics, InvestorTypeEnum,
    InvestorStatusEnum, InvestmentPreferenceEnum, RiskToleranceEnum,
    CommunicationPreferenceEnum
)
from app.services.investor_management_service import InvestorManagementService


class TestInvestorManagementService:
    """Test cases for InvestorManagementService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mocked dependencies"""
        return InvestorManagementService(db=mock_db)
    
    @pytest.fixture
    def sample_investor_data(self):
        """Sample investor data for testing"""
        return {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
            "company": "Doe Investments",
            "title": "Managing Partner",
            "investor_type": InvestorTypeEnum.INDIVIDUAL,
            "investment_preferences": [InvestmentPreferenceEnum.RESIDENTIAL],
            "risk_tolerance": RiskToleranceEnum.MODERATE,
            "min_investment": Decimal("50000"),
            "max_investment": Decimal("500000"),
            "preferred_markets": ["Austin", "Dallas"],
            "communication_preferences": [CommunicationPreferenceEnum.EMAIL],
            "net_worth": Decimal("2000000"),
            "liquid_capital": Decimal("800000"),
            "annual_income": Decimal("300000"),
            "source": "referral",
            "notes": "High-quality investor with strong track record",
            "tags": ["high-value", "residential-focus"]
        }
    
    @pytest.fixture
    def sample_deal_data(self):
        """Sample deal data for testing"""
        return {
            "property_type": "residential",
            "investment_required": Decimal("200000"),
            "market": "Austin",
            "city": "Austin",
            "state": "TX",
            "risk_level": "moderate",
            "distressed": False,
            "expected_return": Decimal("0.15")
        }
    
    # Investor Profile Management Tests
    
    def test_create_investor_profile_success(self, service, sample_investor_data):
        """Test successful investor profile creation"""
        investor = service.create_investor_profile(sample_investor_data)
        
        assert isinstance(investor, InvestorProfile)
        assert investor.first_name == "John"
        assert investor.last_name == "Doe"
        assert investor.email == "john.doe@example.com"
        assert investor.investor_type == InvestorTypeEnum.INDIVIDUAL
        assert investor.status == InvestorStatusEnum.PROSPECT
        assert investor.full_name == "John Doe"
    
    def test_create_investor_profile_validation_error(self, service):
        """Test investor profile creation with invalid data"""
        invalid_data = {
            "first_name": "",  # Empty name should fail
            "email": "invalid-email"  # Invalid email format
        }
        
        with pytest.raises(Exception):
            service.create_investor_profile(invalid_data)
    
    def test_update_investor_profile_success(self, service):
        """Test successful investor profile update"""
        investor_id = uuid4()
        updates = {
            "status": InvestorStatusEnum.ACTIVE,
            "notes": "Updated notes"
        }
        
        updated_investor = service.update_investor_profile(investor_id, updates)
        
        assert isinstance(updated_investor, InvestorProfile)
        assert updated_investor.id == investor_id
    
    def test_get_investor_profile(self, service):
        """Test retrieving investor profile by ID"""
        investor_id = uuid4()
        
        # Since this is a mock implementation, it returns None
        investor = service.get_investor_profile(investor_id)
        assert investor is None
    
    def test_search_investors(self, service):
        """Test searching investors with criteria"""
        criteria = InvestorSearchCriteria(
            investor_types=[InvestorTypeEnum.INDIVIDUAL],
            statuses=[InvestorStatusEnum.ACTIVE],
            min_investment_capacity=Decimal("100000")
        )
        
        investors = service.search_investors(criteria)
        assert isinstance(investors, list)
    
    def test_get_all_investors(self, service):
        """Test retrieving all investors"""
        investors = service.get_all_investors(
            status=InvestorStatusEnum.ACTIVE,
            limit=50,
            offset=0
        )
        
        assert isinstance(investors, list)
    
    # Deal-Investor Matching Tests
    
    def test_match_investors_to_deal(self, service, sample_deal_data):
        """Test matching investors to a deal"""
        deal_id = uuid4()
        
        # Mock the get_all_investors method to return sample investors
        sample_investor = InvestorProfile(
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            investor_type=InvestorTypeEnum.INDIVIDUAL,
            status=InvestorStatusEnum.ACTIVE,
            investment_preferences=[InvestmentPreferenceEnum.RESIDENTIAL],
            risk_tolerance=RiskToleranceEnum.MODERATE,
            min_investment=Decimal("50000"),
            max_investment=Decimal("300000"),
            preferred_markets=["Austin"],
            liquid_capital=Decimal("500000")
        )
        
        with patch.object(service, 'get_all_investors', return_value=[sample_investor]):
            matches = service.match_investors_to_deal(deal_id, sample_deal_data)
        
        assert isinstance(matches, list)
        if matches:  # If there are matches
            match = matches[0]
            assert isinstance(match, DealInvestorMatch)
            assert match.deal_id == deal_id
            assert match.investor_id == sample_investor.id
            assert 0 <= match.match_score <= 1
    
    def test_calculate_investor_match_score(self, service, sample_deal_data):
        """Test calculating match score between investor and deal"""
        investor = InvestorProfile(
            first_name="Test",
            last_name="Investor",
            email="test@example.com",
            investor_type=InvestorTypeEnum.INDIVIDUAL,
            investment_preferences=[InvestmentPreferenceEnum.RESIDENTIAL],
            risk_tolerance=RiskToleranceEnum.MODERATE,
            min_investment=Decimal("50000"),
            max_investment=Decimal("300000"),
            preferred_markets=["Austin"],
            liquid_capital=Decimal("500000"),
            status=InvestorStatusEnum.ACTIVE
        )
        
        score, reasons = service._calculate_investor_match_score(investor, sample_deal_data)
        
        assert isinstance(score, float)
        assert 0 <= score <= 1
        assert isinstance(reasons, list)
    
    def test_check_investment_preferences_match(self, service, sample_deal_data):
        """Test checking investment preferences match"""
        investor = InvestorProfile(
            first_name="Test",
            last_name="Investor",
            email="test@example.com",
            investor_type=InvestorTypeEnum.INDIVIDUAL,
            investment_preferences=[InvestmentPreferenceEnum.RESIDENTIAL]
        )
        
        matches = service._check_investment_preferences_match(investor, sample_deal_data)
        
        assert isinstance(matches, dict)
        assert InvestmentPreferenceEnum.RESIDENTIAL in matches
    
    def test_check_financial_capacity_match(self, service, sample_deal_data):
        """Test checking financial capacity match"""
        investor = InvestorProfile(
            first_name="Test",
            last_name="Investor",
            email="test@example.com",
            investor_type=InvestorTypeEnum.INDIVIDUAL,
            min_investment=Decimal("50000"),
            max_investment=Decimal("300000"),
            liquid_capital=Decimal("500000")
        )
        
        match = service._check_financial_capacity_match(investor, sample_deal_data)
        assert isinstance(match, bool)
        assert match is True  # Deal amount (200k) is within range
    
    def test_check_geographic_match(self, service, sample_deal_data):
        """Test checking geographic preference match"""
        investor = InvestorProfile(
            first_name="Test",
            last_name="Investor",
            email="test@example.com",
            investor_type=InvestorTypeEnum.INDIVIDUAL,
            preferred_markets=["Austin", "Dallas"]
        )
        
        match = service._check_geographic_match(investor, sample_deal_data)
        assert isinstance(match, bool)
        assert match is True  # Deal is in Austin
    
    def test_check_risk_match(self, service, sample_deal_data):
        """Test checking risk tolerance match"""
        investor = InvestorProfile(
            first_name="Test",
            last_name="Investor",
            email="test@example.com",
            investor_type=InvestorTypeEnum.INDIVIDUAL,
            risk_tolerance=RiskToleranceEnum.MODERATE
        )
        
        match = service._check_risk_match(investor, sample_deal_data)
        assert isinstance(match, bool)
        assert match is True  # Deal risk is moderate
    
    # Communication Management Tests
    
    def test_log_communication(self, service):
        """Test logging communication with investor"""
        communication_data = {
            "investor_id": uuid4(),
            "communication_type": CommunicationPreferenceEnum.EMAIL,
            "subject": "New Investment Opportunity",
            "content": "We have a great new deal for you...",
            "direction": "outbound"
        }
        
        communication = service.log_communication(communication_data)
        
        assert isinstance(communication, InvestorCommunication)
        assert communication.subject == "New Investment Opportunity"
        assert communication.direction == "outbound"
    
    def test_get_investor_communications(self, service):
        """Test retrieving investor communications"""
        investor_id = uuid4()
        
        communications = service.get_investor_communications(investor_id, limit=25)
        
        assert isinstance(communications, list)
    
    def test_schedule_follow_up(self, service):
        """Test scheduling follow-up with investor"""
        investor_id = uuid4()
        follow_up_date = datetime.utcnow() + timedelta(days=7)
        
        success = service.schedule_follow_up(investor_id, follow_up_date, "Follow up on deal")
        
        assert success is True
    
    def test_get_pending_follow_ups(self, service):
        """Test retrieving pending follow-ups"""
        follow_ups = service.get_pending_follow_ups(days_ahead=7)
        
        assert isinstance(follow_ups, list)
    
    # Performance Tracking Tests
    
    def test_calculate_investor_performance(self, service):
        """Test calculating investor performance metrics"""
        investor_id = uuid4()
        
        metrics = service.calculate_investor_performance(investor_id)
        
        assert isinstance(metrics, InvestorPerformanceMetrics)
        assert metrics.investor_id == investor_id
    
    def test_get_top_performing_investors(self, service):
        """Test retrieving top performing investors"""
        top_investors = service.get_top_performing_investors(limit=5)
        
        assert isinstance(top_investors, list)
    
    def test_generate_investor_analytics(self, service):
        """Test generating investor analytics"""
        analytics = service.generate_investor_analytics()
        
        assert isinstance(analytics, InvestorAnalytics)
        assert hasattr(analytics, 'total_investors')
        assert hasattr(analytics, 'active_investors')
        assert hasattr(analytics, 'total_invested_capital')
    
    # Investment History Management Tests
    
    def test_record_investment(self, service):
        """Test recording a new investment"""
        investment_data = {
            "investor_id": uuid4(),
            "deal_id": uuid4(),
            "investment_amount": Decimal("150000"),
            "investment_date": datetime.utcnow(),
            "expected_return": Decimal("0.12"),
            "status": "active"
        }
        
        investment = service.record_investment(investment_data)
        
        assert isinstance(investment, InvestmentHistory)
        assert investment.investment_amount == Decimal("150000")
        assert investment.status == "active"
    
    def test_get_investor_investment_history(self, service):
        """Test retrieving investor investment history"""
        investor_id = uuid4()
        
        history = service.get_investor_investment_history(investor_id)
        
        assert isinstance(history, list)
    
    def test_update_investment_performance(self, service):
        """Test updating investment performance"""
        investment_id = uuid4()
        actual_return = Decimal("0.15")
        
        success = service.update_investment_performance(investment_id, actual_return)
        
        assert success is True
    
    # Deal Presentation Management Tests
    
    def test_create_deal_presentation(self, service):
        """Test creating deal presentation record"""
        presentation_data = {
            "investor_id": uuid4(),
            "deal_id": uuid4(),
            "presentation_type": "email"
        }
        
        presentation = service.create_deal_presentation(presentation_data)
        
        assert isinstance(presentation, InvestorDealPresentation)
        assert presentation.presentation_type == "email"
    
    def test_track_presentation_engagement(self, service):
        """Test tracking presentation engagement"""
        presentation_id = uuid4()
        
        success = service.track_presentation_engagement(presentation_id, "opened")
        
        assert success is True
    
    def test_get_presentation_analytics(self, service):
        """Test getting presentation analytics"""
        analytics = service.get_presentation_analytics()
        
        assert isinstance(analytics, dict)
        assert 'total_presentations' in analytics
        assert 'open_rate' in analytics
        assert 'response_rate' in analytics
    
    # Edge Cases and Error Handling Tests
    
    def test_create_investor_with_invalid_email(self, service):
        """Test creating investor with invalid email"""
        invalid_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "invalid-email",
            "investor_type": InvestorTypeEnum.INDIVIDUAL
        }
        
        with pytest.raises(Exception):
            service.create_investor_profile(invalid_data)
    
    def test_match_investors_with_no_active_investors(self, service, sample_deal_data):
        """Test matching when no active investors exist"""
        deal_id = uuid4()
        
        with patch.object(service, 'get_all_investors', return_value=[]):
            matches = service.match_investors_to_deal(deal_id, sample_deal_data)
        
        assert matches == []
    
    def test_financial_capacity_mismatch(self, service):
        """Test financial capacity mismatch scenarios"""
        investor = InvestorProfile(
            first_name="Test",
            last_name="Investor",
            email="test@example.com",
            investor_type=InvestorTypeEnum.INDIVIDUAL,
            max_investment=Decimal("100000")  # Less than deal requirement
        )
        
        deal_data = {"investment_required": Decimal("200000")}
        
        match = service._check_financial_capacity_match(investor, deal_data)
        assert match is False
    
    def test_geographic_mismatch(self, service):
        """Test geographic preference mismatch"""
        investor = InvestorProfile(
            first_name="Test",
            last_name="Investor",
            email="test@example.com",
            investor_type=InvestorTypeEnum.INDIVIDUAL,
            preferred_markets=["New York", "Los Angeles"]
        )
        
        deal_data = {
            "market": "Austin",
            "city": "Austin",
            "state": "TX"
        }
        
        match = service._check_geographic_match(investor, deal_data)
        assert match is False
    
    def test_risk_tolerance_mismatch(self, service):
        """Test risk tolerance mismatch"""
        investor = InvestorProfile(
            first_name="Test",
            last_name="Investor",
            email="test@example.com",
            investor_type=InvestorTypeEnum.INDIVIDUAL,
            risk_tolerance=RiskToleranceEnum.CONSERVATIVE
        )
        
        deal_data = {"risk_level": "high"}
        
        match = service._check_risk_match(investor, deal_data)
        assert match is False


# Integration-style tests that test multiple components together

class TestInvestorManagementIntegration:
    """Integration tests for investor management workflows"""
    
    @pytest.fixture
    def service(self):
        """Create service instance for integration tests"""
        return InvestorManagementService(db=Mock())
    
    def test_complete_investor_onboarding_workflow(self, service):
        """Test complete investor onboarding workflow"""
        # Create investor
        investor_data = {
            "first_name": "Alice",
            "last_name": "Johnson",
            "email": "alice@example.com",
            "investor_type": InvestorTypeEnum.INDIVIDUAL,
            "investment_preferences": [InvestmentPreferenceEnum.RESIDENTIAL],
            "risk_tolerance": RiskToleranceEnum.MODERATE,
            "min_investment": Decimal("100000"),
            "max_investment": Decimal("500000")
        }
        
        investor = service.create_investor_profile(investor_data)
        assert investor.status == InvestorStatusEnum.PROSPECT
        
        # Log initial communication
        communication_data = {
            "investor_id": investor.id,
            "communication_type": CommunicationPreferenceEnum.EMAIL,
            "subject": "Welcome to our platform",
            "content": "Thank you for your interest...",
            "direction": "outbound"
        }
        
        communication = service.log_communication(communication_data)
        assert communication.investor_id == investor.id
        
        # Schedule follow-up
        follow_up_date = datetime.utcnow() + timedelta(days=3)
        success = service.schedule_follow_up(investor.id, follow_up_date)
        assert success is True
    
    def test_deal_matching_and_presentation_workflow(self, service):
        """Test deal matching and presentation workflow"""
        # Create a sample investor
        investor = InvestorProfile(
            first_name="Bob",
            last_name="Wilson",
            email="bob@example.com",
            investor_type=InvestorTypeEnum.INDIVIDUAL,
            status=InvestorStatusEnum.ACTIVE,
            investment_preferences=[InvestmentPreferenceEnum.RESIDENTIAL],
            risk_tolerance=RiskToleranceEnum.MODERATE,
            min_investment=Decimal("150000"),
            max_investment=Decimal("400000"),
            preferred_markets=["Dallas"],
            liquid_capital=Decimal("600000")
        )
        
        # Mock deal data
        deal_id = uuid4()
        deal_data = {
            "property_type": "residential",
            "investment_required": Decimal("250000"),
            "market": "Dallas",
            "city": "Dallas",
            "state": "TX",
            "risk_level": "moderate"
        }
        
        # Mock the get_all_investors method
        with patch.object(service, 'get_all_investors', return_value=[investor]):
            matches = service.match_investors_to_deal(deal_id, deal_data)
        
        assert len(matches) > 0
        match = matches[0]
        assert match.investor_id == investor.id
        
        # Create presentation
        presentation_data = {
            "investor_id": investor.id,
            "deal_id": deal_id,
            "presentation_type": "email"
        }
        
        presentation = service.create_deal_presentation(presentation_data)
        assert presentation.investor_id == investor.id
        assert presentation.deal_id == deal_id
    
    def test_investment_tracking_workflow(self, service):
        """Test investment tracking workflow"""
        investor_id = uuid4()
        deal_id = uuid4()
        
        # Record investment
        investment_data = {
            "investor_id": investor_id,
            "deal_id": deal_id,
            "investment_amount": Decimal("200000"),
            "investment_date": datetime.utcnow(),
            "expected_return": Decimal("0.15"),
            "status": "active"
        }
        
        investment = service.record_investment(investment_data)
        assert investment.investor_id == investor_id
        
        # Calculate performance metrics
        metrics = service.calculate_investor_performance(investor_id)
        assert metrics.investor_id == investor_id
        
        # Update investment performance
        actual_return = Decimal("0.18")
        success = service.update_investment_performance(investment.id, actual_return)
        assert success is True