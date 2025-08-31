import os
import shutil
from datetime import datetime
from typing import List, Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.directory_service import DirectoryService

router = APIRouter()


class CreatePortfolioRequest(BaseModel):
    name: str
    description: Optional[str] = None
    image_ids: List[str]


class ExportPortfolioRequest(BaseModel):
    directory_path: str


class PortfolioResponse(BaseModel):
    portfolio_id: str
    name: str
    description: Optional[str]
    image_count: int
    created_at: str


class ExportResponse(BaseModel):
    success: bool
    exported_count: int
    export_path: str
    message: str


# Simple in-memory storage for portfolios (temporary solution)
_portfolios = {}


@router.post("/portfolio", response_model=PortfolioResponse)
async def create_portfolio(
    request: CreatePortfolioRequest,
    db: Session = Depends(get_db)
):
    """Create a new portfolio with selected images."""
    try:
        # Generate unique portfolio ID
        portfolio_id = str(uuid4())
        
        # Store portfolio data
        portfolio_data = {
            "portfolio_id": portfolio_id,
            "name": request.name,
            "description": request.description,
            "image_ids": request.image_ids,
            "image_count": len(request.image_ids),
            "created_at": datetime.now().isoformat()
        }
        
        _portfolios[portfolio_id] = portfolio_data
        
        return PortfolioResponse(**portfolio_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create portfolio: {str(e)}"
        )


@router.get("/portfolio/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: str,
    db: Session = Depends(get_db)
):
    """Get portfolio details."""
    if portfolio_id not in _portfolios:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    return PortfolioResponse(**_portfolios[portfolio_id])


@router.post("/portfolio/{portfolio_id}/export", response_model=ExportResponse)
async def export_portfolio(
    portfolio_id: str,
    request: ExportPortfolioRequest,
    db: Session = Depends(get_db)
):
    """Export portfolio images to disk."""
    try:
        # Check if portfolio exists
        if portfolio_id not in _portfolios:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        portfolio = _portfolios[portfolio_id]
        
        # Create export directory
        portfolio_name = portfolio["name"].replace(" ", "_").replace("/", "_")
        export_dir = os.path.join(request.directory_path, f"portfolio_{portfolio_name}")
        
        # Create directory if it doesn't exist
        os.makedirs(export_dir, exist_ok=True)
        
        # Get directory service to find image files
        directory_service = DirectoryService(db)
        
        # Ensure directory is set
        if len(directory_service.get_all_sha256s()) == 0:
            directory_service.set_root_directory("/samples")
        
        exported_count = 0
        
        # Copy each image to export directory
        for image_id in portfolio["image_ids"]:
            try:
                # Find source file path (image_id is SHA256)
                source_path = directory_service.get_path_by_sha256(image_id)
                
                if source_path and os.path.exists(source_path):
                    # Get file extension
                    _, ext = os.path.splitext(source_path)
                    
                    # Create destination filename
                    dest_filename = f"{image_id}{ext}"
                    dest_path = os.path.join(export_dir, dest_filename)
                    
                    # Copy file
                    shutil.copy2(source_path, dest_path)
                    exported_count += 1
                    
            except Exception as e:
                # Log error but continue with other images
                print(f"Failed to export image {image_id}: {e}")
                continue
        
        return ExportResponse(
            success=True,
            exported_count=exported_count,
            export_path=export_dir,
            message=f"Successfully exported {exported_count} images to {export_dir}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )