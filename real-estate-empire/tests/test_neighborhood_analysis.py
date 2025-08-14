"""
Unit tests for the Neighborhood Analysis System

Tests the neighborhood boundary detection, trend analysis, school and amenity scoring,
and crime data integration functionality.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.services.neighborhood_analysis_service import NeighborhoodAnalysisService
from app.models.neighborhood_analysis import (
    GeographicBoundary, PropertySale, MarketTrend, School, Amenity, CrimeIncident,
    NeighborhoodScore, NeighborhoodAnalysis, NeighborhoodComparison,
    NeighborhoodSearchCriteria, NeighborhoodSearchResult,
    TrendDirectionEnum, AmenityTypeEnum, SchoolTypeEnum, CrimeTypeEnum
)


class TestNeighborhoodAnalysisService:
    """Test cases for NeighborhoodAnalysisService"""
    
    @pytest.fixture
    def analysis_service(self):
        """Create a NeighborhoodAnalysisService instance for testing"""
        return NeighborhoodAnalysisService()
    
    @pytest.fixture
    def sample_boundary(self):
        """Create a sample geographic boundary for testing"""
        return GeographicBoundary(
            name="Test Neighborhood",
            boundary_type="circular",
            coordinates=[[40.7128, -74.0060], [40.7138, -74.0050], [40.7118, -74.0070]],
            north_lat=40.7138,
            south_lat=40.7118,
            east_lng=-74.0050,
            west_lng=-74.0070,
            center_lat=40.7128,
            center_lng=-74.0060,
            area_sq_miles=1.0
        )
    
    @pytest.fixture
    def sample_schools(self):
        """Create sample schools for testing"""
        return [
            School(
                name="Elementary School 1",
                school_type=SchoolTypeEnum.ELEMENTARY,
                address="123 School St",
                latitude=40.7130,
                longitude=-74.0055,
                rating=8.5,
                enrollment=400,
                student_teacher_ratio=15,
                test_scores={"math": 85, "reading": 88, "science": 82}
            ),
            School(
                name="High School 1",
                school_type=SchoolTypeEnum.HIGH,
                address="456 Education Ave",
                latitude=40.7125,
                longitude=-74.0065,
                rating=7.8,
                enrollment=1200,
                student_teacher_ratio=18,
                test_scores={"math": 78, "reading": 82, "science": 75}
            )
        ]
    
    @pytest.fixture
    def sample_amenities(self):
        """Create sample amenities for testing"""
        return [
            Amenity(
                name="Grocery Store",
                amenity_type=AmenityTypeEnum.GROCERY,
                address="789 Main St",
                latitude=40.7132,
                longitude=-74.0058,
                rating=4.2,
                review_count=150
            ),
            Amenity(
                name="City Park",
                amenity_type=AmenityTypeEnum.PARK,
                address="321 Park Ave",
                latitude=40.7120,
                longitude=-74.0062,
                rating=4.5,
                review_count=89
            )
        ]
    
    @pytest.fixture
    def sample_crime_incidents(self):
        """Create sample crime incidents for testing"""
        return [
            CrimeIncident(
                incident_date=datetime.now() - timedelta(days=30),
                latitude=40.7129,
                longitude=-74.0061,
                crime_type=CrimeTypeEnum.PROPERTY,
                crime_description="Theft from vehicle",
                severity=2,
                resolved=True
            ),
            CrimeIncident(
                incident_date=datetime.now() - timedelta(days=60),
                latitude=40.7127,
                longitude=-74.0059,
                crime_type=CrimeTypeEnum.VIOLENT,
                crime_description="Assault",
                severity=4,
                resolved=False
            )
        ]
    
    def test_create_circular_boundary(self, analysis_service):
        """Test creation of circular boundary"""
        center_lat, center_lng = 40.7128, -74.0060
        radius_miles = 1.0
        
        boundary_points = analysis_service._create_circular_boundary(center_lat, center_lng, radius_miles)
        
        assert len(boundary_points) == 32  # Default number of points
        assert all(len(point) == 2 for point in boundary_points)  # Each point has lat, lng
        
        # Check that points form a rough circle around center
        for point in boundary_points:
            lat, lng = point
            # Points should be within reasonable distance of center
            assert abs(lat - center_lat) <= 0.02  # Rough check
            assert abs(lng - center_lng) <= 0.02
    
    @patch('app.services.neighborhood_analysis_service.Nominatim')
    def test_detect_neighborhood_boundary(self, mock_nominatim, analysis_service):
        """Test neighborhood boundary detection"""
        # Mock geocoder response
        mock_location = Mock()
        mock_location.latitude = 40.7128
        mock_location.longitude = -74.0060
        
        mock_geocoder = Mock()
        mock_geocoder.geocode.return_value = mock_location
        mock_nominatim.return_value = mock_geocoder
        
        address = "123 Test St, New York, NY"
        radius = 1.5
        
        boundary = analysis_service.detect_neighborhood_boundary(address, radius)
        
        assert isinstance(boundary, GeographicBoundary)
        assert boundary.name == f"Neighborhood around {address}"
        assert boundary.boundary_type == "circular"
        assert boundary.center_lat == 40.7128
        assert boundary.center_lng == -74.0060
        assert abs(boundary.area_sq_miles - (3.14159 * radius ** 2)) < 0.1
        assert len(boundary.coordinates) == 32
    
    @patch('app.services.neighborhood_analysis_service.Nominatim')
    def test_detect_neighborhood_boundary_invalid_address(self, mock_nominatim, analysis_service):
        """Test boundary detection with invalid address"""
        mock_geocoder = Mock()
        mock_geocoder.geocode.return_value = None
        mock_nominatim.return_value = mock_geocoder
        
        with pytest.raises(ValueError, match="Could not geocode address"):
            analysis_service.detect_neighborhood_boundary("Invalid Address")
    
    def test_analyze_market_trends(self, analysis_service, sample_boundary):
        """Test market trend analysis"""
        months_back = 6
        trends = analysis_service.analyze_market_trends(sample_boundary, months_back)
        
        assert len(trends) == months_back
        assert all(isinstance(trend, MarketTrend) for trend in trends)
        
        # Check that trends are in chronological order (most recent first)
        for i in range(len(trends) - 1):
            assert trends[i].period_end > trends[i + 1].period_end
        
        # Verify trend data structure
        for trend in trends:
            assert trend.median_price > 0
            assert trend.average_price > 0
            assert trend.sales_count > 0
            assert trend.price_trend in TrendDirectionEnum
            assert trend.volume_trend in TrendDirectionEnum
    
    def test_find_schools_in_area(self, analysis_service, sample_boundary):
        """Test finding schools in area"""
        schools = analysis_service.find_schools_in_area(sample_boundary)
        
        assert len(schools) > 0
        assert all(isinstance(school, School) for school in schools)
        
        # Check that different school types are represented
        school_types = set(school.school_type for school in schools)
        assert SchoolTypeEnum.ELEMENTARY in school_types
        assert SchoolTypeEnum.HIGH in school_types
        
        # Verify school data structure
        for school in schools:
            assert school.name
            assert school.school_type in SchoolTypeEnum
            assert school.latitude != 0
            assert school.longitude != 0
            assert school.rating is not None
            assert school.rating >= 0
    
    def test_find_amenities_in_area(self, analysis_service, sample_boundary):
        """Test finding amenities in area"""
        amenities = analysis_service.find_amenities_in_area(sample_boundary)
        
        assert len(amenities) > 0
        assert all(isinstance(amenity, Amenity) for amenity in amenities)
        
        # Check that different amenity types are represented
        amenity_types = set(amenity.amenity_type for amenity in amenities)
        assert len(amenity_types) > 1  # Should have variety
        
        # Verify amenity data structure
        for amenity in amenities:
            assert amenity.name
            assert amenity.amenity_type in AmenityTypeEnum
            assert amenity.latitude != 0
            assert amenity.longitude != 0
            assert amenity.rating is not None
            assert amenity.rating >= 0
    
    def test_get_crime_data(self, analysis_service, sample_boundary):
        """Test getting crime data"""
        months_back = 12
        incidents = analysis_service.get_crime_data(sample_boundary, months_back)
        
        assert len(incidents) > 0
        assert all(isinstance(incident, CrimeIncident) for incident in incidents)
        
        # Check that different crime types are represented
        crime_types = set(incident.crime_type for incident in incidents)
        assert len(crime_types) > 1
        
        # Verify incident data structure
        for incident in incidents:
            assert incident.incident_date
            assert incident.latitude != 0
            assert incident.longitude != 0
            assert incident.crime_type in CrimeTypeEnum
            assert incident.crime_description
            assert incident.severity is not None
            assert 1 <= incident.severity <= 5
    
    def test_calculate_school_score(self, analysis_service, sample_schools):
        """Test school score calculation"""
        score = analysis_service.calculate_school_score(sample_schools)
        
        assert 0 <= score <= 100
        assert score > 0  # Should have positive score with good schools
        
        # Test with empty schools list
        empty_score = analysis_service.calculate_school_score([])
        assert empty_score == 0.0
        
        # Test with schools without ratings
        schools_no_rating = [
            School(
                name="Test School",
                school_type=SchoolTypeEnum.ELEMENTARY,
                address="Test Address",
                latitude=40.0,
                longitude=-74.0,
                rating=None
            )
        ]
        no_rating_score = analysis_service.calculate_school_score(schools_no_rating)
        assert no_rating_score == 0.0
    
    def test_calculate_amenity_score(self, analysis_service, sample_amenities):
        """Test amenity score calculation"""
        center_lat, center_lng = 40.7128, -74.0060
        score = analysis_service.calculate_amenity_score(sample_amenities, center_lat, center_lng)
        
        assert 0 <= score <= 100
        assert score > 0  # Should have positive score with amenities
        
        # Test with empty amenities list
        empty_score = analysis_service.calculate_amenity_score([], center_lat, center_lng)
        assert empty_score == 0.0
    
    def test_calculate_safety_score(self, analysis_service, sample_crime_incidents):
        """Test safety score calculation"""
        area_sq_miles = 1.0
        score = analysis_service.calculate_safety_score(sample_crime_incidents, area_sq_miles)
        
        assert 0 <= score <= 100
        
        # Test with no crime incidents (should be perfect score)
        perfect_score = analysis_service.calculate_safety_score([], area_sq_miles)
        assert perfect_score == 100.0
        
        # Test that violent crimes lower the score more than property crimes
        violent_incidents = [
            CrimeIncident(
                incident_date=datetime.now() - timedelta(days=30),
                latitude=40.0,
                longitude=-74.0,
                crime_type=CrimeTypeEnum.VIOLENT,
                crime_description="Violent crime",
                severity=4
            )
        ]
        
        property_incidents = [
            CrimeIncident(
                incident_date=datetime.now() - timedelta(days=30),
                latitude=40.0,
                longitude=-74.0,
                crime_type=CrimeTypeEnum.PROPERTY,
                crime_description="Property crime",
                severity=2
            )
        ]
        
        violent_score = analysis_service.calculate_safety_score(violent_incidents, area_sq_miles)
        property_score = analysis_service.calculate_safety_score(property_incidents, area_sq_miles)
        
        assert violent_score < property_score  # Violent crimes should result in lower safety score
    
    def test_calculate_market_trend_score(self, analysis_service):
        """Test market trend score calculation"""
        # Test with rising trend
        rising_trend = MarketTrend(
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now(),
            median_price=300000,
            average_price=320000,
            price_change_percent=8.0,
            price_trend=TrendDirectionEnum.RISING,
            sales_count=25,
            volume_change_percent=5.0,
            volume_trend=TrendDirectionEnum.RISING
        )
        
        rising_score = analysis_service.calculate_market_trend_score([rising_trend])
        assert rising_score > 50  # Should be above neutral
        
        # Test with declining trend
        declining_trend = MarketTrend(
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now(),
            median_price=300000,
            average_price=320000,
            price_change_percent=-5.0,
            price_trend=TrendDirectionEnum.DECLINING,
            sales_count=25,
            volume_change_percent=-10.0,
            volume_trend=TrendDirectionEnum.DECLINING
        )
        
        declining_score = analysis_service.calculate_market_trend_score([declining_trend])
        assert declining_score < 50  # Should be below neutral
        
        # Test with empty trends
        empty_score = analysis_service.calculate_market_trend_score([])
        assert empty_score == 50.0  # Should be neutral
    
    def test_calculate_neighborhood_score(self, analysis_service, sample_boundary, sample_schools, 
                                        sample_amenities, sample_crime_incidents):
        """Test comprehensive neighborhood score calculation"""
        trends = [
            MarketTrend(
                period_start=datetime.now() - timedelta(days=30),
                period_end=datetime.now(),
                median_price=300000,
                average_price=320000,
                price_change_percent=5.0,
                price_trend=TrendDirectionEnum.RISING,
                sales_count=25,
                volume_change_percent=3.0,
                volume_trend=TrendDirectionEnum.STABLE
            )
        ]
        
        score = analysis_service.calculate_neighborhood_score(
            sample_boundary, trends, sample_schools, sample_amenities, sample_crime_incidents
        )
        
        assert isinstance(score, NeighborhoodScore)
        assert score.neighborhood_id == sample_boundary.id
        assert 0 <= score.overall_score <= 100
        assert 0 <= score.market_trend_score <= 100
        assert 0 <= score.school_score <= 100
        assert 0 <= score.amenity_score <= 100
        assert 0 <= score.safety_score <= 100
        assert 0 <= score.appreciation_potential <= 100
        assert 0 <= score.rental_demand <= 100
        assert 0 <= score.liquidity_score <= 100
        assert 0 <= score.confidence_score <= 1
        
        # Check data point counts
        assert score.sales_data_points == len(trends)
        assert score.schools_analyzed == len(sample_schools)
        assert score.amenities_analyzed == len(sample_amenities)
        assert score.crime_incidents_analyzed == len(sample_crime_incidents)
    
    @patch('app.services.neighborhood_analysis_service.Nominatim')
    def test_analyze_neighborhood(self, mock_nominatim, analysis_service):
        """Test complete neighborhood analysis"""
        # Mock geocoder response
        mock_location = Mock()
        mock_location.latitude = 40.7128
        mock_location.longitude = -74.0060
        
        mock_geocoder = Mock()
        mock_geocoder.geocode.return_value = mock_location
        mock_nominatim.return_value = mock_geocoder
        
        address = "123 Test St, New York, NY"
        analysis = analysis_service.analyze_neighborhood(address)
        
        assert isinstance(analysis, NeighborhoodAnalysis)
        assert isinstance(analysis.boundary, GeographicBoundary)
        assert isinstance(analysis.neighborhood_score, NeighborhoodScore)
        assert len(analysis.schools) > 0
        assert len(analysis.amenities) > 0
        assert len(analysis.crime_incidents) > 0
        assert len(analysis.historical_trends) > 0
        assert len(analysis.investment_highlights) > 0
        assert isinstance(analysis.crime_stats, dict)
        
        # Check that all crime types are represented in stats
        for crime_type in CrimeTypeEnum:
            assert crime_type in analysis.crime_stats
    
    def test_search_neighborhoods(self, analysis_service):
        """Test neighborhood search functionality"""
        criteria = NeighborhoodSearchCriteria(
            center_lat=40.7128,
            center_lng=-74.0060,
            radius_miles=5.0,
            min_overall_score=60.0,
            min_school_score=70.0,
            min_safety_score=65.0
        )
        
        with patch.object(analysis_service, 'analyze_neighborhood') as mock_analyze:
            # Mock analysis results
            mock_analysis = Mock()
            mock_analysis.neighborhood_score = Mock()
            mock_analysis.neighborhood_score.overall_score = 75.0
            mock_analysis.neighborhood_score.school_score = 80.0
            mock_analysis.neighborhood_score.safety_score = 70.0
            mock_analysis.neighborhood_score.appreciation_potential = 65.0
            mock_analysis.current_market_trend = None
            mock_analysis.amenities = []
            mock_analysis.schools = []
            
            mock_analyze.return_value = mock_analysis
            
            result = analysis_service.search_neighborhoods(criteria)
            
            assert isinstance(result, NeighborhoodSearchResult)
            assert result.total_found >= 0
            assert result.search_criteria == criteria
            assert result.search_time_seconds > 0
            assert isinstance(result.neighborhoods, list)
    
    def test_meets_criteria(self, analysis_service):
        """Test criteria matching logic"""
        # Create mock analysis
        mock_analysis = Mock()
        mock_analysis.neighborhood_score = Mock()
        mock_analysis.neighborhood_score.overall_score = 75.0
        mock_analysis.neighborhood_score.school_score = 80.0
        mock_analysis.neighborhood_score.safety_score = 70.0
        mock_analysis.neighborhood_score.appreciation_potential = 65.0
        mock_analysis.current_market_trend = Mock()
        mock_analysis.current_market_trend.median_price = 350000
        mock_analysis.amenities = [
            Mock(amenity_type=AmenityTypeEnum.GROCERY),
            Mock(amenity_type=AmenityTypeEnum.PARK)
        ]
        mock_analysis.schools = [Mock(rating=8.5)]
        
        # Test criteria that should match
        matching_criteria = NeighborhoodSearchCriteria(
            min_overall_score=70.0,
            min_school_score=75.0,
            min_safety_score=65.0,
            max_median_price=400000,
            required_amenities=[AmenityTypeEnum.GROCERY],
            min_school_rating=8.0
        )
        
        assert analysis_service._meets_criteria(mock_analysis, matching_criteria) == True
        
        # Test criteria that should not match
        non_matching_criteria = NeighborhoodSearchCriteria(
            min_overall_score=80.0,  # Too high
            min_school_score=85.0,   # Too high
            max_median_price=300000,  # Too low
            required_amenities=[AmenityTypeEnum.HOSPITAL],  # Not available
            min_school_rating=9.0    # Too high
        )
        
        assert analysis_service._meets_criteria(mock_analysis, non_matching_criteria) == False
    
    def test_compare_neighborhoods(self, analysis_service):
        """Test neighborhood comparison functionality"""
        # Create mock neighborhood analyses
        neighborhood1 = Mock()
        neighborhood1.id = uuid.uuid4()
        neighborhood1.neighborhood_score = Mock()
        neighborhood1.neighborhood_score.overall_score = 85.0
        neighborhood1.neighborhood_score.school_score = 90.0
        neighborhood1.neighborhood_score.safety_score = 80.0
        neighborhood1.neighborhood_score.appreciation_potential = 75.0
        neighborhood1.neighborhood_score.rental_demand = 85.0
        neighborhood1.current_market_trend = Mock()
        neighborhood1.current_market_trend.median_price = 400000
        
        neighborhood2 = Mock()
        neighborhood2.id = uuid.uuid4()
        neighborhood2.neighborhood_score = Mock()
        neighborhood2.neighborhood_score.overall_score = 75.0
        neighborhood2.neighborhood_score.school_score = 70.0
        neighborhood2.neighborhood_score.safety_score = 90.0
        neighborhood2.neighborhood_score.appreciation_potential = 85.0
        neighborhood2.neighborhood_score.rental_demand = 75.0
        neighborhood2.current_market_trend = Mock()
        neighborhood2.current_market_trend.median_price = 300000
        
        neighborhoods = [neighborhood1, neighborhood2]
        
        comparison = analysis_service.compare_neighborhoods(neighborhoods)
        
        assert isinstance(comparison, NeighborhoodComparison)
        assert len(comparison.neighborhoods) == 2
        assert 'overall' in comparison.rankings
        assert 'schools' in comparison.rankings
        assert 'safety' in comparison.rankings
        assert 'appreciation' in comparison.rankings
        
        # Check that rankings are correct
        assert comparison.rankings['overall'][0] == neighborhood1.id  # Higher overall score
        assert comparison.rankings['schools'][0] == neighborhood1.id  # Higher school score
        assert comparison.rankings['safety'][0] == neighborhood2.id   # Higher safety score
        
        assert comparison.best_for_families is not None
        assert comparison.best_for_rental is not None
        assert comparison.best_for_appreciation is not None
        assert comparison.best_value is not None
        assert comparison.comparison_summary
    
    def test_compare_neighborhoods_insufficient_data(self, analysis_service):
        """Test comparison with insufficient neighborhoods"""
        with pytest.raises(ValueError, match="Need at least 2 neighborhoods to compare"):
            analysis_service.compare_neighborhoods([Mock()])
    
    def test_generate_investment_highlights(self, analysis_service):
        """Test investment highlights generation"""
        # Create high-scoring neighborhood score
        high_score = NeighborhoodScore(
            neighborhood_id=uuid.uuid4(),
            overall_score=85.0,
            market_trend_score=80.0,
            school_score=85.0,
            amenity_score=75.0,
            safety_score=90.0,
            appreciation_potential=80.0,
            rental_demand=85.0,
            liquidity_score=75.0,
            confidence_score=0.8
        )
        
        trends = [
            MarketTrend(
                period_start=datetime.now() - timedelta(days=30),
                period_end=datetime.now(),
                median_price=300000,
                average_price=320000,
                price_change_percent=7.5,
                price_trend=TrendDirectionEnum.RISING,
                sales_count=25,
                volume_change_percent=3.0,
                volume_trend=TrendDirectionEnum.STABLE
            )
        ]
        
        highlights = analysis_service._generate_investment_highlights(high_score, trends, [], [])
        
        assert len(highlights) > 0
        assert any("excellent" in highlight.lower() or "strong" in highlight.lower() for highlight in highlights)
        assert any("school" in highlight.lower() for highlight in highlights)
        assert any("safe" in highlight.lower() or "crime" in highlight.lower() for highlight in highlights)
        assert any("appreciation" in highlight.lower() for highlight in highlights)
    
    def test_generate_risk_factors(self, analysis_service):
        """Test risk factors generation"""
        # Create low-scoring neighborhood score
        low_score = NeighborhoodScore(
            neighborhood_id=uuid.uuid4(),
            overall_score=35.0,
            market_trend_score=30.0,
            school_score=40.0,
            amenity_score=45.0,
            safety_score=25.0,
            appreciation_potential=30.0,
            rental_demand=35.0,
            liquidity_score=30.0,
            confidence_score=0.6
        )
        
        declining_trends = [
            MarketTrend(
                period_start=datetime.now() - timedelta(days=30),
                period_end=datetime.now(),
                median_price=300000,
                average_price=320000,
                price_change_percent=-5.0,
                price_trend=TrendDirectionEnum.DECLINING,
                sales_count=25,
                volume_change_percent=-8.0,
                volume_trend=TrendDirectionEnum.DECLINING
            )
        ]
        
        recent_violent_crimes = [
            CrimeIncident(
                incident_date=datetime.now() - timedelta(days=15),
                latitude=40.0,
                longitude=-74.0,
                crime_type=CrimeTypeEnum.VIOLENT,
                crime_description="Recent violent crime",
                severity=4
            ) for _ in range(3)
        ]
        
        risk_factors = analysis_service._generate_risk_factors(low_score, declining_trends, recent_violent_crimes)
        
        assert len(risk_factors) > 0
        assert any("crime" in factor.lower() for factor in risk_factors)
        assert any("school" in factor.lower() for factor in risk_factors)
        assert any("declining" in factor.lower() or "weak" in factor.lower() for factor in risk_factors)
        assert any("violent" in factor.lower() for factor in risk_factors)


class TestGeographicBoundary:
    """Test cases for GeographicBoundary model"""
    
    def test_contains_point(self):
        """Test point-in-polygon detection"""
        # Create a simple square boundary
        boundary = GeographicBoundary(
            name="Test Square",
            boundary_type="polygon",
            coordinates=[
                [40.0, -74.0],  # Bottom-left
                [40.0, -73.0],  # Bottom-right
                [41.0, -73.0],  # Top-right
                [41.0, -74.0]   # Top-left
            ],
            north_lat=41.0,
            south_lat=40.0,
            east_lng=-73.0,
            west_lng=-74.0,
            center_lat=40.5,
            center_lng=-73.5
        )
        
        # Test point inside boundary
        assert boundary.contains_point(40.5, -73.5) == True
        
        # Test point outside boundary
        assert boundary.contains_point(42.0, -73.5) == False
        assert boundary.contains_point(40.5, -72.0) == False
        
        # Test point on boundary (edge case)
        assert boundary.contains_point(40.0, -73.5) == True  # On bottom edge


class TestSchoolAndAmenityDistanceCalculation:
    """Test distance calculations for schools and amenities"""
    
    def test_school_distance_calculation(self):
        """Test school distance calculation"""
        school = School(
            name="Test School",
            school_type=SchoolTypeEnum.ELEMENTARY,
            address="Test Address",
            latitude=40.7128,
            longitude=-74.0060,
            rating=8.0
        )
        
        # Distance to same point should be 0
        assert school.distance_to(40.7128, -74.0060) == 0.0
        
        # Distance to nearby point should be reasonable
        distance = school.distance_to(40.7138, -74.0050)
        assert 0 < distance < 1.0  # Should be less than 1 mile
    
    def test_amenity_distance_calculation(self):
        """Test amenity distance calculation"""
        amenity = Amenity(
            name="Test Amenity",
            amenity_type=AmenityTypeEnum.GROCERY,
            latitude=40.7128,
            longitude=-74.0060,
            rating=4.0
        )
        
        # Distance to same point should be 0
        assert amenity.distance_to(40.7128, -74.0060) == 0.0
        
        # Distance to nearby point should be reasonable
        distance = amenity.distance_to(40.7138, -74.0050)
        assert 0 < distance < 1.0  # Should be less than 1 mile


class TestPropertySale:
    """Test cases for PropertySale model"""
    
    def test_calculate_price_per_sqft(self):
        """Test price per square foot calculation"""
        sale = PropertySale(
            address="123 Test St",
            latitude=40.7128,
            longitude=-74.0060,
            sale_price=300000,
            sale_date=datetime.now(),
            square_feet=1500
        )
        
        sale.calculate_price_per_sqft()
        
        assert sale.price_per_sqft == 200.0  # 300000 / 1500
    
    def test_calculate_price_per_sqft_no_sqft(self):
        """Test price per square foot calculation with no square footage"""
        sale = PropertySale(
            address="123 Test St",
            latitude=40.7128,
            longitude=-74.0060,
            sale_price=300000,
            sale_date=datetime.now(),
            square_feet=None
        )
        
        sale.calculate_price_per_sqft()
        
        assert sale.price_per_sqft is None