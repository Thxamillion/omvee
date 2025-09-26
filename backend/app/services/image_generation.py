"""
Image generation service using Replicate API.
Supports multiple models and reference photo integration.
"""
import os
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

import replicate
from app.models_pydantic import VisualPrompt
from app.config import settings, ModelConfig

logger = logging.getLogger(__name__)


class ImageGenerationService:
    """
    Service for generating images from text prompts and optional reference photos.

    Features:
    - Model-agnostic design for easy switching
    - Reference photo support for artist consistency
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
        self.current_model = ModelConfig.image_model
        self.default_params = {
            "aspect_ratio": "16:9",  # Music video standard
            "number_of_images": 1,
            "prompt_optimizer": True
        }

    async def _log_to_file_if_test(self, generation_type: str, prompt: str, response: Dict[str, Any], metadata: Dict[str, Any] = None):
        """Log image generation request and response to file during test runs."""
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

            print(f"🖼️ Image generation log saved: {log_file}")
            print(f"🖼️ Generation type: {generation_type}")
            print(f"🖼️ Model: {self.current_model}")

    async def generate_image_from_prompt(
        self,
        visual_prompt: VisualPrompt,
        reference_image_url: Optional[str] = None,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate image from visual prompt with optional reference photo.

        Args:
            visual_prompt: VisualPrompt object with detailed generation instructions
            reference_image_url: Optional URL of reference image for subject consistency
            custom_params: Optional parameters to override defaults

        Returns:
            Dictionary with generation results and metadata
        """
        try:
            # Prepare generation parameters
            params = {**self.default_params}
            if custom_params:
                params.update(custom_params)

            # Set the main prompt
            params["prompt"] = visual_prompt.image_prompt

            # Add reference image if provided
            if reference_image_url:
                params["subject_reference"] = reference_image_url

            generation_type = "image_with_reference" if reference_image_url else "image_text_only"

            print(f"🖼️ Generating image with {self.current_model}")
            print(f"🖼️ Prompt: {visual_prompt.image_prompt[:100]}...")
            if reference_image_url:
                print(f"🖼️ Reference: {reference_image_url}")

            print(f"🔧 Full parameters being sent to Replicate:")
            for key, value in params.items():
                if key == "prompt":
                    print(f"  {key}: {str(value)[:100]}...")
                else:
                    print(f"  {key}: {value}")

            # Generate image using Replicate
            start_time = datetime.now()

            # Run the prediction using replicate.run
            output = await asyncio.to_thread(
                self.client.run,
                self.current_model,
                input=params
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Process the output
            image_urls = output if isinstance(output, list) else [output]

            result = {
                "success": True,
                "image_urls": image_urls,
                "generation_metadata": {
                    "model": self.current_model,
                    "scene_id": visual_prompt.scene_id,
                    "reference_used": bool(reference_image_url),
                    "reference_url": reference_image_url,
                    "generation_time": duration,
                    "timestamp": end_time.isoformat()
                },
                "visual_prompt": {
                    "scene_id": visual_prompt.scene_id,
                    "image_prompt": visual_prompt.image_prompt,
                    "setting": visual_prompt.setting,
                    "mood": visual_prompt.mood,
                    "shot_type": visual_prompt.shot_type,
                    "color_palette": visual_prompt.color_palette
                },
                "model_parameters": params
            }

            # Log the generation
            await self._log_to_file_if_test(
                generation_type=generation_type,
                prompt=visual_prompt.image_prompt,
                response=result,
                metadata={
                    "scene_id": visual_prompt.scene_id,
                    "reference_image_url": reference_image_url,
                    "generation_time": duration
                }
            )

            print(f"✅ Image generated successfully in {duration:.2f}s")
            print(f"🖼️ Generated {len(image_urls)} image(s)")

            return result

        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "generation_metadata": {
                    "model": self.current_model,
                    "scene_id": visual_prompt.scene_id,
                    "reference_used": bool(reference_image_url),
                    "error_timestamp": datetime.now().isoformat()
                }
            }

            # Log the error
            await self._log_to_file_if_test(
                generation_type="image_generation_error",
                prompt=visual_prompt.image_prompt,
                response=error_result,
                metadata={"error": str(e)}
            )

            logger.error(f"Image generation failed: {e}")
            raise Exception(f"Image generation failed: {e}")

    async def generate_comparison_images(
        self,
        visual_prompt: VisualPrompt,
        reference_image_url: str
    ) -> Dict[str, Any]:
        """
        Generate both text-only and reference-enhanced images for comparison.

        Args:
            visual_prompt: VisualPrompt object
            reference_image_url: URL of reference image

        Returns:
            Dictionary with both generation results for comparison
        """
        try:
            print(f"🔄 Generating comparison images for scene {visual_prompt.scene_id}")

            # Generate text-only version
            text_only_result = await self.generate_image_from_prompt(visual_prompt)

            # Generate reference-enhanced version
            reference_result = await self.generate_image_from_prompt(
                visual_prompt,
                reference_image_url
            )

            comparison_result = {
                "scene_id": visual_prompt.scene_id,
                "prompt_text": visual_prompt.image_prompt[:100] + "...",
                "reference_image_url": reference_image_url,
                "text_only": text_only_result,
                "with_reference": reference_result,
                "comparison_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "model": self.current_model
                }
            }

            print(f"✅ Comparison complete for scene {visual_prompt.scene_id}")
            print(f"🖼️ Text-only: {len(text_only_result['image_urls'])} images")
            print(f"🖼️ With reference: {len(reference_result['image_urls'])} images")

            return comparison_result

        except Exception as e:
            logger.error(f"Comparison generation failed: {e}")
            raise Exception(f"Comparison generation failed: {e}")

    def estimate_cost(self, num_images: int = 1) -> Dict[str, Any]:
        """
        Estimate cost for image generation.

        Args:
            num_images: Number of images to generate

        Returns:
            Cost estimation breakdown
        """
        # MiniMax Image-01 pricing (approximate)
        cost_per_image = 0.05  # Estimate - check current Replicate pricing

        total_cost = cost_per_image * num_images

        return {
            "model": self.current_model,
            "cost_per_image": cost_per_image,
            "num_images": num_images,
            "total_estimated_cost": total_cost,
            "currency": "USD"
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "model": self.current_model,
            "supports_reference_images": True,
            "supports_aspect_ratios": True,
            "supports_batch_generation": True,
            "max_images_per_request": 4,
            "supported_aspect_ratios": ["1:1", "3:4", "4:3", "16:9", "9:16"],
            "default_params": self.default_params
        }