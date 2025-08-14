import typer
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

try:
    from app.cli import app as cli_app
except ModuleNotFoundError:
    print("Failed to import cli_app from app.cli.")
    sys.exit(1)
# Ensure cli_app is assigned to app for Typer to find it if run.py is invoked directly.
# Typer looks for a Typer instance named 'app' by default if no function is called.
app = cli_app

if __name__ == "__main__":
    app()
