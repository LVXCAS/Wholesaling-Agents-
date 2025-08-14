#!/usr/bin/env python3
"""
Test the homeowner conversation simulation system
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.simulation.homeowner_simulator import HomeownerConversationSimulator, test_homeowner_simulator
from app.training.conversation_trainer import ConversationTrainer
from app.simulation.market_simulator import MarketSimulator
from app.services.market_data_service import MarketDataService

async def demonstrate_conversation_system():
    """Demonstrate the complete conversation simulation system"""
    
    print("🏠 Real Estate Conversation Simulation System Demo")
    print("=" * 60)
    
    # Test 1: Basic homeowner simulator
    print("\n1. Testing Homeowner Conversation Simulator...")
    conversation_scenario = await test_homeowner_simulator()
    
    # Test 2: Batch conversation generation
    print("\n2. Testing Batch Conversation Generation...")
    
    # Initialize simulator
    simulator = HomeownerConversationSimulator()
    
    # Sample property data for batch generation
    property_data_list = [
        {
            "asking_price": 350000,
            "city": "Miami",
            "state": "Florida",
            "bedrooms": 3,
            "bathrooms": 2,
            "house_size": 1500,
            "property_type": "single_family"
        },
        {
            "asking_price": 750000,
            "city": "Orlando",
            "state": "Florida", 
            "bedrooms": 4,
            "bathrooms": 3,
            "house_size": 2200,
            "property_type": "single_family"
        },
        {
            "asking_price": 225000,
            "city": "Tampa",
            "state": "Florida",
            "bedrooms": 2,
            "bathrooms": 2,
            "house_size": 1200,
            "property_type": "condo"
        }
    ]
    
    scenario_types = ["cold_call", "follow_up", "objection_handling", "negotiation"]
    
    print("   Generating 5 conversation scenarios...")
    batch_conversations = await simulator.generate_conversation_batch(
        property_data_list, scenario_types, count=5
    )
    
    print(f"✅ Generated {len(batch_conversations)} conversations")
    
    # Analyze the batch
    print(f"\n📊 Batch Analysis:")
    personalities = [conv.get("homeowner_profile").personality for conv in batch_conversations]
    scenarios = [conv.get("context").scenario_type for conv in batch_conversations]
    
    print(f"   Personalities: {set(personalities)}")
    print(f"   Scenarios: {set(scenarios)}")
    
    # Show quality analysis for each
    for i, conv in enumerate(batch_conversations, 1):
        analysis = simulator.analyze_conversation_quality(conv)
        profile = conv.get("homeowner_profile")
        context = conv.get("context")
        
        print(f"   Conversation {i}: {profile.personality} homeowner, {context.scenario_type}")
        print(f"     Realism: {analysis['realism_score']:.1f}/100, Length: {analysis['length']} exchanges")
    
    # Test 3: Conversation Training Integration
    print(f"\n3. Testing Conversation Training Integration...")
    
    try:
        # Initialize training components
        market_service = MarketDataService()
        market_simulator = MarketSimulator(market_service)
        conversation_trainer = ConversationTrainer(market_simulator)
        
        # Create mock agent for testing
        class MockConversationAgent:
            def __init__(self):
                self.agent_id = "conversation_demo_agent"
                self.conversation_skills = {
                    "rapport_building": 0.7,
                    "needs_discovery": 0.6,
                    "objection_handling": 0.5,
                    "value_proposition": 0.8,
                    "closing_skills": 0.6
                }
        
        agent = MockConversationAgent()
        
        print(f"   Training agent on 3 conversation scenarios...")
        training_result = await conversation_trainer.train_agent_on_conversations(
            agent, 
            num_conversations=3,
            scenario_types=["cold_call", "objection_handling", "follow_up"]
        )
        
        session_analysis = training_result["session_analysis"]
        print(f"✅ Conversation training completed!")
        print(f"   Average Score: {session_analysis['average_score']:.1f}/100")
        print(f"   Strongest Skill: {session_analysis['strongest_skill']}")
        print(f"   Needs Improvement: {session_analysis['weakest_skill']}")
        
        # Show improvement recommendations
        recommendations = training_result["improvement_recommendations"]
        if recommendations:
            print(f"   Key Recommendations:")
            for rec in recommendations[:2]:
                print(f"     • {rec}")
        
    except Exception as e:
        print(f"   ⚠️ Conversation training test skipped: {e}")
    
    # Test 4: Demonstrate Different Personality Types
    print(f"\n4. Demonstrating Different Homeowner Personalities...")
    
    personalities = ["analytical", "emotional", "skeptical", "trusting"]
    
    for personality in personalities:
        print(f"\n   🎭 {personality.title()} Homeowner:")
        
        # Create a profile with specific personality
        profile = simulator.generate_homeowner_profile(property_data_list[0])
        profile.personality = personality
        
        # Show personality traits
        traits = simulator.personality_templates[personality]
        print(f"     Traits: {', '.join(traits['traits'][:2])}")
        print(f"     Common Phrases: \"{traits['speech_patterns'][0]}\"")
        print(f"     Main Concerns: {', '.join(traits['concerns'][:2])}")
    
    # Test 5: Scenario Type Demonstrations
    print(f"\n5. Demonstrating Different Scenario Types...")
    
    scenario_descriptions = {
        "cold_call": "Initial outreach to homeowner who hasn't expressed interest",
        "follow_up": "Following up on previous conversation or inquiry",
        "objection_handling": "Addressing specific concerns or resistance",
        "negotiation": "Discussing terms, price, or conditions"
    }
    
    for scenario_type, description in scenario_descriptions.items():
        print(f"   📞 {scenario_type.replace('_', ' ').title()}: {description}")
    
    # Test 6: Show Training Value
    print(f"\n6. Training Value for Real Estate Agents:")
    
    training_benefits = [
        "Practice handling different personality types safely",
        "Learn to recognize emotional cues and respond appropriately", 
        "Develop objection handling skills with realistic scenarios",
        "Build confidence through repetitive practice",
        "Get objective performance feedback and scoring",
        "Train on edge cases and difficult situations",
        "Improve conversation flow and timing",
        "Master different scenario types (cold calls, negotiations, etc.)"
    ]
    
    print(f"   Benefits of Conversation Simulation Training:")
    for benefit in training_benefits:
        print(f"     ✓ {benefit}")
    
    print(f"\n🎉 Conversation Simulation System Demo Complete!")
    print("=" * 60)
    
    print(f"\n💡 Next Steps:")
    print(f"   1. Set up Google Gemini API key for realistic conversations")
    print(f"   2. Integrate with your existing agent training pipeline")
    print(f"   3. Create specialized conversation scenarios for your use cases")
    print(f"   4. Build conversation performance dashboards")
    print(f"   5. Use for ongoing agent coaching and improvement")
    
    print(f"\n🔧 To Enable Gemini Integration:")
    print(f"   1. Get API key from Google AI Studio")
    print(f"   2. Set environment variable: GOOGLE_API_KEY=your_key_here")
    print(f"   3. Or pass directly to HomeownerConversationSimulator(api_key)")
    
    return {
        "sample_conversation": conversation_scenario,
        "batch_conversations": batch_conversations,
        "training_result": training_result if 'training_result' in locals() else None
    }

async def quick_conversation_demo():
    """Quick demo showing a single conversation"""
    
    print("🗣️ Quick Conversation Demo")
    print("=" * 30)
    
    # Initialize simulator
    simulator = HomeownerConversationSimulator()
    
    # Generate a conversation
    property_data = {
        "asking_price": 425000,
        "city": "Miami",
        "state": "Florida",
        "bedrooms": 3,
        "bathrooms": 2,
        "house_size": 1650
    }
    
    profile = simulator.generate_homeowner_profile(property_data)
    print(f"Homeowner: {profile.name} ({profile.personality} personality)")
    print(f"Situation: {profile.reason_for_selling}, {profile.motivation} motivation")
    
    from app.simulation.homeowner_simulator import ConversationContext
    
    context = ConversationContext(
        scenario_type="cold_call",
        property_details=property_data,
        market_conditions={"trend": "stable"},
        previous_interactions=[],
        agent_goal="Schedule property evaluation",
        difficulty_level=0.6
    )
    
    conversation = await simulator.generate_conversation_scenario(profile, context)
    
    print(f"\n📞 Conversation:")
    conv_data = conversation.get("conversation", {}).get("conversation", [])
    
    for exchange in conv_data[:6]:  # Show first 6 exchanges
        speaker = "🏠 Homeowner" if exchange["speaker"] == "homeowner" else "🏢 Agent"
        emotion = f" ({exchange.get('emotion', '')})" if exchange.get('emotion') else ""
        print(f"\n{speaker}{emotion}:")
        print(f"  \"{exchange['message']}\"")
    
    if len(conv_data) > 6:
        print(f"\n... and {len(conv_data) - 6} more exchanges")
    
    outcome = conversation.get("conversation", {}).get("outcome", "unknown")
    print(f"\n📊 Outcome: {outcome}")
    
    return conversation

if __name__ == "__main__":
    # Run quick demo by default, full demo with argument
    if len(sys.argv) > 1 and sys.argv[1] == "full":
        asyncio.run(demonstrate_conversation_system())
    else:
        asyncio.run(quick_conversation_demo())