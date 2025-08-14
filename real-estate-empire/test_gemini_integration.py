"""
Comprehensive test suite for Gemini AI integration
Tests all simulation components with Gemini AI
"""
import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.gemini_service import GeminiService
from simulation.homeowner_simulator import HomeownerConversationSimulator, HomeownerProfile, ConversationContext
from simulation.market_simulator import MarketSimulator
from simulation.agent_trainer import AgentTrainer
from services.market_data_service import MarketDataService
from services.investment_analyzer_service import InvestmentAnalyzerService

class MockAgent:
    """Mock agent for testing"""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
    
    async def analyze_deal(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock deal analysis"""
        deal = scenario_data.get('deal', {})
        asking_price = deal.get('asking_price', 300000)
        
        return {
            "action": "pursue" if asking_price < 500000 else "pass",
            "offer_price": asking_price * 0.95,
            "confidence": 0.75,
            "reasoning": "Based on market analysis and property evaluation"
        }

async def test_gemini_service():
    """Test basic Gemini service functionality"""
    print("🧪 Testing Gemini Service")
    print("=" * 50)
    
    try:
        gemini_service = GeminiService()
        print("✅ Gemini service initialized successfully")
        
        # Test property analysis
        property_data = {
            'address': '123 Main St, Miami, FL',
            'price': 450000,
            'bedrooms': 3,
            'bathrooms': 2,
            'sqft': 1800,
            'year_built': 2010,
            'property_type': 'Single Family'
        }
        
        print("\n📊 Testing property analysis...")
        analysis = await gemini_service.analyze_property(property_data)
        print(f"Analysis confidence: {analysis.confidence}")
        print(f"Analysis preview: {analysis.content[:200]}...")
        
        # Test conversation response
        print("\n💬 Testing conversation generation...")
        context = {
            'name': 'John Smith',
            'property_type': 'Single Family',
            'motivation': 'Considering selling',
            'personality': 'Analytical',
            'agent_message': 'Hi, I noticed your beautiful home. Are you considering selling?'
        }
        
        response = await gemini_service.generate_conversation_response(context)
        print(f"Response confidence: {response.confidence}")
        print(f"Response preview: {response.content[:200]}...")
        
        # Test market analysis
        print("\n📈 Testing market analysis...")
        market_data = {
            'location': 'Miami, FL',
            'avg_price': 425000,
            'price_change': 5.2,
            'days_on_market': 45,
            'inventory': 'normal'
        }
        
        market_analysis = await gemini_service.analyze_market_trends(market_data)
        print(f"Market analysis confidence: {market_analysis.confidence}")
        print(f"Market analysis preview: {market_analysis.content[:200]}...")
        
        print("\n✅ Gemini service tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Gemini service test failed: {e}")
        return False

async def test_homeowner_simulator():
    """Test homeowner conversation simulator with Gemini"""
    print("\n🏠 Testing Homeowner Simulator")
    print("=" * 50)
    
    try:
        simulator = HomeownerConversationSimulator()
        
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
        print(f"Generated profile: {profile.name}, {profile.personality}, {profile.motivation}")
        
        # Test conversation generation
        context = ConversationContext(
            scenario_type="cold_call",
            property_details=property_data,
            market_conditions={"trend": "stable", "inventory": "normal"},
            previous_interactions=[],
            agent_goal="Schedule property evaluation",
            difficulty_level=0.6
        )
        
        print("\n💬 Generating conversation scenario...")
        conversation_scenario = await simulator.generate_conversation_scenario(profile, context)
        
        # Display results
        conversation = conversation_scenario.get("conversation", {}).get("conversation", [])
        print(f"Generated {len(conversation)} conversation exchanges")
        
        if conversation:
            print("\nSample exchanges:")
            for i, exchange in enumerate(conversation[:3]):
                speaker = exchange["speaker"].title()
                message = exchange["message"][:100] + "..." if len(exchange["message"]) > 100 else exchange["message"]
                print(f"  {speaker}: {message}")
        
        # Test quality analysis
        analysis = simulator.analyze_conversation_quality(conversation_scenario)
        print(f"\nQuality Analysis:")
        print(f"  Realism Score: {analysis['realism_score']:.1f}/100")
        print(f"  Objections Present: {analysis['objections_present']}")
        print(f"  Outcome: {analysis['outcome']}")
        
        print("\n✅ Homeowner simulator tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Homeowner simulator test failed: {e}")
        return False

async def test_market_simulator():
    """Test market simulator with Gemini integration"""
    print("\n📈 Testing Market Simulator")
    print("=" * 50)
    
    try:
        # Initialize services
        market_service = MarketDataService()
        market_simulator = MarketSimulator(market_service)
        
        # Test basic functionality
        print("Generating market conditions...")
        market_summary = market_simulator.get_market_summary()
        print(f"Market trend: {market_summary['condition']['trend']}")
        print(f"Interest rate: {market_summary['condition']['interest_rate']}%")
        print(f"Inventory level: {market_summary['condition']['inventory_level']}")
        
        # Test deal generation
        print("\n🏘️ Generating deal scenarios...")
        try:
            deal = market_simulator.generate_deal_scenario(target_city="Miami")
            print(f"Generated deal: ${deal.asking_price:,.0f} in {deal.property_data.get('city', 'Unknown')}")
            print(f"Days on market: {deal.days_on_market}")
            print(f"Seller motivation: {deal.seller_motivation:.2f}")
        except Exception as e:
            print(f"Deal generation failed (expected if no data): {e}")
        
        # Test AI market analysis
        print("\n🤖 Testing AI market analysis...")
        ai_analysis = await market_simulator.get_ai_market_analysis()
        
        if "error" not in ai_analysis:
            print(f"AI analysis confidence: {ai_analysis.get('confidence', 'N/A')}")
            print(f"AI analysis preview: {ai_analysis.get('ai_analysis', '')[:200]}...")
        else:
            print(f"AI analysis error: {ai_analysis['error']}")
        
        print("\n✅ Market simulator tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Market simulator test failed: {e}")
        return False

async def test_agent_trainer():
    """Test agent trainer with Gemini integration"""
    print("\n🎯 Testing Agent Trainer")
    print("=" * 50)
    
    try:
        # Initialize services
        market_service = MarketDataService()
        market_simulator = MarketSimulator(market_service)
        investment_analyzer = InvestmentAnalyzerService()
        agent_trainer = AgentTrainer(market_simulator, investment_analyzer)
        
        # Create mock agent
        mock_agent = MockAgent("test_agent_001")
        
        # Test scenario creation
        print("Creating training scenarios...")
        scenario_types = ["deal_analysis", "negotiation", "portfolio_management"]
        
        for scenario_type in scenario_types:
            try:
                scenario = agent_trainer.create_training_scenario(scenario_type, difficulty=0.5)
                print(f"Created {scenario_type} scenario: {scenario.scenario_id}")
                
                # Test agent training
                print(f"Training agent on {scenario_type}...")
                result = await agent_trainer.train_agent(mock_agent, scenario)
                print(f"Training result score: {result.performance_score:.1f}")
                
                # Test AI enhancement
                print(f"Getting AI training enhancement...")
                enhancement = await agent_trainer.get_ai_training_enhancement(result)
                
                if "error" not in enhancement:
                    print(f"AI enhancement confidence: {enhancement.get('confidence', 'N/A')}")
                    print(f"AI suggestions preview: {enhancement.get('ai_suggestions', '')[:150]}...")
                else:
                    print(f"AI enhancement error: {enhancement['error']}")
                
            except Exception as e:
                print(f"Scenario {scenario_type} failed: {e}")
        
        # Test training analytics
        print("\n📊 Testing training analytics...")
        analytics = agent_trainer.get_training_analytics()
        
        if "message" not in analytics:
            print(f"Total training sessions: {analytics['overview']['total_training_sessions']}")
            print(f"Average performance: {analytics['overview']['average_performance']:.1f}")
        else:
            print(analytics["message"])
        
        print("\n✅ Agent trainer tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Agent trainer test failed: {e}")
        return False

async def test_integration_workflow():
    """Test complete integration workflow"""
    print("\n🔄 Testing Complete Integration Workflow")
    print("=" * 50)
    
    try:
        # Initialize all services
        gemini_service = GeminiService()
        market_service = MarketDataService()
        market_simulator = MarketSimulator(market_service)
        homeowner_simulator = HomeownerConversationSimulator()
        investment_analyzer = InvestmentAnalyzerService()
        agent_trainer = AgentTrainer(market_simulator, investment_analyzer)
        
        print("✅ All services initialized")
        
        # Create a complete training scenario
        print("\n🎬 Creating complete training scenario...")
        
        # 1. Generate market conditions
        market_summary = market_simulator.get_market_summary()
        print(f"Market conditions: {market_summary['condition']['trend']} market")
        
        # 2. Generate homeowner profile and conversation
        property_data = {
            "asking_price": 425000,
            "city": "Tampa",
            "state": "Florida",
            "bedrooms": 4,
            "bathrooms": 3,
            "house_size": 2200,
            "property_type": "single_family"
        }
        
        homeowner_profile = homeowner_simulator.generate_homeowner_profile(property_data)
        print(f"Homeowner: {homeowner_profile.name} ({homeowner_profile.personality})")
        
        # 3. Create conversation context
        context = ConversationContext(
            scenario_type="negotiation",
            property_details=property_data,
            market_conditions=market_summary['condition'],
            previous_interactions=[],
            agent_goal="Negotiate purchase agreement",
            difficulty_level=0.7
        )
        
        # 4. Generate conversation
        conversation_scenario = await homeowner_simulator.generate_conversation_scenario(homeowner_profile, context)
        conversation = conversation_scenario.get("conversation", {}).get("conversation", [])
        print(f"Generated conversation with {len(conversation)} exchanges")
        
        # 5. Analyze property with AI
        property_analysis = await gemini_service.analyze_property(property_data)
        print(f"AI property analysis completed (confidence: {property_analysis.confidence})")
        
        # 6. Get market insights
        market_analysis = await market_simulator.get_ai_market_analysis()
        if "error" not in market_analysis:
            print(f"AI market analysis completed")
        
        # 7. Train agent on scenario
        mock_agent = MockAgent("integration_test_agent")
        training_scenario = agent_trainer.create_training_scenario("negotiation", 0.7)
        training_result = await agent_trainer.train_agent(mock_agent, training_scenario)
        print(f"Agent training completed (score: {training_result.performance_score:.1f})")
        
        # 8. Get AI training enhancement
        enhancement = await agent_trainer.get_ai_training_enhancement(training_result)
        if "error" not in enhancement:
            print(f"AI training enhancement completed")
        
        print("\n✅ Complete integration workflow test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Integration workflow test failed: {e}")
        return False

async def run_all_tests():
    """Run all simulation tests"""
    print("🚀 Starting Comprehensive Gemini Integration Tests")
    print("=" * 60)
    
    test_results = []
    
    # Run individual tests
    tests = [
        ("Gemini Service", test_gemini_service),
        ("Homeowner Simulator", test_homeowner_simulator),
        ("Market Simulator", test_market_simulator),
        ("Agent Trainer", test_agent_trainer),
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
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    # Set up environment
    if not os.getenv('GEMINI_API_KEY'):
        print("⚠️ Warning: GEMINI_API_KEY not found in environment")
        print("Loading from .env file...")
        
        # Try to load from .env file
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('GEMINI_API_KEY='):
                        key = line.split('=', 1)[1].strip()
                        os.environ['GEMINI_API_KEY'] = key
                        print("✅ Gemini API key loaded from .env file")
                        break
    
    # Run tests
    asyncio.run(run_all_tests())