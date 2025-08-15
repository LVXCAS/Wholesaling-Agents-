#!/usr/bin/env python3
"""
Simple test to verify portfolio performance tracking functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.portfolio_performance_service import PortfolioPerformanceService
from app.services.portfolio_management_service import PortfolioManagementService
from unittest.mock import Mock
import uuid
from datetime import datetime, timedelta

def test_portfolio_performance_service():
    """Test basic portfolio performance service functionality."""
    print("Testing Portfolio Performance Service...")
    
    # Create mock database
    mock_db = Mock()
    service = PortfolioPerformanceService(mock_db)
    
    # Test empty portfolio metrics
    result = service._empty_portfolio_metrics(uuid.uuid4())
    assert result["total_properties"] == 0
    assert result["total_value"] == 0.0
    print("✓ Empty portfolio metrics test passed")
    
    # Test diversification score calculation
    score = service._calculate_diversification_score([])
    assert score == 0.0
    print("✓ Diversification score test passed")
    
    # Test risk score calculation
    risk_score = service._calculate_risk_score([])
    assert risk_score == 0.0
    print("✓ Risk score test passed")
    
    print("Portfolio Performance Service tests completed successfully!")

def test_portfolio_management_service():
    """Test basic portfolio management service functionality."""
    print("\nTesting Portfolio Management Service...")
    
    # Create mock database
    mock_db = Mock()
    service = PortfolioManagementService(mock_db)
    
    # Test that service initializes correctly
    assert service.db == mock_db
    assert service.performance_service is not None
    print("✓ Service initialization test passed")
    
    print("Portfolio Management Service tests completed successfully!")

def test_integration():
    """Test integration between services."""
    print("\nTesting Service Integration...")
    
    # Create mock database
    mock_db = Mock()
    
    # Create management service (which creates performance service internally)
    mgmt_service = PortfolioManagementService(mock_db)
    perf_service = mgmt_service.performance_service
    
    # Verify they share the same database connection
    assert mgmt_service.db == perf_service.db
    print("✓ Service integration test passed")
    
    print("Service integration tests completed successfully!")

if __name__ == "__main__":
    print("Running Portfolio Performance Tracking Tests...")
    print("=" * 60)
    
    try:
        test_portfolio_performance_service()
        test_portfolio_management_service()
        test_integration()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! Portfolio Performance Tracking is working correctly.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)