import os
from typing import Dict, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models.image import Image


class DirectoryService:
    """Directory service for uploaded images in /app/uploads directory."""
    
    def __init__(self, db: Session):
        self.db = db
        self.root_directory = "/app/uploads"
        self.supported_extensions = [".jpg", ".jpeg", ".png", ".webp", ".gif"]
        # Ensure upload directory exists
        os.makedirs(self.root_directory, exist_ok=True)
    
    def get_path_by_sha256(self, sha256: str) -> Optional[str]:
        """Get file path by SHA256, checking database first then filesystem."""
        # First check database for exact file_path
        stmt = select(Image.file_path).where(Image.sha256 == sha256)
        result = self.db.execute(stmt).scalar_one_or_none()
        
        if result and os.path.exists(result):
            return result
        
        # Fallback: Try different extensions to find the file (both lowercase and uppercase)
        for ext in self.supported_extensions:
            # Try lowercase extension
            file_path = os.path.join(self.root_directory, f"{sha256}{ext}")
            if os.path.exists(file_path):
                return file_path
            
            # Try uppercase extension
            file_path = os.path.join(self.root_directory, f"{sha256}{ext.upper()}")
            if os.path.exists(file_path):
                return file_path
        return None
    
    def get_all_sha256s(self) -> Set[str]:
        """Get all SHA256s from database (uploaded images)."""
        from sqlalchemy import select
        stmt = select(Image.sha256)
        result = self.db.execute(stmt)
        return {row[0] for row in result}
    
    def get_cache_info(self) -> Dict[str, any]:
        """Get information about uploaded images."""
        all_sha256s = self.get_all_sha256s()
        return {
            "root_directory": self.root_directory,
            "total_images": len(all_sha256s),
            "cache_entries": len(all_sha256s)
        }