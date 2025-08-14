"""
Analyst Agent Tools - Specialized tools for property analysis and financial modeling
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import random
import json

from pydantic import BaseModel, Field

try:
    from ..core.agent_tools import BaseAgentTool, ToolMetadata, ToolCategory, ToolAccessLevel
except ImportError:
    from app.core.agent_tools import BaseAgentTool, ToolMetadata, ToolCategory, ToolAccessLevel

logger = logging.getLogger(__name__)


class ComparablePropertyFinderTool(BaseAgentTool):
    """Tool for finding comparable properties for valuation analysis"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="comparable_property_finder",
            description="Find comparable properties for accurate property valuation",
            category=ToolCategory.ANALYSIS,
            access_level=ToolAccessLevel.RESTRICTED,
            allowed_agents=["analyst", "supervisor"],
            rate_limit=50,
            cost_per_call=0.15,
            timeout_seconds=45
        )
        super().__init__(metadata)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute comparable property search"""
        property_address = kwargs.get("property_address", "")
        property_type = kwargs.get("property_type", "single_family")
        bedrooms = kwargs.get("bedrooms", 3)
        bathrooms = kwargs.get("bathrooms", 2)
        square_feet = kwargs.get("square_feet", 1500)
        max_distance = kwargs.get("max_distance", 2.0)  # miles
        max_age = kwargs.get("max_age", 180)  # days
        
        try:
            # Simulate API call delay
            await asyncio.sleep(0.4)
            
            # Generate comparable properties
            comparables = []
            for i in range(5):
                comp = {
                    "id": str(uuid.uuid4()),
                    "address": f"{1000 + i * 100} Comparable St",
                    "sale_price": 250000 + (i * 15000) - 30000 + random.randint(-20000, 20000),
                    "sale_date": (datetime.now() - timedelta(days=random.randint(30, max_age))).isoformat(),
                    "property_type": property_type,
                    "bedrooms": bedrooms + random.randint(-1, 1),
                    "bathrooms": bathrooms + random.choice([-0.5, 0, 0.5]),
                    "square_feet": square_feet + random.randint(-200, 300),
                    "lot_size": 0.25 + random.uniform(-0.1, 0.2),
                    "year_built": 1990 + random.randint(-10, 20),
                    "distance_miles": random.uniform(0.2, max_distance),
                    "similarity_score": 0.95 - (i * 0.05) + random.uniform(-0.05, 0.05),
                    "condition": random.choice(["excellent", "good", "fair"]),
                    "location_quality": random.choice(["prime", "good", "average"]),
                    "days_on_market": random.randint(15, 90),
                    "price_per_sqft": 0,  # Will be calculated
                    "adjustments": {
                        "condition_adjustment": random.randint(-10000, 5000),
                        "size_adjustment": random.randint(-5000, 8000),
                        "location_adjustment": random.randint(-3000, 5000),
                        "age_adjustment": random.randint(-2000, 3000)
                    }
                }
                
                # Calculate price per square foot
                comp["price_per_sqft"] = comp["sale_price"] / comp["square_feet"]
                
                comparables.append(comp)
            
            # Sort by similarity score
            comparables.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            # Calculate valuation estimates
            price_per_sqft_avg = sum(comp["price_per_sqft"] for comp in comparables) / len(comparables)
            estimated_value = price_per_sqft_avg * square_feet
            
            # Calculate confidence score based on comp quality
            avg_similarity = sum(comp["similarity_score"] for comp in comparables) / len(comparables)
            distance_factor = 1.0 - (sum(comp["distance_miles"] for comp in comparables) / len(comparables) / max_distance)
            confidence_score = (avg_similarity + distance_factor) / 2
            
            return {
                "comparable_properties": comparables,
                "valuation_estimate": {
                    "estimated_value": estimated_value,
                    "price_per_sqft": price_per_sqft_avg,
                    "confidence_score": confidence_score,
                    "comp_count": len(comparables),
                    "valuation_method": "comparable_sales"
                },
                "search_parameters": {
                    "max_distance": max_distance,
                    "max_age": max_age,
                    "property_type": property_type
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Comparable property finder error: {e}")
            return {
                "comparable_properties": [],
                "valuation_estimate": None,
                "error": str(e)
            }


class RepairCostEstimatorTool(BaseAgentTool):
    """Tool for estimating repair costs using AI vision and market data"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="repair_cost_estimator",
            description="Estimate repair costs based on property photos and descriptions",
            category=ToolCategory.ANALYSIS,
            access_level=ToolAccessLevel.RESTRICTED,
            allowed_agents=["analyst", "supervisor"],
            rate_limit=30,
            cost_per_call=0.25,
            timeout_seconds=60
        )
        super().__init__(metadata)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute repair cost estimation"""
        property_photos = kwargs.get("property_photos", [])
        property_description = kwargs.get("property_description", "")
        property_age = kwargs.get("property_age", 30)
        square_feet = kwargs.get("square_feet", 1500)
        property_condition = kwargs.get("property_condition", "fair")
        
        try:
            # Simulate AI vision analysis delay
            await asyncio.sleep(0.6)
            
            # Base repair costs per square foot by condition
            base_costs = {
                "excellent": 5,
                "good": 15,
                "fair": 35,
                "poor": 65,
                "distressed": 85
            }
            
            base_cost_per_sqft = base_costs.get(property_condition, 35)
            
            # Generate detailed repair estimate
            repair_categories = {
                "kitchen_renovation": {
                    "cost": random.randint(8000, 25000),
                    "priority": "high" if "kitchen" in property_description.lower() else "medium",
                    "timeline_days": 14
                },
                "bathroom_updates": {
                    "cost": random.randint(4000, 12000),
                    "priority": "high" if "bathroom" in property_description.lower() else "medium",
                    "timeline_days": 7
                },
                "flooring": {
                    "cost": int(square_feet * random.uniform(3, 8)),
                    "priority": "medium",
                    "timeline_days": 5
                },
                "paint_interior": {
                    "cost": int(square_feet * random.uniform(1.5, 3)),
                    "priority": "low",
                    "timeline_days": 3
                },
                "paint_exterior": {
                    "cost": random.randint(2000, 6000),
                    "priority": "medium",
                    "timeline_days": 4
                },
                "roof_repairs": {
                    "cost": random.randint(3000, 15000),
                    "priority": "high" if property_age > 20 else "low",
                    "timeline_days": 3
                },
                "hvac_updates": {
                    "cost": random.randint(3000, 8000),
                    "priority": "medium" if property_age > 15 else "low",
                    "timeline_days": 2
                },
                "electrical_updates": {
                    "cost": random.randint(2000, 6000),
                    "priority": "high" if property_age > 30 else "low",
                    "timeline_days": 3
                },
                "plumbing_updates": {
                    "cost": random.randint(1500, 5000),
                    "priority": "medium" if property_age > 25 else "low",
                    "timeline_days": 2
                },
                "landscaping": {
                    "cost": random.randint(1000, 4000),
                    "priority": "low",
                    "timeline_days": 2
                },
                "windows_doors": {
                    "cost": random.randint(2000, 8000),
                    "priority": "medium" if property_age > 20 else "low",
                    "timeline_days": 3
                }
            }
            
            # Filter repairs based on condition and age
            selected_repairs = {}
            for category, details in repair_categories.items():
                # Include repair based on priority and random factor
                if (details["priority"] == "high" or 
                    (details["priority"] == "medium" and random.random() > 0.3) or
                    (details["priority"] == "low" and random.random() > 0.7)):
                    selected_repairs[category] = details["cost"]
            
            # Calculate total costs
            subtotal = sum(selected_repairs.values())
            contingency_percentage = 0.15
            contingency_amount = subtotal * contingency_percentage
            total_cost = subtotal + contingency_amount
            
            # Calculate timeline
            max_timeline = max([repair_categories[cat]["timeline_days"] 
                              for cat in selected_repairs.keys()], default=0)
            total_timeline = max_timeline + 5  # Buffer days
            
            # Categorize repairs by priority
            priority_repairs = [cat for cat, details in repair_categories.items() 
                              if cat in selected_repairs and details["priority"] == "high"]
            cosmetic_repairs = [cat for cat, details in repair_categories.items() 
                              if cat in selected_repairs and details["priority"] == "low"]
            
            # Calculate confidence score
            confidence_factors = {
                "has_photos": len(property_photos) > 0,
                "has_description": len(property_description) > 50,
                "known_condition": property_condition != "unknown",
                "reasonable_age": 5 <= property_age <= 100
            }
            confidence_score = sum(confidence_factors.values()) / len(confidence_factors)
            
            return {
                "repair_estimate": {
                    "total_cost": total_cost,
                    "subtotal": subtotal,
                    "contingency_amount": contingency_amount,
                    "contingency_percentage": contingency_percentage,
                    "confidence_score": confidence_score,
                    "cost_per_sqft": total_cost / square_feet,
                    "timeline_days": total_timeline
                },
                "line_items": selected_repairs,
                "repair_categories": {
                    "priority_repairs": priority_repairs,
                    "cosmetic_repairs": cosmetic_repairs,
                    "structural_repairs": [cat for cat in priority_repairs 
                                         if cat in ["roof_repairs", "electrical_updates", "plumbing_updates"]]
                },
                "analysis_factors": {
                    "property_condition": property_condition,
                    "property_age": property_age,
                    "square_feet": square_feet,
                    "photos_analyzed": len(property_photos),
                    "description_length": len(property_description)
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Repair cost estimator error: {e}")
            return {
                "repair_estimate": None,
                "error": str(e)
            }


class FinancialCalculatorTool(BaseAgentTool):
    """Tool for calculating comprehensive financial metrics"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="financial_calculator",
            description="Calculate comprehensive real estate investment financial metrics",
            category=ToolCategory.FINANCIAL,
            access_level=ToolAccessLevel.RESTRICTED,
            allowed_agents=["analyst", "portfolio", "supervisor"],
            rate_limit=100,
            cost_per_call=0.05,
            timeout_seconds=30
        )
        super().__init__(metadata)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute financial calculations"""
        purchase_price = kwargs.get("purchase_price", 0)
        repair_cost = kwargs.get("repair_cost", 0)
        arv = kwargs.get("arv", purchase_price * 1.1)
        monthly_rent = kwargs.get("monthly_rent", purchase_price * 0.01)
        
        # Default assumptions
        down_payment_percentage = kwargs.get("down_payment_percentage", 0.25)
        interest_rate = kwargs.get("interest_rate", 0.07)
        loan_term_years = kwargs.get("loan_term_years", 30)
        vacancy_rate = kwargs.get("vacancy_rate", 0.05)
        management_fee = kwargs.get("management_fee", 0.08)
        maintenance_reserve = kwargs.get("maintenance_reserve", 0.05)
        capex_reserve = kwargs.get("capex_reserve", 0.05)
        insurance_monthly = kwargs.get("insurance_monthly", monthly_rent * 0.02)
        property_tax_monthly = kwargs.get("property_tax_monthly", monthly_rent * 0.03)
        
        try:
            # Calculate basic metrics
            total_investment = purchase_price + repair_cost
            down_payment = total_investment * down_payment_percentage
            loan_amount = total_investment - down_payment
            
            # Calculate monthly mortgage payment
            monthly_rate = interest_rate / 12
            num_payments = loan_term_years * 12
            if monthly_rate > 0:
                monthly_mortgage = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
            else:
                monthly_mortgage = loan_amount / num_payments
            
            # Calculate monthly expenses
            vacancy_loss = monthly_rent * vacancy_rate
            management_cost = monthly_rent * management_fee
            maintenance_cost = monthly_rent * maintenance_reserve
            capex_cost = monthly_rent * capex_reserve
            
            total_monthly_expenses = (
                monthly_mortgage + insurance_monthly + property_tax_monthly +
                vacancy_loss + management_cost + maintenance_cost + capex_cost
            )
            
            # Calculate cash flow
            monthly_cash_flow = monthly_rent - total_monthly_expenses
            annual_cash_flow = monthly_cash_flow * 12
            
            # Calculate investment returns
            cap_rate = (monthly_rent * 12 - (total_monthly_expenses - monthly_mortgage) * 12) / total_investment
            cash_on_cash_return = annual_cash_flow / down_payment if down_payment > 0 else 0
            gross_rent_multiplier = total_investment / (monthly_rent * 12)
            
            # Calculate flip metrics
            selling_costs_percentage = 0.08  # 8% for realtor, closing, etc.
            selling_costs = arv * selling_costs_percentage
            flip_profit = arv - total_investment - selling_costs
            flip_roi = flip_profit / total_investment if total_investment > 0 else 0
            
            # Calculate wholesale metrics
            wholesale_fee = max(5000, total_investment * 0.03)  # 3% or $5k minimum
            wholesale_margin = wholesale_fee / purchase_price if purchase_price > 0 else 0
            
            # Calculate BRRRR metrics
            refinance_ltv = 0.75
            refinance_amount = arv * refinance_ltv
            cash_left_in_deal = total_investment - refinance_amount
            brrrr_cash_on_cash = annual_cash_flow / max(cash_left_in_deal, 1) if cash_left_in_deal > 0 else float('inf')
            
            return {
                "financial_metrics": {
                    "purchase_price": purchase_price,
                    "repair_cost": repair_cost,
                    "total_investment": total_investment,
                    "after_repair_value": arv,
                    "down_payment": down_payment,
                    "loan_amount": loan_amount,
                    
                    # Monthly metrics
                    "monthly_rent": monthly_rent,
                    "monthly_mortgage": monthly_mortgage,
                    "monthly_expenses": total_monthly_expenses,
                    "monthly_cash_flow": monthly_cash_flow,
                    
                    # Annual metrics
                    "annual_cash_flow": annual_cash_flow,
                    "annual_rent": monthly_rent * 12,
                    
                    # Investment returns
                    "cap_rate": cap_rate,
                    "cash_on_cash_return": cash_on_cash_return,
                    "gross_rent_multiplier": gross_rent_multiplier,
                    
                    # Flip metrics
                    "flip_profit": flip_profit,
                    "flip_roi": flip_roi,
                    "flip_timeline_days": 90,
                    "selling_costs": selling_costs,
                    
                    # Wholesale metrics
                    "wholesale_fee": wholesale_fee,
                    "wholesale_margin": wholesale_margin,
                    
                    # BRRRR metrics
                    "refinance_amount": refinance_amount,
                    "cash_left_in_deal": cash_left_in_deal,
                    "brrrr_cash_on_cash": brrrr_cash_on_cash
                },
                "expense_breakdown": {
                    "monthly_mortgage": monthly_mortgage,
                    "insurance": insurance_monthly,
                    "property_tax": property_tax_monthly,
                    "vacancy_loss": vacancy_loss,
                    "management": management_cost,
                    "maintenance": maintenance_cost,
                    "capex": capex_cost
                },
                "assumptions": {
                    "down_payment_percentage": down_payment_percentage,
                    "interest_rate": interest_rate,
                    "loan_term_years": loan_term_years,
                    "vacancy_rate": vacancy_rate,
                    "management_fee": management_fee,
                    "maintenance_reserve": maintenance_reserve,
                    "capex_reserve": capex_reserve
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Financial calculator error: {e}")
            return {
                "financial_metrics": None,
                "error": str(e)
            }


class InvestmentStrategyAnalyzerTool(BaseAgentTool):
    """Tool for analyzing and comparing different investment strategies"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="investment_strategy_analyzer",
            description="Analyze and compare different real estate investment strategies",
            category=ToolCategory.ANALYSIS,
            access_level=ToolAccessLevel.RESTRICTED,
            allowed_agents=["analyst", "portfolio", "supervisor"],
            rate_limit=40,
            cost_per_call=0.20,
            timeout_seconds=45
        )
        super().__init__(metadata)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute investment strategy analysis"""
        financial_metrics = kwargs.get("financial_metrics", {})
        market_conditions = kwargs.get("market_conditions", {})
        investor_profile = kwargs.get("investor_profile", {})
        
        try:
            # Extract key metrics
            total_investment = financial_metrics.get("total_investment", 0)
            arv = financial_metrics.get("after_repair_value", 0)
            annual_cash_flow = financial_metrics.get("annual_cash_flow", 0)
            cap_rate = financial_metrics.get("cap_rate", 0)
            flip_profit = financial_metrics.get("flip_profit", 0)
            wholesale_fee = financial_metrics.get("wholesale_fee", 0)
            
            # Market factors
            market_temp = market_conditions.get("market_temperature", "warm")
            appreciation_rate = market_conditions.get("appreciation_forecast", 0.03)
            rental_demand = market_conditions.get("rental_demand", "moderate")
            
            strategies = []
            
            # Buy and Hold Rental Strategy
            rental_risk = 4.0
            if rental_demand == "high":
                rental_risk -= 1.0
            elif rental_demand == "low":
                rental_risk += 1.0
            
            if cap_rate > 0:
                rental_strategy = {
                    "strategy_type": "buy_and_hold_rental",
                    "potential_profit": annual_cash_flow,
                    "roi": financial_metrics.get("cash_on_cash_return", 0),
                    "risk_level": rental_risk,
                    "timeline_days": 30,
                    "funding_required": financial_metrics.get("down_payment", total_investment * 0.25),
                    "pros": [
                        "Steady monthly cash flow",
                        "Long-term appreciation potential",
                        "Tax benefits and depreciation",
                        "Hedge against inflation"
                    ],
                    "cons": [
                        "Property management responsibilities",
                        "Vacancy and tenant risks",
                        "Maintenance and repair costs",
                        "Market cycle exposure"
                    ],
                    "confidence_score": 0.85 if cap_rate >= 0.08 else 0.70,
                    "market_suitability": 0.8 if rental_demand in ["high", "moderate"] else 0.6
                }
                strategies.append(rental_strategy)
            
            # Fix and Flip Strategy
            flip_risk = 6.0
            if market_temp == "hot":
                flip_risk -= 1.0
            elif market_temp == "cold":
                flip_risk += 1.5
            
            if flip_profit > 0:
                flip_strategy = {
                    "strategy_type": "fix_and_flip",
                    "potential_profit": flip_profit,
                    "roi": financial_metrics.get("flip_roi", 0),
                    "risk_level": flip_risk,
                    "timeline_days": 90,
                    "funding_required": total_investment,
                    "pros": [
                        "Quick profit realization",
                        "No landlord responsibilities",
                        "Market appreciation upside",
                        "Creative and hands-on"
                    ],
                    "cons": [
                        "Market timing risk",
                        "Construction delays and overruns",
                        "Holding costs during renovation",
                        "Capital gains tax implications"
                    ],
                    "confidence_score": 0.75 if market_temp in ["hot", "warm"] else 0.60,
                    "market_suitability": 0.9 if market_temp == "hot" else 0.7 if market_temp == "warm" else 0.5
                }
                strategies.append(flip_strategy)
            
            # Wholesale Strategy
            if wholesale_fee > 0:
                wholesale_strategy = {
                    "strategy_type": "wholesale",
                    "potential_profit": wholesale_fee,
                    "roi": financial_metrics.get("wholesale_margin", 0),
                    "risk_level": 2.0,
                    "timeline_days": 14,
                    "funding_required": 1000,  # Earnest money
                    "pros": [
                        "Very low risk",
                        "Quick turnaround",
                        "No renovation required",
                        "Minimal capital required"
                    ],
                    "cons": [
                        "Lower profit margins",
                        "Requires strong buyer network",
                        "Market dependent",
                        "Reputation sensitive"
                    ],
                    "confidence_score": 0.90,
                    "market_suitability": 0.8
                }
                strategies.append(wholesale_strategy)
            
            # BRRRR Strategy
            if cap_rate > 0 and arv > total_investment:
                brrrr_strategy = {
                    "strategy_type": "brrrr",
                    "potential_profit": annual_cash_flow + (arv - total_investment),
                    "roi": financial_metrics.get("brrrr_cash_on_cash", 0),
                    "risk_level": 5.0,
                    "timeline_days": 120,
                    "funding_required": total_investment,
                    "pros": [
                        "Infinite return potential",
                        "Scale with recycled capital",
                        "Cash flow plus appreciation",
                        "Tax advantages"
                    ],
                    "cons": [
                        "Complex execution",
                        "Refinancing risks",
                        "Market timing sensitive",
                        "Higher management overhead"
                    ],
                    "confidence_score": 0.70,
                    "market_suitability": 0.75 if rental_demand in ["high", "moderate"] else 0.60
                }
                strategies.append(brrrr_strategy)
            
            # Rank strategies by risk-adjusted return
            for strategy in strategies:
                risk_adjusted_score = (
                    strategy["roi"] * strategy["confidence_score"] * strategy["market_suitability"] / 
                    max(strategy["risk_level"], 1)
                )
                strategy["risk_adjusted_score"] = risk_adjusted_score
            
            # Sort by risk-adjusted score
            strategies.sort(key=lambda x: x["risk_adjusted_score"], reverse=True)
            
            # Determine recommended strategy
            recommended_strategy = strategies[0]["strategy_type"] if strategies else None
            
            return {
                "strategies": strategies,
                "recommended_strategy": recommended_strategy,
                "strategy_count": len(strategies),
                "market_analysis": {
                    "market_temperature": market_temp,
                    "rental_demand": rental_demand,
                    "appreciation_forecast": appreciation_rate,
                    "strategy_favorability": {
                        "rental": 0.8 if rental_demand in ["high", "moderate"] else 0.6,
                        "flip": 0.9 if market_temp == "hot" else 0.7 if market_temp == "warm" else 0.5,
                        "wholesale": 0.8,
                        "brrrr": 0.75 if rental_demand in ["high", "moderate"] else 0.60
                    }
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Investment strategy analyzer error: {e}")
            return {
                "strategies": [],
                "recommended_strategy": None,
                "error": str(e)
            }


class RiskAssessmentTool(BaseAgentTool):
    """Tool for comprehensive investment risk assessment"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="risk_assessment_tool",
            description="Assess investment risks and generate confidence scores",
            category=ToolCategory.ANALYSIS,
            access_level=ToolAccessLevel.RESTRICTED,
            allowed_agents=["analyst", "portfolio", "supervisor"],
            rate_limit=60,
            cost_per_call=0.10,
            timeout_seconds=30
        )
        super().__init__(metadata)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute risk assessment"""
        property_data = kwargs.get("property_data", {})
        financial_metrics = kwargs.get("financial_metrics", {})
        market_conditions = kwargs.get("market_conditions", {})
        analysis_data = kwargs.get("analysis_data", {})
        
        try:
            risk_factors = []
            risk_scores = {}
            overall_risk_score = 5.0  # Base risk score (1-10 scale)
            
            # Financial Risk Assessment
            cap_rate = financial_metrics.get("cap_rate", 0)
            cash_flow = financial_metrics.get("monthly_cash_flow", 0)
            roi = financial_metrics.get("roi", 0)
            
            if cap_rate < 0.06:
                risk_factors.append("Low cap rate below market standards")
                risk_scores["financial"] = 7.0
                overall_risk_score += 1.0
            elif cap_rate < 0.08:
                risk_factors.append("Marginal cap rate")
                risk_scores["financial"] = 5.5
                overall_risk_score += 0.5
            else:
                risk_scores["financial"] = 3.0
            
            if cash_flow < 100:
                risk_factors.append("Low monthly cash flow")
                overall_risk_score += 1.0
            
            # Property Risk Assessment
            property_age = datetime.now().year - property_data.get("year_built", 1990)
            condition = property_data.get("condition", "fair")
            
            if property_age > 50:
                risk_factors.append("Older property with potential maintenance issues")
                risk_scores["property"] = 6.0
                overall_risk_score += 0.5
            elif property_age > 30:
                risk_scores["property"] = 4.5
            else:
                risk_scores["property"] = 3.0
            
            if condition in ["poor", "distressed"]:
                risk_factors.append("Property in poor condition requiring significant repairs")
                overall_risk_score += 1.5
            elif condition == "fair":
                overall_risk_score += 0.5
            
            # Market Risk Assessment
            market_temp = market_conditions.get("market_temperature", "warm")
            inventory_level = market_conditions.get("inventory_level", "normal")
            price_trend = market_conditions.get("price_change_yoy", 0)
            
            if market_temp == "cold":
                risk_factors.append("Cold market conditions may affect liquidity")
                risk_scores["market"] = 7.0
                overall_risk_score += 1.0
            elif market_temp == "hot":
                risk_factors.append("Hot market may indicate bubble conditions")
                risk_scores["market"] = 5.5
                overall_risk_score += 0.5
            else:
                risk_scores["market"] = 4.0
            
            if inventory_level == "high":
                risk_factors.append("High inventory may pressure prices")
                overall_risk_score += 0.5
            
            if price_trend < -0.05:
                risk_factors.append("Declining market prices")
                overall_risk_score += 1.0
            
            # Location Risk Assessment
            location_quality = property_data.get("location_quality", "average")
            neighborhood_trend = property_data.get("neighborhood_trend", "stable")
            
            if location_quality == "poor":
                risk_factors.append("Poor location may limit appreciation and rental demand")
                risk_scores["location"] = 7.0
                overall_risk_score += 1.0
            elif location_quality == "average":
                risk_scores["location"] = 4.5
            else:
                risk_scores["location"] = 3.0
            
            if neighborhood_trend == "declining":
                risk_factors.append("Declining neighborhood trend")
                overall_risk_score += 1.0
            
            # Liquidity Risk Assessment
            days_on_market = property_data.get("days_on_market", 30)
            property_type = property_data.get("property_type", "single_family")
            
            if days_on_market > 120:
                risk_factors.append("Extended time on market indicates potential issues")
                risk_scores["liquidity"] = 6.0
                overall_risk_score += 0.5
            elif days_on_market > 60:
                risk_scores["liquidity"] = 4.5
            else:
                risk_scores["liquidity"] = 3.0
            
            if property_type in ["commercial", "multi_family"]:
                risk_scores["liquidity"] = risk_scores.get("liquidity", 4.0) + 1.0
            
            # Financing Risk Assessment
            loan_amount = financial_metrics.get("loan_amount", 0)
            total_investment = financial_metrics.get("total_investment", 1)
            ltv = loan_amount / total_investment if total_investment > 0 else 0
            
            if ltv > 0.8:
                risk_factors.append("High loan-to-value ratio increases financing risk")
                risk_scores["financing"] = 6.5
                overall_risk_score += 0.5
            elif ltv > 0.75:
                risk_scores["financing"] = 4.5
            else:
                risk_scores["financing"] = 3.0
            
            # Calculate confidence score
            data_quality_factors = {
                "has_comps": len(analysis_data.get("comparable_properties", [])) >= 3,
                "recent_comps": True,  # Simplified
                "detailed_financials": bool(financial_metrics),
                "market_data": bool(market_conditions),
                "property_details": bool(property_data)
            }
            
            confidence_score = sum(data_quality_factors.values()) / len(data_quality_factors)
            
            # Adjust confidence based on risk factors
            if len(risk_factors) > 5:
                confidence_score *= 0.9
            elif len(risk_factors) > 3:
                confidence_score *= 0.95
            
            # Cap overall risk score
            overall_risk_score = min(10.0, overall_risk_score)
            
            return {
                "risk_assessment": {
                    "overall_risk_score": overall_risk_score,
                    "risk_level": (
                        "low" if overall_risk_score <= 3.0 else
                        "moderate" if overall_risk_score <= 5.0 else
                        "high" if overall_risk_score <= 7.0 else
                        "very_high"
                    ),
                    "confidence_score": confidence_score,
                    "risk_factors": risk_factors,
                    "risk_categories": risk_scores
                },
                "risk_breakdown": {
                    "financial_risk": risk_scores.get("financial", 5.0),
                    "property_risk": risk_scores.get("property", 5.0),
                    "market_risk": risk_scores.get("market", 5.0),
                    "location_risk": risk_scores.get("location", 5.0),
                    "liquidity_risk": risk_scores.get("liquidity", 5.0),
                    "financing_risk": risk_scores.get("financing", 5.0)
                },
                "mitigation_strategies": self._generate_mitigation_strategies(risk_factors),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Risk assessment error: {e}")
            return {
                "risk_assessment": None,
                "error": str(e)
            }
    
    def _generate_mitigation_strategies(self, risk_factors: List[str]) -> List[str]:
        """Generate risk mitigation strategies"""
        strategies = []
        
        for factor in risk_factors:
            if "cap rate" in factor.lower():
                strategies.append("Consider negotiating lower purchase price or higher rent")
            elif "cash flow" in factor.lower():
                strategies.append("Explore ways to increase rent or reduce expenses")
            elif "condition" in factor.lower():
                strategies.append("Get detailed inspection and contractor estimates")
            elif "market" in factor.lower():
                strategies.append("Monitor market trends and have exit strategy ready")
            elif "location" in factor.lower():
                strategies.append("Focus on properties in better neighborhoods")
            elif "time on market" in factor.lower():
                strategies.append("Investigate reasons for extended marketing time")
        
        return list(set(strategies))  # Remove duplicates


class MarketDataAnalysisTool(BaseAgentTool):
    """Tool for analyzing market data and trends"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="market_data_analysis",
            description="Analyze market data and trends for investment decisions",
            category=ToolCategory.ANALYSIS,
            access_level=ToolAccessLevel.RESTRICTED,
            allowed_agents=["analyst", "portfolio", "supervisor"],
            rate_limit=30,
            cost_per_call=0.20,
            timeout_seconds=45
        )
        super().__init__(metadata)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute market data analysis"""
        property_address = kwargs.get("property_address", "")
        property_type = kwargs.get("property_type", "single_family")
        zip_code = kwargs.get("zip_code", "")
        analysis_period = kwargs.get("analysis_period", 12)  # months
        
        try:
            # Simulate API call delay
            await asyncio.sleep(0.5)
            
            # Generate market analysis data
            current_date = datetime.now()
            
            # Price trend analysis
            price_trends = []
            base_price = 250000
            for i in range(analysis_period):
                month_date = current_date - timedelta(days=30 * i)
                price_change = random.uniform(-0.02, 0.03)  # -2% to +3% monthly
                price = base_price * (1 + price_change * i / 12)
                
                price_trends.append({
                    "date": month_date.strftime("%Y-%m"),
                    "median_price": price,
                    "price_change_mom": price_change,
                    "inventory_level": random.randint(2, 8),  # months of inventory
                    "days_on_market": random.randint(25, 90),
                    "sales_volume": random.randint(50, 200)
                })
            
            # Sort by date
            price_trends.sort(key=lambda x: x["date"])
            
            # Calculate trend metrics
            recent_prices = [trend["median_price"] for trend in price_trends[-6:]]
            older_prices = [trend["median_price"] for trend in price_trends[:6]]
            
            price_appreciation_6m = (sum(recent_prices) / len(recent_prices) - 
                                   sum(older_prices) / len(older_prices)) / sum(older_prices) * len(older_prices)
            
            # Market temperature assessment
            avg_dom = sum(trend["days_on_market"] for trend in price_trends[-3:]) / 3
            avg_inventory = sum(trend["inventory_level"] for trend in price_trends[-3:]) / 3
            
            if avg_dom < 30 and avg_inventory < 3:
                market_temperature = "hot"
            elif avg_dom > 60 or avg_inventory > 6:
                market_temperature = "cold"
            else:
                market_temperature = "warm"
            
            # Rental market analysis
            rental_data = {
                "median_rent": base_price * 0.008 + random.randint(-200, 300),
                "rent_growth_yoy": random.uniform(-0.05, 0.15),
                "vacancy_rate": random.uniform(0.02, 0.12),
                "rental_demand": random.choice(["low", "moderate", "high"]),
                "rent_to_price_ratio": 0.008 + random.uniform(-0.002, 0.004)
            }
            
            # Neighborhood analysis
            neighborhood_data = {
                "walkability_score": random.randint(40, 95),
                "school_rating": random.randint(4, 10),
                "crime_index": random.randint(20, 80),  # Lower is better
                "employment_growth": random.uniform(-0.03, 0.08),
                "population_growth": random.uniform(-0.02, 0.05),
                "median_income": random.randint(45000, 120000),
                "amenities_score": random.randint(50, 90)
            }
            
            # Investment attractiveness score
            attractiveness_factors = {
                "price_trend": 1.0 if price_appreciation_6m > 0.02 else 0.5 if price_appreciation_6m > 0 else 0.0,
                "market_temp": 0.8 if market_temperature == "warm" else 0.6 if market_temperature == "hot" else 0.4,
                "rental_demand": 1.0 if rental_data["rental_demand"] == "high" else 0.7 if rental_data["rental_demand"] == "moderate" else 0.3,
                "vacancy_rate": 1.0 if rental_data["vacancy_rate"] < 0.05 else 0.7 if rental_data["vacancy_rate"] < 0.08 else 0.4,
                "school_rating": neighborhood_data["school_rating"] / 10,
                "crime_safety": (100 - neighborhood_data["crime_index"]) / 100
            }
            
            investment_score = sum(attractiveness_factors.values()) / len(attractiveness_factors)
            
            # Market forecast
            forecast_months = 6
            forecast_data = []
            
            for i in range(1, forecast_months + 1):
                future_date = current_date + timedelta(days=30 * i)
                trend_factor = price_appreciation_6m / 6  # Monthly trend
                seasonal_factor = 0.02 * random.uniform(-1, 1)  # Seasonal variation
                
                forecast_price = price_trends[-1]["median_price"] * (1 + trend_factor + seasonal_factor)
                forecast_rent = rental_data["median_rent"] * (1 + rental_data["rent_growth_yoy"] / 12)
                
                forecast_data.append({
                    "date": future_date.strftime("%Y-%m"),
                    "predicted_price": forecast_price,
                    "predicted_rent": forecast_rent,
                    "confidence": max(0.5, 0.9 - (i * 0.1))  # Decreasing confidence over time
                })
            
            return {
                "market_analysis": {
                    "property_address": property_address,
                    "zip_code": zip_code,
                    "analysis_date": current_date.isoformat(),
                    "analysis_period_months": analysis_period,
                    
                    "price_trends": price_trends,
                    "price_appreciation_6m": price_appreciation_6m,
                    "market_temperature": market_temperature,
                    
                    "rental_market": rental_data,
                    "neighborhood_metrics": neighborhood_data,
                    
                    "investment_attractiveness": {
                        "overall_score": investment_score,
                        "score_breakdown": attractiveness_factors,
                        "recommendation": (
                            "strong_buy" if investment_score > 0.8 else
                            "buy" if investment_score > 0.6 else
                            "hold" if investment_score > 0.4 else
                            "avoid"
                        )
                    },
                    
                    "market_forecast": forecast_data,
                    
                    "key_insights": self._generate_market_insights(
                        market_temperature, price_appreciation_6m, rental_data, neighborhood_data
                    )
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Market data analysis error: {e}")
            return {
                "market_analysis": None,
                "error": str(e)
            }
    
    def _generate_market_insights(self, market_temp: str, price_trend: float, 
                                rental_data: Dict, neighborhood_data: Dict) -> List[str]:
        """Generate key market insights"""
        insights = []
        
        if market_temp == "hot":
            insights.append("Hot market conditions favor quick decisions and competitive offers")
        elif market_temp == "cold":
            insights.append("Cold market provides negotiation opportunities but may affect exit liquidity")
        
        if price_trend > 0.05:
            insights.append("Strong price appreciation indicates good investment timing")
        elif price_trend < -0.02:
            insights.append("Declining prices may signal market correction or opportunity")
        
        if rental_data["vacancy_rate"] < 0.05:
            insights.append("Low vacancy rates support strong rental income potential")
        elif rental_data["vacancy_rate"] > 0.10:
            insights.append("High vacancy rates may impact rental strategy viability")
        
        if neighborhood_data["school_rating"] >= 8:
            insights.append("Excellent schools support long-term property values and rental demand")
        
        if neighborhood_data["crime_index"] < 30:
            insights.append("Low crime area enhances property desirability and safety")
        elif neighborhood_data["crime_index"] > 60:
            insights.append("Higher crime rates may affect property values and rental demand")
        
        return insights


class AnalystToolManager:
    """Manager for coordinating all analyst tools"""
    
    def __init__(self):
        self.tools = {
            "comparable_property_finder": ComparablePropertyFinderTool(),
            "repair_cost_estimator": RepairCostEstimatorTool(),
            "financial_calculator": FinancialCalculatorTool(),
            "investment_strategy_analyzer": InvestmentStrategyAnalyzerTool(),
            "risk_assessment_tool": RiskAssessmentTool(),
            "market_data_analysis": MarketDataAnalysisTool()
        }
        
        self.usage_stats = {tool_name: {"calls": 0, "errors": 0} for tool_name in self.tools.keys()}
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a specific analyst tool"""
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Tool not found: {tool_name}",
                "available_tools": list(self.tools.keys())
            }
        
        try:
            self.usage_stats[tool_name]["calls"] += 1
            result = await self.tools[tool_name].execute(**kwargs)
            
            return {
                "success": True,
                "tool": tool_name,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.usage_stats[tool_name]["errors"] += 1
            logger.error(f"Analyst tool {tool_name} failed: {e}")
            
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """Get usage statistics for all tools"""
        return {
            "tools": list(self.tools.keys()),
            "usage_stats": self.usage_stats,
            "total_calls": sum(stats["calls"] for stats in self.usage_stats.values()),
            "total_errors": sum(stats["errors"] for stats in self.usage_stats.values())
        }
    
    def get_available_tools(self) -> List[str]:
        """Get list of available analyst tools"""
        return list(self.tools.keys())


# Register all analyst tools with the tool registry
def register_analyst_tools():
    """Register all analyst agent tools with the global tool registry"""
    try:
        try:
            from ..core.agent_tools import tool_registry
        except ImportError:
            from app.core.agent_tools import tool_registry
        
        analyst_tools = [
            ComparablePropertyFinderTool(),
            RepairCostEstimatorTool(),
            FinancialCalculatorTool(),
            InvestmentStrategyAnalyzerTool(),
            RiskAssessmentTool(),
            MarketDataAnalysisTool()
        ]
        
        for tool in analyst_tools:
            tool_registry.register_tool(tool)
        
        logger.info(f"Registered {len(analyst_tools)} analyst agent tools")
        return analyst_tools
    except Exception as e:
        logger.error(f"Failed to register analyst tools: {e}")
        return []


# Initialize analyst tool manager
try:
    analyst_tool_manager = AnalystToolManager()
except Exception as e:
    logger.error(f"Failed to initialize analyst tool manager: {e}")
    analyst_tool_manager = None

# Auto-register tools when module is imported (but don't fail if it doesn't work)
try:
    analyst_tools = register_analyst_tools()
except Exception as e:
    logger.error(f"Failed to auto-register analyst tools: {e}")
    analyst_tools = []