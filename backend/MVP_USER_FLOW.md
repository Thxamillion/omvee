# OMVEE MVP User Flow & Implementation Plan

## Overview

This document defines the **Minimum Viable Product (MVP)** user flow for OMVEE's AI-powered music video generation platform. The implementation follows a **step-by-step approach** in the exact order users will experience the product.

---

## 🎯 MVP User Flow

### **1. Upload Song**
- **User Action**: Upload audio file (MP3, WAV, etc.)
- **System Process**:
  ├── Transcribe audio with OpenAI Whisper
  └── Display editable transcription with timestamps
- **User Control**: Edit transcription for accuracy
- **Outcome**: Clean, accurate lyrics with precise timing

### **2. Project Settings**
- **User Input**:
  ├── **Artist Selection**: Choose artist with reference photos
  ├── **Style Preferences**: Visual style, mood, energy level
  └── **Scene Count**: 15-20 scenes (AI recommendation)
- **User Action**: Review settings and click "Accept"
- **Outcome**: Project configuration locked and ready for AI processing

### **3. Accept → Loading Screen**
- **System Processing** (with progress indicators):
  ├── "Analyzing lyrics..." (AI reads transcription)
  ├── "Selecting scenes..." (DeepSeek picks best moments)
  └── "Generating prompts..." (Creates image generation prompts)
- **Duration**: ~2-3 minutes for average song
- **Outcome**: AI-selected scenes with detailed visual prompts

### **4. /editor Screen - Scene Review**
- **Interface Components**:
  ├── **Audio Player**: Play/pause/seek with transcript sync
  ├── **Timeline**: Scene blocks positioned at correct timestamps
  ├── **Scene Details**: Each scene shows:
  │   ├── Lyrics excerpt for that moment
  │   ├── Generated image prompt (detailed description)
  │   └── Artist toggle (include artist in this scene?)
  └── **Selection Controls**: Individual checkboxes ☐ or "Accept All"
- **User Actions**:
  - Click scenes → audio jumps to scene start
  - Review prompts for quality/accuracy
  - Toggle artist presence per scene
  - Select scenes for image generation

### **5. Image Generation Phase**
- **Trigger**: User clicks checkboxes → Generate selected images
- **Process**:
  ├── Generate images for selected scenes (using MiniMax Image-01)
  ├── Display generated images within scene blocks
  └── Present approval interface for each image
- **User Controls**:
  ├── ✅ **Approve**: Accept image for video generation
  ├── 🔄 **Regenerate**: Create new image with same prompt
  ├── ✏️ **Edit Prompt**: Modify prompt and regenerate
  └── **Batch Actions**: "Approve All" or "Regenerate All"
- **Outcome**: Collection of approved images ready for video generation

### **6. Video Generation Phase**
- **Trigger**: "Generate Videos" button (appears when all images approved)
- **Process**:
  ├── Generate videos for approved images (using ByteDance SeeDance)
  ├── Show progress per scene (real-time updates)
  └── Compile final music video
- **Duration**: ~5-8 minutes for 15-20 scenes
- **Outcome**: Complete music video ready for download/preview

---

## 🚀 Implementation Order

### **Phase 1: Audio → Transcription → Editing**

#### Backend Tasks:
1. **Audio Upload Endpoint**
   ```python
   POST /api/projects/{id}/upload-audio
   # Handle file upload, validation, storage
   ```

2. **Whisper Transcription API**
   ```python
   POST /api/transcription/process
   # Integrate existing WhisperService into API endpoint
   ```

3. **Transcription Editing**
   ```python
   PUT /api/projects/{id}/transcription
   # Save user-edited transcription
   ```

#### Frontend Tasks:
1. Audio upload component with progress
2. Transcription display with editing capabilities
3. Save/validate edited transcription

#### Success Criteria:
- [ ] User can upload audio file
- [ ] Transcription appears with editable interface
- [ ] Edited transcription saves to database

---

### **Phase 2: Scene Selection & Prompts**

#### Backend Tasks:
1. **Scene Selection API** (NEW - currently only service exists)
   ```python
   POST /api/scene-selection/analyze
   # Convert OpenRouterService.select_scenes() to API endpoint
   ```

2. **Visual Prompt Generation API** (NEW)
   ```python
   POST /api/prompt-generation/create
   # Convert OpenRouterService.generate_visual_prompts() to API endpoint
   ```

3. **Loading Screen Progress API**
   ```python
   GET /api/projects/{id}/processing-status
   # Real-time updates for loading screen
   ```

#### Frontend Tasks:
1. Project settings form (artist, style, scene count)
2. Loading screen with progress indicators
3. /editor page layout and navigation
4. Audio player component integration

#### Success Criteria:
- [ ] Project settings save correctly
- [ ] Loading screen shows real progress
- [ ] /editor displays scenes with prompts
- [ ] Audio player syncs with timeline

---

### **Phase 3: Image Generation & Approval**

#### Backend Tasks:
1. **Individual Image Generation Endpoints** (enhance existing)
   ```python
   POST /api/image-generation/generate-for-scene
   # Generate image for specific scene with prompt
   ```

2. **Image Approval Tracking**
   ```python
   PUT /api/scenes/{id}/approve-image
   DELETE /api/scenes/{id}/regenerate-image
   ```

3. **Batch Image Operations**
   ```python
   POST /api/image-generation/batch-generate
   POST /api/scenes/batch-approve
   ```

#### Frontend Tasks:
1. Image display within scene blocks
2. Approve/regenerate/edit controls
3. Batch selection and operations
4. Image quality preview

#### Success Criteria:
- [ ] Images generate and display correctly
- [ ] Approval workflow functions smoothly
- [ ] Batch operations work efficiently
- [ ] Edit prompt functionality works

---

### **Phase 4: Video Generation**

#### Backend Tasks:
1. **Video Generation for Approved Images** (enhance existing)
   ```python
   POST /api/video-generation/generate-from-approved
   # Generate videos only for approved images
   ```

2. **Progress Tracking API**
   ```python
   GET /api/video-generation/progress/{job_id}
   # Real-time progress for multiple video generation
   ```

3. **Final Video Compilation**
   ```python
   POST /api/video-compilation/create-final
   # Combine individual scene videos into complete music video
   ```

#### Frontend Tasks:
1. Video generation progress interface
2. Individual video preview
3. Final video player/download
4. Project completion flow

#### Success Criteria:
- [ ] Videos generate from approved images
- [ ] Progress tracking works in real-time
- [ ] Final music video compiles correctly
- [ ] User can preview and download result

---

## 🎨 Key UX Design Decisions

### **Why Show Images for Approval:**
- **Quality Control**: Catch bad images before expensive video generation
- **User Confidence**: Visual confirmation of AI understanding
- **Creative Control**: Users can iterate on prompts
- **Debugging**: Clear separation between image and video issues

### **Individual vs Batch Controls:**
- **Individual Checkboxes**: Fine-grained control for perfectionist users
- **Accept All**: Quick workflow for users trusting AI results
- **Hybrid Approach**: Default to individual, offer batch shortcuts

### **Editor Screen Design:**
- **Audio-Centric**: Everything revolves around audio timeline
- **Visual Hierarchy**: Lyrics → Prompt → Image → Video
- **Click-to-Seek**: All elements navigate audio playback
- **Progressive Disclosure**: Show more details as user progresses

---

## 📊 Technical Considerations

### **Performance Requirements:**
- **Image Generation**: ~2-3 seconds per image (15-20 images = ~1 minute)
- **Video Generation**: ~20-30 seconds per video (15-20 videos = ~8 minutes)
- **Real-time Updates**: Progress updates every 2-3 seconds
- **Audio Streaming**: Smooth playback with seek capabilities

### **Error Handling:**
- **Failed Generations**: Clear retry mechanisms
- **Timeout Handling**: Graceful degradation for long operations
- **Partial Success**: Handle when some scenes succeed, others fail
- **User Recovery**: Easy restart points without losing progress

### **Data Management:**
- **Project State**: Track progress through each phase
- **Asset Organization**: Clean file management for generated content
- **Undo Capabilities**: Allow users to backtrack in workflow
- **Save Points**: Preserve work at each major step

---

## 🎯 MVP Success Metrics

### **User Experience:**
- [ ] Complete workflow from upload to final video
- [ ] Intuitive audio editor with timeline navigation
- [ ] Clear visual feedback at each step
- [ ] Minimal user confusion or workflow abandonment

### **Technical Performance:**
- [ ] Audio transcription accuracy >95%
- [ ] Scene selection relevance (user approval rate >80%)
- [ ] Image generation quality (regeneration rate <30%)
- [ ] End-to-end completion rate >70%

### **Business Validation:**
- [ ] Users complete full workflow
- [ ] Generated videos are shareable quality
- [ ] Users return to create additional projects
- [ ] Platform demonstrates clear value proposition

This MVP provides a complete, high-quality music video generation experience while maintaining user control and creative input throughout the process.