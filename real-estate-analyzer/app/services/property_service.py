# Property Service Module
# Handles all property-related business logic and database operations
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.property import PropertyDB, PropertyCreate, PropertyUpdate


class PropertyService:
    def __init__(self, db: Session):
        self.db = db

    def create_property(self, property_data: PropertyCreate) -> PropertyDB:
        # Create a new property record
        # For Pydantic V2, use .model_dump() instead of .dict()
        db_property = PropertyDB(**property_data.model_dump())
        self.db.add(db_property)
        self.db.commit()
        self.db.refresh(db_property)
        return db_property

    def get_property(self, property_id: UUID) -> Optional[PropertyDB]:
        # Get a single property by ID
        return self.db.query(PropertyDB).filter(PropertyDB.id == property_id).first()

    def get_properties(self, skip: int = 0, limit: int = 100) -> List[PropertyDB]:
        # Get multiple properties with pagination
        return self.db.query(PropertyDB).offset(skip).limit(limit).all()

    def get_properties_by_city(self, city: str) -> List[PropertyDB]:
        # Get properties filtered by city
        return self.db.query(PropertyDB).filter(PropertyDB.city.ilike(f"%{city}%")).all()

    def update_property(self, property_id: UUID, property_data: PropertyUpdate) -> Optional[PropertyDB]:
        # Update an existing property
        db_property = self.get_property(property_id)
        if not db_property:
            return None

        # For Pydantic V2, use .model_dump() instead of .dict()
        update_data = property_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_property, field, value)

        self.db.commit()
        self.db.refresh(db_property)
        return db_property

    def delete_property(self, property_id: UUID) -> bool:
        # Delete a property
        db_property = self.get_property(property_id)
        if not db_property:
            return False

        self.db.delete(db_property)
        self.db.commit()
        return True

    def search_properties(self,
                         min_current_value: Optional[float] = None,
                         max_current_value: Optional[float] = None,
                         min_sqft: Optional[int] = None,
                         max_sqft: Optional[int] = None,
                         bedrooms: Optional[int] = None) -> List[PropertyDB]:
        # Advanced property search with filters using your existing fields
        query = self.db.query(PropertyDB)

        if min_current_value is not None: # Ensure check for None if 0 is a valid value
            query = query.filter(PropertyDB.current_value >= min_current_value)
        if max_current_value is not None:
            query = query.filter(PropertyDB.current_value <= max_current_value)
        if min_sqft is not None:
            query = query.filter(PropertyDB.square_feet >= min_sqft)
        if max_sqft is not None:
            query = query.filter(PropertyDB.square_feet <= max_sqft)
        if bedrooms is not None:
            query = query.filter(PropertyDB.bedrooms == bedrooms)

        return query.all()

    def get_property_by_address(self, address: str) -> Optional[PropertyDB]:
        """Get a property by its address (case-insensitive)."""
        return self.db.query(PropertyDB).filter(
            func.lower(PropertyDB.address) == func.lower(address)
        ).first()

    def list_properties(self) -> List[PropertyDB]:
        """Get all properties."""
        return self.db.query(PropertyDB).all()
