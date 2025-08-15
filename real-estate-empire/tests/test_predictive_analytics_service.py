"""
Unit tests for the Predictive Analytics Service.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services.predictive_analytics_service import PredictiveAnalyticsService
from app.models.predictive_analytics import (
    PredictiveModelDB, PredictionDB, MarketTrendPredictionDB, DealOutcomePredictionDB,
    PortfolioForecastDB, RiskAssessmentDB, PredictionTypeEnum, PredictionStatusEnum,
    RiskLevelEnum, MarketTrendDirectionEnum,
    MarketTrendPredictionRequest, DealOutcomePredictionRequest,
    PortfolioForecastRequest, RiskAssessmentRequest
)
from app.models.portfolio import PortfolioDB
from app.models.property import PropertyDB


class TestPredictiveAnalyticsService:
    """Test cases for PredictiveAnalyticsService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """Create a PredictiveAnalyticsService instance with mocked dependencies."""
        with patch('app.services.predictive_analytics_service.MarketDataService'), \
             patch('app.services.predictive_analytics_service.PortfolioPerformanceService'):
            return PredictiveAnalyticsService(mock_db)
    
    @pytest.fixture
    def sample_portfolio(self):
        """Create a sample portfolio for testing."""
        return PortfolioDB(
            id=uuid.uuid4(),
            name="Test Portfolio",
            total_properties=5,
            total_value=1000000.0,
            total_equity=600000.0,
            monthly_cash_flow=5000.0,
            average_cap_rate=0.08,
            average_coc_return=0.12,
            diversification_score=0.7,
            risk_score=0.3,
            created_at=datetime.utcnow() - timedelta(days=365)
        )
    
    @pytest.fixture
    def sample_property(self):
        """Create a sample property for testing."""
        return PropertyDB(
            id=uuid.uuid4(),
            address="123 Test St",
            city="Austin",
            state="TX",
            zip_code="78701",
            current_value=300000.0,
            year_built=2010,
            days_on_market=30,
            condition_score=0.8,
            crime_score=25.0
        )
    
    def test_predict_market_trend_success(self, service, mock_db):
        """Test successful market trend prediction."""
        # Arrange
        request = MarketTrendPredictionRequest(
            market_area="Austin, TX",
            property_type="single_family",
            forecast_horizon_days=90
        )
        
        mock_model = Mock(spec=PredictiveModelDB)
        mock_model.id = uuid.uuid4()
        
        service._get_or_create_model = Mock(return_value=mock_model)
        service._make_prediction = Mock(return_value={
            "predicted_value": 0.7,
            "confidence_score": 0.85
        })
        
        # Mock the market data service to return None (will use defaults)
        service.market_data_service.get_market_stats = Mock(return_value=None)
        
        # Mock database operations
        def mock_add(obj):
            if hasattr(obj, 'id') and obj.id is None:
                obj.id = uuid.uuid4()
            if hasattr(obj, 'created_at') and obj.created_at is None:
                obj.created_at = datetime.utcnow()
        
        mock_db.add = Mock(side_effect=mock_add)
        mock_db.flush = Mock()
        mock_db.commit = Mock()
        
        # Act
        result = service.predict_market_trend(request)
        
        # Assert
        assert result is not None
        assert result.market_area == "Austin, TX"
        assert result.property_type == "single_family"
        assert result.trend_direction == MarketTrendDirectionEnum.BULLISH
        assert result.confidence_level == 0.85
        assert isinstance(result.forecast_start_date, datetime)
        assert isinstance(result.forecast_end_date, datetime)
        
        # Verify database operations
        mock_db.add.assert_called()
        mock_db.flush.assert_called()
        mock_db.commit.assert_called()
    
    def test_predict_deal_outcome_success(self, service, mock_db):
        """Test successful deal outcome prediction."""
        # Arrange
        property_id = uuid.uuid4()
        request = DealOutcomePredictionRequest(
            property_id=property_id,
            deal_type="flip",
            offer_amount=250000.0,
            estimated_repair_cost=50000.0,
            property_features={
                "bedrooms": 3,
                "bathrooms": 2,
                "square_feet": 1500,
                "arv": 350000.0
            }
        )
        
        mock_model = Mock(spec=PredictiveModelDB)
        mock_model.id = uuid.uuid4()
        
        service._get_or_create_model = Mock(return_value=mock_model)
        service._make_prediction = Mock(return_value={
            "predicted_value": 0.8,
            "confidence_score": 0.75
        })
        
        mock_db.add = Mock()
        mock_db.flush = Mock()
        mock_db.commit = Mock()
        
        # Act
        result = service.predict_deal_outcome(request)
        
        # Assert
        assert result is not None
        assert result.property_id == property_id
        assert result.deal_type == "flip"
        assert result.offer_amount == 250000.0
        assert result.success_probability == 0.75
        assert result.expected_profit > 0
        assert result.risk_level in [RiskLevelEnum.LOW, RiskLevelEnum.MEDIUM]
        
        # Verify database operations
        mock_db.add.assert_called()
        mock_db.flush.assert_called()
        mock_db.commit.assert_called()
    
    def test_forecast_portfolio_performance_success(self, service, mock_db, sample_portfolio):
        """Test successful portfolio performance forecasting."""
        # Arrange
        request = PortfolioForecastRequest(
            portfolio_id=sample_portfolio.id,
            forecast_horizon_months=12,
            scenario_analysis=True
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = sample_portfolio
        
        mock_model = Mock(spec=PredictiveModelDB)
        mock_model.id = uuid.uuid4()
        
        service._get_or_create_model = Mock(return_value=mock_model)
        service._make_prediction = Mock(return_value={
            "predicted_value": 1100000.0,
            "confidence_score": 0.8
        })
        
        mock_db.add = Mock()
        mock_db.flush = Mock()
        mock_db.commit = Mock()
        
        # Act
        result = service.forecast_portfolio_performance(request)
        
        # Assert
        assert result is not None
        assert result.portfolio_id == sample_portfolio.id
        assert result.forecast_horizon_months == 12
        assert result.projected_value > sample_portfolio.total_value
        assert result.projected_appreciation > 0
        assert len(result.monthly_projections) == 12
        assert result.best_case_scenario is not None
        assert result.worst_case_scenario is not None
        assert result.most_likely_scenario is not None
        
        # Verify database operations
        mock_db.add.assert_called()
        mock_db.flush.assert_called()
        mock_db.commit.assert_called()
    
    def test_assess_risk_success(self, service, mock_db, sample_property):
        """Test successful risk assessment."""
        # Arrange
        request = RiskAssessmentRequest(
            target_type="property",
            target_id=sample_property.id,
            include_stress_testing=True,
            include_scenario_analysis=True
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = sample_property
        
        mock_model = Mock(spec=PredictiveModelDB)
        mock_model.id = uuid.uuid4()
        
        service._get_or_create_model = Mock(return_value=mock_model)
        service._make_prediction = Mock(return_value={
            "predicted_value": 35.0,
            "confidence_score": 0.9
        })
        
        mock_db.add = Mock()
        mock_db.flush = Mock()
        mock_db.commit = Mock()
        
        # Act
        result = service.assess_risk(request)
        
        # Assert
        assert result is not None
        assert result.target_type == "property"
        assert result.target_id == sample_property.id
        assert result.overall_risk_score == 35.0
        assert result.risk_level == RiskLevelEnum.MEDIUM
        assert result.market_risk_score is not None
        assert result.liquidity_risk_score is not None
        assert result.stress_test_results is not None
        assert result.scenario_analysis is not None
        
        # Verify database operations
        mock_db.add.assert_called()
        mock_db.flush.assert_called()
        mock_db.commit.assert_called()
    
    def test_get_or_create_model_existing(self, service, mock_db):
        """Test getting an existing model."""
        # Arrange
        existing_model = Mock(spec=PredictiveModelDB)
        existing_model.id = uuid.uuid4()
        existing_model.name = "market_trend"
        existing_model.model_type = "random_forest"
        
        mock_db.query.return_value.filter.return_value.first.return_value = existing_model
        
        # Act
        result = service._get_or_create_model("market_trend", "random_forest")
        
        # Assert
        assert result == existing_model
        mock_db.query.assert_called()
    
    def test_get_or_create_model_new(self, service, mock_db):
        """Test creating a new model when none exists."""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        new_model = Mock(spec=PredictiveModelDB)
        new_model.id = uuid.uuid4()
        
        service._create_and_train_model = Mock(return_value=new_model)
        
        # Act
        result = service._get_or_create_model("market_trend", "random_forest")
        
        # Assert
        assert result == new_model
        service._create_and_train_model.assert_called_once_with("market_trend", "random_forest")
    
    def test_make_heuristic_prediction_market_trend(self, service):
        """Test heuristic prediction for market trends."""
        # Arrange
        features = {
            "price_trend": 0.1,
            "volume_trend": 0.05,
            "avg_price": 300000
        }
        
        # Act
        result = service._make_heuristic_prediction(features, PredictionTypeEnum.MARKET_TREND)
        
        # Assert
        assert "predicted_value" in result
        assert "confidence_score" in result
        assert 0 <= result["confidence_score"] <= 1
        assert isinstance(result["predicted_value"], float)
    
    def test_make_heuristic_prediction_deal_outcome(self, service):
        """Test heuristic prediction for deal outcomes."""
        # Arrange
        features = {
            "profit_margin": 0.2,
            "market_strength": 0.7,
            "offer_amount": 250000
        }
        
        # Act
        result = service._make_heuristic_prediction(features, PredictionTypeEnum.DEAL_OUTCOME)
        
        # Assert
        assert "predicted_value" in result
        assert "confidence_score" in result
        assert 0 <= result["confidence_score"] <= 1
        assert 0 <= result["predicted_value"] <= 1
    
    def test_interpret_market_trend_bullish(self, service):
        """Test market trend interpretation for bullish trend."""
        result = service._interpret_market_trend(0.8)
        assert result == MarketTrendDirectionEnum.BULLISH
    
    def test_interpret_market_trend_bearish(self, service):
        """Test market trend interpretation for bearish trend."""
        result = service._interpret_market_trend(0.2)
        assert result == MarketTrendDirectionEnum.BEARISH
    
    def test_interpret_market_trend_sideways(self, service):
        """Test market trend interpretation for sideways trend."""
        result = service._interpret_market_trend(0.5)
        assert result == MarketTrendDirectionEnum.SIDEWAYS
    
    def test_assess_deal_risk_level_low(self, service):
        """Test deal risk level assessment for low risk."""
        features = {"profit_margin": 0.3}
        result = service._assess_deal_risk_level(features, 0.9)
        assert result == RiskLevelEnum.LOW
    
    def test_assess_deal_risk_level_high(self, service):
        """Test deal risk level assessment for high risk."""
        features = {"profit_margin": 0.05}
        result = service._assess_deal_risk_level(features, 0.3)
        assert result == RiskLevelEnum.HIGH
    
    def test_determine_risk_level_from_score(self, service):
        """Test risk level determination from numeric score."""
        assert service._determine_risk_level(15) == RiskLevelEnum.LOW
        assert service._determine_risk_level(35) == RiskLevelEnum.MEDIUM
        assert service._determine_risk_level(65) == RiskLevelEnum.HIGH
        assert service._determine_risk_level(85) == RiskLevelEnum.VERY_HIGH
    
    def test_calculate_expected_profit(self, service):
        """Test expected profit calculation."""
        request = DealOutcomePredictionRequest(
            deal_type="flip",
            offer_amount=200000.0,
            estimated_repair_cost=30000.0,
            property_features={}
        )
        features = {"property_arv": 280000.0}
        
        result = service._calculate_expected_profit(request, features)
        expected = 280000.0 - 200000.0 - 30000.0  # ARV - offer - repairs
        assert result == expected
    
    def test_calculate_expected_roi(self, service):
        """Test expected ROI calculation."""
        request = DealOutcomePredictionRequest(
            deal_type="flip",
            offer_amount=200000.0,
            property_features={}
        )
        expected_profit = 50000.0
        
        result = service._calculate_expected_roi(request, expected_profit)
        expected_roi = (50000.0 / 200000.0) * 100  # 25%
        assert result == expected_roi
    
    def test_estimate_completion_time(self, service):
        """Test completion time estimation."""
        features = {}
        
        flip_time = service._estimate_completion_time("flip", features)
        rental_time = service._estimate_completion_time("rental", features)
        wholesale_time = service._estimate_completion_time("wholesale", features)
        
        assert flip_time == 120  # 4 months
        assert rental_time == 60   # 2 months
        assert wholesale_time == 30  # 1 month
    
    def test_prepare_market_trend_features(self, service):
        """Test market trend feature preparation."""
        request = MarketTrendPredictionRequest(
            market_area="Austin, TX",
            forecast_horizon_days=90
        )
        
        # Mock market data service
        service.market_data_service.get_market_stats = Mock(return_value=None)
        
        result = service._prepare_market_trend_features(request)
        
        assert "avg_price" in result
        assert "forecast_horizon" in result
        assert "month" in result
        assert "quarter" in result
        assert result["forecast_horizon"] == 90
    
    def test_prepare_deal_outcome_features(self, service):
        """Test deal outcome feature preparation."""
        request = DealOutcomePredictionRequest(
            deal_type="flip",
            offer_amount=250000.0,
            estimated_repair_cost=40000.0,
            property_features={
                "bedrooms": 3,
                "bathrooms": 2.5,
                "arv": 320000.0
            }
        )
        
        result = service._prepare_deal_outcome_features(request)
        
        assert result["offer_amount"] == 250000.0
        assert result["estimated_repair_cost"] == 40000.0
        assert result["deal_type_flip"] == 1
        assert result["deal_type_rental"] == 0
        assert result["property_bedrooms"] == 3
        assert result["property_bathrooms"] == 2.5
        assert "profit_margin" in result
    
    def test_prepare_portfolio_features(self, service, sample_portfolio):
        """Test portfolio feature preparation."""
        result = service._prepare_portfolio_features(sample_portfolio)
        
        assert result["total_properties"] == sample_portfolio.total_properties
        assert result["total_value"] == sample_portfolio.total_value
        assert result["monthly_cash_flow"] == sample_portfolio.monthly_cash_flow
        assert "portfolio_age_days" in result
        assert "current_performance" in result
    
    def test_project_cash_flow(self, service, sample_portfolio):
        """Test cash flow projection."""
        result = service._project_cash_flow(sample_portfolio, 12)
        
        assert result > 0
        assert result > sample_portfolio.monthly_cash_flow * 12  # Should account for growth
    
    def test_calculate_projected_roi(self, service, sample_portfolio):
        """Test projected ROI calculation."""
        projected_value = 1100000.0
        projected_cash_flow = 65000.0
        
        result = service._calculate_projected_roi(sample_portfolio, projected_value, projected_cash_flow)
        
        assert result > 0
        # Should be (value_gain + cash_flow) / initial_value * 100
        expected = ((projected_value - sample_portfolio.total_value) + projected_cash_flow) / sample_portfolio.total_value * 100
        assert abs(result - expected) < 0.01
    
    def test_identify_market_risk_factors(self, service):
        """Test market risk factor identification."""
        features = {
            "total_listings": 1500,  # High inventory
            "price_trend": -0.15     # Declining prices
        }
        
        result = service._identify_market_risk_factors(features)
        
        assert len(result) == 2
        assert "High inventory levels" in result
        assert "Declining price trend" in result
    
    def test_identify_deal_risk_factors(self, service):
        """Test deal risk factor identification."""
        features = {
            "profit_margin": 0.05,    # Low margin
            "estimated_repair_cost": 80000,
            "offer_amount": 200000    # High repair cost ratio
        }
        
        result = service._identify_deal_risk_factors(features)
        
        assert len(result) >= 1
        assert any("Low profit margin" in factor for factor in result)
    
    def test_error_handling_market_trend(self, service, mock_db):
        """Test error handling in market trend prediction."""
        request = MarketTrendPredictionRequest(
            market_area="Invalid, XX",
            forecast_horizon_days=90
        )
        
        # Mock an exception in model creation
        service._get_or_create_model = Mock(side_effect=Exception("Model creation failed"))
        
        with pytest.raises(Exception):
            service.predict_market_trend(request)
    
    def test_error_handling_deal_outcome(self, service, mock_db):
        """Test error handling in deal outcome prediction."""
        request = DealOutcomePredictionRequest(
            deal_type="invalid_type",
            offer_amount=0,  # Invalid amount
            property_features={}
        )
        
        # Mock an exception in prediction
        service._get_or_create_model = Mock(side_effect=Exception("Prediction failed"))
        
        with pytest.raises(Exception):
            service.predict_deal_outcome(request)
    
    def test_portfolio_not_found_error(self, service, mock_db):
        """Test error when portfolio is not found."""
        request = PortfolioForecastRequest(
            portfolio_id=uuid.uuid4(),
            forecast_horizon_months=12
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Portfolio .* not found"):
            service.forecast_portfolio_performance(request)
    
    @pytest.mark.parametrize("prediction_type,expected_enum", [
        ("market_trend", PredictionTypeEnum.MARKET_TREND),
        ("deal_outcome", PredictionTypeEnum.DEAL_OUTCOME),
        ("portfolio_performance", PredictionTypeEnum.PORTFOLIO_PERFORMANCE),
        ("risk_assessment", PredictionTypeEnum.RISK_ASSESSMENT),
        ("unknown_type", PredictionTypeEnum.MARKET_TREND)  # Default
    ])
    def test_get_prediction_type_for_model(self, service, prediction_type, expected_enum):
        """Test prediction type mapping for different model names."""
        result = service._get_prediction_type_for_model(prediction_type)
        assert result == expected_enum
    
    def test_generate_portfolio_scenarios(self, service, sample_portfolio):
        """Test portfolio scenario generation."""
        features = {"market_conditions": 0.6}
        
        result = service._generate_portfolio_scenarios(sample_portfolio, features, 12)
        
        assert "best_case" in result
        assert "worst_case" in result
        assert "most_likely" in result
        
        # Best case should be higher than worst case
        assert result["best_case"]["projected_value"] > result["worst_case"]["projected_value"]
        
        # All scenarios should have probabilities
        assert 0 < result["best_case"]["probability"] <= 1
        assert 0 < result["worst_case"]["probability"] <= 1
        assert 0 < result["most_likely"]["probability"] <= 1
    
    def test_calculate_portfolio_risk_metrics(self, service, sample_portfolio):
        """Test portfolio risk metrics calculation."""
        projections = [
            {"projected_value": 1000000},
            {"projected_value": 1050000},
            {"projected_value": 1100000},
            {"projected_value": 950000},
            {"projected_value": 1025000}
        ]
        
        result = service._calculate_portfolio_risk_metrics(sample_portfolio, projections)
        
        assert "value_at_risk" in result
        assert "expected_shortfall" in result
        assert "volatility" in result
        
        assert result["value_at_risk"] > 0
        assert result["volatility"] >= 0