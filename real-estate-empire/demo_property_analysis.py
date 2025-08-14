"""
Demo: Complete Property Analysis Workflow
Shows how all analysis layers work together
"""
import asyncio
import os
import sys
from pathlib import Path

# Add app directory to path
current_dir = Path(__file__).parent
app_dir = current_dir / "app"
sys.path.insert(0, str(app_dir))

# Set up environment
if not os.getenv('GEMINI_API_KEY'):
    env_path = current_dir / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('GEMINI_API_KEY='):
                    key = line.split('=', 1)[1].strip()
                    os.environ['GEMINI_API_KEY'] = key
                    break

async def demo_complete_property_analysis():
    """Demonstrate complete property analysis workflow"""
    print("🏠 Complete Property Analysis Demo")
    print("=" * 50)
    
    # Sample property data
    property_data = {
        'address': '123 Sunset Boulevard, Miami, FL 33101',
        'price': 485000,
        'asking_price': 485000,
        'bedrooms': 3,
        'bathrooms': 2,
        'sqft': 1850,
        'house_size': 1850,
        'year_built': 2015,
        'property_type': 'Single Family',
        'city': 'Miami',
        'state': 'Florida',
        'acre_lot': 0.25,
        'estimated_rent': 2800
    }
    
    print(f"Analyzing Property: {property_data['address']}")
    print(f"Asking Price: ${property_data['price']:,}")
    print(f"Size: {property_data['bedrooms']}BR/{property_data['bathrooms']}BA, {property_data['sqft']:,} sqft")
    
    # Layer 1: AI Analysis with Gemini
    print(f"\n🤖 Layer 1: AI Analysis (Gemini)")
    print("-" * 30)
    
    try:
        from services.gemini_service import GeminiService
        gemini_service = GeminiService()
        
        ai_analysis = await gemini_service.analyze_property(property_data)
        print(f"✅ AI Analysis Complete (Confidence: {ai_analysis.confidence})")
        print(f"Key Insights: {ai_analysis.content[:200]}...")
        
    except Exception as e:
        print(f"⚠️ AI Analysis unavailable: {e}")
        ai_analysis = None
    
    # Layer 2: Machine Learning Valuation
    print(f"\n📊 Layer 2: ML Valuation")
    print("-" * 30)
    
    try:
        from services.market_data_service import MarketDataService
        from services.property_valuation_service import PropertyValuationService
        
        market_service = MarketDataService()
        valuation_service = PropertyValuationService(market_service)
        
        # Try to load existing model or create mock prediction
        ml_prediction = valuation_service.predict_value(property_data)
        
        if 'error' not in ml_prediction:
            print(f"✅ ML Valuation: ${ml_prediction['predicted_value']:,}")
            print(f"Confidence Interval: ${ml_prediction['confidence_interval']['lower']:,} - ${ml_prediction['confidence_interval']['upper']:,}")
        else:
            print(f"⚠️ ML Valuation: {ml_prediction['error']}")
            # Mock prediction for demo
            ml_prediction = {
                'predicted_value': 475000,
                'confidence_interval': {'lower': 450000, 'upper': 500000}
            }
            print(f"📊 Mock ML Valuation: ${ml_prediction['predicted_value']:,}")
        
    except Exception as e:
        print(f"⚠️ ML Valuation error: {e}")
        ml_prediction = {'predicted_value': 475000, 'confidence_interval': {'lower': 450000, 'upper': 500000}}
    
    # Layer 3: Investment Metrics
    print(f"\n💰 Layer 3: Investment Metrics")
    print("-" * 30)
    
    try:
        from services.investment_analyzer_service import InvestmentAnalyzerService
        
        investment_analyzer = InvestmentAnalyzerService(market_service, valuation_service)
        deal_analysis = investment_analyzer.analyze_investment_opportunity(property_data)
        
        metrics = deal_analysis.investment_metrics
        print(f"✅ Investment Analysis Complete")
        print(f"Investment Score: {metrics.investment_score:.1f}/100")
        print(f"Cap Rate: {metrics.cap_rate:.2f}%" if metrics.cap_rate else "Cap Rate: N/A")
        print(f"Cash-on-Cash Return: {metrics.cash_on_cash_return:.2f}%" if metrics.cash_on_cash_return else "Cash-on-Cash: N/A")
        print(f"Monthly Cash Flow: ${metrics.monthly_cash_flow:.0f}" if metrics.monthly_cash_flow else "Cash Flow: N/A")
        print(f"Risk Level: {metrics.risk_level}")
        print(f"Recommendation: {deal_analysis.recommendation}")
        
    except Exception as e:
        print(f"⚠️ Investment analysis error: {e}")
        # Mock metrics for demo
        print(f"📊 Mock Investment Metrics:")
        print(f"Investment Score: 72.5/100")
        print(f"Cap Rate: 6.8%")
        print(f"Cash-on-Cash Return: 9.2%")
        print(f"Monthly Cash Flow: $425")
        print(f"Risk Level: Medium")
        print(f"Recommendation: BUY - Good investment opportunity")
    
    # Layer 4: Market Comparison
    print(f"\n📈 Layer 4: Market Comparison")
    print("-" * 30)
    
    try:
        market_stats = market_service.get_market_stats('Miami', 'Florida')
        
        if market_stats:
            asking_price = property_data['asking_price']
            price_vs_avg = ((asking_price - market_stats.avg_price) / market_stats.avg_price * 100)
            price_per_sqft = asking_price / property_data['sqft']
            
            print(f"✅ Market Comparison Complete")
            print(f"Market Avg Price: ${market_stats.avg_price:,}")
            print(f"Property Price: ${asking_price:,} ({price_vs_avg:+.1f}% vs market)")
            print(f"Market Avg $/sqft: ${market_stats.avg_price_per_sqft:.0f}")
            print(f"Property $/sqft: ${price_per_sqft:.0f}")
        else:
            print(f"⚠️ No market data available")
            # Mock comparison
            print(f"📊 Mock Market Comparison:")
            print(f"Market Avg Price: $465,000")
            print(f"Property Price: $485,000 (+4.3% vs market)")
            print(f"Market Avg $/sqft: $245")
            print(f"Property $/sqft: $262")
            
    except Exception as e:
        print(f"⚠️ Market comparison error: {e}")
    
    # Summary
    print(f"\n🎯 Analysis Summary")
    print("=" * 50)
    
    estimated_value = ml_prediction.get('predicted_value', 475000)
    asking_price = property_data['asking_price']
    equity_potential = estimated_value - asking_price
    
    print(f"Property Address: {property_data['address']}")
    print(f"Asking Price: ${asking_price:,}")
    print(f"Estimated Value: ${estimated_value:,}")
    print(f"Equity Potential: ${equity_potential:,} ({equity_potential/asking_price*100:+.1f}%)")
    
    if ai_analysis:
        print(f"AI Confidence: {ai_analysis.confidence}")
    
    print(f"\n✅ Complete 4-Layer Analysis Finished!")
    
    return {
        'property_data': property_data,
        'ai_analysis': ai_analysis.content if ai_analysis else None,
        'ml_valuation': ml_prediction,
        'equity_potential': equity_potential
    }

if __name__ == "__main__":
    asyncio.run(demo_complete_property_analysis())