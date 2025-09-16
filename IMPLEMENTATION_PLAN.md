# OMVEE Implementation Plan

## Overview
4-day backend development plan to build the complete AI music video generation pipeline. Each day builds on the previous, with working features at each milestone.

---

## Day 1: Foundation & Infrastructure

### Morning (3-4 hours)
**Goal**: Basic FastAPI app with Supabase connection and core models

#### 1.1 Project Structure Setup
```
omvee/
  backend/
    app/
      __init__.py
      main.py              # FastAPI app entry point
      config.py            # Environment configuration
      database.py          # Supabase connection
      models.py            # SQLAlchemy models
      schemas.py           # Pydantic schemas
      deps.py              # Dependencies (DB session, etc.)
      routers/
        __init__.py
        projects.py        # Project CRUD
        health.py          # Health check
      services/
        __init__.py
        storage.py         # S3 presigned uploads
      workers/
        __init__.py
        celery_app.py      # Celery setup
      utils/
        __init__.py
        events.py          # Redis pub/sub helpers
    alembic/
      env.py
      script.py.mako
      versions/
    docker-compose.yml
    Dockerfile
    requirements.txt
    .env.example
    alembic.ini
```

#### 1.2 Core Setup
- [ ] FastAPI app with CORS and basic middleware
- [ ] Supabase connection via SQLAlchemy
- [ ] Alembic configuration for migrations
- [ ] Docker setup (Redis only, since Supabase is hosted)
- [ ] Environment configuration management

#### 1.3 Database Models
All tables from requirements:
- [ ] `projects` table
- [ ] `selected_scenes` table
- [ ] `scene_prompts` table
- [ ] `generated_images` table
- [ ] `video_clips` table
- [ ] `user_approvals` table
- [ ] `final_videos` table
- [ ] `jobs` table

#### 1.4 Pydantic Schemas
- [ ] Request/response schemas for all models
- [ ] Proper validation and serialization
- [ ] OpenAPI documentation ready

### Afternoon (2-3 hours)
**Goal**: Basic API endpoints and file upload working

#### 1.5 Basic API Endpoints
- [ ] `POST /api/projects` - Create project
- [ ] `GET /api/projects` - List projects
- [ ] `GET /api/projects/{id}` - Get project details
- [ ] `GET /health` - Health check

#### 1.6 File Upload Infrastructure
- [ ] S3 presigned upload setup
- [ ] `POST /api/uploads/presign` endpoint
- [ ] Basic file validation

#### 1.7 Testing & Documentation
- [ ] OpenAPI docs at `/docs` working
- [ ] Basic pytest setup
- [ ] Manual testing of all endpoints

**Day 1 Deliverable**: Working FastAPI app with project CRUD and file uploads

---

## Day 2: Redis, Jobs & AI Service Integration

### Morning (3-4 hours)
**Goal**: Celery workers and real-time updates working

#### 2.1 Redis & Celery Setup
- [ ] Redis pub/sub utilities
- [ ] Celery worker configuration
- [ ] Job model and management
- [ ] Basic task templates

#### 2.2 Server-Sent Events (SSE)
- [ ] `GET /api/projects/{id}/stream` endpoint
- [ ] Redis pub/sub integration
- [ ] Real-time job progress updates
- [ ] Keep-alive and error handling

#### 2.3 AI Service Integrations
- [ ] OpenRouter client for DeepSeek
- [ ] Replicate client for Flux
- [ ] OpenAI client for Whisper
- [ ] Error handling and retries

### Afternoon (2-3 hours)
**Goal**: First AI pipeline working (transcription)

#### 2.4 Transcription Pipeline
- [ ] `POST /api/projects/{id}/transcribe` endpoint
- [ ] Celery task for audio transcription
- [ ] Progress tracking and error handling
- [ ] Store results in database and S3

#### 2.5 Mock Tasks for Development
- [ ] Mock scene analysis task (returns dummy scenes)
- [ ] Mock prompt generation task
- [ ] Mock image generation task
- [ ] All with proper progress updates

**Day 2 Deliverable**: Real-time job system with working transcription

---

## Day 3: Scene Analysis & Image Generation Pipeline

### Morning (3-4 hours)
**Goal**: Complete scene analysis and prompt generation

#### 3.1 Scene Analysis Pipeline
- [ ] `POST /api/projects/{id}/analyze-scenes` endpoint
- [ ] DeepSeek integration for lyric analysis
- [ ] Structured scene selection with reasoning
- [ ] Time alignment with audio
- [ ] Store scenes in database

#### 3.2 Prompt Generation Pipeline
- [ ] `POST /api/projects/{id}/generate-prompts` endpoint
- [ ] DeepSeek integration for visual prompt creation
- [ ] Structured prompt format for image generation
- [ ] Scene-to-prompt mapping

#### 3.3 Scene Management APIs
- [ ] `GET /api/projects/{id}/scenes` - Get scenes
- [ ] `PUT /api/projects/{id}/scenes` - Update scenes
- [ ] Scene editing and reordering

### Afternoon (2-3 hours)
**Goal**: Image generation working end-to-end

#### 3.4 Image Generation Pipeline
- [ ] `POST /api/projects/{id}/generate-images` endpoint
- [ ] Replicate Flux integration
- [ ] Async generation with webhooks
- [ ] Image storage and metadata tracking
- [ ] Error handling and retries

#### 3.5 Image Management APIs
- [ ] `GET /api/projects/{id}/images` - Get generated images
- [ ] Image status tracking
- [ ] Regeneration capabilities

**Day 3 Deliverable**: Complete pipeline from lyrics → scenes → prompts → images

---

## Day 4: Video Generation & Final Assembly

### Morning (3-4 hours)
**Goal**: Video clip generation working

#### 4.1 Image-to-Video Pipeline
- [ ] Research best Replicate model for image-to-video
- [ ] `POST /api/projects/{id}/generate-clips` endpoint
- [ ] Video generation from approved images
- [ ] Clip duration and quality settings
- [ ] Progress tracking and storage

#### 4.2 Video Management APIs
- [ ] `GET /api/projects/{id}/clips` - Get video clips
- [ ] Clip status and metadata
- [ ] Preview and download endpoints

### Afternoon (2-3 hours)
**Goal**: User approval system and final assembly

#### 4.3 Approval System
- [ ] `PUT /api/projects/{id}/approvals` - Submit approvals
- [ ] `GET /api/projects/{id}/approvals` - Get approval status
- [ ] Bulk approval operations
- [ ] Approval history tracking

#### 4.4 Final Video Assembly
- [ ] `POST /api/projects/{id}/assemble-video` endpoint
- [ ] FFmpeg integration for video stitching
- [ ] Audio synchronization
- [ ] Final output generation

#### 4.5 Final Testing & Polish
- [ ] End-to-end workflow testing
- [ ] Error handling improvements
- [ ] Performance optimization
- [ ] Documentation updates

**Day 4 Deliverable**: Complete working backend with full pipeline

---

## Technical Implementation Details

### Error Handling Strategy
- **Retry Logic**: Exponential backoff for AI service calls
- **Partial Failures**: Continue pipeline even if some images fail
- **User Feedback**: Clear error messages via SSE
- **Graceful Degradation**: Fallback options for each service

### Performance Considerations
- **Async Everything**: All AI calls are async via Celery
- **Parallel Processing**: Generate multiple images simultaneously
- **Caching**: Cache API responses where appropriate
- **Batch Operations**: Bulk database operations for efficiency

### Monitoring & Observability
- **Job Status**: Detailed tracking in jobs table
- **Progress Updates**: Real-time progress via SSE
- **Error Logging**: Comprehensive error tracking
- **Performance Metrics**: Track API response times

### Security & Validation
- **Input Validation**: Strict Pydantic validation
- **File Validation**: Audio format and size limits
- **Rate Limiting**: Prevent API abuse
- **Secure Storage**: Presigned URLs for direct upload

---

## Development Workflow

### Each Day Structure
1. **Morning Standup** (15 min): Review previous day, plan current day
2. **Implementation** (3-4 hours): Core development work
3. **Testing** (30 min): Manual testing of new features
4. **Integration** (30 min): Ensure everything works together
5. **Afternoon Session** (2-3 hours): Continue implementation
6. **End-of-Day Review** (15 min): Demo working features, plan next day

### Testing Strategy
- **Unit Tests**: Critical business logic
- **Integration Tests**: API endpoints
- **Manual Testing**: Full workflows
- **Load Testing**: AI service integration

### Git Workflow
- **Feature Branches**: One branch per major feature
- **Daily Commits**: End each day with working commit
- **Clear Messages**: Descriptive commit messages
- **Documentation**: Update docs with each feature

---

## Success Metrics

### Day 1 Success
- [ ] FastAPI app running on localhost
- [ ] Database connection working
- [ ] Can create and list projects
- [ ] File upload working

### Day 2 Success
- [ ] Real-time updates working via SSE
- [ ] Can transcribe audio file
- [ ] Job progress visible in real-time
- [ ] All AI services connected

### Day 3 Success
- [ ] Complete scene analysis working
- [ ] Images generating from prompts
- [ ] Can see generated images in API
- [ ] Pipeline works end-to-end

### Day 4 Success
- [ ] Video clips generating from images
- [ ] User can approve/reject content
- [ ] Final video assembly working
- [ ] Complete music video output

---

## Risk Mitigation

### Technical Risks
- **AI Service Downtime**: Multiple fallback providers
- **Rate Limits**: Implement queuing and throttling
- **Large Files**: Streaming uploads and processing
- **Complex FFmpeg**: Simple operations first, complex later

### Timeline Risks
- **Scope Creep**: Stick to MVP features only
- **Integration Issues**: Test integrations early
- **Performance Problems**: Profile and optimize daily
- **Blocked Dependencies**: Have backup plans

This plan ensures we have a working system at the end of each day, with each day building incrementally toward the final goal.