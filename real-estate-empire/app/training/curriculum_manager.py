import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

class SkillLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class ScenarioCategory(Enum):
    DEAL_ANALYSIS = "deal_analysis"
    NEGOTIATION = "negotiation"
    PORTFOLIO_MANAGEMENT = "portfolio_management"
    MARKET_TIMING = "market_timing"
    RISK_ASSESSMENT = "risk_assessment"
    CLIENT_INTERACTION = "client_interaction"

@dataclass
class LearningObjective:
    """Specific learning objective for training"""
    objective_id: str
    name: str
    description: str
    category: ScenarioCategory
    skill_level: SkillLevel
    prerequisites: List[str]
    success_criteria: Dict[str, float]
    estimated_scenarios: int

@dataclass
class CurriculumModule:
    """A module in the training curriculum"""
    module_id: str
    name: str
    description: str
    learning_objectives: List[LearningObjective]
    estimated_duration: timedelta
    difficulty_progression: str  # "linear", "exponential", "adaptive"
    success_threshold: float

class CurriculumManager:
    """Manages training curriculum and learning progression"""
    
    def __init__(self):
        self.learning_objectives = self._initialize_learning_objectives()
        self.curriculum_modules = self._initialize_curriculum_modules()
        self.agent_progress: Dict[str, Dict] = {}
    
    def _initialize_learning_objectives(self) -> Dict[str, LearningObjective]:
        """Initialize all learning objectives"""
        
        objectives = {}
        
        # Deal Analysis Objectives
        objectives["basic_valuation"] = LearningObjective(
            objective_id="basic_valuation",
            name="Basic Property Valuation",
            description="Learn to accurately estimate property values using comparables",
            category=ScenarioCategory.DEAL_ANALYSIS,
            skill_level=SkillLevel.BEGINNER,
            prerequisites=[],
            success_criteria={"accuracy": 0.8, "consistency": 0.7},
            estimated_scenarios=20
        )
        
        objectives["market_analysis"] = LearningObjective(
            objective_id="market_analysis",
            name="Market Condition Analysis",
            description="Understand and factor in current market conditions",
            category=ScenarioCategory.DEAL_ANALYSIS,
            skill_level=SkillLevel.INTERMEDIATE,
            prerequisites=["basic_valuation"],
            success_criteria={"accuracy": 0.75, "market_awareness": 0.8},
            estimated_scenarios=25
        )
        
        objectives["investment_metrics"] = LearningObjective(
            objective_id="investment_metrics",
            name="Investment Metrics Calculation",
            description="Master cap rates, cash flow, and ROI calculations",
            category=ScenarioCategory.DEAL_ANALYSIS,
            skill_level=SkillLevel.INTERMEDIATE,
            prerequisites=["basic_valuation"],
            success_criteria={"calculation_accuracy": 0.9, "interpretation": 0.8},
            estimated_scenarios=30
        )
        
        # Negotiation Objectives
        objectives["basic_negotiation"] = LearningObjective(
            objective_id="basic_negotiation",
            name="Basic Negotiation Skills",
            description="Learn fundamental negotiation strategies and tactics",
            category=ScenarioCategory.NEGOTIATION,
            skill_level=SkillLevel.BEGINNER,
            prerequisites=[],
            success_criteria={"success_rate": 0.7, "relationship_maintenance": 0.8},
            estimated_scenarios=25
        )
        
        objectives["advanced_negotiation"] = LearningObjective(
            objective_id="advanced_negotiation",
            name="Advanced Negotiation Strategies",
            description="Master complex negotiation scenarios and multi-party deals",
            category=ScenarioCategory.NEGOTIATION,
            skill_level=SkillLevel.ADVANCED,
            prerequisites=["basic_negotiation", "market_analysis"],
            success_criteria={"success_rate": 0.8, "value_creation": 0.75},
            estimated_scenarios=35
        )
        
        # Portfolio Management Objectives
        objectives["portfolio_basics"] = LearningObjective(
            objective_id="portfolio_basics",
            name="Portfolio Management Basics",
            description="Learn portfolio construction and diversification principles",
            category=ScenarioCategory.PORTFOLIO_MANAGEMENT,
            skill_level=SkillLevel.INTERMEDIATE,
            prerequisites=["investment_metrics"],
            success_criteria={"diversification_score": 0.8, "risk_management": 0.75},
            estimated_scenarios=20
        )
        
        objectives["advanced_portfolio"] = LearningObjective(
            objective_id="advanced_portfolio",
            name="Advanced Portfolio Optimization",
            description="Master complex portfolio optimization and rebalancing",
            category=ScenarioCategory.PORTFOLIO_MANAGEMENT,
            skill_level=SkillLevel.ADVANCED,
            prerequisites=["portfolio_basics", "market_analysis"],
            success_criteria={"optimization_score": 0.85, "risk_adjusted_return": 0.8},
            estimated_scenarios=30
        )
        
        # Risk Assessment Objectives
        objectives["risk_identification"] = LearningObjective(
            objective_id="risk_identification",
            name="Risk Identification",
            description="Learn to identify and categorize investment risks",
            category=ScenarioCategory.RISK_ASSESSMENT,
            skill_level=SkillLevel.BEGINNER,
            prerequisites=[],
            success_criteria={"risk_detection": 0.8, "categorization": 0.75},
            estimated_scenarios=15
        )
        
        objectives["risk_mitigation"] = LearningObjective(
            objective_id="risk_mitigation",
            name="Risk Mitigation Strategies",
            description="Develop strategies to mitigate identified risks",
            category=ScenarioCategory.RISK_ASSESSMENT,
            skill_level=SkillLevel.ADVANCED,
            prerequisites=["risk_identification", "portfolio_basics"],
            success_criteria={"mitigation_effectiveness": 0.8, "cost_efficiency": 0.75},
            estimated_scenarios=25
        )
        
        return objectives
    
    def _initialize_curriculum_modules(self) -> Dict[str, CurriculumModule]:
        """Initialize curriculum modules"""
        
        modules = {}
        
        # Foundation Module
        modules["foundation"] = CurriculumModule(
            module_id="foundation",
            name="Real Estate Investment Foundations",
            description="Core skills for real estate investment analysis",
            learning_objectives=[
                self.learning_objectives["basic_valuation"],
                self.learning_objectives["risk_identification"]
            ],
            estimated_duration=timedelta(days=7),
            difficulty_progression="linear",
            success_threshold=0.75
        )
        
        # Intermediate Module
        modules["intermediate"] = CurriculumModule(
            module_id="intermediate",
            name="Market Analysis and Investment Metrics",
            description="Intermediate skills for market analysis and investment evaluation",
            learning_objectives=[
                self.learning_objectives["market_analysis"],
                self.learning_objectives["investment_metrics"],
                self.learning_objectives["basic_negotiation"]
            ],
            estimated_duration=timedelta(days=10),
            difficulty_progression="linear",
            success_threshold=0.8
        )
        
        # Advanced Module
        modules["advanced"] = CurriculumModule(
            module_id="advanced",
            name="Portfolio Management and Advanced Strategies",
            description="Advanced portfolio management and negotiation skills",
            learning_objectives=[
                self.learning_objectives["portfolio_basics"],
                self.learning_objectives["advanced_negotiation"],
                self.learning_objectives["risk_mitigation"]
            ],
            estimated_duration=timedelta(days=14),
            difficulty_progression="adaptive",
            success_threshold=0.85
        )
        
        # Expert Module
        modules["expert"] = CurriculumModule(
            module_id="expert",
            name="Expert-Level Optimization",
            description="Master-level skills for complex scenarios",
            learning_objectives=[
                self.learning_objectives["advanced_portfolio"]
            ],
            estimated_duration=timedelta(days=10),
            difficulty_progression="adaptive",
            success_threshold=0.9
        )
        
        return modules
    
    def create_personalized_curriculum(self, agent_id: str, agent_type: str, 
                                     current_skills: Dict[str, float] = None,
                                     learning_goals: List[str] = None) -> List[CurriculumModule]:
        """Create a personalized curriculum for an agent"""
        
        if current_skills is None:
            current_skills = {}
        
        if learning_goals is None:
            learning_goals = ["deal_analysis", "negotiation", "portfolio_management"]
        
        # Assess current skill level
        skill_assessment = self._assess_skill_level(current_skills)
        
        # Select appropriate modules
        selected_modules = []
        
        # Always start with foundation if skill level is low
        if skill_assessment["overall_level"] == SkillLevel.BEGINNER:
            selected_modules.append(self.curriculum_modules["foundation"])
        
        # Add intermediate module if needed
        if skill_assessment["overall_level"] in [SkillLevel.BEGINNER, SkillLevel.INTERMEDIATE]:
            selected_modules.append(self.curriculum_modules["intermediate"])
        
        # Add advanced module for intermediate+ agents
        if skill_assessment["overall_level"] in [SkillLevel.INTERMEDIATE, SkillLevel.ADVANCED]:
            selected_modules.append(self.curriculum_modules["advanced"])
        
        # Add expert module for advanced agents
        if skill_assessment["overall_level"] == SkillLevel.ADVANCED:
            selected_modules.append(self.curriculum_modules["expert"])
        
        # Customize based on learning goals
        selected_modules = self._customize_for_goals(selected_modules, learning_goals)
        
        # Initialize progress tracking
        self.agent_progress[agent_id] = {
            "current_module": 0,
            "module_progress": {},
            "objective_progress": {},
            "skill_assessment": skill_assessment,
            "learning_goals": learning_goals,
            "start_date": datetime.now()
        }
        
        return selected_modules
    
    def _assess_skill_level(self, current_skills: Dict[str, float]) -> Dict[str, Any]:
        """Assess agent's current skill level"""
        
        if not current_skills:
            return {
                "overall_level": SkillLevel.BEGINNER,
                "category_levels": {},
                "strengths": [],
                "weaknesses": []
            }
        
        # Calculate category averages
        category_scores = {}
        for category in ScenarioCategory:
            category_skills = [score for skill, score in current_skills.items() 
                             if category.value in skill.lower()]
            if category_skills:
                category_scores[category] = np.mean(category_skills)
        
        # Determine overall level
        overall_score = np.mean(list(current_skills.values()))
        
        if overall_score < 0.5:
            overall_level = SkillLevel.BEGINNER
        elif overall_score < 0.7:
            overall_level = SkillLevel.INTERMEDIATE
        elif overall_score < 0.85:
            overall_level = SkillLevel.ADVANCED
        else:
            overall_level = SkillLevel.EXPERT
        
        # Identify strengths and weaknesses
        strengths = [skill for skill, score in current_skills.items() if score > 0.8]
        weaknesses = [skill for skill, score in current_skills.items() if score < 0.6]
        
        return {
            "overall_level": overall_level,
            "overall_score": overall_score,
            "category_levels": category_scores,
            "strengths": strengths,
            "weaknesses": weaknesses
        }
    
    def _customize_for_goals(self, modules: List[CurriculumModule], 
                           learning_goals: List[str]) -> List[CurriculumModule]:
        """Customize modules based on learning goals"""
        
        # For now, return modules as-is
        # In a full implementation, this would filter and reorder modules
        # based on specific learning goals
        
        return modules
    
    def get_next_learning_objective(self, agent_id: str) -> Optional[LearningObjective]:
        """Get the next learning objective for an agent"""
        
        if agent_id not in self.agent_progress:
            return None
        
        progress = self.agent_progress[agent_id]
        
        # Find current module
        current_module_idx = progress["current_module"]
        
        # Get personalized curriculum (would be stored)
        curriculum = self.create_personalized_curriculum(agent_id, "default")
        
        if current_module_idx >= len(curriculum):
            return None  # Curriculum completed
        
        current_module = curriculum[current_module_idx]
        
        # Find next incomplete objective in current module
        for objective in current_module.learning_objectives:
            if objective.objective_id not in progress["objective_progress"]:
                return objective
            
            obj_progress = progress["objective_progress"][objective.objective_id]
            if not obj_progress.get("completed", False):
                return objective
        
        # All objectives in current module completed, move to next module
        progress["current_module"] += 1
        return self.get_next_learning_objective(agent_id)
    
    def update_objective_progress(self, agent_id: str, objective_id: str, 
                                performance_data: Dict[str, Any]):
        """Update progress on a learning objective"""
        
        if agent_id not in self.agent_progress:
            return
        
        progress = self.agent_progress[agent_id]
        
        if objective_id not in progress["objective_progress"]:
            progress["objective_progress"][objective_id] = {
                "attempts": 0,
                "scores": [],
                "completed": False,
                "mastery_level": 0.0
            }
        
        obj_progress = progress["objective_progress"][objective_id]
        obj_progress["attempts"] += 1
        obj_progress["scores"].append(performance_data.get("score", 0))
        
        # Calculate mastery level
        recent_scores = obj_progress["scores"][-5:]  # Last 5 attempts
        obj_progress["mastery_level"] = np.mean(recent_scores) / 100.0
        
        # Check if objective is completed
        objective = self.learning_objectives[objective_id]
        success_criteria = objective.success_criteria
        
        # Simple completion check (would be more sophisticated)
        if obj_progress["mastery_level"] >= success_criteria.get("accuracy", 0.8):
            obj_progress["completed"] = True
    
    def get_curriculum_progress(self, agent_id: str) -> Dict[str, Any]:
        """Get overall curriculum progress for an agent"""
        
        if agent_id not in self.agent_progress:
            return {"error": "Agent not found"}
        
        progress = self.agent_progress[agent_id]
        
        # Calculate completion statistics
        total_objectives = len(self.learning_objectives)
        completed_objectives = sum(1 for obj_progress in progress["objective_progress"].values()
                                 if obj_progress.get("completed", False))
        
        # Calculate average mastery
        mastery_scores = [obj_progress.get("mastery_level", 0) 
                         for obj_progress in progress["objective_progress"].values()]
        average_mastery = np.mean(mastery_scores) if mastery_scores else 0
        
        # Time spent
        time_spent = datetime.now() - progress["start_date"]
        
        return {
            "agent_id": agent_id,
            "overall_progress": completed_objectives / total_objectives * 100,
            "completed_objectives": completed_objectives,
            "total_objectives": total_objectives,
            "average_mastery": average_mastery,
            "current_module": progress["current_module"],
            "time_spent": str(time_spent),
            "learning_goals": progress["learning_goals"],
            "objective_details": progress["objective_progress"]
        }
    
    def recommend_next_scenarios(self, agent_id: str, num_scenarios: int = 5) -> List[Dict[str, Any]]:
        """Recommend next training scenarios based on curriculum"""
        
        next_objective = self.get_next_learning_objective(agent_id)
        
        if not next_objective:
            return []
        
        # Generate scenario recommendations
        recommendations = []
        
        for i in range(num_scenarios):
            # Calculate difficulty based on current progress
            if agent_id in self.agent_progress:
                obj_progress = self.agent_progress[agent_id]["objective_progress"].get(
                    next_objective.objective_id, {}
                )
                attempts = obj_progress.get("attempts", 0)
                mastery = obj_progress.get("mastery_level", 0)
                
                # Adaptive difficulty
                base_difficulty = 0.3 if next_objective.skill_level == SkillLevel.BEGINNER else 0.5
                difficulty_adjustment = min(0.3, attempts * 0.05)  # Increase with attempts
                mastery_adjustment = mastery * 0.2  # Increase with mastery
                
                difficulty = min(1.0, base_difficulty + difficulty_adjustment + mastery_adjustment)
            else:
                difficulty = 0.3
            
            recommendations.append({
                "scenario_type": next_objective.category.value,
                "difficulty": difficulty,
                "learning_objective": next_objective.objective_id,
                "focus_areas": [next_objective.name],
                "success_criteria": next_objective.success_criteria
            })
        
        return recommendations
    
    def generate_curriculum_report(self, agent_id: str) -> Dict[str, Any]:
        """Generate a comprehensive curriculum report"""
        
        progress = self.get_curriculum_progress(agent_id)
        
        if "error" in progress:
            return progress
        
        # Analyze learning patterns
        obj_progress = progress["objective_details"]
        
        # Find strongest and weakest areas
        mastery_by_category = {}
        for obj_id, obj_data in obj_progress.items():
            objective = self.learning_objectives[obj_id]
            category = objective.category.value
            
            if category not in mastery_by_category:
                mastery_by_category[category] = []
            
            mastery_by_category[category].append(obj_data.get("mastery_level", 0))
        
        category_averages = {
            category: np.mean(scores) 
            for category, scores in mastery_by_category.items()
        }
        
        strongest_category = max(category_averages.items(), key=lambda x: x[1]) if category_averages else ("none", 0)
        weakest_category = min(category_averages.items(), key=lambda x: x[1]) if category_averages else ("none", 0)
        
        # Generate recommendations
        recommendations = []
        
        if progress["overall_progress"] < 50:
            recommendations.append("Focus on completing foundation objectives")
        
        if weakest_category[1] < 0.6:
            recommendations.append(f"Additional practice needed in {weakest_category[0]}")
        
        if progress["average_mastery"] > 0.8:
            recommendations.append("Ready for advanced scenarios")
        
        return {
            "progress_summary": progress,
            "category_performance": category_averages,
            "strongest_area": strongest_category[0],
            "weakest_area": weakest_category[0],
            "recommendations": recommendations,
            "next_milestones": self._get_next_milestones(agent_id),
            "estimated_completion": self._estimate_completion_time(agent_id)
        }
    
    def _get_next_milestones(self, agent_id: str) -> List[str]:
        """Get next learning milestones"""
        next_objective = self.get_next_learning_objective(agent_id)
        
        if next_objective:
            return [next_objective.name]
        else:
            return ["Curriculum completed"]
    
    def _estimate_completion_time(self, agent_id: str) -> str:
        """Estimate time to curriculum completion"""
        
        if agent_id not in self.agent_progress:
            return "Unknown"
        
        progress = self.agent_progress[agent_id]
        completed = len([obj for obj in progress["objective_progress"].values() 
                        if obj.get("completed", False)])
        total = len(self.learning_objectives)
        
        if completed == total:
            return "Completed"
        
        # Simple estimation based on current progress rate
        time_spent = datetime.now() - progress["start_date"]
        if completed > 0:
            time_per_objective = time_spent / completed
            remaining_time = time_per_objective * (total - completed)
            return str(remaining_time)
        else:
            return "Unable to estimate"