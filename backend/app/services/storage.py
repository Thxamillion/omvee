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

    def _ensure_bucket_exists(self) -> bool:
        """
        Ensure the storage bucket exists. Create it if it doesn't exist.

        Returns:
            True if bucket exists or was created successfully
        """
        try:
            # Try to list objects in the bucket to check if it exists
            list_result = self.supabase.storage.from_(self.bucket_name).list()
            print(f"Bucket '{self.bucket_name}' exists. List result type: {type(list_result)}")
            print(f"List result: {list_result}")
            return True
        except Exception as list_error:
            print(f"Failed to list bucket '{self.bucket_name}': {list_error}")
            # Bucket might not exist, try to create it
            try:
                print(f"Attempting to create bucket '{self.bucket_name}'...")
                result = self.supabase.storage.create_bucket(self.bucket_name, {"public": True})
                print(f"Create bucket result: {result}")
                return True
            except Exception as create_error:
                print(f"Failed to create bucket '{self.bucket_name}': {create_error}")
                return False

    def test_bucket_access(self) -> dict:
        """
        Test bucket access and return detailed information for debugging.

        Returns:
            Dictionary with test results
        """
        from io import BytesIO

        test_results = {
            "bucket_name": self.bucket_name,
            "exists": False,
            "can_list": False,
            "can_upload": False,
            "error": None
        }

        try:
            # Test bucket listing
            list_result = self.supabase.storage.from_(self.bucket_name).list()
            test_results["exists"] = True
            test_results["can_list"] = True
            test_results["list_result"] = str(list_result)

            # Test small upload
            test_content = b"test content"
            test_path = "test_upload.txt"

            try:
                upload_result = self.supabase.storage.from_(self.bucket_name).upload(
                    file=test_content,
                    path=test_path,
                    file_options={"upsert": "true"}
                )

                # Handle boolean return value properly
                if isinstance(upload_result, bool):
                    test_results["can_upload"] = upload_result
                    test_results["upload_result_type"] = "bool"
                    test_results["upload_result"] = str(upload_result)
                else:
                    test_results["can_upload"] = True
                    test_results["upload_result_type"] = str(type(upload_result))
                    test_results["upload_result"] = str(upload_result)

            except Exception as upload_error:
                test_results["can_upload"] = False
                test_results["upload_error"] = str(upload_error)

            # Clean up test file
            try:
                self.supabase.storage.from_(self.bucket_name).remove([test_path])
            except:
                pass

        except Exception as e:
            test_results["error"] = str(e)

        return test_results

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

        # Ensure bucket exists
        if not self._ensure_bucket_exists():
            raise HTTPException(
                status_code=500,
                detail=f"Storage bucket '{self.bucket_name}' is not available. Please contact support."
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
                print(f"Attempting upload to bucket '{self.bucket_name}', path: '{file_path}'")
                print(f"File content type: {image_file.content_type}, size: {len(processed_content)} bytes")

                try:
                    # Use bytes directly as per Supabase Python client requirements
                    result = self.supabase.storage.from_(self.bucket_name).upload(
                        file=processed_content,
                        path=file_path,
                        file_options={
                            "content-type": image_file.content_type,
                            "cache-control": "3600",
                            "upsert": "true"  # String value as per docs
                        }
                    )

                    print(f"Upload result type: {type(result)}")
                    print(f"Upload result: {result}")

                except Exception as upload_error:
                    print(f"Upload exception: {type(upload_error).__name__}: {upload_error}")
                    print(f"Full error details: {upload_error}")
                    raise Exception(f"Upload failed with exception: {upload_error}")

                # Handle successful upload results
                print(f"Upload result type: {type(result)}")
                print(f"Upload result: {result}")

                # Different Supabase client versions return different result types
                if isinstance(result, bool):
                    if result:
                        print("Upload returned True - upload successful")
                    else:
                        raise Exception(f"Upload failed: Storage service returned False")
                elif hasattr(result, 'status_code'):
                    print(f"Status code: {result.status_code}")
                    if result.status_code not in [200, 201]:
                        raise Exception(f"Upload failed with status {result.status_code}: {result}")
                elif hasattr(result, 'error') and result.error:
                    raise Exception(f"Upload failed with error: {result.error}")
                else:
                    print("Upload completed, assuming success...")

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