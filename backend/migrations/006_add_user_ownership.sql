-- Migration 006: Add user ownership to core tables
-- This migration adds user_id columns to enable multi-user isolation

-- Add user_id to projects table
ALTER TABLE projects ADD COLUMN user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- Add user_id to artists table
ALTER TABLE artists ADD COLUMN user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- Create indexes for performance
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_artists_user_id ON artists(user_id);

-- Update Row Level Security policies for projects
DROP POLICY IF EXISTS "Enable all operations for all users" ON projects;

-- Projects: Users can only access their own projects
CREATE POLICY "Users can view their own projects" ON projects
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own projects" ON projects
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own projects" ON projects
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own projects" ON projects
  FOR DELETE USING (auth.uid() = user_id);

-- Update Row Level Security policies for artists
DROP POLICY IF EXISTS "Enable all operations for all users" ON artists;

-- Artists: Users can only access their own artists
CREATE POLICY "Users can view their own artists" ON artists
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own artists" ON artists
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own artists" ON artists
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own artists" ON artists
  FOR DELETE USING (auth.uid() = user_id);

-- Note: Existing data will have NULL user_id values
-- In production, you would need to assign existing data to specific users
-- For development, existing data can be cleaned up or assigned to test users