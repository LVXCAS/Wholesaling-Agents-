"""
Main FastAPI application for Real Estate Empire Property Analysis API
"""

import logging
import time
import secrets
from fastapi import FastAPI, HTTPException, Depends, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from typing import Dict, Any

from .routers import (
    property_analysis, strategy_analysis, data_export, market_data, 
    investment_analysis, lead_import, lead_management, appointment_scheduling, 
    followup_management, lead_nurturing, data_processor, authentication,
    production_launch
)
from ..simulation import simulation_api
from ..training import simple_training_api
from ..core.database import engine, Base, create_tables
from ..core.security_config import get_security_config

# Get security configuration
security_config = get_security_config()

# Configure logging
logging.basicConfig(
    level=getattr(logging, security_config.settings.SECURITY_LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Custom security middleware."""
    
    async def dispatch(self, request: Request, call_next):
        # Add security headers
        response = await call_next(request)
        
        # Apply security headers
        headers = security_config.get_security_headers()
        for header, value in headers.items():
            response.headers[header] = value
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app, calls_per_minute: int = 100):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries
        self.clients = {
            ip: times for ip, times in self.clients.items()
            if any(t > current_time - 60 for t in times)
        }
        
        # Check rate limit
        if client_ip in self.clients:
            recent_calls = [t for t in self.clients[client_ip] if t > current_time - 60]
            if len(recent_calls) >= self.calls_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            self.clients[client_ip] = recent_calls + [current_time]
        else:
            self.clients[client_ip] = [current_time]
        
        return await call_next(request)

# Create database tables (only if not in test mode)
import os
if not os.getenv("TESTING"):
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")

# Create FastAPI app
app = FastAPI(
    title="Real Estate Empire - Property Analysis API",
    description="Comprehensive property analysis and investment evaluation API with Enterprise Security",
    version="1.0.0",
    docs_url="/docs" if not security_config.is_production() else None,
    redoc_url="/redoc" if not security_config.is_production() else None
)

# Add security middleware
app.add_middleware(SecurityMiddleware)

# Add rate limiting
rate_limit_config = security_config.get_rate_limit_config()
app.add_middleware(RateLimitMiddleware, calls_per_minute=rate_limit_config["per_minute"])

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=security_config.settings.SECRET_KEY,
    max_age=security_config.settings.SESSION_TIMEOUT_MINUTES * 60,
    same_site="strict",
    https_only=security_config.settings.FORCE_HTTPS
)

# Add trusted host middleware for production
if security_config.is_production():
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
    )

# Add CORS middleware
cors_config = security_config.get_cors_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config["allow_origins"],
    allow_credentials=cors_config["allow_credentials"],
    allow_methods=cors_config["allow_methods"],
    allow_headers=cors_config["allow_headers"],
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting Real Estate Empire API")
    logger.info(f"Security configuration loaded - Production: {security_config.is_production()}")
    logger.info(f"HTTPS enforced: {security_config.settings.FORCE_HTTPS}")
    logger.info(f"MFA required: {security_config.settings.REQUIRE_MFA}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Real Estate Empire API")

# Include authentication router first
app.include_router(authentication.router)

# Include other routers
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

app.include_router(
    production_launch.router,
    prefix="/api/v1",
    tags=["Production Launch"]
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Real Estate Empire Property Analysis API",
        "version": "1.0.0",
        "docs": "/docs" if not security_config.is_production() else None,
        "security": {
            "https_enforced": security_config.settings.FORCE_HTTPS,
            "mfa_available": True,
            "audit_enabled": security_config.settings.ENABLE_AUDIT_TRAIL
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "security_status": "active"
    }

@app.get("/security/config")
async def security_config_info():
    """Get public security configuration information."""
    return {
        "password_policy": security_config.get_password_policy(),
        "session_timeout": security_config.settings.SESSION_TIMEOUT_MINUTES,
        "mfa_required": security_config.settings.REQUIRE_MFA,
        "rate_limits": security_config.get_rate_limit_config(),
        "data_protection": {
            "gdpr_compliant": security_config.settings.GDPR_COMPLIANCE,
            "ccpa_compliant": security_config.settings.CCPA_COMPLIANCE
        }
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with security logging"""
    
    # Log security-relevant errors
    if exc.status_code in [401, 403, 429]:
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(
            f"Security event - Status: {exc.status_code}, "
            f"IP: {client_ip}, "
            f"Path: {request.url.path}, "
            f"Detail: {exc.detail}"
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": time.time()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": time.time()
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    # Run with security settings
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="ssl/key.pem" if security_config.settings.FORCE_HTTPS else None,
        ssl_certfile="ssl/cert.pem" if security_config.settings.FORCE_HTTPS else None,
        log_level=security_config.settings.SECURITY_LOG_LEVEL.lower(),
        access_log=True
    )