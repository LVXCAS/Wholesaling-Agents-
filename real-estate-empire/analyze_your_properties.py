"""
Analyze Your Real Properties
Use your enhanced ML system to analyze properties you're actually interested in
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

from demo_complete_analysis import SimplePropertyAnalyzer

async def analyze_your_properties():
    """Analyze properties you're actually interested in"""
    print("🏠 ANALYZE YOUR REAL PROPERTIES")
    print("=" * 50)
    print("Let's analyze some properties you're actually considering!")
    
    analyzer = SimplePropertyAnalyzer()
    
    # You can modify these with real properties you're looking at
    your_properties = [
        {
            'address': 'Enter a real address you\'re considering',
            'asking_price': 450000,  # Change to real asking price
            'bedrooms': 3,
            'bathrooms': 2,
            'sqft': 1800,
            'city': 'Miami',  # Change to real city
            'state': 'Florida',  # Change to real state
            'lot_size': 0.25,
            'estimated_rent': 2800,  # Estimate or research real rent
            'year_built': 2015,
            'property_type': 'Single Family'
        },
        # Add more properties here
        {
            'address': 'Another property you\'re considering',
            'asking_price': 320000,
            'bedrooms': 2,
            'bathrooms': 2,
            'sqft': 1200,
            'city': 'Tampa',
            'state': 'Florida',
            'lot_size': 0.15,
            'estimated_rent': 2100,
            'year_built': 2010,
            'property_type': 'Condo'
        }
    ]
    
    print(f"Analyzing {len(your_properties)} properties...")
    
    for i, property_data in enumerate(your_properties, 1):
        print(f"\n{'='*60}")
        print(f"🏠 PROPERTY {i} ANALYSIS")
        print(f"{'='*60}")
        
        results = await analyzer.analyze_property_complete(property_data)
        
        # Investment recommendation
        investment_score = results['investment_metrics']['investment_score']
        if investment_score >= 80:
            recommendation = "🟢 STRONG BUY"
            action = "This is an excellent investment opportunity!"
        elif investment_score >= 70:
            recommendation = "🟢 BUY"
            action = "This is a good investment opportunity."
        elif investment_score >= 60:
            recommendation = "🟡 CONSIDER"
            action = "Decent investment, analyze carefully."
        elif investment_score >= 40:
            recommendation = "🟠 CAUTION"
            action = "Below average investment, high risk."
        else:
            recommendation = "🔴 AVOID"
            action = "Poor investment opportunity."
        
        print(f"\n🎯 FINAL RECOMMENDATION: {recommendation}")
        print(f"💡 Action: {action}")
        
        # Key insights
        if 'error' not in results['ml_valuation']:
            predicted_value = results['ml_valuation']['predicted_value']
            asking_price = property_data['asking_price']
            equity_potential = predicted_value - asking_price
            
            if equity_potential > 0:
                print(f"💰 Equity Opportunity: ${equity_potential:,.0f} potential profit")
            else:
                print(f"⚠️ Overpriced Warning: ${abs(equity_potential):,.0f} above ML valuation")
        
        cash_flow = results['investment_metrics']['monthly_cash_flow']
        if cash_flow > 0:
            print(f"💸 Positive Cash Flow: ${cash_flow:.0f}/month")
        else:
            print(f"💸 Negative Cash Flow: ${abs(cash_flow):.0f}/month (you'll pay monthly)")
        
        print(f"\n📊 Quick Stats:")
        print(f"  Investment Score: {investment_score:.0f}/100")
        print(f"  Cap Rate: {results['investment_metrics']['cap_rate']:.2f}%")
        print(f"  Cash-on-Cash: {results['investment_metrics']['cash_on_cash_return']:.2f}%")
    
    print(f"\n{'='*60}")
    print("🎉 ANALYSIS COMPLETE!")
    print("=" * 60)
    print("💡 Next Steps:")
    print("  1. Research the neighborhoods in person")
    print("  2. Get professional inspections for top candidates")
    print("  3. Verify rent estimates with local data")
    print("  4. Consider financing options and terms")
    print("  5. Make data-driven offers based on ML valuations")
    
    print(f"\n🚀 You now have superhuman real estate analysis capabilities!")
    print("Use this system to evaluate every property before investing!")

if __name__ == "__main__":
    print("🔧 SETUP INSTRUCTIONS:")
    print("1. Edit the 'your_properties' list above with real properties you're considering")
    print("2. Update addresses, prices, and details with actual data")
    print("3. Run this script to get comprehensive analysis")
    print("4. Use the results to make informed investment decisions!")
    print("\nPress Enter to run with sample data, or Ctrl+C to edit first...")
    input()
    
    asyncio.run(analyze_your_properties())