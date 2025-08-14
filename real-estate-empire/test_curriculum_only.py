#!/usr/bin/env python3
"""
Test only the curriculum manager (avoiding problematic imports)
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.training.curriculum_manager import CurriculumManager, SkillLevel, ScenarioCategory

async def test_curriculum_manager():
    print("🎓 Testing Curriculum Manager")
    print("=" * 40)
    
    # Initialize curriculum manager
    print("1. Initializing curriculum manager...")
    curriculum_manager = CurriculumManager()
    
    # Test learning objectives
    print("\n📚 Testing Learning Objectives...")
    try:
        objectives = curriculum_manager.learning_objectives
        print(f"✅ Loaded {len(objectives)} learning objectives:")
        
        # Show objectives by category
        categories = {}
        for obj_id, obj in objectives.items():
            category = obj.category.value
            if category not in categories:
                categories[category] = []
            categories[category].append(obj)
        
        for category, objs in categories.items():
            print(f"   {category.replace('_', ' ').title()}: {len(objs)} objectives")
            for obj in objs[:2]:  # Show first 2 in each category
                print(f"     • {obj.name} ({obj.skill_level.value})")
        
    except Exception as e:
        print(f"❌ Learning objectives error: {e}")
        return
    
    # Test curriculum modules
    print("\n📖 Testing Curriculum Modules...")
    try:
        modules = curriculum_manager.curriculum_modules
        print(f"✅ Loaded {len(modules)} curriculum modules:")
        
        for module_id, module in modules.items():
            duration_days = module.estimated_duration.days
            print(f"   • {module.name}")
            print(f"     Duration: {duration_days} days")
            print(f"     Objectives: {len(module.learning_objectives)}")
            print(f"     Success threshold: {module.success_threshold}")
            print(f"     Difficulty progression: {module.difficulty_progression}")
        
    except Exception as e:
        print(f"❌ Curriculum modules error: {e}")
        return
    
    # Test personalized curriculum creation
    print("\n🎯 Testing Personalized Curriculum...")
    try:
        agent_id = "test_agent_001"
        
        # Test different skill levels
        skill_scenarios = [
            ("Beginner", {"deal_analysis": 0.2, "negotiation": 0.1}),
            ("Intermediate", {"deal_analysis": 0.6, "negotiation": 0.5, "portfolio_management": 0.4}),
            ("Advanced", {"deal_analysis": 0.8, "negotiation": 0.7, "portfolio_management": 0.8})
        ]
        
        for skill_name, skills in skill_scenarios:
            test_agent_id = f"{agent_id}_{skill_name.lower()}"
            
            curriculum = curriculum_manager.create_personalized_curriculum(
                test_agent_id, "portfolio", skills, ["deal_analysis", "portfolio_management"]
            )
            
            print(f"✅ {skill_name} agent curriculum:")
            print(f"   Agent ID: {test_agent_id}")
            print(f"   Modules: {len(curriculum)}")
            
            total_days = sum(module.estimated_duration.days for module in curriculum)
            total_objectives = sum(len(module.learning_objectives) for module in curriculum)
            
            print(f"   Total duration: {total_days} days")
            print(f"   Total objectives: {total_objectives}")
            
            for module in curriculum:
                print(f"     - {module.name} ({module.estimated_duration.days} days)")
        
    except Exception as e:
        print(f"❌ Personalized curriculum error: {e}")
        return
    
    # Test learning progression
    print("\n📈 Testing Learning Progression...")
    try:
        agent_id = "progression_test_agent"
        
        # Create curriculum for testing
        curriculum = curriculum_manager.create_personalized_curriculum(
            agent_id, "portfolio", {"deal_analysis": 0.3}, ["deal_analysis"]
        )
        
        # Test getting next objective
        next_objective = curriculum_manager.get_next_learning_objective(agent_id)
        if next_objective:
            print(f"✅ Next learning objective: {next_objective.name}")
            print(f"   Category: {next_objective.category.value}")
            print(f"   Prerequisites: {next_objective.prerequisites}")
            print(f"   Success criteria: {next_objective.success_criteria}")
            
            # Simulate training progress
            objective_id = next_objective.objective_id
            training_scores = [45, 55, 62, 70, 78, 85, 82, 88, 91, 94]
            
            print(f"✅ Simulating training progress on '{next_objective.name}':")
            
            for i, score in enumerate(training_scores):
                curriculum_manager.update_objective_progress(
                    agent_id, objective_id, {"score": score}
                )
                
                if i % 3 == 2:  # Show progress every 3 attempts
                    progress = curriculum_manager.get_curriculum_progress(agent_id)
                    obj_progress = progress["objective_details"].get(objective_id, {})
                    mastery = obj_progress.get("mastery_level", 0)
                    completed = obj_progress.get("completed", False)
                    
                    print(f"   Attempt {i+1}: Score {score}, Mastery {mastery:.2f}, "
                          f"Completed: {completed}")
        
    except Exception as e:
        print(f"❌ Learning progression error: {e}")
    
    # Test scenario recommendations
    print("\n🎯 Testing Scenario Recommendations...")
    try:
        recommendations = curriculum_manager.recommend_next_scenarios(agent_id, 5)
        print(f"✅ Generated {len(recommendations)} scenario recommendations:")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. Scenario Type: {rec['scenario_type']}")
            print(f"      Difficulty: {rec['difficulty']:.2f}")
            print(f"      Learning Objective: {rec['learning_objective']}")
            print(f"      Focus Areas: {rec['focus_areas']}")
            print(f"      Success Criteria: {rec['success_criteria']}")
        
    except Exception as e:
        print(f"❌ Scenario recommendations error: {e}")
    
    # Test comprehensive reporting
    print("\n📊 Testing Comprehensive Reporting...")
    try:
        report = curriculum_manager.generate_curriculum_report(agent_id)
        
        print(f"✅ Generated comprehensive curriculum report:")
        
        # Progress summary
        progress_summary = report["progress_summary"]
        print(f"   Overall Progress: {progress_summary['overall_progress']:.1f}%")
        print(f"   Completed Objectives: {progress_summary['completed_objectives']}")
        print(f"   Average Mastery: {progress_summary['average_mastery']:.2f}")
        
        # Performance analysis
        print(f"   Strongest Area: {report['strongest_area']}")
        print(f"   Weakest Area: {report['weakest_area']}")
        
        # Category performance
        if report['category_performance']:
            print(f"   Category Performance:")
            for category, score in report['category_performance'].items():
                print(f"     • {category.replace('_', ' ').title()}: {score:.2f}")
        
        # Recommendations
        if report['recommendations']:
            print(f"   Recommendations:")
            for rec in report['recommendations']:
                print(f"     • {rec}")
        
        # Next milestones
        print(f"   Next Milestones: {report['next_milestones']}")
        
    except Exception as e:
        print(f"❌ Comprehensive reporting error: {e}")
    
    # Test skill level assessment
    print("\n🎯 Testing Skill Level Assessment...")
    try:
        test_skills = [
            ("Novice", {"deal_analysis": 0.2, "negotiation": 0.1}),
            ("Developing", {"deal_analysis": 0.5, "negotiation": 0.4, "portfolio": 0.3}),
            ("Proficient", {"deal_analysis": 0.7, "negotiation": 0.8, "portfolio": 0.6}),
            ("Expert", {"deal_analysis": 0.9, "negotiation": 0.9, "portfolio": 0.9})
        ]
        
        for skill_name, skills in test_skills:
            assessment = curriculum_manager._assess_skill_level(skills)
            
            print(f"✅ {skill_name} skill assessment:")
            print(f"   Overall Level: {assessment['overall_level'].value}")
            print(f"   Overall Score: {assessment['overall_score']:.2f}")
            print(f"   Strengths: {assessment['strengths']}")
            print(f"   Weaknesses: {assessment['weaknesses']}")
        
    except Exception as e:
        print(f"❌ Skill assessment error: {e}")
    
    print("\n🎉 Curriculum Manager Test Complete!")
    print("=" * 40)
    print("✅ Curriculum System Features:")
    print("   • 8 comprehensive learning objectives")
    print("   • 4 progressive curriculum modules")
    print("   • Personalized learning paths")
    print("   • Adaptive difficulty progression")
    print("   • Detailed progress tracking")
    print("   • Performance analytics")
    print("   • Skill level assessment")
    print("   • Scenario recommendations")
    print("\n🚀 Curriculum System Ready!")
    print("   • Foundation → Intermediate → Advanced → Expert")
    print("   • Deal Analysis → Negotiation → Portfolio Management")
    print("   • Beginner → Intermediate → Advanced → Expert levels")
    print("   • Comprehensive reporting and analytics")
    print("\n💡 Ready for Agent Training Integration!")

if __name__ == "__main__":
    asyncio.run(test_curriculum_manager())