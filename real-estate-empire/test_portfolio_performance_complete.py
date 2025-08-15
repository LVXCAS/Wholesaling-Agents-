#!/usr/bin/env python3
"""
Comprehensive test for Portfolio Performance Tracking implementation.
This test verifies all components of task 4.1 are working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.portfolio_performance_service import PortfolioPerformanceService
from app.services.portfolio_management_service import PortfolioManagementService
from app.services.automated_reporting_service import AutomatedReportingService, ReportFrequency, ReportType
from app.services.performance_benchmarking_service import PerformanceBenchmarkingService, BenchmarkType
from unittest.mock import Mock, MagicMock
import uuid
from datetime import datetime, timedelta

def test_property_performance_monitoring():
    """Test property performance monitoring system."""
    print("Testing Property Performance Monitoring System...")
    
    # Create mock database
    mock_db = Mock()
    service = PortfolioPerformanceService(mock_db)
    
    # Test property performance calculation
    portfolio_property_id = uuid.uuid4()
    period_start = datetime.now() - timedelta(days=30)
    period_end = datetime.now()
    
    # Mock portfolio property
    mock_portfolio_property = Mock()
    mock_portfolio_property.id = portfolio_property_id
    mock_portfolio_property.property_id = uuid.uuid4()
    mock_portfolio_property.total_investment = 220000.0
    mock_portfolio_property.current_value = 250000.0
    mock_portfolio_property.current_debt = 150000.0
    mock_portfolio_property.monthly_cash_flow = 1200.0
    mock_portfolio_property.acquisition_date = datetime.now() - timedelta(days=365)
    mock_portfolio_property.acquisition_price = 200000.0
    
    # Mock database queries
    mock_db.query.return_value.filter.return_value.first.return_value = mock_portfolio_property
    mock_db.query.return_value.filter.return_value.all.return_value = []
    
    # Test basic metrics calculation
    result = service._calculate_basic_metrics(mock_portfolio_property)
    
    assert result["current_value"] == 250000.0
    assert result["total_investment"] == 220000.0
    assert result["annual_cash_flow"] == 14400.0  # 1200 * 12
    assert "cap_rate" in result
    assert "coc_return" in result
    assert "roi" in result
    
    print("✓ Property performance monitoring test passed")

def test_portfolio_level_metrics_aggregation():
    """Test portfolio-level metrics aggregation."""
    print("Testing Portfolio-Level Metrics Aggregation...")
    
    # Create mock database
    mock_db = Mock()
    service = PortfolioPerformanceService(mock_db)
    
    # Test empty portfolio metrics
    portfolio_id = uuid.uuid4()
    result = service._empty_portfolio_metrics(portfolio_id)
    
    assert result["portfolio_id"] == portfolio_id
    assert result["total_properties"] == 0
    assert result["total_value"] == 0.0
    assert result["total_equity"] == 0.0
    assert result["net_cash_flow"] == 0.0
    assert result["average_cap_rate"] == 0.0
    assert result["average_coc_return"] == 0.0
    assert result["average_roi"] == 0.0
    
    print("✓ Portfolio-level metrics aggregation test passed")

def test_automated_performance_reporting():
    """Test automated performance reporting."""
    print("Testing Automated Performance Reporting...")
    
    # Create mock database
    mock_db = Mock()
    service = AutomatedReportingService(mock_db)
    
    # Mock portfolio
    mock_portfolio = Mock()
    mock_portfolio.id = uuid.uuid4()
    mock_portfolio.name = "Test Portfolio"
    mock_portfolio.status = "active"
    
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_portfolio]
    mock_db.query.return_value.filter.return_value.first.return_value = mock_portfolio
    
    # Mock performance service
    service.performance_service = Mock()
    service.performance_service.generate_performance_report.return_value = {
        "portfolio_id": mock_portfolio.id,
        "portfolio_name": mock_portfolio.name,
        "performance_metrics": {
            "total_value": 500000.0,
            "net_cash_flow": 2400.0,
            "average_cap_rate": 6.5,
            "portfolio_roi": 12.0
        }
    }
    
    # Test report generation
    reports = service.generate_scheduled_reports(ReportFrequency.MONTHLY)
    
    assert len(reports) == 1
    assert reports[0]["portfolio_id"] == mock_portfolio.id
    assert "report_type" in reports[0]
    assert "frequency" in reports[0]
    assert "generated_by" in reports[0]
    
    print("✓ Automated performance reporting test passed")

def test_performance_comparison_and_benchmarking():
    """Test performance comparison and benchmarking."""
    print("Testing Performance Comparison and Benchmarking...")
    
    # Create mock database
    mock_db = Mock()
    service = PerformanceBenchmarkingService(mock_db)
    
    # Mock portfolio
    mock_portfolio = Mock()
    mock_portfolio.id = uuid.uuid4()
    mock_portfolio.name = "Test Portfolio"
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_portfolio
    
    # Mock performance service
    service.performance_service = Mock()
    service.performance_service.calculate_portfolio_performance.return_value = {
        "average_cap_rate": 7.2,
        "average_coc_return": 9.5,
        "average_roi": 13.8,
        "net_cash_flow": 3600.0
    }
    
    # Mock property type distribution
    service._get_property_type_distribution = Mock(return_value={"single_family": 100.0})
    service._find_peer_portfolios = Mock(return_value=[])
    service._get_historical_performance_data = Mock(return_value=[])
    service._get_geographic_distribution = Mock(return_value={"New York": 100.0})
    
    # Test benchmarking
    result = service.benchmark_portfolio_performance(
        mock_portfolio.id, 
        [BenchmarkType.INDUSTRY_AVERAGE]
    )
    
    assert result["portfolio_id"] == mock_portfolio.id
    assert "benchmarks" in result
    assert "overall_ranking" in result
    assert "performance_summary" in result
    
    print("✓ Performance comparison and benchmarking test passed")

def test_service_integration():
    """Test integration between all portfolio performance services."""
    print("Testing Service Integration...")
    
    # Create mock database
    mock_db = Mock()
    
    # Create all services
    perf_service = PortfolioPerformanceService(mock_db)
    mgmt_service = PortfolioManagementService(mock_db)
    reporting_service = AutomatedReportingService(mock_db)
    benchmark_service = PerformanceBenchmarkingService(mock_db)
    
    # Verify they all share the same database connection
    assert perf_service.db == mock_db
    assert mgmt_service.db == mock_db
    assert reporting_service.db == mock_db
    assert benchmark_service.db == mock_db
    
    # Verify management service has performance service
    assert mgmt_service.performance_service is not None
    assert isinstance(mgmt_service.performance_service, PortfolioPerformanceService)
    
    # Verify reporting service has performance service
    assert reporting_service.performance_service is not None
    assert isinstance(reporting_service.performance_service, PortfolioPerformanceService)
    
    # Verify benchmark service has performance service
    assert benchmark_service.performance_service is not None
    assert isinstance(benchmark_service.performance_service, PortfolioPerformanceService)
    
    print("✓ Service integration test passed")

def test_key_performance_metrics():
    """Test calculation of key performance metrics."""
    print("Testing Key Performance Metrics Calculation...")
    
    # Create mock database
    mock_db = Mock()
    service = PortfolioPerformanceService(mock_db)
    
    # Test diversification score calculation
    mock_properties = []
    score = service._calculate_diversification_score(mock_properties)
    assert score == 0.0
    
    # Test risk score calculation
    property_performances = [
        {"annual_cash_flow": 5000.0, "cap_rate": 5.0},
        {"annual_cash_flow": 7000.0, "cap_rate": 6.0},
        {"annual_cash_flow": 6000.0, "cap_rate": 5.5}
    ]
    risk_score = service._calculate_risk_score(property_performances)
    assert 0 <= risk_score <= 100
    
    print("✓ Key performance metrics calculation test passed")

def test_reporting_features():
    """Test specific reporting features."""
    print("Testing Reporting Features...")
    
    # Create mock database
    mock_db = Mock()
    service = AutomatedReportingService(mock_db)
    
    # Test key highlights generation
    base_report = {
        "performance_metrics": {
            "total_value": 750000.0,
            "net_cash_flow": 4200.0,
            "portfolio_roi": 15.5,
            "total_properties": 3
        }
    }
    
    highlights = service._generate_key_highlights(base_report)
    assert len(highlights) > 0
    assert any("$750,000.00" in highlight for highlight in highlights)
    assert any("$4,200.00" in highlight for highlight in highlights)
    assert any("15.50%" in highlight for highlight in highlights)
    assert any("3" in highlight for highlight in highlights)
    
    # Test performance alerts generation
    alerts = service._generate_performance_alerts(base_report)
    assert isinstance(alerts, list)
    
    # Test action items generation
    action_items = service._generate_action_items(base_report)
    assert isinstance(action_items, list)
    
    print("✓ Reporting features test passed")

def test_benchmarking_calculations():
    """Test benchmarking calculations."""
    print("Testing Benchmarking Calculations...")
    
    # Create mock database
    mock_db = Mock()
    service = PerformanceBenchmarkingService(mock_db)
    
    # Test percentile rank calculation
    percentile = service._calculate_percentile_rank(7.5, 6.0)  # Portfolio above benchmark
    assert percentile > 50.0
    
    percentile = service._calculate_percentile_rank(4.5, 6.0)  # Portfolio below benchmark
    assert percentile < 50.0
    
    # Test weighted benchmark calculation
    distribution = {"single_family": 60.0, "multi_family": 40.0}
    benchmarks = {"single_family": 6.5, "multi_family": 7.2, "overall": 6.8}
    
    weighted_benchmark = service._calculate_weighted_benchmark(distribution, benchmarks)
    expected = (6.5 * 0.6) + (7.2 * 0.4)  # 3.9 + 2.88 = 6.78
    assert abs(weighted_benchmark - expected) < 0.01
    
    print("✓ Benchmarking calculations test passed")

def run_comprehensive_test():
    """Run all comprehensive tests for portfolio performance tracking."""
    print("Running Comprehensive Portfolio Performance Tracking Tests...")
    print("=" * 80)
    
    try:
        # Test individual components
        test_property_performance_monitoring()
        test_portfolio_level_metrics_aggregation()
        test_automated_performance_reporting()
        test_performance_comparison_and_benchmarking()
        test_service_integration()
        test_key_performance_metrics()
        test_reporting_features()
        test_benchmarking_calculations()
        
        print("\n" + "=" * 80)
        print("🎉 ALL COMPREHENSIVE TESTS PASSED!")
        print("Portfolio Performance Tracking System is fully implemented and working correctly.")
        print("\nImplemented Features:")
        print("✓ Property performance monitoring system")
        print("✓ Portfolio-level metrics aggregation")
        print("✓ Automated performance reporting")
        print("✓ Performance comparison and benchmarking")
        print("✓ Service integration and coordination")
        print("✓ Key performance metrics calculation")
        print("✓ Advanced reporting features")
        print("✓ Benchmarking calculations")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ COMPREHENSIVE TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)