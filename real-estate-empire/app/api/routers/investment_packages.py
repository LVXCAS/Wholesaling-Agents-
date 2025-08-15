"""
API router for investment package generation and management.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.models.investment_package import (
    InvestmentPackageTemplate, InvestmentPackage, PackageDistribution,
    PackageGenerationRequest, PackageAnalytics, MarketingMaterial,
    PackageCustomization, PackagePerformanceReport, PackageTypeEnum,
    PackageStatusEnum, DeliveryMethodEnum, PackageFormatEnum
)
from app.services.investment_package_service import InvestmentPackageService

router = APIRouter(prefix="/api/investment-packages", tags=["investment-packages"])


# Request/Response Models

class CreateTemplateRequest(BaseModel):
    name: str
    package_type: PackageTypeEnum
    description: Optional[str] = None
    format: PackageFormatEnum = PackageFormatEnum.PDF
    sections: List[str] = []
    required_data_fields: List[str] = []
    include_financial_projections: bool = True
    include_market_analysis: bool = True
    include_risk_assessment: bool = True
    include_photos: bool = True


class GeneratePackageRequest(BaseModel):
    template_id: UUID
    deal_id: UUID
    package_name: str
    custom_title: Optional[str] = None
    custom_subtitle: Optional[str] = None
    custom_executive_summary: Optional[str] = None
    additional_highlights: List[str] = []
    custom_content: Dict[str, Any] = {}
    format: Optional[PackageFormatEnum] = None
    auto_distribute: bool = False
    distribution_list: List[UUID] = []
    delivery_method: Optional[DeliveryMethodEnum] = None
    priority: str = "normal"
    notes: Optional[str] = None


class DistributePackageRequest(BaseModel):
    investor_ids: List[UUID]
    delivery_method: DeliveryMethodEnum
    custom_message: Optional[str] = None
    subject_line: Optional[str] = None


class TrackEngagementRequest(BaseModel):
    engagement_type: str  # opened, downloaded, viewed, responded
    metadata: Optional[Dict[str, Any]] = None


class UpdateCustomizationRequest(BaseModel):
    preferred_formats: List[PackageFormatEnum] = []
    preferred_delivery_methods: List[DeliveryMethodEnum] = []
    preferred_sections: List[str] = []
    excluded_sections: List[str] = []
    detail_level: str = "standard"
    include_photos: bool = True
    include_charts: bool = True


# Dependency to get service instance
def get_package_service() -> InvestmentPackageService:
    # In a real implementation, this would inject the database session
    return InvestmentPackageService(db=None)


# Template Management Endpoints

@router.post("/templates", response_model=InvestmentPackageTemplate)
async def create_template(
    request: CreateTemplateRequest,
    service: InvestmentPackageService = Depends(get_package_service)
):
    """Create a new package template"""
    try:
        template_data = request.dict()
        template = service.create_template(template_data)
        return template
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating template: {str(e)}"
        )


@router.get("/templates", response_model=List[InvestmentPackageTemplate])
async def get_templates(
    active_only: bool = Query(True),
    package_type: Optional[PackageTypeEnum] = None,
    service: InvestmentPackageService = Depends(get_package_service)
):
    """Get all package templates"""
    try:
        if package_type:
            templates = service.get_templates_by_type(package_type)
        else:
            templates = service.get_all_templates(active_only=active_only)
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving templates: {str(e)}"
        )


@router.get("/templates/{template_id}", response_model=InvestmentPackageTemplate)
async def get_template(
    template_id: UUID,
    service: InvestmentPackageService = Depends(get_package_service)
):
    """Get a specific template"""
    try:
        template = service.get_template(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving template: {str(e)}"
        )


# Package Generation Endpoints

@router.post("/generate", response_model=InvestmentPackage)
async def generate_package(
    request: GeneratePackageRequest,
    background_tasks: BackgroundTasks,
    service: InvestmentPackageService = Depends(get_package_service)
):
    """Generate an investment package"""
    try:
        # Convert to PackageGenerationRequest
        generation_request = PackageGenerationRequest(**request.dict())
        
        # Generate package asynchronously
        package = await service.generate_package(generation_request)
        
        return package
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error generating package: {str(e)}"
        )


@router.get("/packages/{package_id}", response_model=InvestmentPackage)
async def get_package(
    package_id: UUID,
    service: InvestmentPackageService = Depends(get_package_service)
):
    """Get a specific package"""
    try:
        package = service.get_package(package_id)
        if not package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package not found"
            )
        return package
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving package: {str(e)}"
        )


@router.get("/deals/{deal_id}/packages", response_model=List[InvestmentPackage])
async def get_packages_by_deal(
    deal_id: UUID,
    service: InvestmentPackageService = Depends(get_package_service)
):
    """Get all packages for a deal"""
    try:
        packages = service.get_packages_by_deal(deal_id)
        return packages
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving packages: {str(e)}"
        )


@router.put("/packages/{package_id}/status")
async def update_package_status(
    package_id: UUID,
    status: PackageStatusEnum,
    service: InvestmentPackageService = Depends(get_package_service)
):
    """Update package status"""
    try:
        success = service.update_package_status(package_id, status)
        return {"success": success, "message": "Package status updated"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating package status: {str(e)}"
        )


# Distribution Endpoints

@router.post("/packages/{package_id}/distribute", response_model=List[PackageDistribution])
async def distribute_package(
    package_id: UUID,
    request: DistributePackageRequest,
    service: InvestmentPackageService = Depends(get_package_service)
):
    """Distribute a package to investors"""
    try:
        distributions = await service.distribute_package(
            package_id=package_id,
            investor_ids=request.investor_ids,
            delivery_method=request.delivery_method,
            custom_message=request.custom_message
        )
        return distributions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error distributing package: {str(e)}"
        )


@router.post("/distributions/{distribution_id}/track")
async def track_engagement(
    distribution_id: UUID,
    request: TrackEngagementRequest,
    service: InvestmentPackageService = Depends(get_package_service)
):
    """Track package engagement"""
    try:
        success = service.track_package_engagement(
            distribution_id=distribution_id,
            engagement_type=request.engagement_type,
            metadata=request.metadata
        )
        return {"success": success, "message": "Engagement tracked"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error tracking engagement: {str(e)}"
        )


# Analytics Endpoints

@router.get("/packages/{package_id}/analytics", response_model=PackageAnalytics)
async def get_package_analytics(
    package_id: UUID,
    service: InvestmentPackageService = Depends(get_package_service)
):
    """Get analytics for a specific package"""
    try:
        analytics = service.get_package_analytics(package_id)
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving analytics: {str(e)}"
        )


@router.get("/analytics/performance", response_model=PackagePerformanceReport)
async def get_performance_report(
    start_date: datetime,
    end_date: datetime,
    service: InvestmentPackageService = Depends(get_package_service)
):
    """Get performance report for a date range"""
    try:
        report = service.generate_performance_report(start_date, end_date)
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating performance report: {str(e)}"
        )


# Marketing Material Endpoints

@router.post("/packages/{package_id}/marketing-materials", response_model=List[MarketingMaterial])
async def generate_marketing_materials(
    package_id: UUID,
    material_types: List[str],
    service: InvestmentPackageService = Depends(get_package_service)
):
    """Generate marketing materials from a package"""
    try:
        materials = service.generate_marketing_materials(package_id, material_types)
        return materials
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error generating marketing materials: {str(e)}"
        )


# Customization Endpoints

@router.get("/investors/{investor_id}/customization", response_model=PackageCustomization)
async def get_investor_customization(
    investor_id: UUID,
    service: InvestmentPackageService = Depends(get_package_service)
):
    """Get package customization preferences for an investor"""
    try:
        customization = service.get_investor_customization(investor_id)
        if not customization:
            # Return default customization
            customization = PackageCustomization(investor_id=investor_id)
        return customization
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving customization: {str(e)}"
        )


@router.put("/investors/{investor_id}/customization")
async def update_investor_customization(
    investor_id: UUID,
    request: UpdateCustomizationRequest,
    service: InvestmentPackageService = Depends(get_package_service)
):
    """Update package customization preferences for an investor"""
    try:
        customization_data = request.dict()
        customization_data['investor_id'] = investor_id
        customization = PackageCustomization(**customization_data)
        
        success = service.update_investor_customization(investor_id, customization)
        return {"success": success, "message": "Customization updated"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating customization: {str(e)}"
        )


# Utility Endpoints

@router.get("/package-types")
async def get_package_types():
    """Get available package types"""
    return {
        "package_types": [
            {
                "value": pt.value,
                "label": pt.value.replace("_", " ").title(),
                "description": _get_package_type_description(pt)
            }
            for pt in PackageTypeEnum
        ]
    }


@router.get("/formats")
async def get_package_formats():
    """Get available package formats"""
    return {
        "formats": [
            {
                "value": pf.value,
                "label": pf.value.upper(),
                "description": _get_format_description(pf)
            }
            for pf in PackageFormatEnum
        ]
    }


@router.get("/delivery-methods")
async def get_delivery_methods():
    """Get available delivery methods"""
    return {
        "delivery_methods": [
            {
                "value": dm.value,
                "label": dm.value.replace("_", " ").title(),
                "description": _get_delivery_method_description(dm)
            }
            for dm in DeliveryMethodEnum
        ]
    }


def _get_package_type_description(package_type: PackageTypeEnum) -> str:
    """Get description for package type"""
    descriptions = {
        PackageTypeEnum.EXECUTIVE_SUMMARY: "Concise overview of investment opportunity",
        PackageTypeEnum.DETAILED_ANALYSIS: "Comprehensive analysis with full financial projections",
        PackageTypeEnum.INVESTOR_PRESENTATION: "PowerPoint presentation for investor meetings",
        PackageTypeEnum.MARKETING_FLYER: "Single-page marketing flyer",
        PackageTypeEnum.FINANCIAL_PROJECTIONS: "Detailed financial analysis and projections",
        PackageTypeEnum.COMPARATIVE_ANALYSIS: "Comparison with similar investment opportunities",
        PackageTypeEnum.RISK_ASSESSMENT: "Detailed risk analysis and mitigation strategies",
        PackageTypeEnum.CUSTOM: "Custom package with user-defined content"
    }
    return descriptions.get(package_type, "")


def _get_format_description(format_type: PackageFormatEnum) -> str:
    """Get description for format type"""
    descriptions = {
        PackageFormatEnum.PDF: "Portable Document Format - ideal for sharing and printing",
        PackageFormatEnum.POWERPOINT: "Microsoft PowerPoint presentation",
        PackageFormatEnum.WORD: "Microsoft Word document",
        PackageFormatEnum.HTML: "Web-based interactive format",
        PackageFormatEnum.VIDEO: "Video presentation",
        PackageFormatEnum.INTERACTIVE: "Interactive web-based package"
    }
    return descriptions.get(format_type, "")


def _get_delivery_method_description(delivery_method: DeliveryMethodEnum) -> str:
    """Get description for delivery method"""
    descriptions = {
        DeliveryMethodEnum.EMAIL: "Send via email attachment or link",
        DeliveryMethodEnum.DOWNLOAD_LINK: "Provide secure download link",
        DeliveryMethodEnum.PHYSICAL_MAIL: "Print and mail physical copy",
        DeliveryMethodEnum.SECURE_PORTAL: "Upload to secure investor portal",
        DeliveryMethodEnum.PRESENTATION: "Present in person or via video call"
    }
    return descriptions.get(delivery_method, "")


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "investment-packages"}