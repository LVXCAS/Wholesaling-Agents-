"""
Off-market property finder for identifying investment opportunities.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
import json
from dataclasses import dataclass, asdict
from enum import Enum
import re
import statistics
from collections import defaultdict

logger = logging.getLogger(__name__)


class MotivationLevel(Enum):
    """Property owner motivation level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class PropertyCondition(Enum):
    """Estimated property condition."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    DISTRESSED = "distressed"


class OpportunityType(Enum):
    """Type of off-market opportunity."""
    DISTRESSED_OWNER = "distressed_owner"
    HIGH_EQUITY = "high_equity"
    ABSENTEE_OWNER = "absentee_owner"
    ESTATE_SALE = "estate_sale"
    DIVORCE = "divorce"
    FINANCIAL_DISTRESS = "financial_distress"
    TIRED_LANDLORD = "tired_landlord"
    VACANT_PROPERTY = "vacant_property"
    TAX_DELINQUENT = "tax_delinquent"
    CODE_VIOLATIONS = "code_violations"


@dataclass
class OwnerResearch:
    """Owner research and contact information."""
    name: str
    mailing_address: Optional[str] = None
    phone_numbers: Optional[List[str]] = None
    email_addresses: Optional[List[str]] = None
    social_profiles: Optional[List[Dict[str, str]]] = None
    business_affiliations: Optional[List[str]] = None
    property_count: Optional[int] = None
    is_absentee_owner: bool = False
    estimated_net_worth: Optional[str] = None
    contact_confidence: float = 0.0
    last_updated: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        if data.get('last_updated'):
            data['last_updated'] = data['last_updated'].isoformat()
        return data


@dataclass
class MotivationIndicators:
    """Indicators of owner motivation to sell."""
    financial_distress: bool = False
    tax_delinquency: bool = False
    code_violations: bool = False
    vacant_property: bool = False
    estate_situation: bool = False
    divorce_proceedings: bool = False
    job_relocation: bool = False
    multiple_properties: bool = False
    recent_life_events: Optional[List[str]] = None
    motivation_score: float = 0.0
    confidence_level: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class PropertyConditionEstimate:
    """Estimated property condition based on available data."""
    overall_condition: PropertyCondition
    condition_score: float  # 0-100
    repair_estimate: Optional[float] = None
    condition_indicators: Optional[List[str]] = None
    data_sources: Optional[List[str]] = None
    confidence_level: float = 0.0
    last_assessed: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['overall_condition'] = data['overall_condition'].value
        if data.get('last_assessed'):
            data['last_assessed'] = data['last_assessed'].isoformat()
        return data


@dataclass
class OffMarketOpportunity:
    """Off-market property opportunity."""
    opportunity_id: str
    property_address: str
    city: str
    state: str
    zip_code: str
    opportunity_types: List[OpportunityType]
    estimated_value: Optional[float] = None
    estimated_equity: Optional[float] = None
    owner_research: Optional[OwnerResearch] = None
    motivation_indicators: Optional[MotivationIndicators] = None
    condition_estimate: Optional[PropertyConditionEstimate] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    property_type: Optional[str] = None
    last_sale_date: Optional[datetime] = None
    last_sale_price: Optional[float] = None
    tax_assessed_value: Optional[float] = None
    days_on_market_history: Optional[List[int]] = None
    listing_history: Optional[List[Dict[str, Any]]] = None
    neighborhood_data: Optional[Dict[str, Any]] = None
    opportunity_score: float = 0.0
    confidence_score: float = 0.0
    discovered_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert enum values to strings
        data['opportunity_types'] = [ot.value for ot in data['opportunity_types']]
        # Convert datetime objects to ISO strings
        for date_field in ['last_sale_date', 'discovered_date', 'last_updated']:
            if data.get(date_field):
                data[date_field] = data[date_field].isoformat()
        # Convert nested objects
        if data.get('owner_research'):
            data['owner_research'] = self.owner_research.to_dict()
        if data.get('motivation_indicators'):
            data['motivation_indicators'] = self.motivation_indicators.to_dict()
        if data.get('condition_estimate'):
            data['condition_estimate'] = self.condition_estimate.to_dict()
        return data


class OffMarketPropertyFinder:
    """
    Off-market property finder that identifies investment opportunities
    by analyzing various data sources and owner motivation indicators.
    """

    def __init__(
        self,
        mls_client=None,
        public_records_client=None,
        foreclosure_client=None
    ):
        self.mls_client = mls_client
        self.public_records_client = public_records_client
        self.foreclosure_client = foreclosure_client
        
        # Scoring weights for different opportunity types
        self.opportunity_weights = {
            OpportunityType.DISTRESSED_OWNER: 0.9,
            OpportunityType.HIGH_EQUITY: 0.8,
            OpportunityType.ABSENTEE_OWNER: 0.7,
            OpportunityType.ESTATE_SALE: 0.85,
            OpportunityType.DIVORCE: 0.8,
            OpportunityType.FINANCIAL_DISTRESS: 0.9,
            OpportunityType.TIRED_LANDLORD: 0.75,
            OpportunityType.VACANT_PROPERTY: 0.8,
            OpportunityType.TAX_DELINQUENT: 0.85,
            OpportunityType.CODE_VIOLATIONS: 0.7
        }

    async def find_opportunities(
        self,
        city: str,
        state: str,
        zip_codes: Optional[List[str]] = None,
        min_equity: Optional[float] = None,
        max_price: Optional[float] = None,
        opportunity_types: Optional[List[OpportunityType]] = None,
        limit: int = 100
    ) -> List[OffMarketOpportunity]:
        """
        Find off-market opportunities based on criteria.
        
        Args:
            city: Target city
            state: Target state
            zip_codes: Specific ZIP codes to search
            min_equity: Minimum estimated equity
            max_price: Maximum estimated property value
            opportunity_types: Specific opportunity types to focus on
            limit: Maximum number of results
            
        Returns:
            List of off-market opportunities
        """
        logger.info(f"Searching for off-market opportunities in {city}, {state}")
        
        opportunities = []
        
        # Search different data sources in parallel
        tasks = []
        
        # Search for high-equity properties
        if not opportunity_types or OpportunityType.HIGH_EQUITY in opportunity_types:
            tasks.append(self._find_high_equity_properties(city, state, zip_codes, min_equity))
        
        # Search for absentee owners
        if not opportunity_types or OpportunityType.ABSENTEE_OWNER in opportunity_types:
            tasks.append(self._find_absentee_owners(city, state, zip_codes))
        
        # Search for tax delinquent properties
        if not opportunity_types or OpportunityType.TAX_DELINQUENT in opportunity_types:
            tasks.append(self._find_tax_delinquent_properties(city, state, zip_codes))
        
        # Search for vacant properties
        if not opportunity_types or OpportunityType.VACANT_PROPERTY in opportunity_types:
            tasks.append(self._find_vacant_properties(city, state, zip_codes))
        
        # Search for distressed properties
        if not opportunity_types or OpportunityType.DISTRESSED_OWNER in opportunity_types:
            tasks.append(self._find_distressed_properties(city, state, zip_codes))
        
        # Execute searches in parallel
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error in opportunity search: {result}")
                    continue
                if isinstance(result, list):
                    opportunities.extend(result)
        
        # Remove duplicates and score opportunities
        unique_opportunities = self._deduplicate_opportunities(opportunities)
        scored_opportunities = await self._score_opportunities(unique_opportunities)
        
        # Filter by criteria
        filtered_opportunities = self._filter_opportunities(
            scored_opportunities,
            min_equity=min_equity,
            max_price=max_price
        )
        
        # Sort by opportunity score and limit results
        filtered_opportunities.sort(key=lambda x: x.opportunity_score, reverse=True)
        
        logger.info(f"Found {len(filtered_opportunities)} off-market opportunities")
        return filtered_opportunities[:limit]

    async def _find_high_equity_properties(
        self,
        city: str,
        state: str,
        zip_codes: Optional[List[str]] = None
    ) -> List[OffMarketOpportunity]:
        """Find properties with high equity potential."""
        opportunities = []
        
        try:
            if not self.public_records_client:
                logger.warning("Public records client not available for high equity search")
                return opportunities
            
            # Search for properties with low assessed values relative to market
            search_params = {
                'city': city,
                'state': state
            }
            
            if zip_codes:
                for zip_code in zip_codes:
                    search_params['zip_code'] = zip_code
                    records = await self.public_records_client.search_by_address(
                        address="",  # Search all addresses in area
                        **search_params
                    )
                    
                    for record in records:
                        if record.tax_record and record.tax_record.assessed_value:
                            # Estimate market value vs assessed value
                            opportunity = await self._analyze_equity_opportunity(record)
                            if opportunity:
                                opportunities.append(opportunity)
            
        except Exception as e:
            logger.error(f"Error finding high equity properties: {e}")
        
        return opportunities

    async def _find_absentee_owners(
        self,
        city: str,
        state: str,
        zip_codes: Optional[List[str]] = None
    ) -> List[OffMarketOpportunity]:
        """Find properties owned by absentee owners."""
        opportunities = []
        
        try:
            if not self.public_records_client:
                logger.warning("Public records client not available for absentee owner search")
                return opportunities
            
            # Search for properties where owner mailing address differs from property address
            search_params = {
                'city': city,
                'state': state
            }
            
            if zip_codes:
                for zip_code in zip_codes:
                    search_params['zip_code'] = zip_code
                    records = await self.public_records_client.search_by_address(
                        address="",
                        **search_params
                    )
                    
                    for record in records:
                        if self._is_absentee_owner(record):
                            opportunity = await self._create_absentee_opportunity(record)
                            if opportunity:
                                opportunities.append(opportunity)
            
        except Exception as e:
            logger.error(f"Error finding absentee owners: {e}")
        
        return opportunities

    async def _find_tax_delinquent_properties(
        self,
        city: str,
        state: str,
        zip_codes: Optional[List[str]] = None
    ) -> List[OffMarketOpportunity]:
        """Find properties with tax delinquencies."""
        opportunities = []
        
        try:
            if not self.public_records_client:
                logger.warning("Public records client not available for tax delinquent search")
                return opportunities
            
            # Search for properties with unpaid taxes
            search_params = {
                'city': city,
                'state': state
            }
            
            if zip_codes:
                for zip_code in zip_codes:
                    search_params['zip_code'] = zip_code
                    records = await self.public_records_client.search_by_address(
                        address="",
                        **search_params
                    )
                    
                    for record in records:
                        if self._has_tax_delinquency(record):
                            opportunity = await self._create_tax_delinquent_opportunity(record)
                            if opportunity:
                                opportunities.append(opportunity)
            
        except Exception as e:
            logger.error(f"Error finding tax delinquent properties: {e}")
        
        return opportunities

    async def _find_vacant_properties(
        self,
        city: str,
        state: str,
        zip_codes: Optional[List[str]] = None
    ) -> List[OffMarketOpportunity]:
        """Find vacant properties using various indicators."""
        opportunities = []
        
        try:
            # Use multiple data sources to identify vacant properties
            # This could include utility data, mail delivery status, etc.
            
            # For now, use property records and MLS history
            if self.mls_client:
                # Look for properties with long days on market or frequent listings
                mls_properties = await self.mls_client.search_properties(
                    city=city,
                    state=state,
                    limit=500
                )
                
                for prop in mls_properties:
                    if self._indicates_vacancy(prop):
                        opportunity = await self._create_vacant_opportunity(prop)
                        if opportunity:
                            opportunities.append(opportunity)
            
        except Exception as e:
            logger.error(f"Error finding vacant properties: {e}")
        
        return opportunities

    async def _find_distressed_properties(
        self,
        city: str,
        state: str,
        zip_codes: Optional[List[str]] = None
    ) -> List[OffMarketOpportunity]:
        """Find properties with distressed owners."""
        opportunities = []
        
        try:
            # Combine foreclosure data with other distress indicators
            if self.foreclosure_client:
                # Get pre-foreclosure properties
                pre_foreclosures = await self.foreclosure_client.get_pre_foreclosures(
                    city=city,
                    state=state
                )
                
                for foreclosure in pre_foreclosures:
                    opportunity = await self._create_distressed_opportunity(foreclosure)
                    if opportunity:
                        opportunities.append(opportunity)
            
        except Exception as e:
            logger.error(f"Error finding distressed properties: {e}")
        
        return opportunities

    def _is_absentee_owner(self, record) -> bool:
        """Check if property owner is absentee."""
        if not record.owner_info or not record.owner_info.mailing_address:
            return False
        
        property_address = record.property_address.lower().strip()
        mailing_address = record.owner_info.mailing_address.lower().strip()
        
        # Simple check - if mailing address is different from property address
        return property_address != mailing_address

    def _has_tax_delinquency(self, record) -> bool:
        """Check if property has tax delinquency."""
        if not record.tax_record:
            return False
        
        # Check payment status
        if record.tax_record.payment_status and 'delinquent' in record.tax_record.payment_status.lower():
            return True
        
        # Check if due date has passed without payment
        if record.tax_record.due_date and not record.tax_record.last_payment_date:
            return record.tax_record.due_date < datetime.now()
        
        return False

    def _indicates_vacancy(self, property_data) -> bool:
        """Check if property indicators suggest vacancy."""
        # High days on market
        if hasattr(property_data, 'days_on_market') and property_data.days_on_market:
            if property_data.days_on_market > 180:
                return True
        
        # Multiple recent listings
        # This would require additional MLS history data
        
        return False

    async def _analyze_equity_opportunity(self, record) -> Optional[OffMarketOpportunity]:
        """Analyze a property record for equity opportunity."""
        try:
            if not record.tax_record or not record.tax_record.assessed_value:
                return None
            
            # Estimate market value (simplified - would use more sophisticated methods)
            assessed_value = record.tax_record.assessed_value
            estimated_market_value = assessed_value * 1.2  # Rough multiplier
            
            # Calculate potential equity
            estimated_equity = estimated_market_value * 0.7  # Assuming some debt
            
            if estimated_equity < 50000:  # Minimum equity threshold
                return None
            
            # Create opportunity
            opportunity_id = f"HE_{record.record_id}_{int(datetime.now().timestamp())}"
            
            owner_research = None
            if record.owner_info:
                owner_research = OwnerResearch(
                    name=record.owner_info.name,
                    mailing_address=record.owner_info.mailing_address,
                    is_absentee_owner=self._is_absentee_owner(record),
                    last_updated=datetime.now()
                )
            
            motivation_indicators = MotivationIndicators(
                multiple_properties=True,  # Would need to verify
                motivation_score=0.6,
                confidence_level=0.7
            )
            
            return OffMarketOpportunity(
                opportunity_id=opportunity_id,
                property_address=record.property_address,
                city=record.property_address.split(',')[1].strip() if ',' in record.property_address else "",
                state=record.state,
                zip_code="",  # Would extract from address
                opportunity_types=[OpportunityType.HIGH_EQUITY],
                estimated_value=estimated_market_value,
                estimated_equity=estimated_equity,
                owner_research=owner_research,
                motivation_indicators=motivation_indicators,
                tax_assessed_value=assessed_value,
                opportunity_score=0.0,  # Will be calculated later
                confidence_score=0.7,
                discovered_date=datetime.now(),
                last_updated=datetime.now(),
                raw_data=record.raw_data
            )
            
        except Exception as e:
            logger.error(f"Error analyzing equity opportunity: {e}")
            return None

    async def _create_absentee_opportunity(self, record) -> Optional[OffMarketOpportunity]:
        """Create opportunity for absentee owner property."""
        try:
            opportunity_id = f"AO_{record.record_id}_{int(datetime.now().timestamp())}"
            
            owner_research = OwnerResearch(
                name=record.owner_info.name,
                mailing_address=record.owner_info.mailing_address,
                is_absentee_owner=True,
                contact_confidence=0.8,
                last_updated=datetime.now()
            )
            
            motivation_indicators = MotivationIndicators(
                multiple_properties=True,
                motivation_score=0.7,
                confidence_level=0.8
            )
            
            return OffMarketOpportunity(
                opportunity_id=opportunity_id,
                property_address=record.property_address,
                city=record.property_address.split(',')[1].strip() if ',' in record.property_address else "",
                state=record.state,
                zip_code="",
                opportunity_types=[OpportunityType.ABSENTEE_OWNER],
                owner_research=owner_research,
                motivation_indicators=motivation_indicators,
                opportunity_score=0.0,
                confidence_score=0.8,
                discovered_date=datetime.now(),
                last_updated=datetime.now(),
                raw_data=record.raw_data
            )
            
        except Exception as e:
            logger.error(f"Error creating absentee opportunity: {e}")
            return None

    async def _create_tax_delinquent_opportunity(self, record) -> Optional[OffMarketOpportunity]:
        """Create opportunity for tax delinquent property."""
        try:
            opportunity_id = f"TD_{record.record_id}_{int(datetime.now().timestamp())}"
            
            owner_research = None
            if record.owner_info:
                owner_research = OwnerResearch(
                    name=record.owner_info.name,
                    mailing_address=record.owner_info.mailing_address,
                    last_updated=datetime.now()
                )
            
            motivation_indicators = MotivationIndicators(
                financial_distress=True,
                tax_delinquency=True,
                motivation_score=0.85,
                confidence_level=0.9
            )
            
            return OffMarketOpportunity(
                opportunity_id=opportunity_id,
                property_address=record.property_address,
                city=record.property_address.split(',')[1].strip() if ',' in record.property_address else "",
                state=record.state,
                zip_code="",
                opportunity_types=[OpportunityType.TAX_DELINQUENT],
                owner_research=owner_research,
                motivation_indicators=motivation_indicators,
                tax_assessed_value=record.tax_record.assessed_value if record.tax_record else None,
                opportunity_score=0.0,
                confidence_score=0.9,
                discovered_date=datetime.now(),
                last_updated=datetime.now(),
                raw_data=record.raw_data
            )
            
        except Exception as e:
            logger.error(f"Error creating tax delinquent opportunity: {e}")
            return None

    async def _create_vacant_opportunity(self, property_data) -> Optional[OffMarketOpportunity]:
        """Create opportunity for vacant property."""
        try:
            opportunity_id = f"VP_{property_data.mls_id}_{int(datetime.now().timestamp())}"
            
            motivation_indicators = MotivationIndicators(
                vacant_property=True,
                motivation_score=0.75,
                confidence_level=0.6
            )
            
            condition_estimate = PropertyConditionEstimate(
                overall_condition=PropertyCondition.FAIR,
                condition_score=60.0,
                confidence_level=0.5,
                last_assessed=datetime.now()
            )
            
            return OffMarketOpportunity(
                opportunity_id=opportunity_id,
                property_address=property_data.address,
                city=property_data.city,
                state=property_data.state,
                zip_code=property_data.zip_code,
                opportunity_types=[OpportunityType.VACANT_PROPERTY],
                estimated_value=property_data.price,
                bedrooms=property_data.bedrooms,
                bathrooms=property_data.bathrooms,
                square_feet=property_data.square_feet,
                year_built=property_data.year_built,
                property_type=property_data.property_type,
                motivation_indicators=motivation_indicators,
                condition_estimate=condition_estimate,
                opportunity_score=0.0,
                confidence_score=0.6,
                discovered_date=datetime.now(),
                last_updated=datetime.now(),
                raw_data=property_data.raw_data
            )
            
        except Exception as e:
            logger.error(f"Error creating vacant opportunity: {e}")
            return None

    async def _create_distressed_opportunity(self, foreclosure_data) -> Optional[OffMarketOpportunity]:
        """Create opportunity for distressed property."""
        try:
            opportunity_id = f"DO_{foreclosure_data.foreclosure_id}_{int(datetime.now().timestamp())}"
            
            owner_research = OwnerResearch(
                name=foreclosure_data.borrower_name or "Unknown",
                last_updated=datetime.now()
            )
            
            motivation_indicators = MotivationIndicators(
                financial_distress=True,
                motivation_score=0.9,
                confidence_level=0.95
            )
            
            return OffMarketOpportunity(
                opportunity_id=opportunity_id,
                property_address=foreclosure_data.property_address,
                city=foreclosure_data.city,
                state=foreclosure_data.state,
                zip_code=foreclosure_data.zip_code,
                opportunity_types=[OpportunityType.DISTRESSED_OWNER],
                estimated_value=foreclosure_data.estimated_value,
                bedrooms=foreclosure_data.bedrooms,
                bathrooms=foreclosure_data.bathrooms,
                square_feet=foreclosure_data.square_feet,
                year_built=foreclosure_data.year_built,
                property_type=foreclosure_data.property_type,
                owner_research=owner_research,
                motivation_indicators=motivation_indicators,
                opportunity_score=0.0,
                confidence_score=0.95,
                discovered_date=datetime.now(),
                last_updated=datetime.now(),
                raw_data=foreclosure_data.raw_data
            )
            
        except Exception as e:
            logger.error(f"Error creating distressed opportunity: {e}")
            return None

    def _deduplicate_opportunities(
        self,
        opportunities: List[OffMarketOpportunity]
    ) -> List[OffMarketOpportunity]:
        """Remove duplicate opportunities based on property address."""
        seen_addresses = set()
        unique_opportunities = []
        
        for opportunity in opportunities:
            address_key = f"{opportunity.property_address.lower()}_{opportunity.city.lower()}_{opportunity.state.lower()}"
            
            if address_key not in seen_addresses:
                seen_addresses.add(address_key)
                unique_opportunities.append(opportunity)
            else:
                # Merge opportunity types if duplicate found
                for existing in unique_opportunities:
                    existing_key = f"{existing.property_address.lower()}_{existing.city.lower()}_{existing.state.lower()}"
                    if existing_key == address_key:
                        # Merge opportunity types
                        for opp_type in opportunity.opportunity_types:
                            if opp_type not in existing.opportunity_types:
                                existing.opportunity_types.append(opp_type)
                        break
        
        return unique_opportunities

    async def _score_opportunities(
        self,
        opportunities: List[OffMarketOpportunity]
    ) -> List[OffMarketOpportunity]:
        """Score opportunities based on various factors."""
        for opportunity in opportunities:
            score = 0.0
            
            # Base score from opportunity types
            for opp_type in opportunity.opportunity_types:
                score += self.opportunity_weights.get(opp_type, 0.5)
            
            # Motivation score
            if opportunity.motivation_indicators:
                score += opportunity.motivation_indicators.motivation_score * 0.3
            
            # Equity potential
            if opportunity.estimated_equity and opportunity.estimated_value:
                equity_ratio = opportunity.estimated_equity / opportunity.estimated_value
                score += min(equity_ratio, 0.5) * 0.2
            
            # Property condition (lower condition = higher opportunity)
            if opportunity.condition_estimate:
                condition_bonus = (100 - opportunity.condition_estimate.condition_score) / 100 * 0.1
                score += condition_bonus
            
            # Confidence adjustment
            score *= opportunity.confidence_score
            
            # Normalize to 0-1 scale
            opportunity.opportunity_score = min(score, 1.0)
        
        return opportunities

    def _filter_opportunities(
        self,
        opportunities: List[OffMarketOpportunity],
        min_equity: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> List[OffMarketOpportunity]:
        """Filter opportunities based on criteria."""
        filtered = []
        
        for opportunity in opportunities:
            # Filter by minimum equity
            if min_equity and opportunity.estimated_equity:
                if opportunity.estimated_equity < min_equity:
                    continue
            
            # Filter by maximum price
            if max_price and opportunity.estimated_value:
                if opportunity.estimated_value > max_price:
                    continue
            
            filtered.append(opportunity)
        
        return filtered

    async def research_owner_contact_info(
        self,
        opportunity: OffMarketOpportunity
    ) -> OwnerResearch:
        """Research and enrich owner contact information."""
        try:
            if not opportunity.owner_research:
                return OwnerResearch(name="Unknown")
            
            owner_name = opportunity.owner_research.name
            property_address = opportunity.property_address
            
            # Use public records client to enrich contact info
            if self.public_records_client:
                enriched_info = await self.public_records_client.enrich_contact_info(
                    owner_name=owner_name,
                    property_address=property_address
                )
                
                opportunity.owner_research.phone_numbers = enriched_info.get('phone_numbers', [])
                opportunity.owner_research.email_addresses = enriched_info.get('email_addresses', [])
                opportunity.owner_research.social_profiles = enriched_info.get('social_profiles', [])
                opportunity.owner_research.business_affiliations = enriched_info.get('business_info', {}).get('company', [])
                opportunity.owner_research.contact_confidence = enriched_info.get('confidence_scores', {}).get('overall', 0.0)
                opportunity.owner_research.last_updated = datetime.now()
            
            return opportunity.owner_research
            
        except Exception as e:
            logger.error(f"Error researching owner contact info: {e}")
            return opportunity.owner_research or OwnerResearch(name="Unknown")

    async def estimate_property_condition(
        self,
        opportunity: OffMarketOpportunity
    ) -> PropertyConditionEstimate:
        """Estimate property condition using available data."""
        try:
            condition_score = 70.0  # Default fair condition
            condition_indicators = []
            data_sources = []
            
            # Analyze age of property
            if opportunity.year_built:
                age = datetime.now().year - opportunity.year_built
                if age > 50:
                    condition_score -= 20
                    condition_indicators.append("older_property")
                elif age > 30:
                    condition_score -= 10
                    condition_indicators.append("mature_property")
            
            # Analyze opportunity types for condition clues
            for opp_type in opportunity.opportunity_types:
                if opp_type == OpportunityType.DISTRESSED_OWNER:
                    condition_score -= 15
                    condition_indicators.append("potential_deferred_maintenance")
                elif opp_type == OpportunityType.VACANT_PROPERTY:
                    condition_score -= 10
                    condition_indicators.append("vacancy_deterioration")
                elif opp_type == OpportunityType.CODE_VIOLATIONS:
                    condition_score -= 25
                    condition_indicators.append("code_violations")
            
            # Determine overall condition
            if condition_score >= 85:
                overall_condition = PropertyCondition.EXCELLENT
            elif condition_score >= 70:
                overall_condition = PropertyCondition.GOOD
            elif condition_score >= 55:
                overall_condition = PropertyCondition.FAIR
            elif condition_score >= 40:
                overall_condition = PropertyCondition.POOR
            else:
                overall_condition = PropertyCondition.DISTRESSED
            
            # Estimate repair costs based on condition
            repair_estimate = None
            if opportunity.square_feet:
                if overall_condition == PropertyCondition.POOR:
                    repair_estimate = opportunity.square_feet * 25  # $25/sq ft
                elif overall_condition == PropertyCondition.DISTRESSED:
                    repair_estimate = opportunity.square_feet * 40  # $40/sq ft
                elif overall_condition == PropertyCondition.FAIR:
                    repair_estimate = opportunity.square_feet * 15  # $15/sq ft
            
            return PropertyConditionEstimate(
                overall_condition=overall_condition,
                condition_score=condition_score,
                repair_estimate=repair_estimate,
                condition_indicators=condition_indicators,
                data_sources=data_sources,
                confidence_level=0.6,
                last_assessed=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error estimating property condition: {e}")
            return PropertyConditionEstimate(
                overall_condition=PropertyCondition.FAIR,
                condition_score=70.0,
                confidence_level=0.3,
                last_assessed=datetime.now()
            )


# Example usage and testing
async def main():
    """Example usage of OffMarketPropertyFinder."""
    # This would typically be initialized with actual client instances
    finder = OffMarketPropertyFinder()
    
    try:
        # Find off-market opportunities
        opportunities = await finder.find_opportunities(
            city="Austin",
            state="TX",
            min_equity=50000,
            opportunity_types=[
                OpportunityType.HIGH_EQUITY,
                OpportunityType.ABSENTEE_OWNER,
                OpportunityType.TAX_DELINQUENT
            ],
            limit=20
        )
        
        print(f"Found {len(opportunities)} off-market opportunities")
        
        for opp in opportunities[:5]:
            print(f"\n- {opp.property_address}")
            print(f"  Opportunity Types: {[ot.value for ot in opp.opportunity_types]}")
            print(f"  Opportunity Score: {opp.opportunity_score:.2f}")
            print(f"  Estimated Value: ${opp.estimated_value:,.0f}" if opp.estimated_value else "  Estimated Value: Unknown")
            print(f"  Estimated Equity: ${opp.estimated_equity:,.0f}" if opp.estimated_equity else "  Estimated Equity: Unknown")
            
            if opp.owner_research:
                print(f"  Owner: {opp.owner_research.name}")
                if opp.owner_research.is_absentee_owner:
                    print("  Absentee Owner: Yes")
            
            if opp.motivation_indicators:
                print(f"  Motivation Score: {opp.motivation_indicators.motivation_score:.2f}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())