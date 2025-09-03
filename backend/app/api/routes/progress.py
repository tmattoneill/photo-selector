from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.convergence_service import ConvergenceService


router = APIRouter()


class ComponentProgress(BaseModel):
    progress: float
    label: str
    value: int
    total: Optional[int] = None
    target: Optional[float] = None


class ProgressEstimates(BaseModel):
    comparisons_remaining: int
    portfolio_ready: bool
    quality_indicator: str


class ProgressMilestones(BaseModel):
    next_milestone: Optional[int]
    next_milestone_label: Optional[str]
    current_milestone: int


class ProgressResponse(BaseModel):
    overall_progress: float
    components: Dict[str, ComponentProgress]
    estimates: ProgressEstimates
    milestones: ProgressMilestones


@router.get("/progress", response_model=ProgressResponse)
async def get_portfolio_progress(db: Session = Depends(get_db)):
    """
    Get comprehensive portfolio completion progress.
    
    Returns:
    - Overall progress percentage (0-100)
    - Breakdown by component (coverage, exposure, confidence, stability)  
    - Estimates for remaining comparisons and portfolio readiness
    - Milestone information for user motivation
    
    This replaces the simple "Round X" counter with intelligent progress tracking
    based on the Elo+σ convergence algorithm.
    """
    convergence_service = ConvergenceService(db)
    progress_data = convergence_service.get_portfolio_progress()
    
    return ProgressResponse(
        overall_progress=progress_data['overall_progress'],
        components={
            key: ComponentProgress(**value)
            for key, value in progress_data['components'].items()
        },
        estimates=ProgressEstimates(**progress_data['estimates']),
        milestones=ProgressMilestones(**progress_data['milestones'])
    )


@router.get("/progress/simple")
async def get_simple_progress(db: Session = Depends(get_db)):
    """
    Lightweight progress endpoint for frequent polling.
    
    Returns only the essential progress percentage for header display.
    """
    convergence_service = ConvergenceService(db)
    progress_data = convergence_service.get_portfolio_progress()
    
    return {
        "progress": progress_data['overall_progress'],
        "portfolio_ready": progress_data['estimates']['portfolio_ready'],
        "quality": progress_data['estimates']['quality_indicator']
    }