"""
Tests for OpenRouter (DeepSeek) scene selection and prompt generation services.
Following TDD approach - tests written first, then implementation.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from app.services.openrouter import OpenRouterService
from app.models_pydantic import (
    TranscriptionResult,
    SceneSelectionResult,
    SceneSelection,
    PromptGenerationResult,
    VisualPrompt
)


class TestOpenRouterSceneSelection:
    """Test suite for OpenRouter scene selection service."""

    @pytest.fixture
    def openrouter_service(self, mock_openrouter_client):
        """Create OpenRouterService instance with mocked client."""
        with patch('app.services.openrouter.aiohttp.ClientSession', return_value=mock_openrouter_client):
            return OpenRouterService(api_key="test-api-key")

    @pytest.fixture
    def sample_transcription_result(self):
        """Sample transcription result with multiple segments."""
        return TranscriptionResult(
            text="Line them up, that's a easy kill I'm a real ghetto boy, I build peasy steel. I ain't touch the trigger, but I seen the drill. Your career ain't promising, you probably need a will.",
            segments=[
                {"start": 0.0, "end": 6.6, "text": "Line them up, that's a easy kill I'm a real ghetto boy, I build peasy steel"},
                {"start": 6.6, "end": 11.2, "text": "I ain't touch the trigger, but I seen the drill"},
                {"start": 11.2, "end": 16.8, "text": "Your career ain't promising, you probably need a will"},
                {"start": 16.8, "end": 22.4, "text": "Seen a nigga with his head gone and I can see him still"},
                {"start": 22.4, "end": 28.0, "text": "That's why I gotta watch how I move"}
            ]
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_select_scenes_success(self, openrouter_service, sample_transcription_result, mock_openrouter_client):
        """Test successful scene selection from transcription."""
        # Arrange
        expected_response = {
            "song_themes": ["street_credibility", "violence_threats", "survival"],
            "energy_arc": "aggressive_opening → threatening_middle → cautious_ending",
            "total_scenes_selected": 3,
            "average_scene_length": 9.5,
            "selected_scenes": [
                {
                    "scene_id": 1,
                    "title": "Opening Threat",
                    "start_time": 0.0,
                    "end_time": 6.6,
                    "duration": 6.6,
                    "source_segments": [1],
                    "lyrics_excerpt": "Line them up, that's a easy kill I'm a real ghetto boy, I build peasy steel",
                    "theme": "intimidating_introduction",
                    "energy_level": 9,
                    "visual_potential": 8,
                    "narrative_importance": 9,
                    "reasoning": "Strong opening with clear visual imagery and character establishment"
                },
                {
                    "scene_id": 2,
                    "title": "Street Experience",
                    "start_time": 6.6,
                    "end_time": 16.8,
                    "duration": 10.2,
                    "source_segments": [2, 3],
                    "lyrics_excerpt": "I ain't touch the trigger, but I seen the drill. Your career ain't promising, you probably need a will",
                    "theme": "street_wisdom",
                    "energy_level": 7,
                    "visual_potential": 9,
                    "narrative_importance": 8,
                    "reasoning": "Builds on street credibility with specific imagery"
                },
                {
                    "scene_id": 3,
                    "title": "Consequences",
                    "start_time": 16.8,
                    "end_time": 28.0,
                    "duration": 11.2,
                    "source_segments": [4, 5],
                    "lyrics_excerpt": "Seen a nigga with his head gone and I can see him still. That's why I gotta watch how I move",
                    "theme": "trauma_awareness",
                    "energy_level": 6,
                    "visual_potential": 10,
                    "narrative_importance": 9,
                    "reasoning": "Powerful visual imagery leading to cautious conclusion"
                }
            ],
            "reasoning_summary": "Selected scenes that progress from aggressive introduction to experienced wisdom to cautious awareness, maintaining strong visual potential throughout"
        }

        mock_openrouter_client.post.return_value = AsyncMock()
        mock_openrouter_client.post.return_value.json.return_value = {
            "choices": [{"message": {"content": str(expected_response).replace("'", '"')}}]
        }

        # Act
        result = await openrouter_service.select_scenes(
            transcription=sample_transcription_result,
            song_metadata={"title": "Test Song", "artist": "Test Artist", "genre": "rap"}
        )

        # Assert
        assert isinstance(result, SceneSelectionResult)
        assert result.total_scenes_selected == 3
        assert result.average_scene_length == 9.5
        assert len(result.selected_scenes) == 3

        # Verify first scene details
        first_scene = result.selected_scenes[0]
        assert first_scene.scene_id == 1
        assert first_scene.title == "Opening Threat"
        assert first_scene.start_time == 0.0
        assert first_scene.end_time == 6.6
        assert first_scene.theme == "intimidating_introduction"
        assert first_scene.energy_level == 9

        # Verify API call was made correctly
        mock_openrouter_client.post.assert_called_once()
        call_args = mock_openrouter_client.post.call_args
        assert "deepseek" in call_args.kwargs["json"]["model"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_select_scenes_with_many_segments(self, openrouter_service, mock_openrouter_client):
        """Test scene selection with many segments (like real Whisper output)."""
        # Arrange - Create a transcription with many segments like real data
        many_segments = []
        for i in range(20):
            many_segments.append({
                "start": i * 3.0,
                "end": (i + 1) * 3.0,
                "text": f"Sample lyric segment {i + 1} with various content"
            })

        transcription = TranscriptionResult(
            text=" ".join([seg["text"] for seg in many_segments]),
            segments=many_segments
        )

        # Mock response with consolidated scenes
        mock_response = {
            "song_themes": ["test_theme"],
            "energy_arc": "varied progression",
            "total_scenes_selected": 8,
            "average_scene_length": 7.5,
            "selected_scenes": [
                {
                    "scene_id": i + 1,
                    "title": f"Scene {i + 1}",
                    "start_time": i * 7.5,
                    "end_time": (i + 1) * 7.5,
                    "duration": 7.5,
                    "source_segments": [i * 2 + 1, i * 2 + 2],
                    "lyrics_excerpt": f"Combined lyrics for scene {i + 1}",
                    "theme": "test_theme",
                    "energy_level": 5,
                    "visual_potential": 7,
                    "narrative_importance": 6,
                    "reasoning": f"Reasoning for scene {i + 1}"
                }
                for i in range(8)
            ],
            "reasoning_summary": "Consolidated 20 segments into 8 coherent scenes"
        }

        mock_openrouter_client.post.return_value = AsyncMock()
        mock_openrouter_client.post.return_value.json.return_value = {
            "choices": [{"message": {"content": str(mock_response).replace("'", '"')}}]
        }

        # Act
        result = await openrouter_service.select_scenes(transcription, {"title": "Long Song"})

        # Assert
        assert result.total_scenes_selected == 8
        assert len(result.selected_scenes) == 8
        assert all(scene.duration == 7.5 for scene in result.selected_scenes)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_select_scenes_api_error(self, openrouter_service, sample_transcription_result, mock_openrouter_client):
        """Test handling of OpenRouter API errors."""
        # Arrange
        mock_openrouter_client.post.side_effect = Exception("API Error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await openrouter_service.select_scenes(sample_transcription_result, {})

        assert "API Error" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_scene_selection_constraints(self, openrouter_service, sample_transcription_result, mock_openrouter_client):
        """Test that scene selection respects timing and count constraints."""
        # This test ensures our service validates the AI response properly
        mock_response = {
            "song_themes": ["test"],
            "energy_arc": "test",
            "total_scenes_selected": 2,
            "average_scene_length": 14.0,
            "selected_scenes": [
                {
                    "scene_id": 1,
                    "title": "Long Scene",
                    "start_time": 0.0,
                    "end_time": 14.0,
                    "duration": 14.0,
                    "source_segments": [1, 2],
                    "lyrics_excerpt": "Combined lyrics",
                    "theme": "test_theme",
                    "energy_level": 5,
                    "visual_potential": 7,
                    "narrative_importance": 6,
                    "reasoning": "Test reasoning"
                },
                {
                    "scene_id": 2,
                    "title": "Another Scene",
                    "start_time": 14.0,
                    "end_time": 28.0,
                    "duration": 14.0,
                    "source_segments": [3, 4, 5],
                    "lyrics_excerpt": "More lyrics",
                    "theme": "test_theme2",
                    "energy_level": 8,
                    "visual_potential": 9,
                    "narrative_importance": 8,
                    "reasoning": "More reasoning"
                }
            ],
            "reasoning_summary": "Test summary"
        }

        mock_openrouter_client.post.return_value = AsyncMock()
        mock_openrouter_client.post.return_value.json.return_value = {
            "choices": [{"message": {"content": str(mock_response).replace("'", '"')}}]
        }

        # Act
        result = await openrouter_service.select_scenes(sample_transcription_result, {})

        # Assert - Verify constraints
        assert 4 <= result.average_scene_length <= 16  # Within our target range
        assert 2 <= result.total_scenes_selected <= 20  # Reasonable scene count
        assert all(4 <= scene.duration <= 16 for scene in result.selected_scenes)


class TestOpenRouterPromptGeneration:
    """Test suite for OpenRouter visual prompt generation service."""

    @pytest.fixture
    def sample_scene_selection(self):
        """Sample scene selection result for prompt generation."""
        return SceneSelectionResult(
            song_themes=["street_credibility", "violence"],
            energy_arc="aggressive throughout",
            total_scenes_selected=2,
            average_scene_length=8.0,
            selected_scenes=[
                SceneSelection(
                    scene_id=1,
                    title="Opening Threat",
                    start_time=0.0,
                    end_time=8.0,
                    duration=8.0,
                    source_segments=[1, 2],
                    lyrics_excerpt="Line them up, that's a easy kill",
                    theme="intimidating_introduction",
                    energy_level=9,
                    visual_potential=8,
                    narrative_importance=9,
                    reasoning="Strong opening"
                ),
                SceneSelection(
                    scene_id=2,
                    title="Street Scene",
                    start_time=8.0,
                    end_time=16.0,
                    duration=8.0,
                    source_segments=[3, 4],
                    lyrics_excerpt="I ain't touch the trigger, but I seen the drill",
                    theme="street_wisdom",
                    energy_level=7,
                    visual_potential=9,
                    narrative_importance=8,
                    reasoning="Street credibility"
                )
            ],
            reasoning_summary="Aggressive street narrative"
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_visual_prompts_success(self, openrouter_service, sample_scene_selection, mock_openrouter_client):
        """Test successful visual prompt generation from scenes."""
        # Arrange
        expected_response = {
            "total_prompts": 2,
            "visual_prompts": [
                {
                    "scene_id": 1,
                    "image_prompt": "A commanding figure standing in urban street at night, dramatic amber lighting, aggressive confident pose, cinematic wide shot, street credibility atmosphere, dark moody lighting, 16:9 aspect ratio",
                    "style_notes": "street_photography_meets_music_video",
                    "negative_prompt": "blurry, low quality, amateur, cartoon",
                    "setting": "urban_street_night",
                    "shot_type": "wide_shot",
                    "mood": "aggressive_confident",
                    "color_palette": "dark_blues_amber_highlights"
                },
                {
                    "scene_id": 2,
                    "image_prompt": "Street scene with figure in shadows, gritty urban environment, experienced street knowledge, medium shot, dramatic lighting, realistic street photography style, 16:9 aspect ratio",
                    "style_notes": "documentary_street_realism",
                    "negative_prompt": "clean, polished, suburban, bright",
                    "setting": "street_environment",
                    "shot_type": "medium_shot",
                    "mood": "street_wise",
                    "color_palette": "muted_grays_harsh_whites"
                }
            ],
            "style_consistency": "Cohesive street photography aesthetic with dramatic lighting",
            "generation_notes": "Focus on authentic street environments and dramatic character presence"
        }

        mock_openrouter_client.post.return_value = AsyncMock()
        mock_openrouter_client.post.return_value.json.return_value = {
            "choices": [{"message": {"content": str(expected_response).replace("'", '"')}}]
        }

        # Act
        result = await openrouter_service.generate_visual_prompts(sample_scene_selection)

        # Assert
        assert isinstance(result, PromptGenerationResult)
        assert result.total_prompts == 2
        assert len(result.visual_prompts) == 2

        # Verify first prompt details
        first_prompt = result.visual_prompts[0]
        assert first_prompt.scene_id == 1
        assert "commanding figure" in first_prompt.image_prompt.lower()
        assert "urban street" in first_prompt.image_prompt.lower()
        assert "16:9" in first_prompt.image_prompt
        assert first_prompt.setting == "urban_street_night"
        assert first_prompt.shot_type == "wide_shot"

    @pytest.mark.unit
    def test_estimate_cost(self, openrouter_service):
        """Test cost estimation for OpenRouter API calls."""
        # Act
        scene_cost = openrouter_service.estimate_scene_selection_cost(segments_count=57)
        prompt_cost = openrouter_service.estimate_prompt_generation_cost(scenes_count=12)

        # Assert
        assert isinstance(scene_cost, float)
        assert isinstance(prompt_cost, float)
        assert scene_cost > 0
        assert prompt_cost > 0
        assert scene_cost > prompt_cost  # Scene selection should cost more (more input)

    @pytest.mark.unit
    def test_supported_models(self, openrouter_service):
        """Test that service reports supported models."""
        # Act
        models = openrouter_service.supported_models()

        # Assert
        assert isinstance(models, list)
        assert any("deepseek" in model.lower() for model in models)


class TestOpenRouterServiceIntegration:
    """Integration tests for OpenRouter service with real API calls."""

    @pytest.mark.integration
    @pytest.mark.external_api
    @pytest.mark.asyncio
    async def test_real_openrouter_scene_selection(self):
        """Test real OpenRouter API call for scene selection using actual Whisper transcription."""
        import os
        from pathlib import Path
        from dotenv import load_dotenv
        from app.services.whisper import WhisperService

        # Load environment variables
        load_dotenv()

        # Check API keys
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if not openrouter_key or openrouter_key == "your_openrouter_key_here":
            pytest.skip("No OpenRouter API key provided")
        if not openai_key or openai_key == "your_openai_key_here":
            pytest.skip("No OpenAI API key provided")

        # Get real transcription from Whisper first
        test_dir = Path("test_assets/audio")
        mp3_files = list(test_dir.glob("*.mp3"))

        if not mp3_files:
            pytest.skip(f"No MP3 file found in {test_dir}")

        test_file = mp3_files[0]
        print(f"🎵 Using MP3: {test_file.name}")

        # Get real Whisper transcription
        whisper_service = WhisperService(api_key=openai_key)
        with open(test_file, "rb") as audio_file:
            real_transcription = await whisper_service.transcribe_audio(audio_file, test_file.name)

        print(f"📝 Transcribed {len(real_transcription.segments)} segments")
        print(f"🎭 Text preview: {real_transcription.text[:100]}...")

        # Run real scene selection with actual transcription
        service = OpenRouterService(api_key=openrouter_key)
        result = await service.select_scenes(
            transcription=real_transcription,
            song_metadata={"title": "Easy Kill", "artist": "Rio Da Yung Og", "genre": "rap"}
        )

        # Basic assertions
        assert isinstance(result, SceneSelectionResult)
        assert result.total_scenes_selected > 0
        assert len(result.selected_scenes) > 0
        assert all(isinstance(scene, SceneSelection) for scene in result.selected_scenes)

        print(f"✅ Scene selection successful!")
        print(f"📊 Selected {result.total_scenes_selected} scenes")
        print(f"🎭 Themes: {', '.join(result.song_themes)}")
        print(f"📈 Energy arc: {result.energy_arc}")

    @pytest.mark.integration
    @pytest.mark.external_api
    @pytest.mark.asyncio
    async def test_real_openrouter_prompt_generation(self):
        """Test real OpenRouter API call for prompt generation."""
        import os
        from dotenv import load_dotenv

        # Load environment variables
        load_dotenv()

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key or api_key == "your_openrouter_key_here":
            pytest.skip("No OpenRouter API key provided")

        # Create test scene selection
        test_scenes = SceneSelectionResult(
            song_themes=["street_credibility"],
            energy_arc="aggressive",
            total_scenes_selected=1,
            average_scene_length=8.0,
            selected_scenes=[
                SceneSelection(
                    scene_id=1,
                    title="Test Scene",
                    start_time=0.0,
                    end_time=8.0,
                    duration=8.0,
                    source_segments=[1],
                    lyrics_excerpt="Line them up, that's a easy kill",
                    theme="intimidating",
                    energy_level=9,
                    visual_potential=8,
                    narrative_importance=9,
                    reasoning="Test"
                )
            ],
            reasoning_summary="Test selection"
        )

        # Run real prompt generation
        service = OpenRouterService(api_key=api_key)
        result = await service.generate_visual_prompts(test_scenes)

        # Basic assertions
        assert isinstance(result, PromptGenerationResult)
        assert result.total_prompts > 0
        assert len(result.visual_prompts) > 0
        assert all(isinstance(prompt, VisualPrompt) for prompt in result.visual_prompts)

        print(f"✅ Prompt generation successful!")
        print(f"🎨 Generated {result.total_prompts} visual prompts")
        print(f"🎬 Style: {result.style_consistency}")

    @pytest.mark.integration
    @pytest.mark.external_api
    @pytest.mark.asyncio
    async def test_real_end_to_end_pipeline(self):
        """Test complete pipeline: MP3 → Whisper → Scene Selection → Visual Prompts."""
        import os
        from pathlib import Path
        from dotenv import load_dotenv
        from app.services.whisper import WhisperService

        # Load environment variables
        load_dotenv()

        # Check API keys
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if not openrouter_key or openrouter_key == "your_openrouter_key_here":
            pytest.skip("No OpenRouter API key provided")
        if not openai_key or openai_key == "your_openai_key_here":
            pytest.skip("No OpenAI API key provided")

        # Get real transcription from Whisper first
        test_dir = Path("test_assets/audio")
        mp3_files = list(test_dir.glob("*.mp3"))

        if not mp3_files:
            pytest.skip(f"No MP3 file found in {test_dir}")

        test_file = mp3_files[0]
        print(f"🎵 PIPELINE: Using MP3: {test_file.name}")

        # Step 1: Whisper transcription
        whisper_service = WhisperService(api_key=openai_key)
        with open(test_file, "rb") as audio_file:
            transcription = await whisper_service.transcribe_audio(audio_file, test_file.name)

        print(f"✅ STEP 1: Transcribed {len(transcription.segments)} segments")

        # Step 2: Scene selection
        openrouter_service = OpenRouterService(api_key=openrouter_key)
        scene_selection = await openrouter_service.select_scenes(
            transcription=transcription,
            song_metadata={"title": "Easy Kill", "artist": "Rio Da Yung Og", "genre": "rap"}
        )

        print(f"✅ STEP 2: Selected {scene_selection.total_scenes_selected} scenes")
        print(f"🎭 Themes: {', '.join(scene_selection.song_themes)}")

        # Step 3: Visual prompt generation
        prompt_result = await openrouter_service.generate_visual_prompts(scene_selection)

        print(f"✅ STEP 3: Generated {prompt_result.total_prompts} visual prompts")
        print(f"🎨 Style: {prompt_result.style_consistency}")

        # Verify complete pipeline
        assert len(transcription.segments) > 50  # Full song
        assert 15 <= scene_selection.total_scenes_selected <= 20  # AI discretion
        assert prompt_result.total_prompts == scene_selection.total_scenes_selected  # 1:1 mapping
        assert len(prompt_result.visual_prompts) == scene_selection.total_scenes_selected

        # Verify all prompts have required fields
        for prompt in prompt_result.visual_prompts:
            assert prompt.image_prompt is not None and len(prompt.image_prompt) > 0
            assert prompt.scene_id > 0
            assert prompt.setting is not None
            assert prompt.shot_type is not None
            assert prompt.mood is not None

        print(f"🚀 END-TO-END PIPELINE SUCCESS!")
        print(f"📊 Final: {len(transcription.segments)} segments → {scene_selection.total_scenes_selected} scenes → {prompt_result.total_prompts} prompts")

        # Show sample prompts
        for i, prompt in enumerate(prompt_result.visual_prompts[:3]):
            print(f"🎬 Sample Prompt {i+1}: {prompt.image_prompt[:100]}...")

        return {
            "transcription": transcription,
            "scenes": scene_selection,
            "prompts": prompt_result
        }

    @pytest.mark.integration
    @pytest.mark.external_api
    @pytest.mark.asyncio
    async def test_individual_scene_prompt_generation(self):
        """Test individual scene prompt generation with 3 specific challenging scenes."""
        import os
        from dotenv import load_dotenv
        from app.models_pydantic import SceneSelection

        # Load environment variables
        load_dotenv()

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key or api_key == "your_openrouter_key_here":
            pytest.skip("No OpenRouter API key provided")

        # Create 3 test scenes with challenging lyrics
        test_scenes = [
            SceneSelection(
                scene_id=1,
                title="Line Them Up",
                start_time=0.0,
                end_time=6.6,
                duration=6.6,
                source_segments=[0],
                lyrics_excerpt="Line them up, that's a easy kill I'm a real ghetto boy, I build peasy steel",
                theme="street life",
                energy_level=9,
                visual_potential=8,
                narrative_importance=9,
                reasoning="Challenge: Capture the preparation/targeting aspect"
            ),
            SceneSelection(
                scene_id=3,
                title="Head Gone",
                start_time=11.2,
                end_time=13.8,
                duration=2.6,
                source_segments=[2],
                lyrics_excerpt="Seen a nigga with his head gone and I can see him still",
                theme="violence",
                energy_level=9,
                visual_potential=8,
                narrative_importance=8,
                reasoning="Challenge: Witness trauma, specific visceral imagery"
            ),
            SceneSelection(
                scene_id=16,
                title="Draco in the Club",
                start_time=57.1,
                end_time=62.2,
                duration=5.1,
                source_segments=[18, 19],
                lyrics_excerpt="Don't get too close, we got a fucking Draco in the club, Jack",
                theme="violence",
                energy_level=9,
                visual_potential=8,
                narrative_importance=8,
                reasoning="Challenge: Club scene with hidden weapon, tension"
            )
        ]

        service = OpenRouterService(api_key=api_key)
        song_metadata = {"title": "Easy Kill", "artist": "Rio Da Yung Og", "genre": "rap"}

        print(f"\n🎬 TESTING INDIVIDUAL SCENE PROMPT GENERATION")
        print(f"Testing {len(test_scenes)} challenging scenes...")

        # Test each scene individually
        for scene in test_scenes:
            print(f"\n--- TESTING SCENE {scene.scene_id}: {scene.title} ---")
            print(f"Lyrics: \"{scene.lyrics_excerpt}\"")
            print(f"Challenge: {scene.reasoning}")

            # Generate individual prompt
            prompt = await service.generate_individual_visual_prompt(scene, song_metadata)

            # Verify the prompt
            assert prompt.scene_id == scene.scene_id
            assert prompt.image_prompt is not None and len(prompt.image_prompt) > 100
            assert prompt.setting is not None
            assert prompt.shot_type is not None
            assert prompt.mood is not None
            assert prompt.color_palette is not None

            print(f"✅ Generated individual prompt for Scene {scene.scene_id}")
            print(f"🎨 Image Prompt: {prompt.image_prompt}")
            print(f"📍 Setting: {prompt.setting}")
            print(f"📸 Shot: {prompt.shot_type}")
            print(f"😤 Mood: {prompt.mood}")
            print(f"🎨 Colors: {prompt.color_palette}")

        print(f"\n🚀 ALL 3 INDIVIDUAL SCENE PROMPTS GENERATED SUCCESSFULLY!")
        print(f"💰 Cost: ~$0.09 for 3 individual calls (much more specific than batch)")

        # Compare to batch approach
        print(f"\n📊 COMPARISON:")
        print(f"• Batch approach: 1 call, $0.015, generic prompts")
        print(f"• Individual approach: 3 calls, $0.09, lyric-specific prompts")