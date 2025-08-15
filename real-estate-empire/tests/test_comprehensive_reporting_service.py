"""
Unit tests for the Comprehensive Reporting Service.
"""

import pytest
import uuid
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from pathlib import Path

from app.services.comprehensive_reporting_service import ComprehensiveReportingService
from app.models.reporting import (
    ReportTemplateDB, ReportDB, ReportScheduleDB, DashboardDB, ChartConfigDB,
    ReportTypeEnum, ReportStatusEnum, ReportFormatEnum, ScheduleFrequencyEnum,
    ReportTemplateCreate, ReportCreate, ReportScheduleCreate, DashboardCreate,
    ChartConfigCreate, ReportGenerationRequest, BulkReportRequest
)
from app.models.portfolio import PortfolioDB
from app.models.property import PropertyDB


class TestComprehensiveReportingService:
    """Test cases for ComprehensiveReportingService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """Create a ComprehensiveReportingService instance with mocked dependencies."""
        with patch('app.services.comprehensive_reporting_service.PortfolioPerformanceService'), \
             patch('app.services.comprehensive_reporting_service.MarketDataService'):
            return ComprehensiveReportingService(mock_db)
    
    @pytest.fixture
    def sample_report_template(self):
        """Create a sample report template."""
        return ReportTemplateDB(
            id=uuid.uuid4(),
            name="Portfolio Performance Template",
            description="Template for portfolio performance reports",
            report_type=ReportTypeEnum.PORTFOLIO_PERFORMANCE,
            template_config={
                "sections": ["summary", "performance", "charts"],
                "charts": ["portfolio_distribution", "cash_flow"]
            },
            is_active=True,
            created_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_report(self):
        """Create a sample report."""
        return ReportDB(
            id=uuid.uuid4(),
            name="Monthly Portfolio Report",
            description="Monthly performance report",
            report_type=ReportTypeEnum.PORTFOLIO_PERFORMANCE,
            status=ReportStatusEnum.PENDING,
            output_format=ReportFormatEnum.HTML,
            created_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_portfolio(self):
        """Create a sample portfolio."""
        return PortfolioDB(
            id=uuid.uuid4(),
            name="Test Portfolio",
            total_properties=5,
            total_value=1000000.0,
            total_equity=600000.0,
            total_debt=400000.0,
            monthly_income=8000.0,
            monthly_expenses=3000.0,
            monthly_cash_flow=5000.0,
            average_cap_rate=0.08,
            average_coc_return=0.12
        )
    
    def test_create_report_template_success(self, service, mock_db):
        """Test successful report template creation."""
        # Arrange
        template_data = ReportTemplateCreate(
            name="Test Template",
            description="Test template description",
            report_type=ReportTypeEnum.PORTFOLIO_PERFORMANCE,
            template_config={"sections": ["summary", "charts"]}
        )
        
        def mock_add(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()
            obj.is_active = True
            obj.is_system_template = False
        
        mock_db.add = Mock(side_effect=mock_add)
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Act
        result = service.create_report_template(template_data)
        
        # Assert
        assert result is not None
        assert result.name == "Test Template"
        assert result.report_type == ReportTypeEnum.PORTFOLIO_PERFORMANCE
        assert result.template_config == {"sections": ["summary", "charts"]}
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_get_report_templates_success(self, service, mock_db, sample_report_template):
        """Test successful retrieval of report templates."""
        # Arrange
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_report_template]
        
        # Act
        result = service.get_report_templates()
        
        # Assert
        assert len(result) == 1
        assert result[0].name == sample_report_template.name
        assert result[0].report_type == sample_report_template.report_type
        
        mock_db.query.assert_called()
    
    def test_get_report_templates_filtered_by_type(self, service, mock_db, sample_report_template):
        """Test retrieval of report templates filtered by type."""
        # Arrange
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [sample_report_template]
        
        # Act
        result = service.get_report_templates(ReportTypeEnum.PORTFOLIO_PERFORMANCE)
        
        # Assert
        assert len(result) == 1
        assert result[0].report_type == ReportTypeEnum.PORTFOLIO_PERFORMANCE
        
        mock_db.query.assert_called()
    
    def test_create_report_success(self, service, mock_db):
        """Test successful report creation."""
        # Arrange
        report_data = ReportCreate(
            name="Test Report",
            description="Test report description",
            report_type=ReportTypeEnum.PORTFOLIO_PERFORMANCE,
            output_format=ReportFormatEnum.HTML
        )
        
        def mock_add(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()
        
        mock_db.add = Mock(side_effect=mock_add)
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Act
        result = service.create_report(report_data)
        
        # Assert
        assert result is not None
        assert result.name == "Test Report"
        assert result.report_type == ReportTypeEnum.PORTFOLIO_PERFORMANCE
        assert result.status == ReportStatusEnum.PENDING
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @patch('app.services.comprehensive_reporting_service.Path')
    def test_generate_report_success(self, mock_path, service, mock_db, sample_report, sample_portfolio):
        """Test successful report generation."""
        # Arrange
        request = ReportGenerationRequest(report_id=sample_report.id)
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.return_value = sample_report
        mock_db.query.return_value.all.return_value = [sample_portfolio]
        mock_db.commit = Mock()
        
        # Mock file operations
        mock_file_path = Mock()
        mock_file_path.exists.return_value = True
        mock_file_path.stat.return_value.st_size = 1024
        mock_path.return_value = mock_file_path
        
        service._save_report_file = Mock(return_value=mock_file_path)
        
        # Act
        result = service.generate_report(request)
        
        # Assert
        assert result is not None
        assert result.status == ReportStatusEnum.COMPLETED
        assert result.progress_percent == 100
        assert result.file_size == 1024
        
        mock_db.commit.assert_called()
    
    def test_generate_report_not_found(self, service, mock_db):
        """Test report generation when report is not found."""
        # Arrange
        request = ReportGenerationRequest(report_id=uuid.uuid4())
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Report .* not found"):
            service.generate_report(request)
    
    def test_generate_bulk_reports_success(self, service, mock_db, sample_report):
        """Test successful bulk report generation."""
        # Arrange
        report_ids = [uuid.uuid4(), uuid.uuid4()]
        request = BulkReportRequest(report_ids=report_ids)
        
        # Mock successful generation
        mock_result = Mock()
        mock_result.id = report_ids[0]
        mock_result.status = ReportStatusEnum.COMPLETED
        
        service.generate_report = Mock(return_value=mock_result)
        
        # Act
        results = service.generate_bulk_reports(request)
        
        # Assert
        assert len(results) == 2
        assert all(result.status == ReportStatusEnum.COMPLETED for result in results)
        
        assert service.generate_report.call_count == 2
    
    def test_create_dashboard_success(self, service, mock_db):
        """Test successful dashboard creation."""
        # Arrange
        dashboard_data = DashboardCreate(
            name="Test Dashboard",
            description="Test dashboard description",
            layout_config={"grid": {"rows": 3, "cols": 4}},
            widgets_config={"widgets": [{"type": "chart", "id": "chart1"}]}
        )
        
        def mock_add(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()
            obj.is_active = True
        
        mock_db.add = Mock(side_effect=mock_add)
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Act
        result = service.create_dashboard(dashboard_data)
        
        # Assert
        assert result is not None
        assert result.name == "Test Dashboard"
        assert result.layout_config == {"grid": {"rows": 3, "cols": 4}}
        assert result.widgets_config == {"widgets": [{"type": "chart", "id": "chart1"}]}
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_get_dashboards_success(self, service, mock_db):
        """Test successful retrieval of dashboards."""
        # Arrange
        sample_dashboard = DashboardDB(
            id=uuid.uuid4(),
            name="Test Dashboard",
            layout_config={},
            widgets_config={},
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_dashboard]
        
        # Act
        result = service.get_dashboards()
        
        # Assert
        assert len(result) == 1
        assert result[0].name == "Test Dashboard"
        
        mock_db.query.assert_called()
    
    def test_create_chart_config_success(self, service, mock_db):
        """Test successful chart configuration creation."""
        # Arrange
        chart_data = ChartConfigCreate(
            name="Test Chart",
            chart_type="bar",
            data_source="portfolio_performance",
            query_config={"metric": "total_value"}
        )
        
        def mock_add(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()
        
        mock_db.add = Mock(side_effect=mock_add)
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Act
        result = service.create_chart_config(chart_data)
        
        # Assert
        assert result is not None
        assert result.name == "Test Chart"
        assert result.chart_type == "bar"
        assert result.data_source == "portfolio_performance"
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_get_chart_data_success(self, service, mock_db, sample_portfolio):
        """Test successful chart data retrieval."""
        # Arrange
        chart_id = uuid.uuid4()
        chart_config = ChartConfigDB(
            id=chart_id,
            name="Portfolio Chart",
            chart_type="pie",
            data_source="portfolio_performance",
            query_config={"metric": "value"},
            chart_options={"responsive": True}
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = chart_config
        mock_db.query.return_value.all.return_value = [sample_portfolio]
        
        # Act
        result = service.get_chart_data(chart_id)
        
        # Assert
        assert result is not None
        assert result.chart_id == chart_id
        assert result.chart_type == "pie"
        assert result.data is not None
        assert result.options == {"responsive": True}
        
        mock_db.query.assert_called()
    
    def test_get_chart_data_not_found(self, service, mock_db):
        """Test chart data retrieval when chart config is not found."""
        # Arrange
        chart_id = uuid.uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Chart config .* not found"):
            service.get_chart_data(chart_id)
    
    def test_create_report_schedule_success(self, service, mock_db):
        """Test successful report schedule creation."""
        # Arrange
        schedule_data = ReportScheduleCreate(
            report_id=uuid.uuid4(),
            name="Daily Report Schedule",
            frequency=ScheduleFrequencyEnum.DAILY,
            schedule_time="09:00",
            email_recipients=["test@example.com"]
        )
        
        def mock_add(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()
        
        mock_db.add = Mock(side_effect=mock_add)
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Act
        result = service.create_report_schedule(schedule_data)
        
        # Assert
        assert result is not None
        assert result.name == "Daily Report Schedule"
        assert result.frequency == ScheduleFrequencyEnum.DAILY
        assert result.schedule_time == "09:00"
        assert result.email_recipients == ["test@example.com"]
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_process_scheduled_reports_success(self, service, mock_db):
        """Test successful processing of scheduled reports."""
        # Arrange
        schedule = ReportScheduleDB(
            id=uuid.uuid4(),
            report_id=uuid.uuid4(),
            name="Test Schedule",
            frequency=ScheduleFrequencyEnum.DAILY,
            is_active=True,
            next_run_at=datetime.utcnow() - timedelta(minutes=1),  # Due now
            email_recipients=["test@example.com"]
        )
        
        mock_db.query.return_value.filter.return_value.all.return_value = [schedule]
        mock_db.commit = Mock()
        
        # Mock successful report generation
        mock_report_result = Mock()
        mock_report_result.generated_at = datetime.utcnow()
        service.generate_report = Mock(return_value=mock_report_result)
        service._send_report_email = Mock()
        
        # Act
        results = service.process_scheduled_reports()
        
        # Assert
        assert len(results) == 1
        assert results[0]["status"] == "success"
        assert results[0]["schedule_id"] == schedule.id
        
        service.generate_report.assert_called_once()
        service._send_report_email.assert_called_once()
        mock_db.commit.assert_called()
    
    def test_generate_portfolio_performance_report(self, service, mock_db, sample_portfolio):
        """Test portfolio performance report generation."""
        # Arrange
        report = ReportDB(
            id=uuid.uuid4(),
            name="Portfolio Report",
            report_type=ReportTypeEnum.PORTFOLIO_PERFORMANCE
        )
        
        mock_db.query.return_value.all.return_value = [sample_portfolio]
        
        # Act
        result = service._generate_portfolio_performance_report(report)
        
        # Assert
        assert result is not None
        assert result["title"] == "Portfolio Performance Report"
        assert "portfolios" in result
        assert "summary" in result
        assert len(result["portfolios"]) == 1
        assert result["summary"]["total_portfolios"] == 1
        assert result["summary"]["total_value"] == sample_portfolio.total_value
    
    def test_generate_property_analysis_report(self, service, mock_db):
        """Test property analysis report generation."""
        # Arrange
        report = ReportDB(
            id=uuid.uuid4(),
            name="Property Report",
            report_type=ReportTypeEnum.PROPERTY_ANALYSIS,
            filters={"city": "Austin", "state": "TX"}
        )
        
        sample_property = PropertyDB(
            id=uuid.uuid4(),
            address="123 Test St",
            city="Austin",
            state="TX",
            property_type="single_family",
            current_value=300000.0,
            bedrooms=3,
            bathrooms=2.0,
            square_feet=1500,
            year_built=2010
        )
        
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = [sample_property]
        mock_db.query.return_value = mock_query
        
        # Act
        result = service._generate_property_analysis_report(report)
        
        # Assert
        assert result is not None
        assert result["title"] == "Property Analysis Report"
        assert "properties" in result
        assert "summary" in result
        assert len(result["properties"]) == 1
        assert result["summary"]["total_properties"] == 1
        assert result["filters"] == {"city": "Austin", "state": "TX"}
    
    def test_generate_market_analysis_report(self, service, mock_db):
        """Test market analysis report generation."""
        # Arrange
        report = ReportDB(
            id=uuid.uuid4(),
            name="Market Report",
            report_type=ReportTypeEnum.MARKET_ANALYSIS
        )
        
        # Mock market data
        mock_market = Mock()
        mock_market.city = "Austin"
        mock_market.state = "TX"
        mock_market.avg_price = 400000
        mock_market.median_price = 380000
        mock_market.total_listings = 150
        
        service.market_service.get_top_markets = Mock(return_value=[mock_market])
        
        # Act
        result = service._generate_market_analysis_report(report)
        
        # Assert
        assert result is not None
        assert result["title"] == "Market Analysis Report"
        assert "markets" in result
        assert "summary" in result
        assert len(result["markets"]) == 1
        assert result["summary"]["total_markets"] == 1
    
    def test_calculate_next_run_time_daily(self, service):
        """Test next run time calculation for daily frequency."""
        result = service._calculate_next_run_time(ScheduleFrequencyEnum.DAILY, "09:00")
        
        assert result > datetime.utcnow()
        assert (result - datetime.utcnow()).days == 1
    
    def test_calculate_next_run_time_weekly(self, service):
        """Test next run time calculation for weekly frequency."""
        result = service._calculate_next_run_time(ScheduleFrequencyEnum.WEEKLY, "MON")
        
        assert result > datetime.utcnow()
        assert (result - datetime.utcnow()).days == 7
    
    def test_calculate_next_run_time_monthly(self, service):
        """Test next run time calculation for monthly frequency."""
        result = service._calculate_next_run_time(ScheduleFrequencyEnum.MONTHLY, "1")
        
        assert result > datetime.utcnow()
        assert (result - datetime.utcnow()).days == 30
    
    @patch('app.services.comprehensive_reporting_service.plt')
    def test_generate_portfolio_charts(self, mock_plt, service):
        """Test portfolio chart generation."""
        # Arrange
        report_data = {
            "portfolios": [
                {"name": "Portfolio 1", "total_value": 500000, "monthly_cash_flow": 2500},
                {"name": "Portfolio 2", "total_value": 750000, "monthly_cash_flow": 3500}
            ]
        }
        
        # Mock matplotlib
        mock_plt.figure.return_value = Mock()
        mock_plt.pie.return_value = Mock()
        mock_plt.bar.return_value = Mock()
        mock_plt.savefig.return_value = Mock()
        mock_plt.close.return_value = Mock()
        
        # Mock BytesIO
        with patch('app.services.comprehensive_reporting_service.BytesIO') as mock_bytesio:
            mock_buffer = Mock()
            mock_buffer.getvalue.return_value = b"fake_image_data"
            mock_bytesio.return_value = mock_buffer
            
            with patch('app.services.comprehensive_reporting_service.base64') as mock_base64:
                mock_base64.b64encode.return_value.decode.return_value = "fake_base64_data"
                
                # Act
                result = service._generate_portfolio_charts(report_data)
        
        # Assert
        assert "portfolio_distribution" in result
        assert "cash_flow_comparison" in result
        assert result["portfolio_distribution"]["type"] == "pie"
        assert result["cash_flow_comparison"]["type"] == "bar"
    
    @patch('app.services.comprehensive_reporting_service.Path')
    def test_save_report_file_json(self, mock_path, service):
        """Test saving report file in JSON format."""
        # Arrange
        report = ReportDB(
            id=uuid.uuid4(),
            output_format=ReportFormatEnum.JSON
        )
        report_data = {"title": "Test Report"}
        charts_data = {"chart1": {"type": "bar"}}
        
        mock_file_path = Mock()
        mock_path.return_value = mock_file_path
        service.reports_dir = Mock()
        service.reports_dir.__truediv__ = Mock(return_value=mock_file_path)
        
        # Mock file operations
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Act
            result = service._save_report_file(report, report_data, charts_data)
        
        # Assert
        assert result == mock_file_path
        mock_open.assert_called_once()
    
    def test_get_portfolio_chart_data(self, service, mock_db, sample_portfolio):
        """Test getting portfolio chart data."""
        # Arrange
        query_config = {"metric": "total_value"}
        mock_db.query.return_value.all.return_value = [sample_portfolio]
        
        # Act
        result = service._get_portfolio_chart_data(query_config)
        
        # Assert
        assert "data" in result
        assert "labels" in result
        assert "datasets" in result
        assert result["labels"] == [sample_portfolio.name]
        assert result["datasets"][0]["data"] == [sample_portfolio.total_value]
    
    def test_get_property_chart_data(self, service, mock_db):
        """Test getting property chart data."""
        # Arrange
        query_config = {"metric": "property_type"}
        
        sample_properties = [
            PropertyDB(id=uuid.uuid4(), property_type="single_family"),
            PropertyDB(id=uuid.uuid4(), property_type="single_family"),
            PropertyDB(id=uuid.uuid4(), property_type="condo")
        ]
        
        mock_db.query.return_value.all.return_value = sample_properties
        
        # Act
        result = service._get_property_chart_data(query_config)
        
        # Assert
        assert "data" in result
        assert "labels" in result
        assert "datasets" in result
        assert "single_family" in result["labels"]
        assert "condo" in result["labels"]
    
    def test_error_handling_report_generation(self, service, mock_db, sample_report):
        """Test error handling in report generation."""
        # Arrange
        request = ReportGenerationRequest(report_id=sample_report.id)
        mock_db.query.return_value.filter.return_value.first.return_value = sample_report
        
        # Mock an exception during generation
        service._generate_portfolio_performance_report = Mock(side_effect=Exception("Generation failed"))
        
        # Act & Assert
        with pytest.raises(Exception, match="Generation failed"):
            service.generate_report(request)
        
        # Verify report status was updated to failed
        assert sample_report.status == ReportStatusEnum.FAILED
        assert sample_report.error_message == "Generation failed"
    
    def test_error_handling_template_creation(self, service, mock_db):
        """Test error handling in template creation."""
        # Arrange
        template_data = ReportTemplateCreate(
            name="Test Template",
            report_type=ReportTypeEnum.PORTFOLIO_PERFORMANCE,
            template_config={}
        )
        
        mock_db.add = Mock(side_effect=Exception("Database error"))
        mock_db.rollback = Mock()
        
        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            service.create_report_template(template_data)
        
        mock_db.rollback.assert_called_once()
    
    @pytest.mark.parametrize("report_type,expected_method", [
        (ReportTypeEnum.PORTFOLIO_PERFORMANCE, "_generate_portfolio_performance_report"),
        (ReportTypeEnum.PROPERTY_ANALYSIS, "_generate_property_analysis_report"),
        (ReportTypeEnum.MARKET_ANALYSIS, "_generate_market_analysis_report"),
        (ReportTypeEnum.DEAL_PIPELINE, "_generate_deal_pipeline_report"),
        (ReportTypeEnum.FINANCIAL_SUMMARY, "_generate_financial_summary_report"),
        (ReportTypeEnum.RISK_ASSESSMENT, "_generate_risk_assessment_report"),
        (ReportTypeEnum.CUSTOM, "_generate_custom_report")
    ])
    def test_report_generation_method_selection(self, service, report_type, expected_method):
        """Test that the correct generation method is selected for each report type."""
        # This test verifies that the service has the expected methods
        assert hasattr(service, expected_method)
        method = getattr(service, expected_method)
        assert callable(method)