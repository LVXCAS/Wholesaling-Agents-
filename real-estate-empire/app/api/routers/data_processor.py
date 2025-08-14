"""
Data Processor API Router - Handles zip file uploads and processing
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from typing import Optional, Dict, Any
import tempfile
import os
import json
import logging

from ...services.data_processor_service import DataProcessorService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data-processor", tags=["data-processor"])

# Initialize service
data_processor = DataProcessorService()

@router.post("/upload-zip")
async def upload_and_process_zip(
    file: UploadFile = File(...),
    target_schema: Optional[str] = Form(None)
):
    """
    Upload a zip file and process its contents with AI reformatting
    """
    try:
        # Validate file type
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="Only ZIP files are supported")
        
        # Save uploaded file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        # Parse target schema if provided
        schema_dict = None
        if target_schema:
            try:
                schema_dict = json.loads(target_schema)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON in target_schema")
        
        # Process the zip file
        result = data_processor.process_zip_file(temp_file.name, schema_dict)
        
        # Cleanup temp file
        os.unlink(temp_file.name)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Processing failed'))
        
        return {
            "message": "File processed successfully",
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-with-schema")
async def process_with_custom_schema(
    file: UploadFile = File(...),
    schema: Dict[str, Any] = None
):
    """
    Process zip file with a custom ML schema
    """
    try:
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="Only ZIP files are supported")
        
        # Save uploaded file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        # Process with schema
        result = data_processor.process_zip_file(temp_file.name, schema)
        
        # Cleanup
        os.unlink(temp_file.name)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Processing failed'))
        
        return result
        
    except Exception as e:
        logger.error(f"Error in schema processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auto-format")
async def auto_format_data(file: UploadFile = File(...)):
    """
    Automatically determine the best ML format for the data
    """
    try:
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="Only ZIP files are supported")
        
        # Save uploaded file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        # Auto-format processing
        result = data_processor.process_zip_file(temp_file.name, None)
        
        # Cleanup
        os.unlink(temp_file.name)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Processing failed'))
        
        return {
            "message": "Auto-formatting completed",
            "result": result,
            "gemini_recommendations": result.get('reformatted_data', {}).get('gemini_analysis', {})
        }
        
    except Exception as e:
        logger.error(f"Error in auto-formatting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export/{format}")
async def export_processed_data(
    format: str,
    processed_data: Dict[str, Any]
):
    """
    Export processed data in specified format (csv, json, excel)
    """
    try:
        if format not in ['csv', 'json', 'excel']:
            raise HTTPException(status_code=400, detail="Unsupported export format")
        
        # Export data
        output_file = data_processor.export_processed_data(processed_data, format)
        
        if not output_file or not os.path.exists(output_file):
            raise HTTPException(status_code=500, detail="Export failed")
        
        # Return file
        return FileResponse(
            output_file,
            media_type='application/octet-stream',
            filename=f'processed_data.{format}'
        )
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/supported-formats")
async def get_supported_formats():
    """
    Get list of supported file formats
    """
    return {
        "supported_formats": data_processor.supported_formats,
        "description": "File formats that can be processed from zip archives"
    }

@router.post("/validate-schema")
async def validate_schema(schema: Dict[str, Any]):
    """
    Validate a target schema for ML processing
    """
    try:
        # Basic schema validation
        required_fields = ['fields', 'target_variable']
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required fields
        for field in required_fields:
            if field not in schema:
                validation_result["errors"].append(f"Missing required field: {field}")
                validation_result["valid"] = False
        
        # Validate field definitions
        if 'fields' in schema:
            for field_name, field_def in schema['fields'].items():
                if not isinstance(field_def, dict):
                    validation_result["errors"].append(f"Field '{field_name}' must be a dictionary")
                    validation_result["valid"] = False
                elif 'type' not in field_def:
                    validation_result["warnings"].append(f"Field '{field_name}' missing type definition")
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Error validating schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/processing-status/{job_id}")
async def get_processing_status(job_id: str):
    """
    Get status of a processing job (for future async processing)
    """
    # Placeholder for async job tracking
    return {
        "job_id": job_id,
        "status": "completed",
        "message": "Synchronous processing - job completed immediately"
    }