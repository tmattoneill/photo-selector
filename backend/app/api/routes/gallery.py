from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.gallery_service import GalleryService

router = APIRouter()


class ImageResponse(BaseModel):
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


class GalleryResponse(BaseModel):
    images: List[ImageResponse]
    total: int
    offset: int
    limit: int


@router.get("/gallery", response_model=GalleryResponse)
async def get_gallery_images(
    filter: str = Query("liked", description="Filter images by: liked, skipped"),
    limit: int = Query(20, ge=1, le=100, description="Number of images to return"),
    offset: int = Query(0, ge=0, description="Number of images to skip"),
    db: Session = Depends(get_db)
):
    """Get gallery images filtered by user preference."""
    service = GalleryService(db)
    result = service.get_gallery_images(filter, limit, offset)
    
    images = [
        ImageResponse(
            image_id=img.sha256,  # Use SHA256 as ID
            sha256=img.sha256,
            file_path=getattr(img, 'file_path', ''),  # May not be available
            mime_type=getattr(img, 'mime_type', 'unknown'),
            likes=img.likes,
            unlikes=img.unlikes,
            skips=img.skips,
            exposures=img.exposures,
            base64_data=f"/api/image/{img.sha256}",  # SHA256-based serving
            created_at=img.created_at.isoformat()
        ) for img in result["images"]
    ]
    
    return GalleryResponse(
        images=images,
        total=result["total"],
        offset=offset,
        limit=limit
    )