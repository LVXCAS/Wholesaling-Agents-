#!/usr/bin/env python3
"""
Test script to demonstrate the renovation cost prediction model with various scenarios.
"""
import os
import sys
from pathlib import Path
import json
from datetime import datetime
from tabulate import tabulate
import pandas as pd

# Add the project root directory to the Python path
project_root = str(Path(__file__).resolve().parent.parent)
sys.path.append(project_root)

from app.models.renovation_model import RenovationModel

def format_currency(amount):
    """Format amount as currency."""
    return f"${amount:,.2f}"

def test_scenarios():
    """Test various renovation scenarios and display results."""
    print("Initializing Renovation Cost Model...")
    model = RenovationModel()
    
    # Define test scenarios
    scenarios = [
        {
            "name": "Small Kitchen Basic Renovation",
            "category": "kitchen",
            "features": {
                "sqft": 100,
                "quality": "basic",
                "region": "south",
                "age": 15,
                "complexity": 1,
                "material_grade": 2
            }
        },
        {
            "name": "Large Luxury Kitchen Remodel",
            "category": "kitchen",
            "features": {
                "sqft": 300,
                "quality": "luxury",
                "region": "northeast",
                "age": 25,
                "complexity": 3,
                "material_grade": 5
            }
        },
        {
            "name": "Medium Bathroom Update",
            "category": "bathroom",
            "features": {
                "sqft": 80,
                "quality": "medium",
                "region": "west",
                "age": 20,
                "complexity": 2,
                "material_grade": 3
            }
        },
        {
            "name": "Full House Flooring",
            "category": "flooring",
            "features": {
                "sqft": 2000,
                "quality": "medium",
                "region": "midwest",
                "age": 10,
                "complexity": 1,
                "material_grade": 3
            }
        },
        {
            "name": "High-End HVAC System",
            "category": "hvac",
            "features": {
                "sqft": 3000,
                "quality": "luxury",
                "region": "west",
                "age": 30,
                "complexity": 2,
                "material_grade": 5
            }
        }
    ]
    
    # Run predictions
    results = []
    for scenario in scenarios:
        print(f"\nAnalyzing: {scenario['name']}...")
        
        predicted_cost, confidence_score, metrics = model.predict_cost(
            scenario['category'],
            scenario['features']
        )
        
        # Get feature importance for this category
        feature_importance = model.feature_importances.get(scenario['category'], {})
        top_features = sorted(
            feature_importance.get('selected_features', []),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        results.append({
            'Scenario': scenario['name'],
            'Category': scenario['category'].title(),
            'Predicted Cost': format_currency(predicted_cost),
            'Confidence Score': f"{confidence_score:.2%}",
            'Important Features': ', '.join([f"{f[0]} ({f[1]:.3f})" for f in top_features]),
            'Square Footage': scenario['features']['sqft'],
            'Quality Level': scenario['features']['quality'].title(),
            'Region': scenario['features']['region'].title(),
        })
        
        # Show detailed metrics
        print("\nDetailed Metrics:")
        print(f"Prediction Standard Deviation: {metrics.get('prediction_std', 0):,.2f}")
        print(f"Prediction Range: {metrics.get('prediction_range', 0):,.2f}")
        print(f"Model Base Confidence: {metrics.get('base_confidence', 0):.2%}")
        print(f"Market Volatility Factor: {metrics.get('market_volatility', 0):.2%}")
        
        # Show individual model predictions
        if 'individual_predictions' in metrics:
            print("\nIndividual Model Predictions:")
            for model_name, pred in metrics['individual_predictions'].items():
                print(f"{model_name.upper()}: {format_currency(pred)}")
        
        print("-" * 80)
    
    # Display summary table
    print("\nSummary of Renovation Cost Predictions:")
    print(tabulate(
        results,
        headers='keys',
        tablefmt='grid',
        numalign='right',
        stralign='left'
    ))

if __name__ == "__main__":
    test_scenarios()
