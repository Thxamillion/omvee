#!/usr/bin/env python3
"""
Test script to compare batch vs individual visual prompt generation approaches.
This will help determine which method produces better results for the editor UI.
"""

import asyncio
import json
import os
from typing import Dict, Any
from datetime import datetime

# Set environment for test logging
os.environ["ENVIRONMENT"] = "test"

from app.services.openrouter import OpenRouterService
from app.services.whisper import WhisperService
from app.models_pydantic import TranscriptionResult
from app.config import settings


async def load_test_transcription() -> TranscriptionResult:
    """Load or create a test transcription for scene selection."""

    # Create a realistic test transcription with segments
    test_segments = [
        {"start": 0.0, "end": 8.5, "text": "Walking down this empty street tonight"},
        {"start": 8.5, "end": 16.2, "text": "City lights are calling out my name"},
        {"start": 16.2, "end": 24.8, "text": "I've been searching for a sign of life"},
        {"start": 24.8, "end": 32.1, "text": "In this world that's driving me insane"},
        {"start": 32.1, "end": 40.3, "text": "But when I close my eyes I see your face"},
        {"start": 40.3, "end": 48.7, "text": "And all the memories come flooding back"},
        {"start": 48.7, "end": 56.9, "text": "The way you used to laugh and sing with me"},
        {"start": 56.9, "end": 64.4, "text": "Now I'm just a ghost upon this track"},
        {"start": 64.4, "end": 72.1, "text": "So I'll keep on running through the night"},
        {"start": 72.1, "end": 80.8, "text": "Chasing dreams that slip away like smoke"},
        {"start": 80.8, "end": 88.3, "text": "Maybe somewhere I'll find peace of mind"},
        {"start": 88.3, "end": 96.7, "text": "And heal this heart that's nearly broke"},
        {"start": 96.7, "end": 104.2, "text": "The morning sun will rise again"},
        {"start": 104.2, "end": 112.8, "text": "And wash away the tears I've cried"},
        {"start": 112.8, "end": 120.5, "text": "But until then I'll hold onto hope"},
        {"start": 120.5, "end": 128.9, "text": "That you're still here right by my side"},
        {"start": 128.9, "end": 136.4, "text": "Walking down this empty street tonight"},
        {"start": 136.4, "end": 144.1, "text": "I know that I will find my way back home"},
        {"start": 144.1, "end": 152.7, "text": "To you, to love, to all that's right"},
        {"start": 152.7, "end": 160.0, "text": "I won't be lost and I won't be alone"}
    ]

    return TranscriptionResult(
        text=" ".join([seg["text"] for seg in test_segments]),
        segments=test_segments,
        language="en",
        duration=160.0
    )


async def run_comparison_test():
    """Run both prompt generation approaches and compare results."""

    print("🎵 Visual Prompt Generation Comparison Test")
    print("=" * 60)

    # Initialize services
    openrouter_service = OpenRouterService(api_key=settings.openrouter_api_key)

    # Step 1: Get scene selection
    print("\n📋 Step 1: Running scene selection...")
    transcription = await load_test_transcription()

    song_metadata = {
        "title": "Empty Streets",
        "artist": "Test Artist",
        "genre": "Alternative Rock"
    }

    scene_selection = await openrouter_service.select_scenes(
        transcription=transcription,
        target_scenes=15,
        song_metadata=song_metadata
    )

    print(f"✅ Selected {len(scene_selection.selected_scenes)} scenes")
    print(f"📊 Song themes: {', '.join(scene_selection.song_themes)}")
    print(f"⚡ Energy arc: {scene_selection.energy_arc}")

    # Display selected scenes
    print("\n🎬 Selected Scenes:")
    for i, scene in enumerate(scene_selection.selected_scenes, 1):
        print(f"  {i:2d}. {scene.title} ({scene.start_time:.1f}s-{scene.end_time:.1f}s)")
        print(f"      Lyrics: \"{scene.lyrics_excerpt}\"")
        print(f"      Theme: {scene.theme} | Energy: {scene.energy_level}/10")

    # Step 2: Test batch generation
    print(f"\n🔄 Step 2: Testing BATCH generation...")
    batch_start = datetime.now()

    batch_result = await openrouter_service.generate_visual_prompts(scene_selection)

    batch_duration = (datetime.now() - batch_start).total_seconds()
    print(f"✅ Batch generation completed in {batch_duration:.2f}s")
    print(f"📊 Generated {len(batch_result.visual_prompts)} prompts")

    # Step 3: Test individual generation
    print(f"\n🔄 Step 3: Testing INDIVIDUAL generation...")
    individual_start = datetime.now()

    individual_prompts = []
    for i, scene in enumerate(scene_selection.selected_scenes, 1):
        print(f"   Generating prompt {i}/{len(scene_selection.selected_scenes)}...")
        individual_prompt = await openrouter_service.generate_individual_visual_prompt(
            scene=scene,
            song_metadata=song_metadata
        )
        individual_prompts.append(individual_prompt)

    individual_duration = (datetime.now() - individual_start).total_seconds()
    print(f"✅ Individual generation completed in {individual_duration:.2f}s")
    print(f"📊 Generated {len(individual_prompts)} prompts")

    # Step 4: Compare results
    print(f"\n📊 COMPARISON RESULTS")
    print("=" * 60)
    print(f"⏱️  Batch time:      {batch_duration:.2f}s")
    print(f"⏱️  Individual time: {individual_duration:.2f}s")
    print(f"🚀 Speed difference: {individual_duration/batch_duration:.1f}x slower for individual")

    # Save detailed comparison
    comparison_data = {
        "test_metadata": {
            "timestamp": datetime.now().isoformat(),
            "batch_duration_seconds": batch_duration,
            "individual_duration_seconds": individual_duration,
            "speed_ratio": individual_duration / batch_duration,
            "total_scenes": len(scene_selection.selected_scenes)
        },
        "scene_selection": scene_selection.model_dump(),
        "batch_prompts": batch_result.model_dump(),
        "individual_prompts": [prompt.model_dump() for prompt in individual_prompts]
    }

    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"prompt_generation_comparison_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(comparison_data, f, indent=2)

    print(f"\n💾 Detailed comparison saved to: {filename}")

    # Show sample prompt comparisons
    print(f"\n🎨 SAMPLE PROMPT COMPARISON (First 3 scenes)")
    print("=" * 60)

    for i in range(min(3, len(scene_selection.selected_scenes))):
        scene = scene_selection.selected_scenes[i]
        batch_prompt = batch_result.visual_prompts[i]
        individual_prompt = individual_prompts[i]

        print(f"\n🎬 Scene {i+1}: \"{scene.title}\"")
        print(f"📝 Lyrics: \"{scene.lyrics_excerpt}\"")
        print(f"\n📦 BATCH PROMPT:")
        print(f"   {batch_prompt.image_prompt[:150]}...")
        print(f"\n🎯 INDIVIDUAL PROMPT:")
        print(f"   {individual_prompt.image_prompt[:150]}...")
        print(f"\n💭 Style Notes Comparison:")
        print(f"   Batch:      {batch_prompt.style_notes}")
        print(f"   Individual: {individual_prompt.style_notes}")

    print(f"\n🎉 Comparison test completed!")
    print(f"📄 Full results available in: {filename}")


async def main():
    """Main test execution."""
    try:
        await run_comparison_test()
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())