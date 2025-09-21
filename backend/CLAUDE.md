# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OMVEE is a production-ready AI-powered music video generation platform that transforms audio files into professional music videos through a sophisticated 5-stage AI pipeline: **Audio → Transcription → Scene Selection → Visual Prompts → Image Generation → Video Generation**.

## Architecture

**Framework**: FastAPI + Pydantic v2 with comprehensive type validation
**Database**: Supabase (managed PostgreSQL) with real-time capabilities
**Storage**: Supabase Storage with presigned URL uploads
**Queue**: Celery + Redis for async job processing
**AI Pipeline**: OpenAI Whisper → OpenRouter (DeepSeek) → Replicate (MiniMax + ByteDance)

## AI Pipeline Flow

The core system implements a sophisticated transformation pipeline:

1. **Audio Transcription** (`app/services/whisper.py`) - OpenAI Whisper with precise timestamps (~$0.006/minute)
2. **Scene Selection** (`app/services/openrouter.py::select_scenes()`) - DeepSeek analyzes lyrics for 15-20 cinematic scenes (~$0.27/1M tokens)
3. **Visual Prompt Generation** (`app/services/openrouter.py::generate_visual_prompts()`) - Creates detailed image prompts with artist reference integration
4. **Image Generation** (`app/services/image_generation.py`) - MiniMax Image-01 produces 16:9 music video frames (~$0.030/image)
5. **Video Generation** (`app/services/video_generation.py`) - ByteDance SeeDance-1-Lite creates 3-12 second clips with motion

## Key Commands

### Development
```bash
# Start development server
uvicorn app.main:app --reload

# Install dependencies
pip install -r requirements.txt

# Environment setup (required)
cp .env.example .env
# Configure: OPENAI_API_KEY, OPENROUTER_API_KEY, REPLICATE_API_TOKEN, SUPABASE_*
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test types
pytest -m unit          # Fast tests, no external dependencies
pytest -m integration   # Real service integration tests
pytest -m external_api  # Live API testing
pytest -m supabase     # Database integration tests

# Run single test file
pytest tests/test_services/test_openrouter.py

# Generate comprehensive test reports
./generate_test_docs.sh

# Run with coverage analysis
pytest --cov=app
```

## Service Layer Architecture

All AI services follow a consistent async pattern with error handling, cost tracking, and validation:

- **`OpenRouterService`** - Scene selection and prompt generation (700+ lines, handles DeepSeek integration)
- **`ImageGenerationService`** - Replicate MiniMax Image-01 integration with reference photo support
- **`VideoGenerationService`** - Replicate ByteDance SeeDance integration for image-to-video
- **`WhisperService`** - OpenAI audio transcription with format validation
- **`ArtistService`** - Artist management with reference image collections *(Note: Currently sync, needs async conversion)*

## Configuration Management

Centralized model configuration in `app/config.py`:
```python
class ModelConfig:
    image_model: str = "minimax/image-01:47ca89ad..."
    video_model: str = "bytedance/seedance-1-lite:5b618302..."
    scene_selection_model: str = "deepseek/deepseek-chat"
```

## Database Schema

Comprehensive workflow tracking with UUID primary keys and JSONB storage:
- **`projects`** - Main project entities with status tracking
- **`artists`** - Artist profiles with reference image collections
- **`selected_scenes`** - AI-selected lyric moments with precise timing
- **`scene_prompts`** - Generated visual prompts (JSONB storage)
- **`generated_images`** - Image generation results with Replicate tracking
- **`video_clips`** - Video generation metadata and URLs
- **`jobs`** - Async job processing with progress monitoring

## Testing Strategy

The codebase implements comprehensive testing across multiple levels:

**Test Structure**: `tests/{test_services,test_integration,test_endpoints}/`
**Shared Fixtures**: `tests/conftest.py` provides mocks and test data
**Real API Testing**: Integration tests use actual external APIs for confidence
**HTML Reports**: Generated in `test_report.html` with coverage metrics

## Current Status

**✅ Production Ready**: Complete AI pipeline functional with all external integrations working
**✅ Full Test Coverage**: Unit, integration, and external API tests
**✅ Type Safety**: Comprehensive Pydantic models throughout
**✅ Error Handling**: Robust error handling with detailed logging

## Frontend Integration

**API Documentation**: Available at `/docs` (OpenAPI/Swagger)
**Endpoints**: RESTful design with `/api/{projects,artists,uploads,image-generation,video-generation}`
**File Uploads**: Presigned URL system via Supabase Storage
**Type Safety**: All endpoints use strongly-typed Pydantic schemas

## Known Architecture Notes

- **Artist Service Inconsistency**: Currently sync while other services are async (needs conversion)
- **Common Utilities**: Some code duplication in logging/error handling across services
- **Pipeline Orchestration**: Individual endpoints exist, but full pipeline endpoint needed for frontend
- **Model Configuration**: Centralized in `ModelConfig` but could be extended for environment-specific models

See `BACKEND_CLEANUP_PLAN.md` for detailed production readiness roadmap.