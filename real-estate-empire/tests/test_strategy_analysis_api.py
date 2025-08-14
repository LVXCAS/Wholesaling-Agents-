"""
Tests for Strategy Analysis API endpoints
"""

import pytest
import uuid
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set testing environment variable before importing app
os.environ["TESTING"] = "1"

from app.api.main import app
from app.core.database import Base, get_db

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_strategy_analysis.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def sample_property_data():
    """Sample property data for testing"""
    return {
        "address": "456 Strategy Street",
        "city": "Investment City",
        "state": "TX",
        "zip_code": "54321",
        "property_type": "single_family",
        "bedrooms": 3,
        "bathrooms": 2.0,
        "square_feet": 1800,
        "lot_size": 0.3,
        "year_built": 1995,
        "listing_price": 250000,
        "current_value": 280000,
        "condition_score": 0.7
    }

@pytest.fixture
def created_property(sample_property_data):
    """Create a property in the test database"""
    response = client.post("/api/v1/properties/", json=sample_property_data)
    assert response.status_code == 201
    return response.json()

class TestFlipStrategyAnalysis:
    """Test flip strategy analysis endpoints"""
    
    def test_analyze_flip_strategy_default(self, created_property):
        """Test flip strategy analysis with default parameters"""
        property_id = created_property["id"]
        
        response = client.post(f"/api/v1/strategies/{property_id}/flip")
        
        assert response.status_code == 200
        data = response.json()
        assert "strategy" in data
        assert data["property_id"] == property_id
        
        strategy = data["strategy"]
        assert strategy["strategy_type"] == "flip"
        assert "financial_analysis" in strategy
        assert "timeline" in strategy
        assert "risk_assessment" in strategy
        assert "recommendation" in strategy
        
        # Check financial analysis structure
        financial = strategy["financial_analysis"]
        assert "purchase_price" in financial
        assert "repair_costs" in financial
        assert "total_investment" in financial
        assert "after_repair_value" in financial
        assert "net_profit" in financial
        assert "roi_percentage" in financial
    
    def test_analyze_flip_strategy_custom_params(self, created_property):
        """Test flip strategy analysis with custom parameters"""
        property_id = created_property["id"]
        
        response = client.post(
            f"/api/v1/strategies/{property_id}/flip",
            params={
                "purchase_price": 220000,
                "repair_budget": 40000,
                "holding_period_months": 8
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        strategy = data["strategy"]
        
        # Verify custom parameters were used
        financial = strategy["financial_analysis"]
        assert financial["purchase_price"] == 220000
        assert financial["repair_costs"] == 40000
        
        timeline = strategy["timeline"]
        # Timeline should reflect 8-month holding period
        assert timeline["total_timeline_days"] > 200  # Rough check
    
    def test_flip_strategy_recommendation_logic(self, created_property):
        """Test flip strategy recommendation logic"""
        property_id = created_property["id"]
        
        response = client.post(f"/api/v1/strategies/{property_id}/flip")
        
        assert response.status_code == 200
        data = response.json()
        strategy = data["strategy"]
        recommendation = strategy["recommendation"]
        
        assert "proceed" in recommendation
        assert "reason" in recommendation
        assert "key_metrics" in recommendation
        assert isinstance(recommendation["proceed"], bool)

class TestRentalStrategyAnalysis:
    """Test rental strategy analysis endpoints"""
    
    def test_analyze_rental_strategy_default(self, created_property):
        """Test rental strategy analysis with default parameters"""
        property_id = created_property["id"]
        
        response = client.post(f"/api/v1/strategies/{property_id}/rental")
        
        assert response.status_code == 200
        data = response.json()
        assert "strategy" in data
        
        strategy = data["strategy"]
        assert strategy["strategy_type"] == "rental"
        assert "financial_analysis" in strategy
        assert "financing_details" in strategy
        assert "risk_assessment" in strategy
        assert "recommendation" in strategy
        
        # Check rental-specific metrics
        financial = strategy["financial_analysis"]
        assert "monthly_rent" in financial
        assert "monthly_expenses" in financial
        assert "monthly_cash_flow" in financial
        assert "cap_rate_percentage" in financial
        assert "cash_on_cash_return_percentage" in financial
    
    def test_analyze_rental_strategy_custom_financing(self, created_property):
        """Test rental strategy with custom financing parameters"""
        property_id = created_property["id"]
        
        response = client.post(
            f"/api/v1/strategies/{property_id}/rental",
            params={
                "purchase_price": 260000,
                "down_payment_percentage": 0.20,
                "interest_rate": 0.065,
                "loan_term_years": 25
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        strategy = data["strategy"]
        
        # Verify custom financing parameters
        financing = strategy["financing_details"]
        assert financing["down_payment_percentage"] == 20.0
        assert financing["interest_rate_percentage"] == 6.5
        assert financing["loan_term_years"] == 25
        
        financial = strategy["financial_analysis"]
        assert financial["purchase_price"] == 260000
    
    def test_rental_cash_flow_calculation(self, created_property):
        """Test rental cash flow calculation accuracy"""
        property_id = created_property["id"]
        
        response = client.post(f"/api/v1/strategies/{property_id}/rental")
        
        assert response.status_code == 200
        data = response.json()
        strategy = data["strategy"]
        financial = strategy["financial_analysis"]
        
        # Verify cash flow calculation
        monthly_rent = financial["monthly_rent"]
        total_expenses = financial["monthly_expenses"]["total"]
        calculated_cash_flow = monthly_rent - total_expenses
        
        assert abs(financial["monthly_cash_flow"] - calculated_cash_flow) < 0.01

class TestWholesaleStrategyAnalysis:
    """Test wholesale strategy analysis endpoints"""
    
    def test_analyze_wholesale_strategy_default(self, created_property):
        """Test wholesale strategy analysis with default parameters"""
        property_id = created_property["id"]
        
        response = client.post(f"/api/v1/strategies/{property_id}/wholesale")
        
        assert response.status_code == 200
        data = response.json()
        strategy = data["strategy"]
        
        assert strategy["strategy_type"] == "wholesale"
        assert "financial_analysis" in strategy
        assert "timeline" in strategy
        assert "market_analysis" in strategy
        assert "risk_assessment" in strategy
        
        # Check wholesale-specific metrics
        financial = strategy["financial_analysis"]
        assert "contract_price" in financial
        assert "wholesale_fee" in financial
        assert "maximum_allowable_offer" in financial
        assert "profit_margin_percentage" in financial
        assert "roi_annualized_percentage" in financial
    
    def test_analyze_wholesale_strategy_custom_params(self, created_property):
        """Test wholesale strategy with custom parameters"""
        property_id = created_property["id"]
        
        response = client.post(
            f"/api/v1/strategies/{property_id}/wholesale",
            params={
                "contract_price": 200000,
                "wholesale_fee": 15000,
                "assignment_timeline_days": 21
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        strategy = data["strategy"]
        
        # Verify custom parameters
        financial = strategy["financial_analysis"]
        assert financial["contract_price"] == 200000
        assert financial["wholesale_fee"] == 15000
        
        timeline = strategy["timeline"]
        assert timeline["total_timeline_days"] == 21
    
    def test_wholesale_mao_calculation(self, created_property):
        """Test Maximum Allowable Offer (MAO) calculation"""
        property_id = created_property["id"]
        
        response = client.post(f"/api/v1/strategies/{property_id}/wholesale")
        
        assert response.status_code == 200
        data = response.json()
        strategy = data["strategy"]
        financial = strategy["financial_analysis"]
        
        # MAO should be reasonable relative to ARV
        arv = financial["after_repair_value"]
        mao = financial["maximum_allowable_offer"]
        
        assert mao < arv  # MAO should be less than ARV
        assert mao > 0    # MAO should be positive

class TestBRRRRStrategyAnalysis:
    """Test BRRRR strategy analysis endpoints"""
    
    def test_analyze_brrrr_strategy_default(self, created_property):
        """Test BRRRR strategy analysis with default parameters"""
        property_id = created_property["id"]
        
        response = client.post(f"/api/v1/strategies/{property_id}/brrrr")
        
        assert response.status_code == 200
        data = response.json()
        strategy = data["strategy"]
        
        assert strategy["strategy_type"] == "brrrr"
        assert "financial_analysis" in strategy
        assert "refinance_details" in strategy
        assert "timeline" in strategy
        assert "risk_assessment" in strategy
        
        # Check BRRRR-specific metrics
        financial = strategy["financial_analysis"]
        assert "total_investment" in financial
        assert "refinance_amount" in financial
        assert "cash_recovered" in financial
        assert "cash_left_in_deal" in financial
        assert "infinite_return" in financial
    
    def test_analyze_brrrr_strategy_custom_params(self, created_property):
        """Test BRRRR strategy with custom parameters"""
        property_id = created_property["id"]
        
        response = client.post(
            f"/api/v1/strategies/{property_id}/brrrr",
            params={
                "purchase_price": 230000,
                "repair_budget": 35000,
                "refinance_ltv": 0.80,
                "refinance_rate": 0.055
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        strategy = data["strategy"]
        
        # Verify custom parameters
        financial = strategy["financial_analysis"]
        assert financial["purchase_price"] == 230000
        assert financial["repair_costs"] == 35000
        
        refinance = strategy["refinance_details"]
        assert refinance["refinance_ltv_percentage"] == 80.0
        assert refinance["refinance_rate_percentage"] == 5.5
    
    def test_brrrr_cash_recovery_calculation(self, created_property):
        """Test BRRRR cash recovery calculation"""
        property_id = created_property["id"]
        
        response = client.post(f"/api/v1/strategies/{property_id}/brrrr")
        
        assert response.status_code == 200
        data = response.json()
        strategy = data["strategy"]
        financial = strategy["financial_analysis"]
        
        # Verify cash recovery calculation
        total_investment = financial["total_investment"]
        refinance_amount = financial["refinance_amount"]
        cash_recovered = financial["cash_recovered"]
        
        assert cash_recovered == refinance_amount - total_investment
        
        # Check infinite return logic
        cash_left_in_deal = financial["cash_left_in_deal"]
        infinite_return = financial["infinite_return"]
        
        if cash_left_in_deal == 0:
            assert infinite_return is True
        else:
            assert infinite_return is False

class TestStrategyComparison:
    """Test strategy comparison endpoints"""
    
    def test_compare_all_strategies(self, created_property):
        """Test comparing all investment strategies"""
        property_id = created_property["id"]
        
        response = client.post(f"/api/v1/strategies/{property_id}/compare-strategies")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "strategies" in data
        assert "comparison" in data
        assert data["property_id"] == property_id
        
        strategies = data["strategies"]
        # Should include all default strategies
        expected_strategies = ["flip", "rental", "wholesale", "brrrr"]
        for strategy in expected_strategies:
            assert strategy in strategies
            if "error" not in strategies[strategy]:
                assert strategies[strategy]["strategy_type"] == strategy
        
        comparison = data["comparison"]
        if "error" not in comparison:
            assert "comparison_summary" in comparison
    
    def test_compare_selected_strategies(self, created_property):
        """Test comparing selected investment strategies"""
        property_id = created_property["id"]
        
        response = client.post(
            f"/api/v1/strategies/{property_id}/compare-strategies",
            params={
                "include_strategies": ["flip", "rental"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        strategies = data["strategies"]
        # Should only include requested strategies
        assert "flip" in strategies
        assert "rental" in strategies
        assert "wholesale" not in strategies
        assert "brrrr" not in strategies
    
    def test_compare_strategies_with_custom_price(self, created_property):
        """Test strategy comparison with custom purchase price"""
        property_id = created_property["id"]
        
        response = client.post(
            f"/api/v1/strategies/{property_id}/compare-strategies",
            params={
                "purchase_price": 240000,
                "include_strategies": ["flip", "rental", "wholesale"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        strategies = data["strategies"]
        # Verify custom purchase price was used in all strategies
        for strategy_name, strategy_data in strategies.items():
            if "error" not in strategy_data:
                financial = strategy_data["financial_analysis"]
                if "purchase_price" in financial:
                    assert financial["purchase_price"] == 240000

class TestStrategyValidation:
    """Test strategy analysis validation and error handling"""
    
    def test_analyze_strategy_nonexistent_property(self):
        """Test analyzing strategy for non-existent property"""
        fake_id = str(uuid.uuid4())
        
        response = client.post(f"/api/v1/strategies/{fake_id}/flip")
        assert response.status_code == 404
        assert "Property not found" in response.json()["detail"]
    
    def test_analyze_strategy_invalid_parameters(self, created_property):
        """Test strategy analysis with invalid parameters"""
        property_id = created_property["id"]
        
        # Test with negative purchase price
        response = client.post(
            f"/api/v1/strategies/{property_id}/flip",
            params={"purchase_price": -100000}
        )
        # Should handle gracefully or return validation error
        assert response.status_code in [200, 422]
        
        # Test with invalid down payment percentage
        response = client.post(
            f"/api/v1/strategies/{property_id}/rental",
            params={"down_payment_percentage": 1.5}  # 150% down payment
        )
        # Should handle gracefully or return validation error
        assert response.status_code in [200, 422]
    
    def test_compare_strategies_invalid_strategy_list(self, created_property):
        """Test strategy comparison with invalid strategy list"""
        property_id = created_property["id"]
        
        response = client.post(
            f"/api/v1/strategies/{property_id}/compare-strategies",
            params={"include_strategies": ["invalid_strategy", "flip"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include valid strategies and ignore invalid ones
        strategies = data["strategies"]
        assert "flip" in strategies
        assert "invalid_strategy" not in strategies

class TestStrategyRecommendations:
    """Test strategy recommendation logic"""
    
    def test_flip_recommendation_thresholds(self, created_property):
        """Test flip strategy recommendation thresholds"""
        property_id = created_property["id"]
        
        response = client.post(f"/api/v1/strategies/{property_id}/flip")
        
        assert response.status_code == 200
        data = response.json()
        strategy = data["strategy"]
        recommendation = strategy["recommendation"]
        
        # Check that thresholds are applied
        key_metrics = recommendation["key_metrics"]
        assert "min_profit_threshold" in key_metrics
        assert "min_roi_threshold" in key_metrics
        assert "max_risk_threshold" in key_metrics
        
        # Verify recommendation logic
        financial = strategy["financial_analysis"]
        risk = strategy["risk_assessment"]
        
        expected_proceed = (
            financial["net_profit"] > key_metrics["min_profit_threshold"] and
            financial["roi_percentage"] > key_metrics["min_roi_threshold"] and
            risk["risk_score"] < key_metrics["max_risk_threshold"]
        )
        
        assert recommendation["proceed"] == expected_proceed
    
    def test_rental_recommendation_thresholds(self, created_property):
        """Test rental strategy recommendation thresholds"""
        property_id = created_property["id"]
        
        response = client.post(f"/api/v1/strategies/{property_id}/rental")
        
        assert response.status_code == 200
        data = response.json()
        strategy = data["strategy"]
        recommendation = strategy["recommendation"]
        
        # Check rental-specific thresholds
        key_metrics = recommendation["key_metrics"]
        assert "min_cash_flow_threshold" in key_metrics
        assert "min_cap_rate_threshold" in key_metrics
        assert "min_coc_return_threshold" in key_metrics

# Cleanup
def teardown_module():
    """Clean up test database"""
    Base.metadata.drop_all(bind=engine)