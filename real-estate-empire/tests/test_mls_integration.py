"""
Integration tests for MLS client.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp
import json

from app.integrations.mls_client import (
    MLSClient,
    MLSProperty,
    MLSAPIError,
    MLSRateLimitError,
    MLSDataNormalizer,
    MLSPropertyStatus
)


class TestMLSClient:
    """Test cases for MLSClient."""

    @pytest.fixture
    def mls_client(self):
        """Create MLS client for testing."""
        return MLSClient(
            api_key="test-api-key",
            base_url="https://api.test-mls.com/v1",
            max_retries=2,
            retry_delay=0.1,
            rate_limit_per_minute=10
        )

    @pytest.fixture
    def sample_raw_property(self):
        """Sample raw property data from MLS API."""
        return {
            "ListingId": "12345",
            "UnparsedAddress": "123 Main St",
            "City": "Austin",
            "StateOrProvince": "TX",
            "PostalCode": "78701",
            "ListPrice": 450000,
            "BedroomsTotal": 3,
            "BathroomsTotal": 2.5,
            "LivingArea": 2000,
            "LotSizeAcres": 0.25,
            "YearBuilt": 2010,
            "PropertyType": "Single Family",
            "StandardStatus": "Active",
            "DaysOnMarket": 15,
            "ListingContractDate": "2024-01-15T10:00:00Z",
            "PublicRemarks": "Beautiful home in great neighborhood",
            "ListAgentFullName": "John Smith",
            "ListAgentDirectPhone": "555-123-4567",
            "ListAgentEmail": "john@realty.com",
            "Media": [
                {
                    "MediaCategory": "Photo",
                    "MediaURL": "https://photos.mls.com/photo1.jpg"
                },
                {
                    "MediaCategory": "Photo", 
                    "MediaURL": "https://photos.mls.com/photo2.jpg"
                }
            ]
        }

    @pytest.fixture
    def sample_normalized_property(self):
        """Sample normalized property data."""
        return MLSProperty(
            mls_id="12345",
            address="123 Main St",
            city="Austin",
            state="TX",
            zip_code="78701",
            price=450000,
            bedrooms=3,
            bathrooms=2.5,
            square_feet=2000,
            lot_size=0.25,
            year_built=2010,
            property_type="Single Family",
            status="Active",
            days_on_market=15,
            listing_date=datetime(2024, 1, 15, 10, 0, 0),
            photos=["https://photos.mls.com/photo1.jpg", "https://photos.mls.com/photo2.jpg"],
            description="Beautiful home in great neighborhood",
            agent_name="John Smith",
            agent_phone="555-123-4567",
            agent_email="john@realty.com"
        )

    @pytest.mark.asyncio
    async def test_client_context_manager(self, mls_client):
        """Test client as async context manager."""
        async with mls_client as client:
            assert client._session is not None
        # Session should be closed after context exit
        assert mls_client._session.closed

    @pytest.mark.asyncio
    async def test_rate_limiting(self, mls_client):
        """Test rate limiting functionality."""
        # Set very low rate limit for testing
        mls_client.rate_limit_per_minute = 2
        
        # Mock time to control rate limiting
        with patch('time.time') as mock_time:
            mock_time.return_value = 1000.0
            
            # First two requests should go through
            await mls_client._rate_limit()
            await mls_client._rate_limit()
            
            # Third request should trigger rate limiting
            mock_time.return_value = 1030.0  # 30 seconds later
            with patch('asyncio.sleep') as mock_sleep:
                await mls_client._rate_limit()
                mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_request_success(self, mls_client):
        """Test successful API request."""
        mock_response_data = {"results": [{"ListingId": "12345"}]}
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_request.return_value.__aenter__.return_value = mock_response
            
            async with mls_client:
                result = await mls_client._make_request('GET', '/test')
                
            assert result == mock_response_data
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_request_retry_on_server_error(self, mls_client):
        """Test retry logic on server errors."""
        with patch('aiohttp.ClientSession.request') as mock_request:
            # First call returns 500, second call succeeds
            mock_response_error = AsyncMock()
            mock_response_error.status = 500
            mock_response_error.text = AsyncMock(return_value="Server Error")
            
            mock_response_success = AsyncMock()
            mock_response_success.status = 200
            mock_response_success.json = AsyncMock(return_value={"success": True})
            
            mock_request.return_value.__aenter__.side_effect = [
                mock_response_error,
                mock_response_success
            ]
            
            with patch('asyncio.sleep'):  # Speed up test
                async with mls_client:
                    result = await mls_client._make_request('GET', '/test')
                    
            assert result == {"success": True}
            assert mock_request.call_count == 2

    @pytest.mark.asyncio
    async def test_make_request_rate_limit_error(self, mls_client):
        """Test handling of rate limit errors."""
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_response.headers = {'Retry-After': '60'}
            mock_request.return_value.__aenter__.return_value = mock_response
            
            async with mls_client:
                with pytest.raises(MLSRateLimitError):
                    await mls_client._make_request('GET', '/test')

    def test_normalize_property_data(self, mls_client, sample_raw_property):
        """Test property data normalization."""
        normalized = mls_client._normalize_property_data(sample_raw_property)
        
        assert normalized.mls_id == "12345"
        assert normalized.address == "123 Main St"
        assert normalized.city == "Austin"
        assert normalized.state == "TX"
        assert normalized.zip_code == "78701"
        assert normalized.price == 450000
        assert normalized.bedrooms == 3
        assert normalized.bathrooms == 2.5
        assert normalized.square_feet == 2000
        assert normalized.lot_size == 0.25
        assert normalized.year_built == 2010
        assert normalized.property_type == "Single Family"
        assert normalized.status == "Active"
        assert normalized.days_on_market == 15
        assert len(normalized.photos) == 2
        assert normalized.agent_name == "John Smith"

    def test_normalize_property_data_missing_fields(self, mls_client):
        """Test normalization with missing fields."""
        minimal_data = {
            "ListingId": "67890",
            "UnparsedAddress": "456 Oak Ave",
            "City": "Dallas",
            "StateOrProvince": "TX",
            "PostalCode": "75201",
            "ListPrice": 300000
        }
        
        normalized = mls_client._normalize_property_data(minimal_data)
        
        assert normalized.mls_id == "67890"
        assert normalized.address == "456 Oak Ave"
        assert normalized.price == 300000
        assert normalized.bedrooms is None
        assert normalized.bathrooms is None
        assert normalized.square_feet is None

    @pytest.mark.asyncio
    async def test_search_properties(self, mls_client, sample_raw_property):
        """Test property search functionality."""
        mock_response = {
            "results": [sample_raw_property],
            "total_count": 1
        }
        
        with patch.object(mls_client, '_make_request', return_value=mock_response):
            async with mls_client:
                properties = await mls_client.search_properties(
                    city="Austin",
                    state="TX",
                    min_price=400000,
                    max_price=500000
                )
                
        assert len(properties) == 1
        assert properties[0].mls_id == "12345"
        assert properties[0].city == "Austin"

    @pytest.mark.asyncio
    async def test_get_property_by_id(self, mls_client, sample_raw_property):
        """Test getting property by ID."""
        mock_response = {"property": sample_raw_property}
        
        with patch.object(mls_client, '_make_request', return_value=mock_response):
            async with mls_client:
                property_obj = await mls_client.get_property_by_id("12345")
                
        assert property_obj is not None
        assert property_obj.mls_id == "12345"

    @pytest.mark.asyncio
    async def test_get_property_by_id_not_found(self, mls_client):
        """Test getting property by ID when not found."""
        mock_response = {"property": None}
        
        with patch.object(mls_client, '_make_request', return_value=mock_response):
            async with mls_client:
                property_obj = await mls_client.get_property_by_id("nonexistent")
                
        assert property_obj is None

    @pytest.mark.asyncio
    async def test_get_recent_listings(self, mls_client, sample_raw_property):
        """Test getting recent listings."""
        mock_response = {
            "results": [sample_raw_property],
            "total_count": 1
        }
        
        with patch.object(mls_client, '_make_request', return_value=mock_response):
            async with mls_client:
                properties = await mls_client.get_recent_listings(days=7, city="Austin")
                
        assert len(properties) == 1
        assert properties[0].mls_id == "12345"

    @pytest.mark.asyncio
    async def test_get_property_history(self, mls_client):
        """Test getting property history."""
        mock_history = [
            {"date": "2024-01-01", "price": 440000, "status": "Active"},
            {"date": "2024-01-15", "price": 450000, "status": "Active"}
        ]
        mock_response = {"history": mock_history}
        
        with patch.object(mls_client, '_make_request', return_value=mock_response):
            async with mls_client:
                history = await mls_client.get_property_history("12345")
                
        assert len(history) == 2
        assert history[0]["price"] == 440000

    @pytest.mark.asyncio
    async def test_sync_incremental(self, mls_client, sample_raw_property):
        """Test incremental sync functionality."""
        mock_response = {
            "results": [sample_raw_property],
            "total_count": 1
        }
        
        callback_calls = []
        
        async def test_callback(current, total):
            callback_calls.append((current, total))
        
        with patch.object(mls_client, '_make_request', return_value=mock_response):
            async with mls_client:
                last_sync = datetime.now() - timedelta(hours=1)
                properties = await mls_client.sync_incremental(last_sync, test_callback)
                
        assert len(properties) == 1
        assert properties[0].mls_id == "12345"

    def test_property_to_dict(self, sample_normalized_property):
        """Test converting property to dictionary."""
        prop_dict = sample_normalized_property.to_dict()
        
        assert prop_dict["mls_id"] == "12345"
        assert prop_dict["address"] == "123 Main St"
        assert prop_dict["price"] == 450000
        assert isinstance(prop_dict["listing_date"], str)  # Should be ISO string


class TestMLSDataNormalizer:
    """Test cases for MLSDataNormalizer."""

    def test_normalize_property_type(self):
        """Test property type normalization."""
        normalizer = MLSDataNormalizer()
        
        assert normalizer.normalize_property_type("single family") == "Single Family"
        assert normalizer.normalize_property_type("CONDO") == "Condominium"
        assert normalizer.normalize_property_type("townhouse") == "Townhouse"
        assert normalizer.normalize_property_type("multi-family") == "Multi-Family"
        assert normalizer.normalize_property_type("land") == "Land"
        assert normalizer.normalize_property_type("commercial") == "Commercial"
        assert normalizer.normalize_property_type("") == "Unknown"
        assert normalizer.normalize_property_type(None) == "Unknown"

    def test_normalize_status(self):
        """Test status normalization."""
        normalizer = MLSDataNormalizer()
        
        assert normalizer.normalize_status("active") == "Active"
        assert normalizer.normalize_status("PENDING") == "Pending"
        assert normalizer.normalize_status("sold") == "Sold"
        assert normalizer.normalize_status("withdrawn") == "Withdrawn"
        assert normalizer.normalize_status("expired") == "Expired"
        assert normalizer.normalize_status("") == "Unknown"
        assert normalizer.normalize_status(None) == "Unknown"


class TestMLSPropertyStatus:
    """Test cases for MLSPropertyStatus enum."""

    def test_enum_values(self):
        """Test enum values."""
        assert MLSPropertyStatus.ACTIVE.value == "Active"
        assert MLSPropertyStatus.PENDING.value == "Pending"
        assert MLSPropertyStatus.SOLD.value == "Sold"
        assert MLSPropertyStatus.WITHDRAWN.value == "Withdrawn"
        assert MLSPropertyStatus.EXPIRED.value == "Expired"


@pytest.mark.integration
class TestMLSClientIntegration:
    """Integration tests that require actual MLS API access."""

    @pytest.mark.skip(reason="Requires real MLS API credentials")
    @pytest.mark.asyncio
    async def test_real_api_search(self):
        """Test with real MLS API (requires credentials)."""
        # This test would be enabled when real API credentials are available
        client = MLSClient(
            api_key="real-api-key",
            base_url="https://real-mls-api.com/v1"
        )
        
        async with client:
            properties = await client.search_properties(
                city="Austin",
                state="TX",
                limit=5
            )
            
        assert len(properties) <= 5
        for prop in properties:
            assert prop.mls_id
            assert prop.address
            assert prop.city == "Austin"
            assert prop.state == "TX"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])