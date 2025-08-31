from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.choice_service import ChoiceService
from ...services.directory_service import DirectoryService
from ...utils.image_utils import get_sha256_hash

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
    directory_service = DirectoryService(db)
    stats_data = service.get_stats()
    
    # Get all images from current directory cache
    if len(directory_service.get_all_sha256s()) == 0:
        directory_service.set_root_directory("/samples")
    
    # Get paths from cache
    all_sha256s = directory_service.get_all_sha256s()
    image_paths = {sha256: directory_service.get_path_by_sha256(sha256) 
                   for sha256 in all_sha256s}
    
    # Use the image_paths mapping we created above
    directory_images = {sha256: path for sha256, path in image_paths.items() if path}
    
    # Convert by_image data to Pydantic models with file paths
    by_image_stats = []
    for image_data in stats_data["by_image"]:
        sha256 = image_data["sha256"]
        file_path = directory_images.get(sha256, "")
        
        # Only include images that exist in current directory
        if file_path:
            by_image_stats.append(
                ImageStats(
                    image_id=sha256,  # Use SHA256 as image_id
                    sha256=sha256,
                    file_path=file_path,
                    likes=image_data["likes"],
                    unlikes=image_data["unlikes"],
                    skips=image_data["skips"],
                    exposures=image_data["exposures"]
                )
            )
    
    return StatsResponse(
        images=stats_data["images"],
        duplicates=stats_data["duplicates"],
        rounds=stats_data["rounds"],
        by_image=by_image_stats
    )