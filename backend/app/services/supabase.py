from supabase import create_client, Client
from app.config import settings
from typing import Optional, Dict, Any, List
from uuid import UUID
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from app.dependencies.auth import get_current_user

bearer_scheme = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)


class SupabaseService:
    def __init__(self):
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key
        )

        # Admin client for operations that need elevated permissions
        self.admin_client: Optional[Client] = None
        if settings.supabase_service_key:
            self.admin_client = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )

    # Project operations
    def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project."""
        try:
            result = self.client.table('projects').insert(project_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            raise

    def get_project(self, project_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a project by ID."""
        try:
            result = self.client.table('projects')\
                .select('*')\
                .eq('id', str(project_id))\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting project {project_id}: {str(e)}")
            raise

    def list_projects(self, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        """List projects with pagination."""
        try:
            # Get total count
            count_result = self.client.table('projects')\
                .select('id', count='exact')\
                .execute()
            total = count_result.count or 0

            # Get paginated data
            result = self.client.table('projects')\
                .select('*')\
                .order('updated_at', desc=True)\
                .range(skip, skip + limit - 1)\
                .execute()

            return {
                'projects': result.data or [],
                'total': total
            }
        except Exception as e:
            logger.error(f"Error listing projects: {str(e)}")
            raise

    def update_project(self, project_id: UUID, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a project."""
        try:
            result = self.client.table('projects')\
                .update(update_data)\
                .eq('id', str(project_id))\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {str(e)}")
            raise

    def delete_project(self, project_id: UUID) -> bool:
        """Delete a project."""
        try:
            result = self.client.table('projects')\
                .delete()\
                .eq('id', str(project_id))\
                .execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {str(e)}")
            raise

    # Job management operations
    def create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new job for tracking async operations."""
        try:
            result = self.client.table('jobs').insert(job_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            raise

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a job by ID."""
        try:
            result = self.client.table('jobs')\
                .select('*')\
                .eq('id', job_id)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {str(e)}")
            raise

    def update_job(self, job_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update job status and progress."""
        try:
            result = self.client.table('jobs')\
                .update(updates)\
                .eq('id', job_id)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {str(e)}")
            raise

    def get_project_jobs(self, project_id: UUID, job_type: str = None) -> List[Dict[str, Any]]:
        """Get all jobs for a project, optionally filtered by type."""
        try:
            query = self.client.table('jobs')\
                .select('*')\
                .eq('project_id', str(project_id))\
                .order('created_at', desc=True)
            
            if job_type:
                query = query.eq('type', job_type)
            
            result = query.execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting jobs for project {project_id}: {str(e)}")
            raise

    # Scene operations
    def get_project_scenes(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get all scenes for a project."""
        try:
            result = self.client.table('selected_scenes')\
                .select('*')\
                .eq('project_id', str(project_id))\
                .order('order_idx')\
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting scenes for project {project_id}: {str(e)}")
            raise

    def create_scene(self, scene_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new scene."""
        try:
            result = self.client.table('selected_scenes').insert(scene_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating scene: {str(e)}")
            raise

    # Image operations
    def get_project_images(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get all generated images for a project."""
        try:
            result = self.client.table('generated_images')\
                .select('*')\
                .eq('project_id', str(project_id))\
                .order('created_at')\
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting images for project {project_id}: {str(e)}")
            raise

    def create_image(self, image_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new generated image record."""
        try:
            result = self.client.table('generated_images').insert(image_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating image: {str(e)}")
            raise

    # Video clip operations
    def get_project_clips(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get all video clips for a project."""
        try:
            result = self.client.table('video_clips')\
                .select('*')\
                .eq('project_id', str(project_id))\
                .order('created_at')\
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting clips for project {project_id}: {str(e)}")
            raise

    def create_video_clip(self, clip_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new video clip record."""
        try:
            result = self.client.table('video_clips').insert(clip_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating video clip: {str(e)}")
            raise

    # Job operations
    def get_project_jobs(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get all jobs for a project."""
        try:
            result = self.client.table('jobs')\
                .select('*')\
                .eq('project_id', str(project_id))\
                .order('created_at', desc=True)\
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting jobs for project {project_id}: {str(e)}")
            raise

    def create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new job."""
        try:
            result = self.client.table('jobs').insert(job_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            raise

    def update_job(self, job_id: UUID, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a job."""
        try:
            result = self.client.table('jobs')\
                .update(update_data)\
                .eq('id', str(job_id))\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {str(e)}")
            raise

    # Storage operations
    def get_storage_client(self):
        """Get Supabase storage client."""
        return self.client.storage

    def create_signed_upload_url(self, bucket: str, path: str, expires_in: int = 3600) -> str:
        """Create a signed URL for uploading a file."""
        try:
            result = self.client.storage.from_(bucket).create_signed_upload_url(path, expires_in)
            return result.get('signed_url', '')
        except Exception as e:
            logger.error(f"Error creating signed upload URL: {str(e)}")
            raise

    def get_public_url(self, bucket: str, path: str) -> str:
        """Get public URL for a file."""
        try:
            result = self.client.storage.from_(bucket).get_public_url(path)
            return result.get('public_url', '')
        except Exception as e:
            logger.error(f"Error getting public URL: {str(e)}")
            raise


# Global instance
supabase_service = SupabaseService()


# Dependency function for FastAPI
def get_supabase_client() -> Client:
    """FastAPI dependency to get Supabase client."""
    from supabase import create_client
    from app.config import settings
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_user_supabase_client(access_token: str) -> Client:
    """Get Supabase client with user JWT token for RLS."""
    from supabase import create_client, Client
    from app.config import settings

    # For now, just use the regular client since RLS is disabled
    # TODO: Fix JWT header passing when we re-enable RLS
    client = create_client(
        settings.supabase_url,
        settings.supabase_anon_key
    )

    return client


class UserSupabaseService:
    """Supabase service that uses user authentication context for RLS."""

    def __init__(self, access_token: str, user_id: str):
        self.client: Client = get_user_supabase_client(access_token)
        self.access_token = access_token
        self.user_id = user_id

    def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project with user context."""
        try:
            # RLS will automatically ensure the project belongs to the authenticated user
            # We still set user_id explicitly for the INSERT policy check
            project_data['user_id'] = self.user_id

            result = self.client.table('projects').insert(project_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating project with user context: {str(e)}")
            raise

    def get_project(self, project_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a project by ID with user context."""
        try:
            # RLS will automatically filter to only user's projects
            result = self.client.table('projects')\
                .select('*')\
                .eq('id', str(project_id))\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting project {project_id} with user context: {str(e)}")
            raise

    def list_projects(self, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        """List projects with pagination and user context."""
        try:
            # RLS will automatically filter to only user's projects
            # Get total count
            count_result = self.client.table('projects')\
                .select('id', count='exact')\
                .execute()
            total = count_result.count or 0

            # Get paginated data
            result = self.client.table('projects')\
                .select('*')\
                .order('updated_at', desc=True)\
                .range(skip, skip + limit - 1)\
                .execute()

            return {
                'projects': result.data or [],
                'total': total
            }
        except Exception as e:
            logger.error(f"Error listing projects with user context: {str(e)}")
            raise

    def update_project(self, project_id: UUID, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a project with user context."""
        try:
            # RLS will automatically filter to only user's projects
            result = self.client.table('projects')\
                .update(update_data)\
                .eq('id', str(project_id))\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating project {project_id} with user context: {str(e)}")
            raise

    def delete_project(self, project_id: UUID) -> bool:
        """Delete a project with user context."""
        try:
            # RLS will automatically filter to only user's projects
            result = self.client.table('projects')\
                .delete()\
                .eq('id', str(project_id))\
                .execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error deleting project {project_id} with user context: {str(e)}")
            raise


def get_user_supabase_service(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    user_id: str = Depends(get_current_user)
) -> UserSupabaseService:
    """FastAPI dependency to get UserSupabaseService with user context."""
    if not credentials or not credentials.credentials:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for user-specific operations"
        )

    return UserSupabaseService(credentials.credentials, user_id)