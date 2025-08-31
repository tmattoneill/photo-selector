from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.directory_service import DirectoryService
from ...services.pairing_service import PairingService

router = APIRouter()


class ImageData(BaseModel):
    sha256: str
    base64: str  # Will contain the image serving URL
    w: int
    h: int


class PairResponse(BaseModel):
    round: int
    left: Optional[ImageData]
    right: Optional[ImageData]


@router.get("/pair", response_model=PairResponse)
async def get_image_pair(db: Session = Depends(get_db)):
    """Get a pair of images for comparison using Elo+σ pairing algorithm."""
    try:
        directory_service = DirectoryService(db)
        
        # If cache is empty but we have images in database, try to rescan with samples
        if len(directory_service.get_all_sha256s()) == 0:
            # Try to rescan the samples directory (fallback directory)
            try:
                directory_service.set_root_directory("/samples")
            except Exception as scan_error:
                raise HTTPException(
                    status_code=503, 
                    detail=f"No directory set. Please POST to /api/directory first to set a directory. Scan error: {scan_error}"
                )
        
        pairing_service = PairingService(db)
        
        left_data, right_data, current_round = pairing_service.get_next_pair(directory_service)
        
        if not left_data or not right_data:
            raise HTTPException(
                status_code=404, 
                detail="Not enough images available for pairing. Please set a directory with at least 2 images."
            )
        
        def format_image(image_data: dict) -> ImageData:
            return ImageData(
                sha256=image_data["sha256"],
                base64=f"/api/image/{image_data['sha256']}",  # SHA256-based serving
                w=image_data.get("width", 1),  # Default dimensions if not available
                h=image_data.get("height", 1)
            )
        
        return PairResponse(
            round=current_round,
            left=format_image(left_data),
            right=format_image(right_data)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get image pair: {str(e)}")