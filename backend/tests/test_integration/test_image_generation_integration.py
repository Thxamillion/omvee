"""
Integration tests for image generation with real Rio prompts and artist references.
These tests will generate actual images using MiniMax Image-01 model.
"""

import pytest
import pytest_asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from httpx import AsyncClient

from app.main import app
from app.services.image_generation import ImageGenerationService
from app.models_pydantic import VisualPrompt

# Load environment variables for tests
load_dotenv()


class TestImageGenerationIntegration:
    """Integration tests for image generation with real prompts and references."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment for file logging."""
        os.environ["ENVIRONMENT"] = "test"
        yield
        # Cleanup after test
        if "ENVIRONMENT" in os.environ:
            del os.environ["ENVIRONMENT"]

    @pytest.fixture
    def rio_sample_prompt(self):
        """Sample Rio visual prompt for testing."""
        return VisualPrompt(
            scene_id=1,
            image_prompt="Ultra-detailed, cinematic music video frame featuring Rio Da Yung OG as shown in the reference image, standing confidently in a gritty urban alleyway. The artist is dressed in streetwear, including a hoodie and distressed jeans, with his signature chain visible. He holds a metallic object symbolizing 'peasy steel,' glinting under harsh, low-angle streetlight. The alley is lined with graffiti-covered walls and chain-link fences, with faint smoke rising in the background. The camera angle is a dynamic low-angle shot, emphasizing his dominance and the raw energy of the lyrics. Professional music video quality, 16:9 aspect ratio.",
            style_notes="Cinematic style with gritty realism and urban aesthetics. Artist appearance must match reference image.",
            setting="Dimly lit urban alleyway with graffiti-covered walls",
            shot_type="Low-angle close-up shot with dynamic composition",
            mood="Intense, confident, and gritty",
            color_palette="Dark, desaturated tones with metallic silver highlights"
        )

    @pytest.fixture
    def rio_reference_image_url(self):
        """Rio reference image URL for testing."""
        # In real implementation, this would come from artist database
        return "https://example.com/rio_ref_1.jpg"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_image_generation_service_creation(self):
        """Test that ImageGenerationService can be created and configured."""
        try:
            service = ImageGenerationService()

            # Test service properties
            assert service.current_model == "minimax/image-01"
            assert service.default_params["aspect_ratio"] == "16:9"
            assert service.default_params["number_of_images"] == 1

            # Test model info
            model_info = service.get_model_info()
            assert model_info["supports_reference_images"] is True
            assert "16:9" in model_info["supported_aspect_ratios"]

            # Test cost estimation
            cost_estimate = service.estimate_cost(2)
            assert cost_estimate["num_images"] == 2
            assert cost_estimate["total_estimated_cost"] > 0

            print(f"✅ Service created with model: {service.current_model}")
            print(f"✅ Cost per image: ${cost_estimate['cost_per_image']}")

        except ValueError as e:
            if "API token" in str(e):
                pytest.skip("Replicate API token not configured for integration tests")
            else:
                raise

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_text_only_image_generation(self, rio_sample_prompt):
        """Test generating image from text prompt only (no reference)."""
        try:
            service = ImageGenerationService()

            print(f"🖼️ Generating text-only image for scene {rio_sample_prompt.scene_id}")
            print(f"🖼️ Prompt: {rio_sample_prompt.image_prompt[:100]}...")

            result = await service.generate_image_from_prompt(rio_sample_prompt)

            # Verify result structure
            assert result["success"] is True
            assert "image_urls" in result
            assert len(result["image_urls"]) > 0
            assert result["generation_metadata"]["reference_used"] is False

            # Verify metadata
            metadata = result["generation_metadata"]
            assert metadata["model"] == "minimax/image-01"
            assert metadata["scene_id"] == 1
            assert "generation_time" in metadata

            print(f"✅ Generated {len(result['image_urls'])} image(s)")
            print(f"🖼️ Generation time: {metadata['generation_time']:.2f}s")
            print(f"🖼️ Image URLs: {result['image_urls']}")

            # Check that test logs were created
            test_logs_dir = Path("test_logs")
            if test_logs_dir.exists():
                log_files = list(test_logs_dir.glob("*image_text_only*.json"))
                print(f"📋 Text-only generation log files: {len(log_files)}")

            return result

        except ValueError as e:
            if "API token" in str(e):
                pytest.skip("Replicate API token not configured for integration tests")
            else:
                raise
        except Exception as e:
            if "authentication" in str(e).lower() or "token" in str(e).lower():
                pytest.skip(f"Authentication issue: {e}")
            else:
                raise

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_reference_image_generation(self, rio_sample_prompt, rio_reference_image_url):
        """Test generating image with artist reference photo."""
        try:
            service = ImageGenerationService()

            print(f"🖼️ Generating image with reference for scene {rio_sample_prompt.scene_id}")
            print(f"🖼️ Reference: {rio_reference_image_url}")

            result = await service.generate_image_from_prompt(
                rio_sample_prompt,
                reference_image_url=rio_reference_image_url
            )

            # Verify result structure
            assert result["success"] is True
            assert "image_urls" in result
            assert len(result["image_urls"]) > 0
            assert result["generation_metadata"]["reference_used"] is True
            assert result["generation_metadata"]["reference_url"] == rio_reference_image_url

            # Verify metadata
            metadata = result["generation_metadata"]
            assert metadata["model"] == "minimax/image-01"
            assert metadata["scene_id"] == 1

            print(f"✅ Generated {len(result['image_urls'])} image(s) with reference")
            print(f"🖼️ Generation time: {metadata['generation_time']:.2f}s")
            print(f"🖼️ Image URLs: {result['image_urls']}")

            # Check that test logs were created
            test_logs_dir = Path("test_logs")
            if test_logs_dir.exists():
                log_files = list(test_logs_dir.glob("*image_with_reference*.json"))
                print(f"📋 Reference image generation log files: {len(log_files)}")

            return result

        except ValueError as e:
            if "API token" in str(e):
                pytest.skip("Replicate API token not configured for integration tests")
            else:
                raise
        except Exception as e:
            if "authentication" in str(e).lower() or "token" in str(e).lower():
                pytest.skip(f"Authentication issue: {e}")
            else:
                raise

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_comparison_generation(self, rio_sample_prompt, rio_reference_image_url):
        """Test generating both text-only and reference images for comparison."""
        try:
            service = ImageGenerationService()

            print(f"🔄 Generating comparison images for scene {rio_sample_prompt.scene_id}")

            result = await service.generate_comparison_images(
                rio_sample_prompt,
                rio_reference_image_url
            )

            # Verify comparison structure
            assert "text_only" in result
            assert "with_reference" in result
            assert result["scene_id"] == 1
            assert result["reference_image_url"] == rio_reference_image_url

            # Verify both results
            text_only = result["text_only"]
            with_reference = result["with_reference"]

            assert text_only["success"] is True
            assert with_reference["success"] is True
            assert text_only["generation_metadata"]["reference_used"] is False
            assert with_reference["generation_metadata"]["reference_used"] is True

            print(f"✅ Comparison complete:")
            print(f"🖼️ Text-only images: {len(text_only['image_urls'])}")
            print(f"🖼️ Reference images: {len(with_reference['image_urls'])}")
            print(f"🖼️ Text-only URLs: {text_only['image_urls']}")
            print(f"🖼️ Reference URLs: {with_reference['image_urls']}")

            return result

        except ValueError as e:
            if "API token" in str(e):
                pytest.skip("Replicate API token not configured for integration tests")
            else:
                raise
        except Exception as e:
            if "authentication" in str(e).lower() or "token" in str(e).lower():
                pytest.skip(f"Authentication issue: {e}")
            else:
                raise

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_api_endpoints(self):
        """Test image generation API endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as client:

            # Test model info endpoint
            model_response = await client.get("/api/image-generation/model-info")
            if model_response.status_code == 200:
                model_data = model_response.json()
                assert model_data["model"] == "minimax/image-01"
                assert model_data["supports_reference_images"] is True
                print(f"✅ Model info: {model_data['model']}")
            else:
                pytest.skip("Image generation service not available")

            # Test cost estimate endpoint
            cost_response = await client.get("/api/image-generation/cost-estimate?num_images=2")
            if cost_response.status_code == 200:
                cost_data = cost_response.json()
                assert cost_data["num_images"] == 2
                assert cost_data["total_estimated_cost"] > 0
                print(f"✅ Cost estimate: ${cost_data['total_estimated_cost']} for 2 images")

            # Test sample prompt endpoint
            prompt_response = await client.get("/api/image-generation/test-rio-prompt")
            assert prompt_response.status_code == 200
            prompt_data = prompt_response.json()
            assert "image_prompt" in prompt_data
            assert "Rio Da Yung OG" in prompt_data["image_prompt"]
            print(f"✅ Sample prompt contains: {len(prompt_data['image_prompt'])} characters")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_rio_workflow(self, rio_transcription):
        """Test complete workflow: transcription -> scenes -> prompts -> images."""
        try:
            # This test combines all previous work
            from app.services.openrouter import OpenRouterService

            print("🎬 Starting end-to-end Rio workflow test...")

            # Step 1: Use saved transcription (already done via fixture)
            assert len(rio_transcription.segments) > 0
            print(f"✅ Step 1: Transcription loaded ({len(rio_transcription.segments)} segments)")

            # Step 2: Generate scenes
            openrouter_service = OpenRouterService()
            scenes_result = await openrouter_service.select_scenes(
                transcription=rio_transcription,
                target_scenes=16
            )
            assert len(scenes_result.selected_scenes) >= 15
            print(f"✅ Step 2: {len(scenes_result.selected_scenes)} scenes selected")

            # Step 3: Generate enhanced prompt for first scene
            first_scene = scenes_result.selected_scenes[0]
            artist_references = {"029d7f1b-1278-4a2f-94a0-38b20a452515": "https://example.com/rio_ref_1.jpg"}

            visual_prompt = await openrouter_service.generate_individual_visual_prompt_with_artist(
                scene=first_scene,
                artist_reference_images=artist_references
            )
            assert "Rio Da Yung OG" in visual_prompt.image_prompt
            print(f"✅ Step 3: Artist-enhanced prompt generated")
            print(f"🎨 Prompt preview: {visual_prompt.image_prompt[:100]}...")

            # Step 4: Generate image with artist reference
            image_service = ImageGenerationService()
            image_result = await image_service.generate_image_from_prompt(
                visual_prompt,
                reference_image_url="https://example.com/rio_ref_1.jpg"
            )

            assert image_result["success"] is True
            assert len(image_result["image_urls"]) > 0
            print(f"✅ Step 4: Image generated successfully")
            print(f"🖼️ Final image URL: {image_result['image_urls'][0]}")

            # Check all logs were created
            test_logs_dir = Path("test_logs")
            if test_logs_dir.exists():
                all_logs = list(test_logs_dir.glob("*.json"))
                scene_logs = [f for f in all_logs if "scene_selection" in f.name]
                prompt_logs = [f for f in all_logs if "artist_enhanced" in f.name]
                image_logs = [f for f in all_logs if "image_with_reference" in f.name]

                print(f"📋 Total workflow logs: {len(all_logs)}")
                print(f"📋 Scene selection: {len(scene_logs)}")
                print(f"📋 Enhanced prompts: {len(prompt_logs)}")
                print(f"📋 Image generation: {len(image_logs)}")

            return {
                "transcription_segments": len(rio_transcription.segments),
                "scenes_selected": len(scenes_result.selected_scenes),
                "enhanced_prompt": visual_prompt.image_prompt[:100] + "...",
                "image_urls": image_result["image_urls"],
                "workflow_complete": True
            }

        except ValueError as e:
            if "API token" in str(e):
                pytest.skip("Replicate API token not configured for integration tests")
            else:
                raise
        except Exception as e:
            if "authentication" in str(e).lower() or "token" in str(e).lower():
                pytest.skip(f"Authentication issue: {e}")
            else:
                raise