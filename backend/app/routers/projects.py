from fastapi import APIRouter, HTTPException, status
from typing import List
from uuid import UUID

from app.services.supabase import supabase_service
from app import models_pydantic as schemas

router = APIRouter()


@router.post("/projects", response_model=schemas.Project)
async def create_project(project: schemas.ProjectCreate):
    """Create a new project."""
    try:
        project_data = project.model_dump()
        project_data['status'] = 'created'

        result = supabase_service.create_project(project_data)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create project"
            )

        return schemas.Project(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating project: {str(e)}"
        )


@router.get("/projects", response_model=schemas.ProjectList)
async def list_projects(skip: int = 0, limit: int = 50):
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
async def get_project(project_id: UUID):
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
async def update_project(project_id: UUID, project_update: schemas.ProjectUpdate):
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
async def delete_project(project_id: UUID):
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


# Scene endpoints
@router.get("/projects/{project_id}/scenes", response_model=schemas.SceneList)
async def get_project_scenes(project_id: UUID):
    """Get all scenes for a project."""
    try:
        scenes_data = supabase_service.get_project_scenes(project_id)
        scenes = [schemas.SelectedScene(**s) for s in scenes_data]

        return schemas.SceneList(scenes=scenes, total=len(scenes))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting scenes: {str(e)}"
        )


# Images endpoints
@router.get("/projects/{project_id}/images", response_model=schemas.ImageList)
async def get_project_images(project_id: UUID):
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
async def get_project_clips(project_id: UUID):
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
async def get_project_jobs(project_id: UUID):
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