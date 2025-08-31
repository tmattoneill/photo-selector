from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.pairing_service import PairingService

router = APIRouter()


class ChoiceRequest(BaseModel):
    round: int
    left_sha256: str
    right_sha256: str
    selection: str  # "LEFT", "RIGHT", or "SKIP"


class ChoiceResponse(BaseModel):
    saved: bool
    next_round: int


@router.post("/choice", response_model=ChoiceResponse)
async def record_choice(
    request: ChoiceRequest,
    db: Session = Depends(get_db)
):
    """Record user choice between two images identified by SHA256 using Elo+σ algorithm."""
    try:
        # Validate selection
        if request.selection not in ["LEFT", "RIGHT", "SKIP"]:
            raise HTTPException(
                status_code=400, 
                detail="Selection must be 'LEFT', 'RIGHT', or 'SKIP'"
            )
        
        # Record the choice using PairingService per algo-update.yaml spec
        pairing_service = PairingService(db)
        
        result = pairing_service.record_choice(
            round_num=request.round,
            left_sha256=request.left_sha256,
            right_sha256=request.right_sha256,
            outcome=request.selection
        )
        
        # Return success with incremented round
        return ChoiceResponse(saved=True, next_round=request.round + 1)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record choice: {str(e)}")