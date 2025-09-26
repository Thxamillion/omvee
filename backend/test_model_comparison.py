#!/usr/bin/env python3
"""
Model Comparison Test for Scene Selection

Tests multiple AI models on the same transcription data to compare:
- Coverage percentage (how much of the song is included in scenes)
- Scene count and distribution
- Processing speed and cost
- Quality metrics

Usage: python test_model_comparison.py
"""

import json
import time
import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
import sys

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.openrouter import OpenRouterService
from app.models_pydantic import TranscriptionResult, TranscriptionSegment
from app.config import settings

# Models to test
MODELS_TO_TEST = [
    "deepseek/deepseek-v3.1-terminus",
    "deepseek/deepseek-r1-0528",
    "anthropic/claude-3.5-sonnet",
    "google/gemini-2.0-flash-exp",
    "openai/gpt-4o-mini"
]

# Model pricing (per 1M tokens)
MODEL_PRICING = {
    "deepseek/deepseek-v3.1-terminus": {"input": 0.25, "output": 1.0},
    "deepseek/deepseek-r1-0528": {"input": 0.40, "output": 1.75},
    "anthropic/claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
    "google/gemini-2.0-flash-exp": {"input": 1.25, "output": 5.0},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60}
}

class ModelComparisonTest:
    def __init__(self):
        # Load environment variables properly
        from dotenv import load_dotenv
        load_dotenv()

        self.openrouter = OpenRouterService()
        self.test_data = None
        self.results = {}
        self.output_dir = Path("model_comparison_results")
        self.output_dir.mkdir(exist_ok=True)

    def load_test_data(self) -> Dict[str, Any]:
        """Load Rio Easy Kill transcription data"""
        transcript_path = Path("test_assets/transcriptions/rio_easy_kill_transcription.json")

        if not transcript_path.exists():
            raise FileNotFoundError(f"Transcript file not found: {transcript_path}")

        with open(transcript_path, 'r') as f:
            data = json.load(f)

        # Transform to the format expected by scene selection (Pydantic models)
        segments = []
        for i, segment in enumerate(data['segments']):
            segments.append({
                'id': i,
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'].strip()
            })

        transcription = TranscriptionResult(
            text=data['text'],
            segments=segments
        )

        self.test_data = {
            'title': 'Easy Kill',
            'artist': 'Rio Da Yung OG',
            'genre': 'Hip Hop/Rap',
            'total_duration': segments[-1]['end'],
            'transcription': transcription,
            'segment_count': len(segments)
        }

        print(f"✅ Loaded test data: {self.test_data['segment_count']} segments, {self.test_data['total_duration']:.1f}s duration")
        return self.test_data

    def format_transcript_for_model(self) -> str:
        """Format transcript segments for model input"""
        transcript_lines = []
        for segment in self.test_data['transcription'].segments:
            transcript_lines.append(
                f"Segment {segment['id']}: {segment['start']:.1f}s-{segment['end']:.1f}s: {segment['text']}"
            )
        return '\n'.join(transcript_lines)

    async def test_model(self, model_name: str, run_number: int) -> Dict[str, Any]:
        """Test a single model and return results"""
        print(f"🧪 Testing {model_name} (Run {run_number})...")

        transcript_text = self.format_transcript_for_model()

        start_time = time.time()
        try:
            # Use the existing scene selection service with custom model
            original_model = self.openrouter.model
            self.openrouter.model = model_name

            result = await self.openrouter.select_scenes(
                transcription=self.test_data['transcription'],
                target_scenes=18,
                song_metadata={
                    'title': self.test_data['title'],
                    'artist': self.test_data['artist'],
                    'genre': self.test_data['genre']
                },
                song_duration=self.test_data['total_duration']
            )

            # Restore original model
            self.openrouter.model = original_model

            end_time = time.time()
            processing_time = end_time - start_time

            # Calculate metrics
            metrics = self.calculate_metrics(result, processing_time, model_name)

            return {
                "success": True,
                "model": model_name,
                "run": run_number,
                "processing_time": processing_time,
                "result": result.model_dump() if hasattr(result, 'model_dump') else result,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time

            return {
                "success": False,
                "model": model_name,
                "run": run_number,
                "processing_time": processing_time,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def calculate_metrics(self, result: 'SceneSelectionResult', processing_time: float, model_name: str) -> Dict[str, Any]:
        """Calculate quality and performance metrics"""
        scenes = result.selected_scenes if hasattr(result, 'selected_scenes') else []

        # Coverage metrics
        total_scene_duration = sum(scene.duration for scene in scenes)
        coverage_percentage = (total_scene_duration / self.test_data['total_duration']) * 100

        # Scene analysis
        scene_count = len(scenes)
        avg_scene_length = total_scene_duration / scene_count if scene_count > 0 else 0

        # Gap analysis
        gaps = self.find_gaps(scenes)
        total_gap_duration = sum(gap['duration'] for gap in gaps)
        gap_percentage = (total_gap_duration / self.test_data['total_duration']) * 100

        # Overlap analysis
        overlaps = self.find_overlaps(scenes)
        total_overlap_duration = sum(overlap['duration'] for overlap in overlaps)

        # Cost estimation
        estimated_cost = self.estimate_cost(result, model_name)

        # Lyric coverage
        lyric_coverage = self.calculate_lyric_coverage(scenes)

        return {
            "coverage_percentage": round(coverage_percentage, 2),
            "scene_count": scene_count,
            "avg_scene_length": round(avg_scene_length, 2),
            "processing_time": round(processing_time, 2),
            "gaps": {
                "count": len(gaps),
                "total_duration": round(total_gap_duration, 2),
                "percentage": round(gap_percentage, 2),
                "details": gaps
            },
            "overlaps": {
                "count": len(overlaps),
                "total_duration": round(total_overlap_duration, 2),
                "details": overlaps
            },
            "estimated_cost": estimated_cost,
            "lyric_coverage": lyric_coverage
        }

    def find_gaps(self, scenes: List['SceneSelection']) -> List[Dict]:
        """Find timeline gaps between scenes"""
        if not scenes:
            return []

        # Sort scenes by start time
        sorted_scenes = sorted(scenes, key=lambda x: x.start_time)
        gaps = []

        # Check gap at beginning
        if sorted_scenes[0].start_time > 0:
            gaps.append({
                "start": 0,
                "end": sorted_scenes[0].start_time,
                "duration": sorted_scenes[0].start_time
            })

        # Check gaps between scenes
        for i in range(len(sorted_scenes) - 1):
            current_end = sorted_scenes[i].end_time
            next_start = sorted_scenes[i + 1].start_time

            if next_start > current_end:
                gaps.append({
                    "start": current_end,
                    "end": next_start,
                    "duration": next_start - current_end
                })

        # Check gap at end
        last_end = sorted_scenes[-1].end_time
        if last_end < self.test_data['total_duration']:
            gaps.append({
                "start": last_end,
                "end": self.test_data['total_duration'],
                "duration": self.test_data['total_duration'] - last_end
            })

        return gaps

    def find_overlaps(self, scenes: List['SceneSelection']) -> List[Dict]:
        """Find timeline overlaps between scenes"""
        if len(scenes) < 2:
            return []

        sorted_scenes = sorted(scenes, key=lambda x: x.start_time)
        overlaps = []

        for i in range(len(sorted_scenes) - 1):
            current = sorted_scenes[i]
            next_scene = sorted_scenes[i + 1]

            if current.end_time > next_scene.start_time:
                overlap_start = next_scene.start_time
                overlap_end = min(current.end_time, next_scene.end_time)

                overlaps.append({
                    "scene1_id": current.scene_id,
                    "scene2_id": next_scene.scene_id,
                    "start": overlap_start,
                    "end": overlap_end,
                    "duration": overlap_end - overlap_start
                })

        return overlaps

    def calculate_lyric_coverage(self, scenes: List['SceneSelection']) -> Dict[str, Any]:
        """Calculate what percentage of original lyrics are included in scenes"""
        original_text = ' '.join(segment['text'].strip() for segment in self.test_data['transcription'].segments)
        original_words = set(original_text.lower().split())

        scene_text = ' '.join(scene.lyrics_excerpt for scene in scenes)
        scene_words = set(scene_text.lower().split())

        covered_words = scene_words.intersection(original_words)
        coverage_percentage = (len(covered_words) / len(original_words)) * 100 if original_words else 0

        return {
            "original_word_count": len(original_words),
            "scene_word_count": len(scene_words),
            "covered_word_count": len(covered_words),
            "coverage_percentage": round(coverage_percentage, 2)
        }

    def estimate_cost(self, result: 'SceneSelectionResult', model_name: str) -> Dict[str, float]:
        """Estimate API cost based on token usage"""
        if model_name not in MODEL_PRICING:
            return {"input": 0, "output": 0, "total": 0}

        pricing = MODEL_PRICING[model_name]

        # Rough token estimation (1 token ≈ 4 characters)
        transcript_chars = len(self.format_transcript_for_model())
        prompt_chars = transcript_chars + 2000  # Add system prompt overhead
        input_tokens = prompt_chars / 4

        response_chars = len(result.model_dump_json())
        output_tokens = response_chars / 4

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return {
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "input_cost": round(input_cost, 4),
            "output_cost": round(output_cost, 4),
            "total_cost": round(input_cost + output_cost, 4)
        }

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run tests for all models with multiple runs for consistency"""
        self.load_test_data()

        print(f"🚀 Starting model comparison test with {len(MODELS_TO_TEST)} models")
        print(f"📊 Test data: {self.test_data['segment_count']} segments, {self.test_data['total_duration']:.1f}s")
        print()

        all_results = {}

        for model in MODELS_TO_TEST:
            print(f"\n{'='*60}")
            print(f"Testing Model: {model}")
            print(f"{'='*60}")

            model_results = []

            # Run each model twice for consistency check
            for run in [1, 2]:
                result = await self.test_model(model, run)
                model_results.append(result)

                if result["success"]:
                    metrics = result["metrics"]
                    print(f"  Run {run}: ✅ {metrics['scene_count']} scenes, {metrics['coverage_percentage']:.1f}% coverage, {metrics['processing_time']:.1f}s, ${metrics['estimated_cost']['total_cost']:.4f}")
                else:
                    print(f"  Run {run}: ❌ Error: {result['error']}")

                # Small delay between runs
                await asyncio.sleep(1)

            all_results[model] = model_results

            # Save individual model results
            model_file = self.output_dir / f"{model.replace('/', '_')}_results.json"
            with open(model_file, 'w') as f:
                json.dump(model_results, f, indent=2)

        # Save combined results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        combined_file = self.output_dir / f"comparison_results_{timestamp}.json"

        final_results = {
            "timestamp": datetime.now().isoformat(),
            "test_data_info": {
                "title": self.test_data['title'],
                "artist": self.test_data['artist'],
                "duration": self.test_data['total_duration'],
                "segment_count": self.test_data['segment_count']
            },
            "models_tested": MODELS_TO_TEST,
            "results": all_results
        }

        with open(combined_file, 'w') as f:
            json.dump(final_results, f, indent=2)

        print(f"\n✅ Test completed! Results saved to: {combined_file}")

        # Generate summary
        self.generate_summary(final_results)

        return final_results

    def generate_summary(self, results: Dict[str, Any]):
        """Generate a summary comparison table"""
        print(f"\n{'='*80}")
        print("MODEL COMPARISON SUMMARY")
        print(f"{'='*80}")

        print(f"{'Model':<30} {'Scenes':<8} {'Coverage':<10} {'Speed':<8} {'Cost':<8} {'Consistency'}")
        print(f"{'-'*80}")

        for model in MODELS_TO_TEST:
            model_results = results["results"][model]
            successful_runs = [r for r in model_results if r["success"]]

            if not successful_runs:
                print(f"{model:<30} {'FAILED':<8} {'FAILED':<10} {'FAILED':<8} {'FAILED':<8} {'FAILED'}")
                continue

            # Calculate averages
            avg_scenes = sum(r["metrics"]["scene_count"] for r in successful_runs) / len(successful_runs)
            avg_coverage = sum(r["metrics"]["coverage_percentage"] for r in successful_runs) / len(successful_runs)
            avg_speed = sum(r["processing_time"] for r in successful_runs) / len(successful_runs)
            avg_cost = sum(r["metrics"]["estimated_cost"]["total_cost"] for r in successful_runs) / len(successful_runs)

            # Calculate consistency (std dev of coverage)
            if len(successful_runs) > 1:
                coverages = [r["metrics"]["coverage_percentage"] for r in successful_runs]
                consistency = abs(coverages[0] - coverages[1])
            else:
                consistency = 0

            consistency_rating = "HIGH" if consistency < 2 else "MED" if consistency < 5 else "LOW"

            print(f"{model:<30} {avg_scenes:<8.0f} {avg_coverage:<10.1f}% {avg_speed:<8.1f}s ${avg_cost:<7.4f} {consistency_rating}")

        print(f"\n📁 Detailed results saved in: {self.output_dir}")

async def main():
    """Main test runner"""
    test = ModelComparisonTest()

    try:
        results = await test.run_all_tests()
        print("\n🎉 Model comparison test completed successfully!")

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())