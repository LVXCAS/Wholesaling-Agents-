from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
import xgboost as xgb
import lightgbm as lgb
from sklearn.preprocessing import StandardScaler, PolynomialFeatures, RobustScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.feature_selection import SelectKBest, mutual_info_regression
from sklearn.preprocessing import PowerTransformer
from bayes_opt import BayesianOptimization
import json
import os
from datetime import datetime
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

class RenovationModel:
    def __init__(self):
        self.models = {
            'kitchen': None,
            'bathroom': None,
            'flooring': None,
            'electrical': None,
            'plumbing': None,
            'hvac': None,
            'roofing': None
        }
        self.scalers = {}
        self.power_transformers = {}
        self.feature_selectors = {}
        self.poly_features = {}
        self.feature_importances = {}
        self.model_metrics = {}
        self.market_indicators = self._init_market_indicators()
        self.historical_trends = self._load_historical_trends()
        self.load_training_data()
        self.train_models()

    def _init_market_indicators(self) -> Dict:
        """Initialize market condition indicators."""
        return {
            'labor_cost_index': self._get_labor_cost_index(),
            'material_cost_trend': self._get_material_cost_trend(),
            'seasonal_factor': self._calculate_seasonal_factor(),
            'contractor_availability': self._get_contractor_availability()
        }

    def _get_labor_cost_index(self) -> Dict[str, float]:
        """Get regional labor cost indices."""
        return {
            'south': 1.0,
            'midwest': 1.15,
            'northeast': 1.35,
            'west': 1.25
        }

    def _get_material_cost_trend(self) -> float:
        """Calculate material cost trend based on current market data."""
        # This would ideally pull from an external API or database
        base_trend = 1.05  # 5% YoY increase
        return base_trend

    def _calculate_seasonal_factor(self) -> float:
        """Calculate seasonal impact on renovation costs."""
        month = datetime.now().month
        # Peak seasons (summer) have higher costs
        seasonal_factors = {
            1: 0.95, 2: 0.95, 3: 1.0,   # Winter/Early Spring
            4: 1.05, 5: 1.1, 6: 1.15,    # Late Spring/Early Summer
            7: 1.2, 8: 1.2, 9: 1.15,     # Peak Summer/Early Fall
            10: 1.1, 11: 1.0, 12: 0.95   # Late Fall/Winter
        }
        return seasonal_factors[month]

    def _get_contractor_availability(self) -> float:
        """Estimate contractor availability impact on costs."""
        # This would ideally be based on real-time data
        month = datetime.now().month
        # Higher values indicate less availability (higher costs)
        availability_factors = {
            1: 0.9, 2: 0.9, 3: 1.0,    # More availability in winter
            4: 1.1, 5: 1.2, 6: 1.3,    # Less availability in summer
            7: 1.3, 8: 1.3, 9: 1.2,
            10: 1.1, 11: 1.0, 12: 0.9
        }
        return availability_factors[month]

    def _load_historical_trends(self) -> Dict:
        """Load historical cost trends and patterns."""
        try:
            # This would typically load from a database or API
            return {
                'material_cost_index': self._calculate_material_cost_index(),
                'labor_cost_trends': self._calculate_labor_trends(),
                'market_volatility': self._calculate_market_volatility()
            }
        except Exception as e:
            print(f"Warning: Could not load historical trends: {e}")
            return {}

    def _calculate_material_cost_index(self) -> float:
        """Calculate material cost index based on historical data."""
        base_index = 100
        yearly_increase = 0.05  # 5% average yearly increase
        years_since_base = datetime.now().year - 2020
        return base_index * (1 + yearly_increase) ** years_since_base

    def _calculate_labor_trends(self) -> Dict[str, float]:
        """Calculate labor cost trends by region."""
        return {
            'south': 1.03,  # 3% increase
            'midwest': 1.04,
            'northeast': 1.06,
            'west': 1.05
        }

    def _calculate_market_volatility(self) -> float:
        """Calculate market volatility factor."""
        # This would typically use real market data
        return 0.15  # 15% volatility

    def _validate_and_enhance_training_data(self):
        """Validate and enhance training data quality."""
        for category in self.models.keys():
            if category not in self.cost_data['training_data']:
                continue

            for quality_level in self.cost_data['training_data'][category].values():
                if 'samples' not in quality_level:
                    continue

                samples = quality_level['samples']
                validated_samples = []

                for sample in samples:
                    # Basic validation
                    if not self._is_valid_sample(sample):
                        continue

                    # Enhance sample with additional features
                    enhanced_sample = self._enhance_sample(sample)
                    validated_samples.append(enhanced_sample)

                quality_level['samples'] = validated_samples

    def _is_valid_sample(self, sample: Dict) -> bool:
        """Validate individual sample data."""
        required_fields = ['sqft', 'age', 'region', 'quality', 'cost']
        if not all(field in sample for field in required_fields):
            return False

        # Validate numeric ranges
        if not (10 <= sample['sqft'] <= 10000):  # Reasonable sqft range
            return False
        if not (0 <= sample['age'] <= 200):  # Reasonable age range
            return False
        if not (100 <= sample['cost'] <= 1000000):  # Reasonable cost range
            return False

        return True

    def _enhance_sample(self, sample: Dict) -> Dict:
        """Enhance sample with additional derived features."""
        enhanced = sample.copy()

        # Add time-based features
        if 'year' in sample:
            enhanced['data_age'] = datetime.now().year - sample['year']
            
        # Add market adjustment
        if 'region' in sample:
            enhanced['market_factor'] = self.market_indicators['labor_cost_index'].get(
                sample['region'].lower(), 1.0
            ) * self.historical_trends['labor_cost_trends'].get(
                sample['region'].lower(), 1.0
            )

        # Add complexity score if not present
        if 'complexity' not in enhanced:
            # Estimate complexity based on cost and square footage
            cost_per_sqft = enhanced['cost'] / enhanced['sqft']
            enhanced['complexity'] = self._estimate_complexity(cost_per_sqft)

        return enhanced

    def _estimate_complexity(self, cost_per_sqft: float) -> float:
        """Estimate project complexity based on cost per square foot."""
        # Define baseline costs per sqft for different complexity levels
        baselines = {
            'simple': {'min': 50, 'max': 150},
            'medium': {'min': 150, 'max': 300},
            'complex': {'min': 300, 'max': 600}
        }

        if cost_per_sqft < baselines['simple']['max']:
            return 1.0
        elif cost_per_sqft < baselines['medium']['max']:
            return 2.0
        else:
            return 3.0

    def load_training_data(self):
        """Load, validate, and enhance training data from JSON file."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(current_dir, '..', 'data', 'renovation_costs.json')
        
        with open(data_path, 'r') as f:
            self.cost_data = json.load(f)
        
        # Validate and enhance the data
        self._validate_and_enhance_training_data()

        # Generate additional synthetic data if needed
        self._augment_with_synthetic_data()

    def _prepare_features(self, samples: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare feature matrix and target vector from samples with enhanced engineering."""
        X = []
        y = []
        
        for sample in samples:
            # Basic features
            sqft = sample.get('sqft', 0)
            age = datetime.now().year - sample.get('year', 2020)
            quality = self._encode_quality(sample.get('quality', 'basic'))
            region = self._encode_region(sample.get('region', 'south'))
            property_age = sample.get('age', 0)
            complexity = sample.get('complexity', 1)
            material_grade = sample.get('material_grade', 1)
            
            # Advanced feature engineering
            labor_cost_factor = self.market_indicators['labor_cost_index'].get(sample.get('region', 'south'), 1.0)
            material_cost_trend = self.market_indicators['material_cost_trend']
            seasonal_impact = self._calculate_seasonal_factor()
            contractor_availability = self._get_contractor_availability()
            
            # Interaction features
            sqft_quality = sqft * quality
            age_complexity = property_age * complexity
            material_labor_interaction = material_grade * labor_cost_factor
            
            # Market adjustment features
            market_volatility = self.historical_trends.get('market_volatility', 0.15)
            regional_trend = self.historical_trends['labor_cost_trends'].get(sample.get('region', 'south'), 1.0)
            
            features = [
                sqft,
                age,
                quality,
                region,
                property_age,
                complexity,
                material_grade,
                labor_cost_factor,
                material_cost_trend,
                seasonal_impact,
                contractor_availability,
                sqft_quality,
                age_complexity,
                material_labor_interaction,
                market_volatility,
                regional_trend
            ]
            
            X.append(features)
            y.append(sample['cost'])
        
        return np.array(X), np.array(y)

    def _encode_quality(self, quality: str) -> float:
        """Enhanced quality encoding with continuous values."""
        base_quality_map = {
            'basic': 1.0,
            'medium': 2.0,
            'luxury': 3.0
        }
        
        # Add granular quality levels
        detailed_quality_map = {
            'basic-minus': 0.8,
            'basic-plus': 1.2,
            'medium-minus': 1.8,
            'medium-plus': 2.2,
            'luxury-minus': 2.8,
            'luxury-plus': 3.2
        }
        
        quality_map = {**base_quality_map, **detailed_quality_map}
        return quality_map.get(quality.lower(), 1.0)

    def _encode_region(self, region: str) -> float:
        """Enhanced region encoding with market factors."""
        base_region_map = {
            'south': 1.0,
            'midwest': 1.2,
            'northeast': 1.4,
            'west': 1.3
        }
        
        # Apply market trend adjustments
        region_value = base_region_map.get(region.lower(), 1.0)
        trend_adjustment = self.historical_trends['labor_cost_trends'].get(region.lower(), 1.0)
        
        return region_value * trend_adjustment

    def train_models(self):
        """Train ML models for each renovation category with enhanced validation."""
        for category in self.models.keys():
            if category not in self.cost_data['training_data']:
                continue
                
            # Combine samples from all quality levels
            all_samples = []
            for quality_level in self.cost_data['training_data'][category].values():
                if 'samples' in quality_level:
                    all_samples.extend(quality_level['samples'])
            
            if not all_samples:
                continue
                
            X, y = self._prepare_features(all_samples)
            
            # Split data into train, validation, and test sets
            X_train_val, X_test, y_train_val, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            X_train, X_val, y_train, y_val = train_test_split(X_train_val, y_train_val, test_size=0.2, random_state=42)
            
            # Feature selection with reduced number of features
            n_features = min(10, X_train.shape[1])  # Select top 10 features or less
            selector = SelectKBest(score_func=mutual_info_regression, k=n_features)
            X_train_selected = selector.fit_transform(X_train, y_train)
            X_val_selected = selector.transform(X_val)
            X_test_selected = selector.transform(X_test)
            
            # Get selected feature indices
            selected_features = selector.get_support()
            feature_scores = selector.scores_
            feature_names = [
                'sqft', 'data_age', 'quality', 'region', 'property_age',
                'complexity', 'material_grade', 'labor_cost_factor',
                'material_cost_trend', 'seasonal_impact', 'contractor_availability',
                'sqft_quality', 'age_complexity', 'material_labor_interaction',
                'market_volatility', 'regional_trend'
            ]
            
            # Store feature importance information
            self.feature_importances[category] = {
                'selected_features': [
                    (name, score) for name, score, selected in 
                    zip(feature_names[:len(feature_scores)], feature_scores, selected_features)
                    if selected
                ],
                'all_features': [
                    (name, score) for name, score in 
                    zip(feature_names[:len(feature_scores)], feature_scores)
                ]
            }
            
            # Scale selected features
            scaler = RobustScaler()
            X_train_scaled = scaler.fit_transform(X_train_selected)
            X_val_scaled = scaler.transform(X_val_selected)
            X_test_scaled = scaler.transform(X_test_selected)
            
            # Power transformation for normality
            power_transformer = PowerTransformer(method='yeo-johnson')
            X_train_transformed = power_transformer.fit_transform(X_train_scaled)
            X_val_transformed = power_transformer.transform(X_val_scaled)
            X_test_transformed = power_transformer.transform(X_test_scaled)
            
            # Generate polynomial features
            poly = PolynomialFeatures(degree=2, include_bias=False)
            X_train_poly = poly.fit_transform(X_train_transformed)
            X_val_poly = poly.transform(X_val_transformed)
            X_test_poly = poly.transform(X_test_transformed)
            
            # Initialize and train base models with adjusted parameters
            rf_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=3,
                random_state=42,
                n_jobs=-1
            )
            rf_model.fit(X_train_poly, y_train)
            
            gb_model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                min_samples_split=5,
                min_samples_leaf=3,
                learning_rate=0.1,
                random_state=42
            )
            gb_model.fit(X_train_poly, y_train)
            
            # Train XGBoost with adjusted parameters
            xgb_model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                min_child_weight=3,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
            )
            xgb_model.fit(
                X_train_poly, 
                y_train,
                eval_set=[(X_train_poly, y_train), (X_val_poly, y_val)],
                verbose=False
            )
            
            # Train LightGBM with adjusted parameters
            lgb_model = lgb.LGBMRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                min_child_samples=5,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
            )
            lgb_model.fit(
                X_train_poly, 
                y_train,
                eval_set=[(X_val_poly, y_val)],
                callbacks=[lgb.early_stopping(10)]
            )
            
            # Get predictions on validation set
            val_predictions = {
                'rf': rf_model.predict(X_val_poly),
                'gb': gb_model.predict(X_val_poly),
                'xgb': xgb_model.predict(X_val_poly),
                'lgb': lgb_model.predict(X_val_poly)
            }
            
            # Calculate validation scores
            val_scores = {
                'rf': r2_score(y_val, val_predictions['rf']),
                'gb': r2_score(y_val, val_predictions['gb']),
                'xgb': r2_score(y_val, val_predictions['xgb']),
                'lgb': r2_score(y_val, val_predictions['lgb'])
            }
            
            # Calculate weights based on validation performance
            total_score = sum(val_scores.values())
            weights = {k: v/total_score for k, v in val_scores.items()}
            
            # Create weighted ensemble
            ensemble_model = VotingRegressor(
                estimators=[
                    ('rf', rf_model),
                    ('gb', gb_model),
                    ('xgb', xgb_model),
                    ('lgb', lgb_model)
                ],
                weights=[weights['rf'], weights['gb'], weights['xgb'], weights['lgb']]
            )
            
            # Fit the ensemble on combined train+validation set for final training
            X_train_full = np.vstack((X_train_poly, X_val_poly))
            y_train_full = np.concatenate((y_train, y_val))
            ensemble_model.fit(X_train_full, y_train_full)
            
            # Store the ensemble model
            self.models[category] = ensemble_model
            
            # Calculate and store model metrics
            val_predictions = ensemble_model.predict(X_val_poly)
            test_predictions = ensemble_model.predict(X_test_poly)
            
            # Store metrics for later use
            self.scalers[category] = scaler
            self.power_transformers[category] = power_transformer
            self.poly_features[category] = poly
            self.feature_selectors[category] = selector
            
            self.model_metrics[category] = {
                'r2_score': r2_score(y_test, test_predictions),
                'cv_scores': {
                    'rf': cross_val_score(rf_model, X_train_poly, y_train, cv=5),
                    'gb': cross_val_score(gb_model, X_train_poly, y_train, cv=5),
                    'xgb': cross_val_score(xgb_model, X_train_poly, y_train, cv=5),
                    'lgb': cross_val_score(lgb_model, X_train_poly, y_train, cv=5)
                },
                'feature_weights': {
                    'rf': rf_model.feature_importances_.mean(),
                    'gb': gb_model.feature_importances_.mean(),
                    'xgb': float(np.mean(xgb_model.feature_importances_)),
                    'lgb': float(np.mean(lgb_model.feature_importances_))
                }
            }

    def predict_cost(self, category: str, features: Dict) -> Tuple[float, float, Dict]:
        """
        Predict renovation cost for a category and return cost, confidence score, and additional metrics.
        Returns (predicted_cost, confidence_score, additional_metrics)
        """
        if category not in self.models or self.models[category] is None:
            return 0.0, 0.0, {}
            
        # Prepare features
        feature_vector = np.array([[
            features.get('sqft', 0),
            features.get('data_age', 0),
            self._encode_quality(features.get('quality', 'basic')),
            self._encode_region(features.get('region', 'south')),
            features.get('age', 0),
            features.get('complexity', 1),
            features.get('material_grade', 1),
            self.market_indicators['labor_cost_index'].get(features.get('region', 'south'), 1.0),
            self.market_indicators['material_cost_trend'],
            self._calculate_seasonal_factor(),
            self._get_contractor_availability(),
            features.get('sqft', 0) * self._encode_quality(features.get('quality', 'basic')),
            features.get('age', 0) * features.get('complexity', 1),
            features.get('material_grade', 1) * self.market_indicators['labor_cost_index'].get(features.get('region', 'south'), 1.0),
            self.historical_trends.get('market_volatility', 0.15),
            self.historical_trends['labor_cost_trends'].get(features.get('region', 'south'), 1.0)
        ]])
        
        # Apply feature selection
        feature_vector_selected = self.feature_selectors[category].transform(feature_vector)
        
        # Scale features
        feature_vector_scaled = self.scalers[category].transform(feature_vector_selected)
        
        # Apply power transformation
        feature_vector_transformed = self.power_transformers[category].transform(feature_vector_scaled)
        
        # Generate polynomial features
        feature_vector_poly = self.poly_features[category].transform(feature_vector_transformed)
        
        # Get predictions from all models in ensemble
        predictions = []
        for name, model in self.models[category].estimators_:
            pred = model.predict(feature_vector_poly)[0]
            predictions.append(pred)
        
        # Calculate ensemble prediction
        weights = self.model_metrics[category]['feature_weights']
        predicted_cost = np.average(predictions, weights=list(weights.values()))
        
        # Calculate prediction uncertainty
        prediction_std = np.std(predictions)
        prediction_range = max(predictions) - min(predictions)
        
        # Calculate confidence score
        base_confidence = self.model_metrics[category]['r2_score']
        prediction_confidence = 1 - (prediction_std / predicted_cost)
        market_volatility = self.historical_trends.get('market_volatility', 0.15)
        seasonal_impact = abs(self._calculate_seasonal_factor() - 1)
        
        # Combine confidence factors
        confidence_score = min(
            base_confidence * 
            prediction_confidence * 
            (1 - market_volatility) * 
            (1 - seasonal_impact),
            0.95  # Cap at 95% confidence
        )
        
        # Gather metrics
        metrics = {
            'prediction_std': prediction_std,
            'prediction_range': prediction_range,
            'base_confidence': base_confidence,
            'market_volatility': market_volatility,
            'seasonal_impact': seasonal_impact,
            'individual_predictions': dict(zip(['rf', 'gb', 'xgb', 'lgb'], predictions)),
            'feature_importances': self.feature_importances.get(category, {})
        }
        
        return predicted_cost, confidence_score, metrics

    def get_market_volatility_adjustment(self, category: str) -> float:
        """Get market volatility adjustment for a specific renovation category."""
        if category not in self.models or self.models[category] is None:
            return 0.0
            
        # Get base market volatility from historical trends
        base_volatility = self.historical_trends.get('market_volatility', 0.15)
        
        # Adjust based on category-specific factors
        category_factors = {
            'kitchen': 1.2,  # Higher volatility due to appliance prices and labor costs
            'bathroom': 1.1,  # Moderate volatility
            'hvac': 1.3,     # High volatility due to equipment and energy costs
            'flooring': 0.9,  # Lower volatility due to stable material costs
            'electrical': 1.1,
            'plumbing': 1.2,
            'roofing': 1.1
        }
        
        category_multiplier = category_factors.get(category, 1.0)
        seasonal_impact = self._calculate_seasonal_factor() - 1.0  # Convert to adjustment
        
        total_adjustment = (base_volatility * category_multiplier) + seasonal_impact
        return total_adjustment

    def _calculate_data_quality_score(self, category: str) -> float:
        """Calculate a score representing the quality of training data."""
        if category not in self.models or not self.cost_data['training_data'].get(category):
            return 0.0
            
        # Count samples
        total_samples = sum(
            len(quality_level.get('samples', []))
            for quality_level in self.cost_data['training_data'][category].values()
        )
        
        # Calculate synthetic ratio
        synthetic_samples = sum(
            sum(1 for sample in quality_level.get('samples', []) if sample.get('synthetic', False))
            for quality_level in self.cost_data['training_data'][category].values()
        )
        synthetic_ratio = synthetic_samples / total_samples if total_samples > 0 else 1.0
        
        # Calculate age factor (prefer recent data)
        current_year = datetime.now().year
        avg_age = np.mean([
            current_year - sample.get('year', current_year)
            for quality_level in self.cost_data['training_data'][category].values()
            for sample in quality_level.get('samples', [])
            if 'year' in sample
        ])
        age_factor = max(0, 1 - (avg_age / 5))  # Reduce score for older data
        
        # Calculate diversity score
        quality_distribution = [
            len(quality_level.get('samples', []))
            for quality_level in self.cost_data['training_data'][category].values()
        ]
        if quality_distribution:
            diversity_score = min(quality_distribution) / max(quality_distribution) if max(quality_distribution) > 0 else 0
        else:
            diversity_score = 0
            
        # Combine factors
        base_score = min(1.0, total_samples / 1000)  # Normalize to desired sample size
        synthetic_penalty = (1 - synthetic_ratio) * 0.3  # Up to 30% penalty for synthetic data
        
        final_score = base_score * (1 - synthetic_penalty) * age_factor * (0.7 + 0.3 * diversity_score)
        
        return round(final_score, 3)

    def get_feature_importance(self, category: str) -> Dict[str, float]:
        """Get feature importance scores for a category."""
        if category not in self.feature_importances:
            return {}
            
        feature_names = [
            'square_footage',
            'data_age',
            'quality_level',
            'region',
            'property_age',
            'complexity',
            'material_grade'
        ]
        
        return dict(zip(feature_names, self.feature_importances[category]))

    def _augment_with_synthetic_data(self, min_samples_per_category: int = 1000):
        """Generate additional synthetic data if needed."""
        from app.data.training_data_generator import TrainingDataGenerator
        
        generator = TrainingDataGenerator()
        
        for category in self.models.keys():
            if category not in self.cost_data['training_data']:
                continue
                
            category_samples = []
            for quality_level in self.cost_data['training_data'][category].values():
                if 'samples' in quality_level:
                    category_samples.extend(quality_level['samples'])
            
            current_samples = len(category_samples)
            if current_samples < min_samples_per_category:
                samples_needed = min_samples_per_category - current_samples
                samples_per_quality = samples_needed // 3  # Split between quality levels
                
                for quality in ['basic', 'medium', 'luxury']:
                    synthetic_samples = generator.generate_synthetic_samples(
                        category=category,
                        quality=quality,
                        n_samples=samples_per_quality
                    )
                    
                    # Add synthetic samples to training data
                    if quality not in self.cost_data['training_data'][category]:
                        self.cost_data['training_data'][category][quality] = {'samples': []}
                    
                    self.cost_data['training_data'][category][quality]['samples'].extend(synthetic_samples)
                    
        # Save augmented dataset
        self._save_augmented_dataset()

    def _save_augmented_dataset(self):
        """Save the augmented dataset with timestamp."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(current_dir, '..', 'data', f'renovation_costs_augmented_{timestamp}.json')
        
        # Add metadata about the augmentation
        augmented_data = {
            'metadata': {
                'timestamp': timestamp,
                'original_samples': self._count_samples(self.cost_data['training_data']),
                'augmentation_date': datetime.now().isoformat(),
                'data_version': '2.0'
            },
            'training_data': self.cost_data['training_data']
        }
        
        with open(output_path, 'w') as f:
            json.dump(augmented_data, f, indent=2)
            
        print(f"Augmented dataset saved to {output_path}")
        
    def _count_samples(self, data: Dict) -> Dict:
        """Count samples in each category and quality level."""
        counts = {}
        for category, quality_levels in data.items():
            category_count = 0
            quality_counts = {}
            
            for quality, content in quality_levels.items():
                if 'samples' in content:
                    sample_count = len(content['samples'])
                    quality_counts[quality] = sample_count
                    category_count += sample_count
                    
            counts[category] = {
                'total': category_count,
                'by_quality': quality_counts
            }
            
        return counts

    def get_prediction_confidence(self, category: str, prediction: float) -> float:
        """Get the confidence score for a prediction."""
        if category not in self.model_metrics:
            return 0.5  # Default medium confidence if no metrics available
        
        metrics = self.model_metrics[category]
        base_confidence = metrics.get('r2_score', 0.7)
        cv_stability = np.mean([np.std(scores) for scores in metrics.get('cv_scores', {}).values()]) if metrics.get('cv_scores') else 0.2
        
        # Adjust confidence based on prediction magnitude
        avg_cost = np.mean([sample['cost'] for quality_level in self.cost_data['training_data'].get(category, {}).values() 
                          for sample in quality_level.get('samples', [])])
        prediction_factor = 1 - min(abs(prediction - avg_cost) / avg_cost, 0.5)
        
        # Calculate final confidence score
        confidence = base_confidence * (1 - cv_stability) * prediction_factor
        return round(max(min(confidence, 1.0), 0.1), 2)  # Ensure between 0.1 and 1.0
    
    def predict_renovation_cost(
        self,
        category: str,
        sqft: float,
        year: int,
        renovation_level: str,
        region: str,
        age: int = 0,
        complexity: float = 1.0,
        material_grade: int = 1
    ) -> Dict:
        """
        Predict renovation cost for a specific category with additional renovation-specific parameters.
        Returns a dictionary with detailed cost prediction results.
        """
        features = {
            'sqft': sqft,
            'data_age': datetime.now().year - year,
            'quality': renovation_level,
            'region': region,
            'age': age,
            'complexity': complexity,
            'material_grade': material_grade
        }
        
        # Use predict_cost internally and unpack the values
        predicted_cost, confidence_score, metrics = self.predict_cost(category, features)
        
        # Convert to the expected dictionary format
        return {
            'predicted_cost': predicted_cost,
            'confidence_score': confidence_score,
            'prediction_interval': metrics.get('prediction_range', 0),
            'feature_contributions': metrics.get('feature_importances', {}),
            'out_of_range_features': []  # Would be populated by validation logic
        }

    def predict_general_cost(
        self,
        year: int,
        cost_type: str,
        base_cost: float,
        region: str = 'south',
        complexity: float = 1.0
    ) -> Dict:
        """
        Predict general renovation cost of a specific type.
        Returns a dictionary with detailed cost prediction results.
        """
        features = {
            'sqft': base_cost,  # Use base_cost as sqft for scaling
            'data_age': datetime.now().year - year,
            'quality': 'medium',  # Default to medium quality for general costs
            'region': region,
            'age': 0,  # Not relevant for general costs
            'complexity': complexity,
            'material_grade': 3  # Default to medium grade
        }
        
        # Use predict_cost internally and unpack the values
        predicted_cost, confidence_score, metrics = self.predict_cost(cost_type, features)
        
        return {
            'predicted_cost': predicted_cost,
            'confidence_score': confidence_score,
            'prediction_interval': metrics.get('prediction_range', 0),
            'feature_contributions': metrics.get('feature_importances', {}),
            'out_of_range_features': []  # Would be populated by validation logic
        }
