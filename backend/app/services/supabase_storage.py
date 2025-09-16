from app.services.supabase import supabase_service
from typing import Dict, Any
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class SupabaseStorageService:
    def __init__(self):
        self.storage = supabase_service.get_storage_client()

    def create_upload_url(
        self,
        project_id: UUID,
        filename: str,
        content_type: str,
        expires_in: int = 3600
    ) -> Dict[str, Any]:
        """Create a signed upload URL for Supabase Storage."""

        # Define bucket (you'll need to create this in Supabase)
        bucket_name = "project-files"

        # Create organized file path
        file_extension = filename.split('.')[-1] if '.' in filename else ''
        file_path = f"{project_id}/audio/{filename}"

        try:
            # Create signed upload URL
            signed_url = self.storage.from_(bucket_name).create_signed_upload_url(
                file_path,
                expires_in
            )

            # Get public URL for later access
            public_url = self.storage.from_(bucket_name).get_public_url(file_path)

            return {
                'signed_url': signed_url.get('signedURL', ''),
                'file_path': file_path,
                'public_url': public_url.get('publicURL', ''),
                'bucket': bucket_name
            }

        except Exception as e:
            logger.error(f"Error creating upload URL: {str(e)}")
            raise Exception(f"Failed to create upload URL: {str(e)}")

    def get_public_url(self, bucket: str, file_path: str) -> str:
        """Get public URL for a file."""
        try:
            result = self.storage.from_(bucket).get_public_url(file_path)
            return result.get('publicURL', '')
        except Exception as e:
            logger.error(f"Error getting public URL: {str(e)}")
            raise

    def delete_file(self, bucket: str, file_path: str) -> bool:
        """Delete a file from storage."""
        try:
            result = self.storage.from_(bucket).remove([file_path])
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False

    def list_files(self, bucket: str, folder: str = "") -> list:
        """List files in a bucket/folder."""
        try:
            result = self.storage.from_(bucket).list(folder)
            return result.data or []
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return []


# Global instance
supabase_storage_service = SupabaseStorageService()