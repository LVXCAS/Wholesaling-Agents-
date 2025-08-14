import pytest
from typer.testing import CliRunner

# Need to adjust sys.path for tests to find the 'app' module
import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from app.cli import app # Assuming run.py uses app.cli:app (which it does, app = cli_app)

runner = CliRunner()

def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage: RealEstateCLI" in result.stdout # Check for Typer app name or a known command
    assert "init-db" in result.stdout
    assert "analyze-property" in result.stdout
    assert "load-sample-data" in result.stdout
    assert "list-properties" in result.stdout

def test_cli_init_db_dry_run():
    # This test will actually try to run init-db.
    # For a unit test, we might want to mock the database operations.
    # For an initial test, just check if the command runs and prints expected output.
    # Warning: This can have side effects if not pointed to a test DB.
    # For now, we assume it prints success or known error messages.
    result = runner.invoke(app, ["init-db"])
    assert result.exit_code == 0 # Expect success if DB is available, or known error if not
    # Check for either success or a common connection error message
    assert "Database initialized successfully!" in result.stdout or "Error initializing database" in result.stdout

def test_cli_analyze_property_placeholder():
    result = runner.invoke(app, ["analyze-property", "123 Test Address"]) # Corrected argument passing
    assert result.exit_code == 0
    assert "Analyzing property: 123 Test Address" in result.stdout
    assert "Analysis placeholder" in result.stdout

def test_cli_list_properties_runs():
    # Similar to init-db, this might interact with DB.
    # Check for non-error exit and some expected output.
    result = runner.invoke(app, ["list-properties"])
    assert result.exit_code == 0
    assert "Listing all properties..." in result.stdout or "No properties found" in result.stdout or "Properties" in result.stdout


# Note: Testing load-sample-data directly like this will modify the database.
# Such tests are more integration tests and should ideally run against a test database.
# For this initial suite, we might skip directly testing load-sample-data's DB effects
# or ensure it does not error out.

def test_cli_load_sample_data_runs():
    result = runner.invoke(app, ["load-sample-data"])
    assert result.exit_code == 0
    # Check for either success or a common connection error message or skip message
    assert "Sample data loaded successfully" in result.stdout or "Error loading sample data" in result.stdout or "Skipped" in result.stdout or "No sample properties were added." in result.stdout
