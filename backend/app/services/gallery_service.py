from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..models.image import Image


class GalleryService:
    """Service for gallery image management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_gallery_images(self, filter: str, limit: int, offset: int) -> Dict[str, Any]:
        """Get images filtered by user preference (liked/skipped)."""
        
        # Build base query for canonical images only
        base_stmt = select(Image).where(Image.is_canonical == True)
        count_stmt = select(func.count(Image.id)).where(Image.is_canonical == True)
        
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
        
        # Apply pagination
        base_stmt = base_stmt.limit(limit).offset(offset)
        
        # Execute queries
        images = list(self.db.execute(base_stmt).scalars().all())
        total = self.db.execute(count_stmt).scalar() or 0
        
        return {
            "images": images,
            "total": total
        }