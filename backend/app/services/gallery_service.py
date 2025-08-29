import os
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..models.image import Image
from .directory_service import DirectoryService
from ..utils.image_utils import get_sha256_hash, is_supported_image, get_image_dimensions, get_mime_type
from ..core.config import settings


class GalleryService:
    """Service for gallery image management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.directory_service = DirectoryService(db)
    
    def get_gallery_images(self, filter: str, limit: int, offset: int) -> Dict[str, Any]:
        """Get images filtered by user preference (liked/skipped)."""
        
        # Get all images from current directory
        image_files = self.directory_service.scan_directory_images()
        if not image_files:
            return {"images": [], "total": 0}
        
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
            return {"images": [], "total": 0}
        
        # Add ordering by preference strength
        if filter == "liked":
            # Order by like ratio (likes - unlikes) descending
            base_stmt = base_stmt.order_by((Image.likes - Image.unlikes).desc())
        else:
            # Order by skip count descending for skipped images
            base_stmt = base_stmt.order_by(Image.skips.desc())
        
        # Execute queries to get image records
        images = list(self.db.execute(base_stmt).scalars().all())
        total = self.db.execute(count_stmt).scalar() or 0
        
        # Create mapping of SHA256 to file paths for images in current directory
        directory_images = {}
        for file_path in image_files:
            try:
                sha256 = get_sha256_hash(file_path)
                directory_images[sha256] = file_path
            except Exception:
                continue
        
        # Filter images to only include those in the current directory
        filtered_images = []
        for image in images:
            if image.sha256 in directory_images:
                # Add file path information for gallery display
                image.file_path = directory_images[image.sha256]
                
                # Add mime type and dimensions if needed
                try:
                    image.mime_type = get_mime_type(image.file_path)
                    width, height = get_image_dimensions(image.file_path)
                    image.width = width
                    image.height = height
                except Exception:
                    image.mime_type = "unknown"
                    image.width = 0
                    image.height = 0
                
                filtered_images.append(image)
        
        # Apply pagination
        paginated_images = filtered_images[offset:offset+limit]
        
        return {
            "images": paginated_images,
            "total": len(filtered_images)
        }