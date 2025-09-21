from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4


# AI Service Response Models
class TranscriptionSegment(BaseModel):
    """Individual segment from audio transcription."""
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Transcribed text for this segment")


class TranscriptionResult(BaseModel):
    """Result from audio transcription service."""
    text: str = Field(..., description="Full transcribed text")
    segments: List[Dict[str, Any]] = Field(default_factory=list, description="Time-segmented transcription")


class SceneSelection(BaseModel):
    """Individual scene selected by AI from lyrics."""
    scene_id: int = Field(..., description="Unique scene identifier")
    title: str = Field(..., description="Descriptive scene title")
    start_time: float = Field(..., description="Scene start time in seconds")
    end_time: float = Field(..., description="Scene end time in seconds")
    duration: float = Field(..., description="Scene duration in seconds")
    source_segments: List[int] = Field(..., description="Original segment IDs that compose this scene")
    lyrics_excerpt: str = Field(..., description="Combined lyrics for this scene")
    theme: str = Field(..., description="Scene theme/mood")
    energy_level: int = Field(..., ge=1, le=10, description="Energy intensity (1-10)")
    visual_potential: int = Field(..., ge=1, le=10, description="Visual storytelling potential (1-10)")
    narrative_importance: int = Field(..., ge=1, le=10, description="Story significance (1-10)")
    reasoning: str = Field(..., description="AI reasoning for selecting this scene")


class SceneSelectionResult(BaseModel):
    """Result from AI scene selection analysis."""
    song_themes: List[str] = Field(..., description="Identified themes in the song")
    energy_arc: str = Field(..., description="Overall energy progression description")
    total_scenes_selected: int = Field(..., description="Number of scenes selected")
    average_scene_length: float = Field(..., description="Average scene duration")
    selected_scenes: List[SceneSelection] = Field(..., description="Selected scenes for music video")
    reasoning_summary: str = Field(..., description="Overall selection strategy explanation")


class VisualPrompt(BaseModel):
    """Visual prompt for image generation."""
    scene_id: int = Field(..., description="Reference to scene")
    image_prompt: str = Field(..., description="Detailed prompt for image generation")
    style_notes: str = Field(..., description="Style and aesthetic guidance")
    negative_prompt: str = Field(..., description="What to avoid in generation")
    setting: str = Field(..., description="Scene setting/location")
    shot_type: str = Field(..., description="Camera shot type")
    mood: str = Field(..., description="Overall mood/atmosphere")
    color_palette: str = Field(..., description="Suggested color scheme")


class PromptGenerationResult(BaseModel):
    """Result from AI visual prompt generation."""
    total_prompts: int = Field(..., description="Number of prompts generated")
    visual_prompts: List[VisualPrompt] = Field(..., description="Generated visual prompts")
    style_consistency: str = Field(..., description="Overall visual style approach")
    generation_notes: str = Field(..., description="Notes for image generation")


# Artist schemas
class ArtistBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ArtistCreate(ArtistBase):
    reference_image_urls: List[str] = Field(..., min_length=3, max_length=5)


class Artist(ArtistBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reference_image_urls: List[str]
    created_at: datetime


# Base schemas with validation
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    audio_path: Optional[str] = None
    audio_url: Optional[str] = None
    audio_duration: Optional[float] = None
    audio_format: Optional[str] = None
    transcript_text: Optional[str] = None
    transcription_status: Optional[str] = None
    transcription_data: Optional[TranscriptionResult] = None
    transcription_edited: Optional[bool] = None
    status: Optional[str] = None


class Project(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    audio_path: Optional[str] = None
    audio_url: Optional[str] = None
    audio_duration: Optional[float] = None
    audio_format: Optional[str] = None
    transcript_text: Optional[str] = None
    transcription_status: str = "pending"
    transcription_data: Optional[TranscriptionResult] = None
    transcription_edited: bool = False
    status: str = "created"
    available_artist_ids: List[UUID] = Field(default_factory=list)
    selected_reference_images: Dict[str, str] = Field(default_factory=dict)  # {artist_id: image_url}
    created_at: datetime
    updated_at: datetime


# Scene schemas
class SelectedSceneBase(BaseModel):
    lyric_excerpt: str = Field(..., min_length=1)
    theme: str = Field(..., min_length=1, max_length=255)
    ai_reasoning: Optional[str] = None
    order_idx: int = Field(..., ge=0)
    start_time_s: Optional[float] = Field(None, ge=0)
    end_time_s: Optional[float] = Field(None, ge=0)


class SelectedSceneCreate(SelectedSceneBase):
    project_id: UUID


class SelectedScene(SelectedSceneBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    featured_artist_ids: List[UUID] = Field(default_factory=list)
    artist_prominence: str = Field(default="none", pattern="^(primary|background|none)$")


# Prompt schemas
class ScenePromptBase(BaseModel):
    prompt_json: Dict[str, Any]
    generated_by_model: str = Field(..., min_length=1)


class ScenePromptCreate(ScenePromptBase):
    scene_id: UUID


class ScenePrompt(ScenePromptBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scene_id: UUID
    created_at: datetime


# Image schemas
class GeneratedImageBase(BaseModel):
    image_url: Optional[str] = None
    replicate_prediction_id: Optional[str] = None
    status: str = Field(default="generating", pattern="^(generating|completed|failed)$")


class GeneratedImageCreate(GeneratedImageBase):
    project_id: UUID
    scene_id: UUID
    prompt_id: UUID


class GeneratedImage(GeneratedImageBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    scene_id: UUID
    prompt_id: UUID
    created_at: datetime


# Video clip schemas
class VideoClipBase(BaseModel):
    video_url: Optional[str] = None
    duration_s: Optional[float] = Field(None, gt=0)
    replicate_prediction_id: Optional[str] = None
    status: str = Field(default="generating", pattern="^(generating|completed|failed)$")


class VideoClipCreate(VideoClipBase):
    project_id: UUID
    image_id: UUID


class VideoClip(VideoClipBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    image_id: UUID
    created_at: datetime


# Approval schemas
class UserApprovalBase(BaseModel):
    approved: bool
    notes: Optional[str] = None


class UserApprovalCreate(UserApprovalBase):
    project_id: UUID
    scene_id: Optional[UUID] = None
    video_clip_id: Optional[UUID] = None


class UserApproval(UserApprovalBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    scene_id: Optional[UUID] = None
    video_clip_id: Optional[UUID] = None
    created_at: datetime


# Final video schemas
class FinalVideoBase(BaseModel):
    video_path: Optional[str] = None
    status: str = Field(default="assembling", pattern="^(assembling|completed|failed)$")


class FinalVideoCreate(FinalVideoBase):
    project_id: UUID


class FinalVideo(FinalVideoBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    created_at: datetime


# Scene generation API response models
class SceneGenerationJobResponse(BaseModel):
    """Response when starting scene generation job."""
    job_id: str = Field(..., description="Unique job identifier for tracking")
    status: str = Field(..., description="Job status")
    estimated_duration: float = Field(..., description="Estimated duration in seconds")


class SceneGenerationStatusResponse(BaseModel):
    """Real-time status of scene generation job."""
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Current status")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress from 0 to 1")
    completed_prompts: int = Field(..., description="Number of prompts completed")
    total_prompts: int = Field(..., description="Total prompts to generate")
    error_message: Optional[str] = None


class SceneWithPrompt(BaseModel):
    """Scene data with optional visual prompt."""
    scene_id: int = Field(..., description="Scene identifier")
    title: str = Field(..., description="Scene title")
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    duration: float = Field(..., description="Duration in seconds")
    lyrics_excerpt: str = Field(..., description="Scene lyrics")
    theme: str = Field(..., description="Scene theme")
    energy_level: int = Field(..., ge=1, le=10, description="Energy level 1-10")
    visual_potential: int = Field(..., ge=1, le=10, description="Visual potential 1-10")
    narrative_importance: int = Field(..., ge=1, le=10, description="Narrative importance 1-10")
    reasoning: str = Field(..., description="Why this scene was selected")
    visual_prompt: Optional[VisualPrompt] = None
    prompt_status: str = Field(default="pending", description="Prompt generation status")


class ProjectScenesResponse(BaseModel):
    """Response containing all scenes for a project."""
    project_id: str = Field(..., description="Project identifier")
    status: str = Field(..., description="Project status")
    scenes: List[SceneWithPrompt] = Field(..., description="Project scenes")
    completed_prompts: int = Field(..., description="Number of completed prompts")
    total_prompts: int = Field(..., description="Total prompts expected")


# Job schemas
class JobBase(BaseModel):
    type: str = Field(..., min_length=1)
    status: str = Field(default="pending", pattern="^(pending|running|completed|failed)$")
    progress: int = Field(default=0, ge=0, le=100)
    payload_json: Optional[Dict[str, Any]] = None
    result_json: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class JobCreate(JobBase):
    project_id: UUID


class Job(JobBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime


# Response schemas for lists
class ProjectList(BaseModel):
    projects: List[Project]
    total: int


class SceneList(BaseModel):
    scenes: List[SelectedScene]
    total: int


class ImageList(BaseModel):
    images: List[GeneratedImage]
    total: int


class VideoClipList(BaseModel):
    clips: List[VideoClip]
    total: int


class JobList(BaseModel):
    jobs: List[Job]
    total: int


# File upload schemas for Supabase Storage
class SupabaseUploadRequest(BaseModel):
    filename: str = Field(..., min_length=1)
    content_type: str = Field(..., min_length=1)
    project_id: UUID


class SupabaseUploadResponse(BaseModel):
    signed_url: str
    file_path: str
    public_url: str


# Audio Upload Schemas
class AudioUploadRequest(BaseModel):
    filename: str = Field(..., min_length=1, description="Audio filename")
    content_type: str = Field(..., min_length=1, description="Audio content type")


class AudioUploadResponse(BaseModel):
    signed_url: str = Field(..., description="Presigned URL for upload")
    file_path: str = Field(..., description="Storage file path")
    public_url: str = Field(..., description="Public URL after upload")
    upload_instructions: str = Field(..., description="Instructions for upload")


class AudioProcessingRequest(BaseModel):
    audio_url: str = Field(..., description="URL of uploaded audio file")
    audio_format: Optional[str] = Field(None, description="Audio format (mp3, wav, etc.)")


class AudioProcessingResponse(BaseModel):
    audio_url: str = Field(..., description="Processed audio URL")
    audio_duration: float = Field(..., description="Audio duration in seconds")
    audio_format: str = Field(..., description="Detected audio format")
    ready_for_transcription: bool = Field(..., description="Whether audio is ready for transcription")


# Transcription Schemas
class TranscriptionJobResponse(BaseModel):
    job_id: str = Field(..., description="Background job identifier")
    status: str = Field(..., description="Job status")
    estimated_duration: Optional[float] = Field(None, description="Estimated completion time in seconds")


class TranscriptionStatusResponse(BaseModel):
    status: str = Field(..., description="transcription status: pending, processing, completed, failed")
    progress: Optional[float] = Field(None, ge=0.0, le=1.0, description="Progress percentage (0.0-1.0)")
    transcription_data: Optional[TranscriptionResult] = Field(None, description="Transcription result if completed")
    error_message: Optional[str] = Field(None, description="Error details if failed")


class TranscriptionEditRequest(BaseModel):
    transcription_data: TranscriptionResult = Field(..., description="Edited transcription data")
    segments_modified: List[int] = Field(default_factory=list, description="List of modified segment indices")


class SegmentUpdateRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Updated segment text")
    start_time: Optional[float] = Field(None, ge=0, description="Updated start time")
    end_time: Optional[float] = Field(None, ge=0, description="Updated end time")


# Health check schema
class HealthCheck(BaseModel):
    status: str
    supabase: str
    redis: str
    environment: str