-- OMVEE Sample Data
-- Migration: 003_sample_data.sql (Optional)
-- Created: Day 1 - Sample data for testing and development

-- Insert a sample project for testing
INSERT INTO projects (id, name, status) VALUES
('550e8400-e29b-41d4-a716-446655440000', 'Sample Music Video Project', 'created');

-- Insert sample scenes for the project
INSERT INTO selected_scenes (project_id, lyric_excerpt, theme, ai_reasoning, order_idx, start_time_s, end_time_s) VALUES
(
    '550e8400-e29b-41d4-a716-446655440000',
    'Standing in the rain, feeling the pain',
    'melancholy_reflection',
    'This lyric captures a moment of emotional vulnerability and introspection, perfect for a dramatic visual scene',
    1,
    15.5,
    22.3
),
(
    '550e8400-e29b-41d4-a716-446655440000',
    'Dancing through the night, everything''s alright',
    'joyful_celebration',
    'High energy moment expressing freedom and happiness, ideal for vibrant, dynamic visuals',
    2,
    45.8,
    52.1
),
(
    '550e8400-e29b-41d4-a716-446655440000',
    'Looking to the stars, dreaming of tomorrow',
    'hopeful_aspiration',
    'Aspirational and forward-looking theme that suggests limitless possibilities and dreams',
    3,
    78.2,
    85.6
);

-- Insert sample prompts for each scene
INSERT INTO scene_prompts (scene_id, prompt_json, generated_by_model) VALUES
(
    (SELECT id FROM selected_scenes WHERE order_idx = 1 AND project_id = '550e8400-e29b-41d4-a716-446655440000'),
    '{
        "main_prompt": "A cinematic scene of a person standing alone in the rain on an empty city street at dusk",
        "style": "moody, atmospheric, film noir",
        "lighting": "soft streetlight glow, rain reflections",
        "camera_angle": "medium shot, slightly low angle",
        "color_palette": "muted blues and grays with warm street light accents",
        "mood": "melancholic, introspective"
    }',
    'deepseek-chat'
),
(
    (SELECT id FROM selected_scenes WHERE order_idx = 2 AND project_id = '550e8400-e29b-41d4-a716-446655440000'),
    '{
        "main_prompt": "Vibrant dance scene with colorful lights and energetic movement in a crowded nightclub",
        "style": "dynamic, energetic, contemporary",
        "lighting": "strobing colorful lights, neon glow",
        "camera_angle": "wide shot transitioning to close-up",
        "color_palette": "electric blues, hot pinks, bright purples",
        "mood": "joyful, celebratory, alive"
    }',
    'deepseek-chat'
),
(
    (SELECT id FROM selected_scenes WHERE order_idx = 3 AND project_id = '550e8400-e29b-41d4-a716-446655440000'),
    '{
        "main_prompt": "A person gazing up at a starry night sky from a hilltop, city lights twinkling below",
        "style": "dreamy, aspirational, romantic",
        "lighting": "starlight and distant city glow",
        "camera_angle": "wide establishing shot",
        "color_palette": "deep blues and purples with golden city lights",
        "mood": "hopeful, peaceful, inspiring"
    }',
    'deepseek-chat'
);

-- Insert sample jobs to show job tracking
INSERT INTO jobs (project_id, type, status, progress, payload_json) VALUES
(
    '550e8400-e29b-41d4-a716-446655440000',
    'transcribe',
    'completed',
    100,
    '{"audio_file": "sample-song.mp3", "language": "en"}'
),
(
    '550e8400-e29b-41d4-a716-446655440000',
    'analyze_scenes',
    'completed',
    100,
    '{"num_scenes_requested": 3, "style_preference": "cinematic"}'
),
(
    '550e8400-e29b-41d4-a716-446655440000',
    'generate_prompts',
    'completed',
    100,
    '{"model": "deepseek-chat", "prompt_style": "detailed_cinematic"}'
);

-- Note: This sample data helps you test the API endpoints immediately
-- You can delete this data once you have real projects to work with