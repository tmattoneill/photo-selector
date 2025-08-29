from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..models.image import Image
from ..models.choice import Choice
from ..models.user import User


class ChoiceService:
    """Service for choice and statistics management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        # Count all images (no duplicates in new model - SHA256 is unique)
        images_stmt = select(func.count(Image.sha256))
        images_count = self.db.execute(images_stmt).scalar()
        
        # Count total rounds (choices) 
        rounds_stmt = select(func.count(Choice.id))
        rounds_count = self.db.execute(rounds_stmt).scalar()
        
        # Per-image statistics
        images_stmt = select(Image)
        images = list(self.db.execute(images_stmt).scalars().all())
        
        by_image = []
        for image in images:
            by_image.append({
                "sha256": image.sha256,
                "likes": image.likes,
                "unlikes": image.unlikes,
                "skips": image.skips,
                "exposures": image.exposures
            })
        
        return {
            "images": images_count or 0,
            "duplicates": 0,  # No duplicates in new architecture
            "rounds": rounds_count or 0,
            "by_image": by_image
        }
    
    def ensure_default_user(self) -> str:
        """Ensure a default user exists and return their ID."""
        stmt = select(User).limit(1)
        user = self.db.execute(stmt).scalar_one_or_none()
        
        if not user:
            user = User()
            self.db.add(user)
            self.db.commit()
        
        return str(user.id)