"""
Simple Lead Management API endpoints for testing
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import logging

from ...core.database import get_db
from ...models.lead import (
    PropertyLeadCreate, PropertyLeadResponse,
    PropertyLeadDB, LeadStatusEnum
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/leads", tags=["Lead Management"])


@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify router is working."""
    return {"message": "Lead management API is working"}


@router.post("/", response_model=PropertyLeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: PropertyLeadCreate,
    db: Session = Depends(get_db)
):
    """Create a new property lead."""
    try:
        db_lead = PropertyLeadDB(**lead_data.model_dump())
        db.add(db_lead)
        db.commit()
        db.refresh(db_lead)
        
        logger.info(f"Created lead: {db_lead.id}")
        return PropertyLeadResponse.model_validate(db_lead)
        
    except Exception as e:
        logger.error(f"Error creating lead: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lead: {str(e)}"
        )


@router.get("/{lead_id}", response_model=PropertyLeadResponse)
async def get_lead(
    lead_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get lead by ID."""
    try:
        lead = db.query(PropertyLeadDB).filter(PropertyLeadDB.id == lead_id).first()
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        return PropertyLeadResponse.model_validate(lead)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving lead {lead_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve lead: {str(e)}"
        )