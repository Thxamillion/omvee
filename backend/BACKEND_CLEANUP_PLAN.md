# OMVEE Backend Cleanup & Production Readiness Plan

## 🎯 Executive Summary

The OMVEE backend is **functionally complete** with all major AI pipeline components working:
- ✅ **Whisper Integration**: Audio transcription with timestamps
- ✅ **OpenRouter/DeepSeek**: Scene selection and motion prompt generation
- ✅ **Replicate Image Generation**: MiniMax Image-01 with reference photos
- ✅ **Replicate Video Generation**: ByteDance SeeDance-1-Lite image-to-video

**Status**: Ready for frontend integration with cleanup recommended.

---

## 🧹 Immediate Cleanup Required

### 1. Remove Test Scripts from Root Directory
**Files to Delete:**
```bash
rm test_deepseek_director.py      # Converted to proper test
rm test_deepseek_video.py         # Converted to proper test
rm test_director_api.py           # Converted to proper test
rm test_rio_generation.py         # Converted to proper test
rm test_rio_video_generation.py   # Converted to proper test
rm test_whisper_real.py           # Already has proper test

# Keep generate_rio_transcription.py (utility script)
```

### 2. Clean Up Result Files
**Files to Remove:**
```bash
rm *.json transcription_results.txt
# Keep only: requirements.txt, CLAUDE.md, FRONTEND_SPECIFICATION.md
```

### 3. Clean Up Generated Assets
```bash
# Remove test artifacts
rm -rf generated_images/ generated_videos/ test_logs/
```

---

## 🔧 Code Refactoring Priorities

### HIGH PRIORITY (Before Frontend Integration)

#### 1. **Artist Service Async Conversion**
```python
# Current: Sync methods
def get_artist_by_id(self, artist_id: str) -> Optional[Artist]:

# Target: Async methods
async def get_artist_by_id(self, artist_id: str) -> Optional[Artist]:
```

#### 2. **Common Utilities Extraction**
Create `app/utils/` modules:
- `app/utils/logging.py` - Centralized test logging
- `app/utils/response_parser.py` - JSON response handling
- `app/utils/error_handler.py` - Common error patterns
- `app/utils/validation.py` - Input validation helpers

#### 3. **Configuration Consolidation** ✅ **COMPLETED**
Moved hard-coded model values to centralized config:
```python
# In app/config.py
class ModelConfig:
    image_model: str = "minimax/image-01:47ca89ad46682c1dd0ca335601cd7ea2eb10fb94ce4e0a5abafa7e74f23ae7b6"
    video_model: str = "bytedance/seedance-1-lite:5b618302c710fbcf00365dc75133537b5deed8a95dccaf983215559bb31fc943"
    scene_selection_model: str = "deepseek/deepseek-chat"
```

### MEDIUM PRIORITY (Post-MVP)

#### 4. **Add Missing Service Tests**
Missing test files:
- `tests/test_services/test_video_generation.py`
- `tests/test_services/test_image_generation.py`
- `tests/test_services/test_supabase_storage.py`

#### 5. **Add Missing Integration Tests**
- `tests/test_integration/test_video_generation_integration.py`
- `tests/test_integration/test_full_pipeline_integration.py`

---

## 📋 Convert Root Test Scripts to Proper Tests

### 1. **Video Generation Integration Test**
Convert `test_rio_video_generation.py` + `test_deepseek_video.py` into:
```python
# tests/test_integration/test_video_generation_integration.py
class TestVideoGenerationIntegration:
    async def test_manual_video_generation(self):
        """Test video generation with manual motion prompt"""

    async def test_deepseek_director_video_generation(self):
        """Test full pipeline: DeepSeek director → video generation"""

    async def test_video_generation_cost_estimation(self):
        """Test cost estimation accuracy"""
```

### 2. **Director/Motion Prompt Integration Test**
Convert `test_deepseek_director.py` + `test_director_api.py` into:
```python
# tests/test_integration/test_director_integration.py
class TestDeepSeekDirectorIntegration:
    async def test_motion_prompt_generation(self):
        """Test DeepSeek AI director motion prompt generation"""

    async def test_motion_prompt_quality(self):
        """Test motion prompt follows ByteDance SeeDance guidelines"""
```

### 3. **Image Generation Integration Test**
Convert `test_rio_generation.py` into:
```python
# tests/test_integration/test_image_generation_integration.py (enhance existing)
class TestImageGenerationIntegration:
    async def test_reference_image_generation(self):
        """Test image generation with artist reference photos"""

    async def test_comparison_generation(self):
        """Test with/without reference comparison"""
```

---

## 🚀 Frontend Integration Readiness

### API Endpoints Status

#### ✅ **Ready for Frontend**
1. **Health Check**: `GET /health`
2. **Artists**: `GET/POST/PUT/DELETE /api/artists/*`
3. **Projects**: `GET/POST/PUT/DELETE /api/projects/*`
4. **Image Generation**: `POST /api/image-generation/*`
5. **Video Generation**: `POST /api/video-generation/*`
6. **File Uploads**: `POST /api/uploads/*`

#### ⚠️ **Missing for Complete Frontend**
1. **Scene Selection Endpoint**: Convert OpenRouter service to API
2. **Full Pipeline Endpoint**: Single endpoint for complete music video generation
3. **Job Status/Progress**: Real-time progress tracking
4. **File Management**: Delete/organize generated assets

### Required New Endpoints

#### 1. **Scene Selection API**
```python
# app/routers/scene_selection.py
@router.post("/api/scene-selection/analyze")
async def analyze_audio_scenes(request: SceneAnalysisRequest):
    """Convert audio transcription to scene selection using AI"""

@router.get("/api/scene-selection/{project_id}")
async def get_project_scenes(project_id: str):
    """Get scenes for a project"""
```

#### 2. **Pipeline Orchestration API**
```python
# app/routers/pipeline.py
@router.post("/api/pipeline/generate-music-video")
async def generate_complete_music_video(request: PipelineRequest):
    """Full pipeline: Audio → Scenes → Images → Videos → Final Video"""

@router.get("/api/pipeline/status/{job_id}")
async def get_pipeline_status(job_id: str):
    """Get real-time pipeline progress"""
```

#### 3. **Asset Management API**
```python
# app/routers/assets.py
@router.get("/api/assets/{project_id}")
async def list_project_assets(project_id: str):
    """List all generated assets for a project"""

@router.delete("/api/assets/{asset_id}")
async def delete_asset(asset_id: str):
    """Delete generated asset"""
```

---

## 🏗️ Database Schema Completeness

### ✅ **Existing Tables (Ready)**
- `projects` - Project metadata
- `artists` - Artist data and reference images
- `scenes` - Selected scenes from audio analysis
- `images` - Generated image metadata
- `videos` - Generated video metadata
- `jobs` - Async job tracking

### ⚠️ **Missing Tables (Needed)**
```sql
-- Scene selections (from OpenRouter analysis)
CREATE TABLE scene_selections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    scenes JSONB NOT NULL, -- SceneSelectionResult
    transcription_metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Pipeline jobs (for complex workflows)
CREATE TABLE pipeline_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    pipeline_type TEXT NOT NULL, -- 'full_music_video', 'scene_analysis', etc
    status TEXT NOT NULL, -- 'pending', 'processing', 'completed', 'failed'
    progress JSONB, -- Step-by-step progress
    result JSONB, -- Final result
    error_details TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Asset tracking (for file management)
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    asset_type TEXT NOT NULL, -- 'audio', 'image', 'video', 'final_video'
    file_url TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🎬 Production Deployment Checklist

### Environment Configuration
- [ ] **Environment Variables**: All API keys configured
- [ ] **CORS Settings**: Frontend domain added to allowed origins
- [ ] **Database**: Production Supabase instance setup
- [ ] **Redis**: Production Redis instance for job queue
- [ ] **Storage**: Production Supabase Storage buckets

### Performance & Monitoring
- [ ] **Rate Limiting**: Add rate limits to AI service endpoints
- [ ] **Caching**: Implement response caching for expensive operations
- [ ] **Logging**: Structured logging for production debugging
- [ ] **Health Checks**: Comprehensive health monitoring
- [ ] **Error Tracking**: Integration with Sentry or similar

### Security
- [ ] **API Key Validation**: Proper API key management
- [ ] **File Upload Security**: File type/size validation
- [ ] **Input Sanitization**: Prevent injection attacks
- [ ] **HTTPS**: SSL certificate configuration

---

## 📊 Development Timeline

### **Phase 1: Immediate Cleanup (1-2 days)**
- Remove test scripts and clean up artifacts
- Extract common utilities
- Convert Artist service to async
- Add missing service tests

### **Phase 2: Frontend Integration Prep (2-3 days)**
- Create scene selection API endpoints
- Add pipeline orchestration endpoints
- Implement missing database tables
- Add asset management APIs

### **Phase 3: Integration Testing (1-2 days)**
- Convert remaining test scripts to proper tests
- Full pipeline integration tests
- Frontend-backend integration testing

### **Phase 4: Production Readiness (2-3 days)**
- Performance optimization
- Security hardening
- Monitoring and logging setup
- Deployment configuration

---

## 🎯 Next Actions

### **Immediate (Today)**
1. **Clean up root directory**: Remove test scripts and result files
2. **Update todo status**: Mark analysis complete
3. **Start Artist service refactor**: Convert to async

### **This Week**
1. **Extract common utilities**
2. **Add missing API endpoints**
3. **Create proper integration tests**
4. **Database schema updates**

### **Frontend Team Coordination**
1. **API Documentation**: Update OpenAPI docs with new endpoints
2. **Frontend Specification**: Update `FRONTEND_SPECIFICATION.md`
3. **Development Environment**: Ensure frontend can connect to backend locally
4. **Production Planning**: Coordinate deployment strategy

The backend is **architecturally sound and functionally complete**. The main work needed is cleanup, consistency improvements, and adding the orchestration layer for seamless frontend integration.