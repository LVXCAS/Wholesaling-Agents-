"""
Strategy Analysis API endpoints
Implements endpoints for investment strategy analysis including flip, rental, wholesale, and BRRRR strategies
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import logging
from datetime import datetime

from ...core.database import get_db
from ...models.property import PropertyDB
from ...agents.analyst_models import InvestmentStrategy, FinancialMetrics
from ...agents.analyst_agent import AnalystAgent
from ...core.agent_state import AgentState, StateManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize analyst agent for strategy analysis
analyst_agent = AnalystAgent()

@router.post("/{property_id}/flip", response_model=Dict[str, Any])
async def analyze_flip_strategy(
    property_id: uuid.UUID,
    purchase_price: Optional[float] = None,
    repair_budget: Optional[float] = None,
    holding_period_months: int = 6,
    db: Session = Depends(get_db)
):
    """
    Analyze flip investment strategy for a property
    
    - **property_id**: UUID of the property to analyze
    - **purchase_price**: Override purchase price (uses listing price if not provided)
    - **repair_budget**: Override repair budget (uses estimated repairs if not provided)
    - **holding_period_months**: Expected holding period in months
    - Returns detailed flip strategy analysis with profit projections and timeline
    """
    try:
        # Get property from database
        property_record = db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
        
        if not property_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Prepare deal data for strategy analysis
        deal_data = {
            "id": str(property_record.id),
            "property": {
                "address": property_record.address,
                "city": property_record.city,
                "state": property_record.state,
                "property_type": property_record.property_type,
                "square_feet": property_record.square_feet or 1500,
                "bedrooms": property_record.bedrooms,
                "bathrooms": property_record.bathrooms,
                "year_built": property_record.year_built,
                "listing_price": purchase_price or property_record.listing_price,
                "current_value": property_record.current_value,
                "condition_score": property_record.condition_score
            },
            "strategy_type": "flip",
            "parameters": {
                "purchase_price": purchase_price or property_record.listing_price,
                "repair_budget": repair_budget,
                "holding_period_months": holding_period_months,
                "target_profit_margin": 0.20  # 20% profit margin
            }
        }
        
        # Create agent state
        state = StateManager.create_initial_state()
        
        # First get property valuation and repair estimate if not provided
        if not repair_budget:
            repair_result = await analyst_agent.execute_task("estimate_repairs", {"deal": deal_data}, state)
            if repair_result.get("success", False):
                repair_budget = repair_result.get("repair_estimate", {}).get("total_cost", 50000)
                deal_data["parameters"]["repair_budget"] = repair_budget
        
        # Get property valuation for ARV
        valuation_result = await analyst_agent.execute_task("valuate_property", {"deal": deal_data}, state)
        if not valuation_result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get property valuation for flip analysis"
            )
        
        valuation_data = valuation_result.get("data", {}).get("valuation", {})
        arv = valuation_data.get("arv", property_record.current_value or 300000)
        
        # Calculate flip strategy metrics
        purchase_price_final = purchase_price or property_record.listing_price or 250000
        repair_cost_final = repair_budget or 50000
        total_investment = purchase_price_final + repair_cost_final
        
        # Flip costs (closing, holding, selling costs)
        closing_costs = purchase_price_final * 0.03  # 3% closing costs
        holding_costs = (purchase_price_final * 0.01) * (holding_period_months / 12)  # 1% annual holding
        selling_costs = arv * 0.08  # 8% selling costs (agent, closing, etc.)
        total_costs = closing_costs + holding_costs + selling_costs
        
        # Calculate profit and returns
        gross_profit = arv - total_investment
        net_profit = gross_profit - total_costs
        roi = (net_profit / total_investment) * 100 if total_investment > 0 else 0
        profit_margin = (net_profit / arv) * 100 if arv > 0 else 0
        
        # Risk assessment
        risk_factors = []
        risk_score = 5.0  # Base risk score
        
        if profit_margin < 15:
            risk_factors.append("Low profit margin")
            risk_score += 1.5
        
        if holding_period_months > 12:
            risk_factors.append("Extended holding period")
            risk_score += 1.0
        
        if repair_cost_final > (purchase_price_final * 0.3):
            risk_factors.append("High repair costs relative to purchase price")
            risk_score += 1.0
        
        if property_record.condition_score and property_record.condition_score < 0.6:
            risk_factors.append("Poor property condition")
            risk_score += 0.5
        
        # Confidence score based on data quality and market conditions
        confidence_score = 0.8
        if valuation_data.get("confidence_score"):
            confidence_score = min(confidence_score, valuation_data["confidence_score"])
        
        # Create strategy analysis result
        flip_strategy = {
            "strategy_type": "flip",
            "financial_analysis": {
                "purchase_price": purchase_price_final,
                "repair_costs": repair_cost_final,
                "total_investment": total_investment,
                "after_repair_value": arv,
                "closing_costs": closing_costs,
                "holding_costs": holding_costs,
                "selling_costs": selling_costs,
                "total_costs": total_costs,
                "gross_profit": gross_profit,
                "net_profit": net_profit,
                "roi_percentage": roi,
                "profit_margin_percentage": profit_margin
            },
            "timeline": {
                "acquisition_days": 30,
                "renovation_days": holding_period_months * 20,  # Rough estimate
                "marketing_days": 45,
                "total_timeline_days": 30 + (holding_period_months * 20) + 45
            },
            "risk_assessment": {
                "risk_factors": risk_factors,
                "risk_score": min(risk_score, 10.0),
                "confidence_score": confidence_score
            },
            "recommendation": {
                "proceed": net_profit > 20000 and roi > 15 and risk_score < 7,
                "reason": _generate_flip_recommendation_reason(net_profit, roi, risk_score),
                "key_metrics": {
                    "min_profit_threshold": 20000,
                    "min_roi_threshold": 15,
                    "max_risk_threshold": 7
                }
            }
        }
        
        logger.info(f"Completed flip strategy analysis for property: {property_id}")
        
        return {
            "property_id": str(property_id),
            "strategy": flip_strategy,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing flip strategy for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze flip strategy: {str(e)}"
        )

@router.post("/{property_id}/rental", response_model=Dict[str, Any])
async def analyze_rental_strategy(
    property_id: uuid.UUID,
    purchase_price: Optional[float] = None,
    down_payment_percentage: float = 0.25,
    interest_rate: float = 0.07,
    loan_term_years: int = 30,
    db: Session = Depends(get_db)
):
    """
    Analyze rental investment strategy for a property
    
    - **property_id**: UUID of the property to analyze
    - **purchase_price**: Override purchase price (uses listing price if not provided)
    - **down_payment_percentage**: Down payment as percentage of purchase price
    - **interest_rate**: Annual interest rate for financing
    - **loan_term_years**: Loan term in years
    - Returns detailed rental strategy analysis with cash flow projections and cap rate
    """
    try:
        # Get property from database
        property_record = db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
        
        if not property_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Prepare deal data
        deal_data = {
            "id": str(property_record.id),
            "property": {
                "address": property_record.address,
                "city": property_record.city,
                "state": property_record.state,
                "property_type": property_record.property_type,
                "square_feet": property_record.square_feet or 1500,
                "bedrooms": property_record.bedrooms or 3,
                "bathrooms": property_record.bathrooms or 2,
                "listing_price": purchase_price or property_record.listing_price
            },
            "strategy_type": "rental"
        }
        
        # Create agent state
        state = StateManager.create_initial_state()
        
        # Estimate rental income using market data
        from ...agents.analyst_tools import RentalEstimatorTool
        rental_estimator = RentalEstimatorTool()
        
        rental_result = await rental_estimator.execute(
            property_type=property_record.property_type,
            bedrooms=property_record.bedrooms or 3,
            bathrooms=property_record.bathrooms or 2,
            square_feet=property_record.square_feet or 1500,
            city=property_record.city,
            state=property_record.state,
            zip_code=property_record.zip_code
        )
        
        if not rental_result.get("success", False):
            # Use fallback rental estimate
            monthly_rent = (property_record.current_value or 300000) * 0.01  # 1% rule fallback
        else:
            monthly_rent = rental_result.get("monthly_rent_estimate", 2500)
        
        # Calculate financing
        purchase_price_final = purchase_price or property_record.listing_price or 300000
        down_payment = purchase_price_final * down_payment_percentage
        loan_amount = purchase_price_final - down_payment
        
        # Monthly mortgage payment calculation
        monthly_rate = interest_rate / 12
        num_payments = loan_term_years * 12
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
        
        # Operating expenses
        property_taxes = (property_record.tax_amount or purchase_price_final * 0.012) / 12  # Monthly
        insurance = purchase_price_final * 0.003 / 12  # 0.3% annually
        maintenance = monthly_rent * 0.05  # 5% of rent
        vacancy_allowance = monthly_rent * 0.05  # 5% vacancy
        management_fee = monthly_rent * 0.08  # 8% management
        capex_reserve = monthly_rent * 0.05  # 5% capital expenditures
        
        total_expenses = monthly_payment + property_taxes + insurance + maintenance + vacancy_allowance + management_fee + capex_reserve
        
        # Cash flow calculations
        monthly_cash_flow = monthly_rent - total_expenses
        annual_cash_flow = monthly_cash_flow * 12
        
        # Return calculations
        cash_invested = down_payment + (purchase_price_final * 0.03)  # Include closing costs
        cash_on_cash_return = (annual_cash_flow / cash_invested) * 100 if cash_invested > 0 else 0
        cap_rate = ((monthly_rent * 12) - (total_expenses * 12 - monthly_payment * 12)) / purchase_price_final * 100
        
        # Risk assessment
        risk_factors = []
        risk_score = 4.0  # Base risk score for rentals
        
        if monthly_cash_flow < 100:
            risk_factors.append("Low monthly cash flow")
            risk_score += 1.5
        
        if cap_rate < 6:
            risk_factors.append("Low cap rate")
            risk_score += 1.0
        
        if cash_on_cash_return < 8:
            risk_factors.append("Low cash-on-cash return")
            risk_score += 1.0
        
        if property_record.crime_score and property_record.crime_score > 70:
            risk_factors.append("High crime area")
            risk_score += 0.5
        
        # Create rental strategy result
        rental_strategy = {
            "strategy_type": "rental",
            "financial_analysis": {
                "purchase_price": purchase_price_final,
                "down_payment": down_payment,
                "loan_amount": loan_amount,
                "cash_invested": cash_invested,
                "monthly_rent": monthly_rent,
                "monthly_expenses": {
                    "mortgage_payment": monthly_payment,
                    "property_taxes": property_taxes,
                    "insurance": insurance,
                    "maintenance": maintenance,
                    "vacancy_allowance": vacancy_allowance,
                    "management_fee": management_fee,
                    "capex_reserve": capex_reserve,
                    "total": total_expenses
                },
                "monthly_cash_flow": monthly_cash_flow,
                "annual_cash_flow": annual_cash_flow,
                "cap_rate_percentage": cap_rate,
                "cash_on_cash_return_percentage": cash_on_cash_return
            },
            "financing_details": {
                "down_payment_percentage": down_payment_percentage * 100,
                "interest_rate_percentage": interest_rate * 100,
                "loan_term_years": loan_term_years,
                "monthly_payment": monthly_payment
            },
            "risk_assessment": {
                "risk_factors": risk_factors,
                "risk_score": min(risk_score, 10.0),
                "confidence_score": 0.85
            },
            "recommendation": {
                "proceed": monthly_cash_flow > 100 and cap_rate > 6 and cash_on_cash_return > 8,
                "reason": _generate_rental_recommendation_reason(monthly_cash_flow, cap_rate, cash_on_cash_return),
                "key_metrics": {
                    "min_cash_flow_threshold": 100,
                    "min_cap_rate_threshold": 6,
                    "min_coc_return_threshold": 8
                }
            }
        }
        
        logger.info(f"Completed rental strategy analysis for property: {property_id}")
        
        return {
            "property_id": str(property_id),
            "strategy": rental_strategy,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing rental strategy for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze rental strategy: {str(e)}"
        )

@router.post("/{property_id}/wholesale", response_model=Dict[str, Any])
async def analyze_wholesale_strategy(
    property_id: uuid.UUID,
    contract_price: Optional[float] = None,
    wholesale_fee: Optional[float] = None,
    assignment_timeline_days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Analyze wholesale investment strategy for a property
    
    - **property_id**: UUID of the property to analyze
    - **contract_price**: Contract price with seller (uses listing price if not provided)
    - **wholesale_fee**: Wholesale assignment fee (calculated if not provided)
    - **assignment_timeline_days**: Expected timeline to assign contract
    - Returns detailed wholesale strategy analysis with profit projections and assignment potential
    """
    try:
        # Get property from database
        property_record = db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
        
        if not property_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Prepare deal data
        deal_data = {
            "id": str(property_record.id),
            "property": {
                "address": property_record.address,
                "city": property_record.city,
                "state": property_record.state,
                "property_type": property_record.property_type,
                "listing_price": contract_price or property_record.listing_price,
                "current_value": property_record.current_value
            }
        }
        
        # Create agent state
        state = StateManager.create_initial_state()
        
        # Get property valuation for ARV
        valuation_result = await analyst_agent.execute_task("valuate_property", {"deal": deal_data}, state)
        if not valuation_result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get property valuation for wholesale analysis"
            )
        
        valuation_data = valuation_result.get("data", {}).get("valuation", {})
        arv = valuation_data.get("arv", property_record.current_value or 300000)
        
        # Get repair estimate
        repair_result = await analyst_agent.execute_task("estimate_repairs", {"deal": deal_data}, state)
        repair_cost = 50000  # Default
        if repair_result.get("success", False):
            repair_cost = repair_result.get("repair_estimate", {}).get("total_cost", 50000)
        
        # Calculate wholesale metrics
        contract_price_final = contract_price or property_record.listing_price or 200000
        
        # Calculate maximum allowable offer (MAO) for end buyer
        # Typically 70% of ARV minus repairs
        mao = (arv * 0.70) - repair_cost
        
        # Calculate wholesale fee
        if wholesale_fee is None:
            # Wholesale fee is typically the spread between contract price and MAO
            wholesale_fee = max(mao - contract_price_final, 5000)  # Minimum $5k fee
        
        # Calculate margins and returns
        profit_margin = (wholesale_fee / contract_price_final) * 100 if contract_price_final > 0 else 0
        roi_annualized = (wholesale_fee / contract_price_final) * (365 / assignment_timeline_days) * 100 if contract_price_final > 0 and assignment_timeline_days > 0 else 0
        
        # Risk assessment
        risk_factors = []
        risk_score = 6.0  # Base risk score for wholesale
        
        if wholesale_fee < 10000:
            risk_factors.append("Low wholesale fee")
            risk_score += 1.0
        
        if profit_margin < 5:
            risk_factors.append("Low profit margin")
            risk_score += 1.5
        
        if assignment_timeline_days > 45:
            risk_factors.append("Extended assignment timeline")
            risk_score += 1.0
        
        if contract_price_final > (arv * 0.8):
            risk_factors.append("High contract price relative to ARV")
            risk_score += 2.0
        
        # Market factors
        market_demand_score = 0.8  # Placeholder - would come from market analysis
        if market_demand_score < 0.6:
            risk_factors.append("Low market demand for investment properties")
            risk_score += 1.0
        
        # Create wholesale strategy result
        wholesale_strategy = {
            "strategy_type": "wholesale",
            "financial_analysis": {
                "contract_price": contract_price_final,
                "after_repair_value": arv,
                "estimated_repairs": repair_cost,
                "maximum_allowable_offer": mao,
                "wholesale_fee": wholesale_fee,
                "profit_margin_percentage": profit_margin,
                "roi_annualized_percentage": roi_annualized,
                "spread_analysis": {
                    "arv_to_contract_ratio": (contract_price_final / arv) * 100 if arv > 0 else 0,
                    "fee_to_arv_ratio": (wholesale_fee / arv) * 100 if arv > 0 else 0
                }
            },
            "timeline": {
                "contract_execution_days": 3,
                "marketing_days": assignment_timeline_days - 10,
                "assignment_closing_days": 7,
                "total_timeline_days": assignment_timeline_days
            },
            "market_analysis": {
                "investor_demand_score": market_demand_score,
                "comparable_wholesale_fees": {
                    "low": wholesale_fee * 0.7,
                    "average": wholesale_fee,
                    "high": wholesale_fee * 1.3
                }
            },
            "risk_assessment": {
                "risk_factors": risk_factors,
                "risk_score": min(risk_score, 10.0),
                "confidence_score": 0.75
            },
            "recommendation": {
                "proceed": wholesale_fee > 10000 and profit_margin > 5 and risk_score < 8,
                "reason": _generate_wholesale_recommendation_reason(wholesale_fee, profit_margin, risk_score),
                "key_metrics": {
                    "min_fee_threshold": 10000,
                    "min_margin_threshold": 5,
                    "max_risk_threshold": 8
                }
            }
        }
        
        logger.info(f"Completed wholesale strategy analysis for property: {property_id}")
        
        return {
            "property_id": str(property_id),
            "strategy": wholesale_strategy,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing wholesale strategy for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze wholesale strategy: {str(e)}"
        )

@router.post("/{property_id}/brrrr", response_model=Dict[str, Any])
async def analyze_brrrr_strategy(
    property_id: uuid.UUID,
    purchase_price: Optional[float] = None,
    repair_budget: Optional[float] = None,
    refinance_ltv: float = 0.75,
    refinance_rate: float = 0.07,
    db: Session = Depends(get_db)
):
    """
    Analyze BRRRR (Buy, Rehab, Rent, Refinance, Repeat) investment strategy
    
    - **property_id**: UUID of the property to analyze
    - **purchase_price**: Override purchase price (uses listing price if not provided)
    - **repair_budget**: Override repair budget (uses estimated repairs if not provided)
    - **refinance_ltv**: Loan-to-value ratio for refinancing (typically 75%)
    - **refinance_rate**: Interest rate for refinance loan
    - Returns detailed BRRRR strategy analysis with cash recovery and infinite return potential
    """
    try:
        # Get property from database
        property_record = db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
        
        if not property_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Prepare deal data
        deal_data = {
            "id": str(property_record.id),
            "property": {
                "address": property_record.address,
                "city": property_record.city,
                "state": property_record.state,
                "property_type": property_record.property_type,
                "square_feet": property_record.square_feet or 1500,
                "bedrooms": property_record.bedrooms or 3,
                "bathrooms": property_record.bathrooms or 2,
                "listing_price": purchase_price or property_record.listing_price
            }
        }
        
        # Create agent state
        state = StateManager.create_initial_state()
        
        # Get property valuation for ARV
        valuation_result = await analyst_agent.execute_task("valuate_property", {"deal": deal_data}, state)
        if not valuation_result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get property valuation for BRRRR analysis"
            )
        
        valuation_data = valuation_result.get("data", {}).get("valuation", {})
        arv = valuation_data.get("arv", property_record.current_value or 300000)
        
        # Get repair estimate if not provided
        if not repair_budget:
            repair_result = await analyst_agent.execute_task("estimate_repairs", {"deal": deal_data}, state)
            if repair_result.get("success", False):
                repair_budget = repair_result.get("repair_estimate", {}).get("total_cost", 50000)
            else:
                repair_budget = 50000
        
        # Calculate BRRRR metrics
        purchase_price_final = purchase_price or property_record.listing_price or 200000
        total_investment = purchase_price_final + repair_budget
        
        # Refinance calculations
        refinance_amount = arv * refinance_ltv
        cash_recovered = refinance_amount - total_investment
        cash_left_in_deal = max(0, total_investment - refinance_amount)
        
        # Rental analysis (reuse rental calculation logic)
        from ...agents.analyst_tools import RentalEstimatorTool
        rental_estimator = RentalEstimatorTool()
        
        rental_result = await rental_estimator.execute(
            property_type=property_record.property_type,
            bedrooms=property_record.bedrooms or 3,
            bathrooms=property_record.bathrooms or 2,
            square_feet=property_record.square_feet or 1500,
            city=property_record.city,
            state=property_record.state,
            zip_code=property_record.zip_code
        )
        
        monthly_rent = rental_result.get("monthly_rent_estimate", 2500) if rental_result.get("success") else arv * 0.01
        
        # Calculate new mortgage payment after refinance
        monthly_rate = refinance_rate / 12
        num_payments = 30 * 12  # 30-year loan
        monthly_payment = refinance_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
        
        # Operating expenses (similar to rental analysis)
        property_taxes = (property_record.tax_amount or arv * 0.012) / 12
        insurance = arv * 0.003 / 12
        maintenance = monthly_rent * 0.05
        vacancy_allowance = monthly_rent * 0.05
        management_fee = monthly_rent * 0.08
        capex_reserve = monthly_rent * 0.05
        
        total_expenses = monthly_payment + property_taxes + insurance + maintenance + vacancy_allowance + management_fee + capex_reserve
        monthly_cash_flow = monthly_rent - total_expenses
        annual_cash_flow = monthly_cash_flow * 12
        
        # Return calculations
        if cash_left_in_deal > 0:
            cash_on_cash_return = (annual_cash_flow / cash_left_in_deal) * 100
        else:
            cash_on_cash_return = float('inf')  # Infinite return if no cash left in deal
        
        # Risk assessment
        risk_factors = []
        risk_score = 5.5  # Base risk score for BRRRR
        
        if cash_recovered < 0:
            risk_factors.append("Negative cash recovery - additional capital required")
            risk_score += 2.0
        
        if monthly_cash_flow < 100:
            risk_factors.append("Low monthly cash flow after refinance")
            risk_score += 1.5
        
        if refinance_amount > (arv * 0.8):
            risk_factors.append("High refinance LTV may be difficult to obtain")
            risk_score += 1.0
        
        if repair_budget > (purchase_price_final * 0.4):
            risk_factors.append("High repair costs relative to purchase price")
            risk_score += 1.0
        
        # Create BRRRR strategy result
        brrrr_strategy = {
            "strategy_type": "brrrr",
            "financial_analysis": {
                "purchase_price": purchase_price_final,
                "repair_costs": repair_budget,
                "total_investment": total_investment,
                "after_repair_value": arv,
                "refinance_amount": refinance_amount,
                "cash_recovered": cash_recovered,
                "cash_left_in_deal": cash_left_in_deal,
                "monthly_rent": monthly_rent,
                "monthly_expenses": total_expenses,
                "monthly_cash_flow": monthly_cash_flow,
                "annual_cash_flow": annual_cash_flow,
                "cash_on_cash_return_percentage": cash_on_cash_return if cash_on_cash_return != float('inf') else 999,
                "infinite_return": cash_left_in_deal == 0
            },
            "refinance_details": {
                "refinance_ltv_percentage": refinance_ltv * 100,
                "refinance_rate_percentage": refinance_rate * 100,
                "new_monthly_payment": monthly_payment,
                "loan_amount": refinance_amount
            },
            "timeline": {
                "acquisition_days": 30,
                "renovation_days": 90,
                "rent_up_days": 30,
                "refinance_days": 45,
                "total_timeline_days": 195
            },
            "risk_assessment": {
                "risk_factors": risk_factors,
                "risk_score": min(risk_score, 10.0),
                "confidence_score": 0.80
            },
            "recommendation": {
                "proceed": cash_recovered >= 0 and monthly_cash_flow > 100 and risk_score < 8,
                "reason": _generate_brrrr_recommendation_reason(cash_recovered, monthly_cash_flow, risk_score),
                "key_metrics": {
                    "min_cash_recovery_threshold": 0,
                    "min_cash_flow_threshold": 100,
                    "max_risk_threshold": 8
                }
            }
        }
        
        logger.info(f"Completed BRRRR strategy analysis for property: {property_id}")
        
        return {
            "property_id": str(property_id),
            "strategy": brrrr_strategy,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing BRRRR strategy for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze BRRRR strategy: {str(e)}"
        )

@router.post("/{property_id}/compare-strategies", response_model=Dict[str, Any])
async def compare_investment_strategies(
    property_id: uuid.UUID,
    purchase_price: Optional[float] = None,
    include_strategies: List[str] = ["flip", "rental", "wholesale", "brrrr"],
    db: Session = Depends(get_db)
):
    """
    Compare multiple investment strategies for a property
    
    - **property_id**: UUID of the property to analyze
    - **purchase_price**: Override purchase price for all strategies
    - **include_strategies**: List of strategies to compare (flip, rental, wholesale, brrrr)
    - Returns comparison of all requested strategies with recommendations
    """
    try:
        # Get property from database
        property_record = db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
        
        if not property_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        strategies_results = {}
        
        # Analyze each requested strategy
        for strategy in include_strategies:
            try:
                if strategy == "flip":
                    result = await analyze_flip_strategy(property_id, purchase_price, db=db)
                    strategies_results["flip"] = result["strategy"]
                elif strategy == "rental":
                    result = await analyze_rental_strategy(property_id, purchase_price, db=db)
                    strategies_results["rental"] = result["strategy"]
                elif strategy == "wholesale":
                    result = await analyze_wholesale_strategy(property_id, purchase_price, db=db)
                    strategies_results["wholesale"] = result["strategy"]
                elif strategy == "brrrr":
                    result = await analyze_brrrr_strategy(property_id, purchase_price, db=db)
                    strategies_results["brrrr"] = result["strategy"]
                else:
                    logger.warning(f"Unknown strategy: {strategy}")
                    
            except Exception as e:
                logger.error(f"Error analyzing {strategy} strategy: {e}")
                strategies_results[strategy] = {"error": str(e)}
        
        # Compare strategies and make recommendation
        comparison = _compare_strategies(strategies_results)
        
        logger.info(f"Completed strategy comparison for property: {property_id}")
        
        return {
            "property_id": str(property_id),
            "strategies": strategies_results,
            "comparison": comparison,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing strategies for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare investment strategies: {str(e)}"
        )

# Helper functions for generating recommendations

def _generate_flip_recommendation_reason(net_profit: float, roi: float, risk_score: float) -> str:
    """Generate recommendation reason for flip strategy"""
    if net_profit > 20000 and roi > 15 and risk_score < 7:
        return f"Strong flip opportunity with ${net_profit:,.0f} profit and {roi:.1f}% ROI"
    elif net_profit < 10000:
        return f"Low profit potential (${net_profit:,.0f}) makes this flip less attractive"
    elif roi < 10:
        return f"Low ROI ({roi:.1f}%) relative to risk and effort required"
    elif risk_score > 7:
        return f"High risk score ({risk_score:.1f}) indicates significant challenges"
    else:
        return "Marginal flip opportunity - proceed with caution"

def _generate_rental_recommendation_reason(cash_flow: float, cap_rate: float, coc_return: float) -> str:
    """Generate recommendation reason for rental strategy"""
    if cash_flow > 100 and cap_rate > 6 and coc_return > 8:
        return f"Solid rental investment with ${cash_flow:.0f} monthly cash flow and {cap_rate:.1f}% cap rate"
    elif cash_flow < 50:
        return f"Low cash flow (${cash_flow:.0f}) may not cover unexpected expenses"
    elif cap_rate < 5:
        return f"Low cap rate ({cap_rate:.1f}%) indicates overpriced property for rental"
    elif coc_return < 6:
        return f"Low cash-on-cash return ({coc_return:.1f}%) - consider other investments"
    else:
        return "Marginal rental opportunity - analyze local market conditions carefully"

def _generate_wholesale_recommendation_reason(fee: float, margin: float, risk_score: float) -> str:
    """Generate recommendation reason for wholesale strategy"""
    if fee > 10000 and margin > 5 and risk_score < 8:
        return f"Good wholesale opportunity with ${fee:,.0f} fee and {margin:.1f}% margin"
    elif fee < 5000:
        return f"Low wholesale fee (${fee:,.0f}) may not justify time and effort"
    elif margin < 3:
        return f"Thin profit margin ({margin:.1f}%) leaves little room for error"
    elif risk_score > 8:
        return f"High risk score ({risk_score:.1f}) indicates assignment challenges"
    else:
        return "Marginal wholesale opportunity - ensure strong buyer network"

def _generate_brrrr_recommendation_reason(cash_recovered: float, cash_flow: float, risk_score: float) -> str:
    """Generate recommendation reason for BRRRR strategy"""
    if cash_recovered >= 0 and cash_flow > 100 and risk_score < 8:
        return f"Excellent BRRRR opportunity with ${cash_recovered:,.0f} cash recovery and ${cash_flow:.0f} monthly cash flow"
    elif cash_recovered < -20000:
        return f"Significant additional capital required (${abs(cash_recovered):,.0f}) for refinance"
    elif cash_flow < 50:
        return f"Low cash flow (${cash_flow:.0f}) after refinance may not be sustainable"
    elif risk_score > 8:
        return f"High risk score ({risk_score:.1f}) indicates execution challenges"
    else:
        return "Marginal BRRRR opportunity - verify refinance assumptions carefully"

def _compare_strategies(strategies: Dict[str, Any]) -> Dict[str, Any]:
    """Compare strategies and provide overall recommendation"""
    valid_strategies = {k: v for k, v in strategies.items() if "error" not in v}
    
    if not valid_strategies:
        return {"error": "No valid strategies to compare"}
    
    # Extract key metrics for comparison
    comparison_metrics = {}
    
    for strategy_name, strategy_data in valid_strategies.items():
        financial = strategy_data.get("financial_analysis", {})
        risk = strategy_data.get("risk_assessment", {})
        recommendation = strategy_data.get("recommendation", {})
        
        if strategy_name == "flip":
            comparison_metrics[strategy_name] = {
                "profit": financial.get("net_profit", 0),
                "roi": financial.get("roi_percentage", 0),
                "timeline_days": strategy_data.get("timeline", {}).get("total_timeline_days", 365),
                "risk_score": risk.get("risk_score", 10),
                "proceed": recommendation.get("proceed", False)
            }
        elif strategy_name == "rental":
            comparison_metrics[strategy_name] = {
                "annual_cash_flow": financial.get("annual_cash_flow", 0),
                "coc_return": financial.get("cash_on_cash_return_percentage", 0),
                "cap_rate": financial.get("cap_rate_percentage", 0),
                "risk_score": risk.get("risk_score", 10),
                "proceed": recommendation.get("proceed", False)
            }
        elif strategy_name == "wholesale":
            comparison_metrics[strategy_name] = {
                "profit": financial.get("wholesale_fee", 0),
                "roi_annualized": financial.get("roi_annualized_percentage", 0),
                "timeline_days": strategy_data.get("timeline", {}).get("total_timeline_days", 30),
                "risk_score": risk.get("risk_score", 10),
                "proceed": recommendation.get("proceed", False)
            }
        elif strategy_name == "brrrr":
            comparison_metrics[strategy_name] = {
                "cash_recovered": financial.get("cash_recovered", 0),
                "annual_cash_flow": financial.get("annual_cash_flow", 0),
                "coc_return": financial.get("cash_on_cash_return_percentage", 0),
                "risk_score": risk.get("risk_score", 10),
                "proceed": recommendation.get("proceed", False)
            }
    
    # Determine best strategy
    recommended_strategies = [k for k, v in comparison_metrics.items() if v.get("proceed", False)]
    
    if recommended_strategies:
        # Score strategies based on multiple factors
        strategy_scores = {}
        for strategy in recommended_strategies:
            metrics = comparison_metrics[strategy]
            score = 0
            
            # Lower risk is better
            score += (10 - metrics.get("risk_score", 10)) * 10
            
            # Strategy-specific scoring
            if strategy == "flip":
                score += min(metrics.get("roi", 0), 50) * 2  # Cap at 50% ROI
            elif strategy == "rental":
                score += min(metrics.get("coc_return", 0), 20) * 3  # Cap at 20% COC
                score += min(metrics.get("cap_rate", 0), 15) * 2  # Cap at 15% cap rate
            elif strategy == "wholesale":
                score += min(metrics.get("roi_annualized", 0), 100) * 1  # Cap at 100% annualized
            elif strategy == "brrrr":
                score += min(metrics.get("coc_return", 0), 30) * 2  # Cap at 30% COC
                if metrics.get("cash_recovered", 0) > 0:
                    score += 20  # Bonus for positive cash recovery
            
            strategy_scores[strategy] = score
        
        best_strategy = max(strategy_scores.items(), key=lambda x: x[1])
        
        return {
            "recommended_strategy": best_strategy[0],
            "strategy_scores": strategy_scores,
            "viable_strategies": recommended_strategies,
            "comparison_summary": {
                strategy: {
                    "score": strategy_scores.get(strategy, 0),
                    "key_metrics": comparison_metrics[strategy]
                }
                for strategy in valid_strategies.keys()
            }
        }
    else:
        return {
            "recommended_strategy": None,
            "reason": "No strategies meet minimum investment criteria",
            "comparison_summary": {
                strategy: {
                    "key_metrics": comparison_metrics[strategy]
                }
                for strategy in valid_strategies.keys()
            }
        }

# Create RentalEstimatorTool if it doesn't exist
class RentalEstimatorTool:
    """Tool for estimating rental income"""
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute rental estimation"""
        property_type = kwargs.get("property_type", "single_family")
        bedrooms = kwargs.get("bedrooms", 3)
        bathrooms = kwargs.get("bathrooms", 2)
        square_feet = kwargs.get("square_feet", 1500)
        city = kwargs.get("city", "")
        state = kwargs.get("state", "")
        
        # Simple rental estimation logic (would be replaced with real market data)
        base_rent = square_feet * 1.2  # $1.20 per sq ft base
        
        # Adjust for bedrooms/bathrooms
        if bedrooms >= 4:
            base_rent *= 1.1
        if bathrooms >= 3:
            base_rent *= 1.05
        
        # Property type adjustments
        if property_type == "multi_family":
            base_rent *= 0.9
        elif property_type == "condo":
            base_rent *= 1.1
        
        # Add some randomness for realism
        import random
        base_rent *= random.uniform(0.9, 1.1)
        
        return {
            "success": True,
            "monthly_rent_estimate": round(base_rent, 0),
            "confidence_score": 0.8,
            "data_sources": ["market_analysis", "comparable_rentals"]
        }