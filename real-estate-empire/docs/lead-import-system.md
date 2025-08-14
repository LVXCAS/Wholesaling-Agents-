# Lead Import System

The Lead Import System allows users to import property leads from CSV files with intelligent column mapping, data validation, and duplicate detection.

## Features

### 1. CSV Analysis
- Automatic header detection
- Sample data preview
- Intelligent column mapping suggestions
- Data type validation

### 2. Column Mapping Interface
- Visual mapping of CSV columns to system fields
- Required field validation
- Support for both property and lead data
- Flexible mapping configuration

### 3. Data Validation and Error Handling
- Required field validation
- Data type conversion with error handling
- Email and phone number validation
- Property type and source normalization

### 4. Duplicate Detection
- Property duplicate detection based on address
- Lead duplicate detection based on email/phone
- Configurable skip duplicates option
- Detailed duplicate reporting

### 5. Import Options
- Multiple lead source options
- Skip duplicates configuration
- Batch processing with progress tracking
- Comprehensive error reporting

## API Endpoints

### POST /api/lead-import/analyze
Analyze CSV content and suggest column mappings.

**Request:**
```json
{
  "csv_content": "Address,City,State,ZIP,Owner Name,Phone,Email,Price\n123 Main St,Anytown,CA,12345,John Doe,(555) 123-4567,john@example.com,$250000"
}
```

**Response:**
```json
{
  "headers": ["Address", "City", "State", "ZIP", "Owner Name", "Phone", "Email", "Price"],
  "sample_rows": [["123 Main St", "Anytown", "CA", "12345", "John Doe", "(555) 123-4567", "john@example.com", "$250000"]],
  "total_rows": 2,
  "suggested_mapping": {
    "address": "Address",
    "city": "City",
    "state": "State",
    "zip_code": "ZIP",
    "owner_name": "Owner Name",
    "owner_phone": "Phone",
    "owner_email": "Email",
    "asking_price": "Price"
  },
  "analysis_status": "success"
}
```

### POST /api/lead-import/analyze-file
Analyze uploaded CSV file.

**Request:** Multipart form data with CSV file

### POST /api/lead-import/import
Import leads from CSV content.

**Request:**
```json
{
  "csv_content": "...",
  "column_mapping": {
    "address": "Address",
    "city": "City",
    "state": "State",
    "zip_code": "ZIP",
    "owner_name": "Owner Name",
    "owner_phone": "Phone",
    "owner_email": "Email",
    "asking_price": "Price"
  },
  "default_source": "other",
  "skip_duplicates": true
}
```

**Response:**
```json
{
  "total_rows": 1,
  "successful_imports": 1,
  "failed_imports": 0,
  "duplicates_found": 0,
  "errors": [],
  "status": "completed",
  "import_id": "uuid",
  "created_leads": ["lead-uuid"],
  "created_properties": ["property-uuid"]
}
```

### POST /api/lead-import/import-file
Import leads from uploaded CSV file.

**Request:** Multipart form data with CSV file and mapping configuration

### GET /api/lead-import/mapping-template
Get column mapping template and field descriptions.

### GET /api/lead-import/sources
Get available lead source options.

## Supported Fields

### Property Fields (Required)
- **address**: Street address of the property
- **city**: City where property is located
- **state**: State/province where property is located
- **zip_code**: ZIP/postal code

### Property Fields (Optional)
- **property_type**: Type of property (single_family, multi_family, etc.)
- **bedrooms**: Number of bedrooms
- **bathrooms**: Number of bathrooms
- **square_feet**: Square footage of the property
- **year_built**: Year the property was built

### Lead Fields (Optional)
- **owner_name**: Name of the property owner
- **owner_email**: Email address of the owner
- **owner_phone**: Phone number of the owner
- **owner_address**: Mailing address of the owner
- **source**: Source of the lead
- **asking_price**: Asking price for the property
- **mortgage_balance**: Outstanding mortgage balance
- **equity_estimate**: Estimated equity in the property
- **preferred_contact_method**: Preferred way to contact owner
- **condition_notes**: Notes about property condition
- **notes**: General notes about the lead
- **tags**: Comma-separated tags for the lead
- **motivation_factors**: Comma-separated motivation factors

## Data Normalization

### Phone Numbers
- Automatically formatted as (XXX) XXX-XXXX
- Handles various input formats
- Removes non-digit characters

### Property Types
- Normalizes common variations (e.g., "Single Family" → "single_family")
- Supports abbreviations (e.g., "SFH" → "single_family")
- Defaults to "single_family" for unknown types

### Lead Sources
- Maps common source names to enum values
- Supports various naming conventions
- Defaults to "other" for unknown sources

### Email Addresses
- Basic email validation
- Converts to lowercase
- Validates format with regex

## Error Handling

The system provides comprehensive error handling with detailed error messages:

- **Validation Errors**: Missing required fields, invalid data types
- **Duplicate Detection**: Identifies existing properties and leads
- **Data Conversion Errors**: Invalid numbers, dates, or formats
- **File Processing Errors**: Invalid CSV format, encoding issues

## Usage Examples

### Basic CSV Import
```csv
Address,City,State,ZIP,Owner Name,Phone,Email,Price
123 Main St,Anytown,CA,12345,John Doe,(555) 123-4567,john@example.com,$250000
456 Oak Ave,Somewhere,TX,67890,Jane Smith,555-987-6543,jane@example.com,$180000
```

### Advanced CSV with Additional Fields
```csv
Property Address,City,State,ZIP Code,Owner Name,Phone Number,Email,List Price,Property Type,Bedrooms,Bathrooms,Square Feet,Notes
123 Main St,Anytown,CA,12345,John Doe,(555) 123-4567,john@example.com,$250000,Single Family,3,2,1500,Needs minor repairs
456 Oak Ave,Somewhere,TX,67890,Jane Smith,555-987-6543,jane@example.com,$180000,Condo,2,2,1200,Move-in ready
```

## Frontend Interface

The system includes a user-friendly web interface (`lead-import.html`) with:

1. **File Upload**: Drag-and-drop or file browser
2. **Column Mapping**: Visual mapping interface with suggestions
3. **Import Options**: Source selection and duplicate handling
4. **Progress Tracking**: Real-time import progress
5. **Results Summary**: Success/failure statistics and error details

## Testing

The system includes comprehensive unit tests:

- **Service Tests**: `tests/test_lead_import_service.py`
- **API Tests**: `tests/test_lead_import_api.py`

Run tests with:
```bash
python -m pytest tests/test_lead_import_service.py tests/test_lead_import_api.py -v
```

## Dependencies

- **python-multipart**: For file upload handling
- **pandas**: For CSV processing (optional, using built-in csv module)
- **sqlalchemy**: For database operations
- **fastapi**: For API endpoints
- **pydantic**: For data validation

## Security Considerations

- File type validation (CSV only)
- File size limits (configurable)
- Input sanitization and validation
- SQL injection prevention through ORM
- Error message sanitization to prevent information disclosure