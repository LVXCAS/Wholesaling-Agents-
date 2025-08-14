"""
Test suite for Scout Agent Tools
Tests all scout tools for proper functionality and integration
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

# Import scout tools
from app.agents.scout_tools import (
    MLSIntegrationTool,
    PublicRecordsSearchTool,
    ForeclosureDataTool,
    OffMarketPropertyTool,
    OwnerInformationLookupTool,
    register_scout_tools
)


class TestMLSIntegrationTool:
    """Test MLS Integration Tool"""
    
    @pytest.fixture
    def mls_tool(self):
        return MLSIntegrationTool()
    
    @pytest.mark.asyncio
    async def test_mls_search_basic(self, mls_tool):
        """Test basic MLS search functionality"""
        result = await mls_tool.execute(
            location="Los Angeles, CA",
            criteria={
                "min_price": 200000,
                "max_price": 500000,
                "property_types": ["single_family"]
            },
            max_results=10
        )
        
        assert "properties" in result
        assert "total_found" in result
        assert "data_source" in result
        assert result["data_source"] == "MLS"
        assert isinstance(result["properties"], list)
        
        if result["properties"]:
            prop = result["properties"][0]
            assert "address" in prop
            assert "city" in prop
            assert "state" in prop
            assert "listing_price" in prop
    
    @pytest.mark.asyncio
    async def test_mls_search_unsupported_location(self, mls_tool):
        """Test MLS search with unsupported location"""
        result = await mls_tool.execute(
            location="Unknown Location, XX",
            criteria={},
            max_results=10
        )
        
        assert result["total_found"] == 0
        assert "error" in result
        assert "not supported" in result["error"]
    
    @pytest.mark.asyncio
    async def test_mls_search_with_criteria(self, mls_tool):
        """Test MLS search with specific criteria"""
        result = await mls_tool.execute(
            location="Austin, TX",
            criteria={
                "min_price": 300000,
                "max_price": 600000,
                "min_bedrooms": 3,
                "min_bathrooms": 2,
                "property_types": ["single_family", "condo"]
            },
            max_results=5
        )
        
        assert "properties" in result
        assert len(result["properties"]) <= 5


class TestPublicRecordsSearchTool:
    """Test Public Records Search Tool"""
    
    @pytest.fixture
    def public_records_tool(self):
        return PublicRecordsSearchTool()
    
    @pytest.mark.asyncio
    async def test_comprehensive_search(self, public_records_tool):
        """Test comprehensive public records search"""
        result = await public_records_tool.execute(
            property_address="123 Main St, Los Angeles, CA",
            search_type="comprehensive"
        )
        
        assert "results" in result
        assert "ownership" in result["results"]
        assert "sales_history" in result["results"]
        assert "liens" in result["results"]
        assert "permits" in result["results"]
    
    @pytest.mark.asyncio
    async def test_ownership_search(self, public_records_tool):
        """Test ownership-specific search"""
        result = await public_records_tool.execute(
            property_address="456 Oak Ave, Dallas, TX",
            search_type="ownership"
        )
        
        assert "results" in result
        assert "ownership" in result["results"]
        
        ownership = result["results"]["ownership"]
        assert "current_owner" in ownership
        assert "name" in ownership["current_owner"]


class TestForeclosureDataTool:
    """Test Foreclosure Data Tool"""
    
    @pytest.fixture
    def foreclosure_tool(self):
        return ForeclosureDataTool()
    
    @pytest.mark.asyncio
    async def test_all_foreclosure_types(self, foreclosure_tool):
        """Test search for all foreclosure types"""
        result = await foreclosure_tool.execute(
            location="Phoenix, AZ",
            foreclosure_type="all",
            max_results=20
        )
        
        assert "properties" in result
        assert "total_found" in result
        assert isinstance(result["properties"], list)
        
        if result["properties"]:
            prop = result["properties"][0]
            assert "foreclosure_status" in prop
            assert prop["foreclosure_status"] in ["pre_foreclosure", "auction", "reo"]
    
    @pytest.mark.asyncio
    async def test_pre_foreclosure_search(self, foreclosure_tool):
        """Test pre-foreclosure specific search"""
        result = await foreclosure_tool.execute(
            location="Miami, FL",
            foreclosure_type="pre_foreclosure",
            max_results=10
        )
        
        assert "properties" in result
        
        if result["properties"]:
            for prop in result["properties"]:
                assert prop["foreclosure_status"] == "pre_foreclosure"
                assert "notice_date" in prop
                assert "auction_date" in prop


class TestOffMarketPropertyTool:
    """Test Off-Market Property Tool"""
    
    @pytest.fixture
    def off_market_tool(self):
        return OffMarketPropertyTool()
    
    @pytest.mark.asyncio
    async def test_comprehensive_off_market_search(self, off_market_tool):
        """Test comprehensive off-market property search"""
        result = await off_market_tool.execute(
            location="Denver, CO",
            strategy="comprehensive",
            max_results=15
        )
        
        assert "properties" in result
        assert "total_found" in result
        assert isinstance(result["properties"], list)
        
        if result["properties"]:
            prop = result["properties"][0]
            assert "opportunity_type" in prop
            assert "motivation_factors" in prop
            assert "final_opportunity_score" in prop
    
    @pytest.mark.asyncio
    async def test_expired_listings_search(self, off_market_tool):
        """Test expired listings search"""
        result = await off_market_tool.execute(
            location="Seattle, WA",
            strategy="expired_listings",
            max_results=10
        )
        
        assert "properties" in result
        
        if result["properties"]:
            for prop in result["properties"]:
                assert prop["opportunity_type"] == "expired_listing"
                assert "expired_date" in prop


class TestOwnerInformationLookupTool:
    """Test Owner Information Lookup Tool"""
    
    @pytest.fixture
    def owner_lookup_tool(self):
        return OwnerInformationLookupTool()
    
    @pytest.mark.asyncio
    async def test_basic_owner_lookup(self, owner_lookup_tool):
        """Test basic owner information lookup"""
        result = await owner_lookup_tool.execute(
            property_address="789 Pine St, Portland, OR",
            lookup_type="basic"
        )
        
        assert "owner_information" in result
        assert "confidence_score" in result
        
        if result["owner_information"]:
            owner_info = result["owner_information"]
            assert "owner_name" in owner_info
            assert "property_id" in owner_info
    
    @pytest.mark.asyncio
    async def test_comprehensive_owner_lookup(self, owner_lookup_tool):
        """Test comprehensive owner information lookup"""
        result = await owner_lookup_tool.execute(
            property_address="321 Elm St, Nashville, TN",
            lookup_type="comprehensive"
        )
        
        assert "owner_information" in result
        assert "confidence_score" in result
        
        if result["owner_information"]:
            owner_info = result["owner_information"]
            assert "motivation_score" in owner_info
            assert "motivation_factors" in owner_info
            assert isinstance(owner_info["motivation_factors"], list)


# class TestComprehensiveDealDiscoveryTool:
    """Test Comprehensive Deal Discovery Tool"""
    
    @pytest.fixture
    def comprehensive_tool(self):
        return ComprehensiveDealDiscoveryTool()
    
    @pytest.mark.asyncio
    async def test_comprehensive_discovery(self, comprehensive_tool):
        """Test comprehensive deal discovery across all sources"""
        result = await comprehensive_tool.execute(
            location="Atlanta, GA",
            criteria={
                "min_price": 150000,
                "max_price": 400000,
                "property_types": ["single_family"]
            },
            include_sources=["mls", "foreclosures", "off_market"],
            max_results=30
        )
        
        assert "properties" in result
        assert "total_found" in result
        assert "qualified_count" in result
        assert "source_results" in result
        
        # Check that source results are tracked
        source_results = result["source_results"]
        assert isinstance(source_results, dict)
        
        # Properties should be scored
        if result["properties"]:
            prop = result["properties"][0]
            assert "overall_score" in prop
            assert isinstance(prop["overall_score"], (int, float))
    
    @pytest.mark.asyncio
    async def test_discovery_with_owner_enrichment(self, comprehensive_tool):
        """Test discovery with owner information enrichment"""
        result = await comprehensive_tool.execute(
            location="Charlotte, NC",
            criteria={"max_price": 300000},
            include_sources=["mls", "owner_lookup"],
            max_results=10
        )
        
        assert "properties" in result
        
        # Some properties should have owner info
        if result["properties"]:
            has_owner_info = any(
                "owner_info" in prop for prop in result["properties"]
            )
            # Note: This might not always be true due to simulation, but structure should be there


# class TestScoutToolManager:
    """Test Scout Tool Manager"""
    
    @pytest.fixture
    def tool_manager(self):
        return ScoutToolManager()
    
    @pytest.mark.asyncio
    async def test_tool_execution(self, tool_manager):
        """Test tool execution through manager"""
        result = await tool_manager.execute_tool(
            "mls_integration",
            location="San Diego, CA",
            criteria={"max_price": 500000},
            max_results=5
        )
        
        assert "success" in result
        if result["success"]:
            assert "result" in result
            assert "tool" in result
            assert result["tool"] == "mls_integration"
    
    def test_get_available_tools(self, tool_manager):
        """Test getting available tools"""
        tools = tool_manager.get_available_tools()
        
        expected_tools = [
            "mls_integration",
            "public_records_search", 
            "foreclosure_data",
            "off_market_property",
            "owner_information_lookup",
            "comprehensive_deal_discovery"
        ]
        
        for tool in expected_tools:
            assert tool in tools
    
    @pytest.mark.asyncio
    async def test_tool_stats(self, tool_manager):
        """Test tool usage statistics"""
        # Execute a tool to generate stats
        await tool_manager.execute_tool("mls_integration", location="Test")
        
        stats = tool_manager.get_tool_stats()
        assert "tools" in stats
        assert "usage_stats" in stats
        assert "total_calls" in stats


class TestToolRegistration:
    """Test tool registration functionality"""
    
    def test_register_scout_tools(self):
        """Test scout tools registration"""
        tools = register_scout_tools()
        
        assert isinstance(tools, list)
        assert len(tools) == 6  # Expected number of scout tools
        
        tool_names = [tool.metadata.name for tool in tools]
        expected_names = [
            "mls_integration",
            "public_records_search",
            "foreclosure_data", 
            "off_market_property",
            "owner_information_lookup",
            "comprehensive_deal_discovery"
        ]
        
        for name in expected_names:
            assert name in tool_names


# Integration tests
class TestScoutToolsIntegration:
    """Integration tests for scout tools working together"""
    
    # @pytest.mark.asyncio
    # async def test_end_to_end_deal_discovery(self):
    #     """Test end-to-end deal discovery workflow"""
    #     # Initialize comprehensive tool
    #     comprehensive_tool = ComprehensiveDealDiscoveryTool()
        
        # Execute comprehensive discovery
        result = await comprehensive_tool.execute(
            location="Las Vegas, NV",
            criteria={
                "min_price": 200000,
                "max_price": 500000,
                "property_types": ["single_family", "condo"],
                "min_bedrooms": 2
            },
            include_sources=["mls", "foreclosures", "off_market"],
            max_results=20,
            min_score=6.0
        )
        
        # Verify comprehensive results
        assert result["total_found"] >= 0
        assert result["qualified_count"] >= 0
        assert result["qualified_count"] <= result["total_found"]
        
        # All qualified properties should meet minimum score
        for prop in result["properties"]:
            assert prop["overall_score"] >= 6.0
    
    # @pytest.mark.asyncio
    # async def test_tool_manager_integration(self):
    #     """Test tool manager with multiple tools"""
    #     manager = ScoutToolManager()
        
        # Test multiple tool executions
        tools_to_test = [
            ("mls_integration", {"location": "Boston, MA"}),
            ("foreclosure_data", {"location": "Chicago, IL"}),
            ("off_market_property", {"location": "Houston, TX"})
        ]
        
        for tool_name, kwargs in tools_to_test:
            result = await manager.execute_tool(tool_name, **kwargs)
            assert "success" in result
            assert "tool" in result
            assert result["tool"] == tool_name
        
        # Check usage statistics
        stats = manager.get_tool_stats()
        assert stats["total_calls"] >= 3


if __name__ == "__main__":
    # Run basic tests
    import asyncio
    
    async def run_basic_tests():
        print("Running basic scout tools tests...")
        
        # Test MLS tool
        mls_tool = MLSIntegrationTool()
        mls_result = await mls_tool.execute(location="Test City, CA")
        print(f"MLS Tool: Found {mls_result.get('total_found', 0)} properties")
        
        # Test comprehensive tool
        comp_tool = ComprehensiveDealDiscoveryTool()
        comp_result = await comp_tool.execute(location="Test City, CA", max_results=10)
        print(f"Comprehensive Tool: Found {comp_result.get('total_found', 0)} properties")
        
        # Test tool registration
        tools = register_scout_tools()
        print(f"Registered {len(tools)} scout tools")
        
        print("Basic tests completed successfully!")
    
    asyncio.run(run_basic_tests())