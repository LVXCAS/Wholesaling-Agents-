"""
Data Export API endpoints
Implements endpoints for PDF report generation, CSV export, and JSON data export
"""

from fastapi import APIRouter, HTTPException, Depends, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import logging
import io
import csv
import json
from datetime import datetime

from ...core.database import get_db
from ...models.property import PropertyDB, PropertyAnalysisDB

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/{property_id}/pdf", response_class=StreamingResponse)
async def export_property_pdf_report(
    property_id: uuid.UUID,
    include_analysis: bool = True,
    include_comparables: bool = True,
    include_strategies: bool = True,
    db: Session = Depends(get_db)
):
    """
    Generate and export a comprehensive PDF report for a property
    
    - **property_id**: UUID of the property to export
    - **include_analysis**: Include financial analysis in the report
    - **include_comparables**: Include comparable properties in the report
    - **include_strategies**: Include investment strategies in the report
    - Returns PDF file as streaming response
    """
    try:
        # Get property from database
        property_record = db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
        
        if not property_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Get property analyses if requested
        analyses = []
        if include_analysis:
            analyses = db.query(PropertyAnalysisDB).filter(
                PropertyAnalysisDB.property_id == property_id
            ).order_by(PropertyAnalysisDB.created_at.desc()).limit(5).all()
        
        # Generate PDF report
        pdf_buffer = await _generate_pdf_report(
            property_record, 
            analyses, 
            include_comparables, 
            include_strategies
        )
        
        # Create filename
        filename = f"property_report_{property_record.address.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        logger.info(f"Generated PDF report for property: {property_id}")
        
        return StreamingResponse(
            io.BytesIO(pdf_buffer),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF report for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF report: {str(e)}"
        )

@router.get("/{property_id}/csv", response_class=StreamingResponse)
async def export_property_csv_data(
    property_id: uuid.UUID,
    include_analysis: bool = True,
    include_comparables: bool = False,
    db: Session = Depends(get_db)
):
    """
    Export property data and analysis as CSV file
    
    - **property_id**: UUID of the property to export
    - **include_analysis**: Include analysis data in CSV
    - **include_comparables**: Include comparable properties data
    - Returns CSV file as streaming response
    """
    try:
        # Get property from database
        property_record = db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
        
        if not property_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Get property analyses if requested
        analyses = []
        if include_analysis:
            analyses = db.query(PropertyAnalysisDB).filter(
                PropertyAnalysisDB.property_id == property_id
            ).order_by(PropertyAnalysisDB.created_at.desc()).all()
        
        # Generate CSV data
        csv_buffer = await _generate_csv_data(property_record, analyses, include_comparables)
        
        # Create filename
        filename = f"property_data_{property_record.address.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
        
        logger.info(f"Generated CSV export for property: {property_id}")
        
        return StreamingResponse(
            io.StringIO(csv_buffer),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating CSV export for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate CSV export: {str(e)}"
        )

@router.get("/{property_id}/json", response_model=Dict[str, Any])
async def export_property_json_data(
    property_id: uuid.UUID,
    include_analysis: bool = True,
    include_comparables: bool = True,
    include_raw_data: bool = False,
    db: Session = Depends(get_db)
):
    """
    Export property data and analysis as JSON
    
    - **property_id**: UUID of the property to export
    - **include_analysis**: Include analysis data in JSON
    - **include_comparables**: Include comparable properties data
    - **include_raw_data**: Include raw analysis data (detailed JSON fields)
    - Returns comprehensive JSON data structure
    """
    try:
        # Get property from database
        property_record = db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
        
        if not property_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Build property data
        property_data = {
            "id": str(property_record.id),
            "created_at": property_record.created_at.isoformat(),
            "updated_at": property_record.updated_at.isoformat(),
            "basic_info": {
                "address": property_record.address,
                "city": property_record.city,
                "state": property_record.state,
                "zip_code": property_record.zip_code,
                "county": property_record.county,
                "property_type": property_record.property_type,
                "status": property_record.status
            },
            "characteristics": {
                "bedrooms": property_record.bedrooms,
                "bathrooms": property_record.bathrooms,
                "square_feet": property_record.square_feet,
                "lot_size": property_record.lot_size,
                "year_built": property_record.year_built,
                "stories": property_record.stories,
                "garage_spaces": property_record.garage_spaces
            },
            "location": {
                "latitude": property_record.latitude,
                "longitude": property_record.longitude,
                "neighborhood": property_record.neighborhood,
                "school_district": property_record.school_district,
                "walk_score": property_record.walk_score,
                "crime_score": property_record.crime_score
            },
            "financial": {
                "current_value": property_record.current_value,
                "assessed_value": property_record.assessed_value,
                "tax_amount": property_record.tax_amount,
                "listing_price": property_record.listing_price,
                "last_sale_price": property_record.last_sale_price,
                "last_sale_date": property_record.last_sale_date.isoformat() if property_record.last_sale_date else None
            },
            "condition": {
                "condition_score": property_record.condition_score,
                "renovation_needed": property_record.renovation_needed,
                "days_on_market": property_record.days_on_market
            },
            "features": property_record.features or {},
            "photos": property_record.photos or [],
            "description": property_record.description,
            "virtual_tour_url": property_record.virtual_tour_url,
            "data_source": {
                "source": property_record.data_source,
                "external_id": property_record.external_id,
                "data_quality_score": property_record.data_quality_score
            }
        }
        
        # Add analysis data if requested
        if include_analysis:
            analyses = db.query(PropertyAnalysisDB).filter(
                PropertyAnalysisDB.property_id == property_id
            ).order_by(PropertyAnalysisDB.created_at.desc()).all()
            
            property_data["analyses"] = []
            
            for analysis in analyses:
                analysis_data = {
                    "id": str(analysis.id),
                    "created_at": analysis.created_at.isoformat(),
                    "updated_at": analysis.updated_at.isoformat(),
                    "analysis_type": analysis.analysis_type,
                    "valuation": {
                        "arv_estimate": analysis.arv_estimate,
                        "current_value_estimate": analysis.current_value_estimate,
                        "confidence_score": analysis.confidence_score,
                        "comparable_count": analysis.comparable_count
                    },
                    "financial_metrics": {
                        "repair_estimate": analysis.repair_estimate,
                        "potential_profit": analysis.potential_profit,
                        "roi_estimate": analysis.roi_estimate,
                        "cash_flow_estimate": analysis.cash_flow_estimate,
                        "cap_rate": analysis.cap_rate
                    }
                }
                
                # Include raw data if requested
                if include_raw_data and analysis.analysis_data:
                    analysis_data["raw_analysis_data"] = analysis.analysis_data
                
                # Include comparables if requested
                if include_comparables and analysis.comparable_properties:
                    analysis_data["comparable_properties"] = analysis.comparable_properties
                
                property_data["analyses"].append(analysis_data)
        
        # Add export metadata
        export_data = {
            "export_info": {
                "exported_at": datetime.utcnow().isoformat(),
                "export_type": "json",
                "includes_analysis": include_analysis,
                "includes_comparables": include_comparables,
                "includes_raw_data": include_raw_data,
                "total_analyses": len(property_data.get("analyses", []))
            },
            "property": property_data
        }
        
        logger.info(f"Generated JSON export for property: {property_id}")
        
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating JSON export for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate JSON export: {str(e)}"
        )

@router.get("/bulk/csv", response_class=StreamingResponse)
async def export_bulk_properties_csv(
    property_ids: List[uuid.UUID],
    include_analysis: bool = True,
    db: Session = Depends(get_db)
):
    """
    Export multiple properties data as CSV file
    
    - **property_ids**: List of property UUIDs to export
    - **include_analysis**: Include analysis data in CSV
    - Returns CSV file with multiple properties data
    """
    try:
        if len(property_ids) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 100 properties allowed for bulk export"
            )
        
        # Get properties from database
        properties = db.query(PropertyDB).filter(PropertyDB.id.in_(property_ids)).all()
        
        if not properties:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No properties found"
            )
        
        # Generate bulk CSV data
        csv_buffer = await _generate_bulk_csv_data(properties, include_analysis, db)
        
        # Create filename
        filename = f"bulk_properties_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        logger.info(f"Generated bulk CSV export for {len(properties)} properties")
        
        return StreamingResponse(
            io.StringIO(csv_buffer),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating bulk CSV export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate bulk CSV export: {str(e)}"
        )

@router.get("/bulk/json", response_model=Dict[str, Any])
async def export_bulk_properties_json(
    property_ids: List[uuid.UUID],
    include_analysis: bool = True,
    include_comparables: bool = False,
    db: Session = Depends(get_db)
):
    """
    Export multiple properties data as JSON
    
    - **property_ids**: List of property UUIDs to export
    - **include_analysis**: Include analysis data
    - **include_comparables**: Include comparable properties data
    - Returns JSON with multiple properties data
    """
    try:
        if len(property_ids) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 properties allowed for bulk JSON export"
            )
        
        # Get properties from database
        properties = db.query(PropertyDB).filter(PropertyDB.id.in_(property_ids)).all()
        
        if not properties:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No properties found"
            )
        
        # Build bulk export data
        export_data = {
            "export_info": {
                "exported_at": datetime.utcnow().isoformat(),
                "export_type": "bulk_json",
                "total_properties": len(properties),
                "includes_analysis": include_analysis,
                "includes_comparables": include_comparables
            },
            "properties": []
        }
        
        # Process each property
        for property_record in properties:
            # Get individual property JSON data
            property_json = await export_property_json_data(
                property_record.id,
                include_analysis=include_analysis,
                include_comparables=include_comparables,
                include_raw_data=False,
                db=db
            )
            
            export_data["properties"].append(property_json["property"])
        
        logger.info(f"Generated bulk JSON export for {len(properties)} properties")
        
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating bulk JSON export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate bulk JSON export: {str(e)}"
        )

# Helper functions for generating exports

async def _generate_pdf_report(
    property_record: PropertyDB,
    analyses: List[PropertyAnalysisDB],
    include_comparables: bool,
    include_strategies: bool
) -> bytes:
    """Generate PDF report for property"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph("Property Investment Analysis Report", title_style))
        story.append(Spacer(1, 20))
        
        # Property Information
        story.append(Paragraph("Property Information", styles['Heading2']))
        
        property_data = [
            ["Address", f"{property_record.address}, {property_record.city}, {property_record.state} {property_record.zip_code}"],
            ["Property Type", property_record.property_type.replace('_', ' ').title()],
            ["Bedrooms", str(property_record.bedrooms) if property_record.bedrooms else "N/A"],
            ["Bathrooms", str(property_record.bathrooms) if property_record.bathrooms else "N/A"],
            ["Square Feet", f"{property_record.square_feet:,}" if property_record.square_feet else "N/A"],
            ["Year Built", str(property_record.year_built) if property_record.year_built else "N/A"],
            ["Listing Price", f"${property_record.listing_price:,.0f}" if property_record.listing_price else "N/A"],
            ["Current Value", f"${property_record.current_value:,.0f}" if property_record.current_value else "N/A"]
        ]
        
        property_table = Table(property_data, colWidths=[2*inch, 4*inch])
        property_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(property_table)
        story.append(Spacer(1, 20))
        
        # Analysis Results
        if analyses:
            story.append(Paragraph("Financial Analysis", styles['Heading2']))
            
            for analysis in analyses[:3]:  # Limit to 3 most recent analyses
                story.append(Paragraph(f"Analysis: {analysis.analysis_type.title()} ({analysis.created_at.strftime('%Y-%m-%d')})", styles['Heading3']))
                
                analysis_data = [
                    ["ARV Estimate", f"${analysis.arv_estimate:,.0f}" if analysis.arv_estimate else "N/A"],
                    ["Current Value Estimate", f"${analysis.current_value_estimate:,.0f}" if analysis.current_value_estimate else "N/A"],
                    ["Repair Estimate", f"${analysis.repair_estimate:,.0f}" if analysis.repair_estimate else "N/A"],
                    ["Potential Profit", f"${analysis.potential_profit:,.0f}" if analysis.potential_profit else "N/A"],
                    ["ROI Estimate", f"{analysis.roi_estimate:.1f}%" if analysis.roi_estimate else "N/A"],
                    ["Cash Flow Estimate", f"${analysis.cash_flow_estimate:,.0f}" if analysis.cash_flow_estimate else "N/A"],
                    ["Cap Rate", f"{analysis.cap_rate:.1f}%" if analysis.cap_rate else "N/A"],
                    ["Confidence Score", f"{analysis.confidence_score:.1%}" if analysis.confidence_score else "N/A"]
                ]
                
                analysis_table = Table(analysis_data, colWidths=[2*inch, 2*inch])
                analysis_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(analysis_table)
                story.append(Spacer(1, 15))
        
        # Footer
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            alignment=1
        )
        story.append(Paragraph(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by Real Estate Empire", footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.read()
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        # Return a simple text-based PDF if reportlab fails
        return b"PDF generation failed. Please install reportlab library."

async def _generate_csv_data(
    property_record: PropertyDB,
    analyses: List[PropertyAnalysisDB],
    include_comparables: bool
) -> str:
    """Generate CSV data for property"""
    output = io.StringIO()
    
    # Property data headers
    headers = [
        'property_id', 'address', 'city', 'state', 'zip_code', 'property_type',
        'bedrooms', 'bathrooms', 'square_feet', 'lot_size', 'year_built',
        'listing_price', 'current_value', 'assessed_value', 'tax_amount',
        'condition_score', 'days_on_market', 'created_at', 'updated_at'
    ]
    
    # Add analysis headers if analyses exist
    if analyses:
        headers.extend([
            'latest_analysis_type', 'arv_estimate', 'current_value_estimate',
            'repair_estimate', 'potential_profit', 'roi_estimate',
            'cash_flow_estimate', 'cap_rate', 'confidence_score', 'analysis_date'
        ])
    
    writer = csv.writer(output)
    writer.writerow(headers)
    
    # Property data row
    row = [
        str(property_record.id),
        property_record.address,
        property_record.city,
        property_record.state,
        property_record.zip_code,
        property_record.property_type,
        property_record.bedrooms,
        property_record.bathrooms,
        property_record.square_feet,
        property_record.lot_size,
        property_record.year_built,
        property_record.listing_price,
        property_record.current_value,
        property_record.assessed_value,
        property_record.tax_amount,
        property_record.condition_score,
        property_record.days_on_market,
        property_record.created_at.isoformat(),
        property_record.updated_at.isoformat()
    ]
    
    # Add latest analysis data if available
    if analyses:
        latest_analysis = analyses[0]
        row.extend([
            latest_analysis.analysis_type,
            latest_analysis.arv_estimate,
            latest_analysis.current_value_estimate,
            latest_analysis.repair_estimate,
            latest_analysis.potential_profit,
            latest_analysis.roi_estimate,
            latest_analysis.cash_flow_estimate,
            latest_analysis.cap_rate,
            latest_analysis.confidence_score,
            latest_analysis.created_at.isoformat()
        ])
    
    writer.writerow(row)
    
    return output.getvalue()

async def _generate_bulk_csv_data(
    properties: List[PropertyDB],
    include_analysis: bool,
    db: Session
) -> str:
    """Generate bulk CSV data for multiple properties"""
    output = io.StringIO()
    
    # Headers
    headers = [
        'property_id', 'address', 'city', 'state', 'zip_code', 'property_type',
        'bedrooms', 'bathrooms', 'square_feet', 'lot_size', 'year_built',
        'listing_price', 'current_value', 'assessed_value', 'tax_amount',
        'condition_score', 'days_on_market', 'created_at', 'updated_at'
    ]
    
    if include_analysis:
        headers.extend([
            'latest_analysis_type', 'arv_estimate', 'current_value_estimate',
            'repair_estimate', 'potential_profit', 'roi_estimate',
            'cash_flow_estimate', 'cap_rate', 'confidence_score', 'analysis_date'
        ])
    
    writer = csv.writer(output)
    writer.writerow(headers)
    
    # Process each property
    for property_record in properties:
        row = [
            str(property_record.id),
            property_record.address,
            property_record.city,
            property_record.state,
            property_record.zip_code,
            property_record.property_type,
            property_record.bedrooms,
            property_record.bathrooms,
            property_record.square_feet,
            property_record.lot_size,
            property_record.year_built,
            property_record.listing_price,
            property_record.current_value,
            property_record.assessed_value,
            property_record.tax_amount,
            property_record.condition_score,
            property_record.days_on_market,
            property_record.created_at.isoformat(),
            property_record.updated_at.isoformat()
        ]
        
        # Add analysis data if requested
        if include_analysis:
            latest_analysis = db.query(PropertyAnalysisDB).filter(
                PropertyAnalysisDB.property_id == property_record.id
            ).order_by(PropertyAnalysisDB.created_at.desc()).first()
            
            if latest_analysis:
                row.extend([
                    latest_analysis.analysis_type,
                    latest_analysis.arv_estimate,
                    latest_analysis.current_value_estimate,
                    latest_analysis.repair_estimate,
                    latest_analysis.potential_profit,
                    latest_analysis.roi_estimate,
                    latest_analysis.cash_flow_estimate,
                    latest_analysis.cap_rate,
                    latest_analysis.confidence_score,
                    latest_analysis.created_at.isoformat()
                ])
            else:
                # Add empty analysis columns
                row.extend([None] * 10)
        
        writer.writerow(row)
    
    return output.getvalue()