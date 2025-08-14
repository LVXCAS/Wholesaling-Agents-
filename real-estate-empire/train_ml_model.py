"""
ML Model Training Script for Real Estate Property Valuation
Trains a Random Forest model using the realtor data
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import joblib
import sqlite3
import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Add app directory to path
current_dir = Path(__file__).parent
app_dir = current_dir / "app"
sys.path.insert(0, str(app_dir))

class PropertyValuationTrainer:
    def __init__(self, data_path="data/realtor-data.zip.csv"):
        self.data_path = data_path
        self.model = None
        self.encoders = {}
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.model_path = "property_valuation_model.joblib"
        self.encoders_path = "property_encoders.joblib"
        self.scaler_path = "property_scaler.joblib"
        self.db_path = "real_estate_data.db"
        
    def load_and_prepare_data(self):
        """Load and prepare the real estate data"""
        print("📊 Loading real estate data...")
        
        try:
            # Load the CSV data
            df = pd.read_csv(self.data_path)
            print(f"✅ Loaded {len(df):,} records from {self.data_path}")
            
            # Display basic info about the dataset
            print(f"\nDataset Info:")
            print(f"Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            
            # Show first few rows
            print(f"\nFirst 5 rows:")
            print(df.head())
            
            return df
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return None
    
    def clean_and_preprocess_data(self, df):
        """Clean and preprocess the data for training"""
        print("\n🧹 Cleaning and preprocessing data...")
        
        original_size = len(df)
        
        # Standardize column names (common variations)
        column_mapping = {
            'price': 'price',
            'asking_price': 'price',
            'list_price': 'price',
            'bed': 'bedrooms',
            'beds': 'bedrooms',
            'bedroom': 'bedrooms',
            'bath': 'bathrooms',
            'baths': 'bathrooms',
            'bathroom': 'bathrooms',
            'house_size': 'sqft',
            'square_feet': 'sqft',
            'sqft': 'sqft',
            'size': 'sqft',
            'acre_lot': 'lot_size',
            'lot_size': 'lot_size',
            'city': 'city',
            'state': 'state',
            'zip_code': 'zip_code',
            'year_built': 'year_built',
            'property_type': 'property_type'
        }
        
        # Rename columns to standard names
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})
        
        print(f"Available columns after mapping: {list(df.columns)}")
        
        # Required columns for training
        required_columns = ['price']
        optional_columns = ['bedrooms', 'bathrooms', 'sqft', 'city', 'state', 'lot_size', 'year_built']
        
        # Check which columns we have
        available_columns = []
        for col in required_columns + optional_columns:
            if col in df.columns:
                available_columns.append(col)
        
        print(f"Using columns: {available_columns}")
        
        # Filter to available columns
        df = df[available_columns].copy()
        
        # Clean price data
        if 'price' in df.columns:
            # Remove non-numeric prices
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            
            # Remove unrealistic prices
            df = df[(df['price'] >= 10000) & (df['price'] <= 50000000)]
            print(f"After price filtering: {len(df):,} records")
        
        # Clean numeric columns
        numeric_columns = ['bedrooms', 'bathrooms', 'sqft', 'lot_size', 'year_built']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Remove unrealistic values
                if col == 'bedrooms':
                    df = df[(df[col] >= 0) & (df[col] <= 20)]
                elif col == 'bathrooms':
                    df = df[(df[col] >= 0) & (df[col] <= 20)]
                elif col == 'sqft':
                    df = df[(df[col] >= 100) & (df[col] <= 50000)]
                elif col == 'year_built':
                    df = df[(df[col] >= 1800) & (df[col] <= 2025)]
        
        # Remove rows with missing price (target variable)
        df = df.dropna(subset=['price'])
        
        # Fill missing values for features
        for col in df.columns:
            if col != 'price':
                if df[col].dtype in ['object', 'string']:
                    df[col] = df[col].fillna('Unknown')
                else:
                    df[col] = df[col].fillna(df[col].median())
        
        print(f"After cleaning: {len(df):,} records ({len(df)/original_size*100:.1f}% retained)")
        
        return df
    
    def create_features(self, df):
        """Create features for the ML model"""
        print("\n🔧 Creating features...")
        
        # Start with numeric features
        feature_columns = []
        
        # Basic numeric features
        numeric_features = ['bedrooms', 'bathrooms', 'sqft', 'lot_size', 'year_built']
        for col in numeric_features:
            if col in df.columns:
                feature_columns.append(col)
        
        # Encode categorical features
        categorical_features = ['city', 'state', 'property_type']
        for col in categorical_features:
            if col in df.columns:
                print(f"Encoding {col}...")
                self.encoders[col] = LabelEncoder()
                df[f'{col}_encoded'] = self.encoders[col].fit_transform(df[col].astype(str))
                feature_columns.append(f'{col}_encoded')
        
        # Create derived features
        if 'sqft' in df.columns and 'bedrooms' in df.columns:
            df['sqft_per_bedroom'] = df['sqft'] / (df['bedrooms'] + 1)  # +1 to avoid division by zero
            feature_columns.append('sqft_per_bedroom')
        
        if 'sqft' in df.columns and 'bathrooms' in df.columns:
            df['sqft_per_bathroom'] = df['sqft'] / (df['bathrooms'] + 1)
            feature_columns.append('sqft_per_bathroom')
        
        if 'year_built' in df.columns:
            current_year = datetime.now().year
            df['property_age'] = current_year - df['year_built']
            feature_columns.append('property_age')
        
        # Store feature columns
        self.feature_columns = feature_columns
        print(f"Created {len(feature_columns)} features: {feature_columns}")
        
        return df
    
    def train_model(self, df):
        """Train the Random Forest model"""
        print("\n🤖 Training Random Forest model...")
        
        # Prepare features and target
        X = df[self.feature_columns].fillna(0)
        y = df['price']
        
        print(f"Training data shape: {X.shape}")
        print(f"Target range: ${y.min():,.0f} - ${y.max():,.0f}")
        print(f"Target median: ${y.median():,.0f}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest model
        self.model = RandomForestRegressor(
            n_estimators=200,
            max_depth=25,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1,
            verbose=1
        )
        
        print("Training model...")
        self.model.fit(X_train_scaled, y_train)
        
        # Make predictions
        y_pred_train = self.model.predict(X_train_scaled)
        y_pred_test = self.model.predict(X_test_scaled)
        
        # Calculate metrics
        train_mae = mean_absolute_error(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5, scoring='r2')
        
        # Feature importance
        feature_importance = dict(zip(self.feature_columns, self.model.feature_importances_))
        feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
        
        results = {
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "train_mae": train_mae,
            "test_mae": test_mae,
            "train_r2": train_r2,
            "test_r2": test_r2,
            "train_rmse": train_rmse,
            "test_rmse": test_rmse,
            "cv_r2_mean": cv_scores.mean(),
            "cv_r2_std": cv_scores.std(),
            "feature_importance": feature_importance
        }
        
        return results, X_test, y_test, y_pred_test
    
    def save_model(self):
        """Save the trained model and preprocessors"""
        print("\n💾 Saving model and preprocessors...")
        
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.encoders, self.encoders_path)
        joblib.dump(self.scaler, self.scaler_path)
        
        print(f"✅ Model saved to {self.model_path}")
        print(f"✅ Encoders saved to {self.encoders_path}")
        print(f"✅ Scaler saved to {self.scaler_path}")
    
    def create_database(self, df):
        """Create SQLite database for the market data service"""
        print(f"\n🗄️ Creating SQLite database...")
        
        # Create database connection
        conn = sqlite3.connect(self.db_path)
        
        # Save the cleaned data to database
        df.to_sql('properties', conn, if_exists='replace', index=False)
        
        # Create indexes for better performance
        cursor = conn.cursor()
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_city ON properties(city)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_state ON properties(state)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_price ON properties(price)")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Database created: {self.db_path}")
        print(f"✅ Saved {len(df):,} records to database")
    
    def generate_report(self, results, df):
        """Generate a comprehensive training report"""
        print(f"\n📊 TRAINING REPORT")
        print("=" * 50)
        
        print(f"Dataset Statistics:")
        print(f"  Total records: {len(df):,}")
        print(f"  Training samples: {results['training_samples']:,}")
        print(f"  Test samples: {results['test_samples']:,}")
        
        print(f"\nModel Performance:")
        print(f"  Training R²: {results['train_r2']:.4f}")
        print(f"  Test R²: {results['test_r2']:.4f}")
        print(f"  Cross-validation R²: {results['cv_r2_mean']:.4f} ± {results['cv_r2_std']:.4f}")
        
        print(f"\nError Metrics:")
        print(f"  Training MAE: ${results['train_mae']:,.0f}")
        print(f"  Test MAE: ${results['test_mae']:,.0f}")
        print(f"  Training RMSE: ${results['train_rmse']:,.0f}")
        print(f"  Test RMSE: ${results['test_rmse']:,.0f}")
        
        print(f"\nTop 10 Most Important Features:")
        for i, (feature, importance) in enumerate(list(results['feature_importance'].items())[:10], 1):
            print(f"  {i:2d}. {feature}: {importance:.4f}")
        
        # Model quality assessment
        if results['test_r2'] >= 0.8:
            quality = "Excellent"
        elif results['test_r2'] >= 0.7:
            quality = "Good"
        elif results['test_r2'] >= 0.6:
            quality = "Fair"
        else:
            quality = "Needs Improvement"
        
        print(f"\nModel Quality: {quality}")
        
        # Recommendations
        print(f"\nRecommendations:")
        if results['test_r2'] < 0.7:
            print("  • Consider collecting more data")
            print("  • Try feature engineering")
            print("  • Experiment with other algorithms")
        else:
            print("  • Model is ready for production use")
            print("  • Consider periodic retraining")
        
        return results
    
    def test_predictions(self, df):
        """Test the model with sample predictions"""
        print(f"\n🧪 Testing Sample Predictions")
        print("-" * 30)
        
        # Get a few sample properties
        samples = df.sample(5)
        
        for idx, row in samples.iterrows():
            # Prepare features
            features = {}
            for col in self.feature_columns:
                if col in row:
                    features[col] = row[col]
                else:
                    features[col] = 0
            
            # Make prediction
            feature_array = np.array([[features[col] for col in self.feature_columns]])
            feature_array_scaled = self.scaler.transform(feature_array)
            predicted_price = self.model.predict(feature_array_scaled)[0]
            actual_price = row['price']
            
            error_pct = abs(predicted_price - actual_price) / actual_price * 100
            
            print(f"\nSample Property:")
            if 'city' in row and 'state' in row:
                print(f"  Location: {row['city']}, {row['state']}")
            if 'bedrooms' in row and 'bathrooms' in row:
                print(f"  Size: {row['bedrooms']}BR/{row['bathrooms']}BA")
            if 'sqft' in row:
                print(f"  Sqft: {row['sqft']:,.0f}")
            print(f"  Actual Price: ${actual_price:,.0f}")
            print(f"  Predicted Price: ${predicted_price:,.0f}")
            print(f"  Error: {error_pct:.1f}%")

def main():
    """Main training function"""
    print("🏠 Real Estate ML Model Training")
    print("=" * 50)
    
    # Initialize trainer
    trainer = PropertyValuationTrainer()
    
    # Load data
    df = trainer.load_and_prepare_data()
    if df is None:
        print("❌ Failed to load data. Exiting.")
        return
    
    # Clean and preprocess
    df_clean = trainer.clean_and_preprocess_data(df)
    if len(df_clean) < 1000:
        print("❌ Insufficient clean data for training. Need at least 1000 records.")
        return
    
    # Create features
    df_features = trainer.create_features(df_clean)
    
    # Train model
    results, X_test, y_test, y_pred = trainer.train_model(df_features)
    
    # Save model
    trainer.save_model()
    
    # Create database
    trainer.create_database(df_clean)
    
    # Generate report
    trainer.generate_report(results, df_features)
    
    # Test predictions
    trainer.test_predictions(df_features)
    
    print(f"\n🎉 Training Complete!")
    print(f"✅ Model saved and ready for use")
    print(f"✅ Database created for market data service")
    print(f"✅ Test R² Score: {results['test_r2']:.4f}")

if __name__ == "__main__":
    main()