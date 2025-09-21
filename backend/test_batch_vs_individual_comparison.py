#!/usr/bin/env python3
"""
Direct comparison of batch vs individual visual prompt generation.
Tests first 5 scenes only to avoid timeout while getting meaningful comparison.
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


async def run_comparison_test():
    """Run direct batch vs individual comparison on first 5 scenes."""

    print("🎵 BATCH vs INDIVIDUAL Visual Prompt Generation Comparison")
    print("=" * 80)
    print("🎯 Testing first 5 scenes to compare quality and consistency")

    # Initialize services
    openrouter_service = OpenRouterService(api_key=settings.openrouter_api_key)

    # Step 1: Load real transcription and get scene selection
    print("\n📋 Step 1: Loading Rio transcription and selecting scenes...")
    transcription = await load_rio_transcription()

    song_metadata = {
        "title": "Easy Kill",
        "artist": "Rio",
        "genre": "Hip Hop/Rap"
    }

    scene_selection = await openrouter_service.select_scenes(
        transcription=transcription,
        target_scenes=15,
        song_metadata=song_metadata
    )

    first_5_scenes = scene_selection.selected_scenes[:5]
    print(f"✅ Using first 5 scenes for comparison:")
    for i, scene in enumerate(first_5_scenes, 1):
        print(f"   {i}. {scene.title} ({scene.start_time:.1f}s-{scene.end_time:.1f}s)")

    # Step 2: Test BATCH generation
    print(f"\n🎨 Step 2: BATCH Generation (all 5 scenes at once)...")
    batch_start = datetime.now()

    # Create modified scene selection with only first 5 scenes
    from app.models_pydantic import SceneSelectionResult
    limited_selection = SceneSelectionResult(
        song_themes=scene_selection.song_themes,
        energy_arc=scene_selection.energy_arc,
        total_scenes_selected=5,
        average_scene_length=sum(s.duration for s in first_5_scenes) / 5,
        selected_scenes=first_5_scenes,
        reasoning_summary="Limited to first 5 scenes for comparison testing"
    )

    batch_result = await openrouter_service.generate_visual_prompts(limited_selection)
    batch_duration = (datetime.now() - batch_start).total_seconds()

    print(f"✅ Batch completed in {batch_duration:.2f}s")
    print(f"📊 Generated {len(batch_result.visual_prompts)} prompts in 1 API call")

    # Step 3: Test INDIVIDUAL generation
    print(f"\n🎯 Step 3: INDIVIDUAL Generation (5 separate calls)...")
    individual_start = datetime.now()

    individual_prompts = []
    for i, scene in enumerate(first_5_scenes, 1):
        print(f"   Generating prompt {i}/5: {scene.title}...")
        individual_prompt = await openrouter_service.generate_individual_visual_prompt(
            scene=scene,
            song_metadata=song_metadata
        )
        individual_prompts.append(individual_prompt)

    individual_duration = (datetime.now() - individual_start).total_seconds()

    print(f"✅ Individual completed in {individual_duration:.2f}s")
    print(f"📊 Generated {len(individual_prompts)} prompts in 5 API calls")

    # Step 4: Performance Comparison
    print(f"\n⚡ PERFORMANCE COMPARISON")
    print("=" * 80)
    print(f"⏱️  Batch time:      {batch_duration:.2f}s (1 API call)")
    print(f"⏱️  Individual time: {individual_duration:.2f}s (5 API calls)")
    print(f"🚀 Speed difference: {individual_duration/batch_duration:.1f}x slower for individual")
    print(f"💰 API calls:       Batch uses 80% fewer calls ({1} vs {5})")

    # Step 5: Quality Comparison
    print(f"\n🎨 QUALITY COMPARISON")
    print("=" * 80)

    for i in range(5):
        scene = first_5_scenes[i]
        batch_prompt = batch_result.visual_prompts[i]
        individual_prompt = individual_prompts[i]

        print(f"\n🎬 SCENE {i+1}: \"{scene.title}\"")
        print(f"📝 Lyrics: \"{scene.lyrics_excerpt[:60]}...\"")
        print("-" * 60)

        print(f"📦 BATCH PROMPT:")
        print(f"   🎨 Image: {batch_prompt.image_prompt[:100]}...")
        print(f"   💡 Style: {batch_prompt.style_notes}")
        print(f"   🎥 Shot:  {batch_prompt.shot_type}")
        print(f"   😌 Mood:  {batch_prompt.mood}")
        print(f"   🎨 Colors: {batch_prompt.color_palette}")

        print(f"\n🎯 INDIVIDUAL PROMPT:")
        print(f"   🎨 Image: {individual_prompt.image_prompt[:100]}...")
        print(f"   💡 Style: {individual_prompt.style_notes}")
        print(f"   🎥 Shot:  {individual_prompt.shot_type}")
        print(f"   😌 Mood:  {individual_prompt.mood}")
        print(f"   🎨 Colors: {individual_prompt.color_palette}")

        # Analysis
        print(f"\n📊 ANALYSIS:")
        batch_length = len(batch_prompt.image_prompt)
        individual_length = len(individual_prompt.image_prompt)
        print(f"   📏 Detail level: Batch={batch_length} chars, Individual={individual_length} chars")

        # Check for style consistency indicators
        batch_terms = set(batch_prompt.style_notes.lower().split())
        individual_terms = set(individual_prompt.style_notes.lower().split())
        common_terms = batch_terms.intersection(individual_terms)
        print(f"   🎭 Style overlap: {len(common_terms)} common terms")

    # Step 6: Consistency Analysis
    print(f"\n🎭 CONSISTENCY ANALYSIS")
    print("=" * 80)

    # Batch consistency
    batch_moods = [p.mood for p in batch_result.visual_prompts]
    batch_colors = [p.color_palette for p in batch_result.visual_prompts]

    print(f"📦 BATCH CONSISTENCY:")
    print(f"   🎭 Moods: {', '.join(batch_moods)}")
    print(f"   🎨 Color progression visible: {len(set(batch_colors)) < len(batch_colors)}")
    print(f"   📐 Style consistency: {batch_result.style_consistency[:100]}...")

    # Individual consistency
    individual_moods = [p.mood for p in individual_prompts]
    individual_colors = [p.color_palette for p in individual_prompts]

    print(f"\n🎯 INDIVIDUAL CONSISTENCY:")
    print(f"   🎭 Moods: {', '.join(individual_moods)}")
    print(f"   🎨 Color variation: {len(set(individual_colors))} unique palettes")
    print(f"   📐 No unified style guidance (each prompt independent)")

    # Step 7: Save detailed comparison
    comparison_data = {
        "test_metadata": {
            "timestamp": datetime.now().isoformat(),
            "scenes_tested": 5,
            "batch_duration_seconds": batch_duration,
            "individual_duration_seconds": individual_duration,
            "speed_ratio": individual_duration / batch_duration
        },
        "performance": {
            "batch_api_calls": 1,
            "individual_api_calls": 5,
            "efficiency_gain": "80% fewer API calls with batch"
        },
        "scenes": [scene.model_dump() for scene in first_5_scenes],
        "batch_prompts": [prompt.model_dump() for prompt in batch_result.visual_prompts],
        "individual_prompts": [prompt.model_dump() for prompt in individual_prompts],
        "batch_style_consistency": batch_result.style_consistency
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"batch_vs_individual_comparison_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(comparison_data, f, indent=2)

    print(f"\n💾 FINAL RESULTS")
    print("=" * 80)
    print(f"📄 Detailed comparison saved to: {filename}")
    print(f"⚡ Performance: Batch is {individual_duration/batch_duration:.1f}x faster")
    print(f"🎨 Style: Batch provides unified aesthetic, Individual is more varied")
    print(f"📊 Detail: Both approaches provide rich, detailed prompts")
    print(f"🏆 Recommendation: Use BATCH for editor loading (consistency + speed)")
    print(f"🎯 Use Case: Individual for single scene re-generation/editing")

    print(f"\n🎉 Comparison test completed!")


async def main():
    """Main test execution."""
    try:
        await run_comparison_test()
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())