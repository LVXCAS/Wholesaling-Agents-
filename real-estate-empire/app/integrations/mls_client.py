"""
MLS (Multiple Listing Service) API client for real estate data integration.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
import json
from dataclasses import dataclass, asdict
from enum import Enum
import time

logger = logging.getLogger(__name__)


class MLSPropertyStatus(Enum):
    """MLS property status enumeration."""
    ACTIVE = "Active"
    PENDING = "Pending"
    SOLD = "Sold"
    WITHDRAWN = "Withdrawn"
    EXPIRED = "Expired"


@dataclass
class MLSProperty:
    """Normalized MLS property data structure."""
    mls_id: str
    address: str
    city: str
    state: str
    zip_code: str
    price: float
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    property_type: Optional[str] = None
    status: Optional[str] = None
    days_on_market: Optional[int] = None
    listing_date: Optional[datetime] = None
    photos: Optional[List[str]] = None
    description: Optional[str] = None
    agent_name: Optional[str] = None
    agent_phone: Optional[str] = None
    agent_email: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    last_updated: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        if data.get('listing_date'):
            data['listing_date'] = data['listing_date'].isoformat()
        if data.get('last_updated'):
            data['last_updated'] = data['last_updated'].isoformat()
        return data


class MLSAPIError(Exception):
    """Custom exception for MLS API errors."""
    pass


class MLSRateLimitError(MLSAPIError):
    """Exception for rate limit errors."""
    pass


class MLSClient:
    """
    MLS API client with data normalization and error handling.
    
    This client provides a unified interface to various MLS data sources
    with built-in retry logic, rate limiting, and data normalization.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_per_minute: int = 60
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
            MLSAPIError: For API errors
            MLSRateLimitError: For rate limit errors
        """
        await self._ensure_session()
        await self._rate_limit()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'RealEstateEmpire-MLSClient/1.0'
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
                            raise MLSRateLimitError("Rate limit exceeded")
                    
                    # Handle other HTTP errors
                    if response.status >= 400:
                        error_text = await response.text()
                        logger.error(f"MLS API error {response.status}: {error_text}")
                        if attempt < self.max_retries and response.status >= 500:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                            continue
                        else:
                            raise MLSAPIError(f"HTTP {response.status}: {error_text}")
                    
                    # Parse response
                    try:
                        return await response.json()
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON response: {e}")
                        raise MLSAPIError(f"Invalid JSON response: {e}")
                        
            except aiohttp.ClientError as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    raise MLSAPIError(f"Request failed after {self.max_retries} retries: {e}")
        
        raise MLSAPIError("Max retries exceeded")

    def _normalize_property_data(self, raw_data: Dict[str, Any]) -> MLSProperty:
        """
        Normalize raw MLS data to standard format.
        
        Args:
            raw_data: Raw property data from MLS API
            
        Returns:
            Normalized MLSProperty object
        """
        try:
            # Extract basic property information
            mls_id = str(raw_data.get('ListingId', raw_data.get('MlsNumber', '')))
            address = raw_data.get('UnparsedAddress', raw_data.get('StreetName', ''))
            city = raw_data.get('City', '')
            state = raw_data.get('StateOrProvince', '')
            zip_code = raw_data.get('PostalCode', '')
            
            # Extract price information
            price = float(raw_data.get('ListPrice', raw_data.get('CurrentPrice', 0)))
            
            # Extract property details
            bedrooms = raw_data.get('BedroomsTotal')
            if bedrooms is not None:
                bedrooms = int(bedrooms)
                
            bathrooms = raw_data.get('BathroomsTotal')
            if bathrooms is not None:
                bathrooms = float(bathrooms)
                
            square_feet = raw_data.get('LivingArea')
            if square_feet is not None:
                square_feet = int(square_feet)
                
            lot_size = raw_data.get('LotSizeAcres')
            if lot_size is not None:
                lot_size = float(lot_size)
                
            year_built = raw_data.get('YearBuilt')
            if year_built is not None:
                year_built = int(year_built)
            
            # Extract status and timing
            status = raw_data.get('StandardStatus', raw_data.get('MlsStatus'))
            days_on_market = raw_data.get('DaysOnMarket')
            if days_on_market is not None:
                days_on_market = int(days_on_market)
            
            # Parse listing date
            listing_date = None
            listing_date_str = raw_data.get('ListingContractDate', raw_data.get('OnMarketDate'))
            if listing_date_str:
                try:
                    listing_date = datetime.fromisoformat(listing_date_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    logger.warning(f"Could not parse listing date: {listing_date_str}")
            
            # Extract photos
            photos = []
            if 'Media' in raw_data:
                for media in raw_data['Media']:
                    if media.get('MediaCategory') == 'Photo':
                        photos.append(media.get('MediaURL', ''))
            elif 'Photos' in raw_data:
                photos = raw_data['Photos']
            
            # Extract agent information
            agent_name = raw_data.get('ListAgentFullName', raw_data.get('ListingAgentName'))
            agent_phone = raw_data.get('ListAgentDirectPhone', raw_data.get('ListingAgentPhone'))
            agent_email = raw_data.get('ListAgentEmail', raw_data.get('ListingAgentEmail'))
            
            return MLSProperty(
                mls_id=mls_id,
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                price=price,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                square_feet=square_feet,
                lot_size=lot_size,
                year_built=year_built,
                property_type=raw_data.get('PropertyType'),
                status=status,
                days_on_market=days_on_market,
                listing_date=listing_date,
                photos=photos,
                description=raw_data.get('PublicRemarks', raw_data.get('Description')),
                agent_name=agent_name,
                agent_phone=agent_phone,
                agent_email=agent_email,
                raw_data=raw_data,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error normalizing property data: {e}")
            logger.error(f"Raw data: {raw_data}")
            raise MLSAPIError(f"Failed to normalize property data: {e}")

    async def search_properties(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        property_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[MLSProperty]:
        """
        Search for properties based on criteria.
        
        Args:
            city: City name
            state: State abbreviation
            min_price: Minimum price
            max_price: Maximum price
            property_type: Property type filter
            status: Property status filter
            limit: Maximum number of results
            
        Returns:
            List of normalized MLSProperty objects
        """
        params = {'limit': limit}
        
        if city:
            params['city'] = city
        if state:
            params['state'] = state
        if min_price:
            params['min_price'] = min_price
        if max_price:
            params['max_price'] = max_price
        if property_type:
            params['property_type'] = property_type
        if status:
            params['status'] = status
        
        try:
            response = await self._make_request('GET', '/properties/search', params=params)
            
            properties = []
            for raw_property in response.get('results', []):
                try:
                    normalized_property = self._normalize_property_data(raw_property)
                    properties.append(normalized_property)
                except Exception as e:
                    logger.error(f"Failed to normalize property {raw_property.get('ListingId', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(properties)} properties from MLS")
            return properties
            
        except Exception as e:
            logger.error(f"Failed to search properties: {e}")
            raise

    async def get_property_by_id(self, mls_id: str) -> Optional[MLSProperty]:
        """
        Get a specific property by MLS ID.
        
        Args:
            mls_id: MLS listing ID
            
        Returns:
            MLSProperty object or None if not found
        """
        try:
            response = await self._make_request('GET', f'/properties/{mls_id}')
            
            if response.get('property'):
                return self._normalize_property_data(response['property'])
            else:
                logger.warning(f"Property {mls_id} not found")
                return None
                
        except MLSAPIError as e:
            if "404" in str(e):
                return None
            raise

    async def get_recent_listings(
        self,
        days: int = 7,
        city: Optional[str] = None,
        state: Optional[str] = None
    ) -> List[MLSProperty]:
        """
        Get recently listed properties.
        
        Args:
            days: Number of days to look back
            city: City filter
            state: State filter
            
        Returns:
            List of recently listed properties
        """
        since_date = datetime.now() - timedelta(days=days)
        
        params = {
            'since_date': since_date.isoformat(),
            'limit': 500
        }
        
        if city:
            params['city'] = city
        if state:
            params['state'] = state
        
        try:
            response = await self._make_request('GET', '/properties/recent', params=params)
            
            properties = []
            for raw_property in response.get('results', []):
                try:
                    normalized_property = self._normalize_property_data(raw_property)
                    properties.append(normalized_property)
                except Exception as e:
                    logger.error(f"Failed to normalize recent property: {e}")
                    continue
            
            logger.info(f"Retrieved {len(properties)} recent listings")
            return properties
            
        except Exception as e:
            logger.error(f"Failed to get recent listings: {e}")
            raise

    async def get_property_history(self, mls_id: str) -> List[Dict[str, Any]]:
        """
        Get price and status history for a property.
        
        Args:
            mls_id: MLS listing ID
            
        Returns:
            List of historical records
        """
        try:
            response = await self._make_request('GET', f'/properties/{mls_id}/history')
            return response.get('history', [])
            
        except Exception as e:
            logger.error(f"Failed to get property history for {mls_id}: {e}")
            raise

    async def sync_incremental(
        self,
        last_sync_time: datetime,
        callback: Optional[callable] = None
    ) -> List[MLSProperty]:
        """
        Perform incremental sync of properties updated since last sync.
        
        Args:
            last_sync_time: Timestamp of last successful sync
            callback: Optional callback function for progress updates
            
        Returns:
            List of updated properties
        """
        try:
            params = {
                'modified_since': last_sync_time.isoformat(),
                'limit': 1000
            }
            
            response = await self._make_request('GET', '/properties/modified', params=params)
            
            properties = []
            total_count = response.get('total_count', 0)
            
            for i, raw_property in enumerate(response.get('results', [])):
                try:
                    normalized_property = self._normalize_property_data(raw_property)
                    properties.append(normalized_property)
                    
                    if callback and i % 100 == 0:
                        await callback(i, total_count)
                        
                except Exception as e:
                    logger.error(f"Failed to normalize property during sync: {e}")
                    continue
            
            logger.info(f"Incremental sync retrieved {len(properties)} updated properties")
            return properties
            
        except Exception as e:
            logger.error(f"Failed to perform incremental sync: {e}")
            raise


class MLSDataNormalizer:
    """
    Utility class for normalizing MLS data from different sources.
    """
    
    @staticmethod
    def normalize_property_type(raw_type: str) -> str:
        """Normalize property type to standard values."""
        if not raw_type:
            return "Unknown"
        
        raw_type = raw_type.lower().strip()
        
        type_mapping = {
            'single family': 'Single Family',
            'single-family': 'Single Family',
            'sfr': 'Single Family',
            'condo': 'Condominium',
            'condominium': 'Condominium',
            'townhouse': 'Townhouse',
            'townhome': 'Townhouse',
            'multi-family': 'Multi-Family',
            'multifamily': 'Multi-Family',
            'duplex': 'Multi-Family',
            'triplex': 'Multi-Family',
            'fourplex': 'Multi-Family',
            'apartment': 'Multi-Family',
            'land': 'Land',
            'vacant land': 'Land',
            'commercial': 'Commercial',
            'office': 'Commercial',
            'retail': 'Commercial',
            'industrial': 'Commercial'
        }
        
        return type_mapping.get(raw_type, raw_type.title())
    
    @staticmethod
    def normalize_status(raw_status: str) -> str:
        """Normalize property status to standard values."""
        if not raw_status:
            return "Unknown"
        
        raw_status = raw_status.lower().strip()
        
        status_mapping = {
            'active': 'Active',
            'for sale': 'Active',
            'pending': 'Pending',
            'under contract': 'Pending',
            'sold': 'Sold',
            'closed': 'Sold',
            'withdrawn': 'Withdrawn',
            'cancelled': 'Withdrawn',
            'expired': 'Expired',
            'off market': 'Withdrawn'
        }
        
        return status_mapping.get(raw_status, raw_status.title())


# Example usage and testing
async def main():
    """Example usage of MLSClient."""
    # This would typically use real API credentials
    client = MLSClient(
        api_key="your-api-key",
        base_url="https://api.mls-provider.com/v1"
    )
    
    async with client:
        try:
            # Search for properties
            properties = await client.search_properties(
                city="Austin",
                state="TX",
                min_price=200000,
                max_price=500000,
                limit=10
            )
            
            print(f"Found {len(properties)} properties")
            for prop in properties[:3]:
                print(f"- {prop.address}, {prop.city} - ${prop.price:,.0f}")
            
            # Get recent listings
            recent = await client.get_recent_listings(days=3, city="Austin", state="TX")
            print(f"Found {len(recent)} recent listings")
            
        except MLSAPIError as e:
            print(f"MLS API Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())