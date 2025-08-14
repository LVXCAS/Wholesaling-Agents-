import uuid
from typing import List, Any, Optional # Added Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.property import Property, PropertyCreate, PropertyUpdate
from app.services import PropertyService # Corrected: Removed .property_service

router = APIRouter()

@router.post("/", response_model=Property, status_code=status.HTTP_201_CREATED)
def create_property_endpoint(
    *,
    db: Session = Depends(get_db),
    property_in: PropertyCreate
) -> Any:
    service = PropertyService(db)
    db_property = service.create_property(property_data=property_in)
    return db_property

@router.get("/", response_model=List[Property])
def read_properties_endpoint(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    service = PropertyService(db)
    properties = service.get_properties(skip=skip, limit=limit)
    return properties

@router.get("/{property_id}", response_model=Property)
def read_property_endpoint(
    *,
    db: Session = Depends(get_db),
    property_id: uuid.UUID
) -> Any:
    service = PropertyService(db)
    db_property = service.get_property(property_id=property_id)
    if not db_property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    return db_property

@router.put("/{property_id}", response_model=Property)
def update_property_endpoint(
    *,
    db: Session = Depends(get_db),
    property_id: uuid.UUID,
    property_in: PropertyUpdate
) -> Any:
    service = PropertyService(db)
    updated_property = service.update_property(property_id=property_id, property_data=property_in)
    if not updated_property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found for update")
    return updated_property

@router.delete("/{property_id}", response_model=Property)
def delete_property_endpoint(
    *,
    db: Session = Depends(get_db),
    property_id: uuid.UUID
) -> Any:
    service = PropertyService(db)
    property_to_delete = service.get_property(property_id=property_id) #
    if not property_to_delete:
        raise HTTPException(status_code=status.HTTP_44_NOT_FOUND, detail="Property not found for deletion")

    service.delete_property(property_id=property_id)
    return property_to_delete
