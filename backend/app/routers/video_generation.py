"""
API endpoints for video generation with ByteDance SeeDance integration.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from app.services.video_generation import VideoGenerationService
from app.services.openrouter import OpenRouterService
from app.services.supabase import get_supabase_client
from app.models_pydantic import VisualPrompt, SceneSelection
from app.dependencies.auth import get_current_user
from supabase import Client

router = APIRouter(prefix="/video-generation", tags=["video-generation"])


class VideoGenerationRequest(BaseModel):
    """Request for video generation from image."""
    scene_id: int = Field(..., description="Scene ID for tracking")
    image_url: str = Field(..., description="URL of the source image")
    motion_prompt: str = Field(..., description="Motion description for video")
    duration: Optional[int] = Field(5, ge=3, le=12, description="Video duration in seconds")
    custom_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom generation parameters")


class VideoFromSceneRequest(BaseModel):
    """Request for video generation from complete scene context."""
    scene_id: int = Field(..., description="Scene ID")
    image_url: str = Field(..., description="Generated image URL")
    song_title: str = Field(..., description="Song title")
    genre: str = Field(..., description="Music genre")
    artist_present: bool = Field(False, description="Whether artist appears in scene")
    custom_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom parameters")


def get_video_generation_service() -> VideoGenerationService:
    """Dependency to get VideoGenerationService instance."""
    return VideoGenerationService()


def get_openrouter_service() -> OpenRouterService:
    """Dependency to get OpenRouterService instance."""
    return OpenRouterService()


@router.post("/generate", response_model=Dict[str, Any])
async def generate_video(
    request: VideoGenerationRequest,
    video_service: VideoGenerationService = Depends(get_video_generation_service),
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate video from image and motion prompt.

    Args:
        request: Video generation request with image and motion prompt

    Returns:
        Dictionary with generated video URLs and metadata
    """
    try:
        # Create a basic scene object for metadata
        scene = SceneSelection(
            scene_id=request.scene_id,
            title="Manual Generation",
            start_time=0.0,
            end_time=float(request.duration or 5),
            duration=float(request.duration or 5),
            source_segments=[],
            lyrics_excerpt="Manual video generation",
            theme="user-defined",
            energy_level=5,
            visual_potential=5,
            narrative_importance=5,
            reasoning="Manual generation request"
        )

        # Generate video
        result = await video_service.generate_video_from_image(
            image_url=request.image_url,
            motion_prompt=request.motion_prompt,
            scene=scene,
            custom_params=request.custom_params
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video generation failed: {e}")


@router.post("/generate-from-scene", response_model=Dict[str, Any])
async def generate_video_from_scene(
    request: VideoFromSceneRequest,
    video_service: VideoGenerationService = Depends(get_video_generation_service),
    openrouter_service: OpenRouterService = Depends(get_openrouter_service),
    supabase_client: Client = Depends(get_supabase_client),
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate video from complete scene context using AI director.

    This endpoint:
    1. Fetches scene and visual prompt data
    2. Uses DeepSeek as video director to create motion prompt
    3. Generates video with ByteDance SeeDance

    Args:
        request: Complete scene context for video generation

    Returns:
        Dictionary with generated video URLs, motion prompt, and metadata
    """
    try:
        # Fetch scene data from database
        scene_response = supabase_client.table("selected_scenes").select("*").eq("id", request.scene_id).execute()
        if not scene_response.data:
            raise HTTPException(status_code=404, detail=f"Scene {request.scene_id} not found")

        scene_data = scene_response.data[0]
        scene = SceneSelection(
            scene_id=scene_data["id"],
            title=scene_data.get("lyric_excerpt", "Scene")[:50],
            start_time=scene_data.get("start_time_s", 0.0),
            end_time=scene_data.get("end_time_s", 5.0),
            duration=scene_data.get("end_time_s", 5.0) - scene_data.get("start_time_s", 0.0),
            source_segments=[],
            lyrics_excerpt=scene_data["lyric_excerpt"],
            theme=scene_data["theme"],
            energy_level=5,  # Default values
            visual_potential=5,
            narrative_importance=5,
            reasoning=scene_data.get("ai_reasoning", "")
        )

        # Fetch visual prompt data
        prompt_response = supabase_client.table("scene_prompts").select("*").eq("scene_id", request.scene_id).execute()
        if not prompt_response.data:
            raise HTTPException(status_code=404, detail=f"Visual prompt for scene {request.scene_id} not found")

        prompt_data = prompt_response.data[0]["prompt_json"]
        visual_prompt = VisualPrompt(
            scene_id=prompt_data["scene_id"],
            image_prompt=prompt_data["image_prompt"],
            style_notes=prompt_data["style_notes"],
            negative_prompt=prompt_data.get("negative_prompt", ""),
            setting=prompt_data["setting"],
            shot_type=prompt_data["shot_type"],
            mood=prompt_data["mood"],
            color_palette=prompt_data["color_palette"]
        )

        # Generate motion prompt using DeepSeek video director
        motion_prompt = await openrouter_service.generate_video_motion_prompt(
            scene=scene,
            visual_prompt=visual_prompt,
            image_url=request.image_url,
            song_title=request.song_title,
            genre=request.genre,
            artist_present=request.artist_present
        )

        # Generate video
        result = await video_service.generate_video_from_image(
            image_url=request.image_url,
            motion_prompt=motion_prompt,
            scene=scene,
            custom_params=request.custom_params
        )

        # Add motion prompt to result
        result["motion_prompt"] = motion_prompt
        result["director_metadata"] = {
            "song_title": request.song_title,
            "genre": request.genre,
            "artist_present": request.artist_present
        }

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scene video generation failed: {e}")


@router.get("/cost-estimate", response_model=Dict[str, Any])
async def get_cost_estimate(
    num_videos: int = 1,
    duration_seconds: int = 5,
    video_service: VideoGenerationService = Depends(get_video_generation_service)
) -> Dict[str, Any]:
    """
    Get cost estimate for video generation.

    Args:
        num_videos: Number of videos to generate
        duration_seconds: Duration of each video in seconds

    Returns:
        Cost estimation breakdown
    """
    try:
        return video_service.estimate_cost(num_videos, duration_seconds)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cost estimation failed: {e}")


@router.get("/model-info", response_model=Dict[str, Any])
async def get_model_info(
    video_service: VideoGenerationService = Depends(get_video_generation_service)
) -> Dict[str, Any]:
    """
    Get information about the current video generation model.

    Returns:
        Model capabilities and configuration
    """
    try:
        return video_service.get_model_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {e}")


@router.get("/test-rio-video")
async def get_test_rio_video_request() -> Dict[str, Any]:
    """
    Get a sample Rio video generation request for testing.

    Returns:
        Sample video generation request for Rio scene
    """
    return {
        "scene_id": 1,
        "image_url": "https://replicate.delivery/xezq/uted4m5qxiVMRyT9ya9uNyc6Ze3sy08s8zF4EmS0jCEE1jWVA/tmpw3ux6g6p.jpg",
        "song_title": "Easy Kill",
        "genre": "Hip-Hop/Rap",
        "artist_present": True,
        "custom_params": {
            "duration": 6,
            "resolution": "720p"
        },
        "expected_motion_prompt_elements": [
            "Rio Da Yung OG in urban alleyway",
            "holds metallic object",
            "camera movement (low-angle, zoom, pan)",
            "smoke and graffiti background motion",
            "confident, intense expression and movement"
        ]
    }