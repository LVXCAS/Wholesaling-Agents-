"""
Quick Property Analysis - Simple version
Just enter property details and get instant analysis
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

def get_property_input():
    """Get property details from user input"""
    print("🏠 QUICK PROPERTY ANALYSIS")
    print("=" * 40)
    print("Enter property details (press Enter for defaults):")
    
    address = input("Address: ") or "123 Main Street"
    
    try:
        asking_price = float(input("Asking Price ($): ") or "400000")
    except:
        asking_price = 400000
    
    try:
        bedrooms = int(input("Bedrooms: ") or "3")
    except:
        bedrooms = 3
    
    try:
        bathrooms = float(input("Bathrooms: ") or "2")
    except:
        bathrooms = 2
    
    try:
        sqft = int(input("Square Feet: ") or "1800")
    except:
        sqft = 1800
    
    city = input("City: ") or "Miami"
    state = input("State: ") or "Florida"
    
    try:
        estimated_rent = float(input("Estimated Monthly Rent ($): ") or str(asking_price * 0.007))
    except:
        estimated_rent = asking_price * 0.007
    
    return {
        'address': address,
        'asking_price': asking_price,
        'bedrooms': bedrooms,
        'bathrooms': bathrooms,
        'sqft': sqft,
        'city': city,
        'state': state,
        'lot_size': 0.25,
        'estimated_rent': estimated_rent,
        'year_built': 2015,
        'property_type': 'Single Family'
    }

async def quick_analysis():
    """Run quick property analysis"""
    
    analyzer = SimplePropertyAnalyzer()
    
    while True:
        try:
            property_data = get_property_input()
            
            print(f"\n🔍 Analyzing: {property_data['address']}")
            print(f"Price: ${property_data['asking_price']:,} | {property_data['bedrooms']}BR/{property_data['bathrooms']}BA | {property_data['sqft']:,} sqft")
            print("Please wait...")
            
            results = await analyzer.analyze_property_complete(property_data)
            
            # Quick summary
            print(f"\n{'='*50}")
            print(f"🎯 QUICK ANALYSIS RESULTS")
            print(f"{'='*50}")
            
            # ML Valuation
            if 'error' not in results['ml_valuation']:
                predicted_value = results['ml_valuation']['predicted_value']
                asking_price = property_data['asking_price']
                equity_potential = predicted_value - asking_price
                equity_pct = (equity_potential / asking_price) * 100
                
                print(f"🤖 ML Valuation: ${predicted_value:,.0f}")
                if equity_potential > 0:
                    print(f"💰 Equity Potential: +${equity_potential:,.0f} ({equity_pct:+.1f}%) - GOOD DEAL!")
                else:
                    print(f"⚠️ Overpriced: ${abs(equity_potential):,.0f} ({equity_pct:+.1f}%) above ML value")
            
            # Investment metrics
            investment_score = results['investment_metrics']['investment_score']
            cap_rate = results['investment_metrics']['cap_rate']
            cash_flow = results['investment_metrics']['monthly_cash_flow']
            
            print(f"📊 Investment Score: {investment_score:.0f}/100")
            print(f"📈 Cap Rate: {cap_rate:.2f}%")
            
            if cash_flow > 0:
                print(f"💸 Monthly Cash Flow: +${cash_flow:.0f} (POSITIVE!)")
            else:
                print(f"💸 Monthly Cash Flow: ${cash_flow:.0f} (you pay monthly)")
            
            # Market comparison
            if results['market_stats']:
                market_avg = results['market_stats']['avg_price']
                vs_market = ((asking_price - market_avg) / market_avg) * 100
                print(f"🏘️ vs Market Average: {vs_market:+.1f}%")
            
            # Simple recommendation
            if investment_score >= 70 and equity_potential > 0:
                print(f"\n🟢 RECOMMENDATION: BUY - Good investment opportunity!")
            elif investment_score >= 60:
                print(f"\n🟡 RECOMMENDATION: CONSIDER - Analyze carefully")
            elif investment_score >= 40:
                print(f"\n🟠 RECOMMENDATION: CAUTION - Below average investment")
            else:
                print(f"\n🔴 RECOMMENDATION: AVOID - Poor investment opportunity")
            
            # Ask for another analysis
            print(f"\n" + "="*50)
            another = input("Analyze another property? (y/n): ").lower()
            if another != 'y':
                break
                
        except KeyboardInterrupt:
            print(f"\n\n👋 Thanks for using the Real Estate Analysis System!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    
    print(f"\n🎉 Analysis complete! You now have superhuman real estate analysis capabilities!")

if __name__ == "__main__":
    asyncio.run(quick_analysis())