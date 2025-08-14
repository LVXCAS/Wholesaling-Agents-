# Real Estate Empire - Property Analysis API

This API provides comprehensive property analysis and investment evaluation capabilities for real estate investors.

## Overview

The API is built with FastAPI and provides three main categories of endpoints:

1. **Property Analysis** - CRUD operations and financial analysis for properties
2. **Strategy Analysis** - Investment strategy evaluation (flip, rental, wholesale, BRRRR)
3. **Data Export** - Export property data and analysis results in various formats

## API Endpoints

### Property Analysis (`/api/v1/properties`)

#### Basic CRUD Operations
- `POST /` - Create a new property
- `GET /{property_id}` - Get property by ID
- `PUT /{property_id}` - Update property information
- `GET /` - List properties with optional filtering
- `DELETE /{property_id}` - Delete property

#### Analysis Operations
- `POST /{property_id}/analyze` - Perform comprehensive financial analysis
- `GET /{property_id}/comparables` - Get comparable properties for valuation
- `POST /{property_id}/repair-estimate` - Estimate repair costs using AI
- `GET /{property_id}/analyses` - Get historical analyses for a property

### Strategy Analysis (`/api/v1/strategies`)

#### Investment Strategy Endpoints
- `POST /{property_id}/flip` - Analyze flip investment strategy
- `POST /{property_id}/rental` - Analyze rental investment strategy
- `POST /{property_id}/wholesale` - Analyze wholesale investment strategy
- `POST /{property_id}/brrrr` - Analyze BRRRR investment strategy
- `POST /{property_id}/compare-strategies` - Compare multiple strategies

### Data Export (`/api/v1/export`)

#### Single Property Export
- `GET /{property_id}/pdf` - Export property report as PDF
- `GET /{property_id}/csv` - Export property data as CSV
- `GET /{property_id}/json` - Export property data as JSON

#### Bulk Export
- `GET /bulk/csv` - Export multiple properties as CSV
- `GET /bulk/json` - Export multiple properties as JSON

## Running the API

### Development
```bash
cd real-estate-empire
python -m uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
cd real-estate-empire
python -m pytest tests/test_property_analysis_api.py -v
python -m pytest tests/test_strategy_analysis_api.py -v
python -m pytest tests/test_data_export_api.py -v
```

## API Documentation

Once the API is running, you can access:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health

## Example Usage

### Create a Property
```bash
curl -X POST "http://localhost:8000/api/v1/properties/" \
  -H "Content-Type: application/json" \
  -d '{
    "address": "123 Main Street",
    "city": "Anytown",
    "state": "CA",
    "zip_code": "12345",
    "property_type": "single_family",
    "bedrooms": 3,
    "bathrooms": 2.0,
    "square_feet": 1500,
    "listing_price": 300000
  }'
```

### Analyze Property
```bash
curl -X POST "http://localhost:8000/api/v1/properties/{property_id}/analyze?analysis_type=comprehensive"
```

### Compare Investment Strategies
```bash
curl -X POST "http://localhost:8000/api/v1/strategies/{property_id}/compare-strategies"
```

### Export Property Data
```bash
curl "http://localhost:8000/api/v1/export/{property_id}/json?include_analysis=true"
```

## Features Implemented

### Task 3.1: Property Analysis Endpoints ✅
- ✅ Property creation/update endpoints
- ✅ Financial analysis endpoint
- ✅ Comparable analysis endpoint  
- ✅ Repair estimation endpoint
- ✅ API tests for all endpoints

### Task 3.2: Strategy Analysis Endpoints ✅
- ✅ Flip strategy analysis endpoint
- ✅ Rental strategy analysis endpoint
- ✅ Wholesale strategy analysis endpoint
- ✅ BRRRR strategy analysis endpoint
- ✅ API tests for strategy endpoints

### Task 3.3: Data Export Endpoints ✅
- ✅ PDF report generation
- ✅ CSV export functionality
- ✅ JSON data export
- ✅ API tests for export endpoints

## Requirements Satisfied

This implementation satisfies the following requirements from the specification:

- **Requirement 2.1**: Property financial analysis with key metrics
- **Requirement 2.2**: Comparable property analysis for valuation
- **Requirement 2.3**: Repair cost estimation using AI
- **Requirement 2.4**: Multiple investment strategy analysis
- **Requirement 2.5**: Market rent estimation for rental analysis
- **Requirement 2.6**: Confidence scoring for all estimates
- **Requirement 7.1**: Customizable analytics and reporting
- **Requirement 7.2**: Detailed performance reports
- **Requirement 7.5**: Data export capabilities

## Architecture

The API follows a clean architecture pattern:

```
app/api/
├── main.py              # FastAPI application setup
├── routers/
│   ├── property_analysis.py    # Property CRUD and analysis endpoints
│   ├── strategy_analysis.py    # Investment strategy endpoints
│   └── data_export.py          # Data export endpoints
└── README.md           # This documentation

tests/
├── test_property_analysis_api.py
├── test_strategy_analysis_api.py
└── test_data_export_api.py
```

The API integrates with:
- **Database Layer**: SQLAlchemy models for data persistence
- **Analysis Engine**: Analyst agent for property analysis
- **Export Services**: PDF, CSV, and JSON export functionality
- **Validation**: Pydantic models for request/response validation

## Next Steps

To fully integrate with the agentic system:

1. **Agent Integration**: Complete integration with the analyst agent tools
2. **Authentication**: Add user authentication and authorization
3. **Rate Limiting**: Implement API rate limiting
4. **Caching**: Add Redis caching for expensive operations
5. **Monitoring**: Add logging and monitoring capabilities
6. **Documentation**: Expand API documentation with more examples