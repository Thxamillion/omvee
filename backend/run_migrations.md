# Running Database Migrations

## After Creating Your Supabase Project

Once you have your Supabase project set up and credentials, follow these steps:

### Step 1: Run Schema Migration

1. Go to your Supabase dashboard
2. Navigate to **SQL Editor**
3. Copy and paste the contents of `migrations/001_initial_schema.sql`
4. Click **Run** to create all tables, indexes, and functions

### Step 2: Set Up Storage Bucket

1. In Supabase dashboard, go to **Storage**
2. Click **Create bucket**
3. Name: `project-files`
4. Set to **Public** (for easy file access)
5. Click **Create bucket**

### Step 3: Run Storage Migration

1. Back in **SQL Editor**
2. Copy and paste the contents of `migrations/002_storage_setup.sql`
3. Click **Run** to set up storage policies

### Step 4: Add Sample Data (Optional)

1. In **SQL Editor**
2. Copy and paste the contents of `migrations/003_sample_data.sql`
3. Click **Run** to add test data

### Step 5: Verify Setup

Check that these tables were created:
- ✅ projects
- ✅ selected_scenes
- ✅ scene_prompts
- ✅ generated_images
- ✅ video_clips
- ✅ user_approvals
- ✅ final_videos
- ✅ jobs

Check that storage bucket exists:
- ✅ project-files bucket

### Step 6: Update Environment

Update your `backend/.env` file with your Supabase credentials and test the API!

## Alternative: Command Line Setup

If you prefer using the Supabase CLI:

```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Run migrations
supabase db reset --linked
cat migrations/001_initial_schema.sql | supabase db reset --linked --stdin
```

## Troubleshooting

**Error: "relation already exists"**
- Some tables might already exist. You can either:
  - Drop tables manually and re-run
  - Skip the error and continue

**Error: "bucket already exists"**
- The storage bucket was already created. Continue with storage policies.

**Error: "policy already exists"**
- Storage policies were already created. Continue to next step.

Let me know when you've completed the setup and I'll help test the API!