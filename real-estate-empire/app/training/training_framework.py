import asyncio
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

from ..simulation.market_simulator import MarketSimulator
from ..simulation.agent_trainer import AgentTrainer, TrainingScenario, TrainingResult
from ..services.market_data_service import MarketDataService
from ..services.investment_analyzer_service import InvestmentAnalyzerService

logger = logging.getLogger(__name__)

@dataclass
class TrainingConfig:
    """Configuration for agent training"""
    agent_type: str
    training_duration_days: int = 30
    scenarios_per_day: int = 5
    difficulty_progression: str = "linear"  # "linear", "exponential", "adaptive"
    scenario_types: List[str] = None
    target_cities: List[str] = None
    performance_threshold: float = 75.0
    max_training_iterations: int = 1000
    save_checkpoints: bool = True
    checkpoint_interval: int = 50

@dataclass
class LearningCurve:
    """Track learning progress over time"""
    iteration: int
    timestamp: datetime
    performance_score: float
    scenario_type: str
    difficulty: float
    decision_time: float
    confidence: float
    learning_rate: float

@dataclass
class AgentProfile:
    """Agent performance profile and characteristics"""
    agent_id: str
    agent_type: str
    specializations: List[str]
    strengths: List[str]
    weaknesses: List[str]
    preferred_scenarios: List[str]
    risk_tolerance: float
    decision_speed: float
    accuracy_rate: float
    learning_velocity: float
    total_experience: int

class TrainingFramework:
    """Comprehensive agent training framework"""
    
    def __init__(self, market_simulator: MarketSimulator, agent_trainer: AgentTrainer):
        self.market_simulator = market_simulator
        self.agent_trainer = agent_trainer
        self.training_sessions: Dict[str, Dict] = {}
        self.agent_profiles: Dict[str, AgentProfile] = {}
        self.learning_curves: Dict[str, List[LearningCurve]] = {}
        self.training_data_path = Path("training_data")
        self.training_data_path.mkdir(exist_ok=True)
    
    async def create_training_agent(self, agent_type: str, agent_id: str = None) -> 'TrainingAgent':
        """Create a trainable agent wrapper"""
        if not agent_id:
            agent_id = f"{agent_type}_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create base agent profile
        profile = AgentProfile(
            agent_id=agent_id,
            agent_type=agent_type,
            specializations=[],
            strengths=[],
            weaknesses=[],
            preferred_scenarios=[],
            risk_tolerance=0.5,
            decision_speed=1.0,
            accuracy_rate=0.5,
            learning_velocity=0.1,
            total_experience=0
        )
        
        self.agent_profiles[agent_id] = profile
        self.learning_curves[agent_id] = []
        
        return TrainingAgent(agent_id, agent_type, self)
    
    async def run_training_program(self, agent: 'TrainingAgent', config: TrainingConfig) -> Dict[str, Any]:
        """Run a comprehensive training program"""
        
        logger.info(f"Starting training program for {agent.agent_id}")
        
        # Initialize training session
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_data = {
            "session_id": session_id,
            "agent_id": agent.agent_id,
            "config": asdict(config),
            "start_time": datetime.now(),
            "status": "running",
            "results": []
        }
        
        self.training_sessions[session_id] = session_data
        
        try:
            # Phase 1: Foundation Training
            logger.info("Phase 1: Foundation Training")
            foundation_results = await self._run_foundation_training(agent, config)
            session_data["results"].extend(foundation_results)
            
            # Phase 2: Specialized Training
            logger.info("Phase 2: Specialized Training")
            specialized_results = await self._run_specialized_training(agent, config)
            session_data["results"].extend(specialized_results)
            
            # Phase 3: Advanced Scenarios
            logger.info("Phase 3: Advanced Scenarios")
            advanced_results = await self._run_advanced_training(agent, config)
            session_data["results"].extend(advanced_results)
            
            # Phase 4: Performance Evaluation
            logger.info("Phase 4: Performance Evaluation")
            evaluation_results = await self._run_performance_evaluation(agent, config)
            
            # Update agent profile
            await self._update_agent_profile(agent, session_data["results"])
            
            # Generate training report
            report = self._generate_training_report(agent, session_data, evaluation_results)
            
            session_data["status"] = "completed"
            session_data["end_time"] = datetime.now()
            session_data["final_report"] = report
            
            logger.info(f"Training program completed for {agent.agent_id}")
            
            return {
                "session_id": session_id,
                "agent_id": agent.agent_id,
                "status": "completed",
                "training_report": report,
                "performance_improvement": report["performance_summary"]["improvement"],
                "final_score": report["performance_summary"]["final_score"]
            }
            
        except Exception as e:
            logger.error(f"Training program failed for {agent.agent_id}: {e}")
            session_data["status"] = "failed"
            session_data["error"] = str(e)
            raise
    
    async def _run_foundation_training(self, agent: 'TrainingAgent', config: TrainingConfig) -> List[TrainingResult]:
        """Run foundation training phase"""
        results = []
        
        # Basic deal analysis scenarios
        for i in range(20):
            difficulty = 0.2 + (i / 20) * 0.3  # 0.2 to 0.5
            scenario = self.agent_trainer.create_training_scenario("deal_analysis", difficulty)
            result = await self._train_with_feedback(agent, scenario)
            results.append(result)
            
            # Track learning curve
            self._record_learning_point(agent, result, i, "foundation")
        
        return results
    
    async def _run_specialized_training(self, agent: 'TrainingAgent', config: TrainingConfig) -> List[TrainingResult]:
        """Run specialized training based on agent type"""
        results = []
        
        scenario_types = config.scenario_types or ["deal_analysis", "negotiation", "portfolio_management"]
        
        for scenario_type in scenario_types:
            for i in range(15):
                difficulty = 0.4 + (i / 15) * 0.4  # 0.4 to 0.8
                scenario = self.agent_trainer.create_training_scenario(scenario_type, difficulty)
                result = await self._train_with_feedback(agent, scenario)
                results.append(result)
                
                # Track learning curve
                self._record_learning_point(agent, result, len(results), "specialized")
        
        return results
    
    async def _run_advanced_training(self, agent: 'TrainingAgent', config: TrainingConfig) -> List[TrainingResult]:
        """Run advanced training with complex scenarios"""
        results = []
        
        # Multi-step scenarios
        for i in range(10):
            difficulty = 0.7 + (i / 10) * 0.3  # 0.7 to 1.0
            
            # Create complex scenario with multiple properties
            scenario = await self._create_complex_scenario(difficulty)
            result = await self._train_with_feedback(agent, scenario)
            results.append(result)
            
            # Track learning curve
            self._record_learning_point(agent, result, len(results), "advanced")
        
        return results
    
    async def _create_complex_scenario(self, difficulty: float) -> TrainingScenario:
        """Create complex multi-property scenario"""
        
        # Generate multiple deals for portfolio decision
        deals = self.market_simulator.generate_batch_scenarios(3, ["Miami", "Orlando", "Tampa"])
        
        # Create complex scenario
        scenario_data = {
            "scenario_type": "portfolio_optimization",
            "deals": deals,
            "budget_constraint": 1000000,
            "risk_tolerance": np.random.uniform(0.3, 0.8),
            "time_constraint": np.random.randint(30, 90),
            "market_outlook": np.random.choice(["bullish", "bearish", "neutral"])
        }
        
        # Calculate expected outcome
        expected_outcome = {
            "optimal_selection": [],  # Would be calculated by optimization algorithm
            "expected_roi": 0.0,
            "risk_score": 0.0,
            "diversification_score": 0.0
        }
        
        return TrainingScenario(
            scenario_id=f"COMPLEX_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            scenario_type="portfolio_optimization",
            deal=deals[0],  # Primary deal
            expected_outcome=expected_outcome,
            difficulty_level=difficulty,
            learning_objectives=[
                "Multi-property analysis",
                "Budget optimization",
                "Risk management",
                "Portfolio diversification"
            ]
        )
    
    async def _train_with_feedback(self, agent: 'TrainingAgent', scenario: TrainingScenario) -> TrainingResult:
        """Train agent with immediate feedback"""
        
        # Get agent decision
        start_time = datetime.now()
        result = await self.agent_trainer.train_agent(agent, scenario)
        decision_time = (datetime.now() - start_time).total_seconds()
        
        # Provide feedback to agent
        feedback = self._generate_feedback(result)
        await agent.receive_feedback(feedback)
        
        # Update result with timing
        result.decision_time = decision_time
        
        return result
    
    def _generate_feedback(self, result: TrainingResult) -> Dict[str, Any]:
        """Generate constructive feedback for agent"""
        
        feedback = {
            "performance_score": result.performance_score,
            "strengths": [],
            "areas_for_improvement": [],
            "specific_recommendations": [],
            "learning_points": result.learning_points
        }
        
        # Analyze performance
        if result.performance_score >= 80:
            feedback["strengths"].append("Excellent decision-making accuracy")
        elif result.performance_score >= 60:
            feedback["strengths"].append("Good analytical approach")
        else:
            feedback["areas_for_improvement"].append("Decision accuracy needs improvement")
        
        # Specific recommendations based on decision
        decision = result.decision
        expected = result.actual_outcome
        
        if "offer_price" in decision and "max_offer" in expected:
            price_diff = abs(decision["offer_price"] - expected["max_offer"]) / expected["max_offer"]
            if price_diff > 0.1:
                feedback["specific_recommendations"].append(
                    f"Consider market value more carefully - price was {price_diff*100:.1f}% off target"
                )
        
        return feedback
    
    def _record_learning_point(self, agent: 'TrainingAgent', result: TrainingResult, iteration: int, phase: str):
        """Record a point on the learning curve"""
        
        learning_point = LearningCurve(
            iteration=iteration,
            timestamp=result.timestamp,
            performance_score=result.performance_score,
            scenario_type=phase,
            difficulty=0.5,  # Would get from scenario
            decision_time=getattr(result, 'decision_time', 0.0),
            confidence=result.decision.get('confidence', 0.5),
            learning_rate=0.1  # Would calculate based on improvement
        )
        
        self.learning_curves[agent.agent_id].append(learning_point)
    
    async def _run_performance_evaluation(self, agent: 'TrainingAgent', config: TrainingConfig) -> Dict[str, Any]:
        """Run comprehensive performance evaluation"""
        
        evaluation_results = {
            "overall_score": 0.0,
            "category_scores": {},
            "consistency": 0.0,
            "improvement_rate": 0.0,
            "strengths": [],
            "weaknesses": [],
            "recommendations": []
        }
        
        # Test on standardized scenarios
        test_scenarios = []
        for scenario_type in ["deal_analysis", "negotiation", "portfolio_management"]:
            for difficulty in [0.3, 0.6, 0.9]:
                scenario = self.agent_trainer.create_training_scenario(scenario_type, difficulty)
                test_scenarios.append(scenario)
        
        test_results = []
        for scenario in test_scenarios:
            result = await self.agent_trainer.train_agent(agent, scenario)
            test_results.append(result)
        
        # Calculate metrics
        scores = [r.performance_score for r in test_results]
        evaluation_results["overall_score"] = np.mean(scores)
        evaluation_results["consistency"] = 100 - np.std(scores)  # Lower std = higher consistency
        
        # Category performance
        for scenario_type in ["deal_analysis", "negotiation", "portfolio_management"]:
            category_scores = [r.performance_score for r in test_results 
                             if scenario_type in r.scenario_id.lower()]
            if category_scores:
                evaluation_results["category_scores"][scenario_type] = np.mean(category_scores)
        
        # Learning curve analysis
        if len(self.learning_curves[agent.agent_id]) > 10:
            recent_scores = [lp.performance_score for lp in self.learning_curves[agent.agent_id][-10:]]
            early_scores = [lp.performance_score for lp in self.learning_curves[agent.agent_id][:10]]
            evaluation_results["improvement_rate"] = np.mean(recent_scores) - np.mean(early_scores)
        
        return evaluation_results
    
    async def _update_agent_profile(self, agent: 'TrainingAgent', results: List[TrainingResult]):
        """Update agent profile based on training results"""
        
        profile = self.agent_profiles[agent.agent_id]
        
        # Calculate performance metrics
        scores = [r.performance_score for r in results]
        profile.accuracy_rate = np.mean(scores) / 100.0
        profile.total_experience = len(results)
        
        # Identify strengths and weaknesses
        scenario_performance = {}
        for result in results:
            # Extract scenario type from result (simplified)
            scenario_type = "deal_analysis"  # Would extract from result
            if scenario_type not in scenario_performance:
                scenario_performance[scenario_type] = []
            scenario_performance[scenario_type].append(result.performance_score)
        
        # Determine strengths (>75% average) and weaknesses (<60% average)
        profile.strengths = []
        profile.weaknesses = []
        
        for scenario_type, scores in scenario_performance.items():
            avg_score = np.mean(scores)
            if avg_score > 75:
                profile.strengths.append(scenario_type)
            elif avg_score < 60:
                profile.weaknesses.append(scenario_type)
        
        # Calculate learning velocity
        if len(self.learning_curves[agent.agent_id]) > 5:
            recent_improvement = self.learning_curves[agent.agent_id][-1].performance_score - \
                               self.learning_curves[agent.agent_id][-5].performance_score
            profile.learning_velocity = max(0, recent_improvement / 5.0 / 100.0)
    
    def _generate_training_report(self, agent: 'TrainingAgent', session_data: Dict, evaluation: Dict) -> Dict[str, Any]:
        """Generate comprehensive training report"""
        
        results = session_data["results"]
        profile = self.agent_profiles[agent.agent_id]
        learning_curve = self.learning_curves[agent.agent_id]
        
        # Performance summary
        scores = [r.performance_score for r in results]
        performance_summary = {
            "initial_score": scores[0] if scores else 0,
            "final_score": scores[-1] if scores else 0,
            "average_score": np.mean(scores) if scores else 0,
            "best_score": max(scores) if scores else 0,
            "improvement": (scores[-1] - scores[0]) if len(scores) > 1 else 0,
            "consistency": 100 - np.std(scores) if scores else 0
        }
        
        # Learning analysis
        learning_analysis = {
            "total_scenarios": len(results),
            "training_duration": str(session_data.get("end_time", datetime.now()) - session_data["start_time"]),
            "learning_velocity": profile.learning_velocity,
            "plateau_detection": self._detect_learning_plateau(learning_curve),
            "breakthrough_moments": self._identify_breakthroughs(learning_curve)
        }
        
        # Recommendations
        recommendations = []
        
        if performance_summary["improvement"] < 10:
            recommendations.append("Consider adjusting learning parameters or training approach")
        
        if profile.weaknesses:
            recommendations.append(f"Focus additional training on: {', '.join(profile.weaknesses)}")
        
        if evaluation["consistency"] < 70:
            recommendations.append("Work on decision consistency across different scenarios")
        
        return {
            "agent_profile": asdict(profile),
            "performance_summary": performance_summary,
            "learning_analysis": learning_analysis,
            "evaluation_results": evaluation,
            "recommendations": recommendations,
            "training_data": {
                "total_scenarios": len(results),
                "scenario_breakdown": self._analyze_scenario_breakdown(results),
                "difficulty_progression": self._analyze_difficulty_progression(results)
            }
        }
    
    def _detect_learning_plateau(self, learning_curve: List[LearningCurve]) -> bool:
        """Detect if agent has hit a learning plateau"""
        if len(learning_curve) < 20:
            return False
        
        recent_scores = [lp.performance_score for lp in learning_curve[-10:]]
        return np.std(recent_scores) < 5 and np.mean(recent_scores) < 80
    
    def _identify_breakthroughs(self, learning_curve: List[LearningCurve]) -> List[Dict]:
        """Identify breakthrough moments in learning"""
        breakthroughs = []
        
        for i in range(5, len(learning_curve)):
            current_score = learning_curve[i].performance_score
            previous_avg = np.mean([lp.performance_score for lp in learning_curve[i-5:i]])
            
            if current_score > previous_avg + 15:  # 15+ point jump
                breakthroughs.append({
                    "iteration": i,
                    "score_jump": current_score - previous_avg,
                    "timestamp": learning_curve[i].timestamp.isoformat()
                })
        
        return breakthroughs
    
    def _analyze_scenario_breakdown(self, results: List[TrainingResult]) -> Dict[str, int]:
        """Analyze breakdown of scenario types"""
        breakdown = {}
        for result in results:
            # Simplified - would extract actual scenario type
            scenario_type = "deal_analysis"
            breakdown[scenario_type] = breakdown.get(scenario_type, 0) + 1
        return breakdown
    
    def _analyze_difficulty_progression(self, results: List[TrainingResult]) -> Dict[str, Any]:
        """Analyze how difficulty progressed during training"""
        return {
            "started_at": "basic",
            "ended_at": "advanced",
            "progression_rate": "steady"
        }
    
    def save_training_session(self, session_id: str):
        """Save training session data to disk"""
        if session_id in self.training_sessions:
            session_data = self.training_sessions[session_id]
            file_path = self.training_data_path / f"{session_id}.json"
            
            # Convert datetime objects to strings for JSON serialization
            serializable_data = self._make_json_serializable(session_data)
            
            with open(file_path, 'w') as f:
                json.dump(serializable_data, f, indent=2)
    
    def _make_json_serializable(self, obj):
        """Convert objects to JSON serializable format"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        else:
            return obj

class TrainingAgent:
    """Wrapper for agents during training"""
    
    def __init__(self, agent_id: str, agent_type: str, framework: TrainingFramework):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.framework = framework
        self.memory = []
        self.learning_rate = 0.1
        self.confidence_threshold = 0.7
    
    async def analyze_deal(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a deal scenario (mock implementation)"""
        
        deal = scenario_data["deal"]
        asking_price = deal["asking_price"]
        market_condition = deal.get("market_condition", {})
        
        # Simple decision logic (would be replaced with actual agent logic)
        base_confidence = 0.6
        
        # Adjust confidence based on market conditions
        if market_condition.get("trend") == "bull":
            base_confidence += 0.1
        elif market_condition.get("trend") == "bear":
            base_confidence -= 0.1
        
        # Decision based on price and confidence
        if asking_price < 500000 and base_confidence > self.confidence_threshold:
            action = "pursue"
            offer_price = asking_price * 0.95
        else:
            action = "pass"
            offer_price = 0
        
        decision = {
            "action": action,
            "offer_price": offer_price,
            "confidence": base_confidence,
            "reasoning": f"Decision based on price threshold and {market_condition.get('trend', 'unknown')} market",
            "risk_assessment": "medium"
        }
        
        # Store in memory for learning
        self.memory.append({
            "scenario": scenario_data,
            "decision": decision,
            "timestamp": datetime.now()
        })
        
        return decision
    
    async def receive_feedback(self, feedback: Dict[str, Any]):
        """Receive and process training feedback"""
        
        # Adjust learning parameters based on feedback
        performance_score = feedback.get("performance_score", 50)
        
        if performance_score > 80:
            # Good performance, maintain current approach
            pass
        elif performance_score > 60:
            # Moderate performance, slight adjustment
            self.confidence_threshold *= 0.98
        else:
            # Poor performance, significant adjustment
            self.confidence_threshold *= 0.95
            self.learning_rate *= 1.1
        
        # Keep confidence threshold in reasonable bounds
        self.confidence_threshold = max(0.3, min(0.9, self.confidence_threshold))
        self.learning_rate = max(0.05, min(0.3, self.learning_rate))
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            "total_decisions": len(self.memory),
            "confidence_threshold": self.confidence_threshold,
            "learning_rate": self.learning_rate,
            "memory_size": len(self.memory)
        }