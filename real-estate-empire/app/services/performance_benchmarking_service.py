"""
Performance Benchmarking Service for the Real Estate Empire platform.

This service handles performance comparison against industry benchmarks,
peer portfolios, and market indices.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import logging
from statistics import mean, median, stdev
from enum import Enum

from app.models.portfolio import PortfolioDB, PortfolioPropertyDB, PerformanceBenchmark
from app.services.portfolio_performance_service import PortfolioPerformanceService
from app.core.database import get_db

logger = logging.getLogger(__name__)


class BenchmarkType(str, Enum):
    """Enum for benchmark types."""
    INDUSTRY_AVERAGE = "industry_average"
    MARKET_INDEX = "market_index"
    PEER_PORTFOLIO = "peer_portfolio"
    HISTORICAL_PERFORMANCE = "historical_performance"
    GEOGRAPHIC_MARKET = "geographic_market"
    PROPERTY_TYPE = "property_type"


class PerformanceMetric(str, Enum):
    """Enum for performance metrics."""
    CAP_RATE = "cap_rate"
    COC_RETURN = "coc_return"
    ROI = "roi"
    CASH_FLOW = "cash_flow"
    OCCUPANCY_RATE = "occupancy_rate"
    APPRECIATION_RATE = "appreciation_rate"
    TOTAL_RETURN = "total_return"
    EXPENSE_RATIO = "expense_ratio"


class PerformanceBenchmarkingService:
    """Service for benchmarking portfolio performance."""
    
    def __init__(self, db: Session):
        self.db = db
        self.performance_service = PortfolioPerformanceService(db)
        
        # Industry benchmark data (in a real system, this would come from external sources)
        self.industry_benchmarks = {
            PerformanceMetric.CAP_RATE: {
                "single_family": 6.5,
                "multi_family": 7.2,
                "commercial": 8.1,
                "overall": 6.8
            },
            PerformanceMetric.COC_RETURN: {
                "single_family": 8.5,
                "multi_family": 9.2,
                "commercial": 10.1,
                "overall": 8.8
            },
            PerformanceMetric.ROI: {
                "single_family": 12.0,
                "multi_family": 13.5,
                "commercial": 15.2,
                "overall": 12.8
            },
            PerformanceMetric.OCCUPANCY_RATE: {
                "single_family": 92.0,
                "multi_family": 89.5,
                "commercial": 87.2,
                "overall": 90.0
            }
        }
        
        # Geographic market benchmarks
        self.geographic_benchmarks = {
            "New York": {
                PerformanceMetric.CAP_RATE: 4.8,
                PerformanceMetric.COC_RETURN: 6.2,
                PerformanceMetric.APPRECIATION_RATE: 5.5
            },
            "Los Angeles": {
                PerformanceMetric.CAP_RATE: 4.2,
                PerformanceMetric.COC_RETURN: 5.8,
                PerformanceMetric.APPRECIATION_RATE: 6.2
            },
            "Chicago": {
                PerformanceMetric.CAP_RATE: 7.1,
                PerformanceMetric.COC_RETURN: 9.5,
                PerformanceMetric.APPRECIATION_RATE: 3.8
            },
            "Dallas": {
                PerformanceMetric.CAP_RATE: 6.8,
                PerformanceMetric.COC_RETURN: 8.9,
                PerformanceMetric.APPRECIATION_RATE: 4.2
            }
        }
    
    def benchmark_portfolio_performance(self, portfolio_id: uuid.UUID, 
                                      benchmark_types: List[BenchmarkType] = None) -> Dict[str, Any]:
        """Benchmark a portfolio's performance against various benchmarks."""
        try:
            if benchmark_types is None:
                benchmark_types = [
                    BenchmarkType.INDUSTRY_AVERAGE,
                    BenchmarkType.PEER_PORTFOLIO,
                    BenchmarkType.HISTORICAL_PERFORMANCE
                ]
            
            # Get portfolio performance
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            portfolio_performance = self.performance_service.calculate_portfolio_performance(
                portfolio_id, start_date, end_date
            )
            
            # Get portfolio details
            portfolio = self.db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
            if not portfolio:
                raise ValueError(f"Portfolio {portfolio_id} not found")
            
            benchmarks = {}
            
            for benchmark_type in benchmark_types:
                if benchmark_type == BenchmarkType.INDUSTRY_AVERAGE:
                    benchmarks["industry_average"] = self._benchmark_against_industry(
                        portfolio_performance, portfolio_id
                    )
                elif benchmark_type == BenchmarkType.PEER_PORTFOLIO:
                    benchmarks["peer_portfolio"] = self._benchmark_against_peers(
                        portfolio_performance, portfolio_id
                    )
                elif benchmark_type == BenchmarkType.HISTORICAL_PERFORMANCE:
                    benchmarks["historical_performance"] = self._benchmark_against_history(
                        portfolio_performance, portfolio_id
                    )
                elif benchmark_type == BenchmarkType.GEOGRAPHIC_MARKET:
                    benchmarks["geographic_market"] = self._benchmark_against_geography(
                        portfolio_performance, portfolio_id
                    )
                elif benchmark_type == BenchmarkType.PROPERTY_TYPE:
                    benchmarks["property_type"] = self._benchmark_against_property_type(
                        portfolio_performance, portfolio_id
                    )
            
            return {
                "portfolio_id": portfolio_id,
                "portfolio_name": portfolio.name,
                "benchmark_date": datetime.now(),
                "portfolio_performance": portfolio_performance,
                "benchmarks": benchmarks,
                "overall_ranking": self._calculate_overall_ranking(benchmarks),
                "performance_summary": self._generate_performance_summary(benchmarks)
            }
            
        except Exception as e:
            logger.error(f"Error benchmarking portfolio performance: {str(e)}")
            raise
    
    def _benchmark_against_industry(self, portfolio_performance: Dict[str, Any], 
                                  portfolio_id: uuid.UUID) -> Dict[str, Any]:
        """Benchmark against industry averages."""
        try:
            # Get portfolio property types for weighted benchmarking
            property_type_distribution = self._get_property_type_distribution(portfolio_id)
            
            benchmarks = []
            
            # Cap Rate Benchmark
            portfolio_cap_rate = portfolio_performance.get("average_cap_rate", 0)
            industry_cap_rate = self._calculate_weighted_benchmark(
                property_type_distribution, 
                self.industry_benchmarks[PerformanceMetric.CAP_RATE]
            )
            
            benchmarks.append(PerformanceBenchmark(
                metric_name="cap_rate",
                portfolio_value=portfolio_cap_rate,
                benchmark_value=industry_cap_rate,
                percentile_rank=self._calculate_percentile_rank(portfolio_cap_rate, industry_cap_rate),
                comparison_result="above" if portfolio_cap_rate >= industry_cap_rate else "below"
            ))
            
            # Cash-on-Cash Return Benchmark
            portfolio_coc = portfolio_performance.get("average_coc_return", 0)
            industry_coc = self._calculate_weighted_benchmark(
                property_type_distribution,
                self.industry_benchmarks[PerformanceMetric.COC_RETURN]
            )
            
            benchmarks.append(PerformanceBenchmark(
                metric_name="coc_return",
                portfolio_value=portfolio_coc,
                benchmark_value=industry_coc,
                percentile_rank=self._calculate_percentile_rank(portfolio_coc, industry_coc),
                comparison_result="above" if portfolio_coc >= industry_coc else "below"
            ))
            
            # ROI Benchmark
            portfolio_roi = portfolio_performance.get("average_roi", 0)
            industry_roi = self._calculate_weighted_benchmark(
                property_type_distribution,
                self.industry_benchmarks[PerformanceMetric.ROI]
            )
            
            benchmarks.append(PerformanceBenchmark(
                metric_name="roi",
                portfolio_value=portfolio_roi,
                benchmark_value=industry_roi,
                percentile_rank=self._calculate_percentile_rank(portfolio_roi, industry_roi),
                comparison_result="above" if portfolio_roi >= industry_roi else "below"
            ))
            
            return {
                "benchmark_type": "industry_average",
                "benchmarks": [b.dict() for b in benchmarks],
                "property_type_distribution": property_type_distribution,
                "overall_score": self._calculate_benchmark_score(benchmarks)
            }
            
        except Exception as e:
            logger.error(f"Error benchmarking against industry: {str(e)}")
            return {"benchmark_type": "industry_average", "error": str(e)}
    
    def _benchmark_against_peers(self, portfolio_performance: Dict[str, Any], 
                               portfolio_id: uuid.UUID) -> Dict[str, Any]:
        """Benchmark against peer portfolios."""
        try:
            # Get peer portfolios (similar size and strategy)
            peer_portfolios = self._find_peer_portfolios(portfolio_id)
            
            if not peer_portfolios:
                return {
                    "benchmark_type": "peer_portfolio",
                    "message": "No peer portfolios found for comparison"
                }
            
            # Calculate peer performance metrics
            peer_metrics = self._calculate_peer_metrics(peer_portfolios)
            
            benchmarks = []
            
            # Compare key metrics
            metrics_to_compare = [
                ("average_cap_rate", "cap_rate"),
                ("average_coc_return", "coc_return"),
                ("average_roi", "roi"),
                ("portfolio_roi", "total_roi")
            ]
            
            for portfolio_key, benchmark_key in metrics_to_compare:
                portfolio_value = portfolio_performance.get(portfolio_key, 0)
                peer_median = peer_metrics.get(f"median_{benchmark_key}", 0)
                
                benchmarks.append(PerformanceBenchmark(
                    metric_name=benchmark_key,
                    portfolio_value=portfolio_value,
                    benchmark_value=peer_median,
                    percentile_rank=self._calculate_peer_percentile(
                        portfolio_value, peer_metrics.get(f"all_{benchmark_key}", [])
                    ),
                    comparison_result="above" if portfolio_value >= peer_median else "below"
                ))
            
            return {
                "benchmark_type": "peer_portfolio",
                "benchmarks": [b.dict() for b in benchmarks],
                "peer_count": len(peer_portfolios),
                "peer_metrics": peer_metrics,
                "overall_score": self._calculate_benchmark_score(benchmarks)
            }
            
        except Exception as e:
            logger.error(f"Error benchmarking against peers: {str(e)}")
            return {"benchmark_type": "peer_portfolio", "error": str(e)}
    
    def _benchmark_against_history(self, portfolio_performance: Dict[str, Any], 
                                 portfolio_id: uuid.UUID) -> Dict[str, Any]:
        """Benchmark against historical performance."""
        try:
            # Get historical performance data
            historical_data = self._get_historical_performance_data(portfolio_id)
            
            if not historical_data:
                return {
                    "benchmark_type": "historical_performance",
                    "message": "Insufficient historical data for comparison"
                }
            
            benchmarks = []
            
            # Compare current performance to historical averages
            current_metrics = {
                "cap_rate": portfolio_performance.get("average_cap_rate", 0),
                "coc_return": portfolio_performance.get("average_coc_return", 0),
                "roi": portfolio_performance.get("average_roi", 0),
                "cash_flow": portfolio_performance.get("net_cash_flow", 0)
            }
            
            for metric, current_value in current_metrics.items():
                historical_values = [record.get(metric, 0) for record in historical_data]
                historical_avg = mean(historical_values) if historical_values else 0
                
                benchmarks.append(PerformanceBenchmark(
                    metric_name=metric,
                    portfolio_value=current_value,
                    benchmark_value=historical_avg,
                    percentile_rank=self._calculate_historical_percentile(current_value, historical_values),
                    comparison_result="above" if current_value >= historical_avg else "below"
                ))
            
            return {
                "benchmark_type": "historical_performance",
                "benchmarks": [b.dict() for b in benchmarks],
                "historical_periods": len(historical_data),
                "trend_analysis": self._analyze_performance_trends(historical_data),
                "overall_score": self._calculate_benchmark_score(benchmarks)
            }
            
        except Exception as e:
            logger.error(f"Error benchmarking against history: {str(e)}")
            return {"benchmark_type": "historical_performance", "error": str(e)}
    
    def _benchmark_against_geography(self, portfolio_performance: Dict[str, Any], 
                                   portfolio_id: uuid.UUID) -> Dict[str, Any]:
        """Benchmark against geographic market averages."""
        try:
            # Get geographic distribution of portfolio
            geographic_distribution = self._get_geographic_distribution(portfolio_id)
            
            benchmarks = []
            
            for market, percentage in geographic_distribution.items():
                if market in self.geographic_benchmarks:
                    market_benchmarks = self.geographic_benchmarks[market]
                    
                    for metric, benchmark_value in market_benchmarks.items():
                        portfolio_value = portfolio_performance.get(f"average_{metric.value}", 0)
                        
                        benchmarks.append(PerformanceBenchmark(
                            metric_name=f"{market}_{metric.value}",
                            portfolio_value=portfolio_value,
                            benchmark_value=benchmark_value,
                            percentile_rank=self._calculate_percentile_rank(portfolio_value, benchmark_value),
                            comparison_result="above" if portfolio_value >= benchmark_value else "below"
                        ))
            
            return {
                "benchmark_type": "geographic_market",
                "benchmarks": [b.dict() for b in benchmarks],
                "geographic_distribution": geographic_distribution,
                "overall_score": self._calculate_benchmark_score(benchmarks)
            }
            
        except Exception as e:
            logger.error(f"Error benchmarking against geography: {str(e)}")
            return {"benchmark_type": "geographic_market", "error": str(e)}
    
    def _benchmark_against_property_type(self, portfolio_performance: Dict[str, Any], 
                                       portfolio_id: uuid.UUID) -> Dict[str, Any]:
        """Benchmark against property type averages."""
        try:
            # Get property type distribution
            property_type_distribution = self._get_property_type_distribution(portfolio_id)
            
            benchmarks = []
            
            for prop_type, percentage in property_type_distribution.items():
                if prop_type in self.industry_benchmarks[PerformanceMetric.CAP_RATE]:
                    # Benchmark cap rate for this property type
                    portfolio_cap_rate = portfolio_performance.get("average_cap_rate", 0)
                    type_benchmark = self.industry_benchmarks[PerformanceMetric.CAP_RATE][prop_type]
                    
                    benchmarks.append(PerformanceBenchmark(
                        metric_name=f"{prop_type}_cap_rate",
                        portfolio_value=portfolio_cap_rate,
                        benchmark_value=type_benchmark,
                        percentile_rank=self._calculate_percentile_rank(portfolio_cap_rate, type_benchmark),
                        comparison_result="above" if portfolio_cap_rate >= type_benchmark else "below"
                    ))
            
            return {
                "benchmark_type": "property_type",
                "benchmarks": [b.dict() for b in benchmarks],
                "property_type_distribution": property_type_distribution,
                "overall_score": self._calculate_benchmark_score(benchmarks)
            }
            
        except Exception as e:
            logger.error(f"Error benchmarking against property type: {str(e)}")
            return {"benchmark_type": "property_type", "error": str(e)}
    
    def _get_property_type_distribution(self, portfolio_id: uuid.UUID) -> Dict[str, float]:
        """Get the distribution of property types in a portfolio."""
        try:
            # Get portfolio properties
            portfolio_properties = self.db.query(PortfolioPropertyDB).filter(
                PortfolioPropertyDB.portfolio_id == portfolio_id
            ).all()
            
            if not portfolio_properties:
                return {}
            
            # Get property details
            from app.models.property import PropertyDB
            property_ids = [prop.property_id for prop in portfolio_properties]
            properties = self.db.query(PropertyDB).filter(PropertyDB.id.in_(property_ids)).all()
            
            # Calculate distribution
            type_counts = {}
            for prop in properties:
                prop_type = getattr(prop, 'property_type', 'unknown')
                type_counts[prop_type] = type_counts.get(prop_type, 0) + 1
            
            total_properties = len(properties)
            return {
                prop_type: count / total_properties * 100 
                for prop_type, count in type_counts.items()
            }
            
        except Exception as e:
            logger.error(f"Error getting property type distribution: {str(e)}")
            return {}
    
    def _get_geographic_distribution(self, portfolio_id: uuid.UUID) -> Dict[str, float]:
        """Get the geographic distribution of properties in a portfolio."""
        try:
            # Get portfolio properties
            portfolio_properties = self.db.query(PortfolioPropertyDB).filter(
                PortfolioPropertyDB.portfolio_id == portfolio_id
            ).all()
            
            if not portfolio_properties:
                return {}
            
            # Get property details
            from app.models.property import PropertyDB
            property_ids = [prop.property_id for prop in portfolio_properties]
            properties = self.db.query(PropertyDB).filter(PropertyDB.id.in_(property_ids)).all()
            
            # Calculate distribution by city
            city_counts = {}
            for prop in properties:
                city = getattr(prop, 'city', 'unknown')
                city_counts[city] = city_counts.get(city, 0) + 1
            
            total_properties = len(properties)
            return {
                city: count / total_properties * 100 
                for city, count in city_counts.items()
            }
            
        except Exception as e:
            logger.error(f"Error getting geographic distribution: {str(e)}")
            return {}
    
    def _calculate_weighted_benchmark(self, distribution: Dict[str, float], 
                                    benchmarks: Dict[str, float]) -> float:
        """Calculate a weighted benchmark based on distribution."""
        weighted_sum = 0
        total_weight = 0
        
        for category, percentage in distribution.items():
            if category in benchmarks:
                weighted_sum += benchmarks[category] * (percentage / 100)
                total_weight += percentage / 100
        
        # Use overall benchmark if no specific categories match
        if total_weight == 0 and "overall" in benchmarks:
            return benchmarks["overall"]
        
        return weighted_sum / total_weight if total_weight > 0 else 0
    
    def _calculate_percentile_rank(self, portfolio_value: float, benchmark_value: float) -> float:
        """Calculate percentile rank compared to benchmark."""
        if benchmark_value == 0:
            return 50.0
        
        ratio = portfolio_value / benchmark_value
        
        if ratio >= 1.2:
            return 90.0
        elif ratio >= 1.1:
            return 80.0
        elif ratio >= 1.0:
            return 70.0
        elif ratio >= 0.9:
            return 50.0
        elif ratio >= 0.8:
            return 30.0
        else:
            return 10.0
    
    def _find_peer_portfolios(self, portfolio_id: uuid.UUID) -> List[PortfolioDB]:
        """Find peer portfolios for comparison."""
        try:
            # Get the target portfolio
            target_portfolio = self.db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
            if not target_portfolio:
                return []
            
            # Find portfolios with similar characteristics
            peer_portfolios = self.db.query(PortfolioDB).filter(
                and_(
                    PortfolioDB.id != portfolio_id,
                    PortfolioDB.status == "active",
                    # Similar property count (within 50%)
                    PortfolioDB.total_properties >= target_portfolio.total_properties * 0.5,
                    PortfolioDB.total_properties <= target_portfolio.total_properties * 1.5,
                    # Similar investment strategy
                    PortfolioDB.investment_strategy == target_portfolio.investment_strategy
                )
            ).limit(20).all()
            
            return peer_portfolios
            
        except Exception as e:
            logger.error(f"Error finding peer portfolios: {str(e)}")
            return []
    
    def _calculate_peer_metrics(self, peer_portfolios: List[PortfolioDB]) -> Dict[str, Any]:
        """Calculate aggregate metrics for peer portfolios."""
        try:
            metrics = {
                "cap_rate": [],
                "coc_return": [],
                "roi": [],
                "total_roi": []
            }
            
            for portfolio in peer_portfolios:
                metrics["cap_rate"].append(portfolio.average_cap_rate or 0)
                metrics["coc_return"].append(portfolio.average_coc_return or 0)
                metrics["roi"].append(portfolio.average_roi or 0)
                metrics["total_roi"].append(portfolio.total_return_ytd or 0)
            
            # Calculate statistics
            peer_metrics = {}
            for metric, values in metrics.items():
                if values:
                    peer_metrics[f"median_{metric}"] = median(values)
                    peer_metrics[f"mean_{metric}"] = mean(values)
                    peer_metrics[f"std_{metric}"] = stdev(values) if len(values) > 1 else 0
                    peer_metrics[f"all_{metric}"] = values
                else:
                    peer_metrics[f"median_{metric}"] = 0
                    peer_metrics[f"mean_{metric}"] = 0
                    peer_metrics[f"std_{metric}"] = 0
                    peer_metrics[f"all_{metric}"] = []
            
            return peer_metrics
            
        except Exception as e:
            logger.error(f"Error calculating peer metrics: {str(e)}")
            return {}
    
    def _calculate_peer_percentile(self, portfolio_value: float, peer_values: List[float]) -> float:
        """Calculate percentile rank among peers."""
        if not peer_values:
            return 50.0
        
        sorted_values = sorted(peer_values)
        rank = sum(1 for value in sorted_values if value <= portfolio_value)
        
        return (rank / len(sorted_values)) * 100
    
    def _get_historical_performance_data(self, portfolio_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get historical performance data for a portfolio."""
        try:
            from app.models.portfolio import PortfolioPerformanceDB
            
            # Get historical performance records
            historical_records = self.db.query(PortfolioPerformanceDB).filter(
                and_(
                    PortfolioPerformanceDB.portfolio_id == portfolio_id,
                    PortfolioPerformanceDB.period_type == "monthly"
                )
            ).order_by(PortfolioPerformanceDB.period_start.desc()).limit(24).all()
            
            return [
                {
                    "period": record.period_start.strftime("%Y-%m"),
                    "cap_rate": record.average_cap_rate or 0,
                    "coc_return": record.average_coc_return or 0,
                    "roi": record.average_roi or 0,
                    "cash_flow": record.net_cash_flow or 0,
                    "total_return": record.total_return or 0
                }
                for record in historical_records
            ]
            
        except Exception as e:
            logger.error(f"Error getting historical performance data: {str(e)}")
            return []
    
    def _calculate_historical_percentile(self, current_value: float, historical_values: List[float]) -> float:
        """Calculate percentile rank compared to historical performance."""
        if not historical_values:
            return 50.0
        
        sorted_values = sorted(historical_values)
        rank = sum(1 for value in sorted_values if value <= current_value)
        
        return (rank / len(sorted_values)) * 100
    
    def _analyze_performance_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance trends from historical data."""
        if len(historical_data) < 3:
            return {"trend": "insufficient_data"}
        
        # Analyze cap rate trend
        cap_rates = [record["cap_rate"] for record in historical_data[-6:]]  # Last 6 months
        cap_rate_trend = "improving" if cap_rates[-1] > cap_rates[0] else "declining"
        
        # Analyze cash flow trend
        cash_flows = [record["cash_flow"] for record in historical_data[-6:]]
        cash_flow_trend = "improving" if cash_flows[-1] > cash_flows[0] else "declining"
        
        return {
            "cap_rate_trend": cap_rate_trend,
            "cash_flow_trend": cash_flow_trend,
            "data_points": len(historical_data)
        }
    
    def _calculate_benchmark_score(self, benchmarks: List[PerformanceBenchmark]) -> float:
        """Calculate an overall benchmark score."""
        if not benchmarks:
            return 50.0
        
        total_percentile = sum(b.percentile_rank for b in benchmarks)
        return total_percentile / len(benchmarks)
    
    def _calculate_overall_ranking(self, benchmarks: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall ranking across all benchmarks."""
        scores = []
        
        for benchmark_type, benchmark_data in benchmarks.items():
            if isinstance(benchmark_data, dict) and "overall_score" in benchmark_data:
                scores.append(benchmark_data["overall_score"])
        
        if not scores:
            return {"overall_score": 50.0, "ranking": "average"}
        
        overall_score = mean(scores)
        
        if overall_score >= 80:
            ranking = "excellent"
        elif overall_score >= 70:
            ranking = "above_average"
        elif overall_score >= 50:
            ranking = "average"
        elif overall_score >= 30:
            ranking = "below_average"
        else:
            ranking = "poor"
        
        return {
            "overall_score": overall_score,
            "ranking": ranking,
            "benchmark_count": len(scores)
        }
    
    def _generate_performance_summary(self, benchmarks: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a performance summary based on benchmarks."""
        strengths = []
        weaknesses = []
        recommendations = []
        
        for benchmark_type, benchmark_data in benchmarks.items():
            if isinstance(benchmark_data, dict) and "benchmarks" in benchmark_data:
                for benchmark in benchmark_data["benchmarks"]:
                    if benchmark["comparison_result"] == "above":
                        strengths.append(f"{benchmark['metric_name']}: {benchmark['portfolio_value']:.2f} vs {benchmark['benchmark_value']:.2f} benchmark")
                    else:
                        weaknesses.append(f"{benchmark['metric_name']}: {benchmark['portfolio_value']:.2f} vs {benchmark['benchmark_value']:.2f} benchmark")
                        recommendations.append(f"Consider strategies to improve {benchmark['metric_name']}")
        
        return {
            "strengths": strengths[:5],  # Top 5 strengths
            "weaknesses": weaknesses[:5],  # Top 5 weaknesses
            "recommendations": recommendations[:3]  # Top 3 recommendations
        }


def get_performance_benchmarking_service(db: Session = None) -> PerformanceBenchmarkingService:
    """Factory function to get PerformanceBenchmarkingService instance."""
    if db is None:
        db = next(get_db())
    return PerformanceBenchmarkingService(db)