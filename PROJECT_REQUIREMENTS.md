# OMVEE - AI Music Video Generator

## Project Overview
OMVEE is an AI-powered music video generation platform that transforms songs and lyrics into cinematic music videos through automated scene selection, prompt generation, and video creation.

## Workflow
1. **Audio Ingest**: Upload song/audio file
2. **Transcription**: Extract lyrics from audio
3. **Scene Analysis**: AI analyzes lyrics and selects key moments/themes for scenes
4. **Prompt Generation**: AI creates detailed visual prompts for each selected scene
5. **Image Generation**: Generate static images from AI prompts
6. **Video Clip Creation**: Convert static images to animated video clips
7. **User Review & Approval**: User reviews and approves scenes and video clips
8. **Final Assembly**: Stitch approved video clips into complete music video

## Technical Stack

### Backend
- **Framework**: FastAPI + Pydantic v2
- **Database**: Supabase (PostgreSQL) + SQLAlchemy 2.0 + Alembic
- **Queue**: Celery + Redis
- **Real-time Updates**: Server-Sent Events (SSE) + Redis Pub/Sub
- **Storage**: S3-compatible storage with presigned uploads
- **Environment**: Docker + docker-compose

### AI Services
- **LLM**: DeepSeek via OpenRouter API
  - Scene selection from lyrics analysis
  - Visual prompt generation
- **Image Generation**: Flux via Replicate API
  - Static image creation from prompts
  - 16:9 aspect ratio (configurable)
  - 1 image per scene initially
- **Transcription**: OpenAI Whisper API (with Replicate as backup option)
- **Video Generation**: Replicate image-to-video models (TBD - Stable Video Diffusion or similar)

## Data Model

### Core Tables
```sql
projects(
  id UUID PRIMARY KEY,
  name VARCHAR,
  audio_path VARCHAR,
  transcript_text TEXT,
  status VARCHAR, -- 'uploading', 'transcribing', 'analyzing', 'generating', 'reviewing', 'complete'
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

selected_scenes(
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  lyric_excerpt TEXT,
  theme VARCHAR,
  ai_reasoning TEXT,
  order_idx INTEGER,
  start_time_s FLOAT, -- sync with audio
  end_time_s FLOAT
)

scene_prompts(
  id UUID PRIMARY KEY,
  scene_id UUID REFERENCES selected_scenes(id),
  prompt_json JSONB, -- structured prompt data
  generated_by_model VARCHAR,
  created_at TIMESTAMP
)

generated_images(
  id UUID PRIMARY KEY,
  scene_id UUID REFERENCES selected_scenes(id),
  prompt_id UUID REFERENCES scene_prompts(id),
  image_url VARCHAR,
  replicate_prediction_id VARCHAR,
  status VARCHAR, -- 'generating', 'completed', 'failed'
  created_at TIMESTAMP
)

video_clips(
  id UUID PRIMARY KEY,
  image_id UUID REFERENCES generated_images(id),
  video_url VARCHAR,
  duration_s FLOAT,
  replicate_prediction_id VARCHAR,
  status VARCHAR, -- 'generating', 'completed', 'failed'
  created_at TIMESTAMP
)

user_approvals(
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  scene_id UUID REFERENCES selected_scenes(id),
  video_clip_id UUID REFERENCES video_clips(id),
  approved BOOLEAN,
  notes TEXT,
  created_at TIMESTAMP
)

final_videos(
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  video_path VARCHAR,
  status VARCHAR, -- 'assembling', 'completed', 'failed'
  created_at TIMESTAMP
)

jobs(
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  type VARCHAR, -- 'transcribe', 'analyze_scenes', 'generate_prompts', 'generate_images', 'generate_clips', 'assemble_video'
  status VARCHAR, -- 'pending', 'running', 'completed', 'failed'
  progress INTEGER, -- 0-100
  payload_json JSONB,
  result_json JSONB,
  error TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
```

## API Endpoints

### Projects
- `POST /api/projects` - Create new project
- `GET /api/projects` - List projects
- `GET /api/projects/{id}` - Get project details

### Audio & Transcription
- `POST /api/projects/{id}/upload-audio` - Upload audio file
- `POST /api/projects/{id}/transcribe` - Start transcription job

### Scene Analysis & Generation
- `POST /api/projects/{id}/analyze-scenes` - AI scene selection from lyrics
- `GET /api/projects/{id}/scenes` - Get selected scenes
- `PUT /api/projects/{id}/scenes` - Update/modify scenes

### Prompt & Image Generation
- `POST /api/projects/{id}/generate-prompts` - AI prompt generation for scenes
- `POST /api/projects/{id}/generate-images` - Generate images from prompts
- `GET /api/projects/{id}/images` - Get generated images

### Video Generation
- `POST /api/projects/{id}/generate-clips` - Convert images to video clips
- `GET /api/projects/{id}/clips` - Get video clips

### User Review
- `PUT /api/projects/{id}/approvals` - Submit approvals for scenes/clips
- `GET /api/projects/{id}/approvals` - Get approval status

### Final Assembly
- `POST /api/projects/{id}/assemble-video` - Create final music video
- `GET /api/projects/{id}/final-videos` - Get final video status

### Real-time Updates
- `GET /api/projects/{id}/stream` - SSE endpoint for live job updates

### Utilities
- `POST /api/uploads/presign` - Get presigned upload URLs for S3

## File Storage Structure
```
/projects/{project_id}/
  ├── audio/
  │   └── source.{ext}                    # uploaded audio
  ├── transcripts/
  │   └── lyrics.json                     # extracted lyrics
  ├── scenes/
  │   └── analysis.json                   # selected scenes + reasoning
  ├── prompts/
  │   └── {scene_id}.json                 # generated prompts
  ├── images/
  │   └── {scene_id}_{image_id}.png       # generated images
  ├── clips/
  │   └── {scene_id}_{clip_id}.mp4        # generated video clips
  └── final/
      └── {video_id}.mp4                  # assembled music video
```

## Development Environment

### Docker Services
- **redis**: Redis for Celery broker and pub/sub
- **app**: FastAPI application
- **worker**: Celery worker processes

### Environment Variables
```env
DATABASE_URL=postgresql://postgres:[password]@[project-ref].supabase.co:5432/postgres
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_ANON_KEY=eyJ...
REDIS_URL=redis://redis:6379/0
OPENROUTER_API_KEY=sk_or_...
REPLICATE_API_TOKEN=r8_...
OPENAI_API_KEY=sk-...
S3_BUCKET=omvee-storage
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
```

## Development Phases

### Phase 1: Core Infrastructure (Day 1)
- FastAPI app setup with Docker
- Supabase database connection and models
- Alembic migrations setup
- Basic CRUD endpoints for projects
- Redis + SSE streaming setup
- File upload with S3 presigned URLs

### Phase 2: AI Integration (Day 2)
- OpenRouter integration for DeepSeek
- Replicate integration for Flux
- Transcription service (OpenAI Whisper)
- Celery workers for async processing

### Phase 3: Scene Analysis Pipeline (Day 3)
- Lyrics analysis and scene selection
- Prompt generation workflow
- Image generation pipeline
- Progress tracking and error handling

### Phase 4: Video Generation (Day 4)
- Image-to-video conversion
- User approval interface (API only)
- Final video assembly
- End-to-end testing

## Success Criteria
- [ ] Upload audio file and extract lyrics
- [ ] AI automatically selects 3-5 key scenes from lyrics
- [ ] AI generates visual prompts for each scene
- [ ] Generate high-quality images for each prompt
- [ ] Convert images to short video clips (2-5 seconds each)
- [ ] User can review and approve/reject scenes and clips
- [ ] Assemble approved clips into final music video synced to audio
- [ ] Real-time progress updates throughout the process
- [ ] Complete workflow takes < 10 minutes for a 3-minute song