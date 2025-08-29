import os
from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models.image import Image
from ..utils.image_utils import (
    get_sha256_hash,
    get_image_dimensions, 
    get_mime_type,
    encode_image_to_base64,
    is_supported_image,
    get_file_size
)
from ..core.config import settings


class ImageService:
    """Service for image ingestion and management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def ingest_directory(self, directory: str) -> Tuple[int, int, int]:
        """
        Ingest all supported images from a directory recursively.
        
        Returns:
            Tuple[ingested, duplicates, existing]: Counts of processed images
        """
        if not os.path.exists(directory):
            raise ValueError(f"Directory does not exist: {directory}")
        
        # Security check - ensure directory is within allowed path
        abs_directory = os.path.abspath(directory)
        allowed_root = os.path.abspath(settings.image_root)
        if not abs_directory.startswith(allowed_root):
            raise ValueError("Directory path not allowed")
        
        image_files = self._scan_directory(abs_directory)
        
        ingested = 0
        duplicates = 0
        existing = 0
        
        for file_path in image_files:
            result = self._process_image_file(file_path)
            if result == "ingested":
                ingested += 1
            elif result == "duplicate":
                duplicates += 1
            elif result == "existing":
                existing += 1
        
        self.db.commit()
        return ingested, duplicates, existing
    
    def _scan_directory(self, directory: str) -> List[str]:
        """Recursively scan directory for supported image files."""
        image_files = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if is_supported_image(file_path, settings.supported_formats):
                    # Check file size limit
                    file_size = get_file_size(file_path)
                    max_size = settings.max_image_mb * 1024 * 1024
                    if file_size <= max_size:
                        image_files.append(file_path)
        
        return image_files
    
    def _process_image_file(self, file_path: str) -> str:
        """
        Process a single image file.
        
        Returns:
            str: "ingested", "duplicate", or "existing"
        """
        try:
            # Generate hash
            sha256_hash = get_sha256_hash(file_path)
            
            # Check if image already exists
            stmt = select(Image).where(Image.sha256 == sha256_hash)
            existing_image = self.db.execute(stmt).scalar_one_or_none()
            
            if existing_image:
                if existing_image.is_canonical:
                    # Hash exists as canonical, check if this specific file path exists
                    stmt = select(Image).where(
                        Image.sha256 == sha256_hash,
                        Image.file_path == file_path
                    )
                    if self.db.execute(stmt).scalar_one_or_none():
                        return "existing"
                    else:
                        # Create duplicate entry
                        self._create_duplicate_image(file_path, existing_image)
                        return "duplicate"
                else:
                    # Existing image is a duplicate, check if this path exists
                    stmt = select(Image).where(
                        Image.sha256 == sha256_hash,
                        Image.file_path == file_path
                    )
                    if self.db.execute(stmt).scalar_one_or_none():
                        return "existing"
                    else:
                        # Get canonical image
                        canonical = existing_image.canonical or existing_image
                        self._create_duplicate_image(file_path, canonical)
                        return "duplicate"
            else:
                # Create new canonical image
                self._create_canonical_image(file_path, sha256_hash)
                return "ingested"
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return "error"
    
    def _create_canonical_image(self, file_path: str, sha256_hash: str):
        """Create a new canonical image record."""
        width, height = get_image_dimensions(file_path)
        mime_type = get_mime_type(file_path)
        file_size = get_file_size(file_path)
        base64_data = encode_image_to_base64(file_path)
        
        image = Image(
            sha256=sha256_hash,
            file_path=file_path,
            mime_type=mime_type,
            width=width,
            height=height,
            file_size=file_size,
            base64_data=base64_data.encode('utf-8'),
            is_canonical=True,
            canonical_id=None
        )
        
        self.db.add(image)
    
    def _create_duplicate_image(self, file_path: str, canonical_image: Image):
        """Create a duplicate image record pointing to canonical."""
        mime_type = get_mime_type(file_path)
        file_size = get_file_size(file_path)
        
        duplicate = Image(
            sha256=canonical_image.sha256,
            file_path=file_path,
            mime_type=mime_type,
            width=canonical_image.width,
            height=canonical_image.height,
            file_size=file_size,
            base64_data=canonical_image.base64_data,  # Reference same data
            is_canonical=False,
            canonical_id=canonical_image.id
        )
        
        self.db.add(duplicate)
    
    def get_canonical_images(self) -> List[Image]:
        """Get all canonical images."""
        stmt = select(Image).where(Image.is_canonical == True)
        return list(self.db.execute(stmt).scalars().all())
    
    def get_duplicate_count(self) -> int:
        """Get count of duplicate images."""
        stmt = select(Image).where(Image.is_canonical == False)
        return len(list(self.db.execute(stmt).scalars().all()))