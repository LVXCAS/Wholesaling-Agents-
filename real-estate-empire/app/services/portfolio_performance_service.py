"""
Portfolio Performance Tracking Service for the Real Estate Empire platform.

This service handles property performance monitoring, portfolio-level metrics aggregation,
automated performance reporting, and performance comparison and benchmarking.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import logging
from statistics import mean, median, stdev

from app.models.portfolio import (
    PortfolioDB, PortfolioPropertyDB, PropertyPerformanceDB, PortfolioPerformanceDB,
    PortfolioResponse, PortfolioPropertyResponse, PropertyPerformanceResponse,
    PortfolioAnalytics, PerformanceBenchmark, PortfolioSummary
)
from app.models.property import PropertyDB
from app.core.database import get_db

logger = logging.getLogger(__name__)


class PortfolioPerformanceService:
    """Service for tracking and analyzing portfolio performance."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_property_performance(self, portfolio_property_id: uuid.UUID, 
                                     period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Calculate performance metrics for a specific property in a portfolio."""
        try:
            # Get portfolio property
            portfolio_property = self.db.query(PortfolioPropertyDB).filter(
                PortfolioPropertyDB.id == portfolio_property_id
            ).first()
            
            if not portfolio_property:
                raise ValueError(f"Portfolio property {portfolio_property_id} not found")
            
            # Get performance data for the period
            performance_records = self.db.query(PropertyPerformanceDB).filter(
                and_(
                    PropertyPerformanceDB.portfolio_property_id == portfolio_property_id,
                    PropertyPerformanceDB.period_start >= period_start,
                    PropertyPerformanceDB.period_end <= period_end
                )
            ).all()
            
            if not performance_records:
                logger.warning(f"No performance records found for property {portfolio_property_id}")
                return self._calculate_basic_metrics(portfolio_property)
            
            # Aggregate performance data
            total_income = sum(record.total_income for record in performance_records)
            total_expenses = sum(record.total_expenses for record in performance_records)
            net_cash_flow = total_income - total_expenses
            
            # Calculate annualized metrics
            period_months = (period_end - period_start).days / 30.44  # Average days per month
            annual_income = total_income * (12 / period_months) if period_months > 0 else 0
            annual_expenses = total_expenses * (12 / period_months) if period_months > 0 else 0
            annual_cash_flow = net_cash_flow * (12 / period_months) if period_months > 0 else 0
            
            # Calculate key performance metrics
            current_value = portfolio_property.current_value or portfolio_property.total_investment
            
            # Cap Rate = (Annual Net Operating Income / Current Property Value) * 100
            cap_rate = (annual_cash_flow / current_value * 100) if current_value > 0 else 0
            
            # Cash-on-Cash Return = (Annual Cash Flow / Total Cash Invested) * 100
            cash_invested = portfolio_property.total_investment - portfolio_property.current_debt
            coc_return = (annual_cash_flow / cash_invested * 100) if cash_invested > 0 else 0
            
            # ROI = ((Current Value - Total Investment) / Total Investment) * 100
            roi = ((current_value - portfolio_property.total_investment) / 
                   portfolio_property.total_investment * 100) if portfolio_property.total_investment > 0 else 0
            
            # Appreciation rate (annualized)
            acquisition_years = (datetime.now() - portfolio_property.acquisition_date).days / 365.25
            appreciation_rate = 0
            if acquisition_years > 0 and portfolio_property.acquisition_price > 0:
                appreciation_rate = (((current_value / portfolio_property.acquisition_price) ** 
                                   (1 / acquisition_years)) - 1) * 100
            
            # Calculate occupancy rate
            occupancy_rate = mean([record.occupancy_rate for record in performance_records 
                                 if record.occupancy_rate is not None]) if performance_records else None
            
            return {
                "property_id": portfolio_property.property_id,
                "portfolio_property_id": portfolio_property_id,
                "period_start": period_start,
                "period_end": period_end,
                "total_income": total_income,
                "total_expenses": total_expenses,
                "net_cash_flow": net_cash_flow,
                "annual_income": annual_income,
                "annual_expenses": annual_expenses,
                "annual_cash_flow": annual_cash_flow,
                "current_value": current_value,
                "total_investment": portfolio_property.total_investment,
                "current_equity": current_value - portfolio_property.current_debt,
                "cap_rate": cap_rate,
                "coc_return": coc_return,
                "roi": roi,
                "appreciation_rate": appreciation_rate,
                "occupancy_rate": occupancy_rate
            }
            
        except Exception as e:
            logger.error(f"Error calculating property performance: {str(e)}")
            raise
    
    def _calculate_basic_metrics(self, portfolio_property: PortfolioPropertyDB) -> Dict[str, Any]:
        """Calculate basic metrics when no performance records exist."""
        current_value = portfolio_property.current_value or portfolio_property.total_investment
        annual_cash_flow = portfolio_property.monthly_cash_flow * 12
        
        # Basic calculations
        cap_rate = (annual_cash_flow / current_value * 100) if current_value > 0 else 0
        cash_invested = portfolio_property.total_investment - portfolio_property.current_debt
        coc_return = (annual_cash_flow / cash_invested * 100) if cash_invested > 0 else 0
        roi = ((current_value - portfolio_property.total_investment) / 
               portfolio_property.total_investment * 100) if portfolio_property.total_investment > 0 else 0
        
        return {
            "property_id": portfolio_property.property_id,
            "portfolio_property_id": portfolio_property.id,
            "current_value": current_value,
            "total_investment": portfolio_property.total_investment,
            "current_equity": current_value - portfolio_property.current_debt,
            "annual_cash_flow": annual_cash_flow,
            "cap_rate": cap_rate,
            "coc_return": coc_return,
            "roi": roi,
            "monthly_cash_flow": portfolio_property.monthly_cash_flow
        }
    
    def calculate_portfolio_performance(self, portfolio_id: uuid.UUID, 
                                      period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Calculate aggregated performance metrics for an entire portfolio."""
        try:
            # Get portfolio
            portfolio = self.db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
            if not portfolio:
                raise ValueError(f"Portfolio {portfolio_id} not found")
            
            # Get all properties in portfolio
            portfolio_properties = self.db.query(PortfolioPropertyDB).filter(
                PortfolioPropertyDB.portfolio_id == portfolio_id
            ).all()
            
            if not portfolio_properties:
                logger.warning(f"No properties found in portfolio {portfolio_id}")
                return self._empty_portfolio_metrics(portfolio_id)
            
            # Calculate performance for each property
            property_performances = []
            for prop in portfolio_properties:
                try:
                    perf = self.calculate_property_performance(prop.id, period_start, period_end)
                    property_performances.append(perf)
                except Exception as e:
                    logger.error(f"Error calculating performance for property {prop.id}: {str(e)}")
                    continue
            
            if not property_performances:
                return self._empty_portfolio_metrics(portfolio_id)
            
            # Aggregate portfolio metrics
            total_value = sum(perf.get("current_value", 0) for perf in property_performances)
            total_investment = sum(perf.get("total_investment", 0) for perf in property_performances)
            total_equity = sum(perf.get("current_equity", 0) for perf in property_performances)
            total_debt = total_value - total_equity
            
            total_income = sum(perf.get("total_income", 0) for perf in property_performances)
            total_expenses = sum(perf.get("total_expenses", 0) for perf in property_performances)
            net_cash_flow = total_income - total_expenses
            
            annual_cash_flow = sum(perf.get("annual_cash_flow", 0) for perf in property_performances)
            
            # Calculate weighted averages for rates
            cap_rates = [perf.get("cap_rate", 0) for perf in property_performances if perf.get("cap_rate")]
            coc_returns = [perf.get("coc_return", 0) for perf in property_performances if perf.get("coc_return")]
            rois = [perf.get("roi", 0) for perf in property_performances if perf.get("roi")]
            
            average_cap_rate = mean(cap_rates) if cap_rates else 0
            average_coc_return = mean(coc_returns) if coc_returns else 0
            average_roi = mean(rois) if rois else 0
            
            # Calculate portfolio-level ROI
            portfolio_roi = ((total_value - total_investment) / total_investment * 100) if total_investment > 0 else 0
            
            # Calculate diversification score (simplified)
            diversification_score = self._calculate_diversification_score(portfolio_properties)
            
            # Calculate risk score (simplified)
            risk_score = self._calculate_risk_score(property_performances)
            
            return {
                "portfolio_id": portfolio_id,
                "period_start": period_start,
                "period_end": period_end,
                "total_properties": len(portfolio_properties),
                "total_value": total_value,
                "total_investment": total_investment,
                "total_equity": total_equity,
                "total_debt": total_debt,
                "total_income": total_income,
                "total_expenses": total_expenses,
                "net_cash_flow": net_cash_flow,
                "annual_cash_flow": annual_cash_flow,
                "average_cap_rate": average_cap_rate,
                "average_coc_return": average_coc_return,
                "average_roi": average_roi,
                "portfolio_roi": portfolio_roi,
                "diversification_score": diversification_score,
                "risk_score": risk_score,
                "property_performances": property_performances
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio performance: {str(e)}")
            raise
    
    def _empty_portfolio_metrics(self, portfolio_id: uuid.UUID) -> Dict[str, Any]:
        """Return empty metrics for portfolios with no properties."""
        return {
            "portfolio_id": portfolio_id,
            "total_properties": 0,
            "total_value": 0.0,
            "total_investment": 0.0,
            "total_equity": 0.0,
            "total_debt": 0.0,
            "total_income": 0.0,
            "total_expenses": 0.0,
            "net_cash_flow": 0.0,
            "annual_cash_flow": 0.0,
            "average_cap_rate": 0.0,
            "average_coc_return": 0.0,
            "average_roi": 0.0,
            "portfolio_roi": 0.0,
            "diversification_score": 0.0,
            "risk_score": 0.0,
            "property_performances": []
        }
    
    def _calculate_diversification_score(self, portfolio_properties: List[PortfolioPropertyDB]) -> float:
        """Calculate a diversification score based on property characteristics."""
        if not portfolio_properties:
            return 0.0
        
        # Get property details for diversification analysis
        property_ids = [prop.property_id for prop in portfolio_properties]
        properties = self.db.query(PropertyDB).filter(PropertyDB.id.in_(property_ids)).all()
        
        if not properties:
            return 0.0
        
        # Analyze diversification across multiple dimensions
        cities = set(prop.city for prop in properties if hasattr(prop, 'city') and prop.city)
        property_types = set(prop.property_type for prop in properties if hasattr(prop, 'property_type') and prop.property_type)
        neighborhoods = set(prop.neighborhood for prop in properties if hasattr(prop, 'neighborhood') and prop.neighborhood)
        
        # Simple diversification score (0-100)
        city_diversity = min(len(cities) / len(properties), 1.0) * 40 if cities else 0
        type_diversity = min(len(property_types) / len(properties), 1.0) * 30 if property_types else 0
        neighborhood_diversity = min(len(neighborhoods) / len(properties), 1.0) * 30 if neighborhoods else 0
        
        return city_diversity + type_diversity + neighborhood_diversity
    
    def _calculate_risk_score(self, property_performances: List[Dict[str, Any]]) -> float:
        """Calculate a risk score based on performance variability."""
        if not property_performances:
            return 0.0
        
        # Calculate risk based on cash flow variability
        cash_flows = [perf.get("annual_cash_flow", 0) for perf in property_performances]
        cap_rates = [perf.get("cap_rate", 0) for perf in property_performances if perf.get("cap_rate")]
        
        if len(cash_flows) < 2:
            return 50.0  # Medium risk for single property
        
        # Calculate coefficient of variation for cash flows
        cash_flow_mean = mean(cash_flows)
        if cash_flow_mean == 0:
            return 100.0  # High risk if no cash flow
        
        cash_flow_std = stdev(cash_flows)
        cash_flow_cv = cash_flow_std / abs(cash_flow_mean)
        
        # Convert to risk score (0-100, lower is better)
        risk_score = min(cash_flow_cv * 100, 100)
        
        return risk_score
    
    def update_portfolio_metrics(self, portfolio_id: uuid.UUID) -> bool:
        """Update cached portfolio metrics."""
        try:
            # Calculate current performance
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)  # Last year
            
            performance = self.calculate_portfolio_performance(portfolio_id, start_date, end_date)
            
            # Update portfolio record
            portfolio = self.db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
            if not portfolio:
                return False
            
            portfolio.total_properties = performance["total_properties"]
            portfolio.total_value = performance["total_value"]
            portfolio.total_equity = performance["total_equity"]
            portfolio.total_debt = performance["total_debt"]
            portfolio.monthly_income = performance["annual_cash_flow"] / 12
            portfolio.monthly_expenses = performance["total_expenses"] / 12
            portfolio.monthly_cash_flow = performance["net_cash_flow"] / 12
            portfolio.average_cap_rate = performance["average_cap_rate"]
            portfolio.average_coc_return = performance["average_coc_return"]
            portfolio.average_roi = performance["average_roi"]
            portfolio.diversification_score = performance["diversification_score"]
            portfolio.risk_score = performance["risk_score"]
            portfolio.last_performance_update = datetime.now()
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error updating portfolio metrics: {str(e)}")
            self.db.rollback()
            return False
    
    def generate_performance_report(self, portfolio_id: uuid.UUID, 
                                  period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Generate a comprehensive performance report for a portfolio."""
        try:
            # Get portfolio performance
            portfolio_performance = self.calculate_portfolio_performance(portfolio_id, period_start, period_end)
            
            # Get portfolio details
            portfolio = self.db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
            if not portfolio:
                raise ValueError(f"Portfolio {portfolio_id} not found")
            
            # Get historical performance for trends
            historical_performance = self._get_historical_performance(portfolio_id, period_start, period_end)
            
            # Generate benchmarks
            benchmarks = self._generate_benchmarks(portfolio_performance)
            
            # Create comprehensive report
            report = {
                "portfolio_id": portfolio_id,
                "portfolio_name": portfolio.name,
                "report_period": {
                    "start": period_start,
                    "end": period_end
                },
                "generated_at": datetime.now(),
                "summary": {
                    "total_properties": portfolio_performance["total_properties"],
                    "total_value": portfolio_performance["total_value"],
                    "total_equity": portfolio_performance["total_equity"],
                    "net_cash_flow": portfolio_performance["net_cash_flow"],
                    "average_cap_rate": portfolio_performance["average_cap_rate"],
                    "average_coc_return": portfolio_performance["average_coc_return"],
                    "portfolio_roi": portfolio_performance["portfolio_roi"]
                },
                "performance_metrics": portfolio_performance,
                "property_breakdown": portfolio_performance["property_performances"],
                "historical_trends": historical_performance,
                "benchmarks": benchmarks,
                "risk_analysis": {
                    "diversification_score": portfolio_performance["diversification_score"],
                    "risk_score": portfolio_performance["risk_score"]
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {str(e)}")
            raise
    
    def _get_historical_performance(self, portfolio_id: uuid.UUID, 
                                  period_start: datetime, period_end: datetime) -> List[Dict[str, Any]]:
        """Get historical performance data for trend analysis."""
        try:
            # Get monthly performance records
            historical_records = self.db.query(PortfolioPerformanceDB).filter(
                and_(
                    PortfolioPerformanceDB.portfolio_id == portfolio_id,
                    PortfolioPerformanceDB.period_start >= period_start - timedelta(days=365),
                    PortfolioPerformanceDB.period_end <= period_end,
                    PortfolioPerformanceDB.period_type == "monthly"
                )
            ).order_by(PortfolioPerformanceDB.period_start).all()
            
            return [
                {
                    "period": record.period_start.strftime("%Y-%m"),
                    "total_value": record.total_value,
                    "net_cash_flow": record.net_cash_flow,
                    "average_cap_rate": record.average_cap_rate,
                    "total_return": record.total_return
                }
                for record in historical_records
            ]
            
        except Exception as e:
            logger.error(f"Error getting historical performance: {str(e)}")
            return []
    
    def _generate_benchmarks(self, portfolio_performance: Dict[str, Any]) -> List[PerformanceBenchmark]:
        """Generate performance benchmarks for comparison."""
        # Industry benchmarks (these would typically come from market data)
        industry_benchmarks = {
            "cap_rate": 6.5,  # Average cap rate
            "coc_return": 8.0,  # Average cash-on-cash return
            "roi": 12.0,  # Average ROI
            "diversification_score": 60.0  # Good diversification threshold
        }
        
        benchmarks = []
        
        for metric, benchmark_value in industry_benchmarks.items():
            portfolio_value = portfolio_performance.get(f"average_{metric}", portfolio_performance.get(metric, 0))
            
            if portfolio_value >= benchmark_value:
                comparison = "above"
                percentile = min(75 + (portfolio_value - benchmark_value) / benchmark_value * 25, 100)
            else:
                comparison = "below"
                percentile = max(25 - (benchmark_value - portfolio_value) / benchmark_value * 25, 0)
            
            benchmarks.append(PerformanceBenchmark(
                metric_name=metric,
                portfolio_value=portfolio_value,
                benchmark_value=benchmark_value,
                percentile_rank=percentile,
                comparison_result=comparison
            ))
        
        return benchmarks
    
    def get_portfolio_analytics(self, portfolio_id: uuid.UUID) -> PortfolioAnalytics:
        """Get comprehensive analytics for a portfolio."""
        try:
            # Calculate performance for different periods
            end_date = datetime.now()
            ytd_start = datetime(end_date.year, 1, 1)
            inception_start = self._get_portfolio_inception_date(portfolio_id)
            
            # Get YTD performance
            ytd_performance = self.calculate_portfolio_performance(portfolio_id, ytd_start, end_date)
            
            # Get inception-to-date performance
            inception_performance = self.calculate_portfolio_performance(portfolio_id, inception_start, end_date)
            
            # Get trends
            cash_flow_trend = self._get_cash_flow_trend(portfolio_id)
            value_trend = self._get_value_trend(portfolio_id)
            
            # Get property performance breakdown
            property_performance = ytd_performance["property_performances"]
            
            # Generate benchmarks
            benchmarks = self._generate_benchmarks(ytd_performance)
            
            # Risk and diversification analysis
            risk_metrics = {
                "risk_score": ytd_performance["risk_score"],
                "volatility": self._calculate_volatility(portfolio_id),
                "max_drawdown": self._calculate_max_drawdown(portfolio_id)
            }
            
            diversification_analysis = {
                "score": ytd_performance["diversification_score"],
                "geographic_diversity": self._analyze_geographic_diversity(portfolio_id),
                "property_type_diversity": self._analyze_property_type_diversity(portfolio_id)
            }
            
            return PortfolioAnalytics(
                portfolio_id=portfolio_id,
                total_return_ytd=ytd_performance["portfolio_roi"],
                total_return_inception=inception_performance["portfolio_roi"],
                cash_flow_trend=cash_flow_trend,
                value_trend=value_trend,
                performance_by_property=property_performance,
                benchmarks=benchmarks,
                risk_metrics=risk_metrics,
                diversification_analysis=diversification_analysis
            )
            
        except Exception as e:
            logger.error(f"Error getting portfolio analytics: {str(e)}")
            raise
    
    def _get_portfolio_inception_date(self, portfolio_id: uuid.UUID) -> datetime:
        """Get the inception date of a portfolio (earliest property acquisition)."""
        earliest_property = self.db.query(PortfolioPropertyDB).filter(
            PortfolioPropertyDB.portfolio_id == portfolio_id
        ).order_by(PortfolioPropertyDB.acquisition_date).first()
        
        if earliest_property:
            return earliest_property.acquisition_date
        else:
            # Fallback to portfolio creation date
            portfolio = self.db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
            return portfolio.created_at if portfolio else datetime.now()
    
    def _get_cash_flow_trend(self, portfolio_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get cash flow trend data for the last 12 months."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        monthly_records = self.db.query(PortfolioPerformanceDB).filter(
            and_(
                PortfolioPerformanceDB.portfolio_id == portfolio_id,
                PortfolioPerformanceDB.period_start >= start_date,
                PortfolioPerformanceDB.period_type == "monthly"
            )
        ).order_by(PortfolioPerformanceDB.period_start).all()
        
        return [
            {
                "month": record.period_start.strftime("%Y-%m"),
                "cash_flow": record.net_cash_flow,
                "income": record.total_income,
                "expenses": record.total_expenses
            }
            for record in monthly_records
        ]
    
    def _get_value_trend(self, portfolio_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get portfolio value trend data for the last 12 months."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        monthly_records = self.db.query(PortfolioPerformanceDB).filter(
            and_(
                PortfolioPerformanceDB.portfolio_id == portfolio_id,
                PortfolioPerformanceDB.period_start >= start_date,
                PortfolioPerformanceDB.period_type == "monthly"
            )
        ).order_by(PortfolioPerformanceDB.period_start).all()
        
        return [
            {
                "month": record.period_start.strftime("%Y-%m"),
                "total_value": record.total_value,
                "total_equity": record.total_equity,
                "appreciation": record.appreciation
            }
            for record in monthly_records
        ]
    
    def _calculate_volatility(self, portfolio_id: uuid.UUID) -> float:
        """Calculate portfolio volatility based on monthly returns."""
        # This is a simplified volatility calculation
        # In practice, you'd want more sophisticated risk metrics
        monthly_records = self.db.query(PortfolioPerformanceDB).filter(
            and_(
                PortfolioPerformanceDB.portfolio_id == portfolio_id,
                PortfolioPerformanceDB.period_type == "monthly"
            )
        ).order_by(PortfolioPerformanceDB.period_start).limit(12).all()
        
        if len(monthly_records) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(monthly_records)):
            prev_value = monthly_records[i-1].total_value
            curr_value = monthly_records[i].total_value
            if prev_value > 0:
                monthly_return = (curr_value - prev_value) / prev_value
                returns.append(monthly_return)
        
        return stdev(returns) * 100 if len(returns) > 1 else 0.0
    
    def _calculate_max_drawdown(self, portfolio_id: uuid.UUID) -> float:
        """Calculate maximum drawdown over the last 12 months."""
        monthly_records = self.db.query(PortfolioPerformanceDB).filter(
            and_(
                PortfolioPerformanceDB.portfolio_id == portfolio_id,
                PortfolioPerformanceDB.period_type == "monthly"
            )
        ).order_by(PortfolioPerformanceDB.period_start).limit(12).all()
        
        if not monthly_records:
            return 0.0
        
        values = [record.total_value for record in monthly_records]
        max_drawdown = 0.0
        peak = values[0]
        
        for value in values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown * 100
    
    def _analyze_geographic_diversity(self, portfolio_id: uuid.UUID) -> Dict[str, Any]:
        """Analyze geographic diversity of portfolio properties."""
        portfolio_properties = self.db.query(PortfolioPropertyDB).filter(
            PortfolioPropertyDB.portfolio_id == portfolio_id
        ).all()
        
        if not portfolio_properties:
            return {"cities": [], "states": [], "diversity_score": 0.0}
        
        property_ids = [prop.property_id for prop in portfolio_properties]
        properties = self.db.query(PropertyDB).filter(PropertyDB.id.in_(property_ids)).all()
        
        cities = {}
        states = {}
        
        for prop in properties:
            if hasattr(prop, 'city') and prop.city:
                cities[prop.city] = cities.get(prop.city, 0) + 1
            if hasattr(prop, 'state') and prop.state:
                states[prop.state] = states.get(prop.state, 0) + 1
        
        diversity_score = 0.0
        if properties:
            city_diversity = min(len(cities) / len(properties), 1.0) * 50 if cities else 0
            state_diversity = min(len(states) / len(properties), 1.0) * 50 if states else 0
            diversity_score = city_diversity + state_diversity
        
        return {
            "cities": [{"name": city, "count": count} for city, count in cities.items()],
            "states": [{"name": state, "count": count} for state, count in states.items()],
            "diversity_score": diversity_score
        }
    
    def _analyze_property_type_diversity(self, portfolio_id: uuid.UUID) -> Dict[str, Any]:
        """Analyze property type diversity of portfolio properties."""
        portfolio_properties = self.db.query(PortfolioPropertyDB).filter(
            PortfolioPropertyDB.portfolio_id == portfolio_id
        ).all()
        
        if not portfolio_properties:
            return {"types": [], "diversity_score": 0.0}
        
        property_ids = [prop.property_id for prop in portfolio_properties]
        properties = self.db.query(PropertyDB).filter(PropertyDB.id.in_(property_ids)).all()
        
        property_types = {}
        for prop in properties:
            if hasattr(prop, 'property_type') and prop.property_type:
                property_types[prop.property_type] = property_types.get(prop.property_type, 0) + 1
        
        diversity_score = 0.0
        if properties and property_types:
            diversity_score = min(len(property_types) / len(properties), 1.0) * 100
        
        return {
            "types": [{"name": ptype, "count": count} for ptype, count in property_types.items()],
            "diversity_score": diversity_score
        }


def get_portfolio_performance_service(db: Session = None) -> PortfolioPerformanceService:
    """Factory function to get PortfolioPerformanceService instance."""
    if db is None:
        db = next(get_db())
    return PortfolioPerformanceService(db)