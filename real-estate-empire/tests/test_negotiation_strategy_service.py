"""
Unit tests for the Negotiation Strategy Service.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from sqlalchemy.orm import Session
from app.services.negotiation_strategy_service import NegotiationStrategyService
from app.models.property import PropertyDB, PropertyAnalysisDB
from app.models.lead import PropertyLeadDB
from app.models.negotiation import (
    NegotiationStrategyDB,
    MarketConditionEnum,
    SellerMotivationEnum
)


class TestNegotiationStrategyService:
    """Test cases for NegotiationStrategyService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """Create a NegotiationStrategyService instance."""
        return NegotiationStrategyService(mock_db)
    
    @pytest.fixture
    def sample_property(self):
        """Create a sample property for testing."""
        return PropertyDB(
            id=uuid.uuid4(),
            address="123 Test St",
            city="Test City",
            state="TS",
            zip_code="12345",
            property_type="single_family",
            bedrooms=3,
            bathrooms=2.0,
            square_feet=1500,
            year_built=1990,
            listing_price=250000,
            assessed_value=240000,
            days_on_market=45,
            renovation_needed=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_analysis(self):
        """Create a sample property analysis for testing."""
        return PropertyAnalysisDB(
            id=uuid.uuid4(),
            property_id=uuid.uuid4(),
            analysis_type="flip",
            current_value_estimate=245000,
            arv_estimate=280000,
            repair_estimate=15000,
            confidence_score=0.8,
            comparable_count=5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_lead(self):
        """Create a sample property lead for testing."""
        return PropertyLeadDB(
            id=uuid.uuid4(),
            property_id=uuid.uuid4(),
            source="mls",
            lead_score=0.7,
            motivation_factors=["divorce", "relocation"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    def test_generate_strategy_success(self, service, mock_db, sample_property, sample_analysis, sample_lead):
        """Test successful strategy generation."""
        # Setup mocks
        sample_property.id = uuid.uuid4()
        sample_analysis.property_id = sample_property.id
        sample_lead.property_id = sample_property.id
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_property,  # Property query
            sample_analysis,  # Analysis query
            sample_lead       # Lead query
        ]
        
        # Execute
        result = service.generate_strategy(sample_property.id)
        
        # Verify
        assert result is not None
        assert result["property_id"] == sample_property.id
        assert "strategy_name" in result
        assert "recommended_offer_price" in result
        assert "max_offer_price" in result
        assert "negotiation_approach" in result
        assert "market_condition" in result
        assert "seller_motivation" in result
        assert "talking_points" in result
        assert "value_propositions" in result
        assert "potential_objections" in result
        assert "contingencies" in result
        assert "confidence_score" in result
        assert "risk_assessment" in result
        
        # Verify price calculations are reasonable
        assert result["recommended_offer_price"] > 0
        assert result["max_offer_price"] > result["recommended_offer_price"]
        assert result["confidence_score"] >= 0.0
        assert result["confidence_score"] <= 1.0
    
    def test_generate_strategy_property_not_found(self, service, mock_db):
        """Test strategy generation when property is not found."""
        # Setup mock
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute and verify
        property_id = uuid.uuid4()
        with pytest.raises(ValueError, match=f"Property with ID {property_id} not found"):
            service.generate_strategy(property_id)
    
    def test_analyze_market_conditions_buyers_market(self, service, sample_property):
        """Test market condition analysis for buyer's market."""
        sample_property.days_on_market = 120
        
        result = service._analyze_market_conditions(sample_property)
        
        assert result == MarketConditionEnum.BUYERS_MARKET
    
    def test_analyze_market_conditions_sellers_market(self, service, sample_property):
        """Test market condition analysis for seller's market."""
        sample_property.days_on_market = 15
        
        result = service._analyze_market_conditions(sample_property)
        
        assert result == MarketConditionEnum.SELLERS_MARKET
    
    def test_analyze_market_conditions_balanced(self, service, sample_property):
        """Test market condition analysis for balanced market."""
        sample_property.days_on_market = 60
        
        result = service._analyze_market_conditions(sample_property)
        
        assert result == MarketConditionEnum.BALANCED
    
    def test_assess_seller_motivation_urgent(self, service, sample_property, sample_lead):
        """Test seller motivation assessment for urgent motivation."""
        sample_property.days_on_market = 150
        sample_property.renovation_needed = True
        sample_property.listing_price = 200000
        sample_property.assessed_value = 250000  # Price reduced significantly
        sample_lead.motivation_factors = ["divorce", "foreclosure", "relocation"]
        
        result = service._assess_seller_motivation(sample_property, sample_lead)
        
        assert result == SellerMotivationEnum.URGENT
    
    def test_assess_seller_motivation_low(self, service, sample_property):
        """Test seller motivation assessment for low motivation."""
        sample_property.days_on_market = 10
        sample_property.renovation_needed = False
        
        result = service._assess_seller_motivation(sample_property, None)
        
        assert result == SellerMotivationEnum.LOW
    
    def test_calculate_offer_prices_with_analysis(self, service, sample_property, sample_analysis):
        """Test offer price calculation with property analysis."""
        market_condition = MarketConditionEnum.BALANCED
        seller_motivation = SellerMotivationEnum.MODERATE
        
        result = service._calculate_offer_prices(
            sample_property, sample_analysis, market_condition, seller_motivation
        )
        
        assert "recommended" in result
        assert "maximum" in result
        assert result["recommended"] > 0
        assert result["maximum"] > result["recommended"]
        assert result["recommended"] < sample_analysis.current_value_estimate
    
    def test_calculate_offer_prices_without_analysis(self, service, sample_property):
        """Test offer price calculation without property analysis."""
        market_condition = MarketConditionEnum.BUYERS_MARKET
        seller_motivation = SellerMotivationEnum.HIGH
        
        result = service._calculate_offer_prices(
            sample_property, None, market_condition, seller_motivation
        )
        
        assert "recommended" in result
        assert "maximum" in result
        assert result["recommended"] > 0
        assert result["maximum"] > result["recommended"]
        assert result["recommended"] < sample_property.listing_price
    
    def test_determine_negotiation_approach_aggressive(self, service):
        """Test negotiation approach determination for aggressive approach."""
        result = service._determine_negotiation_approach(
            MarketConditionEnum.BUYERS_MARKET,
            SellerMotivationEnum.URGENT
        )
        
        assert result == "aggressive"
    
    def test_determine_negotiation_approach_conservative(self, service):
        """Test negotiation approach determination for conservative approach."""
        result = service._determine_negotiation_approach(
            MarketConditionEnum.SELLERS_MARKET,
            SellerMotivationEnum.LOW
        )
        
        assert result == "conservative"
    
    def test_generate_talking_points(self, service, sample_property, sample_analysis):
        """Test talking points generation."""
        sample_property.days_on_market = 75
        sample_property.renovation_needed = True
        sample_analysis.repair_estimate = 20000
        
        result = service._generate_talking_points(
            sample_property, sample_analysis, MarketConditionEnum.BUYERS_MARKET
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert any("market" in point.lower() for point in result)
        assert any("75 days" in point for point in result)
        assert any("renovation" in point.lower() for point in result)
        assert any("20,000" in point for point in result)
    
    def test_generate_value_propositions(self, service, sample_property):
        """Test value propositions generation."""
        result = service._generate_value_propositions(
            sample_property, MarketConditionEnum.BALANCED
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert any("cash" in prop.lower() for prop in result)
        assert any("closing" in prop.lower() for prop in result)
    
    def test_identify_potential_objections(self, service, sample_property):
        """Test potential objections identification."""
        offer_prices = {"recommended": 200000, "maximum": 220000}
        sample_property.listing_price = 250000
        
        result = service._identify_potential_objections(
            sample_property, offer_prices, MarketConditionEnum.BALANCED
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("objection" in obj and "response" in obj for obj in result)
    
    def test_recommend_contingencies(self, service, sample_property):
        """Test contingencies recommendation."""
        sample_property.year_built = 1975  # Pre-1980 for lead paint
        
        result = service._recommend_contingencies(
            sample_property, MarketConditionEnum.BALANCED
        )
        
        assert isinstance(result, list)
        assert any("inspection" in cont.lower() for cont in result)
        assert any("lead paint" in cont.lower() for cont in result)
    
    def test_assess_negotiation_risks(self, service, sample_property):
        """Test negotiation risk assessment."""
        sample_property.renovation_needed = True
        
        result = service._assess_negotiation_risks(
            sample_property,
            MarketConditionEnum.SELLERS_MARKET,
            SellerMotivationEnum.LOW
        )
        
        assert "overall_risk" in result
        assert "risk_factors" in result
        assert "mitigation_strategies" in result
        assert isinstance(result["risk_factors"], list)
        assert isinstance(result["mitigation_strategies"], list)
        assert result["overall_risk"] in ["low", "medium", "high"]
    
    def test_calculate_confidence_score(self, service, sample_property, sample_analysis):
        """Test confidence score calculation."""
        sample_property.days_on_market = 30
        sample_property.listing_price = 250000
        
        result = service._calculate_confidence_score(
            sample_property,
            sample_analysis,
            MarketConditionEnum.BALANCED,
            SellerMotivationEnum.MODERATE
        )
        
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0
    
    def test_save_strategy(self, service, mock_db):
        """Test saving a negotiation strategy."""
        strategy_data = {
            "property_id": uuid.uuid4(),
            "strategy_name": "Test Strategy",
            "recommended_offer_price": 200000,
            "max_offer_price": 220000,
            "negotiation_approach": "moderate",
            "market_condition": MarketConditionEnum.BALANCED,
            "seller_motivation": SellerMotivationEnum.MODERATE,
            "confidence_score": 0.7
        }
        
        mock_strategy = Mock(spec=NegotiationStrategyDB)
        mock_strategy.id = uuid.uuid4()
        mock_strategy.property_id = strategy_data["property_id"]
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        with patch('app.services.negotiation_strategy_service.NegotiationStrategyDB', return_value=mock_strategy):
            result = service.save_strategy(strategy_data)
        
        assert result == mock_strategy
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_get_strategy(self, service, mock_db):
        """Test getting a negotiation strategy by ID."""
        strategy_id = uuid.uuid4()
        mock_strategy = Mock(spec=NegotiationStrategyDB)
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_strategy
        
        result = service.get_strategy(strategy_id)
        
        assert result == mock_strategy
        mock_db.query.assert_called_once_with(NegotiationStrategyDB)
    
    def test_get_strategies_for_property(self, service, mock_db):
        """Test getting all strategies for a property."""
        property_id = uuid.uuid4()
        mock_strategies = [Mock(spec=NegotiationStrategyDB), Mock(spec=NegotiationStrategyDB)]
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_strategies
        
        result = service.get_strategies_for_property(property_id)
        
        assert result == mock_strategies
        mock_db.query.assert_called_once_with(NegotiationStrategyDB)
    
    def test_calculate_dom_factor(self, service, sample_property):
        """Test days on market factor calculation."""
        sample_property.days_on_market = 90
        
        result = service._calculate_dom_factor(sample_property)
        
        assert result == 0.5  # 90/180
    
    def test_calculate_dom_factor_none(self, service, sample_property):
        """Test days on market factor calculation when DOM is None."""
        sample_property.days_on_market = None
        
        result = service._calculate_dom_factor(sample_property)
        
        assert result is None
    
    def test_calculate_comp_factor(self, service, sample_analysis):
        """Test comparable sales factor calculation."""
        sample_analysis.comparable_count = 5
        
        result = service._calculate_comp_factor(sample_analysis)
        
        assert result == 0.5  # 5/10
    
    def test_calculate_comp_factor_none(self, service):
        """Test comparable sales factor calculation when analysis is None."""
        result = service._calculate_comp_factor(None)
        
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__])