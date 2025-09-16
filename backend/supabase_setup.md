# Supabase Setup Guide for OMVEE

## Step 1: Create Supabase Project

1. Go to [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Click "New Project"
3. Choose your organization (or create one)
4. Project details:
   - **Name**: `omvee-backend`
   - **Database Password**: Generate a strong password and save it
   - **Region**: Choose closest to you (e.g., `us-east-1`)
5. Click "Create new project"
6. Wait for project to be ready (~2-3 minutes)

## Step 2: Get Project Credentials

Once your project is ready:

1. Go to **Settings** → **API**
2. Copy these values:
   - **Project URL** (looks like: `https://abc123.supabase.co`)
   - **anon public key** (starts with `eyJ...`)
   - **service_role secret key** (starts with `eyJ...`)

## Step 3: Update Environment File

Update your `backend/.env` file with:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
REDIS_URL=redis://redis:6379/0
OPENROUTER_API_KEY=sk_or_...
REPLICATE_API_TOKEN=r8_...
OPENAI_API_KEY=sk-...
ENVIRONMENT=development
```

## Next Steps

After setting up the project, I'll provide you with:
1. Migration SQL files to create all tables
2. Storage bucket setup commands
3. Test script to verify everything works

Let me know when you have the Supabase project created and the credentials!