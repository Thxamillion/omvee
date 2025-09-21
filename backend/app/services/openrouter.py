import json
import os
from typing import List, Dict, Any
from datetime import datetime
import aiohttp
from pydantic import ValidationError

from app.models_pydantic import (
    TranscriptionResult,
    SceneSelectionResult,
    PromptGenerationResult
)
from app.config import ModelConfig


class OpenRouterService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")

        self.base_url = "https://openrouter.ai/api/v1"
        self.model = ModelConfig.scene_selection_model

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Thxamillion/omvee",
            "X-Title": "OMVEE Music Video Generator"
        }

    async def _log_to_file_if_test(self, prompt_type: str, prompt: str, response: str, metadata: Dict[str, Any] = None):
        """Log prompt and response to file during test runs for visibility."""
        if os.getenv("ENVIRONMENT") == "test":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
            log_dir = "test_logs"
            os.makedirs(log_dir, exist_ok=True)

            log_entry = {
                "timestamp": timestamp,
                "prompt_type": prompt_type,
                "prompt": prompt,
                "response": response,
                "metadata": metadata or {},
                "model": self.model
            }

            log_file = f"{log_dir}/integration_run_{timestamp}_{prompt_type}.json"
            with open(log_file, "w") as f:
                json.dump(log_entry, f, indent=2)

            print(f"📋 Test log saved: {log_file}")
            print(f"📋 Prompt type: {prompt_type}")
            print(f"📋 Response length: {len(response)} chars")

    async def select_scenes(self, transcription: TranscriptionResult, target_scenes: int = 15, song_metadata: Dict[str, Any] = None) -> SceneSelectionResult:
        """
        Select scenes from transcription using AI analysis.

        Args:
            transcription: The audio transcription with segments
            target_scenes: Number of scenes to select (10-20 range)
            song_metadata: Optional metadata about the song (title, artist, genre)

        Returns:
            SceneSelectionResult with selected scenes
        """
        if not transcription.segments:
            raise ValueError("Transcription must contain segments for scene selection")

        # Validate target_scenes range (15-20 when using AI discretion)
        if not 15 <= target_scenes <= 20:
            target_scenes = 18  # Use 18 as default when AI chooses

        # Build segments text for AI analysis
        segments_text = []
        for i, segment in enumerate(transcription.segments):
            if isinstance(segment, dict) and 'text' in segment and 'start' in segment and 'end' in segment:
                segments_text.append(f"Segment {i}: {segment['start']:.1f}s-{segment['end']:.1f}s: {segment['text']}")
            else:
                # Fallback for different segment formats
                segments_text.append(f"Segment {i}: {segment}")

        song_info = ""
        if song_metadata:
            song_info = f"""
SONG INFORMATION:
- Title: {song_metadata.get('title', 'Unknown')}
- Artist: {song_metadata.get('artist', 'Unknown')}
- Genre: {song_metadata.get('genre', 'Unknown')}
"""

        prompt = f"""You are an expert music video director analyzing song lyrics to select the most cinematic scenes.
{song_info}
TRANSCRIPT SEGMENTS:
{chr(10).join(segments_text)}

TASK: Select between 15-20 scenes from these lyrics that would make the most compelling music video. Use your discretion to choose the optimal number of scenes based on the song content. Each scene should be 5-10 seconds long.

COVERAGE REQUIREMENT: Ensure 100% coverage of the song timeline. When one scene's end_time finishes, the next scene's start_time should begin immediately with NO GAPS. The scenes must cover the entire song from start to finish without skipping any content.

SELECTION CRITERIA:
- Visual storytelling potential (1-10)
- Emotional impact and energy level (1-10)
- Narrative importance to the song (1-10)
- Variety in mood and energy across scenes
- Cinematic appeal and imagery potential
- Complete timeline coverage (no gaps between scenes)

OUTPUT FORMAT (valid JSON only):
{{
  "song_themes": ["theme1", "theme2", "theme3"],
  "energy_arc": "description of song's energy progression",
  "total_scenes_selected": 18,
  "average_scene_length": 7.5,
  "selected_scenes": [
    {{
      "scene_id": 1,
      "title": "Scene title",
      "start_time": 12.5,
      "end_time": 20.0,
      "duration": 7.5,
      "source_segments": [3, 4],
      "lyrics_excerpt": "Combined lyrics text",
      "theme": "Scene theme/mood",
      "energy_level": 7,
      "visual_potential": 9,
      "narrative_importance": 8,
      "reasoning": "Why this scene was selected"
    }}
  ],
  "reasoning_summary": "Overall selection strategy explanation"
}}

Respond with only valid JSON."""

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 4000
                }

                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"OpenRouter API error {response.status}: {error_text}")

                    data = await response.json()

                    # Debug logging
                    print(f"📋 OpenRouter Response Status: {response.status}")
                    print(f"📋 Raw Response: {data}")

                    if 'choices' not in data or not data['choices']:
                        raise Exception("No response choices from OpenRouter API")

                    content = data['choices'][0]['message']['content']
                    print(f"📋 AI Content Response: {content}")

                    # Log to file if in test environment
                    await self._log_to_file_if_test(
                        prompt_type="scene_selection",
                        prompt=prompt,
                        response=content,
                        metadata={
                            "target_scenes": target_scenes,
                            "song_metadata": song_metadata,
                            "segment_count": len(transcription.segments)
                        }
                    )

                    # Strip markdown code blocks if present
                    if content.startswith('```json'):
                        content = content[7:]  # Remove ```json
                    if content.startswith('```'):
                        content = content[3:]   # Remove ```
                    if content.endswith('```'):
                        content = content[:-3]  # Remove trailing ```
                    content = content.strip()

                    # Parse JSON response
                    try:
                        result_json = json.loads(content)
                        return SceneSelectionResult(**result_json)
                    except json.JSONDecodeError as e:
                        raise Exception(f"Invalid JSON response from AI: {content} | Error: {e}")
                    except ValidationError as e:
                        raise Exception(f"Invalid scene selection format: {e}")

        except aiohttp.ClientError as e:
            raise Exception(f"Network error calling OpenRouter: {e}")

    async def generate_visual_prompts(self, scene_selection: SceneSelectionResult) -> PromptGenerationResult:
        """
        Generate visual prompts for selected scenes.

        Args:
            scene_selection: The selected scenes from AI analysis

        Returns:
            PromptGenerationResult with visual prompts
        """
        if not scene_selection.selected_scenes:
            raise ValueError("Scene selection must contain scenes for prompt generation")

        # Build scenes context for AI
        scenes_context = []
        for scene in scene_selection.selected_scenes:
            scenes_context.append(f"""Scene {scene.scene_id}: "{scene.title}"
- Theme: {scene.theme}
- Lyrics: {scene.lyrics_excerpt}
- Energy: {scene.energy_level}/10
- Visual Potential: {scene.visual_potential}/10
- Duration: {scene.duration}s""")

        prompt = f"""You are an expert visual director creating detailed image generation prompts for a music video.

SONG THEMES: {', '.join(scene_selection.song_themes)}
ENERGY ARC: {scene_selection.energy_arc}

SCENES TO VISUALIZE:
{chr(10).join(scenes_context)}

TASK: Create detailed Flux image generation prompts for each scene that will create a cohesive, cinematic music video.

VISUAL STYLE REQUIREMENTS:
- Cinematic lighting and composition
- Consistent visual aesthetic across all scenes
- High production value look
- Emotionally resonant imagery
- Professional music video quality

OUTPUT FORMAT (valid JSON only):
{{
  "total_prompts": {len(scene_selection.selected_scenes)},
  "visual_prompts": [
    {{
      "scene_id": 1,
      "image_prompt": "Detailed prompt for image generation (be very specific about lighting, composition, mood, colors, style)",
      "style_notes": "Style and aesthetic guidance",
      "negative_prompt": "What to avoid in generation",
      "setting": "Scene setting/location",
      "shot_type": "Camera shot type (close-up, wide shot, etc.)",
      "mood": "Overall mood/atmosphere",
      "color_palette": "Suggested color scheme"
    }}
  ],
  "style_consistency": "Overall visual style approach for the music video",
  "generation_notes": "Important notes for image generation"
}}

Respond with only valid JSON."""

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.8,
                    "max_tokens": 4000
                }

                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"OpenRouter API error {response.status}: {error_text}")

                    data = await response.json()

                    if 'choices' not in data or not data['choices']:
                        raise Exception("No response choices from OpenRouter API")

                    content = data['choices'][0]['message']['content']
                    print(f"📋 Visual Prompts AI Response: {content}")

                    # Strip markdown code blocks if present
                    if content.startswith('```json'):
                        content = content[7:]  # Remove ```json
                    if content.startswith('```'):
                        content = content[3:]   # Remove ```
                    if content.endswith('```'):
                        content = content[:-3]  # Remove trailing ```
                    content = content.strip()

                    # Parse JSON response
                    try:
                        result_json = json.loads(content)
                        result = PromptGenerationResult(**result_json)

                        # Debug: Show all complete prompts
                        print(f"\n🎬 ALL {len(result.visual_prompts)} VISUAL PROMPTS:")
                        for i, prompt in enumerate(result.visual_prompts):
                            print(f"\n--- SCENE {prompt.scene_id} ---")
                            print(f"Image Prompt: {prompt.image_prompt}")
                            print(f"Setting: {prompt.setting}")
                            print(f"Shot Type: {prompt.shot_type}")
                            print(f"Mood: {prompt.mood}")
                            print(f"Color Palette: {prompt.color_palette}")

                        return result
                    except json.JSONDecodeError as e:
                        raise Exception(f"Invalid JSON response from AI: {e}")
                    except ValidationError as e:
                        raise Exception(f"Invalid prompt generation format: {e}")

        except aiohttp.ClientError as e:
            raise Exception(f"Network error calling OpenRouter: {e}")

    async def generate_individual_visual_prompt(self, scene: 'SceneSelection', song_metadata: Dict[str, Any] = None) -> 'VisualPrompt':
        """
        Generate a visual prompt for a single scene with focused attention and scene-specific details.

        Args:
            scene: Individual scene to generate prompt for
            song_metadata: Optional metadata about the song

        Returns:
            VisualPrompt with detailed scene-specific generation instructions
        """
        from app.models_pydantic import VisualPrompt

        song_info = ""
        if song_metadata:
            song_info = f"""
SONG CONTEXT:
- Title: {song_metadata.get('title', 'Unknown')}
- Artist: {song_metadata.get('artist', 'Unknown')}
- Genre: {song_metadata.get('genre', 'Unknown')}
"""

        prompt = f"""You are an expert cinematographer creating a specific visual prompt for a music video scene.

{song_info}
SCENE TO VISUALIZE:
- Scene ID: {scene.scene_id}
- Title: "{scene.title}"
- Lyrics: "{scene.lyrics_excerpt}"
- Theme: {scene.theme}
- Duration: {scene.duration} seconds
- Energy Level: {scene.energy_level}/10
- Visual Potential: {scene.visual_potential}/10

TASK: Create a highly specific, lyric-focused image generation prompt that captures the exact imagery and emotion from these lyrics.

REQUIREMENTS:
- Interpret the SPECIFIC lyrics literally and emotionally
- Create vivid, cinema-quality imagery that matches the words
- Include professional photography/cinematography techniques
- Specify exact lighting, composition, and mood
- Make it feel like a professional music video frame
- Include image generation parameters (aspect ratio, style, quality)

OUTPUT FORMAT (valid JSON only):
{{
  "scene_id": {scene.scene_id},
  "image_prompt": "Ultra-detailed, lyric-specific prompt for professional music video scene, including specific lighting, composition, camera angle, mood, and visual elements that directly interpret the lyrics. Include technical specifications for high-quality output.",
  "style_notes": "Specific cinematographic style and aesthetic guidance",
  "negative_prompt": "Specific things to avoid that would diminish the scene's impact",
  "setting": "Exact location/environment described in lyrics",
  "shot_type": "Professional camera shot type and angle",
  "mood": "Specific emotional atmosphere from lyrics",
  "color_palette": "Detailed color scheme that enhances the lyrical content"
}}

Focus on translating the raw emotion and specific imagery from the lyrics into a visual that would make viewers feel the same intensity. Be specific, not generic.

Respond with only valid JSON."""

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.8,
                    "max_tokens": 1000
                }

                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"OpenRouter API error {response.status}: {error_text}")

                    data = await response.json()

                    if 'choices' not in data or not data['choices']:
                        raise Exception("No response choices from OpenRouter API")

                    content = data['choices'][0]['message']['content']
                    print(f"📋 Individual Scene {scene.scene_id} Response: {content}")

                    # Log to file if in test environment
                    await self._log_to_file_if_test(
                        prompt_type="individual_visual_prompt",
                        prompt=prompt,
                        response=content,
                        metadata={
                            "scene_id": scene.scene_id,
                            "scene_title": scene.title,
                            "song_metadata": song_metadata
                        }
                    )

                    # Strip markdown code blocks if present
                    if content.startswith('```json'):
                        content = content[7:]  # Remove ```json
                    if content.startswith('```'):
                        content = content[3:]   # Remove ```
                    if content.endswith('```'):
                        content = content[:-3]  # Remove trailing ```
                    content = content.strip()

                    # Parse JSON response
                    try:
                        result_json = json.loads(content)
                        return VisualPrompt(**result_json)
                    except json.JSONDecodeError as e:
                        raise Exception(f"Invalid JSON response from AI: {content} | Error: {e}")
                    except ValidationError as e:
                        raise Exception(f"Invalid visual prompt format: {e}")

        except aiohttp.ClientError as e:
            raise Exception(f"Network error calling OpenRouter: {e}")

    async def generate_individual_visual_prompt_with_artist(
        self,
        scene: 'SceneSelection',
        artist_reference_images: Dict[str, str],  # {artist_id: image_url}
        song_metadata: Dict[str, Any] = None
    ) -> 'VisualPrompt':
        """
        Generate a visual prompt for a single scene with artist reference images.

        Args:
            scene: Individual scene to generate prompt for
            artist_reference_images: Dictionary mapping artist IDs to reference image URLs
            song_metadata: Optional metadata about the song

        Returns:
            VisualPrompt with detailed scene-specific generation instructions including artist references
        """
        from app.models_pydantic import VisualPrompt

        song_info = ""
        if song_metadata:
            song_info = f"""
SONG CONTEXT:
- Title: {song_metadata.get('title', 'Unknown')}
- Artist: {song_metadata.get('artist', 'Unknown')}
- Genre: {song_metadata.get('genre', 'Unknown')}
"""

        # Build artist reference context
        artist_context = ""
        if artist_reference_images:
            artist_refs = []
            for artist_id, image_url in artist_reference_images.items():
                artist_refs.append(f"- Artist Reference Image: {image_url}")
            artist_context = f"""
ARTIST REFERENCES:
{chr(10).join(artist_refs)}

IMPORTANT: Use the reference image(s) to ensure the generated person matches the actual artist's appearance, clothing style, and distinctive features. Do not create a generic person - reference the specific artist shown in the image.
"""

        prompt = f"""You are an expert cinematographer creating a specific visual prompt for a music video scene.

{song_info}{artist_context}
SCENE TO VISUALIZE:
- Scene ID: {scene.scene_id}
- Title: "{scene.title}"
- Lyrics: "{scene.lyrics_excerpt}"
- Theme: {scene.theme}
- Duration: {scene.duration} seconds
- Energy Level: {scene.energy_level}/10
- Visual Potential: {scene.visual_potential}/10

TASK: Create a highly specific, lyric-focused image generation prompt that captures the exact imagery and emotion from these lyrics, featuring the specific artist(s) shown in the reference image(s).

REQUIREMENTS:
- Interpret the SPECIFIC lyrics literally and emotionally
- Feature the actual artist as shown in reference image (not a generic person)
- Create vivid, cinema-quality imagery that matches the words
- Include professional photography/cinematography techniques
- Specify exact lighting, composition, and mood
- Make it feel like a professional music video frame
- Include image generation parameters (aspect ratio, style, quality)

OUTPUT FORMAT (valid JSON only):
{{
  "scene_id": {scene.scene_id},
  "image_prompt": "Ultra-detailed, lyric-specific prompt for professional music video scene featuring [ARTIST NAME] as shown in reference image, including specific lighting, composition, camera angle, mood, and visual elements that directly interpret the lyrics. Include technical specifications for high-quality output.",
  "style_notes": "Specific cinematographic style and aesthetic guidance with artist consistency",
  "negative_prompt": "Specific things to avoid including generic rapper, different person, unrecognizable face, that would diminish the scene's impact or artist recognition",
  "setting": "Exact location/environment described in lyrics",
  "shot_type": "Professional camera shot type and angle",
  "mood": "Specific emotional atmosphere from lyrics",
  "color_palette": "Detailed color scheme that enhances the lyrical content"
}}

Focus on translating the raw emotion and specific imagery from the lyrics into a visual featuring the actual artist that would make viewers feel the same intensity and recognize the performer.

Respond with only valid JSON."""

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.8,
                    "max_tokens": 1000
                }

                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"OpenRouter API error {response.status}: {error_text}")

                    data = await response.json()

                    if 'choices' not in data or not data['choices']:
                        raise Exception("No response choices from OpenRouter API")

                    content = data['choices'][0]['message']['content']
                    print(f"📋 Artist-Enhanced Scene {scene.scene_id} Response: {content}")

                    # Log to file if in test environment
                    await self._log_to_file_if_test(
                        prompt_type="artist_enhanced_visual_prompt",
                        prompt=prompt,
                        response=content,
                        metadata={
                            "scene_id": scene.scene_id,
                            "scene_title": scene.title,
                            "artist_reference_images": artist_reference_images,
                            "song_metadata": song_metadata
                        }
                    )

                    # Strip markdown code blocks if present
                    if content.startswith('```json'):
                        content = content[7:]  # Remove ```json
                    if content.startswith('```'):
                        content = content[3:]   # Remove ```
                    if content.endswith('```'):
                        content = content[:-3]  # Remove trailing ```
                    content = content.strip()

                    # Parse JSON response
                    try:
                        result_json = json.loads(content)
                        return VisualPrompt(**result_json)
                    except json.JSONDecodeError as e:
                        raise Exception(f"Invalid JSON response from AI: {content} | Error: {e}")
                    except ValidationError as e:
                        raise Exception(f"Invalid visual prompt format: {e}")

        except aiohttp.ClientError as e:
            raise Exception(f"Network error calling OpenRouter: {e}")

    async def _make_openrouter_request(self, system_prompt: str, user_prompt: str, model: str = None) -> str:
        """
        Make a basic OpenRouter API request for text completion.

        Args:
            system_prompt: System instructions for the AI
            user_prompt: User prompt/question
            model: Model to use (defaults to self.model)

        Returns:
            AI response content as string
        """
        model_to_use = model or self.model

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model_to_use,
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }

                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"OpenRouter API error {response.status}: {error_text}")

                    data = await response.json()

                    if 'choices' not in data or not data['choices']:
                        raise Exception("No response choices from OpenRouter API")

                    content = data['choices'][0]['message']['content']
                    return content

        except aiohttp.ClientError as e:
            raise Exception(f"Network error calling OpenRouter: {e}")

    async def generate_video_motion_prompt(
        self,
        scene: 'SceneSelection',
        visual_prompt: 'VisualPrompt',
        image_url: str,
        song_title: str,
        genre: str,
        artist_present: bool = False
    ) -> str:
        """
        Generate a video motion prompt for ByteDance SeeDance using DeepSeek as video director.

        Args:
            scene: Selected scene with lyrics and context
            visual_prompt: Generated visual prompt for context
            image_url: URL of the generated image to analyze
            song_title: Title of the song
            genre: Music genre
            artist_present: Whether artist appears in this scene

        Returns:
            Motion prompt optimized for ByteDance SeeDance-1-Lite
        """
        system_prompt = """You are a professional music video director creating motion prompts for official music videos. Your role is purely creative direction - you're directing a video, not real events.

TECHNICAL GUIDELINES (ByteDance SeeDance):
- Focus on MOVEMENT: describe subject movement, background changes, camera motion
- Be SIMPLE & DIRECT: use clear, simple words
- Include PROMINENT FEATURES: mention distinctive visual elements
- Use CLEAR DEGREE ADVERBS: "quickly", "slowly", "with large amplitude"
- FOLLOW THE IMAGE: never contradict what's visible in the image
- NO NEGATIVE PROMPTS: they don't work with this model

CREATIVE DIRECTION:
- Match the song's actual mood/genre (violent, romantic, energetic, melancholic, etc.)
- Some scenes may have no artist present - focus on environment/objects
- Accurately portray the lyrical content, including violent or mature themes when appropriate
- This is artistic expression for official music videos

OUTPUT: Return only a concise motion prompt optimized for video generation."""

        user_prompt = f"""SCENE CONTEXT:
- Song: {song_title} ({genre})
- Lyrics: "{scene.lyrics_excerpt}"
- Scene Theme: {scene.theme}
- Scene Mood: {visual_prompt.mood}
- Duration: {scene.duration} seconds
- Artist Present: {artist_present}

ANALYZE this image and create a motion prompt that:
1. **START with what you see in the image** - describe the current scene
2. Describes movement/actions that match the lyrics and mood
3. Adds appropriate camera movements (zoom, pan, tilt, etc.)
4. Includes background/environment motion
5. Reflects the song's actual genre and emotional tone

Image URL: {image_url}"""

        try:
            print(f"🎬 Generating video motion prompt for scene {scene.scene_id}")
            print(f"🎬 Song: {song_title} ({genre})")
            print(f"🎬 Lyrics: {scene.lyrics_excerpt[:50]}...")

            response = await self._make_openrouter_request(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=self.model
            )

            motion_prompt = response.strip()

            # Log the generation if in test environment
            await self._log_to_file_if_test(
                prompt_type="video_motion_prompt",
                prompt=user_prompt,
                response=motion_prompt,
                metadata={
                    "scene_id": scene.scene_id,
                    "song_title": song_title,
                    "genre": genre,
                    "artist_present": artist_present,
                    "image_url": image_url,
                    "duration": scene.duration
                }
            )

            print(f"✅ Video motion prompt generated: {motion_prompt[:100]}...")
            return motion_prompt

        except Exception as e:
            print(f"❌ Video motion prompt generation failed: {e}")
            raise Exception(f"Video motion prompt generation failed: {e}")
