import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import sqlite3
from typing import Dict, Any, Optional, List
from pathlib import Path

class PropertyValuationService:
    def __init__(self, market_data_service):
        self.market_service = market_data_service
        self.model = None
        self.encoders = {}
        self.feature_columns = ['bed', 'bath', 'house_size', 'acre_lot', 'city_encoded', 'state_encoded']
        self.model_path = "property_valuation_model.joblib"
        self.encoders_path = "property_encoders.joblib"
        
    def train_model(self, retrain: bool = False):
        """Train the property valuation model"""
        if not retrain and Path(self.model_path).exists():
            self.load_model()
            return {"status": "Model loaded from cache"}
        
        print("Training property valuation model...")
        
        # Load data from SQLite
        conn = sqlite3.connect(self.market_service.db_path)
        query = """
        SELECT price, bed, bath, house_size, acre_lot, city, state
        FROM properties 
        WHERE price IS NOT NULL 
        AND bed IS NOT NULL 
        AND bath IS NOT NULL 
        AND house_size IS NOT NULL
        AND house_size > 0
        AND price > 10000
        AND price < 10000000
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(df) < 1000:
            return {"error": "Insufficient data for training"}
        
        # Encode categorical variables
        self.encoders['city'] = LabelEncoder()
        self.encoders['state'] = LabelEncoder()
        
        df['city_encoded'] = self.encoders['city'].fit_transform(df['city'].astype(str))
        df['state_encoded'] = self.encoders['state'].fit_transform(df['state'].astype(str))
        
        # Prepare features and target
        X = df[self.feature_columns].fillna(0)
        y = df['price']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train model
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Save model and encoders
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.encoders, self.encoders_path)
        
        return {
            "status": "Model trained successfully",
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "mean_absolute_error": mae,
            "r2_score": r2,
            "feature_importance": dict(zip(self.feature_columns, self.model.feature_importances_))
        }
    
    def load_model(self):
        """Load trained model and encoders"""
        if Path(self.model_path).exists() and Path(self.encoders_path).exists():
            self.model = joblib.load(self.model_path)
            self.encoders = joblib.load(self.encoders_path)
            return True
        return False
    
    def predict_value(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict property value using ML model"""
        if not self.model:
            if not self.load_model():
                return {"error": "Model not trained. Please train the model first."}
        
        try:
            # Prepare features
            features = {}
            features['bed'] = property_data.get('bedrooms', 0)
            features['bath'] = property_data.get('bathrooms', 0)
            features['house_size'] = property_data.get('house_size', 0)
            features['acre_lot'] = property_data.get('acre_lot', 0)
            
            # Encode categorical variables
            city = str(property_data.get('city', ''))
            state = str(property_data.get('state', ''))
            
            # Handle unseen categories
            try:
                features['city_encoded'] = self.encoders['city'].transform([city])[0]
            except ValueError:
                features['city_encoded'] = 0  # Default for unseen cities
            
            try:
                features['state_encoded'] = self.encoders['state'].transform([state])[0]
            except ValueError:
                features['state_encoded'] = 0  # Default for unseen states
            
            # Create feature array
            feature_array = np.array([[features[col] for col in self.feature_columns]])
            
            # Make prediction
            predicted_value = self.model.predict(feature_array)[0]
            
            # Get prediction confidence (using model's prediction intervals)
            # For Random Forest, we can use the standard deviation of tree predictions
            tree_predictions = [tree.predict(feature_array)[0] for tree in self.model.estimators_]
            prediction_std = np.std(tree_predictions)
            
            confidence_interval = {
                "lower": max(0, predicted_value - 1.96 * prediction_std),
                "upper": predicted_value + 1.96 * prediction_std
            }
            
            return {
                "predicted_value": round(predicted_value),
                "confidence_interval": {
                    "lower": round(confidence_interval["lower"]),
                    "upper": round(confidence_interval["upper"])
                },
                "prediction_std": round(prediction_std),
                "model_type": "Random Forest",
                "features_used": features
            }
            
        except Exception as e:
            return {"error": f"Prediction failed: {str(e)}"}
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from the trained model"""
        if not self.model:
            if not self.load_model():
                return {"error": "Model not trained"}
        
        return dict(zip(self.feature_columns, self.model.feature_importances_))
    
    def batch_predict(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Predict values for multiple properties"""
        results = []
        for prop in properties:
            prediction = self.predict_value(prop)
            results.append({
                "property": prop,
                "prediction": prediction
            })
        return results