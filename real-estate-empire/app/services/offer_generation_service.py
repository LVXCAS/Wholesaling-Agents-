"""
Offer Generation Service for creating AI-powered real estate offers.
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
    OfferDB,
    OfferCreate,
    OfferTypeEnum,
    NegotiationStatusEnum,
    MarketConditionEnum,
    SellerMotivationEnum
)

logger = logging.getLogger(__name__)


class OfferGenerationService:
    """Service for generating and managing real estate offers."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_offer(self, strategy_id: uuid.UUID, offer_type: OfferTypeEnum = OfferTypeEnum.INITIAL) -> Dict[str, Any]:
        """
        Generate a comprehensive offer based on a negotiation strategy.
        
        Args:
            strategy_id: UUID of the negotiation strategy to base offer on
            offer_type: Type of offer to generate (initial, counter, final, backup)
            
        Returns:
            Dict containing the generated offer details
        """
        try:
            # Get negotiation strategy
            strategy = self.db.query(NegotiationStrategyDB).filter(
                NegotiationStrategyDB.id == strategy_id
            ).first()
            
            if not strategy:
                raise ValueError(f"Negotiation strategy with ID {strategy_id} not found")
            
            # Get property data
            property_data = self.db.query(PropertyDB).filter(
                PropertyDB.id == strategy.property_id
            ).first()
            
            if not property_data:
                raise ValueError(f"Property with ID {strategy.property_id} not found")
            
            # Get property analysis if available
            analysis = self.db.query(PropertyAnalysisDB).filter(
                PropertyAnalysisDB.property_id == strategy.property_id
            ).first()
            
            # Calculate offer price based on strategy and offer type
            offer_price = self._calculate_offer_price(strategy, offer_type)
            
            # Calculate earnest money
            earnest_money = self._calculate_earnest_money(offer_price, strategy.market_condition)
            
            # Calculate down payment
            down_payment = self._calculate_down_payment(offer_price, strategy.negotiation_approach)
            
            # Determine financing type
            financing_type = self._determine_financing_type(strategy.negotiation_approach)
            
            # Calculate closing date
            closing_date = self._calculate_closing_date(strategy.market_condition, strategy.seller_motivation)
            
            # Determine inspection period
            inspection_period = self._determine_inspection_period(property_data, strategy.market_condition)
            
            # Determine contingencies
            contingencies_config = self._determine_contingencies(property_data, strategy, offer_type)
            
            # Generate custom terms
            custom_terms = self._generate_custom_terms(property_data, strategy, offer_type)
            
            # Generate contingency list
            contingency_list = self._generate_contingency_list(property_data, strategy, offer_type)
            
            offer_data = {
                "strategy_id": strategy_id,
                "property_id": strategy.property_id,
                "offer_type": offer_type,
                "offer_amount": offer_price,
                "earnest_money": earnest_money,
                "down_payment": down_payment,
                "financing_type": financing_type,
                "closing_date": closing_date,
                "inspection_period": inspection_period,
                "appraisal_contingency": contingencies_config["appraisal"],
                "financing_contingency": contingencies_config["financing"],
                "inspection_contingency": contingencies_config["inspection"],
                "custom_terms": custom_terms,
                "contingencies": contingency_list,
                "status": NegotiationStatusEnum.INITIATED
            }
            
            logger.info(f"Generated {offer_type} offer for property {strategy.property_id}")
            return offer_data
            
        except Exception as e:
            logger.error(f"Error generating offer for strategy {strategy_id}: {str(e)}")
            raise
    
    def _calculate_offer_price(self, strategy: NegotiationStrategyDB, offer_type: OfferTypeEnum) -> float:
        """Calculate the offer price based on strategy and offer type."""
        base_price = strategy.recommended_offer_price
        max_price = strategy.max_offer_price
        
        # Adjust price based on offer type
        if offer_type == OfferTypeEnum.INITIAL:
            # Start with recommended price
            return base_price
        elif offer_type == OfferTypeEnum.COUNTER:
            # Increase by 2-5% for counter offers
            increase_pct = 0.03 if strategy.negotiation_approach == "aggressive" else 0.02
            return min(base_price * (1 + increase_pct), max_price)
        elif offer_type == OfferTypeEnum.FINAL:
            # Use maximum price for final offers
            return max_price
        elif offer_type == OfferTypeEnum.BACKUP:
            # Slightly higher than recommended for backup offers
            return min(base_price * 1.01, max_price)
        else:
            return base_price
    
    def _calculate_earnest_money(self, offer_price: float, market_condition: MarketConditionEnum) -> float:
        """Calculate appropriate earnest money amount."""
        # Base earnest money percentage
        base_pct = {
            MarketConditionEnum.BUYERS_MARKET: 0.01,    # 1% in buyer's market
            MarketConditionEnum.BALANCED: 0.015,        # 1.5% in balanced market
            MarketConditionEnum.SELLERS_MARKET: 0.02    # 2% in seller's market
        }[market_condition]
        
        earnest_amount = offer_price * base_pct
        
        # Round to nearest $500
        return round(earnest_amount / 500) * 500
    
    def _calculate_down_payment(self, offer_price: float, negotiation_approach: str) -> float:
        """Calculate down payment amount."""
        # Down payment percentage based on approach
        down_pct = {
            "aggressive": 0.20,    # 20% for aggressive (strong offer)
            "moderate": 0.15,      # 15% for moderate
            "conservative": 0.10   # 10% for conservative
        }.get(negotiation_approach, 0.15)
        
        return offer_price * down_pct
    
    def _determine_financing_type(self, negotiation_approach: str) -> str:
        """Determine the best financing type for the offer."""
        if negotiation_approach == "aggressive":
            return "cash"
        elif negotiation_approach == "moderate":
            return "conventional"
        else:
            return "conventional"
    
    def _calculate_closing_date(self, market_condition: MarketConditionEnum, 
                               seller_motivation: SellerMotivationEnum) -> datetime:
        """Calculate optimal closing date."""
        base_days = 30  # Default 30 days
        
        # Adjust based on market conditions
        if market_condition == MarketConditionEnum.SELLERS_MARKET:
            base_days = 21  # Faster closing in seller's market
        elif market_condition == MarketConditionEnum.BUYERS_MARKET:
            base_days = 45  # More time in buyer's market
        
        # Adjust based on seller motivation
        if seller_motivation == SellerMotivationEnum.URGENT:
            base_days = min(base_days, 14)  # Very fast closing for urgent sellers
        elif seller_motivation == SellerMotivationEnum.HIGH:
            base_days = min(base_days, 21)  # Fast closing for motivated sellers
        
        return datetime.now() + timedelta(days=base_days)
    
    def _determine_inspection_period(self, property_data: PropertyDB, 
                                   market_condition: MarketConditionEnum) -> int:
        """Determine appropriate inspection period in days."""
        base_days = 10  # Default 10 days
        
        # Adjust based on market conditions
        if market_condition == MarketConditionEnum.SELLERS_MARKET:
            base_days = 7   # Shorter inspection in seller's market
        elif market_condition == MarketConditionEnum.BUYERS_MARKET:
            base_days = 14  # Longer inspection in buyer's market
        
        # Adjust based on property characteristics
        if property_data.year_built and property_data.year_built < 1980:
            base_days += 3  # More time for older properties
        
        if property_data.renovation_needed:
            base_days += 2  # More time for properties needing work
        
        return base_days
    
    def _determine_contingencies(self, property_data: PropertyDB, strategy: NegotiationStrategyDB, 
                               offer_type: OfferTypeEnum) -> Dict[str, bool]:
        """Determine which contingencies to include."""
        contingencies = {
            "appraisal": True,
            "financing": True,
            "inspection": True
        }
        
        # Adjust based on market conditions and approach
        if strategy.market_condition == MarketConditionEnum.SELLERS_MARKET:
            if strategy.negotiation_approach == "aggressive":
                contingencies["appraisal"] = False  # Waive appraisal in competitive market
            if offer_type == OfferTypeEnum.FINAL:
                contingencies["inspection"] = False  # Waive inspection for final offer
        
        # Cash offers don't need financing contingency
        financing_type = self._determine_financing_type(strategy.negotiation_approach)
        if financing_type == "cash":
            contingencies["financing"] = False
        
        return contingencies
    
    def _generate_custom_terms(self, property_data: PropertyDB, strategy: NegotiationStrategyDB, 
                             offer_type: OfferTypeEnum) -> Dict[str, Any]:
        """Generate custom terms for the offer."""
        custom_terms = {}
        
        # Seller concessions
        if strategy.market_condition == MarketConditionEnum.BUYERS_MARKET:
            custom_terms["seller_concessions"] = min(strategy.recommended_offer_price * 0.03, 5000)
        
        # Rent-back option for motivated sellers
        if strategy.seller_motivation in [SellerMotivationEnum.HIGH, SellerMotivationEnum.URGENT]:
            custom_terms["rent_back_days"] = 30
            custom_terms["rent_back_rate"] = "market_rate"
        
        # As-is purchase for distressed properties
        if property_data.renovation_needed:
            custom_terms["as_is_purchase"] = True
            custom_terms["no_repair_requests"] = True
        
        # Quick close bonus
        if offer_type == OfferTypeEnum.FINAL and strategy.seller_motivation == SellerMotivationEnum.URGENT:
            custom_terms["quick_close_bonus"] = 1000
        
        return custom_terms
    
    def _generate_contingency_list(self, property_data: PropertyDB, strategy: NegotiationStrategyDB, 
                                 offer_type: OfferTypeEnum) -> List[str]:
        """Generate a list of specific contingencies."""
        contingencies = []
        
        # Standard contingencies
        if strategy.market_condition != MarketConditionEnum.SELLERS_MARKET or offer_type != OfferTypeEnum.FINAL:
            contingencies.append(f"{self._determine_inspection_period(property_data, strategy.market_condition)}-day inspection contingency")
        
        # Property-specific contingencies
        if property_data.year_built and property_data.year_built < 1980:
            contingencies.append("Lead-based paint inspection")
        
        if property_data.property_type == "single_family" and not property_data.renovation_needed:
            contingencies.append("Termite inspection")
        
        # Financing contingencies
        financing_type = self._determine_financing_type(strategy.negotiation_approach)
        if financing_type != "cash":
            contingencies.append(f"{financing_type.title()} loan approval contingency")
        
        # Title contingencies
        contingencies.append("Clear title contingency")
        
        # HOA contingencies if applicable
        if property_data.property_type in ["condo", "townhouse"]:
            contingencies.append("HOA document review contingency")
        
        return contingencies
    
    def generate_multiple_offer_strategy(self, strategy_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Generate multiple offer scenarios for a single property.
        
        Args:
            strategy_id: UUID of the negotiation strategy
            
        Returns:
            List of offer scenarios with different terms
        """
        try:
            offers = []
            
            # Generate primary offer
            primary_offer = self.generate_offer(strategy_id, OfferTypeEnum.INITIAL)
            primary_offer["scenario_name"] = "Primary Offer"
            primary_offer["scenario_description"] = "Our main offer with standard terms"
            offers.append(primary_offer)
            
            # Generate aggressive offer (higher price, fewer contingencies)
            aggressive_offer = self.generate_offer(strategy_id, OfferTypeEnum.FINAL)
            aggressive_offer["scenario_name"] = "Aggressive Offer"
            aggressive_offer["scenario_description"] = "Higher price with minimal contingencies"
            offers.append(aggressive_offer)
            
            # Generate conservative offer (lower price, more contingencies)
            strategy = self.db.query(NegotiationStrategyDB).filter(
                NegotiationStrategyDB.id == strategy_id
            ).first()
            
            if strategy:
                conservative_offer = primary_offer.copy()
                conservative_offer["offer_amount"] = strategy.recommended_offer_price * 0.95
                conservative_offer["scenario_name"] = "Conservative Offer"
                conservative_offer["scenario_description"] = "Lower price with full contingencies"
                conservative_offer["inspection_period"] = 14
                conservative_offer["appraisal_contingency"] = True
                conservative_offer["financing_contingency"] = True
                conservative_offer["inspection_contingency"] = True
                offers.append(conservative_offer)
            
            logger.info(f"Generated {len(offers)} offer scenarios for strategy {strategy_id}")
            return offers
            
        except Exception as e:
            logger.error(f"Error generating multiple offer strategy: {str(e)}")
            raise
    
    def save_offer(self, offer_data: Dict[str, Any]) -> OfferDB:
        """Save an offer to the database."""
        try:
            offer = OfferDB(**offer_data)
            self.db.add(offer)
            self.db.commit()
            self.db.refresh(offer)
            
            logger.info(f"Saved offer {offer.id} for property {offer.property_id}")
            return offer
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving offer: {str(e)}")
            raise
    
    def get_offer(self, offer_id: uuid.UUID) -> Optional[OfferDB]:
        """Get an offer by ID."""
        return self.db.query(OfferDB).filter(OfferDB.id == offer_id).first()
    
    def get_offers_for_property(self, property_id: uuid.UUID) -> List[OfferDB]:
        """Get all offers for a property."""
        return self.db.query(OfferDB).filter(
            OfferDB.property_id == property_id
        ).order_by(OfferDB.created_at.desc()).all()
    
    def get_offers_for_strategy(self, strategy_id: uuid.UUID) -> List[OfferDB]:
        """Get all offers for a negotiation strategy."""
        return self.db.query(OfferDB).filter(
            OfferDB.strategy_id == strategy_id
        ).order_by(OfferDB.created_at.desc()).all()
    
    def update_offer_status(self, offer_id: uuid.UUID, status: NegotiationStatusEnum, 
                           response_details: Optional[Dict[str, Any]] = None) -> OfferDB:
        """Update the status of an offer."""
        try:
            offer = self.get_offer(offer_id)
            if not offer:
                raise ValueError(f"Offer with ID {offer_id} not found")
            
            offer.status = status
            offer.updated_at = datetime.utcnow()
            
            if response_details:
                offer.response_received = True
                offer.response_date = datetime.utcnow()
                offer.response_details = response_details
            
            self.db.commit()
            self.db.refresh(offer)
            
            logger.info(f"Updated offer {offer_id} status to {status}")
            return offer
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating offer status: {str(e)}")
            raise
    
    def calculate_offer_competitiveness(self, offer_data: Dict[str, Any], 
                                      market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculate how competitive an offer is in the current market.
        
        Args:
            offer_data: The offer details
            market_data: Optional market data for comparison
            
        Returns:
            Dict with competitiveness analysis
        """
        try:
            # Get property data
            property_data = self.db.query(PropertyDB).filter(
                PropertyDB.id == offer_data["property_id"]
            ).first()
            
            if not property_data:
                raise ValueError("Property not found for competitiveness analysis")
            
            competitiveness = {
                "overall_score": 0.0,  # 0-100 scale
                "strengths": [],
                "weaknesses": [],
                "recommendations": []
            }
            
            # Price competitiveness (40% of score)
            price_score = self._analyze_price_competitiveness(offer_data, property_data)
            competitiveness["overall_score"] += price_score * 0.4
            
            # Terms competitiveness (30% of score)
            terms_score = self._analyze_terms_competitiveness(offer_data)
            competitiveness["overall_score"] += terms_score * 0.3
            
            # Financing competitiveness (20% of score)
            financing_score = self._analyze_financing_competitiveness(offer_data)
            competitiveness["overall_score"] += financing_score * 0.2
            
            # Timeline competitiveness (10% of score)
            timeline_score = self._analyze_timeline_competitiveness(offer_data)
            competitiveness["overall_score"] += timeline_score * 0.1
            
            # Generate recommendations
            competitiveness["recommendations"] = self._generate_competitiveness_recommendations(
                offer_data, competitiveness["overall_score"]
            )
            
            return competitiveness
            
        except Exception as e:
            logger.error(f"Error calculating offer competitiveness: {str(e)}")
            raise
    
    def _analyze_price_competitiveness(self, offer_data: Dict[str, Any], property_data: PropertyDB) -> float:
        """Analyze price competitiveness (0-100 score)."""
        if not property_data.listing_price:
            return 50.0  # Neutral score if no listing price
        
        price_ratio = offer_data["offer_amount"] / property_data.listing_price
        
        if price_ratio >= 1.0:
            return 100.0  # Full price or above
        elif price_ratio >= 0.95:
            return 85.0   # 95%+ of asking
        elif price_ratio >= 0.90:
            return 70.0   # 90-95% of asking
        elif price_ratio >= 0.85:
            return 50.0   # 85-90% of asking
        else:
            return 25.0   # Below 85% of asking
    
    def _analyze_terms_competitiveness(self, offer_data: Dict[str, Any]) -> float:
        """Analyze terms competitiveness (0-100 score)."""
        score = 50.0  # Base score
        
        # Contingency analysis
        if not offer_data.get("appraisal_contingency", True):
            score += 15  # Waiving appraisal is competitive
        if not offer_data.get("inspection_contingency", True):
            score += 20  # Waiving inspection is very competitive
        if not offer_data.get("financing_contingency", True):
            score += 10  # Waiving financing is competitive
        
        # Custom terms analysis
        custom_terms = offer_data.get("custom_terms", {})
        if custom_terms.get("as_is_purchase"):
            score += 10
        if custom_terms.get("rent_back_days"):
            score += 5
        if custom_terms.get("quick_close_bonus"):
            score += 5
        
        return min(score, 100.0)
    
    def _analyze_financing_competitiveness(self, offer_data: Dict[str, Any]) -> float:
        """Analyze financing competitiveness (0-100 score)."""
        financing_type = offer_data.get("financing_type", "conventional")
        
        if financing_type == "cash":
            return 100.0  # Cash is most competitive
        elif financing_type == "conventional":
            return 80.0   # Conventional is good
        elif financing_type == "fha":
            return 60.0   # FHA is less competitive
        else:
            return 50.0   # Other financing types
    
    def _analyze_timeline_competitiveness(self, offer_data: Dict[str, Any]) -> float:
        """Analyze timeline competitiveness (0-100 score)."""
        closing_date = offer_data.get("closing_date")
        if not closing_date:
            return 50.0
        
        if isinstance(closing_date, str):
            closing_date = datetime.fromisoformat(closing_date.replace('Z', '+00:00'))
        
        days_to_close = (closing_date - datetime.now()).days
        
        if days_to_close <= 14:
            return 100.0  # Very fast closing
        elif days_to_close <= 21:
            return 85.0   # Fast closing
        elif days_to_close <= 30:
            return 70.0   # Standard closing
        elif days_to_close <= 45:
            return 50.0   # Slower closing
        else:
            return 25.0   # Very slow closing
    
    def _generate_competitiveness_recommendations(self, offer_data: Dict[str, Any], 
                                                overall_score: float) -> List[str]:
        """Generate recommendations to improve offer competitiveness."""
        recommendations = []
        
        if overall_score < 60:
            recommendations.append("Consider increasing offer price to be more competitive")
        
        if offer_data.get("appraisal_contingency", True):
            recommendations.append("Consider waiving appraisal contingency if comfortable with price")
        
        if offer_data.get("financing_type") != "cash":
            recommendations.append("Cash offer would significantly improve competitiveness")
        
        closing_date = offer_data.get("closing_date")
        if closing_date:
            if isinstance(closing_date, str):
                closing_date = datetime.fromisoformat(closing_date.replace('Z', '+00:00'))
            days_to_close = (closing_date - datetime.now()).days
            if days_to_close > 30:
                recommendations.append("Shorter closing timeline would improve competitiveness")
        
        if not offer_data.get("custom_terms", {}).get("as_is_purchase"):
            recommendations.append("Consider offering to purchase 'as-is' for distressed properties")
        
        return recommendations