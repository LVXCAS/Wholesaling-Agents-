"""
Unit tests for Portfolio Optimization Service.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services.portfolio_optimization_service import (
    PortfolioOptimizationService,
    UnderperformingAsset,
    OptimizationRecommendation,
    DiversificationAnalysis,
    MarketTimingRecommendation,
    OptimizationActionEnum,
    OptimizationPriorityEnum
)
from app.models.portfolio import (
    PortfolioDB, PortfolioPropertyDB, PropertyPerformanceDB
)
from app.models.property import PropertyDB


class TestPortfolioOptimizationService:
    """Test cases for PortfolioOptimizationService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_performance_service(self):
        """Create a mock performance service."""
        return Mock()
    
    @pytest.fixture
    def mock_market_service(self):
        """Create a mock market data service."""
        return Mock()
    
    @pytest.fixture
    def optimization_service(self, mock_db, mock_performance_service, mock_market_service):
        """Create a PortfolioOptimizationService instance with mocked dependencies."""
        service = PortfolioOptimizationService(mock_db)
        service.performance_service = mock_performance_service
        service.market_service = mock_market_service
        return service
    
    @pytest.fixture
    def sample_portfolio_id(self):
        """Sample portfolio ID for testing."""
        return uuid.uuid4()
    
    @pytest.fixture
    def sample_portfolio_properties(self):
        """Sample portfolio properties for testing."""
        return [
            PortfolioPropertyDB(
                id=uuid.uuid4(),
                portfolio_id=uuid.uuid4(),
                property_id=uuid.uuid4(),
                acquisition_date=datetime.now() - timedelta(days=365),
                acquisition_price=200000,
                total_investment=220000,
                current_value=250000,
                monthly_rent=2000,
                monthly_expenses=800,
                monthly_cash_flow=1200
            ),
            PortfolioPropertyDB(
                id=uuid.uuid4(),
                portfolio_id=uuid.uuid4(),
                property_id=uuid.uuid4(),
                acquisition_date=datetime.now() - timedelta(days=200),
                acquisition_price=150000,
                total_investment=165000,
                current_value=160000,
                monthly_rent=1200,
                monthly_expenses=900,
                monthly_cash_flow=300
            )
        ]
    
    def test_detect_underperforming_assets_empty_portfolio(self, optimization_service, sample_portfolio_id, mock_db):
        """Test detecting underperforming assets with empty portfolio."""
        # Setup
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Execute
        result = optimization_service.detect_underperforming_assets(sample_portfolio_id)
        
        # Assert
        assert result == []
    
    def test_detect_underperforming_assets_with_properties(self, optimization_service, sample_portfolio_id, 
                                                         sample_portfolio_properties, mock_db):
        """Test detecting underperforming assets with properties."""
        # Setup
        mock_db.query.return_value.filter.return_value.all.return_value = sample_portfolio_properties
        
        # Mock performance calculations - need to return one at a time
        def mock_performance_calc(prop_id, start_date, end_date):
            if prop_id == sample_portfolio_properties[0].id:
                return {
                    'cap_rate': 5.0,  # Below average
                    'coc_return': 6.0,  # Below average
                    'roi': 10.0,
                    'annual_cash_flow': 14400,
                    'current_value': 250000,
                    'portfolio_property': sample_portfolio_properties[0]
                }
            else:
                return {
                    'cap_rate': 2.0,  # Very low
                    'coc_return': 2.0,  # Very low
                    'roi': -3.0,  # Negative
                    'annual_cash_flow': 3600,
                    'current_value': 160000,
                    'portfolio_property': sample_portfolio_properties[1]
                }
        
        optimization_service.performance_service.calculate_property_performance.side_effect = mock_performance_calc
        
        # Mock property queries
        mock_property = Mock()
        mock_property.address = "123 Test St"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_property
        
        # Execute
        result = optimization_service.detect_underperforming_assets(sample_portfolio_id)
        
        # Assert - should have at least 1 underperforming asset (the worse one)
        assert len(result) >= 1
        assert all(isinstance(asset, UnderperformingAsset) for asset in result)
        if len(result) > 1:
            assert result[0].underperformance_score >= result[1].underperformance_score  # Sorted by score
        assert result[0].priority in [OptimizationPriorityEnum.HIGH, OptimizationPriorityEnum.CRITICAL]
    
    def test_calculate_percentile(self, optimization_service):
        """Test percentile calculation."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        # Test 25th percentile
        result = optimization_service._calculate_percentile(values, 25)
        assert result == 3.25
        
        # Test 50th percentile (median)
        result = optimization_service._calculate_percentile(values, 50)
        assert result == 5.5
        
        # Test 75th percentile
        result = optimization_service._calculate_percentile(values, 75)
        assert result == 7.75
        
        # Test empty list
        result = optimization_service._calculate_percentile([], 50)
        assert result == 0.0
    
    def test_estimate_improvement_impact(self, optimization_service):
        """Test improvement impact estimation."""
        performance = {
            'annual_cash_flow': 10000,
            'current_value': 200000
        }
        
        result = optimization_service._estimate_improvement_impact(performance)
        
        assert 'rent_increase_5pct' in result
        assert 'expense_reduction_10pct' in result
        assert 'value_improvement_10pct' in result
        assert 'combined_optimization' in result
        
        assert result['rent_increase_5pct'] == 500  # 5% of 10000
        assert result['expense_reduction_10pct'] == 1000  # 10% of 10000
        assert result['value_improvement_10pct'] == 20000  # 10% of 200000
        assert result['combined_optimization'] == 1500  # 15% of 10000
    
    def test_generate_optimization_recommendations(self, optimization_service, sample_portfolio_id, mock_db):
        """Test generating optimization recommendations."""
        # Setup
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Mock underperforming assets
        underperforming_asset = UnderperformingAsset(
            portfolio_property_id=uuid.uuid4(),
            property_id=uuid.uuid4(),
            property_address="123 Test St",
            underperformance_score=75,
            issues=["Low cap rate", "Negative cash flow"],
            potential_actions=["Increase rent", "Reduce expenses"],
            estimated_impact={'rent_increase_5pct': 1000},
            priority=OptimizationPriorityEnum.HIGH
        )
        
        optimization_service.detect_underperforming_assets = Mock(return_value=[underperforming_asset])
        optimization_service._generate_portfolio_level_recommendations = Mock(return_value=[])
        optimization_service._generate_diversification_recommendations = Mock(return_value=[])
        optimization_service._generate_market_timing_recommendations = Mock(return_value=[])
        
        # Execute
        result = optimization_service.generate_optimization_recommendations(sample_portfolio_id)
        
        # Assert
        assert len(result) >= 1
        assert all(isinstance(rec, OptimizationRecommendation) for rec in result)
    
    def test_generate_asset_recommendations(self, optimization_service):
        """Test generating recommendations for specific assets."""
        asset = UnderperformingAsset(
            portfolio_property_id=uuid.uuid4(),
            property_id=uuid.uuid4(),
            property_address="123 Test St",
            underperformance_score=75,
            issues=["Cap rate below portfolio average", "Cash flow issues"],
            potential_actions=["Increase rent", "Reduce expenses"],
            estimated_impact={
                'rent_increase_5pct': 1000,
                'expense_reduction_10pct': 800,
                'value_improvement_10pct': 20000
            },
            priority=OptimizationPriorityEnum.HIGH
        )
        
        result = optimization_service._generate_asset_recommendations(asset)
        
        assert len(result) >= 2  # Should generate multiple recommendations
        assert all(isinstance(rec, OptimizationRecommendation) for rec in result)
        assert any(rec.recommendation_type == OptimizationActionEnum.IMPROVE for rec in result)
    
    def test_generate_portfolio_level_recommendations(self, optimization_service, sample_portfolio_id):
        """Test generating portfolio-level recommendations."""
        # Mock portfolio performance
        portfolio_performance = {
            'average_coc_return': 6.0,  # Below 8.0 threshold
            'total_properties': 5,  # Below 10 threshold
            'average_cap_rate': 7.0,  # Above 6.0 threshold
            'annual_cash_flow': 50000,
            'total_value': 1000000
        }
        
        optimization_service.performance_service.calculate_portfolio_performance.return_value = portfolio_performance
        
        result = optimization_service._generate_portfolio_level_recommendations(sample_portfolio_id)
        
        assert len(result) >= 1
        assert all(isinstance(rec, OptimizationRecommendation) for rec in result)
        assert any(rec.recommendation_type == OptimizationActionEnum.REFINANCE for rec in result)
        assert any(rec.recommendation_type == OptimizationActionEnum.ACQUIRE_SIMILAR for rec in result)
    
    def test_analyze_diversification(self, optimization_service, sample_portfolio_id, sample_portfolio_properties, mock_db):
        """Test diversification analysis."""
        # Setup - need to mock the query chain properly
        portfolio_query_mock = Mock()
        portfolio_query_mock.filter.return_value.all.return_value = sample_portfolio_properties
        
        property_query_mock = Mock()
        mock_properties = [
            Mock(id=sample_portfolio_properties[0].property_id, city="City1", state="State1", property_type="SFR"),
            Mock(id=sample_portfolio_properties[1].property_id, city="City2", state="State1", property_type="Condo")
        ]
        property_query_mock.filter.return_value.all.return_value = mock_properties
        
        # Mock the query method to return different mocks based on the model
        def mock_query(model):
            if model.__name__ == 'PortfolioPropertyDB':
                return portfolio_query_mock
            elif model.__name__ == 'PropertyDB':
                return property_query_mock
            else:
                return Mock()
        
        mock_db.query.side_effect = mock_query
        
        result = optimization_service.analyze_diversification(sample_portfolio_id)
        
        assert isinstance(result, DiversificationAnalysis)
        assert result.portfolio_id == sample_portfolio_id
        assert 0 <= result.overall_score <= 100
        assert 'score' in result.geographic_diversity
        assert 'score' in result.property_type_diversity
        assert len(result.recommendations) >= 0
    
    def test_analyze_diversification_empty_portfolio(self, optimization_service, sample_portfolio_id, mock_db):
        """Test diversification analysis with empty portfolio."""
        # Setup
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = optimization_service.analyze_diversification(sample_portfolio_id)
        
        assert isinstance(result, DiversificationAnalysis)
        assert result.portfolio_id == sample_portfolio_id
        assert result.overall_score == 0.0
        assert result.geographic_diversity == {}
        assert result.property_type_diversity == {}
    
    def test_analyze_geographic_diversity(self, optimization_service, sample_portfolio_properties):
        """Test geographic diversity analysis."""
        # Mock property dictionary
        property_dict = {
            sample_portfolio_properties[0].property_id: Mock(city="City1", state="State1"),
            sample_portfolio_properties[1].property_id: Mock(city="City2", state="State2")
        }
        
        result = optimization_service._analyze_geographic_diversity(sample_portfolio_properties, property_dict)
        
        assert 'score' in result
        assert 'city_distribution' in result
        assert 'state_distribution' in result
        assert 0 <= result['score'] <= 100
        assert len(result['city_distribution']) == 2
        assert len(result['state_distribution']) == 2
    
    def test_analyze_property_type_diversity(self, optimization_service, sample_portfolio_properties):
        """Test property type diversity analysis."""
        # Mock property dictionary
        property_dict = {
            sample_portfolio_properties[0].property_id: Mock(property_type="SFR"),
            sample_portfolio_properties[1].property_id: Mock(property_type="Condo")
        }
        
        result = optimization_service._analyze_property_type_diversity(sample_portfolio_properties, property_dict)
        
        assert 'score' in result
        assert 'type_distribution' in result
        assert 0 <= result['score'] <= 100
        assert len(result['type_distribution']) == 2
    
    def test_analyze_price_range_diversity(self, optimization_service, sample_portfolio_properties):
        """Test price range diversity analysis."""
        result = optimization_service._analyze_price_range_diversity(sample_portfolio_properties)
        
        assert 'score' in result
        assert 'range_distribution' in result
        assert 0 <= result['score'] <= 100
        assert 'under_100k' in result['range_distribution']
        assert '100k_250k' in result['range_distribution']
    
    def test_analyze_income_source_diversity(self, optimization_service, sample_portfolio_properties):
        """Test income source diversity analysis."""
        result = optimization_service._analyze_income_source_diversity(sample_portfolio_properties)
        
        assert 'score' in result
        assert 'source_distribution' in result
        assert 0 <= result['score'] <= 100
        assert 'rental_income' in result['source_distribution']
        assert 'appreciation' in result['source_distribution']
    
    def test_analyze_market_timing(self, optimization_service, sample_portfolio_id, sample_portfolio_properties, mock_db):
        """Test market timing analysis."""
        # Setup
        mock_db.query.return_value.filter.return_value.all.return_value = sample_portfolio_properties
        
        # Mock properties
        mock_properties = [Mock(id=prop.property_id) for prop in sample_portfolio_properties]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_properties
        
        result = optimization_service.analyze_market_timing(sample_portfolio_id)
        
        assert isinstance(result, MarketTimingRecommendation)
        assert result.portfolio_id == sample_portfolio_id
        assert result.market_phase in ['expansion', 'peak', 'contraction', 'trough', 'stable', 'unknown']
        assert 0 <= result.timing_confidence <= 1
        assert len(result.recommended_actions) >= 0
        assert 'start' in result.optimal_timing_window
        assert 'end' in result.optimal_timing_window
    
    def test_determine_market_phase(self, optimization_service):
        """Test market phase determination."""
        # Test expansion phase
        indicators = {'price_trend': 'rising', 'inventory_levels': 'low'}
        result = optimization_service._determine_market_phase(indicators)
        assert result == 'expansion'
        
        # Test peak phase
        indicators = {'price_trend': 'rising', 'inventory_levels': 'high'}
        result = optimization_service._determine_market_phase(indicators)
        assert result == 'peak'
        
        # Test contraction phase
        indicators = {'price_trend': 'falling', 'inventory_levels': 'high'}
        result = optimization_service._determine_market_phase(indicators)
        assert result == 'contraction'
        
        # Test trough phase
        indicators = {'price_trend': 'falling', 'inventory_levels': 'low'}
        result = optimization_service._determine_market_phase(indicators)
        assert result == 'trough'
        
        # Test stable phase
        indicators = {'price_trend': 'stable', 'inventory_levels': 'normal'}
        result = optimization_service._determine_market_phase(indicators)
        assert result == 'stable'
    
    def test_get_market_phase_actions(self, optimization_service):
        """Test getting market phase actions."""
        # Test each phase
        phases = ['expansion', 'peak', 'contraction', 'trough', 'stable']
        
        for phase in phases:
            actions = optimization_service._get_market_phase_actions(phase)
            assert isinstance(actions, list)
            assert len(actions) > 0
            assert all(isinstance(action, str) for action in actions)
        
        # Test unknown phase
        actions = optimization_service._get_market_phase_actions('unknown')
        assert isinstance(actions, list)
        assert len(actions) > 0
    
    def test_error_handling_detect_underperforming_assets(self, optimization_service, sample_portfolio_id, mock_db):
        """Test error handling in detect_underperforming_assets."""
        # Setup to raise an exception
        mock_db.query.side_effect = Exception("Database error")
        
        # Execute and assert
        with pytest.raises(Exception, match="Database error"):
            optimization_service.detect_underperforming_assets(sample_portfolio_id)
    
    def test_error_handling_generate_optimization_recommendations(self, optimization_service, sample_portfolio_id):
        """Test error handling in generate_optimization_recommendations."""
        # Setup to raise an exception
        optimization_service.detect_underperforming_assets = Mock(side_effect=Exception("Service error"))
        
        # Execute and assert
        with pytest.raises(Exception, match="Service error"):
            optimization_service.generate_optimization_recommendations(sample_portfolio_id)
    
    def test_error_handling_analyze_diversification(self, optimization_service, sample_portfolio_id, mock_db):
        """Test error handling in analyze_diversification."""
        # Setup to raise an exception
        mock_db.query.side_effect = Exception("Database error")
        
        # Execute and assert
        with pytest.raises(Exception, match="Database error"):
            optimization_service.analyze_diversification(sample_portfolio_id)
    
    def test_error_handling_analyze_market_timing(self, optimization_service, sample_portfolio_id, mock_db):
        """Test error handling in analyze_market_timing."""
        # Setup to raise an exception
        mock_db.query.side_effect = Exception("Database error")
        
        # Execute and assert
        with pytest.raises(Exception, match="Database error"):
            optimization_service.analyze_market_timing(sample_portfolio_id)


if __name__ == "__main__":
    pytest.main([__file__])