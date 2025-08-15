"""
Portfolio Management API Router for the Real Estate Empire platform.

This router provides endpoints for portfolio CRUD operations, property management,
performance tracking, and analytics.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.portfolio import (
    PortfolioCreate, PortfolioUpdate, PortfolioResponse,
    PortfolioPropertyCreate, PortfolioPropertyUpdate, PortfolioPropertyResponse,
    PropertyPerformanceCreate, PropertyPerformanceResponse,
    PortfolioSummary, PortfolioAnalytics
)
from app.services.portfolio_management_service import get_portfolio_management_service
from app.services.portfolio_performance_service import get_portfolio_performance_service

router = APIRouter(prefix="/portfolio", tags=["Portfolio Management"])


# Portfolio CRUD Endpoints

@router.post("/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    db: Session = Depends(get_db)
):
    """Create a new portfolio."""
    try:
        service = get_portfolio_management_service(db)
        return service.create_portfolio(portfolio_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating portfolio: {str(e)}"
        )


@router.get("/", response_model=List[PortfolioResponse])
async def get_portfolios(
    skip: int = Query(0, ge=0, description="Number of portfolios to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of portfolios to return"),
    db: Session = Depends(get_db)
):
    """Get all portfolios with pagination."""
    try:
        service = get_portfolio_management_service(db)
        return service.get_portfolios(skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving portfolios: {str(e)}"
        )


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get a specific portfolio by ID."""
    try:
        service = get_portfolio_management_service(db)
        portfolio = service.get_portfolio(portfolio_id)
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio {portfolio_id} not found"
            )
        return portfolio
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving portfolio: {str(e)}"
        )


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: uuid.UUID,
    portfolio_data: PortfolioUpdate,
    db: Session = Depends(get_db)
):
    """Update a portfolio."""
    try:
        service = get_portfolio_management_service(db)
        portfolio = service.update_portfolio(portfolio_id, portfolio_data)
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio {portfolio_id} not found"
            )
        return portfolio
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating portfolio: {str(e)}"
        )


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Delete a portfolio."""
    try:
        service = get_portfolio_management_service(db)
        success = service.delete_portfolio(portfolio_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio {portfolio_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting portfolio: {str(e)}"
        )


# Portfolio Property Management Endpoints

@router.post("/{portfolio_id}/properties", response_model=PortfolioPropertyResponse, status_code=status.HTTP_201_CREATED)
async def add_property_to_portfolio(
    portfolio_id: uuid.UUID,
    property_data: PortfolioPropertyCreate,
    db: Session = Depends(get_db)
):
    """Add a property to a portfolio."""
    try:
        service = get_portfolio_management_service(db)
        return service.add_property_to_portfolio(portfolio_id, property_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding property to portfolio: {str(e)}"
        )


@router.get("/{portfolio_id}/properties", response_model=List[PortfolioPropertyResponse])
async def get_portfolio_properties(
    portfolio_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get all properties in a portfolio."""
    try:
        service = get_portfolio_management_service(db)
        return service.get_portfolio_properties(portfolio_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving portfolio properties: {str(e)}"
        )


@router.get("/properties/{portfolio_property_id}", response_model=PortfolioPropertyResponse)
async def get_portfolio_property(
    portfolio_property_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get a specific portfolio property."""
    try:
        service = get_portfolio_management_service(db)
        property_obj = service.get_portfolio_property(portfolio_property_id)
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio property {portfolio_property_id} not found"
            )
        return property_obj
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving portfolio property: {str(e)}"
        )


@router.put("/properties/{portfolio_property_id}", response_model=PortfolioPropertyResponse)
async def update_portfolio_property(
    portfolio_property_id: uuid.UUID,
    property_data: PortfolioPropertyUpdate,
    db: Session = Depends(get_db)
):
    """Update a portfolio property."""
    try:
        service = get_portfolio_management_service(db)
        property_obj = service.update_portfolio_property(portfolio_property_id, property_data)
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio property {portfolio_property_id} not found"
            )
        return property_obj
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating portfolio property: {str(e)}"
        )


@router.delete("/properties/{portfolio_property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_property_from_portfolio(
    portfolio_property_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Remove a property from a portfolio."""
    try:
        service = get_portfolio_management_service(db)
        success = service.remove_property_from_portfolio(portfolio_property_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio property {portfolio_property_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing property from portfolio: {str(e)}"
        )


# Performance Tracking Endpoints

@router.post("/properties/{portfolio_property_id}/performance", response_model=PropertyPerformanceResponse, status_code=status.HTTP_201_CREATED)
async def record_property_performance(
    portfolio_property_id: uuid.UUID,
    performance_data: PropertyPerformanceCreate,
    db: Session = Depends(get_db)
):
    """Record performance data for a portfolio property."""
    try:
        # Ensure the portfolio_property_id matches
        performance_data.portfolio_property_id = portfolio_property_id
        
        service = get_portfolio_management_service(db)
        return service.record_property_performance(performance_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error recording property performance: {str(e)}"
        )


@router.get("/properties/{portfolio_property_id}/performance", response_model=List[PropertyPerformanceResponse])
async def get_property_performance_history(
    portfolio_property_id: uuid.UUID,
    limit: int = Query(12, ge=1, le=100, description="Maximum number of performance records to return"),
    db: Session = Depends(get_db)
):
    """Get performance history for a portfolio property."""
    try:
        service = get_portfolio_management_service(db)
        return service.get_property_performance_history(portfolio_property_id, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving property performance history: {str(e)}"
        )


# Portfolio Analytics Endpoints

@router.get("/{portfolio_id}/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    portfolio_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get a comprehensive portfolio summary."""
    try:
        service = get_portfolio_management_service(db)
        summary = service.get_portfolio_summary(portfolio_id)
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio {portfolio_id} not found"
            )
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving portfolio summary: {str(e)}"
        )


@router.get("/{portfolio_id}/analytics", response_model=PortfolioAnalytics)
async def get_portfolio_analytics(
    portfolio_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get comprehensive analytics for a portfolio."""
    try:
        performance_service = get_portfolio_performance_service(db)
        return performance_service.get_portfolio_analytics(portfolio_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving portfolio analytics: {str(e)}"
        )


@router.get("/{portfolio_id}/dashboard")
async def get_portfolio_dashboard(
    portfolio_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get dashboard data for a portfolio."""
    try:
        service = get_portfolio_management_service(db)
        return service.get_portfolio_dashboard_data(portfolio_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving portfolio dashboard data: {str(e)}"
        )


@router.get("/{portfolio_id}/performance")
async def get_portfolio_performance(
    portfolio_id: uuid.UUID,
    period_start: Optional[datetime] = Query(None, description="Start date for performance period"),
    period_end: Optional[datetime] = Query(None, description="End date for performance period"),
    db: Session = Depends(get_db)
):
    """Get portfolio performance metrics for a specific period."""
    try:
        # Default to last 12 months if no period specified
        if not period_end:
            period_end = datetime.now()
        if not period_start:
            period_start = period_end - timedelta(days=365)
        
        performance_service = get_portfolio_performance_service(db)
        return performance_service.calculate_portfolio_performance(portfolio_id, period_start, period_end)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating portfolio performance: {str(e)}"
        )


@router.get("/{portfolio_id}/report")
async def generate_portfolio_report(
    portfolio_id: uuid.UUID,
    period_start: Optional[datetime] = Query(None, description="Start date for report period"),
    period_end: Optional[datetime] = Query(None, description="End date for report period"),
    db: Session = Depends(get_db)
):
    """Generate a comprehensive performance report for a portfolio."""
    try:
        # Default to last 12 months if no period specified
        if not period_end:
            period_end = datetime.now()
        if not period_start:
            period_start = period_end - timedelta(days=365)
        
        performance_service = get_portfolio_performance_service(db)
        return performance_service.generate_performance_report(portfolio_id, period_start, period_end)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating portfolio report: {str(e)}"
        )


# Bulk Operations

@router.put("/{portfolio_id}/properties/values")
async def bulk_update_property_values(
    portfolio_id: uuid.UUID,
    value_updates: Dict[str, float],
    db: Session = Depends(get_db)
):
    """Bulk update property values in a portfolio."""
    try:
        # Convert string UUIDs to UUID objects
        uuid_updates = {uuid.UUID(prop_id): value for prop_id, value in value_updates.items()}
        
        service = get_portfolio_management_service(db)
        success = service.bulk_update_property_values(portfolio_id, uuid_updates)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No properties were updated"
            )
        
        return {"message": f"Successfully updated {len(uuid_updates)} property values"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating property values: {str(e)}"
        )


@router.post("/{portfolio_id}/refresh-metrics")
async def refresh_portfolio_metrics(
    portfolio_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Refresh cached portfolio metrics."""
    try:
        performance_service = get_portfolio_performance_service(db)
        success = performance_service.update_portfolio_metrics(portfolio_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio {portfolio_id} not found"
            )
        
        return {"message": "Portfolio metrics refreshed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error refreshing portfolio metrics: {str(e)}"
        )