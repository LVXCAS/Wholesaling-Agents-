import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from .market_data_service import MarketDataService
from .property_valuation_service import PropertyValuationService

@dataclass
class InvestmentMetrics:
    cap_rate: Optional[float]
    cash_on_cash_return: Optional[float]
    roi: Optional[float]
    monthly_cash_flow: Optional[float]
    break_even_ratio: Optional[float]
    price_to_rent_ratio: Optional[float]
    investment_score: float
    risk_level: str

@dataclass
class DealAnalysis:
    property_data: Dict[str, Any]
    estimated_value: float
    asking_price: float
    equity_potential: float
    investment_metrics: InvestmentMetrics
    market_comparison: Dict[str, Any]
    recommendation: str
    confidence_score: float

class InvestmentAnalyzerService:
    def __init__(self, market_service: MarketDataService, valuation_service: PropertyValuationService):
        self.market_service = market_service
        self.valuation_service = valuation_service
    
    def analyze_investment_opportunity(self, property_data: Dict[str, Any]) -> DealAnalysis:
        """Comprehensive investment analysis of a property"""
        
        # Get estimated value
        valuation = self.valuation_service.predict_value(property_data)
        estimated_value = valuation.get('predicted_value', 0)
        
        asking_price = property_data.get('asking_price', property_data.get('price', 0))
        
        # Calculate equity potential
        equity_potential = estimated_value - asking_price if estimated_value and asking_price else 0
        
        # Calculate investment metrics
        investment_metrics = self._calculate_investment_metrics(property_data)
        
        # Get market comparison
        market_comparison = self._get_market_comparison(property_data)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            equity_potential, investment_metrics, market_comparison
        )
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            valuation, market_comparison, property_data
        )
        
        return DealAnalysis(
            property_data=property_data,
            estimated_value=estimated_value,
            asking_price=asking_price,
            equity_potential=equity_potential,
            investment_metrics=investment_metrics,
            market_comparison=market_comparison,
            recommendation=recommendation,
            confidence_score=confidence_score
        )
    
    def _calculate_investment_metrics(self, property_data: Dict[str, Any]) -> InvestmentMetrics:
        """Calculate key investment metrics"""
        
        purchase_price = property_data.get('asking_price', property_data.get('price', 0))
        monthly_rent = property_data.get('estimated_rent', 0)
        down_payment = property_data.get('down_payment', purchase_price * 0.25)
        
        # Estimate expenses (typical percentages)
        monthly_expenses = {
            'property_tax': purchase_price * 0.012 / 12,  # 1.2% annually
            'insurance': purchase_price * 0.003 / 12,     # 0.3% annually
            'maintenance': monthly_rent * 0.05,           # 5% of rent
            'vacancy': monthly_rent * 0.05,               # 5% vacancy
            'property_management': monthly_rent * 0.08,   # 8% if managed
        }
        
        total_monthly_expenses = sum(monthly_expenses.values())
        
        # Mortgage calculation (assuming 30-year, 7% interest)
        loan_amount = purchase_price - down_payment
        monthly_interest_rate = 0.07 / 12
        num_payments = 30 * 12
        
        if loan_amount > 0:
            monthly_mortgage = loan_amount * (
                monthly_interest_rate * (1 + monthly_interest_rate) ** num_payments
            ) / ((1 + monthly_interest_rate) ** num_payments - 1)
        else:
            monthly_mortgage = 0
        
        # Calculate metrics
        monthly_cash_flow = monthly_rent - total_monthly_expenses - monthly_mortgage
        
        # Cap Rate (NOI / Purchase Price)
        annual_noi = (monthly_rent - total_monthly_expenses + monthly_expenses['property_management']) * 12
        cap_rate = (annual_noi / purchase_price * 100) if purchase_price > 0 else None
        
        # Cash on Cash Return
        annual_cash_flow = monthly_cash_flow * 12
        cash_on_cash = (annual_cash_flow / down_payment * 100) if down_payment > 0 else None
        
        # ROI (including appreciation estimate)
        annual_appreciation = purchase_price * 0.03  # Assume 3% appreciation
        total_annual_return = annual_cash_flow + annual_appreciation
        roi = (total_annual_return / down_payment * 100) if down_payment > 0 else None
        
        # Break-even ratio
        break_even_ratio = ((total_monthly_expenses + monthly_mortgage) / monthly_rent) if monthly_rent > 0 else None
        
        # Price to rent ratio
        annual_rent = monthly_rent * 12
        price_to_rent = (purchase_price / annual_rent) if annual_rent > 0 else None
        
        # Investment score (0-100)
        investment_score = self._calculate_investment_score(
            cap_rate, cash_on_cash, monthly_cash_flow, price_to_rent
        )
        
        # Risk level
        risk_level = self._determine_risk_level(investment_score, cap_rate, cash_on_cash)
        
        return InvestmentMetrics(
            cap_rate=cap_rate,
            cash_on_cash_return=cash_on_cash,
            roi=roi,
            monthly_cash_flow=monthly_cash_flow,
            break_even_ratio=break_even_ratio,
            price_to_rent_ratio=price_to_rent,
            investment_score=investment_score,
            risk_level=risk_level
        )
    
    def _calculate_investment_score(self, cap_rate, cash_on_cash, monthly_cash_flow, price_to_rent) -> float:
        """Calculate overall investment score (0-100)"""
        score = 50  # Base score
        
        # Cap rate scoring
        if cap_rate:
            if cap_rate >= 8:
                score += 20
            elif cap_rate >= 6:
                score += 15
            elif cap_rate >= 4:
                score += 10
            else:
                score -= 10
        
        # Cash on cash return scoring
        if cash_on_cash:
            if cash_on_cash >= 12:
                score += 15
            elif cash_on_cash >= 8:
                score += 10
            elif cash_on_cash >= 5:
                score += 5
            else:
                score -= 5
        
        # Cash flow scoring
        if monthly_cash_flow:
            if monthly_cash_flow >= 500:
                score += 10
            elif monthly_cash_flow >= 200:
                score += 5
            elif monthly_cash_flow >= 0:
                score += 0
            else:
                score -= 15
        
        # Price to rent ratio scoring (lower is better)
        if price_to_rent:
            if price_to_rent <= 12:
                score += 10
            elif price_to_rent <= 15:
                score += 5
            elif price_to_rent <= 20:
                score += 0
            else:
                score -= 10
        
        return max(0, min(100, score))
    
    def _determine_risk_level(self, investment_score, cap_rate, cash_on_cash) -> str:
        """Determine risk level based on metrics"""
        if investment_score >= 80:
            return "Low"
        elif investment_score >= 60:
            return "Medium"
        elif investment_score >= 40:
            return "High"
        else:
            return "Very High"
    
    def _get_market_comparison(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare property to market averages"""
        city = property_data.get('city')
        state = property_data.get('state')
        
        if not city or not state:
            return {"error": "City and state required for market comparison"}
        
        market_stats = self.market_service.get_market_stats(city, state)
        
        if not market_stats:
            return {"error": "No market data available for this location"}
        
        asking_price = property_data.get('asking_price', property_data.get('price', 0))
        house_size = property_data.get('house_size', 0)
        
        comparison = {
            "market_avg_price": market_stats.avg_price,
            "market_median_price": market_stats.median_price,
            "market_avg_price_per_sqft": market_stats.avg_price_per_sqft,
            "property_price": asking_price,
            "property_price_per_sqft": (asking_price / house_size) if house_size > 0 else None,
            "price_vs_market_avg": ((asking_price - market_stats.avg_price) / market_stats.avg_price * 100) if market_stats.avg_price > 0 else None,
            "price_vs_market_median": ((asking_price - market_stats.median_price) / market_stats.median_price * 100) if market_stats.median_price > 0 else None
        }
        
        return comparison
    
    def _generate_recommendation(self, equity_potential, investment_metrics, market_comparison) -> str:
        """Generate investment recommendation"""
        
        score = investment_metrics.investment_score
        equity_pct = (equity_potential / market_comparison.get('property_price', 1)) * 100 if market_comparison.get('property_price') else 0
        
        if score >= 80 and equity_pct >= 10:
            return "STRONG BUY - Excellent investment opportunity with strong metrics and equity potential"
        elif score >= 70 and equity_pct >= 5:
            return "BUY - Good investment opportunity with solid returns"
        elif score >= 60:
            return "CONSIDER - Decent investment but analyze carefully"
        elif score >= 40:
            return "CAUTION - Below average investment, high risk"
        else:
            return "AVOID - Poor investment opportunity with high risk"
    
    def _calculate_confidence_score(self, valuation, market_comparison, property_data) -> float:
        """Calculate confidence in the analysis"""
        confidence = 50  # Base confidence
        
        # Valuation confidence
        if 'predicted_value' in valuation and valuation['predicted_value'] > 0:
            confidence += 20
        
        # Market data availability
        if 'market_avg_price' in market_comparison:
            confidence += 15
        
        # Data completeness
        required_fields = ['asking_price', 'city', 'state', 'house_size']
        complete_fields = sum(1 for field in required_fields if property_data.get(field))
        confidence += (complete_fields / len(required_fields)) * 15
        
        return min(100, confidence)
    
    def find_investment_opportunities(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find properties matching investment criteria"""
        
        # Search properties based on criteria
        min_cap_rate = criteria.get('min_cap_rate', 6)
        max_price = criteria.get('max_price', 1000000)
        min_cash_flow = criteria.get('min_cash_flow', 0)
        target_cities = criteria.get('cities', [])
        
        opportunities = []
        
        # This would typically search your property database
        # For now, return a placeholder structure
        
        return opportunities