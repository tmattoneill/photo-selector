from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.pairing_service import PairingService
from ...services.choice_service import ChoiceService

router = APIRouter()


class ChoiceRequest(BaseModel):
    round: int
    left_id: str
    right_id: str
    selection: str  # "LEFT", "RIGHT", or "SKIP"


class ChoiceResponse(BaseModel):
    saved: bool
    next_round: int


@router.post("/choice", response_model=ChoiceResponse)
async def record_choice(
    request: ChoiceRequest,
    db: Session = Depends(get_db)
):
    """Record user choice between two images."""
    try:
        # Validate selection
        if request.selection not in ["LEFT", "RIGHT", "SKIP"]:
            raise HTTPException(
                status_code=400, 
                detail="Selection must be 'LEFT', 'RIGHT', or 'SKIP'"
            )
        
        # Ensure default user exists
        choice_service = ChoiceService(db)
        user_id = choice_service.ensure_default_user()
        
        # Record the choice
        pairing_service = PairingService(db)
        next_round = pairing_service.record_choice(
            left_id=request.left_id,
            right_id=request.right_id,
            selection=request.selection,
            user_id=user_id,
            round_num=request.round
        )
        
        return ChoiceResponse(saved=True, next_round=next_round)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record choice: {str(e)}")