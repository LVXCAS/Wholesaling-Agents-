"""
Public Records API client for property ownership and tax data integration.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import aiohttp
import json
from dataclasses import dataclass, asdict
from enum import Enum
import re
import time

logger = logging.getLogger(__name__)


class RecordType(Enum):
    """Types of public records."""
    PROPERTY_TAX = "property_tax"
    DEED = "deed"
    MORTGAGE = "mortgage"
    LIEN = "lien"
    PERMIT = "permit"
    ASSESSMENT = "assessment"


@dataclass
class OwnerInfo:
    """Property owner information from public records."""
    name: str
    mailing_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    ownership_percentage: Optional[float] = None
    acquisition_date: Optional[datetime] = None
    acquisition_price: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        if data.get('acquisition_date'):
            data['acquisition_date'] = data['acquisition_date'].isoformat()
        return data


@dataclass
class PropertyTaxRecord:
    """Property tax record information."""
    property_id: str
    tax_year: int
    assessed_value: float
    tax_amount: float
    market_value: Optional[float] = None
    exemptions: Optional[List[str]] = None
    payment_status: Optional[str] = None
    due_date: Optional[datetime] = None
    last_payment_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        if data.get('due_date'):
            data['due_date'] = data['due_date'].isoformat()
        if data.get('last_payment_date'):
            data['last_payment_date'] = data['last_payment_date'].isoformat()
        return data


@dataclass
class DeedRecord:
    """Property deed record information."""
    property_id: str
    deed_type: str
    grantor: str
    grantee: str
    sale_price: Optional[float] = None
    recording_date: Optional[datetime] = None
    document_number: Optional[str] = None
    legal_description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        if data.get('recording_date'):
            data['recording_date'] = data['recording_date'].isoformat()
        return data


@dataclass
class PublicRecord:
    """Generic public record structure."""
    record_id: str
    property_address: str
    record_type: RecordType
    county: str
    state: str
    owner_info: Optional[OwnerInfo] = None
    tax_record: Optional[PropertyTaxRecord] = None
    deed_record: Optional[DeedRecord] = None
    raw_data: Optional[Dict[str, Any]] = None
    last_updated: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['record_type'] = data['record_type'].value
        if data.get('last_updated'):
            data['last_updated'] = data['last_updated'].isoformat()
        if data.get('owner_info'):
            data['owner_info'] = self.owner_info.to_dict()
        if data.get('tax_record'):
            data['tax_record'] = self.tax_record.to_dict()
        if data.get('deed_record'):
            data['deed_record'] = self.deed_record.to_dict()
        return data


class PublicRecordsAPIError(Exception):
    """Custom exception for Public Records API errors."""
    pass


class PublicRecordsClient:
    """
    Public Records API client for property ownership and tax data.
    
    This client integrates with various public records databases to extract
    property ownership information, tax records, and transaction history.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_per_minute: int = 120
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_per_minute = rate_limit_per_minute
        self._last_request_time = 0
        self._request_count = 0
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()

    async def _ensure_session(self):
        """Ensure session is available."""
        if not self._session:
            self._session = aiohttp.ClientSession()

    async def _rate_limit(self):
        """Implement rate limiting."""
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self._last_request_time > 60:
            self._request_count = 0
            self._last_request_time = current_time
        
        # Check if we've exceeded rate limit
        if self._request_count >= self.rate_limit_per_minute:
            sleep_time = 60 - (current_time - self._last_request_time)
            if sleep_time > 0:
                logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
                self._request_count = 0
                self._last_request_time = time.time()
        
        self._request_count += 1

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            
        Returns:
            Response data as dictionary
            
        Raises:
            PublicRecordsAPIError: For API errors
        """
        await self._ensure_session()
        await self._rate_limit()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'RealEstateEmpire-PublicRecordsClient/1.0'
        }
        
        for attempt in range(self.max_retries + 1):
            try:
                async with self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    # Handle rate limiting
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 60))
                        logger.warning(f"Rate limited, waiting {retry_after} seconds")
                        if attempt < self.max_retries:
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            raise PublicRecordsAPIError("Rate limit exceeded")
                    
                    # Handle other HTTP errors
                    if response.status >= 400:
                        error_text = await response.text()
                        logger.error(f"Public Records API error {response.status}: {error_text}")
                        if attempt < self.max_retries and response.status >= 500:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                            continue
                        else:
                            raise PublicRecordsAPIError(f"HTTP {response.status}: {error_text}")
                    
                    # Parse response
                    try:
                        return await response.json()
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON response: {e}")
                        raise PublicRecordsAPIError(f"Invalid JSON response: {e}")
                        
            except aiohttp.ClientError as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    raise PublicRecordsAPIError(f"Request failed after {self.max_retries} retries: {e}")
        
        raise PublicRecordsAPIError("Max retries exceeded")

    def _extract_owner_info(self, raw_data: Dict[str, Any]) -> OwnerInfo:
        """Extract and normalize owner information from raw data."""
        try:
            # Extract owner name
            owner_name = (
                raw_data.get('owner_name') or
                raw_data.get('OwnerName') or
                raw_data.get('PropertyOwner') or
                ""
            ).strip()
            
            # Extract mailing address
            mailing_address = (
                raw_data.get('mailing_address') or
                raw_data.get('MailingAddress') or
                raw_data.get('owner_address')
            )
            
            # Extract address components
            city = raw_data.get('owner_city') or raw_data.get('MailingCity')
            state = raw_data.get('owner_state') or raw_data.get('MailingState')
            zip_code = raw_data.get('owner_zip') or raw_data.get('MailingZip')
            
            # Extract contact information
            phone = self._clean_phone_number(
                raw_data.get('owner_phone') or raw_data.get('PhoneNumber')
            )
            email = raw_data.get('owner_email') or raw_data.get('EmailAddress')
            
            # Extract ownership details
            ownership_percentage = raw_data.get('ownership_percentage')
            if ownership_percentage:
                ownership_percentage = float(ownership_percentage)
            
            # Parse acquisition date
            acquisition_date = None
            date_str = raw_data.get('acquisition_date') or raw_data.get('PurchaseDate')
            if date_str:
                try:
                    acquisition_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    try:
                        acquisition_date = datetime.strptime(date_str, '%Y-%m-%d')
                    except ValueError:
                        logger.warning(f"Could not parse acquisition date: {date_str}")
            
            # Extract acquisition price
            acquisition_price = raw_data.get('acquisition_price') or raw_data.get('PurchasePrice')
            if acquisition_price:
                acquisition_price = float(acquisition_price)
            
            return OwnerInfo(
                name=owner_name,
                mailing_address=mailing_address,
                city=city,
                state=state,
                zip_code=zip_code,
                phone=phone,
                email=email,
                ownership_percentage=ownership_percentage,
                acquisition_date=acquisition_date,
                acquisition_price=acquisition_price
            )
            
        except Exception as e:
            logger.error(f"Error extracting owner info: {e}")
            return OwnerInfo(name="Unknown")

    def _extract_tax_record(self, raw_data: Dict[str, Any]) -> Optional[PropertyTaxRecord]:
        """Extract tax record information from raw data."""
        try:
            if not any(key in raw_data for key in ['tax_year', 'TaxYear', 'assessed_value', 'AssessedValue']):
                return None
            
            property_id = raw_data.get('property_id') or raw_data.get('PropertyID') or ""
            tax_year = int(raw_data.get('tax_year') or raw_data.get('TaxYear') or datetime.now().year)
            
            assessed_value = float(
                raw_data.get('assessed_value') or 
                raw_data.get('AssessedValue') or 
                0
            )
            
            market_value = raw_data.get('market_value') or raw_data.get('MarketValue')
            if market_value:
                market_value = float(market_value)
            
            tax_amount = float(
                raw_data.get('tax_amount') or 
                raw_data.get('TaxAmount') or 
                0
            )
            
            exemptions = raw_data.get('exemptions') or raw_data.get('Exemptions')
            if isinstance(exemptions, str):
                exemptions = [exemptions]
            
            payment_status = raw_data.get('payment_status') or raw_data.get('PaymentStatus')
            
            # Parse dates
            due_date = None
            due_date_str = raw_data.get('due_date') or raw_data.get('DueDate')
            if due_date_str:
                try:
                    due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    try:
                        due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                    except ValueError:
                        logger.warning(f"Could not parse due date: {due_date_str}")
            
            last_payment_date = None
            payment_date_str = raw_data.get('last_payment_date') or raw_data.get('LastPaymentDate')
            if payment_date_str:
                try:
                    last_payment_date = datetime.fromisoformat(payment_date_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    try:
                        last_payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d')
                    except ValueError:
                        logger.warning(f"Could not parse payment date: {payment_date_str}")
            
            return PropertyTaxRecord(
                property_id=property_id,
                tax_year=tax_year,
                assessed_value=assessed_value,
                market_value=market_value,
                tax_amount=tax_amount,
                exemptions=exemptions,
                payment_status=payment_status,
                due_date=due_date,
                last_payment_date=last_payment_date
            )
            
        except Exception as e:
            logger.error(f"Error extracting tax record: {e}")
            return None

    def _extract_deed_record(self, raw_data: Dict[str, Any]) -> Optional[DeedRecord]:
        """Extract deed record information from raw data."""
        try:
            if not any(key in raw_data for key in ['deed_type', 'DeedType', 'grantor', 'Grantor']):
                return None
            
            property_id = raw_data.get('property_id') or raw_data.get('PropertyID') or ""
            deed_type = raw_data.get('deed_type') or raw_data.get('DeedType') or ""
            grantor = raw_data.get('grantor') or raw_data.get('Grantor') or ""
            grantee = raw_data.get('grantee') or raw_data.get('Grantee') or ""
            
            sale_price = raw_data.get('sale_price') or raw_data.get('SalePrice')
            if sale_price:
                sale_price = float(sale_price)
            
            # Parse recording date
            recording_date = None
            date_str = raw_data.get('recording_date') or raw_data.get('RecordingDate')
            if date_str:
                try:
                    recording_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    try:
                        recording_date = datetime.strptime(date_str, '%Y-%m-%d')
                    except ValueError:
                        logger.warning(f"Could not parse recording date: {date_str}")
            
            document_number = raw_data.get('document_number') or raw_data.get('DocumentNumber')
            legal_description = raw_data.get('legal_description') or raw_data.get('LegalDescription')
            
            return DeedRecord(
                property_id=property_id,
                deed_type=deed_type,
                grantor=grantor,
                grantee=grantee,
                sale_price=sale_price,
                recording_date=recording_date,
                document_number=document_number,
                legal_description=legal_description
            )
            
        except Exception as e:
            logger.error(f"Error extracting deed record: {e}")
            return None

    def _clean_phone_number(self, phone: Optional[str]) -> Optional[str]:
        """Clean and format phone number."""
        if not phone:
            return None
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Format as (XXX) XXX-XXXX if 10 digits
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return phone  # Return original if can't format

    async def search_by_address(
        self,
        address: str,
        city: str,
        state: str,
        zip_code: Optional[str] = None
    ) -> List[PublicRecord]:
        """
        Search for public records by property address.
        
        Args:
            address: Property address
            city: City name
            state: State abbreviation
            zip_code: ZIP code (optional)
            
        Returns:
            List of public records for the property
        """
        params = {
            'address': address,
            'city': city,
            'state': state
        }
        
        if zip_code:
            params['zip_code'] = zip_code
        
        try:
            response = await self._make_request('GET', '/records/search', params=params)
            
            records = []
            for raw_record in response.get('records', []):
                try:
                    record = self._normalize_record_data(raw_record)
                    records.append(record)
                except Exception as e:
                    logger.error(f"Failed to normalize record: {e}")
                    continue
            
            logger.info(f"Retrieved {len(records)} public records for {address}")
            return records
            
        except Exception as e:
            logger.error(f"Failed to search records by address: {e}")
            raise

    async def search_by_owner(
        self,
        owner_name: str,
        county: Optional[str] = None,
        state: Optional[str] = None
    ) -> List[PublicRecord]:
        """
        Search for public records by owner name.
        
        Args:
            owner_name: Property owner name
            county: County name (optional)
            state: State abbreviation (optional)
            
        Returns:
            List of public records for the owner
        """
        params = {'owner_name': owner_name}
        
        if county:
            params['county'] = county
        if state:
            params['state'] = state
        
        try:
            response = await self._make_request('GET', '/records/owner', params=params)
            
            records = []
            for raw_record in response.get('records', []):
                try:
                    record = self._normalize_record_data(raw_record)
                    records.append(record)
                except Exception as e:
                    logger.error(f"Failed to normalize owner record: {e}")
                    continue
            
            logger.info(f"Retrieved {len(records)} records for owner {owner_name}")
            return records
            
        except Exception as e:
            logger.error(f"Failed to search records by owner: {e}")
            raise

    async def get_property_tax_history(
        self,
        property_id: str,
        years: int = 5
    ) -> List[PropertyTaxRecord]:
        """
        Get property tax history for a specific property.
        
        Args:
            property_id: Property identifier
            years: Number of years of history to retrieve
            
        Returns:
            List of property tax records
        """
        params = {
            'property_id': property_id,
            'years': years
        }
        
        try:
            response = await self._make_request('GET', '/tax/history', params=params)
            
            tax_records = []
            for raw_record in response.get('tax_records', []):
                try:
                    tax_record = self._extract_tax_record(raw_record)
                    if tax_record:
                        tax_records.append(tax_record)
                except Exception as e:
                    logger.error(f"Failed to extract tax record: {e}")
                    continue
            
            logger.info(f"Retrieved {len(tax_records)} tax records for property {property_id}")
            return tax_records
            
        except Exception as e:
            logger.error(f"Failed to get tax history: {e}")
            raise

    async def get_deed_history(
        self,
        property_id: str,
        years: int = 10
    ) -> List[DeedRecord]:
        """
        Get deed transaction history for a property.
        
        Args:
            property_id: Property identifier
            years: Number of years of history to retrieve
            
        Returns:
            List of deed records
        """
        params = {
            'property_id': property_id,
            'years': years
        }
        
        try:
            response = await self._make_request('GET', '/deeds/history', params=params)
            
            deed_records = []
            for raw_record in response.get('deed_records', []):
                try:
                    deed_record = self._extract_deed_record(raw_record)
                    if deed_record:
                        deed_records.append(deed_record)
                except Exception as e:
                    logger.error(f"Failed to extract deed record: {e}")
                    continue
            
            logger.info(f"Retrieved {len(deed_records)} deed records for property {property_id}")
            return deed_records
            
        except Exception as e:
            logger.error(f"Failed to get deed history: {e}")
            raise

    def _normalize_record_data(self, raw_data: Dict[str, Any]) -> PublicRecord:
        """
        Normalize raw public record data to standard format.
        
        Args:
            raw_data: Raw record data from API
            
        Returns:
            Normalized PublicRecord object
        """
        try:
            record_id = str(raw_data.get('record_id', raw_data.get('RecordID', '')))
            property_address = raw_data.get('property_address', raw_data.get('PropertyAddress', ''))
            county = raw_data.get('county', raw_data.get('County', ''))
            state = raw_data.get('state', raw_data.get('State', ''))
            
            # Determine record type
            record_type = RecordType.PROPERTY_TAX  # Default
            if raw_data.get('record_type'):
                try:
                    record_type = RecordType(raw_data['record_type'])
                except ValueError:
                    logger.warning(f"Unknown record type: {raw_data['record_type']}")
            
            # Extract structured data
            owner_info = self._extract_owner_info(raw_data)
            tax_record = self._extract_tax_record(raw_data)
            deed_record = self._extract_deed_record(raw_data)
            
            return PublicRecord(
                record_id=record_id,
                property_address=property_address,
                record_type=record_type,
                county=county,
                state=state,
                owner_info=owner_info,
                tax_record=tax_record,
                deed_record=deed_record,
                raw_data=raw_data,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error normalizing record data: {e}")
            logger.error(f"Raw data: {raw_data}")
            raise PublicRecordsAPIError(f"Failed to normalize record data: {e}")

    async def validate_owner_info(
        self,
        owner_name: str,
        property_address: str
    ) -> Dict[str, Any]:
        """
        Validate owner information against public records.
        
        Args:
            owner_name: Owner name to validate
            property_address: Property address
            
        Returns:
            Validation results with confidence score
        """
        try:
            params = {
                'owner_name': owner_name,
                'property_address': property_address
            }
            
            response = await self._make_request('GET', '/validate/owner', params=params)
            
            return {
                'is_valid': response.get('is_valid', False),
                'confidence_score': response.get('confidence_score', 0.0),
                'match_details': response.get('match_details', {}),
                'alternative_names': response.get('alternative_names', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to validate owner info: {e}")
            raise

    async def enrich_contact_info(
        self,
        owner_name: str,
        property_address: str
    ) -> Dict[str, Any]:
        """
        Enrich owner contact information from multiple sources.
        
        Args:
            owner_name: Owner name
            property_address: Property address
            
        Returns:
            Enriched contact information
        """
        try:
            params = {
                'owner_name': owner_name,
                'property_address': property_address
            }
            
            response = await self._make_request('GET', '/enrich/contact', params=params)
            
            return {
                'phone_numbers': response.get('phone_numbers', []),
                'email_addresses': response.get('email_addresses', []),
                'social_profiles': response.get('social_profiles', []),
                'business_info': response.get('business_info', {}),
                'confidence_scores': response.get('confidence_scores', {})
            }
            
        except Exception as e:
            logger.error(f"Failed to enrich contact info: {e}")
            raise


# Example usage and testing
async def main():
    """Example usage of PublicRecordsClient."""
    client = PublicRecordsClient(
        api_key="your-api-key",
        base_url="https://api.public-records-provider.com/v1"
    )
    
    async with client:
        try:
            # Search by address
            records = await client.search_by_address(
                address="123 Main St",
                city="Austin",
                state="TX",
                zip_code="78701"
            )
            
            print(f"Found {len(records)} public records")
            for record in records:
                if record.owner_info:
                    print(f"Owner: {record.owner_info.name}")
                if record.tax_record:
                    print(f"Assessed Value: ${record.tax_record.assessed_value:,.0f}")
            
            # Search by owner
            owner_records = await client.search_by_owner(
                owner_name="John Smith",
                state="TX"
            )
            
            print(f"Found {len(owner_records)} properties for John Smith")
            
        except PublicRecordsAPIError as e:
            print(f"Public Records API Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())