#!/usr/bin/env python3
"""
Demo script for the AI-Powered Real Estate Empire Agentic Hive System
Shows the LangGraph workflow in action with mock data
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.langgraph_setup import LangGraphOrchestrator
from app.core.agent_state import StateManager, AgentType, WorkflowStatus
from app.core.agent_communication import AgentCommunicationProtocol
from app.core.llm_config import llm_manager


class RealEstateEmpireDemo:
    """Demo class for the agentic hive system"""
    
    def __init__(self):
        self.orchestrator = LangGraphOrchestrator()
        self.communication = AgentCommunicationProtocol()
        
    async def initialize(self):
        """Initialize the demo system"""
        print("🏠 Initializing AI-Powered Real Estate Empire...")
        print("🧠 Setting up LangGraph Agentic Hive System...")
        
        # Initialize communication protocol
        await self.communication.initialize()
        
        # Register agents
        agents = [
            ("supervisor", {"type": "orchestrator", "capabilities": ["decision_making", "coordination"]}),
            ("scout", {"type": "discovery", "capabilities": ["deal_sourcing", "lead_generation"]}),
            ("analyst", {"type": "analysis", "capabilities": ["financial_modeling", "property_valuation"]}),
            ("negotiator", {"type": "communication", "capabilities": ["seller_outreach", "negotiation"]}),
            ("contract", {"type": "legal", "capabilities": ["contract_generation", "transaction_management"]}),
            ("portfolio", {"type": "management", "capabilities": ["portfolio_optimization", "performance_tracking"]})
        ]
        
        for agent_name, agent_info in agents:
            self.communication.register_agent(agent_name, agent_info)
        
        print(f"✅ Registered {len(agents)} specialized agents")
        print("🚀 System ready for autonomous operation!")
        print()
    
    def create_demo_state(self) -> Dict[str, Any]:
        """Create initial state with demo data"""
        state = StateManager.create_initial_state()
        
        # Set demo configuration
        state.update({
            "current_geographic_focus": "Austin, TX",
            "available_capital": 500000.0,
            "investment_strategy": {
                "primary_strategy": "fix_and_flip",
                "target_roi": 0.20,
                "max_deal_size": 400000,
                "preferred_property_types": ["single_family", "townhouse"]
            },
            "market_conditions": {
                "market_temperature": "warm",
                "median_home_price": 450000,
                "days_on_market": 25,
                "investor_activity": "high"
            },
            "automation_level": "supervised"
        })
        
        return state
    
    async def run_demo_workflow(self):
        """Run a complete demo workflow"""
        print("🎯 Starting Autonomous Real Estate Investment Workflow")
        print("=" * 60)
        
        # Create initial state
        initial_state = self.create_demo_state()
        
        print(f"📍 Geographic Focus: {initial_state['current_geographic_focus']}")
        print(f"💰 Available Capital: ${initial_state['available_capital']:,.2f}")
        print(f"🎯 Investment Strategy: {initial_state['investment_strategy']['primary_strategy']}")
        print(f"🌡️  Market Temperature: {initial_state['market_conditions']['market_temperature']}")
        print()
        
        try:
            # Start the workflow (this would normally run with real LLMs)
            print("🤖 Activating AI Agent Hive...")
            
            # Simulate workflow steps
            await self.simulate_supervisor_decision(initial_state)
            await self.simulate_scout_agent(initial_state)
            await self.simulate_analyst_agent(initial_state)
            await self.simulate_negotiator_agent(initial_state)
            
            print("\n✅ Demo workflow completed successfully!")
            print("🏆 The AI Real Estate Empire is ready for autonomous operation!")
            
        except Exception as e:
            print(f"❌ Demo workflow error: {e}")
    
    async def simulate_supervisor_decision(self, state: Dict[str, Any]):
        """Simulate supervisor agent decision making"""
        print("🧠 SUPERVISOR AGENT: Analyzing system state...")
        
        # Simulate decision making
        await asyncio.sleep(1)
        
        decision = {
            "action": "scout",
            "reasoning": "Portfolio needs new deals. Market conditions are favorable for acquisition.",
            "priority": "high"
        }
        
        print(f"   📊 System Analysis: {len(state.get('current_deals', []))} deals in pipeline")
        print(f"   🎯 Strategic Decision: {decision['action'].upper()}")
        print(f"   💭 Reasoning: {decision['reasoning']}")
        print(f"   ⚡ Priority: {decision['priority']}")
        
        # Send coordination message
        await self.communication.send_task_request(
            sender="supervisor",
            recipient="scout",
            task="find_investment_opportunities",
            data={"location": state["current_geographic_focus"], "budget": state["available_capital"]}
        )
        
        print("   ✅ Task assigned to Scout Agent")
        print()
    
    async def simulate_scout_agent(self, state: Dict[str, Any]):
        """Simulate scout agent deal discovery"""
        print("🔍 SCOUT AGENT: Discovering investment opportunities...")
        
        # Simulate data source scanning
        data_sources = ["MLS", "Zillow", "Public Records", "Foreclosure.com", "Off-Market Networks"]
        
        for source in data_sources:
            print(f"   📡 Scanning {source}...")
            await asyncio.sleep(0.5)
        
        # Simulate deal discovery
        discovered_deals = [
            {
                "address": "1234 Oak Street",
                "city": "Austin",
                "state": "TX",
                "listing_price": 285000,
                "estimated_arv": 380000,
                "lead_score": 8.5,
                "motivation": ["job_relocation", "quick_sale_needed"]
            },
            {
                "address": "5678 Pine Avenue", 
                "city": "Austin",
                "state": "TX",
                "listing_price": 320000,
                "estimated_arv": 420000,
                "lead_score": 7.8,
                "motivation": ["divorce", "financial_distress"]
            },
            {
                "address": "9012 Maple Drive",
                "city": "Austin", 
                "state": "TX",
                "listing_price": 195000,
                "estimated_arv": 285000,
                "lead_score": 9.2,
                "motivation": ["foreclosure", "estate_sale"]
            }
        ]
        
        print(f"   🎯 Found {len(discovered_deals)} high-potential opportunities")
        
        for i, deal in enumerate(discovered_deals, 1):
            print(f"   📍 Deal {i}: {deal['address']}")
            print(f"      💰 Listed: ${deal['listing_price']:,} | ARV: ${deal['estimated_arv']:,}")
            print(f"      ⭐ Score: {deal['lead_score']}/10 | Motivation: {', '.join(deal['motivation'])}")
        
        # Send results to analyst
        await self.communication.send_task_response(
            sender="scout",
            recipient="supervisor", 
            correlation_id="demo-correlation-1",
            result={"deals_found": discovered_deals, "total_count": len(discovered_deals)}
        )
        
        print("   ✅ Deals forwarded to Analyst Agent for evaluation")
        print()
    
    async def simulate_analyst_agent(self, state: Dict[str, Any]):
        """Simulate analyst agent property analysis"""
        print("📊 ANALYST AGENT: Performing comprehensive property analysis...")
        
        # Simulate analysis for top deal
        deal = {
            "address": "9012 Maple Drive",
            "listing_price": 195000,
            "estimated_arv": 285000
        }
        
        print(f"   🏠 Analyzing: {deal['address']}")
        print("   🔍 Running comparable property analysis...")
        await asyncio.sleep(1)
        
        print("   🔨 Estimating repair costs using AI vision...")
        await asyncio.sleep(1)
        
        print("   💹 Calculating financial projections...")
        await asyncio.sleep(1)
        
        # Analysis results
        analysis = {
            "arv_estimate": 285000,
            "repair_estimate": 35000,
            "purchase_price": 195000,
            "potential_profit": 55000,
            "roi": 28.2,
            "confidence_score": 8.7,
            "recommendation": "PROCEED",
            "risk_factors": ["market_volatility", "repair_overruns"],
            "timeline": "4-6 months"
        }
        
        print("   📈 FINANCIAL ANALYSIS COMPLETE:")
        print(f"      🏠 ARV Estimate: ${analysis['arv_estimate']:,}")
        print(f"      🔨 Repair Estimate: ${analysis['repair_estimate']:,}")
        print(f"      💰 Potential Profit: ${analysis['potential_profit']:,}")
        print(f"      📊 ROI: {analysis['roi']:.1f}%")
        print(f"      🎯 Confidence: {analysis['confidence_score']}/10")
        print(f"      ✅ Recommendation: {analysis['recommendation']}")
        
        # Send to negotiator
        await self.communication.send_task_request(
            sender="analyst",
            recipient="negotiator",
            task="initiate_seller_outreach",
            data={"deal": deal, "analysis": analysis, "max_offer": 180000}
        )
        
        print("   ✅ Deal approved - forwarded to Negotiator Agent")
        print()
    
    async def simulate_negotiator_agent(self, state: Dict[str, Any]):
        """Simulate negotiator agent seller outreach"""
        print("🤝 NEGOTIATOR AGENT: Initiating seller outreach campaign...")
        
        deal_address = "9012 Maple Drive"
        
        # Simulate multi-channel outreach
        channels = [
            {"type": "email", "status": "sent", "open_rate": "45%"},
            {"type": "sms", "status": "delivered", "response_rate": "12%"}, 
            {"type": "voice", "status": "voicemail", "callback_rate": "8%"}
        ]
        
        print(f"   📧 Launching personalized outreach for {deal_address}")
        
        for channel in channels:
            print(f"   📱 {channel['type'].upper()}: {channel['status']} - {list(channel.values())[2]}")
            await asyncio.sleep(0.5)
        
        # Simulate seller response
        await asyncio.sleep(2)
        
        print("\n   📞 SELLER RESPONSE RECEIVED:")
        print("   💬 'Hi, I got your message about my property. I am interested in selling quickly.'")
        print("   🧠 AI Sentiment Analysis: POSITIVE (0.78)")
        print("   🎯 Interest Level: HIGH (0.85)")
        print("   💡 Motivation Detected: Quick sale needed, financial pressure")
        
        # Simulate negotiation
        print("\n   🤝 INITIATING NEGOTIATION:")
        print("   💰 Initial Offer: $175,000 (10% below asking)")
        print("   📋 Terms: Cash offer, 14-day close, as-is condition")
        print("   ⚡ Seller Counter: $185,000")
        print("   🎯 Final Agreement: $180,000")
        
        # Send to contract agent
        await self.communication.send_task_request(
            sender="negotiator",
            recipient="contract",
            task="generate_purchase_contract",
            data={
                "agreed_price": 180000,
                "property": deal_address,
                "terms": {"cash_offer": True, "closing_days": 14, "condition": "as_is"}
            }
        )
        
        print("   ✅ Deal negotiated successfully - forwarded to Contract Agent")
        print()
    
    async def show_system_stats(self):
        """Show system performance statistics"""
        print("📊 SYSTEM PERFORMANCE DASHBOARD")
        print("=" * 40)
        
        stats = {
            "Active Agents": len(self.communication.list_active_agents()),
            "Deals Discovered": 3,
            "Deals Analyzed": 1, 
            "Deals Under Contract": 1,
            "Total Pipeline Value": "$800,000",
            "Estimated Profit": "$55,000",
            "Average ROI": "28.2%",
            "System Uptime": "100%"
        }
        
        for metric, value in stats.items():
            print(f"   {metric}: {value}")
        
        print("\n🏆 AI Real Estate Empire Status: OPERATIONAL")
        print("🤖 Autonomous agents working 24/7 to build your real estate portfolio!")


async def main():
    """Main demo function"""
    print("🏠 AI-POWERED REAL ESTATE EMPIRE")
    print("🤖 Autonomous Agentic Hive System Demo")
    print("=" * 50)
    print()
    
    # Check for API keys (in demo mode, we'll simulate)
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  DEMO MODE: Running with simulated LLM responses")
        print("   Set OPENAI_API_KEY environment variable for live LLM integration")
        print()
    
    # Initialize and run demo
    demo = RealEstateEmpireDemo()
    
    try:
        await demo.initialize()
        await demo.run_demo_workflow()
        await demo.show_system_stats()
        
        print("\n" + "=" * 50)
        print("🎉 Demo completed successfully!")
        print("🚀 Ready to deploy your AI Real Estate Empire!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())