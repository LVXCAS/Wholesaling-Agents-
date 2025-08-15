"""
Portfolio Optimization Service for the Real Estate Empire platform.

This service handles underperforming asset detection, optimization recommendation algorithms,
diversification analysis, and market timing recommendations.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import logging
from statistics import mean, median, stdev
from dataclasses import dataclass
from enum import Enum

from app.models.portfolio import (
    PortfolioDB, PortfolioPropertyDB, PropertyPerformanceDB,
    PortfolioResponse, PortfolioPropertyResponse
)
from app.models.property import PropertyDB
from app.services.portfolio_performance_service import PortfolioPerformanceService
from app.services.market_data_service import MarketDataService
from app.core.database import get_db

logger = logging.getLogger(__name__)


class OptimizationActionEnum(str, Enum):
    """Enum for optimization action types."""
    HOLD = "hold"
    SELL = "sell"
    REFINANCE = "refinance"
    IMPROVE = "improve"
    REPOSITION = "reposition"
    ACQUIRE_SIMILAR = "acquire_similar"
    DIVERSIFY = "diversify"


class OptimizationPriorityEnum(str, Enum):
    """Enum for optimization priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class UnderperformingAsset:
    """Data class for underperforming asset information."""
    portfolio_property_id: uuid.UUID
    property_id: uuid.UUID
    property_address: str
    underperformance_score: float
    issues: List[str]
    potential_actions: List[str]
    estimated_impact: Dict[str, float]
    priority: OptimizationPriorityEnum


@dataclass
class OptimizationRecommendation:
    """Data class for optimization recommendations."""
    id: uuid.UUID
    portfolio_id: uuid.UUID
    recommendation_type: OptimizationActionEnum
    title: str
    description: str
    rationale: str
    priority: OptimizationPriorityEnum
    estimated_impact: Dict[str, float]
    implementation_steps: List[str]
    timeline_days: int
    cost_estimate: Optional[float]
    risk_level: str
    affected_properties: List[uuid.UUID]
    created_at: datetime


@dataclass
class DiversificationAnalysis:
    """Data class for diversification analysis results."""
    portfolio_id: uuid.UUID
    overall_score: float
    geographic_diversity: Dict[str, Any]
    property_type_diversity: Dict[str, Any]
    price_range_diversity: Dict[str, Any]
    income_source_diversity: Dict[str, Any]
    recommendations: List[str]
    target_allocations: Dict[str, float]


@dataclass
class MarketTimingRecommendation:
    """Data class for market timing recommendations."""
    portfolio_id: uuid.UUID
    market_phase: str  # "expansion", "peak", "contraction", "trough"
    recommended_actions: List[str]
    market_indicators: Dict[str, Any]
    timing_confidence: float
    optimal_timing_window: Dict[str, datetime]
    risk_factors: List[str]


class PortfolioOptimizationService:
    """Service for portfolio optimization and recommendations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.performance_service = PortfolioPerformanceService(db)
        self.market_service = MarketDataService(db)
    
    def detect_underperforming_assets(self, portfolio_id: uuid.UUID, 
                                    benchmark_percentile: float = 25.0) -> List[UnderperformingAsset]:
        """Detect underperforming assets in a portfolio."""
        try:
            # Get portfolio properties
            portfolio_properties = self.db.query(PortfolioPropertyDB).filter(
                PortfolioPropertyDB.portfolio_id == portfolio_id
            ).all()
            
            if not portfolio_properties:
                return []
            
            # Calculate performance metrics for each property
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            property_performances = []
            for prop in portfolio_properties:
                try:
                    perf = self.performance_service.calculate_property_performance(
                        prop.id, start_date, end_date
                    )
                    perf['portfolio_property'] = prop
                    property_performances.append(perf)
                except Exception as e:
                    logger.error(f"Error calculating performance for property {prop.id}: {str(e)}")
                    continue
            
            if not property_performances:
                return []
            
            # Calculate benchmarks
            cap_rates = [p['cap_rate'] for p in property_performances if p.get('cap_rate', 0) > 0]
            coc_returns = [p['coc_return'] for p in property_performances if p.get('coc_return', 0) > 0]
            rois = [p['roi'] for p in property_performances if p.get('roi')]
            cash_flows = [p['annual_cash_flow'] for p in property_performances]
            
            # Calculate percentile thresholds
            cap_rate_threshold = self._calculate_percentile(cap_rates, benchmark_percentile) if cap_rates else 0
            coc_threshold = self._calculate_percentile(coc_returns, benchmark_percentile) if coc_returns else 0
            roi_threshold = self._calculate_percentile(rois, benchmark_percentile) if rois else 0
            cash_flow_threshold = self._calculate_percentile(cash_flows, benchmark_percentile) if cash_flows else 0
            
            # Identify underperforming assets
            underperforming_assets = []
            
            for perf in property_performances:
                issues = []
                potential_actions = []
                underperformance_score = 0
                
                # Check cap rate performance
                if perf.get('cap_rate', 0) < cap_rate_threshold:
                    issues.append(f"Cap rate ({perf.get('cap_rate', 0):.2f}%) below portfolio average")
                    potential_actions.append("Increase rent or reduce expenses")
                    underperformance_score += 25
                
                # Check cash-on-cash return
                if perf.get('coc_return', 0) < coc_threshold:
                    issues.append(f"Cash-on-cash return ({perf.get('coc_return', 0):.2f}%) below portfolio average")
                    potential_actions.append("Consider refinancing or selling")
                    underperformance_score += 25
                
                # Check ROI
                if perf.get('roi', 0) < roi_threshold:
                    issues.append(f"ROI ({perf.get('roi', 0):.2f}%) below portfolio average")
                    potential_actions.append("Evaluate exit strategy")
                    underperformance_score += 25
                
                # Check cash flow
                if perf.get('annual_cash_flow', 0) < cash_flow_threshold:
                    issues.append(f"Cash flow (${perf.get('annual_cash_flow', 0):,.0f}) below portfolio average")
                    potential_actions.append("Optimize rental income or expenses")
                    underperformance_score += 25
                
                # Check for negative cash flow
                if perf.get('annual_cash_flow', 0) < 0:
                    issues.append("Negative cash flow")
                    potential_actions.append("Urgent: Address cash flow issues")
                    underperformance_score += 50
                
                # Check occupancy if available
                occupancy_rate = perf.get('occupancy_rate')
                if occupancy_rate and occupancy_rate < 90:
                    issues.append(f"Low occupancy rate ({occupancy_rate:.1f}%)")
                    potential_actions.append("Improve marketing or property condition")
                    underperformance_score += 15
                
                # Only include if there are issues
                if issues:
                    prop = perf['portfolio_property']
                    property_obj = self.db.query(PropertyDB).filter(PropertyDB.id == prop.property_id).first()
                    
                    # Determine priority
                    if underperformance_score >= 75:
                        priority = OptimizationPriorityEnum.CRITICAL
                    elif underperformance_score >= 50:
                        priority = OptimizationPriorityEnum.HIGH
                    elif underperformance_score >= 25:
                        priority = OptimizationPriorityEnum.MEDIUM
                    else:
                        priority = OptimizationPriorityEnum.LOW
                    
                    # Estimate impact of improvements
                    estimated_impact = self._estimate_improvement_impact(perf)
                    
                    underperforming_assets.append(UnderperformingAsset(
                        portfolio_property_id=prop.id,
                        property_id=prop.property_id,
                        property_address=property_obj.address if property_obj else "Unknown",
                        underperformance_score=underperformance_score,
                        issues=issues,
                        potential_actions=potential_actions,
                        estimated_impact=estimated_impact,
                        priority=priority
                    ))
            
            # Sort by underperformance score (highest first)
            underperforming_assets.sort(key=lambda x: x.underperformance_score, reverse=True)
            
            logger.info(f"Detected {len(underperforming_assets)} underperforming assets in portfolio {portfolio_id}")
            return underperforming_assets
            
        except Exception as e:
            logger.error(f"Error detecting underperforming assets: {str(e)}")
            raise
    
    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calculate the specified percentile of a list of values."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            weight = index - lower_index
            return sorted_values[lower_index] * (1 - weight) + sorted_values[upper_index] * weight
    
    def _estimate_improvement_impact(self, performance: Dict[str, Any]) -> Dict[str, float]:
        """Estimate the impact of potential improvements."""
        current_cash_flow = performance.get('annual_cash_flow', 0)
        current_value = performance.get('current_value', 0)
        
        # Conservative improvement estimates
        estimated_impact = {
            'rent_increase_5pct': current_cash_flow * 0.05,
            'expense_reduction_10pct': current_cash_flow * 0.10,
            'value_improvement_10pct': current_value * 0.10,
            'combined_optimization': current_cash_flow * 0.15
        }
        
        return estimated_impact
    
    def generate_optimization_recommendations(self, portfolio_id: uuid.UUID) -> List[OptimizationRecommendation]:
        """Generate comprehensive optimization recommendations for a portfolio."""
        try:
            recommendations = []
            
            # Get underperforming assets
            underperforming_assets = self.detect_underperforming_assets(portfolio_id)
            
            # Generate recommendations for underperforming assets
            for asset in underperforming_assets:
                asset_recommendations = self._generate_asset_recommendations(asset)
                recommendations.extend(asset_recommendations)
            
            # Generate portfolio-level recommendations
            portfolio_recommendations = self._generate_portfolio_level_recommendations(portfolio_id)
            recommendations.extend(portfolio_recommendations)
            
            # Generate diversification recommendations
            diversification_recommendations = self._generate_diversification_recommendations(portfolio_id)
            recommendations.extend(diversification_recommendations)
            
            # Generate market timing recommendations
            market_timing_recommendations = self._generate_market_timing_recommendations(portfolio_id)
            recommendations.extend(market_timing_recommendations)
            
            # Sort by priority and impact
            recommendations.sort(key=lambda x: (
                x.priority.value,
                -x.estimated_impact.get('annual_cash_flow_increase', 0)
            ))
            
            logger.info(f"Generated {len(recommendations)} optimization recommendations for portfolio {portfolio_id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {str(e)}")
            raise
    
    def _generate_asset_recommendations(self, asset: UnderperformingAsset) -> List[OptimizationRecommendation]:
        """Generate recommendations for a specific underperforming asset."""
        recommendations = []
        
        # Rent optimization recommendation
        if "below portfolio average" in " ".join(asset.issues):
            recommendations.append(OptimizationRecommendation(
                id=uuid.uuid4(),
                portfolio_id=asset.portfolio_property_id,  # This should be portfolio_id, will fix
                recommendation_type=OptimizationActionEnum.IMPROVE,
                title=f"Optimize Rental Income - {asset.property_address}",
                description="Increase rental income through market-rate adjustments and property improvements",
                rationale="Property is underperforming compared to portfolio average",
                priority=asset.priority,
                estimated_impact={
                    'annual_cash_flow_increase': asset.estimated_impact.get('rent_increase_5pct', 0),
                    'cap_rate_improvement': 0.5,
                    'property_value_increase': asset.estimated_impact.get('value_improvement_10pct', 0)
                },
                implementation_steps=[
                    "Conduct market rent analysis",
                    "Assess property condition and improvement needs",
                    "Implement necessary improvements",
                    "Adjust rent to market rate"
                ],
                timeline_days=90,
                cost_estimate=5000.0,
                risk_level="Low",
                affected_properties=[asset.property_id],
                created_at=datetime.now()
            ))
        
        # Expense reduction recommendation
        if "cash flow" in " ".join(asset.issues).lower():
            recommendations.append(OptimizationRecommendation(
                id=uuid.uuid4(),
                portfolio_id=asset.portfolio_property_id,  # This should be portfolio_id, will fix
                recommendation_type=OptimizationActionEnum.IMPROVE,
                title=f"Reduce Operating Expenses - {asset.property_address}",
                description="Optimize operating expenses through vendor negotiations and efficiency improvements",
                rationale="Property has suboptimal cash flow performance",
                priority=asset.priority,
                estimated_impact={
                    'annual_cash_flow_increase': asset.estimated_impact.get('expense_reduction_10pct', 0),
                    'expense_ratio_improvement': 2.0
                },
                implementation_steps=[
                    "Audit all operating expenses",
                    "Negotiate with service providers",
                    "Implement energy efficiency measures",
                    "Optimize property management processes"
                ],
                timeline_days=60,
                cost_estimate=2000.0,
                risk_level="Low",
                affected_properties=[asset.property_id],
                created_at=datetime.now()
            ))
        
        # Disposition recommendation for critical underperformers
        if asset.priority == OptimizationPriorityEnum.CRITICAL:
            recommendations.append(OptimizationRecommendation(
                id=uuid.uuid4(),
                portfolio_id=asset.portfolio_property_id,  # This should be portfolio_id, will fix
                recommendation_type=OptimizationActionEnum.SELL,
                title=f"Consider Disposition - {asset.property_address}",
                description="Evaluate selling this underperforming asset to redeploy capital",
                rationale="Property is significantly underperforming and may not be recoverable",
                priority=OptimizationPriorityEnum.HIGH,
                estimated_impact={
                    'capital_freed': asset.estimated_impact.get('value_improvement_10pct', 0),
                    'cash_flow_elimination': -abs(asset.estimated_impact.get('rent_increase_5pct', 0))
                },
                implementation_steps=[
                    "Obtain current market valuation",
                    "Calculate net proceeds after sale costs",
                    "Identify replacement investment opportunities",
                    "Execute disposition if favorable"
                ],
                timeline_days=120,
                cost_estimate=None,
                risk_level="Medium",
                affected_properties=[asset.property_id],
                created_at=datetime.now()
            ))
        
        return recommendations
    
    def _generate_portfolio_level_recommendations(self, portfolio_id: uuid.UUID) -> List[OptimizationRecommendation]:
        """Generate portfolio-level optimization recommendations."""
        recommendations = []
        
        try:
            # Get portfolio performance
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            portfolio_performance = self.performance_service.calculate_portfolio_performance(
                portfolio_id, start_date, end_date
            )
            
            # Refinancing recommendation if rates are favorable
            if portfolio_performance.get('average_coc_return', 0) < 8.0:
                recommendations.append(OptimizationRecommendation(
                    id=uuid.uuid4(),
                    portfolio_id=portfolio_id,
                    recommendation_type=OptimizationActionEnum.REFINANCE,
                    title="Portfolio Refinancing Analysis",
                    description="Evaluate refinancing opportunities to improve cash-on-cash returns",
                    rationale="Current cash-on-cash returns are below optimal levels",
                    priority=OptimizationPriorityEnum.MEDIUM,
                    estimated_impact={
                        'annual_cash_flow_increase': portfolio_performance.get('annual_cash_flow', 0) * 0.15,
                        'coc_return_improvement': 2.0
                    },
                    implementation_steps=[
                        "Analyze current loan terms across portfolio",
                        "Obtain refinancing quotes from multiple lenders",
                        "Calculate break-even analysis for each property",
                        "Execute refinancing for properties with positive ROI"
                    ],
                    timeline_days=90,
                    cost_estimate=15000.0,
                    risk_level="Low",
                    affected_properties=[],
                    created_at=datetime.now()
                ))
            
            # Portfolio expansion recommendation
            if portfolio_performance.get('total_properties', 0) < 10 and portfolio_performance.get('average_cap_rate', 0) > 6.0:
                recommendations.append(OptimizationRecommendation(
                    id=uuid.uuid4(),
                    portfolio_id=portfolio_id,
                    recommendation_type=OptimizationActionEnum.ACQUIRE_SIMILAR,
                    title="Portfolio Expansion Opportunity",
                    description="Consider acquiring additional properties to scale portfolio",
                    rationale="Current portfolio is performing well and has capacity for growth",
                    priority=OptimizationPriorityEnum.MEDIUM,
                    estimated_impact={
                        'portfolio_value_increase': portfolio_performance.get('total_value', 0) * 0.20,
                        'annual_cash_flow_increase': portfolio_performance.get('annual_cash_flow', 0) * 0.20
                    },
                    implementation_steps=[
                        "Define acquisition criteria based on current portfolio performance",
                        "Identify target markets and property types",
                        "Secure financing for acquisitions",
                        "Execute acquisition strategy"
                    ],
                    timeline_days=180,
                    cost_estimate=None,
                    risk_level="Medium",
                    affected_properties=[],
                    created_at=datetime.now()
                ))
            
        except Exception as e:
            logger.error(f"Error generating portfolio-level recommendations: {str(e)}")
        
        return recommendations
    
    def _generate_diversification_recommendations(self, portfolio_id: uuid.UUID) -> List[OptimizationRecommendation]:
        """Generate diversification-based recommendations."""
        recommendations = []
        
        try:
            diversification_analysis = self.analyze_diversification(portfolio_id)
            
            if diversification_analysis.overall_score < 60:
                recommendations.append(OptimizationRecommendation(
                    id=uuid.uuid4(),
                    portfolio_id=portfolio_id,
                    recommendation_type=OptimizationActionEnum.DIVERSIFY,
                    title="Improve Portfolio Diversification",
                    description="Enhance portfolio diversification to reduce risk and improve stability",
                    rationale=f"Current diversification score ({diversification_analysis.overall_score:.1f}) is below optimal",
                    priority=OptimizationPriorityEnum.MEDIUM,
                    estimated_impact={
                        'risk_reduction': 15.0,
                        'stability_improvement': 20.0
                    },
                    implementation_steps=diversification_analysis.recommendations,
                    timeline_days=120,
                    cost_estimate=None,
                    risk_level="Low",
                    affected_properties=[],
                    created_at=datetime.now()
                ))
        
        except Exception as e:
            logger.error(f"Error generating diversification recommendations: {str(e)}")
        
        return recommendations
    
    def _generate_market_timing_recommendations(self, portfolio_id: uuid.UUID) -> List[OptimizationRecommendation]:
        """Generate market timing-based recommendations."""
        recommendations = []
        
        try:
            market_timing = self.analyze_market_timing(portfolio_id)
            
            if market_timing.timing_confidence > 0.7:
                action_type = OptimizationActionEnum.HOLD
                if "sell" in market_timing.recommended_actions:
                    action_type = OptimizationActionEnum.SELL
                elif "acquire" in " ".join(market_timing.recommended_actions).lower():
                    action_type = OptimizationActionEnum.ACQUIRE_SIMILAR
                
                recommendations.append(OptimizationRecommendation(
                    id=uuid.uuid4(),
                    portfolio_id=portfolio_id,
                    recommendation_type=action_type,
                    title=f"Market Timing Strategy - {market_timing.market_phase.title()} Phase",
                    description=f"Optimize portfolio strategy based on current {market_timing.market_phase} market phase",
                    rationale=f"Market indicators suggest {market_timing.market_phase} phase with {market_timing.timing_confidence:.1%} confidence",
                    priority=OptimizationPriorityEnum.MEDIUM,
                    estimated_impact={
                        'market_timing_benefit': 10.0,
                        'risk_mitigation': 15.0
                    },
                    implementation_steps=market_timing.recommended_actions,
                    timeline_days=60,
                    cost_estimate=None,
                    risk_level="Medium",
                    affected_properties=[],
                    created_at=datetime.now()
                ))
        
        except Exception as e:
            logger.error(f"Error generating market timing recommendations: {str(e)}")
        
        return recommendations
    
    def analyze_diversification(self, portfolio_id: uuid.UUID) -> DiversificationAnalysis:
        """Analyze portfolio diversification across multiple dimensions."""
        try:
            # Get portfolio properties
            portfolio_properties = self.db.query(PortfolioPropertyDB).filter(
                PortfolioPropertyDB.portfolio_id == portfolio_id
            ).all()
            
            if not portfolio_properties:
                return DiversificationAnalysis(
                    portfolio_id=portfolio_id,
                    overall_score=0.0,
                    geographic_diversity={},
                    property_type_diversity={},
                    price_range_diversity={},
                    income_source_diversity={},
                    recommendations=[],
                    target_allocations={}
                )
            
            # Get property details
            property_ids = [prop.property_id for prop in portfolio_properties]
            properties = self.db.query(PropertyDB).filter(PropertyDB.id.in_(property_ids)).all()
            property_dict = {prop.id: prop for prop in properties}
            
            # Analyze geographic diversity
            geographic_diversity = self._analyze_geographic_diversity(portfolio_properties, property_dict)
            
            # Analyze property type diversity
            property_type_diversity = self._analyze_property_type_diversity(portfolio_properties, property_dict)
            
            # Analyze price range diversity
            price_range_diversity = self._analyze_price_range_diversity(portfolio_properties)
            
            # Analyze income source diversity
            income_source_diversity = self._analyze_income_source_diversity(portfolio_properties)
            
            # Calculate overall diversification score
            overall_score = (
                geographic_diversity.get('score', 0) * 0.3 +
                property_type_diversity.get('score', 0) * 0.25 +
                price_range_diversity.get('score', 0) * 0.25 +
                income_source_diversity.get('score', 0) * 0.2
            )
            
            # Generate recommendations
            recommendations = []
            if geographic_diversity.get('score', 0) < 60:
                recommendations.append("Consider acquiring properties in different geographic markets")
            if property_type_diversity.get('score', 0) < 60:
                recommendations.append("Diversify across different property types (residential, commercial, etc.)")
            if price_range_diversity.get('score', 0) < 60:
                recommendations.append("Balance portfolio across different price ranges")
            if income_source_diversity.get('score', 0) < 60:
                recommendations.append("Diversify income sources (rental, appreciation, development)")
            
            # Generate target allocations
            target_allocations = {
                'geographic_spread': 0.3,
                'property_type_mix': 0.25,
                'price_range_balance': 0.25,
                'income_source_variety': 0.2
            }
            
            return DiversificationAnalysis(
                portfolio_id=portfolio_id,
                overall_score=overall_score,
                geographic_diversity=geographic_diversity,
                property_type_diversity=property_type_diversity,
                price_range_diversity=price_range_diversity,
                income_source_diversity=income_source_diversity,
                recommendations=recommendations,
                target_allocations=target_allocations
            )
            
        except Exception as e:
            logger.error(f"Error analyzing diversification: {str(e)}")
            raise
    
    def _analyze_geographic_diversity(self, portfolio_properties: List[PortfolioPropertyDB], 
                                    property_dict: Dict[uuid.UUID, PropertyDB]) -> Dict[str, Any]:
        """Analyze geographic diversity of portfolio."""
        cities = {}
        states = {}
        total_value = sum(prop.current_value or prop.total_investment for prop in portfolio_properties)
        
        for prop in portfolio_properties:
            property_obj = property_dict.get(prop.property_id)
            if not property_obj:
                continue
            
            prop_value = prop.current_value or prop.total_investment
            
            # City analysis
            city = getattr(property_obj, 'city', 'Unknown')
            cities[city] = cities.get(city, 0) + prop_value
            
            # State analysis
            state = getattr(property_obj, 'state', 'Unknown')
            states[state] = states.get(state, 0) + prop_value
        
        # Calculate diversity scores
        city_concentration = max(cities.values()) / total_value if total_value > 0 else 1
        state_concentration = max(states.values()) / total_value if total_value > 0 else 1
        
        # Score based on concentration (lower concentration = higher score)
        city_score = (1 - city_concentration) * 100
        state_score = (1 - state_concentration) * 100
        overall_score = (city_score + state_score) / 2
        
        return {
            'score': overall_score,
            'city_distribution': cities,
            'state_distribution': states,
            'city_concentration': city_concentration,
            'state_concentration': state_concentration
        }
    
    def _analyze_property_type_diversity(self, portfolio_properties: List[PortfolioPropertyDB], 
                                       property_dict: Dict[uuid.UUID, PropertyDB]) -> Dict[str, Any]:
        """Analyze property type diversity."""
        property_types = {}
        total_value = sum(prop.current_value or prop.total_investment for prop in portfolio_properties)
        
        for prop in portfolio_properties:
            property_obj = property_dict.get(prop.property_id)
            if not property_obj:
                continue
            
            prop_value = prop.current_value or prop.total_investment
            prop_type = getattr(property_obj, 'property_type', 'Unknown')
            property_types[prop_type] = property_types.get(prop_type, 0) + prop_value
        
        # Calculate concentration
        max_concentration = max(property_types.values()) / total_value if total_value > 0 else 1
        score = (1 - max_concentration) * 100
        
        return {
            'score': score,
            'type_distribution': property_types,
            'concentration': max_concentration
        }
    
    def _analyze_price_range_diversity(self, portfolio_properties: List[PortfolioPropertyDB]) -> Dict[str, Any]:
        """Analyze price range diversity."""
        price_ranges = {
            'under_100k': 0,
            '100k_250k': 0,
            '250k_500k': 0,
            '500k_1m': 0,
            'over_1m': 0
        }
        
        total_value = 0
        
        for prop in portfolio_properties:
            prop_value = prop.current_value or prop.total_investment
            total_value += prop_value
            
            if prop_value < 100000:
                price_ranges['under_100k'] += prop_value
            elif prop_value < 250000:
                price_ranges['100k_250k'] += prop_value
            elif prop_value < 500000:
                price_ranges['250k_500k'] += prop_value
            elif prop_value < 1000000:
                price_ranges['500k_1m'] += prop_value
            else:
                price_ranges['over_1m'] += prop_value
        
        # Calculate concentration
        max_concentration = max(price_ranges.values()) / total_value if total_value > 0 else 1
        score = (1 - max_concentration) * 100
        
        return {
            'score': score,
            'range_distribution': price_ranges,
            'concentration': max_concentration
        }
    
    def _analyze_income_source_diversity(self, portfolio_properties: List[PortfolioPropertyDB]) -> Dict[str, Any]:
        """Analyze income source diversity."""
        # This is a simplified analysis - in practice, you'd have more detailed income source data
        income_sources = {
            'rental_income': sum(prop.monthly_rent * 12 for prop in portfolio_properties),
            'appreciation': sum((prop.current_value or prop.total_investment) - prop.total_investment 
                              for prop in portfolio_properties if (prop.current_value or 0) > prop.total_investment)
        }
        
        total_income = sum(income_sources.values())
        
        if total_income == 0:
            return {'score': 0, 'source_distribution': income_sources, 'concentration': 1}
        
        max_concentration = max(income_sources.values()) / total_income
        score = (1 - max_concentration) * 100
        
        return {
            'score': score,
            'source_distribution': income_sources,
            'concentration': max_concentration
        }
    
    def analyze_market_timing(self, portfolio_id: uuid.UUID) -> MarketTimingRecommendation:
        """Analyze market timing for portfolio optimization."""
        try:
            # Get portfolio properties for market analysis
            portfolio_properties = self.db.query(PortfolioPropertyDB).filter(
                PortfolioPropertyDB.portfolio_id == portfolio_id
            ).all()
            
            if not portfolio_properties:
                return MarketTimingRecommendation(
                    portfolio_id=portfolio_id,
                    market_phase="unknown",
                    recommended_actions=[],
                    market_indicators={},
                    timing_confidence=0.0,
                    optimal_timing_window={},
                    risk_factors=[]
                )
            
            # Get market data for portfolio locations
            property_ids = [prop.property_id for prop in portfolio_properties]
            properties = self.db.query(PropertyDB).filter(PropertyDB.id.in_(property_ids)).all()
            
            # Analyze market indicators (simplified)
            market_indicators = {
                'price_trend': 'stable',  # Would come from market data service
                'inventory_levels': 'normal',
                'interest_rates': 'rising',
                'economic_indicators': 'mixed'
            }
            
            # Determine market phase based on indicators
            market_phase = self._determine_market_phase(market_indicators)
            
            # Generate recommendations based on market phase
            recommended_actions = self._get_market_phase_actions(market_phase)
            
            # Calculate timing confidence
            timing_confidence = 0.75  # Simplified - would be based on data quality and consistency
            
            # Determine optimal timing window
            optimal_timing_window = {
                'start': datetime.now(),
                'end': datetime.now() + timedelta(days=90)
            }
            
            # Identify risk factors
            risk_factors = [
                "Interest rate volatility",
                "Economic uncertainty",
                "Local market conditions"
            ]
            
            return MarketTimingRecommendation(
                portfolio_id=portfolio_id,
                market_phase=market_phase,
                recommended_actions=recommended_actions,
                market_indicators=market_indicators,
                timing_confidence=timing_confidence,
                optimal_timing_window=optimal_timing_window,
                risk_factors=risk_factors
            )
            
        except Exception as e:
            logger.error(f"Error analyzing market timing: {str(e)}")
            raise
    
    def _determine_market_phase(self, market_indicators: Dict[str, Any]) -> str:
        """Determine current market phase based on indicators."""
        # Simplified market phase determination
        price_trend = market_indicators.get('price_trend', 'stable')
        inventory = market_indicators.get('inventory_levels', 'normal')
        
        if price_trend == 'rising' and inventory == 'low':
            return 'expansion'
        elif price_trend == 'rising' and inventory == 'high':
            return 'peak'
        elif price_trend == 'falling' and inventory == 'high':
            return 'contraction'
        elif price_trend == 'falling' and inventory == 'low':
            return 'trough'
        else:
            return 'stable'
    
    def _get_market_phase_actions(self, market_phase: str) -> List[str]:
        """Get recommended actions based on market phase."""
        actions = {
            'expansion': [
                "Consider accelerating acquisitions",
                "Lock in favorable financing terms",
                "Focus on value-add opportunities"
            ],
            'peak': [
                "Consider selective dispositions",
                "Harvest gains from appreciated properties",
                "Prepare for market correction"
            ],
            'contraction': [
                "Hold quality assets",
                "Focus on cash flow stability",
                "Prepare for acquisition opportunities"
            ],
            'trough': [
                "Aggressively pursue acquisitions",
                "Focus on distressed opportunities",
                "Prepare for market recovery"
            ],
            'stable': [
                "Maintain current strategy",
                "Focus on operational improvements",
                "Monitor market indicators closely"
            ]
        }
        
        return actions.get(market_phase, actions['stable'])


def get_portfolio_optimization_service(db: Session = None) -> PortfolioOptimizationService:
    """Factory function to get PortfolioOptimizationService instance."""
    if db is None:
        db = next(get_db())
    return PortfolioOptimizationService(db)