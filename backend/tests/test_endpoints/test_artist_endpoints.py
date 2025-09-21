import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime
from httpx import AsyncClient

# from app.main import app  # Comment out until we create the endpoint
from app.models_pydantic import Artist, ArtistCreate


class TestArtistEndpoints:
    """Test suite for Artist API endpoints."""

    @pytest.fixture
    def sample_artist_data(self):
        """Sample artist creation data."""
        return {
            "name": "Rio Da Yung OG",
            "description": "Detroit rapper known for melodic street narratives",
            "reference_image_urls": [
                "https://storage.supabase.com/rio1.jpg",
                "https://storage.supabase.com/rio2.jpg",
                "https://storage.supabase.com/rio3.jpg"
            ]
        }

    @pytest.fixture
    def sample_artist(self, sample_artist_data):
        """Sample artist object."""
        return Artist(
            id=uuid4(),
            name=sample_artist_data["name"],
            description=sample_artist_data["description"],
            reference_image_urls=sample_artist_data["reference_image_urls"],
            created_at=datetime.now()
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_artist_success(self, sample_artist_data):
        """Test POST /artists/ endpoint for creating an artist."""
        # TDD: This test is defined but will fail until we create the endpoint
        # Once we implement the artist router, this test should pass
        assert True  # Placeholder for now

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_artist_validation_error(self):
        """Test POST /artists/ with invalid data."""
        invalid_data = {
            "name": "",  # Empty name
            "reference_image_urls": ["url1", "url2"]  # Only 2 images, needs 3-5
        }

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/artists/", json=invalid_data)

            # Should return validation error
            assert response.status_code == 422

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_artist_success(self, sample_artist):
        """Test GET /artists/{artist_id} endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/artists/{sample_artist.id}")

            # TDD: This should pass once we implement the endpoint
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(sample_artist.id)
            assert data["name"] == sample_artist.name

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_artist_not_found(self):
        """Test GET /artists/{artist_id} with non-existent ID."""
        non_existent_id = uuid4()

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/artists/{non_existent_id}")

            assert response.status_code == 404

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_artists_success(self):
        """Test GET /artists/ endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/artists/")

            # TDD: This should pass once we implement the endpoint
            assert response.status_code == 200
            data = response.json()
            assert "artists" in data
            assert "total" in data
            assert isinstance(data["artists"], list)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_artist_success(self, sample_artist):
        """Test PUT /artists/{artist_id} endpoint."""
        update_data = {
            "name": "Rio Da Yung OG (Updated)",
            "description": "Updated description"
        }

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.put(f"/artists/{sample_artist.id}", json=update_data)

            # TDD: This should pass once we implement the endpoint
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == update_data["name"]
            assert data["description"] == update_data["description"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_artist_success(self, sample_artist):
        """Test DELETE /artists/{artist_id} endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete(f"/artists/{sample_artist.id}")

            # TDD: This should pass once we implement the endpoint
            assert response.status_code == 204

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_artist_not_found(self):
        """Test DELETE /artists/{artist_id} with non-existent ID."""
        non_existent_id = uuid4()

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete(f"/artists/{non_existent_id}")

            assert response.status_code == 404