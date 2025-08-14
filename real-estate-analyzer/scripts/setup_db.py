import logging
import sys
import os

# Add the project root to the Python path to allow importing app modules
# This is often needed when running scripts from a subdirectory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from app.core.database import create_tables, engine # Import engine to check connection
from app.core.config import settings # To ensure DATABASE_URL is loaded via settings
from app.models import property # Ensure models are imported before create_tables
from app.models import valuation # Ensure models are imported

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def initialize_database():
    logger.info("Initializing database...")
    logger.info(f"Using database URL: {settings.DATABASE_URL}") # Log the URL being used (mask password if sensitive)

    try:
        # Attempt a connection to check if the database server is accessible
        with engine.connect() as connection:
            logger.info("Successfully connected to the database server.")

        logger.info("Creating tables based on SQLAlchemy models...")
        # The create_tables function in database.py should handle importing models
        # and calling Base.metadata.create_all(bind=engine)
        create_tables()
        logger.info("Database tables created successfully (or already exist).")

    except Exception as e:
        logger.error(f"An error occurred during database initialization: {e}")
        logger.error("Please ensure the PostgreSQL server is running and accessible, and the DATABASE_URL is correctly configured in your .env file.")
        sys.exit(1)

if __name__ == "__main__":
    initialize_database()
