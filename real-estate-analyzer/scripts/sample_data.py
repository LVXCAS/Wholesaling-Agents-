import sys
import os
from typing import List, Dict, Any

# Add project root to sys.path to allow importing app modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

try:
    from app.core.database import get_db, SessionLocal # SessionLocal for creating a session
    from app.services.property_service import PropertyService
    from app.models.property import PropertyCreate, PropertyTypeEnum # Import Enum if used in data
except ImportError as e:
    print(f"Error importing app modules: {e}")
    print("Please ensure you are running this script from the project root (real-estate-analyzer)")
    print("or that the project root is in your PYTHONPATH.")
    sys.exit(1)

# More diverse sample properties
SAMPLE_PROPERTIES_DATA: List[Dict[str, Any]] = [
    {
        "address": "101 Python Pl", "city": "Devtown", "state": "CA", "zip_code": "90210",
        "property_type": PropertyTypeEnum.SINGLE_FAMILY, "square_feet": 2200, "bedrooms": 4, "bathrooms": 3.0,
        "year_built": 2005, "current_value": 750000.0, "notes": "Modern SFH with pool"
    },
    {
        "address": "202 Java Junction", "city": "Codeville", "state": "NY", "zip_code": "10001",
        "property_type": PropertyTypeEnum.MULTI_FAMILY, "square_feet": 3500, "bedrooms": 6, "bathrooms": 4.0,
        "year_built": 1990, "current_value": 1200000.0, "notes": "Duplex, good rental income"
    },
    {
        "address": "303 SQL Street", "city": "Data City", "state": "TX", "zip_code": "75001",
        "property_type": PropertyTypeEnum.CONDO, "square_feet": 950, "bedrooms": 1, "bathrooms": 1.0,
        "year_built": 2015, "current_value": 320000.0, "notes": "Downtown condo, great views"
    },
    {
        "address": "404 HTML Heights", "city": "Webbington", "state": "FL", "zip_code": "33101",
        "property_type": PropertyTypeEnum.TOWNHOUSE, "square_feet": 1600, "bedrooms": 3, "bathrooms": 2.5,
        "year_built": 2010, "current_value": 450000.0, "notes": "Gated community"
    },
    {
        "address": "505 CSS Corner", "city": "Stylish Springs", "state": "NV", "zip_code": "89101", # Matches CLI sample city/state
        "property_type": PropertyTypeEnum.SINGLE_FAMILY, "square_feet": 1800, "bedrooms": 3, "bathrooms": 2.0,
        "year_built": 1998, "current_value": 380000.0, "notes": "Recently renovated kitchen"
    }
]

def load_all_sample_data():
    print("Starting to load sample properties into the database...")

    db: SessionLocal = next(get_db()) # Get a DB session
    property_service = PropertyService(db)

    loaded_count = 0
    skipped_count = 0

    for prop_data in SAMPLE_PROPERTIES_DATA:
        try:
            # Ensure all required fields for PropertyCreate are present or have defaults
            # The current PropertyCreate model makes many fields optional.
            property_create_obj = PropertyCreate(**prop_data)
            created_property = property_service.create_property(property_create_obj)
            print(f"Successfully loaded: {created_property.address} (ID: {created_property.id})")
            loaded_count += 1
        except Exception as e:
            print(f"Could not load property '{prop_data.get('address', 'Unknown Address')}': {e}")
            skipped_count += 1

    print(f"\n--- Load Summary ---")
    print(f"Successfully loaded properties: {loaded_count}")
    print(f"Skipped properties: {skipped_count}")

    db.close() # Close the session

if __name__ == "__main__":
    # This allows the script to be run directly: python scripts/sample_data.py
    print("This script will load a defined set of sample properties into the database.")
    # confirmation = input("Are you sure you want to proceed? (yes/no): ")
    # if confirmation.lower() == 'yes':
    #     load_all_sample_data()
    # else:
    #     print("Operation cancelled by user.")
    # For automated flow, run directly without input confirmation for now
    load_all_sample_data()
