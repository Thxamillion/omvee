"""
Tests for OpenAI Whisper integration service.
Following TDD approach - tests written first, then implementation.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import io
from pathlib import Path

from app.services.whisper import WhisperService
from app.models_pydantic import TranscriptionResult


class TestWhisperService:
    """Test suite for OpenAI Whisper transcription service."""

    @pytest.fixture
    def whisper_service(self, mock_openai_client):
        """Create WhisperService instance with mocked OpenAI client."""
        with patch('app.services.whisper.AsyncOpenAI', return_value=mock_openai_client):
            return WhisperService(api_key="test-api-key")

    @pytest.fixture
    def sample_audio_file(self):
        """Create a mock audio file for testing."""
        audio_content = b"fake audio content"
        return io.BytesIO(audio_content)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, whisper_service, sample_audio_file, mock_openai_client):
        """Test successful audio transcription."""
        # Arrange
        expected_text = "Standing in the rain, feeling the pain, but I know I'll rise again."
        expected_segments = [
            {"start": 0.0, "end": 15.5, "text": expected_text}
        ]

        mock_response = MagicMock()
        mock_response.text = expected_text
        mock_response.segments = [
            MagicMock(start=0.0, end=15.5, text=expected_text)
        ]
        mock_openai_client.audio.transcriptions.create.return_value = mock_response

        # Act
        result = await whisper_service.transcribe_audio(sample_audio_file, "test.mp3")

        # Assert
        assert isinstance(result, TranscriptionResult)
        assert result.text == expected_text
        assert len(result.segments) == 1
        assert result.segments[0]["start"] == 0.0
        assert result.segments[0]["end"] == 15.5
        assert result.segments[0]["text"] == expected_text

        # Verify OpenAI API was called correctly
        mock_openai_client.audio.transcriptions.create.assert_called_once()
        call_args = mock_openai_client.audio.transcriptions.create.call_args
        assert call_args.kwargs["model"] == "whisper-1"
        assert call_args.kwargs["response_format"] == "verbose_json"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transcribe_audio_with_multiple_segments(self, whisper_service, sample_audio_file, mock_openai_client):
        """Test transcription with multiple segments."""
        # Arrange
        full_text = "Standing in the rain, feeling the pain. Dancing through the night, everything's alright."
        segments = [
            MagicMock(start=0.0, end=15.5, text="Standing in the rain, feeling the pain."),
            MagicMock(start=15.5, end=30.0, text="Dancing through the night, everything's alright.")
        ]

        mock_response = MagicMock()
        mock_response.text = full_text
        mock_response.segments = segments
        mock_openai_client.audio.transcriptions.create.return_value = mock_response

        # Act
        result = await whisper_service.transcribe_audio(sample_audio_file, "test.mp3")

        # Assert
        assert result.text == full_text
        assert len(result.segments) == 2
        assert result.segments[0]["start"] == 0.0
        assert result.segments[1]["start"] == 15.5

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transcribe_audio_api_error(self, whisper_service, sample_audio_file, mock_openai_client):
        """Test handling of OpenAI API errors."""
        # Arrange
        mock_openai_client.audio.transcriptions.create.side_effect = Exception("API Error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await whisper_service.transcribe_audio(sample_audio_file, "test.mp3")

        assert "API Error" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transcribe_audio_empty_result(self, whisper_service, sample_audio_file, mock_openai_client):
        """Test handling of empty transcription result."""
        # Arrange
        mock_response = MagicMock()
        mock_response.text = ""
        mock_response.segments = []
        mock_openai_client.audio.transcriptions.create.return_value = mock_response

        # Act
        result = await whisper_service.transcribe_audio(sample_audio_file, "test.mp3")

        # Assert
        assert result.text == ""
        assert len(result.segments) == 0

    @pytest.mark.unit
    def test_supported_audio_formats(self, whisper_service):
        """Test that service reports supported audio formats."""
        # Act
        formats = whisper_service.supported_formats()

        # Assert
        expected_formats = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
        assert all(fmt in formats for fmt in expected_formats)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_estimate_cost(self, whisper_service):
        """Test cost estimation for transcription."""
        # Act
        cost_1_min = await whisper_service.estimate_cost(duration_minutes=1.0)
        cost_5_min = await whisper_service.estimate_cost(duration_minutes=5.0)

        # Assert
        assert cost_1_min == 0.006  # $0.006 per minute
        assert cost_5_min == 0.030  # $0.006 * 5

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_audio_file_valid_format(self, whisper_service):
        """Test audio file format validation - valid formats."""
        # Act & Assert
        assert whisper_service.validate_audio_file("song.mp3") is True
        assert whisper_service.validate_audio_file("audio.wav") is True
        assert whisper_service.validate_audio_file("video.mp4") is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_audio_file_invalid_format(self, whisper_service):
        """Test audio file format validation - invalid formats."""
        # Act & Assert
        assert whisper_service.validate_audio_file("document.txt") is False
        assert whisper_service.validate_audio_file("image.jpg") is False
        assert whisper_service.validate_audio_file("archive.zip") is False


class TestWhisperServiceIntegration:
    """Integration tests for Whisper service with real API calls."""

    @pytest.mark.integration
    @pytest.mark.external_api
    @pytest.mark.asyncio
    async def test_real_whisper_api_call(self):
        """Test real Whisper API call with actual audio file."""
        import os
        from pathlib import Path
        from dotenv import load_dotenv

        # Load environment variables from .env file
        load_dotenv()

        # Skip if no API key or test file
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_key_here":
            pytest.skip("No OpenAI API key provided")

        # Look for any MP3 file in test_assets/audio
        test_dir = Path("test_assets/audio")
        mp3_files = list(test_dir.glob("*.mp3"))

        if not mp3_files:
            pytest.skip(f"No MP3 file found in {test_dir}")

        test_file = mp3_files[0]  # Use the first MP3 file found
        print(f"🎵 Using test file: {test_file.name}")

        # Run real transcription
        service = WhisperService(api_key=api_key)

        with open(test_file, "rb") as audio_file:
            result = await service.transcribe_audio(audio_file, test_file.name)

        # Basic assertions
        assert result.text is not None
        assert len(result.text) > 0
        assert isinstance(result.segments, list)

        print(f"✅ Transcription successful!")
        print(f"📝 Text: {result.text[:100]}...")
        print(f"🕐 Segments: {len(result.segments)}")