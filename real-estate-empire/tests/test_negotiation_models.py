"""
Unit tests for the Negotiation Models.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.core.database import Base
from app.models.negotiation import (
    NegotiationStrategyDB,
    OfferDB,
    CounterOfferDB,
    NegotiationStrategyCreate,
    NegotiationStrategyResponse,
    OfferCreate,
    OfferResponse,
    CounterOfferCreate,
    CounterOfferResponse,
    NegotiationCoachingRequest,
    NegotiationCoachingResponse,
    NegotiationStatusEnum,
    OfferTypeEnum,
    SellerMotivationEnum,
    MarketConditionEnum
)
from app.models.property import PropertyDB


class TestNegotiationModels:
    """Test cases for negotiation models."""
    
    @pytest.fixture(scope="function")
    def db_session(self):
        """Create an in-memory SQLite database for testing."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()
    
    @pytest.fixture
    def sample_property(self, db_session):
        """Create a sample property in the database."""
        property_data = PropertyDB(
            id=uuid.uuid4(),
            address="123 Test St",
            city="Test City",
            state="TS",
            zip_code="12345",
            property_type="single_family",
            listing_price=250000,
            assessed_value=240000
        )
        db_session.add(property_data)
        db_session.commit()
        db_session.refresh(property_data)
        return property_data
    
    def test_negotiation_strategy_db_creation(self, db_session, sample_property):
        """Test creating a NegotiationStrategyDB instance."""
        strategy = NegotiationStrategyDB(
            property_id=sample_property.id,
            strategy_name="Test Strategy",
            recommended_offer_price=220000,
            max_offer_price=240000,
            negotiation_approach="moderate",
            market_condition=MarketConditionEnum.BALANCED,
            seller_motivation=SellerMotivationEnum.MODERATE,
            confidence_score=0.7,
            talking_points=["Point 1", "Point 2"],
            value_propositions=["Prop 1", "Prop 2"],
            potential_objections=[{"objection": "Price too low", "response": "Market analysis"}],
            contingencies=["Inspection", "Appraisal"],
            risk_assessment={"overall_risk": "medium", "factors": ["market"]}
        )
        
        db_session.add(strategy)
        db_session.commit()
        db_session.refresh(strategy)
        
        # Verify the strategy was created
        assert strategy.id is not None
        assert strategy.property_id == sample_property.id
        assert strategy.strategy_name == "Test Strategy"
        assert strategy.recommended_offer_price == 220000
        assert strategy.max_offer_price == 240000
        assert strategy.negotiation_approach == "moderate"
        assert strategy.market_condition == MarketConditionEnum.BALANCED
        assert strategy.seller_motivation == SellerMotivationEnum.MODERATE
        assert strategy.confidence_score == 0.7
        assert strategy.created_at is not None
        assert strategy.updated_at is not None
        
        # Verify JSON fields
        assert len(strategy.talking_points) == 2
        assert strategy.talking_points[0] == "Point 1"
        assert len(strategy.value_propositions) == 2
        assert len(strategy.potential_objections) == 1
        assert strategy.potential_objections[0]["objection"] == "Price too low"
        assert len(strategy.contingencies) == 2
        assert strategy.risk_assessment["overall_risk"] == "medium"
    
    def test_negotiation_strategy_db_required_fields(self, db_session, sample_property):
        """Test that required fields are enforced."""
        # Test missing property_id
        with pytest.raises(IntegrityError):
            strategy = NegotiationStrategyDB(
                strategy_name="Test Strategy",
                recommended_offer_price=220000,
                max_offer_price=240000,
                negotiation_approach="moderate"
            )
            db_session.add(strategy)
            db_session.commit()
    
    def test_negotiation_strategy_db_defaults(self, db_session, sample_property):
        """Test default values for optional fields."""
        strategy = NegotiationStrategyDB(
            property_id=sample_property.id,
            strategy_name="Test Strategy",
            recommended_offer_price=220000,
            max_offer_price=240000,
            negotiation_approach="moderate"
        )
        
        db_session.add(strategy)
        db_session.commit()
        db_session.refresh(strategy)
        
        # Check defaults
        assert strategy.market_condition == MarketConditionEnum.BALANCED
        assert strategy.seller_motivation == SellerMotivationEnum.MODERATE
        assert strategy.confidence_score == 0.5
    
    def test_offer_db_creation(self, db_session, sample_property):
        """Test creating an OfferDB instance."""
        # First create a strategy
        strategy = NegotiationStrategyDB(
            property_id=sample_property.id,
            strategy_name="Test Strategy",
            recommended_offer_price=220000,
            max_offer_price=240000,
            negotiation_approach="moderate"
        )
        db_session.add(strategy)
        db_session.commit()
        db_session.refresh(strategy)
        
        # Create offer
        offer = OfferDB(
            strategy_id=strategy.id,
            property_id=sample_property.id,
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
            custom_terms={"as_is": True},
            contingencies=["Inspection", "Appraisal"]
        )
        
        db_session.add(offer)
        db_session.commit()
        db_session.refresh(offer)
        
        # Verify the offer was created
        assert offer.id is not None
        assert offer.strategy_id == strategy.id
        assert offer.property_id == sample_property.id
        assert offer.offer_type == OfferTypeEnum.INITIAL
        assert offer.offer_amount == 220000
        assert offer.earnest_money == 3000
        assert offer.down_payment == 44000
        assert offer.financing_type == "conventional"
        assert offer.closing_date is not None
        assert offer.inspection_period == 10
        assert offer.appraisal_contingency == True
        assert offer.financing_contingency == True
        assert offer.inspection_contingency == True
        assert offer.status == NegotiationStatusEnum.INITIATED
        assert offer.response_received == False
        assert offer.custom_terms["as_is"] == True
        assert len(offer.contingencies) == 2
    
    def test_offer_db_relationships(self, db_session, sample_property):
        """Test relationships between Offer and other models."""
        # Create strategy
        strategy = NegotiationStrategyDB(
            property_id=sample_property.id,
            strategy_name="Test Strategy",
            recommended_offer_price=220000,
            max_offer_price=240000,
            negotiation_approach="moderate"
        )
        db_session.add(strategy)
        db_session.commit()
        
        # Create offer
        offer = OfferDB(
            strategy_id=strategy.id,
            property_id=sample_property.id,
            offer_amount=220000
        )
        db_session.add(offer)
        db_session.commit()
        db_session.refresh(offer)
        
        # Test relationships
        assert offer.strategy is not None
        assert offer.strategy.id == strategy.id
        assert offer.property is not None
        assert offer.property.id == sample_property.id
        
        # Test reverse relationship
        assert len(strategy.offers) == 1
        assert strategy.offers[0].id == offer.id
    
    def test_counter_offer_db_creation(self, db_session, sample_property):
        """Test creating a CounterOfferDB instance."""
        # Create strategy and offer first
        strategy = NegotiationStrategyDB(
            property_id=sample_property.id,
            strategy_name="Test Strategy",
            recommended_offer_price=220000,
            max_offer_price=240000,
            negotiation_approach="moderate"
        )
        db_session.add(strategy)
        db_session.commit()
        
        offer = OfferDB(
            strategy_id=strategy.id,
            property_id=sample_property.id,
            offer_amount=220000
        )
        db_session.add(offer)
        db_session.commit()
        db_session.refresh(offer)
        
        # Create counter offer
        counter_offer = CounterOfferDB(
            original_offer_id=offer.id,
            counter_amount=235000,
            seller_changes={"closing_date": "2024-03-15", "appraisal_contingency": False},
            buyer_response={"action": "consider"},
            analysis_result={"recommendation": "counter", "confidence": 0.8},
            recommended_response="counter",
            risk_factors=["Price above budget", "Waived appraisal"]
        )
        
        db_session.add(counter_offer)
        db_session.commit()
        db_session.refresh(counter_offer)
        
        # Verify the counter offer was created
        assert counter_offer.id is not None
        assert counter_offer.original_offer_id == offer.id
        assert counter_offer.counter_amount == 235000
        assert counter_offer.seller_changes["closing_date"] == "2024-03-15"
        assert counter_offer.seller_changes["appraisal_contingency"] == False
        assert counter_offer.buyer_response["action"] == "consider"
        assert counter_offer.analysis_result["recommendation"] == "counter"
        assert counter_offer.recommended_response == "counter"
        assert len(counter_offer.risk_factors) == 2
        assert counter_offer.status == NegotiationStatusEnum.IN_PROGRESS
        assert counter_offer.responded == False
    
    def test_counter_offer_db_relationships(self, db_session, sample_property):
        """Test relationships for CounterOfferDB."""
        # Create the chain: strategy -> offer -> counter_offer
        strategy = NegotiationStrategyDB(
            property_id=sample_property.id,
            strategy_name="Test Strategy",
            recommended_offer_price=220000,
            max_offer_price=240000,
            negotiation_approach="moderate"
        )
        db_session.add(strategy)
        db_session.commit()
        
        offer = OfferDB(
            strategy_id=strategy.id,
            property_id=sample_property.id,
            offer_amount=220000
        )
        db_session.add(offer)
        db_session.commit()
        
        counter_offer = CounterOfferDB(
            original_offer_id=offer.id,
            counter_amount=235000
        )
        db_session.add(counter_offer)
        db_session.commit()
        db_session.refresh(counter_offer)
        
        # Test relationships
        assert counter_offer.original_offer is not None
        assert counter_offer.original_offer.id == offer.id
        
        # Test reverse relationship
        db_session.refresh(offer)
        assert len(offer.counter_offers) == 1
        assert offer.counter_offers[0].id == counter_offer.id
    
    def test_negotiation_strategy_create_pydantic(self):
        """Test NegotiationStrategyCreate Pydantic model."""
        strategy_data = {
            "property_id": uuid.uuid4(),
            "strategy_name": "Test Strategy",
            "recommended_offer_price": 220000,
            "max_offer_price": 240000,
            "negotiation_approach": "moderate",
            "market_condition": MarketConditionEnum.BALANCED,
            "seller_motivation": SellerMotivationEnum.MODERATE,
            "talking_points": ["Point 1", "Point 2"],
            "value_propositions": ["Prop 1", "Prop 2"],
            "potential_objections": [{"objection": "Price", "response": "Analysis"}],
            "contingencies": ["Inspection"],
            "confidence_score": 0.8,
            "risk_assessment": {"level": "low"}
        }
        
        strategy = NegotiationStrategyCreate(**strategy_data)
        
        assert strategy.property_id == strategy_data["property_id"]
        assert strategy.strategy_name == "Test Strategy"
        assert strategy.recommended_offer_price == 220000
        assert strategy.max_offer_price == 240000
        assert strategy.negotiation_approach == "moderate"
        assert strategy.market_condition == MarketConditionEnum.BALANCED
        assert strategy.seller_motivation == SellerMotivationEnum.MODERATE
        assert len(strategy.talking_points) == 2
        assert len(strategy.value_propositions) == 2
        assert len(strategy.potential_objections) == 1
        assert len(strategy.contingencies) == 1
        assert strategy.confidence_score == 0.8
        assert strategy.risk_assessment["level"] == "low"
    
    def test_negotiation_strategy_create_validation(self):
        """Test validation in NegotiationStrategyCreate."""
        # Test confidence score validation
        with pytest.raises(ValueError):
            NegotiationStrategyCreate(
                property_id=uuid.uuid4(),
                strategy_name="Test",
                recommended_offer_price=220000,
                max_offer_price=240000,
                negotiation_approach="moderate",
                confidence_score=1.5  # Invalid: > 1
            )
        
        with pytest.raises(ValueError):
            NegotiationStrategyCreate(
                property_id=uuid.uuid4(),
                strategy_name="Test",
                recommended_offer_price=220000,
                max_offer_price=240000,
                negotiation_approach="moderate",
                confidence_score=-0.1  # Invalid: < 0
            )
    
    def test_offer_create_pydantic(self):
        """Test OfferCreate Pydantic model."""
        offer_data = {
            "strategy_id": uuid.uuid4(),
            "property_id": uuid.uuid4(),
            "offer_type": OfferTypeEnum.INITIAL,
            "offer_amount": 220000,
            "earnest_money": 3000,
            "down_payment": 44000,
            "financing_type": "conventional",
            "closing_date": datetime.now() + timedelta(days=30),
            "inspection_period": 10,
            "appraisal_contingency": True,
            "financing_contingency": True,
            "inspection_contingency": True,
            "custom_terms": {"as_is": True},
            "contingencies": ["Inspection", "Appraisal"]
        }
        
        offer = OfferCreate(**offer_data)
        
        assert offer.strategy_id == offer_data["strategy_id"]
        assert offer.property_id == offer_data["property_id"]
        assert offer.offer_type == OfferTypeEnum.INITIAL
        assert offer.offer_amount == 220000
        assert offer.earnest_money == 3000
        assert offer.down_payment == 44000
        assert offer.financing_type == "conventional"
        assert offer.closing_date is not None
        assert offer.inspection_period == 10
        assert offer.appraisal_contingency == True
        assert offer.financing_contingency == True
        assert offer.inspection_contingency == True
        assert offer.custom_terms["as_is"] == True
        assert len(offer.contingencies) == 2
    
    def test_counter_offer_create_pydantic(self):
        """Test CounterOfferCreate Pydantic model."""
        counter_data = {
            "original_offer_id": uuid.uuid4(),
            "counter_amount": 235000,
            "seller_changes": {"closing_date": "2024-03-15"},
            "buyer_response": {"action": "consider"},
            "analysis_result": {"recommendation": "counter"},
            "recommended_response": "counter",
            "risk_factors": ["Price above budget"]
        }
        
        counter_offer = CounterOfferCreate(**counter_data)
        
        assert counter_offer.original_offer_id == counter_data["original_offer_id"]
        assert counter_offer.counter_amount == 235000
        assert counter_offer.seller_changes["closing_date"] == "2024-03-15"
        assert counter_offer.buyer_response["action"] == "consider"
        assert counter_offer.analysis_result["recommendation"] == "counter"
        assert counter_offer.recommended_response == "counter"
        assert len(counter_offer.risk_factors) == 1
    
    def test_negotiation_coaching_request_pydantic(self):
        """Test NegotiationCoachingRequest Pydantic model."""
        request_data = {
            "property_id": uuid.uuid4(),
            "situation": "Initial offer presentation",
            "seller_response": "Price seems low",
            "specific_concerns": ["price", "timeline"]
        }
        
        request = NegotiationCoachingRequest(**request_data)
        
        assert request.property_id == request_data["property_id"]
        assert request.situation == "Initial offer presentation"
        assert request.seller_response == "Price seems low"
        assert len(request.specific_concerns) == 2
        assert "price" in request.specific_concerns
    
    def test_negotiation_coaching_response_pydantic(self):
        """Test NegotiationCoachingResponse Pydantic model."""
        response_data = {
            "talking_points": ["Point 1", "Point 2"],
            "objection_responses": {"Price too low": "Market analysis shows..."},
            "value_propositions": ["Quick closing", "Cash offer"],
            "negotiation_script": "Thank you for considering our offer...",
            "recommended_approach": "collaborative",
            "confidence_tips": ["Stay calm", "Listen actively"]
        }
        
        response = NegotiationCoachingResponse(**response_data)
        
        assert len(response.talking_points) == 2
        assert "Price too low" in response.objection_responses
        assert len(response.value_propositions) == 2
        assert response.negotiation_script.startswith("Thank you")
        assert response.recommended_approach == "collaborative"
        assert len(response.confidence_tips) == 2
    
    def test_enum_values(self):
        """Test that all enum values are valid."""
        # Test NegotiationStatusEnum
        assert NegotiationStatusEnum.INITIATED == "initiated"
        assert NegotiationStatusEnum.IN_PROGRESS == "in_progress"
        assert NegotiationStatusEnum.COUNTER_OFFER == "counter_offer"
        assert NegotiationStatusEnum.ACCEPTED == "accepted"
        assert NegotiationStatusEnum.REJECTED == "rejected"
        assert NegotiationStatusEnum.STALLED == "stalled"
        assert NegotiationStatusEnum.CLOSED == "closed"
        
        # Test OfferTypeEnum
        assert OfferTypeEnum.INITIAL == "initial"
        assert OfferTypeEnum.COUNTER == "counter"
        assert OfferTypeEnum.FINAL == "final"
        assert OfferTypeEnum.BACKUP == "backup"
        
        # Test SellerMotivationEnum
        assert SellerMotivationEnum.LOW == "low"
        assert SellerMotivationEnum.MODERATE == "moderate"
        assert SellerMotivationEnum.HIGH == "high"
        assert SellerMotivationEnum.URGENT == "urgent"
        
        # Test MarketConditionEnum
        assert MarketConditionEnum.BUYERS_MARKET == "buyers_market"
        assert MarketConditionEnum.SELLERS_MARKET == "sellers_market"
        assert MarketConditionEnum.BALANCED == "balanced"
    
    def test_model_repr_methods(self, db_session, sample_property):
        """Test __repr__ methods for debugging."""
        strategy = NegotiationStrategyDB(
            property_id=sample_property.id,
            strategy_name="Test Strategy",
            recommended_offer_price=220000,
            max_offer_price=240000,
            negotiation_approach="moderate"
        )
        db_session.add(strategy)
        db_session.commit()
        db_session.refresh(strategy)
        
        offer = OfferDB(
            strategy_id=strategy.id,
            property_id=sample_property.id,
            offer_amount=220000
        )
        db_session.add(offer)
        db_session.commit()
        db_session.refresh(offer)
        
        counter_offer = CounterOfferDB(
            original_offer_id=offer.id,
            counter_amount=235000
        )
        db_session.add(counter_offer)
        db_session.commit()
        db_session.refresh(counter_offer)
        
        # Test repr methods
        strategy_repr = repr(strategy)
        assert "NegotiationStrategyDB" in strategy_repr
        assert str(strategy.id) in strategy_repr
        assert "Test Strategy" in strategy_repr
        
        offer_repr = repr(offer)
        assert "OfferDB" in offer_repr
        assert str(offer.id) in offer_repr
        assert "$220000" in offer_repr
        
        counter_repr = repr(counter_offer)
        assert "CounterOfferDB" in counter_repr
        assert str(counter_offer.id) in counter_repr
        assert "$235000" in counter_repr
    
    def test_json_field_serialization(self, db_session, sample_property):
        """Test that JSON fields are properly serialized and deserialized."""
        complex_data = {
            "talking_points": ["Point 1", "Point 2", "Point 3"],
            "value_propositions": ["Prop A", "Prop B"],
            "potential_objections": [
                {"objection": "Price too low", "response": "Market analysis"},
                {"objection": "Need more time", "response": "Flexible timeline"}
            ],
            "contingencies": ["Inspection", "Appraisal", "Financing"],
            "risk_assessment": {
                "overall_risk": "medium",
                "factors": ["market", "property"],
                "mitigation": ["thorough_analysis", "backup_plan"]
            }
        }
        
        strategy = NegotiationStrategyDB(
            property_id=sample_property.id,
            strategy_name="Complex Strategy",
            recommended_offer_price=220000,
            max_offer_price=240000,
            negotiation_approach="moderate",
            **complex_data
        )
        
        db_session.add(strategy)
        db_session.commit()
        db_session.refresh(strategy)
        
        # Verify JSON fields are properly stored and retrieved
        assert len(strategy.talking_points) == 3
        assert strategy.talking_points[2] == "Point 3"
        assert len(strategy.value_propositions) == 2
        assert strategy.value_propositions[1] == "Prop B"
        assert len(strategy.potential_objections) == 2
        assert strategy.potential_objections[1]["objection"] == "Need more time"
        assert len(strategy.contingencies) == 3
        assert strategy.contingencies[2] == "Financing"
        assert strategy.risk_assessment["overall_risk"] == "medium"
        assert len(strategy.risk_assessment["factors"]) == 2
        assert len(strategy.risk_assessment["mitigation"]) == 2


if __name__ == "__main__":
    pytest.main([__file__])