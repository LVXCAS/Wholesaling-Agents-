from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import numpy as np

from app.models.property import PropertyDB
from app.services.property_analyzer import PropertyAnalyzer
from app.services.renovation_calculator import RenovationCalculator

class WholesaleAnalyzer:
    def __init__(self, db: Session):
        self.db = db
        self.property_analyzer = PropertyAnalyzer(db)
        self.renovation_calculator = RenovationCalculator()
        
    def analyze_wholesale_deal(
        self,
        property: PropertyDB,
        condition_score: float,
        max_wholesale_fee_percent: float = 0.15,  # 15% max wholesale fee
        min_profit_margin: float = 0.20,          # 20% minimum profit margin
        holding_cost_monthly: float = 0.01        # 1% monthly holding cost
    ) -> Dict:
        """
        Analyze a property for wholesaling potential.
        Returns comprehensive analysis including ARV, renovation costs,
        wholesale fee potential, and deal scoring.
        """
        # Get ARV analysis
        arv_analysis = self.property_analyzer.analyze_property(property)
        arv = arv_analysis['arv_estimate']
        
        # Get renovation cost analysis
        renovation_analysis = self.renovation_calculator.estimate_renovation_costs(
            property,
            condition_score
        )
        renovation_cost = renovation_analysis['total_cost']
        
        # Calculate maximum allowable offer (MAO)
        estimated_holding_time = self._estimate_holding_time(
            property,
            renovation_analysis['renovation_level']
        )
        holding_costs = property.current_value * (holding_cost_monthly * estimated_holding_time)
        
        # Standard closing costs (buyer and seller)
        closing_costs = arv * 0.06  # Assuming 6% total
        
        # Calculate minimum required profit for end buyer
        min_profit = arv * min_profit_margin
        
        # Calculate maximum wholesale fee
        max_wholesale_fee = arv * max_wholesale_fee_percent
        
        # Calculate MAO (Maximum Allowable Offer)
        mao = (arv - 
               renovation_cost - 
               holding_costs - 
               closing_costs - 
               min_profit - 
               max_wholesale_fee)
        
        # Calculate current spread
        current_spread = mao - property.current_value if property.current_value else 0
        
        # Calculate deal score
        deal_score = self._calculate_deal_score(
            property,
            arv,
            renovation_cost,
            current_spread,
            condition_score,
            arv_analysis['confidence_score'],
            renovation_analysis['confidence_score']
        )
        
        # Generate renovation scope
        renovation_scope = self.renovation_calculator.get_renovation_scope(
            property,
            condition_score
        )
        
        return {
            'arv_analysis': arv_analysis,
            'renovation_analysis': renovation_analysis,
            'wholesale_analysis': {
                'maximum_allowable_offer': round(mao),
                'current_spread': round(current_spread),
                'max_wholesale_fee': round(max_wholesale_fee),
                'estimated_holding_time': estimated_holding_time,
                'holding_costs': round(holding_costs),
                'closing_costs': round(closing_costs),
                'minimum_buyer_profit': round(min_profit)
            },
            'deal_metrics': {
                'deal_score': deal_score,
                'score_components': {
                    'arv_confidence': arv_analysis['confidence_score'],
                    'renovation_confidence': renovation_analysis['confidence_score'],
                    'spread_score': min(1.0, current_spread / (arv * 0.3)),  # Score based on 30% ideal spread
                    'condition_score': condition_score
                }
            },
            'recommendations': {
                'renovation_scope': renovation_scope,
                'deal_type': self._categorize_deal(deal_score),
                'suggested_wholesale_fee': self._suggest_wholesale_fee(
                    current_spread,
                    max_wholesale_fee,
                    deal_score
                )
            }
        }
    
    def _estimate_holding_time(self, property: PropertyDB, renovation_level: str) -> float:
        """Estimate holding time in months based on renovation level and property type."""
        base_time = {
            'basic': 1.0,
            'medium': 2.5,
            'luxury': 4.0
        }
        
        # Add time for property size
        size_factor = 1.0
        if property.square_feet:
            if property.square_feet > 3000:
                size_factor = 1.5
            elif property.square_feet > 2000:
                size_factor = 1.2
        
        return base_time[renovation_level] * size_factor
    
    def _calculate_deal_score(
        self,
        property: PropertyDB,
        arv: float,
        renovation_cost: float,
        spread: float,
        condition_score: float,
        arv_confidence: float,
        renovation_confidence: float
    ) -> float:
        """
        Calculate a deal score from 0-100 based on multiple factors.
        """
        weights = {
            'spread_ratio': 0.4,      # 40% weight on the spread ratio
            'confidence': 0.3,        # 30% weight on confidence scores
            'condition': 0.2,         # 20% weight on property condition
            'deal_size': 0.1          # 10% weight on overall deal size
        }
        
        # Score the spread ratio (spread / ARV)
        spread_ratio = spread / arv if arv > 0 else 0
        spread_score = min(1.0, spread_ratio / 0.3)  # 30% spread is ideal
        
        # Combined confidence score
        confidence_score = (arv_confidence + renovation_confidence) / 2
        
        # Deal size score (larger deals = higher score, up to a point)
        deal_size_score = min(1.0, arv / 1000000)  # Score caps at $1M ARV
        
        # Calculate final score (0-100)
        final_score = (
            (spread_score * weights['spread_ratio']) +
            (confidence_score * weights['confidence']) +
            (condition_score * weights['condition']) +
            (deal_size_score * weights['deal_size'])
        ) * 100
        
        return round(final_score, 1)
    
    def _categorize_deal(self, deal_score: float) -> str:
        """Categorize the deal based on the deal score."""
        if deal_score >= 80:
            return "Exceptional Deal - Fast Action Recommended"
        elif deal_score >= 70:
            return "Strong Deal - Worth Pursuing"
        elif deal_score >= 60:
            return "Fair Deal - Additional Due Diligence Needed"
        elif deal_score >= 50:
            return "Marginal Deal - Proceed with Caution"
        else:
            return "Poor Deal - Not Recommended"
    
    def _suggest_wholesale_fee(
        self,
        spread: float,
        max_fee: float,
        deal_score: float
    ) -> Dict:
        """Suggest an appropriate wholesale fee based on deal metrics."""
        if deal_score >= 80:
            # Exceptional deals can command higher fees
            suggested_fee = min(max_fee, spread * 0.4)
        elif deal_score >= 70:
            # Strong deals
            suggested_fee = min(max_fee, spread * 0.35)
        elif deal_score >= 60:
            # Fair deals
            suggested_fee = min(max_fee, spread * 0.3)
        else:
            # Marginal or poor deals
            suggested_fee = min(max_fee, spread * 0.25)
            
        return {
            'suggested_fee': round(suggested_fee),
            'fee_as_percent_of_spread': round((suggested_fee / spread * 100) if spread > 0 else 0, 1),
            'fee_as_percent_of_arv': round((suggested_fee / max_fee * 15), 1)  # Based on max 15%
        }
