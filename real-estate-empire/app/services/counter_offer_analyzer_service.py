"""
Counter Offer Analyzer Service for analyzing and responding to seller counter offers.
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import json

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.property import PropertyDB, PropertyAnalysisDB
from app.models.negotiation import (
    NegotiationStrategyDB,
    OfferDB,
    CounterOfferDB,
    CounterOfferCreate,
    NegotiationStatusEnum,
    MarketConditionEnum,
    SellerMotivationEnum
)

logger = logging.getLogger(__name__)


class CounterOfferAnalyzerService:
    """Service for analyzing counter offers and generating response recommendations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _serialize_for_json(self, obj: Any) -> Any:
        """Recursively convert datetime objects to ISO strings for JSON serialization."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._serialize_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_for_json(item) for item in obj]
        else:
            return obj
    
    def analyze_counter_offer(self, original_offer_id: uuid.UUID, counter_offer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a counter offer and provide recommendations.
        
        Args:
            original_offer_id: UUID of the original offer
            counter_offer_data: Counter offer details from seller
            
        Returns:
            Dict containing analysis results and recommendations
        """
        try:
            # Get original offer
            original_offer = self.db.query(OfferDB).filter(
                OfferDB.id == original_offer_id
            ).first()
            
            if not original_offer:
                raise ValueError(f"Original offer with ID {original_offer_id} not found")
            
            # Get negotiation strategy
            strategy = self.db.query(NegotiationStrategyDB).filter(
                NegotiationStrategyDB.id == original_offer.strategy_id
            ).first()
            
            if not strategy:
                raise ValueError(f"Negotiation strategy not found for offer {original_offer_id}")
            
            # Get property data
            property_data = self.db.query(PropertyDB).filter(
                PropertyDB.id == original_offer.property_id
            ).first()
            
            if not property_data:
                raise ValueError(f"Property not found for offer {original_offer_id}")
            
            # Extract counter offer details
            counter_amount = counter_offer_data.get("counter_amount", 0)
            seller_changes = counter_offer_data.get("seller_changes", {})
            
            # Perform comprehensive analysis
            price_analysis = self._analyze_price_change(original_offer, counter_amount, strategy)
            terms_analysis = self._analyze_terms_changes(original_offer, seller_changes, strategy)
            risk_assessment = self._assess_counter_offer_risks(original_offer, counter_offer_data, strategy, property_data)
            negotiation_path = self._predict_negotiation_path(original_offer, counter_offer_data, strategy)
            
            # Generate response recommendation
            response_recommendation = self._generate_response_recommendation(
                price_analysis, terms_analysis, risk_assessment, strategy
            )
            
            # Calculate deal viability
            deal_viability = self._calculate_deal_viability(counter_offer_data, strategy, property_data)
            
            analysis_result = {
                "original_offer_id": original_offer_id,
                "counter_amount": counter_amount,
                "price_analysis": price_analysis,
                "terms_analysis": terms_analysis,
                "risk_assessment": risk_assessment,
                "negotiation_path": negotiation_path,
                "response_recommendation": response_recommendation,
                "deal_viability": deal_viability,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "confidence_score": self._calculate_analysis_confidence(price_analysis, terms_analysis, risk_assessment)
            }
            
            # Serialize datetime objects for JSON storage
            analysis_result = self._serialize_for_json(analysis_result)
            
            logger.info(f"Analyzed counter offer for original offer {original_offer_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing counter offer for offer {original_offer_id}: {str(e)}")
            raise
    
    def _analyze_price_change(self, original_offer: OfferDB, counter_amount: float, 
                             strategy: NegotiationStrategyDB) -> Dict[str, Any]:
        """Analyze the price change in the counter offer."""
        original_amount = original_offer.offer_amount
        price_difference = counter_amount - original_amount
        price_change_pct = (price_difference / original_amount) * 100
        
        # Determine if counter is within acceptable range
        max_acceptable = strategy.max_offer_price
        within_budget = counter_amount <= max_acceptable
        
        # Calculate negotiation room
        negotiation_room = max_acceptable - counter_amount if within_budget else 0
        
        # Assess price competitiveness
        if counter_amount <= strategy.recommended_offer_price:
            competitiveness = "excellent"
        elif counter_amount <= strategy.max_offer_price:
            competitiveness = "good"
        elif counter_amount <= strategy.max_offer_price * 1.05:
            competitiveness = "marginal"
        else:
            competitiveness = "poor"
        
        return {
            "original_amount": original_amount,
            "counter_amount": counter_amount,
            "price_difference": price_difference,
            "price_change_percentage": round(price_change_pct, 2),
            "within_budget": within_budget,
            "negotiation_room": negotiation_room,
            "competitiveness": competitiveness,
            "max_acceptable": max_acceptable,
            "distance_from_max": max_acceptable - counter_amount
        }
    
    def _analyze_terms_changes(self, original_offer: OfferDB, seller_changes: Dict[str, Any], 
                              strategy: NegotiationStrategyDB) -> Dict[str, Any]:
        """Analyze changes to terms and conditions."""
        terms_analysis = {
            "closing_date_change": None,
            "contingency_changes": [],
            "custom_terms_changes": [],
            "overall_terms_impact": "neutral",
            "terms_acceptability": "acceptable"
        }
        
        # Analyze closing date changes
        if "closing_date" in seller_changes:
            requested_date = seller_changes["closing_date"]
            if isinstance(requested_date, str):
                requested_date = datetime.fromisoformat(requested_date.replace('Z', '+00:00'))
            
            original_date = original_offer.closing_date
            if original_date:
                date_difference = (requested_date - original_date).days
                terms_analysis["closing_date_change"] = {
                    "original_date": original_date,
                    "requested_date": requested_date,
                    "days_difference": date_difference,
                    "impact": "positive" if date_difference < 0 else "negative" if date_difference > 7 else "neutral"
                }
        
        # Analyze contingency changes
        contingency_fields = ["appraisal_contingency", "financing_contingency", "inspection_contingency"]
        for field in contingency_fields:
            if field in seller_changes:
                original_value = getattr(original_offer, field, True)
                requested_value = seller_changes[field]
                if original_value != requested_value:
                    terms_analysis["contingency_changes"].append({
                        "contingency": field,
                        "original": original_value,
                        "requested": requested_value,
                        "impact": "negative" if original_value and not requested_value else "positive"
                    })
        
        # Analyze custom terms changes
        if "custom_terms" in seller_changes:
            for term, value in seller_changes["custom_terms"].items():
                terms_analysis["custom_terms_changes"].append({
                    "term": term,
                    "value": value,
                    "impact": self._assess_custom_term_impact(term, value)
                })
        
        # Calculate overall terms impact
        negative_impacts = sum(1 for change in terms_analysis["contingency_changes"] if change["impact"] == "negative")
        positive_impacts = sum(1 for change in terms_analysis["contingency_changes"] if change["impact"] == "positive")
        
        if negative_impacts > positive_impacts:
            terms_analysis["overall_terms_impact"] = "negative"
            terms_analysis["terms_acceptability"] = "concerning" if negative_impacts > 2 else "marginal"
        elif positive_impacts > negative_impacts:
            terms_analysis["overall_terms_impact"] = "positive"
            terms_analysis["terms_acceptability"] = "excellent"
        
        return terms_analysis
    
    def _assess_custom_term_impact(self, term: str, value: Any) -> str:
        """Assess the impact of a custom term change."""
        negative_terms = ["seller_concessions", "repair_credits", "warranty_requirements"]
        positive_terms = ["rent_back_days", "flexible_closing", "as_is_acceptance"]
        
        if term in negative_terms:
            return "negative"
        elif term in positive_terms:
            return "positive"
        else:
            return "neutral"
    
    def _assess_counter_offer_risks(self, original_offer: OfferDB, counter_offer_data: Dict[str, Any],
                                   strategy: NegotiationStrategyDB, property_data: PropertyDB) -> Dict[str, Any]:
        """Assess risks associated with the counter offer."""
        risks = {
            "financial_risks": [],
            "timeline_risks": [],
            "market_risks": [],
            "property_risks": [],
            "overall_risk_level": "low",
            "risk_mitigation_strategies": []
        }
        
        counter_amount = counter_offer_data.get("counter_amount", 0)
        
        # Financial risks
        if counter_amount > strategy.max_offer_price:
            risks["financial_risks"].append({
                "risk": "Price exceeds maximum budget",
                "severity": "high",
                "impact": f"${counter_amount - strategy.max_offer_price:,.0f} over budget"
            })
        
        if counter_amount > original_offer.offer_amount * 1.1:
            risks["financial_risks"].append({
                "risk": "Significant price increase",
                "severity": "medium",
                "impact": f"{((counter_amount / original_offer.offer_amount) - 1) * 100:.1f}% increase"
            })
        
        # Timeline risks
        seller_changes = counter_offer_data.get("seller_changes", {})
        if "closing_date" in seller_changes:
            requested_date = seller_changes["closing_date"]
            if isinstance(requested_date, str):
                requested_date = datetime.fromisoformat(requested_date.replace('Z', '+00:00'))
            
            if (requested_date - datetime.now()).days > 60:
                risks["timeline_risks"].append({
                    "risk": "Extended closing timeline",
                    "severity": "medium",
                    "impact": "Increased market exposure and potential for deal failure"
                })
        
        # Market risks
        if strategy.market_condition == MarketConditionEnum.SELLERS_MARKET:
            risks["market_risks"].append({
                "risk": "Seller's market conditions",
                "severity": "medium",
                "impact": "Limited negotiation leverage, potential for competing offers"
            })
        
        # Property risks
        if property_data.renovation_needed and "inspection_contingency" in seller_changes:
            if not seller_changes["inspection_contingency"]:
                risks["property_risks"].append({
                    "risk": "Waiving inspection on property needing repairs",
                    "severity": "high",
                    "impact": "Potential for unknown repair costs"
                })
        
        # Calculate overall risk level
        high_risks = sum(1 for category in risks.values() if isinstance(category, list) 
                        for risk in category if isinstance(risk, dict) and risk.get("severity") == "high")
        medium_risks = sum(1 for category in risks.values() if isinstance(category, list)
                          for risk in category if isinstance(risk, dict) and risk.get("severity") == "medium")
        
        if high_risks > 0:
            risks["overall_risk_level"] = "high"
        elif medium_risks > 2:
            risks["overall_risk_level"] = "high"
        elif medium_risks > 0:
            risks["overall_risk_level"] = "medium"
        
        # Generate risk mitigation strategies
        risks["risk_mitigation_strategies"] = self._generate_risk_mitigation_strategies(risks)
        
        return risks
    
    def _generate_risk_mitigation_strategies(self, risks: Dict[str, Any]) -> List[str]:
        """Generate strategies to mitigate identified risks."""
        strategies = []
        
        # Financial risk mitigation
        for risk in risks.get("financial_risks", []):
            if "exceeds maximum budget" in risk["risk"].lower():
                strategies.append("Consider walking away or significantly reducing other terms")
            elif "significant price increase" in risk["risk"].lower():
                strategies.append("Counter with a smaller price increase and request seller concessions")
        
        # Timeline risk mitigation
        for risk in risks.get("timeline_risks", []):
            if "extended closing" in risk["risk"].lower():
                strategies.append("Negotiate for rate lock extension or seller-paid interest")
        
        # Property risk mitigation
        for risk in risks.get("property_risks", []):
            if "waiving inspection" in risk["risk"].lower():
                strategies.append("Insist on maintaining inspection contingency or request repair credits")
        
        return strategies
    
    def _predict_negotiation_path(self, original_offer: OfferDB, counter_offer_data: Dict[str, Any],
                                 strategy: NegotiationStrategyDB) -> Dict[str, Any]:
        """Predict the likely path of continued negotiation."""
        counter_amount = counter_offer_data.get("counter_amount", 0)
        original_amount = original_offer.offer_amount
        
        # Calculate negotiation progress
        total_gap = strategy.max_offer_price - original_amount
        closed_gap = counter_amount - original_amount
        progress_pct = (closed_gap / total_gap * 100) if total_gap > 0 else 100
        
        # Predict likely outcomes
        if counter_amount <= strategy.max_offer_price:
            likely_outcome = "successful_negotiation"
            success_probability = 0.8
        elif counter_amount <= strategy.max_offer_price * 1.05:
            likely_outcome = "challenging_negotiation"
            success_probability = 0.6
        else:
            likely_outcome = "difficult_negotiation"
            success_probability = 0.3
        
        # Estimate rounds to completion
        price_gap = abs(counter_amount - strategy.max_offer_price)
        if price_gap == 0:
            estimated_rounds = 0
        elif price_gap < original_amount * 0.02:  # Less than 2% of original offer
            estimated_rounds = 1
        elif price_gap < original_amount * 0.05:  # Less than 5% of original offer
            estimated_rounds = 2
        else:
            estimated_rounds = 3
        
        return {
            "negotiation_progress_percentage": round(progress_pct, 1),
            "likely_outcome": likely_outcome,
            "success_probability": success_probability,
            "estimated_rounds_to_completion": estimated_rounds,
            "recommended_next_steps": self._generate_next_steps(likely_outcome, counter_amount, strategy)
        }
    
    def _generate_next_steps(self, likely_outcome: str, counter_amount: float, 
                           strategy: NegotiationStrategyDB) -> List[str]:
        """Generate recommended next steps based on negotiation prediction."""
        steps = []
        
        if likely_outcome == "successful_negotiation":
            if counter_amount <= strategy.recommended_offer_price:
                steps.append("Accept the counter offer immediately")
            else:
                steps.append("Counter with a price slightly below their ask")
                steps.append("Focus on non-price terms to add value")
        
        elif likely_outcome == "challenging_negotiation":
            steps.append("Counter with your maximum price")
            steps.append("Request seller concessions to offset higher price")
            steps.append("Emphasize your strong terms and quick closing")
        
        else:  # difficult_negotiation
            steps.append("Consider walking away if seller won't negotiate")
            steps.append("Present final offer with clear deadline")
            steps.append("Explore creative financing or terms solutions")
        
        return steps
    
    def _generate_response_recommendation(self, price_analysis: Dict[str, Any], 
                                        terms_analysis: Dict[str, Any],
                                        risk_assessment: Dict[str, Any],
                                        strategy: NegotiationStrategyDB) -> Dict[str, Any]:
        """Generate a comprehensive response recommendation."""
        
        # Determine primary recommendation
        if not price_analysis["within_budget"]:
            primary_action = "reject"
            confidence = 0.9
        elif price_analysis["competitiveness"] == "excellent" and terms_analysis["terms_acceptability"] == "acceptable":
            primary_action = "accept"
            confidence = 0.8
        elif risk_assessment["overall_risk_level"] == "high":
            primary_action = "reject"
            confidence = 0.7
        else:
            primary_action = "counter"
            confidence = 0.6
        
        # Generate specific response details
        response_details = self._generate_response_details(primary_action, price_analysis, terms_analysis, strategy)
        
        return {
            "primary_action": primary_action,  # accept, counter, reject
            "confidence": confidence,
            "reasoning": self._generate_reasoning(primary_action, price_analysis, terms_analysis, risk_assessment),
            "response_details": response_details,
            "alternative_approaches": self._generate_alternative_approaches(primary_action, price_analysis, strategy)
        }
    
    def _generate_response_details(self, primary_action: str, price_analysis: Dict[str, Any],
                                 terms_analysis: Dict[str, Any], strategy: NegotiationStrategyDB) -> Dict[str, Any]:
        """Generate specific details for the recommended response."""
        details = {}
        
        if primary_action == "accept":
            details = {
                "message": "Accept the counter offer as presented",
                "justification": "Counter offer meets our criteria and represents good value"
            }
        
        elif primary_action == "counter":
            # Calculate counter offer price
            counter_amount = price_analysis["counter_amount"]
            max_price = strategy.max_offer_price
            
            if counter_amount > max_price:
                suggested_counter = max_price
            else:
                # Split the difference
                original_amount = price_analysis["original_amount"]
                suggested_counter = (counter_amount + original_amount) / 2
                suggested_counter = min(suggested_counter, max_price)
            
            details = {
                "suggested_counter_price": round(suggested_counter, -2),  # Round to nearest $100
                "price_justification": f"Splitting difference while staying within budget of ${max_price:,.0f}",
                "terms_modifications": self._suggest_terms_modifications(terms_analysis),
                "message_tone": "collaborative",
                "deadline": datetime.now() + timedelta(hours=24)
            }
        
        elif primary_action == "reject":
            details = {
                "message": "Respectfully decline the counter offer",
                "justification": "Counter offer exceeds our investment criteria",
                "final_offer_option": {
                    "price": strategy.max_offer_price,
                    "terms": "best and final terms",
                    "deadline": datetime.now() + timedelta(hours=48)
                }
            }
        
        return details
    
    def _suggest_terms_modifications(self, terms_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Suggest modifications to terms based on analysis."""
        modifications = []
        
        # Address negative contingency changes
        for change in terms_analysis.get("contingency_changes", []):
            if change["impact"] == "negative":
                modifications.append({
                    "term": change["contingency"],
                    "suggestion": f"Maintain {change['contingency']} as originally proposed",
                    "reasoning": "Important protection for buyer"
                })
        
        # Address closing date changes
        if terms_analysis.get("closing_date_change") and terms_analysis["closing_date_change"]["impact"] == "negative":
            modifications.append({
                "term": "closing_date",
                "suggestion": "Request original closing date or compromise on timeline",
                "reasoning": "Extended timeline increases deal risk"
            })
        
        return modifications
    
    def _generate_reasoning(self, primary_action: str, price_analysis: Dict[str, Any],
                          terms_analysis: Dict[str, Any], risk_assessment: Dict[str, Any]) -> str:
        """Generate reasoning for the recommendation."""
        reasons = []
        
        if primary_action == "accept":
            if price_analysis["within_budget"]:
                reasons.append(f"Price of ${price_analysis['counter_amount']:,.0f} is within budget")
            if terms_analysis["terms_acceptability"] == "acceptable":
                reasons.append("Terms are acceptable with minimal negative impact")
        
        elif primary_action == "counter":
            if price_analysis["negotiation_room"] > 0:
                reasons.append(f"${price_analysis['negotiation_room']:,.0f} negotiation room available")
            if terms_analysis["overall_terms_impact"] == "negative":
                reasons.append("Terms need improvement to offset price increase")
        
        elif primary_action == "reject":
            if not price_analysis["within_budget"]:
                reasons.append(f"Price exceeds budget by ${abs(price_analysis['distance_from_max']):,.0f}")
            if risk_assessment["overall_risk_level"] == "high":
                reasons.append("High risk factors make deal inadvisable")
        
        return "; ".join(reasons)
    
    def _generate_alternative_approaches(self, primary_action: str, price_analysis: Dict[str, Any],
                                       strategy: NegotiationStrategyDB) -> List[Dict[str, str]]:
        """Generate alternative approaches to consider."""
        alternatives = []
        
        if primary_action == "reject":
            alternatives.append({
                "approach": "Final offer",
                "description": f"Present final offer at ${strategy.max_offer_price:,.0f} with 48-hour deadline"
            })
            alternatives.append({
                "approach": "Walk away",
                "description": "End negotiations and pursue other opportunities"
            })
        
        elif primary_action == "counter":
            alternatives.append({
                "approach": "Accept with conditions",
                "description": "Accept price but negotiate better terms"
            })
            alternatives.append({
                "approach": "Creative financing",
                "description": "Explore seller financing or lease-option arrangements"
            })
        
        elif primary_action == "accept":
            alternatives.append({
                "approach": "Counter for better terms",
                "description": "Accept price but try to improve terms slightly"
            })
        
        return alternatives
    
    def _calculate_deal_viability(self, counter_offer_data: Dict[str, Any], 
                                 strategy: NegotiationStrategyDB, property_data: PropertyDB) -> Dict[str, Any]:
        """Calculate overall deal viability based on counter offer."""
        counter_amount = counter_offer_data.get("counter_amount", 0)
        
        # Financial viability (40% weight)
        if counter_amount <= strategy.recommended_offer_price:
            financial_score = 100
        elif counter_amount <= strategy.max_offer_price:
            financial_score = 80
        elif counter_amount <= strategy.max_offer_price * 1.05:
            financial_score = 60
        else:
            financial_score = 20
        
        # Market viability (30% weight)
        market_score = {
            MarketConditionEnum.BUYERS_MARKET: 80,
            MarketConditionEnum.BALANCED: 70,
            MarketConditionEnum.SELLERS_MARKET: 60
        }[strategy.market_condition]
        
        # Property viability (20% weight)
        property_score = 70  # Base score
        if property_data.renovation_needed:
            property_score -= 10
        if property_data.days_on_market and property_data.days_on_market > 90:
            property_score += 10
        
        # Terms viability (10% weight)
        terms_score = 70  # Base score
        seller_changes = counter_offer_data.get("seller_changes", {})
        if seller_changes.get("inspection_contingency") == False:
            terms_score -= 20
        if seller_changes.get("appraisal_contingency") == False:
            terms_score -= 10
        
        # Calculate weighted overall score
        overall_score = (
            financial_score * 0.4 +
            market_score * 0.3 +
            property_score * 0.2 +
            terms_score * 0.1
        )
        
        # Determine viability level
        if overall_score >= 80:
            viability_level = "excellent"
        elif overall_score >= 70:
            viability_level = "good"
        elif overall_score >= 60:
            viability_level = "marginal"
        else:
            viability_level = "poor"
        
        return {
            "overall_score": round(overall_score, 1),
            "viability_level": viability_level,
            "component_scores": {
                "financial": financial_score,
                "market": market_score,
                "property": property_score,
                "terms": terms_score
            },
            "recommendation": "proceed" if overall_score >= 60 else "reconsider"
        }
    
    def _calculate_analysis_confidence(self, price_analysis: Dict[str, Any], 
                                     terms_analysis: Dict[str, Any],
                                     risk_assessment: Dict[str, Any]) -> float:
        """Calculate confidence score for the analysis."""
        confidence = 0.5  # Base confidence
        
        # Price analysis confidence factors
        if price_analysis["within_budget"]:
            confidence += 0.2
        if price_analysis["competitiveness"] in ["excellent", "good"]:
            confidence += 0.1
        
        # Terms analysis confidence factors
        if terms_analysis["terms_acceptability"] == "acceptable":
            confidence += 0.1
        
        # Risk assessment confidence factors
        if risk_assessment["overall_risk_level"] == "low":
            confidence += 0.1
        elif risk_assessment["overall_risk_level"] == "high":
            confidence -= 0.1
        
        return min(max(confidence, 0.0), 1.0)  # Clamp between 0 and 1
    
    def save_counter_offer_analysis(self, analysis_data: Dict[str, Any]) -> CounterOfferDB:
        """Save counter offer analysis to the database."""
        try:
            counter_offer_data = {
                "original_offer_id": analysis_data["original_offer_id"],
                "counter_amount": analysis_data["counter_amount"],
                "seller_changes": analysis_data.get("seller_changes", {}),
                "analysis_result": {
                    "price_analysis": analysis_data["price_analysis"],
                    "terms_analysis": analysis_data["terms_analysis"],
                    "risk_assessment": analysis_data["risk_assessment"],
                    "negotiation_path": analysis_data["negotiation_path"],
                    "deal_viability": analysis_data["deal_viability"]
                },
                "recommended_response": analysis_data["response_recommendation"]["primary_action"],
                "risk_factors": [risk["risk"] for category in analysis_data["risk_assessment"].values() 
                               if isinstance(category, list) for risk in category if isinstance(risk, dict)]
            }
            
            counter_offer = CounterOfferDB(**counter_offer_data)
            self.db.add(counter_offer)
            self.db.commit()
            self.db.refresh(counter_offer)
            
            logger.info(f"Saved counter offer analysis {counter_offer.id}")
            return counter_offer
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving counter offer analysis: {str(e)}")
            raise
    
    def get_counter_offer(self, counter_offer_id: uuid.UUID) -> Optional[CounterOfferDB]:
        """Get a counter offer by ID."""
        return self.db.query(CounterOfferDB).filter(
            CounterOfferDB.id == counter_offer_id
        ).first()
    
    def get_counter_offers_for_offer(self, offer_id: uuid.UUID) -> List[CounterOfferDB]:
        """Get all counter offers for an original offer."""
        return self.db.query(CounterOfferDB).filter(
            CounterOfferDB.original_offer_id == offer_id
        ).order_by(CounterOfferDB.created_at.desc()).all()
    
    def update_counter_offer_response(self, counter_offer_id: uuid.UUID, 
                                    response_action: str) -> CounterOfferDB:
        """Update counter offer with response action taken."""
        try:
            counter_offer = self.get_counter_offer(counter_offer_id)
            if not counter_offer:
                raise ValueError(f"Counter offer with ID {counter_offer_id} not found")
            
            counter_offer.responded = True
            counter_offer.response_date = datetime.utcnow()
            counter_offer.status = NegotiationStatusEnum.IN_PROGRESS
            
            # Update buyer response
            if not counter_offer.buyer_response:
                counter_offer.buyer_response = {}
            counter_offer.buyer_response["action_taken"] = response_action
            counter_offer.buyer_response["response_date"] = datetime.utcnow().isoformat()
            
            self.db.commit()
            self.db.refresh(counter_offer)
            
            logger.info(f"Updated counter offer {counter_offer_id} with response: {response_action}")
            return counter_offer
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating counter offer response: {str(e)}")
            raise