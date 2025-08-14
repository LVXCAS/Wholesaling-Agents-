from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class PropertyRecord:
    brokered_by: Optional[float]
    status: str
    price: Optional[float]
    bed: Optional[int]
    bath: Optional[float]
    acre_lot: Optional[float]
    street: Optional[str]
    city: str
    state: str
    zip_code: Optional[str]
    house_size: Optional[float]
    prev_sold_date: Optional[str]
    
    @property
    def price_per_sqft(self) -> Optional[float]:
        if self.price and self.house_size and self.house_size > 0:
            return self.price / self.house_size
        return None

@dataclass
class MarketStats:
    city: str
    state: str
    avg_price: float
    median_price: float
    avg_price_per_sqft: float
    total_listings: int
    avg_bedrooms: float
    avg_bathrooms: float
    avg_house_size: float

@dataclass
class ComparableProperty:
    property: PropertyRecord
    similarity_score: float
    distance_factor: float