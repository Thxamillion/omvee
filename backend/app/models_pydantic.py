from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4


# Base schemas with validation
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    audio_path: Optional[str] = None
    transcript_text: Optional[str] = None
    status: Optional[str] = None


class Project(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    audio_path: Optional[str] = None
    transcript_text: Optional[str] = None
    status: str = "created"
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


# Health check schema
class HealthCheck(BaseModel):
    status: str
    supabase: str
    redis: str
    environment: str