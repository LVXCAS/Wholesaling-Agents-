#!/usr/bin/env python3
"""
Analyst Tools Demo - Demonstrates the functionality of all analyst agent tools
"""

import asyncio
import json
from datetime import datetime

# Add parent directory to path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import analyst tools
from app.agents.analyst_tools import (
    ComparablePropertyFinderTool,
    RepairCostEstimatorTool,
    FinancialCalculatorTool,
    InvestmentStrategyAnalyzerTool,
    RiskAssessmentTool,
    MarketDataAnalysisTool,
    AnalystToolManager
)


async def demo_comparable_property_finder():
    """Demo comparable property finder tool"""
    print("\n" + "="*60)
    print("COMPARABLE PROPERTY FINDER DEMO")
    print("="*60)
    
    tool = ComparablePropertyFinderTool()
    
    result = await tool.execute(
        property_address="123 Investment Ave",
        property_type="single_family",
        bedrooms=3,
        bathrooms=2,
        square_feet=1500,
        max_distance=2.0,
        max_age=180
    )
    
    if "error" not in result:
        print(f"Found {len(result['comparable_properties'])} comparable properties")
        print(f"Estimated Value: ${result['valuation_estimate']['estimated_value']:,.2f}")
        print(f"Price per Sq Ft: ${result['valuation_estimate']['price_per_sqft']:.2f}")
        print(f"Confidence Score: {result['valuation_estimate']['confidence_score']:.2f}")
        
        print("\nTop 3 Comparables:")
        for i, comp in enumerate(result['comparable_properties'][:3]):
            print(f"  {i+1}. {comp['address']} - ${comp['sale_price']:,} ({comp['similarity_score']:.2f} similarity)")
    else:
        print(f"Error: {result['error']}")


async def demo_repair_cost_estimator():
    """Demo repair cost estimator tool"""
    print("\n" + "="*60)
    print("REPAIR COST ESTIMATOR DEMO")
    print("="*60)
    
    tool = RepairCostEstimatorTool()
    
    result = await tool.execute(
        property_photos=["kitchen.jpg", "bathroom.jpg", "exterior.jpg"],
        property_description="Property needs kitchen renovation, bathroom updates, and exterior paint",
        property_age=25,
        square_feet=1500,
        property_condition="fair"
    )
    
    if "error" not in result:
        estimate = result['repair_estimate']
        print(f"Total Repair Cost: ${estimate['total_cost']:,.2f}")
        print(f"Subtotal: ${estimate['subtotal']:,.2f}")
        print(f"Contingency (15%): ${estimate['contingency_amount']:,.2f}")
        print(f"Cost per Sq Ft: ${estimate['cost_per_sqft']:.2f}")
        print(f"Timeline: {estimate['timeline_days']} days")
        print(f"Confidence Score: {estimate['confidence_score']:.2f}")
        
        print("\nRepair Line Items:")
        for category, cost in result['line_items'].items():
            print(f"  {category.replace('_', ' ').title()}: ${cost:,}")
    else:
        print(f"Error: {result['error']}")


async def demo_financial_calculator():
    """Demo financial calculator tool"""
    print("\n" + "="*60)
    print("FINANCIAL CALCULATOR DEMO")
    print("="*60)
    
    tool = FinancialCalculatorTool()
    
    result = await tool.execute(
        purchase_price=275000,
        repair_cost=25000,
        arv=350000,
        monthly_rent=2500,
        down_payment_percentage=0.25,
        interest_rate=0.07,
        loan_term_years=30
    )
    
    if "error" not in result:
        metrics = result['financial_metrics']
        print(f"Purchase Price: ${metrics['purchase_price']:,}")
        print(f"Repair Cost: ${metrics['repair_cost']:,}")
        print(f"Total Investment: ${metrics['total_investment']:,}")
        print(f"After Repair Value: ${metrics['after_repair_value']:,}")
        print(f"Monthly Rent: ${metrics['monthly_rent']:,}")
        print(f"Monthly Cash Flow: ${metrics['monthly_cash_flow']:,.2f}")
        print(f"Cap Rate: {metrics['cap_rate']:.2%}")
        print(f"Cash-on-Cash Return: {metrics['cash_on_cash_return']:.2%}")
        print(f"Flip Profit: ${metrics['flip_profit']:,}")
        print(f"Flip ROI: {metrics['flip_roi']:.2%}")
        
        print("\nMonthly Expense Breakdown:")
        expenses = result['expense_breakdown']
        for category, amount in expenses.items():
            print(f"  {category.replace('_', ' ').title()}: ${amount:.2f}")
    else:
        print(f"Error: {result['error']}")


async def demo_investment_strategy_analyzer():
    """Demo investment strategy analyzer tool"""
    print("\n" + "="*60)
    print("INVESTMENT STRATEGY ANALYZER DEMO")
    print("="*60)
    
    tool = InvestmentStrategyAnalyzerTool()
    
    financial_metrics = {
        "total_investment": 300000,
        "after_repair_value": 350000,
        "annual_cash_flow": 6000,
        "cap_rate": 0.08,
        "flip_profit": 30000,
        "wholesale_fee": 8000,
        "cash_on_cash_return": 0.12,
        "flip_roi": 0.10,
        "wholesale_margin": 0.03,
        "down_payment": 75000
    }
    
    market_conditions = {
        "market_temperature": "warm",
        "appreciation_forecast": 0.03,
        "rental_demand": "moderate"
    }
    
    result = await tool.execute(
        financial_metrics=financial_metrics,
        market_conditions=market_conditions,
        investor_profile={}
    )
    
    if "error" not in result:
        print(f"Recommended Strategy: {result['recommended_strategy']}")
        print(f"Number of Viable Strategies: {result['strategy_count']}")
        
        print("\nStrategy Analysis:")
        for i, strategy in enumerate(result['strategies'][:3]):  # Top 3
            print(f"\n{i+1}. {strategy['strategy_type'].replace('_', ' ').title()}")
            print(f"   Potential Profit: ${strategy['potential_profit']:,.2f}")
            print(f"   ROI: {strategy['roi']:.2%}")
            print(f"   Risk Level: {strategy['risk_level']:.1f}/10")
            print(f"   Timeline: {strategy['timeline_days']} days")
            print(f"   Risk-Adjusted Score: {strategy['risk_adjusted_score']:.3f}")
    else:
        print(f"Error: {result['error']}")


async def demo_risk_assessment():
    """Demo risk assessment tool"""
    print("\n" + "="*60)
    print("RISK ASSESSMENT DEMO")
    print("="*60)
    
    tool = RiskAssessmentTool()
    
    property_data = {
        "year_built": 1990,
        "condition": "fair",
        "location_quality": "good",
        "neighborhood_trend": "stable",
        "days_on_market": 45,
        "property_type": "single_family"
    }
    
    financial_metrics = {
        "cap_rate": 0.07,
        "monthly_cash_flow": 300,
        "roi": 0.12,
        "loan_amount": 225000,
        "total_investment": 300000
    }
    
    market_conditions = {
        "market_temperature": "warm",
        "inventory_level": "normal",
        "price_change_yoy": 0.02
    }
    
    result = await tool.execute(
        property_data=property_data,
        financial_metrics=financial_metrics,
        market_conditions=market_conditions,
        analysis_data={"comparable_properties": [1, 2, 3]}
    )
    
    if "error" not in result:
        assessment = result['risk_assessment']
        print(f"Overall Risk Score: {assessment['overall_risk_score']:.1f}/10")
        print(f"Risk Level: {assessment['risk_level'].upper()}")
        print(f"Confidence Score: {assessment['confidence_score']:.2f}")
        
        print(f"\nRisk Factors ({len(assessment['risk_factors'])}):")
        for factor in assessment['risk_factors']:
            print(f"  • {factor}")
        
        print("\nRisk Breakdown:")
        breakdown = result['risk_breakdown']
        for category, score in breakdown.items():
            print(f"  {category.replace('_', ' ').title()}: {score:.1f}/10")
        
        if result['mitigation_strategies']:
            print(f"\nMitigation Strategies ({len(result['mitigation_strategies'])}):")
            for strategy in result['mitigation_strategies']:
                print(f"  • {strategy}")
    else:
        print(f"Error: {result['error']}")


async def demo_market_data_analysis():
    """Demo market data analysis tool"""
    print("\n" + "="*60)
    print("MARKET DATA ANALYSIS DEMO")
    print("="*60)
    
    tool = MarketDataAnalysisTool()
    
    result = await tool.execute(
        property_address="123 Market St",
        property_type="single_family",
        zip_code="12345",
        analysis_period=12
    )
    
    if "error" not in result:
        analysis = result['market_analysis']
        print(f"Market Temperature: {analysis['market_temperature'].upper()}")
        print(f"Price Appreciation (6m): {analysis['price_appreciation_6m']:.2%}")
        
        rental = analysis['rental_market']
        print(f"Median Rent: ${rental['median_rent']:,}")
        print(f"Rent Growth (YoY): {rental['rent_growth_yoy']:.2%}")
        print(f"Vacancy Rate: {rental['vacancy_rate']:.2%}")
        print(f"Rental Demand: {rental['rental_demand'].upper()}")
        
        neighborhood = analysis['neighborhood_metrics']
        print(f"School Rating: {neighborhood['school_rating']}/10")
        print(f"Walkability Score: {neighborhood['walkability_score']}")
        print(f"Crime Index: {neighborhood['crime_index']} (lower is better)")
        
        attractiveness = analysis['investment_attractiveness']
        print(f"Investment Score: {attractiveness['overall_score']:.2f}/1.0")
        print(f"Recommendation: {attractiveness['recommendation'].upper()}")
        
        print(f"\nKey Insights ({len(analysis['key_insights'])}):")
        for insight in analysis['key_insights']:
            print(f"  • {insight}")
    else:
        print(f"Error: {result['error']}")


async def demo_tool_manager():
    """Demo the analyst tool manager"""
    print("\n" + "="*60)
    print("ANALYST TOOL MANAGER DEMO")
    print("="*60)
    
    manager = AnalystToolManager()
    
    print("Available Tools:")
    for tool in manager.get_available_tools():
        print(f"  • {tool}")
    
    # Execute a tool through the manager
    print("\nExecuting financial calculator through manager...")
    result = await manager.execute_tool(
        "financial_calculator",
        purchase_price=250000,
        repair_cost=20000,
        monthly_rent=2000
    )
    
    if result["success"]:
        metrics = result["result"]["financial_metrics"]
        print(f"Monthly Cash Flow: ${metrics['monthly_cash_flow']:,.2f}")
        print(f"Cap Rate: {metrics['cap_rate']:.2%}")
    else:
        print(f"Error: {result['error']}")
    
    # Show usage stats
    print("\nTool Usage Statistics:")
    stats = manager.get_tool_stats()
    print(f"Total Calls: {stats['total_calls']}")
    print(f"Total Errors: {stats['total_errors']}")


async def main():
    """Run all analyst tool demos"""
    print("ANALYST AGENT TOOLS DEMONSTRATION")
    print("=" * 80)
    print(f"Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        await demo_comparable_property_finder()
        await demo_repair_cost_estimator()
        await demo_financial_calculator()
        await demo_investment_strategy_analyzer()
        await demo_risk_assessment()
        await demo_market_data_analysis()
        await demo_tool_manager()
        
        print("\n" + "="*80)
        print("ALL ANALYST TOOLS DEMO COMPLETED SUCCESSFULLY!")
        print("="*80)
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())