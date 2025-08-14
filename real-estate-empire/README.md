# Real Estate Empire

An AI-powered real estate investment platform that automates the full lifecycle of real estate investment, from deal sourcing to portfolio management.

## Features

- **Deal Sourcing**: Automated property discovery from multiple sources
- **AI Property Analysis**: Comprehensive financial analysis with ARV estimation
- **Lead Management**: Track property owners and communication history
- **Wholesale Analysis**: Specialized tools for wholesale real estate deals
- **Portfolio Management**: Track and optimize investment performance
- **AI-Driven Communication**: Automated outreach and follow-up

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL database
- Virtual environment (recommended)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd real-estate-empire
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database configuration
```

5. Initialize the database:
```bash
python scripts/init_db.py
```

### Database Configuration

Set the `DATABASE_URL` environment variable:
```
DATABASE_URL=postgresql://username:password@localhost:5432/real_estate_empire
```

## Project Structure

```
real-estate-empire/
├── app/
│   ├── core/           # Core configuration and database
│   ├── models/         # SQLAlchemy and Pydantic models
│   ├── services/       # Business logic services
│   ├── api/           # FastAPI endpoints
│   └── cli/           # CLI commands
├── scripts/           # Utility scripts
├── tests/            # Test files
└── requirements.txt  # Python dependencies
```

## Data Models

### Property Model
- Comprehensive property information including location, characteristics, and financial data
- Support for multiple property types and statuses
- Integration with external data sources

### Lead Model
- Property owner information and contact details
- Communication history and preferences
- Motivation scoring and tracking

### Wholesale Deal Model
- Deal pipeline management
- Financial analysis and profit calculations
- Buyer matching and assignment tracking

## Development Status

This project is currently in active development. The following components have been implemented:

- ✅ Core data models (Property, Lead, Wholesale Deal)
- ✅ Database configuration and initialization
- 🚧 Business logic services (in progress)
- 🚧 API endpoints (planned)
- 🚧 CLI interface (planned)
- 🚧 AI integration (planned)

## Contributing

This is a private project. Please contact the project owner for contribution guidelines.

## License

Private - All rights reserved.