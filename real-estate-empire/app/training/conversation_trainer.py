import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np
from dataclasses import dataclass

from ..simulation.homeowner_simulator import HomeownerConversationSimulator, HomeownerProfile, ConversationContext
from ..simulation.market_simulator import MarketSimulator

@dataclass
class ConversationTrainingResult:
    """Result of a conversation training session"""
    agent_id: str
    conversation_id: str
    scenario_type: str
    homeowner_personality: str
    agent_responses: List[Dict[str, Any]]
    performance_scores: Dict[str, float]
    areas_for_improvement: List[str]
    successful_techniques: List[str]
    overall_score: float
    timestamp: datetime

class ConversationTrainer:
    """Trains agents on realistic homeowner conversations"""
    
    def __init__(self, market_simulator: MarketSimulator, gemini_api_key: Optional[str] = None):
        self.market_simulator = market_simulator
        self.homeowner_simulator = HomeownerConversationSimulator(gemini_api_key)
        self.training_history: Dict[str, List[ConversationTrainingResult]] = {}
        
        # Conversation skills to evaluate
        self.evaluation_criteria = {
            "rapport_building": {
                "weight": 0.20,
                "description": "Ability to establish trust and connection",
                "indicators": ["personal connection", "active listening", "empathy"]
            },
            "needs_discovery": {
                "weight": 0.25,
                "description": "Uncovering homeowner's real motivations and needs",
                "indicators": ["asking questions", "understanding timeline", "identifying pain points"]
            },
            "objection_handling": {
                "weight": 0.25,
                "description": "Addressing concerns and overcoming resistance",
                "indicators": ["acknowledging concerns", "providing solutions", "reframing objections"]
            },
            "value_proposition": {
                "weight": 0.20,
                "description": "Communicating clear value and benefits",
                "indicators": ["market expertise", "unique advantages", "concrete benefits"]
            },
            "closing_skills": {
                "weight": 0.10,
                "description": "Moving conversation toward next steps",
                "indicators": ["clear call to action", "commitment", "follow-up plan"]
            }
        }
    
    async def train_agent_on_conversations(self, 
                                         agent,
                                         num_conversations: int = 10,
                                         scenario_types: List[str] = None,
                                         difficulty_progression: bool = True) -> Dict[str, Any]:
        """Train an agent on realistic homeowner conversations"""
        
        if scenario_types is None:
            scenario_types = ["cold_call", "follow_up", "objection_handling", "negotiation"]
        
        print(f"🗣️ Starting conversation training for {agent.agent_id}")
        print(f"   Scenarios: {num_conversations} conversations")
        print(f"   Types: {scenario_types}")
        
        training_results = []
        
        for i in range(num_conversations):
            # Progressive difficulty
            if difficulty_progression:
                difficulty = 0.3 + (i / num_conversations) * 0.6
            else:
                difficulty = np.random.uniform(0.4, 0.8)
            
            # Select scenario type
            scenario_type = np.random.choice(scenario_types)
            
            print(f"   Conversation {i+1}/{num_conversations}: {scenario_type} (difficulty: {difficulty:.2f})")
            
            # Generate conversation scenario
            result = await self._run_conversation_training(agent, scenario_type, difficulty)
            training_results.append(result)
            
            # Brief pause between conversations
            await asyncio.sleep(0.1)
        
        # Analyze overall performance
        session_analysis = self._analyze_training_session(agent.agent_id, training_results)
        
        # Store training history
        if agent.agent_id not in self.training_history:
            self.training_history[agent.agent_id] = []
        self.training_history[agent.agent_id].extend(training_results)
        
        print(f"✅ Conversation training completed!")
        print(f"   Average Score: {session_analysis['average_score']:.1f}/100")
        print(f"   Best Skill: {session_analysis['strongest_skill']}")
        print(f"   Needs Work: {session_analysis['weakest_skill']}")
        
        return {
            "session_results": training_results,
            "session_analysis": session_analysis,
            "improvement_recommendations": self._generate_improvement_plan(session_analysis)
        }
    
    async def _run_conversation_training(self, agent, scenario_type: str, difficulty: float) -> ConversationTrainingResult:
        """Run a single conversation training scenario"""
        
        # Generate property for conversation
        property_deal = self.market_simulator.generate_deal_scenario()
        
        property_data = {
            "asking_price": property_deal.asking_price,
            "city": property_deal.property_data["city"],
            "state": property_deal.property_data["state"],
            "bedrooms": property_deal.property_data["bedrooms"],
            "bathrooms": property_deal.property_data["bathrooms"],
            "house_size": property_deal.property_data["house_size"],
            "property_type": "single_family"
        }
        
        # Generate homeowner profile and conversation
        homeowner_profile = self.homeowner_simulator.generate_homeowner_profile(property_data)
        
        context = ConversationContext(
            scenario_type=scenario_type,
            property_details=property_data,
            market_conditions={
                "trend": property_deal.market_condition.trend,
                "interest_rate": property_deal.market_condition.interest_rate
            },
            previous_interactions=[],
            agent_goal=self._get_scenario_goal(scenario_type),
            difficulty_level=difficulty
        )
        
        # Generate the conversation scenario
        conversation_scenario = await self.homeowner_simulator.generate_conversation_scenario(
            homeowner_profile, context
        )
        
        # Have agent respond to each homeowner message
        agent_responses = await self._simulate_agent_responses(agent, conversation_scenario)
        
        # Evaluate agent performance
        performance_scores = self._evaluate_agent_performance(agent_responses, conversation_scenario)
        
        # Generate feedback
        areas_for_improvement, successful_techniques = self._generate_conversation_feedback(
            agent_responses, conversation_scenario, performance_scores
        )
        
        # Calculate overall score
        overall_score = sum(
            score * self.evaluation_criteria[skill]["weight"] 
            for skill, score in performance_scores.items()
        )
        
        return ConversationTrainingResult(
            agent_id=agent.agent_id,
            conversation_id=f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{np.random.randint(1000, 9999)}",
            scenario_type=scenario_type,
            homeowner_personality=homeowner_profile.personality,
            agent_responses=agent_responses,
            performance_scores=performance_scores,
            areas_for_improvement=areas_for_improvement,
            successful_techniques=successful_techniques,
            overall_score=overall_score,
            timestamp=datetime.now()
        )
    
    def _get_scenario_goal(self, scenario_type: str) -> str:
        """Get the goal for different scenario types"""
        goals = {
            "cold_call": "Generate interest and schedule property evaluation",
            "follow_up": "Address concerns and move to next step",
            "objection_handling": "Overcome resistance and build confidence",
            "negotiation": "Reach mutually beneficial agreement"
        }
        return goals.get(scenario_type, "Build relationship and provide value")
    
    async def _simulate_agent_responses(self, agent, conversation_scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate how the agent would respond in the conversation"""
        
        conversation = conversation_scenario.get("conversation", {}).get("conversation", [])
        homeowner_profile = conversation_scenario.get("homeowner_profile")
        context = conversation_scenario.get("context")
        
        agent_responses = []
        
        # Extract homeowner messages for agent to respond to
        homeowner_messages = [msg for msg in conversation if msg["speaker"] == "homeowner"]
        
        for i, homeowner_msg in enumerate(homeowner_messages):
            # Create context for agent response
            response_context = {
                "homeowner_message": homeowner_msg["message"],
                "homeowner_emotion": homeowner_msg.get("emotion", "neutral"),
                "homeowner_personality": homeowner_profile.personality,
                "conversation_stage": i + 1,
                "scenario_type": context.scenario_type,
                "property_details": context.property_details,
                "previous_messages": conversation[:i*2+1] if i > 0 else []
            }
            
            # Get agent's response (simplified - in real implementation, this would call the actual agent)
            agent_response = await self._get_agent_response(agent, response_context)
            agent_responses.append(agent_response)
        
        return agent_responses
    
    async def _get_agent_response(self, agent, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get agent's response to a homeowner message"""
        
        # This is a simplified version - in practice, you'd call your actual agent
        homeowner_msg = context["homeowner_message"]
        emotion = context["homeowner_emotion"]
        personality = context["homeowner_personality"]
        
        # Simulate agent decision-making
        response_data = {
            "message": self._generate_mock_agent_response(homeowner_msg, emotion, personality),
            "strategy": self._identify_response_strategy(homeowner_msg, emotion),
            "techniques_used": self._identify_techniques_used(homeowner_msg, emotion),
            "context_awareness": self._assess_context_awareness(context),
            "empathy_level": self._assess_empathy_level(homeowner_msg, emotion),
            "value_provided": self._assess_value_provided(homeowner_msg)
        }
        
        return response_data
    
    def _generate_mock_agent_response(self, homeowner_msg: str, emotion: str, personality: str) -> str:
        """Generate a mock agent response (replace with actual agent call)"""
        
        # Simple response generation based on emotion and personality
        if emotion == "skeptical":
            return "I completely understand your skepticism. Many homeowners feel that way initially. Let me share some specific information that might help address your concerns."
        elif emotion == "interested":
            return "I'm glad you're interested! Let me provide you with some detailed market analysis for your area so you can make an informed decision."
        elif emotion == "emotional":
            return "I can hear how much this home means to you, and I want to make sure we find the right approach that honors that connection while helping you achieve your goals."
        else:
            return "Thank you for sharing that with me. Based on what you've told me, I think I can help you explore your options without any pressure."
    
    def _identify_response_strategy(self, homeowner_msg: str, emotion: str) -> str:
        """Identify the strategy used in the response"""
        strategies = {
            "skeptical": "acknowledgment_and_evidence",
            "interested": "information_provision",
            "emotional": "empathy_and_validation",
            "hesitant": "reassurance_and_options"
        }
        return strategies.get(emotion, "general_rapport_building")
    
    def _identify_techniques_used(self, homeowner_msg: str, emotion: str) -> List[str]:
        """Identify conversation techniques used"""
        techniques = []
        
        if emotion == "skeptical":
            techniques.extend(["acknowledgment", "social_proof"])
        elif emotion == "interested":
            techniques.extend(["information_sharing", "expertise_demonstration"])
        elif emotion == "emotional":
            techniques.extend(["empathy", "validation", "emotional_intelligence"])
        
        techniques.append("active_listening")
        return techniques
    
    def _assess_context_awareness(self, context: Dict[str, Any]) -> float:
        """Assess how well agent demonstrates context awareness"""
        # Simplified assessment - would be more sophisticated in practice
        return np.random.uniform(0.6, 0.9)
    
    def _assess_empathy_level(self, homeowner_msg: str, emotion: str) -> float:
        """Assess empathy level in response"""
        # Higher empathy for emotional situations
        if emotion in ["emotional", "worried", "sad"]:
            return np.random.uniform(0.7, 0.95)
        else:
            return np.random.uniform(0.5, 0.8)
    
    def _assess_value_provided(self, homeowner_msg: str) -> float:
        """Assess value provided in response"""
        return np.random.uniform(0.6, 0.85)
    
    def _evaluate_agent_performance(self, agent_responses: List[Dict[str, Any]], 
                                  conversation_scenario: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate agent performance across different skills"""
        
        scores = {}
        
        # Rapport Building
        empathy_scores = [resp.get("empathy_level", 0.5) for resp in agent_responses]
        scores["rapport_building"] = np.mean(empathy_scores) * 100
        
        # Needs Discovery
        context_scores = [resp.get("context_awareness", 0.5) for resp in agent_responses]
        scores["needs_discovery"] = np.mean(context_scores) * 100
        
        # Objection Handling
        objections = conversation_scenario.get("conversation", {}).get("key_objections", [])
        objection_handling_score = 80 if len(objections) > 0 else 60  # Simplified
        scores["objection_handling"] = objection_handling_score
        
        # Value Proposition
        value_scores = [resp.get("value_provided", 0.5) for resp in agent_responses]
        scores["value_proposition"] = np.mean(value_scores) * 100
        
        # Closing Skills
        # Check if agent moved conversation forward
        closing_score = 70 + np.random.uniform(-10, 20)  # Simplified
        scores["closing_skills"] = max(0, min(100, closing_score))
        
        return scores
    
    def _generate_conversation_feedback(self, agent_responses: List[Dict[str, Any]], 
                                      conversation_scenario: Dict[str, Any],
                                      performance_scores: Dict[str, float]) -> tuple:
        """Generate specific feedback for the conversation"""
        
        areas_for_improvement = []
        successful_techniques = []
        
        # Analyze performance scores
        for skill, score in performance_scores.items():
            if score < 70:
                areas_for_improvement.append(f"Improve {skill.replace('_', ' ')}")
            elif score > 85:
                successful_techniques.append(f"Excellent {skill.replace('_', ' ')}")
        
        # Analyze specific techniques used
        all_techniques = []
        for response in agent_responses:
            all_techniques.extend(response.get("techniques_used", []))
        
        technique_counts = {}
        for technique in all_techniques:
            technique_counts[technique] = technique_counts.get(technique, 0) + 1
        
        # Most used techniques are successful
        if technique_counts:
            most_used = max(technique_counts.items(), key=lambda x: x[1])
            successful_techniques.append(f"Effective use of {most_used[0].replace('_', ' ')}")
        
        # Check for missing techniques
        homeowner_personality = conversation_scenario.get("homeowner_profile").personality
        if homeowner_personality == "analytical" and "information_sharing" not in all_techniques:
            areas_for_improvement.append("Provide more data and evidence for analytical personalities")
        
        if homeowner_personality == "emotional" and "empathy" not in all_techniques:
            areas_for_improvement.append("Show more empathy for emotional homeowners")
        
        return areas_for_improvement, successful_techniques
    
    def _analyze_training_session(self, agent_id: str, results: List[ConversationTrainingResult]) -> Dict[str, Any]:
        """Analyze overall training session performance"""
        
        if not results:
            return {"error": "No training results to analyze"}
        
        # Calculate averages
        avg_score = np.mean([r.overall_score for r in results])
        
        # Skill analysis
        skill_averages = {}
        for skill in self.evaluation_criteria.keys():
            scores = [r.performance_scores.get(skill, 0) for r in results]
            skill_averages[skill] = np.mean(scores)
        
        strongest_skill = max(skill_averages.items(), key=lambda x: x[1])
        weakest_skill = min(skill_averages.items(), key=lambda x: x[1])
        
        # Personality performance
        personality_performance = {}
        for result in results:
            personality = result.homeowner_personality
            if personality not in personality_performance:
                personality_performance[personality] = []
            personality_performance[personality].append(result.overall_score)
        
        personality_averages = {
            personality: np.mean(scores) 
            for personality, scores in personality_performance.items()
        }
        
        # Improvement tracking
        if len(results) > 5:
            early_scores = [r.overall_score for r in results[:5]]
            late_scores = [r.overall_score for r in results[-5:]]
            improvement = np.mean(late_scores) - np.mean(early_scores)
        else:
            improvement = 0
        
        return {
            "average_score": avg_score,
            "skill_averages": skill_averages,
            "strongest_skill": strongest_skill[0].replace('_', ' '),
            "weakest_skill": weakest_skill[0].replace('_', ' '),
            "personality_performance": personality_averages,
            "improvement": improvement,
            "total_conversations": len(results),
            "scenario_breakdown": self._analyze_scenario_performance(results)
        }
    
    def _analyze_scenario_performance(self, results: List[ConversationTrainingResult]) -> Dict[str, float]:
        """Analyze performance by scenario type"""
        scenario_performance = {}
        
        for result in results:
            scenario = result.scenario_type
            if scenario not in scenario_performance:
                scenario_performance[scenario] = []
            scenario_performance[scenario].append(result.overall_score)
        
        return {
            scenario: np.mean(scores) 
            for scenario, scores in scenario_performance.items()
        }
    
    def _generate_improvement_plan(self, session_analysis: Dict[str, Any]) -> List[str]:
        """Generate specific improvement recommendations"""
        
        recommendations = []
        
        # Overall performance recommendations
        avg_score = session_analysis.get("average_score", 0)
        if avg_score < 70:
            recommendations.append("Focus on fundamental conversation skills training")
        elif avg_score < 85:
            recommendations.append("Work on advanced techniques and personalization")
        
        # Skill-specific recommendations
        skill_averages = session_analysis.get("skill_averages", {})
        for skill, score in skill_averages.items():
            if score < 70:
                skill_name = skill.replace('_', ' ')
                recommendations.append(f"Additional training needed in {skill_name}")
        
        # Personality-specific recommendations
        personality_performance = session_analysis.get("personality_performance", {})
        for personality, score in personality_performance.items():
            if score < 70:
                recommendations.append(f"Practice conversations with {personality} personality types")
        
        # Scenario-specific recommendations
        scenario_breakdown = session_analysis.get("scenario_breakdown", {})
        for scenario, score in scenario_breakdown.items():
            if score < 70:
                recommendations.append(f"Focus on {scenario.replace('_', ' ')} scenarios")
        
        return recommendations
    
    def get_agent_conversation_history(self, agent_id: str) -> Dict[str, Any]:
        """Get conversation training history for an agent"""
        
        if agent_id not in self.training_history:
            return {"message": "No conversation training history found"}
        
        results = self.training_history[agent_id]
        
        return {
            "total_conversations": len(results),
            "average_score": np.mean([r.overall_score for r in results]),
            "recent_performance": [r.overall_score for r in results[-10:]],
            "personality_experience": list(set(r.homeowner_personality for r in results)),
            "scenario_experience": list(set(r.scenario_type for r in results)),
            "improvement_trend": self._calculate_improvement_trend(results),
            "last_training": results[-1].timestamp.isoformat() if results else None
        }
    
    def _calculate_improvement_trend(self, results: List[ConversationTrainingResult]) -> str:
        """Calculate improvement trend over time"""
        
        if len(results) < 5:
            return "insufficient_data"
        
        scores = [r.overall_score for r in results]
        
        # Simple trend analysis
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]
        
        first_avg = np.mean(first_half)
        second_avg = np.mean(second_half)
        
        if second_avg > first_avg + 5:
            return "improving"
        elif second_avg < first_avg - 5:
            return "declining"
        else:
            return "stable"

# Example usage
async def test_conversation_trainer():
    """Test the conversation trainer"""
    
    print("🗣️ Testing Conversation Trainer")
    print("=" * 40)
    
    # Initialize components
    from ..simulation.market_simulator import MarketSimulator
    from ..services.market_data_service import MarketDataService
    
    market_service = MarketDataService()
    market_simulator = MarketSimulator(market_service)
    
    # Initialize conversation trainer
    trainer = ConversationTrainer(market_simulator)
    
    # Create mock agent
    class MockAgent:
        def __init__(self):
            self.agent_id = "conversation_test_agent"
    
    agent = MockAgent()
    
    # Run conversation training
    print("Running conversation training session...")
    training_result = await trainer.train_agent_on_conversations(
        agent, 
        num_conversations=3,
        scenario_types=["cold_call", "objection_handling"]
    )
    
    print("✅ Conversation training test completed!")
    
    return training_result

if __name__ == "__main__":
    asyncio.run(test_conversation_trainer())