"""
API endpoints for negotiation coaching functionality.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.agents.negotiation_coaching_integration import NegotiationCoachingIntegration
from app.models.negotiation import NegotiationCoachingRequest, NegotiationCoachingResponse

router = APIRouter(prefix="/negotiation-coaching", tags=["negotiation-coaching"])


class CoachingRequest(BaseModel):
    """Request model for negotiation coaching."""
    property_id: uuid.UUID
    situation: str
    seller_response: Optional[str] = None
    specific_concerns: Optional[List[str]] = None
    negotiation_phase: str = "initial"


class CoachingEffectivenessRequest(BaseModel):
    """Request model for tracking coaching effectiveness."""
    session_id: str
    outcome: str
    user_feedback: Optional[Dict[str, Any]] = None


class CoachingResponse(BaseModel):
    """Response model for coaching requests."""
    success: bool
    session_id: Optional[str] = None
    coaching: Optional[Dict[str, Any]] = None
    real_time_suggestions: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class EffectivenessResponse(BaseModel):
    """Response model for effectiveness tracking."""
    success: bool
    effectiveness_score: Optional[float] = None
    session_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/get-coaching", response_model=CoachingResponse)
async def get_negotiation_coaching(
    request: CoachingRequest,
    db: Session = Depends(get_db)
) -> CoachingResponse:
    """
    Get real-time negotiation coaching for a property.
    
    Args:
        request: Coaching request with property details and situation
        db: Database session
        
    Returns:
        CoachingResponse with coaching guidance and suggestions
    """
    try:
        coaching_integration = NegotiationCoachingIntegration(db)
        
        result = await coaching_integration.provide_real_time_coaching(
            property_id=request.property_id,
            situation=request.situation,
            seller_response=request.seller_response,
            specific_concerns=request.specific_concerns,
            negotiation_phase=request.negotiation_phase
        )
        
        return CoachingResponse(
            success=result.get("success", False),
            session_id=result.get("session_id"),
            coaching=result.get("coaching"),
            real_time_suggestions=result.get("real_time_suggestions"),
            error=result.get("error")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting negotiation coaching: {str(e)}"
        )


@router.post("/track-effectiveness", response_model=EffectivenessResponse)
async def track_coaching_effectiveness(
    request: CoachingEffectivenessRequest,
    db: Session = Depends(get_db)
) -> EffectivenessResponse:
    """
    Track the effectiveness of a coaching session.
    
    Args:
        request: Effectiveness tracking request
        db: Database session
        
    Returns:
        EffectivenessResponse with tracking results
    """
    try:
        coaching_integration = NegotiationCoachingIntegration(db)
        
        result = await coaching_integration.track_coaching_effectiveness(
            session_id=request.session_id,
            outcome=request.outcome,
            user_feedback=request.user_feedback
        )
        
        return EffectivenessResponse(
            success=result.get("success", False),
            effectiveness_score=result.get("effectiveness_score"),
            session_data=result.get("session_data"),
            error=result.get("error")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error tracking coaching effectiveness: {str(e)}"
        )


@router.get("/analytics")
async def get_coaching_analytics(
    property_id: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get coaching analytics for a specific property or overall.
    
    Args:
        property_id: Optional property ID for specific analytics
        db: Database session
        
    Returns:
        Dict with coaching analytics data
    """
    try:
        coaching_integration = NegotiationCoachingIntegration(db)
        
        analytics = coaching_integration.get_coaching_analytics(property_id)
        
        return {
            "success": True,
            "analytics": analytics
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting coaching analytics: {str(e)}"
        )


@router.get("/report/{property_id}")
async def generate_coaching_report(
    property_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate a comprehensive coaching report for a property.
    
    Args:
        property_id: Property ID for the report
        db: Database session
        
    Returns:
        Dict with comprehensive coaching report
    """
    try:
        coaching_integration = NegotiationCoachingIntegration(db)
        
        report = await coaching_integration.generate_coaching_report(property_id)
        
        if "error" in report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=report["error"]
            )
        
        return {
            "success": True,
            "report": report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating coaching report: {str(e)}"
        )


@router.get("/phase-coaching/{property_id}")
async def get_phase_specific_coaching(
    property_id: str,
    negotiation_phase: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get phase-specific coaching for a property.
    
    Args:
        property_id: Property ID
        negotiation_phase: Current negotiation phase
        db: Database session
        
    Returns:
        Dict with phase-specific coaching guidance
    """
    try:
        from app.services.negotiation_coaching_service import NegotiationCoachingService
        
        coaching_service = NegotiationCoachingService(db)
        
        coaching = coaching_service.generate_situation_specific_coaching(
            property_id=uuid.UUID(property_id),
            negotiation_phase=negotiation_phase
        )
        
        return {
            "success": True,
            "phase_coaching": coaching
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting phase-specific coaching: {str(e)}"
        )


@router.get("/objection-guide")
async def get_objection_handling_guide(
    common_objections: List[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get objection handling guide.
    
    Args:
        common_objections: List of common objections to address
        db: Database session
        
    Returns:
        Dict with objection handling strategies
    """
    try:
        from app.services.negotiation_coaching_service import NegotiationCoachingService
        
        coaching_service = NegotiationCoachingService(db)
        
        if not common_objections:
            common_objections = [
                "Your offer is too low",
                "I need more time to think",
                "I can get more from another buyer",
                "The property is in good condition",
                "I don't trust investors"
            ]
        
        guide = coaching_service.generate_objection_handling_guide(common_objections)
        
        return {
            "success": True,
            "objection_guide": guide
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting objection handling guide: {str(e)}"
        )


@router.get("/health")
async def coaching_health_check() -> Dict[str, Any]:
    """Health check endpoint for coaching service."""
    return {
        "status": "healthy",
        "service": "negotiation-coaching",
        "timestamp": datetime.now().isoformat()
    }