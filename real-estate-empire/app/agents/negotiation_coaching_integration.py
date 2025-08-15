"""
Negotiation Coaching Integration - Real-time coaching for agent workflows
Integrates the negotiation coaching service with agent workflows to provide real-time guidance
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.negotiation_coaching_service import NegotiationCoachingService
from app.models.negotiation import (
    NegotiationCoachingRequest,
    NegotiationCoachingResponse,
    NegotiationStatusEnum
)
from app.core.agent_state import AgentState, AgentType, StateManager

logger = logging.getLogger(__name__)


class NegotiationCoachingIntegration:
    """
    Integration layer for negotiation coaching in agent workflows
    Provides real-time coaching suggestions during negotiations
    """
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        self.coaching_service = NegotiationCoachingService(self.db)
        self.active_coaching_sessions: Dict[str, Dict[str, Any]] = {}
        self.coaching_effectiveness_tracking: Dict[str, Dict[str, Any]] = {}
        
    async def provide_real_time_coaching(
        self, 
        property_id: uuid.UUID, 
        situation: str,
        seller_response: Optional[str] = None,
        specific_concerns: Optional[List[str]] = None,
        negotiation_phase: str = "initial"
    ) -> Dict[str, Any]:
        """
        Provide real-time coaching suggestions during negotiations
        
        Args:
            property_id: UUID of the property being negotiated
            situation: Current negotiation situation description
            seller_response: Latest seller response if any
            specific_concerns: List of specific concerns to address
            negotiation_phase: Current phase of negotiation
            
        Returns:
            Dict containing coaching guidance and suggestions
        """
        try:
            logger.info(f"Providing real-time coaching for property {property_id}, phase: {negotiation_phase}")
            
            # Create coaching request
            coaching_request = NegotiationCoachingRequest(
                property_id=property_id,
                situation=situation,
                seller_response=seller_response,
                specific_concerns=specific_concerns or []
            )
            
            # Get general coaching
            general_coaching = self.coaching_service.generate_coaching(coaching_request)
            
            # Get phase-specific coaching
            phase_coaching = self.coaching_service.generate_situation_specific_coaching(
                property_id, negotiation_phase
            )
            
            # Create coaching session
            session_id = str(uuid.uuid4())
            coaching_session = {
                "session_id": session_id,
                "property_id": str(property_id),
                "situation": situation,
                "negotiation_phase": negotiation_phase,
                "general_coaching": general_coaching.dict(),
                "phase_coaching": phase_coaching,
                "created_at": datetime.now(),
                "effectiveness_score": None,
                "user_feedback": None
            }
            
            self.active_coaching_sessions[session_id] = coaching_session
            
            # Combine coaching responses
            combined_coaching = {
                "session_id": session_id,
                "property_id": str(property_id),
                "negotiation_phase": negotiation_phase,
                "coaching": {
                    "talking_points": general_coaching.talking_points,
                    "objection_responses": general_coaching.objection_responses,
                    "value_propositions": general_coaching.value_propositions,
                    "negotiation_script": general_coaching.negotiation_script,
                    "recommended_approach": general_coaching.recommended_approach,
                    "confidence_tips": general_coaching.confidence_tips,
                    "phase_specific": phase_coaching
                },
                "real_time_suggestions": self._generate_real_time_suggestions(
                    situation, seller_response, negotiation_phase
                ),
                "success": True
            }
            
            logger.info(f"Generated real-time coaching session {session_id}")
            return combined_coaching
            
        except Exception as e:
            logger.error(f"Error providing real-time coaching: {e}")
            return {
                "success": False,
                "error": str(e),
                "coaching": None
            }
    
    def _generate_real_time_suggestions(
        self, 
        situation: str, 
        seller_response: Optional[str], 
        negotiation_phase: str
    ) -> List[Dict[str, Any]]:
        """Generate real-time suggestions based on current context"""
        suggestions = []
        
        # Phase-specific suggestions
        if negotiation_phase == "initial":
            suggestions.extend([
                {
                    "type": "opening",
                    "priority": "high",
                    "suggestion": "Start with rapport building - ask about their situation and timeline",
                    "timing": "immediate"
                },
                {
                    "type": "data_preparation",
                    "priority": "medium",
                    "suggestion": "Have your comparable sales data ready to justify your offer",
                    "timing": "before_offer"
                }
            ])
        elif negotiation_phase == "counter":
            suggestions.extend([
                {
                    "type": "acknowledgment",
                    "priority": "high",
                    "suggestion": "Acknowledge their counter offer positively before presenting your position",
                    "timing": "immediate"
                },
                {
                    "type": "creative_solutions",
                    "priority": "medium",
                    "suggestion": "Look for non-price concessions like closing date flexibility",
                    "timing": "during_negotiation"
                }
            ])
        elif negotiation_phase == "final":
            suggestions.extend([
                {
                    "type": "finality",
                    "priority": "high",
                    "suggestion": "Be clear this is your final offer and set a decision deadline",
                    "timing": "immediate"
                },
                {
                    "type": "walkaway_preparation",
                    "priority": "high",
                    "suggestion": "Be mentally prepared to walk away if terms aren't met",
                    "timing": "before_final_offer"
                }
            ])
        
        # Situation-specific suggestions
        if seller_response:
            if "too low" in seller_response.lower():
                suggestions.append({
                    "type": "price_objection",
                    "priority": "high",
                    "suggestion": "Use comparable sales data to justify your price point",
                    "timing": "immediate"
                })
            elif "need more time" in seller_response.lower():
                suggestions.append({
                    "type": "urgency_creation",
                    "priority": "medium",
                    "suggestion": "Create gentle urgency by mentioning other opportunities",
                    "timing": "immediate"
                })
        
        # Situation-based suggestions
        if "foreclosure" in situation.lower():
            suggestions.append({
                "type": "empathy",
                "priority": "high",
                "suggestion": "Show empathy for their difficult situation while emphasizing speed",
                "timing": "throughout"
            })
        elif "divorce" in situation.lower():
            suggestions.append({
                "type": "simplicity",
                "priority": "high",
                "suggestion": "Emphasize the simplicity and speed of your process",
                "timing": "throughout"
            })
        
        return suggestions
    
    async def integrate_with_negotiator_workflow(
        self, 
        state: AgentState, 
        negotiation_data: Dict[str, Any]
    ) -> AgentState:
        """
        Integrate coaching with negotiator agent workflow
        
        Args:
            state: Current agent state
            negotiation_data: Current negotiation data
            
        Returns:
            Updated agent state with coaching integration
        """
        try:
            property_id = negotiation_data.get("property_id")
            if not property_id:
                return state
            
            # Determine negotiation phase
            negotiation_phase = self._determine_negotiation_phase(negotiation_data)
            
            # Get coaching
            coaching_result = await self.provide_real_time_coaching(
                property_id=uuid.UUID(property_id),
                situation=negotiation_data.get("situation", "Active negotiation"),
                seller_response=negotiation_data.get("latest_response"),
                specific_concerns=negotiation_data.get("concerns", []),
                negotiation_phase=negotiation_phase
            )
            
            if coaching_result.get("success"):
                # Add coaching to agent state
                coaching_data = coaching_result["coaching"]
                
                # Update negotiation data with coaching
                negotiation_data["coaching_session_id"] = coaching_result["session_id"]
                negotiation_data["coaching_suggestions"] = coaching_result["real_time_suggestions"]
                negotiation_data["recommended_approach"] = coaching_data["recommended_approach"]
                negotiation_data["talking_points"] = coaching_data["talking_points"]
                
                # Add agent message about coaching
                state = StateManager.add_agent_message(
                    state,
                    AgentType.NEGOTIATOR,
                    f"Provided real-time coaching for {negotiation_phase} phase negotiation",
                    data={
                        "coaching_session_id": coaching_result["session_id"],
                        "suggestions_count": len(coaching_result["real_time_suggestions"]),
                        "phase": negotiation_phase
                    },
                    priority=2
                )
                
                logger.info(f"Integrated coaching with negotiator workflow for property {property_id}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error integrating coaching with workflow: {e}")
            return state
    
    def _determine_negotiation_phase(self, negotiation_data: Dict[str, Any]) -> str:
        """Determine the current negotiation phase"""
        status = negotiation_data.get("status", "")
        offer_count = negotiation_data.get("offer_count", 0)
        
        # Check for final offer first (highest priority)
        if status == "final_offer" or negotiation_data.get("is_final_offer", False):
            return "final"
        # Check for closing phase
        elif status in ["closing", "under_contract"]:
            return "closing"
        # Check for initial phase
        elif status == "initial_outreach" or offer_count == 0:
            return "initial"
        # Check for counter offer phase
        elif status == "counter_offer" or offer_count > 1:
            return "counter"
        else:
            return "initial"
    
    async def track_coaching_effectiveness(
        self, 
        session_id: str, 
        outcome: str, 
        user_feedback: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track the effectiveness of coaching sessions
        
        Args:
            session_id: ID of the coaching session
            outcome: Outcome of the negotiation (accepted, rejected, counter, etc.)
            user_feedback: Optional user feedback about coaching quality
            
        Returns:
            Dict with tracking results
        """
        try:
            if session_id not in self.active_coaching_sessions:
                return {"success": False, "error": "Session not found"}
            
            session = self.active_coaching_sessions[session_id]
            
            # Calculate effectiveness score based on outcome
            effectiveness_score = self._calculate_effectiveness_score(outcome, user_feedback)
            
            # Update session with effectiveness data
            session["effectiveness_score"] = effectiveness_score
            session["outcome"] = outcome
            session["user_feedback"] = user_feedback
            session["completed_at"] = datetime.now()
            
            # Store in effectiveness tracking
            property_id = session["property_id"]
            if property_id not in self.coaching_effectiveness_tracking:
                self.coaching_effectiveness_tracking[property_id] = {
                    "sessions": [],
                    "average_effectiveness": 0.0,
                    "total_sessions": 0,
                    "successful_outcomes": 0
                }
            
            tracking_data = self.coaching_effectiveness_tracking[property_id]
            tracking_data["sessions"].append(session)
            tracking_data["total_sessions"] += 1
            
            if outcome in ["accepted", "counter_accepted"]:
                tracking_data["successful_outcomes"] += 1
            
            # Calculate average effectiveness
            effectiveness_scores = [s["effectiveness_score"] for s in tracking_data["sessions"] if s["effectiveness_score"] is not None]
            if effectiveness_scores:
                tracking_data["average_effectiveness"] = sum(effectiveness_scores) / len(effectiveness_scores)
            
            logger.info(f"Tracked coaching effectiveness for session {session_id}: {effectiveness_score}")
            
            return {
                "success": True,
                "effectiveness_score": effectiveness_score,
                "session_data": session
            }
            
        except Exception as e:
            logger.error(f"Error tracking coaching effectiveness: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_effectiveness_score(
        self, 
        outcome: str, 
        user_feedback: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate effectiveness score based on outcome and feedback"""
        base_score = 0.0
        
        # Base score from outcome
        outcome_scores = {
            "accepted": 1.0,
            "counter_accepted": 0.9,
            "counter_offer": 0.7,
            "negotiation_continued": 0.6,
            "stalled": 0.3,
            "rejected": 0.1,
            "walked_away": 0.2
        }
        
        base_score = outcome_scores.get(outcome.lower(), 0.5)
        
        # Adjust based on user feedback if provided
        if user_feedback:
            helpfulness = user_feedback.get("helpfulness", 5)  # 1-10 scale
            accuracy = user_feedback.get("accuracy", 5)  # 1-10 scale
            
            feedback_adjustment = ((helpfulness + accuracy) / 20) * 0.3  # Max 30% adjustment
            base_score = min(1.0, base_score + feedback_adjustment)
        
        return round(base_score, 2)
    
    def get_coaching_analytics(self, property_id: Optional[str] = None) -> Dict[str, Any]:
        """Get analytics on coaching effectiveness"""
        try:
            if property_id:
                # Get analytics for specific property
                if property_id in self.coaching_effectiveness_tracking:
                    return self.coaching_effectiveness_tracking[property_id]
                else:
                    return {"error": "No coaching data found for property"}
            else:
                # Get overall analytics
                all_sessions = []
                total_properties = len(self.coaching_effectiveness_tracking)
                
                for prop_data in self.coaching_effectiveness_tracking.values():
                    all_sessions.extend(prop_data["sessions"])
                
                if not all_sessions:
                    return {"message": "No coaching sessions found"}
                
                # Calculate overall metrics
                effectiveness_scores = [s["effectiveness_score"] for s in all_sessions if s["effectiveness_score"] is not None]
                successful_outcomes = len([s for s in all_sessions if s.get("outcome") in ["accepted", "counter_accepted"]])
                
                analytics = {
                    "total_sessions": len(all_sessions),
                    "total_properties": total_properties,
                    "average_effectiveness": sum(effectiveness_scores) / len(effectiveness_scores) if effectiveness_scores else 0.0,
                    "success_rate": successful_outcomes / len(all_sessions) if all_sessions else 0.0,
                    "phase_breakdown": self._get_phase_breakdown(all_sessions),
                    "outcome_breakdown": self._get_outcome_breakdown(all_sessions)
                }
                
                return analytics
                
        except Exception as e:
            logger.error(f"Error getting coaching analytics: {e}")
            return {"error": str(e)}
    
    def _get_phase_breakdown(self, sessions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get breakdown of sessions by negotiation phase"""
        phase_counts = {}
        for session in sessions:
            phase = session.get("negotiation_phase", "unknown")
            phase_counts[phase] = phase_counts.get(phase, 0) + 1
        return phase_counts
    
    def _get_outcome_breakdown(self, sessions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get breakdown of sessions by outcome"""
        outcome_counts = {}
        for session in sessions:
            outcome = session.get("outcome", "unknown")
            outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
        return outcome_counts
    
    async def generate_coaching_report(self, property_id: str) -> Dict[str, Any]:
        """Generate a comprehensive coaching report for a property"""
        try:
            if property_id not in self.coaching_effectiveness_tracking:
                return {"error": "No coaching data found for property"}
            
            tracking_data = self.coaching_effectiveness_tracking[property_id]
            sessions = tracking_data["sessions"]
            
            # Generate report
            report = {
                "property_id": property_id,
                "report_generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_sessions": tracking_data["total_sessions"],
                    "average_effectiveness": tracking_data["average_effectiveness"],
                    "success_rate": tracking_data["successful_outcomes"] / tracking_data["total_sessions"] if tracking_data["total_sessions"] > 0 else 0.0
                },
                "session_details": [],
                "recommendations": []
            }
            
            # Add session details
            for session in sessions:
                session_detail = {
                    "session_id": session["session_id"],
                    "negotiation_phase": session["negotiation_phase"],
                    "effectiveness_score": session.get("effectiveness_score"),
                    "outcome": session.get("outcome"),
                    "created_at": session["created_at"].isoformat(),
                    "coaching_used": {
                        "talking_points_count": len(session["general_coaching"]["talking_points"]),
                        "objection_responses_count": len(session["general_coaching"]["objection_responses"]),
                        "confidence_tips_count": len(session["general_coaching"]["confidence_tips"])
                    }
                }
                report["session_details"].append(session_detail)
            
            # Generate recommendations
            report["recommendations"] = self._generate_coaching_recommendations(tracking_data)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating coaching report: {e}")
            return {"error": str(e)}
    
    def _generate_coaching_recommendations(self, tracking_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on coaching effectiveness data"""
        recommendations = []
        
        avg_effectiveness = tracking_data["average_effectiveness"]
        success_rate = tracking_data["successful_outcomes"] / tracking_data["total_sessions"] if tracking_data["total_sessions"] > 0 else 0.0
        
        if avg_effectiveness < 0.6:
            recommendations.append("Consider adjusting negotiation approach - effectiveness scores are below optimal")
        
        if success_rate < 0.4:
            recommendations.append("Review talking points and value propositions - success rate could be improved")
        
        # Analyze phase-specific performance
        sessions = tracking_data["sessions"]
        phase_effectiveness = {}
        for session in sessions:
            phase = session.get("negotiation_phase", "unknown")
            if phase not in phase_effectiveness:
                phase_effectiveness[phase] = []
            if session.get("effectiveness_score") is not None:
                phase_effectiveness[phase].append(session["effectiveness_score"])
        
        for phase, scores in phase_effectiveness.items():
            if scores and sum(scores) / len(scores) < 0.5:
                recommendations.append(f"Focus on improving {phase} phase coaching - below average effectiveness")
        
        if not recommendations:
            recommendations.append("Coaching performance is good - continue current approach")
        
        return recommendations