import pytest
from uuid import UUID
from datetime import datetime

# Need to adjust sys.path for tests to find the 'app' module
import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from app.models.property import PropertyCreate, PropertyTypeEnum, Property # Added Property for testing response model

def test_property_create_minimal():
    data = {"address": "123 Test St"}
    prop = PropertyCreate(**data)
    assert prop.address == "123 Test St"
    assert prop.city == "" # Default value
    assert prop.property_type == PropertyTypeEnum.SINGLE_FAMILY # Default value

def test_property_create_full():
    now = datetime.utcnow()
    data = {
        "address": "456 Full Ave",
        "city": "Testville",
        "state": "TS",
        "zip_code": "12345",
        "property_type": PropertyTypeEnum.CONDO,
        "square_feet": 1200,
        "bedrooms": 2,
        "bathrooms": 1.5,
        "year_built": 2000,
        "lot_size": 0.05,
        "current_value": 300000.00,
        "last_sale_price": 250000.00,
        "last_sale_date": now,
        "estimated_rent": 2000.00,
        "repair_cost": 5000.00,
        "arv": 320000.00,
        "notes": "A test property",
        "data_source": "test_data"
    }
    prop = PropertyCreate(**data)
    assert prop.address == "456 Full Ave"
    assert prop.city == "Testville"
    assert prop.property_type == PropertyTypeEnum.CONDO
    assert prop.square_feet == 1200
    assert prop.last_sale_date == now
    assert prop.notes == "A test property"

def test_property_create_with_enum_string():
    # Pydantic should coerce valid strings to Enum members
    data = {"address": "789 Enum St", "property_type": "multi_family"}
    prop = PropertyCreate(**data)
    assert prop.property_type == PropertyTypeEnum.MULTI_FAMILY

def test_property_model_from_orm():
    # Test creating the response model (Property) from a dict (simulating ORM object)
    now = datetime.utcnow()
    prop_data_from_db = {
        "id": UUID("a1b2c3d4-e5f6-7890-1234-567890abcdef"),
        "address": "123 ORM St",
        "city": "Las Vegas",
        "state": "NV",
        "zip_code": "89101",
        "property_type": PropertyTypeEnum.SINGLE_FAMILY,
        "square_feet": 1500,
        "bedrooms": 3,
        "bathrooms": 2.0,
        "year_built": 1995,
        "lot_size": 0.18,
        "current_value": 250000.00,
        "last_sale_price": 200000.00,
        "last_sale_date": now,
        "estimated_rent": None,
        "repair_cost": None,
        "arv": None,
        "notes": "",
        "data_source": "manual",
        "created_at": now,
        "updated_at": now,
    }
    # Pydantic V1 uses 'Property.from_orm(obj)' or direct dict unpacking if orm_mode=True
    # Pydantic V2 uses 'Property.model_validate(obj)' for ORM objects or dicts if from_attributes=True
    # Given orm_mode=True in Property model, direct unpacking should work.
    prop = Property(**prop_data_from_db)
    assert prop.id == UUID("a1b2c3d4-e5f6-7890-1234-567890abcdef")
    assert prop.address == "123 ORM St"
    assert prop.property_type == PropertyTypeEnum.SINGLE_FAMILY
