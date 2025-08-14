"""
Unit tests for lead enrichment service.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.services.lead_enrichment_service import (
    LeadEnrichmentService,
    EnrichmentStatus,
    ContactVerificationStatus,
    EnrichmentResult,
    ContactVerificationResult,
    MotivationFactorAnalysis
)
from app.models.lead import PropertyLeadDB, LeadStatusEnum, LeadSourceEnum
from app.integrations.public_records_client import PublicRecord, OwnerInfo, PropertyTaxRecord
from app.integrations.off_market_finder import MotivationLevel


class TestLeadEnrichmentService:
    """Test cases for LeadEnrichmentService."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_public_records_client(self):
        """Mock public records client."""
        client = Mock()
        client.search_by_owner = AsyncMock()
        client.search_by_address = AsyncMock()
        client.get_deed_history = AsyncMock()
        client.enrich_contact_info = AsyncMock()
        return client

    @pytest.fixture
    def enrichment_service(self, mock_public_records_client):
        """Create enrichment service with mocked dependencies."""
        return LeadEnrichmentService(
            public_records_client=mock_public_records_client,
            contact_verification_enabled=True,
            motivation_analysis_enabled=True
        )

    @pytest.fixture
    def sample_lead(self):
        """Create sample lead for testing."""
        lead = Mock(spec=PropertyLeadDB)
        lead.id = "test-lead-123"
        lead.owner_name = "John Smith"
        lead.owner_email = "john.smith@email.com"
        lead.owner_phone = "(555) 123-4567"
        lead.owner_address = None
        lead.owner_city = None
        lead.owner_state = "TX"
        lead.owner_zip = None
        lead.motivation_factors = ["financial_distress"]
        lead.motivation_score = None
        lead.behind_on_payments = False
        lead.repair_needed = True
        lead.estimated_repair_cost = 15000
        lead.equity_estimate = None
        lead.updated_at = datetime.now() - timedelta(days=2)
        
        # Mock property relationship
        lead.property = Mock()
        lead.property.address = "123 Main St"
        lead.property.city = "Austin"
        lead.property.state = "TX"
        lead.property.zip_code = "78701"
        
        return lead

    @pytest.fixture
    def sample_owner_info(self):
        """Create sample owner info for testing."""
        return OwnerInfo(
            name="John Smith",
            mailing_address="456 Oak Ave",
            city="Dallas",
            state="TX",
            zip_code="75201",
            phone="(555) 987-6543",
            email="j.smith@example.com"
        )

    @pytest.fixture
    def sample_public_record(self, sample_owner_info):
        """Create sample public record for testing."""
        from app.integrations.public_records_client import RecordType
        
        tax_record = PropertyTaxRecord(
            property_id="prop-123",
            tax_year=2023,
            assessed_value=250000,
            tax_amount=5000,
            payment_status="current"
        )
        
        return PublicRecord(
            record_id="record-123",
            property_address="123 Main St",
            record_type=RecordType.PROPERTY_TAX,
            county="Travis",
            state="TX",
            owner_info=sample_owner_info,
            tax_record=tax_record
        )

    @pytest.mark.asyncio
    async def test_enrich_lead_success(
        self,
        enrichment_service,
        mock_db,
        sample_lead,
        sample_public_record
    ):
        """Test successful lead enrichment."""
        # Clear some fields to allow enrichment
        sample_lead.owner_address = None
        sample_lead.equity_estimate = None
        
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = sample_lead
        enrichment_service.public_records_client.search_by_owner.return_value = [sample_public_record]
        enrichment_service.public_records_client.search_by_address.return_value = [sample_public_record]
        enrichment_service.public_records_client.enrich_contact_info.return_value = {
            'phone_numbers': ['(555) 111-2222'],
            'email_addresses': ['john@newdomain.com'],
            'confidence_scores': {'phone': 0.9, 'email': 0.8}
        }
        enrichment_service.public_records_client.get_deed_history.return_value = []
        
        # Execute enrichment
        result = await enrichment_service.enrich_lead(mock_db, "test-lead-123")
        
        # Verify result
        assert result.lead_id == "test-lead-123"
        assert result.status == EnrichmentStatus.COMPLETED
        assert result.owner_info_updated is True
        assert result.motivation_factors_updated is True
        assert result.confidence_score > 0
        assert len(result.errors) == 0
        assert "public_records" in result.data_sources
        
        # Verify database commit was called
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_enrich_lead_not_found(self, enrichment_service, mock_db):
        """Test enrichment when lead is not found."""
        # Setup mock to return None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute enrichment
        result = await enrichment_service.enrich_lead(mock_db, "nonexistent-lead")
        
        # Verify result
        assert result.lead_id == "nonexistent-lead"
        assert result.status == EnrichmentStatus.FAILED
        assert "Lead not found" in result.errors

    @pytest.mark.asyncio
    async def test_enrich_lead_recently_enriched(
        self,
        enrichment_service,
        mock_db,
        sample_lead
    ):
        """Test enrichment skipped for recently enriched lead."""
        # Set recent update time
        sample_lead.updated_at = datetime.now() - timedelta(hours=1)
        mock_db.query.return_value.filter.return_value.first.return_value = sample_lead
        
        # Execute enrichment without force refresh
        result = await enrichment_service.enrich_lead(mock_db, "test-lead-123", force_refresh=False)
        
        # Verify result
        assert result.status == EnrichmentStatus.COMPLETED
        assert "recently enriched" in result.errors[0]

    @pytest.mark.asyncio
    async def test_enrich_owner_information(
        self,
        enrichment_service,
        sample_lead,
        sample_public_record
    ):
        """Test owner information enrichment."""
        result = EnrichmentResult(lead_id="test-lead-123", status=EnrichmentStatus.IN_PROGRESS)
        
        # Clear existing owner info to test enrichment
        sample_lead.owner_phone = None
        sample_lead.owner_address = None
        
        # Setup mock
        enrichment_service.public_records_client.search_by_owner.return_value = [sample_public_record]
        
        # Execute enrichment
        await enrichment_service._enrich_owner_information(sample_lead, result)
        
        # Verify result
        assert result.owner_info_updated is True
        assert "public_records" in result.data_sources
        assert "owner_phone" in result.enriched_fields
        assert result.enriched_fields["owner_phone"] == "(555) 987-6543"

    @pytest.mark.asyncio
    async def test_verify_contact_information(self, enrichment_service, sample_lead):
        """Test contact information verification."""
        result = EnrichmentResult(lead_id="test-lead-123", status=EnrichmentStatus.IN_PROGRESS)
        
        # Setup mock for contact enrichment
        enrichment_service.public_records_client.enrich_contact_info.return_value = {
            'phone_numbers': ['(555) 111-2222'],
            'email_addresses': ['john@newdomain.com'],
            'confidence_scores': {'phone': 0.9, 'email': 0.8}
        }
        
        # Execute verification
        await enrichment_service._verify_contact_information(sample_lead, result)
        
        # Verify result - contact verification always adds metadata even if no updates
        assert "contact_verification" in result.enriched_fields
        # The contact_info_updated flag is only set if actual contact data changes

    @pytest.mark.asyncio
    async def test_analyze_motivation_factors(self, enrichment_service, sample_lead):
        """Test motivation factor analysis."""
        result = EnrichmentResult(lead_id="test-lead-123", status=EnrichmentStatus.IN_PROGRESS)
        
        # Set up lead with various motivation indicators
        sample_lead.behind_on_payments = True
        sample_lead.repair_needed = True
        sample_lead.estimated_repair_cost = 25000
        sample_lead.motivation_factors = ["financial_distress", "tax_delinquent"]
        
        # Execute analysis
        await enrichment_service._analyze_motivation_factors(sample_lead, result)
        
        # Verify result
        assert result.motivation_factors_updated is True
        assert "motivation_analysis" in result.data_sources
        assert "motivation_score" in result.enriched_fields
        assert "urgency_level" in result.enriched_fields
        assert result.enriched_fields["motivation_score"] > 0

    @pytest.mark.asyncio
    async def test_enrich_leads_batch(
        self,
        enrichment_service,
        mock_db,
        sample_lead,
        sample_public_record
    ):
        """Test batch lead enrichment."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = sample_lead
        enrichment_service.public_records_client.search_by_owner.return_value = [sample_public_record]
        enrichment_service.public_records_client.enrich_contact_info.return_value = {}
        enrichment_service.public_records_client.get_deed_history.return_value = []
        
        lead_ids = ["lead-1", "lead-2", "lead-3"]
        
        # Execute batch enrichment
        results = await enrichment_service.enrich_leads_batch(
            mock_db,
            lead_ids,
            max_concurrent=2
        )
        
        # Verify results
        assert len(results) == 3
        for result in results:
            assert result.status in [EnrichmentStatus.COMPLETED, EnrichmentStatus.PARTIAL]

    def test_verify_phone_number_valid(self, enrichment_service):
        """Test phone number verification with valid number."""
        phone = "(555) 123-4567"
        
        # Execute verification (this is a sync method)
        result = asyncio.run(enrichment_service._verify_phone_number(phone))
        
        # Verify result
        assert result['is_valid'] is True
        assert result['status'] == 'verified'
        assert result['formatted_number'] == "(555) 123-4567"

    def test_verify_phone_number_invalid(self, enrichment_service):
        """Test phone number verification with invalid number."""
        phone = "invalid-phone"
        
        # Execute verification
        result = asyncio.run(enrichment_service._verify_phone_number(phone))
        
        # Verify result
        assert result['is_valid'] is False
        assert result['status'] == 'invalid'

    def test_verify_email_address_valid(self, enrichment_service):
        """Test email address verification with valid email."""
        email = "test@example.com"
        
        # Execute verification
        result = asyncio.run(enrichment_service._verify_email_address(email))
        
        # Verify result
        assert result['is_valid'] is True
        assert result['status'] == 'verified'
        assert result['verified_email'] == email

    def test_verify_email_address_invalid(self, enrichment_service):
        """Test email address verification with invalid email."""
        email = "invalid-email"
        
        # Execute verification
        result = asyncio.run(enrichment_service._verify_email_address(email))
        
        # Verify result
        assert result['is_valid'] is False
        assert result['status'] == 'invalid'

    def test_is_recently_enriched(self, enrichment_service, sample_lead):
        """Test recent enrichment check."""
        # Test recently updated lead
        sample_lead.updated_at = datetime.now() - timedelta(hours=1)
        assert enrichment_service._is_recently_enriched(sample_lead) is True
        
        # Test old lead
        sample_lead.updated_at = datetime.now() - timedelta(days=2)
        assert enrichment_service._is_recently_enriched(sample_lead) is False
        
        # Test lead with no update time
        sample_lead.updated_at = None
        assert enrichment_service._is_recently_enriched(sample_lead) is False

    def test_determine_final_status(self, enrichment_service):
        """Test final status determination."""
        # Test successful enrichment
        result = EnrichmentResult(
            lead_id="test",
            status=EnrichmentStatus.IN_PROGRESS,
            owner_info_updated=True,
            contact_info_updated=True
        )
        status = enrichment_service._determine_final_status(result)
        assert status == EnrichmentStatus.COMPLETED
        
        # Test partial enrichment with errors
        result.errors = ["Some error"]
        status = enrichment_service._determine_final_status(result)
        assert status == EnrichmentStatus.PARTIAL
        
        # Test failed enrichment
        result.owner_info_updated = False
        result.contact_info_updated = False
        status = enrichment_service._determine_final_status(result)
        assert status == EnrichmentStatus.FAILED

    def test_calculate_confidence_score(self, enrichment_service):
        """Test confidence score calculation."""
        # Test high confidence
        result = EnrichmentResult(
            lead_id="test",
            status=EnrichmentStatus.COMPLETED,
            owner_info_updated=True,
            contact_info_updated=True,
            property_info_updated=True,
            motivation_factors_updated=True,
            data_sources=["public_records", "contact_verification"]
        )
        score = enrichment_service._calculate_confidence_score(result)
        assert score > 0.8
        
        # Test low confidence with errors
        result.errors = ["Error 1", "Error 2"]
        result.owner_info_updated = False
        result.contact_info_updated = False
        score = enrichment_service._calculate_confidence_score(result)
        assert score < 0.5

    @pytest.mark.asyncio
    async def test_get_enrichment_status(self, enrichment_service, mock_db, sample_lead):
        """Test getting enrichment status."""
        # Setup mock
        mock_db.query.return_value.filter.return_value.first.return_value = sample_lead
        sample_lead.motivation_score = 75.0
        sample_lead.lead_score = 85.0
        
        # Execute
        status = await enrichment_service.get_enrichment_status(mock_db, "test-lead-123")
        
        # Verify result
        assert status is not None
        assert status['lead_id'] == "test-lead-123"
        assert status['has_owner_info'] is True
        assert status['has_contact_info'] is True
        assert status['motivation_score'] == 75.0
        assert status['lead_score'] == 85.0

    @pytest.mark.asyncio
    async def test_get_enrichment_status_not_found(self, enrichment_service, mock_db):
        """Test getting enrichment status for non-existent lead."""
        # Setup mock to return None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        status = await enrichment_service.get_enrichment_status(mock_db, "nonexistent")
        
        # Verify result
        assert status is None

    @pytest.mark.asyncio
    async def test_enrichment_with_exception(
        self,
        enrichment_service,
        mock_db,
        sample_lead
    ):
        """Test enrichment handling exceptions gracefully."""
        # Setup mock to raise exception
        mock_db.query.return_value.filter.return_value.first.return_value = sample_lead
        enrichment_service.public_records_client.search_by_owner.side_effect = Exception("API Error")
        enrichment_service.public_records_client.search_by_address.side_effect = Exception("API Error")
        
        # Execute enrichment
        result = await enrichment_service.enrich_lead(mock_db, "test-lead-123")
        
        # Verify result handles exception - may be PARTIAL if some enrichment succeeds
        assert result.status in [EnrichmentStatus.FAILED, EnrichmentStatus.PARTIAL]
        assert "API Error" in str(result.errors)

    def test_enrichment_result_serialization(self):
        """Test EnrichmentResult serialization."""
        result = EnrichmentResult(
            lead_id="test-123",
            status=EnrichmentStatus.COMPLETED,
            owner_info_updated=True,
            confidence_score=0.85,
            data_sources=["public_records"],
            errors=[]
        )
        
        # Test serialization
        data = result.to_dict()
        
        # Verify serialized data
        assert data['lead_id'] == "test-123"
        assert data['status'] == "completed"
        assert data['owner_info_updated'] is True
        assert data['confidence_score'] == 0.85
        assert isinstance(data['last_enriched'], str)

    def test_contact_verification_result_serialization(self):
        """Test ContactVerificationResult serialization."""
        result = ContactVerificationResult(
            phone_verified=True,
            email_verified=False,
            phone_status=ContactVerificationStatus.VERIFIED,
            email_status=ContactVerificationStatus.INVALID,
            verified_phone="(555) 123-4567",
            alternative_phones=["(555) 987-6543"]
        )
        
        # Test serialization
        data = result.to_dict()
        
        # Verify serialized data
        assert data['phone_verified'] is True
        assert data['email_verified'] is False
        assert data['phone_status'] == "verified"
        assert data['email_status'] == "invalid"
        assert data['verified_phone'] == "(555) 123-4567"

    def test_motivation_factor_analysis_serialization(self):
        """Test MotivationFactorAnalysis serialization."""
        analysis = MotivationFactorAnalysis(
            financial_distress_score=0.8,
            overall_motivation_score=0.7,
            motivation_level=MotivationLevel.HIGH,
            key_factors=["financial_distress", "repairs_needed"],
            confidence_level=0.9
        )
        
        # Test serialization
        data = analysis.to_dict()
        
        # Verify serialized data
        assert data['financial_distress_score'] == 0.8
        assert data['overall_motivation_score'] == 0.7
        assert data['motivation_level'] == "high"
        assert data['key_factors'] == ["financial_distress", "repairs_needed"]
        assert data['confidence_level'] == 0.9


class TestEnrichmentServiceIntegration:
    """Integration tests for enrichment service."""

    @pytest.fixture
    def mock_db_integration(self):
        """Mock database session for integration tests."""
        return Mock(spec=Session)

    @pytest.fixture
    def sample_lead_integration(self):
        """Create sample lead for integration testing."""
        lead = Mock(spec=PropertyLeadDB)
        lead.id = "test-lead-123"
        lead.owner_name = "John Smith"
        lead.owner_email = "john.smith@email.com"
        lead.owner_phone = "(555) 123-4567"
        lead.owner_address = None
        lead.owner_city = None
        lead.owner_state = "TX"
        lead.owner_zip = None
        lead.motivation_factors = ["financial_distress"]
        lead.motivation_score = None
        lead.behind_on_payments = False
        lead.repair_needed = True
        lead.estimated_repair_cost = 15000
        lead.equity_estimate = None
        lead.updated_at = datetime.now() - timedelta(days=2)
        
        # Mock property relationship
        lead.property = Mock()
        lead.property.address = "123 Main St"
        lead.property.city = "Austin"
        lead.property.state = "TX"
        lead.property.zip_code = "78701"
        
        return lead

    @pytest.fixture
    def enrichment_service_no_clients(self):
        """Create enrichment service without external clients."""
        return LeadEnrichmentService(
            public_records_client=None,
            contact_verification_enabled=False,
            motivation_analysis_enabled=True
        )

    @pytest.mark.asyncio
    async def test_enrichment_without_public_records_client(
        self,
        enrichment_service_no_clients,
        mock_db_integration,
        sample_lead_integration
    ):
        """Test enrichment when public records client is not available."""
        # Setup mock
        mock_db_integration.query.return_value.filter.return_value.first.return_value = sample_lead_integration
        
        # Execute enrichment
        result = await enrichment_service_no_clients.enrich_lead(mock_db_integration, "test-lead-123")
        
        # Verify result
        assert result.status in [EnrichmentStatus.COMPLETED, EnrichmentStatus.PARTIAL]
        assert result.owner_info_updated is False  # No public records client
        assert result.motivation_factors_updated is True  # Still works without external data

    @pytest.mark.asyncio
    async def test_enrichment_with_disabled_features(
        self,
        mock_db_integration,
        sample_lead_integration
    ):
        """Test enrichment with disabled features."""
        service = LeadEnrichmentService(
            public_records_client=None,
            contact_verification_enabled=False,
            motivation_analysis_enabled=False
        )
        
        # Setup mock
        mock_db_integration.query.return_value.filter.return_value.first.return_value = sample_lead_integration
        
        # Execute enrichment
        result = await service.enrich_lead(mock_db_integration, "test-lead-123")
        
        # Verify result - with all features disabled, enrichment may fail or complete with no updates
        assert result.status in [EnrichmentStatus.COMPLETED, EnrichmentStatus.FAILED]
        assert result.owner_info_updated is False
        assert result.contact_info_updated is False
        assert result.motivation_factors_updated is False


if __name__ == "__main__":
    pytest.main([__file__])