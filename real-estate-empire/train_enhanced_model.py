"""
Enhanced ML Model Training with Multiple Data Sources
Combines property sales data with Zillow rent and home value data
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
import warnings
warnings.filterwarnings('ignore')

class EnhancedPropertyTrainer:
    def __init__(self):
        self.model = None
        self.encoders = {}
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.model_path = "enhanced_property_model.joblib"
        self.encoders_path = "enhanced_encoders.joblib"
        self.scaler_path = "enhanced_scaler.joblib"
        self.db_path = "enhanced_real_estate_data.db"
        
    def load_property_sales_data(self):
        """Load the original property sales data"""
        print("📊 Loading property sales data...")
        
        try:
            df = pd.read_csv("data/realtor-data.zip.csv")
            print(f"✅ Loaded {len(df):,} property sales records")
            
            # Standardize column names
            column_mapping = {
                'price': 'price',
                'bed': 'bedrooms',
                'bath': 'bathrooms',
                'house_size': 'sqft',
                'acre_lot': 'lot_size',
                'city': 'city',
                'state': 'state',
                'zip_code': 'zip_code'
            }
            
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    df = df.rename(columns={old_name: new_name})
            
            return df
            
        except Exception as e:
            print(f"❌ Error loading property sales data: {e}")
            return None
    
    def load_zillow_rent_data(self):
        """Load Zillow rent data (ZORI)"""
        print("🏠 Loading Zillow rent data...")
        
        try:
            df = pd.read_csv("data/Metro_zori_uc_sfrcondomfr_sm_month.csv")
            print(f"✅ Loaded {len(df):,} metro rent records")
            
            # Get the most recent rent data (latest available month)
            date_columns = [col for col in df.columns if col.startswith('20') or col.startswith('19')]
            latest_date = max(date_columns)
            
            # Create rent lookup table
            rent_data = df[['RegionName', 'StateName', latest_date]].copy()
            rent_data = rent_data.rename(columns={
                'RegionName': 'metro_area',
                'StateName': 'state',
                latest_date: 'metro_rent'
            })
            
            # Clean metro names (remove state abbreviations)
            rent_data['metro_area'] = rent_data['metro_area'].str.replace(r', [A-Z]{2}$', '', regex=True)
            
            print(f"Using rent data from: {latest_date}")
            print(f"Sample metro rents:")
            print(rent_data.head())
            
            return rent_data
            
        except Exception as e:
            print(f"❌ Error loading Zillow rent data: {e}")
            return None
    
    def load_zillow_home_values(self):
        """Load Zillow home value data (ZHVI)"""
        print("🏡 Loading Zillow home value data...")
        
        try:
            # Load different tiers of home values
            zhvi_files = [
                "data/Metro_zhvi_uc_sfrcondo_tier_0.0_0.33_sm_sa_month.csv",
                "data/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv", 
                "data/Metro_zhvi_uc_sfrcondo_tier_0.67_1.0_sm_sa_month.csv"
            ]
            
            home_value_data = []
            
            for file_path in zhvi_files:
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    
                    # Get latest date
                    date_columns = [col for col in df.columns if col.startswith('20') or col.startswith('19')]
                    if date_columns:
                        latest_date = max(date_columns)
                        
                        tier_data = df[['RegionName', 'StateName', latest_date]].copy()
                        tier_data['tier'] = file_path.split('_')[-4] + '_' + file_path.split('_')[-3]
                        tier_data = tier_data.rename(columns={
                            'RegionName': 'metro_area',
                            'StateName': 'state',
                            latest_date: 'home_value'
                        })
                        
                        # Clean metro names
                        tier_data['metro_area'] = tier_data['metro_area'].str.replace(r', [A-Z]{2}$', '', regex=True)
                        
                        home_value_data.append(tier_data)
            
            if home_value_data:
                # Combine all tiers and take average
                combined_hv = pd.concat(home_value_data, ignore_index=True)
                avg_home_values = combined_hv.groupby(['metro_area', 'state'])['home_value'].mean().reset_index()
                
                print(f"✅ Processed home value data for {len(avg_home_values)} metros")
                print("Sample home values:")
                print(avg_home_values.head())
                
                return avg_home_values
            else:
                print("⚠️ No home value files found")
                return None
                
        except Exception as e:
            print(f"❌ Error loading home value data: {e}")
            return None
    
    def create_metro_mapping(self, property_df):
        """Create mapping from cities to metro areas"""
        print("🗺️ Creating city to metro mapping...")
        
        # Common metro area mappings
        metro_mappings = {
            # Major metros
            'Miami': 'Miami-Fort Lauderdale-West Palm Beach',
            'Fort Lauderdale': 'Miami-Fort Lauderdale-West Palm Beach',
            'West Palm Beach': 'Miami-Fort Lauderdale-West Palm Beach',
            'Orlando': 'Orlando-Kissimmee-Sanford',
            'Tampa': 'Tampa-St. Petersburg-Clearwater',
            'St Petersburg': 'Tampa-St. Petersburg-Clearwater',
            'Jacksonville': 'Jacksonville',
            'Atlanta': 'Atlanta-Sandy Springs-Roswell',
            'Austin': 'Austin-Round Rock',
            'Houston': 'Houston-The Woodlands-Sugar Land',
            'Dallas': 'Dallas-Fort Worth-Arlington',
            'Fort Worth': 'Dallas-Fort Worth-Arlington',
            'San Antonio': 'San Antonio-New Braunfels',
            'Phoenix': 'Phoenix-Mesa-Scottsdale',
            'Los Angeles': 'Los Angeles-Long Beach-Anaheim',
            'San Diego': 'San Diego-Carlsbad',
            'San Francisco': 'San Francisco-Oakland-Hayward',
            'Oakland': 'San Francisco-Oakland-Hayward',
            'San Jose': 'San Jose-Sunnyvale-Santa Clara',
            'Seattle': 'Seattle-Tacoma-Bellevue',
            'Portland': 'Portland-Vancouver-Hillsboro',
            'Denver': 'Denver-Aurora-Lakewood',
            'Las Vegas': 'Las Vegas-Henderson-Paradise',
            'Chicago': 'Chicago-Naperville-Elgin',
            'Detroit': 'Detroit-Warren-Dearborn',
            'Minneapolis': 'Minneapolis-St. Paul-Bloomington',
            'Boston': 'Boston-Cambridge-Newton',
            'New York': 'New York-Newark-Jersey City',
            'Philadelphia': 'Philadelphia-Camden-Wilmington',
            'Washington': 'Washington-Arlington-Alexandria',
            'Baltimore': 'Baltimore-Columbia-Towson',
            'Charlotte': 'Charlotte-Concord-Gastonia',
            'Raleigh': 'Raleigh',
            'Nashville': 'Nashville-Davidson--Murfreesboro--Franklin',
            'Memphis': 'Memphis',
            'New Orleans': 'New Orleans-Metairie',
            'Kansas City': 'Kansas City',
            'St Louis': 'St. Louis',
            'Cincinnati': 'Cincinnati',
            'Cleveland': 'Cleveland-Elyria',
            'Columbus': 'Columbus',
            'Indianapolis': 'Indianapolis-Carmel-Anderson',
            'Milwaukee': 'Milwaukee-Waukesha-West Allis',
            'Pittsburgh': 'Pittsburgh',
            'Salt Lake City': 'Salt Lake City',
            'Richmond': 'Richmond',
            'Virginia Beach': 'Virginia Beach-Norfolk-Newport News'
        }
        
        # Create reverse mapping for property data
        property_df['metro_area'] = property_df['city'].map(metro_mappings)
        
        # For unmapped cities, use the city name as metro area
        property_df['metro_area'] = property_df['metro_area'].fillna(property_df['city'])
        
        mapped_count = property_df['metro_area'].notna().sum()
        print(f"✅ Mapped {mapped_count:,} properties to metro areas")
        
        return property_df
    
    def merge_datasets(self, property_df, rent_data, home_value_data):
        """Merge all datasets together"""
        print("🔗 Merging datasets...")
        
        original_count = len(property_df)
        
        # Merge with rent data
        if rent_data is not None:
            property_df = property_df.merge(
                rent_data[['metro_area', 'state', 'metro_rent']], 
                on=['metro_area', 'state'], 
                how='left'
            )
            rent_matches = property_df['metro_rent'].notna().sum()
            print(f"✅ Matched {rent_matches:,} properties with rent data")
        
        # Merge with home value data
        if home_value_data is not None:
            property_df = property_df.merge(
                home_value_data[['metro_area', 'state', 'home_value']], 
                on=['metro_area', 'state'], 
                how='left'
            )
            hv_matches = property_df['home_value'].notna().sum()
            print(f"✅ Matched {hv_matches:,} properties with home value data")
        
        print(f"Final dataset: {len(property_df):,} properties with enhanced features")
        
        return property_df
    
    def clean_and_engineer_features(self, df):
        """Clean data and create enhanced features"""
        print("🔧 Cleaning and engineering features...")
        
        original_size = len(df)
        
        # Basic cleaning (same as before)
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df = df[(df['price'] >= 10000) & (df['price'] <= 50000000)]
        
        numeric_columns = ['bedrooms', 'bathrooms', 'sqft', 'lot_size']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove unrealistic values
        df = df[(df['bedrooms'] >= 0) & (df['bedrooms'] <= 20)]
        df = df[(df['bathrooms'] >= 0) & (df['bathrooms'] <= 20)]
        df = df[(df['sqft'] >= 100) & (df['sqft'] <= 50000)]
        
        # Remove rows with missing price
        df = df.dropna(subset=['price'])
        
        # Fill missing values
        for col in df.columns:
            if col != 'price':
                if df[col].dtype in ['object', 'string']:
                    df[col] = df[col].fillna('Unknown')
                else:
                    df[col] = df[col].fillna(df[col].median())
        
        print(f"After cleaning: {len(df):,} records ({len(df)/original_size*100:.1f}% retained)")
        
        # Enhanced feature engineering
        print("Creating enhanced features...")
        
        # Basic derived features
        df['sqft_per_bedroom'] = df['sqft'] / (df['bedrooms'] + 1)
        df['sqft_per_bathroom'] = df['sqft'] / (df['bathrooms'] + 1)
        
        # Price ratios (if we have market data)
        if 'metro_rent' in df.columns:
            df['price_to_rent_ratio'] = df['price'] / (df['metro_rent'] * 12)
            df['rent_yield'] = (df['metro_rent'] * 12) / df['price'] * 100
        
        if 'home_value' in df.columns:
            df['price_vs_metro_value'] = df['price'] / df['home_value']
        
        # Market context features
        if 'metro_rent' in df.columns and 'sqft' in df.columns:
            df['rent_per_sqft'] = df['metro_rent'] / df['sqft']
        
        # Create feature list
        feature_columns = ['bedrooms', 'bathrooms', 'sqft', 'lot_size']
        
        # Add encoded categorical features
        categorical_features = ['city', 'state', 'metro_area']
        for col in categorical_features:
            if col in df.columns:
                print(f"Encoding {col}...")
                self.encoders[col] = LabelEncoder()
                df[f'{col}_encoded'] = self.encoders[col].fit_transform(df[col].astype(str))
                feature_columns.append(f'{col}_encoded')
        
        # Add derived features
        derived_features = ['sqft_per_bedroom', 'sqft_per_bathroom']
        if 'metro_rent' in df.columns:
            derived_features.extend(['price_to_rent_ratio', 'rent_yield', 'rent_per_sqft'])
        if 'home_value' in df.columns:
            derived_features.append('price_vs_metro_value')
        
        for feature in derived_features:
            if feature in df.columns:
                feature_columns.append(feature)
        
        # Add market data features directly
        if 'metro_rent' in df.columns:
            feature_columns.append('metro_rent')
        if 'home_value' in df.columns:
            feature_columns.append('home_value')
        
        self.feature_columns = feature_columns
        print(f"Created {len(feature_columns)} features: {feature_columns}")
        
        return df
    
    def train_enhanced_model(self, df):
        """Train the enhanced Random Forest model"""
        print("\n🤖 Training Enhanced Random Forest Model...")
        
        # Prepare features and target
        X = df[self.feature_columns].fillna(0)
        y = df['price']
        
        print(f"Training data shape: {X.shape}")
        print(f"Features: {self.feature_columns}")
        print(f"Target range: ${y.min():,.0f} - ${y.max():,.0f}")
        print(f"Target median: ${y.median():,.0f}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train enhanced Random Forest
        self.model = RandomForestRegressor(
            n_estimators=300,  # More trees
            max_depth=30,      # Deeper trees
            min_samples_split=3,
            min_samples_leaf=1,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1,
            verbose=1
        )
        
        print("Training enhanced model...")
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
    
    def save_enhanced_model(self):
        """Save the enhanced model and preprocessors"""
        print("\n💾 Saving enhanced model...")
        
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.encoders, self.encoders_path)
        joblib.dump(self.scaler, self.scaler_path)
        
        print(f"✅ Enhanced model saved to {self.model_path}")
        print(f"✅ Encoders saved to {self.encoders_path}")
        print(f"✅ Scaler saved to {self.scaler_path}")
    
    def create_enhanced_database(self, df):
        """Create enhanced SQLite database"""
        print(f"\n🗄️ Creating enhanced database...")
        
        conn = sqlite3.connect(self.db_path)
        df.to_sql('properties', conn, if_exists='replace', index=False)
        
        # Create indexes
        cursor = conn.cursor()
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_city ON properties(city)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_state ON properties(state)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metro ON properties(metro_area)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_price ON properties(price)")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Enhanced database created: {self.db_path}")
        print(f"✅ Saved {len(df):,} records with enhanced features")
    
    def generate_enhanced_report(self, results, df):
        """Generate comprehensive training report"""
        print(f"\n📊 ENHANCED MODEL TRAINING REPORT")
        print("=" * 60)
        
        print(f"Dataset Statistics:")
        print(f"  Total records: {len(df):,}")
        print(f"  Training samples: {results['training_samples']:,}")
        print(f"  Test samples: {results['test_samples']:,}")
        print(f"  Features used: {len(self.feature_columns)}")
        
        print(f"\nEnhanced Model Performance:")
        print(f"  Training R²: {results['train_r2']:.4f}")
        print(f"  Test R²: {results['test_r2']:.4f}")
        print(f"  Cross-validation R²: {results['cv_r2_mean']:.4f} ± {results['cv_r2_std']:.4f}")
        
        print(f"\nError Metrics:")
        print(f"  Training MAE: ${results['train_mae']:,.0f}")
        print(f"  Test MAE: ${results['test_mae']:,.0f}")
        print(f"  Training RMSE: ${results['train_rmse']:,.0f}")
        print(f"  Test RMSE: ${results['test_rmse']:,.0f}")
        
        print(f"\nTop 15 Most Important Features:")
        for i, (feature, importance) in enumerate(list(results['feature_importance'].items())[:15], 1):
            print(f"  {i:2d}. {feature}: {importance:.4f}")
        
        # Enhanced features analysis
        enhanced_features = [f for f in self.feature_columns if any(x in f for x in ['rent', 'value', 'ratio', 'yield'])]
        if enhanced_features:
            print(f"\nEnhanced Features Added:")
            for feature in enhanced_features:
                if feature in results['feature_importance']:
                    importance = results['feature_importance'][feature]
                    print(f"  • {feature}: {importance:.4f} importance")
        
        # Model quality assessment
        if results['test_r2'] >= 0.8:
            quality = "Excellent"
        elif results['test_r2'] >= 0.7:
            quality = "Good"
        elif results['test_r2'] >= 0.6:
            quality = "Fair"
        else:
            quality = "Needs Improvement"
        
        print(f"\nEnhanced Model Quality: {quality}")
        
        # Data coverage analysis
        if 'metro_rent' in df.columns:
            rent_coverage = df['metro_rent'].notna().sum() / len(df) * 100
            print(f"\nData Coverage:")
            print(f"  Properties with rent data: {rent_coverage:.1f}%")
        
        if 'home_value' in df.columns:
            hv_coverage = df['home_value'].notna().sum() / len(df) * 100
            print(f"  Properties with home value data: {hv_coverage:.1f}%")
        
        return results

def main():
    """Main enhanced training function"""
    print("🏠 Enhanced Real Estate ML Model Training")
    print("=" * 60)
    print("Combining property sales + Zillow rent + home value data")
    
    trainer = EnhancedPropertyTrainer()
    
    # Load all datasets
    property_df = trainer.load_property_sales_data()
    if property_df is None:
        print("❌ Failed to load property data. Exiting.")
        return
    
    rent_data = trainer.load_zillow_rent_data()
    home_value_data = trainer.load_zillow_home_values()
    
    # Create metro mapping
    property_df = trainer.create_metro_mapping(property_df)
    
    # Merge datasets
    enhanced_df = trainer.merge_datasets(property_df, rent_data, home_value_data)
    
    # Clean and engineer features
    final_df = trainer.clean_and_engineer_features(enhanced_df)
    
    if len(final_df) < 1000:
        print("❌ Insufficient clean data for training.")
        return
    
    # Train enhanced model
    results, X_test, y_test, y_pred = trainer.train_enhanced_model(final_df)
    
    # Save model
    trainer.save_enhanced_model()
    
    # Create database
    trainer.create_enhanced_database(final_df)
    
    # Generate report
    trainer.generate_enhanced_report(results, final_df)
    
    print(f"\n🎉 Enhanced Training Complete!")
    print(f"✅ Model trained with {len(trainer.feature_columns)} features")
    print(f"✅ Enhanced R² Score: {results['test_r2']:.4f}")
    print(f"✅ Includes rent and home value market data")
    print(f"✅ Ready for superior property analysis!")

if __name__ == "__main__":
    main()