# OMVEE - AI Music Video Generator

## Overview

OMVEE is an AI-powered music video generation platform that transforms songs and lyrics into cinematic music videos through automated scene selection, prompt generation, and video creation.

## Workflow

1. **Audio Ingest**: Upload song/audio file
2. **Transcription**: Extract lyrics from audio
3. **Scene Analysis**: AI analyzes lyrics and selects key moments/themes for scenes
4. **Prompt Generation**: AI creates detailed visual prompts for each selected scene
5. **Image Generation**: Generate static images from AI prompts using Flux
6. **Video Clip Creation**: Convert static images to animated video clips
7. **User Review & Approval**: User reviews and approves scenes and video clips
8. **Final Assembly**: Stitch approved video clips into complete music video

## Technical Stack

### Backend
- **Framework**: FastAPI + Pydantic v2
- **Database**: Supabase (PostgreSQL) + direct client integration
- **Queue**: Celery + Redis
- **Real-time Updates**: Server-Sent Events (SSE) + Redis Pub/Sub
- **Storage**: Supabase Storage with presigned uploads
- **Environment**: Docker + docker-compose

### AI Services
- **LLM**: DeepSeek via OpenRouter API (scene selection & prompt generation)
- **Image Generation**: Flux via Replicate API (16:9 aspect ratio)
- **Transcription**: OpenAI Whisper API
- **Video Generation**: Replicate image-to-video models

## Project Structure

```
omvee/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── config.py          # Environment configuration
│   │   ├── models_pydantic.py # Pydantic models for type safety
│   │   ├── routers/           # API endpoints
│   │   ├── services/          # Supabase and external service clients
│   │   ├── workers/           # Celery async job processors
│   │   └── utils/             # Utility functions
│   ├── migrations/            # Database migration files
│   ├── docker-compose.yml     # Redis service
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment variables
├── PROJECT_REQUIREMENTS.md    # Detailed project specification
├── IMPLEMENTATION_PLAN.md     # 4-day development plan
└── README.md                  # This file
```

## Current Status

✅ **Complete Backend Foundation**
- Supabase database with full schema (8 tables)
- FastAPI API with all CRUD endpoints
- Real-time job tracking infrastructure
- File upload system with Supabase Storage
- Sample data for testing

✅ **Working API Endpoints**
- Projects management
- Scene analysis results
- Job tracking and progress
- Health monitoring

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js v20+ (for development tools)
- Docker (for Redis)
- Supabase account

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/thxamillion/omvee.git
   cd omvee
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   # Fill in your Supabase and API credentials
   ```

3. **Start Services**
   ```bash
   docker-compose up -d redis
   uvicorn app.main:app --reload
   ```

4. **Visit API Documentation**
   - API docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

## API Documentation

The API is fully documented with OpenAPI/Swagger at `/docs` when running the server.

### Key Endpoints
- `GET /api/projects` - List all projects
- `POST /api/projects` - Create new project
- `GET /api/projects/{id}/scenes` - Get AI-selected scenes
- `GET /api/projects/{id}/jobs` - Track processing jobs
- `GET /health` - System health check

## Development

### Database Schema
The complete database schema includes:
- **projects**: Main project entities
- **selected_scenes**: AI-selected lyric moments
- **scene_prompts**: AI-generated visual prompts
- **generated_images**: Flux-generated images
- **video_clips**: Image-to-video conversions
- **user_approvals**: Review and approval workflow
- **final_videos**: Assembled music videos
- **jobs**: Async job tracking

### Next Steps
- AI service integrations (OpenRouter, Replicate, OpenAI)
- Async job processing with Celery workers
- Image generation pipeline
- Video creation workflow
- Frontend development

## Contributing

This project follows a structured development approach with detailed planning and implementation phases. See `IMPLEMENTATION_PLAN.md` for the complete development roadmap.

## License

[Add your license here]