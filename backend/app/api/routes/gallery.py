from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.gallery_service import GalleryService

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