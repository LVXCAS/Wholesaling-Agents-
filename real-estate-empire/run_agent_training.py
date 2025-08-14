#!/usr/bin/env python3
"""
Standalone agent training and deployment system
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.market_data_service import MarketDataService
from app.services.property_valuation_service import PropertyValuationService
from app.services.investment_analyzer_service import InvestmentAnalyzerService
from app.simulation.market_simulator import MarketSimulator
from app.training.curriculum_manager import CurriculumManager
from datetime import datetime
import numpy as np

class StandaloneTrainingAgent:
    """Standalone training agent for deployment"""
    
    def __init__(self, agent_id: str, agent_type: str, specialization: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.specialization = specialization
        self.training_history = []
        self.performance_metrics = {
            "total_scenarios": 0,
            "average_score": 0.0,
            "best_score": 0.0,
            "improvement_rate": 0.0,
            "specialization_score": 0.0
        }
        self.skills = {
            "deal_analysis": 0.5,
            "negotiation": 0.5,
            "portfolio_management": 0.5,
            "market_analysis": 0.5,
            "risk_assessment": 0.5
        }
        
        # Specialization bonuses
        specialization_bonuses = {
            "deal_analyzer": {"deal_analysis": 0.3, "market_analysis": 0.2},
            "negotiation_expert": {"negotiation": 0.3, "deal_analysis": 0.1},
            "portfolio_manager": {"portfolio_management": 0.3, "risk_assessment": 0.2},
            "market_analyst": {"market_analysis": 0.3, "deal_analysis": 0.1},
            "lead_specialist": {"negotiation": 0.2, "market_analysis": 0.1},
            "communication_agent": {"negotiation": 0.1, "market_analysis": 0.1}
        }
        
        if specialization in specialization_bonuses:
            for skill, bonus in specialization_bonuses[specialization].items():
                self.skills[skill] += bonus
    
    async def analyze_deal(self, scenario_data):
        """Analyze a deal scenario with specialized knowledge"""
        deal = scenario_data["deal"]
        asking_price = deal["asking_price"]
        market_value = deal["market_value"]
        market_condition = deal.get("market_condition", {})
        
        # Base confidence influenced by skills and experience
        base_confidence = 0.5 + (self.skills["deal_analysis"] * 0.3)
        base_confidence += min(0.2, len(self.training_history) * 0.005)  # Experience bonus
        
        # Market condition adjustments
        market_skill = self.skills["market_analysis"]
        if market_condition.get("trend") == "bull":
            base_confidence += market_skill * 0.1
        elif market_condition.get("trend") == "bear":
            base_confidence -= market_skill * 0.05
        
        # Specialization-specific logic
        if self.specialization == "deal_analyzer":
            # More conservative, focuses on fundamentals
            equity_threshold = 0.05  # 5% equity minimum
            price_threshold = market_value * 0.95
        elif self.specialization == "negotiation_expert":
            # More aggressive, confident in negotiation abilities
            equity_threshold = -0.02  # Willing to take slight negative equity
            price_threshold = market_value * 0.98
        elif self.specialization == "portfolio_manager":
            # Focuses on portfolio fit and diversification
            equity_threshold = 0.08  # 8% equity for portfolio stability
            price_threshold = market_value * 0.92
        else:
            # Default conservative approach
            equity_threshold = 0.05
            price_threshold = market_value * 0.95
        
        # Decision logic
        equity_potential = (market_value - asking_price) / asking_price if asking_price > 0 else 0
        
        if equity_potential >= equity_threshold and asking_price <= price_threshold:
            action = "pursue"
            # Offer price based on negotiation skill
            negotiation_skill = self.skills["negotiation"]
            discount = 0.03 + (negotiation_skill * 0.05)  # 3-8% discount based on skill
            offer_price = asking_price * (1 - discount)
        else:
            action = "pass"
            offer_price = 0
        
        decision = {
            "action": action,
            "offer_price": offer_price,
            "confidence": min(0.95, base_confidence),
            "reasoning": f"{self.specialization} analysis: {action} based on {equity_potential:.1%} equity potential",
            "specialization": self.specialization,
            "skills_applied": {
                "deal_analysis": self.skills["deal_analysis"],
                "negotiation": self.skills["negotiation"],
                "market_analysis": self.skills["market_analysis"]
            }
        }
        
        return decision
    
    def update_performance(self, score: float, scenario_type: str = "general"):
        """Update performance metrics with learning"""
        self.training_history.append(score)
        
        # Update basic metrics
        self.performance_metrics["total_scenarios"] = len(self.training_history)
        self.performance_metrics["average_score"] = np.mean(self.training_history)
        self.performance_metrics["best_score"] = max(self.training_history)
        
        # Calculate improvement rate
        if len(self.training_history) > 10:
            recent_avg = np.mean(self.training_history[-5:])
            early_avg = np.mean(self.training_history[:5])
            self.performance_metrics["improvement_rate"] = recent_avg - early_avg
        
        # Skill improvement based on performance
        improvement_factor = (score - 50) / 500  # -0.1 to +0.1 based on score
        
        # Update relevant skills
        if scenario_type == "deal_analysis" or "deal" in scenario_type:
            self.skills["deal_analysis"] = min(1.0, self.skills["deal_analysis"] + improvement_factor)
        if scenario_type == "negotiation":
            self.skills["negotiation"] = min(1.0, self.skills["negotiation"] + improvement_factor)
        if "market" in scenario_type:
            self.skills["market_analysis"] = min(1.0, self.skills["market_analysis"] + improvement_factor)
        
        # Specialization score
        specialization_skills = {
            "deal_analyzer": ["deal_analysis", "market_analysis"],
            "negotiation_expert": ["negotiation", "deal_analysis"],
            "portfolio_manager": ["portfolio_management", "risk_assessment"],
            "market_analyst": ["market_analysis", "deal_analysis"],
            "lead_specialist": ["negotiation", "market_analysis"],
            "communication_agent": ["negotiation"]
        }
        
        if self.specialization in specialization_skills:
            relevant_skills = specialization_skills[self.specialization]
            self.performance_metrics["specialization_score"] = np.mean([
                self.skills[skill] for skill in relevant_skills
            ]) * 100

async def train_agent_workforce():
    """Train a complete workforce of specialized agents"""
    
    print("🏠 Real Estate Empire - Standalone Agent Training System")
    print("=" * 65)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize services
    print("\n1. Initializing core services...")
    market_service = MarketDataService()
    valuation_service = PropertyValuationService(market_service)
    investment_service = InvestmentAnalyzerService(market_service, valuation_service)
    market_simulator = MarketSimulator(market_service)
    curriculum_manager = CurriculumManager()
    
    print("✅ Services initialized successfully")
    
    # Define agent specializations
    agent_specs = [
        ("deal_analyzer", "Deal Analysis Specialist", "intensive"),
        ("negotiation_expert", "Negotiation Expert", "intensive"),
        ("portfolio_manager", "Portfolio Manager", "medium"),
        ("market_analyst", "Market Research Analyst", "medium"),
        ("lead_specialist", "Lead Management Specialist", "light"),
        ("communication_agent", "Client Communication Agent", "light")
    ]
    
    trained_agents = []
    
    print(f"\n2. Creating and training {len(agent_specs)} specialized agents...")
    
    for i, (agent_type, description, intensity) in enumerate(agent_specs, 1):
        print(f"\n🤖 Training Agent {i}/{len(agent_specs)}: {description}")
        
        # Create agent
        agent_id = f"{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        agent = StandaloneTrainingAgent(agent_id, agent_type, agent_type)
        
        # Training parameters
        training_params = {
            "intensive": {"sessions": 8, "scenarios_per_session": 15},
            "medium": {"sessions": 5, "scenarios_per_session": 10},
            "light": {"sessions": 3, "scenarios_per_session": 8}
        }
        
        params = training_params[intensity]
        total_scenarios = params["sessions"] * params["scenarios_per_session"]
        
        print(f"   Training intensity: {intensity} ({total_scenarios} scenarios)")
        
        # Training loop
        session_scores = []
        
        for session in range(params["sessions"]):
            session_results = []
            base_difficulty = 0.2 + (session / params["sessions"]) * 0.6  # Progressive difficulty
            
            for scenario in range(params["scenarios_per_session"]):
                # Generate training scenario
                try:
                    deal = market_simulator.generate_deal_scenario()
                    
                    scenario_data = {
                        "deal": {
                            "asking_price": deal.asking_price,
                            "market_value": deal.market_value,
                            "property": deal.property_data,
                            "seller_motivation": deal.seller_motivation,
                            "competition_level": deal.competition_level,
                            "market_condition": {
                                "trend": deal.market_condition.trend,
                                "interest_rate": deal.market_condition.interest_rate
                            }
                        },
                        "difficulty": base_difficulty + (scenario / params["scenarios_per_session"]) * 0.2
                    }
                    
                    # Get agent decision
                    decision = await agent.analyze_deal(scenario_data)
                    
                    # Calculate performance score
                    score = calculate_performance_score(decision, deal, scenario_data["difficulty"])
                    
                    # Update agent
                    agent.update_performance(score, "deal_analysis")
                    session_results.append(score)
                    
                except Exception as e:
                    print(f"   ⚠️ Scenario {scenario + 1} failed: {e}")
                    continue
            
            if session_results:
                session_avg = np.mean(session_results)
                session_scores.append(session_avg)
                print(f"   Session {session + 1}: {session_avg:.1f}/100 avg")
        
        # Training summary
        if session_scores:
            final_performance = agent.performance_metrics
            improvement = session_scores[-1] - session_scores[0] if len(session_scores) > 1 else 0
            
            print(f"✅ Training completed:")
            print(f"   Final average: {final_performance['average_score']:.1f}/100")
            print(f"   Best performance: {final_performance['best_score']:.1f}/100")
            print(f"   Improvement: {improvement:+.1f} points")
            print(f"   Specialization score: {final_performance['specialization_score']:.1f}/100")
            
            trained_agents.append({
                "agent": agent,
                "description": description,
                "performance": final_performance,
                "training_intensity": intensity
            })
        else:
            print(f"❌ Training failed for {description}")
    
    # Workforce summary
    print(f"\n🎉 Agent Workforce Training Complete!")
    print("=" * 65)
    
    if trained_agents:
        print(f"📊 Workforce Summary:")
        print(f"   Total agents trained: {len(trained_agents)}")
        
        avg_performance = np.mean([agent["performance"]["average_score"] for agent in trained_agents])
        print(f"   Average performance: {avg_performance:.1f}/100")
        
        print(f"\n🎯 Agent Specializations and Performance:")
        for agent_data in trained_agents:
            agent = agent_data["agent"]
            perf = agent_data["performance"]
            print(f"   • {agent_data['description']}:")
            print(f"     Performance: {perf['average_score']:.1f}/100")
            print(f"     Specialization: {perf['specialization_score']:.1f}/100")
            print(f"     Total scenarios: {perf['total_scenarios']}")
            print(f"     Improvement: {perf['improvement_rate']:+.1f} points")
        
        # Demonstrate capabilities
        print(f"\n🎭 Demonstrating Agent Capabilities:")
        
        # Generate test scenario
        test_deal = market_simulator.generate_deal_scenario("Miami", "Florida")
        
        print(f"\n📋 Test Scenario:")
        print(f"   Location: {test_deal.property_data['city']}, {test_deal.property_data['state']}")
        print(f"   Property: {test_deal.property_data['bedrooms']}bed/{test_deal.property_data['bathrooms']}bath")
        print(f"   Size: {test_deal.property_data['house_size']:,.0f} sq ft")
        print(f"   Asking Price: ${test_deal.asking_price:,.0f}")
        print(f"   Market Value: ${test_deal.market_value:,.0f}")
        print(f"   Equity Potential: ${test_deal.market_value - test_deal.asking_price:,.0f}")
        
        scenario_data = {
            "deal": {
                "asking_price": test_deal.asking_price,
                "market_value": test_deal.market_value,
                "property": test_deal.property_data,
                "market_condition": {
                    "trend": test_deal.market_condition.trend,
                    "interest_rate": test_deal.market_condition.interest_rate
                }
            }
        }
        
        print(f"\n🤖 Agent Decisions:")
        for agent_data in trained_agents:
            agent = agent_data["agent"]
            decision = await agent.analyze_deal(scenario_data)
            
            print(f"   • {agent_data['description']}:")
            print(f"     Decision: {decision['action'].upper()}")
            if decision['action'] == 'pursue':
                print(f"     Offer: ${decision['offer_price']:,.0f}")
            print(f"     Confidence: {decision['confidence']:.2f}")
            print(f"     Reasoning: {decision['reasoning']}")
        
        # Investment analysis comparison
        print(f"\n💰 AI Investment Analysis (for comparison):")
        try:
            property_data = test_deal.property_data.copy()
            property_data['asking_price'] = test_deal.asking_price
            property_data['estimated_rent'] = test_deal.asking_price * 0.01
            
            analysis = investment_service.analyze_investment_opportunity(property_data)
            print(f"   Recommendation: {analysis.recommendation}")
            print(f"   Investment Score: {analysis.investment_metrics.investment_score:.1f}/100")
            print(f"   Risk Level: {analysis.investment_metrics.risk_level}")
            
        except Exception as e:
            print(f"   Analysis unavailable: {e}")
        
        # Task assignments
        print(f"\n💼 Recommended Task Assignments:")
        
        task_assignments = {
            "deal_analyzer": [
                "Property valuation and analysis",
                "Investment opportunity assessment",
                "Market comparables analysis",
                "Due diligence coordination"
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
        
        for agent_data in trained_agents:
            agent = agent_data["agent"]
            specialization = agent.specialization
            
            if specialization in task_assignments:
                print(f"\n   🤖 {agent_data['description']} ({agent_data['performance']['average_score']:.1f}/100):")
                for task in task_assignments[specialization]:
                    print(f"     • {task}")
        
        print(f"\n🚀 Next Steps:")
        print(f"   1. Agents are trained and ready for deployment")
        print(f"   2. Integrate agents with existing workflows")
        print(f"   3. Monitor performance in production")
        print(f"   4. Continue training based on real-world feedback")
        print(f"   5. Scale successful agents for high-volume tasks")
        
        return trained_agents
    
    else:
        print("❌ No agents were successfully trained")
        return []

def calculate_performance_score(decision, deal, difficulty):
    """Calculate performance score for a decision"""
    score = 50.0  # Base score
    
    asking_price = deal.asking_price
    market_value = deal.market_value
    equity_potential = market_value - asking_price
    
    action = decision.get("action", "pass")
    offer_price = decision.get("offer_price", 0)
    confidence = decision.get("confidence", 0.5)
    
    # Decision accuracy
    if equity_potential > 0:  # Good deal
        if action == "pursue":
            score += 30  # Correct identification
        else:
            score -= 20  # Missed opportunity
    else:  # Poor deal
        if action == "pass":
            score += 25  # Correct avoidance
        else:
            score -= 35  # Bad decision
    
    # Offer price accuracy (if pursuing)
    if action == "pursue" and offer_price > 0 and market_value > 0:
        optimal_offer = market_value * 0.95
        price_accuracy = 1 - abs(offer_price - optimal_offer) / optimal_offer
        score += price_accuracy * 15
    
    # Confidence calibration
    expected_confidence = 0.8 if equity_potential > asking_price * 0.05 else 0.4
    confidence_accuracy = 1 - abs(confidence - expected_confidence)
    score += confidence_accuracy * 10
    
    # Difficulty bonus
    score += difficulty * 5
    
    return max(0, min(100, score))

async def main():
    """Main function"""
    try:
        trained_agents = await train_agent_workforce()
        
        print(f"\n🎉 Training System Complete!")
        print(f"🕐 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if trained_agents:
            print(f"\n✅ Successfully trained {len(trained_agents)} specialized agents")
            print(f"💡 Agents are ready for production deployment")
        
        return trained_agents
        
    except Exception as e:
        print(f"❌ Training system error: {e}")
        return []

if __name__ == "__main__":
    asyncio.run(main())