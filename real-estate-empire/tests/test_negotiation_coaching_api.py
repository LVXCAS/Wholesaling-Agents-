"""
Tests for negotiation coaching API endpoints.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routers.negotiation_coaching import router
from app.agents.negotiation_coaching_integration import NegotiationCoachingIntegration
from app.models.negotiation import NegotiationCoachingResponse


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def client():
    """Create a test client."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def sample_coaching_response():
    """Create a sample coaching response."""
    return {
        "success": True,
        "session_id": str(uuid.uuid4()),
        "coaching": {
            "talking_points": ["Property has been on market for 75 days"],
            "objection_responses": {"Price is too low": "Our offer is based on market analysis"},
            "value_propositions": ["Cash offer eliminates financing risks"],
            "negotiation_script": "Thank you for considering our offer...",
            "recommended_approach": "collaborative",
            "confidence_tips": ["Stay calm and professional"]
        },
        "real_time_suggestions": [
            {
                "type": "opening",
                "priority": "high",
                "suggestion": "Start with rapport building",
                "timing": "immediate"
            }
        ]
    }


class TestNegotiationCoachingAPI:
    """Test cases for negotiation coaching API endpoints."""
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/negotiation-coaching/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "negotiation-coaching"
        assert "timestamp" in data
    
    @patch('app.api.routers.negotiation_coaching.NegotiationCoachingIntegration')
    def test_get_negotiation_coaching_success(self, mock_integration_class, client, mock_db, sample_coaching_response):
        """Test successful negotiation coaching request."""
        # Setup mock
        mock_integration = Mock()
        mock_integration.provide_real_time_coaching = AsyncMock(return_value=sample_coaching_response)
        mock_integration_class.return_value = mock_integration
        
        # Make request
        request_data = {
            "property_id": str(uuid.uuid4()),
            "situation": "Initial offer presentation",
            "seller_response": "Price seems low",
            "specific_concerns": ["price", "timeline"],
            "negotiation_phase": "initial"
        }
        
        with patch('app.api.routers.negotiation_coaching.get_db', return_value=iter([mock_db])):
            response = client.post("/negotiation-coaching/get-coaching", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "session_id" in data
        assert "coaching" in data
        assert "real_time_suggestions" in data
        
        # Verify coaching content
        coaching = data["coaching"]
        assert len(coaching["talking_points"]) > 0
        assert len(coaching["objection_responses"]) > 0
        assert len(coaching["value_propositions"]) > 0
        assert coaching["negotiation_script"] is not None
        assert coaching["recommended_approach"] == "collaborative"
        assert len(coaching["confidence_tips"]) > 0
        
        # Verify suggestions
        suggestions = data["real_time_suggestions"]
        assert len(suggestions) > 0
        assert suggestions[0]["type"] == "opening"
        assert suggestions[0]["priority"] == "high"
    
    @patch('app.api.routers.negotiation_coaching.NegotiationCoachingIntegration')
    def test_get_negotiation_coaching_error(self, mock_integration_class, client, mock_db):
        """Test negotiation coaching request with error."""
        # Setup mock to raise exception
        mock_integration = Mock()
        mock_integration.provide_real_time_coaching = AsyncMock(side_effect=Exception("Service error"))
        mock_integration_class.return_value = mock_integration
        
        # Make request
        request_data = {
            "property_id": str(uuid.uuid4()),
            "situation": "Test situation"
        }
        
        with patch('app.api.routers.negotiation_coaching.get_db', return_value=iter([mock_db])):
            response = client.post("/negotiation-coaching/get-coaching", json=request_data)
        
        # Verify error response
        assert response.status_code == 500
        assert "Error getting negotiation coaching" in response.json()["detail"]
    
    def test_get_negotiation_coaching_invalid_data(self, client):
        """Test negotiation coaching request with invalid data."""
        # Make request with missing required field
        request_data = {
            "situation": "Test situation"
            # Missing property_id
        }
        
        response = client.post("/negotiation-coaching/get-coaching", json=request_data)
        
        # Verify validation error
        assert response.status_code == 422
    
    @patch('app.api.routers.negotiation_coaching.NegotiationCoachingIntegration')
    def test_track_coaching_effectiveness_success(self, mock_integration_class, client, mock_db):
        """Test successful coaching effectiveness tracking."""
        # Setup mock
        mock_integration = Mock()
        effectiveness_result = {
            "success": True,
            "effectiveness_score": 0.8,
            "session_data": {"session_id": "test-session", "outcome": "accepted"}
        }
        mock_integration.track_coaching_effectiveness = AsyncMock(return_value=effectiveness_result)
        mock_integration_class.return_value = mock_integration
        
        # Make request
        request_data = {
            "session_id": "test-session",
            "outcome": "accepted",
            "user_feedback": {"helpfulness": 8, "accuracy": 9}
        }
        
        with patch('app.api.routers.negotiation_coaching.get_db', return_value=iter([mock_db])):
            response = client.post("/negotiation-coaching/track-effectiveness", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["effectiveness_score"] == 0.8
        assert "session_data" in data
    
    @patch('app.api.routers.negotiation_coaching.NegotiationCoachingIntegration')
    def test_track_coaching_effectiveness_error(self, mock_integration_class, client, mock_db):
        """Test coaching effectiveness tracking with error."""
        # Setup mock to raise exception
        mock_integration = Mock()
        mock_integration.track_coaching_effectiveness = AsyncMock(side_effect=Exception("Tracking error"))
        mock_integration_class.return_value = mock_integration
        
        # Make request
        request_data = {
            "session_id": "test-session",
            "outcome": "accepted"
        }
        
        with patch('app.api.routers.negotiation_coaching.get_db', return_value=iter([mock_db])):
            response = client.post("/negotiation-coaching/track-effectiveness", json=request_data)
        
        # Verify error response
        assert response.status_code == 500
        assert "Error tracking coaching effectiveness" in response.json()["detail"]
    
    @patch('app.api.routers.negotiation_coaching.NegotiationCoachingIntegration')
    def test_get_coaching_analytics_overall(self, mock_integration_class, client, mock_db):
        """Test getting overall coaching analytics."""
        # Setup mock
        mock_integration = Mock()
        analytics_result = {
            "total_sessions": 10,
            "total_properties": 5,
            "average_effectiveness": 0.7,
            "success_rate": 0.6,
            "phase_breakdown": {"initial": 4, "counter": 3, "final": 3},
            "outcome_breakdown": {"accepted": 6, "rejected": 2, "counter_offer": 2}
        }
        mock_integration.get_coaching_analytics.return_value = analytics_result
        mock_integration_class.return_value = mock_integration
        
        # Make request
        with patch('app.api.routers.negotiation_coaching.get_db', return_value=iter([mock_db])):
            response = client.get("/negotiation-coaching/analytics")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "analytics" in data
        
        analytics = data["analytics"]
        assert analytics["total_sessions"] == 10
        assert analytics["total_properties"] == 5
        assert analytics["average_effectiveness"] == 0.7
        assert analytics["success_rate"] == 0.6
        assert "phase_breakdown" in analytics
        assert "outcome_breakdown" in analytics
    
    @patch('app.api.routers.negotiation_coaching.NegotiationCoachingIntegration')
    def test_get_coaching_analytics_specific_property(self, mock_integration_class, client, mock_db):
        """Test getting analytics for a specific property."""
        # Setup mock
        mock_integration = Mock()
        property_analytics = {
            "sessions": [{"effectiveness_score": 0.8, "outcome": "accepted"}],
            "average_effectiveness": 0.8,
            "total_sessions": 1,
            "successful_outcomes": 1
        }
        mock_integration.get_coaching_analytics.return_value = property_analytics
        mock_integration_class.return_value = mock_integration
        
        # Make request
        property_id = str(uuid.uuid4())
        with patch('app.api.routers.negotiation_coaching.get_db', return_value=iter([mock_db])):
            response = client.get(f"/negotiation-coaching/analytics?property_id={property_id}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "analytics" in data
        
        analytics = data["analytics"]
        assert analytics["total_sessions"] == 1
        assert analytics["average_effectiveness"] == 0.8
        assert analytics["successful_outcomes"] == 1
    
    @patch('app.api.routers.negotiation_coaching.NegotiationCoachingIntegration')
    def test_generate_coaching_report_success(self, mock_integration_class, client, mock_db):
        """Test successful coaching report generation."""
        # Setup mock
        mock_integration = Mock()
        report_result = {
            "property_id": str(uuid.uuid4()),
            "report_generated_at": datetime.now().isoformat(),
            "summary": {
                "total_sessions": 3,
                "average_effectiveness": 0.75,
                "success_rate": 0.67
            },
            "session_details": [
                {
                    "session_id": "session-1",
                    "negotiation_phase": "initial",
                    "effectiveness_score": 0.8,
                    "outcome": "accepted"
                }
            ],
            "recommendations": ["Continue current approach"]
        }
        mock_integration.generate_coaching_report = AsyncMock(return_value=report_result)
        mock_integration_class.return_value = mock_integration
        
        # Make request
        property_id = str(uuid.uuid4())
        with patch('app.api.routers.negotiation_coaching.get_db', return_value=iter([mock_db])):
            response = client.get(f"/negotiation-coaching/report/{property_id}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "report" in data
        
        report = data["report"]
        assert "property_id" in report
        assert "summary" in report
        assert "session_details" in report
        assert "recommendations" in report
    
    @patch('app.api.routers.negotiation_coaching.NegotiationCoachingIntegration')
    def test_generate_coaching_report_not_found(self, mock_integration_class, client, mock_db):
        """Test coaching report generation when no data found."""
        # Setup mock
        mock_integration = Mock()
        mock_integration.generate_coaching_report = AsyncMock(
            return_value={"error": "No coaching data found for property"}
        )
        mock_integration_class.return_value = mock_integration
        
        # Make request
        property_id = str(uuid.uuid4())
        with patch('app.api.routers.negotiation_coaching.get_db', return_value=iter([mock_db])):
            response = client.get(f"/negotiation-coaching/report/{property_id}")
        
        # Verify error response
        assert response.status_code == 404
        assert "No coaching data found" in response.json()["detail"]
    
    @patch('app.services.negotiation_coaching_service.NegotiationCoachingService')
    def test_get_phase_specific_coaching(self, mock_service_class, client, mock_db):
        """Test getting phase-specific coaching."""
        # Setup mock
        mock_service = Mock()
        phase_coaching = {
            "phase": "initial",
            "objectives": ["Establish rapport", "Present offer"],
            "key_messages": ["We're experienced investors"],
            "tactics": ["Ask open-ended questions"],
            "red_flags": ["Seller seems unrealistic"],
            "success_indicators": ["Seller asks questions"]
        }
        mock_service.generate_situation_specific_coaching.return_value = phase_coaching
        mock_service_class.return_value = mock_service
        
        # Make request
        property_id = str(uuid.uuid4())
        with patch('app.api.routers.negotiation_coaching.get_db', return_value=iter([mock_db])):
            response = client.get(f"/negotiation-coaching/phase-coaching/{property_id}?negotiation_phase=initial")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "phase_coaching" in data
        
        coaching = data["phase_coaching"]
        assert coaching["phase"] == "initial"
        assert len(coaching["objectives"]) > 0
        assert len(coaching["key_messages"]) > 0
        assert len(coaching["tactics"]) > 0
    
    @patch('app.services.negotiation_coaching_service.NegotiationCoachingService')
    def test_get_objection_handling_guide_default(self, mock_service_class, client, mock_db):
        """Test getting objection handling guide with default objections."""
        # Setup mock
        mock_service = Mock()
        objection_guide = {
            "Your offer is too low": {
                "acknowledge": "I understand you feel the offer is low.",
                "bridge": "Let me explain how we arrived at this number.",
                "response": "Our offer is based on current market conditions...",
                "close": "Would you like me to show you the comparable sales?"
            },
            "I need more time to think": {
                "acknowledge": "I understand this is a big decision.",
                "bridge": "However, our offer is time-sensitive.",
                "response": "We can give you 48 hours to consider...",
                "close": "What questions can I answer to help you decide?"
            }
        }
        mock_service.generate_objection_handling_guide.return_value = objection_guide
        mock_service_class.return_value = mock_service
        
        # Make request
        with patch('app.api.routers.negotiation_coaching.get_db', return_value=iter([mock_db])):
            response = client.get("/negotiation-coaching/objection-guide")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "objection_guide" in data
        
        guide = data["objection_guide"]
        assert "Your offer is too low" in guide
        assert "I need more time to think" in guide
        
        # Verify response structure
        for objection, response_data in guide.items():
            assert "acknowledge" in response_data
            assert "bridge" in response_data
            assert "response" in response_data
            assert "close" in response_data
    
    @patch('app.services.negotiation_coaching_service.NegotiationCoachingService')
    def test_get_objection_handling_guide_custom(self, mock_service_class, client, mock_db):
        """Test getting objection handling guide with custom objections."""
        # Setup mock
        mock_service = Mock()
        objection_guide = {
            "Custom objection": {
                "acknowledge": "I understand your concern.",
                "bridge": "Let me address that.",
                "response": "Custom response...",
                "close": "Does that help?"
            }
        }
        mock_service.generate_objection_handling_guide.return_value = objection_guide
        mock_service_class.return_value = mock_service
        
        # Make request with custom objections
        custom_objections = ["Custom objection"]
        with patch('app.api.routers.negotiation_coaching.get_db', return_value=iter([mock_db])):
            response = client.get(
                "/negotiation-coaching/objection-guide",
                params={"common_objections": custom_objections}
            )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "objection_guide" in data
        
        guide = data["objection_guide"]
        assert "Custom objection" in guide


if __name__ == "__main__":
    pytest.main([__file__])