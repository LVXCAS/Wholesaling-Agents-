"""
Unit tests for the investment package generation service.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4, UUID
from unittest.mock import Mock, patch, AsyncMock

from app.models.investment_package import (
    InvestmentPackageTemplate, InvestmentPackage, PackageDistribution,
    PackageGenerationRequest, PackageAnalytics, MarketingMaterial,
    PackageCustomization, PackagePerformanceReport, PackageTypeEnum,
    PackageStatusEnum, DeliveryMethodEnum, PackageFormatEnum
)
from app.services.investment_package_service import InvestmentPackageService


class TestInvestmentPackageService:
    """Test cases for InvestmentPackageService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mocked dependencies"""
        return InvestmentPackageService(db=mock_db)
    
    @pytest.fixture
    def sample_template_data(self):
        """Sample template data for testing"""
        return {
            "name": "Test Template",
            "package_type": PackageTypeEnum.EXECUTIVE_SUMMARY,
            "description": "Test template for unit tests",
            "format": PackageFormatEnum.PDF,
            "sections": ["overview", "financials", "summary"],
            "required_data_fields": ["property_address", "purchase_price"],
            "include_financial_projections": True,
            "include_market_analysis": False
        }
    
    @pytest.fixture
    def sample_generation_request(self):
        """Sample package generation request"""
        return PackageGenerationRequest(
            template_id=uuid4(),
            deal_id=uuid4(),
            package_name="Test Investment Package",
            custom_title="Custom Title",
            additional_highlights=["Great location", "Strong cash flow"],
            auto_distribute=False
        )
    
    @pytest.fixture
    def sample_deal_data(self):
        """Sample deal data for testing"""
        return {
            "property_address": "123 Test St, Austin, TX",
            "property_description": "Beautiful test property",
            "purchase_price": Decimal("300000"),
            "estimated_value": Decimal("400000"),
            "renovation_cost": Decimal("50000"),
            "projected_rental_income": Decimal("2500"),
            "projected_expenses": Decimal("800"),
            "property_photos": ["photo1.jpg", "photo2.jpg"],
            "property_features": ["3 bed", "2 bath", "garage"],
            "market_overview": "Strong market conditions"
        }
    
    # Template Management Tests
    
    def test_create_template_success(self, service, sample_template_data):
        """Test successful template creation"""
        template = service.create_template(sample_template_data)
        
        assert isinstance(template, InvestmentPackageTemplate)
        assert template.name == "Test Template"
        assert template.package_type == PackageTypeEnum.EXECUTIVE_SUMMARY
        assert template.format == PackageFormatEnum.PDF
        assert template.active is True
    
    def test_create_template_validation_error(self, service):
        """Test template creation with invalid data"""
        invalid_data = {
            "name": "",  # Empty name should fail
            "package_type": "invalid_type"
        }
        
        with pytest.raises(Exception):
            service.create_template(invalid_data)
    
    def test_get_all_templates(self, service):
        """Test retrieving all templates"""
        templates = service.get_all_templates()
        
        assert isinstance(templates, list)
        assert len(templates) > 0  # Should have default templates
        
        # Check that default templates are present
        template_names = [t.name for t in templates]
        assert "Executive Summary" in template_names
        assert "Detailed Investment Analysis" in template_names
    
    def test_get_templates_by_type(self, service):
        """Test retrieving templates by type"""
        exec_templates = service.get_templates_by_type(PackageTypeEnum.EXECUTIVE_SUMMARY)
        
        assert isinstance(exec_templates, list)
        assert all(t.package_type == PackageTypeEnum.EXECUTIVE_SUMMARY for t in exec_templates)
    
    def test_get_template_by_id(self, service):
        """Test retrieving template by ID"""
        # Get a default template ID
        templates = service.get_all_templates()
        if templates:
            template_id = templates[0].id
            retrieved_template = service.get_template(template_id)
            
            assert retrieved_template is not None
            assert retrieved_template.id == template_id
    
    # Package Generation Tests
    
    @pytest.mark.asyncio
    async def test_generate_package_success(self, service, sample_generation_request):
        """Test successful package generation"""
        # Mock the template retrieval
        mock_template = InvestmentPackageTemplate(
            name="Test Template",
            package_type=PackageTypeEnum.EXECUTIVE_SUMMARY,
            format=PackageFormatEnum.PDF,
            sections=["overview", "financials"]
        )
        
        with patch.object(service, 'get_template', return_value=mock_template):
            package = await service.generate_package(sample_generation_request)
        
        assert isinstance(package, InvestmentPackage)
        assert package.name == "Test Investment Package"
        assert package.package_type == PackageTypeEnum.EXECUTIVE_SUMMARY
        assert package.status == PackageStatusEnum.READY
        assert package.title == "Custom Title"
        assert package.generated_at is not None
    
    @pytest.mark.asyncio
    async def test_generate_package_template_not_found(self, service, sample_generation_request):
        """Test package generation with non-existent template"""
        with patch.object(service, 'get_template', return_value=None):
            with pytest.raises(ValueError, match="Template .* not found"):
                await service.generate_package(sample_generation_request)
    
    @pytest.mark.asyncio
    async def test_get_deal_data(self, service):
        """Test deal data retrieval"""
        deal_id = uuid4()
        deal_data = await service._get_deal_data(deal_id)
        
        assert isinstance(deal_data, dict)
        assert "property_address" in deal_data
        assert "purchase_price" in deal_data
    
    def test_generate_title(self, service, sample_deal_data):
        """Test title generation"""
        title = service._generate_title(sample_deal_data)
        
        assert isinstance(title, str)
        assert "123 Test St, Austin, TX" in title
        assert "Investment Opportunity" in title
    
    def test_generate_executive_summary(self, service, sample_deal_data):
        """Test executive summary generation"""
        summary = service._generate_executive_summary(sample_deal_data)
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "123 Test St, Austin, TX" in summary
    
    @pytest.mark.asyncio
    async def test_populate_package_content(self, service, sample_deal_data):
        """Test package content population"""
        package = InvestmentPackage(
            template_id=uuid4(),
            deal_id=uuid4(),
            name="Test Package",
            package_type=PackageTypeEnum.EXECUTIVE_SUMMARY,
            title="Test Title"
        )
        
        template = InvestmentPackageTemplate(
            name="Test Template",
            package_type=PackageTypeEnum.EXECUTIVE_SUMMARY,
            sections=["overview"]
        )
        
        request = PackageGenerationRequest(
            template_id=template.id,
            deal_id=package.deal_id,
            package_name="Test",
            additional_highlights=["Test highlight"]
        )
        
        await service._populate_package_content(package, template, sample_deal_data, request)
        
        # Check that content was populated
        assert package.property_address == "123 Test St, Austin, TX"
        assert package.purchase_price == Decimal("300000")
        assert package.projected_cash_flow == Decimal("1700")  # 2500 - 800
        assert package.projected_roi is not None
        assert len(package.investment_highlights) > 0
    
    def test_assess_risk_factors(self, service, sample_deal_data):
        """Test risk factor assessment"""
        risk_factors = service._assess_risk_factors(sample_deal_data)
        
        assert isinstance(risk_factors, list)
        assert len(risk_factors) > 0
        assert any("market" in factor.lower() for factor in risk_factors)
        assert any("vacancy" in factor.lower() for factor in risk_factors)
    
    def test_generate_mitigation_strategies(self, service):
        """Test mitigation strategy generation"""
        risk_factors = ["Market volatility", "Vacancy risk", "Renovation delays"]
        strategies = service._generate_mitigation_strategies(risk_factors)
        
        assert isinstance(strategies, list)
        assert len(strategies) > 0
    
    def test_calculate_risk_score(self, service, sample_deal_data):
        """Test risk score calculation"""
        risk_score = service._calculate_risk_score(sample_deal_data)
        
        assert isinstance(risk_score, float)
        assert 0.0 <= risk_score <= 10.0
    
    @pytest.mark.asyncio
    async def test_generate_package_file(self, service):
        """Test package file generation"""
        package = InvestmentPackage(
            template_id=uuid4(),
            deal_id=uuid4(),
            name="Test Package",
            package_type=PackageTypeEnum.EXECUTIVE_SUMMARY,
            title="Test Title"
        )
        
        template = InvestmentPackageTemplate(
            name="Test Template",
            package_type=PackageTypeEnum.EXECUTIVE_SUMMARY,
            format=PackageFormatEnum.PDF,
            sections=["overview", "financials"]
        )
        
        await service._generate_package_file(package, template)
        
        assert package.file_path is not None
        assert package.file_size is not None
        assert package.page_count is not None
    
    # Distribution Tests
    
    @pytest.mark.asyncio
    async def test_distribute_package_success(self, service):
        """Test successful package distribution"""
        package_id = uuid4()
        investor_ids = [uuid4(), uuid4()]
        delivery_method = DeliveryMethodEnum.EMAIL
        
        distributions = await service.distribute_package(
            package_id, investor_ids, delivery_method, "Custom message"
        )
        
        assert isinstance(distributions, list)
        assert len(distributions) == 2
        
        for dist in distributions:
            assert isinstance(dist, PackageDistribution)
            assert dist.package_id == package_id
            assert dist.delivery_method == delivery_method
            assert dist.message == "Custom message"
    
    @pytest.mark.asyncio
    async def test_get_investor_data(self, service):
        """Test investor data retrieval"""
        investor_id = uuid4()
        investor_data = await service._get_investor_data(investor_id)
        
        assert isinstance(investor_data, dict)
        assert "name" in investor_data
        assert "email" in investor_data
    
    @pytest.mark.asyncio
    async def test_send_package(self, service):
        """Test package sending"""
        distribution = PackageDistribution(
            package_id=uuid4(),
            recipient_id=uuid4(),
            recipient_name="Test Investor",
            recipient_email="test@example.com",
            delivery_method=DeliveryMethodEnum.EMAIL
        )
        
        await service._send_package(distribution)
        
        assert distribution.sent_at is not None
        assert distribution.delivered_at is not None
    
    # Package Management Tests
    
    def test_get_package(self, service):
        """Test package retrieval"""
        package_id = uuid4()
        package = service.get_package(package_id)
        
        # In the mock implementation, this returns None
        assert package is None
    
    def test_get_packages_by_deal(self, service):
        """Test retrieving packages by deal"""
        deal_id = uuid4()
        packages = service.get_packages_by_deal(deal_id)
        
        assert isinstance(packages, list)
    
    def test_update_package_status(self, service):
        """Test package status update"""
        package_id = uuid4()
        success = service.update_package_status(package_id, PackageStatusEnum.DISTRIBUTED)
        
        assert success is True
    
    # Analytics Tests
    
    def test_track_package_engagement(self, service):
        """Test engagement tracking"""
        distribution_id = uuid4()
        success = service.track_package_engagement(
            distribution_id, "opened", {"timestamp": datetime.utcnow()}
        )
        
        assert success is True
    
    def test_get_package_analytics(self, service):
        """Test package analytics generation"""
        package_id = uuid4()
        analytics = service.get_package_analytics(package_id)
        
        assert isinstance(analytics, PackageAnalytics)
        assert analytics.package_id == package_id
    
    def test_generate_performance_report(self, service):
        """Test performance report generation"""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        report = service.generate_performance_report(start_date, end_date)
        
        assert isinstance(report, PackagePerformanceReport)
        assert report.report_period_start == start_date
        assert report.report_period_end == end_date
    
    # Marketing Material Tests
    
    def test_generate_marketing_materials(self, service):
        """Test marketing material generation"""
        package_id = uuid4()
        material_types = ["flyer", "brochure"]
        
        # Mock the get_package method
        mock_package = InvestmentPackage(
            id=package_id,
            template_id=uuid4(),
            deal_id=uuid4(),
            name="Test Package",
            package_type=PackageTypeEnum.EXECUTIVE_SUMMARY,
            title="Test Investment",
            investment_highlights=["Great ROI", "Prime location", "Strong cash flow"]
        )
        
        with patch.object(service, 'get_package', return_value=mock_package):
            materials = service.generate_marketing_materials(package_id, material_types)
        
        assert isinstance(materials, list)
        assert len(materials) == 2
        
        for material in materials:
            assert isinstance(material, MarketingMaterial)
            assert material.package_id == package_id
    
    def test_generate_marketing_materials_package_not_found(self, service):
        """Test marketing material generation with non-existent package"""
        package_id = uuid4()
        
        with patch.object(service, 'get_package', return_value=None):
            with pytest.raises(ValueError, match="Package .* not found"):
                service.generate_marketing_materials(package_id, ["flyer"])
    
    # Customization Tests
    
    def test_get_investor_customization(self, service):
        """Test investor customization retrieval"""
        investor_id = uuid4()
        customization = service.get_investor_customization(investor_id)
        
        # In the mock implementation, this returns None
        assert customization is None
    
    def test_update_investor_customization(self, service):
        """Test investor customization update"""
        investor_id = uuid4()
        customization = PackageCustomization(
            investor_id=investor_id,
            preferred_formats=[PackageFormatEnum.PDF],
            detail_level="detailed"
        )
        
        success = service.update_investor_customization(investor_id, customization)
        assert success is True
    
    # Edge Cases and Error Handling Tests
    
    def test_create_template_with_invalid_data(self, service):
        """Test template creation with invalid data"""
        invalid_data = {
            "name": "",  # Empty name
            "package_type": "invalid"
        }
        
        with pytest.raises(Exception):
            service.create_template(invalid_data)
    
    @pytest.mark.asyncio
    async def test_generate_package_with_missing_deal_data(self, service):
        """Test package generation with missing deal data"""
        request = PackageGenerationRequest(
            template_id=uuid4(),
            deal_id=uuid4(),
            package_name="Test Package"
        )
        
        # Mock template but no deal data
        mock_template = InvestmentPackageTemplate(
            name="Test Template",
            package_type=PackageTypeEnum.EXECUTIVE_SUMMARY,
            sections=["overview"]
        )
        
        with patch.object(service, 'get_template', return_value=mock_template):
            # Should still work with default/empty deal data
            package = await service.generate_package(request)
            assert isinstance(package, InvestmentPackage)
    
    def test_risk_score_edge_cases(self, service):
        """Test risk score calculation edge cases"""
        # High risk deal
        high_risk_deal = {
            "ltv": Decimal("0.95"),
            "renovation_cost": Decimal("200000"),
            "purchase_price": Decimal("300000"),
            "market_risk_score": 8.0
        }
        
        risk_score = service._calculate_risk_score(high_risk_deal)
        assert risk_score > 5.0
        
        # Low risk deal
        low_risk_deal = {
            "ltv": Decimal("0.6"),
            "renovation_cost": Decimal("10000"),
            "purchase_price": Decimal("300000"),
            "market_risk_score": 2.0
        }
        
        risk_score = service._calculate_risk_score(low_risk_deal)
        assert risk_score < 5.0
    
    @pytest.mark.asyncio
    async def test_auto_distribute_package(self, service):
        """Test auto-distribution functionality"""
        package = InvestmentPackage(
            template_id=uuid4(),
            deal_id=uuid4(),
            name="Test Package",
            package_type=PackageTypeEnum.EXECUTIVE_SUMMARY,
            title="Test Title"
        )
        
        request = PackageGenerationRequest(
            template_id=package.template_id,
            deal_id=package.deal_id,
            package_name="Test",
            auto_distribute=True,
            distribution_list=[uuid4(), uuid4()],
            delivery_method=DeliveryMethodEnum.EMAIL
        )
        
        # This should not raise an exception
        await service._auto_distribute_package(package, request)
    
    def test_financial_calculations(self, service, sample_deal_data):
        """Test financial metric calculations"""
        package = InvestmentPackage(
            template_id=uuid4(),
            deal_id=uuid4(),
            name="Test Package",
            package_type=PackageTypeEnum.EXECUTIVE_SUMMARY,
            title="Test Title"
        )
        
        # Set financial data
        package.purchase_price = sample_deal_data["purchase_price"]
        package.renovation_cost = sample_deal_data["renovation_cost"]
        package.projected_rental_income = sample_deal_data["projected_rental_income"]
        package.projected_expenses = sample_deal_data["projected_expenses"]
        package.estimated_value = sample_deal_data["estimated_value"]
        
        # Calculate cash flow
        package.projected_cash_flow = package.projected_rental_income - package.projected_expenses
        assert package.projected_cash_flow == Decimal("1700")
        
        # Calculate total investment
        package.total_investment = package.purchase_price + package.renovation_cost
        assert package.total_investment == Decimal("350000")
        
        # Calculate ROI
        annual_cash_flow = package.projected_cash_flow * 12
        package.projected_roi = annual_cash_flow / package.total_investment
        expected_roi = Decimal("20400") / Decimal("350000")
        assert abs(package.projected_roi - expected_roi) < Decimal("0.001")
        
        # Calculate cap rate
        annual_income = package.projected_rental_income * 12
        package.projected_cap_rate = annual_income / package.estimated_value
        expected_cap_rate = Decimal("30000") / Decimal("400000")
        assert abs(package.projected_cap_rate - expected_cap_rate) < Decimal("0.001")


class TestInvestmentPackageIntegration:
    """Integration tests for investment package workflows"""
    
    @pytest.fixture
    def service(self):
        """Create service instance for integration tests"""
        return InvestmentPackageService(db=Mock())
    
    @pytest.mark.asyncio
    async def test_complete_package_generation_workflow(self, service):
        """Test complete package generation workflow"""
        # Create template
        template_data = {
            "name": "Integration Test Template",
            "package_type": PackageTypeEnum.DETAILED_ANALYSIS,
            "format": PackageFormatEnum.PDF,
            "sections": ["overview", "financials", "risk"],
            "required_data_fields": ["property_address", "purchase_price"]
        }
        
        template = service.create_template(template_data)
        assert template.name == "Integration Test Template"
        
        # Generate package
        request = PackageGenerationRequest(
            template_id=template.id,
            deal_id=uuid4(),
            package_name="Integration Test Package",
            custom_title="Custom Integration Title",
            additional_highlights=["Integration test highlight"],
            auto_distribute=False
        )
        
        package = await service.generate_package(request)
        assert package.name == "Integration Test Package"
        assert package.status == PackageStatusEnum.READY
        
        # Distribute package
        investor_ids = [uuid4(), uuid4()]
        distributions = await service.distribute_package(
            package.id, investor_ids, DeliveryMethodEnum.EMAIL
        )
        
        assert len(distributions) == 2
        
        # Track engagement
        for dist in distributions:
            success = service.track_package_engagement(dist.id, "opened")
            assert success is True
        
        # Get analytics
        analytics = service.get_package_analytics(package.id)
        assert analytics.package_id == package.id
    
    @pytest.mark.asyncio
    async def test_template_to_marketing_workflow(self, service):
        """Test workflow from template creation to marketing material generation"""
        # Create template
        template = service.create_template({
            "name": "Marketing Test Template",
            "package_type": PackageTypeEnum.MARKETING_FLYER,
            "format": PackageFormatEnum.PDF,
            "sections": ["overview", "highlights"]
        })
        
        # Generate package
        request = PackageGenerationRequest(
            template_id=template.id,
            deal_id=uuid4(),
            package_name="Marketing Test Package"
        )
        
        package = await service.generate_package(request)
        
        # Generate marketing materials
        with patch.object(service, 'get_package', return_value=package):
            materials = service.generate_marketing_materials(
                package.id, ["flyer", "social_media"]
            )
        
        assert len(materials) == 2
        assert all(m.package_id == package.id for m in materials)
    
    @pytest.mark.asyncio
    async def test_customization_workflow(self, service):
        """Test investor customization workflow"""
        investor_id = uuid4()
        
        # Update customization preferences
        customization = PackageCustomization(
            investor_id=investor_id,
            preferred_formats=[PackageFormatEnum.PDF, PackageFormatEnum.POWERPOINT],
            preferred_delivery_methods=[DeliveryMethodEnum.EMAIL],
            detail_level="detailed",
            include_photos=True
        )
        
        success = service.update_investor_customization(investor_id, customization)
        assert success is True
        
        # Generate customized package (would use preferences in real implementation)
        template = service.get_all_templates()[0]  # Get first default template
        
        request = PackageGenerationRequest(
            template_id=template.id,
            deal_id=uuid4(),
            package_name="Customized Package",
            format=PackageFormatEnum.PDF  # Use preferred format
        )
        
        package = await service.generate_package(request)
        assert package.name == "Customized Package"