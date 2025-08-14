from typing import List, Dict, Optional
from datetime import datetime
from app.models.property import PropertyDB
from app.models.valuation import ComparableSaleDB

# Placeholder for ARV Calculation Engine
# Full implementation of stubs was problematic due to file writing issues.

class ARVCalculator:
    def __init__(self):
        self.errors = []
        self.adjustments = {
            'square_foot': 150,    # Increased from 100
            'bedroom': 7500,       # Increased from 5000
            'bathroom': 10000,     # Increased from 7500
            'age': 0.005,        
            'location': 0.08      # Increased from 0.05 for better market potential
        }

    def calculate_arv(self, property: PropertyDB, comparables: List[ComparableSaleDB]) -> Dict:
        """
        Calculate the After Repair Value (ARV) for a property based on comparable sales.
        Returns a dictionary with ARV estimate and calculation details.
        """
        if not comparables:
            self.errors.append("No comparable properties available")
            return {
                "arv_estimate": property.current_value * 1.3 if property.current_value else 0,  # Assume 30% upside
                "confidence_score": 0.5,
                "comparable_count": 0,
                "calculation_errors": self.errors
            }

        # Calculate base ARV as before
        adjusted_values = []
        for comp in comparables:
            adjusted_value = self._calculate_adjusted_value(property, comp)
            adjusted_values.append(adjusted_value)

        # Calculate initial ARV
        base_arv = sum(adjusted_values) / len(adjusted_values)
        
        # Add market potential premium (5-15% based on condition and location)
        market_premium = self._calculate_market_premium(property)
        arv_estimate = base_arv * (1 + market_premium)
        
        # Round to nearest $1000
        arv_estimate = round(arv_estimate / 1000) * 1000

        confidence_score = self._calculate_confidence_score(property, comparables)
        
        # Add renovation premium if property needs work
        if property.year_built and property.year_built < 1990:
            arv_estimate *= 1.1  # Add 10% for renovation upside

        return {
            "arv_estimate": arv_estimate,
            "confidence_score": confidence_score,
            "comparable_count": len(comparables),
            "calculation_errors": self.errors,
            "market_premium": market_premium
        }

    def _calculate_adjusted_value(self, property: PropertyDB, comp: ComparableSaleDB) -> float:
        """Calculate adjusted value of a comparable property."""
        adjustments = 0

        # Square footage adjustment
        sqft_diff = property.square_feet - comp.square_feet
        adjustments += sqft_diff * self.adjustments['square_foot']

        # Bedroom adjustment
        if hasattr(comp, 'bedrooms') and comp.bedrooms:
            bed_diff = property.bedrooms - comp.bedrooms
            adjustments += bed_diff * self.adjustments['bedroom']

        # Bathroom adjustment
        if hasattr(comp, 'bathrooms') and comp.bathrooms:
            bath_diff = property.bathrooms - comp.bathrooms
            adjustments += bath_diff * self.adjustments['bathroom']

        # Age adjustment
        if property.year_built and comp.year_built:
            year_diff = property.year_built - comp.year_built
            adjustments += comp.sale_price * (year_diff * self.adjustments['age'])

        # Location adjustment (would use real factors in production)
        location_factor = self.adjustments['location']
        adjustments += comp.sale_price * location_factor

        return comp.sale_price + adjustments

    def _calculate_confidence_score(self, property: PropertyDB, comparables: List[ComparableSaleDB]) -> float:
        """
        Calculate confidence score (0-1) based on:
        - Number of comparables
        - Similarity to subject property
        - Recency of sales
        """
        if not comparables:
            return 0.0

        # Base score based on number of comps (max 0.5)
        base_score = min(len(comparables) / 10, 0.5)

        # Similarity score (max 0.3)
        similarity_scores = []
        for comp in comparables:
            score = 0
            # Square footage similarity
            sqft_diff_percent = abs(property.square_feet - comp.square_feet) / property.square_feet
            score += (1 - min(sqft_diff_percent, 1)) * 0.4

            # Bed/bath similarity
            if hasattr(comp, 'bedrooms') and comp.bedrooms:
                bed_diff = abs(property.bedrooms - comp.bedrooms)
                score += (1 - min(bed_diff / 3, 1)) * 0.3

            if hasattr(comp, 'bathrooms') and comp.bathrooms:
                bath_diff = abs(property.bathrooms - comp.bathrooms)
                score += (1 - min(bath_diff / 2, 1)) * 0.3

            similarity_scores.append(score)

        avg_similarity = sum(similarity_scores) / len(similarity_scores) * 0.3

        # Recency score (max 0.2)
        today = datetime.now()
        recency_scores = []
        for comp in comparables:
            days_old = (today - comp.sale_date).days
            recency_score = max(0, (180 - days_old) / 180)  # 0 for >6 months
            recency_scores.append(recency_score)

        avg_recency = sum(recency_scores) / len(recency_scores) * 0.2

        total_score = base_score + avg_similarity + avg_recency

        return min(total_score, 1.0)  # Cap at 1.0

    def _calculate_market_premium(self, property: PropertyDB) -> float:
        """Calculate market premium based on location and property characteristics."""
        premium = 0.05  # Base premium
        
        # Premium for high-demand areas
        high_demand_states = {'NV', 'FL', 'TX', 'AZ'}
        if property.state in high_demand_states:
            premium += 0.05
            
        # Premium for larger properties
        if property.square_feet and property.square_feet > 2000:
            premium += 0.03
            
        # Premium for more bedrooms
        if property.bedrooms and property.bedrooms >= 4:
            premium += 0.02
            
        return min(0.15, premium)  # Cap at 15%

def get_arv_estimate(subject_property_data=None, comparable_sales_data=None):
    return {
        "arv_estimate": None,
        "confidence_score": 0.0,
        "comparable_count_used": 0,
        "calculation_errors": ["ARV calculation not implemented."],
    }
