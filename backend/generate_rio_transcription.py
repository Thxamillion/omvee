#!/usr/bin/env python3
"""
One-time script to generate and save Rio transcription for testing.
This avoids calling Whisper API during every test run.
"""

import asyncio
import json
from app.services.whisper import WhisperService

async def generate_and_save_transcription():
    """Generate transcription and save to file."""

    audio_file_path = "test_assets/audio/Rio Da Yung Og - Easy Kill (Official Video).mp3"
    output_file_path = "test_assets/transcriptions/rio_easy_kill_transcription.json"

    print(f"🎵 Transcribing: {audio_file_path}")
    print("⏳ This will take a moment and cost ~$0.006...")

    try:
        # Initialize Whisper service
        whisper_service = WhisperService()

        # Generate transcription
        with open(audio_file_path, "rb") as audio_file:
            transcription = await whisper_service.transcribe_audio(
                audio_file=audio_file,
                filename="Rio Da Yung Og - Easy Kill (Official Video).mp3"
            )

        # Convert to dict for JSON serialization
        transcription_dict = {
            "text": transcription.text,
            "segments": transcription.segments
        }

        # Save to file
        with open(output_file_path, "w") as f:
            json.dump(transcription_dict, f, indent=2)

        print(f"✅ Transcription saved to: {output_file_path}")
        print(f"📊 Total segments: {len(transcription.segments)}")
        print(f"📝 Text length: {len(transcription.text)} characters")

        # Show first few segments as preview
        print("\n📋 First 3 segments preview:")
        for i, segment in enumerate(transcription.segments[:3]):
            if isinstance(segment, dict):
                print(f"  {i+1}: {segment.get('start', 0):.1f}s-{segment.get('end', 0):.1f}s: {segment.get('text', '')}")
            else:
                print(f"  {i+1}: {segment}")

    except Exception as e:
        print(f"❌ Error generating transcription: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(generate_and_save_transcription())