#!/usr/bin/env python3
"""
Rapid Agent Improvement System using Real Estate Dataset
Leverages 2.2M+ property records to create expert-level training data
"""

import asyncio
import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Tuple
import sqlite3
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.market_data_service import MarketDataService
from app.services.property_valuation_service import PropertyValuationService
from app.services.investment_analyzer_service import InvestmentAnalyzerService
from app.simulation.market_simulator import MarketSimulator
from run_agent_training import StandaloneTrainingAgent

class ExpertDataGenerator:
    """Generate expert-level training data from real estate dataset"""
    
    def __init__(self):
        self.market_service = MarketDataService()
        self.valuation_service = PropertyValuationService(self.market_service)
        self.investment_service = InvestmentAnalyzerService(self.market_service, self.valuation_service)
        
        # Expert decision criteria (derived from successful real estate patterns)
        self.expert_criteria = {
            "excellent_deal": {
                "price_to_market_ratio": 0.85,  # 15% below market
                "price_per_sqft_percentile": 25,  # Bottom 25% of market
                "cap_rate_min": 8.0,
                "cash_flow_min": 200
            },
            "good_deal": {
                "price_to_market_ratio": 0.92,  # 8% below market
                "price_per_sqft_percentile": 40,
                "cap_rate_min": 6.0,
                "cash_flow_min": 100
            },
            "marginal_deal": {
                "price_to_market_ratio": 0.98,  # 2% below market
                "price_per_sqft_percentile": 60,
                "cap_rate_min": 4.0,
                "cash_flow_min": 0
            }
        }
    
    async def generate_expert_training_dataset(self, sample_size: int = 10000) -> List[Dict[str, Any]]:
        """Generate expert-labeled training data from real estate dataset"""
        
        print(f"🎓 Generating Expert Training Dataset from {sample_size:,} properties...")
        
        # Load real estate data
        conn = sqlite3.connect(self.market_service.db_path)
        
        # Sample diverse properties across different markets and price ranges
        query = """
        SELECT * FROM properties 
        WHERE price IS NOT NULL 
        AND house_size IS NOT NULL 
        AND bed IS NOT NULL 
        AND bath IS NOT NULL
        AND price > 50000 
        AND price < 2000000
        AND house_size > 500
        ORDER BY RANDOM() 
        LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=[sample_size])
        conn.close()
        
        print(f"✅ Loaded {len(df):,} properties for expert analysis")
        
        expert_dataset = []
        
        # Process properties in batches for efficiency
        batch_size = 100
        total_batches = len(df) // batch_size + 1
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, len(df))
            batch_df = df.iloc[start_idx:end_idx]
            
            if batch_idx % 10 == 0:
                print(f"   Processing batch {batch_idx + 1}/{total_batches}...")
            
            for _, property_row in batch_df.iterrows():
                try:
                    expert_decision = await self._generate_expert_decision(property_row)
                    if expert_decision:
                        expert_dataset.append(expert_decision)
                except Exception as e:
                    continue  # Skip problematic properties
        
        print(f"✅ Generated {len(expert_dataset):,} expert-labeled training examples")
        
        # Save dataset for reuse
        with open("expert_training_dataset.json", "w") as f:
            json.dump(expert_dataset, f, indent=2, default=str)
        
        return expert_dataset
    
    async def _generate_expert_decision(self, property_row: pd.Series) -> Dict[str, Any]:
        """Generate expert decision for a single property"""
        
        # Extract property data
        property_data = {
            'city': property_row['city'],
            'state': property_row['state'],
            'bedrooms': property_row['bed'],
            'bathrooms': property_row['bath'],
            'house_size': property_row['house_size'],
            'acre_lot': property_row.get('acre_lot', 0),
            'asking_price': property_row['price'],
            'estimated_rent': property_row['price'] * 0.01  # 1% rule estimate
        }
        
        # Get market analysis
        try:
            market_stats = self.market_service.get_market_stats(
                property_data['city'], property_data['state']
            )
            
            if not market_stats:
                return None
            
            # Calculate key metrics
            price_per_sqft = property_data['asking_price'] / property_data['house_size']
            market_price_per_sqft = market_stats.avg_price_per_sqft
            
            # Price analysis
            price_to_market_ratio = property_data['asking_price'] / market_stats.avg_price
            price_per_sqft_ratio = price_per_sqft / market_price_per_sqft
            
            # Investment analysis
            investment_analysis = self.investment_service.analyze_investment_opportunity(property_data)
            
            # Generate expert decision based on multiple criteria
            expert_decision = self._make_expert_decision(
                property_data, market_stats, investment_analysis, 
                price_to_market_ratio, price_per_sqft_ratio
            )
            
            return {
                "property_data": property_data,
                "market_context": {
                    "avg_price": market_stats.avg_price,
                    "avg_price_per_sqft": market_stats.avg_price_per_sqft,
                    "total_listings": market_stats.total_listings,
                    "price_to_market_ratio": price_to_market_ratio,
                    "price_per_sqft_ratio": price_per_sqft_ratio
                },
                "investment_metrics": {
                    "investment_score": investment_analysis.investment_metrics.investment_score,
                    "cap_rate": investment_analysis.investment_metrics.cap_rate,
                    "monthly_cash_flow": investment_analysis.investment_metrics.monthly_cash_flow,
                    "risk_level": investment_analysis.investment_metrics.risk_level
                },
                "expert_decision": expert_decision,
                "reasoning": expert_decision["reasoning"]
            }
            
        except Exception as e:
            return None
    
    def _make_expert_decision(self, property_data: Dict, market_stats, investment_analysis, 
                            price_to_market_ratio: float, price_per_sqft_ratio: float) -> Dict[str, Any]:
        """Make expert-level investment decision based on comprehensive analysis"""
        
        # Initialize decision
        decision = {
            "action": "pass",
            "confidence": 0.5,
            "offer_price": 0,
            "deal_quality": "poor",
            "reasoning": "",
            "key_factors": []
        }
        
        # Scoring system
        score = 0
        factors = []
        
        # Factor 1: Price relative to market (30% weight)
        if price_to_market_ratio <= 0.85:
            score += 30
            factors.append("Excellent price (15%+ below market)")
        elif price_to_market_ratio <= 0.92:
            score += 20
            factors.append("Good price (8%+ below market)")
        elif price_to_market_ratio <= 0.98:
            score += 10
            factors.append("Fair price (2%+ below market)")
        else:
            score -= 10
            factors.append("Overpriced relative to market")
        
        # Factor 2: Price per sq ft analysis (20% weight)
        if price_per_sqft_ratio <= 0.8:
            score += 20
            factors.append("Excellent price per sq ft")
        elif price_per_sqft_ratio <= 0.9:
            score += 15
            factors.append("Good price per sq ft")
        elif price_per_sqft_ratio <= 1.0:
            score += 5
            factors.append("Market-rate price per sq ft")
        else:
            score -= 10
            factors.append("High price per sq ft")
        
        # Factor 3: Investment metrics (25% weight)
        investment_score = investment_analysis.investment_metrics.investment_score
        if investment_score >= 80:
            score += 25
            factors.append("Excellent investment metrics")
        elif investment_score >= 60:
            score += 15
            factors.append("Good investment metrics")
        elif investment_score >= 40:
            score += 5
            factors.append("Fair investment metrics")
        else:
            score -= 15
            factors.append("Poor investment metrics")
        
        # Factor 4: Cash flow potential (15% weight)
        monthly_cash_flow = investment_analysis.investment_metrics.monthly_cash_flow or 0
        if monthly_cash_flow >= 500:
            score += 15
            factors.append("Strong positive cash flow")
        elif monthly_cash_flow >= 200:
            score += 10
            factors.append("Positive cash flow")
        elif monthly_cash_flow >= 0:
            score += 5
            factors.append("Break-even cash flow")
        else:
            score -= 10
            factors.append("Negative cash flow")
        
        # Factor 5: Market liquidity (10% weight)
        if market_stats.total_listings > 1000:
            score += 10
            factors.append("Liquid market")
        elif market_stats.total_listings > 500:
            score += 5
            factors.append("Moderate market activity")
        else:
            score -= 5
            factors.append("Limited market activity")
        
        # Make final decision based on score
        if score >= 70:
            decision["action"] = "pursue"
            decision["deal_quality"] = "excellent"
            decision["confidence"] = min(0.95, 0.7 + (score - 70) * 0.01)
            decision["offer_price"] = property_data["asking_price"] * 0.95  # Aggressive offer
        elif score >= 50:
            decision["action"] = "pursue"
            decision["deal_quality"] = "good"
            decision["confidence"] = min(0.85, 0.6 + (score - 50) * 0.01)
            decision["offer_price"] = property_data["asking_price"] * 0.97  # Moderate offer
        elif score >= 30:
            decision["action"] = "consider"
            decision["deal_quality"] = "marginal"
            decision["confidence"] = min(0.75, 0.5 + (score - 30) * 0.01)
            decision["offer_price"] = property_data["asking_price"] * 0.98  # Conservative offer
        else:
            decision["action"] = "pass"
            decision["deal_quality"] = "poor"
            decision["confidence"] = max(0.6, 0.8 - (30 - score) * 0.01)
            decision["offer_price"] = 0
        
        # Generate reasoning
        decision["key_factors"] = factors
        decision["reasoning"] = f"Expert analysis: {decision['deal_quality']} deal (score: {score}/100). " + \
                              f"Key factors: {', '.join(factors[:3])}"
        
        return decision

class RapidAgentImprover:
    """Rapidly improve agents using expert training data"""
    
    def __init__(self, expert_dataset: List[Dict[str, Any]]):
        self.expert_dataset = expert_dataset
        self.training_examples = self._prepare_training_examples()
    
    def _prepare_training_examples(self) -> List[Dict[str, Any]]:
        """Prepare training examples from expert dataset"""
        
        training_examples = []
        
        for example in self.expert_dataset:
            # Create scenario data
            scenario_data = {
                "deal": {
                    "asking_price": example["property_data"]["asking_price"],
                    "market_value": example["property_data"]["asking_price"],  # Use asking as baseline
                    "property": {
                        "city": example["property_data"]["city"],
                        "state": example["property_data"]["state"],
                        "bedrooms": example["property_data"]["bedrooms"],
                        "bathrooms": example["property_data"]["bathrooms"],
                        "house_size": example["property_data"]["house_size"]
                    },
                    "market_condition": {
                        "trend": "stable",  # Default
                        "interest_rate": 6.0  # Default
                    }
                },
                "market_context": example["market_context"],
                "expert_decision": example["expert_decision"],
                "difficulty": 0.7  # Real-world difficulty
            }
            
            training_examples.append(scenario_data)
        
        return training_examples
    
    async def rapid_improve_agent(self, agent: StandaloneTrainingAgent, 
                                num_examples: int = 1000) -> Dict[str, Any]:
        """Rapidly improve agent using expert training data"""
        
        print(f"🚀 Rapid improvement training for {agent.specialization}")
        print(f"   Using {num_examples:,} expert examples...")
        
        # Select training examples
        training_subset = np.random.choice(
            self.training_examples, 
            size=min(num_examples, len(self.training_examples)), 
            replace=False
        )
        
        improvement_results = {
            "agent_id": agent.agent_id,
            "specialization": agent.specialization,
            "training_examples": len(training_subset),
            "before_performance": agent.performance_metrics.copy(),
            "training_progress": [],
            "after_performance": {},
            "improvement_metrics": {}
        }
        
        # Training loop with expert feedback
        batch_size = 50
        total_batches = len(training_subset) // batch_size + 1
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, len(training_subset))
            batch_examples = training_subset[start_idx:end_idx]
            
            batch_scores = []
            
            for example in batch_examples:
                # Get agent decision
                agent_decision = await agent.analyze_deal(example)
                expert_decision = example["expert_decision"]
                
                # Calculate alignment score with expert
                alignment_score = self._calculate_expert_alignment(
                    agent_decision, expert_decision
                )
                
                # Provide expert feedback
                feedback = self._generate_expert_feedback(
                    agent_decision, expert_decision, alignment_score
                )
                
                # Update agent with expert feedback
                await self._apply_expert_feedback(agent, feedback, alignment_score)
                
                batch_scores.append(alignment_score)
            
            # Track progress
            batch_avg = np.mean(batch_scores)
            improvement_results["training_progress"].append({
                "batch": batch_idx + 1,
                "average_alignment": batch_avg,
                "examples_processed": end_idx
            })
            
            if batch_idx % 5 == 0:
                print(f"   Batch {batch_idx + 1}/{total_batches}: {batch_avg:.1f}% expert alignment")
        
        # Final performance assessment
        improvement_results["after_performance"] = agent.performance_metrics.copy()
        improvement_results["improvement_metrics"] = self._calculate_improvement_metrics(
            improvement_results["before_performance"],
            improvement_results["after_performance"],
            improvement_results["training_progress"]
        )
        
        return improvement_results
    
    def _calculate_expert_alignment(self, agent_decision: Dict, expert_decision: Dict) -> float:
        """Calculate how well agent decision aligns with expert decision"""
        
        alignment_score = 0.0
        
        # Action alignment (40% weight)
        agent_action = agent_decision.get("action", "pass")
        expert_action = expert_decision.get("action", "pass")
        
        if agent_action == expert_action:
            alignment_score += 40
        elif (agent_action in ["pursue", "consider"] and expert_action in ["pursue", "consider"]) or \
             (agent_action == "pass" and expert_action == "pass"):
            alignment_score += 20  # Partial credit for similar decisions
        
        # Confidence alignment (20% weight)
        agent_confidence = agent_decision.get("confidence", 0.5)
        expert_confidence = expert_decision.get("confidence", 0.5)
        confidence_diff = abs(agent_confidence - expert_confidence)
        confidence_score = max(0, 20 * (1 - confidence_diff))
        alignment_score += confidence_score
        
        # Offer price alignment (25% weight) - if both are pursuing
        if agent_action in ["pursue", "consider"] and expert_action in ["pursue", "consider"]:
            agent_offer = agent_decision.get("offer_price", 0)
            expert_offer = expert_decision.get("offer_price", 0)
            
            if agent_offer > 0 and expert_offer > 0:
                price_diff = abs(agent_offer - expert_offer) / expert_offer
                price_score = max(0, 25 * (1 - price_diff))
                alignment_score += price_score
            else:
                alignment_score += 10  # Partial credit if both have offers
        elif agent_action == "pass" and expert_action == "pass":
            alignment_score += 25  # Full credit for both passing
        
        # Deal quality understanding (15% weight)
        expert_quality = expert_decision.get("deal_quality", "poor")
        
        # Infer agent's quality assessment from action and confidence
        if agent_action == "pursue" and agent_confidence > 0.8:
            agent_quality = "excellent"
        elif agent_action == "pursue" and agent_confidence > 0.6:
            agent_quality = "good"
        elif agent_action == "consider":
            agent_quality = "marginal"
        else:
            agent_quality = "poor"
        
        if agent_quality == expert_quality:
            alignment_score += 15
        elif abs(["poor", "marginal", "good", "excellent"].index(agent_quality) - 
                ["poor", "marginal", "good", "excellent"].index(expert_quality)) == 1:
            alignment_score += 7  # Close assessment
        
        return min(100, alignment_score)
    
    def _generate_expert_feedback(self, agent_decision: Dict, expert_decision: Dict, 
                                alignment_score: float) -> Dict[str, Any]:
        """Generate expert feedback for agent improvement"""
        
        feedback = {
            "alignment_score": alignment_score,
            "corrections": [],
            "reinforcements": [],
            "learning_points": []
        }
        
        # Action feedback
        agent_action = agent_decision.get("action", "pass")
        expert_action = expert_decision.get("action", "pass")
        
        if agent_action != expert_action:
            feedback["corrections"].append({
                "aspect": "action",
                "agent_value": agent_action,
                "expert_value": expert_action,
                "explanation": f"Expert would {expert_action} based on: {expert_decision.get('reasoning', 'analysis')}"
            })
        else:
            feedback["reinforcements"].append(f"Correct action: {agent_action}")
        
        # Confidence feedback
        agent_confidence = agent_decision.get("confidence", 0.5)
        expert_confidence = expert_decision.get("confidence", 0.5)
        
        if abs(agent_confidence - expert_confidence) > 0.2:
            feedback["corrections"].append({
                "aspect": "confidence",
                "agent_value": agent_confidence,
                "expert_value": expert_confidence,
                "explanation": f"Expert confidence based on deal quality: {expert_decision.get('deal_quality', 'unknown')}"
            })
        
        # Key learning points from expert reasoning
        expert_factors = expert_decision.get("key_factors", [])
        if expert_factors:
            feedback["learning_points"] = expert_factors[:3]  # Top 3 factors
        
        return feedback
    
    async def _apply_expert_feedback(self, agent: StandaloneTrainingAgent, 
                                   feedback: Dict[str, Any], alignment_score: float):
        """Apply expert feedback to improve agent"""
        
        # Adjust agent's internal parameters based on feedback
        learning_rate = 0.1
        
        # Update skills based on corrections
        for correction in feedback["corrections"]:
            aspect = correction["aspect"]
            
            if aspect == "action":
                # Adjust decision thresholds
                if correction["expert_value"] == "pursue" and correction["agent_value"] == "pass":
                    # Agent was too conservative
                    agent.skills["deal_analysis"] = min(1.0, agent.skills["deal_analysis"] + learning_rate * 0.1)
                elif correction["expert_value"] == "pass" and correction["agent_value"] == "pursue":
                    # Agent was too aggressive
                    agent.skills["risk_assessment"] = min(1.0, agent.skills["risk_assessment"] + learning_rate * 0.1)
            
            elif aspect == "confidence":
                # Adjust confidence calibration
                expert_conf = correction["expert_value"]
                agent_conf = correction["agent_value"]
                
                if expert_conf > agent_conf:
                    # Should be more confident
                    agent.skills["market_analysis"] = min(1.0, agent.skills["market_analysis"] + learning_rate * 0.05)
                else:
                    # Should be less confident
                    agent.skills["risk_assessment"] = min(1.0, agent.skills["risk_assessment"] + learning_rate * 0.05)
        
        # Positive reinforcement for correct decisions
        if alignment_score > 80:
            # Reinforce current approach
            for skill in agent.skills:
                agent.skills[skill] = min(1.0, agent.skills[skill] + learning_rate * 0.02)
        
        # Update performance tracking
        agent.update_performance(alignment_score, "expert_training")
    
    def _calculate_improvement_metrics(self, before: Dict, after: Dict, 
                                     progress: List[Dict]) -> Dict[str, Any]:
        """Calculate improvement metrics"""
        
        metrics = {
            "performance_improvement": after["average_score"] - before["average_score"],
            "consistency_improvement": (100 - np.std([p["average_alignment"] for p in progress])) - 
                                     (100 - np.std([before["average_score"]])),
            "learning_velocity": 0.0,
            "final_expert_alignment": progress[-1]["average_alignment"] if progress else 0,
            "improvement_trend": "improving" if len(progress) > 1 and 
                               progress[-1]["average_alignment"] > progress[0]["average_alignment"] else "stable"
        }
        
        # Calculate learning velocity (improvement per batch)
        if len(progress) > 1:
            alignments = [p["average_alignment"] for p in progress]
            metrics["learning_velocity"] = (alignments[-1] - alignments[0]) / len(alignments)
        
        return metrics

async def main():
    """Main rapid improvement function"""
    
    print("🚀 Real Estate Agent Rapid Improvement System")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Generate expert training dataset
    print("\n📊 Step 1: Generating Expert Training Dataset")
    expert_generator = ExpertDataGenerator()
    
    # Check if we already have expert dataset
    if os.path.exists("expert_training_dataset.json"):
        print("   Loading existing expert dataset...")
        with open("expert_training_dataset.json", "r") as f:
            expert_dataset = json.load(f)
        print(f"   ✅ Loaded {len(expert_dataset):,} expert examples")
    else:
        expert_dataset = await expert_generator.generate_expert_training_dataset(5000)
    
    if not expert_dataset:
        print("❌ Failed to generate expert dataset")
        return
    
    # Step 2: Create and train baseline agents
    print(f"\n🤖 Step 2: Creating Baseline Agents")
    from run_agent_training import train_agent_workforce
    
    # Train baseline agents
    baseline_agents = await train_agent_workforce()
    
    if not baseline_agents:
        print("❌ Failed to create baseline agents")
        return
    
    print(f"✅ Created {len(baseline_agents)} baseline agents")
    
    # Step 3: Rapid improvement using expert data
    print(f"\n🚀 Step 3: Rapid Agent Improvement")
    
    improver = RapidAgentImprover(expert_dataset)
    improvement_results = []
    
    for i, agent_data in enumerate(baseline_agents, 1):
        agent = agent_data["agent"]
        print(f"\n   Improving Agent {i}/{len(baseline_agents)}: {agent_data['description']}")
        
        # Store baseline performance
        baseline_performance = agent.performance_metrics.copy()
        
        # Rapid improvement
        result = await improver.rapid_improve_agent(agent, num_examples=1000)
        improvement_results.append(result)
        
        # Show improvement
        improvement = result["improvement_metrics"]["performance_improvement"]
        expert_alignment = result["improvement_metrics"]["final_expert_alignment"]
        
        print(f"   ✅ Improvement: {improvement:+.1f} points")
        print(f"   📈 Expert Alignment: {expert_alignment:.1f}%")
        print(f"   🎯 Learning Velocity: {result['improvement_metrics']['learning_velocity']:+.2f}/batch")
    
    # Step 4: Validation of improved agents
    print(f"\n🔍 Step 4: Validating Improved Agents")
    
    from validate_agent_readiness import AgentReadinessValidator
    
    validator = AgentReadinessValidator()
    
    # Create improved agent data structure
    improved_agents = []
    for i, agent_data in enumerate(baseline_agents):
        improved_agents.append({
            "agent": agent_data["agent"],
            "description": agent_data["description"],
            "performance": agent_data["agent"].performance_metrics,
            "improvement_result": improvement_results[i]
        })
    
    # Validate improved agents
    validation_results = await validator.validate_agent_workforce(improved_agents)
    
    # Step 5: Results summary
    print(f"\n🎉 RAPID IMPROVEMENT RESULTS")
    print("=" * 60)
    
    # Overall improvement metrics
    total_improvement = sum(r["improvement_metrics"]["performance_improvement"] 
                          for r in improvement_results)
    avg_improvement = total_improvement / len(improvement_results)
    avg_expert_alignment = np.mean([r["improvement_metrics"]["final_expert_alignment"] 
                                  for r in improvement_results])
    
    print(f"📈 Overall Results:")
    print(f"   Average Performance Improvement: {avg_improvement:+.1f} points")
    print(f"   Average Expert Alignment: {avg_expert_alignment:.1f}%")
    print(f"   Agents Ready for Production: {sum(1 for r in validation_results['agent_results'].values() if r['production_readiness_score'] >= 75)}/{len(baseline_agents)}")
    
    # Individual agent results
    print(f"\n🤖 Individual Agent Improvements:")
    for i, result in enumerate(improvement_results):
        agent_name = baseline_agents[i]["description"]
        improvement = result["improvement_metrics"]["performance_improvement"]
        alignment = result["improvement_metrics"]["final_expert_alignment"]
        readiness = validation_results["agent_results"][result["agent_id"]]["production_readiness_score"]
        
        status = "✅ READY" if readiness >= 75 else "⚠️ IMPROVING" if readiness >= 60 else "❌ NEEDS WORK"
        
        print(f"   {status} {agent_name}:")
        print(f"      Performance: {improvement:+.1f} points")
        print(f"      Expert Alignment: {alignment:.1f}%")
        print(f"      Production Readiness: {readiness:.1f}/100")
    
    # Save results
    final_results = {
        "improvement_summary": {
            "total_agents": len(baseline_agents),
            "average_improvement": avg_improvement,
            "average_expert_alignment": avg_expert_alignment,
            "ready_for_production": sum(1 for r in validation_results['agent_results'].values() 
                                      if r['production_readiness_score'] >= 75)
        },
        "individual_results": improvement_results,
        "validation_results": validation_results,
        "expert_dataset_size": len(expert_dataset),
        "timestamp": datetime.now().isoformat()
    }
    
    with open("rapid_improvement_results.json", "w") as f:
        json.dump(final_results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: rapid_improvement_results.json")
    print(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return final_results

if __name__ == "__main__":
    asyncio.run(main())