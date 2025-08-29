# Image Preference Picker - Development Progress

## Current Status: ✅ COMPLETE ARCHITECTURE REDESIGN

**Date**: August 29, 2025
**Status**: Major refactoring completed - ready for testing

## What Was Wrong Before

The original architecture had a fundamental misunderstanding:
- ❌ Images were "ingested" into database as base64 blobs
- ❌ Comparisons served from database storage
- ❌ Docker-only directory access
- ❌ Broken image display due to base64/URL mismatches

## Current Correct Architecture

### Core Principle
**Images are read directly from user's selected directory, NOT stored in database. Database only tracks user choices/statistics using SHA256 as the primary key.**

### How It Works Now
1. **Directory Selection**: User sets any local directory via `/api/directory`
2. **Real-Time Scanning**: Each `/api/pair` request scans directory for supported images
3. **SHA256 Tracking**: Uses SHA256 of image content for uniqueness/choice tracking
4. **Direct File Serving**: Images served via `/api/image/{sha256}` from filesystem
5. **Choice Storage**: Only user selections stored in database (likes/unlikes/skips)

## Latest Changes Made

### Backend Changes
1. **Database Schema Redesign**:
   ```python
   # OLD Image model: stored file paths, base64 data, dimensions
   # NEW Image model: only SHA256 + statistics
   class Image(Base):
       sha256 = Column(String(64), primary_key=True)  # SHA256 as PK
       likes = Column(Integer, default=0)
       unlikes = Column(Integer, default=0) 
       skips = Column(Integer, default=0)
       exposures = Column(Integer, default=0)
       # No file storage fields!
   ```

2. **New Services Created**:
   - `DirectoryService`: Real-time directory scanning and pairing logic
   - `DirectoryChoiceService`: Records choices using SHA256 keys
   
3. **API Endpoints Updated**:
   - `POST /api/directory` - Sets working directory (replaces ingest)
   - `GET /api/pair` - Scans directory real-time for image pairs
   - `GET /api/image/{sha256}` - Serves images by SHA256 lookup
   - `POST /api/choice` - Records choices with left_sha256/right_sha256

4. **Key Files Modified**:
   - `backend/app/models/image.py` - Simplified to statistics only
   - `backend/app/models/choice.py` - Uses SHA256 references
   - `backend/app/api/routes/directory.py` - New directory endpoint
   - `backend/app/services/directory_service.py` - Core scanning logic
   - `backend/app/services/directory_choice_service.py` - Choice recording

### Frontend Changes
1. **API Integration Updated**:
   ```typescript
   // OLD: Uses image_id
   // NEW: Uses SHA256
   interface ImageData {
       sha256: string;
       base64: string; // Contains "/api/image/{sha256}" URL
       w: number;
       h: number;
   }
   ```

2. **Key Files Modified**:
   - `frontend/src/api/types.ts` - Updated interfaces for SHA256
   - `frontend/src/api/client.ts` - Added getImageUrl() helper
   - `frontend/src/pages/Home.tsx` - Uses SHA256 for choice submission
   - `frontend/src/components/Header.tsx` - Directory setting UI

## Technical Architecture Details

### Image Pairing Flow
1. User requests `/api/pair`
2. Backend scans current directory for supported images (jpg, png, webp, heic)
3. Calculates SHA256 for each image file on-demand
4. Looks up existing statistics from database by SHA256
5. Uses exposure-balanced algorithm with skip resurfacing (11-49 rounds)
6. Returns two image data objects with `/api/image/{sha256}` URLs

### Choice Recording Flow
1. User makes selection (LEFT/RIGHT/SKIP)
2. Frontend sends `left_sha256`, `right_sha256`, `selection` to `/api/choice`
3. Backend creates/updates Image records in database with statistics
4. Updates exposure counts, likes/unlikes/skips for both images
5. Implements skip resurfacing logic (next_eligible_round)

### Image Serving Flow
1. Frontend requests `http://localhost:8000/api/image/{sha256}`
2. Backend finds file in current directory matching SHA256
3. Serves file directly via FastAPI FileResponse with correct MIME type

## Configuration Changes

- Removed `IMAGE_ROOT` restriction - now accepts any directory path
- Added HEIC support with `pillow-heif` dependency
- Updated Docker to allow broader filesystem access (will need volume updates)

## Current File Structure

```
backend/
├── app/
│   ├── models/
│   │   ├── image.py          # ✅ SHA256-based statistics model
│   │   └── choice.py         # ✅ SHA256 foreign keys
│   ├── services/
│   │   ├── directory_service.py         # ✅ Real-time directory scanning
│   │   └── directory_choice_service.py  # ✅ Choice recording
│   └── api/routes/
│       ├── directory.py      # ✅ Directory selection endpoint  
│       ├── pair.py          # ✅ Directory-based pairing
│       ├── choice.py        # ✅ SHA256-based choice recording
│       └── image.py         # ✅ SHA256-based file serving

frontend/
├── src/
│   ├── api/
│   │   ├── types.ts         # ✅ SHA256-based interfaces
│   │   └── client.ts        # ✅ Directory API + image URL helper
│   ├── components/
│   │   ├── Header.tsx       # ✅ Directory chooser UI
│   │   └── ImageCard.tsx    # ✅ Uses getImageUrl() helper
│   └── pages/
│       └── Home.tsx         # ✅ SHA256-based choice submission
```

## Testing Status

- ✅ Backend syntax validation passes
- ✅ Frontend TypeScript compilation succeeds  
- ✅ All modified files compile without errors
- ⏳ End-to-end testing needed (requires running Docker setup)

## Next Steps When Resuming

1. **Database Migration**: The schema changes are breaking - will need to either:
   - Reset database completely, or
   - Create Alembic migration for the new schema

2. **Docker Updates**: May need to update docker-compose.yml to allow broader filesystem access

3. **Testing**: Start Docker and test the full flow:
   ```bash
   docker compose up --build
   # Test: Set directory → Get pair → Make choice → Verify images display
   ```

4. **Known Issues to Watch**: 
   - SHA256 calculation performance with large directories
   - Directory access permissions across different OS
   - Gallery endpoint not updated for new architecture (still references old fields)

## Key Algorithms Preserved

- **Skip Resurfacing**: 11-49 round random intervals still implemented
- **Exposure Balancing**: Prioritizes images with fewer exposures  
- **Previous Round Exclusion**: Avoids showing same images in consecutive rounds
- **30% Skip Injection**: Eligible skipped images have 30% chance of reappearing

## Success Criteria

When working correctly:
- ✅ User can set any local directory path
- ✅ Images display directly from filesystem (no database storage)
- ✅ Choices are recorded and statistics tracked by SHA256
- ✅ Same image content treated consistently regardless of filename
- ✅ All existing pairing algorithms work with new architecture

**The architecture is now correct and ready for testing!**