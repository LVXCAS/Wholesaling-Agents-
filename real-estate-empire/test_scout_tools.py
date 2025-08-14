#!/usr/bin/env python3
"""
Test script for Scout Agent tools
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

async def test_scout_tools():
    """Test all scout tools individually"""
    
    print("Testing Scout Agent Tools...")
    print("=" * 50)
    
    try:
        # Import tools directly
        from app.agents.scout_tools import (
            MLSIntegrationTool,
            PublicRecordsSearchTool,
            ForeclosureDataTool,
            OffMarketPropertyTool,
            OwnerInformationLookupTool
        )
        
        print("✓ All scout tools imported successfully")
        
        # Test MLS Integration Tool
        print("\n1. Testing MLS Integration Tool...")
        mls_tool = MLSIntegrationTool()
        result = await mls_tool.execute(
            location="Los Angeles, CA",
            criteria={"max_price": 500000},
            max_results=3
        )
        print(f"   - Properties found: {len(result.get('properties', []))}")
        print(f"   - Data source: {result.get('data_source', 'Unknown')}")
        
        # Test Public Records Search Tool
        print("\n2. Testing Public Records Search Tool...")
        records_tool = PublicRecordsSearchTool()
        result = await records_tool.execute(
            property_address="123 Main St, Los Angeles, CA",
            search_type="ownership"
        )
        print(f"   - Search completed: {bool(result.get('results'))}")
        print(f"   - Owner found: {bool(result.get('results', {}).get('ownership'))}")
        
        # Test Foreclosure Data Tool
        print("\n3. Testing Foreclosure Data Tool...")
        foreclosure_tool = ForeclosureDataTool()
        result = await foreclosure_tool.execute(
            location="Los Angeles, CA",
            foreclosure_type="pre_foreclosure",
            max_results=3
        )
        print(f"   - Foreclosure properties found: {len(result.get('properties', []))}")
        
        # Test Off-Market Property Tool
        print("\n4. Testing Off-Market Property Tool...")
        off_market_tool = OffMarketPropertyTool()
        result = await off_market_tool.execute(
            location="Los Angeles, CA",
            strategy="expired_listings",
            max_results=3
        )
        print(f"   - Off-market properties found: {len(result.get('properties', []))}")
        
        # Test Owner Information Lookup Tool
        print("\n5. Testing Owner Information Lookup Tool...")
        owner_tool = OwnerInformationLookupTool()
        result = await owner_tool.execute(
            property_address="123 Main St, Los Angeles, CA",
            lookup_type="basic"
        )
        owner_info = result.get('owner_information', {})
        print(f"   - Owner name: {owner_info.get('owner_name', 'Not found')}")
        print(f"   - Confidence score: {result.get('confidence_score', 0):.2f}")
        
        print("\n" + "=" * 50)
        print("✓ All scout tools tested successfully!")
        
        # Test tool metadata
        print("\nTool Metadata:")
        tools = [mls_tool, records_tool, foreclosure_tool, off_market_tool, owner_tool]
        for tool in tools:
            print(f"   - {tool.metadata.name}: {tool.metadata.description[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing scout tools: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_scout_tools())
    sys.exit(0 if success else 1)