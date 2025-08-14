"""
Property Analysis API endpoints
Implements endpoints for property creation/update, financial analysis, comparable analysis, and repair estimation
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import logging
from datetime import datetime

from ...core.database import get_db
from ...models.property import (
    PropertyCreate, PropertyUpdate, PropertyResponse, 
    PropertyAnalysisCreate, PropertyAnalysisResponse,
    PropertyDB, PropertyAnalysisDB
)
from ...agents.analyst_models import PropertyAnalysis, PropertyValuation, RepairEstimate, FinancialMetrics
from ...agents.analyst_agent import AnalystAgent
from ...core.agent_state import AgentState, StateManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize analyst agent for analysis operations
analyst_agent = AnalystAgent()

@router.post("/", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_property(
    property_data: PropertyCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new property record
    
    - **property_data**: Property information including address, characteristics, and financial data
    - Returns the created property with assigned ID
    """
    try:
        # Create property database record
        db_property = PropertyDB(**property_data.model_dump())
        db.add(db_property)
        db.commit()
        db.refresh(db_property)
        
        logger.info(f"Created property: {db_property.id}")
        
        return PropertyResponse.model_validate(db_property)
        
    except Exception as e:
        logger.error(f"Error creating property: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create property: {str(e)}"
        )

@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get property by ID
    
    - **property_id**: UUID of the property to retrieve
    - Returns property details
    """
    try:
        property_record = db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
        
        if not property_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        return PropertyResponse.model_validate(property_record)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve property: {str(e)}"
        )

@router.put("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: uuid.UUID,
    property_update: PropertyUpdate,
    db: Session = Depends(get_db)
):
    """
    Update property information
    
    - **property_id**: UUID of the property to update
    - **property_update**: Updated property information
    - Returns the updated property
    """
    try:
        property_record = db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
        
        if not property_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Update only provided fields
        update_data = property_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(property_record, field, value)
        
        property_record.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(property_record)
        
        logger.info(f"Updated property: {property_id}")
        
        return PropertyResponse.model_validate(property_record)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating property {property_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update property: {str(e)}"
        )

@router.get("/", response_model=List[PropertyResponse])
async def list_properties(
    skip: int = 0,
    limit: int = 100,
    property_type: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List properties with optional filtering
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **property_type**: Filter by property type
    - **city**: Filter by city
    - **state**: Filter by state
    - Returns list of properties
    """
    try:
        query = db.query(PropertyDB)
        
        # Apply filters
        if property_type:
            query = query.filter(PropertyDB.property_type == property_type)
        if city:
            query = query.filter(PropertyDB.city.ilike(f"%{city}%"))
        if state:
            query = query.filter(PropertyDB.state.ilike(f"%{state}%"))
        
        properties = query.offset(skip).limit(limit).all()
        
        return [PropertyResponse.model_validate(prop) for prop in properties]
        
    except Exception as e:
        logger.error(f"Error listing properties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list properties: {str(e)}"
        )

@router.post("/{property_id}/analyze", response_model=Dict[str, Any])
async def analyze_property_financial(
    property_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    analysis_type: str = "comprehensive",
    db: Session = Depends(get_db)
):
    """
    Perform comprehensive financial analysis on a property
    
    - **property_id**: UUID of the property to analyze
    - **analysis_type**: Type of analysis (comprehensive, quick, detailed)
    - Returns detailed financial analysis including valuation, repair estimates, and investment metrics
    """
    try:
        # Get property from database
        property_record = db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
        
        if not property_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Convert property to deal format for analyst agent
        deal_data = {
            "id": str(property_record.id),
            "property": {
                "address": property_record.address,
                "city": property_record.city,
                "state": property_record.state,
                "zip_code": property_record.zip_code,
                "property_type": property_record.property_type,
                "bedrooms": property_record.bedrooms,
                "bathrooms": property_record.bathrooms,
                "square_feet": property_record.square_feet,
                "lot_size": property_record.lot_size,
                "year_built": property_record.year_built,
                "current_value": property_record.current_value,
                "listing_price": property_record.listing_price,
                "condition_score": property_record.condition_score,
                "photos": property_record.photos or [],
                "features": property_record.features or {}
            }
        }
        
        # Create agent state
        state = StateManager.create_initial_state()
        
        # Execute analysis based on type
        if analysis_type == "comprehensive":
            analysis_result = await analyst_agent.execute_task("analyze_property", {"deal": deal_data}, state)
        elif analysis_type == "valuation":
            analysis_result = await analyst_agent.execute_task("valuate_property", {"deal": deal_data}, state)
        elif analysis_type == "financial":
            analysis_result = await analyst_agent.execute_task("calculate_financials", {"deal": deal_data}, state)
        else:
            analysis_result = await analyst_agent.execute_task("analyze_property", {"deal": deal_data}, state)
        
        if not analysis_result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Analysis failed: {analysis_result.get('error', 'Unknown error')}"
            )
        
        # Store analysis results in database
        analysis_data = analysis_result.get("analysis", {})
        if analysis_data:
            db_analysis = PropertyAnalysisDB(
                property_id=property_id,
                analysis_type=analysis_type,
                arv_estimate=analysis_data.get("valuation", {}).get("arv"),
                current_value_estimate=analysis_data.get("valuation", {}).get("current_value"),
                confidence_score=analysis_data.get("confidence_level"),
                repair_estimate=analysis_data.get("repair_estimate", {}).get("total_cost"),
                potential_profit=analysis_data.get("financial_metrics", {}).get("flip_profit"),
                roi_estimate=analysis_data.get("financial_metrics", {}).get("roi"),
                cash_flow_estimate=analysis_data.get("financial_metrics", {}).get("monthly_cash_flow"),
                cap_rate=analysis_data.get("financial_metrics", {}).get("cap_rate"),
                analysis_data=analysis_data,
                comparable_properties=analysis_data.get("comparable_properties", [])
            )
            
            db.add(db_analysis)
            db.commit()
            db.refresh(db_analysis)
        
        logger.info(f"Completed {analysis_type} analysis for property: {property_id}")
        
        return {
            "property_id": str(property_id),
            "analysis_type": analysis_type,
            "analysis_id": str(db_analysis.id) if analysis_data else None,
            "success": True,
            "analysis": analysis_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze property: {str(e)}"
        )

@router.get("/{property_id}/comparables", response_model=Dict[str, Any])
async def get_comparable_properties(
    property_id: uuid.UUID,
    max_distance: float = 2.0,
    max_age_days: int = 180,
    min_comps: int = 3,
    db: Session = Depends(get_db)
):
    """
    Get comparable properties for valuation analysis
    
    - **property_id**: UUID of the property to find comparables for
    - **max_distance**: Maximum distance in miles for comparable properties
    - **max_age_days**: Maximum age in days for comparable sales
    - **min_comps**: Minimum number of comparable properties to find
    - Returns list of comparable properties with similarity scores and adjustments
    """
    try:
        # Get property from database
        property_record = db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
        
        if not property_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Use analyst agent's comparable finder tool
        from ...agents.analyst_tools import ComparablePropertyFinderTool
        
        comp_finder = ComparablePropertyFinderTool()
        
        comp_result = await comp_finder.execute(
            property_address=property_record.address,
            property_type=property_record.property_type,
            bedrooms=property_record.bedrooms or 3,
            bathrooms=property_record.bathrooms or 2,
            square_feet=property_record.square_feet or 1500,
            max_distance=max_distance,
            max_age=max_age_days
        )
        
        if not comp_result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to find comparable properties"
            )
        
        comparables = comp_result.get("comparable_properties", [])
        valuation_estimate = comp_result.get("valuation_estimate", {})
        
        # Filter to minimum number of comparables
        if len(comparables) < min_comps:
            logger.warning(f"Found only {len(comparables)} comparables, requested minimum {min_comps}")
        
        logger.info(f"Found {len(comparables)} comparable properties for property: {property_id}")
        
        return {
            "property_id": str(property_id),
            "comparable_properties": comparables[:10],  # Limit to top 10
            "valuation_estimate": valuation_estimate,
            "search_criteria": {
                "max_distance_miles": max_distance,
                "max_age_days": max_age_days,
                "min_comparables": min_comps
            },
            "total_found": len(comparables),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding comparables for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find comparable properties: {str(e)}"
        )

@router.post("/{property_id}/repair-estimate", response_model=Dict[str, Any])
async def estimate_repair_costs(
    property_id: uuid.UUID,
    photos: Optional[List[str]] = None,
    description: Optional[str] = None,
    condition_override: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Estimate repair costs for a property using AI analysis
    
    - **property_id**: UUID of the property to estimate repairs for
    - **photos**: Optional list of property photo URLs for AI analysis
    - **description**: Optional property condition description
    - **condition_override**: Optional condition override (excellent, good, fair, poor)
    - Returns detailed repair cost estimate with line items and confidence score
    """
    try:
        # Get property from database
        property_record = db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
        
        if not property_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Prepare deal data for repair estimation
        deal_data = {
            "id": str(property_record.id),
            "property": {
                "address": property_record.address,
                "property_type": property_record.property_type,
                "square_feet": property_record.square_feet or 1500,
                "year_built": property_record.year_built,
                "condition_score": property_record.condition_score,
                "photos": photos or property_record.photos or [],
                "description": description or property_record.description or "",
                "features": property_record.features or {}
            }
        }
        
        # Override condition if provided
        if condition_override:
            deal_data["property"]["condition_override"] = condition_override
        
        # Create agent state
        state = StateManager.create_initial_state()
        
        # Execute repair estimation
        repair_result = await analyst_agent.execute_task("estimate_repairs", {"deal": deal_data}, state)
        
        if not repair_result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Repair estimation failed: {repair_result.get('error', 'Unknown error')}"
            )
        
        repair_estimate = repair_result.get("repair_estimate", {})
        
        logger.info(f"Completed repair estimation for property: {property_id}")
        
        return {
            "property_id": str(property_id),
            "repair_estimate": repair_estimate,
            "analysis_inputs": {
                "photos_provided": len(photos) if photos else 0,
                "description_provided": bool(description),
                "condition_override": condition_override
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error estimating repairs for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to estimate repair costs: {str(e)}"
        )

@router.get("/{property_id}/analyses", response_model=List[PropertyAnalysisResponse])
async def get_property_analyses(
    property_id: uuid.UUID,
    analysis_type: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get historical analyses for a property
    
    - **property_id**: UUID of the property
    - **analysis_type**: Optional filter by analysis type
    - **limit**: Maximum number of analyses to return
    - Returns list of historical property analyses
    """
    try:
        query = db.query(PropertyAnalysisDB).filter(PropertyAnalysisDB.property_id == property_id)
        
        if analysis_type:
            query = query.filter(PropertyAnalysisDB.analysis_type == analysis_type)
        
        analyses = query.order_by(PropertyAnalysisDB.created_at.desc()).limit(limit).all()
        
        return [PropertyAnalysisResponse.model_validate(analysis) for analysis in analyses]
        
    except Exception as e:
        logger.error(f"Error retrieving analyses for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve property analyses: {str(e)}"
        )

@router.delete("/{property_id}")
async def delete_property(
    property_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a property and all associated analyses
    
    - **property_id**: UUID of the property to delete
    - Returns confirmation of deletion
    """
    try:
        property_record = db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
        
        if not property_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Delete associated analyses first
        db.query(PropertyAnalysisDB).filter(PropertyAnalysisDB.property_id == property_id).delete()
        
        # Delete property
        db.delete(property_record)
        db.commit()
        
        logger.info(f"Deleted property: {property_id}")
        
        return {
            "message": "Property deleted successfully",
            "property_id": str(property_id),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting property {property_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete property: {str(e)}"
        )