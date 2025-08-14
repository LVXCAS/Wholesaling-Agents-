from fastapi import FastAPI
from app.core.config import settings
from app.api.endpoints.properties import router as properties_router # Import the specific router
# Placeholder for future analysis router
# from app.api.endpoints.analysis import router as analysis_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

@app.get("/", tags=["Root"])
async def read_root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": "1.0", # Or some other version identifier
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

# Include API routers
app.include_router(properties_router, prefix=f"{settings.API_V1_STR}/properties", tags=["Properties"])
# Example for analysis router:
# app.include_router(analysis_router, prefix=f"{settings.API_V1_STR}/analysis", tags=["Analysis"])

if __name__ == "__main__":
    # This block is for running with ''python app/main.py'' directly
    # Typically, Uvicorn is used from the command line: uvicorn app.main:app --reload
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
