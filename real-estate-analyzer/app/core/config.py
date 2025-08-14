from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Database URL
    DATABASE_URL: str = "postgresql://user:pass@localhost/realestate"

    # API Rate Limiting
    API_RATE_LIMIT: int = 100 # Example: requests per minute

    # Cache Time-To-Live
    CACHE_TTL: int = 3600 # Seconds

    # Logging Level
    LOG_LEVEL: str = "INFO"

    # Real Estate Analysis Parameters
    ANALYSIS_RADIUS: float = 0.5 # Default radius in miles
    MAX_PROPERTY_AGE: int = 6    # Default maximum age in months for comparable sales

    # Optional: Project Name, API Prefix, etc. can be added here
    PROJECT_NAME: str = "Real Estate Analyzer"
    API_V1_STR: str = "/api/v1"

    # Pydantic-settings configuration
    # This tells Pydantic to load variables from a .env file if present,
    # and that environment variables are case-insensitive (though usually upper-case is convention).
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)


# Create a single instance of the settings to be used throughout the application
settings = Settings()
