"""
Lead Management API endpoints
Implements CRUD operations, filtering, sorting, assignment, and status management for property leads
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Dict, Any, Optional
import uuid
import logging
from datetime import datetime, timedelta

from ...core.database import get_db
from ...models.lead import (
    PropertyLeadCreate, PropertyLeadUpdate, PropertyLeadResponse,
    CommunicationCreate, CommunicationResponse,
    PropertyLeadDB, CommunicationDB,
    LeadStatusEnum, LeadSourceEnum, ContactMethodEnum
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/leads", tags=["Lead Management"])


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
        
        logger.info(f"Created lead: {db_lead.id} for property: {db_lead.property_id}")
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


@router.put("/{lead_id}", response_model=PropertyLeadResponse)
async def update_lead(
    lead_id: uuid.UUID,
    lead_update: PropertyLeadUpdate,
    db: Session = Depends(get_db)
):
    """Update lead information."""
    try:
        lead = db.query(PropertyLeadDB).filter(PropertyLeadDB.id == lead_id).first()
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        # Update only provided fields
        update_data = lead_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lead, field, value)
        
        lead.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(lead)
        
        logger.info(f"Updated lead: {lead_id}")
        return PropertyLeadResponse.model_validate(lead)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating lead {lead_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update lead: {str(e)}"
        )


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Delete a lead and all associated communications."""
    try:
        lead = db.query(PropertyLeadDB).filter(PropertyLeadDB.id == lead_id).first()
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        # Delete associated communications first
        db.query(CommunicationDB).filter(CommunicationDB.lead_id == lead_id).delete()
        
        # Delete the lead
        db.delete(lead)
        db.commit()
        
        logger.info(f"Deleted lead: {lead_id}")
        return {"message": "Lead deleted successfully", "lead_id": str(lead_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting lead {lead_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete lead: {str(e)}"
        )


@router.get("/", response_model=List[PropertyLeadResponse])
async def list_leads(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    status: Optional[LeadStatusEnum] = Query(None, description="Filter by lead status"),
    source: Optional[LeadSourceEnum] = Query(None, description="Filter by lead source"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned user"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum lead score"),
    max_score: Optional[float] = Query(None, ge=0, le=100, description="Maximum lead score"),
    search: Optional[str] = Query(None, description="Search in owner name, email, phone, or notes"),
    sort_by: Optional[str] = Query("created_at", description="Field to sort by"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db)
):
    """List leads with filtering, sorting, and pagination."""
    try:
        query = db.query(PropertyLeadDB)
        
        # Apply filters
        if status:
            query = query.filter(PropertyLeadDB.status == status)
        
        if source:
            query = query.filter(PropertyLeadDB.source == source)
        
        if assigned_to:
            query = query.filter(PropertyLeadDB.assigned_to == assigned_to)
        
        if min_score is not None:
            query = query.filter(PropertyLeadDB.lead_score >= min_score)
        
        if max_score is not None:
            query = query.filter(PropertyLeadDB.lead_score <= max_score)
        
        if search:
            search_filter = or_(
                PropertyLeadDB.owner_name.ilike(f"%{search}%"),
                PropertyLeadDB.owner_email.ilike(f"%{search}%"),
                PropertyLeadDB.owner_phone.ilike(f"%{search}%"),
                PropertyLeadDB.notes.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Apply sorting
        if hasattr(PropertyLeadDB, sort_by):
            sort_column = getattr(PropertyLeadDB, sort_by)
            if sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        else:
            # Default sort by created_at desc
            query = query.order_by(desc(PropertyLeadDB.created_at))
        
        # Apply pagination
        leads = query.offset(skip).limit(limit).all()
        
        return [PropertyLeadResponse.model_validate(lead) for lead in leads]
        
    except Exception as e:
        logger.error(f"Error listing leads: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list leads: {str(e)}"
        )


@router.patch("/{lead_id}/status", response_model=PropertyLeadResponse)
async def update_lead_status(
    lead_id: uuid.UUID,
    new_status: LeadStatusEnum,
    db: Session = Depends(get_db)
):
    """Update lead status."""
    try:
        lead = db.query(PropertyLeadDB).filter(PropertyLeadDB.id == lead_id).first()
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        old_status = lead.status
        lead.status = new_status
        lead.updated_at = datetime.utcnow()
        
        # Update contact tracking based on status
        if new_status == LeadStatusEnum.CONTACTED and old_status == LeadStatusEnum.NEW:
            lead.first_contact_date = datetime.utcnow()
            lead.last_contact_date = datetime.utcnow()
        elif new_status in [LeadStatusEnum.CONTACTED, LeadStatusEnum.INTERESTED]:
            lead.last_contact_date = datetime.utcnow()
        
        db.commit()
        db.refresh(lead)
        
        logger.info(f"Updated lead {lead_id} status from {old_status} to {new_status}")
        return PropertyLeadResponse.model_validate(lead)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating lead status {lead_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update lead status: {str(e)}"
        )


@router.patch("/{lead_id}/assign", response_model=PropertyLeadResponse)
async def assign_lead(
    lead_id: uuid.UUID,
    assigned_to: str,
    db: Session = Depends(get_db)
):
    """Assign lead to a user."""
    try:
        lead = db.query(PropertyLeadDB).filter(PropertyLeadDB.id == lead_id).first()
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        old_assignee = lead.assigned_to
        lead.assigned_to = assigned_to
        lead.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(lead)
        
        logger.info(f"Assigned lead {lead_id} from {old_assignee} to {assigned_to}")
        return PropertyLeadResponse.model_validate(lead)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning lead {lead_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign lead: {str(e)}"
        )


@router.post("/{lead_id}/communications", response_model=CommunicationResponse, status_code=status.HTTP_201_CREATED)
async def create_communication(
    lead_id: uuid.UUID,
    communication_data: CommunicationCreate,
    db: Session = Depends(get_db)
):
    """Create a communication record for a lead."""
    try:
        # Verify lead exists
        lead = db.query(PropertyLeadDB).filter(PropertyLeadDB.id == lead_id).first()
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        # Ensure lead_id matches
        communication_data.lead_id = lead_id
        
        # Create communication record
        db_communication = CommunicationDB(**communication_data.model_dump())
        db.add(db_communication)
        
        # Update lead contact tracking
        lead.contact_attempts += 1
        lead.last_contact_date = datetime.utcnow()
        lead.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_communication)
        
        logger.info(f"Created communication: {db_communication.id} for lead: {lead_id}")
        return CommunicationResponse.model_validate(db_communication)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating communication for lead {lead_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create communication: {str(e)}"
        )


@router.get("/{lead_id}/communications", response_model=List[CommunicationResponse])
async def get_lead_communications(
    lead_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    channel: Optional[str] = Query(None, description="Filter by communication channel"),
    direction: Optional[str] = Query(None, description="Filter by direction (inbound/outbound)"),
    db: Session = Depends(get_db)
):
    """Get communications for a lead."""
    try:
        # Verify lead exists
        lead = db.query(PropertyLeadDB).filter(PropertyLeadDB.id == lead_id).first()
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        query = db.query(CommunicationDB).filter(CommunicationDB.lead_id == lead_id)
        
        # Apply filters
        if channel:
            query = query.filter(CommunicationDB.channel == channel)
        
        if direction:
            query = query.filter(CommunicationDB.direction == direction)
        
        # Order by created_at desc (most recent first)
        query = query.order_by(desc(CommunicationDB.created_at))
        
        # Apply pagination
        communications = query.offset(skip).limit(limit).all()
        
        return [CommunicationResponse.model_validate(comm) for comm in communications]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting communications for lead {lead_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get communications: {str(e)}"
        )


@router.get("/stats/summary")
async def get_lead_stats(
    assigned_to: Optional[str] = Query(None, description="Filter stats by assigned user"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include in stats"),
    db: Session = Depends(get_db)
):
    """Get lead statistics and summary."""
    try:
        # Calculate date range
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(PropertyLeadDB)
        
        # Apply filters
        if assigned_to:
            query = query.filter(PropertyLeadDB.assigned_to == assigned_to)
        
        # Get total counts
        total_leads = query.count()
        new_leads = query.filter(PropertyLeadDB.created_at >= start_date).count()
        
        # Get status distribution
        status_stats = (
            query.with_entities(
                PropertyLeadDB.status,
                func.count(PropertyLeadDB.id).label('count')
            )
            .group_by(PropertyLeadDB.status)
            .all()
        )
        
        # Get source distribution
        source_stats = (
            query.with_entities(
                PropertyLeadDB.source,
                func.count(PropertyLeadDB.id).label('count')
            )
            .group_by(PropertyLeadDB.source)
            .all()
        )
        
        # Get average lead score
        from sqlalchemy import func
        avg_score = query.with_entities(
            func.avg(PropertyLeadDB.lead_score)
        ).scalar() or 0
        
        # Get conversion metrics
        contacted_leads = query.filter(
            PropertyLeadDB.status.in_([
                LeadStatusEnum.CONTACTED,
                LeadStatusEnum.INTERESTED,
                LeadStatusEnum.QUALIFIED,
                LeadStatusEnum.UNDER_CONTRACT,
                LeadStatusEnum.CLOSED
            ])
        ).count()
        
        qualified_leads = query.filter(
            PropertyLeadDB.status.in_([
                LeadStatusEnum.QUALIFIED,
                LeadStatusEnum.UNDER_CONTRACT,
                LeadStatusEnum.CLOSED
            ])
        ).count()
        
        closed_leads = query.filter(PropertyLeadDB.status == LeadStatusEnum.CLOSED).count()
        
        # Calculate conversion rates
        contact_rate = (contacted_leads / total_leads * 100) if total_leads > 0 else 0
        qualification_rate = (qualified_leads / contacted_leads * 100) if contacted_leads > 0 else 0
        close_rate = (closed_leads / qualified_leads * 100) if qualified_leads > 0 else 0
        
        return {
            "summary": {
                "total_leads": total_leads,
                "new_leads_last_30_days": new_leads,
                "average_lead_score": round(avg_score, 2),
                "contact_rate": round(contact_rate, 2),
                "qualification_rate": round(qualification_rate, 2),
                "close_rate": round(close_rate, 2)
            },
            "status_distribution": {status: count for status, count in status_stats},
            "source_distribution": {source: count for source, count in source_stats},
            "conversion_funnel": {
                "total_leads": total_leads,
                "contacted": contacted_leads,
                "qualified": qualified_leads,
                "closed": closed_leads
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting lead stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get lead stats: {str(e)}"
        )

@router.put("/{lead_id}", response_model=PropertyLeadResponse)
async def update_lead(
    lead_id: uuid.UUID,
    lead_update: PropertyLeadUpdate,
    db: Session = Depends(get_db)
):
    """Update lead information."""
    try:
        lead = db.query(PropertyLeadDB).filter(PropertyLeadDB.id == lead_id).first()
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        # Update only provided fields
        update_data = lead_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lead, field, value)
        
        from datetime import datetime
        lead.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(lead)
        
        logger.info(f"Updated lead: {lead_id}")
        return PropertyLeadResponse.model_validate(lead)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating lead {lead_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update lead: {str(e)}"
        )


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Delete a lead and all associated communications."""
    try:
        lead = db.query(PropertyLeadDB).filter(PropertyLeadDB.id == lead_id).first()
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        # Delete the lead
        db.delete(lead)
        db.commit()
        
        logger.info(f"Deleted lead: {lead_id}")
        return {"message": "Lead deleted successfully", "lead_id": str(lead_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting lead {lead_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete lead: {str(e)}"
        )