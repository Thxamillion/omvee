"""
API endpoints for image generation with artist reference support.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.services.image_generation import ImageGenerationService
from app.services.artist import ArtistService
from app.services.supabase import get_supabase_client
from app.dependencies.auth import get_current_user
from app.models_pydantic import VisualPrompt
from supabase import Client

router = APIRouter(prefix="/image-generation", tags=["image-generation"])


class ImageGenerationRequest(BaseModel):
    """Request for image generation."""
    scene_id: int = Field(..., description="Scene ID for tracking")
    image_prompt: str = Field(..., description="Detailed image generation prompt")
    style_notes: Optional[str] = Field(None, description="Style guidance")
    negative_prompt: Optional[str] = Field(None, description="What to avoid in generation")
    setting: Optional[str] = Field(None, description="Scene setting")
    shot_type: Optional[str] = Field(None, description="Camera shot type")
    mood: Optional[str] = Field(None, description="Scene mood")
    color_palette: Optional[str] = Field(None, description="Color scheme")
    reference_image_url: Optional[str] = Field(None, description="Optional reference image URL")
    custom_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom generation parameters")




def get_image_generation_service() -> ImageGenerationService:
    """Dependency to get ImageGenerationService instance."""
    return ImageGenerationService()


def get_artist_service(supabase_client: Client = Depends(get_supabase_client)) -> ArtistService:
    """Dependency to get ArtistService instance."""
    return ArtistService(supabase_client)


@router.post("/generate", response_model=Dict[str, Any])
async def generate_image(
    request: ImageGenerationRequest,
    user_id: str = Depends(get_current_user),
    image_service: ImageGenerationService = Depends(get_image_generation_service)
) -> Dict[str, Any]:
    """
    Generate image from prompt with optional reference image.

    Args:
        request: Image generation request with prompt and optional reference

    Returns:
        Dictionary with generated image URLs and metadata
    """
    try:
        # Create VisualPrompt object
        visual_prompt = VisualPrompt(
            scene_id=request.scene_id,
            image_prompt=request.image_prompt,
            style_notes=request.style_notes or "",
            negative_prompt=request.negative_prompt or "",
            setting=request.setting or "",
            shot_type=request.shot_type or "",
            mood=request.mood or "",
            color_palette=request.color_palette or ""
        )

        # Generate image
        result = await image_service.generate_image_from_prompt(
            visual_prompt=visual_prompt,
            reference_image_url=request.reference_image_url,
            custom_params=request.custom_params
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")



@router.post("/generate-with-artist/{artist_id}", response_model=Dict[str, Any])
async def generate_image_with_artist(
    artist_id: UUID,
    request: ImageGenerationRequest,
    user_id: str = Depends(get_current_user),
    image_service: ImageGenerationService = Depends(get_image_generation_service),
    artist_service: ArtistService = Depends(get_artist_service)
) -> Dict[str, Any]:
    """
    Generate image using artist's reference image automatically.

    Args:
        artist_id: UUID of the artist to use for reference
        request: Image generation request (reference_image_url will be ignored)

    Returns:
        Dictionary with generated image URLs and metadata
    """
    try:
        # Get artist details
        artist = await artist_service.get_artist_by_id(artist_id)
        if not artist:
            raise HTTPException(status_code=404, detail="Artist not found")

        # Select a reference image (use first one for now)
        if not artist.reference_image_urls:
            raise HTTPException(status_code=400, detail="Artist has no reference images")

        reference_image_url = artist.reference_image_urls[0]

        # Create VisualPrompt object
        visual_prompt = VisualPrompt(
            scene_id=request.scene_id,
            image_prompt=request.image_prompt,
            style_notes=request.style_notes or "",
            negative_prompt=request.negative_prompt or "",
            setting=request.setting or "",
            shot_type=request.shot_type or "",
            mood=request.mood or "",
            color_palette=request.color_palette or ""
        )

        # Generate image with artist reference
        result = await image_service.generate_image_from_prompt(
            visual_prompt=visual_prompt,
            reference_image_url=reference_image_url,
            custom_params=request.custom_params
        )

        # Add artist information to result
        result["artist_metadata"] = {
            "artist_id": str(artist_id),
            "artist_name": artist.name,
            "reference_image_used": reference_image_url
        }

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Artist image generation failed: {e}")


@router.get("/cost-estimate", response_model=Dict[str, Any])
async def get_cost_estimate(
    num_images: int = 1,
    user_id: str = Depends(get_current_user),
    image_service: ImageGenerationService = Depends(get_image_generation_service)
) -> Dict[str, Any]:
    """
    Get cost estimate for image generation.

    Args:
        num_images: Number of images to generate

    Returns:
        Cost estimation breakdown
    """
    try:
        return image_service.estimate_cost(num_images)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cost estimation failed: {e}")


@router.get("/model-info", response_model=Dict[str, Any])
async def get_model_info(
    user_id: str = Depends(get_current_user),
    image_service: ImageGenerationService = Depends(get_image_generation_service)
) -> Dict[str, Any]:
    """
    Get information about the current image generation model.

    Returns:
        Model capabilities and configuration
    """
    try:
        return image_service.get_model_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {e}")


@router.get("/test-rio-prompt")
async def get_test_rio_prompt(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get a sample Rio prompt for testing image generation.

    Returns:
        Sample visual prompt for Rio Da Yung OG scene
    """
    return {
        "scene_id": 1,
        "image_prompt": "Ultra-detailed, cinematic music video frame featuring Rio Da Yung OG as shown in the reference image, standing confidently in a gritty urban alleyway. The artist is dressed in streetwear, including a hoodie and distressed jeans, with his signature chain visible. He holds a metallic object symbolizing 'peasy steel,' glinting under harsh, low-angle streetlight. The alley is lined with graffiti-covered walls and chain-link fences, with faint smoke rising in the background. The camera angle is a dynamic low-angle shot, emphasizing his dominance and the raw energy of the lyrics. Professional music video quality, 16:9 aspect ratio.",
        "style_notes": "Cinematic style with gritty realism and urban aesthetics. Artist appearance must match reference image.",
        "setting": "Dimly lit urban alleyway with graffiti-covered walls",
        "shot_type": "Low-angle close-up shot with dynamic composition",
        "mood": "Intense, confident, and gritty",
        "color_palette": "Dark, desaturated tones with metallic silver highlights",
        "reference_image_url": "REPLACE_WITH_REAL_RIO_IMAGE_URL",
        "lyrics_context": "Line them up, that's a easy kill I'm a real ghetto boy, I build peasy steel"
    }


