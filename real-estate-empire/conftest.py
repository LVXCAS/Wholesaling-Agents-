"""
Pytest configuration and fixtures
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Also add the app directory
app_dir = project_root / "app"
sys.path.insert(0, str(app_dir))

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_gemini_service():
    """Mock Gemini service for testing"""
    mock = Mock()
    mock.analyze_property = AsyncMock(return_value={
        "analysis": "Test analysis",
        "score": 85,
        "recommendations": ["Test recommendation"]
    })
    return mock

@pytest.fixture
def sample_property_data():
    """Sample property data for testing"""
    return {
        "address": "123 Test St",
        "city": "Test City",
        "state": "CA",
        "zip_code": "12345",
        "price": 500000,
        "bedrooms": 3,
        "bathrooms": 2,
        "square_feet": 1500,
        "lot_size": 0.25,
        "year_built": 2000
    }