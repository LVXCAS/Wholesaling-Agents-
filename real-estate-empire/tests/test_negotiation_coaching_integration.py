"""
Integration tests for negotiation coaching workflow integration.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.agents.negotiation_coaching_integration import NegotiationCoachingIntegration
from app.models.negotiation import NegotiationCoachingResponse
from app.core.agent_state import AgentState, AgentType


class TestNegotiationCoachingIntegration:
    """Test cases for NegotiationCoachingIntegration."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock()
    
    @pytest.fixture
    def integration(self, mock_db):
        """Create a NegotiationCoachingIntegration instance."""
        return NegotiationCoachingIntegration(mock_db)
    
    @pytest.fixture
    def sample_coaching_response(self):
        """Create a sample coaching response."""
        return NegotiationCoachingResponse(
            talking_points=[
                "Property has been on market for 75 days",
                "We can close quickly without financing delays"
            ],
            objection_responses={
                "Price is too low": "Our offer is based on current market analysis and comparable sales",
                "I need more time": "We can be flexible with closing timeline to work with your schedule"
            },
            value_propositions=[
                "Cash offer eliminates financing risks",
                "No real estate commissions to pay"
            ],
            negotiation_script="Thank you for considering our offer...",
            recommended_approach="collaborative",
            confidence_tips=[
                "Stay calm and professional",
                "Listen actively to seller concerns"
            ]
        )
    
    @pytest.fixture
    def sample_agent_state(self):
        """Create a sample agent state."""
        return {
            "deals": [],
            "active_negotiations": [],
            "agent_messages": [],
            "market_conditions": {
                "market_type": "buyers_market",
                "average_days_on_market": 45
            }
        }
    
    @pytest.fixture
    def sample_negotiation_data(self):
        """Create sample negotiation data."""
        return {
            "property_id": str(uuid.uuid4()),
            "situation": "Initial offer presentation",
            "status": "initial_outreach",
            "offer_count": 0,
            "latest_response": "The price seems low for this property",
            "concerns": ["price", "timeline"]
        }
    
    @pytest.mark.asyncio
    async def test_provide_real_time_coaching_success(self, integration, sample_coaching_response):
        """Test successful real-time coaching provision."""
        property_id = uuid.uuid4()
        
        # Mock the coaching service
        with patch.object(integration.coaching_service, 'generate_coaching', return_value=sample_coaching_response):
            with patch.object(integration.coaching_service, 'generate_situation_specific_coaching', 
                            return_value={"phase": "initial", "objectives": ["Build rapport"]}):
                
                result = await integration.provide_real_time_coaching(
                    property_id=property_id,
                    situation="Initial offer presentation",
                    seller_response="Price seems low",
                    specific_concerns=["price"],
                    negotiation_phase="initial"
                )
        
        # Verify result
        assert result["success"] is True
        assert "session_id" in result
        assert "coaching" in result
        assert "real_time_suggestions" in result
        
        # Verify coaching content
        coaching = result["coaching"]
        assert len(coaching["talking_points"]) > 0
        assert len(coaching["objection_responses"]) > 0
        assert len(coaching["value_propositions"]) > 0
        assert coaching["negotiation_script"] is not None
        assert coaching["recommended_approach"] == "collaborative"
        assert len(coaching["confidence_tips"]) > 0
        assert "phase_specific" in coaching
        
        # Verify session was stored
        session_id = result["session_id"]
        assert session_id in integration.active_coaching_sessions
        
        session = integration.active_coaching_sessions[session_id]
        assert session["property_id"] == str(property_id)
        assert session["negotiation_phase"] == "initial"
        assert session["situation"] == "Initial offer presentation"
    
    @pytest.mark.asyncio
    async def test_provide_real_time_coaching_error_handling(self, integration):
        """Test error handling in real-time coaching."""
        property_id = uuid.uuid4()
        
        # Mock the coaching service to raise an exception
        with patch.object(integration.coaching_service, 'generate_coaching', side_effect=Exception("Service error")):
            result = await integration.provide_real_time_coaching(
                property_id=property_id,
                situation="Test situation"
            )
        
        # Verify error handling
        assert result["success"] is False
        assert "error" in result
        assert result["coaching"] is None
    
    def test_generate_real_time_suggestions_initial_phase(self, integration):
        """Test real-time suggestions for initial phase."""
        suggestions = integration._generate_real_time_suggestions(
            situation="First contact with seller",
            seller_response=None,
            negotiation_phase="initial"
        )
        
        assert len(suggestions) > 0
        
        # Check for phase-specific suggestions
        suggestion_types = [s["type"] for s in suggestions]
        assert "opening" in suggestion_types
        assert "data_preparation" in suggestion_types
        
        # Verify suggestion structure
        for suggestion in suggestions:
            assert "type" in suggestion
            assert "priority" in suggestion
            assert "suggestion" in suggestion
            assert "timing" in suggestion
    
    def test_generate_real_time_suggestions_counter_phase(self, integration):
        """Test real-time suggestions for counter offer phase."""
        suggestions = integration._generate_real_time_suggestions(
            situation="Received counter offer",
            seller_response="I need $10,000 more",
            negotiation_phase="counter"
        )
        
        assert len(suggestions) > 0
        
        # Check for phase-specific suggestions
        suggestion_types = [s["type"] for s in suggestions]
        assert "acknowledgment" in suggestion_types
        assert "creative_solutions" in suggestion_types
    
    def test_generate_real_time_suggestions_final_phase(self, integration):
        """Test real-time suggestions for final phase."""
        suggestions = integration._generate_real_time_suggestions(
            situation="Making final offer",
            seller_response=None,
            negotiation_phase="final"
        )
        
        assert len(suggestions) > 0
        
        # Check for phase-specific suggestions
        suggestion_types = [s["type"] for s in suggestions]
        assert "finality" in suggestion_types
        assert "walkaway_preparation" in suggestion_types
    
    def test_generate_real_time_suggestions_with_seller_response(self, integration):
        """Test real-time suggestions based on seller response."""
        suggestions = integration._generate_real_time_suggestions(
            situation="Negotiation in progress",
            seller_response="Your price is too low for this property",
            negotiation_phase="counter"
        )
        
        # Check for response-specific suggestions
        suggestion_types = [s["type"] for s in suggestions]
        assert "price_objection" in suggestion_types
        
        # Find the price objection suggestion
        price_suggestion = next(s for s in suggestions if s["type"] == "price_objection")
        assert price_suggestion["priority"] == "high"
        assert "comparable sales" in price_suggestion["suggestion"].lower()
    
    def test_generate_real_time_suggestions_situation_specific(self, integration):
        """Test situation-specific real-time suggestions."""
        # Test foreclosure situation
        foreclosure_suggestions = integration._generate_real_time_suggestions(
            situation="Seller facing foreclosure",
            seller_response=None,
            negotiation_phase="initial"
        )
        
        suggestion_types = [s["type"] for s in foreclosure_suggestions]
        assert "empathy" in suggestion_types
        
        # Test divorce situation
        divorce_suggestions = integration._generate_real_time_suggestions(
            situation="Divorce situation - need quick sale",
            seller_response=None,
            negotiation_phase="initial"
        )
        
        suggestion_types = [s["type"] for s in divorce_suggestions]
        assert "simplicity" in suggestion_types
    
    @pytest.mark.asyncio
    async def test_integrate_with_negotiator_workflow(self, integration, sample_agent_state, 
                                                    sample_negotiation_data, sample_coaching_response):
        """Test integration with negotiator workflow."""
        # Mock the coaching service
        with patch.object(integration.coaching_service, 'generate_coaching', return_value=sample_coaching_response):
            with patch.object(integration.coaching_service, 'generate_situation_specific_coaching', 
                            return_value={"phase": "initial", "objectives": ["Build rapport"]}):
                
                updated_state = await integration.integrate_with_negotiator_workflow(
                    sample_agent_state, sample_negotiation_data
                )
        
        # Verify state was updated
        assert len(updated_state["agent_messages"]) > 0
        
        # Verify negotiation data was updated with coaching
        assert "coaching_session_id" in sample_negotiation_data
        assert "coaching_suggestions" in sample_negotiation_data
        assert "recommended_approach" in sample_negotiation_data
        assert "talking_points" in sample_negotiation_data
        
        # Verify coaching session was created
        session_id = sample_negotiation_data["coaching_session_id"]
        assert session_id in integration.active_coaching_sessions
    
    def test_determine_negotiation_phase_initial(self, integration):
        """Test negotiation phase determination for initial phase."""
        negotiation_data = {
            "status": "initial_outreach",
            "offer_count": 0
        }
        
        phase = integration._determine_negotiation_phase(negotiation_data)
        assert phase == "initial"
    
    def test_determine_negotiation_phase_counter(self, integration):
        """Test negotiation phase determination for counter phase."""
        negotiation_data = {
            "status": "counter_offer",
            "offer_count": 2
        }
        
        phase = integration._determine_negotiation_phase(negotiation_data)
        assert phase == "counter"
    
    def test_determine_negotiation_phase_final(self, integration):
        """Test negotiation phase determination for final phase."""
        negotiation_data = {
            "status": "final_offer",
            "is_final_offer": True,
            "offer_count": 3
        }
        
        phase = integration._determine_negotiation_phase(negotiation_data)
        assert phase == "final"
    
    def test_determine_negotiation_phase_closing(self, integration):
        """Test negotiation phase determination for closing phase."""
        negotiation_data = {
            "status": "under_contract",
            "offer_count": 2
        }
        
        phase = integration._determine_negotiation_phase(negotiation_data)
        assert phase == "closing"
    
    @pytest.mark.asyncio
    async def test_track_coaching_effectiveness_success(self, integration):
        """Test successful coaching effectiveness tracking."""
        # Create a coaching session first
        session_id = str(uuid.uuid4())
        property_id = str(uuid.uuid4())
        
        integration.active_coaching_sessions[session_id] = {
            "session_id": session_id,
            "property_id": property_id,
            "situation": "Test negotiation",
            "negotiation_phase": "initial",
            "created_at": datetime.now(),
            "effectiveness_score": None
        }
        
        # Track effectiveness
        result = await integration.track_coaching_effectiveness(
            session_id=session_id,
            outcome="accepted",
            user_feedback={"helpfulness": 8, "accuracy": 9}
        )
        
        # Verify result
        assert result["success"] is True
        assert result["effectiveness_score"] > 0.8  # Should be high for accepted outcome
        
        # Verify session was updated
        session = integration.active_coaching_sessions[session_id]
        assert session["effectiveness_score"] is not None
        assert session["outcome"] == "accepted"
        assert session["user_feedback"] is not None
        
        # Verify tracking data was created
        assert property_id in integration.coaching_effectiveness_tracking
        tracking_data = integration.coaching_effectiveness_tracking[property_id]
        assert tracking_data["total_sessions"] == 1
        assert tracking_data["successful_outcomes"] == 1
    
    @pytest.mark.asyncio
    async def test_track_coaching_effectiveness_session_not_found(self, integration):
        """Test effectiveness tracking with non-existent session."""
        result = await integration.track_coaching_effectiveness(
            session_id="non-existent",
            outcome="accepted"
        )
        
        assert result["success"] is False
        assert "Session not found" in result["error"]
    
    def test_calculate_effectiveness_score_accepted(self, integration):
        """Test effectiveness score calculation for accepted outcome."""
        score = integration._calculate_effectiveness_score("accepted")
        assert score == 1.0
    
    def test_calculate_effectiveness_score_rejected(self, integration):
        """Test effectiveness score calculation for rejected outcome."""
        score = integration._calculate_effectiveness_score("rejected")
        assert score == 0.1
    
    def test_calculate_effectiveness_score_with_feedback(self, integration):
        """Test effectiveness score calculation with user feedback."""
        score = integration._calculate_effectiveness_score(
            "counter_offer",
            user_feedback={"helpfulness": 10, "accuracy": 10}
        )
        
        # Should be higher than base score due to excellent feedback
        base_score = 0.7  # Base score for counter_offer
        assert score > base_score
        assert score <= 1.0
    
    def test_get_coaching_analytics_specific_property(self, integration):
        """Test getting analytics for a specific property."""
        property_id = str(uuid.uuid4())
        
        # Add some test data
        integration.coaching_effectiveness_tracking[property_id] = {
            "sessions": [
                {"effectiveness_score": 0.8, "outcome": "accepted"},
                {"effectiveness_score": 0.6, "outcome": "counter_offer"}
            ],
            "average_effectiveness": 0.7,
            "total_sessions": 2,
            "successful_outcomes": 1
        }
        
        analytics = integration.get_coaching_analytics(property_id)
        
        assert analytics["total_sessions"] == 2
        assert analytics["average_effectiveness"] == 0.7
        assert analytics["successful_outcomes"] == 1
    
    def test_get_coaching_analytics_overall(self, integration):
        """Test getting overall coaching analytics."""
        # Add test data for multiple properties
        property1 = str(uuid.uuid4())
        property2 = str(uuid.uuid4())
        
        integration.coaching_effectiveness_tracking[property1] = {
            "sessions": [
                {"effectiveness_score": 0.8, "outcome": "accepted", "negotiation_phase": "initial"},
                {"effectiveness_score": 0.6, "outcome": "counter_offer", "negotiation_phase": "counter"}
            ],
            "total_sessions": 2,
            "successful_outcomes": 1
        }
        
        integration.coaching_effectiveness_tracking[property2] = {
            "sessions": [
                {"effectiveness_score": 0.9, "outcome": "accepted", "negotiation_phase": "final"}
            ],
            "total_sessions": 1,
            "successful_outcomes": 1
        }
        
        analytics = integration.get_coaching_analytics()
        
        assert analytics["total_sessions"] == 3
        assert analytics["total_properties"] == 2
        assert analytics["success_rate"] == 2/3  # 2 successful out of 3 total
        assert "phase_breakdown" in analytics
        assert "outcome_breakdown" in analytics
    
    def test_get_coaching_analytics_no_data(self, integration):
        """Test getting analytics when no data exists."""
        analytics = integration.get_coaching_analytics()
        assert "message" in analytics
        assert "No coaching sessions found" in analytics["message"]
    
    def test_get_phase_breakdown(self, integration):
        """Test phase breakdown calculation."""
        sessions = [
            {"negotiation_phase": "initial"},
            {"negotiation_phase": "initial"},
            {"negotiation_phase": "counter"},
            {"negotiation_phase": "final"}
        ]
        
        breakdown = integration._get_phase_breakdown(sessions)
        
        assert breakdown["initial"] == 2
        assert breakdown["counter"] == 1
        assert breakdown["final"] == 1
    
    def test_get_outcome_breakdown(self, integration):
        """Test outcome breakdown calculation."""
        sessions = [
            {"outcome": "accepted"},
            {"outcome": "accepted"},
            {"outcome": "rejected"},
            {"outcome": "counter_offer"}
        ]
        
        breakdown = integration._get_outcome_breakdown(sessions)
        
        assert breakdown["accepted"] == 2
        assert breakdown["rejected"] == 1
        assert breakdown["counter_offer"] == 1
    
    @pytest.mark.asyncio
    async def test_generate_coaching_report(self, integration):
        """Test coaching report generation."""
        property_id = str(uuid.uuid4())
        
        # Add test data
        integration.coaching_effectiveness_tracking[property_id] = {
            "sessions": [
                {
                    "session_id": str(uuid.uuid4()),
                    "negotiation_phase": "initial",
                    "effectiveness_score": 0.8,
                    "outcome": "accepted",
                    "created_at": datetime.now(),
                    "general_coaching": {
                        "talking_points": ["Point 1", "Point 2"],
                        "objection_responses": {"Objection": "Response"},
                        "confidence_tips": ["Tip 1"]
                    }
                }
            ],
            "total_sessions": 1,
            "average_effectiveness": 0.8,
            "successful_outcomes": 1
        }
        
        report = await integration.generate_coaching_report(property_id)
        
        # Verify report structure
        assert "property_id" in report
        assert "report_generated_at" in report
        assert "summary" in report
        assert "session_details" in report
        assert "recommendations" in report
        
        # Verify summary
        summary = report["summary"]
        assert summary["total_sessions"] == 1
        assert summary["average_effectiveness"] == 0.8
        assert summary["success_rate"] == 1.0
        
        # Verify session details
        assert len(report["session_details"]) == 1
        session_detail = report["session_details"][0]
        assert "session_id" in session_detail
        assert "negotiation_phase" in session_detail
        assert "coaching_used" in session_detail
    
    @pytest.mark.asyncio
    async def test_generate_coaching_report_no_data(self, integration):
        """Test coaching report generation with no data."""
        property_id = str(uuid.uuid4())
        
        report = await integration.generate_coaching_report(property_id)
        
        assert "error" in report
        assert "No coaching data found" in report["error"]
    
    def test_generate_coaching_recommendations_low_effectiveness(self, integration):
        """Test coaching recommendations for low effectiveness."""
        tracking_data = {
            "average_effectiveness": 0.4,
            "total_sessions": 10,
            "successful_outcomes": 2,
            "sessions": [
                {"negotiation_phase": "initial", "effectiveness_score": 0.3},
                {"negotiation_phase": "initial", "effectiveness_score": 0.4}
            ]
        }
        
        recommendations = integration._generate_coaching_recommendations(tracking_data)
        
        assert len(recommendations) > 0
        recommendation_text = " ".join(recommendations).lower()
        assert "effectiveness" in recommendation_text or "approach" in recommendation_text
    
    def test_generate_coaching_recommendations_good_performance(self, integration):
        """Test coaching recommendations for good performance."""
        tracking_data = {
            "average_effectiveness": 0.8,
            "total_sessions": 10,
            "successful_outcomes": 8,
            "sessions": [
                {"negotiation_phase": "initial", "effectiveness_score": 0.8},
                {"negotiation_phase": "counter", "effectiveness_score": 0.9}
            ]
        }
        
        recommendations = integration._generate_coaching_recommendations(tracking_data)
        
        assert len(recommendations) > 0
        recommendation_text = " ".join(recommendations).lower()
        assert "good" in recommendation_text or "continue" in recommendation_text


if __name__ == "__main__":
    pytest.main([__file__])