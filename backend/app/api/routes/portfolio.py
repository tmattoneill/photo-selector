from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.portfolio_service import PortfolioService

router = APIRouter()


class CreatePortfolioRequest(BaseModel):
    name: str
    description: Optional[str] = None
    image_ids: List[str]


class PortfolioResponse(BaseModel):
    portfolio_id: str
    name: str
    description: Optional[str]
    image_count: int
    created_at: str


@router.post("/portfolio", response_model=PortfolioResponse)
async def create_portfolio(
    request: CreatePortfolioRequest,
    db: Session = Depends(get_db)
):
    """Create a new portfolio with selected images."""
    service = PortfolioService(db)
    
    try:
        portfolio = service.create_portfolio(
            name=request.name,
            description=request.description,
            image_ids=request.image_ids
        )
        
        return PortfolioResponse(
            portfolio_id=str(portfolio.id),
            name=portfolio.name,
            description=portfolio.description,
            image_count=len(portfolio.images),
            created_at=portfolio.created_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
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
    service = PortfolioService(db)
    
    portfolio = service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    return PortfolioResponse(
        portfolio_id=str(portfolio.id),
        name=portfolio.name,
        description=portfolio.description,
        image_count=len(portfolio.images),
        created_at=portfolio.created_at.isoformat()
    )


@router.get("/portfolio/{portfolio_id}/download")
async def download_portfolio(
    portfolio_id: str,
    db: Session = Depends(get_db)
):
    """Download portfolio as a zip file."""
    service = PortfolioService(db)
    
    try:
        zip_buffer, zip_filename, exported_count = service.export_portfolio_to_zip(portfolio_id)
        
        if exported_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No images found to export"
            )
        
        # Return the zip file as a streaming response
        return StreamingResponse(
            iter([zip_buffer.read()]),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}",
                "Content-Length": str(len(zip_buffer.getvalue()))
            }
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        )

# Export endpoint removed - use /download instead to get zip files