"""
Unit tests for Performance Benchmarking Service.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.performance_benchmarking_service import (
    PerformanceBenchmarkingService, BenchmarkType, PerformanceMetric
)
from app.models.portfolio import PortfolioDB, PortfolioPropertyDB, PerformanceBenchmark


class TestPerformanceBenchmarkingService:
    """Test cases for PerformanceBenchmarkingService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_performance_service(self):
        """Create a mock performance service."""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_db, mock_performance_service):
        """Create a PerformanceBenchmarkingService instance."""
        service = PerformanceBenchmarkingService(mock_db)
        service.performance_service = mock_performance_service
        return service
    
    @pytest.fixture
    def sample_portfolio(self):
        """Create a sample portfolio."""
        return PortfolioDB(
            id=uuid.uuid4(),
            name="Test Portfolio",
            status="active",
            total_properties=3,
            average_cap_rate=6.8,
            average_coc_return=9.2,
            average_roi=13.5
        )
    
    @pytest.fixture
    def sample_portfolio_performance(self):
        """Create sample portfolio performance data."""
        return {
            "average_cap_rate": 7.2,
            "average_coc_return": 9.8,
            "average_roi": 14.5,
            "net_cash_flow": 3600.0,
            "total_value": 850000.0
        }
    
    def test_benchmark_portfolio_performance(self, service, mock_db, sample_portfolio, 
                                           sample_portfolio_performance, mock_performance_service):
        """Test benchmarking portfolio performance."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = sample_portfolio
        mock_performance_service.calculate_portfolio_performance.return_value = sample_portfolio_performance
        
        # Mock helper methods
        service._get_property_type_distribution = Mock(return_value={"single_family": 100.0})
        service._find_peer_portfolios = Mock(return_value=[])
        service._get_historical_performance_data = Mock(return_value=[])
        
        # Test
        result = service.benchmark_portfolio_performance(
            sample_portfolio.id,
            [BenchmarkType.INDUSTRY_AVERAGE]
        )
        
        # Assertions
        assert result["portfolio_id"] == sample_portfolio.id
        assert result["portfolio_name"] == sample_portfolio.name
        assert "benchmark_date" in result
        assert "portfolio_performance" in result
        assert "benchmarks" in result
        assert "overall_ranking" in result
        assert "performance_summary" in result
        
        # Check industry benchmark
        assert "industry_average" in result["benchmarks"]
        industry_benchmark = result["benchmarks"]["industry_average"]
        assert "benchmarks" in industry_benchmark
        assert "overall_score" in industry_benchmark
    
    def test_benchmark_against_industry(self, service, mock_db, sample_portfolio_performance):
        """Test benchmarking against industry averages."""
        # Mock property type distribution
        service._get_property_type_distribution = Mock(return_value={"single_family": 100.0})
        
        # Test
        result = service._benchmark_against_industry(sample_portfolio_performance, uuid.uuid4())
        
        # Assertions
        assert result["benchmark_type"] == "industry_average"
        assert "benchmarks" in result
        assert "property_type_distribution" in result
        assert "overall_score" in result
        
        benchmarks = result["benchmarks"]
        assert len(benchmarks) >= 3  # cap_rate, coc_return, roi
        
        # Check benchmark structure
        for benchmark in benchmarks:
            assert "metric_name" in benchmark
            assert "portfolio_value" in benchmark
            assert "benchmark_value" in benchmark
            assert "percentile_rank" in benchmark
            assert "comparison_result" in benchmark
    
    def test_benchmark_against_peers(self, service, mock_db, sample_portfolio_performance):
        """Test benchmarking against peer portfolios."""
        # Create mock peer portfolios
        peer_portfolios = [
            PortfolioDB(
                id=uuid.uuid4(),
                name="Peer 1",
                average_cap_rate=6.5,
                average_coc_return=8.8,
                average_roi=12.0,
                total_return_ytd=11.5
            ),
            PortfolioDB(
                id=uuid.uuid4(),
                name="Peer 2",
                average_cap_rate=7.0,
                average_coc_return=9.5,
                average_roi=13.8,
                total_return_ytd=13.2
            )
        ]
        
        # Mock peer finding
        service._find_peer_portfolios = Mock(return_value=peer_portfolios)
        
        # Test
        result = service._benchmark_against_peers(sample_portfolio_performance, uuid.uuid4())
        
        # Assertions
        assert result["benchmark_type"] == "peer_portfolio"
        assert "benchmarks" in result
        assert "peer_count" in result
        assert "peer_metrics" in result
        assert "overall_score" in result
        
        assert result["peer_count"] == 2
        
        benchmarks = result["benchmarks"]
        assert len(benchmarks) > 0
        
        # Check peer metrics calculation
        peer_metrics = result["peer_metrics"]
        assert "median_cap_rate" in peer_metrics
        assert "mean_cap_rate" in peer_metrics
        assert "std_cap_rate" in peer_metrics
    
    def test_benchmark_against_history(self, service, mock_db, sample_portfolio_performance):
        """Test benchmarking against historical performance."""
        # Create mock historical data
        historical_data = [
            {
                "period": "2023-01",
                "cap_rate": 6.0,
                "coc_return": 8.5,
                "roi": 12.0,
                "cash_flow": 3000.0
            },
            {
                "period": "2023-02",
                "cap_rate": 6.2,
                "coc_return": 8.8,
                "roi": 12.5,
                "cash_flow": 3200.0
            },
            {
                "period": "2023-03",
                "cap_rate": 6.5,
                "coc_return": 9.0,
                "roi": 13.0,
                "cash_flow": 3400.0
            }
        ]
        
        # Mock historical data retrieval
        service._get_historical_performance_data = Mock(return_value=historical_data)
        
        # Test
        result = service._benchmark_against_history(sample_portfolio_performance, uuid.uuid4())
        
        # Assertions
        assert result["benchmark_type"] == "historical_performance"
        assert "benchmarks" in result
        assert "historical_periods" in result
        assert "trend_analysis" in result
        assert "overall_score" in result
        
        assert result["historical_periods"] == 3
        
        benchmarks = result["benchmarks"]
        assert len(benchmarks) > 0
        
        # Check trend analysis
        trend_analysis = result["trend_analysis"]
        assert "cap_rate_trend" in trend_analysis
        assert "cash_flow_trend" in trend_analysis
    
    def test_calculate_percentile_rank(self, service, mock_db):
        """Test percentile rank calculation."""
        # Test portfolio above benchmark
        percentile = service._calculate_percentile_rank(7.5, 6.0)
        assert percentile > 50.0
        
        # Test portfolio at benchmark
        percentile = service._calculate_percentile_rank(6.0, 6.0)
        assert percentile == 70.0
        
        # Test portfolio below benchmark
        percentile = service._calculate_percentile_rank(4.5, 6.0)
        assert percentile < 50.0
        
        # Test with zero benchmark
        percentile = service._calculate_percentile_rank(5.0, 0.0)
        assert percentile == 50.0
    
    def test_calculate_weighted_benchmark(self, service, mock_db):
        """Test weighted benchmark calculation."""
        distribution = {
            "single_family": 60.0,
            "multi_family": 40.0
        }
        
        benchmarks = {
            "single_family": 6.5,
            "multi_family": 7.2,
            "overall": 6.8
        }
        
        weighted_benchmark = service._calculate_weighted_benchmark(distribution, benchmarks)
        
        # Expected: (6.5 * 0.6) + (7.2 * 0.4) = 3.9 + 2.88 = 6.78
        expected = 6.78
        assert abs(weighted_benchmark - expected) < 0.01
    
    def test_calculate_weighted_benchmark_no_match(self, service, mock_db):
        """Test weighted benchmark calculation with no matching categories."""
        distribution = {
            "unknown_type": 100.0
        }
        
        benchmarks = {
            "single_family": 6.5,
            "multi_family": 7.2,
            "overall": 6.8
        }
        
        weighted_benchmark = service._calculate_weighted_benchmark(distribution, benchmarks)
        
        # Should fall back to overall benchmark
        assert weighted_benchmark == 6.8
    
    def test_find_peer_portfolios(self, service, mock_db):
        """Test finding peer portfolios."""
        # Create target portfolio
        target_portfolio = PortfolioDB(
            id=uuid.uuid4(),
            name="Target Portfolio",
            total_properties=5,
            investment_strategy="buy_and_hold",
            status="active"
        )
        
        # Create potential peer portfolios
        peer1 = PortfolioDB(
            id=uuid.uuid4(),
            name="Peer 1",
            total_properties=4,  # Within 50% range
            investment_strategy="buy_and_hold",
            status="active"
        )
        
        peer2 = PortfolioDB(
            id=uuid.uuid4(),
            name="Peer 2",
            total_properties=7,  # Within 50% range
            investment_strategy="buy_and_hold",
            status="active"
        )
        
        non_peer = PortfolioDB(
            id=uuid.uuid4(),
            name="Non-Peer",
            total_properties=15,  # Outside range
            investment_strategy="buy_and_hold",
            status="active"
        )
        
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = target_portfolio
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [peer1, peer2]
        
        # Test
        peers = service._find_peer_portfolios(target_portfolio.id)
        
        # Assertions
        assert len(peers) == 2
        assert peer1 in peers
        assert peer2 in peers
    
    def test_calculate_peer_metrics(self, service, mock_db):
        """Test peer metrics calculation."""
        peer_portfolios = [
            PortfolioDB(
                id=uuid.uuid4(),
                average_cap_rate=6.0,
                average_coc_return=8.0,
                average_roi=12.0,
                total_return_ytd=10.0
            ),
            PortfolioDB(
                id=uuid.uuid4(),
                average_cap_rate=7.0,
                average_coc_return=9.0,
                average_roi=14.0,
                total_return_ytd=12.0
            ),
            PortfolioDB(
                id=uuid.uuid4(),
                average_cap_rate=8.0,
                average_coc_return=10.0,
                average_roi=16.0,
                total_return_ytd=14.0
            )
        ]
        
        # Test
        metrics = service._calculate_peer_metrics(peer_portfolios)
        
        # Assertions
        assert "median_cap_rate" in metrics
        assert "mean_cap_rate" in metrics
        assert "std_cap_rate" in metrics
        assert "all_cap_rate" in metrics
        
        # Check median calculation
        assert metrics["median_cap_rate"] == 7.0  # Middle value
        
        # Check mean calculation
        assert metrics["mean_cap_rate"] == 7.0  # (6+7+8)/3
        
        # Check that all values are stored
        assert len(metrics["all_cap_rate"]) == 3
    
    def test_calculate_peer_percentile(self, service, mock_db):
        """Test peer percentile calculation."""
        peer_values = [5.0, 6.0, 7.0, 8.0, 9.0]
        
        # Test portfolio at median
        percentile = service._calculate_peer_percentile(7.0, peer_values)
        assert percentile == 60.0  # 3 out of 5 values are <= 7.0
        
        # Test portfolio at top
        percentile = service._calculate_peer_percentile(10.0, peer_values)
        assert percentile == 100.0  # All values are <= 10.0
        
        # Test portfolio at bottom
        percentile = service._calculate_peer_percentile(4.0, peer_values)
        assert percentile == 0.0  # No values are <= 4.0
        
        # Test with empty peer values
        percentile = service._calculate_peer_percentile(7.0, [])
        assert percentile == 50.0
    
    def test_get_property_type_distribution(self, service, mock_db):
        """Test property type distribution calculation."""
        portfolio_id = uuid.uuid4()
        
        # Create mock portfolio properties
        portfolio_properties = [
            PortfolioPropertyDB(id=uuid.uuid4(), property_id=uuid.uuid4()),
            PortfolioPropertyDB(id=uuid.uuid4(), property_id=uuid.uuid4()),
            PortfolioPropertyDB(id=uuid.uuid4(), property_id=uuid.uuid4())
        ]
        
        # Create mock properties with types
        from app.models.property import PropertyDB
        properties = [
            Mock(property_type="single_family"),
            Mock(property_type="single_family"),
            Mock(property_type="multi_family")
        ]
        
        # Setup mocks
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            portfolio_properties,  # First call for portfolio properties
            properties  # Second call for property details
        ]
        
        # Test
        distribution = service._get_property_type_distribution(portfolio_id)
        
        # Assertions
        assert "single_family" in distribution
        assert "multi_family" in distribution
        assert abs(distribution["single_family"] - 66.67) < 0.1  # 2/3 * 100
        assert abs(distribution["multi_family"] - 33.33) < 0.1   # 1/3 * 100
    
    def test_calculate_benchmark_score(self, service, mock_db):
        """Test benchmark score calculation."""
        benchmarks = [
            PerformanceBenchmark(
                metric_name="cap_rate",
                portfolio_value=7.0,
                benchmark_value=6.0,
                percentile_rank=80.0,
                comparison_result="above"
            ),
            PerformanceBenchmark(
                metric_name="coc_return",
                portfolio_value=8.0,
                benchmark_value=9.0,
                percentile_rank=60.0,
                comparison_result="below"
            ),
            PerformanceBenchmark(
                metric_name="roi",
                portfolio_value=12.0,
                benchmark_value=11.0,
                percentile_rank=70.0,
                comparison_result="above"
            )
        ]
        
        # Test
        score = service._calculate_benchmark_score(benchmarks)
        
        # Expected: (80 + 60 + 70) / 3 = 70.0
        assert score == 70.0
    
    def test_calculate_overall_ranking(self, service, mock_db):
        """Test overall ranking calculation."""
        benchmarks = {
            "industry_average": {"overall_score": 75.0},
            "peer_portfolio": {"overall_score": 85.0},
            "historical_performance": {"overall_score": 65.0}
        }
        
        # Test
        ranking = service._calculate_overall_ranking(benchmarks)
        
        # Assertions
        assert "overall_score" in ranking
        assert "ranking" in ranking
        assert "benchmark_count" in ranking
        
        # Expected score: (75 + 85 + 65) / 3 = 75.0
        assert ranking["overall_score"] == 75.0
        assert ranking["ranking"] == "above_average"  # 75 is above average
        assert ranking["benchmark_count"] == 3
    
    def test_generate_performance_summary(self, service, mock_db):
        """Test performance summary generation."""
        benchmarks = {
            "industry_average": {
                "benchmarks": [
                    {
                        "metric_name": "cap_rate",
                        "portfolio_value": 7.5,
                        "benchmark_value": 6.5,
                        "comparison_result": "above"
                    },
                    {
                        "metric_name": "coc_return",
                        "portfolio_value": 8.0,
                        "benchmark_value": 9.0,
                        "comparison_result": "below"
                    }
                ]
            }
        }
        
        # Test
        summary = service._generate_performance_summary(benchmarks)
        
        # Assertions
        assert "strengths" in summary
        assert "weaknesses" in summary
        assert "recommendations" in summary
        
        # Check that strengths and weaknesses are identified
        assert len(summary["strengths"]) > 0
        assert len(summary["weaknesses"]) > 0
        assert len(summary["recommendations"]) > 0
        
        # Check content
        assert any("cap_rate" in strength for strength in summary["strengths"])
        assert any("coc_return" in weakness for weakness in summary["weaknesses"])


if __name__ == "__main__":
    pytest.main([__file__])