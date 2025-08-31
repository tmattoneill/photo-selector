from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.convergence_service import ConvergenceService


router = APIRouter()


class ImageRanking(BaseModel):
    sha256: str
    mu: float
    sigma: float
    exposures: int
    rank: int
    ci_lower: float
    ci_upper: float


class CoverageInfo(BaseModel):
    unseen_count: int
    seen_count: int
    total_count: int
    coverage_pct: float
    coverage_complete: bool


class BoundaryAnalysis(BaseModel):
    boundary_gap: float
    boundary_sigmas: List[float]
    max_boundary_sigma: float
    k_image: Optional[Dict[str, Any]]
    k_plus_1_image: Optional[Dict[str, Any]]


class StabilityAnalysis(BaseModel):
    window_start: int
    window_end: int
    window_size: int
    top_k_swaps_in_window: int
    stability_attained: bool


class ProgressMeter(BaseModel):
    name: str
    value: float
    target: float
    progress: float


class UISignals(BaseModel):
    meters: List[ProgressMeter]


class ConvergencePredicates(BaseModel):
    coverage_complete: bool
    exposures_floor_met: bool
    confidence_separation: bool
    stability_attained: bool


class AutoFinishDecision(BaseModel):
    should_auto_finish: bool
    reason: str


class TopKData(BaseModel):
    k: int
    median_mu: float
    top_k_sha256s: List[str]
    top_k_images: List[Dict[str, Any]]


class StateResponse(BaseModel):
    current_round: int
    coverage: CoverageInfo
    top_k: TopKData
    stability: StabilityAnalysis
    boundary: BoundaryAnalysis
    predicates: ConvergencePredicates
    auto_finish: AutoFinishDecision
    ui_signals: UISignals


@router.get("/state", response_model=StateResponse)
async def get_convergence_state(db: Session = Depends(get_db)):
    """
    Get comprehensive convergence state and progress metrics per algo-update.yaml spec.
    
    Returns current convergence status including:
    - Coverage metrics (seen/unseen image counts)
    - Top-K stability tracking over 120-round windows
    - Confidence interval boundary analysis
    - Auto-finish predicates and decision logic
    - UI progress meters for user feedback
    """
    convergence_service = ConvergenceService(db)
    state = convergence_service.get_convergence_state()
    
    return StateResponse(
        current_round=state['current_round'],
        coverage=CoverageInfo(**state['coverage']),
        top_k=TopKData(**state['top_k']),
        stability=StabilityAnalysis(**state['stability']),
        boundary=BoundaryAnalysis(**state['boundary']),
        predicates=ConvergencePredicates(**state['predicates']),
        auto_finish=AutoFinishDecision(**state['auto_finish']),
        ui_signals=UISignals(**state['ui_signals'])
    )