from supabase import create_client, Client
from app.config import settings
from typing import Optional, Dict, Any, List
from uuid import UUID
import logging

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
            return result.get('signedURL', '')
        except Exception as e:
            logger.error(f"Error creating signed upload URL: {str(e)}")
            raise

    def get_public_url(self, bucket: str, path: str) -> str:
        """Get public URL for a file."""
        try:
            result = self.client.storage.from_(bucket).get_public_url(path)
            return result.get('publicURL', '')
        except Exception as e:
            logger.error(f"Error getting public URL: {str(e)}")
            raise


# Global instance
supabase_service = SupabaseService()