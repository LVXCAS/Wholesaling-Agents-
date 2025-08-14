"""
Unit tests for Investment Criteria System

Tests the investment criteria models, services, and API endpoints.
"""

import pytest
import uuid
from datetime import datetime
from typing import List

from app.models.investment_criteria import (
    InvestmentCriteria, CriteriaRule, CriteriaMatch, CriteriaTemplate,
    CriteriaOperator, GeographicCriteria, FinancialCriteria,
    PropertyCriteria, MarketCriteria, StrategyTypeEnum
)
from app.models.property import PropertyCreate, PropertyTypeEnum
from app.services.investment_criteria_service import (
    InvestmentCriteriaService, CriteriaTemplateService
)


class TestInvestmentCriteriaModels:
    """Test investment criteria data models"""
    
    def test_criteria_rule_creation(self):
        """Test creating a criteria rule"""
        rule = CriteriaRule(
            field="price",
            operator=CriteriaOperator.LESS_THAN,
            value=300000,
            weight=8.0,
            required=True
        )
        
        assert rule.field == "price"
        assert rule.operator == CriteriaOperator.LESS_THAN
        assert rule.value == 300000
        assert rule.weight == 8.0
        assert rule.required is True
    
    def test_criteria_rule_validation(self):
        """Test criteria rule validation"""
        # Test BETWEEN operator validation
        with pytest.raises(ValueError):
            CriteriaRule(
                field="price",
                operator=CriteriaOperator.BETWEEN,
                value=300000  # Should be a list for BETWEEN
            )
        
        # Valid BETWEEN rule
        rule = CriteriaRule(
            field="price",
            operator=CriteriaOperator.BETWEEN,
            value=[200000, 400000]
        )
        assert rule.value == [200000, 400000]
    
    def test_geographic_criteria(self):
        """Test geographic criteria model"""
        geo = GeographicCriteria(
            states=["CA", "TX", "FL"],
            cities=["Los Angeles", "Austin"],
            max_distance_from_point=50.0,
            center_lat=34.0522,
            center_lng=-118.2437,
            exclude_states=["NY"]
        )
        
        assert "CA" in geo.states
        assert geo.max_distance_from_point == 50.0
        assert "NY" in geo.exclude_states
    
    def test_financial_criteria(self):
        """Test financial criteria model"""
        fin = FinancialCriteria(
            min_price=100000,
            max_price=500000,
            min_cap_rate=8.0,
            min_cash_flow=200,
            min_roi=15.0,
            max_repair_cost=50000
        )
        
        assert fin.min_price == 100000
        assert fin.max_price == 500000
        assert fin.min_cap_rate == 8.0
        assert fin.min_cash_flow == 200
    
    def test_property_criteria(self):
        """Test property criteria model"""
        prop = PropertyCriteria(
            property_types=[PropertyTypeEnum.SINGLE_FAMILY, PropertyTypeEnum.CONDO],
            min_bedrooms=2,
            max_bedrooms=5,
            min_square_feet=1000,
            max_square_feet=3000,
            required_features=["garage", "yard"]
        )
        
        assert PropertyTypeEnum.SINGLE_FAMILY in prop.property_types
        assert prop.min_bedrooms == 2
        assert "garage" in prop.required_features
    
    def test_investment_criteria_creation(self):
        """Test creating complete investment criteria"""
        criteria = InvestmentCriteria(
            name="Test Flip Criteria",
            description="Criteria for fix-and-flip properties",
            strategy=StrategyTypeEnum.FLIP,
            geographic=GeographicCriteria(states=["CA"]),
            financial=FinancialCriteria(max_price=400000, min_roi=20.0),
            property=PropertyCriteria(property_types=[PropertyTypeEnum.SINGLE_FAMILY]),
            market=MarketCriteria(distressed_only=True)
        )
        
        assert criteria.name == "Test Flip Criteria"
        assert criteria.strategy == StrategyTypeEnum.FLIP
        assert criteria.geographic.states == ["CA"]
        assert criteria.financial.max_price == 400000
        assert criteria.market.distressed_only is True
    
    def test_criteria_match_model(self):
        """Test criteria match result model"""
        match = CriteriaMatch(
            property_id=uuid.uuid4(),
            criteria_id=uuid.uuid4(),
            overall_score=85.5,
            meets_required=True,
            geographic_score=90.0,
            financial_score=80.0,
            property_score=85.0,
            confidence_score=0.9
        )
        
        assert match.overall_score == 85.5
        assert match.meets_required is True
        assert match.confidence_score == 0.9


class TestInvestmentCriteriaService:
    """Test investment criteria service"""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        return InvestmentCriteriaService()
    
    @pytest.fixture
    def sample_property(self):
        """Create sample property for testing"""
        return PropertyCreate(
            address="123 Test St",
            city="Los Angeles",
            state="CA",
            zip_code="90210",
            property_type=PropertyTypeEnum.SINGLE_FAMILY,
            bedrooms=3,
            bathrooms=2.0,
            square_feet=1500,
            year_built=1980,
            listing_price=350000
        )
    
    @pytest.fixture
    def sample_criteria(self):
        """Create sample criteria for testing"""
        return InvestmentCriteria(
            name="Test Criteria",
            strategy=StrategyTypeEnum.FLIP,
            geographic=GeographicCriteria(states=["CA"]),
            financial=FinancialCriteria(
                min_price=200000,
                max_price=500000,
                min_roi=15.0
            ),
            property=PropertyCriteria(
                property_types=[PropertyTypeEnum.SINGLE_FAMILY],
                min_bedrooms=2,
                max_bedrooms=5
            )
        )
    
    def test_create_criteria(self, service):
        """Test creating investment criteria"""
        criteria = InvestmentCriteria(
            name="Test Criteria",
            strategy=StrategyTypeEnum.RENTAL
        )
        
        result = service.create_criteria(criteria)
        assert result.id is not None
        assert result.name == "Test Criteria"
        assert result.created_at is not None
    
    def test_evaluate_property_geographic_match(self, service, sample_property, sample_criteria):
        """Test property evaluation with geographic criteria"""
        match = service.evaluate_property(sample_property, sample_criteria)
        
        # PropertyCreate doesn't have an id, so we check that one was generated
        assert match.property_id is not None
        assert match.criteria_id == sample_criteria.id
        assert match.geographic_score == 100.0  # CA property matches CA criteria
        assert match.overall_score > 0
    
    def test_evaluate_property_geographic_mismatch(self, service, sample_property, sample_criteria):
        """Test property evaluation with geographic mismatch"""
        # Change property state to non-matching state
        sample_property.state = "NY"
        
        match = service.evaluate_property(sample_property, sample_criteria)
        
        assert match.geographic_score == 0.0  # NY property doesn't match CA criteria
        assert match.meets_required is False
        assert "geographic_criteria" in match.failed_required_rules
    
    def test_evaluate_property_financial_criteria(self, service, sample_property, sample_criteria):
        """Test property evaluation with financial criteria"""
        match = service.evaluate_property(sample_property, sample_criteria)
        
        # Property price (350000) is within range (200000-500000)
        assert match.financial_score == 100.0
        assert match.meets_required is True
    
    def test_evaluate_property_price_too_high(self, service, sample_property, sample_criteria):
        """Test property evaluation with price too high"""
        sample_property.listing_price = 600000  # Above max_price of 500000
        
        match = service.evaluate_property(sample_property, sample_criteria)
        
        assert match.financial_score == 0.0
        assert match.meets_required is False
    
    def test_evaluate_property_criteria(self, service, sample_property, sample_criteria):
        """Test property evaluation with property criteria"""
        match = service.evaluate_property(sample_property, sample_criteria)
        
        # Property has 3 bedrooms (within 2-5 range) and is single family
        assert match.property_score == 100.0
        assert match.meets_required is True
    
    def test_evaluate_property_bedrooms_mismatch(self, service, sample_property, sample_criteria):
        """Test property evaluation with bedroom mismatch"""
        sample_property.bedrooms = 1  # Below min_bedrooms of 2
        
        match = service.evaluate_property(sample_property, sample_criteria)
        
        # Should get penalty but not fail completely
        assert match.property_score < 100.0
        assert match.property_score > 0.0
    
    def test_evaluate_custom_rules(self, service, sample_property):
        """Test evaluation with custom rules"""
        custom_rules = [
            CriteriaRule(
                field="square_feet",
                operator=CriteriaOperator.GREATER_THAN,
                value=1000,
                weight=5.0,
                required=True
            ),
            CriteriaRule(
                field="year_built",
                operator=CriteriaOperator.GREATER_EQUAL,
                value=1970,
                weight=3.0,
                required=False
            )
        ]
        
        criteria = InvestmentCriteria(
            name="Custom Rules Test",
            strategy=StrategyTypeEnum.FLIP,
            custom_rules=custom_rules
        )
        
        match = service.evaluate_property(sample_property, criteria)
        
        # Property has 1500 sq ft (>1000) and built in 1980 (>=1970)
        assert match.custom_rules_score == 100.0
        assert match.meets_required is True
    
    def test_evaluate_custom_rules_required_failure(self, service, sample_property):
        """Test evaluation with failing required custom rule"""
        custom_rules = [
            CriteriaRule(
                field="square_feet",
                operator=CriteriaOperator.GREATER_THAN,
                value=2000,  # Property only has 1500 sq ft
                weight=5.0,
                required=True
            )
        ]
        
        criteria = InvestmentCriteria(
            name="Required Rule Test",
            strategy=StrategyTypeEnum.FLIP,
            custom_rules=custom_rules
        )
        
        match = service.evaluate_property(sample_property, criteria)
        
        assert match.custom_rules_score == 0.0
        assert match.meets_required is False
        assert "custom_rules" in match.failed_required_rules
    
    def test_batch_evaluate_properties(self, service, sample_criteria):
        """Test batch property evaluation"""
        properties = [
            PropertyCreate(
                address="123 Test St",
                city="Los Angeles",
                state="CA",
                zip_code="90210",
                property_type=PropertyTypeEnum.SINGLE_FAMILY,
                bedrooms=3,
                listing_price=300000
            ),
            PropertyCreate(
                address="456 Test Ave",
                city="San Francisco",
                state="CA",
                zip_code="94102",
                property_type=PropertyTypeEnum.CONDO,
                bedrooms=2,
                listing_price=450000
            )
        ]
        
        matches = service.batch_evaluate_properties(properties, sample_criteria)
        
        assert len(matches) == 2
        assert all(isinstance(match, CriteriaMatch) for match in matches)
        # PropertyCreate doesn't have ids, but matches should have generated property_ids
        assert matches[0].property_id is not None
        assert matches[1].property_id is not None
    
    def test_get_matching_summary(self, service, sample_criteria):
        """Test generating matching summary"""
        properties = [
            PropertyCreate(
                address="123 Test St",
                city="Los Angeles",
                state="CA",
                zip_code="90210",
                property_type=PropertyTypeEnum.SINGLE_FAMILY,
                bedrooms=3,
                listing_price=300000
            ),
            PropertyCreate(
                address="456 Test Ave",
                city="Austin",
                state="TX",  # Won't match CA criteria
                zip_code="78701",
                property_type=PropertyTypeEnum.SINGLE_FAMILY,
                bedrooms=3,
                listing_price=250000
            )
        ]
        
        matches = service.batch_evaluate_properties(properties, sample_criteria)
        summary = service.get_matching_summary(matches)
        
        assert summary.total_properties_evaluated == 2
        assert summary.properties_meeting_criteria == 1  # Only CA property meets criteria
        assert len(summary.top_matches) <= 10
        assert summary.average_score >= 0.0


class TestCriteriaTemplateService:
    """Test criteria template service"""
    
    @pytest.fixture
    def service(self):
        """Create template service instance"""
        return CriteriaTemplateService()
    
    def test_create_template(self, service):
        """Test creating criteria template"""
        criteria = InvestmentCriteria(
            name="Template Criteria",
            strategy=StrategyTypeEnum.RENTAL
        )
        
        template = CriteriaTemplate(
            name="Rental Template",
            description="Template for rental properties",
            strategy=StrategyTypeEnum.RENTAL,
            criteria=criteria,
            is_public=True
        )
        
        result = service.create_template(template)
        assert result.id is not None
        assert result.name == "Rental Template"
        assert result.is_public is True
    
    def test_get_default_templates(self, service):
        """Test getting default templates"""
        templates = service.get_default_templates()
        
        assert "flip" in templates
        assert "rental" in templates
        
        flip_template = templates["flip"]
        assert flip_template.strategy == "flip"
        assert flip_template.criteria.strategy == "flip"
        assert flip_template.is_public is True
        
        rental_template = templates["rental"]
        assert rental_template.strategy == "rental"
        assert rental_template.criteria.strategy == "rental"


class TestCriteriaOperators:
    """Test criteria operators"""
    
    @pytest.fixture
    def service(self):
        return InvestmentCriteriaService()
    
    def test_equals_operator(self, service):
        """Test EQUALS operator"""
        property_data = PropertyCreate(
            address="123 Test St",
            city="Test City",
            state="CA",
            zip_code="12345",
            bedrooms=3
        )
        
        rule = CriteriaRule(
            field="bedrooms",
            operator=CriteriaOperator.EQUALS,
            value=3
        )
        
        result = service._evaluate_single_rule(property_data, rule)
        assert result is True
        
        rule.value = 4
        result = service._evaluate_single_rule(property_data, rule)
        assert result is False
    
    def test_greater_than_operator(self, service):
        """Test GREATER_THAN operator"""
        property_data = PropertyCreate(
            address="123 Test St",
            city="Test City",
            state="CA",
            zip_code="12345",
            square_feet=1500
        )
        
        rule = CriteriaRule(
            field="square_feet",
            operator=CriteriaOperator.GREATER_THAN,
            value=1000
        )
        
        result = service._evaluate_single_rule(property_data, rule)
        assert result is True
        
        rule.value = 2000
        result = service._evaluate_single_rule(property_data, rule)
        assert result is False
    
    def test_between_operator(self, service):
        """Test BETWEEN operator"""
        property_data = PropertyCreate(
            address="123 Test St",
            city="Test City",
            state="CA",
            zip_code="12345",
            listing_price=300000
        )
        
        rule = CriteriaRule(
            field="listing_price",
            operator=CriteriaOperator.BETWEEN,
            value=[200000, 400000]
        )
        
        result = service._evaluate_single_rule(property_data, rule)
        assert result is True
        
        rule.value = [350000, 500000]
        result = service._evaluate_single_rule(property_data, rule)
        assert result is False
    
    def test_in_operator(self, service):
        """Test IN operator"""
        property_data = PropertyCreate(
            address="123 Test St",
            city="Test City",
            state="CA",
            zip_code="12345"
        )
        
        rule = CriteriaRule(
            field="state",
            operator=CriteriaOperator.IN,
            value=["CA", "TX", "FL"]
        )
        
        result = service._evaluate_single_rule(property_data, rule)
        assert result is True
        
        rule.value = ["NY", "NJ"]
        result = service._evaluate_single_rule(property_data, rule)
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__])