# Model Testing Guide

This guide explains how to accurately test the negotiation models and services in the Real Estate Empire platform.

## Overview

We have implemented comprehensive testing for the negotiation system with **142 test cases** covering:

- **16 Model Tests** - Database models, Pydantic models, relationships, and validation
- **24 Strategy Service Tests** - Negotiation strategy generation and analysis
- **40 Offer Generation Tests** - Offer creation, pricing, and competitiveness analysis
- **30 Counter Offer Analyzer Tests** - Counter offer analysis and response recommendations
- **25 Coaching Service Tests** - Negotiation coaching and guidance generation
- **7 Integration Tests** - End-to-end workflow testing

## Testing Approach

### 1. Model Testing (`test_negotiation_models.py`)

**Database Model Testing:**
- Uses in-memory SQLite database for fast, isolated tests
- Tests model creation, relationships, and constraints
- Validates required fields and default values
- Tests JSON field serialization/deserialization

```python
@pytest.fixture(scope="function")
def db_session(self):
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
```

**Pydantic Model Testing:**
- Tests model validation and serialization
- Validates field constraints (e.g., confidence_score 0-1 range)
- Tests enum values and type checking

**Key Testing Patterns:**
- Create real database instances to test relationships
- Test both valid and invalid data scenarios
- Verify JSON field handling for complex data structures
- Test model `__repr__` methods for debugging

### 2. Service Testing

**Unit Testing with Mocks:**
- Mock database sessions to isolate business logic
- Test individual methods with controlled inputs
- Verify error handling and edge cases

```python
@pytest.fixture
def mock_db(self):
    """Create a mock database session."""
    return Mock(spec=Session)

@pytest.fixture
def service(self, mock_db):
    """Create service instance with mocked database."""
    return NegotiationStrategyService(mock_db)
```

**Business Logic Testing:**
- Test calculation algorithms (pricing, scoring, analysis)
- Verify decision logic (market conditions, approaches)
- Test data transformation and formatting

### 3. Integration Testing (`test_negotiation_integration.py`)

**End-to-End Workflow Testing:**
- Tests complete negotiation workflow from strategy to coaching
- Uses real database with in-memory SQLite
- Verifies data consistency across services
- Tests error handling and recovery

**Key Integration Scenarios:**
- Complete negotiation workflow (strategy → offer → counter-offer → coaching)
- Multiple offer generation strategies
- Market condition adaptation
- Data consistency and validation
- Error handling across services

## Best Practices for Model Testing

### 1. Database Testing

**Use In-Memory Databases:**
```python
engine = create_engine("sqlite:///:memory:", echo=False)
Base.metadata.create_all(engine)
```

**Benefits:**
- Fast test execution
- Complete isolation between tests
- No external dependencies
- Real database behavior testing

### 2. Mock vs Real Database

**Use Mocks For:**
- Unit testing business logic
- Testing error conditions
- Isolating specific functionality
- Fast execution of many test cases

**Use Real Database For:**
- Testing model relationships
- Validating constraints and foreign keys
- Integration testing
- JSON field serialization testing

### 3. Test Data Management

**Create Realistic Test Data:**
```python
@pytest.fixture
def sample_property(self, db_session):
    """Create a sample property in the database."""
    property_data = PropertyDB(
        address="123 Test St",
        city="Test City",
        listing_price=250000,
        days_on_market=60,
        renovation_needed=True
    )
    db_session.add(property_data)
    db_session.commit()
    db_session.refresh(property_data)
    return property_data
```

### 4. JSON Field Testing

**Handle DateTime Serialization:**
```python
def _serialize_for_json(self, obj: Any) -> Any:
    """Recursively convert datetime objects to ISO strings."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: self._serialize_for_json(value) for key, value in obj.items()}
    # ... handle other types
```

**Test Complex JSON Data:**
- Test nested dictionaries and arrays
- Verify data integrity after database round-trip
- Test edge cases with special characters and large data

### 5. Relationship Testing

**Test Foreign Key Constraints:**
```python
def test_offer_db_relationships(self, db_session, sample_property):
    """Test relationships between Offer and other models."""
    # Create strategy first
    strategy = NegotiationStrategyDB(...)
    db_session.add(strategy)
    db_session.commit()
    
    # Create offer with relationship
    offer = OfferDB(strategy_id=strategy.id, ...)
    db_session.add(offer)
    db_session.commit()
    
    # Test relationships work
    assert offer.strategy is not None
    assert offer.strategy.id == strategy.id
```

### 6. Validation Testing

**Test Field Constraints:**
```python
def test_confidence_score_validation(self):
    """Test confidence score must be between 0 and 1."""
    with pytest.raises(ValueError):
        NegotiationStrategyCreate(
            confidence_score=1.5  # Invalid: > 1
        )
```

**Test Required Fields:**
```python
def test_required_fields(self, db_session):
    """Test that required fields are enforced."""
    with pytest.raises(IntegrityError):
        strategy = NegotiationStrategyDB()  # Missing required fields
        db_session.add(strategy)
        db_session.commit()
```

## Running the Tests

### Run All Negotiation Tests
```bash
python -m pytest tests/test_negotiation_models.py tests/test_negotiation_strategy_service.py tests/test_offer_generation_service.py tests/test_counter_offer_analyzer_service.py tests/test_negotiation_coaching_service.py tests/test_negotiation_integration.py -v
```

### Run Specific Test Categories
```bash
# Model tests only
python -m pytest tests/test_negotiation_models.py -v

# Integration tests only
python -m pytest tests/test_negotiation_integration.py -v

# Service tests only
python -m pytest tests/test_negotiation_*_service.py -v
```

### Test Coverage Analysis
```bash
# Install coverage tool
pip install coverage

# Run tests with coverage
coverage run -m pytest tests/test_negotiation*.py

# Generate coverage report
coverage report -m
coverage html  # Creates htmlcov/index.html
```

## Common Testing Patterns

### 1. Parameterized Tests
```python
@pytest.mark.parametrize("market_condition,expected_approach", [
    (MarketConditionEnum.BUYERS_MARKET, "aggressive"),
    (MarketConditionEnum.SELLERS_MARKET, "conservative"),
    (MarketConditionEnum.BALANCED, "moderate"),
])
def test_negotiation_approach(self, service, market_condition, expected_approach):
    result = service._determine_approach(market_condition)
    assert result == expected_approach
```

### 2. Exception Testing
```python
def test_property_not_found(self, service, mock_db):
    """Test error handling when property doesn't exist."""
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(ValueError, match="Property.*not found"):
        service.generate_strategy(uuid.uuid4())
```

### 3. Mock Verification
```python
def test_database_interaction(self, service, mock_db):
    """Test that service interacts with database correctly."""
    mock_strategy = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_strategy
    
    result = service.get_strategy(uuid.uuid4())
    
    assert result == mock_strategy
    mock_db.query.assert_called_once_with(NegotiationStrategyDB)
```

## Test Results Summary

✅ **142 Total Tests Passing**
- 16 Model tests (database models, Pydantic models, validation)
- 24 Strategy service tests (market analysis, pricing, risk assessment)
- 40 Offer generation tests (pricing, terms, competitiveness)
- 30 Counter offer analyzer tests (analysis, recommendations, risk)
- 25 Coaching service tests (guidance, scripts, objection handling)
- 7 Integration tests (end-to-end workflows, error handling)

This comprehensive testing approach ensures:
- **Data Integrity** - Models work correctly with the database
- **Business Logic Accuracy** - Calculations and decisions are correct
- **Error Handling** - System gracefully handles edge cases
- **Integration Reliability** - Components work together properly
- **Regression Prevention** - Changes don't break existing functionality

The testing framework provides confidence that the negotiation system will work reliably in production while making it easy to add new features and maintain the codebase.