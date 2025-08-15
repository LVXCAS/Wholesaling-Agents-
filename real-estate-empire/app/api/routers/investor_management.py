"""
API router for investor relationship management.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.models.investor import (
    InvestorProfile, InvestmentHistory, InvestorCommunication,
    InvestorPerformanceMetrics, DealInvestorMatch, InvestorDealPresentation,
    InvestorSearchCriteria, InvestorAnalytics, InvestorTypeEnum,
    InvestorStatusEnum, InvestmentPreferenceEnum, RiskToleranceEnum,
    CommunicationPreferenceEnum
)
from app.services.investor_management_service import InvestorManagementService

router = APIRouter(prefix="/api/investor-management", tags=["investor-management"])


# Request/Response Models

class CreateInvestorRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    investor_type: InvestorTypeEnum
    investment_preferences: List[InvestmentPreferenceEnum] = []
    risk_tolerance: RiskToleranceEnum = RiskToleranceEnum.MODERATE
    min_investment: Optional[Decimal] = None
    max_investment: Optional[Decimal] = None
    preferred_markets: List[str] = []
    communication_preferences: List[CommunicationPreferenceEnum] = []
    net_worth: Optional[Decimal] = None
    liquid_capital: Optional[Decimal] = None
    annual_income: Optional[Decimal] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = []


class UpdateInvestorRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    investor_type: Optional[InvestorTypeEnum] = None
    status: Optional[InvestorStatusEnum] = None
    investment_preferences: Optional[List[InvestmentPreferenceEnum]] = None
    risk_tolerance: Optional[RiskToleranceEnum] = None
    min_investment: Optional[Decimal] = None
    max_investment: Optional[Decimal] = None
    preferred_markets: Optional[List[str]] = None
    communication_preferences: Optional[List[CommunicationPreferenceEnum]] = None
    net_worth: Optional[Decimal] = None
    liquid_capital: Optional[Decimal] = None
    annual_income: Optional[Decimal] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class LogCommunicationRequest(BaseModel):
    investor_id: UUID
    communication_type: CommunicationPreferenceEnum
    subject: str
    content: str
    direction: str  # inbound, outbound
    deal_id: Optional[UUID] = None
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None


class RecordInvestmentRequest(BaseModel):
    investor_id: UUID
    deal_id: UUID
    investment_amount: Decimal
    investment_date: datetime
    expected_return: Optional[Decimal] = None
    status: str = "active"
    notes: Optional[str] = None


class DealMatchRequest(BaseModel):
    deal_id: UUID
    property_type: str
    investment_required: Decimal
    market: str
    city: str
    state: str
    risk_level: str = "moderate"
    distressed: bool = False
    expected_return: Optional[Decimal] = None


class CreatePresentationRequest(BaseModel):
    investor_id: UUID
    deal_id: UUID
    presentation_type: str  # email, pdf, video, meeting


# Dependency to get service instance
def get_investor_service() -> InvestorManagementService:
    # In a real implementation, this would inject the database session
    return InvestorManagementService(db=None)


# Investor Profile Endpoints

@router.post("/investors", response_model=InvestorProfile)
async def create_investor(
    request: CreateInvestorRequest,
    service: InvestorManagementService = Depends(get_investor_service)
):
    """Create a new investor profile"""
    try:
        investor_data = request.dict()
        investor = service.create_investor_profile(investor_data)
        return investor
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating investor: {str(e)}"
        )


@router.get("/investors", response_model=List[InvestorProfile])
async def get_investors(
    status: Optional[InvestorStatusEnum] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: InvestorManagementService = Depends(get_investor_service)
):
    """Get all investors with optional filtering"""
    try:
        investors = service.get_all_investors(status=status, limit=limit, offset=offset)
        return investors
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving investors: {str(e)}"
        )


@router.get("/investors/{investor_id}", response_model=InvestorProfile)
async def get_investor(
    investor_id: UUID,
    service: InvestorManagementService = Depends(get_investor_service)
):
    """Get investor profile by ID"""
    try:
        investor = service.get_investor_profile(investor_id)
        if not investor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Investor not found"
            )
        return investor
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving investor: {str(e)}"
        )


@router.put("/investors/{investor_id}", response_model=InvestorProfile)
async def update_investor(
    investor_id: UUID,
    request: UpdateInvestorRequest,
    service: InvestorManagementService = Depends(get_investor_service)
):
    """Update an investor profile"""
    try:
        updates = {k: v for k, v in request.dict().items() if v is not None}
        investor = service.update_investor_profile(investor_id, updates)
        return investor
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating investor: {str(e)}"
        )


@router.post("/investors/search", response_model=List[InvestorProfile])
async def search_investors(
    criteria: InvestorSearchCriteria,
    service: InvestorManagementService = Depends(get_investor_service)
):
    """Search investors based on criteria"""
    try:
        investors = service.search_investors(criteria)
        return investors
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error searching investors: {str(e)}"
        )


# Deal Matching Endpoints

@router.post("/deals/{deal_id}/matches", response_model=List[DealInvestorMatch])
async def match_investors_to_deal(
    deal_id: UUID,
    deal_data: DealMatchRequest,
    service: InvestorManagementService = Depends(get_investor_service)
):
    """Find investors that match a specific deal"""
    try:
        matches = service.match_investors_to_deal(deal_id, deal_data.dict())
        return matches
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error matching investors to deal: {str(e)}"
        )


# Communication Endpoints

@router.post("/communications", response_model=InvestorCommunication)
async def log_communication(
    request: LogCommunicationRequest,
    service: InvestorManagementService = Depends(get_investor_service)
):
    """Log a communication with an investor"""
    try:
        communication = service.log_communication(request.dict())
        return communication
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error logging communication: {str(e)}"
        )


@router.get("/investors/{investor_id}/communications", response_model=List[InvestorCommunication])
async def get_investor_communications(
    investor_id: UUID,
    limit: int = Query(50, ge=1, le=500),
    service: InvestorManagementService = Depends(get_investor_service)
):
    """Get communication history for an investor"""
    try:
        communications = service.get_investor_communications(investor_id, limit)
        return communications
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving communications: {str(e)}"
        )


@router.post("/investors/{investor_id}/follow-up")
async def schedule_follow_up(
    investor_id: UUID,
    follow_up_date: datetime,
    notes: str = "",
    service: InvestorManagementService = Depends(get_investor_service)
):
    """Schedule a follow-up with an investor"""
    try:
        success = service.schedule_follow_up(investor_id, follow_up_date, notes)
        return {"success": success, "message": "Follow-up scheduled successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error scheduling follow-up: {str(e)}"
        )


@router.get("/follow-ups")
async def get_pending_follow_ups(
    days_ahead: int = Query(7, ge=1, le=30),
    service: InvestorManagementService = Depends(get_investor_service)
):
    """Get pending follow-ups for the next N days"""
    try:
        follow_ups = service.get_pending_follow_ups(days_ahead)
        return {"follow_ups": follow_ups}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving follow-ups: {str(e)}"
        )


# Investment History Endpoints

@router.post("/investments", response_model=InvestmentHistory)
async def record_investment(
    request: RecordInvestmentRequest,
    service: InvestorManagementService = Depends(get_investor_service)
):
    """Record a new investment by an investor"""
    try:
        investment = service.record_investment(request.dict())
        return investment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error recording investment: {str(e)}"
        )


@router.get("/investors/{investor_id}/investments", response_model=List[InvestmentHistory])
async def get_investor_investments(
    investor_id: UUID,
    service: InvestorManagementService = Depends(get_investor_service)
):
    """Get investment history for an investor"""
    try:
        investments = service.get_investor_investment_history(investor_id)
        return investments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving investments: {str(e)}"
        )


@router.put("/investments/{investment_id}/performance")
async def update_investment_performance(
    investment_id: UUID,
    actual_return: Decimal,
    service: InvestorManagementService = Depends(get_investor_service)
):
    """Update the actual return for an investment"""
    try:
        success = service.update_investment_performance(investment_id, actual_return)
        return {"success": success, "message": "Investment performance updated"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating investment performance: {str(e)}"
        )


# Performance and Analytics Endpoints

@router.get("/investors/{investor_id}/performance", response_model=InvestorPerformanceMetrics)
async def get_investor_performance(
    investor_id: UUID,
    service: InvestorManagementService = Depends(get_investor_service)
):
    """Get performance metrics for an investor"""
    try:
        performance = service.calculate_investor_performance(investor_id)
        return performance
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating investor performance: {str(e)}"
        )


@router.get("/analytics/top-performers")
async def get_top_performing_investors(
    limit: int = Query(10, ge=1, le=50),
    service: InvestorManagementService = Depends(get_investor_service)
):
    """Get top performing investors by ROI"""
    try:
        top_investors = service.get_top_performing_investors(limit)
        return {"top_investors": top_investors}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving top performers: {str(e)}"
        )


@router.get("/analytics", response_model=InvestorAnalytics)
async def get_investor_analytics(
    service: InvestorManagementService = Depends(get_investor_service)
):
    """Get comprehensive investor analytics"""
    try:
        analytics = service.generate_investor_analytics()
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating analytics: {str(e)}"
        )


# Deal Presentation Endpoints

@router.post("/presentations", response_model=InvestorDealPresentation)
async def create_deal_presentation(
    request: CreatePresentationRequest,
    service: InvestorManagementService = Depends(get_investor_service)
):
    """Create a deal presentation record"""
    try:
        presentation = service.create_deal_presentation(request.dict())
        return presentation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating presentation: {str(e)}"
        )


@router.post("/presentations/{presentation_id}/engagement")
async def track_presentation_engagement(
    presentation_id: UUID,
    engagement_type: str,
    service: InvestorManagementService = Depends(get_investor_service)
):
    """Track engagement with a deal presentation"""
    try:
        success = service.track_presentation_engagement(presentation_id, engagement_type)
        return {"success": success, "message": "Engagement tracked successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error tracking engagement: {str(e)}"
        )


@router.get("/analytics/presentations")
async def get_presentation_analytics(
    deal_id: Optional[UUID] = None,
    service: InvestorManagementService = Depends(get_investor_service)
):
    """Get analytics for deal presentations"""
    try:
        analytics = service.get_presentation_analytics(deal_id)
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating presentation analytics: {str(e)}"
        )


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "investor-management"}