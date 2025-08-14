from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from ..services.market_data_service import MarketDataService
from ..services.property_valuation_service import PropertyValuationService
from ..services.investment_analyzer_service import InvestmentAnalyzerService
from ..simulation.market_simulator import MarketSimulator
from .curriculum_manager import CurriculumManager

router = APIRouter(prefix="/training", tags=["agent-training"])

# Initialize components
market_service = MarketDataService()
valuation_service = PropertyValuationService(market_service)
investment_service = InvestmentAnalyzerService(market_service, valuation_service)
market_simulator = MarketSimulator(market_service)
curriculum_manager = CurriculumManager()

# Global training state
training_state = {
    "agents": {},
    "training_sessions": {},
    "completed_training": []
}

class SimpleTrainingAgent:
    """Simple training agent for demonstration"""
    
    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.training_history = []
        self.performance_metrics = {
            "total_scenarios": 0,
            "average_score": 0.0,
            "best_score": 0.0,
            "improvement_rate": 0.0
        }
    
    async def analyze_deal(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a deal scenario"""
        deal = scenario_data["deal"]
        asking_price = deal["asking_price"]
        market_condition = deal.get("market_condition", {})
        
        # Simple decision logic that improves with training
        base_confidence = 0.6 + (len(self.training_history) * 0.01)  # Improves with experience
        base_confidence = min(0.9, base_confidence)
        
        # Market condition adjustments
        if market_condition.get("trend") == "bull":
            base_confidence += 0.05
        elif market_condition.get("trend") == "bear":
            base_confidence -= 0.05
        
        # Decision logic
        if asking_price < 400000 and base_confidence > 0.7:
            action = "pursue"
            offer_price = asking_price * 0.95
        elif asking_price < 600000 and base_confidence > 0.8:
            action = "pursue"
            offer_price = asking_price * 0.92
        else:
            action = "pass"
            offer_price = 0
        
        decision = {
            "action": action,
            "offer_price": offer_price,
            "confidence": base_confidence,
            "reasoning": f"Decision based on price analysis and {market_condition.get('trend', 'stable')} market",
            "agent_type": self.agent_type
        }
        
        return decision
    
    def update_performance(self, score: float):
        """Update performance metrics"""
        self.training_history.append(score)
        self.performance_metrics["total_scenarios"] = len(self.training_history)
        self.performance_metrics["average_score"] = sum(self.training_history) / len(self.training_history)
        self.performance_metrics["best_score"] = max(self.training_history)
        
        if len(self.training_history) > 5:
            recent_avg = sum(self.training_history[-5:]) / 5
            early_avg = sum(self.training_history[:5]) / 5
            self.performance_metrics["improvement_rate"] = recent_avg - early_avg

@router.post("/create-agent")
async def create_training_agent(
    agent_type: str,
    agent_id: Optional[str] = None
):
    """Create a new training agent"""
    try:
        if not agent_id:
            agent_id = f"{agent_type}_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create training agent
        agent = SimpleTrainingAgent(agent_id, agent_type)
        
        # Create curriculum
        curriculum = curriculum_manager.create_personalized_curriculum(
            agent_id, agent_type, {}, ["deal_analysis", "negotiation", "portfolio_management"]
        )
        
        # Store agent
        training_state["agents"][agent_id] = {
            "agent": agent,
            "curriculum": curriculum,
            "created_at": datetime.now(),
            "status": "created"
        }
        
        return {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "status": "created",
            "curriculum_modules": len(curriculum)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quick-training/{agent_id}")
async def quick_training_session(
    agent_id: str,
    num_scenarios: int = 10,
    difficulty_start: float = 0.3
):
    """Run a quick training session"""
    try:
        if agent_id not in training_state["agents"]:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent_data = training_state["agents"][agent_id]
        agent = agent_data["agent"]
        
        results = []
        
        for i in range(num_scenarios):
            # Progressive difficulty
            difficulty = difficulty_start + (i / num_scenarios) * 0.4
            difficulty = min(1.0, difficulty)
            
            # Generate deal scenario
            deal = market_simulator.generate_deal_scenario()
            
            # Create scenario data
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
                "difficulty": difficulty
            }
            
            # Get agent decision
            decision = await agent.analyze_deal(scenario_data)
            
            # Calculate performance score
            score = calculate_performance_score(decision, deal, difficulty)
            
            # Update agent performance
            agent.update_performance(score)
            
            results.append({
                "scenario": i + 1,
                "difficulty": difficulty,
                "decision": decision,
                "performance_score": score,
                "deal_summary": {
                    "asking_price": deal.asking_price,
                    "market_value": deal.market_value,
                    "equity_potential": deal.market_value - deal.asking_price
                }
            })
        
        # Calculate session summary
        scores = [r["performance_score"] for r in results]
        summary = {
            "total_scenarios": len(results),
            "average_score": sum(scores) / len(scores),
            "best_score": max(scores),
            "improvement": scores[-1] - scores[0] if len(scores) > 1 else 0,
            "agent_performance": agent.performance_metrics
        }
        
        return {
            "agent_id": agent_id,
            "session_summary": summary,
            "detailed_results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def calculate_performance_score(decision: Dict[str, Any], deal, difficulty: float) -> float:
    """Calculate performance score for a decision"""
    score = 50.0  # Base score
    
    # Analyze decision quality
    asking_price = deal.asking_price
    market_value = deal.market_value
    equity_potential = market_value - asking_price
    
    action = decision.get("action", "pass")
    offer_price = decision.get("offer_price", 0)
    confidence = decision.get("confidence", 0.5)
    
    # Good deal identification
    if equity_potential > 0:  # Good deal
        if action == "pursue":
            score += 30  # Correctly identified good deal
        else:
            score -= 20  # Missed good deal
    else:  # Poor deal
        if action == "pass":
            score += 20  # Correctly avoided bad deal
        else:
            score -= 30  # Pursued bad deal
    
    # Offer price accuracy
    if action == "pursue" and offer_price > 0:
        if market_value > 0:
            price_accuracy = 1 - abs(offer_price - market_value * 0.95) / market_value
            score += price_accuracy * 20
    
    # Confidence calibration
    expected_confidence = 0.8 if equity_potential > 0 else 0.4
    confidence_accuracy = 1 - abs(confidence - expected_confidence)
    score += confidence_accuracy * 10
    
    # Difficulty bonus
    score += difficulty * 10
    
    return max(0, min(100, score))

@router.get("/agent-performance/{agent_id}")
async def get_agent_performance(agent_id: str):
    """Get agent performance metrics"""
    try:
        if agent_id not in training_state["agents"]:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent_data = training_state["agents"][agent_id]
        agent = agent_data["agent"]
        
        return {
            "agent_id": agent_id,
            "agent_type": agent.agent_type,
            "performance_metrics": agent.performance_metrics,
            "training_history": agent.training_history[-10:],  # Last 10 scores
            "status": agent_data["status"],
            "created_at": agent_data["created_at"].isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/curriculum/{agent_id}")
async def get_agent_curriculum(agent_id: str):
    """Get curriculum progress for an agent"""
    try:
        progress = curriculum_manager.get_curriculum_progress(agent_id)
        next_objective = curriculum_manager.get_next_learning_objective(agent_id)
        recommendations = curriculum_manager.recommend_next_scenarios(agent_id, 3)
        
        return {
            "agent_id": agent_id,
            "curriculum_progress": progress,
            "next_objective": {
                "name": next_objective.name,
                "description": next_objective.description,
                "category": next_objective.category.value
            } if next_objective else None,
            "scenario_recommendations": recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-training/{agent_id}")
async def batch_training_session(
    agent_id: str,
    num_sessions: int = 5,
    scenarios_per_session: int = 10
):
    """Run multiple training sessions"""
    try:
        if agent_id not in training_state["agents"]:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        session_results = []
        
        for session in range(num_sessions):
            # Progressive difficulty across sessions
            base_difficulty = 0.2 + (session / num_sessions) * 0.6
            
            result = await quick_training_session(
                agent_id, scenarios_per_session, base_difficulty
            )
            
            session_results.append({
                "session": session + 1,
                "summary": result["session_summary"],
                "base_difficulty": base_difficulty
            })
        
        # Overall summary
        all_scores = []
        for session in session_results:
            all_scores.append(session["summary"]["average_score"])
        
        overall_summary = {
            "total_sessions": len(session_results),
            "total_scenarios": num_sessions * scenarios_per_session,
            "overall_average": sum(all_scores) / len(all_scores),
            "best_session": max(all_scores),
            "improvement": all_scores[-1] - all_scores[0] if len(all_scores) > 1 else 0
        }
        
        return {
            "agent_id": agent_id,
            "batch_training_complete": True,
            "overall_summary": overall_summary,
            "session_results": session_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents")
async def list_training_agents():
    """List all training agents"""
    try:
        agents = []
        
        for agent_id, agent_data in training_state["agents"].items():
            agent = agent_data["agent"]
            agents.append({
                "agent_id": agent_id,
                "agent_type": agent.agent_type,
                "status": agent_data["status"],
                "performance": agent.performance_metrics,
                "created_at": agent_data["created_at"].isoformat()
            })
        
        return {
            "agents": agents,
            "total_agents": len(agents)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/training-analytics")
async def get_training_analytics():
    """Get overall training analytics"""
    try:
        total_agents = len(training_state["agents"])
        
        if total_agents == 0:
            return {
                "message": "No agents created yet",
                "total_agents": 0
            }
        
        # Aggregate performance metrics
        all_scores = []
        agent_types = {}
        
        for agent_data in training_state["agents"].values():
            agent = agent_data["agent"]
            if agent.performance_metrics["total_scenarios"] > 0:
                all_scores.append(agent.performance_metrics["average_score"])
                
                agent_type = agent.agent_type
                if agent_type not in agent_types:
                    agent_types[agent_type] = []
                agent_types[agent_type].append(agent.performance_metrics["average_score"])
        
        analytics = {
            "total_agents": total_agents,
            "agents_with_training": len(all_scores),
            "overall_performance": {
                "average_score": sum(all_scores) / len(all_scores) if all_scores else 0,
                "best_score": max(all_scores) if all_scores else 0,
                "score_distribution": {
                    "excellent": len([s for s in all_scores if s >= 80]),
                    "good": len([s for s in all_scores if 60 <= s < 80]),
                    "needs_improvement": len([s for s in all_scores if s < 60])
                }
            },
            "performance_by_type": {
                agent_type: {
                    "count": len(scores),
                    "average": sum(scores) / len(scores)
                }
                for agent_type, scores in agent_types.items()
            }
        }
        
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))