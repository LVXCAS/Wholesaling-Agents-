"""
Models package for the Real Estate Empire platform.
"""

from .property import (
    PropertyDB,
    PropertyAnalysisDB,
    PropertyCreate,
    PropertyUpdate,
    PropertyResponse,
    PropertyAnalysisCreate,
    PropertyAnalysisResponse,
    PropertyTypeEnum,
    PropertyStatusEnum,
)

from .lead import (
    PropertyLeadDB,
    CommunicationDB,
    PropertyLeadCreate,
    PropertyLeadUpdate,
    PropertyLeadResponse,
    CommunicationCreate,
    CommunicationResponse,
    LeadStatusEnum,
    LeadSourceEnum,
    ContactMethodEnum,
)

from .wholesale import (
    WholesaleDealDB,
    RepairItemDB,
    InvestmentStrategyDB,
    WholesaleDealCreate,
    WholesaleDealUpdate,
    WholesaleDealResponse,
    RepairItemCreate,
    RepairItemResponse,
    InvestmentStrategyCreate,
    InvestmentStrategyResponse,
    DealStatusEnum,
    StrategyTypeEnum,
)

__all__ = [
    # Property models
    "PropertyDB",
    "PropertyAnalysisDB",
    "PropertyCreate",
    "PropertyUpdate",
    "PropertyResponse",
    "PropertyAnalysisCreate",
    "PropertyAnalysisResponse",
    "PropertyTypeEnum",
    "PropertyStatusEnum",
    
    # Lead models
    "PropertyLeadDB",
    "CommunicationDB",
    "PropertyLeadCreate",
    "PropertyLeadUpdate",
    "PropertyLeadResponse",
    "CommunicationCreate",
    "CommunicationResponse",
    "LeadStatusEnum",
    "LeadSourceEnum",
    "ContactMethodEnum",
    
    # Wholesale models
    "WholesaleDealDB",
    "RepairItemDB",
    "InvestmentStrategyDB",
    "WholesaleDealCreate",
    "WholesaleDealUpdate",
    "WholesaleDealResponse",
    "RepairItemCreate",
    "RepairItemResponse",
    "InvestmentStrategyCreate",
    "InvestmentStrategyResponse",
    "DealStatusEnum",
    "StrategyTypeEnum",
]