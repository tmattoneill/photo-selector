import os
import shutil
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models.portfolio import Portfolio
from ..models.image import Image
from ..models.user import User
from .choice_service import ChoiceService
from .directory_service import DirectoryService


class PortfolioService:
    """Service for portfolio management and export."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_portfolio(self, name: str, description: Optional[str], image_ids: List[str]) -> Portfolio:
        """Create a new portfolio with specified images (SHA256 hashes)."""
        
        # Get default user
        choice_service = ChoiceService(self.db)
        user_id = choice_service.ensure_default_user()
        
        # Validate that image_ids are SHA256 hashes (should be strings, not UUIDs)
        for image_id in image_ids:
            if not isinstance(image_id, str) or len(image_id) != 64:
                raise ValueError(f"Invalid image ID format (expected SHA256): {image_id}")
        
        # Check that all images exist (by SHA256)
        stmt = select(Image).where(Image.sha256.in_(image_ids))
        existing_images = list(self.db.execute(stmt).scalars().all())
        
        if len(existing_images) != len(image_ids):
            found_sha256s = {img.sha256 for img in existing_images}
            missing = set(image_ids) - found_sha256s
            raise ValueError(f"Some images were not found: {missing}")
        
        # Create portfolio
        portfolio = Portfolio(
            name=name,
            description=description,
            user_id=UUID(user_id),
            images=existing_images
        )
        
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        
        return portfolio
    
    def get_portfolio(self, portfolio_id: str) -> Optional[Portfolio]:
        """Get a portfolio by ID."""
        try:
            portfolio_uuid = UUID(portfolio_id)
        except ValueError:
            return None
        
        stmt = select(Portfolio).where(Portfolio.id == portfolio_uuid)
        return self.db.execute(stmt).scalar_one_or_none()
    
    def export_portfolio(self, portfolio_id: str, directory_path: str) -> Dict[str, Any]:
        """Export portfolio images to the specified directory."""
        
        # Get portfolio with images loaded
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            raise FileNotFoundError(f"Portfolio {portfolio_id} not found")
        
        # Create export directory
        portfolio_name_clean = portfolio.name.replace(" ", "_").replace("/", "_")
        full_export_path = os.path.join(directory_path, f"portfolio_{portfolio_name_clean}")
        os.makedirs(full_export_path, exist_ok=True)
        
        # Get directory service to find image files
        directory_service = DirectoryService(self.db)
        
        # Ensure directory is set
        if len(directory_service.get_all_sha256s()) == 0:
            directory_service.set_root_directory("/samples")
        
        exported_count = 0
        
        # Export each image by copying from filesystem
        for image in portfolio.images:
            try:
                # Find source file path using SHA256
                source_path = directory_service.get_path_by_sha256(image.sha256)
                
                if source_path and os.path.exists(source_path):
                    # Get file extension
                    _, ext = os.path.splitext(source_path)
                    
                    # Create destination filename (SHA256 + original extension)
                    dest_filename = f"{image.sha256}{ext}"
                    dest_path = os.path.join(full_export_path, dest_filename)
                    
                    # Copy file
                    shutil.copy2(source_path, dest_path)
                    exported_count += 1
                else:
                    print(f"Warning: Could not find file for image {image.sha256}")
                
            except Exception as e:
                # Log error but continue with other images
                print(f"Failed to export image {image.sha256}: {str(e)}")
                continue
        
        return {
            "exported_count": exported_count,
            "export_path": full_export_path
        }