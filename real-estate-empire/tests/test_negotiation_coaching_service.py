"""
Unit tests for the Negotiation Coaching Service.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock

from sqlalchemy.orm import Session
from app.services.negotiation_coaching_service import NegotiationCoachingService
from app.models.property import PropertyDB, PropertyAnalysisDB
from app.models.lead import PropertyLeadDB
from app.models.negotiation import (
    NegotiationStrategyDB,
    MarketConditionEnum,
    SellerMotivationEnum,
    NegotiationCoachingRequest
)


class TestNegotiationCoachingService:
    """Test cases for NegotiationCoachingService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """Create a NegotiationCoachingService instance."""
        return NegotiationCoachingService(mock_db)
    
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
            days_on_market=75,
            renovation_needed=True,
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
            market_condition=MarketConditionEnum.BUYERS_MARKET,
            seller_motivation=SellerMotivationEnum.HIGH,
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
            repair_estimate=25000,
            confidence_score=0.8,
            comparable_count=4,
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
    
    @pytest.fixture
    def sample_coaching_request(self, sample_property):
        """Create a sample coaching request."""
        return NegotiationCoachingRequest(
            property_id=sample_property.id,
            situation="Initial offer presentation to motivated seller",
            seller_response="They said the price seems low",
            specific_concerns=["price", "timeline"]
        )
    
    def test_generate_coaching_success(self, service, mock_db, sample_property, 
                                     sample_strategy, sample_analysis, sample_lead, sample_coaching_request):
        """Test successful coaching generation."""
        # Setup mocks
        sample_strategy.property_id = sample_property.id
        sample_analysis.property_id = sample_property.id
        sample_lead.property_id = sample_property.id
        
        mock_db.query.return_value.filter.return_value.first.return_value = sample_property
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.side_effect = [
            sample_strategy,  # Latest strategy
            sample_analysis   # Latest analysis
        ]
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_property,  # Property query
            sample_lead       # Lead query (after strategy and analysis queries)
        ]
        
        # Execute
        result = service.generate_coaching(sample_coaching_request)
        
        # Verify
        assert result is not None
        assert len(result.talking_points) > 0
        assert len(result.objection_responses) > 0
        assert len(result.value_propositions) > 0
        assert result.negotiation_script is not None
        assert result.recommended_approach is not None
        assert len(result.confidence_tips) > 0
        
        # Check that talking points include property-specific information
        talking_points_text = " ".join(result.talking_points).lower()
        assert "75 days" in talking_points_text or "market" in talking_points_text
        
        # Check that objection responses include price objection
        assert "Price is too low" in result.objection_responses or "price" in str(result.objection_responses).lower()
    
    def test_generate_coaching_property_not_found(self, service, mock_db, sample_coaching_request):
        """Test coaching generation when property is not found."""
        # Setup mock
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute and verify
        with pytest.raises(ValueError, match=f"Property with ID {sample_coaching_request.property_id} not found"):
            service.generate_coaching(sample_coaching_request)
    
    def test_generate_talking_points_with_strategy(self, service, sample_property, sample_strategy, sample_analysis):
        """Test talking points generation with strategy and analysis."""
        result = service._generate_talking_points(
            sample_property, sample_strategy, sample_analysis, "Initial offer"
        )
        
        assert len(result) > 0
        talking_points_text = " ".join(result).lower()
        
        # Should include days on market
        assert "75 days" in talking_points_text
        
        # Should include renovation mention
        assert "renovation" in talking_points_text or "repair" in talking_points_text
        
        # Should include market condition
        assert "buyer" in talking_points_text or "market" in talking_points_text
        
        # Should include repair estimate
        assert "25,000" in talking_points_text or "repair" in talking_points_text
    
    def test_generate_talking_points_without_strategy(self, service, sample_property):
        """Test talking points generation without strategy."""
        result = service._generate_talking_points(
            sample_property, None, None, "Counter offer situation"
        )
        
        assert len(result) > 0
        # Should still include basic talking points
        talking_points_text = " ".join(result).lower()
        assert "close" in talking_points_text or "financing" in talking_points_text
    
    def test_generate_objection_responses_basic(self, service, sample_property, sample_strategy):
        """Test basic objection responses generation."""
        result = service._generate_objection_responses(
            sample_property, sample_strategy, None, None
        )
        
        assert len(result) > 0
        assert "Price is too low" in result
        assert "I can get more from another buyer" in result
        assert "I need more time to think" in result
        
        # Check response quality
        price_response = result["Price is too low"]
        assert len(price_response) > 50  # Should be substantial response
        assert "market" in price_response.lower() or "analysis" in price_response.lower()
    
    def test_generate_objection_responses_with_seller_response(self, service, sample_property, sample_strategy):
        """Test objection responses with seller response."""
        seller_response = "Your price is way too low for this property"
        
        result = service._generate_objection_responses(
            sample_property, sample_strategy, seller_response, None
        )
        
        # Should include response-specific objection
        assert any("too low" in key.lower() for key in result.keys())
    
    def test_generate_objection_responses_with_concerns(self, service, sample_property, sample_strategy):
        """Test objection responses with specific concerns."""
        concerns = ["commission", "repair costs"]
        
        result = service._generate_objection_responses(
            sample_property, sample_strategy, None, concerns
        )
        
        # Should include concern-specific responses
        concern_keys = [key for key in result.keys() if "concern" in key.lower()]
        assert len(concern_keys) >= 1
    
    def test_generate_value_propositions_basic(self, service, sample_property, sample_strategy):
        """Test basic value propositions generation."""
        result = service._generate_value_propositions(
            sample_property, sample_strategy, "Initial offer"
        )
        
        assert len(result) > 0
        value_props_text = " ".join(result).lower()
        
        # Should include key value propositions
        assert "cash" in value_props_text or "financing" in value_props_text
        assert "commission" in value_props_text
        assert "as-is" in value_props_text or "repair" in value_props_text
    
    def test_generate_value_propositions_situation_specific(self, service, sample_property, sample_strategy):
        """Test situation-specific value propositions."""
        result = service._generate_value_propositions(
            sample_property, sample_strategy, "Foreclosure situation"
        )
        
        value_props_text = " ".join(result).lower()
        assert "foreclosure" in value_props_text or "credit" in value_props_text
    
    def test_generate_negotiation_script_initial(self, service, sample_property, sample_strategy):
        """Test negotiation script generation for initial offer."""
        talking_points = ["Property has been on market 75 days", "We can close quickly"]
        value_props = ["Cash offer", "No commissions"]
        
        result = service._generate_negotiation_script(
            sample_property, sample_strategy, "initial offer", talking_points, value_props
        )
        
        assert len(result) > 100  # Should be substantial script
        script_lower = result.lower()
        
        # Should include key sections
        assert "opening" in script_lower
        assert "key points" in script_lower or "talking points" in script_lower
        assert "value" in script_lower
        assert "closing" in script_lower
    
    def test_generate_negotiation_script_counter_offer(self, service, sample_property, sample_strategy):
        """Test negotiation script generation for counter offer."""
        talking_points = ["We want to find mutual solution"]
        value_props = ["Speed and certainty"]
        
        result = service._generate_negotiation_script(
            sample_property, sample_strategy, "counter offer received", talking_points, value_props
        )
        
        script_lower = result.lower()
        assert "counter offer" in script_lower
        assert "mutual" in script_lower or "agreement" in script_lower
    
    def test_determine_recommended_approach_with_strategy(self, service, sample_property, sample_strategy):
        """Test recommended approach determination with strategy."""
        # Test different situations
        result1 = service._determine_recommended_approach(sample_property, sample_strategy, "initial contact")
        assert result1 == "consultative"
        
        result2 = service._determine_recommended_approach(sample_property, sample_strategy, "final offer")
        assert result2 == "direct"
        
        result3 = service._determine_recommended_approach(sample_property, sample_strategy, "counter offer")
        assert result3 == "collaborative"
        
        result4 = service._determine_recommended_approach(sample_property, sample_strategy, "urgent foreclosure")
        assert result4 == "empathetic"
    
    def test_determine_recommended_approach_without_strategy(self, service, sample_property):
        """Test recommended approach determination without strategy."""
        result = service._determine_recommended_approach(sample_property, None, "general negotiation")
        assert result == "moderate"  # Should default to moderate
    
    def test_generate_confidence_tips_basic(self, service):
        """Test basic confidence tips generation."""
        result = service._generate_confidence_tips("Initial negotiation", None)
        
        assert len(result) >= 5  # Should have at least 5 basic tips
        tips_text = " ".join(result).lower()
        
        # Should include key confidence concepts
        assert "professional" in tips_text or "calm" in tips_text
        assert "listen" in tips_text
        assert "preparation" in tips_text or "prepared" in tips_text
    
    def test_generate_confidence_tips_nervous_situation(self, service):
        """Test confidence tips for nervous situation."""
        result = service._generate_confidence_tips("I'm nervous about this negotiation", None)
        
        tips_text = " ".join(result).lower()
        assert "nervous" in tips_text or "preparation" in tips_text
        assert "practice" in tips_text
    
    def test_generate_confidence_tips_with_concerns(self, service):
        """Test confidence tips with specific concerns."""
        concerns = ["price objections", "time pressure"]
        result = service._generate_confidence_tips("Difficult negotiation", concerns)
        
        tips_text = " ".join(result).lower()
        assert "price" in tips_text or "comparable" in tips_text
        assert "time" in tips_text or "speed" in tips_text
    
    def test_generate_situation_specific_coaching_initial(self, service, mock_db, sample_property, sample_strategy):
        """Test situation-specific coaching for initial phase."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = sample_property
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = sample_strategy
        
        result = service.generate_situation_specific_coaching(sample_property.id, "initial")
        
        assert result["phase"] == "initial"
        assert len(result["objectives"]) > 0
        assert len(result["key_messages"]) > 0
        assert len(result["tactics"]) > 0
        assert len(result["red_flags"]) > 0
        assert len(result["success_indicators"]) > 0
        
        # Check content relevance
        objectives_text = " ".join(result["objectives"]).lower()
        assert "rapport" in objectives_text or "credibility" in objectives_text
    
    def test_generate_situation_specific_coaching_counter(self, service, mock_db, sample_property, sample_strategy):
        """Test situation-specific coaching for counter phase."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = sample_property
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = sample_strategy
        
        result = service.generate_situation_specific_coaching(sample_property.id, "counter")
        
        assert result["phase"] == "counter"
        
        # Check counter-specific content
        objectives_text = " ".join(result["objectives"]).lower()
        assert "gap" in objectives_text or "creative" in objectives_text
        
        tactics_text = " ".join(result["tactics"]).lower()
        assert "acknowledge" in tactics_text or "what if" in tactics_text
    
    def test_generate_situation_specific_coaching_final(self, service, mock_db, sample_property, sample_strategy):
        """Test situation-specific coaching for final phase."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = sample_property
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = sample_strategy
        
        result = service.generate_situation_specific_coaching(sample_property.id, "final")
        
        assert result["phase"] == "final"
        
        # Check final-specific content
        objectives_text = " ".join(result["objectives"]).lower()
        assert "final" in objectives_text or "walkaway" in objectives_text
        
        key_messages_text = " ".join(result["key_messages"]).lower()
        assert "final" in key_messages_text or "best" in key_messages_text
    
    def test_generate_situation_specific_coaching_closing(self, service, mock_db, sample_property, sample_strategy):
        """Test situation-specific coaching for closing phase."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = sample_property
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = sample_strategy
        
        result = service.generate_situation_specific_coaching(sample_property.id, "closing")
        
        assert result["phase"] == "closing"
        
        # Check closing-specific content
        objectives_text = " ".join(result["objectives"]).lower()
        assert "closing" in objectives_text or "coordinate" in objectives_text
        
        tactics_text = " ".join(result["tactics"]).lower()
        assert "update" in tactics_text or "flexible" in tactics_text
    
    def test_generate_objection_handling_guide(self, service):
        """Test objection handling guide generation."""
        common_objections = ["Price is too high", "I need more time", "Custom objection"]
        
        result = service.generate_objection_handling_guide(common_objections)
        
        assert len(result) >= 3  # Should include standard + custom objections
        
        # Check standard objections are included
        assert "Your offer is too low" in result
        assert "I need to think about it" in result
        
        # Check custom objection is included
        assert "Custom objection" in result
        
        # Check response structure
        for objection, response in result.items():
            assert "acknowledge" in response
            assert "bridge" in response
            assert "response" in response
            assert "close" in response
    
    def test_generate_custom_objection_response(self, service):
        """Test custom objection response generation."""
        objection = "I don't trust investors"
        
        result = service._generate_custom_objection_response(objection)
        
        assert "acknowledge" in result
        assert "bridge" in result
        assert "response" in result
        assert "close" in result
        
        # Check that acknowledgment includes the objection
        assert "trust" in result["acknowledge"].lower()
    
    def test_get_latest_strategy(self, service, mock_db, sample_strategy):
        """Test getting latest strategy."""
        property_id = uuid.uuid4()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = sample_strategy
        
        result = service._get_latest_strategy(property_id)
        
        assert result == sample_strategy
        mock_db.query.assert_called_with(NegotiationStrategyDB)
    
    def test_get_latest_analysis(self, service, mock_db, sample_analysis):
        """Test getting latest analysis."""
        property_id = uuid.uuid4()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = sample_analysis
        
        result = service._get_latest_analysis(property_id)
        
        assert result == sample_analysis
        mock_db.query.assert_called_with(PropertyAnalysisDB)
    
    def test_get_property_lead(self, service, mock_db, sample_lead):
        """Test getting property lead."""
        property_id = uuid.uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = sample_lead
        
        result = service._get_property_lead(property_id)
        
        assert result == sample_lead
        mock_db.query.assert_called_with(PropertyLeadDB)


if __name__ == "__main__":
    pytest.main([__file__])