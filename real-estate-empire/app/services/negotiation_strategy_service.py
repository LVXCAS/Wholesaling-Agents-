"""
Negotiation Strategy Service for generating AI-powered negotiation strategies.
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.property import PropertyDB, PropertyAnalysisDB
from app.models.lead import PropertyLeadDB
from app.models.negotiation import (
    NegotiationStrategyDB, 
    NegotiationStrategyCreate,
    MarketConditionEnum,
    SellerMotivationEnum
)

logger = logging.getLogger(__name__)


class NegotiationStrategyService:
    """Service for generating and managing negotiation strategies."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_strategy(self, property_id: uuid.UUID) -> Dict[str, Any]:
        """
        Generate a comprehensive negotiation strategy for a property.
        
        Args:
            property_id: UUID of the property to generate strategy for
            
        Returns:
            Dict containing the generated negotiation strategy
        """
        try:
            # Get property data
            property_data = self.db.query(PropertyDB).filter(
                PropertyDB.id == property_id
            ).first()
            
            if not property_data:
                raise ValueError(f"Property with ID {property_id} not found")
            
            # Get property analysis if available
            analysis = self.db.query(PropertyAnalysisDB).filter(
                PropertyAnalysisDB.property_id == property_id
            ).first()
            
            # Get lead information if available
            lead = self.db.query(PropertyLeadDB).filter(
                PropertyLeadDB.property_id == property_id
            ).first()
            
            # Analyze market conditions
            market_condition = self._analyze_market_conditions(property_data)
            
            # Assess seller motivation
            seller_motivation = self._assess_seller_motivation(property_data, lead)
            
            # Calculate recommended offer prices
            offer_prices = self._calculate_offer_prices(property_data, analysis, market_condition, seller_motivation)
            
            # Determine negotiation approach
            negotiation_approach = self._determine_negotiation_approach(market_condition, seller_motivation)
            
            # Generate talking points
            talking_points = self._generate_talking_points(property_data, analysis, market_condition)
            
            # Generate value propositions
            value_propositions = self._generate_value_propositions(property_data, market_condition)
            
            # Identify potential objections and responses
            objections = self._identify_potential_objections(property_data, offer_prices, market_condition)
            
            # Recommend contingencies
            contingencies = self._recommend_contingencies(property_data, market_condition)
            
            # Assess risks
            risk_assessment = self._assess_negotiation_risks(property_data, market_condition, seller_motivation)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(property_data, analysis, market_condition, seller_motivation)
            
            strategy = {
                "property_id": property_id,
                "strategy_name": f"Strategy for {property_data.address}",
                "recommended_offer_price": offer_prices["recommended"],
                "max_offer_price": offer_prices["maximum"],
                "negotiation_approach": negotiation_approach,
                "market_condition": market_condition,
                "seller_motivation": seller_motivation,
                "days_on_market_factor": self._calculate_dom_factor(property_data),
                "comparable_sales_factor": self._calculate_comp_factor(analysis),
                "talking_points": talking_points,
                "value_propositions": value_propositions,
                "potential_objections": objections,
                "contingencies": contingencies,
                "confidence_score": confidence_score,
                "risk_assessment": risk_assessment
            }
            
            logger.info(f"Generated negotiation strategy for property {property_id}")
            return strategy
            
        except Exception as e:
            logger.error(f"Error generating negotiation strategy for property {property_id}: {str(e)}")
            raise
    
    def _analyze_market_conditions(self, property_data: PropertyDB) -> MarketConditionEnum:
        """Analyze current market conditions for the property location."""
        try:
            # Simple market analysis based on days on market and price trends
            dom = property_data.days_on_market or 0
            
            # Basic market condition logic (can be enhanced with real market data)
            if dom > 90:
                return MarketConditionEnum.BUYERS_MARKET
            elif dom < 30:
                return MarketConditionEnum.SELLERS_MARKET
            else:
                return MarketConditionEnum.BALANCED
                
        except Exception as e:
            logger.warning(f"Error analyzing market conditions: {str(e)}")
            return MarketConditionEnum.BALANCED
    
    def _assess_seller_motivation(self, property_data: PropertyDB, lead: Optional[PropertyLeadDB]) -> SellerMotivationEnum:
        """Assess seller motivation level based on available data."""
        try:
            motivation_score = 0
            
            # Days on market factor
            dom = property_data.days_on_market or 0
            if dom > 120:
                motivation_score += 3
            elif dom > 60:
                motivation_score += 2
            elif dom > 30:
                motivation_score += 1
            
            # Property condition factor
            if property_data.renovation_needed:
                motivation_score += 2
            
            # Lead motivation indicators
            if lead and lead.motivation_factors:
                motivation_score += len(lead.motivation_factors)
            
            # Price reduction history (simplified)
            if property_data.listing_price and property_data.assessed_value:
                price_ratio = property_data.listing_price / property_data.assessed_value
                if price_ratio < 0.9:
                    motivation_score += 2
                elif price_ratio < 0.95:
                    motivation_score += 1
            
            # Convert score to enum
            if motivation_score >= 6:
                return SellerMotivationEnum.URGENT
            elif motivation_score >= 4:
                return SellerMotivationEnum.HIGH
            elif motivation_score >= 2:
                return SellerMotivationEnum.MODERATE
            else:
                return SellerMotivationEnum.LOW
                
        except Exception as e:
            logger.warning(f"Error assessing seller motivation: {str(e)}")
            return SellerMotivationEnum.MODERATE
    
    def _calculate_offer_prices(self, property_data: PropertyDB, analysis: Optional[PropertyAnalysisDB], 
                               market_condition: MarketConditionEnum, seller_motivation: SellerMotivationEnum) -> Dict[str, float]:
        """Calculate recommended and maximum offer prices."""
        try:
            # Base price from analysis or listing price
            if analysis and analysis.current_value_estimate:
                base_price = analysis.current_value_estimate
            elif property_data.listing_price:
                base_price = property_data.listing_price
            elif property_data.assessed_value:
                base_price = property_data.assessed_value
            else:
                raise ValueError("No price reference available for offer calculation")
            
            # Market condition adjustments
            market_multiplier = {
                MarketConditionEnum.BUYERS_MARKET: 0.85,
                MarketConditionEnum.BALANCED: 0.90,
                MarketConditionEnum.SELLERS_MARKET: 0.95
            }[market_condition]
            
            # Seller motivation adjustments
            motivation_multiplier = {
                SellerMotivationEnum.URGENT: 0.80,
                SellerMotivationEnum.HIGH: 0.85,
                SellerMotivationEnum.MODERATE: 0.90,
                SellerMotivationEnum.LOW: 0.95
            }[seller_motivation]
            
            # Calculate recommended offer (conservative)
            recommended_offer = base_price * market_multiplier * motivation_multiplier
            
            # Calculate maximum offer (10% higher than recommended)
            max_offer = recommended_offer * 1.10
            
            # Ensure max offer doesn't exceed base price
            max_offer = min(max_offer, base_price * 0.98)
            
            return {
                "recommended": round(recommended_offer, -2),  # Round to nearest $100
                "maximum": round(max_offer, -2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating offer prices: {str(e)}")
            # Fallback to simple calculation
            fallback_price = property_data.listing_price or property_data.assessed_value or 200000
            return {
                "recommended": round(fallback_price * 0.85, -2),
                "maximum": round(fallback_price * 0.92, -2)
            }
    
    def _determine_negotiation_approach(self, market_condition: MarketConditionEnum, 
                                      seller_motivation: SellerMotivationEnum) -> str:
        """Determine the appropriate negotiation approach."""
        if market_condition == MarketConditionEnum.BUYERS_MARKET:
            if seller_motivation in [SellerMotivationEnum.HIGH, SellerMotivationEnum.URGENT]:
                return "aggressive"
            else:
                return "moderate"
        elif market_condition == MarketConditionEnum.SELLERS_MARKET:
            return "conservative"
        else:  # Balanced market
            if seller_motivation == SellerMotivationEnum.URGENT:
                return "moderate"
            else:
                return "conservative"
    
    def _generate_talking_points(self, property_data: PropertyDB, analysis: Optional[PropertyAnalysisDB], 
                               market_condition: MarketConditionEnum) -> List[str]:
        """Generate key talking points for negotiation."""
        talking_points = []
        
        # Market-based talking points
        if market_condition == MarketConditionEnum.BUYERS_MARKET:
            talking_points.append("Current market conditions favor buyers with increased inventory")
            talking_points.append("Properties are taking longer to sell, giving us negotiating leverage")
        
        # Property-specific talking points
        if property_data.days_on_market and property_data.days_on_market > 60:
            talking_points.append(f"Property has been on market for {property_data.days_on_market} days")
        
        if property_data.renovation_needed:
            talking_points.append("Property requires significant renovation investment")
        
        # Financial talking points
        if analysis and analysis.repair_estimate:
            talking_points.append(f"Estimated repair costs of ${analysis.repair_estimate:,.0f} must be factored in")
        
        # Closing and terms talking points
        talking_points.extend([
            "We can offer a quick, hassle-free closing",
            "We're pre-approved buyers with strong financing",
            "We can be flexible on closing date to meet your needs"
        ])
        
        return talking_points
    
    def _generate_value_propositions(self, property_data: PropertyDB, 
                                   market_condition: MarketConditionEnum) -> List[str]:
        """Generate value propositions for the seller."""
        value_props = [
            "Cash offer with no financing contingencies",
            "Quick closing within 2-3 weeks",
            "Purchase property as-is with no repair requests",
            "No real estate agent commissions to pay",
            "Certainty of closing with experienced investor"
        ]
        
        if market_condition == MarketConditionEnum.BUYERS_MARKET:
            value_props.append("Guaranteed sale in uncertain market conditions")
        
        return value_props
    
    def _identify_potential_objections(self, property_data: PropertyDB, offer_prices: Dict[str, float], 
                                     market_condition: MarketConditionEnum) -> List[Dict[str, str]]:
        """Identify potential seller objections and prepare responses."""
        objections = []
        
        # Price objection
        if property_data.listing_price and offer_prices["recommended"] < property_data.listing_price:
            discount_pct = (1 - offer_prices["recommended"] / property_data.listing_price) * 100
            objections.append({
                "objection": f"Your offer is {discount_pct:.1f}% below asking price",
                "response": "Our offer reflects current market conditions and the property's condition. We can close quickly with no contingencies."
            })
        
        # Market objections
        objections.extend([
            {
                "objection": "I think I can get more money from another buyer",
                "response": "While that's possible, we offer certainty and speed. A bird in the hand is worth two in the bush."
            },
            {
                "objection": "I need more time to think about it",
                "response": "I understand this is a big decision. Our offer is good for 48 hours to ensure we can move quickly for you."
            },
            {
                "objection": "The property is worth more than your offer",
                "response": "We've done extensive market analysis. Our offer accounts for current market conditions and necessary repairs."
            }
        ])
        
        return objections
    
    def _recommend_contingencies(self, property_data: PropertyDB, 
                               market_condition: MarketConditionEnum) -> List[str]:
        """Recommend appropriate contingencies for the offer."""
        contingencies = []
        
        # Standard contingencies
        if market_condition != MarketConditionEnum.SELLERS_MARKET:
            contingencies.extend([
                "10-day inspection contingency",
                "Appraisal contingency (if financing)"
            ])
        
        # Property-specific contingencies
        if property_data.year_built and property_data.year_built < 1980:
            contingencies.append("Lead paint inspection")
        
        if not property_data.renovation_needed:
            contingencies.append("7-day inspection for major systems only")
        
        return contingencies
    
    def _assess_negotiation_risks(self, property_data: PropertyDB, market_condition: MarketConditionEnum, 
                                seller_motivation: SellerMotivationEnum) -> Dict[str, Any]:
        """Assess risks associated with the negotiation."""
        risks = {
            "overall_risk": "medium",
            "risk_factors": [],
            "mitigation_strategies": []
        }
        
        # Market risks
        if market_condition == MarketConditionEnum.SELLERS_MARKET:
            risks["risk_factors"].append("Competitive market may lead to bidding war")
            risks["mitigation_strategies"].append("Be prepared to increase offer quickly")
        
        # Seller motivation risks
        if seller_motivation == SellerMotivationEnum.LOW:
            risks["risk_factors"].append("Seller may not be motivated to negotiate")
            risks["mitigation_strategies"].append("Focus on non-price benefits and convenience")
        
        # Property risks
        if property_data.renovation_needed:
            risks["risk_factors"].append("Unknown repair costs may exceed estimates")
            risks["mitigation_strategies"].append("Include thorough inspection contingency")
        
        # Calculate overall risk level
        risk_score = len(risks["risk_factors"])
        if risk_score >= 3:
            risks["overall_risk"] = "high"
        elif risk_score <= 1:
            risks["overall_risk"] = "low"
        
        return risks
    
    def _calculate_confidence_score(self, property_data: PropertyDB, analysis: Optional[PropertyAnalysisDB],
                                  market_condition: MarketConditionEnum, seller_motivation: SellerMotivationEnum) -> float:
        """Calculate confidence score for the negotiation strategy."""
        confidence = 0.5  # Base confidence
        
        # Data quality factors
        if analysis:
            confidence += 0.2
        if property_data.days_on_market:
            confidence += 0.1
        if property_data.listing_price:
            confidence += 0.1
        
        # Market factors
        if market_condition == MarketConditionEnum.BUYERS_MARKET:
            confidence += 0.1
        elif market_condition == MarketConditionEnum.SELLERS_MARKET:
            confidence -= 0.1
        
        # Seller motivation factors
        if seller_motivation in [SellerMotivationEnum.HIGH, SellerMotivationEnum.URGENT]:
            confidence += 0.1
        elif seller_motivation == SellerMotivationEnum.LOW:
            confidence -= 0.1
        
        return min(max(confidence, 0.0), 1.0)  # Clamp between 0 and 1
    
    def _calculate_dom_factor(self, property_data: PropertyDB) -> Optional[float]:
        """Calculate days on market factor."""
        if not property_data.days_on_market:
            return None
        
        # Normalize DOM to a 0-1 scale (180 days = 1.0)
        return min(property_data.days_on_market / 180.0, 1.0)
    
    def _calculate_comp_factor(self, analysis: Optional[PropertyAnalysisDB]) -> Optional[float]:
        """Calculate comparable sales factor."""
        if not analysis or not analysis.comparable_count:
            return None
        
        # More comps = higher confidence (10 comps = 1.0)
        return min(analysis.comparable_count / 10.0, 1.0)
    
    def save_strategy(self, strategy_data: Dict[str, Any]) -> NegotiationStrategyDB:
        """Save a negotiation strategy to the database."""
        try:
            strategy = NegotiationStrategyDB(**strategy_data)
            self.db.add(strategy)
            self.db.commit()
            self.db.refresh(strategy)
            
            logger.info(f"Saved negotiation strategy {strategy.id} for property {strategy.property_id}")
            return strategy
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving negotiation strategy: {str(e)}")
            raise
    
    def get_strategy(self, strategy_id: uuid.UUID) -> Optional[NegotiationStrategyDB]:
        """Get a negotiation strategy by ID."""
        return self.db.query(NegotiationStrategyDB).filter(
            NegotiationStrategyDB.id == strategy_id
        ).first()
    
    def get_strategies_for_property(self, property_id: uuid.UUID) -> List[NegotiationStrategyDB]:
        """Get all negotiation strategies for a property."""
        return self.db.query(NegotiationStrategyDB).filter(
            NegotiationStrategyDB.property_id == property_id
        ).order_by(NegotiationStrategyDB.created_at.desc()).all()
    
    def update_strategy_with_market_changes(self, strategy_id: uuid.UUID) -> NegotiationStrategyDB:
        """Update an existing strategy with current market conditions."""
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            raise ValueError(f"Strategy with ID {strategy_id} not found")
        
        # Regenerate strategy with current data
        updated_strategy_data = self.generate_strategy(strategy.property_id)
        
        # Update existing strategy
        for key, value in updated_strategy_data.items():
            if key != "property_id":  # Don't update the property_id
                setattr(strategy, key, value)
        
        strategy.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(strategy)
        
        logger.info(f"Updated negotiation strategy {strategy_id} with current market data")
        return strategy