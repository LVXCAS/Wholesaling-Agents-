#!/usr/bin/env python3
"""
Test script for market data functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.market_data_service import MarketDataService
from app.services.property_valuation_service import PropertyValuationService
from app.services.investment_analyzer_service import InvestmentAnalyzerService

def test_market_data():
    print("🏠 Testing Real Estate Market Data System")
    print("=" * 50)
    
    # Initialize services
    print("1. Initializing Market Data Service...")
    market_service = MarketDataService()
    
    print("2. Initializing Property Valuation Service...")
    valuation_service = PropertyValuationService(market_service)
    
    print("3. Initializing Investment Analyzer Service...")
    investment_service = InvestmentAnalyzerService(market_service, valuation_service)
    
    # Test market stats
    print("\n📊 Testing Market Statistics...")
    try:
        stats = market_service.get_market_stats("Miami", "Florida")
        if stats:
            print(f"✅ Miami, FL Market Stats:")
            print(f"   Average Price: ${stats.avg_price:,.2f}")
            print(f"   Median Price: ${stats.median_price:,.2f}")
            print(f"   Price per Sq Ft: ${stats.avg_price_per_sqft:.2f}")
            print(f"   Total Listings: {stats.total_listings}")
        else:
            print("❌ No market data found for Miami, FL")
    except Exception as e:
        print(f"❌ Error getting market stats: {e}")
    
    # Test top markets
    print("\n🏆 Testing Top Markets...")
    try:
        top_markets = market_service.get_top_markets(5)
        print(f"✅ Found {len(top_markets)} top markets:")
        for i, market in enumerate(top_markets[:3], 1):
            print(f"   {i}. {market.city}, {market.state} - {market.total_listings} listings")
    except Exception as e:
        print(f"❌ Error getting top markets: {e}")
    
    # Test property valuation
    print("\n💰 Testing Property Valuation...")
    try:
        # Train model first
        print("   Training valuation model...")
        training_result = valuation_service.train_model()
        print(f"   Training result: {training_result.get('status', 'Unknown')}")
        
        # Test prediction
        test_property = {
            'city': 'Miami',
            'state': 'Florida',
            'bedrooms': 3,
            'bathrooms': 2,
            'house_size': 1500,
            'acre_lot': 0.25
        }
        
        prediction = valuation_service.predict_value(test_property)
        if 'predicted_value' in prediction:
            print(f"✅ Property valuation: ${prediction['predicted_value']:,}")
            print(f"   Confidence interval: ${prediction['confidence_interval']['lower']:,} - ${prediction['confidence_interval']['upper']:,}")
        else:
            print(f"❌ Valuation error: {prediction.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Error in property valuation: {e}")
    
    # Test investment analysis
    print("\n📈 Testing Investment Analysis...")
    try:
        test_investment = {
            'city': 'Miami',
            'state': 'Florida',
            'bedrooms': 3,
            'bathrooms': 2,
            'house_size': 1500,
            'asking_price': 350000,
            'estimated_rent': 2500,
            'acre_lot': 0.25
        }
        
        analysis = investment_service.analyze_investment_opportunity(test_investment)
        print(f"✅ Investment Analysis:")
        print(f"   Recommendation: {analysis.recommendation}")
        print(f"   Investment Score: {analysis.investment_metrics.investment_score:.1f}/100")
        print(f"   Cap Rate: {analysis.investment_metrics.cap_rate:.2f}%" if analysis.investment_metrics.cap_rate else "   Cap Rate: N/A")
        print(f"   Monthly Cash Flow: ${analysis.investment_metrics.monthly_cash_flow:,.2f}" if analysis.investment_metrics.monthly_cash_flow else "   Monthly Cash Flow: N/A")
        print(f"   Risk Level: {analysis.investment_metrics.risk_level}")
    except Exception as e:
        print(f"❌ Error in investment analysis: {e}")
    
    # Test comparables
    print("\n🏘️ Testing Comparable Properties...")
    try:
        comparables = market_service.find_comparables(test_property, limit=5)
        print(f"✅ Found {len(comparables)} comparable properties:")
        for i, comp in enumerate(comparables[:3], 1):
            print(f"   {i}. ${comp.property.price:,} - {comp.property.bed}bed/{comp.property.bath}bath - {comp.similarity_score:.1f}% match")
    except Exception as e:
        print(f"❌ Error finding comparables: {e}")
    
    print("\n🎉 Market Data System Test Complete!")
    print("=" * 50)
    print("💡 Next steps:")
    print("   1. Start the API server: python -m app.api.main")
    print("   2. Open market-analysis.html in your browser")
    print("   3. Test the web interface")

if __name__ == "__main__":
    test_market_data()