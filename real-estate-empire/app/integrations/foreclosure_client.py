"""
Foreclosure data API client for distressed property integration.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import aiohttp
import json
from dataclasses import dataclass, asdict
from enum import Enum
import time

logger = logging.getLogger(__name__)


class ForeclosureStatus(Enum):
    """Foreclosure status enumeration."""
    PRE_FORECLOSURE = "pre_foreclosure"
    AUCTION_SCHEDULED = "auction_scheduled"
    AUCTION_POSTPONED = "auction_postponed"
    SOLD_AT_AUCTION = "sold_at_auction"
    BANK_OWNED = "bank_owned"
    CANCELLED = "cancelled"
    REDEEMED = "redeemed"


class AuctionType(Enum):
    """Auction type enumeration."""
    TRUSTEE_SALE = "trustee_sale"
    SHERIFF_SALE = "sheriff_sale"
    JUDICIAL_SALE = "judicial_sale"
    TAX_SALE = "tax_sale"


@dataclass
class ForeclosureProperty:
    """Foreclosure property data structure."""
    foreclosure_id: str
    property_address: str
    city: str
    state: str
    zip_code: str
    status: ForeclosureStatus
    auction_type: Optional[AuctionType] = None
    auction_date: Optional[datetime] = None
    auction_time: Optional[str] = None
    auction_location: Optional[str] = None
    opening_bid: Optional[float] = None
    estimated_value: Optional[float] = None
    loan_balance: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    property_type: Optional[str] = None
    default_amount: Optional[float] = None
    filing_date: Optional[datetime] = None
    trustee_name: Optional[str] = None
    trustee_phone: Optional[str] = None
    lender_name: Optional[str] = None
    borrower_name: Optional[str] = None
    legal_description: Optional[str] = None
    case_number: Optional[str] = None
    photos: Optional[List[str]] = None
    days_until_auction: Optional[int] = None
    postponement_count: Optional[int] = None
    last_updated: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert enum values to strings
        data['status'] = data['status'].value
        if data.get('auction_type'):
            data['auction_type'] = data['auction_type'].value
        # Convert datetime objects to ISO strings
        for date_field in ['auction_date', 'filing_date', 'last_updated']:
            if data.get(date_field):
                data[date_field] = data[date_field].isoformat()
        return data


@dataclass
class AuctionInfo:
    """Auction information structure."""
    auction_id: str
    property_address: str
    auction_date: datetime
    auction_time: str
    auction_location: str
    auction_type: AuctionType
    opening_bid: float
    estimated_value: Optional[float] = None
    trustee_name: Optional[str] = None
    trustee_phone: Optional[str] = None
    registration_required: bool = True
    deposit_required: Optional[float] = None
    terms_of_sale: Optional[str] = None
    postponement_history: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['auction_type'] = data['auction_type'].value
        data['auction_date'] = data['auction_date'].isoformat()
        return data


class ForeclosureAPIError(Exception):
    """Custom exception for Foreclosure API errors."""
    pass


class ForeclosureClient:
    """
    Foreclosure data API client for distressed property information.
    
    This client integrates with foreclosure data providers to track
    properties in various stages of foreclosure, auction schedules,
    and distressed property opportunities.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_per_minute: int = 100
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
            ForeclosureAPIError: For API errors
        """
        await self._ensure_session()
        await self._rate_limit()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'RealEstateEmpire-ForeclosureClient/1.0'
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
                            raise ForeclosureAPIError("Rate limit exceeded")
                    
                    # Handle other HTTP errors
                    if response.status >= 400:
                        error_text = await response.text()
                        logger.error(f"Foreclosure API error {response.status}: {error_text}")
                        if attempt < self.max_retries and response.status >= 500:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                            continue
                        else:
                            raise ForeclosureAPIError(f"HTTP {response.status}: {error_text}")
                    
                    # Parse response
                    try:
                        return await response.json()
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON response: {e}")
                        raise ForeclosureAPIError(f"Invalid JSON response: {e}")
                        
            except aiohttp.ClientError as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    raise ForeclosureAPIError(f"Request failed after {self.max_retries} retries: {e}")
        
        raise ForeclosureAPIError("Max retries exceeded")

    def _normalize_foreclosure_data(self, raw_data: Dict[str, Any]) -> ForeclosureProperty:
        """
        Normalize raw foreclosure data to standard format.
        
        Args:
            raw_data: Raw foreclosure data from API
            
        Returns:
            Normalized ForeclosureProperty object
        """
        try:
            # Extract basic property information
            foreclosure_id = str(raw_data.get('foreclosure_id', raw_data.get('ForeclosureId', '')))
            property_address = raw_data.get('property_address', raw_data.get('PropertyAddress', ''))
            city = raw_data.get('city', raw_data.get('City', ''))
            state = raw_data.get('state', raw_data.get('State', ''))
            zip_code = raw_data.get('zip_code', raw_data.get('ZipCode', ''))
            
            # Extract status
            status_str = raw_data.get('status', raw_data.get('ForeclosureStatus', 'pre_foreclosure'))
            try:
                status = ForeclosureStatus(status_str.lower())
            except ValueError:
                logger.warning(f"Unknown foreclosure status: {status_str}")
                status = ForeclosureStatus.PRE_FORECLOSURE
            
            # Extract auction type
            auction_type = None
            auction_type_str = raw_data.get('auction_type', raw_data.get('AuctionType'))
            if auction_type_str:
                try:
                    auction_type = AuctionType(auction_type_str.lower())
                except ValueError:
                    logger.warning(f"Unknown auction type: {auction_type_str}")
            
            # Parse auction date
            auction_date = None
            auction_date_str = raw_data.get('auction_date', raw_data.get('AuctionDate'))
            if auction_date_str:
                try:
                    auction_date = datetime.fromisoformat(auction_date_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    try:
                        auction_date = datetime.strptime(auction_date_str, '%Y-%m-%d')
                    except ValueError:
                        logger.warning(f"Could not parse auction date: {auction_date_str}")
            
            # Parse filing date
            filing_date = None
            filing_date_str = raw_data.get('filing_date', raw_data.get('FilingDate'))
            if filing_date_str:
                try:
                    filing_date = datetime.fromisoformat(filing_date_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    try:
                        filing_date = datetime.strptime(filing_date_str, '%Y-%m-%d')
                    except ValueError:
                        logger.warning(f"Could not parse filing date: {filing_date_str}")
            
            # Extract financial information
            opening_bid = raw_data.get('opening_bid', raw_data.get('OpeningBid'))
            if opening_bid is not None:
                opening_bid = float(opening_bid)
            
            estimated_value = raw_data.get('estimated_value', raw_data.get('EstimatedValue'))
            if estimated_value is not None:
                estimated_value = float(estimated_value)
            
            loan_balance = raw_data.get('loan_balance', raw_data.get('LoanBalance'))
            if loan_balance is not None:
                loan_balance = float(loan_balance)
            
            default_amount = raw_data.get('default_amount', raw_data.get('DefaultAmount'))
            if default_amount is not None:
                default_amount = float(default_amount)
            
            # Extract property details
            bedrooms = raw_data.get('bedrooms', raw_data.get('Bedrooms'))
            if bedrooms is not None:
                bedrooms = int(bedrooms)
                
            bathrooms = raw_data.get('bathrooms', raw_data.get('Bathrooms'))
            if bathrooms is not None:
                bathrooms = float(bathrooms)
                
            square_feet = raw_data.get('square_feet', raw_data.get('SquareFeet'))
            if square_feet is not None:
                square_feet = int(square_feet)
                
            lot_size = raw_data.get('lot_size', raw_data.get('LotSize'))
            if lot_size is not None:
                lot_size = float(lot_size)
                
            year_built = raw_data.get('year_built', raw_data.get('YearBuilt'))
            if year_built is not None:
                year_built = int(year_built)
            
            # Extract auction and legal information
            auction_time = raw_data.get('auction_time', raw_data.get('AuctionTime'))
            auction_location = raw_data.get('auction_location', raw_data.get('AuctionLocation'))
            trustee_name = raw_data.get('trustee_name', raw_data.get('TrusteeName'))
            trustee_phone = raw_data.get('trustee_phone', raw_data.get('TrusteePhone'))
            lender_name = raw_data.get('lender_name', raw_data.get('LenderName'))
            borrower_name = raw_data.get('borrower_name', raw_data.get('BorrowerName'))
            legal_description = raw_data.get('legal_description', raw_data.get('LegalDescription'))
            case_number = raw_data.get('case_number', raw_data.get('CaseNumber'))
            
            # Extract photos
            photos = []
            if 'photos' in raw_data:
                photos = raw_data['photos']
            elif 'Photos' in raw_data:
                photos = raw_data['Photos']
            
            # Calculate days until auction
            days_until_auction = None
            if auction_date:
                days_until_auction = (auction_date.date() - datetime.now().date()).days
            
            # Extract postponement count
            postponement_count = raw_data.get('postponement_count', raw_data.get('PostponementCount'))
            if postponement_count is not None:
                postponement_count = int(postponement_count)
            
            return ForeclosureProperty(
                foreclosure_id=foreclosure_id,
                property_address=property_address,
                city=city,
                state=state,
                zip_code=zip_code,
                status=status,
                auction_type=auction_type,
                auction_date=auction_date,
                auction_time=auction_time,
                auction_location=auction_location,
                opening_bid=opening_bid,
                estimated_value=estimated_value,
                loan_balance=loan_balance,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                square_feet=square_feet,
                lot_size=lot_size,
                year_built=year_built,
                property_type=raw_data.get('property_type', raw_data.get('PropertyType')),
                default_amount=default_amount,
                filing_date=filing_date,
                trustee_name=trustee_name,
                trustee_phone=trustee_phone,
                lender_name=lender_name,
                borrower_name=borrower_name,
                legal_description=legal_description,
                case_number=case_number,
                photos=photos,
                days_until_auction=days_until_auction,
                postponement_count=postponement_count,
                last_updated=datetime.now(),
                raw_data=raw_data
            )
            
        except Exception as e:
            logger.error(f"Error normalizing foreclosure data: {e}")
            logger.error(f"Raw data: {raw_data}")
            raise ForeclosureAPIError(f"Failed to normalize foreclosure data: {e}")

    async def search_foreclosures(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        status: Optional[ForeclosureStatus] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        auction_date_from: Optional[datetime] = None,
        auction_date_to: Optional[datetime] = None,
        limit: int = 100
    ) -> List[ForeclosureProperty]:
        """
        Search for foreclosure properties based on criteria.
        
        Args:
            city: City name
            state: State abbreviation
            zip_code: ZIP code
            status: Foreclosure status filter
            min_value: Minimum estimated value
            max_value: Maximum estimated value
            auction_date_from: Auction date range start
            auction_date_to: Auction date range end
            limit: Maximum number of results
            
        Returns:
            List of foreclosure properties
        """
        params = {'limit': limit}
        
        if city:
            params['city'] = city
        if state:
            params['state'] = state
        if zip_code:
            params['zip_code'] = zip_code
        if status:
            params['status'] = status.value
        if min_value:
            params['min_value'] = min_value
        if max_value:
            params['max_value'] = max_value
        if auction_date_from:
            params['auction_date_from'] = auction_date_from.isoformat()
        if auction_date_to:
            params['auction_date_to'] = auction_date_to.isoformat()
        
        try:
            response = await self._make_request('GET', '/foreclosures/search', params=params)
            
            properties = []
            for raw_property in response.get('results', []):
                try:
                    normalized_property = self._normalize_foreclosure_data(raw_property)
                    properties.append(normalized_property)
                except Exception as e:
                    logger.error(f"Failed to normalize foreclosure property: {e}")
                    continue
            
            logger.info(f"Retrieved {len(properties)} foreclosure properties")
            return properties
            
        except Exception as e:
            logger.error(f"Failed to search foreclosures: {e}")
            raise

    async def get_upcoming_auctions(
        self,
        days_ahead: int = 30,
        city: Optional[str] = None,
        state: Optional[str] = None
    ) -> List[AuctionInfo]:
        """
        Get upcoming foreclosure auctions.
        
        Args:
            days_ahead: Number of days to look ahead
            city: City filter
            state: State filter
            
        Returns:
            List of upcoming auctions
        """
        end_date = datetime.now() + timedelta(days=days_ahead)
        
        params = {
            'auction_date_from': datetime.now().isoformat(),
            'auction_date_to': end_date.isoformat(),
            'limit': 500
        }
        
        if city:
            params['city'] = city
        if state:
            params['state'] = state
        
        try:
            response = await self._make_request('GET', '/auctions/upcoming', params=params)
            
            auctions = []
            for raw_auction in response.get('auctions', []):
                try:
                    auction = self._normalize_auction_data(raw_auction)
                    auctions.append(auction)
                except Exception as e:
                    logger.error(f"Failed to normalize auction data: {e}")
                    continue
            
            logger.info(f"Retrieved {len(auctions)} upcoming auctions")
            return auctions
            
        except Exception as e:
            logger.error(f"Failed to get upcoming auctions: {e}")
            raise

    def _normalize_auction_data(self, raw_data: Dict[str, Any]) -> AuctionInfo:
        """Normalize raw auction data."""
        try:
            auction_id = str(raw_data.get('auction_id', raw_data.get('AuctionId', '')))
            property_address = raw_data.get('property_address', raw_data.get('PropertyAddress', ''))
            
            # Parse auction date
            auction_date_str = raw_data.get('auction_date', raw_data.get('AuctionDate'))
            auction_date = datetime.fromisoformat(auction_date_str.replace('Z', '+00:00'))
            
            auction_time = raw_data.get('auction_time', raw_data.get('AuctionTime', ''))
            auction_location = raw_data.get('auction_location', raw_data.get('AuctionLocation', ''))
            
            # Parse auction type
            auction_type_str = raw_data.get('auction_type', raw_data.get('AuctionType', 'trustee_sale'))
            auction_type = AuctionType(auction_type_str.lower())
            
            opening_bid = float(raw_data.get('opening_bid', raw_data.get('OpeningBid', 0)))
            
            estimated_value = raw_data.get('estimated_value', raw_data.get('EstimatedValue'))
            if estimated_value is not None:
                estimated_value = float(estimated_value)
            
            deposit_required = raw_data.get('deposit_required', raw_data.get('DepositRequired'))
            if deposit_required is not None:
                deposit_required = float(deposit_required)
            
            registration_required = raw_data.get('registration_required', True)
            if isinstance(registration_required, str):
                registration_required = registration_required.lower() in ('true', 'yes', '1')
            
            return AuctionInfo(
                auction_id=auction_id,
                property_address=property_address,
                auction_date=auction_date,
                auction_time=auction_time,
                auction_location=auction_location,
                auction_type=auction_type,
                opening_bid=opening_bid,
                estimated_value=estimated_value,
                trustee_name=raw_data.get('trustee_name', raw_data.get('TrusteeName')),
                trustee_phone=raw_data.get('trustee_phone', raw_data.get('TrusteePhone')),
                registration_required=registration_required,
                deposit_required=deposit_required,
                terms_of_sale=raw_data.get('terms_of_sale', raw_data.get('TermsOfSale')),
                postponement_history=raw_data.get('postponement_history', [])
            )
            
        except Exception as e:
            logger.error(f"Error normalizing auction data: {e}")
            raise ForeclosureAPIError(f"Failed to normalize auction data: {e}")

    async def get_foreclosure_by_id(self, foreclosure_id: str) -> Optional[ForeclosureProperty]:
        """
        Get a specific foreclosure property by ID.
        
        Args:
            foreclosure_id: Foreclosure ID
            
        Returns:
            ForeclosureProperty object or None if not found
        """
        try:
            response = await self._make_request('GET', f'/foreclosures/{foreclosure_id}')
            
            if response.get('foreclosure'):
                return self._normalize_foreclosure_data(response['foreclosure'])
            else:
                logger.warning(f"Foreclosure {foreclosure_id} not found")
                return None
                
        except ForeclosureAPIError as e:
            if "404" in str(e):
                return None
            raise

    async def track_foreclosure_status(
        self,
        foreclosure_id: str
    ) -> Dict[str, Any]:
        """
        Track the status changes of a foreclosure property.
        
        Args:
            foreclosure_id: Foreclosure ID to track
            
        Returns:
            Status tracking information
        """
        try:
            response = await self._make_request('GET', f'/foreclosures/{foreclosure_id}/status')
            
            return {
                'current_status': response.get('current_status'),
                'status_history': response.get('status_history', []),
                'next_milestone': response.get('next_milestone'),
                'estimated_timeline': response.get('estimated_timeline', {}),
                'risk_factors': response.get('risk_factors', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to track foreclosure status: {e}")
            raise

    async def predict_auction_timeline(
        self,
        foreclosure_id: str
    ) -> Dict[str, Any]:
        """
        Predict auction timeline based on historical data and current status.
        
        Args:
            foreclosure_id: Foreclosure ID
            
        Returns:
            Timeline prediction information
        """
        try:
            response = await self._make_request('GET', f'/foreclosures/{foreclosure_id}/timeline')
            
            return {
                'predicted_auction_date': response.get('predicted_auction_date'),
                'confidence_score': response.get('confidence_score', 0.0),
                'factors_considered': response.get('factors_considered', []),
                'similar_cases': response.get('similar_cases', []),
                'postponement_probability': response.get('postponement_probability', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Failed to predict auction timeline: {e}")
            raise

    async def get_pre_foreclosures(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        days_in_default: Optional[int] = None
    ) -> List[ForeclosureProperty]:
        """
        Get properties in pre-foreclosure status.
        
        Args:
            city: City filter
            state: State filter
            days_in_default: Minimum days in default
            
        Returns:
            List of pre-foreclosure properties
        """
        params = {'status': ForeclosureStatus.PRE_FORECLOSURE.value}
        
        if city:
            params['city'] = city
        if state:
            params['state'] = state
        if days_in_default:
            params['days_in_default'] = days_in_default
        
        try:
            response = await self._make_request('GET', '/foreclosures/pre-foreclosure', params=params)
            
            properties = []
            for raw_property in response.get('results', []):
                try:
                    normalized_property = self._normalize_foreclosure_data(raw_property)
                    properties.append(normalized_property)
                except Exception as e:
                    logger.error(f"Failed to normalize pre-foreclosure property: {e}")
                    continue
            
            logger.info(f"Retrieved {len(properties)} pre-foreclosure properties")
            return properties
            
        except Exception as e:
            logger.error(f"Failed to get pre-foreclosures: {e}")
            raise

    async def get_bank_owned_properties(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> List[ForeclosureProperty]:
        """
        Get bank-owned (REO) properties.
        
        Args:
            city: City filter
            state: State filter
            min_value: Minimum estimated value
            max_value: Maximum estimated value
            
        Returns:
            List of bank-owned properties
        """
        params = {'status': ForeclosureStatus.BANK_OWNED.value}
        
        if city:
            params['city'] = city
        if state:
            params['state'] = state
        if min_value:
            params['min_value'] = min_value
        if max_value:
            params['max_value'] = max_value
        
        try:
            response = await self._make_request('GET', '/foreclosures/bank-owned', params=params)
            
            properties = []
            for raw_property in response.get('results', []):
                try:
                    normalized_property = self._normalize_foreclosure_data(raw_property)
                    properties.append(normalized_property)
                except Exception as e:
                    logger.error(f"Failed to normalize bank-owned property: {e}")
                    continue
            
            logger.info(f"Retrieved {len(properties)} bank-owned properties")
            return properties
            
        except Exception as e:
            logger.error(f"Failed to get bank-owned properties: {e}")
            raise


# Example usage and testing
async def main():
    """Example usage of ForeclosureClient."""
    client = ForeclosureClient(
        api_key="your-api-key",
        base_url="https://api.foreclosure-provider.com/v1"
    )
    
    async with client:
        try:
            # Search for foreclosures
            foreclosures = await client.search_foreclosures(
                city="Austin",
                state="TX",
                status=ForeclosureStatus.PRE_FORECLOSURE,
                limit=10
            )
            
            print(f"Found {len(foreclosures)} foreclosure properties")
            for prop in foreclosures[:3]:
                print(f"- {prop.property_address}, {prop.city} - Status: {prop.status.value}")
                if prop.auction_date:
                    print(f"  Auction Date: {prop.auction_date.strftime('%Y-%m-%d')}")
            
            # Get upcoming auctions
            auctions = await client.get_upcoming_auctions(days_ahead=14, city="Austin", state="TX")
            print(f"Found {len(auctions)} upcoming auctions")
            
            # Get pre-foreclosures
            pre_foreclosures = await client.get_pre_foreclosures(city="Austin", state="TX")
            print(f"Found {len(pre_foreclosures)} pre-foreclosure properties")
            
        except ForeclosureAPIError as e:
            print(f"Foreclosure API Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())