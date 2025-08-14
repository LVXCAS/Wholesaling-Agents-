"""
Unit tests for the Lead Scoring System

Tests the lead scoring algorithm, motivation analysis, deal potential estimation,
and confidence scoring functionality.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.services.lead_scoring_service import LeadScoringService
from app.models.lead_scoring import (
    LeadScore, MotivationIndicator, PropertyConditionScore, MarketMetrics,
    FinancialIndicators, OwnerProfile, ScoringWeights, ScoringConfig,
    MotivationFactorEnum, DealPotentialEnum, LeadSourceEnum,
    LeadScoringBatch, LeadScoringBatchResult, ScoringAnalytics
)
from app.models.lead import PropertyLeadDB, PropertyLeadCreate


class TestLeadScoringService:
    """Test cases for LeadScoringService"""
    
    @pytest.fixture
    def scoring_service(self):
        """Create a LeadScoringService instance for testing"""
        return LeadScoringService()
    
    @pytest.fixture
    def sample_lead(self):
        """Create a sample lead for testing"""
        lead = Mock()
        lead.id = uuid.uuid4()
        lead.source = LeadSourceEnum.MLS
        lead.asking_price = 200000
        lead.mortgage_balance = 150000
        lead.monthly_payment = 1200
        lead.behind_on_payments = False
        lead.repair_needed = True
        lead.estimated_repair_cost = 15000
        lead.condition_notes = "Needs cosmetic updates and new flooring"
        lead.contact_attempts = 2
        
        # Mock property data
        lead.property = Mock()
        lead.property.id = uuid.uuid4()
        lead.property.days_on_market = 45
        lead.property.year_built = 1985
        lead.property.occupancy_status = 'occupied'
        lead.property.original_list_price = 220000
        
        # Mock owner info
        lead.owner_info = Mock()
        lead.owner_info.out_of_state = False
        lead.owner_info.property_count = 1
        
        # Mock motivation indicators
        lead.motivation_indicators = ['financial_distress', 'property_condition']
        
        return lead
    
    @pytest.fixture
    def high_motivation_lead(self):
        """Create a lead with high motivation indicators"""
        lead = Mock()
        lead.id = uuid.uuid4()
        lead.source = LeadSourceEnum.FORECLOSURE
        lead.asking_price = 180000
        lead.mortgage_balance = 170000
        lead.monthly_payment = 1400
        lead.behind_on_payments = True
        lead.repair_needed = True
        lead.estimated_repair_cost = 25000
        lead.condition_notes = "Foundation issues, roof problems, water damage"
        lead.contact_attempts = 1
        
        # Mock property data
        lead.property = Mock()
        lead.property.id = uuid.uuid4()
        lead.property.days_on_market = 120
        lead.property.year_built = 1970
        lead.property.occupancy_status = 'vacant'
        lead.property.original_list_price = 200000
        
        # Mock owner info
        lead.owner_info = Mock()
        lead.owner_info.out_of_state = True
        lead.owner_info.property_count = 5
        
        # Mock motivation indicators
        lead.motivation_indicators = ['financial_distress', 'foreclosure_threat', 'vacant_property', 'tired_landlord']
        
        return lead
    
    @pytest.fixture
    def low_motivation_lead(self):
        """Create a lead with low motivation indicators"""
        lead = Mock()
        lead.id = uuid.uuid4()
        lead.source = LeadSourceEnum.MLS
        lead.asking_price = 300000
        lead.mortgage_balance = 100000
        lead.monthly_payment = 800
        lead.behind_on_payments = False
        lead.repair_needed = False
        lead.estimated_repair_cost = 0
        lead.condition_notes = "Excellent condition, recently renovated"
        lead.contact_attempts = 0
        
        # Mock property data
        lead.property = Mock()
        lead.property.id = uuid.uuid4()
        lead.property.days_on_market = 10
        lead.property.year_built = 2015
        lead.property.occupancy_status = 'occupied'
        lead.property.original_list_price = 300000
        
        # Mock owner info
        lead.owner_info = Mock()
        lead.owner_info.out_of_state = False
        lead.owner_info.property_count = 1
        
        # Mock motivation indicators
        lead.motivation_indicators = []
        
        return lead
    
    def test_score_lead_basic(self, scoring_service, sample_lead):
        """Test basic lead scoring functionality"""
        score = scoring_service.score_lead(sample_lead)
        
        assert isinstance(score, LeadScore)
        assert score.lead_id == sample_lead.id
        assert score.property_id == sample_lead.property.id
        assert 0 <= score.overall_score <= 100
        assert score.deal_potential in DealPotentialEnum
        assert 0 <= score.confidence_score <= 1
        assert len(score.recommended_actions) > 0
        assert score.priority_level in ['low', 'medium', 'high', 'urgent']
    
    def test_motivation_analysis(self, scoring_service, sample_lead):
        """Test motivation indicator analysis"""
        indicators = scoring_service._analyze_motivation_indicators(sample_lead)
        
        assert len(indicators) > 0
        assert all(isinstance(indicator, MotivationIndicator) for indicator in indicators)
        
        # Check for expected motivation factors
        factor_types = [indicator.factor for indicator in indicators]
        assert MotivationFactorEnum.FINANCIAL_DISTRESS in factor_types
        assert MotivationFactorEnum.PROPERTY_CONDITION in factor_types
        
        # Verify confidence scores are valid
        assert all(0 <= indicator.confidence <= 1 for indicator in indicators)
        assert all(indicator.weight > 0 for indicator in indicators)
    
    def test_high_motivation_lead_scoring(self, scoring_service, high_motivation_lead):
        """Test scoring of high motivation lead"""
        score = scoring_service.score_lead(high_motivation_lead)
        
        # High motivation lead should have high scores
        assert score.motivation_score > 60
        assert score.overall_score > 50
        assert score.deal_potential in [DealPotentialEnum.GOOD, DealPotentialEnum.EXCELLENT]
        assert score.priority_level in ['high', 'urgent']
        assert score.estimated_close_probability > 0.5
        
        # Should have multiple motivation indicators
        assert len(score.motivation_indicators) >= 3
        
        # Should have actionable recommendations
        assert len(score.recommended_actions) > 0
        assert any('priority' in rec.lower() for rec in score.recommended_actions)
    
    def test_low_motivation_lead_scoring(self, scoring_service, low_motivation_lead):
        """Test scoring of low motivation lead"""
        score = scoring_service.score_lead(low_motivation_lead)
        
        # Low motivation lead should have lower scores
        assert score.motivation_score < 40
        assert score.deal_potential in [DealPotentialEnum.POOR, DealPotentialEnum.VERY_POOR, DealPotentialEnum.FAIR]
        assert score.priority_level in ['low', 'medium']
        assert score.estimated_close_probability < 0.7
    
    def test_property_condition_analysis(self, scoring_service, sample_lead):
        """Test property condition analysis"""
        condition = scoring_service._analyze_property_condition(sample_lead)
        
        assert isinstance(condition, PropertyConditionScore)
        assert 0 <= condition.overall_score <= 100
        assert 0 <= condition.structural_score <= 100
        assert 0 <= condition.cosmetic_score <= 100
        assert 0 <= condition.systems_score <= 100
        assert condition.repair_needed == sample_lead.repair_needed
        assert condition.estimated_repair_cost == sample_lead.estimated_repair_cost
        assert 0 <= condition.confidence_score <= 1
    
    def test_market_metrics_analysis(self, scoring_service, sample_lead):
        """Test market metrics analysis"""
        metrics = scoring_service._analyze_market_metrics(sample_lead)
        
        assert isinstance(metrics, MarketMetrics)
        assert metrics.days_on_market == sample_lead.property.days_on_market
        assert 0 <= metrics.market_activity_score <= 100
        assert metrics.seasonal_factor > 0
        
        # Check price reduction calculation
        expected_reduction = sample_lead.property.original_list_price - sample_lead.asking_price
        assert metrics.total_price_reduction == expected_reduction
    
    def test_financial_indicators_analysis(self, scoring_service, sample_lead):
        """Test financial indicators analysis"""
        indicators = scoring_service._analyze_financial_indicators(sample_lead)
        
        assert isinstance(indicators, FinancialIndicators)
        
        # Check equity calculation
        expected_equity = ((sample_lead.asking_price - sample_lead.mortgage_balance) / sample_lead.asking_price) * 100
        assert abs(indicators.equity_percentage - expected_equity) < 0.01
        
        # Check loan to value calculation
        expected_ltv = (sample_lead.mortgage_balance / sample_lead.asking_price) * 100
        assert abs(indicators.loan_to_value - expected_ltv) < 0.01
    
    def test_owner_profile_analysis(self, scoring_service, sample_lead):
        """Test owner profile analysis"""
        profile = scoring_service._analyze_owner_profile(sample_lead)
        
        assert isinstance(profile, OwnerProfile)
        assert profile.out_of_state_owner == sample_lead.owner_info.out_of_state
        assert profile.property_count == sample_lead.owner_info.property_count
        assert profile.contact_attempts == sample_lead.contact_attempts
        assert profile.investor_profile == (sample_lead.owner_info.property_count > 1)
    
    def test_motivation_score_calculation(self, scoring_service):
        """Test motivation score calculation"""
        indicators = [
            MotivationIndicator(
                factor=MotivationFactorEnum.FINANCIAL_DISTRESS,
                confidence=0.9,
                weight=8.0,
                evidence="Behind on payments"
            ),
            MotivationIndicator(
                factor=MotivationFactorEnum.PROPERTY_CONDITION,
                confidence=0.7,
                weight=6.0,
                evidence="Needs repairs"
            )
        ]
        
        config = scoring_service.default_config
        score = scoring_service._calculate_motivation_score(indicators, config)
        
        assert 0 <= score <= 100
        assert score > 0  # Should have positive score with indicators
    
    def test_overall_score_calculation(self, scoring_service):
        """Test overall score calculation with weighted components"""
        lead_score = LeadScore(
            lead_id=uuid.uuid4(),
            overall_score=0.0,
            deal_potential=DealPotentialEnum.POOR,
            confidence_score=0.0,
            motivation_score=80.0,
            financial_score=60.0,
            property_score=40.0,
            market_score=70.0,
            owner_score=50.0
        )
        
        config = scoring_service.default_config
        overall_score = scoring_service._calculate_overall_score(lead_score, config)
        
        assert 0 <= overall_score <= 100
        
        # Verify weighted calculation
        expected_score = (
            80.0 * (config.weights.motivation_weight / 100) +
            60.0 * (config.weights.financial_weight / 100) +
            40.0 * (config.weights.property_weight / 100) +
            70.0 * (config.weights.market_weight / 100) +
            50.0 * (config.weights.owner_weight / 100)
        )
        
        assert abs(overall_score - expected_score) < 0.01
    
    def test_deal_potential_determination(self, scoring_service):
        """Test deal potential category determination"""
        config = scoring_service.default_config
        
        # Test excellent threshold
        potential = scoring_service._determine_deal_potential(85.0, config)
        assert potential == DealPotentialEnum.EXCELLENT
        
        # Test good threshold
        potential = scoring_service._determine_deal_potential(65.0, config)
        assert potential == DealPotentialEnum.GOOD
        
        # Test fair threshold
        potential = scoring_service._determine_deal_potential(45.0, config)
        assert potential == DealPotentialEnum.FAIR
        
        # Test poor threshold
        potential = scoring_service._determine_deal_potential(25.0, config)
        assert potential == DealPotentialEnum.POOR
        
        # Test very poor
        potential = scoring_service._determine_deal_potential(15.0, config)
        assert potential == DealPotentialEnum.VERY_POOR
    
    def test_confidence_score_calculation(self, scoring_service, sample_lead):
        """Test confidence score calculation"""
        score = scoring_service.score_lead(sample_lead)
        
        assert 0 <= score.confidence_score <= 1
        
        # Lead with more data should have higher confidence
        assert score.confidence_score > 0.3  # Should be above minimum with sample data
    
    def test_recommendations_generation(self, scoring_service, high_motivation_lead):
        """Test recommendation generation"""
        score = scoring_service.score_lead(high_motivation_lead)
        
        assert len(score.recommended_actions) > 0
        
        # High motivation lead should get priority recommendations
        recommendations_text = ' '.join(score.recommended_actions).lower()
        assert any(word in recommendations_text for word in ['priority', 'immediately', 'urgent', 'high'])
    
    def test_profit_estimation(self, scoring_service, sample_lead):
        """Test profit potential estimation"""
        score = scoring_service.score_lead(sample_lead)
        
        if score.estimated_profit_potential is not None:
            assert score.estimated_profit_potential >= 0
    
    def test_batch_scoring(self, scoring_service, sample_lead, high_motivation_lead, low_motivation_lead):
        """Test batch lead scoring"""
        leads = [sample_lead, high_motivation_lead, low_motivation_lead]
        
        result = scoring_service.score_leads_batch(leads)
        
        assert isinstance(result, LeadScoringBatchResult)
        assert result.total_leads == 3
        assert result.successful_scores == 3
        assert result.failed_scores == 0
        assert len(result.scores) == 3
        assert len(result.errors) == 0
        assert result.processing_time > 0
        assert result.completed_at is not None
    
    def test_batch_scoring_with_errors(self, scoring_service):
        """Test batch scoring with invalid leads"""
        # Create a lead that will cause an error
        invalid_lead = Mock()
        invalid_lead.id = None  # This should cause an error
        
        valid_lead = Mock()
        valid_lead.id = uuid.uuid4()
        valid_lead.source = LeadSourceEnum.MLS
        valid_lead.asking_price = 200000
        valid_lead.property = Mock()
        valid_lead.property.id = uuid.uuid4()
        
        leads = [valid_lead, invalid_lead]
        
        result = scoring_service.score_leads_batch(leads)
        
        assert result.total_leads == 2
        assert result.successful_scores >= 1  # At least the valid lead should succeed
        assert result.failed_scores >= 0  # May or may not fail depending on error handling
    
    def test_custom_scoring_config(self, scoring_service, sample_lead):
        """Test scoring with custom configuration"""
        # Create custom config with different weights
        custom_weights = ScoringWeights(
            motivation_weight=40.0,
            financial_weight=30.0,
            property_weight=15.0,
            market_weight=10.0,
            owner_weight=5.0
        )
        
        custom_config = ScoringConfig(
            name="Custom Test Config",
            weights=custom_weights,
            excellent_threshold=85.0,
            good_threshold=70.0,
            fair_threshold=50.0,
            poor_threshold=30.0
        )
        
        score = scoring_service.score_lead(sample_lead, custom_config)
        
        assert isinstance(score, LeadScore)
        assert score.scoring_version == "1.0"
    
    def test_scoring_analytics(self, scoring_service):
        """Test scoring analytics generation"""
        analytics = scoring_service.get_scoring_analytics()
        
        assert isinstance(analytics, ScoringAnalytics)
        assert analytics.total_leads_scored >= 0
        assert 0 <= analytics.average_score <= 100
        assert isinstance(analytics.score_distribution, dict)
        assert all(potential in analytics.score_distribution for potential in DealPotentialEnum)
    
    def test_empty_lead_scoring(self, scoring_service):
        """Test scoring with minimal lead data"""
        minimal_lead = Mock()
        minimal_lead.id = uuid.uuid4()
        minimal_lead.source = LeadSourceEnum.MLS
        
        score = scoring_service.score_lead(minimal_lead)
        
        assert isinstance(score, LeadScore)
        assert score.overall_score >= 0
        assert score.confidence_score < 0.5  # Should have low confidence with minimal data
    
    def test_motivation_factor_weights(self, scoring_service):
        """Test that motivation factor weights are properly applied"""
        config = scoring_service.default_config
        
        # Verify all motivation factors have weights
        for factor in MotivationFactorEnum:
            assert factor in config.motivation_factor_weights
            assert config.motivation_factor_weights[factor] > 0
        
        # Verify high-impact factors have higher weights
        assert config.motivation_factor_weights[MotivationFactorEnum.FINANCIAL_DISTRESS] > \
               config.motivation_factor_weights[MotivationFactorEnum.MARKET_TIMING]
    
    def test_scoring_weights_validation(self):
        """Test scoring weights validation"""
        valid_weights = ScoringWeights(
            motivation_weight=30.0,
            financial_weight=25.0,
            property_weight=20.0,
            market_weight=15.0,
            owner_weight=10.0
        )
        
        assert valid_weights.validate_weights() == True
        
        invalid_weights = ScoringWeights(
            motivation_weight=50.0,
            financial_weight=25.0,
            property_weight=20.0,
            market_weight=15.0,
            owner_weight=10.0
        )
        
        assert invalid_weights.validate_weights() == False


class TestMotivationIndicatorDetection:
    """Test cases for motivation indicator detection"""
    
    def test_financial_distress_detection(self):
        """Test detection of financial distress indicators"""
        lead = Mock()
        lead.behind_on_payments = True
        lead.motivation_indicators = ['financial_distress']
        
        service = LeadScoringService()
        indicators = service._analyze_motivation_indicators(lead)
        
        factor_types = [indicator.factor for indicator in indicators]
        assert MotivationFactorEnum.FINANCIAL_DISTRESS in factor_types
    
    def test_property_condition_detection(self):
        """Test detection of property condition motivation"""
        lead = Mock()
        lead.property = Mock()
        lead.property.condition_score = 0.3  # Poor condition
        lead.motivation_indicators = []
        
        service = LeadScoringService()
        indicators = service._analyze_motivation_indicators(lead)
        
        factor_types = [indicator.factor for indicator in indicators]
        assert MotivationFactorEnum.PROPERTY_CONDITION in factor_types
    
    def test_vacant_property_detection(self):
        """Test detection of vacant property motivation"""
        lead = Mock()
        lead.property = Mock()
        lead.property.occupancy_status = 'vacant'
        lead.motivation_indicators = []
        
        service = LeadScoringService()
        indicators = service._analyze_motivation_indicators(lead)
        
        factor_types = [indicator.factor for indicator in indicators]
        assert MotivationFactorEnum.VACANT_PROPERTY in factor_types
    
    def test_out_of_state_owner_detection(self):
        """Test detection of out-of-state owner motivation"""
        lead = Mock()
        lead.owner_info = Mock()
        lead.owner_info.out_of_state = True
        lead.motivation_indicators = []
        
        service = LeadScoringService()
        indicators = service._analyze_motivation_indicators(lead)
        
        factor_types = [indicator.factor for indicator in indicators]
        assert MotivationFactorEnum.TIRED_LANDLORD in factor_types


class TestScoringEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_none_values_handling(self):
        """Test handling of None values in lead data"""
        lead = Mock()
        lead.id = uuid.uuid4()
        lead.source = LeadSourceEnum.MLS
        lead.asking_price = None
        lead.property = None
        lead.owner_info = None
        
        service = LeadScoringService()
        score = service.score_lead(lead)
        
        assert isinstance(score, LeadScore)
        assert score.overall_score >= 0
    
    def test_zero_values_handling(self):
        """Test handling of zero values"""
        lead = Mock()
        lead.id = uuid.uuid4()
        lead.source = LeadSourceEnum.MLS
        lead.asking_price = 0
        lead.mortgage_balance = 0
        lead.estimated_repair_cost = 0
        
        service = LeadScoringService()
        score = service.score_lead(lead)
        
        assert isinstance(score, LeadScore)
        assert score.overall_score >= 0
    
    def test_extreme_values_handling(self):
        """Test handling of extreme values"""
        lead = Mock()
        lead.id = uuid.uuid4()
        lead.source = LeadSourceEnum.MLS
        lead.asking_price = 10000000  # Very high price
        lead.mortgage_balance = 15000000  # Higher than asking price
        lead.estimated_repair_cost = 1000000  # Very high repair cost
        
        lead.property = Mock()
        lead.property.days_on_market = 1000  # Very long time on market
        lead.property.year_built = 1800  # Very old property
        
        service = LeadScoringService()
        score = service.score_lead(lead)
        
        assert isinstance(score, LeadScore)
        assert 0 <= score.overall_score <= 100