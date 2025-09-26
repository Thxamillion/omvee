"""
Scene selection and visual prompt generation router.
Handles Phase 2 of the AI pipeline: Scene Selection → Visual Prompts.
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
from uuid import UUID
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

from app.services.openrouter import OpenRouterService
from app.services.supabase import supabase_service
from app import models_pydantic as schemas
from app.config import settings
from app.dependencies.auth import get_current_user

router = APIRouter()

# Initialize OpenRouter service
openrouter_service = OpenRouterService(api_key=settings.openrouter_api_key)

# Job tracking is now handled via database instead of in-memory
# scene_generation_jobs = {}  # DEPRECATED - using jobs table


async def scene_selection_task(project_id: str, job_id: str):
    """Background task for scene selection only."""
    try:
        # Update job status in database
        supabase_service.update_job(job_id, {
            'status': 'running',
            'progress': 10,
            'payload_json': {
                'project_id': project_id,
                'stage': 'selecting_scenes'
            }
        })

        # Get project and validate it has transcription
        project = supabase_service.get_project(UUID(project_id))
        if not project:
            raise Exception("Project not found")

        transcription_data = project.get('transcription_data')
        if not transcription_data:
            raise Exception("Project has no transcription data")

        # Convert to TranscriptionResult
        transcription_result = schemas.TranscriptionResult(**transcription_data)

        # Update progress
        supabase_service.update_job(job_id, {
            'progress': 30,
            'payload_json': {
                'project_id': project_id,
                'stage': 'analyzing_lyrics'
            }
        })

        # Scene selection
        song_metadata = {
            'title': project.get('name', 'Unknown'),
            'artist': project.get('artist', 'Unknown'),
            'genre': project.get('genre', 'Unknown')
        }

        # Get song duration from project or transcription
        song_duration = project.get('audio_duration')

        scene_selection = await openrouter_service.select_scenes(
            transcription=transcription_result,
            target_scenes=15,
            song_metadata=song_metadata,
            song_duration=song_duration
        )

        # Update progress
        supabase_service.update_job(job_id, {
            'progress': 80,
            'payload_json': {
                'project_id': project_id,
                'stage': 'saving_scenes'
            }
        })

        # Save scenes to database
        scenes_data = []
        for i, scene in enumerate(scene_selection.selected_scenes):
            scene_data = {
                'project_id': str(project_id),
                'lyric_excerpt': scene.lyrics_excerpt,
                'theme': scene.theme,
                'order_idx': i,
                'scene_id': scene.scene_id,
                'title': scene.title,
                'start_time': float(scene.start_time),
                'end_time': float(scene.end_time),
                'duration': float(scene.duration),
                'energy_level': int(scene.energy_level),
                'visual_potential': int(scene.visual_potential),
                'narrative_importance': int(scene.narrative_importance),
                'reasoning': scene.reasoning
            }
            scenes_data.append(scene_data)

        # Save scenes in batch
        for scene_data in scenes_data:
            supabase_service.create_scene(scene_data)

        # Update project with scene selection data
        update_data = {
            'status': 'scenes_processing',
            'scene_selection_data': scene_selection.model_dump(),
            'scenes_count': len(scene_selection.selected_scenes)
        }
        supabase_service.update_project(UUID(project_id), update_data)

        # Mark job as completed
        supabase_service.update_job(job_id, {
            'status': 'completed',
            'progress': 100,
            'result_json': {
                'scenes_count': len(scene_selection.selected_scenes),
                'completion_time': str(datetime.now())
            },
            'payload_json': {
                'project_id': project_id,
                'stage': 'completed',
                'scenes_count': len(scene_selection.selected_scenes)
            }
        })

        print(f"✅ Scene selection completed: {len(scene_selection.selected_scenes)} scenes")

        # Automatically start visual prompt generation job
        prompt_job_data = {
            'project_id': str(project_id),
            'type': 'generate_visual_prompts',
            'status': 'pending',
            'progress': 0,
            'payload_json': {
                'project_id': str(project_id),
                'stage': 'initializing',
                'completed_prompts': 0,
                'total_prompts': len(scene_selection.selected_scenes)
            }
        }
        prompt_job = supabase_service.create_job(prompt_job_data)
        prompt_job_id = prompt_job['id']

        # Start prompt generation task
        from fastapi import BackgroundTasks
        import asyncio
        asyncio.create_task(visual_prompt_generation_task(project_id, prompt_job_id))

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
        print(f"❌ Scene selection failed: {str(e)}")


async def visual_prompt_generation_task(project_id: str, job_id: str):
    """Background task for visual prompt generation only."""
    try:
        # Update job status
        supabase_service.update_job(job_id, {
            'status': 'running',
            'progress': 10,
            'payload_json': {
                'project_id': project_id,
                'completed_prompts': 0,
                'stage': 'loading_scenes'
            }
        })

        # Get project and scenes
        project = supabase_service.get_project(UUID(project_id))
        if not project:
            raise Exception("Project not found")

        scenes = supabase_service.get_project_scenes(UUID(project_id))
        if not scenes:
            raise Exception("No scenes found for project")

        # Update job with total prompts count
        supabase_service.update_job(job_id, {
            'progress': 20,
            'payload_json': {
                'project_id': project_id,
                'completed_prompts': 0,
                'total_prompts': len(scenes),
                'stage': 'generating_prompts'
            }
        })

        # Convert database scenes to SceneSelection format
        scene_selections = []
        for scene in scenes:
            scene_selection = schemas.SceneSelection(
                scene_id=scene['scene_id'],
                title=scene['title'],
                start_time=scene['start_time'],
                end_time=scene['end_time'],
                duration=scene['duration'],
                source_segments=[],  # Default empty list - not stored in database
                lyrics_excerpt=scene['lyric_excerpt'],
                theme=scene['theme'],
                energy_level=scene['energy_level'],
                visual_potential=scene['visual_potential'],
                narrative_importance=scene['narrative_importance'],
                reasoning=scene['reasoning']
            )
            scene_selections.append(scene_selection)

        print(f"🎨 Starting parallel generation of {len(scenes)} visual prompts...")

        # Get song metadata and artist references
        song_metadata = {
            'title': project.get('name', 'Unknown'),
            'artist': project.get('artist', 'Unknown'),
            'genre': project.get('genre', 'Unknown')
        }
        artist_reference_images = project.get('selected_reference_images', {})

        # Fire all prompt generation tasks in parallel
        prompt_tasks = [
            openrouter_service.generate_individual_visual_prompt_with_artist(
                scene, artist_reference_images, song_metadata
            )
            for scene in scene_selections
        ]

        # Wait for all prompts to complete
        visual_prompts = await asyncio.gather(*prompt_tasks)

        # Save prompts and update progress
        for i, (scene, prompt) in enumerate(zip(scene_selections, visual_prompts)):
            # Save to database
            supabase_service.client.table('selected_scenes')\
                .update({
                    'visual_prompt_data': prompt.model_dump(),
                    'prompt_status': 'completed'
                })\
                .eq('project_id', project_id)\
                .eq('scene_id', scene.scene_id)\
                .execute()

            # Update progress
            completed_prompts = i + 1
            progress = 20 + int(70 * completed_prompts / len(visual_prompts))
            supabase_service.update_job(job_id, {
                'progress': progress,
                'payload_json': {
                    'project_id': project_id,
                    'completed_prompts': completed_prompts,
                    'total_prompts': len(visual_prompts),
                    'stage': 'generating_prompts'
                }
            })

        # Update project status to fully completed
        supabase_service.update_project(UUID(project_id), {
            'status': 'scenes_completed'
        })

        # Mark job as completed
        supabase_service.update_job(job_id, {
            'status': 'completed',
            'progress': 100,
            'result_json': {
                'prompts_generated': len(visual_prompts),
                'completion_time': str(datetime.now())
            },
            'payload_json': {
                'project_id': project_id,
                'completed_prompts': len(visual_prompts),
                'total_prompts': len(visual_prompts),
                'stage': 'completed'
            }
        })

        print(f"✅ Visual prompt generation completed: {len(visual_prompts)} prompts")

    except Exception as e:
        # Mark job as failed
        supabase_service.update_job(job_id, {
            'status': 'failed',
            'progress': 0,
            'error': str(e),
            'payload_json': {
                'project_id': project_id,
                'completed_prompts': 0,
                'stage': 'failed'
            }
        })
        print(f"❌ Visual prompt generation failed: {str(e)}")


@router.post("/projects/{project_id}/scenes/select", response_model=schemas.SceneGenerationJobResponse)
async def start_scene_generation(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    """Start scene selection and parallel visual prompt generation."""
    try:
        # Check if project exists and belongs to user
        project = supabase_service.get_project(project_id)
        if project and project.get('user_id') != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Project does not belong to user"
            )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        if not project.get('transcription_data'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project has no transcription data. Complete transcription first."
            )

        # Check if already processing or completed
        current_status = project.get('status', 'created')
        if current_status in ['scenes_processing', 'scenes_completed']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project scenes already {current_status.replace('_', ' ')}"
            )

        # Create scene selection job in database
        job_data = {
            'project_id': str(project_id),
            'type': 'select_scenes',
            'status': 'pending',
            'progress': 0,
            'payload_json': {
                'project_id': str(project_id),
                'stage': 'initializing'
            }
        }
        job = supabase_service.create_job(job_data)
        job_id = job['id']

        # Update project status
        update_data = {'status': 'scenes_processing'}
        supabase_service.update_project(project_id, update_data)

        # Start background scene selection
        background_tasks.add_task(
            scene_selection_task,
            str(project_id),
            job_id
        )

        return schemas.SceneGenerationJobResponse(
            job_id=job_id,
            status='started',
            estimated_duration=60.0  # ~1 minute for scene selection + parallel prompts
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start scene generation: {str(e)}"
        )


@router.post("/projects/{project_id}/scenes/generate-prompts", response_model=schemas.SceneGenerationJobResponse)
async def retry_visual_prompt_generation(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    """Retry visual prompt generation for existing scenes."""
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

        # Verify scenes exist
        scenes_count = project.get('scenes_count', 0)
        if scenes_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No scenes exist yet. Run scene selection first."
            )

        # Check for existing running visual prompt jobs
        existing_jobs = supabase_service.client.table('jobs')\
            .select('*')\
            .eq('project_id', str(project_id))\
            .eq('type', 'generate_visual_prompts')\
            .eq('status', 'running')\
            .execute()

        if existing_jobs.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Visual prompt generation is already running for this project"
            )

        # Create new visual prompt generation job
        job_data = {
            'project_id': str(project_id),
            'type': 'generate_visual_prompts',
            'status': 'pending',
            'progress': 0,
            'payload_json': {
                'project_id': str(project_id),
                'stage': 'initializing',
                'completed_prompts': 0,
                'total_prompts': scenes_count
            }
        }
        job = supabase_service.create_job(job_data)
        job_id = job['id']

        # Update project status if needed
        if project.get('status') != 'scenes_processing':
            supabase_service.update_project(project_id, {'status': 'scenes_processing'})

        # Start background visual prompt generation task
        background_tasks.add_task(
            visual_prompt_generation_task,
            str(project_id),
            job_id
        )

        return schemas.SceneGenerationJobResponse(
            job_id=job_id,
            status='started',
            estimated_duration=30.0  # ~30 seconds for visual prompt generation only
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start visual prompt generation: {str(e)}"
        )


@router.get("/projects/{project_id}/scenes", response_model=schemas.ProjectScenesResponse)
async def get_project_scenes(
    project_id: UUID,
    user_id: str = Depends(get_current_user)
):
    """Get all scenes and their visual prompts for a project."""
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

        # Get scenes from database
        scenes = supabase_service.get_project_scenes(project_id)

        # Convert to response format
        scene_responses = []
        completed_prompts = 0

        for scene in scenes:
            visual_prompt_data = scene.get('visual_prompt_data')
            prompt_status = scene.get('prompt_status', 'pending')

            if prompt_status == 'completed' and visual_prompt_data:
                completed_prompts += 1
                visual_prompt = schemas.VisualPrompt(**visual_prompt_data)
            else:
                visual_prompt = None

            scene_response = schemas.SceneWithPrompt(
                scene_id=scene['scene_id'],
                title=scene['title'],
                start_time=scene['start_time'],
                end_time=scene['end_time'],
                duration=scene['duration'],
                lyrics_excerpt=scene['lyric_excerpt'],
                theme=scene['theme'],
                energy_level=scene['energy_level'],
                visual_potential=scene['visual_potential'],
                narrative_importance=scene['narrative_importance'],
                reasoning=scene['reasoning'],
                visual_prompt=visual_prompt,
                prompt_status=prompt_status
            )
            scene_responses.append(scene_response)

        return schemas.ProjectScenesResponse(
            project_id=str(project_id),
            status=project.get('status', 'created'),
            scenes=scene_responses,
            completed_prompts=completed_prompts,
            total_prompts=len(scenes)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting project scenes: {str(e)}"
        )


@router.get("/scenes/jobs/{job_id}/status", response_model=schemas.SceneGenerationStatusResponse)
async def get_scene_generation_status(
    job_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get real-time scene generation progress."""
    try:
        job = supabase_service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scene generation job not found"
            )

        # Verify job belongs to user through project ownership
        payload = job.get('payload_json', {})
        project_id = payload.get('project_id')
        if project_id:
            project = supabase_service.get_project(UUID(project_id))
            if project and project.get('user_id') != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Job does not belong to user"
                )

        # Extract payload data
        payload = job.get('payload_json', {})
        
        return schemas.SceneGenerationStatusResponse(
            job_id=job_id,
            status=job['status'],
            progress=job.get('progress', 0) / 100.0,  # Convert to 0-1 scale
            completed_prompts=payload.get('completed_prompts', 0),
            total_prompts=payload.get('total_prompts', 0),
            error_message=job.get('error')
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting job status: {str(e)}"
        )


@router.put("/projects/{project_id}/scenes/{scene_id}/regenerate", response_model=schemas.VisualPrompt)
async def regenerate_scene_prompt(
    project_id: UUID,
    scene_id: int,
    user_id: str = Depends(get_current_user)
):
    """Regenerate visual prompt for a specific scene."""
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

        # Get the specific scene
        scenes = supabase_service.get_project_scenes(project_id)
        target_scene = None
        for scene in scenes:
            if scene['scene_id'] == scene_id:
                target_scene = scene
                break

        if not target_scene:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scene not found"
            )

        # Convert to SceneSelection format for regeneration
        scene_selection = schemas.SceneSelection(
            scene_id=target_scene['scene_id'],
            title=target_scene['title'],
            start_time=target_scene['start_time'],
            end_time=target_scene['end_time'],
            duration=target_scene['duration'],
            lyrics_excerpt=target_scene['lyric_excerpt'],
            theme=target_scene['theme'],
            energy_level=target_scene['energy_level'],
            visual_potential=target_scene['visual_potential'],
            narrative_importance=target_scene['narrative_importance'],
            reasoning=target_scene['reasoning']
        )

        song_metadata = {
            'title': project.get('name', 'Unknown'),
            'artist': project.get('artist', 'Unknown'),
            'genre': project.get('genre', 'Unknown')
        }

        # Get artist reference images from project
        artist_reference_images = project.get('selected_reference_images', {})

        # Generate new prompt with artist references
        new_prompt = await openrouter_service.generate_individual_visual_prompt_with_artist(
            scene=scene_selection,
            artist_reference_images=artist_reference_images,
            song_metadata=song_metadata
        )

        # Update in database
        supabase_service.client.table('selected_scenes')\
            .update({
                'visual_prompt_data': new_prompt.model_dump(),
                'prompt_status': 'completed'
            })\
            .eq('project_id', str(project_id))\
            .eq('scene_id', scene_id)\
            .execute()

        return new_prompt

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate scene prompt: {str(e)}"
        )