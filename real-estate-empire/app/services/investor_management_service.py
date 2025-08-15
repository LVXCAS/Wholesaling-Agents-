"""
Investor relationship management service for the Real Estate Empire platform.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.models.investor import (
    InvestorProfile, InvestmentHistory, InvestorCommunication,
    InvestorPerformanceMetrics, DealInvestorMatch, InvestorDealPresentation,
    InvestorSearchCriteria, InvestorAnalytics, InvestorTypeEnum,
    InvestorStatusEnum, InvestmentPreferenceEnum, RiskToleranceEnum,
    CommunicationPreferenceEnum
)

logger = logging.getLogger(__name__)


class InvestorManagementService:
    """Service for managing investor relationships and communications"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Investor Profile Management
    
    def create_investor_profile(self, investor_data: Dict[str, Any]) -> InvestorProfile:
        """Create a new investor profile"""
        try:
            investor = InvestorProfile(**investor_data)
            # In a real implementation, this would save to database
            logger.info(f"Created investor profile for {investor.full_name}")
            return investor
        except Exception as e:
            logger.error(f"Error creating investor profile: {str(e)}")
            raise
    
    def update_investor_profile(self, investor_id: UUID, updates: Dict[str, Any]) -> InvestorProfile:
        """Update an existing investor profile"""
        try:
            # In a real implementation, this would fetch from database and update
            updates['updated_at'] = datetime.utcnow()
            logger.info(f"Updated investor profile {investor_id}")
            
            # For testing purposes, create a minimal valid investor profile
            # In a real implementation, this would fetch existing data and merge updates
            base_data = {
                "id": investor_id,
                "first_name": "Test",
                "last_name": "Investor",
                "email": "test@example.com",
                "investor_type": InvestorTypeEnum.INDIVIDUAL
            }
            base_data.update(updates)
            
            return InvestorProfile(**base_data)
        except Exception as e:
            logger.error(f"Error updating investor profile {investor_id}: {str(e)}")
            raise
    
    def get_investor_profile(self, investor_id: UUID) -> Optional[InvestorProfile]:
        """Get investor profile by ID"""
        try:
            # In a real implementation, this would fetch from database
            logger.info(f"Retrieved investor profile {investor_id}")
            return None  # Placeholder
        except Exception as e:
            logger.error(f"Error retrieving investor profile {investor_id}: {str(e)}")
            raise
    
    def search_investors(self, criteria: InvestorSearchCriteria) -> List[InvestorProfile]:
        """Search investors based on criteria"""
        try:
            # In a real implementation, this would build and execute database query
            investors = []
            logger.info(f"Found {len(investors)} investors matching criteria")
            return investors
        except Exception as e:
            logger.error(f"Error searching investors: {str(e)}")
            raise
    
    def get_all_investors(self, 
                         status: Optional[InvestorStatusEnum] = None,
                         limit: int = 100,
                         offset: int = 0) -> List[InvestorProfile]:
        """Get all investors with optional filtering"""
        try:
            # In a real implementation, this would fetch from database
            investors = []
            logger.info(f"Retrieved {len(investors)} investors")
            return investors
        except Exception as e:
            logger.error(f"Error retrieving investors: {str(e)}")
            raise
    
    # Deal-Investor Matching
    
    def match_investors_to_deal(self, deal_id: UUID, deal_data: Dict[str, Any]) -> List[DealInvestorMatch]:
        """Find investors that match a specific deal"""
        try:
            matches = []
            
            # Get all active investors
            active_investors = self.get_all_investors(status=InvestorStatusEnum.ACTIVE)
            
            for investor in active_investors:
                match_score, match_reasons = self._calculate_investor_match_score(
                    investor, deal_data
                )
                
                if match_score > 0.3:  # Minimum match threshold
                    match = DealInvestorMatch(
                        deal_id=deal_id,
                        investor_id=investor.id,
                        match_score=match_score,
                        match_reasons=match_reasons,
                        investment_preferences_match=self._check_investment_preferences_match(
                            investor, deal_data
                        ),
                        risk_assessment_match=self._check_risk_match(investor, deal_data),
                        financial_capacity_match=self._check_financial_capacity_match(
                            investor, deal_data
                        ),
                        geographic_preference_match=self._check_geographic_match(
                            investor, deal_data
                        )
                    )
                    matches.append(match)
            
            # Sort by match score descending
            matches.sort(key=lambda x: x.match_score, reverse=True)
            
            logger.info(f"Found {len(matches)} investor matches for deal {deal_id}")
            return matches
            
        except Exception as e:
            logger.error(f"Error matching investors to deal {deal_id}: {str(e)}")
            raise
    
    def _calculate_investor_match_score(self, 
                                      investor: InvestorProfile, 
                                      deal_data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Calculate match score between investor and deal"""
        score = 0.0
        reasons = []
        
        # Investment preferences match (30% weight)
        if self._check_investment_preferences_match(investor, deal_data):
            score += 0.3
            reasons.append("Investment preferences align")
        
        # Financial capacity match (25% weight)
        if self._check_financial_capacity_match(investor, deal_data):
            score += 0.25
            reasons.append("Financial capacity sufficient")
        
        # Geographic preference match (20% weight)
        if self._check_geographic_match(investor, deal_data):
            score += 0.2
            reasons.append("Geographic preference match")
        
        # Risk tolerance match (15% weight)
        if self._check_risk_match(investor, deal_data):
            score += 0.15
            reasons.append("Risk tolerance appropriate")
        
        # Historical performance bonus (10% weight)
        if self._check_historical_performance(investor):
            score += 0.1
            reasons.append("Strong historical performance")
        
        return min(score, 1.0), reasons
    
    def _check_investment_preferences_match(self, 
                                          investor: InvestorProfile, 
                                          deal_data: Dict[str, Any]) -> Dict[str, bool]:
        """Check if deal matches investor's investment preferences"""
        deal_type = deal_data.get('property_type', '').lower()
        
        matches = {}
        for pref in investor.investment_preferences:
            if pref == InvestmentPreferenceEnum.RESIDENTIAL and 'residential' in deal_type:
                matches[pref] = True
            elif pref == InvestmentPreferenceEnum.COMMERCIAL and 'commercial' in deal_type:
                matches[pref] = True
            elif pref == InvestmentPreferenceEnum.DISTRESSED and deal_data.get('distressed', False):
                matches[pref] = True
            else:
                matches[pref] = False
        
        return matches
    
    def _check_financial_capacity_match(self, 
                                      investor: InvestorProfile, 
                                      deal_data: Dict[str, Any]) -> bool:
        """Check if investor has financial capacity for the deal"""
        deal_amount = deal_data.get('investment_required', 0)
        
        if investor.min_investment and deal_amount < investor.min_investment:
            return False
        
        if investor.max_investment and deal_amount > investor.max_investment:
            return False
        
        if investor.liquid_capital and deal_amount > investor.liquid_capital:
            return False
        
        return True
    
    def _check_geographic_match(self, 
                              investor: InvestorProfile, 
                              deal_data: Dict[str, Any]) -> bool:
        """Check if deal location matches investor's geographic preferences"""
        if not investor.preferred_markets:
            return True  # No preference means all markets acceptable
        
        deal_market = deal_data.get('market', '').lower()
        deal_city = deal_data.get('city', '').lower()
        deal_state = deal_data.get('state', '').lower()
        
        for market in investor.preferred_markets:
            market_lower = market.lower()
            if (market_lower in deal_market or 
                market_lower in deal_city or 
                market_lower in deal_state):
                return True
        
        return False
    
    def _check_risk_match(self, 
                         investor: InvestorProfile, 
                         deal_data: Dict[str, Any]) -> bool:
        """Check if deal risk level matches investor's risk tolerance"""
        deal_risk = deal_data.get('risk_level', 'moderate').lower()
        
        risk_mapping = {
            RiskToleranceEnum.CONSERVATIVE: ['low', 'conservative'],
            RiskToleranceEnum.MODERATE: ['low', 'moderate', 'conservative'],
            RiskToleranceEnum.AGGRESSIVE: ['low', 'moderate', 'high', 'aggressive']
        }
        
        acceptable_risks = risk_mapping.get(investor.risk_tolerance, ['moderate'])
        return deal_risk in acceptable_risks
    
    def _check_historical_performance(self, investor: InvestorProfile) -> bool:
        """Check if investor has good historical performance"""
        # In a real implementation, this would check investment history
        # For now, return True for active investors
        return investor.status == InvestorStatusEnum.ACTIVE
    
    # Communication Management
    
    def log_communication(self, communication_data: Dict[str, Any]) -> InvestorCommunication:
        """Log a communication with an investor"""
        try:
            communication = InvestorCommunication(**communication_data)
            logger.info(f"Logged communication with investor {communication.investor_id}")
            return communication
        except Exception as e:
            logger.error(f"Error logging communication: {str(e)}")
            raise
    
    def get_investor_communications(self, 
                                  investor_id: UUID,
                                  limit: int = 50) -> List[InvestorCommunication]:
        """Get communication history for an investor"""
        try:
            # In a real implementation, this would fetch from database
            communications = []
            logger.info(f"Retrieved {len(communications)} communications for investor {investor_id}")
            return communications
        except Exception as e:
            logger.error(f"Error retrieving communications for investor {investor_id}: {str(e)}")
            raise
    
    def schedule_follow_up(self, 
                          investor_id: UUID, 
                          follow_up_date: datetime,
                          notes: str = "") -> bool:
        """Schedule a follow-up with an investor"""
        try:
            # In a real implementation, this would create a scheduled task
            logger.info(f"Scheduled follow-up with investor {investor_id} for {follow_up_date}")
            return True
        except Exception as e:
            logger.error(f"Error scheduling follow-up with investor {investor_id}: {str(e)}")
            raise
    
    def get_pending_follow_ups(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get pending follow-ups for the next N days"""
        try:
            # In a real implementation, this would query scheduled follow-ups
            follow_ups = []
            logger.info(f"Retrieved {len(follow_ups)} pending follow-ups")
            return follow_ups
        except Exception as e:
            logger.error(f"Error retrieving pending follow-ups: {str(e)}")
            raise
    
    # Performance Tracking
    
    def calculate_investor_performance(self, investor_id: UUID) -> InvestorPerformanceMetrics:
        """Calculate performance metrics for an investor"""
        try:
            # In a real implementation, this would aggregate investment history
            metrics = InvestorPerformanceMetrics(investor_id=investor_id)
            logger.info(f"Calculated performance metrics for investor {investor_id}")
            return metrics
        except Exception as e:
            logger.error(f"Error calculating performance for investor {investor_id}: {str(e)}")
            raise
    
    def get_top_performing_investors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing investors by ROI"""
        try:
            # In a real implementation, this would query and rank investors
            top_investors = []
            logger.info(f"Retrieved top {limit} performing investors")
            return top_investors
        except Exception as e:
            logger.error(f"Error retrieving top performing investors: {str(e)}")
            raise
    
    def generate_investor_analytics(self) -> InvestorAnalytics:
        """Generate comprehensive investor analytics"""
        try:
            analytics = InvestorAnalytics()
            
            # In a real implementation, this would calculate actual metrics
            analytics.total_investors = 0
            analytics.active_investors = 0
            analytics.prospect_investors = 0
            
            logger.info("Generated investor analytics")
            return analytics
        except Exception as e:
            logger.error(f"Error generating investor analytics: {str(e)}")
            raise
    
    # Investment History Management
    
    def record_investment(self, investment_data: Dict[str, Any]) -> InvestmentHistory:
        """Record a new investment by an investor"""
        try:
            investment = InvestmentHistory(**investment_data)
            logger.info(f"Recorded investment for investor {investment.investor_id}")
            return investment
        except Exception as e:
            logger.error(f"Error recording investment: {str(e)}")
            raise
    
    def get_investor_investment_history(self, investor_id: UUID) -> List[InvestmentHistory]:
        """Get investment history for an investor"""
        try:
            # In a real implementation, this would fetch from database
            history = []
            logger.info(f"Retrieved investment history for investor {investor_id}")
            return history
        except Exception as e:
            logger.error(f"Error retrieving investment history for investor {investor_id}: {str(e)}")
            raise
    
    def update_investment_performance(self, 
                                    investment_id: UUID, 
                                    actual_return: Decimal) -> bool:
        """Update the actual return for an investment"""
        try:
            # In a real implementation, this would update the database
            logger.info(f"Updated investment performance for {investment_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating investment performance {investment_id}: {str(e)}")
            raise
    
    # Deal Presentation Management
    
    def create_deal_presentation(self, presentation_data: Dict[str, Any]) -> InvestorDealPresentation:
        """Create a deal presentation record"""
        try:
            presentation = InvestorDealPresentation(**presentation_data)
            logger.info(f"Created deal presentation for investor {presentation.investor_id}")
            return presentation
        except Exception as e:
            logger.error(f"Error creating deal presentation: {str(e)}")
            raise
    
    def track_presentation_engagement(self, 
                                    presentation_id: UUID, 
                                    engagement_type: str) -> bool:
        """Track engagement with a deal presentation"""
        try:
            # In a real implementation, this would update the presentation record
            logger.info(f"Tracked {engagement_type} for presentation {presentation_id}")
            return True
        except Exception as e:
            logger.error(f"Error tracking presentation engagement: {str(e)}")
            raise
    
    def get_presentation_analytics(self, deal_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get analytics for deal presentations"""
        try:
            # In a real implementation, this would calculate actual metrics
            analytics = {
                'total_presentations': 0,
                'open_rate': 0.0,
                'download_rate': 0.0,
                'response_rate': 0.0,
                'interest_rate': 0.0
            }
            logger.info("Generated presentation analytics")
            return analytics
        except Exception as e:
            logger.error(f"Error generating presentation analytics: {str(e)}")
            raise