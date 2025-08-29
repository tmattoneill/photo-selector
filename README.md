# Image Preference Picker

A sophisticated image comparison and ranking application that allows users to build preferences through pairwise comparisons. Features intelligent skip resurfacing, duplicate detection, and comprehensive statistics.

## Features

- **Pairwise Image Comparison**: Compare two images at a time with simple controls
- **Smart Skip Resurfacing**: Skipped images resurface after 11-49 subsequent rounds
- **Duplicate Detection**: SHA-256 content hashing prevents duplicate canonical images
- **Intelligent Pairing**: Prioritizes images with fewer exposures for balanced distribution
- **Keyboard Shortcuts**: Fast navigation with 1, 2, 3 keys
- **Real-time Statistics**: Track likes, unlikes, skips, and exposures
- **Base64 Storage**: Self-contained deployment with images stored in database
- **Responsive UI**: Clean, modern interface built with Tailwind CSS

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: React 18, TypeScript, Vite, TailwindCSS
- **Database**: PostgreSQL 15 with Alembic migrations
- **Deployment**: Docker Compose with nginx
- **Testing**: Pytest (backend), Vitest (frontend)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OR Python 3.11+ and Node.js 18+

### Option 1: Docker (Recommended)

1. **Clone and prepare**:
   ```bash
   git clone <repository>
   cd photo-sort
   cp .env.example .env
   ```

2. **Add sample images** (optional):
   ```bash
   # The samples/ directory is already included with test images
   # Or add your own images to samples/
   ```

3. **Start all services**:
   ```bash
   docker compose up --build
   ```

4. **Initialize database**:
   ```bash
   # In another terminal
   docker compose exec backend alembic upgrade head
   ```

5. **Access the application**:
   - Frontend: http://localhost:5173
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - PgAdmin (optional): http://localhost:5050 (admin@picker.local / admin)

### Option 2: Manual Development Setup

#### Backend Setup

1. **Create virtual environment**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or: venv\\Scripts\\activate  # Windows
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL**:
   ```bash
   # Install PostgreSQL 15
   createdb picker
   ```

4. **Configure environment**:
   ```bash
   cp ../.env.example .env
   # Edit .env with your database URL and image directory
   ```

5. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Start server**:
   ```bash
   uvicorn app.main:app --reload
   ```

#### Frontend Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

## Usage

### Ingesting Images

1. Click "Change Folder" in the top header
2. Enter the absolute path to your image directory
3. Click "Ingest" to process all supported images (jpg, jpeg, png, webp)

### Making Comparisons

- **Left Image**: Click the left image or press `1`
- **Right Image**: Click the right image or press `2` 
- **Skip Both**: Click "Skip Both" or press `3`

### Viewing Statistics

Click "📊 View Statistics" to see:
- Total images, duplicates, and rounds completed
- Most liked and most exposed images
- Per-image statistics including likes, unlikes, skips, and exposures

## API Reference

### Core Endpoints

```bash
# Health check
GET /api/health

# Ingest directory
POST /api/ingest
Content-Type: application/json
{
  "dir": "/path/to/images"
}

# Get image pair
GET /api/pair

# Submit choice
POST /api/choice
Content-Type: application/json
{
  "round": 1,
  "left_id": "uuid",
  "right_id": "uuid", 
  "selection": "LEFT" | "RIGHT" | "SKIP"
}

# Get statistics
GET /api/stats
```

### Sample curl Commands

```bash
# Check API health
curl http://localhost:8000/api/health

# Ingest sample images
curl -X POST http://localhost:8000/api/ingest \\
  -H "Content-Type: application/json" \\
  -d '{"dir": "/absolute/path/to/samples"}'

# Get an image pair
curl http://localhost:8000/api/pair

# Submit a preference
curl -X POST http://localhost:8000/api/choice \\
  -H "Content-Type: application/json" \\
  -d '{
    "round": 1,
    "left_id": "image-uuid-1",
    "right_id": "image-uuid-2", 
    "selection": "LEFT"
  }'

# Get statistics
curl http://localhost:8000/api/stats
```

## Key Algorithms

### Skip Resurfacing

When images are skipped:
1. Both images get `skips` count incremented
2. Each image gets a random requeue round: `current_round + random(11-49)`
3. Images become eligible for injection when `current_round >= requeue_round`
4. Eligible skipped images have a 30% chance of being injected into new pairs

### Pairing Logic

1. Start with canonical images only (no duplicates)
2. Exclude images shown in the immediately previous round
3. Check for eligible skipped images and inject one with 30% probability
4. Otherwise, select two images preferring those with fewer exposures
5. Within exposure tiers, selection is random for fairness

### Duplicate Handling

- Images with identical SHA-256 content hashes are detected as duplicates
- First occurrence becomes the canonical image
- Additional instances are stored as duplicate references
- Only canonical images participate in comparisons
- All file paths are preserved for reference

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests  
cd frontend
npm test

# Run tests in Docker
docker compose exec backend pytest
docker compose exec frontend npm test
```

### Database Migrations

```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```

### Adding New Features

1. Backend changes: Add models, services, routes
2. Update database: Create Alembic migration
3. Frontend changes: Add components, pages, API calls
4. Update tests: Add test cases for new functionality

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | - | PostgreSQL connection string |
| `IMAGE_ROOT` | `/absolute/path/to/images` | Root directory for image ingestion |
| `MAX_IMAGE_MB` | `8` | Maximum image size in MB |
| `API_PREFIX` | `/api` | API route prefix |
| `HOST` | `0.0.0.0` | Server bind host |
| `PORT` | `8000` | Server port |
| `DEBUG` | `False` | Enable debug mode |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Allowed CORS origins |

### Supported Image Formats

- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`) 
- WebP (`.webp`)

Files are validated by both extension and MIME type for security.

## Deployment

### Production Docker

```bash
# Build and run in production mode
docker compose -f docker-compose.yml up -d

# View logs
docker compose logs -f

# Scale services
docker compose up -d --scale backend=2
```

### Security Considerations

- Images are validated by MIME type, not just extension
- Directory traversal protection prevents access outside IMAGE_ROOT
- File size limits prevent resource exhaustion
- SQL injection protection via SQLAlchemy ORM
- CORS configuration restricts API access

## Troubleshooting

### Common Issues

**"Not enough images available for pairing"**
- Ensure images are ingested: POST to `/api/ingest`
- Check that images are supported formats and under size limit
- Verify IMAGE_ROOT environment variable is correct

**Database connection errors**
- Verify PostgreSQL is running and accessible
- Check DATABASE_URL format: `postgresql+psycopg://user:pass@host:port/db`
- Ensure database exists and user has permissions

**Frontend can't reach backend**
- Backend should be running on port 8000
- Check CORS_ORIGINS includes frontend URL
- Verify network connectivity between services

**Images not loading in UI**
- Check browser console for base64 encoding errors
- Verify Pillow can open the image files
- Check file permissions and paths

### Getting Help

1. Check application logs: `docker compose logs`
2. Verify API health: `curl http://localhost:8000/api/health`
3. Check database connectivity: `docker compose exec postgres psql -U user picker`
4. Review browser console for frontend errors

## License

This project is licensed under the MIT License.