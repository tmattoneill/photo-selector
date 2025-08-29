from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.directory_service import DirectoryService

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
    """Get a pair of images for comparison from current directory."""
    try:
        service = DirectoryService(db)
        left_data, right_data, current_round = service.get_image_pair_from_directory()
        
        if not left_data or not right_data:
            raise HTTPException(
                status_code=404, 
                detail="Not enough images available for pairing. Please set a directory with at least 2 images."
            )
        
        def format_image(image_data: dict) -> ImageData:
            return ImageData(
                sha256=image_data["sha256"],
                base64=f"/api/image/{image_data['sha256']}",  # SHA256-based serving
                w=image_data["width"],
                h=image_data["height"]
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