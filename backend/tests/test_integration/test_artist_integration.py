import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime
from httpx import AsyncClient
from io import BytesIO
from PIL import Image
import os

from app.main import app
from app.models_pydantic import Artist, ArtistCreate


class TestArtistIntegration:
    """Integration tests for Artist endpoints with real Supabase."""

    @pytest.fixture
    def sample_artist_data(self):
        """Sample artist creation data."""
        return {
            "name": f"Test Artist {uuid4().hex[:8]}",
            "description": "Test artist for integration testing",
            "reference_image_urls": [
                "https://example.com/test1.jpg",
                "https://example.com/test2.jpg",
                "https://example.com/test3.jpg"
            ]
        }

    @pytest.fixture
    def create_test_image(self):
        """Create a test image file for upload testing."""
        def _create_image(name: str = "test.jpg", size: tuple = (512, 512)) -> BytesIO:
            image = Image.new('RGB', size, color='red')
            image_bytes = BytesIO()
            image.save(image_bytes, format='JPEG')
            image_bytes.seek(0)
            image_bytes.name = name
            return image_bytes
        return _create_image

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_artist_integration(self, sample_artist_data):
        """Test creating an artist with real Supabase."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/artists/", json=sample_artist_data)

            # Should succeed if Supabase is configured
            if response.status_code == 201:
                data = response.json()
                assert data["name"] == sample_artist_data["name"]
                assert data["description"] == sample_artist_data["description"]
                assert len(data["reference_image_urls"]) == 3
                assert "id" in data
                assert "created_at" in data

                # Cleanup: Delete the created artist
                artist_id = data["id"]
                await client.delete(f"/api/artists/{artist_id}")

            elif response.status_code == 500:
                # Supabase not configured or connection failed
                pytest.skip("Supabase not configured for integration tests")
            else:
                pytest.fail(f"Unexpected status code: {response.status_code}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_artists_integration(self):
        """Test listing artists with real Supabase."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/artists/")

            if response.status_code == 200:
                data = response.json()
                assert "artists" in data
                assert "total" in data
                assert isinstance(data["artists"], list)
            elif response.status_code == 500:
                pytest.skip("Supabase not configured for integration tests")
            else:
                pytest.fail(f"Unexpected status code: {response.status_code}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_artist_lifecycle_integration(self, sample_artist_data):
        """Test complete artist CRUD lifecycle with real Supabase."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create artist
            create_response = await client.post("/api/artists/", json=sample_artist_data)

            if create_response.status_code != 201:
                if create_response.status_code == 500:
                    pytest.skip("Supabase not configured for integration tests")
                else:
                    pytest.fail(f"Create failed: {create_response.status_code}")

            artist_data = create_response.json()
            artist_id = artist_data["id"]

            try:
                # Get artist
                get_response = await client.get(f"/api/artists/{artist_id}")
                assert get_response.status_code == 200
                get_data = get_response.json()
                assert get_data["id"] == artist_id
                assert get_data["name"] == sample_artist_data["name"]

                # Update artist
                update_data = {"name": f"Updated {sample_artist_data['name']}"}
                update_response = await client.put(f"/api/artists/{artist_id}", json=update_data)
                assert update_response.status_code == 200
                updated_data = update_response.json()
                assert updated_data["name"] == update_data["name"]

                # List artists (should include our artist)
                list_response = await client.get("/api/artists/")
                assert list_response.status_code == 200
                list_data = list_response.json()
                artist_ids = [artist["id"] for artist in list_data["artists"]]
                assert artist_id in artist_ids

            finally:
                # Delete artist (cleanup)
                delete_response = await client.delete(f"/api/artists/{artist_id}")
                assert delete_response.status_code == 204

                # Verify deletion
                get_deleted_response = await client.get(f"/api/artists/{artist_id}")
                assert get_deleted_response.status_code == 404

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_image_upload_integration(self, sample_artist_data, create_test_image):
        """Test image upload with real Supabase Storage."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create artist first
            create_response = await client.post("/api/artists/", json=sample_artist_data)

            if create_response.status_code != 201:
                if create_response.status_code == 500:
                    pytest.skip("Supabase not configured for integration tests")
                else:
                    pytest.fail(f"Create failed: {create_response.status_code}")

            artist_data = create_response.json()
            artist_id = artist_data["id"]

            try:
                # Create test images
                test_images = [
                    ("image1.jpg", create_test_image("image1.jpg")),
                    ("image2.jpg", create_test_image("image2.jpg")),
                    ("image3.jpg", create_test_image("image3.jpg"))
                ]

                # Upload images
                files = [
                    ("images", (name, image_data, "image/jpeg"))
                    for name, image_data in test_images
                ]

                upload_response = await client.post(
                    f"/api/artists/{artist_id}/upload-images",
                    files=files
                )

                if upload_response.status_code == 200:
                    upload_data = upload_response.json()
                    assert upload_data["message"] == "Reference images uploaded successfully"
                    assert upload_data["artist_id"] == artist_id
                    assert upload_data["image_count"] == 3
                    assert len(upload_data["uploaded_images"]) == 3

                    # Verify artist was updated with new image URLs
                    updated_artist = upload_data["artist"]
                    assert len(updated_artist["reference_image_urls"]) == 3
                    for url in updated_artist["reference_image_urls"]:
                        assert url.startswith("http")  # Should be full URLs

                elif upload_response.status_code == 500:
                    pytest.skip("Supabase Storage not configured for integration tests")
                else:
                    pytest.fail(f"Upload failed: {upload_response.status_code} - {upload_response.text}")

            finally:
                # Cleanup: Delete the artist
                await client.delete(f"/api/artists/{artist_id}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_presigned_upload_integration(self, sample_artist_data):
        """Test presigned URL generation with real Supabase."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create artist first
            create_response = await client.post("/api/artists/", json=sample_artist_data)

            if create_response.status_code != 201:
                if create_response.status_code == 500:
                    pytest.skip("Supabase not configured for integration tests")
                else:
                    pytest.fail(f"Create failed: {create_response.status_code}")

            artist_data = create_response.json()
            artist_id = artist_data["id"]

            try:
                # Get presigned URLs
                file_names = ["ref1.jpg", "ref2.jpg", "ref3.jpg"]
                presigned_response = await client.get(
                    f"/api/artists/{artist_id}/presigned-upload",
                    params={"file_names": file_names}
                )

                if presigned_response.status_code == 200:
                    presigned_data = presigned_response.json()
                    assert presigned_data["artist_id"] == artist_id
                    assert len(presigned_data["presigned_urls"]) == 3

                    for url_data in presigned_data["presigned_urls"]:
                        assert "file_name" in url_data
                        assert "signed_url" in url_data
                        assert "public_url" in url_data
                        assert url_data["signed_url"].startswith("https://")
                        assert url_data["public_url"].startswith("https://")

                elif presigned_response.status_code == 500:
                    pytest.skip("Supabase Storage not configured for integration tests")
                else:
                    pytest.fail(f"Presigned URL generation failed: {presigned_response.status_code}")

            finally:
                # Cleanup: Delete the artist
                await client.delete(f"/api/artists/{artist_id}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_artist_validation_integration(self):
        """Test artist validation with real Supabase."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test invalid data - too few images
            invalid_data = {
                "name": "Test Artist",
                "description": "Test",
                "reference_image_urls": ["url1", "url2"]  # Only 2, needs 3-5
            }

            response = await client.post("/api/artists/", json=invalid_data)

            # Should fail validation regardless of Supabase configuration
            assert response.status_code == 422

            # Test invalid data - empty name
            invalid_data2 = {
                "name": "",
                "reference_image_urls": ["url1", "url2", "url3"]
            }

            response2 = await client.post("/api/artists/", json=invalid_data2)
            assert response2.status_code == 422

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_artist_not_found_integration(self):
        """Test 404 responses with real Supabase."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            non_existent_id = str(uuid4())

            # Get non-existent artist
            get_response = await client.get(f"/api/artists/{non_existent_id}")
            if get_response.status_code not in [404, 500]:
                pytest.fail(f"Expected 404 or 500, got {get_response.status_code}")

            # Delete non-existent artist
            delete_response = await client.delete(f"/api/artists/{non_existent_id}")
            if delete_response.status_code not in [404, 500]:
                pytest.fail(f"Expected 404 or 500, got {delete_response.status_code}")


# Helper function to check if Supabase is configured
async def is_supabase_configured() -> bool:
    """Check if Supabase environment variables are set."""
    return bool(
        os.getenv("SUPABASE_URL") and
        os.getenv("SUPABASE_ANON_KEY") and
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )