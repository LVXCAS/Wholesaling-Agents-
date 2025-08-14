import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.renovation_model import RenovationModel
from tabulate import tabulate
import pytest

def test_renovation_cost_prediction():
    """Test the renovation cost prediction model with various scenarios."""
    model = RenovationModel()
    
    # Define test scenarios
    test_cases = [
        {
            'name': 'Basic Kitchen Renovation',
            'category': 'kitchen',
            'features': {
                'quality': 'basic',
                'sqft': 150,
                'age': 20,
                'region': 'south',
                'material_grade': 2,
                'complexity': 1.0
            }
        },
        {
            'name': 'Luxury Bathroom Remodel',
            'category': 'bathroom',
            'features': {
                'quality': 'luxury',
                'sqft': 100,
                'age': 35,
                'region': 'northeast',
                'material_grade': 5,
                'complexity': 2.5
            }
        },
        {
            'name': 'Medium HVAC Upgrade',
            'category': 'hvac',
            'features': {
                'quality': 'medium',
                'sqft': 2000,
                'age': 15,
                'region': 'midwest',
                'material_grade': 3,
                'complexity': 1.5
            }
        },
        {
            'name': 'Premium Flooring Installation',
            'category': 'flooring',
            'features': {
                'quality': 'luxury',
                'sqft': 2500,
                'age': 0,
                'region': 'west',
                'material_grade': 5,
                'complexity': 2.0
            }
        }
    ]
    
    # Run predictions and collect results
    results = []
    for case in test_cases:
        try:
            # Unpack prediction tuple - we get (cost, confidence, metrics)
            prediction, confidence, _ = model.predict_cost(
                category=case['category'],
                features=case['features']
            )
            
            # Get volatility adjustment
            volatility = model.get_market_volatility_adjustment(case['category'])
            
            results.append([
                case['name'],
                f"${prediction:,.2f}",
                f"{confidence:.1%}",
                f"{volatility:+.1%}",
                "✓"
            ])
        except Exception as e:
            results.append([
                case['name'],
                "ERROR",
                "N/A",
                "N/A",
                f"✗ ({str(e)})"
            ])
    
    # Display results in a nice table
    headers = ["Scenario", "Estimated Cost", "Confidence", "Market Adjustment", "Status"]
    print("\nRenovation Cost Prediction Test Results:")
    print(tabulate(results, headers=headers, tablefmt="grid"))
    
    # Assert that we got valid predictions
    assert all(row[4] == "✓" for row in results), "Some predictions failed"

if __name__ == "__main__":
    test_renovation_cost_prediction()
