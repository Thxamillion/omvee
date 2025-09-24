# OMVEE Project - Claude Code Instructions

## Project Overview
OMVEE is an AI-powered music video generation platform with a Next.js frontend and FastAPI backend.

## Development Setup
- **Frontend**: Next.js 15 + React 19 + TypeScript (port 3001)
- **Backend**: FastAPI + Python (port 8001)
- **Database**: Supabase PostgreSQL
- **Storage**: Supabase Storage for audio files

## Key Commands
```bash
# Frontend (from omvee-ui/)
npm run dev          # Start development server
npm run build        # Build for production
npm run lint         # Run linting
npm run typecheck    # Type checking

# Backend (from backend/)
python -m uvicorn app.main:app --reload --port 8001  # Start API server
pytest               # Run tests
```

## Architecture Notes

### Frontend Structure
- `/src/app/` - Next.js 15 app router pages
- `/src/components/` - React components
- `/src/lib/` - API client, types, utilities

### Key Components
- **VideoEditor.tsx** (1,342 lines) - Main dashboard/projects page (needs refactoring)
- **TranscriptEditor.tsx** - Unified audio upload → transcription → editing workflow
- **apiClient** - Centralized API communication

### API Integration
- Real API client in `src/lib/api.ts`
- TypeScript types in `src/lib/types.ts`
- Presigned URL upload pattern for audio files

## Current State (Phase 1 Complete)
✅ **MVP Working Features:**
- Project creation and management
- Audio file upload with presigned URLs
- OpenAI Whisper transcription integration
- Real-time transcription status polling
- Interactive transcript editing with audio sync
- Unified workflow in single transcript page

## Improvements Tracking
The `/improvements/` folder contains markdown files documenting potential enhancements for each page/component:

- `transcript-editor.md` - TranscriptEditor component improvements
- Future files for other components as needed

Each improvement file includes:
- Current status and functionality
- Known issues with impact assessment
- Potential enhancements
- Technical notes and file references

## Development Guidelines
- Use existing TypeScript types from `/src/lib/types.ts`
- Follow established API patterns in `apiClient`
- Check existing components for patterns before creating new ones
- Add improvement notes to relevant files in `/improvements/` folder

## Recent Changes
- Unified project workflow to single transcript page
- Fixed audio player controls and seek functionality
- Implemented click-to-seek segment interaction
- Removed blocking edit requirement for transcript confirmation
- Fixed duplicate project creation race condition

## Next Priority Areas
1. Refactor VideoEditor.tsx (1,342 lines) into smaller components
2. Address progress bar during transcription
3. Implement video generation pipeline (Phase 2)

---
*This file helps Claude Code understand the project structure and current state for efficient development assistance.*
- Check our current claude code background tasks, befor startig front or backend servers.