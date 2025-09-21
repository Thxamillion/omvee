"""
Shared test fixtures and configuration for OMVEE tests.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any
import uuid
from datetime import datetime
import json
from pathlib import Path

import httpx
from app.models_pydantic import TranscriptionResult


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_supabase_service():
    """Mock Supabase service for testing."""
    service = MagicMock()

    # Mock project data
    service.create_project.return_value = {
        "id": str(uuid.uuid4()),
        "name": "Test Project",
        "status": "created",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    service.get_project.return_value = {
        "id": str(uuid.uuid4()),
        "name": "Test Project",
        "status": "created",
        "audio_path": None,
        "transcript_text": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    return service


@pytest.fixture
def sample_audio_transcript():
    """Sample audio transcript for testing."""
    return {
        "text": "Standing in the rain, feeling the pain, but I know I'll rise again. Dancing through the night, everything's alright, living life without a care.",
        "segments": [
            {
                "start": 0.0,
                "end": 15.5,
                "text": "Standing in the rain, feeling the pain, but I know I'll rise again."
            },
            {
                "start": 15.5,
                "end": 30.0,
                "text": "Dancing through the night, everything's alright, living life without a care."
            }
        ]
    }


@pytest.fixture
def rio_transcription():
    """Real Rio Da Yung OG transcription for integration testing without Whisper API calls."""
    transcription_path = Path("test_assets/transcriptions/rio_easy_kill_transcription.json")

    if not transcription_path.exists():
        pytest.skip(f"Rio transcription not found at {transcription_path}. Run generate_rio_transcription.py first.")

    with open(transcription_path) as f:
        data = json.load(f)

    return TranscriptionResult(**data)


@pytest.fixture
def sample_scenes_response():
    """Sample AI scene selection response for testing."""
    return {
        "scenes": [
            {
                "lyric_excerpt": "Standing in the rain, feeling the pain",
                "theme": "melancholy_reflection",
                "ai_reasoning": "Emotional vulnerability perfect for dramatic visuals",
                "start_time_s": 0.0,
                "end_time_s": 15.5,
                "order_idx": 1
            },
            {
                "lyric_excerpt": "Dancing through the night, everything's alright",
                "theme": "joyful_celebration",
                "ai_reasoning": "High energy moment for vibrant, dynamic visuals",
                "start_time_s": 15.5,
                "end_time_s": 30.0,
                "order_idx": 2
            }
        ]
    }


@pytest.fixture
def sample_prompts_response():
    """Sample AI prompt generation response for testing."""
    return {
        "prompts": [
            {
                "scene_id": str(uuid.uuid4()),
                "visual_prompt": "A cinematic shot of a person standing alone in heavy rain on an empty city street at dusk, dramatic lighting, melancholic mood, photorealistic, 16:9 aspect ratio",
                "style_notes": "moody, dramatic, urban setting",
                "ai_reasoning": "Rain imagery enhances the emotional weight of feeling pain and vulnerability"
            },
            {
                "scene_id": str(uuid.uuid4()),
                "visual_prompt": "Dynamic party scene with vibrant neon lights, people dancing energetically, colorful confetti falling, joyful expressions, high energy nightclub atmosphere, 16:9 aspect ratio",
                "style_notes": "vibrant, energetic, celebratory",
                "ai_reasoning": "High-energy dancing visuals match the upbeat lyrics about dancing through the night"
            }
        ]
    }


@pytest.fixture
def sample_image_generation_response():
    """Sample Flux image generation response for testing."""
    return {
        "id": "test-prediction-id",
        "status": "succeeded",
        "output": ["https://example.com/generated-image-1.jpg"],
        "created_at": "2025-01-01T00:00:00Z",
        "completed_at": "2025-01-01T00:00:30Z"
    }


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for Whisper API testing."""
    client = MagicMock()

    # Mock audio transcription response as async
    async_mock_response = AsyncMock()
    async_mock_response.text = "Standing in the rain, feeling the pain, but I know I'll rise again. Dancing through the night, everything's alright, living life without a care."
    async_mock_response.segments = [
        MagicMock(
            start=0.0,
            end=15.5,
            text="Standing in the rain, feeling the pain, but I know I'll rise again."
        ),
        MagicMock(
            start=15.5,
            end=30.0,
            text="Dancing through the night, everything's alright, living life without a care."
        )
    ]

    client.audio.transcriptions.create = AsyncMock(return_value=async_mock_response)

    return client


@pytest.fixture
def mock_replicate_client():
    """Mock Replicate client for Flux image generation testing."""
    client = MagicMock()

    # Mock prediction creation and polling
    prediction = MagicMock()
    prediction.id = "test-prediction-id"
    prediction.status = "succeeded"
    prediction.output = ["https://example.com/generated-image-1.jpg"]

    client.predictions.create.return_value = prediction
    client.predictions.get.return_value = prediction

    return client


@pytest.fixture
def test_project_id():
    """Test project UUID for consistency across tests."""
    return "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def test_scene_id():
    """Test scene UUID for consistency across tests."""
    return "660e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def mock_openrouter_client():
    """Mock HTTP client for OpenRouter API testing."""
    client = MagicMock()

    # Mock aiohttp session context manager behavior
    session = MagicMock()
    response = AsyncMock()
    response.status = 200
    response.json = AsyncMock(return_value={
        "choices": [{"message": {"content": "{}"}}]
    })

    session.post = AsyncMock(return_value=response)
    client.__aenter__ = AsyncMock(return_value=session)
    client.__aexit__ = AsyncMock(return_value=False)

    return client