"""
Comprehensive Reporting Service for the Real Estate Empire platform.

This service provides:
- Automated report generation
- Custom dashboard creation
- Data visualization and charting
- Scheduled reporting automation
"""

import uuid
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import logging
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

from app.models.reporting import (
    ReportTemplateDB, ReportDB, ReportScheduleDB, DashboardDB, ChartConfigDB,
    ReportTypeEnum, ReportStatusEnum, ReportFormatEnum, ScheduleFrequencyEnum,
    ReportTemplateCreate, ReportTemplateResponse, ReportCreate, ReportResponse,
    ReportScheduleCreate, ReportScheduleResponse, DashboardCreate, DashboardResponse,
    ChartConfigCreate, ChartConfigResponse, ChartDataResponse,
    ReportGenerationRequest, BulkReportRequest
)
from app.models.portfolio import PortfolioDB, PortfolioPropertyDB, PropertyPerformanceDB
from app.models.property import PropertyDB
from app.models.predictive_analytics import PredictionDB
from app.services.portfolio_performance_service import PortfolioPerformanceService
from app.services.market_data_service import MarketDataService

logger = logging.getLogger(__name__)


class ComprehensiveReportingService:
    """Service for comprehensive reporting and analytics."""
    
    def __init__(self, db: Session):
        self.db = db
        self.portfolio_service = PortfolioPerformanceService(db)
        self.market_service = MarketDataService()
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        
        # Chart styling
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    # Report Template Management
    
    def create_report_template(self, template_data: ReportTemplateCreate) -> ReportTemplateResponse:
        """Create a new report template."""
        try:
            template_db = ReportTemplateDB(
                name=template_data.name,
                description=template_data.description,
                report_type=template_data.report_type,
                template_config=template_data.template_config,
                default_parameters=template_data.default_parameters,
                layout_config=template_data.layout_config,
                style_config=template_data.style_config
            )
            
            self.db.add(template_db)
            self.db.commit()
            self.db.refresh(template_db)
            
            logger.info(f"Created report template: {template_data.name}")
            
            return ReportTemplateResponse.model_validate(template_db)
            
        except Exception as e:
            logger.error(f"Error creating report template: {str(e)}")
            self.db.rollback()
            raise
    
    def get_report_templates(self, report_type: Optional[ReportTypeEnum] = None) -> List[ReportTemplateResponse]:
        """Get all report templates, optionally filtered by type."""
        try:
            query = self.db.query(ReportTemplateDB).filter(ReportTemplateDB.is_active == True)
            
            if report_type:
                query = query.filter(ReportTemplateDB.report_type == report_type)
            
            templates = query.all()
            return [ReportTemplateResponse.model_validate(template) for template in templates]
            
        except Exception as e:
            logger.error(f"Error getting report templates: {str(e)}")
            raise
    
    # Report Generation
    
    def create_report(self, report_data: ReportCreate) -> ReportResponse:
        """Create a new report."""
        try:
            report_db = ReportDB(
                name=report_data.name,
                description=report_data.description,
                report_type=report_data.report_type,
                template_id=report_data.template_id,
                parameters=report_data.parameters,
                filters=report_data.filters,
                date_range_start=report_data.date_range_start,
                date_range_end=report_data.date_range_end,
                output_format=report_data.output_format,
                status=ReportStatusEnum.PENDING
            )
            
            self.db.add(report_db)
            self.db.commit()
            self.db.refresh(report_db)
            
            logger.info(f"Created report: {report_data.name}")
            
            return ReportResponse.model_validate(report_db)
            
        except Exception as e:
            logger.error(f"Error creating report: {str(e)}")
            self.db.rollback()
            raise
    
    def generate_report(self, request: ReportGenerationRequest) -> ReportResponse:
        """Generate a report."""
        try:
            report = self.db.query(ReportDB).filter(ReportDB.id == request.report_id).first()
            if not report:
                raise ValueError(f"Report {request.report_id} not found")
            
            # Check if report already exists and is not forced regeneration
            if (report.status == ReportStatusEnum.COMPLETED and 
                report.file_path and 
                Path(report.file_path).exists() and 
                not request.force_regenerate):
                return ReportResponse.model_validate(report)
            
            # Update status to generating
            report.status = ReportStatusEnum.GENERATING
            report.progress_percent = 0
            self.db.commit()
            
            # Generate report based on type
            start_time = datetime.utcnow()
            
            if report.report_type == ReportTypeEnum.PORTFOLIO_PERFORMANCE:
                report_data = self._generate_portfolio_performance_report(report)
            elif report.report_type == ReportTypeEnum.PROPERTY_ANALYSIS:
                report_data = self._generate_property_analysis_report(report)
            elif report.report_type == ReportTypeEnum.MARKET_ANALYSIS:
                report_data = self._generate_market_analysis_report(report)
            elif report.report_type == ReportTypeEnum.DEAL_PIPELINE:
                report_data = self._generate_deal_pipeline_report(report)
            elif report.report_type == ReportTypeEnum.FINANCIAL_SUMMARY:
                report_data = self._generate_financial_summary_report(report)
            elif report.report_type == ReportTypeEnum.RISK_ASSESSMENT:
                report_data = self._generate_risk_assessment_report(report)
            else:
                report_data = self._generate_custom_report(report)
            
            # Generate charts
            charts_data = self._generate_report_charts(report, report_data)
            
            # Save report file
            file_path = self._save_report_file(report, report_data, charts_data)
            
            # Update report status
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            report.status = ReportStatusEnum.COMPLETED
            report.progress_percent = 100
            report.report_data = report_data
            report.charts_data = charts_data
            report.file_path = str(file_path)
            report.file_size = file_path.stat().st_size if file_path.exists() else 0
            report.generated_at = datetime.utcnow()
            report.generation_time_seconds = generation_time
            
            self.db.commit()
            
            logger.info(f"Generated report {report.name} in {generation_time:.2f} seconds")
            
            return ReportResponse.model_validate(report)
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            # Update report status to failed
            if 'report' in locals():
                report.status = ReportStatusEnum.FAILED
                report.error_message = str(e)
                self.db.commit()
            raise
    
    def generate_bulk_reports(self, request: BulkReportRequest) -> List[ReportResponse]:
        """Generate multiple reports in bulk."""
        try:
            results = []
            
            for report_id in request.report_ids:
                try:
                    generation_request = ReportGenerationRequest(
                        report_id=report_id,
                        force_regenerate=True
                    )
                    result = self.generate_report(generation_request)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error generating report {report_id}: {str(e)}")
                    # Create a failed result
                    failed_report = self.db.query(ReportDB).filter(ReportDB.id == report_id).first()
                    if failed_report:
                        failed_report.status = ReportStatusEnum.FAILED
                        failed_report.error_message = str(e)
                        self.db.commit()
                        results.append(ReportResponse.model_validate(failed_report))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk report generation: {str(e)}")
            raise
    
    # Dashboard Management
    
    def create_dashboard(self, dashboard_data: DashboardCreate) -> DashboardResponse:
        """Create a custom dashboard."""
        try:
            dashboard_db = DashboardDB(
                name=dashboard_data.name,
                description=dashboard_data.description,
                layout_config=dashboard_data.layout_config,
                widgets_config=dashboard_data.widgets_config,
                refresh_interval_seconds=dashboard_data.refresh_interval_seconds,
                is_public=dashboard_data.is_public,
                is_default=dashboard_data.is_default
            )
            
            self.db.add(dashboard_db)
            self.db.commit()
            self.db.refresh(dashboard_db)
            
            logger.info(f"Created dashboard: {dashboard_data.name}")
            
            return DashboardResponse.model_validate(dashboard_db)
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {str(e)}")
            self.db.rollback()
            raise
    
    def get_dashboards(self) -> List[DashboardResponse]:
        """Get all active dashboards."""
        try:
            dashboards = self.db.query(DashboardDB).filter(DashboardDB.is_active == True).all()
            return [DashboardResponse.model_validate(dashboard) for dashboard in dashboards]
            
        except Exception as e:
            logger.error(f"Error getting dashboards: {str(e)}")
            raise
    
    # Chart Management
    
    def create_chart_config(self, chart_data: ChartConfigCreate) -> ChartConfigResponse:
        """Create a chart configuration."""
        try:
            chart_db = ChartConfigDB(
                name=chart_data.name,
                chart_type=chart_data.chart_type,
                data_source=chart_data.data_source,
                query_config=chart_data.query_config,
                chart_options=chart_data.chart_options,
                width=chart_data.width,
                height=chart_data.height,
                refresh_interval_seconds=chart_data.refresh_interval_seconds
            )
            
            self.db.add(chart_db)
            self.db.commit()
            self.db.refresh(chart_db)
            
            logger.info(f"Created chart config: {chart_data.name}")
            
            return ChartConfigResponse.model_validate(chart_db)
            
        except Exception as e:
            logger.error(f"Error creating chart config: {str(e)}")
            self.db.rollback()
            raise
    
    def get_chart_data(self, chart_id: uuid.UUID) -> ChartDataResponse:
        """Get data for a specific chart."""
        try:
            chart_config = self.db.query(ChartConfigDB).filter(ChartConfigDB.id == chart_id).first()
            if not chart_config:
                raise ValueError(f"Chart config {chart_id} not found")
            
            # Generate chart data based on data source and query config
            chart_data = self._generate_chart_data(chart_config)
            
            return ChartDataResponse(
                chart_id=chart_id,
                chart_type=chart_config.chart_type,
                data=chart_data["data"],
                labels=chart_data.get("labels"),
                datasets=chart_data.get("datasets"),
                options=chart_config.chart_options,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error getting chart data: {str(e)}")
            raise
    
    # Report Scheduling
    
    def create_report_schedule(self, schedule_data: ReportScheduleCreate) -> ReportScheduleResponse:
        """Create a report schedule."""
        try:
            # Calculate next run time
            next_run = self._calculate_next_run_time(schedule_data.frequency, schedule_data.schedule_time)
            
            schedule_db = ReportScheduleDB(
                report_id=schedule_data.report_id,
                name=schedule_data.name,
                frequency=schedule_data.frequency,
                schedule_time=schedule_data.schedule_time,
                timezone=schedule_data.timezone,
                email_recipients=schedule_data.email_recipients,
                next_run_at=next_run
            )
            
            self.db.add(schedule_db)
            self.db.commit()
            self.db.refresh(schedule_db)
            
            logger.info(f"Created report schedule: {schedule_data.name}")
            
            return ReportScheduleResponse.model_validate(schedule_db)
            
        except Exception as e:
            logger.error(f"Error creating report schedule: {str(e)}")
            self.db.rollback()
            raise
    
    def process_scheduled_reports(self) -> List[Dict[str, Any]]:
        """Process all scheduled reports that are due."""
        try:
            now = datetime.utcnow()
            due_schedules = self.db.query(ReportScheduleDB).filter(
                and_(
                    ReportScheduleDB.is_active == True,
                    ReportScheduleDB.next_run_at <= now
                )
            ).all()
            
            results = []
            
            for schedule in due_schedules:
                try:
                    # Generate the report
                    generation_request = ReportGenerationRequest(
                        report_id=schedule.report_id,
                        force_regenerate=True
                    )
                    report_result = self.generate_report(generation_request)
                    
                    # Update schedule
                    schedule.last_run_at = now
                    schedule.last_run_status = "success"
                    schedule.next_run_at = self._calculate_next_run_time(
                        schedule.frequency, 
                        schedule.schedule_time
                    )
                    
                    # Send email if recipients are configured
                    if schedule.email_recipients:
                        self._send_report_email(schedule, report_result)
                    
                    results.append({
                        "schedule_id": schedule.id,
                        "report_id": schedule.report_id,
                        "status": "success",
                        "generated_at": report_result.generated_at
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing scheduled report {schedule.id}: {str(e)}")
                    schedule.last_run_at = now
                    schedule.last_run_status = f"failed: {str(e)}"
                    schedule.next_run_at = self._calculate_next_run_time(
                        schedule.frequency, 
                        schedule.schedule_time
                    )
                    
                    results.append({
                        "schedule_id": schedule.id,
                        "report_id": schedule.report_id,
                        "status": "failed",
                        "error": str(e)
                    })
            
            self.db.commit()
            
            logger.info(f"Processed {len(due_schedules)} scheduled reports")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing scheduled reports: {str(e)}")
            raise
    
    # Report Generation Methods
    
    def _generate_portfolio_performance_report(self, report: ReportDB) -> Dict[str, Any]:
        """Generate portfolio performance report data."""
        try:
            # Get portfolio data
            portfolios = self.db.query(PortfolioDB).all()
            
            report_data = {
                "title": "Portfolio Performance Report",
                "generated_at": datetime.utcnow().isoformat(),
                "date_range": {
                    "start": report.date_range_start.isoformat() if report.date_range_start else None,
                    "end": report.date_range_end.isoformat() if report.date_range_end else None
                },
                "portfolios": [],
                "summary": {
                    "total_portfolios": len(portfolios),
                    "total_properties": 0,
                    "total_value": 0,
                    "total_cash_flow": 0,
                    "average_roi": 0
                }
            }
            
            total_value = 0
            total_cash_flow = 0
            total_properties = 0
            roi_values = []
            
            for portfolio in portfolios:
                portfolio_data = {
                    "id": str(portfolio.id),
                    "name": portfolio.name,
                    "properties_count": portfolio.total_properties,
                    "total_value": portfolio.total_value,
                    "monthly_cash_flow": portfolio.monthly_cash_flow,
                    "average_cap_rate": portfolio.average_cap_rate,
                    "average_coc_return": portfolio.average_coc_return,
                    "risk_score": portfolio.risk_score
                }
                
                report_data["portfolios"].append(portfolio_data)
                
                total_value += portfolio.total_value or 0
                total_cash_flow += portfolio.monthly_cash_flow or 0
                total_properties += portfolio.total_properties or 0
                
                if portfolio.average_coc_return:
                    roi_values.append(portfolio.average_coc_return)
            
            # Update summary
            report_data["summary"]["total_properties"] = total_properties
            report_data["summary"]["total_value"] = total_value
            report_data["summary"]["total_cash_flow"] = total_cash_flow
            report_data["summary"]["average_roi"] = np.mean(roi_values) if roi_values else 0
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error generating portfolio performance report: {str(e)}")
            raise
    
    def _generate_property_analysis_report(self, report: ReportDB) -> Dict[str, Any]:
        """Generate property analysis report data."""
        try:
            # Get property data
            query = self.db.query(PropertyDB)
            
            if report.filters:
                if "city" in report.filters:
                    query = query.filter(PropertyDB.city.ilike(f"%{report.filters['city']}%"))
                if "state" in report.filters:
                    query = query.filter(PropertyDB.state == report.filters["state"])
                if "property_type" in report.filters:
                    query = query.filter(PropertyDB.property_type == report.filters["property_type"])
            
            properties = query.all()
            
            report_data = {
                "title": "Property Analysis Report",
                "generated_at": datetime.utcnow().isoformat(),
                "filters": report.filters or {},
                "properties": [],
                "summary": {
                    "total_properties": len(properties),
                    "average_value": 0,
                    "value_range": {"min": 0, "max": 0},
                    "property_types": {},
                    "locations": {}
                }
            }
            
            values = []
            property_types = {}
            locations = {}
            
            for property_obj in properties:
                property_data = {
                    "id": str(property_obj.id),
                    "address": property_obj.address,
                    "city": property_obj.city,
                    "state": property_obj.state,
                    "property_type": property_obj.property_type,
                    "current_value": property_obj.current_value,
                    "bedrooms": property_obj.bedrooms,
                    "bathrooms": property_obj.bathrooms,
                    "square_feet": property_obj.square_feet,
                    "year_built": property_obj.year_built
                }
                
                report_data["properties"].append(property_data)
                
                if property_obj.current_value:
                    values.append(property_obj.current_value)
                
                # Count property types
                prop_type = property_obj.property_type
                property_types[prop_type] = property_types.get(prop_type, 0) + 1
                
                # Count locations
                location = f"{property_obj.city}, {property_obj.state}"
                locations[location] = locations.get(location, 0) + 1
            
            # Update summary
            if values:
                report_data["summary"]["average_value"] = np.mean(values)
                report_data["summary"]["value_range"]["min"] = min(values)
                report_data["summary"]["value_range"]["max"] = max(values)
            
            report_data["summary"]["property_types"] = property_types
            report_data["summary"]["locations"] = locations
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error generating property analysis report: {str(e)}")
            raise
    
    def _generate_market_analysis_report(self, report: ReportDB) -> Dict[str, Any]:
        """Generate market analysis report data."""
        try:
            # Get top markets
            top_markets = self.market_service.get_top_markets(20)
            
            report_data = {
                "title": "Market Analysis Report",
                "generated_at": datetime.utcnow().isoformat(),
                "markets": [],
                "summary": {
                    "total_markets": len(top_markets),
                    "average_price": 0,
                    "price_range": {"min": 0, "max": 0},
                    "most_active_market": None
                }
            }
            
            prices = []
            most_active = None
            max_listings = 0
            
            for market in top_markets:
                market_data = {
                    "city": market.city,
                    "state": market.state,
                    "avg_price": market.avg_price,
                    "median_price": market.median_price,
                    "avg_price_per_sqft": market.avg_price_per_sqft,
                    "total_listings": market.total_listings,
                    "avg_bedrooms": market.avg_bedrooms,
                    "avg_bathrooms": market.avg_bathrooms
                }
                
                report_data["markets"].append(market_data)
                
                prices.append(market.avg_price)
                
                if market.total_listings > max_listings:
                    max_listings = market.total_listings
                    most_active = f"{market.city}, {market.state}"
            
            # Update summary
            if prices:
                report_data["summary"]["average_price"] = np.mean(prices)
                report_data["summary"]["price_range"]["min"] = min(prices)
                report_data["summary"]["price_range"]["max"] = max(prices)
            
            report_data["summary"]["most_active_market"] = most_active
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error generating market analysis report: {str(e)}")
            raise
    
    def _generate_deal_pipeline_report(self, report: ReportDB) -> Dict[str, Any]:
        """Generate deal pipeline report data."""
        try:
            # Get predictions (representing deals in pipeline)
            predictions = self.db.query(PredictionDB).filter(
                PredictionDB.prediction_type == "deal_outcome"
            ).all()
            
            report_data = {
                "title": "Deal Pipeline Report",
                "generated_at": datetime.utcnow().isoformat(),
                "deals": [],
                "summary": {
                    "total_deals": len(predictions),
                    "high_confidence_deals": 0,
                    "average_confidence": 0,
                    "pipeline_value": 0
                }
            }
            
            confidence_scores = []
            high_confidence_count = 0
            
            for prediction in predictions:
                deal_data = {
                    "id": str(prediction.id),
                    "created_at": prediction.created_at.isoformat(),
                    "predicted_value": prediction.predicted_value,
                    "confidence_score": prediction.confidence_score,
                    "target_entity_id": str(prediction.target_entity_id) if prediction.target_entity_id else None,
                    "features": prediction.input_features
                }
                
                report_data["deals"].append(deal_data)
                
                if prediction.confidence_score:
                    confidence_scores.append(prediction.confidence_score)
                    if prediction.confidence_score > 0.8:
                        high_confidence_count += 1
            
            # Update summary
            report_data["summary"]["high_confidence_deals"] = high_confidence_count
            if confidence_scores:
                report_data["summary"]["average_confidence"] = np.mean(confidence_scores)
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error generating deal pipeline report: {str(e)}")
            raise
    
    def _generate_financial_summary_report(self, report: ReportDB) -> Dict[str, Any]:
        """Generate financial summary report data."""
        try:
            # Get portfolio financial data
            portfolios = self.db.query(PortfolioDB).all()
            
            report_data = {
                "title": "Financial Summary Report",
                "generated_at": datetime.utcnow().isoformat(),
                "financial_metrics": {
                    "total_portfolio_value": 0,
                    "total_equity": 0,
                    "total_debt": 0,
                    "monthly_income": 0,
                    "monthly_expenses": 0,
                    "net_cash_flow": 0,
                    "average_cap_rate": 0,
                    "average_coc_return": 0
                },
                "portfolio_breakdown": []
            }
            
            total_value = 0
            total_equity = 0
            total_debt = 0
            monthly_income = 0
            monthly_expenses = 0
            cap_rates = []
            coc_returns = []
            
            for portfolio in portfolios:
                portfolio_data = {
                    "name": portfolio.name,
                    "value": portfolio.total_value or 0,
                    "equity": portfolio.total_equity or 0,
                    "debt": portfolio.total_debt or 0,
                    "monthly_cash_flow": portfolio.monthly_cash_flow or 0,
                    "cap_rate": portfolio.average_cap_rate,
                    "coc_return": portfolio.average_coc_return
                }
                
                report_data["portfolio_breakdown"].append(portfolio_data)
                
                total_value += portfolio.total_value or 0
                total_equity += portfolio.total_equity or 0
                total_debt += portfolio.total_debt or 0
                monthly_income += portfolio.monthly_income or 0
                monthly_expenses += portfolio.monthly_expenses or 0
                
                if portfolio.average_cap_rate:
                    cap_rates.append(portfolio.average_cap_rate)
                if portfolio.average_coc_return:
                    coc_returns.append(portfolio.average_coc_return)
            
            # Update financial metrics
            report_data["financial_metrics"]["total_portfolio_value"] = total_value
            report_data["financial_metrics"]["total_equity"] = total_equity
            report_data["financial_metrics"]["total_debt"] = total_debt
            report_data["financial_metrics"]["monthly_income"] = monthly_income
            report_data["financial_metrics"]["monthly_expenses"] = monthly_expenses
            report_data["financial_metrics"]["net_cash_flow"] = monthly_income - monthly_expenses
            report_data["financial_metrics"]["average_cap_rate"] = np.mean(cap_rates) if cap_rates else 0
            report_data["financial_metrics"]["average_coc_return"] = np.mean(coc_returns) if coc_returns else 0
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error generating financial summary report: {str(e)}")
            raise
    
    def _generate_risk_assessment_report(self, report: ReportDB) -> Dict[str, Any]:
        """Generate risk assessment report data."""
        try:
            # Get risk assessment predictions
            risk_predictions = self.db.query(PredictionDB).filter(
                PredictionDB.prediction_type == "risk_assessment"
            ).all()
            
            report_data = {
                "title": "Risk Assessment Report",
                "generated_at": datetime.utcnow().isoformat(),
                "risk_assessments": [],
                "summary": {
                    "total_assessments": len(risk_predictions),
                    "high_risk_count": 0,
                    "medium_risk_count": 0,
                    "low_risk_count": 0,
                    "average_risk_score": 0
                }
            }
            
            risk_scores = []
            high_risk = 0
            medium_risk = 0
            low_risk = 0
            
            for prediction in risk_predictions:
                risk_level = "low"
                if prediction.predicted_value > 75:
                    risk_level = "high"
                    high_risk += 1
                elif prediction.predicted_value > 50:
                    risk_level = "medium"
                    medium_risk += 1
                else:
                    low_risk += 1
                
                assessment_data = {
                    "id": str(prediction.id),
                    "target_entity_type": prediction.target_entity_type,
                    "target_entity_id": str(prediction.target_entity_id) if prediction.target_entity_id else None,
                    "risk_score": prediction.predicted_value,
                    "risk_level": risk_level,
                    "confidence": prediction.confidence_score,
                    "created_at": prediction.created_at.isoformat()
                }
                
                report_data["risk_assessments"].append(assessment_data)
                
                if prediction.predicted_value:
                    risk_scores.append(prediction.predicted_value)
            
            # Update summary
            report_data["summary"]["high_risk_count"] = high_risk
            report_data["summary"]["medium_risk_count"] = medium_risk
            report_data["summary"]["low_risk_count"] = low_risk
            if risk_scores:
                report_data["summary"]["average_risk_score"] = np.mean(risk_scores)
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error generating risk assessment report: {str(e)}")
            raise
    
    def _generate_custom_report(self, report: ReportDB) -> Dict[str, Any]:
        """Generate custom report data."""
        try:
            # Basic custom report structure
            report_data = {
                "title": report.name,
                "generated_at": datetime.utcnow().isoformat(),
                "parameters": report.parameters or {},
                "filters": report.filters or {},
                "data": {}
            }
            
            # Add custom logic based on parameters
            if report.parameters:
                # This would be expanded based on specific custom report requirements
                report_data["data"]["message"] = "Custom report generated successfully"
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error generating custom report: {str(e)}")
            raise
    
    def _generate_report_charts(self, report: ReportDB, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate charts for the report."""
        try:
            charts_data = {}
            
            if report.report_type == ReportTypeEnum.PORTFOLIO_PERFORMANCE:
                charts_data = self._generate_portfolio_charts(report_data)
            elif report.report_type == ReportTypeEnum.PROPERTY_ANALYSIS:
                charts_data = self._generate_property_charts(report_data)
            elif report.report_type == ReportTypeEnum.MARKET_ANALYSIS:
                charts_data = self._generate_market_charts(report_data)
            elif report.report_type == ReportTypeEnum.FINANCIAL_SUMMARY:
                charts_data = self._generate_financial_charts(report_data)
            
            return charts_data
            
        except Exception as e:
            logger.error(f"Error generating report charts: {str(e)}")
            return {}
    
    def _generate_portfolio_charts(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate charts for portfolio performance report."""
        try:
            charts = {}
            
            if "portfolios" in report_data and report_data["portfolios"]:
                # Portfolio value distribution pie chart
                portfolios = report_data["portfolios"]
                names = [p["name"] for p in portfolios]
                values = [p["total_value"] for p in portfolios]
                
                plt.figure(figsize=(10, 6))
                plt.pie(values, labels=names, autopct='%1.1f%%')
                plt.title("Portfolio Value Distribution")
                
                # Convert to base64
                buffer = BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight')
                buffer.seek(0)
                chart_data = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                
                charts["portfolio_distribution"] = {
                    "type": "pie",
                    "title": "Portfolio Value Distribution",
                    "data": chart_data
                }
                
                # Cash flow bar chart
                cash_flows = [p["monthly_cash_flow"] for p in portfolios]
                
                plt.figure(figsize=(12, 6))
                plt.bar(names, cash_flows)
                plt.title("Monthly Cash Flow by Portfolio")
                plt.xlabel("Portfolio")
                plt.ylabel("Monthly Cash Flow ($)")
                plt.xticks(rotation=45)
                
                buffer = BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight')
                buffer.seek(0)
                chart_data = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                
                charts["cash_flow_comparison"] = {
                    "type": "bar",
                    "title": "Monthly Cash Flow by Portfolio",
                    "data": chart_data
                }
            
            return charts
            
        except Exception as e:
            logger.error(f"Error generating portfolio charts: {str(e)}")
            return {}
    
    def _generate_property_charts(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate charts for property analysis report."""
        try:
            charts = {}
            
            if "summary" in report_data and "property_types" in report_data["summary"]:
                # Property types distribution
                property_types = report_data["summary"]["property_types"]
                
                plt.figure(figsize=(10, 6))
                plt.pie(property_types.values(), labels=property_types.keys(), autopct='%1.1f%%')
                plt.title("Property Types Distribution")
                
                buffer = BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight')
                buffer.seek(0)
                chart_data = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                
                charts["property_types"] = {
                    "type": "pie",
                    "title": "Property Types Distribution",
                    "data": chart_data
                }
            
            return charts
            
        except Exception as e:
            logger.error(f"Error generating property charts: {str(e)}")
            return {}
    
    def _generate_market_charts(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate charts for market analysis report."""
        try:
            charts = {}
            
            if "markets" in report_data and report_data["markets"]:
                markets = report_data["markets"][:10]  # Top 10 markets
                
                # Average price comparison
                market_names = [f"{m['city']}, {m['state']}" for m in markets]
                avg_prices = [m["avg_price"] for m in markets]
                
                plt.figure(figsize=(12, 8))
                plt.barh(market_names, avg_prices)
                plt.title("Average Property Prices by Market")
                plt.xlabel("Average Price ($)")
                
                buffer = BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight')
                buffer.seek(0)
                chart_data = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                
                charts["market_prices"] = {
                    "type": "bar",
                    "title": "Average Property Prices by Market",
                    "data": chart_data
                }
            
            return charts
            
        except Exception as e:
            logger.error(f"Error generating market charts: {str(e)}")
            return {}
    
    def _generate_financial_charts(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate charts for financial summary report."""
        try:
            charts = {}
            
            if "financial_metrics" in report_data:
                metrics = report_data["financial_metrics"]
                
                # Asset allocation pie chart
                labels = ["Equity", "Debt"]
                values = [metrics["total_equity"], metrics["total_debt"]]
                
                plt.figure(figsize=(8, 8))
                plt.pie(values, labels=labels, autopct='%1.1f%%')
                plt.title("Asset Allocation")
                
                buffer = BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight')
                buffer.seek(0)
                chart_data = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                
                charts["asset_allocation"] = {
                    "type": "pie",
                    "title": "Asset Allocation",
                    "data": chart_data
                }
            
            return charts
            
        except Exception as e:
            logger.error(f"Error generating financial charts: {str(e)}")
            return {}
    
    def _generate_chart_data(self, chart_config: ChartConfigDB) -> Dict[str, Any]:
        """Generate data for a specific chart configuration."""
        try:
            data_source = chart_config.data_source
            query_config = chart_config.query_config
            
            if data_source == "portfolio_performance":
                return self._get_portfolio_chart_data(query_config)
            elif data_source == "property_analysis":
                return self._get_property_chart_data(query_config)
            elif data_source == "market_data":
                return self._get_market_chart_data(query_config)
            else:
                return {"data": {}, "labels": [], "datasets": []}
            
        except Exception as e:
            logger.error(f"Error generating chart data: {str(e)}")
            return {"data": {}, "labels": [], "datasets": []}
    
    def _get_portfolio_chart_data(self, query_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get chart data for portfolio metrics."""
        portfolios = self.db.query(PortfolioDB).all()
        
        labels = [p.name for p in portfolios]
        values = [p.total_value or 0 for p in portfolios]
        
        return {
            "data": {"labels": labels, "values": values},
            "labels": labels,
            "datasets": [{
                "label": "Portfolio Value",
                "data": values,
                "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF"]
            }]
        }
    
    def _get_property_chart_data(self, query_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get chart data for property metrics."""
        properties = self.db.query(PropertyDB).all()
        
        # Group by property type
        type_counts = {}
        for prop in properties:
            prop_type = prop.property_type
            type_counts[prop_type] = type_counts.get(prop_type, 0) + 1
        
        return {
            "data": {"labels": list(type_counts.keys()), "values": list(type_counts.values())},
            "labels": list(type_counts.keys()),
            "datasets": [{
                "label": "Property Count",
                "data": list(type_counts.values()),
                "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF"]
            }]
        }
    
    def _get_market_chart_data(self, query_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get chart data for market metrics."""
        # This would integrate with market data service
        return {
            "data": {"labels": ["Market 1", "Market 2"], "values": [100, 200]},
            "labels": ["Market 1", "Market 2"],
            "datasets": [{
                "label": "Market Activity",
                "data": [100, 200],
                "backgroundColor": ["#FF6384", "#36A2EB"]
            }]
        }
    
    def _save_report_file(self, report: ReportDB, report_data: Dict[str, Any], charts_data: Dict[str, Any]) -> Path:
        """Save report to file."""
        try:
            file_name = f"report_{report.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            if report.output_format == ReportFormatEnum.JSON:
                file_path = self.reports_dir / f"{file_name}.json"
                with open(file_path, 'w') as f:
                    json.dump({
                        "report_data": report_data,
                        "charts_data": charts_data
                    }, f, indent=2, default=str)
            
            elif report.output_format == ReportFormatEnum.HTML:
                file_path = self.reports_dir / f"{file_name}.html"
                html_content = self._generate_html_report(report_data, charts_data)
                with open(file_path, 'w') as f:
                    f.write(html_content)
            
            elif report.output_format == ReportFormatEnum.CSV:
                file_path = self.reports_dir / f"{file_name}.csv"
                self._save_csv_report(file_path, report_data)
            
            else:
                # Default to JSON
                file_path = self.reports_dir / f"{file_name}.json"
                with open(file_path, 'w') as f:
                    json.dump({
                        "report_data": report_data,
                        "charts_data": charts_data
                    }, f, indent=2, default=str)
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving report file: {str(e)}")
            raise
    
    def _generate_html_report(self, report_data: Dict[str, Any], charts_data: Dict[str, Any]) -> str:
        """Generate HTML report content."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report_data.get('title', 'Report')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .chart {{ text-align: center; margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{report_data.get('title', 'Report')}</h1>
                <p>Generated: {report_data.get('generated_at', '')}</p>
            </div>
        """
        
        # Add charts
        for chart_name, chart_info in charts_data.items():
            html += f"""
            <div class="section">
                <h2>{chart_info.get('title', chart_name)}</h2>
                <div class="chart">
                    <img src="data:image/png;base64,{chart_info.get('data', '')}" alt="{chart_info.get('title', chart_name)}">
                </div>
            </div>
            """
        
        # Add summary data
        if "summary" in report_data:
            html += """
            <div class="section">
                <h2>Summary</h2>
                <table>
            """
            for key, value in report_data["summary"].items():
                if isinstance(value, dict):
                    continue
                html += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{value}</td></tr>"
            html += "</table></div>"
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _save_csv_report(self, file_path: Path, report_data: Dict[str, Any]):
        """Save report data as CSV."""
        try:
            # Convert report data to DataFrame and save as CSV
            if "portfolios" in report_data:
                df = pd.DataFrame(report_data["portfolios"])
            elif "properties" in report_data:
                df = pd.DataFrame(report_data["properties"])
            elif "markets" in report_data:
                df = pd.DataFrame(report_data["markets"])
            else:
                # Create a simple summary CSV
                df = pd.DataFrame([report_data.get("summary", {})])
            
            df.to_csv(file_path, index=False)
            
        except Exception as e:
            logger.error(f"Error saving CSV report: {str(e)}")
            raise
    
    def _calculate_next_run_time(self, frequency: str, schedule_time: Optional[str]) -> datetime:
        """Calculate the next run time for a scheduled report."""
        now = datetime.utcnow()
        
        if frequency == ScheduleFrequencyEnum.DAILY:
            next_run = now + timedelta(days=1)
        elif frequency == ScheduleFrequencyEnum.WEEKLY:
            next_run = now + timedelta(weeks=1)
        elif frequency == ScheduleFrequencyEnum.MONTHLY:
            next_run = now + timedelta(days=30)
        elif frequency == ScheduleFrequencyEnum.QUARTERLY:
            next_run = now + timedelta(days=90)
        elif frequency == ScheduleFrequencyEnum.ANNUALLY:
            next_run = now + timedelta(days=365)
        else:
            next_run = now + timedelta(days=1)  # Default to daily
        
        return next_run
    
    def _send_report_email(self, schedule: ReportScheduleDB, report: ReportResponse):
        """Send report via email to recipients."""
        try:
            # This would integrate with an email service
            logger.info(f"Sending report {report.name} to {len(schedule.email_recipients)} recipients")
            # Email sending logic would go here
            
        except Exception as e:
            logger.error(f"Error sending report email: {str(e)}")
            raise