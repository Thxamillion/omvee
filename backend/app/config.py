from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: Optional[str] = None  # For admin operations

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # AI Services
    openrouter_api_key: str
    replicate_api_token: str
    openai_api_key: str

    # App
    environment: str = "development"
    debug: bool = True
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    class Config:
        env_file = ".env"


settings = Settings()