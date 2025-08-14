from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
import asyncio
from ..services.market_data_service import MarketDataService
from ..services.property_valuation_service import PropertyValuationService
from ..services.investment_analyzer_service import InvestmentAnalyzerService
from .market_simulator import MarketSimulator
from .agent_trainer import AgentTrainer
# from ..agents.portfolio_agent import PortfolioAgent
# from ..agents.contract_agent import ContractAgent

router = APIRouter(prefix="/simulation", tags=["simulation"])

# Initialize simulation components
market_service = MarketDataService()
valuation_service = PropertyValuationService(market_service)
investment_service = InvestmentAnalyzerService(market_service, valuation_service)
market_simulator = MarketSimulator(market_service)
agent_trainer = AgentTrainer(market_simulator, investment_service)

# Global simulation state
simulation_state = {
    "active_simulations": {},
    "trained_agents": {}
}

@router.get("/market-condition")
async def get_current_market_condition():
    """Get current simulated market conditions"""
    try:
        return market_simulator.get_market_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-deal")
async def generate_deal_scenario(
    city: Optional[str] = None,
    state: Optional[str] = None
):
    """Generate a realistic deal scenario for testing"""
    try:
        deal = market_simulator.generate_deal_scenario(city, state)
        
        return {
            "deal_id": deal.property_id,
            "property": deal.property_data,
            "market_value": deal.market_value,
            "asking_price": deal.asking_price,
            "seller_motivation": deal.seller_motivation,
            "days_on_market": deal.days_on_market,
            "competition_level": deal.competition_level,
            "market_condition": {
                "trend": deal.market_condition.trend,
                "interest_rate": deal.market_condition.interest_rate,
                "inventory_level": deal.market_condition.inventory_level,
                "price_momentum": deal.market_condition.price_momentum,
                "season": deal.market_condition.season
            },
            "created_at": deal.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-batch-deals")
async def generate_batch_deals(
    count: int = 10,
    cities: Optional[List[str]] = None
):
    """Generate multiple deal scenarios for batch training"""
    try:
        deals = market_simulator.generate_batch_scenarios(count, cities)
        
        return {
            "deals": [
                {
                    "deal_id": deal.property_id,
                    "property": deal.property_data,
                    "asking_price": deal.asking_price,
                    "market_value": deal.market_value,
                    "seller_motivation": deal.seller_motivation,
                    "competition_level": deal.competition_level,
                    "market_trend": deal.market_condition.trend
                }
                for deal in deals
            ],
            "total_generated": len(deals),
            "market_condition": market_simulator.get_market_summary()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-training-scenario")
async def create_training_scenario(
    scenario_type: str,
    difficulty: float = 0.5
):
    """Create a training scenario for agent training"""
    try:
        if scenario_type not in ["deal_analysis", "negotiation", "portfolio_management"]:
            raise HTTPException(status_code=400, detail="Invalid scenario type")
        
        if not 0.0 <= difficulty <= 1.0:
            raise HTTPException(status_code=400, detail="Difficulty must be between 0.0 and 1.0")
        
        scenario = agent_trainer.create_training_scenario(scenario_type, difficulty)
        
        return {
            "scenario_id": scenario.scenario_id,
            "scenario_type": scenario.scenario_type,
            "difficulty_level": scenario.difficulty_level,
            "learning_objectives": scenario.learning_objectives,
            "deal": {
                "property": scenario.deal.property_data,
                "asking_price": scenario.deal.asking_price,
                "market_value": scenario.deal.market_value,
                "seller_motivation": scenario.deal.seller_motivation,
                "days_on_market": scenario.deal.days_on_market,
                "competition_level": scenario.deal.competition_level
            },
            "expected_outcome": scenario.expected_outcome
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train-agent")
async def train_agent_endpoint(
    agent_type: str,
    num_scenarios: int = 10,
    scenario_types: Optional[List[str]] = None
):
    """Train an agent using simulation scenarios"""
    try:
        # Create mock agent instance for training
        class MockAgent:
            def __init__(self, agent_type):
                self.agent_id = f"{agent_type}_agent_{len(simulation_state['trained_agents'])}"
                self.agent_type = agent_type
            
            async def analyze_deal(self, scenario_data):
                # Mock decision logic
                deal = scenario_data["deal"]
                asking_price = deal["asking_price"]
                action = "pursue" if asking_price < 500000 else "pass"
                offer_price = asking_price * 0.95 if action == "pursue" else 0
                
                return {
                    "action": action,
                    "offer_price": offer_price,
                    "confidence": 0.75,
                    "reasoning": f"Mock {agent_type} agent decision"
                }
        
        agent = MockAgent(agent_type)
        
        # Run training session
        session_result = await agent_trainer.run_training_session(
            agent, num_scenarios, scenario_types
        )
        
        # Store trained agent
        simulation_state["trained_agents"][agent.agent_id] = {
            "agent": agent,
            "training_results": session_result
        }
        
        return {
            "agent_id": agent.agent_id,
            "training_completed": True,
            "session_summary": session_result["session_summary"],
            "performance_metrics": session_result.get("agent_performance")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/training-analytics")
async def get_training_analytics():
    """Get comprehensive training analytics"""
    try:
        analytics = agent_trainer.get_training_analytics()
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate-market-cycle")
async def simulate_market_cycle(days: int = 365):
    """Simulate market conditions over time"""
    try:
        if days < 1 or days > 3650:  # Max 10 years
            raise HTTPException(status_code=400, detail="Days must be between 1 and 3650")
        
        conditions = market_simulator.simulate_market_cycle(days)
        
        # Sample conditions for response (don't return all days)
        sample_size = min(50, len(conditions))
        sample_indices = [int(i * len(conditions) / sample_size) for i in range(sample_size)]
        sampled_conditions = [conditions[i] for i in sample_indices]
        
        return {
            "simulation_days": days,
            "total_conditions": len(conditions),
            "sampled_conditions": [
                {
                    "day": idx,
                    "trend": cond.trend,
                    "interest_rate": round(cond.interest_rate, 2),
                    "price_momentum": round(cond.price_momentum, 3),
                    "volatility": round(cond.volatility, 3),
                    "inventory_level": cond.inventory_level
                }
                for idx, cond in zip(sample_indices, sampled_conditions)
            ],
            "summary": {
                "avg_interest_rate": round(sum(c.interest_rate for c in conditions) / len(conditions), 2),
                "trend_distribution": {
                    "bull": sum(1 for c in conditions if c.trend == "bull"),
                    "bear": sum(1 for c in conditions if c.trend == "bear"),
                    "stable": sum(1 for c in conditions if c.trend == "stable")
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active-deals")
async def get_active_deals():
    """Get all active simulated deals"""
    try:
        deals = market_simulator.active_deals
        
        return {
            "active_deals": [
                {
                    "deal_id": deal.property_id,
                    "property": deal.property_data,
                    "asking_price": deal.asking_price,
                    "market_value": deal.market_value,
                    "days_on_market": deal.days_on_market,
                    "seller_motivation": deal.seller_motivation,
                    "competition_level": deal.competition_level,
                    "created_at": deal.created_at.isoformat()
                }
                for deal in deals
            ],
            "total_active": len(deals)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/close-deal/{deal_id}")
async def close_deal(deal_id: str, outcome: Dict[str, Any]):
    """Close a simulated deal with outcome"""
    try:
        success = market_simulator.close_deal(deal_id, outcome)
        
        if success:
            return {
                "deal_id": deal_id,
                "status": "closed",
                "outcome": outcome
            }
        else:
            raise HTTPException(status_code=404, detail="Deal not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trained-agents")
async def get_trained_agents():
    """Get list of trained agents and their performance"""
    try:
        agents_info = []
        
        for agent_id, agent_data in simulation_state["trained_agents"].items():
            training_results = agent_data["training_results"]
            
            agents_info.append({
                "agent_id": agent_id,
                "agent_type": getattr(agent_data["agent"], "__class__", {}).get("__name__", "Unknown"),
                "training_summary": training_results["session_summary"],
                "performance": training_results.get("agent_performance")
            })
        
        return {
            "trained_agents": agents_info,
            "total_agents": len(agents_info)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset-simulation")
async def reset_simulation():
    """Reset simulation state"""
    try:
        # Clear active deals
        market_simulator.active_deals.clear()
        market_simulator.deal_history.clear()
        
        # Reset market conditions
        market_simulator.current_condition = market_simulator._generate_market_condition()
        
        # Clear training data
        agent_trainer.training_history.clear()
        agent_trainer.agent_performances.clear()
        
        # Clear simulation state
        simulation_state["active_simulations"].clear()
        simulation_state["trained_agents"].clear()
        
        return {
            "status": "simulation_reset",
            "message": "All simulation data has been cleared"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))