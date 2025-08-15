"""
Integration tests for funding source management workflows.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4, UUID
from unittest.mock import Mock, patch

from app.models.funding import (
    FundingSource, LoanProduct, FundingApplication, FundingSourceMatch,
    FundingSourcePerformance, FundingSearchCriteria, FundingAnalytics,
    FundingSourceTypeEnum, LoanTypeEnum, PropertyTypeEnum,
    FundingStatusEnum, ApplicationStatusEnum
)
from app.services.funding_source_service import FundingSourceService


class TestFundingSourceIntegration:
    """Integration tests for funding source management workflows"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mocked dependencies"""
        return FundingSourceService(db=mock_db)
    
    @pytest.fixture
    def sample_funding_source_data(self):
        """Sample funding source data for testing"""
        return {
            "name": "First National Bank",
            "funding_type": FundingSourceTypeEnum.BANK,
            "contact_name": "John Smith",
            "email": "john.smith@firstnational.com",
            "phone": "+1-555-123-4567",
            "website": "https://firstnational.com",
            "min_loan_amount": Decimal("50000"),
            "max_loan_amount": Decimal("2000000"),
            "min_credit_score": 620,
            "max_ltv": Decimal("0.85"),
            "states_covered": ["TX", "CA", "FL"],
            "loan_types": [LoanTypeEnum.CONVENTIONAL, LoanTypeEnum.JUMBO],
            "property_types": [PropertyTypeEnum.SINGLE_FAMILY, PropertyTypeEnum.CONDO],
            "typical_rate_range_min": Decimal("0.045"),
            "typical_rate_range_max": Decimal("0.065"),
            "typical_processing_days": 30,
            "notes": "Excellent relationship, fast processing",
            "tags": ["preferred", "fast-processing"]
        }
    
    @pytest.fixture
    def sample_loan_product_data(self):
        """Sample loan product data for testing"""
        return {
            "funding_source_id": uuid4(),
            "name": "Conventional 30-Year Fixed",
            "loan_type": LoanTypeEnum.CONVENTIONAL,
            "property_types": [PropertyTypeEnum.SINGLE_FAMILY],
            "min_amount": Decimal("100000"),
            "max_amount": Decimal("1500000"),
            "min_term_months": 360,
            "max_term_months": 360,
            "base_rate": Decimal("0.055"),
            "origination_fee": Decimal("0.01"),
            "min_credit_score": 640,
            "max_ltv": Decimal("0.8"),
            "typical_processing_days": 25
        }
    
    @pytest.fixture
    def sample_deal_data(self):
        """Sample deal data for testing"""
        return {
            "loan_amount": Decimal("300000"),
            "loan_type": "conventional",
            "property_type": "single_family",
            "property_value": Decimal("400000"),
            "state": "TX",
            "credit_score": 720,
            "ltv": Decimal("0.75")
        }
    
    def test_complete_funding_source_lifecycle(self, service, sample_funding_source_data):
        """Test complete funding source management lifecycle"""
        # Create funding source
        funding_source = service.create_funding_source(sample_funding_source_data)
        assert isinstance(funding_source, FundingSource)
        assert funding_source.name == "First National Bank"
        assert funding_source.funding_type == FundingSourceTypeEnum.BANK
        assert funding_source.status == FundingStatusEnum.ACTIVE
        
        # Update funding source
        updates = {
            "status": FundingStatusEnum.ACTIVE,
            "notes": "Updated relationship notes",
            "typical_processing_days": 25
        }
        updated_source = service.update_funding_source(funding_source.id, updates)
        assert isinstance(updated_source, FundingSource)
        
        # Calculate performance metrics
        performance = service.calculate_source_performance(funding_source.id)
        assert isinstance(performance, FundingSourcePerformance)
        assert performance.funding_source_id == funding_source.id
    
    def test_loan_product_management_workflow(self, service, sample_loan_product_data):
        """Test loan product creation and management"""
        # Create loan product
        loan_product = service.create_loan_product(sample_loan_product_data)
        assert isinstance(loan_product, LoanProduct)
        assert loan_product.name == "Conventional 30-Year Fixed"
        assert loan_product.loan_type == LoanTypeEnum.CONVENTIONAL
        
        # Update loan product
        updates = {
            "base_rate": Decimal("0.052"),
            "typical_processing_days": 20
        }
        updated_product = service.update_loan_product(loan_product.id, updates)
        assert isinstance(updated_product, LoanProduct)
        
        # Get loan products for funding source
        products = service.get_loan_products(loan_product.funding_source_id)
        assert isinstance(products, list)
    
    def test_deal_funding_matching_workflow(self, service, sample_deal_data):
        """Test deal to funding source matching workflow"""
        # Create sample funding sources
        bank_source = FundingSource(
            name="Test Bank",
            funding_type=FundingSourceTypeEnum.BANK,
            status=FundingStatusEnum.ACTIVE,
            min_loan_amount=Decimal("100000"),
            max_loan_amount=Decimal("1000000"),
            min_credit_score=650,
            max_ltv=Decimal("0.8"),
            states_covered=["TX"],
            loan_types=[LoanTypeEnum.CONVENTIONAL],
            property_types=[PropertyTypeEnum.SINGLE_FAMILY],
            typical_rate_range_min=Decimal("0.05"),
            typical_rate_range_max=Decimal("0.07")
        )
        
        hard_money_source = FundingSource(
            name="Hard Money Lender",
            funding_type=FundingSourceTypeEnum.HARD_MONEY,
            status=FundingStatusEnum.ACTIVE,
            min_loan_amount=Decimal("50000"),
            max_loan_amount=Decimal("2000000"),
            min_credit_score=600,
            max_ltv=Decimal("0.7"),
            states_covered=["TX", "CA"],
            loan_types=[LoanTypeEnum.HARD_MONEY],
            property_types=[PropertyTypeEnum.SINGLE_FAMILY],
            typical_rate_range_min=Decimal("0.08"),
            typical_rate_range_max=Decimal("0.12")
        )
        
        # Mock the get_all_funding_sources method
        with patch.object(service, 'get_all_funding_sources', 
                         return_value=[bank_source, hard_money_source]):
            
            deal_id = uuid4()
            matches = service.match_funding_sources_to_deal(deal_id, sample_deal_data)
        
        assert isinstance(matches, list)
        if matches:  # If there are matches
            match = matches[0]
            assert isinstance(match, FundingSourceMatch)
            assert match.deal_id == deal_id
            assert 0 <= match.match_score <= 1
    
    def test_funding_application_workflow(self, service):
        """Test funding application creation and management"""
        # Create funding application
        application_data = {
            "funding_source_id": uuid4(),
            "deal_id": uuid4(),
            "loan_amount": Decimal("250000"),
            "loan_type": LoanTypeEnum.CONVENTIONAL,
            "property_type": PropertyTypeEnum.SINGLE_FAMILY,
            "property_address": "123 Main St, Austin, TX",
            "property_value": Decimal("350000"),
            "borrower_name": "Jane Doe",
            "borrower_email": "jane@example.com",
            "credit_score": 740,
            "annual_income": Decimal("80000")
        }
        
        application = service.create_funding_application(application_data)
        assert isinstance(application, FundingApplication)
        assert application.loan_amount == Decimal("250000")
        assert application.status == ApplicationStatusEnum.DRAFT
        
        # Update application status
        success = service.update_application_status(
            application.id, 
            ApplicationStatusEnum.SUBMITTED,
            "Application submitted for review"
        )
        assert success is True
        
        # Get applications by deal
        applications = service.get_applications_by_deal(application.deal_id)
        assert isinstance(applications, list)
        
        # Get pending applications
        pending = service.get_pending_applications()
        assert isinstance(pending, list)
    
    def test_loan_product_comparison_workflow(self, service, sample_deal_data):
        """Test loan product comparison functionality"""
        # Create sample loan products
        product1 = LoanProduct(
            funding_source_id=uuid4(),
            name="Bank Product A",
            loan_type=LoanTypeEnum.CONVENTIONAL,
            property_types=[PropertyTypeEnum.SINGLE_FAMILY],
            min_amount=Decimal("100000"),
            max_amount=Decimal("1000000"),
            min_term_months=360,
            max_term_months=360,
            base_rate=Decimal("0.055"),
            origination_fee=Decimal("0.01")
        )
        
        product2 = LoanProduct(
            funding_source_id=uuid4(),
            name="Bank Product B",
            loan_type=LoanTypeEnum.CONVENTIONAL,
            property_types=[PropertyTypeEnum.SINGLE_FAMILY],
            min_amount=Decimal("150000"),
            max_amount=Decimal("2000000"),
            min_term_months=360,
            max_term_months=360,
            base_rate=Decimal("0.052"),
            origination_fee=Decimal("0.005")
        )
        
        # Mock the service methods
        with patch.object(service, 'get_all_funding_sources', return_value=[]):
            with patch.object(service, 'get_loan_products', return_value=[product1, product2]):
                comparisons = service.compare_loan_products(sample_deal_data)
        
        assert isinstance(comparisons, list)
    
    def test_funding_source_search_and_filtering(self, service):
        """Test funding source search functionality"""
        # Test search with criteria
        criteria = FundingSearchCriteria(
            funding_types=[FundingSourceTypeEnum.BANK],
            loan_types=[LoanTypeEnum.CONVENTIONAL],
            states=["TX"],
            min_loan_amount=Decimal("100000"),
            max_rate=Decimal("0.07")
        )
        
        sources = service.search_funding_sources(criteria)
        assert isinstance(sources, list)
        
        # Test get all sources with filtering
        all_sources = service.get_all_funding_sources(
            status=FundingStatusEnum.ACTIVE,
            limit=50
        )
        assert isinstance(all_sources, list)
    
    def test_funding_analytics_generation(self, service):
        """Test funding analytics generation"""
        analytics = service.generate_funding_analytics()
        
        assert isinstance(analytics, FundingAnalytics)
        assert hasattr(analytics, 'total_funding_sources')
        assert hasattr(analytics, 'total_applications')
        assert hasattr(analytics, 'overall_approval_rate')
        assert hasattr(analytics, 'funding_type_distribution')
    
    def test_relationship_management_workflow(self, service):
        """Test funding source relationship management"""
        source_id = uuid4()
        
        # Update relationship contact
        contact_date = datetime.utcnow()
        success = service.update_relationship_contact(
            source_id, 
            contact_date, 
            "Discussed new loan products"
        )
        assert success is True
        
        # Get relationship reminders
        reminders = service.get_relationship_reminders(days_ahead=30)
        assert isinstance(reminders, list)
    
    def test_funding_source_matching_algorithms(self, service):
        """Test funding source matching algorithm accuracy"""
        # Create a funding source with specific criteria
        source = FundingSource(
            name="Selective Lender",
            funding_type=FundingSourceTypeEnum.PORTFOLIO_LENDER,
            min_loan_amount=Decimal("200000"),
            max_loan_amount=Decimal("800000"),
            min_credit_score=700,
            max_ltv=Decimal("0.75"),
            states_covered=["TX"],
            loan_types=[LoanTypeEnum.PORTFOLIO],
            property_types=[PropertyTypeEnum.SINGLE_FAMILY],
            typical_rate_range_min=Decimal("0.06"),
            typical_rate_range_max=Decimal("0.08")
        )
        
        # Test matching deal that should match
        matching_deal = {
            "loan_amount": Decimal("400000"),
            "loan_type": "portfolio",
            "property_type": "single_family",
            "state": "TX",
            "credit_score": 750,
            "ltv": Decimal("0.7")
        }
        
        score, reasons = service._calculate_funding_match_score(source, matching_deal)
        assert score > 0.5  # Should be a good match
        assert len(reasons) > 0
        
        # Test deal that should not match
        non_matching_deal = {
            "loan_amount": Decimal("100000"),  # Below minimum
            "loan_type": "conventional",
            "property_type": "commercial",
            "state": "NY",  # Not covered
            "credit_score": 600,  # Below minimum
            "ltv": Decimal("0.9")  # Above maximum
        }
        
        score, reasons = service._calculate_funding_match_score(source, non_matching_deal)
        assert score < 0.3  # Should be a poor match
    
    def test_loan_product_rate_estimation(self, service):
        """Test loan product rate estimation accuracy"""
        product = LoanProduct(
            funding_source_id=uuid4(),
            name="Test Product",
            loan_type=LoanTypeEnum.CONVENTIONAL,
            property_types=[PropertyTypeEnum.SINGLE_FAMILY],
            min_amount=Decimal("100000"),
            max_amount=Decimal("1000000"),
            min_term_months=360,
            max_term_months=360,
            base_rate=Decimal("0.055"),
            rate_adjustments={
                "high_ltv": Decimal("0.0025"),
                "low_credit": Decimal("0.005")
            }
        )
        
        # Test rate estimation for good borrower
        good_deal = {
            "credit_score": 780,
            "ltv": Decimal("0.7")
        }
        
        rate = service._estimate_product_rate(product, good_deal)
        assert rate == Decimal("0.055")  # Base rate, no adjustments
        
        # Test rate estimation for higher risk borrower
        risky_deal = {
            "credit_score": 620,
            "ltv": Decimal("0.85")
        }
        
        rate = service._estimate_product_rate(product, risky_deal)
        assert rate > Decimal("0.055")  # Should have adjustments
    
    def test_performance_metrics_calculation(self, service):
        """Test funding source performance metrics calculation"""
        source_id = uuid4()
        
        # Calculate performance metrics
        performance = service.calculate_source_performance(source_id)
        
        assert isinstance(performance, FundingSourcePerformance)
        assert performance.funding_source_id == source_id
        assert hasattr(performance, 'approval_rate')
        assert hasattr(performance, 'average_processing_days')
        assert hasattr(performance, 'total_amount_funded')
        
        # Get top performing sources
        top_sources = service.get_top_performing_sources(limit=5)
        assert isinstance(top_sources, list)
    
    def test_error_handling_and_edge_cases(self, service):
        """Test error handling and edge cases"""
        # Test with invalid funding source data
        invalid_data = {
            "name": "",  # Empty name should fail
            "funding_type": "invalid_type"
        }
        
        with pytest.raises(Exception):
            service.create_funding_source(invalid_data)
        
        # Test matching with no active sources
        with patch.object(service, 'get_all_funding_sources', return_value=[]):
            matches = service.match_funding_sources_to_deal(uuid4(), {})
            assert matches == []
        
        # Test loan amount validation
        source = FundingSource(
            name="Test Source",
            funding_type=FundingSourceTypeEnum.BANK,
            min_loan_amount=Decimal("500000"),
            max_loan_amount=Decimal("1000000")
        )
        
        # Deal below minimum
        low_deal = {"loan_amount": Decimal("300000")}
        assert not service._check_loan_amount_match(source, low_deal)
        
        # Deal above maximum
        high_deal = {"loan_amount": Decimal("1500000")}
        assert not service._check_loan_amount_match(source, high_deal)
        
        # Deal within range
        good_deal = {"loan_amount": Decimal("750000")}
        assert service._check_loan_amount_match(source, good_deal)


class TestFundingSourceServiceUnit:
    """Unit tests for individual FundingSourceService methods"""
    
    @pytest.fixture
    def service(self):
        """Create service instance for unit tests"""
        return FundingSourceService(db=Mock())
    
    def test_check_credit_score_match(self, service):
        """Test credit score matching logic"""
        source = FundingSource(
            name="Test",
            funding_type=FundingSourceTypeEnum.BANK,
            min_credit_score=680
        )
        
        # Good credit score
        good_deal = {"credit_score": 720}
        assert service._check_credit_score_match(source, good_deal)
        
        # Poor credit score
        poor_deal = {"credit_score": 620}
        assert not service._check_credit_score_match(source, poor_deal)
        
        # No requirement
        no_req_source = FundingSource(
            name="Test",
            funding_type=FundingSourceTypeEnum.BANK
        )
        assert service._check_credit_score_match(no_req_source, poor_deal)
    
    def test_check_ltv_match(self, service):
        """Test LTV matching logic"""
        source = FundingSource(
            name="Test",
            funding_type=FundingSourceTypeEnum.BANK,
            max_ltv=Decimal("0.8")
        )
        
        # Good LTV
        good_deal = {"ltv": Decimal("0.75")}
        assert service._check_ltv_match(source, good_deal)
        
        # High LTV
        high_deal = {"ltv": Decimal("0.9")}
        assert not service._check_ltv_match(source, high_deal)
    
    def test_check_geographic_match(self, service):
        """Test geographic matching logic"""
        # Nationwide lender
        nationwide_source = FundingSource(
            name="Test",
            funding_type=FundingSourceTypeEnum.BANK,
            nationwide=True
        )
        
        deal = {"state": "CA"}
        assert service._check_geographic_match(nationwide_source, deal)
        
        # State-specific lender
        state_source = FundingSource(
            name="Test",
            funding_type=FundingSourceTypeEnum.BANK,
            states_covered=["TX", "FL"]
        )
        
        # Covered state
        tx_deal = {"state": "TX"}
        assert service._check_geographic_match(state_source, tx_deal)
        
        # Non-covered state
        ca_deal = {"state": "CA"}
        assert not service._check_geographic_match(state_source, ca_deal)
    
    def test_check_property_type_match(self, service):
        """Test property type matching logic"""
        source = FundingSource(
            name="Test",
            funding_type=FundingSourceTypeEnum.BANK,
            property_types=[PropertyTypeEnum.SINGLE_FAMILY, PropertyTypeEnum.CONDO]
        )
        
        # Supported type
        sf_deal = {"property_type": "single_family"}
        assert service._check_property_type_match(source, sf_deal)
        
        # Unsupported type
        commercial_deal = {"property_type": "commercial"}
        assert not service._check_property_type_match(source, commercial_deal)
        
        # No restrictions
        no_restriction_source = FundingSource(
            name="Test",
            funding_type=FundingSourceTypeEnum.BANK
        )
        assert service._check_property_type_match(no_restriction_source, commercial_deal)
    
    def test_estimate_rate_calculation(self, service):
        """Test interest rate estimation"""
        source = FundingSource(
            name="Test",
            funding_type=FundingSourceTypeEnum.BANK,
            typical_rate_range_min=Decimal("0.05"),
            typical_rate_range_max=Decimal("0.07")
        )
        
        # Base case
        base_deal = {"credit_score": 700, "ltv": Decimal("0.8")}
        rate = service._estimate_rate(source, base_deal)
        assert rate == Decimal("0.06")  # Average of range
        
        # High credit score
        good_deal = {"credit_score": 780, "ltv": Decimal("0.75")}
        good_rate = service._estimate_rate(source, good_deal)
        assert good_rate < Decimal("0.06")
        
        # Low credit score and high LTV
        risky_deal = {"credit_score": 620, "ltv": Decimal("0.9")}
        risky_rate = service._estimate_rate(source, risky_deal)
        assert risky_rate > Decimal("0.06")