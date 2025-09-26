# Celery Migration Plan: Fix Stuck Job Issues

## Problem Summary

The OMVEE backend currently uses **FastAPI BackgroundTasks** for all long-running AI processing jobs (transcription, scene generation, image generation, video generation). This causes critical issues:

### ❌ Current Issues
- **Jobs get stuck permanently** when server restarts
- **No job persistence** - tasks lost from memory
- **No retry mechanism** for failed jobs
- **No monitoring/observability** of job progress
- **Race conditions** between job DB records and actual task execution

### ✅ What Should Happen
- Jobs should survive server restarts
- Failed jobs should retry automatically
- Job status should be observable and manageable
- Robust error handling and logging

## Current Architecture Problems

### Files Using Broken FastAPI BackgroundTasks:
```
/app/routers/transcription.py:209    - Audio transcription
/app/routers/scenes.py:362          - Scene selection
/app/routers/scenes.py:448          - Visual prompt generation
/app/routers/image_generation.py:4  - Image generation (likely)
```

### Example of Broken Pattern:
```python
# BROKEN: FastAPI BackgroundTasks
background_tasks.add_task(transcription_background_task, project_id, audio_url, job_id)
# ❌ Lost on server restart
# ❌ No retry on failure
# ❌ No monitoring
```

## Migration Strategy

### Phase 1: Infrastructure Setup (2-4 hours)

1. **Create Missing Tasks File**
   ```bash
   touch app/workers/tasks.py
   ```

2. **Start Redis Server**
   ```bash
   redis-server
   # OR using Docker:
   docker run -d -p 6379:6379 redis:alpine
   ```

3. **Define Celery Tasks**
   ```python
   # app/workers/tasks.py
   from app.workers.celery_app import celery_app
   from app.services.whisper import WhisperService
   from app.services.supabase import supabase_service

   @celery_app.task(bind=True, max_retries=3)
   def transcribe_audio_task(self, project_id: str, audio_url: str, job_id: str):
       try:
           # Move transcription_background_task logic here
           # Add proper error handling and retries
       except Exception as exc:
           # Exponential backoff retry
           raise self.retry(exc=exc, countdown=60, max_retries=3)
   ```

4. **Start Celery Worker**
   ```bash
   celery -A app.workers.celery_app worker --loglevel=info
   ```

### Phase 2: Migrate Individual Job Types (1-2 days)

#### A. Transcription Jobs (`transcription.py`)
```python
# OLD:
background_tasks.add_task(transcription_background_task, project_id, audio_url, job_id)

# NEW:
from app.workers.tasks import transcribe_audio_task
transcribe_audio_task.delay(project_id, audio_url, job_id)
```

#### B. Scene Generation Jobs (`scenes.py`)
```python
# OLD:
background_tasks.add_task(scene_generation_background_task, ...)

# NEW:
from app.workers.tasks import generate_scenes_task
generate_scenes_task.delay(project_id, job_id)
```

#### C. Visual Prompt Jobs (`scenes.py`)
```python
# OLD:
background_tasks.add_task(visual_prompt_generation_task, ...)

# NEW:
from app.workers.tasks import generate_visual_prompts_task
generate_visual_prompts_task.delay(project_id, job_id)
```

#### D. Image/Video Generation Jobs
- Similar pattern for remaining job types

### Phase 3: Enhanced Job Management (1 day)

1. **Job Status Monitoring**
   ```python
   @celery_app.task(bind=True)
   def long_running_task(self):
       # Update job progress in DB
       supabase_service.update_job(job_id, {
           'progress': 50,
           'status': 'running'
       })
   ```

2. **Retry Logic**
   ```python
   @celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
   def resilient_task(self):
       try:
           # Task logic
       except Exception as exc:
           if self.request.retries < self.max_retries:
               raise self.retry(exc=exc, countdown=2 ** self.request.retries)
           else:
               # Mark job as failed in DB
               supabase_service.update_job(job_id, {'status': 'failed'})
   ```

3. **Dead Letter Queue**
   - Failed jobs after max retries
   - Manual intervention capability

## Migration Steps

### Week 1: Core Infrastructure
- [ ] Create `app/workers/tasks.py`
- [ ] Set up Redis server
- [ ] Test Celery worker startup
- [ ] Migrate transcription jobs only
- [ ] Test transcription end-to-end

### Week 2: Full Migration
- [ ] Migrate scene generation jobs
- [ ] Migrate visual prompt jobs
- [ ] Migrate image generation jobs
- [ ] Migrate video generation jobs

### Week 3: Production Hardening
- [ ] Add job monitoring dashboard
- [ ] Implement retry policies
- [ ] Add job cleanup/archival
- [ ] Load testing with multiple workers

## Immediate Benefits

### ✅ After Migration:
- **Jobs survive server restarts** - Stored in Redis, not memory
- **Automatic retries** - Failed jobs retry with backoff
- **Horizontal scaling** - Multiple worker processes
- **Job monitoring** - View job status, progress, logs
- **Graceful shutdowns** - Jobs complete before worker shutdown

### 📊 Observability Improvements:
```bash
# Monitor jobs
celery -A app.workers.celery_app inspect active

# View worker status
celery -A app.workers.celery_app inspect stats

# Purge stuck jobs
celery -A app.workers.celery_app purge
```

## Production Deployment

### Development:
```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Celery Worker
celery -A app.workers.celery_app worker --loglevel=info

# Terminal 3: FastAPI Server
uvicorn app.main:app --reload
```

### Production:
```bash
# Use supervisord or systemd for process management
# Multiple worker processes for scaling
# Redis persistence for job durability
# Monitoring with Flower or custom dashboard
```

## Risk Assessment

### Low Risk:
- Transcription migration (single job type)
- Infrastructure setup

### Medium Risk:
- Scene generation migration (complex job chains)
- Concurrent job handling

### High Risk:
- Production deployment coordination
- Data migration for existing stuck jobs

## Rollback Plan

If migration causes issues:
1. **Keep FastAPI BackgroundTasks** as fallback
2. **Feature flag** to switch between Celery/BackgroundTasks
3. **Gradual rollout** by job type
4. **Database rollback** to restore stuck jobs

---

**Estimated Total Effort: 1-2 weeks**
**Immediate Priority: Fix stuck transcription jobs**
**Long-term Goal: Production-ready job processing**