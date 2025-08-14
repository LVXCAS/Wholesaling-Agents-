"""
Create a simple web interface for your property analysis system
"""
import os
from pathlib import Path

def create_web_app():
    """Create a simple Flask web app for property analysis"""
    
    # Create the web app file
    web_app_code = '''
from flask import Flask, render_template, request, jsonify
import asyncio
import sys
from pathlib import Path

# Add app directory to path
current_dir = Path(__file__).parent
app_dir = current_dir / "app"
sys.path.insert(0, str(app_dir))

from demo_complete_analysis import SimplePropertyAnalyzer

app = Flask(__name__)
analyzer = SimplePropertyAnalyzer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_property():
    try:
        data = request.json
        
        property_data = {
            'address': data.get('address', ''),
            'asking_price': float(data.get('asking_price', 0)),
            'bedrooms': int(data.get('bedrooms', 3)),
            'bathrooms': int(data.get('bathrooms', 2)),
            'sqft': int(data.get('sqft', 1500)),
            'city': data.get('city', ''),
            'state': data.get('state', ''),
            'lot_size': float(data.get('lot_size', 0.2)),
            'estimated_rent': float(data.get('estimated_rent', 0)),
            'year_built': int(data.get('year_built', 2010)),
            'property_type': data.get('property_type', 'Single Family')
        }
        
        # Run analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(analyzer.analyze_property_complete(property_data))
        loop.close()
        
        # Format results for web
        response = {
            'success': True,
            'property': property_data,
            'results': results
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
'''
    
    # Create templates directory and HTML
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)
    
    html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real Estate Analysis System</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .results { margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 4px; }
        .recommendation { font-size: 18px; font-weight: bold; margin: 10px 0; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .metric { background: white; padding: 15px; border-radius: 4px; border-left: 4px solid #007bff; }
    </style>
</head>
<body>
    <h1>🏠 Real Estate Analysis System</h1>
    <p>Powered by ML trained on 1.6M+ properties</p>
    
    <form id="analysisForm">
        <div class="form-group">
            <label for="address">Property Address:</label>
            <input type="text" id="address" name="address" required>
        </div>
        
        <div class="form-group">
            <label for="asking_price">Asking Price ($):</label>
            <input type="number" id="asking_price" name="asking_price" required>
        </div>
        
        <div class="form-group">
            <label for="bedrooms">Bedrooms:</label>
            <input type="number" id="bedrooms" name="bedrooms" value="3" required>
        </div>
        
        <div class="form-group">
            <label for="bathrooms">Bathrooms:</label>
            <input type="number" id="bathrooms" name="bathrooms" value="2" step="0.5" required>
        </div>
        
        <div class="form-group">
            <label for="sqft">Square Feet:</label>
            <input type="number" id="sqft" name="sqft" required>
        </div>
        
        <div class="form-group">
            <label for="city">City:</label>
            <input type="text" id="city" name="city" required>
        </div>
        
        <div class="form-group">
            <label for="state">State:</label>
            <input type="text" id="state" name="state" required>
        </div>
        
        <div class="form-group">
            <label for="lot_size">Lot Size (acres):</label>
            <input type="number" id="lot_size" name="lot_size" value="0.25" step="0.01">
        </div>
        
        <div class="form-group">
            <label for="estimated_rent">Estimated Monthly Rent ($):</label>
            <input type="number" id="estimated_rent" name="estimated_rent">
        </div>
        
        <div class="form-group">
            <label for="year_built">Year Built:</label>
            <input type="number" id="year_built" name="year_built" value="2010">
        </div>
        
        <button type="submit">🔍 Analyze Property</button>
    </form>
    
    <div id="results" class="results" style="display: none;">
        <h2>Analysis Results</h2>
        <div id="resultsContent"></div>
    </div>
    
    <script>
        document.getElementById('analysisForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());
            
            document.getElementById('results').style.display = 'none';
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    displayResults(result);
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        });
        
        function displayResults(result) {
            const ml_val = result.results.ml_valuation;
            const investment = result.results.investment_metrics;
            const asking_price = result.property.asking_price;
            
            let html = `
                <div class="recommendation">
                    🎯 Investment Score: ${investment.investment_score.toFixed(0)}/100
                </div>
                
                <div class="metrics">
                    <div class="metric">
                        <h4>🤖 ML Valuation</h4>
                        <p>Predicted: $${ml_val.predicted_value.toLocaleString()}</p>
                        <p>vs Asking: ${((ml_val.predicted_value - asking_price) / asking_price * 100).toFixed(1)}%</p>
                    </div>
                    
                    <div class="metric">
                        <h4>💰 Investment Metrics</h4>
                        <p>Cap Rate: ${investment.cap_rate.toFixed(2)}%</p>
                        <p>Cash-on-Cash: ${investment.cash_on_cash_return.toFixed(2)}%</p>
                    </div>
                    
                    <div class="metric">
                        <h4>💸 Cash Flow</h4>
                        <p>Monthly: $${investment.monthly_cash_flow.toFixed(0)}</p>
                        <p>Annual: $${(investment.monthly_cash_flow * 12).toFixed(0)}</p>
                    </div>
                </div>
            `;
            
            document.getElementById('resultsContent').innerHTML = html;
            document.getElementById('results').style.display = 'block';
        }
    </script>
</body>
</html>
'''
    
    # Write files
    with open("web_app.py", "w") as f:
        f.write(web_app_code)
    
    with open(templates_dir / "index.html", "w") as f:
        f.write(html_template)
    
    print("🌐 Web App Created!")
    print("=" * 30)
    print("Files created:")
    print("  ✅ web_app.py - Flask web application")
    print("  ✅ templates/index.html - Web interface")
    print()
    print("To run your web app:")
    print("  1. pip install flask")
    print("  2. python web_app.py")
    print("  3. Open http://localhost:5000 in your browser")
    print()
    print("🎉 You'll have a web interface for your ML property analysis!")

if __name__ == "__main__":
    create_web_app()