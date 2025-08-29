from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.portfolio_service import PortfolioService

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


@router.post("/portfolio/{portfolio_id}/export", response_model=ExportResponse)
async def export_portfolio(
    portfolio_id: str,
    request: ExportPortfolioRequest,
    db: Session = Depends(get_db)
):
    """Export portfolio images to disk."""
    service = PortfolioService(db)
    
    try:
        result = service.export_portfolio(portfolio_id, request.directory_path)
        
        return ExportResponse(
            success=True,
            exported_count=result["exported_count"],
            export_path=result["export_path"],
            message=f"Successfully exported {result['exported_count']} images to {result['export_path']}"
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )