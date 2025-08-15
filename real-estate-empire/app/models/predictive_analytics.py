"""
Predictive analytics data models for the Real Estate Empire platform.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlalchemy import Column, DateTime, Float, Integer, String, Boolean, Text, JSON, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from app.core.database import Base


class PredictionTypeEnum(str, Enum):
    """Enum for prediction types."""
    MARKET_TREND = "market_trend"
    PROPERTY_VALUE = "property_value"
    DEAL_OUTCOME = "deal_outcome"
    PORTFOLIO_PERFORMANCE = "portfolio_performance"
    RISK_ASSESSMENT = "risk_assessment"
    CASH_FLOW_FORECAST = "cash_flow_forecast"
    MARKET_TIMING = "market_timing"


class PredictionStatusEnum(str, Enum):
    """Enum for prediction status."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class RiskLevelEnum(str, Enum):
    """Enum for risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class MarketTrendDirectionEnum(str, Enum):
    """Enum for market trend directions."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"


class PredictiveModelDB(Base):
    """SQLAlchemy model for predictive models."""
    __tablename__ = "predictive_models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Model Information
    name = Column(String, nullable=False)
    model_type = Column(String, nullable=False)  # e.g., "linear_regression", "random_forest", "neural_network"
    prediction_type = Column(String, nullable=False)
    version = Column(String, nullable=False, default="1.0")
    
    # Model Performance
    accuracy_score = Column(Float, nullable=True)
    precision_score = Column(Float, nullable=True)
    recall_score = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    mae = Column(Float, nullable=True)
    r2_score = Column(Float, nullable=True)
    
    # Model Configuration
    features = Column(JSON, nullable=True)  # List of feature names
    hyperparameters = Column(JSON, nullable=True)
    training_data_size = Column(Integer, nullable=True)
    validation_data_size = Column(Integer, nullable=True)
    
    # Model Status
    is_active = Column(Boolean, default=True)
    is_production = Column(Boolean, default=False)
    last_trained = Column(DateTime, nullable=True)
    last_validated = Column(DateTime, nullable=True)
    
    # Model Storage
    model_path = Column(String, nullable=True)  # Path to serialized model
    model_settings = Column(JSON, nullable=True)
    
    # Relationships
    predictions = relationship("PredictionDB", back_populates="model")
    
    def __repr__(self):
        return f"<PredictiveModelDB(id={self.id}, name={self.name}, type={self.model_type})>"


class PredictionDB(Base):
    """SQLAlchemy model for predictions."""
    __tablename__ = "predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("predictive_models.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Prediction Details
    prediction_type = Column(String, nullable=False)
    target_entity_type = Column(String, nullable=False)  # e.g., "property", "portfolio", "market"
    target_entity_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Input Data
    input_features = Column(JSON, nullable=False)
    feature_importance = Column(JSON, nullable=True)
    
    # Prediction Results
    predicted_value = Column(Float, nullable=True)
    predicted_class = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    probability_distribution = Column(JSON, nullable=True)
    
    # Prediction Metadata
    prediction_horizon = Column(Integer, nullable=True)  # Days into the future
    prediction_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default=PredictionStatusEnum.COMPLETED)
    
    # Validation
    actual_value = Column(Float, nullable=True)
    actual_class = Column(String, nullable=True)
    validation_date = Column(DateTime, nullable=True)
    prediction_error = Column(Float, nullable=True)
    
    # Additional Data
    notes = Column(Text, nullable=True)
    prediction_metadata = Column(JSON, nullable=True)
    
    # Relationship
    model = relationship("PredictiveModelDB", back_populates="predictions")
    
    def __repr__(self):
        return f"<PredictionDB(id={self.id}, type={self.prediction_type}, value={self.predicted_value})>"


class MarketTrendPredictionDB(Base):
    """SQLAlchemy model for market trend predictions."""
    __tablename__ = "market_trend_predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("predictions.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Market Information
    market_area = Column(String, nullable=False)  # e.g., "Austin, TX"
    property_type = Column(String, nullable=True)
    price_segment = Column(String, nullable=True)  # e.g., "luxury", "affordable", "mid-range"
    
    # Trend Predictions
    trend_direction = Column(String, nullable=False)
    price_change_percent = Column(Float, nullable=True)
    volume_change_percent = Column(Float, nullable=True)
    days_on_market_change = Column(Float, nullable=True)
    
    # Confidence and Risk
    confidence_level = Column(Float, nullable=False)
    risk_factors = Column(JSON, nullable=True)
    supporting_indicators = Column(JSON, nullable=True)
    
    # Time Horizon
    forecast_start_date = Column(DateTime, nullable=False)
    forecast_end_date = Column(DateTime, nullable=False)
    
    def __repr__(self):
        return f"<MarketTrendPredictionDB(id={self.id}, market={self.market_area}, trend={self.trend_direction})>"


class DealOutcomePredictionDB(Base):
    """SQLAlchemy model for deal outcome predictions."""
    __tablename__ = "deal_outcome_predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("predictions.id"), nullable=False)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Deal Information
    deal_type = Column(String, nullable=False)  # e.g., "flip", "rental", "wholesale"
    offer_amount = Column(Float, nullable=False)
    estimated_repair_cost = Column(Float, nullable=True)
    
    # Outcome Predictions
    success_probability = Column(Float, nullable=False)
    expected_profit = Column(Float, nullable=True)
    expected_roi = Column(Float, nullable=True)
    time_to_completion = Column(Integer, nullable=True)  # Days
    
    # Risk Assessment
    risk_level = Column(String, nullable=False)
    risk_factors = Column(JSON, nullable=True)
    mitigation_strategies = Column(JSON, nullable=True)
    
    # Market Context
    market_conditions = Column(JSON, nullable=True)
    comparable_deals = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<DealOutcomePredictionDB(id={self.id}, deal_type={self.deal_type}, success_prob={self.success_probability})>"


class PortfolioForecastDB(Base):
    """SQLAlchemy model for portfolio performance forecasts."""
    __tablename__ = "portfolio_forecasts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("predictions.id"), nullable=False)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Forecast Period
    forecast_start_date = Column(DateTime, nullable=False)
    forecast_end_date = Column(DateTime, nullable=False)
    forecast_horizon_months = Column(Integer, nullable=False)
    
    # Financial Forecasts
    projected_value = Column(Float, nullable=True)
    projected_cash_flow = Column(Float, nullable=True)
    projected_roi = Column(Float, nullable=True)
    projected_appreciation = Column(Float, nullable=True)
    
    # Monthly Projections
    monthly_projections = Column(JSON, nullable=True)  # Array of monthly forecasts
    
    # Scenario Analysis
    best_case_scenario = Column(JSON, nullable=True)
    worst_case_scenario = Column(JSON, nullable=True)
    most_likely_scenario = Column(JSON, nullable=True)
    
    # Risk Metrics
    value_at_risk = Column(Float, nullable=True)
    expected_shortfall = Column(Float, nullable=True)
    volatility_estimate = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<PortfolioForecastDB(id={self.id}, portfolio_id={self.portfolio_id}, horizon={self.forecast_horizon_months}m)>"


class RiskAssessmentDB(Base):
    """SQLAlchemy model for risk assessments."""
    __tablename__ = "risk_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("predictions.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Assessment Target
    target_type = Column(String, nullable=False)  # "property", "portfolio", "deal"
    target_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Overall Risk Score
    overall_risk_score = Column(Float, nullable=False)  # 0-100 scale
    risk_level = Column(String, nullable=False)
    
    # Risk Categories
    market_risk_score = Column(Float, nullable=True)
    liquidity_risk_score = Column(Float, nullable=True)
    credit_risk_score = Column(Float, nullable=True)
    operational_risk_score = Column(Float, nullable=True)
    regulatory_risk_score = Column(Float, nullable=True)
    
    # Risk Factors
    identified_risks = Column(JSON, nullable=True)
    risk_mitigation_strategies = Column(JSON, nullable=True)
    
    # Stress Testing
    stress_test_results = Column(JSON, nullable=True)
    scenario_analysis = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<RiskAssessmentDB(id={self.id}, target_type={self.target_type}, risk_level={self.risk_level})>"


# Pydantic models for API requests and responses

class PredictiveModelCreate(BaseModel):
    """Pydantic model for creating a predictive model."""
    name: str
    model_type: str
    prediction_type: PredictionTypeEnum
    version: str = "1.0"
    features: Optional[List[str]] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class PredictiveModelResponse(BaseModel):
    """Pydantic model for predictive model API responses."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    name: str
    model_type: str
    prediction_type: PredictionTypeEnum
    version: str
    accuracy_score: Optional[float] = None
    precision_score: Optional[float] = None
    recall_score: Optional[float] = None
    f1_score: Optional[float] = None
    rmse: Optional[float] = None
    mae: Optional[float] = None
    r2_score: Optional[float] = None
    features: Optional[List[str]] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    training_data_size: Optional[int] = None
    validation_data_size: Optional[int] = None
    is_active: bool
    is_production: bool
    last_trained: Optional[datetime] = None
    last_validated: Optional[datetime] = None
    model_path: Optional[str] = None
    model_settings: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class PredictionRequest(BaseModel):
    """Pydantic model for prediction requests."""
    prediction_type: PredictionTypeEnum
    target_entity_type: str
    target_entity_id: Optional[uuid.UUID] = None
    input_features: Dict[str, Any]
    prediction_horizon: Optional[int] = None
    
    class Config:
        from_attributes = True


class PredictionResponse(BaseModel):
    """Pydantic model for prediction API responses."""
    id: uuid.UUID
    model_id: uuid.UUID
    created_at: datetime
    prediction_type: PredictionTypeEnum
    target_entity_type: str
    target_entity_id: Optional[uuid.UUID] = None
    input_features: Dict[str, Any]
    feature_importance: Optional[Dict[str, Any]] = None
    predicted_value: Optional[float] = None
    predicted_class: Optional[str] = None
    confidence_score: Optional[float] = None
    probability_distribution: Optional[Dict[str, Any]] = None
    prediction_horizon: Optional[int] = None
    prediction_date: datetime
    expiry_date: Optional[datetime] = None
    status: PredictionStatusEnum
    notes: Optional[str] = None
    prediction_metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class MarketTrendPredictionRequest(BaseModel):
    """Pydantic model for market trend prediction requests."""
    market_area: str
    property_type: Optional[str] = None
    price_segment: Optional[str] = None
    forecast_horizon_days: int = 90
    
    class Config:
        from_attributes = True


class MarketTrendPredictionResponse(BaseModel):
    """Pydantic model for market trend prediction responses."""
    id: uuid.UUID
    prediction_id: uuid.UUID
    created_at: datetime
    market_area: str
    property_type: Optional[str] = None
    price_segment: Optional[str] = None
    trend_direction: MarketTrendDirectionEnum
    price_change_percent: Optional[float] = None
    volume_change_percent: Optional[float] = None
    days_on_market_change: Optional[float] = None
    confidence_level: float
    risk_factors: Optional[List[str]] = None
    supporting_indicators: Optional[List[str]] = None
    forecast_start_date: datetime
    forecast_end_date: datetime
    
    class Config:
        from_attributes = True


class DealOutcomePredictionRequest(BaseModel):
    """Pydantic model for deal outcome prediction requests."""
    property_id: Optional[uuid.UUID] = None
    deal_type: str
    offer_amount: float
    estimated_repair_cost: Optional[float] = None
    property_features: Dict[str, Any]
    market_context: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class DealOutcomePredictionResponse(BaseModel):
    """Pydantic model for deal outcome prediction responses."""
    id: uuid.UUID
    prediction_id: uuid.UUID
    property_id: Optional[uuid.UUID] = None
    created_at: datetime
    deal_type: str
    offer_amount: float
    estimated_repair_cost: Optional[float] = None
    success_probability: float
    expected_profit: Optional[float] = None
    expected_roi: Optional[float] = None
    time_to_completion: Optional[int] = None
    risk_level: RiskLevelEnum
    risk_factors: Optional[List[str]] = None
    mitigation_strategies: Optional[List[str]] = None
    market_conditions: Optional[Dict[str, Any]] = None
    comparable_deals: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True


class PortfolioForecastRequest(BaseModel):
    """Pydantic model for portfolio forecast requests."""
    portfolio_id: uuid.UUID
    forecast_horizon_months: int = 12
    scenario_analysis: bool = True
    
    class Config:
        from_attributes = True


class PortfolioForecastResponse(BaseModel):
    """Pydantic model for portfolio forecast responses."""
    id: uuid.UUID
    prediction_id: uuid.UUID
    portfolio_id: uuid.UUID
    created_at: datetime
    forecast_start_date: datetime
    forecast_end_date: datetime
    forecast_horizon_months: int
    projected_value: Optional[float] = None
    projected_cash_flow: Optional[float] = None
    projected_roi: Optional[float] = None
    projected_appreciation: Optional[float] = None
    monthly_projections: Optional[List[Dict[str, Any]]] = None
    best_case_scenario: Optional[Dict[str, Any]] = None
    worst_case_scenario: Optional[Dict[str, Any]] = None
    most_likely_scenario: Optional[Dict[str, Any]] = None
    value_at_risk: Optional[float] = None
    expected_shortfall: Optional[float] = None
    volatility_estimate: Optional[float] = None
    
    class Config:
        from_attributes = True


class RiskAssessmentRequest(BaseModel):
    """Pydantic model for risk assessment requests."""
    target_type: str
    target_id: uuid.UUID
    include_stress_testing: bool = True
    include_scenario_analysis: bool = True
    
    class Config:
        from_attributes = True


class RiskAssessmentResponse(BaseModel):
    """Pydantic model for risk assessment responses."""
    id: uuid.UUID
    prediction_id: uuid.UUID
    created_at: datetime
    target_type: str
    target_id: uuid.UUID
    overall_risk_score: float
    risk_level: RiskLevelEnum
    market_risk_score: Optional[float] = None
    liquidity_risk_score: Optional[float] = None
    credit_risk_score: Optional[float] = None
    operational_risk_score: Optional[float] = None
    regulatory_risk_score: Optional[float] = None
    identified_risks: Optional[List[Dict[str, Any]]] = None
    risk_mitigation_strategies: Optional[List[Dict[str, Any]]] = None
    stress_test_results: Optional[Dict[str, Any]] = None
    scenario_analysis: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True