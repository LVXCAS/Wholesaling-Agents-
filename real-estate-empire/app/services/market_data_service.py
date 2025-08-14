import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from pathlib import Path
import sqlite3
from ..models.market_data import PropertyRecord, MarketStats, ComparableProperty

class MarketDataService:
    def __init__(self, data_path: str = "data/realtor-data.zip.csv"):
        self.data_path = data_path
        self.db_path = "market_data.db"
        self._df = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize SQLite database for faster queries"""
        if not Path(self.db_path).exists():
            self._load_and_process_data()
    
    def _load_and_process_data(self):
        """Load CSV data and create SQLite database"""
        print("Loading market data...")
        df = pd.read_csv(self.data_path)
        
        # Clean and process data
        df = df.dropna(subset=['city', 'state', 'price'])
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['house_size'] = pd.to_numeric(df['house_size'], errors='coerce')
        df['bed'] = pd.to_numeric(df['bed'], errors='coerce')
        df['bath'] = pd.to_numeric(df['bath'], errors='coerce')
        
        # Calculate price per sqft
        df['price_per_sqft'] = df['price'] / df['house_size']
        
        # Save to SQLite
        conn = sqlite3.connect(self.db_path)
        df.to_sql('properties', conn, if_exists='replace', index=False)
        conn.close()
        print(f"Processed {len(df)} properties")
    
    def get_market_stats(self, city: str, state: str) -> Optional[MarketStats]:
        """Get market statistics for a city/state"""
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT 
            AVG(price) as avg_price,
            AVG(price_per_sqft) as avg_price_per_sqft,
            COUNT(*) as total_listings,
            AVG(bed) as avg_bedrooms,
            AVG(bath) as avg_bathrooms,
            AVG(house_size) as avg_house_size
        FROM properties 
        WHERE LOWER(city) = LOWER(?) AND LOWER(state) = LOWER(?)
        AND price IS NOT NULL
        """
        
        result = pd.read_sql_query(query, conn, params=[city, state])
        conn.close()
        
        if result.empty or result.iloc[0]['total_listings'] == 0:
            return None
            
        row = result.iloc[0]
        
        # Get median price separately
        conn = sqlite3.connect(self.db_path)
        median_query = """
        SELECT price FROM properties 
        WHERE LOWER(city) = LOWER(?) AND LOWER(state) = LOWER(?)
        AND price IS NOT NULL
        ORDER BY price
        """
        prices = pd.read_sql_query(median_query, conn, params=[city, state])
        conn.close()
        
        median_price = prices['price'].median() if not prices.empty else 0
        
        return MarketStats(
            city=city,
            state=state,
            avg_price=float(row['avg_price'] or 0),
            median_price=float(median_price),
            avg_price_per_sqft=float(row['avg_price_per_sqft'] or 0),
            total_listings=int(row['total_listings']),
            avg_bedrooms=float(row['avg_bedrooms'] or 0),
            avg_bathrooms=float(row['avg_bathrooms'] or 0),
            avg_house_size=float(row['avg_house_size'] or 0)
        )
    
    def find_comparables(self, target_property: Dict[str, Any], limit: int = 10) -> List[ComparableProperty]:
        """Find comparable properties"""
        city = target_property.get('city', '')
        state = target_property.get('state', '')
        bedrooms = target_property.get('bedrooms', 0)
        bathrooms = target_property.get('bathrooms', 0)
        house_size = target_property.get('house_size', 0)
        
        conn = sqlite3.connect(self.db_path)
        
        # Find properties in same city/state with similar characteristics
        query = """
        SELECT * FROM properties 
        WHERE LOWER(city) = LOWER(?) AND LOWER(state) = LOWER(?)
        AND price IS NOT NULL
        AND ABS(bed - ?) <= 1
        AND ABS(bath - ?) <= 1
        AND (house_size IS NULL OR ABS(house_size - ?) <= ?)
        ORDER BY 
            ABS(bed - ?) + 
            ABS(bath - ?) + 
            CASE WHEN house_size IS NOT NULL THEN ABS(house_size - ?) / 1000.0 ELSE 0 END
        LIMIT ?
        """
        
        size_tolerance = house_size * 0.3 if house_size > 0 else 1000
        
        df = pd.read_sql_query(query, conn, params=[
            city, state, bedrooms, bathrooms, house_size, size_tolerance,
            bedrooms, bathrooms, house_size, limit
        ])
        conn.close()
        
        comparables = []
        for _, row in df.iterrows():
            prop = PropertyRecord(
                brokered_by=row.get('brokered_by'),
                status=row.get('status', ''),
                price=row.get('price'),
                bed=row.get('bed'),
                bath=row.get('bath'),
                acre_lot=row.get('acre_lot'),
                street=row.get('street'),
                city=row.get('city', ''),
                state=row.get('state', ''),
                zip_code=row.get('zip_code'),
                house_size=row.get('house_size'),
                prev_sold_date=row.get('prev_sold_date')
            )
            
            # Calculate similarity score
            similarity = self._calculate_similarity(target_property, row)
            
            comparables.append(ComparableProperty(
                property=prop,
                similarity_score=similarity,
                distance_factor=1.0  # Same city
            ))
        
        return comparables
    
    def _calculate_similarity(self, target: Dict[str, Any], comp: pd.Series) -> float:
        """Calculate similarity score between properties"""
        score = 100.0
        
        # Bedroom difference penalty
        if target.get('bedrooms') and comp.get('bed'):
            score -= abs(target['bedrooms'] - comp['bed']) * 10
        
        # Bathroom difference penalty
        if target.get('bathrooms') and comp.get('bath'):
            score -= abs(target['bathrooms'] - comp['bath']) * 15
        
        # Size difference penalty
        if target.get('house_size') and comp.get('house_size'):
            size_diff = abs(target['house_size'] - comp['house_size']) / target['house_size']
            score -= size_diff * 30
        
        return max(0, score)
    
    def estimate_property_value(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate property value using comparables"""
        comparables = self.find_comparables(property_data, limit=20)
        
        if not comparables:
            return {"error": "No comparable properties found"}
        
        # Weight prices by similarity
        weighted_prices = []
        total_weight = 0
        
        for comp in comparables:
            if comp.property.price:
                weight = comp.similarity_score / 100.0
                weighted_prices.append(comp.property.price * weight)
                total_weight += weight
        
        if total_weight == 0:
            return {"error": "No valid price data in comparables"}
        
        estimated_value = sum(weighted_prices) / total_weight
        
        # Get price range
        prices = [c.property.price for c in comparables if c.property.price]
        
        return {
            "estimated_value": round(estimated_value),
            "price_range": {
                "min": min(prices),
                "max": max(prices),
                "median": np.median(prices)
            },
            "comparable_count": len(comparables),
            "confidence": min(100, len(comparables) * 5)  # Higher confidence with more comps
        }
    
    def get_top_markets(self, limit: int = 20) -> List[MarketStats]:
        """Get top markets by activity"""
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT 
            city, state,
            AVG(price) as avg_price,
            AVG(price_per_sqft) as avg_price_per_sqft,
            COUNT(*) as total_listings,
            AVG(bed) as avg_bedrooms,
            AVG(bath) as avg_bathrooms,
            AVG(house_size) as avg_house_size
        FROM properties 
        WHERE price IS NOT NULL
        GROUP BY city, state
        HAVING COUNT(*) >= 10
        ORDER BY COUNT(*) DESC
        LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=[limit])
        conn.close()
        
        markets = []
        for _, row in df.iterrows():
            # Get median price
            conn = sqlite3.connect(self.db_path)
            median_query = """
            SELECT price FROM properties 
            WHERE LOWER(city) = LOWER(?) AND LOWER(state) = LOWER(?)
            AND price IS NOT NULL
            ORDER BY price
            """
            prices = pd.read_sql_query(median_query, conn, params=[row['city'], row['state']])
            conn.close()
            
            median_price = prices['price'].median() if not prices.empty else 0
            
            markets.append(MarketStats(
                city=row['city'],
                state=row['state'],
                avg_price=float(row['avg_price']),
                median_price=float(median_price),
                avg_price_per_sqft=float(row['avg_price_per_sqft'] or 0),
                total_listings=int(row['total_listings']),
                avg_bedrooms=float(row['avg_bedrooms'] or 0),
                avg_bathrooms=float(row['avg_bathrooms'] or 0),
                avg_house_size=float(row['avg_house_size'] or 0)
            ))
        
        return markets