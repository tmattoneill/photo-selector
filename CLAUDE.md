# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Image Preference Picker is a sophisticated web application for building image preferences through pairwise comparisons. The system has evolved to include an Elo+σ rating system, directory-based image serving, and gallery/portfolio management capabilities.

**Current State**: The project is transitioning from simple counter-based preferences to a sophisticated Elo rating system with convergence detection (see ALGO-UPDATE.md for full implementation plan).

**Key Features:**
- Elo+σ rating system (μ=1500±σ=350 initial ratings)
- Directory-based image serving with SHA-256 hashing
- Smart skip resurfacing with epsilon-greedy pairing
- Portfolio/gallery system with multiple selection policies
- Convergence detection and auto-finish capabilities
- Real-time statistics and analytics

## Architecture

### Tech Stack
- **Backend**: Python 3.11 + FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS + Testing Library
- **Database**: PostgreSQL 15 with Alembic migrations
- **Deployment**: Docker Compose with nginx
- **Testing**: Pytest (backend), Vitest (frontend)

### Core Components

**Backend** (`backend/app/`):
- `models/` - SQLAlchemy models (Image, Choice, AppState, Portfolio, Gallery, Duplicate)
- `services/` - Business logic services:
  - `directory_service.py` - Filesystem operations and SHA-256 hashing
  - `pairing_service.py` - Epsilon-greedy pairing with skip resurfacing
  - `choice_service.py` - Elo rating calculations and choice processing
  - `portfolio_service.py` - Gallery/portfolio creation and management
  - `convergence_service.py` - Convergence detection algorithms
- `api/routes/` - FastAPI endpoints (health, directory, pair, choice, stats, portfolio, gallery)
- `utils/` - Utilities (image processing, Elo calculations)
- `core/config.py` - Algorithm parameters and settings

**Frontend** (`frontend/src/`):
- `components/` - React components (ImageCard, PairSelector, Header, Stats, PortfolioModal, ResetButton)
- `pages/` - Route pages (Home, StatsPage, GalleryPage)
- `api/` - API client and TypeScript types
- `hooks/` - Custom hooks (useKeyboard for shortcuts)

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

# Run linting
docker compose exec frontend npm run lint
```

### Manual Development
```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend setup
cd frontend
npm install
npm run dev

# Run tests
cd backend && pytest
cd frontend && npm test

# Run linting/type checking
cd frontend && npm run lint
cd frontend && npm run build  # includes tsc typecheck
```

### Database Operations
```bash
# Create migration (from backend/ directory)
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Downgrade one step
alembic downgrade -1

# Reset database (Docker)
docker compose down -v  # removes volumes
docker compose up --build
docker compose exec backend alembic upgrade head
```

## API Architecture

### Core Endpoints
- `GET /api/health` - Health check
- `POST /api/directory` - Set image directory and trigger scan
- `GET /api/pair` - Get image pair using epsilon-greedy algorithm
- `POST /api/choice` - Submit choice and update Elo ratings (LEFT/RIGHT/SKIP)
- `GET /api/stats` - Comprehensive statistics and convergence metrics
- `GET /api/state` - Current convergence state and progress
- `GET /api/image/{sha256}` - Stream image by SHA-256 hash
- Portfolio/Gallery CRUD endpoints

### Image Serving
Images are served directly from filesystem via SHA-256 streaming endpoints, replacing the previous base64 storage approach for better performance and scalability.

## Key Algorithms

### Elo+σ Rating System
- **Initial ratings**: μ=1500, σ=350
- **Expected score**: E(a) = 1/(1+10^((μb-μa)/400))
- **Dynamic K-factor**: K = clamp(24*(σ/350), 8, 48)
- **Sigma decay**: σ_new = max(60, σ*0.97) on each exposure
- **Updates**: Atomic transactions for rating changes

### Epsilon-Greedy Pairing Algorithm
1. **Pool Management**: UNSEEN, ACTIVE, SKIPPED_ELIGIBLE pools
2. **Skip Resurfacing**: Random cooldown (11-49 rounds)
3. **Recent Suppression**: Ring buffers prevent immediate re-pairing
4. **Information Selection**: Maximize uncertainty (σ), minimize rating gap (|Δμ|)
5. **Epsilon Exploration**: 10% random selection within shortlist

### Convergence Detection
- **Top-K Stability**: Track rank swaps over 120-round windows
- **Confidence Intervals**: CI = μ ± z*σ for boundary separation
- **Coverage Requirements**: Minimum exposures per image
- **Auto-finish Criteria**: Multiple conditions for completion detection

## Configuration

### Algorithm Parameters (`backend/app/core/config.py`)
Key settings from algo-update.yaml specification:
- `epsilon_greedy: 0.10` - Exploration rate
- `skip_inject_probability: 0.30` - Skip resurfacing chance
- `skip_resurface_min/max_rounds: 11/49` - Skip cooldown range
- `target_top_k: 40` - Portfolio size target
- `min_exposures_per_image: 5` - Coverage requirement
- `sigma_confident_max: 90.0` - Convergence uncertainty threshold

### Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `MAX_IMAGE_MB` - Maximum image size (default: 250MB)
- `MAX_TOTAL_FILES` - File limit (default: 200,000)
- `CORS_ORIGINS` - Allowed frontend origins
- `PARALLEL_WORKERS` - Hashing workers (default: 4)

### Supported Formats
- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- WebP (`.webp`)
- GIF (`.gif`)

## Testing

### Backend Tests (`backend/tests/`)
- **Unit tests**: Elo calculations, pairing logic, convergence detection
- **Integration tests**: API endpoints, database operations
- **Performance tests**: Large image set handling
- Run with: `pytest` (Docker: `docker compose exec backend pytest`)

### Frontend Tests (`frontend/src/**/*.test.tsx`)
- **Component tests**: React Testing Library with Vitest
- **Interaction tests**: Keyboard shortcuts, user flows
- **API integration**: Mock testing with axios
- Run with: `npm test` (Docker: `docker compose exec frontend npm test`)

## Common Development Tasks

### Adding New Algorithm Parameters
1. Update `backend/app/core/config.py` with new settings
2. Add to `Settings` class with defaults
3. Update algorithm implementations in services/
4. Add tests for parameter validation

### Modifying Rating Logic
- **Core logic**: `backend/app/services/choice_service.py`
- **Elo calculations**: `backend/app/utils/elo_utils.py`
- **Pairing algorithm**: `backend/app/services/pairing_service.py`
- **Tests**: `backend/tests/test_choice_service.py`, `test_pairing.py`

### Frontend Component Development
- **Main UI**: `frontend/src/components/PairSelector.tsx`
- **Statistics**: `frontend/src/components/Stats.tsx`
- **Portfolios**: `frontend/src/components/PortfolioModal.tsx`
- **Styling**: TailwindCSS classes
- **State management**: React hooks and context
- **Keyboard shortcuts**: `frontend/src/hooks/useKeyboard.ts`

### Database Schema Changes
1. Create migration: `cd backend && alembic revision --autogenerate -m "Description"`
2. Review generated migration file in `backend/alembic/versions/`
3. Test migration: `alembic upgrade head`
4. Update models in `backend/app/models/`
5. Update services and API endpoints as needed

## Database Schema

### Core Tables
- `images` - Image metadata with Elo ratings (mu, sigma, exposures, etc.)
- `choices` - User selections with round tracking and rating updates
- `app_state` - Global state (current round, convergence status)
- `duplicates` - SHA-256 duplicate mappings
- `portfolios` - User-created image collections
- `galleries` - Immutable snapshots with selection criteria

### Key Columns
- `images.mu/sigma` - Elo rating with uncertainty
- `images.next_eligible_round` - Skip resurfacing logic
- `images.sha256_hash` - Content-based duplicate detection
- `choices.left_mu_before/after` - Rating change tracking
- `app_state.convergence_status` - System state tracking

## Migration and Rollback

The project includes migration tools for transitioning from the legacy counter-based system to the new Elo system. Key migration considerations:
- Parallel schema support for gradual transition
- Optional legacy data import
- Rollback procedures with feature flags
- Data validation and verification scripts