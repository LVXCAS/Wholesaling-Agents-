from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from typing import Dict, Any

app = FastAPI(
    title="Real Estate Empire API Gateway",
    description="Central API Gateway for Real Estate Empire microservices",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
SERVICES = {
    "auth": "http://auth-service:8001",
    "property": "http://property-service:8002",
    "lead": "http://lead-service:8003",
    "outreach": "http://outreach-service:8004",
    "transaction": "http://transaction-service:8005",
    "portfolio": "http://portfolio-service:8006",
    "reporting": "http://reporting-service:8007",
    "ml": "http://ml-service:8008",
}

@app.get("/")
async def root():
    return {"message": "Real Estate Empire API Gateway", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancer"""
    return {"status": "healthy", "services": list(SERVICES.keys())}

@app.get("/services/status")
async def services_status():
    """Check status of all microservices"""
    status = {}
    async with httpx.AsyncClient() as client:
        for service_name, service_url in SERVICES.items():
            try:
                response = await client.get(f"{service_url}/health", timeout=5.0)
                status[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds()
                }
            except Exception as e:
                status[service_name] = {
                    "status": "unreachable",
                    "error": str(e)
                }
    return status

# Route proxy function
async def proxy_request(service: str, path: str, method: str = "GET", **kwargs):
    """Proxy requests to appropriate microservice"""
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service {service} not found")
    
    service_url = SERVICES[service]
    url = f"{service_url}{path}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(method, url, **kwargs)
            return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Service {service} unavailable: {str(e)}")

# Authentication routes
@app.post("/auth/login")
async def login(credentials: Dict[str, Any]):
    return await proxy_request("auth", "/login", "POST", json=credentials)

@app.post("/auth/register")
async def register(user_data: Dict[str, Any]):
    return await proxy_request("auth", "/register", "POST", json=user_data)

# Property analysis routes
@app.get("/properties/{property_id}")
async def get_property(property_id: str):
    return await proxy_request("property", f"/properties/{property_id}")

@app.post("/properties/analyze")
async def analyze_property(property_data: Dict[str, Any]):
    return await proxy_request("property", "/analyze", "POST", json=property_data)

# Lead management routes
@app.get("/leads")
async def get_leads():
    return await proxy_request("lead", "/leads")

@app.post("/leads")
async def create_lead(lead_data: Dict[str, Any]):
    return await proxy_request("lead", "/leads", "POST", json=lead_data)

# Outreach routes
@app.post("/outreach/campaigns")
async def create_campaign(campaign_data: Dict[str, Any]):
    return await proxy_request("outreach", "/campaigns", "POST", json=campaign_data)

# Transaction routes
@app.get("/transactions")
async def get_transactions():
    return await proxy_request("transaction", "/transactions")

# Portfolio routes
@app.get("/portfolio")
async def get_portfolio():
    return await proxy_request("portfolio", "/portfolio")

# Reporting routes
@app.get("/reports/{report_type}")
async def get_report(report_type: str):
    return await proxy_request("reporting", f"/reports/{report_type}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)