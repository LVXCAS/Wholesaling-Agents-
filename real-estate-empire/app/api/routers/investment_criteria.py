"""
Investment Criteria API Router

This module provides REST API endpoints for managing investment criteria,
evaluating properties, and working with criteria templates.
"""

from typing import List, Optional, Dict, Any
import uuid
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.investment_criteria import (
    InvestmentCriteria, CriteriaTemplate, CriteriaMatch, 
    CriteriaMatchSummary, StrategyTypeEnum
)
from app.models.property import PropertyCreate
from app.services.investment_criteria_service import (
    InvestmentCriteriaService, CriteriaTemplateService
)

router = APIRouter(prefix="/api/investment-criteria", tags=["Investment Criteria"])


@router.post("/criteria", response_model=InvestmentCriteria)
async def create_criteria(
    criteria: InvestmentCriteria,
    db: Session = Depends(get_db)
):
    """Create new investment criteria"""
    service = InvestmentCriteriaService(db)
    try:
        return service.create_criteria(criteria)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/criteria", response_model=List[InvestmentCriteria])
async def list_criteria(
    active_only: bool = Query(True, description="Only return active criteria"),
    db: Session = Depends(get_db)
):
    """List all investment criteria"""
    service = InvestmentCriteriaService(db)
    return service.list_criteria(active_only=active_only)


@router.get("/criteria/{criteria_id}", response_model=InvestmentCriteria)
async def get_criteria(
    criteria_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get investment criteria by ID"""
    service = InvestmentCriteriaService(db)
    criteria = service.get_criteria(criteria_id)
    if not criteria:
        raise HTTPException(status_code=404, detail="Criteria not found")
    return criteria


@router.put("/criteria/{criteria_id}", response_model=InvestmentCriteria)
async def update_criteria(
    criteria_id: uuid.UUID,
    updates: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update investment criteria"""
    service = InvestmentCriteriaService(db)
    criteria = service.update_criteria(criteria_id, updates)
    if not criteria:
        raise HTTPException(status_code=404, detail="Criteria not found")
    return criteria


@router.delete("/criteria/{criteria_id}")
async def delete_criteria(
    criteria_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Delete investment criteria"""
    service = InvestmentCriteriaService(db)
    success = service.delete_criteria(criteria_id)
    if not success:
        raise HTTPException(status_code=404, detail="Criteria not found")
    return {"message": "Criteria deleted successfully"}


@router.post("/criteria/{criteria_id}/evaluate", response_model=CriteriaMatch)
async def evaluate_property(
    criteria_id: uuid.UUID,
    property_data: PropertyCreate,
    db: Session = Depends(get_db)
):
    """Evaluate a single property against investment criteria"""
    service = InvestmentCriteriaService(db)
    criteria = service.get_criteria(criteria_id)
    if not criteria:
        raise HTTPException(status_code=404, detail="Criteria not found")
    
    try:
        return service.evaluate_property(property_data, criteria)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/criteria/{criteria_id}/evaluate-batch", response_model=List[CriteriaMatch])
async def evaluate_properties_batch(
    criteria_id: uuid.UUID,
    properties: List[PropertyCreate],
    db: Session = Depends(get_db)
):
    """Evaluate multiple properties against investment criteria"""
    service = InvestmentCriteriaService(db)
    criteria = service.get_criteria(criteria_id)
    if not criteria:
        raise HTTPException(status_code=404, detail="Criteria not found")
    
    try:
        return service.batch_evaluate_properties(properties, criteria)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/criteria/{criteria_id}/evaluate-summary", response_model=CriteriaMatchSummary)
async def evaluate_properties_summary(
    criteria_id: uuid.UUID,
    properties: List[PropertyCreate],
    db: Session = Depends(get_db)
):
    """Evaluate multiple properties and return summary"""
    service = InvestmentCriteriaService(db)
    criteria = service.get_criteria(criteria_id)
    if not criteria:
        raise HTTPException(status_code=404, detail="Criteria not found")
    
    try:
        matches = service.batch_evaluate_properties(properties, criteria)
        return service.get_matching_summary(matches)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Template endpoints
@router.post("/templates", response_model=CriteriaTemplate)
async def create_template(
    template: CriteriaTemplate,
    db: Session = Depends(get_db)
):
    """Create new criteria template"""
    service = CriteriaTemplateService(db)
    try:
        return service.create_template(template)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates", response_model=List[CriteriaTemplate])
async def list_templates(
    strategy: Optional[StrategyTypeEnum] = Query(None, description="Filter by strategy"),
    public_only: bool = Query(False, description="Only return public templates"),
    db: Session = Depends(get_db)
):
    """List available criteria templates"""
    service = CriteriaTemplateService(db)
    return service.list_templates(strategy=strategy, public_only=public_only)


@router.get("/templates/defaults", response_model=Dict[str, CriteriaTemplate])
async def get_default_templates(db: Session = Depends(get_db)):
    """Get default templates for common strategies"""
    service = CriteriaTemplateService(db)
    return service.get_default_templates()


@router.get("/templates/{template_id}", response_model=CriteriaTemplate)
async def get_template(
    template_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get criteria template by ID"""
    service = CriteriaTemplateService(db)
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("/templates/{template_id}/use", response_model=InvestmentCriteria)
async def use_template(
    template_id: uuid.UUID,
    customizations: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """Create criteria from template with optional customizations"""
    template_service = CriteriaTemplateService(db)
    criteria_service = InvestmentCriteriaService(db)
    
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Create criteria from template
    criteria = template.criteria.copy()
    criteria.id = uuid.uuid4()
    criteria.name = f"{template.name} - {criteria.id}"
    
    # Apply customizations if provided
    if customizations:
        for key, value in customizations.items():
            if hasattr(criteria, key):
                setattr(criteria, key, value)
    
    try:
        return criteria_service.create_criteria(criteria)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Utility endpoints
@router.get("/strategies", response_model=List[str])
async def get_available_strategies():
    """Get list of available investment strategies"""
    return [strategy.value for strategy in StrategyTypeEnum]


@router.post("/validate-criteria", response_model=Dict[str, Any])
async def validate_criteria(criteria: InvestmentCriteria):
    """Validate investment criteria without saving"""
    try:
        # Basic validation is handled by Pydantic
        # Additional business logic validation could go here
        return {
            "valid": True,
            "message": "Criteria is valid",
            "warnings": []
        }
    except Exception as e:
        return {
            "valid": False,
            "message": str(e),
            "warnings": []
        }