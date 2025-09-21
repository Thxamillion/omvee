from typing import List, Optional, Dict, Any
from uuid import UUID
import os
from io import BytesIO
from PIL import Image

from supabase import Client
from fastapi import UploadFile, HTTPException


class StorageService:
    """Service for handling file uploads to Supabase Storage."""

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.bucket_name = "project-files"  # Must match your Supabase bucket name

    async def upload_artist_reference_images(
        self,
        artist_id: UUID,
        image_files: List[UploadFile]
    ) -> List[str]:
        """
        Upload artist reference images to Supabase Storage.

        Args:
            artist_id: UUID of the artist
            image_files: List of uploaded image files (3-5 files)

        Returns:
            List of public URLs for uploaded images

        Raises:
            HTTPException: If upload fails or validation errors
        """
        # Validate number of images
        if not 3 <= len(image_files) <= 5:
            raise HTTPException(
                status_code=422,
                detail="Must upload between 3 and 5 reference images"
            )

        uploaded_urls = []

        try:
            for i, image_file in enumerate(image_files):
                # Validate file type
                if not image_file.content_type.startswith('image/'):
                    raise HTTPException(
                        status_code=422,
                        detail=f"File {image_file.filename} is not an image"
                    )

                # Validate file size (max 10MB)
                if image_file.size > 10 * 1024 * 1024:
                    raise HTTPException(
                        status_code=422,
                        detail=f"File {image_file.filename} is too large (max 10MB)"
                    )

                # Generate file path
                file_extension = image_file.filename.split('.')[-1].lower()
                file_path = f"artists/{artist_id}/reference_{i+1}.{file_extension}"

                # Read file content
                file_content = await image_file.read()

                # Optional: Resize image for consistency (e.g., max 1024x1024)
                processed_content = self._process_image(file_content, max_size=(1024, 1024))

                # Upload to Supabase Storage
                result = self.supabase.storage.from_(self.bucket_name).upload(
                    path=file_path,
                    file=processed_content,
                    file_options={
                        "content-type": image_file.content_type,
                        "cache-control": "3600",
                        "upsert": True  # Allow overwriting existing files
                    }
                )

                if result.status_code not in [200, 201]:
                    raise Exception(f"Upload failed: {result}")

                # Get public URL
                public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(file_path)
                uploaded_urls.append(public_url)

                # Reset file pointer for next iteration
                await image_file.seek(0)

            return uploaded_urls

        except HTTPException:
            # Clean up any successfully uploaded files if there was an error
            await self._cleanup_uploaded_files(artist_id, len(uploaded_urls))
            raise
        except Exception as e:
            # Clean up any successfully uploaded files if there was an error
            await self._cleanup_uploaded_files(artist_id, len(uploaded_urls))
            raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

    def _process_image(self, image_content: bytes, max_size: tuple = (1024, 1024)) -> bytes:
        """
        Process image to ensure consistent size and format.

        Args:
            image_content: Raw image bytes
            max_size: Maximum dimensions (width, height)

        Returns:
            Processed image bytes
        """
        try:
            # Open image
            image = Image.open(BytesIO(image_content))

            # Convert to RGB if necessary (handles RGBA, etc.)
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Resize if too large (maintain aspect ratio)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Save to bytes
            output = BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()

        except Exception:
            # If processing fails, return original content
            return image_content

    async def _cleanup_uploaded_files(self, artist_id: UUID, num_files: int):
        """Clean up uploaded files if there was an error."""
        try:
            for i in range(num_files):
                file_path = f"artists/{artist_id}/reference_{i+1}.jpg"
                self.supabase.storage.from_(self.bucket_name).remove([file_path])
        except Exception:
            # Ignore cleanup errors
            pass

    async def delete_artist_reference_images(self, artist_id: UUID) -> bool:
        """
        Delete all reference images for an artist.

        Args:
            artist_id: UUID of the artist

        Returns:
            True if deletion successful
        """
        try:
            # List all files for the artist
            result = self.supabase.storage.from_(self.bucket_name).list(f"artists/{artist_id}")

            if result:
                file_paths = [f"artists/{artist_id}/{file['name']}" for file in result]
                self.supabase.storage.from_(self.bucket_name).remove(file_paths)

            return True

        except Exception as e:
            print(f"Error deleting artist images: {e}")
            return False

    async def get_presigned_upload_url(
        self,
        artist_id: UUID,
        file_name: str,
        expires_in: int = 3600
    ) -> Dict[str, str]:
        """
        Generate presigned URL for client-side upload.

        Args:
            artist_id: UUID of the artist
            file_name: Name of the file to upload
            expires_in: URL expiration time in seconds

        Returns:
            Dictionary with presigned URL and file path
        """
        try:
            file_path = f"artists/{artist_id}/{file_name}"

            # Generate presigned URL for upload
            result = self.supabase.storage.from_(self.bucket_name).create_signed_upload_url(
                path=file_path,
                expires_in=expires_in
            )

            return {
                "signed_url": result["signedURL"],
                "file_path": file_path,
                "public_url": self.supabase.storage.from_(self.bucket_name).get_public_url(file_path),
                "expires_in": expires_in
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate presigned URL: {e}")

    async def validate_image_file(self, file: UploadFile) -> bool:
        """
        Validate uploaded image file.

        Args:
            file: Uploaded file to validate

        Returns:
            True if valid image file
        """
        # Check content type
        if not file.content_type.startswith('image/'):
            return False

        # Check file size (max 10MB)
        if file.size > 10 * 1024 * 1024:
            return False

        # Check file extension
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            return False

        return True