"""
Contract generation service.
Handles dynamic contract assembly, field population, and validation.
"""

import re
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4

from app.models.contract import (
    ContractDocument, ContractTemplate, ContractClause, ContractParty,
    ContractGenerationRequest, ContractValidationResult, ContractStatus,
    ClauseType
)
from app.services.contract_template_service import ContractTemplateService


class ContractGenerationService:
    """Service for generating contracts from templates."""
    
    def __init__(self, template_service: ContractTemplateService):
        self.template_service = template_service
    
    def generate_contract(self, request: ContractGenerationRequest) -> ContractDocument:
        """Generate a contract from a template and deal data."""
        # Get template
        template = self.template_service.get_template(request.template_id)
        if not template:
            raise ValueError(f"Template {request.template_id} not found")
        
        # Create contract document
        contract = ContractDocument(
            template_id=request.template_id,
            contract_type=template.contract_type,
            parties=request.parties,
            field_values=self._extract_field_values(template, request.deal_data, request.custom_terms)
        )
        
        # Determine which clauses to include
        included_clauses = self._determine_included_clauses(
            template, 
            request.deal_data,
            request.include_optional_clauses,
            request.exclude_clauses
        )
        contract.included_clauses = included_clauses
        
        # Generate contract content
        contract.generated_content = self._generate_contract_content(
            template, 
            included_clauses, 
            contract.field_values,
            request.parties
        )
        
        # Extract key contract terms
        self._extract_contract_terms(contract, request.deal_data)
        
        return contract
    
    def _extract_field_values(self, template: ContractTemplate, 
                             deal_data: Dict[str, Any], 
                             custom_terms: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate field values from deal data."""
        field_values = {}
        
        # Process required fields
        for field_name, field_type in template.required_fields.items():
            value = self._get_field_value(field_name, deal_data, custom_terms)
            if value is None:
                raise ValueError(f"Required field '{field_name}' is missing")
            
            # Type conversion and validation
            converted_value = self._convert_field_value(value, field_type, field_name)
            field_values[field_name] = converted_value
        
        # Process optional fields
        for field_name, field_type in template.optional_fields.items():
            value = self._get_field_value(field_name, deal_data, custom_terms)
            if value is not None:
                converted_value = self._convert_field_value(value, field_type, field_name)
                field_values[field_name] = converted_value
        
        return field_values
    
    def _get_field_value(self, field_name: str, 
                        deal_data: Dict[str, Any], 
                        custom_terms: Dict[str, Any]) -> Any:
        """Get field value from deal data or custom terms."""
        # Check custom terms first
        if field_name in custom_terms:
            return custom_terms[field_name]
        
        # Check deal data
        if field_name in deal_data:
            return deal_data[field_name]
        
        # Check nested fields (e.g., property.address)
        if '.' in field_name:
            parts = field_name.split('.')
            value = deal_data
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            return value
        
        return None
    
    def _convert_field_value(self, value: Any, field_type: str, field_name: str) -> Any:
        """Convert and validate field value to the specified type."""
        try:
            if field_type == "string":
                return str(value)
            elif field_type == "int":
                return int(float(value))  # Handle string numbers
            elif field_type == "float":
                return float(value)
            elif field_type == "boolean":
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    return value.lower() in ('true', 'yes', '1', 'on')
                return bool(value)
            elif field_type == "date":
                if isinstance(value, date):
                    return value
                if isinstance(value, datetime):
                    return value.date()
                if isinstance(value, str):
                    # Try common date formats
                    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y'):
                        try:
                            return datetime.strptime(value, fmt).date()
                        except ValueError:
                            continue
                    raise ValueError(f"Invalid date format: {value}")
            elif field_type == "datetime":
                if isinstance(value, datetime):
                    return value
                if isinstance(value, str):
                    # Try common datetime formats
                    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%m/%d/%Y %H:%M'):
                        try:
                            return datetime.strptime(value, fmt)
                        except ValueError:
                            continue
                    raise ValueError(f"Invalid datetime format: {value}")
            else:
                return value  # Unknown type, return as-is
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert field '{field_name}' to {field_type}: {e}")
    
    def _determine_included_clauses(self, template: ContractTemplate,
                                   deal_data: Dict[str, Any],
                                   include_optional: List[str],
                                   exclude_clauses: List[str]) -> List[UUID]:
        """Determine which clauses to include in the contract."""
        included_clauses = []
        
        for clause_id in template.clauses:
            clause = self.template_service.get_clause(clause_id)
            if not clause or not clause.is_active:
                continue
            
            # Check if clause is excluded
            if clause.name in exclude_clauses or str(clause_id) in exclude_clauses:
                continue
            
            # Include based on clause type
            if clause.clause_type == ClauseType.REQUIRED:
                included_clauses.append(clause_id)
            elif clause.clause_type == ClauseType.STANDARD:
                included_clauses.append(clause_id)
            elif clause.clause_type == ClauseType.CONDITIONAL:
                if self._evaluate_clause_conditions(clause, deal_data):
                    included_clauses.append(clause_id)
            elif clause.clause_type == ClauseType.OPTIONAL:
                if (clause.name in include_optional or 
                    str(clause_id) in include_optional):
                    included_clauses.append(clause_id)
        
        return included_clauses
    
    def _evaluate_clause_conditions(self, clause: ContractClause, 
                                   deal_data: Dict[str, Any]) -> bool:
        """Evaluate whether a conditional clause should be included."""
        if not clause.conditions:
            return True
        
        for condition_key, expected_value in clause.conditions.items():
            actual_value = self._get_field_value(condition_key, deal_data, {})
            
            # Simple equality check
            if actual_value != expected_value:
                return False
        
        return True
    
    def _generate_contract_content(self, template: ContractTemplate,
                                  included_clauses: List[UUID],
                                  field_values: Dict[str, Any],
                                  parties: List[ContractParty]) -> str:
        """Generate the full contract content."""
        content_parts = []
        
        # Add header
        content_parts.append(self._generate_contract_header(template, parties))
        
        # Add clauses organized by sections
        sections = self._organize_clauses_by_section(template, included_clauses)
        
        for section_name, clause_ids in sections.items():
            if clause_ids:
                content_parts.append(f"\n## {section_name}\n")
                
                for clause_id in clause_ids:
                    clause = self.template_service.get_clause(clause_id)
                    if clause:
                        clause_content = self._populate_clause_variables(clause, field_values)
                        content_parts.append(f"{clause_content}\n")
        
        # Add signature section
        content_parts.append(self._generate_signature_section(parties))
        
        return "\n".join(content_parts)
    
    def _generate_contract_header(self, template: ContractTemplate, 
                                 parties: List[ContractParty]) -> str:
        """Generate contract header with title and parties."""
        header_parts = [
            f"# {template.name}",
            "",
            "## Parties",
            ""
        ]
        
        for i, party in enumerate(parties, 1):
            header_parts.append(f"{i}. **{party.role.title()}**: {party.name}")
            if party.address:
                header_parts.append(f"   Address: {party.address}")
            if party.email:
                header_parts.append(f"   Email: {party.email}")
            if party.phone:
                header_parts.append(f"   Phone: {party.phone}")
            header_parts.append("")
        
        return "\n".join(header_parts)
    
    def _organize_clauses_by_section(self, template: ContractTemplate, 
                                    included_clauses: List[UUID]) -> Dict[str, List[UUID]]:
        """Organize clauses by section based on template structure."""
        sections = {}
        
        # Get section order from template structure
        template_sections = template.template_structure.get("sections", [])
        section_order = {s["name"]: s["order"] for s in template_sections}
        
        # Group clauses by category (which maps to sections)
        for clause_id in included_clauses:
            clause = self.template_service.get_clause(clause_id)
            if not clause:
                continue
            
            # Map clause category to section name
            section_name = self._map_category_to_section(clause.category)
            
            if section_name not in sections:
                sections[section_name] = []
            sections[section_name].append(clause_id)
        
        # Sort sections by order
        sorted_sections = {}
        for section_name in sorted(sections.keys(), 
                                 key=lambda x: section_order.get(x, 999)):
            sorted_sections[section_name] = sections[section_name]
        
        return sorted_sections
    
    def _map_category_to_section(self, category: str) -> str:
        """Map clause category to section name."""
        category_mapping = {
            "pricing": "Purchase Price and Terms",
            "earnest_money": "Purchase Price and Terms",
            "contingencies": "Contingencies",
            "closing": "Closing",
            "condition": "Property Condition",
            "assignment": "Assignment Rights",
            "general": "General Provisions"
        }
        
        return category_mapping.get(category, "General Provisions")
    
    def _populate_clause_variables(self, clause: ContractClause, 
                                  field_values: Dict[str, Any]) -> str:
        """Populate clause variables with actual values."""
        content = clause.content
        
        # Find all variables in the format ${variable_name}
        variables = re.findall(r'\$\{([^}]+)\}', content)
        
        for variable in variables:
            if variable in field_values:
                value = field_values[variable]
                
                # Format value based on type
                if isinstance(value, float):
                    if variable.endswith('_rate') or variable.endswith('_percent'):
                        formatted_value = f"{value:.2f}%"
                    elif 'price' in variable or 'amount' in variable or 'cost' in variable:
                        formatted_value = f"${value:,.2f}"
                    else:
                        formatted_value = f"{value:.2f}"
                elif isinstance(value, date):
                    formatted_value = value.strftime("%B %d, %Y")
                elif isinstance(value, datetime):
                    formatted_value = value.strftime("%B %d, %Y at %I:%M %p")
                else:
                    formatted_value = str(value)
                
                content = content.replace(f"${{{variable}}}", formatted_value)
            else:
                # Leave placeholder for missing variables
                content = content.replace(f"${{{variable}}}", f"[{variable.upper()}]")
        
        return content
    
    def _generate_signature_section(self, parties: List[ContractParty]) -> str:
        """Generate signature section for all parties."""
        signature_parts = [
            "\n## Signatures",
            "",
            "By signing below, the parties agree to the terms and conditions of this agreement.",
            ""
        ]
        
        for party in parties:
            if party.signature_required:
                signature_parts.extend([
                    f"**{party.role.title()}:**",
                    "",
                    f"Signature: ___________________________ Date: ___________",
                    "",
                    f"Print Name: {party.name}",
                    ""
                ])
        
        return "\n".join(signature_parts)
    
    def _extract_contract_terms(self, contract: ContractDocument, 
                               deal_data: Dict[str, Any]):
        """Extract key contract terms for easy access."""
        field_values = contract.field_values
        
        # Extract common terms
        if "purchase_price" in field_values:
            contract.purchase_price = field_values["purchase_price"]
        
        if "earnest_money" in field_values:
            contract.earnest_money = field_values["earnest_money"]
        
        if "closing_date" in field_values:
            contract.closing_date = field_values["closing_date"]
        
        if "inspection_period" in field_values:
            contract.inspection_period = field_values["inspection_period"]
        
        if "financing_required" in field_values:
            contract.financing_contingency = field_values["financing_required"]
        
        # Extract property address
        if "property_address" in field_values:
            contract.property_address = field_values["property_address"]
        elif "property" in deal_data and isinstance(deal_data["property"], dict):
            prop = deal_data["property"]
            if "address" in prop:
                contract.property_address = prop["address"]
    
    def validate_contract(self, contract: ContractDocument) -> ContractValidationResult:
        """Validate a generated contract."""
        errors = []
        warnings = []
        missing_fields = []
        suggestions = []
        
        # Check required content
        if not contract.generated_content:
            errors.append("Contract content is empty")
        
        if not contract.parties:
            errors.append("Contract must have at least one party")
        
        # Check for placeholder variables in content
        if contract.generated_content:
            placeholders = re.findall(r'\[([A-Z_]+)\]', contract.generated_content)
            if placeholders:
                missing_fields.extend(placeholders)
                warnings.append(f"Contract contains unfilled placeholders: {', '.join(placeholders)}")
        
        # Validate parties
        for party in contract.parties:
            if not party.name:
                errors.append(f"Party with role '{party.role}' is missing a name")
            
            if party.signature_required and not party.email:
                warnings.append(f"Party '{party.name}' requires signature but has no email for e-signature")
        
        # Check contract terms
        if contract.purchase_price and contract.purchase_price <= 0:
            errors.append("Purchase price must be greater than zero")
        
        if contract.earnest_money and contract.purchase_price:
            if contract.earnest_money > contract.purchase_price:
                errors.append("Earnest money cannot exceed purchase price")
        
        if contract.closing_date:
            closing_date = contract.closing_date
            if isinstance(closing_date, datetime):
                closing_date = closing_date.date()
            if closing_date <= datetime.now().date():
                warnings.append("Closing date is in the past")
        
        # Suggestions
        if not contract.property_address:
            suggestions.append("Consider adding property address for clarity")
        
        if len(contract.parties) < 2:
            suggestions.append("Most contracts require at least two parties (buyer and seller)")
        
        return ContractValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            missing_fields=missing_fields,
            suggestions=suggestions
        )
    
    def update_contract_status(self, contract: ContractDocument, 
                              new_status: ContractStatus) -> ContractDocument:
        """Update contract status and related timestamps."""
        contract.status = new_status
        contract.updated_at = datetime.now()
        
        if new_status == ContractStatus.EXECUTED:
            contract.executed_at = datetime.now()
        
        return contract
    
    def regenerate_contract(self, contract: ContractDocument, 
                           updated_data: Dict[str, Any]) -> ContractDocument:
        """Regenerate contract with updated data."""
        # Get original template
        template = self.template_service.get_template(contract.template_id)
        if not template:
            raise ValueError(f"Template {contract.template_id} not found")
        
        # Merge existing field values with updates
        merged_field_values = {**contract.field_values, **updated_data}
        
        # Create new generation request
        request = ContractGenerationRequest(
            template_id=contract.template_id,
            deal_data=merged_field_values,
            parties=contract.parties,
            custom_terms=updated_data
        )
        
        # Generate new contract
        new_contract = self.generate_contract(request)
        
        # Preserve original contract metadata
        new_contract.id = contract.id
        new_contract.created_at = contract.created_at
        new_contract.created_by = contract.created_by
        new_contract.deal_id = contract.deal_id
        
        return new_contract