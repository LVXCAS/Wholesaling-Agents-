import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import numpy as np
from .market_simulator import MarketSimulator, SimulatedDeal
from ..services.investment_analyzer_service import InvestmentAnalyzerService
from ..services.gemini_service import GeminiService

@dataclass
class AgentPerformance:
    """Track agent performance metrics"""
    agent_id: str
    agent_type: str
    decisions_made: int
    successful_decisions: int
    total_profit: float
    average_roi: float
    risk_score: float
    learning_rate: float
    confidence_score: float

@dataclass
class TrainingScenario:
    """A training scenario for agents"""
    scenario_id: str
    scenario_type: str  # "deal_analysis", "negotiation", "portfolio_management"
    deal: SimulatedDeal
    expected_outcome: Dict[str, Any]
    difficulty_level: float  # 0.0 to 1.0
    learning_objectives: List[str]

@dataclass
class TrainingResult:
    """Result of a training scenario"""
    scenario_id: str
    agent_id: str
    decision: Dict[str, Any]
    actual_outcome: Dict[str, Any]
    performance_score: float
    learning_points: List[str]
    timestamp: datetime

class AgentTrainer:
    """Train and evaluate real estate AI agents using simulations"""
    
    def __init__(self, market_simulator: MarketSimulator, investment_analyzer: InvestmentAnalyzerService):
        self.market_simulator = market_simulator
        self.investment_analyzer = investment_analyzer
        try:
            self.gemini_service = GeminiService()
            print("✅ Gemini service integrated into agent trainer")
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize Gemini service in agent trainer: {e}")
            self.gemini_service = None
        
        self.agent_performances: Dict[str, AgentPerformance] = {}
        self.training_history: List[TrainingResult] = []
        
    def create_training_scenario(self, scenario_type: str, difficulty: float = 0.5) -> TrainingScenario:
        """Create a training scenario for agents"""
        
        # Generate a deal based on scenario type
        if scenario_type == "deal_analysis":
            deal = self.market_simulator.generate_deal_scenario()
            expected_outcome = self._calculate_expected_deal_outcome(deal)
            learning_objectives = [
                "Accurate property valuation",
                "Risk assessment",
                "Market timing analysis",
                "Investment potential evaluation"
            ]
            
        elif scenario_type == "negotiation":
            deal = self.market_simulator.generate_deal_scenario()
            # Make it a negotiation scenario by adjusting seller motivation
            deal.seller_motivation = np.random.uniform(0.3, 0.9)
            expected_outcome = self._calculate_negotiation_outcome(deal)
            learning_objectives = [
                "Negotiation strategy selection",
                "Counter-offer analysis",
                "Closing techniques",
                "Relationship management"
            ]
            
        elif scenario_type == "portfolio_management":
            deal = self.market_simulator.generate_deal_scenario()
            expected_outcome = self._calculate_portfolio_impact(deal)
            learning_objectives = [
                "Portfolio diversification",
                "Risk management",
                "Cash flow optimization",
                "Long-term strategy alignment"
            ]
        else:
            raise ValueError(f"Unknown scenario type: {scenario_type}")
        
        scenario = TrainingScenario(
            scenario_id=f"TRAIN_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{np.random.randint(1000, 9999)}",
            scenario_type=scenario_type,
            deal=deal,
            expected_outcome=expected_outcome,
            difficulty_level=difficulty,
            learning_objectives=learning_objectives
        )
        
        return scenario
    
    def _calculate_expected_deal_outcome(self, deal: SimulatedDeal) -> Dict[str, Any]:
        """Calculate expected outcome for a deal analysis scenario"""
        
        # Use our investment analyzer to get the "correct" analysis
        property_data = deal.property_data.copy()
        property_data['asking_price'] = deal.asking_price
        
        analysis = self.investment_analyzer.analyze_investment_opportunity(property_data)
        
        return {
            "should_pursue": analysis.investment_metrics.investment_score > 60,
            "estimated_value": analysis.estimated_value,
            "max_offer": deal.market_value * 0.95,  # 5% below market value
            "expected_roi": analysis.investment_metrics.roi,
            "risk_level": analysis.investment_metrics.risk_level,
            "confidence": analysis.confidence_score
        }
    
    def _calculate_negotiation_outcome(self, deal: SimulatedDeal) -> Dict[str, Any]:
        """Calculate expected outcome for negotiation scenario"""
        
        # Negotiation success depends on seller motivation and market conditions
        base_discount = 0.05  # 5% base discount
        
        # Higher seller motivation = more discount possible
        motivation_discount = deal.seller_motivation * 0.1
        
        # Market conditions affect negotiation power
        market_discount = 0.0
        if deal.market_condition.trend == "bear":
            market_discount = 0.05
        elif deal.market_condition.inventory_level == "high":
            market_discount = 0.03
        
        total_discount = base_discount + motivation_discount + market_discount
        final_price = deal.asking_price * (1 - total_discount)
        
        return {
            "negotiation_success": True,
            "final_price": final_price,
            "discount_achieved": total_discount,
            "negotiation_rounds": np.random.randint(2, 6),
            "seller_satisfaction": max(0.3, deal.seller_motivation),
            "time_to_close": np.random.randint(30, 60)
        }
    
    def _calculate_portfolio_impact(self, deal: SimulatedDeal) -> Dict[str, Any]:
        """Calculate expected portfolio impact"""
        
        # Simplified portfolio analysis
        property_data = deal.property_data.copy()
        property_data['asking_price'] = deal.asking_price
        
        analysis = self.investment_analyzer.analyze_investment_opportunity(property_data)
        
        return {
            "portfolio_fit": analysis.investment_metrics.investment_score > 70,
            "diversification_benefit": np.random.uniform(0.1, 0.8),
            "cash_flow_impact": analysis.investment_metrics.monthly_cash_flow,
            "risk_contribution": analysis.investment_metrics.risk_level,
            "strategic_alignment": np.random.uniform(0.5, 1.0)
        }
    
    async def train_agent(self, agent, scenario: TrainingScenario) -> TrainingResult:
        """Train an agent on a specific scenario"""
        
        # Present scenario to agent
        scenario_data = {
            "deal": {
                "property": scenario.deal.property_data,
                "asking_price": scenario.deal.asking_price,
                "days_on_market": scenario.deal.days_on_market,
                "seller_motivation": scenario.deal.seller_motivation,
                "competition_level": scenario.deal.competition_level,
                "market_condition": asdict(scenario.deal.market_condition)
            },
            "scenario_type": scenario.scenario_type,
            "learning_objectives": scenario.learning_objectives
        }
        
        # Get agent's decision
        if hasattr(agent, 'analyze_deal'):
            decision = await agent.analyze_deal(scenario_data)
        elif hasattr(agent, 'make_decision'):
            decision = await agent.make_decision(scenario_data)
        else:
            # Fallback for agents without specific methods
            decision = {"action": "analyze", "confidence": 0.5}
        
        # Evaluate performance
        performance_score = self._evaluate_agent_decision(
            decision, scenario.expected_outcome, scenario.difficulty_level
        )
        
        # Generate learning points
        learning_points = self._generate_learning_points(
            decision, scenario.expected_outcome, performance_score
        )
        
        # Create training result
        result = TrainingResult(
            scenario_id=scenario.scenario_id,
            agent_id=getattr(agent, 'agent_id', 'unknown'),
            decision=decision,
            actual_outcome=scenario.expected_outcome,
            performance_score=performance_score,
            learning_points=learning_points,
            timestamp=datetime.now()
        )
        
        # Update agent performance tracking
        self._update_agent_performance(result)
        
        # Store training history
        self.training_history.append(result)
        
        return result
    
    def _evaluate_agent_decision(self, decision: Dict[str, Any], expected: Dict[str, Any], difficulty: float) -> float:
        """Evaluate how well the agent performed"""
        
        score = 0.0
        max_score = 100.0
        
        # Check key decision alignment
        if "should_pursue" in expected and "action" in decision:
            expected_action = "pursue" if expected["should_pursue"] else "pass"
            actual_action = decision.get("action", "unknown")
            
            if (expected_action == "pursue" and actual_action in ["buy", "pursue", "negotiate"]) or \
               (expected_action == "pass" and actual_action in ["pass", "reject"]):
                score += 40.0
        
        # Check price accuracy
        if "max_offer" in expected and "offer_price" in decision:
            expected_price = expected["max_offer"]
            actual_price = decision["offer_price"]
            price_diff = abs(expected_price - actual_price) / expected_price
            price_score = max(0, 30.0 * (1 - price_diff))
            score += price_score
        
        # Check confidence calibration
        if "confidence" in expected and "confidence" in decision:
            expected_conf = expected["confidence"] / 100.0
            actual_conf = decision["confidence"]
            conf_diff = abs(expected_conf - actual_conf)
            conf_score = max(0, 20.0 * (1 - conf_diff))
            score += conf_score
        
        # Adjust for difficulty
        adjusted_score = score * (1 + difficulty * 0.2)  # Bonus for harder scenarios
        
        return min(100.0, adjusted_score)
    
    def _generate_learning_points(self, decision: Dict[str, Any], expected: Dict[str, Any], score: float) -> List[str]:
        """Generate learning points for the agent"""
        
        points = []
        
        if score < 50:
            points.append("Decision accuracy needs improvement")
            
        if "offer_price" in decision and "max_offer" in expected:
            if decision["offer_price"] > expected["max_offer"] * 1.1:
                points.append("Offer price too high - consider market value more carefully")
            elif decision["offer_price"] < expected["max_offer"] * 0.9:
                points.append("Offer price too low - may miss good opportunities")
        
        if score > 80:
            points.append("Excellent decision-making - maintain this approach")
        elif score > 60:
            points.append("Good decision with room for refinement")
        
        return points
    
    async def get_ai_training_enhancement(self, training_result: TrainingResult) -> Dict[str, Any]:
        """Get AI-powered training enhancement suggestions"""
        if not self.gemini_service:
            return {"error": "Gemini service not available"}
        
        try:
            training_data = {
                "scenario_type": "training_analysis",
                "performance_metrics": {
                    "score": training_result.performance_score,
                    "agent_id": training_result.agent_id
                },
                "conversation_log": [
                    f"Decision: {training_result.decision}",
                    f"Expected: {training_result.actual_outcome}",
                    f"Learning Points: {training_result.learning_points}"
                ],
                "outcome": "success" if training_result.performance_score > 70 else "needs_improvement"
            }
            
            enhancement = await self.gemini_service.enhance_agent_training(training_data)
            return {
                "ai_suggestions": enhancement.content,
                "confidence": enhancement.confidence,
                "training_data": training_data
            }
        except Exception as e:
            return {"error": f"AI enhancement failed: {e}"}
    
    def _update_agent_performance(self, result: TrainingResult):
        """Update agent performance metrics"""
        
        agent_id = result.agent_id
        
        if agent_id not in self.agent_performances:
            self.agent_performances[agent_id] = AgentPerformance(
                agent_id=agent_id,
                agent_type="unknown",
                decisions_made=0,
                successful_decisions=0,
                total_profit=0.0,
                average_roi=0.0,
                risk_score=0.5,
                learning_rate=0.1,
                confidence_score=0.5
            )
        
        perf = self.agent_performances[agent_id]
        perf.decisions_made += 1
        
        if result.performance_score > 70:
            perf.successful_decisions += 1
        
        # Update running averages
        perf.confidence_score = (perf.confidence_score * 0.9) + (result.performance_score / 100.0 * 0.1)
    
    async def run_training_session(self, agent, num_scenarios: int = 10, scenario_types: List[str] = None) -> Dict[str, Any]:
        """Run a complete training session for an agent"""
        
        if scenario_types is None:
            scenario_types = ["deal_analysis", "negotiation", "portfolio_management"]
        
        results = []
        
        for i in range(num_scenarios):
            # Vary difficulty over time
            difficulty = min(1.0, 0.2 + (i / num_scenarios) * 0.8)
            
            # Choose scenario type
            scenario_type = np.random.choice(scenario_types)
            
            # Create and run scenario
            scenario = self.create_training_scenario(scenario_type, difficulty)
            result = await self.train_agent(agent, scenario)
            results.append(result)
            
            print(f"Scenario {i+1}/{num_scenarios}: {scenario_type} - Score: {result.performance_score:.1f}")
        
        # Calculate session summary
        avg_score = np.mean([r.performance_score for r in results])
        improvement = results[-1].performance_score - results[0].performance_score if len(results) > 1 else 0
        
        return {
            "session_summary": {
                "scenarios_completed": len(results),
                "average_score": avg_score,
                "improvement": improvement,
                "best_score": max(r.performance_score for r in results),
                "worst_score": min(r.performance_score for r in results)
            },
            "results": results,
            "agent_performance": self.agent_performances.get(getattr(agent, 'agent_id', 'unknown'))
        }
    
    def get_training_analytics(self) -> Dict[str, Any]:
        """Get comprehensive training analytics"""
        
        if not self.training_history:
            return {"message": "No training data available"}
        
        # Overall statistics
        total_sessions = len(self.training_history)
        avg_score = np.mean([r.performance_score for r in self.training_history])
        
        # Performance by scenario type
        scenario_performance = {}
        for result in self.training_history:
            scenario_type = next(
                (s.scenario_type for s in [self.create_training_scenario("deal_analysis")] 
                 if s.scenario_id == result.scenario_id), 
                "unknown"
            )
            
            if scenario_type not in scenario_performance:
                scenario_performance[scenario_type] = []
            scenario_performance[scenario_type].append(result.performance_score)
        
        # Agent rankings
        agent_scores = {}
        for result in self.training_history:
            if result.agent_id not in agent_scores:
                agent_scores[result.agent_id] = []
            agent_scores[result.agent_id].append(result.performance_score)
        
        agent_rankings = [
            {
                "agent_id": agent_id,
                "average_score": np.mean(scores),
                "total_scenarios": len(scores),
                "improvement_trend": scores[-1] - scores[0] if len(scores) > 1 else 0
            }
            for agent_id, scores in agent_scores.items()
        ]
        agent_rankings.sort(key=lambda x: x["average_score"], reverse=True)
        
        return {
            "overview": {
                "total_training_sessions": total_sessions,
                "average_performance": avg_score,
                "active_agents": len(self.agent_performances)
            },
            "scenario_performance": {
                scenario: {
                    "average_score": np.mean(scores),
                    "total_attempts": len(scores)
                }
                for scenario, scores in scenario_performance.items()
            },
            "agent_rankings": agent_rankings,
            "recent_activity": [
                {
                    "timestamp": r.timestamp.isoformat(),
                    "agent_id": r.agent_id,
                    "score": r.performance_score,
                    "scenario_id": r.scenario_id
                }
                for r in self.training_history[-10:]  # Last 10 results
            ]
        }