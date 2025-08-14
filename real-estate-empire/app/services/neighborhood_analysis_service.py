"""
Neighborhood Analysis Service

This service handles neighborhood boundary detection, trend analysis,
school and amenity scoring, and crime data integration.
"""

from typing import List, Dict, Optional, Any, Tuple
import uuid
import math
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import requests
import json
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

from app.models.neighborhood_analysis import (
    GeographicBoundary, PropertySale, MarketTrend, School, Amenity, CrimeIncident,
    NeighborhoodScore, NeighborhoodAnalysis, NeighborhoodComparison,
    NeighborhoodAlert, NeighborhoodSearchCriteria, NeighborhoodSearchResult,
    TrendDirectionEnum, AmenityTypeEnum, SchoolTypeEnum, CrimeTypeEnum
)
from app.core.database import get_db


class NeighborhoodAnalysisService:
    """Service for neighborhood analysis and scoring"""
    
    def __init__(self, db: Session = None):
        self.db = db
        self.geocoder = Nominatim(user_agent="real_estate_empire")
        
        # API keys would be loaded from environment variables
        self.google_maps_api_key = None  # os.getenv('GOOGLE_MAPS_API_KEY')
        self.crime_data_api_key = None   # os.getenv('CRIME_DATA_API_KEY')
    
    def detect_neighborhood_boundary(self, address: str, radius_miles: float = 1.0) -> GeographicBoundary:
        """Detect neighborhood boundary around a given address"""
        # Geocode the address to get coordinates
        location = self.geocoder.geocode(address)
        if not location:
            raise ValueError(f"Could not geocode address: {address}")
        
        center_lat = location.latitude
        center_lng = location.longitude
        
        # Create a circular boundary (simplified approach)
        # In a real implementation, this would use actual neighborhood boundaries
        boundary_points = self._create_circular_boundary(center_lat, center_lng, radius_miles)
        
        # Calculate bounding box
        lats = [point[0] for point in boundary_points]
        lngs = [point[1] for point in boundary_points]
        
        return GeographicBoundary(
            name=f"Neighborhood around {address}",
            boundary_type="circular",
            coordinates=boundary_points,
            north_lat=max(lats),
            south_lat=min(lats),
            east_lng=max(lngs),
            west_lng=min(lngs),
            center_lat=center_lat,
            center_lng=center_lng,
            area_sq_miles=math.pi * radius_miles ** 2
        )
    
    def _create_circular_boundary(self, center_lat: float, center_lng: float, radius_miles: float) -> List[List[float]]:
        """Create a circular boundary with given center and radius"""
        points = []
        num_points = 32  # Number of points to create the circle
        
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            
            # Calculate point on circle
            # Approximate conversion: 1 degree latitude ≈ 69 miles
            lat_offset = (radius_miles / 69.0) * math.cos(angle)
            lng_offset = (radius_miles / (69.0 * math.cos(math.radians(center_lat)))) * math.sin(angle)
            
            point_lat = center_lat + lat_offset
            point_lng = center_lng + lng_offset
            
            points.append([point_lat, point_lng])
        
        return points
    
    def analyze_market_trends(self, boundary: GeographicBoundary, months_back: int = 12) -> List[MarketTrend]:
        """Analyze market trends for a neighborhood"""
        # In a real implementation, this would query MLS data or property sales APIs
        # For now, we'll create mock trend data
        
        trends = []
        end_date = datetime.now()
        
        for i in range(months_back):
            period_end = end_date - timedelta(days=30 * i)
            period_start = period_end - timedelta(days=30)
            
            # Mock trend data - in reality this would come from actual sales data
            base_price = 300000 + (i * 5000)  # Simulate price appreciation
            sales_count = 15 + (i % 5)  # Simulate varying sales volume
            
            trend = MarketTrend(
                period_start=period_start,
                period_end=period_end,
                median_price=base_price,
                average_price=base_price * 1.1,
                price_change_percent=2.5 - (i * 0.2),  # Decreasing growth rate
                price_trend=TrendDirectionEnum.RISING if i < 6 else TrendDirectionEnum.STABLE,
                sales_count=sales_count,
                volume_change_percent=5.0 - (i * 0.5),
                volume_trend=TrendDirectionEnum.STABLE,
                days_on_market_avg=25 + (i * 2),
                inventory_months=3.5 + (i * 0.1),
                median_price_per_sqft=base_price / 1500,
                price_per_sqft_change=2.0 - (i * 0.1)
            )
            
            trends.append(trend)
        
        return trends
    
    def find_schools_in_area(self, boundary: GeographicBoundary, max_distance_miles: float = 2.0) -> List[School]:
        """Find schools within or near the neighborhood boundary"""
        # In a real implementation, this would query school district APIs or databases
        # For now, we'll create mock school data
        
        schools = []
        
        # Generate mock schools around the neighborhood center
        school_types = [SchoolTypeEnum.ELEMENTARY, SchoolTypeEnum.MIDDLE, SchoolTypeEnum.HIGH]
        
        for i, school_type in enumerate(school_types):
            # Place schools at different distances from center
            distance = 0.5 + (i * 0.3)  # 0.5, 0.8, 1.1 miles
            angle = i * 120  # Spread them around
            
            # Calculate school location
            lat_offset = (distance / 69.0) * math.cos(math.radians(angle))
            lng_offset = (distance / (69.0 * math.cos(math.radians(boundary.center_lat)))) * math.sin(math.radians(angle))
            
            school_lat = boundary.center_lat + lat_offset
            school_lng = boundary.center_lng + lng_offset
            
            school = School(
                name=f"{school_type.value.title()} School {i+1}",
                school_type=school_type,
                address=f"123 School St, City, State",
                latitude=school_lat,
                longitude=school_lng,
                rating=7.5 + (i * 0.5),  # Varying ratings
                enrollment=300 + (i * 200),
                student_teacher_ratio=15 + i,
                test_scores={
                    "math": 75 + (i * 5),
                    "reading": 80 + (i * 3),
                    "science": 70 + (i * 7)
                }
            )
            
            schools.append(school)
        
        return schools
    
    def find_amenities_in_area(self, boundary: GeographicBoundary, max_distance_miles: float = 1.0) -> List[Amenity]:
        """Find amenities within the neighborhood"""
        # In a real implementation, this would query Google Places API or similar
        # For now, we'll create mock amenity data
        
        amenities = []
        amenity_types = [
            AmenityTypeEnum.GROCERY, AmenityTypeEnum.RESTAURANT, AmenityTypeEnum.PARK,
            AmenityTypeEnum.SHOPPING, AmenityTypeEnum.TRANSIT, AmenityTypeEnum.GYM
        ]
        
        for i, amenity_type in enumerate(amenity_types):
            # Distribute amenities around the neighborhood
            for j in range(2):  # 2 of each type
                distance = 0.2 + (j * 0.3)
                angle = (i * 60) + (j * 30)
                
                lat_offset = (distance / 69.0) * math.cos(math.radians(angle))
                lng_offset = (distance / (69.0 * math.cos(math.radians(boundary.center_lat)))) * math.sin(math.radians(angle))
                
                amenity_lat = boundary.center_lat + lat_offset
                amenity_lng = boundary.center_lng + lng_offset
                
                amenity = Amenity(
                    name=f"{amenity_type.value.title()} {j+1}",
                    amenity_type=amenity_type,
                    address=f"{100 + (i*10) + j} Main St, City, State",
                    latitude=amenity_lat,
                    longitude=amenity_lng,
                    rating=3.5 + (j * 0.5),
                    review_count=50 + (i * 20) + (j * 10),
                    hours="9 AM - 9 PM",
                    phone=f"555-{100 + i}{10 + j}0-{1000 + (i*100) + (j*10)}"
                )
                
                amenities.append(amenity)
        
        return amenities
    
    def get_crime_data(self, boundary: GeographicBoundary, months_back: int = 12) -> List[CrimeIncident]:
        """Get crime data for the neighborhood"""
        # In a real implementation, this would query crime data APIs
        # For now, we'll create mock crime data
        
        incidents = []
        crime_types = [CrimeTypeEnum.PROPERTY, CrimeTypeEnum.VIOLENT, CrimeTypeEnum.DRUG, CrimeTypeEnum.TRAFFIC]
        
        # Generate incidents over the past months
        for month in range(months_back):
            incidents_per_month = 5 + (month % 3)  # Varying incident counts
            
            for i in range(incidents_per_month):
                # Random location within boundary
                incident_lat = boundary.center_lat + ((i % 3 - 1) * 0.01)
                incident_lng = boundary.center_lng + ((i % 5 - 2) * 0.01)
                
                incident_date = datetime.now() - timedelta(days=30 * month + i * 7)
                crime_type = crime_types[i % len(crime_types)]
                
                incident = CrimeIncident(
                    incident_date=incident_date,
                    latitude=incident_lat,
                    longitude=incident_lng,
                    address=f"{100 + i} Crime St, City, State",
                    crime_type=crime_type,
                    crime_description=f"{crime_type.value.title()} incident #{i+1}",
                    severity=1 + (i % 4),  # Severity 1-4
                    resolved=(i % 3 == 0)  # Some incidents resolved
                )
                
                incidents.append(incident)
        
        return incidents
    
    def calculate_school_score(self, schools: List[School]) -> float:
        """Calculate overall school score for the neighborhood"""
        if not schools:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for school in schools:
            if school.rating is not None:
                # Weight schools by type (high schools weighted more)
                weight = 1.0
                if school.school_type == SchoolTypeEnum.HIGH:
                    weight = 1.5
                elif school.school_type == SchoolTypeEnum.MIDDLE:
                    weight = 1.2
                
                # Convert 0-10 rating to 0-100 score
                school_score = (school.rating / 10.0) * 100
                total_score += school_score * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return total_score / total_weight
    
    def calculate_amenity_score(self, amenities: List[Amenity], center_lat: float, center_lng: float) -> float:
        """Calculate amenity access score"""
        if not amenities:
            return 0.0
        
        # Score based on variety and proximity of amenities
        amenity_types_present = set(amenity.amenity_type for amenity in amenities)
        variety_score = (len(amenity_types_present) / len(AmenityTypeEnum)) * 100
        
        # Calculate average distance to amenities
        total_distance = 0.0
        for amenity in amenities:
            distance = amenity.distance_to(center_lat, center_lng)
            total_distance += distance
        
        avg_distance = total_distance / len(amenities)
        
        # Closer amenities score higher (max distance of 2 miles for scoring)
        proximity_score = max(0, (2.0 - avg_distance) / 2.0) * 100
        
        # Combine variety and proximity (60% variety, 40% proximity)
        return (variety_score * 0.6) + (proximity_score * 0.4)
    
    def calculate_safety_score(self, crime_incidents: List[CrimeIncident], area_sq_miles: float) -> float:
        """Calculate safety score based on crime data"""
        if not crime_incidents:
            return 100.0  # Perfect score if no crime data
        
        # Calculate crime rate per square mile per year
        recent_incidents = [
            incident for incident in crime_incidents
            if incident.incident_date > datetime.now() - timedelta(days=365)
        ]
        
        crime_rate = len(recent_incidents) / area_sq_miles if area_sq_miles > 0 else len(recent_incidents)
        
        # Weight crimes by severity and type
        weighted_crime_score = 0.0
        for incident in recent_incidents:
            weight = 1.0
            
            # Violent crimes weighted more heavily
            if incident.crime_type == CrimeTypeEnum.VIOLENT:
                weight = 3.0
            elif incident.crime_type == CrimeTypeEnum.PROPERTY:
                weight = 2.0
            elif incident.crime_type == CrimeTypeEnum.DRUG:
                weight = 1.5
            
            # Severity multiplier
            severity_multiplier = incident.severity if incident.severity else 1
            weighted_crime_score += weight * severity_multiplier
        
        # Normalize to 0-100 scale (lower crime = higher score)
        # Assume 50 weighted incidents per sq mile per year is average (score = 50)
        normalized_score = max(0, 100 - (weighted_crime_score / area_sq_miles) * 2)
        
        return min(100.0, normalized_score)
    
    def calculate_market_trend_score(self, trends: List[MarketTrend]) -> float:
        """Calculate market trend score"""
        if not trends:
            return 50.0  # Neutral score
        
        # Use the most recent trend
        recent_trend = trends[0] if trends else None
        if not recent_trend:
            return 50.0
        
        score = 50.0  # Base score
        
        # Price trend factor
        if recent_trend.price_trend == TrendDirectionEnum.RISING:
            score += 25
        elif recent_trend.price_trend == TrendDirectionEnum.DECLINING:
            score -= 25
        
        # Price change percentage factor
        if recent_trend.price_change_percent > 5:
            score += 15
        elif recent_trend.price_change_percent > 2:
            score += 10
        elif recent_trend.price_change_percent < -2:
            score -= 15
        
        # Volume trend factor
        if recent_trend.volume_trend == TrendDirectionEnum.RISING:
            score += 10
        elif recent_trend.volume_trend == TrendDirectionEnum.DECLINING:
            score -= 10
        
        return min(100.0, max(0.0, score))
    
    def calculate_neighborhood_score(self, boundary: GeographicBoundary, trends: List[MarketTrend],
                                   schools: List[School], amenities: List[Amenity],
                                   crime_incidents: List[CrimeIncident]) -> NeighborhoodScore:
        """Calculate comprehensive neighborhood score"""
        
        # Calculate component scores
        market_trend_score = self.calculate_market_trend_score(trends)
        school_score = self.calculate_school_score(schools)
        amenity_score = self.calculate_amenity_score(amenities, boundary.center_lat, boundary.center_lng)
        safety_score = self.calculate_safety_score(crime_incidents, boundary.area_sq_miles or 1.0)
        
        # Calculate overall score (weighted average)
        weights = {
            'market': 0.3,
            'schools': 0.25,
            'amenities': 0.2,
            'safety': 0.25
        }
        
        overall_score = (
            market_trend_score * weights['market'] +
            school_score * weights['schools'] +
            amenity_score * weights['amenities'] +
            safety_score * weights['safety']
        )
        
        # Calculate investment-specific metrics
        appreciation_potential = market_trend_score  # Simplified
        rental_demand = (school_score + amenity_score) / 2  # Families prefer good schools and amenities
        liquidity_score = market_trend_score  # Active markets are more liquid
        
        # Calculate confidence based on data availability
        data_points = len(trends) + len(schools) + len(amenities) + len(crime_incidents)
        confidence_score = min(1.0, data_points / 50.0)  # Assume 50 data points for full confidence
        
        return NeighborhoodScore(
            neighborhood_id=boundary.id,
            overall_score=overall_score,
            market_trend_score=market_trend_score,
            school_score=school_score,
            amenity_score=amenity_score,
            safety_score=safety_score,
            appreciation_potential=appreciation_potential,
            rental_demand=rental_demand,
            liquidity_score=liquidity_score,
            confidence_score=confidence_score,
            sales_data_points=len(trends),
            schools_analyzed=len(schools),
            amenities_analyzed=len(amenities),
            crime_incidents_analyzed=len(crime_incidents)
        )
    
    def analyze_neighborhood(self, address: str, radius_miles: float = 1.0) -> NeighborhoodAnalysis:
        """Perform complete neighborhood analysis"""
        
        # Detect neighborhood boundary
        boundary = self.detect_neighborhood_boundary(address, radius_miles)
        
        # Gather data
        trends = self.analyze_market_trends(boundary)
        schools = self.find_schools_in_area(boundary)
        amenities = self.find_amenities_in_area(boundary)
        crime_incidents = self.get_crime_data(boundary)
        
        # Calculate scores
        neighborhood_score = self.calculate_neighborhood_score(
            boundary, trends, schools, amenities, crime_incidents
        )
        
        # Generate insights
        investment_highlights = self._generate_investment_highlights(
            neighborhood_score, trends, schools, amenities
        )
        risk_factors = self._generate_risk_factors(
            neighborhood_score, trends, crime_incidents
        )
        
        # Create crime statistics
        crime_stats = {}
        for crime_type in CrimeTypeEnum:
            crime_stats[crime_type] = len([
                incident for incident in crime_incidents
                if incident.crime_type == crime_type
            ])
        
        return NeighborhoodAnalysis(
            boundary=boundary,
            current_market_trend=trends[0] if trends else None,
            historical_trends=trends,
            schools=schools,
            amenities=amenities,
            crime_incidents=crime_incidents,
            crime_stats=crime_stats,
            neighborhood_score=neighborhood_score,
            analysis_radius_miles=radius_miles,
            investment_highlights=investment_highlights,
            risk_factors=risk_factors
        )
    
    def _generate_investment_highlights(self, score: NeighborhoodScore, trends: List[MarketTrend],
                                      schools: List[School], amenities: List[Amenity]) -> List[str]:
        """Generate investment highlights based on analysis"""
        highlights = []
        
        if score.overall_score >= 80:
            highlights.append("Excellent overall neighborhood score")
        elif score.overall_score >= 70:
            highlights.append("Strong neighborhood fundamentals")
        
        if score.school_score >= 80:
            highlights.append("High-quality schools in the area")
        
        if score.safety_score >= 80:
            highlights.append("Low crime rates and safe environment")
        
        if score.market_trend_score >= 70:
            highlights.append("Positive market trends and price appreciation")
        
        if score.amenity_score >= 70:
            highlights.append("Good access to amenities and services")
        
        if trends and trends[0].price_change_percent > 5:
            highlights.append(f"Strong price appreciation of {trends[0].price_change_percent:.1f}%")
        
        return highlights
    
    def _generate_risk_factors(self, score: NeighborhoodScore, trends: List[MarketTrend],
                             crime_incidents: List[CrimeIncident]) -> List[str]:
        """Generate risk factors based on analysis"""
        risk_factors = []
        
        if score.safety_score < 50:
            risk_factors.append("Higher than average crime rates")
        
        if score.school_score < 50:
            risk_factors.append("Below average school quality")
        
        if trends and trends[0].price_trend == TrendDirectionEnum.DECLINING:
            risk_factors.append("Declining market trends")
        
        if score.market_trend_score < 40:
            risk_factors.append("Weak market fundamentals")
        
        # Check for recent violent crimes
        recent_violent_crimes = [
            incident for incident in crime_incidents
            if incident.crime_type == CrimeTypeEnum.VIOLENT and
            incident.incident_date > datetime.now() - timedelta(days=90)
        ]
        
        if len(recent_violent_crimes) > 2:
            risk_factors.append("Recent increase in violent crime")
        
        return risk_factors
    
    def search_neighborhoods(self, criteria: NeighborhoodSearchCriteria) -> NeighborhoodSearchResult:
        """Search for neighborhoods matching criteria"""
        start_time = datetime.now()
        
        # In a real implementation, this would query a database of analyzed neighborhoods
        # For now, we'll return a mock result
        
        matching_neighborhoods = []
        
        # Mock search - in reality this would query actual neighborhood data
        if criteria.center_lat and criteria.center_lng:
            # Analyze a few neighborhoods around the search center
            for i in range(3):
                offset_lat = criteria.center_lat + (i - 1) * 0.01
                offset_lng = criteria.center_lng + (i - 1) * 0.01
                
                mock_address = f"Mock Address {i+1}, City, State"
                try:
                    analysis = self.analyze_neighborhood(mock_address)
                    
                    # Check if it meets criteria
                    if self._meets_criteria(analysis, criteria):
                        matching_neighborhoods.append(analysis)
                except:
                    continue  # Skip if analysis fails
        
        end_time = datetime.now()
        search_time = (end_time - start_time).total_seconds()
        
        return NeighborhoodSearchResult(
            neighborhoods=matching_neighborhoods,
            total_found=len(matching_neighborhoods),
            search_criteria=criteria,
            search_time_seconds=search_time
        )
    
    def _meets_criteria(self, analysis: NeighborhoodAnalysis, criteria: NeighborhoodSearchCriteria) -> bool:
        """Check if a neighborhood analysis meets the search criteria"""
        score = analysis.neighborhood_score
        
        # Check score thresholds
        if criteria.min_overall_score and score.overall_score < criteria.min_overall_score:
            return False
        
        if criteria.min_school_score and score.school_score < criteria.min_school_score:
            return False
        
        if criteria.min_safety_score and score.safety_score < criteria.min_safety_score:
            return False
        
        if criteria.min_appreciation_potential and score.appreciation_potential < criteria.min_appreciation_potential:
            return False
        
        # Check market criteria
        if criteria.max_median_price and analysis.current_market_trend:
            if analysis.current_market_trend.median_price > criteria.max_median_price:
                return False
        
        # Check amenity requirements
        if criteria.required_amenities:
            available_amenity_types = set(amenity.amenity_type for amenity in analysis.amenities)
            required_types = set(criteria.required_amenities)
            
            if not required_types.issubset(available_amenity_types):
                return False
        
        # Check school requirements
        if criteria.min_school_rating:
            max_school_rating = max(
                (school.rating for school in analysis.schools if school.rating),
                default=0
            )
            if max_school_rating < criteria.min_school_rating:
                return False
        
        return True
    
    def compare_neighborhoods(self, neighborhood_analyses: List[NeighborhoodAnalysis]) -> NeighborhoodComparison:
        """Compare multiple neighborhoods"""
        if len(neighborhood_analyses) < 2:
            raise ValueError("Need at least 2 neighborhoods to compare")
        
        # Create rankings by different criteria
        rankings = {}
        
        # Overall score ranking
        overall_ranking = sorted(
            neighborhood_analyses,
            key=lambda n: n.neighborhood_score.overall_score,
            reverse=True
        )
        rankings['overall'] = [n.id for n in overall_ranking]
        
        # School score ranking
        school_ranking = sorted(
            neighborhood_analyses,
            key=lambda n: n.neighborhood_score.school_score,
            reverse=True
        )
        rankings['schools'] = [n.id for n in school_ranking]
        
        # Safety score ranking
        safety_ranking = sorted(
            neighborhood_analyses,
            key=lambda n: n.neighborhood_score.safety_score,
            reverse=True
        )
        rankings['safety'] = [n.id for n in safety_ranking]
        
        # Appreciation potential ranking
        appreciation_ranking = sorted(
            neighborhood_analyses,
            key=lambda n: n.neighborhood_score.appreciation_potential,
            reverse=True
        )
        rankings['appreciation'] = [n.id for n in appreciation_ranking]
        
        # Determine best for different purposes
        best_for_appreciation = appreciation_ranking[0].id if appreciation_ranking else None
        best_for_rental = sorted(
            neighborhood_analyses,
            key=lambda n: n.neighborhood_score.rental_demand,
            reverse=True
        )[0].id
        
        best_for_families = sorted(
            neighborhood_analyses,
            key=lambda n: (n.neighborhood_score.school_score + n.neighborhood_score.safety_score) / 2,
            reverse=True
        )[0].id
        
        # Best value (high score, low price)
        best_value = None
        if all(n.current_market_trend for n in neighborhood_analyses):
            value_ranking = sorted(
                neighborhood_analyses,
                key=lambda n: n.neighborhood_score.overall_score / (n.current_market_trend.median_price / 100000),
                reverse=True
            )
            best_value = value_ranking[0].id if value_ranking else None
        
        # Generate comparison summary
        summary = self._generate_comparison_summary(neighborhood_analyses, rankings)
        
        return NeighborhoodComparison(
            neighborhoods=neighborhood_analyses,
            rankings=rankings,
            best_for_appreciation=best_for_appreciation,
            best_for_rental=best_for_rental,
            best_for_families=best_for_families,
            best_value=best_value,
            comparison_summary=summary
        )
    
    def _generate_comparison_summary(self, neighborhoods: List[NeighborhoodAnalysis], 
                                   rankings: Dict[str, List[uuid.UUID]]) -> str:
        """Generate a summary of the neighborhood comparison"""
        if not neighborhoods:
            return "No neighborhoods to compare."
        
        best_overall = next(n for n in neighborhoods if n.id == rankings['overall'][0])
        best_schools = next(n for n in neighborhoods if n.id == rankings['schools'][0])
        safest = next(n for n in neighborhoods if n.id == rankings['safety'][0])
        
        summary = f"Comparison of {len(neighborhoods)} neighborhoods:\n\n"
        summary += f"Best Overall: {best_overall.boundary.name} (Score: {best_overall.neighborhood_score.overall_score:.1f})\n"
        summary += f"Best Schools: {best_schools.boundary.name} (School Score: {best_schools.neighborhood_score.school_score:.1f})\n"
        summary += f"Safest: {safest.boundary.name} (Safety Score: {safest.neighborhood_score.safety_score:.1f})\n"
        
        return summary