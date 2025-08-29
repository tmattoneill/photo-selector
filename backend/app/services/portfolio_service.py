import os
import base64
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models.portfolio import Portfolio
from ..models.image import Image
from ..models.user import User
from .choice_service import ChoiceService


class PortfolioService:
    """Service for portfolio management and export."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_portfolio(self, name: str, description: Optional[str], image_ids: List[str]) -> Portfolio:
        """Create a new portfolio with specified images."""
        
        # Get default user
        choice_service = ChoiceService(self.db)
        user_id = choice_service.ensure_default_user()
        
        # Validate image IDs exist and are canonical
        image_uuids = []
        for image_id in image_ids:
            try:
                image_uuids.append(UUID(image_id))
            except ValueError:
                raise ValueError(f"Invalid image ID format: {image_id}")
        
        # Check that all images exist and are canonical
        stmt = select(Image).where(
            Image.id.in_(image_uuids),
            Image.is_canonical == True
        )
        existing_images = list(self.db.execute(stmt).scalars().all())
        
        if len(existing_images) != len(image_ids):
            raise ValueError("Some images were not found or are not canonical")
        
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
        
        # Get portfolio
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            raise FileNotFoundError(f"Portfolio {portfolio_id} not found")
        
        # Create export directory
        full_export_path = os.path.join(directory_path, f"portfolio_{portfolio.name}")
        os.makedirs(full_export_path, exist_ok=True)
        
        exported_count = 0
        
        # Export each image
        for image in portfolio.images:
            try:
                # Decode base64 data
                image_data = base64.b64decode(image.base64_data)
                
                # Generate filename from original path
                original_filename = os.path.basename(image.file_path)
                export_filename = f"{image.sha256[:8]}_{original_filename}"
                export_file_path = os.path.join(full_export_path, export_filename)
                
                # Write image file
                with open(export_file_path, 'wb') as f:
                    f.write(image_data)
                
                exported_count += 1
                
            except Exception as e:
                # Log error but continue with other images
                print(f"Failed to export image {image.id}: {str(e)}")
                continue
        
        return {
            "exported_count": exported_count,
            "export_path": full_export_path
        }