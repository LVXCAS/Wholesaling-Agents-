from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

from ..services.market_data_service import MarketDataService
from ..services.property_valuation_service import PropertyValuationService
from ..services.investment_analyzer_service import InvestmentAnalyzerService
from ..simulation.market_simulator import MarketSimulator
from ..simulation.agent_trainer import AgentTrainer
from .training_framework import TrainingFramework, TrainingConfig, TrainingAgent
from .curriculum_manager import CurriculumManager

router = APIRouter(prefix="/training", tags=["agent-training"])

# Initialize training components
market_service = MarketDataService()
valuation_service = PropertyValuationService(market_service)
investment_service = InvestmentAnalyzerService(market_service, valuation_service)
market_simulator = MarketSimulator(market_service)
agent_trainer = AgentTrainer(market_simulator, investment_service)
training_framework = TrainingFramework(market_simulator, agent_trainer)
curriculum_manager = CurriculumManager()

# Global training state
training_state = {
    "active_training_sessions": {},
    "trained_agents": {},
    "training_history": []
}

@router.post("/create-agent")
async def create_training_agent(
    agent_type: str,
    agent_id: Optional[str] = None,
    initial_skills: Optional[Dict[str, float]] = None
):
    """Create a new training agent"""
    try:
        # Create training agent
        agent = await training_framework.create_training_agent(agent_type, agent_id)
        
        # Create personalized curriculum
        learning_goals = ["deal_analysis", "negotiation", "portfolio_management"]
        curriculum = curriculum_manager.create_personalized_curriculum(
            agent.agent_id, agent_type, initial_skills, learning_goals
        )
        
        # Store agent
        training_state["trained_agents"][agent.agent_id] = {
            "agent": agent,
            "curriculum": curriculum,
            "created_at": datetime.now(),
            "status": "created"
        }
        
        return {
            "agent_id": agent.agent_id,
            "agent_type": agent_type,
            "status": "created",
            "curriculum_modules": len(curriculum),
            "estimated_training_time": sum(module.estimated_duration.days for module in curriculum)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-training/{agent_id}")
async def start_training_program(
    agent_id: str,
    background_tasks: BackgroundTasks,
    training_duration_days: int = 30,
    scenarios_per_day: int = 5,
    difficulty_progression: str = "linear"
):
    """Start a comprehensive training program for an agent"""
    try:
        if agent_id not in training_state["trained_agents"]:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent_data = training_state["trained_agents"][agent_id]
        agent = agent_data["agent"]
        
        # Create training configuration
        config = TrainingConfig(
            agent_type=agent.agent_type,
            training_duration_days=training_duration_days,
            scenarios_per_day=scenarios_per_day,
            difficulty_progression=difficulty_progression,
            scenario_types=["deal_analysis", "negotiation", "portfolio_management"],
            target_cities=["Miami", "Orlando", "Tampa", "Jacksonville"],
            performance_threshold=75.0,
            max_training_iterations=training_duration_days * scenarios_per_day
        )
        
        # Start training in background
        session_id = f"training_{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        training_state["active_training_sessions"][session_id] = {
            "agent_id": agent_id,
            "status": "starting",
            "start_time": datetime.now(),
            "config": config
        }
        
        # Run training asynchronously
        background_tasks.add_task(
            run_training_background,
            session_id,
            agent,
            config
        )
        
        return {
            "session_id": session_id,
            "agent_id": agent_id,
            "status": "training_started",
            "estimated_scenarios": config.max_training_iterations,
            "estimated_duration_days": training_duration_days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def run_training_background(session_id: str, agent: TrainingAgent, config: TrainingConfig):
    """Run training program in background"""
    try:
        training_state["active_training_sessions"][session_id]["status"] = "running"
        
        # Run the training program
        result = await training_framework.run_training_program(agent, config)
        
        # Update session status
        training_state["active_training_sessions"][session_id].update({
            "status": "completed",
            "end_time": datetime.now(),
            "result": result
        })
        
        # Move to history
        training_state["training_history"].append(training_state["active_training_sessions"][session_id])
        
        # Update agent status
        if agent.agent_id in training_state["trained_agents"]:
            training_state["trained_agents"][agent.agent_id]["status"] = "trained"
            training_state["trained_agents"][agent.agent_id]["last_training"] = result
        
    except Exception as e:
        training_state["active_training_sessions"][session_id].update({
            "status": "failed",
            "error": str(e),
            "end_time": datetime.now()
        })

@router.get("/training-status/{session_id}")
async def get_training_status(session_id: str):
    """Get status of a training session"""
    try:
        if session_id in training_state["active_training_sessions"]:
            session = training_state["active_training_sessions"][session_id]
            
            # Calculate progress if running
            progress = 0
            if session["status"] == "running":
                # Estimate progress based on time elapsed
                elapsed = datetime.now() - session["start_time"]
                estimated_total = session["config"].training_duration_days * 24 * 3600  # seconds
                progress = min(95, (elapsed.total_seconds() / estimated_total) * 100)
            elif session["status"] == "completed":
                progress = 100
            
            return {
                "session_id": session_id,
                "status": session["status"],
                "progress": progress,
                "agent_id": session["agent_id"],
                "start_time": session["start_time"].isoformat(),
                "elapsed_time": str(datetime.now() - session["start_time"]),
                "result": session.get("result"),
                "error": session.get("error")
            }
        else:
            # Check training history
            for historical_session in training_state["training_history"]:
                if historical_session.get("session_id") == session_id:
                    return {
                        "session_id": session_id,
                        "status": historical_session["status"],
                        "progress": 100 if historical_session["status"] == "completed" else 0,
                        "result": historical_session.get("result"),
                        "historical": True
                    }
            
            raise HTTPException(status_code=404, detail="Training session not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quick-training/{agent_id}")
async def quick_training_session(
    agent_id: str,
    num_scenarios: int = 10,
    scenario_type: str = "deal_analysis",
    difficulty: float = 0.5
):
    """Run a quick training session for immediate feedback"""
    try:
        if agent_id not in training_state["trained_agents"]:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent = training_state["trained_agents"][agent_id]["agent"]
        
        # Run quick training
        results = []
        for i in range(num_scenarios):
            # Progressive difficulty
            current_difficulty = difficulty + (i / num_scenarios) * 0.3
            current_difficulty = min(1.0, current_difficulty)
            
            # Create scenario
            scenario = agent_trainer.create_training_scenario(scenario_type, current_difficulty)
            
            # Train agent
            result = await agent_trainer.train_agent(agent, scenario)
            results.append({
                "scenario_id": scenario.scenario_id,
                "performance_score": result.performance_score,
                "decision": result.decision,
                "learning_points": result.learning_points
            })
        
        # Calculate session summary
        scores = [r["performance_score"] for r in results]
        summary = {
            "total_scenarios": len(results),
            "average_score": sum(scores) / len(scores),
            "best_score": max(scores),
            "worst_score": min(scores),
            "improvement": scores[-1] - scores[0] if len(scores) > 1 else 0
        }
        
        return {
            "agent_id": agent_id,
            "session_type": "quick_training",
            "summary": summary,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/curriculum/{agent_id}")
async def get_agent_curriculum(agent_id: str):
    """Get curriculum and progress for an agent"""
    try:
        # Get curriculum progress
        progress = curriculum_manager.get_curriculum_progress(agent_id)
        
        # Get next learning objective
        next_objective = curriculum_manager.get_next_learning_objective(agent_id)
        
        # Get scenario recommendations
        recommendations = curriculum_manager.recommend_next_scenarios(agent_id, 5)
        
        return {
            "agent_id": agent_id,
            "curriculum_progress": progress,
            "next_objective": {
                "name": next_objective.name,
                "description": next_objective.description,
                "category": next_objective.category.value,
                "skill_level": next_objective.skill_level.value
            } if next_objective else None,
            "recommended_scenarios": recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-progress/{agent_id}")
async def update_learning_progress(
    agent_id: str,
    objective_id: str,
    performance_data: Dict[str, Any]
):
    """Update learning progress for a specific objective"""
    try:
        curriculum_manager.update_objective_progress(agent_id, objective_id, performance_data)
        
        # Get updated progress
        progress = curriculum_manager.get_curriculum_progress(agent_id)
        
        return {
            "agent_id": agent_id,
            "objective_id": objective_id,
            "updated_progress": progress,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/curriculum-report/{agent_id}")
async def get_curriculum_report(agent_id: str):
    """Get comprehensive curriculum report for an agent"""
    try:
        report = curriculum_manager.generate_curriculum_report(agent_id)
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent-performance/{agent_id}")
async def get_agent_performance(agent_id: str):
    """Get detailed performance metrics for an agent"""
    try:
        if agent_id not in training_state["trained_agents"]:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent_data = training_state["trained_agents"][agent_id]
        agent = agent_data["agent"]
        
        # Get agent's internal metrics
        performance_metrics = agent.get_performance_metrics()
        
        # Get training framework metrics
        if agent_id in training_framework.agent_profiles:
            profile = training_framework.agent_profiles[agent_id]
            learning_curve = training_framework.learning_curves.get(agent_id, [])
            
            # Calculate recent performance trend
            recent_scores = [lp.performance_score for lp in learning_curve[-10:]]
            trend = "improving" if len(recent_scores) > 1 and recent_scores[-1] > recent_scores[0] else "stable"
            
            return {
                "agent_id": agent_id,
                "agent_profile": {
                    "agent_type": profile.agent_type,
                    "total_experience": profile.total_experience,
                    "accuracy_rate": profile.accuracy_rate,
                    "learning_velocity": profile.learning_velocity,
                    "strengths": profile.strengths,
                    "weaknesses": profile.weaknesses
                },
                "performance_metrics": performance_metrics,
                "learning_curve": {
                    "total_points": len(learning_curve),
                    "recent_trend": trend,
                    "recent_scores": recent_scores[-5:] if recent_scores else []
                },
                "status": agent_data["status"],
                "last_training": agent_data.get("last_training")
            }
        else:
            return {
                "agent_id": agent_id,
                "performance_metrics": performance_metrics,
                "status": agent_data["status"],
                "message": "Limited performance data available"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/training-analytics")
async def get_training_analytics():
    """Get overall training analytics across all agents"""
    try:
        # Active sessions
        active_sessions = len(training_state["active_training_sessions"])
        
        # Total trained agents
        total_agents = len(training_state["trained_agents"])
        
        # Training history summary
        completed_sessions = len(training_state["training_history"])
        
        # Agent performance distribution
        agent_scores = []
        for agent_data in training_state["trained_agents"].values():
            if "last_training" in agent_data and agent_data["last_training"]:
                final_score = agent_data["last_training"]["training_report"]["performance_summary"]["final_score"]
                agent_scores.append(final_score)
        
        performance_distribution = {
            "excellent": len([s for s in agent_scores if s >= 80]),
            "good": len([s for s in agent_scores if 60 <= s < 80]),
            "needs_improvement": len([s for s in agent_scores if s < 60])
        }
        
        return {
            "overview": {
                "total_agents": total_agents,
                "active_training_sessions": active_sessions,
                "completed_training_sessions": completed_sessions
            },
            "performance_distribution": performance_distribution,
            "average_performance": sum(agent_scores) / len(agent_scores) if agent_scores else 0,
            "training_framework_stats": training_framework.agent_trainer.get_training_analytics()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents")
async def list_training_agents():
    """List all training agents and their status"""
    try:
        agents = []
        
        for agent_id, agent_data in training_state["trained_agents"].items():
            agents.append({
                "agent_id": agent_id,
                "agent_type": agent_data["agent"]["agent_type"],
                "status": agent_data["status"],
                "created_at": agent_data["created_at"].isoformat(),
                "curriculum_modules": len(agent_data["curriculum"]),
                "has_training_history": "last_training" in agent_data
            })
        
        return {
            "agents": agents,
            "total_agents": len(agents)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/agent/{agent_id}")
async def delete_training_agent(agent_id: str):
    """Delete a training agent and its data"""
    try:
        if agent_id not in training_state["trained_agents"]:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Remove from trained agents
        del training_state["trained_agents"][agent_id]
        
        # Remove from training framework
        if agent_id in training_framework.agent_profiles:
            del training_framework.agent_profiles[agent_id]
        
        if agent_id in training_framework.learning_curves:
            del training_framework.learning_curves[agent_id]
        
        # Remove from curriculum manager
        if agent_id in curriculum_manager.agent_progress:
            del curriculum_manager.agent_progress[agent_id]
        
        return {
            "agent_id": agent_id,
            "status": "deleted",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))