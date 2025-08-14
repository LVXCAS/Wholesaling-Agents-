#!/usr/bin/env python3
"""
Comprehensive Agent Readiness Validation System
Tests agents against real-world scenarios and benchmarks
"""

import asyncio
import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Tuple
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.market_data_service import MarketDataService
from app.services.property_valuation_service import PropertyValuationService
from app.services.investment_analyzer_service import InvestmentAnalyzerService
from app.simulation.market_simulator import MarketSimulator
from run_agent_training import StandaloneTrainingAgent, calculate_performance_score

class AgentReadinessValidator:
    """Validates agent readiness for production deployment"""
    
    def __init__(self):
        self.market_service = MarketDataService()
        self.valuation_service = PropertyValuationService(self.market_service)
        self.investment_service = InvestmentAnalyzerService(self.market_service, self.valuation_service)
        self.market_simulator = MarketSimulator(self.market_service)
        
        # Validation benchmarks
        self.benchmarks = {
            "minimum_accuracy": 70.0,      # Minimum 70% accuracy
            "consistency_threshold": 15.0,  # Max 15 point std deviation
            "improvement_rate": 5.0,        # Must show 5+ point improvement
            "specialization_score": 60.0,   # 60% specialization minimum
            "real_data_correlation": 0.6,   # 60% correlation with expert analysis
            "edge_case_handling": 50.0,     # 50% success on edge cases
            "production_readiness": 75.0    # Overall readiness score
        }
    
    async def validate_agent_workforce(self, trained_agents: List[Dict]) -> Dict[str, Any]:
        """Comprehensive validation of the entire agent workforce"""
        
        print("🔍 Agent Readiness Validation System")
        print("=" * 60)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        validation_results = {
            "overall_readiness": False,
            "agent_results": {},
            "benchmark_analysis": {},
            "production_recommendations": [],
            "risk_assessment": {},
            "validation_timestamp": datetime.now().isoformat()
        }
        
        print(f"\n📊 Validating {len(trained_agents)} agents against production benchmarks...")
        
        # Test each agent
        for i, agent_data in enumerate(trained_agents, 1):
            agent = agent_data["agent"]
            print(f"\n🤖 Validating Agent {i}/{len(trained_agents)}: {agent_data['description']}")
            
            agent_validation = await self.validate_single_agent(agent, agent_data)
            validation_results["agent_results"][agent.agent_id] = agent_validation
            
            # Show key metrics
            readiness = agent_validation["production_readiness_score"]
            status = "✅ READY" if readiness >= self.benchmarks["production_readiness"] else "❌ NOT READY"
            print(f"   {status} - Readiness Score: {readiness:.1f}/100")
        
        # Overall workforce analysis
        validation_results["benchmark_analysis"] = self.analyze_workforce_benchmarks(validation_results["agent_results"])
        validation_results["production_recommendations"] = self.generate_production_recommendations(validation_results)
        validation_results["risk_assessment"] = self.assess_production_risks(validation_results)
        
        # Determine overall readiness
        ready_agents = sum(1 for result in validation_results["agent_results"].values() 
                          if result["production_readiness_score"] >= self.benchmarks["production_readiness"])
        
        validation_results["overall_readiness"] = ready_agents >= len(trained_agents) * 0.7  # 70% must be ready
        
        # Display results
        self.display_validation_results(validation_results)
        
        return validation_results
    
    async def validate_single_agent(self, agent: StandaloneTrainingAgent, agent_data: Dict) -> Dict[str, Any]:
        """Comprehensive validation of a single agent"""
        
        validation_result = {
            "agent_id": agent.agent_id,
            "specialization": agent.specialization,
            "tests_performed": {},
            "benchmark_scores": {},
            "production_readiness_score": 0.0,
            "readiness_factors": {},
            "recommendations": []
        }
        
        # Test 1: Real Data Accuracy Test
        print("   📈 Testing real data accuracy...")
        real_data_score = await self.test_real_data_accuracy(agent)
        validation_result["tests_performed"]["real_data_accuracy"] = real_data_score
        
        # Test 2: Consistency Test
        print("   🎯 Testing decision consistency...")
        consistency_score = await self.test_decision_consistency(agent)
        validation_result["tests_performed"]["consistency"] = consistency_score
        
        # Test 3: Edge Case Handling
        print("   ⚠️ Testing edge case handling...")
        edge_case_score = await self.test_edge_case_handling(agent)
        validation_result["tests_performed"]["edge_case_handling"] = edge_case_score
        
        # Test 4: Expert Correlation
        print("   👨‍💼 Testing expert correlation...")
        expert_correlation = await self.test_expert_correlation(agent)
        validation_result["tests_performed"]["expert_correlation"] = expert_correlation
        
        # Test 5: Market Condition Adaptation
        print("   🌊 Testing market adaptation...")
        market_adaptation = await self.test_market_adaptation(agent)
        validation_result["tests_performed"]["market_adaptation"] = market_adaptation
        
        # Test 6: Stress Testing
        print("   💪 Stress testing performance...")
        stress_test_score = await self.stress_test_agent(agent)
        validation_result["tests_performed"]["stress_test"] = stress_test_score
        
        # Calculate benchmark scores
        validation_result["benchmark_scores"] = self.calculate_benchmark_scores(
            validation_result["tests_performed"], agent_data["performance"]
        )
        
        # Calculate overall production readiness
        validation_result["production_readiness_score"] = self.calculate_production_readiness(
            validation_result["benchmark_scores"]
        )
        
        # Generate recommendations
        validation_result["recommendations"] = self.generate_agent_recommendations(
            validation_result["benchmark_scores"], agent.specialization
        )
        
        return validation_result
    
    async def test_real_data_accuracy(self, agent: StandaloneTrainingAgent) -> Dict[str, Any]:
        """Test agent accuracy on real market data"""
        
        # Get real properties from different markets
        test_markets = [("Miami", "Florida"), ("Orlando", "Florida"), ("Tampa", "Florida")]
        results = []
        
        for city, state in test_markets:
            try:
                # Generate real market scenarios
                deals = self.market_simulator.generate_batch_scenarios(10, [city])
                
                for deal in deals:
                    scenario_data = {
                        "deal": {
                            "asking_price": deal.asking_price,
                            "market_value": deal.market_value,
                            "property": deal.property_data,
                            "market_condition": {
                                "trend": deal.market_condition.trend,
                                "interest_rate": deal.market_condition.interest_rate
                            }
                        }
                    }
                    
                    # Get agent decision
                    decision = await agent.analyze_deal(scenario_data)
                    
                    # Calculate accuracy against known market value
                    accuracy = self.calculate_decision_accuracy(decision, deal)
                    results.append(accuracy)
                    
            except Exception as e:
                print(f"     ⚠️ Error testing {city}: {e}")
                continue
        
        if not results:
            return {"average_accuracy": 0.0, "sample_size": 0, "error": "No valid test data"}
        
        return {
            "average_accuracy": np.mean(results),
            "accuracy_std": np.std(results),
            "sample_size": len(results),
            "min_accuracy": min(results),
            "max_accuracy": max(results)
        }
    
    async def test_decision_consistency(self, agent: StandaloneTrainingAgent) -> Dict[str, Any]:
        """Test agent consistency across similar scenarios"""
        
        # Create similar scenarios with slight variations
        base_deal = self.market_simulator.generate_deal_scenario("Miami", "Florida")
        
        similar_scenarios = []
        decisions = []
        
        # Generate 20 similar scenarios
        for i in range(20):
            # Add small variations to the base deal
            variation_factor = 1.0 + np.random.uniform(-0.05, 0.05)  # ±5% variation
            
            scenario_data = {
                "deal": {
                    "asking_price": base_deal.asking_price * variation_factor,
                    "market_value": base_deal.market_value * variation_factor,
                    "property": base_deal.property_data,
                    "market_condition": {
                        "trend": base_deal.market_condition.trend,
                        "interest_rate": base_deal.market_condition.interest_rate
                    }
                }
            }
            
            decision = await agent.analyze_deal(scenario_data)
            decisions.append(decision)
            similar_scenarios.append(scenario_data)
        
        # Analyze consistency
        actions = [d["action"] for d in decisions]
        confidences = [d["confidence"] for d in decisions]
        
        # Calculate consistency metrics
        action_consistency = len(set(actions)) / len(actions)  # Lower is more consistent
        confidence_std = np.std(confidences)
        
        consistency_score = max(0, 100 - (action_consistency * 50 + confidence_std * 100))
        
        return {
            "consistency_score": consistency_score,
            "action_consistency": 1 - action_consistency,  # Higher is better
            "confidence_std": confidence_std,
            "sample_size": len(decisions)
        }
    
    async def test_edge_case_handling(self, agent: StandaloneTrainingAgent) -> Dict[str, Any]:
        """Test agent performance on edge cases"""
        
        edge_cases = []
        
        # Create various edge case scenarios
        base_deal = self.market_simulator.generate_deal_scenario()
        
        # Edge Case 1: Extremely overpriced property
        edge_case_1 = {
            "deal": {
                "asking_price": base_deal.market_value * 2.0,  # 100% overpriced
                "market_value": base_deal.market_value,
                "property": base_deal.property_data,
                "market_condition": {"trend": "stable", "interest_rate": 6.0}
            },
            "expected_action": "pass"
        }
        edge_cases.append(edge_case_1)
        
        # Edge Case 2: Extremely underpriced property
        edge_case_2 = {
            "deal": {
                "asking_price": base_deal.market_value * 0.6,  # 40% underpriced
                "market_value": base_deal.market_value,
                "property": base_deal.property_data,
                "market_condition": {"trend": "bull", "interest_rate": 5.0}
            },
            "expected_action": "pursue"
        }
        edge_cases.append(edge_case_2)
        
        # Edge Case 3: Market crash scenario
        edge_case_3 = {
            "deal": {
                "asking_price": base_deal.asking_price,
                "market_value": base_deal.market_value * 0.8,  # Market declined
                "property": base_deal.property_data,
                "market_condition": {"trend": "bear", "interest_rate": 8.0}
            },
            "expected_action": "pass"
        }
        edge_cases.append(edge_case_3)
        
        # Test each edge case
        correct_decisions = 0
        total_cases = len(edge_cases)
        
        for edge_case in edge_cases:
            decision = await agent.analyze_deal(edge_case)
            if decision["action"] == edge_case["expected_action"]:
                correct_decisions += 1
        
        edge_case_score = (correct_decisions / total_cases) * 100
        
        return {
            "edge_case_score": edge_case_score,
            "correct_decisions": correct_decisions,
            "total_cases": total_cases,
            "success_rate": correct_decisions / total_cases
        }
    
    async def test_expert_correlation(self, agent: StandaloneTrainingAgent) -> Dict[str, Any]:
        """Test correlation with expert investment analysis"""
        
        correlations = []
        
        # Test against 20 properties
        for _ in range(20):
            deal = self.market_simulator.generate_deal_scenario()
            
            # Get agent decision
            scenario_data = {
                "deal": {
                    "asking_price": deal.asking_price,
                    "market_value": deal.market_value,
                    "property": deal.property_data,
                    "market_condition": {
                        "trend": deal.market_condition.trend,
                        "interest_rate": deal.market_condition.interest_rate
                    }
                }
            }
            
            agent_decision = await agent.analyze_deal(scenario_data)
            
            # Get expert analysis (our investment analyzer)
            try:
                property_data = deal.property_data.copy()
                property_data['asking_price'] = deal.asking_price
                property_data['estimated_rent'] = deal.asking_price * 0.01
                
                expert_analysis = self.investment_service.analyze_investment_opportunity(property_data)
                
                # Compare decisions
                agent_score = 100 if agent_decision["action"] == "pursue" else 0
                expert_score = expert_analysis.investment_metrics.investment_score
                
                # Calculate correlation
                correlation = 1 - abs(agent_score - expert_score) / 100
                correlations.append(correlation)
                
            except Exception as e:
                continue
        
        if not correlations:
            return {"correlation": 0.0, "sample_size": 0}
        
        return {
            "correlation": np.mean(correlations),
            "correlation_std": np.std(correlations),
            "sample_size": len(correlations)
        }
    
    async def test_market_adaptation(self, agent: StandaloneTrainingAgent) -> Dict[str, Any]:
        """Test agent adaptation to different market conditions"""
        
        market_conditions = [
            {"trend": "bull", "interest_rate": 4.0},
            {"trend": "bear", "interest_rate": 8.0},
            {"trend": "stable", "interest_rate": 6.0}
        ]
        
        adaptation_scores = []
        
        for condition in market_conditions:
            # Test 10 scenarios in each market condition
            condition_scores = []
            
            for _ in range(10):
                deal = self.market_simulator.generate_deal_scenario()
                
                scenario_data = {
                    "deal": {
                        "asking_price": deal.asking_price,
                        "market_value": deal.market_value,
                        "property": deal.property_data,
                        "market_condition": condition
                    }
                }
                
                decision = await agent.analyze_deal(scenario_data)
                
                # Score based on market-appropriate behavior
                score = self.score_market_appropriate_behavior(decision, condition, deal)
                condition_scores.append(score)
            
            adaptation_scores.append(np.mean(condition_scores))
        
        return {
            "adaptation_score": np.mean(adaptation_scores),
            "bull_market_score": adaptation_scores[0],
            "bear_market_score": adaptation_scores[1],
            "stable_market_score": adaptation_scores[2],
            "adaptation_consistency": 100 - np.std(adaptation_scores)
        }
    
    async def stress_test_agent(self, agent: StandaloneTrainingAgent) -> Dict[str, Any]:
        """Stress test agent with high volume and difficult scenarios"""
        
        print("     Processing 100 high-difficulty scenarios...")
        
        stress_results = []
        processing_times = []
        
        for i in range(100):
            start_time = datetime.now()
            
            # Generate high-difficulty scenario
            deal = self.market_simulator.generate_deal_scenario()
            
            # Make it more challenging
            difficulty_multiplier = np.random.uniform(1.5, 2.0)
            
            scenario_data = {
                "deal": {
                    "asking_price": deal.asking_price * difficulty_multiplier,
                    "market_value": deal.market_value,
                    "property": deal.property_data,
                    "market_condition": {
                        "trend": np.random.choice(["bull", "bear", "stable"]),
                        "interest_rate": np.random.uniform(3.0, 9.0)
                    }
                },
                "difficulty": 0.9  # High difficulty
            }
            
            try:
                decision = await agent.analyze_deal(scenario_data)
                score = calculate_performance_score(decision, deal, 0.9)
                stress_results.append(score)
                
                processing_time = (datetime.now() - start_time).total_seconds()
                processing_times.append(processing_time)
                
            except Exception as e:
                stress_results.append(0)  # Failed scenario
                processing_times.append(10.0)  # Penalty time
        
        return {
            "stress_test_score": np.mean(stress_results),
            "success_rate": len([s for s in stress_results if s > 0]) / len(stress_results),
            "average_processing_time": np.mean(processing_times),
            "max_processing_time": max(processing_times),
            "scenarios_processed": len(stress_results)
        }
    
    def calculate_decision_accuracy(self, decision: Dict, deal) -> float:
        """Calculate accuracy of agent decision against known market data"""
        
        equity_potential = (deal.market_value - deal.asking_price) / deal.asking_price
        action = decision["action"]
        
        # Good decision if:
        # - Pursues deals with positive equity (>2%)
        # - Passes on deals with negative equity (<-2%)
        # - Shows appropriate confidence
        
        if equity_potential > 0.02:  # Good deal
            accuracy = 100 if action == "pursue" else 20
        elif equity_potential < -0.02:  # Bad deal
            accuracy = 100 if action == "pass" else 10
        else:  # Marginal deal
            accuracy = 70  # Either decision is reasonable
        
        # Adjust for confidence appropriateness
        confidence = decision.get("confidence", 0.5)
        expected_confidence = 0.8 if abs(equity_potential) > 0.05 else 0.6
        confidence_penalty = abs(confidence - expected_confidence) * 20
        
        return max(0, accuracy - confidence_penalty)
    
    def score_market_appropriate_behavior(self, decision: Dict, market_condition: Dict, deal) -> float:
        """Score decision appropriateness for market conditions"""
        
        base_score = 50
        trend = market_condition["trend"]
        interest_rate = market_condition["interest_rate"]
        
        # Market-appropriate behavior scoring
        if trend == "bull":
            # Should be more aggressive in bull markets
            if decision["action"] == "pursue":
                base_score += 30
            confidence_bonus = (decision["confidence"] - 0.6) * 20
        elif trend == "bear":
            # Should be more conservative in bear markets
            if decision["action"] == "pass":
                base_score += 30
            confidence_penalty = (decision["confidence"] - 0.4) * 10
            base_score -= max(0, confidence_penalty)
        else:  # stable
            # Balanced approach
            base_score += 20
        
        # Interest rate sensitivity
        if interest_rate > 7.0:  # High rates
            if decision["action"] == "pass":
                base_score += 10
        elif interest_rate < 5.0:  # Low rates
            if decision["action"] == "pursue":
                base_score += 10
        
        return max(0, min(100, base_score))
    
    def calculate_benchmark_scores(self, test_results: Dict, training_performance: Dict) -> Dict[str, float]:
        """Calculate scores against production benchmarks"""
        
        benchmark_scores = {}
        
        # Accuracy benchmark
        real_data_accuracy = test_results.get("real_data_accuracy", {}).get("average_accuracy", 0)
        benchmark_scores["accuracy"] = min(100, (real_data_accuracy / self.benchmarks["minimum_accuracy"]) * 100)
        
        # Consistency benchmark
        consistency = test_results.get("consistency", {}).get("consistency_score", 0)
        benchmark_scores["consistency"] = consistency
        
        # Improvement benchmark
        improvement = training_performance.get("improvement_rate", 0)
        benchmark_scores["improvement"] = min(100, max(0, (improvement / self.benchmarks["improvement_rate"]) * 100))
        
        # Specialization benchmark
        specialization = training_performance.get("specialization_score", 0)
        benchmark_scores["specialization"] = min(100, (specialization / self.benchmarks["specialization_score"]) * 100)
        
        # Expert correlation benchmark
        correlation = test_results.get("expert_correlation", {}).get("correlation", 0)
        benchmark_scores["expert_correlation"] = (correlation / self.benchmarks["real_data_correlation"]) * 100
        
        # Edge case handling benchmark
        edge_case_score = test_results.get("edge_case_handling", {}).get("edge_case_score", 0)
        benchmark_scores["edge_case_handling"] = edge_case_score
        
        # Stress test benchmark
        stress_score = test_results.get("stress_test", {}).get("stress_test_score", 0)
        benchmark_scores["stress_test"] = stress_score
        
        return benchmark_scores
    
    def calculate_production_readiness(self, benchmark_scores: Dict[str, float]) -> float:
        """Calculate overall production readiness score"""
        
        # Weighted scoring
        weights = {
            "accuracy": 0.25,
            "consistency": 0.20,
            "expert_correlation": 0.15,
            "edge_case_handling": 0.15,
            "stress_test": 0.10,
            "specialization": 0.10,
            "improvement": 0.05
        }
        
        weighted_score = sum(
            benchmark_scores.get(metric, 0) * weight 
            for metric, weight in weights.items()
        )
        
        return min(100, weighted_score)
    
    def generate_agent_recommendations(self, benchmark_scores: Dict[str, float], specialization: str) -> List[str]:
        """Generate specific recommendations for agent improvement"""
        
        recommendations = []
        
        if benchmark_scores.get("accuracy", 0) < 70:
            recommendations.append("Requires additional training on real market data")
        
        if benchmark_scores.get("consistency", 0) < 70:
            recommendations.append("Needs consistency improvement - consider decision framework refinement")
        
        if benchmark_scores.get("expert_correlation", 0) < 60:
            recommendations.append("Low correlation with expert analysis - review decision logic")
        
        if benchmark_scores.get("edge_case_handling", 0) < 50:
            recommendations.append("Poor edge case handling - add specialized training scenarios")
        
        if benchmark_scores.get("stress_test", 0) < 60:
            recommendations.append("Performance degrades under stress - optimize processing efficiency")
        
        # Specialization-specific recommendations
        if specialization == "deal_analyzer" and benchmark_scores.get("accuracy", 0) < 80:
            recommendations.append("Deal analysis accuracy below expectations - focus on valuation training")
        
        if not recommendations:
            recommendations.append("Agent meets production standards - ready for deployment")
        
        return recommendations
    
    def analyze_workforce_benchmarks(self, agent_results: Dict) -> Dict[str, Any]:
        """Analyze benchmark performance across the workforce"""
        
        all_scores = {}
        
        for agent_result in agent_results.values():
            benchmark_scores = agent_result.get("benchmark_scores", {})
            for metric, score in benchmark_scores.items():
                if metric not in all_scores:
                    all_scores[metric] = []
                all_scores[metric].append(score)
        
        benchmark_analysis = {}
        
        for metric, scores in all_scores.items():
            benchmark_analysis[metric] = {
                "average": np.mean(scores),
                "min": min(scores),
                "max": max(scores),
                "std": np.std(scores),
                "passing_agents": len([s for s in scores if s >= 70])
            }
        
        return benchmark_analysis
    
    def generate_production_recommendations(self, validation_results: Dict) -> List[str]:
        """Generate production deployment recommendations"""
        
        recommendations = []
        
        ready_agents = sum(1 for result in validation_results["agent_results"].values() 
                          if result["production_readiness_score"] >= self.benchmarks["production_readiness"])
        
        total_agents = len(validation_results["agent_results"])
        
        if ready_agents == total_agents:
            recommendations.append("✅ All agents ready for production deployment")
        elif ready_agents >= total_agents * 0.7:
            recommendations.append(f"⚠️ {ready_agents}/{total_agents} agents ready - deploy ready agents, continue training others")
        else:
            recommendations.append(f"❌ Only {ready_agents}/{total_agents} agents ready - additional training required")
        
        # Specific recommendations based on benchmark analysis
        benchmark_analysis = validation_results.get("benchmark_analysis", {})
        
        for metric, analysis in benchmark_analysis.items():
            if analysis["average"] < 70:
                recommendations.append(f"Workforce weakness in {metric} - average {analysis['average']:.1f}/100")
        
        return recommendations
    
    def assess_production_risks(self, validation_results: Dict) -> Dict[str, Any]:
        """Assess risks of production deployment"""
        
        risks = {
            "high_risk_factors": [],
            "medium_risk_factors": [],
            "low_risk_factors": [],
            "overall_risk_level": "LOW"
        }
        
        # Analyze risk factors
        benchmark_analysis = validation_results.get("benchmark_analysis", {})
        
        for metric, analysis in benchmark_analysis.items():
            avg_score = analysis["average"]
            std_score = analysis["std"]
            
            if avg_score < 50:
                risks["high_risk_factors"].append(f"Poor {metric} performance ({avg_score:.1f}/100)")
            elif avg_score < 70:
                risks["medium_risk_factors"].append(f"Below-average {metric} performance ({avg_score:.1f}/100)")
            
            if std_score > 20:
                risks["medium_risk_factors"].append(f"High {metric} variability ({std_score:.1f} std)")
        
        # Determine overall risk level
        if risks["high_risk_factors"]:
            risks["overall_risk_level"] = "HIGH"
        elif len(risks["medium_risk_factors"]) > 3:
            risks["overall_risk_level"] = "MEDIUM"
        else:
            risks["overall_risk_level"] = "LOW"
        
        return risks
    
    def display_validation_results(self, validation_results: Dict):
        """Display comprehensive validation results"""
        
        print(f"\n🎯 AGENT READINESS VALIDATION RESULTS")
        print("=" * 60)
        
        # Overall readiness
        overall_ready = validation_results["overall_readiness"]
        status = "✅ WORKFORCE READY" if overall_ready else "❌ WORKFORCE NOT READY"
        print(f"\n{status} for Production Deployment")
        
        # Individual agent results
        print(f"\n📊 Individual Agent Results:")
        
        for agent_id, result in validation_results["agent_results"].items():
            readiness = result["production_readiness_score"]
            specialization = result["specialization"]
            
            status_icon = "✅" if readiness >= 75 else "⚠️" if readiness >= 60 else "❌"
            print(f"\n   {status_icon} {specialization.replace('_', ' ').title()}")
            print(f"      Production Readiness: {readiness:.1f}/100")
            
            # Show key test results
            tests = result["tests_performed"]
            if "real_data_accuracy" in tests:
                accuracy = tests["real_data_accuracy"].get("average_accuracy", 0)
                print(f"      Real Data Accuracy: {accuracy:.1f}%")
            
            if "consistency" in tests:
                consistency = tests["consistency"].get("consistency_score", 0)
                print(f"      Decision Consistency: {consistency:.1f}/100")
            
            if "expert_correlation" in tests:
                correlation = tests["expert_correlation"].get("correlation", 0)
                print(f"      Expert Correlation: {correlation:.2f}")
            
            # Show top recommendations
            recommendations = result.get("recommendations", [])
            if recommendations:
                print(f"      Key Recommendation: {recommendations[0]}")
        
        # Benchmark analysis
        print(f"\n📈 Workforce Benchmark Analysis:")
        benchmark_analysis = validation_results.get("benchmark_analysis", {})
        
        for metric, analysis in benchmark_analysis.items():
            avg_score = analysis["average"]
            passing = analysis["passing_agents"]
            total = len(validation_results["agent_results"])
            
            status_icon = "✅" if avg_score >= 70 else "⚠️" if avg_score >= 50 else "❌"
            print(f"   {status_icon} {metric.replace('_', ' ').title()}: {avg_score:.1f}/100 ({passing}/{total} agents passing)")
        
        # Production recommendations
        print(f"\n💡 Production Recommendations:")
        for rec in validation_results.get("production_recommendations", []):
            print(f"   • {rec}")
        
        # Risk assessment
        print(f"\n⚠️ Risk Assessment:")
        risks = validation_results.get("risk_assessment", {})
        risk_level = risks.get("overall_risk_level", "UNKNOWN")
        
        risk_colors = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}
        print(f"   Overall Risk Level: {risk_colors.get(risk_level, '⚪')} {risk_level}")
        
        if risks.get("high_risk_factors"):
            print(f"   High Risk Factors:")
            for factor in risks["high_risk_factors"]:
                print(f"     🔴 {factor}")
        
        if risks.get("medium_risk_factors"):
            print(f"   Medium Risk Factors:")
            for factor in risks["medium_risk_factors"][:3]:  # Show top 3
                print(f"     🟡 {factor}")
        
        print(f"\n🎉 Validation Complete!")
        print(f"🕐 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    """Main validation function"""
    
    # First, train agents (reuse from previous training)
    print("🏠 Real Estate Empire - Agent Readiness Validation")
    print("=" * 60)
    
    # Import and run agent training
    from run_agent_training import train_agent_workforce
    
    print("1. Training agent workforce...")
    trained_agents = await train_agent_workforce()
    
    if not trained_agents:
        print("❌ No agents available for validation")
        return
    
    print(f"\n2. Validating {len(trained_agents)} trained agents...")
    
    # Initialize validator and run validation
    validator = AgentReadinessValidator()
    validation_results = await validator.validate_agent_workforce(trained_agents)
    
    # Save validation results
    with open("agent_validation_results.json", "w") as f:
        json.dump(validation_results, f, indent=2, default=str)
    
    print(f"\n💾 Validation results saved to: agent_validation_results.json")
    
    return validation_results

if __name__ == "__main__":
    asyncio.run(main())