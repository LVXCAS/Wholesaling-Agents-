#!/bin/bash
# Setup script for the Real Estate Analyzer project

echo "🚀 Starting Real Estate Analyzer Setup..."

# Exit immediately if a command exits with a non-zero status.
set -e

echo "\n🐍 Ensuring Python dependencies are installed..."
# This might be redundant if postCreateCommand in devcontainer runs it,
# but good for standalone setup or if user wants to re-run.
pip install -r requirements.txt
echo "✅ Dependencies checked/installed."

echo "\n💾 Initializing database (creating tables if they do not exist)..."
# This uses the Typer CLI command defined in app/cli.py
python run.py init-db # Corrected: was 'db init-db'
echo "✅ Database initialized."

echo "\n🌱 Loading sample data into the database..."
# This uses the Typer CLI command, which loads a few samples.
# Alternatively, could run: python scripts/sample_data.py for more diverse data.
python run.py load-sample-data
echo "✅ Sample data loading process completed."

echo "\n🔍 Running a placeholder analysis demo..."
# This calls the placeholder CLI command.
# Replace '123 Main St, Las Vegas, NV 89101' with an address from your sample data if available and relevant.
# The analyze-property command currently takes --id, not an address string directly.
# The user CLI had analyze-property <address>
# My current app/cli.py has: analyze-property --id <UUID> and analyze-address <address_string>
# Let's use analyze-address as it's simpler for a demo without needing an ID.
# The user's latest app/cli.py has `analyze-property` taking an address string.
# Let's verify current app/cli.py:
# @app.command() def analyze_property(address: str):
# Yes, it takes an address.

python run.py analyze-property "123 Main St" # Corrected: address is an argument, not an option
echo "✅ Placeholder analysis demo command executed."


# List some properties as a final check
echo "\n📋 Listing a few properties from the database..."
python run.py list-properties # Assuming list-properties supports --limit, if not, just list-properties
# The user's app/cli.py for list-properties does not have --limit.
# So, just call list-properties.
# python run.py list-properties


echo "\n🎉 Setup Complete! You can now use the Real Estate Analyzer CLI."
echo "   Try running: python run.py --help"
