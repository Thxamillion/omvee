from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict
from uuid import UUID

from app.services.supabase import supabase_service, get_user_supabase_service, UserSupabaseService
from app.services.supabase_storage import supabase_storage_service
from app.dependencies.auth import get_current_user
from app import models_pydantic as schemas

router = APIRouter()


@router.post("/projects", response_model=schemas.Project)
async def create_project(
    project: schemas.ProjectCreate,
    user_id: str = Depends(get_current_user)
):
    """Create a new project."""
    try:
        project_data = project.model_dump()
        project_data['status'] = 'created'
        project_data['user_id'] = user_id

        result = supabase_service.create_project(project_data)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create project"
            )

        return schemas.Project(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating project: {str(e)}"
        )


@router.get("/projects", response_model=schemas.ProjectList)
async def list_projects(
    skip: int = 0,
    limit: int = 50,
    user_id: str = Depends(get_current_user)
):
    """List all projects with pagination."""
    try:
        result = supabase_service.list_projects(skip=skip, limit=limit)
        projects = [schemas.Project(**p) for p in result['projects']]

        return schemas.ProjectList(
            projects=projects,
            total=result['total']
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing projects: {str(e)}"
        )


@router.get("/projects/{project_id}", response_model=schemas.Project)
async def get_project(
    project_id: UUID,
    user_id: str = Depends(get_current_user)
):
    """Get a specific project by ID."""
    try:
        result = supabase_service.get_project(project_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        return schemas.Project(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting project: {str(e)}"
        )


@router.put("/projects/{project_id}", response_model=schemas.Project)
async def update_project(project_id: UUID, project_update: schemas.ProjectUpdate, user_id: str = Depends(get_current_user)):
    """Update a project."""
    try:
        # First check if project exists
        existing_project = supabase_service.get_project(project_id)
        if not existing_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Update with only provided fields
        update_data = project_update.model_dump(exclude_unset=True)
        if not update_data:
            return schemas.Project(**existing_project)

        result = supabase_service.update_project(project_id, update_data)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update project"
            )

        return schemas.Project(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating project: {str(e)}"
        )


@router.delete("/projects/{project_id}")
async def delete_project(project_id: UUID, user_id: str = Depends(get_current_user)):
    """Delete a project."""
    try:
        # First check if project exists
        existing_project = supabase_service.get_project(project_id)
        if not existing_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        success = supabase_service.delete_project(project_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete project"
            )

        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting project: {str(e)}"
        )


# Audio upload endpoints
@router.post("/projects/{project_id}/upload-audio", response_model=schemas.AudioUploadResponse)
async def upload_project_audio(project_id: UUID, audio_request: schemas.AudioUploadRequest, user_id: str = Depends(get_current_user)):
    """Create presigned URL for audio upload to specific project."""
    try:
        # First check if project exists
        existing_project = supabase_service.get_project(project_id)
        if not existing_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Validate audio content type
        allowed_types = [
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/aac',
            'audio/ogg', 'audio/flac', 'audio/x-wav', 'audio/mp4'
        ]

        if audio_request.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Content type {audio_request.content_type} not allowed. "
                       f"Allowed types: {', '.join(allowed_types)}"
            )

        # Create presigned upload URL for audio
        upload_data = supabase_storage_service.create_upload_url(
            project_id=str(project_id),
            filename=audio_request.filename,
            content_type=audio_request.content_type,
            expires_in=3600  # 1 hour
        )

        return schemas.AudioUploadResponse(
            signed_url=upload_data['signed_url'],
            file_path=upload_data['file_path'],
            public_url=upload_data['public_url'],
            upload_instructions="Upload your audio file using the signed_url with PUT method"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create audio upload URL: {str(e)}"
        )


@router.post("/projects/{project_id}/process-audio", response_model=schemas.AudioProcessingResponse)
async def process_project_audio(project_id: UUID, audio_info: schemas.AudioProcessingRequest, user_id: str = Depends(get_current_user)):
    """Process uploaded audio file and prepare for transcription."""
    try:
        # Check if project exists
        existing_project = supabase_service.get_project(project_id)
        if not existing_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # TODO: Add audio file validation and metadata extraction
        # For now, we'll extract format from URL and estimate duration
        audio_format = audio_info.audio_format
        if not audio_format:
            # Try to extract from URL
            if '.mp3' in audio_info.audio_url:
                audio_format = 'mp3'
            elif '.wav' in audio_info.audio_url:
                audio_format = 'wav'
            elif '.m4a' in audio_info.audio_url:
                audio_format = 'm4a'
            else:
                audio_format = 'unknown'

        # Update project with audio information
        update_data = {
            'audio_url': audio_info.audio_url,
            'audio_format': audio_format,
            'transcription_status': 'ready'  # Ready for transcription
        }

        # TODO: Add actual audio duration extraction
        # For now, we'll use a placeholder
        audio_duration = 180.0  # 3 minutes default

        update_data['audio_duration'] = audio_duration

        result = supabase_service.update_project(project_id, update_data)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update project with audio information"
            )

        return schemas.AudioProcessingResponse(
            audio_url=audio_info.audio_url,
            audio_duration=audio_duration,
            audio_format=audio_format,
            ready_for_transcription=True
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process audio: {str(e)}"
        )



# Images endpoints
@router.get("/projects/{project_id}/images", response_model=schemas.ImageList)
async def get_project_images(project_id: UUID, user_id: str = Depends(get_current_user)):
    """Get all generated images for a project."""
    try:
        images_data = supabase_service.get_project_images(project_id)
        images = [schemas.GeneratedImage(**i) for i in images_data]

        return schemas.ImageList(images=images, total=len(images))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting images: {str(e)}"
        )


# Video clips endpoints
@router.get("/projects/{project_id}/clips", response_model=schemas.VideoClipList)
async def get_project_clips(project_id: UUID, user_id: str = Depends(get_current_user)):
    """Get all video clips for a project."""
    try:
        clips_data = supabase_service.get_project_clips(project_id)
        clips = [schemas.VideoClip(**c) for c in clips_data]

        return schemas.VideoClipList(clips=clips, total=len(clips))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting clips: {str(e)}"
        )


# Jobs endpoints
@router.get("/projects/{project_id}/jobs", response_model=schemas.JobList)
async def get_project_jobs(project_id: UUID, user_id: str = Depends(get_current_user)):
    """Get all jobs for a project."""
    try:
        jobs_data = supabase_service.get_project_jobs(project_id)
        jobs = [schemas.Job(**j) for j in jobs_data]

        return schemas.JobList(jobs=jobs, total=len(jobs))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting jobs: {str(e)}"
        )


# Artist association endpoints
@router.put("/projects/{project_id}/artists")
async def associate_artists_with_project(
    project_id: UUID,
    artist_associations: Dict[str, str],  # {artist_id: selected_image_url}
    user_id: str = Depends(get_current_user)
):
    """
    Associate artists with a project and set their selected reference images.

    Args:
        project_id: UUID of the project
        artist_associations: Dictionary mapping artist_id to selected_image_url

    Returns:
        Updated project with selected_reference_images
    """
    try:
        # Verify project exists
        project = supabase_service.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Verify all artists exist and image URLs are valid
        from app.services.artist import ArtistService
        artist_service = ArtistService(supabase_service.client)

        artist_ids = [UUID(artist_id) for artist_id in artist_associations.keys()]
        artists = await artist_service.get_artists_by_ids(artist_ids)

        if len(artists) != len(artist_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more artists not found"
            )

        # Validate selected image URLs belong to the artists
        for artist in artists:
            selected_url = artist_associations[str(artist.id)]
            if selected_url not in artist.reference_image_urls:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Selected image URL not found in artist {artist.name}'s reference images"
                )

        # Update project with artist associations
        update_data = {
            'available_artist_ids': [str(artist_id) for artist_id in artist_ids],
            'selected_reference_images': artist_associations
        }

        updated_project = supabase_service.update_project(project_id, update_data)
        return updated_project

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to associate artists: {str(e)}"
        )


@router.get("/projects/{project_id}/available-artists")
async def get_available_artists_for_project(project_id: UUID, user_id: str = Depends(get_current_user)):
    """
    Get all available artists for project selection.

    Args:
        project_id: UUID of the project

    Returns:
        List of available artists with reference images
    """
    try:
        # Verify project exists
        project = supabase_service.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Get all artists
        from app.services.artist import ArtistService
        artist_service = ArtistService(supabase_service.client)
        artists = await artist_service.list_artists(limit=100)

        # Get currently selected artists for this project
        current_associations = project.get('selected_reference_images', {})

        # Format response with selection status
        artist_data = []
        for artist in artists:
            artist_info = {
                'id': str(artist.id),
                'name': artist.name,
                'description': artist.description,
                'reference_image_urls': artist.reference_image_urls,
                'created_at': artist.created_at.isoformat(),
                'is_selected': str(artist.id) in current_associations,
                'selected_image_url': current_associations.get(str(artist.id))
            }
            artist_data.append(artist_info)

        return {
            'project_id': str(project_id),
            'available_artists': artist_data,
            'total_artists': len(artist_data),
            'selected_count': len(current_associations)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available artists: {str(e)}"
        )