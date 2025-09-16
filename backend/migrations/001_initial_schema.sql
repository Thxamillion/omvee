-- OMVEE Initial Database Schema
-- Migration: 001_initial_schema.sql
-- Created: Day 1 - Initial tables for AI music video generation

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Projects table - Main project entity
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    audio_path VARCHAR(500),
    transcript_text TEXT,
    status VARCHAR(50) DEFAULT 'created' CHECK (status IN ('created', 'transcribing', 'analyzing', 'generating', 'reviewing', 'complete')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Selected scenes table - AI-selected lyric moments
CREATE TABLE selected_scenes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    lyric_excerpt TEXT NOT NULL,
    theme VARCHAR(255) NOT NULL,
    ai_reasoning TEXT,
    order_idx INTEGER NOT NULL,
    start_time_s REAL,
    end_time_s REAL,
    CONSTRAINT order_idx_positive CHECK (order_idx >= 0)
);

-- Scene prompts table - AI-generated visual prompts
CREATE TABLE scene_prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scene_id UUID NOT NULL REFERENCES selected_scenes(id) ON DELETE CASCADE,
    prompt_json JSONB NOT NULL,
    generated_by_model VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Generated images table - Flux-generated images
CREATE TABLE generated_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    scene_id UUID NOT NULL REFERENCES selected_scenes(id) ON DELETE CASCADE,
    prompt_id UUID NOT NULL REFERENCES scene_prompts(id) ON DELETE CASCADE,
    image_url VARCHAR(500),
    replicate_prediction_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'generating' CHECK (status IN ('generating', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Video clips table - Image-to-video conversions
CREATE TABLE video_clips (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    image_id UUID NOT NULL REFERENCES generated_images(id) ON DELETE CASCADE,
    video_url VARCHAR(500),
    duration_s REAL,
    replicate_prediction_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'generating' CHECK (status IN ('generating', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT duration_positive CHECK (duration_s > 0)
);

-- User approvals table - Review and approval system
CREATE TABLE user_approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    scene_id UUID REFERENCES selected_scenes(id) ON DELETE CASCADE,
    video_clip_id UUID REFERENCES video_clips(id) ON DELETE CASCADE,
    approved BOOLEAN NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT approval_target CHECK (scene_id IS NOT NULL OR video_clip_id IS NOT NULL)
);

-- Final videos table - Assembled music videos
CREATE TABLE final_videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    video_path VARCHAR(500),
    status VARCHAR(50) DEFAULT 'assembling' CHECK (status IN ('assembling', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Jobs table - Async job tracking
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('transcribe', 'analyze_scenes', 'generate_prompts', 'generate_images', 'generate_clips', 'assemble_video')),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    payload_json JSONB,
    result_json JSONB,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_updated_at ON projects(updated_at DESC);

CREATE INDEX idx_selected_scenes_project_id ON selected_scenes(project_id);
CREATE INDEX idx_selected_scenes_order ON selected_scenes(project_id, order_idx);

CREATE INDEX idx_scene_prompts_scene_id ON scene_prompts(scene_id);

CREATE INDEX idx_generated_images_project_id ON generated_images(project_id);
CREATE INDEX idx_generated_images_scene_id ON generated_images(scene_id);
CREATE INDEX idx_generated_images_status ON generated_images(status);

CREATE INDEX idx_video_clips_project_id ON video_clips(project_id);
CREATE INDEX idx_video_clips_image_id ON video_clips(image_id);
CREATE INDEX idx_video_clips_status ON video_clips(status);

CREATE INDEX idx_user_approvals_project_id ON user_approvals(project_id);
CREATE INDEX idx_user_approvals_scene_id ON user_approvals(scene_id);
CREATE INDEX idx_user_approvals_video_clip_id ON user_approvals(video_clip_id);

CREATE INDEX idx_final_videos_project_id ON final_videos(project_id);
CREATE INDEX idx_final_videos_status ON final_videos(status);

CREATE INDEX idx_jobs_project_id ON jobs(project_id);
CREATE INDEX idx_jobs_type ON jobs(type);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to automatically update updated_at
CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE projects IS 'Main project entity for AI music video generation';
COMMENT ON TABLE selected_scenes IS 'AI-selected lyric moments that will become video scenes';
COMMENT ON TABLE scene_prompts IS 'AI-generated visual prompts for each scene';
COMMENT ON TABLE generated_images IS 'Static images generated from prompts using Flux';
COMMENT ON TABLE video_clips IS 'Video clips generated from static images';
COMMENT ON TABLE user_approvals IS 'User review and approval of scenes and clips';
COMMENT ON TABLE final_videos IS 'Final assembled music videos';
COMMENT ON TABLE jobs IS 'Async job tracking for AI pipeline operations';

COMMENT ON COLUMN projects.status IS 'Project workflow status';
COMMENT ON COLUMN selected_scenes.order_idx IS 'Scene order in the final video';
COMMENT ON COLUMN generated_images.replicate_prediction_id IS 'Replicate API prediction ID for tracking';
COMMENT ON COLUMN video_clips.duration_s IS 'Video clip duration in seconds';
COMMENT ON COLUMN jobs.progress IS 'Job completion percentage (0-100)';