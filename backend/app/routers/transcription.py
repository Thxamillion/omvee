"""
Audio transcription router using OpenAI Whisper API.
Handles audio transcription, progress tracking, and editing.
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
from uuid import UUID
import asyncio
import httpx
from typing import Optional

from app.services.whisper import WhisperService
from app.services.supabase import supabase_service
from app import models_pydantic as schemas
from app.dependencies.auth import get_current_user

router = APIRouter()

# Initialize Whisper service
whisper_service = WhisperService()

# Transcription now uses DB-backed jobs via the jobs table (see scenes.py pattern)


async def download_audio_file(audio_url: str) -> bytes:
    """Download audio file from URL for transcription."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(audio_url, timeout=60.0)
            if response.status_code == 200:
                return response.content
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to download audio file: {response.status_code}"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading audio file: {str(e)}"
        )


async def transcription_background_task(project_id: str, audio_url: str, job_id: str):
    """Background task for audio transcription using DB-backed jobs."""
    try:
        # Mark job as running
        supabase_service.update_job(job_id, {
            'status': 'running',
            'progress': 10,
            'payload_json': {
                'project_id': project_id,
                'stage': 'initializing'
            }
        })

        # Download audio file
        audio_content = await download_audio_file(audio_url)
        supabase_service.update_job(job_id, {
            'progress': 30,
            'payload_json': {
                'project_id': project_id,
                'stage': 'downloaded_audio'
            }
        })

        # Extract filename from URL for format detection
        filename = audio_url.split('/')[-1]
        if '?' in filename:
            filename = filename.split('?')[0]

        # Transcribe audio
        from io import BytesIO
        audio_file = BytesIO(audio_content)
        audio_file.name = filename

        transcription_result = await whisper_service.transcribe_audio(
            audio_file=audio_file,
            filename=filename
        )

        supabase_service.update_job(job_id, {
            'progress': 80,
            'payload_json': {
                'project_id': project_id,
                'stage': 'transcribed'
            }
        })

        # Save transcription to project
        update_data = {
            'transcription_status': 'completed',
            'transcription_data': transcription_result.model_dump(),
            'transcript_text': transcription_result.text
        }
        result = supabase_service.update_project(UUID(project_id), update_data)
        if not result:
            raise Exception("Failed to save transcription to project")

        # Mark job as completed
        supabase_service.update_job(job_id, {
            'status': 'completed',
            'progress': 100,
            'result_json': transcription_result.model_dump(),
            'payload_json': {
                'project_id': project_id,
                'stage': 'completed'
            }
        })

    except Exception as e:
        # Mark job as failed
        supabase_service.update_job(job_id, {
            'status': 'failed',
            'progress': 0,
            'error': str(e),
            'payload_json': {
                'project_id': project_id,
                'stage': 'failed'
            }
        })


@router.post("/projects/{project_id}/transcribe", response_model=schemas.TranscriptionJobResponse)
async def start_transcription(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    """Start transcription job for project audio."""
    try:
        # Check if project exists and belongs to user
        project = supabase_service.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        if project.get('user_id') != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Project does not belong to user"
            )

        if not project.get('audio_url'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project has no audio file. Upload audio first."
            )

        # Check if already transcribing or completed
        current_status = project.get('transcription_status', 'pending')
        if current_status == 'processing':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transcription already in progress"
            )

        if current_status == 'completed':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project already transcribed. Use PUT endpoint to edit."
            )

        # Prevent duplicate active transcription jobs for this project
        active_jobs = [j for j in supabase_service.get_project_jobs(project_id) if j.get('type') in ('transcribe', 'transcription') and j.get('status') in ('pending', 'running')]
        if active_jobs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transcription already in progress"
            )

        # Create DB job entry
        job_data = {
            'project_id': str(project_id),
            'type': 'transcribe',
            'status': 'pending',
            'progress': 0,
            'payload_json': {
                'project_id': str(project_id),
                'stage': 'queued'
            }
        }
        job = supabase_service.create_job(job_data)
        job_id = job['id']

        # Update project transcription status
        supabase_service.update_project(project_id, {'transcription_status': 'processing'})

        # Start background transcription (DB-backed job)
        background_tasks.add_task(
            transcription_background_task,
            str(project_id),
            project['audio_url'],
            job_id
        )

        # Estimate duration based on audio length
        audio_duration = project.get('audio_duration', 180.0)  # Default 3 minutes
        estimated_duration = audio_duration * 0.1  # Roughly 10% of audio length

        return schemas.TranscriptionJobResponse(
            job_id=job_id,
            status='started',
            estimated_duration=estimated_duration
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start transcription: {str(e)}"
        )


@router.get("/projects/{project_id}/transcription", response_model=schemas.TranscriptionStatusResponse)
async def get_transcription(
    project_id: UUID,
    user_id: str = Depends(get_current_user)
):
    """Get transcription results for project."""
    try:
        project = supabase_service.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        if project.get('user_id') != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Project does not belong to user"
            )

        transcription_status = project.get('transcription_status', 'pending')
        transcription_data = project.get('transcription_data')

        # Convert transcription_data to TranscriptionResult if it exists
        transcription_result = None
        if transcription_data:
            transcription_result = schemas.TranscriptionResult(**transcription_data)

        return schemas.TranscriptionStatusResponse(
            status=transcription_status,
            progress=1.0 if transcription_status == 'completed' else None,
            transcription_data=transcription_result
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting transcription: {str(e)}"
        )


@router.get("/transcription/jobs/{job_id}/status", response_model=schemas.TranscriptionStatusResponse)
async def get_transcription_job_status(
    job_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get real-time transcription job progress."""
    try:
        job = supabase_service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcription job not found"
            )

        # Verify job belongs to user through project ownership
        payload = job.get('payload_json', {})
        project_id = payload.get('project_id') or job.get('project_id')
        if project_id:
            project = supabase_service.get_project(UUID(project_id))
            if project and project.get('user_id') != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Job does not belong to user"
                )

        # Convert result to TranscriptionResult if available
        transcription_result = None
        if job.get('result_json'):
            transcription_result = schemas.TranscriptionResult(**job['result_json'])

        # Convert integer progress (0-100) to 0-1 float to keep prior response shape
        progress = None
        if job.get('progress') is not None:
            try:
                progress = float(job['progress']) / 100.0
            except Exception:
                progress = None

        return schemas.TranscriptionStatusResponse(
            status=job['status'],
            progress=progress,
            transcription_data=transcription_result,
            error_message=job.get('error')
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting job status: {str(e)}"
        )


@router.put("/projects/{project_id}/transcription", response_model=schemas.TranscriptionStatusResponse)
async def update_transcription(
    project_id: UUID,
    transcription_edit: schemas.TranscriptionEditRequest,
    user_id: str = Depends(get_current_user)
):
    """Save user-edited transcription."""
    try:
        # Check if project exists and belongs to user
        project = supabase_service.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        if project.get('user_id') != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Project does not belong to user"
            )

        # Validate that project has a transcription
        if project.get('transcription_status') != 'completed':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project has no completed transcription to edit"
            )

        # Update project with edited transcription
        update_data = {
            'transcription_data': transcription_edit.transcription_data.model_dump(),
            'transcript_text': transcription_edit.transcription_data.text,
            'transcription_edited': True
        }

        result = supabase_service.update_project(project_id, update_data)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to save edited transcription"
            )

        return schemas.TranscriptionStatusResponse(
            status='completed',
            progress=1.0,
            transcription_data=transcription_edit.transcription_data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update transcription: {str(e)}"
        )


@router.post("/transcription/estimate-cost")
async def estimate_transcription_cost(audio_duration_minutes: float):
    """Estimate cost for audio transcription."""
    try:
        if audio_duration_minutes <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio duration must be positive"
            )

        cost = await whisper_service.estimate_cost(audio_duration_minutes)

        return {
            "audio_duration_minutes": audio_duration_minutes,
            "estimated_cost_usd": cost,
            "cost_per_minute": whisper_service.COST_PER_MINUTE
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error estimating cost: {str(e)}"
        )
