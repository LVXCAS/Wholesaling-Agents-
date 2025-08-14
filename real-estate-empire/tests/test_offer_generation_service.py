"""
Unit tests for the Offer Generation Service.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from sqlalchemy.orm import Session
from app.services.offer_generation_service import OfferGenerationService
from app.models.property import PropertyDB, PropertyAnalysisDB
from app.models.lead import PropertyLeadDB
from app.models.negotiation import (
    NegotiationStrategyDB,
    OfferDB,
    OfferTypeEnum,
    NegotiationStatusEnum,
    MarketConditionEnum,
    SellerMotivationEnum
)


class TestOfferGenerationService:
    """Test cases for OfferGenerationService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """Create an OfferGenerationService instance."""
        return OfferGenerationService(mock_db)
    
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
    def sample_strategy(self):
        """Create a sample negotiation strategy for testing."""
        return NegotiationStrategyDB(
            id=uuid.uuid4(),
            property_id=uuid.uuid4(),
            strategy_name="Test Strategy",
            recommended_offer_price=220000,
            max_offer_price=240000,
            negotiation_approach="moderate",
            market_condition=MarketConditionEnum.BALANCED,
            seller_motivation=SellerMotivationEnum.MODERATE,
            confidence_score=0.7,
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
    
    def test_generate_offer_success(self, service, mock_db, sample_property, sample_strategy, sample_analysis):
        """Test successful offer generation."""
        # Setup mocks
        sample_strategy.property_id = sample_property.id
        sample_analysis.property_id = sample_property.id
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_strategy,  # Strategy query
            sample_property,  # Property query
            sample_analysis   # Analysis query
        ]
        
        # Execute
        result = service.generate_offer(sample_strategy.id, OfferTypeEnum.INITIAL)
        
        # Verify
        assert result is not None
        assert result["strategy_id"] == sample_strategy.id
        assert result["property_id"] == sample_property.id
        assert result["offer_type"] == OfferTypeEnum.INITIAL
        assert result["offer_amount"] > 0
        assert result["earnest_money"] > 0
        assert result["down_payment"] > 0
        assert "financing_type" in result
        assert "closing_date" in result
        assert "inspection_period" in result
        assert "appraisal_contingency" in result
        assert "financing_contingency" in result
        assert "inspection_contingency" in result
        assert "custom_terms" in result
        assert "contingencies" in result
        assert result["status"] == NegotiationStatusEnum.INITIATED
    
    def test_generate_offer_strategy_not_found(self, service, mock_db):
        """Test offer generation when strategy is not found."""
        # Setup mock
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute and verify
        strategy_id = uuid.uuid4()
        with pytest.raises(ValueError, match=f"Negotiation strategy with ID {strategy_id} not found"):
            service.generate_offer(strategy_id)
    
    def test_generate_offer_property_not_found(self, service, mock_db, sample_strategy):
        """Test offer generation when property is not found."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_strategy,  # Strategy query
            None              # Property query
        ]
        
        # Execute and verify
        with pytest.raises(ValueError, match=f"Property with ID {sample_strategy.property_id} not found"):
            service.generate_offer(sample_strategy.id)
    
    def test_calculate_offer_price_initial(self, service, sample_strategy):
        """Test offer price calculation for initial offer."""
        result = service._calculate_offer_price(sample_strategy, OfferTypeEnum.INITIAL)
        
        assert result == sample_strategy.recommended_offer_price
    
    def test_calculate_offer_price_counter(self, service, sample_strategy):
        """Test offer price calculation for counter offer."""
        result = service._calculate_offer_price(sample_strategy, OfferTypeEnum.COUNTER)
        
        assert result > sample_strategy.recommended_offer_price
        assert result <= sample_strategy.max_offer_price
    
    def test_calculate_offer_price_final(self, service, sample_strategy):
        """Test offer price calculation for final offer."""
        result = service._calculate_offer_price(sample_strategy, OfferTypeEnum.FINAL)
        
        assert result == sample_strategy.max_offer_price
    
    def test_calculate_earnest_money_buyers_market(self, service):
        """Test earnest money calculation in buyer's market."""
        result = service._calculate_earnest_money(200000, MarketConditionEnum.BUYERS_MARKET)
        
        assert result == 2000  # 1% of 200k
    
    def test_calculate_earnest_money_sellers_market(self, service):
        """Test earnest money calculation in seller's market."""
        result = service._calculate_earnest_money(200000, MarketConditionEnum.SELLERS_MARKET)
        
        assert result == 4000  # 2% of 200k
    
    def test_calculate_down_payment_aggressive(self, service):
        """Test down payment calculation for aggressive approach."""
        result = service._calculate_down_payment(200000, "aggressive")
        
        assert result == 40000  # 20% of 200k
    
    def test_calculate_down_payment_conservative(self, service):
        """Test down payment calculation for conservative approach."""
        result = service._calculate_down_payment(200000, "conservative")
        
        assert result == 20000  # 10% of 200k
    
    def test_determine_financing_type_aggressive(self, service):
        """Test financing type determination for aggressive approach."""
        result = service._determine_financing_type("aggressive")
        
        assert result == "cash"
    
    def test_determine_financing_type_moderate(self, service):
        """Test financing type determination for moderate approach."""
        result = service._determine_financing_type("moderate")
        
        assert result == "conventional"
    
    def test_calculate_closing_date_urgent_seller(self, service):
        """Test closing date calculation for urgent seller."""
        result = service._calculate_closing_date(
            MarketConditionEnum.BALANCED,
            SellerMotivationEnum.URGENT
        )
        
        expected_date = datetime.now() + timedelta(days=14)
        assert abs((result - expected_date).days) <= 1  # Allow 1 day difference
    
    def test_calculate_closing_date_sellers_market(self, service):
        """Test closing date calculation in seller's market."""
        result = service._calculate_closing_date(
            MarketConditionEnum.SELLERS_MARKET,
            SellerMotivationEnum.MODERATE
        )
        
        expected_date = datetime.now() + timedelta(days=21)
        assert abs((result - expected_date).days) <= 1  # Allow 1 day difference
    
    def test_determine_inspection_period_old_property(self, service, sample_property):
        """Test inspection period determination for old property."""
        sample_property.year_built = 1975
        
        result = service._determine_inspection_period(sample_property, MarketConditionEnum.BALANCED)
        
        assert result >= 13  # Base 10 + 3 for old property
    
    def test_determine_inspection_period_needs_renovation(self, service, sample_property):
        """Test inspection period determination for property needing renovation."""
        sample_property.renovation_needed = True
        
        result = service._determine_inspection_period(sample_property, MarketConditionEnum.BALANCED)
        
        assert result >= 12  # Base 10 + 2 for renovation needed
    
    def test_determine_contingencies_sellers_market_aggressive(self, service, sample_property, sample_strategy):
        """Test contingency determination in seller's market with aggressive approach."""
        sample_strategy.market_condition = MarketConditionEnum.SELLERS_MARKET
        sample_strategy.negotiation_approach = "aggressive"
        
        result = service._determine_contingencies(sample_property, sample_strategy, OfferTypeEnum.INITIAL)
        
        assert result["appraisal"] == False  # Waived in aggressive seller's market
        assert result["financing"] == False  # Cash offer
        assert result["inspection"] == True   # Still included for initial offer
    
    def test_determine_contingencies_final_offer(self, service, sample_property, sample_strategy):
        """Test contingency determination for final offer."""
        sample_strategy.market_condition = MarketConditionEnum.SELLERS_MARKET
        
        result = service._determine_contingencies(sample_property, sample_strategy, OfferTypeEnum.FINAL)
        
        assert result["inspection"] == False  # Waived for final offer in seller's market
    
    def test_generate_custom_terms_buyers_market(self, service, sample_property, sample_strategy):
        """Test custom terms generation in buyer's market."""
        sample_strategy.market_condition = MarketConditionEnum.BUYERS_MARKET
        
        result = service._generate_custom_terms(sample_property, sample_strategy, OfferTypeEnum.INITIAL)
        
        assert "seller_concessions" in result
        assert result["seller_concessions"] > 0
    
    def test_generate_custom_terms_motivated_seller(self, service, sample_property, sample_strategy):
        """Test custom terms generation for motivated seller."""
        sample_strategy.seller_motivation = SellerMotivationEnum.HIGH
        
        result = service._generate_custom_terms(sample_property, sample_strategy, OfferTypeEnum.INITIAL)
        
        assert "rent_back_days" in result
        assert result["rent_back_days"] == 30
    
    def test_generate_custom_terms_renovation_needed(self, service, sample_property, sample_strategy):
        """Test custom terms generation for property needing renovation."""
        sample_property.renovation_needed = True
        
        result = service._generate_custom_terms(sample_property, sample_strategy, OfferTypeEnum.INITIAL)
        
        assert result["as_is_purchase"] == True
        assert result["no_repair_requests"] == True
    
    def test_generate_contingency_list(self, service, sample_property, sample_strategy):
        """Test contingency list generation."""
        result = service._generate_contingency_list(sample_property, sample_strategy, OfferTypeEnum.INITIAL)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert any("inspection" in cont.lower() for cont in result)
        assert any("title" in cont.lower() for cont in result)
    
    def test_generate_contingency_list_old_property(self, service, sample_property, sample_strategy):
        """Test contingency list generation for old property."""
        sample_property.year_built = 1975
        
        result = service._generate_contingency_list(sample_property, sample_strategy, OfferTypeEnum.INITIAL)
        
        assert any("lead" in cont.lower() for cont in result)
    
    def test_generate_contingency_list_condo(self, service, sample_property, sample_strategy):
        """Test contingency list generation for condo."""
        sample_property.property_type = "condo"
        
        result = service._generate_contingency_list(sample_property, sample_strategy, OfferTypeEnum.INITIAL)
        
        assert any("hoa" in cont.lower() for cont in result)
    
    def test_generate_multiple_offer_strategy(self, service, mock_db, sample_strategy):
        """Test multiple offer strategy generation."""
        # Setup mock
        mock_db.query.return_value.filter.return_value.first.return_value = sample_strategy
        
        with patch.object(service, 'generate_offer') as mock_generate:
            mock_generate.side_effect = [
                {"offer_amount": 220000, "scenario": "primary"},
                {"offer_amount": 240000, "scenario": "aggressive"}
            ]
            
            result = service.generate_multiple_offer_strategy(sample_strategy.id)
        
        assert len(result) == 3  # Primary, aggressive, conservative
        assert result[0]["scenario_name"] == "Primary Offer"
        assert result[1]["scenario_name"] == "Aggressive Offer"
        assert result[2]["scenario_name"] == "Conservative Offer"
    
    def test_save_offer(self, service, mock_db):
        """Test saving an offer."""
        offer_data = {
            "strategy_id": uuid.uuid4(),
            "property_id": uuid.uuid4(),
            "offer_type": OfferTypeEnum.INITIAL,
            "offer_amount": 220000,
            "earnest_money": 3000,
            "status": NegotiationStatusEnum.INITIATED
        }
        
        mock_offer = Mock(spec=OfferDB)
        mock_offer.id = uuid.uuid4()
        mock_offer.property_id = offer_data["property_id"]
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        with patch('app.services.offer_generation_service.OfferDB', return_value=mock_offer):
            result = service.save_offer(offer_data)
        
        assert result == mock_offer
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_get_offer(self, service, mock_db):
        """Test getting an offer by ID."""
        offer_id = uuid.uuid4()
        mock_offer = Mock(spec=OfferDB)
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_offer
        
        result = service.get_offer(offer_id)
        
        assert result == mock_offer
        mock_db.query.assert_called_once_with(OfferDB)
    
    def test_get_offers_for_property(self, service, mock_db):
        """Test getting all offers for a property."""
        property_id = uuid.uuid4()
        mock_offers = [Mock(spec=OfferDB), Mock(spec=OfferDB)]
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_offers
        
        result = service.get_offers_for_property(property_id)
        
        assert result == mock_offers
        mock_db.query.assert_called_once_with(OfferDB)
    
    def test_get_offers_for_strategy(self, service, mock_db):
        """Test getting all offers for a strategy."""
        strategy_id = uuid.uuid4()
        mock_offers = [Mock(spec=OfferDB), Mock(spec=OfferDB)]
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_offers
        
        result = service.get_offers_for_strategy(strategy_id)
        
        assert result == mock_offers
        mock_db.query.assert_called_once_with(OfferDB)
    
    def test_update_offer_status(self, service, mock_db):
        """Test updating offer status."""
        offer_id = uuid.uuid4()
        mock_offer = Mock(spec=OfferDB)
        mock_offer.id = offer_id
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_offer
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        response_details = {"seller_response": "accepted"}
        
        result = service.update_offer_status(offer_id, NegotiationStatusEnum.ACCEPTED, response_details)
        
        assert result == mock_offer
        assert mock_offer.status == NegotiationStatusEnum.ACCEPTED
        assert mock_offer.response_received == True
        assert mock_offer.response_details == response_details
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_update_offer_status_not_found(self, service, mock_db):
        """Test updating offer status when offer is not found."""
        offer_id = uuid.uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match=f"Offer with ID {offer_id} not found"):
            service.update_offer_status(offer_id, NegotiationStatusEnum.ACCEPTED)
    
    def test_calculate_offer_competitiveness(self, service, mock_db, sample_property):
        """Test offer competitiveness calculation."""
        offer_data = {
            "property_id": sample_property.id,
            "offer_amount": 240000,  # 96% of listing price
            "appraisal_contingency": False,
            "financing_type": "cash",
            "closing_date": datetime.now() + timedelta(days=21)
        }
        
        mock_db.query.return_value.filter.return_value.first.return_value = sample_property
        
        result = service.calculate_offer_competitiveness(offer_data)
        
        assert "overall_score" in result
        assert "strengths" in result
        assert "weaknesses" in result
        assert "recommendations" in result
        assert 0 <= result["overall_score"] <= 100
    
    def test_analyze_price_competitiveness_full_price(self, service, sample_property):
        """Test price competitiveness analysis for full price offer."""
        offer_data = {"offer_amount": 250000}  # Full listing price
        
        result = service._analyze_price_competitiveness(offer_data, sample_property)
        
        assert result == 100.0
    
    def test_analyze_price_competitiveness_low_offer(self, service, sample_property):
        """Test price competitiveness analysis for low offer."""
        offer_data = {"offer_amount": 200000}  # 80% of listing price
        
        result = service._analyze_price_competitiveness(offer_data, sample_property)
        
        assert result == 25.0
    
    def test_analyze_terms_competitiveness_waived_contingencies(self, service):
        """Test terms competitiveness analysis with waived contingencies."""
        offer_data = {
            "appraisal_contingency": False,
            "inspection_contingency": False,
            "financing_contingency": False,
            "custom_terms": {"as_is_purchase": True}
        }
        
        result = service._analyze_terms_competitiveness(offer_data)
        
        assert result >= 90.0  # High score for waived contingencies
    
    def test_analyze_financing_competitiveness_cash(self, service):
        """Test financing competitiveness analysis for cash offer."""
        offer_data = {"financing_type": "cash"}
        
        result = service._analyze_financing_competitiveness(offer_data)
        
        assert result == 100.0
    
    def test_analyze_financing_competitiveness_fha(self, service):
        """Test financing competitiveness analysis for FHA loan."""
        offer_data = {"financing_type": "fha"}
        
        result = service._analyze_financing_competitiveness(offer_data)
        
        assert result == 60.0
    
    def test_analyze_timeline_competitiveness_fast_close(self, service):
        """Test timeline competitiveness analysis for fast closing."""
        offer_data = {"closing_date": datetime.now() + timedelta(days=14)}
        
        result = service._analyze_timeline_competitiveness(offer_data)
        
        assert result == 100.0
    
    def test_analyze_timeline_competitiveness_slow_close(self, service):
        """Test timeline competitiveness analysis for slow closing."""
        offer_data = {"closing_date": datetime.now() + timedelta(days=60)}
        
        result = service._analyze_timeline_competitiveness(offer_data)
        
        assert result == 25.0
    
    def test_generate_competitiveness_recommendations_low_score(self, service):
        """Test competitiveness recommendations for low score."""
        offer_data = {
            "appraisal_contingency": True,
            "financing_type": "conventional",
            "closing_date": datetime.now() + timedelta(days=45)
        }
        
        result = service._generate_competitiveness_recommendations(offer_data, 40.0)
        
        assert len(result) > 0
        assert any("increasing offer price" in rec.lower() for rec in result)
        assert any("waiving appraisal" in rec.lower() for rec in result)


if __name__ == "__main__":
    pytest.main([__file__])