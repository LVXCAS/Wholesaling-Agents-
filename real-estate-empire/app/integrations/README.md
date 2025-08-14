# Data Source Integrations

This module contains integrations with various real estate data sources to support the AI-Powered Real Estate Empire platform.

## Overview

The data source integrations provide unified access to multiple real estate data providers, enabling the platform to:

- Source properties from MLS listings
- Access public records for ownership and tax information
- Track foreclosure properties and auction schedules
- Identify off-market investment opportunities

## Components

### 1. MLS Integration (`mls_client.py`)

**Purpose**: Integrate with Multiple Listing Service (MLS) APIs to access property listings.

**Key Features**:
- Property search with multiple criteria
- Data normalization across different MLS providers
- Incremental sync for updated listings
- Rate limiting and error handling
- Property history tracking

**Main Classes**:
- `MLSClient`: Main client for MLS API interactions
- `MLSProperty`: Normalized property data structure
- `MLSDataNormalizer`: Utility for data standardization

**Usage Example**:
```python
from app.integrations.mls_client import MLSClient

async with MLSClient(api_key="your-key", base_url="https://api.mls.com") as client:
    properties = await client.search_properties(
        city="Austin",
        state="TX",
        min_price=200000,
        max_price=500000
    )
```

### 2. Public Records Integration (`public_records_client.py`)

**Purpose**: Access public records for property ownership, tax records, and transaction history.

**Key Features**:
- Property owner information lookup
- Tax record history and assessment data
- Deed and transaction records
- Contact information enrichment
- Owner validation and verification

**Main Classes**:
- `PublicRecordsClient`: Main client for public records APIs
- `PublicRecord`: Unified record structure
- `OwnerInfo`: Property owner information
- `PropertyTaxRecord`: Tax assessment data
- `DeedRecord`: Property transaction records

**Usage Example**:
```python
from app.integrations.public_records_client import PublicRecordsClient

async with PublicRecordsClient(api_key="your-key", base_url="https://api.records.com") as client:
    records = await client.search_by_address(
        address="123 Main St",
        city="Austin",
        state="TX"
    )
```

### 3. Foreclosure Data Integration (`foreclosure_client.py`)

**Purpose**: Track properties in foreclosure and auction schedules.

**Key Features**:
- Foreclosure property search and tracking
- Auction schedule and information
- Status tracking and timeline prediction
- Pre-foreclosure and bank-owned property identification
- Distressed property opportunity detection

**Main Classes**:
- `ForeclosureClient`: Main client for foreclosure data APIs
- `ForeclosureProperty`: Foreclosure property data
- `AuctionInfo`: Auction details and scheduling
- `ForeclosureStatus`: Status enumeration
- `AuctionType`: Auction type classification

**Usage Example**:
```python
from app.integrations.foreclosure_client import ForeclosureClient, ForeclosureStatus

async with ForeclosureClient(api_key="your-key", base_url="https://api.foreclosure.com") as client:
    foreclosures = await client.search_foreclosures(
        city="Austin",
        state="TX",
        status=ForeclosureStatus.PRE_FORECLOSURE
    )
```

### 4. Off-Market Property Finder (`off_market_finder.py`)

**Purpose**: Identify off-market investment opportunities using multiple data sources and algorithms.

**Key Features**:
- Multi-source opportunity identification
- Owner motivation scoring
- Property condition estimation
- Contact information research
- Opportunity scoring and ranking
- Distressed property detection

**Main Classes**:
- `OffMarketPropertyFinder`: Main finder engine
- `OffMarketOpportunity`: Investment opportunity data
- `OwnerResearch`: Owner contact and research data
- `MotivationIndicators`: Owner motivation analysis
- `PropertyConditionEstimate`: Property condition assessment

**Opportunity Types**:
- High equity properties
- Absentee owners
- Tax delinquent properties
- Vacant properties
- Distressed owners
- Estate sales
- Divorce situations
- Financial distress
- Tired landlords
- Code violations

**Usage Example**:
```python
from app.integrations.off_market_finder import OffMarketPropertyFinder, OpportunityType

finder = OffMarketPropertyFinder(
    mls_client=mls_client,
    public_records_client=records_client,
    foreclosure_client=foreclosure_client
)

opportunities = await finder.find_opportunities(
    city="Austin",
    state="TX",
    min_equity=50000,
    opportunity_types=[
        OpportunityType.HIGH_EQUITY,
        OpportunityType.ABSENTEE_OWNER,
        OpportunityType.TAX_DELINQUENT
    ]
)
```

## Common Features

All integration clients include:

### Error Handling
- Comprehensive exception handling
- Retry logic with exponential backoff
- Rate limiting compliance
- Timeout management

### Data Normalization
- Standardized data structures
- Field mapping and validation
- Type conversion and cleaning
- Missing data handling

### Async Support
- Full async/await support
- Context manager integration
- Concurrent request handling
- Session management

### Testing
- Comprehensive unit tests
- Integration test framework
- Mock data and fixtures
- Error scenario testing

## Configuration

Each client requires configuration for:

- **API Key**: Authentication credentials
- **Base URL**: API endpoint URL
- **Rate Limits**: Requests per minute limits
- **Retry Settings**: Max retries and delay configuration
- **Timeout Settings**: Request timeout values

## Requirements Mapping

This implementation addresses the following requirements from the specification:

- **Requirement 1.1**: Automated deal sourcing from MLS listings, off-market properties, foreclosures, and public records
- **Requirement 1.2**: User-defined investment criteria filtering
- **Requirement 1.3**: Real-time notifications and dashboard updates
- **Requirement 1.5**: Owner contact information gathering and verification

## Error Handling

All clients implement robust error handling:

```python
try:
    properties = await client.search_properties(...)
except MLSAPIError as e:
    logger.error(f"MLS API error: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

## Rate Limiting

Built-in rate limiting prevents API quota exhaustion:

```python
client = MLSClient(
    api_key="your-key",
    base_url="https://api.mls.com",
    rate_limit_per_minute=60  # Configurable rate limit
)
```

## Data Validation

All data is validated and normalized:

```python
# Raw API data is automatically normalized
raw_data = {"ListPrice": "450000", "BedroomsTotal": "3"}
normalized = client._normalize_property_data(raw_data)
# Results in clean, typed data
assert normalized.price == 450000.0
assert normalized.bedrooms == 3
```

## Testing

Run all integration tests:

```bash
# Run all integration tests
python -m pytest tests/test_*_integration.py -v

# Run specific integration tests
python -m pytest tests/test_mls_integration.py -v
python -m pytest tests/test_public_records_integration.py -v
python -m pytest tests/test_foreclosure_integration.py -v
python -m pytest tests/test_off_market_finder.py -v
```

## Future Enhancements

Potential improvements for future versions:

1. **Additional Data Sources**: Integration with more MLS providers, county records, etc.
2. **Machine Learning**: Enhanced property condition estimation using ML models
3. **Real-time Updates**: WebSocket connections for live data feeds
4. **Caching**: Redis integration for improved performance
5. **Batch Processing**: Bulk data import and processing capabilities
6. **Data Quality**: Enhanced validation and data quality scoring
7. **API Versioning**: Support for multiple API versions
8. **Monitoring**: Detailed metrics and monitoring integration

## Dependencies

Key dependencies used:

- `aiohttp`: Async HTTP client
- `asyncio`: Async programming support
- `dataclasses`: Data structure definitions
- `enum`: Enumeration support
- `datetime`: Date/time handling
- `logging`: Comprehensive logging
- `json`: JSON data processing
- `re`: Regular expression support
- `time`: Time-based operations

## Performance Considerations

- **Async Operations**: All I/O operations are async for better performance
- **Connection Pooling**: HTTP session reuse for efficiency
- **Rate Limiting**: Prevents API throttling and quota exhaustion
- **Data Caching**: Reduces redundant API calls
- **Batch Processing**: Efficient handling of large datasets
- **Memory Management**: Proper cleanup and resource management

This integration layer provides a solid foundation for the real estate data sourcing requirements of the AI-Powered Real Estate Empire platform.