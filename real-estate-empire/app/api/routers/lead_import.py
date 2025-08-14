"""
Lead import API router for the Real Estate Empire platform.
Provides endpoints for CSV import functionality with column mapping and validation.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.lead_import_service import LeadImportService, ColumnMapping, ImportResult
from app.models.lead import LeadSourceEnum


router = APIRouter(prefix="/api/lead-import", tags=["lead-import"])


class CSVAnalysisRequest(BaseModel):
    """Request model for CSV analysis."""
    csv_content: str


class CSVAnalysisResponse(BaseModel):
    """Response model for CSV analysis."""
    headers: List[str]
    sample_rows: List[List[str]]
    total_rows: int
    suggested_mapping: Dict[str, str]
    analysis_status: str
    error_message: str = None


class ImportRequest(BaseModel):
    """Request model for lead import."""
    csv_content: str
    column_mapping: Dict[str, str]
    default_source: LeadSourceEnum = LeadSourceEnum.OTHER
    skip_duplicates: bool = True


class ImportResponse(BaseModel):
    """Response model for import results."""
    total_rows: int
    successful_imports: int
    failed_imports: int
    duplicates_found: int
    errors: List[Dict[str, Any]]
    status: str
    import_id: str
    created_leads: List[str]
    created_properties: List[str]


@router.post("/analyze", response_model=CSVAnalysisResponse)
async def analyze_csv(
    request: CSVAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze CSV content and suggest column mappings.
    
    Args:
        request: CSV analysis request with content
        db: Database session
        
    Returns:
        Analysis results with suggested mappings
    """
    try:
        import_service = LeadImportService(db)
        result = import_service.analyze_csv(request.csv_content)
        
        return CSVAnalysisResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV analysis failed: {str(e)}")


@router.post("/analyze-file")
async def analyze_csv_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Analyze uploaded CSV file and suggest column mappings.
    
    Args:
        file: Uploaded CSV file
        db: Database session
        
    Returns:
        Analysis results with suggested mappings
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        import_service = LeadImportService(db)
        result = import_service.analyze_csv(csv_content)
        
        return CSVAnalysisResponse(**result)
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding not supported. Please use UTF-8 encoded CSV files.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV analysis failed: {str(e)}")


@router.post("/import", response_model=ImportResponse)
async def import_leads(
    request: ImportRequest,
    db: Session = Depends(get_db)
):
    """
    Import leads from CSV content using provided column mapping.
    
    Args:
        request: Import request with CSV content and mapping
        db: Database session
        
    Returns:
        Import results with success/failure details
    """
    try:
        # Convert mapping dict to ColumnMapping object
        column_mapping = ColumnMapping(**request.column_mapping)
        
        import_service = LeadImportService(db)
        result = import_service.import_leads(
            csv_content=request.csv_content,
            column_mapping=column_mapping,
            default_source=request.default_source,
            skip_duplicates=request.skip_duplicates
        )
        
        # Convert UUIDs to strings for JSON serialization
        return ImportResponse(
            total_rows=result.total_rows,
            successful_imports=result.successful_imports,
            failed_imports=result.failed_imports,
            duplicates_found=result.duplicates_found,
            errors=result.errors,
            status=result.status.value,
            import_id=result.import_id,
            created_leads=[str(lead_id) for lead_id in result.created_leads],
            created_properties=[str(prop_id) for prop_id in result.created_properties]
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lead import failed: {str(e)}")


@router.post("/import-file")
async def import_leads_from_file(
    file: UploadFile = File(...),
    column_mapping: str = Form(...),
    default_source: LeadSourceEnum = Form(LeadSourceEnum.OTHER),
    skip_duplicates: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    Import leads from uploaded CSV file.
    
    Args:
        file: Uploaded CSV file
        column_mapping: JSON string of column mapping
        default_source: Default source for leads
        skip_duplicates: Whether to skip duplicate leads
        db: Database session
        
    Returns:
        Import results with success/failure details
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Parse column mapping JSON
        import json
        try:
            mapping_dict = json.loads(column_mapping)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid column mapping JSON")
        
        # Convert mapping dict to ColumnMapping object
        column_mapping_obj = ColumnMapping(**mapping_dict)
        
        import_service = LeadImportService(db)
        result = import_service.import_leads(
            csv_content=csv_content,
            column_mapping=column_mapping_obj,
            default_source=default_source,
            skip_duplicates=skip_duplicates
        )
        
        # Convert UUIDs to strings for JSON serialization
        return ImportResponse(
            total_rows=result.total_rows,
            successful_imports=result.successful_imports,
            failed_imports=result.failed_imports,
            duplicates_found=result.duplicates_found,
            errors=result.errors,
            status=result.status.value,
            import_id=result.import_id,
            created_leads=[str(lead_id) for lead_id in result.created_leads],
            created_properties=[str(prop_id) for prop_id in result.created_properties]
        )
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding not supported. Please use UTF-8 encoded CSV files.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lead import failed: {str(e)}")


@router.get("/mapping-template")
async def get_mapping_template():
    """
    Get a template for column mapping configuration.
    
    Returns:
        Template showing available mapping fields
    """
    template = {
        "property_fields": {
            "address": "Street address of the property",
            "city": "City where property is located",
            "state": "State/province where property is located",
            "zip_code": "ZIP/postal code",
            "property_type": "Type of property (single_family, multi_family, etc.)",
            "bedrooms": "Number of bedrooms",
            "bathrooms": "Number of bathrooms",
            "square_feet": "Square footage of the property",
            "year_built": "Year the property was built"
        },
        "lead_fields": {
            "owner_name": "Name of the property owner",
            "owner_email": "Email address of the owner",
            "owner_phone": "Phone number of the owner",
            "owner_address": "Mailing address of the owner",
            "source": "Source of the lead",
            "asking_price": "Asking price for the property",
            "mortgage_balance": "Outstanding mortgage balance",
            "equity_estimate": "Estimated equity in the property",
            "preferred_contact_method": "Preferred way to contact owner",
            "condition_notes": "Notes about property condition",
            "notes": "General notes about the lead",
            "tags": "Comma-separated tags for the lead",
            "motivation_factors": "Comma-separated motivation factors"
        },
        "example_mapping": {
            "address": "Property Address",
            "city": "City",
            "state": "State",
            "zip_code": "ZIP Code",
            "owner_name": "Owner Name",
            "owner_phone": "Phone Number",
            "owner_email": "Email",
            "asking_price": "List Price"
        }
    }
    
    return template


@router.get("/sources")
async def get_available_sources():
    """
    Get list of available lead sources.
    
    Returns:
        List of available lead source options
    """
    sources = [
        {"value": source.value, "label": source.value.replace("_", " ").title()}
        for source in LeadSourceEnum
    ]
    
    return {"sources": sources}