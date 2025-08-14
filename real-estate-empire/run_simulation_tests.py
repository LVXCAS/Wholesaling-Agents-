"""
Test runner for all simulation components
Handles import paths and runs comprehensive tests
"""
import os
import sys
import asyncio
from pathlib import Path

# Add the app directory to Python path
current_dir = Path(__file__).parent
app_dir = current_dir / "app"
sys.path.insert(0, str(app_dir))

# Set up environment
if not os.getenv('GEMINI_API_KEY'):
    env_path = current_dir / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('GEMINI_API_KEY='):
                    key = line.split('=', 1)[1].strip()
                    os.environ['GEMINI_API_KEY'] = key
                    print("✅ Gemini API key loaded from .env file")
                    break

async def test_basic_imports():
    """Test that all imports work correctly"""
    print("🔧 Testing Basic Imports")
    print("=" * 50)
    
    try:
        from services.gemini_service import GeminiService
        print("✅ GeminiService imported successfully")
        
        gemini_service = GeminiService()
        print("✅ GeminiService initialized successfully")
        
        # Test basic property analysis
        property_data = {
            'address': '123 Test St, Miami, FL',
            'price': 450000,
            'bedrooms': 3,
            'bathrooms': 2,
            'sqft': 1800,
            'year_built': 2010,
            'property_type': 'Single Family'
        }
        
        print("🏠 Testing property analysis...")
        analysis = await gemini_service.analyze_property(property_data)
        print(f"Analysis confidence: {analysis.confidence}")
        print(f"Analysis preview: {analysis.content[:150]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

async def test_homeowner_simulator():
    """Test homeowner simulator functionality"""
    print("\n🏠 Testing Homeowner Simulator")
    print("=" * 50)
    
    try:
        from simulation.homeowner_simulator import HomeownerConversationSimulator, ConversationContext
        
        simulator = HomeownerConversationSimulator()
        print("✅ HomeownerConversationSimulator initialized")
        
        # Test profile generation
        property_data = {
            "asking_price": 350000,
            "city": "Orlando",
            "state": "Florida",
            "bedrooms": 3,
            "bathrooms": 2,
            "house_size": 1600,
            "property_type": "single_family"
        }
        
        profile = simulator.generate_homeowner_profile(property_data)
        print(f"✅ Generated profile: {profile.name}, {profile.personality}, {profile.motivation}")
        
        # Test conversation generation
        context = ConversationContext(
            scenario_type="cold_call",
            property_details=property_data,
            market_conditions={"trend": "stable", "inventory": "normal"},
            previous_interactions=[],
            agent_goal="Schedule property evaluation",
            difficulty_level=0.6
        )
        
        print("💬 Generating conversation scenario...")
        conversation_scenario = await simulator.generate_conversation_scenario(profile, context)
        
        conversation = conversation_scenario.get("conversation", {}).get("conversation", [])
        print(f"✅ Generated {len(conversation)} conversation exchanges")
        
        if conversation:
            print("Sample exchange:")
            exchange = conversation[0]
            speaker = exchange["speaker"].title()
            message = exchange["message"][:100] + "..." if len(exchange["message"]) > 100 else exchange["message"]
            print(f"  {speaker}: {message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Homeowner simulator test failed: {e}")
        return False

async def test_conversation_generation():
    """Test conversation generation with different personalities"""
    print("\n🎭 Testing Conversation Generation")
    print("=" * 50)
    
    try:
        from services.gemini_service import GeminiService
        
        gemini_service = GeminiService()
        
        # Test different conversation contexts
        contexts = [
            {
                'name': 'John Smith',
                'property_type': 'Single Family',
                'motivation': 'Urgent sale needed',
                'personality': 'Analytical',
                'agent_message': 'Hi John, I understand you need to sell quickly. Can we discuss your timeline?'
            },
            {
                'name': 'Mary Johnson',
                'property_type': 'Condo',
                'motivation': 'Exploring options',
                'personality': 'Emotional',
                'agent_message': 'Hi Mary, I noticed your beautiful condo. Are you considering any changes?'
            },
            {
                'name': 'Bob Wilson',
                'property_type': 'Townhouse',
                'motivation': 'Investment opportunity',
                'personality': 'Skeptical',
                'agent_message': 'Hi Bob, I have an investor interested in properties like yours.'
            }
        ]
        
        for i, context in enumerate(contexts, 1):
            print(f"\nTesting conversation {i}: {context['personality']} personality")
            
            response = await gemini_service.generate_conversation_response(context)
            print(f"  Confidence: {response.confidence}")
            print(f"  Response: {response.content[:120]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Conversation generation test failed: {e}")
        return False

async def test_market_analysis():
    """Test market analysis functionality"""
    print("\n📈 Testing Market Analysis")
    print("=" * 50)
    
    try:
        from services.gemini_service import GeminiService
        
        gemini_service = GeminiService()
        
        # Test market trend analysis
        market_data = {
            'location': 'Miami, FL',
            'avg_price': 425000,
            'price_change': 5.2,
            'days_on_market': 45,
            'inventory': 'normal',
            'recent_sales': [
                {'price': 420000, 'days_on_market': 30, 'location': 'Miami, FL'},
                {'price': 450000, 'days_on_market': 25, 'location': 'Miami, FL'},
                {'price': 380000, 'days_on_market': 60, 'location': 'Miami, FL'}
            ]
        }
        
        print("Analyzing market trends...")
        analysis = await gemini_service.analyze_market_trends(market_data)
        print(f"✅ Market analysis completed")
        print(f"  Confidence: {analysis.confidence}")
        print(f"  Analysis preview: {analysis.content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Market analysis test failed: {e}")
        return False

async def test_agent_training_enhancement():
    """Test agent training enhancement"""
    print("\n🎯 Testing Agent Training Enhancement")
    print("=" * 50)
    
    try:
        from services.gemini_service import GeminiService
        
        gemini_service = GeminiService()
        
        # Mock training data
        training_data = {
            "scenario_type": "deal_analysis",
            "performance_metrics": {
                "score": 75.5,
                "agent_id": "test_agent_001"
            },
            "conversation_log": [
                "Agent analyzed property at $450,000",
                "Agent offered $425,000 (94.4% of asking)",
                "Decision was appropriate for market conditions"
            ],
            "outcome": "success"
        }
        
        print("Generating training enhancement suggestions...")
        enhancement = await gemini_service.enhance_agent_training(training_data)
        print(f"✅ Training enhancement completed")
        print(f"  Confidence: {enhancement.confidence}")
        print(f"  Suggestions preview: {enhancement.content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent training enhancement test failed: {e}")
        return False

async def test_integration_workflow():
    """Test complete integration workflow"""
    print("\n🔄 Testing Integration Workflow")
    print("=" * 50)
    
    try:
        from services.gemini_service import GeminiService
        
        gemini_service = GeminiService()
        
        # Simulate a complete real estate analysis workflow
        print("1. Analyzing property...")
        property_data = {
            'address': '456 Ocean Drive, Miami Beach, FL',
            'price': 750000,
            'bedrooms': 2,
            'bathrooms': 2,
            'sqft': 1200,
            'year_built': 2015,
            'property_type': 'Condo'
        }
        
        property_analysis = await gemini_service.analyze_property(property_data)
        print(f"   ✅ Property analysis completed (confidence: {property_analysis.confidence})")
        
        print("2. Generating homeowner conversation...")
        conversation_context = {
            'name': 'Sarah Martinez',
            'property_type': 'Condo',
            'motivation': 'Considering selling',
            'personality': 'Analytical',
            'agent_message': 'Hi Sarah, I see you have a beautiful oceanfront condo. The market is very strong right now.'
        }
        
        conversation_response = await gemini_service.generate_conversation_response(conversation_context)
        print(f"   ✅ Conversation generated (confidence: {conversation_response.confidence})")
        
        print("3. Analyzing market conditions...")
        market_data = {
            'location': 'Miami Beach, FL',
            'avg_price': 680000,
            'price_change': 8.5,
            'days_on_market': 35,
            'inventory': 'low'
        }
        
        market_analysis = await gemini_service.analyze_market_trends(market_data)
        print(f"   ✅ Market analysis completed (confidence: {market_analysis.confidence})")
        
        print("4. Enhancing agent training...")
        training_data = {
            "scenario_type": "luxury_condo_analysis",
            "performance_metrics": {"score": 88.2, "agent_id": "luxury_specialist"},
            "conversation_log": ["Successful high-value property analysis"],
            "outcome": "excellent"
        }
        
        training_enhancement = await gemini_service.enhance_agent_training(training_data)
        print(f"   ✅ Training enhancement completed (confidence: {training_enhancement.confidence})")
        
        print("\n✅ Complete integration workflow successful!")
        return True
        
    except Exception as e:
        print(f"❌ Integration workflow test failed: {e}")
        return False

async def run_all_tests():
    """Run all simulation tests"""
    print("🚀 Starting Simulation Test Suite")
    print("=" * 60)
    
    test_results = []
    
    # Run tests in sequence
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Homeowner Simulator", test_homeowner_simulator),
        ("Conversation Generation", test_conversation_generation),
        ("Market Analysis", test_market_analysis),
        ("Agent Training Enhancement", test_agent_training_enhancement),
        ("Integration Workflow", test_integration_workflow)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            test_results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Gemini integration is working correctly.")
        print("\n📋 Next Steps:")
        print("  • Run comprehensive tests: python test_simulation_comprehensive.py")
        print("  • Run performance tests: python test_simulation_performance.py")
        print("  • Test specific components individually")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(run_all_tests())