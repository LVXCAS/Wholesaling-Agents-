"""
Integration tests for Public Records client.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp
import json

from app.integrations.public_records_client import (
    PublicRecordsClient,
    PublicRecord,
    OwnerInfo,
    PropertyTaxRecord,
    DeedRecord,
    RecordType,
    PublicRecordsAPIError
)


class TestPublicRecordsClient:
    """Test cases for PublicRecordsClient."""

    @pytest.fixture
    def records_client(self):
        """Create Public Records client for testing."""
        return PublicRecordsClient(
            api_key="test-api-key",
            base_url="https://api.test-records.com/v1",
            max_retries=2,
            retry_delay=0.1,
            rate_limit_per_minute=10
        )

    @pytest.fixture
    def sample_raw_record(self):
        """Sample raw record data from Public Records API."""
        return {
            "record_id": "PR12345",
            "property_address": "123 Main St",
            "county": "Travis",
            "state": "TX",
            "record_type": "property_tax",
            "owner_name": "John Smith",
            "mailing_address": "456 Oak Ave",
            "owner_city": "Austin",
            "owner_state": "TX",
            "owner_zip": "78701",
            "owner_phone": "5551234567",
            "owner_email": "john@email.com",
            "acquisition_date": "2020-05-15",
            "acquisition_price": 350000,
            "tax_year": 2023,
            "assessed_value": 400000,
            "market_value": 450000,
            "tax_amount": 8500,
            "exemptions": ["Homestead"],
            "payment_status": "Paid",
            "due_date": "2023-12-31",
            "last_payment_date": "2023-11-15"
        }

    @pytest.fixture
    def sample_deed_record(self):
        """Sample deed record data."""
        return {
            "record_id": "DR67890",
            "property_address": "789 Pine St",
            "county": "Harris",
            "state": "TX",
            "record_type": "deed",
            "deed_type": "Warranty Deed",
            "grantor": "Jane Doe",
            "grantee": "Bob Johnson",
            "sale_price": 275000,
            "recording_date": "2023-03-20",
            "document_number": "DOC2023-001234",
            "legal_description": "Lot 5, Block 2, Subdivision ABC"
        }

    @pytest.mark.asyncio
    async def test_client_context_manager(self, records_client):
        """Test client as async context manager."""
        async with records_client as client:
            assert client._session is not None
        # Session should be closed after context exit
        assert records_client._session.closed

    @pytest.mark.asyncio
    async def test_rate_limiting(self, records_client):
        """Test rate limiting functionality."""
        # Set very low rate limit for testing
        records_client.rate_limit_per_minute = 2
        
        # Mock time to control rate limiting
        with patch('time.time') as mock_time:
            mock_time.return_value = 1000.0
            
            # First two requests should go through
            await records_client._rate_limit()
            await records_client._rate_limit()
            
            # Third request should trigger rate limiting
            mock_time.return_value = 1030.0  # 30 seconds later
            with patch('asyncio.sleep') as mock_sleep:
                await records_client._rate_limit()
                mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_request_success(self, records_client):
        """Test successful API request."""
        mock_response_data = {"records": [{"record_id": "PR12345"}]}
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_request.return_value.__aenter__.return_value = mock_response
            
            async with records_client:
                result = await records_client._make_request('GET', '/test')
                
            assert result == mock_response_data
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_request_retry_on_server_error(self, records_client):
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
                async with records_client:
                    result = await records_client._make_request('GET', '/test')
                    
            assert result == {"success": True}
            assert mock_request.call_count == 2

    def test_extract_owner_info(self, records_client, sample_raw_record):
        """Test owner information extraction."""
        owner_info = records_client._extract_owner_info(sample_raw_record)
        
        assert owner_info.name == "John Smith"
        assert owner_info.mailing_address == "456 Oak Ave"
        assert owner_info.city == "Austin"
        assert owner_info.state == "TX"
        assert owner_info.zip_code == "78701"
        assert owner_info.phone == "(555) 123-4567"
        assert owner_info.email == "john@email.com"
        assert owner_info.acquisition_price == 350000
        assert owner_info.acquisition_date.year == 2020

    def test_extract_owner_info_minimal(self, records_client):
        """Test owner info extraction with minimal data."""
        minimal_data = {
            "owner_name": "Jane Doe"
        }
        
        owner_info = records_client._extract_owner_info(minimal_data)
        
        assert owner_info.name == "Jane Doe"
        assert owner_info.mailing_address is None
        assert owner_info.phone is None

    def test_extract_tax_record(self, records_client, sample_raw_record):
        """Test tax record extraction."""
        tax_record = records_client._extract_tax_record(sample_raw_record)
        
        assert tax_record is not None
        assert tax_record.tax_year == 2023
        assert tax_record.assessed_value == 400000
        assert tax_record.market_value == 450000
        assert tax_record.tax_amount == 8500
        assert tax_record.exemptions == ["Homestead"]
        assert tax_record.payment_status == "Paid"

    def test_extract_tax_record_missing_data(self, records_client):
        """Test tax record extraction with missing data."""
        minimal_data = {"owner_name": "John Doe"}
        
        tax_record = records_client._extract_tax_record(minimal_data)
        
        assert tax_record is None

    def test_extract_deed_record(self, records_client, sample_deed_record):
        """Test deed record extraction."""
        deed_record = records_client._extract_deed_record(sample_deed_record)
        
        assert deed_record is not None
        assert deed_record.deed_type == "Warranty Deed"
        assert deed_record.grantor == "Jane Doe"
        assert deed_record.grantee == "Bob Johnson"
        assert deed_record.sale_price == 275000
        assert deed_record.document_number == "DOC2023-001234"

    def test_clean_phone_number(self, records_client):
        """Test phone number cleaning and formatting."""
        # Test various phone number formats
        assert records_client._clean_phone_number("5551234567") == "(555) 123-4567"
        assert records_client._clean_phone_number("(555) 123-4567") == "(555) 123-4567"
        assert records_client._clean_phone_number("555-123-4567") == "(555) 123-4567"
        assert records_client._clean_phone_number("1-555-123-4567") == "(555) 123-4567"
        assert records_client._clean_phone_number("15551234567") == "(555) 123-4567"
        assert records_client._clean_phone_number("") is None
        assert records_client._clean_phone_number(None) is None

    def test_normalize_record_data(self, records_client, sample_raw_record):
        """Test record data normalization."""
        normalized = records_client._normalize_record_data(sample_raw_record)
        
        assert normalized.record_id == "PR12345"
        assert normalized.property_address == "123 Main St"
        assert normalized.county == "Travis"
        assert normalized.state == "TX"
        assert normalized.record_type == RecordType.PROPERTY_TAX
        assert normalized.owner_info is not None
        assert normalized.owner_info.name == "John Smith"
        assert normalized.tax_record is not None
        assert normalized.tax_record.assessed_value == 400000

    @pytest.mark.asyncio
    async def test_search_by_address(self, records_client, sample_raw_record):
        """Test searching records by address."""
        mock_response = {
            "records": [sample_raw_record],
            "total_count": 1
        }
        
        with patch.object(records_client, '_make_request', return_value=mock_response):
            async with records_client:
                records = await records_client.search_by_address(
                    address="123 Main St",
                    city="Austin",
                    state="TX",
                    zip_code="78701"
                )
                
        assert len(records) == 1
        assert records[0].record_id == "PR12345"
        assert records[0].property_address == "123 Main St"

    @pytest.mark.asyncio
    async def test_search_by_owner(self, records_client, sample_raw_record):
        """Test searching records by owner name."""
        mock_response = {
            "records": [sample_raw_record],
            "total_count": 1
        }
        
        with patch.object(records_client, '_make_request', return_value=mock_response):
            async with records_client:
                records = await records_client.search_by_owner(
                    owner_name="John Smith",
                    county="Travis",
                    state="TX"
                )
                
        assert len(records) == 1
        assert records[0].owner_info.name == "John Smith"

    @pytest.mark.asyncio
    async def test_get_property_tax_history(self, records_client):
        """Test getting property tax history."""
        mock_tax_records = [
            {
                "property_id": "PROP123",
                "tax_year": 2023,
                "assessed_value": 400000,
                "tax_amount": 8500
            },
            {
                "property_id": "PROP123",
                "tax_year": 2022,
                "assessed_value": 380000,
                "tax_amount": 8100
            }
        ]
        mock_response = {"tax_records": mock_tax_records}
        
        with patch.object(records_client, '_make_request', return_value=mock_response):
            async with records_client:
                tax_records = await records_client.get_property_tax_history("PROP123", years=2)
                
        assert len(tax_records) == 2
        assert tax_records[0].tax_year == 2023
        assert tax_records[0].assessed_value == 400000

    @pytest.mark.asyncio
    async def test_get_deed_history(self, records_client):
        """Test getting deed history."""
        mock_deed_records = [
            {
                "property_id": "PROP123",
                "deed_type": "Warranty Deed",
                "grantor": "Jane Doe",
                "grantee": "John Smith",
                "sale_price": 350000,
                "recording_date": "2020-05-15"
            }
        ]
        mock_response = {"deed_records": mock_deed_records}
        
        with patch.object(records_client, '_make_request', return_value=mock_response):
            async with records_client:
                deed_records = await records_client.get_deed_history("PROP123", years=5)
                
        assert len(deed_records) == 1
        assert deed_records[0].deed_type == "Warranty Deed"
        assert deed_records[0].sale_price == 350000

    @pytest.mark.asyncio
    async def test_validate_owner_info(self, records_client):
        """Test owner information validation."""
        mock_response = {
            "is_valid": True,
            "confidence_score": 0.95,
            "match_details": {"name_match": True, "address_match": True},
            "alternative_names": []
        }
        
        with patch.object(records_client, '_make_request', return_value=mock_response):
            async with records_client:
                validation = await records_client.validate_owner_info(
                    owner_name="John Smith",
                    property_address="123 Main St"
                )
                
        assert validation["is_valid"] is True
        assert validation["confidence_score"] == 0.95
        assert validation["match_details"]["name_match"] is True

    @pytest.mark.asyncio
    async def test_enrich_contact_info(self, records_client):
        """Test contact information enrichment."""
        mock_response = {
            "phone_numbers": ["(555) 123-4567", "(555) 987-6543"],
            "email_addresses": ["john@email.com", "j.smith@company.com"],
            "social_profiles": [{"platform": "LinkedIn", "url": "linkedin.com/in/johnsmith"}],
            "business_info": {"company": "Smith Enterprises"},
            "confidence_scores": {"phone": 0.9, "email": 0.8}
        }
        
        with patch.object(records_client, '_make_request', return_value=mock_response):
            async with records_client:
                enriched = await records_client.enrich_contact_info(
                    owner_name="John Smith",
                    property_address="123 Main St"
                )
                
        assert len(enriched["phone_numbers"]) == 2
        assert len(enriched["email_addresses"]) == 2
        assert enriched["confidence_scores"]["phone"] == 0.9

    def test_owner_info_to_dict(self):
        """Test OwnerInfo to_dict conversion."""
        owner = OwnerInfo(
            name="John Smith",
            mailing_address="456 Oak Ave",
            city="Austin",
            state="TX",
            zip_code="78701",
            phone="(555) 123-4567",
            email="john@email.com",
            acquisition_date=datetime(2020, 5, 15),
            acquisition_price=350000
        )
        
        owner_dict = owner.to_dict()
        
        assert owner_dict["name"] == "John Smith"
        assert owner_dict["acquisition_price"] == 350000
        assert isinstance(owner_dict["acquisition_date"], str)  # Should be ISO string

    def test_tax_record_to_dict(self):
        """Test PropertyTaxRecord to_dict conversion."""
        tax_record = PropertyTaxRecord(
            property_id="PROP123",
            tax_year=2023,
            assessed_value=400000,
            tax_amount=8500,
            due_date=datetime(2023, 12, 31),
            last_payment_date=datetime(2023, 11, 15)
        )
        
        tax_dict = tax_record.to_dict()
        
        assert tax_dict["property_id"] == "PROP123"
        assert tax_dict["tax_year"] == 2023
        assert tax_dict["assessed_value"] == 400000
        assert isinstance(tax_dict["due_date"], str)  # Should be ISO string

    def test_deed_record_to_dict(self):
        """Test DeedRecord to_dict conversion."""
        deed_record = DeedRecord(
            property_id="PROP123",
            deed_type="Warranty Deed",
            grantor="Jane Doe",
            grantee="John Smith",
            sale_price=350000,
            recording_date=datetime(2020, 5, 15)
        )
        
        deed_dict = deed_record.to_dict()
        
        assert deed_dict["property_id"] == "PROP123"
        assert deed_dict["deed_type"] == "Warranty Deed"
        assert deed_dict["sale_price"] == 350000
        assert isinstance(deed_dict["recording_date"], str)  # Should be ISO string

    def test_public_record_to_dict(self):
        """Test PublicRecord to_dict conversion."""
        owner_info = OwnerInfo(name="John Smith")
        tax_record = PropertyTaxRecord(
            property_id="PROP123",
            tax_year=2023,
            assessed_value=400000,
            tax_amount=8500
        )
        
        record = PublicRecord(
            record_id="PR12345",
            property_address="123 Main St",
            record_type=RecordType.PROPERTY_TAX,
            county="Travis",
            state="TX",
            owner_info=owner_info,
            tax_record=tax_record,
            last_updated=datetime.now()
        )
        
        record_dict = record.to_dict()
        
        assert record_dict["record_id"] == "PR12345"
        assert record_dict["record_type"] == "property_tax"
        assert isinstance(record_dict["owner_info"], dict)
        assert isinstance(record_dict["tax_record"], dict)
        assert isinstance(record_dict["last_updated"], str)


class TestRecordType:
    """Test cases for RecordType enum."""

    def test_enum_values(self):
        """Test enum values."""
        assert RecordType.PROPERTY_TAX.value == "property_tax"
        assert RecordType.DEED.value == "deed"
        assert RecordType.MORTGAGE.value == "mortgage"
        assert RecordType.LIEN.value == "lien"
        assert RecordType.PERMIT.value == "permit"
        assert RecordType.ASSESSMENT.value == "assessment"


@pytest.mark.integration
class TestPublicRecordsClientIntegration:
    """Integration tests that require actual Public Records API access."""

    @pytest.mark.skip(reason="Requires real Public Records API credentials")
    @pytest.mark.asyncio
    async def test_real_api_search(self):
        """Test with real Public Records API (requires credentials)."""
        # This test would be enabled when real API credentials are available
        client = PublicRecordsClient(
            api_key="real-api-key",
            base_url="https://real-records-api.com/v1"
        )
        
        async with client:
            records = await client.search_by_address(
                address="123 Main St",
                city="Austin",
                state="TX"
            )
            
        assert len(records) >= 0
        for record in records:
            assert record.record_id
            assert record.property_address
            assert record.county
            assert record.state == "TX"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])