-- Migration: Add artists table and update existing tables for artist references
-- Date: 2024-09-17
-- Description: Artist asset management system

-- Create artists table
CREATE TABLE artists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    reference_image_urls TEXT[] NOT NULL CHECK (array_length(reference_image_urls, 1) BETWEEN 3 AND 5),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for better performance
CREATE INDEX idx_artists_name ON artists(name);
CREATE INDEX idx_artists_created_at ON artists(created_at);

-- Update projects table to support artist references
ALTER TABLE projects
ADD COLUMN available_artist_ids UUID[] DEFAULT '{}',
ADD COLUMN selected_reference_images JSONB DEFAULT '{}';

-- Update selected_scenes table to support artist assignments
ALTER TABLE selected_scenes
ADD COLUMN featured_artist_ids UUID[] DEFAULT '{}',
ADD COLUMN artist_prominence TEXT DEFAULT 'none' CHECK (artist_prominence IN ('primary', 'background', 'none'));

-- Add indexes for artist references
CREATE INDEX idx_projects_available_artist_ids ON projects USING GIN(available_artist_ids);
CREATE INDEX idx_selected_scenes_featured_artist_ids ON selected_scenes USING GIN(featured_artist_ids);
CREATE INDEX idx_selected_scenes_artist_prominence ON selected_scenes(artist_prominence);

-- Add foreign key constraints (optional, for data integrity)
-- Note: These are commented out as Supabase handles relationships via application logic
-- ALTER TABLE projects ADD CONSTRAINT fk_projects_artists
--   FOREIGN KEY (available_artist_ids) REFERENCES artists(id);
-- ALTER TABLE selected_scenes ADD CONSTRAINT fk_scenes_artists
--   FOREIGN KEY (featured_artist_ids) REFERENCES artists(id);

-- Insert sample artist for testing (optional)
INSERT INTO artists (name, description, reference_image_urls) VALUES
(
    'Rio Da Yung OG',
    'Detroit rapper known for melodic street narratives and authentic storytelling',
    ARRAY[
        'https://example.com/rio_ref_1.jpg',
        'https://example.com/rio_ref_2.jpg',
        'https://example.com/rio_ref_3.jpg'
    ]
);

-- Grant permissions (adjust based on your RLS policies)
-- Enable RLS if not already enabled
ALTER TABLE artists ENABLE ROW LEVEL SECURITY;

-- Create basic RLS policy (adjust based on your auth requirements)
CREATE POLICY "Allow all operations on artists" ON artists
    FOR ALL USING (true) WITH CHECK (true);

-- Comments for documentation
COMMENT ON TABLE artists IS 'Artist profiles with reference images for music video generation';
COMMENT ON COLUMN artists.name IS 'Artist or performer name';
COMMENT ON COLUMN artists.description IS 'Optional description of the artist';
COMMENT ON COLUMN artists.reference_image_urls IS 'Array of 3-5 reference image URLs from Supabase Storage';
COMMENT ON COLUMN projects.available_artist_ids IS 'UUIDs of artists available for this project';
COMMENT ON COLUMN projects.selected_reference_images IS 'JSON mapping of artist_id to selected reference image URL for this project';
COMMENT ON COLUMN selected_scenes.featured_artist_ids IS 'UUIDs of artists featured in this scene';
COMMENT ON COLUMN selected_scenes.artist_prominence IS 'Artist prominence level: primary, background, or none';