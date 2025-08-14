#!/usr/bin/env python3

import sys
sys.path.append('.')

from typing import List, Dict, Optional, Any, Tuple
import uuid
import math
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

try:
    from app.models.lead_scoring import (
        LeadScore, MotivationIndicator, PropertyConditionScore, MarketMetrics,
        FinancialIndicators, OwnerProfile, ScoringWeights, ScoringConfig,
        MotivationFactorEnum, DealPotentialEnum, LeadSourceEnum,
        LeadScoringBatch, LeadScoringBatchResult, ScoringAnalytics
    )
    print("✓ Lead scoring models imported")
except Exception as e:
    print(f"✗ Lead scoring models failed: {e}")

try:
    from app.models.lead import PropertyLeadDB, PropertyLeadCreate
    print("✓ Lead models imported")
except Exception as e:
    print(f"✗ Lead models failed: {e}")

try:
    from app.core.database import get_db
    print("✓ Database imported")
except Exception as e:
    print(f"✗ Database failed: {e}")

# Try to define a minimal class
class TestLeadScoringService:
    """Test service for scoring real estate leads"""
    
    def __init__(self, db: Session = None):
        self.db = db
        print("TestLeadScoringService created successfully")

# Test the class
try:
    service = TestLeadScoringService()
    print("✓ Test service created successfully")
except Exception as e:
    print(f"✗ Test service failed: {e}")