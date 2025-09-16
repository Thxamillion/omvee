from fastapi import APIRouter
import redis
from app.config import settings
from app.services.supabase import supabase_service
from app import models_pydantic as schemas

router = APIRouter()


@router.get("/health", response_model=schemas.HealthCheck)
async def health_check():
    """Health check endpoint to verify Supabase and redis connectivity."""

    # Check Supabase
    try:
        # Simple query to test connection
        result = supabase_service.client.table('projects').select('id').limit(1).execute()
        supabase_status = "healthy"
    except Exception as e:
        supabase_status = f"unhealthy: {str(e)}"

    # Check Redis
    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    overall_status = "healthy" if supabase_status == "healthy" and redis_status == "healthy" else "unhealthy"

    return schemas.HealthCheck(
        status=overall_status,
        supabase=supabase_status,
        redis=redis_status,
        environment=settings.environment
    )