"""
API router for funding source management.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.models.funding import (
    FundingSource, LoanProduct, FundingApplication, FundingSourceMatch,
    FundingSourcePerformance, FundingSearchCriteria, FundingAnalytics,
    FundingSourceTypeEnum, LoanTypeEnum, PropertyTypeEnum,
    FundingStatusEnum, ApplicationStatusEnum
)
from app.services.funding_source_service import FundingSourceService

router = APIRouter(prefix="/api/funding-management", tags=["funding-management"])


# Request/Response Models

class CreateFundingSourceRequest(BaseModel):
    name: str
    funding_type: FundingSourceTypeEnum
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    min_loan_amount: Optional[Decimal] = None
    max_loan_amount: Optional[Decimal] = None
    min_credit_score: Optional[int] = None
    max_ltv: Optional[Decimal] = None
    states_covered: List[str] = []
    nationwide: bool = False
    loan_types: List[LoanTypeEnum] = []
    property_types: List[PropertyTypeEnum] = []
    typical_rate_range_min: Optional[Decimal] = None
    typical_rate_range_max: Optional[Decimal] = None
    typical_processing_days: Optional[int] = None
    notes: Optional[str] = None
    tags: List[str] = []


class UpdateFundingSourceRequest(BaseModel):
    name: Optional[str] = None
    status: Optional[FundingStatusEnum] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    min_loan_amount: Optional[Decimal] = None
    max_loan_amount: Optional[Decimal] = None
    min_credit_score: Optional[int] = None
    max_ltv: Optional[Decimal] = None
    states_covered: Optional[List[str]] = None
    loan_types: Optional[List[LoanTypeEnum]] = None
    property_types: Optional[List[PropertyTypeEnum]] = None
    typical_rate_range_min: Optional[Decimal] = None
    typical_rate_range_max: Optional[Decimal] = None
    typical_processing_days: Optional[int] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class CreateLoanProductRequest(BaseModel):
    funding_source_id: UUID
    name: str
    loan_type: LoanTypeEnum
    property_types: List[PropertyTypeEnum] = []
    min_amount: Decimal
    max_amount: Decimal
    min_term_months: int
    max_term_months: int
    base_rate: Optional[Decimal] = None
    origination_fee: Optional[Decimal] = None
    min_credit_score: Optional[int] = None
    max_ltv: Optional[Decimal] = None
    typical_processing_days: Optional[int] = None


class CreateApplicationRequest(BaseModel):
    funding_source_id: UUID
    deal_id: UUID
    loan_amount: Decimal
    loan_type: LoanTypeEnum
    property_type: PropertyTypeEnum
    property_address: str
    property_value: Optional[Decimal] = None
    borrower_name: str
    borrower_email: Optional[str] = None
    borrower_phone: Optional[str] = None
    credit_score: Optional[int] = None
    annual_income: Optional[Decimal] = None


class DealFundingMatchRequest(BaseModel):
    deal_id: UUID
    loan_amount: Decimal
    loan_type: LoanTypeEnum
    property_type: PropertyTypeEnum
    property_value: Decimal
    state: str
    credit_score: Optional[int] = None
    ltv: Optional[Decimal] = None


class UpdateApplicationStatusRequest(BaseModel):
    status: ApplicationStatusEnum
    notes: Optional[str] = None
    approved_amount: Optional[Decimal] = None
    approved_rate: Optional[Decimal] = None
    approved_term_months: Optional[int] = None


# Dependency to get service instance
def get_funding_service() -> FundingSourceService:
    # In a real implementation, this would inject the database session
    return FundingSourceService(db=None)


# Funding Source Endpoints

@router.post("/sources", response_model=FundingSource)
async def create_funding_source(
    request: CreateFundingSourceRequest,
    service: FundingSourceService = Depends(get_funding_service)
):
    """Create a new funding source"""
    try:
        source_data = request.dict()
        source = service.create_funding_source(source_data)
        return source
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating funding source: {str(e)}"
        )


@router.get("/sources", response_model=List[FundingSource])
async def get_funding_sources(
    status_filter: Optional[FundingStatusEnum] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: FundingSourceService = Depends(get_funding_service)
):
    """Get all funding sources with optional filtering"""
    try:
        sources = service.get_all_funding_sources(
            status=status_filter, 
            limit=limit, 
            offset=offset
        )
        return sources
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving funding sources: {str(e)}"
        )


@router.get("/sources/{source_id}", response_model=FundingSource)
async def get_funding_source(
    source_id: UUID,
    service: FundingSourceService = Depends(get_funding_service)
):
    """Get funding source by ID"""
    try:
        source = service.get_funding_source(source_id)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Funding source not found"
            )
        return source
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving funding source: {str(e)}"
        )


@router.put("/sources/{source_id}", response_model=FundingSource)
async def update_funding_source(
    source_id: UUID,
    request: UpdateFundingSourceRequest,
    service: FundingSourceService = Depends(get_funding_service)
):
    """Update a funding source"""
    try:
        updates = {k: v for k, v in request.dict().items() if v is not None}
        source = service.update_funding_source(source_id, updates)
        return source
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating funding source: {str(e)}"
        )


@router.post("/sources/search", response_model=List[FundingSource])
async def search_funding_sources(
    criteria: FundingSearchCriteria,
    service: FundingSourceService = Depends(get_funding_service)
):
    """Search funding sources based on criteria"""
    try:
        sources = service.search_funding_sources(criteria)
        return sources
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error searching funding sources: {str(e)}"
        )


# Loan Product Endpoints

@router.post("/loan-products", response_model=LoanProduct)
async def create_loan_product(
    request: CreateLoanProductRequest,
    service: FundingSourceService = Depends(get_funding_service)
):
    """Create a new loan product"""
    try:
        product_data = request.dict()
        product = service.create_loan_product(product_data)
        return product
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating loan product: {str(e)}"
        )


@router.get("/sources/{source_id}/loan-products", response_model=List[LoanProduct])
async def get_loan_products(
    source_id: UUID,
    service: FundingSourceService = Depends(get_funding_service)
):
    """Get loan products for a funding source"""
    try:
        products = service.get_loan_products(source_id)
        return products
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving loan products: {str(e)}"
        )


@router.put("/loan-products/{product_id}", response_model=LoanProduct)
async def update_loan_product(
    product_id: UUID,
    updates: Dict[str, Any],
    service: FundingSourceService = Depends(get_funding_service)
):
    """Update a loan product"""
    try:
        product = service.update_loan_product(product_id, updates)
        return product
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating loan product: {str(e)}"
        )


# Deal Matching Endpoints

@router.post("/deals/{deal_id}/matches", response_model=List[FundingSourceMatch])
async def match_funding_sources_to_deal(
    deal_id: UUID,
    deal_data: DealFundingMatchRequest,
    service: FundingSourceService = Depends(get_funding_service)
):
    """Find funding sources that match a specific deal"""
    try:
        matches = service.match_funding_sources_to_deal(deal_id, deal_data.dict())
        return matches
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error matching funding sources to deal: {str(e)}"
        )


@router.post("/deals/compare-loans")
async def compare_loan_products(
    deal_data: DealFundingMatchRequest,
    source_ids: Optional[List[UUID]] = None,
    service: FundingSourceService = Depends(get_funding_service)
):
    """Compare loan products across funding sources"""
    try:
        comparisons = service.compare_loan_products(deal_data.dict(), source_ids)
        return {"comparisons": comparisons}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error comparing loan products: {str(e)}"
        )


# Application Management Endpoints

@router.post("/applications", response_model=FundingApplication)
async def create_funding_application(
    request: CreateApplicationRequest,
    service: FundingSourceService = Depends(get_funding_service)
):
    """Create a new funding application"""
    try:
        application = service.create_funding_application(request.dict())
        return application
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating funding application: {str(e)}"
        )


@router.put("/applications/{application_id}/status")
async def update_application_status(
    application_id: UUID,
    request: UpdateApplicationStatusRequest,
    service: FundingSourceService = Depends(get_funding_service)
):
    """Update application status"""
    try:
        success = service.update_application_status(
            application_id, 
            request.status, 
            request.notes
        )
        return {"success": success, "message": "Application status updated"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating application status: {str(e)}"
        )


@router.get("/deals/{deal_id}/applications", response_model=List[FundingApplication])
async def get_applications_by_deal(
    deal_id: UUID,
    service: FundingSourceService = Depends(get_funding_service)
):
    """Get all applications for a deal"""
    try:
        applications = service.get_applications_by_deal(deal_id)
        return applications
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving applications: {str(e)}"
        )


@router.get("/sources/{source_id}/applications", response_model=List[FundingApplication])
async def get_applications_by_source(
    source_id: UUID,
    service: FundingSourceService = Depends(get_funding_service)
):
    """Get all applications for a funding source"""
    try:
        applications = service.get_applications_by_source(source_id)
        return applications
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving applications: {str(e)}"
        )


@router.get("/applications/pending", response_model=List[FundingApplication])
async def get_pending_applications(
    service: FundingSourceService = Depends(get_funding_service)
):
    """Get all pending applications requiring follow-up"""
    try:
        applications = service.get_pending_applications()
        return applications
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving pending applications: {str(e)}"
        )


# Performance and Analytics Endpoints

@router.get("/sources/{source_id}/performance", response_model=FundingSourcePerformance)
async def get_source_performance(
    source_id: UUID,
    service: FundingSourceService = Depends(get_funding_service)
):
    """Get performance metrics for a funding source"""
    try:
        performance = service.calculate_source_performance(source_id)
        return performance
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating source performance: {str(e)}"
        )


@router.get("/analytics/top-performers")
async def get_top_performing_sources(
    limit: int = Query(10, ge=1, le=50),
    service: FundingSourceService = Depends(get_funding_service)
):
    """Get top performing funding sources"""
    try:
        top_sources = service.get_top_performing_sources(limit)
        return {"top_sources": top_sources}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving top performers: {str(e)}"
        )


@router.get("/analytics", response_model=FundingAnalytics)
async def get_funding_analytics(
    service: FundingSourceService = Depends(get_funding_service)
):
    """Get comprehensive funding analytics"""
    try:
        analytics = service.generate_funding_analytics()
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating analytics: {str(e)}"
        )


# Relationship Management Endpoints

@router.post("/sources/{source_id}/contact")
async def update_relationship_contact(
    source_id: UUID,
    contact_date: datetime,
    notes: str = "",
    service: FundingSourceService = Depends(get_funding_service)
):
    """Update last contact date for a funding source relationship"""
    try:
        success = service.update_relationship_contact(source_id, contact_date, notes)
        return {"success": success, "message": "Relationship contact updated"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating relationship contact: {str(e)}"
        )


@router.get("/relationships/reminders")
async def get_relationship_reminders(
    days_ahead: int = Query(30, ge=1, le=365),
    service: FundingSourceService = Depends(get_funding_service)
):
    """Get funding sources that need relationship maintenance"""
    try:
        reminders = service.get_relationship_reminders(days_ahead)
        return {"reminders": reminders}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving relationship reminders: {str(e)}"
        )


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "funding-management"}