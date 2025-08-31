from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ...core.database import get_db

router = APIRouter()


class ResetResponse(BaseModel):
    success: bool
    message: str
    reset_items: list[str]


@router.post("/reset", response_model=ResetResponse)
async def reset_gallery_data(db: Session = Depends(get_db)):
    """Reset all gallery data for testing purposes."""
    
    try:
        reset_items = []
        
        # Reset image statistics back to defaults
        db.execute(text("""
            UPDATE images SET 
                likes = 0,
                unlikes = 0, 
                skips = 0,
                exposures = 0,
                mu = 1500.0,
                sigma = 350.0,
                last_seen_round = NULL,
                next_eligible_round = NULL,
                is_archived_hard_no = false
        """))
        reset_items.append("Image statistics and Elo ratings")
        
        # Clear all choice history  
        db.execute(text("DELETE FROM choices"))
        reset_items.append("All choice history")
        
        # Reset round counter to 1
        db.execute(text("UPDATE app_state_new SET round = 1"))
        reset_items.append("Round counter")
        
        # Clear all portfolios (if tables exist)
        try:
            db.execute(text("DELETE FROM portfolio_images"))
            db.execute(text("DELETE FROM portfolios"))
            reset_items.append("All portfolios")
        except Exception:
            pass  # Tables may not exist yet
        
        # Clear gallery images (if tables exist)
        try:
            db.execute(text("DELETE FROM gallery_images"))
            db.execute(text("DELETE FROM galleries"))
            reset_items.append("All galleries")
        except Exception:
            pass  # Tables may not exist yet
        
        db.commit()
        
        return ResetResponse(
            success=True,
            message="Gallery data has been reset successfully",
            reset_items=reset_items
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to reset gallery data: {str(e)}"
        )