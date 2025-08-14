#!/usr/bin/env python3
"""
Demo script for the AI Data Processor
Creates sample data files, zips them, and demonstrates the processing workflow
"""

import os
import zipfile
import pandas as pd
import json
import tempfile
from datetime import datetime, timedelta
import random
import numpy as np

from app.services.data_processor_service import DataProcessorService

def create_sample_real_estate_data():
    """Create sample real estate datasets"""
    print("🏠 Creating sample real estate datasets...")
    
    # Create temporary directory for sample files
    temp_dir = tempfile.mkdtemp(prefix="sample_data_")
    
    # Dataset 1: Property Sales Data (CSV)
    print("  📊 Creating property sales data...")
    sales_data = []
    for i in range(500):
        sales_data.append({
            'property_id': f'PROP_{i:04d}',
            'address': f'{random.randint(100, 9999)} {random.choice(["Main", "Oak", "Pine", "Elm", "Cedar"])} {random.choice(["St", "Ave", "Dr", "Ln"])}',
            'city': random.choice(['Las Vegas', 'Henderson', 'North Las Vegas', 'Boulder City']),
            'state': 'NV',
            'zip_code': random.choice(['89101', '89102', '89103', '89104', '89105']),
            'sale_price': random.randint(200000, 800000),
            'bedrooms': random.randint(2, 6),
            'bathrooms': round(random.uniform(1.0, 4.5), 1),
            'square_feet': random.randint(1000, 4000),
            'lot_size': round(random.uniform(0.1, 1.0), 2),
            'year_built': random.randint(1980, 2023),
            'property_type': random.choice(['Single Family', 'Condo', 'Townhouse']),
            'sale_date': (datetime.now() - timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d'),
            'days_on_market': random.randint(1, 180),
            'listing_price': lambda x: x + random.randint(-50000, 50000)
        })
        # Fix listing price calculation
        sales_data[i]['listing_price'] = sales_data[i]['sale_price'] + random.randint(-50000, 50000)
    
    sales_df = pd.DataFrame(sales_data)
    sales_file = os.path.join(temp_dir, 'property_sales.csv')
    sales_df.to_csv(sales_file, index=False)
    
    # Dataset 2: Market Trends (Excel)
    print("  📈 Creating market trends data...")
    market_data = []
    for month in range(24):  # 2 years of data
        date = datetime.now() - timedelta(days=30 * month)
        market_data.append({
            'month': date.strftime('%Y-%m'),
            'median_price': random.randint(350000, 450000),
            'avg_days_on_market': random.randint(25, 60),
            'inventory_count': random.randint(800, 1500),
            'price_per_sqft': round(random.uniform(150, 250), 2),
            'new_listings': random.randint(200, 400),
            'closed_sales': random.randint(180, 350),
            'market_temperature': random.choice(['Hot', 'Warm', 'Balanced', 'Cool'])
        })
    
    market_df = pd.DataFrame(market_data)
    market_file = os.path.join(temp_dir, 'market_trends.xlsx')
    market_df.to_excel(market_file, index=False)
    
    # Dataset 3: Property Features (JSON)
    print("  🏡 Creating property features data...")
    features_data = []
    for i in range(200):
        features_data.append({
            'property_id': f'PROP_{i:04d}',
            'features': {
                'pool': random.choice([True, False]),
                'garage': random.choice([True, False]),
                'fireplace': random.choice([True, False]),
                'hardwood_floors': random.choice([True, False]),
                'updated_kitchen': random.choice([True, False]),
                'master_suite': random.choice([True, False])
            },
            'neighborhood_score': round(random.uniform(6.0, 10.0), 1),
            'school_rating': random.randint(6, 10),
            'walkability_score': random.randint(40, 95),
            'crime_index': round(random.uniform(1.0, 5.0), 1),
            'hoa_fee': random.randint(0, 300) if random.choice([True, False]) else 0
        })
    
    features_file = os.path.join(temp_dir, 'property_features.json')
    with open(features_file, 'w') as f:
        json.dump(features_data, f, indent=2)
    
    # Dataset 4: Owner Information (TSV)
    print("  👥 Creating owner information data...")
    owner_data = []
    for i in range(300):
        owner_data.append({
            'property_id': f'PROP_{i:04d}',
            'owner_name': f'Owner {i+1}',
            'owner_type': random.choice(['Individual', 'LLC', 'Trust', 'Corporation']),
            'ownership_duration': random.randint(1, 20),
            'out_of_state': random.choice([True, False]),
            'investment_property': random.choice([True, False]),
            'mortgage_balance': random.randint(0, 400000) if random.choice([True, False]) else 0,
            'equity_percentage': round(random.uniform(20, 100), 1)
        })
    
    owner_df = pd.DataFrame(owner_data)
    owner_file = os.path.join(temp_dir, 'owner_info.tsv')
    owner_df.to_csv(owner_file, sep='\t', index=False)
    
    # Dataset 5: Market Analysis Notes (TXT)
    print("  📝 Creating market analysis notes...")
    notes_content = """
Market Analysis Summary - Las Vegas Real Estate

Key Observations:
- Strong seller's market with low inventory
- Average days on market trending downward
- Price appreciation of 8-12% year over year
- High demand in suburban areas
- Investment activity increasing in certain zip codes

Neighborhood Insights:
- Henderson showing strongest growth
- North Las Vegas emerging as value play
- Luxury market (>$600k) showing resilience
- First-time buyer segment facing affordability challenges

Investment Opportunities:
- Fix-and-flip potential in older neighborhoods
- Buy-and-hold strategies working well
- Short-term rental market expanding
- Commercial real estate showing mixed signals

Data Quality Notes:
- Some properties missing square footage data
- HOA information incomplete for condos
- School ratings need verification
- Crime data may be outdated for some areas
    """
    
    notes_file = os.path.join(temp_dir, 'market_analysis_notes.txt')
    with open(notes_file, 'w') as f:
        f.write(notes_content.strip())
    
    return temp_dir

def create_zip_file(data_dir):
    """Create a ZIP file from the sample data directory"""
    print("📦 Creating ZIP file...")
    
    zip_path = os.path.join(os.path.dirname(data_dir), 'sample_real_estate_data.zip')
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, data_dir)
                zipf.write(file_path, arcname)
                print(f"  ✅ Added {arcname}")
    
    print(f"📦 ZIP file created: {zip_path}")
    return zip_path

def create_ml_schema():
    """Create a sample ML schema for real estate price prediction"""
    return {
        "fields": {
            "sale_price": {
                "type": "float",
                "required": True,
                "description": "Target variable - property sale price"
            },
            "bedrooms": {
                "type": "int",
                "min": 1,
                "max": 10,
                "description": "Number of bedrooms"
            },
            "bathrooms": {
                "type": "float",
                "min": 1.0,
                "max": 10.0,
                "description": "Number of bathrooms"
            },
            "square_feet": {
                "type": "int",
                "min": 500,
                "max": 10000,
                "description": "Living area in square feet"
            },
            "lot_size": {
                "type": "float",
                "min": 0.1,
                "max": 5.0,
                "description": "Lot size in acres"
            },
            "year_built": {
                "type": "int",
                "min": 1900,
                "max": 2024,
                "description": "Year property was built"
            },
            "property_type": {
                "type": "string",
                "enum": ["Single Family", "Condo", "Townhouse"],
                "description": "Type of property"
            },
            "days_on_market": {
                "type": "int",
                "min": 1,
                "max": 365,
                "description": "Days property was on market"
            },
            "neighborhood_score": {
                "type": "float",
                "min": 1.0,
                "max": 10.0,
                "description": "Neighborhood desirability score"
            },
            "school_rating": {
                "type": "int",
                "min": 1,
                "max": 10,
                "description": "Local school district rating"
            }
        },
        "target_variable": "sale_price",
        "ml_task": "regression",
        "preprocessing": {
            "handle_missing": "median",
            "scale_features": True,
            "encode_categorical": "onehot",
            "remove_outliers": True
        },
        "validation": {
            "test_size": 0.2,
            "cross_validation": 5,
            "metrics": ["mae", "rmse", "r2"]
        }
    }

def demo_auto_processing(zip_path):
    """Demo automatic data processing without schema"""
    print("\n🤖 Demo 1: Automatic Data Processing")
    print("=" * 50)
    
    processor = DataProcessorService()
    result = processor.process_zip_file(zip_path, None)
    
    if result['success']:
        print("✅ Processing successful!")
        print(f"📊 Files processed: {len(result['processed_data'])}")
        
        # Show file breakdown
        report = result.get('report', {})
        file_breakdown = report.get('file_breakdown', {})
        print(f"📁 Total files: {file_breakdown.get('total_files', 0)}")
        print(f"📈 Data files: {len(file_breakdown.get('data_files', []))}")
        
        # Show AI insights
        reformatted = result.get('reformatted_data', {})
        if 'gemini_analysis' in reformatted:
            print("\n🧠 AI Analysis:")
            analysis = reformatted['gemini_analysis']
            if isinstance(analysis, dict):
                for key, value in analysis.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {analysis}")
        
        return result
    else:
        print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
        return None

def demo_schema_processing(zip_path, schema):
    """Demo processing with custom ML schema"""
    print("\n🎯 Demo 2: Schema-Based Processing")
    print("=" * 50)
    
    processor = DataProcessorService()
    result = processor.process_zip_file(zip_path, schema)
    
    if result['success']:
        print("✅ Schema-based processing successful!")
        
        # Show mapping insights
        reformatted = result.get('reformatted_data', {})
        if 'gemini_analysis' in reformatted:
            analysis = reformatted['gemini_analysis']
            print("\n🗺️ Mapping Strategy:")
            if isinstance(analysis, dict) and 'mapping_strategy' in analysis:
                print(f"  {analysis['mapping_strategy']}")
            
            print("\n🧹 Cleaning Steps:")
            if isinstance(analysis, dict) and 'cleaning_steps' in analysis:
                steps = analysis['cleaning_steps']
                if isinstance(steps, list):
                    for step in steps:
                        print(f"  • {step}")
                else:
                    print(f"  • {steps}")
        
        return result
    else:
        print(f"❌ Schema processing failed: {result.get('error', 'Unknown error')}")
        return None

def demo_export(result, format='csv'):
    """Demo data export functionality"""
    print(f"\n💾 Demo 3: Export to {format.upper()}")
    print("=" * 50)
    
    processor = DataProcessorService()
    output_file = processor.export_processed_data(result, format)
    
    if output_file and os.path.exists(output_file):
        file_size = os.path.getsize(output_file)
        print(f"✅ Export successful!")
        print(f"📁 File: {output_file}")
        print(f"📊 Size: {file_size:,} bytes")
        return output_file
    else:
        print("❌ Export failed")
        return None

def main():
    """Main demo function"""
    print("🚀 AI Data Processor Demo")
    print("=" * 60)
    print("This demo creates sample real estate data and shows how")
    print("Gemini AI can reformat it for machine learning training.")
    print()
    
    try:
        # Step 1: Create sample data
        data_dir = create_sample_real_estate_data()
        
        # Step 2: Create ZIP file
        zip_path = create_zip_file(data_dir)
        
        # Step 3: Demo auto processing
        auto_result = demo_auto_processing(zip_path)
        
        # Step 4: Demo schema processing
        schema = create_ml_schema()
        print(f"\n📋 Using ML Schema with {len(schema['fields'])} fields:")
        for field, config in list(schema['fields'].items())[:5]:  # Show first 5
            print(f"  • {field}: {config['type']} - {config.get('description', 'No description')}")
        if len(schema['fields']) > 5:
            print(f"  ... and {len(schema['fields']) - 5} more fields")
        
        schema_result = demo_schema_processing(zip_path, schema)
        
        # Step 5: Demo export
        if auto_result:
            csv_file = demo_export(auto_result, 'csv')
            json_file = demo_export(auto_result, 'json')
        
        print("\n🎉 Demo completed successfully!")
        print("\nNext steps:")
        print("1. 🌐 Open the web interface: app/frontend/data-processor.html")
        print("2. 🚀 Start the API server: uvicorn app.api.main:app --reload")
        print("3. 📤 Upload your own ZIP files for AI processing")
        
        # Cleanup
        print(f"\n🧹 Cleaning up temporary files...")
        import shutil
        shutil.rmtree(os.path.dirname(data_dir))
        print("✅ Cleanup complete")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()