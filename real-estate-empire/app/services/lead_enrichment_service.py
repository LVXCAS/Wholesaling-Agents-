"""
Lead enrichment service for enhancing lead data with additional information.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import re
import json
from dataclasses import dataclass, asdict
from enum import Enum

from sqlalchemy.orm import Session
from app.models.lead import PropertyLeadDB, PropertyLeadUpdate
from app.integrations.public_records_client import PublicRecordsClient, OwnerInfo
from app.integrations.off_market_finder import MotivationIndicators, MotivationLevel

logger = logging.getLogger(__name__)


class EnrichmentStatus(Enum):
    """Status of enrichment process."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ContactVerificationStatus(Enum):
    """Status of contact verification."""
    VERIFIED = "verified"
    INVALID = "invalid"
    UNVERIFIED = "unverified"
    DO_NOT_CONTACT = "do_not_contact"


@dataclass
class EnrichmentResult:
    """Result of lead enrichment process."""
    lead_id: str
    status: EnrichmentStatus
    owner_info_updated: bool = False
    contact_info_updated: bool = False
    property_info_updated: bool = False
    motivation_factors_updated: bool = False
    confidence_score: float = 0.0
    data_sources: List[str] = None
    errors: List[str] = None
    enriched_fields: Dict[str, Any] = None
    processing_time: float = 0.0
    last_enriched: datetime = None

    def __post_init__(self):
        if self.data_sources is None:
            self.data_sources = []
        if self.errors is None:
            self.errors = []
        if self.enriched_fields is None:
            self.enriched_fields = {}
        if self.last_enriched is None:
            self.last_enriched = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['status'] = data['status'].value
        data['last_enriched'] = data['last_enriched'].isoformat()
        return data


@dataclass
class ContactVerificationResult:
    """Result of contact information verification."""
    phone_verified: bool = False
    email_verified: bool = False
    phone_status: ContactVerificationStatus = ContactVerificationStatus.UNVERIFIED
    email_status: ContactVerificationStatus = ContactVerificationStatus.UNVERIFIED
    verified_phone: Optional[str] = None
    verified_email: Optional[str] = None
    alternative_phones: List[str] = None
    alternative_emails: List[str] = None
    verification_confidence: float = 0.0
    verification_date: datetime = None

    def __post_init__(self):
        if self.alternative_phones is None:
            self.alternative_phones = []
        if self.alternative_emails is None:
            self.alternative_emails = []
        if self.verification_date is None:
            self.verification_date = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['phone_status'] = data['phone_status'].value
        data['email_status'] = data['email_status'].value
        data['verification_date'] = data['verification_date'].isoformat()
        return data


@dataclass
class MotivationFactorAnalysis:
    """Analysis of owner motivation factors."""
    financial_distress_score: float = 0.0
    property_condition_score: float = 0.0
    ownership_duration_score: float = 0.0
    market_conditions_score: float = 0.0
    life_events_score: float = 0.0
    overall_motivation_score: float = 0.0
    motivation_level: MotivationLevel = MotivationLevel.LOW
    key_factors: List[str] = None
    confidence_level: float = 0.0
    analysis_date: datetime = None

    def __post_init__(self):
        if self.key_factors is None:
            self.key_factors = []
        if self.analysis_date is None:
            self.analysis_date = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['motivation_level'] = data['motivation_level'].value
        data['analysis_date'] = data['analysis_date'].isoformat()
        return data


class LeadEnrichmentService:
    """
    Service for enriching lead data with additional information from various sources.
    
    This service enhances lead records by:
    1. Looking up detailed owner information
    2. Verifying and enriching contact information
    3. Adding property details and market data
    4. Analyzing motivation factors
    """

    def __init__(
        self,
        public_records_client: Optional[PublicRecordsClient] = None,
        contact_verification_enabled: bool = True,
        motivation_analysis_enabled: bool = True
    ):
        self.public_records_client = public_records_client
        self.contact_verification_enabled = contact_verification_enabled
        self.motivation_analysis_enabled = motivation_analysis_enabled
        
        # Phone number regex patterns
        self.phone_patterns = [
            r'^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$',
            r'^([0-9]{3})[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$',
            r'^\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$'
        ]
        
        # Email regex pattern
        self.email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    async def enrich_lead(
        self,
        db: Session,
        lead_id: str,
        force_refresh: bool = False
    ) -> EnrichmentResult:
        """
        Enrich a single lead with additional information.
        
        Args:
            db: Database session
            lead_id: Lead ID to enrich
            force_refresh: Force refresh even if recently enriched
            
        Returns:
            EnrichmentResult with details of enrichment process
        """
        start_time = datetime.now()
        
        try:
            # Get lead from database
            lead = db.query(PropertyLeadDB).filter(PropertyLeadDB.id == lead_id).first()
            if not lead:
                return EnrichmentResult(
                    lead_id=lead_id,
                    status=EnrichmentStatus.FAILED,
                    errors=["Lead not found"]
                )
            
            # Check if enrichment is needed
            if not force_refresh and self._is_recently_enriched(lead):
                return EnrichmentResult(
                    lead_id=lead_id,
                    status=EnrichmentStatus.COMPLETED,
                    errors=["Lead recently enriched, use force_refresh=True to override"]
                )
            
            logger.info(f"Starting enrichment for lead {lead_id}")
            
            result = EnrichmentResult(lead_id=lead_id, status=EnrichmentStatus.IN_PROGRESS)
            
            # Perform enrichment tasks in parallel
            tasks = []
            
            # Owner information lookup
            if lead.owner_name or (lead.property and hasattr(lead.property, 'address')):
                tasks.append(self._enrich_owner_information(lead, result))
            
            # Contact information verification
            if self.contact_verification_enabled and (lead.owner_email or lead.owner_phone):
                tasks.append(self._verify_contact_information(lead, result))
            
            # Property information enrichment
            if lead.property:
                tasks.append(self._enrich_property_information(lead, result))
            
            # Motivation factor analysis
            if self.motivation_analysis_enabled:
                tasks.append(self._analyze_motivation_factors(lead, result))
            
            # Execute enrichment tasks
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update lead in database
            update_data = self._prepare_lead_update(result)
            if update_data:
                for field, value in update_data.items():
                    setattr(lead, field, value)
                
                lead.updated_at = datetime.now()
                db.commit()
            
            # Calculate final status and confidence
            result.status = self._determine_final_status(result)
            result.confidence_score = self._calculate_confidence_score(result)
            result.processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Enrichment completed for lead {lead_id} with status {result.status.value}")
            return result
            
        except Exception as e:
            logger.error(f"Error enriching lead {lead_id}: {e}")
            return EnrichmentResult(
                lead_id=lead_id,
                status=EnrichmentStatus.FAILED,
                errors=[str(e)],
                processing_time=(datetime.now() - start_time).total_seconds()
            )

    async def enrich_leads_batch(
        self,
        db: Session,
        lead_ids: List[str],
        max_concurrent: int = 5,
        force_refresh: bool = False
    ) -> List[EnrichmentResult]:
        """
        Enrich multiple leads in batch with concurrency control.
        
        Args:
            db: Database session
            lead_ids: List of lead IDs to enrich
            max_concurrent: Maximum concurrent enrichment tasks
            force_refresh: Force refresh even if recently enriched
            
        Returns:
            List of EnrichmentResult objects
        """
        logger.info(f"Starting batch enrichment for {len(lead_ids)} leads")
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def enrich_with_semaphore(lead_id: str) -> EnrichmentResult:
            async with semaphore:
                return await self.enrich_lead(db, lead_id, force_refresh)
        
        # Execute enrichment tasks with concurrency control
        tasks = [enrich_with_semaphore(lead_id) for lead_id in lead_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        enrichment_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error enriching lead {lead_ids[i]}: {result}")
                enrichment_results.append(EnrichmentResult(
                    lead_id=lead_ids[i],
                    status=EnrichmentStatus.FAILED,
                    errors=[str(result)]
                ))
            else:
                enrichment_results.append(result)
        
        # Log batch results
        successful = sum(1 for r in enrichment_results if r.status == EnrichmentStatus.COMPLETED)
        failed = sum(1 for r in enrichment_results if r.status == EnrichmentStatus.FAILED)
        partial = sum(1 for r in enrichment_results if r.status == EnrichmentStatus.PARTIAL)
        
        logger.info(f"Batch enrichment completed: {successful} successful, {partial} partial, {failed} failed")
        
        return enrichment_results

    async def _enrich_owner_information(
        self,
        lead: PropertyLeadDB,
        result: EnrichmentResult
    ) -> None:
        """Enrich owner information using public records."""
        try:
            if not self.public_records_client:
                result.errors.append("Public records client not available")
                return
            
            # Search by owner name if available
            if lead.owner_name:
                owner_records = await self.public_records_client.search_by_owner(
                    owner_name=lead.owner_name,
                    state=lead.owner_state
                )
                
                if owner_records:
                    # Use the first matching record
                    record = owner_records[0]
                    if record.owner_info:
                        owner_info = record.owner_info
                        
                        # Update lead with enriched owner information
                        enriched_data = {}
                        
                        if not lead.owner_email and owner_info.email:
                            enriched_data['owner_email'] = owner_info.email
                        
                        if not lead.owner_phone and owner_info.phone:
                            enriched_data['owner_phone'] = owner_info.phone
                        
                        if not lead.owner_address and owner_info.mailing_address:
                            enriched_data['owner_address'] = owner_info.mailing_address
                            enriched_data['owner_city'] = owner_info.city
                            enriched_data['owner_state'] = owner_info.state
                            enriched_data['owner_zip'] = owner_info.zip_code
                        
                        if enriched_data:
                            result.enriched_fields.update(enriched_data)
                            result.owner_info_updated = True
                            result.data_sources.append("public_records")
            
            # Search by property address if owner name search didn't yield results
            elif lead.property and hasattr(lead.property, 'address'):
                property_records = await self.public_records_client.search_by_address(
                    address=lead.property.address,
                    city=lead.property.city,
                    state=lead.property.state,
                    zip_code=lead.property.zip_code
                )
                
                if property_records:
                    record = property_records[0]
                    if record.owner_info:
                        owner_info = record.owner_info
                        
                        enriched_data = {}
                        
                        if not lead.owner_name and owner_info.name:
                            enriched_data['owner_name'] = owner_info.name
                        
                        if not lead.owner_email and owner_info.email:
                            enriched_data['owner_email'] = owner_info.email
                        
                        if not lead.owner_phone and owner_info.phone:
                            enriched_data['owner_phone'] = owner_info.phone
                        
                        if not lead.owner_address and owner_info.mailing_address:
                            enriched_data['owner_address'] = owner_info.mailing_address
                            enriched_data['owner_city'] = owner_info.city
                            enriched_data['owner_state'] = owner_info.state
                            enriched_data['owner_zip'] = owner_info.zip_code
                        
                        if enriched_data:
                            result.enriched_fields.update(enriched_data)
                            result.owner_info_updated = True
                            result.data_sources.append("public_records")
            
        except Exception as e:
            logger.error(f"Error enriching owner information: {e}")
            result.errors.append(f"Owner information enrichment failed: {str(e)}")

    async def _verify_contact_information(
        self,
        lead: PropertyLeadDB,
        result: EnrichmentResult
    ) -> None:
        """Verify and enrich contact information."""
        try:
            verification_result = ContactVerificationResult()
            
            # Verify phone number
            if lead.owner_phone:
                phone_verification = await self._verify_phone_number(lead.owner_phone)
                verification_result.phone_verified = phone_verification['is_valid']
                verification_result.phone_status = ContactVerificationStatus(
                    phone_verification.get('status', 'unverified')
                )
                verification_result.verified_phone = phone_verification.get('formatted_number')
                verification_result.alternative_phones = phone_verification.get('alternatives', [])
            
            # Verify email address
            if lead.owner_email:
                email_verification = await self._verify_email_address(lead.owner_email)
                verification_result.email_verified = email_verification['is_valid']
                verification_result.email_status = ContactVerificationStatus(
                    email_verification.get('status', 'unverified')
                )
                verification_result.verified_email = email_verification.get('verified_email')
                verification_result.alternative_emails = email_verification.get('alternatives', [])
            
            # Enrich with additional contact information if available
            if self.public_records_client and lead.owner_name:
                contact_enrichment = await self.public_records_client.enrich_contact_info(
                    owner_name=lead.owner_name,
                    property_address=getattr(lead.property, 'address', '') if lead.property else ''
                )
                
                # Add alternative contact methods
                if contact_enrichment.get('phone_numbers'):
                    verification_result.alternative_phones.extend(
                        contact_enrichment['phone_numbers']
                    )
                
                if contact_enrichment.get('email_addresses'):
                    verification_result.alternative_emails.extend(
                        contact_enrichment['email_addresses']
                    )
            
            # Update lead with verified contact information
            enriched_data = {}
            
            if verification_result.verified_phone and verification_result.verified_phone != lead.owner_phone:
                enriched_data['owner_phone'] = verification_result.verified_phone
            
            if verification_result.verified_email and verification_result.verified_email != lead.owner_email:
                enriched_data['owner_email'] = verification_result.verified_email
            
            # Set do not contact flags based on verification
            if verification_result.phone_status == ContactVerificationStatus.DO_NOT_CONTACT:
                enriched_data['do_not_call'] = True
                enriched_data['do_not_text'] = True
            
            if verification_result.email_status == ContactVerificationStatus.DO_NOT_CONTACT:
                enriched_data['do_not_email'] = True
            
            if enriched_data:
                result.enriched_fields.update(enriched_data)
                result.contact_info_updated = True
                result.data_sources.append("contact_verification")
            
            # Store verification result in lead notes or metadata
            verification_data = verification_result.to_dict()
            result.enriched_fields['contact_verification'] = verification_data
            
        except Exception as e:
            logger.error(f"Error verifying contact information: {e}")
            result.errors.append(f"Contact verification failed: {str(e)}")

    async def _enrich_property_information(
        self,
        lead: PropertyLeadDB,
        result: EnrichmentResult
    ) -> None:
        """Enrich property information from various sources."""
        try:
            if not lead.property:
                return
            
            enriched_data = {}
            
            # Get property records for additional details
            if self.public_records_client:
                property_records = await self.public_records_client.search_by_address(
                    address=lead.property.address,
                    city=lead.property.city,
                    state=lead.property.state,
                    zip_code=lead.property.zip_code
                )
                
                if property_records:
                    record = property_records[0]
                    
                    # Update property tax information
                    if record.tax_record:
                        tax_record = record.tax_record
                        
                        if tax_record.assessed_value and not lead.equity_estimate:
                            # Estimate equity based on assessed value
                            estimated_market_value = tax_record.assessed_value * 1.2
                            estimated_mortgage = estimated_market_value * 0.7
                            estimated_equity = estimated_market_value - estimated_mortgage
                            enriched_data['equity_estimate'] = estimated_equity
                        
                        # Check for tax delinquency
                        if tax_record.payment_status and 'delinquent' in tax_record.payment_status.lower():
                            motivation_factors = lead.motivation_factors or []
                            if 'tax_delinquent' not in motivation_factors:
                                motivation_factors.append('tax_delinquent')
                                enriched_data['motivation_factors'] = motivation_factors
                    
                    # Get deed history for ownership duration
                    deed_history = await self.public_records_client.get_deed_history(
                        property_id=record.record_id,
                        years=10
                    )
                    
                    if deed_history:
                        latest_deed = deed_history[0]
                        if latest_deed.recording_date:
                            ownership_duration = (datetime.now() - latest_deed.recording_date).days
                            
                            # Long ownership might indicate attachment to property
                            if ownership_duration > 3650:  # 10+ years
                                motivation_factors = lead.motivation_factors or []
                                if 'long_term_owner' not in motivation_factors:
                                    motivation_factors.append('long_term_owner')
                                    enriched_data['motivation_factors'] = motivation_factors
            
            if enriched_data:
                result.enriched_fields.update(enriched_data)
                result.property_info_updated = True
                result.data_sources.append("property_records")
            
        except Exception as e:
            logger.error(f"Error enriching property information: {e}")
            result.errors.append(f"Property information enrichment failed: {str(e)}")

    async def _analyze_motivation_factors(
        self,
        lead: PropertyLeadDB,
        result: EnrichmentResult
    ) -> None:
        """Analyze and detect owner motivation factors."""
        try:
            analysis = MotivationFactorAnalysis()
            
            # Analyze financial distress indicators
            financial_indicators = []
            
            if lead.behind_on_payments:
                financial_indicators.append('behind_on_payments')
                analysis.financial_distress_score += 0.3
            
            if lead.motivation_factors:
                if 'tax_delinquent' in lead.motivation_factors:
                    financial_indicators.append('tax_delinquent')
                    analysis.financial_distress_score += 0.4
                
                if 'foreclosure' in lead.motivation_factors:
                    financial_indicators.append('foreclosure')
                    analysis.financial_distress_score += 0.5
            
            # Analyze property condition indicators
            condition_indicators = []
            
            if lead.repair_needed:
                condition_indicators.append('repairs_needed')
                analysis.property_condition_score += 0.2
            
            if lead.estimated_repair_cost and lead.estimated_repair_cost > 10000:
                condition_indicators.append('high_repair_cost')
                analysis.property_condition_score += 0.3
            
            # Analyze ownership duration (if available from property enrichment)
            if 'long_term_owner' in (lead.motivation_factors or []):
                analysis.ownership_duration_score += 0.1  # Lower motivation for long-term owners
            else:
                analysis.ownership_duration_score += 0.2  # Higher motivation for newer owners
            
            # Analyze market conditions (simplified)
            analysis.market_conditions_score = 0.5  # Neutral market conditions
            
            # Analyze life events indicators
            life_event_indicators = []
            
            if lead.motivation_factors:
                life_events = ['divorce', 'death', 'job_loss', 'relocation', 'retirement']
                for event in life_events:
                    if event in lead.motivation_factors:
                        life_event_indicators.append(event)
                        analysis.life_events_score += 0.2
            
            # Calculate overall motivation score
            scores = [
                analysis.financial_distress_score,
                analysis.property_condition_score,
                analysis.ownership_duration_score,
                analysis.market_conditions_score,
                analysis.life_events_score
            ]
            
            analysis.overall_motivation_score = sum(scores) / len(scores)
            
            # Determine motivation level
            if analysis.overall_motivation_score >= 0.7:
                analysis.motivation_level = MotivationLevel.VERY_HIGH
            elif analysis.overall_motivation_score >= 0.5:
                analysis.motivation_level = MotivationLevel.HIGH
            elif analysis.overall_motivation_score >= 0.3:
                analysis.motivation_level = MotivationLevel.MEDIUM
            else:
                analysis.motivation_level = MotivationLevel.LOW
            
            # Compile key factors
            analysis.key_factors = financial_indicators + condition_indicators + life_event_indicators
            
            # Calculate confidence level
            data_points = len([x for x in [
                lead.behind_on_payments,
                lead.repair_needed,
                lead.estimated_repair_cost,
                lead.motivation_factors
            ] if x])
            
            analysis.confidence_level = min(data_points / 4.0, 1.0)
            
            # Update lead with motivation analysis
            enriched_data = {
                'motivation_score': analysis.overall_motivation_score * 100,  # Convert to 0-100 scale
                'urgency_level': analysis.motivation_level.value
            }
            
            # Add new motivation factors if discovered
            current_factors = lead.motivation_factors or []
            new_factors = [f for f in analysis.key_factors if f not in current_factors]
            if new_factors:
                enriched_data['motivation_factors'] = current_factors + new_factors
            
            if enriched_data:
                result.enriched_fields.update(enriched_data)
                result.motivation_factors_updated = True
                result.data_sources.append("motivation_analysis")
            
            # Store detailed analysis
            result.enriched_fields['motivation_analysis'] = analysis.to_dict()
            
        except Exception as e:
            logger.error(f"Error analyzing motivation factors: {e}")
            result.errors.append(f"Motivation analysis failed: {str(e)}")

    async def _verify_phone_number(self, phone: str) -> Dict[str, Any]:
        """Verify phone number format and validity."""
        try:
            # Clean phone number
            cleaned_phone = re.sub(r'\D', '', phone)
            
            # Check format
            is_valid = False
            formatted_number = None
            
            for pattern in self.phone_patterns:
                match = re.match(pattern, phone)
                if match:
                    is_valid = True
                    # Format as (XXX) XXX-XXXX
                    if len(cleaned_phone) == 10:
                        formatted_number = f"({cleaned_phone[:3]}) {cleaned_phone[3:6]}-{cleaned_phone[6:]}"
                    elif len(cleaned_phone) == 11 and cleaned_phone[0] == '1':
                        formatted_number = f"({cleaned_phone[1:4]}) {cleaned_phone[4:7]}-{cleaned_phone[7:]}"
                    break
            
            # In a real implementation, you would also check against:
            # - Do Not Call registry
            # - Phone validation services
            # - Carrier lookup services
            
            return {
                'is_valid': is_valid,
                'formatted_number': formatted_number,
                'status': 'verified' if is_valid else 'invalid',
                'alternatives': []  # Would be populated by phone lookup services
            }
            
        except Exception as e:
            logger.error(f"Error verifying phone number: {e}")
            return {
                'is_valid': False,
                'status': 'unverified',
                'alternatives': []
            }

    async def _verify_email_address(self, email: str) -> Dict[str, Any]:
        """Verify email address format and validity."""
        try:
            # Check format
            is_valid = bool(re.match(self.email_pattern, email))
            
            # In a real implementation, you would also:
            # - Check against email validation services
            # - Verify domain exists
            # - Check for disposable email providers
            # - Check against suppression lists
            
            return {
                'is_valid': is_valid,
                'verified_email': email if is_valid else None,
                'status': 'verified' if is_valid else 'invalid',
                'alternatives': []  # Would be populated by email lookup services
            }
            
        except Exception as e:
            logger.error(f"Error verifying email address: {e}")
            return {
                'is_valid': False,
                'status': 'unverified',
                'alternatives': []
            }

    def _is_recently_enriched(self, lead: PropertyLeadDB, hours: int = 24) -> bool:
        """Check if lead was recently enriched."""
        if not lead.updated_at:
            return False
        
        time_since_update = datetime.now() - lead.updated_at
        return time_since_update < timedelta(hours=hours)

    def _prepare_lead_update(self, result: EnrichmentResult) -> Dict[str, Any]:
        """Prepare lead update data from enrichment result."""
        update_data = {}
        
        # Add enriched fields to update data
        for field, value in result.enriched_fields.items():
            # Skip metadata fields
            if field not in ['contact_verification', 'motivation_analysis']:
                update_data[field] = value
        
        return update_data

    def _determine_final_status(self, result: EnrichmentResult) -> EnrichmentStatus:
        """Determine final enrichment status based on results."""
        if result.errors:
            if any([
                result.owner_info_updated,
                result.contact_info_updated,
                result.property_info_updated,
                result.motivation_factors_updated
            ]):
                return EnrichmentStatus.PARTIAL
            else:
                return EnrichmentStatus.FAILED
        else:
            return EnrichmentStatus.COMPLETED

    def _calculate_confidence_score(self, result: EnrichmentResult) -> float:
        """Calculate overall confidence score for enrichment."""
        scores = []
        
        # Base score on number of successful enrichments
        successful_enrichments = sum([
            result.owner_info_updated,
            result.contact_info_updated,
            result.property_info_updated,
            result.motivation_factors_updated
        ])
        
        base_score = successful_enrichments / 4.0
        
        # Adjust based on data sources
        data_source_bonus = min(len(result.data_sources) * 0.1, 0.3)
        
        # Penalty for errors
        error_penalty = min(len(result.errors) * 0.1, 0.5)
        
        final_score = max(0.0, min(1.0, base_score + data_source_bonus - error_penalty))
        
        return final_score

    async def get_enrichment_status(
        self,
        db: Session,
        lead_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get enrichment status for a lead."""
        try:
            lead = db.query(PropertyLeadDB).filter(PropertyLeadDB.id == lead_id).first()
            if not lead:
                return None
            
            return {
                'lead_id': lead_id,
                'last_updated': lead.updated_at.isoformat() if lead.updated_at else None,
                'has_owner_info': bool(lead.owner_name and lead.owner_email),
                'has_contact_info': bool(lead.owner_phone or lead.owner_email),
                'has_motivation_factors': bool(lead.motivation_factors),
                'motivation_score': lead.motivation_score,
                'lead_score': lead.lead_score
            }
            
        except Exception as e:
            logger.error(f"Error getting enrichment status: {e}")
            return None