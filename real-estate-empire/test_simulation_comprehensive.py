"""
Comprehensive simulation testing suite
Tests all simulation components thoroughly
"""
import asyncio
import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add app directory to path
from pathlib import Path
current_dir = Path(__file__).parent
app_dir = current_dir / "app"
sys.path.insert(0, str(app_dir))

from simulation.homeowner_simulator import HomeownerConversationSimulator, HomeownerProfile, ConversationContext
from simulation.market_simulator import MarketSimulator
from simulation.agent_trainer import AgentTrainer
from services.market_data_service import MarketDataService
from services.investment_analyzer_service import InvestmentAnalyzerService

class AdvancedMockAgent:
    """Advanced mock agent with different strategies"""
    def __init__(self, agent_id: str, strategy: str = "balanced"):
        self.agent_id = agent_id
        self.strategy = strategy
        self.learning_history = []
    
    async def analyze_deal(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock deal analysis with different strategies"""
        deal = scenario_data.get('deal', {})
        asking_price = deal.get('asking_price', 300000)
        market_condition = deal.get('market_condition', {})
        
        if self.strategy == "aggressive":
            return {
                "action": "pursue",
                "offer_price": asking_price * 0.85,  # Aggressive low offer
                "confidence": 0.9,
                "reasoning": "Aggressive strategy - aim for maximum profit"
            }
        elif self.strategy == "conservative":
            return {
                "action": "pass" if asking_price > 400000 else "pursue",
                "offer_price": asking_price * 0.98,  # Conservative offer
                "confidence": 0.6,
                "reasoning": "Conservative approach - minimize risk"
            }
        else:  # balanced
            market_trend = market_condition.get('trend', 'stable')
            multiplier = 0.92 if market_trend == 'bear' else 0.95
            
            return {
                "action": "pursue" if asking_price < 600000 else "pass",
                "offer_price": asking_price * multiplier,
                "confidence": 0.75,
                "reasoning": "Balanced approach based on market conditions"
            }

async def test_homeowner_personality_consistency():
    """Test homeowner personality consistency across conversations"""
    print("🎭 Testing Homeowner Personality Consistency")
    print("=" * 50)
    
    simulator = HomeownerConversationSimulator()
    personalities = ["analytical", "emotional", "skeptical", "trusting"]
    
    results = {}
    
    for personality in personalities:
        print(f"\nTesting {personality} personality...")
        
        # Create multiple conversations with same personality
        conversations = []
        for i in range(3):
            property_data = {
                "asking_price": 400000 + (i * 50000),
                "city": "Miami",
                "state": "Florida",
                "bedrooms": 3,
                "bathrooms": 2,
                "house_size": 1800,
                "property_type": "single_family"
            }
            
            # Force specific personality
            profile = simulator.generate_homeowner_profile(property_data)
            profile.personality = personality
            
            context = ConversationContext(
                scenario_type="cold_call",
                property_details=property_data,
                market_conditions={"trend": "stable", "inventory": "normal"},
                previous_interactions=[],
                agent_goal="Schedule property evaluation",
                difficulty_level=0.5
            )
            
            conversation_scenario = await simulator.generate_conversation_scenario(profile, context)
            conversations.append(conversation_scenario)
        
        # Analyze consistency
        consistency_scores = []
        for conv in conversations:
            analysis = simulator.analyze_conversation_quality(conv)
            consistency_scores.append(analysis['realism_score'])
        
        avg_consistency = sum(consistency_scores) / len(consistency_scores)
        results[personality] = {
            "average_consistency": avg_consistency,
            "conversations_tested": len(conversations),
            "scores": consistency_scores
        }
        
        print(f"  Average consistency: {avg_consistency:.1f}/100")
    
    print(f"\n📊 Personality Consistency Results:")
    for personality, data in results.items():
        print(f"  {personality.title()}: {data['average_consistency']:.1f}/100")
    
    return results

async def test_market_condition_evolution():
    """Test market condition evolution over time"""
    print("\n📈 Testing Market Condition Evolution")
    print("=" * 50)
    
    market_service = MarketDataService()
    market_simulator = MarketSimulator(market_service)
    
    print("Simulating market evolution over 30 days...")
    
    # Track market evolution
    conditions_history = market_simulator.simulate_market_cycle(days=30)
    
    # Analyze trends
    trends = [c.trend for c in conditions_history]
    interest_rates = [c.interest_rate for c in conditions_history]
    price_momentum = [c.price_momentum for c in conditions_history]
    
    # Calculate statistics
    trend_changes = sum(1 for i in range(1, len(trends)) if trends[i] != trends[i-1])
    avg_interest_rate = sum(interest_rates) / len(interest_rates)
    rate_volatility = max(interest_rates) - min(interest_rates)
    
    print(f"Market Evolution Analysis:")
    print(f"  Trend changes: {trend_changes} over 30 days")
    print(f"  Average interest rate: {avg_interest_rate:.2f}%")
    print(f"  Interest rate volatility: {rate_volatility:.2f}%")
    print(f"  Final trend: {conditions_history[-1].trend}")
    print(f"  Final momentum: {conditions_history[-1].price_momentum:.3f}")
    
    # Test AI market analysis
    print(f"\n🤖 Testing AI market analysis...")
    ai_analysis = await market_simulator.get_ai_market_analysis()
    
    if "error" not in ai_analysis:
        print(f"  AI analysis generated successfully")
        print(f"  Confidence: {ai_analysis.get('confidence', 'N/A')}")
    else:
        print(f"  AI analysis error: {ai_analysis['error']}")
    
    return {
        "trend_changes": trend_changes,
        "avg_interest_rate": avg_interest_rate,
        "rate_volatility": rate_volatility,
        "ai_analysis_success": "error" not in ai_analysis
    }

async def test_agent_learning_progression():
    """Test agent learning and improvement over time"""
    print("\n🎯 Testing Agent Learning Progression")
    print("=" * 50)
    
    # Initialize services
    market_service = MarketDataService()
    market_simulator = MarketSimulator(market_service)
    investment_analyzer = InvestmentAnalyzerService()
    agent_trainer = AgentTrainer(market_simulator, investment_analyzer)
    
    # Test different agent strategies
    strategies = ["aggressive", "conservative", "balanced"]
    results = {}
    
    for strategy in strategies:
        print(f"\nTesting {strategy} agent strategy...")
        
        agent = AdvancedMockAgent(f"{strategy}_agent", strategy)
        
        # Run training sessions with increasing difficulty
        session_results = []
        for session in range(3):
            difficulty = 0.3 + (session * 0.3)  # 0.3, 0.6, 0.9
            
            print(f"  Session {session + 1} (difficulty: {difficulty:.1f})...")
            
            # Create and run scenarios
            scenario_scores = []
            for _ in range(5):  # 5 scenarios per session
                scenario = agent_trainer.create_training_scenario("deal_analysis", difficulty)
                result = await agent_trainer.train_agent(agent, scenario)
                scenario_scores.append(result.performance_score)
            
            avg_score = sum(scenario_scores) / len(scenario_scores)
            session_results.append(avg_score)
            print(f"    Average score: {avg_score:.1f}")
        
        # Calculate improvement
        improvement = session_results[-1] - session_results[0] if len(session_results) > 1 else 0
        
        results[strategy] = {
            "session_scores": session_results,
            "improvement": improvement,
            "final_score": session_results[-1]
        }
        
        print(f"  Overall improvement: {improvement:.1f} points")
    
    print(f"\n📊 Agent Strategy Comparison:")
    for strategy, data in results.items():
        print(f"  {strategy.title()}: Final score {data['final_score']:.1f}, Improvement {data['improvement']:.1f}")
    
    return results

async def test_scenario_difficulty_scaling():
    """Test scenario difficulty scaling"""
    print("\n⚖️ Testing Scenario Difficulty Scaling")
    print("=" * 50)
    
    market_service = MarketDataService()
    market_simulator = MarketSimulator(market_service)
    investment_analyzer = InvestmentAnalyzerService()
    agent_trainer = AgentTrainer(market_simulator, investment_analyzer)
    
    # Test different difficulty levels
    difficulty_levels = [0.1, 0.3, 0.5, 0.7, 0.9]
    scenario_types = ["deal_analysis", "negotiation", "portfolio_management"]
    
    results = {}
    
    for scenario_type in scenario_types:
        print(f"\nTesting {scenario_type} scenarios...")
        
        type_results = {}
        agent = AdvancedMockAgent(f"test_agent_{scenario_type}", "balanced")
        
        for difficulty in difficulty_levels:
            print(f"  Difficulty {difficulty:.1f}...")
            
            # Create multiple scenarios at this difficulty
            scores = []
            for _ in range(3):
                scenario = agent_trainer.create_training_scenario(scenario_type, difficulty)
                result = await agent_trainer.train_agent(agent, scenario)
                scores.append(result.performance_score)
            
            avg_score = sum(scores) / len(scores)
            type_results[difficulty] = avg_score
            print(f"    Average score: {avg_score:.1f}")
        
        results[scenario_type] = type_results
    
    print(f"\n📊 Difficulty Scaling Analysis:")
    for scenario_type, difficulty_scores in results.items():
        print(f"  {scenario_type.title()}:")
        for difficulty, score in difficulty_scores.items():
            print(f"    Difficulty {difficulty:.1f}: {score:.1f} points")
    
    return results

async def test_conversation_batch_generation():
    """Test batch conversation generation"""
    print("\n📦 Testing Batch Conversation Generation")
    print("=" * 50)
    
    simulator = HomeownerConversationSimulator()
    
    # Test batch generation
    property_data_list = [
        {
            "asking_price": 300000,
            "city": "Orlando",
            "state": "Florida",
            "bedrooms": 2,
            "bathrooms": 2,
            "house_size": 1200,
            "property_type": "condo"
        },
        {
            "asking_price": 450000,
            "city": "Tampa",
            "state": "Florida",
            "bedrooms": 3,
            "bathrooms": 2,
            "house_size": 1800,
            "property_type": "single_family"
        },
        {
            "asking_price": 650000,
            "city": "Miami",
            "state": "Florida",
            "bedrooms": 4,
            "bathrooms": 3,
            "house_size": 2400,
            "property_type": "single_family"
        }
    ]
    
    scenario_types = ["cold_call", "follow_up", "negotiation"]
    
    print("Generating batch of 10 conversations...")
    start_time = time.time()
    
    conversations = await simulator.generate_conversation_batch(
        property_data_list, scenario_types, count=10
    )
    
    generation_time = time.time() - start_time
    
    # Analyze batch results
    scenario_type_counts = {}
    personality_counts = {}
    quality_scores = []
    
    for conv in conversations:
        # Count scenario types
        scenario_type = conv.get("context", {}).scenario_type
        scenario_type_counts[scenario_type] = scenario_type_counts.get(scenario_type, 0) + 1
        
        # Count personalities
        personality = conv.get("homeowner_profile", {}).personality
        personality_counts[personality] = personality_counts.get(personality, 0) + 1
        
        # Analyze quality
        quality = simulator.analyze_conversation_quality(conv)
        quality_scores.append(quality['realism_score'])
    
    avg_quality = sum(quality_scores) / len(quality_scores)
    
    print(f"Batch Generation Results:")
    print(f"  Total conversations: {len(conversations)}")
    print(f"  Generation time: {generation_time:.2f} seconds")
    print(f"  Average quality score: {avg_quality:.1f}/100")
    print(f"  Scenario type distribution: {scenario_type_counts}")
    print(f"  Personality distribution: {personality_counts}")
    
    return {
        "total_conversations": len(conversations),
        "generation_time": generation_time,
        "average_quality": avg_quality,
        "scenario_distribution": scenario_type_counts,
        "personality_distribution": personality_counts
    }

async def test_performance_benchmarks():
    """Test performance benchmarks for all components"""
    print("\n⚡ Testing Performance Benchmarks")
    print("=" * 50)
    
    benchmarks = {}
    
    # Benchmark homeowner simulator
    print("Benchmarking homeowner simulator...")
    simulator = HomeownerConversationSimulator()
    
    start_time = time.time()
    for _ in range(5):
        property_data = {
            "asking_price": 400000,
            "city": "Miami",
            "state": "Florida",
            "bedrooms": 3,
            "bathrooms": 2,
            "house_size": 1800,
            "property_type": "single_family"
        }
        
        profile = simulator.generate_homeowner_profile(property_data)
        context = ConversationContext(
            scenario_type="cold_call",
            property_details=property_data,
            market_conditions={"trend": "stable", "inventory": "normal"},
            previous_interactions=[],
            agent_goal="Schedule property evaluation",
            difficulty_level=0.5
        )
        
        await simulator.generate_conversation_scenario(profile, context)
    
    homeowner_time = (time.time() - start_time) / 5
    benchmarks["homeowner_simulator"] = homeowner_time
    
    # Benchmark market simulator
    print("Benchmarking market simulator...")
    market_service = MarketDataService()
    market_simulator = MarketSimulator(market_service)
    
    start_time = time.time()
    for _ in range(10):
        try:
            market_simulator.generate_deal_scenario()
        except:
            pass  # Expected if no data
        market_simulator.get_market_summary()
    
    market_time = (time.time() - start_time) / 10
    benchmarks["market_simulator"] = market_time
    
    # Benchmark agent trainer
    print("Benchmarking agent trainer...")
    investment_analyzer = InvestmentAnalyzerService()
    agent_trainer = AgentTrainer(market_simulator, investment_analyzer)
    agent = AdvancedMockAgent("benchmark_agent", "balanced")
    
    start_time = time.time()
    for _ in range(5):
        scenario = agent_trainer.create_training_scenario("deal_analysis", 0.5)
        await agent_trainer.train_agent(agent, scenario)
    
    trainer_time = (time.time() - start_time) / 5
    benchmarks["agent_trainer"] = trainer_time
    
    print(f"Performance Benchmarks (average time per operation):")
    for component, avg_time in benchmarks.items():
        print(f"  {component}: {avg_time:.3f} seconds")
    
    return benchmarks

async def run_comprehensive_tests():
    """Run all comprehensive simulation tests"""
    print("🚀 Starting Comprehensive Simulation Tests")
    print("=" * 60)
    
    test_results = {}
    
    # Run all tests
    tests = [
        ("Personality Consistency", test_homeowner_personality_consistency),
        ("Market Evolution", test_market_condition_evolution),
        ("Agent Learning", test_agent_learning_progression),
        ("Difficulty Scaling", test_scenario_difficulty_scaling),
        ("Batch Generation", test_conversation_batch_generation),
        ("Performance Benchmarks", test_performance_benchmarks)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            start_time = time.time()
            result = await test_func()
            test_time = time.time() - start_time
            
            test_results[test_name] = {
                "result": result,
                "execution_time": test_time,
                "status": "passed"
            }
            print(f"✅ {test_name} completed in {test_time:.2f} seconds")
            
        except Exception as e:
            test_results[test_name] = {
                "error": str(e),
                "status": "failed"
            }
            print(f"❌ {test_name} failed: {e}")
    
    # Generate comprehensive report
    print(f"\n{'='*60}")
    print("📊 COMPREHENSIVE TEST REPORT")
    print("=" * 60)
    
    passed = sum(1 for result in test_results.values() if result["status"] == "passed")
    total = len(test_results)
    
    print(f"Overall Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print(f"\nDetailed Results:")
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result["status"] == "passed" else "❌ FAILED"
        if result["status"] == "passed":
            time_info = f" ({result['execution_time']:.2f}s)"
        else:
            time_info = f" - Error: {result['error']}"
        
        print(f"  {test_name}: {status}{time_info}")
    
    # Save detailed results
    report_file = f"simulation_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    if passed == total:
        print("🎉 All comprehensive tests passed! Simulation system is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the detailed report for more information.")
    
    return test_results

if __name__ == "__main__":
    # Set up environment
    if not os.getenv('GEMINI_API_KEY'):
        print("⚠️ Warning: GEMINI_API_KEY not found in environment")
        print("Loading from .env file...")
        
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('GEMINI_API_KEY='):
                        key = line.split('=', 1)[1].strip()
                        os.environ['GEMINI_API_KEY'] = key
                        print("✅ Gemini API key loaded from .env file")
                        break
    
    # Run comprehensive tests
    asyncio.run(run_comprehensive_tests())