from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.gallery_service import GalleryService
from ...services.directory_service import DirectoryService
from ...models.image import Image
from ...utils.image_utils import get_sha256_hash
from sqlalchemy import select, func

router = APIRouter()


# Request Models
class CreateGalleryRequest(BaseModel):
    name: str = Field(..., description="Gallery name")
    selection_policy: str = Field(..., description="Selection policy: top_k, threshold_mu, threshold_ci, manual")
    selection_params: Dict[str, Any] = Field(..., description="Policy parameters")
    duplicates_policy: str = Field("collapse_to_canonical", description="Duplicates handling policy")


class UpdateGalleryRequest(BaseModel):
    name: Optional[str] = None
    remove_sha256: Optional[str] = None
    add_sha256: Optional[str] = None
    re_rank: Optional[bool] = False


# Response Models
class ImageRanking(BaseModel):
    sha256: str
    mu: float
    sigma: float
    exposures: int
    rank: int


class GallerySummary(BaseModel):
    gallery_id: int
    name: str
    size: int
    created_at: datetime


class CreateGalleryResponse(BaseModel):
    gallery_id: int
    name: str
    size: int
    created_at: datetime
    sample: List[ImageRanking]


class GalleryDetail(BaseModel):
    gallery_id: int
    name: str
    size: int
    created_at: datetime
    images: List[ImageRanking]


@router.post("/galleries", response_model=CreateGalleryResponse)
async def create_gallery(
    request: CreateGalleryRequest,
    db: Session = Depends(get_db)
):
    """Create a new gallery with specified selection policy."""
    service = GalleryService(db)
    
    try:
        result = service.create_gallery(
            name=request.name,
            selection_policy=request.selection_policy,
            selection_params=request.selection_params,
            duplicates_policy=request.duplicates_policy
        )
        return CreateGalleryResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create gallery: {str(e)}")


@router.get("/galleries", response_model=List[GallerySummary])
async def list_galleries(db: Session = Depends(get_db)):
    """List all galleries with summary information."""
    service = GalleryService(db)
    galleries = service.list_galleries()
    return [GallerySummary(**gallery) for gallery in galleries]


@router.get("/galleries/{gallery_id}", response_model=GalleryDetail)
async def get_gallery(
    gallery_id: int = Path(..., description="Gallery ID"),
    db: Session = Depends(get_db)
):
    """Get gallery details with all images."""
    service = GalleryService(db)
    gallery = service.get_gallery(gallery_id)
    
    if not gallery:
        raise HTTPException(status_code=404, detail="Gallery not found")
    
    return GalleryDetail(**gallery)


@router.patch("/galleries/{gallery_id}")
async def update_gallery(
    gallery_id: int = Path(..., description="Gallery ID"),
    request: UpdateGalleryRequest = ...,
    db: Session = Depends(get_db)
):
    """Update gallery (rename, add/remove images, re-rank)."""
    service = GalleryService(db)
    
    success = service.update_gallery(
        gallery_id=gallery_id,
        name=request.name,
        remove_sha256=request.remove_sha256,
        add_sha256=request.add_sha256,
        re_rank=request.re_rank or False
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Gallery not found")
    
    return {"ok": True}


@router.delete("/galleries/{gallery_id}")
async def delete_gallery(
    gallery_id: int = Path(..., description="Gallery ID"),
    db: Session = Depends(get_db)
):
    """Delete gallery and all its images."""
    service = GalleryService(db)
    
    success = service.delete_gallery(gallery_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Gallery not found")
    
    return {"ok": True}

# Legacy compatibility endpoint for old frontend
class LegacyImageResponse(BaseModel):
    image_id: str
    sha256: str
    file_path: str
    mime_type: str
    likes: int
    unlikes: int
    skips: int
    exposures: int
    base64_data: str
    created_at: str


class LegacyGalleryResponse(BaseModel):
    images: List[LegacyImageResponse]
    total: int
    offset: int
    limit: int


@router.get("/gallery", response_model=LegacyGalleryResponse)
async def get_legacy_gallery_images(
    filter: str = Query("liked", description="Filter images by: liked, skipped"),
    limit: int = Query(20, ge=1, le=100, description="Number of images to return"),
    offset: int = Query(0, ge=0, description="Number of images to skip"),
    db: Session = Depends(get_db)
):
    """Legacy gallery endpoint for liked/skipped images (compatibility)."""
    
    directory_service = DirectoryService(db)
    
    # Get uploaded images
    
    # Get paths from cache
    all_sha256s = directory_service.get_all_sha256s()
    image_paths = {sha256: directory_service.get_path_by_sha256(sha256) 
                   for sha256 in all_sha256s}
    
    # Build base query - get all images that have stats
    base_stmt = select(Image)
    count_stmt = select(func.count(Image.sha256))
    
    # Apply filters
    if filter == "liked":
        # Images with more likes than unlikes
        base_stmt = base_stmt.where(Image.likes > Image.unlikes)
        count_stmt = count_stmt.where(Image.likes > Image.unlikes)
    elif filter == "skipped":
        # Images that have been skipped at least once
        base_stmt = base_stmt.where(Image.skips > 0)
        count_stmt = count_stmt.where(Image.skips > 0)
    else:
        # Invalid filter, return empty
        return LegacyGalleryResponse(images=[], total=0, offset=offset, limit=limit)
    
    # Add ordering by preference strength
    if filter == "liked":
        # Order by like ratio (likes - unlikes) descending
        base_stmt = base_stmt.order_by((Image.likes - Image.unlikes).desc())
    else:
        # Order by skip count descending for skipped images
        base_stmt = base_stmt.order_by(Image.skips.desc())
    
    # Apply pagination
    base_stmt = base_stmt.offset(offset).limit(limit)
    
    # Execute queries to get image records
    images = list(db.execute(base_stmt).scalars().all())
    total = db.execute(count_stmt).scalar() or 0
    
    # Filter images to only include those in the current directory
    filtered_images = []
    for image in images:
        file_path = image_paths.get(image.sha256)
        if file_path:
            filtered_images.append(
                LegacyImageResponse(
                    image_id=image.sha256,  # Use SHA256 as ID
                    sha256=image.sha256,
                    file_path=file_path,
                    mime_type="image/jpeg",  # Default fallback
                    likes=image.likes,
                    unlikes=image.unlikes,
                    skips=image.skips,
                    exposures=image.exposures,
                    base64_data=f"/api/image/{image.sha256}",  # SHA256-based serving
                    created_at=datetime.now().isoformat()  # Use current time as fallback
                )
            )
    
    return LegacyGalleryResponse(
        images=filtered_images,
        total=len(filtered_images),
        offset=offset,
        limit=limit
    )
