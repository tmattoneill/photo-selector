from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.directory_service import DirectoryService
from ...services.pairing_service import PairingService
from ...utils.image_utils import get_image_dimensions

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
        
        # Check if there are any uploaded images
        if len(directory_service.get_all_sha256s()) == 0:
            raise HTTPException(
                status_code=404,
                detail="No images found. Please upload images using the folder picker in the UI."
            )
        
        pairing_service = PairingService(db)
        
        left_data, right_data, current_round = pairing_service.get_next_pair(directory_service)
        
        if not left_data or not right_data:
            raise HTTPException(
                status_code=404, 
                detail="Not enough images available for pairing. Please upload at least 2 images using the folder picker."
            )
        
        def format_image(image_data: dict) -> ImageData:
            # Get actual image dimensions from file
            width, height = 1, 1  # Default fallback
            try:
                file_path = directory_service.get_path_by_sha256(image_data["sha256"])
                if file_path:
                    width, height = get_image_dimensions(file_path)
                    if width == 0 and height == 0:
                        # Fall back to 1x1 if dimensions couldn't be read
                        width, height = 1, 1
            except Exception as e:
                # Debug: you could log the exception here
                pass
            
            return ImageData(
                sha256=image_data["sha256"],
                base64=f"/api/image/{image_data['sha256']}",  # SHA256-based serving
                w=width,
                h=height
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