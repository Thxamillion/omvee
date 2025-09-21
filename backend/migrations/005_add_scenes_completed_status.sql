-- Migration: 005_add_scenes_completed_status.sql
-- Add missing 'scenes_completed' status to projects table
-- This status is used when scene generation and prompt generation are both complete

-- Drop the existing constraint
ALTER TABLE projects DROP CONSTRAINT IF EXISTS projects_status_check;

-- Add the new constraint with 'scenes_completed' included
ALTER TABLE projects ADD CONSTRAINT projects_status_check
    CHECK (status IN (
        'created', 
        'transcribing', 
        'analyzing', 
        'generating', 
        'reviewing', 
        'complete', 
        'scenes_processing',
        'scenes_completed'
    ));

-- Comment
COMMENT ON CONSTRAINT projects_status_check ON projects IS 'Allowed project status values including scenes_processing and scenes_completed for AI scene generation workflow';
