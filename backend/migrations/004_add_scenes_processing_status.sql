-- Migration: 004_add_scenes_processing_status.sql
-- Add 'scenes_processing' status to projects table constraint
-- This allows the scene generation workflow to properly update project status

-- Drop the existing constraint
ALTER TABLE projects DROP CONSTRAINT projects_status_check;

-- Add the new constraint with 'scenes_processing' included
ALTER TABLE projects ADD CONSTRAINT projects_status_check
    CHECK (status IN ('created', 'transcribing', 'analyzing', 'generating', 'reviewing', 'complete', 'scenes_processing'));

-- Comment
COMMENT ON CONSTRAINT projects_status_check ON projects IS 'Allowed project status values including scenes_processing for AI scene generation workflow';