from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List, Dict, Any
from uuid import UUID

from app.models_pydantic import Artist, ArtistCreate
from app.services.artist import ArtistService
from app.services.storage import StorageService
from app.services.supabase import get_supabase_client
from app.dependencies.auth import get_current_user
from supabase import Client


router = APIRouter(prefix="/artists", tags=["artists"])


def get_artist_service(supabase_client: Client = Depends(get_supabase_client)) -> ArtistService:
    """Dependency to get ArtistService instance."""
    return ArtistService(supabase_client)


def get_storage_service(supabase_client: Client = Depends(get_supabase_client)) -> StorageService:
    """Dependency to get StorageService instance."""
    return StorageService(supabase_client)


@router.get("/test-storage", response_model=Dict[str, Any])
async def test_storage_access(
    storage_service: StorageService = Depends(get_storage_service)
) -> Dict[str, Any]:
    """
    Test storage bucket access for debugging.

    Returns:
        Dictionary with detailed storage access test results
    """
    try:
        test_results = storage_service.test_bucket_access()
        return {
            "status": "success",
            "test_results": test_results,
            "bucket_configured": test_results.get("exists", False),
            "upload_working": test_results.get("can_upload", False)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "bucket_configured": False,
            "upload_working": False
        }


@router.post("/", response_model=Artist, status_code=201)
async def create_artist(
    artist_data: ArtistCreate,
    user_id: str = Depends(get_current_user),
    artist_service: ArtistService = Depends(get_artist_service)
) -> Artist:
    """
    Create a new artist with reference images.

    Args:
        artist_data: Artist creation data including name, description, and reference images

    Returns:
        Created Artist object

    Raises:
        HTTPException: If creation fails
    """
    try:
        return await artist_service.create_artist(artist_data, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create artist: {e}")


@router.get("/{artist_id}", response_model=Artist)
async def get_artist(
    artist_id: UUID,
    user_id: str = Depends(get_current_user),
    artist_service: ArtistService = Depends(get_artist_service)
) -> Artist:
    """
    Get an artist by ID.

    Args:
        artist_id: UUID of the artist

    Returns:
        Artist object

    Raises:
        HTTPException: If artist not found
    """
    artist = await artist_service.get_artist_by_id(artist_id)
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    return artist


@router.get("/", response_model=Dict[str, Any])
async def list_artists(
    limit: int = 100,
    offset: int = 0,
    user_id: str = Depends(get_current_user),
    artist_service: ArtistService = Depends(get_artist_service)
) -> Dict[str, Any]:
    """
    List all artists with pagination.

    Args:
        limit: Maximum number of artists to return (default: 100)
        offset: Number of artists to skip (default: 0)

    Returns:
        Dictionary containing list of artists and total count
    """
    try:
        artists = await artist_service.list_artists(limit=limit, offset=offset)
        return {
            "artists": artists,
            "total": len(artists),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list artists: {e}")


@router.put("/{artist_id}", response_model=Artist)
async def update_artist(
    artist_id: UUID,
    update_data: Dict[str, Any],
    user_id: str = Depends(get_current_user),
    artist_service: ArtistService = Depends(get_artist_service)
) -> Artist:
    """
    Update an artist's information.

    Args:
        artist_id: UUID of the artist to update
        update_data: Dictionary of fields to update

    Returns:
        Updated Artist object

    Raises:
        HTTPException: If artist not found or update fails
    """
    try:
        updated_artist = await artist_service.update_artist(artist_id, update_data)
        if not updated_artist:
            raise HTTPException(status_code=404, detail="Artist not found")
        return updated_artist
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update artist: {e}")


@router.delete("/{artist_id}", status_code=204)
async def delete_artist(
    artist_id: UUID,
    user_id: str = Depends(get_current_user),
    artist_service: ArtistService = Depends(get_artist_service)
):
    """
    Delete an artist.

    Args:
        artist_id: UUID of the artist to delete

    Raises:
        HTTPException: If artist not found or deletion fails
    """
    try:
        success = await artist_service.delete_artist(artist_id)
        if not success:
            raise HTTPException(status_code=404, detail="Artist not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete artist: {e}")


@router.post("/{artist_id}/upload-images", response_model=Dict[str, Any])
async def upload_artist_reference_images(
    artist_id: UUID,
    images: List[UploadFile] = File(..., description="3-5 reference images"),
    user_id: str = Depends(get_current_user),
    artist_service: ArtistService = Depends(get_artist_service),
    storage_service: StorageService = Depends(get_storage_service)
) -> Dict[str, Any]:
    """
    Upload reference images for an artist.

    Args:
        artist_id: UUID of the artist
        images: List of 3-5 image files to upload

    Returns:
        Dictionary with uploaded image URLs and artist update status
    """
    try:
        # Verify artist exists
        artist = await artist_service.get_artist_by_id(artist_id)
        if not artist:
            raise HTTPException(status_code=404, detail="Artist not found")

        # Validate number of images
        if not 3 <= len(images) <= 5:
            raise HTTPException(
                status_code=422,
                detail="Must upload between 3 and 5 reference images"
            )

        # Validate each image file
        for image in images:
            if not await storage_service.validate_image_file(image):
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid image file: {image.filename}"
                )

        # Upload images to storage
        uploaded_urls = await storage_service.upload_artist_reference_images(
            artist_id, images
        )

        # Update artist with new reference image URLs
        updated_artist = await artist_service.update_artist(
            artist_id,
            {"reference_image_urls": uploaded_urls}
        )

        return {
            "message": "Reference images uploaded successfully",
            "artist_id": str(artist_id),
            "uploaded_images": uploaded_urls,
            "image_count": len(uploaded_urls),
            "artist": updated_artist
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload images: {e}")


@router.get("/{artist_id}/presigned-upload", response_model=Dict[str, Any])
async def get_presigned_upload_urls(
    artist_id: UUID,
    file_names: List[str],
    user_id: str = Depends(get_current_user),
    storage_service: StorageService = Depends(get_storage_service)
) -> Dict[str, Any]:
    """
    Get presigned URLs for client-side image uploads.

    Args:
        artist_id: UUID of the artist
        file_names: List of file names to upload

    Returns:
        Dictionary with presigned URLs for each file
    """
    try:
        if not 3 <= len(file_names) <= 5:
            raise HTTPException(
                status_code=422,
                detail="Must provide between 3 and 5 file names"
            )

        presigned_urls = []
        for file_name in file_names:
            url_data = await storage_service.get_presigned_upload_url(artist_id, file_name)
            presigned_urls.append({
                "file_name": file_name,
                **url_data
            })

        return {
            "artist_id": str(artist_id),
            "presigned_urls": presigned_urls,
            "upload_instructions": {
                "method": "PUT",
                "content_type": "image/*",
                "max_size_mb": 10
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate presigned URLs: {e}")