from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.pairing_service import PairingService

router = APIRouter()


class ImageData(BaseModel):
    image_id: str
    sha256: str
    base64: str
    w: int
    h: int


class PairResponse(BaseModel):
    round: int
    left: Optional[ImageData]
    right: Optional[ImageData]


@router.get("/pair", response_model=PairResponse)
async def get_image_pair(db: Session = Depends(get_db)):
    """Get a pair of images for comparison."""
    try:
        service = PairingService(db)
        left_image, right_image, current_round = service.get_image_pair()
        
        if not left_image or not right_image:
            raise HTTPException(
                status_code=404, 
                detail="Not enough images available for pairing"
            )
        
        def format_image(image) -> ImageData:
            return ImageData(
                image_id=str(image.id),
                sha256=image.sha256,
                base64=image.base64_data.decode('utf-8'),
                w=image.width,
                h=image.height
            )
        
        return PairResponse(
            round=current_round,
            left=format_image(left_image),
            right=format_image(right_image)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get image pair: {str(e)}")