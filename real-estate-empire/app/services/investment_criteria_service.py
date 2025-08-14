"""
Investment Criteria Service

This service handles investment criteria management, property matching,
and scoring algorithms for the deal sourcing engine.
"""

from typing import List, Dict, Optional, Any, Tuple
import uuid
import math
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.investment_criteria import (
    InvestmentCriteria, CriteriaRule, CriteriaMatch, CriteriaTemplate,
    CriteriaOperator, CriteriaMatchSummary, GeographicCriteria,
    FinancialCriteria, PropertyCriteria, MarketCriteria
)
from app.models.property import PropertyCreate, PropertyTypeEnum
from app.core.database import get_db


class InvestmentCriteriaService:
    """Service for managing investment criteria and property matching"""
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
    
    def create_criteria(self, criteria: InvestmentCriteria) -> InvestmentCriteria:
        """Create new investment criteria"""
        criteria.id = uuid.uuid4()
        criteria.created_at = datetime.now()
        criteria.updated_at = datetime.now()
        
        # Store in database (implementation depends on your ORM setup)
        # For now, we'll return the criteria as-is
        return criteria
    
    def get_criteria(self, criteria_id: uuid.UUID) -> Optional[InvestmentCriteria]:
        """Get investment criteria by ID"""
        # Implementation would query database
        # For now, return None
        return None
    
    def list_criteria(self, active_only: bool = True) -> List[InvestmentCriteria]:
        """List all investment criteria"""
        # Implementation would query database
        # For now, return empty list
        return []
    
    def update_criteria(self, criteria_id: uuid.UUID, updates: Dict[str, Any]) -> Optional[InvestmentCriteria]:
        """Update investment criteria"""
        criteria = self.get_criteria(criteria_id)
        if not criteria:
            return None
        
        for key, value in updates.items():
            if hasattr(criteria, key):
                setattr(criteria, key, value)
        
        criteria.updated_at = datetime.now()
        return criteria
    
    def delete_criteria(self, criteria_id: uuid.UUID) -> bool:
        """Delete investment criteria"""
        # Implementation would delete from database
        return True
    
    def evaluate_property(self, property_data: PropertyCreate, criteria: InvestmentCriteria) -> CriteriaMatch:
        """Evaluate a property against investment criteria"""
        
        match = CriteriaMatch(
            property_id=getattr(property_data, 'id', None) or uuid.uuid4(),
            criteria_id=criteria.id,
            overall_score=0.0,
            meets_required=True,
            rule_results={},
            failed_required_rules=[]
        )
        
        scores = []
        weights = []
        
        # Evaluate geographic criteria
        if criteria.geographic:
            geo_score, geo_meets_required = self._evaluate_geographic_criteria(
                property_data, criteria.geographic
            )
            match.geographic_score = geo_score
            scores.append(geo_score)
            weights.append(1.0)  # Default weight
            
            if not geo_meets_required:
                match.meets_required = False
                match.failed_required_rules.append("geographic_criteria")
        
        # Evaluate financial criteria
        if criteria.financial:
            fin_score, fin_meets_required = self._evaluate_financial_criteria(
                property_data, criteria.financial
            )
            match.financial_score = fin_score
            scores.append(fin_score)
            weights.append(2.0)  # Higher weight for financial criteria
            
            if not fin_meets_required:
                match.meets_required = False
                match.failed_required_rules.append("financial_criteria")
        
        # Evaluate property criteria
        if criteria.property:
            prop_score, prop_meets_required = self._evaluate_property_criteria(
                property_data, criteria.property
            )
            match.property_score = prop_score
            scores.append(prop_score)
            weights.append(1.0)
            
            if not prop_meets_required:
                match.meets_required = False
                match.failed_required_rules.append("property_criteria")
        
        # Evaluate market criteria
        if criteria.market:
            market_score, market_meets_required = self._evaluate_market_criteria(
                property_data, criteria.market
            )
            match.market_score = market_score
            scores.append(market_score)
            weights.append(1.5)
            
            if not market_meets_required:
                match.meets_required = False
                match.failed_required_rules.append("market_criteria")
        
        # Evaluate custom rules
        if criteria.custom_rules:
            custom_score, custom_meets_required = self._evaluate_custom_rules(
                property_data, criteria.custom_rules
            )
            match.custom_rules_score = custom_score
            scores.append(custom_score)
            weights.append(1.0)
            
            if not custom_meets_required:
                match.meets_required = False
                match.failed_required_rules.append("custom_rules")
        
        # Calculate overall weighted score
        if scores and weights:
            weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
            total_weight = sum(weights)
            match.overall_score = weighted_sum / total_weight
        
        # Set confidence score based on data completeness
        match.confidence_score = self._calculate_confidence_score(property_data)
        
        return match
    
    def _evaluate_geographic_criteria(self, property_data: PropertyCreate, geo_criteria: GeographicCriteria) -> Tuple[float, bool]:
        """Evaluate geographic criteria"""
        score = 100.0
        meets_required = True
        
        # Check states
        if geo_criteria.states and property_data.state:
            if property_data.state.upper() not in [s.upper() for s in geo_criteria.states]:
                score = 0.0
                meets_required = False
        
        # Check excluded states
        if geo_criteria.exclude_states and property_data.state:
            if property_data.state.upper() in [s.upper() for s in geo_criteria.exclude_states]:
                score = 0.0
                meets_required = False
        
        # Check cities
        if geo_criteria.cities and property_data.city:
            if property_data.city.upper() not in [c.upper() for c in geo_criteria.cities]:
                score *= 0.5  # Partial penalty for city mismatch
        
        # Check zip codes
        if geo_criteria.zip_codes and property_data.zip_code:
            if property_data.zip_code not in geo_criteria.zip_codes:
                score *= 0.7  # Partial penalty for zip code mismatch
        
        # Check distance (would need geocoding service)
        if (geo_criteria.max_distance_from_point and 
            geo_criteria.center_lat and geo_criteria.center_lng):
            # For now, assume distance check passes
            # In real implementation, would calculate distance using geocoding
            pass
        
        return score, meets_required
    
    def _evaluate_financial_criteria(self, property_data: PropertyCreate, fin_criteria: FinancialCriteria) -> Tuple[float, bool]:
        """Evaluate financial criteria"""
        score = 100.0
        meets_required = True
        
        # Get property price (from listing_price or estimated value)
        price = getattr(property_data, 'listing_price', None) or getattr(property_data, 'estimated_value', None)
        
        if price:
            # Check price range
            if fin_criteria.min_price and price < fin_criteria.min_price:
                score = 0.0
                meets_required = False
            
            if fin_criteria.max_price and price > fin_criteria.max_price:
                score = 0.0
                meets_required = False
        
        # For other financial metrics, we'd need property analysis data
        # This would typically come from the analyst agent
        
        # Check cap rate (if available)
        cap_rate = getattr(property_data, 'cap_rate', None)
        if cap_rate and fin_criteria.min_cap_rate:
            if cap_rate < fin_criteria.min_cap_rate:
                score *= 0.5
        
        # Check cash flow (if available)
        cash_flow = getattr(property_data, 'monthly_cash_flow', None)
        if cash_flow and fin_criteria.min_cash_flow:
            if cash_flow < fin_criteria.min_cash_flow:
                score *= 0.5
        
        return score, meets_required
    
    def _evaluate_property_criteria(self, property_data: PropertyCreate, prop_criteria: PropertyCriteria) -> Tuple[float, bool]:
        """Evaluate property criteria"""
        score = 100.0
        meets_required = True
        
        # Check property type
        if prop_criteria.property_types and property_data.property_type:
            if property_data.property_type not in prop_criteria.property_types:
                score = 0.0
                meets_required = False
        
        # Check bedrooms
        if property_data.bedrooms is not None:
            if prop_criteria.min_bedrooms and property_data.bedrooms < prop_criteria.min_bedrooms:
                score *= 0.7
            if prop_criteria.max_bedrooms and property_data.bedrooms > prop_criteria.max_bedrooms:
                score *= 0.7
        
        # Check bathrooms
        if property_data.bathrooms is not None:
            if prop_criteria.min_bathrooms and property_data.bathrooms < prop_criteria.min_bathrooms:
                score *= 0.7
            if prop_criteria.max_bathrooms and property_data.bathrooms > prop_criteria.max_bathrooms:
                score *= 0.7
        
        # Check square footage
        if property_data.square_feet is not None:
            if prop_criteria.min_square_feet and property_data.square_feet < prop_criteria.min_square_feet:
                score *= 0.8
            if prop_criteria.max_square_feet and property_data.square_feet > prop_criteria.max_square_feet:
                score *= 0.8
        
        # Check year built
        if property_data.year_built is not None:
            if prop_criteria.min_year_built and property_data.year_built < prop_criteria.min_year_built:
                score *= 0.6
            if prop_criteria.max_year_built and property_data.year_built > prop_criteria.max_year_built:
                score *= 0.6
        
        # Check required features
        if prop_criteria.required_features and property_data.features:
            property_features = property_data.features.keys() if isinstance(property_data.features, dict) else property_data.features
            for required_feature in prop_criteria.required_features:
                if required_feature not in property_features:
                    score *= 0.5
        
        return score, meets_required
    
    def _evaluate_market_criteria(self, property_data: PropertyCreate, market_criteria: MarketCriteria) -> Tuple[float, bool]:
        """Evaluate market criteria"""
        score = 100.0
        meets_required = True
        
        # Check days on market
        days_on_market = getattr(property_data, 'days_on_market', None)
        if days_on_market is not None:
            if market_criteria.min_days_on_market and days_on_market < market_criteria.min_days_on_market:
                score *= 0.8
            if market_criteria.max_days_on_market and days_on_market > market_criteria.max_days_on_market:
                score *= 0.8
        
        # Check if distressed only
        if market_criteria.distressed_only:
            is_distressed = getattr(property_data, 'is_distressed', False)
            if not is_distressed:
                score = 0.0
                meets_required = False
        
        # Check if foreclosure only
        if market_criteria.foreclosure_only:
            is_foreclosure = getattr(property_data, 'is_foreclosure', False)
            if not is_foreclosure:
                score = 0.0
                meets_required = False
        
        # Check motivation indicators
        if market_criteria.motivated_seller_indicators:
            motivation_indicators = getattr(property_data, 'motivation_indicators', [])
            for required_indicator in market_criteria.motivated_seller_indicators:
                if required_indicator not in motivation_indicators:
                    score *= 0.7
        
        return score, meets_required
    
    def _evaluate_custom_rules(self, property_data: PropertyCreate, custom_rules: List[CriteriaRule]) -> Tuple[float, bool]:
        """Evaluate custom rules"""
        score = 100.0
        meets_required = True
        
        for rule in custom_rules:
            rule_result = self._evaluate_single_rule(property_data, rule)
            
            if rule.required and not rule_result:
                meets_required = False
                score = 0.0
                break
            
            if not rule_result:
                # Apply weight-based penalty
                penalty = (rule.weight / 10.0) * 0.5  # Max 50% penalty for weight 10
                score *= (1.0 - penalty)
        
        return score, meets_required
    
    def _evaluate_single_rule(self, property_data: PropertyCreate, rule: CriteriaRule) -> bool:
        """Evaluate a single criteria rule"""
        try:
            # Get property value for the field
            property_value = getattr(property_data, rule.field, None)
            
            if property_value is None:
                return False
            
            # Apply operator
            if rule.operator == CriteriaOperator.EQUALS:
                return property_value == rule.value
            elif rule.operator == CriteriaOperator.GREATER_THAN:
                return property_value > rule.value
            elif rule.operator == CriteriaOperator.LESS_THAN:
                return property_value < rule.value
            elif rule.operator == CriteriaOperator.GREATER_EQUAL:
                return property_value >= rule.value
            elif rule.operator == CriteriaOperator.LESS_EQUAL:
                return property_value <= rule.value
            elif rule.operator == CriteriaOperator.BETWEEN:
                if isinstance(rule.value, list) and len(rule.value) == 2:
                    return rule.value[0] <= property_value <= rule.value[1]
                return False
            elif rule.operator == CriteriaOperator.IN:
                return property_value in rule.value
            elif rule.operator == CriteriaOperator.NOT_IN:
                return property_value not in rule.value
            elif rule.operator == CriteriaOperator.CONTAINS:
                if isinstance(property_value, (list, str)):
                    return rule.value in property_value
                return False
            
            return False
            
        except Exception:
            return False
    
    def _calculate_confidence_score(self, property_data: PropertyCreate) -> float:
        """Calculate confidence score based on data completeness"""
        total_fields = 0
        complete_fields = 0
        
        # Core fields
        core_fields = ['address', 'city', 'state', 'zip_code', 'property_type']
        for field in core_fields:
            total_fields += 1
            if getattr(property_data, field, None):
                complete_fields += 1
        
        # Optional fields
        optional_fields = ['bedrooms', 'bathrooms', 'square_feet', 'year_built', 'lot_size']
        for field in optional_fields:
            total_fields += 1
            if getattr(property_data, field, None):
                complete_fields += 1
        
        return complete_fields / total_fields if total_fields > 0 else 0.0
    
    def batch_evaluate_properties(self, properties: List[PropertyCreate], criteria: InvestmentCriteria) -> List[CriteriaMatch]:
        """Evaluate multiple properties against criteria"""
        matches = []
        for property_data in properties:
            match = self.evaluate_property(property_data, criteria)
            matches.append(match)
        
        return matches
    
    def get_matching_summary(self, matches: List[CriteriaMatch]) -> CriteriaMatchSummary:
        """Generate summary of matching results"""
        total_evaluated = len(matches)
        meeting_criteria = len([m for m in matches if m.meets_required])
        
        if total_evaluated > 0:
            average_score = sum(m.overall_score for m in matches) / total_evaluated
        else:
            average_score = 0.0
        
        # Get top matches (sorted by score)
        top_matches = sorted(matches, key=lambda m: m.overall_score, reverse=True)[:10]
        
        return CriteriaMatchSummary(
            total_properties_evaluated=total_evaluated,
            properties_meeting_criteria=meeting_criteria,
            average_score=average_score,
            top_matches=top_matches,
            criteria_effectiveness={}  # Could calculate effectiveness metrics
        )


class CriteriaTemplateService:
    """Service for managing criteria templates"""
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
    
    def create_template(self, template: CriteriaTemplate) -> CriteriaTemplate:
        """Create a new criteria template"""
        template.id = uuid.uuid4()
        template.created_at = datetime.now()
        return template
    
    def get_template(self, template_id: uuid.UUID) -> Optional[CriteriaTemplate]:
        """Get template by ID"""
        return None
    
    def list_templates(self, strategy: Optional[str] = None, public_only: bool = False) -> List[CriteriaTemplate]:
        """List available templates"""
        return []
    
    def get_default_templates(self) -> Dict[str, CriteriaTemplate]:
        """Get default templates for common strategies"""
        templates = {}
        
        # Flip strategy template
        flip_criteria = InvestmentCriteria(
            name="Default Flip Criteria",
            description="Standard criteria for fix-and-flip properties",
            strategy="flip",
            financial=FinancialCriteria(
                max_price=300000,
                min_arv=400000,
                max_repair_cost=50000,
                min_roi=20.0
            ),
            property=PropertyCriteria(
                property_types=["single_family", "condo"],
                min_bedrooms=2,
                max_year_built=1990
            ),
            market=MarketCriteria(
                min_days_on_market=30,
                distressed_only=True
            )
        )
        
        templates["flip"] = CriteriaTemplate(
            name="Fix and Flip Template",
            description="Template for fix-and-flip investments",
            strategy="flip",
            criteria=flip_criteria,
            is_public=True
        )
        
        # Rental strategy template
        rental_criteria = InvestmentCriteria(
            name="Default Rental Criteria",
            description="Standard criteria for rental properties",
            strategy="rental",
            financial=FinancialCriteria(
                max_price=250000,
                min_cap_rate=8.0,
                min_cash_flow=200
            ),
            property=PropertyCriteria(
                property_types=["single_family", "multi_family"],
                min_bedrooms=2
            )
        )
        
        templates["rental"] = CriteriaTemplate(
            name="Buy and Hold Rental Template",
            description="Template for rental property investments",
            strategy="rental",
            criteria=rental_criteria,
            is_public=True
        )
        
        return templates