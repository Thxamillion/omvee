from pydantic_settings import BaseSettings
from typing import Optional


class ModelConfig:
    """AI Model configuration - centralized model IDs"""
    # Image Generation
    image_model: str = "minimax/image-01:47ca89ad46682c1dd0ca335601cd7ea2eb10fb94ce4e0a5abafa7e74f23ae7b6"

    # Video Generation
    video_model: str = "bytedance/seedance-1-lite:5b618302c710fbcf00365dc75133537b5deed8a95dccaf983215559bb31fc943"

    # Scene Selection & Prompt Generation
    scene_selection_model: str = "deepseek/deepseek-chat"


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
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:8000"]

    class Config:
        env_file = ".env"


settings = Settings()