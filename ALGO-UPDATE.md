# ALGO-UPDATE.md - Implementation Plan for Elo+σ Rating System

## Executive Summary
Complete overhaul of the image preference system, replacing simple counters with an Elo+σ rating system, directory-based image serving, sophisticated pairing algorithms, and convergence detection.

## Phase 1: Database & Core Infrastructure (Days 1-3)

### 1.1 Database Migration Strategy
- **Create new schema alongside existing** (parallel run capability)
- New tables: images (with mu/sigma), choices, app_state, duplicates, galleries, gallery_images
- Migration script to optionally import existing preferences as initial choices
- Add SHA-256 hashing for all images

### 1.2 Directory Service Implementation
- Create `DirectoryService` class for filesystem operations
- Implement SHA-256 hashing with caching (path, size, mtime)
- Support incremental rescans with parallel hashing
- Replace base64 storage with file streaming

### 1.3 Core Models Update
- Update SQLAlchemy models for new schema
- Add Elo rating fields (mu=1500, sigma=350)
- Remove base64_data field
- Add round tracking and skip resurfacing fields

## Phase 2: Rating Algorithm Implementation (Days 4-6)

### 2.1 Elo+σ Rating System
- Implement expected score calculation: E(a) = 1/(1+10^((μb-μa)/400))
- Dynamic K-factor: K = clamp(24*(σ/350), 8, 48)
- Sigma decay on exposure: σ_new = max(60, σ*0.97)
- Atomic transaction updates for choices

### 2.2 Pairing Engine
- Implement pool definitions (UNSEEN, ACTIVE, SKIPPED_ELIGIBLE)
- Information-theoretic pair selection (maximize σ, minimize |Δμ|)
- Skip resurfacing with random cooldown (11-49 rounds)
- Recent-pair suppression with ring buffers

### 2.3 Choice Processing
- LEFT/RIGHT updates Elo ratings
- SKIP sets next_eligible_round
- Track likes/unlikes/skips separately
- Clear skip cooldowns on actual choice

## Phase 3: Advanced Features (Days 7-9)

### 3.1 Convergence Detection
- Track top-K stability over 120-round windows
- Compute confidence intervals: CI = μ ± z*σ
- Boundary gap calculation for separation
- Auto-finish predicates and UI signals

### 3.2 Gallery System
- Multiple selection policies (top_k, threshold_mu, threshold_ci, manual)
- Duplicate handling options (include/collapse/exclude)
- Dense ranking with tie-breaking
- Immutable snapshots at creation time

### 3.3 Telemetry & Analytics
- Per-round state snapshots
- Top-K tracking with swap detection
- Coverage metrics (seen vs unseen)
- Convergence indicators

## Phase 4: API & Backend Updates (Days 10-12)

### 4.1 New Endpoints
- `POST /api/directory` - Set root directory
- `GET /api/pair` - Enhanced with meta info
- `POST /api/choice` - Elo updates
- `GET /api/state` - Convergence status
- `GET /api/image/{sha256}` - Stream from disk
- Gallery CRUD endpoints

### 4.2 Service Refactoring
- Replace ImageService with DirectoryService
- Rewrite PairingService for new algorithm
- Update ChoiceService for Elo calculations
- Add GalleryService for collections

### 4.3 Performance Optimizations
- In-memory caching for hot paths
- Connection pooling for DB
- Streaming for large images
- Parallel hashing workers

## Phase 5: Frontend Updates (Days 13-15)

### 5.1 Core UI Changes
- Display μ and σ instead of simple stats
- Progress indicators for convergence
- Gallery management interface
- Directory selection dialog

### 5.2 New Components
- ConvergenceMeters (gap, uncertainty, stability)
- GalleryView and GalleryList
- DirectoryPicker
- RatingDisplay (μ ± σ visualization)

### 5.3 UX Enhancements
- Real-time convergence feedback
- "Ready to finish" modal
- Keyboard shortcuts preserved
- Loading states for directory scans

## Phase 6: Testing & Migration (Days 16-18)

### 6.1 Test Coverage
- Unit tests for Elo calculations
- Integration tests for pairing logic
- Performance tests (50k images)
- End-to-end user flows

### 6.2 Migration Tools
- Data conversion scripts
- Rollback procedures
- Parallel run capability
- Verification scripts

### 6.3 Documentation
- API documentation
- Algorithm explanation
- Deployment guide
- User manual updates

## Second-Order Impacts

### Performance Considerations
- **Disk I/O increase**: Streaming from filesystem vs cached base64
- **Memory usage**: In-memory caching of SHA mappings
- **Network traffic**: Larger payloads without base64 compression
- **Solution**: Implement CDN/caching layer, optimize chunk sizes

### User Experience Changes
- **Learning curve**: More complex rating system
- **Longer convergence**: Needs more comparisons for stability
- **Better results**: More accurate preference modeling
- **Solution**: Progressive disclosure, tooltips, visual guides

### Data Migration Challenges
- **Incompatible schemas**: Cannot directly map old to new
- **Lost history**: Some statistics won't transfer
- **Solution**: Optional legacy import, clear communication

## Third-Order Impacts

### Operational Complexity
- **Directory management**: Users must maintain file organization
- **Backup considerations**: Images no longer in database
- **Monitoring needs**: More metrics to track
- **Solution**: Admin tools, monitoring dashboards

### Scalability Changes
- **Better**: No database bloat from base64
- **Worse**: Filesystem dependency
- **Different**: More complex caching requirements
- **Solution**: Consider S3/object storage for future

### Future Extensibility
- **Positive**: Gallery system enables sharing/export
- **Positive**: Elo system can incorporate time decay
- **Positive**: Directory service can add watch/sync
- **Consideration**: API versioning strategy needed

## Risk Mitigation

### Critical Risks
1. **Data loss during migration**: Implement comprehensive backups
2. **Performance degradation**: Extensive load testing required
3. **User confusion**: Gradual rollout with feature flags
4. **Algorithm bugs**: Extensive unit testing of Elo math

### Rollback Strategy
- Database migrations reversible
- Keep old schema tables temporarily
- Feature flags for gradual enablement
- Parallel run capability for validation

## Implementation Order

### Week 1
1. Database schema and migrations
2. Directory service with SHA-256
3. Basic Elo implementation

### Week 2
4. Pairing algorithm
5. Convergence detection
6. Gallery system

### Week 3
7. Frontend updates
8. Testing suite
9. Migration tools
10. Documentation

## Success Metrics
- All images rated with stable μ/σ
- Convergence achieved in <500 comparisons
- Gallery creation from converged set
- No data loss during migration
- Performance targets met (<50ms pairing)

## Next Steps
1. Review and approve plan
2. Set up development branch
3. Begin Phase 1 implementation
4. Daily progress reviews
5. Testing at each phase completion

## Key Implementation Files

### Backend Changes Required
- `backend/app/models/` - Complete schema overhaul
- `backend/app/services/directory_service.py` - New file
- `backend/app/services/pairing_service.py` - Complete rewrite
- `backend/app/services/choice_service.py` - Elo calculations
- `backend/app/services/gallery_service.py` - New file
- `backend/app/api/routes/` - New endpoints
- `backend/app/core/config.py` - Algorithm parameters
- `backend/alembic/versions/` - Migration scripts

### Frontend Changes Required
- `frontend/src/api/` - Updated API types
- `frontend/src/components/` - New convergence UI
- `frontend/src/pages/` - Gallery pages
- `frontend/src/hooks/` - Directory management
- `frontend/src/utils/` - Rating calculations

### Critical Dependencies
- Ensure PostgreSQL version compatibility
- Review FastAPI streaming capabilities
- Frontend state management for convergence data
- Testing framework for statistical algorithms