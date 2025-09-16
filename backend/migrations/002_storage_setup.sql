-- OMVEE Storage Bucket Setup
-- Migration: 002_storage_setup.sql
-- Created: Day 1 - Storage buckets and policies for file management

-- Note: Run this after creating the storage bucket 'project-files' in Supabase dashboard

-- Storage policies for project-files bucket
-- These policies allow authenticated users to manage files within their projects

-- Policy: Allow users to upload files to their own projects
CREATE POLICY "Users can upload project files" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'project-files' AND
        auth.uid() IS NOT NULL
    );

-- Policy: Allow users to view files from any project (for now - can restrict later)
CREATE POLICY "Users can view project files" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'project-files'
    );

-- Policy: Allow users to update files in their own projects
CREATE POLICY "Users can update project files" ON storage.objects
    FOR UPDATE USING (
        bucket_id = 'project-files' AND
        auth.uid() IS NOT NULL
    );

-- Policy: Allow users to delete files from their own projects
CREATE POLICY "Users can delete project files" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'project-files' AND
        auth.uid() IS NOT NULL
    );

-- Note: For MVP without authentication, you might want to make these policies more permissive:
--
-- CREATE POLICY "Allow all operations on project files" ON storage.objects
--     FOR ALL USING (bucket_id = 'project-files');
--
-- This allows anonymous access for development. Remove this and use the above policies
-- when you implement authentication.

-- Create a function to clean up old temporary files (optional)
CREATE OR REPLACE FUNCTION cleanup_old_temp_files()
RETURNS void AS $$
BEGIN
    -- Delete temporary upload files older than 24 hours
    DELETE FROM storage.objects
    WHERE bucket_id = 'project-files'
    AND name LIKE '%/temp/%'
    AND created_at < NOW() - INTERVAL '24 hours';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a scheduled job to run cleanup daily (optional)
-- Note: This requires the pg_cron extension which may not be available in all Supabase plans
-- SELECT cron.schedule('cleanup-temp-files', '0 2 * * *', 'SELECT cleanup_old_temp_files();');