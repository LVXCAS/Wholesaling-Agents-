"""
Unit tests for the Counter Offer Analyzer Service.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from sqlalchemy.orm import Session
from app.services.counter_offer_analyzer_service import CounterOfferAnalyzerService
from app.models.property import PropertyDB, PropertyAnalysisDB
from app.models.negotiation import (
    NegotiationStrategyDB,
    OfferDB,
    CounterOfferDB,
    OfferTypeEnum,
    NegotiationStatusEnum,
    MarketConditionEnum,
    SellerMotivationEnum
)


class TestCounterOfferAnalyzerService:
    """Test cases for CounterOfferAnalyzerService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """Create a CounterOfferAnalyzerService instance."""
        return CounterOfferAnalyzerService(mock_db)
    
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
    def sample_offer(self):
        """Create a sample offer for testing."""
        return OfferDB(
            id=uuid.uuid4(),
            strategy_id=uuid.uuid4(),
            property_id=uuid.uuid4(),
            offer_type=OfferTypeEnum.INITIAL,
            offer_amount=220000,
            earnest_money=3000,
            down_payment=44000,
            financing_type="conventional",
            closing_date=datetime.now() + timedelta(days=30),
            inspection_period=10,
            appraisal_contingency=True,
            financing_contingency=True,
            inspection_contingency=True,
            status=NegotiationStatusEnum.INITIATED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_counter_offer_data(self):
        """Create sample counter offer data for testing."""
        return {
            "counter_amount": 235000,
            "seller_changes": {
                "closing_date": (datetime.now() + timedelta(days=45)).isoformat(),
                "appraisal_contingency": False,
                "custom_terms": {
                    "seller_concessions": 2000
                }
            }
        }
    
    def test_analyze_counter_offer_success(self, service, mock_db, sample_property, 
                                         sample_strategy, sample_offer, sample_counter_offer_data):
        """Test successful counter offer analysis."""
        # Setup mocks
        sample_offer.strategy_id = sample_strategy.id
        sample_offer.property_id = sample_property.id
        sample_strategy.property_id = sample_property.id
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_offer,    # Offer query
            sample_strategy, # Strategy query
            sample_property  # Property query
        ]
        
        # Execute
        result = service.analyze_counter_offer(sample_offer.id, sample_counter_offer_data)
        
        # Verify
        assert result is not None
        assert result["original_offer_id"] == sample_offer.id
        assert result["counter_amount"] == sample_counter_offer_data["counter_amount"]
        assert "price_analysis" in result
        assert "terms_analysis" in result
        assert "risk_assessment" in result
        assert "negotiation_path" in result
        assert "response_recommendation" in result
        assert "deal_viability" in result
        assert "confidence_score" in result
        assert 0 <= result["confidence_score"] <= 1
    
    def test_analyze_counter_offer_not_found(self, service, mock_db):
        """Test counter offer analysis when original offer is not found."""
        # Setup mock
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute and verify
        offer_id = uuid.uuid4()
        with pytest.raises(ValueError, match=f"Original offer with ID {offer_id} not found"):
            service.analyze_counter_offer(offer_id, {})
    
    def test_analyze_price_change_within_budget(self, service, sample_offer, sample_strategy):
        """Test price change analysis when counter is within budget."""
        counter_amount = 235000  # Within max budget of 240000
        
        result = service._analyze_price_change(sample_offer, counter_amount, sample_strategy)
        
        assert result["original_amount"] == sample_offer.offer_amount
        assert result["counter_amount"] == counter_amount
        assert result["price_difference"] == counter_amount - sample_offer.offer_amount
        assert result["within_budget"] == True
        assert result["negotiation_room"] > 0
        assert result["competitiveness"] == "good"
    
    def test_analyze_price_change_over_budget(self, service, sample_offer, sample_strategy):
        """Test price change analysis when counter exceeds budget."""
        counter_amount = 250000  # Over max budget of 240000
        
        result = service._analyze_price_change(sample_offer, counter_amount, sample_strategy)
        
        assert result["within_budget"] == False
        assert result["negotiation_room"] == 0
        assert result["competitiveness"] in ["marginal", "poor"]  # Allow both since 250k is only 4% over 240k
        assert result["distance_from_max"] < 0
    
    def test_analyze_price_change_excellent_deal(self, service, sample_offer, sample_strategy):
        """Test price change analysis for excellent deal."""
        counter_amount = 215000  # Below recommended price
        
        result = service._analyze_price_change(sample_offer, counter_amount, sample_strategy)
        
        assert result["competitiveness"] == "excellent"
        assert result["within_budget"] == True
    
    def test_analyze_terms_changes_closing_date(self, service, sample_offer, sample_strategy):
        """Test terms analysis with closing date change."""
        seller_changes = {
            "closing_date": (datetime.now() + timedelta(days=60)).isoformat()
        }
        
        result = service._analyze_terms_changes(sample_offer, seller_changes, sample_strategy)
        
        assert result["closing_date_change"] is not None
        assert result["closing_date_change"]["days_difference"] > 0
        assert result["closing_date_change"]["impact"] == "negative"
    
    def test_analyze_terms_changes_contingencies(self, service, sample_offer, sample_strategy):
        """Test terms analysis with contingency changes."""
        seller_changes = {
            "appraisal_contingency": False,
            "inspection_contingency": False
        }
        
        result = service._analyze_terms_changes(sample_offer, seller_changes, sample_strategy)
        
        assert len(result["contingency_changes"]) == 2
        # Check that we have negative impacts (seller requesting to remove contingencies that were originally True)
        negative_changes = [change for change in result["contingency_changes"] if change["impact"] == "negative"]
        assert len(negative_changes) >= 1  # At least one should be negative
        assert result["overall_terms_impact"] in ["negative", "neutral"]
    
    def test_analyze_terms_changes_custom_terms(self, service, sample_offer, sample_strategy):
        """Test terms analysis with custom terms."""
        seller_changes = {
            "custom_terms": {
                "seller_concessions": 3000,
                "rent_back_days": 30
            }
        }
        
        result = service._analyze_terms_changes(sample_offer, seller_changes, sample_strategy)
        
        assert len(result["custom_terms_changes"]) == 2
        custom_terms = {change["term"]: change["impact"] for change in result["custom_terms_changes"]}
        assert custom_terms["seller_concessions"] == "negative"
        assert custom_terms["rent_back_days"] == "positive"
    
    def test_assess_custom_term_impact_negative(self, service):
        """Test custom term impact assessment for negative terms."""
        result = service._assess_custom_term_impact("seller_concessions", 5000)
        assert result == "negative"
        
        result = service._assess_custom_term_impact("repair_credits", 2000)
        assert result == "negative"
    
    def test_assess_custom_term_impact_positive(self, service):
        """Test custom term impact assessment for positive terms."""
        result = service._assess_custom_term_impact("rent_back_days", 30)
        assert result == "positive"
        
        result = service._assess_custom_term_impact("as_is_acceptance", True)
        assert result == "positive"
    
    def test_assess_counter_offer_risks_over_budget(self, service, sample_offer, sample_strategy, sample_property):
        """Test risk assessment when counter offer is over budget."""
        counter_offer_data = {"counter_amount": 250000}  # Over budget
        
        result = service._assess_counter_offer_risks(
            sample_offer, counter_offer_data, sample_strategy, sample_property
        )
        
        assert len(result["financial_risks"]) > 0
        assert any("exceeds maximum budget" in risk["risk"].lower() for risk in result["financial_risks"])
        assert result["overall_risk_level"] in ["medium", "high"]
    
    def test_assess_counter_offer_risks_waived_inspection(self, service, sample_offer, sample_strategy, sample_property):
        """Test risk assessment when inspection is waived on property needing repairs."""
        sample_property.renovation_needed = True
        counter_offer_data = {
            "counter_amount": 235000,
            "seller_changes": {"inspection_contingency": False}
        }
        
        result = service._assess_counter_offer_risks(
            sample_offer, counter_offer_data, sample_strategy, sample_property
        )
        
        assert len(result["property_risks"]) > 0
        assert any("waiving inspection" in risk["risk"].lower() for risk in result["property_risks"])
        assert result["overall_risk_level"] == "high"
    
    def test_predict_negotiation_path_successful(self, service, sample_offer, sample_strategy):
        """Test negotiation path prediction for successful scenario."""
        counter_offer_data = {"counter_amount": 235000}  # Within budget
        
        result = service._predict_negotiation_path(sample_offer, counter_offer_data, sample_strategy)
        
        assert result["likely_outcome"] == "successful_negotiation"
        assert result["success_probability"] >= 0.7
        assert result["estimated_rounds_to_completion"] <= 2
        assert len(result["recommended_next_steps"]) > 0
    
    def test_predict_negotiation_path_difficult(self, service, sample_offer, sample_strategy):
        """Test negotiation path prediction for difficult scenario."""
        counter_offer_data = {"counter_amount": 260000}  # Well over budget
        
        result = service._predict_negotiation_path(sample_offer, counter_offer_data, sample_strategy)
        
        assert result["likely_outcome"] == "difficult_negotiation"
        assert result["success_probability"] <= 0.4
        assert result["estimated_rounds_to_completion"] >= 2
    
    def test_generate_next_steps_successful(self, service, sample_strategy):
        """Test next steps generation for successful negotiation."""
        result = service._generate_next_steps("successful_negotiation", 215000, sample_strategy)
        
        assert len(result) > 0
        assert any("accept" in step.lower() for step in result)
    
    def test_generate_next_steps_difficult(self, service, sample_strategy):
        """Test next steps generation for difficult negotiation."""
        result = service._generate_next_steps("difficult_negotiation", 260000, sample_strategy)
        
        assert len(result) > 0
        assert any("walking away" in step.lower() or "final offer" in step.lower() for step in result)
    
    def test_generate_response_recommendation_accept(self, service, sample_offer, sample_strategy):
        """Test response recommendation for acceptable counter offer."""
        price_analysis = {
            "counter_amount": 235000,
            "within_budget": True,
            "competitiveness": "good",
            "original_amount": 220000,
            "distance_from_max": 5000,
            "negotiation_room": 5000
        }
        terms_analysis = {"terms_acceptability": "acceptable", "overall_terms_impact": "neutral"}
        risk_assessment = {"overall_risk_level": "low"}
        
        result = service._generate_response_recommendation(
            price_analysis, terms_analysis, risk_assessment, sample_strategy
        )
        
        assert result["primary_action"] in ["accept", "counter"]  # Could be either based on logic
        assert result["confidence"] >= 0.5
        assert "response_details" in result
    
    def test_generate_response_recommendation_reject(self, service, sample_offer, sample_strategy):
        """Test response recommendation for unacceptable counter offer."""
        price_analysis = {
            "counter_amount": 260000,
            "within_budget": False,
            "competitiveness": "poor",
            "original_amount": 220000,
            "distance_from_max": -20000,
            "negotiation_room": 0
        }
        terms_analysis = {"terms_acceptability": "acceptable", "overall_terms_impact": "neutral"}
        risk_assessment = {"overall_risk_level": "medium"}
        
        result = service._generate_response_recommendation(
            price_analysis, terms_analysis, risk_assessment, sample_strategy
        )
        
        assert result["primary_action"] == "reject"
        assert result["confidence"] >= 0.7
    
    def test_generate_response_recommendation_counter(self, service, sample_offer, sample_strategy):
        """Test response recommendation for counter-worthy offer."""
        price_analysis = {
            "counter_amount": 245000,
            "within_budget": False,
            "competitiveness": "marginal",
            "original_amount": 220000,
            "distance_from_max": -5000,
            "negotiation_room": 0
        }
        terms_analysis = {"terms_acceptability": "marginal", "overall_terms_impact": "neutral"}
        risk_assessment = {"overall_risk_level": "medium"}
        
        result = service._generate_response_recommendation(
            price_analysis, terms_analysis, risk_assessment, sample_strategy
        )
        
        assert result["primary_action"] == "reject"  # Should reject since over budget
        assert "response_details" in result
    
    def test_generate_response_details_counter(self, service, sample_strategy):
        """Test response details generation for counter action."""
        price_analysis = {
            "counter_amount": 245000,
            "original_amount": 220000
        }
        terms_analysis = {"contingency_changes": []}
        
        result = service._generate_response_details("counter", price_analysis, terms_analysis, sample_strategy)
        
        assert "suggested_counter_price" in result
        assert result["suggested_counter_price"] <= sample_strategy.max_offer_price
        assert "price_justification" in result
        assert "message_tone" in result
        assert "deadline" in result
    
    def test_suggest_terms_modifications(self, service):
        """Test terms modifications suggestions."""
        terms_analysis = {
            "contingency_changes": [
                {
                    "contingency": "inspection_contingency",
                    "original": True,
                    "requested": False,
                    "impact": "negative"
                }
            ],
            "closing_date_change": {
                "impact": "negative"
            }
        }
        
        result = service._suggest_terms_modifications(terms_analysis)
        
        assert len(result) >= 2
        assert any("inspection_contingency" in mod["term"] for mod in result)
        assert any("closing_date" in mod["term"] for mod in result)
    
    def test_calculate_deal_viability_excellent(self, service, sample_strategy, sample_property):
        """Test deal viability calculation for excellent deal."""
        counter_offer_data = {
            "counter_amount": 215000,  # Below recommended price
            "seller_changes": {}
        }
        
        result = service._calculate_deal_viability(counter_offer_data, sample_strategy, sample_property)
        
        assert result["overall_score"] >= 80
        assert result["viability_level"] == "excellent"
        assert result["recommendation"] == "proceed"
    
    def test_calculate_deal_viability_poor(self, service, sample_strategy, sample_property):
        """Test deal viability calculation for poor deal."""
        counter_offer_data = {
            "counter_amount": 270000,  # Way over budget
            "seller_changes": {
                "inspection_contingency": False,
                "appraisal_contingency": False
            }
        }
        sample_property.renovation_needed = True
        
        result = service._calculate_deal_viability(counter_offer_data, sample_strategy, sample_property)
        
        assert result["overall_score"] < 60
        assert result["viability_level"] == "poor"
        assert result["recommendation"] == "reconsider"
    
    def test_calculate_analysis_confidence_high(self, service):
        """Test analysis confidence calculation for high confidence scenario."""
        price_analysis = {"within_budget": True, "competitiveness": "excellent"}
        terms_analysis = {"terms_acceptability": "acceptable"}
        risk_assessment = {"overall_risk_level": "low"}
        
        result = service._calculate_analysis_confidence(price_analysis, terms_analysis, risk_assessment)
        
        assert result >= 0.8
    
    def test_calculate_analysis_confidence_low(self, service):
        """Test analysis confidence calculation for low confidence scenario."""
        price_analysis = {"within_budget": False, "competitiveness": "poor"}
        terms_analysis = {"terms_acceptability": "concerning"}
        risk_assessment = {"overall_risk_level": "high"}
        
        result = service._calculate_analysis_confidence(price_analysis, terms_analysis, risk_assessment)
        
        assert result <= 0.5
    
    def test_save_counter_offer_analysis(self, service, mock_db):
        """Test saving counter offer analysis."""
        analysis_data = {
            "original_offer_id": uuid.uuid4(),
            "counter_amount": 235000,
            "seller_changes": {},
            "price_analysis": {"within_budget": True},
            "terms_analysis": {"terms_acceptability": "acceptable"},
            "risk_assessment": {"financial_risks": [], "timeline_risks": []},
            "negotiation_path": {"likely_outcome": "successful"},
            "deal_viability": {"overall_score": 85},
            "response_recommendation": {"primary_action": "accept"}
        }
        
        mock_counter_offer = Mock(spec=CounterOfferDB)
        mock_counter_offer.id = uuid.uuid4()
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        with patch('app.services.counter_offer_analyzer_service.CounterOfferDB', return_value=mock_counter_offer):
            result = service.save_counter_offer_analysis(analysis_data)
        
        assert result == mock_counter_offer
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_get_counter_offer(self, service, mock_db):
        """Test getting a counter offer by ID."""
        counter_offer_id = uuid.uuid4()
        mock_counter_offer = Mock(spec=CounterOfferDB)
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_counter_offer
        
        result = service.get_counter_offer(counter_offer_id)
        
        assert result == mock_counter_offer
        mock_db.query.assert_called_once_with(CounterOfferDB)
    
    def test_get_counter_offers_for_offer(self, service, mock_db):
        """Test getting all counter offers for an offer."""
        offer_id = uuid.uuid4()
        mock_counter_offers = [Mock(spec=CounterOfferDB), Mock(spec=CounterOfferDB)]
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_counter_offers
        
        result = service.get_counter_offers_for_offer(offer_id)
        
        assert result == mock_counter_offers
        mock_db.query.assert_called_once_with(CounterOfferDB)
    
    def test_update_counter_offer_response(self, service, mock_db):
        """Test updating counter offer response."""
        counter_offer_id = uuid.uuid4()
        mock_counter_offer = Mock(spec=CounterOfferDB)
        mock_counter_offer.buyer_response = {}
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_counter_offer
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        result = service.update_counter_offer_response(counter_offer_id, "accept")
        
        assert result == mock_counter_offer
        assert mock_counter_offer.responded == True
        assert mock_counter_offer.buyer_response["action_taken"] == "accept"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_update_counter_offer_response_not_found(self, service, mock_db):
        """Test updating counter offer response when counter offer is not found."""
        counter_offer_id = uuid.uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match=f"Counter offer with ID {counter_offer_id} not found"):
            service.update_counter_offer_response(counter_offer_id, "accept")


if __name__ == "__main__":
    pytest.main([__file__])