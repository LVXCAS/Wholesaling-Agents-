import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from ..services.market_data_service import MarketDataService
from ..services.gemini_service import GeminiService
from ..models.market_data import PropertyRecord

@dataclass
class MarketCondition:
    """Current market state"""
    trend: str  # "bull", "bear", "stable"
    interest_rate: float
    inventory_level: str  # "low", "normal", "high"
    price_momentum: float  # -1.0 to 1.0
    volatility: float  # 0.0 to 1.0
    season: str  # "spring", "summer", "fall", "winter"

@dataclass
class SimulatedDeal:
    """A simulated real estate deal"""
    property_id: str
    property_data: Dict[str, Any]
    market_value: float
    asking_price: float
    seller_motivation: float  # 0.0 to 1.0
    days_on_market: int
    competition_level: float  # 0.0 to 1.0
    market_condition: MarketCondition
    created_at: datetime

class MarketSimulator:
    """Simulates realistic real estate market conditions and deals"""
    
    def __init__(self, market_service: MarketDataService):
        self.market_service = market_service
        try:
            self.gemini_service = GeminiService()
            print("✅ Gemini service integrated into market simulator")
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize Gemini service in market simulator: {e}")
            self.gemini_service = None
        
        self.current_condition = self._generate_market_condition()
        self.active_deals: List[SimulatedDeal] = []
        self.deal_history: List[SimulatedDeal] = []
        
    def _generate_market_condition(self) -> MarketCondition:
        """Generate realistic market conditions"""
        trends = ["bull", "bear", "stable"]
        trend_weights = [0.3, 0.2, 0.5]  # Stable markets more common
        
        trend = np.random.choice(trends, p=trend_weights)
        
        # Interest rates typically 3-8%
        base_rate = 5.5
        rate_variation = np.random.normal(0, 1.5)
        interest_rate = max(2.0, min(10.0, base_rate + rate_variation))
        
        # Inventory levels
        inventory_levels = ["low", "normal", "high"]
        inventory_weights = [0.25, 0.5, 0.25]
        inventory = np.random.choice(inventory_levels, p=inventory_weights)
        
        # Price momentum based on trend
        if trend == "bull":
            price_momentum = np.random.uniform(0.2, 0.8)
        elif trend == "bear":
            price_momentum = np.random.uniform(-0.8, -0.2)
        else:
            price_momentum = np.random.uniform(-0.3, 0.3)
        
        # Volatility
        volatility = np.random.uniform(0.1, 0.6)
        
        # Season
        seasons = ["spring", "summer", "fall", "winter"]
        season = np.random.choice(seasons)
        
        return MarketCondition(
            trend=trend,
            interest_rate=interest_rate,
            inventory_level=inventory,
            price_momentum=price_momentum,
            volatility=volatility,
            season=season
        )
    
    def generate_deal_scenario(self, target_city: str = None, target_state: str = None) -> SimulatedDeal:
        """Generate a realistic deal scenario from market data"""
        
        # Get a random property from our dataset
        import sqlite3
        import pandas as pd
        
        conn = sqlite3.connect(self.market_service.db_path)
        
        # Build query based on targets
        conditions = ["price IS NOT NULL", "house_size IS NOT NULL"]
        params = []
        
        if target_city:
            conditions.append("LOWER(city) = LOWER(?)")
            params.append(target_city)
        
        if target_state:
            conditions.append("LOWER(state) = LOWER(?)")
            params.append(target_state)
        
        query = f"""
        SELECT * FROM properties 
        WHERE {' AND '.join(conditions)}
        ORDER BY RANDOM() 
        LIMIT 1
        """
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if df.empty:
            raise ValueError("No properties found for simulation")
        
        property_row = df.iloc[0]
        
        # Create property data
        property_data = {
            'city': property_row['city'],
            'state': property_row['state'],
            'bedrooms': property_row['bed'],
            'bathrooms': property_row['bath'],
            'house_size': property_row['house_size'],
            'acre_lot': property_row.get('acre_lot', 0),
            'zip_code': property_row.get('zip_code')
        }
        
        # Base market value from our data
        base_value = property_row['price']
        
        # Apply market conditions to value
        market_multiplier = 1.0 + (self.current_condition.price_momentum * 0.1)
        market_value = base_value * market_multiplier
        
        # Generate asking price with seller psychology
        seller_motivation = np.random.uniform(0.2, 1.0)
        
        if seller_motivation > 0.8:  # Highly motivated
            asking_multiplier = np.random.uniform(0.95, 1.05)
        elif seller_motivation > 0.5:  # Moderately motivated
            asking_multiplier = np.random.uniform(1.0, 1.15)
        else:  # Not very motivated
            asking_multiplier = np.random.uniform(1.1, 1.3)
        
        asking_price = market_value * asking_multiplier
        
        # Days on market based on conditions
        if self.current_condition.inventory_level == "low":
            days_on_market = np.random.randint(1, 30)
        elif self.current_condition.inventory_level == "normal":
            days_on_market = np.random.randint(15, 90)
        else:  # high inventory
            days_on_market = np.random.randint(60, 180)
        
        # Competition level
        if self.current_condition.trend == "bull":
            competition_level = np.random.uniform(0.6, 1.0)
        elif self.current_condition.trend == "bear":
            competition_level = np.random.uniform(0.1, 0.4)
        else:
            competition_level = np.random.uniform(0.3, 0.7)
        
        deal = SimulatedDeal(
            property_id=f"SIM_{random.randint(100000, 999999)}",
            property_data=property_data,
            market_value=market_value,
            asking_price=asking_price,
            seller_motivation=seller_motivation,
            days_on_market=days_on_market,
            competition_level=competition_level,
            market_condition=self.current_condition,
            created_at=datetime.now()
        )
        
        self.active_deals.append(deal)
        return deal
    
    def simulate_market_cycle(self, days: int = 365) -> List[MarketCondition]:
        """Simulate market conditions over time"""
        conditions = []
        current_date = datetime.now()
        
        for day in range(days):
            # Evolve market conditions
            self.current_condition = self._evolve_market_condition(self.current_condition)
            conditions.append(self.current_condition)
            current_date += timedelta(days=1)
        
        return conditions
    
    def _evolve_market_condition(self, current: MarketCondition) -> MarketCondition:
        """Evolve market conditions over time"""
        
        # Trend persistence with some randomness
        trend_change_prob = 0.05  # 5% chance to change trend each day
        
        if np.random.random() < trend_change_prob:
            trends = ["bull", "bear", "stable"]
            new_trend = np.random.choice([t for t in trends if t != current.trend])
        else:
            new_trend = current.trend
        
        # Interest rate changes (more gradual)
        rate_change = np.random.normal(0, 0.01)  # Small daily changes
        new_rate = max(2.0, min(10.0, current.interest_rate + rate_change))
        
        # Price momentum evolution
        momentum_change = np.random.normal(0, 0.05)
        new_momentum = max(-1.0, min(1.0, current.price_momentum + momentum_change))
        
        # Volatility changes
        volatility_change = np.random.normal(0, 0.02)
        new_volatility = max(0.1, min(1.0, current.volatility + volatility_change))
        
        return MarketCondition(
            trend=new_trend,
            interest_rate=new_rate,
            inventory_level=current.inventory_level,  # Keep same for simplicity
            price_momentum=new_momentum,
            volatility=new_volatility,
            season=current.season  # Keep same for simplicity
        )
    
    def get_market_summary(self) -> Dict[str, Any]:
        """Get current market summary"""
        return {
            "condition": {
                "trend": self.current_condition.trend,
                "interest_rate": round(self.current_condition.interest_rate, 2),
                "inventory_level": self.current_condition.inventory_level,
                "price_momentum": round(self.current_condition.price_momentum, 3),
                "volatility": round(self.current_condition.volatility, 3),
                "season": self.current_condition.season
            },
            "active_deals": len(self.active_deals),
            "total_deals_generated": len(self.deal_history) + len(self.active_deals)
        }
    
    async def get_ai_market_analysis(self) -> Dict[str, Any]:
        """Get AI-powered market analysis using Gemini"""
        if not self.gemini_service:
            return {"error": "Gemini service not available"}
        
        try:
            market_data = {
                "trend": self.current_condition.trend,
                "interest_rate": self.current_condition.interest_rate,
                "inventory": self.current_condition.inventory_level,
                "price_change": self.current_condition.price_momentum * 100,
                "volatility": self.current_condition.volatility,
                "season": self.current_condition.season,
                "active_deals": len(self.active_deals),
                "recent_sales": [
                    {
                        "price": deal.asking_price,
                        "days_on_market": deal.days_on_market,
                        "location": f"{deal.property_data.get('city', 'Unknown')}, {deal.property_data.get('state', 'Unknown')}"
                    }
                    for deal in self.active_deals[:5]
                ]
            }
            
            analysis = await self.gemini_service.analyze_market_trends(market_data)
            return {
                "ai_analysis": analysis.content,
                "confidence": analysis.confidence,
                "market_data": market_data
            }
        except Exception as e:
            return {"error": f"AI analysis failed: {e}"}
    
    def generate_batch_scenarios(self, count: int, cities: List[str] = None) -> List[SimulatedDeal]:
        """Generate multiple deal scenarios for training"""
        scenarios = []
        
        for _ in range(count):
            city = np.random.choice(cities) if cities else None
            try:
                deal = self.generate_deal_scenario(target_city=city)
                scenarios.append(deal)
            except ValueError:
                continue  # Skip if no properties found
        
        return scenarios
    
    def close_deal(self, deal_id: str, outcome: Dict[str, Any]):
        """Record deal outcome and move to history"""
        deal = next((d for d in self.active_deals if d.property_id == deal_id), None)
        
        if deal:
            # Add outcome data to deal
            deal.outcome = outcome
            
            # Move to history
            self.active_deals.remove(deal)
            self.deal_history.append(deal)
            
            return True
        return False