import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime
from typing import List, Dict, Any

from app.models_pydantic import Artist, ArtistCreate, VisualPrompt, SceneSelection
from app.services.artist import ArtistService


class TestArtistService:
    """Test suite for Artist service database operations."""

    @pytest.fixture
    def sample_artist_data(self):
        """Sample artist creation data."""
        return {
            "name": "Rio Da Yung OG",
            "description": "Detroit rapper known for melodic street narratives",
            "reference_image_urls": [
                "https://example.com/rio1.jpg",
                "https://example.com/rio2.jpg",
                "https://example.com/rio3.jpg"
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

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for testing."""
        mock_client = Mock()
        mock_table = Mock()
        mock_client.table.return_value = mock_table
        return mock_client, mock_table

    @pytest.fixture
    def artist_service(self, mock_supabase_client):
        """Artist service with mocked Supabase client."""
        mock_client, _ = mock_supabase_client
        return ArtistService(mock_client)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_artist_success(self, artist_service, mock_supabase_client, sample_artist_data):
        """Test creating an artist successfully."""
        # Arrange
        mock_client, mock_table = mock_supabase_client
        artist_id = uuid4()
        mock_response = Mock()
        mock_response.data = [{
            'id': str(artist_id),
            'name': sample_artist_data['name'],
            'description': sample_artist_data['description'],
            'reference_image_urls': sample_artist_data['reference_image_urls'],
            'created_at': datetime.now().isoformat()
        }]
        mock_table.insert.return_value.execute.return_value = mock_response

        # Act
        artist_create = ArtistCreate(**sample_artist_data)
        result = await artist_service.create_artist(artist_create)

        # Assert
        assert result.name == sample_artist_data['name']
        assert result.description == sample_artist_data['description']
        assert result.reference_image_urls == sample_artist_data['reference_image_urls']
        assert isinstance(result.id, type(artist_id))
        mock_table.insert.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_artist_validation_error(self):
        """Test artist creation with invalid data."""
        # Test validation requirements
        invalid_data = {
            "name": "",  # Empty name should fail
            "reference_image_urls": ["url1", "url2"]  # Only 2 images, needs 3-5
        }

        with pytest.raises(ValueError):
            ArtistCreate(**invalid_data)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_artist_by_id_success(self, artist_service, mock_supabase_client, sample_artist):
        """Test retrieving artist by ID."""
        # Arrange
        mock_client, mock_table = mock_supabase_client
        mock_response = Mock()
        mock_response.data = [{
            'id': str(sample_artist.id),
            'name': sample_artist.name,
            'description': sample_artist.description,
            'reference_image_urls': sample_artist.reference_image_urls,
            'created_at': sample_artist.created_at.isoformat()
        }]
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_response

        # Act
        result = await artist_service.get_artist_by_id(sample_artist.id)

        # Assert
        assert result is not None
        assert result.id == sample_artist.id
        assert result.name == sample_artist.name
        mock_table.select.assert_called_once_with('*')

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_artist_by_id_not_found(self, artist_service, mock_supabase_client):
        """Test retrieving non-existent artist."""
        # Arrange
        mock_client, mock_table = mock_supabase_client
        mock_response = Mock()
        mock_response.data = []  # No artist found
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_response

        # Act
        result = await artist_service.get_artist_by_id(uuid4())

        # Assert
        assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_artists_success(self):
        """Test listing all artists."""
        # This test will be implemented after we create the ArtistService
        pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_artist_success(self, sample_artist):
        """Test updating artist information."""
        # This test will be implemented after we create the ArtistService
        pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_artist_success(self, sample_artist):
        """Test deleting an artist."""
        # This test will be implemented after we create the ArtistService
        pass

    @pytest.mark.unit
    def test_artist_model_validation(self):
        """Test Artist model validation rules."""
        # Test valid artist
        valid_data = {
            "name": "Test Artist",
            "reference_image_urls": ["url1", "url2", "url3"]
        }
        artist_create = ArtistCreate(**valid_data)
        assert artist_create.name == "Test Artist"
        assert len(artist_create.reference_image_urls) == 3

        # Test invalid: too few images
        with pytest.raises(ValueError):
            ArtistCreate(
                name="Test",
                reference_image_urls=["url1", "url2"]  # Only 2, needs 3-5
            )

        # Test invalid: too many images
        with pytest.raises(ValueError):
            ArtistCreate(
                name="Test",
                reference_image_urls=["url1", "url2", "url3", "url4", "url5", "url6"]  # 6, max is 5
            )

        # Test invalid: empty name
        with pytest.raises(ValueError):
            ArtistCreate(
                name="",
                reference_image_urls=["url1", "url2", "url3"]
            )


class TestArtistPromptGeneration:
    """Test suite for artist-enhanced prompt generation."""

    @pytest.fixture
    def sample_scene(self):
        """Sample scene for prompt generation."""
        return SceneSelection(
            scene_id=1,
            title="Street Lineup",
            start_time=10.0,
            end_time=17.5,
            duration=7.5,
            source_segments=[2, 3],
            lyrics_excerpt="Line them up, that's a easy kill I'm a real ghetto boy, I build peasy steel",
            theme="preparation_targeting",
            energy_level=8,
            visual_potential=9,
            narrative_importance=8,
            reasoning="Captures the preparation and targeting mindset"
        )

    @pytest.fixture
    def artist_reference_images(self):
        """Sample artist reference images."""
        return {
            str(uuid4()): "https://storage.supabase.com/rio_ref_1.jpg"
        }

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_prompt_with_artist_reference(self, sample_scene, artist_reference_images):
        """Test generating visual prompt with artist reference image."""
        from app.services.openrouter import OpenRouterService

        # Mock OpenRouter service
        mock_openrouter = Mock()
        mock_openrouter.generate_individual_visual_prompt_with_artist = AsyncMock()

        # Expected enhanced prompt result
        enhanced_prompt = VisualPrompt(
            scene_id=1,
            image_prompt="Rio Da Yung OG (as shown in reference image) standing in urban street lineup, dramatic lighting, aggressive confident pose",
            style_notes="street_photography_meets_music_video_with_artist_reference",
            negative_prompt="generic rapper, different person, blurry face",
            setting="urban_street_night",
            shot_type="wide_shot",
            mood="aggressive_confident",
            color_palette="dark_blues_amber_highlights"
        )

        mock_openrouter.generate_individual_visual_prompt_with_artist.return_value = enhanced_prompt

        # Act
        result = await mock_openrouter.generate_individual_visual_prompt_with_artist(
            sample_scene, artist_reference_images
        )

        # Assert
        assert "Rio Da Yung OG" in result.image_prompt
        assert "reference image" in result.image_prompt
        assert "generic rapper" in result.negative_prompt
        mock_openrouter.generate_individual_visual_prompt_with_artist.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_prompt_without_artist_reference(self, sample_scene):
        """Test generating visual prompt without artist reference (fallback)."""
        # This test will be implemented after we enhance OpenRouterService
        pass

    @pytest.mark.unit
    def test_artist_reference_image_selection(self):
        """Test random selection of artist reference image per project."""
        # Test that we consistently select the same random image for a project
        # This test will be implemented after we create the selection logic
        pass