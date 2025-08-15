"""
Predictive Analytics Service for the Real Estate Empire platform.

This service provides machine learning-based predictions for:
- Market trend prediction
- Deal outcome prediction
- Portfolio performance forecasting
- Risk assessment automation
"""

import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score, precision_score, recall_score, f1_score
import joblib
import logging
from pathlib import Path

from app.models.predictive_analytics import (
    PredictiveModelDB, PredictionDB, MarketTrendPredictionDB, 
    DealOutcomePredictionDB, PortfolioForecastDB, RiskAssessmentDB,
    PredictionTypeEnum, PredictionStatusEnum, RiskLevelEnum, MarketTrendDirectionEnum,
    PredictionRequest, PredictionResponse, MarketTrendPredictionRequest, MarketTrendPredictionResponse,
    DealOutcomePredictionRequest, DealOutcomePredictionResponse,
    PortfolioForecastRequest, PortfolioForecastResponse,
    RiskAssessmentRequest, RiskAssessmentResponse
)
from app.models.portfolio import PortfolioDB, PortfolioPropertyDB, PropertyPerformanceDB
from app.models.property import PropertyDB
from app.services.market_data_service import MarketDataService
from app.services.portfolio_performance_service import PortfolioPerformanceService

logger = logging.getLogger(__name__)


class PredictiveAnalyticsService:
    """Service for predictive analytics and machine learning predictions."""
    
    def __init__(self, db: Session):
        self.db = db
        self.market_data_service = MarketDataService()
        self.portfolio_service = PortfolioPerformanceService(db)
        self.models_dir = Path("models/predictive")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize scalers and encoders
        self.scalers = {}
        self.encoders = {}
        
        # Model cache
        self._model_cache = {}
    
    def predict_market_trend(self, request: MarketTrendPredictionRequest) -> MarketTrendPredictionResponse:
        """Predict market trends for a specific area."""
        try:
            # Get or create market trend model
            model = self._get_or_create_model("market_trend", "random_forest")
            
            # Prepare features for prediction
            features = self._prepare_market_trend_features(request)
            
            # Make prediction
            prediction_data = self._make_prediction(model, features, PredictionTypeEnum.MARKET_TREND)
            
            # Interpret prediction results
            trend_direction = self._interpret_market_trend(prediction_data["predicted_value"])
            price_change = self._calculate_price_change_forecast(features, prediction_data["predicted_value"])
            
            # Create prediction record
            prediction_db = PredictionDB(
                model_id=model.id,
                prediction_type=PredictionTypeEnum.MARKET_TREND,
                target_entity_type="market",
                input_features=features,
                predicted_value=prediction_data["predicted_value"],
                confidence_score=prediction_data["confidence_score"],
                prediction_horizon=request.forecast_horizon_days,
                prediction_date=datetime.utcnow(),
                expiry_date=datetime.utcnow() + timedelta(days=request.forecast_horizon_days)
            )
            self.db.add(prediction_db)
            self.db.flush()
            
            # Create market trend prediction record
            market_trend_db = MarketTrendPredictionDB(
                prediction_id=prediction_db.id,
                market_area=request.market_area,
                property_type=request.property_type,
                price_segment=request.price_segment,
                trend_direction=trend_direction,
                price_change_percent=price_change,
                confidence_level=prediction_data["confidence_score"],
                risk_factors=self._identify_market_risk_factors(features),
                supporting_indicators=self._get_supporting_indicators(features),
                forecast_start_date=datetime.utcnow(),
                forecast_end_date=datetime.utcnow() + timedelta(days=request.forecast_horizon_days)
            )
            self.db.add(market_trend_db)
            self.db.commit()
            
            return MarketTrendPredictionResponse(
                id=market_trend_db.id,
                prediction_id=prediction_db.id,
                created_at=market_trend_db.created_at,
                market_area=request.market_area,
                property_type=request.property_type,
                price_segment=request.price_segment,
                trend_direction=trend_direction,
                price_change_percent=price_change,
                confidence_level=prediction_data["confidence_score"],
                risk_factors=market_trend_db.risk_factors,
                supporting_indicators=market_trend_db.supporting_indicators,
                forecast_start_date=market_trend_db.forecast_start_date,
                forecast_end_date=market_trend_db.forecast_end_date
            )
            
        except Exception as e:
            logger.error(f"Error predicting market trend: {str(e)}")
            raise
    
    def predict_deal_outcome(self, request: DealOutcomePredictionRequest) -> DealOutcomePredictionResponse:
        """Predict the outcome of a real estate deal."""
        try:
            # Get or create deal outcome model
            model = self._get_or_create_model("deal_outcome", "random_forest_classifier")
            
            # Prepare features for prediction
            features = self._prepare_deal_outcome_features(request)
            
            # Make prediction
            prediction_data = self._make_prediction(model, features, PredictionTypeEnum.DEAL_OUTCOME)
            
            # Calculate deal metrics
            success_probability = prediction_data["confidence_score"]
            expected_profit = self._calculate_expected_profit(request, features)
            expected_roi = self._calculate_expected_roi(request, expected_profit)
            time_to_completion = self._estimate_completion_time(request.deal_type, features)
            risk_level = self._assess_deal_risk_level(features, success_probability)
            
            # Create prediction record
            prediction_db = PredictionDB(
                model_id=model.id,
                prediction_type=PredictionTypeEnum.DEAL_OUTCOME,
                target_entity_type="deal",
                target_entity_id=request.property_id,
                input_features=features,
                predicted_value=success_probability,
                confidence_score=prediction_data["confidence_score"],
                prediction_date=datetime.utcnow()
            )
            self.db.add(prediction_db)
            self.db.flush()
            
            # Create deal outcome prediction record
            deal_outcome_db = DealOutcomePredictionDB(
                prediction_id=prediction_db.id,
                property_id=request.property_id,
                deal_type=request.deal_type,
                offer_amount=request.offer_amount,
                estimated_repair_cost=request.estimated_repair_cost,
                success_probability=success_probability,
                expected_profit=expected_profit,
                expected_roi=expected_roi,
                time_to_completion=time_to_completion,
                risk_level=risk_level,
                risk_factors=self._identify_deal_risk_factors(features),
                mitigation_strategies=self._suggest_mitigation_strategies(risk_level, features),
                market_conditions=self._get_market_conditions(request.market_context),
                comparable_deals=self._find_comparable_deals(request)
            )
            self.db.add(deal_outcome_db)
            self.db.commit()
            
            return DealOutcomePredictionResponse(
                id=deal_outcome_db.id,
                prediction_id=prediction_db.id,
                property_id=request.property_id,
                created_at=deal_outcome_db.created_at,
                deal_type=request.deal_type,
                offer_amount=request.offer_amount,
                estimated_repair_cost=request.estimated_repair_cost,
                success_probability=success_probability,
                expected_profit=expected_profit,
                expected_roi=expected_roi,
                time_to_completion=time_to_completion,
                risk_level=risk_level,
                risk_factors=deal_outcome_db.risk_factors,
                mitigation_strategies=deal_outcome_db.mitigation_strategies,
                market_conditions=deal_outcome_db.market_conditions,
                comparable_deals=deal_outcome_db.comparable_deals
            )
            
        except Exception as e:
            logger.error(f"Error predicting deal outcome: {str(e)}")
            raise
    
    def forecast_portfolio_performance(self, request: PortfolioForecastRequest) -> PortfolioForecastResponse:
        """Forecast portfolio performance over time."""
        try:
            # Get or create portfolio performance model
            model = self._get_or_create_model("portfolio_performance", "random_forest")
            
            # Get portfolio data
            portfolio = self.db.query(PortfolioDB).filter(PortfolioDB.id == request.portfolio_id).first()
            if not portfolio:
                raise ValueError(f"Portfolio {request.portfolio_id} not found")
            
            # Prepare features for prediction
            features = self._prepare_portfolio_features(portfolio)
            
            # Generate monthly forecasts
            monthly_projections = []
            current_date = datetime.utcnow()
            
            for month in range(request.forecast_horizon_months):
                forecast_date = current_date + timedelta(days=30 * month)
                month_features = features.copy()
                month_features["forecast_month"] = month
                month_features["forecast_date"] = forecast_date.timestamp()
                
                prediction_data = self._make_prediction(model, month_features, PredictionTypeEnum.PORTFOLIO_PERFORMANCE)
                
                monthly_projections.append({
                    "month": month + 1,
                    "date": forecast_date.isoformat(),
                    "projected_value": prediction_data["predicted_value"],
                    "confidence": prediction_data["confidence_score"]
                })
            
            # Calculate aggregate projections
            final_projection = monthly_projections[-1]
            projected_value = final_projection["projected_value"]
            projected_appreciation = ((projected_value - portfolio.total_value) / portfolio.total_value) * 100
            projected_cash_flow = self._project_cash_flow(portfolio, request.forecast_horizon_months)
            projected_roi = self._calculate_projected_roi(portfolio, projected_value, projected_cash_flow)
            
            # Scenario analysis
            scenarios = {}
            if request.scenario_analysis:
                scenarios = self._generate_portfolio_scenarios(portfolio, features, request.forecast_horizon_months)
            
            # Risk metrics
            risk_metrics = self._calculate_portfolio_risk_metrics(portfolio, monthly_projections)
            
            # Create prediction record
            prediction_db = PredictionDB(
                model_id=model.id,
                prediction_type=PredictionTypeEnum.PORTFOLIO_PERFORMANCE,
                target_entity_type="portfolio",
                target_entity_id=request.portfolio_id,
                input_features=features,
                predicted_value=projected_value,
                confidence_score=np.mean([p["confidence"] for p in monthly_projections]),
                prediction_horizon=request.forecast_horizon_months * 30,
                prediction_date=datetime.utcnow(),
                expiry_date=datetime.utcnow() + timedelta(days=request.forecast_horizon_months * 30)
            )
            self.db.add(prediction_db)
            self.db.flush()
            
            # Create portfolio forecast record
            forecast_db = PortfolioForecastDB(
                prediction_id=prediction_db.id,
                portfolio_id=request.portfolio_id,
                forecast_start_date=datetime.utcnow(),
                forecast_end_date=datetime.utcnow() + timedelta(days=request.forecast_horizon_months * 30),
                forecast_horizon_months=request.forecast_horizon_months,
                projected_value=projected_value,
                projected_cash_flow=projected_cash_flow,
                projected_roi=projected_roi,
                projected_appreciation=projected_appreciation,
                monthly_projections=monthly_projections,
                best_case_scenario=scenarios.get("best_case"),
                worst_case_scenario=scenarios.get("worst_case"),
                most_likely_scenario=scenarios.get("most_likely"),
                value_at_risk=risk_metrics.get("value_at_risk"),
                expected_shortfall=risk_metrics.get("expected_shortfall"),
                volatility_estimate=risk_metrics.get("volatility")
            )
            self.db.add(forecast_db)
            self.db.commit()
            
            return PortfolioForecastResponse(
                id=forecast_db.id,
                prediction_id=prediction_db.id,
                portfolio_id=request.portfolio_id,
                created_at=forecast_db.created_at,
                forecast_start_date=forecast_db.forecast_start_date,
                forecast_end_date=forecast_db.forecast_end_date,
                forecast_horizon_months=request.forecast_horizon_months,
                projected_value=projected_value,
                projected_cash_flow=projected_cash_flow,
                projected_roi=projected_roi,
                projected_appreciation=projected_appreciation,
                monthly_projections=monthly_projections,
                best_case_scenario=scenarios.get("best_case"),
                worst_case_scenario=scenarios.get("worst_case"),
                most_likely_scenario=scenarios.get("most_likely"),
                value_at_risk=risk_metrics.get("value_at_risk"),
                expected_shortfall=risk_metrics.get("expected_shortfall"),
                volatility_estimate=risk_metrics.get("volatility")
            )
            
        except Exception as e:
            logger.error(f"Error forecasting portfolio performance: {str(e)}")
            raise
    
    def assess_risk(self, request: RiskAssessmentRequest) -> RiskAssessmentResponse:
        """Perform comprehensive risk assessment."""
        try:
            # Get or create risk assessment model
            model = self._get_or_create_model("risk_assessment", "random_forest")
            
            # Prepare features based on target type
            features = self._prepare_risk_assessment_features(request)
            
            # Make prediction
            prediction_data = self._make_prediction(model, features, PredictionTypeEnum.RISK_ASSESSMENT)
            
            # Calculate risk scores
            overall_risk_score = prediction_data["predicted_value"]
            risk_level = self._determine_risk_level(overall_risk_score)
            
            # Calculate category-specific risk scores
            risk_scores = self._calculate_category_risk_scores(features)
            
            # Identify risks and mitigation strategies
            identified_risks = self._identify_risks(features, overall_risk_score)
            mitigation_strategies = self._suggest_risk_mitigation(identified_risks, request.target_type)
            
            # Stress testing and scenario analysis
            stress_test_results = {}
            scenario_analysis = {}
            
            if request.include_stress_testing:
                stress_test_results = self._perform_stress_testing(features, request.target_type)
            
            if request.include_scenario_analysis:
                scenario_analysis = self._perform_risk_scenario_analysis(features, request.target_type)
            
            # Create prediction record
            prediction_db = PredictionDB(
                model_id=model.id,
                prediction_type=PredictionTypeEnum.RISK_ASSESSMENT,
                target_entity_type=request.target_type,
                target_entity_id=request.target_id,
                input_features=features,
                predicted_value=overall_risk_score,
                confidence_score=prediction_data["confidence_score"],
                prediction_date=datetime.utcnow()
            )
            self.db.add(prediction_db)
            self.db.flush()
            
            # Create risk assessment record
            risk_assessment_db = RiskAssessmentDB(
                prediction_id=prediction_db.id,
                target_type=request.target_type,
                target_id=request.target_id,
                overall_risk_score=overall_risk_score,
                risk_level=risk_level,
                market_risk_score=risk_scores.get("market_risk"),
                liquidity_risk_score=risk_scores.get("liquidity_risk"),
                credit_risk_score=risk_scores.get("credit_risk"),
                operational_risk_score=risk_scores.get("operational_risk"),
                regulatory_risk_score=risk_scores.get("regulatory_risk"),
                identified_risks=identified_risks,
                risk_mitigation_strategies=mitigation_strategies,
                stress_test_results=stress_test_results,
                scenario_analysis=scenario_analysis
            )
            self.db.add(risk_assessment_db)
            self.db.commit()
            
            return RiskAssessmentResponse(
                id=risk_assessment_db.id,
                prediction_id=prediction_db.id,
                created_at=risk_assessment_db.created_at,
                target_type=request.target_type,
                target_id=request.target_id,
                overall_risk_score=overall_risk_score,
                risk_level=risk_level,
                market_risk_score=risk_scores.get("market_risk"),
                liquidity_risk_score=risk_scores.get("liquidity_risk"),
                credit_risk_score=risk_scores.get("credit_risk"),
                operational_risk_score=risk_scores.get("operational_risk"),
                regulatory_risk_score=risk_scores.get("regulatory_risk"),
                identified_risks=identified_risks,
                risk_mitigation_strategies=mitigation_strategies,
                stress_test_results=stress_test_results,
                scenario_analysis=scenario_analysis
            )
            
        except Exception as e:
            logger.error(f"Error assessing risk: {str(e)}")
            raise
    
    def _get_or_create_model(self, model_name: str, model_type: str) -> PredictiveModelDB:
        """Get existing model or create a new one."""
        # Check cache first
        cache_key = f"{model_name}_{model_type}"
        if cache_key in self._model_cache:
            return self._model_cache[cache_key]
        
        # Check database
        model = self.db.query(PredictiveModelDB).filter(
            PredictiveModelDB.name == model_name,
            PredictiveModelDB.model_type == model_type,
            PredictiveModelDB.is_active == True
        ).first()
        
        if not model:
            # Create new model
            model = self._create_and_train_model(model_name, model_type)
        
        # Cache the model
        self._model_cache[cache_key] = model
        return model
    
    def _create_and_train_model(self, model_name: str, model_type: str) -> PredictiveModelDB:
        """Create and train a new predictive model."""
        logger.info(f"Creating and training new model: {model_name} ({model_type})")
        
        # Generate training data
        training_data = self._generate_training_data(model_name)
        
        if training_data is None or len(training_data) < 10:
            # Create a basic model with default parameters for now
            logger.warning(f"Insufficient training data for {model_name}, creating basic model")
            model_db = PredictiveModelDB(
                name=model_name,
                model_type=model_type,
                prediction_type=self._get_prediction_type_for_model(model_name),
                version="1.0",
                is_active=True,
                is_production=False,
                last_trained=datetime.utcnow()
            )
            self.db.add(model_db)
            self.db.commit()
            return model_db
        
        # Split data
        X = training_data.drop(['target'], axis=1)
        y = training_data['target']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Create and train model
        if "classifier" in model_type:
            if model_type == "random_forest_classifier":
                ml_model = RandomForestClassifier(n_estimators=100, random_state=42)
            else:
                ml_model = LogisticRegression(random_state=42)
        else:
            if model_type == "random_forest":
                ml_model = RandomForestRegressor(n_estimators=100, random_state=42)
            else:
                ml_model = LinearRegression()
        
        # Scale features if needed
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        ml_model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        y_pred = ml_model.predict(X_test_scaled)
        
        # Calculate metrics
        metrics = {}
        if "classifier" in model_type:
            metrics = {
                "accuracy_score": accuracy_score(y_test, y_pred),
                "precision_score": precision_score(y_test, y_pred, average='weighted'),
                "recall_score": recall_score(y_test, y_pred, average='weighted'),
                "f1_score": f1_score(y_test, y_pred, average='weighted')
            }
        else:
            metrics = {
                "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
                "mae": mean_absolute_error(y_test, y_pred),
                "r2_score": r2_score(y_test, y_pred)
            }
        
        # Save model
        model_path = self.models_dir / f"{model_name}_{model_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.joblib"
        joblib.dump({
            'model': ml_model,
            'scaler': scaler,
            'features': list(X.columns)
        }, model_path)
        
        # Create database record
        model_db = PredictiveModelDB(
            name=model_name,
            model_type=model_type,
            prediction_type=self._get_prediction_type_for_model(model_name),
            version="1.0",
            features=list(X.columns),
            training_data_size=len(X_train),
            validation_data_size=len(X_test),
            is_active=True,
            is_production=True,
            last_trained=datetime.utcnow(),
            last_validated=datetime.utcnow(),
            model_path=str(model_path),
            **metrics
        )
        self.db.add(model_db)
        self.db.commit()
        
        logger.info(f"Successfully trained model {model_name} with metrics: {metrics}")
        return model_db
    
    def _make_prediction(self, model: PredictiveModelDB, features: Dict[str, Any], prediction_type: PredictionTypeEnum) -> Dict[str, Any]:
        """Make a prediction using the specified model."""
        try:
            # Load the trained model
            if model.model_path and Path(model.model_path).exists():
                model_data = joblib.load(model.model_path)
                ml_model = model_data['model']
                scaler = model_data['scaler']
                feature_names = model_data['features']
            else:
                # Use a simple heuristic-based prediction if no trained model exists
                return self._make_heuristic_prediction(features, prediction_type)
            
            # Prepare feature vector
            feature_vector = []
            for feature_name in feature_names:
                feature_vector.append(features.get(feature_name, 0))
            
            # Scale features
            feature_vector_scaled = scaler.transform([feature_vector])
            
            # Make prediction
            prediction = ml_model.predict(feature_vector_scaled)[0]
            
            # Calculate confidence score
            if hasattr(ml_model, 'predict_proba'):
                probabilities = ml_model.predict_proba(feature_vector_scaled)[0]
                confidence_score = max(probabilities)
            else:
                # For regression models, use a simple confidence metric
                confidence_score = min(0.95, max(0.5, 1.0 - abs(prediction) / 1000000))
            
            return {
                "predicted_value": float(prediction),
                "confidence_score": float(confidence_score)
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            # Fallback to heuristic prediction
            return self._make_heuristic_prediction(features, prediction_type)
    
    def _make_heuristic_prediction(self, features: Dict[str, Any], prediction_type: PredictionTypeEnum) -> Dict[str, Any]:
        """Make a heuristic-based prediction when ML model is not available."""
        if prediction_type == PredictionTypeEnum.MARKET_TREND:
            # Simple market trend heuristic
            price_trend = features.get("price_trend", 0)
            volume_trend = features.get("volume_trend", 0)
            prediction = (price_trend + volume_trend) / 2
            confidence = 0.6
        elif prediction_type == PredictionTypeEnum.DEAL_OUTCOME:
            # Simple deal outcome heuristic
            profit_margin = features.get("profit_margin", 0)
            market_strength = features.get("market_strength", 0.5)
            prediction = min(0.9, max(0.1, (profit_margin * 0.6 + market_strength * 0.4)))
            confidence = 0.7
        elif prediction_type == PredictionTypeEnum.PORTFOLIO_PERFORMANCE:
            # Simple portfolio performance heuristic
            current_performance = features.get("current_performance", 0)
            market_conditions = features.get("market_conditions", 0.5)
            prediction = current_performance * (1 + market_conditions * 0.1)
            confidence = 0.65
        else:
            # Default prediction
            prediction = 0.5
            confidence = 0.5
        
        return {
            "predicted_value": float(prediction),
            "confidence_score": float(confidence)
        }
    
    # Feature preparation methods
    def _prepare_market_trend_features(self, request: MarketTrendPredictionRequest) -> Dict[str, Any]:
        """Prepare features for market trend prediction."""
        # Get market data
        city, state = request.market_area.split(", ") if ", " in request.market_area else (request.market_area, "")
        market_stats = self.market_data_service.get_market_stats(city, state)
        
        features = {
            "avg_price": market_stats.avg_price if market_stats else 300000,
            "median_price": market_stats.median_price if market_stats else 280000,
            "avg_price_per_sqft": market_stats.avg_price_per_sqft if market_stats else 150,
            "total_listings": market_stats.total_listings if market_stats else 100,
            "avg_bedrooms": market_stats.avg_bedrooms if market_stats else 3,
            "avg_bathrooms": market_stats.avg_bathrooms if market_stats else 2,
            "forecast_horizon": request.forecast_horizon_days,
            "month": datetime.utcnow().month,
            "quarter": (datetime.utcnow().month - 1) // 3 + 1,
            "price_trend": np.random.normal(0, 0.1),  # Placeholder
            "volume_trend": np.random.normal(0, 0.1),  # Placeholder
            "economic_indicator": np.random.normal(0.5, 0.2)  # Placeholder
        }
        
        return features
    
    def _prepare_deal_outcome_features(self, request: DealOutcomePredictionRequest) -> Dict[str, Any]:
        """Prepare features for deal outcome prediction."""
        features = {
            "offer_amount": request.offer_amount,
            "estimated_repair_cost": request.estimated_repair_cost or 0,
            "deal_type_flip": 1 if request.deal_type == "flip" else 0,
            "deal_type_rental": 1 if request.deal_type == "rental" else 0,
            "deal_type_wholesale": 1 if request.deal_type == "wholesale" else 0,
        }
        
        # Add property features
        for key, value in request.property_features.items():
            if isinstance(value, (int, float)):
                features[f"property_{key}"] = value
            elif isinstance(value, bool):
                features[f"property_{key}"] = 1 if value else 0
        
        # Add market context
        if request.market_context:
            for key, value in request.market_context.items():
                if isinstance(value, (int, float)):
                    features[f"market_{key}"] = value
        
        # Calculate derived features
        features["profit_margin"] = (features.get("property_arv", request.offer_amount) - request.offer_amount - features["estimated_repair_cost"]) / request.offer_amount
        features["market_strength"] = np.random.uniform(0.3, 0.8)  # Placeholder
        
        return features
    
    def _prepare_portfolio_features(self, portfolio: PortfolioDB) -> Dict[str, Any]:
        """Prepare features for portfolio performance prediction."""
        features = {
            "total_properties": portfolio.total_properties,
            "total_value": portfolio.total_value,
            "total_equity": portfolio.total_equity,
            "monthly_cash_flow": portfolio.monthly_cash_flow,
            "average_cap_rate": portfolio.average_cap_rate or 0,
            "average_coc_return": portfolio.average_coc_return or 0,
            "diversification_score": portfolio.diversification_score or 0.5,
            "risk_score": portfolio.risk_score or 0.5,
            "portfolio_age_days": (datetime.utcnow() - portfolio.created_at).days,
            "current_performance": portfolio.total_return_ytd or 0,
            "market_conditions": np.random.uniform(0.3, 0.8)  # Placeholder
        }
        
        return features
    
    def _prepare_risk_assessment_features(self, request: RiskAssessmentRequest) -> Dict[str, Any]:
        """Prepare features for risk assessment."""
        features = {
            "target_type": request.target_type,
            "assessment_date": datetime.utcnow().timestamp(),
        }
        
        if request.target_type == "property":
            property_obj = self.db.query(PropertyDB).filter(PropertyDB.id == request.target_id).first()
            if property_obj:
                features.update({
                    "property_value": property_obj.current_value or 0,
                    "property_age": (datetime.utcnow().year - (property_obj.year_built or 2000)),
                    "days_on_market": property_obj.days_on_market or 0,
                    "condition_score": property_obj.condition_score or 0.5,
                    "crime_score": property_obj.crime_score or 50
                })
        elif request.target_type == "portfolio":
            portfolio = self.db.query(PortfolioDB).filter(PortfolioDB.id == request.target_id).first()
            if portfolio:
                features.update(self._prepare_portfolio_features(portfolio))
        
        # Add market risk factors
        features.update({
            "market_volatility": np.random.uniform(0.1, 0.5),  # Placeholder
            "interest_rate_risk": np.random.uniform(0.2, 0.6),  # Placeholder
            "liquidity_risk": np.random.uniform(0.1, 0.4),  # Placeholder
        })
        
        return features
    
    # Helper methods for interpretation and calculation
    def _interpret_market_trend(self, predicted_value: float) -> MarketTrendDirectionEnum:
        """Interpret market trend prediction."""
        if predicted_value > 0.6:
            return MarketTrendDirectionEnum.BULLISH
        elif predicted_value < 0.4:
            return MarketTrendDirectionEnum.BEARISH
        elif abs(predicted_value - 0.5) < 0.05:
            return MarketTrendDirectionEnum.SIDEWAYS
        else:
            return MarketTrendDirectionEnum.VOLATILE
    
    def _calculate_price_change_forecast(self, features: Dict[str, Any], predicted_value: float) -> float:
        """Calculate price change forecast."""
        base_change = (predicted_value - 0.5) * 20  # Convert to percentage
        market_factor = features.get("price_trend", 0) * 10
        return base_change + market_factor
    
    def _assess_deal_risk_level(self, features: Dict[str, Any], success_probability: float) -> RiskLevelEnum:
        """Assess deal risk level."""
        if success_probability > 0.8:
            return RiskLevelEnum.LOW
        elif success_probability > 0.6:
            return RiskLevelEnum.MEDIUM
        elif success_probability > 0.4:
            return RiskLevelEnum.HIGH
        else:
            return RiskLevelEnum.VERY_HIGH
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevelEnum:
        """Determine risk level from score."""
        if risk_score < 25:
            return RiskLevelEnum.LOW
        elif risk_score < 50:
            return RiskLevelEnum.MEDIUM
        elif risk_score < 75:
            return RiskLevelEnum.HIGH
        else:
            return RiskLevelEnum.VERY_HIGH
    
    # Placeholder methods for complex calculations
    def _generate_training_data(self, model_name: str) -> Optional[pd.DataFrame]:
        """Generate training data for the model."""
        # This would typically load historical data from the database
        # For now, return None to trigger heuristic predictions
        return None
    
    def _get_prediction_type_for_model(self, model_name: str) -> PredictionTypeEnum:
        """Get prediction type enum for model name."""
        mapping = {
            "market_trend": PredictionTypeEnum.MARKET_TREND,
            "deal_outcome": PredictionTypeEnum.DEAL_OUTCOME,
            "portfolio_performance": PredictionTypeEnum.PORTFOLIO_PERFORMANCE,
            "risk_assessment": PredictionTypeEnum.RISK_ASSESSMENT
        }
        return mapping.get(model_name, PredictionTypeEnum.MARKET_TREND)
    
    def _identify_market_risk_factors(self, features: Dict[str, Any]) -> List[str]:
        """Identify market risk factors."""
        risk_factors = []
        if features.get("total_listings", 0) > 1000:
            risk_factors.append("High inventory levels")
        if features.get("price_trend", 0) < -0.1:
            risk_factors.append("Declining price trend")
        return risk_factors
    
    def _get_supporting_indicators(self, features: Dict[str, Any]) -> List[str]:
        """Get supporting indicators for market trend."""
        indicators = []
        if features.get("volume_trend", 0) > 0.1:
            indicators.append("Increasing transaction volume")
        if features.get("economic_indicator", 0.5) > 0.6:
            indicators.append("Strong economic conditions")
        return indicators
    
    def _calculate_expected_profit(self, request: DealOutcomePredictionRequest, features: Dict[str, Any]) -> float:
        """Calculate expected profit for a deal."""
        arv = features.get("property_arv", request.offer_amount * 1.2)
        total_cost = request.offer_amount + (request.estimated_repair_cost or 0)
        return max(0, arv - total_cost)
    
    def _calculate_expected_roi(self, request: DealOutcomePredictionRequest, expected_profit: float) -> float:
        """Calculate expected ROI for a deal."""
        if request.offer_amount > 0:
            return (expected_profit / request.offer_amount) * 100
        return 0
    
    def _estimate_completion_time(self, deal_type: str, features: Dict[str, Any]) -> int:
        """Estimate completion time for a deal."""
        base_times = {
            "flip": 120,  # 4 months
            "rental": 60,  # 2 months
            "wholesale": 30  # 1 month
        }
        return base_times.get(deal_type, 90)
    
    def _identify_deal_risk_factors(self, features: Dict[str, Any]) -> List[str]:
        """Identify risk factors for a deal."""
        risk_factors = []
        if features.get("profit_margin", 0) < 0.1:
            risk_factors.append("Low profit margin")
        if features.get("estimated_repair_cost", 0) > features.get("offer_amount", 0) * 0.3:
            risk_factors.append("High repair costs")
        return risk_factors
    
    def _suggest_mitigation_strategies(self, risk_level: RiskLevelEnum, features: Dict[str, Any]) -> List[str]:
        """Suggest risk mitigation strategies."""
        strategies = []
        if risk_level in [RiskLevelEnum.HIGH, RiskLevelEnum.VERY_HIGH]:
            strategies.append("Conduct thorough due diligence")
            strategies.append("Negotiate lower purchase price")
            strategies.append("Secure contingency funding")
        return strategies
    
    def _get_market_conditions(self, market_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Get current market conditions."""
        return market_context or {
            "market_strength": "moderate",
            "inventory_levels": "normal",
            "price_trends": "stable"
        }
    
    def _find_comparable_deals(self, request: DealOutcomePredictionRequest) -> List[Dict[str, Any]]:
        """Find comparable deals."""
        # This would typically query historical deal data
        return [
            {
                "deal_type": request.deal_type,
                "offer_amount": request.offer_amount * 0.95,
                "outcome": "successful",
                "profit": request.offer_amount * 0.15
            }
        ]
    
    def _project_cash_flow(self, portfolio: PortfolioDB, months: int) -> float:
        """Project cash flow for portfolio."""
        monthly_cash_flow = portfolio.monthly_cash_flow or 0
        growth_rate = 0.02  # 2% monthly growth assumption
        total_projected = 0
        
        for month in range(months):
            monthly_amount = monthly_cash_flow * (1 + growth_rate) ** month
            total_projected += monthly_amount
        
        return total_projected
    
    def _calculate_projected_roi(self, portfolio: PortfolioDB, projected_value: float, projected_cash_flow: float) -> float:
        """Calculate projected ROI for portfolio."""
        if portfolio.total_value > 0:
            total_return = (projected_value - portfolio.total_value) + projected_cash_flow
            return (total_return / portfolio.total_value) * 100
        return 0
    
    def _generate_portfolio_scenarios(self, portfolio: PortfolioDB, features: Dict[str, Any], months: int) -> Dict[str, Any]:
        """Generate portfolio scenarios."""
        base_value = portfolio.total_value
        
        return {
            "best_case": {
                "projected_value": base_value * 1.2,
                "probability": 0.1,
                "assumptions": ["Strong market growth", "All properties perform well"]
            },
            "worst_case": {
                "projected_value": base_value * 0.8,
                "probability": 0.1,
                "assumptions": ["Market downturn", "High vacancy rates"]
            },
            "most_likely": {
                "projected_value": base_value * 1.05,
                "probability": 0.8,
                "assumptions": ["Moderate market growth", "Normal performance"]
            }
        }
    
    def _calculate_portfolio_risk_metrics(self, portfolio: PortfolioDB, projections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate portfolio risk metrics."""
        values = [p["projected_value"] for p in projections]
        
        return {
            "value_at_risk": np.percentile(values, 5),  # 5% VaR
            "expected_shortfall": np.mean([v for v in values if v <= np.percentile(values, 5)]),
            "volatility": np.std(values) / np.mean(values) if values else 0
        }
    
    def _calculate_category_risk_scores(self, features: Dict[str, Any]) -> Dict[str, float]:
        """Calculate category-specific risk scores."""
        return {
            "market_risk": features.get("market_volatility", 0.3) * 100,
            "liquidity_risk": features.get("liquidity_risk", 0.2) * 100,
            "credit_risk": features.get("interest_rate_risk", 0.3) * 100,
            "operational_risk": np.random.uniform(10, 40),  # Placeholder
            "regulatory_risk": np.random.uniform(5, 25)  # Placeholder
        }
    
    def _identify_risks(self, features: Dict[str, Any], risk_score: float) -> List[Dict[str, Any]]:
        """Identify specific risks."""
        risks = []
        
        if risk_score > 60:
            risks.append({
                "type": "Market Risk",
                "severity": "High",
                "description": "High market volatility detected",
                "impact": "Potential value decline"
            })
        
        if features.get("liquidity_risk", 0) > 0.3:
            risks.append({
                "type": "Liquidity Risk",
                "severity": "Medium",
                "description": "Limited market liquidity",
                "impact": "Difficulty selling assets quickly"
            })
        
        return risks
    
    def _suggest_risk_mitigation(self, risks: List[Dict[str, Any]], target_type: str) -> List[Dict[str, Any]]:
        """Suggest risk mitigation strategies."""
        strategies = []
        
        for risk in risks:
            if risk["type"] == "Market Risk":
                strategies.append({
                    "risk_type": "Market Risk",
                    "strategy": "Diversify across multiple markets",
                    "priority": "High",
                    "timeline": "Immediate"
                })
            elif risk["type"] == "Liquidity Risk":
                strategies.append({
                    "risk_type": "Liquidity Risk",
                    "strategy": "Maintain cash reserves",
                    "priority": "Medium",
                    "timeline": "Short-term"
                })
        
        return strategies
    
    def _perform_stress_testing(self, features: Dict[str, Any], target_type: str) -> Dict[str, Any]:
        """Perform stress testing."""
        return {
            "market_crash_scenario": {
                "value_decline": -30,
                "probability": 0.05,
                "impact": "Severe"
            },
            "interest_rate_shock": {
                "rate_increase": 3.0,
                "impact_on_value": -15,
                "probability": 0.15
            }
        }
    
    def _perform_risk_scenario_analysis(self, features: Dict[str, Any], target_type: str) -> Dict[str, Any]:
        """Perform risk scenario analysis."""
        return {
            "economic_recession": {
                "probability": 0.2,
                "impact_severity": "High",
                "value_impact": -25,
                "duration_months": 18
            },
            "local_market_downturn": {
                "probability": 0.3,
                "impact_severity": "Medium",
                "value_impact": -15,
                "duration_months": 12
            }
        }