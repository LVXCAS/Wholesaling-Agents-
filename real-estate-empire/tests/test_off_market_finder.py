"""
Unit tests for Off-market property finder.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.off_market_finder import (
    OffMarketPropertyFinder,
    OffMarketOpportunity,
    OwnerResearch,
    MotivationIndicators,
    PropertyConditionEstimate,
    MotivationLevel,
    PropertyCondition,
    OpportunityType
)


class TestOffMarketPropertyFinder:
    """Test cases for OffMarketPropertyFinder."""

    @pytest.fixture
    def mock_mls_client(self):
        """Mock MLS client."""
        return AsyncMock()

    @pytest.fixture
    def mock_public_records_client(self):
        """Mock public records client."""
        return AsyncMock()

    @pytest.fixture
    def mock_foreclosure_client(self):
        """Mock foreclosure client."""
        return AsyncMock()

    @pytest.fixture
    def finder(self, mock_mls_client, mock_public_records_client, mock_foreclosure_client):
        """Create OffMarketPropertyFinder with mocked clients."""
        return OffMarketPropertyFinder(
            mls_client=mock_mls_client,
            public_records_client=mock_public_records_client,
            foreclosure_client=mock_foreclosure_client
        )

    @pytest.fixture
    def sample_public_record(self):
        """Sample public record for testing."""
        owner_info = MagicMock()
        owner_info.name = "John Smith"
        owner_info.mailing_address = "456 Oak Ave, Dallas, TX"
        
        tax_record = MagicMock()
        tax_record.assessed_value = 300000
        tax_record.payment_status = "Current"
        tax_record.due_date = datetime.now() + timedelta(days=30)
        tax_record.last_payment_date = datetime.now() - timedelta(days=30)
        
        record = MagicMock()
        record.record_id = "PR12345"
        record.property_address = "123 Main St, Austin, TX"
        record.state = "TX"
        record.owner_info = owner_info
        record.tax_record = tax_record
        record.raw_data = {"test": "data"}
        
        return record

    @pytest.fixture
    def sample_foreclosure_property(self):
        """Sample foreclosure property for testing."""
        return MagicMock(
            foreclosure_id="FC12345",
            property_address="789 Pine St",
            city="Austin",
            state="TX",
            zip_code="78701",
            estimated_value=250000,
            bedrooms=3,
            bathrooms=2,
            square_feet=1800,
            year_built=2000,
            property_type="Single Family",
            borrower_name="Jane Doe",
            raw_data={"foreclosure": "data"}
        )

    def test_is_absentee_owner_true(self, finder, sample_public_record):
        """Test absentee owner detection - positive case."""
        assert finder._is_absentee_owner(sample_public_record) is True

    def test_is_absentee_owner_false(self, finder):
        """Test absentee owner detection - negative case."""
        record = MagicMock(
            property_address="123 Main St, Austin, TX",
            owner_info=MagicMock(
                mailing_address="123 Main St, Austin, TX"
            )
        )
        assert finder._is_absentee_owner(record) is False

    def test_is_absentee_owner_no_mailing_address(self, finder):
        """Test absentee owner detection with no mailing address."""
        record = MagicMock(
            property_address="123 Main St, Austin, TX",
            owner_info=MagicMock(mailing_address=None)
        )
        assert finder._is_absentee_owner(record) is False

    def test_has_tax_delinquency_by_status(self, finder):
        """Test tax delinquency detection by payment status."""
        record = MagicMock(
            tax_record=MagicMock(
                payment_status="Delinquent",
                due_date=None,
                last_payment_date=None
            )
        )
        assert finder._has_tax_delinquency(record) is True

    def test_has_tax_delinquency_by_due_date(self, finder):
        """Test tax delinquency detection by overdue date."""
        record = MagicMock(
            tax_record=MagicMock(
                payment_status="Pending",
                due_date=datetime.now() - timedelta(days=30),
                last_payment_date=None
            )
        )
        assert finder._has_tax_delinquency(record) is True

    def test_has_tax_delinquency_false(self, finder):
        """Test tax delinquency detection - negative case."""
        record = MagicMock(
            tax_record=MagicMock(
                payment_status="Current",
                due_date=datetime.now() + timedelta(days=30),
                last_payment_date=datetime.now() - timedelta(days=10)
            )
        )
        assert finder._has_tax_delinquency(record) is False

    def test_indicates_vacancy_high_dom(self, finder):
        """Test vacancy detection with high days on market."""
        property_data = MagicMock(days_on_market=200)
        assert finder._indicates_vacancy(property_data) is True

    def test_indicates_vacancy_false(self, finder):
        """Test vacancy detection - negative case."""
        property_data = MagicMock(days_on_market=30)
        assert finder._indicates_vacancy(property_data) is False

    @pytest.mark.asyncio
    async def test_analyze_equity_opportunity(self, finder, sample_public_record):
        """Test equity opportunity analysis."""
        opportunity = await finder._analyze_equity_opportunity(sample_public_record)
        
        assert opportunity is not None
        assert opportunity.opportunity_id.startswith("HE_")
        assert OpportunityType.HIGH_EQUITY in opportunity.opportunity_types
        assert opportunity.estimated_value == 360000  # 300000 * 1.2
        assert abs(opportunity.estimated_equity - 252000) < 1  # 360000 * 0.7 (allow for floating point precision)
        assert opportunity.owner_research is not None
        assert opportunity.owner_research.name == "John Smith"
        assert opportunity.owner_research.is_absentee_owner is True

    @pytest.mark.asyncio
    async def test_analyze_equity_opportunity_low_equity(self, finder):
        """Test equity opportunity analysis with low equity."""
        record = MagicMock(
            record_id="PR12345",
            property_address="123 Main St, Austin, TX",
            state="TX",
            owner_info=None,
            tax_record=MagicMock(assessed_value=50000),  # Low value
            raw_data={}
        )
        
        opportunity = await finder._analyze_equity_opportunity(record)
        assert opportunity is None  # Should be filtered out due to low equity

    @pytest.mark.asyncio
    async def test_create_absentee_opportunity(self, finder, sample_public_record):
        """Test creating absentee owner opportunity."""
        opportunity = await finder._create_absentee_opportunity(sample_public_record)
        
        assert opportunity is not None
        assert opportunity.opportunity_id.startswith("AO_")
        assert OpportunityType.ABSENTEE_OWNER in opportunity.opportunity_types
        assert opportunity.owner_research.is_absentee_owner is True
        assert opportunity.confidence_score == 0.8

    @pytest.mark.asyncio
    async def test_create_tax_delinquent_opportunity(self, finder, sample_public_record):
        """Test creating tax delinquent opportunity."""
        # Modify record to have tax delinquency
        sample_public_record.tax_record.payment_status = "Delinquent"
        
        opportunity = await finder._create_tax_delinquent_opportunity(sample_public_record)
        
        assert opportunity is not None
        assert opportunity.opportunity_id.startswith("TD_")
        assert OpportunityType.TAX_DELINQUENT in opportunity.opportunity_types
        assert opportunity.motivation_indicators.financial_distress is True
        assert opportunity.motivation_indicators.tax_delinquency is True
        assert opportunity.confidence_score == 0.9

    @pytest.mark.asyncio
    async def test_create_vacant_opportunity(self, finder):
        """Test creating vacant property opportunity."""
        property_data = MagicMock(
            mls_id="MLS12345",
            address="123 Main St",
            city="Austin",
            state="TX",
            zip_code="78701",
            price=300000,
            bedrooms=3,
            bathrooms=2,
            square_feet=1800,
            year_built=2000,
            property_type="Single Family",
            raw_data={"mls": "data"}
        )
        
        opportunity = await finder._create_vacant_opportunity(property_data)
        
        assert opportunity is not None
        assert opportunity.opportunity_id.startswith("VP_")
        assert OpportunityType.VACANT_PROPERTY in opportunity.opportunity_types
        assert opportunity.motivation_indicators.vacant_property is True
        assert opportunity.condition_estimate is not None
        assert opportunity.condition_estimate.overall_condition == PropertyCondition.FAIR

    @pytest.mark.asyncio
    async def test_create_distressed_opportunity(self, finder, sample_foreclosure_property):
        """Test creating distressed property opportunity."""
        opportunity = await finder._create_distressed_opportunity(sample_foreclosure_property)
        
        assert opportunity is not None
        assert opportunity.opportunity_id.startswith("DO_")
        assert OpportunityType.DISTRESSED_OWNER in opportunity.opportunity_types
        assert opportunity.motivation_indicators.financial_distress is True
        assert opportunity.confidence_score == 0.95

    def test_deduplicate_opportunities(self, finder):
        """Test opportunity deduplication."""
        # Create duplicate opportunities
        opp1 = OffMarketOpportunity(
            opportunity_id="1",
            property_address="123 Main St",
            city="Austin",
            state="TX",
            zip_code="78701",
            opportunity_types=[OpportunityType.HIGH_EQUITY],
            opportunity_score=0.8,
            confidence_score=0.7,
            discovered_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        opp2 = OffMarketOpportunity(
            opportunity_id="2",
            property_address="123 Main St",
            city="Austin",
            state="TX",
            zip_code="78701",
            opportunity_types=[OpportunityType.ABSENTEE_OWNER],
            opportunity_score=0.7,
            confidence_score=0.8,
            discovered_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        opportunities = [opp1, opp2]
        unique_opportunities = finder._deduplicate_opportunities(opportunities)
        
        assert len(unique_opportunities) == 1
        assert len(unique_opportunities[0].opportunity_types) == 2
        assert OpportunityType.HIGH_EQUITY in unique_opportunities[0].opportunity_types
        assert OpportunityType.ABSENTEE_OWNER in unique_opportunities[0].opportunity_types

    @pytest.mark.asyncio
    async def test_score_opportunities(self, finder):
        """Test opportunity scoring."""
        opportunity = OffMarketOpportunity(
            opportunity_id="1",
            property_address="123 Main St",
            city="Austin",
            state="TX",
            zip_code="78701",
            opportunity_types=[OpportunityType.HIGH_EQUITY, OpportunityType.ABSENTEE_OWNER],
            estimated_value=300000,
            estimated_equity=150000,
            motivation_indicators=MotivationIndicators(motivation_score=0.8),
            condition_estimate=PropertyConditionEstimate(
                overall_condition=PropertyCondition.FAIR,
                condition_score=60.0
            ),
            opportunity_score=0.0,
            confidence_score=0.8,
            discovered_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        opportunities = [opportunity]
        scored_opportunities = await finder._score_opportunities(opportunities)
        
        assert scored_opportunities[0].opportunity_score > 0
        assert scored_opportunities[0].opportunity_score <= 1.0

    def test_filter_opportunities_by_equity(self, finder):
        """Test filtering opportunities by minimum equity."""
        opp1 = OffMarketOpportunity(
            opportunity_id="1",
            property_address="123 Main St",
            city="Austin",
            state="TX",
            zip_code="78701",
            opportunity_types=[OpportunityType.HIGH_EQUITY],
            estimated_equity=100000,
            opportunity_score=0.8,
            confidence_score=0.7,
            discovered_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        opp2 = OffMarketOpportunity(
            opportunity_id="2",
            property_address="456 Oak Ave",
            city="Austin",
            state="TX",
            zip_code="78701",
            opportunity_types=[OpportunityType.HIGH_EQUITY],
            estimated_equity=30000,  # Below threshold
            opportunity_score=0.7,
            confidence_score=0.8,
            discovered_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        opportunities = [opp1, opp2]
        filtered = finder._filter_opportunities(opportunities, min_equity=50000)
        
        assert len(filtered) == 1
        assert filtered[0].opportunity_id == "1"

    def test_filter_opportunities_by_price(self, finder):
        """Test filtering opportunities by maximum price."""
        opp1 = OffMarketOpportunity(
            opportunity_id="1",
            property_address="123 Main St",
            city="Austin",
            state="TX",
            zip_code="78701",
            opportunity_types=[OpportunityType.HIGH_EQUITY],
            estimated_value=250000,
            opportunity_score=0.8,
            confidence_score=0.7,
            discovered_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        opp2 = OffMarketOpportunity(
            opportunity_id="2",
            property_address="456 Oak Ave",
            city="Austin",
            state="TX",
            zip_code="78701",
            opportunity_types=[OpportunityType.HIGH_EQUITY],
            estimated_value=400000,  # Above threshold
            opportunity_score=0.7,
            confidence_score=0.8,
            discovered_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        opportunities = [opp1, opp2]
        filtered = finder._filter_opportunities(opportunities, max_price=300000)
        
        assert len(filtered) == 1
        assert filtered[0].opportunity_id == "1"

    @pytest.mark.asyncio
    async def test_research_owner_contact_info(self, finder):
        """Test owner contact information research."""
        opportunity = OffMarketOpportunity(
            opportunity_id="1",
            property_address="123 Main St",
            city="Austin",
            state="TX",
            zip_code="78701",
            opportunity_types=[OpportunityType.HIGH_EQUITY],
            owner_research=OwnerResearch(name="John Smith"),
            opportunity_score=0.8,
            confidence_score=0.7,
            discovered_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        # Mock enriched contact info
        finder.public_records_client.enrich_contact_info.return_value = {
            'phone_numbers': ['555-123-4567'],
            'email_addresses': ['john@email.com'],
            'social_profiles': [{'platform': 'LinkedIn', 'url': 'linkedin.com/in/john'}],
            'business_info': {'company': 'Smith Enterprises'},
            'confidence_scores': {'overall': 0.85}
        }
        
        enriched_research = await finder.research_owner_contact_info(opportunity)
        
        assert enriched_research.phone_numbers == ['555-123-4567']
        assert enriched_research.email_addresses == ['john@email.com']
        assert enriched_research.contact_confidence == 0.85

    @pytest.mark.asyncio
    async def test_estimate_property_condition_old_property(self, finder):
        """Test property condition estimation for old property."""
        opportunity = OffMarketOpportunity(
            opportunity_id="1",
            property_address="123 Main St",
            city="Austin",
            state="TX",
            zip_code="78701",
            opportunity_types=[OpportunityType.HIGH_EQUITY],
            year_built=1960,  # Old property
            square_feet=1800,
            opportunity_score=0.8,
            confidence_score=0.7,
            discovered_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        condition_estimate = await finder.estimate_property_condition(opportunity)
        
        assert condition_estimate.condition_score < 70  # Should be reduced for age
        assert "older_property" in condition_estimate.condition_indicators
        assert condition_estimate.repair_estimate is not None

    @pytest.mark.asyncio
    async def test_estimate_property_condition_distressed(self, finder):
        """Test property condition estimation for distressed property."""
        opportunity = OffMarketOpportunity(
            opportunity_id="1",
            property_address="123 Main St",
            city="Austin",
            state="TX",
            zip_code="78701",
            opportunity_types=[OpportunityType.DISTRESSED_OWNER, OpportunityType.VACANT_PROPERTY],
            year_built=2000,
            square_feet=1800,
            opportunity_score=0.8,
            confidence_score=0.7,
            discovered_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        condition_estimate = await finder.estimate_property_condition(opportunity)
        
        assert condition_estimate.condition_score < 70  # Should be reduced for distress indicators
        assert "potential_deferred_maintenance" in condition_estimate.condition_indicators
        assert "vacancy_deterioration" in condition_estimate.condition_indicators

    @pytest.mark.asyncio
    async def test_find_opportunities_integration(self, finder):
        """Test the main find_opportunities method integration."""
        # Mock the individual search methods
        finder._find_high_equity_properties = AsyncMock(return_value=[
            OffMarketOpportunity(
                opportunity_id="HE1",
                property_address="123 Main St",
                city="Austin",
                state="TX",
                zip_code="78701",
                opportunity_types=[OpportunityType.HIGH_EQUITY],
                estimated_equity=100000,
                opportunity_score=0.0,
                confidence_score=0.8,
                discovered_date=datetime.now(),
                last_updated=datetime.now()
            )
        ])
        
        finder._find_absentee_owners = AsyncMock(return_value=[
            OffMarketOpportunity(
                opportunity_id="AO1",
                property_address="456 Oak Ave",
                city="Austin",
                state="TX",
                zip_code="78701",
                opportunity_types=[OpportunityType.ABSENTEE_OWNER],
                opportunity_score=0.0,
                confidence_score=0.7,
                discovered_date=datetime.now(),
                last_updated=datetime.now()
            )
        ])
        
        finder._find_tax_delinquent_properties = AsyncMock(return_value=[])
        finder._find_vacant_properties = AsyncMock(return_value=[])
        finder._find_distressed_properties = AsyncMock(return_value=[])
        
        opportunities = await finder.find_opportunities(
            city="Austin",
            state="TX",
            min_equity=50000,
            limit=10
        )
        
        assert len(opportunities) == 2
        assert opportunities[0].opportunity_score > 0  # Should be scored
        
        # Verify search methods were called
        finder._find_high_equity_properties.assert_called_once()
        finder._find_absentee_owners.assert_called_once()


class TestDataClasses:
    """Test cases for data classes."""

    def test_owner_research_to_dict(self):
        """Test OwnerResearch to_dict conversion."""
        owner_research = OwnerResearch(
            name="John Smith",
            mailing_address="456 Oak Ave",
            phone_numbers=["555-123-4567"],
            email_addresses=["john@email.com"],
            is_absentee_owner=True,
            contact_confidence=0.85,
            last_updated=datetime.now()
        )
        
        data = owner_research.to_dict()
        
        assert data["name"] == "John Smith"
        assert data["is_absentee_owner"] is True
        assert data["contact_confidence"] == 0.85
        assert isinstance(data["last_updated"], str)  # Should be ISO string

    def test_motivation_indicators_to_dict(self):
        """Test MotivationIndicators to_dict conversion."""
        motivation = MotivationIndicators(
            financial_distress=True,
            tax_delinquency=True,
            vacant_property=False,
            motivation_score=0.85,
            confidence_level=0.9
        )
        
        data = motivation.to_dict()
        
        assert data["financial_distress"] is True
        assert data["tax_delinquency"] is True
        assert data["vacant_property"] is False
        assert data["motivation_score"] == 0.85

    def test_property_condition_estimate_to_dict(self):
        """Test PropertyConditionEstimate to_dict conversion."""
        condition = PropertyConditionEstimate(
            overall_condition=PropertyCondition.FAIR,
            condition_score=65.0,
            repair_estimate=25000,
            condition_indicators=["older_property"],
            confidence_level=0.7,
            last_assessed=datetime.now()
        )
        
        data = condition.to_dict()
        
        assert data["overall_condition"] == "fair"
        assert data["condition_score"] == 65.0
        assert data["repair_estimate"] == 25000
        assert isinstance(data["last_assessed"], str)  # Should be ISO string

    def test_off_market_opportunity_to_dict(self):
        """Test OffMarketOpportunity to_dict conversion."""
        opportunity = OffMarketOpportunity(
            opportunity_id="TEST123",
            property_address="123 Main St",
            city="Austin",
            state="TX",
            zip_code="78701",
            opportunity_types=[OpportunityType.HIGH_EQUITY, OpportunityType.ABSENTEE_OWNER],
            estimated_value=300000,
            estimated_equity=150000,
            owner_research=OwnerResearch(name="John Smith"),
            motivation_indicators=MotivationIndicators(motivation_score=0.8),
            condition_estimate=PropertyConditionEstimate(
                overall_condition=PropertyCondition.GOOD,
                condition_score=80.0
            ),
            opportunity_score=0.85,
            confidence_score=0.9,
            discovered_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        data = opportunity.to_dict()
        
        assert data["opportunity_id"] == "TEST123"
        assert data["opportunity_types"] == ["high_equity", "absentee_owner"]
        assert data["estimated_value"] == 300000
        assert isinstance(data["owner_research"], dict)
        assert isinstance(data["motivation_indicators"], dict)
        assert isinstance(data["condition_estimate"], dict)
        assert isinstance(data["discovered_date"], str)  # Should be ISO string


class TestEnums:
    """Test cases for enums."""

    def test_motivation_level_enum(self):
        """Test MotivationLevel enum values."""
        assert MotivationLevel.LOW.value == "low"
        assert MotivationLevel.MEDIUM.value == "medium"
        assert MotivationLevel.HIGH.value == "high"
        assert MotivationLevel.VERY_HIGH.value == "very_high"

    def test_property_condition_enum(self):
        """Test PropertyCondition enum values."""
        assert PropertyCondition.EXCELLENT.value == "excellent"
        assert PropertyCondition.GOOD.value == "good"
        assert PropertyCondition.FAIR.value == "fair"
        assert PropertyCondition.POOR.value == "poor"
        assert PropertyCondition.DISTRESSED.value == "distressed"

    def test_opportunity_type_enum(self):
        """Test OpportunityType enum values."""
        assert OpportunityType.DISTRESSED_OWNER.value == "distressed_owner"
        assert OpportunityType.HIGH_EQUITY.value == "high_equity"
        assert OpportunityType.ABSENTEE_OWNER.value == "absentee_owner"
        assert OpportunityType.ESTATE_SALE.value == "estate_sale"
        assert OpportunityType.DIVORCE.value == "divorce"
        assert OpportunityType.FINANCIAL_DISTRESS.value == "financial_distress"
        assert OpportunityType.TIRED_LANDLORD.value == "tired_landlord"
        assert OpportunityType.VACANT_PROPERTY.value == "vacant_property"
        assert OpportunityType.TAX_DELINQUENT.value == "tax_delinquent"
        assert OpportunityType.CODE_VIOLATIONS.value == "code_violations"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])