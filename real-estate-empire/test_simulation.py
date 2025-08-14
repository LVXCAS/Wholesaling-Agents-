#!/usr/bin/env python3
"""
Test script for agent simulation system
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.market_data_service import MarketDataService
from app.services.property_valuation_service import PropertyValuationService
from app.services.investment_analyzer_service import InvestmentAnalyzerService
from app.simulation.market_simulator import MarketSimulator
from app.simulation.agent_trainer import AgentTrainer
from app.agents.portfolio_agent import PortfolioAgent

async def test_simulation_system():
    print("🤖 Testing Real Estate Agent Simulation System")
    print("=" * 60)
    
    # Initialize services
    print("1. Initializing services...")
    market_service = MarketDataService()
    valuation_service = PropertyValuationService(market_service)
    investment_service = InvestmentAnalyzerService(market_service, valuation_service)
    
    print("2. Initializing simulation components...")
    market_simulator = MarketSimulator(market_service)
    agent_trainer = AgentTrainer(market_simulator, investment_service)
    
    # Test market simulation
    print("\n📊 Testing Market Simulation...")
    try:
        market_summary = market_simulator.get_market_summary()
        print(f"✅ Market Condition: {market_summary['condition']['trend']} market")
        print(f"   Interest Rate: {market_summary['condition']['interest_rate']}%")
        print(f"   Inventory Level: {market_summary['condition']['inventory_level']}")
        print(f"   Price Momentum: {market_summary['condition']['price_momentum']:.3f}")
    except Exception as e:
        print(f"❌ Market simulation error: {e}")
    
    # Test deal generation
    print("\n🏠 Testing Deal Generation...")
    try:
        deal = market_simulator.generate_deal_scenario("Miami", "Florida")
        print(f"✅ Generated deal: {deal.property_id}")
        print(f"   Property: {deal.property_data['bedrooms']}bed/{deal.property_data['bathrooms']}bath")
        print(f"   Asking Price: ${deal.asking_price:,.0f}")
        print(f"   Market Value: ${deal.market_value:,.0f}")
        print(f"   Seller Motivation: {deal.seller_motivation:.2f}")
        print(f"   Days on Market: {deal.days_on_market}")
    except Exception as e:
        print(f"❌ Deal generation error: {e}")
        return
    
    # Test batch deal generation
    print("\n📦 Testing Batch Deal Generation...")
    try:
        batch_deals = market_simulator.generate_batch_scenarios(5, ["Miami", "Orlando"])
        print(f"✅ Generated {len(batch_deals)} deals")
        for i, deal in enumerate(batch_deals[:3], 1):
            print(f"   {i}. {deal.property_data['city']} - ${deal.asking_price:,.0f}")
    except Exception as e:
        print(f"❌ Batch generation error: {e}")
    
    # Test training scenario creation
    print("\n🎯 Testing Training Scenario Creation...")
    try:
        scenario = agent_trainer.create_training_scenario("deal_analysis", difficulty=0.7)
        print(f"✅ Created training scenario: {scenario.scenario_id}")
        print(f"   Type: {scenario.scenario_type}")
        print(f"   Difficulty: {scenario.difficulty_level}")
        print(f"   Learning Objectives: {len(scenario.learning_objectives)}")
        print(f"   Expected Action: {'Pursue' if scenario.expected_outcome.get('should_pursue') else 'Pass'}")
    except Exception as e:
        print(f"❌ Training scenario error: {e}")
        return
    
    # Test agent training
    print("\n🤖 Testing Agent Training...")
    try:
        # Create a simple mock agent for testing
        class MockAgent:
            def __init__(self):
                self.agent_id = "test_agent_001"
            
            async def analyze_deal(self, scenario_data):
                # Simple mock decision logic
                deal = scenario_data["deal"]
                asking_price = deal["asking_price"]
                
                # Mock analysis
                action = "pursue" if asking_price < 500000 else "pass"
                offer_price = asking_price * 0.95 if action == "pursue" else 0
                
                return {
                    "action": action,
                    "offer_price": offer_price,
                    "confidence": 0.75,
                    "reasoning": "Mock agent decision based on price threshold"
                }
        
        mock_agent = MockAgent()
        
        # Train on the scenario we created
        result = await agent_trainer.train_agent(mock_agent, scenario)
        print(f"✅ Agent training completed")
        print(f"   Performance Score: {result.performance_score:.1f}/100")
        print(f"   Decision: {result.decision.get('action', 'unknown')}")
        print(f"   Learning Points: {len(result.learning_points)}")
        
        if result.learning_points:
            print(f"   Key Learning: {result.learning_points[0]}")
    
    except Exception as e:
        print(f"❌ Agent training error: {e}")
    
    # Test training session
    print("\n🏋️ Testing Training Session...")
    try:
        session_result = await agent_trainer.run_training_session(
            mock_agent, num_scenarios=3, scenario_types=["deal_analysis"]
        )
        
        summary = session_result["session_summary"]
        print(f"✅ Training session completed")
        print(f"   Scenarios: {summary['scenarios_completed']}")
        print(f"   Average Score: {summary['average_score']:.1f}")
        print(f"   Improvement: {summary['improvement']:.1f}")
        print(f"   Best Score: {summary['best_score']:.1f}")
        
    except Exception as e:
        print(f"❌ Training session error: {e}")
    
    # Test market cycle simulation
    print("\n📈 Testing Market Cycle Simulation...")
    try:
        conditions = market_simulator.simulate_market_cycle(30)  # 30 days
        print(f"✅ Simulated {len(conditions)} days of market conditions")
        
        # Analyze trends
        bull_days = sum(1 for c in conditions if c.trend == "bull")
        bear_days = sum(1 for c in conditions if c.trend == "bear")
        stable_days = sum(1 for c in conditions if c.trend == "stable")
        
        print(f"   Bull market days: {bull_days}")
        print(f"   Bear market days: {bear_days}")
        print(f"   Stable market days: {stable_days}")
        
        avg_rate = sum(c.interest_rate for c in conditions) / len(conditions)
        print(f"   Average interest rate: {avg_rate:.2f}%")
        
    except Exception as e:
        print(f"❌ Market cycle simulation error: {e}")
    
    # Test analytics
    print("\n📊 Testing Training Analytics...")
    try:
        analytics = agent_trainer.get_training_analytics()
        
        if "overview" in analytics:
            overview = analytics["overview"]
            print(f"✅ Training analytics generated")
            print(f"   Total sessions: {overview['total_training_sessions']}")
            print(f"   Average performance: {overview['average_performance']:.1f}")
            print(f"   Active agents: {overview['active_agents']}")
        else:
            print(f"✅ Analytics available: {analytics.get('message', 'Data generated')}")
            
    except Exception as e:
        print(f"❌ Analytics error: {e}")
    
    print("\n🎉 Agent Simulation System Test Complete!")
    print("=" * 60)
    print("💡 Simulation System Features:")
    print("   ✅ Realistic market condition simulation")
    print("   ✅ Deal scenario generation from real data")
    print("   ✅ Agent training with performance tracking")
    print("   ✅ Multi-scenario training sessions")
    print("   ✅ Market cycle simulation")
    print("   ✅ Comprehensive analytics")
    print("\n🚀 Next Steps:")
    print("   1. Start API: python -m app.api.main")
    print("   2. Access simulation endpoints at /api/v1/simulation/")
    print("   3. Train your agents with realistic scenarios")
    print("   4. Monitor performance and optimize strategies")

if __name__ == "__main__":
    asyncio.run(test_simulation_system())