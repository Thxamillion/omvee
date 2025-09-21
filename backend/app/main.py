from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import health, projects, uploads, artists, image_generation, video_generation, transcription, scenes

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
app.include_router(artists.router, prefix="/api", tags=["artists"])
app.include_router(image_generation.router, prefix="/api", tags=["image-generation"])
app.include_router(video_generation.router, prefix="/api", tags=["video-generation"])
app.include_router(transcription.router, prefix="/api", tags=["transcription"])
app.include_router(scenes.router, prefix="/api", tags=["scenes"])


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