from typing import Dict, List, Optional
from datetime import datetime
from app.models.property import PropertyDB
from app.models.renovation_model import RenovationModel

class RenovationCalculator:
    def __init__(self):
        self.model = RenovationModel()
        
    def _get_complexity_score(self, property: PropertyDB, renovation_level: str) -> int:
        """Calculate renovation complexity score based on property attributes."""
        score = 1
        if not property.year_built:
            return score
            
        age = datetime.now().year - property.year_built
        if age > 50:
            score += 2
        elif age > 30:
            score += 1
            
        if renovation_level == 'luxury':
            score += 1
            
        # Cap at maximum complexity
        return min(score, 5)
        
    def _get_material_grade(self, renovation_level: str) -> int:
        """Map renovation level to material grade."""
        return {
            'basic': 1,
            'medium': 2,
            'luxury': 3
        }.get(renovation_level, 1)
        
    def estimate_renovation_costs(self, property: PropertyDB, condition_score: float) -> Dict:
        """
        Estimate renovation costs using enhanced ML model predictions.
        Returns detailed breakdown of costs with confidence scores and ranges.
        """
        current_year = datetime.now().year
        renovation_level = self._determine_renovation_level(condition_score)
        state = property.state
        sqft = property.square_feet or 1500  # Default if missing
        age = datetime.now().year - (property.year_built or (current_year - 30))
        
        # Get regional cost factors
        regional_factor = self.model.get_regional_factor(state)
        labor_rates = self.model.get_labor_rates(state)
        region = self._get_region(state)
        complexity = self._get_complexity_score(property, renovation_level)
        material_grade = self._get_material_grade(renovation_level)
        
        # Initialize result structures
        result = {
            'costs': {},
            'confidence_scores': {},
            'prediction_ranges': {},
            'feature_impacts': {},
            'warnings': []
        }
        
        # Kitchen renovation with enhanced prediction
        kitchen_data = self.model.predict_renovation_cost(
            'kitchen',
            sqft * 0.1,  # Assume kitchen is 10% of total sqft
            current_year,
            renovation_level,
            region,
            age=age,
            complexity=complexity,
            material_grade=material_grade
        )
        result['costs']['kitchen'] = kitchen_data['predicted_cost'] * regional_factor
        result['confidence_scores']['kitchen'] = kitchen_data['confidence_score']
        result['prediction_ranges']['kitchen'] = kitchen_data['prediction_interval']
        result['feature_impacts']['kitchen'] = kitchen_data['feature_contributions']
        
        if kitchen_data['out_of_range_features']:
            result['warnings'].append(f"Kitchen estimation: Features {', '.join(kitchen_data['out_of_range_features'])} are outside typical ranges")
            
        # Bathroom renovation
        bath_sqft = 50 * (property.bathrooms or 2)  # Estimate 50 sqft per bathroom
        bathroom_data = self.model.predict_renovation_cost(
            'bathroom',
            bath_sqft,
            current_year,
            renovation_level,
            region,
            age=age,
            complexity=complexity,
            material_grade=material_grade
        )
        result['costs']['bathroom'] = bathroom_data['predicted_cost'] * regional_factor * (property.bathrooms or 2)
        result['confidence_scores']['bathroom'] = bathroom_data['confidence_score']
        result['prediction_ranges']['bathroom'] = bathroom_data['prediction_interval']
        result['feature_impacts']['bathroom'] = bathroom_data['feature_contributions']
        
        if bathroom_data['out_of_range_features']:
            result['warnings'].append(f"Bathroom estimation: Features {', '.join(bathroom_data['out_of_range_features'])} are outside typical ranges")
            
        # Flooring
        floor_cost_data = self.model.predict_general_cost(
            current_year,
            'lumber',  # Using lumber as proxy for flooring
            sqft * self.model.cost_data['flooring']['cost_per_sqft'][renovation_level]['hardwood'],
            region=region,
            complexity=complexity
        )
        result['costs']['flooring'] = floor_cost_data['predicted_cost'] * regional_factor
        result['confidence_scores']['flooring'] = floor_cost_data['confidence_score']
        result['prediction_ranges']['flooring'] = floor_cost_data['prediction_interval']
        result['feature_impacts']['flooring'] = floor_cost_data['feature_contributions']
        
        # HVAC
        hvac_cost_data = self.model.predict_general_cost(
            current_year,
            'electrical',  # Using electrical as proxy for HVAC
            sqft * 1.5 + 5000,
            region=region,
            complexity=complexity
        )
        result['costs']['hvac'] = hvac_cost_data['predicted_cost'] * regional_factor
        result['confidence_scores']['hvac'] = hvac_cost_data['confidence_score']
        result['prediction_ranges']['hvac'] = hvac_cost_data['prediction_interval']
        result['feature_impacts']['hvac'] = hvac_cost_data['feature_contributions']
        
        # Electrical
        electrical_cost_data = self.model.predict_general_cost(
            current_year,
            'electrical',
            sqft * 2 + 3000,
            region=region,
            complexity=complexity
        )
        result['costs']['electrical'] = electrical_cost_data['predicted_cost'] * regional_factor
        result['confidence_scores']['electrical'] = electrical_cost_data['confidence_score']
        result['prediction_ranges']['electrical'] = electrical_cost_data['prediction_interval']
        result['feature_impacts']['electrical'] = electrical_cost_data['feature_contributions']
        
        # Plumbing
        plumbing_cost_data = self.model.predict_general_cost(
            current_year,
            'plumbing',
            sqft * 1.5 + 4000,
            region=region,
            complexity=complexity
        )
        result['costs']['plumbing'] = plumbing_cost_data['predicted_cost'] * regional_factor
        result['confidence_scores']['plumbing'] = plumbing_cost_data['confidence_score']
        result['prediction_ranges']['plumbing'] = plumbing_cost_data['prediction_interval']
        result['feature_impacts']['plumbing'] = plumbing_cost_data['feature_contributions']
        
        # Structural (if needed)
        if condition_score < 0.3:
            structural_cost_data = self.model.predict_general_cost(
                current_year,
                'concrete',  # Using concrete as proxy for structural work
                sqft * 10,
                region=region,
                complexity=complexity + 1  # Increase complexity for structural work
            )
            result['costs']['structural'] = structural_cost_data['predicted_cost'] * regional_factor
            result['confidence_scores']['structural'] = structural_cost_data['confidence_score']
            result['prediction_ranges']['structural'] = structural_cost_data['prediction_interval']
            result['feature_impacts']['structural'] = structural_cost_data['feature_contributions']
            
        # Calculate labor costs
        labor_hours = self._estimate_labor_hours(result['costs'], renovation_level)
        labor_cost = (
            labor_hours['general_contractor'] * labor_rates['general_contractor'] +
            labor_hours['skilled'] * labor_rates['skilled_labor'] +
            labor_hours['unskilled'] * labor_rates['unskilled_labor']
        )
        result['costs']['labor'] = labor_cost
        result['confidence_scores']['labor'] = 0.85  # Labor rates are relatively stable
        
        # Calculate total cost and overall confidence
        total_cost = sum(result['costs'].values())
        
        # Weight confidences by cost proportion
        weighted_confidence = sum(
            conf * (result['costs'][comp] / total_cost)
            for comp, conf in result['confidence_scores'].items()
        )
        
        # Add contingency based on confidence
        contingency = total_cost * (1 - weighted_confidence)
        total_with_contingency = total_cost + contingency
        
        # Prepare final result
        result.update({
            'total_cost': round(total_with_contingency),
            'base_cost': round(total_cost),
            'contingency': round(contingency),
            'overall_confidence': weighted_confidence,
            'renovation_level': renovation_level,
            'regional_factor': regional_factor,
            'labor_rates': labor_rates,
            'complexity_score': complexity,
            'material_grade': material_grade
        })
        
        # Validate results with model metrics
        for component in ['kitchen', 'bathroom']:
            metrics = self.model.validate_model(component)
            if metrics['r2_score'] < 0.7:  # Arbitrary threshold
                result['warnings'].append(f"Low model accuracy for {component} predictions (R² = {metrics['r2_score']:.2f})")
            
        return result
        confidences['kitchen'] = kitchen_conf
        
        # Bathroom renovation
        bath_sqft = 50 * (property.bathrooms or 2)  # Estimate 50 sqft per bathroom
        bathroom_cost, bathroom_conf = self.model.predict_renovation_cost(
            'bathroom',
            bath_sqft,
            current_year,
            renovation_level,
            self._get_region(state)
        )
        costs['bathroom'] = bathroom_cost * regional_factor * (property.bathrooms or 2)
        confidences['bathroom'] = bathroom_conf
        
        # Flooring
        flooring_cost, flooring_conf = self.model.predict_general_cost(
            current_year,
            'lumber',  # Use lumber as proxy for flooring
            sqft * self.model.cost_data['flooring']['cost_per_sqft'][renovation_level]['hardwood']
        )
        costs['flooring'] = flooring_cost * regional_factor
        confidences['flooring'] = flooring_conf
        
        # HVAC
        hvac_base = sqft * 1.5 + 5000
        hvac_cost, hvac_conf = self.model.predict_general_cost(
            current_year,
            'electrical',  # Use electrical as proxy for HVAC
            hvac_base
        )
        costs['hvac'] = hvac_cost * regional_factor
        confidences['hvac'] = hvac_conf
        
        # Electrical
        electrical_base = sqft * 2 + 3000
        electrical_cost, electrical_conf = self.model.predict_general_cost(
            current_year,
            'electrical',
            electrical_base
        )
        costs['electrical'] = electrical_cost * regional_factor
        confidences['electrical'] = electrical_conf
        
        # Plumbing
        plumbing_base = sqft * 1.5 + 4000
        plumbing_cost, plumbing_conf = self.model.predict_general_cost(
            current_year,
            'plumbing',
            plumbing_base
        )
        costs['plumbing'] = plumbing_cost * regional_factor
        confidences['plumbing'] = plumbing_conf
        
        # Structural (if needed)
        if condition_score < 0.3:
            structural_base = sqft * 10
            structural_cost, structural_conf = self.model.predict_general_cost(
                current_year,
                'concrete',  # Use concrete as proxy for structural work
                structural_base
            )
            costs['structural'] = structural_cost * regional_factor
            confidences['structural'] = structural_conf
            
        # Calculate labor costs
        labor_hours = self._estimate_labor_hours(costs, renovation_level)
        labor_cost = (
            labor_hours['general_contractor'] * labor_rates['general_contractor'] +
            labor_hours['skilled'] * labor_rates['skilled_labor'] +
            labor_hours['unskilled'] * labor_rates['unskilled_labor']
        )
        costs['labor'] = labor_cost
        confidences['labor'] = 0.85  # Labor rates are fairly stable
        
        # Calculate total cost and overall confidence
        total_cost = sum(costs.values())
        
        # Weight confidences by cost proportion
        weighted_confidence = sum(
            conf * (costs[comp] / total_cost)
            for comp, conf in confidences.items()
        )
        
        # Add contingency based on confidence
        contingency = total_cost * (1 - weighted_confidence)
        total_with_contingency = total_cost + contingency
        
        return {
            'total_cost': round(total_with_contingency),
            'base_cost': round(total_cost),
            'contingency': round(contingency),
            'cost_breakdown': {k: round(v) for k, v in costs.items()},
            'confidence_breakdown': confidences,
            'confidence_score': weighted_confidence,
            'renovation_level': renovation_level,
            'regional_factor': regional_factor,
            'labor_rates': labor_rates
        }
    
    def _determine_renovation_level(self, condition_score: float) -> str:
        """Determine renovation quality level needed based on condition."""
        if condition_score < 0.2:
            return 'luxury'  # Complete renovation needed
        elif condition_score < 0.4:
            return 'medium'
        else:
            return 'basic'
            
    def _get_region(self, state: str) -> str:
        """Map state to region."""
        regions = {
            'NY': 'northeast',
            'NJ': 'northeast',
            'CT': 'northeast',
            'MA': 'northeast',
            'CA': 'west',
            'OR': 'west',
            'WA': 'west',
            'IL': 'midwest',
            'OH': 'midwest',
            'MI': 'midwest',
            'FL': 'south',
            'TX': 'south',
            'GA': 'south'
        }
        return regions.get(state, 'midwest')
        
    def _estimate_labor_hours(self, costs: Dict[str, float], renovation_level: str) -> Dict[str, float]:
        """Estimate required labor hours based on costs and renovation level."""
        total_material_cost = sum(costs.values())
        
        # Labor hours as proportion of material costs
        labor_factors = {
            'luxury': {'gc': 0.15, 'skilled': 0.4, 'unskilled': 0.2},
            'medium': {'gc': 0.12, 'skilled': 0.35, 'unskilled': 0.25},
            'basic': {'gc': 0.1, 'skilled': 0.3, 'unskilled': 0.3}
        }
        
        factors = labor_factors[renovation_level]
        return {
            'general_contractor': total_material_cost * factors['gc'] / 100,  # Divide by hourly rate
            'skilled': total_material_cost * factors['skilled'] / 75,         # Approximate skilled labor rate
            'unskilled': total_material_cost * factors['unskilled'] / 25      # Approximate unskilled labor rate
        }
        
    def get_renovation_scope(self, property: PropertyDB, condition_score: float) -> List[str]:
        """Generate detailed list of recommended renovation tasks."""
        renovation_level = self._determine_renovation_level(condition_score)
        scope = []
        
        if condition_score < 0.2:
            scope.extend([
                "Complete gut renovation required",
                "Structural inspection and potential repairs needed",
                "Full electrical system replacement",
                "Complete plumbing system replacement",
                "New HVAC system installation",
                "Roof replacement likely needed",
                "Complete kitchen remodel with high-end appliances",
                f"Full renovation of {property.bathrooms} bathrooms",
                "Premium flooring throughout",
                "New windows and doors",
                "Exterior siding or stucco repair/replacement",
                "Foundation inspection and repairs"
            ])
        elif condition_score < 0.4:
            scope.extend([
                "Major kitchen renovation with new appliances",
                f"Renovation of {property.bathrooms} bathrooms",
                "Electrical system updates",
                "Plumbing system updates",
                "HVAC system repair or replacement",
                "New flooring in main living areas",
                "Interior wall repairs and fresh paint",
                "Window repairs or selective replacement",
                "Exterior repairs and paint"
            ])
        elif condition_score < 0.6:
            scope.extend([
                "Kitchen appliance updates",
                "Bathroom fixture updates",
                "Flooring repairs or replacement in worn areas",
                "HVAC servicing",
                "Minor electrical updates",
                "Minor plumbing repairs",
                "Interior painting",
                "General repairs and maintenance"
            ])
        else:
            scope.extend([
                "Minor kitchen updates",
                "Bathroom refresh",
                "Floor refinishing where needed",
                "Fresh paint in select areas",
                "General maintenance",
                "Landscaping improvements"
            ])
            
        if property.year_built and (datetime.now().year - property.year_built) > 30:
            scope.extend([
                "Age-related updates may be needed",
                "Code compliance verification",
                "Energy efficiency improvements recommended"
            ])
            
        return scope
