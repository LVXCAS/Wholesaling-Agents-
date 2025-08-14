"""
Lead import service for the Real Estate Empire platform.
Handles CSV import functionality with column mapping, validation, and duplicate detection.
"""

import csv
import io
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.lead import (
    PropertyLeadDB, PropertyLeadCreate, LeadStatusEnum, LeadSourceEnum, ContactMethodEnum
)
from app.models.property import PropertyDB, PropertyCreate
from app.core.database import get_db


class ImportStatusEnum(str, Enum):
    """Enum for import status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class ImportResult:
    """Result of a lead import operation."""
    total_rows: int
    successful_imports: int
    failed_imports: int
    duplicates_found: int
    errors: List[Dict[str, Any]]
    status: ImportStatusEnum
    import_id: str
    created_leads: List[uuid.UUID]
    created_properties: List[uuid.UUID]


@dataclass
class ValidationError:
    """Validation error for a specific row."""
    row_number: int
    field: str
    value: Any
    error_message: str


@dataclass
class ColumnMapping:
    """Column mapping configuration for CSV import."""
    # Property fields
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    property_type: Optional[str] = None
    bedrooms: Optional[str] = None
    bathrooms: Optional[str] = None
    square_feet: Optional[str] = None
    year_built: Optional[str] = None
    
    # Lead fields
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    owner_phone: Optional[str] = None
    source: Optional[str] = None
    asking_price: Optional[str] = None
    motivation_factors: Optional[str] = None
    notes: Optional[str] = None
    
    # Optional fields
    owner_address: Optional[str] = None
    preferred_contact_method: Optional[str] = None
    mortgage_balance: Optional[str] = None
    equity_estimate: Optional[str] = None
    condition_notes: Optional[str] = None
    tags: Optional[str] = None


class LeadImportService:
    """Service for importing leads from CSV files."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_csv(self, csv_content: str) -> Dict[str, Any]:
        """
        Analyze CSV content and suggest column mappings.
        
        Args:
            csv_content: Raw CSV content as string
            
        Returns:
            Dictionary with analysis results and suggested mappings
        """
        try:
            # Parse CSV to get headers and sample data
            csv_reader = csv.reader(io.StringIO(csv_content))
            headers = next(csv_reader)
            
            # Get first few rows as samples
            sample_rows = []
            for i, row in enumerate(csv_reader):
                if i >= 5:  # Limit to 5 sample rows
                    break
                sample_rows.append(row)
            
            # Suggest column mappings based on header names
            suggested_mapping = self._suggest_column_mapping(headers)
            
            return {
                "headers": headers,
                "sample_rows": sample_rows,
                "total_rows": len(sample_rows) + 1,  # +1 for header
                "suggested_mapping": suggested_mapping,
                "analysis_status": "success"
            }
            
        except Exception as e:
            return {
                "analysis_status": "error",
                "error_message": str(e)
            }
    
    def import_leads(
        self, 
        csv_content: str, 
        column_mapping: ColumnMapping,
        default_source: LeadSourceEnum = LeadSourceEnum.OTHER,
        skip_duplicates: bool = True
    ) -> ImportResult:
        """
        Import leads from CSV content using provided column mapping.
        
        Args:
            csv_content: Raw CSV content as string
            column_mapping: Column mapping configuration
            default_source: Default source for leads if not specified
            skip_duplicates: Whether to skip duplicate leads
            
        Returns:
            ImportResult with details of the import operation
        """
        import_id = str(uuid.uuid4())
        errors = []
        created_leads = []
        created_properties = []
        duplicates_found = 0
        
        try:
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            rows = list(csv_reader)
            total_rows = len(rows)
            
            if total_rows == 0:
                return ImportResult(
                    total_rows=0,
                    successful_imports=0,
                    failed_imports=0,
                    duplicates_found=0,
                    errors=[{"error": "No data rows found in CSV"}],
                    status=ImportStatusEnum.FAILED,
                    import_id=import_id,
                    created_leads=[],
                    created_properties=[]
                )
            
            # Process each row
            for row_index, row in enumerate(rows, start=2):  # Start at 2 (header is row 1)
                try:
                    # Extract and validate property data
                    property_data = self._extract_property_data(row, column_mapping, row_index)
                    if not property_data:
                        continue
                    
                    # Check for duplicate property
                    existing_property = self._find_duplicate_property(property_data)
                    
                    if existing_property:
                        property_id = existing_property.id
                    else:
                        # Create new property
                        property_create = PropertyCreate(**property_data)
                        new_property = PropertyDB(**property_create.dict())
                        self.db.add(new_property)
                        self.db.flush()  # Get the ID
                        property_id = new_property.id
                        created_properties.append(property_id)
                    
                    # Extract and validate lead data
                    lead_data = self._extract_lead_data(row, column_mapping, property_id, default_source, row_index)
                    if not lead_data:
                        continue
                    
                    # Check for duplicate lead
                    if skip_duplicates:
                        existing_lead = self._find_duplicate_lead(lead_data, property_id)
                        if existing_lead:
                            duplicates_found += 1
                            continue
                    
                    # Create new lead
                    lead_create = PropertyLeadCreate(**lead_data)
                    new_lead = PropertyLeadDB(**lead_create.dict())
                    self.db.add(new_lead)
                    self.db.flush()  # Get the ID
                    created_leads.append(new_lead.id)
                    
                except Exception as e:
                    errors.append({
                        "row": row_index,
                        "error": str(e),
                        "data": row
                    })
            
            # Commit all changes
            self.db.commit()
            
            successful_imports = len(created_leads)
            failed_imports = len(errors)
            
            # Determine status
            if successful_imports == 0:
                status = ImportStatusEnum.FAILED
            elif failed_imports == 0:
                status = ImportStatusEnum.COMPLETED
            else:
                status = ImportStatusEnum.PARTIAL
            
            return ImportResult(
                total_rows=total_rows,
                successful_imports=successful_imports,
                failed_imports=failed_imports,
                duplicates_found=duplicates_found,
                errors=errors,
                status=status,
                import_id=import_id,
                created_leads=created_leads,
                created_properties=created_properties
            )
            
        except Exception as e:
            self.db.rollback()
            return ImportResult(
                total_rows=0,
                successful_imports=0,
                failed_imports=1,
                duplicates_found=0,
                errors=[{"error": f"Import failed: {str(e)}"}],
                status=ImportStatusEnum.FAILED,
                import_id=import_id,
                created_leads=[],
                created_properties=[]
            )
    
    def _suggest_column_mapping(self, headers: List[str]) -> Dict[str, str]:
        """
        Suggest column mappings based on header names.
        
        Args:
            headers: List of CSV headers
            
        Returns:
            Dictionary with suggested mappings
        """
        mapping = {}
        
        # Define mapping patterns
        patterns = {
            "address": ["address", "street", "property_address", "street_address"],
            "city": ["city", "town", "municipality"],
            "state": ["state", "province", "region"],
            "zip_code": ["zip", "zipcode", "zip_code", "postal_code"],
            "property_type": ["type", "property_type", "prop_type"],
            "bedrooms": ["bedrooms", "beds", "bed", "bedroom_count"],
            "bathrooms": ["bathrooms", "baths", "bath", "bathroom_count"],
            "square_feet": ["sqft", "square_feet", "sq_ft", "size"],
            "year_built": ["year_built", "built", "construction_year"],
            "owner_name": ["owner", "owner_name", "name", "seller_name"],
            "owner_email": ["email", "owner_email", "contact_email"],
            "owner_phone": ["phone", "owner_phone", "contact_phone", "telephone"],
            "source": ["source", "lead_source", "origin"],
            "asking_price": ["price", "asking_price", "list_price", "listing_price"],
            "notes": ["notes", "comments", "description", "remarks"]
        }
        
        # Match headers to patterns
        for header in headers:
            header_lower = header.lower().strip()
            for field, pattern_list in patterns.items():
                if any(pattern in header_lower for pattern in pattern_list):
                    mapping[field] = header
                    break
        
        return mapping
    
    def _extract_property_data(self, row: Dict[str, str], mapping: ColumnMapping, row_index: int) -> Optional[Dict[str, Any]]:
        """
        Extract property data from CSV row.
        
        Args:
            row: CSV row data
            mapping: Column mapping configuration
            row_index: Row number for error reporting
            
        Returns:
            Property data dictionary or None if invalid
        """
        try:
            # Required fields
            address = self._get_mapped_value(row, mapping.address)
            city = self._get_mapped_value(row, mapping.city)
            state = self._get_mapped_value(row, mapping.state)
            zip_code = self._get_mapped_value(row, mapping.zip_code)
            
            if not all([address, city, state, zip_code]):
                raise ValueError("Missing required property fields: address, city, state, zip_code")
            
            property_data = {
                "address": address.strip(),
                "city": city.strip(),
                "state": state.strip(),
                "zip_code": zip_code.strip()
            }
            
            # Optional fields
            if mapping.property_type:
                prop_type = self._get_mapped_value(row, mapping.property_type)
                if prop_type:
                    property_data["property_type"] = self._normalize_property_type(prop_type)
            
            if mapping.bedrooms:
                bedrooms = self._get_mapped_value(row, mapping.bedrooms)
                if bedrooms:
                    property_data["bedrooms"] = self._safe_int_convert(bedrooms)
            
            if mapping.bathrooms:
                bathrooms = self._get_mapped_value(row, mapping.bathrooms)
                if bathrooms:
                    property_data["bathrooms"] = self._safe_float_convert(bathrooms)
            
            if mapping.square_feet:
                sqft = self._get_mapped_value(row, mapping.square_feet)
                if sqft:
                    property_data["square_feet"] = self._safe_int_convert(sqft)
            
            if mapping.year_built:
                year = self._get_mapped_value(row, mapping.year_built)
                if year:
                    property_data["year_built"] = self._safe_int_convert(year)
            
            return property_data
            
        except Exception as e:
            raise ValueError(f"Row {row_index}: {str(e)}")
    
    def _extract_lead_data(
        self, 
        row: Dict[str, str], 
        mapping: ColumnMapping, 
        property_id: uuid.UUID,
        default_source: LeadSourceEnum,
        row_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Extract lead data from CSV row.
        
        Args:
            row: CSV row data
            mapping: Column mapping configuration
            property_id: Associated property ID
            default_source: Default source if not specified
            row_index: Row number for error reporting
            
        Returns:
            Lead data dictionary or None if invalid
        """
        try:
            lead_data = {
                "property_id": property_id,
                "source": default_source
            }
            
            # Owner information
            if mapping.owner_name:
                name = self._get_mapped_value(row, mapping.owner_name)
                if name:
                    lead_data["owner_name"] = name.strip()
            
            if mapping.owner_email:
                email = self._get_mapped_value(row, mapping.owner_email)
                if email and self._is_valid_email(email):
                    lead_data["owner_email"] = email.strip().lower()
            
            if mapping.owner_phone:
                phone = self._get_mapped_value(row, mapping.owner_phone)
                if phone:
                    lead_data["owner_phone"] = self._normalize_phone(phone)
            
            if mapping.owner_address:
                addr = self._get_mapped_value(row, mapping.owner_address)
                if addr:
                    lead_data["owner_address"] = addr.strip()
            
            # Source override
            if mapping.source:
                source = self._get_mapped_value(row, mapping.source)
                if source:
                    normalized_source = self._normalize_source(source)
                    if normalized_source:
                        lead_data["source"] = normalized_source
            
            # Financial information
            if mapping.asking_price:
                price = self._get_mapped_value(row, mapping.asking_price)
                if price:
                    lead_data["asking_price"] = self._safe_float_convert(price)
            
            if mapping.mortgage_balance:
                balance = self._get_mapped_value(row, mapping.mortgage_balance)
                if balance:
                    lead_data["mortgage_balance"] = self._safe_float_convert(balance)
            
            if mapping.equity_estimate:
                equity = self._get_mapped_value(row, mapping.equity_estimate)
                if equity:
                    lead_data["equity_estimate"] = self._safe_float_convert(equity)
            
            # Contact preferences
            if mapping.preferred_contact_method:
                method = self._get_mapped_value(row, mapping.preferred_contact_method)
                if method:
                    normalized_method = self._normalize_contact_method(method)
                    if normalized_method:
                        lead_data["preferred_contact_method"] = normalized_method
            
            # Additional information
            if mapping.condition_notes:
                notes = self._get_mapped_value(row, mapping.condition_notes)
                if notes:
                    lead_data["condition_notes"] = notes.strip()
            
            if mapping.notes:
                notes = self._get_mapped_value(row, mapping.notes)
                if notes:
                    lead_data["notes"] = notes.strip()
            
            if mapping.tags:
                tags = self._get_mapped_value(row, mapping.tags)
                if tags:
                    # Split tags by comma and clean them
                    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
                    if tag_list:
                        lead_data["tags"] = tag_list
            
            if mapping.motivation_factors:
                factors = self._get_mapped_value(row, mapping.motivation_factors)
                if factors:
                    # Split factors by comma and clean them
                    factor_list = [factor.strip() for factor in factors.split(",") if factor.strip()]
                    if factor_list:
                        lead_data["motivation_factors"] = factor_list
            
            return lead_data
            
        except Exception as e:
            raise ValueError(f"Row {row_index}: {str(e)}")
    
    def _find_duplicate_property(self, property_data: Dict[str, Any]) -> Optional[PropertyDB]:
        """
        Find duplicate property based on address.
        
        Args:
            property_data: Property data dictionary
            
        Returns:
            Existing PropertyDB instance or None
        """
        return self.db.query(PropertyDB).filter(
            and_(
                PropertyDB.address == property_data["address"],
                PropertyDB.city == property_data["city"],
                PropertyDB.state == property_data["state"],
                PropertyDB.zip_code == property_data["zip_code"]
            )
        ).first()
    
    def _find_duplicate_lead(self, lead_data: Dict[str, Any], property_id: uuid.UUID) -> Optional[PropertyLeadDB]:
        """
        Find duplicate lead based on property and owner information.
        
        Args:
            lead_data: Lead data dictionary
            property_id: Property ID
            
        Returns:
            Existing PropertyLeadDB instance or None
        """
        query = self.db.query(PropertyLeadDB).filter(
            PropertyLeadDB.property_id == property_id
        )
        
        # Check for duplicate based on owner email or phone
        conditions = []
        if lead_data.get("owner_email"):
            conditions.append(PropertyLeadDB.owner_email == lead_data["owner_email"])
        if lead_data.get("owner_phone"):
            conditions.append(PropertyLeadDB.owner_phone == lead_data["owner_phone"])
        
        if conditions:
            query = query.filter(or_(*conditions))
            return query.first()
        
        return None
    
    def _get_mapped_value(self, row: Dict[str, str], column_name: Optional[str]) -> Optional[str]:
        """Get value from row using mapped column name."""
        if not column_name or column_name not in row:
            return None
        value = row[column_name]
        return value.strip() if value and value.strip() else None
    
    def _safe_int_convert(self, value: str) -> Optional[int]:
        """Safely convert string to integer."""
        try:
            # Remove commas and other formatting
            clean_value = value.replace(",", "").replace("$", "").strip()
            return int(float(clean_value))  # Handle decimal strings
        except (ValueError, TypeError):
            return None
    
    def _safe_float_convert(self, value: str) -> Optional[float]:
        """Safely convert string to float."""
        try:
            # Remove commas, dollar signs, and other formatting
            clean_value = value.replace(",", "").replace("$", "").strip()
            return float(clean_value)
        except (ValueError, TypeError):
            return None
    
    def _normalize_property_type(self, prop_type: str) -> str:
        """Normalize property type to enum value."""
        prop_type_lower = prop_type.lower().strip()
        
        type_mapping = {
            "single family": "single_family",
            "single-family": "single_family",
            "sfh": "single_family",
            "house": "single_family",
            "multi family": "multi_family",
            "multi-family": "multi_family",
            "duplex": "multi_family",
            "triplex": "multi_family",
            "fourplex": "multi_family",
            "condo": "condo",
            "condominium": "condo",
            "townhouse": "townhouse",
            "townhome": "townhouse",
            "apartment": "apartment",
            "commercial": "commercial",
            "land": "land",
            "mobile home": "mobile_home",
            "mobile": "mobile_home",
            "manufactured": "mobile_home"
        }
        
        return type_mapping.get(prop_type_lower, "single_family")
    
    def _normalize_source(self, source: str) -> Optional[str]:
        """Normalize source to enum value."""
        source_lower = source.lower().strip()
        
        source_mapping = {
            "mls": "mls",
            "public records": "public_records",
            "public": "public_records",
            "foreclosure": "foreclosure",
            "fsbo": "fsbo",
            "for sale by owner": "fsbo",
            "expired": "expired_listing",
            "expired listing": "expired_listing",
            "absentee": "absentee_owner",
            "absentee owner": "absentee_owner",
            "high equity": "high_equity",
            "distressed": "distressed",
            "referral": "referral",
            "marketing": "marketing",
            "cold call": "cold_call",
            "direct mail": "direct_mail",
            "mail": "direct_mail"
        }
        
        return source_mapping.get(source_lower, "other")
    
    def _normalize_contact_method(self, method: str) -> Optional[str]:
        """Normalize contact method to enum value."""
        method_lower = method.lower().strip()
        
        method_mapping = {
            "email": "email",
            "phone": "phone",
            "call": "phone",
            "text": "text",
            "sms": "text",
            "mail": "mail",
            "postal": "mail"
        }
        
        return method_mapping.get(method_lower)
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number format."""
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone))
        
        # Format as (XXX) XXX-XXXX if 10 digits
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            # Remove leading 1
            digits = digits[1:]
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        else:
            # Return original if can't format
            return phone
    
    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip()) is not None