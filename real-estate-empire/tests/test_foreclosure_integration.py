"""
Integration tests for Foreclosure client.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp
import json

from app.integrations.foreclosure_client import (
    ForeclosureClient,
    ForeclosureProperty,
    AuctionInfo,
    ForeclosureStatus,
    AuctionType,
    ForeclosureAPIError
)


class TestForeclosureClient:
    """Test cases for ForeclosureClient."""

    @pytest.fixture
    def foreclosure_client(self):
        """Create Foreclosure client for testing."""
        return ForeclosureClient(
            api_key="test-api-key",
            base_url="https://api.test-foreclosure.com/v1",
            max_retries=2,
            retry_delay=0.1,
            rate_limit_per_minute=10
        )

    @pytest.fixture
    def sample_raw_foreclosure(self):
        """Sample raw foreclosure data from API."""
        return {
            "foreclosure_id": "FC12345",
            "property_address": "123 Main St",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701",
            "status": "pre_foreclosure",
            "auction_type": "trustee_sale",
            "auction_date": "2024-03-15T10:00:00Z",
            "auction_time": "10:00 AM",
            "auction_location": "County Courthouse Steps",
            "opening_bid": 250000,
            "estimated_value": 350000,
            "loan_balance": 280000,
            "bedrooms": 3,
            "bathrooms": 2.5,
            "square_feet": 2000,
            "lot_size": 0.25,
            "year_built": 2010,
            "property_type": "Single Family",
            "default_amount": 15000,
            "filing_date": "2024-01-15T00:00:00Z",
            "trustee_name": "ABC Trustee Services",
            "trustee_phone": "555-123-4567",
            "lender_name": "First National Bank",
            "borrower_name": "John Smith",
            "legal_description": "Lot 5, Block 2, Subdivision ABC",
            "case_number": "FC2024-001234",
            "photos": ["https://photos.foreclosure.com/photo1.jpg"],
            "postponement_count": 1
        }

    @pytest.fixture
    def sample_auction_data(self):
        """Sample auction data."""
        return {
            "auction_id": "AU67890",
            "property_address": "456 Oak Ave",
            "auction_date": "2024-03-20T11:00:00Z",
            "auction_time": "11:00 AM",
            "auction_location": "County Courthouse",
            "auction_type": "sheriff_sale",
            "opening_bid": 180000,
            "estimated_value": 220000,
            "trustee_name": "XYZ Trustee Co",
            "trustee_phone": "555-987-6543",
            "registration_required": True,
            "deposit_required": 5000,
            "terms_of_sale": "Cash only, 10% deposit required",
            "postponement_history": []
        }

    @pytest.mark.asyncio
    async def test_client_context_manager(self, foreclosure_client):
        """Test client as async context manager."""
        async with foreclosure_client as client:
            assert client._session is not None
        # Session should be closed after context exit
        assert foreclosure_client._session.closed

    @pytest.mark.asyncio
    async def test_rate_limiting(self, foreclosure_client):
        """Test rate limiting functionality."""
        # Set very low rate limit for testing
        foreclosure_client.rate_limit_per_minute = 2
        
        # Mock time to control rate limiting
        with patch('time.time') as mock_time:
            mock_time.return_value = 1000.0
            
            # First two requests should go through
            await foreclosure_client._rate_limit()
            await foreclosure_client._rate_limit()
            
            # Third request should trigger rate limiting
            mock_time.return_value = 1030.0  # 30 seconds later
            with patch('asyncio.sleep') as mock_sleep:
                await foreclosure_client._rate_limit()
                mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_request_success(self, foreclosure_client):
        """Test successful API request."""
        mock_response_data = {"results": [{"foreclosure_id": "FC12345"}]}
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_request.return_value.__aenter__.return_value = mock_response
            
            async with foreclosure_client:
                result = await foreclosure_client._make_request('GET', '/test')
                
            assert result == mock_response_data
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_request_retry_on_server_error(self, foreclosure_client):
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
                async with foreclosure_client:
                    result = await foreclosure_client._make_request('GET', '/test')
                    
            assert result == {"success": True}
            assert mock_request.call_count == 2

    def test_normalize_foreclosure_data(self, foreclosure_client, sample_raw_foreclosure):
        """Test foreclosure data normalization."""
        normalized = foreclosure_client._normalize_foreclosure_data(sample_raw_foreclosure)
        
        assert normalized.foreclosure_id == "FC12345"
        assert normalized.property_address == "123 Main St"
        assert normalized.city == "Austin"
        assert normalized.state == "TX"
        assert normalized.zip_code == "78701"
        assert normalized.status == ForeclosureStatus.PRE_FORECLOSURE
        assert normalized.auction_type == AuctionType.TRUSTEE_SALE
        assert normalized.opening_bid == 250000
        assert normalized.estimated_value == 350000
        assert normalized.loan_balance == 280000
        assert normalized.bedrooms == 3
        assert normalized.bathrooms == 2.5
        assert normalized.square_feet == 2000
        assert normalized.trustee_name == "ABC Trustee Services"
        assert normalized.lender_name == "First National Bank"
        assert normalized.postponement_count == 1
        assert len(normalized.photos) == 1

    def test_normalize_foreclosure_data_minimal(self, foreclosure_client):
        """Test normalization with minimal data."""
        minimal_data = {
            "foreclosure_id": "FC67890",
            "property_address": "456 Oak Ave",
            "city": "Dallas",
            "state": "TX",
            "zip_code": "75201",
            "status": "bank_owned"
        }
        
        normalized = foreclosure_client._normalize_foreclosure_data(minimal_data)
        
        assert normalized.foreclosure_id == "FC67890"
        assert normalized.property_address == "456 Oak Ave"
        assert normalized.status == ForeclosureStatus.BANK_OWNED
        assert normalized.opening_bid is None
        assert normalized.bedrooms is None

    def test_normalize_auction_data(self, foreclosure_client, sample_auction_data):
        """Test auction data normalization."""
        normalized = foreclosure_client._normalize_auction_data(sample_auction_data)
        
        assert normalized.auction_id == "AU67890"
        assert normalized.property_address == "456 Oak Ave"
        assert normalized.auction_time == "11:00 AM"
        assert normalized.auction_location == "County Courthouse"
        assert normalized.auction_type == AuctionType.SHERIFF_SALE
        assert normalized.opening_bid == 180000
        assert normalized.estimated_value == 220000
        assert normalized.registration_required is True
        assert normalized.deposit_required == 5000

    @pytest.mark.asyncio
    async def test_search_foreclosures(self, foreclosure_client, sample_raw_foreclosure):
        """Test foreclosure search functionality."""
        mock_response = {
            "results": [sample_raw_foreclosure],
            "total_count": 1
        }
        
        with patch.object(foreclosure_client, '_make_request', return_value=mock_response):
            async with foreclosure_client:
                foreclosures = await foreclosure_client.search_foreclosures(
                    city="Austin",
                    state="TX",
                    status=ForeclosureStatus.PRE_FORECLOSURE,
                    min_value=200000,
                    max_value=400000
                )
                
        assert len(foreclosures) == 1
        assert foreclosures[0].foreclosure_id == "FC12345"
        assert foreclosures[0].city == "Austin"
        assert foreclosures[0].status == ForeclosureStatus.PRE_FORECLOSURE

    @pytest.mark.asyncio
    async def test_get_upcoming_auctions(self, foreclosure_client, sample_auction_data):
        """Test getting upcoming auctions."""
        mock_response = {
            "auctions": [sample_auction_data],
            "total_count": 1
        }
        
        with patch.object(foreclosure_client, '_make_request', return_value=mock_response):
            async with foreclosure_client:
                auctions = await foreclosure_client.get_upcoming_auctions(
                    days_ahead=30,
                    city="Austin",
                    state="TX"
                )
                
        assert len(auctions) == 1
        assert auctions[0].auction_id == "AU67890"
        assert auctions[0].auction_type == AuctionType.SHERIFF_SALE

    @pytest.mark.asyncio
    async def test_get_foreclosure_by_id(self, foreclosure_client, sample_raw_foreclosure):
        """Test getting foreclosure by ID."""
        mock_response = {"foreclosure": sample_raw_foreclosure}
        
        with patch.object(foreclosure_client, '_make_request', return_value=mock_response):
            async with foreclosure_client:
                foreclosure = await foreclosure_client.get_foreclosure_by_id("FC12345")
                
        assert foreclosure is not None
        assert foreclosure.foreclosure_id == "FC12345"

    @pytest.mark.asyncio
    async def test_get_foreclosure_by_id_not_found(self, foreclosure_client):
        """Test getting foreclosure by ID when not found."""
        mock_response = {"foreclosure": None}
        
        with patch.object(foreclosure_client, '_make_request', return_value=mock_response):
            async with foreclosure_client:
                foreclosure = await foreclosure_client.get_foreclosure_by_id("nonexistent")
                
        assert foreclosure is None

    @pytest.mark.asyncio
    async def test_track_foreclosure_status(self, foreclosure_client):
        """Test tracking foreclosure status."""
        mock_response = {
            "current_status": "pre_foreclosure",
            "status_history": [
                {"status": "default", "date": "2024-01-01"},
                {"status": "pre_foreclosure", "date": "2024-01-15"}
            ],
            "next_milestone": "auction_scheduled",
            "estimated_timeline": {"auction_date": "2024-03-15"},
            "risk_factors": ["high_equity", "owner_occupied"]
        }
        
        with patch.object(foreclosure_client, '_make_request', return_value=mock_response):
            async with foreclosure_client:
                status = await foreclosure_client.track_foreclosure_status("FC12345")
                
        assert status["current_status"] == "pre_foreclosure"
        assert len(status["status_history"]) == 2
        assert status["next_milestone"] == "auction_scheduled"

    @pytest.mark.asyncio
    async def test_predict_auction_timeline(self, foreclosure_client):
        """Test auction timeline prediction."""
        mock_response = {
            "predicted_auction_date": "2024-03-15",
            "confidence_score": 0.85,
            "factors_considered": ["filing_date", "state_laws", "court_backlog"],
            "similar_cases": [{"case_id": "FC11111", "timeline": 90}],
            "postponement_probability": 0.25
        }
        
        with patch.object(foreclosure_client, '_make_request', return_value=mock_response):
            async with foreclosure_client:
                timeline = await foreclosure_client.predict_auction_timeline("FC12345")
                
        assert timeline["predicted_auction_date"] == "2024-03-15"
        assert timeline["confidence_score"] == 0.85
        assert timeline["postponement_probability"] == 0.25

    @pytest.mark.asyncio
    async def test_get_pre_foreclosures(self, foreclosure_client, sample_raw_foreclosure):
        """Test getting pre-foreclosure properties."""
        mock_response = {
            "results": [sample_raw_foreclosure],
            "total_count": 1
        }
        
        with patch.object(foreclosure_client, '_make_request', return_value=mock_response):
            async with foreclosure_client:
                pre_foreclosures = await foreclosure_client.get_pre_foreclosures(
                    city="Austin",
                    state="TX",
                    days_in_default=30
                )
                
        assert len(pre_foreclosures) == 1
        assert pre_foreclosures[0].status == ForeclosureStatus.PRE_FORECLOSURE

    @pytest.mark.asyncio
    async def test_get_bank_owned_properties(self, foreclosure_client):
        """Test getting bank-owned properties."""
        bank_owned_data = {
            "foreclosure_id": "FC99999",
            "property_address": "789 Pine St",
            "city": "Houston",
            "state": "TX",
            "zip_code": "77001",
            "status": "bank_owned",
            "estimated_value": 150000
        }
        
        mock_response = {
            "results": [bank_owned_data],
            "total_count": 1
        }
        
        with patch.object(foreclosure_client, '_make_request', return_value=mock_response):
            async with foreclosure_client:
                bank_owned = await foreclosure_client.get_bank_owned_properties(
                    city="Houston",
                    state="TX",
                    min_value=100000,
                    max_value=200000
                )
                
        assert len(bank_owned) == 1
        assert bank_owned[0].status == ForeclosureStatus.BANK_OWNED

    def test_foreclosure_property_to_dict(self, sample_raw_foreclosure, foreclosure_client):
        """Test ForeclosureProperty to_dict conversion."""
        foreclosure = foreclosure_client._normalize_foreclosure_data(sample_raw_foreclosure)
        foreclosure_dict = foreclosure.to_dict()
        
        assert foreclosure_dict["foreclosure_id"] == "FC12345"
        assert foreclosure_dict["status"] == "pre_foreclosure"
        assert foreclosure_dict["auction_type"] == "trustee_sale"
        assert isinstance(foreclosure_dict["auction_date"], str)  # Should be ISO string
        assert isinstance(foreclosure_dict["filing_date"], str)  # Should be ISO string

    def test_auction_info_to_dict(self, sample_auction_data, foreclosure_client):
        """Test AuctionInfo to_dict conversion."""
        auction = foreclosure_client._normalize_auction_data(sample_auction_data)
        auction_dict = auction.to_dict()
        
        assert auction_dict["auction_id"] == "AU67890"
        assert auction_dict["auction_type"] == "sheriff_sale"
        assert auction_dict["opening_bid"] == 180000
        assert isinstance(auction_dict["auction_date"], str)  # Should be ISO string

    def test_days_until_auction_calculation(self, foreclosure_client):
        """Test days until auction calculation."""
        # Create foreclosure with auction date 10 days from now
        future_date = datetime.now() + timedelta(days=10)
        raw_data = {
            "foreclosure_id": "FC12345",
            "property_address": "123 Main St",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701",
            "status": "auction_scheduled",
            "auction_date": future_date.isoformat()
        }
        
        normalized = foreclosure_client._normalize_foreclosure_data(raw_data)
        
        # Should be approximately 10 days (allowing for small time differences)
        assert 9 <= normalized.days_until_auction <= 11


class TestForeclosureStatus:
    """Test cases for ForeclosureStatus enum."""

    def test_enum_values(self):
        """Test enum values."""
        assert ForeclosureStatus.PRE_FORECLOSURE.value == "pre_foreclosure"
        assert ForeclosureStatus.AUCTION_SCHEDULED.value == "auction_scheduled"
        assert ForeclosureStatus.AUCTION_POSTPONED.value == "auction_postponed"
        assert ForeclosureStatus.SOLD_AT_AUCTION.value == "sold_at_auction"
        assert ForeclosureStatus.BANK_OWNED.value == "bank_owned"
        assert ForeclosureStatus.CANCELLED.value == "cancelled"
        assert ForeclosureStatus.REDEEMED.value == "redeemed"


class TestAuctionType:
    """Test cases for AuctionType enum."""

    def test_enum_values(self):
        """Test enum values."""
        assert AuctionType.TRUSTEE_SALE.value == "trustee_sale"
        assert AuctionType.SHERIFF_SALE.value == "sheriff_sale"
        assert AuctionType.JUDICIAL_SALE.value == "judicial_sale"
        assert AuctionType.TAX_SALE.value == "tax_sale"


@pytest.mark.integration
class TestForeclosureClientIntegration:
    """Integration tests that require actual Foreclosure API access."""

    @pytest.mark.skip(reason="Requires real Foreclosure API credentials")
    @pytest.mark.asyncio
    async def test_real_api_search(self):
        """Test with real Foreclosure API (requires credentials)."""
        # This test would be enabled when real API credentials are available
        client = ForeclosureClient(
            api_key="real-api-key",
            base_url="https://real-foreclosure-api.com/v1"
        )
        
        async with client:
            foreclosures = await client.search_foreclosures(
                city="Austin",
                state="TX",
                limit=5
            )
            
        assert len(foreclosures) <= 5
        for foreclosure in foreclosures:
            assert foreclosure.foreclosure_id
            assert foreclosure.property_address
            assert foreclosure.city == "Austin"
            assert foreclosure.state == "TX"
            assert isinstance(foreclosure.status, ForeclosureStatus)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])