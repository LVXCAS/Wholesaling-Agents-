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
    ContractType, ClauseType
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
        
        for condition_key, condition_value in clause.conditions.items():
            actual_value = self._get_field_value(condition_key, deal_data, {})
            
            # Handle different condition types
            if isinstance(condition_value, dict):
                # Complex condition with operator
                operator = condition_value.get("operator", "eq")
                expected_value = condition_value.get("value")
                
                if not self._evaluate_condition_operator(actual_value, operator, expected_value):
                    return False
            else:
                # Simple equality check
                if actual_value != condition_value:
                    return False
        
        return True
    
    def _evaluate_condition_operator(self, actual_value: Any, operator: str, expected_value: Any) -> bool:
        """Evaluate a condition using the specified operator."""
        try:
            if operator == "eq":
                return actual_value == expected_value
            elif operator == "ne":
                return actual_value != expected_value
            elif operator == "gt":
                return float(actual_value) > float(expected_value)
            elif operator == "gte":
                return float(actual_value) >= float(expected_value)
            elif operator == "lt":
                return float(actual_value) < float(expected_value)
            elif operator == "lte":
                return float(actual_value) <= float(expected_value)
            elif operator == "in":
                return actual_value in expected_value
            elif operator == "not_in":
                return actual_value not in expected_value
            elif operator == "contains":
                return str(expected_value).lower() in str(actual_value).lower()
            elif operator == "exists":
                return actual_value is not None
            elif operator == "not_exists":
                return actual_value is None
            else:
                # Unknown operator, default to equality
                return actual_value == expected_value
        except (ValueError, TypeError):
            # If comparison fails, condition is false
            return False
    
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
        
        # Find all variables in the format ${variable_name} or ${variable_name:format}
        variables = re.findall(r'\$\{([^}]+)\}', content)
        
        for variable_expr in variables:
            # Parse variable name and optional format
            if ':' in variable_expr:
                variable, format_spec = variable_expr.split(':', 1)
            else:
                variable = variable_expr
                format_spec = None
            
            if variable in field_values:
                value = field_values[variable]
                formatted_value = self._format_variable_value(value, variable, format_spec)
                content = content.replace(f"${{{variable_expr}}}", formatted_value)
            else:
                # Check for computed variables
                computed_value = self._compute_variable_value(variable, field_values)
                if computed_value is not None:
                    formatted_value = self._format_variable_value(computed_value, variable, format_spec)
                    content = content.replace(f"${{{variable_expr}}}", formatted_value)
                else:
                    # Leave placeholder for missing variables
                    content = content.replace(f"${{{variable_expr}}}", f"[{variable.upper()}]")
        
        return content
    
    def _format_variable_value(self, value: Any, variable: str, format_spec: Optional[str] = None) -> str:
        """Format a variable value based on its type and format specification."""
        if format_spec:
            # Use explicit format specification
            if format_spec == "currency":
                return f"${float(value):,.2f}"
            elif format_spec == "percent":
                return f"{float(value):.2f}%"
            elif format_spec == "date":
                if isinstance(value, str):
                    value = datetime.fromisoformat(value).date()
                return value.strftime("%B %d, %Y")
            elif format_spec == "datetime":
                if isinstance(value, str):
                    value = datetime.fromisoformat(value)
                return value.strftime("%B %d, %Y at %I:%M %p")
            elif format_spec == "upper":
                return str(value).upper()
            elif format_spec == "lower":
                return str(value).lower()
            elif format_spec == "title":
                return str(value).title()
            elif format_spec.startswith("number:"):
                # Format: number:2 for 2 decimal places
                decimals = int(format_spec.split(':')[1])
                return f"{float(value):.{decimals}f}"
            else:
                # Unknown format, return as string
                return str(value)
        
        # Auto-format based on variable name and type
        if isinstance(value, float):
            if variable.endswith('_rate') or variable.endswith('_percent') or 'rate' in variable:
                return f"{value:.2f}%"
            elif any(keyword in variable for keyword in ['price', 'amount', 'cost', 'fee', 'deposit', 'money']):
                return f"${value:,.2f}"
            else:
                return f"{value:.2f}"
        elif isinstance(value, int):
            if any(keyword in variable for keyword in ['price', 'amount', 'cost', 'fee', 'deposit', 'money']):
                return f"${value:,}"
            else:
                return f"{value:,}"
        elif isinstance(value, date):
            return value.strftime("%B %d, %Y")
        elif isinstance(value, datetime):
            return value.strftime("%B %d, %Y at %I:%M %p")
        elif isinstance(value, bool):
            return "Yes" if value else "No"
        else:
            return str(value)
    
    def _compute_variable_value(self, variable: str, field_values: Dict[str, Any]) -> Any:
        """Compute derived variable values from existing field values."""
        # Common computed variables
        if variable == "purchase_price_words":
            price = field_values.get("purchase_price")
            if price:
                return self._number_to_words(price)
        
        elif variable == "down_payment_amount":
            price = field_values.get("purchase_price")
            down_percent = field_values.get("down_payment_percent")
            if price and down_percent:
                return price * (down_percent / 100)
        
        elif variable == "loan_amount":
            price = field_values.get("purchase_price")
            down_payment = field_values.get("down_payment_amount")
            if not down_payment:
                # Calculate down payment if not provided
                down_payment = self._compute_variable_value("down_payment_amount", field_values)
            if price and down_payment:
                return price - down_payment
        
        elif variable == "monthly_payment":
            loan_amount = field_values.get("loan_amount")
            if not loan_amount:
                # Calculate loan amount if not provided
                loan_amount = self._compute_variable_value("loan_amount", field_values)
            interest_rate = field_values.get("interest_rate")
            loan_term = field_values.get("loan_term_years", 30)
            if loan_amount and interest_rate:
                return self._calculate_monthly_payment(loan_amount, interest_rate, loan_term)
        
        elif variable == "closing_costs":
            price = field_values.get("purchase_price")
            if price:
                # Estimate 2-3% of purchase price
                return price * 0.025
        
        elif variable == "property_taxes_annual":
            price = field_values.get("purchase_price")
            tax_rate = field_values.get("property_tax_rate", 1.2)  # Default 1.2%
            if price:
                return price * (tax_rate / 100)
        
        elif variable == "property_taxes_monthly":
            annual_taxes = self._compute_variable_value("property_taxes_annual", field_values)
            if annual_taxes:
                return annual_taxes / 12
        
        return None
    
    def _number_to_words(self, number: float) -> str:
        """Convert a number to words (simplified implementation)."""
        # This is a simplified implementation - in production, use a library like num2words
        if number == 0:
            return "Zero"
        
        # Handle common real estate amounts
        if number >= 1000000:
            millions = int(number / 1000000)
            remainder = number % 1000000
            if remainder == 0:
                return f"{self._basic_number_to_words(millions)} Million"
            else:
                return f"{self._basic_number_to_words(millions)} Million {self._number_to_words(remainder)}"
        elif number >= 1000:
            thousands = int(number / 1000)
            remainder = number % 1000
            if remainder == 0:
                return f"{self._basic_number_to_words(thousands)} Thousand"
            else:
                return f"{self._basic_number_to_words(thousands)} Thousand {self._basic_number_to_words(remainder)}"
        else:
            return self._basic_number_to_words(int(number))
    
    def _basic_number_to_words(self, number: int) -> str:
        """Convert basic numbers (0-999) to words."""
        ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
        teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", 
                "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
        
        if number == 0:
            return ""
        elif number < 10:
            return ones[number]
        elif number < 20:
            return teens[number - 10]
        elif number < 100:
            return tens[number // 10] + ("" if number % 10 == 0 else " " + ones[number % 10])
        else:
            hundreds = number // 100
            remainder = number % 100
            result = ones[hundreds] + " Hundred"
            if remainder > 0:
                result += " " + self._basic_number_to_words(remainder)
            return result
    
    def _calculate_monthly_payment(self, loan_amount: float, annual_rate: float, years: int) -> float:
        """Calculate monthly mortgage payment."""
        monthly_rate = annual_rate / 100 / 12
        num_payments = years * 12
        
        if monthly_rate == 0:
            return loan_amount / num_payments
        
        return loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
               ((1 + monthly_rate) ** num_payments - 1)
    
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
        """Validate a generated contract with comprehensive checks."""
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
        party_roles = set()
        for party in contract.parties:
            if not party.name:
                errors.append(f"Party with role '{party.role}' is missing a name")
            
            if party.signature_required and not party.email:
                warnings.append(f"Party '{party.name}' requires signature but has no email for e-signature")
            
            # Check for duplicate roles
            if party.role in party_roles:
                warnings.append(f"Multiple parties have the same role: '{party.role}'")
            party_roles.add(party.role)
            
            # Validate email format if provided
            if party.email and not self._is_valid_email(party.email):
                errors.append(f"Invalid email format for party '{party.name}': {party.email}")
        
        # Contract type specific validations
        self._validate_contract_type_specific(contract, errors, warnings, suggestions)
        
        # Financial validations
        self._validate_financial_terms(contract, errors, warnings, suggestions)
        
        # Date validations
        self._validate_dates(contract, errors, warnings, suggestions)
        
        # Legal compliance checks
        self._validate_legal_compliance(contract, errors, warnings, suggestions)
        
        # Content quality checks
        self._validate_content_quality(contract, errors, warnings, suggestions)
        
        return ContractValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            missing_fields=missing_fields,
            suggestions=suggestions
        )
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_contract_type_specific(self, contract: ContractDocument, 
                                       errors: List[str], warnings: List[str], 
                                       suggestions: List[str]):
        """Validate contract based on its specific type."""
        if contract.contract_type == ContractType.PURCHASE_AGREEMENT:
            # Purchase agreement specific validations
            if not contract.purchase_price:
                errors.append("Purchase agreement must have a purchase price")
            
            if not contract.property_address:
                errors.append("Purchase agreement must specify property address")
            
            # Check for required parties
            party_roles = {p.role for p in contract.parties}
            if "buyer" not in party_roles:
                warnings.append("Purchase agreement should have a buyer")
            if "seller" not in party_roles:
                warnings.append("Purchase agreement should have a seller")
        
        elif contract.contract_type == ContractType.LEASE_AGREEMENT:
            # Lease agreement specific validations
            party_roles = {p.role for p in contract.parties}
            if "tenant" not in party_roles and "lessee" not in party_roles:
                warnings.append("Lease agreement should have a tenant/lessee")
            if "landlord" not in party_roles and "lessor" not in party_roles:
                warnings.append("Lease agreement should have a landlord/lessor")
        
        elif contract.contract_type == ContractType.WHOLESALE_ASSIGNMENT:
            # Assignment specific validations
            party_roles = {p.role for p in contract.parties}
            if "assignor" not in party_roles:
                warnings.append("Assignment agreement should have an assignor")
            if "assignee" not in party_roles:
                warnings.append("Assignment agreement should have an assignee")
    
    def _validate_financial_terms(self, contract: ContractDocument, 
                                 errors: List[str], warnings: List[str], 
                                 suggestions: List[str]):
        """Validate financial terms and calculations."""
        # Purchase price validations
        if contract.purchase_price:
            if contract.purchase_price <= 0:
                errors.append("Purchase price must be greater than zero")
            elif contract.purchase_price < 1000:
                warnings.append("Purchase price seems unusually low")
            elif contract.purchase_price > 50000000:
                warnings.append("Purchase price seems unusually high")
        
        # Earnest money validations
        if contract.earnest_money and contract.purchase_price:
            if contract.earnest_money > contract.purchase_price:
                errors.append("Earnest money cannot exceed purchase price")
            elif contract.earnest_money < contract.purchase_price * 0.005:  # Less than 0.5%
                warnings.append("Earnest money is less than 0.5% of purchase price")
            elif contract.earnest_money > contract.purchase_price * 0.1:  # More than 10%
                warnings.append("Earnest money is more than 10% of purchase price")
        
        # Field value validations
        field_values = contract.field_values or {}
        
        # Interest rate validation
        if "interest_rate" in field_values:
            rate = field_values["interest_rate"]
            if isinstance(rate, (int, float)):
                if rate < 0:
                    errors.append("Interest rate cannot be negative")
                elif rate > 50:
                    warnings.append("Interest rate seems unusually high")
        
        # Down payment validation
        if "down_payment_percent" in field_values:
            down_percent = field_values["down_payment_percent"]
            if isinstance(down_percent, (int, float)):
                if down_percent < 0 or down_percent > 100:
                    errors.append("Down payment percentage must be between 0 and 100")
    
    def _validate_dates(self, contract: ContractDocument, 
                       errors: List[str], warnings: List[str], 
                       suggestions: List[str]):
        """Validate date fields and relationships."""
        today = datetime.now().date()
        
        # Closing date validation
        if contract.closing_date:
            closing_date = contract.closing_date
            if isinstance(closing_date, datetime):
                closing_date = closing_date.date()
            
            if closing_date <= today:
                warnings.append("Closing date is in the past or today")
            elif closing_date > today + timedelta(days=365):
                warnings.append("Closing date is more than a year in the future")
        
        # Inspection period validation
        if contract.inspection_period:
            if contract.inspection_period < 0:
                errors.append("Inspection period cannot be negative")
            elif contract.inspection_period > 60:
                warnings.append("Inspection period is longer than 60 days")
        
        # Field value date validations
        field_values = contract.field_values or {}
        
        for field_name, value in field_values.items():
            if isinstance(value, (date, datetime)):
                check_date = value.date() if isinstance(value, datetime) else value
                
                if "expir" in field_name.lower() and check_date <= today:
                    warnings.append(f"{field_name} has already expired")
                elif "deadline" in field_name.lower() and check_date <= today:
                    warnings.append(f"{field_name} deadline has passed")
    
    def _validate_legal_compliance(self, contract: ContractDocument, 
                                  errors: List[str], warnings: List[str], 
                                  suggestions: List[str]):
        """Validate legal compliance and required disclosures."""
        content = contract.generated_content or ""
        content_lower = content.lower()
        
        # Check for required disclosures (basic checks)
        if contract.contract_type == ContractType.PURCHASE_AGREEMENT:
            if "lead-based paint" not in content_lower and "lead paint" not in content_lower:
                suggestions.append("Consider adding lead-based paint disclosure for properties built before 1978")
            
            if "as-is" in content_lower:
                suggestions.append("Ensure 'as-is' clause complies with local regulations")
        
        # Check for potentially problematic clauses
        problematic_terms = [
            ("liquidated damages", "Liquidated damages clause may need legal review"),
            ("specific performance", "Specific performance clause may need legal review"),
            ("arbitration", "Arbitration clause may affect legal rights"),
            ("waiver", "Waiver clauses should be carefully reviewed")
        ]
        
        for term, warning in problematic_terms:
            if term in content_lower:
                suggestions.append(warning)
    
    def _validate_content_quality(self, contract: ContractDocument, 
                                 errors: List[str], warnings: List[str], 
                                 suggestions: List[str]):
        """Validate content quality and completeness."""
        content = contract.generated_content or ""
        
        # Check minimum content length
        if len(content) < 500:
            warnings.append("Contract content seems unusually short")
        
        # Check for common formatting issues
        if content.count('\n') < 5:
            suggestions.append("Consider adding more paragraph breaks for readability")
        
        # Check for signature section
        if "signature" not in content.lower():
            warnings.append("Contract may be missing signature section")
        
        # Check for date references
        if not re.search(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\w+ \d{1,2}, \d{4}\b', content):
            suggestions.append("Contract may be missing important dates")
        
        # Check for monetary amounts
        if not re.search(r'\$[\d,]+\.?\d*', content):
            suggestions.append("Contract may be missing monetary amounts")
    
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