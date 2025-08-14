#!/usr/bin/env python3
"""
Deploy trained agents to complete remaining Real Estate Empire tasks
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import time

API_BASE = "http://localhost:8000/api/v1"

async def create_and_train_agent(session, agent_type: str, training_intensity: str = "medium"):
    """Create and train a specialized agent"""
    
    print(f"🤖 Creating {agent_type} agent...")
    
    # Create agent
    async with session.post(f"{API_BASE}/training/create-agent", 
                           params={"agent_type": agent_type}) as response:
        if response.status == 200:
            agent_data = await response.json()
            agent_id = agent_data["agent_id"]
            print(f"✅ Created agent: {agent_id}")
        else:
            print(f"❌ Failed to create {agent_type} agent")
            return None
    
    # Determine training parameters based on intensity
    training_params = {
        "light": {"num_sessions": 3, "scenarios_per_session": 5},
        "medium": {"num_sessions": 5, "scenarios_per_session": 10},
        "intensive": {"num_sessions": 8, "scenarios_per_session": 15}
    }
    
    params = training_params.get(training_intensity, training_params["medium"])
    
    print(f"🏋️ Training {agent_type} agent with {params['num_sessions']} sessions...")
    
    # Run batch training
    async with session.post(f"{API_BASE}/training/batch-training/{agent_id}", 
                           params=params) as response:
        if response.status == 200:
            training_result = await response.json()
            summary = training_result["overall_summary"]
            
            print(f"✅ Training completed for {agent_type} agent:")
            print(f"   Total scenarios: {summary['total_scenarios']}")
            print(f"   Average performance: {summary['overall_average']:.1f}/100")
            print(f"   Best session: {summary['best_session']:.1f}/100")
            print(f"   Improvement: {summary['improvement']:+.1f} points")
            
            return {
                "agent_id": agent_id,
                "agent_type": agent_type,
                "performance": summary,
                "status": "trained"
            }
        else:
            print(f"❌ Training failed for {agent_type} agent")
            return None

async def deploy_agent_workforce():
    """Deploy a complete workforce of trained agents"""
    
    print("🚀 Deploying Real Estate Empire AI Workforce")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        # Test API connectivity
        try:
            async with session.get(f"{API_BASE}/health") as response:
                if response.status == 200:
                    print("✅ API server is running")
                else:
                    print("❌ API server not responding")
                    return
        except Exception as e:
            print(f"❌ Cannot connect to API server: {e}")
            print("💡 Make sure to run: python -m app.api.main")
            return
        
        # Define agent specializations
        agent_specializations = [
            ("deal_analyzer", "intensive"),     # Core deal analysis
            ("negotiation_expert", "intensive"), # Negotiation specialist
            ("portfolio_manager", "medium"),    # Portfolio optimization
            ("market_analyst", "medium"),       # Market research
            ("lead_specialist", "light"),       # Lead management
            ("communication_agent", "light"),   # Client communication
        ]
        
        trained_agents = []
        
        # Create and train specialized agents
        for agent_type, intensity in agent_specializations:
            agent = await create_and_train_agent(session, agent_type, intensity)
            if agent:
                trained_agents.append(agent)
            
            # Brief pause between training sessions
            await asyncio.sleep(1)
        
        print(f"\n🎉 Agent Workforce Deployment Complete!")
        print("=" * 60)
        
        # Display workforce summary
        print(f"📊 Workforce Summary:")
        print(f"   Total agents deployed: {len(trained_agents)}")
        
        if trained_agents:
            avg_performance = sum(agent["performance"]["overall_average"] 
                                for agent in trained_agents) / len(trained_agents)
            print(f"   Average performance: {avg_performance:.1f}/100")
            
            # Performance by specialization
            print(f"\n🎯 Agent Specializations:")
            for agent in trained_agents:
                perf = agent["performance"]["overall_average"]
                improvement = agent["performance"]["improvement"]
                print(f"   • {agent['agent_type']}: {perf:.1f}/100 ({improvement:+.1f} improvement)")
        
        # Get training analytics
        try:
            async with session.get(f"{API_BASE}/training/training-analytics") as response:
                if response.status == 200:
                    analytics = await response.json()
                    
                    print(f"\n📈 Training Analytics:")
                    print(f"   Total trained agents: {analytics['agents_with_training']}")
                    
                    if 'overall_performance' in analytics:
                        perf = analytics['overall_performance']
                        print(f"   Overall average: {perf['average_score']:.1f}/100")
                        print(f"   Best performer: {perf['best_score']:.1f}/100")
                        
                        dist = perf['score_distribution']
                        print(f"   Performance distribution:")
                        print(f"     Excellent (80+): {dist['excellent']} agents")
                        print(f"     Good (60-79): {dist['good']} agents")
                        print(f"     Needs improvement (<60): {dist['needs_improvement']} agents")
        
        except Exception as e:
            print(f"⚠️ Could not retrieve analytics: {e}")
        
        # Task assignment recommendations
        print(f"\n💼 Recommended Task Assignments:")
        
        task_assignments = {
            "deal_analyzer": [
                "Property valuation and analysis",
                "Investment opportunity assessment", 
                "Market comparables analysis",
                "Deal structuring recommendations"
            ],
            "negotiation_expert": [
                "Contract negotiations",
                "Offer and counter-offer strategies",
                "Closing process management",
                "Dispute resolution"
            ],
            "portfolio_manager": [
                "Portfolio optimization",
                "Risk management",
                "Asset allocation strategies",
                "Performance monitoring"
            ],
            "market_analyst": [
                "Market trend analysis",
                "Neighborhood research",
                "Economic impact assessment",
                "Investment timing recommendations"
            ],
            "lead_specialist": [
                "Lead qualification and scoring",
                "Follow-up management",
                "Conversion optimization",
                "Client relationship management"
            ],
            "communication_agent": [
                "Client communications",
                "Marketing content creation",
                "Appointment scheduling",
                "Customer service"
            ]
        }
        
        for agent in trained_agents:
            agent_type = agent["agent_type"]
            if agent_type in task_assignments:
                print(f"\n   🤖 {agent_type} ({agent['performance']['overall_average']:.1f}/100):")
                for task in task_assignments[agent_type]:
                    print(f"     • {task}")
        
        print(f"\n🚀 Next Steps:")
        print(f"   1. Agents are trained and ready for deployment")
        print(f"   2. Integrate agents with existing workflows")
        print(f"   3. Monitor performance in production")
        print(f"   4. Continue training based on real-world feedback")
        print(f"   5. Scale successful agents for high-volume tasks")
        
        print(f"\n💡 API Endpoints Available:")
        print(f"   • Agent Performance: GET {API_BASE}/training/agent-performance/{{agent_id}}")
        print(f"   • Training Analytics: GET {API_BASE}/training/training-analytics")
        print(f"   • Market Analysis: GET {API_BASE}/market-data/stats/{{city}}/{{state}}")
        print(f"   • Investment Analysis: POST {API_BASE}/investment-analysis/analyze-deal")
        print(f"   • Simulation: POST {API_BASE}/simulation/generate-deal")
        
        return trained_agents

async def demonstrate_agent_capabilities(trained_agents):
    """Demonstrate the capabilities of trained agents"""
    
    if not trained_agents:
        print("No trained agents available for demonstration")
        return
    
    print(f"\n🎭 Demonstrating Agent Capabilities")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # Generate a test deal
        async with session.post(f"{API_BASE}/simulation/generate-deal", 
                               params={"city": "Miami", "state": "Florida"}) as response:
            if response.status == 200:
                deal_data = await response.json()
                print(f"📋 Test Deal Generated:")
                print(f"   Location: {deal_data['property']['city']}, {deal_data['property']['state']}")
                print(f"   Asking Price: ${deal_data['asking_price']:,.0f}")
                print(f"   Market Value: ${deal_data['market_value']:,.0f}")
                print(f"   Equity Potential: ${deal_data['market_value'] - deal_data['asking_price']:,.0f}")
                
                # Test investment analysis
                property_data = {
                    "city": deal_data['property']['city'],
                    "state": deal_data['property']['state'],
                    "bedrooms": deal_data['property']['bedrooms'],
                    "bathrooms": deal_data['property']['bathrooms'],
                    "house_size": deal_data['property']['house_size'],
                    "asking_price": deal_data['asking_price'],
                    "estimated_rent": deal_data['asking_price'] * 0.01
                }
                
                async with session.post(f"{API_BASE}/investment-analysis/analyze-deal", 
                                       json=property_data) as response:
                    if response.status == 200:
                        analysis = await response.json()
                        print(f"\n💰 AI Investment Analysis:")
                        print(f"   Recommendation: {analysis['recommendation']}")
                        print(f"   Investment Score: {analysis['investment_metrics']['investment_score']:.1f}/100")
                        print(f"   Risk Level: {analysis['investment_metrics']['risk_level']}")
                        if analysis['investment_metrics']['cap_rate']:
                            print(f"   Cap Rate: {analysis['investment_metrics']['cap_rate']:.2f}%")
                        if analysis['investment_metrics']['monthly_cash_flow']:
                            print(f"   Monthly Cash Flow: ${analysis['investment_metrics']['monthly_cash_flow']:,.2f}")
        
        # Test market analysis
        async with session.get(f"{API_BASE}/market-data/stats/Miami/Florida") as response:
            if response.status == 200:
                market_stats = await response.json()
                print(f"\n📊 Market Intelligence:")
                print(f"   Average Price: ${market_stats['avg_price']:,.0f}")
                print(f"   Price per Sq Ft: ${market_stats['avg_price_per_sqft']:.2f}")
                print(f"   Total Listings: {market_stats['total_listings']:,}")
        
        print(f"\n✅ Agent capabilities successfully demonstrated!")

async def main():
    """Main deployment function"""
    
    print("🏠 Real Estate Empire - AI Agent Deployment System")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Deploy workforce
    trained_agents = await deploy_agent_workforce()
    
    # Demonstrate capabilities
    if trained_agents:
        await demonstrate_agent_capabilities(trained_agents)
    
    print(f"\n🎉 Deployment Complete!")
    print(f"🕐 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return trained_agents

if __name__ == "__main__":
    asyncio.run(main())