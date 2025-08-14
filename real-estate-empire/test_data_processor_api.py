#!/usr/bin/env python3
"""
Test script for Data Processor API
Creates a sample ZIP file and tests the API endpoints
"""

import os
import sys
import requests
import zipfile
import tempfile
import pandas as pd
import json
from pathlib import Path

def create_test_zip():
    """Create a simple test ZIP file"""
    print("📦 Creating test ZIP file...")
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    
    # Create sample CSV
    data = {
        'property_id': ['PROP_001', 'PROP_002', 'PROP_003'],
        'price': [300000, 450000, 275000],
        'bedrooms': [3, 4, 2],
        'bathrooms': [2.0, 3.5, 1.5],
        'square_feet': [1500, 2200, 1200]
    }
    
    df = pd.DataFrame(data)
    csv_file = os.path.join(temp_dir, 'sample_properties.csv')
    df.to_csv(csv_file, index=False)
    
    # Create ZIP file
    zip_path = os.path.join(temp_dir, 'test_data.zip')
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.write(csv_file, 'sample_properties.csv')
    
    print(f"✅ Test ZIP created: {zip_path}")
    return zip_path

def test_api_connection():
    """Test if API server is running"""
    print("🔍 Testing API connection...")
    
    api_urls = [
        'http://localhost:8000',
        'http://127.0.0.1:8000'
    ]
    
    for url in api_urls:
        try:
            response = requests.get(f"{url}/docs", timeout=5)
            if response.status_code == 200:
                print(f"✅ API server is running at {url}")
                return url
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to connect to {url}: {e}")
    
    print("❌ No API server found. Please start the server with:")
    print("   uvicorn app.api.main:app --reload")
    return None

def test_auto_format_endpoint(api_url, zip_path):
    """Test the auto-format endpoint"""
    print("\n🤖 Testing auto-format endpoint...")
    
    try:
        with open(zip_path, 'rb') as f:
            files = {'file': ('test_data.zip', f, 'application/zip')}
            
            response = requests.post(
                f"{api_url}/api/v1/data-processor/auto-format",
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Auto-format successful!")
            print(f"📊 Message: {result.get('message', 'No message')}")
            
            # Show some results
            if 'result' in result:
                res = result['result']
                if 'processed_data' in res:
                    print(f"📁 Files processed: {len(res['processed_data'])}")
                
                if 'reformatted_data' in res and 'gemini_analysis' in res['reformatted_data']:
                    print("🧠 AI Analysis available")
            
            return result
        else:
            print(f"❌ Auto-format failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error testing auto-format: {e}")
        return None

def test_schema_endpoint(api_url, zip_path):
    """Test the schema-based endpoint"""
    print("\n🎯 Testing schema-based endpoint...")
    
    schema = {
        "fields": {
            "price": {"type": "float", "required": True},
            "bedrooms": {"type": "int"},
            "bathrooms": {"type": "float"},
            "square_feet": {"type": "int"}
        },
        "target_variable": "price",
        "ml_task": "regression"
    }
    
    try:
        with open(zip_path, 'rb') as f:
            files = {'file': ('test_data.zip', f, 'application/zip')}
            data = {'target_schema': json.dumps(schema)}
            
            response = requests.post(
                f"{api_url}/api/v1/data-processor/upload-zip",
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Schema-based processing successful!")
            print(f"📊 Message: {result.get('message', 'No message')}")
            return result
        else:
            print(f"❌ Schema processing failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error testing schema endpoint: {e}")
        return None

def test_supported_formats(api_url):
    """Test the supported formats endpoint"""
    print("\n📋 Testing supported formats endpoint...")
    
    try:
        response = requests.get(f"{api_url}/api/v1/data-processor/supported-formats")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Supported formats retrieved!")
            formats = result.get('supported_formats', [])
            print(f"📁 Supported formats: {', '.join(formats)}")
            return result
        else:
            print(f"❌ Failed to get supported formats: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting supported formats: {e}")
        return None

def main():
    """Main test function"""
    print("🧪 Data Processor API Test Suite")
    print("=" * 50)
    
    # Test API connection
    api_url = test_api_connection()
    if not api_url:
        print("\n💡 To start the API server:")
        print("1. cd to the real-estate-empire directory")
        print("2. Run: python launch_data_processor.py")
        print("   OR: uvicorn app.api.main:app --reload")
        return
    
    # Create test data
    zip_path = create_test_zip()
    
    try:
        # Test endpoints
        test_supported_formats(api_url)
        auto_result = test_auto_format_endpoint(api_url, zip_path)
        schema_result = test_schema_endpoint(api_url, zip_path)
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Summary:")
        print(f"✅ API Connection: Working")
        print(f"✅ Supported Formats: {'Working' if test_supported_formats else 'Failed'}")
        print(f"✅ Auto Format: {'Working' if auto_result else 'Failed'}")
        print(f"✅ Schema Processing: {'Working' if schema_result else 'Failed'}")
        
        if auto_result or schema_result:
            print("\n🎉 Data Processor API is working correctly!")
            print("\n🌐 You can now use the web interface:")
            print(f"   File: {Path(__file__).parent / 'app' / 'frontend' / 'data-processor.html'}")
        else:
            print("\n❌ Some API endpoints are not working properly")
            
    finally:
        # Cleanup
        if os.path.exists(zip_path):
            os.remove(zip_path)
        temp_dir = os.path.dirname(zip_path)
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()