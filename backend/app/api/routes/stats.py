from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.choice_service import ChoiceService

router = APIRouter()


class ImageStats(BaseModel):
    image_id: str
    sha256: str
    file_path: str
    likes: int
    unlikes: int
    skips: int
    exposures: int


class StatsResponse(BaseModel):
    images: int
    duplicates: int
    rounds: int
    by_image: List[ImageStats]


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """Get application statistics."""
    service = ChoiceService(db)
    stats_data = service.get_stats()
    
    # Convert by_image data to Pydantic models
    by_image_stats = [
        ImageStats(**image_data) for image_data in stats_data["by_image"]
    ]
    
    return StatsResponse(
        images=stats_data["images"],
        duplicates=stats_data["duplicates"],
        rounds=stats_data["rounds"],
        by_image=by_image_stats
    )