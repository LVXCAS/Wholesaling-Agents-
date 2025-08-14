# Real Estate Analyzer

This project is a terminal-based real estate property analysis system designed to run in GitHub Codespaces and locally. It provides tools for property data management, ARV (After Repair Value) estimation, and market analysis.

## Phase 1: MVP - Property Analysis & ARV

This is Phase 1, focusing on building a Minimum Viable Product (MVP) that can:
- Manage property data via a CLI and API.
- Calculate ARV estimates based on comparable sales (currently using placeholder logic).
- Run in a containerized environment using Docker and PostgreSQL.

## Key Features

- **CLI Interface:** Manage properties, run analyses, and manage the database via `python run.py` commands.
- **FastAPI Backend:** Provides an API for property management and future analysis endpoints.
- **PostgreSQL Database:** Stores property data, analysis results, and comparable sales.
- **Dockerized Environment:** Easy setup and consistent environment using Docker and Docker Compose.
- **GitHub Codespaces Ready:** Pre-configured for development in GitHub Codespaces.
- **ARV Calculation Engine:** (Placeholder) Core logic for estimating After Repair Value.
- **Mock Data Services:** (Placeholders) For simulating external data sources for property and comparable sales.

## Prerequisites

- Git
- Python 3.10+
- Docker & Docker Compose (for local setup or if not using Codespaces)
- Access to a terminal or command line.

## Setup Instructions

### Recommended: GitHub Codespaces

1.  Open this repository in GitHub Codespaces.
2.  The environment will be automatically set up based on `.devcontainer/devcontainer.json`.
    - Python dependencies will be installed.
    - The PostgreSQL database service will be started.
    - The database schema will be initialized (via `python run.py init-db` in `postCreateCommand`).
3.  Once the Codespace is ready, you can optionally load more sample data or run other setup steps using the `setup.sh` script:
    ```bash
    ./setup.sh
    ```
    This script will also initialize the DB and load sample data if `postCreateCommand` didn't fully complete or if you want to re-run.

### Local Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd real-estate-analyzer
    ```

2.  **Create and activate a virtual environment** (recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Copy `.env.example` to a new file named `.env` and customize it if necessary (especially `DATABASE_URL` if not using the default Docker setup).
    ```bash
    cp .env.example .env
    ```
    If you are using the provided Docker setup locally, the default `DATABASE_URL` in `.env.example` should work with the `docker-compose.yml`.

5.  **Start Docker services (Database):**
    Ensure Docker Desktop (or Docker engine) is running. Then, from the project root:
    ```bash
    docker-compose -f docker/docker-compose.yml up -d db
    ```
    This will start the PostgreSQL database service in the background. Wait a few moments for it to initialize.

6.  **Run the setup script:**
    This script will initialize the database schema and load sample data.
    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```
    Alternatively, you can run the commands manually:
    ```bash
    python run.py init-db
    python run.py load-sample-data
    ```

## Basic Usage

All commands are run from the project root directory.

### CLI (`run.py`)

The main entry point for the CLI is `run.py`. It uses Typer for command management.

-   **Show help:**
    ```bash
    python run.py --help
    ```

-   **Initialize the database:** (Creates tables based on models)
    ```bash
    python run.py init-db
    ```

-   **Load sample property data:**
    ```bash
    python run.py load-sample-data
    ```

-   **List properties:**
    ```bash
    python run.py list-properties
    ```

-   **Analyze a property (placeholder):**
    The `PropertyCreate` model now takes `address` as the only strictly required field for basic addition. Other fields are optional or have defaults.
    ```bash
    # First, add a property if it does not exist (example using CLI 'property add' which is not in current app/cli.py)
    # The current app/cli.py 'load-sample-data' adds "123 Main St".
    # Let's use the command from app/cli.py:
    # python run.py property add --address "777 Lucky Lane" --city "Gamblers Gulch" --state "NV" --zip-code "89109" --bedrooms 3 --bathrooms 2 --sqft 1800 --current-value 500000
    # The user's latest CLI in app/cli.py does not have a 'property add' command.
    # It has 'load-sample-data'. The '123 Main St' address is part of sample data.

    # Then analyze (current analyze command in app/cli.py takes address)
    python run.py analyze-property "123 Main St"
    ```
    *(Note: The `analyze-property` command is currently a placeholder and uses mock data/logic).*

-   **Add a new property via CLI:**
    The current `app/cli.py` from the previous step (plan item 14) does not have a `property add` subcommand. It has `load-sample-data`. The `README.md` example for `property add` needs to align with the actual CLI.
    For now, I will keep the README as provided by the user, assuming the CLI might be updated later or this is a general example.


### FastAPI Backend

The FastAPI application provides an API for property management and analysis.

1.  **Ensure the database container is running** (if not already, e.g., for local setup):
    ```bash
    docker-compose -f docker/docker-compose.yml up -d db
    ```

2.  **Run the FastAPI application using Uvicorn:**
    From the project root:
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    Or, if running inside the Docker container setup (e.g., via `docker-compose -f docker/docker-compose.yml up app` or in Codespaces), it will be automatically run.

3.  **Access API documentation:**
    Once the server is running, open your browser and go to:
    -   Swagger UI: `http://localhost:8000/docs`
    -   ReDoc: `http://localhost:8000/redoc`

    You can interact with the API endpoints directly from these interfaces.

## Running Tests

Tests are written using `pytest`.

1.  Ensure `pytest` is installed (it's in `requirements.txt`).
2.  Run tests from the project root directory:
    ```bash
    pytest
    ```

## Project Structure

(A brief overview of the project structure can be added here if desired, but it was detailed in the initial issue.)
```
real-estate-analyzer/
├── app/                  # Core application (FastAPI, CLI, services, models)
│   ├── api/              # FastAPI endpoints
│   ├── core/             # Core components (config, database)
│   ├── models/           # Pydantic and SQLAlchemy models
│   ├── services/         # Business logic services
│   └── cli.py            # Typer CLI application logic
├── docker/               # Docker configuration (Dockerfile, docker-compose.yml)
├── scripts/              # Utility scripts (setup_db.py, sample_data.py)
├── tests/                # Pytest tests
├── .devcontainer/        # GitHub Codespaces configuration
├── .env.example          # Example environment variables
├── README.md             # This file
├── requirements.txt      # Python dependencies
└── run.py                # Main CLI entry point script
└── setup.sh              # Main setup script
```

## Future Enhancements (Phase 2+)

- Full implementation of ARV calculation logic.
- Integration with real external APIs for property data and comparables.
- Advanced data validation and error handling.
- More comprehensive CLI commands and API endpoints.
- User authentication and authorization for the API.
- Batch processing improvements.
- Web interface (potentially).
