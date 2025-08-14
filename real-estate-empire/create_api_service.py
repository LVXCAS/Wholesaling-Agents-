"""
Create a REST API service for your property analysis system
"""

def create_api_service():
    """Create a FastAPI service for property analysis"""
    
    api_code = '''
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio
import sys
from pathlib import Path

# Add app directory to path
current_dir = Path(__file__).parent
app_dir = current_dir / "app"
sys.path.insert(0, str(app_dir))

from demo_complete_analysis import SimplePropertyAnalyzer

app = FastAPI(title="Real Estate Analysis API", version="1.0.0")
analyzer = SimplePropertyAnalyzer()

class PropertyRequest(BaseModel):
    address: str
    asking_price: float
    bedrooms: int
    bathrooms: float
    sqft: int
    city: str
    state: str
    lot_size: Optional[float] = 0.25
    estimated_rent: Optional[float] = None
    year_built: Optional[int] = 2010
    property_type: Optional[str] = "Single Family"

class PropertyResponse(BaseModel):
    success: bool
    property: dict
    ml_valuation: dict
    investment_metrics: dict
    market_stats: Optional[dict]
    recommendation: str
    confidence: float

@app.get("/")
async def root():
    return {
        "message": "Real Estate Analysis API",
        "version": "1.0.0",
        "description": "ML-powered property analysis trained on 1.6M+ properties",
        "endpoints": {
            "analyze": "POST /analyze - Analyze a property",
            "health": "GET /health - Health check"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": analyzer is not None}

@app.post("/analyze", response_model=PropertyResponse)
async def analyze_property(property_request: PropertyRequest):
    try:
        property_data = {
            'address': property_request.address,
            'asking_price': property_request.asking_price,
            'bedrooms': property_request.bedrooms,
            'bathrooms': property_request.bathrooms,
            'sqft': property_request.sqft,
            'city': property_request.city,
            'state': property_request.state,
            'lot_size': property_request.lot_size,
            'estimated_rent': property_request.estimated_rent or property_request.asking_price * 0.007,
            'year_built': property_request.year_built,
            'property_type': property_request.property_type
        }
        
        # Run analysis
        results = await analyzer.analyze_property_complete(property_data)
        
        # Generate recommendation
        investment_score = results['investment_metrics']['investment_score']
        if investment_score >= 80:
            recommendation = "STRONG_BUY"
        elif investment_score >= 70:
            recommendation = "BUY"
        elif investment_score >= 60:
            recommendation = "CONSIDER"
        elif investment_score >= 40:
            recommendation = "CAUTION"
        else:
            recommendation = "AVOID"
        
        # Calculate confidence
        confidence = 0.85 if 'error' not in results['ml_valuation'] else 0.5
        
        return PropertyResponse(
            success=True,
            property=property_data,
            ml_valuation=results['ml_valuation'],
            investment_metrics=results['investment_metrics'],
            market_stats=results.get('market_stats'),
            recommendation=recommendation,
            confidence=confidence
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch_analyze")
async def batch_analyze(properties: list[PropertyRequest]):
    """Analyze multiple properties at once"""
    results = []
    
    for prop in properties:
        try:
            result = await analyze_property(prop)
            results.append(result)
        except Exception as e:
            results.append({
                "success": False,
                "error": str(e),
                "property": prop.dict()
            })
    
    return {"results": results, "total": len(results)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    
    # Create requirements file
    requirements = '''
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
'''
    
    # Create example client
    client_code = '''
import requests
import json

# Example usage of the Real Estate Analysis API

API_BASE = "http://localhost:8000"

def analyze_property(property_data):
    """Analyze a single property"""
    response = requests.post(f"{API_BASE}/analyze", json=property_data)
    return response.json()

def batch_analyze(properties_list):
    """Analyze multiple properties"""
    response = requests.post(f"{API_BASE}/batch_analyze", json=properties_list)
    return response.json()

# Example usage
if __name__ == "__main__":
    # Single property analysis
    property_data = {
        "address": "123 Main St, Miami, FL",
        "asking_price": 450000,
        "bedrooms": 3,
        "bathrooms": 2,
        "sqft": 1800,
        "city": "Miami",
        "state": "Florida",
        "lot_size": 0.25,
        "estimated_rent": 2800
    }
    
    print("🏠 Analyzing single property...")
    result = analyze_property(property_data)
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Batch analysis
    properties = [
        {
            "address": "456 Oak Ave, Austin, TX",
            "asking_price": 520000,
            "bedrooms": 4,
            "bathrooms": 3,
            "sqft": 2200,
            "city": "Austin",
            "state": "Texas"
        },
        {
            "address": "789 Pine St, Atlanta, GA",
            "asking_price": 320000,
            "bedrooms": 2,
            "bathrooms": 2,
            "sqft": 1200,
            "city": "Atlanta",
            "state": "Georgia"
        }
    ]
    
    print("\\n🏠 Analyzing multiple properties...")
    batch_result = batch_analyze(properties)
    print(f"Batch result: {json.dumps(batch_result, indent=2)}")
'''
    
    # Write files
    with open("api_service.py", "w") as f:
        f.write(api_code)
    
    with open("api_requirements.txt", "w") as f:
        f.write(requirements)
    
    with open("api_client_example.py", "w") as f:
        f.write(client_code)
    
    print("🔌 API Service Created!")
    print("=" * 30)
    print("Files created:")
    print("  ✅ api_service.py - FastAPI service")
    print("  ✅ api_requirements.txt - Dependencies")
    print("  ✅ api_client_example.py - Usage examples")
    print()
    print("To run your API service:")
    print("  1. pip install -r api_requirements.txt")
    print("  2. python api_service.py")
    print("  3. Visit http://localhost:8000/docs for API documentation")
    print()
    print("🎉 You'll have a REST API for your ML property analysis!")

if __name__ == "__main__":
    create_api_service()