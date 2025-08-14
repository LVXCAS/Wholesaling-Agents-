import random
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.gemini_service import GeminiService

@dataclass
class HomeownerProfile:
    """Profile of a simulated homeowner"""
    name: str
    age: int
    income_level: str  # "low", "middle", "high"
    family_status: str  # "single", "married", "family", "empty_nest"
    motivation: str  # "urgent", "exploring", "reluctant", "motivated"
    personality: str  # "analytical", "emotional", "skeptical", "trusting"
    property_type: str
    location: str
    years_owned: int
    mortgage_status: str  # "paid_off", "low_balance", "high_balance"
    reason_for_selling: str
    price_expectations: str  # "realistic", "high", "flexible"
    timeline: str  # "immediate", "flexible", "long_term"

@dataclass
class ConversationContext:
    """Context for a conversation scenario"""
    scenario_type: str  # "cold_call", "follow_up", "negotiation", "objection_handling"
    property_details: Dict[str, Any]
    market_conditions: Dict[str, Any]
    previous_interactions: List[str]
    agent_goal: str
    difficulty_level: float

class HomeownerConversationSimulator:
    """Generates realistic homeowner conversations using Google Gemini"""
    
    def __init__(self, api_key: Optional[str] = None):
        try:
            self.gemini_service = GeminiService()
            self.use_mock = False
            print("✅ Gemini service initialized successfully")
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize Gemini service: {e}")
            print("Using mock responses instead.")
            self.use_mock = True
            self.gemini_service = None
        
        self._initialize_personality_templates()
    
    def _initialize_personality_templates(self):
        """Initialize personality templates"""
        # Homeowner personality templates
        self.personality_templates = {
            "analytical": {
                "traits": ["data-driven", "asks detailed questions", "wants proof", "compares options"],
                "speech_patterns": ["Can you show me the numbers?", "What's the market data?", "I need to analyze this"],
                "concerns": ["market timing", "financial implications", "comparable sales"]
            },
            "emotional": {
                "traits": ["sentimental", "attached to home", "family-focused", "story-driven"],
                "speech_patterns": ["This house means so much to us", "We raised our kids here", "It's hard to let go"],
                "concerns": ["family impact", "memories", "finding the right buyer"]
            },
            "skeptical": {
                "traits": ["distrustful", "questions motives", "needs convincing", "cautious"],
                "speech_patterns": ["How do I know you're not just trying to make a sale?", "That sounds too good to be true", "I've heard that before"],
                "concerns": ["agent credibility", "hidden costs", "market manipulation"]
            },
            "trusting": {
                "traits": ["cooperative", "relies on expertise", "decision-ready", "optimistic"],
                "speech_patterns": ["What do you recommend?", "You're the expert", "That makes sense"],
                "concerns": ["making the right choice", "timing", "process complexity"]
            }
        }
        
        # Common objections and concerns
        self.common_objections = [
            "The market might get better",
            "I'm not sure about the price",
            "I need to talk to my spouse",
            "The timing isn't right",
            "I'm worried about where we'll move",
            "The fees seem high",
            "I want to try selling myself first",
            "I'm not ready to show the house yet"
        ]
    
    def generate_homeowner_profile(self, property_data: Dict[str, Any]) -> HomeownerProfile:
        """Generate a realistic homeowner profile"""
        
        # Determine profile based on property characteristics
        property_value = property_data.get('asking_price', 300000)
        location = property_data.get('city', 'Unknown')
        bedrooms = property_data.get('bedrooms', 3)
        
        # Income level based on property value
        if property_value < 200000:
            income_level = "low"
        elif property_value < 500000:
            income_level = "middle"
        else:
            income_level = "high"
        
        # Family status based on bedrooms
        if bedrooms <= 2:
            family_status = random.choice(["single", "married"])
        elif bedrooms <= 4:
            family_status = random.choice(["married", "family"])
        else:
            family_status = random.choice(["family", "empty_nest"])
        
        # Generate other characteristics
        motivations = ["urgent", "exploring", "reluctant", "motivated"]
        personalities = list(self.personality_templates.keys())
        
        reasons = [
            "downsizing", "upsizing", "job relocation", "retirement", 
            "divorce", "financial hardship", "investment opportunity", "lifestyle change"
        ]
        
        return HomeownerProfile(
            name=random.choice(["John", "Mary", "David", "Sarah", "Michael", "Lisa", "Robert", "Jennifer"]),
            age=random.randint(25, 75),
            income_level=income_level,
            family_status=family_status,
            motivation=random.choice(motivations),
            personality=random.choice(personalities),
            property_type=property_data.get('property_type', 'single_family'),
            location=location,
            years_owned=random.randint(1, 30),
            mortgage_status=random.choice(["paid_off", "low_balance", "high_balance"]),
            reason_for_selling=random.choice(reasons),
            price_expectations=random.choice(["realistic", "high", "flexible"]),
            timeline=random.choice(["immediate", "flexible", "long_term"])
        )
    
    async def generate_conversation_scenario(self, 
                                           homeowner_profile: HomeownerProfile,
                                           context: ConversationContext) -> Dict[str, Any]:
        """Generate a realistic conversation scenario using Gemini"""
        
        if self.use_mock:
            return self._generate_mock_conversation(homeowner_profile, context)
        
        # Create detailed prompt for Gemini
        prompt = self._create_conversation_prompt(homeowner_profile, context)
        
        try:
            response = await self._call_gemini_async(prompt)
            conversation_data = self._parse_gemini_response(response)
            
            return {
                "homeowner_profile": homeowner_profile,
                "context": context,
                "conversation": conversation_data,
                "training_objectives": self._generate_training_objectives(context),
                "success_metrics": self._generate_success_metrics(homeowner_profile, context)
            }
            
        except Exception as e:
            print(f"Error generating conversation with Gemini: {e}")
            return self._generate_mock_conversation(homeowner_profile, context)
    
    def _create_conversation_prompt(self, profile: HomeownerProfile, context: ConversationContext) -> str:
        """Create a detailed prompt for Gemini to generate realistic conversations"""
        
        personality_info = self.personality_templates[profile.personality]
        
        prompt = f"""
        Generate a realistic real estate conversation between a real estate agent and a homeowner.

        HOMEOWNER PROFILE:
        - Name: {profile.name}
        - Age: {profile.age}
        - Income Level: {profile.income_level}
        - Family Status: {profile.family_status}
        - Motivation: {profile.motivation}
        - Personality: {profile.personality}
        - Years Owned: {profile.years_owned}
        - Reason for Selling: {profile.reason_for_selling}
        - Price Expectations: {profile.price_expectations}
        - Timeline: {profile.timeline}

        PERSONALITY TRAITS:
        - Characteristics: {', '.join(personality_info['traits'])}
        - Common Phrases: {', '.join(personality_info['speech_patterns'])}
        - Main Concerns: {', '.join(personality_info['concerns'])}

        CONVERSATION CONTEXT:
        - Scenario Type: {context.scenario_type}
        - Property: {context.property_details}
        - Market Conditions: {context.market_conditions}
        - Agent Goal: {context.agent_goal}
        - Difficulty Level: {context.difficulty_level}/10

        REQUIREMENTS:
        1. Generate a realistic conversation with 8-12 exchanges
        2. Include natural speech patterns, hesitations, and realistic responses
        3. Incorporate the homeowner's personality traits and concerns
        4. Include at least 2-3 objections or challenges for the agent
        5. Make the conversation feel authentic and unscripted
        6. Include emotional elements appropriate to the situation
        7. End with a clear outcome (positive, negative, or neutral)

        FORMAT YOUR RESPONSE AS JSON:
        {{
            "conversation": [
                {{"speaker": "agent", "message": "agent's opening message"}},
                {{"speaker": "homeowner", "message": "homeowner's response", "emotion": "curious/skeptical/interested/etc"}},
                ...
            ],
            "outcome": "positive/negative/neutral",
            "key_objections": ["objection1", "objection2"],
            "emotional_moments": ["description of emotional moments"],
            "agent_performance_notes": "areas where agent succeeded or could improve"
        }}

        Generate the conversation now:
        """
        
        return prompt
    
    async def _call_gemini_async(self, prompt: str) -> str:
        """Call Gemini API asynchronously"""
        try:
            if self.gemini_service:
                # Use the conversation response method from our service
                context = {
                    'conversation_history': [],
                    'current_topic': 'homeowner_simulation',
                    'agent_message': prompt
                }
                response = await self.gemini_service.generate_conversation_response(context)
                return response.content
            else:
                raise Exception("Gemini service not available")
        except Exception as e:
            raise Exception(f"Gemini API call failed: {e}")
    
    def _parse_gemini_response(self, response: str) -> Dict[str, Any]:
        """Parse Gemini's JSON response"""
        try:
            # Extract JSON from response (Gemini sometimes adds extra text)
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing Gemini response: {e}")
            # Return a basic structure if parsing fails
            return {
                "conversation": [
                    {"speaker": "agent", "message": "Hello, I'm calling about your property listing."},
                    {"speaker": "homeowner", "message": "I'm not really interested right now.", "emotion": "skeptical"}
                ],
                "outcome": "neutral",
                "key_objections": ["not interested"],
                "emotional_moments": [],
                "agent_performance_notes": "Could improve opening approach"
            }
    
    def _generate_mock_conversation(self, profile: HomeownerProfile, context: ConversationContext) -> Dict[str, Any]:
        """Generate a mock conversation when Gemini is not available"""
        
        personality_info = self.personality_templates[profile.personality]
        
        # Create a basic conversation based on personality
        conversation = [
            {"speaker": "agent", "message": f"Hi {profile.name}, I'm calling about your beautiful home in {profile.location}. I have some buyers who might be very interested."},
        ]
        
        # Add homeowner response based on personality
        if profile.personality == "skeptical":
            conversation.append({
                "speaker": "homeowner", 
                "message": "How did you get my number? I'm not sure I want to sell right now.",
                "emotion": "suspicious"
            })
        elif profile.personality == "analytical":
            conversation.append({
                "speaker": "homeowner",
                "message": "What kind of buyers? What price range are we talking about? I'd need to see some market data first.",
                "emotion": "curious"
            })
        elif profile.personality == "emotional":
            conversation.append({
                "speaker": "homeowner",
                "message": "This house means a lot to us. We've lived here for years. It would have to be the right situation.",
                "emotion": "sentimental"
            })
        else:  # trusting
            conversation.append({
                "speaker": "homeowner",
                "message": "Oh, that's interesting. Tell me more about these buyers. What do you think my house is worth?",
                "emotion": "interested"
            })
        
        # Add a few more exchanges
        conversation.extend([
            {"speaker": "agent", "message": "I understand your concerns. Based on recent sales in your area, I believe your home could sell for around $X. Would you be interested in a free market analysis?"},
            {"speaker": "homeowner", "message": random.choice(self.common_objections), "emotion": "hesitant"},
            {"speaker": "agent", "message": "That's completely understandable. Many homeowners feel that way initially. What if we started with just getting you the information so you know your options?"}
        ])
        
        return {
            "homeowner_profile": profile,
            "context": context,
            "conversation": {
                "conversation": conversation,
                "outcome": "neutral",
                "key_objections": [random.choice(self.common_objections)],
                "emotional_moments": ["homeowner expressed attachment to property"],
                "agent_performance_notes": "Good rapport building, could address objections more directly"
            },
            "training_objectives": self._generate_training_objectives(context),
            "success_metrics": self._generate_success_metrics(profile, context)
        }
    
    def _generate_training_objectives(self, context: ConversationContext) -> List[str]:
        """Generate training objectives based on scenario"""
        
        base_objectives = [
            "Build rapport and trust",
            "Listen actively to homeowner concerns",
            "Provide value and market insights"
        ]
        
        scenario_objectives = {
            "cold_call": [
                "Create interest in first 30 seconds",
                "Handle initial skepticism",
                "Secure permission to continue conversation"
            ],
            "follow_up": [
                "Reference previous conversation",
                "Address any concerns raised previously",
                "Move conversation forward"
            ],
            "negotiation": [
                "Find win-win solutions",
                "Handle price objections",
                "Close for next steps"
            ],
            "objection_handling": [
                "Acknowledge concerns without dismissing",
                "Provide evidence and social proof",
                "Redirect to benefits"
            ]
        }
        
        return base_objectives + scenario_objectives.get(context.scenario_type, [])
    
    def _generate_success_metrics(self, profile: HomeownerProfile, context: ConversationContext) -> Dict[str, Any]:
        """Generate success metrics for the conversation"""
        
        return {
            "primary_goal": context.agent_goal,
            "success_indicators": [
                "Homeowner engagement level",
                "Objections successfully addressed",
                "Next steps agreed upon",
                "Rapport established"
            ],
            "difficulty_factors": [
                f"Homeowner personality: {profile.personality}",
                f"Motivation level: {profile.motivation}",
                f"Price expectations: {profile.price_expectations}"
            ],
            "scoring_criteria": {
                "rapport_building": "Did agent establish trust and connection?",
                "needs_discovery": "Did agent uncover homeowner's real motivations?",
                "objection_handling": "How well did agent address concerns?",
                "value_proposition": "Did agent clearly communicate value?",
                "next_steps": "Was a clear next action established?"
            }
        }
    
    async def generate_conversation_batch(self, 
                                        property_data_list: List[Dict[str, Any]], 
                                        scenario_types: List[str],
                                        count: int = 10) -> List[Dict[str, Any]]:
        """Generate a batch of conversation scenarios"""
        
        conversations = []
        
        for i in range(count):
            # Select random property and scenario
            property_data = random.choice(property_data_list)
            scenario_type = random.choice(scenario_types)
            
            # Generate homeowner profile
            profile = self.generate_homeowner_profile(property_data)
            
            # Create context
            context = ConversationContext(
                scenario_type=scenario_type,
                property_details=property_data,
                market_conditions={"trend": "stable", "inventory": "normal"},
                previous_interactions=[],
                agent_goal="Schedule property evaluation" if scenario_type == "cold_call" else "Move to next step",
                difficulty_level=random.uniform(0.3, 0.9)
            )
            
            # Generate conversation
            conversation_scenario = await self.generate_conversation_scenario(profile, context)
            conversations.append(conversation_scenario)
            
            print(f"Generated conversation {i+1}/{count}: {profile.personality} homeowner, {scenario_type} scenario")
        
        return conversations
    
    def analyze_conversation_quality(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the quality and realism of generated conversations"""
        
        conversation = conversation_data.get("conversation", {}).get("conversation", [])
        
        analysis = {
            "length": len(conversation),
            "agent_messages": len([msg for msg in conversation if msg["speaker"] == "agent"]),
            "homeowner_messages": len([msg for msg in conversation if msg["speaker"] == "homeowner"]),
            "emotional_variety": len(set(msg.get("emotion", "neutral") for msg in conversation if msg["speaker"] == "homeowner")),
            "objections_present": len(conversation_data.get("conversation", {}).get("key_objections", [])),
            "outcome": conversation_data.get("conversation", {}).get("outcome", "unknown"),
            "realism_score": self._calculate_realism_score(conversation_data)
        }
        
        return analysis
    
    def _calculate_realism_score(self, conversation_data: Dict[str, Any]) -> float:
        """Calculate a realism score for the conversation"""
        
        score = 0.0
        
        # Check for natural conversation flow
        conversation = conversation_data.get("conversation", {}).get("conversation", [])
        if len(conversation) >= 6:
            score += 20
        
        # Check for objections (realistic conversations have objections)
        objections = conversation_data.get("conversation", {}).get("key_objections", [])
        if len(objections) >= 2:
            score += 25
        
        # Check for emotional moments
        emotional_moments = conversation_data.get("conversation", {}).get("emotional_moments", [])
        if emotional_moments:
            score += 20
        
        # Check for personality consistency
        profile = conversation_data.get("homeowner_profile")
        if profile and self._check_personality_consistency(conversation, profile):
            score += 25
        
        # Check for realistic outcome
        outcome = conversation_data.get("conversation", {}).get("outcome", "")
        if outcome in ["positive", "negative", "neutral"]:
            score += 10
        
        return min(100.0, score)
    
    def _check_personality_consistency(self, conversation: List[Dict], profile: HomeownerProfile) -> bool:
        """Check if conversation is consistent with homeowner personality"""
        
        personality_traits = self.personality_templates.get(profile.personality, {})
        speech_patterns = personality_traits.get("speech_patterns", [])
        
        homeowner_messages = [msg["message"] for msg in conversation if msg["speaker"] == "homeowner"]
        
        # Simple check: see if any speech patterns are reflected
        for message in homeowner_messages:
            for pattern in speech_patterns:
                if any(word in message.lower() for word in pattern.lower().split()):
                    return True
        
        return False

# Example usage and testing
async def test_homeowner_simulator():
    """Test the homeowner conversation simulator"""
    
    print("🏠 Testing Homeowner Conversation Simulator")
    print("=" * 50)
    
    # Initialize simulator (will use mock if no API key)
    simulator = HomeownerConversationSimulator()
    
    # Sample property data
    property_data = {
        "asking_price": 450000,
        "city": "Miami",
        "state": "Florida",
        "bedrooms": 3,
        "bathrooms": 2,
        "house_size": 1800,
        "property_type": "single_family"
    }
    
    # Generate homeowner profile
    profile = simulator.generate_homeowner_profile(property_data)
    print(f"Generated Profile: {profile.name}, {profile.age}yo, {profile.personality} personality")
    print(f"Motivation: {profile.motivation}, Reason: {profile.reason_for_selling}")
    
    # Create conversation context
    context = ConversationContext(
        scenario_type="cold_call",
        property_details=property_data,
        market_conditions={"trend": "stable", "inventory": "normal"},
        previous_interactions=[],
        agent_goal="Schedule property evaluation",
        difficulty_level=0.7
    )
    
    # Generate conversation
    print(f"\nGenerating {context.scenario_type} conversation...")
    conversation_scenario = await simulator.generate_conversation_scenario(profile, context)
    
    # Display conversation
    print(f"\n📞 Conversation Preview:")
    conversation = conversation_scenario.get("conversation", {}).get("conversation", [])
    for i, exchange in enumerate(conversation[:4]):  # Show first 4 exchanges
        speaker = exchange["speaker"].title()
        message = exchange["message"][:100] + "..." if len(exchange["message"]) > 100 else exchange["message"]
        emotion = exchange.get("emotion", "")
        emotion_text = f" ({emotion})" if emotion else ""
        print(f"  {speaker}{emotion_text}: {message}")
    
    if len(conversation) > 4:
        print(f"  ... and {len(conversation) - 4} more exchanges")
    
    # Show analysis
    analysis = simulator.analyze_conversation_quality(conversation_scenario)
    print(f"\n📊 Conversation Analysis:")
    print(f"  Length: {analysis['length']} exchanges")
    print(f"  Objections: {analysis['objections_present']}")
    print(f"  Outcome: {analysis['outcome']}")
    print(f"  Realism Score: {analysis['realism_score']:.1f}/100")
    
    # Show training objectives
    objectives = conversation_scenario.get("training_objectives", [])
    print(f"\n🎯 Training Objectives:")
    for obj in objectives[:3]:
        print(f"  • {obj}")
    
    print(f"\n✅ Homeowner Simulator Test Complete!")
    
    return conversation_scenario

if __name__ == "__main__":
    asyncio.run(test_homeowner_simulator())