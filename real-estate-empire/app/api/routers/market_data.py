from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from ...services.market_data_service import MarketDataService
from ...models.market_data import MarketStats, ComparableProperty

router = APIRouter(prefix="/market-data", tags=["market-data"])
market_service = MarketDataService()

@router.get("/stats/{city}/{state}", response_model=MarketStats)
async def get_market_stats(city: str, state: str):
    """Get market statistics for a specific city and state"""
    stats = market_service.get_market_stats(city, state)
    if not stats:
        raise HTTPException(status_code=404, detail="No market data found for this location")
    return stats

@router.post("/comparables")
async def find_comparables(property_data: Dict[str, Any], limit: int = Query(10, ge=1, le=50)):
    """Find comparable properties for valuation"""
    try:
        comparables = market_service.find_comparables(property_data, limit)
        return {
            "comparables": [
                {
                    "property": {
                        "price": comp.property.price,
                        "bedrooms": comp.property.bed,
                        "bathrooms": comp.property.bath,
                        "house_size": comp.property.house_size,
                        "city": comp.property.city,
                        "state": comp.property.state,
                        "zip_code": comp.property.zip_code,
                        "price_per_sqft": comp.property.price_per_sqft,
                        "status": comp.property.status
                    },
                    "similarity_score": comp.similarity_score,
                    "distance_factor": comp.distance_factor
                }
                for comp in comparables
            ],
            "total_found": len(comparables)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/estimate-value")
async def estimate_property_value(property_data: Dict[str, Any]):
    """Estimate property value using comparable sales"""
    try:
        estimation = market_service.estimate_property_value(property_data)
        return estimation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-markets")
async def get_top_markets(limit: int = Query(20, ge=1, le=100)):
    """Get top markets by listing activity"""
    try:
        markets = market_service.get_top_markets(limit)
        return {
            "markets": [
                {
                    "city": market.city,
                    "state": market.state,
                    "avg_price": market.avg_price,
                    "median_price": market.median_price,
                    "avg_price_per_sqft": market.avg_price_per_sqft,
                    "total_listings": market.total_listings,
                    "avg_bedrooms": market.avg_bedrooms,
                    "avg_bathrooms": market.avg_bathrooms,
                    "avg_house_size": market.avg_house_size
                }
                for market in markets
            ],
            "total_markets": len(markets)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_properties(
    city: Optional[str] = None,
    state: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_bedrooms: Optional[int] = None,
    max_bedrooms: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """Search properties with filters"""
    try:
        import sqlite3
        import pandas as pd
        
        conn = sqlite3.connect(market_service.db_path)
        
        conditions = ["price IS NOT NULL"]
        params = []
        
        if city:
            conditions.append("LOWER(city) = LOWER(?)")
            params.append(city)
        
        if state:
            conditions.append("LOWER(state) = LOWER(?)")
            params.append(state)
        
        if min_price:
            conditions.append("price >= ?")
            params.append(min_price)
        
        if max_price:
            conditions.append("price <= ?")
            params.append(max_price)
        
        if min_bedrooms:
            conditions.append("bed >= ?")
            params.append(min_bedrooms)
        
        if max_bedrooms:
            conditions.append("bed <= ?")
            params.append(max_bedrooms)
        
        query = f"""
        SELECT * FROM properties 
        WHERE {' AND '.join(conditions)}
        ORDER BY price DESC
        LIMIT ?
        """
        params.append(limit)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        properties = []
        for _, row in df.iterrows():
            properties.append({
                "price": row.get('price'),
                "bedrooms": row.get('bed'),
                "bathrooms": row.get('bath'),
                "house_size": row.get('house_size'),
                "city": row.get('city'),
                "state": row.get('state'),
                "zip_code": row.get('zip_code'),
                "price_per_sqft": row.get('price_per_sqft'),
                "status": row.get('status'),
                "acre_lot": row.get('acre_lot')
            })
        
        return {
            "properties": properties,
            "total_found": len(properties)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))