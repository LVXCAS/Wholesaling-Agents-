"""
Negotiation Coaching Service for providing AI-powered negotiation guidance and scripts.
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.property import PropertyDB, PropertyAnalysisDB
from app.models.lead import PropertyLeadDB
from app.models.negotiation import (
    NegotiationStrategyDB,
    OfferDB,
    CounterOfferDB,
    MarketConditionEnum,
    SellerMotivationEnum,
    NegotiationCoachingRequest,
    NegotiationCoachingResponse
)

logger = logging.getLogger(__name__)


class NegotiationCoachingService:
    """Service for providing negotiation coaching and guidance."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_coaching(self, request: NegotiationCoachingRequest) -> NegotiationCoachingResponse:
        """
        Generate comprehensive negotiation coaching based on the current situation.
        
        Args:
            request: Coaching request with property ID and situation details
            
        Returns:
            NegotiationCoachingResponse with coaching guidance
        """
        try:
            # Get property data
            property_data = self.db.query(PropertyDB).filter(
                PropertyDB.id == request.property_id
            ).first()
            
            if not property_data:
                raise ValueError(f"Property with ID {request.property_id} not found")
            
            # Get related data
            strategy = self._get_latest_strategy(request.property_id)
            analysis = self._get_latest_analysis(request.property_id)
            lead = self._get_property_lead(request.property_id)
            
            # Generate talking points
            talking_points = self._generate_talking_points(
                property_data, strategy, analysis, request.situation
            )
            
            # Generate objection responses
            objection_responses = self._generate_objection_responses(
                property_data, strategy, request.seller_response, request.specific_concerns
            )
            
            # Generate value propositions
            value_propositions = self._generate_value_propositions(
                property_data, strategy, request.situation
            )
            
            # Generate negotiation script
            negotiation_script = self._generate_negotiation_script(
                property_data, strategy, request.situation, talking_points, value_propositions
            )
            
            # Determine recommended approach
            recommended_approach = self._determine_recommended_approach(
                property_data, strategy, request.situation
            )
            
            # Generate confidence tips
            confidence_tips = self._generate_confidence_tips(
                request.situation, request.specific_concerns
            )
            
            coaching_response = NegotiationCoachingResponse(
                talking_points=talking_points,
                objection_responses=objection_responses,
                value_propositions=value_propositions,
                negotiation_script=negotiation_script,
                recommended_approach=recommended_approach,
                confidence_tips=confidence_tips
            )
            
            logger.info(f"Generated negotiation coaching for property {request.property_id}")
            return coaching_response
            
        except Exception as e:
            logger.error(f"Error generating negotiation coaching: {str(e)}")
            raise
    
    def _get_latest_strategy(self, property_id: uuid.UUID) -> Optional[NegotiationStrategyDB]:
        """Get the latest negotiation strategy for a property."""
        return self.db.query(NegotiationStrategyDB).filter(
            NegotiationStrategyDB.property_id == property_id
        ).order_by(NegotiationStrategyDB.created_at.desc()).first()
    
    def _get_latest_analysis(self, property_id: uuid.UUID) -> Optional[PropertyAnalysisDB]:
        """Get the latest property analysis."""
        return self.db.query(PropertyAnalysisDB).filter(
            PropertyAnalysisDB.property_id == property_id
        ).order_by(PropertyAnalysisDB.created_at.desc()).first()
    
    def _get_property_lead(self, property_id: uuid.UUID) -> Optional[PropertyLeadDB]:
        """Get the property lead information."""
        return self.db.query(PropertyLeadDB).filter(
            PropertyLeadDB.property_id == property_id
        ).first()
    
    def _generate_talking_points(self, property_data: PropertyDB, strategy: Optional[NegotiationStrategyDB],
                               analysis: Optional[PropertyAnalysisDB], situation: str) -> List[str]:
        """Generate key talking points for the negotiation."""
        talking_points = []
        
        # Property-specific talking points
        if property_data.days_on_market and property_data.days_on_market > 60:
            talking_points.append(f"This property has been on the market for {property_data.days_on_market} days, indicating seller motivation")
        
        if property_data.renovation_needed:
            talking_points.append("The property requires significant renovation work, which adds risk and cost to the investment")
        
        # Market-based talking points
        if strategy:
            if strategy.market_condition == MarketConditionEnum.BUYERS_MARKET:
                talking_points.append("Current market conditions favor buyers with increased inventory and longer selling times")
            elif strategy.market_condition == MarketConditionEnum.SELLERS_MARKET:
                talking_points.append("While it's a seller's market, we offer certainty and speed of closing")
        
        # Financial talking points
        if analysis:
            if analysis.repair_estimate:
                talking_points.append(f"Our analysis shows approximately ${analysis.repair_estimate:,.0f} in necessary repairs")
            
            if analysis.comparable_count and analysis.comparable_count >= 3:
                talking_points.append(f"Based on {analysis.comparable_count} comparable sales, our offer reflects current market value")
        
        # Situation-specific talking points
        if "counter offer" in situation.lower():
            talking_points.append("We've carefully considered your counter offer and want to find a mutually beneficial solution")
        
        if "final offer" in situation.lower():
            talking_points.append("This represents our best and final offer based on our investment criteria")
        
        # Value proposition talking points
        talking_points.extend([
            "We can close quickly without financing delays or complications",
            "We're experienced investors who can handle any property condition",
            "We offer a hassle-free transaction with no real estate agent commissions"
        ])
        
        return talking_points
    
    def _generate_objection_responses(self, property_data: PropertyDB, strategy: Optional[NegotiationStrategyDB],
                                    seller_response: Optional[str], specific_concerns: Optional[List[str]]) -> Dict[str, str]:
        """Generate responses to common seller objections."""
        objection_responses = {}
        
        # Price objections
        objection_responses["Price is too low"] = (
            "I understand your concern about the price. Our offer is based on extensive market analysis "
            "and accounts for the current condition of the property and necessary repairs. We're offering "
            "a fair market price that allows us to invest in improving the property."
        )
        
        objection_responses["I can get more from another buyer"] = (
            "While you might receive other offers, we provide certainty and speed. We can close in as little as "
            "2 weeks with no financing contingencies. A bird in the hand is worth two in the bush."
        )
        
        objection_responses["I need more time to think"] = (
            "I completely understand this is a big decision. However, our offer is time-sensitive due to "
            "market conditions and our investment timeline. We can give you 48 hours to consider, "
            "which should be enough time to make an informed decision."
        )
        
        # Condition objections
        if property_data.renovation_needed:
            objection_responses["The property is in good condition"] = (
                "The property has good bones, but our inspection revealed several items that need attention. "
                "We're prepared to take on these repairs and restore the property to its full potential."
            )
        
        # Market objections
        if strategy and strategy.market_condition == MarketConditionEnum.SELLERS_MARKET:
            objection_responses["It's a seller's market"] = (
                "You're right that it's generally a seller's market, but every property is unique. "
                "We're offering speed and certainty, which is valuable in any market condition."
            )
        
        # Timeline objections
        objection_responses["I need more time to move"] = (
            "We can be flexible with the closing date and even offer a rent-back period if you need "
            "time to find your next home. Our goal is to make this as convenient as possible for you."
        )
        
        # Financing objections
        objection_responses["I want to wait for a financed buyer"] = (
            "Financed buyers bring uncertainty - loan denials, appraisal issues, and delays are common. "
            "We eliminate all those risks with our cash offer and proven track record."
        )
        
        # Address specific concerns if provided
        if specific_concerns:
            for concern in specific_concerns:
                if "commission" in concern.lower():
                    objection_responses[f"Concern about {concern}"] = (
                        "By selling directly to us, you save the typical 6% real estate commission, "
                        "which on this property would be significant savings."
                    )
                elif "repair" in concern.lower():
                    objection_responses[f"Concern about {concern}"] = (
                        "We buy properties as-is, so you don't need to worry about making any repairs "
                        "or improvements. We handle everything after closing."
                    )
        
        # Seller response specific objections
        if seller_response:
            if "too low" in seller_response.lower():
                objection_responses["Seller says price is too low"] = (
                    "I hear that you feel the price is low. Let me explain how we arrived at this number "
                    "based on comparable sales, necessary repairs, and current market conditions."
                )
            elif "need more" in seller_response.lower():
                objection_responses["Seller needs more money"] = (
                    "I understand you have financial needs. Let's see if we can structure the deal "
                    "in a way that works better for you, perhaps with a quicker closing or other terms."
                )
        
        return objection_responses
    
    def _generate_value_propositions(self, property_data: PropertyDB, strategy: Optional[NegotiationStrategyDB],
                                   situation: str) -> List[str]:
        """Generate compelling value propositions for the seller."""
        value_props = []
        
        # Speed and certainty
        value_props.extend([
            "Guaranteed closing in 2-3 weeks with no financing delays",
            "Cash purchase eliminates loan approval risks and appraisal issues",
            "No real estate agent commissions - you keep more of the sale price"
        ])
        
        # Convenience factors
        value_props.extend([
            "We buy the property as-is - no need for repairs or improvements",
            "We handle all paperwork and closing coordination",
            "Flexible closing date to accommodate your timeline"
        ])
        
        # Market-specific value props
        if strategy:
            if strategy.market_condition == MarketConditionEnum.BUYERS_MARKET:
                value_props.append("Guaranteed sale in a challenging market with limited buyer activity")
            elif strategy.seller_motivation in [SellerMotivationEnum.HIGH, SellerMotivationEnum.URGENT]:
                value_props.append("Quick resolution for your urgent situation")
        
        # Property-specific value props
        if property_data.renovation_needed:
            value_props.append("No need to invest time and money in repairs before selling")
        
        if property_data.days_on_market and property_data.days_on_market > 90:
            value_props.append("End the stress of having your property on the market for months")
        
        # Situation-specific value props
        if "foreclosure" in situation.lower():
            value_props.append("Stop foreclosure proceedings and protect your credit")
        
        if "divorce" in situation.lower():
            value_props.append("Quick, clean sale to help you move forward")
        
        if "inheritance" in situation.lower():
            value_props.append("Hassle-free solution for inherited property management")
        
        return value_props
    
    def _generate_negotiation_script(self, property_data: PropertyDB, strategy: Optional[NegotiationStrategyDB],
                                   situation: str, talking_points: List[str], value_propositions: List[str]) -> str:
        """Generate a complete negotiation script."""
        
        # Opening
        script_parts = [
            "OPENING:",
            "Thank you for taking the time to speak with me about your property. I understand this is an important decision for you, and I want to make sure we find a solution that works for both of us.",
            ""
        ]
        
        # Situation acknowledgment
        if "counter offer" in situation.lower():
            script_parts.extend([
                "ACKNOWLEDGING THE COUNTER OFFER:",
                "I've carefully reviewed your counter offer, and I appreciate you working with us to find a mutually beneficial agreement.",
                ""
            ])
        elif "initial offer" in situation.lower():
            script_parts.extend([
                "PRESENTING THE OFFER:",
                "Based on our analysis of your property and current market conditions, I'd like to present our offer and explain how we arrived at these terms.",
                ""
            ])
        
        # Key talking points
        script_parts.extend([
            "KEY POINTS TO DISCUSS:",
            *[f"• {point}" for point in talking_points[:5]],  # Limit to top 5 points
            ""
        ])
        
        # Value proposition
        script_parts.extend([
            "VALUE WE PROVIDE:",
            *[f"• {prop}" for prop in value_propositions[:4]],  # Limit to top 4 props
            ""
        ])
        
        # Addressing concerns
        script_parts.extend([
            "ADDRESSING CONCERNS:",
            "I want to address any concerns you might have about our offer. What questions can I answer for you?",
            "",
            "COMMON RESPONSES:",
            "• If price is a concern: 'I understand price is important. Let me explain how we calculated this fair market value...'",
            "• If timing is a concern: 'We can be flexible with the closing date to work with your schedule...'",
            "• If condition is a concern: 'We buy properties as-is, so you don't need to worry about any repairs...'",
            ""
        ])
        
        # Closing
        if strategy and strategy.negotiation_approach == "aggressive":
            script_parts.extend([
                "CLOSING (DIRECT APPROACH):",
                "Based on everything we've discussed, I believe our offer represents excellent value for your situation. Are you ready to move forward with this agreement?"
            ])
        else:
            script_parts.extend([
                "CLOSING (COLLABORATIVE APPROACH):",
                "I want to make sure this works for you. What would it take to move forward with this transaction? Is there anything else we need to address?"
            ])
        
        return "\n".join(script_parts)
    
    def _determine_recommended_approach(self, property_data: PropertyDB, strategy: Optional[NegotiationStrategyDB],
                                      situation: str) -> str:
        """Determine the recommended negotiation approach."""
        
        if strategy:
            base_approach = strategy.negotiation_approach
        else:
            base_approach = "moderate"
        
        # Adjust based on situation
        if "final offer" in situation.lower():
            return "direct"
        elif "counter offer" in situation.lower():
            return "collaborative"
        elif "initial contact" in situation.lower():
            return "consultative"
        elif any(word in situation.lower() for word in ["urgent", "foreclosure", "divorce"]):
            return "empathetic"
        else:
            return base_approach
    
    def _generate_confidence_tips(self, situation: str, specific_concerns: Optional[List[str]]) -> List[str]:
        """Generate tips to boost negotiation confidence."""
        tips = [
            "Remember that you're providing a valuable service by offering a quick, hassle-free sale",
            "Stay calm and professional - your expertise and preparation will show",
            "Listen actively to understand the seller's real concerns and motivations",
            "Use silence effectively - don't feel pressured to fill every pause",
            "Focus on the mutual benefits rather than just your position"
        ]
        
        # Situation-specific tips
        if "nervous" in situation.lower() or "first time" in situation.lower():
            tips.extend([
                "It's normal to feel nervous - preparation is your best confidence booster",
                "Practice your key talking points beforehand",
                "Remember that the seller called you - they're interested in what you offer"
            ])
        
        if "counter offer" in situation.lower():
            tips.extend([
                "A counter offer means they're engaged - that's positive progress",
                "Stay flexible and look for creative solutions that work for both parties",
                "Don't take negotiations personally - it's just business"
            ])
        
        if "difficult seller" in situation.lower():
            tips.extend([
                "Stay patient and professional even if the seller becomes emotional",
                "Acknowledge their concerns before presenting your position",
                "Sometimes walking away is the best negotiation tactic"
            ])
        
        # Address specific concerns
        if specific_concerns:
            if any("price" in concern.lower() for concern in specific_concerns):
                tips.append("Have your comparable sales data ready to justify your price")
            
            if any("time" in concern.lower() for concern in specific_concerns):
                tips.append("Emphasize the speed and certainty of your offer")
            
            if any("competition" in concern.lower() for concern in specific_concerns):
                tips.append("Focus on your unique advantages rather than competing on price alone")
        
        return tips
    
    def generate_situation_specific_coaching(self, property_id: uuid.UUID, 
                                           negotiation_phase: str) -> Dict[str, Any]:
        """
        Generate coaching specific to the current negotiation phase.
        
        Args:
            property_id: UUID of the property
            negotiation_phase: Current phase (initial, counter, final, closing)
            
        Returns:
            Dict with phase-specific coaching guidance
        """
        try:
            property_data = self.db.query(PropertyDB).filter(
                PropertyDB.id == property_id
            ).first()
            
            if not property_data:
                raise ValueError(f"Property with ID {property_id} not found")
            
            strategy = self._get_latest_strategy(property_id)
            
            coaching = {
                "phase": negotiation_phase,
                "objectives": [],
                "key_messages": [],
                "tactics": [],
                "red_flags": [],
                "success_indicators": []
            }
            
            if negotiation_phase == "initial":
                coaching.update(self._generate_initial_phase_coaching(property_data, strategy))
            elif negotiation_phase == "counter":
                coaching.update(self._generate_counter_phase_coaching(property_data, strategy))
            elif negotiation_phase == "final":
                coaching.update(self._generate_final_phase_coaching(property_data, strategy))
            elif negotiation_phase == "closing":
                coaching.update(self._generate_closing_phase_coaching(property_data, strategy))
            
            return coaching
            
        except Exception as e:
            logger.error(f"Error generating situation-specific coaching: {str(e)}")
            raise
    
    def _generate_initial_phase_coaching(self, property_data: PropertyDB, 
                                       strategy: Optional[NegotiationStrategyDB]) -> Dict[str, List[str]]:
        """Generate coaching for initial offer phase."""
        return {
            "objectives": [
                "Establish rapport and credibility",
                "Present offer with clear justification",
                "Gauge seller's motivation and timeline",
                "Set expectations for next steps"
            ],
            "key_messages": [
                "We're experienced investors who close quickly",
                "Our offer is based on thorough market analysis",
                "We can provide certainty in an uncertain market",
                "We're here to solve your property situation"
            ],
            "tactics": [
                "Ask open-ended questions about their situation",
                "Listen more than you talk in the first conversation",
                "Provide comparable sales data to support your offer",
                "Emphasize speed and certainty over price"
            ],
            "red_flags": [
                "Seller seems unrealistic about property value",
                "Multiple family members involved in decision",
                "Property has undisclosed issues or liens",
                "Seller is not the actual decision maker"
            ],
            "success_indicators": [
                "Seller asks questions about the process",
                "Seller shares details about their situation",
                "Seller agrees to consider the offer",
                "Seller provides timeline for decision"
            ]
        }
    
    def _generate_counter_phase_coaching(self, property_data: PropertyDB,
                                       strategy: Optional[NegotiationStrategyDB]) -> Dict[str, List[str]]:
        """Generate coaching for counter offer phase."""
        return {
            "objectives": [
                "Understand the gap between positions",
                "Find creative solutions beyond price",
                "Maintain relationship while protecting interests",
                "Move toward final agreement"
            ],
            "key_messages": [
                "We want to find a solution that works for everyone",
                "Let's explore options beyond just price",
                "We're committed to closing this transaction",
                "Time is valuable for both of us"
            ],
            "tactics": [
                "Acknowledge their position before presenting yours",
                "Offer non-price concessions (timing, terms, etc.)",
                "Use 'what if' scenarios to explore options",
                "Set deadlines to create urgency"
            ],
            "red_flags": [
                "Seller keeps moving the goalposts",
                "Unreasonable demands or ultimatums",
                "Seller shopping your offer to other buyers",
                "Emotional decision-making overriding logic"
            ],
            "success_indicators": [
                "Seller is willing to negotiate on terms",
                "Gap between positions is narrowing",
                "Seller shows urgency to close",
                "Both parties making concessions"
            ]
        }
    
    def _generate_final_phase_coaching(self, property_data: PropertyDB,
                                     strategy: Optional[NegotiationStrategyDB]) -> Dict[str, List[str]]:
        """Generate coaching for final offer phase."""
        return {
            "objectives": [
                "Present best and final terms clearly",
                "Create urgency for decision",
                "Prepare for potential walkaway",
                "Secure commitment or move on"
            ],
            "key_messages": [
                "This is our best and final offer",
                "We need a decision by [specific time]",
                "We have other opportunities if this doesn't work",
                "We're confident this is a fair deal"
            ],
            "tactics": [
                "Be direct and clear about finality",
                "Set firm deadline for response",
                "Summarize all value propositions",
                "Be prepared to walk away"
            ],
            "red_flags": [
                "Seller trying to negotiate after 'final' offer",
                "Requests for extensions without commitment",
                "New issues or demands appearing",
                "Seller stalling without clear reason"
            ],
            "success_indicators": [
                "Seller accepts the final offer",
                "Seller asks about next steps",
                "Seller shows urgency to close",
                "Clear commitment to move forward"
            ]
        }
    
    def _generate_closing_phase_coaching(self, property_data: PropertyDB,
                                       strategy: Optional[NegotiationStrategyDB]) -> Dict[str, List[str]]:
        """Generate coaching for closing coordination phase."""
        return {
            "objectives": [
                "Coordinate smooth closing process",
                "Address any last-minute issues",
                "Maintain seller satisfaction",
                "Complete transaction successfully"
            ],
            "key_messages": [
                "We're committed to closing on schedule",
                "We'll handle all the details",
                "Any issues can be resolved quickly",
                "Thank you for choosing to work with us"
            ],
            "tactics": [
                "Provide regular updates on closing progress",
                "Address concerns immediately",
                "Be flexible on minor issues",
                "Maintain professional communication"
            ],
            "red_flags": [
                "Seller getting cold feet",
                "New demands or conditions",
                "Title or inspection issues",
                "Financing problems (if applicable)"
            ],
            "success_indicators": [
                "All documents signed and submitted",
                "Seller cooperative with closing process",
                "No major issues discovered",
                "Closing scheduled and confirmed"
            ]
        }
    
    def generate_objection_handling_guide(self, common_objections: List[str]) -> Dict[str, Dict[str, str]]:
        """
        Generate a comprehensive objection handling guide.
        
        Args:
            common_objections: List of common objections to address
            
        Returns:
            Dict with objection handling strategies
        """
        objection_guide = {}
        
        # Standard objections with responses
        standard_objections = {
            "Your offer is too low": {
                "acknowledge": "I understand you feel the offer is low.",
                "bridge": "Let me explain how we arrived at this number.",
                "response": "Our offer is based on current market conditions, comparable sales, and the property's condition. We factor in repair costs and market risks to ensure a fair price.",
                "close": "Would you like me to show you the comparable sales we used?"
            },
            "I need to think about it": {
                "acknowledge": "Of course, this is an important decision.",
                "bridge": "I want to make sure you have all the information you need.",
                "response": "What specific concerns do you have that I can address? Our offer is time-sensitive due to market conditions, but I want you to feel confident in your decision.",
                "close": "What would help you make a decision by tomorrow?"
            },
            "I want to get other offers": {
                "acknowledge": "That's understandable - you want to explore all options.",
                "bridge": "Let me share what makes our offer unique.",
                "response": "While you might get other offers, we provide certainty and speed. We can close in 2 weeks with no financing contingencies. Other buyers might have loan issues or delays.",
                "close": "How important is certainty versus potentially getting a slightly higher offer that might fall through?"
            }
        }
        
        # Add standard objections to guide
        objection_guide.update(standard_objections)
        
        # Add custom objections if provided
        for objection in common_objections:
            if objection not in objection_guide:
                objection_guide[objection] = self._generate_custom_objection_response(objection)
        
        return objection_guide
    
    def _generate_custom_objection_response(self, objection: str) -> Dict[str, str]:
        """Generate a custom response structure for a specific objection."""
        # This would use AI/ML to generate appropriate responses
        # For now, providing a template structure
        return {
            "acknowledge": f"I understand your concern about {objection.lower()}.",
            "bridge": "Let me address that for you.",
            "response": "This is a common concern, and here's how we handle it...",
            "close": "Does that address your concern?"
        }