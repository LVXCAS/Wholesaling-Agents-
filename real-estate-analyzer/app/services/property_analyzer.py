from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
import random  # For mock data, remove in production

from app.models.property import PropertyDB
from app.models.valuation import AnalysisResultDB, ComparableSaleDB
from app.services.comparable_finder import ComparableFinder
from app.services.arv_calculator import ARVCalculator

class PropertyAnalyzer:
    def __init__(self, db: Session):
        self.db = db
        self.comparable_finder = ComparableFinder(db)
        self.arv_calculator = ARVCalculator()

    def analyze_property(self, property: PropertyDB) -> Dict:
        """
        Analyze a property and calculate its ARV (After Repair Value).
        Returns a dictionary with analysis results including ARV estimate,
        confidence score, and other metrics.
        """
        # Find comparable properties
        comparables = self._find_comparable_properties(property)
        
        # Calculate ARV and get analysis details
        analysis_result = self.arv_calculator.calculate_arv(property, comparables)
        
        # Add repair estimate and profit potential
        repair_estimate = self._estimate_repairs(property)
        profit_potential = self._calculate_profit_potential(
            analysis_result["arv_estimate"],
            property.current_value or 0,
            repair_estimate
        )
        
        analysis_result["repair_estimate"] = repair_estimate
        analysis_result["profit_potential"] = profit_potential
        
        return analysis_result

    def _find_comparable_properties(self, property: PropertyDB) -> List[ComparableSaleDB]:
        """Find comparable properties within defined criteria."""
        # This is a mock implementation
        comps_count = random.randint(3, 8)
        comps = []
        
        base_price = property.current_value or 250000
        for _ in range(comps_count):
            price_variation = random.uniform(-0.15, 0.15)
            sqft_variation = random.uniform(-0.1, 0.1)
            
            comp = ComparableSaleDB(
                address=f"{random.randint(100, 999)} {random.choice(['Oak', 'Maple', 'Pine', 'Cedar'])} {random.choice(['St', 'Ave', 'Ln', 'Rd'])}",
                city=property.city,
                state=property.state,
                zip_code=property.zip_code,
                bedrooms=property.bedrooms + random.choice([-1, 0, 1]),
                bathrooms=property.bathrooms + random.choice([-0.5, 0, 0.5]),
                square_feet=int(property.square_feet * (1 + sqft_variation)),
                lot_size=property.lot_size,
                year_built=property.year_built - random.randint(-5, 5) if property.year_built else None,
                sale_price=base_price * (1 + price_variation),
                sale_date=datetime.now() - timedelta(days=random.randint(1, 180)),
                property_type=property.property_type.value
            )
            comps.append(comp)
        
        return comps

    def _estimate_repairs(self, property: PropertyDB) -> float:
        """Estimate repair costs based on property condition (mock implementation)."""
        base_repair_cost = property.square_feet * random.uniform(5, 30)
        if property.year_built:
            age = datetime.now().year - property.year_built
            age_factor = age / 50  # Older homes need more repairs
            base_repair_cost *= (1 + age_factor)
        
        # Round to nearest $100
        return round(base_repair_cost / 100) * 100

    def _calculate_profit_potential(self, arv: float, current_value: float, repair_cost: float) -> float:
        """Calculate potential profit after repairs."""
        # Assume 10% transaction costs (closing costs, realtor fees, etc.)
        transaction_costs = arv * 0.1
        
        profit = arv - current_value - repair_cost - transaction_costs
        
        # Round to nearest $100
        return round(profit / 100) * 100
