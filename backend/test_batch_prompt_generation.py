#!/usr/bin/env python3
"""
Test batch visual prompt generation using real Rio Easy Kill transcription.
Focus only on batch generation to avoid timeout and get readable comparison results.
"""

import asyncio
import json
import os
from typing import Dict, Any
from datetime import datetime

# Set environment for test logging
os.environ["ENVIRONMENT"] = "test"

from app.services.openrouter import OpenRouterService
from app.models_pydantic import TranscriptionResult
from app.config import settings


async def load_rio_transcription() -> TranscriptionResult:
    """Load the Rio Easy Kill transcription from test assets."""

    with open("test_assets/transcriptions/rio_easy_kill_transcription.json", "r") as f:
        data = json.load(f)

    return TranscriptionResult(
        text=data["text"],
        segments=data["segments"]
    )


async def run_batch_generation_test():
    """Run batch visual prompt generation test with readable results."""

    print("🎵 Rio Easy Kill - Batch Visual Prompt Generation Test")
    print("=" * 70)

    # Initialize services
    openrouter_service = OpenRouterService(api_key=settings.openrouter_api_key)

    # Step 1: Load real transcription
    print("\n📋 Step 1: Loading Rio Easy Kill transcription...")
    transcription = await load_rio_transcription()

    duration = transcription.segments[-1]["end"] if transcription.segments else 0.0
    print(f"✅ Transcription loaded: {duration:.1f}s")
    print(f"📊 Total segments: {len(transcription.segments)}")
    print(f"🎤 Sample lyrics: \"{transcription.text[:100]}...\"")

    song_metadata = {
        "title": "Easy Kill",
        "artist": "Rio",
        "genre": "Hip Hop/Rap"
    }

    # Step 2: Scene selection
    print(f"\n🎬 Step 2: Running scene selection...")
    scene_start = datetime.now()

    scene_selection = await openrouter_service.select_scenes(
        transcription=transcription,
        target_scenes=15,
        song_metadata=song_metadata
    )

    scene_duration = (datetime.now() - scene_start).total_seconds()
    print(f"✅ Scene selection completed in {scene_duration:.2f}s")
    print(f"📊 Selected {len(scene_selection.selected_scenes)} scenes")
    print(f"🎭 Themes: {', '.join(scene_selection.song_themes)}")
    print(f"⚡ Energy arc: {scene_selection.energy_arc}")

    # Step 3: Batch visual prompt generation
    print(f"\n🎨 Step 3: Running BATCH visual prompt generation...")
    batch_start = datetime.now()

    batch_result = await openrouter_service.generate_visual_prompts(scene_selection)

    batch_duration = (datetime.now() - batch_start).total_seconds()
    print(f"✅ Batch generation completed in {batch_duration:.2f}s")
    print(f"📊 Generated {len(batch_result.visual_prompts)} visual prompts")

    # Step 4: Display readable results
    print(f"\n📋 SCENE SELECTION RESULTS")
    print("=" * 70)

    for i, scene in enumerate(scene_selection.selected_scenes, 1):
        print(f"\n🎬 Scene {i:2d}: \"{scene.title}\"")
        print(f"    ⏱️  Time: {scene.start_time:.1f}s → {scene.end_time:.1f}s ({scene.duration:.1f}s)")
        print(f"    🎵 Lyrics: \"{scene.lyrics_excerpt[:80]}...\"")
        print(f"    🎭 Theme: {scene.theme} | Energy: {scene.energy_level}/10 | Visual: {scene.visual_potential}/10")

    print(f"\n🎨 VISUAL PROMPTS COMPARISON")
    print("=" * 70)

    # Show detailed prompts for first 5 scenes
    for i in range(min(5, len(scene_selection.selected_scenes))):
        scene = scene_selection.selected_scenes[i]
        prompt = batch_result.visual_prompts[i]

        print(f"\n🎬 Scene {i+1}: \"{scene.title}\"")
        print(f"📝 Lyrics: \"{scene.lyrics_excerpt}\"")
        print(f"🎨 Visual Prompt:")
        print(f"    {prompt.image_prompt}")
        print(f"💡 Style Notes: {prompt.style_notes}")
        print(f"🚫 Negative Prompt: {prompt.negative_prompt}")
        print(f"📍 Setting: {prompt.setting}")
        print(f"🎥 Shot Type: {prompt.shot_type}")
        print(f"😌 Mood: {prompt.mood}")
        print(f"🎨 Colors: {prompt.color_palette}")

    # Show remaining scenes summarized
    if len(scene_selection.selected_scenes) > 5:
        print(f"\n📋 REMAINING SCENES SUMMARY ({len(scene_selection.selected_scenes) - 5} scenes)")
        print("-" * 50)

        for i in range(5, len(scene_selection.selected_scenes)):
            scene = scene_selection.selected_scenes[i]
            prompt = batch_result.visual_prompts[i]

            print(f"Scene {i+1:2d}: {scene.title[:25]:<25} | {prompt.mood[:20]:<20} | {prompt.shot_type}")

    # Step 5: Save detailed results
    results_data = {
        "test_metadata": {
            "timestamp": datetime.now().isoformat(),
            "song": f"{song_metadata['artist']} - {song_metadata['title']}",
            "scene_duration_seconds": scene_duration,
            "batch_duration_seconds": batch_duration,
            "total_scenes": len(scene_selection.selected_scenes),
            "total_prompts": len(batch_result.visual_prompts)
        },
        "transcription_info": {
            "duration": duration,
            "segments_count": len(transcription.segments),
            "text_preview": transcription.text[:200] + "..."
        },
        "scene_selection": scene_selection.model_dump(),
        "visual_prompts": batch_result.model_dump()
    }

    # Save to timestamped file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rio_batch_generation_results_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(results_data, f, indent=2)

    print(f"\n💾 RESULTS SUMMARY")
    print("=" * 70)
    print(f"📄 Detailed results saved to: {filename}")
    print(f"⏱️  Scene selection: {scene_duration:.2f}s")
    print(f"⏱️  Batch generation: {batch_duration:.2f}s")
    print(f"📊 Total scenes: {len(scene_selection.selected_scenes)}")
    print(f"🎨 Visual prompts: {len(batch_result.visual_prompts)}")
    print(f"🎭 Themes: {', '.join(scene_selection.song_themes)}")
    print(f"🎯 Style consistency: {batch_result.style_consistency[:100]}...")

    print(f"\n🎉 Batch generation test completed successfully!")


async def main():
    """Main test execution."""
    try:
        await run_batch_generation_test()
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())