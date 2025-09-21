# OMVEE Audio Editor Integration Plan

## Vision

Create a sophisticated timeline-based editor interface that provides precise audio-synchronized control over the music video creation process. Users should be able to navigate, review, and edit AI-generated scenes with professional-grade audio controls.

## Core Editor Features

### 1. **Audio Player Integration**
- Embedded audio player with professional controls
- Play/pause, scrubbing, volume control
- Time display (current position / total duration)
- Keyboard shortcuts (spacebar = play/pause, arrow keys = seek)
- Click-to-seek on timeline bar

### 2. **Transcript-Audio Synchronization**
- Display full transcript with precise timestamps
- **Click any word/line** → audio jumps to that exact moment
- **Real-time highlighting** of current lyrics as audio plays
- Word-level precision for fine-grained navigation
- Auto-scroll transcript to follow audio playback

### 3. **Scene-Audio Navigation**
- AI-selected scenes displayed as blocks on timeline
- **Click any scene** → audio jumps to scene start time
- Scene boundaries clearly marked with start/end times
- **Current scene highlighting** as audio plays through it
- Scene duration and lyric preview on hover

### 4. **Timeline Controls**
- Linear timeline showing song duration (no waveform needed)
- Scene blocks positioned at correct timestamps
- Drag to adjust scene boundaries
- Visual playhead indicator showing current position
- Zoom in/out for precision editing

## User Workflow

```
1. Upload Song
   └── Audio player loads, timeline appears

2. AI Processing
   ├── Transcription appears with clickable timestamps
   └── Scene blocks appear on timeline

3. Review & Edit
   ├── Click transcript → jump to lyrics
   ├── Click scenes → jump to scene start
   ├── Drag scene boundaries to adjust timing
   └── Add/remove scenes manually

4. Generate Content
   ├── Create images for selected scenes
   ├── Generate videos with motion
   └── Preview final music video
```

## Technical Implementation

### Frontend Components Required

#### Audio Player Component
```typescript
interface AudioPlayer {
  src: string;              // Audio file URL
  currentTime: number;      // Current playback position
  duration: number;         // Total song length
  isPlaying: boolean;       // Play/pause state
  volume: number;           // Volume level (0-1)

  // Methods
  play(): void;
  pause(): void;
  seekTo(time: number): void;
  onTimeUpdate(callback: (time: number) => void): void;
}
```

#### Timeline Component
```typescript
interface Timeline {
  duration: number;         // Total song duration
  currentTime: number;      // Current playback position
  scenes: Scene[];          // Scene blocks to display

  // Events
  onSeek(time: number): void;
  onSceneClick(scene: Scene): void;
  onSceneDrag(sceneId: string, newStart: number, newEnd: number): void;
}
```

#### Transcript Component
```typescript
interface TranscriptSegment {
  id: string;
  text: string;
  startTime: number;
  endTime: number;
  isActive: boolean;        // Currently playing
}

interface Transcript {
  segments: TranscriptSegment[];
  currentTime: number;

  // Events
  onSegmentClick(segment: TranscriptSegment): void;
}
```

### Backend API Extensions Required

#### Audio Streaming Endpoint
```python
# app/routers/audio.py
@router.get("/api/projects/{project_id}/audio")
async def stream_project_audio(project_id: str):
    """Stream audio file for project with proper headers for seeking"""
    # Return audio with Range request support for scrubbing
```

#### Scene Management API
```python
# app/routers/scenes.py
@router.put("/api/projects/{project_id}/scenes/{scene_id}")
async def update_scene_timing(
    project_id: str,
    scene_id: str,
    timing_update: SceneTimingUpdate
):
    """Update scene start/end times from editor"""

@router.post("/api/projects/{project_id}/scenes")
async def create_custom_scene(
    project_id: str,
    scene_request: CustomSceneRequest
):
    """Add manually created scene"""
```

#### Real-time Sync (Optional)
```python
# WebSocket for live editing collaboration
@app.websocket("/ws/projects/{project_id}/editor")
async def editor_websocket(websocket: WebSocket, project_id: str):
    """Real-time updates for collaborative editing"""
```

### State Management

#### Editor State
```typescript
interface EditorState {
  // Audio
  audioUrl: string;
  currentTime: number;
  isPlaying: boolean;
  duration: number;

  // Content
  transcript: TranscriptSegment[];
  scenes: Scene[];

  // UI
  selectedSceneId: string | null;
  timelineZoom: number;

  // Actions
  seekToTime(time: number): void;
  selectScene(sceneId: string): void;
  updateSceneTiming(sceneId: string, start: number, end: number): void;
}
```

## Database Schema Updates

### Enhanced Scene Storage
```sql
-- Add user editing capabilities to scenes table
ALTER TABLE scenes ADD COLUMN user_modified BOOLEAN DEFAULT FALSE;
ALTER TABLE scenes ADD COLUMN custom_start_time FLOAT;
ALTER TABLE scenes ADD COLUMN custom_end_time FLOAT;
ALTER TABLE scenes ADD COLUMN user_notes TEXT;

-- Track editing history
CREATE TABLE scene_edits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scene_id UUID REFERENCES scenes(id),
    user_id UUID, -- When auth is added
    edit_type TEXT NOT NULL, -- 'timing_change', 'manual_create', 'delete'
    old_values JSONB,
    new_values JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Project Audio Storage
```sql
-- Track audio file information
ALTER TABLE projects ADD COLUMN audio_url TEXT;
ALTER TABLE projects ADD COLUMN audio_duration FLOAT;
ALTER TABLE projects ADD COLUMN audio_format TEXT;
```

## Implementation Priority

### Phase 1: Basic Audio Player (Week 1)
- [ ] Audio player component with play/pause/seek
- [ ] Timeline component showing duration
- [ ] Basic scene block display
- [ ] Click scene → seek to start time

### Phase 2: Transcript Integration (Week 2)
- [ ] Display transcript with timestamps
- [ ] Click transcript → seek to time
- [ ] Highlight current transcript segment
- [ ] Auto-scroll transcript during playback

### Phase 3: Scene Editing (Week 3)
- [ ] Drag scene boundaries to adjust timing
- [ ] Add custom scenes manually
- [ ] Delete/modify existing scenes
- [ ] Save scene modifications to database

### Phase 4: Polish & UX (Week 4)
- [ ] Keyboard shortcuts for editor
- [ ] Scene preview on hover
- [ ] Undo/redo functionality
- [ ] Performance optimization for long songs

## Technical Considerations

### Audio Performance
- **Preloading**: Load audio immediately on project open
- **Seeking**: Ensure smooth scrubbing without delays
- **Caching**: Cache audio files for repeated access
- **Format Support**: MP3, WAV, M4A compatibility

### Sync Accuracy
- **Timestamp Precision**: Use millisecond precision for timing
- **Update Frequency**: 60fps updates for smooth timeline movement
- **Debouncing**: Prevent excessive API calls during dragging

### Responsive Design
- **Mobile Considerations**: Touch-friendly controls for tablets
- **Screen Sizes**: Timeline scales appropriately
- **Accessibility**: Keyboard navigation support

## Integration with Existing Backend

### Leverage Current Architecture
- **Whisper Integration**: Already provides precise timestamps
- **Scene Selection**: AI scenes become editable blocks
- **Pydantic Models**: Extend existing Scene models
- **Supabase Storage**: Store audio files efficiently

### API Compatibility
- **Maintain Existing Endpoints**: Don't break current functionality
- **Extend Scene Models**: Add editing fields to existing schemas
- **Backward Compatibility**: Support both AI-only and edited workflows

This audio editor creates a professional music video production environment where users have precise creative control while leveraging AI assistance.