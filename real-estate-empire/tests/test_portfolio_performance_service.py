"""
Unit tests for Portfolio Performance Service.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.portfolio_performance_service import PortfolioPerformanceService
from app.models.portfolio import (
    PortfolioDB, PortfolioPropertyDB, PropertyPerformanceDB, PortfolioPerformanceDB
)
from app.models.property import PropertyDB


class TestPortfolioPerformanceService:
    """Test cases for PortfolioPerformanceService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """Create a PortfolioPerformanceService instance."""
        return PortfolioPerformanceService(mock_db)
    
    @pytest.fixture
    def sample_portfolio_property(self):
        """Create a sample portfolio property."""
        return PortfolioPropertyDB(
            id=uuid.uuid4(),
            portfolio_id=uuid.uuid4(),
            property_id=uuid.uuid4(),
            acquisition_date=datetime.now() - timedelta(days=365),
            acquisition_price=200000.0,
            closing_costs=5000.0,
            rehab_costs=15000.0,
            total_investment=220000.0,
            current_value=250000.0,
            current_debt=150000.0,
            monthly_rent=2000.0,
            monthly_expenses=800.0,
            monthly_cash_flow=1200.0
        )
    
    @pytest.fixture
    def sample_performance_records(self, sample_portfolio_property):
        """Create sample performance records."""
        return [
            PropertyPerformanceDB(
                id=uuid.uuid4(),
                portfolio_property_id=sample_portfolio_property.id,
                period_start=datetime.now() - timedelta(days=30),
                period_end=datetime.now(),
                period_type="monthly",
                rental_income=2000.0,
                other_income=0.0,
                total_income=2000.0,
                mortgage_payment=800.0,
                property_taxes=200.0,
                insurance=100.0,
                maintenance_repairs=150.0,
                property_management=100.0,
                utilities=50.0,
                other_expenses=0.0,
                total_expenses=1400.0,
                net_cash_flow=600.0,
                estimated_value=250000.0,
                occupancy_rate=100.0
            )
        ]
    
    def test_calculate_property_performance_with_records(self, service, mock_db, 
                                                       sample_portfolio_property, sample_performance_records):
        """Test calculating property performance with existing records."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = sample_portfolio_property
        mock_db.query.return_value.filter.return_value.all.return_value = sample_performance_records
        
        # Test
        period_start = datetime.now() - timedelta(days=30)
        period_end = datetime.now()
        result = service.calculate_property_performance(sample_portfolio_property.id, period_start, period_end)
        
        # Assertions
        assert result["property_id"] == sample_portfolio_property.property_id
        assert result["total_income"] == 2000.0
        assert result["total_expenses"] == 1400.0
        assert result["net_cash_flow"] == 600.0
        assert result["current_value"] == 250000.0
        assert result["cap_rate"] > 0  # Should calculate a positive cap rate
        assert result["coc_return"] > 0  # Should calculate a positive cash-on-cash return
    
    def test_calculate_property_performance_no_records(self, service, mock_db, sample_portfolio_property):
        """Test calculating property performance with no existing records."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = sample_portfolio_property
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Test
        period_start = datetime.now() - timedelta(days=30)
        period_end = datetime.now()
        result = service.calculate_property_performance(sample_portfolio_property.id, period_start, period_end)
        
        # Assertions
        assert result["property_id"] == sample_portfolio_property.property_id
        assert result["current_value"] == 250000.0
        assert result["annual_cash_flow"] == 14400.0  # 1200 * 12
        assert "cap_rate" in result
        assert "coc_return" in result
        assert "roi" in result
    
    def test_calculate_property_performance_property_not_found(self, service, mock_db):
        """Test calculating property performance when property is not found."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Test
        period_start = datetime.now() - timedelta(days=30)
        period_end = datetime.now()
        
        with pytest.raises(ValueError, match="Portfolio property .* not found"):
            service.calculate_property_performance(uuid.uuid4(), period_start, period_end)
    
    def test_calculate_portfolio_performance(self, service, mock_db, sample_portfolio_property, sample_performance_records):
        """Test calculating portfolio-level performance."""
        # Create sample portfolio
        portfolio = PortfolioDB(
            id=uuid.uuid4(),
            name="Test Portfolio",
            total_properties=1
        )
        
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = portfolio
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_portfolio_property]
        
        # Mock the property performance calculation
        with patch.object(service, 'calculate_property_performance') as mock_calc:
            mock_calc.return_value = {
                "current_value": 250000.0,
                "total_investment": 220000.0,
                "current_equity": 100000.0,
                "total_income": 2000.0,
                "total_expenses": 1400.0,
                "annual_cash_flow": 7200.0,
                "cap_rate": 2.88,
                "coc_return": 10.29,
                "roi": 13.64
            }
            
            # Test
            period_start = datetime.now() - timedelta(days=30)
            period_end = datetime.now()
            result = service.calculate_portfolio_performance(portfolio.id, period_start, period_end)
            
            # Assertions
            assert result["portfolio_id"] == portfolio.id
            assert result["total_properties"] == 1
            assert result["total_value"] == 250000.0
            assert result["total_investment"] == 220000.0
            assert result["total_equity"] == 100000.0
            assert result["net_cash_flow"] == 600.0
            assert result["average_cap_rate"] == 2.88
            assert result["average_coc_return"] == 10.29
            assert result["average_roi"] == 13.64
    
    def test_calculate_portfolio_performance_no_properties(self, service, mock_db):
        """Test calculating portfolio performance with no properties."""
        # Create sample portfolio
        portfolio = PortfolioDB(
            id=uuid.uuid4(),
            name="Empty Portfolio",
            total_properties=0
        )
        
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = portfolio
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Test
        period_start = datetime.now() - timedelta(days=30)
        period_end = datetime.now()
        result = service.calculate_portfolio_performance(portfolio.id, period_start, period_end)
        
        # Assertions
        assert result["portfolio_id"] == portfolio.id
        assert result["total_properties"] == 0
        assert result["total_value"] == 0.0
        assert result["total_investment"] == 0.0
        assert result["total_equity"] == 0.0
        assert result["net_cash_flow"] == 0.0
    
    def test_calculate_portfolio_performance_portfolio_not_found(self, service, mock_db):
        """Test calculating portfolio performance when portfolio is not found."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Test
        period_start = datetime.now() - timedelta(days=30)
        period_end = datetime.now()
        
        with pytest.raises(ValueError, match="Portfolio .* not found"):
            service.calculate_portfolio_performance(uuid.uuid4(), period_start, period_end)
    
    def test_update_portfolio_metrics(self, service, mock_db, sample_portfolio_property):
        """Test updating portfolio metrics."""
        # Create sample portfolio
        portfolio = PortfolioDB(
            id=uuid.uuid4(),
            name="Test Portfolio",
            total_properties=0
        )
        
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = portfolio
        
        # Mock the portfolio performance calculation
        with patch.object(service, 'calculate_portfolio_performance') as mock_calc:
            mock_calc.return_value = {
                "total_properties": 1,
                "total_value": 250000.0,
                "total_equity": 100000.0,
                "total_debt": 150000.0,
                "annual_cash_flow": 7200.0,
                "total_expenses": 16800.0,
                "net_cash_flow": 7200.0,
                "average_cap_rate": 2.88,
                "average_coc_return": 10.29,
                "average_roi": 13.64,
                "diversification_score": 50.0,
                "risk_score": 25.0
            }
            
            # Test
            result = service.update_portfolio_metrics(portfolio.id)
            
            # Assertions
            assert result is True
            assert portfolio.total_properties == 1
            assert portfolio.total_value == 250000.0
            assert portfolio.total_equity == 100000.0
            assert portfolio.total_debt == 150000.0
            assert portfolio.monthly_income == 600.0  # 7200 / 12
            assert portfolio.average_cap_rate == 2.88
            assert portfolio.average_coc_return == 10.29
            assert portfolio.average_roi == 13.64
            assert portfolio.diversification_score == 50.0
            assert portfolio.risk_score == 25.0
            mock_db.commit.assert_called_once()
    
    def test_update_portfolio_metrics_portfolio_not_found(self, service, mock_db):
        """Test updating portfolio metrics when portfolio is not found."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Test
        result = service.update_portfolio_metrics(uuid.uuid4())
        
        # Assertions
        assert result is False
    
    def test_generate_performance_report(self, service, mock_db, sample_portfolio_property):
        """Test generating a performance report."""
        # Create sample portfolio
        portfolio = PortfolioDB(
            id=uuid.uuid4(),
            name="Test Portfolio"
        )
        
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = portfolio
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        # Mock the portfolio performance calculation
        with patch.object(service, 'calculate_portfolio_performance') as mock_calc:
            mock_calc.return_value = {
                "total_properties": 1,
                "total_value": 250000.0,
                "total_equity": 100000.0,
                "net_cash_flow": 7200.0,
                "average_cap_rate": 2.88,
                "average_coc_return": 10.29,
                "portfolio_roi": 13.64,
                "diversification_score": 50.0,
                "risk_score": 25.0,
                "property_performances": []
            }
            
            # Test
            period_start = datetime.now() - timedelta(days=30)
            period_end = datetime.now()
            result = service.generate_performance_report(portfolio.id, period_start, period_end)
            
            # Assertions
            assert result["portfolio_id"] == portfolio.id
            assert result["portfolio_name"] == "Test Portfolio"
            assert "report_period" in result
            assert "generated_at" in result
            assert "summary" in result
            assert "performance_metrics" in result
            assert "property_breakdown" in result
            assert "historical_trends" in result
            assert "benchmarks" in result
            assert "risk_analysis" in result
            
            # Check summary data
            summary = result["summary"]
            assert summary["total_properties"] == 1
            assert summary["total_value"] == 250000.0
            assert summary["total_equity"] == 100000.0
            assert summary["net_cash_flow"] == 7200.0
            assert summary["average_cap_rate"] == 2.88
            assert summary["average_coc_return"] == 10.29
            assert summary["portfolio_roi"] == 13.64
    
    def test_calculate_diversification_score(self, service, mock_db):
        """Test calculating diversification score."""
        # Create sample properties with different characteristics
        properties = [
            PropertyDB(id=uuid.uuid4(), city="New York", property_type="single_family", neighborhood="Manhattan"),
            PropertyDB(id=uuid.uuid4(), city="Los Angeles", property_type="condo", neighborhood="Hollywood"),
            PropertyDB(id=uuid.uuid4(), city="Chicago", property_type="multi_family", neighborhood="Loop")
        ]
        
        portfolio_properties = [
            PortfolioPropertyDB(property_id=prop.id) for prop in properties
        ]
        
        # Setup mocks
        mock_db.query.return_value.filter.return_value.all.return_value = properties
        
        # Test
        score = service._calculate_diversification_score(portfolio_properties)
        
        # Assertions
        assert 0 <= score <= 100
        assert score > 0  # Should have some diversification with different cities/types
    
    def test_calculate_diversification_score_empty(self, service, mock_db):
        """Test calculating diversification score with no properties."""
        # Test
        score = service._calculate_diversification_score([])
        
        # Assertions
        assert score == 0.0
    
    def test_calculate_risk_score(self, service, mock_db):
        """Test calculating risk score."""
        # Create sample property performances with varying cash flows
        property_performances = [
            {"annual_cash_flow": 5000.0, "cap_rate": 5.0},
            {"annual_cash_flow": 7000.0, "cap_rate": 6.0},
            {"annual_cash_flow": 6000.0, "cap_rate": 5.5},
            {"annual_cash_flow": 8000.0, "cap_rate": 7.0}
        ]
        
        # Test
        score = service._calculate_risk_score(property_performances)
        
        # Assertions
        assert 0 <= score <= 100
        assert isinstance(score, float)
    
    def test_calculate_risk_score_single_property(self, service, mock_db):
        """Test calculating risk score with single property."""
        # Create sample property performance
        property_performances = [
            {"annual_cash_flow": 5000.0, "cap_rate": 5.0}
        ]
        
        # Test
        score = service._calculate_risk_score(property_performances)
        
        # Assertions
        assert score == 50.0  # Medium risk for single property
    
    def test_calculate_risk_score_no_cash_flow(self, service, mock_db):
        """Test calculating risk score with no cash flow."""
        # Create sample property performances with zero cash flow
        property_performances = [
            {"annual_cash_flow": 0.0, "cap_rate": 0.0},
            {"annual_cash_flow": 0.0, "cap_rate": 0.0}
        ]
        
        # Test
        score = service._calculate_risk_score(property_performances)
        
        # Assertions
        assert score == 100.0  # High risk if no cash flow
    
    def test_get_portfolio_analytics(self, service, mock_db):
        """Test getting portfolio analytics."""
        portfolio_id = uuid.uuid4()
        
        # Mock the portfolio inception date
        with patch.object(service, '_get_portfolio_inception_date') as mock_inception:
            mock_inception.return_value = datetime.now() - timedelta(days=365)
            
            # Mock the portfolio performance calculations
            with patch.object(service, 'calculate_portfolio_performance') as mock_calc:
                mock_calc.return_value = {
                    "portfolio_roi": 15.0,
                    "risk_score": 30.0,
                    "diversification_score": 70.0,
                    "property_performances": []
                }
                
                # Mock other methods
                with patch.object(service, '_get_cash_flow_trend') as mock_cash_trend, \
                     patch.object(service, '_get_value_trend') as mock_value_trend, \
                     patch.object(service, '_generate_benchmarks') as mock_benchmarks, \
                     patch.object(service, '_calculate_volatility') as mock_volatility, \
                     patch.object(service, '_calculate_max_drawdown') as mock_drawdown, \
                     patch.object(service, '_analyze_geographic_diversity') as mock_geo, \
                     patch.object(service, '_analyze_property_type_diversity') as mock_type:
                    
                    mock_cash_trend.return_value = []
                    mock_value_trend.return_value = []
                    mock_benchmarks.return_value = []
                    mock_volatility.return_value = 5.0
                    mock_drawdown.return_value = 2.0
                    mock_geo.return_value = {"diversity_score": 60.0}
                    mock_type.return_value = {"diversity_score": 80.0}
                    
                    # Test
                    result = service.get_portfolio_analytics(portfolio_id)
                    
                    # Assertions
                    assert result.portfolio_id == portfolio_id
                    assert result.total_return_ytd == 15.0
                    assert result.total_return_inception == 15.0
                    assert isinstance(result.cash_flow_trend, list)
                    assert isinstance(result.value_trend, list)
                    assert isinstance(result.performance_by_property, list)
                    assert isinstance(result.benchmarks, list)
                    assert isinstance(result.risk_metrics, dict)
                    assert isinstance(result.diversification_analysis, dict)


if __name__ == "__main__":
    pytest.main([__file__])