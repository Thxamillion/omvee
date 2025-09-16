from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import health, projects, uploads

app = FastAPI(
    title="OMVEE API",
    description="AI-powered music video generation platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(uploads.router, prefix="/api", tags=["uploads"])


@app.get("/")
async def root():
    return {
        "message": "OMVEE API - Supabase Edition",
        "version": "1.0.0",
        "environment": settings.environment,
        "features": ["supabase", "redis", "celery", "ai-pipeline"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=settings.debug)