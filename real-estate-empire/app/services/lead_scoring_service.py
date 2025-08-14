"""
Lead Scoring Service

This service handles lead scoring, motivation analysis, and deal potential estimation
for the real estate deal sourcing engine.
"""

from typing import List, Dict, Optional, Any, Tuple
import uuid
import math
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.lead_scoring import (
    LeadScore, MotivationIndicator, PropertyConditionScore, MarketMetrics,
    FinancialIndicators, OwnerProfile, ScoringWeights, ScoringConfig,
    MotivationFactorEnum, DealPotentialEnum, LeadSourceEnum,
    LeadScoringBatch, LeadScoringBatchResult, ScoringAnalytics
)
from app.models.lead import PropertyLeadDB, PropertyLeadCreate
from app.core.database import get_db


class LeadScoringService:
    """Service for scoring real estate leads"""
    
    def __init__(self, db: Session = None):
        self.db = db
        self.default_config = self._get_default_config()
    
    def score_lead(self, lead: PropertyLeadDB, config: Optional[ScoringConfig] = None) -> LeadScore:
        """Score a single lead"""
        if config is None:
            config = self.default_config
        
        # Initialize lead score
        lead_score = LeadScore(
            lead_id=lead.id or uuid.uuid4(),
            property_id=getattr(lead.property, 'id', None) if hasattr(lead, 'property') else None,
            overall_score=0.0,
            deal_potential=DealPotentialEnum.POOR,
            confidence_score=0.0,
            motivation_score=0.0,
            financial_score=0.0,
            property_score=0.0,
            market_score=0.0,
            owner_score=0.0
        )
        
        # Analyze motivation indicators
        motivation_indicators = self._analyze_motivation_indicators(lead)
        lead_score.motivation_indicators = motivation_indicators
        lead_score.motivation_score = self._calculate_motivation_score(motivation_indicators, config)
        
        # Analyze property condition
        property_condition = self._analyze_property_condition(lead)
        lead_score.property_condition = property_condition
        lead_score.property_score = self._calculate_property_score(property_condition)
        
        # Analyze market metrics
        market_metrics = self._analyze_market_metrics(lead)
        lead_score.market_metrics = market_metrics
        lead_score.market_score = self._calculate_market_score(market_metrics)
        
        # Analyze financial indicators
        financial_indicators = self._analyze_financial_indicators(lead)
        lead_score.financial_indicators = financial_indicators
        lead_score.financial_score = self._calculate_financial_score(financial_indicators)
        
        # Analyze owner profile
        owner_profile = self._analyze_owner_profile(lead)
        lead_score.owner_profile = owner_profile
        lead_score.owner_score = self._calculate_owner_score(owner_profile)
        
        # Calculate overall score
        lead_score.overall_score = self._calculate_overall_score(lead_score, config)
        lead_score.deal_potential = self._determine_deal_potential(lead_score.overall_score, config)
        lead_score.confidence_score = self._calculate_confidence_score(lead_score)
        
        # Generate recommendations
        lead_score.recommended_actions = self._generate_recommendations(lead_score)
        lead_score.priority_level = self._determine_priority_level(lead_score)
        lead_score.estimated_close_probability = self._estimate_close_probability(lead_score)
        lead_score.estimated_profit_potential = self._estimate_profit_potential(lead_score, lead)
        
        return lead_score 
   
    def _analyze_motivation_indicators(self, lead: PropertyLeadDB) -> List[MotivationIndicator]:
        """Analyze and detect motivation indicators"""
        indicators = []
        
        # Check for explicit motivation indicators
        if hasattr(lead, 'motivation_factors') and lead.motivation_factors:
            for indicator_str in lead.motivation_factors:
                try:
                    factor = MotivationFactorEnum(indicator_str.lower().replace(' ', '_'))
                    indicators.append(MotivationIndicator(
                        factor=factor,
                        confidence=0.8,
                        weight=8.0,
                        evidence=f"Explicitly indicated: {indicator_str}",
                        source="lead_data"
                    ))
                except ValueError:
                    pass
        
        # Check financial indicators
        if hasattr(lead, 'behind_on_payments') and lead.behind_on_payments:
            indicators.append(MotivationIndicator(
                factor=MotivationFactorEnum.FINANCIAL_DISTRESS,
                confidence=0.9,
                weight=10.0,
                evidence="Behind on mortgage payments",
                source="financial_data"
            ))
        
        # Check for repair needs as motivation indicator
        if hasattr(lead, 'repair_needed') and lead.repair_needed:
            indicators.append(MotivationIndicator(
                factor=MotivationFactorEnum.PROPERTY_CONDITION,
                confidence=0.7,
                weight=6.0,
                evidence="Property needs repairs",
                source="lead_data"
            ))
        
        return indicators
    
    def _analyze_property_condition(self, lead: PropertyLeadDB) -> Optional[PropertyConditionScore]:
        """Analyze property condition for scoring"""
        # Initialize with default scores
        overall_score = 75.0
        structural_score = 75.0
        cosmetic_score = 75.0
        systems_score = 75.0
        
        # Adjust based on property age
        if hasattr(lead, 'property') and lead.property and hasattr(lead.property, 'year_built'):
            if lead.property.year_built:
                current_year = datetime.now().year
                age = current_year - lead.property.year_built
                
                if age > 50:
                    overall_score -= 20
                    structural_score -= 25
                    systems_score -= 30
                elif age > 30:
                    overall_score -= 10
                    systems_score -= 15
                elif age > 15:
                    systems_score -= 5
        
        # Check for repair indicators
        repair_needed = False
        estimated_repair_cost = None
        repair_urgency = "low"
        
        if hasattr(lead, 'repair_needed') and lead.repair_needed:
            repair_needed = True
            overall_score -= 25
            cosmetic_score -= 30
            repair_urgency = "medium"
            
            if hasattr(lead, 'estimated_repair_cost') and lead.estimated_repair_cost:
                estimated_repair_cost = lead.estimated_repair_cost
                
                if estimated_repair_cost > 50000:
                    overall_score -= 30
                    structural_score -= 40
                    repair_urgency = "high"
                elif estimated_repair_cost > 20000:
                    overall_score -= 15
                    cosmetic_score -= 20
        
        # Ensure scores don't go below 0
        overall_score = max(0, overall_score)
        structural_score = max(0, structural_score)
        cosmetic_score = max(0, cosmetic_score)
        systems_score = max(0, systems_score)
        
        return PropertyConditionScore(
            overall_score=overall_score,
            structural_score=structural_score,
            cosmetic_score=cosmetic_score,
            systems_score=systems_score,
            repair_needed=repair_needed,
            estimated_repair_cost=estimated_repair_cost,
            repair_urgency=repair_urgency,
            assessment_method="automated_analysis",
            confidence_score=0.6
        )    

    def _analyze_market_metrics(self, lead: PropertyLeadDB) -> Optional[MarketMetrics]:
        """Analyze market-related metrics"""
        days_on_market = None
        price_reductions = 0
        total_price_reduction = 0.0
        price_reduction_percentage = 0.0
        
        market_activity_score = 50.0
        
        current_month = datetime.now().month
        seasonal_factor = 1.0
        
        if current_month in [4, 5, 6, 7, 8]:
            seasonal_factor = 1.1
        elif current_month in [11, 12, 1, 2]:
            seasonal_factor = 0.9
        
        return MarketMetrics(
            days_on_market=days_on_market,
            price_reductions=price_reductions,
            total_price_reduction=total_price_reduction,
            price_reduction_percentage=price_reduction_percentage,
            market_activity_score=market_activity_score,
            seasonal_factor=seasonal_factor,
            market_trend="stable"
        )
    
    def _analyze_financial_indicators(self, lead: PropertyLeadDB) -> Optional[FinancialIndicators]:
        """Analyze financial indicators for scoring"""
        equity_percentage = None
        loan_to_value = None
        monthly_payment = None
        
        if hasattr(lead, 'asking_price') and lead.asking_price:
            asking_price = lead.asking_price
            
            if hasattr(lead, 'mortgage_balance') and lead.mortgage_balance:
                mortgage_balance = lead.mortgage_balance
                equity = asking_price - mortgage_balance
                equity_percentage = (equity / asking_price) * 100 if asking_price > 0 else 0
                loan_to_value = (mortgage_balance / asking_price) * 100 if asking_price > 0 else 0
        
        if hasattr(lead, 'monthly_payment') and lead.monthly_payment:
            monthly_payment = lead.monthly_payment
        
        return FinancialIndicators(
            equity_percentage=equity_percentage,
            loan_to_value=loan_to_value,
            monthly_payment=monthly_payment,
            payment_to_income_ratio=None,
            tax_delinquency=False,
            tax_amount_owed=None,
            foreclosure_status=None,
            foreclosure_date=None,
            bankruptcy_history=False,
            lien_amount=None
        )
    
    def _analyze_owner_profile(self, lead: PropertyLeadDB) -> Optional[OwnerProfile]:
        """Analyze owner profile for scoring"""
        contact_attempts = 0
        
        if hasattr(lead, 'contact_attempts') and lead.contact_attempts:
            contact_attempts = lead.contact_attempts
        
        return OwnerProfile(
            ownership_duration=None,
            owner_occupied=None,
            out_of_state_owner=False,
            property_count=None,
            investor_profile=False,
            age_estimate=None,
            life_stage=None,
            contact_attempts=contact_attempts,
            responsiveness_score=None,
            previous_sales=None,
            sale_frequency=None
        )    
    
    def _calculate_motivation_score(self, indicators: List[MotivationIndicator], config: ScoringConfig) -> float:
        """Calculate motivation score from indicators"""
        if not indicators:
            return 0.0
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for indicator in indicators:
            factor_weight = config.motivation_factor_weights.get(indicator.factor, 5.0)
            weighted_score = factor_weight * indicator.confidence * indicator.weight
            total_weighted_score += weighted_score
            total_weight += factor_weight
        
        if total_weight == 0:
            return 0.0
        
        raw_score = (total_weighted_score / total_weight) * 10
        return min(100.0, max(0.0, raw_score))
    
    def _calculate_property_score(self, condition: Optional[PropertyConditionScore]) -> float:
        """Calculate property score from condition assessment"""
        if not condition:
            return 50.0
        
        score = (
            condition.overall_score * 0.4 +
            condition.structural_score * 0.3 +
            condition.cosmetic_score * 0.2 +
            condition.systems_score * 0.1
        )
        
        if condition.repair_needed:
            if condition.repair_urgency == "high":
                score *= 0.7
            elif condition.repair_urgency == "medium":
                score *= 0.85
            else:
                score *= 0.95
        
        return min(100.0, max(0.0, score))
    
    def _calculate_market_score(self, metrics: Optional[MarketMetrics]) -> float:
        """Calculate market score from market metrics"""
        if not metrics:
            return 50.0
        
        score = 50.0
        
        if metrics.days_on_market:
            if metrics.days_on_market > 120:
                score += 30
            elif metrics.days_on_market > 60:
                score += 15
            elif metrics.days_on_market < 14:
                score -= 10
        
        if metrics.price_reduction_percentage:
            if metrics.price_reduction_percentage > 10:
                score += 25
            elif metrics.price_reduction_percentage > 5:
                score += 15
        
        if metrics.market_activity_score:
            activity_adjustment = (100 - metrics.market_activity_score) * 0.2
            score += activity_adjustment
        
        if metrics.seasonal_factor:
            score *= metrics.seasonal_factor
        
        return min(100.0, max(0.0, score))
    
    def _calculate_financial_score(self, indicators: Optional[FinancialIndicators]) -> float:
        """Calculate financial score from financial indicators"""
        if not indicators:
            return 50.0
        
        score = 50.0
        
        if indicators.equity_percentage is not None:
            if indicators.equity_percentage > 50:
                score += 20
            elif indicators.equity_percentage > 30:
                score += 10
            elif indicators.equity_percentage < 10:
                score -= 15
        
        if indicators.loan_to_value is not None:
            if indicators.loan_to_value > 90:
                score += 15
            elif indicators.loan_to_value < 50:
                score += 5
        
        if indicators.tax_delinquency:
            score += 25
        
        if indicators.foreclosure_status:
            score += 30
        
        if indicators.bankruptcy_history:
            score += 20
        
        if indicators.lien_amount and indicators.lien_amount > 0:
            score += 15
        
        return min(100.0, max(0.0, score))
    
    def _calculate_owner_score(self, profile: Optional[OwnerProfile]) -> float:
        """Calculate owner score from owner profile"""
        if not profile:
            return 50.0
        
        score = 50.0
        
        if profile.out_of_state_owner:
            score += 15
        
        if profile.investor_profile:
            score += 10
        
        if profile.property_count and profile.property_count > 3:
            score += 10
        
        if profile.contact_attempts > 5:
            score -= 10
        elif profile.contact_attempts > 0 and profile.responsiveness_score and profile.responsiveness_score > 50:
            score += 10
        
        if profile.ownership_duration:
            if profile.ownership_duration > 10:
                score += 5
            elif profile.ownership_duration < 2:
                score -= 5
        
        return min(100.0, max(0.0, score))    
    
    def _calculate_overall_score(self, lead_score: LeadScore, config: ScoringConfig) -> float:
        """Calculate overall weighted score"""
        weights = config.weights
        
        total_score = (
            lead_score.motivation_score * (weights.motivation_weight / 100) +
            lead_score.financial_score * (weights.financial_weight / 100) +
            lead_score.property_score * (weights.property_weight / 100) +
            lead_score.market_score * (weights.market_weight / 100) +
            lead_score.owner_score * (weights.owner_weight / 100)
        )
        
        return min(100.0, max(0.0, total_score))
    
    def _determine_deal_potential(self, overall_score: float, config: ScoringConfig) -> DealPotentialEnum:
        """Determine deal potential category from overall score"""
        if overall_score >= config.excellent_threshold:
            return DealPotentialEnum.EXCELLENT
        elif overall_score >= config.good_threshold:
            return DealPotentialEnum.GOOD
        elif overall_score >= config.fair_threshold:
            return DealPotentialEnum.FAIR
        elif overall_score >= config.poor_threshold:
            return DealPotentialEnum.POOR
        else:
            return DealPotentialEnum.VERY_POOR
    
    def _calculate_confidence_score(self, lead_score: LeadScore) -> float:
        """Calculate confidence in the scoring"""
        confidence_factors = []
        
        if lead_score.motivation_indicators:
            avg_motivation_confidence = sum(i.confidence for i in lead_score.motivation_indicators) / len(lead_score.motivation_indicators)
            confidence_factors.append(avg_motivation_confidence)
        
        if lead_score.property_condition:
            confidence_factors.append(lead_score.property_condition.confidence_score)
        
        data_completeness = 0.0
        total_fields = 5
        
        if lead_score.motivation_indicators:
            data_completeness += 1
        if lead_score.financial_indicators:
            data_completeness += 1
        if lead_score.property_condition:
            data_completeness += 1
        if lead_score.market_metrics:
            data_completeness += 1
        if lead_score.owner_profile:
            data_completeness += 1
        
        completeness_score = data_completeness / total_fields
        confidence_factors.append(completeness_score)
        
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        else:
            return 0.3
    
    def _generate_recommendations(self, lead_score: LeadScore) -> List[str]:
        """Generate action recommendations based on score"""
        recommendations = []
        
        if lead_score.deal_potential == DealPotentialEnum.EXCELLENT:
            recommendations.append("High priority lead - initiate contact immediately")
            recommendations.append("Prepare competitive offer strategy")
        elif lead_score.deal_potential == DealPotentialEnum.GOOD:
            recommendations.append("Good opportunity - contact within 24 hours")
            recommendations.append("Research comparable sales for offer preparation")
        elif lead_score.deal_potential == DealPotentialEnum.FAIR:
            recommendations.append("Moderate opportunity - add to follow-up sequence")
        else:
            recommendations.append("Low priority - monitor for changes")
        
        if lead_score.motivation_score > 70:
            recommendations.append("High motivation detected - focus on seller benefits")
        
        if lead_score.property_condition and lead_score.property_condition.repair_needed:
            recommendations.append("Property needs repairs - factor into offer calculations")
        
        return recommendations
    
    def _determine_priority_level(self, lead_score: LeadScore) -> str:
        """Determine priority level for the lead"""
        if lead_score.overall_score >= 80:
            return "urgent"
        elif lead_score.overall_score >= 60:
            return "high"
        elif lead_score.overall_score >= 40:
            return "medium"
        else:
            return "low"
    
    def _estimate_close_probability(self, lead_score: LeadScore) -> float:
        """Estimate probability of closing the deal"""
        base_probability = lead_score.overall_score / 100.0
        
        adjustments = 0.0
        
        if lead_score.motivation_score > 70:
            adjustments += 0.1
        
        if lead_score.market_score > 60:
            adjustments += 0.05
        
        if lead_score.financial_indicators:
            if lead_score.financial_indicators.tax_delinquency or lead_score.financial_indicators.foreclosure_status:
                adjustments += 0.15
        
        if lead_score.owner_profile and lead_score.owner_profile.responsiveness_score and lead_score.owner_profile.responsiveness_score > 50:
            adjustments += 0.1
        
        final_probability = min(1.0, max(0.0, base_probability + adjustments))
        return final_probability
    
    def _estimate_profit_potential(self, lead_score: LeadScore, lead: PropertyLeadDB) -> Optional[float]:
        """Estimate potential profit from the deal"""
        if not hasattr(lead, 'asking_price') or not lead.asking_price:
            return None
        
        asking_price = lead.asking_price
        estimated_profit = 0.0
        
        if lead_score.property_condition:
            if lead_score.property_condition.estimated_repair_cost:
                repair_cost = lead_score.property_condition.estimated_repair_cost
                arv = asking_price * 1.2
                max_offer = arv * 0.7 - repair_cost
                if max_offer > asking_price:
                    estimated_profit = max_offer - asking_price - repair_cost
        
        wholesale_profit = asking_price * 0.05
        
        return max(estimated_profit, wholesale_profit) if estimated_profit > 0 else wholesale_profit
    
    def _get_default_config(self) -> ScoringConfig:
        """Get default scoring configuration"""
        return ScoringConfig(
            name="Default Lead Scoring",
            description="Default configuration for lead scoring algorithm"
        )    
    
    def score_leads_batch(self, leads: List[PropertyLeadDB], config: Optional[ScoringConfig] = None) -> LeadScoringBatchResult:
        """Score multiple leads in batch"""
        start_time = datetime.now()
        
        result = LeadScoringBatchResult(
            total_leads=len(leads),
            successful_scores=0,
            failed_scores=0,
            processing_time=0.0,
            started_at=start_time
        )
        
        for lead in leads:
            try:
                score = self.score_lead(lead, config)
                result.scores.append(score)
                result.successful_scores += 1
            except Exception as e:
                result.errors.append({
                    "lead_id": str(lead.id) if hasattr(lead, 'id') and lead.id else "unknown",
                    "error": str(e),
                    "timestamp": datetime.now()
                })
                result.failed_scores += 1
        
        end_time = datetime.now()
        result.completed_at = end_time
        result.processing_time = (end_time - start_time).total_seconds()
        
        return result
    
    def get_scoring_analytics(self, period_start: Optional[datetime] = None, 
                            period_end: Optional[datetime] = None) -> ScoringAnalytics:
        """Get analytics for lead scoring performance"""
        if period_end is None:
            period_end = datetime.now()
        if period_start is None:
            period_start = period_end - timedelta(days=30)
        
        return ScoringAnalytics(
            total_leads_scored=0,
            average_score=0.0,
            score_distribution={
                DealPotentialEnum.EXCELLENT: 0,
                DealPotentialEnum.GOOD: 0,
                DealPotentialEnum.FAIR: 0,
                DealPotentialEnum.POOR: 0,
                DealPotentialEnum.VERY_POOR: 0
            },
            top_motivation_factors=[],
            conversion_rates={},
            period_start=period_start,
            period_end=period_end
        )