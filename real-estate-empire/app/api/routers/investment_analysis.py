from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from ...services.market_data_service import MarketDataService
from ...services.property_valuation_service import PropertyValuationService
from ...services.investment_analyzer_service import InvestmentAnalyzerService

router = APIRouter(prefix="/investment-analysis", tags=["investment-analysis"])

# Initialize services
market_service = MarketDataService()
valuation_service = PropertyValuationService(market_service)
investment_service = InvestmentAnalyzerService(market_service, valuation_service)

@router.post("/analyze-deal")
async def analyze_investment_deal(property_data: Dict[str, Any]):
    """Comprehensive investment analysis of a property deal"""
    try:
        analysis = investment_service.analyze_investment_opportunity(property_data)
        
        return {
            "property": {
                "asking_price": analysis.asking_price,
                "estimated_value": analysis.estimated_value,
                "equity_potential": analysis.equity_potential,
                "equity_percentage": (analysis.equity_potential / analysis.asking_price * 100) if analysis.asking_price > 0 else 0
            },
            "investment_metrics": {
                "cap_rate": analysis.investment_metrics.cap_rate,
                "cash_on_cash_return": analysis.investment_metrics.cash_on_cash_return,
                "roi": analysis.investment_metrics.roi,
                "monthly_cash_flow": analysis.investment_metrics.monthly_cash_flow,
                "break_even_ratio": analysis.investment_metrics.break_even_ratio,
                "price_to_rent_ratio": analysis.investment_metrics.price_to_rent_ratio,
                "investment_score": analysis.investment_metrics.investment_score,
                "risk_level": analysis.investment_metrics.risk_level
            },
            "market_comparison": analysis.market_comparison,
            "recommendation": analysis.recommendation,
            "confidence_score": analysis.confidence_score
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-analyze")
async def batch_analyze_deals(properties: List[Dict[str, Any]]):
    """Analyze multiple investment opportunities"""
    try:
        results = []
        for prop in properties:
            analysis = investment_service.analyze_investment_opportunity(prop)
            results.append({
                "property_id": prop.get('id', len(results)),
                "address": f"{prop.get('city', '')}, {prop.get('state', '')}",
                "asking_price": analysis.asking_price,
                "investment_score": analysis.investment_metrics.investment_score,
                "monthly_cash_flow": analysis.investment_metrics.monthly_cash_flow,
                "cap_rate": analysis.investment_metrics.cap_rate,
                "recommendation": analysis.recommendation,
                "risk_level": analysis.investment_metrics.risk_level
            })
        
        # Sort by investment score
        results.sort(key=lambda x: x['investment_score'], reverse=True)
        
        return {
            "analyzed_properties": results,
            "total_analyzed": len(results),
            "top_opportunities": results[:5]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train-valuation-model")
async def train_valuation_model(retrain: bool = False):
    """Train or retrain the property valuation model"""
    try:
        result = valuation_service.train_model(retrain=retrain)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict-value")
async def predict_property_value(property_data: Dict[str, Any]):
    """Predict property value using ML model"""
    try:
        prediction = valuation_service.predict_value(property_data)
        return prediction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model-info")
async def get_model_info():
    """Get information about the valuation model"""
    try:
        feature_importance = valuation_service.get_feature_importance()
        return {
            "model_type": "Random Forest Regressor",
            "feature_importance": feature_importance,
            "model_trained": valuation_service.model is not None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-metrics")
async def calculate_investment_metrics(property_data: Dict[str, Any]):
    """Calculate investment metrics for a property"""
    try:
        metrics = investment_service._calculate_investment_metrics(property_data)
        
        return {
            "cap_rate": metrics.cap_rate,
            "cash_on_cash_return": metrics.cash_on_cash_return,
            "roi": metrics.roi,
            "monthly_cash_flow": metrics.monthly_cash_flow,
            "break_even_ratio": metrics.break_even_ratio,
            "price_to_rent_ratio": metrics.price_to_rent_ratio,
            "investment_score": metrics.investment_score,
            "risk_level": metrics.risk_level
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))