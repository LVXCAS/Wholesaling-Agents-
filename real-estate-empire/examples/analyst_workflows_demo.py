"""
Analyst Workflows Demo
Demonstrates the five core analyst workflows in action
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.agents.analyst_agent import AnalystAgent
from app.agents.analyst_workflows import AnalystWorkflows
from app.agents.analyst_models import PropertyValuation, RepairEstimate, FinancialMetrics
from app.core.agent_state import StateManager, AgentType


async def demo_analyst_workflows():
    """Demonstrate analyst workflows"""
    print("🏠 Analyst Agent Workflows Demo")
    print("=" * 50)
    
    # Create sample deal
    sample_deal = {
        "id": "demo-deal-123",
        "property_address": "123 Investment Ave",
        "city": "Real Estate City",
        "state": "RE",
        "zip_code": "12345",
        "property_type": "single_family",
        "bedrooms": 3,
        "bathrooms": 2,
        "square_feet": 1500,
        "year_built": 1990,
        "listing_price": 250000,
        "property_condition": "fair",
        "description": "Great investment opportunity in growing neighborhood"
    }
    
    # Create sample state
    state = StateManager.create_initial_state()
    state["market_conditions"] = {
        "market_temperature": "warm",
        "price_change_yoy": 0.05,
        "rental_demand": "moderate",
        "cap_rate_average": 0.08,
        "rent_growth_yoy": 0.03
    }
    state["investment_criteria"] = {
        "min_cap_rate": 0.08,
        "min_cash_flow": 200,
        "max_risk_score": 7.0,
        "min_roi": 0.15
    }
    
    # Create mock analyst agent
    mock_agent = Mock()
    mock_agent.name = "DemoAnalystAgent"
    mock_agent.agent_type = AgentType.ANALYST
    
    # Create workflows instance
    workflows = AnalystWorkflows(mock_agent)
    
    print(f"📊 Analyzing property: {sample_deal['property_address']}")
    print(f"💰 Listing price: ${sample_deal['listing_price']:,}")
    print(f"🏡 {sample_deal['bedrooms']}BR/{sample_deal['bathrooms']}BA, {sample_deal['square_feet']:,} sq ft")
    print()
    
    # Mock tools for demonstration
    def create_mock_tools():
        # Mock comparable property finder
        comp_tool = AsyncMock()
        comp_tool.execute.return_value = {
            "comparable_properties": [
                {
                    "id": "comp1",
                    "address": "100 Similar St",
                    "sale_price": 245000,
                    "similarity_score": 0.92,
                    "distance_miles": 0.3,
                    "sale_date": "2024-06-15",
                    "bedrooms": 3,
                    "bathrooms": 2,
                    "square_feet": 1480
                },
                {
                    "id": "comp2",
                    "address": "200 Comparable Ave",
                    "sale_price": 255000,
                    "similarity_score": 0.88,
                    "distance_miles": 0.7,
                    "sale_date": "2024-06-20",
                    "bedrooms": 3,
                    "bathrooms": 2,
                    "square_feet": 1520
                },
                {
                    "id": "comp3",
                    "address": "300 Market Rd",
                    "sale_price": 248000,
                    "similarity_score": 0.85,
                    "distance_miles": 1.1,
                    "sale_date": "2024-06-10",
                    "bedrooms": 3,
                    "bathrooms": 2,
                    "square_feet": 1495
                }
            ],
            "valuation_estimate": {
                "estimated_value": 249000,
                "price_per_sqft": 166.0,
                "confidence_score": 0.88,
                "comp_count": 3,
                "valuation_method": "comparable_sales"
            }
        }
        
        # Mock financial calculator
        financial_tool = AsyncMock()
        financial_tool.execute.return_value = {
            "financial_metrics": {
                "purchase_price": 250000,
                "repair_cost": 30000,
                "total_investment": 280000,
                "after_repair_value": 275000,
                "monthly_rent": 2400,
                "monthly_expenses": 1680,
                "monthly_cash_flow": 720,
                "annual_cash_flow": 8640,
                "cap_rate": 0.092,
                "cash_on_cash_return": 0.123,
                "roi": 0.168,
                "gross_rent_multiplier": 9.7,
                "flip_profit": 22000,
                "flip_roi": 0.079,
                "wholesale_fee": 7500,
                "wholesale_margin": 0.03
            },
            "expense_breakdown": {
                "monthly_mortgage": 1200,
                "insurance": 150,
                "property_tax": 200,
                "vacancy_loss": 120,
                "management": 192,
                "maintenance": 120,
                "capex": 120
            },
            "assumptions": {
                "down_payment_percentage": 0.25,
                "interest_rate": 0.07,
                "vacancy_rate": 0.05,
                "management_fee": 0.08
            }
        }
        
        # Mock strategy analyzer
        strategy_tool = AsyncMock()
        strategy_tool.execute.return_value = {
            "strategies": [
                {
                    "strategy_type": "buy_and_hold_rental",
                    "potential_profit": 8640,
                    "roi": 0.123,
                    "risk_level": 4.5,
                    "timeline_days": 30,
                    "funding_required": 70000,
                    "pros": ["Steady monthly cash flow", "Long-term appreciation", "Tax benefits"],
                    "cons": ["Property management required", "Vacancy risk", "Maintenance costs"],
                    "confidence_score": 0.87
                },
                {
                    "strategy_type": "fix_and_flip",
                    "potential_profit": 22000,
                    "roi": 0.079,
                    "risk_level": 6.0,
                    "timeline_days": 90,
                    "funding_required": 280000,
                    "pros": ["Quick profit realization", "No landlord duties"],
                    "cons": ["Market timing risk", "Construction delays", "Higher taxes"],
                    "confidence_score": 0.75
                },
                {
                    "strategy_type": "wholesale",
                    "potential_profit": 7500,
                    "roi": 0.75,
                    "risk_level": 2.0,
                    "timeline_days": 14,
                    "funding_required": 1000,
                    "pros": ["Very low risk", "Quick turnaround", "Minimal capital"],
                    "cons": ["Lower profit margins", "Requires buyer network"],
                    "confidence_score": 0.92
                }
            ],
            "recommended_strategy": "buy_and_hold_rental",
            "market_analysis": {
                "market_temperature": "warm",
                "rental_demand": "moderate",
                "strategy_favorability": {
                    "rental": 0.8,
                    "flip": 0.7,
                    "wholesale": 0.8
                }
            }
        }
        
        # Mock risk assessment
        risk_tool = AsyncMock()
        risk_tool.execute.return_value = {
            "risk_assessment": {
                "risk_factors": [
                    "Property age (34 years) may require major system updates",
                    "Moderate rental demand increases vacancy risk",
                    "Fair condition requires significant repairs"
                ],
                "overall_risk_score": 5.2,
                "risk_categories": {
                    "property_risk": 6.0,
                    "market_risk": 4.5,
                    "financial_risk": 4.8,
                    "liquidity_risk": 5.5
                },
                "mitigation_strategies": [
                    "Conduct thorough property inspection",
                    "Maintain 6-month expense reserve",
                    "Consider property management company",
                    "Monitor local market conditions"
                ]
            }
        }
        
        def mock_get_tool(tool_name):
            tools = {
                "comparable_property_finder": comp_tool,
                "financial_calculator": financial_tool,
                "investment_strategy_analyzer": strategy_tool,
                "risk_assessment_tool": risk_tool
            }
            return tools.get(tool_name)
        
        return mock_get_tool
    
    # Execute workflows with mocked tools
    with patch('app.core.agent_tools.tool_registry.get_tool', side_effect=create_mock_tools()):
        
        # 1. Property Valuation Workflow
        print("1️⃣ Property Valuation Workflow")
        print("-" * 30)
        valuation_result = await workflows.execute_property_valuation_workflow(sample_deal, state)
        
        if valuation_result.success:
            valuation_data = valuation_result.data["valuation"]
            print(f"✅ Current Value: ${valuation_data['current_value']:,.0f}")
            print(f"✅ After Repair Value (ARV): ${valuation_data['arv']:,.0f}")
            print(f"✅ Confidence Score: {valuation_data['confidence_score']:.1%}")
            print(f"✅ Comparable Properties: {valuation_data['comp_count']}")
            print(f"⏱️ Execution Time: {valuation_result.execution_time:.2f}s")
        else:
            print(f"❌ Failed: {valuation_result.error}")
        print()
        
        # 2. Financial Analysis Workflow
        print("2️⃣ Financial Analysis Workflow")
        print("-" * 30)
        
        # Create valuation and repair estimate objects
        valuation = PropertyValuation(**valuation_result.data["valuation"])
        repair_estimate = RepairEstimate(
            total_cost=30000,
            confidence_score=0.82,
            line_items={"kitchen": 15000, "bathroom": 8000, "flooring": 7000},
            contingency_percentage=0.15,
            timeline_days=45
        )
        
        financial_result = await workflows.execute_financial_analysis_workflow(
            sample_deal, valuation, repair_estimate, state
        )
        
        if financial_result.success:
            metrics = financial_result.data["financial_metrics"]
            print(f"✅ Monthly Cash Flow: ${metrics['monthly_cash_flow']:,.0f}")
            print(f"✅ Cap Rate: {metrics['cap_rate']:.1%}")
            print(f"✅ Cash-on-Cash Return: {metrics['cash_on_cash_return']:.1%}")
            print(f"✅ ROI: {metrics['roi']:.1%}")
            print(f"⏱️ Execution Time: {financial_result.execution_time:.2f}s")
        else:
            print(f"❌ Failed: {financial_result.error}")
        print()
        
        # 3. Strategy Comparison Workflow
        print("3️⃣ Strategy Comparison Workflow")
        print("-" * 30)
        
        financial_metrics = FinancialMetrics(**financial_result.data["financial_metrics"])
        strategy_result = await workflows.execute_strategy_comparison_workflow(
            sample_deal, financial_metrics, state
        )
        
        if strategy_result.success:
            strategies = strategy_result.data["strategies"]
            recommended = strategy_result.data["recommended_strategy"]
            print(f"✅ Recommended Strategy: {recommended.replace('_', ' ').title()}")
            print(f"✅ Strategies Analyzed: {len(strategies)}")
            
            for i, strategy in enumerate(strategies[:3], 1):
                print(f"   {i}. {strategy['strategy_type'].replace('_', ' ').title()}")
                print(f"      💰 Profit: ${strategy['potential_profit']:,.0f}")
                print(f"      📊 ROI: {strategy['roi']:.1%}")
                print(f"      ⚠️ Risk: {strategy['risk_level']:.1f}/10")
                print(f"      📅 Timeline: {strategy['timeline_days']} days")
            
            print(f"⏱️ Execution Time: {strategy_result.execution_time:.2f}s")
        else:
            print(f"❌ Failed: {strategy_result.error}")
        print()
        
        # 4. Risk Assessment Workflow
        print("4️⃣ Risk Assessment Workflow")
        print("-" * 30)
        
        analysis_data = {
            "valuation": valuation_result.data,
            "financial_metrics": financial_result.data,
            "strategies": strategy_result.data
        }
        
        risk_result = await workflows.execute_risk_assessment_workflow(
            sample_deal, analysis_data, state
        )
        
        if risk_result.success:
            risk_data = risk_result.data
            print(f"✅ Overall Risk Score: {risk_data['overall_risk_score']:.1f}/10")
            print(f"✅ Risk Factors Identified: {len(risk_data['risk_factors'])}")
            
            print("   Key Risk Factors:")
            for factor in risk_data['risk_factors'][:3]:
                print(f"   • {factor}")
            
            print(f"⏱️ Execution Time: {risk_result.execution_time:.2f}s")
        else:
            print(f"❌ Failed: {risk_result.error}")
        print()
        
        # 5. Recommendation Generation Workflow
        print("5️⃣ Recommendation Generation Workflow")
        print("-" * 30)
        
        workflow_results = {
            "property_valuation": valuation_result,
            "financial_analysis": financial_result,
            "strategy_comparison": strategy_result,
            "risk_assessment": risk_result
        }
        
        recommendation_result = await workflows.execute_recommendation_generation_workflow(
            sample_deal, workflow_results, state
        )
        
        if recommendation_result.success:
            rec_data = recommendation_result.data
            recommendation = rec_data["investment_recommendation"]
            confidence = rec_data["confidence_level"]
            reasoning = rec_data["recommendation_reason"]
            
            # Format recommendation with emoji
            rec_emoji = {
                "proceed": "🟢",
                "caution": "🟡", 
                "reject": "🔴"
            }.get(recommendation, "⚪")
            
            print(f"{rec_emoji} Investment Recommendation: {recommendation.upper()}")
            print(f"✅ Confidence Level: {confidence:.1%}")
            print(f"📝 Reasoning: {reasoning}")
            
            key_metrics = rec_data["key_metrics"]
            print("\n📊 Key Metrics Summary:")
            print(f"   • Cap Rate: {key_metrics.get('cap_rate', 0):.1%}")
            print(f"   • Monthly Cash Flow: ${key_metrics.get('cash_flow', 0):,.0f}")
            print(f"   • ROI: {key_metrics.get('roi', 0):.1%}")
            print(f"   • Risk Score: {key_metrics.get('risk_score', 0):.1f}/10")
            
            print(f"⏱️ Execution Time: {recommendation_result.execution_time:.2f}s")
        else:
            print(f"❌ Failed: {recommendation_result.error}")
        print()
        
        # Workflow Summary
        print("📈 Workflow Execution Summary")
        print("-" * 30)
        
        all_results = [valuation_result, financial_result, strategy_result, risk_result, recommendation_result]
        successful = sum(1 for r in all_results if r.success)
        total_time = sum(r.execution_time for r in all_results)
        avg_confidence = sum(r.confidence_score for r in all_results if r.success) / max(successful, 1)
        
        print(f"✅ Workflows Completed: {successful}/5")
        print(f"⏱️ Total Execution Time: {total_time:.2f}s")
        print(f"📊 Average Confidence: {avg_confidence:.1%}")
        
        # Show workflow history
        history = workflows.get_workflow_history()
        print(f"📚 Workflow History: {sum(len(results) for results in history.values())} total executions")
        
        print("\n🎉 Analyst Workflows Demo Complete!")


if __name__ == "__main__":
    asyncio.run(demo_analyst_workflows())