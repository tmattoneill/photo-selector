# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Image Preference Picker is a sophisticated web application for building image preferences through pairwise comparisons. Users repeatedly choose between pairs of images or skip, with intelligent resurfacing logic and comprehensive statistics tracking.

**Key Features:**
- Smart skip resurfacing (11-49 round intervals)
- SHA-256 duplicate detection and canonical image management  
- Exposure-balanced pairing algorithm
- Base64 storage for self-contained deployment
- Real-time statistics and analytics

## Architecture

### Tech Stack
- **Backend**: Python 3.11 + FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS
- **Database**: PostgreSQL 15 with Alembic migrations
- **Deployment**: Docker Compose with nginx

### Core Components

**Backend** (`backend/`):
- `app/models/` - SQLAlchemy models (User, Image, Choice, AppState)
- `app/services/` - Business logic (ImageService, PairingService, ChoiceService)
- `app/api/routes/` - FastAPI endpoints (health, ingest, pair, choice, stats)
- `app/utils/` - Image processing utilities (SHA-256, base64, dimensions)

**Frontend** (`frontend/`):
- `src/components/` - React components (ImageCard, PairSelector, Header, Stats)
- `src/pages/` - Route pages (Home, StatsPage)
- `src/api/` - API client and TypeScript types
- `src/hooks/` - Custom hooks (keyboard shortcuts)

## Development Commands

### Docker (Recommended)
```bash
# Start all services
docker compose up --build

# Run database migrations
docker compose exec backend alembic upgrade head

# Run tests
docker compose exec backend pytest
docker compose exec frontend npm test
```

### Manual Development
```bash
# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend  
cd frontend
npm install
npm run dev
```

### Database Operations
```bash
# Create migration
cd backend && alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/ingest` - Ingest directory of images
- `GET /api/pair` - Get image pair for comparison
- `POST /api/choice` - Submit user selection (LEFT/RIGHT/SKIP)
- `GET /api/stats` - Get comprehensive statistics

## Key Algorithms

### Skip Resurfacing Logic
- Skipped images get `next_eligible_round = current_round + random(11, 49)`
- When `current_round >= next_eligible_round`, image becomes eligible
- 30% probability of injecting eligible skipped image into new pairs

### Pairing Algorithm
1. Start with canonical images (no duplicates)
2. Exclude previous round images to avoid repetition
3. Check for eligible skipped images (30% injection probability)
4. Select by minimum exposure count, then random within tier

### Duplicate Detection
- SHA-256 content hashing identifies duplicates
- First occurrence becomes canonical, others reference it
- Only canonical images participate in comparisons
- All file paths preserved for audit trail

## Configuration

### Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `IMAGE_ROOT` - Root directory for image ingestion
- `MAX_IMAGE_MB` - Maximum image size limit (default: 8)
- `CORS_ORIGINS` - Allowed frontend origins

### Supported Formats
- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- WebP (`.webp`)

Images validated by both extension and MIME type.

## Testing

### Backend Tests (`backend/tests/`)
- API endpoint tests with test database
- Service logic tests for pairing and ingestion
- Run with: `pytest`

### Frontend Tests (`frontend/src/**/*.test.tsx`)
- Component unit tests with React Testing Library
- Keyboard shortcut functionality
- Run with: `npm test`

## Common Tasks

### Adding New Image Format
1. Update `settings.supported_formats` in `backend/app/core/config.py`
2. Add MIME type mapping in `backend/app/utils/image_utils.py`
3. Test ingestion with sample files

### Modifying Pairing Logic
- Edit `backend/app/services/pairing_service.py`
- Key method: `_select_by_exposure()` for selection algorithm
- Update tests in `backend/tests/test_pairing.py`

### UI/UX Changes
- Main components in `frontend/src/components/`
- Styling via TailwindCSS classes
- Keyboard shortcuts in `frontend/src/hooks/useKeyboard.ts`

## Database Schema

### Key Tables
- `users` - User accounts (single default user for now)
- `images` - Canonical images and duplicates with statistics
- `choices` - User selections with round tracking
- `app_state` - Application state (current round counter)

### Important Columns
- `images.is_canonical` - Distinguishes originals from duplicates
- `images.next_eligible_round` - Skip resurfacing logic
- `images.exposures/likes/unlikes/skips` - Statistics counters
- `choices.round` - Sequential round numbering