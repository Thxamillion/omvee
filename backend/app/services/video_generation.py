"""
Video generation service using Replicate API with ByteDance SeeDance.
Supports image-to-video generation for music videos.
"""
import os
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

import replicate
from app.models_pydantic import VisualPrompt, SceneSelection
from app.config import settings, ModelConfig

logger = logging.getLogger(__name__)


class VideoGenerationService:
    """
    Service for generating videos from images and motion prompts.

    Features:
    - Image-to-video generation using ByteDance SeeDance
    - Motion prompt integration
    - Cost tracking and logging
    - Async processing for better performance
    """

    def __init__(self, api_token: str = None):
        self.api_token = api_token or settings.replicate_api_token
        if not self.api_token:
            raise ValueError("Replicate API token is required")

        # Initialize Replicate client
        self.client = replicate.Client(api_token=self.api_token)

        # Current model configuration
        self.current_model = ModelConfig.video_model
        self.default_params = {
            "duration": 5,  # seconds
            "resolution": "720p",
            "aspect_ratio": "16:9",
            "camera_fixed": False
        }

    async def _log_to_file_if_test(self, generation_type: str, prompt: str, response: Dict[str, Any], metadata: Dict[str, Any] = None):
        """Log video generation request and response to file during test runs."""
        if os.getenv("ENVIRONMENT") == "test":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            log_dir = "test_logs"
            os.makedirs(log_dir, exist_ok=True)

            log_entry = {
                "timestamp": timestamp,
                "generation_type": generation_type,
                "model": self.current_model,
                "prompt": prompt,
                "response": response,
                "metadata": metadata or {}
            }

            log_file = f"{log_dir}/integration_run_{timestamp}_{generation_type}.json"
            import json
            with open(log_file, "w") as f:
                json.dump(log_entry, f, indent=2)

            print(f"🎬 Video generation log saved: {log_file}")
            print(f"🎬 Generation type: {generation_type}")
            print(f"🎬 Model: {self.current_model}")

    async def generate_video_from_image(
        self,
        image_url: str,
        motion_prompt: str,
        scene: SceneSelection,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate video from image and motion prompt using ByteDance SeeDance.

        Args:
            image_url: URL of the source image
            motion_prompt: Motion description for video generation
            scene: Scene information for metadata
            custom_params: Optional parameters to override defaults

        Returns:
            Dictionary with generation results and metadata
        """
        try:
            # Prepare generation parameters
            params = {**self.default_params}
            if custom_params:
                params.update(custom_params)

            # Set the main parameters
            params["image"] = image_url
            params["prompt"] = motion_prompt

            # Override duration from scene if available
            if scene.duration:
                params["duration"] = min(max(int(scene.duration), 3), 12)  # ByteDance limits: 3-12 seconds

            generation_type = "video_from_image"

            print(f"🎬 Generating video with {self.current_model}")
            print(f"🎬 Motion prompt: {motion_prompt[:100]}...")
            print(f"🎬 Duration: {params['duration']} seconds")
            print(f"🎬 Image: {image_url}")

            # Generate video using Replicate
            start_time = datetime.now()

            # Run the prediction
            output = await asyncio.to_thread(
                self.client.run,
                self.current_model,
                input=params
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Process the output
            video_urls = output if isinstance(output, list) else [output]

            result = {
                "success": True,
                "video_urls": video_urls,
                "generation_metadata": {
                    "model": self.current_model,
                    "scene_id": scene.scene_id,
                    "image_url": image_url,
                    "motion_prompt": motion_prompt,
                    "generation_time": duration,
                    "timestamp": end_time.isoformat(),
                    "duration_seconds": params["duration"]
                },
                "scene_context": {
                    "scene_id": scene.scene_id,
                    "title": scene.title,
                    "lyrics_excerpt": scene.lyrics_excerpt,
                    "theme": scene.theme,
                    "energy_level": scene.energy_level
                },
                "model_parameters": params
            }

            # Log the generation
            await self._log_to_file_if_test(
                generation_type=generation_type,
                prompt=motion_prompt,
                response=result,
                metadata={
                    "scene_id": scene.scene_id,
                    "image_url": image_url,
                    "generation_time": duration,
                    "video_duration": params["duration"]
                }
            )

            print(f"✅ Video generated successfully in {duration:.2f}s")
            print(f"🎬 Generated {len(video_urls)} video(s)")

            return result

        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "generation_metadata": {
                    "model": self.current_model,
                    "scene_id": scene.scene_id,
                    "image_url": image_url,
                    "error_timestamp": datetime.now().isoformat()
                }
            }

            # Log the error
            await self._log_to_file_if_test(
                generation_type="video_generation_error",
                prompt=motion_prompt,
                response=error_result,
                metadata={"error": str(e)}
            )

            logger.error(f"Video generation failed: {e}")
            raise Exception(f"Video generation failed: {e}")

    def estimate_cost(self, num_videos: int = 1, duration_seconds: int = 5) -> Dict[str, Any]:
        """
        Estimate cost for video generation.

        Args:
            num_videos: Number of videos to generate
            duration_seconds: Duration of each video

        Returns:
            Cost estimation breakdown
        """
        # ByteDance SeeDance pricing (approximate - check current Replicate pricing)
        base_cost_per_second = 0.01  # Estimate
        cost_per_video = base_cost_per_second * duration_seconds

        total_cost = cost_per_video * num_videos

        return {
            "model": self.current_model,
            "cost_per_second": base_cost_per_second,
            "cost_per_video": cost_per_video,
            "duration_seconds": duration_seconds,
            "num_videos": num_videos,
            "total_estimated_cost": total_cost,
            "currency": "USD"
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "model": self.current_model,
            "supports_image_to_video": True,
            "supports_text_to_video": True,
            "min_duration": 3,
            "max_duration": 12,
            "supported_resolutions": ["480p", "720p"],
            "supported_aspect_ratios": ["16:9", "4:3", "1:1"],
            "frame_rate": 24,
            "default_params": self.default_params
        }