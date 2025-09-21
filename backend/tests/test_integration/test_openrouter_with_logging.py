"""
Integration tests for OpenRouter service with real Rio transcription and file logging.
These tests will generate actual AI prompts and save logs to test_logs/ directory.
"""

import pytest
import pytest_asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

from app.services.openrouter import OpenRouterService
from app.models_pydantic import TranscriptionResult

# Load environment variables for tests
load_dotenv()


class TestOpenRouterIntegrationWithLogging:
    """Integration tests with real Rio transcription and file logging enabled."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment for file logging."""
        os.environ["ENVIRONMENT"] = "test"
        yield
        # Cleanup after test
        if "ENVIRONMENT" in os.environ:
            del os.environ["ENVIRONMENT"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_scene_selection_with_rio_transcription(self, rio_transcription):
        """Test scene selection using real Rio transcription with file logging."""

        # Ensure we have the transcription
        assert rio_transcription is not None
        assert len(rio_transcription.segments) > 0
        print(f"📊 Testing with Rio transcription: {len(rio_transcription.segments)} segments")

        openrouter_service = OpenRouterService()

        # Test scene selection with Rio's actual lyrics
        song_metadata = {
            "title": "Easy Kill",
            "artist": "Rio Da Yung OG",
            "genre": "Hip-Hop/Rap"
        }

        result = await openrouter_service.select_scenes(
            transcription=rio_transcription,
            target_scenes=18,  # AI will choose 15-20
            song_metadata=song_metadata
        )

        # Verify the result
        assert result is not None
        assert hasattr(result, 'selected_scenes')
        assert len(result.selected_scenes) >= 15
        assert len(result.selected_scenes) <= 20

        # Verify timeline coverage
        total_duration = rio_transcription.segments[-1]['end'] if rio_transcription.segments else 0
        first_scene_start = result.selected_scenes[0].start_time
        last_scene_end = result.selected_scenes[-1].end_time

        print(f"📊 Scene Analysis:")
        print(f"  - Total scenes selected: {len(result.selected_scenes)}")
        print(f"  - Audio duration: {total_duration:.1f}s")
        print(f"  - Scenes cover: {first_scene_start:.1f}s to {last_scene_end:.1f}s")
        print(f"  - Coverage: {((last_scene_end - first_scene_start) / total_duration * 100):.1f}%")

        # Check that test logs were created
        test_logs_dir = Path("test_logs")
        if test_logs_dir.exists():
            log_files = list(test_logs_dir.glob("*scene_selection*.json"))
            print(f"📋 Log files created: {len(log_files)}")
            if log_files:
                print(f"📋 Latest log: {log_files[-1]}")

        return result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_individual_prompt_generation_with_rio(self, rio_transcription):
        """Test individual prompt generation with a Rio scene."""

        openrouter_service = OpenRouterService()

        # First get scenes
        scenes_result = await openrouter_service.select_scenes(
            transcription=rio_transcription,
            target_scenes=16
        )

        # Pick the first scene for detailed prompt generation
        first_scene = scenes_result.selected_scenes[0]

        song_metadata = {
            "title": "Easy Kill",
            "artist": "Rio Da Yung OG",
            "genre": "Hip-Hop/Rap"
        }

        # Generate individual prompt
        visual_prompt = await openrouter_service.generate_individual_visual_prompt(
            scene=first_scene,
            song_metadata=song_metadata
        )

        # Verify the prompt
        assert visual_prompt is not None
        assert hasattr(visual_prompt, 'image_prompt')
        assert len(visual_prompt.image_prompt) > 50  # Should be detailed

        print(f"🎬 Generated Visual Prompt for Scene {first_scene.scene_id}:")
        print(f"  - Title: {first_scene.title}")
        print(f"  - Lyrics: {first_scene.lyrics_excerpt}")
        print(f"  - Prompt: {visual_prompt.image_prompt[:100]}...")
        print(f"  - Setting: {visual_prompt.setting}")
        print(f"  - Mood: {visual_prompt.mood}")

        # Check that test logs were created
        test_logs_dir = Path("test_logs")
        if test_logs_dir.exists():
            log_files = list(test_logs_dir.glob("*individual_visual_prompt*.json"))
            print(f"📋 Individual prompt log files: {len(log_files)}")

        return visual_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_artist_enhanced_prompt_generation(self, rio_transcription):
        """Test artist-enhanced prompt generation with Rio reference images."""

        openrouter_service = OpenRouterService()

        # First get scenes
        scenes_result = await openrouter_service.select_scenes(
            transcription=rio_transcription,
            target_scenes=16
        )

        # Pick the first scene for artist-enhanced prompt
        first_scene = scenes_result.selected_scenes[0]

        song_metadata = {
            "title": "Easy Kill",
            "artist": "Rio Da Yung OG",
            "genre": "Hip-Hop/Rap"
        }

        # Mock artist reference images (in real use, these would come from database)
        artist_reference_images = {
            "029d7f1b-1278-4a2f-94a0-38b20a452515": "https://example.com/rio_ref_1.jpg"
        }

        # Generate artist-enhanced prompt
        visual_prompt = await openrouter_service.generate_individual_visual_prompt_with_artist(
            scene=first_scene,
            artist_reference_images=artist_reference_images,
            song_metadata=song_metadata
        )

        # Verify the prompt includes artist context
        assert visual_prompt is not None
        assert hasattr(visual_prompt, 'image_prompt')
        assert len(visual_prompt.image_prompt) > 50

        print(f"🎨 Artist-Enhanced Prompt for Scene {first_scene.scene_id}:")
        print(f"  - Title: {first_scene.title}")
        print(f"  - Lyrics: {first_scene.lyrics_excerpt}")
        print(f"  - Artist Prompt: {visual_prompt.image_prompt[:150]}...")
        print(f"  - Style Notes: {visual_prompt.style_notes}")

        # Check that test logs were created with artist metadata
        test_logs_dir = Path("test_logs")
        if test_logs_dir.exists():
            log_files = list(test_logs_dir.glob("*artist_enhanced_visual_prompt*.json"))
            print(f"📋 Artist-enhanced prompt log files: {len(log_files)}")

        return visual_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_workflow_with_rio(self, rio_transcription):
        """Test the complete workflow: transcription -> scenes -> prompts with logging."""

        openrouter_service = OpenRouterService()

        song_metadata = {
            "title": "Easy Kill",
            "artist": "Rio Da Yung OG",
            "genre": "Hip-Hop/Rap"
        }

        # Step 1: Scene Selection
        print("🎬 Step 1: Selecting scenes...")
        scenes_result = await openrouter_service.select_scenes(
            transcription=rio_transcription,
            target_scenes=17,
            song_metadata=song_metadata
        )

        # Step 2: Generate prompts for first 3 scenes
        print("🎨 Step 2: Generating visual prompts...")
        for i, scene in enumerate(scenes_result.selected_scenes[:3]):
            visual_prompt = await openrouter_service.generate_individual_visual_prompt(
                scene=scene,
                song_metadata=song_metadata
            )
            print(f"  - Scene {scene.scene_id}: {visual_prompt.setting}")

        # Verify all steps completed
        assert len(scenes_result.selected_scenes) >= 15
        print(f"✅ Full workflow completed with {len(scenes_result.selected_scenes)} scenes")

        # Check all logs were created
        test_logs_dir = Path("test_logs")
        if test_logs_dir.exists():
            all_logs = list(test_logs_dir.glob("*.json"))
            print(f"📋 Total log files created: {len(all_logs)}")

            # Show log types
            scene_logs = [f for f in all_logs if "scene_selection" in f.name]
            prompt_logs = [f for f in all_logs if "individual_visual_prompt" in f.name]
            print(f"📋 Scene selection logs: {len(scene_logs)}")
            print(f"📋 Individual prompt logs: {len(prompt_logs)}")

        return scenes_result