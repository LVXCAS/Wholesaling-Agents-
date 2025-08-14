"""
Neighborhood Analysis Models for Real Estate Deal Sourcing

This module defines the data models for neighborhood analysis, trend analysis,
school and amenity scoring, and crime data integration.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
import uuid
from datetime import datetime
from geopy.distance import geodesic


class TrendDirectionEnum(str, Enum):
    """Trend direction for neighborhood analysis"""
    RISING = "rising"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"


class AmenityTypeEnum(str, Enum):
    """Types of neighborhood amenities"""
    SCHOOL = "school"
    HOSPITAL = "hospital"
    SHOPPING = "shopping"
    RESTAURANT = "restaurant"
    PARK = "park"
    TRANSIT = "transit"
    ENTERTAINMENT = "entertainment"
    GYM = "gym"
    LIBRARY = "library"
    GROCERY = "grocery"
    GAS_STATION = "gas_station"
    BANK = "bank"
    PHARMACY = "pharmacy"


class SchoolTypeEnum(str, Enum):
    """Types of schools"""
    ELEMENTARY = "elementary"
    MIDDLE = "middle"
    HIGH = "high"
    PRIVATE = "private"
    CHARTER = "charter"


class CrimeTypeEnum(str, Enum):
    """Types of crimes for analysis"""
    VIOLENT = "violent"
    PROPERTY = "property"
    DRUG = "drug"
    TRAFFIC = "traffic"
    OTHER = "other"


class GeographicBoundary(BaseModel):
    """Geographic boundary definition"""
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    name: str = Field(..., description="Name of the boundary area")
    boundary_type: str = Field(..., description="Type of boundary (zip, city, neighborhood, etc.)")
    
    # Polygon coordinates (list of [lat, lng] pairs)
    coordinates: List[List[float]] = Field(..., description="Boundary coordinates as polygon")
    
    # Bounding box for quick filtering
    north_lat: float = Field(..., description="Northern latitude boundary")
    south_lat: float = Field(..., description="Southern latitude boundary")
    east_lng: float = Field(..., description="Eastern longitude boundary")
    west_lng: float = Field(..., description="Western longitude boundary")
    
    # Center point
    center_lat: float = Field(..., description="Center latitude")
    center_lng: float = Field(..., description="Center longitude")
    
    # Metadata
    area_sq_miles: Optional[float] = Field(None, description="Area in square miles")
    population: Optional[int] = Field(None, description="Population count")
    created_at: datetime = Field(default_factory=datetime.now)
    
    def contains_point(self, lat: float, lng: float) -> bool:
        """Check if a point is within this boundary using ray casting algorithm"""
        x, y = lng, lat
        n = len(self.coordinates)
        inside = False
        
        p1x, p1y = self.coordinates[0]
        for i in range(1, n + 1):
            p2x, p2y = self.coordinates[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside


class PropertySale(BaseModel):
    """Individual property sale record"""
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    address: str = Field(..., description="Property address")
    latitude: float = Field(..., description="Property latitude")
    longitude: float = Field(..., description="Property longitude")
    
    sale_price: float = Field(..., ge=0, description="Sale price")
    sale_date: datetime = Field(..., description="Date of sale")
    
    # Property details
    bedrooms: Optional[int] = Field(None, ge=0, description="Number of bedrooms")
    bathrooms: Optional[float] = Field(None, ge=0, description="Number of bathrooms")
    square_feet: Optional[int] = Field(None, ge=0, description="Square footage")
    lot_size: Optional[float] = Field(None, ge=0, description="Lot size in acres")
    year_built: Optional[int] = Field(None, ge=1800, le=2030, description="Year built")
    
    property_type: Optional[str] = Field(None, description="Property type")
    
    # Calculated metrics
    price_per_sqft: Optional[float] = Field(None, ge=0, description="Price per square foot")
    
    def calculate_price_per_sqft(self):
        """Calculate price per square foot"""
        if self.square_feet and self.square_feet > 0:
            self.price_per_sqft = self.sale_price / self.square_feet


class MarketTrend(BaseModel):
    """Market trend analysis for a time period"""
    period_start: datetime = Field(..., description="Start of analysis period")
    period_end: datetime = Field(..., description="End of analysis period")
    
    # Price trends
    median_price: float = Field(..., ge=0, description="Median sale price")
    average_price: float = Field(..., ge=0, description="Average sale price")
    price_change_percent: float = Field(..., description="Price change percentage")
    price_trend: TrendDirectionEnum = Field(..., description="Price trend direction")
    
    # Volume trends
    sales_count: int = Field(..., ge=0, description="Number of sales")
    volume_change_percent: float = Field(..., description="Volume change percentage")
    volume_trend: TrendDirectionEnum = Field(..., description="Volume trend direction")
    
    # Market metrics
    days_on_market_avg: Optional[float] = Field(None, ge=0, description="Average days on market")
    inventory_months: Optional[float] = Field(None, ge=0, description="Months of inventory")
    
    # Price per square foot trends
    median_price_per_sqft: Optional[float] = Field(None, ge=0, description="Median price per sqft")
    price_per_sqft_change: Optional[float] = Field(None, description="Price per sqft change %")


class School(BaseModel):
    """School information"""
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    name: str = Field(..., description="School name")
    school_type: SchoolTypeEnum = Field(..., description="Type of school")
    
    # Location
    address: str = Field(..., description="School address")
    latitude: float = Field(..., description="School latitude")
    longitude: float = Field(..., description="School longitude")
    
    # Ratings and scores
    rating: Optional[float] = Field(None, ge=0, le=10, description="School rating (0-10)")
    test_scores: Optional[Dict[str, float]] = Field(None, description="Test scores by subject")
    
    # Demographics
    enrollment: Optional[int] = Field(None, ge=0, description="Student enrollment")
    student_teacher_ratio: Optional[float] = Field(None, ge=0, description="Student to teacher ratio")
    
    # Distance calculation helper
    def distance_to(self, lat: float, lng: float) -> float:
        """Calculate distance to a point in miles"""
        return geodesic((self.latitude, self.longitude), (lat, lng)).miles


class Amenity(BaseModel):
    """Neighborhood amenity"""
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    name: str = Field(..., description="Amenity name")
    amenity_type: AmenityTypeEnum = Field(..., description="Type of amenity")
    
    # Location
    address: Optional[str] = Field(None, description="Amenity address")
    latitude: float = Field(..., description="Amenity latitude")
    longitude: float = Field(..., description="Amenity longitude")
    
    # Quality metrics
    rating: Optional[float] = Field(None, ge=0, le=5, description="Rating (0-5 stars)")
    review_count: Optional[int] = Field(None, ge=0, description="Number of reviews")
    
    # Additional info
    hours: Optional[str] = Field(None, description="Operating hours")
    phone: Optional[str] = Field(None, description="Phone number")
    website: Optional[str] = Field(None, description="Website URL")
    
    def distance_to(self, lat: float, lng: float) -> float:
        """Calculate distance to a point in miles"""
        return geodesic((self.latitude, self.longitude), (lat, lng)).miles


class CrimeIncident(BaseModel):
    """Crime incident record"""
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    incident_date: datetime = Field(..., description="Date of incident")
    
    # Location
    latitude: float = Field(..., description="Incident latitude")
    longitude: float = Field(..., description="Incident longitude")
    address: Optional[str] = Field(None, description="Incident address")
    
    # Crime details
    crime_type: CrimeTypeEnum = Field(..., description="Type of crime")
    crime_description: str = Field(..., description="Crime description")
    severity: Optional[int] = Field(None, ge=1, le=5, description="Severity level (1-5)")
    
    # Status
    resolved: bool = Field(default=False, description="Whether incident was resolved")


class NeighborhoodScore(BaseModel):
    """Comprehensive neighborhood scoring"""
    neighborhood_id: uuid.UUID = Field(..., description="Neighborhood identifier")
    
    # Overall scores (0-100)
    overall_score: float = Field(..., ge=0, le=100, description="Overall neighborhood score")
    
    # Component scores
    market_trend_score: float = Field(..., ge=0, le=100, description="Market trend score")
    school_score: float = Field(..., ge=0, le=100, description="School quality score")
    amenity_score: float = Field(..., ge=0, le=100, description="Amenity access score")
    safety_score: float = Field(..., ge=0, le=100, description="Safety/crime score")
    walkability_score: Optional[float] = Field(None, ge=0, le=100, description="Walkability score")
    
    # Investment metrics
    appreciation_potential: float = Field(..., ge=0, le=100, description="Price appreciation potential")
    rental_demand: float = Field(..., ge=0, le=100, description="Rental demand score")
    liquidity_score: float = Field(..., ge=0, le=100, description="Market liquidity score")
    
    # Confidence and metadata
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in scoring")
    data_freshness: datetime = Field(default_factory=datetime.now, description="When data was last updated")
    
    # Supporting data counts
    sales_data_points: int = Field(default=0, ge=0, description="Number of sales used")
    schools_analyzed: int = Field(default=0, ge=0, description="Number of schools analyzed")
    amenities_analyzed: int = Field(default=0, ge=0, description="Number of amenities analyzed")
    crime_incidents_analyzed: int = Field(default=0, ge=0, description="Number of crime incidents analyzed")


class NeighborhoodAnalysis(BaseModel):
    """Complete neighborhood analysis result"""
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    boundary: GeographicBoundary = Field(..., description="Neighborhood boundary")
    
    # Market analysis
    current_market_trend: MarketTrend = Field(..., description="Current market trend")
    historical_trends: List[MarketTrend] = Field(default_factory=list, description="Historical trends")
    
    # Schools and amenities
    schools: List[School] = Field(default_factory=list, description="Schools in/near neighborhood")
    amenities: List[Amenity] = Field(default_factory=list, description="Amenities in neighborhood")
    
    # Crime data
    crime_incidents: List[CrimeIncident] = Field(default_factory=list, description="Recent crime incidents")
    crime_stats: Dict[CrimeTypeEnum, int] = Field(default_factory=dict, description="Crime statistics by type")
    
    # Scoring
    neighborhood_score: NeighborhoodScore = Field(..., description="Comprehensive neighborhood score")
    
    # Analysis metadata
    analysis_date: datetime = Field(default_factory=datetime.now)
    analysis_radius_miles: float = Field(default=1.0, ge=0, description="Analysis radius in miles")
    
    # Investment insights
    investment_highlights: List[str] = Field(default_factory=list, description="Key investment highlights")
    risk_factors: List[str] = Field(default_factory=list, description="Potential risk factors")
    comparable_neighborhoods: List[str] = Field(default_factory=list, description="Similar neighborhoods")


class NeighborhoodComparison(BaseModel):
    """Comparison between multiple neighborhoods"""
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    comparison_date: datetime = Field(default_factory=datetime.now)
    
    neighborhoods: List[NeighborhoodAnalysis] = Field(..., description="Neighborhoods being compared")
    
    # Ranking by different criteria
    rankings: Dict[str, List[uuid.UUID]] = Field(
        default_factory=dict,
        description="Rankings by criteria (overall, schools, safety, etc.)"
    )
    
    # Comparison insights
    best_for_appreciation: Optional[uuid.UUID] = Field(None, description="Best for price appreciation")
    best_for_rental: Optional[uuid.UUID] = Field(None, description="Best for rental income")
    best_for_families: Optional[uuid.UUID] = Field(None, description="Best for families")
    best_value: Optional[uuid.UUID] = Field(None, description="Best value proposition")
    
    comparison_summary: str = Field(default="", description="Summary of comparison results")


class NeighborhoodAlert(BaseModel):
    """Alert for neighborhood changes"""
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    neighborhood_id: uuid.UUID = Field(..., description="Neighborhood being monitored")
    
    alert_type: str = Field(..., description="Type of alert")
    alert_message: str = Field(..., description="Alert message")
    severity: str = Field(..., description="Alert severity (low/medium/high)")
    
    # Trigger data
    trigger_metric: str = Field(..., description="Metric that triggered alert")
    old_value: Optional[float] = Field(None, description="Previous value")
    new_value: Optional[float] = Field(None, description="New value")
    change_percent: Optional[float] = Field(None, description="Percentage change")
    
    created_at: datetime = Field(default_factory=datetime.now)
    acknowledged: bool = Field(default=False, description="Whether alert was acknowledged")


class NeighborhoodSearchCriteria(BaseModel):
    """Criteria for searching neighborhoods"""
    # Geographic constraints
    center_lat: Optional[float] = Field(None, description="Center latitude for search")
    center_lng: Optional[float] = Field(None, description="Center longitude for search")
    radius_miles: Optional[float] = Field(None, ge=0, description="Search radius in miles")
    
    # Score thresholds
    min_overall_score: Optional[float] = Field(None, ge=0, le=100, description="Minimum overall score")
    min_school_score: Optional[float] = Field(None, ge=0, le=100, description="Minimum school score")
    min_safety_score: Optional[float] = Field(None, ge=0, le=100, description="Minimum safety score")
    min_appreciation_potential: Optional[float] = Field(None, ge=0, le=100, description="Minimum appreciation potential")
    
    # Market criteria
    max_median_price: Optional[float] = Field(None, ge=0, description="Maximum median price")
    min_price_trend: Optional[TrendDirectionEnum] = Field(None, description="Minimum price trend")
    
    # Amenity requirements
    required_amenities: List[AmenityTypeEnum] = Field(default_factory=list, description="Required amenity types")
    max_distance_to_amenities: Optional[float] = Field(None, ge=0, description="Max distance to amenities (miles)")
    
    # School requirements
    min_school_rating: Optional[float] = Field(None, ge=0, le=10, description="Minimum school rating")
    required_school_types: List[SchoolTypeEnum] = Field(default_factory=list, description="Required school types")


class NeighborhoodSearchResult(BaseModel):
    """Result from neighborhood search"""
    neighborhoods: List[NeighborhoodAnalysis] = Field(default_factory=list, description="Matching neighborhoods")
    total_found: int = Field(..., ge=0, description="Total neighborhoods found")
    search_criteria: NeighborhoodSearchCriteria = Field(..., description="Search criteria used")
    search_date: datetime = Field(default_factory=datetime.now)
    
    # Search performance
    search_time_seconds: float = Field(..., ge=0, description="Search execution time")
    
    class Config:
        use_enum_values = True