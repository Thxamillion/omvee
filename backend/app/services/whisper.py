"""
OpenAI Whisper integration service for audio transcription.
Provides high-accuracy speech-to-text with precise timestamps.
"""
import asyncio
from typing import BinaryIO, List, Dict, Any
from pathlib import Path
import logging

from openai import AsyncOpenAI
from app.models_pydantic import TranscriptionResult
from app.config import settings

logger = logging.getLogger(__name__)


class WhisperService:
    """
    Service for transcribing audio using OpenAI Whisper API.

    Features:
    - Segment-level timestamps for precise timing
    - Support for multiple audio formats
    - Cost estimation and validation
    - Async processing for better performance
    """

    # Supported audio formats by Whisper API
    SUPPORTED_FORMATS = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]

    # Pricing: $0.006 per minute
    COST_PER_MINUTE = 0.006

    def __init__(self, api_key: str = None):
        """Initialize Whisper service with OpenAI API key."""
        if api_key:
            self.api_key = api_key
        else:
            # Try to get from settings, but don't fail if not available (for testing)
            try:
                self.api_key = settings.openai_api_key
            except AttributeError:
                self.api_key = None

        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None

    async def transcribe_audio(
        self,
        audio_file: BinaryIO,
        filename: str,
        language: str = None
    ) -> TranscriptionResult:
        """
        Transcribe audio file with detailed timestamps.

        Args:
            audio_file: Audio file buffer
            filename: Original filename for format detection
            language: Optional language hint (ISO-639-1)

        Returns:
            TranscriptionResult with full text and timestamped segments

        Raises:
            ValueError: If audio format is not supported
            Exception: If API call fails
        """
        try:
            # Validate file format
            if not self.validate_audio_file(filename):
                raise ValueError(f"Unsupported audio format. Supported: {self.SUPPORTED_FORMATS}")

            logger.info(f"Starting transcription for {filename}")

            # Prepare file for API call
            audio_file.seek(0)  # Ensure we're at the beginning

            # Call Whisper API with verbose response for timestamps
            response = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=(filename, audio_file, "audio/mpeg"),
                response_format="verbose_json",
                language=language
            )

            # Convert API response to our model
            segments = []
            if hasattr(response, 'segments') and response.segments:
                for segment in response.segments:
                    # Handle both dict and object formats
                    if isinstance(segment, dict):
                        segments.append({
                            "start": segment.get("start", 0),
                            "end": segment.get("end", 0),
                            "text": segment.get("text", "")
                        })
                    else:
                        segments.append({
                            "start": getattr(segment, "start", 0),
                            "end": getattr(segment, "end", 0),
                            "text": getattr(segment, "text", "")
                        })

            result = TranscriptionResult(
                text=response.text,
                segments=segments
            )

            logger.info(f"Transcription completed. Text length: {len(result.text)} chars, "
                       f"Segments: {len(result.segments)}")

            return result

        except Exception as e:
            logger.error(f"Transcription failed for {filename}: {str(e)}")
            raise

    def validate_audio_file(self, filename: str) -> bool:
        """
        Validate if audio file format is supported.

        Args:
            filename: Audio file name

        Returns:
            True if format is supported, False otherwise
        """
        file_extension = Path(filename).suffix.lower().lstrip('.')
        return file_extension in self.SUPPORTED_FORMATS

    def supported_formats(self) -> List[str]:
        """Return list of supported audio formats."""
        return self.SUPPORTED_FORMATS.copy()

    async def estimate_cost(self, duration_minutes: float) -> float:
        """
        Estimate transcription cost based on audio duration.

        Args:
            duration_minutes: Audio duration in minutes

        Returns:
            Estimated cost in USD
        """
        return duration_minutes * self.COST_PER_MINUTE

    async def get_audio_duration(self, audio_file: BinaryIO) -> float:
        """
        Estimate audio duration (placeholder - would need audio analysis library).

        Args:
            audio_file: Audio file buffer

        Returns:
            Estimated duration in minutes

        Note:
            This is a placeholder. In production, you'd use a library like
            python-ffmpeg, librosa, or mutagen to get actual duration.
        """
        # Placeholder estimation based on file size
        audio_file.seek(0, 2)  # Seek to end
        file_size_mb = audio_file.tell() / (1024 * 1024)
        audio_file.seek(0)  # Reset to beginning

        # Rough estimation: ~1MB per minute for compressed audio
        estimated_minutes = file_size_mb
        return estimated_minutes


# Global service instance - will be initialized when needed
whisper_service = None

def get_whisper_service() -> WhisperService:
    """Get or create the global WhisperService instance."""
    global whisper_service
    if whisper_service is None:
        whisper_service = WhisperService()
    return whisper_service