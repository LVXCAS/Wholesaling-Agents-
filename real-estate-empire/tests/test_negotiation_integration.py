"""
Integration tests for the complete negotiation system.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.property import PropertyDB
from app.models.negotiation import (
    NegotiationStrategyDB,
    OfferDB,
    CounterOfferDB,
    OfferTypeEnum,
    NegotiationStatusEnum,
    MarketConditionEnum,
    SellerMotivationEnum,
    NegotiationCoachingRequest
)
from app.services.negotiation_strategy_service import NegotiationStrategyService
from app.services.offer_generation_service import OfferGenerationService
from app.services.counter_offer_analyzer_service import CounterOfferAnalyzerService
from app.services.negotiation_coaching_service import NegotiationCoachingService


class TestNegotiationIntegration:
    """Integration tests for the complete negotiation workflow."""
    
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
            address="123 Integration Test St",
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
            days_on_market=60,
            renovation_needed=True
        )
        db_session.add(property_data)
        db_session.commit()
        db_session.refresh(property_data)
        return property_data
    
    @pytest.fixture
    def strategy_service(self, db_session):
        """Create a NegotiationStrategyService instance."""
        return NegotiationStrategyService(db_session)
    
    @pytest.fixture
    def offer_service(self, db_session):
        """Create an OfferGenerationService instance."""
        return OfferGenerationService(db_session)
    
    @pytest.fixture
    def counter_service(self, db_session):
        """Create a CounterOfferAnalyzerService instance."""
        return CounterOfferAnalyzerService(db_session)
    
    @pytest.fixture
    def coaching_service(self, db_session):
        """Create a NegotiationCoachingService instance."""
        return NegotiationCoachingService(db_session)
    
    def test_complete_negotiation_workflow(self, db_session, sample_property, 
                                         strategy_service, offer_service, 
                                         counter_service, coaching_service):
        """Test the complete negotiation workflow from strategy to coaching."""
        
        # Step 1: Generate negotiation strategy
        strategy_data = strategy_service.generate_strategy(sample_property.id)
        assert strategy_data is not None
        assert strategy_data["property_id"] == sample_property.id
        assert strategy_data["recommended_offer_price"] > 0
        assert strategy_data["max_offer_price"] > strategy_data["recommended_offer_price"]
        
        # Save the strategy
        saved_strategy = strategy_service.save_strategy(strategy_data)
        assert saved_strategy.id is not None
        
        # Step 2: Generate initial offer based on strategy
        offer_data = offer_service.generate_offer(saved_strategy.id, OfferTypeEnum.INITIAL)
        assert offer_data is not None
        assert offer_data["strategy_id"] == saved_strategy.id
        assert offer_data["property_id"] == sample_property.id
        assert offer_data["offer_amount"] > 0
        
        # Save the offer
        saved_offer = offer_service.save_offer(offer_data)
        assert saved_offer.id is not None
        
        # Step 3: Simulate seller counter offer
        counter_offer_data = {
            "counter_amount": offer_data["offer_amount"] + 15000,  # Seller wants $15k more
            "seller_changes": {
                "closing_date": (datetime.now() + timedelta(days=45)).isoformat(),
                "appraisal_contingency": False,
                "custom_terms": {
                    "seller_concessions": 2000
                }
            }
        }
        
        # Step 4: Analyze the counter offer
        analysis_result = counter_service.analyze_counter_offer(saved_offer.id, counter_offer_data)
        assert analysis_result is not None
        assert analysis_result["original_offer_id"] == saved_offer.id
        assert analysis_result["counter_amount"] == counter_offer_data["counter_amount"]
        assert "price_analysis" in analysis_result
        assert "terms_analysis" in analysis_result
        assert "risk_assessment" in analysis_result
        assert "response_recommendation" in analysis_result
        
        # Save the counter offer analysis
        saved_counter_offer = counter_service.save_counter_offer_analysis(analysis_result)
        assert saved_counter_offer.id is not None
        
        # Step 5: Generate coaching for the negotiation situation
        coaching_request = NegotiationCoachingRequest(
            property_id=sample_property.id,
            situation=f"Received counter offer of ${counter_offer_data['counter_amount']:,}",
            seller_response="They want more money and fewer contingencies",
            specific_concerns=["price", "contingencies", "timeline"]
        )
        
        coaching_response = coaching_service.generate_coaching(coaching_request)
        assert coaching_response is not None
        assert len(coaching_response.talking_points) > 0
        assert len(coaching_response.objection_responses) > 0
        assert len(coaching_response.value_propositions) > 0
        assert coaching_response.negotiation_script is not None
        assert coaching_response.recommended_approach is not None
        assert len(coaching_response.confidence_tips) > 0
        
        # Step 6: Verify data relationships and integrity
        # Check that strategy has offers
        db_session.refresh(saved_strategy)
        assert len(saved_strategy.offers) == 1
        assert saved_strategy.offers[0].id == saved_offer.id
        
        # Check that offer has counter offers
        db_session.refresh(saved_offer)
        assert len(saved_offer.counter_offers) == 1
        assert saved_offer.counter_offers[0].id == saved_counter_offer.id
        
        # Check that counter offer references original offer
        db_session.refresh(saved_counter_offer)
        assert saved_counter_offer.original_offer.id == saved_offer.id
        
        # Step 7: Test updating offer status based on analysis
        recommendation = analysis_result["response_recommendation"]["primary_action"]
        updated_offer = offer_service.update_offer_status(
            saved_offer.id, 
            NegotiationStatusEnum.COUNTER_OFFER,
            {"analysis_recommendation": recommendation}
        )
        assert updated_offer.status == NegotiationStatusEnum.COUNTER_OFFER
        assert updated_offer.response_received == True
        assert updated_offer.response_details["analysis_recommendation"] == recommendation
    
    def test_multiple_offers_workflow(self, db_session, sample_property, 
                                    strategy_service, offer_service):
        """Test generating multiple offer scenarios."""
        
        # Generate strategy
        strategy_data = strategy_service.generate_strategy(sample_property.id)
        saved_strategy = strategy_service.save_strategy(strategy_data)
        
        # Generate multiple offer scenarios
        offer_scenarios = offer_service.generate_multiple_offer_strategy(saved_strategy.id)
        
        assert len(offer_scenarios) >= 3  # Should have at least 3 scenarios
        
        scenario_names = [scenario["scenario_name"] for scenario in offer_scenarios]
        assert "Primary Offer" in scenario_names
        assert "Aggressive Offer" in scenario_names
        assert "Conservative Offer" in scenario_names
        
        # Verify price progression
        primary_offer = next(s for s in offer_scenarios if s["scenario_name"] == "Primary Offer")
        aggressive_offer = next(s for s in offer_scenarios if s["scenario_name"] == "Aggressive Offer")
        conservative_offer = next(s for s in offer_scenarios if s["scenario_name"] == "Conservative Offer")
        
        assert aggressive_offer["offer_amount"] > primary_offer["offer_amount"]
        assert conservative_offer["offer_amount"] < primary_offer["offer_amount"]
    
    def test_negotiation_coaching_phases(self, db_session, sample_property, coaching_service):
        """Test coaching for different negotiation phases."""
        
        phases = ["initial", "counter", "final", "closing"]
        
        for phase in phases:
            coaching = coaching_service.generate_situation_specific_coaching(
                sample_property.id, phase
            )
            
            assert coaching["phase"] == phase
            assert len(coaching["objectives"]) > 0
            assert len(coaching["key_messages"]) > 0
            assert len(coaching["tactics"]) > 0
            assert len(coaching["red_flags"]) > 0
            assert len(coaching["success_indicators"]) > 0
            
            # Verify phase-specific content
            if phase == "initial":
                objectives_text = " ".join(coaching["objectives"]).lower()
                assert "rapport" in objectives_text or "credibility" in objectives_text
            elif phase == "final":
                key_messages_text = " ".join(coaching["key_messages"]).lower()
                assert "final" in key_messages_text or "best" in key_messages_text
    
    def test_offer_competitiveness_analysis(self, db_session, sample_property, 
                                          strategy_service, offer_service):
        """Test offer competitiveness analysis integration."""
        
        # Generate strategy and offer
        strategy_data = strategy_service.generate_strategy(sample_property.id)
        saved_strategy = strategy_service.save_strategy(strategy_data)
        
        offer_data = offer_service.generate_offer(saved_strategy.id, OfferTypeEnum.INITIAL)
        
        # Analyze competitiveness
        competitiveness = offer_service.calculate_offer_competitiveness(offer_data)
        
        assert "overall_score" in competitiveness
        assert "strengths" in competitiveness
        assert "weaknesses" in competitiveness
        assert "recommendations" in competitiveness
        assert 0 <= competitiveness["overall_score"] <= 100
        assert isinstance(competitiveness["recommendations"], list)
    
    def test_strategy_market_adaptation(self, db_session, sample_property, strategy_service):
        """Test that strategies adapt to different market conditions."""
        
        # Test with different property characteristics
        properties = []
        
        # Buyer's market property (long DOM)
        buyers_market_prop = PropertyDB(
            id=uuid.uuid4(),
            address="456 Buyers Market St",
            city="Test City",
            state="TS",
            zip_code="12345",
            property_type="single_family",
            listing_price=300000,
            assessed_value=290000,
            days_on_market=120,  # Long DOM indicates buyer's market
            renovation_needed=False
        )
        db_session.add(buyers_market_prop)
        
        # Seller's market property (short DOM)
        sellers_market_prop = PropertyDB(
            id=uuid.uuid4(),
            address="789 Sellers Market St",
            city="Test City",
            state="TS",
            zip_code="12345",
            property_type="single_family",
            listing_price=300000,
            assessed_value=290000,
            days_on_market=15,  # Short DOM indicates seller's market
            renovation_needed=False
        )
        db_session.add(sellers_market_prop)
        
        db_session.commit()
        
        # Generate strategies for both properties
        buyers_strategy = strategy_service.generate_strategy(buyers_market_prop.id)
        sellers_strategy = strategy_service.generate_strategy(sellers_market_prop.id)
        
        # Verify different market conditions are detected
        assert buyers_strategy["market_condition"] == MarketConditionEnum.BUYERS_MARKET
        assert sellers_strategy["market_condition"] == MarketConditionEnum.SELLERS_MARKET
        
        # Verify different negotiation approaches
        assert buyers_strategy["negotiation_approach"] in ["aggressive", "moderate"]
        assert sellers_strategy["negotiation_approach"] in ["conservative", "moderate"]
        
        # Verify different offer prices (buyer's market should be more aggressive)
        buyers_offer_ratio = buyers_strategy["recommended_offer_price"] / buyers_market_prop.listing_price
        sellers_offer_ratio = sellers_strategy["recommended_offer_price"] / sellers_market_prop.listing_price
        
        assert buyers_offer_ratio < sellers_offer_ratio  # More aggressive in buyer's market
    
    def test_error_handling_and_recovery(self, db_session, strategy_service, 
                                       offer_service, counter_service):
        """Test error handling throughout the negotiation workflow."""
        
        # Test with non-existent property
        fake_property_id = uuid.uuid4()
        
        with pytest.raises(ValueError, match="Property.*not found"):
            strategy_service.generate_strategy(fake_property_id)
        
        # Test with non-existent strategy
        fake_strategy_id = uuid.uuid4()
        
        with pytest.raises(ValueError, match="Negotiation strategy.*not found"):
            offer_service.generate_offer(fake_strategy_id)
        
        # Test with non-existent offer
        fake_offer_id = uuid.uuid4()
        
        with pytest.raises(ValueError, match="Original offer.*not found"):
            counter_service.analyze_counter_offer(fake_offer_id, {"counter_amount": 250000})
    
    def test_data_consistency_and_validation(self, db_session, sample_property, 
                                           strategy_service, offer_service):
        """Test data consistency and validation across the workflow."""
        
        # Generate strategy
        strategy_data = strategy_service.generate_strategy(sample_property.id)
        
        # Validate strategy data consistency
        assert strategy_data["recommended_offer_price"] <= strategy_data["max_offer_price"]
        assert 0 <= strategy_data["confidence_score"] <= 1
        assert strategy_data["market_condition"] in [e.value for e in MarketConditionEnum]
        assert strategy_data["seller_motivation"] in [e.value for e in SellerMotivationEnum]
        
        # Save strategy and generate offer
        saved_strategy = strategy_service.save_strategy(strategy_data)
        offer_data = offer_service.generate_offer(saved_strategy.id)
        
        # Validate offer data consistency
        assert offer_data["offer_amount"] > 0
        assert offer_data["earnest_money"] > 0
        assert offer_data["down_payment"] > 0
        assert offer_data["inspection_period"] > 0
        assert offer_data["closing_date"] > datetime.now()
        
        # Validate offer amount is within strategy bounds
        assert offer_data["offer_amount"] <= saved_strategy.max_offer_price
        
        # Save offer and verify database consistency
        saved_offer = offer_service.save_offer(offer_data)
        
        # Verify relationships
        db_session.refresh(saved_strategy)
        db_session.refresh(saved_offer)
        
        assert saved_offer.strategy_id == saved_strategy.id
        assert saved_offer.property_id == sample_property.id
        assert saved_strategy.property_id == sample_property.id
        
        # Verify foreign key constraints
        assert saved_offer.strategy is not None
        assert saved_offer.property is not None
        assert saved_strategy.property is not None


if __name__ == "__main__":
    pytest.main([__file__])