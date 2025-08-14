"""
Main FastAPI application for Real Estate Empire Property Analysis API
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any

from .routers import property_analysis, strategy_analysis, data_export, market_data, investment_analysis, lead_import, lead_management, appointment_scheduling, followup_management, lead_nurturing, data_processor
from ..simulation import simulation_api
from ..training import simple_training_api
from ..core.database import engine, Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables (only if not in test mode)
import os
if not os.getenv("TESTING"):
    Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Real Estate Empire - Property Analysis API",
    description="Comprehensive property analysis and investment evaluation API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    property_analysis.router,
    prefix="/api/v1/properties",
    tags=["Property Analysis"]
)

app.include_router(
    strategy_analysis.router,
    prefix="/api/v1/strategies",
    tags=["Strategy Analysis"]
)

app.include_router(
    data_export.router,
    prefix="/api/v1/export",
    tags=["Data Export"]
)

app.include_router(
    lead_import.router,
    tags=["Lead Import"]
)

app.include_router(
    lead_management.router,
    tags=["Lead Management"]
)

app.include_router(
    appointment_scheduling.router,
    prefix="/api/v1",
    tags=["Appointment Scheduling"]
)

app.include_router(
    followup_management.router,
    prefix="/api/v1",
    tags=["Follow-up Management"]
)

app.include_router(
    lead_nurturing.router,
    prefix="/api/v1",
    tags=["Lead Nurturing"]
)

app.include_router(
    market_data.router,
    prefix="/api/v1",
    tags=["Market Data"]
)

app.include_router(
    investment_analysis.router,
    prefix="/api/v1",
    tags=["Investment Analysis"]
)

app.include_router(
    data_processor.router,
    prefix="/api/v1",
    tags=["Data Processor"]
)

app.include_router(
    simulation_api.router,
    prefix="/api/v1",
    tags=["Agent Simulation"]
)

app.include_router(
    simple_training_api.router,
    prefix="/api/v1",
    tags=["Agent Training"]
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Real Estate Empire Property Analysis API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "1.0.0"
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)